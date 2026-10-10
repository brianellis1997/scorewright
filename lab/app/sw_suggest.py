"""Register a rendered suggestion with the running server.  usage: python sw_suggest.py <final.xml> <lo> <hi> "note" [lines.txt]"""
import sys, json, urllib.request
body = dict(file=sys.argv[1], lo=int(sys.argv[2]), hi=int(sys.argv[3]), note=sys.argv[4], lines=(open(sys.argv[5]).read().split('\n') if len(sys.argv) > 5 else None))
r = urllib.request.urlopen(urllib.request.Request('http://localhost:8790/api/suggest', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}))
print(r.read().decode())
