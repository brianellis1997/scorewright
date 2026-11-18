"""The Dorico steps for 111326 S24 (lab/pieces/p111326_s24.py), after S23. The bassoon's F in bar 49
becomes an eighth (EventEdit.DurationShortenByGrid three times: it keeps its ID and the slur from bar
48 that ends on it); the old runs of the piccolo, the flute and Violin I are deleted; then each line is
typed, the runs with NoteInput.StartTupletRun (Definition 6:4 for the sextuplets, 3:2 for the
sixteenth triplets; Set=true starts the run, Set=false ends it), its sharps checked and its marks
added. The E-flat clarinet's tie from bar 48 comes last.
usage (whisperer env): python lab/pieces/p111326_s24_dorico.py <S23.xml> <S24.dorico.json>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
import p111326_s24 as s24  # noqa: E402

DELETES = [('P1', (49, 0), (52, 1)), ('P2', (49, 0), (52, Fraction(3, 4))),
           ('P28', (49, 0), (49, Fraction(3, 4))), ('P28', (51, 1), (52, Fraction(3, 4)))]


def run_events(pid, bars, skip_rest=True):
    out = []
    for bar in bars:
        for ev in s24.RUNS[pid][bar]:
            if ev[0] == 'r':
                if not skip_rest:
                    out.append((None, ev[1]))
            elif ev[0] == 'n':
                out.append((ev[1], ev[2], 'tie' if len(ev) > 3 and ev[3] in ('start', 'both') else None))
            else:
                ratio = f'{ev[1][0]}:{ev[1][1]}'
                if out and out[-1][0] == 'end tuplet' and out[-1][1] == ratio:
                    out.pop()
                else:
                    out.append(('tuplet', ratio))
                out += [(n, Fraction(1, 4)) for n in ev[2]]
                out.append(('end tuplet', ratio))
    return out


def sharps(score, pid, bars, after=None, until=None):
    """[(bar, onset, k)]: typed notes spelled with a sharp, k repeated ones counted as one group"""
    seq = []
    for bar in bars:
        for it in score.items(pid, bar):
            if it[1] == 'Rest' or it[2] or (after and (bar, it[0]) < after) or (until and (bar, it[0]) >= until):
                continue
            seq.append((bar, it[0], it[1][0]))
    out = []
    for b, o, n in seq:
        if '#' in n[1:]:
            if out and out[-1][3] == n and out[-1][4]:
                out[-1][2] += 1
            else:
                out.append([b, o, 1, n, True])
        elif out:
            out[-1][4] = False
    return [(b, o, k) for b, o, k, n, _ in out]


def plan(x):
    p = Plan(x)
    p.step('Bassoon: bar 49 F to an eighth', 'P7', 49, 0, edits=['EventEdit.DurationShortenByGrid'] * 3)
    for pid, a, z in DELETES:
        p.step(f'{p.who(pid)}: the old run in bars {a[0]}-{z[0]} out', pid, *a, to=z, edits=['Edit.Delete'])
    final = s24.notes(x)
    want = Score(final)
    state = [s24.cleared(x)]
    p.use(state[0])

    def line(pid, start, events, bars, after=None, until=None, untie=False):
        """type a line; after and until (bar, onset) bound the typed notes where kept notes share the bars;
        untie: the tie from the bar before comes in a later step"""
        p.notes(pid, *start, events)
        state[0] = s24.copy_bars(state[0], final, pid, bars)
        if untie:
            s0, s1 = s24.measure_span(state[0], pid, bars[0])
            body = re.sub(r'<tie type="stop"/>|<tied type="stop"/>', '', state[0][s0:s1], count=2)
            state[0] = state[0][:s0] + body + state[0][s1:]
        typed = [(b, it[0]) for b in bars for it in want.items(pid, b) if it[1] != 'Rest'
                 and (not after or (b, it[0]) >= after) and (not until or (b, it[0]) < until)]
        p.after_notes(state[0], pid, *typed[-1])
        for b, o, k in reversed(sharps(want, pid, bars, after, until)):
            p.spell(pid, b, o, group=k)

    line('P1', (48, 1), run_events('P1', range(48, 53)), range(48, 53))
    p.dynamic('P1', 48, 1, 'f')
    line('P2', (49, 0), run_events('P2', range(49, 53)), range(49, 53), until=(52, 1))
    line('P28', (49, 0), run_events('P28', [49]), [49], until=(49, 1))
    line('P28', (51, 1), run_events('P28', [51, 52]), [51, 52], after=(51, 1), until=(52, 1))
    for pid in ('P1', 'P2', 'P28'):
        for a, z in s24.SLURS[pid]:
            p.slur(pid, a, z)
    oboe = [(n, Fraction(1, 2)) for b in (49, 50, 51) for n in s24.OBOE[b]] + [(n, Fraction(1, 2)) for n in s24.OBOE_52]
    line('P3', (49, 0), oboe, range(49, 53), until=(52, 1))
    p.dynamic('P3', 49, 0, 'f')
    line('P5', (49, 0), [('A5', 2)], [49], untie=True)
    clar = [(n, 2, 'tie' if t in ('start', 'both') else None) for n, t in s24.held(s24.CLARINET)]
    line('P6', (49, 0), clar, range(49, 53))
    p.dynamic('P6', 49, 0, 'f')
    p.slur('P6', *s24.SLURS['P6'][0])
    bsn = [('F3', Fraction(1, 2))] * 3 + [(n, Fraction(1, 2)) for n in s24.BASSOON[1:] for _ in range(4)]
    line('P7', (49, Fraction(1, 2)), bsn, range(49, 59), after=(49, Fraction(1, 2)))
    p.tie('P5', 48, 1)
    state[0] = s24.copy_bars(state[0], final, 'P5', [48, 49])
    p.use(state[0])
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S24: {bad[:5]}'
    p.save(sys.argv[2], requires=['S23'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
