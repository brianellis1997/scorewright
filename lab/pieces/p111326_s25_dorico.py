"""The Dorico steps for 111326 S25 (lab/pieces/p111326_s25.py), on his project as exported at 17:30.
His F in bar 61 moves down two scale steps to D (it keeps its ID and his slur); the old flute echo of
bars 65-72 is deleted and the new figures typed from beat 1.5 of bar 65, then their slurs; then the
swell on his line in bars 73-77.
usage (whisperer env): python lab/pieces/p111326_s25_dorico.py <working.xml> <S25.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
import p111326_s25 as s25  # noqa: E402


def plan(x):
    p = Plan(x)
    p.pitch('P2', 61, 1, -2)
    p.step('Flute: the old echo in bars 65-72 out', 'P2', 65, 1, to=(72, 0), edits=['Edit.Delete'])
    cleared = s25.fix_61(x)
    for b in range(65, 73):
        cleared = put(cleared, 'P2', b, [(None, 8, None)])
    p.use(cleared)
    events = []
    for b, evs in sorted(s25.bars().items()):
        for n, d, t in evs[1:] if b == 65 else evs:
            events.append((n, Fraction(d, 4)))
    while events[-1][0] is None:
        events.pop()
    p.notes('P2', 65, Fraction(1, 2), events)
    final = s25.notes(x)
    p.after_notes(final, 'P2', 72, 0)
    for b in s25.FIGURES:
        p.slur('P2', (b, Fraction(1, 2)), (b + 1, 0))
    p.hairpin('P2', (73, Fraction(1, 2)), (76, Fraction(1, 2)))
    p.hairpin('P2', (76, 1), (77, 0), up=False)
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S25: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
