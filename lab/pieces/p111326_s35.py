"""111326 S35 (Nov 23 2026), Brian, after S34: "I'm trying to keep the momentum going with the
trumpets... there's a lot of lines playing in the same melodic range and notes... my idea of trying to
dovetail the trumpets into the strings picking them up an octave higher... I don't know if I'm fully
convinced... that high G... will be screaming through this texture... the clarinet mezzo forte and a
bassoon playing piano... it seems kind of awkward to have the trumpets and all these instruments just
die out suddenly, so maybe we just hold their notes carried over like quarter notes". Builds on his
export of Nov 23 (his trumpet line of bars 106-108 and his Violin I of bars 108-111).
- His trumpet line (G F | E B | C, bars 106-108) moves to Violin I an octave up (G6 F6 | E6 B5),
  with its slurs, mp; it runs straight into his bars 108-111. The dovetail happens at the phrase's
  bar line: the trumpets end their phrase in bar 105, the violins pick up the new one an octave
  higher. The clarinet and oboe keep their octave to themselves (the trumpet had landed in unison
  with them four times in three bars), and the high G is a violin G.
- Bar 106: tuba, bass trombone, contrabassoon and basses (F), trombone (F), Wagner tuba (A), violas
  (F) and Violin II (C) carry the tutti into the F chord as a quarter note, p.
usage (whisperer env): python lab/pieces/p111326_s35.py <export.xml> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s10 import put  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402
from fractions import Fraction  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
VIOLIN = {106: [('G6', 6, None), ('F6', 2, None)], 107: [('E6', 6, None), ('B5', 2, None)]}
CARRY = {'P16': 'F1', 'P15': 'F2', 'P8': 'F2', 'P32': 'F2', 'P14': 'F3', 'P11': 'A3', 'P30': 'F4', 'P29': 'C6'}


def check(x):
    sc = Score(x)
    got = [[(it[0], it[1]) for it in sc.items('P12', b)] for b in (106, 107, 108)]
    assert got == [[(0, ['G5']), (3 * H, ['F5'])], [(0, ['E5']), (3 * H, ['B4'])], [(0, ['C5']), (1, 'Rest')]], got
    assert all(it[1] == 'Rest' for b in (106, 107) for it in sc.items('P28', b))
    assert [it[1] for it in sc.items('P28', 108)][0] == ['C6']
    for pid in CARRY:
        assert all(it[1] == 'Rest' for it in sc.items(pid, 106)), pid


def notes(x):
    check(x)
    for b in (106, 107, 108):
        x = put(x, 'P12', b, [(None, 8, None)])
    for b, evs in VIOLIN.items():
        x = put(x, 'P28', b, evs)
    for pid, n in CARRY.items():
        x = put(x, pid, 106, [(n, 4, None), (None, 4, None)])
    return x


def build(x):
    y = notes(x)
    m = Marks(y)
    for b in VIOLIN:
        m.slur('P28', (b, 0), (b, 3 * H))
    m.dynamic('P28', 106, 0, 'mp')
    for pid in CARRY:
        m.dynamic(pid, 106, 0, 'p')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
