"""Print the raw forced-decode output for the first N docs of one kind (debugging truncation).
usage: T2S_CKPT=... T2S_MAXP=2048 python ft3/peek_forced.py <docs.jsonl> <kind> <n>"""
import os, sys, json, random, collections, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from eval_edit import crop, MAXP, PATCH_SIZE, A, DEV
from forced import write_forced, template_from_truth
from unidecode import unidecode
docs = [json.loads(l) for l in open(sys.argv[1])]
random.seed(11); random.shuffle(docs)
ds = [d for d in docs if d['kind'] == sys.argv[2]][:int(sys.argv[3])]
model, pat = A.load()
for d in ds:
    text = crop(d['text'], d['answer_start'], budget_chars=MAXP * PATCH_SIZE * 0.8)
    text = ''.join(c if ord(c) < 128 else unidecode(c) for c in text.replace('♭', 'b').replace('♯', '#'))
    a0 = text.index('%%answer\n') + len('%%answer\n')
    prefix, truth = text[:a0], text[a0:]
    instr = text.split('\n', 1)[0].replace('%%instruction: ', '')
    truth_lines = [l for l in truth.split('\n') if l.strip()]
    print('=====', d['score'][:40], '|', instr[:100])
    print('prefix chars', len(prefix), 'template', template_from_truth(truth_lines))
    print('prefix tail:', repr(prefix[-300:]))
    gen = write_forced(model, pat, pat.encode_plan(instr).to(DEV), prefix, template_from_truth(truth_lines), temperature=0.6, max_secs=240)
    print('RAW GEN:', repr(gen[:400]))
    for t in truth_lines[:2]: print('truth:', t[:120])
print('PEEK_FORCED_DONE')
