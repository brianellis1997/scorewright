"""The Dorico steps for 111326 S30 (lab/pieces/p111326_s30.py): the steps of S28 with its swells and
the winds' phrase slurs.
usage (whisperer env): python lab/pieces/p111326_s30_dorico.py <S27.xml> <S30.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Score  # noqa: E402
import p111326_s28 as s28  # noqa: E402
import p111326_s28_dorico as s28d  # noqa: E402
import p111326_s30 as s30  # noqa: E402


def plan(x):
    s28.slurs, s28.swells = s30.slurs, s30.swells
    return s28d.plan(x)


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S30: {bad[:6]}'
    p.save(sys.argv[2], requires=['S27'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
