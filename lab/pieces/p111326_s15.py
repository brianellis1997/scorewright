"""111326 S15 (Nov 14 2026): the climax again, after Brian's notes on S14: "I don't like the harmony,
I don't think we have that second chord... all the rhythm just stops, it becomes this tutti with no
rhythmic involvement... the rhythm should be pounded through string runs or percussion or wind
runs... the winds should be running... the winds really cannot compete with the heavy brass and the
high strings... the horns, the trumpets should be leading here, maybe some strings... the cor
anglais is not going to be heard, the clarinet is not going to be heard... the lower wind
instruments should be contributing to the harmony... everything is static half notes... this
fortissimo again is coming out of nowhere... the violin going up from that B to E hasn't occurred".
- Harmony: F/C, A7/C sharp (it replaces C sharp-F-A, so the melody's E and G are in the chord), Dm,
  E7/D, Am/E, D7/F sharp, E7/G sharp, Am.
- The melody leads in the brass: horn 1 and trumpet 1 together, horn 2 and trumpet 2 a third below,
  at E4 to G4 (not the trumpets' top register); Violin I and the piccolo two octaves up, Violin II
  one octave up; the oboe a third below Violin II.
- The flute and the E flat clarinet run in sixteenths over each chord (down and up the chord).
- The cor anglais, B flat clarinet, bassoon and Wagner tuba hold the harmony (the lower winds).
- Rhythm: violas in eighths between two chord tones, cellos in eighths on the bass, double basses,
  trombones and tuba in accented quarters on the bass, the timpani on A and E (quarter, two eighths).
- The lead-in: the timpani roll on E in bars 47-48 and grow; the trumpets warm up in bar 47 and play
  the G that falls to the E; on beat 2 of bar 48 the flute and violins run B, C, D up to the E.
  Horns, clarinets, violas, low strings, bassoon and trombones grow through bars 46-48 (S14).
- The harp ends its run with one F chord on bar 49 (it is not heard in the tutti). At bar 56 the
  rhythm stops on beat 1 and the melody holds the A, with a diminuendo from bar 53.
usage (whisperer env): python lab/pieces/p111326_s15.py <working.xml (S12)> <out.xml>"""
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
          53: [('E4', 2, None), ('D4', 6, None)], 54: [('C4', 8, None)], 55: [('B3', 8, None)], 56: [('A3', 8, None)]}
SECOND = {49: [('C4', 8, None)], 50: [('C#4', 4, None), ('E4', 4, None)], 51: [('C4', 8, None)], 52: [('B3', 4, None), ('E4', 4, None)],
          53: [('C4', 2, None), ('B3', 6, None)], 54: [('A3', 8, None)], 55: [('G#3', 8, None)], 56: [('E3', 8, None)]}
RUNS = {49: 'E6 C6 A5 F5 C5 F5 A5 C6', 50: 'E6 C#6 A5 G5 E5 G5 A5 C#6', 51: 'F6 D6 A5 F5 D5 F5 A5 D6', 52: 'E6 D6 B5 G#5 E5 G#5 B5 D6',
        53: 'E6 C6 A5 E5 A5 C6 E6 A6', 54: 'F#6 D6 C6 A5 F#5 A5 C6 D6', 55: 'E6 D6 B5 G#5 E5 G#5 B5 D6', 56: 'E6 C6 A5 E5'}
CHORDS = ['F/C', 'A7/C#', 'Dm', 'E7/D', 'Am/E', 'D7/F#', 'E7/G#', 'Am']
PAD = {'P4': ['F4', 'G4', 'F4', 'G#4', 'A4', 'A4', 'G#4', 'A4'], 'P6': ['C4', 'E4', 'D4', 'D4', 'C4', 'C4', 'D4', 'C4'],
       'P7': ['A3', 'A3', 'A3', 'B3', 'A3', 'A3', 'B3', 'A3'], 'P11': ['A3', 'A3', 'A3', 'B3', 'A3', 'A3', 'B3', 'A3']}
