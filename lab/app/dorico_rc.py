"""Edit the Dorico project Brian has open, live, through Dorico 4's remote-control link
(ws://127.0.0.1:4560). Every command is one undo step in his project, so Cmd+Z takes any of it back.

The first connection makes Dorico ask Brian to allow "Scorewright" (push him first). The session
token it returns is kept outside the public repo, in $E/_bridge/dorico/session_token.txt, and later
connections reuse it without a prompt. Dorico 4.0 answers "command" and "getstatus" only; getstatus
does not say what is selected. What is selected comes from Dorico's status bar through
accessibility: "Bar 16" and "Note: A4 (Up-stem Voice 1)", in concert pitch.

Command names and their parameters: Dorico's key-command file
(/Applications/Dorico 4.app/Contents/Resources/keycommands_en.json) and its log
(~/Library/Application Support/Steinberg/Dorico 4/application.log), which records every command
Brian runs, with parameters. Found on Nov 13 2026 (Dorico 4.0.31):
- Edit.SelectAtPoint?X=..&Y=..&AddToSelection=0&BlockSelection=0&NextSelectionAtPoint=0&SelectionTriggerAction=0
  selects what is at a page position; the log has the positions of his own clicks. A start point.
- EventEdit.NavigateRight / NavigateLeft: the next item on the staff; NavigateRightBar: the first
  item of the next bar; NavigateUp / NavigateDown: the next note of a chord, then the next staff, one
  step at a time; NavigateRightExtend: extend the selection. NavigateDownNextStave goes to the bottom
  staff, not the next one. With nothing selected, NavigateRight selects the time signature in bar 1,
  where no move works.
- NoteInput.CreateDynamic?Definition=mp&UseLocalOverride=0 (no popover), NoteInput.SetArticulation?Value=kStaccatoTenuto,
  NoteInput.SlurStart and NoteInput.HairpinStart?Type=kGradualDynamicUp&GradualDynamicType=kCrescOrDim
  (Down for a diminuendo) over the selection.
usage: python app/dorico_rc.py allow    asks Dorico for access and saves the token
       python app/dorico_rc.py status   prints what the status bar shows
from code: d = Dorico(); d.cmd('EventEdit.NavigateRight'); bar, item, texts = d.sb()"""
import asyncio, json, os, subprocess, sys

import websockets

TOKEN = '/Users/bdogellis/Documents/Score Exports/_bridge/dorico/session_token.txt'
URL = 'ws://127.0.0.1:4560'
SB = '''tell application "System Events"
tell process "Dorico 4"
set w to first window whose subrole is "AXStandardWindow"
set out to ""
repeat with t in (static texts of w)
set out to out & (value of t as text) & "|"
end repeat
return out
end tell
end tell'''


class Dorico:
    def __init__(self, allow=False):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.ws = self.loop.run_until_complete(websockets.connect(URL, max_size=None, open_timeout=10))
        hello = {"message": "connect", "clientName": "Scorewright", "handshakeVersion": "1.0"}
        if os.path.exists(TOKEN) and not allow:
            hello['sessionToken'] = open(TOKEN).read().strip()
            self.send(hello)
            r = self.recv(5, first=True)
            if not r or r[0].get('code') != 'kConnected':
                raise RuntimeError(f'Dorico refused the saved token: {r}. Run "dorico_rc.py allow".')
            return
        self.send(hello)
        r = self.recv(240, first=True)
        token = r[0].get('sessionToken') if r else None
        if not token:
            raise RuntimeError(f'Dorico gave no token (Brian did not allow it?): {r}')
        os.makedirs(os.path.dirname(TOKEN), exist_ok=True)
        open(TOKEN, 'w').write(token)
        self.send({"message": "acceptsessiontoken", "sessionToken": token})
        self.recv(5, first=True)

    def send(self, m):
        self.loop.run_until_complete(self.ws.send(json.dumps(m)))

    def recv(self, wait=0.3, first=False):
        out = []

        async def get():
            try:
                while True:
                    out.append(json.loads(await asyncio.wait_for(self.ws.recv(), wait)))
                    if first:
                        return
            except asyncio.TimeoutError:
                pass
        self.loop.run_until_complete(get())
        return out

    def cmd(self, command, n=1, wait=0.15):
        """run a command n times; returns the error answers, empty when all were accepted"""
        res = []
        for _ in range(n):
            self.send({"message": "command", "command": command})
            res += self.recv(wait)
        return [r for r in res if r.get('code') not in (None, 'kOK')]

    def status(self):
        self.send({"message": "getstatus"})
        return [r for r in self.recv(1.0) if r.get('message') == 'status']

    def sb(self):
        """(bar, item, all texts) from the status bar, e.g. (16, 'Note: A4 (Up-stem Voice 1)', [...])"""
        r = subprocess.run(['osascript', '-e', SB], capture_output=True, text=True, timeout=30).stdout.strip()
        parts = [p for p in r.split('|') if p]
        at = next((i for i, p in enumerate(parts) if p.startswith('Bar ') and p.split()[1].isdigit()), None)
        if at is None:
            return None, 'No selection' if 'No selection' in parts else '', parts
        item = parts[at + 1] if at + 1 < len(parts) and not parts[at + 1].startswith('Flow ') else ''
        return int(parts[at].split()[1]), item, parts


if __name__ == '__main__':
    if sys.argv[1:] == ['allow']:
        Dorico(allow=True)
        print('allowed; token saved')
    else:
        print(Dorico().sb())
