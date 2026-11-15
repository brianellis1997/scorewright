"""The Dorico steps for 111326 S18 (lab/pieces/p111326_s18.py), on his project as exported at 17:00.
First the crescendos on bars 46-48, the harp's G sharp to G in bar 48, his viola chord in bar 49
without its F, his D flat in bar 56 respelled; then each new line, typed, its sharps checked, and
its marks; his own trumpet and Violin I get their dynamics and slurs; the harp's chord last.
usage (whisperer env): python lab/pieces/p111326_s18_dorico.py <working.xml> <S18.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10_dorico import last_note, typed  # noqa: E402
from p111326_s15_dorico import sharp_groups  # noqa: E402
import p111326_s14 as s14  # noqa: E402
import p111326_s18 as s18  # noqa: E402


def plan(x):
    p = Plan(x)
    for pid, bar in s14.RAMP.items():
        p.hairpin(pid, (bar, 0), (bar, 0))
    p.pitch('P26', 48, 1.5, -1, chromatic=True)
    state = [s18.harp_48(x)]
    p.use(state[0])

    def line(l, after=None):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff)
        state[0] = after(state[0]) if after else s18.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o, k in reversed(sharp_groups(l)):
            p.spell(pid, b, o, staff=staff, group=k)

    line(('P30', 1, 49, 0, {49: [(list(reversed(s18.VIOLA_49)), 8, None)]}), after=s18.viola_49)
    state[0] = s18.respell_56(state[0])
    p.use(state[0])
    p.spell('P28', 56, 0)
    for l in s18.lines():
        pid = l[0]
        line(l)
        if pid in ('P13',):
            p.dynamic(pid, 48, 1.0, 'f')
            for a, z in s18.BRASS_SLURS:
                p.slur(pid, a, z)
        if pid in ('P9', 'P10'):
            p.dynamic(pid, 49, 0, 'f')
            p.slur(pid, *s18.BRASS_SLURS[1])
        if pid in ('P2', 'P1'):
            p.dynamic(pid, 49, 0, 'f')
            for a, z in s18.RUN_SLURS:
                p.slur(pid, a, z)
        if pid in ('P29', 'P2', 'P3'):
            p.dynamic(pid, 52, 1.0, 'ff' if pid == 'P29' else 'f')
            for a, z in s18.MELODY_SLURS:
                p.slur(pid, a, z)
        if pid in ('P28', 'P29'):
            p.dynamic(pid, 49, 0, 'mf')
        if pid in ('P11', 'P7', 'P31', 'P32', 'P14', 'P15', 'P16', 'P17'):
            p.dynamic(pid, 49, 0, 'f')
        if pid in s18.PAD_PARTS + ('P7', 'P31', 'P32', 'P14', 'P15', 'P16', 'P17'):
            p.dynamic(pid, 53, 0, 'mf')
        if pid == 'P7':
            p.slur(pid, (48, 1.0), (49, 0))
        if pid in s18.PAD_PARTS:
            for a, z in ((53, 56), (57, 60)):
                starts = [b for b in range(a, z + 1) for n, d, t in l[4].get(b, [])[:1] if n and t not in ('stop', 'both')]
                if len(starts) > 1:
                    p.slur(pid, (starts[0], 0), (starts[-1], 0))
        if pid in s18.ACCENTS:
            p.articulate(pid, (49, 0), (60, 1.0))
        if pid == 'P17':
            p.dynamic(pid, 47, 0, 'p')
            p.hairpin(pid, (47, 0), (48, 1.75))
    p.dynamic('P12', 48, 1.0, 'f')
    for a, z in s18.BRASS_SLURS:
        p.slur('P12', a, z)
    p.dynamic('P28', 52, 1.0, 'ff')
    for a, z in s18.MELODY_SLURS:
        p.slur('P28', a, z)
    p.dynamic('P30', 49, 0, 'mf')
    p.dynamic('P30', 53, 0, 'mf')
    lh, rh = s18.HARP_CHORD
    line(('P26', 1, 49, 0, {49: [(list(rh), 8, None)]}), after=lambda y: y)
    line(('P26', 2, 49, 0, {49: [(list(lh), 8, None)]}), after=s14.harp)
    p.dynamic('P26', 49, 0, 'f', staff=2)
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s18.notes(x))
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S18: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
