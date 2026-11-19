"""The Dorico steps for 111326 S33 (lab/pieces/p111326_s33.py), on his export after S32. The flute's
and oboe's held B of bar 96 are cut to a quarter (EventEdit.DurationShortenByGrid); his viola chords of
bars 97-105 are deleted (a rest in note entry leaves an old note in place); then every line is typed
(the bar 99 triplets with NoteInput.StartTupletRun 3:2), its sharps and flats checked; the harp staff by
staff; the four glissandi (NoteInput.CreateGlissando, two notes each); then the slurs, the trumpets'
portato quarters in the violins and the flute, the hairpins and the dynamics.
usage (whisperer env): python lab/pieces/p111326_s33_dorico.py <export.xml> <S33.dorico.json>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan, Score  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s10 import octave, put  # noqa: E402
from p111326_s24 import copy_bars  # noqa: E402
from p111326_s28_dorico import accidentals  # noqa: E402
import p111326_s33 as s33  # noqa: E402

H = Fraction(1, 2)
HELD = {'P2': 'B5', 'P3': 'B4'}
ORDER = ['P2', 'P3', 'P1', 'P6', 'P29', 'P28', 'P9', 'P10', 'P11', 'P14', 'P15', 'P16', 'P8', 'P32', 'P7', 'P30', 'P31', 'P17']
STARTS = {'P2': (96, 1), 'P3': (96, 1), 'P28': (102, 0), 'P30': (97, H), 'P31': (97, H)}


def line_events(bars, start, trip=None):
    """typed events from (bar, onset) start: rests before it skipped, ties kept, a bar the line leaves
    out is a bar of rest; a part that doubles the tune plays bar 99's triplet trip octaves away"""
    out, b0, o0 = [], start[0], Fraction(start[1])
    for b in range(min(bars), max(bars) + 1):
        if b == 99 and trip is not None:
            out += [('tuplet', '3:2')] + [(octave(n, trip), H) for n in s33.TRIPLET] + [('end tuplet', '3:2')]
            out += [(octave(n, trip), H) for n in s33.AFTER]
            continue
        t = Fraction(0)
        for n, d, tie in bars.get(b, [(None, 8, None)]):
            q = Fraction(d, 4)
            if (b, t) >= (b0, o0):
                out.append((n, q, 'tie' if tie in ('start', 'both') else None))
            t += q
    while out and out[-1][0] is None:
        out.pop()
    return out


def harp_events(staff):
    out = []
    for b in range(96, 106):
        if staff == 1:
            out += [(e[0], Fraction(e[1], 4)) for e in s33.GLISS.get(b, [(None, 8)])]
        elif b >= 97:
            out += [(s33.STRIKES[b], 1), (None, 1)] if b in s33.STRIKES else [(None, 2)]
    if staff == 1:
        out = out[1:]
    while out[-1][0] is None:
        out.pop()
    return out


def shortened(x, pid):
    """bar 96 as Dorico has it once the held note is cut to a quarter (its slur's end kept)"""
    s0, s1 = measure_span(x, pid, 96)
    body = x[s0:s1]
    (m,) = re.finditer(r'<note>(?:(?!</note>).)*<pitch>.*?</note>', body, re.S)
    old = m.group(0).replace('<duration>8</duration>', '<duration>4</duration>', 1).replace('<type>half</type>', '<type>quarter</type>', 1)
    rest = '<note><rest/><duration>4</duration><voice>1</voice><type>quarter</type><staff>1</staff></note>'
    return x[:s0] + body[:m.start()] + old + rest + body[m.end():] + x[s1:]


def plan(x):
    p = Plan(x)
    final = s33.notes(x)
    want = Score(final)
    state = x
    for pid in HELD:
        p.shorten(pid, 96, 0, 2)
        state = shortened(state, pid)
    last = [it[0] for it in p.cur.nav('P30', 105)][-1]
    p.step('Viola: his chords of bars 97-105 out', 'P30', 97, 0, to=(105, last), edits=['Edit.Delete'])
    for b in s33.BARS:
        state = put(state, 'P30', b, [(None, 8, None)])
    p.use(state)
    ls = s33.lines()
    for pid, name in s33.PICKUP.items():
        ls[pid][96] = [(HELD[pid], 4, None), (name, 4, None)]
    for pid in ORDER:
        bars = ls[pid]
        start = STARTS.get(pid, (97, 0))
        trip = s33.DOUBLE.get(pid)
        p.notes(pid, *start, line_events(bars, start, trip))
        state = copy_bars(state, final, pid, sorted(set(bars) | ({99} if trip is not None else set())))
        typed = [(b, it[0]) for b in range(start[0], max(bars) + 1) for it in want.items(pid, b)
                 if it[1] != 'Rest' and not it[2] and (b, it[0]) >= start]
        p.after_notes(state, pid, *typed[-1])
        for b, o, k in reversed(accidentals(want, pid, bars, start)):
            p.spell(pid, b, o, group=k)
    p.notes('P26', 96, 1, harp_events(1), staff=1)
    p.notes('P26', 97, 0, harp_events(2), staff=2)
    state = copy_bars(state, final, 'P26', range(96, 106))
    p.use(state)
    for a, z in (((104, 1), (105, 0)), ((104, 0), (104, 1)), ((101, 1), (102, 0)), ((96, 1), (97, 0))):
        p.gliss('P26', a, z)
    for pid, a, z in s33.slurs(want):
        p.slur(pid, a, z)
    for pid in ('P28', 'P29', 'P2'):
        for b in (103, 105):
            p.articulate(pid, (b, 0), (b, 1), 'kStaccatoTenuto')
    for pid in ('P12', 'P13'):
        p.hairpin(pid, (101, 1), (102, 3 * H))
    for pid in s33.FADING:
        f = s33.firsts(want, pid, 105)
        p.hairpin(pid, (105, f[0]), (105, f[-1]), up=False)
    p.dynamic('P16', 94, 0, 'ff')
    for pid in s33.ACCOMP:
        p.dynamic(pid, 97, s33.firsts(want, pid, 97)[0], 'f')
    for pid in ('P12', 'P13'):
        p.dynamic(pid, 101, 1, 'f')
        p.dynamic(pid, 103, 0, 'ff')
    for pid in ('P28', 'P29', 'P2'):
        p.dynamic(pid, 102, 0, 'f')
    return p, final


if __name__ == '__main__':
    x = open(sys.argv[1], encoding='utf-8').read()
    p, final = plan(x)
    want = Score(final)
    bad = [(pid, st, b) for pid, st in want.staves for b in want.parts[pid][0] if want.items(pid, b, st) != p.cur.items(pid, b, st)]
    assert not bad, f'the steps do not end at S33: {bad[:6]}'
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
