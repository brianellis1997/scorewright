"""111326 S4 (Nov 13 2026): S3 with the strings' repeated quarter notes held. Brian: "the strings
have some quarter note repeats, those should be half notes, not individual quarter notes. They're
just harmony, so it needs to seem smooth." Where a player repeats a note inside a bar (the viola in
bars 18 and 19, Violin II in bar 19), the two quarters become one half note, and a slur that ended
on the second quarter ends on the half note. The notes that move (Violin I G-F and E-D, Violin II
E-D) keep their quarters, so the inner line still moves.
usage (whisperer env): python lab/pieces/p111326_s4.py <S3.musicxml> <out.musicxml>"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from p111326_s2 import measure_span, pitch_of, sounding  # noqa: E402
from xml_marks import pitches  # noqa: E402

TYPES = {2: 'eighth', 4: 'quarter', 8: 'half', 16: 'whole'}


def merge_repeats(x, pid, bars):
    for bar in bars:
        s0, s1 = measure_span(x, pid, bar)
        body = x[s0:s1]
        notes = [m for m in re.finditer(r'<note[ >].*?</note>', body, re.S)]
        for a, b in zip(notes, notes[1:]):
            ta, tb = a.group(0), b.group(0)
            if any(('<rest' in t or '<chord/>' in t) for t in (ta, tb)) or pitch_of(ta) != pitch_of(tb):
                continue
            if body[a.end():b.start()].strip():
                continue
            d = int(re.search(r'<duration>(\d+)</duration>', ta).group(1)) + int(re.search(r'<duration>(\d+)</duration>', tb).group(1))
            merged = re.sub(r'<duration>\d+</duration>', f'<duration>{d}</duration>', ta, count=1)
            merged = re.sub(r'<type>\w+</type>', f'<type>{TYPES[d]}</type>', merged, count=1)
            stops = re.findall(r'<slur type="stop"[^>]*/>', tb)
            if stops:
                merged = merged.replace('</notations>', ''.join(stops) + '</notations>', 1) if '<notations>' in merged else \
                    merged.replace('</note>', '<notations>' + ''.join(stops) + '</notations></note>', 1)
            body = body[:a.start()] + merged + body[b.end():]
            x = x[:s0] + body + x[s1:]
            break
    return x


if __name__ == '__main__':
    src, out = sys.argv[1], sys.argv[2]
    x0 = open(src, encoding='utf-8').read()
    x = x0
    for pid in ('P28', 'P29', 'P30'):
        x = merge_repeats(x, pid, range(16, 25))
    for pid in ('P28', 'P29', 'P30'):
        for bar in range(16, 25):
            assert sorted(set(sounding(x, pid, [bar]))) == sorted(set(sounding(x0, pid, [bar]))), (pid, bar)
            s0, s1 = measure_span(x, pid, bar)
            total = sum(int(d) for n, d in re.findall(r'(<note[ >](?:(?!</note>).)*?<duration>(\d+)</duration>)', x[s0:s1], re.S) if '<chord/>' not in n)
            assert total == 8, (pid, bar, total)
    p0, p1 = pitches(x0), pitches(x)
    for pid in ('P28', 'P29', 'P30'):
        p0.pop(pid), p1.pop(pid)
    assert p0 == p1, 'another part changed'
    open(out, 'w', encoding='utf-8').write(x)
    print(f'{out}: repeated string notes held, same harmony, every bar full')
