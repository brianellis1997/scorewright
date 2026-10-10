"""Retrieval across Brian's own corpus: "where have I solved a passage like this before?"

WHY INTERVALS AND RHYTHM, not harmony: roman-numeral analysis is the weakest thing in this project
(PROJECT.md 12e) and is wrecked by his MIDI-entered enharmonic spelling. Melodic INTERVALS and
duration RATIOS are deterministic, transposition-invariant, tempo-invariant, and need no analysis
that could be wrong. They are also what a composer actually recognises: shape and gesture.

WHY SQLITE, not a dict: 2,074,004 note events across 1,607 scores. A naive in-memory index is
several GB, and a memory exhaustion already killed this project's export run once. Everything here
streams one score at a time and batches to disk.

    python retrieve.py --build                          (~1,607 scores)
    python retrieve.py --query "Briello no 36 in D# minor" 13 --part 0
"""
import argparse, os, re, sqlite3, sys, time

COMPACT = '/Users/bdogellis/Documents/Score Exports/compact/'
DB = '/Users/bdogellis/Documents/Score Exports/retrieval.sqlite'
N = 5                       # notes per n-gram (so 4 intervals)

STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
# The duration must NOT be `[\d.]+`: the encoder appends articulations as `.stac` and ties as `~`,
# so a greedy dot-class swallows the articulation's leading dot and yields '0.25.' -> ValueError.
_D = r'(\d+(?:\.\d+)?)'
TOK = re.compile(r'\[([^\]]+)\]:' + _D + r'|([A-G][#\-]*)(-?\d+):' + _D + r'|r:' + _D)


def midi(name):
    """'F#4' / 'B-2' / 'C##5' -> midi number. '-' is music21's flat, as written by the encoder."""
    m = re.match(r'^([A-G])([#\-]*)(-?\d+)$', name)
    if not m:
        return None
    acc = m.group(2).count('#') - m.group(2).count('-')
    return STEP[m.group(1)] + acc + (int(m.group(3)) + 1) * 12


def parse_line(line):
    """A compact part line -> [ (voice_seq, ...) ], each voice_seq = [(midi, dur, measure)].

    A REST BREAKS THE PHRASE and starts a new sequence: an interval across a rest is not a melodic
    interval, it is two separate gestures. Chords contribute their TOP note, which is where the line
    lives. `//` separates simultaneous voices; each is its own melodic line.
    """
    if ':' not in line:
        return []
    body = line.split(':', 1)[1] if re.match(r'^[^|]{0,40}?: ', line) else line
    seqs, cur = [], []
    for mno, bar in enumerate(body.split('|'), start=1):
        for voice in bar.split('//'):
            for m in TOK.finditer(voice):
                if m.group(6):                      # rest
                    if len(cur) >= N:
                        seqs.append(cur)
                    cur = []
                    continue
                if m.group(1):                      # chord -> top note
                    ps = [midi(p) for p in m.group(1).split()]
                    ps = [p for p in ps if p is not None]
                    if not ps:
                        continue
                    pit, dur = max(ps), float(m.group(2))
                else:
                    pit, dur = midi(m.group(3) + m.group(4)), float(m.group(5))
                    if pit is None:
                        continue
                cur.append((pit, dur, mno))
    if len(cur) >= N:
        seqs.append(cur)
    return seqs


def _ratio(a, b):
    """Quantised duration ratio, so the same gesture matches at any note value."""
    if a <= 0:
        return 0
    r = b / a
    for i, v in enumerate((0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)):
        if abs(r - v) < 0.13:
            return i + 1
    return 9


def grams(seq):
    """(kind, hash, measure) for every window. kind 0 = intervals only, 1 = intervals + rhythm."""
    out = []
    for i in range(len(seq) - N + 1):
        w = seq[i:i + N]
        iv = tuple(max(-24, min(24, w[j + 1][0] - w[j][0])) for j in range(N - 1))
        if all(v == 0 for v in iv):
            continue                                 # a repeated note matches everything; useless
        rh = tuple(_ratio(w[j][1], w[j + 1][1]) for j in range(N - 1))
        out.append((0, hash(iv) & 0x7FFFFFFFFFFFFFFF, w[0][2]))
        out.append((1, hash((iv, rh)) & 0x7FFFFFFFFFFFFFFF, w[0][2]))
    return out


