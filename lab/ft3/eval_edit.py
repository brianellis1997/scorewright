"""Ground-truth benchmark for the instructed-infill model.

Every eval document carries the composer's real answer, so accuracy per edit kind is measurable
without anyone listening: the model writes the answer lines after %%answer, and we compare them
bar by bar with the original. Metrics (all per bar, averaged):
  pitch_f1  : F1 between the multiset of midi pitches the model wrote and the original's
  exact     : the answer line is byte-identical after whitespace normalisation (doublings should
              approach this; nothing else will)
  rhythm    : fraction of answer bars whose durations sum to the right length (verifier-style)
usage: T2S_CKPT=<pth> python ft3/eval_edit.py <docs_eval.jsonl> <n_per_kind> [temperature]
"""
import os, sys, re, json, time, random, collections
import torch
from unidecode import unidecode
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.dirname(HERE)
sys.path.insert(0, SCR); sys.path.insert(0, os.path.join(SCR, 'ft2'))
import t2s_arm as A                                   # load() honours T2S_CKPT; NA.abc_pitches
from t2s_arm import PATCH_SIZE, PATCH_LENGTH, DEV
from forced import write_forced, template_from_truth
FORCED = bool(os.environ.get('T2S_FORCED'))
MAXP = int(os.environ.get('T2S_MAXP', 512))


def crop(text, answer_start, budget_chars):
    """Keep header + answer + the body lines nearest the target region until budget_chars."""
    ctx, ans = text[:answer_start], text[answer_start:]
    lines = [l for l in ctx.split('\n') if l.strip()]
    bi = next((i for i, l in enumerate(lines) if l.startswith('[V:') or l.startswith('[b:') or l == '?'), len(lines))
    header, body = lines[:bi], [l for l in lines[bi:] if l != '%%answer']
    tgt = [i for i, l in enumerate(body) if l.endswith(']?') or l == '?' or '?|' in l]
    if not tgt:                                    # continuation: the target is the end
        tgt = [len(body) - 1]
    lo, hi = min(tgt), max(tgt)
    keep = set(range(lo, hi + 1))
    used = sum(len(l) + 1 for l in header) + sum(len(body[i]) + 1 for i in keep) + len(ans) + 16
    left, right = lo - 1, hi + 1
    while used < budget_chars and (left >= 0 or right < len(body)):
        cand = []
        if left >= 0: cand.append(left)
        if right < len(body): cand.append(right)
        i = cand[0] if len(cand) == 1 else (left if random.random() < 0.7 else right)
        if used + len(body[i]) + 1 > budget_chars:
            break
        keep.add(i); used += len(body[i]) + 1
        if i == left: left -= 1
        else: right += 1
    body2 = [body[i] for i in sorted(keep)]
    return '\n'.join(header + body2) + '\n%%answer\n' + ans


NA = A.NA


@torch.no_grad()

def crop_fit(text, answer_start, pat, room=320):
    """crop() measured in characters, but the patchilizer pads every line to whole patches, so a
    26K-char prefix from a 300-bar quartet came out at the full 2048-patch window and the model
    had no room to answer (19/20 doubling prompts on Sept 4). Shrink the char budget until the
    encoded prefix leaves `room` patches for the answer."""
    budget = MAXP * PATCH_SIZE * 0.8
    for _ in range(12):
        t = crop(text, answer_start, budget_chars=budget)
        a0 = t.index('%%answer\n') + len('%%answer\n')
        if len(pat.encode_generate(t[:a0])) <= MAXP - room:
            return t
        budget *= 0.8
    return t


STREAM = bool(os.environ.get('T2S_STREAM'))


def stream_prefix(prefix, n_answer_lines):
    """docs3 format at inference: the encoder adds [r:idx/remaining] to every tunebody line in
    training (stream mode), so the prompt must carry the same tags. remaining counts down to the
    last answer line, which is how the model knows when to stop."""
    lines = [l for l in prefix.split('\n') if l.strip()]
    bi = next((i for i, l in enumerate(lines) if l.startswith('[V:')), len(lines))
    body = lines[bi:]
    total = len(body) + n_answer_lines
    tagged = [f'[r:{i}/{total - i - 1}]' + l for i, l in enumerate(body)]
    return '\n'.join(lines[:bi] + tagged) + '\n'


def next_stream_tag(prefix, n_answer_lines, k):
    """the [r:] tag the k-th answer line should start with (forced mode)."""
    body = sum(1 for l in prefix.split('\n') if l.strip()) - next((i for i, l in enumerate([x for x in prefix.split('\n') if x.strip()]) if l.startswith('[V:')), 0)
    total = body + n_answer_lines
    i = body + k
    return f'[r:{i}/{total - i - 1}]'

def write_answer(model, pat, instr, prefix, n_lines, temperature=0.7, max_secs=240):
    plan_ids = pat.encode_plan(instr).to(DEV)
    ip = pat.encode_generate(prefix)
    ip = torch.tensor([[x for sub in ip for x in sub]], device=DEV).reshape(1, -1)
    gen, t0 = '', time.time()
    no_eos = bool(os.environ.get('T2S_NO_EOS'))
    retries = 0
    while gen.count('\n') < n_lines:
        p = model.generate(plan_ids.unsqueeze(0), ip.unsqueeze(0), top_k=9, top_p=0.9, temperature=temperature)
        if p[0] == pat.bos_token_id and p[1] == pat.eos_token_id:
            retries += 1
            if no_eos and retries < 12 and time.time() - t0 < max_secs:
                continue                      # length guard: the request said n bars; resample this patch
            break
        if no_eos:
            txt = pat.decode([p])
            if '|]' in txt:                   # end-of-piece barline before the requested length: rewrite as a plain barline
                p = [ord(c) for c in txt.replace('|]', '| ')][:PATCH_SIZE]
                p = p + [pat.special_token_id] * (PATCH_SIZE - len(p))
        gen += pat.decode([p])
        end = False
        for j in range(len(p)):
            if end: p[j] = pat.special_token_id
            if p[j] == pat.eos_token_id: end = True
        ip = torch.cat([ip, torch.tensor([p], device=DEV)], dim=1)
        if time.time() - t0 > max_secs or ip.shape[1] >= PATCH_LENGTH * PATCH_SIZE or len(gen) > 20000:
            break
    return gen


