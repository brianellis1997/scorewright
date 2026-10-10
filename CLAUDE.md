# CLAUDE.md

Operating manual for a Claude Code session working on Scorewright. Read it once top to bottom, then read [lab/COMPOSING.md](lab/COMPOSING.md) before you write a note.

## What this is

Scorewright is a copilot for composers. Use that phrase; it is how Brian describes it.

Brian is a composer and a software engineer. Here you (Claude Code) compose in his style through a notation harness. You read his whole score, pull examples from his own 1,607-score archive, write new bars in ABC, convert and splice them into his MusicXML, and register the result as a suggestion. A web page shows it in green on his phone or desktop. He accepts or rejects it, usually with a spoken reason, and every verdict is logged to `_bridge/verdicts.jsonl` as training and eval data. Playback comes from MuseScore's command line within seconds, then from Dorico with NotePerformer (35-90 s per render).

No trained music model is in the loop. The model is you. The value is in what gets read, decided and checked, and in his verdicts. How it ended up this way: [docs/history.md](docs/history.md).

## Where things are

Code, in this repo (`/Users/bdogellis/repos/scorewright`):

- `lab/COMPOSING.md`: the composing procedure and every rule learned from his verdicts. The most important file here. Link to it, never copy it.
- `lab/app/`: the surface. `server.py` (runs under launchd), `page.html`, `render_one.py`, `dorico_render.py`, `np_agent.py`, `listen.py`, `hum.py`, `media.py`, `Scorewright.qml` (MuseScore panel), and the scripts you use to talk to the server: `sw_wait.sh`, `sw_say.py`, `sw_suggest.py`, `sw_working.py`.
- `lab/*.py`: the composing tools (below), plus many scripts from the training phase that the loop does not use.
- `lab/band/orchestrate_bv.py`: worked example of orchestrating a two-stave sketch for concert band.
- Root modules the loop uses: `xmledit.py` (MusicXML text surgery, excerpts), `diffview.py` (Verovio rendering), `retrieve.py` (corpus index), `ranges.py` (instrument ranges). `analyze.py` is the Aug 28 analysis layer. Most other root files belong to the Aug 28-29 OpenRouter phase.
- `lab/NotaGen`: git submodule (ElectricAlexis/NotaGen). The pipeline uses its `data/xml2abc.py`, `data/abc2xml.py`, `data/prep_corpus.py`, and `rest_unreduce` from `inference/inference.py`. `data/prep_corpus.py` is ours, not upstream: on a fresh clone copy `lab/notagen_prep_corpus.py` there, or `t2s_edit_apply.py` (and so `dump_abc.py` and `human_apply.py`) cannot convert anything.
- `deploy/com.scorewright.server.plist`: the launchd job. The installed copy is `~/Library/LaunchAgents/com.scorewright.server.plist`.

Data, outside the repo in `~/Documents/Score Exports` (`$E` below):

- `PROJECT.md`: the living spec, about 3,900 lines of measurements, decisions and wrong turns. Read its newest sections when you start, and grep it before researching anything.
- `MusicXML/`: the archive, 1,607 scores exported from Sibelius. Read only.
- `extra_sept2026/`: 48 more scores exported Sept 22 2026. See its `README.txt`.
- `_logs/archive_name_map.json`: real titles for archive files whose names were cut at a period.
- `compact/`, `retrieval.sqlite`, `abc_reduced/`: what retrieval and `corpus_find.py` read.
- `_scorewright_out/session/<piece>/`: one folder per piece. `state.json`, `working.musicxml`, `S<n>.musicxml` and `S<n>.green.musicxml` with their `.svg`, `.audio.txt`, `.bars.json`, `.np.m4a`, plus takes and `uploads/`.
- `_bridge/`: `verdicts.jsonl`, `queue/inbox.jsonl`, `queue/outbox.jsonl`, `current_session.txt`, `heavy.lock`, `suggestions/`.

More: [docs/architecture.md](docs/architecture.md), [docs/corpus.md](docs/corpus.md).

## Environments

Never run a bare `python` or `pip`. Install with `<that env's python> -m pip install ...` into the env that needs it.

