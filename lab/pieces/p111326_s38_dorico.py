"""The Dorico steps for 111326 S38 (lab/pieces/p111326_s38.py), on his export of Nov 23: the steps of S37
(lab/pieces/p111326_s36_dorico.py with the horns' and bassoon's slurs), plus Brian's Violin I fix: his
line from the second triplet of bar 108 to bar 111 deleted (a range over a whole tuplet removes the
tuplet, scratch test of Nov 23), then G F | E. F | E typed from beat 2 of bar 108 with the caret
brought there from the cellos' note on that beat (inside a tuplet the caret moves by the tuplet's notes),
and the two slurs.
usage (whisperer env): python lab/pieces/p111326_s38_dorico.py <export.xml> <S38.dorico.json>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
import p111326_s35 as s35  # noqa: E402
import p111326_s36 as s36  # noqa: E402
import p111326_s37 as s37  # noqa: E402
import p111326_s38 as s38  # noqa: E402

H = Fraction(1, 2)


def cleared_108(x):
    """Violin I as Dorico has it once the line from the second triplet on is deleted: the first triplet,
    then a quarter rest (bar 108 keeps its 12 divisions), and bars 109-111 empty"""
    s0, s1 = measure_span(x, 'P28', 108)
    body = x[s0:s1]
    notes = list(re.finditer(r'<note[ >].*?</note>', body, re.S))
    rest = '<note><rest/><duration>12</duration><voice>1</voice><type>quarter</type><staff>1</staff></note>'
    x = x[:s0] + body[:notes[2].end()] + rest + body[notes[5].end():] + x[s1:]
    for b in s38.LATER:
        x = put(x, 'P28', b, [(None, 8, None)])
    return x


def plan(x):
    p = Plan(x)
    sc0 = Score(x)
    final = s38.fix(s37.build(x))
    p.step('Trumpet 1: his line of bars 106-108 out', 'P12', 106, 0, to=(108, 0), edits=['Edit.Delete'])
    state = x
    for b in (106, 107, 108):
        state = put(state, 'P12', b, [(None, 8, None)])
    p.use(state)
    p.notes('P28', 106, 0, [('G6', 3 * H), ('F6', H), ('E6', 3 * H), ('B5', H)])
    state = copy_bars(state, final, 'P28', [106, 107])
    p.after_notes(state, 'P28', 107, 3 * H)
    p.step('Violin I: bar 108 beat 2 to bar 111 out', 'P28', 108, 1, to=(111, 0), edits=['Edit.Delete'])
    state = cleared_108(state)
    p.use(state)
    p.notes('P28', 108, 1, [('G6', H), ('F6', H), ('E6', 3 * H), ('F6', H), ('E6', 1)], start=('P31', 1, 108, 1))
    state = copy_bars(state, final, 'P28', [108, 109, 110, 111])
    p.after_notes(state, 'P28', 110, 0)
    for pid, n in s36.CARRY.items():
        p.notes(pid, 106, 0, [(n, 1)])
        state = copy_bars(state, final, pid, [106])
        p.after_notes(state, pid, 106, 0)
    for b in s35.VIOLIN:
        p.slur('P28', (b, 0), (b, 3 * H))
    for a, z in s38.SLURS:
        p.slur('P28', a, z)
    for pid in list(s36.CARRY) + list(s37.INTO_106):
        p.slur(pid, (105, s36.last_of_105(sc0, pid)), (106, 0))
    p.dynamic('P28', 106, 0, 'mp')
    for pid in s36.CARRY:
        p.dynamic(pid, 106, 0, 'p')
    for pid in s36.CLIMAX:
        p.dynamic(pid, 96, 0, 'fff')
    for pid in s36.BACK_TO_FF:
        p.dynamic(pid, 97, 0, 'ff')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S38: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
