"""111326 S3 (Nov 13 2026): S2 with slurs in the strings. Brian on S2: "okay, now we're talking, this
is a bit better, but the strings need their slurs as well." Violin I, Violin II and the viola are
slurred over each phrase, bars 16-19 and 20-24, as his horns are over bars 8-11 and 12-16: the same
two halves of the theme (F G Em E, then F G Em E F).
usage (whisperer env): python lab/pieces/p111326_s3.py <S2.musicxml> <out.musicxml>"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xml_marks import Marks, pitches  # noqa: E402

if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    x = open(src, encoding='utf-8').read()
    m = Marks(x)
    for pid in ('P28', 'P29', 'P30'):
        m.slur(pid, (16, 0), (19, 1))
        m.slur(pid, (20, 0), (24, 0))
    new = m.text()
    assert pitches(new) == pitches(x), 'a note changed'
    open(out, 'w', encoding='utf-8').write(new)
    print(f'{out}: six slurs added in the strings, every note unchanged')
