"""111326 S21 (Nov 15 2026): S20 with "div." on the violas, whose chords (his, bars 49-60) are divided
in three. Brian: "at least mark it divisi on the score." Dorico 4 has no div. playing technique, so
in Dorico it is staff text (Plan.text).
usage (whisperer env): python lab/pieces/p111326_s21.py <working.xml> <out.xml>"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s20 as s20  # noqa: E402
from xml_marks import Marks  # noqa: E402

TEXTS = [('P30', 49, 0, 'div.')]
SLURS = s20.SLURS
write_line, notes, harp_48, viola_49, respell_56 = s20.write_line, s20.notes, s20.harp_48, s20.viola_49, s20.respell_56
HARP_CHORD, VIOLA_49, BRASS_SLURS, RUN_SLURS, MELODY_SLURS, PAD_PARTS, ACCENTS = (
    s20.HARP_CHORD, s20.VIOLA_49, s20.BRASS_SLURS, s20.RUN_SLURS, s20.MELODY_SLURS, s20.PAD_PARTS, s20.ACCENTS)
lines = s20.lines


def build(x):
    m = Marks(s20.build(x))
    for pid, bar, onset, words in TEXTS:
        m.words(pid, bar, onset, words, italic=False)
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
