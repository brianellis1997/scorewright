"""111326 S2 (Nov 13 2026): the chords Brian wrote on one staff, spread across the section, and the
eighths in 2/4 beamed in pairs. His words: "these multi-chord things in the horns and the strings
are obviously meant to be exploded across the instruments. The horn can only play one note at a
time... horns 1 and 2 play the top two notes, and a similar instrument, the Wagner tuba or a
trombone, takes the lower note... the violin can't play that low F: the first and second violins
take the top notes, and the viola takes the bottom note... I wanted a wind vibe." And: "in 2/4, four
eighth notes should be two groups of two eighth notes."

- horns, bars 8-16: Horn 1 the top note, Horn 2 the middle, the Wagner tuba the bottom. The Wagner
  tuba is played by horn players and was made to blend with horns, so the chord keeps one soft
  colour; a trombone at p is brighter. Horn 1's slurs, p, hairpin and pp go to all three.
- strings, bars 16-24: Violin I the top note, Violin II the middle, the viola the bottom (E3 to C4,
  low for a violin, the middle of the viola). The pp goes to all three.
- every bar of four eighths: two beamed pairs.
Every pitch is planned at concert pitch. The file keeps Dorico's own encoding (horns written a fifth
higher, the Wagner tuba a whole step higher, with <transpose>), so it goes back into Dorico as is.
usage (whisperer env): python lab/pieces/p111326_s2.py <in.xml> <out.musicxml>"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from xml_marks import pitches  # noqa: E402

STEPS = 'CDEFGAB'
PC = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)
SPREAD = (('P9', ('P10', 'P11'), range(8, 17)), ('P28', ('P29', 'P30'), range(16, 25)))
ITEM = re.compile(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>|<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>', re.S)
ACC = {1: 'sharp', -1: 'flat', 0: 'natural', 2: 'double-sharp', -2: 'flat-flat'}


def part_span(x, pid):
    m = re.search(rf'<part id="{pid}">', x)
    return m.end(), x.index('</part>', m.end())


def measure_span(x, pid, bar):
    ps, pe = part_span(x, pid)
    m = re.compile(rf'<measure number="{bar}"[^>]*>').search(x, ps, pe)
    return m.end(), x.index('</measure>', m.end())


def transpose_of(x, pid):
    ps, pe = part_span(x, pid)
    t = re.search(r'<transpose\b.*?</transpose>', x[ps:pe], re.S)
    if not t:
        return 0, 0
    g = lambda tag: int((re.search(rf'<{tag}>(-?\d+)</{tag}>', t.group(0)) or [0, 0])[1])
    return g('diatonic') + 7 * g('octave-change'), g('chromatic') + 12 * g('octave-change')


def key_of(x, pid):
    ps, pe = part_span(x, pid)
    return int(re.search(r'<fifths>(-?\d+)</fifths>', x[ps:pe]).group(1))


def shift(p, d, c):
    step, alter, octave = p
    di = octave * 7 + STEPS.index(step) + d
    mi = 12 * (octave + 1) + PC[step] + alter + c
    s, o = STEPS[di % 7], di // 7
    return s, mi - (12 * (o + 1) + PC[s]), o


def pitch_of(note):
    m = re.search(r'<step>(\w)</step>(?:\s*<alter>(-?\d+)</alter>)?\s*<octave>(\d+)</octave>', note)
    return m.group(1), int(m.group(2) or 0), int(m.group(3))


def midi(p):
    return 12 * (p[2] + 1) + PC[p[0]] + p[1]


def key_alter(step, fifths):
    if fifths > 0 and step in 'FCGDAEB'[:fifths]:
        return 1
    if fifths < 0 and step in 'BEADGCF'[:-fifths]:
        return -1
    return 0


def accidental(p, fifths, state):
    step, alter, octave = p
    if state.get((step, octave), key_alter(step, fifths)) == alter:
        return ''
    state[(step, octave)] = alter
    return ACC[alter]


def items(body):
    out = []
    for m in ITEM.finditer(body):
        s = m.group(0)
        if s.startswith('<note') and '<chord/>' in s and out and out[-1][0] == 'group':
            out[-1][1].append(s)
        elif s.startswith('<note'):
            out.append(['group', [s]])
        else:
            out.append(['attr' if s.startswith('<attributes') else 'other', s])
    return out


def strip_slurs(note):
    note = re.sub(r'\s*<slur [^>]*/>', '', note)
    return re.sub(r'\s*<notations>\s*</notations>', '', note)


def with_notations(note, extra):
    if not extra:
        return note
    if '<notations>' in note:
        return note.replace('</notations>', ''.join(extra) + '</notations>', 1)
    at = note.rfind('</note>')
    return note[:at] + '<notations>' + ''.join(extra) + '</notations>' + note[at:]


def make_note(src, p, acc):
    dur = re.search(r'<duration>(\d+)</duration>', src).group(1)
    typ = re.search(r'<type>(\w+)</type>', src).group(1)
    step, alter, octave = p
    return (f'<note><pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter else '') + f'<octave>{octave}</octave></pitch>'
            f'<duration>{dur}</duration><voice>1</voice><type>{typ}</type>' + '<dot/>' * src.count('<dot/>')
            + (f'<accidental>{acc}</accidental>' if acc else '') + '<staff>1</staff></note>')


def make_rest(src):
    dur = re.search(r'<duration>(\d+)</duration>', src).group(1)
    typ = re.search(r'<type>(\w+)</type>', src)
    return f'<note><rest/><duration>{dur}</duration><voice>1</voice>' + (f'<type>{typ.group(1)}</type>' if typ else '') + '<staff>1</staff></note>'


def spread(x, src, dests, bars):
    tr = {p: transpose_of(x, p) for p in (src,) + dests}
    keys = {p: key_of(x, p) for p in dests}
    edits = []
    for bar in bars:
        s0, s1 = measure_span(x, src, bar)
        new_src, new_dest, state = [], {d: [] for d in dests}, {d: {} for d in dests}
        for kind, val in items(x[s0:s1]):
            if kind != 'group':
                new_src.append(val)
                if kind == 'other':
                    for d in dests:
                        new_dest[d].append(val)
                continue
            if '<rest' in val[0]:
                new_src.append(val[0])
                for d in dests:
                    new_dest[d].append(make_rest(val[0]))
                continue
            chord = sorted(val, key=lambda n: -midi(shift(pitch_of(n), *tr[src])))
            if len(chord) != 1 + len(dests):
                raise SystemExit(f'{src} bar {bar}: a chord of {len(chord)} notes for {1 + len(dests)} players')
            slurs = [s for n in val for s in re.findall(r'<slur [^>]*/>', n)]
            new_src.append(with_notations(strip_slurs(chord[0]).replace('<chord/>', ''), slurs))
            for d, n in zip(dests, chord[1:]):
                concert = shift(pitch_of(n), *tr[src])
                written = shift(concert, -tr[d][0], -tr[d][1])
                new_dest[d].append(with_notations(make_note(n, written, accidental(written, keys[d], state[d])), slurs))
        edits.append((s0, s1, ''.join(new_src)))
        for d in dests:
            d0, d1 = measure_span(x, d, bar)
            old = items(x[d0:d1])
            assert all(k != 'group' or '<rest' in v[0] for k, v in old), f'{d} bar {bar} is not empty'
            edits.append((d0, d1, ''.join([v for k, v in old if k != 'group'] + new_dest[d])))
    for s, e, t in sorted(edits, reverse=True):
        x = x[:s] + t + x[e:]
    return x


def rebeam(x, beat=4):
    """eighths beamed per quarter beat (Dorico exports 4 divisions to a quarter)"""
    def fix(m):
        body, t, beats = m.group(2), 0, {}
        for n in re.finditer(r'<note[ >].*?</note>', body, re.S):
            s = n.group(0)
            if '<chord/>' in s:
                continue
            if '<type>eighth</type>' in s and '<beam number="1">' in s:
                beats.setdefault(t // beat, []).append(n)
            d = re.search(r'<duration>(\d+)</duration>', s)
            t += int(d.group(1)) if d else 0
        reps = []
        for group in beats.values():
            for i, n in enumerate(group):
                state = 'begin' if i == 0 else 'end' if i == len(group) - 1 else 'continue'
                new = re.sub(r'\s*<beam number="1">\w+</beam>', '', n.group(0)) if len(group) == 1 else \
                    re.sub(r'<beam number="1">\w+</beam>', f'<beam number="1">{state}</beam>', n.group(0))
                reps.append((n.start(), n.end(), new))
        for s, e, t2 in sorted(reps, reverse=True):
            body = body[:s] + t2 + body[e:]
        return m.group(1) + body + '</measure>'
    return re.sub(r'(<measure number="\d+"[^>]*>)(.*?)</measure>', fix, x, flags=re.S)


def sounding(x, pid, bars):
    tr = transpose_of(x, pid)
    out = []
    for bar in bars:
        s0, s1 = measure_span(x, pid, bar)
        out += sorted(midi(shift(pitch_of(n), *tr)) for n in re.findall(r'<note[ >].*?</note>', x[s0:s1], re.S) if '<rest' not in n)
    return out


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    x0 = open(src, encoding='utf-8').read()
    x = x0
    for s, dests, bars in SPREAD:
        x = spread(x, s, dests, bars)
    x = rebeam(x)
    p0, p1 = pitches(x0), pitches(x)
    for s, dests, bars in SPREAD:
        assert sorted(sounding(x0, s, bars)) == sorted(sum((sounding(x, p, bars) for p in (s,) + dests), [])), f'{s}: the chords changed'
        for p in (s,) + dests:
            p0.pop(p), p1.pop(p)
    assert p0 == p1, 'a part outside the spread changed'
    open(out, 'w', encoding='utf-8').write(x)
    print(f'{out}: chords spread, beams in pairs, same sounding notes')
