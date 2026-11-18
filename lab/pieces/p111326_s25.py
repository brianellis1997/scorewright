"""111326 S25 (Nov 17 2026), after Brian's reason on S24: "I really do like the... melody that the
flute is having with the cor anglais... I think it might be like a quarter note too late... whenever
the cor anglais has that dotted quarter it should pick up on the following eighth notes... I just
altered the flute line of bar 61 through 64, look at what I did... make sure we're not having any
like awkward dissonances between the English and flutes... could you do the rest"; "a crescendo from
73 to the middle of 76 and then decrescendo as the flute plays out".
- Flute, bars 65-72: his figure. While the cor anglais holds its dotted quarter, three eighths from
  beat 1.5 (rising in 65 and 69, falling in 67 and 71), then a dotted quarter on the next downbeat as
  the cor anglais moves on; it moves in tenths and sixths with the cor anglais, stays above it, and
  ends on the downbeat of bar 72 (F, an octave over the cor anglais), before its A and B.
- Bar 61: his F on beat 2 becomes D (E, D, E): the F was a minor ninth over the held cor anglais E.
- Bars 73-77: his line swells to the D in the middle of bar 76, then fades to its end.
usage (whisperer env): python lab/pieces/p111326_s25.py <working.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import put  # noqa: E402
from xml_marks import Marks  # noqa: E402

FIGURES = {65: ('D5', 'E5', 'F5', 'G5'), 67: ('A5', 'G5', 'F5', 'E5'), 69: ('F5', 'G5', 'A5', 'G5'), 71: ('B5', 'A5', 'G5', 'F5')}


def bars():
    out = {}
    for b, (a, c, d, land) in FIGURES.items():
        out[b] = [(None, 2, None), (a, 2, None), (c, 2, None), (d, 2, None)]
        out[b + 1] = [(land, 4, None), (None, 4, None)] if b == 71 else [(land, 6, None), (None, 2, None)]
    return out


def fix_61(x):
    s0, s1 = measure_span(x, 'P2', 61)
    body = x[s0:s1]
    pat = r'<pitch>\s*<step>F</step>\s*<octave>5</octave>\s*</pitch>'
    assert len(re.findall(pat, body)) == 1, 'bar 61: one F5 expected'
    return x[:s0] + re.sub(pat, '<pitch><step>D</step><octave>5</octave></pitch>', body) + x[s1:]


def notes(x):
    x = fix_61(x)
    for b, events in bars().items():
        x = put(x, 'P2', b, events)
    return beam_eighths(x, 'P2', range(65, 73))


def build(x):
    m = Marks(notes(x))
    for b in FIGURES:
        m.slur('P2', (b, 0.5), (b + 1, 0))
    m.hairpin('P2', (73, 0.5), (76, 1), 'crescendo')
    m.hairpin('P2', (76, 1), (77, 1), 'diminuendo')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
