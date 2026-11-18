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
3. Check. `$W app/dorico_apply.py S<n>.dorico.json --check` finds every note the plan selects by ID
   in the newest copy of his project (the autosave, or the file Dorico last saved) and sends nothing
   to Dorico. The live `--probe` also reads each start in the status bar and places each caret, but
   it moves the selection, enters note input and plays every selected note in his Dorico: on Nov 14
   he saw that with no word in the panel ("You're changing my actual Dorico score"). Use it only
   when he is away, and say so in the panel first.
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
| spelling of a typed sharp or flat | `p.spell('P31', 3, 0)` | the runner reads the note and sends `NoteEdit.RespellUsingNoteNameBelow` (or `...Above` for a flat) only when Dorico shows the other name; the run report counts the fixes |
| shorten a note that stays | `p.shorten('P30', 60, 0, 2)` | `EventEdit.DurationShortenByGrid` n times (grid: an eighth); one step per chord note, each selected by its own ID |
| tuplets in note entry | events `('tuplet', '6:4')`, notes at their written value (1/4), `('end tuplet', '6:4')` | `NoteValue` first, then `NoteInput.StartTupletRun?Definition=6:4&Set=true`, the notes, `...&Set=false` |
| move an existing note by scale steps | `p.pitch('P6', 2, 0, 2)` | `NoteEdit.PitchUp` (Alt+Up) n times, `NoteEdit.PitchDown` for down: the note keeps its ID, ties, slurs and dynamics, so it beats retyping one note |
| new notes | `p.notes('P3', 18, 0, [('G4', 1), ('A4', 1, 'tie'), (None, 0.5)])` | select a note with an ID, `NoteInput.Enter?Set=true`, caret moves, then for every note `NoteInput.NoteValue?LogDuration=kCrotchet&Set=true` and, only for a dotted note, `NoteInput.SetDotted?Value=1&Set=true`; then `NoteInput.MIDINoteInput?MIDIPitches=67` (a chord: `60\,64\,67`); `NoteInput.Tie` after a note ties it to the next typed note; `NoteInput.Exit` |
| a caret from a named note | `p.notes('P26', 1, 0, events, staff=2, start=('P26', 2, 1, 0))` | when the search cannot know a note still has its ID (the left hand of a harp after the right hand was retyped) |
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

## Spelling, retyped passages and restarts (S10, Nov 14)

- MIDI input picks the spelling itself, from context: the viola's single G sharp came in as A flat
  (S6), the harp's G sharp after an E came in right (S8). So the plan has a `spell` step for every
  typed sharp or flat, and the runner respells only a note that shows the other name.
- To change the pitch of a note that stays (the clarinet hint in S10), move it by scale steps
  (`p.pitch`); retyping would make a new note, and its slur and dynamic could go with the old one.
- A builder that clears a bar must take out chord notes too (`<chord/>`). S10's first build cleared
  only the first note of each horn chord, so the new E4 kept the old C4 and A3 under it. The change
  listing (every part, old against new) showed it before Brian saw anything.
- After Dorico restarts it has no autosave until the project changes. The runner reads the newest of
  the autosave and the file Dorico last saved (the log line `Saving document: 0 to <path>`).

## Hairpins on typed notes, and resuming (S10, Nov 14)

- After `HairpinStart` on a range of typed notes, `NavigateNextItemSamePosition` did not come back
  to the start note in 6 tries (S10 step 27, Violin II), so the run stopped although the hairpin was
  in. The runner now marks the selection as lost instead of stopping, and the next step starts from
  a note with an ID (its `via`), never from `rel`. A run resumed with `--from` starts lost too.
- So the planner does not plan a return step after a hairpin on typed notes: the next step starts
  from a note with an ID. To find one, `via` looks up to 24 bars back on the same staff (the flute's
  last note before a long rest), then on a staff above (`NavigateDown`), then on a staff below
  (`NavigateUp`, one press into each staff, one more per extra chord note). A tied note on a staff in
  between blocks a vertical walk, because the arrows stop on the tie chain.
