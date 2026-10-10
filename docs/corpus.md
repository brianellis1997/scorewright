# Corpus and retrieval

Brian's own scores are the source of his idiom. COMPOSING.md section 4 puts it plainly: his style is retrieved, not guessed. This page covers what the archive is, how it was exported, what derived files exist, and the retrieval tools.

All paths below are in `~/Documents/Score Exports` (`$E`). `W` is the whisperer python, `T` the text2score python (see [CLAUDE.md](../CLAUDE.md)).

## The archive: `MusicXML/`

- About 1,609 unique Sibelius scores, deduplicated by content hash from 3,450 `.sib` files. The staged copies are in `_source_sib/` (1,609 files). Their modification times are the original composition dates, 2016 to 2022, and `corpus_find.py` and the unfinished-piece scan use them.
- Exported Aug 28 2026 with Sibelius's ConvertFolderToMusicXML batch plugin: 1,607 files, 1.0 GB. A memory exhaustion killed the first run at 1,211 files; it was resumed in chunks.
- By content hash only 16 files are redundant (1%). They were not deleted. `Ballad 1` and `Fur Maddie` are the same piece.
- MusicXML was chosen over MIDI because it keeps dynamics, slurs, articulations, text, instrument names and enharmonic spelling.
- About half the multi-part scores are stored at written pitch: 42 of 76 sampled have `<transpose>` elements. Never assume concert pitch; check `<transpose>`, or `transpose=` in the dump's header.

**Read only.** It is the only copy, and it cost a licence recovery and two days to produce. Nothing edits it. A session copies a score in (`sw_working.py`), and the composing tools write into `lab/`.

## File names

Sibelius's `SaveAs` treated everything after the last period in a name as an extension. In the August export:

- two scores collided with a sibling and were overwritten: "Variations on a Mozart No.1" (2016) and the June 2018 "52818 8";
- thirteen came out with shortened names. `String Quartet No.musicxml` is "String Quartet No. 1". `Concerto NO. 1.musicxml` is really "Concerto NO. 1. Em", and `Concerto NO.musicxml` is "Concerto NO. 1".

`_logs/archive_name_map.json` has 15 entries: those 13 plus the two collision survivors (`52818 8.musicxml` is the May "52818 8.0", `Variations on a Mozart No.musicxml` is "No. 2"). Each entry gives the real title and the file with the same music in `extra_sept2026/`. The archive was not renamed, and should stay that way.

## `extra_sept2026/`

48 scores exported on Sept 22 2026, before the Sibelius subscription ended. Folders `MusicXML/`, `PDF/`, `MIDI/`, `src/` (period-free `.sib` copies), plus `manifest.json` (origin and reason for each file) and `README.txt`. Periods in names became underscores.

Why they were missing from the archive:

- the two filename collisions, and the 13 shortened names (re-exported under their full names);
- pieces that only ever lived as email attachments, 2018 to 2020 (Owl, Songbird, Flamingo, Save the Infants, Temperament, Cristobal and others);
- one title that was never staged, "Miniature no 1 (2021)";
- about a dozen pieces where a newer copy existed than the one exported, named `<title> - newer <date>`.

