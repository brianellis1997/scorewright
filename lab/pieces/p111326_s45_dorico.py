"""The Dorico steps for 111326 S45 (lab/pieces/p111326_s45.py): the steps of S44 with Violin II typed from bar 128
through its held notes into his run of bars 133-134 (all notes, so the caret needs no sixteenth moves), its
bowing slurs among the slurs, and its mp after S44's dynamics.
usage (whisperer env): python lab/pieces/p111326_s45_dorico.py <export.xml> <S45.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Score  # noqa: E402
import p111326_s44_dorico as s44d  # noqa: E402
import p111326_s45 as s45  # noqa: E402


def plan(x):
    with s45.patched():
        p, final = s44d.plan(x)
    p.dynamic('P29', 133, 0, 'mp')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S45: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
