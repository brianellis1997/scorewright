"""Apply an instructed edit to a real score with the edit model: the product path.

  request = dict(kind='infill'|'double'|'fill_harmony'|'continue', bars=[lo,hi], voices=[k..], text=instruction)
  1. score MusicXML -> rest-reduced interleaved ABC (NotaGen pipeline, original key)
  2. blank the requested voices/bars -> document up to %%answer
  3. model writes the answer lines; splice them back by [b:] index and [V:] number
  4. ABC -> MusicXML (post.to_xml) -> splice into the original engraving (splice.splice) -> ranges check
usage: T2S_CKPT=<pth> python t2s_edit_apply.py <score.musicxml> <kind> <lo> <hi> "<instruction>" [voice numbers comma-sep] [tag]
"""
import os, sys, re, json, time, subprocess, warnings
warnings.filterwarnings('ignore')
import torch
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
sys.path.insert(0, os.path.join(HERE, 'ft3'))
import t2s_arm as A
from t2s_arm import PATCH_SIZE, PATCH_LENGTH, DEV
import edit_format as EF
import post, splice
from eval_edit import write_answer, crop, stream_prefix, next_stream_tag
from to_stream_format import convert as to_stream
from forced import write_forced, template_from_truth, voice_ranges_from_header
WH = '/Users/bdogellis/miniforge3/envs/whisperer/bin/python'
XML2ABC = f'{HERE}/NotaGen/data/xml2abc.py'
PREP = f'{HERE}/NotaGen/data/prep_corpus.py'


def score_to_reduced_abc(xml_path, work):
    """MusicXML -> rest-reduced interleaved ABC in the original key, via the corpus pipeline."""
    os.makedirs(f'{work}/abc', exist_ok=True)
    subprocess.run([WH, '-W', 'ignore', XML2ABC, '-o', f'{work}/abc', xml_path], capture_output=True)
    env = dict(os.environ, ORI_FOLDER=f'{work}/abc', INTERLEAVED_FOLDER=f'{work}/abci', AUGMENTED_FOLDER=f'{work}/abcr', EVAL_SPLIT='0', KEYS_ORIG='1')
    subprocess.run([WH, PREP], cwd=os.path.dirname(PREP), env=env, capture_output=True)
    stem = os.path.splitext(os.path.basename(xml_path))[0]
    abci = f'{work}/abci/{stem}.abc'
    if not os.path.exists(abci):
        return None
    sys.path.insert(0, HERE)
    from reduce_interleaved import reduce_text                  # line-by-line: cannot lose bars
    red, key = reduce_text(open(abci, encoding='utf-8', errors='ignore').read())
    return red


def splice_answer(abc_text, answer_lines, kind):
    header, body, names = EF.parse_abc(abc_text)
    body = list(body)
    for line in answer_lines:
        line = re.sub(r'^\[r:[^\]]*\]', '', line)
        line = re.sub(r'^(\[V:\d+\])(\[b:\d+\])', r'\2\1', line)
        m = re.match(r'\[b:(\d+)\](.*)', line)
        if not m:
            continue
        i, content = int(m.group(1)), m.group(2)
        if kind in ('infill', 'continue'):
            if i < len(body): body[i] = content
            else: body.append(content)
        else:
            if i >= len(body):
                continue
            segs = dict(EF.segments(body[i]))
            for v, seg in EF.segments(content):
                segs[v] = seg
            body[i] = ''.join(segs[v] for v in sorted(segs))
    return '\n'.join(header + body) + '\n'


