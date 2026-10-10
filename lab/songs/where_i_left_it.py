"""Where I Left It: a song for English horn and piano on Claude's lyrics, written in the manner of
Brian's 2019 song studies (the 9/19/19 English horn study and no 8 above all): a long-breathed
singing line over a rippling right-hand broken-chord figure and a walking left hand, phrase-level
hairpins, a flat-side middle section, a forte return and a sighing close with a ritardando.

Everything is generated from the tables below: harmony per beat, the English horn line in CONCERT
pitch (transposed here to written pitch, a fifth up, key of A), lyrics as ABC w: lines, piano
textures per section. abc2xml converts, then the English horn transposition gets its diatonic step.
usage (whisperer env): python lab/songs/where_i_left_it.py
output: ~/Documents/Score Exports/_scorewright_out/songs/where_i_left_it.{abc,musicxml}"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it'

# ---------------------------------------------------------------- pitch helpers
LET = 'CDEFGAB'
STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
KEYSIG = {'D': {'F': 1, 'C': 1}, 'A': {'F': 1, 'C': 1, 'G': 1}}


def parse(p):
    m = re.fullmatch(r'([A-G])(#|b)?(\d)', p)
    return m.group(1), {'#': 1, 'b': -1, None: 0}[m.group(2)], int(m.group(3))


def midi(l, a, o):
    return 12 * (o + 1) + STEP[l] + a


def up_fifth(p):
    """written pitch of an English horn: a perfect fifth above concert, spelled by letter"""
    l, a, o = parse(p)
    m = midi(l, a, o) + 7
    i = LET.index(l) + 4
    o2, l2 = o + i // 7, LET[i % 7]
    a2 = m - midi(l2, 0, o2)
    return l2 + {1: '#', -1: 'b', 0: ''}[a2] + str(o2)


def abc_pitch(p, key, state):
    """key signature and bar carry decide which accidentals print"""
    l, a, o = parse(p)
    cur = state.get((l, o), KEYSIG[key].get(l, 0))
    acc = ''
    if a != cur:
        acc = {1: '^', -1: '_', 0: '='}[a]
        state[(l, o)] = a
    if o <= 4:
        return acc + l + ',' * (4 - o)
    return acc + l.lower() + "'" * (o - 5)


def dur(n):
    return '' if n == 1 else str(n)


# ---------------------------------------------------------------- harmony
LH = {'D': ('D2', 'A2'), 'D/C#': ('C#2', 'A2'), 'A/C#': ('C#2', 'E2'), 'Bm': ('B1', 'F#2'), 'Bm7': ('B1', 'F#2'),
      'Bm/A': ('A1', 'F#2'), 'Bm7/A': ('A1', 'F#2'), 'Bm/D': ('D2', 'F#2'), 'G': ('G1', 'D2'), 'Gmaj7': ('G1', 'D2'),
      'Gm': ('G1', 'D2'), 'Gm6': ('G1', 'D2'), 'Em7': ('E2', 'B2'), 'E7/G#': ('G#2', 'E2'), 'F#m7': ('F#2', 'C#3'),
      'A7sus4': ('A1', 'E2'), 'A7': ('A1', 'E2'), 'A': ('A1', 'E2'), 'D/F#': ('F#2', 'A2'), 'D/A': ('A1', 'D2'),
      'C#m7b5': ('C#2', 'G2'), 'F#7': ('F#2', 'C#3'), 'Bb': ('Bb1', 'F2'), 'C': ('C2', 'G2')}
RH = {'D': ('A3', 'D4', 'F#4'), 'D/C#': ('A3', 'D4', 'F#4'), 'A/C#': ('A3', 'C#4', 'E4'), 'Bm': ('B3', 'D4', 'F#4'),
      'Bm7': ('A3', 'D4', 'F#4'), 'Bm/A': ('B3', 'D4', 'F#4'), 'Bm7/A': ('B3', 'D4', 'F#4'), 'Bm/D': ('B3', 'D4', 'F#4'),
      'G': ('G3', 'B3', 'D4'), 'Gmaj7': ('B3', 'D4', 'F#4'), 'Gm': ('Bb3', 'D4', 'G4'), 'Gm6': ('Bb3', 'D4', 'E4'),
      'Em7': ('G3', 'B3', 'D4'), 'E7/G#': ('B3', 'D4', 'E4'), 'F#m7': ('A3', 'C#4', 'E4'), 'A7sus4': ('G3', 'D4', 'E4'),
      'A7': ('G3', 'C#4', 'E4'), 'A': ('A3', 'C#4', 'E4'), 'D/F#': ('A3', 'D4', 'F#4'), 'D/A': ('A3', 'D4', 'F#4'),
      'C#m7b5': ('G3', 'B3', 'E4'), 'F#7': ('A#3', 'C#4', 'E4'), 'Bb': ('Bb3', 'D4', 'F4'), 'C': ('G3', 'C4', 'E4')}

INTRO = ['D|D', 'Bm7|Bm7/A', 'Gmaj7|Gmaj7', 'A7sus4|A7']
VERSE = ['D|A/C#', 'Bm|Bm/A', 'Gmaj7|Gmaj7', 'Em7|A7',
         'D/F#|G', 'F#m7|Em7', 'A7sus4|A7sus4', 'A7|A7',
         'D|A/C#', 'Bm|Bm/A', 'Gmaj7|Gmaj7', 'Em7|Em7',
         'F#m7|Em7', 'Bm7|A7sus4', 'A7sus4|A7sus4', 'A7|A7']
CHORUS = ['G|G', 'D/F#|D/F#', 'Em7|Em7', 'A7sus4|A7',
          'Bm7|Bm7', 'Gmaj7|Gmaj7', 'Em7|Em7', 'A7sus4|A7',
          'G|G', 'D/F#|D/F#', 'Bm7|Bm7/A', 'Gmaj7|Gmaj7',
          'Em7|E7/G#', 'A7sus4|A7', 'D|D', 'D/C#|Bm7']
INTER1 = ['Gmaj7|Gmaj7', 'A7sus4|A7']
INTER2 = ['Gmaj7|Gmaj7', 'Gm6|Gm6']
BRIDGE = ['Bm|Bm', 'A|A', 'Gm|Gm', 'Gm6|A7',
          'Em7|Em7', 'Bm/D|Bm/D', 'C#m7b5|C#m7b5', 'F#7|F#7',
          'Bb|Bb', 'C|C', 'D|D', 'D/F#|D/F#',
          'G|G', 'Em7|E7/G#', 'A7sus4|A7sus4', 'A7|A7']
CODA = ['Gmaj7|Gmaj7', 'D|A/C#', 'Gm6|Gm6', 'D|D']

# ---------------------------------------------------------------- the English horn line (concert pitch)
# tokens: Pitch/sixteenths, ~ ties to the next note, z/n rest, ( ) slur, !...! decoration on the next note,
# "text" above the next note, N/... a note that takes no lyric (wordless)
EH_INTRO = ['z/12', 'z/12', 'z/12', 'z/8 !p! !<(! ( F#4/2 G4/2']


def verse_eh(first):
    return [
        'A4/3 G4/1 F#4/2 E4/3 F#4/1 G4/2', 'A4/3 B4/1 A4/2 !<)! !>(! F#4/6~', '!>)! F#4/12 )', 'z/8 !<(! ( E4/2 F#4/2',
        'F#4/3 G4/1 A4/2 B4/3 A4/1 G4/2', 'A4/3 G4/1 F#4/2 !<)! !>(! E4/6~', '!>)! E4/12 )', 'z/8 !<(! ( F#4/2 G4/2',
        'A4/3 B4/1 A4/2 D5/3 C#5/1 B4/2', 'A4/3 B4/1 C#5/2 !<)! !>(! D5/6~', '!>)! D5/12 )', 'z/8 ( C#5/2 B4/2',
        'A4/3 G4/1 F#4/2 G4/3 F#4/1 E4/2', '!>(! F#4/3 E4/1 D4/2 E4/6~', '!>)! E4/12 )',
        'z/8 ' + ('!mp! ' if first else '!mf! ') + '( A4/2 B4/2']


def chorus_eh(last_pickup):
    return [
        '!<(! D5/6 B4/2 A4/4', 'B4/6 A4/4 F#4/2', 'B4/8 A4/2 G4/2', '!<)! A4/6 ) z/2 ( B4/2 C#5/2',
        'D5/8 C#5/2 B4/2', 'B4/6 A4/4 G4/2', '!>(! B4/8 A4/2 G4/2', '!>)! A4/8 ) ( B4/2 C#5/2',
        '!<(! D5/6 B4/2 A4/4', 'B4/6 A4/4 F#4/2', '!<)! E5/8 D5/2 C#5/2', '!>(! B4/8 ) ( A4/2 B4/2',
        'B4/8 G#4/2 A4/2', 'B4/8 A4/2 C#5/2', '!>)! D5/12~', 'D5/6 ) z/6']


EH_INTER1 = ['z/12', 'z/8 !p! !<(! ( F#4/2 G4/2']
EH_INTER2 = ['z/12', 'z/8 !pp! ( D4/2 E4/2']
EH_BRIDGE = [
    'F#4/8 E4/2 D4/2', 'E4/8 D4/2 C#4/2', 'Bb4/8 A4/4 )', 'z/8 ( E4/2 G4/2',
    'B4/8 A4/2 G4/2', 'F#4/8 E4/2 D4/2', 'G4/12', 'F#4/6 ) z/2 !<(! ( C#4/2 D4/2',
    '!mp! F4/8 G4/2 A4/2', 'C5/8 B4/2 C#5/2', '!<)! !mf! D5/12~', 'D5/6 ) z/2 !<(! ( A4/2 B4/2',
    'D5/8 C#5/2 B4/2', '!<)! !f! E5/12~', 'E5/12~', 'E5/8 ) ( D5/2 E5/2']
EH_LAST = [
    'F#5/6 E5/2 D5/4', 'E5/6 D5/4 A4/2', '!>(! B4/8 A4/2 G4/2', '!>)! !mf! A4/6 ) z/2 ( B4/2 C#5/2',
    'D5/8 C#5/2 B4/2', 'B4/6 A4/4 G4/2', 'B4/8 A4/2 G4/2', 'A4/8 ) ( B4/2 C#5/2',
    '!<(! D5/6 B4/2 A4/4', 'B4/6 A4/2 F#4/2 A4/2', 'E5/8 D5/2 C#5/2', '!<)! !f! F#5/8 ) ( E5/2 D5/2',
    '!>(! B4/8 G#4/2 A4/2', '"^rit." B4/8 A4/2 C#5/2', '!>)! !mp! D5/12~', 'D5/6 ) z/6']
EH_CODA = ['z/8 !pp! ( N/F#4/2 N/G4/2', 'N/A4/3 N/G4/1 N/F#4/2 N/E4/3 N/F#4/1 N/G4/2', 'N/A4/12', '!fermata! N/F#4/12 )']

# ---------------------------------------------------------------- the words
V1 = ("There's a light in the win-dow I swore I'd turn off, and a cup in the sink from the morn-ing I left, "
      "there's a song on the stand with the last line crossed out, and a chair pulled a-way like it's hold-ing its breath.")
V2 = ("I got bus-y with liv-ing, the way peo-ple do, let the weeks fold like let-ters I meant to send back, "
      "and the cit-y got loud-er, the nights got too short, and the qui-et I need-ed slipped out through the cracks.")
CH = ("And it's still where I left it, still warm on the keys, like a friend at a ta-ble who saved me a seat. "
      "Oh, it's still where I left it, it nev-er let go, it just wait-ed for me to come home.")
BR = ("I was scared it would sound like a stran-ger, that I'd lost my way in-to the room, _ "
      "but the first note came back like a name I for-got that I knew.")
LAST = ("And it's still where I left it, still warm on the keys, and the song I walked out on was wait-ing for me. "
        "Oh, it's still where I left it, and I won't let it go, so I'll leave the light on and come home.")


def syllables(text):
    out = []
    for w in text.split():
        parts = w.split('-')
        out += [p + '-' for p in parts[:-1]] + [parts[-1]]
    return out


# ---------------------------------------------------------------- assemble
SECTIONS = [  # name, harmony, english horn, piano texture, piano dynamic at the start
    ('intro', INTRO, EH_INTRO, 'ripple', '!p!'),
    ('verse 1', VERSE, verse_eh(True), 'ripple', None),
    ('chorus 1', CHORUS, chorus_eh(False), 'full', '!mp!'),
    ('interlude', INTER1, EH_INTER1, 'ripple', '!p!'),
    ('verse 2', VERSE, verse_eh(False), 'ripple', None),
    ('chorus 2', CHORUS, chorus_eh(False), 'full', '!mf!'),
    ('interlude 2', INTER2, EH_INTER2, 'ripple', '!pp!'),
    ('bridge', BRIDGE, EH_BRIDGE, 'bridge', None),
    ('last chorus', CHORUS, EH_LAST, 'climax', '!f!'),
    ('coda', CODA, EH_CODA, 'coda', '!pp!'),
]
WORDS = syllables(V1) + syllables(CH) + syllables(V2) + syllables(CH) + syllables(BR) + syllables(LAST)


def eh_bar(spec):
    """concert tokens -> written ABC (key A) and the number of notes that take a syllable"""
    state, out, kinds, tied = {}, [], [], getattr(eh_bar, 'tied', False)
    for tok in re.findall(r'"[^"]*"|!\S+?!|\(|\)|\S+', spec):
        if tok.startswith('!') or tok.startswith('"') or tok in '()':
            out.append(tok)
            continue
        if tok.startswith('z/'):
            out.append('z' + dur(int(tok[2:])))
            continue
        wordless = tok.startswith('N/')
        tok = tok[2:] if wordless else tok
        tie = tok.endswith('~')
        p, n = tok.rstrip('~').split('/')
        out.append(abc_pitch(up_fifth(p), 'A', state) + dur(int(n)) + ('-' if tie else ''))
        kinds.append('k' if (tied or wordless) else 's')    # abc2xml gives every note a syllable, ties included
        tied = tie
    eh_bar.tied = tied
    return ' '.join(out).replace('( ', '(').replace(' )', ')'), kinds


def piano_bar(h, texture, first_dyn, ped):
    beats = h.split('|')
    rh, lh = [], []
    st, stl = {}, {}
    for bi, c in enumerate(beats):
        x1, x2, x3 = RH[c]
        ns = [abc_pitch(p, 'D', st) for p in (x1, x2, x3)]
        lead = (first_dyn + ' ') if (bi == 0 and first_dyn) else ''
        if texture in ('ripple', 'coda'):
            rh.append(lead + 'z2 ' + ns[0] + ns[1] + ns[2] + ns[1])
        elif texture == 'bridge-sparse':
            rh.append(lead + '[' + ''.join(ns) + ']6')
        else:
            rh.append(lead + '[' + ''.join(ns) + ']2' + ns[0] + ns[1] + ns[2] + ns[1])
        b = LH[c][0] if (bi == 0 or beats[1] != beats[0]) else LH[c][1]
        note = abc_pitch(b, 'D', stl)
        if texture == 'climax' and bi == 0:
            l, a, o = parse(b)
            note = '[' + note + abc_pitch(l + {1: '#', -1: 'b', 0: ''}[a] + str(o + 1), 'D', stl) + ']'
        change = (bi == 0) or (beats[1] != beats[0])
        pd = ''
        if change:
            pd = '!ped!' if not ped['on'] else '!ped-up!!ped!'
            ped['on'] = True
        lh.append(pd + note + '3')
    return ' '.join(rh), ' '.join(lh)


def build():
    bars = []
    for name, harm, eh, texture, dyn in SECTIONS:
        assert len(harm) == len(eh), (name, len(harm), len(eh))
        for i, (h, e) in enumerate(zip(harm, eh)):
            tex = texture
            if texture == 'bridge':
                tex = 'bridge-sparse' if i < 8 else ('ripple' if i < 12 else 'climax')
            d = dyn if i == 0 else None
            if texture == 'bridge' and i in (0, 8, 12):
                d = {0: '!pp!', 8: '!mp!', 12: '!f!'}[i]
            if texture == 'climax' and i == 2:
                d = '!mf!'
            if texture == 'climax' and i == 10:
                d = '!f!'
            if texture == 'climax' and i == 13:
                d = '!mp!'
            bars.append(dict(section=name, h=h, eh=e, tex=tex, dyn=d))
    ped = dict(on=False)
    for b in bars:
        b['eh_abc'], b['kinds'] = eh_bar(b['eh'])
        b['sung'] = b['kinds'].count('s')
        b['rh'], b['lh'] = piano_bar(b['h'], b['tex'], b['dyn'], ped)
    bars[-1]['rh'] = '!fermata!!arpeggio![' + ''.join(abc_pitch(p, 'D', {}) for p in ('D4', 'F#4', 'A4', 'E5')) + ']12'
    bars[-1]['lh'] = '!ped-up!!ped!!fermata![' + abc_pitch('D1', 'D', {}) + abc_pitch('D2', 'D', {}) + ']6'
    return bars


def to_abc(bars):
    total = sum(b['sung'] for b in bars)
    assert total == len(WORDS), f'{total} sung notes for {len(WORDS)} syllables'
    head = ['X:1', 'T:Where I Left It', 'C:Scorewright, after the song studies of Brian Ellis',
            'M:6/8', 'L:1/16', 'Q:"Lento" 3/8=48', '%%score 1 {2 3}', 'K:D',
            'V:1 clef=treble nm="English Horn" snm="E. H." transpose=-7',
            'V:2 clef=treble nm="Piano" snm="Pno."', 'V:3 clef=bass']
    body, wi = [], 0
    for s in range(0, len(bars), 4):
        blk = bars[s:s + 4]
        eh = ' | '.join(b['eh_abc'] for b in blk) + ' |' + ('|' if s + 4 >= len(bars) else '')
        body.append('[V:1] ' + ('[K:A] ' if s == 0 else '') + '[L:1/16] ' + eh)
        kinds = [k for b in blk for k in b['kinds']]
        if 's' in kinds:
            line = ''
            for k in kinds:
                w = '*' if k == 'k' else WORDS[wi]
                wi += k == 's'
                line += w if line.endswith('-') else (' ' + w if line else w)
            body.append('w: ' + line)
        body.append('[V:2] [L:1/16] ' + ' | '.join(b['rh'] for b in blk) + ' |' + ('|' if s + 4 >= len(bars) else ''))
        body.append('[V:3] [L:1/8] ' + ' | '.join(b['lh'] for b in blk) + ' |' + ('|' if s + 4 >= len(bars) else ''))
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
    if first.count('<key>') > 1:                 # the global K:D lands before the English horn's own [K:A]
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
