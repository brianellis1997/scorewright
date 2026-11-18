"""111326 S24 (Nov 16 2026), after Brian's message at 21:01 on bars 48-49: "there's still something
missing... I kind of prefer... non on the beat runs, so... sextuplets, 12 in a bar... everything is
just too on the nose... look at what Tchaikovsky does, it's a lot of offbeat fluid stuff that's
flowing"; "a piccolo directly doubling the flute at the same register is just awkward"; "the
clarinets completely drop off, they have a crescendo in bar 48 but then they completely drop off in
bar 49... maybe the bassoons are doubling what the cellos are doing, maybe the clarinets are doubling
what the violas are doing"; the oboe: "maybe whatever the violins are doing". Builds on S23.
- Runs in sixteenth sextuplets that grow out of a held note just after the beat: the flute rises in
  bar 49 and falls in bar 50, rises again in bar 51, and in bar 52 falls (an eighth and a sixteenth
  triplet) while Violin I climbs in the same rhythm, so both arrive on the C sharp before his D.
- Violin I's figures in bars 49, 51 and 52 become an eighth and a sixteenth triplet, so no square
  sixteenths are left under the sextuplets.
- Piccolo: a sextuplet lead-in from beat 2 of bar 48, then a third above the flute (never the
  unison), up to C sharp 7 at most.
- Oboe: doubles Violin II in bars 49-52, as it does before and after.
- E-flat clarinet: its crescendo arrives, A held into bar 49; it rests until his line in bar 53.
  B-flat clarinet: doubles the violas' top note in bars 49-52 (C, B, B, C sharp), then his line.
- Bassoon: the cellos' eighths in bars 49-58 (bars 59-60 keep the held E of the fade).
usage (whisperer env): python lab/pieces/p111326_s24.py <S23.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import accidental, key_of, measure_span, part_span, rebeam, shift, transpose_of  # noqa: E402
from p111326_s5 import parse, tie, write_bar  # noqa: E402
from p111326_s6 import beam_eighths  # noqa: E402
from p111326_s10 import held, put  # noqa: E402
from xml_marks import Marks  # noqa: E402

SIX, THREE = ('6', '4'), ('3', '2')
RUNS = {
    'P1': {48: [('r', 1), ('t', SIX, ['B5', 'C6', 'D6', 'E6', 'F6', 'G6'])],
           49: [('n', 'A6', 1, 'start'), ('t', SIX, ['A6', 'E6', 'F6', 'G6', 'A6', 'B6'], 'stop')],
           50: [('t', SIX, ['C7', 'B6', 'A6', 'G6', 'F#6', 'E6']), ('n', 'D6', 1, 'start')],
           51: [('n', 'D6', 1, 'both'), ('t', SIX, ['D6', 'E6', 'F#6', 'G#6', 'A6', 'B6'], 'stop')],
           52: [('n', 'C#7', Fraction(1, 2)), ('t', THREE, ['B6', 'A6', 'G#6']), ('n', 'E6', 1)]},
    'P2': {49: [('n', 'A5', 1, 'start'), ('t', SIX, ['A5', 'C6', 'D6', 'E6', 'F6', 'G6'], 'stop')],
           50: [('t', SIX, ['A6', 'G6', 'F#6', 'E6', 'D6', 'C6']), ('n', 'B5', 1, 'start')],
           51: [('n', 'B5', 1, 'both'), ('t', SIX, ['B5', 'C#6', 'D6', 'E6', 'F#6', 'G#6'], 'stop')],
           52: [('n', 'A6', Fraction(1, 2)), ('t', THREE, ['G#6', 'F#6', 'E6'])]},
    'P28': {49: [('n', 'A5', Fraction(1, 2)), ('t', THREE, ['G5', 'F5', 'E5'])],
            51: [('n', 'B4', Fraction(1, 2)), ('t', THREE, ['C#5', 'D5', 'E5'])],
            52: [('n', 'F#5', Fraction(1, 2)), ('t', THREE, ['G#5', 'A5', 'B5'])]},
}
WINDOWS = {('P1', 48): (0, 2), ('P1', 49): (0, 2), ('P1', 50): (0, 2), ('P1', 51): (0, 2), ('P1', 52): (0, 2),
           ('P2', 49): (0, 2), ('P2', 50): (0, 2), ('P2', 51): (0, 2), ('P2', 52): (0, 1),
           ('P28', 49): (0, 1), ('P28', 51): (1, 2), ('P28', 52): (0, 1)}
OBOE = {49: ['A4'] * 4, 50: ['B4'] * 4, 51: ['B4'] * 4}
OBOE_52 = ['C#5', 'C#5']
CLARINET = ['C5', 'B4', 'B4', 'C#5']
BASSOON = ['F3', 'G3', 'E3', 'A3', 'D3', 'G3', 'C3', 'C#3', 'D3', 'F3']
SLURS = {'P1': [((48, 1), (49, 0)), ((49, 0), (50, 1)), ((50, 1), (52, 1))],
         'P2': [((49, 0), (50, 1)), ((50, 1), (52, Fraction(5, 6)))],
         'P28': [((49, 0), (49, Fraction(5, 6))), ((51, 1), (52, Fraction(5, 6)))],
         'P6': [((49, 0), (52, 0))]}
DIV = 12
TYPE12 = {24: ('half', 0), 12: ('quarter', 0), 6: ('eighth', 0), 3: ('16th', 0), 2: ('16th', 0)}


SPAN = {'P1': (48, 52), 'P2': (49, 52), 'P28': (49, 52)}


def scale(x, pid, k=3):
    """the run bars of a part in 12 divisions to the quarter (room for sixteenth sextuplets), every
    other bar byte for byte as it was, so the notes there keep their Dorico IDs in the plan"""
    a, z = SPAN[pid]
    for bar in range(a, z + 1):
        s0, s1 = measure_span(x, pid, bar)
        body = re.sub(r'<duration>(\d+)</duration>', lambda m: f'<duration>{int(m.group(1)) * k}</duration>', x[s0:s1])
        body = re.sub(r'<divisions>(\d+)</divisions>', lambda m: f'<divisions>{int(m.group(1)) * k}</divisions>', body)
        if bar == a and '<divisions>' not in body:
            body = f'<attributes><divisions>{4 * k}</divisions></attributes>' + body
        x = x[:s0] + body + x[s1:]
    s0, s1 = measure_span(x, pid, z + 1)
    return x if '<divisions>' in x[s0:s1] else x[:s0] + '<attributes><divisions>4</divisions></attributes>' + x[s0:]


def cleared(x):
    """the score as Dorico has it once the old runs are deleted and the bassoon's F is an eighth"""
    for pid in RUNS:
        x = scale(x, pid)
    for (pid, bar), (a, z) in WINDOWS.items():
        x = splice(x, pid, bar, a * DIV, z * DIV, rest_xml((z - a) * DIV))
    s0, s1 = measure_span(x, 'P7', 49)
    body = x[s0:s1].replace('<duration>8</duration>', '<duration>2</duration>', 1).replace('<type>half</type>', '<type>eighth</type>', 1)
    last = body.rindex('</note>') + len('</note>')
    body = body[:last] + ('<note><rest/><duration>2</duration><voice>1</voice><type>eighth</type><staff>1</staff></note>'
                          '<note><rest/><duration>4</duration><voice>1</voice><type>quarter</type><staff>1</staff></note>') + body[last:]
    return x[:s0] + body + x[s1:]


