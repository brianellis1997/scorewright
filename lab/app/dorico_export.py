"""Export the Dorico project that Brian has open to MusicXML, so Scorewright can read it, without
saving, closing or changing the project. Each step is checked by listing Dorico's windows, untitled
dialogs included:
  1. refuse unless exactly one project window is open and no dialog is
  2. move earlier exports of this project in "Flows from <project>" to the Trash, so Dorico never
     asks whether to replace a file
  3. File > Export > MusicXML... (menu items are clickable), then AXRaise and Return on the
     "Export MusicXML" dialog (Dorico's own buttons are not clickable through accessibility)
  4. wait for "<project> - Full score - 01 <flow>.xml"; the part layouts Dorico writes beside it go
     to the Trash
These are the steps first done by hand for 111326 on Nov 13 2026. The dialog keeps Brian's own
settings (uncompressed .xml, every layout, a folder per project).
usage (whisperer env): python app/dorico_export.py [--dry-run] [copy_to.xml]
prints the full-score path; exit 0 ok, 1 failed, 2 busy"""
import glob, os, shutil, subprocess, sys, time

DP = os.path.expanduser('~/Documents/Dorico Projects')
PROC = 'Dorico 4'
DIALOG = 'Export MusicXML'


def osa(script, timeout=30):
    r = subprocess.run(['osascript', '-e', script], capture_output=True, text=True, timeout=timeout)
    return r.stdout.rstrip('\n')


def wins():
    out = osa(f'''tell application "System Events"
if not (exists process "{PROC}") then return ""
tell process "{PROC}"
set s to ""
repeat with w in windows
set {{x, y}} to position of w
set {{ww, hh}} to size of w
set s to s & (name of w as text) & tab & (subrole of w as text) & tab & x & tab & y & tab & ww & tab & hh & linefeed
end repeat
return s
end tell
end tell''')
    return [row.split('\t') for row in out.splitlines() if len(row.split('\t')) == 6]


def wait(cond, timeout, step=0.5):
    t = time.time()
    while time.time() - t < timeout:
        v = cond()
        if v:
            return v
        time.sleep(step)
    return None


def trash(paths):
    if paths:
        d = os.path.expanduser(f'~/.Trash/Scorewright export {time.strftime("%Y-%m-%d %H-%M-%S")}')
        os.makedirs(d, exist_ok=True)
        for p in paths:
            shutil.move(p, d)


def project_name(title):
    names = [os.path.basename(f)[:-len('.dorico')] for f in glob.glob(f'{glob.escape(DP)}/**/*.dorico', recursive=True)
             if '/Backup Projects/' not in f]
    found = sorted((n for n in names if title == n or title.endswith(' in ' + n)), key=len)
    return found[-1] if found else title.split(' in ', 1)[-1]


def main(args):
    dry = '--dry-run' in args
    args = [a for a in args if a != '--dry-run']
    ws = wins()
    projects = [w for w in ws if w[1] == 'AXStandardWindow']
    other = [w for w in ws if w[1] != 'AXStandardWindow' and not (w[1] == 'AXUnknown' and w[0] == '')]
    if len(projects) != 1 or other:
        print('busy: need exactly one Dorico project window and no dialog:', ws)
        return 2
    project = project_name(projects[0][0])
    folder = f'{DP}/Flows from {project}'
    old = glob.glob(f'{glob.escape(folder)}/{glob.escape(project)} - *.xml')
    print(f'project "{project}"; {len(old)} earlier export(s) in "{folder}" go to the Trash')
    if dry:
        return 0
    trash(old)
    marker = time.time()
    osa(f'tell application "{PROC}" to activate\ndelay 0.4\ntell application "System Events" to tell process "{PROC}" to '
        f'click menu item "MusicXML..." of menu 1 of menu item "Export" of menu 1 of menu bar item "File" of menu bar 1')
    if not wait(lambda: any(w[0] == DIALOG for w in wins()), 12):
        print('failed: no Export MusicXML dialog:', wins())
        return 1
    osa(f'tell application "{PROC}" to activate\ndelay 0.4\ntell application "System Events" to tell process "{PROC}"\n'
        f'perform action "AXRaise" of window "{DIALOG}"\ndelay 0.3\nkey code 36\nend tell')
    if not wait(lambda: not any(w[0] == DIALOG for w in wins()), 60):
        print('failed: the export dialog is still open:', wins())
        return 1

    def full():
        new = [f for f in glob.glob(f'{glob.escape(folder)}/*.xml') if os.path.getmtime(f) >= marker]
        score = [f for f in new if ' - Full score - ' in f] or new
        if not score:
            return None
        s = max(score, key=os.path.getmtime)
        size = os.path.getsize(s)
        time.sleep(1)
        return s if size > 1000 and os.path.getsize(s) == size else None
    score = wait(full, 60, 1)
    if not score:
        print('failed: no MusicXML appeared in', folder)
        return 1
    trash([f for f in glob.glob(f'{glob.escape(folder)}/*.xml') if os.path.getmtime(f) >= marker and f != score])
    if args:
        shutil.copy(score, args[0])
    print(score)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
