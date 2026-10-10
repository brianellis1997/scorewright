"""Print a score as a harmonic reduction to read like a lead sheet: one line per bar with the chord
and bass per window (half bar in 4/4 and 12/8, a beat in 6/8, the bar in 3/4), the melody in
sounding pitch with durations in quarters, and the accompaniment's onsets per beat.

The point is to read a composer's progressions, harmonic rhythm and textures with your own eyes,
fast, across many pieces; style_profile.py summarises, this shows.

usage (whisperer env): python reduce_harmony.py <score.musicxml> [first_bar] [last_bar]"""
import sys, bisect
from collections import Counter
from music21 import converter
import style_profile as sp

Q = {'maj': '', 'min': 'm', 'dim': 'dim', 'aug': '+', 'sus4': 'sus4', 'sus2': 'sus2', '7': '7', 'maj7': 'maj7',
     'm7': 'm7', 'm7b5': 'ø7', 'dim7': 'o7', 'mmaj7': 'm(maj7)', '7sus4': '7sus4', '6': '6', 'm6': 'm6',
     'add9': 'add9', 'madd9': 'm(add9)', '9': '9', 'maj9': 'maj9', 'm9': 'm9', '7b9': '7b9', '7#5': '7#5'}
N = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
FLATKEY = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


def name(pc, sharps):
    return (FLATKEY if sharps < 0 else N)[pc % 12]


def reduce(path, lo=1, hi=10 ** 6):
    sc = converter.parse(path)
    try:
        sc = sc.toSoundingPitch()
    except Exception:
        pass
    parts = list(sc.parts)
    names = [(p.partName or '') for p in parts]
    mi = next((i for i, n in enumerate(names) if not any(k in n.lower() for k in sp.KEYBOARD)), None)
    mel = sp.melody_of(parts[mi]) if mi is not None else []
    acc = sorted(x for i, p in enumerate(parts) if i != mi for x in sp.notes_of(p))
    accst = [s for s, _, _ in acc]
    measures = list(parts[mi if mi is not None else 0].getElementsByClass('Measure'))
    ai = next(i for i in range(len(parts)) if i != mi)
    kms = list(parts[ai].getElementsByClass('Measure'))
    out, lastkey, lastts = [], None, None
    for bi, m in enumerate(measures):
        if not lo <= bi + 1 <= hi:
            continue
        t0 = float(m.offset)
        ln = float(m.duration.quarterLength)
        ts = m.getContextByClass('TimeSignature')
        ks = (kms[bi] if bi < len(kms) else m).getContextByClass('KeySignature')
        sharps = ks.sharps if ks is not None else 0
        tss = ts.ratioString if ts is not None else '4/4'
        head = ''
        if (sharps, tss) != (lastkey, lastts):
            head = f'[key {sharps:+d}, {tss}] '
            lastkey, lastts = sharps, tss
        beat = float(ts.beatDuration.quarterLength) if ts is not None else 1.0
        win = {'4/4': 2.0, '12/8': 3.0, '2/4': 2.0, '6/8': 1.5, '3/4': 3.0, '9/8': 1.5, '3/8': 1.5}.get(tss, beat)
        cells, t = [], t0
        while t < t0 + ln - 1e-6:
            t1 = min(t + win, t0 + ln)
            w, bass_now, bass_any = Counter(), None, None
            for s, e, mm in acc[bisect.bisect_left(accst, t - 64):]:
                if s >= t1:
                    break
                ov = min(e, t1) - max(s, t)
                if ov <= 1e-6:
                    continue
                w[mm % 12] += ov / win + 1.0
                if s <= t + 1e-6 and (bass_now is None or mm < bass_now):
                    bass_now = mm
                if bass_any is None or mm < bass_any:
                    bass_any = mm
            bass = bass_now if bass_now is not None else bass_any
            c = sp.label_chord(w, bass % 12 if bass is not None else None)
            if c:
                lab = name(c[0], sharps) + Q[c[1]] + ('' if bass is None or bass % 12 == c[0] else '/' + name(bass, sharps))
            elif w:
                tot = sum(w.values())
                lab = '[' + ' '.join(name(pc, sharps) for pc, v in sorted(w.items(), key=lambda x: -x[1]) if v >= .12 * tot) + ']'
            else:
                lab = '-'
            cells.append(lab)
            t = t1
        ms = [(s, e, x) for s, e, x in mel if t0 - 1e-6 <= s < t0 + ln - 1e-6]
        mtxt = ' '.join(f'{name(x, sharps)}{x // 12 - 1}:{round(min(e, t0 + ln) - s, 2):g}' for s, e, x in ms) or '-'
        on = []
        b = t0
        while b < t0 + ln - 1e-6:
            on.append(len({round(s, 3) for s in accst[bisect.bisect_left(accst, b - 1e-6):bisect.bisect_left(accst, b + beat - 1e-6)]}))
            b += beat
        out.append(f'{bi + 1:4} {head}| ' + ' | '.join(f'{c:10}' for c in cells) + f' || {mtxt} || acc {"".join(str(min(o, 9)) for o in on)}')
    return names[mi] if mi is not None else '?', out


if __name__ == '__main__':
    lo = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    hi = int(sys.argv[3]) if len(sys.argv) > 3 else 10 ** 6
    mel, lines = reduce(sys.argv[1], lo, hi)
    print(f'{sys.argv[1].rsplit("/", 1)[-1]}  (melody: {mel})')
    print('\n'.join(lines))
