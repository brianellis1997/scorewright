"""One-line verdict logging: python log_verdict.py <tag> <score 0-5> "<verdict as he said it>" ["<task>"]
Stores the triple (suggestion lines + rendered score + his words) so it is training data."""
import sys, json, os, shutil, datetime
B = '/Users/bdogellis/Documents/Score Exports/_bridge'; L = os.path.dirname(os.path.abspath(__file__))
tag, score, verdict = sys.argv[1], int(sys.argv[2]), sys.argv[3]
task = sys.argv[4] if len(sys.argv) > 4 else ''
os.makedirs(f'{B}/suggestions', exist_ok=True)
meta = {}
if os.path.exists(f'{L}/apply_{tag}.json'): meta = json.load(open(f'{L}/apply_{tag}.json'))
if os.path.exists(f'{L}/apply_{tag}_final.xml'): shutil.copy(f'{L}/apply_{tag}_final.xml', f'{B}/suggestions/{tag}.musicxml')
rec = dict(ts=datetime.datetime.now().isoformat(timespec='minutes'), test=tag, task=task or meta.get('instr', ''), bars=meta.get('bars'),
           suggestion_lines=meta.get('lines'), score_file=f'suggestions/{tag}.musicxml', verdict=verdict, score=score)
open(f'{B}/verdicts.jsonl', 'a').write(json.dumps(rec) + '\n')
print('logged', tag, score, '| total', sum(1 for _ in open(f'{B}/verdicts.jsonl')))
