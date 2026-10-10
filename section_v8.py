"""Bars 17-21, generated FROM BRIAN'S OWN CORPUS rather than from theory.

Six drafts composed from principles were dead. This one is different in kind: the melody was not
invented, it was RETRIEVED - the last five notes of his own flute line were used as a seed, every
place in his 1,607 scores where that exact shape and rhythm occurs was found, and what he actually
wrote next was stitched together. Four fragments, from `72816` and `10 1 16 no2`.

The line climbs an octave then circles around Bb6 with a chromatic E natural - a shape I would not
have produced and would not have chosen. That is the point.

Harmony follows the MELODY (Bb with a flat 7) instead of the melody following my harmonic plan.
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


def _conv(e, part, oc):
    if e.startswith('{'):
        head, body = e.split(' ', 1)
        return head + ' ' + ' '.join(
            f'{w(t.split(":")[0], part, oc)}:{t.split(":")[1]}'
            for t in body.rstrip('}').split()) + '}'
    if e.startswith('r:'):
        return e
    return f'{w(e.split(":")[0], part, oc)}:{e.split(":")[1]}'


E = [{'op': 'append_measures', 'count': 4, 'why': 'no bars past 17'}]


def put(bar, part, ev, why, oc=0):
    E.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
              'events': [_conv(e, part, oc) for e in ev], 'why': why})


# ---- THE RETRIEVED MELODY (concert pitch) ----------------------------------------------------
# The retrieved fragment begins on A5 - the leading tone - because the seed ended there. A is a
# PICKUP, not a downbeat; landing it simultaneously with the motor's Bb is a real clash. Start the
# bar on Bb and let the octave rise complete instead.
MEL = {18: ['B-5:0.5', 'C6:0.5', 'D6:0.5', 'E-6:0.5', 'F6:0.5', 'G6:0.5', 'A-6:0.5', 'B-6:0.5'],
       19: ['B-6:0.5', 'A-6:0.5', 'G6:0.5', 'F6:0.5', 'E-6:0.5', 'F6:0.5', 'B-6:0.5', 'A-6:0.5'],
       20: ['G6:0.5', 'F6:0.5', 'E-6:0.5', 'F6:0.5', 'B-6:1', 'A-6:1'],
       21: ['G6:1', 'F6:0.5', 'E-6:0.5', 'D6:1', 'B-5:1']}
MEL_PARTS = [('Flute 1', 0), ('Flute 2', -1), ('Violin I', 0), ('Violin II', -1)]

# ---- harmony implied BY the melody: Bb with a flat 7 -> Eb -> Bb -> F --------------------------
#      Bb=Bb D F   Eb=Eb G Bb   F=F A C
CH = {17: ('B-4', 'F4', 'D4'), 18: ('B-4', 'F4', 'D4'), 19: ('B-4', 'G4', 'E-4'),
      20: ('B-4', 'F4', 'D4'), 21: ('C5', 'A4', 'F4')}
MOTOR = [('Clarinet in Bb 1', 0, 0), ('Clarinet in Bb 2', 1, 0), ('Bass Clarinet in Bb', 2, -1),
         ('Horn in F 1', 0, 0), ('Horn in F 2', 1, 0), ('Horn in F 3', 2, 0), ('Viola', 1, 0)]
BASS = {17: 'B-2', 18: 'B-2', 19: 'E-2', 20: 'B-2', 21: 'F2'}
BASS_PARTS = [('Bassoon 2', 0), ('Bass Trombone', 0), ('Tuba', 0), ('Contrabass', -1)]
MOTIF = {20: ['D5:1', 'r:1', 'r:1', 'B-4:0.5', 'F5:0.5'],
         # no A here: the melody is on Bb at that moment and A attacks against it
         21: ['C5:1', 'r:1', 'r:1', 'F4:0.5', 'C5:0.5']}
MOTIF_PARTS = [('Oboe 1', 0), ('Trumpet in Bb 1', 0), ('Trombone 1', -1), ('Bassoon 1', -1)]

for bar in (17, 18, 19, 20, 21):
    tones = CH[bar]
    for part, idx, oc in MOTOR:
        a = tones[idx]
        put(bar, part, [f'{{3:2 {a}:1 {a}:1 {a}:1}}', f'{{3:2 {a}:1 {a}:1 {a}:1}}'],
            'the sextuplet motor never stops - bar 17 is a dynamic collapse, not a hole', oc)
    if bar >= 18:
        for part, oc in MEL_PARTS:
            put(bar, part, MEL[bar],
                'the melody, RETRIEVED from your own scores (72816 and 10 1 16 no2) rather than '
                'invented - it climbs an octave then circles around Bb6', oc)
        for part, oc in BASS_PARTS:
            put(bar, part, [f'{BASS[bar]}:4'], 'bass follows the melody: Bb - Eb - Bb - F', oc)
    if bar in MOTIF:
        for part, oc in MOTIF_PARTS:
            put(bar, part, MOTIF[bar], 'your bar 1-8 motif returns after two bars away', oc)

# ---- PHRASING. 136 slurs in his eight bars, zero in my four - that alone is most of why it did
# not flow. His rules, read off the score:
#   running-eighth melodic lines : ONE slur per bar, downbeat to the last note
#   the motif                    : slur from the two-eighth pickup ACROSS the barline into the
#                                  next downbeat - "eighth notes on the final beat resolving to a
#                                  quarter note of the first beat of the measure"
#   the sextuplet motor          : no slurs
MEL_LEN = {18: 8, 19: 8, 20: 6, 21: 5}
for bar, n in MEL_LEN.items():
    for part, oc in MEL_PARTS:
        E.append({'op': 'add_slur', 'measure': bar, 'from_index': 0, 'to_index': n - 1,
                  'part': part, 'staff': 1, 'voice': 1,
                  'why': 'one slur across the bar, the way you phrase a running line'})
# the motif's pickup slurs into the NEXT bar's downbeat
for part, oc in MOTIF_PARTS:
    E.append({'op': 'add_slur', 'measure': 20, 'from_index': 1, 'to_index': 0, 'to_measure': 21,
              'part': part, 'staff': 1, 'voice': 1,
              'why': 'the two eighths on beat 4 are a PICKUP - slurred over the barline into the '
                     'next downbeat, exactly as in your bars 13-16'})

for bar, dyn in ((17, 'pp'), (18, 'mp'), (20, 'mf'), (21, 'f')):
    E.append({'op': 'add_dynamic', 'measure': bar, 'part': 'Clarinet in Bb 1', 'value': dyn,
              'why': 'the shape is made by dynamics, the way you do it'})

out = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/edits_v8.json'
json.dump(E, open(out, 'w'), indent=1)
print(f'{len(E)} ops -> {out}')
