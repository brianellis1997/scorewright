"""ABC -> MusicXML, with the two round-trip bugs that silently destroy the result.

1. rest_unreduce needs `calculate_bartext_duration` IN SCOPE. Without it every bar-duration lookup
   fails inside a bare `except`, `ref_dur` is never assigned, and it dies on the first bar. The
   failure message names the wrong thing entirely.
2. An EMPTY bracket group in the %%score line (here the percussion staff, written as `[ ]`) breaks
   abc2xml's part mapping and it SILENTLY DROPS every voice after it. That is how all five string
   parts vanished from the first render without a single warning.
"""
import re, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(f'{HERE}/NotaGen/inference/inference.py').read()
_fn = src[src.index('def rest_unreduce'):src.index('def inference_patch')]
from abctoolkit.utils import Barline_regexPattern, Exclaim_re, Quote_re, SquareBracket_re
from abctoolkit.duration import calculate_bartext_duration
_ns = {'re': re, 'Barline_regexPattern': Barline_regexPattern, 'Exclaim_re': Exclaim_re,
       'Quote_re': Quote_re, 'SquareBracket_re': SquareBracket_re,
       'calculate_bartext_duration': calculate_bartext_duration}
exec(_fn, _ns)


def to_xml(abc_text, out_stem):
    lines = [l + '\n' for l in abc_text.split('\n') if l.strip()]
    lines = _ns['rest_unreduce'](lines)
    t = ''.join(lines)
    head, rest = t.split('\n', 1)
    t = re.sub(r'\[\s*\]\s*', '', head) + '\n' + rest
    p = f'{HERE}/{out_stem}.abc'
    open(p, 'w').write(t)
    r = subprocess.run([sys.executable, '-W', 'ignore', f'{HERE}/NotaGen/data/abc2xml.py',
                        '-o', HERE, p], capture_output=True)
    return f'{HERE}/{out_stem}.xml', r.returncode


if __name__ == '__main__':
    x, rc = to_xml(open(f'{HERE}/oi_full.abc').read(), 'oi_long')
    print('rc', rc, '->', x)
