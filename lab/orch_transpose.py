"""Concert-pitch ABC lines -> written-pitch lines per voice, using the score header's transpose=
and each voice's key signature (inline [K:] seen in the score or the global K:). Accidentals in the
input are ABSOLUTE (every altered note carries ^ _ or =, unmarked = natural). Output uses the
normal ABC convention: key signature implied, accidentals only where needed, carried through the bar.
usage: python orch_transpose.py <reduced_score.txt from dump_abc.py> <concert_lines.txt> <out_lines.txt>"""
import re, sys
STEP = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
NAMES_SHARP = ['C', '^C', 'D', '^D', 'E', 'F', '^F', 'G', '^G', 'A', '^A', 'B']
NAMES_FLAT = ['C', '_D', 'D', '_E', 'E', 'F', '_G', 'G', '_A', 'A', '_B', 'B']
KEYSIG = {'C': {}, 'G': {'F': 1}, 'D': {'F': 1, 'C': 1}, 'A': {'F': 1, 'C': 1, 'G': 1}, 'E': {'F': 1, 'C': 1, 'G': 1, 'D': 1},
          'F': {'B': -1}, 'Bb': {'B': -1, 'E': -1}, 'Eb': {'B': -1, 'E': -1, 'A': -1}, 'Ab': {'B': -1, 'E': -1, 'A': -1, 'D': -1}}
KEYED = '--keyed' in sys.argv
sys.argv = [a for a in sys.argv if a != '--keyed']
hdr_text = open(sys.argv[1]).read()
gkey = re.search(r'^K:(\S+)', hdr_text, re.M).group(1)
trans, vkey = {}, {}
for line in hdr_text.split('\n'):
    mv = re.match(r'^V:(\d+)\b', line)
    if mv:
        mt = re.search(r'transpose=(-?\d+)', line)
        trans[int(mv.group(1))] = -int(mt.group(1)) if mt else 0
for m in re.finditer(r'\[V:(\d+)\]\[K:([A-G][b#]?)\]', hdr_text):
    vkey.setdefault(int(m.group(1)), m.group(2))
flat_keys = {'F', 'Bb', 'Eb', 'Ab', 'Db'}
NOTE = re.compile(r"(\^\^|__|\^|_|=)?([A-Ga-g])([,']*)")
def midi(acc, letter, octs):
    base = STEP[letter.upper()] + (60 if letter.isupper() else 72) + 12 * (octs.count("'") - octs.count(','))
    return base + {'^': 1, '^^': 2, '_': -1, '__': -2, '=': 0, None: 0}[acc]
LETTERS = 'CDEFGAB'
DEG = [0, 1, 1, 2, 2, 3, 3, 4, 5, 5, 6, 6, 7, 8, 8, 9]          # semitones -> letter steps (M2=1, P5=4, P8=7, M9=8)
def spell_by_letter(letter, octs, m_written, shift):
    """keep the letter arithmetic of the interval: concert E up a major second is F sharp, not G flat."""
    li = LETTERS.index(letter.upper()); steps = DEG[shift] if 0 <= shift < len(DEG) else round(shift * 7 / 12)
    oct_in = (5 if letter.islower() else 4) + octs.count("'") - octs.count(',')
    li2 = li + steps; oct2 = oct_in + li2 // 7; li2 %= 7
    natural = STEP[LETTERS[li2]] + 12 * (oct2 + 1)
    alt = m_written - natural
    if abs(alt) > 2:
        return spell(m_written, None)
    acc = {2: '^^', 1: '^', 0: '', -1: '_', -2: '__'}[alt]
    wl = LETTERS[li2]; wl = wl.lower() if oct2 >= 5 else wl
    wo = "'" * (oct2 - 5) if oct2 >= 5 else ',' * (4 - oct2)
    return acc, wl, wo
def spell(m, key, prefer_sharp=False):
    names = NAMES_SHARP if prefer_sharp else NAMES_FLAT
    pc = m % 12; octave = m // 12 - 1
    nm = names[pc]; acc = nm[0] if nm[0] in '^_' else ''; letter = nm[-1]
    if octave >= 5: letter = letter.lower(); octs = "'" * (octave - 5)
    else: octs = ',' * (4 - octave)
    return acc, letter, octs
def convert_segment(seg, shift, key):
    ks = KEYSIG.get(key, {})
    state = {}
    in_ks = KEYSIG.get(gkey, {}) if KEYED else {}
    in_state = {}
    def rep(m):
        acc, letter, octs = m.group(1), m.group(2), m.group(3)
        if KEYED:                                   # input written with the concert key signature and bar carry
            k = (letter.upper(), octs)
            if acc is None:
                alt_in = in_state.get(k, in_ks.get(letter.upper(), 0))
            else:
                alt_in = {'^': 1, '^^': 2, '_': -1, '__': -2, '=': 0}[acc]; in_state[k] = alt_in
            p = midi(None, letter, octs) + alt_in + shift
        else:
            p = midi(acc, letter, octs) + shift
        wacc, wl, wo = spell_by_letter(letter, octs, p, shift) if shift >= 0 else spell(p, key)
        alt = {'^^': 2, '^': 1, '_': -1, '__': -2, '': 0}[wacc]
        cur = state.get((wl.upper(), wo), ks.get(wl.upper(), 0))
        out = ''
        if alt != cur:
            out = {2: '^^', 1: '^', -1: '_', -2: '__', 0: '='}[alt]
            state[(wl.upper(), wo)] = alt
        return out + wl + wo
    return NOTE.sub(rep, seg)
out = []
for line in open(sys.argv[2]):
    line = line.rstrip('\n')
    if not line.strip(): continue
    parts = re.split(r'(?=\[V:\d+\])', line)
    res = parts[0]
    for seg in parts[1:]:
        v = int(re.match(r'\[V:(\d+)\]', seg).group(1))
        key = vkey.get(v, gkey); shift = trans.get(v, 0)
        body = seg[len(f'[V:{v}]'):]
        body = seg[len(f'[V:{v}]'):]
        chunks = re.split(r'(![^!]*!|"[^"]*"|\[[A-Zr]:[^\]]*\])', body)
        res += f'[V:{v}]' + ''.join(c if i % 2 else convert_segment(c, shift, key) for i, c in enumerate(chunks))
    out.append(res)
open(sys.argv[3], 'w').write('\n'.join(out) + '\n')
print('TRANSPOSED', len(out), 'lines; voices:', {v: (trans.get(v, 0), vkey.get(v, gkey)) for v in sorted(set(trans) | set(vkey))})
