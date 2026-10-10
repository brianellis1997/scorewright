"""NotePerformer render helper. Claims render jobs from the Scorewright server and runs dorico_render.py.
Lives outside the server because driving Dorico's windows needs a process macOS trusts with
Accessibility; the launchd server is not. Run it from a trusted context (the Claude Code session, or
launchd once its python has Accessibility permission). Shares the heavy.lock with upload transcription.
usage: python app/np_agent.py"""
import json, os, subprocess, sys, time, urllib.request, fcntl

HERE = os.path.dirname(os.path.abspath(__file__))
S = 'http://127.0.0.1:8790'
LOCK = '/Users/bdogellis/Documents/Score Exports/_bridge/heavy.lock'


def call(path, body=None):
    req = urllib.request.Request(S + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={'Content-Type': 'application/json'}, method='POST' if body is not None else 'GET')
    return json.loads(urllib.request.urlopen(req, timeout=20).read() or b'{}')


while True:
    try:
        job = call('/api/np/claim')
    except Exception:
        time.sleep(10); continue
    if not job.get('stem'):
        time.sleep(4); continue
    with open(LOCK, 'a') as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            r = subprocess.run([sys.executable, f'{HERE}/dorico_render.py', job['xml'], job['stem']], capture_output=True, text=True, timeout=900)
            rc, tail = r.returncode, (r.stdout + r.stderr).strip()[-300:]
        except Exception as e:
            rc, tail = 1, str(e)
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN)
    print(time.strftime('%H:%M:%S'), os.path.basename(job['stem']), rc, tail.splitlines()[-1:] if tail else '', flush=True)
    try:
        call('/api/np/done', dict(job, rc=rc, tail=tail))
    except Exception:
        pass
    if rc == 3:
        time.sleep(60)
