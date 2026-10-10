"""Where I Left It, S5: intro, verse 1 and chorus 1, built on Brian's own sketch for the song
(Oct 9 2026, from memory): "E minor starting on G; Em to F# half-diminished seventh to B major and
back to E minor, then the four chords over again; the melody from G up to E and back down,
resolving to B on the B major chord."

- verse: his four-chord cycle four times, one chord a bar; the second time with the bass moving
  E, A, D#, E (F#ø7/A, B7/D#) so the D# rises to E; the last cycle stops on B7, held under
  "holding its breath"
- melody: his outline, G rising to E, back down to B on the B chord; chromatic notes only where
  they lean the right way (D# up to E); leaps prepared and recovered
- breath: a rest at every comma, at most about seven seconds between breaths (lint_line.py)
- accompaniment that develops across the repeats instead of standing still: a nocturne left
  hand throughout; the right hand silent, then a slow inner line (B C B A G), then off-beat
  chords, then held chords
- chorus: the circle of fifths in E minor (Em Am7 D7 Gmaj7 Cmaj7 F#ø7 B7 Em) ending in his
  F#ø7, B7, Em; the melody falls a step every two bars; the right hand carries the guide tones
  (each seventh falls to the next chord's third); "me" on D# leaning up to E on "home"
usage (whisperer env): python lab/songs/where_i_left_it_s5.py"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import syllables, V1, CH  # noqa: E402
from where_i_left_it_s3 import eh_bar, join_beats, abc_pitch, dur  # noqa: E402

LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it_s5'
WORDS = syllables(V1) + syllables(CH)


def rh_bar(spec, pd, st):
    """right hand: 'z4 [G3 B3]4 ...' (sixteenths); '' for a silent bar"""
    if not spec:
        return (pd or '') + 'z16'
    ev, t = [], 0
    for tok in re.findall(r'\[[^\]]*\]\d+|z\d+|[A-G][#b]?\d+/\d+', spec):
        if tok.startswith('z'):
            n = int(tok[1:])
            ev.append((t * 3, 'z' + dur(n), True, 3 * n))
        elif tok.startswith('['):
            ps, n = tok[1:].split(']')
            n = int(n)
            ev.append((t * 3, '[' + ''.join(abc_pitch(p, 'G', st) for p in ps.split()) + ']' + dur(n), False, 3 * n))
        else:
            p, n = tok.split('/')
            n = int(n)
            ev.append((t * 3, abc_pitch(p, 'G', st) + dur(n), False, 3 * n))
        t += n
    assert t == 16, spec
    s = join_beats(ev)
    return (pd or '') + s


def lh_bar(spec, ped):
    st = {}
    ev = []
    for i, p in enumerate(spec.split()):
        txt = abc_pitch(p, 'G', st) + '2'
        if i == 0:
            txt = ('!ped-up!!ped!' if ped['on'] else '!ped!') + txt
            ped['on'] = True
        ev.append((i * 6, txt, False, 6))
    assert len(ev) == 8, spec
    return join_beats(ev)


def bar(eh, lh, rh='', pd=None):
    return dict(eh=eh, lh=lh, rh=rh, pd=pd)


EM = 'E2 B2 E3 G3 B3 G3 E3 B2'
FSHD = 'F#2 C3 E3 A3 C4 A3 E3 C3'
FSHD_A = 'A1 E2 A2 C3 F#3 C3 A2 E2'
B7 = 'B1 F#2 A2 D#3 F#3 D#3 A2 F#2'
B7_DS = 'D#2 A2 B2 F#3 A3 F#3 B2 A2'
# chorus: bass, fifth, octave rocking, the middle left free for the right hand's guide tones
C_EM = 'E2 B2 E3 B2 E2 B2 E3 B2'
C_AM = 'A1 E2 A2 E2 A1 E2 A2 E2'
C_D = 'D2 A2 D3 A2 D2 A2 D3 A2'
C_G = 'G1 D2 G2 D2 G1 D2 G2 D2'
C_C = 'C2 G2 C3 G2 C2 G2 C3 G2'
C_FS = 'F#1 C2 F#2 C2 F#1 C2 F#2 C2'
C_B = 'B1 F#2 B2 F#2 B1 F#2 B2 F#2'

INTRO = [
    bar('z/16', EM, pd='!pp!'),
    bar('z/16', FSHD),
    bar('z/16', B7),
    bar('z/12 !p! ( E4/2 F#4/2', EM),
]
VERSE = [
    # cycle 1: the voice alone over the left hand
    bar('!<(! G4/8 A4/4 B4/4', EM, pd='!p!'),
    bar('!<)! !>(! E5/8 C5/2 ) !>)! z/2 ( C5/4', FSHD),
    bar('!<(! B4/8 !<)! !>(! A4/4 A4/4', B7),
    bar('G4/8 ) !>)! z/4 ( E4/2 F#4/2', EM),
    # cycle 2: bass E A D# E, a slow inner line in the right hand
    bar('!<(! G4/8 A4/4 B4/4', EM, 'B3/16'),
    bar('!<)! E5/8 ) z/4 ( C5/2 B4/2', FSHD_A, 'C4/16'),
    bar('!>(! C5/4 M/B4/4 A4/4 A4/4', B7_DS, 'B3/8 A3/8'),
    bar('G4/8 ) !>)! z/4 ( G4/2 A4/2', EM, 'G3/16'),
    # cycle 3: higher, off-beat chords
    bar('!mp! !<(! B4/8 C5/4 D5/4', EM, 'z4 [G3 B3]4 z4 [G3 B3]4', '!mp!'),
    bar('E5/8 ) z/4 ( C5/2 E5/2', FSHD, 'z4 [A3 C4]4 z4 [A3 E4]4'),
    bar('!<)! !>(! F#5/8 E5/4 D#5/4', B7, 'z4 [A3 D#4]4 z4 [A3 F#4]4'),
    bar('E5/8 ) !>)! z/4 ( D5/2 C5/2', EM, 'z4 [G3 B3]4 z4 [G3 E4]4'),
    # cycle 4: down again, ending on B7 held
    bar('!p! !>(! B4/8 A4/4 G4/4', EM, '[G3 B3]16', '!p!'),
    bar('A4/8 ) !>)! z/4 ( C5/2 B4/2', FSHD, '[A3 C4]16'),
    bar('!<(! F#4/8 G4/4 A4/4', B7, '[A3 D#4]16'),
    bar('!<)! !>(! A4/8 ) !>)! z/4 ( C5/2 D5/2', B7, '[A3 D#4]16'),
]
CHORUS = [
    bar('!mp! !<(! E5/8 D5/4 C5/4', C_EM, '[G3 B3]8 [G3 B3]8', '!mp!'),
    bar('!<)! !>(! C5/8 B4/2 ) !>)! z/2 ( B4/4', C_AM, '[G3 C4]8 [G3 C4]8'),
    bar('!<(! D5/8 C5/4 B4/4', C_D, '[F#3 C4]8 [F#3 C4]8'),
    bar('!<)! !>(! B4/8 ) !>)! z/4 ( A4/2 B4/2', C_G, '[F#3 B3]8 [F#3 B3]8'),
    bar('!<(! C5/8 B4/4 A4/4', C_C, '[E3 B3]8 [E3 B3]8'),
    bar('!<)! A4/8 F#4/2 ) z/2 ( G4/4', C_FS, '[E3 A3]8 [E3 A3]8'),
    bar('!>(! B4/8 A4/4 A4/4', C_B, '[D#3 A3]8 [D#3 A3]8'),
    bar('G4/8 ) !>)! z/4 ( C5/2 D5/2', C_EM, '[E3 G3]8 [E3 B3]8'),
    bar('!mf! !<(! E5/8 D5/4 C5/4', C_EM, '[G3 B3]8 [G3 B3]8', '!mf!'),
    bar('C5/8 B4/2 ) z/2 ( B4/4', C_AM, '[G3 C4]8 [G3 C4]8'),
    bar('!<)! !>(! F#5/8 E5/4 C5/4', C_D, '[F#3 C4]8 [F#3 C4]8'),
    bar('B4/8 ) !>)! z/4 ( B4/2 C5/2', C_G, '[F#3 B3]8 [F#3 B3]8'),
    bar('!<(! E5/8 D5/4 C5/4', C_C, '[E3 B3]8 [E3 B3]8'),
    bar('!<)! !>(! C5/8 ) !>)! z/8', C_FS, '[E3 A3]8 [E3 A3]8'),
    bar('z/4 ( !p! !<(! B4/4 D#5/8', C_B, '[D#3 A3]8 [D#3 A3]8', '!p!'),
    bar('!<)! !>(! E5/12 ) !>)! z/4', C_EM, '[E3 G3 B3]16', '!pp!'),
]
SECTIONS = [('intro', INTRO), ('verse 1', VERSE), ('chorus 1', CHORUS)]


def build():
    bars = [dict(b, section=n) for n, sec in SECTIONS for b in sec]
    carry, ped = dict(tied=False), dict(on=False)
    for b in bars:
        b['eh_abc'], b['kinds'] = eh_bar(b['eh'], carry, key='D')
        b['rh_abc'] = rh_bar(b['rh'], b['pd'], {})
        b['lh_abc'] = lh_bar(b['lh'], ped)
    return bars


def to_abc(bars):
    sung = sum(k == 's' for b in bars for k in b['kinds'])
    assert sung == len(WORDS), f'{sung} sung notes for {len(WORDS)} syllables'
    head = ['X:1', 'T:Where I Left It', 'C:Scorewright, on a sketch by Brian Ellis',
            'M:4/4', 'L:1/16', 'Q:"Lento" 1/4=63', '%%score 1 {2 3}', 'K:Em',
            'V:1 clef=treble nm="English Horn" snm="E. H." transpose=-7',
            'V:2 clef=treble nm="Piano" snm="Pno."', 'V:3 clef=bass']
    body, wi = [], 0
    for s in range(0, len(bars), 4):
        blk = bars[s:s + 4]
        end = ' |' + ('|' if s + 4 >= len(bars) else '')
        body.append('[V:1] ' + ('[K:Bm] ' if s == 0 else '') + ' | '.join(b['eh_abc'] for b in blk) + end)
        kinds = [k for b in blk for k in b['kinds']]
        if 's' in kinds or 'm' in kinds:
            line = ''
            for k in kinds:
                w = {'k': '*', 'm': '_'}.get(k) or WORDS[wi]
                wi += k == 's'
                line += w if line.endswith('-') else (' ' + w if line else w)
            body.append('w: ' + line)
        body.append('[V:2] ' + ' | '.join(b['rh_abc'] for b in blk) + end)
        body.append('[V:3] ' + ' | '.join(b['lh_abc'] for b in blk) + end)
    return '\n'.join(head + body) + '\n'


def convert(abc):
    os.makedirs(OUT, exist_ok=True)
    p = f'{OUT}/{NAME}.abc'
    open(p, 'w').write(abc)
    r = subprocess.run([sys.executable, '-W', 'ignore', f'{LAB}/NotaGen/data/abc2xml.py', '-o', OUT, p], capture_output=True, text=True)
    x = f'{OUT}/{NAME}.xml'
    if not os.path.exists(x):
        sys.exit('abc2xml failed: ' + r.stderr[-800:])
    xml = open(x, encoding='utf-8').read()
    xml = xml.replace('<transpose>', '<transpose><diatonic>-4</diatonic>', 1)
    p1 = xml.index('<part id="P1">'); m1 = xml.index('</measure>', p1)
    first = xml[p1:m1]
    if first.count('<key>') > 1:
        k = first.index('<key>'); ke = first.index('</key>', k) + len('</key>')
        xml = xml[:p1] + first[:k] + first[ke:] + xml[m1:]
    out = f'{OUT}/{NAME}.musicxml'
    open(out, 'w', encoding='utf-8').write(xml)
    os.remove(x)
    return out, r.stderr.strip()


if __name__ == '__main__':
    bars = build()
    out, log = convert(to_abc(bars))
    print(f'{len(bars)} bars, {len(WORDS)} syllables -> {out}')
    if log:
        print(log[-1500:])
