"""Register a rendered suggestion with the running server.
usage: python sw_suggest.py <final.xml> <lo> <hi> "note" [lines.txt] [--plan S.dorico.json]
--plan: the Dorico steps for this change (lab/dorico_plan.py); they are saved beside the suggestion
as S<n>.dorico.json, and Brian's Accept runs them in his open Dorico project (sw_on_accept.py)."""
import sys, json, shutil, urllib.request
args = sys.argv[1:]
plan = None
if '--plan' in args:
    i = args.index('--plan'); plan = args[i + 1]; del args[i:i + 2]
body = dict(file=args[0], lo=int(args[1]), hi=int(args[2]), note=args[3], lines=(open(args[4]).read().split('\n') if len(args) > 4 else None))
r = urllib.request.urlopen(urllib.request.Request('http://localhost:8790/api/suggest', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}))
print(r.read().decode())
if plan:
    st = json.load(urllib.request.urlopen('http://localhost:8790/api/state'))
    sid = st['suggestions'][-1]['id']
    dst = f"/Users/bdogellis/Documents/Score Exports/_scorewright_out/session/{st['session']}/{sid}.dorico.json"
    shutil.copy(plan, dst)
    print(f'{sid}: Dorico plan saved, {len(json.load(open(plan))["steps"])} steps -> {dst}')
