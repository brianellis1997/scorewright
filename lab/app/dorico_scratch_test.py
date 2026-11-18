"""Try Dorico commands in a scratch project, never in Brian's. A small MusicXML opens as a new project
next to his; it is saved once, so its notes have IDs in the file (lab/dorico_file.py); each test
selects notes by ID and sends commands; the project is saved again and the result is read back from the
file. Then the scratch project closes and its files go to the Trash. Before every command the front
window must be the scratch project, or the test stops.

Tests (Nov 16 2026, for S23 and S24 of 111326):
  shorten   EventEdit.DurationShortenByGrid on a note tied over the bar line, on one note of a chord,
            and three times on a half note
  tuplets   in note input: a quarter tied into a 6:4 run (NoteInput.StartTupletRun?Definition=6:4&Set=true),
            twelve sixteenths, Set=false, a quarter, an eighth, then a 3:2 run of three sixteenths
usage (whisperer env): python app/dorico_scratch_test.py   (Brian's OK first: it opens a window in his Dorico)"""
import glob, os, re, shutil, subprocess, sys, time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import dorico_file  # noqa: E402
from dorico_rc import Dorico  # noqa: E402
from dorico_render import dialogs, keys, menu, osa, projects, wait  # noqa: E402

LOG = os.path.expanduser('~/Library/Application Support/Steinberg/Dorico 4/application.log')
TRASH = os.path.expanduser('~/.Trash')


def note(step, octave, dur, typ, extra='', alter=0, chord=False):
    return (f'<note>{"<chord/>" if chord else ""}<pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter else '') +
            f'<octave>{octave}</octave></pitch><duration>{dur}</duration>{extra}<voice>1</voice><type>{typ}</type></note>')


def rest(dur=8, typ='whole'):
    return f'<note><rest/><duration>{dur}</duration><voice>1</voice><type>{typ}</type></note>'


def scratch_xml():
    head = ('<attributes><divisions>4</divisions><key><fifths>0</fifths></key><time><beats>2</beats><beat-type>4</beat-type></time>'
            '<clef><sign>{}</sign><line>{}</line></clef></attributes>')
    fl = {1: note('C', 5, 4, 'quarter') + note('D', 5, 4, 'quarter'),
          2: note('E', 5, 8, 'half', '<tie type="start"/>'), 3: note('E', 5, 8, 'half', '<tie type="stop"/>'),
          4: note('G', 4, 4, 'quarter') + note('A', 4, 4, 'quarter'), 5: note('F', 5, 8, 'half')}
    va = {1: note('C', 4, 8, 'half') + note('E', 4, 8, 'half', chord=True) + note('G', 4, 8, 'half', chord=True)}
    parts = ''
    for pid, bars, clef in (('P1', fl, ('G', 2)), ('P2', va, ('C', 3))):
        parts += f'<part id="{pid}">' + ''.join(f'<measure number="{b}">' + (head.format(*clef) if b == 1 else '') + bars.get(b, rest()) + '</measure>'
                                                for b in range(1, 9)) + '</part>'
    return ('<?xml version="1.0" encoding="UTF-8"?><score-partwise version="3.1"><part-list>'
            '<score-part id="P1"><part-name>Flute</part-name></score-part><score-part id="P2"><part-name>Viola</part-name></score-part>'
            f'</part-list>{parts}</score-partwise>')


def front():
    return osa('tell application "System Events" to tell process "Dorico" to get name of front window')


def saved_to(stem, since):
    for line in reversed(open(LOG, errors='replace').read().splitlines()):
        m = re.search(r'^(\S+ \S+) .*Saving document: \d+ to (.+\.dorico)\s*$', line)
        if m and stem in os.path.basename(m.group(2)) and os.path.exists(m.group(2)) and os.path.getmtime(m.group(2)) >= since:
            return m.group(2)
    return None


def notes_of(path):
    out = {}
    for f in dorico_file.read(path).flows:
        for n in f.notes:
            out.setdefault(n.instrument, []).append(n)
    return {k: sorted(v, key=lambda n: (n.position, -(n.pitch or 0))) for k, v in out.items()}


def show(ns):
    return ' '.join(f'{n.bar}@{n.onset}:{n.pitch_name}/{n.duration}' for n in ns)


