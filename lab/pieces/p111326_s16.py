"""111326 S16 (Nov 14 2026): the climax again, after Brian's notes on S15: "the clarinet is way
too high in its register, the flute is in the right register; however they are interrupting with
the melody... make sure the runs are complementing the melody, not stepping on top of it... runs
don't have to be just broken chords, they can be chromatic at times... like Tchaikovsky... some
dynamics do come out of nowhere... the harmony still not right: definitely F major... F major to G
major to E minor... then slide to A major... then D minor, G7, E minor again, falling fifths".
- Harmony: F, G, Em, A7, Dm, G7, Em, Am (his falling fifths after F and G); bass F G E A D G E A.
- Melody: horn 1 and trumpet 1 at E4 to G4, horn 2 and trumpet 2 a third or a sixth below; Violin I
  an octave up, Violin II a third or sixth below it. Bar 54 is C to B over G7, and the B holds
  into E minor.
- Runs: flute and piccolo in sixteenths on scales with chromatic passing notes (F sharp, D sharp,
  C sharp, B flat, G sharp), always above the violins' top note, so they never cross the melody.
- The E flat clarinet resolves its G sharp to A on bar 49 and stops; the oboe ends with the theme.
- Held chords below the melody: cor anglais (C4 to D4), B flat clarinet and Wagner tuba (G3, A3),
  bassoon (D3 to F3).
- Lead-ins on the last beat of bar 48: Violin I falls B, A, G, F to the E; Violin II rises G, A, B
  to the C; cellos, bassoon and basses rise C, D, E to the F. The timpani roll and the trumpets'
  warm-up and G stay. New instruments enter f; the strings, which were playing, go to ff.
- Rhythm: violas and cellos in eighths, basses, trombones and tuba in accented quarters, timpani
  on A, D and E.
usage (whisperer env): python lab/pieces/p111326_s16.py <working.xml (S12)> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span, rebeam  # noqa: E402
import p111326_s5  # noqa: E402
from p111326_s5 import write_bar  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import clear_bar, held, octave  # noqa: E402
from xml_marks import Marks  # noqa: E402
import p111326_s14 as s14  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
BARS = range(49, 57)
MELODY = {49: [('E4', 8, 'start')], 50: [('E4', 4, 'stop'), ('G4', 4, None)], 51: [('E4', 8, 'start')], 52: [('E4', 4, 'stop'), ('G4', 4, None)],
          53: [('E4', 2, None), ('D4', 6, None)], 54: [('C4', 4, None), ('B3', 4, 'start')], 55: [('B3', 8, 'stop')], 56: [('A3', 8, None)]}
SECOND = {49: [('C4', 8, None)], 50: [('G3', 4, None), ('B3', 4, None)], 51: [('G3', 8, None)], 52: [('C#4', 4, None), ('E4', 4, None)],
          53: [('C4', 2, None), ('A3', 6, None)], 54: [('A3', 4, None), ('G3', 4, 'start')], 55: [('G3', 8, 'stop')], 56: [('E3', 8, None)]}
RUNS = {49: 'A5 Bb5 C6 D6 E6 F6 F#6 G6', 50: 'A6 G6 F#6 F6 E6 D6 C6 B5', 51: 'A5 B5 C6 D6 D#6 E6 F#6 G6', 52: 'A6 G6 F6 E6 D6 C#6 Bb5 A5',
        53: 'Bb5 C6 D6 E6 F6 G6 G#6 A6', 54: 'G6 F6 E6 D6 C6 B5 A5 G#5', 55: 'A5 B5 C6 D6 D#6 E6 F#6 G6', 56: 'G#6 A6 E6 C6'}
CHORDS = ['F', 'G', 'Em', 'A7', 'Dm', 'G7', 'Em', 'Am']
PAD = {'P4': ['C4', 'B3', 'B3', 'C#4', 'D4', 'B3', 'B3', 'C4'], 'P6': ['A3', 'G3', 'G3', 'A3', 'A3', 'G3', 'G3', 'A3'],
       'P11': ['A3', 'G3', 'G3', 'A3', 'A3', 'G3', 'G3', 'A3'], 'P7': ['F3', 'D3', 'E3', 'E3', 'F3', 'F3', 'E3', 'E3']}
BASS = ['F3', 'G3', 'E3', 'A3', 'D3', 'G3', 'E3', 'A3']
VIOLA = [('A3', 'C4'), ('B3', 'D4'), ('B3', 'E4'), ('G3', 'C#4'), ('A3', 'D4'), ('B3', 'F4'), ('B3', 'E4')]
TIMPANI = ['A2', 'D3', 'E2', 'A2', 'D3', 'D3', 'E2']
LEAD_IN = {'P28': [('B5', 1, None), ('A5', 1, None), ('G5', 1, None), ('F5', 1, None)],
           'P29': [('G4', 2, None), ('A4', 1, None), ('B4', 1, None)],
           'P31': [('C3', 2, None), ('D3', 1, None), ('E3', 1, None)],
           'P7': [('C3', 2, None), ('D3', 1, None), ('E3', 1, None)],
           'P32': [('C2', 2, None), ('D2', 1, None), ('E2', 1, None)]}
BRASS = ('P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16')
MELODY_PARTS = ('P9', 'P10', 'P12', 'P13', 'P28', 'P29')
RUN_PARTS = ('P2', 'P1')
ACCENTS = ('P14', 'P15', 'P16')
DIM = ((53, 0), (56, 0))
MELODY_SLURS = [((50, 1.0), (52, 0)), ((52, 1.0), (56, 0))]
RUN_SLURS = [((49, 0), (50, 1.75)), ((51, 0), (52, 1.75)), ((53, 0), (54, 1.75)), ((55, 0), (56, 0.75))]


def shift(events, k):
    return {b: [(octave(n, k), d, t) for n, d, t in ev] for b, ev in events.items()}


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    melody = {'P9': shift(MELODY, 0), 'P10': shift(SECOND, 0),
              'P12': {47: [('E4', 8, 'start')], 48: [('E4', 4, 'stop'), ('G4', 4, None)], **shift(MELODY, 0)},
              'P13': {47: [('B3', 8, 'start')], 48: [('B3', 4, 'stop'), ('E4', 4, None)], **shift(SECOND, 0), 56: [('C4', 8, None)]},
              'P28': {48: LEAD_IN['P28'], **shift(MELODY, 1)}, 'P29': {48: LEAD_IN['P29'], **shift(SECOND, 1)}}
    for pid in MELODY_PARTS:
        bars = melody[pid]
        first = min(bars)
        out.append((pid, 1, first, 1.0 if pid in LEAD_IN else 0, bars))
    runs = {b: [(n, 1, None) for n in RUNS[b].split()] + ([('A5', 4, None)] if b == 56 else []) for b in BARS}
    for pid in RUN_PARTS:
        out.append((pid, 1, 49, 0, runs))
    out.append(('P5', 1, 49, 0, {49: [('A5', 4, None), (None, 4, None)]}))
    for pid, names in PAD.items():
        bars = {b: [(n, 8, t)] for b, (n, t) in zip(BARS, held(names))}
        out.append((pid, 1, 48, 1.0, {48: LEAD_IN['P7'], **bars}) if pid == 'P7' else (pid, 1, 49, 0, bars))
    stop = lambda name: [(name, 4, None), (None, 4, None)]
    out.append(('P30', 1, 49, 0, {**{b: [(a, 2, None), (c, 2, None), (a, 2, None), (c, 2, None)] for b, (a, c) in zip(BARS, VIOLA)}, 56: stop('A3')}))
    out.append(('P31', 1, 48, 1.0, {48: LEAD_IN['P31'], **{b: [(n, 2, None)] * 4 for b, n in zip(BARS, BASS[:7])}, 56: stop('A2')}))
    out.append(('P32', 1, 48, 1.0, {48: LEAD_IN['P32'], **{b: [(octave(n, -1), 4, None)] * 2 for b, n in zip(BARS, BASS[:7])}, 56: stop('A1')}))
    out.append(('P14', 1, 49, 0, {**{b: [(n, 4, None)] * 2 for b, n in zip(BARS, BASS[:7])}, 56: stop('A3')}))
    for pid in ('P15', 'P16'):
        out.append((pid, 1, 49, 0, {**{b: [(octave(n, -1), 4, None)] * 2 for b, n in zip(BARS, BASS[:7])}, 56: stop('A2')}))
    out.append(('P17', 1, 47, 0, {47: [('E2', 1, None)] * 8, 48: [('E2', 1, None)] * 8,
                                  **{b: [(n, 4, None), (n, 2, None), (n, 2, None)] for b, n in zip(BARS, TIMPANI)}, 56: stop('A2')}))
    return out


def beam16(x, pid, bar):
    """sixteenths in groups of four get two beams (Dorico beams them itself; this is for the picture)"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    notes = list(re.finditer(r'<note[ >].*?</note>', body, re.S))
    t, groups, cur = 0, [], []
    for m in notes:
        n = m.group(0)
        d = int(re.search(r'<duration>(\d+)</duration>', n).group(1))
        if '<type>16th</type>' in n and '<rest' not in n and (not cur or t // 4 == cur[0][1] // 4):
            cur.append((m, t))
        else:
            if len(cur) > 1:
                groups.append(cur)
            cur = [(m, t)] if '<type>16th</type>' in n and '<rest' not in n else []
        t += d
    if len(cur) > 1:
        groups.append(cur)
    edits = []
    for g in groups:
        for i, (m, _) in enumerate(g):
            kind = 'begin' if i == 0 else 'end' if i == len(g) - 1 else 'continue'
            edits.append((m.start(), m.end(), m.group(0).replace('</staff>', f'</staff><beam number="1">{kind}</beam><beam number="2">{kind}</beam>', 1)))
    for a, z, new in reversed(edits):
        body = body[:a] + new + body[z:]
    return x[:s0] + body + x[s1:]


def write_line(x, line):
    pid, staff, bar, onset, bars = line
    for b, events in bars.items():
        if b == 48 and pid in LEAD_IN:
            old = [ev for ev in p111326_s5.voice_one(x, pid, 48) if ev[0] < 4]
            if pid in ('P28', 'P29'):
                keep = [(name_of(x, pid, n), 2, None) for t, s, e, n in old]
            else:
                keep = [(name_of(x, pid, old[0][3]), 4, 'stop')]
            x = write_bar(clear_bar(x, pid, 48), pid, 48, keep + events)
        else:
            x = write_bar(x, pid, b, events)
    return x


def name_of(x, pid, note):
    from p111326_s10 import name_of as nm
    return nm(p111326_s5.concert_of(x, pid, note))


def notes(x):
    for line in lines():
        x = write_line(x, line)
    return s14.harp(x)


STRINGS = ('P28', 'P29', 'P30', 'P31', 'P32')
HARP_CHORD = (('F2', 'C3', 'F3'), ('A4', 'C5', 'F5'))
s14.HARP_CHORD = HARP_CHORD


def build(x):
    y = rebeam(notes(x))
    for pid in ('P30', 'P31'):
        y = beam_eighths(y, pid, BARS)
    for pid in RUN_PARTS + ('P17',):
        for b in range(47, 57):
            y = beam16(y, pid, b)
    for pid in LEAD_IN:
        y = beam16(y, pid, 48)
    m = Marks(y)
    for pid, bar in s14.RAMP.items():
        m.hairpin(pid, (bar, 0), (49, 0), 'crescendo')
    m.dynamic('P17', 47, 0, 'p')
    m.hairpin('P17', (47, 0), (48, 1.75), 'crescendo')
    for pid in ('P12', 'P13'):
        m.dynamic(pid, 47, 0, 'mp')
        m.hairpin(pid, (47, 0), (48, 1.0), 'crescendo')
    for pid in ('P28', 'P29'):
        m.hairpin(pid, (48, 1.0), (49, 0), 'crescendo')
    for line in lines():
        pid = line[0]
        if pid == 'P5':
            continue
        m.dynamic(pid, 49, 0, 'ff' if pid in STRINGS else 'f')
        if pid in MELODY_PARTS:
            if pid in ('P12', 'P13', 'P28', 'P29'):
                m.slur(pid, (48, 1.0), (49, 0))
            for a, z in MELODY_SLURS:
                m.slur(pid, a, z)
            m.hairpin(pid, *DIM, 'diminuendo')
        elif pid in RUN_PARTS:
            for a, z in RUN_SLURS:
                m.slur(pid, a, z)
            m.hairpin(pid, *DIM, 'diminuendo')
        elif pid in PAD:
            if pid == 'P7':
                m.slur(pid, (48, 1.0), (49, 0))
            for a, z in s14.s13.pad_slurs(line):
                m.slur(pid, a, z)
        if pid in ACCENTS:
            for b in BARS:
                for o in ((0,) if b == 56 else (0, 1.0)):
                    m.articulation(pid, b, o, 'accent')
    m.dynamic('P26', 49, 0, 'f')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
