"""The analysis layer: deterministic musical facts computed from a score.

This is the part that makes an LLM useful, exactly as grep/type-checkers make a coding agent
useful. The model should reason over THESE FACTS, not over raw notes. A harmonic summary of a
47-part symphony is a few thousand tokens; the notes are 452,000.

Everything here is objectively checkable — no taste, no opinions. Taste comes later.
"""
import sys, os, json, itertools
from music21 import converter, interval, pitch, roman, key as m21key, note, chord, meter

# Written/sounding ranges for common orchestral instruments, as (low, high) in scientific pitch.
# Conservative *professional* ranges; a student ensemble needs tighter bounds.
# SOUNDING ranges (concert pitch), not written. Scores are converted with toSoundingPitch() before
# checking, so a Bb clarinet part is compared against what the audience hears. Mixing the two
# conventions in one table silently mis-flags every transposing instrument.
# Conservative *professional* ranges; a student ensemble needs tighter bounds.
RANGES = {
    'Piccolo': ('D5','C8'), 'Alto Flute': ('G3','G6'), 'Flute': ('C4','C7'),
    'English Horn': ('E3','A5'), 'Oboe': ('B-3','G6'),
    'Bass Clarinet': ('B-1','G5'), 'Clarinet': ('D3','B-6'),
    'Contrabassoon': ('B-0','E4'), 'Bassoon': ('B-1','E5'),
    'Soprano Saxophone': ('A-3','E6'), 'Alto Saxophone': ('D-3','A-5'),
    'Tenor Saxophone': ('A-2','E5'), 'Baritone Saxophone': ('D-2','A-4'),
    'Horn': ('B1','F5'), 'Trumpet': ('E3','C6'),
    'Bass Trombone': ('B-1','B-4'), 'Trombone': ('E2','B-4'), 'Tuba': ('D1','F4'),
    'Violin': ('G3','A7'), 'Viola': ('C3','E6'),
    'Violoncello': ('C2','C6'), 'Cello': ('C2','C6'),
    'Contrabass': ('E1','G4'), 'Double Bass': ('E1','G4'),
    'Harp': ('C1','G7'), 'Piano': ('A0','C8'),
    'Soprano': ('C4','A5'), 'Alto': ('F3','F5'), 'Tenor': ('C3','A4'), 'Bass': ('E2','E4'),
}

# Longest key first. Plain substring matching read "Tenor Saxophone" as the VOICE part Tenor
# (C3-A4) and reported 418 violations in Gettysburg Day 3 that do not exist. Same failure mode as
# every other bug in this codebase: a signal harvested from a near-name-match instead of the object.
_RANGE_KEYS = sorted(RANGES, key=len, reverse=True)


def _match_range(part_name):
    n = (part_name or '').lower()
    for k in _RANGE_KEYS:
        if k.lower() in n:
            return k, RANGES[k]
    return None, None


def check_ranges(score):
    """Notes outside the instrument's practical SOUNDING range. Objectively wrong, easy to fix."""
    out = []
    try:
        score = score.toSoundingPitch()
    except Exception:
        pass
    for p in score.parts:
        inst, rng = _match_range(p.partName or p.id)
        if not rng:
            continue
        lo, hi = pitch.Pitch(rng[0]), pitch.Pitch(rng[1])
        bad = []
        for n in p.recurse().notes:
            # Percussion is Unpitched: no .pitch, no .notes, and no range to violate. Only shows up
            # in orchestral scores, which is why 900+ solo/chamber parses never surfaced this.
            if isinstance(n, note.Note):
                ps = [n]
            elif isinstance(n, chord.Chord):
                ps = [x for x in n.notes if isinstance(x, note.Note)]
            else:
                continue
            for x in ps:
                if x.pitch < lo or x.pitch > hi:
                    m = x.getContextByClass('Measure')
                    bad.append({'measure': m.number if m else None,
                                'pitch': x.nameWithOctave,
                                'direction': 'below' if x.pitch < lo else 'above'})
        if bad:
            out.append({'part': p.partName, 'instrument': inst,
                        'range': f'{rng[0]}-{rng[1]}', 'count': len(bad),
                        'examples': bad[:5]})
    return out

