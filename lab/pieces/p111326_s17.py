"""111326 S17 (Nov 14 2026), [CONTINUE] after S16: bars 57-64, the quieter phrase after the climax.
Brian at noon: "then we get into a quieter phrase, because this whole culmination is kind of a
single thing; we might want to move on to a new idea or texture once this calms down."
- The climax's G-to-E figure (a quarter on beat 2 falling a third to a held note) comes back as
  soft echoes, each lower and softer: flute G-E over A minor (p), oboe C-A over F (p), clarinet F-D
  over D minor (pp), horn 1 B-G sharp over E (pp).
- Harmony A minor, F, D minor, E, two bars each; it ends open on E, where a new idea can start.
- Texture: the strings hold the chords pp (Violin II keeps the E it ends the climax on, tied over
  the bar line), the double basses pluck each new chord, and the harp's run comes back, p, every bar.
- The held chords of the climax (cor anglais, B flat clarinet, Wagner tuba, bassoon) fade in their
  last bar, so the climax closes softly into it.
usage (whisperer env): python lab/pieces/p111326_s17.py <S16.xml> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s5 import tie, write_bar  # noqa: E402
from p111326_s6 import harp_bar  # noqa: E402
from p111326_s10 import held  # noqa: E402
from xml_marks import Marks  # noqa: E402

BARS = range(57, 65)
ECHOES = [('P2', 57, 'G5', 'E5', 'p'), ('P3', 59, 'C5', 'A4', 'p'), ('P6', 61, 'F4', 'D4', 'pp'), ('P9', 63, 'B3', 'G#3', 'pp')]
PADS = {'P29': ['E4', 'E4', 'F4', 'F4', 'F4', 'F4', 'E4', 'E4'], 'P30': ['C4', 'C4', 'C4', 'C4', 'D4', 'D4', 'B3', 'B3'],
        'P31': ['A2', 'A2', 'F2', 'F2', 'D2', 'D2', 'E2', 'E2']}
PLUCKS = {57: 'A2', 59: 'F2', 61: 'D2', 63: 'E2'}
HARP = {57: (('A2', 'E3', 'A3', 'C4'), ('E4', 'A4', 'C5', 'A4')), 59: (('F2', 'C3', 'F3', 'A3'), ('C4', 'F4', 'A4', 'F4')),
        61: (('D2', 'A2', 'D3', 'F3'), ('A3', 'D4', 'F4', 'D4')), 63: (('E2', 'B2', 'E3', 'G#3'), ('B3', 'E4', 'G#4', 'E4'))}
FADES = {'P4': 56, 'P6': 56, 'P11': 56, 'P7': 55}
HOLD = ('P29', 56, 57)


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    for pid, bar, q, h, _ in ECHOES:
        out.append((pid, 1, bar, 1.0, {bar: [(q, 4, None)], bar + 1: [(h, 8, None)]}))
    for pid, names in PADS.items():
        out.append((pid, 1, 57, 0, {b: [(n, 8, t)] for b, (n, t) in zip(BARS, held(names))}))
    out.append(('P32', 1, 57, 0, {b: [(PLUCKS[b], 4, None), (None, 4, None)] if b in PLUCKS else [(None, 8, None)] for b in BARS}))
    return out


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        x = write_bar(x, pid, b, ([(None, int(onset * 4), None)] if b == bar and onset else []) + events)
    return x


def harp(x, right=True, left=True):
    for bar in BARS:
        lh, rh = HARP[bar - (bar - 57) % 2]
        x = harp_bar(x, 'P26', bar, lh if left else (), rh if right else ())
    return x


def notes(x, tied=True):
    for line in lines():
        x = write_line(x, line)
    x = harp(x)
    return tie(x, *HOLD) if tied else x


def build(x):
    m = Marks(notes(x))
    for pid, bar in FADES.items():
        m.hairpin(pid, (bar, 0), (57, 0), 'diminuendo')
    for pid, bar, q, h, dyn in ECHOES:
        m.dynamic(pid, bar, 1.0, dyn)
        m.slur(pid, (bar, 1.0), (bar + 1, 0))
    for pid in PADS:
        m.dynamic(pid, 57, 0, 'pp')
    m.words('P32', 57, 0, 'pizz.', italic=False)
    m.dynamic('P32', 57, 0, 'p')
    m.dynamic('P26', 57, 0, 'p')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
