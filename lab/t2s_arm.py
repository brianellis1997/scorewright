"""Text2Score as a plan-steered continuation engine for Orchestral Idea, on Apple silicon.

Same trick as notagen_arm.py (it is NotaGen's decoder) plus the one thing NotaGen never had: a
per-measure plan the patch decoder cross-attends to. Prefix = his 16 bars with [r:i/31-i] stream
markers so the model knows 16 bars remain; plan = P0 (says nothing about 17-32) or P1 (thin to
strings, new material, winds then brass, dominant by 32). The measurable question: do the sounding
instruments in bars 17-20 follow the plan, or does it rebuild the tutti like everything before it.
"""
import os, sys, re, json, time, argparse, warnings, subprocess
warnings.filterwarnings('ignore')
import torch
HERE = os.path.dirname(os.path.abspath(__file__))
T2S = '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
os.chdir(T2S)
sys.path.insert(0, f'{T2S}/text2music/inference'); sys.path.insert(0, T2S); sys.path.insert(0, HERE)
from utils import *          # Patchilizer, CustomLMHeadModel
from config import *         # PATCH_*, HIDDEN_SIZE, INFERENCE_WEIGHTS_PATH
from transformers import GPT2Config
import notagen_arm as NA
import post, splice

DEV = torch.device(os.environ['T2S_DEVICE']) if os.environ.get('T2S_DEVICE') else (torch.device('mps') if torch.backends.mps.is_available() else torch.device('cpu'))
SRC = '/Users/bdogellis/Documents/Score Exports/abc_augmented/Bb/Orchestral Idea_Bb.abc'
ORIG = '/Users/bdogellis/Documents/Score Exports/MusicXML/Orchestral Idea.musicxml'
TOTAL = int(os.environ.get('T2S_TOTAL', 32))
KEEP = 16
STRINGS = {20, 21, 22, 23, 24}

lines = [l for l in open(SRC).read().split('\n') if l.strip()] if os.path.exists(SRC) else []
bi = [i for i, l in enumerate(lines) if l.startswith('[V:')]
head, body = (lines[:bi[0]], [lines[j] for j in bi]) if bi else ([], [])
body = body[:KEEP]
prefix = '\n'.join(head + [f'[r:{i}/{TOTAL - 1 - i}]' + l for i, l in enumerate(body)]) + '\n'
VNAME = {int(m.group(1)): m.group(2) for m in re.finditer(r'^V:(\d+)[^\n]*?nm="([^"]+)"', '\n'.join(head), re.M)}
NAME2V = {v: k for k, v in VNAME.items()}


