"""111326 S29 (Nov 17 2026), Brian on S28: "extend the phrase... in a more grandiose way, like the
strings even higher, an octave higher, at least the violin ones... reaching the flutes this time...
really exploding in a burst of passion and melody... we just repeat this four bars thing... more
instruments added, higher octaves in the violins lead in the melody... more support underneath...
doubling the underlying structure... the harp doing a bit more runs and accents... some percussion
in there just highlighting some phrases".
- Bars 86-89, the third statement: the tune in both violins in octaves (Violin I an octave up, with
  the E-flat clarinet; Violin II at pitch, with the B-flat clarinet); the descant in the flute an
  octave up and in the oboe at pitch. Violin I reaches its octave with a sixteenth run that starts
  after the beat in bar 85 (from the descant's D).
- Underneath: the violas' and cellos' sixteenths go on; the bassoon's eighths and the contrabassoon
  (with the basses) on the bass; horns, trombones and Wagner tuba hold the harmony.
- Harp: a rising arpeggio each bar, and a chord on the arrival. Timpani: D on bar 87, a measured roll
  on E into bar 90, A on the arrival.
- His harmony on beat 2 of bar 89 (E, G sharp, C over the bass E) is kept by the brass and the harp.
- In this statement only, the descant's C on beat 2 of bar 87 is B: doubled in octaves, the C would
  rub a minor second against the tune's B in four octaves at once.
- Bar 90: everything lands on A minor (the G sharps rise to A, the cellos' A flat rises to A).
- f from bar 86, a crescendo from bar 88, ff on bar 90.
usage (whisperer env): python lab/pieces/p111326_s29.py <S28.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s5 import write_bar  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
from p111326_s10 import octave, put  # noqa: E402
from p111326_s15 import beam16  # noqa: E402
import p111326_s28 as s28  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
GRAND = range(86, 90)
TUNE = {86: [('D5', 2), ('C5', 2), ('B4', 4)], 87: [('A4', 4), ('B4', 4)], 88: [('C5', 2), ('B4', 2), ('G4', 4)],
        89: [('E4', 4), ('G4', 2), ('C5', 2)], 90: [('A4', 8)]}
DESCANT = {86: [('A4', 6), ('F5', 2)], 87: [('E5', 2), ('D5', 2), ('B4', 2), ('D5', 2, 'start')], 88: [('D5', 6, 'stop'), ('E5', 2)],
           89: [('D5', 2), ('C5', 2), ('B4', 2), ('G#4', 2)], 90: [('A4', 8)]}
RUN_85 = [('D5', 2), ('E5', 1), ('F5', 1), ('G5', 1), ('A5', 1), ('B5', 1), ('C6', 1)]
BASS = {86: ['F3'] * 4, 87: ['D3'] * 4, 88: ['C3'] * 4, 89: ['C3', 'C3', 'E3', 'E3']}
LOW = {86: [('F2', 4), (None, 4)], 87: [('D2', 4), (None, 4)], 88: [('C2', 4), (None, 4)], 89: [('C2', 4), ('E2', 4)], 90: [('A1', 8)]}
HOLD = {'P9': {86: [('C4', 8)], 87: [('D4', 4), ('C4', 4)], 88: [('C4', 8)], 89: [('C4', 8)], 90: [('C4', 8)]},
        'P10': {86: [('A3', 8)], 87: [('A3', 6), ('Ab3', 2)], 88: [('G3', 8)], 89: [('G3', 6), ('Ab3', 2)], 90: [('A3', 8)]},
        'P14': {86: [('A3', 8)], 87: [('A3', 8)], 88: [('G3', 8)], 89: [('G3', 4), ('E3', 4)], 90: [('A3', 8)]},
        'P15': {86: [('F2', 8)], 87: [('D2', 8)], 88: [('C2', 8)], 89: [('C2', 4), ('E2', 4)], 90: [('A1', 8)]},
        'P11': {86: [('F3', 8)], 87: [('F3', 8)], 88: [('E3', 8)], 89: [('E3', 8)], 90: [('E3', 8)]}}
HARP = {86: (('F2', 'C3', 'F3', 'A3'), ('C4', 'F4', 'A4', 'C5')), 87: (('D2', 'A2', 'D3', 'F3'), ('A3', 'D4', 'F4', 'A4')),
        88: (('C2', 'G2', 'C3', 'E3'), ('G3', 'C4', 'E4', 'G4')), 89: (('C2', 'G2', 'C3', 'E3'), ('C4', 'E4', 'G#4', 'C5'))}
HARP_90 = (('A2', 'E3', 'A3'), ('C4', 'E4', 'A4'))
TIMPANI = {87: [('D3', 4), (None, 4)], 89: [(None, 4), ('E2', 1), ('E2', 1), ('E2', 1), ('E2', 1)], 90: [('A2', 4), (None, 4)]}


def ev(d):
    """{bar: [(name, divisions[, tie])]} -> {bar: [(name, divisions, tie)]}"""
    return {b: [(e[0], e[1], e[2] if len(e) > 2 else None) for e in evs] for b, evs in d.items()}


def up(d):
    return {b: [(octave(n, 1), q, t) for n, q, t in evs] for b, evs in ev(d).items()}


def tied(lines):
    """held notes tied over the bar lines of bars 86-89; the arrival in bar 90 is struck again"""
    out = s28.sustained({b: [(n, q) for n, q, *_ in evs] for b, evs in lines.items() if b < 90})
    out[90] = [(n, q, None) for n, q, *_ in lines[90]]
    return out


def strings_16ths(x):
    """the violas' and cellos' sixteenths of bars 78-81 again in 86-89, and their arrival in bar 90"""
    sc = Score(x)
    top, low = {}, {}
    for b in GRAND:
        src = b - 8
        for part, out in (('P30', top), ('P31', low)):
            out[b] = [(None, 2, None)] + [(it[1][0], 1, None) for it in sc.items(part, src) if it[1] != 'Rest']
    top[90], low[90] = [('C4', 8, None)], [('A3', 8, None)]
    return top, low


def lines(x):
    top, low = strings_16ths(x)
    return {
        'P28': {**up(TUNE)}, 'P29': ev(TUNE), 'P5': up(TUNE), 'P6': ev(TUNE),
        'P2': up(DESCANT), 'P3': ev(DESCANT), 'P30': top, 'P31': low,
        'P32': ev(LOW), 'P8': ev(LOW),
        'P7': {**{b: [(n, 2, None) for n in names] for b, names in BASS.items()}, 90: [('A2', 8, None)]},
        **{pid: tied(h) for pid, h in HOLD.items()},
        'P17': ev(TIMPANI),
    }


def run_85(x):
    """Violin I, bar 85: the descant's D, then sixteenths up to the octave"""
    return put(x, 'P28', 85, [(n, q, None) for n, q in RUN_85])


