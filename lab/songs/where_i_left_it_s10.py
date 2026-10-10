"""Where I Left It, S10: the rest of the song after the accepted S9 (bars 1-37), from his
▶ continue on Oct 10 2026. Written after reading S9 as engraved pages, start to finish, and the
second halves of his Song Studies no 8 and no 12 (how he builds a return, a climax, an ending).

What the read of S9 gave, and where it goes:
- the verse tune (G A B | C) and its piano, the bass arpeggio with the rising sigh, are the song's
  "first notes". The bridge sets "but the first note came back" to exactly those notes over exactly
  that piano, and the last line "so I'll leave the light on" brings back the "light in the window"
  tune over the opening texture before the piano plays its intro once more.
- verse 1 had the relative major once (D7/F# to G). Verse 2 has the false resolution there
  (D7/F# to B minor, "C over B" leaning down), and its last line heads straight into the chorus
  with the piano silent under the pickup, "the quiet slipped out".
- the piano answers every breath (falling triplets, the thirds of bar 21); it keeps doing so.
- one figure per section, building: verse 2 rocks in eighths from the start (no 8, bar 38), the
  sigh in the right hand, then thirds under the tune; chorus 2 doubles the horn an octave below,
  then in thirds, and ends deceptively on C ("home" is not home yet); the bridge is a slow chorale
  over moving bass, then the opening, then the nocturne left hand into G (the relative major
  arrives once, on "knew"); the last chorus has octave basses and chords under the tune, peaks
  on "won't" (F#5, the song's ceiling, not higher), and thins to the opening.
- the ending is his: a ritardando in real tempo steps, the tune in the piano, the horn holding a
  soft note over the last chord (no 12).
usage (whisperer env): python lab/songs/where_i_left_it_s10.py"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import syllables, V1, V2, CH, BR, LAST  # noqa: E402
from where_i_left_it_s3 import join_beats, abc_pitch, dur  # noqa: E402
import where_i_left_it_s6 as s6  # noqa: E402
import where_i_left_it_s7 as s7  # noqa: E402
import where_i_left_it_s9 as s9  # noqa: E402

NAME = 'where_i_left_it_s10'
WORDS = syllables(V1) + syllables(CH) + syllables(V2) + syllables(CH) + [w for w in syllables(BR) if w != '_'] + syllables(LAST)


def rh_bar(spec, pd, st):
    """s6.rh_bar, plus chords inside triplets: '(3 [E1 E2]/2 B2/2 E3/2'"""
    if not spec:
        return (pd or '') + 'z16'
    ev, t, trip, deco = [], 0, 0, ''
    for tok in re.findall(r'!\S+?!|\(3|\[[^\]]*\]/?\d+|z\d+|[A-G][#b]?\d+/\d+', spec):
        if tok.startswith('!'):
            deco += tok
            continue
        if tok == '(3':
            trip = 3
            continue
        pre = deco + ('(3' if trip == 3 else '')
        deco = ''
        if tok.startswith('z'):
            n = int(tok[1:])
            ev.append((t, pre + 'z' + dur(n), True, 3 * n))
            t += 3 * n
            continue
        if tok.startswith('['):
            ps, n = tok[1:].split(']')
            n = int(n.lstrip('/'))
            txt = '[' + ''.join(abc_pitch(p, 'G', st) for p in ps.split()) + ']' + dur(n)
        else:
            p, n = tok.split('/')
            n = int(n)
            txt = abc_pitch(p, 'G', st) + dur(n)
        d = 2 * n if trip else 3 * n
        ev.append((t, pre + txt, False, d))
        trip = max(0, trip - 1)
        t += d
    assert t == 48, (spec, t)
    return (pd or '') + join_beats(ev)


s6.rh_bar = rh_bar

ROCK = {'Em': 'E2 B2 G3 B2 E2 B2 G3 B2', 'F#o7': 'F#2 C3 A3 C3 F#2 C3 A3 C3', 'B7': 'B1 F#2 D#3 F#2 B1 A2 D#3 A2',
        'D7/F#': 'F#2 D3 A3 D3 F#2 C3 A3 C3', 'Bm7': 'B1 F#2 D3 F#2 B1 A2 D3 A2'}


def rock(ch):
    return ' '.join(p + '/2' for p in ROCK[ch].split())


def flowx(ch):
    """the chorus flow with the bass doubled at the octave"""
    a, b, c, d, e, f = s9.LH6[ch].split()
    o = int(a[-1])
    lo = f'{a[:-1]}{o - 1} {a}' if o >= 2 else f'{a} {a[:-1]}{o + 1}'
    half = f'(3 [{lo}]/2 {b}/2 {c}/2 (3 {d}/2 {e}/2 {f}/2'
    return half + ' ' + half


def arp(ch):
    """the intro's bass: a short arpeggio on the beat, then space"""
    return {'Em': 'E2/2 B2/2 G3/2 z2 z8', 'F#o7': 'F#2/2 C3/2 A3/2 z2 z8', 'B7': 'B1/2 F#2/2 D#3/2 z2 z8',
            'Cmaj7': 'C2/2 G2/2 E3/2 z2 z8'}[ch]