BASS = ['C3', 'C#3', 'D3', 'D3', 'E3', 'F#3', 'G#3', 'A3']
VIOLA = [('A3', 'C4'), ('G3', 'C#4'), ('A3', 'D4'), ('B3', 'D4'), ('A3', 'C4'), ('A3', 'C4'), ('B3', 'D4')]
TIMPANI = ['A2', 'A2', 'A2', 'E2', 'E2', 'A2', 'E2']
LEAD_IN = {'P2': 1, 'P28': 1, 'P29': 0}
BRASS = ('P9', 'P10', 'P11', 'P12', 'P13', 'P14', 'P15', 'P16')
MELODY_PARTS = ('P9', 'P10', 'P12', 'P13', 'P28', 'P29', 'P3', 'P1')
RUN_PARTS = ('P2', 'P5')
ACCENTS = ('P14', 'P15', 'P16')
DIM = ((53, 0), (56, 0))
MELODY_SLURS = [((50, 1.0), (52, 0)), ((52, 1.0), (56, 0))]
RUN_SLURS = [((49, 0), (50, 1.75)), ((51, 0), (52, 1.75)), ((53, 0), (54, 1.75)), ((55, 0), (56, 0.75))]


def shift(events, k):
    return {b: [(octave(n, k), d, t) for n, d, t in ev] for b, ev in events.items()}


def lead_in(k):
    """beat 2 of bar 48: B (eighth), C, D (sixteenths) up to the E of bar 49"""
    return [(octave('B4', k), 2, None), (octave('C5', k), 1, None), (octave('D5', k), 1, None)]


def lines():
    """(pid, staff, first bar, onset, {bar: [(name, divisions, tie)]}), in the order Dorico gets them"""
    out = []
    melody = {'P9': shift(MELODY, 0), 'P10': shift(SECOND, 0),
              'P12': {47: [('E4', 8, 'start')], 48: [('E4', 4, 'stop'), ('G4', 4, None)], **shift(MELODY, 0)},
              'P13': {47: [('B3', 8, 'start')], 48: [('B3', 4, 'stop'), ('E4', 4, None)], **shift(SECOND, 0), 56: [('C4', 8, None)]},
              'P28': {48: lead_in(1), **shift(MELODY, 2)}, 'P29': {48: lead_in(0), **shift(MELODY, 1)},
              'P3': {**shift(SECOND, 1), 56: [('E4', 8, None)]}, 'P1': shift(MELODY, 2)}
    for pid in MELODY_PARTS:
        bars = melody[pid]
        first = min(bars)
        out.append((pid, 1, first, 1.0 if pid in LEAD_IN else 0, bars))
    runs = {b: [(n, 1, None) for n in RUNS[b].split()] + ([('A5', 4, None)] if b == 56 else []) for b in BARS}
    out.append(('P2', 1, 48, 1.0, {48: lead_in(1), **runs}))
    out.append(('P5', 1, 49, 0, runs))
    for pid, names in PAD.items():
        out.append((pid, 1, 49, 0, {b: [(n, 8, t)] for b, (n, t) in zip(BARS, held(names))}))
    stop = lambda name: [(name, 4, None), (None, 4, None)]
    out.append(('P30', 1, 49, 0, {**{b: [(a, 2, None), (c, 2, None), (a, 2, None), (c, 2, None)] for b, (a, c) in zip(BARS, VIOLA)}, 56: stop('A3')}))
    out.append(('P31', 1, 49, 0, {**{b: [(n, 2, None)] * 4 for b, n in zip(BARS, BASS[:7])}, 56: stop('A2')}))
    out.append(('P32', 1, 49, 0, {**{b: [(octave(n, -1), 4, None)] * 2 for b, n in zip(BARS, BASS[:7])}, 56: stop('A1')}))
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
            keep = [(name_of(x, pid, n), 2, None) for t, s, e, n in old]
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
    for line in lines():
        pid = line[0]
        m.dynamic(pid, 49, 0, 'f' if pid in BRASS + ('P17',) else 'ff')
        if pid in MELODY_PARTS:
            if pid in ('P12', 'P13', 'P28', 'P29'):
                m.slur(pid, (48, 1.0), (49, 0))
            for a, z in MELODY_SLURS:
                m.slur(pid, a, z)
            m.hairpin(pid, *DIM, 'diminuendo')
        elif pid in RUN_PARTS:
            slurs = [((48, 1.0), (50, 1.75))] + RUN_SLURS[1:] if pid == 'P2' else RUN_SLURS
            for a, z in slurs:
                m.slur(pid, a, z)
            m.hairpin(pid, *DIM, 'diminuendo')
        elif pid in PAD:
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
