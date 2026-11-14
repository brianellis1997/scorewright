"""The Dorico steps for 111326 S6 (lab/pieces/p111326_s6.py), made with the suggestion so that
Brian's Accept puts it into his open project at once (app/dorico_apply.py, app/DORICO.md).

Order, because a tie merges two notes into one event and the merged note loses its ID:
1. the clarinet chords spread over Eb clarinet, Bb clarinet and bassoon, the E sharp respelled F,
   the clarinets' dynamics and slurs;
2. the new lines typed from the caret (oboe, cor anglais, Violin I, the pizzicato parts, the harp);
3. the marks on the new notes and the flute's slurs;
4. every tie between existing notes, right to left on each staff.
The plan walks over the score as it is at each point: x0 (the export), x1 (after the paste),
x2 (after the respell), x3 (after the new lines, before the ties between existing notes).
usage (whisperer env): python lab/pieces/p111326_s6_dorico.py <dorico_export.xml> <S6.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan  # noqa: E402
from p111326_s2 import spread  # noqa: E402
from p111326_s5 import OBOE, TIES, VIOLIN_I, respell, voice_one, write_bar  # noqa: E402
from p111326_s6 import COR, HARP, PIZZ, harp_bar  # noqa: E402

HALF_REST = '<note><rest/><duration>8</duration><voice>1</voice><type>half</type><staff>1</staff></note>'


def x1_of(x0):
    return spread(x0, 'P5', ('P6', 'P7'), range(24, 32))


def x2_of(x0):
    return spread(respell(x0, 'P5', 25, ('C', 2, 4), ('D', 0, 4)), 'P5', ('P6', 'P7'), range(24, 32))


def oboe_events():
    ev = dict(OBOE)
    ev[18] = [('G4', 4, None), ('A4', 4, None)]
    return ev


def x3_of(x2):
    x = x2
    for bar, events in oboe_events().items():
        x = write_bar(x, 'P3', bar, events)
    first, last = voice_one(x, 'P28', 24)[0], voice_one(x, 'P28', 24)[-1]
    x = x[:first[1]] + HALF_REST + x[last[2]:]
    for bar, events in VIOLIN_I.items():
        x = write_bar(x, 'P28', bar, events)
    for bar, (vc, vla, v2a, v2b) in PIZZ.items():
        x = write_bar(x, 'P31', bar, [(vc, 2, None), (None, 2, None), (None, 4, None)])
        if vla:
            x = write_bar(x, 'P30', bar, [(None, 2, None), (vla, 2, None), (None, 4, None)])
            x = write_bar(x, 'P29', bar, [(None, 4, None), (v2a, 2, None), (v2b, 2, None)])
    for bar, events in COR.items():
        x = write_bar(x, 'P4', bar, events)
    for bar, (lh, rh) in HARP.items():
        x = harp_bar(x, 'P26', bar, lh, rh)
    return x


def typed(bars):
    """bar-wise events (concert name, divisions, tie kind) -> note entry events (name, quarters, 'tie')"""
    out = []
    for bar in sorted(bars):
        for name, div, tie in bars[bar]:
            out.append((name, div / 4, 'tie' if tie in ('start', 'both') else None))
    return out


def plan(x0):
    x1, x2 = x1_of(x0), x2_of(x0)
    x3 = x3_of(x2)
    p = Plan(x0)
    p.explode('P5', 24, 31, staves=3)
    p.use(x1)
    p.respell('P6', 25, 0)
    p.use(x2)
    for pid in ('P5', 'P6', 'P7'):
        p.dynamic(pid, 24, 0, 'p')
    p.slur('P5', (24, 0), (27, 0), staves=3)
    p.slur('P5', (28, 0), (31, 0), staves=3)
    p.notes('P3', 18, 0, typed(oboe_events()))
    p.notes('P4', 24, 0, typed(COR))
    p.notes('P28', 24, 0, typed(VIOLIN_I))
    p.notes('P29', 25, 0, typed({b: [(None, 4, None), (v2a, 2, None), (v2b, 2, None)] for b, (vc, vla, v2a, v2b) in PIZZ.items() if vla}))
    p.notes('P30', 25, 0, typed({b: [(None, 2, None), (vla, 2, None), (None, 4, None)] for b, (vc, vla, v2a, v2b) in PIZZ.items() if vla}))
    p.notes('P31', 24, 0, typed({b: [(vc, 2, None), (None, 2, None), (None, 4, None)] for b, (vc, vla, v2a, v2b) in PIZZ.items()}))
    p.notes('P26', 28, 0, typed({b: [(None, 4, None)] + [(n, 1, None) for n in rh] for b, (lh, rh) in HARP.items()}), staff=1)
    p.notes('P26', 28, 0, typed({b: [(n, 1, None) for n in lh] + [(None, 4, None)] for b, (lh, rh) in HARP.items()}), staff=2)
    p.use(x3)
    p.slur('P3', (18, 1.0), (20, 0))
    p.slur('P3', (21, 0), (24, 0))
    p.hairpin('P3', (22, 1.0), (24, 0), up=False)
    p.dynamic('P3', 24, 0, 'pp')
    p.dynamic('P4', 24, 1.0, 'p')
    p.slur('P4', (24, 1.0), (26, 1.5))
    p.slur('P4', (28, 0), (31, 0))
    p.dynamic('P28', 24, 0, 'p')
    p.slur('P28', (25, 1.0), (26, 0))
    p.slur('P28', (27, 1.0), (30, 0))
    p.slur('P2', (25, 1.0), (26, 0))
    p.slur('P2', (27, 1.0), (30, 0))
    p.technique('P31', 24, 0)
    p.dynamic('P31', 24, 0, 'p')
    p.technique('P30', 25, 0.5)
    p.dynamic('P30', 25, 0.5, 'p')
    p.technique('P29', 25, 1.0)
    p.dynamic('P29', 25, 1.0, 'p')
    p.dynamic('P26', 28, 1.0, 'p', staff=1)
    for pid, pairs in TIES.items():
        for b0, b1 in sorted(pairs, reverse=True):
            p.tie(pid, b0, 0)
    return p


if __name__ == '__main__':
    p = plan(open(sys.argv[1], encoding='utf-8').read())
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
