"""Where I Left It, S9: S8 revised after his verdict (Oct 10 2026): "great work; the accompaniment
is much better. Still some harmonic thing missing: in my minor-key music there's a hint of the
relative major: a D major chord hinting at resolving to the relative major, and maybe it does, or
a false resolution to the minor v (B minor). That's what Rachmaninoff does. Not constantly, just
hints." Also: the piano's repeated diminuendos fade it to silence (bug); the chorus figure is
"on the nose" from his Song Study no 3; the four slow bars before the chorus were drawn out.

His archive (find_progression.py): i VII III 376 times, i VII v 323 times, e.g. The Ocean
(Gm9 F7b9 Bbmaj9), A set of 5 Nocturnes (Abm7 F#7/Bb B), 117 Art Song (Bbm Ab/C Fm).

- verse line 2: Em, D7/F#, G, Em. The relative major arrives once, under "morning I left", where
  the C-B sigh becomes a 4-3 suspension over G.
- verse line 4: Em, Am, D/F#, D. The breath is held on D major, and the piano's one-bar answer
  falls to B minor (the false resolution) before the dominant. The four bars of B7 are gone and
  the transition is a bar shorter.
- chorus: the left hand flows in triplet eighths. The right hand has its own counter-line that
  moves while the horn holds and holds while it moves; the second time it doubles the horn.
  No piano hairpins.
usage (whisperer env): python lab/songs/where_i_left_it_s9.py"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import where_i_left_it_s6 as s6  # noqa: E402
import where_i_left_it_s7 as s7  # noqa: E402
import where_i_left_it_s8 as s8  # noqa: E402

NAME = 'where_i_left_it_s9'

LH6 = {'Em': 'E2 B2 E3 G3 E3 B2', 'Am7': 'A1 E2 A2 C3 A2 E2', 'D7': 'D2 A2 C3 F#3 C3 A2', 'Gmaj7': 'G1 D2 G2 B2 G2 D2',
       'Cmaj7': 'C2 G2 C3 E3 C3 G2', 'F#o7': 'F#1 C2 F#2 A2 F#2 C2', 'B7': 'B1 F#2 A2 D#3 A2 F#2'}


def flow(ch):
    a, b, c, d, e, f = LH6[ch].split()
    half = f'(3 {a}/2 {b}/2 {c}/2 (3 {d}/2 {e}/2 {f}/2'
    return half + ' ' + half


COUNTER = ['G4/4 F#4/4 E4/8', 'A3/4 C4/4 E4/8', 'F#3/4 A3/4 C4/8', 'B3/4 D4/4 F#4/8',
           'E4/4 G4/4 E4/8', 'C4/4 E4/4 C4/8', 'D#4/4 F#4/4 D#4/8', 'E4/4 B3/4 E4/4 z4']
CHORDS = ['Em', 'Am7', 'D7', 'Gmaj7', 'Cmaj7', 'F#o7', 'B7', 'Em']


def apply():
    eh, piano = s8.apply()
    piano[9] = ('A3/2 C4/2 D4/2 C4/2 A3/8', '[F#1 D2]16', None)
    piano[10] = ('[G3 B3]16', '[G1 D2]16', None)
    piano[17] = ('[A3 C4]8 (3 E4/2 C4/2 A3/2 z4', '[A1 E2]16', None)
    piano[18] = ('[A3 D4]16', '[F#1 D2]16', None)
    piano[19] = ('[F#3 A3 D4]8 z8', '[D2 A2]8 z8', None)
    piano[20] = ('[D4 F#4]4 [B3 D4]4 [F#3 A3]4 z4', 'B1/4 B2/4 B1/4 z4', '!p!')
    del piano[21]
    del eh[20]
    first = 21
    for i, ch in enumerate(CHORDS):
        piano[first + i] = (COUNTER[i], flow(ch), '!mp!' if i == 0 else None)
    for i, ch in enumerate(CHORDS):
        r, l, d = piano[first + 8 + i]
        if i < 6:
            l = flow(ch)
        piano[first + 8 + i] = (r, l, d)
    return eh, piano


if __name__ == '__main__':
    eh, piano = apply()
    assert len(eh) == len(piano) == 37, (len(eh), len(piano))
    s7.EH, s7.PIANO = eh, piano
    bars = s7.build()
    s6.NAME = NAME
    out, log = s6.convert(s6.to_abc(bars))
    print(f'{len(bars)} bars -> {out}')
    if log:
        print(log[-1500:])
