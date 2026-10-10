# Scorewright composing harness

How a frontier model continues, fills, orchestrates or edits one of Brian's scores so that the
result sounds like his piece and not like a generic continuation. This is the procedure that
produced the results he rated 3 to 4 out of 5 on Sept 4 2026 (String Quartet No, 3 5 piano take 2,
Mother's Day 2021, Orchestral Idea), after two days of results he rated 0. The difference was not
the model. It was what the model read, what it decided before writing a note, and what it checked
after. Follow this in order. Every step has a tool in this folder.

## 0. What the product is

Not a trained music model. A harness around a frontier LLM, exactly like a coding agent is a
harness around a frontier LLM: read the whole codebase, understand the structure, make a
deliberate change, run the checks, show a diff, let the author accept or reject. The base model
is someone else's; the value is the reading, the decision, the verification and the feedback loop
(his verdicts in `_bridge/verdicts.jsonl`).

## 1. Read the whole piece, never the last four bars

The first three continuations Brian rated as "just varying the previous four bars", and he was
right: only 10 to 12 bars had been read. Everything rated well was written after reading every
bar.

    python dump_abc.py "<Score Exports>/MusicXML/<piece>.musicxml" <tag>
    python brief.py "<piece stem>" [last_written_bar] [part] [instrument regex]

`dump_abc.py` prints the score as rest-reduced interleaved ABC: one line per bar, one
`[V:k]...|` segment per voice that sounds in that bar, resting voices omitted. `brief.py` adds
the form map (empty bars = section breaks or the gap), tempo/text/meter changes, the last written
bars, and retrieval exemplars (section 4).

While reading, write down, in words, before touching a note:

- **Form.** Where the sections are. His sketches are often several ideas separated by empty bars
  or double barlines (3 5 piano: D major lyrical theme, running figures, staccato Allegro,
  chromatic Moderato). Name each one and its bars.
- **Material.** The two or three motifs that define the piece: the rhythm of the opening theme,
  the characteristic figure of the last section (a triplet turn into a held note, a paired
  sixteenth figure, a quarter-rest-rest-pickup motif), the accompaniment pattern (sextuplet
  arpeggio, block chords, pulsing eighths, ostinato).
- **Harmonic language.** What the piece actually does, not textbook: chromatic mediants, an
  augmented colour, a dim7 alternating with a maj9, a diatonic sequence. Brian objected to a
  chromatic-mediant climb that was not in the piece's language (Bright Valley 96-98). Stay inside
  the language the piece has already shown.
- **Register and texture per voice.** Where each hand or instrument lives. The single most
  common failure of the trained model was a right hand sinking into the bass register at the
  seam. Note the last bar's register for every voice and keep it unless the music moves it.
- **Where it stopped and why.** A piece that stops mid-phrase wants the phrase finished. A piece
  that stops after a complete section wants either the next section or a return. A hand that is
  empty for two bars while the other continues (Mother's Day 29-30) wants that hand written over
  what exists, not a fresh start after it.
- **Unfinished orchestration.** Chord figures in one part of an ensemble (Violin II playing
  three-note chords in a quartet) are shorthand for lines that belong to other instruments.
  Spreading them is an edit he wants, one line per instrument.

## 2. Decide the structural move before writing

Every well-rated take made one deliberate move about the whole piece:

- 3 5 piano: bring the opening theme and its arpeggio texture back, transposed into the last
  section's key, with the last section's ornament added to it. ("Holy shit, great job.")
- 724 piano: let the rising sequence peak, broaden on the dominant, then the opening melody
  returns over its own ostinato.
- String Quartet No: hand the theme to the viola while the violins take the pulsing
  accompaniment, then the forte phrase returns tutti.
- Orchestral Idea: keep all four layers of the last bar running and move the harmony.

Write the move down in one sentence. If the sentence is "continue the pattern", read again.

Rules learned from his verdicts:

- **Never end unless asked.** Every forced ending was called "abrupt". An accented ff cadence followed by a sudden piano chord also reads as an ending ("you seem to want to end the piece, it is nowhere near ending"); a section closes on its last strong beat with the accompaniment still moving. A continuation stops where
  the next idea would start: on a tie, a crescendo, an open dominant. Ending is a separate
  request with a real approach, a phrase and not a chord.
- **Recapitulation is legitimate; variation of the last phrase is not enough.** Bringing earlier
  material back, transformed, is what he recognised as composing. Restating the last four bars
  with different notes is what he called "not inventing anything".
- **Transitions need the bars before the gap.** He noted the theme's return was not smooth
  because the existing bars could not be touched. The harness must be allowed to propose edits
  to the one or two bars before the gap, shown as a diff.
- **His style is retrieved, not guessed** (section 4).
- **Pedal where the original pedals.** If his bars carry a pedal line, the new bars carry one,
  changed at every harmony (`!ped!` on the new harmony, `!ped-up!` just before it). Leaving pedal
  out of an arpeggiated texture he had pedalled was called "an obvious miss".
- **Smooth the seam by editing the bar before it.** Block chords straight into an arpeggio figure
  was "abrupt"; the fix is a lead-in written into the last beat of his final bar, offered as part
  of the suggestion, not a new texture dropped in at the barline.
- **Do not repeat an accompaniment figure for eight bars.** A motor kept for the whole
  continuation was "obnoxious"; alternate it with the piece's other accompaniment pattern.
- **One player carries the line.** Handing a melody between violin I and violin II every bar
  was "kind of interesting" but "awkward for the string player" (S15). Give the line to one
  player for the phrase; the other violin supports (the long figure underneath, or thirds in
  the climb).
- **Diminution answers a statement.** His own prescription after the climax (S15 reason): take
  the half-note figure (long note, repeated, lower neighbour, back) and mimic it in eighth
  notes, mirrored, cascading down a step per cell, "very passionate". Harmony he asked for:
  G#m, C#m7, F#, then F# to D#m as a "false pretense", then back to G#m, Rachmaninoff-like.
  When he gives a harmonic plan in words, use it bar for bar and say so in the note.
- **His development is a sequence, and the unit is the thing he sang.** Bars 41-48 of the
  quartet took fifteen takes (S12-S26). What he accepted: the two-bar unit (long note tied into
  the neighbour figure, then the eighth-note cell easing into quarters) repeated a step lower
  each time with the bass in descending fifths, one harmony per bar, the same hairpin shape
  every unit; then after two units leave the pattern (chromatic bass G# G F# to the dominant)
  instead of running the fifths on. What he rejected on the way: eighth-note runs that never
  stop ("too fast", "rushed"), harmony held for two bars, sudden dynamic jumps instead of
  hairpins, the line traded between the violins, a missing tie on a held note ("do not see
  everything that came before"), and continuing the circle of fifths past two units. When he
  gives notes or a chord plan in words, write exactly that, ties included, before adding
  anything of your own.
- **A piano sketch of an ensemble piece is an orchestration request.** Bright Valley 18-81 is a
  band piece written on two staves ("probably trumpet", "wind choir" in his own text); the useful
  output is the band score, with dynamics, slurs, articulations and tempo, not a continuation.

## 3. Write in ABC, the way his files are written

Output is answer lines in the same format the reduced score uses, one line per bar:

    [b:<bar index, 0-based>][V:1]<bar>|[V:2]<bar>|...

Conventions that matter, all learned the hard way:

- **Units.** `L:` is the unit length. A score can have different units per voice: in Orchestral
  Idea flutes, clarinet 1, bassoons and strings are `L:1/8`, everything else `L:1/4`, and Bright
  Valley's bass voice is `L:1/4` while its right hand is `L:1/8`. Read the header. Every bar of
  every voice must sum to the meter in that voice's unit. `check_lines.py` does the arithmetic,
  including tuplets `(3`, `(6:4:6`, `(3:2:2` and broken rhythms `>` `<`:

      python check_lines.py <lines.txt> 8 "4:3,4,6,7,10-19,24"

  (8 units per bar by default, 4 for the listed voices). Never render a file that fails it.
- **Key signature and accidentals.** In `K:D`, `c` means C sharp. In `K:Bb`, `E` means E flat.
  An accidental applies for the rest of the bar to that pitch in that octave. Write `=` for a
  natural where the key or an earlier accidental would alter the note. When copying his own
  lines back (a recapitulation), copy them verbatim, his accidentals are already right.
- **Pitch and octave.** `C` is middle C (C4); `c` is C5; `,` and `'` move octaves. Piano left
  hand in the small octave is `C,` to `B,`. Contra octave is `C,,`.
- **Chords** `[CEG]2`, **ties** `-`, **slurs** `( )`, **staccato** `.` before the note,
  **decorations** `!p! !mf! !f! !ff! !<(! !<)! !>(! !>)! !tenuto! !accent! !fermata! !ped! !ped-up!
  !arpeggio!`, **text** `"^Tempo I"` `"^rit."` `"^a tempo"` `"_dim"`, **tempo** `[Q:1/4=100]`.
  These are the spellings his own exports use (counts in PROJECT.md 52a), so they round-trip.
- **Rest-reduced format.** A voice that rests for a whole bar is omitted from that bar's line.
  When continuing an ensemble piece, include every voice that should sound. Invisible rests `x`
  are legal but render as gaps; write `z`.
- **Transposing instruments.** Write the whole ensemble in concert pitch and let
  `orch_transpose.py` produce written pitch per voice from the header's `transpose=` and each
  voice's inline `[K:]`. It spells by interval letters (concert E up a major second is F sharp,
  not G flat) and emits accidentals relative to the written key with bar carry:

      python orch_transpose.py <reduced_score.txt> <concert_lines.txt> <written_lines.txt>

- **Generating many voices.** For 24 staves, build the lines in a small Python script from a
  per-unit table (harmony per two bars, one entry per layer) rather than typing 192 segments by
  hand. See the Orchestral Idea block in the session log for the shape of that table.

- **Close every slur inside its bar.** A slur opened on the last note of one bar and closed in
  the next (`(A|` ... `B)`) comes out of abc2xml as one arc across four bars. Write
  `(B A G F) E3 E`, never `B)AGF`. Bars 17-24 of the quartet carry this artifact.
- **Beams follow the spaces.** ABC beams every run of notes not separated by a space. Write
  4/4 eighths as two groups of four, `(d'e'd'c') (c'd'c'b)`, never eight in a row; S16 was
  rejected on sight for "quarter notes connected", eighths beamed across the whole bar.
  Check the picture before registering a suggestion (headless Chrome screenshot of the SVG).

## 4. Retrieval: his idiom comes from his corpus

`retrieve.py` (repo root) indexes every melodic shape in all 1,607 scores by intervals and
rhythm ratios (SQLite, `Score Exports/retrieval.sqlite`). `brief.py` queries it for the last
written bars and prints his own passages with the same shape, in his notation, with slur and
dynamic counts. Filter by instrument when the question is idiom, not harmony:

    python brief.py "String Quartet No" 16 0 "violin|viola|cello"

For a NEW piece there is no passage to match yet; pull exemplars by what the piece will be:

    python corpus_find.py "<instrument regex>" [key] [meter] [since] [max]   # his scores by instrumentation/key/meter/date

Read two or three of the closest (dump_abc) before writing a bar, the way you would reread your
own recent work in the same genre.

Measured idiom that is now a rule (PROJECT.md 52e): in his string parts 46% of notes are under a
slur; slurs are 2 notes (49%), 3 notes (22%), 4 notes (25%), almost never longer; hairpins and
accents are everywhere; staccato dots on accompaniment pulses. Write strings that way. Do the
same measurement for any idiom question before guessing (pedalling, doubling, voicing).

## 5. Check, render, show

    python human_apply.py <score.xml> <cut_at_bar> <lo> <hi> <lines.txt> <tag> "<what was done>"
    SW_WHOLE=1 python apply_page.py <tag> <lo> <hi> "<title>"      # whisperer env
    python color_xml.py apply_<tag>_final.xml "<piece> (Scorewright edits in green).musicxml" <lo> <hi>
    python fix_pedal.py "<that file>" "<that file>"      # Sibelius drops pedal retakes; rewrite them as release+press
    python mark_xml.py "<that file>" "<... (marked).musicxml>" <lo> <hi>   # Sibelius drops note colour; text + bracket instead
    python layout_xml.py "<file>" "<file>"    # staff size / page / distances by staff count; strips stacked positions
    open -a "Dorico 4" "<file>"               # Dorico keeps the green note colour and plays through NotePerformer

`human_apply.py` splices the lines into the score through the same path as the model pages
(ABC to MusicXML, then into the original engraving so his bars are untouched). `apply_page.py`
reports range violations in the edited bars from `ranges.py` (textbook instrument ranges; the
report is information, never a mask). The green MusicXML opens in Dorico (colour kept, NotePerformer playback) or MuseScore. Sibelius was cancelled on Sept 22 2026 and dropped the colour anyway.
NotePerformer in Dorico is the listening he trusts.

Before opening anything for him: the duration check passed, zero unexplained range violations,
every voice that should sound is present, and the rendered bar count matches.

## 6. Record the verdict

Every reaction goes into `_bridge/verdicts.jsonl` as he said it, with the page tag, the task,
what was read, and a 0-5 score. That log is the evaluation set for the harness and the reason
this document exists. When a verdict contains a rule ("never force an ending", "spread the
chords across the instruments", "that's not my harmonic language"), add the rule to section 2
here and to PROJECT.md.

## 7. What changed between the failures and the successes

Same model. The failures read a fragment and continued it. The successes read the whole piece,
named its sections and material, chose a structural move that related the new bars to the old
ones, wrote in the piece's own language and register, checked the arithmetic, and did not try
to finish. That is the harness.

## 8. Orchestrating a sketch (band/orchestrate_bv.py is the worked example)

A two-stave sketch with ensemble intent ("probably trumpet", "wind choir" in his own text) is an
orchestration request. Procedure:

1. Dump the sketch, identify its voices (melody, counter-line, chord layer, bass) and their units.
2. Map the form bar by bar to sections (fanfare, wind choir, tutti, serene, climax, hold, link,
   close) using his labels, dynamics and double bars.
3. Write an instrumentation template (`band/band_header.abc`: staves, clefs, `transpose=`,
   score brackets) and, for each section, an assignment table: which sketch voice each
   instrument plays, which chord tone (chords are split, every wind and brass part is one line),
   and octave. Follow his labels first; keep families together (brass on fanfares, woodwinds on
   the choir, everyone at the tutti, piccolo an octave above the melody, tuba an octave below the
   bass).
4. Generate concert-pitch lines from the table, scale any quarter-unit voice to eighths, add the
   section dynamic where a part enters, keep his slurs, articulations and hairpins verbatim, keep
   his text in one voice only.
5. Fit every line into the instrument's sounding range by octaves (key-aware: an unmarked B in
   B flat is B flat), check every bar's duration, then `orch_transpose.py --keyed` to written
   pitch, assemble header + lines, convert with abc2xml, verify with music21 (part count, bar
   lengths) and `ranges.check`, open in Dorico.


Rules from his verdict on the first band pass (score 4):
- **Flutes live high.** A flute in the middle of the treble staff is inaudible under a band; put
  flute lines an octave above the sketch's right hand and let the piccolo double the flute an
  octave above that at the tutti. A solo flute in a quiet section: also an octave up.
- **Trumpets overwhelm.** In the tutti keep the trumpets a dynamic below the woodwinds, and keep
  them off the top octave; forte trumpets only on the fanfares and the climax.
- **Snare drum on the rhythmic hits** (the fanfare rhythm), rolls or silence elsewhere.
- **Winds breathe.** Rests between phrases in wind and brass parts are part of the writing, not
  gaps to fill.
- **He reads text.** "probably trumpet", "wind choir", "serene" in the sketch are instructions
  and the model reads them (they arrive as `"^text"` in the ABC). Follow them before inventing.
- **Lines have lives.** An instrument that starts a phrase finishes it, even across a section
  boundary (a flute doubling the oboe does not vanish mid-slur when the trumpets take over).
  The bass instruments carry the bass through every section that has one; sustaining voices
  (horns) hold chord tones softly under the wind sections. He called the alternative "block,
  block, block".
- **One instrument, one line.** "Trumpet 2" never gets a chord or a second voice; that is what
  "Trumpets" on one staff would mean. Split chords before they reach a single player.
- **Balance is written into the dynamics by role.** Whoever carries the melody gets the higher
  marking; brass in an accompanying role sit two steps under the wind melody (winds f, brass
  mp). This is standard band practice, not just a playback workaround; it is how a conductor
  reads the score. Reinforce it by doubling the wind melody in octaves rather than by marking
  winds louder than they can play.
- **Register continuity per player.** When a part re-enters or a texture changes (the 6/4 hold
  into the tutti), each instrument takes the chord tone nearest where it left off; an alto sax
  does not jump from A3 to D5 because a chord slot said so. The generator has a continuity
  pass (`continuous()`) that shifts a re-entry by an octave when that halves the leap and stays
  in range; the same judgement applies when writing by hand.
- **His development is not textbook development.** Two "developments" built from imitation,
  sequences and a modulation were rejected as "spinning out the same material" and "harmony
  weird". His own finished quartet (String Quartet Final, 2022) develops by: a small figure held
  as an ostinato for many bars, the bass moving underneath in two-bar steps (D, G, E, A), long
  sustained inner notes, crescendo/decrescendo swells, sudden accented tutti hits, and a slow
  descending line on top over six bars. Read a finished piece of his in the genre for the
  device before inventing one (corpus_find, then dump_abc).
- **Join by resolution, not by entry.** A bar that ends on a dominant with the melody on the
  leading tone wants the next bar to resolve it in the same instrument (A sharp to B in Violin
  I) with a common tone held in another. A fresh instrument entering with a new figure at a
  section seam reads as "no continuity".
- **Answer a new melody before leaving it.** When his last bars introduce a new phrase (the
  forte melody at 13-16), the continuation is its consequent, same opening, different ending,
  same accompaniment texture, not a new section. Leaving after four bars of a new idea was
  "moving completely on to something else, awkward".
- **String chords are one player's hands.** Triple stops in viola and cello were "impossible";
  write double stops a single player can hold (fifths, sixths, octaves, thirds in the right
  register), even where his own sketch had triple stops. Check every `[...]` in a string part.
- **The join can reach back into an accepted bar.** When the accepted bar ends on a held note
  and the new bar starts elsewhere, the fix (a run up into the new note) belongs in the
  accepted bar, offered as part of the next suggestion. Also remove any tie that would now
  connect different pitches across the seam.
- **Keep the accompaniment's rhythmic roles.** In his intro the cello owns beat 1 and the
  offbeat quarters, the viola owns beats 2, 3 and 4. Two parts both starting off the beat left
  nobody on beat 1: "makes no sense, weird sounding". When reusing a texture, copy who plays
  where, not just the pitches. Also: do not restate a dynamic a part already has; a diminuendo
  from forte needs no new "f".
- **A B melody should be the theme in disguise.** "I'm not sure where that's coming from" is the
  verdict on a fresh tune; derive B's melody from the theme's head in the new pulse so the
  origin is audible, then bend its second half.
- **Do not answer anticipation with a soft phrase.** When an accepted bar ends as a build
  ("an explosion is about to happen"), the next bars keep climbing until the explosion; a quiet
  answer at that point "kills the tension" and has to rebuild from zero.
- **After the climax, deliver.** Once the build has peaked, the next bars must be the payoff, a
  melody or a dialogue, not two more bars of climb and not the earlier forte phrase replayed at
  ff ("playing the same shit we already did"). Peak, then sing.
- **A leap needs an approach.** A seventh in a violin line "is not natural" without a run,
  triplet or sextuplet into it; write the approach into the bar before.
- **Development, not restatement.** Bringing the theme back a third time was "not going
  anywhere". After the recapitulation move, develop: sequence the head figure through new
  harmony, imitate between instruments, drive to a dominant, leave it open.

Result for Bright Valley 18-81: 23 parts, 64 bars, no wrong-length bars, no range violations,
first pass in one afternoon. Expect his verdict to move instrument choices, doublings and
dynamics; those become the next rows of the assignment table, not new code.

## 9. The surface (lab/app)

Rule of the loop: **the suggestion block is the message.** sw_suggest's note is what he reads;
do not follow it with an sw_say that says the same thing ("S20 is up, 41-48, ..."). He sees the
block in the chat already. sw_say is only for something the block cannot carry: a question, a
bug you fixed, a withdrawal. Keep those to one or two sentences.

Rule of the loop: **an Accept is not a request.** After he accepts, wait. He either says what he
wants next (talk or type) or presses ▶ continue, which sends "[CONTINUE]". Composing the next
bars on your own after an accept produced two open suggestions for the same bars and a
confused user. One open suggestion per region at a time.

    # server.py runs under launchd (com.scorewright.server): http://localhost:8790, ws://localhost:8791; never start a second copy
    python app/sw_working.py <score.musicxml>
    python app/sw_suggest.py <final.xml> <lo> <hi> "note" [lines.txt]    # after human_apply
    python app/sw_say.py "reply text" <session>
    ./app/sw_wait.sh                          # background in the Claude Code session: blocks until he speaks
    python app/np_agent.py                    # background in the Claude Code session too: NotePerformer renders

**NotePerformer audio.** Every render (suggestion, working score) is queued in the server; the helper
`app/np_agent.py` claims jobs and runs `app/dorico_render.py` (open in Dorico, Export Audio,
close without saving; about 35-90 s). It must run from a process macOS trusts with Accessibility:
the launchd server is not ("osascript is not allowed assistive access"), this Claude Code session
is. So start the helper in the background at the start of every session, next to sw_wait.sh.
Until a render lands the page plays MuseScore's basic audio; the play button says "▶ NotePerformer"
once it is ready. Renders and upload transcriptions share `_bridge/heavy.lock` so they never
compete for CPU (Dorico timed out opening a file while a transcription ran).

**Pieces.** The header menu switches pieces (sessions) or opens "New piece" (title, instruments
preset, key, meter, tempo): the server builds an empty score from ABC through abc2xml, switches to
it, and writes `[NEW PIECE <name>] ...` to the inbox. The current piece is remembered in
`_bridge/current_session.txt`, so restarts come back to it; it overrides the session named in the
launchd plist.

**Uploads.** 📎 takes any audio or video file from the phone, streams it to the Mac, pulls the
audio out with PyAV (`app/media.py`), and transcribes it in the background (`listen.py --upload`:
tempo from beat tracking, strict speech filter, a 16-bar preview, a MIDI file of everything). The
card offers "use it", which sends `[TAKE upload_HHMMSS] <his words>` with the notes attached.
Measured on a MuseScore rendering of Nocturne no 6 (2 min 22 s, not a real piano): about 90 s,
828 of 832 notes matched the score.
    python app/hum.py <audio.wav> [bpm]       # anaconda base python (HUM_PY in server.py): librosa pyin -> notes

The 🎹 button is a take from the piano: press, play and talk, press again. The page records the
mic; the server captures MIDI from any keyboard plugged into the Mac the whole time (app/server.py
midi_listen, mido) and pairs it with the take; app/listen.py then runs whisper (base, word
timestamps) for the words and, when no MIDI arrived, the ByteDance piano transcription model on
the audio (notes heard inside speech spans are dropped, so talk before or after playing). Notes are
quantized to eighths at the working score's tempo, notes at or above the hand split = right hand
(V:1), below it = left hand (V:2), rendered as a small staff he confirms with "use it". That writes
`[TAKE take_HHMMSS] <words>` to the inbox; the notes are in
`session/<name>/take_HHMMSS.abc` (per-bar `[b:i][V:1]...|[V:2]...|` lines, K:C with explicit
accidentals), the audio and MIDI beside it. MIDI is exact. The audio model on a phone recording of his real piano (Sept 7 2026 take) needs:
onsets clustered within 100 ms (chord notes arrive jittered), ghosts dropped (under 120 ms or
velocity under 30: attack harmonics, high spurious notes), and an adaptive hand split (the
emptiest pitch between G#3 and G#4) so the top of a left-hand chord is not called melody. The
page records with echo cancellation, noise suppression and gain control off. It is useless on
hummed or synthetic tones. Rhythm is his "future problem": trust pitches and
register, treat durations as a sketch.

The 🎵 button records him humming or singing, decodes to WAV in the browser, posts to /api/hum,
and drops "[HUM] I heard: D#5(2) E5(1) ..." into the text box (lengths in eighths at the working
score's tempo) for him to correct and send. Repeated notes on one pitch are split by onsets and
are the weak spot; treat what arrives as his intent, not gospel.

He talks in the page (mic) or the MuseScore panel; both land in inbox.jsonl. Compose as in
sections 1-5, then register the result with sw_suggest; it appears green in both surfaces.
Accept copies the suggestion over the working score; Reject keeps the working score; both log a
verdict with his words. Never write to the working score directly: everything goes through a
suggestion so the log stays complete.

## 10. A new piece from words (lab/songs/where_i_left_it.py is the worked example)

When he asks for a whole piece, not a continuation, there is no score to splice into, so write a
build script under `lab/songs/` that generates the full ABC: harmony per beat, the melody in
concert pitch, the words, and the accompaniment per section. Re-running it rebuilds the piece, so
revisions are edits to tables, not to 100 bars of ABC.

1. **Retrieve his idiom for the exact pairing first.** `corpus_find.py` with the instruments, then
   `dump_abc.py` on the two or three closest pieces (for "Where I Left It": the 9/19/19 English horn
   study, Song Study no 8, and no 5 for 6/8). Write down what he does: register, accompaniment
   figure, bass motion, where the middle section goes harmonically, how it ends.
2. **Let the words set the meter.** Mark the stresses. Anapests (da da DUM) want 6/8 or 12/8,
   iambs and trochees want 4/4 or 3/4. Put stressed syllables on strong beats and let line ends
   hold while the accompaniment fills.
3. **Words go on the notes as ABC `w:` lines** under the melody voice. abc2xml writes them as
   MusicXML `<lyric>` with begin/middle/end syllables; Verovio draws them and Dorico imports them.
   - **abc2xml gives every note a syllable, the second half of a tie included.** Put `*` in the
     `w:` line for every tie continuation and every wordless note, or the words slide one note early.
   - `_` extends the previous syllable over a new note (a melisma); `-` joins syllables of a word.
4. **Transposing melody instruments**: write the voice in written pitch with its own key,
   `V:1 ... transpose=-7` and `[K:A]` at the start of that voice for an English horn in a D major
   piece. abc2xml writes `<transpose>` with only `<chromatic>`: add `<diatonic>` (-4 for a fifth),
   and delete the extra `<key>` the global K: leaves in the first bar of that part.
5. **Check before showing**: every bar's length in every staff, the sounding range, that each
   syllable sits on its note (no syllable on a tie continuation), and every strong-beat or long
   melody note against the accompaniment chord (expect only deliberate suspensions and colours).
   Then render, look, and register it as a suggestion in its own piece so his verdict is logged.
