"""Last 11 PDFs via Verovio + Chrome print-to-PDF (MuseScore rejects them even laundered), and
the 2 MIDIs whose repeats music21 cannot expand (strip the repeat marks, then write)."""
import os, sys, warnings
warnings.simplefilter('ignore')
sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import verovio
from playwright.sync_api import sync_playwright
from music21 import converter, bar, repeat
SRC='/Users/bdogellis/Documents/Score Exports/MusicXML'
PDF='/Users/bdogellis/Documents/Score Exports/PDF'
MID='/Users/bdogellis/Documents/Score Exports/MIDI'

need_pdf=[f for f in sorted(os.listdir(SRC)) if f.endswith('.musicxml')
          and not os.path.exists(f'{PDF}/{f[:-9]}.pdf')]
need_mid=[f for f in sorted(os.listdir(SRC)) if f.endswith('.musicxml')
          and not os.path.exists(f'{MID}/{f[:-9]}.mid')]
print(f'pdf: {len(need_pdf)}  mid: {len(need_mid)}', flush=True)

with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    pg=b.new_page()
    for f in need_pdf:
        try:
            tk=verovio.toolkit()
            tk.setOptions({'scale':40,'breaks':'auto','pageWidth':2100,'pageHeight':2970,
                           'footer':'none'})
            tk.loadData(open(f'{SRC}/{f}').read())
            pages=''.join(f'<div style="page-break-after:always">{tk.renderToSVG(i)}</div>'
                          for i in range(1, tk.getPageCount()+1))
            pg.set_content(f'<html><body style="margin:0">{pages}</body></html>')
            pg.pdf(path=f'{PDF}/{f[:-9]}.pdf', format='A4', print_background=True)
            print(f'  pdf ok: {f} ({tk.getPageCount()} pages)', flush=True)
        except Exception as e:
            print(f'  pdf FAIL: {f}: {str(e)[:80]}', flush=True)
    b.close()

for f in need_mid:
    try:
        s=converter.parse(f'{SRC}/{f}')
        for el in list(s.recurse().getElementsByClass((repeat.RepeatMark, bar.Repeat))):
            el.activeSite.remove(el)
        s.toSoundingPitch().write('midi', fp=f'{MID}/{f[:-9]}.mid')
        print(f'  mid ok (repeats stripped, plays once through): {f}', flush=True)
    except Exception as e:
        print(f'  mid FAIL: {f}: {str(e)[:80]}', flush=True)
print('FINAL11 DONE', flush=True)
