"""Blind A/B: Brian's fine-tuned model vs the SAME architecture before his corpus.

The clean comparison is pre/post fine-tune of the identical 110M checkpoint - not NotaGen-X,
which differs in size and training. Same prompt (Orchestral Idea bars 8-16), same sampling
(temp 0.9, 6 bars), FIRST VALID sample per model rather than best-of-N, so no taste of mine
filters the comparison. Order on the page is randomized; the mapping is written here, never
shown on the page.
"""
import json, os, random, re, sys, time, warnings
warnings.simplefilter('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import notagen_arm as NA
import post, splice

MODELS = '/Users/bdogellis/Documents/Score Exports/_models/'
STOCK = MODELS + 'weights_notagen_pretrain_p_size_16_p_length_2048_p_layers_12_c_layers_3_h_size_768_lr_0.0002_batch_8.pth'
BRIAN = MODELS + 'weights_notagen_brian_small.pth'
SRC = '/Users/bdogellis/Documents/Score Exports/abc_augmented/Bb/Orchestral Idea_Bb.abc'
ORIG = '/Users/bdogellis/Documents/Score Exports/MusicXML/Orchestral Idea.musicxml'

lines = [l for l in open(SRC).read().split('\n') if l.strip()]
bi = [i for i, l in enumerate(lines) if l.startswith('[V:')]
head, body = lines[:bi[0]], [lines[j] for j in bi]
prefix = '\n'.join(head + body[-9:]) + '\n'


def valid(gen):
    bars = [l for l in gen.split('\n') if l.strip()]
    return len(bars) >= 4


def sample(path, tag):
    m, p = NA.load(path, layers=12, hidden=768, char_layers=3, patch_length=2048)
    print(f'{tag} loaded', flush=True)
    for i in range(4):
        t0 = time.time()
        gen = NA.continue_abc(m, p, prefix, n_bars=6, temperature=0.9)
        print(f'  {tag} try {i}: {len([l for l in gen.split(chr(10)) if l.strip()])} bars '
              f'{time.time()-t0:.0f}s', flush=True)
        if valid(gen):
            full = re.sub(r'\[r:\d+/\d+\]', '', '\n'.join(head + body) + '\n' + gen)
            try:
                x, rc = post.to_xml(full, f'h2h_{tag}')
                a, f2, last = splice.splice(ORIG, x, f'{HERE}/h2h_{tag}_spliced.xml')
                raw = open(f'{HERE}/h2h_{tag}_spliced.xml').read()
                raw = re.sub(r'<print\b[^>]*/>', '', raw)
                raw = re.sub(r'<print\b[^>]*>.*?</print>', '', raw, flags=re.S)
                from music21 import converter
                s = converter.parse_data if False else None
                open(f'{HERE}/h2h_{tag}_final.xml', 'w').write(raw)
                return f'{HERE}/h2h_{tag}_final.xml', gen
            except Exception as e:
                print(f'  {tag} assembly failed: {type(e).__name__} {str(e)[:80]}', flush=True)
    return None, None


if __name__ == '__main__':
    del sys.modules['notagen_arm']
    import notagen_arm as NA2
    globals()['NA'] = NA2
    xa, ga = sample(STOCK, 'stock')
    xb, gb = sample(BRIAN, 'brian')
    order = random.sample(['stock', 'brian'], 2)
    json.dump({'v1': order[0], 'v2': order[1]}, open(f'{HERE}/h2h_key.json', 'w'))
    print('DONE H2H', xa, xb, 'order hidden in h2h_key.json', flush=True)
