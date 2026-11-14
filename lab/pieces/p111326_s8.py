"""111326 S8 (Nov 13 2026), on S7 (everything one bar later): an 8-bar introduction and a touch of
warmth where the horns drop out.
- Introduction, bars 1-8: "sparse, but maybe include some hints at the second thing in it as well,
  and maybe some hints to this first thing as well". The theme's own loop at half speed (F, G,
  E minor, E: two bars a chord) over a cello and bass pedal, pp; the harp's rising figure from the
  second section (S6) in every other bar; the clarinet hints at the second theme's shape (a held
  note, then a rising third, then the held note again: A4 | B4 D5 | B4); horn 1 hints at the
  first theme's head (two eighths slurred into a portato quarter), and the oboe's real pickup in
  bar 8 answers it an octave higher. Bar 8 is E major, so the theme lands on F in bar 9.
- Warmth, bars 17-24: "I feel like there's something missing when the horns drop off as the flute
  takes over... a touch more warmth... not too thick". After the horns stop, nothing sounds below
  the viola's C4. The cellos (arco) and one bassoon, pp, play each chord's bass (F, G, E) and hold
  it where it repeats. The cellos stop on beat 1 of bar 24 to take up pizzicato for bar 25.
usage (whisperer env): python lab/pieces/p111326_s8.py <S7.xml> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s5 import write_bar  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
from p111326_s2 import rebeam  # noqa: E402
from xml_marks import Marks  # noqa: E402

PEDAL = {1: 'F', 2: 'F', 3: 'G', 4: 'G', 5: 'E', 6: 'E', 7: 'E', 8: 'E'}
TIE_PEDAL = {1: 'start', 2: 'stop', 3: 'start', 4: 'stop', 5: 'start', 6: 'both', 7: 'both', 8: 'stop'}
HARP = {  # bar: (left hand on beat 1, right hand on beat 2), sixteenths
    1: (('F2', 'A2', 'C3', 'F3'), ('A3', 'C4', 'F4', 'A4')),
    3: (('G2', 'B2', 'D3', 'G3'), ('B3', 'D4', 'G4', 'B4')),
    5: (('E2', 'G2', 'B2', 'E3'), ('G3', 'B3', 'E4', 'G4')),
    7: (('E2', 'G#2', 'B2', 'E3'), ('G#3', 'B3', 'E4', 'G#4'))}
CLARINET = {2: [('A4', 8, None)], 3: [('B4', 4, None), ('D5', 4, None)], 4: [('B4', 8, None)]}
HORN = {6: [(None, 4, None), ('E4', 2, None), ('D4', 2, None)], 7: [('E4', 4, None), (None, 4, None)]}
WARM = {17: [('F3', 8, None)], 18: [('G3', 8, None)], 19: [('E3', 8, 'start')], 20: [('E3', 8, 'stop')],
        21: [('F3', 8, None)], 22: [('G3', 8, None)], 23: [('E3', 8, 'start')]}
CELLO_24 = [('E3', 4, 'stop'), (None, 4, None)]
BASSOON_24 = [('E3', 8, 'stop')]


def notes(x):
    for bar, root in PEDAL.items():
        tie = TIE_PEDAL[bar]
        x = write_bar(x, 'P31', bar, [(root + '3', 8, tie)])
        x = write_bar(x, 'P32', bar, [(root + '2', 8, tie)])
    for bar, (lh, rh) in HARP.items():
        x = harp_bar(x, 'P26', bar, lh, rh)
    for bar, events in CLARINET.items():
        x = write_bar(x, 'P6', bar, events)
    for bar, events in HORN.items():
        x = write_bar(x, 'P9', bar, events)
    for pid in ('P31', 'P7'):
        for bar, events in WARM.items():
            x = write_bar(x, pid, bar, events)
    x = write_bar(x, 'P31', 24, CELLO_24)
    x = write_bar(x, 'P7', 24, BASSOON_24)
    x = rebeam(x)
    return beam_eighths(x, 'P9', HORN)


def build(x):
    m = Marks(notes(x))
    for pid in ('P31', 'P32'):
        m.dynamic(pid, 1, 0, 'pp')
    m.dynamic('P26', 1, 1.0, 'p')
    m.dynamic('P6', 2, 0, 'p')
    m.slur('P6', (2, 0), (4, 0))
    m.dynamic('P9', 6, 1.0, 'pp')
    m.slur('P9', (6, 1.0), (7, 0))
    m.articulation('P9', 7, 0, 'detached-legato')
    for pid in ('P31', 'P7'):
        m.dynamic(pid, 17, 0, 'pp')
        m.slur(pid, (17, 0), (20, 0))
        m.slur(pid, (21, 0), (24, 0))
    m.words('P31', 17, 0, 'arco', italic=False)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
