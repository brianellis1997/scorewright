"""Corpus-wide self-quotation: which of Brian's pieces share material with which?

He recognised the Briello 36 / Briello 230 match as a motif he consciously reused nine years ago.
If the index found that one, it can find the rest of the network.

Only RARE shapes count. An n-gram appearing in 200 scores is a scale fragment; one appearing in two
or three is a quotation. Runs entirely in SQL so nothing is held in memory.
"""
import re, sqlite3, collections, sys
DB = '/Users/bdogellis/Documents/Score Exports/retrieval.sqlite'
MIN_DF, MAX_DF = 2, 6          # shared by at least 2 scores, at most 6


def _norm(name):
    """Filename with version noise stripped, to spot drafts of the same piece."""
    n = name.lower()
    n = re.sub(r'\b(score|version|rev|revision|edit|final|full|no|copy|draft|v)\b', ' ', n)
    n = re.sub(r'[^a-z]+', '', n)
    return n


def pairs(min_shared=6, limit=40, cross_piece_only=False, max_shared=None):
    con = sqlite3.connect(DB)
    names = dict(con.execute('SELECT id, stem FROM score').fetchall())
    # rare interval+rhythm shapes only (kind 1 - shape AND gesture, the strong signal)
    q = '''SELECT h, GROUP_CONCAT(DISTINCT sid) FROM post WHERE kind=1
           GROUP BY h HAVING COUNT(DISTINCT sid) BETWEEN ? AND ?'''
    link = collections.Counter()
    for h, sids in con.execute(q, (MIN_DF, MAX_DF)):
        ids = sorted({int(x) for x in sids.split(',')})
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                link[(ids[i], ids[j])] += 1
    con.close()
    out = []
    for (a, b), n in link.most_common():
        if n < min_shared or (max_shared and n > max_shared):
            continue
        A, B = names[a], names[b]
        if cross_piece_only:
            # drafts of one piece share thousands of shapes and drown genuine quotation between
            # DIFFERENT pieces - which is the interesting relationship (Briello 36 <-> 230).
            na, nb = _norm(A), _norm(B)
            if na == nb or na in nb or nb in na:
                continue
        out.append((A, B, n))
    return out[:limit]


if __name__ == '__main__':
    lo = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    hi = int(sys.argv[2]) if len(sys.argv) > 2 else None
    res = pairs(min_shared=lo, limit=40, cross_piece_only=True, max_shared=hi)
    print(f'{len(res)} cross-piece links, {lo}-{hi or "inf"} rare shapes shared\n')
    print(f'{"shared":>7}   piece A / piece B')
    for a, b, n in res:
        print(f'{n:>7}   {a[:40]:<42} <-> {b[:40]}')
