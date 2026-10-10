"""Plan-constrained decoding for Text2Score.

The soft plan (cross-attention) did not thin the texture: bar 17 came out with 14 voices at mf
against a plan of five strings at pp. Rest-reduced interleaved ABC omits every resting voice, so
which instruments play in a bar is exactly the set of [V:k] tags the model emits in that line.
That makes the instruction enforceable at decode time: while the model is writing "[V:" we only let
it sample digits that lead to a voice the plan allows for the bar being written. The model still
chooses every note; it just cannot bring in an instrument the plan says is silent. Agogic (2026)
reported the same kind of decode-time constraint lifting instrument F1 from .28 to .60.
"""
import os, sys, re, json, time, argparse
import numpy as np, torch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import t2s_arm as A
from t2s_arm import PATCH_SIZE, PATCH_LENGTH, DEV, KEEP, TOTAL, NAME2V, prefix, head, body
from samplings import top_p_sampling, top_k_sampling, temperature_sampling
from utils import safe_normalize_probs


def plan_voice_sets(plan_txt):
    """bar -> set of allowed voice numbers, carried forward from the last planned measure."""
    spec = {}
    for m in re.finditer(r'Measure: (\d+)\n  Instruments: ([^\n]*)', plan_txt):
        names = [n.strip() for n in m.group(2).split(',') if n.strip()]
        spec[int(m.group(1))] = {NAME2V[n] for n in names if n in NAME2V}
    out, cur = {}, None
    for b in range(1, TOTAL + 1):
        if b in spec:
            cur = spec[b]
        out[b] = cur
    return out


MIN_FRAC = float(os.environ.get('T2S_MINFRAC', 0))


def allowed_chars(cur_line, voices):
    """Constraint on the NEXT character; None = unconstrained.
    Two rules. While a [V:k] tag is being written, only digits that lead to a voice the plan allows
    for this bar AND that has not already been written in this line. And when a voice's bar has
    just closed (line ends with |) and every allowed voice is already in the line, the only legal
    next character is the newline: the bar is complete, no instrument may be added."""
    if voices is None:
        return None
    used = {int(v) for v in re.findall(r'\[V:(\d+)\]', cur_line)}
    remaining = set(voices) - used
    if cur_line.endswith('|') and not remaining:
        return {'\n'}
    need = int(MIN_FRAC * len(voices) + 0.999)
    if MIN_FRAC and cur_line.endswith('|') and len(used) < need and remaining:
        return {'['}
    if MIN_FRAC and cur_line.endswith('|[') and len(used) < need and remaining:
        return {'V'}
    if MIN_FRAC and cur_line.endswith('|[V') and len(used) < need and remaining:
        return {':'}
    m = re.search(r'\[V:(\d*)$', cur_line)
    if not m:
        return None
    so_far = m.group(1)
    pool = remaining or set(voices)
    ok = set()
    for v in pool:
        t = str(v)
        if t.startswith(so_far):
            ok.add(']' if len(t) == len(so_far) else t[len(so_far)])
    return ok


@torch.no_grad()
def gen_patch(model, plan_ids, patches, text_so_far, voices, top_k, top_p, temperature):
    if patches.shape[-1] % PATCH_SIZE != 0:
        tokens = patches[:, -(patches.shape[-1] % PATCH_SIZE):].squeeze(0)
        tokens = torch.cat((torch.tensor([model.bos_token_id], device=DEV), tokens), dim=-1)
        patches = patches[:, :-(patches.shape[-1] % PATCH_SIZE)]
    else:
        tokens = torch.tensor([model.bos_token_id], device=DEV)
    patches = patches.reshape(1, -1, PATCH_SIZE)
    enc = model.patch_level_model(plan_ids.unsqueeze(0), patches)['last_hidden_state']
    out, cur = [], text_so_far
    while True:
        prob = model.char_level_decoder.generate(enc[0][-1], tokens).cpu().detach().numpy()
        prob = safe_normalize_probs(prob)
        ok = allowed_chars(cur, voices)
        if ok is not None:
            mask = np.zeros_like(prob)
            for c in ok:
                mask[ord(c)] = 1
            prob = safe_normalize_probs(prob * mask) if (prob * mask).sum() > 0 else safe_normalize_probs(mask)
        prob = safe_normalize_probs(top_k_sampling(prob, top_k=top_k, return_probs=True))
        prob = safe_normalize_probs(top_p_sampling(prob, top_p=top_p, return_probs=True))
        tok = int(temperature_sampling(prob, temperature=temperature))
        out.append(tok)
        if tok >= 3:
            cur += chr(tok)
            if chr(tok) == '\n':
                cur = ''
        if len(tokens) >= PATCH_SIZE:
            break
        tokens = torch.cat((tokens, torch.tensor([tok], device=DEV)), dim=0)
    return out


