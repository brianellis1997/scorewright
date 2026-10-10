"""Where I Left It, S6: S5's harmony, tune and left hand, revised after his verdict on S5
("an improvement, right direction; compose in concert pitch, always; the right hand: I would be
filling in, doubling the melody at times, or in thirds, some ornamentation, or filling lines when
the melody stops").

- concert pitch: the English horn is written as it sounds, no transposition (his preference for
  every transposing instrument)
- the right hand follows his song studies (rh_profile.py: across the 14 studies the right hand
  doubles about a third of the melody's notes, harmonises it in thirds or sixths, and fills about
  70% of the melody's rests with a line). Here:
  - intro: the right hand plays the tune first
  - verse: bare on the first pass, then thirds under the tune, then the tune an octave below;
    a short fill (a triplet or an arpeggio) in each of the horn's breaths
  - verse end: held chords with fills
  - chorus: guide tones with fills, then sixths and thirds under the tune, and a descending run
    into "to come home"
usage (whisperer env): python lab/songs/where_i_left_it_s6.py"""
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it import syllables, V1, CH  # noqa: E402
from where_i_left_it_s3 import eh_bar, join_beats, abc_pitch, dur  # noqa: E402
import where_i_left_it_s5 as s5  # noqa: E402

LAB = os.path.dirname(HERE)
OUT = '/Users/bdogellis/Documents/Score Exports/_scorewright_out/songs'
NAME = 'where_i_left_it_s6'
WORDS = syllables(V1) + syllables(CH)


def rh_bar(spec, pd, st):
    """right hand in 48ths of a bar: 'z4', 'E4/8', '[G3 B3]8', '(3 B4/2 A4/2 G4/2' (an eighth
    triplet: three notes in one beat)"""
    if not spec:
        return (pd or '') + 'z16'
    ev, t, trip = [], 0, 0
    for tok in re.findall(r'\(3|\[[^\]]*\]\d+|z\d+|[A-G][#b]?\d+/\d+', spec):
        if tok == '(3':
            trip = 3
            continue
        pre = '(3' if trip == 3 else ''
        if tok.startswith('z'):
            n = int(tok[1:]); d = 3 * n
            ev.append((t, 'z' + dur(n), True, d))
        elif tok.startswith('['):
            ps, n = tok[1:].split(']'); n = int(n); d = 3 * n
            ev.append((t, '[' + ''.join(abc_pitch(p, 'G', st) for p in ps.split()) + ']' + dur(n), False, d))
        else:
            p, n = tok.split('/'); n = int(n)
            d = 2 * n if trip else 3 * n
            ev.append((t, pre + abc_pitch(p, 'G', st) + dur(n), False, d))
            trip = max(0, trip - 1)
        t += d
    assert t == 48, (spec, t)
    return (pd or '') + join_beats(ev)


RH = [
    # intro: the tune first
    'G4/8 A4/4 B4/4', 'E5/8 C5/4 z4', 'B4/8 A4/4 A4/4', 'G4/8 z4 z4',
    # verse, first pass: bare, one fill in the breath
    '', '', '', 'z8 (3 B4/2 A4/2 G4/2 z4',
    # second pass: thirds under the tune, fills in the breaths
    'E4/8 F#4/4 G4/4', 'C5/8 (3 A4/2 B4/2 C5/2 A4/2 G4/2', '[D#4 A4]8 F#4/4 F#4/4', 'E4/8 (3 B4/2 A4/2 G4/2 z4',
    # third pass: the tune an octave below, arpeggio and scale fills
    'B3/8 C4/4 D4/4', 'E4/8 (3 C4/2 E4/2 A4/2 C4/2 E4/2', 'F#4/8 E4/4 D#4/4', 'E4/8 (3 G4/2 F#4/2 E4/2 D4/2 C4/2',
    # fourth pass: held chords, fills
    '[G3 B3]16', '[A3 C4]8 (3 E4/2 C4/2 A3/2 z4', '[A3 D#4]16', '[A3 D#4]8 (3 F#4/2 A4/2 B4/2 z4',
    # chorus: guide tones with fills
    '[G3 B3]8 [G3 B3]8', '[G3 C4]8 [G3 C4]8', '[F#3 C4]8 [F#3 C4]8', '[F#3 B3]8 (3 D4/2 F#4/2 A4/2 z4',
    '[E3 B3]8 [E3 B3]8', '[E3 A3]8 [E3 A3]8', '[D#3 A3]8 [D#3 A3]8', '[E3 G3]8 (3 B3/2 E4/2 G4/2 z4',
    # chorus again: sixths and thirds under the tune, a run into "to come home"
    'G4/8 F#4/4 E4/4', 'E4/8 D4/2 z2 D4/4', 'A4/8 G4/4 E4/4', 'D4/8 (3 F#4/2 G4/2 A4/2 D4/2 E4/2',
    'C5/8 B4/4 A4/4', 'A4/8 (3 C5/2 B4/2 A4/2 (3 G4/2 F#4/2 E4/2', 'D#4/4 [F#4 A4]4 [F#4 A4]8', '[E4 G4 B4]12 (3 B4/2 A4/2 G4/2',
]


def build():
    bars = [dict(b, section=n) for n, sec in s5.SECTIONS for b in sec]
    assert len(bars) == len(RH)
    carry, ped = dict(tied=False), dict(on=False)
    for b, rh in zip(bars, RH):
        b['eh_abc'], b['kinds'] = eh_bar(b['eh'], carry, key='G', transpose=False)
        b['rh_abc'] = rh_bar(rh, b['pd'], {})
        b['lh_abc'] = s5.lh_bar(b['lh'], ped)
    bars[0]['rh_abc'] = '!p!' + bars[0]['rh_abc'] if not bars[0]['rh_abc'].startswith('!') else bars[0]['rh_abc']
    return bars


def to_abc(bars):
    sung = sum(k == 's' for b in bars for k in b['kinds'])
    assert sung == len(WORDS), f'{sung} sung notes for {len(WORDS)} syllables'
    head = ['X:1', 'T:Where I Left It', 'C:Scorewright, on a sketch by Brian Ellis',
            'M:4/4', 'L:1/16', 'Q:"Lento" 1/4=63', '%%score 1 {2 3}', 'K:Em',
            'V:1 clef=treble nm="English Horn" snm="E. H."',
            'V:2 clef=treble nm="Piano" snm="Pno."', 'V:3 clef=bass']
    body, wi = [], 0
    for s in range(0, len(bars), 4):
        blk = bars[s:s + 4]
        end = ' |' + ('|' if s + 4 >= len(bars) else '')
        body.append('[V:1] ' + ' | '.join(b['eh_abc'] for b in blk) + end)
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
    out = f'{OUT}/{NAME}.musicxml'
    os.replace(x, out)
    return out, r.stderr.strip()


if __name__ == '__main__':
    bars = build()
    out, log = convert(to_abc(bars))
    print(f'{len(bars)} bars, {len(WORDS)} syllables -> {out}')
    if log:
        print(log[-1500:])
