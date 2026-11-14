"""111326 S5 (Nov 13 2026), from Brian's panel message after S4.
- Harmony held over the bar line: "if they're not changing their note, just hold them over" (horns
  9-15, strings 17-23, the new clarinet choir).
- The oboe after it hands the melody to the flute: "should it have a contrapuntal line to the
  melody? what do you think". A slow line under the flute, mostly in contrary motion, that holds
  while the flute moves and hands over to the clarinets on the downbeat of bar 24.
- His new section (bars 24-31: flute melody, harmony sketched as chords on the Eb clarinet): the
  chords spread over Eb clarinet, Bb clarinet and bassoon; Violin I doubles the flute ("maybe we
  want the melody doubled with a string"); pizzicato ("plucks on the offbeats... light harmony
  spelled out in those chords"): cellos on the beat, Violin II and violas on the offbeats.
Built from Dorico's export; pitches are planned at concert pitch and written in Dorico's encoding.
usage (whisperer env): python lab/pieces/p111326_s5.py <dorico_export.xml> <out.xml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from p111326_s2 import accidental, key_of, measure_span, pitch_of, rebeam, shift, spread, transpose_of, with_notations  # noqa: E402
from xml_marks import Marks  # noqa: E402

DIV = 4
TYPE = {2: ('eighth', 0), 3: ('eighth', 1), 4: ('quarter', 0), 6: ('quarter', 1), 8: ('half', 0)}
NOTE_RE = re.compile(r'<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>', re.S)

OBOE = {  # concert pitch; tie: 'start', 'stop' or 'both'
    18: [('G4', 4, 'stop'), ('A4', 4, None)],
    19: [('B4', 4, None), ('G#4', 4, None)],
    20: [('A4', 8, None)],
    21: [('G4', 8, 'start')],
    22: [('G4', 4, 'stop'), ('E4', 4, 'start')],
    23: [('E4', 8, 'stop')],
    24: [('F4', 4, None), (None, 4, None)],
}
VIOLIN_I = {
    24: [('E5', 8, 'start')],
    25: [('E5', 4, 'stop'), ('G5', 4, None)],
    26: [('E5', 8, 'start')],
    27: [('E5', 4, 'stop'), ('G5', 4, None)],
    28: [('E5', 2, None), ('D5', 6, None)],
    29: [('C5', 8, None)],
    30: [('B4', 8, 'start')],
    31: [('B4', 4, 'stop'), (None, 4, None)],
}
CHORDS = {24: ('A4', 'F4', 'C4'), 25: ('A4', 'F4', 'C#4'), 26: ('A4', 'F4', 'D4'), 27: ('B4', 'G#4', 'D4'),
          28: ('C5', 'A4', 'E4'), 29: ('C5', 'A4', 'F#4'), 30: ('B4', 'G4', 'D4'), 31: ('G#4', 'E4', 'D4')}
TIES = {
    'P9': [(10, 11), (13, 14)],
    'P10': [(9, 10), (10, 11), (14, 15)],
    'P11': [(9, 10), (13, 14), (14, 15)],
    'P28': [(17, 18), (22, 23)],
    'P30': [(17, 18), (22, 23)],
    'P3': [(17, 18)],
    'P5': [(24, 25), (25, 26), (28, 29)],
    'P6': [(24, 25), (25, 26), (28, 29)],
    'P7': [(26, 27), (30, 31)],
}


def parse(name):
    m = re.match(r'([A-G])(#|b)?(\d)', name)
    return m.group(1), {'#': 1, 'b': -1}.get(m.group(2), 0), int(m.group(3))


def concert_of(x, pid, note):
    return shift(pitch_of(note), *transpose_of(x, pid))


def voice_one(x, pid, bar):
    """[(onset in divisions, start, end, note text)] of the notes and rests that start an item"""
    s0, s1 = measure_span(x, pid, bar)
    t, out = 0, []
    for m in NOTE_RE.finditer(x[s0:s1]):
        s = m.group(0)
        d = int((re.search(r'<duration>(\d+)</duration>', s) or [0, 0])[1])
        if s.startswith('<backup'):
            t -= d
        elif s.startswith('<forward'):
            t += d
        elif '<chord/>' not in s:
            out.append((t, s0 + m.start(), s0 + m.end(), s))
            t += d
    return out


def add_tie(note, kind):
    note = note.replace('</duration>', f'</duration><tie type="{kind}"/>', 1)
    return with_notations(note, [f'<tied type="{kind}"/>'])


def tie(x, pid, b0, b1):
    """tie the last note of bar b0 to the first note of bar b1 (same pitch)"""
    last, first = voice_one(x, pid, b0)[-1], voice_one(x, pid, b1)[0]
    assert '<rest' not in last[3] and '<rest' not in first[3], f'{pid} {b0}-{b1}: a rest'
    assert pitch_of(last[3]) == pitch_of(first[3]), f'{pid} {b0}-{b1}: {pitch_of(last[3])} and {pitch_of(first[3])}'
    x = x[:first[1]] + add_tie(first[3], 'stop') + x[first[2]:]
    return x[:last[1]] + add_tie(last[3], 'start') + x[last[2]:]


def write_bar(x, pid, bar, events):
    """replace a bar of rests with events [(concert name or None, divisions, tie)] in Dorico's encoding"""
    d, c = transpose_of(x, pid)
    fifths, state = key_of(x, pid), {}
    old = voice_one(x, pid, bar)
    assert all('<rest' in n for _, _, _, n in old), f'{pid} bar {bar} is not empty'
    out = []
    for name, dur, tied in events:
        typ, dots = TYPE[dur]
        if name is None:
            out.append(f'<note><rest/><duration>{dur}</duration><voice>1</voice><type>{typ}</type>{"<dot/>" * dots}<staff>1</staff></note>')
            continue
        step, alter, octave = shift(parse(name), -d, -c)
        acc = accidental((step, alter, octave), fifths, state)
        kinds = {'start': ['start'], 'stop': ['stop'], 'both': ['stop', 'start'], None: []}[tied]
        out.append(f'<note><pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter else '') + f'<octave>{octave}</octave></pitch>'
                   f'<duration>{dur}</duration>' + ''.join(f'<tie type="{k}"/>' for k in kinds) +
                   f'<voice>1</voice><type>{typ}</type>{"<dot/>" * dots}' + (f'<accidental>{acc}</accidental>' if acc else '') +
                   '<staff>1</staff>' + (f'<notations>{"".join(f"<tied type=\"{k}\"/>" for k in kinds)}</notations>' if kinds else '') + '</note>')
    start, end = old[0][1], old[-1][2]
    return x[:start] + ''.join(out) + x[end:]


