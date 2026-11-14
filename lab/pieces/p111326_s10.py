"""111326 S10 (Nov 14 2026), from Brian's panel message after S9.
- The opening "sounds modal... like F Lydian... it's not appealing to me": F then G made F sound like
  home, with B natural as its Lydian fourth. The introduction now starts on A minor, with the bass
  falling by half steps (A, G sharp, G, F sharp, F, to E in bars 7-8): the bass of his new section,
  so the introduction hints at it. Harp: Am, E/G sharp, D/F sharp, E. The clarinet's hint follows
  the new chords (C5 | B4 D5 | C5); horn 1's hint and the oboe's pickup stay.
- His new section (bars 32-40: the theme varied in Violin I over a lament bass sketched as horn
  chords): "I want the strings to take over... a bit more passion... the horns filling out the
  harmony... bassoons doubling at parts... trombones just quarter notes on the ground notes... the
  double bass comes in with pizz". Violin II plays the melody an octave lower, with his slurs; the
  horn chords spread over horns 1-2 and the Wagner tuba, held where a note repeats; the violas
  double horn 2; cellos and bassoon play the bass of his chords an octave lower; the double bass
  plays pizzicato an octave below them on each downbeat; the trombones play quarter notes on beat 1,
  in octaves. mf, a crescendo to f on the A5 in bar 36, then a diminuendo. Strings that leave
  pizzicato get "arco" (a technique lasts until the opposite one).
Dorico's MusicXML export leaves playing techniques out, so with_techniques() puts back the ones his
project has (S8 and S6) before the export becomes the working score.
usage (whisperer env): python lab/pieces/p111326_s10.py <working.xml> <out.xml>
                       python lab/pieces/p111326_s10.py --working <dorico_export.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span, rebeam  # noqa: E402
from p111326_s5 import concert_of, voice_one, write_bar  # noqa: E402
from p111326_s6 import beam_eighths, harp_bar  # noqa: E402
import p111326_s8  # noqa: E402
from xml_marks import Marks  # noqa: E402

TECHNIQUES = [('P31', 17, 0, 'arco'), ('P31', 25, 0, 'pizz.'), ('P30', 26, 0.5, 'pizz.'), ('P29', 26, 1.0, 'pizz.')]
LAMENT = ['A', 'A', 'G#', 'G', 'F#', 'F', 'E', 'E']
LAMENT_TIES = ['start', 'stop', None, None, None, None, 'start', 'stop']
HARP = {1: (('A2', 'C3', 'E3', 'A3'), ('C4', 'E4', 'A4', 'C5')),
        3: (('G#2', 'B2', 'E3', 'G#3'), ('B3', 'E4', 'G#4', 'B4')),
        5: (('F#2', 'A2', 'D3', 'F#3'), ('A3', 'D4', 'F#4', 'A4'))}
CLARINET = {2: ('A4', 'C5', 2), 4: ('B4', 'C5', 1)}
SECTION = range(33, 41)
EMPTY = '<note><rest/><duration>8</duration><voice>1</voice><type>whole</type><staff>1</staff></note>'


def name_of(p):
    step, alter, octave = p
    return step + {1: '#', -1: 'b', 0: ''}[alter] + str(octave)


def octave(name, k):
    return None if name is None else name[:-1] + str(int(name[-1]) + k)


def clear_bar(x, pid, bar):
    """every note of a one-voice bar (chord notes too) becomes one whole-bar rest; directions stay"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    assert '<backup>' not in body, f'{pid} bar {bar} has more than one voice'
    first = re.search(r'<note[ >]', body).start()
    return x[:s0] + body[:first] + EMPTY + re.sub(r'<note[ >].*?</note>', '', body[first:], flags=re.S) + x[s1:]


def put(x, pid, bar, events):
    return write_bar(clear_bar(x, pid, bar), pid, bar, events)


def clear_harp(x, pid, bar):
    s0, s1 = measure_span(x, pid, bar)
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', x[s0:s1], re.S))
    rest = lambda staff: f'<note><rest/><duration>8</duration><voice>{staff}</voice><type>whole</type><staff>{staff}</staff></note>'
    return x[:s0] + keep + rest(1) + '<backup><duration>8</duration></backup>' + rest(2) + x[s1:]


def held(names):
    """one note a bar, tied where the next bar has the same note"""
    kind = {(False, False): None, (True, False): 'stop', (False, True): 'start', (True, True): 'both'}
    return [(n, kind[(i > 0 and names[i - 1] == n, i + 1 < len(names) and names[i + 1] == n)]) for i, n in enumerate(names)]


def sketch(x):
    """his horn chords in bars 33-40 as three lines, top first (concert names)"""
    chords = []
    for bar in SECTION:
        s0, s1 = measure_span(x, 'P9', bar)
        notes = [m.group(0) for m in re.finditer(r'<note[ >].*?</note>', x[s0:s1], re.S) if '<rest' not in m.group(0)]
        chords.append(sorted((concert_of(x, 'P9', v) for v in notes), key=lambda p: -(p[2] * 12 + 'C D EF G A B'.index(p[0]) + p[1])))
    assert all(len(c) == 3 for c in chords), chords
    return [[name_of(c[k]) for c in chords] for k in range(3)]


