"""Measure a composer's harmonic and melodic habits from their scores, and hold a draft up against them.

For every beat it names the accompaniment's chord (template match on the pitch classes sounding in
that beat, weighted by duration), then asks what the melody does against it: a plain chord tone
(root, third, fifth), a colour tone the accompaniment also has (seventh, sixth, added ninth), or a
note outside the chord, and whether that note resolves by step (appoggiatura, or suspension when it
was held over). On top: chord vocabulary, chromatic chords, root and bass motion, harmonic rhythm,
how long one accompaniment rhythm runs before it changes, and melodic steps and leaps.

Everything is in sounding pitch (transposing parts are converted). The melody is the first part
that is not a keyboard, guitar or harp; everything else is the accompaniment.

usage (whisperer env):
  python style_profile.py <ref.musicxml> [...] [--draft <draft.musicxml>] [--examples N] [--json out.json]
Reference pieces are summarised (median and range per measure); a draft is flagged wherever it
falls outside the reference range."""
import sys, json, bisect, statistics, argparse, os
from collections import Counter
from music21 import converter

TEMPLATES = {
    'maj': (0, 4, 7), 'min': (0, 3, 7), 'dim': (0, 3, 6), 'aug': (0, 4, 8), 'sus4': (0, 5, 7), 'sus2': (0, 2, 7),
    '7': (0, 4, 7, 10), 'maj7': (0, 4, 7, 11), 'm7': (0, 3, 7, 10), 'm7b5': (0, 3, 6, 10), 'dim7': (0, 3, 6, 9),
    'mmaj7': (0, 3, 7, 11), '7sus4': (0, 5, 7, 10), '6': (0, 4, 7, 9), 'm6': (0, 3, 7, 9),
    'add9': (0, 2, 4, 7), 'madd9': (0, 2, 3, 7), '9': (0, 2, 4, 7, 10), 'maj9': (0, 2, 4, 7, 11), 'm9': (0, 2, 3, 7, 10),
    '7b9': (0, 1, 4, 7, 10), '7#5': (0, 4, 8, 10),
}
FAMILY = {'maj': 'triad', 'min': 'triad', 'dim': 'dim/aug', 'aug': 'dim/aug', 'sus4': 'sus', 'sus2': 'sus',
          '7sus4': 'sus', '7': 'seventh', 'maj7': 'seventh', 'm7': 'seventh', 'm7b5': 'seventh', 'dim7': 'seventh',
          'mmaj7': 'seventh', '7#5': 'seventh', '6': 'added', 'm6': 'added', 'add9': 'added', 'madd9': 'added',
          '9': 'added', 'maj9': 'added', 'm9': 'added', '7b9': 'added'}
NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
KEYBOARD = ('piano', 'pno', 'guitar', 'gtr', 'harp', 'organ', 'celesta', 'keyboard', 'harpsichord')
EPS = 1e-6


def label_chord(w, bass):
    """w: {pc: weight}. -> (root, quality) or None. The smallest template that holds every significant
    pitch class, missing at most its fifth; ties go to the reading whose root is in the bass."""
    tot = sum(w.values())
    if tot <= 0:
        return None
    sig = {pc for pc, v in w.items() if v >= 0.12 * tot}
    if len(sig) < 2:
        return None
    best = None
    for r in sig:
        for i, (q, ivs) in enumerate(TEMPLATES.items()):
            tones = {(r + x) % 12 for x in ivs}
            if not sig <= tones:
                continue
            missing = tones - sig
            if missing and missing != {(r + 7) % 12}:
                continue
            key = (len(ivs), r != bass, len(missing), i)
            if best is None or key < best[0]:
                best = (key, (r, q))
    return best[1] if best else None


def tone_class(pc, chord):
    r, q = chord
    iv = (pc - r) % 12
    ivs = TEMPLATES[q]
    third = [x for x in ivs if x in (3, 4)] or [x for x in ivs if x in (2, 5)]
    plain = {0} | ({6, 7, 8} & set(ivs)) | set(third[:1])
    if iv in plain:
        return 'plain'
    if iv in ivs:
        return 'colour'
    return 'outside'


