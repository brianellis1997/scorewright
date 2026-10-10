"""Scorewright local server: the loop that Claude Code is for code.

Owns one session folder (working score + numbered suggestions + chat + verdicts) and exposes it
three ways:
  HTTP  :8790  the phone/browser page (chat with mic, score with green bars, accept/reject, play)
  WS    :8791  the MuseScore panel (same chat and buttons, opens suggestions in the editor)
  files        the Claude Code session: inbox.jsonl (what Brian said), outbox.jsonl (replies),
               suggestions registered with sw_suggest.py

Run (whisperer env):  python app/server.py [session_name]
"""
import os, sys, json, time, threading, asyncio, re, shutil, subprocess, datetime, urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.dirname(HERE)
sys.path.insert(0, '/Users/bdogellis/repos/scorewright'); sys.path.insert(0, LAB)
E = '/Users/bdogellis/Documents/Score Exports'
BRIDGE = f'{E}/_bridge'
CUR = f'{BRIDGE}/current_session.txt'
def _initial_session():
    try:
        name = open(CUR).read().strip()
        if name: return name
    except FileNotFoundError: pass
    return sys.argv[1] if len(sys.argv) > 1 else 'current'
SESSION = _initial_session()
SDIR = f'{E}/_scorewright_out/session/{SESSION}'
os.makedirs(SDIR, exist_ok=True); os.makedirs(f'{BRIDGE}/queue', exist_ok=True)
INBOX, OUTBOX = f'{BRIDGE}/queue/inbox.jsonl', f'{BRIDGE}/queue/outbox.jsonl'
STATE = f'{SDIR}/state.json'
lock = threading.Lock()
STARTED = str(time.time())
HUM_PY = '/Users/bdogellis/opt/anaconda3/bin/python'    # the one env here where librosa imports cleanly

def score_bpm(path):
    try:
        import re
        m = re.search(r'<per-minute>([\d.]+)</per-minute>', open(path, encoding='utf-8').read()) or re.search(r'tempo="([\d.]+)"', open(path, encoding='utf-8').read())
        return float(m.group(1)) if m else 120.0
    except Exception: return 120.0
render_lock = threading.Lock()
clients = set()          # websocket clients (MuseScore panels)
loop = None

def now(): return datetime.datetime.now().isoformat(timespec='seconds')
def load():
    if os.path.exists(STATE): return json.load(open(STATE))
    return dict(session=SESSION, working=None, suggestions=[], chat=[], seq=0)
def save(st): json.dump(st, open(STATE, 'w'), indent=1)
def chat(st, who, text, extra=None):
    st['chat'].append(dict(ts=now(), who=who, text=text, **(extra or {})))
    st['chat'] = st['chat'][-200:]

def render_svg(xml_path, lo=None, hi=None):
    import diffview, xmledit
    xml = open(xml_path, encoding='utf-8').read()
    try:
        last = max(int(m) for m in re.findall(r'<measure number="(\d+)"', xml))
    except ValueError:
        last = 1
    ex = xmledit.excerpt(xml, 1, last, None) if lo is None else xmledit.excerpt(xml, max(1, lo - 4), min(last, hi + 4), None)
    out = diffview.render(ex, width=1400, timemap=True, n_parts=99)
    return out[0]

def audio_uri(xml_path, lo=None, hi=None):
    """audio through MuseScore's engine (Muse Sounds when installed), windowless, cached per file."""
    import base64, hashlib
    key = hashlib.md5((xml_path + str(os.path.getmtime(xml_path))).encode()).hexdigest()[:12]
    mp3 = f'{SDIR}/audio_{key}.mp3'
    if not os.path.exists(mp3):
        subprocess.run(['/Applications/MuseScore 4.app/Contents/MacOS/mscore', '-o', mp3, xml_path], capture_output=True, timeout=180)
    if not os.path.exists(mp3): return ''
    return 'data:audio/mpeg;base64,' + base64.b64encode(open(mp3, 'rb').read()).decode()

def prerender(xml_path, out_stem, lo=None, hi=None):
    """svg + audio to files in a fresh process, one at a time."""
    def work():
        with render_lock:
            r = subprocess.run([sys.executable, f'{HERE}/render_one.py', xml_path, out_stem, os.path.dirname(out_stem)], capture_output=True, text=True, timeout=300)
            print('render', os.path.basename(out_stem), (r.stdout + r.stderr).strip().split('\n')[-1][:120], flush=True)
        mark_np(out_stem, False)
        enqueue_np(xml_path, out_stem)
    threading.Thread(target=work, daemon=True).start()

