"""The Dorico steps for 111326 S8 (lab/pieces/p111326_s8.py), on the score after S7.
The introduction has no notes with IDs before it, so each caret starts at a note in bar 9 (or the
nearest staff with one) and moves left and down. Each new line is typed, then its marks follow from
the last typed note, which Dorico leaves selected; after each mark the runner steps back to the note
(restore). Ties are typed with the notes.
usage (whisperer env): python lab/pieces/p111326_s8_dorico.py <S7.xml> <S8.dorico.json>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from dorico_plan import Plan  # noqa: E402
from p111326_s8 import BASSOON_24, CELLO_24, CLARINET, HARP, HORN, PEDAL, TIE_PEDAL, WARM, notes  # noqa: E402


def typed(bars):
    out = []
    for bar in sorted(bars):
        for name, div, tie in bars[bar]:
            out.append((name, div / 4, 'tie' if tie in ('start', 'both') else None))
    return out


def plan(x7):
    x8 = notes(x7)
    pedal = lambda octave: {b: [(PEDAL[b] + octave, 8, TIE_PEDAL[b])] for b in PEDAL}
    cello = {**pedal('3'), **{b: [(None, 8, None)] for b in range(9, 17)}, **WARM, 24: CELLO_24}
    harp_rh = {b: ([(None, 4, None)] + [(n, 1, None) for n in HARP[b][1]]) if b in HARP else [(None, 8, None)] for b in range(1, 8)}
    harp_lh = {b: ([(n, 1, None) for n in HARP[b][0]] + [(None, 4, None)]) if b in HARP else [(None, 8, None)] for b in range(1, 8)}
    p = Plan(x7)
    p.notes('P31', 1, 0, typed(cello))
    p.after_notes(x8, 'P31', 23, 0)
    p.dynamic('P31', 1, 0, 'pp')
    p.dynamic('P31', 17, 0, 'pp')
    p.slur('P31', (17, 0), (19, 0))
    p.slur('P31', (21, 0), (23, 0))
    p.notes('P32', 1, 0, typed(pedal('2')))
    p.after_notes(x8, 'P32', 5, 0)
    p.dynamic('P32', 1, 0, 'pp')
    p.notes('P26', 1, 0, typed(harp_rh), staff=1)
    p.notes('P26', 1, 0, typed(harp_lh), staff=2)
    p.after_notes(x8, 'P26', 7, 0.75, staff=2)
    p.dynamic('P26', 1, 0, 'p', staff=2)
    p.notes('P6', 2, 0, typed(CLARINET))
    p.after_notes(x8, 'P6', 4, 0)
    p.dynamic('P6', 2, 0, 'p')
    p.slur('P6', (2, 0), (4, 0))
    p.notes('P9', 6, 0, typed(HORN))
    p.after_notes(x8, 'P9', 7, 0)
    p.dynamic('P9', 6, 1.0, 'pp')
    p.slur('P9', (6, 1.0), (7, 0))
    p.articulation('P9', 7, 0, 'kStaccatoTenuto')
    p.notes('P7', 17, 0, typed({**WARM, 24: BASSOON_24}))
    p.after_notes(x8, 'P7', 23, 0)
    p.dynamic('P7', 17, 0, 'pp')
    p.slur('P7', (17, 0), (19, 0))
    p.slur('P7', (21, 0), (23, 0))
    return p


if __name__ == '__main__':
    p = plan(open(sys.argv[1], encoding='utf-8').read())
    p.save(sys.argv[2])
    print(f'{len(p.steps)} steps, {p.commands()} commands ->', sys.argv[2])
