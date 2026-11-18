"""111326 S32 (Nov 17 2026), Brian: "then it leads into the E quarter note, D, C, B, C, those are
eighth notes, and then E quarter note, like that's the climax... add those three bars afterwards...
the harmony... F major, then G major and then E minor". The cor anglais's closing figure (bars 74-76:
E, E | D, C, B, C | E) comes back as the climax, over F, G and E minor. Builds on S31.
- The melody in octaves: piccolo, Violin I, Violin II with the B-flat clarinet, and horn 1 an octave
  lower; each arrives from its last note of bar 93 by a third.
- The descant's G sharp rises to A over the F chord and goes on to B: flute and oboe hold A, B (then
  D on beat 2 of bar 95, so the melody's C passes against a whole step, not a held B), B; horn 2 and
  the Wagner tuba hold A, B (then G), B under them.
- Trombone, Wagner tuba and bass trombone hold the chords (F, A over F; G, B over G; G, B over E),
  each a step or a fourth from its last note; the tuba doubles the bass an octave down, the
  contrabassoon and the basses hold F, G, E.
- The violas' and cellos' sixteenths go on over the new chords; the bassoon's eighths too, holding
  the E on the climax. Harp: rising arpeggios. Timpani: a measured roll on E into bar 96.
- ff goes on, with a crescendo over bars 94-95 into the E of bar 96.
usage (whisperer env): python lab/pieces/p111326_s32.py <S31.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
from p111326_s10 import octave, put  # noqa: E402
from p111326_s15 import beam16  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
BARS = range(94, 97)
MELODY = {94: [('E5', 4), ('E5', 4)], 95: [('D5', 2), ('C5', 2), ('B4', 2), ('C5', 2)], 96: [('E5', 8)]}
INNER = {94: [('A4', 8)], 95: [('B4', 4), ('D5', 4)], 96: [('B4', 8)]}
LOW_INNER = {94: [('A3', 8)], 95: [('B3', 4), ('G3', 4)], 96: [('B3', 8)]}


def shift(d, k):
    return {b: [(octave(n, k), q, None) for n, q in evs] for b, evs in d.items()}


def held(names):
    return {b: [(n, 8, None)] for b, n in zip(BARS, names)}


def sixteenths(names):
    return {b: [(None, 2, None)] + [(n, 1, None)] * 6 for b, n in zip(BARS, names)}


LINES = {
    'P1': shift(MELODY, 2), 'P28': shift(MELODY, 1), 'P29': shift(MELODY, 0), 'P6': shift(MELODY, 0),
    'P9': shift(MELODY, -1),
    'P2': shift(INNER, 1), 'P3': shift(INNER, 0), 'P10': shift(LOW_INNER, 0),
    'P14': held(['F3', 'G3', 'G3']), 'P11': shift(LOW_INNER, 0), 'P15': held(['F2', 'G2', 'E2']),
    'P16': held(['F1', 'G1', 'E1']), 'P8': held(['F2', 'G2', 'E2']), 'P32': held(['F2', 'G2', 'E2']),
    'P30': sixteenths(['C4', 'D4', 'E4']), 'P31': sixteenths(['F3', 'G3', 'E3']),
    'P7': {94: [('F3', 2, None)] * 4, 95: [('G3', 2, None)] * 4, 96: [('E3', 8, None)]},
    'P17': {95: [(None, 4, None)] + [('E2', 1, None)] * 4, 96: [('E2', 4, None), (None, 4, None)]},
}
HARP = {94: (('F2', 'C3', 'F3', 'A3'), ('C4', 'F4', 'A4', 'C5')), 95: (('G2', 'D3', 'G3', 'B3'), ('D4', 'G4', 'B4', 'D5')),
        96: (('E2', 'B2', 'E3', 'G3'), ('B3', 'E4', 'G4', 'B4'))}
MELODIC = ('P1', 'P28', 'P29', 'P6', 'P9')
WIND_SLURS = {pid: [((94, 0), (96, 0))] for pid in ('P1', 'P6', 'P9', 'P2', 'P3', 'P10', 'P14', 'P11', 'P15')}


def notes(x):
    for pid, bars in LINES.items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    for b, (lh, rh) in HARP.items():
        s0, s1 = measure_span(x, 'P26', b)
        x = x[:s0] + re.sub(r'<note[ >].*?</note>|<backup>.*?</backup>', '', x[s0:s1], flags=re.S) + x[s1:]
        x = harp_bar(x, 'P26', b, lh, rh)
    for pid in ('P28', 'P29', 'P6', 'P1', 'P9', 'P7'):
        x = beam_eighths(x, pid, BARS)
    for pid, bars in (('P30', BARS), ('P31', BARS), ('P17', [95])):
        for b in bars:
            x = beam16(x, pid, b)
    return x


def build(x):
    y = notes(x)
    m = Marks(y)
    for pid in MELODIC:
        m.hairpin(pid, (94, 0), (96, 0), 'crescendo')
    m.hairpin('P17', (95, 1), (96, 0), 'crescendo')
    for pid in ('P28', 'P29'):
        m.slur(pid, (95, 0), (95, 3 * H))
    for pid, sl in WIND_SLURS.items():
        for a, z in sl:
            m.slur(pid, a, z)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
