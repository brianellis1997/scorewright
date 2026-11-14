# Dorico playbook

How a suggestion goes into Brian's open Dorico project the moment he presses Accept, in any score
(piano, chamber, orchestra), with any instruments and any layout. Measured on Nov 13 2026 in
111326 (Dorico 4.0.31, 32 instruments on 36 staves, page view at 150%).

Brian, Nov 13: "the second that you give me the suggestion, you would have already mapped how to
do it... You click accept, it automatically implements it." And: "What if my score changes? What if
I add an instrument?... Is this a generalizable design?"

## The idea

Dorico's remote-control link takes commands only; it cannot say where a note is. But every note has
internal IDs, and `EventEdit.Select?FlowID=0&EventID=14&EventBlockID=8` selects that note with one
command (about 150 ms). The IDs are in Dorico's autosave of the project
(`~/Library/Application Support/Steinberg/Dorico 4/AutoSave/<project>.dorico`), which
`lab/dorico_file.py` reads in about 0.07 s: every note with its IDs, instrument (the MusicXML part
name), staff, bar, onset and sounding pitch. So no click positions and no layout: a plan names its
targets musically (part, staff, bar, onset, pitch) and the runner looks the IDs up when it runs.

A note the plan writes itself has no ID yet: Dorico refuses `File.AutoSave` over the link (kError)
and autosaves on its own only every few minutes. Such a target is reached from the nearest note that
has an ID (`via`: the same staff earlier, or a staff above, then arrows), or from where the step
before left the selection (`rel`; after note entry the last typed note stays selected).

## The flow

1. Read. If he edited since the last export (`edits_since` in `dorico_rc.py`), export again with
   `dorico_export.py` (about 6 s; it presses Return in his Dorico). Read it as pages
   (`reading_copy.py`, then `engrave_pages.py`), at concert pitch.
2. Suggest. Build the change from that export (pieces like `lab/pieces/p111326_s6.py`) and its plan
   from the same export (`lab/pieces/p111326_s6_dorico.py` and `lab/dorico_plan.py`), with the
   score states the plan walks over (after a paste, after the new lines). Register the suggestion
   with `sw_suggest.py ... --plan plan.json`, or copy the plan to `S<n>.dorico.json` in the session.
3. Probe. `$W app/dorico_apply.py S<n>.dorico.json --probe` jumps to every start that has an ID,
   checks it in the status bar, and places each caret, but types and edits nothing.
4. Accept. `sw_wait.sh` sees `[ACCEPT S<n>]` and runs `sw_on_accept.py` before it prints the line:
   the plan runs (`dorico_apply.py`), the panel says "Putting S<n> into Dorico now", then the result.
   After a full run it exports the project and compares it with the suggestion (`lab/dorico_check.py`),
   and the panel and the waiter output (`[DORICO S<n>] done: ... CHECK: ...`) say what differs. Each run
   is logged in `$E/_bridge/dorico/apply_log.jsonl`.
5. After. A stop happens before the step whose target does not match, and the steps before it stay
   in. Fix that step, say so in one line, and go on: `dorico_apply.py S<n>.dorico.json --from k`.
   The first time a recipe runs, export and compare every note (`xml_marks.pitches`) and mark.

A Reject or a comment never touches Dorico.

## Never undo blindly

Dorico's undo history holds every selection move ("Undo Select"), every caret move ("Undo Move
Caret Up"), every typed note ("Undo Input Note") and every mark ("Undo Note Input"). A count of
edits says nothing about how many undo steps a run made. So runs fix forward. If something must be
taken back, undo one step at a time while reading the Edit menu's first item, and stop at a known
title; then export and compare with the export from before (that is how the Nov 13 test notes in
bars 50-52 were removed, 48 undo steps in all).

## Recipes (Plan methods)

