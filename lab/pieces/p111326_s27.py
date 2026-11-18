"""111326 S27 (Nov 17 2026), Brian on S26: "the flute actually kind of seems to get in the way in
the beginning... let the cor anglais play a bit, the flute can come in at bar 63... remove it
sometimes... 74 is a bit too noisy... maybe shorten 74, and one of the 60s bars as well, the flute is
distracting a bit, just a bit".
- Bars 61-62: the flute's first figure goes; it comes in at bar 63.
- Bars 69-70: its figure goes, so the cor anglais is alone on its high Cs (bars 68 and 70).
- Bar 74: C and D as quarters in place of four eighths, under his slur from bar 73.
- Bar 75: the C on beat 2 becomes A; the C was a minor ninth over the cor anglais B ("make sure we're
  not having any like awkward dissonances between the English and flutes").
usage (whisperer env): python lab/pieces/p111326_s27.py <working.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span  # noqa: E402
from p111326_s10 import put  # noqa: E402
from xml_marks import Marks  # noqa: E402

REST = {61: [(None, 8, None)], 62: [(None, 8, None)], 69: [(None, 8, None)], 70: [(None, 8, None)]}
BAR_74 = [('C5', 4, None), ('D5', 4, None)]


def fix_75(x):
    s0, s1 = measure_span(x, 'P2', 75)
    body = x[s0:s1]
    pat = r'<pitch>\s*<step>C</step>\s*<octave>5</octave>\s*</pitch>'
    assert len(re.findall(pat, body)) == 1, 'bar 75: one C5 expected'
    return x[:s0] + re.sub(pat, '<pitch><step>A</step><octave>4</octave></pitch>', body) + x[s1:]


def notes(x):
    for b, events in REST.items():
        x = put(x, 'P2', b, events)
    return fix_75(put(x, 'P2', 74, BAR_74))


def build(x):
    m = Marks(notes(x))
    m.slur('P2', (73, 0.5), (74, 1))
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
