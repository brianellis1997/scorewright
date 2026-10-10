"""How much of the MusicXML does the compact encoding actually keep? Measured on a random sample."""
import os, random, collections, json
from music21 import converter, note, chord, dynamics, spanner, meter, key, tempo

D = '/Users/bdogellis/Documents/Score Exports/MusicXML/'
files = sorted(f for f in os.listdir(D) if f.endswith('.musicxml'))
random.seed(7)
sample = random.sample(files, 120)

tot = collections.Counter(); n_with = collections.Counter(); ok = 0
for fn in sample:
    try:
        s = converter.parse(D + fn)
    except Exception:
        continue
    r = s.recurse()
    f = {
      'ties':        sum(1 for n in r.notes if getattr(n, 'tie', None)),
      'slurs':       len(r.getElementsByClass(spanner.Slur)),
      'wedges':      len(r.getElementsByClass(dynamics.DynamicWedge)),
      'dynamics':    len(r.getElementsByClass(dynamics.Dynamic)),
      'articulations': sum(len(n.articulations) for n in r.notes),
      'expressions': sum(len(n.expressions) for n in r.notes),
      'tuplets':     sum(1 for n in r.notes if n.duration.tuplets),
      'grace':       sum(1 for n in r.notes if n.duration.isGrace),
      'timesig>1':   max(0, len(r.getElementsByClass(meter.TimeSignature)) - 1),
      'keysig>1':    max(0, len(r.getElementsByClass(key.KeySignature)) - 1),
      'tempo':       len(r.getElementsByClass(tempo.MetronomeMark)),
      'VOICES':      len(r.getElementsByClass('Voice')),
    }
    for k, v in f.items():
        tot[k] += v
        if v: n_with[k] += 1
    ok += 1

KEPT = {'articulations': 'kept (on the note)', 'dynamics': 'kept BUT POSITION LOST',
        'tuplets': 'duration kept, notation lost', 'VOICES': 'would be LOST if present'}
print(f'sampled {ok} scores of {len(files)}\n')
print(f'{"feature":<16}{"total":>9}{"scores w/ it":>14}{"% of scores":>12}   status')
for k, v in sorted(tot.items(), key=lambda x: -x[1]):
    print(f'{k:<16}{v:>9,}{n_with[k]:>14}{100*n_with[k]/ok:>11.0f}%   {KEPT.get(k, "*** LOST ***")}')