| Change | Plan call | Dorico commands |
|---|---|---|
| dynamic | `p.dynamic('P2', 15, 1.5, 'mp')` | `NoteInput.CreateDynamic?Definition=mp&UseLocalOverride=0` |
| articulation | `p.articulation('P2', 16, 0, 'kStaccatoTenuto')` | `NoteInput.SetArticulation?Value=kStaccatoTenuto` |
| playing technique | `p.technique('P31', 24, 0, 'pizz.')` | `NoteInput.CreatePlayingTechnique?Definition=pizz.`: the popover text. `Definition=pt.pizzicato` does nothing (7 ms, no error) |
| slur | `p.slur('P28', (25, 1.0), (26, 0), staves=1)` | a range, then `NoteInput.SlurStart` |
| hairpin | `p.hairpin('P3', (22, 1.0), (24, 0), up=False)` | a range, then `NoteInput.HairpinStart?Type=kGradualDynamicDown&GradualDynamicType=kCrescOrDim` |
| hold a repeated note | `p.tie('P10', 14, 0)` | `NoteInput.Tie` on the first note: it ties to the next note of that pitch |
| beams in pairs | `p.split_beam('P3', 10, 1.0)` | `Edit.SplitBeam` on the note that starts the new beam |
| respell | `p.respell('P6', 25, 0, up=True)` | `NoteEdit.RespellUsingNoteNameAbove` (E sharp to F) or `...Below` |
| spread a chord part | `p.explode('P5', 24, 31, staves=3)` | the range, `Edit.Copy`; the start, `NavigateDownExtend` x2, `Edit.PasteExplode` |
| new notes | `p.notes('P3', 18, 0, [('G4', 1), ('A4', 1, 'tie'), (None, 0.5)])` | select a note with an ID, `NoteInput.Enter?Set=true`, caret moves, then for every note `NoteInput.NoteValue?LogDuration=kCrotchet&Set=true` and, only for a dotted note, `NoteInput.SetDotted?Value=1&Set=true`; then `NoteInput.MIDINoteInput?MIDIPitches=67` (a chord: `60\,64\,67`); `NoteInput.Tie` after a note ties it to the next typed note; `NoteInput.Exit` |
| insert bars | `p.insert_bars(3, 1, check=('P3', 7, 1.0))` | `NoteInput.CreateBarLine?Duration=2\, 1&RhythmicPosition=4\, 1&RhythmicPositionIncludesLeftOfNotes=1&FlowID=0`: time in quarters as `n\, d` (the form Dorico logs for the system track's insert); then the check note, by its ID, must be one bar later. `CreateBarLine?Value=10&Location=End` adds bars at the end |
| anything else | `p.step(label, pid, bar, onset, to=(bar, onset), down=n, edits=[...], plain=[...])` | |

Order the steps so that every ID is still valid when it is used: a tie merges two notes into one
event (the second loses its ID), a paste makes new notes. In S6: the paste and its marks first, then
the new lines, then the marks on them, then every tie between existing notes, right to left on each
staff. Call `p.use(xml)` with the score as it is after a step that changes what later steps count.

## Note entry traps (learned in the S6 run, Nov 13)

Every stop and every difference the check finds gets its cause and its rule here, in the same commit
as the fix (Brian: "we're learning from our mistakes as we go on").

- A plan that builds on another suggestion names it: `p.save(path, requires=['S7'])`. If that
  suggestion's plan has not run, the Accept hook runs it first, withdraws it in the panel ("included
  in S9"), waits for the autosave, then runs the plan. (Nov 13: S9 was accepted before S7 and stopped
  at step 1, with no change, because the bar it looked for had not moved yet.)

- Note values: use the names in Dorico's key-command file: kSemibreve, kMinim, kCrotchet, kQuaver,
  kSemiQuaver, kDemiSemiQuaver. `kSemiquaver` (small q) is accepted without an error and types
  whole notes: the harp's sixteenths came in two bars long.
- A new note value clears the dot, and `SetDotted` toggles it. `SetDotted?Value=1&Set=false` right
  after a new value turned the dot ON, and Violin I came in a quarter too long. So send the value
  before every note, the dot only for a dotted note, and never `Set=false`.
- MIDI pitch 68 comes in as A flat. Respell where the plan has G sharp
  (`NoteEdit.RespellUsingNoteNameBelow`), or plan the respell steps with the notes.
- Typing over a region leaves the tail of a longer old note that started earlier. To clear a region,
  start the range at the first item of its first bar on every staff (the harp kept two E3 tails).
