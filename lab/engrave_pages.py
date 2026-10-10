"""Engrave a score to page images with MuseScore, for reading it the way a musician does: the first
step of every continue, revision or rejection (COMPOSING.md section 1). Read every page with the
Read tool before writing a note.

MuseScore 4 often exits with 134 after it has written the pages, so the exit code is ignored and
the pages are what count.
usage (whisperer env): python engrave_pages.py <score.musicxml> [out_dir]"""
import glob, os, subprocess, sys

MSCORE = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'

score = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.environ.get('TMPDIR', '/tmp'), 'sw_pages')
os.makedirs(out, exist_ok=True)
stem = os.path.splitext(os.path.basename(score))[0]
for old in glob.glob(f'{out}/{stem}-*.png'):
    os.remove(old)
subprocess.run([MSCORE, '-o', f'{out}/{stem}.png', score], capture_output=True, timeout=240)
pages = sorted(glob.glob(f'{out}/{stem}-*.png'), key=lambda p: int(p.rsplit('-', 1)[1][:-4]))
if not pages:
    sys.exit('MuseScore wrote no pages for ' + score)
print('\n'.join(pages))
