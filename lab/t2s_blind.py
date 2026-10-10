"""Morning blind test: verify each sample on the FINAL XML (pitched notes per bar), then publish
the pages under shuffled letters. The mapping goes to t2s_blind_key.json, never on a page.

usage (whisperer env): python t2s_blind.py stock_P1_48c_0 s1_P1_48c_0 s2_P1_48c_0 ...
"""
import os, re, sys, json, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, '/Users/bdogellis/repos/scorewright')
import xmledit, show
STR = ('Violin I', 'Violin II', 'Viola', 'Violoncello', 'Contrabass')
WANT = ['Flute 1', 'Oboe 1', 'Clarinet in Bb 1', 'Bassoon 1', 'Horn in F 1', 'Trumpet in Bb 1', 'Trombone 1',
        'Violin I', 'Violin II', 'Viola', 'Violoncello', 'Contrabass']


def pitched(x, m, i):
    return sum(1 for _, b in xmledit.measure_notes(x, m, part=i) if '<pitch>' in b)


def verify(tag):
    raw = open(f'{HERE}/t2s_{tag}_final.xml').read()
    parts = xmledit.parts(raw)
    last = max(int(m) for m in re.findall(r'<measure number="(\d+)"', raw))
    row, empty = [], 0
    for m in range(17, last + 1):
        n_parts = sum(1 for i, *_ in parts if pitched(raw, m, i) > 0)
        empty += n_parts == 0
        row.append(f'{m}:{n_parts}')
    return raw, last, ' '.join(row), empty


if __name__ == '__main__':
    tags = sys.argv[1:]
    letters = list('ABCDEFGH')[:len(tags)]
    random.shuffle(letters)
    key = {}
    for tag, L in zip(tags, letters):
        try:
            raw, last, row, empty = verify(tag)
        except Exception as e:
            print(f'{tag}: FAILED {type(e).__name__} {str(e)[:100]}', flush=True); continue
        print(f'{tag:20s} -> {L}   bars 17..{last} parts-with-notes: {row}   empty bars: {empty}', flush=True)
        html = show.build(raw, 13, last, 17, f'Blind {L}',
                          rationale='Bars 1-16 are yours. Bars 17 on: one of three models, same plan, same constraints. '
                                    'Which model is hidden until you judge.', want=WANT)
        open(f'{HERE}/sw_blind_{L}.html', 'w').write(html)
        key[L] = tag
    json.dump(key, open(f'{HERE}/t2s_blind_key.json', 'w'), indent=1)
    print('BLIND_READY', ' '.join(f'http://localhost:8765/sw_blind_{L}.html' for L in sorted(key)), flush=True)
