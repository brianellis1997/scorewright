"""111326 S6 (Nov 13 2026): S5 revised after Brian's panel message: "the pizzicato's almost there...
going up as well in the upper register, maybe some harp influence here as well... maybe the
introduction of a new instrument... the flute can't be detached, it needs some slurring".
- The pizzicato climbs each bar: cellos on the beat, violas on its offbeat, Violin II on beat 2 and
  its offbeat, up to D5, under the melody.
- The harp joins for the second phrase (28-31) with rising sixteenths, under the melody.
- A new color, the cor anglais, with a counter-line that moves in the long notes of the melody and
  rises while the melody falls; its turn in bar 29 is the theme's turn, inverted.
- Slurs for the flute and Violin I in 24-31 (each G5 slurred into the next phrase).
Everything else as S5 (lab/pieces/p111326_s5.py).
usage (whisperer env): python lab/pieces/p111326_s6.py <dorico_export.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import accidental, key_of, measure_span, rebeam, shift  # noqa: E402
from p111326_s5 import common, common_marks, parse, voice_one, write_bar  # noqa: E402
from xml_marks import Marks  # noqa: E402

PIZZ = {  # bar: cello on the beat, viola on its offbeat, Violin II on beat 2 and its offbeat
    24: ('C3', None, None, None),
    25: ('C#3', 'F4', 'A4', 'C#5'), 26: ('D3', 'F4', 'A4', 'D5'), 27: ('D3', 'G#4', 'B4', 'D5'),
    28: ('E3', 'E4', 'A4', 'C5'), 29: ('F#3', 'D4', 'A4', 'C5'), 30: ('D3', 'G4', 'B4', 'D5'),
    31: ('D3', 'G#4', 'B4', 'D5')}
HARP = {  # bar: left hand on beat 1, right hand on beat 2, sixteenths
    28: (('E3', 'A3', 'C4', 'E4'), ('A4', 'C5', 'A4', 'E4')),
    29: (('F#3', 'A3', 'C4', 'D4'), ('F#4', 'A4', 'C5', 'A4')),
    30: (('D3', 'G3', 'B3', 'D4'), ('G4', 'B4', 'D5', 'B4')),
    31: (('D3', 'E3', 'G#3', 'B3'), ('D4', 'E4', 'G#4', 'B4'))}
COR = {
    24: [(None, 4, None), ('A4', 4, 'start')],
    25: [('A4', 4, 'stop'), ('F4', 4, 'start')],
    26: [('F4', 2, 'stop'), ('G4', 2, None), ('A4', 2, None), ('B4', 2, 'start')],
    27: [('B4', 8, 'stop')],
    28: [('C5', 4, None), ('B4', 2, None), ('A4', 2, None)],
    29: [('G4', 2, None), ('F#4', 2, None), ('E4', 2, None), ('F#4', 2, None)],
    30: [('G4', 8, None)],
    31: [('G#4', 8, None)]}


def sixteenths(names, voice, staff, fifths, state):
    out = []
    for i, name in enumerate(names):
        step, alter, octave = parse(name)
        acc = accidental((step, alter, octave), fifths, state)
        b = 'begin' if i == 0 else 'end' if i == len(names) - 1 else 'continue'
        out.append(f'<note><pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter else '') + f'<octave>{octave}</octave></pitch>'
                   f'<duration>1</duration><voice>{voice}</voice><type>16th</type>' + (f'<accidental>{acc}</accidental>' if acc else '') +
                   f'<staff>{staff}</staff><beam number="1">{b}</beam><beam number="2">{b}</beam></note>')
    return ''.join(out)


def harp_bar(x, pid, bar, lh, rh):
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    assert '<pitch>' not in body, f'{pid} bar {bar} is not empty'
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', body, re.S))
    fifths = key_of(x, pid)
    right = '<note><rest/><duration>4</duration><voice>1</voice><type>quarter</type><staff>1</staff></note>' + sixteenths(rh, 1, 1, fifths, {})
    left = sixteenths(lh, 2, 2, fifths, {}) + '<note><rest/><duration>4</duration><voice>2</voice><type>quarter</type><staff>2</staff></note>'
    return x[:s0] + keep + right + '<backup><duration>8</duration></backup>' + left + x[s1:]


def beam_eighths(x, pid, bars):
    """eighths that follow each other inside one beat get a beam, as Dorico writes them (pairs in 2/4)"""
    for bar in bars:
        groups, cur, last_beat = [], [], None
        for t, s, e, note in voice_one(x, pid, bar):
            beat = t // 4
            if '<type>eighth</type>' in note and '<rest' not in note and (not cur or beat == last_beat):
                cur.append((s, e, note))
            else:
                if len(cur) > 1:
                    groups.append(cur)
                cur = [(s, e, note)] if '<type>eighth</type>' in note and '<rest' not in note else []
            last_beat = beat
        if len(cur) > 1:
            groups.append(cur)
        edits = []
        for g in groups:
            for i, (s, e, note) in enumerate(g):
                if '<beam' in note:
                    continue
                b = 'begin' if i == 0 else 'end' if i == len(g) - 1 else 'continue'
                edits.append((s, e, note.replace('</staff>', f'</staff><beam number="1">{b}</beam>', 1)))
        for s, e, t in sorted(edits, reverse=True):
            x = x[:s] + t + x[e:]
    return x


def build(x):
    x = common(x)
    for bar, (vc, vla, v2a, v2b) in PIZZ.items():
        x = write_bar(x, 'P31', bar, [(vc, 2, None), (None, 2, None), (None, 4, None)])
        if vla:
            x = write_bar(x, 'P30', bar, [(None, 2, None), (vla, 2, None), (None, 4, None)])
            x = write_bar(x, 'P29', bar, [(None, 4, None), (v2a, 2, None), (v2b, 2, None)])
    for bar, events in COR.items():
        x = write_bar(x, 'P4', bar, events)
    for bar, (lh, rh) in HARP.items():
        x = harp_bar(x, 'P26', bar, lh, rh)
    x = rebeam(x)
    x = beam_eighths(x, 'P4', COR)
    x = beam_eighths(x, 'P29', PIZZ)
    m = Marks(x)
    common_marks(m)
    for pid, slurs in (('P28', [((25, 1.0), (27, 0)), ((27, 1.0), (31, 0))]),
                       ('P2', [((25, 1.0), (27, 0)), ((27, 1.0), (31, 0))]),
                       ('P4', [((24, 1.0), (27, 0)), ((28, 0), (31, 0))])):
        for a, b in slurs:
            m.slur(pid, a, b)
    m.dynamic('P4', 24, 1.0, 'p')
    m.words('P31', 24, 0, 'pizz.', italic=False)
    m.dynamic('P31', 24, 0, 'p')
    m.words('P30', 25, 0.5, 'pizz.', italic=False)
    m.dynamic('P30', 25, 0.5, 'p')
    m.words('P29', 25, 1.0, 'pizz.', italic=False)
    m.dynamic('P29', 25, 1.0, 'p')
    m.dynamic('P26', 28, 1.0, 'p')
    return m.text()


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    open(dst, 'w', encoding='utf-8').write(build(open(src, encoding='utf-8').read()))
    print('wrote', dst)
