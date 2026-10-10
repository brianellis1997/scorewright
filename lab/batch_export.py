"""All 1,607 MusicXML -> PDF + MIDI via MuseScore CLI, Sibelius-free.

Uses -j job-file mode: one MuseScore process per chunk of 50 scores (per-file spawning would boot
the app 3,214 times). Chunks are resumable - files with both outputs already present are skipped -
and a chunk that hangs (one pathological score) is killed after 10 min and its files retried
individually, so one bad score cannot sink the batch. This export is the precondition on the
calendar reminder for cancelling the Sibelius subscription (Sept 24).
"""
import json, os, subprocess, sys, time
M = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'
SRC = '/Users/bdogellis/Documents/Score Exports/MusicXML'
PDF = '/Users/bdogellis/Documents/Score Exports/PDF'
MID = '/Users/bdogellis/Documents/Score Exports/MIDI'
os.makedirs(PDF, exist_ok=True); os.makedirs(MID, exist_ok=True)

def todo():
    out = []
    for f in sorted(os.listdir(SRC)):
        if not f.endswith('.musicxml'):
            continue
        # f[:-9] strips '.musicxml' INCLUDING the dot, so '{stem}pdf' produced extensionless
        # names like 'Xpdf' and MuseScore silently skipped all 1,607 files. The dot matters.
        stem = f[:-9]
        p, m = f'{PDF}/{stem}.pdf', f'{MID}/{stem}.mid'
        if not (os.path.exists(p) and os.path.getsize(p) > 1000
                and os.path.exists(m) and os.path.getsize(m) > 100):
            out.append((f'{SRC}/{f}', p, m))
    return out

def run_chunk(chunk, timeout):
    job = [{'in': i, 'out': [p, m]} for i, p, m in chunk]
    jp = '/tmp/ms_job.json'
    json.dump(job, open(jp, 'w'))
    try:
        subprocess.run([M, '-j', jp], capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False
    return True

t0 = time.time()
items = todo()
print(f'{len(items)} scores need exporting', flush=True)
i = 0
while i < len(items):
    chunk = items[i:i+50]
    ok = run_chunk(chunk, 600)
    if not ok:
        print(f'chunk at {i} timed out - retrying files singly', flush=True)
        for it in chunk:
            run_chunk([it], 90)
    i += 50
    done = 1607 - len(todo())
    print(f'progress: {done}/1607 complete  ({(time.time()-t0)/60:.0f} min)', flush=True)
left = todo()
print(f'BATCH DONE: {1607-len(left)}/1607 exported, {len(left)} failed', flush=True)
for it in left[:10]:
    print('  failed:', os.path.basename(it[0]), flush=True)
