"""111326 S13 (Nov 14 2026), from Brian's reason after S12: "we do the whole theme but a bit more
intense... ramping up with a fuller orchestra... we bring back the high G falling down to E phrase,
the thing that started with the flute and the violin earlier, and that's an explosion, because it's
kind of the climax... I know we definitely want the first four bars... the F sharp going to E
major... then we get into a quieter phrase... what do you think?"
The climax, bars 49-56, ff, the whole orchestra:
- Melody: the phrase of bars 25-32 (E held, G falling back to E, then E D C B), in octaves:
  piccolo two octaves up, flute, E flat clarinet and Violin I one octave up, oboe, both trumpets and
  Violin II as written. Its end changes: it falls on to A (E, D, C, B, A) while the bass rises.
- Harmony: the first four bars as in bars 25-28 (F/C, F+ over C sharp, Dm, E7/D, the bass rising C,
  C sharp, D). Then the bass goes on rising, E, F sharp, G sharp, A (Am/E, D7/F sharp, E7/G sharp,
  Am): the first full cadence on A minor in the piece, so the climax closes as one thing.
- Counter-line: the cor anglais line of bars 25-32 comes back with it, doubled by the B flat
  clarinet and the violas; its last two notes follow the new harmony (G sharp, A).
- Horns and Wagner tuba hold the chords, with the common notes tied; cellos, bassoon and trombone
  play the rising bass, bass trombone, tuba and double basses an octave lower; the harp's run goes on.
- A diminuendo as the melody falls (bars 53-56), so the quieter idea after it can begin.
usage (whisperer env): python lab/pieces/p111326_s13.py <working.xml (S12)> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import rebeam  # noqa: E402
from p111326_s5 import write_bar  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
from p111326_s10 import held, octave  # noqa: E402
from xml_marks import Marks  # noqa: E402

BARS = range(49, 57)
MELODY = {49: [('E5', 8, 'start')], 50: [('E5', 4, 'stop'), ('G5', 4, None)], 51: [('E5', 8, 'start')], 52: [('E5', 4, 'stop'), ('G5', 4, None)],
          53: [('E5', 2, None), ('D5', 6, None)], 54: [('C5', 8, None)], 55: [('B4', 8, None)], 56: [('A4', 8, None)]}
MELODY_PARTS = {'P1': 2, 'P2': 1, 'P5': 1, 'P28': 1, 'P3': 0, 'P12': 0, 'P13': 0, 'P29': 0}
COUNTER = {49: [(None, 4, None), ('A4', 4, 'start')], 50: [('A4', 4, 'stop'), ('F4', 4, 'start')],
           51: [('F4', 2, 'stop'), ('G4', 2, None), ('A4', 2, None), ('B4', 2, 'start')], 52: [('B4', 8, 'stop')],
           53: [('C5', 4, None), ('B4', 2, None), ('A4', 2, None)], 54: [('G4', 2, None), ('F#4', 2, None), ('E4', 2, None), ('F#4', 2, None)],
           55: [('G#4', 8, None)], 56: [('A4', 8, None)]}
COUNTER_PARTS = ('P4', 'P6', 'P30')
HORN1 = ['F4', 'F4', 'F4', 'G#4', 'A4', 'A4', 'G#4', 'A4']
HORN2 = ['C4', 'C#4', 'D4', 'D4', 'C4', 'C4', 'D4', 'C4']
TUBA_W = ['A3', 'A3', 'A3', 'B3', 'A3', 'A3', 'B3', 'A3']
BASS = ['C3', 'C#3', 'D3', 'D3', 'E3', 'F#3', 'G#3', 'A3']
PADS = [('P9', HORN1, 0), ('P10', HORN2, 0), ('P11', TUBA_W, 0), ('P31', BASS, 0), ('P7', BASS, 0), ('P14', BASS, 0),
        ('P15', BASS, -1), ('P16', BASS, -1), ('P32', BASS, -1)]
HARP = {49: (('C3', 'F3', 'A3', 'C4'), ('F4', 'A4', 'C5', 'A4')), 50: (('C#3', 'F3', 'A3', 'C#4'), ('F4', 'A4', 'C#5', 'A4')),
        51: (('D3', 'F3', 'A3', 'D4'), ('F4', 'A4', 'D5', 'A4')), 52: (('D3', 'E3', 'G#3', 'B3'), ('D4', 'E4', 'G#4', 'B4')),
        53: (('E3', 'A3', 'C4', 'E4'), ('A4', 'C5', 'A4', 'E4')), 54: (('F#3', 'A3', 'C4', 'D4'), ('F#4', 'A4', 'C5', 'A4')),
        55: (('G#2', 'E3', 'G#3', 'B3'), ('D4', 'E4', 'G#4', 'B4')), 56: (('A2', 'E3', 'A3', 'C4'), ('E4', 'A4', 'C5', 'A4'))}
MELODY_SLURS = [((50, 1.0), (52, 0)), ((52, 1.0), (56, 0))]
COUNTER_SLURS = [((49, 1.0), (52, 0)), ((53, 0), (56, 0))]
DIM = ((53, 0), (56, 0))


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    for pid, k in MELODY_PARTS.items():
        out.append((pid, 1, 49, 0, {b: [(octave(n, k), d, t) for n, d, t in ev] for b, ev in MELODY.items()}))
    for pid in COUNTER_PARTS:
        out.append((pid, 1, 49, 0, COUNTER))
    for pid, names, k in PADS:
        out.append((pid, 1, 49, 0, {b: [(octave(n, k), 8, t)] for b, (n, t) in zip(BARS, held(names))}))
    return out


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        x = write_bar(x, pid, b, events)
    return x


def harp(x):
    for bar, (lh, rh) in HARP.items():
        x = harp_bar(x, 'P26', bar, lh, rh)
    return x


def notes(x):
    for line in lines():
        x = write_line(x, line)
    return harp(x)


def pad_slurs(line):
    """a slur over each four-bar half, from its first new note to its last"""
    pid, staff, bar, onset, bars = line
    starts = [b for b in sorted(bars) for n, d, t in bars[b][:1] if n and t not in ('stop', 'both')]
    out = []
    for half in (range(49, 53), range(53, 57)):
        s = [b for b in starts if b in half]
        if len(s) > 1:
            out.append(((s[0], 0), (s[-1], 0)))
    return out


def build(x):
    y = rebeam(notes(x))
    for pid in COUNTER_PARTS + ('P3', 'P29'):
        y = beam_eighths(y, pid, BARS)
    m = Marks(y)
    for line in lines():
        pid = line[0]
        m.dynamic(pid, 49, 1.0 if pid in COUNTER_PARTS else 0, 'ff')
        if pid in MELODY_PARTS:
            for a, z in MELODY_SLURS:
                m.slur(pid, a, z)
            m.hairpin(pid, *DIM, 'diminuendo')
        elif pid in COUNTER_PARTS:
            for a, z in COUNTER_SLURS:
                m.slur(pid, a, z)
        else:
            for a, z in pad_slurs(line):
                m.slur(pid, a, z)
    m.dynamic('P26', 49, 0, 'f')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
