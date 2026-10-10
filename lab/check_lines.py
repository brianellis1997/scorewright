"""Bar-duration check for hand-written answer lines ([b:i][V:k]...|...). Prints each voice
segment's length in eighths against the meter; exits 1 if any bar is off.
usage: python check_lines.py <lines.txt> <eighths_per_bar>"""
import re, sys
from fractions import Fraction as F
lines = [l.rstrip('\n') for l in open(sys.argv[1]) if l.strip()]
want = F(sys.argv[2])
units = {}
for spec in sys.argv[3:]:            # e.g. 4:3,4,6,7,10-19,24  (voices whose bar should total 4 units)
    tot, vs = spec.split(':'); 
    for part in vs.split(','):
        a, _, b = part.partition('-'); 
        for v in range(int(a), int(b or a) + 1): units[v] = F(tot)
TOK = re.compile(r'!([^!]*)!|"[^"]*"|\{[^}]*\}|\[[A-Zr]:[^\]]*\]|\((\d+)(?::(\d+))?(?::(\d+))?|\[([^\]]+)\]([\d/]*)|([_=^]*[A-Ga-gzx][,\']*)([\d/]*)|([<>])|(\))|(-)|(\s+)|(.)')
def dur(s):
    if not s: return F(1)
    if s.startswith('/'): return F(1, 2 ** len(s)) if set(s) == {'/'} else F(1, int(s[1:]))
    if '/' in s:
        a, b = s.split('/', 1); return F(int(a), int(b) if b else 2)
    return F(int(s))
bad = 0
for line in lines:
    mb = re.search(r'\[b:(\d+)\]', line); bar = int(mb.group(1)) + 1 if mb else '?'
    for seg in re.split(r'(?=\[V:\d+\])', line):
        mv = re.match(r'\[V:(\d+)\]', seg)
        if not mv: continue
        body = seg[mv.end():].rstrip('|')
        total = F(0); tup = None; broken = None; last = F(0)
        for m in TOK.finditer(body):
            if m.group(2):
                p, q, r = int(m.group(2)), m.group(3), m.group(4)
                q = int(q) if q else (3 if p in (2, 4, 8) else 2); r = int(r) if r else p
                tup = [F(q, p), r]; continue
            d = None
            if m.group(5) is not None: d = dur(m.group(6))
            elif m.group(7): d = dur(m.group(8))
            if d is None:
                if m.group(9):
                    broken = m.group(9)
                    total += last / 2 if broken == '>' else -last / 2   # the note before a > gets longer, before a < shorter
                continue
            if broken:
                d = d * F(3, 2) if broken == '<' else d * F(1, 2); broken = None
            if tup:
                d *= tup[0]; tup[1] -= 1
                if tup[1] == 0: tup = None
            total += d
            last = d
        exp = units.get(int(mv.group(1)), want)
        flag = '' if total == exp else '   <-- expected %s' % exp
        if flag: bad += 1
        print(f'bar {bar:>3} V:{mv.group(1)} {str(total):>5} eighths{flag}')
print('CHECK', 'FAIL' if bad else 'OK', bad, 'bad segments')
# octave-slip guard: an interval wider than an octave between neighbouring notes of one voice is almost always a case slip (B for b)
import re as _re
_STEP = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)
def _midi(tok):
    m = _re.match(r"[_^=]*([A-Ga-g])([,']*)", tok)
    if not m: return None
    p = _STEP[m.group(1).upper()] + (12 * 5 if m.group(1).islower() else 12 * 4)
    return p + 12 * m.group(2).count("'") - 12 * m.group(2).count(',')
for l in lines:
    for seg in _re.findall(r'\[V:(\d+)\]([^|]*)', l):
        body = _re.sub(r'"[^"]*"|![^!]*!|\[[^\]]*\]', ' ', seg[1])
        toks = [t for t in _re.findall(r"[_^=]*[A-Ga-g][,']*", body)]
        ms = [_midi(t) for t in toks]
        for a, b, ta, tb in zip(ms, ms[1:], toks, toks[1:]):
            if a is not None and b is not None and abs(a - b) > 12:
                print(f"WARN octave slip? {l[:8]} V:{seg[0]} {ta} -> {tb} ({abs(a-b)} semitones)")
sys.exit(1 if bad else 0)