def build(limit=None):
    if os.path.exists(DB):
        os.remove(DB)
    con = sqlite3.connect(DB)
    con.executescript('''
      PRAGMA journal_mode=OFF; PRAGMA synchronous=OFF;
      CREATE TABLE score (id INTEGER PRIMARY KEY, stem TEXT UNIQUE);
      CREATE TABLE post (kind INT, h INTEGER, sid INT, part INT, meas INT);
    ''')
    files = sorted(f for f in os.listdir(COMPACT) if f.endswith('.txt'))[:limit]
    t0, batch = time.time(), []
    for sid, fn in enumerate(files):
        stem = fn[:-4]
        con.execute('INSERT INTO score VALUES (?,?)', (sid, stem))
        try:
            txt = open(COMPACT + fn).read()
        except Exception:
            continue
        body = txt.split('\n\n', 1)[-1] if txt.startswith('KEY SIGNATURES') else txt
        for pi, line in enumerate(body.split('\n')):
            for seq in parse_line(line):
                for k, h, mno in grams(seq):
                    batch.append((k, h, sid, pi, mno))
        if len(batch) > 200_000:
            con.executemany('INSERT INTO post VALUES (?,?,?,?,?)', batch)
            con.commit(); batch = []
        if (sid + 1) % 200 == 0:
            print(f'  {sid + 1}/{len(files)}  {(time.time() - t0) / 60:.1f} min', flush=True)
    if batch:
        con.executemany('INSERT INTO post VALUES (?,?,?,?,?)', batch)
    con.commit()
    print('  indexing...', flush=True)
    con.execute('CREATE INDEX ix ON post(kind, h)')
    con.commit()
    n = con.execute('SELECT COUNT(*) FROM post').fetchone()[0]
    print(f'DONE {len(files)} scores, {n:,} postings, '
          f'{os.path.getsize(DB) / 1e6:.0f} MB, {(time.time() - t0) / 60:.1f} min')
    con.close()


def _load_seqs(stem):
    txt = open(COMPACT + stem + '.txt').read()
    body = txt.split('\n\n', 1)[-1] if txt.startswith('KEY SIGNATURES') else txt
    return [(pi, parse_line(line)) for pi, line in enumerate(body.split('\n'))]