def notes_of(part):
    """[(start, end, midi)] sounding notes, ties merged; chords give every pitch"""
    out, open_ties = [], {}
    for n in part.flatten().notes:
        if n.duration.quarterLength <= 0:
            continue
        s = float(n.offset); e = s + float(n.duration.quarterLength)
        for p in n.pitches:
            m = int(round(p.ps))
            t = n.tie.type if n.tie is not None else None
            if t in ('stop', 'continue') and m in open_ties:
                idx = open_ties[m]
                out[idx] = (out[idx][0], e, m)
                if t == 'stop':
                    del open_ties[m]
                continue
            out.append((s, e, m))
            if t == 'start':
                open_ties[m] = len(out) - 1
    return sorted(out)


def melody_of(part):
    """top line only: one note per onset"""
    ns = notes_of(part)
    by = {}
    for s, e, m in ns:
        if s not in by or m > by[s][2]:
            by[s] = (s, e, m)
    return [by[k] for k in sorted(by)]


def profile(path, examples=0):
    sc = converter.parse(path)
    try:
        sc = sc.toSoundingPitch()
    except Exception:
        pass
    parts = list(sc.parts)
    names = [(p.partName or '') for p in parts]
    mi = next((i for i, n in enumerate(names) if not any(k in n.lower() for k in KEYBOARD)), None)
    if mi is None:
        return None
    mel = melody_of(parts[mi])
    acc = sorted(x for i, p in enumerate(parts) if i != mi for x in notes_of(p))
    measures = list(parts[mi].getElementsByClass('Measure'))
    ai = next(i for i in range(len(parts)) if i != mi)
    kmeasures = list(parts[ai].getElementsByClass('Measure'))
    starts = [float(m.offset) for m in measures]
    mstarts = [s for s, _, _ in mel]
    accstarts = [s for s, _, _ in acc]

    windows = []                              # (bar, t0, t1, chord, bass, keysig)
    for bi, m in enumerate(measures):
        ts = m.getContextByClass('TimeSignature')
        ks = (kmeasures[bi] if bi < len(kmeasures) else m).getContextByClass('KeySignature')
        sharps = ks.sharps if ks is not None else 0
        beat = float(ts.beatDuration.quarterLength) if ts is not None else 1.0
        length = float(m.duration.quarterLength) or (float(ts.barDuration.quarterLength) if ts else 4.0)
        t = starts[bi]
        while t < starts[bi] + length - EPS:
            t1 = min(t + beat, starts[bi] + length)
            lo = bisect.bisect_left(accstarts, t - 64)
            w, bass_now, bass_any = Counter(), None, None
            for s, e, mm in acc[lo:]:
                if s >= t1:
                    break
                ov = min(e, t1) - max(s, t)
                if ov <= EPS:
                    continue
                w[mm % 12] += ov / beat + 1.0
                if s <= t + EPS and (bass_now is None or mm < bass_now):
                    bass_now = mm
                if bass_any is None or mm < bass_any:
                    bass_any = mm
            bass = bass_now if bass_now is not None else bass_any
            chord = label_chord(w, bass % 12 if bass is not None else None)
            windows.append(dict(bar=bi + 1, t0=t, t1=t1, chord=chord, bass=bass, sharps=sharps,
                                beat_in_bar=round((t - starts[bi]) / beat), w=w))
            t = t1
    wstarts = [x['t0'] for x in windows]

    def window_at(t):
        i = bisect.bisect_right(wstarts, t + EPS) - 1
        return windows[i] if i >= 0 else None

    def diatonic(sharps):
        tonic = (7 * sharps) % 12
        return {(tonic + x) % 12 for x in (0, 2, 4, 5, 7, 9, 11)}

    # melody against harmony, at every beat
    beats = Counter(); downs = Counter(); kinds = Counter(); ex = []
    seen = {}
    for wd in windows:
        if wd['chord'] is None:
            continue
        i = bisect.bisect_right(mstarts, wd['t0'] + EPS) - 1
        if i < 0:
            continue
        s, e, m = mel[i]
        if e <= wd['t0'] + EPS:
            continue
        if i in seen and seen[i][1] == wd['chord']:
            continue
        before = seen.get(i, (None, None))[0]
        c = tone_class(m % 12, wd['chord'])
        seen[i] = (c, wd['chord'])
        beats[c] += 1
        if wd['beat_in_bar'] == 0:
            downs[c] += 1
        if c == 'outside':
            kind = 'free'
            if i + 1 < len(mel):
                s2, e2, m2 = mel[i + 1]
                w2 = window_at(s2)
                if w2 and w2['chord'] and abs(m2 - m) in (1, 2) and tone_class(m2 % 12, w2['chord']) != 'outside':
                    held = s < wd['t0'] - EPS
                    p = mel[i - 1] if i > 0 and s - mel[i - 1][1] < 1.0 else None
                    if held and before in ('plain', 'colour'):
                        kind = 'suspension'
                    elif not held and p and abs(m - p[2]) in (1, 2) and (m - p[2]) * (m2 - m) > 0:
                        kind = 'accented passing'
                    else:
                        kind = 'appoggiatura'
                    kind += ' down' if m2 < m else ' up'
            kinds[kind] += 1
            if len(ex) < examples and kind != 'free':
                r, q = wd['chord']
                ex.append(f"bar {wd['bar']} beat {wd['beat_in_bar'] + 1}: {NAMES[m % 12]} over {NAMES[r]}{q} -> {kind}")

    # melody time on plain / colour / outside tones
    mtime = Counter()
    for s, e, m in mel:
        j = bisect.bisect_right(wstarts, s + EPS) - 1
        j = max(j, 0)
        while j < len(windows) and windows[j]['t0'] < e - EPS:
            wd = windows[j]
            ov = min(e, wd['t1']) - max(s, wd['t0'])
            if ov > EPS and wd['chord'] is not None:
                mtime[tone_class(m % 12, wd['chord'])] += ov
            j += 1

    # chord vocabulary, chromatic chords, root motion, bass motion, harmonic rhythm
    fam = Counter(); quality = Counter(); chrom = 0; labelled = 0; inv = 0
    roots, changes, prev = Counter(), 0, None
    for wd in windows:
        c = wd['chord']
        if c is None:
            fam['unlabelled'] += 1
            continue
        labelled += 1
        r, q = c
        fam[FAMILY[q]] += 1
        quality[q] += 1
        if wd['bass'] is not None and wd['bass'] % 12 != r:
            inv += 1
        tones = {(r + x) % 12 for x in TEMPLATES[q]}
        if not tones <= diatonic(wd['sharps']):
            chrom += 1
        if prev is not None and c != prev:
            changes += 1
            d = (r - prev[0]) % 12
            roots[{0: 'same root', 5: 'fifth', 7: 'fifth', 1: 'step', 2: 'step', 10: 'step', 11: 'step',
                   3: 'third', 4: 'third', 8: 'third', 9: 'third', 6: 'tritone'}[d]] += 1
        prev = c
    bw = [(wd['bass'], wd['chord']) for wd in windows if wd['bass'] is not None]
    bm = Counter()
    pedal = 0
    for (a, ca), (b, cb) in zip(bw, bw[1:]):
        if a == b:
            if ca and cb and ca != cb:
                pedal += 1
            continue
        d = abs(b - a)
        bm['chromatic step' if d == 1 else 'whole step' if d == 2 else 'leap']+= 1

    # texture: how many bars one accompaniment rhythm runs before it changes
    pats, shapes = [], []
    for bi in range(len(measures)):
        t0 = starts[bi]; t1 = starts[bi + 1] if bi + 1 < len(starts) else t0 + float(measures[bi].duration.quarterLength)
        lo = bisect.bisect_left(accstarts, t0 - EPS); hi = bisect.bisect_left(accstarts, t1 - EPS)
        on = tuple(sorted({round(s - t0, 3) for s, _, _ in acc[lo:hi]}))
        top = {}
        for s, _, mm in acc[lo:hi]:
            top[s] = max(top.get(s, mm), mm)
        tops = [top[k] for k in sorted(top)]
        pats.append(on)
        shapes.append((on, tuple((b > a) - (b < a) for a, b in zip(tops, tops[1:]))))

    def run_lengths(seq, filled):
        runs, run = [], 1
        for a, b in zip(seq, seq[1:]):
            if a == b and filled(a):
                run += 1
            else:
                runs.append(run); run = 1
        runs.append(run)
        return runs
    runs, sruns = run_lengths(pats, bool), run_lengths(shapes, lambda x: bool(x[0]))

    # melody shape
    ivs = [abs(b[2] - a[2]) for a, b in zip(mel, mel[1:]) if b[0] - a[1] < 1.0]
    chrom_mel = sum(1 for s, e, m in mel if (m % 12) not in diatonic((window_at(s) or windows[0])['sharps']))
    keys = sum(1 for a, b in zip(windows, windows[1:]) if a['sharps'] != b['sharps'])

    def frac(c, k):
        n = sum(c.values())
        return round(c[k] / n, 3) if n else 0.0

    nb = len(measures)
    tm = sum(mtime.values())
    return dict(
        piece=os.path.basename(path).rsplit('.', 1)[0], melody=names[mi], bars=nb,
        beats_plain=frac(beats, 'plain'), beats_colour=frac(beats, 'colour'), beats_outside=frac(beats, 'outside'),
        downbeats_plain=frac(downs, 'plain'), downbeats_outside=frac(downs, 'outside'),
        time_plain=round(mtime['plain'] / tm, 3) if tm else 0, time_outside=round(mtime['outside'] / tm, 3) if tm else 0,
        outside_resolved=round(1 - kinds['free'] / max(1, sum(kinds.values())), 3),
        appoggiaturas_per_8_bars=round(8 * sum(v for k, v in kinds.items() if k.startswith('appog')) / nb, 2),
        suspensions_per_8_bars=round(8 * sum(v for k, v in kinds.items() if k.startswith('susp')) / nb, 2),
        accented_passing_per_8_bars=round(8 * sum(v for k, v in kinds.items() if k.startswith('accented')) / nb, 2),
        chords_triad=frac(fam, 'triad'), chords_seventh=frac(fam, 'seventh'), chords_added=frac(fam, 'added'),
        chords_sus=frac(fam, 'sus'), chords_dim_aug=frac(fam, 'dim/aug'), unlabelled=frac(fam, 'unlabelled'),
        inversions=round(inv / labelled, 3) if labelled else 0, chromatic_chords=round(chrom / labelled, 3) if labelled else 0,
        changes_per_bar=round(changes / nb, 2),
        root_fifth=frac(roots, 'fifth'), root_step=frac(roots, 'step'), root_third=frac(roots, 'third'),
        root_same=frac(roots, 'same root'), root_tritone=frac(roots, 'tritone'),
        bass_chromatic=frac(bm, 'chromatic step'), bass_whole=frac(bm, 'whole step'), bass_leap=frac(bm, 'leap'),
        pedal_per_8_bars=round(8 * pedal / nb, 2),
        rhythm_longest_run=max(runs), rhythm_mean_run=round(statistics.mean(runs), 2),
        figure_longest_run=max(sruns), figure_mean_run=round(statistics.mean(sruns), 2),
        melody_steps=round(sum(1 for x in ivs if 1 <= x <= 2) / len(ivs), 3) if ivs else 0,
        melody_leaps=round(sum(1 for x in ivs if x >= 5) / len(ivs), 3) if ivs else 0,
        melody_chromatic=round(chrom_mel / len(mel), 3) if mel else 0,
        key_changes=keys,
        top_qualities=[f'{q} {v}' for q, v in quality.most_common(6)],
        examples=ex,
    )


