"""The Dorico steps for 111326 S14 (lab/pieces/p111326_s14.py), on his project after S12.
First the crescendos on the notes he already has in bars 46-48 (each selected by its ID), then each
new line: typed, its sharps checked, then its dynamics, slurs and (last) its hairpins; the harp's
chord at the end.
usage (whisperer env): python lab/pieces/p111326_s14_dorico.py <working.xml> <S14.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10_dorico import black_keys, last_note, typed  # noqa: E402
import p111326_s13 as s13  # noqa: E402
import p111326_s14 as s14  # noqa: E402


def plan(x):
    p = Plan(x)
    for pid, bar in s14.RAMP.items():
        p.hairpin(pid, (bar, 0), (bar, 0))
    state = [x]

    def line(l, after=None):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff)
        state[0] = after(state[0]) if after else s14.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o in reversed(black_keys(l)):
            p.spell(pid, b, o, staff=staff)

    for l in s14.lines():
        pid = l[0]
        line(l)
        if pid in ('P12', 'P13'):
            p.dynamic(pid, 47, 0, 'mp')
        p.dynamic(pid, 49, 1.0 if pid in s13.COUNTER_PARTS else 0, 'f' if pid in s14.BRASS else 'ff')
        if pid in s14.MELODY_PARTS or pid in s14.SECOND_PARTS or pid in ('P12', 'P13'):
            for a, z in (s14.TRUMPET_SLURS if pid in ('P12', 'P13') else s14.MELODY_SLURS):
                p.slur(pid, a, z)
            if pid in ('P12', 'P13'):
                p.hairpin(pid, (47, 0), (48, 1.0))
            p.hairpin(pid, *s13.DIM, up=False)
        elif pid in s13.COUNTER_PARTS:
            for a, z in s13.COUNTER_SLURS:
                p.slur(pid, a, z)
        else:
            for a, z in s13.pad_slurs(l):
                p.slur(pid, a, z)
    lh, rh = s14.HARP_CHORD
    line(('P26', 1, 49, 0, {49: [(list(rh), 8, None)]}), after=lambda y: y)
    line(('P26', 2, 49, 0, {49: [(list(lh), 8, None)]}), after=s14.harp)
    p.dynamic('P26', 49, 0, 'f', staff=2)
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s14.notes(x))
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S14: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
