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
| glissando line | `p.gliss('P26', (101, 1), (102, 0))` | the two notes as a range, then `NoteInput.CreateGlissando` (no parameters): one line from the first selected note to the last, in Dorico's default style; a down-and-up gesture is two steps |
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
  at step 1, with no change, because the bar it looked for had not moved yet.) The hook follows the
  chain to the end, deepest plan first (Nov 17, see "The S31 accept chain").

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
  starts on a later note of the range counts too (S38 step 31, Nov 23: a range from bar 105 to the
  first note of a slur to bar 108 read "Bars 105-108"). S12 step 14 seemed to show the opposite
  ("Bars 43-44" with a slur from bar 44 inside it), but that slur ended on the downbeat of bar 45,
  so by the rule below it counts only to bar 44.
- The planner now reads every slur in the file and remembers each one it adds (`Plan.slurs`), and
  expects that wider range.
- It counts a slur up to where its last note starts. A slur that ends on a note at the start of a
  bar counts only to the bar before: S26 step 4 selected the cor anglais from bar 70 to 71 on a note
  that starts a slur to the downbeat of bar 72, and Dorico showed "Bars 70-71" (step 5 then read
  "Bars 72-73" for the same case). S12's slur ended on beat 1.5 of bar 44, so bar 44 counted. A slur
  that ends on a tie continuation keeps the bar where the chain ends (S13), unless the chain starts on
  a downbeat: then it counts the chain's first bar (S38 step 31: a slur to the E on the downbeat of
  bar 108, tied into 109, counted to 108).
