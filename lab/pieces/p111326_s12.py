"""111326 S12 (Nov 14 2026), [CONTINUE] after S11: bars 41-48.
The move: his lament phrase (bars 33-40) ends over its E pedal, and the main theme returns with the
whole orchestra on F, the same step from E to F that took the introduction into the theme at bar 9.
Its bass now rises (F, G, G sharp, A, B, the bass of the horn chords in bars 9-16) after the falling
lament.
- Melody: the oboe's theme of bars 8-16 with its slurs, portato and hairpins, in octaves: flute and
  Violin I an octave up (his idea, "having the violin ones up an octave"), oboe and Violin II as
  written. Flute and oboe take the pickup in bar 40 while the violins finish their phrase (a
  hand-off that overlaps, as at bar 15).
- Harmony: the horn chords of bars 9-16 (F, G, Em/G, E/G sharp, F/A, G/B, Em/B, E/B). Horn 1's C and
  horn 2's A are held over from bar 40. The clarinets double horns 1 and 2 an octave up; the violas
  stay with horn 2.
- The phrase rule, line by line: the harp's run goes on over the new chords (the top of the right
  hand with horn 1); cellos and bassoon go on as the bass; the double bass leaves pizzicato for arco
  under the tutti; the trombones keep their quarter notes on beat 1, now on the rising bass.
- mf, with the theme's own hairpins (up to the G in bar 43 and the F in bar 47).
usage (whisperer env): python lab/pieces/p111326_s12.py <working.xml (S11)> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import rebeam  # noqa: E402
from p111326_s5 import tie, write_bar  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
from p111326_s10 import held, octave  # noqa: E402
from xml_marks import Marks  # noqa: E402

BARS = range(41, 49)
THEME = {41: [('E5', 4), ('E5', 2), ('D5', 2)], 42: [('E5', 4), ('E5', 2), ('D5', 2)], 43: [('E5', 2), ('F5', 2), ('G5', 2), ('F5', 2)],
         44: [('E5', 2), ('D5', 2), ('D5', 2), ('C5', 2)], 45: [('D5', 4), ('D5', 2), ('C5', 2)], 46: [('D5', 4), ('D5', 2), ('C5', 2)],
         47: [('D5', 2), ('E5', 2), ('F5', 2), ('E5', 2)], 48: [('D5', 2), ('C5', 2), ('B4', 4)]}
PICKUP = [('E5', 2), ('D5', 2)]
HORN1 = ['C4', 'D4', 'E4', 'E4', 'F4', 'G4', 'G4', 'G#4']
HORN2 = ['A3', 'B3', 'B3', 'B3', 'C4', 'D4', 'E4', 'E4']
BASS = ['F3', 'G3', 'G3', 'G#3', 'A3', 'B3', 'B3', 'B3']
HARP = {41: (('F2', 'C3', 'F3', 'A3'), ('F4', 'A4', 'C5', 'A4')), 42: (('G2', 'D3', 'G3', 'B3'), ('G4', 'B4', 'D5', 'B4')),
        43: (('G2', 'E3', 'G3', 'B3'), ('G4', 'B4', 'E5', 'B4')), 44: (('G#2', 'E3', 'G#3', 'B3'), ('G#4', 'B4', 'E5', 'B4')),
        45: (('A2', 'F3', 'A3', 'C4'), ('A4', 'C5', 'F5', 'C5')), 46: (('B2', 'G3', 'B3', 'D4'), ('B4', 'D5', 'G5', 'D5')),
        47: (('B2', 'G3', 'B3', 'E4'), ('B4', 'E5', 'G5', 'E5')), 48: (('B2', 'G#3', 'B3', 'E4'), ('B4', 'E5', 'G#5', 'E5'))}
MELODY = {'P2': 1, 'P3': 0, 'P28': 1, 'P29': 0}
SLURS = [((40, 1.0), (41, 0)), ((41, 1.0), (42, 0)), ((42, 1.0), (44, 0.5)), ((44, 1.0), (45, 0)), ((45, 1.0), (46, 0)), ((46, 1.0), (48, 1.0))]
PORTATO = [(41, 0), (42, 0), (45, 0), (46, 0)]
HAIRPINS = [((42, 1.0), (43, 1.0), True), ((43, 1.5), (44, 1.5), False), ((46, 1.0), (47, 1.0), True), ((47, 1.5), (48, 0.5), False)]


def pad(names, k=0):
    return {b: [(octave(n, k), 8, t)] for b, (n, t) in zip(BARS, held([octave(n, 0) for n in names]))}


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    for pid, up in MELODY.items():
        bars = {b: [(octave(n, up), d, None) for n, d in THEME[b]] for b in BARS}
        if pid in ('P2', 'P3'):
            bars = {40: [(octave(n, up), d, None) for n, d in PICKUP], **bars}
            out.append((pid, 1, 40, 1.0, bars))
        else:
            out.append((pid, 1, 41, 0, bars))
    for pid, names, k in (('P9', HORN1, 0), ('P10', HORN2, 0), ('P11', BASS, 0), ('P5', HORN1, 1), ('P6', HORN2, 1), ('P30', HORN2, 0),
                          ('P31', BASS, -1), ('P7', BASS, -1), ('P32', BASS, -2)):
        out.append((pid, 1, 41, 0, pad(names, k)))
    out.append(('P14', 1, 41, 0, {b: [(n, 4, None), (None, 4, None)] for b, n in zip(BARS, BASS)}))
    out.append(('P15', 1, 41, 0, {b: [(octave(n, -1), 4, None), (None, 4, None)] for b, n in zip(BARS, BASS)}))
    return out


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        x = write_bar(x, pid, b, ([(None, int(onset * 4), None)] if b == bar and onset else []) + events)
    return x


def harp(x):
    for bar, (lh, rh) in HARP.items():
        x = harp_bar(x, 'P26', bar, lh, rh)
    return x


HOLDS = [('P9', 40, 41), ('P10', 40, 41), ('P30', 40, 41)]


def notes(x, tied=True):
    for line in lines():
        x = write_line(x, line)
    x = harp(x)
    if tied:
        for pid, b0, b1 in HOLDS:
            x = tie(x, pid, b0, b1)
    return x


def pad_slurs(line):
    """a slur over each four-bar half, from its first new note to its last (a held note is not new)"""
    pid, staff, bar, onset, bars = line
    starts = [b for b in sorted(bars) for n, d, t in bars[b][:1] if n and t not in ('stop', 'both')]
    if pid in [h[0] for h in HOLDS]:
        starts = starts[1:]
    out = []
    for half in (range(41, 45), range(45, 49)):
        s = [b for b in starts if b in half]
        if len(s) > 1:
            out.append(((s[0], 0), (s[-1], 0)))
    return out


def build(x):
    y = rebeam(notes(x))
    for pid in MELODY:
        y = beam_eighths(y, pid, range(40, 49))
    m = Marks(y)
    for pid in MELODY:
        for a, z in SLURS[0 if pid in ('P2', 'P3') else 1:]:
            m.slur(pid, a, z)
        for b, o in PORTATO:
            m.articulation(pid, b, o, 'detached-legato')
        m.dynamic(pid, *((40, 1.0) if pid in ('P2', 'P3') else (41, 0)), 'mf')
        for a, z, up in HAIRPINS:
            m.hairpin(pid, a, z, 'crescendo' if up else 'diminuendo')
    for line in lines():
        pid = line[0]
        if pid in MELODY:
            continue
        m.dynamic(pid, 41, 0, 'mp' if pid in ('P14', 'P15') else 'mf')
        if pid in ('P14', 'P15', 'P32'):
            continue
        for a, z in pad_slurs(line):
            m.slur(pid, a, z)
    m.words('P32', 41, 0, 'arco', italic=False)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
