"""What is actually inside IMSLP's symbolic files? Download a random sample of ZIPs and MXLs
(disclaimer cookie set), list ZIP contents by extension, parse MXLs with music21 and count parts."""
import random, urllib.request, zipfile, io, collections, os, sys, time, warnings
warnings.filterwarnings('ignore')
random.seed(3)
rows = [l.rstrip('\n').split('\t') for l in open('imslp_files.tsv')]
UA = {'User-Agent': 'scorewright-research/0.1 (brianellis1997@gmail.com)', 'Cookie': 'imslpdisclaimeraccepted=yes'}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=120).read()
zips = random.sample([r for r in rows if r[0] == 'zip'], 40)
inner = collections.Counter(); zip_kinds = collections.Counter(); ok = 0
for e, size, name, url in zips:
    try:
        data = get(url)
        if not data.startswith(b'PK'):
            zip_kinds['not-a-zip (disclaimer/html?)'] += 1; continue
        z = zipfile.ZipFile(io.BytesIO(data)); ok += 1
        exts = collections.Counter(n.rsplit('.', 1)[-1].lower() for n in z.namelist() if '.' in n)
        inner.update(exts)
        kind = 'notation source' if any(k in exts for k in ('sib', 'mus', 'musx', 'ly', 'mscz', 'mscx', 'xml', 'mxl', 'musicxml', 'cap', 'capx', 'enc', 'nwc')) else ('audio' if any(k in exts for k in ('mp3', 'wav', 'flac', 'ogg')) else ('images/pdf' if any(k in exts for k in ('pdf', 'jpg', 'png', 'tif', 'tiff')) else 'other'))
        zip_kinds[kind] += 1
        time.sleep(1.5)
    except Exception as ex:
        zip_kinds[f'error {type(ex).__name__}'] += 1
print('ZIP sample', len(zips), 'opened', ok, '| kinds:', dict(zip_kinds))
print('  inner extensions:', inner.most_common(15), flush=True)
from music21 import converter
mxls = random.sample([r for r in rows if r[0] == 'mxl'], 25)
parts = []; fails = 0; names = []
for e, size, name, url in mxls:
    try:
        data = get(url)
        p = f'imslp_sample/{name}'
        open(p, 'wb').write(data)
        s = converter.parse(p)
        parts.append(len(s.parts)); names.append((name[:50], len(s.parts), len(s.parts[0].getElementsByClass('Measure')) if s.parts else 0))
        time.sleep(1.5)
    except Exception as ex:
        fails += 1
print('MXL sample', len(mxls), 'parsed', len(parts), 'failed', fails, '| parts per score:', sorted(parts))
for n in names[:12]: print('  ', n)
print('SAMPLE_DONE', flush=True)
