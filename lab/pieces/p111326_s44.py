"""111326 S44 (Nov 25 2026), Brian, after S43: "I've continued a bit of it, this time the violins taking over
the oboe... let the oboe dovetail a bit more into that violin line, it can just hold the E for an eighth, no
longer... I filled in harmony in the viola line... maybe lower, more spread out... I definitely want the first
violins taking the melody, maybe doubled with flutes... that line [his Violin II run]... seems like a wind
line... the clarinet might be good... keep the texture we're building here, keep the instruments going, we're
only adding new instruments". Builds on his export of Nov 25, 08:55 (his Violin I of bars 128-134, his Violin
II run of bars 131-134, his viola chords A, Dm, G7 over B, F, C, F, G7 over B).
- Melody: Violin I as he wrote it, doubled by the flute in unison, mp; the third time (bars 133-134) the
  piccolo joins an octave up and the three go mf.
- His run moves to the clarinet, mp, which keeps its off-beats until the run starts; Violin II goes on with
  its held line.
- His chords, spread an octave lower: Violin II holds the top note (E F F F E F F), the violas the middle
  (C sharp D D C C C B); the trombone and Wagner tuba double them an octave down and the bass trombone holds
  the bass (A D G F A F G), all slurred in from their notes of bar 127, p.
- The pulse goes on: harp off-beat chords, bassoon off-beats, the pizzicato basses and contrabassoon on both
  beats; the cellos answer where the melody holds (bars 129, 131, 133).
- The oboe holds its E an eighth into the violins' entry (bar 128).
usage (whisperer env): python lab/pieces/p111326_s44.py <export.xml> <out.xml>"""
import os, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import octave, put  # noqa: E402
from p111326_s15 import beam16  # noqa: E402
import p111326_s43 as s43  # noqa: E402
from dorico_plan import Score  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
p111326_s5.TYPE.setdefault(3, ('eighth', 1))
H = Fraction(1, 2)
Q4 = Fraction(1, 4)
BARS = range(128, 135)
CHORDS = {128: ['E5', 'C#5', 'A4'], 129: ['F5', 'D5', 'A4'], 130: ['F5', 'D5', 'B4'], 131: ['F5', 'C5'], 132: ['E5', 'C5'],
          133: ['F5', 'C5'], 134: ['F5', 'B4']}
TOP = dict(zip(BARS, ['E4', 'F4', 'F4', 'F4', 'E4', 'F4', 'F4']))
MID = dict(zip(BARS, ['C#4', 'D4', 'D4', 'C4', 'C4', 'C4', 'B3']))
BASS = dict(zip(BARS, ['A2', 'D2', 'G2', 'F2', 'A2', 'F2', 'G2']))
OFF = lambda a, b: [(None, 2, None), (a, 2, None), (None, 2, None), (b, 2, None)]
BASSOON = {128: OFF('C#3', 'E3'), 129: OFF('D3', 'F3'), 130: OFF('D3', 'F3'), 131: OFF('C3', 'F3'), 132: OFF('C3', 'E3'),
           133: OFF('C3', 'F3'), 134: OFF('B2', 'F3')}
HARP = {128: (['E4', 'A4'], ['A2']), 129: (['D4', 'F4', 'A4'], ['D3']), 130: (['D4', 'F4', 'G4'], ['G2']),
        131: (['C4', 'F4'], ['F2']), 132: (['C4', 'E4', 'A4'], ['A2']), 133: (['C4', 'F4'], ['F2']),
        134: (['D4', 'F4', 'G4'], ['G2'])}
CELLO = {129: [(None, 4), ('F3', 2), ('D3', 2)], 130: [('B2', 4), (None, 4)], 131: [(None, 4), ('A3', 2), ('G3', 2)],
         132: [('E3', 4), (None, 4)], 133: [(None, 4), ('A3', 2), ('G3', 2)], 134: [('F3', 4), (None, 4)]}
RUN_FROM = (131, Fraction(5, 4))


def tied(names):
    bars = sorted(names)
    out = {}
    for i, b in enumerate(bars):
        n = names[b]
        before = i > 0 and names[bars[i - 1]] == n
        after = i + 1 < len(bars) and names[bars[i + 1]] == n
        out[b] = [(n, 8, {(False, False): None, (True, False): 'stop', (False, True): 'start', (True, True): 'both'}[(before, after)])]
    return out


def his(x):
    """his Violin I melody and Violin II run, as events {bar: [(name, sixteenths)]}"""
    sc = Score(x)
    def evs(pid, bars):
        out = {}
        for b in bars:
            its = sc.items(pid, b)
            row = []
            for k, it in enumerate(its):
                end = its[k + 1][0] if k + 1 < len(its) else Fraction(2)
                row.append((None if it[1] == 'Rest' else it[1][0], int((end - it[0]) * 4), 'stop' if it[2] else ('start' if it[3] else None)))
            out[b] = row
        return out
    return evs('P28', BARS), evs('P29', range(131, 135))