- A part that has not played before (the trumpets in S14) has no note with an ID on its own staff,
  so after a hairpin its next mark needs a vertical walk. The vertical search now looks up to 8 bars
  back (it was 4), so it finds a note on a nearby staff in a bar that a long tie does not block.
- Six replies on Nov 13-14 never reached the panel: `sw_say.py` without a session tagged them
  `current`, and the server drops those. It now uses the current piece by default.

## Ranges that start on a slur (S12, Nov 14)

- The status bar reads a range as far as the last bar of a slur that starts on the range's first
  note: S12 step 13 selected the flute from bar 42 to bar 43, on a note that starts a slur to bar 44,
  and Dorico showed "Bars 42-44", so the range check stopped the run before the hairpin. A slur that
  starts on a later note of the range does not count (step 14 read "Bars 43-44" with a slur from bar
  44 to 45 inside it).
- The planner now reads every slur in the file and remembers each one it adds (`Plan.slurs`), and
  expects that wider range.
- A hairpin that spans the first selected note also counts, from its first bar (S21 step 108: the
  bassoon's crescendo over bars 46-48 made a 48-49 range read "Bars 46-49"). A hairpin that ends
  before the first note does not (S12 step 14). `Plan.hairpins` keeps each one's exact end
  (`Score.item_end`, after its tie chain); replayed on S12 and S21 the planner gives exactly the
  ranges that went in. Replayed on S12, it gives exactly the ranges that went in. Whether a
  hairpin that starts on the first note also counts is not known yet; a stop will tell.
- A range may end on a note that continues a tie (S13: a slur from the G to the held E, which the
  file writes as ending in the bar after the E starts). The arrows never stop on a tie continuation,
  so the planner aims at the note that starts the chain (`Score.chain_start`); the range then covers
  the whole chain.

## Repeated sharps, ranges of accents, tuplets (S15, Nov 14)

- A run of repeated sharp notes (the cellos' four C sharps) is typed one after the other, and
  Dorico spells them alike. `p.spell(..., group=k)` checks the first one; only if it shows the flat
  does the runner extend over all k and respell them at once. A respell of a note that is already
  right is not safe: "using note name below" turns C sharp into B double sharp.
- `p.articulate(pid, start, end, 'kAccent')` puts one articulation on every note of a range. Values:
  kAccent, kMarcato, kStaccato, kStaccatissimo, kTenuto, kStaccatoTenuto, kStress, kUnstress.
- Tuplets: see "Tuplets, shortened notes and hairpins already in the score" below (S24).

## Dorico on another desktop (S21, Nov 15)

- S21 stopped at step 16 with "Dorico shows bar None nothing": Dorico's project window had moved to
  another desktop (Spaces). There the accessibility API lists no window, so the status bar cannot be
  read. Activating Dorico does not help, because "switch to a Space with open windows" is off on
  this Mac (`defaults read com.apple.dock workspaces-auto-swoosh` is 0); the window server
  (`Quartz.CGWindowListCopyWindowInfo`) still lists it, with onscreen False.
- The runner now checks `window_visible()` before the first step (nothing is done if it is false)
  and names the cause when a check reads nothing. The fix is Brian's: switch to Dorico's desktop.
  Ask in the panel and by a push, and wait for the window in the background, then go on with --from.

## Beaming in pairs (S22, Nov 15)

- In this project 2/4 eighths beam in fours. A time signature does not change that:
  `NoteInput.CreateTimeSignature?Definition=...` took `2/4\,2+2` (a comma in a value must be sent as
  `\,`, as in chords; a bare comma split it into `2/4` and a stray `2+2=`) and `[1+1]/4`, and the
  export still showed four-note beams. It is the project setting Notation Options > Beam Grouping,
  eighth notes in quarter-note time signatures: break the beams at each beat.
- That dialog cannot be driven from outside: its category list ignores AX clicks, keyboard
  selection and the search box (tried Nov 15; closed with Escape, nothing applied). Brian sets it
  himself in a few seconds, or every group is split with `p.split_beam(pid, bar, 1.0)`.

## Staff text (S21, Nov 15)

- Dorico 4 has no "div." or "unis." playing technique (`playingTechniqueDefinitions.xml` has none),
  and `NoteInput.CreateText?ParagraphStyleID=paragraph.defaulttext` opens a text box but takes no
  words. `p.text(pid, bar, onset, 'div.')` sends it, then the runner brings Dorico to the front and
  types the words only if the focused element is a text field (AXTextArea or AXTextField), so the
  keys can never land on the score as shortcuts; otherwise it presses Escape and the run report
  says the text was not added. Then `NoteInput.TextCreateFinished`. Text steps go last.
- First use, S21: the words went in, but `NoteInput.TextCreateFinished` sent over the link (no
  parameters) did nothing, and the text box stayed open, so Dorico refused the next command. Escape
  closes it and keeps the text: Dorico then runs `TextCreateFinished?FlowID=..&EventBlockID=..&
  AboveOrBelow=kAbove&IsSystemText=0&RhythmicPositionPair=..` itself. The runner now types, then
  presses Escape, and checks that the text box closed.
- The MusicXML export leaves staff text out (only text such as "Con dolcezza" on a tempo or
  expression comes through), so the check cannot see it: look at Dorico's window (a screenshot of
  that window only) to confirm.

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
- S9 (the introduction, the warmth and two fixes; 7 typed lines and 18 marks and ties): 25 steps in
  48 s on the first try, and the export matched in every note, spelling, rhythm, tie and mark.

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

## Tuplets, shortened notes and hairpins already in the score (S23-S24, Nov 16-17)

Brian accepted S24 (which ran S23 first) before the scratch test below had run. S23 went in, all 91
steps, with one wrong note length; S24 stopped twice before an edit, and every note of both came out
right after the fixes (a new export matched in every note, rhythm and tie).

- Tuplets: `NoteInput.StartTupletRun?Definition=6:4&Set=true` starts a run of sixteenth sextuplets
  and `...&Set=false` ends it (both are in Brian's own log). The tuplet takes the note value that is
  set when it starts, so the plan sends `NoteInput.NoteValue?LogDuration=kSemiQuaver&Set=true` first.
  A run goes on over groups of the same ratio. `NoteInput.Tie` before the run ties a quarter into the
  first tuplet note. 3:2 works the same way for sixteenth triplets.
- A note tied into a tuplet from a note outside it is a second event in Dorico. The right arrow and
  `NavigateRightExtend` stop on it once more; the left arrow does not. S24 stopped at step 26: a range
  from such a quarter ended one note short ("Bars 49-50", wanted 49-51). `Score.stops` and
  `Score.forward` count the right-arrow stops, and ranges and forward walks use them.
- `EventEdit.DurationShortenByGrid` shortens the selected note by the rhythmic grid (an eighth) and
  keeps its ID, tie and slur. It shortens only the selected note. S23 selected the violas' chord by
  the ID of its top note, so their E and B held on; a two-step repair fixed it. `p.shorten` makes one
  step per chord note, each selected by its own ID.
- A hairpin that is already in the score and stops on the first selected note widens the status bar's
  range, like one that spans it: S24 step 39 read "Bars 47-52" for a 49-52 range, because the
  clarinet's crescendo from bar 47 stops at bar 49. `Score.wedges` reads the score's hairpins, and the
  range check counts those that end on the first note. It counts a hairpin that an earlier step of the
  same plan made in the same way (S25: a diminuendo that starts where the crescendo ends expects the
  crescendo's bars too); S25 is the first run of that half of the rule.
- MusicXML: sextuplets need 12 divisions to the quarter. Raise them only in the bars with tuplets (an
  `<attributes><divisions>` in the first one and back to 4 after them), so the other bars stay byte for
  byte and their notes keep their IDs in the plan. `Score` and `color_xml.py` read divisions bar by
  bar, and the colorer compares lengths in quarters.
- `app/dorico_scratch_test.py` tries commands in a scratch project beside his: it opens a small
  MusicXML, saves it so its notes have IDs, runs the commands, reads the result back from the file,
  then closes the project and moves it to the Trash. It has not run yet. Run it, after a panel line
  and his OK, before a plan uses a command that no run has used.
