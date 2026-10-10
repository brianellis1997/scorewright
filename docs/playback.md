# Playback

Every score the page can show (the working score and each suggestion) gets audio twice. MuseScore's command line renders it within seconds so there is always something to play. Then Dorico 4 with NotePerformer renders it again, which takes 35 to 90 seconds, and that audio replaces the first. NotePerformer is the listening Brian trusts.

## MuseScore audio, the instant fallback

`lab/app/render_one.py <score> <out_stem> <session_dir>` runs after every registered suggestion, every change of working score, and on `/api/rerender`. One run at a time (the server's `render_lock`), each in a fresh process.

- SVG: Verovio through `diffview.render`, the whole score on one page, written to `<stem>.svg`.
- Audio: `/Applications/MuseScore 4.app/Contents/MacOS/mscore -o <session>/audio_<key>.mp3 <score>`, windowless, 180 s timeout. `<key>` is the first 12 hex digits of the md5 of the file path plus its modification time, so an unchanged file is never rendered twice. The mp3 goes into `<stem>.audio.txt` as a `data:audio/mpeg;base64,...` URI, which is what `/audio?id=` returns.
- Sounds: MuseScore's own engine. Muse Hub is installed; Muse Sounds play if their packs have been installed inside it.
- Bar times: music21 parses the score and walks the first part's measures, adding each bar's length at the current tempo (the first metronome mark seen in a bar, 120 if none). The result, `[[bar, seconds], ...]`, goes to `<stem>.bars.json`, and the page seeks with it.

## NotePerformer through Dorico 4

NotePerformer runs only inside the notation programs it supports: Sibelius, Finale and Dorico. Its AU refuses any other host ("NotePerformer AU only supports MakeMusic Finale"), and MuseScore is not supported. Working around that check is off the table. So Scorewright drives Dorico to export the audio.

Setup facts:

- NotePerformer 5 (5.1.2), perpetual licence. A fresh installer comes through the request form at wallanderinstruments.com/request; the link arrives by email.
- Dorico 4's default playback template is NotePerformer: `~/Library/Application Support/Steinberg/Dorico 4/Preferences.xml` sets `defaultPlaybackTemplate` to `playbacktemplate.noteperformer`. Any MusicXML opened in Dorico plays through it with no per-file setup.
- Dorico imports the green note colour and the "Scorewright suggestion" text, so "open in Dorico" shows the suggestion in context. Sibelius dropped the colour.

### The queue

1. After each MuseScore render the server queues a NotePerformer job for the same file, unless one is already pending or the score has no pitched notes. At start, and on every piece switch, `np_catch_up` queues the working score and every open suggestion whose `.np.m4a` is missing or older than the score.
2. `lab/app/np_agent.py` asks `/api/np/claim` every 4 s (every 10 s while the server is unreachable). For a job it takes `_bridge/heavy.lock`, runs `dorico_render.py <xml> <stem>` with its own python (900 s timeout), and reports to `/api/np/done` with the return code and the end of the output. It prints one line per job: time, stem, return code, last output line.
3. The server acts on the code:

| code | meaning | server does |
|---|---|---|
| 0 | audio written | sets `np_audio[<stem>]`; the play button turns into "▶ NotePerformer" |
| 1 | failed | drops the job |
| 2 | busy: a Dorico project or dialog was already open | retries after 90 s |
| 3 | this process may not control other apps | retries after 300 s; the helper also sleeps 60 s |

Codes 2 and 3 are retried up to 40 times. The queue lives in memory, so a server restart empties it, and `np_catch_up` refills it for the working score and open suggestions.

### What `dorico_render.py` does

1. Checks permission: asks System Events for a process name; "not allowed assistive access" means exit 3.
2. Refuses with exit 2 if any Dorico project window or dialog is open. It never touches Brian's own work. The Steinberg Hub window does not count.
3. Copies the MusicXML to a temporary folder under a unique name (`sw_<stem>_<epoch>.musicxml`), so the exported audio name is new and Dorico never asks to overwrite.
4. Opens the copy with `open -a "Dorico 4"` and waits up to 300 s for the project window, then 120 s more (a late window is closed, and the run fails).
5. Fails if a dialog appears right after opening.
6. Clicks File > Export > Audio... through System Events (up to three tries), then sends Return to the Export Audio dialog, with `activate` and `AXRaise` of the dialog in the same AppleScript. Sends Return once more if the dialog is still there.
7. Waits up to 300 s for a new `sw_*` WAV, FLAC or MP3 under `~/Documents/Dorico Projects/` whose size holds still for 3 s.
8. Always closes the project: Escape any dialog (after a screenshot), File > Close Project (up to three tries; Dorico reports it disabled yet obeys a retry), Cmd+D to answer "Save changes?" with Don't Save. Deletes the temporary folder.
9. Normalises the peak to 0.89 (about -1 dBFS), encodes AAC at 160 kbps with `afconvert` to `<stem>.np.m4a`, writes `<stem>.audio.txt` as `data:audio/mp4;base64,...`, and deletes the exported file and any empty folder Dorico made for it.

Any unexpected dialog is screenshotted, only its own rectangle, to `_bridge/dorico_debug_<step>_<n>.png` before the script gives up.

### GUI rules this code follows

Learned the hard way on Sept 22 2026, when a hidden overwrite prompt blocked Dorico for minutes:

- Most dialogs are untitled. A window list that filters or strips empty names never sees them. List name, subrole and bounds for every window (`wins()`), and never `.strip()` the AppleScript output: an untitled dialog's row starts with a tab.
- Check for dialogs before starting and after every step. Confirm each click with the window list.
- Dorico's menu items are clickable through System Events; its dialog buttons are not. Use keys: Return for Export Audio, Cmd+D for Don't Save, Escape to cancel an overwrite prompt. Cmd+W does nothing; use File > Close Project.
- Avoid dialogs by design: unique export names, and refuse to start when anything is already open.
- Screenshot only the dialog's rectangle (`screencapture -x -R x,y,w,h`), never the whole screen.

### Why the helper runs in the Claude Code session

macOS answers "osascript is not allowed assistive access" when the launchd server tries to drive another app, and the Claude Code session's process is trusted. So `np_agent.py` runs as a background task of the session (see the checklist in [CLAUDE.md](../CLAUDE.md)). To make it independent, Brian grants Accessibility to the whisperer python (`/Users/bdogellis/miniforge3/envs/whisperer/bin/python`) once in System Settings > Privacy & Security > Accessibility; then the helper can run as its own launchd job. On Oct 9 2026 there was no such job; the helper ran from a Claude Code session.

## How it plays out in the page

- `/audio?id=` returns whatever `<stem>.audio.txt` holds: MuseScore audio first, NotePerformer once it lands.
- The play button reads "▶ play", then "▶ play (NotePerformer rendering)" while the stem is queued, then "▶ NotePerformer".
- Any new render of a stem (a rebase, `/api/rerender`) puts the MuseScore audio back and queues NotePerformer again.
- On Accept the working score takes over the suggestion's NotePerformer audio if it had any; otherwise a render is queued for it.

## Living with Dorico

- When Brian presses "open in Dorico", that project stays open, and every render in the queue is refused as busy until he closes it (retried every 90 s, up to 40 times, about an hour).
- Renders and upload transcriptions share `_bridge/heavy.lock`. Dorico once missed its open timeout while a transcription was running; now one waits for the other.
- Renders steal focus: Dorico is activated for each one. Mention it if he is working on the Mac.

## The older audio path

`diffview.audio()` turns MusicXML into MIDI with a custom writer (`midiwrite.py`: one track and channel per part, General MIDI programs from part names, ties merged, the score's own tempo) and plays it through FluidSynth with the FluidR3 GM soundfont. The root `render_audio.py` does the same for a whole archive score with music21's MIDI writer. This path made the audio for the August HTML diff pages and still backs `show.py`. The surface does not use it. Its history explains a lot of early verdicts: until Aug 29 every transposing instrument played at written pitch (out of tune), all parts once collapsed onto one MIDI channel, and every piece played at 120 until Sept 4. See PROJECT.md sections 32, 40a and 52g.
