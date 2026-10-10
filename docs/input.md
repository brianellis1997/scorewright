# Input: voice, takes, hum and uploads

Besides typing, Brian has four buttons in the page: 🎤 talk, 🎹 take, 🎵 hum, 📎 upload. The recording buttons use the browser's microphone, which browsers allow only on HTTPS or localhost; on the phone that is why the page is opened through the Tailscale HTTPS address.

## 🎤 Talk

Browser speech recognition (Chrome, and Safari on the iPhone), English, continuous, with interim results written into the text box as he speaks. Nothing is sent until he presses Send or Enter, so he can fix misheard words first. Pressing 🎤 again stops it, and Send stops it too. In a browser without speech recognition the button is disabled. After a Reject the mic starts by itself so he can say why.

## 🎹 Take: play and talk

For playing an idea on the piano and talking about it in one go.

1. He presses 🎹. The page calls `/api/take/start`, so the server notes the start time and reports the MIDI ports it can see, then records the mic with echo cancellation, noise suppression and automatic gain all off. The button's tooltip lists the MIDI ports, or says "no MIDI keyboard seen, using the piano model on the audio".
2. He plays and talks. Talk before or after playing, not over it.
3. He presses 🎹 again. The browser decodes the recording to a mono 16-bit WAV and posts it to `/api/take/stop` ("listening back… (speech and piano, up to a minute)").
4. The server saves `take_HHMMSS.wav`, collects every MIDI note-on and note-off received between start and stop into `take_HHMMSS.midi.json`, and runs `listen.py` at the working score's tempo (its first metronome mark, 120 if none).
5. The take box shows "I heard (midi or piano model): ...", the notes on a small two-staff score, and his words in an editable box. "use it" sends it; "discard" closes the box.
6. "use it" posts `/api/take/use`. The chat and the inbox get `[TAKE take_HHMMSS] <his words>`, and the inbox line also carries `take` (the `.abc` path), `wav` and `midi` (the `.midi.json` path).

MIDI comes from any keyboard plugged into the Mac. The server opens every MIDI input it sees (it rescans every 2 s) and buffers notes the whole time it runs, so a keyboard can be plugged in at any point.

### What `listen.py` does

`listen.py <wav> <bpm or auto> [midi.json or -] [stem] [--upload] [--out=dir]`, whisperer env. Prints one JSON line.

- Words: Whisper `base`, English, with word timestamps. The audio is loaded with librosa at 16 kHz, because Whisper's own loader calls ffmpeg. For a take the words are Whisper's whole transcript. Segments with `no_speech_prob` under 0.6 supply the speech spans, with words less than half a second apart merged into one span.
- Notes: if MIDI arrived, those notes as played, exact. Otherwise the ByteDance piano transcription model (`piano_transcription_inference`, on the CPU) runs on the audio, also loaded through librosa. Its notes are then cleaned: anything starting within 0.15 s of a speech span is dropped, and so are ghosts, notes shorter than 120 ms or quieter than velocity 30.
- Quantising: onsets within 100 ms count as one chord (model jitter, real hands). Onsets and lengths are rounded to eighths at the given tempo. Bars are always 8 eighths, 4/4, whatever the piece's meter. A note that crosses a barline is split and tied.
- Hands: the split point is the emptiest pitch between G#3 and G#4 (MIDI 56 to 68), ties going to the one nearest D4. Notes at or above it go to V:1 as the right hand, notes below to V:2. The summary names the top note of each right-hand onset as the melody.
- Output: per-bar lines `[b:i][V:1]...|[V:2]...|` in C with sharps written out, a "heard" summary (the first 24 melody notes, the first 8 chords), and an SVG made with `abc2xml.py` and Verovio. Rendering writes `<stem>.abc` and `<stem>.xml` into `lab/app/` as a side effect.

### What to trust

From COMPOSING.md section 9: MIDI is exact. The audio model was tuned on a phone recording of his real piano (Sept 7 2026), which is where the 100 ms chord window, the ghost filter and the adaptive hand split came from. It is useless on hummed or synthetic tones. Rhythm is his "future problem": trust pitches and register, treat durations as a sketch.

Other limits worth knowing:

