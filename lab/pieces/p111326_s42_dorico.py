"""The Dorico steps for 111326 S42 (lab/pieces/p111326_s42.py), on his export of Nov 24, 07:39: his chords on the
trombone staff (bars 115-127) deleted, then every line typed (horn 2, Wagner tuba, trombone, bass trombone,
Violin II, violas, cellos, and the pizzicato bass in the basses and contrabassoon, still pizz. from S41), their
sharps and flats checked; then the slurs, the clarinet's and oboe's swells (each hairpin selected up to the note
before its target) and the dynamics.
usage (whisperer env): python lab/pieces/p111326_s42_dorico.py <export.xml> <S42.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s39_dorico as s39d  # noqa: E402
import p111326_s42 as s42  # noqa: E402

ORDER = ['P10', 'P11', 'P14', 'P15', 'P29', 'P30', 'P31', 'P32', 'P8']


def plan(x):
    p = Plan(x)
    final = s42.notes(x)
    want = Score(final)
    last = [it[0] for it in p.cur.nav('P14', 127)][-1]
    p.step('Trombone: his chords of bars 115-127 out', 'P14', 115, 0, to=(127, last), edits=['Edit.Delete'])
    state = x
    for b in s42.BARS:
        state = put(state, 'P14', b, [(None, 8, None)])
    p.use(state)
    ls = s42.lines()
    for pid in ORDER:
        bars = ls[pid]
        start = (min(bars), 0)
        evs = events(bars, start)
        k = next(i for i, e in enumerate(evs) if e[0] is not None)
        start = (start[0], sum((Fraction(e[1]) for e in evs[:k]), Fraction(0)))
        p.notes(pid, *start, evs[k:])
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2]]
        p.after_notes(state, pid, *typed[-1])
        for b, o, n in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=n)
    for pid, sl in s42.SLURS.items():
        for a, z in sl:
            p.slur(pid, a, z)
    for pid, (a, peak, end) in s42.SWELLS.items():
        p.hairpin(pid, a, s39d.before(want, pid, peak))
        p.hairpin(pid, peak, s39d.before(want, pid, end), up=False)
    p.dynamic('P9', 115, 0, 'mp')
    for pid, (a, peak, end) in s42.SWELLS.items():
        p.dynamic(pid, *a, 'mp')
        p.dynamic(pid, *peak, 'mf')
        p.dynamic(pid, *end, 'p')
    for pid, at in list(s42.SOFT.items()) + list(s42.AGAIN.items()):
        p.dynamic(pid, *at, 'p')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S42: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
