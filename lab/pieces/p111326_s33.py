"""111326 S33 (Nov 18 2026), Brian, after S32: "I filled in some... following melody with the harmony
in the violas again; don't have the violas with that line, exploded out across... instruments again
where I got to climax... the violin one contains the melody of course; let everything continue...
and then you see how the trumpets kind of take over in bar 101, they lead the melody; the violins
will be in support, either accenting certain figures or provide harmonies on top... the harp...
glissandi accenting certain figures... a sudden run up and then accenting that percussion hit... it
can also go down and then up... contrasting with the phrase". Builds on his export after S32: his
Violin I (bars 96-101), his trumpets (101-105), and his clarinet and oboe (106-109) stay as written.
- His viola chords (A, Dm over A, G7, C7 over G, Fmaj7, D7 over F sharp, C over G, G, Am) are spread
  as at the climax: horns 1 and 2 and the Wagner tuba hold the upper voices; bass trombone, tuba,
  contrabassoon and basses the bass (the chords' lowest notes A A G G F F# G G A); the trombone, the
  cellos' sixteenths and the bassoon's eighths keep that bass an octave up, the violas' sixteenths the
  top voice.
- Bars 97-101: Violin I's melody in octaves: the piccolo an octave up, the flute with it, oboe,
  clarinet and Violin II an octave down (flute and oboe join his E on beat 2 of bar 96); horn 1 leaves
  the tune for the top voice (as the tune it crossed horn 2 and rubbed a semitone against the violas);
  the accompaniment f. The held parts breathe on beat 2 of bar 101, under the trumpets' pickup.
- Bars 101-105: the trumpets lead (f, a crescendo to ff in bar 103). Violin I, Violin II and the flute
  hold the harmony above them (D, E, D, E over A, C, B, C) and strike the trumpets' two quarters in
  bars 103 and 105 with them. Everything falls away over bar 105, under the
  clarinet's entry in bar 106.
- Harp: a glissando up into bar 97 and one into the trumpets' bar 102, each with a timpani stroke;
  in bar 104 one down and one up into bar 105, with the last stroke. White notes only (no pedal
  change): E minor, F major seventh and G under them.
- The tuba had no dynamic since bar 53 (mf) when S32 brought it in: ff in bar 94.
usage (whisperer env): python lab/pieces/p111326_s33.py <export.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import accidental, key_of, measure_span, shift, transpose_of  # noqa: E402
from p111326_s5 import parse  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import octave, put  # noqa: E402
from p111326_s15 import beam16  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
BARS = range(97, 106)
TUNE = {97: [('G6', 6), ('F6', 2)], 98: [('E6', 6), ('B5', 2)], 100: [('E6', 6), ('F6', 2)], 101: [('E6', 4), (None, 4)]}
TRIPLET, AFTER = ['C6', 'D6', 'E6'], ['G6', 'F6']
V1 = dict(zip(BARS, ['E4', 'F4', 'F4', 'E4', 'E4', 'D4', 'E4', 'D4', 'E4']))
V2 = dict(zip(BARS, ['C#4', 'D4', 'B3', 'C4', 'C4', 'C4', 'C4', 'B3', 'C4']))
V3 = dict(zip(BARS, ['A3', 'A3', 'G3', 'Bb3', 'A3', 'A3', 'G3', 'G3', 'A3']))
BASS = dict(zip(BARS, ['A', 'A', 'G', 'G', 'F', 'F#', 'G', 'G', 'A']))
DOUBLE = {'P1': 1, 'P2': 0, 'P3': -1, 'P6': -1, 'P29': -1}
PICKUP = {'P2': 'E6', 'P3': 'E5'}
HALO = {'P28': ['D6', 'E6', 'D6', 'E6'], 'P2': ['D6', 'E6', 'D6', 'E6'], 'P29': ['A5', 'C6', 'B5', 'C6']}
PHRASES = ((97, 101), (102, 105))
GLISS = {96: [(None, 4), ('B3', 4, 'start')], 97: [('G6', 4, 'stop'), (None, 4)], 101: [(None, 4), ('C4', 4, 'start')],
         102: [('A5', 4, 'stop'), (None, 4)], 104: [('D6', 4, 'start'), ('D4', 4, 'both')], 105: [('A5', 4, 'stop'), (None, 4)]}
STRIKES = {97: ['A1', 'A2'], 102: ['D2', 'A2'], 105: ['A1', 'A2']}
TIMPANI = {97: 'A2', 102: 'D3', 105: 'A2'}
ACCOMP = ('P30', 'P31', 'P32', 'P7', 'P8', 'P9', 'P10', 'P11', 'P14', 'P15', 'P16', 'P17')
FADING = ('P2', 'P7', 'P8', 'P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16', 'P28', 'P29', 'P30', 'P31', 'P32')
HELD_SLURS = ('P9', 'P10', 'P11', 'P14', 'P15')


def check_sketch(x):
    """his viola chords and Violin I are what this builds on"""
    sc = Score(x)
    for b in BARS:
        (it,) = sc.items('P30', b)
        names = it[1]
        assert names[0] == V1[b] and names[-1] == BASS[b] + names[-1][-1], (b, names)
        assert set(names[1:-1]) <= {V2[b], V3[b]} and V2[b] in names, (b, names)
    got = [(b, [(it[0], it[1]) for it in sc.items('P28', b)]) for b in range(97, 102)]
    want = [(97, [(0, ['G6']), (Fraction(3, 2), ['F6'])]), (98, [(0, ['E6']), (Fraction(3, 2), ['B5'])]),
            (99, [(0, ['C6']), (Fraction(1, 3), ['D6']), (Fraction(2, 3), ['E6']), (1, ['G6']), (Fraction(3, 2), ['F6'])]),
            (100, [(0, ['E6']), (Fraction(3, 2), ['F6'])]), (101, [(0, ['E6']), (1, 'Rest')])]
    assert got == want, got


def ev(evs, k=0):
    return [(octave(n, k), q, None) for n, q in evs]


def tied(names, bars=BARS, breaks=(102,)):
    """one note a bar, tied into the next bar when it repeats, struck again at each break"""
    out = {}
    for i, b in enumerate(bars):
        n = names[b]
        before = i > 0 and names[bars[i - 1]] == n and b not in breaks
        after = i + 1 < len(bars) and names[bars[i + 1]] == n and bars[i + 1] not in breaks
        out[b] = [(n, 8, {(False, False): None, (True, False): 'stop', (False, True): 'start', (True, True): 'both'}[(before, after)])]
    return out


def bass(k):
    return tied({b: f'{n}{k}' for b, n in BASS.items()})


def phrased(names):
    """held, with a breath on beat 2 of bar 101, where the trumpets come in"""
    out = tied(names)
    n, _, t = out[101][0]
    out[101] = [(n, 4, 'stop' if t in ('stop', 'both') else None), (None, 4, None)]
    return out


def lines():
    out = {}
    for pid, k in DOUBLE.items():
        out[pid] = {b: ev(evs, k) for b, evs in TUNE.items()}
    for pid, names in HALO.items():
        bars = out.setdefault(pid, {})
        for b, n in zip(range(102, 106), names):
            bars[b] = [(n, 8, None)] if b % 2 == 0 else [(n, 4, None), (n, 4, None)]
    out['P9'] = phrased(V1)
    out['P10'] = phrased(V2)
    out['P11'] = phrased(V3)
    out['P14'] = phrased({b: f'{n}3' for b, n in BASS.items()})
    for pid, k in (('P15', 2), ('P16', 1), ('P8', 2), ('P32', 2)):
        out[pid] = bass(k)
    out['P7'] = {b: [(f'{n}3', 2, None)] * 4 for b, n in BASS.items()}
    out['P7'][105] = [('A3', 8, None)]
    out['P30'] = {b: [(None, 2, None)] + [(V2[b] if b == 101 else V1[b], 1, None)] * 6 for b in BARS}
    out['P31'] = {b: [(None, 2, None)] + [(f'{BASS[b]}3', 1, None)] * 6 for b in BARS}
    out['P17'] = {b: [(n, 4, None), (None, 4, None)] for b, n in TIMPANI.items()}
    return out


def pitch_xml(x, pid, name, state):
    d, c = transpose_of(x, pid)
    p = shift(parse(name), -d, -c)
    acc = accidental(p, key_of(x, pid), state)
    return (f'<pitch><step>{p[0]}</step>' + (f'<alter>{p[1]}</alter>' if p[1] else '') + f'<octave>{p[2]}</octave></pitch>',
            f'<accidental>{acc}</accidental>' if acc else '')


def triplet_bar(x, pid, k):
    """bar 99 for a part that doubles Violin I k octaves away: C D E as eighth triplets, then G F
    (12 divisions to the quarter in this bar only, as Dorico writes his)"""
    s0, s1 = measure_span(x, pid, 99)
    body = x[s0:s1]
    assert '<pitch>' not in body, f'{pid} bar 99 is not empty'
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', body, re.S))
    keep = re.sub(r'<divisions>\d+</divisions>', '<divisions>12</divisions>', keep)
    state, out = {}, []
    tm = '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes><normal-type>eighth</normal-type></time-modification>'
    for i, n in enumerate(TRIPLET):
        p, acc = pitch_xml(x, pid, octave(n, k), state)
        beam = ('begin', 'continue', 'end')[i]
        tup = {0: '<tuplet type="start" bracket="yes" number="1"/>', 2: '<tuplet type="stop" bracket="yes" number="1"/>'}.get(i, '')
        out.append(f'<note>{p}<duration>4</duration><voice>1</voice><type>eighth</type>{acc}{tm}<staff>1</staff>'
                   f'<beam number="1">{beam}</beam>' + (f'<notations>{tup}</notations>' if tup else '') + '</note>')
    for i, n in enumerate(AFTER):
        p, acc = pitch_xml(x, pid, octave(n, k), state)
        out.append(f'<note>{p}<duration>6</duration><voice>1</voice><type>eighth</type>{acc}<staff>1</staff>'
                   f'<beam number="1">{("begin", "end")[i]}</beam></note>')
    return x[:s0] + keep + ''.join(out) + x[s1:]


def harp_bar(x, bar, rh, lh):
    """one bar of Harp 1: rh = [(name or None, divisions, glissando)], lh = [(names or None, divisions)]"""
    s0, s1 = measure_span(x, 'P26', bar)
    body = x[s0:s1]
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', body, re.S))
    typ = {4: 'quarter', 8: 'whole'}
    state = {}

    def notes(evs, staff):
        out = []
        for e in evs:
            names, d = e[0], e[1]
            gl = e[2] if len(e) > 2 else None
            if names is None:
                out.append(f'<note><rest/><duration>{d}</duration><voice>{staff}</voice><type>{typ[d]}</type><staff>{staff}</staff></note>')
                continue
            for i, n in enumerate([names] if isinstance(names, str) else names):
                p, acc = pitch_xml(x, 'P26', n, state)
                marks = {'start': '<glissando line-type="wavy" number="1" type="start">gliss.</glissando>',
                         'stop': '<glissando line-type="wavy" number="1" type="stop"/>',
                         'both': '<glissando line-type="wavy" number="1" type="stop"/><glissando line-type="wavy" number="2" type="start">gliss.</glissando>'}.get(gl, '')
                if gl == 'stop' and bar == 105:
                    marks = '<glissando line-type="wavy" number="2" type="stop"/>'
                out.append(f'<note>{"<chord/>" if i else ""}{p}<duration>{d}</duration><voice>{staff}</voice><type>{typ[d]}</type>{acc}'
                           f'<staff>{staff}</staff>' + (f'<notations>{marks}</notations>' if marks else '') + '</note>')
        return ''.join(out)

    if lh is None:
        cut = body.index('<backup>')
        head = re.sub(r'<note[ >].*?</note>', '', body[:cut], flags=re.S)
        return x[:s0] + head + notes(rh, 1) + body[cut:] + x[s1:]
    return x[:s0] + keep + notes(rh, 1) + '<backup><duration>8</duration></backup>' + notes(lh, 2) + x[s1:]


def harp(x):
    for b in range(96, 106):
        rh = GLISS.get(b, [(None, 8)])
        lh = None if b == 96 else ([(STRIKES[b], 4), (None, 4)] if b in STRIKES else [(None, 8)])
        x = harp_bar(x, b, rh, lh)
    return x


def pickup(x, pid, name):
    """bar 96: the held note keeps its first beat (and its slur's end), the tune's E comes in on beat 2"""
    s0, s1 = measure_span(x, pid, 96)
    body = x[s0:s1]
    (m,) = re.finditer(r'<note>(?:(?!</note>).)*<pitch>.*?</note>', body, re.S)
    old = m.group(0).replace('<duration>8</duration>', '<duration>4</duration>', 1).replace('<type>half</type>', '<type>quarter</type>', 1)
    assert '<duration>4</duration>' in old and '<tie' not in old, (pid, old)
    p, acc = pitch_xml(x, pid, name, {})
    new = f'<note>{p}<duration>4</duration><voice>1</voice><type>quarter</type>{acc}<staff>1</staff></note>'
    return x[:s0] + body[:m.start()] + old + new + body[m.end():] + x[s1:]


def notes(x):
    check_sketch(x)
    for pid, name in PICKUP.items():
        x = pickup(x, pid, name)
    for b in BARS:
        x = put(x, 'P30', b, [(None, 8, None)])
    for pid, bars in lines().items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    for pid, k in DOUBLE.items():
        x = triplet_bar(x, pid, k)
    x = harp(x)
    for pid in ('P1', 'P2', 'P3', 'P6', 'P29', 'P7'):
        x = beam_eighths(x, pid, [b for b in BARS if b != 99])
    for pid in ('P30', 'P31'):
        for b in BARS:
            x = beam16(x, pid, b)
    return x


def firsts(sc, pid, bar):
    return [it[0] for it in sc.items(pid, bar) if it[1] != 'Rest' and not it[2]]


def last_at(sc, pid, bar):
    f = firsts(sc, pid, bar)
    return (bar, f[-1]) if f else sc.chain_start(pid, bar, 0)


VIOLIN_SLURS = [((97, 0), (97, 3 * H)), ((98, 0), (98, 3 * H)), ((99, 0), (99, Fraction(2, 3))), ((99, 1), (99, 3 * H)), ((100, 0), (100, 3 * H))]


def slurs(sc):
    """[(pid, start, end)]: Violin II bows as Violin I; the winds on the tune take one slur over the
    phrase, the held parts one over each phrase"""
    out = [('P29', a, z) for a, z in VIOLIN_SLURS]
    for pid in ('P1', 'P2', 'P3', 'P6'):
        out.append((pid, (96, 1) if pid in PICKUP else (97, 0), (101, 0)))
    for pid in HELD_SLURS:
        for a, z in PHRASES:
            out.append((pid, (a, 0), last_at(sc, pid, z)))
    return out


def build(x):
    y = notes(x)
    sc = Score(y)
    m = Marks(y)
    m.dynamic('P16', 94, 0, 'ff')
    for pid in ACCOMP:
        m.dynamic(pid, 97, firsts(sc, pid, 97)[0], 'f')
    for pid in ('P12', 'P13'):
        m.dynamic(pid, 101, 1, 'f')
        m.hairpin(pid, (101, 1), (103, 0), 'crescendo')
        m.dynamic(pid, 103, 0, 'ff')
    for pid in ('P28', 'P29', 'P2'):
        m.dynamic(pid, 102, 0, 'f')
    for pid in ('P28', 'P29', 'P2'):
        for b in (103, 105):
            for o in (0, 1):
                m.articulation(pid, b, o, 'detached-legato')
    for pid, a, z in slurs(sc):
        m.slur(pid, a, z)
    for pid in FADING:
        m.hairpin(pid, (105, firsts(sc, pid, 105)[0]), (105, None), 'diminuendo')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