def respell(x, pid, bar, old, new):
    """one chord note of a bar, written pitch old -> new (same sound), e.g. Eb clarinet C##4 -> D4"""
    s0, s1 = measure_span(x, pid, bar)
    body = x[s0:s1]
    pat = re.compile(r'<pitch>\s*<step>{}</step>\s*<alter>{}</alter>\s*<octave>{}</octave>\s*</pitch>'.format(*old))
    assert len(pat.findall(body)) == 1, f'{pid} bar {bar}: {old} not found once'
    body = pat.sub('<pitch><step>{}</step><octave>{}</octave></pitch>'.format(new[0], new[2]), body)
    body = re.sub(r'(<step>{}</step><octave>{}</octave></pitch>.*?)<accidental>[^<]*</accidental>'.format(new[0], new[2]), r'\1', body, count=1, flags=re.S)
    return x[:s0] + body + x[s1:]


def common(x):
    """what S5 and S6 share: the clarinet choir, the oboe line, Violin I's melody, every held note"""
    x = respell(x, 'P5', 25, ('C', 2, 4), ('D', 0, 4))
    x = spread(x, 'P5', ('P6', 'P7'), range(24, 32))
    for bar, (top, mid, low) in CHORDS.items():
        got = [concert_of(x, pid, voice_one(x, pid, bar)[0][3]) for pid in ('P5', 'P6', 'P7')]
        assert got == [parse(top), parse(mid), parse(low)], f'bar {bar}: {got}'
    for bar, events in OBOE.items():
        x = write_bar(x, 'P3', bar, events)
    s, e = voice_one(x, 'P3', 17)[-1][1:3]
    x = x[:s] + add_tie(x[s:e], 'start') + x[e:]
    s, e = voice_one(x, 'P28', 24)[0][1:3]
    s2, e2 = voice_one(x, 'P28', 24)[-1][1:3]
    x = x[:s] + '<note><rest/><duration>8</duration><voice>1</voice><type>half</type><staff>1</staff></note>' + x[e2:]
    for bar, events in VIOLIN_I.items():
        x = write_bar(x, 'P28', bar, events)
    b23 = voice_one(x, 'P28', 23)[-1]
    x = x[:b23[1]] + with_notations(b23[3], ['<slur type="stop" number="1"/>']) + x[b23[2]:]
    for pid, pairs in TIES.items():
        for b0, b1 in pairs:
            if pid == 'P3':
                continue
            x = tie(x, pid, b0, b1)
    return x


def common_marks(m):
    m.slur('P3', (18, 1.0), (20, 0))
    m.slur('P3', (21, 0), (24, 0))
    m.hairpin('P3', (23, 0), (24, 0), 'diminuendo')
    m.dynamic('P3', 24, 0, 'pp')
    m.dynamic('P28', 24, 0, 'p')
    for pid in ('P5', 'P6', 'P7'):
        m.dynamic(pid, 24, 0, 'p')
        m.slur(pid, (24, 0), (27, 0))
        m.slur(pid, (28, 0), (31, 0))


def build(x):
    x = common(x)
    for bar, (top, mid, low) in CHORDS.items():
        x = write_bar(x, 'P31', bar, [(low[:-1] + str(int(low[-1]) - 1), 2, None), (None, 2, None), (None, 4, None)])
        if bar > 24:
            x = write_bar(x, 'P29', bar, [(None, 2, None), (top, 2, None), (None, 2, None), (top, 2, None)])
            x = write_bar(x, 'P30', bar, [(None, 2, None), (mid, 2, None), (None, 2, None), (mid, 2, None)])
    x = rebeam(x)
    m = Marks(x)
    common_marks(m)
    m.slur('P28', (24, 0), (25, 1.0))
    m.slur('P28', (26, 0), (27, 1.0))
    m.slur('P28', (28, 0), (29, 0))
    m.words('P31', 24, 0, 'pizz.', italic=False)
    m.dynamic('P31', 24, 0, 'p')
    for pid in ('P29', 'P30'):
        m.words(pid, 25, 0.5, 'pizz.', italic=False)
        m.dynamic(pid, 25, 0.5, 'p')
    return m.text()


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    out = build(open(src, encoding='utf-8').read())
    open(dst, 'w', encoding='utf-8').write(out)
    print('wrote', dst)
