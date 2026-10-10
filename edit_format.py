"""Build instructed-infill training documents (PROJECT.md section 49) from a derive_edits record
and the score's rest-reduced interleaved ABC.

Document:
    %%instruction: <text>
    <ABC header lines>
    <body lines; the requested voices/bars replaced by placeholders `[V:k]?|`, or whole lines by `?`>
    %%answer
    <the removed material, one line per bar: [b:<bar index>][V:k]...|[V:j]...|>
Loss is taken on everything after the `%%answer` line. The answer keeps the exact interleaved
format the model already writes, so inference is: write the document up to `%%answer`, let the
model continue, splice the answer lines back into the score by [b:] index and [V:] number.
"""
import os, re, json, random

VOICE_RE = re.compile(r'\[V:(\d+)\]')


def parse_abc(text):
    lines = [l for l in text.split('\n') if l.strip()]
    bi = next((i for i, l in enumerate(lines) if l.startswith('[V:')), None)
    if bi is None:
        return None, None, None
    header, body = lines[:bi], lines[bi:]
    names = {}
    for l in header:
        m = re.match(r'^V:(\d+)\b.*?nm="([^"]*)"', l)
        if m:
            names[int(m.group(1))] = m.group(2)
    return header, body, names


def segments(line):
    """[(voice, segment_text)] in order of appearance; segment includes its [V:k] tag and bar."""
    idx = [(m.start(), int(m.group(1))) for m in VOICE_RE.finditer(line)]
    out = []
    for n, (st, v) in enumerate(idx):
        en = idx[n + 1][0] if n + 1 < len(idx) else len(line)
        out.append((v, line[st:en]))
    return out


_MIDX = {}


def measure_index(xml_path):
    if xml_path in _MIDX:
        return _MIDX[xml_path]
    r = _measure_index(xml_path)
    if len(_MIDX) > 4000:
        _MIDX.clear()
    _MIDX[xml_path] = r
    return r


def _measure_index(xml_path):
    """measure number (as written in the MusicXML) -> 0-based position, from the first part."""
    txt = open(xml_path, encoding='utf-8', errors='ignore').read() if not xml_path.endswith('.mxl') else _mxl_text(xml_path)
    first = txt.split('</part>')[0]
    nums = re.findall(r'<measure[^>]*\bnumber="([^"]+)"', first)
    out = {}
    for i, n in enumerate(nums):
        try:
            out.setdefault(int(n), i)
        except ValueError:
            pass
    return out


def _mxl_text(path):
    import zipfile
    z = zipfile.ZipFile(path)
    name = next(n for n in z.namelist() if n.endswith('.xml') and not n.startswith('META-INF'))
    return z.read(name).decode('utf-8', errors='ignore')


def voice_for(part_idx, part_name, names):
    for v, n in names.items():
        if n == part_name:
            return v
    return part_idx + 1


ORD = {1: 'first', 2: 'second', 3: 'third', 4: 'fourth'}


def instruction(rec, vnames):
    lo, hi = rec['bars']
    span = f'bars {lo}-{hi}' if lo != hi else f'bar {lo}'
    k = rec['kind']
    if k == 'double':
        src, dst = rec['parts']
        d = rec['detail']
        how = {'unison': 'in unison', 'octave up': 'an octave up', 'octave down': 'an octave down',
               'two octaves up': 'two octaves up', 'two octaves down': 'two octaves down'}[d]
        return random.choice([
            f'double the {src} line {how} in the {dst}, {span}',
            f'{dst}: double {src} {how}, {span}',
            f'add a doubling of the {src} to the {dst} {how} for {span}',
            f'have the {dst} double the {src} {how} in {span}'])
    if k == 'fill_harmony':
        (p,) = rec['parts']
        return random.choice([
            f'fill in the harmony in the {p}, {span}',
            f'write a sustained inner voice for the {p} that fits the harmony, {span}',
            f'{p} is empty in {span}; give it a supporting harmony part',
            f'add held harmony notes in the {p} for {span}'])
    if k == 'continue':
        n = hi - lo + 1
        return random.choice([
            f'continue the piece for {n} more bars',
            f'write the next {n} bars',
            f'finish the passage: {n} bars that follow from what came before',
            f'compose {n} bars that continue this'])
    if k == 'infill':
        return random.choice([
            f'fill in {span} for all instruments so the music connects bar {lo - 1} to bar {hi + 1}',
            f'{span} are missing in every part; write them',
            f'complete the gap at {span}',
            f'write {span}, all parts, to bridge the music on either side'])
    return f'{k} {span}'


