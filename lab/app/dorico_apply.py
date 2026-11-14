"""Run a suggestion's Dorico steps (S<n>.dorico.json, written by lab/dorico_plan.py with the
suggestion) in Brian's open project the moment he presses Accept: sw_wait.sh hands the Accept to
sw_on_accept.py, which calls run(). Recipes, timings and the plan format: DORICO.md.

How Dorico takes commands: it answers each one when it queues it (a few ms) and decides then whether
the command is allowed, against the selection at that moment; it carries the command out later
(about 90 ms for a selection move in a 36-staff score) and then pushes "selectionchanged". So after
the start click the runner waits for that message, then sends the walk as one burst. The status bar
is read once at each target (about 190 ms; the read also waits until the queue is done). Edits go
one at a time, each counted. A failed check or a refused command undoes this run's edits, so his
project is never left half changed. A short walk from the step before is tried first when the plan
has one; when it misses, the full walk from the anchor follows.
usage (whisperer env): python app/dorico_apply.py <S<n>.dorico.json>      exit 0 done, 1 stopped"""
import asyncio, datetime, fcntl, json, re, sys, time

from dorico_rc import Dorico

BRIDGE = '/Users/bdogellis/Documents/Score Exports/_bridge/dorico'


class Stop(Exception):
    pass


def expand(specs):
    out = []
    for spec in specs:
        name, _, n = spec.partition('*')
        out += [name] * int(n or 1)
    return out


def run(plan, label=''):
    lock = open(f'{BRIDGE}/apply.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX)
    d = Dorico()
    done, short, missed, t0 = 0, 0, 0, time.time()

    async def burst(cmds):
        for c in cmds:
            await d.ws.send(json.dumps({"message": "command", "command": c}))
        codes = []
        while len(codes) < len(cmds):
            r = json.loads(await asyncio.wait_for(d.ws.recv(), 10))
            if r.get('message') == 'response':
                codes.append(r.get('code'))
        return codes

    async def settle(wait):
        try:
            while json.loads(await asyncio.wait_for(d.ws.recv(), wait)).get('message') != 'selectionchanged':
                pass
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

    def edit(spec):
        nonlocal done
        for c in expand([spec]):
            if d.loop.run_until_complete(burst([c]))[0] != 'kOK':
                raise Stop(f'Dorico refused {c}')
            done += 1

    def there(step):
        bar, wants = step['expect']
        b, item, _ = d.sb()
        item = item.replace('♯', '#').replace('♭', 'b')
        return (b == bar and any(item.startswith(w) for w in wants)), f'bar {b} {item or "nothing"}'

    def walk(step):
        nonlocal short, missed
        if 'rel' in step:
            if go(step['rel'], soft=True) and there(step)[0]:
                short += 1
                return
            missed += 1
        d.loop.run_until_complete(settle(0.02))
        go([plan['anchor']['command']])
        d.loop.run_until_complete(settle(0.6))
        go(step['moves'])
        ok, shows = there(step)
        if not ok:
            raise Stop(f'{step["label"]}: expected bar {step["expect"][0]} {step["expect"][1][0].strip()}, Dorico shows {shows}')

    def check_range(step):
        lo, hi = step['range']
        got = next(([int(v) for v in re.findall(r'\d+', p)] for p in d.sb()[2] if re.match(r'Bars? \d', p)), [])
        if got not in ([lo, hi], [lo] if lo == hi else None):
            raise Stop(f'{step["label"]}: the selection covers bars {got}, wanted {lo}-{hi}')

    try:
        d.loop.run_until_complete(burst(['NoteInput.Exit']))
        for step in plan['steps']:
            walk(step)
            go(step.get('extend', []))
            if 'range' in step:
                check_range(step)
            go(step['plain'])
            for c in step['edits']:
                edit(c)
        go(['Edit.SelectNone'])
        ok, msg = True, f'{done} edits in {time.time() - t0:.1f} s, every target checked'
    except (Stop, asyncio.TimeoutError) as e:
        if done:
            d.loop.run_until_complete(burst(['Edit.Undo'] * done))
        ok, msg = False, f'stopped and undid this run ({done} edits): {e}'
    with open(f'{BRIDGE}/apply_log.jsonl', 'a') as f:
        f.write(json.dumps(dict(ts=datetime.datetime.now().isoformat(timespec='seconds'), plan=label,
                                steps=len(plan['steps']), short_walks=short, short_missed=missed, ok=ok, msg=msg)) + '\n')
    return ok, msg


if __name__ == '__main__':
    ok, msg = run(json.load(open(sys.argv[1])), sys.argv[1])
    print(('done: ' if ok else 'STOPPED: ') + msg)
    sys.exit(0 if ok else 1)
