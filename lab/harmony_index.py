"""Reduce every score in the archive to chords, bass, melody and accompaniment rhythm per window,
and store one JSON file per score, so progressions can be searched across all of his music
(find_progression.py). Resumable: scores already indexed are skipped.

usage (whisperer env): python harmony_index.py [--jobs 4] [--limit N]
output: ~/Documents/Score Exports/_logs/harmony_index/<stem>.json"""
import os, sys, json, glob, bisect, argparse, signal
from collections import Counter
from multiprocessing import Pool

E = '/Users/bdogellis/Documents/Score Exports'
OUT = f'{E}/_logs/harmony_index'
SOURCES = [f'{E}/MusicXML', f'{E}/extra_sept2026/MusicXML']
WIN = {'4/4': 2.0, '12/8': 3.0, '2/4': 2.0, '6/8': 1.5, '3/4': 3.0, '9/8': 1.5, '3/8': 1.5, '2/2': 2.0, '5/4': 2.5}


def index_one(path):
    stem = os.path.basename(path).rsplit('.', 1)[0]
    dst = f'{OUT}/{stem}.json'
    if os.path.exists(dst):
        return stem, 'skip'
    signal.signal(signal.SIGALRM, lambda *a: (_ for _ in ()).throw(TimeoutError()))
    signal.alarm(120)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import style_profile as sp
        from music21 import converter
        sc = converter.parse(path)
        try:
            sc = sc.toSoundingPitch()
        except Exception:
            pass
        parts = list(sc.parts)
        names = [(p.partName or '') for p in parts]
        keyboard = [i for i, n in enumerate(names) if any(k in n.lower() for k in sp.KEYBOARD)]
        others = [i for i in range(len(parts)) if i not in keyboard]
        mi = others[0] if others else 0
        mel = sp.melody_of(parts[mi])
        acc = sorted(x for i, p in enumerate(parts) if i != mi for x in sp.notes_of(p)) if len(parts) > 1 else []
        if not acc:
            acc = sorted(sp.notes_of(parts[0]))
        accst = [s for s, _, _ in acc]
        measures = list(parts[mi].getElementsByClass('Measure'))
        kmeas = list(parts[keyboard[0] if keyboard else 0].getElementsByClass('Measure'))
        bars = []
        for bi, m in enumerate(measures):
            t0 = float(m.offset)
            ln = float(m.duration.quarterLength)
            ts = m.getContextByClass('TimeSignature')
            ks = (kmeas[bi] if bi < len(kmeas) else m).getContextByClass('KeySignature')
            tss = ts.ratioString if ts is not None else '4/4'
            win = WIN.get(tss, float(ts.beatDuration.quarterLength) if ts is not None else 1.0)
            wins, t = [], t0
            while t < t0 + ln - 1e-6:
                t1 = min(t + win, t0 + ln)
                w, bn, ba = Counter(), None, None
                for s, e, mm in acc[bisect.bisect_left(accst, t - 64):]:
                    if s >= t1:
                        break
                    ov = min(e, t1) - max(s, t)
                    if ov <= 1e-6:
                        continue
                    w[mm % 12] += ov / win + 1.0
                    if s <= t + 1e-6 and (bn is None or mm < bn):
                        bn = mm
                    if ba is None or mm < ba:
                        ba = mm
                bass = bn if bn is not None else ba
                c = sp.label_chord(w, bass % 12 if bass is not None else None) if w else None
                wins.append([c[0] if c else None, c[1] if c else None, bass])
                t = t1
            ms = [[s - t0, round(e - s, 3), x] for s, e, x in mel if t0 - 1e-6 <= s < t0 + ln - 1e-6]
            bars.append(dict(n=bi + 1, ts=tss, ks=ks.sharps if ks is not None else 0, w=wins, m=ms))
        json.dump(dict(stem=stem, parts=names, melody=names[mi] if names else '', bars=bars), open(dst, 'w'))
        return stem, 'ok'
    except Exception as ex:
        return stem, f'error {type(ex).__name__}'
    finally:
        signal.alarm(0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    files = sorted(f for d in SOURCES for f in glob.glob(f'{d}/*.musicxml'))
    if a.limit:
        files = files[:a.limit]
    done = errs = 0
    with Pool(a.jobs, maxtasksperchild=20) as pool:
        for i, (stem, st) in enumerate(pool.imap_unordered(index_one, files)):
            done += st == 'ok'
            errs += st.startswith('error')
            if i % 50 == 0 or st.startswith('error'):
                print(f'{i + 1}/{len(files)} {stem[:40]}: {st}', flush=True)
    print(f'indexed {done}, errors {errs}, total {len(files)}')


if __name__ == '__main__':
    main()
