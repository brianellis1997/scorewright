"""111326 S14 (Nov 14 2026): S13's climax again, after Brian's notes on it: "the transition is not
smooth... you're missing the G fall into that E... what instruments are free to take this? maybe
the trumpets... a trumpet in that high E, especially the G, is going to overpower the whole
orchestra... the trumpets haven't played anything up to this point... either move them down an
octave or have them warm up, that could also dovetail into this new phrase... the harp is not going
to be heard... what about doubling it a third down or a sixth below to fill out the harmony".
- The G returns: the trumpets come in softly in bar 47 on the E and B of the chord (they warm up
  while the theme ends), then play the G pickup in bar 48 that falls to the E in bar 49, in thirds.
  Their part is an octave lower than in S13 (melody E4 to G4), and they play f, not ff.
- Spacing: each octave of the melody gets a second voice a third below (a fourth where a third
  does not fit the chord): Violin II and the trumpet 2 under the oboe and trumpet 1, the E flat
  clarinet under the flute and Violin I. The piccolo doubles the flute.
- Instrumental dynamics: brass f, strings and woodwinds ff. The harp, which nobody hears in the
  tutti, ends its run with one full F chord on the downbeat of bar 49.
- The transition: horns, clarinets, violas, low strings, bassoon and trombones grow through the
  last notes of bar 48 into the ff.
- The rest is S13: the cor anglais line with clarinet and violas, the horn chords, the rising bass
  (C, C sharp, D, then E, F sharp, G sharp, A), the full close on A minor, the diminuendo.
usage (whisperer env): python lab/pieces/p111326_s14.py <working.xml (S12)> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import key_of, measure_span, rebeam, shift, transpose_of  # noqa: E402
from p111326_s5 import accidental, parse, write_bar  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import held, octave  # noqa: E402
from xml_marks import Marks  # noqa: E402
import p111326_s13 as s13  # noqa: E402

BARS = s13.BARS
SECOND = {49: [('C5', 8, None)], 50: [('C#5', 4, None), ('E5', 4, None)], 51: [('C5', 8, None)], 52: [('B4', 4, None), ('E5', 4, None)],
          53: [('C5', 2, None), ('B4', 6, None)], 54: [('A4', 8, None)], 55: [('G#4', 8, None)], 56: [('E4', 8, None)]}
MELODY_PARTS = {'P1': 1, 'P2': 1, 'P28': 1, 'P3': 0}
SECOND_PARTS = {'P5': 1, 'P29': 0}
TRUMPET1 = {47: [('E4', 8, 'start')], 48: [('E4', 4, 'stop'), ('G4', 4, None)], **{b: [(octave(n, -1), d, t) for n, d, t in ev] for b, ev in s13.MELODY.items()}}
TRUMPET2 = {47: [('B3', 8, 'start')], 48: [('B3', 4, 'stop'), ('E4', 4, None)],
            **{b: [(octave(n, -1), d, t) for n, d, t in ev] for b, ev in SECOND.items() if b != 56}, 56: [('C4', 8, None)]}
HARP_CHORD = (('C2', 'F2', 'C3'), ('F4', 'A4', 'C5'))
BRASS = ('P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16')
RAMP = {'P5': 48, 'P6': 47, 'P7': 46, 'P9': 48, 'P10': 47, 'P11': 46, 'P14': 48, 'P15': 48, 'P30': 47, 'P31': 46, 'P32': 46}
MELODY_SLURS = s13.MELODY_SLURS
TRUMPET_SLURS = [((48, 1.0), (49, 0))] + MELODY_SLURS


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    for pid, k in MELODY_PARTS.items():
        out.append((pid, 1, 49, 0, {b: [(octave(n, k), d, t) for n, d, t in ev] for b, ev in s13.MELODY.items()}))
    for pid, k in SECOND_PARTS.items():
        out.append((pid, 1, 49, 0, {b: [(octave(n, k), d, t) for n, d, t in ev] for b, ev in SECOND.items()}))
    out.append(('P12', 1, 47, 0, TRUMPET1))
    out.append(('P13', 1, 47, 0, TRUMPET2))
    out += [l for l in s13.lines() if l[0] in s13.COUNTER_PARTS or l[0] in [p[0] for p in s13.PADS]]
    return out


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        x = write_bar(x, pid, b, events)
    return x


def chord_notes(x, pid, names, staff, voice, dur=8):
    d, c = transpose_of(x, pid)
    fifths, state, out = key_of(x, pid), {}, []
    for i, name in enumerate(names):
        step, alter, octv = shift(parse(name), -d, -c)
        acc = accidental((step, alter, octv), fifths, state)
        out.append('<note>' + ('<chord/>' if i else '') + f'<pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter else '') +
                   f'<octave>{octv}</octave></pitch><duration>{dur}</duration><voice>{voice}</voice><type>half</type>' +
                   (f'<accidental>{acc}</accidental>' if acc else '') + f'<staff>{staff}</staff></note>')
    return ''.join(out)


def harp(x, bar=49):
    s0, s1 = measure_span(x, 'P26', bar)
    body = x[s0:s1]
    assert '<pitch>' not in body, f'harp bar {bar} is not empty'
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', body, re.S))
    lh, rh = HARP_CHORD
    return x[:s0] + keep + chord_notes(x, 'P26', rh, 1, 1) + '<backup><duration>8</duration></backup>' + chord_notes(x, 'P26', lh, 2, 2) + x[s1:]


def notes(x):
    for line in lines():
        x = write_line(x, line)
    return harp(x)


def build(x):
    y = rebeam(notes(x))
    for pid in s13.COUNTER_PARTS + ('P3', 'P29'):
        y = beam_eighths(y, pid, BARS)
    m = Marks(y)
    for pid, bar in RAMP.items():
        m.hairpin(pid, (bar, 0), (49, 0), 'crescendo')
    for line in lines():
        pid = line[0]
        if pid in ('P12', 'P13'):
            m.dynamic(pid, 47, 0, 'mp')
            m.hairpin(pid, (47, 0), (49, 0), 'crescendo')
        m.dynamic(pid, 49, 1.0 if pid in s13.COUNTER_PARTS else 0, 'f' if pid in BRASS else 'ff')
        if pid in MELODY_PARTS or pid in SECOND_PARTS or pid in ('P12', 'P13'):
            for a, z in (TRUMPET_SLURS if pid in ('P12', 'P13') else MELODY_SLURS):
                m.slur(pid, a, z)
            m.hairpin(pid, *s13.DIM, 'diminuendo')
        elif pid in s13.COUNTER_PARTS:
            for a, z in s13.COUNTER_SLURS:
                m.slur(pid, a, z)
        else:
            for a, z in s13.pad_slurs(line):
                m.slur(pid, a, z)
    m.dynamic('P26', 49, 0, 'f')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
