"""Compare what Dorico has (a fresh export) with the suggestion it should match: every note, its
spelling, rhythm and ties, bar by bar on every staff, and the marks per part (slurs, ties, hairpins,
dynamics). Playing techniques are left out, because Dorico's MusicXML export does not write them.
sw_on_accept.py runs this after every Accept; it is how the Nov 13 typing errors were found.
usage (whisperer env): python dorico_check.py <suggestion.musicxml> <dorico_export.xml>
from code: problems(want_xml, got_xml) -> list of lines, empty when everything matches"""
import re, sys

from dorico_plan import Score


def durations(score_xml, pid, bar, staff):
    part = re.search(rf'<part id="{pid}">(.*?)</part>', score_xml, re.S).group(1)
    m = re.search(rf'<measure number="{bar}"[^>]*>(.*?)</measure>', part, re.S)
    out = []
    for n in re.findall(r'<note[ >].*?</note>', m.group(1) if m else '', re.S):
        if '<chord/>' not in n and int((re.search(r'<staff>(\d+)', n) or [0, 1])[1]) == staff:
            out.append(int((re.search(r'<duration>(\d+)', n) or [0, 0])[1]))
    return out


def marks(score_xml, pid):
    body = re.search(rf'<part id="{pid}">(.*?)</part>', score_xml, re.S).group(1)
    return dict(slurs=len(re.findall(r'<slur [^>]*type="start"', body)), ties=body.count('<tie type="start"/>'),
                hairpins=len(re.findall(r'<wedge [^>]*type="(?:crescendo|diminuendo)"', body)),
                dynamics=re.findall(r'<dynamics[^>]*>\s*<(\w+)/>', body))


def problems(want_xml, got_xml):
    want, got = Score(want_xml), Score(got_xml)
    out = []
    for pid, staff in want.staves:
        if pid not in got.parts:
            out.append(f'{want.names[pid]} is missing in Dorico')
            continue
        for bar in sorted(want.parts[pid][0]):
            w = [it[:3] for it in want.items(pid, bar, staff)]
            g = [it[:3] for it in got.items(pid, bar, staff)] if bar in got.parts[pid][0] else []
            if w != g or durations(want_xml, pid, bar, staff) != durations(got_xml, pid, bar, staff):
                show = lambda its: ' '.join(('~' if it[2] else '') + ('r' if it[1] == 'Rest' else '+'.join(it[1])) for it in its)
                out.append(f'{want.names[pid]} staff {staff} bar {bar}: wanted {show(w)}, Dorico has {show(g)}')
    for pid in want.parts:
        if pid in got.parts and marks(want_xml, pid) != marks(got_xml, pid):
            out.append(f'{want.names[pid]} marks: wanted {marks(want_xml, pid)}, Dorico has {marks(got_xml, pid)}')
    return out


if __name__ == '__main__':
    lines = problems(open(sys.argv[1], encoding='utf-8').read(), open(sys.argv[2], encoding='utf-8').read())
    print('\n'.join(lines) if lines else 'Dorico matches the suggestion in every note, spelling, rhythm, tie and mark.')
    sys.exit(1 if lines else 0)