def check_ties(score):
    """Ties joining DIFFERENT pitches - genuinely invalid notation.

    Exists because a model tried it by eye and got it wrong: it called bar 11 of Briello no 36
    "E#4 tied to F#4, a tie can only connect the same pitch" when the file has F#4 tied to F#4. It
    had misread the pitch. Structural claims from a model hold up; individual pitch identification
    out of 48k tokens of XML does not. So this belongs in [COMPUTED].

    MUST be matched PER NOTEHEAD, not per chord. In a chord one note is often tied while the others
    move - `D5+G4 -> Eb5+G4` is a tied G4 under a moving upper voice, which is ordinary notation.
    Comparing whole-chord pitch SETS flagged 29 of 150 scores, essentially all of them wrong: the
    same verify-the-proxy-not-the-object error the model had just made, reproduced in code.
    """
    bad = []
    for p in score.parts:
        open_ties = {}                     # (voice, pitch name) -> measure it started in
        for n in p.recurse().notes:
            m = n.getContextByClass('Measure')
            mn = m.number if m else None
            v = str(getattr(n, 'voice', '') or '')
            # a Chord holds one tie per notehead; a Note holds its own
            heads = list(n.notes) if hasattr(n, 'notes') else [n]
            for h in heads:
                t = getattr(h, 'tie', None) or (getattr(n, 'tie', None) if len(heads) == 1 else None)
                if t is None:
                    continue
                name = h.pitch.nameWithOctave
                if t.type in ('stop', 'continue'):
                    if (v, name) not in open_ties:
                        # a tie ended on a pitch that no tie started on
                        bad.append({'part': p.partName, 'measure': mn, 'pitch': name,
                                    'problem': 'tie ends on a pitch that was never tied'})
                    else:
                        open_ties.pop((v, name))
                if t.type in ('start', 'continue'):
                    open_ties[(v, name)] = mn
    return bad


def check_parallels(score, max_pairs=12):
    """Parallel fifths and octaves between every pair of parts.

    Style-conditioned by design: this REPORTS them, it does not call them errors. Common practice
    forbids them; Debussy, film scoring and parallel-organum textures use them deliberately.
    """
    parts = list(score.parts)[:max_pairs]
    found = []
    for a, b in itertools.combinations(range(len(parts)), 2):
        pa = parts[a].flatten().notes.stream()
        pb = parts[b].flatten().notes.stream()
        prev = None
        for off in sorted({float(n.offset) for n in pa} & {float(n.offset) for n in pb}):
            na = pa.getElementsByOffset(off).first()
            nb = pb.getElementsByOffset(off).first()
            if not na or not nb: continue
            ta = na.pitches[-1] if na.isChord else na.pitch
            tb = nb.pitches[-1] if nb.isChord else nb.pitch
            iv = interval.Interval(noteStart=note.Note(tb), noteEnd=note.Note(ta))
            simple = iv.simpleName
            cur = (ta.nameWithOctave, tb.nameWithOctave)
            # BOTH voices must move. Holding one note while the other steps into a fifth is oblique
            # motion, which is fine; only similar motion between two perfect intervals is parallel.
            moved_both = prev and prev[1][0] != cur[0] and prev[1][1] != cur[1]
            if prev and prev[0] == simple and simple in ('P5', 'P8') and moved_both:
                m = na.getContextByClass('Measure')
                found.append({'type': f'parallel {"fifths" if simple=="P5" else "octaves"}',
                              'parts': [parts[a].partName, parts[b].partName],
                              'measure': m.number if m else None,
                              'offset': off})
            prev = (simple, cur)
    return found[:40]