| env | interpreter | runs |
|---|---|---|
| whisperer (3.12) | `/Users/bdogellis/miniforge3/envs/whisperer/bin/python` | nearly everything: `server.py`, `np_agent.py`, `dorico_render.py`, `render_one.py`, `listen.py`, `media.py`, `brief.py`, `corpus_find.py`, `check_lines.py`, `orch_transpose.py`, `apply_page.py`, `color_xml.py` and the other post-processors, `log_verdict.py`, the `sw_*.py` scripts |
| text2score (3.10) | `/Users/bdogellis/miniforge3/envs/text2score/bin/python` | `human_apply.py` and `dump_abc.py`. Both import `lab/t2s_edit_apply.py`, which needs torch, transformers 5 and the Text2Score repo in `$E/_models/_text2score`. The server's `rebase_open` runs `human_apply.py` with this python, and `brief.py` shells out to it for `dump_abc.py`. No model runs when you use them. |
| anaconda base (3.8) | `/Users/bdogellis/opt/anaconda3/bin/python` | `lab/app/hum.py` only (`HUM_PY` in `server.py`) |

Each Bash call starts a fresh shell, so define the shorthands used below in the same command:

    W=/Users/bdogellis/miniforge3/envs/whisperer/bin/python
    T=/Users/bdogellis/miniforge3/envs/text2score/bin/python
    E="/Users/bdogellis/Documents/Score Exports"
    cd /Users/bdogellis/repos/scorewright/lab

## Session start checklist

1. Read `lab/COMPOSING.md`. Skim the end of `$E/PROJECT.md` for anything newer than this file.
2. Server up? `launchctl list | grep scorewright` shows a PID, and `curl -s -m 3 http://127.0.0.1:8790/api/sessions` returns JSON. If not, see [docs/operations.md](docs/operations.md).
3. Is another session already running the loop? `ps -axo pid,etime,command | grep -E "sw_wait.sh|np_agent.py" | grep -v grep`. Two waiters both wake on the same message and both answer it. If another live session owns them, leave them alone. If they look orphaned, ask Brian before stopping anything.
4. Start the waiter as a background task: `/Users/bdogellis/repos/scorewright/lab/app/sw_wait.sh`. It blocks until Brian says something in the page, prints every inbox line it has not delivered yet (the count lives in `_bridge/queue/.inbox_cursor`), and exits. Handle the lines, then start it again. One must be running the whole time he works.
5. Start the NotePerformer helper as a background task: `cd /Users/bdogellis/repos/scorewright/lab && /Users/bdogellis/miniforge3/envs/whisperer/bin/python -u app/np_agent.py | tee -a app/np_agent.log`. It has to run from this session. macOS refuses Accessibility to the launchd server ("osascript is not allowed assistive access"), and the helper drives Dorico through System Events. The permanent fix is for Brian to grant Accessibility to the whisperer python once; then the helper can run under launchd as well.
6. Which piece? `cat "$E/_bridge/current_session.txt"`, then read that folder's `state.json` for the working score path and any suggestion with `"status": "open"`.

## The loop

He talks or types in the page, or in the MuseScore panel. Each message becomes a line in `_bridge/queue/inbox.jsonl`, and `sw_wait.sh` hands it to you. What arrives:

- plain text: what he wants
- `[ACCEPT S<n>]`, `[REJECT S<n>]`: a button press, usually with no text
- `[S<n> reason] ...`: whatever he says or types right after a button. After a Reject it is his reason. After an Accept it is often what he wants next, so read it as a request too.
- `[CONTINUE] propose the next bars from where the working score stops`: the ▶ continue button
- `[TAKE take_HHMMSS] ...` or `[TAKE upload_HHMMSS] ...`: notes he played or uploaded. The JSON line carries `take` (the `.abc` file), `wav` and `midi` paths. See [docs/input.md](docs/input.md).
- `[HUM] I heard: D#5(2) E5(1) ... | ...`: hummed notes, possibly corrected by him, lengths in eighths
- `[NEW PIECE <name>] ...`: he made a new piece from the header menu

