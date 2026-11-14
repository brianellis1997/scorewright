"""111326, Brian's romantic orchestral sketch in Dorico 4 (Nov 13 2026). S1 adds only the marks he
asked for, on Dorico's own MusicXML export, so every note and Dorico's encoding stay as they are
and the passage can go back into his project.

His words: "make the flute and oboe stand out. The oboe will naturally stand out at this register,
but the French horns are going to overpower the oboe if no dynamics are enforced... the strings
need to be pianissimo... the main theme piano, maybe mezzo piano for the oboe, and the
accompaniment piano, more soft, so the melody really rings out... mimic the oboe's slurring for
the flute... the quarter note is somewhere in between a normal note and a staccato, a lot of
breath, so the wind player can breathe after it and get into the flowing rhythm of bar 10... the
dynamics follow the melody: very subtle in the beginning, the climax at the top G in bar 10, then
a decrescendo as it goes down."

The sketch, in concert pitch (2/4, quarter = 72): the oboe states the theme in bars 7-17 over horn
chords F, G, Em/G, E/G#, F/A, G/B, Em, E, F (A minor VI VII v V, one chord a bar). The flute takes
the theme on the upbeat of bar 15 while the oboe finishes its phrase, and the horns dovetail into
Violin I on the same F major chord at bar 16.

- oboe and flute: mp; a portato (tenuto-staccato) on each quarter that ends a slurred upbeat
  (oboe bars 8, 9, 12, 13; flute 16, 17, 20, 21); a swell to each high point and down after it
- flute: the oboe's slur groups, bar for bar; its last two notes (G-F) slurred as the oboe's A-G
- oboe: down to p at bar 17 under the flute's entry
- horns: p; down to pp into the dovetail chord; Violin I enters pp on that chord
usage (whisperer env): python lab/pieces/p111326_s1.py <dorico export.xml> <out.musicxml>"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xml_marks import Marks, pitches  # noqa: E402

FL, OB, HN, VN = 'P2', 'P3', 'P9', 'P28'


def mark(xml):
    m = Marks(xml)
    m.dynamic(OB, 7, 1, 'mp')
    for bar in (8, 9, 12, 13):
        m.articulation(OB, bar, 0, 'detached-legato')
    m.hairpin(OB, (9, 1), (10, 1), 'crescendo')
    m.hairpin(OB, (10, 1), (12, 0), 'diminuendo')
    m.hairpin(OB, (13, 1), (14, 1), 'crescendo')
    m.hairpin(OB, (14, 1), (17, 0), 'diminuendo')
    m.dynamic(OB, 17, 0, 'p')

    m.dynamic(FL, 15, 1, 'mp')
    for start, stop in (((15, 1), (16, 0)), ((16, 1), (17, 0)), ((17, 1), (19, 0.5)), ((19, 1), (20, 0)),
                        ((20, 1), (21, 0)), ((21, 1), (23, 0.5)), ((23, 1), (24, 0))):
        m.slur(FL, start, stop)
    for bar in (16, 17, 20, 21):
        m.articulation(FL, bar, 0, 'detached-legato')
    m.hairpin(FL, (17, 1), (18, 1), 'crescendo')
    m.hairpin(FL, (18, 1), (20, 0), 'diminuendo')
    m.hairpin(FL, (21, 1), (23, 1), 'crescendo')
    m.hairpin(FL, (23, 1), (24, None), 'diminuendo')

    m.dynamic(HN, 8, 0, 'p')
    m.hairpin(HN, (15, 0), (16, 0), 'diminuendo')
    m.dynamic(HN, 16, 0, 'pp')

    m.dynamic(VN, 16, 0, 'pp')
    return m.text()


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    xml = open(src, encoding='utf-8').read()
    new = mark(xml)
    assert pitches(new) == pitches(xml), 'a note changed'
    open(out, 'w', encoding='utf-8').write(new)
    print(f'{out}: {len(new) - len(xml)} characters of marks added, every note unchanged')