# ---------- NotePerformer audio through Dorico, one render at a time --------------------------
import queue
NP_Q = queue.Queue(); NP_PENDING = set()
import fcntl
class FileLock:
    """cross-process: a Dorico render (np_agent.py) and a transcription never run at once; Dorico timed out opening a file while one ran"""
    def __init__(self, path): self.path = path; self.f = None
    def acquire(self): self.f = open(self.path, 'a'); fcntl.flock(self.f, fcntl.LOCK_EX)
    def release(self):
        if self.f: fcntl.flock(self.f, fcntl.LOCK_UN); self.f.close(); self.f = None
HEAVY_PATH = f'{BRIDGE}/heavy.lock'

def mark_np(stem, ok):
    sp = f'{os.path.dirname(stem)}/state.json'; key = os.path.basename(stem)
    with lock:
        if not os.path.exists(sp): return
        st = json.load(open(sp)); st.setdefault('np_audio', {})
        if ok: st['np_audio'][key] = now()
        else: st['np_audio'].pop(key, None)
        json.dump(st, open(sp, 'w'), indent=1)

def enqueue_np(xml_path, stem):
    if stem in NP_PENDING or not os.path.exists(xml_path): return
    if '<pitch>' not in open(xml_path, encoding='utf-8', errors='ignore').read(): return     # an empty score has nothing to hear
    NP_PENDING.add(stem); NP_Q.put((xml_path, stem, 0))

def np_claim():
    try: xml_path, stem, tries = NP_Q.get_nowait()
    except queue.Empty: return {}
    return dict(xml=xml_path, stem=stem, tries=tries)

def np_done(xml_path, stem, tries, rc, tail=''):
    print('np', os.path.basename(stem), rc, tail[-160:], flush=True)
    if rc == 0:
        mark_np(stem, True); NP_PENDING.discard(stem)
    elif rc in (2, 3) and tries < 40:          # 2: Dorico busy with his own project, 3: helper lacks permission; try again later
        threading.Timer(90 if rc == 2 else 300, lambda a=(xml_path, stem, tries + 1): NP_Q.put(a)).start()
    else:
        NP_PENDING.discard(stem)

def np_catch_up():
    """give the working score and every open suggestion NotePerformer audio if it is missing or stale"""
    st = load(); items = []
    if st.get('working'): items.append((st['working'], f'{SDIR}/working'))
    items += [(x['green'], f"{SDIR}/{x['id']}") for x in st['suggestions'] if x['status'] == 'open']
    for xml_path, stem in items:
        m4a = stem + '.np.m4a'
        if os.path.exists(m4a) and os.path.exists(xml_path) and os.path.getmtime(m4a) > os.path.getmtime(xml_path):
            if os.path.basename(stem) not in st.get('np_audio', {}): mark_np(stem, True)
        else:
            enqueue_np(xml_path, stem)

# ---------- pieces (sessions) ------------------------------------------------------------------
PRESETS = {
    'Solo piano': [('Piano', 'piano')],
    'String quartet': [('Violin I', 'treble'), ('Violin II', 'treble'), ('Viola', 'alto'), ('Violoncello', 'bass')],
    'Piano trio': [('Violin', 'treble'), ('Violoncello', 'bass'), ('Piano', 'piano')],
    'Voice and piano': [('Voice', 'treble'), ('Piano', 'piano')],
    'Violin and piano': [('Violin', 'treble'), ('Piano', 'piano')],
    'Cello and piano': [('Violoncello', 'bass'), ('Piano', 'piano')],
    'String orchestra': [('Violin I', 'treble'), ('Violin II', 'treble'), ('Viola', 'alto'), ('Violoncello', 'bass'), ('Contrabass', 'bass')],
}
SHORT = {'Violin I': 'Vln. I', 'Violin II': 'Vln. II', 'Violin': 'Vln.', 'Viola': 'Vla.', 'Violoncello': 'Vc.', 'Contrabass': 'Cb.', 'Voice': 'V.', 'Piano': 'Pno.'}

def abc_key(k):
    k = (k or 'C').strip()
    m = re.match(r'^([A-Ga-g])\s*([#b♯♭]?)\s*(.*)$', k)
    if not m: return 'C'
    note = m.group(1).upper() + {'♯': '#', '♭': 'b'}.get(m.group(2), m.group(2))
    rest = m.group(3).lower()
    return note + ('m' if rest.startswith('m') and not rest.startswith('maj') else '')