def harp(x):
    for b, (lh, rh) in HARP.items():
        s0, s1 = measure_span(x, 'P26', b)
        x = x[:s0] + re.sub(r'<note[ >].*?</note>|<backup>.*?</backup>', '', x[s0:s1], flags=re.S) + x[s1:]
        x = harp_bar(x, 'P26', b, lh, rh)
    s0, s1 = measure_span(x, 'P26', 90)
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', x[s0:s1], re.S))
    chord = lambda names, staff: ''.join(
        f'<note>{"<chord/>" if i else ""}<pitch><step>{n[0]}</step><octave>{n[-1]}</octave></pitch><duration>8</duration>'
        f'<voice>{staff}</voice><type>half</type><staff>{staff}</staff></note>' for i, n in enumerate(names))
    body = keep + chord(HARP_90[1], 1) + '<backup><duration>8</duration></backup>' + chord(HARP_90[0], 2)
    return x[:s0] + body + x[s1:]


def notes(x):
    ls = lines(x)
    x = run_85(x)
    for pid, bars in ls.items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    x = harp(x)
    for pid in ('P28', 'P29', 'P5', 'P6', 'P2', 'P3', 'P7'):
        x = beam_eighths(x, pid, range(85, 91))
    for pid, bars in (('P30', GRAND), ('P31', GRAND), ('P28', [85]), ('P17', [89])):
        for b in bars:
            x = beam16(x, pid, b)
    return x


PARTS = ('P28', 'P29', 'P5', 'P6', 'P2', 'P3', 'P30', 'P31', 'P32', 'P8', 'P7', 'P9', 'P10', 'P14', 'P15', 'P11')


def firsts(sc, pid, bar):
    return [it[0] for it in sc.items(pid, bar) if it[1] != 'Rest' and not it[2]]


def swell_start(sc, pid):
    """where the crescendo to bar 90 starts: the first note of bar 88, or the start of the note held into it"""
    f = firsts(sc, pid, 88)
    if f and f[0] == 0:
        return (88, 0)
    return sc.chain_start(pid, 88, 0)


def build(x):
    y = notes(x)
    sc = Score(y)
    m = Marks(y)
    for pid in PARTS + ('P17',):
        m.dynamic(pid, 86 if pid != 'P17' else 87, firsts(sc, pid, 86 if pid != 'P17' else 87)[0], 'f')
        m.dynamic(pid, 90, 0, 'ff')
    m.dynamic('P26', 86, 0, 'f')
    m.dynamic('P26', 90, 0, 'ff')
    for pid in PARTS:
        m.hairpin(pid, swell_start(sc, pid), (90, 0), 'crescendo')
    m.hairpin('P17', (89, 1), (90, 0), 'crescendo')
    m.slur('P28', (85, 0), (86, 0))
    for pid, src in (('P28', 'P29'), ('P29', 'P29'), ('P5', 'P29'), ('P6', 'P29')):
        for a, z in [((86, 0), (86, 1)), ((88, 0), (88, 1)), ((89, 1), (89, Fraction(3, 2)))]:
            m.slur(pid, a, z)
    for pid in ('P2', 'P3'):
        for a, z in [((87, 0), (88, 0)), ((89, 0), (89, Fraction(3, 2)))]:
            m.slur(pid, a, z)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