Rules, from COMPOSING.md section 9 and from what went wrong in earlier sessions:

- Reply only through `sw_say.py`, and always pass the session name: `$W app/sw_say.py "text" <session>`. Without it the line is tagged `current`, and the server silently drops any outbox line whose session is not the current piece.
- The suggestion block is the message. Never follow `sw_suggest` with an `sw_say` that repeats it. `sw_say` is for a question, a fix, or a withdrawal, in one or two sentences.
- Acknowledge at once when a request will take more than a minute (a continue, a rewrite): `$W app/sw_say.py "<what, roughly how long>" <session> --working`. The page then shows "Claude is working on it · N min" under the chat until the next suggestion or reply. Brian, Oct 10 2026: "when I press continue, nothing's happening; I don't know what's going on." The page also says when nothing is listening: `sw_wait.sh` keeps `_bridge/queue/.listener` fresh while it waits, and `/api/state` reports `listening`, `undelivered`, `delivered_at` and `busy`.
- An Accept is not a request. Wait for his words or `[CONTINUE]`.
- One open suggestion per region at a time.
- Never write to the working score directly. Every change goes through a suggestion so the log stays complete. `sw_working.py` loads a piece; it is not an editing tool.
- After a rejection reason: compose, `check_lines.py`, `human_apply.py`, `sw_suggest.py`. In that order, nothing in between, within minutes.
- Never end a piece unless he asks. A continuation stops where the next idea would start.
- If he gives a verdict in words instead of a button, record it through the API so the working score and the log stay consistent: `curl -s -X POST http://127.0.0.1:8790/api/accept -H 'Content-Type: application/json' -d '{"id":"S5","text":"<his words>","who":"claude"}'` (or `/api/reject`). The chat labels it "Noted from your message".
- To withdraw a suggestion: `curl -s -X POST http://127.0.0.1:8790/api/withdraw -H 'Content-Type: application/json' -d '{"id":"S5"}'`, then one `sw_say` line saying why.
- Do not run `log_verdict.py` during the loop. The server logs every button press and every reason.
- Do not restart the server while he might be dictating; a restart reloads his page. After any restart, confirm that an `sw_say` reply shows up in the chat.
- Keep terminal output to a line while he is working. No side projects in the middle of a region.

## How to compose

Follow `lab/COMPOSING.md` in order. The tools, in the order you reach for them (run from `lab/`):

1. Read the whole piece, never just the last four bars. Every continue, revision or rejection starts here, even when the piece is already in your context: `$W engrave_pages.py <working.musicxml>`, read every page with the Read tool, and write down the melody, harmony, motifs, texture and what is still open before you look at anything else (COMPOSING.md section 1, "Every time"). Brian, Oct 10 2026: "I always re-listen to everything before I start writing again."
   - `$T dump_abc.py <score.musicxml> <tag>`: the score as rest-reduced interleaved ABC, header first, one line per bar. For a piece in progress, point it at the session's `working.musicxml`. Printed line numbers are 1-based; the `[b:i]` you write is 0-based.
   - `$W brief.py "<archive stem>" [last_bar] [part] ["violin|viola|cello"]`: form map (empty bars, tempo and text changes), the last written bars, and retrieval exemplars from his corpus with his slurs and dynamics. Archive pieces only; it reads `$E/MusicXML/<stem>.musicxml`.
   - `$W corpus_find.py "<instrument regex>" [key] [meter] [since YYYY-MM-DD] [max]`: his scores by instrumentation, key, meter and date, for a new piece. Then `dump_abc.py` two or three of them.
