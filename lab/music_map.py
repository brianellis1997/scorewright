"""A map of a composer's phrases: every phrase of every score placed by what it sounds like, in four
views (overall, melody, rhythm, harmony), with nearest neighbours and clusters named in words.

Brian, Oct 10 2026: "upload your scores and we'll visualize your motifs, your harmonic patterns...
a wow factor." It reads the chord-and-melody index (harmony_index.py), so any folder of MusicXML
works the same way: index it, then map it.

Phrases are cut where a singer would breathe: at a rest of a quarter or more, and phrases longer than
eight bars are split at their longest note. Features are independent of key and tempo: interval
classes and contour for melody; note values, triplets, syncopation and rests for rhythm; chord
colours, root motion and harmonic rhythm for harmony. Each view: z-scores, PCA, k-means clusters
(fit in the PCA space, not the picture), UMAP to 2D, and neighbours from other pieces.

With --ref (an index of other composers, from fetch_reference.py) their phrases share the layout,
and every phrase also gets its nearest phrases by those composers.

usage (whisperer env): python music_map.py [--index DIR] [--ref DIR] [--extra "Name=score.musicxml" ...] [--out DIR] [--respread]
writes map.json (pieces, coordinates, regions, neighbours), notes.json (own and extra phrases' notes
and chords) and notes_ref.json (the reference composers') to --out (default: Score Exports/_logs/music_map)"""
import argparse, glob, json, math, os, re, sys, tempfile
import numpy as np

E = '/Users/bdogellis/Documents/Score Exports'
HERE = os.path.dirname(os.path.abspath(__file__))
VIEWS = ['overall', 'melody', 'rhythm', 'harmony']
K = 8
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
QNAME = {'maj': '', 'min': 'm', 'dim': 'dim', 'aug': '+', 'sus4': 'sus4', 'sus2': 'sus2', '7sus4': '7sus4', '7': '7',
         'maj7': 'maj7', 'm7': 'm7', 'm7b5': 'ø7', 'dim7': 'o7', 'add9': 'add9', 'madd9': 'm(add9)', 'maj9': 'maj9',
         'm9': 'm9', '6': '6', 'm6': 'm6', 'mmaj7': 'm(maj7)', '9': '9', '7b9': '7b9', '7#5': '7#5'}
COLOUR = {'maj': 'major', 'min': 'minor', 'sus4': 'sus', 'sus2': 'sus', '7sus4': 'sus', '7': 'dominant', '9': 'dominant',
          '7b9': 'dominant', '7#5': 'dominant', 'maj7': 'maj7/add9', 'maj9': 'maj7/add9', 'add9': 'maj7/add9', '6': 'maj7/add9',
          'm7': 'minor 7/9', 'm9': 'minor 7/9', 'madd9': 'minor 7/9', 'm6': 'minor 7/9', 'mmaj7': 'minor 7/9',
          'dim': 'diminished', 'dim7': 'diminished', 'm7b5': 'diminished', 'aug': 'augmented'}
COLOURS = ['major', 'minor', 'sus', 'dominant', 'maj7/add9', 'minor 7/9', 'diminished', 'augmented']

# feature name -> (words when a cluster has more of it, words when it has less)
MEL = {'repeat': ('repeated notes', None), 'step': ('stepwise', None), 'third': ('thirds', None), 'leap': ('leaps', 'no leaps'),
       'wide': ('wide leaps', None), 'chrom': ('chromatic', None), 'up': ('rising', 'falling'), 'net': ('ends high', 'ends low'),
       'range': ('wide range', 'narrow range'), 'zigzag': ('zigzag', 'smooth lines'), 'peak': ('peaks late', 'peaks early'),
       'run': ('long scale runs', None), 'arp': ('arpeggios', None), 'turn': ('turns', None)}