def blank_score(path, title, preset, key, meter, tempo, bars):
    num, den = (int(x) for x in meter.split('/'))
    units = num * 16 // den
    voices, groups, v = [], [], 0
    for name, clef in PRESETS.get(preset, PRESETS['Solo piano']):
        if clef == 'piano':
            voices.append(f'V:{v+1} clef=treble nm="{name}" snm="{SHORT.get(name, name)}"'); voices.append(f'V:{v+2} clef=bass')
            groups.append('{' + f'{v+1} {v+2}' + '}'); v += 2
        else:
            voices.append(f'V:{v+1} clef={clef} nm="{name}" snm="{SHORT.get(name, name)}"'); groups.append(str(v + 1)); v += 1
    body = [f'[V:{i}] ' + ' '.join(f'z{units}|' for _ in range(bars)) for i in range(1, v + 1)]
    abc = '\n'.join(['X:1', f'T:{title}', 'C:Brian Ellis', '%%score ' + ' '.join(groups), 'L:1/16', f'M:{meter}', f'Q:1/4={tempo}', f'K:{abc_key(key)}', *voices, *body]) + '\n'
    d = os.path.dirname(path); stem = os.path.splitext(os.path.basename(path))[0]
    open(f'{d}/{stem}.abc', 'w').write(abc)
    subprocess.run([sys.executable, '-W', 'ignore', f'{LAB}/NotaGen/data/abc2xml.py', '-o', d, f'{d}/{stem}.abc'], capture_output=True, timeout=60)
    x = f'{d}/{stem}.xml'
    if not os.path.exists(x): raise RuntimeError('abc2xml failed')
    os.replace(x, path)
    return path

def use_session(name):
    global SESSION, SDIR, STATE
    with lock:
        SESSION = name; SDIR = f'{E}/_scorewright_out/session/{name}'; STATE = f'{SDIR}/state.json'
        os.makedirs(SDIR, exist_ok=True); open(CUR, 'w').write(name)
    threading.Thread(target=np_catch_up, daemon=True).start()

def list_sessions():
    base = f'{E}/_scorewright_out/session'; out = []
    for n in os.listdir(base):
        sp = f'{base}/{n}/state.json'
        if os.path.exists(sp):
            try: st = json.load(open(sp))
            except Exception: continue
            out.append(dict(name=n, title=st.get('title') or n, mtime=os.path.getmtime(sp)))
    return sorted(out, key=lambda x: -x['mtime'])

def act_new_piece(title, preset, key, meter, tempo, bars=8):
    title = (title or 'Untitled').strip()[:80]
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'piece'
    base = f'{E}/_scorewright_out/session'; name, i = slug, 2
    while os.path.exists(f'{base}/{name}/state.json'): name = f'{slug}-{i}'; i += 1
    use_session(name)
    start = blank_score(f'{SDIR}/start.musicxml', title, preset, key, meter, int(tempo), int(bars))
    with lock:
        st = dict(session=name, title=title, preset=preset, key=key, meter=meter, tempo=int(tempo), created=now(), working=None, suggestions=[], chat=[], seq=0)
        chat(st, 'claude', f'New piece: {title}. {preset}, {key}, {meter}, quarter = {tempo}. Tell me what you have in mind, play or upload something, or press continue.')
        save(st)
    act_set_working(start)
    open(INBOX, 'a').write(json.dumps(dict(ts=now(), session=name, text=f'[NEW PIECE {name}] {title}: {preset}, {key}, {meter}, quarter={tempo}')) + '\n')
    return name

# ---------- uploads: any audio or video file, transcribed in the background -------------------
JOBS = {}
def run_upload(jid, path, sdir, bpm):
    got = False
    try:
        JOBS[jid] = dict(status='waiting for the Mac to finish a playback render')
        heavy = FileLock(HEAVY_PATH); heavy.acquire(); got = True
        JOBS[jid] = dict(status='extracting audio')
        wav = f'{sdir}/{jid}.wav'
        r = subprocess.run([sys.executable, f'{HERE}/media.py', path, wav], capture_output=True, text=True, timeout=3600)
        if not os.path.exists(wav): raise RuntimeError('could not read the audio: ' + (r.stderr or r.stdout)[-300:])
        JOBS[jid] = dict(status='transcribing')
        out = subprocess.run([sys.executable, f'{HERE}/listen.py', wav, str(bpm), '-', jid, '--upload', f'--out={sdir}'], capture_output=True, text=True, timeout=7200, cwd=LAB)
        res = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else dict(error=out.stderr[-600:])
        res['id'] = jid
        if res.get('svg'): open(f'{sdir}/{jid}.svg', 'w').write(res.pop('svg'))
        if res.get('abc'): open(f'{sdir}/{jid}.abc', 'w').write(res.pop('abc') + '\n')
        notes = res.pop('notes', [])
        json.dump(notes, open(f'{sdir}/{jid}.midi.json', 'w'))
        res['n_notes'] = len(notes); res['svg_url'] = f'/take_svg?id={jid}'
        JOBS[jid] = dict(status='done', result=res)
    except Exception as e:
        JOBS[jid] = dict(status='failed', error=str(e)[:400])
    finally:
        if got: heavy.release()

