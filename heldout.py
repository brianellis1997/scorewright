"""Held-out next-note prediction: does anything actually predict Brian's music?

THE SPLIT IS BY SCORE, NOT BY BAR, and this is the whole experiment. The retrieval index is built
over the corpus; if a test bar comes from a score that is IN the index, retrieval finds the literal
continuation and scores 100% while having learned nothing. So the index is rebuilt from the TRAIN
stems only, and the test stems are never indexed.

Arms:
  0 last      repeat the last interval and the last duration. The floor. If nothing beats this,
              nothing here is doing any work.
  0b zero     predict "same note again". The other trivial floor.
  1 retrieval generate.best_real against the train-only index (the current engine).
  2/3         NotaGen zero-shot / fine-tuned - added once the ABC pipeline exists.

Metrics: interval accuracy is first because it is transposition-invariant and is the actual
musical unit. COVERAGE is reported separately and matters as much as accuracy: a retrieval engine
that only fires on familiar ground is a lookup table, not a model.

    python heldout.py --build      rebuild the train-only index
    python heldout.py --run        score the arms
"""
import argparse, collections, hashlib, math, os, random, sqlite3, sys, time
import retrieve, generate

COMPACT = retrieve.COMPACT
TRAIN_DB = '/Users/bdogellis/Documents/Score Exports/retrieval_train.sqlite'
N = retrieve.N
TEST_FRAC = 0.10


def split():
    """Deterministic by stem hash, so every run and every arm sees the identical split."""
    stems = sorted(f[:-4] for f in os.listdir(COMPACT) if f.endswith('.txt'))
    test = [s for s in stems
            if int(hashlib.sha1(s.encode()).hexdigest()[:8], 16) % 1000 < TEST_FRAC * 1000]
    train = [s for s in stems if s not in set(test)]
    return train, test


def build_index(stems, path=TRAIN_DB):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript('''
      PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
      CREATE TABLE score (id INTEGER PRIMARY KEY, stem TEXT UNIQUE);
      CREATE TABLE post (kind INT, h INTEGER, sid INT, part INT, meas INT);
    ''')
    t0, batch = time.time(), []
    for sid, stem in enumerate(stems):
        con.execute('INSERT INTO score VALUES (?,?)', (sid, stem))
        try:
            txt = open(COMPACT + stem + '.txt').read()
        except Exception:
            continue
        body = txt.split('\n\n', 1)[-1] if txt.startswith('KEY SIGNATURES') else txt
        for pi, line in enumerate(body.split('\n')):
            for seq in retrieve.parse_line(line):
                for k, h, mno in retrieve.grams(seq):
                    batch.append((k, h, sid, pi, mno))
        if len(batch) > 200_000:
            con.executemany('INSERT INTO post VALUES (?,?,?,?,?)', batch)
            con.commit(); batch = []
    if batch:
        con.executemany('INSERT INTO post VALUES (?,?,?,?,?)', batch)
    con.commit()
    con.execute('CREATE INDEX ix ON post(kind, h)')
    con.commit()
    n = con.execute('SELECT COUNT(*) FROM post').fetchone()[0]
    print(f'train index: {len(stems)} scores, {n:,} postings, '
          f'{os.path.getsize(path)/1e6:.0f} MB, {time.time()-t0:.0f}s')
    con.close()


def points(test, per_score=20, seed=0):
    """(context5, target) sampled from held-out scores. Context is 5 notes, target is the 6th."""
    rnd = random.Random(seed)
    out = []
    for stem in test:
        try:
            txt = open(COMPACT + stem + '.txt').read()
        except Exception:
            continue
        body = txt.split('\n\n', 1)[-1] if txt.startswith('KEY SIGNATURES') else txt
        cands = []
        for pi, line in enumerate(body.split('\n')):
            for s in retrieve.parse_line(line):
                for i in range(len(s) - N):
                    cands.append((stem, pi, s[i:i + N], s[i + N]))
        if not cands:
            continue
        out += rnd.sample(cands, min(per_score, len(cands)))
    return out


