"""Derive (instruction -> edit) training examples from finished scores, with no labelling.

The commit-diff trick, for music. A finished score contains its own edit history if you remove
something a composer would plausibly have added: an octave doubling, a unison doubling, a
sustained inner voice, the last N bars, a window of bars. The instruction is the inverse of the
removal, the answer is the original. Runs on any MusicXML: Brian's corpus first, PDMX after.

v1 only DETECTS and COUNTS examples per score, writing one JSON record per example:
  {score, kind, parts:[names], part_idx:[i..], bars:[lo,hi], detail}
The training text format is built from these records later.
"""
import os, sys, json, glob, random, warnings
from collections import defaultdict
warnings.filterwarnings('ignore')
from music21 import converter

SHIFTS = {0: 'unison', 12: 'octave up', -12: 'octave down', 24: 'two octaves up', -24: 'two octaves down'}


def bar_events(part):
    """measure number -> tuple of (offset, quarterLength, sorted midi pitches) for sounding notes."""
    out = {}
    for m in part.getElementsByClass('Measure'):
        ev = []
        for n in m.notes:
            ev.append((round(float(n.offset), 3), round(float(n.quarterLength), 3), tuple(sorted(q.midi for q in n.pitches))))
        out[m.number] = tuple(sorted(ev))
    return out


def shifted(ev, k):
    return tuple((o, d, tuple(p + k for p in ps)) for o, d, ps in ev)


def runs(flags, min_len):
    """consecutive measure numbers where flag is true, as (lo, hi) with hi-lo+1 >= min_len."""
    out, start, prev = [], None, None
    for m in sorted(flags):
        if flags[m]:
            if start is None:
                start = m
            elif prev is not None and m != prev + 1:
                if prev - start + 1 >= min_len:
                    out.append((start, prev))
                start = m
            prev = m
        else:
            if start is not None and prev - start + 1 >= min_len:
                out.append((start, prev))
            start = None
    if start is not None and prev - start + 1 >= min_len:
        out.append((start, prev))
    return out


def derive(path, min_run=2, seed=0):
    rnd = random.Random(seed)
    s = converter.parse(path).toSoundingPitch()
    parts = [p for p in s.parts]
    names = [p.partName or f'part{i}' for i, p in enumerate(parts)]
    ev = [bar_events(p) for p in parts]
    all_bars = sorted(set().union(*[set(e) for e in ev])) if ev else []
    n_bars = len(all_bars)
    stem = os.path.splitext(os.path.basename(path))[0]
    recs = []

    # 1. doublings: part b == part a shifted by k, same rhythm, over a run of bars
    for a in range(len(parts)):
        for b in range(len(parts)):
            if a == b:
                continue
            for k, label in SHIFTS.items():
                flags = {}
                for m in all_bars:
                    ea, eb = ev[a].get(m, ()), ev[b].get(m, ())
                    flags[m] = bool(ea) and len(ea) >= 2 and shifted(ea, k) == eb
                for lo, hi in runs(flags, min_run):
                    recs.append(dict(score=stem, kind='double', parts=[names[a], names[b]], part_idx=[a, b],
                                     bars=[lo, hi], detail=label))

    # 2. sustained inner voice: few long notes per bar, neither the highest nor the lowest sounding part
    for b in range(len(parts)):
        flags = {}
        for m in all_bars:
            eb = ev[b].get(m, ())
            if not eb or len(eb) > 2 or any(d < 2.0 for _, d, _ in eb):
                flags[m] = False; continue
            tops = [max(p for _, _, ps in e[m] for p in ps) for e in ev if e.get(m)]
            bots = [min(p for _, _, ps in e[m] for p in ps) for e in ev if e.get(m)]
            my_top = max(p for _, _, ps in eb for p in ps); my_bot = min(p for _, _, ps in eb for p in ps)
            flags[m] = len(tops) >= 3 and my_top < max(tops) and my_bot > min(bots)
        for lo, hi in runs(flags, min_run):
            recs.append(dict(score=stem, kind='fill_harmony', parts=[names[b]], part_idx=[b], bars=[lo, hi], detail='sustained inner voice'))

    # 3. continuation: the last 8 bars, when the score is long enough to have established itself
    if n_bars >= 24:
        recs.append(dict(score=stem, kind='continue', parts=names, part_idx=list(range(len(parts))),
                         bars=[all_bars[-8], all_bars[-1]], detail='last 8 bars'))

    # 4. infill: one random 4-bar window with music on both sides
    if n_bars >= 16:
        i = rnd.randint(4, n_bars - 8)
        recs.append(dict(score=stem, kind='infill', parts=names, part_idx=list(range(len(parts))),
                         bars=[all_bars[i], all_bars[i + 3]], detail='4-bar window, all parts'))
    return recs, n_bars, len(parts)


def _one(path):
    try:
        return derive(path)[0]
    except Exception:
        return None


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '/Users/bdogellis/Documents/Score Exports/MusicXML'
    out = sys.argv[2] if len(sys.argv) > 2 else '/Users/bdogellis/Documents/Score Exports/edits_v1.jsonl'
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    if src.endswith('.txt'):
        base = os.path.dirname(os.path.abspath(src))
        files = [os.path.join(base, l.strip().lstrip('./')) for l in open(src) if l.strip()]
    else:
        files = sorted(glob.glob(f'{src}/*.musicxml') + glob.glob(f'{src}/*.xml') + glob.glob(f'{src}/*.mxl'))
    if limit:
        random.seed(1); files = random.sample(files, min(limit, len(files)))
    counts = defaultdict(int); scores_with = defaultdict(int); errs = 0
    from concurrent.futures import ProcessPoolExecutor, as_completed

    with open(out, 'w') as f, ProcessPoolExecutor(max_workers=int(os.environ.get('DERIVE_WORKERS', 4))) as ex:
        futs = [ex.submit(_one, path) for path in files]
        for i, fu in enumerate(as_completed(futs), 1):
            recs = fu.result()
            if recs is None:
                errs += 1; continue
            kinds = set()
            for r in recs:
                f.write(json.dumps(r) + '\n'); counts[r['kind']] += 1; kinds.add(r['kind'])
            for k in kinds:
                scores_with[k] += 1
            if i % 500 == 0:
                print(f'{i}/{len(files)} examples so far {dict(counts)} errors {errs}', flush=True)
    print('DERIVE_DONE files', len(files), 'errors', errs)
    for k in sorted(counts):
        print(f'  {k:14s} {counts[k]:6d} examples in {scores_with[k]:4d} scores')
