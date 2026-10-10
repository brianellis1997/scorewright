# The surface

The page Brian works in, served by `lab/app/server.py` from `lab/app/page.html`, and the MuseScore panel that mirrors it.

- Phone: https://macbook-pro.tail2783bf.ts.net (Tailscale must be on, tailnet only)
- On the Mac: http://localhost:8790

## Layout

On a desktop the chat sits in a left column (280 to 380 px) and the score fills the rest. At 800 px wide or less the page becomes one column: the score on top at about half the screen height, the chat below, larger buttons, a toolbar that scrolls sideways, and the desktop-only controls hidden. The page itself never scrolls sideways; only the score pane scrolls. Dark mode follows the system setting, and the score keeps a white background in both.

## Header: pieces

The menu on the right of the header lists every piece (a session folder with a `state.json`), newest first, by title, plus "＋ New piece…". Picking a piece switches the server to it and reloads the page. The choice is saved in `_bridge/current_session.txt`, so a server restart comes back to the same piece, and every device sees the switch on its next poll.

"New piece" opens a form:

| field | values |
|---|---|
| Title | required; the folder name is made from it (`Improvisation in D minor` becomes `improvisation-in-d-minor`, with `-2`, `-3` if taken) |
| Instruments | Solo piano, String quartet, Piano trio, Voice and piano, Violin and piano, Cello and piano, String orchestra |
| Key | free text, default C. "D minor" becomes `Dm`, "Bb" stays `Bb` |
| Meter | 4/4, 3/4, 6/8, 2/4, 5/4, 12/8 |
| Tempo | quarter = 30 to 240, default 90 |

The server writes an ABC file with the preset's staves (piano gets a braced treble and bass pair) and eight empty bars, converts it with NotaGen's `abc2xml.py` to `start.musicxml`, makes that the working score, posts a greeting in the chat, and writes `[NEW PIECE <name>] <title>: <preset>, <key>, <meter>, quarter=<tempo>` to the inbox. From there he can talk, play, or upload something.

## Chat column

- His messages sit on the right in blue, Claude's on the left in green, each with "you" or "Claude" and the time.
- A suggestion shows as a green-bordered card: id, bars, status (open, accepted, rejected, withdrawn), and Claude's note. While it is open it has Accept, Reject and show buttons. "show" puts that suggestion in the score pane and scrolls to its first bar.
- A take or upload he sent shows its rendered staff under the message.
- The log keeps its scroll position unless it was already at the bottom.

Under the log is the input row: 🎤 talk, 🎵 hum, 🎹 take, 📎 upload, the text box, Send and ＋ Review. On a phone the text box gets its own full-width row above the buttons. Enter sends, Cmd or Ctrl+Enter adds to the review, Shift+Enter makes a new line. The text box saves every keystroke on the device, so a draft survives a reload, and clears on send. When bars are selected, Send puts them in front of the message (`[S10 bars 45–48] ...`). The four buttons are described in [input.md](input.md).

## Review comments

A review works like a pull-request review: comments on passages collect in a draft and reach Claude together, so he is never mid-change while Brian is still reviewing (Oct 10 2026).

- Select a bar or a passage in the score pane (below), say or type the comment, press ＋ Review. With nothing selected the comment is general. The selection clears after each comment.
- "Your review · N comments" appears above the input row: each comment with its suggestion and bars (amber), × to remove it, a tap to show those bars. The commented bars are shaded amber on the score.
- Submit review sends them all. Text still in the box is added as one more comment first.
- The draft lives on the server (`review` in `state.json`, `/api/review`), so it survives reloads and is the same on the phone and the desktop.
- On submit the server writes one chat entry, one inbox line `[REVIEW S<n>] k comments` with a line per comment (the JSON also carries the list as `review`), and one `verdicts.jsonl` record per suggestion commented on: `verdict: "CHANGES REQUESTED. ..."`, `source: "ui-review"`, with the comments.

Dorico does not export its own comments (not in MusicXML, not as a file). Its Remote Control API can read the current selection, which is the way to comment on single notes from Dorico later.

## Accept and Reject

Pressing Accept or Reject records the verdict at once with no text. Then the text box placeholder changes:

- after Accept: "Accepted S<n>. Talk or type what you want next, or press ▶ continue to let Claude propose"
- after Reject: "Rejected S<n>. Why not? talk or type", and the mic starts listening by itself