def broadcast(msg):
    if loop is None: return
    data = json.dumps(msg)
    async def _send():
        dead = []
        for ws in list(clients):
            try: await ws.send(data)
            except Exception: dead.append(ws)
        for d in dead: clients.discard(d)
    asyncio.run_coroutine_threadsafe(_send(), loop)

# ---------- actions shared by HTTP, WS and the CLI ----------------------------------------
def act_message(text, who='brian'):
    with lock:
        st = load(); chat(st, who, text); save(st)
    if who == 'brian':
        open(INBOX, 'a').write(json.dumps(dict(ts=now(), session=SESSION, text=text)) + '\n')
    broadcast(dict(type='chat', who=who, text=text))

def act_suggest(xml_path, lo, hi, note, lines=None):
    with lock:
        st = load(); st['seq'] += 1; sid = f"S{st['seq']}"
        dst = f'{SDIR}/{sid}.musicxml'; shutil.copy(xml_path, dst)
        # editor copies: green + markers + pedal fix + layout
        W = sys.executable
        subprocess.run([W, f'{LAB}/color_xml.py', dst, f'{SDIR}/{sid}.green.musicxml', str(lo), str(hi)], capture_output=True)
        subprocess.run([W, f'{LAB}/fix_pedal.py', f'{SDIR}/{sid}.green.musicxml', f'{SDIR}/{sid}.green.musicxml'], capture_output=True)
        subprocess.run([W, f'{LAB}/mark_xml.py', f'{SDIR}/{sid}.green.musicxml', f'{SDIR}/{sid}.green.musicxml', str(lo), str(hi)], capture_output=True)
        subprocess.run([W, f'{LAB}/layout_xml.py', f'{SDIR}/{sid}.green.musicxml', f'{SDIR}/{sid}.green.musicxml'], capture_output=True)
        sug = dict(id=sid, ts=now(), lo=lo, hi=hi, note=note, file=dst, green=f'{SDIR}/{sid}.green.musicxml', status='open', lines=lines)
        st['suggestions'].append(sug); chat(st, 'claude', f'Suggestion {sid}: bars {lo}-{hi}. {note}', dict(suggestion=sid)); save(st)
    prerender(sug['green'], f'{SDIR}/{sid}')
    broadcast(dict(type='suggestion', **sug))
    return sid

def act_verdict(sid, accepted, text='', who='brian'):
    with lock:
        st = load(); sug = next((s for s in st['suggestions'] if s['id'] == sid), None)
        if not sug: return False
        sug['status'] = 'accepted' if accepted else 'rejected'; sug['verdict'] = text
        if accepted:
            shutil.copy(sug['file'], f'{SDIR}/working.musicxml'); st['working'] = f'{SDIR}/working.musicxml'
            for ext in ('.audio.txt', '.bars.json', '.np.m4a'):
                if os.path.exists(f"{SDIR}/{sid}{ext}"): shutil.copy(f"{SDIR}/{sid}{ext}", f'{SDIR}/working{ext}')
            def redraw(xml=f'{SDIR}/working.musicxml', stem=f'{SDIR}/working'):
                with render_lock:
                    subprocess.run([sys.executable, f'{HERE}/render_one.py', xml, stem, SDIR], capture_output=True, text=True, timeout=300)
            threading.Thread(target=redraw, daemon=True).start()
            st.setdefault('np_audio', {})
            if st['np_audio'].get(sid): st['np_audio']['working'] = now()
            else:
                st['np_audio'].pop('working', None)
                threading.Thread(target=enqueue_np, args=(f'{SDIR}/working.musicxml', f'{SDIR}/working'), daemon=True).start()
            rebase_open(st)
        label = ('Accepted ' if accepted else 'Rejected ') + sid + (': ' + text if text else '')
        chat(st, who, label if who == 'brian' else 'Noted from your message, ' + label[0].lower() + label[1:], dict(verdict=sid)); save(st)
    rec = dict(ts=now(), test=f'{SESSION}/{sid}', task=sug.get('note', ''), bars=[sug['lo'], sug['hi']], suggestion_lines=sug.get('lines'),
               score_file=sug['file'], verdict=('ACCEPTED. ' if accepted else 'REJECTED. ') + text, score=4 if accepted else 1, source='ui')
    open(f'{BRIDGE}/verdicts.jsonl', 'a').write(json.dumps(rec) + '\n')
    open(INBOX, 'a').write(json.dumps(dict(ts=now(), session=SESSION, text=f"[{'ACCEPT' if accepted else 'REJECT'} {sid}] {text}")) + '\n')
    broadcast(dict(type='verdict', id=sid, accepted=accepted, text=text))
    return True