def melody(x):
    """Violin I from bar 32 beat 2 to bar 40: {bar: [(concert name, divisions)]}"""
    out = {}
    for bar in range(32, 41):
        out[bar] = [(name_of(concert_of(x, 'P28', n)) if '<rest' not in n else None, int(re.search(r'<duration>(\d+)</duration>', n).group(1)))
                    for t, s, e, n in voice_one(x, 'P28', bar) if bar > 32 or t >= 4]
    return out


def lines(x):
    """every new line: (pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    top, mid, low = sketch(x)
    tune = melody(x)
    out = [('P31', 1, 1, 0, {b: [(LAMENT[b - 1] + '3', 8, LAMENT_TIES[b - 1])] for b in range(1, 9)}),
           ('P32', 1, 1, 0, {b: [(LAMENT[b - 1] + '2', 8, LAMENT_TIES[b - 1])] for b in range(1, 9)}),
           ('P29', 1, 32, 1.0, {b: [(octave(n, -1), d, None) for n, d in tune[b]] for b in tune})]
    for pid, names in (('P9', top), ('P10', mid), ('P11', low), ('P30', mid), ('P31', [octave(n, -1) for n in low]), ('P7', [octave(n, -1) for n in low])):
        out.append((pid, 1, 33, 0, {b: [(n, 8, t)] for b, (n, t) in zip(SECTION, held(names))}))
    out.append(('P32', 1, 33, 0, {b: [(octave(n, -2), 2, None), (None, 2, None), (None, 4, None)] for b, n in zip(SECTION, low)}))
    out.append(('P14', 1, 33, 0, {b: [(n, 4, None), (None, 4, None)] for b, n in zip(SECTION, low)}))
    out.append(('P15', 1, 33, 0, {b: [(octave(n, -1), 4, None), (None, 4, None)] for b, n in zip(SECTION, low)}))
    return out


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        if b == bar and onset:
            events = [(None, int(onset * 4), None)] + events
        x = put(x, pid, b, events)
    return x


def harp(x, right=True, left=True):
    for bar, (lh, rh) in HARP.items():
        old_lh, old_rh = p111326_s8.HARP[bar]
        x = harp_bar(clear_harp(x, 'P26', bar), 'P26', bar, lh if left else old_lh, rh if right else old_rh)
    return x


def clarinet(x):
    for bar, (old, new, _) in CLARINET.items():
        (t, s, e, n), = voice_one(x, 'P6', bar)
        assert name_of(concert_of(x, 'P6', n)) == old, (bar, n)
        x = put(x, 'P6', bar, [(new, 8, None)])
    return x


def notes(x):
    """the notes and ties of S10 (what Dorico has after the note entry)"""
    ls = lines(x)
    for line in ls[:2]:
        x = write_line(x, line)
    x = clarinet(harp(x))
    for line in ls[2:]:
        x = write_line(x, line)
    return x


def build(x):
    m = Marks(beam_eighths(rebeam(notes(x)), 'P29', range(32, 41)))
    m.slur('P6', (2, 0), (4, 0))
    for (b0, o0), (b1, o1) in VIOLIN_SLURS:
        m.slur('P29', (b0, o0), (b1, o1))
    m.words('P29', 32, 1.0, 'arco', italic=False)
    for pid in ('P28', 'P29'):
        m.dynamic(pid, 32, 1.0, 'mf')
        m.hairpin(pid, (33, 0), (36, 0.5), 'crescendo')
        m.dynamic(pid, 36, 1.0, 'f')
        m.hairpin(pid, (37, 0), (40, 1.5), 'diminuendo')
    for pid, spans in PAD_SLURS.items():
        m.dynamic(pid, 33, 0, 'mp')
        for a, z in spans:
            m.slur(pid, (a, 0), (z, 0))
    for pid in ('P30', 'P31'):
        m.words(pid, 33, 0, 'arco', italic=False)
    m.words('P32', 33, 0, 'pizz.', italic=False)
    m.dynamic('P32', 33, 0, 'mf')
    for pid in ('P14', 'P15'):
        m.dynamic(pid, 33, 0, 'mp')
    return m.text()


VIOLIN_SLURS = [((32, 1.0), (33, 0)), ((33, 1.0), (34, 0)), ((34, 1.0), (36, 0.5)), ((36, 1.0), (37, 0)), ((37, 1.0), (38, 0)),
                ((38, 1.0), (39, 1.5)), ((40, 0), (40, 1.5))]
PAD_SLURS = {'P9': [(33, 37)], 'P10': [(33, 40)], 'P11': [(33, 38)], 'P30': [(33, 36), (38, 40)], 'P31': [(33, 36), (37, 38)], 'P7': [(33, 38)]}


def with_techniques(x):
    m = Marks(x)
    for pid, bar, onset, text in TECHNIQUES:
        m.words(pid, bar, onset, text, italic=False)
    return m.text()


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[0] == '--working':
        open(args[2], 'w', encoding='utf-8').write(with_techniques(open(args[1], encoding='utf-8').read()))
    else:
        open(args[1], 'w', encoding='utf-8').write(build(open(args[0], encoding='utf-8').read()))
    print('wrote', args[-1])
