"""The Dorico steps for 111326 S31 (lab/pieces/p111326_s31.py), on S30. Every line is typed (Violin I
and the piccolo from beat 1.5 of bar 85; the flute after its A in bar 86, the oboe from its F; the
harp staff by staff), its sharps and flats checked; then the slurs, the crescendos and the dynamics.
usage (whisperer env): python lab/pieces/p111326_s31_dorico.py <S30.xml> <S31.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import octave  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals, events  # noqa: E402
import p111326_s31 as s31  # noqa: E402

H = Fraction(1, 2)


def harp_events(staff):
    out = []
    for b in s31.GRAND:
        lh, rh = s31.HARP[86 + (b - 86) % 4]
        out += [(None, 1)] + [(n, Fraction(1, 4)) for n in rh] if staff == 1 else [(n, Fraction(1, 4)) for n in lh] + [(None, 1)]
    while out[-1][0] is None:
        out.pop()
    return out


def plan(x):
    p = Plan(x)
    final = s31.notes(x)
    want = Score(final)
    state = x
    ls = s31.lines(x)
    ls['P28'] = {85: [(n, q, None) for n, q in s31.RUN_85], **ls['P28']}
    ls['P1'] = {85: [(None, 2, None)] + [(octave(n, 1), q, None) for n, q in s31.RUN_85[1:]], **ls['P1']}
    starts = {'P28': (85, H), 'P1': (85, H), 'P2': (86, 3 * H), 'P3': (86, 3 * H), 'P30': (86, H), 'P31': (86, H), 'P17': (87, 0)}
    for pid, bars in ls.items():
        start = starts.get(pid, (86, 0))
        p.notes(pid, *start, events(bars, start))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2] and (b, it[0]) >= start]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=k)
    for staff in (1, 2):
        p.notes('P26', 86, 0, harp_events(staff), staff=staff)
    state = copy_bars(state, final, 'P26', s31.GRAND)
    p.use(state)
    for b in (89, 93):
        p.spell('P26', b, 3 * H, staff=1)
    p.slur('P28', (85, 0), (86, 0))
    for pid in ('P28', 'P29'):
        for a, z in s31.STRING_SLURS:
            p.slur(pid, a, z)
            p.slur(pid, (a[0] + 4, a[1]), (z[0] + 4, z[1]))
    for pid in s31.WINDS:
        for a, z in s31.wind_slurs(want, pid):
            p.slur(pid, a, z)
    p.hairpin('P1', (85, H), (85, Fraction(7, 4)))
    for pid in s31.PARTS:
        p.hairpin(pid, s31.swell(want, pid)[0], s31.last_at(want, pid, 89))
    p.dynamic('P1', 85, H, 'mf')
    for pid in s31.PARTS:
        p.dynamic(pid, *s31.swell(want, pid)[0], 'f')
        p.dynamic(pid, 90, s31.firsts(want, pid, 90)[0], 'ff')
    p.dynamic('P17', 87, 0, 'f')
    p.dynamic('P17', 91, 0, 'ff')
    p.dynamic('P26', 86, 0, 'f', staff=2)
    p.dynamic('P26', 90, 0, 'ff', staff=2)
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S31: {bad[:6]}'
    p.save(sys.argv[2], requires=['S30'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