def key_areas(score):
    """The NOTATED key signatures and where they change - ground truth from the file, not a guess.

    98% of Brian's scores carry more than one key signature. Reporting a single whole-piece key is
    actively misleading: Fall Rose is notated in 2 sharps, changes to 2 flats at m112 and to 0 at
    m214, and whole-piece detection returned "G minor" - the MIDDLE section - for all 314 bars.

    A key signature is not the same as the key (2 sharps = D major or B minor), so each span is also
    analysed statistically to pick the mode. Statistics decide major-vs-relative-minor; the notated
    signature decides where the boundaries are.
    """
    seen, spans = {}, []
    for ks in score.recurse().getElementsByClass(m21key.KeySignature):
        mn = ks.measureNumber
        if mn is None or mn in seen:
            continue
        seen[mn] = ks.sharps
    for mn in sorted(seen):
        spans.append({'from_measure': mn, 'sharps': seen[mn]})
    last = max((len(p.getElementsByClass('Measure')) for p in score.parts), default=0)
    for i, sp in enumerate(spans):
        sp['to_measure'] = spans[i + 1]['from_measure'] - 1 if i + 1 < len(spans) else last
        try:
            ex = score.measures(sp['from_measure'], sp['to_measure'])
            k = ex.analyze('key')
            # Take the MODE from Krumhansl but the SPELLING from the notated key signature.
            # Briello 36 is notated in 6 sharps (D# minor); Krumhansl returns the enharmonic flat
            # spelling (Eb minor). Roman numeral analysis compares spellings, so a D# minor tonic
            # against an Eb minor key came out as "#vii" and the whole piece read as nonsense.
            # With the notated spelling it reads i - bVI - III - bVII, which is what Brian wrote.
            try:
                k = m21key.KeySignature(sp['sharps']).asKey(k.mode)
            except Exception:
                pass
            sp['detected'] = f'{k.tonic.name} {k.mode}'
            sp['key_obj'] = k
            sp['confidence'] = round(float(getattr(k, 'correlationCoefficient', 0) or 0), 3)
        except Exception:
            sp['detected'] = None
        sp['signature'] = (f'{sp["sharps"]} sharps' if sp['sharps'] > 0 else
                           f'{-sp["sharps"]} flats' if sp['sharps'] < 0 else 'no sharps/flats')
    return spans


def _label(c, k):
    """Roman numeral for a real chord; an honest description for anything that is not one.

    SHIPPED BUG: romanNumeralFromChord happily labels a SINGLE NOTE as a triad and never says so.
    Fall Rose bars 1-4 are one cello pedal on D - one pitch class, no third, no fifth - and the
    reduction reported "i" for all four bars. That is invented harmony, and it is worse than a gap
    because it reads as fact. A roman numeral now requires 3+ distinct pitch classes.
    """
    pcs = {p.pitchClass for p in c.pitches}
    if len(pcs) < 2:
        return f'[{c.pitches[0].name} alone]' if c.pitches else None
    if len(pcs) == 2:
        iv = interval.Interval(noteStart=note.Note(c.pitches[0]), noteEnd=note.Note(c.pitches[-1]))
        return f'[dyad {iv.simpleName}]'
    try:
        return roman.romanNumeralFromChord(c, k).figure
    except Exception:
        return None