- The MusicXML export leaves playing techniques out. Check them in Dorico: select the note, then
  `EventEdit.NavigateNextItemSamePosition` shows "Playing technique: Pizzicato".

The S6 run: steps 1-18, a stop at 19 (a bar jump over a tied note, see below), steps 19-25, a stop
at 26 (a range too long, from the dot error), a repair plan (`lab/pieces/p111326_s6_repair.py`, 8
steps), steps 26-56, three finish steps. Then a fresh export matched S6 in every note, spelling,
rhythm and tie. Every stop came before an edit at the wrong place.

## Marks on typed notes, and carets in empty bars (S8, Nov 13)

- After a mark (dynamic, slur, hairpin, technique) Dorico selects the new mark. A typed note has no
  ID, so the next step cannot jump back to it. `restore` steps through the items at that place with
  `EventEdit.NavigateNextItemSamePosition` (Note, Playing technique, Dynamic, Note...) until the
  status bar shows the note again. So the marks for a new line go right after its note entry, each
  starting from the last typed note (Dorico leaves it selected after `NoteInput.Exit`).
- An introduction has no notes before it. The caret then starts at a note with an ID in a later bar
  (or on a staff below) and moves with `NoteInput.MoveLeftBar` and `NoteInput.MoveUp`.
- After a run that moved notes (inserted bars), the autosave still has the old bars until Dorico
  autosaves again (every few minutes; `File.AutoSave` over the link returns kError). The Accept hook
  waits for that autosave before the next plan.

## Timings (111326, 36 staves)

- Select by ID: about 150 ms. A selection move with the arrows: 75 to 107 ms; Dorico redraws the
  page and plays the selected note each time.
- A caret move in note input: 5 to 36 ms. A typed note (`MIDINoteInput`): about 22 ms.
- Edits: split beam 125 ms, articulation 134, slur 188, tie 197, hairpin 207, dynamic 213, delete 314.
- A status-bar read: about 190 ms.
- The S6 probe: 56 steps, every ID start found and every caret placed, in about 25 s. The real run:
  steps 19-25 in about 10 s, steps 26-56 in 21 s, the repair (two retyped passages) in 21 s.

## How Dorico takes commands

- It answers a command when it queues it (a few ms) and decides then whether the command is
  allowed, against the selection at that moment. It carries the command out later, then pushes
  `selectionchanged` (twice) and a `status` (`hasSelection`, `noteInputActive`). So wait for
  `selectionchanged` after a jump, and for `noteInputActive` after `NoteInput.Enter`.
- `EventEdit.Select` selects one note; it ignores `AddToSelection` and `BlockSelection`. A range is
  the start by ID, then `NavigateRightExtend` n times (n counted in the plan; exact, tested), plus
  `NavigateDownExtend` for more staves. `NavigateRightExtendBar` is not reliable (8 presses gave 4
  to 12 bars).
- A tie chain is one note event and one item: the arrows stop once on it, and the status bar shows
  "Bars 24-25" with its "Note: E5" (the bar is the first). A range that ends on it covers it to its
  last bar. `NavigateRightBar` from it jumps to the first item of the first bar after the tie ends,
  so it skips the bars the tie covers (the planner simulates this, `Plan.walk`).
- `NavigateDown` and `NavigateUp` pass each note of a chord, then the next staff;
  `NavigateDownNextStave` goes to the bottom staff. With nothing selected, `NavigateRight` selects
  the bar-1 time signature, where no move works.
- `NoteInput.Exit` after typing leaves the last typed note selected; without typing it puts the
  selection back. `NoteInput.MoveDown` moves the caret one staff, `MoveRightBar` to the next bar's
  start, `MoveRight` one grid step (his grid is an eighth).
- MIDI note input goes in at concert pitch in his concert-pitch layout (cor anglais: MIDI 69 is A4).
- `Edit.GoTo` (Go To Bar) moves only the view. `Edit.SelectAtEndOfFlow` selects a range to the end.
  `Edit.SelectAll` then an arrow starts from whatever Dorico last had in focus.
- The MusicXML export has no layout, so click positions cannot be computed; they are not needed.
- The log has our commands too. `Remote Control Client N connected` and `socket disconnected` frame
  our runs; `edits_since` leaves them out.
