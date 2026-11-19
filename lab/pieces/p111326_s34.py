"""111326 S34 (Nov 18 2026): S33 again, after Brian's notes on it: "I really like how things pause
almost like at a climax on bar 97, but then the rhythm and all the supporting shit needs to come back
98... the bottom fell out going from 96 to 97... it's fine for 97 but bring it up and bring it back in
98"; and "continue with bar 106... the winds should be in the background with the harmony of F major,
D minor, C major... something should be going on, a new theme in the background, while not
contrapuntally clashing with these lines". Builds on his export after S32, as S33 did.
- Bar 97 stays as in S33: the pause after the climax.
- From bar 98 the rhythm and the low end come back: a crescendo over bar 97 to ff; the cellos'
  sixteenths and the bassoon's eighths drop an octave (A2 G2 G2 F2 F#2 G2 G2 A2); contrabassoon and
  basses strike each downbeat; the timpani each bar; the harp's arpeggios between its glissandi; the
  held brass struck again in bar 98.
- Bars 106-109, under his clarinet and oboe: horns and bassoon hold F, Dm, C and C (E in the bass on
  beat 2 of bar 109, under the oboe's G sharp), p; the cellos have a new theme, mp, rising where the
  clarinet falls (A C D | F E D | E D C | B C E); their sixteenths of bar 105 rise A C E into it.
usage (whisperer env): python lab/pieces/p111326_s34.py <export.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s15 import beam16  # noqa: E402
import p111326_s33 as s33  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
BACK = range(98, 106)
BREAKS = (98, 102)
TIMPANI = {97: 'A2', 98: 'A2', 99: 'D3', 100: 'E2', 101: 'A2', 102: 'D3', 103: 'E2', 104: 'D3', 105: 'A2'}
ARPEGGIOS = {98: (('A2', 'D3', 'F3', 'A3'), ('D4', 'F4', 'A4', 'D5')), 99: (('G2', 'D3', 'F3', 'B3'), ('D4', 'F4', 'G4', 'B4')),
             100: (('G2', 'C3', 'E3', 'G3'), ('C4', 'E4', 'G4', 'C5')), 103: (('G2', 'C3', 'E3', 'G3'), ('C4', 'E4', 'G4', 'C5'))}
LEFT_101 = ('F2', 'C3', 'F3', 'A3')
THEME = {106: [('A3', 4), ('C4', 2), ('D4', 2)], 107: [('F4', 4), ('E4', 2), ('D4', 2)],
         108: [('E4', 4), ('D4', 2), ('C4', 2)], 109: [('B3', 2), ('C4', 2), ('E3', 4)]}
WINDS_106 = {'P9': {106: [('C4', 8, None)], 107: [('D4', 8, None)], 108: [('E4', 8, 'start')], 109: [('E4', 8, 'stop')]},
             'P10': {106: [('A3', 8, 'start')], 107: [('A3', 8, 'stop')], 108: [('G3', 8, 'start')], 109: [('G3', 4, 'stop'), ('E3', 4, None)]},
             'P7': {106: [('F2', 8, None)], 107: [('D2', 8, None)], 108: [('C2', 8, 'start')], 109: [('C2', 4, 'stop'), ('E2', 4, None)]}}
SWELL = ('P30', 'P31', 'P32', 'P7', 'P8', 'P9', 'P10', 'P11', 'P14', 'P15', 'P16')
THEME_SLURS = [((106, 0), (107, 3 * H)), ((108, 0), (109, 1))]


def phrased(names):
    out = s33.tied(names, breaks=BREAKS)
    n, _, t = out[101][0]
    out[101] = [(n, 4, 'stop' if t in ('stop', 'both') else None), (None, 4, None)]
    return out


def lines():
    out = s33.lines()
    out['P9'] = phrased(s33.V1)
    out['P10'] = phrased(s33.V2)
    out['P11'] = phrased(s33.V3)
    out['P14'] = phrased({b: f'{n}3' for b, n in s33.BASS.items()})
    for pid, k in (('P15', 2), ('P16', 1)):
        out[pid] = s33.tied({b: f'{n}{k}' for b, n in s33.BASS.items()}, breaks=BREAKS)
    for pid in ('P8', 'P32'):
        out[pid] = {97: [('A2', 8, None)], **{b: [(f'{s33.BASS[b]}2', 4, None), (None, 4, None)] for b in range(98, 105)}, 105: [('A2', 8, None)]}
    for b in BACK:
        out['P31'][b] = [(None, 2, None)] + [(f'{s33.BASS[b]}2', 1, None)] * 6
        out['P7'][b] = [(f'{s33.BASS[b]}2', 2, None)] * 4
    out['P7'][105] = [('A2', 8, None)]
    out['P17'] = {b: [(n, 4, None), (None, 4, None)] for b, n in TIMPANI.items()}
    for pid, bars in WINDS_106.items():
        out[pid].update(bars)
    out['P31'][105] = [(None, 2, None)] + [(n, 1, None) for n in ('A2', 'A2', 'C3', 'C3', 'E3', 'E3')]
    out['P31'].update({b: [(n, d, None) for n, d in evs] for b, evs in THEME.items()})
    return out


def harp(x):
    x = s33.harp(x)
    for b, (lh, rh) in ARPEGGIOS.items():
        x = harp_bar(x, 'P26', b, lh, rh)
    return left_101(x)


def left_101(x):
    """bar 101: the left hand's arpeggio on beat 1 under the glissando's start"""
    from p111326_s2 import key_of, measure_span
    from p111326_s6 import sixteenths
    s0, s1 = measure_span(x, 'P26', 101)
    body = x[s0:s1]
    cut = body.index('<backup>')
    left = sixteenths(LEFT_101, 2, 2, key_of(x, 'P26'), {}) + '<note><rest/><duration>4</duration><voice>2</voice><type>quarter</type><staff>2</staff></note>'
    return x[:s0] + body[:cut] + '<backup><duration>8</duration></backup>' + left + x[s1:]


def notes(x):
    s33.check_sketch(x)
    for pid, name in s33.PICKUP.items():
        x = s33.pickup(x, pid, name)
    for b in s33.BARS:
        x = put(x, 'P30', b, [(None, 8, None)])
    for pid, bars in lines().items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    for pid, k in s33.DOUBLE.items():
        x = s33.triplet_bar(x, pid, k)
    x = harp(x)
    for pid in ('P1', 'P2', 'P3', 'P6', 'P29', 'P7', 'P31'):
        x = beam_eighths(x, pid, [b for b in range(97, 110) if b != 99])
    for pid in ('P30', 'P31'):
        for b in s33.BARS:
            x = beam16(x, pid, b)
    return x


def slurs(sc):
    out = [s for s in s33.slurs(sc)]
    out = [(pid, a, z) for pid, a, z in out if pid not in s33.HELD_SLURS]
    for pid in s33.HELD_SLURS:
        for a, z in ((98, 101), (102, 105)):
            out.append((pid, (a, 0), s33.last_at(sc, pid, z)))
    out += [('P31', a, z) for a, z in THEME_SLURS]
    out += [('P9', (106, 0), (108, 0)), ('P10', (106, 0), (109, 1)), ('P7', (106, 0), (109, 1))]
    return out


def build(x):
    y = notes(x)
    sc = Score(y)
    m = Marks(y)
    m.dynamic('P16', 94, 0, 'ff')
    for pid in s33.ACCOMP:
        m.dynamic(pid, 97, s33.firsts(sc, pid, 97)[0], 'f')
    for pid in SWELL:
        f = s33.firsts(sc, pid, 97)
        m.hairpin(pid, (97, f[0]), (97, None), 'crescendo')
    for pid in SWELL + ('P17',):
        m.dynamic(pid, 98, s33.firsts(sc, pid, 98)[0], 'ff')
    for pid in ('P12', 'P13'):
        m.dynamic(pid, 101, 1, 'f')
        m.hairpin(pid, (101, 1), (103, 0), 'crescendo')
        m.dynamic(pid, 103, 0, 'ff')
    for pid in ('P28', 'P29', 'P2'):
        m.dynamic(pid, 102, 0, 'f')
        for b in (103, 105):
            for o in (0, 1):
                m.articulation(pid, b, o, 'detached-legato')
    for pid, a, z in slurs(sc):
        m.slur(pid, a, z)
    for pid in s33.FADING:
        m.hairpin(pid, (105, s33.firsts(sc, pid, 105)[0]), (105, None), 'diminuendo')
    for pid in ('P9', 'P10', 'P7'):
        m.dynamic(pid, 106, 0, 'p')
    m.dynamic('P31', 106, 0, 'mp')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
