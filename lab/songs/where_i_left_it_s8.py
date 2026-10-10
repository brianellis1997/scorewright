"""Where I Left It, S8: S7 with Brian's melody changes (Oct 10 2026): "instead of rising up to
that E, rise up to the C below it, and instead of falling from E to C, fall from C to A; instead of
repeating the A (B, A, A, G), go B, A, F#, G. Adapt the accompaniment if needed."

- verse line 1: "win-dow I" C5 A4 A4 (was E5 C5 C5); "swore I'd turn off" B4 A4 F#4 G4 (was B A A G)
- the same two figures where they recur over the same chords: verse line 2 ("sink, from the" C5,
  A4 B4; "morn-ing I left" C5-B4 A4 F#4 G4) and the chorus ("saved me a seat" B4 A4 F#4 G4).
  Verse line 3 ("song on the stand") keeps its climb to F#5.
- the piano's intro, which plays the tune first, takes the new notes
usage (whisperer env): python lab/songs/where_i_left_it_s8.py"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import where_i_left_it_s6 as s6  # noqa: E402
import where_i_left_it_s7 as s7  # noqa: E402

NAME = 'where_i_left_it_s8'
EDITS = {  # bar number: (old, new) English horn, concert pitch
    6: ('!<)! !>(! E5/8 C5/2 ) !>)! z/2 ( C5/4', '!<)! !>(! C5/8 A4/2 ) !>)! z/2 ( A4/4'),
    7: ('!<(! B4/8 !<)! !>(! A4/4 A4/4', '!<(! B4/8 !<)! !>(! A4/4 F#4/4'),
    10: ('!<)! E5/8 ) z/4 ( C5/2 B4/2', '!<)! C5/8 ) z/4 ( A4/2 B4/2'),
    11: ('!>(! C5/4 M/B4/4 A4/4 A4/4', '!>(! C5/4 M/B4/4 A4/4 F#4/4'),
    29: ('!>(! B4/8 A4/4 A4/4', '!>(! B4/8 A4/4 F#4/4'),
}
INTRO_RH = {2: 'C5/8 A4/4 z4', 3: 'B4/8 A4/4 F#4/4'}


def apply():
    eh, piano = list(s7.EH), list(s7.PIANO)
    for n, (old, new) in EDITS.items():
        assert eh[n - 1] == old, (n, eh[n - 1])
        eh[n - 1] = new
    for n, rh in INTRO_RH.items():
        r, l, d = piano[n - 1]
        piano[n - 1] = (rh, l, d)
    return eh, piano


if __name__ == '__main__':
    s7.EH, s7.PIANO = apply()
    bars = s7.build()
    s6.NAME = NAME
    out, log = s6.convert(s6.to_abc(bars))
    print(f'{len(bars)} bars -> {out}')
    if log:
        print(log[-1500:])
