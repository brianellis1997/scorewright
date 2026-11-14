"""The Dorico steps for 111326 S10 (lab/pieces/p111326_s10.py), on his project as exported at 09:14.
Each line is typed over what is there (the old introduction, Violin II's last pizzicato pair, the
horn chord sketch), then every sharp in it gets a spelling step (MIDI input picks G sharp or A flat
by itself; the runner respells only a wrong one), then its marks, each from the line's own notes.
The clarinet's two changed notes move up by scale steps, so they keep the slur and the dynamic.
Violin I is his: only the dynamics and hairpins go on it.
usage (whisperer env): python lab/pieces/p111326_s10_dorico.py <working.xml> <S10.dorico.json>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
import p111326_s10 as s10  # noqa: E402


def typed(line):
    pid, staff, bar, onset, bars = line
    out = []
    for b in sorted(bars):
        for name, div, tie in bars[b]:
            out.append((name, div / 4, 'tie' if tie in ('start', 'both') else None))
    return out


def black_keys(line):
    """(bar, onset) of every note in the line spelled with a sharp or flat, chain starts only"""
    pid, staff, bar, onset, bars = line
    out = []
    for b in sorted(bars):
        t = onset if b == bar else 0
        for name, div, tie in bars[b]:
            if isinstance(name, str) and re.search(r'[#b]', name[1:]) and tie not in ('stop', 'both'):
                out.append((b, t))
            t += div / 4
    return out


def last_note(line):
    pid, staff, bar, onset, bars = line
    out = None
    for b in sorted(bars):
        t = onset if b == bar else 0
        for name, div, tie in bars[b]:
            if name and tie not in ('stop', 'both'):
                out = (b, t)
            t += div / 4
    return out


def plan(x):
    p = Plan(x)
    ls = {(l[0], l[2]): l for l in s10.lines(x)}
    state = [x]

    def line(key, after, **kw):
        l = ls[key]
        pid, staff, bar, onset, _ = l
        p.notes(pid, bar, onset, typed(l), staff=staff, **kw)
        state[0] = after(state[0])
        p.after_notes(state[0], pid, *last_note(l), staff=staff)
        for b, o in reversed(black_keys(l)):
            p.spell(pid, b, o, staff=staff)

    for key in (('P31', 1), ('P32', 1)):
        line(key, lambda y, k=key: s10.write_line(y, ls[k]))

    rh = {b: ([(None, 4, None)] + [(n, 1, None) for n in s10.HARP[b][1]]) if b in s10.HARP else [(None, 8, None)] for b in range(1, 6)}
    lh = {b: ([(n, 1, None) for n in s10.HARP[b][0]] + ([(None, 4, None)] if b < 5 else [])) if b in s10.HARP else [(None, 8, None)] for b in range(1, 6)}
    ls[('P26', 1)] = ('P26', 1, 1, 0, rh)
    ls[('P26', 2)] = ('P26', 2, 1, 0, lh)
    line(('P26', 1), lambda y: s10.harp(y, right=True, left=False))
    line(('P26', 2), lambda y: s10.harp(s10.harp(y, right=False, left=False), right=True, left=True), start=('P26', 2, 1, 0))

    for bar, (old, new, steps) in s10.CLARINET.items():
        p.pitch('P6', bar, 0, steps)
    state[0] = s10.clarinet(state[0])
    p.use(state[0])

    line(('P29', 32), lambda y: s10.write_line(y, ls[('P29', 32)]))
    p.technique('P29', 32, 1.0, 'arco')
    p.dynamic('P29', 32, 1.0, 'mf')
    for a, z in s10.VIOLIN_SLURS:
        p.slur('P29', a, z)
    p.hairpin('P29', (33, 0), (36, 0.5))
    p.dynamic('P29', 36, 1.0, 'f')
    p.hairpin('P29', (37, 0), (40, 1.5), up=False)

    p.dynamic('P28', 32, 1.0, 'mf')
    p.hairpin('P28', (33, 0), (36, 0.5))
    p.dynamic('P28', 36, 1.0, 'f')
    p.hairpin('P28', (37, 0), (40, 1.5), up=False)

    for pid in ('P9', 'P10', 'P11', 'P30', 'P31', 'P7', 'P32', 'P14', 'P15'):
        line((pid, 33), lambda y, k=(pid, 33): s10.write_line(y, ls[k]))
        if pid in ('P30', 'P31'):
            p.technique(pid, 33, 0, 'arco')
        if pid == 'P32':
            p.technique(pid, 33, 0, 'pizz.')
        p.dynamic(pid, 33, 0, 'mf' if pid == 'P32' else 'mp')
        for a, z in s10.PAD_SLURS.get(pid, []):
            p.slur(pid, (a, 0), (z, 0))
    return p, state[0]


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want, got = Score(s10.notes(x)), Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != got.items(pid, b, st)]
    assert not bad, f'the steps do not end at S10: {bad[:5]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
