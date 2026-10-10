"""Generate continuations from BRIAN'S OWN NOTES, not from music theory.

Six drafts composed from principles were all dead. The reason: I satisfy constraints, and the
constraint set is satisfiable by infinitely many musically inert solutions. What I lack is an
internalised musical language - which is exactly what 1,607 of his scores are.

So: don't compose. RETRIEVE AND CONTINUE. Take the shape of the line as it stands, find every place
in his corpus where he wrote that shape, and look at what he actually wrote NEXT. Transpose those
real continuations into the current context and stitch them. The material is his; the arithmetic
is mine.

This is an n-gram continuation model over a personal corpus - no training, no compute, and the
idiom comes out right because every note came out of a piece he wrote.
"""
import collections, math, re, sqlite3
import retrieve

STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def line_of(stem, part, lo, hi):
    """[(midi, quarters, bar)] for one part over a bar range, from the compact cache."""
    out = []
    for pi, seqs in retrieve._load_seqs(stem):
        if pi != part:
            continue
        for s in seqs:
            out += [t for t in s if lo <= t[2] <= hi]
    return out


def _ivs(line):
    return tuple(line[i + 1][0] - line[i][0] for i in range(len(line) - 1))


def continuations(seed, n_after=8, max_df=60, con=None, kind=1):
    """`seed` is 5 (midi, dur, bar) tuples. kind=1 keys on intervals AND rhythm, which is far more
    specific than intervals alone - a plain stepwise shape appears in 812 of his scores and says
    nothing, while the same shape with its rhythm appears in a handful and says a lot."""
    """Every place in the corpus where `seed_ivs` occurs -> what follows it.

    Returns [(score, part, [(interval, duration)...], weight)]. Rare shapes weigh more: a figure he
    used in three pieces says far more about what he does next than a scale fragment in three
    hundred.
    """
    close = con is None
    con = con or sqlite3.connect(retrieve.DB)
    total = con.execute('SELECT COUNT(*) FROM score').fetchone()[0]
    names = dict(con.execute('SELECT id, stem FROM score').fetchall())
    N = retrieve.N
    iv = tuple(max(-24, min(24, seed[j + 1][0] - seed[j][0])) for j in range(N - 1))
    rh = tuple(retrieve._ratio(seed[j][1], seed[j + 1][1]) for j in range(N - 1))
    h = hash((iv, rh) if kind == 1 else iv) & 0x7FFFFFFFFFFFFFFF
    rows = con.execute('SELECT sid, part, meas FROM post WHERE kind=? AND h=?',
                       (kind, h)).fetchall()
    df = len({r[0] for r in rows})
    if not rows or df > max_df:
        if close:
            con.close()
        return [], df
    w = math.log(max(total / max(df, 1), 1.01))
    out = []
    for sid, part, meas in rows[:60]:
        stem = names[sid]
        try:
            seqs = retrieve._load_seqs(stem)
        except Exception:
            continue
        for pi, ss in seqs:
            if pi != part:
                continue
            for s in ss:
                for i in range(len(s) - N):
                    got_iv = tuple(max(-24, min(24, s[i + k + 1][0] - s[i + k][0]))
                                   for k in range(N - 1))
                    got_rh = tuple(retrieve._ratio(s[i + k][1], s[i + k + 1][1])
                                   for k in range(N - 1))
                    if got_iv != iv or (kind == 1 and got_rh != rh):
                        continue
                    j = i + N - 1
                    tail = s[j:j + n_after + 1]
                    if len(tail) < 3:
                        continue
                    steps = [(tail[k + 1][0] - tail[k][0], tail[k + 1][1])
                             for k in range(len(tail) - 1)]
                    out.append((stem, pi, steps, w))
    if close:
        con.close()
    return out, df


def realise(start_midi, steps, limit=(55, 96)):
    """Turn (interval, duration) steps into concrete pitches from a starting note."""
    notes, cur = [], start_midi
    for iv, dur in steps:
        cur += iv
        while cur > limit[1]:
            cur -= 12
        while cur < limit[0]:
            cur += 12
        notes.append((cur, dur))
    return notes


def midi_name(m):
    from music21 import pitch
    p = pitch.Pitch()
    p.midi = m
    return p.nameWithOctave