2. Write down form, material, harmonic language, register per voice, and where and why it stopped. Then the structural move in one sentence. If the sentence is "continue the pattern", read again.
3. Write answer lines, one bar per line: `[b:<0-based bar>][V:1]...|[V:2]...|`, using the spellings his exports use (COMPOSING.md section 3). Keep lines files in `lab/` (earlier takes are `lab/human_<piece>_<take>_lines.txt`); the `/tmp` scratchpad is purged after a few days.
4. Check durations: `$W check_lines.py lines.txt 8 "4:3,4,6"`. The second argument is units per bar in the default `L:` unit, and `total:voices` overrides it per voice. It must end with `CHECK OK`. Read any `WARN octave slip?` line. Never render a file that fails.
5. Transposing instruments: concert pitch, always, for Brian. Write and notate every part at sounding pitch: no `transpose=` in ABC, no `<transpose>` in MusicXML. Only a user who wants transposed parts gets `$W orch_transpose.py <dump.txt> <concert.txt> <written.txt> [--keyed]`.
6. Splice: `$T human_apply.py <score.musicxml> <cut_at> <lo> <hi> lines.txt <tag> "<what was done>"` writes `lab/apply_<tag>_final.xml`. `cut_at` is how many bars of the input to keep (the last written bar when continuing past an empty tail, 9999 to keep everything). `lo` and `hi` are the 1-based bars of the suggestion, including any lead-in bar you rewrote.
7. Verify (next section).
8. Register: `$W app/sw_suggest.py apply_<tag>_final.xml <lo> <hi> "<note>" lines.txt`. The note is what he reads in the card. Always pass `lines.txt`: the server needs the lines to rebase this suggestion if he accepts a different one first.