def rebase_open(st):
    """after an Accept, every other open suggestion is re-applied on top of the new working score so
    what he sees in 'show' always includes what he already accepted."""
    def work(sugs, working):
        for sug in sugs:
            lines = [l for l in (sug.get('lines') or []) if l.strip()]
            if not lines: continue
            tmp = f"{SDIR}/{sug['id']}.lines.txt"; open(tmp, 'w').write('\n'.join(lines) + '\n')
            tag = f"rebase_{SESSION}_{sug['id']}"
            r = subprocess.run(['/Users/bdogellis/miniforge3/envs/text2score/bin/python', f'{LAB}/human_apply.py', working, '9999', str(sug['lo']), str(sug['hi']), tmp, tag, sug.get('note', '')], capture_output=True, text=True, timeout=600)
            fin = f'{LAB}/apply_{tag}_final.xml'
            if not os.path.exists(fin): print('rebase failed', sug['id'], r.stderr[-200:], flush=True); continue
            shutil.copy(fin, sug['file'])
            W = sys.executable
            subprocess.run([W, f'{LAB}/color_xml.py', sug['file'], sug['green'], str(sug['lo']), str(sug['hi'])], capture_output=True)
            subprocess.run([W, f'{LAB}/fix_pedal.py', sug['green'], sug['green']], capture_output=True)
            subprocess.run([W, f'{LAB}/mark_xml.py', sug['green'], sug['green'], str(sug['lo']), str(sug['hi'])], capture_output=True)
            subprocess.run([W, f'{LAB}/layout_xml.py', sug['green'], sug['green']], capture_output=True)
            for ext in ('.svg', '.audio.txt', '.bars.json'):
                try: os.remove(f"{SDIR}/{sug['id']}{ext}")
                except FileNotFoundError: pass
            prerender(sug['green'], f"{SDIR}/{sug['id']}")
            print('rebased', sug['id'], flush=True)
    sugs = [dict(x) for x in st['suggestions'] if x['status'] == 'open']
    threading.Thread(target=work, args=(sugs, st['working']), daemon=True).start()

def act_set_working(xml_path):
    with lock:
        st = load(); shutil.copy(xml_path, f'{SDIR}/working.musicxml'); st['working'] = f'{SDIR}/working.musicxml'
        chat(st, 'claude', f'Working score set: {os.path.basename(xml_path)}'); save(st)
    prerender(f'{SDIR}/working.musicxml', f'{SDIR}/working')
    broadcast(dict(type='working', file=f'{SDIR}/working.musicxml'))

MIDI_EVENTS = []; MIDI_PORTS = {}; TAKE = {}
def midi_listen():
    """open every MIDI input that appears (keyboard plugged in any time) and buffer note on/off with wall-clock times"""
    try: import mido
    except Exception as e: print('midi: mido missing', e); return
    last_scan = 0
    while True:
        now = time.time()
        if now - last_scan > 2:
            last_scan = now
            try:
                for name in mido.get_input_names():
                    if name not in MIDI_PORTS:
                        try: MIDI_PORTS[name] = mido.open_input(name); print('midi: listening on', name)
                        except Exception as e: print('midi: cannot open', name, e)
            except Exception as e: print('midi scan', e)
        for name, port in list(MIDI_PORTS.items()):
            try:
                for m in port.iter_pending():
                    if m.type in ('note_on', 'note_off'):
                        MIDI_EVENTS.append((time.time(), m.note, m.velocity if m.type == 'note_on' else 0))
            except Exception as e:
                print('midi: lost', name, e); MIDI_PORTS.pop(name, None)
        if len(MIDI_EVENTS) > 50000: del MIDI_EVENTS[:25000]
        time.sleep(0.005)