def copy_bars(x, src, pid, bars):
    """the bars of one part as they are in src"""
    for bar in bars:
        a0, a1 = measure_span(src, pid, bar)
        s0, s1 = measure_span(x, pid, bar)
        x = x[:s0] + src[a0:a1] + x[s1:]
    return x


def note_xml(x, pid, name, dur, state, tied=None, tm=None, tup=None, beams=()):
    d, c = transpose_of(x, pid)
    p = shift(parse(name), -d, -c)
    acc = accidental(p, key_of(x, pid), state)
    typ, dots = TYPE12[dur] if not tm else ('16th', 0)
    kinds = {'start': ['start'], 'stop': ['stop'], 'both': ['stop', 'start'], None: []}[tied]
    out = f'<note><pitch><step>{p[0]}</step>' + (f'<alter>{p[1]}</alter>' if p[1] else '') + f'<octave>{p[2]}</octave></pitch>'
    out += f'<duration>{dur}</duration>' + ''.join(f'<tie type="{k}"/>' for k in kinds)
    out += f'<voice>1</voice><type>{typ}</type>' + '<dot/>' * dots + (f'<accidental>{acc}</accidental>' if acc else '')
    if tm:
        out += f'<time-modification><actual-notes>{tm[0]}</actual-notes><normal-notes>{tm[1]}</normal-notes></time-modification>'
    out += '<staff>1</staff>' + ''.join(f'<beam number="{i + 1}">{b}</beam>' for i, b in enumerate(beams))
    marks = ''.join(f'<tied type="{k}"/>' for k in kinds) + (f'<tuplet type="{tup}" bracket="yes"/>' if tup else '')
    return out + (f'<notations>{marks}</notations>' if marks else '') + '</note>'


