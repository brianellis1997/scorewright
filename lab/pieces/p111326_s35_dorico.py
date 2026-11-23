"""The Dorico steps for 111326 S35 (lab/pieces/p111326_s35.py), on his export of Nov 23: his trumpet line
of bars 106-108 deleted, the same line typed in Violin I an octave up, the carried quarter notes of bar
106, then the slurs and the dynamics.
usage (whisperer env): python lab/pieces/p111326_s35_dorico.py <export.xml> <S35.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
import p111326_s35 as s35  # noqa: E402

H = Fraction(1, 2)


def plan(x):
    p = Plan(x)
    final = s35.notes(x)
    p.step('Trumpet 1: his line of bars 106-108 out', 'P12', 106, 0, to=(108, 0), edits=['Edit.Delete'])
    state = x
    for b in (106, 107, 108):
        state = put(state, 'P12', b, [(None, 8, None)])
    p.use(state)
    p.notes('P28', 106, 0, [('G6', 3 * H), ('F6', H), ('E6', 3 * H), ('B5', H)])
    state = copy_bars(state, final, 'P28', [106, 107])
    p.after_notes(state, 'P28', 107, 3 * H)
    for pid, n in s35.CARRY.items():
        p.notes(pid, 106, 0, [(n, 1)])
        state = copy_bars(state, final, pid, [106])
        p.after_notes(state, pid, 106, 0)
    for b in s35.VIOLIN:
        p.slur('P28', (b, 0), (b, 3 * H))
    p.dynamic('P28', 106, 0, 'mp')
    for pid in s35.CARRY:
        p.dynamic(pid, 106, 0, 'p')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S35: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
