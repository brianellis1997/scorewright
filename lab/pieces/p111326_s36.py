"""111326 S36 (Nov 23 2026): S35 again, after Brian's notes on it: "there should be a slur to that final
note... when we're fading out or doing these transitions or dovetails, slurring is vital"; "the
trumpets are still fading out to nothingness... they don't even have a dynamic marking for what
they're fading out to... we want them to decrescendo to piano". Builds on his export of Nov 23.
- As S35: his trumpet line of bars 106-108 in Violin I an octave up (mp, his slurs).
- Every part that fades over bar 105 is slurred into one quarter note of the F chord in bar 106, at
  p: the target of its decrescendo. The trumpets and the flute now come in too. A part whose note
  would repeat moves to another note of the chord, so the slur never joins two equal notes (a tie
  there would leave the p nowhere to go): Wagner tuba A to C, Violin II C to A, trumpet 2 C to A.
- The crescendos into the climax (bars 94-96) end on fff in bar 96, and the tune's parts come back
  to ff in bar 97 under Violin I's new melody.
usage (whisperer env): python lab/pieces/p111326_s36.py <export.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s10 import put  # noqa: E402
import p111326_s35 as s35  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
CARRY = {'P16': 'F1', 'P15': 'F2', 'P8': 'F2', 'P32': 'F2', 'P14': 'F3', 'P11': 'C4', 'P30': 'F4', 'P29': 'A5',
         'P12': 'F5', 'P13': 'A4', 'P2': 'C6'}
CLIMAX = ('P1', 'P6', 'P9', 'P28', 'P29', 'P17')
BACK_TO_FF = ('P1', 'P6', 'P28', 'P29')


def last_of_105(sc, pid):
    return [it[0] for it in sc.items(pid, 105) if it[1] != 'Rest'][-1]


def notes(x):
    s35.check(x)
    for b in (106, 107, 108):
        x = put(x, 'P12', b, [(None, 8, None)])
    for pid in CARRY:
        assert all(it[1] == 'Rest' for it in Score(x).items(pid, 106)), pid
    for b, evs in s35.VIOLIN.items():
        x = put(x, 'P28', b, evs)
    for pid, n in CARRY.items():
        x = put(x, pid, 106, [(n, 4, None), (None, 4, None)])
    return x


def build(x):
    sc0 = Score(x)
    y = notes(x)
    m = Marks(y)
    for b in s35.VIOLIN:
        m.slur('P28', (b, 0), (b, 3 * H))
    for pid in CARRY:
        m.slur(pid, (105, last_of_105(sc0, pid)), (106, 0), number=2)
        m.dynamic(pid, 106, 0, 'p')
    m.dynamic('P28', 106, 0, 'mp')
    for pid in CLIMAX:
        m.dynamic(pid, 96, 0, 'fff')
    for pid in BACK_TO_FF:
        m.dynamic(pid, 97, 0, 'ff')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
