"""Where I Left It, S11: S10 after Brian's verdict (Oct 10 2026): "very monotonous, slow. The
material's all right, believable, but mundane; especially the chorus: boring, long, treading,
slow. The accompaniment is somewhat interesting with the triplets at times, but uninspired."

Why it plodded: nearly every horn bar was a half note and two quarters, the harmony changed once a
bar, everything ran at quarter = 63, and the chorus took 16 bars to walk down from E5. The Phrase
Atlas put 24 of its 28 phrases in his sparsest region (stepwise, narrow, long notes).

What changes, keeping the accepted material:
- tempo: quarter = 72 (Andante); each chorus poco piu mosso at 80
- the chorus lyric is anapestic ("and it's STILL where I LEFT it, still WARM on the KEYS"), so the
  chorus lilts: each stress on beat 1 or 3, the two light syllables as triplet eighths before it.
  The same pitches as the accepted chorus, two bars a line instead of four: 9 bars, not 16.
- harmony twice as fast in the chorus: the accepted circle of fifths, two chords a bar
- a groove under it: the triplet left hand he liked, now one chord per half bar with octave basses
  later, and pulsing off-beat triplet chords in the right hand
- verses stay straight (the contrast is part of the cure); the last line returns to the verse tune
usage (whisperer env): python lab/songs/where_i_left_it_s11.py"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from where_i_left_it_s3 import join_beats, abc_pitch, dur, BAR  # noqa: E402
import where_i_left_it_s6 as s6  # noqa: E402
import where_i_left_it_s7 as s7  # noqa: E402
import where_i_left_it_s9 as s9  # noqa: E402
import where_i_left_it_s10 as s10  # noqa: E402

NAME = 'where_i_left_it_s11'


def eh_bar(spec, carry, key='G', transpose=False):
    """s3.eh_bar with rests inside triplets ('(3 z/2 C5/2 D5/2')"""
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
            d = 2 * n if trip else 3 * n
            events.append((t, pre + 'z' + dur(n), True, d))
            pre, t, trip = '', t + d, max(0, trip - 1)
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
        d = 2 * n if trip else 3 * n
        events.append((t, pre + abc_pitch(p, key, state) + dur(n) + ('-' if tie else ''), False, d))
        pre, t, trip = '', t + d, max(0, trip - 1)
        kinds.append(kind)
        carry['tied'] = tie
    assert t == BAR, f'English horn bar is {t}/48: {spec}'
    return join_beats(events), kinds


def rh_bar(spec, pd, st):
    """s10.rh_bar with rests inside triplets, and the tuplet mark before any decoration"""
    if not spec:
        return (pd or '') + 'z16'
    ev, t, trip, deco = [], 0, 0, ''
    for tok in re.findall(r'!\S+?!|\(3|\[[^\]]*\]/?\d+|z\d+|[A-G][#b]?\d+/\d+', spec):
        if tok.startswith('!'):
            deco += tok
            continue
        if tok == '(3':
            trip = 3
            continue
        pre = ('(3' if trip == 3 else '') + deco
        deco = ''
        if tok.startswith('z'):
            n = int(tok[1:])
            txt = 'z' + dur(n)
        elif tok.startswith('['):
            ps, n = tok[1:].split(']')
            n = int(n.lstrip('/'))
            txt = '[' + ''.join(abc_pitch(p, 'G', st) for p in ps.split()) + ']' + dur(n)
        else:
            p, n = tok.split('/')
            n = int(n)
            txt = abc_pitch(p, 'G', st) + dur(n)
        d = 2 * n if trip else 3 * n
        ev.append((t, pre + txt, tok.startswith('z'), d))
        trip = max(0, trip - 1)
        t += d
    assert t == 48, (spec, t)
    return (pd or '') + join_beats(ev)


s7.eh_bar = eh_bar
s6.rh_bar = rh_bar

LH = dict(s9.LH6, C='C2 G2 C3 E3 C3 G2')
PULSE = {'Em': 'G3 B3 E4', 'Am7': 'G3 C4 E4', 'D7': 'F#3 A3 C4', 'Gmaj7': 'F#3 B3 D4', 'Cmaj7': 'G3 B3 E4',
         'F#o7': 'A3 C4 E4', 'B7': 'F#3 A3 D#4', 'C': 'G3 C4 E4'}
FULL = {'Em': 'G3 B3 E4 G4', 'Am7': 'G3 C4 E4 G4', 'D7': 'F#3 A3 C4 D4', 'Gmaj7': 'F#3 B3 D4 F#4', 'Cmaj7': 'G3 B3 E4 G4',
        'F#o7': 'A3 C4 E4 F#4', 'B7': 'F#3 A3 D#4 F#4', 'C': 'G3 C4 E4 G4'}


def lh_half(ch, octave, second):
    """one chord for two beats: bass, fifth, octave, tenth and back, in triplet eighths; the second
    chord of a bar takes its own pedal"""
    a, b, c, d, e, f = LH[ch].split()
    if octave:
        o = int(a[-1])
        a = f'[{a[:-1]}{o - 1} {a}]' if o >= 2 else f'[{a} {a[:-1]}{o + 1}]'
    ped = '!ped-up!!ped! ' if second else ''
    return f'(3 {ped}{a}/2 {b}/2 {c}/2 (3 {d}/2 {e}/2 {f}/2'


def rh_half(ch, full):
    c = (FULL if full else PULSE)[ch]
    beat = f'(3 z2 [{c}]/2 [{c}]/2'
    return beat + ' ' + beat


CHORUS_HARM = [('Em', 'Am7'), ('D7', 'Gmaj7'), ('Cmaj7', 'F#o7'), ('B7', 'Em'), ('Em', 'Am7'), ('D7', 'Gmaj7'), ('Cmaj7', 'F#o7')]
# the accepted chorus pitches, lilting: the stress a quarter tied into a triplet, the two light syllables after it
CH_EH = [
    '{d1} !<(! E5/4~ (3 E5/2 D5/2 C5/2 C5/4~ (3 C5/2 B4/2 B4/2',
    '!<)! !>(! D5/4~ (3 D5/2 C5/2 B4/2 B4/4 ) (3 !>)! z/2 ( A4/2 B4/2',
    '!<(! C5/4~ (3 C5/2 B4/2 A4/2 A4/4~ (3 A4/2 F#4/2 G4/2',
    '!<)! !>(! B4/4~ (3 B4/2 A4/2 F#4/2 G4/4 ) (3 !>)! z/2 ( C5/2 D5/2',
    '{d2} !<(! E5/4~ (3 E5/2 D5/2 C5/2 C5/4~ (3 C5/2 B4/2 B4/2',
    '!<)! !>(! F#5/4~ (3 F#5/2 E5/2 C5/2 B4/4 ) (3 !>)! z/2 ( B4/2 C5/2',
    '!<(! E5/4~ (3 E5/2 D5/2 C5/2 !<)! !>(! C5/8 )',
    '!>)! z/4 (3 z/2 !p! !<(! ( B4/2 D#5/2 !<)! !>(! E5/8~',
    'E5/8 ) !>)! z/8']
# the last chorus: "and the song I walked out on was waiting for me", "and I won't let it go", then
# the verse's first phrase for "so I'll leave the light on" (S10)
LAST_EH = [
    '!f! !<(! E5/4~ (3 E5/2 D5/2 C5/2 C5/4~ (3 C5/2 B4/2 B4/2',
    '!<)! !>(! D5/4~ (3 D5/2 C5/2 B4/2 B4/4 ) (3 !>)! z/2 ( A4/2 B4/2',
    '!<(! C5/4~ (3 C5/2 B4/2 A4/2 A4/4~ (3 A4/2 F#4/2 G4/2',
    '!<)! !>(! B4/4~ (3 B4/2 A4/2 F#4/2 G4/4 ) (3 !>)! z/2 ( C5/2 D5/2',
    '!<(! E5/4~ (3 E5/2 D5/2 C5/2 C5/4 (3 B4/2 B4/2 D5/2',
    '!<)! !ff! !>(! F#5/4~ (3 F#5/2 E5/2 C5/2 B4/4 ) (3 !>)! z/2 !p! ( E4/2 F#4/2'] + s10.LAST_EH[12:16]


def chorus_piano(end, dyn1, dyn2, full=False):
    """seven lilting bars on two chords each, then "to come home" landing on end (Em, or C to lead
    into the bridge) and a bar holding it"""
    bars = []
    for k, (a, b) in enumerate(CHORUS_HARM):
        octave = full or k >= 4
        dyn = dyn1 if k == 0 else (dyn2 if k == 4 else None)
        bars.append((rh_half(a, full) + ' ' + rh_half(b, full), lh_half(a, octave, False) + ' ' + lh_half(b, octave, True), dyn))
    land = {'Em': ('[G3 B3 E4]8', '[E1 E2]8'), 'C': ('[G3 C4 E4]8', '[C2 G2]8')}[end]
    bars.append((rh_half('B7', full) + ' ' + land[0], lh_half('B7', True, False) + ' !ped-up!!ped! ' + land[1], '!p!'))
    bars.append(('[G3 B3 E4]12 (3 B4/2 A4/2 G4/2' if end == 'Em' else '[E4 G4 C5]12 z4', '[E1 E2]16' if end == 'Em' else '[C2 G2]16', None))
    return bars


def last_piano():
    bars = []
    for k, (a, b) in enumerate(CHORUS_HARM[:6]):
        bars.append((rh_half(a, True) + ' ' + rh_half(b, True), lh_half(a, True, False) + ' ' + lh_half(b, True, True),
                     '!f!' if k == 0 else ('!ff!' if k == 5 else None)))
    r, l, d = bars[5]
    bars[5] = (rh_half('D7', True) + ' [F#3 B3 D4]4 z4', lh_half('D7', True, False) + ' !ped-up!!ped! [G1 G2]4 z4', d)
    return bars + s10.LAST_PNO[12:16]


def song():
    eh9, pno9 = s9.apply()
    eh, piano = list(eh9[:20]), list(pno9[:20])
    eh.append(eh9[20].replace('z/12 !p! ( C5/2 D5/2', 'z/12 (3 z/2 !p! ( C5/2 D5/2'))
    piano.append(pno9[20])
    eh += [b.replace('{d1}', '!mp!').replace('{d2}', '!mf!') for b in CH_EH]
    piano += chorus_piano('Em', '!mp!', '!mf!')
    eh += s10.INTER_EH
    piano += s10.INTER_PNO
    v2 = list(s10.V2_EH)
    v2[-1] = v2[-1].replace('z/4 ( C5/2 D5/2', 'z/4 (3 z/2 ( C5/2 D5/2')
    eh += v2
    piano += s10.V2_PNO
    eh += [b.replace('{d1}', '!mf!').replace('{d2}', '') for b in CH_EH]
    piano += chorus_piano('C', '!mf!', None)
    br = list(s10.BR_EH)
    br[-1] = br[-1].replace('z/12 !mf! ( C5/2 D5/2', 'z/12 (3 z/2 !mf! ( C5/2 D5/2')
    eh += br
    piano += s10.BR_PNO
    eh += LAST_EH
    piano += last_piano()
    eh += s10.CODA_EH
    piano += s10.CODA_PNO
    return eh, piano


# chorus 1 at bar 22, interlude 31, verse 2 33, chorus 2 49, bridge 58, last chorus 69 (final line 75), coda 79-81
TEMPO = [(22, 0, 80, 'poco più mosso'), (31, 0, 72, 'a tempo'), (49, 0, 80, 'poco più mosso'), (58, 0, 72, 'a tempo'),
         (69, 0, 80, 'poco più mosso'), (75, 0, 72, 'poco rit.'), (75, 2, 68, None), (76, 0, 65, None), (76, 2, 62, None),
         (77, 0, 60, None), (77, 2, 58, None), (78, 0, 62, 'meno mosso'), (80, 0, 58, 'rit.'), (80, 1, 55, None),
         (80, 2, 52, None), (80, 3, 48, None), (81, 0, 44, None)]


if __name__ == '__main__':
    eh, piano = song()
    assert len(eh) == len(piano) == 81, (len(eh), len(piano))
    s7.EH, s7.PIANO = eh, piano
    bars = s7.build()
    s6.NAME, s6.WORDS = NAME, s10.WORDS
    abc = s6.to_abc(bars).replace(' ||\n', ' |]\n').replace('Q:"Lento" 1/4=63', 'Q:"Andante" 1/4=72')
    out, log = s6.convert(abc)
    s10.TEMPO = TEMPO
    xml = s10.add_tempi(open(out, encoding='utf-8').read())
    open(out, 'w', encoding='utf-8').write(xml)
    print(f'{len(bars)} bars, {len(s10.WORDS)} syllables -> {out}')
    if log:
        print(log[-1500:])
