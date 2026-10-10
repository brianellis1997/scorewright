"""Bars 17-21, third attempt - built from what the piece already IS.

What I missed twice: the A section's own melody is Eb6 - C6 - **Gb6**, and the bass alternates
F# against F natural. The Bb/Gb pull is not exotic, it IS this piece. Treating bVI as a foreign
arrival was why it sounded jarring AND unrelated at the same time.

Also: he never stops the motion. Every continuation in his corpus keeps a line moving and shapes it
with hairpins. So the "pause" is a DYNAMIC COLLAPSE, not a hole - the motor keeps turning at pp.

  17  motor ALONE at pp - clarinets, horns, viola keep the sextuplets, everything else drops out.
      Motion continues; the tutti simply falls away. That is the transition.
  18  Gb finally ARRIVES as a plateau rather than an oscillation. mp. A new long-breathed melody
      enters over the continuing motor - stepwise, continuous eighths.
  19  the melody sequences up; still Gb.
  20  Eb minor - the line turns and starts descending. cresc.
  21  F7 - the dominant returns, so it points home. f. Open, wanting bar 22.

New: a four-bar melodic arc instead of a repeated one-bar cell, and the brass motif drops out for
two bars so its return in 20-21 means something.
"""
import json, re
import xmledit as x
from music21 import pitch

RAW = open('/Users/bdogellis/Documents/Score Exports/MusicXML/Orchestral Idea.musicxml').read()
SHIFT = {}
for i, _pid, name, lo, hi in x.parts(RAW):
    m = re.search(r'<transpose>[\s\S]*?</transpose>', RAW[lo:hi])
    s = 0
    if m:
        ch = re.search(r'<chromatic>(-?\d+)</chromatic>', m.group(0))
        oc = re.search(r'<octave-change>(-?\d+)</octave-change>', m.group(0))
        s = -((int(ch.group(1)) if ch else 0) + 12 * (int(oc.group(1)) if oc else 0))
    SHIFT[name] = s
def w(c, part, oc=0):
    return pitch.Pitch(c).transpose(12 * oc + SHIFT.get(part, 0)).nameWithOctave

E = [{'op': 'append_measures', 'count': 4, 'why': 'no bars past 17'}]
def put(bar, part, ev, why, oc=0):
    E.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
              'events': [e if e.startswith(('r:', '{')) else
                         (('{3:2 ' + ' '.join(f'{w(t.split(":")[0], part, oc)}:{t.split(":")[1]}'
                                              for t in e[5:-1].split()) + '}')
                          if e.startswith('{3:2') else
                          f'{w(e.split(":")[0], part, oc)}:{e.split(":")[1]}') for e in ev],
              'why': why})

# ---- the melody: ONE four-bar arc, stepwise, continuous eighths -------------------------------
MEL = {18: ['r:0.5', 'B-5:0.5', 'A-5:0.5', 'G-5:0.5', 'A-5:0.5', 'B-5:0.5', 'D-6:1'],
       19: ['r:0.5', 'E-6:0.5', 'D-6:0.5', 'C-6:0.5', 'D-6:0.5', 'E-6:0.5', 'G-6:1'],
       20: ['G-6:1', 'F6:0.5', 'E-6:0.5', 'D-6:0.5', 'C-6:0.5', 'B-5:1'],
       21: ['A-5:1', 'G-5:0.5', 'F5:0.5', 'E-5:0.5', 'D-5:0.5', 'C5:1']}
MEL_PARTS = [('Flute 1', 0), ('Flute 2', -1), ('Violin I', 0), ('Violin II', -1)]

# ---- the motor: sextuplets, unbroken from bar 16 through bar 21 -------------------------------
MOTOR = {17: {'a': 'B-4', 'b': 'G-4', 'c': 'E-4'},
         18: {'a': 'B-4', 'b': 'G-4', 'c': 'D-4'},
         19: {'a': 'D-5', 'b': 'B-4', 'c': 'G-4'},
         20: {'a': 'B-4', 'b': 'G-4', 'c': 'E-4'},
         21: {'a': 'C5',  'b': 'A-4', 'c': 'E-4'}}
MOTOR_PARTS = [('Clarinet in Bb 1', 'a', 0), ('Clarinet in Bb 2', 'b', 0),
               ('Bass Clarinet in Bb', 'c', -1), ('Horn in F 1', 'a', 0),
               ('Horn in F 2', 'b', 0), ('Horn in F 3', 'c', 0), ('Viola', 'b', 0)]

# ---- bass: a slow stepwise descent under it all ------------------------------------------------
BASS = {17: 'G-2', 18: 'G-2', 19: 'D-2', 20: 'E-2', 21: 'F2'}
BASS_PARTS = [('Bassoon 2', 0), ('Bass Trombone', 0), ('Tuba', 0), ('Contrabass', -1)]

# ---- the brass motif: SILENT in 18-19, returns in 20-21 so the return means something ----------
MOTIF = {20: ['E-5:1', 'r:1', 'r:1', 'C-5:0.5', 'G-5:0.5'],
         21: ['C5:1',  'r:1', 'r:1', 'A-4:0.5', 'E-5:0.5']}
MOTIF_PARTS = [('Oboe 1', 0), ('Trumpet in Bb 1', 0), ('Trombone 1', -1), ('Bassoon 1', -1)]

for bar in (17, 18, 19, 20, 21):
    t = MOTOR[bar]
    for part, tone, oc in MOTOR_PARTS:
        a = t[tone]
        put(bar, part, [f'{{3:2 {a}:1 {a}:1 {a}:1}}', f'{{3:2 {a}:1 {a}:1 {a}:1}}'],
            'the sextuplet motor never stops - bar 17 is a dynamic collapse, not a hole', oc)
    if bar >= 18:
        for part, oc in MEL_PARTS:
            put(bar, part, MEL[bar], 'one four-bar melodic arc, stepwise and continuous', oc)
        for part, oc in BASS_PARTS:
            put(bar, part, [f'{BASS[bar]}:4'], 'slow stepwise bass: Gb - Gb - Db - Eb - F', oc)
    if bar in MOTIF:
        for part, oc in MOTIF_PARTS:
            put(bar, part, MOTIF[bar], 'your bar 1-8 motif returns after two bars away', oc)

for bar, dyn in ((17, 'pp'), (18, 'mp'), (20, 'mf'), (21, 'f')):
    E.append({'op': 'add_dynamic', 'measure': bar, 'part': 'Clarinet in Bb 1', 'value': dyn,
              'why': 'the shape is made by dynamics, the way you do it'})

out = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/edits_v3.json'
json.dump(E, open(out, 'w'), indent=1)
print(f'{len(E)} ops -> {out}')
