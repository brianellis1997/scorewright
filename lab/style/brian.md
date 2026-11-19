# Brian's style guide

Read this before writing a note for Brian, then [COMPOSING.md](../COMPOSING.md). Each rule says
where it came from. Keep his words where he gave them.

To add a rule, Brian starts a message with `style:` in the Scorewright page or in the chat. Append
it under the right heading with the date and the piece, in his words plus one line on what it means
in notation, then confirm it in one line (`sw_say`).

## Orchestral writing

General principles: how to think about instruments, lines and phrases. They are not fixed
assignments ("the brass always state the motif"); Brian, Nov 14 2026: "it's a general principle...
you're not hard coding in shit... general principles that you need to be aware of." Examples come
from 111326 (Nov 2026); what belongs to that piece only is in `lab/pieces/p111326_notes.md`.

### What each instrument can do

- **Brass are the least agile and the loudest.** Give them simple lines (a short statement, held
  chords, notes on the beat), not fluid runs: "a brass can't play these fluid lines... it's a very
  easy thing for brass to play." They overpower most of the orchestra, so use them sparingly and
  balance them by dynamics and register: "trumpets are pretty much the loudest instrument in the
  orchestra, and up in that high register at fortissimo they're going to drown out everything else."
- **Players warm up.** A player who has been resting does not come in on a high, exposed note at
  full force: "you expect them to start on that high E? That's just unrealistic. Either move them
  down an octave or have them warm up." An earlier, softer entry can also lead into the new phrase.
  The same holds for woodwinds: "a clarinet way up high, like there's no way a clarinetist can hit
  that, so just off rip." (Nov 17 2026)
- **Strings are the most fluid.** They can take the ornamented, singing lines; when they really
  sing a melody, they double it in octaves.
