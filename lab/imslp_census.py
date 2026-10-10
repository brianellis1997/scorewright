"""Census of EVERY file on IMSLP by extension, via the MediaWiki API (old-style query-continue).
Writes non-PDF, non-image file names to imslp_files.tsv so we know exactly how much symbolic
material (mxl, mscz, mid, zip-of-sources) exists, not a guess."""
import json, urllib.request, urllib.parse, time, collections, sys
UA = {'User-Agent': 'scorewright-research/0.1 (brianellis1997@gmail.com)'}
def api(params):
    req = urllib.request.Request('https://imslp.org/api.php?' + urllib.parse.urlencode(params), headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=90))
ext = collections.Counter(); tot = 0; aifrom = None; pages = 0; t0 = time.time()
KEEP = {'mxl', 'xml', 'musicxml', 'mscz', 'mscx', 'mid', 'midi', 'zip', 'sib', 'mus', 'musx', 'ly', 'cap', 'capx', 'enc', 'nwc', 'abc', 'krn'}
out = open('imslp_files.tsv', 'w')
while True:
    p = dict(action='query', list='allimages', ailimit='500', aiprop='size|url', format='json')
    if aifrom: p['aifrom'] = aifrom
    for attempt in range(5):
        try:
            r = api(p); break
        except Exception as e:
            time.sleep(5 * (attempt + 1)); r = None
    if r is None:
        print('giving up at', aifrom, flush=True); break
    for i in r['query']['allimages']:
        tot += 1
        e = i['name'].rsplit('.', 1)[-1].lower() if '.' in i['name'] else '?'
        ext[e] += 1
        if e in KEEP:
            out.write(f"{e}\t{i.get('size', 0)}\t{i['name']}\t{i.get('url', '')}\n")
    pages += 1
    nxt = None
    if 'continue' in r: nxt = r['continue'].get('aicontinue')
    elif 'query-continue' in r: nxt = r['query-continue'].get('allimages', {}).get('aifrom') or r['query-continue'].get('allimages', {}).get('aicontinue')
    if pages % 100 == 0:
        out.flush(); print(f'{tot} files, {time.time()-t0:.0f}s, top: {ext.most_common(8)}', flush=True)
    if not nxt: break
    aifrom = nxt; time.sleep(0.25)
out.close()
print('CENSUS_DONE total', tot)
for e, n in ext.most_common(30): print(f'  {e:10s} {n}')
