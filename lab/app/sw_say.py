"""Claude's reply into the Scorewright chat.  usage: python sw_say.py "text" [session] [--working]
(no session: the current piece, from current_session.txt; the server drops a line for any other piece)
--working marks the reply as an acknowledgment of work in progress: the page then shows "Claude is
working on it" with the elapsed minutes until the next suggestion or reply."""
import sys, json, datetime
B = '/Users/bdogellis/Documents/Score Exports/_bridge/queue/outbox.jsonl'
args = [a for a in sys.argv[1:] if a != '--working']
CUR = '/Users/bdogellis/Documents/Score Exports/_bridge/current_session.txt'
session = args[1] if len(args) > 1 else open(CUR).read().strip()
rec = dict(ts=datetime.datetime.now().isoformat(timespec='seconds'), session=session, text=args[0])
if '--working' in sys.argv:
    rec['working'] = True
open(B, 'a').write(json.dumps(rec) + '\n')
print('said')