For a whole new piece, from his words or from scratch, there is no score to splice into: follow COMPOSING.md section 10 and the worked example `lab/songs/where_i_left_it_s3.py`, which builds the full ABC (words as `w:` lines, transposing melody voice, piano figures, beams in fours) and registers it as a suggestion in its own piece. Start from his own idea when he has one (a progression, a contour, a take), and search the archive for how he treats it: `$W find_progression.py "<pattern>" --melody` (COMPOSING.md section 13). Every melody passes `$W lint_line.py <score>` before he hears it: accidentals leaning the right way, breaths, recovered leaps, range. For anything "in his style" (or anyone's), read his engraved pages first, as images (`$E/PDF/<stem>.pdf` with the Read tool, a few pages at a time): what each part does, register, doubling, counter-lines, space, how the parts answer each other (COMPOSING.md section 12). Before he hears a draft, render it and read your own pages the same way against his. Then the reductions: `$W reduce_harmony.py <score>` (COMPOSING.md section 12). Write from what they do, then use `$W style_profile.py <his scores> --draft <draft>` only to catch gross mismatches (section 11). S1 of "Where I Left It" was "too pop". S2 was rewritten to the profile's numbers, landed inside his range on every measure, and was still "odd, not mine".

The server makes the green editor copy itself (`color_xml.py`, `fix_pedal.py`, `mark_xml.py`, `layout_xml.py`). The manual versions of those steps in COMPOSING.md section 5 are for producing a standalone file. For a piano sketch that is really an ensemble piece, see COMPOSING.md section 8 and `band/orchestrate_bv.py`.

## Verify before he sees it

COMPOSING.md section 5: the duration check passed, zero unexplained range violations, every voice that should sound is present, and the bar count is what you meant.

- `check_lines.py` printed `CHECK OK`.
- `SW_WHOLE=1 $W apply_page.py <tag> <lo> <hi> "<title>"` prints the parts with notes in each bar around the edit and the range violations in the edited bars (sounding pitch, from `ranges.py`). Ranges are information, never a mask. Ignore the HTML page and the `localhost:8765` link it also produces; nothing serves that port now.
- Look at the picture (COMPOSING.md section 3). `$W app/render_one.py apply_<tag>_final.xml <scratch>/look <scratch>` writes the same SVG the page will show (plus MuseScore audio and bar times). Screenshot it with headless Chrome on a throwaway profile, `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless --user-data-dir=<scratch>/chrome --window-size=1600,1200 --screenshot=<scratch>/look.png <scratch>/look.svg`, and read the PNG. Eighths beamed across a whole bar and a slur that spans four bars only show up there.
- Read the notes back against the bars before them: register, texture, who plays on the beat. Passing checks do not mean the music works (PROJECT.md sections 30 and 32d).

## Gotchas

- `human_apply.py` keeps bars 1 to `lo`-1 byte for byte. Everything from `lo` on, including bars after `hi`, comes back through the ABC round trip, and `<print>` layout is stripped.
- Continuation lines past the end of the input are appended in order, whatever their `[b:i]` says. Start at exactly the next index.
- `brief.py` caches its reduced ABC in `$E/_scorewright_out/<stem>_reduced.txt` and never refreshes it.
- `_bridge/current_session.txt` beats the session name in the launchd plist. Switch pieces from the page menu.
- `server.py` reads `page.html` once at start. Scripts it runs as subprocesses (`render_one.py`, `listen.py`, `human_apply.py`, the post-processors) pick up changes on the next call, `dorico_render.py` on the next render; a change to `np_agent.py` needs the helper restarted.
- `apply_page.py` ends by copying its HTML into a `/private/tmp/...` scratchpad path hardcoded from an earlier session. When that folder is gone it raises after printing the checks. The checks are what you need.
- Mac GUI automation: untitled dialogs are invisible if you filter or strip window names. List name, subrole and bounds for every window (see `wins()` in `dorico_render.py`), never `.strip()` that output, and look for dialogs before and after every step.
- Dorico 4: menu items are clickable through System Events, its dialog buttons are not. Use keys: Export Audio is Return, the save prompt is Cmd+D (Don't Save), Escape cancels. Export to unique filenames so no overwrite prompt can appear. `dorico_render.py` refuses to render while any Dorico project is open, including one Brian opened himself or with "open in Dorico", so renders wait (retried every 90 s) until he closes it.
- Screenshots: only a window or dialog rectangle (`screencapture -x -R x,y,w,h`), never the full screen. A full-screen capture once caught his university login.
- Sibelius is gone: subscription cancelled Sept 22 2026, ended Sept 27. Dorico 4, with NotePerformer as its default playback template, is the notation app, and "open in Dorico" is the page button.
- Audio files: `media.py` uses PyAV because Homebrew's ffmpeg was broken when uploads were built. Whisper and the piano model load audio through librosa because their own loaders call ffmpeg. (On Oct 9 2026 Homebrew ffmpeg decoded WAV and m4a fine again. Nothing depends on it; leave PyAV in place.)
- The `/tmp` scratchpad is purged after about three days. Durable code and notes go in `lab/`.

## What not to do

- Never edit, rename or write into `$E/MusicXML/`. Treat `$E/extra_sept2026/` the same way. Real titles come from the name map.
- Never edit a session's `working.musicxml` or `state.json` by hand.
- No GPU or API spend without a dry run shown to Brian first: the exact training and decode code on a sample, encoded sizes, skip counts and raw outputs (`lab/PREFLIGHT.md`). He decides.
- No MPS or GPU training on the Mac. For any Mac-side model job: keep the MPS memory ceiling on (never `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0`), 512 patches at most, check `memory_pressure` and swap before and during, tell Brian before it starts, and stop it if per-item times keep climbing. The Mac crashed on Sept 4 2026 when these were ignored.
- Do not propose more NotaGen or Text2Score training without a concrete reason the frontier path cannot cover.
- Do not start a second server by hand. The launchd copy holds ports 8790 and 8791.
- Do not kill or restart processes you did not start: another session's waiter or helper, Brian's Dorico, his browsers.
- Do not try to host NotePerformer outside Dorico. It refuses unsupported hosts, and getting around that check is off the table.
- Do not call a take good because the checks pass. Checks say "not broken". He decides whether it is good.

## Docs

- [README.md](README.md): short overview and quick start
- [docs/architecture.md](docs/architecture.md): components, data flow, `state.json`, every HTTP route
- [docs/surface.md](docs/surface.md): every page feature, and the MuseScore panel
- [docs/playback.md](docs/playback.md): MuseScore audio and NotePerformer through Dorico
- [docs/input.md](docs/input.md): voice, the take button, hum, uploads
- [docs/corpus.md](docs/corpus.md): the archive, retrieval, the export history
- [docs/operations.md](docs/operations.md): running, restarting, logs, troubleshooting
- [docs/history.md](docs/history.md): what was tried, what failed, and why the project pivoted