- A hairpin that spans the first selected note also counts, from its first bar (S21 step 108: the
  bassoon's crescendo over bars 46-48 made a 48-49 range read "Bars 46-49"). That holds for a hairpin the
  same run made, not for one already in his score: S41 step 21 selected the clarinet from beat 2 of bar
  109, under his decrescendo of bars 108-109, and Dorico showed "Bars 109-110" (Nov 24). A hairpin from
  the score counts only when it ends on the first selected note with a dynamic there (S24). Rebuilt with
  this rule, the S31, S34 and S38 plans come out as they ran. A hairpin that ends
  before the first note does not (S12 step 14). `Plan.hairpins` keeps each one's exact end
  (`Score.item_end`, after its tie chain); replayed on S12 and S21 the planner gives exactly the
  ranges that went in. Replayed on S12, it gives exactly the ranges that went in. A hairpin
  that starts on the first note does not count (S27 step 5, Nov 17).
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
  range check counts those that end on the first note, but only when a dynamic sits at that end: the
  "f" that step 38 had put on bar 49 joined the crescendo to the note. Without a dynamic it does not
  count. S25's last step expected "Bars 73-77" for a decrescendo starting where its crescendo ended,
  and Dorico showed "Bars 76-77"; the plan now counts a hairpin's end only with a dynamic there
  (`Score.dyns`, and the dynamics the plan makes).
- MusicXML: sextuplets need 12 divisions to the quarter. Raise them only in the bars with tuplets (an
  `<attributes><divisions>` in the first one and back to 4 after them), so the other bars stay byte for
  byte and their notes keep their IDs in the plan. `Score` and `color_xml.py` read divisions bar by
  bar, and the colorer compares lengths in quarters.
- `app/dorico_scratch_test.py` tries commands in a scratch project beside his: it opens a small
  MusicXML, saves it so its notes have IDs, runs the commands, reads the result back from the file,
  then closes the project and moves it to the Trash. It has not run yet. Run it, after a panel line
  and his OK, before a plan uses a command that no run has used.

## The export takes the front, and how an extra hairpin was taken back (S25, Nov 17)

- `dorico_export.py` brings Dorico to the front to click File > Export. At 17:32:34, while it did,
  Dorico ran `NoteInput.RepeatLast` (the R key) on the selected crescendo and made a copy from bar 76
  to 79: most likely a key Brian was typing in the panel went to Dorico. So: before an export, a panel
  line asks him not to type, then wait about 10 seconds; the export now gives the front back to the
  app that had it. A server signal that he is typing would be better (the page keeps its draft only in
  the browser).
- Taking the copy back: stepping through the items at the note where it started
  (`EventEdit.NavigateNextItemSamePosition`) found only the note, and Dorico 4 has no command that
  selects only hairpins. The undo history did it, by the rule above: six "Undo Select" steps (from
  that probe), then "Undo Repeat", undone once, with the Edit menu's first item read before each
  step. An export before and after showed that no note changed.
- A run also stops when Brian edits the notes a plan targets after its last export (S25 step 9: "no ID
  for Flute bar 76 D5"). Export again, build the step on his new notes, and run it alone.

## The S31 accept chain: rests, empty bars and hairpins (S27-S31, Nov 17)

Brian accepted S31 at 18:53. S31 builds on S30, and S30 on S27. The run put every note in, but two
plans stopped before an edit, the violas of bars 79-85 came out garbled and the timpani came in a bar
early. A repair plan fixed both, and a new export then matched S27, S30 and S31 in every note. S32
ran next on the fixed tools: 37 steps in 65 s, every target checked, and its check matched in every
note and mark.

- The hook ran S30 and S31 but not S27: it followed `requires` one level only. `put_in_requires` in
  `sw_on_accept.py` now runs every plan in the chain, deepest first, withdraws each in the panel and
  waits for the autosave. If one stops, the hook stops too: "a suggestion it builds on did not go in".
- Result files: each run writes `S<n>.dorico.result.json`, and the hook skips a plan whose result is
  ok. `dorico_apply.py S<n>.dorico.json --from k` writes it too when a plan finished by hand ends ok.
- `/api/accept` with `"who":"claude"` queues an `[ACCEPT S<n>]` line in the inbox, like his button,
  and sets the working score to that suggestion's file. The waiter then hands the line to the hook,
  which runs the plan again. For a plan already put in by hand: write its result file first, then
  record the verdict, then load the working score from a fresh export (`sw_working.py`).
- A rest in note entry only moves the caret. An old note under it stays, and the caret can stop on
  it, so the notes after come in shifted. S30 typed the violas (an eighth rest, then six sixteenths)
  over his double stops of bars 79-85: the double stops on the downbeats stayed, and the sixteenths
  came in a sixteenth late. `Plan.notes` now refuses a line with a rest over an old note
  (`check_rests`). Delete the region first (`p.step(..., to=..., edits=['Edit.Delete'])`, then
  `p.use` a score with rests there). The S28 builder now deletes his viola bars 78-85 before it
  types; `pieces/p111326_s31_repair.py` deleted and typed the region again.
- A typed line must cover every bar from its first to its last. S31's timpani line skipped its empty
  bar 88, so every later timpani note came in a bar early (step 115). `events()` in
  `pieces/p111326_s28_dorico.py` now fills a bar the line leaves out with a bar of rest.
- Dorico cuts a rest at the beats: a dotted-quarter rest on the downbeat of a 2/4 bar is a quarter
  rest and an eighth rest, and the arrows stop on each. The plan's file had one rest, so three oboe
  walks of S31 (steps 52, 70, 92) came out one stop short. `write_bar` in `pieces/p111326_s5.py` now
  cuts every rest at the beats, except a whole-bar rest (`rest_pieces`). Rebuilt with it, S31's plan
  gives exactly the steps that ran.
- Typing over the first or last note of a hairpin takes the hairpin away. S31 step 32: S30's Violin I
  crescendo ended on the note that S31's run replaced, and a range from bar 85 then read "Bars 85-86",
  not 82-86. `Plan.notes` drops such hairpins from its records (`drop_hairpins`).
- A hairpin that starts on the first selected note does not widen the range. S27 step 5: the flute's
  crescendo from bar 73 started on the slur's first note; Dorico showed "Bars 73-74", the plan wanted
  73-76. Only a hairpin that starts before the first note and runs through it counts, or one that ends
  on it with a dynamic there.
- A slur that ends on a downbeat counts that bar when its last note is tied on. S30 step 67: the
  flute's slur from bar 82 ended on the downbeat of bar 86, on a note tied on, and Dorico showed "Bars
  82-86". After S31 made that note one dotted quarter, the same range read "Bars 82-85". Rebuilt now,
  S30's plan expects 82-86 there, and adds the viola delete step; nothing else changes.

## Glissandi, and the first run of the scratch test (S33, Nov 18)

- `NoteInput.CreateGlissando` (no default key; Dorico calls it "Create Glissando") puts a glissando
  line between selected notes. On a range of two notes it made one line. On a range of three notes it
  also made one line, from the first note to the last, with nothing at the middle note. So
  `p.gliss` takes two notes, and the harp's down-and-up in bar 104 of S33 is two steps.
- The file keeps each line as a `GlissandoLineEventDefinition` with the IDs of its two notes
  (`fromNoteEventAndBlockInstanceIDs`, `toNoteEventAndBlockInstanceIDs`); `glissandi()` in
  `app/dorico_scratch_test.py` reads them back.
- Dorico imports glissando lines from MusicXML as the file draws them (wavy or straight). A plan's
  lines take Dorico's default style, so the picture of a suggestion and his score can differ there.
- When two glissandi share a note (D6 to D4 to A5), the plan makes the second line first. Then no
  selection starts on a note that already has a glissando. A glissando that starts on the last
  selected note does not widen the range (a slur there does, S38): S34's step 34 (D6 to D4, the D4 already
  starting the line to bar 105) read bar 104 alone, and all 131 steps went in on the first run.
- The test was the first run of `app/dorico_scratch_test.py` (`... gliss`, with a panel line and
  his OK). It opened, saved, closed and trashed its project in about 30 seconds, and his project stayed
  the only one open. `dorico_file` gives the notes of that imported project no bar numbers, so the
  harness picks them by position (two quarters to a bar).
- A part that comes in after a long rest needs a dynamic at its entry, or it plays at whatever it had
  last: S32 brought the tuba in at bar 94 under ff brass with its mf from bar 53. `clash_check.py` now
  lists every entry after four bars of rest or more with no dynamic.

## The scratch test that closed his project, and tuplets (S38, Nov 23)

What happened. The tuplet test's MusicXML put a `<dot/>` and a tuplet mark before `<voice>`, so Dorico
stopped on "MusicXML validation failed". The harness sent Cmd+S and Return into that warning; its OK
button takes no keys and has no accessibility element. The cleanup then clicked File > Close Project
three times while the warning was open, and Dorico queued them as forced commands ("Posting command
(force): File.CloseProject" in its log). When the warning went (a click at its OK button's screen
position), the scratch project's Save sheet and save prompt came up; after its Don't Save, the second
queued Close Project closed Brian's project. It had no unsaved changes (last save 07:18), so nothing
was lost, and it was open again at 07:39. Rules, all now in `app/dorico_scratch_test.py`:

- Check every scratch MusicXML against Dorico's own schema before Dorico sees it
  (`Contents/Resources/musicxml/musicxml.xsd`, its imports pointed at the local `xml.xsd` and
  `xlink.xsd`); write notes in the schema's order (`plain()`).
- After the scratch project opens, stop if any dialog is open, and send nothing.
- Never click a menu command while a dialog is open: Dorico queues it and runs it later on whatever
  project is in front.
- Close only the scratch project: it must be in front, one Close Project, and Don't Save only for a
  prompt whose window under it is the scratch project (`close_scratch`).
- Send a key in the same AppleScript that brings Dorico to the front and checks the front window; in
  separate calls the key can land in another app.

Tuplets, from the test that then ran cleanly:

- A range delete that covers a whole tuplet removes the tuplet too; the tuplet before it stays.
- Inside a tuplet the caret moves by the tuplet's notes, not by the grid: two MoveRight from the first
  note of an eighth-note triplet stopped at 2/3, and the first typed note went into the tuplet.
  `Plan.notes` now refuses a caret path through tuplet notes. Start the caret at the onset from a note
  on another staff (`start=(pid, staff, bar, onset)`), as S38 does from the cellos.

After a project is closed and opened again, Dorico keeps no autosave until it changes. The offline
check (`dorico_apply.py --check`) then reads the open project window's name, or else the last saved
project that is not a scratch test (the newest save was a scratch project in the Trash).
