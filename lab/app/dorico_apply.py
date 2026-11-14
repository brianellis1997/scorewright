"""Run a suggestion's Dorico steps (S<n>.dorico.json, written by lab/dorico_plan.py with the
suggestion) in Brian's open project the moment he presses Accept: sw_wait.sh hands the Accept to
sw_on_accept.py, which calls run(). Recipes, timings and the plan format: DORICO.md.

Each target is selected by its internal IDs, read from Dorico's autosave of the project
(lab/dorico_file.py): one EventEdit.Select, in any score and layout. A target the plan wrote itself
is reached from a note that has an ID (via) or from where the step before left the selection
(rel). After a mark on such a note Dorico selects the new mark; "restore" steps through the items at
that position (NavigateNextItemSamePosition) back to the note, so the next step can start there. Note entry starts the caret at a note with an ID and moves it. The status bar is read at
every target before anything changes there.

How Dorico takes commands: it answers each one when it queues it and decides then whether the
command is allowed, against the selection at that moment; it carries it out later and then pushes
"selectionchanged". So the runner waits for that message after each jump. Dorico's undo history
also holds every selection and caret move, so a stopped run is never undone blindly: it stops
before the step whose target does not match, says which step, and can go on from there (--from).
usage (whisperer env): python app/dorico_apply.py <S<n>.dorico.json> [--from k] [--probe]      exit 0 done, 1 stopped
--probe jumps to every start that has an ID and checks it, and places each caret, but types and edits nothing."""
import asyncio, datetime, fcntl, json, os, re, sys, time
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from dorico_rc import Dorico, edits_since  # noqa: E402
import dorico_file  # noqa: E402
from dorico_plan import midi  # noqa: E402

BRIDGE = '/Users/bdogellis/Documents/Score Exports/_bridge/dorico'
AUTOSAVE = os.path.expanduser('~/Library/Application Support/Steinberg/Dorico 4/AutoSave')


class Stop(Exception):
    pass


def expand(specs):
    out = []
    for spec in specs:
        name, _, n = spec.partition('*')
        out += [name] * int(n or 1)
    return out


