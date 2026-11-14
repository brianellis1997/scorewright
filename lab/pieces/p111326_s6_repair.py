"""The repair after the first S6 run in Dorico (Nov 13 2026, 22:11). Steps 1-25 went in, with three
typing errors of the planner: the harp's sixteenths came in as whole notes (kSemiquaver is not a
Dorico name; kSemiQuaver is), Violin I bars 29-31 came in a quarter too long (SetDotted Set=false
toggled the dot back on), and MIDI 68 came in as A flat where the plan has G sharp. This plan clears
and retypes those notes, and respells the A flats, on the score as Dorico has it (an export after
the stop); then S6 goes on from step 26.
usage (whisperer env): python lab/pieces/p111326_s6_repair.py <dorico_export_2019.xml> <export_after_stop.xml> <repair.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan  # noqa: E402
from p111326_s6 import HARP  # noqa: E402


def last_note_bar(p, pid, staff, start):
    last = start
    for b in sorted(x for x in p.cur.parts[pid][0] if x >= start):
        its = [it for it in p.cur.nav(pid, b, staff) if it[1] != 'Rest']
        if its:
            last = p.cur.chain_end(pid, b, its[-1][0], staff)
    return last


def plan(x0, now):
    p = Plan(x0)
    p.use(now)
    p.step('clear Violin I bars 29-32', 'P28', 29, 0, to=(30, 1.0), edits=['Edit.Delete'])
    p.notes('P28', 29, 0, [('C5', 2), ('B4', 2, 'tie'), ('B4', 1)])
    end = max(last_note_bar(p, 'P26', 1, 28), last_note_bar(p, 'P26', 2, 28))
    while not p.cur.nav('P26', end, 1):
        end += 1
    p.step(f'clear the harp, bars 28-{end}', 'P26', 28, 1.0, staff=1, to=(end, None), down=1, edits=['Edit.Delete'])
    rh = [ev for b in sorted(HARP) for ev in [(None, 1)] + [(n, 0.25) for n in HARP[b][1]]]
    lh = [ev for b in sorted(HARP) for ev in [(n, 0.25) for n in HARP[b][0]] + [(None, 1)]]
    p.notes('P26', 28, 0, rh, staff=1)
    p.notes('P26', 28, 0, lh, staff=2)
    p.respell('P4', 31, 0, up=False)
    p.respell('P30', 27, 0.5, up=False)
    p.respell('P30', 31, 0.5, up=False)
    return p


if __name__ == '__main__':
    p = plan(open(sys.argv[1], encoding='utf-8').read(), open(sys.argv[2], encoding='utf-8').read())
    p.save(sys.argv[3])
    print(f'{len(p.steps)} steps ->', sys.argv[3])
