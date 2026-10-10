"""Splice generated bars into Brian's ORIGINAL MusicXML so his engraving survives.

The ABC round trip destroys engraving and drops parts (percussion, harp, piano vanish). So:
bars 1..keep_through come from his file byte-for-byte; bars after that come from the generated
XML, matched to his parts by part-name; parts the generator does not know get whole-bar rests.
A <divisions> is declared at the seam so the generated durations mean what they say.

Rewritten 2026-09-03 after the original was lost to the /tmp purge. Same interface:
    splice(orig_path, gen_path, out_path, keep_through=16) -> (n_parts, n_filled, last_bar)
"""
import re


def parts_of(xml):
    """[(part_id, part_name, part_body)] in score order."""
    names = {m.group(1): re.sub(r'<[^>]+>', '', m.group(2)).strip()
             for m in re.finditer(r'<score-part id="([^"]+)">.*?<part-name>(.*?)</part-name>', xml, re.S)}
    out = []
    for m in re.finditer(r'<part id="([^"]+)">(.*?)</part>', xml, re.S):
        out.append((m.group(1), names.get(m.group(1), m.group(1)), m.group(2)))
    return out


def measures(body):
    """[(number, full measure element text)] in order."""
    return [(m.group(1), m.group(0)) for m in re.finditer(r'<measure\b[^>]*\bnumber="([^"]+)"[^>]*>.*?</measure>', body, re.S)]


def staves_in(body):
    m = re.search(r'<staves>(\d+)</staves>', body)
    return int(m.group(1)) if m else 1


def divisions_in(body):
    m = re.search(r'<divisions>(\d+)</divisions>', body)
    return int(m.group(1)) if m else 480


def rest_bar(num, divs, staves, beats=4, beat_type=4):
    dur = int(divs * beats * 4 / beat_type)
    rests = ''.join(f'<note><rest measure="yes"/><duration>{dur}</duration><voice>{s}</voice><staff>{s}</staff></note>'
                    + (f'<backup><duration>{dur}</duration></backup>' if s < staves else '') for s in range(1, staves + 1))
    return f'<measure number="{num}">{rests}</measure>'


def _strip_number(mtext, num):
    return re.sub(r'(<measure\b[^>]*\bnumber=")[^"]+(")', lambda m: m.group(1) + str(num) + m.group(2), mtext, count=1)


def _ensure_divisions(mtext, divs):
    if '<divisions>' in mtext:
        return mtext
    if '<attributes>' in mtext:
        return mtext.replace('<attributes>', f'<attributes><divisions>{divs}</divisions>', 1)
    return re.sub(r'(<measure\b[^>]*>)', lambda m: m.group(1) + f'<attributes><divisions>{divs}</divisions></attributes>', mtext, count=1)


def _time_sig(body):
    m = re.search(r'<time[^>]*>.*?<beats>(\d+)</beats>.*?<beat-type>(\d+)</beat-type>', body, re.S)
    return (int(m.group(1)), int(m.group(2))) if m else (4, 4)


def splice(orig_path, gen_path, out_path, keep_through=16):
    orig = open(orig_path, encoding='utf-8').read()
    gen = open(gen_path, encoding='utf-8').read()
    gparts = {name: body for _, name, body in parts_of(gen)}
    gen_last = max((len(measures(b)) for b in gparts.values()), default=0)
    filled = 0
    new_bodies = {}
    for pid, name, body in parts_of(orig):
        oms = measures(body)
        kept = [t for n, t in oms[:keep_through]]
        odivs = divisions_in(body)
        beats, bt = _time_sig(body)
        gbody = gparts.get(name)
        if gbody is None:                             # try loose name match (case, spacing)
            key = re.sub(r'\W+', '', name.lower())
            gbody = next((b for n, b in gparts.items() if re.sub(r'\W+', '', n.lower()) == key), None)
        if gbody is not None:
            gms = measures(gbody)[keep_through:]
            gdivs = divisions_in(gbody)
            appended = []
            for i, (n, t) in enumerate(gms):
                t = _strip_number(t, keep_through + 1 + i)
                if i == 0:
                    t = _ensure_divisions(t, gdivs)
                appended.append(t)
        else:
            filled += 1
            staves = staves_in(body)
            appended = [rest_bar(keep_through + 1 + i, odivs, staves, beats, bt) for i in range(max(0, gen_last - keep_through))]
        new_bodies[pid] = '\n'.join(kept + appended)

    def repl(m):
        pid = m.group(1)
        return f'<part id="{pid}">\n' + new_bodies.get(pid, m.group(2)) + '\n</part>'
    out = re.sub(r'<part id="([^"]+)">(.*?)</part>', repl, orig, flags=re.S)
    open(out_path, 'w', encoding='utf-8').write(out)
    last = keep_through + max(0, gen_last - keep_through)
    return len(new_bodies), filled, last
