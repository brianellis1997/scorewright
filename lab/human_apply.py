"""Splice hand-written (or frontier-LLM-written) answer lines into a score through the same
pipeline t2s_edit_apply uses after the model step. Lines use the [b:i][V:k]...| format.
usage: python human_apply.py <xml> <cut_at> <lo> <hi> <lines.txt> <tag> "<who wrote it>" """
import os, re, sys, json
import t2s_edit_apply as T
xml_path, cut, lo, hi, lines_path, tag, who = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5], sys.argv[6], sys.argv[7]
HERE = T.HERE
abc = T.score_to_reduced_abc(xml_path, f'{HERE}/apply_{tag}')
assert abc, 'conversion failed'
header, body, names = T.EF.parse_abc(abc)
body = body[:cut]
abc = '\n'.join(header + body) + '\n'
lines = [l.rstrip('\n') for l in open(lines_path) if l.strip()]
new_abc = T.splice_answer(abc, lines, 'continue')
x, rc = T.post.to_xml(re.sub(r'%\d+', '', new_abc), f'apply_{tag}')
out = f'{HERE}/apply_{tag}_final.xml'
try:
    T.splice.splice(xml_path, x, f'{HERE}/apply_{tag}_spliced.xml', keep_through=lo - 1)
    raw = open(f'{HERE}/apply_{tag}_spliced.xml').read()
    raw = re.sub(r'<print\b[^>]*/>', '', raw); raw = re.sub(r'<print\b[^>]*>.*?</print>', '', raw, flags=re.S)
    open(out, 'w').write(raw)
except Exception as e:
    print('splice into original failed, using the converted XML:', type(e).__name__, flush=True)
    open(out, 'w').write(open(x).read())
json.dump(dict(kind='continue', bars=[lo, hi], voices=sorted(names), instr=who, lines=lines), open(f'{HERE}/apply_{tag}.json', 'w'), indent=1)
print('APPLY_DONE', out)