# interlude: the tune's opening in the piano, the B7 without its third (bar 21) under the pickup
INTER_EH = ['z/16', 'z/12 !p! ( E4/2 F#4/2']
INTER_PNO = [('G4/8 A4/4 B4/4', arp('Em'), '!p!'),
             ('C5/8 B4/4 z4', 'F#2/2 C3/2 A3/2 z2 !ped-up!!ped! B1/2 F#2/2 A2/2 z2', None)]

# verse 2: verse 1's tune, rhythms fitted to the new words ("let-ters", "loud-er", "need-ed" are
# never split by a rest); line 2 resolves falsely to B minor; line 4 runs straight into the chorus
V2_EH = [
    '!<(! G4/8 A4/4 B4/4', '!<)! !>(! C5/8 A4/2 ) !>)! z/2 ( A4/4', '!<(! B4/8 !<)! !>(! A4/4 F#4/4', 'G4/8 ) !>)! z/4 ( E4/2 F#4/2',
    '!<(! G4/8 A4/4 B4/4', '!<)! !>(! C5/8 A4/2 ) !>)! z/2 ( B4/4', '!>(! C5/4 M/B4/4 A4/4 F#4/4', 'G4/8 ) !>)! z/4 ( G4/2 A4/2',
    '!mp! !<(! B4/8 C5/4 D5/4', 'E5/8 C5/2 ) z/2 ( E5/4', '!<)! !>(! F#5/8 E5/4 D#5/4', 'E5/8 ) !>)! z/4 ( D5/2 C5/2',
    '!p! !>(! B4/8 A4/4 G4/4', 'A4/6 G4/2 ) !>)! z/4 ( B4/4', '!<(! F#4/8 G4/4 A4/4', '!<)! !>(! A4/8 ) !>)! z/4 ( C5/2 D5/2']
V2_PNO = [
    # the rising sigh of verse 1 over a rocking left hand
    ('z6 B3/2 E4/8', rock('Em'), '!p!'),
    ('z6 A3/2 E4/8', rock('F#o7'), None),
    ('z6 B3/2 D#4/8', rock('B7'), None),
    ('E4/8 (3 B4/2 A4/2 G4/2 z4', rock('Em'), None),
    # a counter-line that moves under the held notes
    ('E4/4 D4/4 B3/8', rock('Em'), None),
    ('A3/4 C4/4 D4/8', rock('D7/F#'), None),
    ('[B3 D4]16', rock('Bm7'), None),
    ('B3/8 (3 C4/2 D4/2 E4/2 z4', rock('Em'), None),
    # thirds under the tune, an octave below
    ('[G3 B3]8 [A3 C4]4 [B3 D4]4', rock('Em'), '!mp!'),
    ('[C4 E4]8 [A3 C4]2 z2 [C4 E4]4', rock('F#o7'), None),
    ('[A3 D#4 F#4]8 [A3 E4]4 [B3 D#4]4', rock('B7'), None),
    ('[G3 E4]8 (3 G4/2 F#4/2 E4/2 [B3 D4]2 [A3 C4]2', rock('Em'), None),
    # the quiet: held chords, and nothing under the pickup
    ('[G3 B3]16', '[E1 E2]16', '!p!'),
    ('[G3 B3]8 (3 E4/2 C4/2 G3/2 z4', '[C2 G2]16', None),
    ('[A3 C4]16', '[F#1 C2]16', None),
    ('[F#3 A3]8 z8', '[B1 F#2]8 z8', None),
]

# chorus 2: the tune an octave below, then in thirds; "home" lands on C
CH2_RH = ['E4/8 D4/4 C4/4', 'C4/8 B3/2 z2 B3/4', 'D4/8 C4/4 B3/4', 'B3/8 (3 D4/2 F#4/2 A4/2 A3/2 B3/2',
          'C4/8 B3/4 A3/4', 'A3/8 F#3/2 z2 G3/4', 'B3/8 A3/4 F#3/4', 'G3/8 (3 B3/2 E4/2 G4/2 z4',
          '[G3 E4]8 [B3 D4]4 [A3 C4]4', '[E3 C4]8 [G3 B3]2 z2 [G3 B3]4', '[A3 F#4]8 [C4 E4]4 [A3 C4]4',
          '[D3 B3]8 (3 D4/2 F#4/2 A4/2 [G3 B3]2 [A3 C4]2', '[G3 E4]8 [B3 D4]4 [A3 C4]4',
          '[E3 C4]8 (3 C5/2 B4/2 A4/2 (3 G4/2 F#4/2 E4/2', 'D#4/4 [F#4 A4]4 [F#4 A4]8', '[E4 G4 C5]12 z4']