def midi_notes_since(t0, t1):
    """pair note on/off inside [t0, t1] -> [{midi, start, end, vel}] with times relative to t0"""
    on = {}; notes = []
    for t, n, v in [e for e in MIDI_EVENTS if t0 <= e[0] <= t1]:
        if v > 0: on[n] = (t, v)
        elif n in on:
            s, vel = on.pop(n); notes.append(dict(midi=n, start=round(s - t0, 3), end=round(t - t0, 3), vel=vel))
    for n, (s, vel) in on.items(): notes.append(dict(midi=n, start=round(s - t0, 3), end=round(t1 - t0, 3), vel=vel))
    return sorted(notes, key=lambda x: x['start'])

def watch_outbox():
    """replies written by the Claude Code session (sw_say.py) go to the UIs."""
    seen = load().get('outbox_seen', 0)
    while True:
        try:
            if os.path.exists(OUTBOX):
                lines = [l for l in open(OUTBOX).read().split('\n') if l.strip()]
                if len(lines) < seen: seen = len(lines)
                for l in lines[seen:]:
                    if l.strip():
                        m = json.loads(l)
                        if m.get('session', SESSION) == SESSION:
                            with lock:
                                st = load(); chat(st, 'claude', m['text']); save(st)
                            broadcast(dict(type='chat', who='claude', text=m['text']))
                if len(lines) != seen:
                    seen = len(lines)
                    with lock:
                        st = load(); st['outbox_seen'] = seen; save(st)
        except Exception as e:
            print('outbox watch', e)
        time.sleep(1)

