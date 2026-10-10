# History

How Scorewright went from "train a music model" to "a frontier model plus a harness". Condensed from `~/Documents/Score Exports/PROJECT.md`, which has every measurement; section numbers below point into it.

## Aug 28 2026: the corpus and the first plan (sections 1-14)

- Sibelius licence recovered. 3,450 `.sib` files deduplicated by content to 1,609; 1,607 exported to MusicXML.
- The framing from day one: Claude Code for music notation. The first plan was an analysis layer (harmony, voice leading, ranges, texture, form) for a model to reason over.
- Raw MusicXML was too big (median solo piece 68k tokens, Gettysburg Day 3 10.2M), so a compact encoding was built at about 1.8% of the size.
- Checking the claims broke things. The encoder silently lost notes in about a quarter of the corpus. Key detection was 77.5% right against 307 titled pieces. Roman numerals were computed in the wrong key.
- Format test: five frontier models all got Briello no 36's key wrong from the compaction. From stripped MusicXML, which states the key, all four that answered got it right. Settled: stripped MusicXML is the working representation.
- Hearing against reading: the same model described a piece differently from audio and from the score. Brian's own words sat between the two.

## Aug 29: the edit loop, built and broken (sections 15-45)

- `xmledit.py` edits the MusicXML text surgically, because music21's writer turns a no-op save into an 11,071-line diff. Verovio renders; `diffview.py` drew red and green diffs.
- `scorewright.py` drove models over OpenRouter with source tags on every claim. The edit vocabulary grew to 11 ops, and `retrieve.py` indexed every melodic shape in the corpus in 12 seconds.
- A pattern settled in: models get the gestalt right and single symbols wrong. Anything where off-by-one matters gets computed and handed over.
- Orchestral work exposed one silent bug after another: every edit landed on Flute 1, 422 of 458 notes played on one MIDI channel as a contrabass, and every transposing instrument was out of tune in every render. Brian: "you're not actually testing this and looking at it yourself." The rule since: verify the object, not a proxy.
- About $8-12 of OpenRouter credit went on whole-score prompts. `offline.py` then put Claude Code itself in the loop at $0.
- Sibelius threw away MusicXML note colour, showed an import dialog on every open, and its plugin colour writes did not persist. It left the loop; the browser became the review surface.
- NotaGen-X (516M parameters, open weights) resolved a pickup zero-shot in one run. Twelve more runs showed that first run was a lucky draw.
- Instruction-gated sampling picked two "winners"; Brian rejected both. "You're the one scoring, but you don't know music." Gates certify "not broken", never "good".

## Aug 30 to Sept 2: training (sections 46-49)

