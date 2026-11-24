"""111326 S42 (Nov 24 2026), Brian, after S41: "please orchestrate the new bars/melody i added". Builds on his
export of Nov 24, 07:39: a melody handed on from horn 1 (bars 115-117: C | B D | C) to the clarinet (118-122)
to the oboe (122-128), over chords he wrote on the trombone staff: Am, E over G sharp, Am | F minor, Dm over F,
G, Em over G | A, Dm over A, A, Dm over A, B flat minor, B flat diminished.
- Each melody keeps its own register and is the only line there; the harmony sits under it, p.
- Bass: basses pizzicato with the contrabassoon on every downbeat, his bass notes (A G# A F F G G A A A A Bb
  Bb), as in S41.
- Under the horn: horn 2 (A, G sharp, A), the Wagner tuba (E, held) and the trombone (C, B, C) hold his
  chords as a soft brass chorale, spread instead of his close low chord.
- Under the clarinet and the oboe: Violin II and the violas hold the chords' upper notes, below the melody;
  in bars 126-127 the trombone, Wagner tuba and bass trombone join them for the dark B flat minor and
  diminished chords.
- The cellos answer where a melody holds a long note (bars 119, 121, 123, 125), as their contrasting line did
  before: short slurred figures on the chord, p.
- Shapes: the horn mp; the clarinet mp, up to mf on its high A (bar 120), down to p on the E that ends its
  triplet and its slur (bar 121); the oboe the same, up to mf on its high A (bar 126), down to p on the E of its
  triplet (bar 127). His E after each triplet stays struck again, as he wrote it. Every hairpin ends on a dynamic.
usage (whisperer env): python lab/pieces/p111326_s42.py <export.xml> <out.xml>"""
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
BARS = range(115, 128)
CHORDS = {115: ['E3', 'C3', 'A2'], 116: ['E3', 'B2', 'G#2'], 117: ['E3', 'C3', 'A2'], 118: ['C3', 'Ab2', 'F2'],
          119: ['D3', 'A2', 'F2'], 120: ['D3', 'B2', 'G2'], 121: ['E3', 'B2', 'G2'], 122: ['E3', 'C#3', 'A2'],
          123: ['F3', 'D3', 'A2'], 124: ['E3', 'C#3', 'A2'], 125: ['F3', 'D3', 'A2'], 126: ['F3', 'Db3', 'Bb2'],
          127: ['Fb3', 'Db3', 'Bb2']}
BASS = dict(zip(BARS, ['A2', 'G#2', 'A2', 'F2', 'F2', 'G2', 'G2', 'A2', 'A2', 'A2', 'A2', 'Bb2', 'Bb2']))


def tied(names):
    """{bar: note}: one note a bar, tied into the next bar when it repeats"""
    bars = sorted(names)
    out = {}
    for i, b in enumerate(bars):
        n = names[b]
        before = i > 0 and bars[i - 1] == b - 1 and names[bars[i - 1]] == n
        after = i + 1 < len(bars) and bars[i + 1] == b + 1 and names[bars[i + 1]] == n
        out[b] = [(n, 8, {(False, False): None, (True, False): 'stop', (False, True): 'start', (True, True): 'both'}[(before, after)])]
    return out


HELD = {
    'P10': tied({115: 'A3', 116: 'G#3', 117: 'A3'}),
    'P11': tied({115: 'E3', 116: 'E3', 117: 'E3', 126: 'Db3', 127: 'Db3'}),
    'P14': tied({115: 'C3', 116: 'B2', 117: 'C3', 126: 'F3', 127: 'Fb3'}),
    'P15': tied({126: 'Bb2', 127: 'Bb2'}),
    'P29': tied(dict(zip(range(118, 128), ['C4', 'D4', 'D4', 'E4', 'E4', 'F4', 'E4', 'F4', 'F4', 'Fb4']))),
    'P30': tied(dict(zip(range(118, 128), ['Ab3', 'A3', 'B3', 'B3', 'C#4', 'D4', 'C#4', 'D4', 'Db4', 'Db4']))),
}
CELLO = {119: [(None, 4), ('F3', 2), ('E3', 2)], 120: [('D3', 4), (None, 4)], 121: [(None, 4), ('E3', 2), ('D3', 2)],
         122: [('C#3', 4), (None, 4)], 123: [('D3', 2), ('E3', 2), ('F3', 4)], 125: [('F3', 2), ('E3', 2), ('D3', 4)]}
PIZZ = ('P32', 'P8')
SLURS = {'P10': [((115, 0), (117, 0))], 'P14': [((115, 0), (117, 0)), ((126, 0), (127, 0))],
         'P29': [((118, 0), (119, 0)), ((123, 0), (125, 0))], 'P30': [((118, 0), (119, 0)), ((122, 0), (125, 0))],
         'P31': [((119, 1), (120, 0)), ((121, 1), (122, 0)), ((123, 0), (123, 1)), ((125, 0), (125, 1))]}
SWELLS = {'P6': ((118, 0), (120, 1), (121, Fraction(2, 3))), 'P3': ((122, 1), (126, 1), (127, Fraction(2, 3)))}
SOFT = {'P10': (115, 0), 'P11': (115, 0), 'P14': (115, 0), 'P29': (118, 0), 'P30': (118, 0), 'P31': (119, 1), 'P15': (126, 0)}
AGAIN = {'P11': (126, 0), 'P14': (126, 0)}


def check(x):
    sc = Score(x)
    for b, names in CHORDS.items():
        (it,) = [i for i in sc.items('P14', b) if i[1] != 'Rest']
        assert it[1] == names, (b, it[1])
    assert [(it[0], it[1][0]) for it in sc.items('P9', 115) if it[1] != 'Rest'] == [(0, 'C4')]
    assert [it[1][0] for it in sc.items('P6', 118) if it[1] != 'Rest'] == ['B4', 'E5']
    assert [it[1][0] for it in sc.items('P3', 126) if it[1] != 'Rest'] == ['E5', 'A5']
    for pid in ('P10', 'P11', 'P15', 'P29', 'P30', 'P31', 'P32', 'P8'):
        for b in BARS:
            assert all(it[1] == 'Rest' for it in sc.items(pid, b)), (pid, b)


def lines():
    ls = {pid: dict(bars) for pid, bars in HELD.items()}
    ls['P31'] = {b: [(n, d, None) for n, d in evs] for b, evs in CELLO.items()}
    for pid in PIZZ:
        ls[pid] = {b: [(BASS[b], 4, None), (None, 4, None)] for b in BARS}
    return ls


def notes(x):
    check(x)
    for b in BARS:
        x = put(x, 'P14', b, [(None, 8, None)])
    for pid, bars in lines().items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    return beam_eighths(x, 'P31', BARS)


def build(x):
    y = notes(x)
    m = Marks(y)
    for pid, sl in SLURS.items():
        for a, z in sl:
            m.slur(pid, a, z)
    m.dynamic('P9', 115, 0, 'mp')
    for pid, (a, peak, last) in SWELLS.items():
        m.dynamic(pid, *a, 'mp')
        m.hairpin(pid, a, peak, 'crescendo')
        m.dynamic(pid, *peak, 'mf')
        m.hairpin(pid, peak, last, 'diminuendo')
        m.dynamic(pid, *last, 'p')
    for pid, at in list(SOFT.items()) + list(AGAIN.items()):
        m.dynamic(pid, *at, 'p')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
