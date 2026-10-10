"""GROUND-TRUTH BENCHMARK for key detection, using Brian's own filenames.

Hundreds of scores are titled "... in F minor" / "... in Db". That is a label written by the
composer, which makes it far better evidence than anything we could assert ourselves.

Enharmonics count as correct: D# minor and Eb minor are the same key, differently spelled.
Relative and parallel confusions are counted SEPARATELY, because they are the interesting failures.
"""
import os, re, json, collections
from music21 import converter, pitch

D = '/Users/bdogellis/Documents/Score Exports/MusicXML/'
TITLE = re.compile(r'\bin\s+([A-G][#b♯♭]?)\s*(major|minor|maj|min)?\b', re.I)

def norm(p):
    try:
        return pitch.Pitch(p.replace('b', '-') if len(p) > 1 and p[1] in 'b♭' else p.replace('♯', '#')).pitchClass
    except Exception:
        return None

rows, files = [], sorted(f for f in os.listdir(D) if f.endswith('.musicxml'))
for fn in files:
    m = TITLE.search(os.path.splitext(fn)[0])
    if not m:
        continue
    tonic, mode = m.group(1), (m.group(2) or '').lower()
    mode = 'minor' if mode.startswith('min') else ('major' if mode.startswith('maj') else None)
    rows.append({'file': fn, 'tonic': tonic, 'mode': mode})

print(f'{len(rows)} scores of {len(files)} declare a key in the filename\n')
res = collections.Counter(); detail = []
for r in rows:
    try:
        s = converter.parse(D + r['file'])
        k = s.analyze('key')
    except Exception:
        res['parse error'] += 1; continue
    got_pc, want_pc = k.tonic.pitchClass, norm(r['tonic'])
    got_mode = k.mode
    if want_pc is None:
        continue
    same_pc = got_pc == want_pc
    if r['mode'] is None:                      # title gave no mode -> judge tonic only
        res['tonic only: correct' if same_pc else 'tonic only: WRONG'] += 1
        cat = 'ok' if same_pc else 'wrong'
    elif same_pc and got_mode == r['mode']:
        res['exact'] += 1; cat = 'ok'
    elif same_pc:
        res['right tonic, WRONG MODE (parallel)'] += 1; cat = 'parallel'
    elif (r['mode'] == 'major' and got_mode == 'minor' and (want_pc - got_pc) % 12 == 3) or \
         (r['mode'] == 'minor' and got_mode == 'major' and (got_pc - want_pc) % 12 == 3):
        res['RELATIVE key confusion'] += 1; cat = 'relative'
    else:
        res['WRONG'] += 1; cat = 'wrong'
    detail.append({'file': r['file'], 'want': f"{r['tonic']} {r['mode'] or '?'}",
                   'got': f'{k.tonic.name} {got_mode}', 'cat': cat,
                   'conf': round(float(getattr(k, 'correlationCoefficient', 0) or 0), 3)})

n = sum(res.values())
print(f'{"outcome":<38}{"n":>6}{"%":>8}')
for k2, v in res.most_common():
    print(f'{k2:<38}{v:>6}{100*v/n:>7.1f}%')
strict = res['exact'] + res['tonic only: correct']
print(f'\nCORRECT (incl. enharmonic): {strict}/{n} = {100*strict/n:.1f}%')
json.dump(detail, open('bench_key_results.json', 'w'), indent=1)
print('\n--- a few genuine failures ---')
for d in [x for x in detail if x['cat'] in ('wrong', 'parallel', 'relative')][:12]:
    print(f"  {d['cat']:<9} want {d['want']:<11} got {d['got']:<11} conf {d['conf']}  {d['file'][:44]}")
