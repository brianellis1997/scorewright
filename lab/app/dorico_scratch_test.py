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
  gliss     NoteInput.CreateGlissando on a range of two notes (flute bar 1) and of three (bars 4-5):
            the lines it makes are read back from the file (GlissandoLineEventDefinition) (Nov 18, S33)
  tuplet    a bar of two eighth-note triplets: the second triplet and the next three bars deleted as one
            range (Edit.Delete), then G F as plain eighths typed where it was, then E. F | E: are the
            tuplet's records gone, and where do the new notes land? (Nov 23, S38)
usage (whisperer env): python app/dorico_scratch_test.py [gliss]   (Brian's OK first: it opens a window in his Dorico)"""
import glob, os, re, shutil, subprocess, sys, time, zipfile
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import dorico_file  # noqa: E402
from dorico_rc import Dorico  # noqa: E402
from dorico_render import dialogs, keys, menu, osa, projects, wait, wins  # noqa: E402

LOG = os.path.expanduser('~/Library/Application Support/Steinberg/Dorico 4/application.log')
XSD = '/Applications/Dorico 4.app/Contents/Resources/musicxml/musicxml.xsd'
TRASH = os.path.expanduser('~/.Trash')


def note(step, octave, dur, typ, extra='', alter=0, chord=False):
    return (f'<note>{"<chord/>" if chord else ""}<pitch><step>{step}</step>' + (f'<alter>{alter}</alter>' if alter else '') +
            f'<octave>{octave}</octave></pitch><duration>{dur}</duration>{extra}<voice>1</voice><type>{typ}</type></note>')


def rest(dur=8, typ='whole'):
    return f'<note><rest/><duration>{dur}</duration><voice>1</voice><type>{typ}</type></note>'


def plain(step, octave, dur, typ, dot=False, tm=False, tup=None):
    """a note with its elements in the order the schema wants (Nov 23: a tuplet mark before <voice> made
    Dorico stop on "MusicXML validation failed", and the test went wrong behind that warning)"""
    t = '<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes></time-modification>' if tm else ''
    n = f'<notations><tuplet type="{tup}" bracket="yes"/></notations>' if tup else ''
    return (f'<note><pitch><step>{step}</step><octave>{octave}</octave></pitch><duration>{dur}</duration><voice>1</voice>'
            f'<type>{typ}</type>{"<dot/>" if dot else ""}{t}{n}</note>')


def tuplet_xml():
    """one flute: C D E | E F G as eighth triplets, then G F (quarters) | E. F | E, at 12 divisions"""
    trip = lambda st, k: plain(st, 5, 4, 'eighth', tm=True, tup={0: 'start', 2: 'stop'}.get(k))
    bars = {1: ''.join(trip(st, k) for k, st in enumerate('CDE')) + ''.join(trip(st, k) for k, st in enumerate('EFG')),
            2: plain('G', 5, 12, 'quarter') + plain('F', 5, 12, 'quarter'),
            3: plain('E', 5, 18, 'quarter', dot=True) + plain('F', 5, 6, 'eighth'),
            4: plain('E', 5, 12, 'quarter') + rest(12, 'quarter')}
    head = ('<attributes><divisions>12</divisions><key><fifths>0</fifths></key><time><beats>2</beats><beat-type>4</beat-type></time>'
            '<clef><sign>G</sign><line>2</line></clef></attributes>')
    body = ''.join(f'<measure number="{b}">' + (head if b == 1 else '') + bars.get(b, rest(24, 'whole')) + '</measure>' for b in range(1, 9))
    return ('<?xml version="1.0" encoding="UTF-8"?><score-partwise version="3.1"><part-list>'
            f'<score-part id="P1"><part-name>Flute</part-name></score-part></part-list><part id="P1">{body}</part></score-partwise>')


def tuplets(path):
    """[(kind, fields)] of every tuplet record in the file"""
    with zipfile.ZipFile(path) as z:
        tree, _ = dorico_file._parse(z.read('score.dtn'))
    out = []
    for f in tree.items(tree.child(0, 'flows')):
        for b in tree.items(tree.child(f, 'blocks')):
            for e in tree.items(tree.child(b, 'events')):
                if 'uplet' in tree.name(e):
                    out.append((tree.name(e), tree.text(e)))
    return out


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


def validate(xml):
    """the schema errors of a MusicXML text, checked against Dorico's own copy of the schema ([] = valid)"""
    from lxml import etree
    text = open(XSD, encoding='utf-8').read().replace('http://www.musicxml.org/xsd/', '')
    schema = etree.XMLSchema(etree.fromstring(text.encode('utf-8'), base_url=XSD))
    doc = etree.fromstring(xml.encode('utf-8'))
    return [] if schema.validate(doc) else [f'line {e.line}: {e.message}' for e in schema.error_log][:5]


def close_scratch(stem, his):
    """close the scratch project and nothing else. Nov 23: the old cleanup clicked File > Close Project three
    times while a warning was open; Dorico queued them as forced commands, and when the warning went, the
    second one closed Brian's project. Now: nothing while any dialog is open, the scratch project must be
    in front, one Close Project only, and Don't Save only for a prompt that sits over the scratch project"""
    if dialogs(exclude=()):
        print('a dialog is open, so nothing was sent; close it by hand:', dialogs(exclude=()))
        return False
    w = next((w[0] for w in projects() if stem in w[0]), None)
    if not w:
        return True
    keys('', raise_window=w)
    time.sleep(0.6)
    if stem not in front():
        print('the scratch project is not in front, so nothing was sent:', front())
        return False
    menu('File', 'Close Project')
    if wait(lambda: dialogs(exclude=()), 6):
        order = [x[0] for x in wins() if x[1] == 'AXStandardWindow']
        if not order or stem not in order[0]:
            print('a prompt is open but the scratch project is not under it; nothing sent:', order)
            return False
        keys('keystroke "d" using command down')
    gone = wait(lambda: not any(stem in x[0] for x in projects()), 10)
    return bool(gone) and any(x[0] == his for x in projects())


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


def glissandi(path):
    """[(kind, fields)] of every glissando line in the file"""
    with zipfile.ZipFile(path) as z:
        tree, _ = dorico_file._parse(z.read('score.dtn'))
    out = []
    for f in tree.items(tree.child(0, 'flows')):
        for b in tree.items(tree.child(f, 'blocks')):
            for e in tree.items(tree.child(b, 'events')):
                if 'liss' in tree.name(e):
                    out.append((tree.name(e), tree.text(e)))
    return out


def show(ns):
    return ' '.join(f'{n.position}:{n.pitch_name}/{n.duration}' for n in ns)


def main(mode='shorten'):
    if len(projects()) != 1 or dialogs(exclude=()):
        print('busy: need his one project window and no dialog:', projects(), dialogs(exclude=()))
        return 2
    his = projects()[0][0]
    stem = f'sw_test_{int(time.time())}'
    tmp = os.path.join(os.path.dirname(LOG), 'sw_scratch')
    os.makedirs(tmp, exist_ok=True)
    src = f'{tmp}/{stem}.musicxml'
    xml = tuplet_xml() if mode == 'tuplet' else scratch_xml()
    bad = validate(xml)
    if bad:
        print('the scratch MusicXML is not valid, so Dorico was not touched:', bad)
        return 1
    open(src, 'w').write(xml)
    start = time.time()
    subprocess.run(['open', '-a', 'Dorico 4', src])
    mine = wait(lambda: next((w[0] for w in projects() if stem in w[0]), None), 120, 2)
    if not mine:
        print('failed: the scratch project did not open', projects(), dialogs(exclude=()))
        return 1
    time.sleep(2)
    if dialogs(exclude=()):
        print('a dialog opened with the scratch project, so nothing was sent:', dialogs(exclude=()))
        return 1
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
        fl, va = ns['Flute'], ns.get('Viola', [])
        print('before:', show(fl), '|', show(va))
        d = Dorico()

        def run(cmds):
            if stem not in front():
                raise RuntimeError(f'the front window is {front()!r}, not the scratch project')
            for c in cmds:
                err = d.cmd(c, wait=0.12)
                if err:
                    print('  refused:', c, err)

        pick = lambda ns, bar, name: next(n for n in ns if (n.bar or int(n.position // 2) + 1) == bar and n.pitch_name == name)
        if mode == 'tuplet':
            at = lambda pos: next(n for n in fl if n.position == pos)
            print('tuplets before:', [(k, f.get('position'), f.get('duration')) for k, f in tuplets(path)])
            run([at(1).select_command] + ['EventEdit.NavigateRightExtend'] * 7 + ['Edit.Delete'])
            time.sleep(0.8)
            before = os.path.getmtime(path)
            keys('keystroke "s" using command down', raise_window=mine)
            wait(lambda: os.path.getmtime(path) > before, 20, 1)
            print('after delete:', show(notes_of(path)['Flute']))
            print('tuplets after delete:', [(k, f.get('position'), f.get('duration')) for k, f in tuplets(path)])
            fl = notes_of(path)['Flute']
            run([at(0).select_command, 'NoteInput.Enter?Set=true'])
            time.sleep(0.6)
            typed = [('kQuaver', 0, 91), ('kQuaver', 0, 89), ('kCrotchet', 1, 88), ('kQuaver', 0, 89), ('kCrotchet', 0, 88)]
            cmds = ['NoteInput.MoveRight', 'NoteInput.MoveRight']
            for v, dot, m in typed:
                cmds += [f'NoteInput.NoteValue?LogDuration={v}&Set=true'] + (['NoteInput.SetDotted?Value=1&Set=true'] if dot else []) + [f'NoteInput.MIDINoteInput?MIDIPitches={m}']
            run(cmds + ['NoteInput.Exit'])
            time.sleep(1)
            before = os.path.getmtime(path)
            keys('keystroke "s" using command down', raise_window=mine)
            wait(lambda: os.path.getmtime(path) > before, 20, 1)
            print('after typing:', show(notes_of(path)['Flute']))
            print('tuplets after typing:', [(k, f.get('position'), f.get('duration')) for k, f in tuplets(path)])
            return 0
        if mode == 'gliss':
            print('glissandi before:', glissandi(path))
            run([pick(fl, 1, 'C5').select_command, 'EventEdit.NavigateRightExtend', 'NoteInput.CreateGlissando'])
            time.sleep(0.5)
            run([pick(fl, 4, 'G4').select_command, 'EventEdit.NavigateRightExtend', 'EventEdit.NavigateRightExtend', 'NoteInput.CreateGlissando'])
            time.sleep(1)
            before = os.path.getmtime(path)
            keys('keystroke "s" using command down', raise_window=mine)
            wait(lambda: os.path.getmtime(path) > before, 20, 1)
            ids = {n.event_id: f'{n.bar}@{n.onset}:{n.pitch_name}' for n in notes_of(path)['Flute']}
            for kind, f in glissandi(path):
                print('after:', kind, {k: ids.get(int(v), v) if k.lower().endswith('eventid') and str(v).isdigit() else v for k, v in f.items()})
            print('notes after:', show(notes_of(path)['Flute']))
            return 0
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
        closed = close_scratch(stem, his)
        print('scratch closed:', closed, '| left open:', [w[0] for w in projects()], '(his:', his + ')')
        for f in glob.glob(f'{tmp}/{stem}*') + ([path] if path else []):
            if f and os.path.exists(f):
                shutil.move(f, os.path.join(TRASH, os.path.basename(f)))


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:2]))