CH2_LH = [s9.flow(c) for c in s9.CHORDS] + [s9.flow(c) for c in s9.CHORDS[:6]] + ['[B1 F#2]16', '[C2 G2]16']
CH2_DYN = {0: '!mp!', 8: '!mf!', 14: '!p!'}

# bridge: speech rhythms over a slow chorale and moving bass (C A F# B), the opening for
# "the first note came back", then D7 to G for "a name I forgot that I knew"
BR_EH = [
    'z/12 !p! ( G4/2 A4/2',
    '!<(! B4/4 A4/2 G4/2 E4/4 G4/2 A4/2',
    '!<)! !>(! C5/6 B4/2 ) !>)! z/4 ( A4/2 B4/2',
    '!>(! C5/4 B4/2 A4/4 G4/2 F#4/2 F#4/2',
    'E4/6 M/D#4/2 ) !>)! z/4 ( E4/2 F#4/2',
    '!<(! G4/8 A4/4 B4/4',
    'C5/8 ) z/4 ( A4/2 B4/2',
    'C5/6 ) z/2 ( A4/4 D5/4',
    '!<)! !mf! !>(! E5/8 D5/4 C5/4',
    'B4/8 ) !>)! z/8',
    'z/12 !mf! ( C5/2 D5/2']
BR_PNO = [
    ('[E4 G4]4 [C4 E4]4 [A3 C4]4 z4', 'C2/4 C3/4 C2/4 z4', '!p!'),
    ('[E3 G3 B3]8 [E3 G3 C4]8', '[C2 G2]16', None),
    ('[E3 A3 C4]8 [E3 G3 C4]8', '[A1 E2]16', None),
    ('[E3 A3 C4]16', '[F#1 C2]16', None),
    ('[F#3 A3 B3]16', '[B1 F#2]16', None),
    ('z6 B3/2 E4/8', arp('Em'), None),
    ('z6 E3/2 A3/8', arp('F#o7'), None),
    ('z6 C4/2 G4/8', 'D2/2 A2/2 D3/2 G3/2 A3/2 G3/2 D3/2 A2/2', '!mp!'),
    ('[A3 C4 F#4]16', 'F#2/2 A2/2 D3/2 F#3/2 A3/2 F#3/2 D3/2 A2/2', '!mf!'),
    ('[G3 B3 D4]8 [B3 D4]4 [C4 E4]4', 'G1/2 D2/2 G2/2 B2/2 D3/2 B2/2 G2/2 D2/2', '!mp!'),
    ('(3 E4/2 G4/2 B4/2 (3 C5/2 E5/2 G5/2 [F#4 A4]4 z4', 'C2/2 G2/2 C3/2 E3/2 !ped-up!!ped! [B1 F#2]4 z4', None),
]

# last chorus: the same tune; "and I won't" takes the peak; "so I'll leave the light on" is the
# verse's first phrase, over the opening piano
LAST_EH = [
    '!f! !<(! E5/8 D5/4 C5/4', '!<)! !>(! C5/8 B4/2 ) !>)! z/2 ( B4/4', '!<(! D5/8 C5/4 B4/4', '!<)! !>(! B4/8 ) !>)! z/4 ( A4/2 B4/2',
    '!<(! C5/8 B4/4 A4/4', '!<)! A4/8 F#4/2 ) z/2 ( G4/4', '!>(! B4/8 A4/4 F#4/4', 'G4/8 ) !>)! z/4 ( C5/2 D5/2',
    '!<(! E5/8 D5/4 C5/4', 'C5/8 B4/2 ) z/2 ( B4/2 D5/2', '!<)! !ff! !>(! F#5/8 E5/4 C5/4', 'B4/8 ) !>)! z/4 ( !p! E4/2 F#4/2',
    '!<(! G4/8 A4/4 B4/4', '!<)! !>(! C5/8 ) !>)! z/8', 'z/4 ( !<(! B4/4 D#5/8', '!<)! !>(! E5/12 ) !>)! z/4']
