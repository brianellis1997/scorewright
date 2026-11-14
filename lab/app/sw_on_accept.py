"""Put an accepted suggestion into Brian's open Dorico project the moment he presses Accept.
sw_wait.sh pipes every new inbox line here. For an "[ACCEPT S<n>]" line whose suggestion has a Dorico
plan beside it (S<n>.dorico.json, saved by sw_suggest.py --plan), this runs the plan
(dorico_apply.py) and tells Brian the result in the panel. A plan runs once: its result is kept in
S<n>.dorico.result.json; a stopped run keeps its edits so far and goes on from the stopped step
(dorico_apply.py --from k). After a full run it exports the project and compares it with the
suggestion (lab/dorico_check.py), and the panel says what, if anything, differs. Every other line
passes untouched.
usage: sw_wait.sh does it; by hand: echo '<inbox line>' | python sw_on_accept.py [--quiet]"""
import datetime, glob, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dorico_apply import run  # noqa: E402
from dorico_check import problems  # noqa: E402

E = '/Users/bdogellis/Documents/Score Exports'
OUTBOX = f'{E}/_bridge/queue/outbox.jsonl'
QUIET = '--quiet' in sys.argv


def say(session, text, working=False):
    if QUIET:
        return
    rec = dict(ts=datetime.datetime.now().isoformat(timespec='seconds'), session=session, text=text)
    if working:
        rec['working'] = True
    open(OUTBOX, 'a').write(json.dumps(rec) + '\n')


def fresh_autosave(session, sid):
    """after a run that changed the project, wait for Dorico's next autosave (it comes every few
    minutes, and over the link Dorico refuses to autosave): its note numbers are what the plan uses"""
    log = f'{E}/_bridge/dorico/apply_log.jsonl'
    saves = glob.glob(os.path.expanduser('~/Library/Application Support/Steinberg/Dorico 4/AutoSave/*.dorico'))
    if not os.path.exists(log) or not saves:
        return True
    runs = [json.loads(x) for x in open(log) if x.strip()]
    changed = [r['ts'] for r in runs if r.get('done', 0) > r.get('start', 0) and 'probe' not in r.get('msg', '')]
    newest = max(saves, key=os.path.getmtime)
    if not changed or datetime.datetime.fromtimestamp(os.path.getmtime(newest)).isoformat(timespec='seconds') > changed[-1]:
        return True
    say(session, f'Waiting for Dorico to autosave (it does that every few minutes) before {sid}, so every note has its new number.', working=True)
    t0, m0 = time.time(), os.path.getmtime(newest)
    while time.time() - t0 < 420:
        time.sleep(5)
        if os.path.getmtime(newest) != m0:
            time.sleep(2)
            return True
    say(session, f'Dorico did not autosave in 7 minutes, so {sid} is not in yet. I will look at it.')
    print(f'[DORICO {sid}] WAITING: no autosave in 7 minutes', flush=True)
    return False


for line in sys.stdin:
    try:
        rec = json.loads(line)
    except ValueError:
        continue
    m = re.match(r'\[ACCEPT (S\d+)\]', rec.get('text', ''))
    if not m:
        continue
    sid, session = m.group(1), rec.get('session', 'current')
    base = f'{E}/_scorewright_out/session/{session}/{sid}.dorico'
    if not os.path.exists(base + '.json') or os.path.exists(base + '.result.json'):
        continue
    plan = json.load(open(base + '.json'))
    if not fresh_autosave(session, sid):
        continue
    say(session, f'Putting {sid} into Dorico now: {len(plan["steps"])} steps.', working=True)
    ok, msg, done = run(plan, base + '.json')
    json.dump(dict(ok=ok, msg=msg, done=done, ts=datetime.datetime.now().isoformat(timespec='seconds')), open(base + '.result.json', 'w'))
    if not ok:
        say(session, f'{sid} is not all in Dorico yet: it {msg}. Only the steps before it are in your score. I will fix that step and finish it.')
        print(f'[DORICO {sid}] STOPPED: {msg}', flush=True)
        continue
    folder = f'{E}/_scorewright_out/session/{session}'
    export = f'{folder}/dorico_export_after_{sid}.xml'
    subprocess.run([sys.executable, f'{HERE}/dorico_export.py', export], capture_output=True, text=True, timeout=300)
    lines = problems(open(f'{folder}/{sid}.musicxml', encoding='utf-8').read(), open(export, encoding='utf-8').read()) if os.path.exists(export) else ['no export to check']
    check = 'A fresh export matches it in every note, spelling, rhythm, tie and mark.' if not lines else \
        f'A fresh export differs in {len(lines)} place(s), first: {lines[0]}. I will fix that.'
    say(session, f'{sid} is in Dorico: {msg}. {check}')
    print(f'[DORICO {sid}] done: {msg}. CHECK: ' + ('all match' if not lines else ' | '.join(lines[:8])), flush=True)
