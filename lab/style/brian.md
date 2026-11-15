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
  obvious." (Nov 13 2026)

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
- **Melody hand-offs overlap, and accompaniment dovetails.** The new instrument enters on the
  upbeat while the old one finishes; an accompaniment passes to the next section on the same chord
  and voicing, on a downbeat, the leaving section fading as the entering one comes in softly.
- **Hand-offs are fluid.** An instrument that takes over a line arrives smoothly, and one that
  leaves a line for a new role leaves it smoothly. If the next note is far from where it was, it
  runs or steps there (a scale, a sextuplet run): "the violin one literally goes up like an
  octave... it needs to be a fluid transition, maybe a sextuplet run or some type of thing, to make
  it a more natural transition"; "to go from that high B all the way down more than an octave to a
  lower A, it's just kind of awkward." (Nov 14-15 2026)
- **A loud arrival never comes out of nowhere.** Build into it with rhythm and lead-ins: "this
  fortissimo again is coming out of nowhere... it's just not natural, it's not a smooth transition."
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
- **Flowing runs are slurred.** A run in a flowing texture is played legato, in one bow or one
  breath: "they should be slurred... it should be a flowing texture, therefore the run should be
  slurred... the violin playing detache up that run just doesn't make sense." Repeated notes that
  only add texture can stay detached. (Nov 15 2026)
- **Phrase marks go with the music.** A theme that moves to another instrument keeps its slurs and
  articulation, and every player in a texture gets the phrase slurs ("the strings need their slurs
  as well").

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
