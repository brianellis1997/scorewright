"""111326 S18 (Nov 14 2026): the climax orchestrated around the phrase Brian wrote himself after
S16 (trumpet 1 in bars 48-52, Violin I from bar 52, the viola's chords for bars 49-60): "let me fill
out this phrase so you don't have to keep guessing... notice how the trumpets are playing the first
statements, the G fall into the E; it's a very easy thing for brass to play; brass can't play the
fluid lines... the violins take over the melody... violin 2 doubling an octave below... the viola
is showing the harmony that I want for this entire phrase... I like the texture that you have".
His notes stay as he wrote them (D flat in bar 56 respelled C sharp, the note of his chord there).
- Harmony (his viola): F, G, Em, A, Dm, G, C, A7 over C sharp, Dm, F (with his D sharp: the German
  sixth), E, E. Bass F G E A D G C C# D F E E.
- Bars 48-52, the brass statement: trumpet 2 a third or fourth below his trumpet 1; horns 1 and 2
  double them from bar 49. The violins pulse his chords in eighths (Violin I the top note, Violin II
  the middle one) and the flute and piccolo run above, as in S16; their last run falls into his
  C sharp on beat 2 of bar 52, where the flute takes the melody with Violin I.
- Bars 52-60, the violins: Violin II and the oboe an octave below his Violin I; the horns, Wagner
  tuba, cor anglais and B flat clarinet hold his chords (his voicing, held where a note repeats);
  his violas keep their chords.
- Rhythm all through, as in S16: cellos in eighths, double basses, trombones and tuba in accented
  quarters on the bass, timpani on A, D and E; the bassoon holds the bass. Lead-ins in bar 48 and
  the timpani roll stay; the E flat clarinet resolves G sharp to A; the harp's F chord on bar 49.
usage (whisperer env): python lab/pieces/p111326_s18.py <working.xml> <out.xml>
                       python lab/pieces/p111326_s18.py --working <dorico_export.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span, rebeam  # noqa: E402
import p111326_s5  # noqa: E402
from p111326_s5 import write_bar  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import clear_bar, held, name_of, octave  # noqa: E402
from xml_marks import Marks  # noqa: E402
import p111326_s14 as s14  # noqa: E402
from p111326_s15 import beam16  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
BARS = range(49, 61)
TECHNIQUES = [('P31', 17, 0, 'arco'), ('P31', 25, 0, 'pizz.'), ('P30', 26, 0.5, 'pizz.'), ('P29', 26, 1.0, 'pizz.'), ('P29', 32, 1.0, 'arco'),
              ('P30', 33, 0, 'arco'), ('P31', 33, 0, 'arco'), ('P32', 33, 0, 'pizz.'), ('P32', 41, 0, 'arco')]
CHORDS = {49: ('C4', 'F4', 'A4'), 50: ('D4', 'G4', 'B4'), 51: ('E4', 'G4', 'B4'), 52: ('E4', 'A4', 'C#5'), 53: ('D4', 'F4', 'A4'),
          54: ('D4', 'G4', 'B4'), 55: ('C4', 'E4', 'G4'), 56: ('C#4', 'E4', 'G4'), 57: ('D4', 'F4', 'A4'), 58: ('C4', 'F4', 'A4'),
          59: ('B3', 'E4', 'G#4'), 60: ('B3', 'E4', 'G#4')}
BASS = ['F3', 'G3', 'E3', 'A3', 'D3', 'G3', 'C3', 'C#3', 'D3', 'F3', 'E3', 'E3']
TIMPANI = ['A2', 'D3', 'E2', 'A2', 'D3', 'D3', 'E2', 'A2', 'D3', 'A2', 'E2', 'E2']
MELODY = {52: [('C#6', 4, None)], 53: [('D6', 6, None), ('E6', 2, None)], 54: [('F6', 4, None), ('E6', 2, None), ('D6', 2, None)],
          55: [('B5', 6, None), ('C6', 2, None)], 56: [('C#6', 8, None)], 57: [('C6', 6, None), ('D6', 2, None)], 58: [('D#6', 8, None)],
          59: [('E6', 8, 'start')], 60: [('E6', 8, 'stop')]}
RUNS = {49: 'A5 Bb5 C6 D6 E6 F6 F#6 G6', 50: 'A6 G6 F#6 F6 E6 D6 C6 B5', 51: 'A5 B5 C6 D6 D#6 E6 F#6 G6', 52: 'A6 G#6 F#6 E6'}
LEAD_IN = {'P31': [('C#3', 2, None), ('D#3', 1, None), ('E3', 1, None)], 'P7': [('C#3', 2, None), ('D#3', 1, None), ('E3', 1, None)],
           'P32': [('C#2', 2, None), ('D#2', 1, None), ('E2', 1, None)]}
HARP_CHORD = (('F2', 'C3', 'F3'), ('A4', 'C5', 'A5'))
VIOLA_49 = ('C4', 'A4')
s14.HARP_CHORD = HARP_CHORD
MELODY_SLURS = [((52, 1.0), (54, 1.5)), ((55, 0), (56, 0)), ((57, 0), (59, 0))]
BRASS_SLURS = [((48, 1.0), (49, 0)), ((50, 1.0), (51, 0))]
RUN_SLURS = [((49, 0), (50, 1.75)), ((51, 0), (52, 0.75))]
ACCENTS = ('P14', 'P15', 'P16')
PAD_PARTS = ('P9', 'P10', 'P11', 'P4', 'P6')


def shift(events, k):
    return {b: [(octave(n, k), d, t) for n, d, t in ev] for b, ev in events.items()}


def pad(voice):
    """bars 53-60 of one voice of his chords, held where it repeats"""
    names = [CHORDS[b][voice] for b in range(53, 61)]
    return {b: [(n, 8, t)] for b, (n, t) in zip(range(53, 61), held(names))}


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    out.append(('P13', 1, 48, 1.0, {48: [('E4', 4, None)], 49: [('C4', 8, None)], 50: [('B3', 4, None), ('D4', 4, None)],
                                    51: [('B3', 8, None)], 52: [('C#4', 4, None), (None, 4, None)]}))
    out.append(('P9', 1, 48, 1.0, {48: [('G4', 4, None)], 49: [('E4', 8, 'start')], 50: [('E4', 4, 'stop'), ('G4', 4, None)], 51: [('E4', 8, 'start')],
                                   52: [('E4', 4, 'stop'), (None, 4, None)], **pad(2)}))
    out.append(('P10', 1, 49, 0, {49: [('C4', 8, None)], 50: [('B3', 4, None), ('D4', 4, None)], 51: [('B3', 8, None)],
                                  52: [('C#4', 4, None), (None, 4, None)], **pad(1)}))
    out.append(('P11', 1, 49, 0, {49: [('F3', 8, None)], 50: [('G3', 8, None)], 51: [('E3', 8, None)], 52: [('A3', 8, None)], **pad(0)}))
    for pid, voice in (('P28', 2), ('P29', 1)):
        pulse = {b: [(CHORDS[b][voice] if (pid, b) != ('P29', 49) else 'C5', 2, None)] * 4 for b in (49, 50, 51)}
        pulse[52] = [(CHORDS[52][voice], 2, None)] * 2
        if pid == 'P29':
            pulse[52] = pulse[52] + [('C#5', 4, None)]
            pulse.update({b: [(octave(n, -1), d, t) for n, d, t in MELODY[b]] for b in range(53, 61)})
        out.append((pid, 1, 49, 0, pulse))
    runs = {b: [(n, 1, None) for n in RUNS[b].split()] for b in RUNS}
    out.append(('P2', 1, 49, 0, {**runs, 52: runs[52] + MELODY[52], **{b: MELODY[b] for b in range(53, 61)}}))
    out.append(('P1', 1, 49, 0, {**runs, 52: runs[52] + MELODY[52]}))
    out.append(('P3', 1, 52, 1.0, shift(MELODY, -1)))
    out.append(('P5', 1, 48, 1.0, {48: [('A5', 4, None)]}))
    out.append(('P4', 1, 53, 0, pad(1)))
    out.append(('P6', 1, 53, 0, pad(2)))
    out.append(('P7', 1, 48, 1.0, {48: LEAD_IN['P7'], **{b: [(n, 8, t)] for b, (n, t) in zip(BARS, held(BASS))}}))
    out.append(('P31', 1, 48, 1.0, {48: LEAD_IN['P31'], **{b: [(n, 2, None)] * 4 for b, n in zip(BARS, BASS)}}))
    out.append(('P32', 1, 48, 1.0, {48: LEAD_IN['P32'], **{b: [(octave(n, -1), 4, None)] * 2 for b, n in zip(BARS, BASS)}}))
    out.append(('P14', 1, 49, 0, {b: [(n, 4, None)] * 2 for b, n in zip(BARS, BASS)}))
    for pid in ('P15', 'P16'):
        out.append((pid, 1, 49, 0, {b: [(octave(n, -1), 4, None)] * 2 for b, n in zip(BARS, BASS)}))
    out.append(('P17', 1, 47, 0, {47: [('E2', 1, None)] * 8, 48: [('E2', 1, None)] * 8,
                                  **{b: [(n, 4, None), (n, 2, None), (n, 2, None)] for b, n in zip(BARS, TIMPANI)}}))
    return out


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        if b == 48 and pid in LEAD_IN:
            old = [ev for ev in p111326_s5.voice_one(x, pid, 48) if ev[0] < 4]
            x = write_bar(clear_bar(x, pid, 48), pid, 48, [(name_of(p111326_s5.concert_of(x, pid, old[0][3])), 4, 'stop')] + events)
        elif b == 48 and onset and pid in ('P9', 'P5'):
            old = [ev for ev in p111326_s5.voice_one(x, pid, 48)]
            first = name_of(p111326_s5.concert_of(x, pid, old[0][3]))
            x = write_bar(clear_bar(x, pid, 48), pid, 48, [(first, 4, None)] + events)
        elif b == 52 and pid in ('P28',):
            s0, s1 = measure_span(x, pid, 52)
            notes = [m for m in re.finditer(r'<note[ >].*?</note>', x[s0:s1], re.S)]
            first = notes[0]
            assert '<rest' in first.group(0), 'Violin I bar 52 should start with a rest'
            x = x[:s0 + first.start()] + bar_events(x, pid, events) + x[s0 + first.end():]
        else:
            x = write_bar(x, pid, b, ([(None, int(onset * 4), None)] if b == bar and onset else []) + events)
    return x


def bar_events(x, pid, events):
    """notes in Dorico's encoding for part of a bar (write_bar needs a whole empty bar)"""
    tmp = write_bar(EMPTY_BAR, 'P1', 1, events)
    return ''.join(m.group(0) for m in re.finditer(r'<note[ >].*?</note>', tmp, re.S))


