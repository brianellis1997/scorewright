"""The Dorico steps for 111326 S36 (lab/pieces/p111326_s36.py), on his export of Nov 23: his trumpet line of
bars 106-108 deleted and typed in Violin I an octave up; one quarter note of bar 106 typed in each part
that fades over bar 105; then the slurs (Violin I's, and each fade's last note into its bar 106 note),
and the dynamics (p in bar 106, mp for Violin I, fff in bar 96, ff in bar 97).
usage (whisperer env): python lab/pieces/p111326_s36_dorico.py <export.xml> <S36.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
import p111326_s35 as s35  # noqa: E402
import p111326_s36 as s36  # noqa: E402

H = Fraction(1, 2)


def plan(x, extra_slurs=()):
    """extra_slurs: more parts slurred from their last note of bar 105 into bar 106 (S37)"""
    p = Plan(x)
    sc0 = Score(x)
    final = s36.notes(x)
    p.step('Trumpet 1: his line of bars 106-108 out', 'P12', 106, 0, to=(108, 0), edits=['Edit.Delete'])
    state = x
    for b in (106, 107, 108):
        state = put(state, 'P12', b, [(None, 8, None)])
    p.use(state)
    p.notes('P28', 106, 0, [('G6', 3 * H), ('F6', H), ('E6', 3 * H), ('B5', H)])
    state = copy_bars(state, final, 'P28', [106, 107])
    p.after_notes(state, 'P28', 107, 3 * H)
    for pid, n in s36.CARRY.items():
        p.notes(pid, 106, 0, [(n, 1)])
        state = copy_bars(state, final, pid, [106])
        p.after_notes(state, pid, 106, 0)
    for b in s35.VIOLIN:
        p.slur('P28', (b, 0), (b, 3 * H))
    for pid in list(s36.CARRY) + list(extra_slurs):
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
    assert not bad, f'the steps do not end at S36: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
