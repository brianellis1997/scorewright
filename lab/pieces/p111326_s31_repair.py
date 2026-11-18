"""Repair after the S30/S31 runs of Nov 17 (lab/app/DORICO.md): the violas of bars 79-85 kept his old
double stops under the new eighth rests and came in shifted; the timpani skipped its empty bar 88 and
came in a bar early. Both regions are deleted and typed again, then the timpani's ff.
usage (whisperer env): python lab/pieces/p111326_s31_repair.py <export.xml> <S31.xml> <repair.dorico.json>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import events  # noqa: E402
import p111326_s5  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))


def plan(x, want_xml):
    want = Score(want_xml)
    p = Plan(x)
    last = [it[0] for it in p.cur.nav('P30', 85)][-1]
    p.step('Viola: bars 79-85 out', 'P30', 79, 0, to=(85, last), edits=['Edit.Delete'])
    p.step('Timpani: the notes of bars 88-90 out', 'P17', 88, 1, to=(90, 1), edits=['Edit.Delete'])
    state = x
    for b in range(79, 86):
        state = put(state, 'P30', b, [(None, 8, None)])
    for b in range(88, 91):
        state = put(state, 'P17', b, [(None, 8, None)])
    p.use(state)
    viola = {b: [(None, 2, None)] + [(it[1][0], 1, None) for it in want.items('P30', b) if it[1] != 'Rest'] for b in range(79, 86)}
    p.notes('P30', 79, 0, events(viola, (79, 0)))
    state = copy_bars(state, want_xml, 'P30', range(79, 86))
    p.after_notes(state, 'P30', 85, Fraction(7, 4))
    timp = {89: [(None, 4, None), ('E2', 4, None)], 91: [('D3', 4, None), (None, 4, None)], 93: [(None, 4, None), ('E2', 4, None)]}
    p.notes('P17', 89, 1, events(timp, (89, 1)))
    state = copy_bars(state, want_xml, 'P17', range(88, 94))
    p.after_notes(state, 'P17', 93, 1)
    p.dynamic('P17', 91, 0, 'ff')
    return p


if __name__ == '__main__':
    x, want_xml = (open(f, encoding='utf-8').read() for f in sys.argv[1:3])
    p = plan(x, want_xml)
    p.save(sys.argv[3])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[3])