Whatever he sends next is stored as that suggestion's reason (`/api/verdict_note`): added to the suggestion's verdict text, logged in `verdicts.jsonl`, and delivered to Claude as `[S<n> reason] ...`. After an Accept that next message is often his next request, and Claude should read it that way.

On Accept the suggestion's clean score becomes the working score and any other open suggestion is rebuilt on top of it. The working view reuses the accepted suggestion's render, so the accepted bars still look green, with the suggestion label, until the working score is rendered again.

## Score pane

The toolbar, left to right:

- what is showing: "working score" or "suggestion S<n> (green = new)", plus "· bar N selected" or "· bars N–M selected"
- ↔ to… and × (only while something is selected): ↔ then a tap on another bar extends the selection to that passage; × clears it
- a hint, desktop only: click a bar to select it, shift-click to extend, P or space plays from there, press again to stop, ← → move the selection
- zoom out and zoom in (the minus and plus buttons): steps of 1x, 1.5x, 2x and 3x of the pane width, remembered per device. Zooming keeps the selected bar (or the suggestion's first bar) in view.
- working: show the working score
- latest suggestion: hidden when nothing is open. When a newer open suggestion arrives it turns green and reads "new: S<n> (click to show)".
- ▶ play: plays from the selected bar, or bar 1. Its label says "▶ play" while only MuseScore audio exists, "▶ play (NotePerformer rendering)" while a render is queued, and "▶ NotePerformer" once that audio is in.
- ▶ continue: sends `[CONTINUE] propose the next bars from where the working score stops` as a message
- open in Dorico, open in MuseScore (desktop only): open the green copy of the suggestion being shown, or the working score, in Dorico 4 or MuseScore 4 on the Mac

The score is a Verovio SVG of the whole piece on one long page. A suggestion is drawn from its green copy: the new bars' notes and rests are green, "▶ Scorewright suggestion: bars lo-hi" sits over the first one, a dashed green bracket spans the region, and "◀ end of scorewright suggestion" marks the bar after it.

Clicking a bar selects it with a blue box. The hit test runs per bar in its own coordinate system and picks the tightest bar under the click, because slurs and hairpins inflate their neighbours' boxes. On the phone, tap a bar, then ▶ play.

Keys (ignored while typing): P or space toggles playback from the selected bar (the first bar of a passage), Escape stops, ← and → move the selection one bar, Shift+← and Shift+→ shrink or grow a passage. Playback seeks to the bar's start time from `<id>.bars.json`. If the audio is not rendered yet the page says "audio still rendering, try again in a few seconds". See [playback.md](playback.md).

## Live updates

The page polls `/api/state` every 2 s. It redraws the chat only when the chat or the suggestions changed, and it never switches what he is looking at; a new suggestion only lights the button. When NotePerformer audio arrives for the view on screen and nothing is playing, the page drops the old audio so the next play loads the new one.

The whole page reloads when the server has restarted (`page_version` changed) or the current piece changed. The reload waits while 🎤 or 🎵 is recording. A 🎹 take in progress is not protected, so do not restart the server while he is playing.

When the page first loads it shows the newest open suggestion, or the working score if none is open.

## MuseScore panel

`lab/app/Scorewright.qml`, installed as `~/Documents/MuseScore4/Plugins/Scorewright/Scorewright.qml` for MuseScore Studio 4.7. It has to be enabled once in MuseScore's plugin manager. It is a 420 by 640 dialog that connects to `ws://localhost:8791` when run.

- status line: connected, and the working score's file name
- auto-open (on by default): every new suggestion's green copy opens as a new score tab
- reconnect
- the chat, with Open, Accept and Reject on open suggestions
- a "why" box whose text goes with the next Accept or Reject, so the reason is in the same verdict record
- a message box (Enter sends; the macOS dictation key works there)

The panel only works on the Mac itself; port 8791 is not exposed through Tailscale. Note entry happens in MuseScore or Dorico; the page is the remote.

## What it does not do

- No note entry in the page, and no undo other than rejecting a suggestion.
- No login. The server listens on all interfaces, so anything that can reach port 8790 can use it. Phone access is meant to go through the tailnet.
- The server still accepts `app=Sibelius` on `/open`, but there is no button for it. Sibelius dropped to the free Sibelius First tier when the subscription ended on Sept 27 2026.
