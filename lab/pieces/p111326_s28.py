"""111326 S28 (Nov 17 2026), Brian's new phrase from bar 78 and his notes on it: "spread out the
cello... move the top line to the viola... you can completely replace the viola section it started in
bar 78 with top note in the cellos"; "the G sharp going up to an F is a bit awkward in the double
bass... it can go from like a G sharp to an E and then an F"; "the cello can of course double the
double bass an octave up"; "the flute can be doubling the violin two an octave higher... while the
clarinet in B flat takes the first violins"; "a more intense section... mezzo forte... make it
crescendo and decrescendo as it leads into... bar 80... the lines repeat".
- Bar 77: the basses G sharp then E in quarters, into his F; the cellos the same an octave up.
- Bars 78-86: Violin I and Violin II swap lines, so the descant (which starts above the tune) is in
  Violin I and the tune in Violin II; each keeps his slurs.
- His cello double stops split: the top notes go to the violas (in place of their part), the bottom
  notes stay in the cellos. His viola notes become the horns' held harmony (horn 1 the upper line
  C and D, horn 2 the lower one, A, A flat, G).
- The B-flat clarinet doubles the tune. The flute joins on the repeat, from beat 2.5 of bar 82, an
  octave above the descant, so the repeat grows.
- The bassoon plays the bass in eighths (its C from bar 76 now ends at bar 78, and so does the
  violas' E, which would rub a half step against the bassoon's F).
- mf from bar 78; each half of the phrase swells to bar 80 (and 84) and falls away after it. The
  horns hold their harmony mp, under the swells.
usage (whisperer env): python lab/pieces/p111326_s28.py <working.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s5 import concert_of, voice_one, write_bar  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import held, name_of, octave, put  # noqa: E402
from p111326_s15 import beam16  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
PHRASE = range(78, 86)
H1 = {78: [('C4', 8)], 79: [('D4', 4), ('C4', 4)], 80: [('C4', 8)], 81: [('C4', 8)]}
H2 = {78: [('A3', 8)], 79: [('A3', 6), ('Ab3', 2)], 80: [('G3', 8)], 81: [('G3', 6), ('Ab3', 2)]}
BASS = {78: ['F3'] * 4, 79: ['D3'] * 4, 80: ['C3'] * 4, 81: ['C3', 'C3', 'E3', 'E3']}
SWELLS = [((78, 79), True), ((80, 81), False), ((82, 83), True), ((84, 85), False)]


def line_of(x, pid, bars):
    """{bar: [(concert name or None, divisions, tie)]} of a one-voice part"""
    out = {}
    for b in bars:
        evs = []
        for t, s0, s1, n in voice_one(x, pid, b):
            d = int(re.search(r'<duration>(\d+)</duration>', n).group(1))
            if '<rest' in n:
                evs.append((None, d, None))
                continue
            stop, start = '<tie type="stop"/>' in n, '<tie type="start"/>' in n
            evs.append((name_of(concert_of(x, pid, n)), d, 'both' if stop and start else 'start' if start else 'stop' if stop else None))
        out[b] = evs
    return out


def split_cello(x):
    """his cello double stops, bar by bar: (top line, bottom line) as sixteenths after an eighth rest"""
    sc = Score(x)
    top, low = {}, {}
    for b in PHRASE:
        notes = [it for it in sc.items('P31', b) if it[1] != 'Rest']
        assert [it[0] for it in notes] == [Fraction(k, 4) for k in range(2, 8)], (b, notes)
        top[b] = [(None, 2, None)] + [(it[1][0], 1, None) for it in notes]
        low[b] = [(None, 2, None)] + [(it[1][-1], 1, None) for it in notes]
    return top, low


def repeat(d):
    """bars 78-81 again as 82-85"""
    return {**d, **{b + 4: v for b, v in d.items()}}


def sustained(lines):
    """[(name, divisions)] per bar, tied where the same note goes on over the bar line"""
    bars = sorted(lines)
    out = {b: [[n, d, None] for n, d in lines[b]] for b in bars}
    for a, b in zip(bars, bars[1:]):
        last, first = out[a][-1], out[b][0]
        if last[0] == first[0]:
            last[2] = 'both' if last[2] == 'stop' else 'start'
            first[2] = 'both' if first[2] == 'start' else 'stop'
    return {b: [tuple(e) for e in evs] for b, evs in out.items()}


def lines(x):
    """{pid: {bar: events}} for every part S28 writes"""
    tune, descant = line_of(x, 'P28', range(78, 87)), line_of(x, 'P29', range(78, 87))
    top, low = split_cello(x)
    flute = {b: [(octave(n, 1), d, t) for n, d, t in descant[b]] for b in range(82, 87)}
    flute[82] = [(None, 4, None), (None, 2, None)] + flute[82][1:]
    return {
        'P28': descant, 'P29': tune, 'P30': top, 'P31': {77: [('G#2', 4, None), ('E3', 4, None)], **low},
        'P32': {77: [('G#1', 4, None), ('E2', 4, None)]},
        'P6': {b: tune[b] for b in PHRASE}, 'P2': flute,
        'P9': sustained(repeat(H1)), 'P10': sustained(repeat(H2)),
        'P7': {b: [(n, 2, None) for n in names] for b, names in repeat(BASS).items()},
    }


def untie_77(x, pid):
    """a note held from before ends at bar 78: no tie from bar 77 (the bassoon's C; the violas' E,
    which rubbed a half step against the bassoon's new F on the downbeat of bar 78)"""
    s0, s1 = measure_span(x, pid, 77)
    body = x[s0:s1]
    assert body.count('<tie type="start"/>') == 1, f'{pid} bar 77: one tie start expected'
    body = body.replace('<tie type="start"/>', '', 1).replace('<tied type="start"/>', '', 1)
    return x[:s0] + body + x[s1:]


def notes(x):
    ls = lines(x)
    x = untie_77(untie_77(x, 'P7'), 'P30')
    for pid, bars in ls.items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    for pid in ('P28', 'P29', 'P6', 'P2', 'P7'):
        x = beam_eighths(x, pid, range(77, 87))
    for pid in ('P30', 'P31'):
        for b in PHRASE:
            x = beam16(x, pid, b)
    return x


def chains(sc, pid, bar):
    return [it[0] for it in sc.items(pid, bar) if it[1] != 'Rest' and not it[2]]


def swells(sc, pid):
    """(start, end, up) for each swell this part plays in"""
    out = []
    for (a, z), up in SWELLS:
        first, last = chains(sc, pid, a), chains(sc, pid, z)
        if first and last:
            out.append(((a, first[0]), (z, last[-1]), up))
    return out


SLURS_FROM = {'P28': 'P29', 'P29': 'P28', 'P6': 'P28'}
SWELLING = ('P28', 'P29', 'P30', 'P31', 'P32', 'P6', 'P7', 'P2')


def slurs(x, pid):
    """his slurs on a line, for the part that now plays it (the flute: his descant's, from bar 83)"""
    src = 'P29' if pid == 'P2' else SLURS_FROM[pid]
    sc = Score(x)
    out = []
    part = re.search(rf'<part id="{src}">(.*?)</part>', x, re.S).group(1)
    open_ = None
    for mm in re.finditer(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', part, re.S):
        b = int(mm.group(1))
        if not 78 <= b <= 86:
            continue
        t = 0
        for n in re.finditer(r'<note[ >].*?</note>', mm.group(2), re.S):
            s = n.group(0)
            if '<slur type="start"' in s:
                open_ = (b, Fraction(t, 4))
            if '<slur type="stop"' in s and open_:
                out.append((open_, (b, Fraction(t, 4))))
                open_ = None
            if '<chord/>' not in s:
                t += int(re.search(r'<duration>(\d+)</duration>', s).group(1))
    if pid == 'P6':
        out = [s for s in out if s[1][0] <= 85]
    if pid == 'P2':
        out = [s for s in out if s[0][0] >= 83]
    return out


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
    for pid in SWELLING:
        ws = swells(sc, pid)
        first = ws[0][0]
        m.dynamic(pid, *first, 'mf')
        for a, z, up in ws:
            end = sc.item_end(pid, *z)
            m.hairpin(pid, a, end if end[0] <= z[0] or end[1] else (z[0], None), 'crescendo' if up else 'diminuendo')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
