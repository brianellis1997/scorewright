"""The Dorico steps for 111326 S17 (lab/pieces/p111326_s17.py), on his project after S16 (which it
requires: the Accept hook puts S16 in first and waits for Dorico's autosave).
First the fades on the held chords of the climax's last bar, then the echoes, the string chords,
the plucked basses and the harp, each with its sharps checked and its marks; Violin II's tie last.
usage (whisperer env): python lab/pieces/p111326_s17_dorico.py <S16.xml> <S17.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s10_dorico import last_note, typed  # noqa: E402
from p111326_s15_dorico import sharp_groups  # noqa: E402
import p111326_s17 as s17  # noqa: E402


def plan(x):
    p = Plan(x)
    for pid, bar in s17.FADES.items():
        p.hairpin(pid, (bar, 0), (bar, 0), up=False)
    state = [x]

    def line(l, after=None):
        pid, staff, bar, onset, bars = l
        p.notes(pid, bar, onset, typed(l), staff=staff)
        state[0] = after(state[0]) if after else s17.write_line(state[0], l)
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o, k in reversed(sharp_groups(l)):
            p.spell(pid, b, o, staff=staff, group=k)

    echoes = {e[0]: e for e in s17.ECHOES}
    for l in s17.lines():
        pid = l[0]
        line(l)
        if pid in echoes:
            _, bar, q, h, dyn = echoes[pid]
            p.dynamic(pid, bar, 1.0, dyn)
            p.slur(pid, (bar, 1.0), (bar + 1, 0))
        elif pid in s17.PADS:
            p.dynamic(pid, 57, 0, 'pp')
        elif pid == 'P32':
            p.technique(pid, 57, 0, 'pizz.')
            p.dynamic(pid, 57, 0, 'p')
    line(('P26', 1, 57, 0, {b: [(None, 4, None)] + [(n, 1, None) for n in s17.HARP[b - (b - 57) % 2][1]] for b in s17.BARS}),
         after=lambda y: s17.harp(y, right=True, left=False))
    line(('P26', 2, 57, 0, {b: [(n, 1, None) for n in s17.HARP[b - (b - 57) % 2][0]] + ([(None, 4, None)] if b != 64 else []) for b in s17.BARS}),
         after=lambda y: s17.notes(x, tied=False))
    p.dynamic('P26', 57, 0, 'p', staff=2)
    p.tie(*s17.HOLD[:2], 0)
    return p


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p = plan(x)
    want = Score(s17.notes(x, tied=False))
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S17: {bad[:5]}'
    p.save(sys.argv[2], requires=['S16'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