- Takes are quantised as 4/4 even in a 3/4 or 6/8 piece.
- Takes do not hold `_bridge/heavy.lock`, so a take during a Dorico render competes with it for the CPU.
- A server restart during a take reloads the page, and the take is lost.

## 🎵 Hum

For singing or humming a line.

1. He presses 🎵, hums, presses again.
2. The browser decodes the recording to WAV and posts it to `/api/hum`. The server saves `hum_HHMMSS.wav` and runs `hum.py` with the anaconda base python (`HUM_PY` in `server.py`, `/Users/bdogellis/opt/anaconda3/bin/python`), at the working score's tempo, with a 120 s timeout.
3. `hum.py` tracks pitch with librosa's pyin (70 to 1100 Hz) and finds onsets. A new note starts when the pitch moves more than 60 cents from the running median, or at an onset once the current note has lasted 80 ms. Segments under 80 ms are dropped, and re-attacks of one pitch across gaps under 20 ms are glued back together. Lengths are rounded to eighths, at least one.
4. The text box gets `[HUM] I heard: D#5(2) E5(1) ... | ` appended, lengths in eighths. He corrects it and sends it like any other message.

The weak spot is a repeated note on one pitch, which only an onset can split. Treat what arrives as his intent, not gospel. `hum.py` converts non-WAV input with ffmpeg, but the page always sends WAV.

## 📎 Upload: any recording or video

For a recording he already has: a voice memo, a video of him playing, an improvisation.

1. 📎 opens the file picker (any audio or video type). The page streams the file as it is to `/api/upload?name=<file name>` and shows the percentage. On failure it says "upload failed. Try again on Wi-Fi."
2. The server writes it to `uploads/upload_HHMMSS_<name>` in the session folder, returns the job id, and starts a background job.
3. The job waits for `_bridge/heavy.lock` ("waiting for the Mac to finish a playback render"), then runs `media.py`, which pulls the audio track out with PyAV into a mono 16-bit 22,050 Hz `upload_HHMMSS.wav` ("extracting audio"), then `listen.py --upload` with the tempo set to `auto` ("transcribing").
4. Upload mode differs from a take in four ways: a strict speech filter (`no_speech_prob` under 0.4, `avg_logprob` above -0.8, compression ratio under 2.2, no conditioning on earlier text) because Whisper invents words over music; tempo from librosa beat tracking, folded into 60-160 bpm; a preview of only the first 16 bars; and a MIDI file of every note, `upload_HHMMSS.mid`.
5. The page polls `/api/job` every 2.5 s and shows the status and elapsed seconds, with the note "A recording takes about two thirds of its own length to transcribe."
6. When it is done, the take box shows the note count, bars and tempo, the 16-bar preview, a MIDI download link, and the words. "use it" sends `[TAKE upload_HHMMSS] <his words>`; here `midi` points to `upload_HHMMSS.midi.json`, the transcribed notes as JSON.

Files in the session folder: `uploads/upload_HHMMSS_<name>`, `upload_HHMMSS.wav`, `.abc` (every bar), `.svg` (the preview), `.midi.json`, `.mid`.

Measured on Sept 23 2026 (PROJECT.md section 56) with a 2 min 22 s MuseScore rendering of "Nocturne no 6": extraction about 1 s, transcription with tempo detection about 90 s, 832 notes, 828 of them matching the score, tempo 99.4 detected against 100 written. Expect a 10-minute improvisation to take 6 to 7 minutes and give a few thousand notes. A phone recording of a real piano in a room will score lower.

Upload job status lives in the server's memory. If the server restarts mid-job, the page reports "could not transcribe that: unknown"; upload again.

## Using a take or upload (for Claude)

- The inbox line gives the paths. The session's `.abc` file holds only the per-bar lines, no header: units are eighths (`L:1/8`), bars are 4/4, key C with sharps written out, V:1 right hand, V:2 left hand.
- `listen.py` writes a natural (`=`) when a bar returns to a pitch it sharpened earlier, since under ABC rules an accidental lasts to the end of the bar. Takes made before Oct 9 2026 lack these: in their `^C C` the second note reads as C sharp.
- Move it into the piece yourself: re-bar it to the piece's meter if it is not 4/4, respell it in the piece's key, put it in the right register and voices.
- MIDI takes are exact. For the audio model, trust pitches and register and treat rhythm as a sketch. His words in the same message say what he means by it.
