"""Bars 18-21 of `Orchestral Idea`, written by hand in CONCERT pitch, transposed by code.

Harmony: Bb (I) -> Eb (IV) -> Cm (ii) -> F (V).  It ends ON THE DOMINANT so the phrase stays open
and demands a bar 22 - continuing, not concluding.

All four of bar 16's layers keep running:
  A  running eighths   Fl 1/2, Vln I/II, Vc
  B  the quarter-rest-rest-two-eighths motif   Ob 1/2, Bsn 1/2, Tpt 1/2, Tbn 1/2
  C  sextuplet motor   Cl 1/2, BsCl, Hn 1-4, Vla
  D  sustained bass    BTbn, Tuba, Cb   (Brian's own m16 pattern, hole and all)
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


def w(concert, part, oct_shift=0):
    """concert pitch -> the pitch to WRITE for `part`."""
    p = pitch.Pitch(concert).transpose(12 * oct_shift + SHIFT.get(part, 0))
    return p.nameWithOctave.replace('-', '-')


# ---- layer A: running eighths, the melodic line -------------------------------------------
# NO Ab in the melody. Layer C holds G through bars 19-20, and a passing Ab against a sustained
# G is a harsh semitone that Brian heard immediately ("some off pitches"). Diatonic is not the same
# as consonant against what is actually sounding underneath.
A = {18: ['r:0.5', 'B-5', 'A5', 'G5', 'A5', 'G5', ('F5', 1)],
     19: ['r:0.5', 'E-6', 'D6', 'C6', 'D6', 'C6', ('B-5', 1)],
     20: ['r:0.5', 'D6', 'C6', 'B-5', 'C6', 'B-5', ('G5', 1)],
     21: ['r:0.5', 'C6', 'B-5', 'A5', 'B-5', 'A5', ('G5', 1)]}
A_PARTS = [('Flute 1', 0), ('Flute 2', -1), ('Violin I', 0), ('Violin II', -1),
           ('Violoncello', -2)]

# ---- layer B: the motif --------------------------------------------------------------------
B = {18: ['D5', 'r', 'r', 'B-4', 'F5'], 19: ['E-5', 'r', 'r', 'G4', 'B-4'],
     20: ['E-5', 'r', 'r', 'C5', 'G5'], 21: ['F5', 'r', 'r', 'A4', 'C5']}
B_PARTS = [('Oboe 1', 0), ('Oboe 2', -1), ('Trumpet in Bb 1', 0), ('Trumpet in Bb 2', -1),
           ('Trombone 1', -1), ('Trombone 2', -2), ('Bassoon 1', -1), ('Bassoon 2', -2)]

# ---- layer C: sextuplet motor, one chord tone each ------------------------------------------
C_TONE = {18: {'a': 'B-4', 'b': 'F4', 'c': 'D4', 'end': 'A4'},
          19: {'a': 'B-4', 'b': 'G4', 'c': 'E-4', 'end': 'G4'},
          20: {'a': 'C5', 'b': 'G4', 'c': 'E-4', 'end': 'C5'},
          21: {'a': 'C5', 'b': 'A4', 'c': 'F4', 'end': 'A4'}}
C_PARTS = [('Clarinet in Bb 1', 'a', 0), ('Clarinet in Bb 2', 'b', 0),
           ('Bass Clarinet in Bb', 'c', -1), ('Horn in F 1', 'a', 0), ('Horn in F 2', 'b', 0),
           ('Horn in F 3', 'c', 0), ('Horn in F 4', 'c', -1), ('Viola', 'b', 0)]

# ---- layer D: sustained bass ----------------------------------------------------------------
D = {18: 'B-2', 19: 'E-2', 20: 'C2', 21: 'F2'}
D_PARTS = [('Bass Trombone', 0), ('Tuba', 0), ('Contrabass', -1)]

edits = [{'op': 'append_measures', 'count': 4,
          'why': 'the piece has no bars past 17 to continue into'}]

for bar in (18, 19, 20, 21):
    for part, oc in A_PARTS:
        ev = []
        for tok in A[bar]:
            if tok == 'r:0.5':
                ev.append('r:0.5')
            elif isinstance(tok, tuple):
                ev.append(f'{w(tok[0], part, oc)}:{tok[1]}')
            else:
                ev.append(f'{w(tok, part, oc)}:0.5')
        edits.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
                      'events': ev, 'why': 'running eighths - layer A keeps the motion alive'})
    for part, oc in B_PARTS:
        ev = [f'{w(B[bar][0], part, oc)}:1', 'r:1', 'r:1',
              f'{w(B[bar][3], part, oc)}:0.5', f'{w(B[bar][4], part, oc)}:0.5']
        edits.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
                      'events': ev, 'why': 'the m1-8 motif, quarter + two eighths'})
    for part, tone, oc in C_PARTS:
        a = w(C_TONE[bar][tone], part, oc)
        e = w(C_TONE[bar]['end'], part, oc)
        edits.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
                      'events': [f'{{3:2 {a}:1 {a}:1 {a}:1}}', f'{{3:2 {a}:1 {a}:1 {e}:1}}'],
                      'why': 'sextuplet motor - the layer that must not stop'})
    for part, oc in D_PARTS:
        edits.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
                      'events': [f'{w(D[bar], part, oc)}:1', 'r:1', 'r:2'],
                      'why': 'sustained bass, as in m16'})

out = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/edits.json'
json.dump(edits, open(out, 'w'), indent=1)
print(f'{len(edits)} ops -> {out}')