def score(preds, name):
    """preds: [(pred_iv, pred_dur, true_iv, true_dur, fired)]"""
    fired = [p for p in preds if p[4]]
    n = len(preds)
    if not n:
        return
    def pct(x, d):
        return f'{100*x/d:5.1f}%' if d else '    -'
    iv_all = sum(1 for p in preds if p[4] and p[0] == p[2])
    du_all = sum(1 for p in preds if p[4] and abs(p[1] - p[3]) < 1e-6)
    jo_all = sum(1 for p in preds if p[4] and p[0] == p[2] and abs(p[1] - p[3]) < 1e-6)
    iv_f = sum(1 for p in fired if p[0] == p[2])
    du_f = sum(1 for p in fired if abs(p[1] - p[3]) < 1e-6)
    print(f'{name:<22} coverage {pct(len(fired), n)}   '
          f'interval {pct(iv_all, n)} (of fired {pct(iv_f, len(fired))})   '
          f'dur {pct(du_all, n)}   joint {pct(jo_all, n)}')


def run(args):
    train, test = split()
    print(f'split: {len(train)} train / {len(test)} test scores')
    if not os.path.exists(TRAIN_DB):
        print('no train index; run --build first'); return
    pts = points(test, per_score=args.per_score)
    print(f'{len(pts)} prediction points from {len(set(p[0] for p in pts))} held-out scores\n')

    a_last, a_zero, a_ret, a_hyb, a_rhy = [], [], [], [], []
    con = sqlite3.connect(TRAIN_DB)
    generate.retrieve.DB = TRAIN_DB          # make sure nothing reaches the full index
    t0 = 0
    for idx, (stem, pi, ctx, tgt) in enumerate(pts):
        true_iv = tgt[0] - ctx[-1][0]
        true_du = tgt[1]
        last_iv = ctx[-1][0] - ctx[-2][0]
        a_last.append((last_iv, ctx[-1][1], true_iv, true_du, True))
        a_zero.append((0, ctx[-1][1], true_iv, true_du, True))
        best = None
        for kd, mdf in ((1, 60), (1, 200), (0, 200), (1, 900), (0, 900)):
            best, df, nn = generate.best_real(ctx, con=con, kind=kd, max_df=mdf)
            if best:
                break
        if best:
            steps = best[2]
            a_ret.append((steps[0][0], steps[0][1], true_iv, true_du, True))
            # Retrieval is good at SHAPE and bad at RHYTHM. Take the interval from the corpus and
            # the duration from the local context instead of importing the fragment's rhythm.
            a_hyb.append((steps[0][0], ctx[-1][1], true_iv, true_du, True))
        else:
            a_ret.append((None, None, true_iv, true_du, False))
            a_hyb.append((last_iv, ctx[-1][1], true_iv, true_du, True))
        # rhythm-aware retrieval: among real continuations, prefer one whose first duration is
        # consistent with the note we are continuing from.
        if best:
            outs, df = generate.continuations(ctx, con=con, kind=1, max_df=900)
            if not outs:
                outs, df = generate.continuations(ctx, con=con, kind=0, max_df=900)
            pick = None
            for _s, _p, st, w in outs:
                if st and abs(st[0][1] - ctx[-1][1]) < 1e-6:
                    pick = st; break
            pick = pick or best[2]
            a_rhy.append((pick[0][0], pick[0][1], true_iv, true_du, True))
        else:
            a_rhy.append((None, None, true_iv, true_du, False))
        if (idx + 1) % 200 == 0:
            print(f'  ...{idx+1}/{len(pts)}', flush=True)
    con.close()
    print()
    score(a_zero, 'arm 0a repeat-note')
    score(a_last, 'arm 0b last-interval')
    score(a_ret,  'arm 1  retrieval')
    score(a_hyb,  'arm 1b ret-iv+last-dur')
    score(a_rhy,  'arm 1c rhythm-aware ret')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--per-score', type=int, default=20)
    a = ap.parse_args()
    if a.build:
        tr, te = split()
        print(f'{len(tr)} train / {len(te)} test')
        build_index(tr)
    if a.run:
        run(a)
