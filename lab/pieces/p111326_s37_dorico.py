"""The Dorico steps for 111326 S37 (lab/pieces/p111326_s37.py): the steps of S36 with the slurs of horn 1,
horn 2 and the bassoon from bar 105 into bar 106 among the other slurs (before any dynamic).
usage (whisperer env): python lab/pieces/p111326_s37_dorico.py <export.xml> <S37.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Score  # noqa: E402
import p111326_s36_dorico as s36d  # noqa: E402
import p111326_s37 as s37  # noqa: E402


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = s36d.plan(x, extra_slurs=s37.INTO_106)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S37: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
