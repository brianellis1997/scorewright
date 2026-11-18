"""The Dorico steps for 111326 S32 (lab/pieces/p111326_s32.py), on S31: every line typed (the violas
and cellos from beat 1.5, the timpani from beat 2 of bar 95, the harp staff by staff), then the
slurs and the crescendos into bar 96.
usage (whisperer env): python lab/pieces/p111326_s32_dorico.py <S31.xml> <S32.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s32 as s32  # noqa: E402

H = Fraction(1, 2)


def plan(x):
    p = Plan(x)
    final = s32.notes(x)
    want = Score(final)
    state = x
    starts = {'P30': (94, H), 'P31': (94, H), 'P17': (95, 1)}
    for pid, bars in s32.LINES.items():
        start = starts.get(pid, (94, 0))
        p.notes(pid, *start, events(bars, start))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2] and (b, it[0]) >= start]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=k)
    for staff in (1, 2):
        evs = []
        for b in s32.BARS:
            lh, rh = s32.HARP[b]
            evs += [(None, 1)] + [(n, Fraction(1, 4)) for n in rh] if staff == 1 else [(n, Fraction(1, 4)) for n in lh] + [(None, 1)]
        while evs[-1][0] is None:
            evs.pop()
        p.notes('P26', 94, 0, evs, staff=staff)
    state = copy_bars(state, final, 'P26', s32.BARS)
    p.use(state)
    for pid in ('P28', 'P29'):
        p.slur(pid, (95, 0), (95, 3 * H))
    for pid, sl in s32.WIND_SLURS.items():
        for a, z in sl:
            p.slur(pid, a, z)
    for pid in s32.MELODIC:
        last = [it[0] for it in want.items(pid, 95) if it[1] != 'Rest' and not it[2]][-1]
        p.hairpin(pid, (94, 0), (95, last))
    p.hairpin('P17', (95, 1), (95, Fraction(7, 4)))
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S32: {bad[:6]}'
    p.save(sys.argv[2], requires=['S31'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