def load():
    pc = GPT2Config(num_hidden_layers=PATCH_NUM_LAYERS, max_length=PATCH_LENGTH, max_position_embeddings=PATCH_LENGTH,
                    n_embd=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=1)
    bc = GPT2Config(num_hidden_layers=CHAR_NUM_LAYERS, max_length=PATCH_SIZE + 1, max_position_embeddings=PATCH_SIZE + 1,
                    hidden_size=HIDDEN_SIZE, num_attention_heads=HIDDEN_SIZE // 64, vocab_size=128)
    m = CustomLMHeadModel(encoder_config=pc, decoder_config=bc)
    ckpt = os.environ.get('T2S_CKPT', INFERENCE_WEIGHTS_PATH)
    ck = torch.load(ckpt, map_location='cpu', weights_only=False)
    m.load_state_dict(ck['model'], strict=False)
    print('checkpoint', os.path.basename(ckpt), 'epoch', ck.get('epoch'), 'eval', ck.get('eval'), flush=True)
    del ck
    return m.to(DEV).eval(), Patchilizer()


@torch.no_grad()
def continue_abc(model, pat, plan_ids, prefix, n_bars, top_k=9, top_p=0.9, temperature=1.0, max_secs=1500, log=None):
    ip = pat.encode_generate(prefix)
    ip = torch.tensor([[x for sub in ip for x in sub]], device=DEV).reshape(1, -1)
    gen, t0, last_bars = '', time.time(), 0
    while gen.count('\n') < n_bars:
        p = model.generate(plan_ids.unsqueeze(0), ip.unsqueeze(0), top_k=top_k, top_p=top_p, temperature=temperature)
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
        if nb != last_bars and log:
            log(f'    bar {KEEP + nb} done at {time.time() - t0:.0f}s')
            last_bars = nb
        if time.time() - t0 > max_secs or len(gen) > 80_000:
            break
        if ip.shape[1] >= PATCH_LENGTH * PATCH_SIZE:
            full = prefix + gen
            cut = full.rfind('\n')
            if cut < len(prefix):
                break
            full = full[:cut + 1]
            gen = full[len(prefix):]
            b = full.split('\n')
            k = next((i for i, l in enumerate(b) if l.startswith('[V:') or l.startswith('[r:')), None)
            if k is None:
                break
            meta, bars = b[:k], [l for l in b[k:] if l.strip()]
            ip = pat.encode_generate('\n'.join(meta + bars[-max(2, len(bars) // 3):]) + '\n')
            ip = torch.tensor([[x for sub in ip for x in sub]], device=DEV).reshape(1, -1)
    cut = gen.rfind('\n')
    return gen[:cut + 1] if cut >= 0 else gen


def voices_of(bar_line):
    out = {}
    for m in re.finditer(r'\[V:(\d+)\]([^\[]*(?:\[(?!V:)[^\]]*\][^\[]*)*)', bar_line):
        out[int(m.group(1))] = m.group(2)
    return out


def analyse(gen):
    bars = [l for l in gen.split('\n') if l.strip()]
    rows = []
    for i, bl in enumerate(bars):
        vs = voices_of(bl)
        sounding = sorted(v for v, t in vs.items() if NA.abc_pitches(t))
        notes = sum(len(NA.abc_pitches(t)) for t in vs.values())
        dyn = re.findall(r'!(p{2,4}|p|mp|mf|f{1,3})!', bl)
        rows.append(dict(bar=KEEP + 1 + i, n_sounding=len(sounding), strings_only=bool(sounding) and set(sounding) <= STRINGS,
                         sounding=sounding, notes=notes, dyn=dyn[:6]))
    return rows


def assemble(gen, tag):
    gen = re.sub(r'%\d+', '', gen)
    full = '\n'.join(head + body) + '\n' + re.sub(r'\[r:\d+/\d+\]', '', gen)
    x, rc = post.to_xml(full, f't2s_{tag}')
    a, f2, last = splice.splice(ORIG, x, f'{HERE}/t2s_{tag}_spliced.xml', keep_through=KEEP)
    raw = open(f'{HERE}/t2s_{tag}_spliced.xml').read()
    raw = re.sub(r'<print\b[^>]*/>', '', raw)
    raw = re.sub(r'<print\b[^>]*>.*?</print>', '', raw, flags=re.S)
    out = f'{HERE}/t2s_{tag}_final.xml'
    open(out, 'w').write(raw)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--plan', default='P1')
    ap.add_argument('--n', type=int, default=1)
    ap.add_argument('--bars', type=int, default=16)
    ap.add_argument('--temp', type=float, default=1.0)
    ap.add_argument('--start', type=int, default=0)
    a = ap.parse_args()
    logf = open(f'{HERE}/t2s_{a.plan}.log', 'a')

    def log(s):
        print(s, flush=True); logf.write(s + '\n'); logf.flush()

    log(f'prefix: {len(body)} bars, {len(prefix)} chars; voices {len(VNAME)}; plan {a.plan}; device {DEV}')
    t0 = time.time()
    model, pat = load()
    log(f'model loaded {time.time() - t0:.0f}s')
    plan_txt = open(f'{HERE}/t2s_plan_{a.plan}.txt').read()
    plan_ids = pat.encode_plan(plan_txt).to(DEV)
    log(f'plan tokens {plan_ids.shape[0]}')
    for i in range(a.start, a.start + a.n):
        tag = f'{a.plan}_{i}'
        t1 = time.time()
        gen = continue_abc(model, pat, plan_ids, prefix, a.bars, temperature=a.temp, log=log)
        open(f'{HERE}/t2s_{tag}.abc', 'w').write(gen)
        rows = analyse(gen)
        log(f'  {tag}: {len(rows)} bars in {time.time() - t1:.0f}s')
        for r in rows:
            log(f"    bar {r['bar']:2d} voices {r['n_sounding']:2d} strings_only={r['strings_only']} dyn={r['dyn']} sounding={r['sounding']}")
        try:
            final = assemble(gen, tag)
            log(f'  assembled -> {final}')
        except Exception as e:
            final = None
            log(f'  assembly failed: {type(e).__name__} {str(e)[:120]}')
        with open(f'{HERE}/t2s_runs.jsonl', 'a') as f:
            f.write(json.dumps(dict(tag=tag, plan=a.plan, temp=a.temp, secs=round(time.time() - t1), bars=len(rows),
                                    rows=rows, final=final)) + '\n')
    log('T2S_DONE ' + a.plan)
