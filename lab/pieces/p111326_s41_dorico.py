"""The Dorico steps for 111326 S41 (lab/pieces/p111326_s41.py), on his export of Nov 24: his viola chords of
bars 110-114 deleted, then Violin II, violas, cellos, basses, contrabassoon and the clarinet's bar 110 typed,
their sharps checked, pizz. for the basses, then the slurs, the oboe's two hairpins (each selected up to the
note before its target) and the dynamics.
usage (whisperer env): python lab/pieces/p111326_s41_dorico.py <export.xml> <S41.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s41 as s41  # noqa: E402

H = Fraction(1, 2)
ORDER = ['P29', 'P30', 'P31', 'P32', 'P8', 'P6']


def plan(x):
    p = Plan(x)
    final = s41.notes(x)
    want = Score(final)
    last = [it[0] for it in p.cur.nav('P30', 114)][-1]
    p.step('Viola: his chords of bars 110-114 out', 'P30', 110, 0, to=(114, last), edits=['Edit.Delete'])
    state = x
    for b in s41.BARS:
        state = put(state, 'P30', b, [(None, 8, None)])
    p.use(state)
    ls = s41.lines()
    for pid in ORDER:
        bars = ls[pid]
        p.notes(pid, 110, 0, events(bars, (110, 0)))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2]]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, (110, 0))):
            p.spell(pid, b, o, group=k)
    p.technique('P32', 110, 0, 'pizz.')
    for pid, sl in s41.SLURS.items():
        for a, z in sl:
            p.slur(pid, a, z)
    om = s41.OBOE_MARKS
    p.hairpin('P3', om['start'], (111, 3 * H))
    p.hairpin('P3', om['dim_from'], (113, 3 * H), up=False)
    for pid, at in s41.HIS_PEAKS.items():
        p.dynamic(pid, *at, 'f')
    p.dynamic('P6', 110, 0, 'p')
    p.dynamic('P3', *om['start'], 'mp')
    p.dynamic('P3', *om['peak'], 'mf')
    p.dynamic('P3', *om['last'], 'p')
    for pid in ('P29', 'P30', 'P32', 'P8'):
        p.dynamic(pid, 110, 0, 'p')
    p.dynamic('P31', 110, 0, 'mp')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S41: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
