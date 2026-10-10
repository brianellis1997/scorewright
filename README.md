# Scorewright

A copilot for composers. Private project.

Brian composes, and has 1,607 of his own scores exported from Sibelius to MusicXML. Scorewright lets Claude Code compose with him the way it codes with a programmer. It reads his whole score, pulls examples from his own archive, writes new bars in ABC, splices them into his MusicXML, and shows them in green on a phone-friendly page. He listens, then accepts or rejects with a spoken reason. Every verdict is logged, and those verdicts are the evaluation set the harness is tuned against.

There is no trained music model in the loop. Training was tried first (NotaGen, Text2Score, a $50 GPU day). Its continuations scored 0 or 1 out of 5; the one exception was a four-bar left-hand fill that got a 3. Claude reading the whole piece and writing the bars itself scored 3 and 4 the same day. [docs/history.md](docs/history.md) tells that story.

## How it works

- `lab/app/server.py` runs under launchd and serves the page on port 8790, on the Mac and on the phone through Tailscale.
- Brian talks, types, plays (🎹 with a MIDI keyboard or the mic), hums (🎵) or uploads a recording (📎). Everything he says lands in `_bridge/queue/inbox.jsonl`.
- A Claude Code session waits on that inbox, composes by the procedure in [lab/COMPOSING.md](lab/COMPOSING.md), and registers the result as a suggestion.
- The page draws the suggestion with Verovio, the new bars green, and plays it: MuseScore audio within seconds, NotePerformer through Dorico 4 a minute or so later.
- Accept makes it the working score; Reject keeps the old one. Both go to `_bridge/verdicts.jsonl` with his words.

## Quick start

For Brian:

1. Open http://localhost:8790 on the Mac, or https://macbook-pro.tail2783bf.ts.net on the phone with Tailscale on.
2. In Claude Code, in `~/repos/scorewright`, ask it to start the Scorewright loop. It follows the checklist in [CLAUDE.md](CLAUDE.md) and starts two background helpers: the inbox waiter and the NotePerformer renderer.
3. Pick a piece in the header menu, or "New piece" for an empty score.
4. Say what you want, or press ▶ continue. Accept or Reject each suggestion, then say why.
5. "open in Dorico" opens what you are looking at in Dorico 4, green notes kept, with NotePerformer.

For a Claude Code session: read [CLAUDE.md](CLAUDE.md), then [lab/COMPOSING.md](lab/COMPOSING.md).

## Requirements

- macOS, with the conda envs `whisperer` (nearly everything) and `text2score` (`human_apply.py`, `dump_abc.py`), plus the anaconda base python for `hum.py`. Never a bare `python`.
- Dorico 4 with NotePerformer 5 (its default playback template), MuseScore 4, Tailscale.
- The data folder `~/Documents/Score Exports`: the archive, the retrieval index, the session folders, the bridge files. It is not in the repo.

## Layout

| path | what |
|---|---|
| `CLAUDE.md` | operating manual for Claude Code sessions |
| `lab/COMPOSING.md` | the composing procedure and the rules learned from his verdicts |
| `lab/app/` | the server, the page, rendering, NotePerformer, input transcription, the MuseScore panel |
| `lab/*.py` | composing tools, plus scripts from the training phase |
| `lab/band/` | the concert band orchestration of Bright Valley |
| `lab/songs/` | build scripts for whole new pieces: `where_i_left_it.py` (S1, too pop), `where_i_left_it_s2.py` (S2, odd), `where_i_left_it_s3.py` (S3, in his song-study grammar), English horn and piano with words |
| `lab/style_profile.py` | measures a composer's harmonic and melodic habits from their scores and flags where a draft falls outside them |
| `lab/rh_profile.py` | what the accompaniment's right hand does against the melody: doubling, thirds and sixths, fills in the melody's rests |
| `lab/lint_line.py` | checks a melody for wrong-way accidentals, unrecovered or augmented leaps, phrases too long to breathe, range |
| `lab/harmony_index.py`, `lab/find_progression.py` | index the harmony of all 1,655 scores; find a progression in any key and show the melody he wrote over it |
| `lab/reduce_harmony.py` | prints a score as a lead-sheet reduction, one line per bar (chords, bass, melody, accompaniment rhythm), to read many pieces fast |
| `lab/NotaGen/` | git submodule; its ABC converters are used by the pipeline |
| `*.py` at the root | `xmledit.py`, `diffview.py`, `retrieve.py`, `ranges.py`, `analyze.py`, and the August prototypes |
| `deploy/` | the launchd plist |
| `docs/` | the documentation below |

## Docs

- [docs/architecture.md](docs/architecture.md): components, data flow, `state.json`, HTTP routes
- [docs/surface.md](docs/surface.md): the page and the MuseScore panel
- [docs/playback.md](docs/playback.md): MuseScore and NotePerformer audio
- [docs/input.md](docs/input.md): talk, take, hum, upload
- [docs/corpus.md](docs/corpus.md): the archive, retrieval, the export history
- [docs/operations.md](docs/operations.md): running, restarting, logs, troubleshooting
- [docs/history.md](docs/history.md): what was tried and why it changed course

The living spec, with every measurement, is `~/Documents/Score Exports/PROJECT.md`.
