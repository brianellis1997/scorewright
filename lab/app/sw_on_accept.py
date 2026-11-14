"""Put an accepted suggestion into Brian's open Dorico project the moment he presses Accept.
sw_wait.sh pipes every new inbox line here. For an "[ACCEPT S<n>]" line whose suggestion has a Dorico
plan beside it (S<n>.dorico.json, saved by sw_suggest.py --plan), this runs the plan
(dorico_apply.py) and tells Brian the result in the panel. A plan runs once: its result is kept in
S<n>.dorico.result.json; a stopped run keeps its edits so far and goes on from the stopped step
(dorico_apply.py --from k). Every other line passes untouched.
usage: sw_wait.sh does it; by hand: echo '<inbox line>' | python sw_on_accept.py [--quiet]"""
import datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from dorico_apply import run  # noqa: E402

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
    say(session, f'Putting {sid} into Dorico now: {len(plan["steps"])} steps.', working=True)
    ok, msg, done = run(plan, base + '.json')
    json.dump(dict(ok=ok, msg=msg, done=done, ts=datetime.datetime.now().isoformat(timespec='seconds')), open(base + '.result.json', 'w'))
    say(session, f'{sid} is in Dorico: {msg}.' if ok else
        f'{sid} is not all in Dorico yet: it {msg}. Only the steps before it are in your score. I will fix that step and finish it.')
    print(f'[DORICO {sid}] ' + ('done: ' if ok else 'STOPPED: ') + msg, flush=True)
