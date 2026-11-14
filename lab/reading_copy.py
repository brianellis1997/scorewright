"""A copy of a big score for reading as pages (engrave_pages.py): every part at concert pitch (written
pitch moved by its <transpose>, octave transpositions kept as written), parts that never play
dropped, and bars after the last note cut.
usage (whisperer env): python reading_copy.py <score.xml> <out.xml> [first_bar last_bar]"""
import re, sys

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from dorico_plan import shift  # noqa: E402

src, dst = sys.argv[1], sys.argv[2]
x = open(src).read()
lo = int(sys.argv[3]) if len(sys.argv) > 4 else 1
hi = int(sys.argv[4]) if len(sys.argv) > 4 else None

parts = re.findall(r'<part id="([^"]+)">(.*?)</part>', x, re.S)
playing = [pid for pid, body in parts if '<pitch>' in body]
if hi is None:
    hi = max(int(n) for pid, body in parts if pid in playing
             for n, m in re.findall(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', body, re.S) if '<pitch>' in m)


def concert(body):
    t = re.search(r'<transpose\b[^>]*>.*?</transpose>', body, re.S)
    if not t:
        return body
    g = lambda tag: int(m.group(1)) if (m := re.search(rf'<{tag}>(-?\d+)</{tag}>', t.group(0))) else 0
    d, c = g('diatonic'), g('chromatic')
    if d == 0 and c == 0:
        return body

    def one(m):
        p = shift((m.group(1), int(m.group(2) or 0), int(m.group(3))), d, c)
        return f'<pitch><step>{p[0]}</step>' + (f'<alter>{p[1]}</alter>' if p[1] else '') + f'<octave>{p[2]}</octave></pitch>'
    body = re.sub(r'<pitch>\s*<step>(\w)</step>\s*(?:<alter>(-?\d+)</alter>\s*)?<octave>(\d+)</octave>\s*</pitch>', one, body)
    body = re.sub(r'<accidental>[^<]*</accidental>', '', body)
    body = re.sub(r'<transpose\b[^>]*>.*?</transpose>', '', body, flags=re.S)
    return re.sub(r'<fifths>-?\d+</fifths>', '<fifths>0</fifths>', body)


def cut(body):
    first = re.search(r'<attributes>.*?</attributes>', body, re.S)

    def keep(m):
        n = int(m.group(1))
        if n == lo and lo > 1 and first:
            return m.group(0).replace('>', '>' + first.group(0), 1)
        return m.group(0) if lo <= n <= hi else ''
    return re.sub(r'<measure number="(\d+)"[^>]*>.*?</measure>\s*', keep, body, flags=re.S)


out = x
for pid, body in parts:
    out = out.replace(f'<part id="{pid}">{body}</part>', f'<part id="{pid}">{cut(concert(body))}</part>' if pid in playing else '')
for pid, _ in parts:
    if pid not in playing:
        out = re.sub(rf'<score-part id="{pid}">.*?</score-part>\s*', '', out, flags=re.S)
open(dst, 'w').write(out)
print(f'{len(playing)} of {len(parts)} parts play; bars {lo}-{hi}')
