"""Tint the notes of bars lo..hi green in a MusicXML file so a score editor shows what the model
wrote (MuseScore, Sibelius and Dorico all honour the MusicXML note color attribute).
usage: python color_xml.py <in.xml> <out.xml> <lo> <hi> [#hex]"""
import re, sys
src, dst, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
col = sys.argv[5] if len(sys.argv) > 5 else '#0B8A3E'
xml = open(src, encoding='utf-8').read()
def tint(m):
    num = int(m.group(1))
    body = m.group(2)
    if lo <= num <= hi:
        body = re.sub(r'<note(?![^>]*\bcolor=)', f'<note color="{col}"', body)
        body = re.sub(r'<rest(?![^>]*\bcolor=)(/?)>', f'<rest color="{col}"\\1>', body)
    return f'<measure number="{num}"{m.group(3)}>{body}</measure>'
out, n = re.subn(r'<measure number="(\d+)"([^>]*)>(.*?)</measure>', lambda m: tint(type('M', (), {'group': lambda self, i, m=m: (m.group(1), m.group(3), m.group(2))[i - 1]})()), xml, flags=re.S)
open(dst, 'w', encoding='utf-8').write(out)
print('COLORED', dst, 'measures processed', n, 'green notes', out.count(f'color="{col}"'))
