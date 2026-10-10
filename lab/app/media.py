"""Extract the audio track of any audio or video file (mov, mp4, m4a, mp3, wav, webm, ...) to a mono
16-bit WAV. PyAV ships its own FFmpeg, so this works while Homebrew's ffmpeg is broken on this Mac.
usage: python media.py <input> <output.wav> [sample_rate]"""
import sys
import av
import soundfile as sf

src, dst = sys.argv[1], sys.argv[2]
sr = int(sys.argv[3]) if len(sys.argv) > 3 else 22050
with av.open(src) as c:
    stream = next((s for s in c.streams if s.type == 'audio'), None)
    if stream is None:
        sys.exit('no audio track in ' + src)
    rs = av.AudioResampler(format='s16', layout='mono', rate=sr)
    n = 0
    with sf.SoundFile(dst, 'w', samplerate=sr, channels=1, subtype='PCM_16') as out:
        for frame in c.decode(stream):
            for f in rs.resample(frame):
                a = f.to_ndarray().reshape(-1); out.write(a); n += len(a)
        for f in rs.resample(None):
            a = f.to_ndarray().reshape(-1); out.write(a); n += len(a)
print(f'ok {dst} {n / sr:.1f}s')