LAST_PNO = [
    ('[G3 B3 E4]8 [B3 D4]4 [A3 C4]4', flowx('Em'), '!f!'),
    ('[E3 A3 C4]8 [G3 B3]2 z2 [G3 B3]4', flowx('Am7'), None),
    ('[F#3 A3 D4]8 [A3 C4]4 [G3 B3]4', flowx('D7'), None),
    ('[D3 F#3 B3]8 (3 A4/2 F#4/2 D4/2 [F#3 A3]2 [G3 B3]2', flowx('Gmaj7'), None),
    ('[E3 G3 C4]8 [G3 B3]4 [E3 A3]4', flowx('Cmaj7'), None),
    ('[A3 C4 E4]8 [F#3 A3]2 z2 [G3 B3]4', flowx('F#o7'), None),
    ('[D#3 F#3 B3]8 [F#3 A3]4 [D#3 F#3]4', flowx('B7'), None),
    ('[E3 G3 B3]8 (3 B3/2 E4/2 G4/2 z4', flowx('Em'), None),
    ('[G3 B3 E4]8 [B3 D4]4 [A3 C4]4', flowx('Em'), None),
    ('[E3 A3 C4]8 [G3 B3]2 z2 [G3 B3]2 [B3 D4]2', flowx('Am7'), None),
    ('[A3 C4 F#4]8 [A3 C4 E4]4 [F#3 A3 C4]4', flowx('D7'), '!ff!'),
    ('[D3 F#3 B3]8 (3 B4/2 A4/2 G4/2 z4', s9.flow('Gmaj7'), '!mf!'),
    ('z6 B3/2 E4/8', arp('Cmaj7'), '!p!'),
    ('z6 E3/2 A3/8', arp('F#o7'), None),
    ('z6 F#3/2 A3/8', arp('B7'), None),
    ('G4/8 A4/4 B4/4', arp('Em'), None),
]

# coda: the piano finishes its tune; the horn holds a soft fifth over the last chord
CODA_EH = ['z/16', 'z/16', '!pp! !fermata! N/B4/16']
CODA_PNO = [('C5/8 A4/4 z4', arp('F#o7'), None),
            ('B4/8 A4/4 F#4/4', arp('B7'), None),
            ('!fermata! [B3 E4 G4]16', '!fermata! [E1 E2 B2]16', '!pp!')]

# (bar, quarter beat from 0, quarter notes per minute, words)
TEMPO = [(95, 0, 60, 'poco rit.'), (95, 2, 58, None), (96, 0, 56, None), (96, 2, 54, None), (97, 0, 52, None),
         (97, 2, 50, None), (98, 0, 56, 'meno mosso'), (100, 0, 52, 'rit.'), (100, 1, 50, None), (100, 2, 47, None),
         (100, 3, 44, None), (101, 0, 40, None)]


def add_tempi(xml):
    """real tempo changes: <sound tempo> at quarter beats of the English horn part"""
    p1 = xml.index('<part id="P1">')
    div = int(re.search(r'<divisions>(\d+)</divisions>', xml[p1:]).group(1))
    for barno, beat, q, text in sorted(TEMPO, reverse=True):
        ms = xml.index(f'<measure number="{barno}"', p1)
        me = xml.index('</measure>', ms)
        pos, t = None, 0
        for m in re.finditer(r'<note[ >].*?</note>', xml[ms:me], re.S):
            if t >= beat * div:
                pos = ms + m.start()
                break
            if '<chord/>' not in m.group(0) and '<grace' not in m.group(0):
                t += int(re.search(r'<duration>(\d+)</duration>', m.group(0)).group(1))
        if pos is None:
            pos = me
        el = (f'<direction placement="above"><direction-type><words font-style="italic">{text}</words>'
              f'</direction-type><sound tempo="{q}"/></direction>') if text else f'<sound tempo="{q}"/>'
        xml = xml[:pos] + el + xml[pos:]
    return xml


def song():
    eh, piano = s9.apply()
    chorus_eh = eh[21:37]
    eh = eh + INTER_EH + V2_EH + chorus_eh + BR_EH + LAST_EH + CODA_EH
    piano = piano + INTER_PNO + V2_PNO
    piano += [(r, l, CH2_DYN.get(i)) for i, (r, l) in enumerate(zip(CH2_RH, CH2_LH))]
    piano += BR_PNO + LAST_PNO + CODA_PNO
    return eh, piano


if __name__ == '__main__':
    eh, piano = song()
    assert len(eh) == len(piano) == 101, (len(eh), len(piano))
    s7.EH, s7.PIANO = eh, piano
    bars = s7.build()
    s6.NAME, s6.WORDS = NAME, WORDS
    abc = s6.to_abc(bars).replace(' ||\n', ' |]\n')
    out, log = s6.convert(abc)
    xml = add_tempi(open(out, encoding='utf-8').read())
    open(out, 'w', encoding='utf-8').write(xml)
    print(f'{len(bars)} bars, {len(WORDS)} syllables -> {out}')
    if log:
        print(log[-1500:])
