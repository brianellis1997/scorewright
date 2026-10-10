"""One take from the piano: speech -> words (whisper), notes -> quantized ABC (MIDI if captured, else
ByteDance piano transcription on the audio), plus a rendered SVG of what was heard.
usage: python listen.py <take.wav> <bpm> [midi_notes.json] [out_stem]   prints one JSON line"""
import sys, os, json, re, subprocess, warnings
warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
sys.path.insert(0, LAB); sys.path.insert(0, os.path.dirname(LAB))

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
ABC = ['C', '^C', 'D', '^D', 'E', 'F', '^F', 'G', '^G', 'A', '^A', 'B']

def name(m): return f'{NAMES[m % 12]}{m // 12 - 1}'
def abc_pitch(m):
    o = m // 12 - 1; s = ABC[m % 12]
    return (s.lower() + "'" * (o - 5)) if o >= 5 else (s + ',' * (4 - o))
def dur_s(d): return '' if d == 1 else str(d)

def words_from(wav, strict=False):
    """-> (text, [(start, end)] speech spans) so notes the piano model hears inside speech can be dropped.
    strict (long uploads, mostly music): only confident speech counts, since whisper invents words over music"""
    try:
        import whisper
        import librosa, numpy as np
        y, _ = librosa.load(wav, sr=16000, mono=True)          # whisper's own loader needs ffmpeg; this does not
        if len(y) < 1600: return '', []
        m = whisper.load_model('base')
        r = m.transcribe(y.astype(np.float32), fp16=False, language='en', word_timestamps=True, condition_on_previous_text=not strict)
        ok = (lambda sg: sg.get('no_speech_prob', 1) < 0.4 and sg.get('avg_logprob', -9) > -0.8 and sg.get('compression_ratio', 9) < 2.2) if strict \
             else (lambda sg: sg.get('no_speech_prob', 1) < 0.6)
        segs = [sg for sg in r.get('segments', []) if ok(sg)]
        words = [w for sg in segs for w in sg.get('words', [])]
        spans = []                                              # word spans merged across gaps under half a second
        for w in words:
            a, b = float(w['start']), float(w['end'])
            if spans and a - spans[-1][1] < 0.5: spans[-1] = (spans[-1][0], b)
            else: spans.append((a, b))
        return (' '.join(sg.get('text', '').strip() for sg in segs) if strict else r.get('text', '').strip()), spans
    except Exception as e:
        sys.stderr.write(f'whisper: {e}\n'); return '', []

def clean(notes, spans, min_len=0.12, min_vel=30):
    """drop what the piano model hears inside speech, plus ghosts (very short or very quiet)"""
    def in_speech(t): return any(a - 0.15 <= t <= b + 0.15 for a, b in spans)
    return [n for n in notes if n['end'] - n['start'] >= min_len and n['vel'] >= min_vel and not in_speech(n['start'])]

def notes_from_audio(wav):
    from piano_transcription_inference import PianoTranscription, sample_rate
    import librosa
    audio, _ = librosa.load(wav, sr=sample_rate, mono=True)      # the package's own loader needs ffmpeg
    tr = PianoTranscription(device='cpu', checkpoint_path=None)
    d = tr.transcribe(audio, None)
    return [dict(midi=int(e['midi_note']), start=float(e['onset_time']), end=float(e['offset_time']), vel=int(e['velocity']))
            for e in d['est_note_events']]

def quantize(notes, bpm):
    """notes -> per-bar ABC lines, melody (top note of each onset) in V:1, the rest as chords in V:2"""
    if not notes: return [], ''
    e = 30.0 / bpm; t0 = min(n['start'] for n in notes)
    groups = []                                              # onsets within 100 ms are one chord (model jitter, human hands)
    for n in sorted(notes, key=lambda x: x['start']):
        if groups and n['start'] - groups[-1][0] < 0.1: groups[-1][1].append(n)
        else: groups.append([n['start'], [n]])
    ons = {}
    for t, ns in groups:
        q = int(round((t - t0) / e))
        for n in ns:
            d = max(1, int(round((n['end'] - t) / e)))
            if n['midi'] not in [m for m, _ in ons.get(q, [])]: ons.setdefault(q, []).append((n['midi'], d))
    qs = sorted(ons); total = max(q + max(d for _, d in ons[q]) for q in qs); nbars = (total + 7) // 8
    def line(events):     # events: list of (q, dur, [midis]) sorted; returns per-bar strings
        bars = [''] * nbars; pos = 0
        for i, (q, d, ms) in enumerate(events):
            nxt = events[i + 1][0] if i + 1 < len(events) else total
            while pos < q:                                   # rest up to the onset
                b, off = divmod(pos, 8); step = min(q - pos, 8 - off); bars[b] += f'z{dur_s(step)} '; pos += step
            d = max(1, min(d, nxt - q)); pos = q
            tok = abc_pitch(ms[0]) if len(ms) == 1 else '[' + ''.join(abc_pitch(m) for m in sorted(ms)) + ']'
            if not tok: continue
            while d > 0:                                     # a note that crosses the barline is split and tied
                b, off = divmod(pos, 8); step = min(d, 8 - off)
                bars[b] += f'{tok}{dur_s(step)}{"-" if d > step else ""} '; pos += step; d -= step
        while pos < nbars * 8:
            b, off = divmod(pos, 8); step = 8 - off; bars[b] += f'z{dur_s(step)} '; pos += step
        return [x.strip() for x in bars]
    pitches = [m for q in qs for m, _ in ons[q]]             # hand split: the emptiest pitch in the middle register
    SPLIT = min(range(56, 69), key=lambda c: (sum(1 for m in pitches if abs(m - c) <= 1), abs(c - 62)))
    mel, acc = [], []
    for q in qs:
        rh = sorted({m for m, _ in ons[q] if m >= SPLIT}); lh = sorted({m for m, _ in ons[q] if m < SPLIT})
        if rh: mel.append((q, max(d for m, d in ons[q] if m == rh[-1]), rh))
        if lh: acc.append((q, max(d for m, d in ons[q] if m in lh), lh))
    v1, v2 = line(mel), (line(acc) if acc else ['z8'] * nbars)
    lines = [f'[b:{i}][V:1]{v1[i]}|[V:2]{v2[i]}|' for i in range(nbars)]
    heard = 'melody ' + ' '.join(name(m[-1]) for _, _, m in mel[:24]) + (' …' if len(mel) > 24 else '')
    if acc: heard += ' | chords ' + ' '.join('[' + ' '.join(name(m) for m in ms) + ']' for _, _, ms in acc[:8]) + (' …' if len(acc) > 8 else '')
    return lines, heard

