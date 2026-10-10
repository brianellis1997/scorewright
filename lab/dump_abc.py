"""Print a score's rest-reduced ABC through the same converter the pipeline uses.
usage: python dump_abc.py <xml> <tag>"""
import sys
import t2s_edit_apply as T
abc = T.score_to_reduced_abc(sys.argv[1], f'{T.HERE}/apply_{sys.argv[2]}')
header, body, names = T.EF.parse_abc(abc)
print('\n'.join(header)); print('voices:', names)
for i, l in enumerate(body, 1): print(f'{i:4d}  {l}')
