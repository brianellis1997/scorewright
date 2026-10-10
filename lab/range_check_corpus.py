"""Calibrate ranges.py against Brian's own scores: a textbook table should flag ~nothing in
finished, played music. Anything it flags a lot is a table or part-name problem, not his."""
import sys, glob, random, collections, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import ranges
from music21 import converter
files = sorted(glob.glob('/Users/bdogellis/Documents/Score Exports/MusicXML/*.musicxml'))
random.seed(1); files = random.sample(files, 250)
viol = collections.Counter(); notes = collections.Counter(); unknown = collections.Counter(); ex = {}
for i, f in enumerate(files):
    try:
        s = converter.parse(f).toSoundingPitch()
    except Exception:
        continue
    for p in s.parts:
        r = ranges.range_of(p.partName)
        if r is None:
            unknown[p.partName] += 1; continue
        k = p.partName
        for n in p.recurse().notes:
            for q in n.pitches:
                notes[k] += 1
                if q.midi < r[0] or q.midi > r[1]:
                    viol[k] += 1; ex.setdefault(k, (f.split('/')[-1][:40], q.midi))
    if (i + 1) % 50 == 0:
        print(f'{i+1}/{len(files)}', flush=True)
print('\nVIOLATIONS by part (rate, count, example score, midi):')
for k, v in viol.most_common(25):
    print(f'  {k:28s} {100*v/notes[k]:5.1f}%  {v:5d}/{notes[k]:<6d} {ex[k]}')
print('\nUNKNOWN part names (no range):', unknown.most_common(20))
print('RANGE_CHECK_DONE')
