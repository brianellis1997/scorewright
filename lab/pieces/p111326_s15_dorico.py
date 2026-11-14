"""The Dorico steps for 111326 S15 (lab/pieces/p111326_s15.py), on his project after S12.
First the crescendos on the notes he already has in bars 46-48 (by ID). Then each new line: typed,
its sharps checked (a run of repeated sharps as one group), then its dynamics, slurs, accents and,
last, its hairpins. The harp's chord at the end.
usage (whisperer env): python lab/pieces/p111326_s15_dorico.py <working.xml> <S15.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10_dorico import last_note, typed  # noqa: E402
import p111326_s14 as s14  # noqa: E402
import p111326_s15 as s15  # noqa: E402


def sharp_groups(line):
    """[(bar, onset, k)]: each run of k repeated notes spelled with a sharp or flat, in typing order"""
    pid, staff, bar, onset, bars = line
    seq = []
    for b in sorted(bars):
        t = onset if b == bar else 0
        for name, div, tie in bars[b]:
            if name is None:
                seq.append(None)
            elif tie not in ('stop', 'both'):
                seq.append((b, t, name))
            t += div / 4
    out = []
    for item in seq:
        if item and isinstance(item[2], str) and ('#' in item[2][1:] or 'b' in item[2][1:]):
            if out and out[-1][3] == item[2] and out[-1][4]:
                out[-1][2] += 1
            else:
                out.append([item[0], item[1], 1, item[2], True])
        elif out:
            out[-1][4] = False
    return [(b, t, k) for b, t, k, _, _ in out]


def plan(x):
    p = Plan(x)
    for pid, bar in s14.RAMP.items():
        p.hairpin(pid, (bar, 0), (bar, 0))
    state = [x]

    def line(l, after=None):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff)
        state[0] = after(state[0]) if after else s15.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o, k in reversed(sharp_groups(l)):
            p.spell(pid, b, o, staff=staff, group=k)

    for l in s15.lines():
        pid = l[0]
        line(l)
        if pid in ('P12', 'P13'):
            p.dynamic(pid, 47, 0, 'mp')
        if pid == 'P17':
            p.dynamic(pid, 47, 0, 'p')
        p.dynamic(pid, 49, 0, 'f' if pid in s15.BRASS + ('P17',) else 'ff')
        if pid in s15.MELODY_PARTS:
            if pid in ('P12', 'P13', 'P28', 'P29'):
                p.slur(pid, (48, 1.0), (49, 0))
            for a, z in s15.MELODY_SLURS:
                p.slur(pid, a, z)
        elif pid in s15.RUN_PARTS:
            for a, z in ([((48, 1.0), (50, 1.75))] + s15.RUN_SLURS[1:] if pid == 'P2' else s15.RUN_SLURS):
                p.slur(pid, a, z)
        elif pid in s15.PAD:
            for a, z in s14.s13.pad_slurs(l):
                p.slur(pid, a, z)
        if pid in s15.ACCENTS:
            p.articulate(pid, (49, 0), (56, 0))
        if pid in ('P12', 'P13'):
            p.hairpin(pid, (47, 0), (48, 1.0))
        if pid == 'P17':
            p.hairpin(pid, (47, 0), (48, 1.75))
        if pid in s15.MELODY_PARTS or pid in s15.RUN_PARTS:
            p.hairpin(pid, *s15.DIM, up=False)
    lh, rh = s14.HARP_CHORD
    line(('P26', 1, 49, 0, {49: [(list(rh), 8, None)]}), after=lambda y: y)
    line(('P26', 2, 49, 0, {49: [(list(lh), 8, None)]}), after=s14.harp)
    p.dynamic('P26', 49, 0, 'f', staff=2)
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s15.notes(x))
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S15: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
