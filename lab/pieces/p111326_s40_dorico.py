"""The Dorico steps for 111326 S40 (lab/pieces/p111326_s40.py), on his export after S38: the lines of S39
without the flute, the violas with the cellos' theme, and Violin I typed from bar 110 over its E there (the
triplet of bar 112 with NoteInput.StartTupletRun 3:2) to the E of bar 114; then the slurs, the swells and
the dynamics.
usage (whisperer env): python lab/pieces/p111326_s40_dorico.py <export.xml> <S40.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s33 as s33  # noqa: E402
import p111326_s39 as s39  # noqa: E402
import p111326_s39_dorico as s39d  # noqa: E402
import p111326_s40 as s40  # noqa: E402

H = Fraction(1, 2)
ORDER = ['P3', 'P6', 'P9', 'P10', 'P7', 'P31', 'P30', 'P32']
VIOLIN_EVENTS = ([('G6', 3 * H), ('F6', H), ('E6', 3 * H), ('B5', H), ('tuplet', '3:2')] + [(n, H) for n in s33.TRIPLET] +
                 [('end tuplet', '3:2')] + [(n, H) for n in s33.AFTER] + [('E6', 3 * H), ('F6', H), ('E6', 1)])


def plan(x):
    p = Plan(x)
    final = s40.notes(x)
    want = Score(final)
    state = x
    ls = s40.lines()
    for pid in ORDER:
        bars = ls[pid]
        p.notes(pid, 110, 0, events(bars, (110, 0)))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2]]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, (110, 0))):
            p.spell(pid, b, o, group=k)
    p.notes('P28', 110, 0, VIOLIN_EVENTS)
    state = copy_bars(state, final, 'P28', range(110, 115))
    p.after_notes(state, 'P28', 114, 0)
    for pid, sl in s39.SLURS.items():
        if pid != 'P2':
            for a, z in sl:
                p.slur(pid, a, z)
    for a, z in s39.SLURS['P31']:
        p.slur('P30', a, z)
    for a, z in s40.VIOLIN_SLURS:
        p.slur('P28', a, z)
    for pid in ('P6', 'P3'):
        p.hairpin(pid, (110, 0), s39d.before(want, pid, s39.PEAK[pid]))
        p.hairpin(pid, s39.PEAK[pid], s39d.before(want, pid, s39.LAST[pid]), up=False)
    p.hairpin('P28', (113, 0), (113, 3 * H), up=False)
    for pid in ('P6', 'P3'):
        p.dynamic(pid, 110, 0, 'mf')
        p.dynamic(pid, *s39.PEAK[pid], 'f')
        p.dynamic(pid, *s39.LAST[pid], 'mp')
    p.dynamic('P32', 110, 0, 'p')
    p.dynamic('P30', 110, 0, 'mp')
    p.dynamic('P28', 110, 0, 'mf')
    p.dynamic('P28', 114, 0, 'mp')
    for pid, at in s39.HIS_PEAKS.items():
        p.dynamic(pid, *at, 'f')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S40: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
