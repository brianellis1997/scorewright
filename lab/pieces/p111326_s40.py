"""111326 S40 (Nov 23 2026): S39 again, after Brian's note: "we're missing the continuation of the melody that
the first violin is playing... I don't know how I feel about the contrabass playing a line but not the
violas... I like the line... actually I think it's fine". Builds on his export after S38.
- Violin I's melody goes on: from bar 110 it plays its melody again (G F | E B | C D E G F | E F) and
  arrives on E in bar 114. Its E of bar 110 becomes the melody's first G, so the line rises E F G; mf, with
  the melody's slurs and a decrescendo to mp on the E of bar 114.
- The violas join the cellos' theme in unison, mp, so the strings come in as a section; the basses stay as
  the floor under the bassoon.
- The flute's octave doubling of the tune is gone: it sat in Violin I's octave.
- The rest as in S39: the tune in the clarinet, the oboe's descant from its A, horns, bassoon and basses on
  F, Dm, C, C, the swells to f and back to mp, f on the peaks of his swells in bar 108.
usage (whisperer env): python lab/pieces/p111326_s40.py <export.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import put  # noqa: E402
import p111326_s33 as s33  # noqa: E402
import p111326_s39 as s39  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
VIOLIN = {110: [('G6', 6, None), ('F6', 2, None)], 111: [('E6', 6, None), ('B5', 2, None)],
          113: [('E6', 6, None), ('F6', 2, None)], 114: [('E6', 4, None), (None, 4, None)]}
TRIPLET_BAR = 112
VIOLIN_SLURS = [((110, 0), (110, 3 * H)), ((111, 0), (111, 3 * H)), ((112, 0), (112, Fraction(2, 3))), ((112, 1), (112, 3 * H)),
                ((113, 0), (113, 3 * H))]
PARTS = ('P3', 'P6', 'P9', 'P10', 'P7', 'P31', 'P32', 'P30')


def triplet_at(x, pid, bar):
    """Violin I's triplet bar (C D E as eighth triplets, then G F), as s33.triplet_bar writes bar 99"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    assert '<pitch>' not in body, f'{pid} bar {bar} is not empty'
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', body, re.S))
    keep = re.sub(r'<divisions>\d+</divisions>', '<divisions>12</divisions>', keep) if '<divisions>' in keep else keep + '<attributes><divisions>12</divisions></attributes>'
    tm = '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes><normal-type>eighth</normal-type></time-modification>'
    state, out = {}, []
    for i, n in enumerate(s33.TRIPLET):
        p, acc = s33.pitch_xml(x, pid, n, state)
        tup = {0: '<tuplet type="start" bracket="yes" number="1"/>', 2: '<tuplet type="stop" bracket="yes" number="1"/>'}.get(i, '')
        out.append(f'<note>{p}<duration>4</duration><voice>1</voice><type>eighth</type>{acc}{tm}<staff>1</staff>'
                   f'<beam number="1">{("begin", "continue", "end")[i]}</beam>' + (f'<notations>{tup}</notations>' if tup else '') + '</note>')
    for i, n in enumerate(s33.AFTER):
        p, acc = s33.pitch_xml(x, pid, n, state)
        out.append(f'<note>{p}<duration>6</duration><voice>1</voice><type>eighth</type>{acc}<staff>1</staff>'
                   f'<beam number="1">{("begin", "end")[i]}</beam></note>')
    x = x[:s0] + keep + ''.join(out) + x[s1:]
    n0, n1 = measure_span(x, pid, bar + 1)
    if '<divisions>' not in x[n0:n1]:
        x = x[:n0] + '<attributes><divisions>4</divisions></attributes>' + x[n0:]
    return x


def lines():
    ls = {pid: bars for pid, bars in s39.lines().items() if pid != 'P2'}
    ls['P30'] = ls['P31']
    return ls


def check(x):
    sc = Score(x)
    assert [(it[0], it[1]) for it in sc.items('P28', 110)] == [(0, ['E6']), (1, 'Rest')]
    for b in (111, 112, 113, 114):
        assert all(it[1] == 'Rest' for it in sc.items('P28', b)), b
    for b in s39.BARS:
        assert all(it[1] == 'Rest' for it in sc.items('P30', b)), b


def notes(x):
    check(x)
    s39.check(x)
    for pid, bars in lines().items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    for b, evs in VIOLIN.items():
        x = put(x, 'P28', b, evs)
    x = triplet_at(x, 'P28', TRIPLET_BAR)
    for pid in ('P6', 'P3', 'P31', 'P30'):
        x = beam_eighths(x, pid, s39.BARS)
    return x


def build(x):
    y = notes(x)
    m = Marks(y)
    for pid, sl in s39.SLURS.items():
        if pid != 'P2':
            for a, z in sl:
                m.slur(pid, a, z)
    for a, z in s39.SLURS['P31']:
        m.slur('P30', a, z)
    for a, z in VIOLIN_SLURS:
        m.slur('P28', a, z)
    for pid in ('P6', 'P3'):
        m.dynamic(pid, 110, 0, 'mf')
        m.hairpin(pid, (110, 0), s39.PEAK[pid], 'crescendo')
        m.dynamic(pid, *s39.PEAK[pid], 'f')
        m.hairpin(pid, s39.PEAK[pid], s39.LAST[pid], 'diminuendo')
        m.dynamic(pid, *s39.LAST[pid], 'mp')
    m.dynamic('P32', 110, 0, 'p')
    m.dynamic('P30', 110, 0, 'mp')
    m.dynamic('P28', 110, 0, 'mf')
    m.hairpin('P28', (113, 0), (114, 0), 'diminuendo')
    m.dynamic('P28', 114, 0, 'mp')
    for pid, at in s39.HIS_PEAKS.items():
        m.dynamic(pid, *at, 'f')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
