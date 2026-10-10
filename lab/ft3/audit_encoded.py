"""Preflight step 1: encoded sizes per task kind, measured in patches the way the trainer sees them.
usage (text2score env): T2S_MAXP=2048 python ft3/audit_encoded.py <docs.jsonl> [sample_n]"""
import os, sys, json, random, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, os.path.join(HERE, '..', 'ft2'))
from eval_edit import crop, crop_fit, MAXP, PATCH_SIZE
from utils import Patchilizer
pat = Patchilizer()
path, n = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 500
docs = [json.loads(l) for l in open(path)]
random.seed(11); random.shuffle(docs); docs = docs[:n]
BIG = 10 ** 6
def count(txt): return len(pat.encode_generate(txt, patch_length=BIG))
def audit(label, cropper):
    st = collections.defaultdict(lambda: dict(n=0, sizes=[], skip=0, cut=0))
    for d in docs:
        text = cropper(d)
        a0 = text.index('%%answer\n') + len('%%answer\n')
        pre, full = count(text[:a0]), count(text)
        s = st[d['kind']]; s['n'] += 1; s['sizes'].append(full)
        s['skip'] += pre >= MAXP - 1
        s['cut'] += (pre < MAXP - 1) and (full > MAXP)
    print(f'{label}: window {MAXP} patches, sample {len(docs)} docs from {os.path.basename(path)}')
    bad = False
    for k, s in sorted(st.items()):
        z = sorted(s['sizes']); med, mx = z[len(z) // 2], z[-1]
        skip, cut = 100 * s['skip'] / s['n'], 100 * s['cut'] / s['n']
        flag = '  <-- FIX FIRST' if skip + cut > 5 else ''
        bad |= bool(flag)
        print(f'  {k:12s} n={s["n"]:4d}  patches median {med:5d} max {mx:5d}  skipped {skip:4.0f}%  answer cut {cut:4.0f}%{flag}')
    return bad
bad = audit('character crop (what the GPU day used)', lambda d: crop(d['text'], d['answer_start'], budget_chars=MAXP * PATCH_SIZE * 0.8))
bad = audit('patch-measured crop_fit (fixed)', lambda d: crop_fit(d['text'], d['answer_start'], pat))
print('PREFLIGHT_ENCODED', 'FAIL' if bad else 'OK')
