"""The Dorico steps for 111326 S12 (lab/pieces/p111326_s12.py), on his project after S11.
Each line is typed, its sharps get spelling steps, then its marks; hairpins come last in a line,
because after a hairpin on new notes the next step starts again from a note with an ID. The three
notes held over from bar 40 are tied last.
usage (whisperer env): python lab/pieces/p111326_s12_dorico.py <working.xml> <S12.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s6 import harp_bar  # noqa: E402
from p111326_s10_dorico import black_keys, last_note, typed  # noqa: E402
import p111326_s12 as s12  # noqa: E402


def plan(x):
    p = Plan(x)
    state = [x]

    def line(l, after=None, start=None):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff, **({'start': start} if start else {}))
        state[0] = after(state[0]) if after else s12.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o in reversed(black_keys(l)):
            p.spell(pid, b, o, staff=staff)

    for l in s12.lines():
        pid = l[0]
        line(l)
        if pid in s12.MELODY:
            p.dynamic(pid, *((40, 1.0) if pid in ('P2', 'P3') else (41, 0)), 'mf')
            for a, z in s12.SLURS[0 if pid in ('P2', 'P3') else 1:]:
                p.slur(pid, a, z)
            for b, o in s12.PORTATO:
                p.articulation(pid, b, o, 'kStaccatoTenuto')
            for a, z, up in s12.HAIRPINS:
                p.hairpin(pid, a, z, up=up)
            continue
        if pid == 'P32':
            p.technique(pid, 41, 0, 'arco')
        p.dynamic(pid, 41, 0, 'mp' if pid in ('P14', 'P15') else 'mf')
        if pid not in ('P14', 'P15', 'P32'):
            for a, z in s12.pad_slurs(l):
                p.slur(pid, a, z)

    bars = sorted(s12.HARP)
    rh = {b: [(None, 4, None)] + [(n, 1, None) for n in s12.HARP[b][1]] for b in bars}
    lh = {b: [(n, 1, None) for n in s12.HARP[b][0]] + ([(None, 4, None)] if b != bars[-1] else []) for b in bars}

    before = state[0]

    def harp_rh(y):
        for b in bars:
            y = harp_bar(y, 'P26', b, (), s12.HARP[b][1])
        return y
    line(('P26', 1, bars[0], 0, rh), after=harp_rh)
    line(('P26', 2, bars[0], 0, lh), after=lambda y: s12.harp(before))
    for pid, b0, b1 in s12.HOLDS:
        p.tie(pid, 37 if pid == 'P9' else b0, 0)
    return p, state[0]


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(s12.notes(x, tied=False))
    got = p.cur
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != got.items(pid, b, st)]
    assert not bad, f'the steps do not end at S12: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
