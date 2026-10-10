"""Claude's reply into the Scorewright chat.  usage: python sw_say.py "text" [session]"""
import sys, json, datetime
B = '/Users/bdogellis/Documents/Score Exports/_bridge/queue/outbox.jsonl'
open(B, 'a').write(json.dumps(dict(ts=datetime.datetime.now().isoformat(timespec='seconds'), session=sys.argv[2] if len(sys.argv) > 2 else 'current', text=sys.argv[1])) + '\n')
print('said')
