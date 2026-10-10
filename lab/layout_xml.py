"""Give an exported MusicXML sane engraving defaults so Sibelius does not crunch it: staff size
from the staff count, page size, staff and system distances, and strip absolute default-x/y
positions from dynamics/words so Sibelius' Magnetic Layout places them instead of stacking them.
usage: python layout_xml.py <in.xml> <out.xml>"""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
x = open(src, encoding='utf-8').read()
n_parts = len(re.findall(r'<score-part id=', x))
# staff size in mm by staff count; tenths are 1/10 of a staff space, staff = 4 spaces
staff_mm = 7.0 if n_parts <= 2 else 6.5 if n_parts <= 4 else 5.5 if n_parts <= 12 else 4.6
mm_per_tenth = staff_mm / 40
page_w, page_h = (210, 297) if n_parts <= 8 else (297, 420)      # A4 else A3 for big scores
tenths = lambda mm: round(mm / mm_per_tenth)
defaults = f'''<defaults>
  <scaling><millimeters>{staff_mm:.2f}</millimeters><tenths>40</tenths></scaling>
  <page-layout><page-height>{tenths(page_h)}</page-height><page-width>{tenths(page_w)}</page-width>
    <page-margins type="both"><left-margin>{tenths(12)}</left-margin><right-margin>{tenths(12)}</right-margin><top-margin>{tenths(12)}</top-margin><bottom-margin>{tenths(12)}</bottom-margin></page-margins></page-layout>
  <system-layout><system-margins><left-margin>0</left-margin><right-margin>0</right-margin></system-margins><system-distance>{110 if n_parts > 8 else 130}</system-distance></system-layout>
  <staff-layout><staff-distance>{70 if n_parts > 8 else 90}</staff-distance></staff-layout>
</defaults>'''
x = re.sub(r'<defaults>.*?</defaults>', '', x, flags=re.S)
x = re.sub(r'(</identification>|</work>|<part-list>)', lambda m: (defaults + '\n' + m.group(1)) if m.group(1) == '<part-list>' else m.group(1), x, count=1) if '</identification>' not in x else x.replace('</identification>', '</identification>\n' + defaults, 1)
# absolute positions on directions/dynamics/words/wedges/pedal: drop them, keep placement above/below
x = re.sub(r'(<(?:words|dynamics|wedge|pedal|metronome|octave-shift|bracket)\b[^>]*?)\s+(?:default-x|default-y|relative-x|relative-y)="[^"]*"', r'\1', x)
x = re.sub(r'(<(?:words|dynamics|wedge|pedal|metronome|octave-shift|bracket)\b[^>]*?)\s+(?:default-x|default-y|relative-x|relative-y)="[^"]*"', r'\1', x)
x = re.sub(r'(<(?:words|dynamics|wedge|pedal|metronome|octave-shift|bracket)\b[^>]*?)\s+(?:default-x|default-y|relative-x|relative-y)="[^"]*"', r'\1', x)
open(dst, 'w', encoding='utf-8').write(x)
print('LAYOUT', dst, 'parts', n_parts, 'staff', staff_mm, 'mm, page', page_w, 'x', page_h)
