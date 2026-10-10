"""Convert the whole MusicXML corpus to a cached compact encoding + per-score metadata.

Compact format, one line per part:
    <part name>: <bar> | <bar> | ...
where a bar is space-separated events:  C4:1.0   [C4 E4 G4]:2.0   r:0.5   and
inline markers  <f>  <cresc>  .staccato  ~slur

Deliberately lossy on ENGRAVING (page layout, beams, stem direction, spacing) and lossless on
MUSICAL CONTENT (pitch, rhythm, dynamics, articulations, tempo, key, time signature).
Measured 2.7-4.6% of MusicXML token cost. See PROJECT.md §5.
"""
import os, sys, json, time, traceback
from music21 import converter, note, chord, dynamics, expressions, tempo, meter, key as m21key

SRC = '/Users/bdogellis/Documents/Score Exports/MusicXML'
OUT = '/Users/bdogellis/Documents/Score Exports/compact'
META = os.path.join(OUT, '_meta')
os.makedirs(OUT, exist_ok=True); os.makedirs(META, exist_ok=True)

def fmt_dur(d):
    f = float(d)
    return str(int(f)) if f == int(f) else f'{f:g}'

def encode(score):
    lines, meta = [], {}
    try:
        ks = score.analyze('key')
        meta['key_detected'] = f'{ks.tonic.name} {ks.mode}'
    except Exception:
        meta['key_detected'] = None
    tss = score.recurse().getElementsByClass(meter.TimeSignature)
    meta['time_signatures'] = sorted({t.ratioString for t in tss})[:6]
    mms = score.recurse().getElementsByClass(tempo.MetronomeMark)
    meta['tempos'] = sorted({int(t.number) for t in mms if t.number})[:6]

    # HEADER. The encoding used to emit notes only, which deleted the one field that decides the
    # key. Measured on Briello no 36: from notes alone, 5/5 models answered F# major; the true key
    # is D# minor, stated in the MusicXML as <fifths>6</fifths> + <mode>minor</mode>. Passing the
    # notated signature and mode through costs a handful of tokens. Never make a model infer what
    # the file already says.
    head = []
    kss = list(score.recurse().getElementsByClass(m21key.KeySignature))
    if kss:
        seen_ks = []
        for ks in kss:
            mn = ks.measureNumber
            ent = (mn, ks.sharps, getattr(ks, 'mode', None))
            if ent not in seen_ks:
                seen_ks.append(ent)
        head.append('KEY SIGNATURES: ' + '; '.join(
            f'm{mn or 1}: {sh:+d} ({"sharps" if sh > 0 else "flats" if sh < 0 else "none"})'
            + (f' {mo}' if mo else '') for mn, sh, mo in seen_ks[:8]))
    if meta['time_signatures']:
        head.append('TIME SIGNATURES: ' + ', '.join(meta['time_signatures']))
    if meta['tempos']:
        head.append('TEMPI: ' + ', '.join(str(t) for t in meta['tempos']))

    total_notes = 0
    for p in score.parts:
        name = (p.partName or p.id or 'part')
        cells = []
        for m in p.getElementsByClass('Measure'):
            # A Measure may hold notes DIRECTLY, or split them across Voice objects (piano
            # left/right hand, string divisi). m.notesAndRests does NOT descend into Voices, so the
            # first version of this encoder silently dropped 49% of "Briello no 36 in D# minor" and
            # lost notes in 26% of the corpus. Voices are emitted in parallel, separated by ' // '.
            vs = list(m.getElementsByClass('Voice'))
            groups = [list(v.notesAndRests) for v in vs] if vs else [list(m.notesAndRests)]
            gout = []
            for grp in groups:
                ev = []
                for el in grp:
                    d = fmt_dur(el.duration.quarterLength)
                    # '~' marks a note tied INTO the next one. Without it a note held across a
                    # barline reads as two separate attacks, which is a different rhythm.
                    tie = getattr(el, 'tie', None)
                    t = '~' if tie is not None and tie.type in ('start', 'continue') else ''
                    if isinstance(el, chord.Chord):
                        ev.append('[' + ' '.join(n.nameWithOctave for n in el.notes) + f']:{d}{t}')
                        total_notes += len(el.notes)
                    elif isinstance(el, note.Note):
                        a = ''.join('.' + x.name[:4] for x in el.articulations) if el.articulations else ''
                        ev.append(f'{el.nameWithOctave}:{d}{a}{t}')
                        total_notes += 1
                    else:
                        ev.append(f'r:{d}')
                gout.append(' '.join(ev))
            cell = ' // '.join(g for g in gout if g)
            for el in m.getElementsByClass(dynamics.Dynamic):
                cell += f' <{el.value}>'
            cells.append(cell)
        lines.append(f'{name}: ' + ' | '.join(cells))
    meta['parts'] = [(p.partName or p.id or 'part') for p in score.parts]
    meta['n_parts'] = len(score.parts)
    meta['n_measures'] = max((len(p.getElementsByClass('Measure')) for p in score.parts), default=0)
    meta['n_notes'] = total_notes
    return '\n'.join(head + [''] + lines) if head else '\n'.join(lines), meta


def main():
    files = sorted(f for f in os.listdir(SRC) if f.endswith('.musicxml'))
    only = sys.argv[1:] or None
    if only: files = [f for f in files if f in only]
    ok = fail = skip = 0
    t_start = time.time()
    for i, fn in enumerate(files, 1):
        stem = os.path.splitext(fn)[0]
        dst = os.path.join(OUT, stem + '.txt')
        if os.path.exists(dst):
            skip += 1; continue
        try:
            t0 = time.time()
            s = converter.parse(os.path.join(SRC, fn))
            body, meta = encode(s)
            meta['source'] = fn
            meta['parse_seconds'] = round(time.time() - t0, 2)
            meta['chars'] = len(body)
            open(dst, 'w').write(body)
            json.dump(meta, open(os.path.join(META, stem + '.json'), 'w'))
            ok += 1
        except Exception as e:
            fail += 1
            with open(os.path.join(OUT, '_failures.log'), 'a') as fh:
                fh.write(f'{fn}\t{type(e).__name__}: {str(e)[:160]}\n')
        if i % 50 == 0:
            el = time.time() - t_start
            print(f'  {i}/{len(files)}  ok={ok} fail={fail} skip={skip}  {el/60:.1f} min', flush=True)
    print(f'DONE ok={ok} fail={fail} skip={skip} in {(time.time()-t_start)/60:.1f} min')

if __name__ == '__main__':
    main()