def check(x):
    sc = Score(x)
    for b, names in CHORDS.items():
        (it,) = sc.items('P30', b)
        assert it[1] == names, (b, it[1])
    assert [it[1][0] for it in sc.items('P28', 128) if it[1] != 'Rest'] == ['C6']
    assert [it[1][0] for it in sc.items('P29', 131) if it[1] != 'Rest'] == ['B4', 'C5', 'D5']
    assert [(it[0], it[1][0], it[2]) for it in sc.items('P3', 128) if it[1] != 'Rest'] == [(0, 'E5', True)]
    for pid in ('P1', 'P2', 'P6', 'P7', 'P26', 'P31', 'P32', 'P8', 'P14', 'P11', 'P15'):
        for b in BARS:
            assert all(it[1] == 'Rest' for st in ((1, 2) if pid == 'P26' else (1,)) for it in sc.items(pid, b, st)), (pid, b)


def lines(x):
    melody, run = his(x)
    ls = {}
    ls['P2'] = {b: [(n, d, t) for n, d, t in evs] for b, evs in melody.items()}
    ls['P1'] = {b: [(octave(n, 1) if n else None, d, t) for n, d, t in melody[b]] for b in (133, 134)}
    clar = {128: OFF('E4', 'E4'), 129: OFF('F4', 'F4'), 130: OFF('F4', 'F4')}
    assert run[131][0] == (None, 4, None) and run[131][1][:2] == (None, 1), run[131]
    clar[131] = [(None, 2, None), ('F4', 2, None)] + run[131][1:]
    for b in (132, 133, 134):
        clar[b] = run[b]
    ls['P6'] = clar
    ls['P29'] = tied(TOP)
    ls['P30'] = tied(MID)
    ls['P14'] = tied({b: octave(n, -1) for b, n in MID.items()})
    ls['P11'] = tied({b: octave(n, -1) for b, n in TOP.items()})
    ls['P15'] = tied(BASS)
    ls['P7'] = dict(BASSOON)
    ls['P31'] = {b: [(n, d, None) for n, d in evs] for b, evs in CELLO.items()}
    for pid in ('P32', 'P8'):
        ls[pid] = {b: [(BASS[b], 4, None), (BASS[b], 4, None)] for b in BARS}
    return ls


def oboe_held(x):
    """the oboe's tied E ends an eighth later: bar 128 E (dotted quarter, tie end), an eighth rest"""
    return put(x, 'P3', 128, [('E5', 6, 'stop'), (None, 2, None)])


def harp_events(bar, staff):
    rh, lh = HARP[bar]
    names = rh if staff == 1 else lh
    return [(None, 2), (names, 2), (None, 2), (names, 2)]


def notes(x):
    check(x)
    ls = lines(x)
    for b in BARS:
        x = put(x, 'P30', b, [(None, 8, None)])
    for b in range(131, 135):
        x = put(x, 'P29', b, [(None, 8, None)])
    for pid, bars in ls.items():
        for b, evs in bars.items():
            x = put(x, pid, b, list(evs))
    x = oboe_held(x)
    saved = s43.HARP, s43.harp_events
    s43.HARP, s43.harp_events = {b: (r, l, 2) for b, (r, l) in HARP.items()}, harp_events
    try:
        for b in HARP:
            x = s43.harp_bar(x, b)
    finally:
        s43.HARP, s43.harp_events = saved
    for pid in ('P2', 'P1', 'P31', 'P7'):
        x = beam_eighths(x, pid, BARS)
    for b in range(131, 135):
        x = beam16(x, 'P6', b)
    return x


SLURS = {'P2': [((128, 1), (130, 1)), ((131, 0), (132, 1)), ((133, 0), (134, 1))], 'P1': [((133, 0), (134, 1))],
         'P6': [(RUN_FROM, (132, Fraction(7, 4))), ((133, Fraction(5, 4)), (134, Fraction(7, 4)))],
         'P31': [((129, 1), (130, 0)), ((131, 1), (132, 0)), ((133, 1), (134, 0))]}
INTO_128 = ('P14', 'P11', 'P15')


def build(x):
    y = notes(x)
    m = Marks(y)
    for pid, sl in SLURS.items():
        for a, z in sl:
            m.slur(pid, a, z)
    sc = Score(y)
    for pid in INTO_128:
        m.slur(pid, sc.chain_start(pid, 127, 0), (128, 0), number=2)
    for pid in ('P28', 'P2'):
        m.dynamic(pid, 128, 1, 'mp')
        m.dynamic(pid, 133, 0, 'mf')
    m.dynamic('P1', 133, 0, 'mf')
    m.dynamic('P6', *RUN_FROM, 'mp')
    m.dynamic('P31', 129, 1, 'p')
    for b in BARS:
        for o in (H, 3 * H):
            m.articulation('P7', b, o, 'staccato')
    for b in (128, 129, 130):
        for o in (H, 3 * H):
            m.articulation('P6', b, o, 'staccato')
    m.articulation('P6', 131, H, 'staccato')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
