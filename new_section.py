"""Bars 17-21: a NEW SECTION, not more of the same.

Brian: "it's kinda just repeating the motifs. I think we need a new texture. Where do you think we
should go from here?"

The argument: bar 16 is the peak of an 8-bar tutti and bar 17 is a GRAND PAUSE. After a silence like
that, returning to the same tutti wastes it. The pause should read as the hinge between sections.

So:
  bar 17  the silence BREAKS with one low voice - cello and bass alone, pp, on Gb.
          Gb is bVI of Bb, a semitone above the F we were sitting on: distant, warm, and clearly
          a new world rather than a continuation.
  bar 18  horn alone takes the A-section motif (quarter, rest, two eighths) into the new key.
  bar 19  clarinet and bassoon join - three voices.
  bar 20  flute and oboe - five voices, the line rising.
  bar 21  strings enter sustained; the new texture is established and wants to keep growing.

Sparse -> building is the opposite of what came before, which is the point.
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
    return pitch.Pitch(concert).transpose(12 * oct_shift + SHIFT.get(part, 0)).nameWithOctave


E = [{'op': 'append_measures', 'count': 4, 'why': 'no bars exist past 17'}]


def put(bar, part, events, why, oc=0):
    E.append({'op': 'write_notes', 'measure': bar, 'part': part, 'staff': 1, 'voice': 1,
              'events': [e if e.startswith('r:') or e.startswith('{')
                         else f'{w(e.split(":")[0], part, oc)}:{e.split(":")[1]}' for e in events],
              'why': why})


# --- bar 17: the silence breaks. two voices, pp, nothing else. -------------------------------
put(17, 'Violoncello', ['G-2:4'], 'the pause breaks with one low voice on Gb - bVI, a semitone '
                                  'above the F we were sitting on, and a new world')
put(17, 'Contrabass', ['G-2:4'], 'doubling the cello an octave down; nothing else plays', oc=-1)

# --- bar 18: horn alone, the A-section motif in the new key ----------------------------------
put(18, 'Horn in F 1', ['B-4:1', 'r:1', 'r:1', 'G-4:0.5', 'D-5:0.5'],
    'the bar 1-8 motif returns ALONE in Gb - the same shape, a different world')

# --- bar 19: clarinet and bassoon join --------------------------------------------------------
put(19, 'Horn in F 1', ['D-5:1', 'r:1', 'r:1', 'B-4:0.5', 'G-4:0.5'], 'the motif continues')
put(19, 'Clarinet in Bb 1', ['G-4:2', 'D-4:2'], 'a second voice enters, sustained '
    '(Db not F - F is the leading tone of Gb and clashes against it)')
put(19, 'Bassoon 1', ['D-3:4'], 'bass support arrives under the horn')

# --- bar 20: flute and oboe, the line rising ---------------------------------------------------
put(20, 'Horn in F 1', ['G-4:1', 'r:1', 'r:1', 'D-5:0.5', 'F5:0.5'], 'the motif rises')
put(20, 'Clarinet in Bb 1', ['B-4:2', 'A-4:2'], 'inner voice')
put(20, 'Bassoon 1', ['G-2:4'], 'bass')
put(20, 'Flute 1', ['D-6:2', 'B-5:2'], 'flute enters high and quiet - the texture opens '
    'upward (Bb not Cb, which would sit a semitone under the oboe)')
put(20, 'Oboe 1', ['B-5:4'], 'oboe sustains against the flute')

# --- bar 21: strings enter; the new texture is established -------------------------------------
put(21, 'Horn in F 1', ['D-5:1', 'r:1', 'r:1', 'B-4:0.5', 'G-4:0.5'], 'the motif settles '
    '(Db not F - F clashed against the Gb in clarinet, oboe and viola)')
put(21, 'Clarinet in Bb 1', ['G-4:4'], 'sustained')
put(21, 'Bassoon 1', ['B-2:4'], 'bass moves to Bb - the pull home begins')
put(21, 'Flute 1', ['B-5:4'], 'held')
put(21, 'Oboe 1', ['G-5:4'], 'held')
put(21, 'Violin I', ['D-5:4'], 'strings enter sustained - the new section is established')
put(21, 'Violin II', ['B-4:4'], 'strings')
put(21, 'Viola', ['G-4:4'], 'strings')
put(21, 'Violoncello', ['D-4:4'], 'strings')

out = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/edits_new.json'
json.dump(E, open(out, 'w'), indent=1)
print(f'{len(E)} ops -> {out}')