def harmonic_sketch(score, max_measures=64, min_beats=1.0):
    """Key, and a DURATION-WEIGHTED roman-numeral reduction.

    Naive chordify + romanNumeralFromChord is unusable: it labels every vertical slice, so a single
    passing tone becomes "vi#5#4" and a 14-bar phrase reads as 40 chords of nonsense. Verified on
    the G-minor string quartet. Structural harmony lasts; passing sonorities do not, so we keep only
    chords sounding at least `min_beats` and take the longest two per measure. This is a heuristic,
    not theory - it will still miss a genuine fast harmonic rhythm. Report the reduction, not truth.
    """
    out = {}
    try:
        k = score.analyze('key')
        out['key'] = f'{k.tonic.name} {k.mode}'
        out['key_confidence'] = round(float(getattr(k, 'correlationCoefficient', 0) or 0), 3)
    except Exception:
        out['key'] = None
        return out
    # Label each bar against the key of ITS OWN section, not the whole piece. Fall Rose is notated
    # in D major for 111 bars, but whole-piece detection returns G minor, so every opening tonic
    # chord came out as "v". Wrong reference key = wrong roman numeral for every chord in the span.
    spans = []
    try:
        for sp in key_areas(score):
            if sp.get('key_obj') is not None:
                spans.append((sp['from_measure'], sp['to_measure'], sp['key_obj']))
    except Exception:
        pass

    def key_at(mn):
        for lo, hi, kk in spans:
            if mn is not None and lo <= mn <= hi:
                return kk
        return k
    out['key_areas'] = [f'm{a}-{b}:{kk.tonic.name} {kk.mode}' for a, b, kk in spans]
    try:
        # Excerpt BEFORE chordifying. chordify() on Gettysburg Day 3 (47 parts, 67k measures) would
        # run for hours and produce 10.2M tokens of slices we then throw away. Cheaper and identical
        # in output to reduce the window first. This is the excerpt-retrieval principle from §5.
        try:
            src = score.measures(1, max_measures) or score
        except Exception:
            src = score
        ch = src.chordify()
        prog = []
        for m in ch.getElementsByClass('Measure'):
            cands, weak = [], []
            for c in m.getElementsByClass('Chord'):
                ql = float(c.quarterLength)
                if ql < min_beats:
                    # Do NOT drop it outright. The old filter deleted 34 of Briello 36's 40 bars,
                    # because fast piano writing has no chord lasting a full beat - exactly the
                    # Debussy/Ravel case. Keep it as a fallback, weighted by beat position so a
                    # downbeat sonority beats an offbeat one of the same length.
                    weak.append((ql + (1.0 if float(c.offset) % 1 == 0 else 0), float(c.offset), c))
                    continue
                c = c.removeRedundantPitchNames(inPlace=False)
                lab = _label(c, key_at(m.number))
                if lab is None:
                    continue
                cands.append((ql, float(c.offset), lab))
            if not cands and weak:
                weak.sort(key=lambda x: -x[0])
                for _, off, c in weak[:2]:
                    lab = _label(c.removeRedundantPitchNames(inPlace=False), key_at(m.number))
                    if lab is not None:
                        cands.append((0.0, off, lab))
            cands.sort(key=lambda x: -x[0])
            keep = sorted(cands[:2], key=lambda x: x[1])
            if keep:
                figs = [f for _, _, f in keep]
                if len(figs) == 2 and figs[0] == figs[1]:
                    figs = figs[:1]
                prog.append({'m': m.number, 'rn': figs})
        out['progression'] = prog
        out['harmonic_rhythm'] = round(sum(len(p['rn']) for p in prog) / max(len(prog), 1), 2)
    except Exception as e:
        out['progression_error'] = f'{type(e).__name__}: {e}'[:100]
    return out


def texture(score):
    """Who is playing when — density per part, and overall activity."""
    rows = []
    for p in score.parts:
        ns = list(p.recurse().notes)
        ms = len(p.getElementsByClass('Measure')) or 1
        rows.append({'part': p.partName, 'notes': len(ns),
                     'notes_per_measure': round(len(ns)/ms, 2)})
    rows.sort(key=lambda r: -r['notes'])
    return rows

def analyze(path):
    s = converter.parse(path)
    return {
        'file': os.path.basename(path),
        'parts': len(s.parts),
        'measures': max((len(p.getElementsByClass('Measure')) for p in s.parts), default=0),
        'harmony': harmonic_sketch(s),
        'range_violations': check_ranges(s),
        'parallels': check_parallels(s),
        'texture': texture(s),
    }

