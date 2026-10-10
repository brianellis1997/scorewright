"""Re-render every Text2Score sample with inline %N comments stripped, then verify the OBJECT:
pitched notes per bar in the final MusicXML the page plays, not the ABC the model wrote."""
import os, re, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import post, splice, xmledit, show
ORIG = '/Users/bdogellis/Documents/Score Exports/MusicXML/Orchestral Idea.musicxml'
STR = ('Violin I', 'Violin II', 'Viola', 'Violoncello', 'Contrabass')
WANT = ['Flute 1', 'Oboe 1', 'Clarinet in Bb 1', 'Bassoon 1', 'Horn in F 1', 'Trumpet in Bb 1', 'Trombone 1',
        'Violin I', 'Violin II', 'Viola', 'Violoncello', 'Contrabass']


def pitched(x, m, i):
    return sum(1 for _, b in xmledit.measure_notes(x, m, part=i) if '<pitch>' in b)


def redo(tag, title):
    t = open(f'{HERE}/t2s_{tag}.abc').read()
    t = re.sub(r'%\d+', '', t)
    x, rc = post.to_xml(t, f't2s_{tag}_fixed')
    splice.splice(ORIG, x, f'{HERE}/t2s_{tag}_spliced.xml', keep_through=16)
    raw = open(f'{HERE}/t2s_{tag}_spliced.xml').read()
    raw = re.sub(r'<print\b[^>]*/>', '', raw)
    raw = re.sub(r'<print\b[^>]*>.*?</print>', '', raw, flags=re.S)
    open(f'{HERE}/t2s_{tag}_final.xml', 'w').write(raw)
    parts = xmledit.parts(raw)
    idx = {n: i for i, _p, n, _a, _b in parts}
    last = max(int(m) for m in re.findall(r'<measure number="(\d+)"', raw))
    row = []
    for m in range(17, last + 1):
        n_parts = sum(1 for i, _p, n, _a, _b in parts if pitched(raw, m, i) > 0)
        s = sum(pitched(raw, m, idx[n]) for n in STR)
        row.append(f'{m}:{n_parts}/{s}')
    print(f'{tag:12s} bars 17..{last}  parts-with-notes/string-notes: ' + ' '.join(row), flush=True)
    plan = open(f"{HERE}/t2s_plan_{tag.split('_')[0].rstrip('c')}.txt").read()
    rat = ('Bars 1-16 are yours, byte for byte. Bars 17 on were written by Text2Score. Plan given:\n\n' + plan)
    html = show.build(raw, 13, last, 17, title, rationale=rat.replace('\n', '<br>'), want=WANT)
    open(f'{HERE}/sw_t2s_{tag}.html', 'w').write(html)


if __name__ == '__main__':
    for tag, title in [('P1_48c_2', 'constrained + must-play, sample 2 (re-rendered)'),
                       ('P1_48c_1', 'constrained, piece continues, sample 1 (re-rendered)'),
                       ('P1c_1', 'constrained, sample 1 (re-rendered)'),
                       ('P1c_0', 'constrained, sample 0 (re-rendered)'),
                       ('P1_0', 'soft plan only (re-rendered)'),
                       ('P0_0', 'control, no plan (re-rendered)')]:
        try:
            redo(tag, 'Text2Score, ' + title)
        except Exception as e:
            print(f'{tag}: FAILED {type(e).__name__} {str(e)[:150]}', flush=True)
    print('REASSEMBLE_DONE')
