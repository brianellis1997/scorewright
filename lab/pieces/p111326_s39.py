"""111326 S39 (Nov 23 2026), after Brian's [CONTINUE]: bars 110-113, the second time through the phrase that
came back softly at bar 106. The piece has gone in pairs (78-81 and 82-85, 86-89 and 90-93), so this is
the pair's second half, a little fuller, and it ends on the same augmented chord over E as bar 109, so the
next idea can start at bar 114. Builds on his export after S38.
- The tune: the clarinet again, with the flute an octave higher (mf).
- The descant: the oboe, now from its first note, the A that resolves its G sharp of bar 109.
- The cellos' theme again; horns and bassoon hold F, Dm, C and C (E under the G sharp) at p; the basses
  join the bassoon an octave lower, p.
- Clarinet, flute and oboe swell to f in bar 112 and fall back to mp on their last note, the shape of
  his swells in bars 106-109, which now peak on f (bar 108) and end on the mf of bar 110.
usage (whisperer env): python lab/pieces/p111326_s39.py <export.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import octave, put  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
BARS = range(110, 114)
TUNE = {110: [('D5', 2), ('C5', 2), ('B4', 4)], 111: [('A4', 4), ('B4', 4)], 112: [('C5', 2), ('B4', 2), ('G4', 4)],
        113: [('E4', 4), ('G4', 2), ('C5', 2)]}
DESCANT = {110: [('A4', 6, None), ('F5', 2, None)], 111: [('E5', 2, None), ('D5', 2, None), ('C5', 2, None), ('D5', 2, 'start')],
           112: [('D5', 6, 'stop'), ('E5', 2, None)], 113: [('D5', 2, None), ('C5', 2, None), ('B4', 2, None), ('G#4', 2, None)]}
THEME = {110: [('A3', 4), ('C4', 2), ('D4', 2)], 111: [('F4', 4), ('E4', 2), ('D4', 2)],
         112: [('E4', 4), ('D4', 2), ('C4', 2)], 113: [('B3', 2), ('C4', 2), ('E3', 4)]}
HELD = {'P9': {110: [('C4', 8, None)], 111: [('D4', 8, None)], 112: [('E4', 8, 'start')], 113: [('E4', 8, 'stop')]},
        'P10': {110: [('A3', 8, 'start')], 111: [('A3', 8, 'stop')], 112: [('G3', 8, 'start')], 113: [('G3', 4, 'stop'), ('E3', 4, None)]},
        'P7': {110: [('F2', 8, None)], 111: [('D2', 8, None)], 112: [('C2', 8, 'start')], 113: [('C2', 4, 'stop'), ('E2', 4, None)]},
        'P32': {110: [('F2', 8, None)], 111: [('D2', 8, None)], 112: [('C2', 8, 'start')], 113: [('C2', 4, 'stop'), ('E2', 4, None)]}}
LEADS = ('P6', 'P2', 'P3')
HIS_PEAKS = {'P6': (108, 0), 'P3': (108, 3 * H)}
PEAK = {'P6': (112, 0), 'P2': (112, 0), 'P3': (112, 3 * H)}
LAST = {'P6': (113, 3 * H), 'P2': (113, 3 * H), 'P3': (113, 3 * H)}
SLURS = {'P6': [((110, 0), (111, 1)), ((112, 0), (113, 3 * H))], 'P2': [((110, 0), (111, 1)), ((112, 0), (113, 3 * H))],
         'P3': [((110, 0), (111, 3 * H)), ((112, 3 * H), (113, 3 * H))], 'P31': [((110, 0), (111, 3 * H)), ((112, 0), (113, 1))],
         'P9': [((110, 0), (112, 0))], 'P10': [((110, 0), (113, 1))], 'P7': [((110, 0), (113, 1))],
         'P32': [((110, 0), (111, 0)), ((112, 0), (113, 1))]}


def lines():
    return {
        'P6': {b: [(n, d, None) for n, d in evs] for b, evs in TUNE.items()},
        'P2': {b: [(octave(n, 1), d, None) for n, d in evs] for b, evs in TUNE.items()},
        'P3': DESCANT,
        'P31': {b: [(n, d, None) for n, d in evs] for b, evs in THEME.items()},
        **HELD,
    }


def check(x):
    sc = Score(x)
    for pid in lines():
        for b in BARS:
            assert all(it[1] == 'Rest' for it in sc.items(pid, b)), (pid, b)
    assert [it[1][0] for it in sc.items('P3', 109) if it[1] != 'Rest'][-1] == 'G#4'


def notes(x):
    check(x)
    for pid, bars in lines().items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    for pid in ('P6', 'P2', 'P3', 'P31'):
        x = beam_eighths(x, pid, BARS)
    return x


def build(x):
    y = notes(x)
    m = Marks(y)
    for pid, sl in SLURS.items():
        for a, z in sl:
            m.slur(pid, a, z)
    for pid in LEADS:
        m.dynamic(pid, 110, 0, 'mf')
        m.hairpin(pid, (110, 0), PEAK[pid], 'crescendo')
        m.dynamic(pid, *PEAK[pid], 'f')
        m.hairpin(pid, PEAK[pid], LAST[pid], 'diminuendo')
        m.dynamic(pid, *LAST[pid], 'mp')
    m.dynamic('P32', 110, 0, 'p')
    for pid, at in HIS_PEAKS.items():
        m.dynamic(pid, *at, 'f')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