RHY = {'tempo': ('fast tempo', 'slow tempo'), 'speed': ('rapid notes', 'unhurried'), 'sixteenth': ('sixteenths', None), 'triplet': ('triplets', None), 'eighth': ('eighths', None), 'quarter': ('quarters', None),
       'long': ('long notes', None), 'dotted': ('dotted rhythms', None), 'density': ('busy', 'sparse'), 'sync': ('syncopated', 'on the beat'),
       'rest': ('broken by rests', None), 'cell': ('repeated rhythm cells', None), 'bars': ('long phrases', 'short phrases'),
       'pickup': ('pickups', 'starts on the beat')}
HAR = {'none': ('melody alone', None), 'fourth': ('roots up a 4th', None), 'fifth': ('roots up a 5th', None), 'stepup': ('roots step up', None),
       'stepdown': ('roots step down', None), 'third': ('roots by thirds', None), 'tritone': ('tritone roots', None),
       'changes': ('fast changes', 'slow harmony'), 'static': ('held chords', None), 'inv': ('inversions and pedals', None),
       'outside': ('roots outside the key', None)}
HAR.update({'q_' + c: (c + ' chords', None) for c in COLOURS})


def bar_len(ts):
    try:
        n, d = ts.split('/')
        return int(n) * 4 / int(d)
    except ValueError:
        return 4.0


def beat_len(ts):
    n, d = (int(x) for x in ts.split('/')) if '/' in ts else (4, 4)
    return 1.5 * 4 / d if d == 8 and n % 3 == 0 else 4 / d


def load(path):
    d = json.load(open(path))
    notes, wins, bars, t = [], [], [], 0.0
    for b in d['bars']:
        L = bar_len(b['ts'])
        bars.append((b['n'], t, L, b['ks'], b['ts']))
        seen = {}
        for on, du, p in b['m']:
            if du <= 0:
                continue
            k = round(on, 3)
            if k not in seen or p > seen[k][2]:
                seen[k] = (t + on, du, p, b['n'], on, b['ts'], b['ks'])
        notes += sorted(seen.values())
        wl = L / max(1, len(b['w']))
        for i, (r, q, bass) in enumerate(b['w']):
            wins.append((t + i * wl, wl, r, q, bass, b['ks']))
        t += L
    return d, skyline(notes), wins, bars


def skyline(notes):
    """the top voice only: a note that starts while a higher note is still sounding belongs to an inner
    voice and is dropped; a held note is cut where the next melody note starts"""
    out = []
    for n in notes:
        if out and n[0] < out[-1][0] + out[-1][1] - 1e-6:
            if n[2] < out[-1][2]:
                continue
            out[-1] = (out[-1][0], n[0] - out[-1][0]) + out[-1][2:]
        out.append(n)
    return out


def nice_title(t, composer=''):
    t = re.sub(r'^(bach|mozart|beethoven|haydn|schumann robert|schumann clara|chopin|schubert|handel|corelli|joplin)\s+', '', t, flags=re.I)
    if composer == 'Chopin':
        t = re.sub(r'\s\d{3}(\s.*)?$', '', t)
    t = re.sub(r'\bbwv\s*(\d+(?:\.\d+)?)', r'BWV \1', t, flags=re.I)
    t = re.sub(r'\bopus\s*(\d+)\s*no\s*(\d+)', r'Op. \1 No. \2', t, flags=re.I)
    t = re.sub(r'\bopus\s*(\d+)', r'Op. \1', t, flags=re.I)
    t = re.sub(r'\s*\bmovement\s*(\d+)', r', mvt \1', t, flags=re.I)
    t = re.sub(r'\bk\s?(\d+)\b', r'K. \1', t)
    t = re.sub(r'\bno\s?(\d+)\b', r'No. \1', t, flags=re.I)
    t = re.sub(r'\b(Preludes|Etudes|Prelude|Etude)\s+op\s+(\d+)\s+(\d+)\b', lambda m: f'{m.group(1).rstrip("s")} Op. {m.group(2)} No. {m.group(3)}', t, flags=re.I)
    t = re.sub(r'\bPiano Sonatas\s+(\d+)\s+(\d+)', r'Piano Sonata ' + ('D. ' if composer == 'Schubert' else 'No. ') + r'\1, mvt \2', t)
    t = re.sub(r'\s+sonata\d+\s+(\d+)\w*$', r', mvt \1', t)
    t = re.sub(r'\bop(\d+)n(\d+)\b', r'Op. \1 No. \2', t, flags=re.I)
    t = re.sub(r'\bOp\.\s*Op\.', 'Op.', t, flags=re.I)
    t = re.sub(r'\b([A-Z]{4,})\b', lambda m: m.group(1).capitalize(), t)
    t = re.sub(r'\s+', ' ', t).strip(' .')
    return t[:1].upper() + t[1:]


