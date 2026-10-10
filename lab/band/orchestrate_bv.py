"""Bright Valley Exaltation Sketch, bars 18-81: Brian's two-stave orchestral sketch -> concert band.

The sketch has four voices: V1 right-hand melody/figures (L:1/8), V2 a second right-hand voice
(counter-line, L:1/8), V3 left-hand chords (L:1/4), V4 bass line (L:1/8). His own labels:
"probably trumpet" at the bar-18 pickup, "wind choir" at 22, "A" at 33, "B"/"serene" at 42.
This script assigns each sketch voice to band instruments section by section (chord tones split
so every wind and brass part is one line), scales V3 to eighth units, shifts octaves where the
instrument lives elsewhere, adds section dynamics, and writes concert-pitch lines. Transposition
to written pitch is done afterwards by orch_transpose.py.
"""
import re, sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NOTE = re.compile(r"(\^\^|__|\^|_|=)?([A-Ga-g])([,']*)")
FIELD = re.compile(r'(![^!]*!|"[^"]*"|\[[A-Zr]:[^\]]*\])')

# ---------- sketch -----------------------------------------------------------------------
sketch = {}
for line in open(os.path.join(HERE, 'sketch_18_81.txt')):
    m = re.match(r'\s*(\d+)\s+(.*)$', line.rstrip('\n'))
    if not m: continue
    bar = int(m.group(1)); segs = {}
    for seg in re.split(r'(?=\[V:\d+\])', m.group(2)):
        mv = re.match(r'\[V:(\d+)\]', seg)
        if mv: segs[int(mv.group(1))] = seg[mv.end():].rstrip('|')
    sketch[bar] = segs

# ---------- ABC helpers ------------------------------------------------------------------
def shift_oct(seg, n):
    if not n: return seg
    def rep(m):
        acc, l, o = m.group(1) or '', m.group(2), m.group(3)
        octv = (5 if l.islower() else 4) + o.count("'") - o.count(',') + n
        L = l.upper() if octv < 5 else l.lower()
        return acc + L + ("'" * (octv - 5) if octv >= 5 else ',' * (4 - octv))
    return ''.join(c if i % 2 else NOTE.sub(rep, c) for i, c in enumerate(FIELD.split(seg)))

def pitch(acc, l, o):
    return STEP[l.upper()] + (60 if l.isupper() else 72) + 12 * (o.count("'") - o.count(',')) + {'^': 1, '^^': 2, '_': -1, '__': -2, '=': 0, '': 0, None: 0}[acc]

