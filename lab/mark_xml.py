"""Sibelius ignores MusicXML note colour, so mark the suggested region with things it does import:
a bold text at the first edited bar and at the bar after the last, plus a bracket line spanning
the region. usage: python mark_xml.py <in.xml> <out.xml> <lo> <hi> ["label"]"""
import re, sys
src, dst, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
label = sys.argv[5] if len(sys.argv) > 5 else 'Scorewright suggestion'
x = open(src, encoding='utf-8').read()
def direction(words, extra=''):
    return f'<direction placement="above"><direction-type><words font-weight="bold" font-size="11" color="#0B8A3E">{words}</words></direction-type>{extra}</direction>'
def bracket(t):
    return f'<direction placement="above"><direction-type><bracket type="{t}" number="2" line-end="{"down" if t == "start" else "down"}" line-type="dashed" color="#0B8A3E"/></direction-type></direction>'
first_part_done = False
def fix(m):
    global first_part_done
    num = int(m.group(1)); head, body = m.group(2), m.group(3)
    if not first_part_done:
        if num == lo: body = direction(f'▶ {label}: bars {lo}-{hi}') + bracket('start') + body
        if num == hi: body = body + bracket('stop')
        if num == hi + 1: body = direction(f'◀ end of {label.lower()}') + body
    return f'<measure number="{num}"{head}>{body}</measure>'
parts = re.split(r'(<part id="[^"]+">)', x)
out = parts[0]
for i in range(1, len(parts), 2):
    seg = re.sub(r'<measure number="(\d+)"([^>]*)>(.*?)</measure>', fix, parts[i + 1], flags=re.S)
    out += parts[i] + seg
    first_part_done = True
open(dst, 'w', encoding='utf-8').write(out)
print('MARKED', dst, 'bars', lo, '-', hi)
