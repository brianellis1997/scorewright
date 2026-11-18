"""The Dorico steps for 111326 S29 (lab/pieces/p111326_s29.py), on S28. Every line is typed (Violin I
from beat 1.5 of bar 85, over the end of its descant; the harp staff by staff), its sharps and flats
checked; then the slurs, the f and ff, and the crescendos to bar 90.
usage (whisperer env): python lab/pieces/p111326_s29_dorico.py <S28.xml> <S29.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s29 as s29  # noqa: E402

H = Fraction(1, 2)


def harp_events(staff, bar):
    lh, rh = s29.HARP[bar]
    if staff == 1:
        return [(None, 1)] + [(n, Fraction(1, 4)) for n in rh]
    return [(n, Fraction(1, 4)) for n in lh] + [(None, 1)]


def plan(x):
    p = Plan(x)
    final = s29.notes(x)
    want = Score(final)
    state = x
    ls = s29.lines(x)
    ls['P28'] = {85: [(n, q, None) for n, q in s29.RUN_85], **ls['P28']}
    starts = {'P28': (85, H), 'P30': (86, H), 'P31': (86, H), 'P17': (87, 0)}
    for pid, bars in ls.items():
        start = starts.get(pid, (86, 0))
        p.notes(pid, *start, events(bars, start))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2] and (b, it[0]) >= start]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=k)
    for staff in (1, 2):
        evs = [e for b in sorted(s29.HARP) for e in harp_events(staff, b)]
        evs.append((list(s29.HARP_90[2 - staff]), 2))
        p.notes('P26', 86, 0, evs, staff=staff)
    state = copy_bars(state, final, 'P26', range(86, 91))
    p.use(state)
    p.spell('P26', 89, Fraction(3, 2), staff=1)
    p.slur('P28', (85, 0), (86, 0))
    for pid in ('P28', 'P29', 'P5', 'P6'):
        for a, z in [((86, 0), (86, 1)), ((88, 0), (88, 1)), ((89, 1), (89, Fraction(3, 2)))]:
            p.slur(pid, a, z)
    for pid in ('P2', 'P3'):
        for a, z in [((87, 0), (88, 0)), ((89, 0), (89, Fraction(3, 2)))]:
            p.slur(pid, a, z)
    for pid in s29.PARTS:
        a = s29.swell_start(want, pid)
        z = [it[0] for it in want.items(pid, 89) if it[1] != 'Rest' and not it[2]]
        last = (89, z[-1]) if z else want.chain_start(pid, 89, 0)
        p.hairpin(pid, a, last)
    p.hairpin('P17', (89, 1), (89, Fraction(7, 4)))
    for pid in s29.PARTS + ('P17',):
        bar = 87 if pid == 'P17' else 86
        p.dynamic(pid, bar, s29.firsts(want, pid, bar)[0], 'f')
        p.dynamic(pid, 90, 0, 'ff')
    p.dynamic('P26', 86, 0, 'f', staff=2)
    p.dynamic('P26', 90, 0, 'ff', staff=2)
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S29: {bad[:6]}'
    p.save(sys.argv[2], requires=['S28'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
