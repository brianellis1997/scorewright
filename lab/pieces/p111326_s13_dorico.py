"""The Dorico steps for 111326 S13 (lab/pieces/p111326_s13.py), on his project after S12.
Each line is typed, its sharps get spelling steps, then its dynamic, slurs and (last) its hairpin;
then the harp's two staves.
usage (whisperer env): python lab/pieces/p111326_s13_dorico.py <working.xml> <S13.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s6 import harp_bar  # noqa: E402
from p111326_s10_dorico import black_keys, last_note, typed  # noqa: E402
import p111326_s13 as s13  # noqa: E402


def plan(x):
    p = Plan(x)
    state = [x]

    def line(l, after=None):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff)
        state[0] = after(state[0]) if after else s13.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o in reversed(black_keys(l)):
            p.spell(pid, b, o, staff=staff)

    for l in s13.lines():
        pid = l[0]
        line(l)
        p.dynamic(pid, 49, 1.0 if pid in s13.COUNTER_PARTS else 0, 'ff')
        if pid in s13.MELODY_PARTS:
            for a, z in s13.MELODY_SLURS:
                p.slur(pid, a, z)
            p.hairpin(pid, *s13.DIM, up=False)
        elif pid in s13.COUNTER_PARTS:
            for a, z in s13.COUNTER_SLURS:
                p.slur(pid, a, z)
        else:
            for a, z in s13.pad_slurs(l):
                p.slur(pid, a, z)

    bars = sorted(s13.HARP)
    rh = {b: [(None, 4, None)] + [(n, 1, None) for n in s13.HARP[b][1]] for b in bars}
    lh = {b: [(n, 1, None) for n in s13.HARP[b][0]] + ([(None, 4, None)] if b != bars[-1] else []) for b in bars}
    before = state[0]

    def harp_rh(y):
        for b in bars:
            y = harp_bar(y, 'P26', b, (), s13.HARP[b][1])
        return y
    line(('P26', 1, bars[0], 0, rh), after=harp_rh)
    line(('P26', 2, bars[0], 0, lh), after=lambda y: s13.harp(before))
    p.dynamic('P26', 49, 0, 'f', staff=2)
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s13.notes(x))
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S13: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