def run(plan, label='', start=0, probe=False):
    lock = open(f'{BRIDGE}/apply.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX)
    d = Dorico()
    t0, done, short = time.time(), start, 0
    texts = d.sb()[2]
    project = next((t.split(' in ', 1)[1] for t in texts if t.startswith('Flow ') and ' in ' in t), None)
    auto = f'{AUTOSAVE}/{project}.dorico'
    notes = [n for f in dorico_file.read(auto).flows for n in f.notes] if project and os.path.exists(auto) else []
    since = datetime.datetime.fromtimestamp(os.path.getmtime(auto)).strftime('%Y-%m-%d %H:%M:%S') if notes else None
    late = edits_since(since) if since else []

    async def burst(cmds):
        for c in cmds:
            await d.ws.send(json.dumps({"message": "command", "command": c}))
        codes = []
        while len(codes) < len(cmds):
            r = json.loads(await asyncio.wait_for(d.ws.recv(), 10))
            if r.get('message') == 'response':
                codes.append(r.get('code'))
        return codes

    async def settle(wait, until='selectionchanged'):
        try:
            while True:
                r = json.loads(await asyncio.wait_for(d.ws.recv(), wait))
                if r.get('message') == until or (until == 'noteinput' and r.get('message') == 'status' and r.get('noteInputActive') is True):
                    return
        except asyncio.TimeoutError:
            pass

    def go(specs, soft=False):
        cmds = expand(specs)
        for c, code in zip(cmds, d.loop.run_until_complete(burst(cmds)) if cmds else []):
            if code != 'kOK':
                if soft:
                    return False
                raise Stop(f'Dorico refused {c}')
        return True

    def one_by_one(specs):
        for c in expand(specs):
            if d.loop.run_until_complete(burst([c]))[0] != 'kOK':
                raise Stop(f'Dorico refused {c}')

    def find(t):
        want = {midi(n) for n in t['names'] or []}
        cands = [n for n in notes if n.instrument == t['part'] and n.staff == t['staff'] and n.bar == t['bar']
                 and n.onset == Fraction(t['onset']) and n.pitch in want]
        if not cands:
            raise Stop(f'no ID for {t["part"]} bar {t["bar"]} {"/".join(t["names"] or [])}'
                       + (f' (the autosave is from {since[11:]}; you edited after it)' if late else ''))
        return max(cands, key=lambda n: n.pitch).select_command

    def jump(t):
        d.loop.run_until_complete(settle(0.02))
        go([find(t)])
        d.loop.run_until_complete(settle(1.0))

    def there(expect):
        bar, wants = expect
        b, item, _ = d.sb()
        item = item.replace('♯', '#').replace('♭', 'b')
        return (b == bar and any(item.startswith(w) for w in wants)), f'bar {b} {item or "nothing"}'

    def check(expect, what):
        ok, shows = there(expect)
        if not ok:
            raise Stop(f'{what}: expected bar {expect[0]} {expect[1][0].strip()}, Dorico shows {shows}')

    def check_range(step):
        lo, hi = step['range']
        got = next(([int(v) for v in re.findall(r'\d+', p)] for p in d.sb()[2] if re.match(r'Bars? \d', p)), [])
        if got not in ([lo, hi], [lo] if lo == hi else None):
            raise Stop(f'{step["label"]}: the selection covers bars {got}, wanted {lo}-{hi}')

    steps = plan['steps']
    try:
        d.loop.run_until_complete(burst(['NoteInput.Exit']))
        for i in range(start, len(steps)):
            step = steps[i]
            if 'insert' in step:
                if not probe:
                    one_by_one(step['insert'])
                    d.loop.run_until_complete(settle(1.5))
                jump(step['then'])
                check(step['expect'] if not probe else [step['then']['bar'], step['expect'][1]], step['label'])
            elif 'caret' in step:
                c = step['caret']
                jump(c['start'])
                check(c['expect'], step['label'])
                go(['NoteInput.Enter?Set=true'])
                d.loop.run_until_complete(settle(1.0, 'noteinput'))
                one_by_one(c['moves'] + (['NoteInput.Exit'] if probe else step['edits']))
                d.loop.run_until_complete(settle(1.5))
            elif probe:
                if step['target']:
                    jump(step['target'])
                    check(step['expect'], step['label'])
                    go(step.get('extend', []))
                    if 'range' in step:
                        check_range(step)
                elif step.get('via'):
                    jump(step['via']['target'])
            else:
                if step.get('rel') is not None and go(step['rel'], soft=True) and there(step['expect'])[0]:
                    short += 1
                else:
                    if step['target']:
                        jump(step['target'])
                    elif step.get('via'):
                        jump(step['via']['target'])
                        go(step['via']['moves'])
                    else:
                        raise Stop(f'{step["label"]}: no way to reach it')
                    check(step['expect'], step['label'])
                go(step.get('extend', []))
                if 'range' in step:
                    check_range(step)
                go(step['plain'])
                one_by_one(step['edits'])
                if step.get('restore'):
                    d.loop.run_until_complete(settle(0.6))
                    for _ in range(6):
                        if there(step['expect'])[0]:
                            break
                        go(['EventEdit.NavigateNextItemSamePosition'])
                    else:
                        raise Stop(f'{step["label"]}: done, but the note was not found again after it')
            done = i + 1
        go(['Edit.SelectNone'])
        ok, msg = True, f'{len(steps) - start} steps in {time.time() - t0:.1f} s, every target checked' + (' (probe: nothing changed)' if probe else '')
    except (Stop, asyncio.TimeoutError) as e:
        ok, msg = False, f'stopped at step {done + 1} of {len(steps)} ({steps[done]["label"]}): {e or "Dorico did not answer"}'
    with open(f'{BRIDGE}/apply_log.jsonl', 'a') as f:
        f.write(json.dumps(dict(ts=datetime.datetime.now().isoformat(timespec='seconds'), plan=label, start=start, done=done,
                                steps=len(steps), short_walks=short, ok=ok, msg=msg)) + '\n')
    return ok, msg, done


if __name__ == '__main__':
    k = int(sys.argv[sys.argv.index('--from') + 1]) - 1 if '--from' in sys.argv else 0
    ok, msg, done = run(json.load(open(sys.argv[1])), sys.argv[1], k, '--probe' in sys.argv)
    print(('done: ' if ok else 'STOPPED: ') + msg)
    sys.exit(0 if ok else 1)
