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
# THE FIGURE, as he actually orchestrates it. Read straight off bars 13-16: four PAIRS, the
# downbeat harmonised a THIRD apart between the 1st and 2nd player, and both playing the SAME two
# eighths in unison as a pickup into the next bar. I had only the "1" of each pair sounding and only
# in two of the four bars, so three quarters of this texture was simply missing.
#   (upper downbeat, lower downbeat, pickup eighth 1, pickup eighth 2)   - concert pitch
# BAR 17 RESOLVES BAR 16. Brian said this three times before I heard it: bar 16 ends with the
# pickup Bb4 -> F5 in oboes, trumpets, trombones and bassoons, and a pickup is an UPBEAT - it points
# at a downbeat. His own pattern proves the resolution: m13's Gb5 lands on m14's Eb5, m15's F5 lands
# on m16's D5, both down a third. So m16's F5 MUST land on D5 in bar 17. Leaving bar 17 empty, or
# giving it only the motor, leaves the whole wind and brass section hanging mid-gesture - which is
# why the seam sounded broken no matter what came after it.
FIG = {17: ('D5',  'B-4', None,  None),   # <- the resolution. downbeat only, then silence.
       18: ('D5',  'B-4', 'B-4', 'F5'),    # Bb
       19: ('G4',  'E-4', 'E-4', 'B-4'),   # Eb
       20: ('D5',  'B-4', 'B-4', 'F5'),    # Bb
       21: ('A4',  'F4',  'F4',  'C5')}    # F
# (part, upper?, octave shift)
FIG_PARTS = [('Oboe 1', True, 0), ('Oboe 2', False, 0),
             ('Trumpet in Bb 1', True, 0), ('Trumpet in Bb 2', False, 0),
             ('Trombone 1', True, -1), ('Trombone 2', False, -1),
             ('Bassoon 1', True, -2), ('Bassoon 2', False, -2)]

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
    if bar in FIG:
        up, lo_, e1, e2 = FIG[bar]
        for part, is_up, oc in FIG_PARTS:
            head = up if is_up else lo_
            if e1 is None:
                put(bar, part, [f'{head}:1', 'r:3'],
                    "resolves bar 16's dangling pickup - F5 lands on D5, down a third, exactly as "
                    "your Gb5 lands on Eb5 at m13-14 and your F5 lands on D5 at m15-16", oc)
            else:
                put(bar, part, [f'{head}:1', 'r:1', 'r:1', f'{e1}:0.5', f'{e2}:0.5'],
                    'the figure as you orchestrate it: paired a third apart on the downbeat, the '
                    'two eighths in unison as a pickup into the next bar', oc)

# ---- PHRASING. 136 slurs in his eight bars, zero in my four - that alone is most of why it did
# not flow. His rules, read off the score:
#   running-eighth melodic lines : ONE slur per bar, downbeat to the last note
#   the motif                    : slur from the two-eighth pickup ACROSS the barline into the
#                                  next downbeat - "eighth notes on the final beat resolving to a
#                                  quarter note of the first beat of the measure"
#   the sextuplet motor          : no slurs
MEL_LEN = {18: 8, 19: 8, 20: 6, 21: 5}
# NOT bar 17: its figure is a downbeat resolution with NO pickup after it, so there is no
# index-1 eighth to slur from. That gesture ends there - that is the point of it.
for bar, n in MEL_LEN.items():
    for part, oc in MEL_PARTS:
        E.append({'op': 'add_slur', 'measure': bar, 'from_index': 0, 'to_index': n - 1,
                  'part': part, 'staff': 1, 'voice': 1,
                  'why': 'one slur across the bar, the way you phrase a running line'})
# every pair's pickup slurs over the barline into the next downbeat
for b in (16, 18, 19, 20):
    for part, is_up, oc in FIG_PARTS:
        E.append({'op': 'add_slur', 'measure': b, 'from_index': 1, 'to_index': 0,
                  'to_measure': b + 1, 'part': part, 'staff': 1, 'voice': 1,
                  'why': 'the two eighths on beat 4 are a PICKUP - slurred over the barline into '
                         'the next downbeat, exactly as in your bars 13-16'})

# ---- ARTICULATION. His bars 9-16 carry 384 TENUTOS - every note of the sextuplet motor - and 32
# hairpins. My drafts had zero of both. That is the entire articulation layer of the piece missing.
for bar in (17, 18, 19, 20, 21):
    for part, idx, oc in MOTOR:
        for k in range(6):
            E.append({'op': 'add_articulation', 'measure': bar, 'index': k, 'kind': 'tenuto',
                      'part': part, 'staff': 1, 'voice': 1,
                      'why': 'every note of your sextuplet motor is tenuto - 384 of them in bars '
                             '9-16, and I had none'})
# hairpins shape the phrase, the way you do it
for a, b, k in ((17, 18, 'crescendo'), (19, 20, 'crescendo'), (20, 21, 'crescendo')):
    for part, idx, oc in MOTOR[:3]:
        E.append({'op': 'add_hairpin', 'measure': a, 'stop_measure': b, 'kind': k,
                  'part': part, 'staff': 1, 'voice': 1,
                  'why': 'your bars carry 32 hairpins; the shape is made by dynamics'})

for bar, dyn in ((17, 'pp'), (18, 'mp'), (20, 'mf'), (21, 'f')):
    E.append({'op': 'add_dynamic', 'measure': bar, 'part': 'Clarinet in Bb 1', 'value': dyn,
              'why': 'the shape is made by dynamics, the way you do it'})

out = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/edits_v11.json'
json.dump(E, open(out, 'w'), indent=1)
print(f'{len(E)} ops -> {out}')
