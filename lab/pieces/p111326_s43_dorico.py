"""The Dorico steps for 111326 S43 (lab/pieces/p111326_s43.py), on his export of Nov 25: the steps of S42 with
the quarter notes of bar 118 in horn 2, Wagner tuba and trombone (typed with their lines), horn 1's bar 118 C
typed and tied from his C of bar 117, the bassoon's and clarinet's off-beats (staccato over each range), the
basses' and contrabassoon's both beats, the harp's off-beat chords staff by staff (its B flats and D flats
checked as repeated single notes); then the slurs (with the three fades into bar 118), the hairpins and the
dynamics.
usage (whisperer env): python lab/pieces/p111326_s43_dorico.py <export.xml> <S43.dorico.json>"""
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
import p111326_s43 as s43  # noqa: E402

H = Fraction(1, 2)
ORDER = ['P10', 'P11', 'P14', 'P15', 'P29', 'P30', 'P31', 'P32', 'P8', 'P7', 'P6', 'P9']


def harp_line(staff):
    out = []
    for b in range(min(s43.HARP), max(s43.HARP) + 1):
        out += [(n, Fraction(d, 4)) for n, d in s43.harp_events(b, staff)]
    k = next(i for i, e in enumerate(out) if e[0] is not None)
    return sum((e[1] for e in out[:k]), Fraction(0)), out[k:]


def plan(x):
    p = Plan(x)
    final = s43.notes(x)
    untied = s43.notes(x, tied=False)
    want = Score(final)
    last = [it[0] for it in p.cur.nav('P14', 127)][-1]
    p.step('Trombone: his chords of bars 115-127 out', 'P14', 115, 0, to=(127, last), edits=['Edit.Delete'])
    state = x
    for b in s42.BARS:
        state = put(state, 'P14', b, [(None, 8, None)])
    p.use(state)
    ls = s43.lines()
    for pid in ORDER:
        bars = ls[pid]
        evs = events(bars, (min(bars), 0))
        k = next(i for i, e in enumerate(evs) if e[0] is not None)
        start = (min(bars), sum((Fraction(e[1]) for e in evs[:k]), Fraction(0)))
        p.notes(pid, *start, evs[k:])
        state = copy_bars(state, untied, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in Score(state).items(pid, b) if it[1] != 'Rest' and not it[2]]
        p.after_notes(state, pid, *typed[-1])
        for b, o, n in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=n)
    p.tie('P9', 117, 0)
    state = copy_bars(state, final, 'P9', [117, 118])
    p.use(state)
    first = min(s43.HARP)
    for staff in (1, 2):
        onset, evs = harp_line(staff)
        p.notes('P26', first, onset, evs, staff=staff)
    state = copy_bars(state, final, 'P26', sorted(s43.HARP))
    p.use(state)
    for b in (126, 127):
        for o in (H, 3 * H):
            p.spell('P26', b, o, staff=2)
    for o in (H, 3 * H):
        p.spell('P26', 127, o, staff=1)
    p.articulate('P7', (124, H), (127, 3 * H), 'kStaccato')
    p.articulate('P6', (126, H), (127, 3 * H), 'kStaccato')
    for pid, sl in s42.SLURS.items():
        for a, z in sl:
            p.slur(pid, a, z)
    for pid in s43.INTO_118:
        p.slur(pid, s43.FADE_FROM[pid] if pid == 'P11' else (117, 0), (118, 0))
    for pid, (a, peak, end) in s42.SWELLS.items():
        p.hairpin(pid, a, s39d.before(want, pid, peak))
        p.hairpin(pid, peak, s39d.before(want, pid, end), up=False)
    for pid in s43.INTO_118:
        p.hairpin(pid, s43.FADE_FROM[pid], s43.FADE_FROM[pid], up=False)
    p.dynamic('P9', 115, 0, 'mp')
    for pid, (a, peak, end) in s42.SWELLS.items():
        p.dynamic(pid, *a, 'mp')
        p.dynamic(pid, *peak, 'mf')
        p.dynamic(pid, *end, 'p')
    for pid, at in list(s42.SOFT.items()) + list(s42.AGAIN.items()):
        p.dynamic(pid, *at, 'p')
    for pid in s43.INTO_118:
        p.dynamic(pid, 118, 0, 'pp')
    p.dynamic('P26', 122, 3 * H, 'p')
    p.dynamic('P7', 124, H, 'p')
    p.dynamic('P6', 126, H, 'p')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S43: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
