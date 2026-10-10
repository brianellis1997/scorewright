"""The brief a composer reads before writing: the whole piece as reduced ABC with section breaks
marked, where it stops and which voices stop, and retrieval exemplars from Brian's other scores
that share the shape of the last written bars (with his slurs and dynamics as he wrote them).
usage (whisperer env): python brief.py <score stem> [last_written_bar] [part index for retrieval]"""
import os, re, sys, json, sqlite3
sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import retrieve
E = '/Users/bdogellis/Documents/Score Exports'
stem = sys.argv[1]
red = f'{E}/_scorewright_out/{stem}_reduced.txt'
if not os.path.exists(red):
    os.system(f'cd {os.path.dirname(os.path.abspath(__file__))} && /Users/bdogellis/miniforge3/envs/text2score/bin/python dump_abc.py "{E}/MusicXML/{stem}.musicxml" BRIEF 2>/dev/null | grep -v -i "warn\\|transformers" > "{red}"')
txt = open(red).read().split('\n')
body = [l for l in txt if re.match(r'\s*\d+\s+\[V:', l)]
hdr = [l for l in txt if l.startswith(('L:', 'M:', 'K:', 'Q:', 'V:', '%%score'))]
bars = [(int(l.split()[0]), l.split(None, 1)[1]) for l in body]
def has_notes(seg): return bool(re.search(r'[A-Ga-g]', re.sub(r'![^!]*!|"[^"]*"|\[[A-Zr]:[^\]]*\]', '', seg)))
last = int(sys.argv[2]) if len(sys.argv) > 2 else max((n for n, l in bars if has_notes(l)), default=0)
print('=== HEADER'); print('\n'.join(hdr))
print(f'=== FORM  ({len(bars)} bars in the file, music stops at bar {last})')
empty_runs, run = [], []
for n, l in bars:
    if not has_notes(l): run.append(n)
    elif run: empty_runs.append((run[0], run[-1])); run = []
if run: empty_runs.append((run[0], run[-1]))
print('empty bars (section breaks or the gap):', empty_runs)
for n, l in bars:
    if '"^' in l or '[Q:' in l or '[M:' in l or '[K:' in l or '||' in l:
        print(f'  bar {n}: ' + ', '.join(sorted(set(re.findall(r'"\^([^"]*)"|\[(?:Q|M|K):[^\]]*\]|\|\|', l))))[:120])
print('=== LAST WRITTEN BARS')
for n, l in bars:
    if last - 4 <= n <= last: print(f'{n:4d}  {l[:400]}')
print('=== RETRIEVAL: where he wrote this shape before (his notation, slurs, dynamics)')
part = int(sys.argv[3]) if len(sys.argv) > 3 else 0
instr = re.compile(sys.argv[4], re.I) if len(sys.argv) > 4 else None   # e.g. 'violin|viola|cello'
try:
    con = sqlite3.connect(retrieve.DB)
    hits, _ = retrieve.query(stem, max(1, last - 3), last, part=part, top=60 if instr else 6, con=con)
    shown = 0
    for h in hits:
        if shown >= 6: break
        m = str(h['measures']); lo, hi = (m.split('-') + [m])[:2]
        try: ex = retrieve.excerpt_text(h['score'], int(lo), int(hi), part=h['part'], max_chars=320)
        except Exception as e: ex = f'(excerpt unavailable: {e})'
        if instr and not instr.search(ex.split(' m')[0]): continue
        shown += 1
        print(f"- {h['score']} bars {m} part {h['part']} (weight {h['weight']}):\n    " + ex.replace('\n', '\n    '))
except Exception as e:
    print('retrieval unavailable:', e)
