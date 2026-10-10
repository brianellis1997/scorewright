"""Listen page for an applied edit: green bands on the edited bars, verified on the final XML.
usage (whisperer env): python apply_page.py <tag> <lo> <hi> "<title>"
"""
import os, re, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import show, xmledit, ranges
from music21 import converter

tag, lo, hi, title = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
xml = open(f'{HERE}/apply_{tag}_final.xml').read()
parts = xmledit.parts(xml)
last = max(int(m) for m in re.findall(r'<measure number="(\d+)"', xml))
rows = []
for m in range(max(1, lo - 2), min(last, hi + 2) + 1):
    n = sum(1 for i, *_ in parts if any('<pitch>' in b for _, b in xmledit.measure_notes(xml, m, part=i)))
    rows.append(f'{m}:{n}')
print('parts with notes per bar:', ' '.join(rows))
s = converter.parse(xmledit.excerpt(xml, lo, hi, None)).toSoundingPitch()
viol = ranges.check(s)
print('range violations in the edited bars:', len(viol), viol[:5])
meta = json.load(open(f'{HERE}/apply_{tag}.json'))
ck = os.path.basename(os.environ.get('T2S_CKPT', 'combined checkpoint, step 18000'))
rat = (f"Request: {meta['instr']}<br>Bars {lo}-{hi} written by the edit model ({ck}). "
       f"Everything else is yours. Range violations in the edited bars: {len(viol)}.")
WANT = ['Flute 1', 'Oboe 1', 'Clarinet in Bb 1', 'Bassoon 1', 'Horn in F 1', 'Trumpet in Bb 1', 'Trombone 1',
        'Violin I', 'Violin II', 'Viola', 'Violoncello', 'Contrabass']
names = {n for _, _, n, *_ in parts}
want = [w for w in WANT if w in names] or None
whole = bool(os.environ.get('SW_WHOLE'))
html = show.build(xml, 1 if whole else max(1, lo - 4), last if whole else min(last, hi + 4), lo, title, rationale=rat, want=want)
out = f'{HERE}/sw_apply_{tag}.html'
open(out, 'w').write(html)
import shutil; shutil.copy(out, '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/' + os.path.basename(out))
print('PAGE http://localhost:8765/' + os.path.basename(out))
