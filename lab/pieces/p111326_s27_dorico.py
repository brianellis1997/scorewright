"""The Dorico steps for 111326 S27 (lab/pieces/p111326_s27.py), on his project as exported at 18:12.
Two flute figures are deleted (bars 61-62 and 69-70); bar 74 is typed again as two quarters, which
takes his slur's last note, so the slur from bar 73 is made again to the new D.
usage (whisperer env): python lab/pieces/p111326_s27_dorico.py <working.xml> <S27.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
import p111326_s27 as s27  # noqa: E402

H = Fraction(1, 2)


def plan(x):
    p = Plan(x)
    p.step('Flute: bars 61-62 out', 'P2', 61, H, to=(61, 3 * H), edits=['Edit.Delete'])
    p.step('Flute: bars 69-70 out', 'P2', 69, H, to=(70, 0), edits=['Edit.Delete'])
    p.pitch('P2', 75, 1, -2)
    state = s27.fix_75(x)
    for b, events in s27.REST.items():
        state = put(state, 'P2', b, events)
    p.use(state)
    p.notes('P2', 74, 0, [('C5', 1), ('D5', 1)])
    final = s27.notes(x)
    p.after_notes(final, 'P2', 74, 1)
    p.slur('P2', (73, H), (74, 1))
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S27: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