def build(rec, abc_text, xml_path):
    header, body, names = parse_abc(abc_text)
    if header is None:
        return None
    midx = measure_index(xml_path)
    lo, hi = rec['bars']
    if lo not in midx or hi not in midx:
        return None
    i0, i1 = midx[lo], midx[hi]
    if i1 >= len(body) or i0 > i1:
        return None
    kind = rec['kind']
    targets = [voice_for(pi, pn, names) for pi, pn in zip(rec['part_idx'], rec['parts'])]
    if kind == 'double':
        targets = targets[1:]                      # remove the DOUBLING voice, keep the source
    ctx, ans = list(body), []
    if kind in ('double', 'fill_harmony'):
        for i in range(i0, i1 + 1):
            segs = segments(body[i])
            present = {v for v, _ in segs}
            keep, removed = [], []
            for v, seg in segs:
                (removed if v in targets else keep).append((v, seg))
            if not removed:
                return None                        # the voice rests here in the reduced text; skip example
            for v in sorted(set(targets) - present):
                pass                               # resting target voices simply stay absent
            ph = [(v, f'[V:{v}]?|') for v in sorted(t for t in targets if t in present)]
            merged = sorted(keep + ph, key=lambda t: t[0])
            ctx[i] = ''.join(seg for _, seg in merged)
            ans.append(f'[b:{i}]' + ''.join(seg for _, seg in sorted(removed, key=lambda t: t[0])))
    elif kind == 'infill':
        for i in range(i0, i1 + 1):
            ans.append(f'[b:{i}]' + body[i])
            ctx[i] = '?'
    elif kind == 'continue':
        ans = [f'[b:{i}]' + body[i] for i in range(i0, i1 + 1)]
        ctx = body[:i0]
    else:
        return None
    ctx = [f'[b:{i}]' + l for i, l in enumerate(ctx)]
    text = '%%instruction: ' + instruction(rec, names) + '\n' + '\n'.join(header + ctx) + '\n%%answer\n' + '\n'.join(ans) + '\n'
    return dict(text=text, answer_start=text.index('%%answer\n') + len('%%answer\n'), kind=kind, score=rec['score'])


if __name__ == '__main__':
    import sys
    recs_path, abc_dir, xml_dir, out = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    n = ok = 0
    with open(out, 'w') as f:
        for line in open(recs_path):
            rec = json.loads(line); n += 1
            if limit and n > limit:
                break
            abc = os.path.join(abc_dir, rec['score'] + '.abc')
            xml = next((os.path.join(xml_dir, rec['score'] + e) for e in ('.musicxml', '.xml', '.mxl')
                        if os.path.exists(os.path.join(xml_dir, rec['score'] + e))), None)
            if not os.path.exists(abc) or xml is None:
                continue
            doc = build(rec, open(abc, encoding='utf-8').read(), xml)
            if doc:
                f.write(json.dumps(doc) + '\n'); ok += 1
    print(f'FORMAT_DONE {ok}/{n} documents -> {out}')


# ---- marking tasks: strip a class of markings from the target bars, ask for them back ---------
DYN_RE = re.compile(r'!(p{1,4}|f{1,4}|mp|mf|sfz|sfp|fp|fz|<\(|<\)|>\(|>\)|crescendo\(|crescendo\)|diminuendo\(|diminuendo\)|cresc\(|cresc\)|dim\(|dim\))!')
ART_RE = re.compile(r'!(tenuto|staccato|accent|>|\^|marcato|wedge|upbow|downbow|fermata|trill|turn|mordent|slide)!')
PED_RE = re.compile(r'!(ped|ped-up)!')
MARK_KINDS = {'dynamics': (DYN_RE, 'dynamics'), 'articulation': (ART_RE, 'articulations'), 'pedal': (PED_RE, 'pedal markings')}


def mark_records(abc_text, stem, window=4, min_marks=3, rnd=None):
    """Derive marking records straight from the reduced ABC: 4-bar windows that carry at least
    min_marks of a class -> {score, kind, bars(0-based indexes here), n_marks}."""
    rnd = rnd or random
    header, body, names = parse_abc(abc_text)
    if header is None:
        return []
    out = []
    for kind, (rx, _) in MARK_KINDS.items():
        counts = [len(rx.findall(l)) for l in body]
        starts = [i for i in range(0, max(0, len(body) - window + 1)) if sum(counts[i:i + window]) >= min_marks]
        rnd.shuffle(starts)
        taken = set()
        for i in starts[:6]:
            if any(j in taken for j in range(i, i + window)):
                continue
            taken.update(range(i, i + window))
            out.append(dict(score=stem, kind=kind, idx=[i, i + window - 1], n_marks=sum(counts[i:i + window])))
    return out


def build_marks(rec, abc_text):
    header, body, names = parse_abc(abc_text)
    if header is None:
        return None
    rx, word = MARK_KINDS[rec['kind']]
    i0, i1 = rec['idx']
    if i1 >= len(body):
        return None
    ctx = list(body); ans = []
    for i in range(i0, i1 + 1):
        ans.append(f'[b:{i}]' + body[i])
        ctx[i] = rx.sub('', body[i])
    span = f'bars {i0 + 1}-{i1 + 1}'
    instr = random.choice([f'add {word} to {span}', f'{span} have no {word}; write them in',
                           f'mark up {span} with {word}', f'put {word} on {span}, all parts'])
    ctx = [f'[b:{i}]' + l for i, l in enumerate(ctx)]
    text = '%%instruction: ' + instr + '\n' + '\n'.join(header + ctx) + '\n%%answer\n' + '\n'.join(ans) + '\n'
    return dict(text=text, answer_start=text.index('%%answer\n') + len('%%answer\n'), kind=rec['kind'], score=rec['score'])
