"""Derived-edit records + rest-reduced ABC (original key) + MusicXML -> training documents.

usage: build_docs.py <edits.jsonl> <augmented_root> <index.jsonl or ''> <xml_dir> <out.jsonl> [eval_frac]
  augmented_root: NotaGen-style folder with <key>/<stem>_<key>.abc (rest-reduced, interleaved)
  index.jsonl:    NotaGen index with {'path': .../<stem>, 'key': 'Bmin'} to pick the original key;
                  pass '' to search every key folder for the stem (slower, works without an index)
Writes out.jsonl and, if eval_frac > 0, out_eval.jsonl split BY SCORE so no score leaks across.
"""
import os, sys, json, re, random, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_format

PC = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'Fb': 4, 'E#': 5, 'F': 5, 'F#': 6, 'Gb': 6,
      'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11, 'B#': 0}
NAME = {0: ['C'], 1: ['Db', 'C#'], 2: ['D'], 3: ['Eb'], 4: ['E'], 5: ['F'], 6: ['F#', 'Gb'], 7: ['G'], 8: ['Ab'], 9: ['A'], 10: ['Bb'], 11: ['B', 'Cb']}


def key_folders(key):
    m = re.match(r'^([A-G][#b]?)(min|dor|phr|lyd|mix|loc|maj|m)?$', key or '')
    if not m:
        return []
    pc = PC.get(m.group(1), 0)
    pc = (pc + {'min': 3, 'm': 3, 'dor': 10, 'phr': 8, 'lyd': 5, 'mix': 7, 'loc': 1}.get(m.group(2) or '', 0)) % 12
    return NAME[pc]


def find_abc(root, stem, key):
    for k in key_folders(key):
        p = os.path.join(root, k, f'{stem}_{k}.abc')
        if os.path.exists(p):
            return p
    hits = glob.glob(os.path.join(root, '*', f'{stem}_*.abc'))
    return hits[0] if hits else None


if __name__ == '__main__':
    edits, root, index, xml_dir, out = sys.argv[1:6]
    eval_frac = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0
    keys = {}
    if index:
        for l in open(index):
            r = json.loads(l); keys[os.path.basename(r['path'])] = r.get('key')
    recs = [json.loads(l) for l in open(edits)]
    cap = int(os.environ.get('MAX_PER_SCORE_KIND', 0))
    if cap:
        random.seed(3); random.shuffle(recs); seen = {}
        kept = []
        for r in recs:
            k = (r['score'], r['kind']); seen[k] = seen.get(k, 0) + 1
            if seen[k] <= cap: kept.append(r)
        print(f'capped {len(recs)} -> {len(kept)} records ({cap} per score and kind)', flush=True); recs = kept
    xml_map = {}
    if xml_dir.endswith('.txt'):
        base = os.path.dirname(os.path.abspath(xml_dir))
        for l in open(xml_dir):
            if l.strip():
                pth = os.path.join(base, l.strip().lstrip('./')); xml_map[os.path.splitext(os.path.basename(pth))[0]] = pth
    scores = sorted({r['score'] for r in recs})
    random.seed(7); random.shuffle(scores)
    eval_scores = set(scores[:int(len(scores) * eval_frac)])
    outs = {'train': open(out, 'w'), 'eval': open(out.replace('.jsonl', '_eval.jsonl'), 'w') if eval_frac else None}
    n = ok = 0; cache = {}
    for r in recs:
        n += 1
        stem = r['score']
        if stem not in cache:
            abc = find_abc(root, stem, keys.get(stem))
            xml = xml_map.get(stem) if xml_map else next((os.path.join(xml_dir, stem + e) for e in ('.musicxml', '.xml', '.mxl') if os.path.exists(os.path.join(xml_dir, stem + e))), None)
            cache[stem] = (open(abc, encoding='utf-8').read() if abc else None, xml)
        abc_text, xml = cache[stem]
        if not abc_text or not xml:
            continue
        try:
            doc = edit_format.build(r, abc_text, xml)
        except Exception:
            doc = None
        if doc:
            f = outs['eval'] if stem in eval_scores and outs['eval'] else outs['train']
            f.write(json.dumps(doc) + '\n'); ok += 1
        if n % 2000 == 0:
            print(f'{n}/{len(recs)} docs {ok}', flush=True)
    print(f'BUILD_DONE {ok}/{n} documents from {len(scores)} scores ({len(eval_scores)} eval scores)', flush=True)
