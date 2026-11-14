# Dorico playbook

How a suggestion goes into Brian's open Dorico project the moment he presses Accept. Measured on
Nov 13 2026 in 111326 (Dorico 4.0.31, 32 instruments on 36 staves, page view at 150%).

Brian, Nov 13: "the second that you give me the suggestion, you would have already mapped how to
do it... You click accept, it automatically implements it." Before this, the steps were worked out
live after the Accept, with a status read after every move, and S4 took many minutes.

## The flow

1. Read. If he edited since the last export, export again. `edits_since('2026-11-13 19:38:00')` in
   `dorico_rc.py` lists his score-changing commands from Dorico's log, leaving out our own runs.
   Not empty: `dorico_export.py` (about 32 s; it presses Return in his Dorico).
2. Suggest. Build the change from that export, and its plan from the same export with
   `lab/dorico_plan.py` (the plan walks over the score Dorico has now, not over the suggestion).
   Register both: `sw_suggest.py <file> <lo> <hi> "note" --plan plan.json`. The plan is saved
   beside the suggestion as `S<n>.dorico.json`.
3. Accept. `sw_wait.sh` sees `[ACCEPT S<n>]` and runs `sw_on_accept.py` before it prints the line.
   That runs the plan (`dorico_apply.py`), says "Putting S<n> into Dorico now" in the panel, then the
   result. You read `[DORICO S<n>] done: ...` or `STOPPED: ...` in the waiter output. Each run is in
   `$E/_bridge/dorico/apply_log.jsonl` with its time and its short walks.
4. After. STOPPED: the runner already undid its own edits, and the reason names the step. Fix the
   plan, tell him in one line, and run it by hand (`$W app/dorico_apply.py S<n>.dorico.json`). Done:
   the first time a recipe is used, export and compare every note (`pitches()`) and mark (`Marks`)
   with the suggestion; after that the target checks are enough.

A Reject or a comment never touches Dorico.

## Recipes

`p = Plan(export_xml, anchor=('P3', 7, 234, 201))`. The anchor is an item whose page position comes
from his own clicks in Dorico's log (`Edit.SelectAtPoint?X=..&Y=..`); for 111326 it is the oboe's
rest in bar 7. A new piece needs one: a click of his on a rest or note that the status bar names.
Onsets are in quarters from the bar line; `None` as an end onset means the last item of the bar.

| Change | Plan call | Dorico commands |
|---|---|---|
| dynamic | `p.dynamic('P2', 15, 1.5, 'mp')` | `NoteInput.CreateDynamic?Definition=mp&UseLocalOverride=0` |
| articulation | `p.articulation('P2', 16, 0, 'kStaccatoTenuto')` | `NoteInput.SetArticulation?Value=kStaccatoTenuto` |
| slur | `p.slur('P28', (16, 0), (19, None), staves=3)` | a range, then `NoteInput.SlurStart` |
| hairpin | `p.hairpin('P2', (16, 0), (18, 1.0), up=False)` | a range, then `NoteInput.HairpinStart?Type=kGradualDynamicDown&GradualDynamicType=kCrescOrDim` |
| hold a repeated note | `p.tie('P29', 17, 0)` | `NoteInput.Tie` on the first of two equal notes (two tied quarters in 2/4 show as a half note) |
| beams in pairs | `p.split_beam('P3', 10, 1.0)` | `Edit.SplitBeam` on the note that starts the new beam |
| spread a chord part | `p.explode('P9', 8, 16, staves=3)` | the range, `Edit.Copy`; the start, `NavigateDownExtend` x2, `Edit.PasteExplode` (slurs, dynamics and hairpins go to every staff) |
| anything else | `p.step(label, p.at(pid, bar, onset), to=(bar, onset), down=n, edits=[...], plain=[...])` | `edits` are one undo step each; `plain` (like `Edit.Copy`) are none |

Order the steps: one staff at a time, left to right, so most steps get a short walk from the step
before. Ties go last on their staff: a tie merges two items, and the planner refuses a later step
in that bar. After an explode, `p.use(score_after_it)` before steps on the filled staves.
`p.commands()` counts the commands; `p.save(path)` writes the plan.

## Timings

- A selection move (`EventEdit.Navigate*`, `Edit.SelectAtPoint`, `Edit.SelectNone`): 75 to 107 ms,
  one after another. Dorico redraws the page and plays the selected note each time. This sets the pace.
- A caret move in note input: 5 to 36 ms. `NoteInput.MIDINoteInput`: about 22 ms.
- Edits: split beam 125 ms, articulation 134, slur 188, tie 197, hairpin 207, dynamic 213, delete 314.
- A status-bar read: about 190 ms.
- Probe plans: 10 targets on 9 staves, every walk from the anchor: 12.3 s. 8 targets on 3 staves,
  5 short walks: 4.5 s.

## How Dorico takes commands

- It answers a command when it queues it (a few ms) and decides then whether the command is allowed,
  against the selection at that moment. It carries the command out later, then pushes
  `selectionchanged` (twice) and a `status` with `hasSelection`. So: after the start click, wait for
  `selectionchanged` before the walk. With nothing selected, `NavigateRightBar` is refused.
- `NavigateRightExtend` n times, with n counted from the export, ends on the last item of the target
  bar exactly (tested on horn 1, violin I and the oboe). `NavigateRightExtendBar` is not reliable:
  8 presses gave 4 to 12 bars.
- `NavigateDown` and `NavigateUp` pass each note of a chord, then the next staff.
  `NavigateDownNextStave` goes to the bottom staff, not the next one.
- With nothing selected, `NavigateRight` selects the bar-1 time signature, where no move works.
- `NoteInput.Exit` puts the selection back where it was before note input, so the fast caret cannot
  pick a target. `Edit.GoTo` (Go To Bar) moves only the view. `Edit.SelectAtEndOfFlow` selects a
  range to the end of the flow.
- The MusicXML export has no layout (no positions), so a click position for any note cannot be
  computed. The only known positions are his own clicks in the log.
- The log has our commands too. `Remote Control Client N connected` and `socket disconnected` frame
  our runs; `edits_since` leaves them out.
- Not yet known: whether a note tied from the bar before is a separate item for the arrows. The
  planner refuses walks and ranges over one. Test it on the first plan that needs it.

## Note entry (not in plans yet)

From his log: `NoteInput.Enter?Set=true` (caret at the selection), `NoteInput.NoteValue?LogDuration=kQuaver&Set=true`
(also kSemiquaver, kCrotchet, kMinim), `NoteInput.SetDotted?Value=1&Set=true`,
`NoteInput.MIDINoteInput?MIDIPitches=72` or a chord `MIDIPitches=60\,64\,67` (concert pitch in his
concert-pitch layout), `NoteInput.MoveRight` (one grid step; his grid is an eighth),
`NoteInput.MoveRightBar`, `NoteInput.MoveDown` (next staff),
`NoteInput.StartTupletRun?Definition=3:2&Set=true` and `Set=false`, `NoteInput.Exit`. Insert is
off, so new notes overwrite. Before a plan uses these, measure how many undo steps one
`MIDINoteInput` makes: the runner's undo count depends on it.

## Faster later

- A second start point near the target bars: one of his recent clicks from the log, named by the
  notes around it in a fresh export. Saves up to about 1 s a step in far bars.
- Read the status bar through the accessibility API in-process (pyobjc) in place of osascript:
  about 190 ms to about 20 ms a target.
