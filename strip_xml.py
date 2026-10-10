"""Strip MusicXML of everything with no musical meaning. ~47% of tokens, zero content lost.

Keeps: pitch, duration, ties, slurs, wedges, dynamics, pedal, words, metronome, key, mode, time,
clef, voice, staff, articulations, ornaments, tuplets, grace notes.
Drops: colors, fonts, engraving coordinates, page/system layout, stems, beams, per-note instrument
ids, <type> (redundant with <duration>), measure widths, print/placement hints, indentation.
"""
import re, sys, os

def strip(s):
    # Self-closing FIRST. `<print[\s\S]*?</print>` matches a self-closing `<print/>` as its opener
    # and then runs to the NEXT `</print>`, swallowing every barline, clef, repeat, ending and key
    # signature in between. Eagle Act 1 lost half its <mode> elements this way - the one field that
    # identifies the key. The negative lookahead makes the paired pattern skip self-closing tags.
    s = re.sub(r'<print[^>]*/>', '', s)
    s = re.sub(r'<print(?![^>]*/>)[\s\S]*?</print>', '', s)
    s = re.sub(r'\s*color="[^"]*"', '', s)
    s = re.sub(r'\s*font-(family|style|size|weight)="[^"]*"', '', s)
    s = re.sub(r'\s*(default|relative)-[xy]="[^"]*"', '', s)
    s = re.sub(r'\s*width="[^"]*"', '', s)
    s = re.sub(r'\s*(placement|valign|justify|halign|print-object|bezier-[a-z0-9]+|dir)="[^"]*"', '', s)
    s = re.sub(r'<stem>[^<]*</stem>', '', s)
    s = re.sub(r'<beam[^>]*>[^<]*</beam>', '', s)
    s = re.sub(r'<instrument[^>]*/>', '', s)
    s = re.sub(r'<type>[^<]*</type>', '', s)
    s = re.sub(r'<staff-details[^>]*/>|<staff-layout[\s\S]*?</staff-layout>', '', s)
    s = re.sub(r'<identification[\s\S]*?</identification>|<defaults[\s\S]*?</defaults>', '', s)
    s = re.sub(r'\n\s+', '\n', s)
    s = re.sub(r'\n{2,}', '\n', s)
    return s

if __name__ == '__main__':
    D = '/Users/bdogellis/Documents/Score Exports/MusicXML/'
    for fn in sys.argv[1:]:
        p = fn if os.path.exists(fn) else D + fn
        out = strip(open(p).read())
        dst = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/' + os.path.basename(p).replace('.musicxml', '.stripped.xml')
        open(dst, 'w').write(out)
        print(f'{os.path.basename(p)[:44]:<46} -> {dst}')
