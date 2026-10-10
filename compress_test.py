"""Measure REAL compression: MusicXML -> compact encodings. No API calls, no cost."""
import sys, os, io, time, tiktoken
from music21 import converter, note, chord

enc = tiktoken.get_encoding('cl100k_base')
D = '/Users/bdogellis/Documents/Score Exports/MusicXML'

def toks(s): return len(enc.encode(s))

def to_compact(score):
    """Minimal custom encoding: one line per part, bar-delimited, pitch+duration only.
    Deliberately lossy on layout, keeps pitch/rhythm/dynamics/articulations."""
    out = []
    for p in score.parts:
        name = (p.partName or 'part')[:18]
        toks_ = []
        for m in p.getElementsByClass('Measure'):
            cell = []
            for el in m.notesAndRests:
                d = el.duration.quarterLength
                if isinstance(el, chord.Chord):
                    cell.append('[' + ' '.join(n.nameWithOctave for n in el.notes) + f']{d}')
                elif isinstance(el, note.Note):
                    cell.append(f'{el.nameWithOctave}{d}')
                else:
                    cell.append(f'r{d}')
            toks_.append(' '.join(cell))
        out.append(f'{name}: ' + ' | '.join(toks_))
    return '\n'.join(out)

for fn in sys.argv[1:]:
    p = os.path.join(D, fn)
    raw = open(p, encoding='utf-8', errors='replace').read()
    t0 = time.time()
    try:
        s = converter.parse(p)
    except Exception as e:
        print(f"{fn[:40]:42s} PARSE FAILED: {str(e)[:50]}"); continue
    parse_s = time.time() - t0
    compact = to_compact(s)
    rt, ct = toks(raw), toks(compact)
    print(f"{fn[:40]:42s} parts={len(s.parts):3d} xml={rt:>10,d} compact={ct:>9,d} "
          f"ratio={ct/rt*100:5.1f}%  parse={parse_s:5.1f}s")