They were found by a content-hash audit of all 3,992 `.sib` files outside `_source_sib` (1,942 unique, 341 never staged, most of those auto-backups and Double/Half variants). The MusicXML came from Sibelius 2026.8 through a one-shot plugin (`lab/sibelius_SWExport.plg.txt`, run from the ribbon's Command Search, log in `_bridge/swexport.log`). PDF and MIDI came from MuseScore, except four scores MuseScore rejects: three reuse the archive's PDF and MIDI of identical music, and "73119 - newer 2019-07-31" was engraved by Verovio.

These 48 are not in the retrieval index or in `abc_reduced/`, which both predate them. `dump_abc.py` reads them directly.

The lesson went into PROJECT.md section 54: verify an export against its sources by content, never against its own outputs by name. "1,607 / 1,607, zero missing" was true of the outputs and false of the archive.

## `PDF/` and `MIDI/`

1,607 of each, made Aug 30 2026 without Sibelius. MuseScore's command line, fed job files in chunks, did 1,482. Another 113 needed a music21 re-serialisation first, because MuseScore exits with code 40 on some quirk of Sibelius's export. The last 11 PDFs came from Verovio printed through headless Chrome, and the last 2 MIDIs from music21 with the repeat marks stripped.

Known quirks: the "Concerto NO" and "Symphony No.1" MIDIs play once through, because their repeat structure is malformed in the source. The 11 Verovio PDFs (the three Gettysburg Day 1 variants, Tragic, Concerto No. 1 and others) look different from MuseScore's engraving.

## Derived files

| path | what | used by |
|---|---|---|
| `compact/` | the Aug 28 compact encoding of all 1,607 scores, with `_meta/`. Keeps pitch, duration and dynamics; drops slurs, hairpins, tempo marks, ornaments | `retrieve.py` |
| `retrieval.sqlite` | the n-gram index, 112 MB | `retrieve.py`, `brief.py` |
| `abc_reduced/<key>/` | rest-reduced interleaved ABC in the original key, 1,599 scores, rebuilt Sept 3 with `reduce_interleaved.py` | `corpus_find.py` |
| `abc/`, `abc_interleaved/`, `abc_augmented/` | NotaGen conversion and preprocessing (Aug 29) | training only |
| `plans/`, `docs*.jsonl`, `edits*.jsonl` | Text2Score plans and training documents | training only |
| `_corpora/` | PDMX, OpenScore Lieder and quartets, the IMSLP file census | training only |
| `_models/` | NotaGen, NotaGen-X, Text2Score and CLaMP 2 weights, and every fine-tuned checkpoint, including `cloud/t2s_edit_cloud.pth` from the GPU day | not used by the harness |
| `working/` | living copies from the Aug 29 `scorewright.py` loop, a git repo | not used by the surface |
| `_scorewright_out/` | session folders, standalone green files from Sept 4, `brief.py` caches | the surface, `brief.py` |

## Retrieval: `retrieve.py` (repo root)

It answers "where have I written this shape before?"

- What is indexed: every window of five consecutive notes (four intervals) in every part and voice of the compact cache. A chord contributes its top note, where the line lives. A rest breaks the phrase. Windows that are one repeated note are skipped. Each window gets two keys: the intervals alone, and the intervals plus quantised duration ratios.
- Why intervals and rhythm, not harmony: they are transposition- and tempo-invariant, deterministic, and need no harmonic analysis. Roman numerals were the weakest part of the August work, and his MIDI-entered spelling breaks them.
- Ranking: inverse document frequency, so a shape found in three scores says more than one found in ten thousand. Interval-plus-rhythm matches weigh 1.6 times as much. Shapes in more than a quarter of all scores are ignored. Each n-gram is credited once per 8-bar region of the other score, so a piece that repeats one figure twenty times does not outrank a piece sharing twenty different figures. The query's own score is excluded.
- Build: `$W retrieve.py --build` deletes and rebuilds `retrieval.sqlite` from `compact/` (about 12 s; 2,661,682 postings).
- Query: `$W retrieve.py --query "<stem>" <lo> <hi> [--part N]` prints weight, score, part, bars and match count. (The example in the module docstring passes one bar number; the parser wants both.)
- Reading a hit: `excerpt_text(stem, lo, hi, part)` returns the compact notes for those bars plus, from the real MusicXML, a notation line: slur count (or "NO slurs"), articulations, ornaments, dynamics, hairpins. That line exists because the compact cache has no slurs, and a model once described retrieved passages as slurred when one of them had none.
- Form map: `self_map(stem)` runs the index against the piece itself and reports which 4-bar blocks restate which.

Limits: melodic shape only. Inner voices are invisible because only the top note of a chord counts. A hit is located to an 8-bar block, not a beat. Similar is not the same as relevant.

A held-out benchmark (PROJECT.md section 40c, 164 test scores) found retrieval doubles the baseline on predicting the next interval and is worse than the baseline on rhythm. Take shapes from the corpus and rhythm from the piece in front of you.

## `brief.py`

    $W brief.py "<stem>" [last_written_bar] [part] ["instrument regex"]
    $W brief.py "String Quartet No" 16 0 "violin|viola|cello"

For an archive piece, by stem. The first run converts `$E/MusicXML/<stem>.musicxml` through `dump_abc.py` (under the text2score python) and caches it in `$E/_scorewright_out/<stem>_reduced.txt`. The cache is never refreshed; delete it to rebuild.

It prints:

- `=== HEADER`: the `L:`, `M:`, `K:`, `Q:`, `V:` and `%%score` lines;
- `=== FORM`: the number of bars, the last bar with notes (or the one you pass), the runs of empty bars (section breaks or the gap), and every bar with text, a tempo, meter or key change, or a double bar;
- `=== LAST WRITTEN BARS`: the last five;
- `=== RETRIEVAL`: up to six passages from his other scores that share the shape of the last four written bars, in his notation with slur and dynamic counts. With an instrument regex it searches the top 60 hits and keeps those from matching parts.

For a piece in progress in a session, run `dump_abc.py` on the session's `working.musicxml` instead; `brief.py` only sees the archive version.

## `corpus_find.py`

    $W corpus_find.py "<instrument regex>" [key] [meter] [since YYYY-MM-DD] [max]
    $W corpus_find.py "violin|viola|cello" "" 4/4 2019-01-01 8

For a new piece, where there is no passage to match yet. It reads every file in `abc_reduced/*/`, keeps scores whose part names match the regex and whose `K:`, `M:` and date match, and prints the newest first (12 by default): date, stem, key, meter, tempo, bars, number of parts, part names. Read two or three of the closest with `dump_abc.py` before writing a bar.

## Measured idiom

COMPOSING.md section 4 has the numbers for his string writing (46% of string notes under a slur, slurs of two to four notes, hairpins and accents everywhere, staccato on accompaniment pulses) and the standing rule: measure the idiom in his corpus before guessing.

Marking counts across his corpus, in lines of ABC (PROJECT.md section 52a): `!<(!` 16,727, `!>(!` 12,595, `!tenuto!` 2,187, `!ped!` 2,068, `!ped-up!` 1,753, `!arpeggio!` 1,171, `!fermata!` 838, text annotations 6,349.

## Unfinished pieces

Many of his scores stop early. Measured on Aug 29 (PROJECT.md section 23a): 209 pieces leave eight or more empty bars after the last note, 452 scores are more than 40% empty, 212 have a completely silent part, and 144 are 16 bars or shorter.

`lab/unfinished_piano_since_fall2018.txt` lists unfinished solo piano pieces dated Sept 1 2018 or later. The scan found 66; the file shows the first 25, newest first. On Sept 4 2026 Brian made these the working set and asked for no more tests on the Piano Sonata in Gm BEM 001, which he dislikes.
