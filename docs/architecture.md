# Architecture

Scorewright is a local server, a web page, a set of command-line tools, and a Claude Code session that does the composing. The pieces talk through HTTP on port 8790 and through files in `~/Documents/Score Exports/_bridge` (`$E/_bridge` below).

## Components

    Brian
      | browser: https://macbook-pro.tail2783bf.ts.net (phone, via Tailscale) or http://localhost:8790
      | MuseScore panel (Scorewright.qml): ws://localhost:8791
      v
    lab/app/server.py        launchd job com.scorewright.server, whisperer python
      | owns $E/_scorewright_out/session/<piece>/ and its state.json
      | appends to _bridge/queue/inbox.jsonl, reads _bridge/queue/outbox.jsonl
      | appends to _bridge/verdicts.jsonl
      | subprocesses: render_one.py, color_xml.py, fix_pedal.py, mark_xml.py, layout_xml.py,
      |               human_apply.py (rebase), listen.py, media.py, hum.py, abc2xml.py (new pieces)
      | in-memory NotePerformer render queue
      v
    Claude Code session
      sw_wait.sh          blocks on inbox.jsonl, prints new lines, exits
      np_agent.py         polls /api/np/claim, runs dorico_render.py (Dorico 4 + NotePerformer)
      composing tools     lab/dump_abc.py, brief.py, check_lines.py, human_apply.py, ...
      sw_suggest.py       POST /api/suggest
      sw_working.py       POST /api/working
      sw_say.py           appends to outbox.jsonl

| component | file | role |
|---|---|---|
| server | `lab/app/server.py` | One process for one current piece. Serves the page and its JSON API on 8790 and the MuseScore panel on 8791, keeps `state.json`, writes the inbox and the verdict log, watches the outbox, listens to MIDI keyboards, queues renders. Binds `0.0.0.0` with no authentication. |
| page | `lab/app/page.html` | The surface: chat, mic, take, hum and upload buttons, the score, Accept and Reject, playback. Polls `/api/state` every 2 s. See [surface.md](surface.md). |
| MuseScore panel | `lab/app/Scorewright.qml` | MuseScore Studio 4.7 plugin: the same chat and verdict buttons, opens suggestions as score tabs. Uses the WebSocket. |
| renderer | `lab/app/render_one.py` | One score to `<stem>.svg` (Verovio), `<stem>.audio.txt` (MuseScore mp3 as a data URI) and `<stem>.bars.json` (bar start times). A fresh process each time because Verovio is not thread-safe. |
| NotePerformer helper | `lab/app/np_agent.py`, `lab/app/dorico_render.py` | Claims render jobs from the server and drives Dorico 4 to export audio. Runs from the Claude Code session because it needs Accessibility. See [playback.md](playback.md). |
| input | `lab/app/listen.py`, `hum.py`, `media.py` | Takes, hum and uploads to notes. See [input.md](input.md). |
| loop scripts | `lab/app/sw_wait.sh`, `sw_say.py`, `sw_suggest.py`, `sw_working.py` | How the Claude Code session hears Brian and answers him. |
| composing tools | `lab/*.py` | Read, write, check and splice. See [COMPOSING.md](../lab/COMPOSING.md). |

## From his voice to a green suggestion and a logged verdict

