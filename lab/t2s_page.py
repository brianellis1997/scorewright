"""Final spliced XML -> the listen-and-judge page (green bands on the new bars, per-bar seek,
accept/reject/free-text). Runs under the whisperer env because show.py needs music21 + verovio.

usage: python t2s_page.py <tag> [title]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import show

tag = sys.argv[1]
title = sys.argv[2] if len(sys.argv) > 2 else f'Text2Score {tag}'
xml = open(f'{HERE}/t2s_{tag}_final.xml').read()
WANT = ['Flute 1', 'Oboe 1', 'Clarinet in Bb 1', 'Bassoon 1', 'Horn in F 1', 'Trumpet in Bb 1', 'Trombone 1',
        'Violin I', 'Violin II', 'Viola', 'Violoncello', 'Contrabass']
plan = open(f"{HERE}/t2s_plan_{tag.split('_')[0].rstrip('c')}.txt").read()
rat = ('Bars 1-16 are yours, byte for byte. Bars 17-32 were written by Text2Score (NotaGen architecture plus a '
       'per-measure plan). The plan it was given:\n\n' + plan)
html = show.build(xml, 13, 32, 17, title, rationale=rat.replace('\n', '<br>'), want=WANT)
out = f'{HERE}/sw_t2s_{tag}.html'
open(out, 'w').write(html)
print('PAGE', out, 'http://localhost:8765/' + os.path.basename(out))