if __name__ == '__main__':
    xml_path, kind, lo, hi, instr = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    voices = [int(v) for v in sys.argv[6].split(',')] if len(sys.argv) > 6 and sys.argv[6] else []
    tag = sys.argv[7] if len(sys.argv) > 7 else 'apply'
    work = f'{HERE}/apply_{tag}'
    abc = score_to_reduced_abc(xml_path, work)
    assert abc, 'conversion failed'
    header, body, names = EF.parse_abc(abc)
    cut = int(os.environ.get('T2S_CUT_AT', 0))
    if cut:
        body = body[:cut]
        abc = '\n'.join(header + body) + '\n'
    midx = EF.measure_index(xml_path)
    i0, i1 = midx.get(lo, 0), midx.get(hi, 0)
    rec = dict(kind=kind, bars=[lo, hi], score=tag)
    if kind == 'double':
        src, dst = voices
        rec['parts'] = [names.get(src, f'V{src}'), names.get(dst, f'V{dst}')]; rec['part_idx'] = [src - 1, dst - 1]; rec['detail'] = 'octave up'
    elif kind == 'fill_harmony':
        (dst,) = voices; rec['parts'] = [names.get(dst, f'V{dst}')]; rec['part_idx'] = [dst - 1]
    else:
        rec['parts'] = [names.get(v, f'V{v}') for v in sorted(names)]; rec['part_idx'] = [v - 1 for v in sorted(names)]
    if kind == 'continue' and hi > len(body):
        n = len(body)
        voices = sorted({v for l in body for v, _ in EF.segments(l)} | set(names))
        ctx = [f'[b:{i}]' + l for i, l in enumerate(body)]
        k = hi - lo + 1
        ans = [f'[b:{n + j}]' + ''.join(f'[V:{v}]?|' for v in voices) for j in range(k)]
        text0 = '%%instruction: ' + instr + '\n' + '\n'.join(header + ctx) + '\n%%answer\n' + '\n'.join(ans) + '\n'
        doc = dict(text=text0, answer_start=text0.index('%%answer\n') + len('%%answer\n'), kind='continue', score=tag)
        lo, hi = n + 1, n + k
    else:
        doc = EF.build(rec, abc, xml_path)
    if not doc and kind == 'fill_harmony':
        (dst,) = voices
        ctx = []
        for i, l in enumerate(body):
            if i0 <= i <= i1:
                segs = dict(EF.segments(l)); segs[dst] = f'[V:{dst}]?|'
                l = ''.join(segs[v] for v in sorted(segs))
            ctx.append(f'[b:{i}]' + l)
        ans = [f'[b:{i}][V:{dst}]?|' for i in range(i0, i1 + 1)]
        text0 = '%%instruction: ' + instr + '\n' + '\n'.join(header + ctx) + '\n%%answer\n' + '\n'.join(ans) + '\n'
        doc = dict(text=text0, answer_start=text0.index('%%answer\n') + len('%%answer\n'), kind='fill_harmony', score=tag)
    assert doc, 'could not build the document (the target voice may rest there)'
    text = doc['text'].replace(doc['text'].split('\n', 1)[0], '%%instruction: ' + instr, 1)
    a0 = text.index('%%answer\n') + len('%%answer\n')
    n_lines = len([l for l in text[a0:].split('\n') if l.strip()])
    text = crop(text, a0, budget_chars=512 * PATCH_SIZE * 0.8)
    STREAM = bool(os.environ.get('T2S_STREAM'))
    if STREAM:
        text = to_stream(text)
    a0 = text.index('%%answer\n') + len('%%answer\n')
    prefix = text[:a0]
    raw_prefix = prefix
    if STREAM:
        prefix = stream_prefix(prefix, n_lines)
    model, pat = A.load()
    t0 = time.time()
    truth_lines = [l for l in doc['text'][doc['answer_start']:].split('\n') if l.strip()]
    if os.environ.get('T2S_FORCED'):
        vr = voice_ranges_from_header(header) if os.environ.get('T2S_RANGES') else None
        print('voice ranges (written pitch):', vr, flush=True)
        N = int(os.environ.get('T2S_N', 1))
        import statistics
        def mids(seg):
            return [{'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[m.group(1).upper()] + (60 if m.group(1).isupper() else 72)
                    + 12 * (m.group(2).count("'") - m.group(2).count(',')) for m in re.finditer(r"(?:__|_|\^\^|\^|=)?([A-Ga-g])([,']*)", re.sub(r'![^!]*!|"[^"]*"|\[[A-Zr]:[^\]]*\]', '', seg))]
        def per_voice_median(lines):
            acc = {}
            for l in lines:
                for sg in re.split(r'(?=\[V:)', l):
                    mv = re.match(r'\[V:(\d+)\]', sg)
                    if mv: acc.setdefault(int(mv.group(1)), []).extend(mids(sg))
            return {v: statistics.median(x) for v, x in acc.items() if x}
        ref = per_voice_median(body[max(0, i0 - 8):i0] if kind != 'continue' else body[-8:])
        cands = []
        for k in range(N):
            tags = [next_stream_tag(raw_prefix, n_lines, k) for k in range(n_lines)] if STREAM else None
            g = write_forced(model, pat, pat.encode_plan(instr).to(DEV), prefix, template_from_truth(truth_lines), temperature=float(os.environ.get('T2S_TEMP', 0.7)), max_secs=900, voice_ranges=vr, line_tags=tags, voice_first=STREAM)
            med = per_voice_median([l for l in g.split('\n') if l.strip()])
            drift = sum(abs(med[v] - ref[v]) for v in med if v in ref) / max(1, len([v for v in med if v in ref]))
            cands.append((drift, k, g))
            print(f'  candidate {k}: register drift {drift:.1f} semitones from the preceding 8 bars', flush=True)
        cands.sort()
        gen = cands[0][2]
        print(f'  picked candidate {cands[0][1]} (least register drift)', flush=True)
    else:
        gen = write_answer(model, pat, instr, prefix, n_lines, temperature=float(os.environ.get('T2S_TEMP', 0.7)), max_secs=900)
    lines = [l for l in gen.split('\n') if l.strip()][:n_lines]
    lines = [re.sub(r'(?<![A-Za-z!"])x(?=\d|\s|\||/|$)', 'z', l) for l in lines]   # invisible rests shown as rests
    print(f'model wrote {len(lines)} answer lines in {time.time()-t0:.0f}s', flush=True)
    for l in lines: print('  ', l[:200])
    new_abc = splice_answer(abc, lines, kind)
    x, rc = post.to_xml(re.sub(r'%\d+', '', new_abc), f'apply_{tag}')
    out = f'{HERE}/apply_{tag}_final.xml'
    try:
        splice.splice(xml_path, x, f'{HERE}/apply_{tag}_spliced.xml', keep_through=lo - 1)
        raw = open(f'{HERE}/apply_{tag}_spliced.xml').read()
        raw = re.sub(r'<print\b[^>]*/>', '', raw); raw = re.sub(r'<print\b[^>]*>.*?</print>', '', raw, flags=re.S)
        open(out, 'w').write(raw)
    except Exception as e:
        print('splice into original failed, using the converted XML:', type(e).__name__, flush=True)
        open(out, 'w').write(open(x).read())
    json.dump(dict(kind=kind, bars=[lo, hi], voices=voices, instr=instr, lines=lines), open(f'{HERE}/apply_{tag}.json', 'w'), indent=1)
    print('APPLY_DONE', out, flush=True)