- NotaGen small (110M) fine-tuned on his corpus overnight on the M1. Blind A/B: his model "just a little better... but they both kinda suck."
- No-spend rule: free tracks only until the project shows more potential. PDF and MIDI for all 1,607 scores made without Sibelius.
- Field check (section 48): no "GPT-3 for scores" exists, and all the machine-readable symbolic music in the world is roughly 1-2M pieces, mostly folk tunes and solo piano. Parameter count was not the constraint. Conclusion at the time: build Cursor-for-scores, not a base model.
- Text2Score (NotaGen's architecture plus a per-bar plan) ported into its own `text2score` env. Decode-time voice masks made the instrumentation exact. The notes were still "awful, out of tone", and his first verdicts had been on renders that an ABC comment bug had broken.
- Text2Score fine-tuned on his scores with plans: eval loss 0.71 to 0.31, and all six blind samples unusable. Measured cause: winds against the strings' harmony 35-64% of the time, against his 4.6%.
- Section 49 designed one model for instructed infill, trained on edits derived by removing something and asking for it back (his corpus, OpenScore, PDMX's 254K scores). IMSLP turned out to be PDFs behind a CAPTCHA.
- Bugs in the data itself: a third of his rest-reduced files were truncated; `reduce_interleaved.py` fixed it.

## Sept 3: data loss and the laptop ceiling (section 49)

- macOS purged the `/tmp` scratchpad and took a dozen scripts with it. Everything moved into `lab/`.
- The laptop's 512-patch window could not see an orchestra. Piano edits were plausible but landed in the wrong bars; dictating the bar addresses fixed placement.
- First non-negative verdict, on a left-hand fill in the G minor sonata: "actually pretty good".
- Continuations of an unfinished piece "literally go below what is playable on a piano". A range mask in the decoder stopped that.

## Sept 3-4: the GPU day (sections 50-51)

- One H100 pass on RunPod over 280,658 instructed-edit documents: $50.02 of a $60 budget.
- Held-out loss fell from 0.313 to 0.129. The bar-level pass rule fixed in advance failed.
- Two bugs a free dry run would have caught: a crop counted characters instead of patches and dropped 40-67% of the doubling and harmony documents, and a countdown habit from pretraining ended answers after one or two bars.
- The Mac crashed during a Mac-side benchmark run with the MPS memory ceiling switched off. Since then: no MPS training on the Mac, and no spend without a dry run (`lab/PREFLIGHT.md`).
- Every piano continuation from the new checkpoint scored 0 or 1. "God awful." "Listening to a completely different piece."

## Sept 4: the pivot (sections 51w-52)

- Brian: "this has been done in other modalities, coding agents; what are we missing?" Coding agents sit on frontier base models trained by others. Three days had gone into building the base at a thousandth of the scale.
- The test: Claude read the ABC of "3 5 piano" and wrote bars 36-43 itself, with two more pieces alongside. Verdict on all three: "a significant improvement" over the model, but "not my style", and "did you read the entire piece?" It had read 10-12 bars.
- Take 2, after reading all 35 bars, brought the opening theme back in the last section's key. "Holy shit, great job... that's more like it." Score 4, the first positive score in the log.
- New direction (section 52): a frontier model reading the whole score, the notation tools already built, and his verdicts as the eval set. Claude cannot be fine-tuned through Anthropic's API, so specialisation means reading, retrieving his own scores, and rules taken from his verdicts. NotaGen stays optional.
- The same afternoon and evening: the quartet "sounded like something I would compose" (4), his string idiom was measured over 332 scores, pedal retakes were fixed, a band orchestration of Bright Valley 18-81 drew "very impressed, awesome job" (4), and `lab/COMPOSING.md` was written so the procedure could be repeated by any model.

## Sept 4-7: the surface (section 53)

- `lab/app/`: the server, the phone page, the MuseScore panel. The first composed bars were accepted that evening, in session `quartet2`.
- Bars 41-48 of the quartet took fifteen takes (S12 to S26). The rules from those rejections are in COMPOSING.md section 2.
- S30 to S33 were turned down as "the same texture over and over" and "what story are we telling". He said "cut", and the working score went back to 48 bars.
- Phone access through Tailscale, the server under launchd, hum and take buttons.

## Sept 22-23: off Sibelius (sections 54-56)

- An export audit found the August export incomplete because of periods in file names. 48 more scores went to `extra_sept2026/`, and then the Sibelius subscription was cancelled.
- Dorico 4 became the notation app. NotePerformer renders through Dorico were wired into the page, along with new pieces from the header menu and uploads of any recording or video.

## Where it stands (Oct 9 2026)

- Oct 9: the first whole song. Claude wrote the lyrics ("Where I Left It"), then set them for English horn and piano after his 14 song studies, words under the notes (`lab/songs/where_i_left_it.py`, PROJECT.md section 57). It is S1 of the piece `where-i-left-it`, the current piece. His verdict: impressive, lyrics and pedalling right, but "too pop, saccharine, on the nose, no mystery", one accompaniment rhythm for too long, abrupt key changes, fades that stopped before the held notes, no ritardando. S1 rejected. `lab/style_profile.py` measured his 17 songs and S1: S1 fell outside his range on 8 measures (melody on plain chord tones 80% of beats, one figure for 72 bars). S2 (`lab/songs/where_i_left_it_s2.py`) was rewritten and measured until it fell inside on all of them, and posted the same day. `quartet2` keeps its 48-bar working score with S34 (bars 49-65) still open.
- 125 lines in `_bridge/verdicts.jsonl`. The GitHub repo went public on Oct 9 2026.
- Open items from section 55: pick a public name ("Scorewright" is already taken by scorewright.com), and re-test the 🎹 take with a real piano. From section 56: grant Accessibility to the whisperer python so the NotePerformer helper can run under launchd.
- The bet behind it, from section 45: an owner's own corpus plus his own verdicts are the two things a single composer can supply that the field lacks.
