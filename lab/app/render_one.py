"""Render one score to <stem>.svg and <stem>.audio.txt in a fresh process (verovio is not thread-safe).
usage: python app/render_one.py <score.musicxml> <out_stem> <session_dir>"""
import sys, os, re, base64, hashlib, subprocess
sys.path.insert(0, '/Users/bdogellis/repos/scorewright'); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
xml_path, stem, sdir = sys.argv[1], sys.argv[2], sys.argv[3]
import diffview, xmledit
xml = open(xml_path, encoding='utf-8').read()
last = max(int(m) for m in re.findall(r'<measure number="(\d+)"', xml))
svg = diffview.render(xmledit.excerpt(xml, 1, last, None), width=1400, timemap=True, n_parts=99)[0]
if '<svg width="0px"' not in svg:
    open(stem + '.svg', 'w').write(svg); print('svg ok', len(svg))
else:
    print('svg EMPTY')
key = hashlib.md5((xml_path + str(os.path.getmtime(xml_path))).encode()).hexdigest()[:12]
mp3 = f'{sdir}/audio_{key}.mp3'
if not os.path.exists(mp3):
    subprocess.run(['/Applications/MuseScore 4.app/Contents/MacOS/mscore', '-o', mp3, xml_path], capture_output=True, timeout=180)
if os.path.exists(mp3):
    open(stem + '.audio.txt', 'w').write('data:audio/mpeg;base64,' + base64.b64encode(open(mp3, 'rb').read()).decode()); print('audio ok')
# bar start times (seconds) for play-from-bar, following the score's metronome marks
try:
    from music21 import converter
    s = converter.parse(xml_path)
    bpm = 120.0; out = []; t = 0.0
    marks = {}
    for mm in s.recurse().getElementsByClass('MetronomeMark'):
        try:
            q = mm.getQuarterBPM()
            if q: marks.setdefault(mm.measureNumber, q)
        except Exception: pass
    for m in s.parts[0].getElementsByClass('Measure'):
        if m.number in marks: bpm = float(marks[m.number])
        out.append([m.number, round(t, 3)])
        t += float(m.barDuration.quarterLength) / bpm * 60
    import json; open(stem + '.bars.json', 'w').write(json.dumps(out)); print('bars ok', len(out))
except Exception as e:
    print('bars failed', e)
