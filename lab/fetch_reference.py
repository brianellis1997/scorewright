"""Reference scores by other composers for the Phrase Atlas: download, name, and index them like
Brian's own (harmony_index.py), so his phrases can be compared with Chopin's, Bach's, Mozart's,
Rachmaninoff's. Brian, Oct 10 2026: "definitely include Chopin pieces, Bach pieces, Rachmaninoff
stuff, and Mozart and stuff like that."

Sources (the music is public domain; the encodings are not cleared for commercial use, so this is
for his own atlas until a product source is chosen):
- ASAP dataset (github.com/fosfrancesco/asap-dataset, CC BY-NC-SA 4.0): MusicXML piano works by Bach,
  Beethoven, Liszt, Schubert, Haydn, Schumann, Rachmaninoff, Ravel, Debussy, Scriabin and others.
  Its Chopin and Mozart are skipped: the two sets below cover them more fully.
- Chopin, complete opus works (github.com/craigsapp/chopin-humdrum-nifc, Humdrum, no licence stated):
  every piece, from the first of its source editions.
- Mozart piano sonatas (github.com/craigsapp/mozart-piano-sonatas, Humdrum).
- music21's bundled corpus: Bach chorales and more, Mozart, Beethoven and Haydn quartets, Schumann.

Files go to Score Exports/reference/files/<Composer>__<title>.<ext>; the index to
Score Exports/_logs/harmony_index_ref/. Never into the repo.
usage (whisperer env): python fetch_reference.py [--jobs 4]"""
import argparse, json, os, re, sys, urllib.request
from multiprocessing import Pool

E = '/Users/bdogellis/Documents/Score Exports'
DST = f'{E}/reference/files'
IDX = f'{E}/_logs/harmony_index_ref'
HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://api.github.com/repos/{}/git/trees/{}?recursive=1'
RAW = 'https://raw.githubusercontent.com/{}/{}/{}'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'scorewright-reference'})
    return urllib.request.urlopen(req, timeout=60).read()


def slug(s):
    return re.sub(r'[^A-Za-z0-9.]+', ' ', s).strip().replace(' ', '_')[:80]


def save(composer, title, ext, data):
    p = f'{DST}/{composer}__{slug(title)}.{ext}'
    if not os.path.exists(p):
        open(p, 'wb').write(data)
    return p


def asap():
    tree = json.loads(get(API.format('fosfrancesco/asap-dataset', 'master')))['tree']
    paths = [t['path'] for t in tree if t['path'].endswith('.musicxml')]
    have = set(paths)
    for p in paths:
        composer = p.split('/')[0]
        if composer in ('Chopin', 'Mozart') or ('_no_repeat' in p and p.replace('_no_repeat', '') in have):
            continue
        title = ' '.join(p.split('/')[1:-1]).replace('_', ' ')
        yield save(composer, title, 'musicxml', get(RAW.format('fosfrancesco/asap-dataset', 'master', p)))


def humdrum(repo, composer, one_per_piece):
    tree = json.loads(get(API.format(repo, 'main')))['tree']
    seen = set()
    for p in sorted(t['path'] for t in tree if t['path'].endswith('.krn')):
        name = p.rsplit('/', 1)[-1][:-4]
        key = '-'.join(name.split('-')[:2]) if one_per_piece else name
        if key in seen:
            continue
        seen.add(key)
        data = get(RAW.format(repo, 'main', p))
        txt = data.decode('utf-8', 'ignore')
        t = re.search(r'^!!!OTL[^:]*:\s*(.+)$', txt, re.M)
        n = re.search(r'^!!!OPS:\s*(.+)$', txt, re.M)
        title = (t.group(1).strip() if t else name) + (f' Op. {n.group(1).strip()}' if n and 'Op' not in (t.group(1) if t else '') else '')
        yield save(composer, f'{title} {key}', 'krn', data)


CHOPIN_GENRES = [('fantaisie impromptu', 'Fantaisie-Impromptu'), ('nocturne', 'Nocturne'), ('etude', 'Etude'), ('ballade', 'Ballade'),
                 ('scherzo', 'Scherzo'), ('mazurka', 'Mazurka'), ('mazourka', 'Mazurka'), ('polonaise', 'Polonaise'), ('polonoise', 'Polonaise'),
                 ('valse', 'Waltz'), ('waltz', 'Waltz'), ('prelud', 'Prelude'), ('impromptu', 'Impromptu'), ('sonate', 'Sonata'), ('sonata', 'Sonata'),
                 ('rondo', 'Rondo'), ('variations', 'Variations'), ('concerto', 'Concerto'), ('trio', 'Trio'), ('fantaisie', 'Fantaisie'),
                 ('berceuse', 'Berceuse'), ('barcarolle', 'Barcarolle'), ('bolero', 'Bolero'), ('tarentelle', 'Tarantella'), ('tarantelle', 'Tarantella'),
                 ('allegro de concert', 'Allegro de concert'), ('krakowiak', 'Krakowiak'), ('introduction', 'Introduction and Polonaise')]


