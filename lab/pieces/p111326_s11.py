"""111326 S11 (Nov 14 2026): Brian's phrase rule (style/brian.md, "A new phrase starts from everything
that is already sounding") on the lines that S10 left hanging at bar 32.
- The harp's run (bars 29-32: the left hand rises on beat 1, the right hand arches on beat 2)
  continues through the new phrase over its chords: Am, E/G sharp, Em/G, D/F sharp, F, C/E, E+,
  Am/E. The left hand starts on the falling bass; the top of the right hand moves with horn 2 and
  the violas an octave higher. mp, one step up from its p, as the strings grow.
- The cor anglais and the E flat clarinet end their line on the G sharp of bar 32: each resolves to
  A in bar 33, slurred, and fades.
- The B flat clarinet's E is held into bar 33, where horn 1 takes the same E (a dovetail), and fades.
- The rest already has a place: the flute ends on its long B as Violin I takes the melody; the
  bassoon goes to the bass line; the pizzicato strings change to arco.
usage (whisperer env): python lab/pieces/p111326_s11.py <working.xml (S10)> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s5 import tie, write_bar  # noqa: E402
from p111326_s6 import harp_bar  # noqa: E402
from xml_marks import Marks  # noqa: E402

HARP = {33: (('A2', 'E3', 'A3', 'C4'), ('E4', 'A4', 'C5', 'A4')),
        34: (('G#2', 'E3', 'G#3', 'B3'), ('E4', 'G#4', 'B4', 'G#4')),
        35: (('G2', 'E3', 'G3', 'B3'), ('E4', 'G4', 'B4', 'G4')),
        36: (('F#2', 'D3', 'F#3', 'A3'), ('D4', 'F#4', 'A4', 'F#4')),
        37: (('F2', 'C3', 'F3', 'A3'), ('C4', 'F4', 'A4', 'F4')),
        38: (('E2', 'C3', 'E3', 'G3'), ('C4', 'E4', 'G4', 'E4')),
        39: (('E2', 'C3', 'E3', 'G#3'), ('C4', 'E4', 'G#4', 'E4')),
        40: (('E2', 'C3', 'E3', 'A3'), ('C4', 'E4', 'A4', 'E4'))}
ENDS = {'P4': 'A4', 'P5': 'A4', 'P6': 'E4'}


def harp(x):
    for bar, (lh, rh) in HARP.items():
        x = harp_bar(x, 'P26', bar, lh, rh)
    return x


def ends(x):
    for pid, name in ENDS.items():
        x = write_bar(x, pid, 33, [(name, 8, None)])
    return x


def notes(x, tied=True):
    x = ends(harp(x))
    return tie(x, 'P6', 32, 33) if tied else x


def build(x):
    m = Marks(notes(x))
    m.dynamic('P26', 33, 0, 'mp')
    for pid in ('P4', 'P5'):
        m.slur(pid, (32, 0), (33, 0), number=2)
    for pid in ENDS:
        m.hairpin(pid, (32, 0), (33, 0), 'diminuendo')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
