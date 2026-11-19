"""The Dorico steps for 111326 S34 (lab/pieces/p111326_s34.py), on his export after S32: the steps of S33
(lab/pieces/p111326_s33_dorico.py) with S34's lines (the low end and the rhythm back from bar 98, bars
106-109), the harp's arpeggios between its glissandi, the crescendos over bar 97 and the ff of bar 98,
and the p and mp of bar 106.
usage (whisperer env): python lab/pieces/p111326_s34_dorico.py <export.xml> <S34.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals  # noqa: E402
import p111326_s33 as s33  # noqa: E402
import p111326_s33_dorico as s33d  # noqa: E402
import p111326_s34 as s34  # noqa: E402

H = Fraction(1, 2)
Q = Fraction(1, 4)


def harp_events(staff):
    out = []
    for b in range(96, 106):
        if staff == 1:
            if b in s34.ARPEGGIOS:
                out += [(None, 1)] + [(n, Q) for n in s34.ARPEGGIOS[b][1]]
            else:
                out += [(e[0], Fraction(e[1], 4)) for e in s33.GLISS.get(b, [(None, 8)])]
        elif b >= 97:
            lh = s34.ARPEGGIOS[b][0] if b in s34.ARPEGGIOS else s34.LEFT_101 if b == 101 else None
            if lh:
                out += [(n, Q) for n in lh] + [(None, 1)]
            elif b in s33.STRIKES:
                out += [(s33.STRIKES[b], 1), (None, 1)]
            else:
                out += [(None, 2)]
    if staff == 1:
        out = out[1:]
    while out[-1][0] is None:
        out.pop()
    return out


def plan(x):
    p = Plan(x)
    final = s34.notes(x)
    want = Score(final)
    state = x
    for pid in s33d.HELD:
        p.shorten(pid, 96, 0, 2)
        state = s33d.shortened(state, pid)
    last = [it[0] for it in p.cur.nav('P30', 105)][-1]
    p.step('Viola: his chords of bars 97-105 out', 'P30', 97, 0, to=(105, last), edits=['Edit.Delete'])
    for b in s33.BARS:
        state = put(state, 'P30', b, [(None, 8, None)])
    p.use(state)
    ls = s34.lines()
    for pid, name in s33.PICKUP.items():
        ls[pid][96] = [(s33d.HELD[pid], 4, None), (name, 4, None)]
    for pid in s33d.ORDER:
        bars = ls[pid]
        start = s33d.STARTS.get(pid, (97, 0))
        trip = s33.DOUBLE.get(pid)
        p.notes(pid, *start, s33d.line_events(bars, start, trip))
        state = copy_bars(state, final, pid, sorted(set(bars) | ({99} if trip is not None else set())))
        typed = [(b, it[0]) for b in range(start[0], max(bars) + 1) for it in want.items(pid, b)
                 if it[1] != 'Rest' and not it[2] and (b, it[0]) >= start]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=k)
    p.notes('P26', 96, 1, harp_events(1), staff=1)
    p.notes('P26', 97, 0, harp_events(2), staff=2)
    state = copy_bars(state, final, 'P26', range(96, 106))
    p.use(state)
    for a, z in (((104, 1), (105, 0)), ((104, 0), (104, 1)), ((101, 1), (102, 0)), ((96, 1), (97, 0))):
        p.gliss('P26', a, z)
    for pid, a, z in s34.slurs(want):
        p.slur(pid, a, z)
    for pid in ('P28', 'P29', 'P2'):
        for b in (103, 105):
            p.articulate(pid, (b, 0), (b, 1), 'kStaccatoTenuto')
    for pid in s34.SWELL:
        f = s33.firsts(want, pid, 97)
        p.hairpin(pid, (97, f[0]), (97, f[-1]))
    for pid in ('P12', 'P13'):
        p.hairpin(pid, (101, 1), (102, 3 * H))
    for pid in s33.FADING:
        f = s33.firsts(want, pid, 105)
        p.hairpin(pid, (105, f[0]), (105, f[-1]), up=False)
    p.dynamic('P16', 94, 0, 'ff')
    for pid in s33.ACCOMP:
        p.dynamic(pid, 97, s33.firsts(want, pid, 97)[0], 'f')
    for pid in s34.SWELL + ('P17',):
        p.dynamic(pid, 98, s33.firsts(want, pid, 98)[0], 'ff')
    for pid in ('P12', 'P13'):
        p.dynamic(pid, 101, 1, 'f')
        p.dynamic(pid, 103, 0, 'ff')
    for pid in ('P28', 'P29', 'P2'):
        p.dynamic(pid, 102, 0, 'f')
    for pid in ('P9', 'P10', 'P7'):
        p.dynamic(pid, 106, 0, 'p')
    p.dynamic('P31', 106, 0, 'mp')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S34: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
