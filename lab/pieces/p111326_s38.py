"""111326 S38 (Nov 23 2026): S37 with Brian's fix to his Violin I line: "the first triplet should stay but
the second triplet should go away, and it should be replaced by two eighth notes with a G and an F... the
same pattern that appeared previously... the G and the F that are quarter notes in the next bar should go
away, and that bar should just be replaced with the... dotted quarter E... all that violin move up a bar".
Violin I's bars 106-110 are now the melody of bars 97-101 an octave... at the same height: G F | E B |
C D E (triplet) G F | E F | E, with the slurs of bars 99 and 100.
usage (whisperer env): python lab/pieces/p111326_s38.py <export.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span  # noqa: E402
from p111326_s10 import put  # noqa: E402
import p111326_s33 as s33  # noqa: E402
import p111326_s37 as s37  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

H = Fraction(1, 2)
AFTER = ['G6', 'F6']
LATER = {109: [('E6', 6, None), ('F6', 2, None)], 110: [('E6', 4, None), (None, 4, None)], 111: [(None, 8, None)]}
SLURS = [((108, 1), (108, 3 * H)), ((109, 0), (109, 3 * H))]


def check(x):
    sc = Score(x)
    got = [[(it[0], it[1][0] if it[1] != 'Rest' else 'r', it[4]) for it in sc.items('P28', b)] for b in (108, 109, 110, 111)]
    t = Fraction(1, 3)
    assert got == [[(0, 'C6', True), (t, 'D6', True), (2 * t, 'E6', True), (1, 'E6', True), (1 + t, 'F6', True), (1 + 2 * t, 'G6', True)],
                   [(0, 'G6', False), (1, 'F6', False)], [(0, 'E6', False), (3 * H, 'F6', False)], [(0, 'E6', False), (1, 'r', False)]], got
    for b in LATER:
        s0, s1 = measure_span(x, 'P28', b)
        assert re.findall(r'<divisions>(\d+)</divisions>', x[s0:s1]) in ([], ['4']), b


def bar_108(x):
    """his first triplet stays; the second gives way to G F as plain eighths (12 divisions, as his bar)"""
    s0, s1 = measure_span(x, 'P28', 108)
    body = x[s0:s1]
    notes = list(re.finditer(r'<note[ >].*?</note>', body, re.S))
    assert len(notes) == 6 and '<time-modification>' in notes[3].group(0)
    state, new = {}, ''
    for i, n in enumerate(AFTER):
        p, acc = s33.pitch_xml(x, 'P28', n, state)
        new += (f'<note>{p}<duration>6</duration><voice>1</voice><type>eighth</type>{acc}<staff>1</staff>'
                f'<beam number="1">{("begin", "end")[i]}</beam></note>')
    return x[:s0] + body[:notes[2].end()] + new + body[notes[5].end():] + x[s1:]


def fix(x):
    """the Violin I fix alone, on a score that has his bars 108-111"""
    check(x)
    x = bar_108(x)
    for b, evs in LATER.items():
        x = put(x, 'P28', b, evs)
    return x


def build(x):
    y = fix(s37.build(x))
    m = Marks(y)
    for a, z in SLURS:
        m.slur('P28', a, z)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