SKIP = ('piece', 'melody', 'bars', 'top_qualities', 'examples', 'key_changes')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('refs', nargs='*')
    ap.add_argument('--draft')
    ap.add_argument('--examples', type=int, default=0)
    ap.add_argument('--json')
    a = ap.parse_args()
    refs = [p for p in (profile(f, a.examples) for f in a.refs) if p]
    draft = profile(a.draft, a.examples) if a.draft else None
    for p in refs + ([draft] if draft else []):
        print(f"{p['piece']} ({p['melody']}, {p['bars']} bars): " + ', '.join(p['top_qualities']))
        for e in p['examples']:
            print('   ', e)
    keys = [k for k in (refs or [draft])[0] if k not in SKIP]
    if refs:
        print(f"\n{'measure':28} {'median':>7} {'range':>15}" + (f" {'draft':>7}" if draft else ''))
        for k in keys:
            vals = sorted(p[k] for p in refs)
            med = statistics.median(vals)
            line = f'{k:28} {med:7.3g} {vals[0]:7.3g}-{vals[-1]:<7.3g}'
            if draft:
                d = draft[k]
                flag = '  <-- below' if d < vals[0] else '  <-- above' if d > vals[-1] else ''
                line += f' {d:7.3g}{flag}'
            print(line)
    elif draft:
        for k in keys:
            print(f'{k:28} {draft[k]}')
    if a.json:
        json.dump(dict(refs=refs, draft=draft), open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