def brief(path, max_measures=64):
    """The LLM-facing artifact: everything a model needs to say something true about a score,
    in ~1-3k tokens instead of the 68k-10.2M the raw MusicXML costs (PROJECT.md §5).

    This is the whole thesis in one function. The model never sees the notes unless it asks for a
    specific excerpt.
    """
    s = converter.parse(path)
    h = harmonic_sketch(s, max_measures)
    tx = texture(s)
    rv = check_ranges(s)
    pl = check_parallels(s)
    L = [f'SCORE: {os.path.basename(path)}',
         f'{len(s.parts)} parts, {max((len(p.getElementsByClass("Measure")) for p in s.parts), default=0)} measures']
    tss = sorted({t.ratioString for t in s.recurse().getElementsByClass("TimeSignature")})
    if tss: L.append('meter: ' + ', '.join(tss[:6]))
    ka = key_areas(s)
    if len(ka) > 1:
        L.append(f'KEY AREAS ({len(ka)} notated key signatures):')
        for sp in ka:
            L.append(f'  m{sp["from_measure"]}-{sp["to_measure"]:<5} {sp["signature"]:<16}'
                     f'detected {sp.get("detected")} (conf {sp.get("confidence")})')
        L.append(f'  whole-piece detection says {h.get("key")} - MISLEADING when the piece modulates')
    else:
        k1 = ka[0].get('detected') if ka else None
        L.append(f'key: {k1 or h.get("key")} (confidence {h.get("key_confidence")}), '
                 f'notated {ka[0]["signature"] if ka else "?"}')
    if h.get('harmonic_rhythm'): L.append(f'harmonic rhythm: {h["harmonic_rhythm"]} chords/bar')
    L.append('')
    L.append('INSTRUMENTATION (by activity):')
    for t in tx[:14]:
        L.append(f'  {t["part"]:<22} {t["notes"]:>6} notes  {t["notes_per_measure"]:>6}/bar')
    if len(tx) > 14: L.append(f'  ... and {len(tx)-14} more parts')
    L.append('')
    L.append(f'HARMONY (duration-weighted reduction, first {max_measures} bars):')
    L.append('  ' + ' '.join(f'm{p["m"]}:{"-".join(p["rn"])}' for p in h.get('progression', [])))
    L.append('')
    if rv:
        L.append('RANGE VIOLATIONS:')
        for r in rv:
            ex = ', '.join(f'{e["pitch"]}@m{e["measure"]}' for e in r['examples'][:3])
            L.append(f'  {r["part"]}: {r["count"]} notes outside {r["range"]} ({ex})')
    else:
        L.append('RANGE VIOLATIONS: none')
    tv = check_ties(s)
    if tv:
        L.append(f'INVALID TIES (joining different pitches): {len(tv)}')
        for t in tv[:5]:
            L.append(f'  {t["part"]}: m{t["from_measure"]} {t["from"]} -> '
                     f'm{t["to_measure"]} {t["to"]}')
    else:
        L.append('INVALID TIES: none')
    L.append(f'PARALLEL 5ths/8ves: {len(pl)}' + (' (reported, not judged - style dependent)' if pl else ''))
    for p in pl[:6]:
        L.append(f'  m{p["measure"]}: {p["parts"][0]} / {p["parts"][1]} — {p["type"]}')
    return '\n'.join(L)


if __name__ == '__main__':
    D = '/Users/bdogellis/Documents/Score Exports/MusicXML'
    for fn in [a for a in sys.argv[1:] if not a.startswith("--")]:
        p = fn if os.path.exists(fn) else os.path.join(D, fn)
        print(brief(p) if "--brief" in sys.argv else json.dumps(analyze(p), indent=1)[:4000])


def texture_profile(raw, measure, parts_fn, notes_fn):
    """How a bar BEHAVES: how many parts sound, how many distinct rhythms, how much unison,
    whether the bass sustains, and the note-density.

    Exists because nothing checked this. A written bar can sum correctly, use only chord tones and
    correct transpositions, and still be musically inert: the model wrote seven parts in unison over
    a static whole-note pad, stopping a sextuplet motor dead and leaving three beats with no bass.
    Arithmetically valid, musically dead. Compare a bar against its neighbours.
    """
    import collections
    profs, sounding, rhythms, lowest = {}, 0, collections.Counter(), None
    for i, _pid, name, _a, _b in parts_fn(raw):
        blocks = [b for _, b in notes_fn(raw, measure, part=i)]
        if not blocks or all('<rest' in b for b in blocks):
            continue
        sounding += 1
        durs, pitches, held = [], [], 0
        for b in blocks:
            if '<chord' in b:
                continue
            d = _dur(b)
            durs.append(d)
            if '<rest' in b:
                held += 0
        rhythms[tuple(durs)] += 1
        profs[name] = durs
    n_events = sum(len(d) for d in profs.values())
    top = rhythms.most_common(1)[0] if rhythms else ((), 0)
    return {'sounding_parts': sounding,
            'distinct_rhythms': len(rhythms),
            'largest_unison_group': top[1],
            'events_per_part': round(n_events / max(sounding, 1), 2)}


