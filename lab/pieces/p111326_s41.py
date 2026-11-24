"""111326 S41 (Nov 24 2026), Brian, after S40: "I filled in actually what I think the melody should be... the
harmony in the violas... please space it out amongst the strings... the lower notes could be a pizzicato in
the contrabass doubled by a contrabassoon... oboe solo for this very light harmonic accompaniment... the
oboe should kind of speak solo, the only one in that register... the harmony should be underneath it... we
definitely need some held-out notes for the harmony, maybe in the violas and second violins... the counter
melodies covering the other remaining notes... the clarinet and the cello playing contrasting lines... continue
that pattern if it makes sense". Builds on his export of Nov 24 (his oboe line of bars 109-115 and his viola
chords of bars 110-114: F, D7 over F sharp, C over G, G sharp diminished seventh, Am, the bass rising F F#
G G# A).
- The oboe speaks alone in its register (G sharp 4 to E5): mp from its pickup, up to mf on the E of bar 112,
  down to p on the E of bar 114 where his slur ends (his tied last E stays as he wrote it).
- His chords, spread under it: Violin II holds the top notes (F D E D C), the violas the middle ones (C, held
  over bars 110-112, B, A), both p; basses pizzicato with the contrabassoon on each downbeat, F F# G G# A, p.
- The cellos keep the contrasting line going, now against the oboe: they move where it holds and cover the
  chord notes the held parts leave out (A, F, E): A G F | D F# A C | G E | F | E, mp.
- The clarinet ends its tune with a slur into one quarter note, F, p, in bar 110 (an A there would rub a
  semitone against the oboe's tied G sharp), so it does not fade into nothing.
- His swells of bars 106-109 get their peaks and targets: f in bar 108, then p (clarinet) and mp (oboe) in bar
  110.
usage (whisperer env): python lab/pieces/p111326_s41.py <export.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import put  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
BARS = range(110, 115)
CHORDS = {110: ['F4', 'C4', 'A3', 'F2'], 111: ['D4', 'C4', 'A3', 'F#2'], 112: ['E4', 'C4', 'G3', 'G2'],
          113: ['D4', 'B3', 'F3', 'Ab2'], 114: ['C4', 'A3', 'E3', 'A2']}
TOP = dict(zip(BARS, ['F4', 'D4', 'E4', 'D4', 'C4']))
MIDDLE = dict(zip(BARS, ['C4', 'C4', 'C4', 'B3', 'A3']))
BASS = dict(zip(BARS, ['F2', 'F#2', 'G2', 'G#2', 'A2']))
CELLO = {110: [('A3', 4), ('G3', 2), ('F3', 2)], 111: [('D3', 2), ('F#3', 2), ('A3', 2), ('C4', 2)],
         112: [('G3', 4), ('E3', 4)], 113: [('F3', 8)], 114: [('E3', 8)]}
OBOE_MARKS = dict(start=(110, 1), peak=(112, 0), dim_from=(113, 0), last=(114, 0))
HIS_PEAKS = {'P6': (108, 0), 'P3': (108, 3 * H)}
CLARINET_110 = 'F4'


def check(x):
    sc = Score(x)
    for b, names in CHORDS.items():
        (it,) = sc.items('P30', b)
        assert it[1] == names or (b == 113 and it[1][:3] == names[:3]), (b, it[1])
    got = [[(it[0], it[1] if it[1] == 'Rest' else it[1][0]) for it in sc.items('P3', b)] for b in (110, 112, 114)]
    assert got == [[(0, 'G#4'), (H, 'Rest'), (1, 'A4'), (3 * H, 'B4')], [(0, 'E5'), (1, 'E5')], [(0, 'E5'), (1, 'E5')]], got
    for pid in ('P29', 'P31', 'P32', 'P8'):
        for b in BARS:
            assert all(it[1] == 'Rest' for it in sc.items(pid, b)), (pid, b)
    assert all(it[1] == 'Rest' for it in sc.items('P6', 110))


def held(names):
    out = {}
    bars = list(BARS)
    for i, b in enumerate(bars):
        n = names[b]
        before = i > 0 and names[bars[i - 1]] == n
        after = i + 1 < len(bars) and names[bars[i + 1]] == n
        out[b] = [(n, 8, {(False, False): None, (True, False): 'stop', (False, True): 'start', (True, True): 'both'}[(before, after)])]
    return out


def lines():
    return {
        'P29': held(TOP),
        'P30': held(MIDDLE),
        'P31': {b: [(n, d, None) for n, d in evs] for b, evs in CELLO.items()},
        'P32': {b: [(BASS[b], 4, None), (None, 4, None)] for b in BARS},
        'P8': {b: [(BASS[b], 4, None), (None, 4, None)] for b in BARS},
        'P6': {110: [(CLARINET_110, 4, None), (None, 4, None)]},
    }


def notes(x):
    check(x)
    for pid, bars in lines().items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    return beam_eighths(x, 'P31', BARS)


SLURS = {'P29': [((110, 0), (111, 0)), ((112, 0), (114, 0))], 'P30': [((113, 0), (114, 0))],
         'P31': [((110, 0), (110, 3 * H)), ((111, 0), (111, 3 * H)), ((112, 0), (112, 1)), ((113, 0), (114, 0))],
         'P6': [((109, 3 * H), (110, 0))]}


def build(x):
    y = notes(x)
    m = Marks(y)
    for pid, sl in SLURS.items():
        for a, z in sl:
            m.slur(pid, a, z, number=2 if pid == 'P6' else 1)
    for pid, at in HIS_PEAKS.items():
        m.dynamic(pid, *at, 'f')
    m.dynamic('P6', 110, 0, 'p')
    om = OBOE_MARKS
    m.dynamic('P3', *om['start'], 'mp')
    m.hairpin('P3', om['start'], om['peak'], 'crescendo')
    m.dynamic('P3', *om['peak'], 'mf')
    m.hairpin('P3', om['dim_from'], om['last'], 'diminuendo')
    m.dynamic('P3', *om['last'], 'p')
    for pid in ('P29', 'P30', 'P32', 'P8'):
        m.dynamic(pid, 110, 0, 'p')
    m.dynamic('P31', 110, 0, 'mp')
    m.words('P32', 110, 0, 'pizz.')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