1. He taps 🎤 in the page. The browser's speech recognition fills the text box, he fixes anything it misheard and presses Send (or Enter).
2. The page posts `/api/message`. The server appends the text to the chat in `state.json` and appends `{"ts", "session", "text"}` to `_bridge/queue/inbox.jsonl`. MuseScore panels get the chat line over the WebSocket.
3. `sw_wait.sh`, running in the background of the Claude Code session, sees the inbox grow past its cursor, prints the new lines, updates `_bridge/queue/.inbox_cursor` and exits. Claude Code is notified that the task finished.
4. Claude reads the whole piece (`dump_abc.py`, `brief.py`), decides the move, writes `[b:i][V:k]...|` lines, checks them with `check_lines.py`, and splices them with `human_apply.py` into `lab/apply_<tag>_final.xml`. Procedure: [COMPOSING.md](../lab/COMPOSING.md).
5. `sw_suggest.py <final.xml> <lo> <hi> "<note>" lines.txt` posts `/api/suggest`. The server increments `seq`, copies the file to `S<n>.musicxml`, and builds the editor copy `S<n>.green.musicxml`: `color_xml.py` tints bars lo-hi green, `fix_pedal.py` rewrites pedal retakes as release plus press, `mark_xml.py` adds "▶ Scorewright suggestion: bars lo-hi" text and a dashed bracket, `layout_xml.py` sets staff size and page layout. It adds the suggestion (status `open`) and a chat entry, then starts a render.
6. The render thread runs `render_one.py` on the green copy: `S<n>.svg`, `S<n>.audio.txt` (MuseScore audio) and `S<n>.bars.json`. Then the server queues a NotePerformer render for the same file.
7. The page, polling every 2 s, shows a green-bordered card in the chat with Accept, Reject and show, and lights the "latest suggestion" button ("new: S<n> (click to show)"). It does not switch the score view by itself.
8. `np_agent.py` claims the job (`/api/np/claim`), runs `dorico_render.py` under `_bridge/heavy.lock`, and reports back (`/api/np/done`). On success `S<n>.np.m4a` exists, `S<n>.audio.txt` now holds the NotePerformer audio, and `state.json` gets `np_audio["S<n>"]`. The play button reads "▶ NotePerformer".
9. He presses Accept or Reject. The page posts `/api/accept` or `/api/reject` with empty text. The server sets the status and appends a verdict record to `_bridge/verdicts.jsonl` (score 4 for accept, 1 for reject, `source: "ui"`) and `[ACCEPT S<n>]` or `[REJECT S<n>]` to the inbox.
10. On Accept the server copies `S<n>.musicxml` (the clean copy, not the green one) over `working.musicxml`, along with its SVG, audio, bar times and NotePerformer audio. That SVG was drawn from the green copy, so the accepted bars stay green in the working view until the working score is rendered again. Then it rebases every other open suggestion onto the new working score in a background thread (`rebase_open`: re-runs `human_apply.py` with the stored lines under the text2score python, rebuilds the green copy, re-renders).
11. Whatever he says or types next goes to `/api/verdict_note`: appended to the suggestion's `verdict` text, logged as its own verdict record (`note: "reason given after the button"`), and sent to the inbox as `[S<n> reason] ...`. After a Reject that is his reason, and the mic starts by itself to take it. After an Accept it is often his next request.
12. `sw_wait.sh` delivers the verdict and the reason. After a rejection Claude composes the next take straight away. After an accept Claude waits for his words or `[CONTINUE]`.

Replies that are not suggestions go the other way: `sw_say.py "text" <session>` appends `{"ts", "session", "text"}` to `_bridge/queue/outbox.jsonl`. The server's outbox watcher (1 s poll) adds lines whose session matches the current piece to the chat and broadcasts them. Lines for other sessions are skipped and never shown.

## state.json

One per piece, at `$E/_scorewright_out/session/<piece>/state.json`. Written only by the server, under a lock.

| field | meaning |
|---|---|
| `session` | piece name, same as the folder name |
| `title` | display title in the header menu |
| `preset`, `key`, `meter`, `tempo`, `created` | set when the piece was made with "New piece" |
| `working` | absolute path of `working.musicxml`, or null before a score is set |
| `seq` | number of the last suggestion |
| `suggestions` | list of suggestion records (below) |
| `chat` | the last 200 chat entries |
| `np_audio` | `{stem: time}` for stems whose NotePerformer audio is ready, e.g. `working`, `S34` |
| `outbox_seen` | how many outbox lines have been delivered |

