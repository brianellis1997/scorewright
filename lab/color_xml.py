"""Tint a suggestion so it reads like a code review. Compared with the piece's working score
(working.musicxml next to the suggestion), by part, bar, onset, sounding pitch and length: notes the
suggestion adds or changes are green, notes it keeps stay black, and a note it removes from a chord
stays in place in red (a ghost chord note, which render_one.py leaves out of the audio). Without a
working score, every note of bars lo..hi is green (MuseScore, Sibelius and Dorico all honour the
MusicXML note color attribute).
usage: python color_xml.py <in.xml> <out.xml> <lo> <hi> [#hex]"""
import os, re, sys
from fractions import Fraction

GREEN, RED = '#0B8A3E', '#C02626'
STEPS = 'CDEFGAB'
PC = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)
NOTE = re.compile(r'<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>', re.S)


def transposes(xml):
    out = {}
    for pm in re.finditer(r'<part id="([^"]*)">(.*?)</part>', xml, re.S):
        t = re.search(r'<transpose\b.*?</transpose>', pm.group(2), re.S)
        out[pm.group(1)] = int(re.search(r'<chromatic>(-?\d+)</chromatic>', t.group(0)).group(1)) + 12 * int(
            (re.search(r'<octave-change>(-?\d+)</octave-change>', t.group(0)) or [0, 0])[1]) if t else 0
    return out


def divisions_by_bar(part):
    """{bar: divisions to the quarter there}: Dorico writes 4, and more in a part with tuplets"""
    out, cur = {}, 1
    for mm in re.finditer(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', part, re.S):
        d = re.search(r'<divisions>(\d+)</divisions>', mm.group(2))
        cur = int(d.group(1)) if d else cur
        out[int(mm.group(1))] = cur
    return out


def notes(body, div=1):
    """[(onset, sounding key, start, end, chord)] for the pitched notes of a bar, in voice order; onset
    and length in quarters, so parts written with different divisions compare"""
    t, last, out = 0, 0, []
    for m in NOTE.finditer(body):
        s = m.group(0)
        d = re.search(r'<duration>(\d+)</duration>', s)
        d = int(d.group(1)) if d else 0
        if s.startswith('<backup'):
            t -= d
            continue
        if s.startswith('<forward'):
            t += d
            continue
        chord = '<chord/>' in s
        if not chord:
            last = t
            t += d
        p = re.search(r'<step>(\w)</step>(?:\s*<alter>(-?\d+)</alter>)?\s*<octave>(\d+)</octave>', s)
        if p and '<grace' not in s:
            midi = 12 * (int(p.group(3)) + 1) + PC[p.group(1)] + int(p.group(2) or 0)
            on = Fraction(last, div)
            out.append((on, (on, midi, Fraction(d, div)), m.start(), m.end(), chord))
    return out


def ghost(note):
    note = re.sub(r'\s*<(notations|lyric)>.*?</\1>', '', note, flags=re.S)
    note = re.sub(r'\s*<(beam|tie|stem)[^>]*>(?:[^<]*</\1>)?', '', note)
    note = note.replace('<chord/>', '')
    return re.sub(r'^<note[^>]*>', f'<note color="{RED}"><chord/>', note)


def diff(xml, old, lo, hi):
    tr_new, tr_old = transposes(xml), transposes(old)
    measures, old_div = {}, {}
    for pm in re.finditer(r'<part id="([^"]*)">(.*?)</part>', old, re.S):
        old_div[pm.group(1)] = divisions_by_bar(pm.group(2))
        for mm in re.finditer(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', pm.group(2), re.S):
            if lo <= int(mm.group(1)) <= hi:
                measures[(pm.group(1), int(mm.group(1)))] = mm.group(2)
    out, counts = [], [0, 0]
    pos = 0
    for pm in re.finditer(r'<part id="([^"]*)">(.*?)</part>', xml, re.S):
        pid = pm.group(1)
        out.append(xml[pos:pm.start(2)])
        part, ppos, pout = pm.group(2), 0, []
        new_div = divisions_by_bar(part)
        for mm in re.finditer(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', part, re.S):
            bar, body = int(mm.group(1)), mm.group(2)
            pout.append(part[ppos:mm.start(2)])
            ppos = mm.end(2)
            if not lo <= bar <= hi:
                pout.append(body)
                continue
            new = [(on, (k[0], k[1] + tr_new.get(pid, 0), k[2]), s, e, c) for on, k, s, e, c in notes(body, new_div.get(bar, 1))]
            ob = measures.get((pid, bar), '')
            gone = [(on, (k[0], k[1] + tr_old.get(pid, 0), k[2]), ob[s:e]) for on, k, s, e, c in notes(ob, old_div.get(pid, {}).get(bar, 1))]
            pool = [k for _, k, _ in gone]
            edits = []
            for on, k, s, e, c in new:
                if k in pool:
                    pool.remove(k)
                else:
                    edits.append((s, s + len('<note'), f'<note color="{GREEN}"'))
                    counts[0] += 1
            removed = {}
            for on, k, text in gone:
                if k in pool:
                    pool.remove(k)
                    removed.setdefault(on, []).append(text)
            for on, texts in removed.items():
                anchor = [e for o, _, s, e, c in new if o == on]
                if anchor:
                    edits.append((max(anchor), max(anchor), ''.join(ghost(t) for t in texts)))
                    counts[1] += len(texts)
            for s, e, t in sorted(edits, reverse=True):
                body = body[:s] + t + body[e:]
            pout.append(body)
        pout.append(part[ppos:])
        out.append(''.join(pout))
        pos = pm.end(2)
    out.append(xml[pos:])
    return ''.join(out), counts


if __name__ == '__main__':
    src, dst, lo, hi = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    col = sys.argv[5] if len(sys.argv) > 5 else GREEN
    xml = open(src, encoding='utf-8').read()
    working = os.path.join(os.path.dirname(os.path.abspath(src)), 'working.musicxml')
    if os.path.exists(working) and os.path.abspath(working) != os.path.abspath(src):
        out, (added, removed) = diff(xml, open(working, encoding='utf-8').read(), lo, hi)
        open(dst, 'w', encoding='utf-8').write(out)
        print('COLORED', dst, 'as a diff:', added, 'green', removed, 'red')
        sys.exit(0)

    def tint(m):
        num, body = int(m.group(1)), m.group(3)
        if lo <= num <= hi:
            body = re.sub(r'<note(?![^>]*\bcolor=)', f'<note color="{col}"', body)
            body = re.sub(r'<rest(?![^>]*\bcolor=)(/?)>', f'<rest color="{col}"\\1>', body)
        return f'<measure number="{num}"{m.group(2)}>{body}</measure>'
    out, n = re.subn(r'<measure number="(\d+)"([^>]*)>(.*?)</measure>', tint, xml, flags=re.S)
    open(dst, 'w', encoding='utf-8').write(out)
    print('COLORED', dst, 'measures processed', n, 'green notes', out.count(f'color="{col}"'))