# ---------- HTTP -------------------------------------------------------------------------
PAGE = open(f'{HERE}/page.html', encoding='utf-8').read() if os.path.exists(f'{HERE}/page.html') else '<h1>page.html missing</h1>'

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, code, body, ctype='application/json'):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(code); self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*'); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        if u.path == '/': return self._send(200, PAGE, 'text/html; charset=utf-8')
        if u.path == '/api/state':
            st = load(); st['page_version'] = STARTED; st['session'] = SESSION; st['np_pending'] = [os.path.basename(x) for x in NP_PENDING if os.path.dirname(x) == SDIR]
            return self._send(200, json.dumps(st))
        if u.path == '/api/sessions':
            return self._send(200, json.dumps(dict(current=SESSION, sessions=list_sessions(), presets=list(PRESETS))))
        if u.path == '/file':
            name = os.path.basename(q.get('name', [''])[0]); p = f'{SDIR}/{name}'
            types = {'.mid': 'audio/midi', '.svg': 'image/svg+xml', '.abc': 'text/plain', '.m4a': 'audio/mp4', '.musicxml': 'application/vnd.recordare.musicxml+xml'}
            ext = os.path.splitext(name)[1].lower()
            if ext not in types or not os.path.exists(p): return self._send(404, 'not found', 'text/plain')
            self.send_response(200); self.send_header('Content-Type', types[ext]); self.send_header('Content-Disposition', f'attachment; filename="{name}"')
            data = open(p, 'rb').read(); self.send_header('Content-Length', str(len(data))); self.end_headers(); self.wfile.write(data); return
        if u.path == '/api/np/claim':
            return self._send(200, json.dumps(np_claim()))
        if u.path == '/api/job':
            return self._send(200, json.dumps(JOBS.get(q.get('id', [''])[0], dict(status='unknown'))))
        if u.path == '/take_svg':
            p = f"{SDIR}/{os.path.basename(q.get('id', [''])[0])}.svg"
            return self._send(200, open(p, encoding='utf-8').read() if os.path.exists(p) else '', 'image/svg+xml')
        if u.path == '/svg':
            sid = q.get('id', [''])[0] or 'working'
            f = f'{SDIR}/{sid}.svg'
            if os.path.exists(f): return self._send(200, open(f).read(), 'image/svg+xml')
            return self._send(404, '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="60"><text x="10" y="35" font-size="16" fill="#888">rendering, try again in a moment</text></svg>', 'image/svg+xml')
        if u.path == '/audio':
            sid = q.get('id', [''])[0] or 'working'
            f = f'{SDIR}/{sid}.audio.txt'
            return self._send(200, open(f).read() if os.path.exists(f) else '', 'text/plain')
        if u.path == '/bars':
            sid = q.get('id', [''])[0] or 'working'
            f = f'{SDIR}/{sid}.bars.json'
            return self._send(200, open(f).read() if os.path.exists(f) else '[]')
        if u.path == '/open':
            st = load(); sid = q.get('id', [''])[0]; app = q.get('app', ['Dorico'])[0]
            sug = next((s for s in st['suggestions'] if s['id'] == sid), None)
            path = (sug['green'] if sug else st.get('working'))
            cmd = {'Dorico': ['open', '-a', 'Dorico 4'], 'MuseScore': ['open', '-a', 'MuseScore 4'], 'Sibelius': [f'{LAB}/open_in_sibelius.sh']}.get(app, ['open', '-a', 'Dorico 4'])
            if path: subprocess.Popen(cmd + [path])
            return self._send(200, '{"ok":true}')
        return self._send(404, 'not found', 'text/plain')
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        up = urllib.parse.urlparse(self.path)
        if up.path == '/api/upload':
            qs = urllib.parse.parse_qs(up.query)
            name = re.sub(r'[^A-Za-z0-9._ -]+', '_', qs.get('name', ['upload'])[0])[-80:] or 'upload'
            jid = time.strftime('upload_%H%M%S'); sdir = SDIR; os.makedirs(f'{sdir}/uploads', exist_ok=True)
            path = f'{sdir}/uploads/{jid}_{name}'
            left = n
            with open(path, 'wb') as f:
                while left > 0:
                    chunk = self.rfile.read(min(left, 1 << 20))
                    if not chunk: break
                    f.write(chunk); left -= len(chunk)
            if left > 0: return self._send(400, json.dumps(dict(error='upload cut short')))
            bpm = qs.get('bpm', ['auto'])[0]
            JOBS[jid] = dict(status='queued')
            threading.Thread(target=run_upload, args=(jid, path, sdir, bpm), daemon=True).start()
            return self._send(200, json.dumps(dict(id=jid, bytes=n)))
        if self.path == '/api/take/start':
            self.rfile.read(n); TAKE['t0'] = time.time(); TAKE['midi_before'] = len(MIDI_EVENTS)
            return self._send(200, json.dumps(dict(ok=True, midi_ports=list(MIDI_PORTS))))
        if self.path == '/api/take/stop':
            raw = self.rfile.read(n); t1 = time.time(); t0 = TAKE.get('t0', t1 - 60); tid = time.strftime('take_%H%M%S')
            wav = f'{SDIR}/{tid}.wav'; open(wav, 'wb').write(raw)
            notes = midi_notes_since(t0, t1); mj = f'{SDIR}/{tid}.midi.json'; json.dump(notes, open(mj, 'w'))
            try:
                st = load(); bpm = score_bpm(st.get('working'))
                out = subprocess.run([sys.executable, f'{HERE}/listen.py', wav, str(bpm), mj if notes else '-', tid], capture_output=True, text=True, timeout=600, cwd=LAB)
                res = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else dict(error=out.stderr[-600:])
            except Exception as e: res = dict(error=str(e))
            res['id'] = tid
            if res.get('svg'): open(f'{SDIR}/{tid}.svg', 'w').write(res['svg'])
            if res.get('abc'): open(f'{SDIR}/{tid}.abc', 'w').write(res['abc'] + '\n')
            return self._send(200, json.dumps(res))
        if self.path == '/api/hum':
            raw = self.rfile.read(n); path = f'{SDIR}/hum_{time.strftime("%H%M%S")}.wav'; open(path, 'wb').write(raw)
            try:
                st = load(); bpm = score_bpm(st.get('working'))
                out = subprocess.run([HUM_PY, f'{HERE}/hum.py', path, str(bpm)], capture_output=True, text=True, timeout=120)
                res = json.loads(out.stdout.strip().splitlines()[-1]) if out.stdout.strip() else dict(error=out.stderr[-400:])
            except Exception as e: res = dict(error=str(e))
            return self._send(200, json.dumps(res))
        body = json.loads(self.rfile.read(n) or b'{}')
        if self.path == '/api/message': act_message(body.get('text', '')); return self._send(200, '{"ok":true}')
        if self.path == '/api/np/done':
            np_done(body.get('xml', ''), body.get('stem', ''), int(body.get('tries', 0)), int(body.get('rc', 1)), body.get('tail', ''))
            return self._send(200, '{"ok":true}')
        if self.path == '/api/new':
            try:
                name = act_new_piece(body.get('title', ''), body.get('preset', 'Solo piano'), body.get('key', 'C'), body.get('meter', '4/4'), body.get('tempo', 90), body.get('bars', 8))
                return self._send(200, json.dumps(dict(ok=True, session=name)))
            except Exception as e:
                return self._send(500, json.dumps(dict(ok=False, error=str(e)[:300])))
        if self.path == '/api/session':
            name = os.path.basename(body.get('name', ''))
            if not os.path.exists(f'{E}/_scorewright_out/session/{name}/state.json'): return self._send(404, json.dumps(dict(ok=False)))
            use_session(name); return self._send(200, json.dumps(dict(ok=True, session=name)))
        if self.path == '/api/take/use':
            tid, words = body['id'], body.get('words', '').strip()
            text = f"[TAKE {tid}] {words}".strip()
            with lock:
                st = load(); chat(st, 'brian', text, dict(take=tid)); save(st)
            open(INBOX, 'a').write(json.dumps(dict(ts=now(), session=SESSION, text=text, take=f'{SDIR}/{tid}.abc', wav=f'{SDIR}/{tid}.wav', midi=f'{SDIR}/{tid}.midi.json')) + '\n')
            broadcast(dict(type='chat', who='brian', text=text))
            return self._send(200, '{"ok":true}')
        if self.path == '/api/accept': act_verdict(body['id'], True, body.get('text', ''), body.get('who', 'brian')); return self._send(200, '{"ok":true}')
        if self.path == '/api/reject': act_verdict(body['id'], False, body.get('text', ''), body.get('who', 'brian')); return self._send(200, '{"ok":true}')
        if self.path == '/api/suggest': act_suggest(body['file'], int(body['lo']), int(body['hi']), body.get('note', ''), body.get('lines')); return self._send(200, '{"ok":true}')
        if self.path == '/api/withdraw':
            sid = body['id']
            with lock:
                st = load(); sug = next((x for x in st['suggestions'] if x['id'] == sid), None)
                if sug: sug['status'] = 'withdrawn'; chat(st, 'claude', f'Withdrew {sid} at your request.'); save(st)
            broadcast(dict(type='verdict', id=sid, accepted=False, text='withdrawn'))
            return self._send(200, '{"ok":true}')
        if self.path == '/api/verdict_note':
            sid, text = body['id'], body.get('text', '')
            with lock:
                st = load(); sug = next((x for x in st['suggestions'] if x['id'] == sid), None)
                if sug: sug['verdict'] = ((sug.get('verdict') or '') + ' ' + text).strip()
                chat(st, 'brian', text, dict(verdict=sid)); save(st)
            open(f'{BRIDGE}/verdicts.jsonl', 'a').write(json.dumps(dict(ts=now(), test=f'{SESSION}/{sid}', verdict=text, note='reason given after the button', source='ui')) + '\n')
            open(INBOX, 'a').write(json.dumps(dict(ts=now(), session=SESSION, text=f'[{sid} reason] {text}')) + '\n')
            broadcast(dict(type='chat', who='brian', text=text))
            return self._send(200, '{"ok":true}')
        if self.path == '/api/rerender':
            st = load()
            if st.get('working'): prerender(st['working'], f'{SDIR}/working')
            for sug in st['suggestions']: prerender(sug['green'], f"{SDIR}/{sug['id']}")
            return self._send(200, '{"ok":true}')
        if self.path == '/api/working': act_set_working(body['file']); return self._send(200, '{"ok":true}')
        return self._send(404, 'not found', 'text/plain')

