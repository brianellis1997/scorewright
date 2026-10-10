"""Render a MusicXML file to audio through Dorico 4 + NotePerformer, unattended.

Sequence (each step verified by listing windows, including UNTITLED dialogs):
  1. refuse if any Dorico project or dialog is already open (never touch Brian's own work)
  2. copy the MusicXML to a unique name, so the exported WAV name is new and Dorico never asks
     "Do you want to overwrite the file ...?"
  3. open it, File > Export > Audio... (menu bar items ARE clickable), then activate + AXRaise +
     Return in ONE AppleScript (Dorico's own dialog buttons are NOT clickable through accessibility)
  4. wait for the audio file to appear and stop growing
  5. File > Close Project, then Cmd+D answers "Save changes ... before closing?" with Don't Save
  6. normalise, AAC-encode with afconvert, write <out_stem>.np.m4a and the page's <out_stem>.audio.txt
Any unexpected dialog: screenshot it to _bridge/dorico_debug_*.png, press Escape, clean up, fail.
usage: python dorico_render.py <score.musicxml> <out_stem>      exit 0 ok, 1 failed, 2 busy, 3 no permission"""
import sys, os, time, subprocess, base64, tempfile, glob, shutil

DP = os.path.expanduser('~/Documents/Dorico Projects')
BRIDGE = '/Users/bdogellis/Documents/Score Exports/_bridge'
HUB = 'Steinberg Hub'


def osa(script, timeout=30):
    r = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=timeout)
    return r.stdout.rstrip('\n')          # never strip() here: an untitled dialog's row starts with a tab


def wins():
    """[(name, subrole, x, y, w, h)] for every Dorico window, untitled dialogs included."""
    out = osa('''tell application "System Events"
if not (exists process "Dorico") then return ""
set s to ""
tell process "Dorico"
repeat with w in windows
set {x, y} to position of w
set {ww, hh} to size of w
set s to s & (name of w as text) & tab & (subrole of w as text) & tab & x & tab & y & tab & ww & tab & hh & linefeed
end repeat
end tell
return s
end tell''')
    rows = []
    for line in out.splitlines():
        p = line.split('\t')
        if len(p) == 6:
            rows.append((p[0], p[1], *[int(float(v)) for v in p[2:]]))
    return rows


def projects():
    return [w for w in wins() if w[1] == 'AXStandardWindow' and w[0] != HUB]


def dialogs(exclude=('Export Audio',)):
    return [w for w in wins() if w[1] in ('AXDialog', 'AXSystemDialog') and w[0] not in exclude]


def snap(tag):
    """screenshot every dialog window (never the whole screen) for diagnosis"""
    paths = []
    for i, w in enumerate(dialogs(exclude=())):
        p = f'{BRIDGE}/dorico_debug_{tag}_{i}.png'
        subprocess.run(['screencapture', '-x', f'-R{w[2]},{w[3]},{w[4]},{w[5]}', p])
        paths.append(p)
    return paths


def menu(*path):
    items = ' of '.join(f'menu 1 of menu item "{p}"' for p in reversed(path[1:-1]))
    target = f'menu item "{path[-1]}" of ' + (items + ' of ' if items else '') + f'menu 1 of menu bar item "{path[0]}" of menu bar 1'
    osa(f'tell application "Dorico 4" to activate\ndelay 0.5\ntell application "System Events" to tell process "Dorico" to click {target}')


def keys(body, raise_window=None):
    r = f'perform action "AXRaise" of window "{raise_window}"\ndelay 0.4\n' if raise_window else ''
    osa(f'tell application "Dorico 4" to activate\ndelay 0.8\ntell application "System Events" to tell process "Dorico"\n{r}{body}\nend tell')


def wait(cond, timeout, step=1.0):
    t = time.time()
    while time.time() - t < timeout:
        v = cond()
        if v:
            return v
        time.sleep(step)
    return None