`/api/state` returns the file with `session` set to the current piece, plus two fields that are not stored: `page_version` (the server's start time; the page reloads when it changes) and `np_pending` (stems still waiting for NotePerformer).

A suggestion record:

| field | meaning |
|---|---|
| `id` | `S<n>` |
| `ts` | when it was registered |
| `lo`, `hi` | first and last bar of the suggestion, 1-based |
| `note` | the text shown in the card |
| `file` | `S<n>.musicxml`, the clean score that becomes the working score on Accept |
| `green` | `S<n>.green.musicxml`, the editor copy that is rendered and opened in Dorico or MuseScore |
| `status` | `open`, `accepted`, `rejected` or `withdrawn` |
| `lines` | the answer lines sent with `sw_suggest.py`; needed for rebasing |
| `verdict` | his words, once he has given them |

A chat entry has `ts`, `who` (`brian` or `claude`) and `text`, plus one of `suggestion`, `verdict` or `take` when it refers to one.

## Files in a session folder

- `state.json`
- `working.musicxml` and its `working.svg`, `working.audio.txt`, `working.bars.json`, `working.np.m4a`
- `S<n>.musicxml`, `S<n>.green.musicxml`, `S<n>.svg`, `S<n>.audio.txt`, `S<n>.bars.json`, `S<n>.np.m4a`, and `S<n>.lines.txt` once it has been rebased
- `audio_<md5>.mp3`: MuseScore renders, cached by file path plus modification time
- `start.musicxml` and `start.abc` for a piece made with "New piece"
- `take_HHMMSS.wav`, `.midi.json`, `.abc`, `.svg` for each 🎹 take; `hum_HHMMSS.wav` for each hum
- `uploads/upload_HHMMSS_<name>` (the file as sent) and `upload_HHMMSS.wav`, `.abc`, `.svg`, `.midi.json`, `.mid`

## The bridge folder

| file | what |
|---|---|
| `queue/inbox.jsonl` | everything Brian says, one JSON line each: `ts`, `session`, `text`; takes and uploads add `take`, `wav`, `midi` |
| `queue/.inbox_cursor` | how many inbox lines `sw_wait.sh` has delivered |
| `queue/outbox.jsonl` | Claude's replies from `sw_say.py`: `ts`, `session`, `text` |
| `verdicts.jsonl` | every verdict (124 lines on Oct 9 2026) |
| `current_session.txt` | the current piece; the server starts on it |
| `heavy.lock` | `flock` shared by NotePerformer renders and upload transcriptions |
| `suggestions/` | lines plus rendered MusicXML for verdicts logged with `log_verdict.py` (pre-surface) |
| `dorico_debug_*.png` | screenshots of unexpected Dorico dialogs |
| `swexport.log` | log of the Sept 22 Sibelius export plugin |

Verdict records written by the surface:

- Accept or Reject: `ts`, `test` (`<session>/S<n>`), `task` (the note), `bars`, `suggestion_lines`, `score_file`, `verdict` (`"ACCEPTED. ..."` or `"REJECTED. ..."`), `score` (always 4 or 1), `source: "ui"`
- Reason after the button: `ts`, `test`, `verdict` (his words), `note: "reason given after the button"`, `source: "ui"`

`lab/log_verdict.py <tag> <score 0-5> "<verdict>" ["<task>"]` writes the older shape (`score_file: suggestions/<tag>.musicxml`, a real 0-5 score) and copies `lab/apply_<tag>_final.xml` into `suggestions/`. Records from the training phase have other fields (`model`, `piece`, `decode`, `candidate`, `his_words`). Join a reason to its verdict by `test`.

## HTTP routes (port 8790)

GET:

| route | what it does |
|---|---|
| `/` | the page (`page.html`, read once at server start) |
| `/api/state` | the current piece's `state.json`, with `page_version` and `np_pending` added |
| `/api/sessions` | current piece, all pieces (`name`, `title`, `mtime`, newest first), preset names |
| `/file?name=` | download a file from the session folder as an attachment; only `.mid`, `.svg`, `.abc`, `.m4a`, `.musicxml` |
| `/api/np/claim` | next NotePerformer job as `{xml, stem, tries}`, or `{}` when the queue is empty |
| `/api/job?id=` | status of an upload job: `queued`, waiting for a render, `extracting audio`, `transcribing`, `done` with `result`, `failed`, or `unknown` |
| `/take_svg?id=` | the rendered staff of a take or upload |
| `/svg?id=` | the score SVG for `working` (default) or `S<n>`; a 404 placeholder ("rendering, try again in a moment") until it exists |
| `/audio?id=` | the audio data URI for `working` or `S<n>` as plain text, empty if none yet |
| `/bars?id=` | `[[bar, start_seconds], ...]` for play-from-bar |
| `/open?id=&app=` | open the suggestion's green copy, or the working score when `id` is empty, in `Dorico` (default, Dorico 4), `MuseScore` (MuseScore 4) or `Sibelius` (`lab/open_in_sibelius.sh`) |

POST:

| route | body | what it does |
|---|---|---|
| `/api/message` | `{text}` | chat entry plus inbox line |
| `/api/suggest` | `{file, lo, hi, note, lines}` | register a suggestion (what `sw_suggest.py` calls) |
| `/api/accept` | `{id, text, who}` | accept: verdict record, working score replaced, other open suggestions rebased. `who` other than `brian` labels the chat line "Noted from your message" |
| `/api/reject` | `{id, text, who}` | reject: verdict record |
| `/api/verdict_note` | `{id, text}` | the reason after a button: added to the suggestion, own verdict record, `[S<n> reason]` inbox line |
| `/api/withdraw` | `{id}` | mark a suggestion withdrawn; no verdict record |
| `/api/working` | `{file}` | copy a score in as the working score and render it (what `sw_working.py` calls) |
| `/api/rerender` | none | re-render SVG and MuseScore audio for the working score and every suggestion |
| `/api/new` | `{title, preset, key, meter, tempo, bars}` | new piece: empty score built from ABC with `abc2xml.py` (8 bars by default), switch to it, `[NEW PIECE ...]` inbox line |
| `/api/session` | `{name}` | switch to an existing piece |
| `/api/take/start` | none | remember the take's start time; returns the MIDI ports the server can see |
| `/api/take/stop` | WAV bytes | save the take, pair MIDI captured since start, run `listen.py`; returns words, notes, ABC, SVG, source, tempo |
| `/api/take/use` | `{id, words}` | send a take or upload to the inbox as `[TAKE <id>] <words>` with its file paths |
| `/api/hum` | WAV bytes | run `hum.py`; returns `{heard, abc, notes, bpm, seconds}` |
| `/api/upload?name=&bpm=` | the file | stream it to `uploads/`, start a background transcription job; returns `{id, bytes}` |
| `/api/np/done` | `{xml, stem, tries, rc, tail}` | `np_agent.py` reports a render result |

## WebSocket (port 8791)

Used only by the MuseScore panel; the page polls HTTP instead. Client to server: `{type: "message", text}`, `{type: "accept", id, text}`, `{type: "reject", id, text}`, `{type: "state"}`. Plain text that is not JSON counts as a message. Server to clients: `state` (the whole state, on connect and on request), `chat`, `suggestion`, `verdict`, `working`. Port 8791 is not exposed through Tailscale.

## Threads, queues and locks

- The main thread runs the WebSocket server. Daemon threads run the HTTP server, the outbox watcher (1 s poll), the MIDI listener (rescans ports every 2 s), and `np_catch_up` at start and on every piece switch.
- `lock` guards `state.json`. `render_lock` makes `render_one.py` runs go one at a time.
- The NotePerformer queue is in memory. `np_catch_up` refills it at start for the working score and open suggestions whose `.np.m4a` is missing or older than the score. Return code 2 (Dorico busy) is retried after 90 s, code 3 (no Accessibility) after 300 s, up to 40 tries.
- `_bridge/heavy.lock` is an `flock` taken by `np_agent.py` around each Dorico render and by upload jobs around extraction and transcription, so the two never compete for the CPU. Takes and hums do not take it.
- Upload job status, the MIDI buffer and the take start time live in memory and are lost on restart.

## Code map

`lab/app/`:

| file | one line |
|---|---|
| `server.py` | the server described above |
| `page.html` | the page |
| `render_one.py` | `<xml> <out_stem> <session_dir>`: SVG, MuseScore audio, bar times |
| `dorico_render.py` | `<xml> <out_stem>`: NotePerformer audio through Dorico; exit 0 ok, 1 failed, 2 busy, 3 no permission |
| `np_agent.py` | render helper loop; polls every 4 s |
| `listen.py` | `<wav> <bpm or auto> [midi.json or -] [stem] [--upload] [--out=dir]`: whisper words plus notes as ABC |
| `hum.py` | `<audio> [bpm]`: pyin pitch tracking to notes |
| `media.py` | `<input> <output.wav> [rate]`: audio track of any audio or video file, through PyAV |
| `sw_wait.sh` | block until new inbox lines, print them, exit |
| `sw_say.py` | `"text" [session]`: reply into the chat |
| `sw_suggest.py` | `<final.xml> <lo> <hi> "note" [lines.txt]`: register a suggestion |
| `sw_working.py` | `<score.musicxml>`: set the working score |
| `Scorewright.qml` | MuseScore panel |

`lab/`, the tools the loop uses:

| file | one line |
|---|---|
| `COMPOSING.md` | the procedure and the rules |
| `dump_abc.py` | `<xml> <tag>`: rest-reduced interleaved ABC of a score (text2score env) |
| `brief.py` | `<stem> [last_bar] [part] [instrument regex]`: form map, last bars, retrieval exemplars |
| `corpus_find.py` | `"<instrument regex>" [key] [meter] [since] [max]`: his scores by what a new piece needs |
| `check_lines.py` | `<lines.txt> <units_per_bar> [total:voices ...]`: bar durations, octave-slip warnings |
| `orch_transpose.py` | `<dump.txt> <concert.txt> <written.txt> [--keyed]`: concert to written pitch per voice |
| `human_apply.py` | `<xml> <cut_at> <lo> <hi> <lines.txt> <tag> "<who>"`: splice lines into the score (text2score env) |
| `t2s_edit_apply.py` | the conversion pipeline `human_apply.py` and `dump_abc.py` import (MusicXML to reduced ABC, splice, ABC to MusicXML) |
| `reduce_interleaved.py` | rest reduction line by line, so no bar can be lost |
| `post.py`, `splice.py` | ABC to MusicXML with NotaGen's `rest_unreduce`; splice generated bars into the original engraving by part name |
| `apply_page.py` | `<tag> <lo> <hi> "<title>"`: parts with notes per bar and range violations for an applied edit |
| `color_xml.py` | `<in> <out> <lo> <hi> [#hex]`: tint notes and rests of bars lo-hi (default `#0B8A3E`) |
| `fix_pedal.py` | `<in> <out>`: rewrite `<pedal type="change"/>` as release plus press |
| `mark_xml.py` | `<in> <out> <lo> <hi> ["label"]`: bold green text at the start and after the end, dashed bracket over the region |
| `layout_xml.py` | `<in> <out>`: staff size by staff count, A4 or A3, staff and system distances, strip absolute positions from directions |
| `log_verdict.py` | `<tag> <score> "<verdict>" ["<task>"]`: manual verdict logging (pre-surface) |
| `open_in_sibelius.sh` | open a file in Sibelius and press Return on the import dialog (Sibelius is gone) |
| `band/orchestrate_bv.py` | Bright Valley 18-81 sketch to 24 concert-band parts (23 pitched plus snare), concert pitch |
| `songs/where_i_left_it.py` | a whole song built from tables (harmony per beat, concert melody, lyrics as `w:` lines, piano textures), converted with `abc2xml.py` into `$E/_scorewright_out/songs/`; the worked example for COMPOSING.md section 10 |
| `PREFLIGHT.md` | the checklist before any paid run |

Repo root:

| file | one line |
|---|---|
| `xmledit.py` | text-level MusicXML edit ops (`set_pitch`, `write_notes`, `add_slur`, `append_measures` and others), part-aware locators, `excerpt()` that carries key, time, clef and transpose into a slice |
| `diffview.py` | Verovio rendering (`render`, used by `render_one.py`), plus the older red/green HTML diff with FluidSynth audio |
| `retrieve.py` | melodic interval and rhythm n-gram index over the corpus in SQLite: `--build`, `query`, `excerpt_text`, `self_map` |
| `ranges.py` | textbook sounding ranges by part name, `check(score)` on a sounding-pitch music21 score; physical rules only |
| `analyze.py` | the Aug 28 analysis layer: notated key areas, harmonic sketch, range, parallel and tie checks, texture, `brief()` |
| `edit_format.py` | ABC parsing helpers used by `t2s_edit_apply.py` (and the training documents) |
| `show.py` | HTML listen pages with green bar bands, used by `apply_page.py` |
| `scorewright.py`, `offline.py`, `compose.py` and the rest | the Aug 28-29 OpenRouter and hand-orchestration phase; not used by the surface |
