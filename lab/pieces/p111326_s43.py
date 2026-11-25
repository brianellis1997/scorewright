"""111326 S43 (Nov 25 2026): S42 again, after Brian's notes on it: "some instruments just drop out, like the
horns just completely drop out... I'd like for them to fade out or dovetail into the violins, just hold out
for an eighth or quarter note as the violins take over that harmonic space"; "once the oboe comes in it would
be nice to have some more rhythmic pace ramping up, not super... some percussive hits... more pizzicato in
the strings... offbeat blows from some of the instruments... maybe a harp, not a fluid thing". Builds on his
export of Nov 25 (the same notes as S42's).
- Bar 118: horn 1 ties its last C into a quarter note, where Violin II takes the same C. Horn 2 (A to A flat),
  the Wagner tuba (E to F) and the trombone (C to A flat) slur by step into a quarter note of the F minor
  chord and fade to pp on it, while Violin II and the violas come in.
- From the oboe's entry a light pulse builds: the harp plucks dry chords on the off-beats, once a bar in bars
  122-123 and twice from bar 124; the bassoon adds staccato off-beats from bar 124 and the clarinet from bar
  126; the pizzicato basses and contrabassoon play both beats from bar 124. All p.
- The rest as in S42.
usage (whisperer env): python lab/pieces/p111326_s43.py <export.xml> <out.xml>"""
import os, re, sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import p111326_s5  # noqa: E402
from p111326_s2 import measure_span  # noqa: E402
from p111326_s5 import tie  # noqa: E402
from p111326_s10 import put  # noqa: E402
import p111326_s33 as s33  # noqa: E402
import p111326_s42 as s42  # noqa: E402
from xml_marks import Marks  # noqa: E402

p111326_s5.TYPE.setdefault(1, ('16th', 0))
H = Fraction(1, 2)
INTO_118 = {'P10': 'Ab3', 'P11': 'F3', 'P14': 'Ab2'}
FADE_FROM = {'P10': (117, 0), 'P11': (115, 0), 'P14': (117, 0)}
OFF = lambda a, b: [(None, 2, None), (a, 2, None), (None, 2, None), (b, 2, None)]
BASSOON = {124: OFF('C#3', 'E3'), 125: OFF('D3', 'F3'), 126: OFF('Db3', 'F3'), 127: OFF('Db3', 'Fb3')}
CLARINET = {126: OFF('F4', 'F4'), 127: OFF('Fb4', 'Fb4')}
BOTH_BEATS = {124: 'A2', 125: 'A2', 126: 'Bb2', 127: 'Bb2'}
HARP = {122: (['E4', 'A4'], ['A2'], 1), 123: (['D4', 'F4', 'A4'], ['A2'], 1), 124: (['E4', 'A4'], ['A2'], 2),
        125: (['D4', 'F4', 'A4'], ['A2'], 2), 126: (['F4'], ['Bb2'], 2), 127: (['Db4'], ['Bb2'], 2)}


def lines():
    ls = s42.lines()
    for pid, n in INTO_118.items():
        ls[pid][118] = [(n, 4, None), (None, 4, None)]
    for pid in ('P32', 'P8'):
        for b, n in BOTH_BEATS.items():
            ls[pid][b] = [(n, 4, None), (n, 4, None)]
    ls['P7'] = dict(BASSOON)
    ls['P6'] = dict(CLARINET)
    ls['P9'] = {118: [('C4', 4, None), (None, 4, None)]}
    return ls


def harp_events(bar, staff):
    """[(names or None, divisions)]: the off-beat chords of one bar (once: on beat 2.5; twice: 1.5 and 2.5)"""
    rh, lh, times = HARP[bar]
    names = rh if staff == 1 else lh
    if times == 1:
        return [(None, 4), (None, 2), (names, 2)]
    return [(None, 2), (names, 2), (None, 2), (names, 2)]


def harp_bar(x, bar):
    s0, s1 = measure_span(x, 'P26', bar)
    body = x[s0:s1]
    assert '<pitch>' not in body, f'harp bar {bar} is not empty'
    keep = ''.join(m.group(0) for m in re.finditer(r'<attributes>.*?</attributes>|<direction[ >].*?</direction>', body, re.S))
    typ = {2: 'eighth', 4: 'quarter'}
    state = {}

    def notes(staff):
        out = []
        for names, d in harp_events(bar, staff):
            if names is None:
                out.append(f'<note><rest/><duration>{d}</duration><voice>{staff}</voice><type>{typ[d]}</type><staff>{staff}</staff></note>')
                continue
            for i, n in enumerate(names):
                p, acc = s33.pitch_xml(x, 'P26', n, state)
                out.append(f'<note>{"<chord/>" if i else ""}{p}<duration>{d}</duration><voice>{staff}</voice><type>{typ[d]}</type>{acc}<staff>{staff}</staff></note>')
        return ''.join(out)

    return x[:s0] + keep + notes(1) + '<backup><duration>8</duration></backup>' + notes(2) + x[s1:]


def notes(x, tied=True):
    """the notes of S43 (tied=False: horn 1's C of bar 118 not yet tied from bar 117, as the steps have it
    before their tie step)"""
    y = s42.notes(x)
    for pid, bars in lines().items():
        for b, evs in bars.items():
            if pid in s42.lines() and evs == s42.lines()[pid].get(b):
                continue
            y = put(y, pid, b, list(evs))
    if tied:
        y = tie(y, 'P9', 117, 118)
    for b in HARP:
        y = harp_bar(y, b)
    return y


def build(x):
    marked = s42.build(x)
    y = marked
    for pid, bars in lines().items():
        for b, evs in bars.items():
            if pid in s42.lines() and evs == s42.lines()[pid].get(b):
                continue
            y = put(y, pid, b, list(evs))
    y = tie(y, 'P9', 117, 118)
    for b in HARP:
        y = harp_bar(y, b)
    m = Marks(y)
    for pid in INTO_118:
        m.slur(pid, FADE_FROM[pid] if pid == 'P11' else (117, 0), (118, 0), number=2)
        m.hairpin(pid, FADE_FROM[pid], (118, 0), 'diminuendo')
        m.dynamic(pid, 118, 0, 'pp')
    m.dynamic('P26', 122, 3 * H, 'p')
    m.dynamic('P7', 124, H, 'p')
    m.dynamic('P6', 126, H, 'p')
    for pid, bars in (('P7', BASSOON), ('P6', CLARINET)):
        for b in bars:
            for o in (H, 3 * H):
                m.articulation(pid, b, o, 'staccato')
    return m.text()


if __name__ == '__main__':
    open(sys.argv[2], 'w', encoding='utf-8').write(build(open(sys.argv[1], encoding='utf-8').read()))
    print('wrote', sys.argv[2])