def render(lines, stem):
    import verovio
    v1 = ' '.join(re.search(r'\[V:1\](.*?)\|', l).group(1) + '|' for l in lines)
    v2 = ' '.join(re.search(r'\[V:2\](.*?)\|', l).group(1) + '|' for l in lines)
    abc = f'X:1\nT:\nL:1/8\nM:4/4\nK:C\nV:1 clef=treble\nV:2 clef=bass\n[V:1] {v1}\n[V:2] {v2}\n'
    p = f'{HERE}/{stem}.abc'; open(p, 'w').write(abc)
    r = subprocess.run([sys.executable, '-W', 'ignore', f'{LAB}/NotaGen/data/abc2xml.py', '-o', HERE, p], capture_output=True, text=True)
    x = f'{HERE}/{stem}.xml'
    if not os.path.exists(x): raise RuntimeError('abc2xml: ' + r.stderr[-300:])
    tk = verovio.toolkit(); tk.setOptions({'scale': 35, 'adjustPageHeight': True, 'pageWidth': 2400, 'footer': 'none', 'header': 'none', 'breaks': 'none'})
    tk.loadData(open(x, encoding='utf-8').read()); return tk.renderToSVG(1)

def auto_tempo(wav):
    """beat tracking on the audio, folded into 60-160 so a half- or double-time estimate still gives a usable grid"""
    import librosa, numpy as np
    y, sr = librosa.load(wav, sr=22050, mono=True)
    t, _ = librosa.beat.beat_track(y=y, sr=sr)
    t = float(np.atleast_1d(t)[0]) or 100.0
    while t < 60: t *= 2
    while t > 160: t /= 2
    return round(t, 1)

def write_midi(notes, path, bpm):
    import mido
    mf = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); mf.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    tick = lambda sec: int(round(sec * bpm / 60 * 480))
    ev = sorted([(tick(n['start']), 1, n['midi'], n.get('vel', 64)) for n in notes] + [(tick(n['end']), 0, n['midi'], 0) for n in notes])
    last = 0
    for t, on, m, v in ev:
        tr.append(mido.Message('note_on' if on else 'note_off', note=m, velocity=v if on else 0, time=t - last)); last = t
    mf.save(path)

if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    upload = '--upload' in sys.argv
    outdir = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--out=')), None)
    wav = args[0]
    bpm = auto_tempo(wav) if args[1] == 'auto' else float(args[1])
    midi_json = args[2] if len(args) > 2 and args[2] != '-' else None
    stem = args[3] if len(args) > 3 else 'take'
    out = dict(words='', notes=[], abc='', heard='', svg='', source='none', tempo=bpm)
    spans = []
    if wav != '-' and os.path.exists(wav): out['words'], spans = words_from(wav, strict=upload)
    notes = json.load(open(midi_json)) if midi_json and os.path.exists(midi_json) else []
    if notes: out['source'] = 'midi'
    elif wav != '-' and os.path.exists(wav):
        try: notes = clean(notes_from_audio(wav), spans); out['source'] = 'piano model' if notes else 'none'
        except Exception as e: out['error'] = f'piano model: {e}'
    out['notes'] = notes
    if notes:
        lines, heard = quantize(notes, bpm); out['abc'] = '\n'.join(lines); out['heard'] = heard
        out['bars'] = len(lines); out['seconds'] = round(max(n['end'] for n in notes), 1)
        try: out['svg'] = render(lines[:16] if upload else lines, stem)
        except Exception as e: out['error'] = f'render: {e}'
        if outdir:
            try: write_midi(notes, f'{outdir}/{stem}.mid', bpm)
            except Exception as e: out['error'] = f'midi: {e}'
    print(json.dumps(out))
