"""Set the session's working score.  usage: python sw_working.py <score.musicxml>"""
import sys, json, urllib.request
r = urllib.request.urlopen(urllib.request.Request('http://localhost:8790/api/working', data=json.dumps(dict(file=sys.argv[1])).encode(), headers={'Content-Type': 'application/json'}))
print(r.read().decode())
