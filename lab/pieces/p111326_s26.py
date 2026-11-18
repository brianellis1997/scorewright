"""111326 S26 (Nov 17 2026), Brian on S25: "i feel like the english horn (cor anglais) needs some
dynamics that follows its melodic line". His style guide: "Dynamics follow the melody... a crescendo
to the high point, a decrescendo as the line falls; the end of a phrase recedes."
- Phrase 1 (60-64): mp, a small swell from the B in bar 61 to the G in bar 62, back down to the E.
- Phrase 2 (64-68): a crescendo up the rising line, A to G, to mf in bar 68.
- Phrase 3 (68-72): mf on the two high Cs, a decrescendo as the line falls, to mp on the F in bar 72,
  so the low A and B are soft.
- Phrase 4 (72-77): a crescendo up to the E in bar 74, then the held E fades with the flute.
usage (whisperer env): python lab/pieces/p111326_s26.py <working.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from xml_marks import Marks  # noqa: E402

H = Fraction(1, 2)
HAIRPINS = [((61, 3 * H), (62, 0), True), ((62, 1), (64, 0), False), ((64, 1), (67, 3 * H), True),
            ((70, 1), (71, 3 * H), False), ((72, 1), (73, 3 * H), True), ((76, 1), (76, 1), False)]
DYNAMICS = [(68, 0, 'mf'), (72, 0, 'mp')]
ENDS = {(62, 0): (62, 1), (64, 0): (64, 1), (67, 3 * H): (68, 0), (71, 3 * H): (72, 0), (73, 3 * H): (74, 0), (76, 1): (77, 2)}


def build(x):
    m = Marks(x)
    for a, z, up in HAIRPINS:
        stop = ENDS[z]
        m.hairpin('P4', a, stop if stop[1] < 2 else (stop[0] + 1, 0), 'crescendo' if up else 'diminuendo')
    for bar, onset, mark in DYNAMICS:
        m.dynamic('P4', bar, onset, mark)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