def chord_note(seg, which):
    """replace every chord by one of its notes: 'top', 'mid', 'bot'."""
    def rep(m):
        notes = NOTE.findall(m.group(1))
        if not notes: return m.group(0)
        notes = sorted(notes, key=lambda t: pitch(*t))
        pick = {'top': notes[-1], 'bot': notes[0], 'mid': notes[len(notes) // 2] if len(notes) > 2 else notes[-1]}[which]
        return ''.join(pick) + m.group(2)
    return ''.join(c if i % 2 else re.sub(r'\[([^\]]+)\]([\d/]*)', rep, c) for i, c in enumerate(FIELD.split(seg)))

def scale2(seg):
    """L:1/4 -> L:1/8: double every duration."""
    def dur2(d):
        if d == '': return '2'
        if d == '/': return ''
        if d == '//': return '/'
        if '/' in d:
            a, b = d.split('/', 1); a = int(a or 1); b = int(b or 2)
            from fractions import Fraction as F
            v = F(a, b) * 2
            return '' if v == 1 else (str(v.numerator) if v.denominator == 1 else f'{v.numerator}/{v.denominator}')
        return str(int(d) * 2)
    def rep(m):
        return m.group(1) + dur2(m.group(2))
    return ''.join(c if i % 2 else re.sub(r"((?:\[[^\]]+\])|(?:(?:\^\^|__|\^|_|=)?[A-Ga-gzx][,']*))([\d/]*)", rep, c) for i, c in enumerate(FIELD.split(seg)))

def strip_dyn(seg):
    return re.sub(r'!(p|pp|mp|mf|f|ff|fff)!', '', seg)

# ---------- instruments (concert pitch) --------------------------------------------------
V = dict(picc=1, fl1=2, fl2=3, ob=4, bsn=5, cl1=6, cl2=7, cl3=8, bcl=9, asx1=10, asx2=11, tsx=12, bsx=13,
         tpt1=14, tpt2=15, tpt3=16, hn1=17, hn2=18, tbn1=19, tbn2=20, euph=21, tuba=22, timp=23, snare=24)
KEYS = {6: 'C', 7: 'C', 8: 'C', 9: 'C', 10: 'G', 11: 'G', 12: 'C', 13: 'G', 14: 'C', 15: 'C', 16: 'C', 17: 'F', 18: 'F'}

def src(bar, v): return sketch.get(bar, {}).get(v)

def v3(bar, which, oct=0):
    s = src(bar, 3)
    return shift_oct(chord_note(scale2(s), which), oct) if s else None
def v1(bar, which=None, oct=0):
    s = src(bar, 1)
    if s is None: return None
    return shift_oct(chord_note(s, which) if which else s, oct)
def v2(bar, oct=0):
    s = src(bar, 2)
    if not s: return None
    return shift_oct(chord_note(s, 'top').replace('x', 'z'), oct)
def v4(bar, oct=0):
    s = src(bar, 4); return shift_oct(s, oct) if s else None
def bass(bar, oct=0):
    """the bass line: V4 when written, else the bottom of the V3 chords."""
    return v4(bar, oct) or v3(bar, 'bot', oct)
def timp(bar):
    b = src(bar, 4) or (scale2(src(bar, 3)) if src(bar, 3) else None)
    if not b: return None
    m = NOTE.search(chord_note(b, 'bot'))
    if not m: return None
    note = shift_oct(''.join(m.groups('')), -1) if pitch(*m.groups('')) >= 53 else ''.join(m.groups(''))
    return f'{note}2 z2 z4'


def picc(bar):
    """piccolo an octave above the melody; two octaves where that would sit below its D5 bottom."""
    s = v1(bar, 'top', 1)
    if not s: return None
    ps = [pitch(*t) for t in NOTE.findall(''.join(c for i, c in enumerate(FIELD.split(s)) if i % 2 == 0))]
    if ps and min(ps) < 74:
        s2 = v1(bar, 'top', 2)
        ps2 = [pitch(*t) for t in NOTE.findall(''.join(c for i, c in enumerate(FIELD.split(s2)) if i % 2 == 0))]
        return s2 if max(ps2) <= 105 else None
    return s

RANGE = dict(picc=(74, 105), fl1=(59, 96), fl2=(59, 96), ob=(58, 91), bsn=(34, 75), cl1=(50, 91), cl2=(50, 91), cl3=(50, 91), bcl=(38, 77),
             asx1=(49, 81), asx2=(49, 81), tsx=(44, 76), bsx=(36, 69), tpt1=(52, 82), tpt2=(52, 82), tpt3=(52, 82), hn1=(41, 77), hn2=(41, 77),
             tbn1=(40, 70), tbn2=(40, 70), euph=(40, 70), tuba=(26, 58), timp=(38, 55), snare=(0, 127))
NAME = {v: k for k, v in V.items()}
KEYFLAT = {'B': -1, 'E': -1}                    # concert key Bb: unmarked B and E are flat
def kpitch(t):
    acc, l, o = t
    return pitch(acc, l, o) + (KEYFLAT.get(l.upper(), 0) if not acc else 0)
def fit(seg, v):
    """move a line by octaves until it sits inside the instrument's sounding range."""
    lo, hi = RANGE[NAME[v]]
    for _ in range(3):
        ps = [kpitch(t) for t in NOTE.findall(''.join(c for i, c in enumerate(FIELD.split(seg)) if i % 2 == 0))]
        if not ps: return seg
        if min(ps) < lo and max(ps) + 12 <= hi: seg = shift_oct(seg, 1)
        elif max(ps) > hi and min(ps) - 12 >= lo: seg = shift_oct(seg, -1)
        else: return seg
    return seg

def rhythm_of(seg):
    """the same rhythm on one unpitched line (snare): every note/chord becomes c, slurs and ties dropped."""
    def body(c):
        c = re.sub(r'\[[^\]]+\]([\d/]*)', r'c\1', c)
        c = re.sub(r"(?:\^\^|__|\^|_|=)?[A-Ga-g][,']*", 'c', c)
        return re.sub(r'\((?!\d)', '', c).replace(')', '').replace('-', '')
    return ''.join(c if i % 2 else body(c) for i, c in enumerate(FIELD.split(seg)))

def last_pitch(seg):
    ns = NOTE.findall(''.join(c for i, c in enumerate(FIELD.split(seg)) if i % 2 == 0))
    return kpitch(ns[-1]) if ns else None
def first_pitch(seg):
    ns = NOTE.findall(''.join(c for i, c in enumerate(FIELD.split(seg)) if i % 2 == 0))
    return kpitch(ns[0]) if ns else None
def continuous(prev, seg, v):
    """line continuity: if a part re-enters more than a sixth away from where it left off and an
    octave shift brings it closer while staying in range, shift the whole bar."""
    if not prev or not seg: return seg
    a, b = last_pitch(prev), first_pitch(seg)
    if a is None or b is None or abs(a - b) <= 9: return seg
    lo, hi = RANGE[NAME[v]]
    for n in (-1, 1):
        s2 = shift_oct(seg, n); b2 = first_pitch(s2)
        ps = [kpitch(t) for t in NOTE.findall(''.join(c for i, c in enumerate(FIELD.split(s2)) if i % 2 == 0))]
        if b2 is not None and abs(a - b2) < abs(a - b) and min(ps) >= lo and max(ps) <= hi:
            return s2
    return seg

# ---------- sections -----------------------------------------------------------------------
def section(bar):
    if bar == 18: return 'pickup'
    if 19 <= bar <= 21 or 59 <= bar <= 61: return 'fanfare'
    if 22 <= bar <= 27 or 62 <= bar <= 67: return 'windchoir'
    if bar in (28, 68): return 'handoff'
    if 29 <= bar <= 32 or 69 <= bar <= 72: return 'fanfare2'
    if 33 <= bar <= 40 or 73 <= bar <= 80: return 'tutti'
    if bar == 41: return 'link'
    if 42 <= bar <= 48: return 'serene'
    if bar == 49: return 'run'
    if 50 <= bar <= 57: return 'climax'
    if bar == 58: return 'hold'
    if bar == 81: return 'close'
    return 'rest'

DYN = dict(pickup='!f!', fanfare='!f!', windchoir='!p!', handoff='', fanfare2='!f!', tutti='!f!', link='!mf!', serene='!p!', run='', climax='!ff!', hold='', close='!f!')

def orchestrate(bar):
    sec = section(bar); out = {}
    if sec == 'pickup':
        out[V['cl1']] = "(6:4:6DA,F, A,DF D z/ z/ z2"
        out[V['tpt1']] = 'z4 z z/"^probably trumpet"!f! d/ .d.d'
        out[V['tpt2']] = 'z4 z z/!f! B/ .B.B'
        out[V['tbn1']] = "G,,2 z2 F,,2 z2"; out[V['tuba']] = "G,,,2 z2 F,,,2 z2"
    elif sec in ('fanfare', 'fanfare2'):
        out[V['tpt1']] = v1(bar, 'top'); out[V['tpt2']] = v2(bar) or v1(bar, 'bot')
        if v2(bar) and v1(bar, 'bot') != v1(bar, 'top'): out[V['tpt3']] = v1(bar, 'bot')
        else: out[V['tpt3']] = v3(bar, 'top')
        out[V['hn1']] = v3(bar, 'top'); out[V['hn2']] = v3(bar, 'bot')
        out[V['tbn1']] = v3(bar, 'mid'); out[V['tbn2']] = v3(bar, 'bot')
        out[V['euph']] = bass(bar); out[V['tuba']] = bass(bar, -1); out[V['timp']] = timp(bar)
        if sec == 'fanfare2':
            out[V['fl1']] = shift_oct(v1(bar, 'top'), 1); out[V['fl2']] = v1(bar, 'top'); out[V['picc']] = shift_oct(v1(bar, 'top'), 2)
            out[V['cl1']] = v1(bar, 'top'); out[V['cl2']] = v1(bar, 'bot')
    elif sec == 'windchoir':
        out[V['ob']] = v1(bar); out[V['cl1']] = v1(bar); out[V['fl2']] = shift_oct(v2(bar), 1) if v2(bar) else None; out[V['fl1']] = shift_oct(v1(bar), 1); out[V['cl2']] = v2(bar) or v3(bar, 'top')
        out[V['cl3']] = v3(bar, 'top'); out[V['asx1']] = v3(bar, 'top'); out[V['asx2']] = v3(bar, 'mid'); out[V['tsx']] = v3(bar, 'bot')
        out[V['bsn']] = bass(bar); out[V['bcl']] = bass(bar); out[V['bsx']] = bass(bar)
    elif sec == 'handoff':
        s = src(bar, 1)                       # "...) z/!f! [Dd]/ .[Dd].[Dd]" : winds finish, trumpets take the pickup
        head, tail = s.split('z/', 1)
        out[V['ob']] = head + 'z/ z/ z2'; out[V['cl1']] = head + 'z/ z/ z2'; out[V['fl1']] = shift_oct(head + 'z/ z/ z2', 1)
        out[V['tpt1']] = 'z4 z z/' + chord_note(tail, 'top'); out[V['tpt2']] = 'z4 z z/' + chord_note(tail, 'bot')
        out[V['fl2']] = v2(bar); out[V['cl2']] = v2(bar) or v3(bar, 'top')
        out[V['cl3']] = v3(bar, 'top'); out[V['asx1']] = v3(bar, 'top'); out[V['asx2']] = v3(bar, 'mid'); out[V['tsx']] = v3(bar, 'bot')
        out[V['bsn']] = bass(bar); out[V['bcl']] = bass(bar); out[V['bsx']] = bass(bar)
    elif sec in ('tutti', 'climax'):
        top, bot = v1(bar, 'top'), v1(bar, 'bot')
        out[V['fl1']] = shift_oct(top, 1); out[V['fl2']] = shift_oct(v2(bar) or bot, 1); out[V['picc']] = shift_oct(top, 2) if sec == 'climax' else picc(bar)
        out[V['ob']] = top; out[V['cl1']] = bot if sec == 'climax' else top; out[V['cl2']] = v2(bar) or v3(bar, 'top'); out[V['cl3']] = v3(bar, 'top')
        out[V['asx1']] = v2(bar) or v3(bar, 'top'); out[V['asx2']] = v3(bar, 'mid'); out[V['tsx']] = v3(bar, 'bot')
        out[V['bsx']] = bass(bar); out[V['bsn']] = bass(bar); out[V['bcl']] = bass(bar)
        out[V['tpt1']] = bot if sec == 'climax' else top; out[V['tpt2']] = v2(bar) or v3(bar, 'top'); out[V['tpt3']] = v3(bar, 'top')
        if sec == 'climax':
            out[V['hn1']] = v4(bar) or v3(bar, 'top'); out[V['hn2']] = v4(bar) or v3(bar, 'bot')
            out[V['tbn1']] = v4(bar) or v3(bar, 'mid'); out[V['tbn2']] = v4(bar) or v3(bar, 'bot')
        else:
            out[V['hn1']] = v3(bar, 'top'); out[V['hn2']] = v3(bar, 'bot'); out[V['tbn1']] = v3(bar, 'mid'); out[V['tbn2']] = v3(bar, 'bot')
        out[V['euph']] = bass(bar); out[V['tuba']] = bass(bar, -1); out[V['timp']] = timp(bar)
        if sec == 'tutti':                     # balance: the wind melody is f, brass accompaniment two steps under it
            for k in ('tpt2', 'tpt3', 'hn1', 'hn2', 'tbn1', 'tbn2'):
                if out.get(V[k]): out[V[k]] = '!mp! ' + out[V[k]]
            if out.get(V['tpt1']): out[V['tpt1']] = '!mf! ' + out[V['tpt1']]
    elif sec in ('link', 'close'):
        out[V['euph']] = chord_note(v2(bar), 'bot') if v2(bar) else None; out[V['tbn1']] = v3(bar, 'top'); out[V['tbn2']] = v3(bar, 'bot')
        out[V['tuba']] = v4(bar, -1); out[V['bsn']] = v4(bar); out[V['bcl']] = v4(bar); out[V['bsx']] = v4(bar); out[V['hn2']] = v3(bar, 'bot')
    elif sec == 'serene':
        out[V['fl1']] = shift_oct(v1(bar), 1); out[V['cl1']] = v3(bar, 'top'); out[V['cl2']] = v3(bar, 'mid'); out[V['cl3']] = v3(bar, 'bot')
        out[V['bsn']] = bass(bar, -1); out[V['bcl']] = bass(bar, -1)
    elif sec == 'run':
        for k in ('ob', 'cl1', 'cl2'): out[V[k]] = v1(bar)
        out[V['fl1']] = shift_oct(v1(bar), 1); out[V['fl2']] = shift_oct(v1(bar), 1); out[V['picc']] = shift_oct(v1(bar), 2)
        out[V['asx1']] = v3(bar, 'top'); out[V['asx2']] = v3(bar, 'mid'); out[V['tsx']] = v3(bar, 'bot'); out[V['bsn']] = bass(bar); out[V['bcl']] = bass(bar)
    elif sec == 'hold':
        hold_top, hold_bot = '[M:6/4]!>(! b8!p!!>)! z2 z2', '[M:6/4]!>(! d8!p!!>)! z2 z2'
        for k in ('picc', 'fl1', 'ob', 'cl1'): out[V[k]] = hold_top if k != 'picc' else shift_oct(hold_top, 1)
        for k in ('fl2', 'cl2', 'asx1'): out[V[k]] = hold_bot
        out[V['cl3']] = '[M:6/4]!>(! F8!p!!>)! z2 z2'; out[V['asx2']] = '[M:6/4]!>(! F8!p!!>)! z2 z2'; out[V['tsx']] = '[M:6/4]!>(! _B,8!p!!>)! z2 z2'
        low = '[M:6/4]' + v3(bar, 'top')
        out[V['tbn1']] = low; out[V['tbn2']] = '[M:6/4]' + v3(bar, 'bot'); out[V['euph']] = '[M:6/4]' + v3(bar, 'bot'); out[V['tuba']] = '[M:6/4]' + v3(bar, 'bot', -1)
        out[V['hn1']] = '[M:6/4]!>(! F8!p!!>)! z2 z2'; out[V['hn2']] = '[M:6/4]!>(! _B,8!p!!>)! z2 z2'
        out[V['bsn']] = '[M:6/4]!>(! _B,,8!p!!>)! z2 z2'; out[V['bcl']] = '[M:6/4]!>(! _B,,8!p!!>)! z2 z2'; out[V['bsx']] = '[M:6/4]!>(! _B,,8!p!!>)! z2 z2'
        out[V['tpt1']] = '[M:6/4] z8 z z/!f! d/ .d.d'; out[V['tpt2']] = '[M:6/4] z8 z z/!f! B/ .B.B'; out[V['tpt3']] = '[M:6/4] z12'
        out[V['timp']] = '[M:6/4]!>(! _B,,8!p!!>)! z2 z2'
    if sec in ('fanfare', 'fanfare2', 'link', 'close', 'climax') and bass(bar):
        for k in ('bsn', 'bcl', 'bsx'):
            if V[k] not in out: out[V[k]] = bass(bar)
    if sec in ('windchoir', 'handoff', 'serene', 'run') and v3(bar, 'top'):
        if V['hn1'] not in out: out[V['hn1']] = '!p! ' + v3(bar, 'top')
        if V['hn2'] not in out: out[V['hn2']] = '!p! ' + v3(bar, 'bot')
    if sec in ('pickup', 'fanfare', 'fanfare2', 'handoff', 'tutti', 'climax') and out.get(V['tpt1']):
        out[V['snare']] = rhythm_of(out[V['tpt1']])
    if sec == 'hold':
        out[V['snare']] = '[M:6/4] z8 z z/ c/ .c.c'
    return {v: fit(s, v) for v, s in out.items() if s}

prev_sec = None
lines = []
prev_out = {}
for bar in range(18, 82):
    sec = section(bar); out = orchestrate(bar)
    out = {v: continuous(prev_out.get(v), s_, v) for v, s_ in out.items()}
    prev_out = dict(out)
    if bar == 59:
        out = {v: (s if '[M:4/4]' in s else '[M:4/4]' + s) for v, s in out.items()}
        for v in range(1, 24):
            if v not in out: out[v] = '[M:4/4] z8'
    if sec != prev_sec and DYN.get(sec):
        for v in out:
            if not re.search(r'!(p|pp|mp|mf|f|ff)!', out[v]): out[v] = DYN[sec] + ' ' + out[v]
    prev_sec = sec
    if bar == 18:
        for v, k in KEYS.items():
            out[v] = f'[K:{k}]' + (out.get(v) or ' z8')
    for v in list(out):
        out[v] = out[v].replace('$', '')
        if v not in (V['tpt1'], V['fl1']): out[v] = re.sub(r'"\^[^"]*"', '', out[v])
        out[v] = re.sub(r'  +', ' ', out[v]).strip()
    lines.append(f'[b:{bar - 1}]' + ''.join(f'[V:{v}]{out[v]}|' for v in sorted(out)))
open(os.path.join(HERE, 'bv_band_concert.txt'), 'w').write('\n'.join(lines) + '\n')
print('wrote', len(lines), 'bars; example bar 33:'); print(lines[15][:700])
