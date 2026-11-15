"""111326 S19 (Nov 14 2026): S18 with a fluid hand-off. Brian: "when the violins are taking over the
melody from the trumpets... the violin one literally goes up like an octave. It needs to be a fluid
transition, maybe a sextuplet run or some type of thing, to make it a more natural transition."
- Violin I runs up a scale in sixteenths from bar 51, beat 2: B, C sharp, D, E (over E minor), then
  F sharp, G sharp, A, B (over A), into his C sharp on beat 2 of bar 52, while the flute's run falls
  the other way into the same C sharp. (Sixteenths: Dorico's tuplet input is not tested yet.)
- Violin II steps up A, B into its C sharp, the octave below.
Everything else is S18.
usage (whisperer env): python lab/pieces/p111326_s19.py <working.xml> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s18 as s18  # noqa: E402
from p111326_s15 import beam16  # noqa: E402

RUN = {51: [('B4', 2, None), ('B4', 2, None), ('B4', 1, None), ('C#5', 1, None), ('D5', 1, None), ('E5', 1, None)],
       52: [('F#5', 1, None), ('G#5', 1, None), ('A5', 1, None), ('B5', 1, None)]}
STEP = {52: [('A4', 2, None), ('B4', 2, None), ('C#5', 4, None)]}


def lines():
    out = []
    for l in s18.lines_s18():
        pid, staff, bar, onset, bars = l
        if pid == 'P28':
            bars = {**bars, **RUN}
        elif pid == 'P29':
            bars = {**bars, **STEP}
        out.append((pid, staff, bar, onset, bars))
    return out


s18.lines_s18 = s18.lines
s18.lines = lines
write_line, notes, harp_48, viola_49, respell_56 = s18.write_line, s18.notes, s18.harp_48, s18.viola_49, s18.respell_56
HARP_CHORD, VIOLA_49, BRASS_SLURS, RUN_SLURS, MELODY_SLURS, PAD_PARTS, ACCENTS = (
    s18.HARP_CHORD, s18.VIOLA_49, s18.BRASS_SLURS, s18.RUN_SLURS, s18.MELODY_SLURS, s18.PAD_PARTS, s18.ACCENTS)


def build(x):
    y = s18.build(x)
    for b in (51, 52):
        y = beam16(y, 'P28', b)
    return y


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
