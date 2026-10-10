"""Unfinished piano pieces: one piano part, real music, then empty bars at the end of the score.
usage: python find_unfinished.py [since YYYY-MM-DD] [min_trailing_empty]"""
import os, re, sys, glob, time, datetime
E = '/Users/bdogellis/Documents/Score Exports'
since = sys.argv[1] if len(sys.argv) > 1 else '2018-09-01'
min_empty = int(sys.argv[2]) if len(sys.argv) > 2 else 3
MEAS = re.compile(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', re.S)
def piano_only(xml):
    parts = re.findall(r'<score-part id="[^"]+">(.*?)</score-part>', xml, re.S)
    if len(parts) != 1:
        return False
    name = re.search(r'<part-name>([^<]*)</part-name>', parts[0])
    staves = re.search(r'<staves>(\d+)</staves>', xml)
    return ('iano' in (name.group(1) if name else '')) or (staves and staves.group(1) == '2')
def date_of(stem):
    sib = os.path.join(E, '_source_sib', stem + '.sib')
    if os.path.exists(sib):
        return datetime.date.fromtimestamp(os.path.getmtime(sib)).isoformat()
    return None
rows = []
for f in sorted(glob.glob(os.path.join(E, 'MusicXML', '*.musicxml'))):
    xml = open(f, encoding='utf-8', errors='ignore').read()
    if not piano_only(xml):
        continue
    first_part = re.search(r'<part id="[^"]+">(.*?)</part>', xml, re.S)
    ms = MEAS.findall(first_part.group(1) if first_part else xml)
    if len(ms) < 12:
        continue
    has = [('<pitch>' in body) for _, body in ms]
    last = max((i for i, h in enumerate(has) if h), default=-1) + 1
    trailing = len(ms) - last
    notes = xml.count('<pitch>')
    stem = os.path.splitext(os.path.basename(f))[0]
    d = date_of(stem) or 'unknown'
    if trailing >= min_empty and last >= 8 and (d == 'unknown' or d >= since):
        rows.append((d, trailing, last, len(ms), notes, stem))
rows.sort(reverse=True)
print(f'unfinished piano pieces since {since} (last bar with notes / total bars, trailing empty bars):')
for d, tr, last, n, notes, stem in rows[:25]:
    print(f'  {d}  {stem:40s} notes to bar {last:4d} of {n:4d}  ({tr} empty at the end, {notes} notes)')
print('FOUND', len(rows))
