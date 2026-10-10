# Operations

Running the system, restarting it, where the logs are, and what to do when something looks wrong. Shorthands as in [CLAUDE.md](../CLAUDE.md): `W` is the whisperer python, `T` the text2score python, `E` is `~/Documents/Score Exports`.

## What runs where

| piece | how it runs | output |
|---|---|---|
| `lab/app/server.py` | launchd job `com.scorewright.server`: whisperer python, working directory `lab/`, `RunAtLoad` and `KeepAlive`, argument `quartet2` (ignored while `_bridge/current_session.txt` exists) | `lab/app/server.log`, stdout and stderr |
| Tailscale serve | https://macbook-pro.tail2783bf.ts.net, tailnet only, proxies `/` to `http://127.0.0.1:8790` | Tailscale app |
| `lab/app/sw_wait.sh` | background task of the Claude Code session, restarted after each delivery | the new inbox lines |
| `lab/app/np_agent.py` | background task of the Claude Code session | one line per render; `lab/app/np_agent.log` when started with `tee` |
| Dorico 4 | opened and closed by `dorico_render.py` for every render, or by Brian through "open in Dorico" | `_bridge/dorico_debug_*.png` |
| MuseScore 4 | its command line runs for every render; the app when Brian opens a file in it | none |

The plist is `deploy/com.scorewright.server.plist`; the installed copy is `~/Library/LaunchAgents/com.scorewright.server.plist` (identical on Oct 9 2026).

Ports 8790 (HTTP) and 8791 (WebSocket) listen on all interfaces with no authentication, so anything on the same network can reach them. Phone access is meant to go through Tailscale. Only 8790 is proxied; the MuseScore panel is local to the Mac. The Tailscale command line is not on the PATH; it lives at `/Applications/Tailscale.app/Contents/MacOS/Tailscale`.

## Health check

    launchctl list | grep scorewright                         # PID, last exit status, label
    lsof -nP -iTCP -sTCP:LISTEN | grep -E ":(8790|8791)\b"    # both ports listening
    curl -s -m 3 http://127.0.0.1:8790/api/sessions           # current piece and all pieces
    tail -n 30 /Users/bdogellis/repos/scorewright/lab/app/server.log
    ps -axo pid,etime,command | grep -E "sw_wait.sh|np_agent.py" | grep -v grep
    /Applications/Tailscale.app/Contents/MacOS/Tailscale serve status

## Restarting the server

    launchctl kickstart -k gui/$(id -u)/com.scorewright.server

What a restart costs:

- Every open page reloads (`page_version` changes). The page puts off its reload while 🎤 or 🎵 is recording, but not during a 🎹 take. Drafts in the text box survive.
- Lost from memory: upload jobs in progress, the NotePerformer queue (`np_catch_up` queues the working score and open suggestions again), the MIDI buffer, and a take's start time.

Restart after changing `server.py` or `page.html`, and not while Brian might be dictating or playing. Afterwards send a one-line `sw_say` and check it appears in the chat.

After editing the plist, copy it to `~/Library/LaunchAgents/` and reload the job:

    launchctl bootout gui/$(id -u)/com.scorewright.server
    launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.scorewright.server.plist

Do not start `lab/app/server.py` by hand while the launchd copy is up; a second copy cannot bind the ports. (COMPOSING.md section 9 shows that command from before the server moved to launchd.)

## Which change needs what

| you changed | takes effect |
|---|---|
| `server.py`, `page.html` | after a server restart |
| `render_one.py`, `listen.py`, `hum.py`, `media.py`, `human_apply.py`, `t2s_edit_apply.py`, `color_xml.py`, `fix_pedal.py`, `mark_xml.py`, `layout_xml.py` | the next time the server runs it |
| `dorico_render.py` | the next NotePerformer render |
| `np_agent.py` | after restarting the helper |
| `sw_wait.sh` | the next time you start it |
| `Scorewright.qml` | after copying it to `~/Documents/MuseScore4/Plugins/Scorewright/` and reopening the panel |

## Pieces

- The current piece is in `$E/_bridge/current_session.txt`. The server starts on it, whatever the plist says.
- Switch from the page's header menu, or `POST /api/session {"name": "<piece>"}`.
- A new empty piece: "New piece" in the header menu, or `POST /api/new`.
- To start from an existing score there is no single route. Create the piece with "New piece" (the title you type is what the menu shows), then load the score: `$W /Users/bdogellis/repos/scorewright/lab/app/sw_working.py "<score>.musicxml"`. The server copies it in as `working.musicxml`; the original is never touched.
- Old pieces stay in `$E/_scorewright_out/session/`. Nothing deletes them.

## Logs and records

- `lab/app/server.log`: a "Scorewright server: ..." line at each start; `render <stem> <last line of output>` for each render (normally `bars ok <n>`); `np <stem> <code> <tail>` for each NotePerformer result; `rebased S<n>` or `rebase failed S<n> ...` after an Accept; MIDI port messages; Python tracebacks. HTTP requests are not logged.
- The helper's output: `HH:MM:SS <stem> <code> [last line]` per render.
- `$E/_bridge/queue/inbox.jsonl` and `outbox.jsonl`: the whole conversation in both directions.
- `$E/_bridge/verdicts.jsonl`: every verdict.
- `$E/_bridge/dorico_debug_<step>_<n>.png`: screenshots of the dialog a render ran into.
- `lab/apply_<tag>*`: everything `human_apply.py` made for one take (work folder, ABC, converted, spliced and final XML, a JSON summary). Gitignored.

