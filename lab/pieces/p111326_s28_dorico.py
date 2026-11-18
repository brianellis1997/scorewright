"""The Dorico steps for 111326 S28 (lab/pieces/p111326_s28.py), on S27. The held C of the bassoon and
the held E of the violas end at bar 78 (EventEdit.DurationShortenByGrid); both violin lines of bars
78-86 and his viola double stops of bars 78-85 are deleted (a rest in note entry leaves an old note
in place: S30, Nov 17); then each line is typed (the bass turn in bar 77, the cellos' and violas' sixteenths
over his double stops, the two violin lines swapped, the clarinet, the flute, the horns, the
bassoon), its sharps and flats checked; then the slurs, and last the mf and the swells.
usage (whisperer env): python lab/pieces/p111326_s28_dorico.py <S27.xml> <S28.dorico.json>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s10 import put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
import p111326_s28 as s28  # noqa: E402


def events(bars, start):
    """typed events from (bar, onset) start: rests before it are skipped, ties kept; a bar the line
    leaves out is a bar of rest (S31, Nov 17: the timpani's empty bar 88 was skipped, and every later
    timpani note came in a bar early)"""
    out, b0, o0 = [], start[0], Fraction(start[1])
    for b in range(min(bars), max(bars) + 1):
        t = Fraction(0)
        for n, d, tie in bars.get(b, [(None, 8, None)]):
            q = Fraction(d, 4)
            if (b, t) >= (b0, o0):
                out.append((n, q, 'tie' if tie in ('start', 'both') else None))
            t += q
    while out and out[-1][0] is None:
        out.pop()
    return out


def accidentals(score, pid, bars, start):
    """[(bar, onset, k)]: typed notes with a sharp or a flat, k repeated ones as one group"""
    seq = []
    for b in sorted(bars):
        for it in score.items(pid, b):
            if it[1] == 'Rest' or it[2] or (b, it[0]) < start:
                continue
            seq.append((b, it[0], it[1][0]))
    out = []
    for b, o, n in seq:
        if '#' in n[1:] or 'b' in n[1:]:
            if out and out[-1][3] == n and out[-1][4]:
                out[-1][2] += 1
            else:
                out.append([b, o, 1, n, True])
        elif out:
            out[-1][4] = False
    return [(b, o, k) for b, o, k, n, _ in out]


def first_to_rest(x, pid, bar):
    """the note that starts a bar becomes a rest of its length (the end of a held note, cut off)"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    m = re.search(r'<note[ >].*?</note>', body, re.S)
    d = int(re.search(r'<duration>(\d+)</duration>', m.group(0)).group(1))
    typ = re.search(r'<type>(\w+)</type>', m.group(0)).group(1)
    rest = f'<note><rest/><duration>{d}</duration><voice>1</voice><type>{typ}</type><staff>1</staff></note>'
    return x[:s0] + body[:m.start()] + rest + body[m.end():] + x[s1:]


def plan(x):
    p = Plan(x)
    p.shorten('P7', 76, 0, 4)
    p.shorten('P30', 75, 0, 1)
    tune_end = [it[0] for it in p.cur.items('P28', 85) if it[1] != 'Rest'][-1]
    p.step('Violin I: the tune of bars 78-85 out', 'P28', 78, 0, to=(85, tune_end), edits=['Edit.Delete'])
    p.step('Violin II: the descant of bars 78-86 out', 'P29', 78, Fraction(3, 2), to=(86, 0), edits=['Edit.Delete'])
    viola_end = [it[0] for it in p.cur.items('P30', 85) if it[1] != 'Rest'][-1]
    p.step('Viola: his double stops of bars 78-85 out', 'P30', 78, Fraction(1, 2), to=(85, viola_end), edits=['Edit.Delete'])
    final = s28.notes(x)
    want = Score(final)
    state = s28.untie_77(s28.untie_77(x, 'P7'), 'P30')
    for b in range(78, 79):
        state = put(state, 'P7', b, [(None, 8, None)])
    state = first_to_rest(state, 'P30', 78)
    for b in range(78, 86):
        state = put(state, 'P30', b, [(None, 8, None)])
    for pid, bars in (('P28', range(78, 87)), ('P29', range(78, 87))):
        for b in bars:
            state = put(state, pid, b, [(None, 8, None)])
    p.use(state)
    ls = s28.lines(x)
    order = [('P32', (77, 0)), ('P31', (77, 0)), ('P30', (78, Fraction(1, 2))), ('P28', (78, Fraction(3, 2))),
             ('P29', (78, 0)), ('P6', (78, 0)), ('P2', (82, Fraction(3, 2))), ('P9', (78, 0)), ('P10', (78, 0)), ('P7', (78, 0))]
    for pid, start in order:
        bars = ls[pid]
        p.notes(pid, *start, events(bars, start))
        state = copy_bars(state, final, pid, sorted(bars))
        typed = [(b, it[0]) for b in sorted(bars) for it in want.items(pid, b) if it[1] != 'Rest' and not it[2] and (b, it[0]) >= start]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=k)
    for pid in ('P28', 'P29', 'P6', 'P2'):
        for a, z in s28.slurs(x, pid):
            p.slur(pid, a, z)
    for pid in s28.SWELLING:
        ws = s28.swells(want, pid)
        for a, z, up in ws:
            p.hairpin(pid, a, z, up=up)
        p.dynamic(pid, *ws[0][0], 'mf')
    for pid in ('P9', 'P10'):
        p.dynamic(pid, 78, 0, 'mp')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S28: {bad[:6]}'
    p.save(sys.argv[2], requires=['S27'])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
