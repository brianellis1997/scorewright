"""Hum/sing -> notes.  usage: python hum.py <audio file> [bpm]   prints JSON {heard, abc, notes}"""
import sys, json, subprocess, tempfile, os
import numpy as np, librosa

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
ABC = ['C', '^C', 'D', '^D', 'E', 'F', '^F', 'G', '^G', 'A', '^A', 'B']

def to_wav(src):
    out = tempfile.mktemp(suffix='.wav')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', src, '-ac', '1', '-ar', '22050', out], check=True)
    return out

def name(m):
    return f'{NAMES[m % 12]}{m // 12 - 1}'

def abc_note(m, eighths):
    o = m // 12 - 1; s = ABC[m % 12]
    if o >= 5: s = s.lower() + "'" * (o - 5)
    else: s = s + ',' * (4 - o)
    return s + ('' if eighths == 1 else str(eighths))

def segments(f0, voiced, hop_s, onsets=(), min_len=0.08, split_cents=60):
    segs = []; cur = []; onsets = set(onsets)
    for i, (f, v) in enumerate(zip(f0, voiced)):
        if v and f and not np.isnan(f):
            m = librosa.hz_to_midi(f)
            if cur and (abs(m - np.median(cur)) * 100 > split_cents or (i in onsets and len(cur) * hop_s >= min_len)):
                segs.append((cur, i)); cur = []
            cur.append(m)
        elif cur:
            segs.append((cur, i)); cur = []
    if cur: segs.append((cur, len(f0)))
    out = []
    for ms, end in segs:
        dur = len(ms) * hop_s
        if dur < min_len: continue
        out.append(dict(midi=int(round(float(np.median(ms)))), sec=round(dur, 3), start=round((end - len(ms)) * hop_s, 3)))
    merged = []
    for n in out:                       # glue re-attacks of the same pitch across tiny gaps
        if merged and merged[-1]['midi'] == n['midi'] and n['start'] - (merged[-1]['start'] + merged[-1]['sec']) < 0.02:
            merged[-1]['sec'] = round(n['start'] + n['sec'] - merged[-1]['start'], 3)
        else: merged.append(n)
    return merged

def main(path, bpm=120.0):
    wav = path if path.lower().endswith('.wav') else to_wav(path)
    y, sr = librosa.load(wav, sr=22050)
    if wav != path: os.unlink(wav)
    hop = 256
    f0, vflag, vprob = librosa.pyin(y, fmin=70, fmax=1100, sr=sr, frame_length=2048, hop_length=hop)
    ons = librosa.onset.onset_detect(y=y, sr=sr, hop_length=hop, backtrack=False, delta=0.15)
    notes = segments(f0, vflag, hop / sr, onsets=ons)
    eighth = 30.0 / bpm
    for n in notes:
        n['name'] = name(n['midi']); n['eighths'] = max(1, int(round(n['sec'] / eighth)))
    heard = ' '.join(f"{n['name']}({n['eighths']})" for n in notes)
    abc = ' '.join(abc_note(n['midi'], n['eighths']) for n in notes)
    return dict(heard=heard, abc=abc, notes=notes, bpm=bpm, seconds=round(len(y) / sr, 2))

if __name__ == '__main__':
    print(json.dumps(main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 120.0)))