# ---------- WebSocket (MuseScore panel) ---------------------------------------------------
async def ws_main():
    import websockets
    async def handler(ws):
        clients.add(ws)
        try:
            await ws.send(json.dumps(dict(type='state', **load())))
            async for raw in ws:
                try: m = json.loads(raw)
                except Exception: m = dict(type='message', text=raw)
                if m.get('type') == 'message': act_message(m.get('text', ''))
                elif m.get('type') == 'accept': act_verdict(m['id'], True, m.get('text', ''))
                elif m.get('type') == 'reject': act_verdict(m['id'], False, m.get('text', ''))
                elif m.get('type') == 'state': await ws.send(json.dumps(dict(type='state', **load())))
        finally:
            clients.discard(ws)
    async with websockets.serve(handler, '0.0.0.0', 8791):
        await asyncio.Future()

def main():
    global loop
    threading.Thread(target=watch_outbox, daemon=True).start()
    threading.Thread(target=midi_listen, daemon=True).start()
    threading.Thread(target=np_catch_up, daemon=True).start()
    threading.Thread(target=lambda: ThreadingHTTPServer(('0.0.0.0', 8790), H).serve_forever(), daemon=True).start()
    print(f'Scorewright server: http://localhost:8790  ws://localhost:8791  session={SESSION}  dir={SDIR}', flush=True)
    loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop)
    loop.run_until_complete(ws_main())

if __name__ == '__main__':
    main()
