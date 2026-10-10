"""Where I Left It, S3: intro, verse 1 and chorus 1 only, a vibe check after two misses.

Written in the grammar of Brian's 14 song studies, read bar by bar with reduce_harmony.py
(COMPOSING.md section 12), not from averages:
- slow harmony: one chord a bar, the intro and the verse's first lines on a D pedal rocking
  between Dmaj9 and Asus4/D (his openings: F#sus4/B in no 9, Asus4/D in no 1 and no 11)
- colour from the sonority (maj9, sus4, add9, m9, a Lydian #11 in the melody), not from
  changing chords; plain diatonic motion underneath (D, Bm, G, Em, A)
- a borrowed iv once in the verse (Gm(add9)/Bb under "crossed out") and once at the cadence
  (Gm6 under "me", then D on "home": his Cm-G in no 3 and no 4); V/vi (F#7/A#) before it
- one accompaniment figure per section: the verse is a left-hand eighth-note wave alone, the
  chorus adds right-hand chords on the half bar
- a simple stepwise melody built from one two-bar motif, long notes on the stressed syllables,
  his triplet turn (E5, then E D E in no 1) on a few held notes
- 4/4, slow, like most of the studies

usage (whisperer env): python lab/songs/where_i_left_it_s3.py
output: ~/Documents/Score Exports/_scorewright_out/songs/where_i_left_it_s3.{abc,musicxml}"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import parse, up_fifth, syllables, V1, CH  # noqa: E402

LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it_s3'
WORDS = syllables(V1) + syllables(CH)
KEYSIG = {'D': {'F': 1, 'C': 1}, 'A': {'F': 1, 'C': 1, 'G': 1}}
BAR, BEAT = 48, 12                 # in 48ths of a whole bar: a sixteenth is 3, a triplet eighth is 4


def abc_pitch(p, key, state):
    l, a, o = parse(p)
    cur = state.get((l, o), KEYSIG[key].get(l, 0))
    acc = ''
    if a != cur:
        acc = {1: '^', -1: '_', 0: '='}[a]
        state[(l, o)] = a
    return acc + (l + ',' * (4 - o) if o <= 4 else l.lower() + "'" * (o - 5))


def dur(n):
    return '' if n == 1 else str(n)


def join_beats(events):
    """events: (start in 48ths, text, is_rest, length). Notes in one beam group are written without
    spaces. In 4/4 eighths beam in fours, one group per half bar, as in his scores; a group holding
    anything shorter than an eighth (sixteenths, triplets) splits by beat; rests break beams."""
    out = ''
    for i, (st, txt, rest, d) in enumerate(events):
        if i:
            pst, ptxt, prest, pd = events[i - 1]
            brk = rest or prest or st % (BAR // 2) == 0 or (st % BEAT == 0 and (d < 6 or pd < 6))
            out += ' ' if brk else ''
        out += txt
    return out


def eh_bar(spec, carry):
    """concert tokens -> written ABC. Pitch/sixteenths, ~ tie, z/n rest, ( ) slur, !..! decoration,
    N/ wordless, M/ melisma; '(3' makes the next three notes a triplet. kinds: s syllable, k no
    lyric (tie continuation, wordless), m melisma."""
    state, events, kinds, pre, t, trip = {}, [], [], '', 0, 0
    for tok in re.findall(r'"[^"]*"|!\S+?!|\(3|\(|\)|\S+', spec):
        if tok == '(3':
            pre += '(3'
            trip = 3
            continue
        if tok.startswith('!') or tok.startswith('"') or tok == '(':
            pre += tok
            continue
        if tok == ')':
            st, txt, rest, d = events[-1]
            events[-1] = (st, txt + ')', rest, d)
            continue
        if tok.startswith('z/'):
            n = int(tok[2:])
            events.append((t, pre + 'z' + dur(n), True, 3 * n))
            pre = ''
            t += 3 * n
            continue
        kind = 's'
        if tok.startswith('N/'):
            kind, tok = 'k', tok[2:]
        elif tok.startswith('M/'):
            kind, tok = 'm', tok[2:]
        tie = tok.endswith('~')
        p, n = tok.rstrip('~').split('/')
        n = int(n)
        if carry['tied']:
            kind = 'k'
            if any(d in pre for d in ('!<)!', '!>)!')) and not any(d in pre for d in ('!<(!', '!>(!')):
                raise ValueError(f'hairpin ends on a tied continuation (cut-off fade): {spec}')
        events.append((t, pre + abc_pitch(up_fifth(p), 'A', state) + dur(n) + ('-' if tie else ''), False, 2 * n if trip else 3 * n))
        pre = ''
        t += 2 * n if trip else 3 * n
        trip = max(0, trip - 1)
        kinds.append(kind)
        carry['tied'] = tie
    assert t == BAR, f'English horn bar is {t}/48: {spec}'
    return join_beats(events), kinds


def piano_bar(b, ped):
    """left hand: eight eighth notes (a wave through the chord, the bass on beat one); right hand:
    optional chords on the half bar ('-' for rests)."""
    st, stl = {}, {}
    lh = b['lh'].split()
    assert len(lh) == 8, b['lh']
    ev = []
    for i, p in enumerate(lh):
        txt = abc_pitch(p, 'D', stl) + '2'
        if i == 0:
            txt = ('!ped-up!!ped!' if ped['on'] else '!ped!') + txt
            ped['on'] = True
        ev.append((i * 6, txt, False, 6))
    lhs = join_beats(ev)
    if not b['rh']:
        rhs = 'z16' if not b['pd'] else b['pd'] + 'z16'
    else:
        parts = []
        for j, ch in enumerate(b['rh'].split('|')):
            ch = ch.split()
            n = 8 if len(b['rh'].split('|')) == 2 else 16
            parts.append('[' + ''.join(abc_pitch(p, 'D', st) for p in ch) + ']' + dur(n) if len(ch) > 1 else abc_pitch(ch[0], 'D', st) + dur(n))
        if b['pd']:
            parts[0] = b['pd'] + parts[0]
        rhs = ' '.join(parts)
    return rhs, lhs


def bar(eh, lh, rh=None, pd=None):
    return dict(eh=eh, lh=lh, rh=rh, pd=pd)


# left-hand waves, one chord a bar
DMAJ9 = 'D2 A2 C#3 E3 F#3 E3 C#3 A2'
ASUS = 'D2 A2 D3 E3 G3 E3 D3 A2'          # Asus4 over the D pedal
BMADD9 = 'B1 F#2 C#3 D3 F#3 D3 C#3 F#2'
GMAJ9 = 'G1 D2 A2 B2 F#3 B2 A2 D2'
EM9 = 'E2 B2 D3 F#3 G3 F#3 D3 B2'
A_SUS_RES = 'A1 E2 A2 D3 E3 C#3 A2 E2'    # sus4 resolving to the third in the second half
A_SUS = 'A1 E2 A2 D3 E3 D3 A2 E2'         # left suspended
D_C = 'C2 A2 D3 F#3 A3 F#3 D3 A2'         # D over C
GMAJ9_B = 'B1 G2 D3 F#3 A3 F#3 D3 G2'
GM_BB = 'Bb1 G2 D3 A3 Bb3 A3 D3 G2'       # Gm(add9) over Bb, the borrowed iv
D_A = 'A1 F#2 A2 D3 F#3 D3 A2 F#2'
G_ADD9 = 'G1 D2 A2 B2 D3 B2 A2 D2'
D_FS = 'F#1 D2 A2 D3 F#3 D3 A2 D2'
A7SUS_RES = 'A1 E2 G2 D3 E3 C#3 G2 E2'
FS7_AS = 'A#1 F#2 C#3 E3 F#3 E3 C#3 F#2'
BM7 = 'B1 F#2 A2 D3 F#3 D3 A2 F#2'
GM6 = 'G1 D2 Bb2 E3 G3 E3 Bb2 D2'
D_HOME = 'D2 A2 D3 F#3 A3 F#3 D3 A2'
D_ADD9 = 'D2 A2 E3 F#3 A3 F#3 E3 A2'

INTRO = [
    bar('z/16', DMAJ9, pd='!pp!'),
    bar('z/16', ASUS),
    bar('z/16', DMAJ9),
    bar('z/12 !p! ( A3/2 D4/2', ASUS),
]
VERSE = [
    bar('!<(! F#4/8 E4/4 D4/4', DMAJ9, pd='!p!'),
    bar('E4/8 F#4/4 G4/4', ASUS),
    bar('!<)! !>(! A4/8 G4/4 F#4/4', DMAJ9),
    bar('E4/4 (3 M/E4/2 M/F#4/2 M/E4/2 ) !>)! z/4 ( D4/2 E4/2', ASUS),
    bar('!<(! F#4/8 E4/4 D4/4', BMADD9),
    bar('A4/8 B4/4 C#5/4', GMAJ9),
    bar('!<)! !>(! D5/8 C#5/4 B4/4', EM9),
    bar('A4/8 ) !>)! z/4 ( A3/2 D4/2', A_SUS_RES),
    bar('!<(! F#4/8 E4/4 D4/4', DMAJ9),
    bar('E4/8 F#4/4 G4/4', D_C),
    bar('!<)! !>(! A4/8 G4/4 F#4/4', GMAJ9_B),
    bar('Bb4/4 (3 M/Bb4/2 M/C5/2 M/Bb4/2 ) !>)! z/4 ( A4/2 G4/2', GM_BB),
    bar('!<(! B4/8 A4/4 G4/4', D_A),
    bar('F#4/8 G4/4 A4/4', EM9),
    bar('!<)! !>(! B4/8 A4/4 G4/4', GMAJ9),
    bar('D4/8 ) !>)! z/4 ( F#4/2 G4/2', A_SUS),
]
CHORUS = [
    bar('!mp! !<(! A4/8 B4/4 A4/4', G_ADD9, 'B3 D4 | A3 D4', '!mp!'),
    bar('D5/8 C#5/4 B4/4', D_FS, 'A3 D4 | A3 C#4'),
    bar('!<)! !>(! F#5/8 E5/4 D5/4', EM9, 'B3 D4 | B3 E4'),
    bar('E5/4 (3 M/E5/2 M/F#5/2 M/E5/2 ) !>)! z/4 ( B4/2 C#5/2', A_SUS_RES, 'D4 E4 | C#4 E4'),
    bar('!<(! D5/8 C#5/4 B4/4', BMADD9, 'D4 F#4 | C#4 F#4'),
    bar('A4/8 B4/4 C#5/4', GMAJ9, 'B3 F#4 | A3 D4'),
    bar('!<)! !>(! D5/8 E5/4 F#5/4', EM9, 'D4 G4 | D4 F#4'),
    bar('E5/6 M/D5/2 ) !>)! z/4 ( F#4/2 G4/2', A7SUS_RES, 'D4 G4 | C#4 G4'),
    bar('!mf! !<(! A4/8 B4/4 A4/4', G_ADD9, 'B3 D4 | A3 D4', '!mf!'),
    bar('D5/8 C#5/4 B4/4', D_FS, 'A3 D4 | A3 C#4'),
    bar('!<)! !>(! F#5/8 E5/4 D5/4', BMADD9, 'D4 F#4 | C#4 F#4'),
    bar('C#5/8 ) !>)! z/4 ( B4/2 C#5/2', FS7_AS, 'C#4 E4 | A#3 E4'),
    bar('!<(! D5/8 C#5/4 B4/4', BM7, 'D4 F#4 | D4 F#4'),
    bar('!<)! !>(! Bb4/8 A4/4 G4/4', GM6, 'Bb3 D4 | Bb3 E4'),
    bar('F#4/16~', D_HOME, 'A3 D4', '!p!'),
    bar('F#4/8 ) !>)! z/8', D_ADD9, 'A3 E4', '!pp!'),
]
SECTIONS = [('intro', INTRO), ('verse 1', VERSE), ('chorus 1', CHORUS)]


def build():
    bars = [dict(b, section=n) for n, sec in SECTIONS for b in sec]
    carry, ped = dict(tied=False), dict(on=False)
    for b in bars:
        b['eh_abc'], b['kinds'] = eh_bar(b['eh'], carry)
        b['rh_abc'], b['lh_abc'] = piano_bar(b, ped)
    return bars


def to_abc(bars):
    sung = sum(k == 's' for b in bars for k in b['kinds'])
    assert sung == len(WORDS), f'{sung} sung notes for {len(WORDS)} syllables'
    head = ['X:1', 'T:Where I Left It', 'C:Scorewright, after the song studies of Brian Ellis',
            'M:4/4', 'L:1/16', 'Q:"Lento" 1/4=63', '%%score 1 {2 3}', 'K:D',
            'V:1 clef=treble nm="English Horn" snm="E. H." transpose=-7',
            'V:2 clef=treble nm="Piano" snm="Pno."', 'V:3 clef=bass']
    body, wi = [], 0
    for s in range(0, len(bars), 4):
        blk = bars[s:s + 4]
        end = ' |' + ('|' if s + 4 >= len(bars) else '')
        body.append('[V:1] ' + ('[K:A] ' if s == 0 else '') + ' | '.join(b['eh_abc'] for b in blk) + end)
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
