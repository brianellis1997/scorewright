"""Where I Left It, second version (S2): the same words, form and instruments as S1, rewritten after
Brian's verdict on S1 ("too pop, too saccharine, on the nose, no mystery; the left-hand texture ran
too long; key changes too abrupt; decrescendos cut off before the held notes; no ritardando").

What changed, measured against his songs with style_profile.py (see COMPOSING.md section 11):
- harmony from his own vocabulary: tonic and dominant pedals with chords moving above them, polychords
  (C/D, A/G), Lydian #4, borrowed bVI, iv and bVII, half-diminished and V7(b9) chords, chromatic bass,
  a deceptive bVI under the last held "home", a plagal iv-I to close
- the melody leans: most stressed syllables are appoggiaturas or suspensions that resolve by step,
  some resolve only when the harmony moves under a held note, a few never resolve
- verse 2 reharmonises verse 1's tune; its third line planes major sevenths up by step
- the bridge reaches the flat side gradually (D -> Dm -> Bb -> Gb) and returns to D by the common
  tone F# = Gb, where the intro's figure comes back with the words "the first note came back"
- the accompaniment changes figure every one to four bars
- every hairpin on a held note runs to the end of the note; tempo changes are real <sound tempo>
  steps (poco rit. into the last chorus, rit. and molto rit. in the coda)

usage (whisperer env): python lab/songs/where_i_left_it_s2.py
output: ~/Documents/Score Exports/_scorewright_out/songs/where_i_left_it_s2.{abc,musicxml}"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import parse, up_fifth, dur, syllables, V1, V2, CH, BR, LAST  # noqa: E402

LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it_s2'
WORDS = syllables(V1) + syllables(CH) + syllables(V2) + syllables(CH) + syllables(BR) + syllables(LAST)

KEYSIG = {'D': {'F': 1, 'C': 1}, 'A': {'F': 1, 'C': 1, 'G': 1}, 'Bb': {'B': -1, 'E': -1}, 'F': {'B': -1}}
WRITTEN = {'D': 'A', 'Bb': 'F'}
QUARTER = 69                       # dotted quarter = 46


def abc_pitch(p, key, state):
    l, a, o = parse(p)
    cur = state.get((l, o), KEYSIG[key].get(l, 0))
    acc = ''
    if a != cur:
        acc = {1: '^', -1: '_', 0: '='}[a]
        state[(l, o)] = a
    if o <= 4:
        return acc + l + ',' * (4 - o)
    return acc + l.lower() + "'" * (o - 5)


def bar(eh, h1, h2=None, tex='pulse', pd=None, key='D'):
    return dict(eh=eh, h=[h1, h2 or h1], tex=tex if isinstance(tex, list) else [tex, tex], pd=pd, key=key)


# ---------------------------------------------------------------- the bars
# eh: English horn in CONCERT pitch. Pitch/sixteenths, ~ ties into the next note, z/n rest, ( ) slur,
# !...! decoration on the next event, N/ a wordless note, M/ a melisma note (extends the syllable).
# h: 'left hand ; right hand' for each beat, low to high. tex: the piano figure for each beat.
INTRO = [
    bar('z/12', 'D2 A2 ; A3 C#4 F#4 E5', 'D2 A2 ; A3 C#4 F#4 D5', 'arch', '!pp!'),
    bar('z/12', 'D2 A2 ; A3 D4 G#4 E5', 'D2 A2 ; A3 C#4 G#4 C#5', 'arch'),
    bar('z/12', 'D2 A2 ; F3 Bb3 D4 C5', 'D2 A2 ; F3 A3 D4 Bb4', 'fall'),
    bar('z/12', 'D2 G2 ; G3 Bb3 E4 A4', 'A1 E2 ; G3 B3 D4 G4', 'fall'),
    bar('z/8 !p! ( A3/2 C#4/2', 'A1 E2 ; G3 C#4 F#4', 'A1 E2 ; E3 G3 B3', 'pulse'),
]
VERSE1 = [
    bar('!<(! E4/4 D4/1 A3/1 F#4/3 E4/1 D4/2', 'D2 A2 ; F#3 A3 D4', 'D2 A2 ; E3 G3 B3', 'pulse', '!p!'),
    bar('B4/4 A4/1 G4/1 !<)! !>(! F#4/6~', 'D2 A2 ; E3 G3 C4', 'C#2 G2 ; E3 G3 B3', 'pulse'),
    bar('F#4/12 )', 'C2 ; D3 F#3 A3', 'B1 F#2 ; D3 F#3 B3', 'pulse'),
    bar('!>)! z/8 ( B3/2 C#4/2', 'B1 F#2 ; D3 F#3 A3 D4', 'D2 ; B2 E3 G3', ['arch', 'wave']),
    bar('!<(! D4/4 C#4/1 B3/1 G4/3 F#4/1 E4/2', 'A1 E2 ; C#3 E3 A3', 'G1 ; E3 G3 B3', 'ripple'),
    bar('Bb4/4 A4/1 G4/1 !<)! !>(! E4/6~', 'C2 G2 ; E3 G3 Bb3', 'Bb1 G2 ; D3 E3 G3', 'ripple'),
    bar('E4/6 M/D4/2 M/C#4/2 M/D4/2 )', 'A1 E2 ; C#3 E3 G3', 'A1 E2 ; D3 E3 G3', 'wave'),
    bar('!>)! z/8 ( E4/2 F#4/2', 'A1 E2 ; C#3 E3 A3', 'C#2 A2 ; E3 G3 Bb3', 'wave'),
    bar('!<(! G4/4 F#4/1 A4/1 E5/3 D5/1 B4/2', 'B1 F#2 ; D3 F#3 B3 D4', 'G1 D2 ; D3 F#3 B3 D4', 'arch'),
    bar('C#5/4 B4/1 A4/1 !<)! !>(! G4/6', 'B1 ; D3 G3 B3 D4', 'F#1 C#2 ; E3 A#3 C#4 E4', 'arch'),
    bar('M/F#4/12 )', 'B1 F#2 ; D3 F#3 B3', 'D2 A2 ; F#3 B3 D4', 'pulse'),
    bar('!>)! z/8 ( D4/2 E4/2', 'G1 ; D3 E3 B3', 'A1 E2 ; G3 B3 C#4', ['wave', 'pulse']),
    bar('!<(! G4/4 F#4/1 E4/1 B4/3 A4/1 G4/2', 'D2 ; G3 B3 D4', 'C2 G2 ; E3 G3 C4', 'chorale'),
    bar('A4/4 G4/1 E4/1 !<)! !>(! D4/6~', 'G1 D2 ; Bb2 E3 G3', 'A1 E2 ; D3 G3 B3', 'chorale'),
    bar('D4/12~', 'A1 E2 ; D3 G3 B3', None, 'wave'),
    bar('D4/4 ) !>)! z/4 ( A4/2 B4/2', 'A1 E2 ; D3 G3 B3', 'A1 E2 ; E3 G3 B3', ['wave', 'pulse']),
]
CHORUS1 = [
    bar('!mp! !<(! C#5/4 B4/1 A4/1 D5/3 C#5/1 B4/2', 'G1 D2 B2 ; D3 G3', 'G#1 E2 B2 ; D3 E3', 'barc', '!mp!'),
    bar('E5/4 D5/1 B4/1 !<)! !>(! C#5/6~', 'A1 E2 C#3 ; E3 A3', 'A#1 F#2 C#3 ; F#3 A#3', 'barc'),
    bar('C#5/6 M/B4/6~', 'B1 F#2 D3 ; F#3 B3', 'G#1 D2 B2 ; F#3 B3', 'barc'),
    bar('B4/4 ) !>)! z/4 ( F#4/2 G4/2', 'B1 G2 D3 ; G3 B3', 'A1 E2 ; C#3 E3 G3 A3', ['barc', 'arch']),
    bar('!<(! A4/4 G4/1 F#4/1 D5/3 C#5/1 B4/2', 'G1 D2 ; D3 G3 B3 D4', 'G1 D2 ; C#3 E3 A3 C#4', 'arch'),
    bar('E5/4 D5/1 C#5/1 !<)! !>(! B4/6~', 'B1 ; E3 G3 B3 E4', 'G1 D2 ; E3 G3 B3 D4', 'arch'),
    bar('B4/12 )', 'A1 E2 ; D3 G3 B3', 'C#2 A2 ; E3 G3 A3', 'wave'),
    bar('!>)! z/8 ( A4/2 B4/2', 'A1 E2 ; C#3 G3 Bb3', 'A1 E2 ; C#3 G3 B3', 'pulse'),
    bar('!mf! !<(! C#5/4 B4/1 A4/1 D5/3 C#5/1 B4/2', 'G1 D2 B2 ; D3 G3', 'D2 F#2 B2 ; D3 F#3', 'barc', '!mf!'),
    bar('F#5/4 E5/1 D5/1 !<)! !>(! E5/6~', 'A1 E2 C#3 ; G3 C#4', 'D#2 A2 F#3 ; B3 C4', 'barc'),
    bar('E5/12 )', 'E2 B2 G3 ; E4 G4', 'D2 B2 G3 ; E4 G4', 'barc'),
    bar('!>)! z/8 ( C#5/2 D5/2', 'E2 C3 G3 ; C4 E4', 'A1 E2 C#3 ; E3 G3', 'barc'),
    bar('!<(! E5/4 D5/1 B4/1 Bb4/4 A4/1 G4/1', 'G1 E2 B2 ; E3 G3', 'Bb1 G2 D3 ; E3 G3', 'barc'),
    bar('!<)! !>(! D5/12~', 'A1 E2 ; D3 G3 B3', 'A1 E2 ; C#3 G3 Bb3', 'chorale'),
    bar('D5/12~', 'Bb1 F2 ; D3 F3 A3', 'G1 D2 ; Bb2 E3 G3', 'chorale'),
    bar('D5/6 ) !>)! z/6', 'D2 A2 ; F#3 A3 B3', 'F#1 D2 ; E3 A3', 'chorale'),
]
INTER1 = [
    bar('z/12', 'D2 A2 ; A3 C#4 F#4 E5', 'D2 A2 ; A3 C#4 F#4 D5', 'arch', '!p!'),
    bar('z/8 !p! ( B3/2 C#4/2', 'D2 A2 ; A3 D4 G#4 E5', 'F#1 C#2 ; E3 A#3 C#4', ['arch', 'pulse']),
]
VERSE2 = [
    bar('!<(! E4/4 D4/1 A3/1 F#4/3 E4/1 D4/2', 'B1 F#2 ; D3 F#3 B3', 'F#1 ; A2 D3 F#3', 'ripple', '!p!'),
    bar('B4/4 A4/1 G4/1 !<)! !>(! F#4/6~', 'A1 E2 ; E3 G3 C4', 'D2 ; D3 F#3 B3', 'ripple'),
    bar('F#4/12 )', 'G1 D2 ; F#3 B3 D4', 'E2 B2 ; F#3 G3 D4', 'rock'),
    bar('!>)! z/8 ( B3/2 C#4/2', 'A1 E2 ; G3 B3 D4', 'C#2 A2 ; E3 G3 B3', 'rock'),
    bar('!<(! D4/4 C#4/1 B3/1 G4/3 F#4/1 E4/2', 'A1 ; D3 F#3 A3', 'G1 ; E3 G3 B3', 'wave'),
    bar('Bb4/4 A4/1 G4/1 !<)! !>(! E4/6~', 'C2 G2 ; E3 G3 Bb3', 'D2 ; Bb2 D3 G3', 'wave'),
    bar('E4/6 M/D4/2 M/C#4/2 M/D4/2 )', 'A1 E2 ; C#3 E3 G3 A3', 'A1 E2 ; D3 E3 G3 A3', 'arch'),
    bar('!>)! z/8 ( F#4/2 G4/2', 'A1 E2 ; C#3 E3 G3 B3', 'E2 A2 ; C#3 E3 G3 Bb3', 'arch'),
    bar('!<(! A4/3 G4/1 F#4/2 B4/3 A4/1 G#4/2', 'G1 D2 ; B2 D3 F#3 B3', 'A1 E2 ; C#3 E3 G#3 C#4', 'arch'),
    bar('C#5/3 B4/1 A#4/2 !<)! !>(! D5/6~', 'B1 F#2 ; D#3 F#3 A#3 D#4', 'C2 G2 ; E3 G3 B3 E4', 'arch'),
    bar('D5/12 )', 'D2 A2 ; F#3 A3 C#4 F#4', 'D2 ; D3 F#3 B3 D4', 'arch'),
    bar('!>)! z/8 ( F#4/2 G4/2', 'G1 ; D3 E3 B3', 'C#2 ; E3 G3 B3', 'wave'),
    bar('!<(! A4/4 G4/1 F#4/1 B4/3 A4/1 G#4/2', 'A1 E2 ; D3 F#3 B3', 'A1 E2 ; D3 G#3 B3', 'pulse'),
    bar('G4/4 F#4/1 F4/1 !<)! !>(! E4/6~', 'A1 E2 ; C#3 E3 G3', 'A1 E2 ; C#3 G3 Bb3', 'pulse'),
    bar('E4/12 )', 'A1 E2 ; D3 G3 B3', None, 'chorale'),
    bar('!>)! z/8 ( A4/2 B4/2', 'A1 E2 ; D3 G3 B3', 'A1 E2 ; C#3 G3 B3', ['chorale', 'pulse']),
]
CHORUS2 = [
    bar('!mf! !<(! C#5/4 B4/1 A4/1 D5/3 C#5/1 B4/2', 'G1 D2 ; D3 G3 B3 D4', 'B1 ; D3 E3 G#3 B3', 'arch', '!mf!'),
    bar('E5/4 D5/1 B4/1 !<)! !>(! C#5/6~', 'A1 ; C#3 E3 A3 C#4', 'C#2 ; C#3 F#3 A#3 C#4', 'arch'),
    bar('C#5/6 M/B4/6~', 'B1 F#2 ; D3 F#3 B3 D4', 'D2 ; F#3 B3 D4', ['arch', 'wave']),
    bar('B4/4 ) !>)! z/4 ( F#4/2 G4/2', 'G1 D2 ; D3 G3 B3 D4', 'A1 E2 ; C#3 E3 G3 A3', 'arch'),
    bar('!<(! A4/3 M/B4/1 G4/1 F#4/1 D5/3 C#5/1 B4/2', 'G1 D2 B2 ; D3 G3', 'G1 E2 A2 ; C#3 E3', 'barc'),
    bar('E5/4 D5/1 C#5/1 !<)! !>(! B4/6~', 'B1 G2 E3 ; G3 B3', 'G1 D2 B2 ; E3 G3', 'barc'),
    bar('B4/6 M/A4/6 )', 'A1 E2 ; D3 G3 B3', 'C#2 A2 ; E3 G3 A3', 'rock'),
    bar('!>)! z/8 ( A4/2 B4/2', 'A1 E2 ; C#3 G3 Bb3', 'A1 E2 ; C#3 G3 B3', 'pulse'),
    bar('!f! !<(! C#5/4 B4/1 A4/1 D5/3 C#5/1 B4/2', 'G1 G2 ; D3 G3 B3', 'D2 D3 ; F#3 B3 D4', 'pulse', '!f!'),
    bar('F#5/4 E5/1 D5/1 !<)! !>(! E5/6~', 'A1 A2 ; E3 G3 C#4', 'F#1 F#2 ; A3 B3 D#4', 'pulse'),
    bar('E5/12 )', 'E2 B2 ; E3 G3 B3 E4', 'D2 A2 ; E3 G3 B3 D4', 'arch'),
    bar('!>)! z/8 ( C#5/2 D5/2', 'E2 C3 ; E3 G3 C4 E4', 'A1 E2 ; C#3 E3 G3 A3', 'arch'),
    bar('!<(! E5/4 D5/1 B4/1 Bb4/4 A4/1 G4/1', 'G1 E2 B2 ; E3 G3', 'D2 G2 Bb2 ; E3 G3', 'barc'),
    bar('!<)! !>(! D5/12~', 'A1 E2 ; D3 G3 B3', 'A1 E2 ; C#3 G3 Bb3', 'chorale'),
    bar('D5/12~', 'Bb1 F2 ; D3 F3 A3', 'G1 D2 ; Bb2 E3 G3', 'chorale'),
    bar('D5/6 ) !>)! z/6', 'D2 A2 ; F#3 A3 B3', 'D2 A2 ; F3 A3 C4', 'chorale'),
]
INTER2 = [
    bar('z/12', 'D2 A2 ; F3 A3 C4 E4', 'Bb1 F2 ; D3 F3 A3 C4', 'arch', '!p!', key='Bb'),
    bar('z/8 !pp! ( D4/2 Eb4/2', 'G1 D2 ; Bb2 D3 F3 A3', 'G1 D2 ; Bb2 D3 F3', ['fall', 'pulse'], key='Bb'),
]
BRIDGE = [
    bar('!<(! F#4/4 G4/1 A4/1 C5/3 Bb4/1 G4/2', 'G1 D2 ; Bb2 D3 A3', 'Eb2 Bb2 ; G3 D4', 'heart', '!pp!', key='Bb'),
    bar('F#4/4 D4/2 ) z/2 ( D4/2 Eb4/2', 'Bb1 F#2 ; D3 F#3 Bb3', 'G1 ; Bb2 Eb3 D4', 'heart', key='Bb'),
    bar('!<)! !>(! Bb4/4 Ab4/2 G4/3 F4/1 Eb4/1 Db4/1', 'Ab1 Eb2 ; C3 Eb3 G3', 'C2 G2 ; Bb2 Eb3 G3', 'rock', key='Bb'),
    bar('F4/6 Eb4/6 )', 'Gb1 Db2 ; Bb2 Db3 F3 Ab3', None, 'arch', key='Bb'),
    bar('!>)! z/12', 'Gb1 Db2 ; Bb2 Db3 F3 Bb3', 'Gb1 Db2 ; Bb2 C3 F3 Bb3', 'fall', '!pp!', key='Bb'),
    bar('z/12', 'Eb2 Bb2 ; Db3 Gb3 Bb3 F4', 'Eb2 Bb2 ; Db3 Gb3 Bb3 Db4', 'arch', key='Bb'),
    bar('z/12', 'Db2 Ab2 ; Cb3 Eb3 Gb3 Bb3', 'Db2 Ab2 ; F3 Ab3 Cb4 Eb4', 'arch', key='Bb'),
    bar('z/8 !p! ( Bb4/2 Db5/2', 'Gb1 Db2 ; Bb2 Db3 Gb3 Bb3', 'Gb1 Db2 ; Bb2 Db3 F3', ['arch', 'pulse'], key='Bb'),
    bar('!<(! E5/6 D5/3 C#5/3', 'D2 A2 ; F#3 A3 C#4 E4', 'D2 A2 ; F#3 A3 C#4 D4', 'arch', '!p!'),
    bar('F#5/6 E5/3 D5/3', 'D2 A2 ; E3 G#3 B3 D4', None, 'arch'),
    bar('G5/6 F#5/3 E5/3', 'F#1 C#2 ; A2 D3 F#3 A3', None, 'arch', '!mf!'),
    bar('G#5/6 F#5/3 E5/3', 'G#1 E2 ; B2 D3 F#3 B3', 'B1 ; D3 E3 G#3 B3', 'arch'),
    bar('!<)! !f! A5/12~', 'G1 D2 B2 ; F#3 B3 C#4 E4', None, 'barc', '!f!'),
    bar('!>(! A5/6 M/G5/6', 'E2 B2 ; G3 B3 D4 F#4', None, 'arch'),
    bar('M/F#5/6 M/E5/6 )', 'A1 E2 ; D3 G3 B3', 'A1 E2 ; C#3 G3 B3', 'wave', '!mp!'),
    bar('!>)! z/8 ( C#5/2 D5/2', 'A1 E2 ; C#3 G3 Bb3', 'A1 E2 ; C#3 G3 B3', 'pulse'),
]
LASTCH = [
    bar('!f! !<(! E5/4 D5/1 C#5/1 F#5/3 E5/1 D5/2', 'G1 D2 B2 ; D3 G3 B3', 'G#1 E2 B2 ; D3 E3 G#3', 'drive', '!f!'),
    bar('G5/4 F#5/1 D5/1 !<)! !>(! E5/6~', 'A1 E2 C#3 ; G3 C#4', 'A#1 F#2 C#3 ; F#3 A#3 C#4', 'drive'),
    bar('E5/6 M/D5/6~', 'B1 F#2 D3 ; F#3 B3', 'G#1 D2 B2 ; F#3 B3', 'drive'),
    bar('D5/4 ) !>)! z/4 ( B4/2 C#5/2', 'B1 G2 D3 ; G3 B3', 'C#2 A2 E3 ; G3 A3', 'barc'),
    bar('!<(! F#5/4 E5/1 D5/1 A5/3 G5/1 F#5/2', 'E2 B2 ; G3 B3 D4 E4', 'E2 ; E3 G3 C4 E4', 'arch'),
    bar('E5/4 D5/1 C#5/1 !<)! !>(! D5/6~', 'B1 ; E3 G#3 B3 E4', 'E2 B2 ; D3 E3 G#3 B3', 'arch'),
    bar('D5/12 )', 'A1 E2 ; D3 G3 B3', 'C#2 A2 ; E3 G3 A3', 'wave'),
    bar('!>)! z/8 ( C#5/2 D5/2', 'A1 E2 ; C#3 G3 Bb3', 'A1 E2 ; C#3 G3 B3', 'pulse'),
    bar('!<(! E5/4 D5/1 C#5/1 F#5/3 E5/1 D5/1 E5/1', 'G1 D2 B2 ; D3 G3 B3', 'G#1 E2 B2 ; D3 E3 G#3', 'drive'),
    bar('!ff! A5/4 G5/1 F#5/1 !<)! !>(! G5/6~', 'D#2 A2 F#3 ; B3 C4', 'E2 B2 G3 ; D4 F#4', 'drive', '!ff!'),
    bar('G5/12 )', 'E2 C3 G3 ; C4 E4', 'A1 E2 ; D3 G3 B3', ['barc', 'wave']),
    bar('!>)! z/8 ( D5/2 E5/2', 'C#2 A2 ; E3 G3 B3', 'A1 E2 ; C#3 G3 Bb3', 'pulse', '!f!'),
    bar('!<(! F#5/4 E5/2 G#5/4 A5/2', 'D2 A2 ; D3 F#3 A3 B3', 'A1 F#2 ; D3 F#3 A3 D4', 'arch'),
    bar('F#5/3 E5/3 !<)! !<(! D5/6~', 'D2 A2 ; F#3 A3 D4', 'A1 E2 ; D3 G3 B3', ['wave', 'chorale']),
    bar('D5/6~ !<)! !>(! D5/6~', 'A1 E2 ; C#3 G3 Bb3', 'Bb1 F2 ; D3 F3 A3', 'chorale'),
    bar('D5/12~', 'G1 D2 ; Bb2 E3 G3', 'Bb1 G2 ; D3 E3 G3', 'chorale', '!mp!'),
    bar('D5/6 ) !>)! z/6', 'D2 A2 ; F#3 A3 B3', 'D2 A2 ; F#3 A3 B3 E4', ['chorale', 'arch'], '!p!'),
]
CODA = [
    bar('z/12', 'D2 A2 ; A3 C#4 F#4 E5', 'D2 A2 ; A3 C#4 F#4 D5', 'arch'),
    bar('z/6 !pp! ( !<(! N/E5/4 N/D5/2', 'D2 A2 ; F#3 A3 D4 G#4', 'D2 A2 ; F#3 A3 C#4 G#4', 'arch', '!pp!'),
    bar('!<)! !>(! N/C5/6 N/Bb4/6', 'D2 A2 ; F3 Bb3 C4 D4', 'D2 A2 ; F3 A3 Bb3 D4', 'fall'),
    bar('N/A4/12', 'D2 G2 ; G3 Bb3 D4 E4', 'D2 A2 ; F#3 A3 D4 E4', 'arch'),
    bar('N/A4/6 N/C#5/3 N/D5/3', 'D2 A2 ; F#3 A3 B3 E4', 'D2 A2 ; F#3 G#3 B3 E4', 'wave'),
    bar('!>)! !ppp! !fermata! N/E5/12 )', 'D2 A2 ; A3 D4 F#4 B4', None, 'final'),
]
SECTIONS = [('intro', INTRO), ('verse 1', VERSE1), ('chorus 1', CHORUS1), ('interlude', INTER1),
            ('verse 2', VERSE2), ('chorus 2', CHORUS2), ('interlude 2', INTER2), ('bridge', BRIDGE),
            ('last chorus', LASTCH), ('coda', CODA)]

# (bar index from 1, beat 0/1, quarter-note tempo, text or None)
_b = {name: 1 + sum(len(s) for _, s in SECTIONS[:i]) for i, (name, _) in enumerate(SECTIONS)}
TEMPO = [(_b['bridge'] + 14, 0, 65, 'poco rit.'), (_b['bridge'] + 14, 1, 61, None),
         (_b['bridge'] + 15, 0, 57, None), (_b['bridge'] + 15, 1, 54, None),
         (_b['last chorus'], 0, QUARTER, 'a tempo'),
         (_b['coda'] + 2, 0, 66, 'rit.'), (_b['coda'] + 2, 1, 63, None), (_b['coda'] + 3, 0, 59, None),
         (_b['coda'] + 3, 1, 55, None), (_b['coda'] + 4, 0, 50, 'molto rit.'), (_b['coda'] + 4, 1, 45, None),
         (_b['coda'] + 5, 0, 40, None)]


# ---------------------------------------------------------------- English horn
def eh_bar(spec, key, carry):
    """concert tokens -> written ABC and one kind per note: s syllable, k tie continuation or
    wordless (no lyric), m melisma (extender). A hairpin may not END on a tie continuation unless a
    new hairpin starts there (a swell): that is the S1 bug, a fade that stops before the held note."""
    state, out, kinds = {}, [], []
    pend, used = [], 0
    for tok in re.findall(r'"[^"]*"|!\S+?!|\(|\)|\S+', spec):
        if tok.startswith('!') or tok.startswith('"') or tok in '()':
            out.append(tok)
            if tok.startswith('!'):
                pend.append(tok)
            continue
        if tok.startswith('z/'):
            out.append('z' + dur(int(tok[2:])))
            used += int(tok[2:])
            pend = []
            continue
        kind = 's'
        if tok.startswith('N/'):
            kind, tok = 'k', tok[2:]
        elif tok.startswith('M/'):
            kind, tok = 'm', tok[2:]
        tie = tok.endswith('~')
        p, n = tok.rstrip('~').split('/')
        if carry['tied']:
            kind = 'k'
            stops = [d for d in pend if d in ('!<)!', '!>)!')]
            starts = [d for d in pend if d in ('!<(!', '!>(!')]
            if stops and not starts:
                raise ValueError(f'hairpin ends on a tied continuation (cut-off fade): {spec}')
        out.append(abc_pitch(up_fifth(p), WRITTEN[key], state) + dur(int(n)) + ('-' if tie else ''))
        kinds.append(kind)
        used += int(n)
        carry['tied'] = tie
        pend = []
    assert used == 12, f'English horn bar is {used} sixteenths: {spec}'
    return ' '.join(out).replace('( ', '(').replace(' )', ')'), kinds


# ---------------------------------------------------------------- piano
def piano_beat(tex, L, R, key, st, stl):
    n = lambda p: abc_pitch(p, key, st)
    nl = lambda p: abc_pitch(p, key, stl)
    ch = lambda ps, d, f: ('[' + ''.join(f(p) for p in ps) + ']' if len(ps) > 1 else f(ps[0])) + dur(d)
    r = R
    if tex == 'pulse':
        rh = ['z2', ch(r, 2, n), ch(r, 2, n)]
    elif tex == 'ripple':
        rh = ['z2', n(r[0]) + '', n(r[1]), n(r[2]), n(r[1])]
    elif tex == 'wave':
        t, m, lo = r[-1], r[-2], r[-3]
        rh = [n(t), n(m), n(lo), n(m), n(t), n(m)]
    elif tex == 'arch':
        rh = [n(x) for x in (r[0], r[1], r[2], r[3], r[2], r[1])] if len(r) >= 4 else \
             [n(x) for x in (r[0], r[1], r[2], r[1], r[0], r[1])]
    elif tex == 'fall':
        rh = [n(x) for x in (r[3], r[2], r[1], r[0], r[1], r[2])] if len(r) >= 4 else \
             [n(x) for x in (r[2], r[1], r[0], r[1], r[2], r[1])]
    elif tex == 'rock':
        rh = [n(x) for x in (r[0], r[2], r[1], r[2], r[0], r[2])]
    elif tex in ('barc', 'drive'):
        rh = ['z2', ch(r, 4, n)] if tex == 'barc' else ['z2', ch(r, 2, n), ch(r, 2, n)]
    elif tex in ('chorale', 'heart', 'final'):
        rh = [ch(r, 6, n)]
    else:
        raise ValueError(tex)
    if tex in ('barc', 'drive'):
        assert len(L) == 3, (tex, L)
        lh = [nl(L[0]) + '2', nl(L[1]) + '2', nl(L[2]) + '2']
    elif tex == 'heart':
        lh = [ch(L, 4, nl), ch(L, 2, nl)]
    else:
        lh = [ch(L, 6, nl)]
    rh = [x if any(c.isdigit() for c in x[-2:]) or x.startswith('z') else x for x in rh]
    return rh, lh


def piano_bar(b, prev, ped):
    st, stl = {}, {}
    rh_all, lh_all, beats = [], [], []
    for bi in (0, 1):
        L, R = [s.split() for s in b['h'][bi].split(';')]
        tex = b['tex'][bi]
        rh, lh = piano_beat(tex, L, R, b['key'], st, stl)
        if bi == 0 and b['pd']:
            rh[0] = b['pd'] + rh[0]
        change = (L, R) != prev[0] or bi == 0 and b['h'][0] != prev[1]
        if change:
            lh[0] = ('!ped-up!!ped!' if ped['on'] else '!ped!') + lh[0]
            ped['on'] = True
        prev[0] = (L, R)
        beats.append((tex, L, R, change))
        rh_all += rh
        lh_all += lh
    prev[1] = b['h'][1]
    t0, L0, R0, _ = beats[0]
    t1, L1, R1, c1 = beats[1]
    if t0 == t1 and L0 == L1 and t0 in ('pulse', 'chorale', 'arch', 'fall', 'wave', 'ripple', 'rock', 'final') and not c1:
        lh_all = [lh_all[0][:-1] + '12' if lh_all[0].endswith('6') else lh_all[0]]
        if t0 in ('chorale', 'final') and R0 == R1:
            rh_all = [rh_all[0][:-1] + '12']
    if b['tex'][0] == 'final':
        rh_all = ['!fermata!!arpeggio!' + rh_all[0].replace('!fermata!', '')]
        lh_all = ['!fermata!' + lh_all[0]]
    return ' '.join(rh_all), ' '.join(lh_all)


# ---------------------------------------------------------------- assemble
def build():
    bars = [dict(b, section=name) for name, sec in SECTIONS for b in sec]
    carry, prev, ped = dict(tied=False), [None, None], dict(on=False)
    for b in bars:
        b['eh_abc'], b['kinds'] = eh_bar(b['eh'], b['key'], carry)
        b['rh'], b['lh'] = piano_bar(b, prev, ped)
    return bars


def to_abc(bars):
    sung = sum(k == 's' for b in bars for k in b['kinds'])
    assert sung == len(WORDS), f'{sung} sung notes for {len(WORDS)} syllables'
    head = ['X:1', 'T:Where I Left It', 'C:Scorewright, after the songs of Brian Ellis',
            'M:6/8', 'L:1/16', f'Q:"Lento" 3/8={QUARTER * 2 // 3}', '%%score 1 {2 3}', 'K:D',
            'V:1 clef=treble nm="English Horn" snm="E. H." transpose=-7',
            'V:2 clef=treble nm="Piano" snm="Pno."', 'V:3 clef=bass']
    body, wi, key = [], 0, 'D'
    for s in range(0, len(bars), 4):
        blk = bars[s:s + 4]
        ehs, rhs, lhs = [], [], []
        for b in blk:
            kc = b['key'] != key
            key = b['key']
            ehs.append((f'[K:{WRITTEN[key]}] ' if kc else '') + b['eh_abc'])
            rhs.append((f'[K:{key}] ' if kc else '') + b['rh'])
            lhs.append((f'[K:{key}] ' if kc else '') + b['lh'])
        end = ' |' + ('|' if s + 4 >= len(bars) else '')
        body.append('[V:1] ' + ('[K:A] ' if s == 0 else '') + ' | '.join(ehs) + end)
        kinds = [k for b in blk for k in b['kinds']]
        if 's' in kinds or 'm' in kinds:
            line = ''
            for k in kinds:
                w = {'k': '*', 'm': '_'}.get(k) or WORDS[wi]
                wi += k == 's'
                line += w if line.endswith('-') else (' ' + w if line else w)
            body.append('w: ' + line)
        body.append('[V:2] ' + ' | '.join(rhs) + end)
        body.append('[V:3] ' + ' | '.join(lhs) + end)
    return '\n'.join(head + body) + '\n'


def add_tempi(xml):
    """real tempo changes: <sound tempo> at the given beats of the English horn part, words where named"""
    p1 = xml.index('<part id="P1">')
    div = int(re.search(r'<divisions>(\d+)</divisions>', xml[p1:]).group(1))
    for barno, beat, q, text in sorted(TEMPO, reverse=True):
        ms = xml.index(f'<measure number="{barno}"', p1)
        me = xml.index('</measure>', ms)
        target = beat * 3 * div // 2
        pos, t = None, 0
        for m in re.finditer(r'<note[ >].*?</note>', xml[ms:me], re.S):
            if t >= target:
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


def convert(abc):
    os.makedirs(OUT, exist_ok=True)
    p = f'{OUT}/{NAME}.abc'
    open(p, 'w').write(abc)
    r = subprocess.run([sys.executable, '-W', 'ignore', f'{LAB}/NotaGen/data/abc2xml.py', '-o', OUT, p], capture_output=True, text=True)
    x = f'{OUT}/{NAME}.xml'
    if not os.path.exists(x):
        sys.exit('abc2xml failed: ' + r.stderr[-800:])
    xml = open(x, encoding='utf-8').read()
    xml = xml.replace('<transpose>', '<transpose><diatonic>-4</diatonic>', 1)
    p1 = xml.index('<part id="P1">'); m1 = xml.index('</measure>', p1)
    first = xml[p1:m1]
    if first.count('<key>') > 1:
        k = first.index('<key>'); ke = first.index('</key>', k) + len('</key>')
        xml = xml[:p1] + first[:k] + first[ke:] + xml[m1:]
    xml = add_tempi(xml)
    out = f'{OUT}/{NAME}.musicxml'
    open(out, 'w', encoding='utf-8').write(xml)
    os.remove(x)
    return out, r.stderr.strip()


if __name__ == '__main__':
    bars = build()
    out, log = convert(to_abc(bars))
    print(f'{len(bars)} bars, {len(WORDS)} syllables -> {out}')
    if log:
        print(log[-1500:])
