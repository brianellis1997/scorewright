"""111326 S31 (Nov 17 2026): S29 again, after Brian's notes on it: "I said four bars, I meant eight
bars... it's missing the second iteration of the four bars phrase... don't end"; "a clarinet way up
high... there's no way a clarinetist can hit that just off rip"; "maybe we can have the piccolo
doubling the violin run"; "a diminuendo... and then have that forte on bar 86 doesn't make sense";
"the oboe definitely needs slurs... the winds... are for actual phrases and breaths". Builds on S30.
- The grand statement is eight bars, the four-bar phrase twice (86-89, 90-93), and does not end:
  bar 93 stays on its E, ready for what comes next.
- The tune in both violins in octaves (Violin I an octave up, which it reaches by the sixteenth run
  in bar 85; Violin II at pitch with the B-flat clarinet); the piccolo doubles the run an octave up
  and then Violin I's line an octave higher. No E-flat clarinet.
- The descant: flute an octave up, oboe at pitch from where its phrase starts (beat 2.5 of bar 86).
  Its C on beat 2 of bars 87 and 91 is B: doubled in octaves, the C rubbed against the tune's B.
- Underneath: the violas' and cellos' sixteenths, the bassoon's eighths, contrabassoon and basses on
  the bass, horns, trombones and Wagner tuba holding the harmony (struck again in bar 90).
- Harp: a rising arpeggio each bar. Timpani: D on bars 87 and 91, E on beat 2 of bars 89 and 93.
- f in bar 86 after S30's crescendo, a crescendo to bar 90, ff for the second time through.
- Winds: one slur over each phrase; the strings keep their bowings.
usage (whisperer env): python lab/pieces/p111326_s31.py <S30.xml> <out.xml>"""
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
import p111326_s28 as s28  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
GRAND = range(86, 94)
TUNE = {86: [('D5', 2), ('C5', 2), ('B4', 4)], 87: [('A4', 4), ('B4', 4)], 88: [('C5', 2), ('B4', 2), ('G4', 4)],
        89: [('E4', 4), ('G4', 2), ('C5', 2)]}
DESCANT = {86: [('A4', 6), ('F5', 2)], 87: [('E5', 2), ('D5', 2), ('B4', 2), ('D5', 2, 'start')], 88: [('D5', 6, 'stop'), ('E5', 2)],
           89: [('D5', 2), ('C5', 2), ('B4', 2), ('G#4', 2)]}
RUN_85 = [('D5', 2), ('E5', 1), ('F5', 1), ('G5', 1), ('A5', 1), ('B5', 1), ('C6', 1)]
BASS = {86: ['F3'] * 4, 87: ['D3'] * 4, 88: ['C3'] * 4, 89: ['C3', 'C3', 'E3', 'E3']}
LOW = {86: [('F2', 4), (None, 4)], 87: [('D2', 4), (None, 4)], 88: [('C2', 4), (None, 4)], 89: [('C2', 4), ('E2', 4)]}
HOLD = {'P9': {86: [('C4', 8)], 87: [('D4', 4), ('C4', 4)], 88: [('C4', 8)], 89: [('C4', 8)]},
        'P10': {86: [('A3', 8)], 87: [('A3', 6), ('Ab3', 2)], 88: [('G3', 8)], 89: [('G3', 6), ('Ab3', 2)]},
        'P14': {86: [('A3', 8)], 87: [('A3', 8)], 88: [('G3', 8)], 89: [('G3', 4), ('E3', 4)]},
        'P15': {86: [('F2', 8)], 87: [('D2', 8)], 88: [('C2', 8)], 89: [('C2', 4), ('E2', 4)]},
        'P11': {86: [('F3', 8)], 87: [('F3', 8)], 88: [('E3', 8)], 89: [('E3', 8)]}}
HARP = {86: (('F2', 'C3', 'F3', 'A3'), ('C4', 'F4', 'A4', 'C5')), 87: (('D2', 'A2', 'D3', 'F3'), ('A3', 'D4', 'F4', 'A4')),
        88: (('C2', 'G2', 'C3', 'E3'), ('G3', 'C4', 'E4', 'G4')), 89: (('C2', 'G2', 'C3', 'E3'), ('C4', 'E4', 'G#4', 'C5'))}
TIMPANI = {87: [('D3', 4), (None, 4)], 89: [(None, 4), ('E2', 4)]}


def twice(d):
    """bars 86-89 again as 90-93"""
    return {**d, **{b + 4: v for b, v in d.items()}}


def ev(d):
    return {b: [(e[0], e[1], e[2] if len(e) > 2 else None) for e in evs] for b, evs in d.items()}


def up(d, k=1):
    return {b: [(octave(n, k), q, t) for n, q, t in evs] for b, evs in ev(d).items()}


def held(d):
    """held notes tied over the bar lines inside each time through, struck again in bar 90"""
    out = {}
    for first in (86, 90):
        part = {b: [(n, q) for n, q, *_ in d[b - first + 86]] for b in range(first, first + 4)}
        out.update(s28.sustained(part))
    return out


def strings_16ths(x):
    """the violas' and cellos' sixteenths of bars 78-81, twice"""
    sc = Score(x)
    top, low = {}, {}
    for b in GRAND:
        src = 78 + (b - 86) % 4
        for part, out in (('P30', top), ('P31', low)):
            out[b] = [(None, 2, None)] + [(it[1][0], 1, None) for it in sc.items(part, src) if it[1] != 'Rest']
    return top, low


