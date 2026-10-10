"""Where I Left It, S4: intro, verse 1 and chorus 1 in B minor, after his verdict on S3 ("better,
you're getting the style; still pop-music-y, generic inspirational, slightly corny; when I was
messing around I had it in a minor key").

What S3 still had that is not his: the chorus ran G(add9), D/F#, Em9, Asus4, A (IV, I6, ii, Vsus,
V), the stock worship-song progression, and the tune climbed to a bright high point. S4 keeps the
song-study grammar (COMPOSING.md section 12) and takes the minor and modal side of it, as most of
his studies do (no 5, 7, 9, 10, 11, 9/23/19):
- a B pedal rocking between Bm(add9) and B7sus4 for the intro and the first verse lines (his no 9
  opens on a B pedal with sus sonorities)
- modal minor: the minor v (F#m7) and F#sus4 that never becomes F# major, VI (Gmaj9), iv (Em9), no
  leading-tone cadence; one Neapolitan C/E under "crossed out"
- the chorus turns to the relative major over a D pedal, Dmaj7 rocking with Em9/D (not I to IV)
- "home" lands deceptively on Gmaj9 with the melody holding B, and the harmony settles to Bm(add9)
  under the held note
- the tune stays low and narrow (B3 to A4), mostly stepwise, a two-bar motif recoloured by the
  harmony, his triplet turn; dynamics pp to mp, no climax
usage (whisperer env): python lab/songs/where_i_left_it_s4.py"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import syllables, V1, CH  # noqa: E402
from where_i_left_it_s3 import eh_bar, piano_bar, bar  # noqa: E402

LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it_s4'
WORDS = syllables(V1) + syllables(CH)

BMADD9 = 'B1 F#2 C#3 D3 F#3 D3 C#3 F#2'
B7SUS = 'B1 F#2 E3 F#3 A3 F#3 E3 F#2'
GMAJ9 = 'G1 D2 A2 B2 F#3 B2 A2 D2'
EM9 = 'E2 B2 D3 F#3 G3 F#3 D3 B2'
FSM7 = 'F#1 C#2 A2 C#3 E3 C#3 A2 C#2'
FSM7_A = 'A1 F#2 C#3 E3 A3 E3 C#3 F#2'
FSSUS = 'F#1 C#2 B2 C#3 E3 C#3 B2 C#2'          # F#sus4, never F# major
C_E = 'E2 C3 G3 B3 C4 B3 G3 C3'                 # Neapolitan in first inversion
DMAJ7 = 'D2 A2 C#3 E3 F#3 E3 C#3 A2'
EM9_D = 'D2 B2 E3 F#3 G3 F#3 E3 B2'
BM9 = 'B1 F#2 C#3 D3 A3 D3 C#3 F#2'
GMAJ7 = 'G1 D2 B2 D3 F#3 D3 B2 D2'
GMAJ9_HOME = 'G1 D2 A2 B2 D3 B2 A2 D2'

INTRO = [
    bar('z/16', BMADD9, pd='!pp!'),
    bar('z/16', B7SUS),
    bar('z/16', BMADD9),
    bar('z/12 !pp! ( B3/2 C#4/2', B7SUS),
]
VERSE = [
    bar('!<(! D4/8 C#4/4 B3/4', BMADD9),
    bar('C#4/8 D4/4 E4/4', B7SUS),
    bar('!<)! !>(! F#4/8 E4/4 D4/4', BMADD9),
    bar('C#4/4 (3 M/C#4/2 M/D4/2 M/C#4/2 ) !>)! z/4 ( B3/2 C#4/2', B7SUS),
    bar('!<(! D4/8 C#4/4 B3/4', GMAJ9),
    bar('F#4/8 G4/4 A4/4', EM9),
    bar('!<)! !>(! A4/8 G#4/4 F#4/4', FSM7),
    bar('C#4/8 ) !>)! z/4 ( B3/2 C#4/2', BMADD9),
    bar('!<(! D4/8 C#4/4 B3/4', BMADD9),
    bar('C#4/8 D4/4 E4/4', B7SUS),
    bar('!<)! !>(! F#4/8 E4/4 D4/4', GMAJ9),
    bar('E4/4 (3 M/E4/2 M/F#4/2 M/E4/2 ) !>)! z/4 ( D4/2 C#4/2', C_E),
    bar('!<(! D4/8 E4/4 F#4/4', GMAJ9),
    bar('A4/8 G4/4 F#4/4', FSM7_A),
    bar('!<)! !>(! G4/8 F#4/4 E4/4', EM9),
    bar('B3/8 ) !>)! z/4 ( D4/2 E4/2', FSSUS),
]
CHORUS = [
    bar('!p! !<(! A4/8 A4/4 G4/4', DMAJ7, 'F#3 A3 | F#3 A3', '!p!'),
    bar('F#4/8 E4/4 D4/4', EM9_D, 'G3 B3 | F#3 B3'),
    bar('!<)! !>(! E4/8 F#4/4 G4/4', DMAJ7, 'F#3 A3 | E3 A3'),
    bar('F#4/4 (3 M/F#4/2 M/G4/2 M/F#4/2 ) !>)! z/4 ( D4/2 E4/2', EM9_D, 'G3 B3 | F#3 B3'),
    bar('!<(! F#4/8 E4/4 D4/4', BM9, 'D3 A3 | C#3 A3'),
    bar('G4/8 F#4/4 E4/4', EM9, 'D3 G3 | D3 F#3'),
    bar('!<)! !>(! F#4/8 E4/4 D4/4', GMAJ7, 'B2 D3 | B2 F#3'),
    bar('C#4/8 ) !>)! z/4 ( F#4/2 G4/2', FSSUS, 'B2 E3 | A2 E3'),
    bar('!mp! !<(! A4/8 A4/4 G4/4', DMAJ7, 'F#3 A3 | F#3 A3', '!mp!'),
    bar('F#4/8 E4/4 D4/4', EM9_D, 'G3 B3 | F#3 B3'),
    bar('!<)! !>(! F#4/8 G4/4 F#4/4', BMADD9, 'D3 F#3 | C#3 F#3'),
    bar('E4/4 (3 M/E4/2 M/F#4/2 M/E4/2 ) !>)! z/4 ( F#4/2 G4/2', EM9, 'D3 G3 | D3 F#3'),
    bar('!<(! A4/8 G4/4 F#4/4', GMAJ9, 'B2 F#3 | A2 D3'),
    bar('!<)! !>(! E4/8 D4/4 C#4/4', FSSUS, 'B2 E3 | C#3 E3'),
    bar('B3/16~', GMAJ9_HOME, 'B2 D3', '!pp!'),
    bar('B3/8 ) !>)! z/8', BMADD9, 'B2 D3'),
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
            'M:4/4', 'L:1/16', 'Q:"Lento" 1/4=60', '%%score 1 {2 3}', 'K:Bm',
            'V:1 clef=treble nm="English Horn" snm="E. H." transpose=-7',
            'V:2 clef=treble nm="Piano" snm="Pno."', 'V:3 clef=bass']
    body, wi = [], 0
    for s in range(0, len(bars), 4):
        blk = bars[s:s + 4]
        end = ' |' + ('|' if s + 4 >= len(bars) else '')
        body.append('[V:1] ' + ('[K:F#m] ' if s == 0 else '') + ' | '.join(b['eh_abc'] for b in blk) + end)
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