def close_project():
    if dialogs():
        snap('beforeclose'); keys('key code 53'); time.sleep(1.5)
    for _ in range(3):                      # Dorico reports Close Project as disabled yet obeys a retry
        if not projects():
            break
        menu('File', 'Close Project')
        if wait(lambda: dialogs(), 8):
            keys('keystroke "d" using command down')
        wait(lambda: not projects() and not dialogs(), 10)
    left = projects() or dialogs()
    if left:
        snap('stuck')
    return not left


def allowed():
    r = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of first process'], capture_output=True, text=True, timeout=30)
    return 'not allowed assistive access' not in r.stderr


def main(xml, stem):
    if not allowed():
        print('no permission: this process may not control other apps (System Settings > Privacy & Security > Accessibility)'); return 3
    if projects() or dialogs(exclude=()):
        print('busy: a Dorico project or dialog is already open'); return 2
    marker = time.time()
    tmpdir = tempfile.mkdtemp(prefix='sw_np_')
    src = f'{tmpdir}/sw_{os.path.basename(stem)}_{int(marker)}.musicxml'
    shutil.copy(xml, src)
    audio = None
    try:
        subprocess.run(['open', '-a', 'Dorico 4', src])
        if not wait(lambda: projects(), 300, 2):
            late = wait(lambda: projects(), 120, 3)       # it may still arrive; nothing else was open, so it is ours to close
            print('failed: Dorico did not open the file in time' + (' (arrived late, closed)' if late else ''), snap('open')); return 1
        time.sleep(2)
        if dialogs():
            print('failed: unexpected dialog after open', snap('afteropen')); return 1
        opened = None
        for _ in range(3):
            menu('File', 'Export', 'Audio...')
            opened = wait(lambda: any(w[0] == 'Export Audio' for w in wins()), 12)
            if opened:
                break
        if not opened:
            print('failed: no Export Audio dialog', snap('noexport')); return 1
        keys('key code 36', raise_window='Export Audio')
        if not wait(lambda: not any(w[0] == 'Export Audio' for w in wins()), 8):
            keys('key code 36', raise_window='Export Audio')

        def rendered():
            new = [f for f in glob.glob(f'{DP}/**/sw_*', recursive=True)
                   if f.lower().endswith(('.wav', '.flac', '.mp3')) and os.path.getmtime(f) >= marker]
            if not new:
                return None
            f = max(new, key=os.path.getmtime)
            s1 = os.path.getsize(f); time.sleep(3)
            return f if s1 > 1000 and os.path.getsize(f) == s1 and not any(w[0] == 'Export Audio' for w in wins()) else None
        audio = wait(rendered, 300, 2)
        if not audio:
            print('failed: no audio file appeared', snap('noaudio')); return 1
    finally:
        closed = close_project()
        shutil.rmtree(tmpdir, ignore_errors=True)
        if not closed:
            print('warning: Dorico project or dialog still open')
    return finish(audio, stem, marker)


def finish(audio, stem, marker):
    import numpy as np, soundfile as sf
    out = stem + '.np.m4a'
    if audio.lower().endswith('.mp3'):
        data, mime = open(audio, 'rb').read(), 'audio/mpeg'
    else:
        y, sr = sf.read(audio)
        peak = float(np.max(np.abs(y))) or 1.0
        y = y * (0.89 / peak)
        with tempfile.TemporaryDirectory() as d:
            tmp = f'{d}/n.wav'
            sf.write(tmp, y, sr, subtype='PCM_16')
            subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '160000', tmp, out], check=True)
        data, mime = open(out, 'rb').read(), 'audio/mp4'
    open(stem + '.audio.txt', 'w').write(f'data:{mime};base64,' + base64.b64encode(data).decode())
    os.remove(audio)
    d = os.path.dirname(audio)
    while d.startswith(DP + '/') and os.path.isdir(d) and not os.listdir(d) and os.path.getmtime(d) >= marker - 5:
        os.rmdir(d); d = os.path.dirname(d)
    print('np ok', os.path.basename(out), len(data)); return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
