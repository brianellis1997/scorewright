"""Sibelius' MusicXML import ignores <pedal type="change"/> (a retake), so a pedal line with retakes
comes back as one unbroken pedal. Rewrite every retake as a release followed by a new press so
the score shows and plays the pedal the way it was written.
usage: python fix_pedal.py <in.xml> <out.xml>"""
import re, sys
x = open(sys.argv[1], encoding='utf-8').read()
n = 0
def rep(m):
    global n; n += 1
    attrs = m.group(1)
    keep = ' '.join(a for a in re.findall(r'\S+="[^"]*"', attrs) if not a.startswith(("type=", "line=")))
    return f'<pedal {keep} type="stop"/></direction-type></direction><direction placement="below"><direction-type><pedal {keep} type="start" line="yes"/>'
x2 = re.sub(r'<pedal([^>]*?)type="change"([^>]*?)/>', lambda m: rep(type('M', (), {'group': lambda self, i, m=m: m.group(1) + m.group(2)})()), x)
open(sys.argv[2], 'w', encoding='utf-8').write(x2)
print('PEDAL_FIXED retakes rewritten as release+press:', n)