## Troubleshooting by symptom

### The page will not load on the phone

Check that Tailscale is on, on the Mac and on the phone, and that `serve status` still maps `/` to port 8790. Then check the server from the Mac with the health check above.

### The page will not load on the Mac either

If `launchctl list` shows no PID or a non-zero exit status, read the end of `server.log` for the traceback, fix it, and kickstart. An "address already in use" error means another copy holds the port, usually a hand-started `server.py`.

### He talks and nothing happens

First see whether his message arrived: `tail -n 3 "$E/_bridge/queue/inbox.jsonl"`. If it did, no waiter is running; start `sw_wait.sh`. If two answers come back for one message, two sessions are each running a waiter; stop one.

### Claude's replies do not show up

`sw_say.py` was run without the session name: the line is tagged `current` and skipped. Check the last lines of `outbox.jsonl` for the session field. Also look for "outbox watch" errors in `server.log`.

### A suggestion card appears but the score says "rendering, try again in a moment"

The render is still running or it failed. Renders run one at a time, so after an Accept with several open suggestions, or after `/api/rerender`, they queue up. `server.log` keeps only the last output line of each render (normally `bars ok <n>`, or the error that stopped it). For the whole story, run `$W lab/app/render_one.py <S<n>.green.musicxml> <scratch>/test <scratch>` by hand and read its lines: `svg ok`, `svg EMPTY` (Verovio could not draw the file), `audio ok`, `bars ok`.

### Play says "audio still rendering"

MuseScore has not written the mp3 yet, or it failed (180 s timeout). Check `server.log`, and try `"/Applications/MuseScore 4.app/Contents/MacOS/mscore" -o /tmp/test.mp3 <file>` on the same file.

### The play button never turns into "▶ NotePerformer"

Go down the list: Is `np_agent.py` running? Does Dorico have a project open, perhaps from "open in Dorico" (code 2, retried every 90 s until it is closed)? Is the helper running somewhere without Accessibility (code 3; it has to run from the Claude Code session)? Did the render fail (code 1; see `_bridge/dorico_debug_*.png` and the helper's output)? Is an upload transcription holding `heavy.lock`?

### "failed: Dorico did not open the file in time"

Dorico can be slow to start, and once missed the timeout while a transcription ran. The job is dropped. The next render of that score queues it again, and at server start `np_catch_up` queues missing audio for the working score and open suggestions.

### Dorico is left with a dialog or project open

`dorico_render.py` screenshots it and tries Escape and Close Project. If something is still open it prints "warning: Dorico project or dialog still open", and every later render is refused as busy. Look at the screenshot, then close it by hand, or ask Brian if it might be his. Never kill Dorico while he could be using it.

### An upload sits on "waiting for the Mac to finish a playback render"

A Dorico render holds `heavy.lock`. It moves on when the render ends.

### An upload says "could not transcribe that: unknown"

The server restarted during the job. Upload again. "could not read the audio" means PyAV found no audio track in the file.

### A take hears no notes, or the wrong ones

He talked while playing (notes inside speech are dropped), no MIDI keyboard was connected (the 🎹 tooltip says so) and the audio model struggled, or the piece is not in 4/4 (takes are quantised in 4/4). Treat rhythm as a sketch either way.

### Hum returns an error

`hum.py` runs on the anaconda base python. Check that `/Users/bdogellis/opt/anaconda3/bin/python -c "import librosa"` still works.

### After an Accept, another open suggestion looks wrong or lost the accepted bars

Its rebase failed (`rebase failed S<n>` in `server.log`), or it was skipped because that suggestion was registered without lines. Withdraw it and register a fresh one built on the new working score.

### `human_apply.py` or `dump_abc.py` fails on import

Errors about torch, transformers, `utils` or `config` mean the wrong python. Use the text2score env.

### `check_lines.py` flags bars that look right

That voice uses a different `L:` unit, so pass per-voice totals (`"4:3,4,6"`). Tuplets and broken rhythms are handled, but a misplaced tuplet ratio will show up here.

### Bars are missing at the end of a long score in the page

`render_one.py` renders page 1 of one tall page (page height 60000). A very long score can run past it.

### The Mac runs hot or slow

Look for a model job first. Orphaned automation Chrome processes driving `replayd` are the usual cause on this Mac. Any Mac-side model job follows the rules below.

## Machine and money rules

- No MPS or GPU training on the Mac (Brian's call, Sept 4 2026, after a crash). For any model job on the Mac: keep the MPS memory ceiling on (never `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`), at most 512 patches of context, check `memory_pressure` and swap before starting and every few minutes, tell Brian before it starts, and stop it if per-item times keep climbing. That means it is swapping.
- No GPU or API spend without a dry run shown to him first: run the exact training and decode code on a sample, then show the encoded sizes (patches or tokens, not characters), skip and truncation counts, and raw outputs with no harness. `lab/PREFLIGHT.md` is the checklist. He decides.
- Nothing about the composing loop needs either. It runs on Claude Code and the Mac's CPU.
