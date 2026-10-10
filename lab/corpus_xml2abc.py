"""MusicXML/MXL -> standard ABC for a list of files, with NotaGen's xml2abc.py (Wim Vree),
4 workers, resumable. Usage: corpus_xml2abc.py <list.txt or folder> <out_dir> [limit]"""
import os, sys, glob, subprocess, time
from concurrent.futures import ProcessPoolExecutor, as_completed
XML2ABC = '/Users/bdogellis/repos/scorewright/lab/NotaGen/data/xml2abc.py'
PY = '/Users/bdogellis/miniforge3/envs/whisperer/bin/python'
src, out = sys.argv[1], sys.argv[2]
limit = int(sys.argv[3]) if len(sys.argv) > 3 else 0
os.makedirs(out, exist_ok=True)
if src.endswith('.txt'):
    base = os.path.dirname(os.path.abspath(src))
    files = [os.path.join(base, l.strip().lstrip('./')) for l in open(src) if l.strip()]
else:
    files = sorted(glob.glob(f'{src}/*.musicxml') + glob.glob(f'{src}/*.xml') + glob.glob(f'{src}/*.mxl'))
if limit: files = files[:limit]

def one(f):
    stem = os.path.splitext(os.path.basename(f))[0]
    dst = os.path.join(out, stem + '.abc')
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return 'skip'
    try:
        r = subprocess.run([PY, '-W', 'ignore', XML2ABC, '-o', out, f], capture_output=True, text=True, timeout=180)
        return 'ok' if os.path.exists(dst) and os.path.getsize(dst) > 0 else 'fail'
    except Exception:
        return 'fail'

if __name__ == '__main__':
    t0 = time.time(); n = {'ok': 0, 'skip': 0, 'fail': 0}
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(one, f) for f in files]
        for i, fu in enumerate(as_completed(futs), 1):
            n[fu.result()] += 1
            if i % 500 == 0:
                print(f'{i}/{len(files)} {n} {time.time()-t0:.0f}s', flush=True)
    print(f'XML2ABC_DONE {len(files)} {n} {time.time()-t0:.0f}s', flush=True)