CHOPIN_OPUS = {1: 'Rondo', 2: 'Variations', 3: 'Introduction and Polonaise', 4: 'Sonata', 5: 'Rondo', 6: 'Mazurka', 7: 'Mazurka', 8: 'Trio',
               9: 'Nocturne', 10: 'Etude', 11: 'Concerto', 12: 'Variations', 13: 'Fantasy on Polish Airs', 14: 'Krakowiak', 15: 'Nocturne',
               16: 'Rondo', 17: 'Mazurka', 18: 'Waltz', 19: 'Bolero', 20: 'Scherzo', 21: 'Concerto', 22: 'Andante spianato and Polonaise',
               23: 'Ballade', 24: 'Mazurka', 25: 'Etude', 26: 'Polonaise', 27: 'Nocturne', 28: 'Prelude', 29: 'Impromptu', 30: 'Mazurka',
               31: 'Scherzo', 32: 'Nocturne', 33: 'Mazurka', 34: 'Waltz', 35: 'Sonata', 36: 'Impromptu', 37: 'Nocturne', 38: 'Ballade',
               39: 'Scherzo', 40: 'Polonaise', 41: 'Mazurka', 42: 'Waltz', 43: 'Tarantella', 44: 'Polonaise', 45: 'Prelude',
               46: 'Allegro de concert', 47: 'Ballade', 48: 'Nocturne', 49: 'Fantaisie', 50: 'Mazurka', 51: 'Impromptu', 52: 'Ballade',
               53: 'Polonaise', 54: 'Scherzo', 55: 'Nocturne', 56: 'Mazurka', 57: 'Berceuse', 58: 'Sonata', 59: 'Mazurka', 60: 'Barcarolle',
               61: 'Polonaise-Fantaisie', 62: 'Nocturne', 63: 'Mazurka', 64: 'Waltz', 65: 'Cello Sonata', 66: 'Fantaisie-Impromptu', 74: 'Song'}


def chopin_nifc():
    """Files are <opus>[_range]-<edition>-<publisher>-<piece>.krn, one per piece per first edition:
    keep the first edition of each piece and name it by genre, opus and number"""
    repo = 'craigsapp/chopin-humdrum-nifc'
    tree = json.loads(get(API.format(repo, 'main')))['tree']
    first = {}
    for p in sorted(t['path'] for t in tree if t['path'].endswith('.krn')):
        parts = p.rsplit('/', 1)[-1][:-4].split('-')
        opus = re.match(r'\d+', parts[0])
        if opus:
            first.setdefault((int(opus.group()), int(parts[-1]) if parts[-1].isdigit() else 1), p)
    per_opus = {}
    for opus, piece in first:
        per_opus.setdefault(opus, set()).add(piece)
    for (opus, piece), p in sorted(first.items()):
        data = get(RAW.format(repo, 'main', p))
        t = re.search(r'^!!!OTL[^:]*:\s*(.+)$', data.decode('utf-8', 'ignore'), re.M)
        text = (t.group(1) if t else '').lower().replace('.', ' ')
        found = [(text.find(k), name) for k, name in CHOPIN_GENRES if k in text]
        genre = CHOPIN_OPUS.get(opus) or (min(found)[1] if found else 'Piece')
        yield save('Chopin', f'{genre} Op. {opus}' + (f' No. {piece}' if len(per_opus[opus]) > 1 else ''), 'krn', data)


def music21_corpus():
    from music21 import corpus
    keep = {'bach': 'Bach', 'mozart': 'Mozart', 'beethoven': 'Beethoven', 'haydn': 'Haydn', 'schumann_robert': 'Schumann',
            'schumann_clara': 'Clara Schumann', 'chopin': 'Chopin', 'schubert': 'Schubert', 'handel': 'Handel', 'corelli': 'Corelli', 'joplin': 'Joplin'}
    paths = [str(p) for p in corpus.getPaths()]
    as_xml = {p.rsplit('.', 1)[0] for p in paths if p.endswith(('.mxl', '.xml', '.musicxml'))}
    for p in paths:
        rel = p.split('/corpus/')[-1]
        folder = rel.split('/')[0]
        stem, ext = p.rsplit('.', 1)
        if folder not in keep or 'choraleAnalyses' in rel or (ext not in ('mxl', 'xml', 'musicxml') and stem in as_xml):
            continue
        name = rel[len(folder) + 1:].rsplit('.', 1)[0].replace('/', ' ')
        yield save(keep[folder], f'{folder} {name}', ext, open(p, 'rb').read())


def work(path):
    sys.path.insert(0, HERE)
    import harmony_index as hi
    hi.OUT = IDX
    try:
        return hi.index_one(path)
    except Exception as e:
        return os.path.basename(path), f'failed {type(e).__name__}'


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--only', help='one source: asap, chopin, mozart or music21')
    a = ap.parse_args()
    os.makedirs(DST, exist_ok=True)
    os.makedirs(IDX, exist_ok=True)
    files = []
    sources = {'asap': lambda: asap(), 'chopin': lambda: chopin_nifc(),
               'mozart': lambda: humdrum('craigsapp/mozart-piano-sonatas', 'Mozart', False), 'music21': lambda: music21_corpus()}
    for name, make in sources.items():
        if a.only and name != a.only:
            continue
        got = list(make())
        print(name, len(got), 'files', flush=True)
        files += got
    with Pool(a.jobs, maxtasksperchild=20) as pool:
        res = pool.map(work, files, chunksize=4)
    print('indexed', sum(1 for _, s in res if s in ('ok', 'skip') or s is None), 'of', len(files),
          '; failed', [n for n, s in res if s and str(s).startswith('failed')][:20], flush=True)