EMPTY_BAR = ('<part-list><score-part id="P1"><part-name>x</part-name></score-part></part-list><part id="P1"><measure number="1">'
             '<attributes><divisions>4</divisions><key><fifths>0</fifths></key></attributes>'
             '<note><rest/><duration>8</duration><voice>1</voice><type>whole</type><staff>1</staff></note></measure></part>')


def respell_56(x):
    """his D flat 6 in bar 56 is the C sharp of his chord there"""
    s0, s1 = measure_span(x, 'P28', 56)
    body = x[s0:s1]
    new = re.sub(r'<step>D</step>\s*<alter>-1</alter>', '<step>C</step><alter>1</alter>', body, count=1)
    new = re.sub(r'<accidental>flat</accidental>', '<accidental>sharp</accidental>', new, count=1)
    return x[:s0] + new + x[s1:]


def harp_48(x):
    """the harp's G sharp on beat 2 of bar 48 becomes G natural, the note of his trumpet's pickup"""
    s0, s1 = measure_span(x, 'P26', 48)
    body = x[s0:s1]
    new = re.sub(r'(<step>G</step>)\s*<alter>1</alter>(\s*<octave>5</octave>)', r'\1\2', body, count=1)
    new = new.replace('<accidental>sharp</accidental>', '<accidental>natural</accidental>', 1) if new != body else new
    assert new != body, 'no G sharp 5 in the harp in bar 48'
    return x[:s0] + new + x[s1:]


