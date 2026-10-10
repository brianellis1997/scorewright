"""Claude's reply into the Scorewright chat.  usage: python sw_say.py "text" [session] [--working]
--working marks the reply as an acknowledgment of work in progress: the page then shows "Claude is
working on it" with the elapsed minutes until the next suggestion or reply."""
import sys, json, datetime
B = '/Users/bdogellis/Documents/Score Exports/_bridge/queue/outbox.jsonl'
args = [a for a in sys.argv[1:] if a != '--working']
rec = dict(ts=datetime.datetime.now().isoformat(timespec='seconds'), session=args[1] if len(args) > 1 else 'current', text=args[0])
if '--working' in sys.argv:
    rec['working'] = True
open(B, 'a').write(json.dumps(rec) + '\n')
print('said')
