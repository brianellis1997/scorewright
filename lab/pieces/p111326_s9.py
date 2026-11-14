"""111326 S9 (Nov 13 2026): S8 plus two things from Brian's panel message.
- Violin I starts its doubling of the flute one note earlier: "it should start doubling with that G
  at the quarter note before the E". The pad's B3 in bar 24 ends on beat 1, and G5 on beat 2 is
  slurred into the E5, as in the flute. The slur over the tied E5 alone goes away.
- "The clarinet in B flat sounds out of tune": its pitches are right (measured: every note within
  about 12 cents of concert pitch), but in bar 28 the flute's G natural on beat 2 sounds against the
  clarinet's held G sharp (the third of E7). The clarinet now moves up to A on beat 2, the note it
  goes to in bar 29 anyway, and holds it over the bar line.
usage (whisperer env): python lab/pieces/p111326_s9.py <S7.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import measure_span  # noqa: E402
import p111326_s8  # noqa: E402


def one_note(x, pid, bar, test):
    s0, s1 = measure_span(x, pid, bar)
    notes = [m for m in re.finditer(r'<note[ >].*?</note>', x[s0:s1], re.S) if test(m.group(0))]
    assert len(notes) == 1, f'{pid} bar {bar}: {len(notes)} notes match'
    return s0 + notes[0].start(), s0 + notes[0].end(), notes[0].group(0)


def shorten(note):
    return note.replace('<duration>8</duration>', '<duration>4</duration>', 1).replace('<type>half</type>', '<type>quarter</type>', 1)


def changes(x):
    s, e, b3 = one_note(x, 'P28', 24, lambda n: '<step>B</step>' in n)
    g5 = ('<note><pitch><step>G</step><octave>5</octave></pitch><duration>4</duration><voice>1</voice><type>quarter</type>'
          '<staff>1</staff><notations><slur type="start" number="1"/></notations></note>')
    x = x[:s] + shorten(b3) + g5 + x[e:]
    s, e, e5 = one_note(x, 'P28', 25, lambda n: '<step>E</step>' in n)
    x = x[:s] + re.sub(r'\s*<slur type="start"[^>]*/>', '', e5) + x[e:]
    s, e, gs = one_note(x, 'P6', 28, lambda n: '<step>A</step>' in n)
    a4 = ('<note><pitch><step>B</step><octave>4</octave></pitch><duration>4</duration><tie type="start"/><voice>1</voice>'
          '<type>quarter</type><staff>1</staff><notations><tied type="start"/><slur type="start" number="1"/></notations></note>')
    x = x[:s] + shorten(gs) + a4 + x[e:]
    s, e, b4 = one_note(x, 'P6', 29, lambda n: '<step>B</step>' in n)
    b4 = re.sub(r'\s*<slur type="start"[^>]*/>', '', b4).replace('<tie type="start"/>', '<tie type="stop"/><tie type="start"/>', 1)
    b4 = b4.replace('<tied type="start"/>', '<tied type="stop"/><tied type="start"/>', 1)
    return x[:s] + b4 + x[e:]


def build(x7):
    return changes(p111326_s8.build(x7))


def notes(x7):
    """S9 with its notes and ties, before the marks (what Dorico has after the note entry)"""
    return changes(p111326_s8.notes(x7))


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
