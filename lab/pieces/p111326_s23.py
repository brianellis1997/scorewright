"""111326 S23 (Nov 16 2026), after Brian's messages at 21:04 and 21:16: the climax fades and stops for
his new cor anglais melody (bars 60-77), whose chords he sketched as triads in the bassoon (61-78).
"I want decrescendo happening in measure 60"; "the quarter notes should be like that same quarter
notes accents that we've been using this whole time... similar slurring as before for the cor
anglais"; "there's a lot of like tricords but maybe we want to space those out better cuz I can
imagine it would be very muddy... explode them out into whatever instruments... nothing really over
the cor anglais"; "a mimicking thing... maybe like the flute and soft register... not taking away
from the cor anglais... when it hits that A B in measure 72 the flute should kind of drop out".
- Bars 59-60: every part that holds the climax chord fades from bar 59 and stops on beat 2 of bar 60,
  where his pickup (G, F) comes in alone. Held on, the chord's G sharp and E rub a semitone against it.
- Cor anglais: mp; each 8th-note pickup slurred into the next downbeat quarter, which is portato.
- His chords, pp: violas the top note, the bassoon the middle one, cellos the bass, double basses the
  bass an octave lower; held notes tied over the bar line. In bars 68-71, where the melody is high,
  the violas move up (D, C, C, B) to open the chord.
- Flute, pp: each cor anglais pickup echoed one bar later, an octave higher (the last note fitted to
  the chord), slurred into a portato quarter. It stops on the downbeat of bar 72.
usage (whisperer env): python lab/pieces/p111326_s23.py <working.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span, rebeam  # noqa: E402
from p111326_s5 import write_bar  # noqa: E402
from p111326_s10 import clear_bar, held, put  # noqa: E402
from xml_marks import Marks  # noqa: E402

HELD = ['P2', 'P3', 'P5', 'P6', 'P7', 'P9', 'P10', 'P11', 'P28', 'P29']
REPEATED = ['P14', 'P15', 'P16', 'P17', 'P31', 'P32']
CHORD = 'P30'
FADE = HELD + REPEATED + [CHORD]
BARS = range(61, 79)
VIOLA = ['A3', 'A3', 'A3', 'A3', 'A3', 'B3', 'B3', 'D4', 'C4', 'C4', 'B3', 'A3', 'F3', 'F3', 'E3', 'E3', 'E3', 'E3']
BASSOON = ['E3', 'E3', 'F3', 'F#3', 'F3', 'G3', 'G3', 'F3', 'F3', 'E3', 'E3', 'D3', 'D3', 'D3', 'D3', 'C3', 'C3', 'C3']
CELLO = ['C3', 'C3', 'C3', 'C3', 'D3', 'E3', 'D3', 'D3', 'C3', 'C3', 'B2', 'B2', 'A2', 'G2', 'G2', 'G2', 'G#2', 'A2']
BASS = [n[:-1] + str(int(n[-1]) - 1) for n in CELLO]
PADS = {'P30': VIOLA, 'P7': BASSOON, 'P31': CELLO, 'P32': BASS}
ECHOES = {61: ('G5', 'F5', 'E5'), 63: ('G5', 'F5', 'E5'), 65: ('G5', 'A5', 'B5'), 67: ('E5', 'D5', 'E5'),
          69: ('C6', 'B5', 'A5'), 71: ('C6', 'B5', 'G5')}
CA_SLURS = [((b, 1.0), (b + 2, 0)) for b in range(60, 76, 2)]
PHRASES = [(61, 64), (65, 68), (69, 72), (73, 76), (77, 78)]


TYPES = {2: 'eighth', 4: 'quarter', 8: 'half'}


def cut(x, pid, bar, at=4, length=8):
    """the bar sounds until `at` divisions: a note that lasts past it ends there, keeping its tie from
    the bar before and its marks; notes that start later go, and one rest fills the bar"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    assert '<backup>' not in body, (pid, bar)
    out, pos, t, start, end = [], 0, 0, 0, None
    for m in re.finditer(r'<note[ >].*?</note>', body, re.S):
        s = m.group(0)
        d = int(re.search(r'<duration>(\d+)</duration>', s).group(1))
        if '<chord/>' not in s:
            start, t = t, t + d
        out.append(body[pos:m.start()])
        pos = m.end()
        if start >= at:
            continue
        if start + d > at:
            assert '<rest' not in s and '<dot/>' not in s and 'type="start"' not in s, (pid, bar, s)
            s = s.replace(f'<duration>{d}</duration>', f'<duration>{at - start}</duration>')
            s = re.sub(r'<type>\w+</type>', f'<type>{TYPES[at - start]}</type>', s)
        out.append(s)
        end = len(''.join(out))
    text = ''.join(out)
    rest = f'<note><rest/><duration>{length - at}</duration><voice>1</voice><type>{TYPES[length - at]}</type><staff>1</staff></note>'
    body = text[:end] + rest + text[end:] + body[pos:]
    return x[:s0] + body + x[s1:]


def stop(x):
    """bar 60: every part of the climax chord sounds on beat 1 only"""
    for pid in FADE:
        x = cut(x, pid, 60)
    return x


def pad_line(pid):
    names = PADS[pid]
    return (pid, 1, 61, 0, {b: [(n, 8, t)] for b, (n, t) in zip(BARS, held(names))})


def echo_line():
    """the flute from beat 2 of bar 61 (the writer puts the rest before it)"""
    bars = {}
    for b, (a, c, land) in ECHOES.items():
        bars[b] = ([(None, 4, None)] if b > 61 else []) + [(a, 2, None), (c, 2, None)]
        bars[b + 1] = [(land, 4, None), (None, 4, None)]
    return ('P2', 1, 61, 1.0, bars)


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    return [echo_line()] + [pad_line(pid) for pid in ('P30', 'P7', 'P31', 'P32')]


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        events = ([(None, int(onset * 4), None)] if b == bar and onset else []) + events
        x = put(x, pid, b, events) if pid == 'P7' else write_bar(x, pid, b, events)
    return x


def notes(x):
    x = stop(x)
    for line in lines():
        x = write_line(x, line)
    return x


def slur_groups(names):
    """phrase slurs for a held line: from the first to the last new note of each phrase"""
    out = []
    for a, z in PHRASES:
        starts = [b for b, (n, t) in zip(BARS, held(names)) if a <= b <= z and t not in ('stop', 'both')]
        if len(starts) > 1:
            out.append(((starts[0], 0), (starts[-1], 0)))
    return out


def build(x):
    m = Marks(notes(x))
    for pid in FADE:
        m.hairpin(pid, (59, 0), (60, 1.0), 'diminuendo')
    m.dynamic('P4', 60, 1.0, 'mp')
    for a, z in CA_SLURS:
        m.slur('P4', a, z)
        m.articulation('P4', z[0], 0, 'detached-legato')
    m.dynamic('P2', 61, 1.0, 'pp')
    for b in ECHOES:
        m.slur('P2', (b, 1.0), (b + 1, 0))
        m.articulation('P2', b + 1, 0, 'detached-legato')
    for pid in PADS:
        m.dynamic(pid, 61, 0, 'pp')
        for a, z in slur_groups(PADS[pid]):
            m.slur(pid, a, z)
    m.words('P30', 61, 0, 'unis.', italic=False)
    return rebeam(m.text())


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
