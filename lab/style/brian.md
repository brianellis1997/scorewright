# Brian's style guide

Read this before writing a note for Brian, then [COMPOSING.md](../COMPOSING.md). Each rule says
where it came from. Keep his words where he gave them.

To add a rule, Brian starts a message with `style:` in the Scorewright page or in the chat. Append
it under the right heading with the date and the piece, in his words plus one line on what it means
in notation, then confirm it in one line (`sw_say`).

## Orchestral writing

From 111326, a romantic orchestral sketch in Dorico (Nov 13 2026), the first piece composed
together. Bars refer to that sketch.

- **The first statement of a theme has "a slight wind feel".** The oboe sings in its warm upper
  middle register (E5 to G5) over sustained horn chords. Then the flute takes the theme, "with the
  strings subtly assisting", and the texture builds after that.
- **Melody hand-offs overlap.** The new instrument enters on the upbeat while the old one finishes
  its phrase: the flute enters at bar 15, beat 2, and the oboe ends at bar 17.
- **Dovetailing.** The accompaniment passes from one section to the next on the same chord, in the
  same voicing, on a downbeat: the horns end on F major at bar 16 as Violin I starts that F major
  chord. The section that leaves fades (diminuendo to pp); the section that enters comes in pp.
- **Dynamic levels: the melody rings out.** Melody mp ("maybe mezzo piano for the oboe"),
  accompaniment p ("piano, more soft"), strings under a melody pp ("the strings can't overpower the
  flute"). Horns overpower an oboe if no dynamic is written.
- **Dynamics follow the melody.** Very subtle at the start, a crescendo to the high point ("the
  climax to the top G in bar 10"), a decrescendo as the line falls. The end of a phrase recedes,
  most of all under the next instrument's entry.
- **Breath in the line.** An eighth-note upbeat is slurred into the next downbeat quarter, and that
  quarter is portato (tenuto-staccato, a dot and a line): "somewhere in between a normal note and a
  staccato... a lot of breath into the melody, where the wind instrument can really breathe after
  that and get into the flowing rhythm." Long slurs cover the flowing eighth-note runs.
- **A theme that changes instruments keeps its slurs.** When the flute takes the oboe's theme, it
  copies the oboe's slur groups and articulation bar for bar.
- **A chord on one staff is a sketch for the section.** Spread it across the players before
  anything else, without being asked: "the horn can only play one note at a time... horns 1 and 2
  take the top two notes, and a similar instrument, the Wagner tuba or a trombone, takes the lower
  note... the violin can't play that low F: the first and second violins take the top notes and the
  viola takes the bottom." Copy the slurs and dynamics to every player and check each range. "This
  is basic school writing... it has to be obvious." (Nov 13 2026)
- **Every player has the phrase slurs.** When a texture passes to new players, they get slurs
  over the same phrases: the strings in bars 16-24 slur 16-19 and 20-24, as the horns slur 8-11 and
  12-16. ("The strings need their slurs as well.")
- **Harmony parts hold their common tones, also over the bar line.** A note a player repeats inside a
  bar is one held note, not two quarters; only the voices that move change: "those should be half
  notes, not individual quarter notes. They're just harmony, so it needs to seem smooth." A note
  that continues into the next bar is tied over the bar line: "we want the horns and the
  accompaniment as continuous as possible... if they're not changing their note, just hold them
  over." His example: Violin I enters on A, falls to a G half note, and the next bar starts with a
  G quarter, so the G is tied over. "When I compose, the harmony tries to be as continuous and fluid
  as possible... sometimes there are exceptions." (Nov 13 2026)
- **A new phrase starts from everything that is already sounding.** His sketch of a new phrase is
  often only the melody and the harmony; the other lines are still going. "The cohesiveness of the
  phrasing needs to be maintained... look at what everything else is doing. Like the harp just
  started this run 4 bars ago, right? We can't just leave it and fill in the harmony or melody...
  Where's this harp part going? How does it evolve into this phrase? Do we dovetail it into another
  instrument, or does it just kind of end? It doesn't make sense to end abruptly. That's not my
  style. If it's going to end, it has to end smoothly. Or keep the pattern going, if it makes sense,
  or have the harp devolve into a phrase, maybe accenting the melody or the harmony in some way, or
  a counter melody... Look at all the different ideas going on right now, the texture, the
  individual lines: where are they all heading? Do some continue, do we dovetail into another
  phrase, politely end that phrase in a smooth way, or do we need to add new instruments?" In
  notation: before the new phrase, list every line that sounds in the bars before it, and give each
  one a fate in the suggestion. It continues (the figure follows the new chords), it dovetails
  (another instrument takes it on the same beat), it ends smoothly (a leading tone resolves, a line
  lands on a held chord tone, a diminuendo), or it changes its role (it doubles the melody's
  accents, marks the harmony, or becomes a counter-melody). A line never just stops. Then decide
  which new instruments join. (Nov 14 2026, 111326 bars 29-33: S10 left the harp's run of bars
  29-32 and the cor anglais and E flat clarinet on a G sharp with nowhere to go.)
- **Harmony in the theme.** One chord per 2/4 bar, a modal minor loop under a melody centred on E:
  F, G, Em, E (A minor VI, VII, v, V), with inversions in the second half (F/A, G/B).

## Songs

From "Where I Left It" (Oct 2026). The full list of rules from his verdicts is in
[COMPOSING.md](../COMPOSING.md) section 2. The ones he repeated most:

- Slow, suspended harmony over pedals; plain diatonic motion; in minor, a hint of the relative
  major, not more.
- One accompaniment figure per section, with space; the piano answers the melody's breaths.
- Simple stepwise melodies; high points are rare (C, not E).
- Breaths every 8 seconds or less in a wind or vocal line.
- A song must move: S10 was "monotonous, slow, the chorus boring". Vary the rhythm from bar to bar,
  change chords faster in a chorus, and do not hold one tempo for the whole song.

## Notation

- Concert pitch, always, for every instrument (Oct 10 2026). He writes horns, clarinets, trumpets and
  the Wagner tuba at concert pitch: "they might say horn in F, but the notation is in pitch" (Nov 13).
  Dorico's MusicXML stores them at written pitch with `<transpose>`: convert in code, never call his
  parts transposed.
- In 2/4, eighth notes are beamed in pairs, one beam per beat, never four to a bar (Nov 13). In
  4/4, four eighths per half bar (Oct 9).
