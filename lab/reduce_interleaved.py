"""Interleaved ABC -> rest-reduced interleaved ABC, done line by line, so no bar is ever lost.

NotaGen's preprocessing rebuilds the reduced file from a per-voice dictionary and, for 31% of
Brian's scores (20% of PDMX), that dictionary is shorter than the piece: the reduced files were
TRUNCATED (median 62% of the bars kept, a tenth of them under 13%). Every training run so far
ate those files. The interleaved files are correct, so reduce those directly: keep a voice's
segment when it contains a note, drop it when the bar is only rests; always keep bar 0 in full
so [K:]/clef prefixes survive.

usage: reduce_interleaved.py <interleaved_dir> <out_dir> [index.jsonl]
  writes <out_dir>/<key>/<stem>_<key>.abc (key = folder name from the score's K: field, so the
  existing build_docs.py find_abc() keeps working) and <out_dir>.jsonl with {'path','key'}.
"""
import os, re, sys, json, glob
VOICE = re.compile(r'\[V:(\d+)\]')
NOTE = re.compile(r'[A-Ga-g]')
PC = {'C': 'C', 'C#': 'C#', 'Db': 'Db', 'D': 'D', 'Eb': 'Eb', 'E': 'E', 'F': 'F', 'F#': 'F#', 'Gb': 'Gb', 'G': 'G',
      'Ab': 'Ab', 'A': 'A', 'Bb': 'Bb', 'B': 'B', 'Cb': 'Cb'}
REL = {'min': 3, 'm': 3, 'dor': 10, 'phr': 8, 'lyd': 5, 'mix': 7, 'loc': 1}
NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
PCN = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'Fb': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11, 'Cb': 11}


def key_folder(kfield):
    m = re.match(r'^([A-G][#b]?)\s*(min|dor|phr|lyd|mix|loc|maj|m)?', (kfield or 'C').strip())
    if not m:
        return 'C'
    pc = (PCN.get(m.group(1), 0) + REL.get((m.group(2) or '').lower(), 0)) % 12
    return NAMES[pc]


def strip_marks(seg):
    """text with decorations, quoted text and inline fields removed, for the note test."""
    s = re.sub(r'![^!]*!', '', seg)
    s = re.sub(r'"[^"]*"', '', s)
    s = re.sub(r'\[[A-Z]:[^\]]*\]', '', s)
    return s


def reduce_text(text):
    lines = [l for l in text.split('\n') if l.strip()]
    bi = next((i for i, l in enumerate(lines) if l.startswith('[V:')), None)
    if bi is None:
        return None, None
    header, body = lines[:bi], lines[bi:]
    kfield = next((l[2:] for l in header if l.startswith('K:')), 'C')
    out = []
    for i, line in enumerate(body):
        idx = [(m.start(), int(m.group(1))) for m in VOICE.finditer(line)]
        segs = []
        for n, (st, v) in enumerate(idx):
            en = idx[n + 1][0] if n + 1 < len(idx) else len(line)
            segs.append(line[st:en])
        if i == 0:
            out.append(''.join(segs))
        else:
            keep = [s for s in segs if NOTE.search(strip_marks(s[s.index(']') + 1:]))]
            out.append(''.join(keep) if keep else segs[0])
    return '\n'.join(header + out) + '\n', key_folder(kfield)


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    files = sorted(glob.glob(os.path.join(src, '*.abc')))
    n = ok = 0; index = []
    for f in files:
        n += 1
        try:
            txt = open(f, encoding='utf-8', errors='ignore').read()
            red, key = reduce_text(txt)
        except Exception:
            red = None
        if not red:
            continue
        stem = os.path.splitext(os.path.basename(f))[0]
        os.makedirs(os.path.join(dst, key), exist_ok=True)
        open(os.path.join(dst, key, f'{stem}_{key}.abc'), 'w', encoding='utf-8').write(red)
        index.append({'path': os.path.join(dst, stem), 'key': key}); ok += 1
        if n % 5000 == 0:
            print(f'{n}/{len(files)}', flush=True)
    with open(dst + '.jsonl', 'w') as w:
        for r in index:
            w.write(json.dumps(r) + '\n')
    print(f'REDUCE_DONE {ok}/{n} -> {dst}')
