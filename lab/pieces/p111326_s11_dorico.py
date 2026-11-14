"""The Dorico steps for 111326 S11 (lab/pieces/p111326_s11.py), on his project after S10.
The harp's two staves are typed one after the other, each followed by its spelling steps; then each
woodwind's last note, its slur and its diminuendo from the old note (which has an ID), and the B flat
clarinet's tie last.
usage (whisperer env): python lab/pieces/p111326_s11_dorico.py <working.xml> <S11.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s5 import write_bar  # noqa: E402
from p111326_s6 import harp_bar  # noqa: E402
import p111326_s11 as s11  # noqa: E402


def plan(x):
    p = Plan(x)
    bars = sorted(s11.HARP)
    rh = [(None, 1)] * 0
    for b in bars:
        rh += [(None, 1)] + [(n, 0.25) for n in s11.HARP[b][1]]
    lh = []
    for b in bars:
        lh += [(n, 0.25) for n in s11.HARP[b][0]] + ([(None, 1)] if b != bars[-1] else [])
    p.notes('P26', bars[0], 0, rh, staff=1)
    y = x
    for b in bars:
        y = harp_bar(y, 'P26', b, (), s11.HARP[b][1])
    p.after_notes(y, 'P26', bars[-1], 1.75, staff=1)
    for b in reversed(bars):
        for k in (3, 2, 1, 0):
            if '#' in s11.HARP[b][1][k]:
                p.spell('P26', b, 1 + k / 4, staff=1)
    p.notes('P26', bars[0], 0, lh, staff=2)
    y = s11.harp(x)
    p.after_notes(y, 'P26', bars[-1], 0.75, staff=2)
    for b in reversed(bars):
        for k in (3, 2, 1, 0):
            if '#' in s11.HARP[b][0][k]:
                p.spell('P26', b, k / 4, staff=2)
    p.dynamic('P26', 33, 0, 'mp', staff=2)
    for pid, name in s11.ENDS.items():
        p.notes(pid, 33, 0, [(name, 2)])
        y = write_bar(y, pid, 33, [(name, 8, None)])
        p.after_notes(y, pid, 33, 0)
        if pid != 'P6':
            p.slur(pid, (32, 0), (33, 0))
        p.hairpin(pid, (32, 0), (33, 0), up=False)
    p.tie('P6', 32, 0)
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s11.notes(x, tied=False))
    got = p.cur
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != got.items(pid, b, st)]
    assert not bad, f'the steps do not end at S11: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