def split_long(ph, max_q):
    if len(ph) < 10 or ph[-1][0] + ph[-1][1] - ph[0][0] <= max_q:
        return [ph]
    n = len(ph)
    lo, hi = n // 4, 3 * n // 4
    cut = max(range(lo, hi), key=lambda i: (ph[i][1] + (ph[i + 1][0] - ph[i][0] - ph[i][1]), -abs(i - n // 2)))
    return split_long(ph[:cut + 1], max_q) + split_long(ph[cut + 1:], max_q)


def phrases(notes, bars):
    out, cur = [], []
    for n in notes:
        if cur and n[0] - (cur[-1][0] + cur[-1][1]) >= 0.999:
            out.append(cur)
            cur = []
        cur.append(n)
    if cur:
        out.append(cur)
    res = []
    for ph in out:
        L = bar_len(ph[0][5])
        res += split_long(ph, 8 * L)
    return [ph for ph in res if len(ph) >= 5]


def frac(xs, f):
    return sum(1 for x in xs if f(x)) / len(xs) if xs else 0.0


def melody_features(ph):
    p = [n[2] for n in ph]
    iv = [b - a for a, b in zip(p, p[1:])]
    a = [abs(x) for x in iv]
    nz = [x for x in a if x]
    dirs = [(x > 0) - (x < 0) for x in iv]
    moving = [x for x in dirs if x]
    changes = sum(1 for x, y in zip(moving, moving[1:]) if x != y)
    run, best = 1, 1
    for x, y in zip(dirs, dirs[1:]):
        run = run + 1 if x == y and x else 1
        best = max(best, run)
    rng = max(p) - min(p)
    arp = sum(1 for x, y in zip(iv, iv[1:]) if 3 <= abs(x) <= 5 and 3 <= abs(y) <= 5 and (x > 0) == (y > 0)) / max(1, len(iv) - 1)
    turn = sum(1 for i in range(len(iv) - 2) if all(1 <= abs(v) <= 2 for v in iv[i:i + 3]) and iv[i] * iv[i + 1] < 0) / max(1, len(iv) - 2)
    return dict(repeat=frac(a, lambda x: x == 0), step=frac(a, lambda x: 1 <= x <= 2), third=frac(a, lambda x: 3 <= x <= 4),
                leap=frac(a, lambda x: x >= 5), wide=frac(a, lambda x: x >= 8), chrom=frac(nz, lambda x: x == 1),
                up=frac(iv, lambda x: x > 0), net=(p[-1] - p[0]) / 12, range=rng / 12, zigzag=changes / max(1, len(moving) - 1),
                peak=int(np.argmax(p)) / max(1, len(p) - 1), run=best / len(p), arp=arp, turn=turn)


def rhythm_features(ph, bpm=80.0):
    du = [n[1] for n in ph]
    span = ph[-1][0] + ph[-1][1] - ph[0][0]
    ts = ph[0][5]
    beat = beat_len(ts)
    near = lambda x, v: abs(x - v) < 0.02
    trip = frac(du, lambda x: any(near(x, v) for v in (1 / 3, 2 / 3, 1 / 6, 4 / 3)))
    gaps = sum(max(0.0, b[0] - (a[0] + a[1])) for a, b in zip(ph, ph[1:]))
    bars = {}
    for n in ph:
        bars.setdefault(n[3], []).append(round(n[4], 2))
    cells = [tuple(v) for _, v in sorted(bars.items())]
    cell = sum(1 for x, y in zip(cells, cells[1:]) if x == y) / max(1, len(cells) - 1)
    return dict(sixteenth=frac(du, lambda x: x <= 0.26), triplet=trip, eighth=frac(du, lambda x: near(x, 0.5)),
                quarter=frac(du, lambda x: near(x, 1.0)), long=frac(du, lambda x: x >= 2), dotted=frac(du, lambda x: any(near(x, v) for v in (0.75, 1.5, 3.0))),
                density=math.log(len(ph) / max(span, 0.25)), sync=frac(ph, lambda n: (n[4] % beat) > 0.01 and n[1] > beat * 0.6),
                rest=gaps / max(span, 0.25), cell=cell, bars=span / bar_len(ts), pickup=1.0 if ph[0][4] > 0.01 else 0.0,
                tempo=math.log(bpm / 80), speed=math.log(max(0.1, len(ph) / max(0.25, span * 60 / bpm))))


TEMPO_WORDS = [('prestissimo', 190), ('presto', 172), ('vivace', 150), ('allegretto', 112), ('allegro', 132), ('moderato', 100),
               ('andantino', 84), ('andante', 76), ('adagietto', 70), ('adagio', 66), ('larghetto', 58), ('largo', 50), ('lento', 56), ('grave', 40)]
EXTRA_SRC = {}


def tempo_of(stem, kind):
    """quarter notes per minute from the score: the first <sound tempo> (MusicXML) or *MM (Humdrum),
    else the first Italian tempo word in its directions; 80 when nothing is marked"""
    if kind == 2:
        cands = glob.glob(f'{E}/reference/files/{glob.escape(stem)}.*')
    elif kind == 1:
        cands = [EXTRA_SRC.get(stem, '')]
    else:
        cands = [f'{E}/MusicXML/{stem}.musicxml', f'{E}/extra_sept2026/MusicXML/{stem}.musicxml']
    for path in cands:
        if not path or not os.path.exists(path):
            continue
        try:
            if path.endswith('.mxl'):
                import zipfile
                with zipfile.ZipFile(path) as z:
                    name = next((n for n in z.namelist() if n.endswith(('.xml', '.musicxml')) and not n.startswith('META')), None)
                    txt = z.read(name).decode('utf-8', 'ignore') if name else ''
            else:
                txt = open(path, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        m = re.search(r'<sound[^>]*\btempo="([\d.]+)"', txt) or re.search(r'^\*MM([\d.]+)', txt, re.M)
        if m and 20 <= float(m.group(1)) <= 300:
            return float(m.group(1))
        mm = re.search(r'<metronome[^>]*>\s*<beat-unit>(\w+)</beat-unit>(\s*<beat-unit-dot\s*/>)?\s*<per-minute>([\d.]+)</per-minute>', txt)
        if mm:
            unit = {'whole': 4, 'half': 2, 'quarter': 1, 'eighth': 0.5, '16th': 0.25}.get(mm.group(1), 1) * (1.5 if mm.group(2) else 1)
            q = float(mm.group(3)) * unit
            if 20 <= q <= 300:
                return q
        words = ' '.join(re.findall(r'<words[^>]*>([^<]+)</words>', txt) + re.findall(r'^!!!OMD[^:]*:\s*(.+)$', txt, re.M)
                         + re.findall(r'^\*MM\[([^\]]+)\]', txt, re.M)).lower()
        hits = [(words.find(w), q) for w, q in TEMPO_WORDS if w in words]
        if hits:
            return float(min(hits)[1])
    return 80.0


def harmony_features(ph, wins, starts):
    t0, t1 = ph[0][0], ph[-1][0] + ph[-1][1]
    i0 = int(np.searchsorted(starts, t0, side='right')) - 1
    ws = [w for w in wins[max(0, i0):] if w[0] < t1 - 1e-6]
    lab = [w for w in ws if w[3]]
    f = dict(none=1 - len(lab) / max(1, len(ws)))
    for c in COLOURS:
        f['q_' + c] = frac(lab, lambda w, c=c: COLOUR.get(w[3]) == c)
    seq = []
    for w in lab:
        if not seq or (w[2], w[3]) != (seq[-1][2], seq[-1][3]):
            seq.append(w)
    mv = [(b[2] - a[2]) % 12 for a, b in zip(seq, seq[1:]) if b[2] != a[2]]
    f.update(fourth=frac(mv, lambda x: x == 5), fifth=frac(mv, lambda x: x == 7), stepup=frac(mv, lambda x: x in (1, 2)),
             stepdown=frac(mv, lambda x: x in (10, 11)), third=frac(mv, lambda x: x in (3, 4, 8, 9)), tritone=frac(mv, lambda x: x == 6))
    nbars = max(1e-6, (t1 - t0) / bar_len(ph[0][5]))
    f['changes'] = min(4.0, (len(seq) - 1) / nbars) if seq else 0.0
    f['static'] = frac(list(zip(lab, lab[1:])), lambda ab: (ab[0][2], ab[0][3]) == (ab[1][2], ab[1][3]))
    f['inv'] = frac(lab, lambda w: w[4] is not None and w[4] % 12 != w[2])
    f['outside'] = frac(lab, lambda w: (w[2] - 7 * w[5]) % 12 not in (0, 2, 4, 5, 7, 9, 11))
    names = [NAMES[w[2]] + QNAME.get(w[3], '') for w in seq]
    timed = []
    for w in ws:
        s, e = max(w[0], t0), min(w[0] + w[1], t1)
        if not w[3] or e <= s:
            continue
        if timed and timed[-1][2:4] == [w[2], w[3]] and abs(timed[-1][5] - s) < 1e-6:
            timed[-1][5] = e
        else:
            timed.append([s, 0, w[2], w[3], w[4], e])
    harm = [[round((s - t0) * 12), max(1, round((e - s) * 12)), r, q, b] for s, _, r, q, b, e in timed]
    return f, names, harm


def phrase_rows(index_paths, kind=0):
    pieces, rows = [], []
    for path in index_paths:
        try:
            d, notes, wins, bars = load(path)
        except Exception as e:
            print('skip', os.path.basename(path), e, file=sys.stderr)
            continue
        if not notes:
            continue
        starts = np.array([w[0] for w in wins]) if wins else np.array([0.0])
        pi = len(pieces)
        d['bpm'] = tempo_of(d['stem'], kind)
        pieces.append(d)
        for ph in phrases(notes, bars):
            m, r = melody_features(ph), rhythm_features(ph, d['bpm'])
            h, chords, harm = harmony_features(ph, wins, starts) if wins else ({}, [], [])
            rows.append(dict(piece=pi, bar=ph[0][3], end=ph[-1][3], m=m, r=r, h=h, chords=chords, harm=harm,
                             notes=[[round((n[0] - ph[0][0]) * 12), max(1, round(n[1] * 12)), n[2]] for n in ph]))
    return pieces, rows


def matrix(rows, key, names):
    return np.array([[row[key].get(n, 0.0) for n in names] for row in rows], dtype=float)


def describe(raw, labels, names, words, k):
    mu, sd = raw.mean(0), raw.std(0) + 1e-9
    out = []
    for c in range(k):
        z = (raw[labels == c].mean(0) - mu) / sd
        picks = []
        for j in np.argsort(-np.abs(z)):
            if abs(z[j]) < 0.35 or len(picks) == 3:
                break
            w = words[names[j]][0 if z[j] > 0 else 1]
            if w and w not in picks:
                picks.append(w)
        out.append(dict(label=', '.join(picks) or 'in between', n=int((labels == c).sum())))
    return out


def spread(xy, n_main):
    """UMAP leaves most phrases in a dense core and repeated or rare ones in far islands; a radial
    log scale around the median keeps the core readable and puts the islands in a ring at the edge"""
    d = xy - np.median(xy[:n_main], 0)
    d = d / (np.percentile(np.abs(d[:n_main]), 98, 0) + 1e-9)
    r = np.hypot(d[:, 0], d[:, 1])
    a = np.median(r[:n_main]) + 1e-9
    rn = np.minimum(1.0, np.log1p(r / a) / np.log1p(np.percentile(r[:n_main], 99.8) / a))
    g = d / np.maximum(r, 1e-9)[:, None] * rn[:, None]
    return np.clip((g + 1) / 2, 0, 1)


def respread(path):
    m = json.load(open(path))
    for v in m['views']:
        g = spread(np.array([m['x'][v], m['y'][v]], float).T, m['n_main'])
        m['x'][v] = [int(t) for t in np.round(g[:, 0] * 999)]
        m['y'][v] = [int(t) for t in np.round(g[:, 1] * 999)]
    json.dump(m, open(path, 'w'), separators=(',', ':'))


def add(pieces, rows, more, more_rows):
    base = len(pieces)
    for r in more_rows:
        r['piece'] += base
    pieces += more
    rows += more_rows


def build(index_paths, extra, ref_paths=()):
    """rows: the composer's own phrases [0, n_main), reference composers' [n_main, n_fit), extra pieces after.
    Scaling, PCA and regions come from the composer's own phrases; the layout from own + reference."""
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    from sklearn.neighbors import NearestNeighbors
    import umap

    pieces, rows = phrase_rows(index_paths, 0)
    for d in pieces:
        d['kind'] = 0
    n_main = len(rows)
    rp, rr = phrase_rows(ref_paths, 2)
    for d in rp:
        comp, _, title = d['stem'].partition('__')
        d.update(kind=2, composer=comp.replace('_', ' '), title=nice_title(title.replace('_', ' '), comp))
    add(pieces, rows, rp, rr)
    n_fit = len(rows)
    xp, xr = phrase_rows(list(extra.values()), 1)
    for d, name in zip(xp, extra):
        d.update(kind=1, title=name)
    add(pieces, rows, xp, xr)
    print(f'{len(pieces)} pieces, {len(rows)} phrases: {n_main} own, {n_fit - n_main} reference, {len(xr)} from {", ".join(extra) or "no extra"}', flush=True)

    blocks = {}
    for key, view, words in (('m', 'melody', MEL), ('r', 'rhythm', RHY), ('h', 'harmony', HAR)):
        names = list(words)
        raw = matrix(rows, key, names)
        mu, sd = raw[:n_main].mean(0), raw[:n_main].std(0) + 1e-9
        blocks[view] = (names, words, raw, np.clip((raw - mu) / sd, -4, 4))
    blocks['overall'] = (None, None, None, np.hstack([z / math.sqrt(z.shape[1]) for _, _, _, z in (blocks[v] for v in ('melody', 'rhythm', 'harmony'))]))

    out = dict(views=VIEWS, n_main=n_main, n_fit=n_fit, x={}, y={}, c={}, nn={}, nr={}, clusters={})
    for view in VIEWS:
        names, words, raw, z = blocks[view]
        pca = PCA(n_components=min(12, z.shape[1]), random_state=7).fit(z[:n_main])
        p = pca.transform(z)
        km = KMeans(n_clusters=K, n_init=10, random_state=7).fit(p[:n_main])
        order = np.argsort(-np.bincount(km.labels_, minlength=K))
        remap = np.empty(K, int)
        remap[order] = np.arange(K)
        lab = remap[km.predict(p)]
        um = umap.UMAP(n_neighbors=25, min_dist=0.08, random_state=7).fit(p[:n_fit])
        xy = np.vstack([um.embedding_, um.transform(p[n_fit:])]) if len(p) > n_fit else um.embedding_
        g = spread(xy, n_main)
        out['x'][view] = [int(v) for v in np.round(g[:, 0] * 999)]
        out['y'][view] = [int(v) for v in np.round(g[:, 1] * 999)]
        out['c'][view] = ''.join(str(int(v)) for v in lab)
        for key, lo, hi in (('nn', 0, n_main), ('nr', n_main, n_fit)):
            if hi <= lo:
                out[key][view] = [[] for _ in rows]
                continue
            _, idx = NearestNeighbors(n_neighbors=40).fit(p[lo:hi]).kneighbors(p)
            out[key][view] = [[int(j + lo) for j in cand if rows[j + lo]['piece'] != rows[i]['piece']][:5] for i, cand in enumerate(idx)]
        if view == 'overall':
            descs = []
            for c in range(K):
                parts = []
                for v in ('melody', 'rhythm', 'harmony'):
                    nm, wd, rw, _ = blocks[v]
                    parts.append(describe(rw[:n_main], lab[:n_main], nm, wd, K)[c]['label'])
                descs.append(dict(label='; '.join(x for x in parts if x != 'in between') or 'in between', n=int((lab[:n_main] == c).sum())))
            out['clusters'][view] = descs
        else:
            out['clusters'][view] = describe(raw[:n_main], lab[:n_main], names, words, K)
        print(view, 'done', flush=True)

    years = {}
    for path in glob.glob(f'{E}/_source_sib/*.sib'):
        years[os.path.basename(path)[:-4]] = int(__import__('datetime').date.fromtimestamp(os.path.getmtime(path)).year)
    out['pieces'] = [dict(t=d.get('title') or d['stem'], y=years.get(d['stem']), q=round(d['bpm']), k=d['kind'], c=d.get('composer'),
                          p=' + '.join(dict.fromkeys(d.get('parts') or []))[:60]) for d in pieces]
    out['piece'] = [r['piece'] for r in rows]
    out['bar'] = [r['bar'] for r in rows]
    out['end'] = [r['end'] for r in rows]
    comp = {}
    for r in rows[n_main:n_fit]:
        c = pieces[r['piece']]['composer']
        comp.setdefault(c, [set(), 0])
        comp[c][0].add(r['piece'])
        comp[c][1] += 1
    out['composers'] = [dict(name=c, pieces=len(v[0]), phrases=v[1]) for c, v in sorted(comp.items(), key=lambda kv: -kv[1][1])]
    ref = lambda i: n_main <= i < n_fit
    pick = lambda want: dict(notes=[r['notes'] if ref(i) == want else None for i, r in enumerate(rows)],
                             chords=[' '.join(r['chords'][:12]) if ref(i) == want else None for i, r in enumerate(rows)],
                             harm=[r['harm'] if ref(i) == want else None for i, r in enumerate(rows)])
    own, others = pick(False), pick(True)
    return out, own, others


def index_extra(spec, tmp):
    name, path = spec.split('=', 1)
    sys.path.insert(0, HERE)
    import harmony_index as hi
    hi.OUT = tmp
    stem, status = hi.index_one(path)
    EXTRA_SRC[stem] = path
    return name, f'{tmp}/{stem}.json'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--index', default=f'{E}/_logs/harmony_index')
    ap.add_argument('--extra', action='append', default=[])
    ap.add_argument('--ref', help='index folder of other composers to compare with (fetch_reference.py)')
    ap.add_argument('--out', default=f'{E}/_logs/music_map')
    ap.add_argument('--respread', action='store_true', help='only redo the 2D spacing of an existing map.json')
    a = ap.parse_args()
    if a.respread:
        respread(f'{a.out}/map.json')
        sys.exit(0)
    os.makedirs(a.out, exist_ok=True)
    tmp = tempfile.mkdtemp()
    extra = dict(index_extra(s, tmp) for s in a.extra)
    paths = sorted(glob.glob(f'{a.index}/*.json'))
    refs = sorted(p for p in glob.glob(f'{a.ref}/*.json') if 'choraleAnalyses' not in p) if a.ref else []
    m, own, others = build(paths, extra, refs)
    json.dump(m, open(f'{a.out}/map.json', 'w'), separators=(',', ':'))
    json.dump(own, open(f'{a.out}/notes.json', 'w'), separators=(',', ':'))
    json.dump(others, open(f'{a.out}/notes_ref.json', 'w'), separators=(',', ':'))
    for f in ('map.json', 'notes.json', 'notes_ref.json'):
        print(f, round(os.path.getsize(f'{a.out}/{f}') / 1e6, 1), 'MB')
