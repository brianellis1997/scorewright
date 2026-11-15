"""111326 S20 (Nov 15 2026): S19 after Brian's notes on the strings: "the violin one runs... should
be slurred... a flowing texture... the violin playing detache up that run just doesn't make
sense... violin two is playing higher than violin one in that moment, and then they cross again...
that just doesn't make sense from a school writing perspective... from the violin one perspective,
to go from that high B all the way down more than an octave to a lower A is just kind of awkward".
- The strings keep their order all through bars 49-52: Violin I, then Violin II, then the violas
  (whose chord tops are B and C sharp in bars 50-52); no part crosses the one above it.
- Violin I leaves his theme's B5 by step: a slurred run down A, G, F, E on beat 1 of bar 49, then
  pulses C (bar 49), D (bar 50), B (bar 51), and runs up, slurred, from bar 51 beat 2 into his
  C sharp on beat 2 of bar 52.
- Violin II leaves its B4 by step to A, then pulses B (bars 50-51) and C sharp (bar 52), never
  below the violas' top note, and arrives on the C sharp of the melody the octave below.
Everything else is S18.
usage (whisperer env): python lab/pieces/p111326_s20.py <working.xml> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s18 as s18  # noqa: E402
from p111326_s15 import beam16  # noqa: E402

VIOLIN_I = {49: [('A5', 1, None), ('G5', 1, None), ('F5', 1, None), ('E5', 1, None), ('C5', 2, None), ('C5', 2, None)],
            50: [('D5', 2, None)] * 4,
            51: [('B4', 2, None), ('B4', 2, None), ('B4', 1, None), ('C#5', 1, None), ('D5', 1, None), ('E5', 1, None)],
            52: [('F#5', 1, None), ('G#5', 1, None), ('A5', 1, None), ('B5', 1, None)]}
VIOLIN_II = {49: [('A4', 2, None)] * 4, 50: [('B4', 2, None)] * 4, 51: [('B4', 2, None)] * 4,
             52: [('C#5', 2, None), ('C#5', 2, None), ('C#5', 4, None)]}
SLURS = [('P28', (49, 0), (49, 0.75)), ('P28', (51, 1.0), (52, 0.75))]

base = getattr(s18, 'lines_s18', s18.lines)
s18.lines_s18 = base


def lines():
    out = []
    for l in base():
        pid, staff, bar, onset, bars = l
        if pid == 'P28':
            bars = {**bars, **VIOLIN_I}
        elif pid == 'P29':
            bars = {**bars, **VIOLIN_II}
        out.append((pid, staff, bar, onset, bars))
    return out


s18.lines = lines
write_line, notes, harp_48, viola_49, respell_56 = s18.write_line, s18.notes, s18.harp_48, s18.viola_49, s18.respell_56
HARP_CHORD, VIOLA_49, BRASS_SLURS, RUN_SLURS, MELODY_SLURS, PAD_PARTS, ACCENTS = (
    s18.HARP_CHORD, s18.VIOLA_49, s18.BRASS_SLURS, s18.RUN_SLURS, s18.MELODY_SLURS, s18.PAD_PARTS, s18.ACCENTS)


def build(x):
    from xml_marks import Marks
    y = s18.build(x)
    for b in (49, 51, 52):
        y = beam16(y, 'P28', b)
    m = Marks(y)
    for pid, a, z in SLURS:
        m.slur(pid, a, z, number=2)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