def viola_49(x):
    """his viola chord in bar 49 without its F4, which rubs against the trumpet's E4 (the F stays in the bass)"""
    s0, s1 = measure_span(x, 'P30', 49)
    body = x[s0:s1]
    new = re.sub(r'<note><chord/><pitch><step>F</step><octave>4</octave></pitch>.*?</note>', '', body, count=1, flags=re.S)
    if new == body:
        new = re.sub(r'<note>\s*<chord/>\s*<pitch>\s*<step>F</step>\s*<octave>4</octave>\s*</pitch>.*?</note>', '', body, count=1, flags=re.S)
    assert new != body, 'no F4 in the viola chord of bar 49'
    return x[:s0] + new + x[s1:]


def notes(x):
    for line in lines():
        x = write_line(x, line)
    return s14.harp(viola_49(harp_48(respell_56(x))))


def build(x):
    y = rebeam(notes(x))
    for pid in ('P28', 'P29', 'P31'):
        y = beam_eighths(y, pid, range(49, 53) if pid != 'P31' else BARS)
    for pid in ('P2', 'P1', 'P17'):
        for b in range(47, 53):
            y = beam16(y, pid, b)
    for pid in LEAD_IN:
        y = beam16(y, pid, 48)
    m = Marks(y)
    for pid, bar in s14.RAMP.items():
        m.hairpin(pid, (bar, 0), (49, 0), 'crescendo')
    m.dynamic('P17', 47, 0, 'p')
    m.hairpin('P17', (47, 0), (48, 1.75), 'crescendo')
    for pid in ('P12', 'P13'):
        m.dynamic(pid, 48, 1.0, 'f')
        for a, z in BRASS_SLURS:
            m.slur(pid, a, z)
    for pid in ('P9', 'P10'):
        m.dynamic(pid, 49, 0, 'f')
        m.slur(pid, *BRASS_SLURS[1])
    for pid in ('P28', 'P29', 'P30'):
        m.dynamic(pid, 49, 0, 'mf')
    for pid in ('P2', 'P1'):
        m.dynamic(pid, 49, 0, 'f')
        for a, z in RUN_SLURS:
            m.slur(pid, a, z)
    for pid in ('P28', 'P29', 'P2', 'P3'):
        m.dynamic(pid, 52, 1.0, 'ff' if pid in ('P28', 'P29') else 'f')
        for a, z in MELODY_SLURS:
            m.slur(pid, a, z)
    for pid in ('P11', 'P7', 'P31', 'P32', 'P14', 'P15', 'P16', 'P17'):
        m.dynamic(pid, 49, 0, 'f')
    for pid in PAD_PARTS + ('P7', 'P31', 'P32', 'P14', 'P15', 'P16', 'P17', 'P30'):
        m.dynamic(pid, 53, 0, 'mf')
    m.slur('P7', (48, 1.0), (49, 0))
    for line in lines():
        if line[0] in PAD_PARTS:
            for a, z in ((53, 56), (57, 60)):
                starts = [b for b in range(a, z + 1) for n, d, t in line[4].get(b, [])[:1] if n and t not in ('stop', 'both')]
                if len(starts) > 1:
                    m.slur(line[0], (starts[0], 0), (starts[-1], 0))
    for pid in ACCENTS:
        for b in BARS:
            for o in (0, 1.0):
                m.articulation(pid, b, o, 'accent')
    m.dynamic('P26', 49, 0, 'f')
    return m.text()


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
