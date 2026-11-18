"""111326 S30 (Nov 17 2026): S28 again, after Brian's notes on S29: "there's a lot of like forte
dynamics just coming out of nowhere... a diminuendo in the strings and then have that forte on bar
86 doesn't make sense"; "the winds in general shouldn't be following slurring patterns of the
strings... the winds are for actual phrases and breaths... winds should be slurring more".
- The notes of S28. The first statement still swells to bar 80 and falls away; the repeat (bars
  82-85) now grows all the way into bar 86, where S31's forte starts.
- The clarinet and the flute get one slur over each phrase; the strings keep their bowings.
usage (whisperer env): python lab/pieces/p111326_s30.py <S27.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s28 as s28  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

SWELLS = [((78, 79), True), ((80, 81), False), ((82, 85), True)]
H = Fraction(1, 2)
WIND_SLURS = {'P6': [((78, 0), (81, 3 * H)), ((82, 0), (85, 3 * H))], 'P2': [((82, 3 * H), (86, 0))]}
notes = s28.notes
slurs_s28 = s28.slurs


def swells(sc, pid):
    out = []
    for (a, z), up in SWELLS:
        first, last = s28.chains(sc, pid, a), s28.chains(sc, pid, z)
        if first and last:
            out.append(((a, first[0]), (z, last[-1]), up))
    return out


def slurs(x, pid):
    return WIND_SLURS[pid] if pid in WIND_SLURS else slurs_s28(x, pid)


def build(x):
    marks = {pid: slurs(x, pid) for pid in ('P28', 'P29', 'P6', 'P2')}
    y = notes(x)
    sc = Score(y)
    m = Marks(y)
    for pid, sl in marks.items():
        for a, z in sl:
            m.slur(pid, a, z)
    for pid in ('P9', 'P10'):
        m.dynamic(pid, 78, 0, 'mp')
    for pid in s28.SWELLING:
        ws = swells(sc, pid)
        m.dynamic(pid, *ws[0][0], 'mf')
        for a, z, up in ws:
            end = sc.item_end(pid, *z)
            m.hairpin(pid, a, end if end[0] <= z[0] or end[1] else (z[0], None), 'crescendo' if up else 'diminuendo')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
