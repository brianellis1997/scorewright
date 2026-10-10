"""Where I Left It, S7: S5's tune and harmony (his E minor sketch), concert pitch, with the piano
rewritten from reading his song studies as pages (the engraved PDFs, read as a musician reads
them), not from measurements. What the pages show and what S7 does with it:

- space: in no 3 the piano plays a short bass arpeggio at the start of the bar, a two-note
  rising sigh in the right hand, and rests; the voice floats. Verse, first pass: the same.
- complementary motion: in no 1 the piano moves when the oboe holds and simplifies when it
  moves. Verse, second pass: the right hand has a short counter-line under each held note and
  holds under the moving notes; the bass sustains.
- doubling is earned: in no 8 the piano doubles the theme an octave up only when it returns,
  with the left hand turned to flowing arpeggios. Verse, third pass: the nocturne left hand,
  the tune an octave below in the right.
- the piano gets its own phrase: in no 8 the piano answers the horn alone in parallel thirds
  over rocking octaves. Two new bars after "holding its breath": the voice stops, the chord
  stops, and the piano answers in thirds over the held dominant.
- the chorus changes texture once, as no 3 does at "we used to": the hands trade
  triplet-sixteenth arpeggios with rests between, each right-hand wave falling away as his do; the second time through, the right hand
  doubles the voice an octave below over the same left hand, then thins to "home".
usage (whisperer env): python lab/songs/where_i_left_it_s7.py"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import syllables, V1, CH  # noqa: E402
from where_i_left_it_s3 import eh_bar  # noqa: E402
import where_i_left_it_s5 as s5  # noqa: E402
import where_i_left_it_s6 as s6  # noqa: E402

LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it_s7'
WORDS = syllables(V1) + syllables(CH)

eh = [b['eh'] for _, sec in s5.SECTIONS for b in sec]
eh[19] = '!<)! !>(! A4/8 ) !>)! z/8'
EH = eh[:20] + ['z/16', 'z/12 !p! ( C5/2 D5/2'] + eh[20:]


def arp(lh, rh):
    """the chorus figure for one half bar: a rising bass arpeggio on the beat, the right hand's
    up-and-down answer a beat later"""
    a, b, c = lh.split()
    r1, r2, r3, r4 = rh.split()
    return (f'(3 {a}/1 {b}/1 {c}/1 z2 z4', f'z2 !>(! (3 {r1}/1 {r2}/1 {r3}/1 (3 {r4}/1 {r3}/1 {r2}/1 !>)! z2')


CH_CHORDS = {'Em': ('E2 B2 E3', 'G3 B3 E4 G4'), 'Am7': ('A1 E2 A2', 'G3 C4 E4 G4'), 'D7': ('D2 A2 D3', 'F#3 A3 C4 D4'),
             'Gmaj7': ('G1 D2 G2', 'F#3 B3 D4 F#4'), 'Cmaj7': ('C2 G2 C3', 'E3 G3 B3 E4'), 'F#o7': ('F#1 C2 F#2', 'E3 A3 C4 E4'),
             'B7': ('B1 F#2 B2', 'D#3 F#3 A3 B3')}


def chorus_bar(ch, rh=None):
    l, r = arp(*CH_CHORDS[ch])
    return (rh if rh is not None else r + ' ' + r), l + ' ' + l


PIANO = [  # (right hand, left hand, dynamic)
    # intro: the tune in the right hand, a short arpeggio and space in the left
    ('G4/8 A4/4 B4/4', 'E2/2 B2/2 G3/2 z2 z8', '!p!'),
    ('E5/8 C5/4 z4', 'F#2/2 C3/2 A3/2 z2 z8', None),
    ('B4/8 A4/4 A4/4', 'B1/2 F#2/2 D#3/2 z2 z8', None),
    ('G4/8 z4 z4', 'E2/2 B2/2 G3/2 z2 z8', None),
    # verse 1, first pass: space, the rising sigh of no 3
    ('z6 B3/2 E4/8', 'E2/2 B2/2 G3/2 z2 z8', None),
    ('z6 E3/2 A3/8', 'F#2/2 C3/2 A3/2 z2 z8', None),
    ('z6 F#3/2 A3/8', 'B1/2 F#2/2 D#3/2 z2 z8', None),
    ('z8 (3 B4/2 A4/2 G4/2 z4', 'E2/2 B2/2 G3/2 z2 z8', None),
    # second pass: a counter-line under the held notes, held under the moving ones
    ('B3/2 C4/2 B3/2 A3/2 G3/8', '[E2 B2]16', None),
    ('A3/2 C4/2 E4/2 C4/2 A3/8', '[A1 E2]16', None),
    ('[F#3 A3]16', '[D#2 A2]16', None),
    ('B3/2 G3/2 E3/2 G3/2 (3 B3/2 C4/2 D4/2 E4/4', '[E2 B2]16', None),
    # third pass: the nocturne left hand, the tune an octave below
    ('B3/8 C4/4 D4/4', 'E2/2 B2/2 E3/2 G3/2 B3/2 G3/2 E3/2 B2/2', '!mp!'),
    ('E4/8 (3 C4/2 E4/2 A4/2 C4/2 E4/2', 'F#2/2 C3/2 E3/2 A3/2 C4/2 A3/2 E3/2 C3/2', None),
    ('F#4/8 E4/4 D#4/4', 'B1/2 F#2/2 A2/2 D#3/2 F#3/2 D#3/2 A2/2 F#2/2', None),
    ('E4/8 (3 G4/2 F#4/2 E4/2 D4/2 C4/2', 'E2/2 B2/2 E3/2 G3/2 B3/2 G3/2 E3/2 B2/2', None),
    # fourth pass: thinning to the held breath; the chord stops with the voice
    ('[G3 B3]16', '[E1 E2]16', '!p!'),
    ('[A3 C4]8 (3 E4/2 C4/2 A3/2 z4', '[F#1 F#2]16', None),
    ('[A3 D#4]16', '[B1 F#2]16', None),
    ('[A3 D#4]8 z8', '[B1 F#2]8 z8', None),
    # the piano answers alone in thirds over rocking octaves (no 8)
    ('[D#4 F#4]4 [E4 G4]4 [F#4 A4]8', 'B1/4 B2/4 B1/4 B2/4', '!p!'),
    ('[G4 B4]8 [F#4 A4]4 z4', 'B1/4 B2/4 B1/4 z4', None),
]
CH_SEQ = ['Em', 'Am7', 'D7', 'Gmaj7', 'Cmaj7', 'F#o7', 'B7', 'Em']
for i, c in enumerate(CH_SEQ):
    r, l = chorus_bar(c)
    PIANO.append((r, l, '!mp!' if i == 0 else None))
DOUBLE = ['E4/8 D4/4 C4/4', 'C4/8 B3/2 z2 B3/4', 'F#4/8 E4/4 C4/4', 'B3/8 (3 D4/2 F#4/2 A4/2 B3/2 C4/2',
          'E4/8 D4/4 C4/4', 'C4/8 (3 C5/2 B4/2 A4/2 (3 G4/2 F#4/2 E4/2', 'D#4/4 [F#4 A4]4 [F#4 A4]8',
          '[E4 G4 B4]12 (3 B4/2 A4/2 G4/2']
for i, (c, d) in enumerate(zip(CH_SEQ, DOUBLE)):
    r, l = chorus_bar(c, d)
    if i >= 6:
        l = {'B7': '[B1 F#2]16', 'Em': '[E1 E2]16'}[c]
    PIANO.append((r, l, '!mf!' if i == 0 else ('!p!' if i == 6 else None)))
assert len(PIANO) == len(EH) == 38, (len(PIANO), len(EH))


def lh_bar(spec, ped):
    s = s6.rh_bar(spec, None, {})
    i = 2 if s.startswith('(3') else 0
    tag = '!ped-up!!ped!' if ped['on'] else '!ped!'
    ped['on'] = True
    return s[:i] + tag + s[i:]


def build():
    bars = []
    carry, ped = dict(tied=False), dict(on=False)
    for e, (r, l, d) in zip(EH, PIANO):
        b = dict(eh=e)
        b['eh_abc'], b['kinds'] = eh_bar(e, carry, key='G', transpose=False)
        b['rh_abc'] = s6.rh_bar(r, d, {})
        b['lh_abc'] = lh_bar(l, ped)
        bars.append(b)
    return bars


if __name__ == '__main__':
    bars = build()
    s6.NAME = NAME
    out, log = s6.convert(s6.to_abc(bars))
    print(f'{len(bars)} bars, {len(WORDS)} syllables -> {out}')
    if log:
        print(log[-1500:])
