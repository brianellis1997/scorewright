"""Corpus-wide token statistics for the compact cache. Measured, never estimated."""
import os, json, statistics as st
import tiktoken

CD = '/Users/bdogellis/Documents/Score Exports/compact'
MD = os.path.join(CD, '_meta')
XD = '/Users/bdogellis/Documents/Score Exports/MusicXML'
enc = tiktoken.get_encoding('cl100k_base')

rows = []
for f in sorted(os.listdir(MD)):
    if not f.endswith('.json'):
        continue
    m = json.load(open(os.path.join(MD, f)))
    stem = f[:-5]
    txt = os.path.join(CD, stem + '.txt')
    if not os.path.exists(txt):
        continue
    t = len(enc.encode(open(txt).read()))
    xml = os.path.join(XD, m['source'])
    xb = os.path.getsize(xml) if os.path.exists(xml) else 0
    rows.append({'stem': stem, 'tok': t, 'parts': m['n_parts'], 'meas': m['n_measures'],
                 'notes': m['n_notes'], 'xml_bytes': xb, 'key': m.get('key_detected'),
                 'secs': m.get('parse_seconds', 0)})

json.dump(rows, open(os.path.join(CD, '_stats.json'), 'w'))
toks = sorted(r['tok'] for r in rows)
print(f'scores        : {len(rows)}')
print(f'total tokens  : {sum(toks):,}')
print(f'median        : {int(st.median(toks)):,}')
print(f'mean          : {int(st.mean(toks)):,}')
print(f'p90 / p99     : {toks[int(len(toks)*.9)]:,} / {toks[int(len(toks)*.99)]:,}')
print(f'max           : {toks[-1]:,}')
print(f'parse time    : {sum(r["secs"] for r in rows)/60:.1f} min total')
print()
BUCKETS = [('solo (1)',1,1), ('duo-trio (2-3)',2,3), ('chamber (4-8)',4,8),
           ('ensemble (9-19)',9,19), ('orchestral (20+)',20,999)]
print(f'{"category":<18}{"n":>6}{"median tok":>12}{"max tok":>12}{"median %XML":>14}')
for name, lo, hi in BUCKETS:
    g = [r for r in rows if lo <= r['parts'] <= hi]
    if not g: continue
    ts = sorted(r['tok'] for r in g)
    # % of the raw MusicXML byte size the compact form occupies
    ratios = [100.0*len(open(os.path.join(CD, r['stem']+'.txt')).read())/r['xml_bytes']
              for r in g if r['xml_bytes'] > 0]
    print(f'{name:<18}{len(g):>6}{int(st.median(ts)):>12,}{ts[-1]:>12,}'
          f'{st.median(ratios):>13.1f}%')
print()
print('fits in a 200k window :', f"{sum(1 for t in toks if t<=200_000)}/{len(toks)}",
      f"({100*sum(1 for t in toks if t<=200_000)/len(toks):.1f}%)")
print('fits in a 1M window   :', f"{sum(1 for t in toks if t<=1_000_000)}/{len(toks)}",
      f"({100*sum(1 for t in toks if t<=1_000_000)/len(toks):.1f}%)")
print()
print('LARGEST 5:')
for r in sorted(rows, key=lambda r:-r['tok'])[:5]:
    print(f'  {r["tok"]:>9,} tok  {r["parts"]:>3}p {r["meas"]:>6}m  {r["stem"][:52]}')