- **Each instrument has a register where it sounds right, and a tutti covers some of them.** "The
  clarinet is way too high in its register; the flute is in the right register." Under full brass
  and high strings, woodwinds in their middle registers are not heard ("the cor anglais is not going
  to be heard, the clarinet is not going to be heard... the lower wind instruments should be
  contributing to the harmony"): give them figures that cut through, or let them support.
- **Parts of a section keep their order.** Violin I stays above Violin II, Violin II above the
  violas, part 1 above part 2: "violin two is playing higher than violin one... and then they cross
  again... that just doesn't make sense from a school writing perspective, from an orchestration
  perspective." A fix for one problem (a clash) must not make another (a crossing): check again
  after every change. (Nov 15 2026)
- **Every part is heard, or it supports.** Ask of each part whether it can be heard where it is;
  if not, give it a supporting role or let it rest: "if not, should they be supporting some harmonic
  texture?"
- **A chord on one staff is a sketch for the section.** Single-line instruments play one note
  each: spread the chord across the players, copy slurs and dynamics to each, check every range.
  "The horn can only play one note at a time... This is basic school writing... it has to be
  obvious." (Nov 13 2026) The same for a harmony he writes as chords on one string staff: "the
  harmony in the violas again... don't have the violas with that line, exploded out across...
  instruments." (Nov 18 2026)
- **In a tutti, a wind with no line of its own doubles the strings in its register.** The
  woodwinds mirror the string section: flutes and oboes with the violins, clarinets with the
  violas, bassoons with the cellos, the contrabassoon with the double basses. A wind that doubles a
  string part keeps doing it to the end of the phrase, and a part that crescendos into a bar plays
  in that bar: "the clarinets completely drop off, they have a crescendo in bar 48 but then they
  completely drop off in bar 49... maybe the bassoons are doubling what the cellos are doing, maybe
  the clarinets are doubling what the violas are doing... an obvious pattern that we can mimic."
  (Nov 16 2026)
- **The piccolo is not a second flute.** A unison with the flute adds nothing: "a piccolo directly
  doubling the flute at the same register is just awkward orchestration." It plays an octave above
  the flute, or a third or a sixth above where the octave would screech (its top fifth, A7 to C8).
  (Nov 16 2026)

- **The harp accents with glissandi.** In a full texture its job is the glissando that marks a
  figure: "glissandi... accenting certain figures... like a sudden run up and then accenting that
  percussion hit... it can also go down and then up... contrasting with the phrase." A glissando up
  arrives with a stroke (timpani, a low chord in the left hand). (Nov 18 2026)

### Lines and harmony

- **Harmony parts hold their common tones, also over the bar line.** A repeated note is one held
  note, tied over the bar line if it continues: "the harmony tries to be as continuous and fluid as
  possible... if they're not changing their note, just hold them over... sometimes there are
  exceptions." (Nov 13 2026)
- **No hard clashes between the lines and the harmony.** "Be mindful of how the individual lines
  are interacting with the harmonies... some passing tones are fine of course, but no obvious hard
  dissonances, notes within semitones." A held note a minor second or a minor ninth from another
  part is wrong; a short passing note is fine. `lab/clash_check.py` lists them. (Nov 14 2026)
- **Spacing.** A loud melody is not only unisons and octaves: "what about doubling it a minor third
  or a third down, or a sixth below, to fill out the harmony?"
- **Runs complement the melody; they never step on it.** A run stays in its own register and never
  crosses the melody: "make sure the runs are complementing the melody, not interrupting or stepping
  on top of it."
- **Runs may be chromatic.** "Runs don't have to be just broken chords; they can be chromatic at
  times... like Tchaikovsky orchestrates: running winds, sometimes some chromaticism, passing
  notes... it adds color and movement, especially when there's a lot of vibrance."
- **Runs flow across the beat.** A run in sextuplets (twelve to a 2/4 bar) or in sixteenth-note
  triplets that starts just after a beat and arrives on the next one flows; sixteenths that start
  on the beat sound square: "I kind of prefer non on the beat runs... sextuplets... everything is
  just too on the nose... look at what Tchaikovsky does, it's a lot of offbeat fluid stuff that's
  flowing." (Nov 16 2026)
- **Chords under a solo are spread out.** Close triads in a low register turn to mud: "there's a lot
  of tri-chords but maybe we want to space those out better cuz I can imagine it would be very
  muddy." Put the bass low, keep the other chord notes apart, give each note its own player, and
  keep them all under the solo: "nothing really over the cor anglais, it would just be supporting
  harmony underneath." (Nov 16 2026)
- **An imitation answers the solo; it never competes.** A second line can echo the solo's figure in
  its gaps, softly: "a mimicking thing... like a canon almost, but not taking away from the cor
  anglais... the cor anglais is really the central part." It drops out when the solo reaches its
  key moment: "especially when it hits that A B... the flute should kind of drop out." (Nov 16 2026)

### Phrases and transitions

- **A new phrase starts from everything that is already sounding.** "The cohesiveness of the
  phrasing needs to be maintained... look at all the different ideas going on right now, the
  texture, the individual lines: where are they all heading?" Before a new phrase, give every line
  that sounds a fate: it continues, it dovetails into another instrument, it ends smoothly ("it
  doesn't make sense to end abruptly. That's not my style"), or it changes its role (accenting the
  melody or the harmony, a counter-melody). Then decide which instruments join. (Nov 14 2026)
- **A phrase keeps its lead-in.** When a phrase comes back, its pickup comes back with it; if the
  instruments with the melody are busy, instruments that are free take it: "you're missing the G
  fall into that E... it comes out of nowhere."
- **The section that gives up the melody supports the one that takes it.** It accents the new
  melody's figures or holds harmony above it; it does not double it: "the trumpets kind of take
  over... they lead the melody; the violins will be in support, either accenting certain figures or
  provide harmonies on top." (Nov 18 2026)
- **Melody hand-offs overlap, and accompaniment dovetails.** The new instrument enters on the
  upbeat while the old one finishes; an accompaniment passes to the next section on the same chord
  and voicing, on a downbeat, the leaving section fading as the entering one comes in softly.
- **Hand-offs are fluid.** An instrument that takes over a line arrives smoothly, and one that
  leaves a line for a new role leaves it smoothly. If the next note is far from where it was, it
  runs or steps there (a scale, a sextuplet run): "the violin one literally goes up like an
  octave... it needs to be a fluid transition, maybe a sextuplet run or some type of thing, to make
  it a more natural transition"; "to go from that high B all the way down more than an octave to a
  lower A, it's just kind of awkward." An instrument that joins a line in a far register gets a
  bar or two to reach it, then doubles: "we could have bar 41 and 42 be a transition for the
  violins to start to reach up to that register and then be fully doubling the flutes... this is a
  pattern, I will point this out every single time." (Nov 14-15 2026)
- **A loud arrival never comes out of nowhere.** Build into it with rhythm and lead-ins: "this
  fortissimo again is coming out of nowhere... it's just not natural, it's not a smooth transition."
  A forte never follows a diminuendo; the bars before it grow into it: "a diminuendo in the strings
  and then that forte on bar 86 doesn't make sense." (Nov 17 2026)
- **Loud passages keep their rhythm.** Held notes everywhere make a static tutti: "all the rhythm
  just stops... the rhythm should be pounded, through string runs or percussion or wind runs."

### Dynamics and articulation

- **The melody rings out.** The accompaniment sits under it ("the strings can't overpower the
  flute"); write a dynamic for every part, or the loud ones cover it.
- **Dynamics follow the melody.** Subtle at the start, a crescendo to the high point, a
  decrescendo as the line falls; the end of a phrase recedes, most of all under the next entry.
- **Breath in the line.** An eighth-note upbeat is slurred into the next downbeat quarter, and that
  quarter is portato (tenuto-staccato): "somewhere in between a normal note and a staccato... a lot
  of breath into the melody." Long slurs cover flowing runs.
- **Winds slur by phrase and breath; strings slur by bow.** A wind part does not copy the strings'
  slurs one to one: "the winds in general shouldn't be following slurring patterns of the strings;
  the strings' slurring patterns are for their bowing techniques, but the winds are for actual
  phrases and breaths... in fact winds should be slurring more most of the time." One slur over each
  phrase, with a breath at its end. (Nov 17 2026)
- **Flowing runs are slurred.** A run in a flowing texture is played legato, in one bow or one
  breath: "they should be slurred... it should be a flowing texture, therefore the run should be
  slurred... the violin playing detache up that run just doesn't make sense." Repeated notes that
  only add texture can stay detached. (Nov 15 2026)
- **Phrase marks go with the music.** A theme that moves to another instrument keeps its slurs and
  articulation, and every player in a texture gets the phrase slurs ("the strings need their slurs
  as well"). A new melody in the same style takes the same marks: "the quarter notes should be like
  that same quarter notes accents that we've been using this whole time... similar slurring as
  before." (Nov 16 2026)

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
