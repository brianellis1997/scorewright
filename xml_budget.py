"""Where does MusicXML spend its tokens? Measured by stripping one category at a time."""
import re, os, sys, random
import tiktoken
enc = tiktoken.get_encoding('cl100k_base')
D = '/Users/bdogellis/Documents/Score Exports/MusicXML/'

STRIP = [
 ('color attributes',        lambda s: re.sub(r'\s*color="[^"]*"', '', s)),
 ('font-* attributes',       lambda s: re.sub(r'\s*font-(family|style|size|weight)="[^"]*"', '', s)),
 ('engraving coords',        lambda s: re.sub(r'\s*(default|relative)-[xy]="[^"]*"', '', s)),
 ('<print>/layout blocks',   lambda s: re.sub(r'<print[\s\S]*?</print>|<print[^>]*/>', '', s)),
 ('stem/beam',               lambda s: re.sub(r'<stem>[^<]*</stem>|<beam[^>]*>[^<]*</beam>', '', s)),
 ('<instrument .../>',       lambda s: re.sub(r'<instrument[^>]*/>', '', s)),
 ('<type> (dur is enough)',  lambda s: re.sub(r'<type>[^<]*</type>', '', s)),
 ('measure width=',          lambda s: re.sub(r'\s*width="[^"]*"', '', s)),
 ('placement/valign/justify',lambda s: re.sub(r'\s*(placement|valign|justify|halign|print-object|number)="[^"]*"', '', s)),
 ('xml indentation',         lambda s: re.sub(r'\n\s+', '\n', s)),
]

files = sys.argv[1:] or ['Briello no 36 in D# minor.musicxml', '9 16 String Quartet.musicxml',
                         'Gettysburg Symphony Day 1.musicxml']
for fn in files:
    s = open(D + fn).read()
    base = len(enc.encode(s))
    print(f'\n{fn[:48]}   {base:,} tokens')
    cur, run = s, base
    for name, fn2 in STRIP:
        cur = fn2(cur)
        n = len(enc.encode(cur))
        print(f'   -{name:<26} {run-n:>8,} tok  ({100*(run-n)/base:>4.1f}%)   running: {n:,}')
        run = n
    print(f'   {"=> after all strips":<28} {run:>8,} tok  ({100*run/base:.1f}% of original)')
