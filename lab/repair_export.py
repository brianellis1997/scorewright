"""The 125 scores MuseScore rejects (exit 40) all parse fine in music21, so: launder each through
a music21 re-serialisation (which normalises whatever Sibelius-export quirk trips MuseScore's
importer) and convert the laundered copy. The PDF/MIDI keeps the ORIGINAL name. Any survivor that
still fails gets its MIDI from music21 directly (at sounding pitch) and is listed for the PDF."""
import os, subprocess, sys, tempfile, time, warnings
warnings.simplefilter('ignore')
from music21 import converter
M = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'
SRC = '/Users/bdogellis/Documents/Score Exports/MusicXML'
PDF = '/Users/bdogellis/Documents/Score Exports/PDF'
MID = '/Users/bdogellis/Documents/Score Exports/MIDI'

fails = []
todo = [f for f in sorted(os.listdir(SRC)) if f.endswith('.musicxml')
        and not (os.path.exists(f'{PDF}/{f[:-9]}.pdf') and os.path.exists(f'{MID}/{f[:-9]}.mid'))]
print(f'{len(todo)} to repair', flush=True)
for n, f in enumerate(todo, 1):
    stem = f[:-9]
    try:
        s = converter.parse(f'{SRC}/{f}')
        with tempfile.TemporaryDirectory() as d:
            lx = f'{d}/laundered.musicxml'
            s.write('musicxml', fp=lx)
            r = subprocess.run([M, '-o', f'{PDF}/{stem}.pdf', lx], capture_output=True, timeout=120)
            r2 = subprocess.run([M, '-o', f'{MID}/{stem}.mid', lx], capture_output=True, timeout=120)
        if r.returncode or r2.returncode:
            raise RuntimeError(f'mscore {r.returncode}/{r2.returncode}')
    except Exception as e:
        try:
            s.toSoundingPitch().write('midi', fp=f'{MID}/{stem}.mid')
            fails.append((f, f'PDF failed ({str(e)[:40]}), MIDI via music21'))
        except Exception as e2:
            fails.append((f, f'both failed: {str(e2)[:60]}'))
    if n % 25 == 0:
        print(f'  {n}/{len(todo)}', flush=True)
print(f'REPAIR DONE: {len(todo)-len(fails)} fully fixed, {len(fails)} partial/failed', flush=True)
for f, why in fails:
    print(f'  {f}: {why}', flush=True)
