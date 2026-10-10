"""MusicXML -> MIDI -> audio, so a model can HEAR a score instead of reading about it.

Exists because Brian observed that the model's written descriptions read like someone looking at a
score rather than hearing it. Testing that needs actual audio. Requires `brew install fluid-synth`;
ffmpeg on this machine is broken (missing libvpx), so conversion uses macOS `afconvert`.

    python render_audio.py "Briello no 36 in D# minor"
"""
import os, sys, subprocess
from music21 import converter

SF = '/usr/local/lift/Soundfonts/FluidR3_GM2-2.sf2'
D = '/Users/bdogellis/Documents/Score Exports/MusicXML/'
OUT = '/Users/bdogellis/Documents/Score Exports/_audio/'

def render(stem):
    os.makedirs(OUT, exist_ok=True)
    mid, wav = OUT + stem + '.mid', OUT + stem + '.wav'
    converter.parse(D + stem + '.musicxml').toSoundingPitch().stripTies().write('midi', fp=mid)
    subprocess.run(['fluidsynth', '-ni', '-F', wav, '-r', '44100', SF, mid],
                   check=True, capture_output=True)
    # mono 16k wav for model input; m4a for a human to listen to
    subprocess.run(['afconvert', '-f', 'WAVE', '-d', 'LEI16@16000', '-c', '1',
                    wav, OUT + stem + '_16k.wav'], check=True, capture_output=True)
    subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '48000',
                    wav, OUT + stem + '.m4a'], check=True, capture_output=True)
    os.remove(wav)
    return OUT + stem + '_16k.wav', OUT + stem + '.m4a'

if __name__ == '__main__':
    for s in sys.argv[1:]:
        print(*render(s), sep='\n')
