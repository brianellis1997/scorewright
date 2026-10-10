"""Extract a Text2Score plan (.pkl) for every score in Brian's corpus, using their own pipeline,
so a fine-tune can learn 'his texture, given a plan'. CPU only, resumable, 4 workers."""
import os, sys, glob, pickle, time, warnings
warnings.filterwarnings('ignore')
from concurrent.futures import ProcessPoolExecutor, as_completed
T2S = '/Users/bdogellis/Documents/Score Exports/_models/_text2score'
SRC = '/Users/bdogellis/Documents/Score Exports/MusicXML'
OUT = '/Users/bdogellis/Documents/Score Exports/plans'
os.makedirs(OUT, exist_ok=True)


def one(path):
    sys.path.insert(0, T2S)
    import numpy as np
    from text2music.data.utils.xml2plan import get_full_plan_pipeline
    stem = os.path.splitext(os.path.basename(path))[0]
    dst = f'{OUT}/{stem}.pkl'
    if os.path.exists(dst):
        return stem, 'skip'
    try:
        plan = get_full_plan_pipeline(path)
        def conv(o):
            if isinstance(o, dict): return {k: conv(v) for k, v in o.items()}
            if isinstance(o, (list, set)): return [conv(i) for i in o]
            if isinstance(o, (np.integer, np.floating)): return o.item()
            return o
        pickle.dump(conv(plan), open(dst, 'wb'))
        return stem, 'ok'
    except Exception as e:
        return stem, f'ERR {type(e).__name__}: {str(e)[:80]}'


if __name__ == '__main__':
    files = sorted(glob.glob(f'{SRC}/*.musicxml'))
    t0 = time.time(); n = {'ok': 0, 'skip': 0, 'err': 0}
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = [ex.submit(one, f) for f in files]
        for i, fu in enumerate(as_completed(futs), 1):
            stem, st = fu.result()
            n['ok' if st == 'ok' else 'skip' if st == 'skip' else 'err'] += 1
            if st.startswith('ERR'):
                print(f'  {stem}: {st}', flush=True)
            if i % 100 == 0:
                print(f'{i}/{len(files)} ok={n["ok"]} skip={n["skip"]} err={n["err"]} {time.time()-t0:.0f}s', flush=True)
    print(f'PLANS_DONE {n} {time.time()-t0:.0f}s', flush=True)