def rest_xml(dur):
    typ, _ = TYPE12[dur]
    return f'<note><rest/><duration>{dur}</duration><voice>1</voice><type>{typ}</type><staff>1</staff></note>'


def events_xml(x, pid, events):
    """the notes of a run bar (12 divisions to the quarter)"""
    state, out = {}, []
    for i, ev in enumerate(events):
        if ev[0] == 'r':
            out.append(rest_xml(int(ev[1] * DIV)))
        elif ev[0] == 'n':
            name, q, tied = ev[1], ev[2], (ev[3] if len(ev) > 3 else None)
            nxt = events[i + 1] if i + 1 < len(events) else None
            beams = ('begin',) if q == Fraction(1, 2) and nxt and nxt[0] == 't' and nxt[1] == THREE else ()
            out.append(note_xml(x, pid, name, int(q * DIV), state, tied, beams=beams))
        else:
            _, tm, names = ev[:3]
            tied_first = ev[3] if len(ev) > 3 else None
            after_eighth = i > 0 and events[i - 1][0] == 'n' and events[i - 1][2] == Fraction(1, 2) and tm == THREE
            for k, name in enumerate(names):
                last = k == len(names) - 1
                b2 = 'begin' if k == 0 else 'end' if last else 'continue'
                b1 = ('continue' if not last else 'end') if after_eighth else b2
                out.append(note_xml(x, pid, name, 2, state, tied_first if k == 0 else None, tm,
                                    'start' if k == 0 else 'stop' if last else None, (b1, b2)))
    return ''.join(out)


def splice(x, pid, bar, t0, t1, new):
    """the notes of one voice that start in [t0, t1) divisions give way to new, at the first one's place"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    assert '<backup>' not in body, (pid, bar)
    t, cut, at = 0, [], None
    for m in re.finditer(r'<note[ >].*?</note>', body, re.S):
        s = m.group(0)
        d = int(re.search(r'<duration>(\d+)</duration>', s).group(1))
        start = t
        if '<chord/>' not in s:
            t += d
        if t0 <= start < t1:
            cut.append((m.start(), m.end()))
            at = m.start() if at is None else at
    assert cut, (pid, bar, t0, t1)
    for a, b in reversed(cut):
        body = body[:a] + body[b:]
    body = body[:at] + new + body[at:]
    return x[:s0] + body + x[s1:]


def runs(x):
    for pid in RUNS:
        x = scale(x, pid)
    for (pid, bar), (a, z) in WINDOWS.items():
        x = splice(x, pid, bar, a * DIV, z * DIV, events_xml(x, pid, RUNS[pid][bar]))
    return x


def winds(x):
    for bar, names in OBOE.items():
        x = write_bar(x, 'P3', bar, [(n, 2, None) for n in names])
    state = {}
    x = splice(x, 'P3', 52, 0, 4, ''.join(note_xml4(x, 'P3', n, state) for n in OBOE_52))
    x = write_bar(x, 'P5', 49, [('A5', 8, 'stop')])
    x = tie(x, 'P5', 48, 49)
    for bar, (n, t) in zip(range(49, 53), held(CLARINET)):
        x = write_bar(x, 'P6', bar, [(n, 8, t)])
    for bar, n in zip(range(49, 59), BASSOON):
        x = put(x, 'P7', bar, [(n, 2, None)] * 4)
    x = beam_eighths(x, 'P3', range(49, 53))
    return beam_eighths(x, 'P7', range(49, 59))


def note_xml4(x, pid, name, state):
    d, c = transpose_of(x, pid)
    p = shift(parse(name), -d, -c)
    acc = accidental(p, key_of(x, pid), state)
    return (f'<note><pitch><step>{p[0]}</step>' + (f'<alter>{p[1]}</alter>' if p[1] else '') + f'<octave>{p[2]}</octave></pitch>'
            f'<duration>2</duration><voice>1</voice><type>eighth</type>' + (f'<accidental>{acc}</accidental>' if acc else '') + '<staff>1</staff></note>')


def notes(x):
    return runs(rebeam(winds(x)))


def build(x):
    m = Marks(notes(x))
    m.dynamic('P1', 48, 1, 'f')
    for pid in ('P3', 'P6'):
        m.dynamic(pid, 49, 0, 'f')
    for pid, slurs in SLURS.items():
        for a, z in slurs:
            m.slur(pid, a, z)
    m._notation('P7', 49, 0, plain='<slur type="stop" number="1"/>')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