def consensus(seed, con=None, n=8, kind=1):
    """What does he MOST OFTEN do after this shape?

    Aggregates every continuation of the seed across the corpus into a weighted distribution over
    the next interval at each step, then walks the most likely path. This is the closest thing to
    borrowed intuition available without training: not what theory says should come next, but what
    Brian empirically writes next after this exact figure.
    """
    outs, df = continuations(seed, con=con, kind=kind)
    if not outs:
        return [], df, 0
    steps = []
    for k in range(n):
        votes = collections.Counter()
        durs = collections.Counter()
        for _stem, _pi, st, w in outs:
            if k < len(st):
                votes[st[k][0]] += w
                durs[round(st[k][1], 3)] += w
        if not votes:
            break
        steps.append((votes.most_common(1)[0][0], durs.most_common(1)[0][0]))
    return steps, df, len(outs)


def agreement(seed, con=None, n=6, kind=1):
    """How much do his continuations AGREE? High agreement = a real habit; low = anything goes."""
    outs, df = continuations(seed, con=con, kind=kind)
    if not outs:
        return []
    rows = []
    for k in range(n):
        votes = collections.Counter()
        for _s, _p, st, w in outs:
            if k < len(st):
                votes[st[k][0]] += w
        if not votes:
            break
        tot = sum(votes.values())
        top, tw = votes.most_common(1)[0]
        rows.append((k, top, tw / tot, len(votes)))
    return rows


def best_real(seed, con=None, n=8, kind=1, max_df=60):
    """Pick the most TYPICAL continuation he actually wrote, rather than synthesising one.

    Taking the argmax interval at every step collapses to the mode - "A5 A5 A5 A5", individually
    most likely and collectively not music. Classic greedy-decoding failure. Instead: score every
    REAL continuation by how well it agrees with the aggregate tendency, and return the best one.
    Whatever comes back is a phrase he actually wrote, so it cannot be musically inert.
    """
    outs, df = continuations(seed, con=con, kind=kind, max_df=max_df)
    if not outs:
        return None, df, 0
    # aggregate tendency per step
    prof = []
    for k in range(n):
        v = collections.Counter()
        for _s, _p, st, w in outs:
            if k < len(st):
                v[st[k][0]] += w
        prof.append(v)
    best, bestscore = None, -1e9
    for stem, pi, st, w in outs:
        if len(st) < 4:
            continue
        sc = 0.0
        for k in range(min(n, len(st))):
            tot = sum(prof[k].values()) or 1
            sc += prof[k].get(st[k][0], 0) / tot
        # prefer motion over a static line: a continuation that never moves is not a continuation
        moving = sum(1 for iv, _ in st[:n] if iv != 0)
        sc = sc / max(min(n, len(st)), 1) + 0.35 * (moving / max(min(n, len(st)), 1))
        if sc > bestscore:
            best, bestscore = (stem, pi, st[:n], w), sc
    return best, df, len(outs)


def chain(seed, bars=4, beats_per_bar=4.0, con=None, kind=1, limit=(60, 96)):
    """Build a whole phrase: continue, re-seed from the end of what came back, continue again.

    This is the generative loop. Every fragment is real music of his; the joins are where it can go
    wrong, so each new seed is the last five notes of what we already have, meaning each fragment is
    chosen to follow the one before it in HIS idiom rather than mine.
    """
    cur = list(seed)
    out = []
    want = bars * beats_per_bar
    used = []
    guard = 0
    while sum(d for _, d in out) < want and guard < 12:
        guard += 1
        # Progressive relaxation. A rising scale is a very common shape, so a strict rarity
        # threshold finds nothing to continue it with and the phrase stops after one fragment.
        # Try specific first (intervals AND rhythm, rare), then loosen.
        best = None
        for kd, mdf in ((1, 60), (1, 200), (0, 200), (1, 900), (0, 900)):
            best, df, n = best_real(cur[-retrieve.N:], con=con, kind=kd, max_df=mdf)
            if best:
                break
            best = None
        if not best:
            break
        stem, pi, steps, w = best
        notes = realise(cur[-1][0], steps, limit)
        for m, d in notes:
            if sum(x for _, x in out) >= want:
                break
            out.append((m, d))
            cur.append((m, d, 0))
        used.append(stem)
    return out, used