@torch.no_grad()
def continue_constrained(model, pat, plan_ids, vsets, n_bars, top_k=9, top_p=0.9, temperature=1.0, max_secs=3600, log=None):
    ip = pat.encode_generate(prefix)
    ip = torch.tensor([[x for sub in ip for x in sub]], device=DEV).reshape(1, -1)
    gen, t0, last = '', time.time(), 0
    while gen.count('\n') < n_bars:
        bar = KEEP + 1 + gen.count('\n')
        cur_line = gen[gen.rfind('\n') + 1:]
        p = gen_patch(model, plan_ids, ip, cur_line, vsets.get(bar), top_k, top_p, temperature)
        if p[0] == pat.bos_token_id and p[1] == pat.eos_token_id:
            break
        gen += pat.decode([p])
        end = False
        for j in range(len(p)):
            if end:
                p[j] = pat.special_token_id
            if p[j] == pat.eos_token_id:
                end = True
        ip = torch.cat([ip, torch.tensor([p], device=DEV)], dim=1)
        nb = gen.count('\n')
        if nb != last and log:
            log(f'    bar {KEEP + nb} done at {time.time() - t0:.0f}s'); last = nb
        if time.time() - t0 > max_secs or len(gen) > 80_000 or ip.shape[1] >= PATCH_LENGTH * PATCH_SIZE:
            break
    cut = gen.rfind('\n')
    return gen[:cut + 1] if cut >= 0 else gen


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', default='P1')
    ap.add_argument('--n', type=int, default=1)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--bars', type=int, default=16)
    ap.add_argument('--temp', type=float, default=1.0)
    a = ap.parse_args()
    logf = open(f"{HERE}/t2s_{os.environ.get('T2S_LABEL', '')}{a.plan}c.log", 'a')

    def log(s):
        print(s, flush=True); logf.write(s + '\n'); logf.flush()

    plan_txt = open(f'{HERE}/t2s_plan_{a.plan}.txt').read()
    vsets = plan_voice_sets(plan_txt)
    log(f'MIN_FRAC {MIN_FRAC}'); log('voice sets: ' + ', '.join(f'{b}:{sorted(vsets[b]) if vsets[b] else None}' for b in (17, 21, 25, 29, 32)))
    model, pat = A.load()
    plan_ids = pat.encode_plan(plan_txt).to(DEV)
    for i in range(a.start, a.start + a.n):
        tag = f"{os.environ.get('T2S_LABEL', '')}{a.plan}c_{i}"
        t1 = time.time()
        gen = continue_constrained(model, pat, plan_ids, vsets, a.bars, temperature=a.temp, log=log)
        open(f'{HERE}/t2s_{tag}.abc', 'w').write(gen)
        rows = A.analyse(gen)
        log(f'  {tag}: {len(rows)} bars in {time.time() - t1:.0f}s')
        for r in rows:
            log(f"    bar {r['bar']:2d} voices {r['n_sounding']:2d} strings_only={r['strings_only']} dyn={r['dyn']} sounding={r['sounding']}")
        try:
            final = A.assemble(gen, tag); log(f'  assembled -> {final}')
        except Exception as e:
            final = None; log(f'  assembly failed: {type(e).__name__} {str(e)[:120]}')
        with open(f'{HERE}/t2s_runs.jsonl', 'a') as f:
            f.write(json.dumps(dict(tag=tag, plan=a.plan + 'c', temp=a.temp, secs=round(time.time() - t1), bars=len(rows), rows=rows, final=final)) + '\n')
    log('T2S_DONE ' + a.plan + 'c')
