"""Find Brian's own scores by what a new piece needs: instrumentation, key, meter, tempo, date.
The exemplars a brief should show before composing something new (no passage to match yet).
usage (whisperer env): python corpus_find.py "<instrument regex>" [key] [meter] [since YYYY-MM-DD] [max]
e.g. python corpus_find.py "violin|viola|cello" "" 4/4 2019-01-01 8"""
import os, re, sys, glob, datetime
E = '/Users/bdogellis/Documents/Score Exports'
instr = re.compile(sys.argv[1], re.I) if len(sys.argv) > 1 and sys.argv[1] else None
key = sys.argv[2] if len(sys.argv) > 2 else ''
meter = sys.argv[3] if len(sys.argv) > 3 else ''
since = sys.argv[4] if len(sys.argv) > 4 else ''
mx = int(sys.argv[5]) if len(sys.argv) > 5 else 12
rows = []
for f in glob.glob(f'{E}/abc_reduced/*/*.abc'):
    t = open(f, encoding='utf-8', errors='ignore').read()
    hdr = t.split('\n[V:', 1)[0]
    names = re.findall(r'^V:\d+[^\n]*? nm="([^"]*)"', hdr, re.M)
    k = re.search(r'^K:(\S+)', hdr, re.M); m = re.search(r'^M:(\S+)', hdr, re.M); q = re.search(r'^Q:(\S+)', hdr, re.M)
    stem = os.path.basename(f).rsplit('_', 1)[0]
    sib = f'{E}/_source_sib/{stem}.sib'
    d = datetime.date.fromtimestamp(os.path.getmtime(sib)).isoformat() if os.path.exists(sib) else ''
    bars = t.count('\n[V:')
    if instr and not any(instr.search(n) for n in names): continue
    if key and (not k or k.group(1).lower() != key.lower()): continue
    if meter and (not m or m.group(1) != meter): continue
    if since and d and d < since: continue
    rows.append((d, stem, k.group(1) if k else '?', m.group(1) if m else '?', q.group(1) if q else '', bars, len(names), ', '.join(dict.fromkeys(names))[:60]))
rows.sort(reverse=True)
print(f'{len(rows)} scores match; newest first:')
for d, stem, k, m, q, bars, n, names in rows[:mx]:
    print(f'  {d or "----------"}  {stem[:34]:34s} {k:5s} {m:5s} {q:10s} {bars:4d} bars  {n:2d} parts  {names}')