def norm(line):
    line = re.sub(r'\[r:\d+/\d+\]', '', line)
    return re.sub(r'\s+', '', line)


def f1(a, b):
    ca, cb = collections.Counter(a), collections.Counter(b)
    inter = sum((ca & cb).values())
    if not a and not b: return 1.0
    if not inter: return 0.0
    p, r = inter / len(a), inter / len(b)
    return 2 * p * r / (p + r)


if __name__ == '__main__':
    docs_path, n_per = sys.argv[1], int(sys.argv[2])
    temp = float(sys.argv[3]) if len(sys.argv) > 3 else 0.7
    docs = [json.loads(l) for l in open(docs_path)]
    random.seed(11); random.shuffle(docs)
    by = collections.defaultdict(list)
    only = set(os.environ.get('T2S_KINDS', '').split(',')) - {''}
    for d in docs:
        if only and d['kind'] not in only: continue
        if len(by[d['kind']]) < n_per: by[d['kind']].append(d)
    model, pat = A.load()
    res = collections.defaultdict(lambda: collections.defaultdict(list))
    out = open(os.path.join(HERE, f"eval_{'forced_' if FORCED else ''}{os.path.basename(os.environ.get('T2S_CKPT', 'stock'))[:30]}.jsonl"), 'w')
    for kind, ds in by.items():
        for d in ds:
            text = crop_fit(d['text'], d['answer_start'], pat)
            text = ''.join(c if ord(c) < 128 else unidecode(c) for c in text.replace('\u266d', 'b').replace('\u266f', '#'))
            a0 = text.index('%%answer\n') + len('%%answer\n')
            prefix, truth = text[:a0], text[a0:]
            instr = text.split('\n', 1)[0].replace('%%instruction: ', '')
            truth_lines = [l for l in truth.split('\n') if l.strip()]
            t0 = time.time()
            raw_prefix = prefix
            if STREAM:
                prefix = stream_prefix(prefix, len(truth_lines))
            if FORCED:
                tags = [next_stream_tag(raw_prefix, len(truth_lines), k) for k in range(len(truth_lines))] if STREAM else None
                gen = write_forced(model, pat, pat.encode_plan(instr).to(DEV), prefix, template_from_truth(truth_lines), temperature=temp, max_secs=240, line_tags=tags, voice_first=STREAM)
            else:
                gen = write_answer(model, pat, instr, prefix, len(truth_lines), temperature=temp)
            gen_lines = [l for l in gen.split('\n') if '[V:' in l]
            by_b = {}
            for gl in gen_lines:
                mb = re.search(r'\[b:(\d+)\]', gl)
                if mb and int(mb.group(1)) not in by_b: by_b[int(mb.group(1))] = gl
            pf, ex, pc, hit = [], [], [], 0
            for k, tl in enumerate(truth_lines):
                mb = re.search(r'\[b:(\d+)\]', tl); tb = int(mb.group(1)) if mb else None
                gl = by_b.get(tb) if tb in by_b else (gen_lines[k] if k < len(gen_lines) else '')
                hit += tb in by_b
                pt, pg = NA.abc_pitches(re.sub(r'\[b:\d+\]', '', tl)), NA.abc_pitches(re.sub(r'\[b:\d+\]', '', gl))
                pf.append(f1(pg, pt)); pc.append(f1([x % 12 for x in pg], [x % 12 for x in pt]))
                ex.append(norm(gl) == norm(tl))
            res[kind]['pitch_f1'].append(sum(pf) / len(pf)); res[kind]['exact'].append(sum(ex) / len(ex))
            res[kind]['pc_f1'].append(sum(pc) / len(pc)); res[kind]['bar_hit'].append(hit / len(truth_lines))
            res[kind]['secs'].append(time.time() - t0)
            out.write(json.dumps(dict(kind=kind, score=d['score'], instr=instr, truth=truth_lines, gen=gen_lines,
                                      pitch_f1=res[kind]['pitch_f1'][-1], exact=res[kind]['exact'][-1])) + '\n'); out.flush()
            print(f"  {kind:12s} {d['score'][:28]:28s} f1 {res[kind]['pitch_f1'][-1]:.2f} exact {res[kind]['exact'][-1]:.2f} {time.time()-t0:.0f}s", flush=True)
    print('EVAL_DONE', os.environ.get('T2S_CKPT', 'stock'))
    for kind in res:
        m = res[kind]
        print(f"  {kind:12s} n={len(m['pitch_f1'])} pitch_f1 {sum(m['pitch_f1'])/len(m['pitch_f1']):.3f}  pitchclass_f1 {sum(m['pc_f1'])/len(m['pc_f1']):.3f}  bar_hit {sum(m['bar_hit'])/len(m['bar_hit']):.2f}  exact {sum(m['exact'])/len(m['exact']):.3f}  {sum(m['secs'])/len(m['secs']):.0f}s each")