def lines(x):
    top, low = strings_16ths(x)
    oboe = twice(ev(DESCANT))
    oboe[86] = [(None, 6, None), ('F5', 2, None)]
    return {
        'P28': twice(up(TUNE)), 'P29': twice(ev(TUNE)), 'P6': twice(ev(TUNE)), 'P1': twice(up(TUNE, 2)),
        'P2': twice(up(DESCANT)), 'P3': oboe, 'P30': top, 'P31': low,
        'P32': twice(ev(LOW)), 'P8': twice(ev(LOW)),
        'P7': twice({b: [(n, 2, None) for n in names] for b, names in BASS.items()}),
        **{pid: held(h) for pid, h in HOLD.items()},
        'P17': twice(ev(TIMPANI)),
    }


def bar_85(x):
    """Violin I: the descant's D, then sixteenths up to its octave; the piccolo the same run an octave up"""
    x = put(x, 'P28', 85, [(n, q, None) for n, q in RUN_85])
    return put(x, 'P1', 85, [(None, 2, None)] + [(octave(n, 1), q, None) for n, q in RUN_85[1:]])


def harp(x):
    for b in GRAND:
        lh, rh = HARP[86 + (b - 86) % 4]
        s0, s1 = measure_span(x, 'P26', b)
        x = x[:s0] + re.sub(r'<note[ >].*?</note>|<backup>.*?</backup>', '', x[s0:s1], flags=re.S) + x[s1:]
        x = harp_bar(x, 'P26', b, lh, rh)
    return x


def flute_86(x):
    """the flute keeps its A from S30 (where S30's slur ends) and plays the descant's F after it"""
    s0, s1 = measure_span(x, 'P2', 86)
    body = x[s0:s1]
    rests = list(re.finditer(r'<note>\s*<rest/>.*?</note>|<note><rest/>.*?</note>', body, re.S))
    assert len(rests) == 1 and '<duration>2</duration>' in rests[0].group(0), 'flute bar 86: one eighth rest expected'
    f6 = p111326_s5.write_bar(put(x, 'P2', 86, [(None, 8, None)]), 'P2', 86, [(None, 6, None), ('F6', 2, None)])
    a0, a1 = measure_span(f6, 'P2', 86)
    note = re.findall(r'<note>(?:(?!</note>).)*<pitch>.*?</note>', f6[a0:a1], re.S)[-1]
    r = rests[0]
    return x[:s0] + body[:r.start()] + note + body[r.end():] + x[s1:]


def notes(x):
    ls = lines(x)
    x = bar_85(x)
    x = flute_86(x)
    for pid, bars in ls.items():
        for b, evs in bars.items():
            if (pid, b) == ('P2', 86):
                continue
            x = put(x, pid, b, list(evs))
    x = harp(x)
    for pid in ('P28', 'P29', 'P6', 'P1', 'P2', 'P3', 'P7'):
        x = beam_eighths(x, pid, range(85, 94))
    for pid, bars in (('P30', GRAND), ('P31', GRAND), ('P28', [85]), ('P1', [85])):
        for b in bars:
            x = beam16(x, pid, b)
    return x


PARTS = ('P28', 'P29', 'P6', 'P1', 'P2', 'P3', 'P30', 'P31', 'P32', 'P8', 'P7', 'P9', 'P10', 'P14', 'P15', 'P11')
STRING_SLURS = [((86, 0), (86, 1)), ((88, 0), (88, 1)), ((89, 1), (89, 3 * H))]


def firsts(sc, pid, bar):
    return [it[0] for it in sc.items(pid, bar) if it[1] != 'Rest' and not it[2]]


def lasts(sc, pid, bar):
    """the last note that starts in the bar, or the start of the note held into it"""
    f = firsts(sc, pid, bar)
    return f[-1] if f else sc.chain_start(pid, bar, 0)[1]


def last_at(sc, pid, bar):
    f = firsts(sc, pid, bar)
    return (bar, f[-1]) if f else sc.chain_start(pid, bar, 0)


def wind_slurs(sc, pid):
    """one slur over each phrase: the descant's phrases start on its F, the others on the downbeat"""
    if pid in ('P2', 'P3'):
        return [((86, 3 * H), (90, 0)), ((90, 3 * H), (93, 3 * H))]
    out = [((86, firsts(sc, pid, 86)[0]), last_at(sc, pid, 89)), ((90, firsts(sc, pid, 90)[0]), last_at(sc, pid, 93))]
    return ([((85, H), (86, 0))] if pid == 'P1' else []) + out


WINDS = ('P1', 'P6', 'P2', 'P3', 'P9', 'P10', 'P14', 'P15', 'P11')


def swell(sc, pid):
    """the crescendo of the first time through: from the first note of bar 86 to the last of bar 89"""
    first = (86, firsts(sc, pid, 86)[0]) if firsts(sc, pid, 86) else sc.chain_start(pid, 86, 0)
    return first, (89, lasts(sc, pid, 89))


def build(x):
    y = notes(x)
    sc = Score(y)
    m = Marks(y)
    for pid in PARTS:
        m.dynamic(pid, *swell(sc, pid)[0], 'f')
        m.dynamic(pid, 90, firsts(sc, pid, 90)[0], 'ff')
        m.hairpin(pid, swell(sc, pid)[0], (90, 0), 'crescendo')
    m.dynamic('P17', 87, 0, 'f')
    m.dynamic('P17', 91, 0, 'ff')
    m.dynamic('P26', 86, 0, 'f')
    m.dynamic('P26', 90, 0, 'ff')
    m.dynamic('P1', 85, H, 'mf')
    m.hairpin('P1', (85, H), (86, 0), 'crescendo')
    m.slur('P28', (85, 0), (86, 0))
    for pid in ('P28', 'P29'):
        for a, z in STRING_SLURS:
            m.slur(pid, a, z)
            m.slur(pid, (a[0] + 4, a[1]), (z[0] + 4, z[1]))
    for pid in WINDS:
        for a, z in wind_slurs(sc, pid):
            m.slur(pid, a, z)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