def main():
    if len(projects()) != 1 or dialogs(exclude=()):
        print('busy: need his one project window and no dialog:', projects(), dialogs(exclude=()))
        return 2
    his = projects()[0][0]
    stem = f'sw_test_{int(time.time())}'
    tmp = os.path.join(os.path.dirname(LOG), 'sw_scratch')
    os.makedirs(tmp, exist_ok=True)
    src = f'{tmp}/{stem}.musicxml'
    open(src, 'w').write(scratch_xml())
    start = time.time()
    subprocess.run(['open', '-a', 'Dorico 4', src])
    mine = wait(lambda: next((w[0] for w in projects() if stem in w[0]), None), 120, 2)
    if not mine:
        print('failed: the scratch project did not open', projects())
        return 1
    time.sleep(2)
    path = None
    try:
        keys('keystroke "s" using command down', raise_window=mine)
        time.sleep(2.5)
        keys('key code 36')
        path = wait(lambda: saved_to(stem, start), 30, 1)
        if not path:
            print('failed: no save of the scratch project in the log', dialogs(exclude=()))
            return 1
        ns = notes_of(path)
        fl, va = ns['Flute'], ns['Viola']
        print('before:', show(fl), '|', show(va))
        d = Dorico()

        def run(cmds):
            if stem not in front():
                raise RuntimeError(f'the front window is {front()!r}, not the scratch project')
            for c in cmds:
                err = d.cmd(c, wait=0.12)
                if err:
                    print('  refused:', c, err)

        pick = lambda ns, bar, name: next(n for n in ns if n.bar == bar and n.pitch_name == name)
        run([pick(fl, 2, 'E5').select_command] + ['EventEdit.DurationShortenByGrid'] * 2)
        run([pick(va, 1, 'E4').select_command] + ['EventEdit.DurationShortenByGrid'] * 2)
        run([pick(fl, 5, 'F5').select_command] + ['EventEdit.DurationShortenByGrid'] * 3)
        six = [81, 84, 86, 88, 89, 91, 93, 91, 90, 88, 86, 84]
        cmds = [pick(fl, 4, 'G4').select_command, 'NoteInput.Enter?Set=true']
        run(cmds)
        time.sleep(0.6)
        cmds = ['NoteInput.MoveRightBar', 'NoteInput.MoveRightBar',
                'NoteInput.NoteValue?LogDuration=kCrotchet&Set=true', 'NoteInput.MIDINoteInput?MIDIPitches=81', 'NoteInput.Tie',
                'NoteInput.NoteValue?LogDuration=kSemiQuaver&Set=true', 'NoteInput.StartTupletRun?Definition=6:4&Set=true']
        cmds += [c for p in six for c in ('NoteInput.NoteValue?LogDuration=kSemiQuaver&Set=true', f'NoteInput.MIDINoteInput?MIDIPitches={p}')]
        cmds += ['NoteInput.StartTupletRun?Definition=6:4&Set=false',
                 'NoteInput.NoteValue?LogDuration=kCrotchet&Set=true', 'NoteInput.MIDINoteInput?MIDIPitches=83',
                 'NoteInput.NoteValue?LogDuration=kQuaver&Set=true', 'NoteInput.MIDINoteInput?MIDIPitches=81',
                 'NoteInput.NoteValue?LogDuration=kSemiQuaver&Set=true', 'NoteInput.StartTupletRun?Definition=3:2&Set=true']
        cmds += [c for p in (79, 77, 76) for c in ('NoteInput.NoteValue?LogDuration=kSemiQuaver&Set=true', f'NoteInput.MIDINoteInput?MIDIPitches={p}')]
        cmds += ['NoteInput.StartTupletRun?Definition=3:2&Set=false', 'NoteInput.Exit']
        run(cmds)
        time.sleep(1)
        before = os.path.getmtime(path)
        keys('keystroke "s" using command down', raise_window=mine)
        wait(lambda: os.path.getmtime(path) > before, 20, 1)
        ns = notes_of(path)
        print('after: ', show(ns['Flute']), '|', show(ns['Viola']))
        return 0
    finally:
        if stem in front():
            keys('key code 53')
        for _ in range(3):
            w = next((w[0] for w in projects() if stem in w[0]), None)
            if not w:
                break
            keys('', raise_window=w)
            menu('File', 'Close Project')
            if wait(lambda: dialogs(), 6):
                keys('keystroke "d" using command down')
            wait(lambda: not any(stem in w[0] for w in projects()), 10)
        print('left open:', [w[0] for w in projects()], '(his:', his + ')')
        for f in glob.glob(f'{tmp}/{stem}*') + ([path] if path else []):
            if f and os.path.exists(f):
                shutil.move(f, os.path.join(TRASH, os.path.basename(f)))


if __name__ == '__main__':
    sys.exit(main())
