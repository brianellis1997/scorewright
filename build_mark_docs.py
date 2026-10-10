"""Marking-task documents (dynamics, articulation, pedal) from a reduced-ABC corpus.
usage: build_mark_docs.py <abcr_root> <out.jsonl> [eval_frac] [max_scores]"""
import os, sys, json, glob, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_format as EF
root, out = sys.argv[1], sys.argv[2]
eval_frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
max_scores = int(sys.argv[4]) if len(sys.argv) > 4 else 0
files = sorted(glob.glob(os.path.join(root, '*', '*.abc')))
random.seed(9); random.shuffle(files)
if max_scores: files = files[:max_scores]
n_eval = int(len(files) * eval_frac)
outs = {'train': open(out, 'w'), 'eval': open(out.replace('.jsonl', '_eval.jsonl'), 'w') if eval_frac else None}
counts = {}; ok = 0
for k, f in enumerate(files):
    txt = open(f, encoding='utf-8', errors='ignore').read()
    stem = os.path.basename(f).rsplit('_', 1)[0]
    for rec in EF.mark_records(txt, stem, rnd=random.Random(k)):
        doc = EF.build_marks(rec, txt)
        if doc:
            (outs['eval'] if k < n_eval and outs['eval'] else outs['train']).write(json.dumps(doc) + '\n')
            counts[rec['kind']] = counts.get(rec['kind'], 0) + 1; ok += 1
print('MARKS_DONE', ok, 'docs from', len(files), 'scores:', counts)
