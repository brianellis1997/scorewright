"""The Dorico steps for 111326 S39 (lab/pieces/p111326_s39.py), on his export after S38: every line typed
from bar 110 (the oboe's G sharp checked), then the slurs, the swells (each hairpin selected up to the note
before its target, so it ends where the target dynamic sits), and the dynamics, with f on the peaks of
his own swells in bar 108.
usage (whisperer env): python lab/pieces/p111326_s39_dorico.py <export.xml> <S39.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s39 as s39  # noqa: E402

H = Fraction(1, 2)
ORDER = ['P2', 'P3', 'P6', 'P9', 'P10', 'P7', 'P31', 'P32']


def before(sc, pid, at):
    """the last note that starts before (bar, onset), as the start of its tie chain"""
    b, o = at
    its = [(b, it[0]) for it in sc.items(pid, b) if it[1] != 'Rest' and not it[2] and it[0] < o]
    if not its:
        its = [(b - 1, it[0]) for it in sc.items(pid, b - 1) if it[1] != 'Rest' and not it[2]]
    return sc.chain_start(pid, *its[-1])


def plan(x):
    p = Plan(x)
    final = s39.notes(x)
    want = Score(final)
    state = x
    ls = s39.lines()
    for pid in ORDER:
        bars = ls[pid]
        p.notes(pid, 110, 0, events(bars, (110, 0)))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2]]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, (110, 0))):
            p.spell(pid, b, o, group=k)
    for pid, sl in s39.SLURS.items():
        for a, z in sl:
            p.slur(pid, a, z)
    for pid in s39.LEADS:
        p.hairpin(pid, (110, 0), before(want, pid, s39.PEAK[pid]))
        p.hairpin(pid, s39.PEAK[pid], before(want, pid, s39.LAST[pid]), up=False)
    for pid in s39.LEADS:
        p.dynamic(pid, 110, 0, 'mf')
        p.dynamic(pid, *s39.PEAK[pid], 'f')
        p.dynamic(pid, *s39.LAST[pid], 'mp')
    p.dynamic('P32', 110, 0, 'p')
    for pid, at in s39.HIS_PEAKS.items():
        p.dynamic(pid, *at, 'f')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S39: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
