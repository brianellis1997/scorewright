"""111326 S45 (Nov 25 2026): S44 again, after Brian's note: "the only edition I would make is to have another
instrument double the clarinet's line in 133, another instrument family... a string... in the same register...
maybe hand off the harmony that the violin twos are playing to the viola... what do you think". Builds on his
export of Nov 25, 08:55, as S44 did.
- From bar 133 Violin II doubles the clarinet's run (his own Violin II line of bars 133-134, with his bowing
  slurs), mp. Its held F of bars 133-134 is not handed on: the Wagner tuba holds F, and the harp and the
  bassoon pluck it on every off-beat, so the chord stays full.
- The rest as in S44.
usage (whisperer env): python lab/pieces/p111326_s45.py <export.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s44 as s44  # noqa: E402
from xml_marks import Marks  # noqa: E402

DOUBLED = (133, 134)
VIOLIN_II_SLURS = [((133, Fraction(5, 4)), (133, Fraction(7, 4))), ((134, 0), (134, Fraction(7, 4)))]
_lines = s44.lines


def lines(x):
    ls = _lines(x)
    _, run = s44.his(x)
    for b in DOUBLED:
        ls['P29'][b] = run[b]
    return ls


class patched:
    """S44's builders with S45's Violin II"""
    def __enter__(self):
        self.saved = s44.lines, dict(s44.SLURS)
        s44.lines = lines
        s44.SLURS['P29'] = VIOLIN_II_SLURS

    def __exit__(self, *a):
        s44.lines, slurs = self.saved
        s44.SLURS.clear()
        s44.SLURS.update(slurs)


def notes(x):
    with patched():
        return s44.notes(x)


def build(x):
    with patched():
        y = s44.build(x)
    m = Marks(y)
    m.dynamic('P29', 133, 0, 'mp')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