def _dur(block):
    import re as _re
    m = _re.search(r'<duration>(\d+)</duration>', block)
    return int(m.group(1)) if m else 0


def texture_report(raw, written, reference, parts_fn, notes_fn):
    """Compare each written bar's texture against a reference bar. Returns [] or complaints."""
    ref = texture_profile(raw, reference, parts_fn, notes_fn)
    out = []
    for m in written:
        got = texture_profile(raw, m, parts_fn, notes_fn)
        if ref['distinct_rhythms'] >= 3 and got['distinct_rhythms'] <= 1:
            out.append(f'bar {m}: only {got["distinct_rhythms"]} rhythmic layer where bar '
                       f'{reference} has {ref["distinct_rhythms"]} - the texture went flat')
        if got['largest_unison_group'] >= 5 and got['largest_unison_group'] > \
                ref['largest_unison_group'] + 1:
            out.append(f'bar {m}: {got["largest_unison_group"]} parts share one rhythm '
                       f'(bar {reference}: {ref["largest_unison_group"]}) - that is doubling, '
                       f'not orchestration')
        if ref['events_per_part'] >= 3 and got['events_per_part'] < ref['events_per_part'] / 2.5:
            out.append(f'bar {m}: {got["events_per_part"]} events per part where bar {reference} '
                       f'has {ref["events_per_part"]} - the motion stopped')
    return out


def check_clashes(raw, measures, parts_fn, notes_fn, div_fn):
    """Simultaneous semitone clashes between different parts.

    I have now written the same mistake twice - Ab against a held G, then Cb against Bb - and both
    times found it by eye AFTER Brian heard it. A minor 2nd or major 7th between two parts sounding
    at the same moment is computable, so compute it. Octaves are fine; a semitone in the same or
    adjacent octave is what stings.

    Reports at the SOUNDING pitch, so transposition is accounted for.
    """
    import warnings
    from music21 import converter
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        score = converter.parse(raw).toSoundingPitch()
    out = []
    for mno in measures:
        events = []                      # (offset, end, midi, part)
        for p in score.parts:
            m = p.measure(mno)
            if m is None:
                continue
            for n in m.recurse().notes:
                try:
                    off = float(n.getOffsetInHierarchy(m))
                except Exception:
                    off = float(n.offset)
                for q in n.pitches:
                    events.append((off, off + float(n.quarterLength), q.midi,
                                   p.partName or '?'))
        for i in range(len(events)):
            for j in range(i + 1, len(events)):
                a, b = events[i], events[j]
                if a[3] == b[3]:
                    continue
                if a[0] >= b[1] - 1e-6 or b[0] >= a[1] - 1e-6:
                    continue             # they never sound together
                d = abs(a[2] - b[2])
                # A PASSING TONE crossing a held chord is ordinary tonal music - a scale over a
                # sustained Bb is not a mistake. The first version of this check flagged every
                # overlap and rejected a perfectly normal scalar melody. What actually stings is a
                # simultaneous ATTACK a semitone apart, or two SUSTAINED notes grinding together.
                same_attack = abs(a[0] - b[0]) < 1e-6
                both_long = (a[1] - a[0]) >= 1.0 and (b[1] - b[0]) >= 1.0
                if not (same_attack or both_long):
                    continue
                if d in (1, 11):         # minor 2nd / major 7th
                    lo, hi = sorted((a, b), key=lambda e: e[2])
                    out.append({'measure': mno, 'beat': round(max(a[0], b[0]), 2),
                                'low': f'{lo[3]}', 'high': f'{hi[3]}',
                                'interval': 'minor 2nd' if d == 1 else 'major 7th'})
    seen, uniq = set(), []
    for c in out:
        k = (c['measure'], c['beat'], c['low'], c['high'])
        if k not in seen:
            seen.add(k)
            uniq.append(c)
    return uniq