def query(stem, lo, hi, part=None, top=8, con=None):
    """Passages elsewhere in the corpus that share melodic shape with bars [lo, hi] of `stem`.

    Ranked by INVERSE DOCUMENT FREQUENCY: an n-gram occurring in 10,000 places says nothing, one
    occurring in three is a real correspondence. Interval+rhythm matches (kind 1) are weighted above
    interval-only (kind 0) because sharing both shape and gesture is a stronger signal.
    """
    import math, collections
    close = con is None
    con = con or sqlite3.connect(DB)
    total = con.execute('SELECT COUNT(*) FROM score').fetchone()[0]
    me = con.execute('SELECT id FROM score WHERE stem=?', (stem,)).fetchone()
    me = me[0] if me else -1

    wanted = []
    for pi, seqs in _load_seqs(stem):
        if part is not None and pi != part:
            continue
        for seq in seqs:
            sub = [t for t in seq if lo <= t[2] <= hi]
            if len(sub) >= N:
                wanted += [(k, h) for k, h, _ in grams(sub)]
    if not wanted:
        if close:
            con.close()
        return [], 0

    hits = collections.defaultdict(float)
    where = collections.defaultdict(list)
    for k, h in set(wanted):
        rows = con.execute('SELECT sid, part, meas FROM post WHERE kind=? AND h=?', (k, h)).fetchall()
        df = len({r[0] for r in rows})
        if df == 0 or df > total * 0.25:            # ubiquitous shapes carry no information
            continue
        w = math.log(total / df) * (1.6 if k == 1 else 1.0)
        # Credit each n-gram ONCE per target region. Crediting every posting let a piece that
        # repeats one figure twenty times outrank a piece sharing twenty DIFFERENT figures - it
        # measured the target's repetitiveness, not the strength of the correspondence.
        credited = set()
        for sid, pt, ms in rows:
            if sid == me:
                continue
            region = (sid, pt, ms // 8)
            where[region].append(ms)
            if region in credited:
                continue
            credited.add(region)
            hits[region] += w

    names = dict(con.execute('SELECT id, stem FROM score').fetchall())
    out = []
    for (sid, pt, blk), sc in sorted(hits.items(), key=lambda kv: -kv[1])[:top]:
        ms = sorted(set(where[(sid, pt, blk)]))
        out.append({'score': names[sid], 'part': pt, 'measures': f'{ms[0]}-{ms[-1]}'
                    if ms[0] != ms[-1] else str(ms[0]), 'weight': round(sc, 1),
                    'n_matches': len(set(where[(sid, pt, blk)]))})
    if close:
        con.close()
    return out, len(set(wanted))


XML_DIR = '/Users/bdogellis/Documents/Score Exports/MusicXML/'


def passage_notation(stem, lo, hi):
    """Slurs, articulations and ornaments actually present in those bars, read from the MusicXML.

    THE COMPACT CACHE DOES NOT ENCODE SLURS (PROJECT.md 12b). Handed a corpus excerpt with no slur
    data, the model asserted that the retrieved passages were "consistently phrased as single
    slurred gestures" - true for two of them and FALSE for Briello no 230 bars 3-6, which has none.
    A retrieved passage must carry the notation someone will reason about, or it invites exactly
    that fabrication.
    """
    import xmledit
    try:
        raw = open(XML_DIR + stem + '.musicxml').read()
    except FileNotFoundError:
        return ''
    ex = xmledit.excerpt(raw, lo, hi)
    if not ex:
        return ''
    slurs = len(re.findall(r'<slur[^>]*type="start"', ex))
    arts = re.findall(r'<(accent|staccato|tenuto|strong-accent|staccatissimo|'
                      r'detached-legato|spiccato)\s*/>', ex)
    orns = re.findall(r'<(trill-mark|mordent|inverted-mordent|turn|shake|tremolo)\s*/>', ex)
    dyn = re.findall(r'<dynamics[^>]*>\s*<(\w+)\s*/>', ex)
    wedge = len(re.findall(r'<wedge[^>]*type="(?:crescendo|diminuendo)"', ex))
    bits = [f'{slurs} slur(s)' if slurs else 'NO slurs']
    if arts:
        import collections
        bits.append(', '.join(f'{v}x {k}' for k, v in collections.Counter(arts).items()))
    if orns:
        bits.append('ornaments: ' + ', '.join(sorted(set(orns))))
    if dyn:
        bits.append('dynamics: ' + ' '.join(dyn[:4]))
    if wedge:
        bits.append(f'{wedge} hairpin(s)')
    return '   [notation: ' + '; '.join(bits) + ']'


def excerpt_text(stem, lo, hi, part=None, max_chars=400):
    """The compact notes for those bars, so a retrieved passage can be READ, not just cited."""
    txt = open(COMPACT + stem + '.txt').read()
    body = txt.split('\n\n', 1)[-1] if txt.startswith('KEY SIGNATURES') else txt
    lines = body.split('\n')
    out = []
    for pi, line in enumerate(lines):
        if part is not None and pi != part:
            continue
        if ': ' not in line:
            continue
        name, rest = line.split(': ', 1)
        bars = rest.split(' | ')
        seg = ' | '.join(bars[lo - 1:hi])
        if seg.strip():
            out.append(f'{name} m{lo}-{hi}: {seg[:max_chars]}')
    if out:
        out.append(passage_notation(stem, lo, hi))
    return '\n'.join(x for x in out if x)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', action='store_true')
    ap.add_argument('--query', nargs=3, metavar=('STEM', 'LO', 'HI'))
    ap.add_argument('--part', type=int, default=None)
    a = ap.parse_args()
    if a.build:
        build()
    elif a.query:
        stem, lo, hi = a.query[0], int(a.query[1]), int(a.query[2])
        res, nq = query(stem, lo, hi, a.part)
        print(f'{nq} n-grams from {stem} m{lo}-{hi}\n')
        for r in res:
            print(f'  {r["weight"]:>6.1f}  {r["score"][:46]:<48} part {r["part"]} '
                  f'm{r["measures"]}  ({r["n_matches"]} matches)')


def self_map(stem, block=4, min_shared=3, top=14, con=None):
    """Where material RECURS INSIDE one piece - the form map.

    Brian: "how do these edits relate to the rest of the piece? ... it's like writing a novel, you
    need to take into account what has come before." The model receives the whole score, but raw
    text with no structural summary. This gives it the outline: which passages restate which.

    Same index, queried against the score itself instead of excluding it.
    """
    close = con is None
    con = con or sqlite3.connect(DB)
    row = con.execute('SELECT id FROM score WHERE stem=?', (stem,)).fetchone()
    if not row:
        if close:
            con.close()
        return []
    sid = row[0]
    import collections
    # hash -> the measure-blocks of THIS piece where it occurs
    occ = collections.defaultdict(set)
    for k, h, ms in con.execute(
            'SELECT kind, h, meas FROM post WHERE sid=? AND kind=1', (sid,)):
        occ[h].add(ms // block)
    link = collections.Counter()
    for h, blocks in occ.items():
        bl = sorted(blocks)
        if len(bl) < 2:
            continue
        for i in range(len(bl)):
            for j in range(i + 1, len(bl)):
                if bl[j] - bl[i] >= 2:              # ignore a shape spilling into the next block
                    link[(bl[i], bl[j])] += 1
    if close:
        con.close()
    out = []
    for (a, b), n in link.most_common():
        if n < min_shared:
            continue
        out.append({'from': f'{a * block + 1}-{(a + 1) * block}',
                    'to': f'{b * block + 1}-{(b + 1) * block}', 'shared': n})
        if len(out) >= top:
            break
    return out


def form_text(stem, block=4):
    """The form map as a line for [COMPUTED]."""
    m = self_map(stem, block=block)
    if not m:
        return 'FORM MAP: no passage in this piece restates another closely enough to report.'
    lines = ['FORM MAP - passages inside THIS piece that restate each other (shared rare shapes).',
             'Use it to see what has already been said and where, before adding to it.']
    for r in m:
        lines.append(f'  bars {r["from"]:<9} <-> bars {r["to"]:<9} ({r["shared"]} shared shapes)')
    return '\n'.join(lines)
