"""Performance marks for a MusicXML file whose notes must not change: dynamics, hairpins,
articulations and slurs, placed by part id, bar number and onset. Everything else, the layout and
Dorico's own encoding of transposing instruments (written pitch plus <transpose>) included, stays
byte for byte, so the file can go back into Dorico.

An onset is in quarter notes from the start of the bar, in voice 1. A hairpin or direction placed
at onset None goes at the end of the bar. Every position is found in the original text, and the
edits are applied together by text().

usage:
    m = Marks(open(path, encoding='utf-8').read())
    m.dynamic('P3', 7, 1, 'mp')
    m.hairpin('P3', (9, 1), (10, 1), 'crescendo')
    m.articulation('P3', 8, 0, 'detached-legato')
    m.slur('P2', (15, 1), (16, 0))
    open(out, 'w', encoding='utf-8').write(m.text())
    pitches(text) lists every pitch per part, to prove that nothing but marks changed."""
import re

NOTE_RE = re.compile(r'<note[ >][\s\S]*?</note>|<backup>[\s\S]*?</backup>|<forward>[\s\S]*?</forward>')


class Marks:
    def __init__(self, xml):
        self.xml = xml
        self.inserts = {}
        self.notes = {}
        self.wedge = {}

    def _part(self, pid):
        m = re.search(rf'<part id="{pid}">', self.xml)
        if not m:
            raise ValueError(f'no part {pid}')
        return m.end(), self.xml.index('</part>', m.end())

    def _measure(self, pid, bar):
        ps, pe = self._part(pid)
        m = re.compile(rf'<measure number="{bar}"[^>]*>').search(self.xml, ps, pe)
        if not m:
            raise ValueError(f'no bar {bar} in {pid}')
        return m.start(), m.end(), self.xml.index('</measure>', m.end())

    def _divisions(self, pid, bar):
        ps, _ = self._part(pid)
        _, _, me = self._measure(pid, bar)
        return int(re.findall(r'<divisions>(\d+)</divisions>', self.xml[ps:me])[-1])

    def events(self, pid, bar):
        """[(onset, start, end, chord, rest, voice)] for every note of the bar"""
        _, mo, me = self._measure(pid, bar)
        div = self._divisions(pid, bar)
        t, last, out = 0, 0, []
        for ev in NOTE_RE.finditer(self.xml, mo, me):
            s = ev.group(0)
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
            v = re.search(r'<voice>(\d+)</voice>', s)
            out.append((last / div, ev.start(), ev.end(), chord, '<rest' in s, v.group(1) if v else '1'))
        return out

    def _note(self, pid, bar, onset, rests=False):
        for on, s, e, chord, rest, v in self.events(pid, bar):
            if abs(on - onset) < 1e-6 and not chord and v == '1' and (rests or not rest):
                return s, e
        raise ValueError(f'no note in {pid} bar {bar} at onset {onset}')

    def _at(self, pid, bar, onset):
        if onset is None:
            return self._measure(pid, bar)[2]
        return self._note(pid, bar, onset, rests=True)[0]

    def direction(self, pid, bar, onset, body, placement='below'):
        at = self._at(pid, bar, onset)
        self.inserts.setdefault(at, []).append(
            f'<direction placement="{placement}"><direction-type>{body}</direction-type><staff>1</staff></direction>')

    def dynamic(self, pid, bar, onset, mark, placement='below'):
        self.direction(pid, bar, onset, f'<dynamics><{mark}/></dynamics>', placement)

    def words(self, pid, bar, onset, text, placement='above', italic=True):
        style = ' font-style="italic"' if italic else ''
        self.direction(pid, bar, onset, f'<words{style}>{text}</words>', placement)

    def hairpin(self, pid, start, stop, kind='crescendo', placement='below'):
        n = self.wedge[pid] = self.wedge.get(pid, 0) % 2 + 1
        self.direction(pid, *start, f'<wedge type="{kind}" number="{n}"/>', placement)
        self.direction(pid, *stop, f'<wedge type="stop" number="{n}"/>', placement)

    def _notation(self, pid, bar, onset, plain='', art=''):
        s, e = self._note(pid, bar, onset)
        rec = self.notes.setdefault(s, [e, [], []])
        if plain:
            rec[1].append(plain)
        if art:
            rec[2].append(art)

    def articulation(self, pid, bar, onset, art):
        self._notation(pid, bar, onset, art=f'<{art}/>')

    def slur(self, pid, start, stop, number=1):
        self._notation(pid, *start, plain=f'<slur type="start" number="{number}"/>')
        self._notation(pid, *stop, plain=f'<slur type="stop" number="{number}"/>')

    def _rebuild(self, note, plain, arts):
        art = ''.join(arts)
        if '<notations>' in note:
            if art and '<articulations>' in note:
                note = note.replace('</articulations>', art + '</articulations>', 1)
            elif art:
                plain = plain + [f'<articulations>{art}</articulations>']
            return note.replace('</notations>', ''.join(plain) + '</notations>', 1)
        block = '<notations>' + ''.join(plain) + (f'<articulations>{art}</articulations>' if art else '') + '</notations>'
        at = note.find('<lyric')
        at = note.rfind('</note>') if at < 0 else at
        return note[:at] + block + note[at:]

    def text(self):
        ops = [(s, 1, e, self._rebuild(self.xml[s:e], plain, arts)) for s, (e, plain, arts) in self.notes.items()]
        ops += [(at, 0, at, ''.join(t)) for at, t in self.inserts.items()]
        x = self.xml
        for s, _, e, t in sorted(ops, key=lambda o: (o[0], o[1]), reverse=True):
            x = x[:s] + t + x[e:]
        return x


def pitches(xml):
    """{part id: [(bar, step, alter, octave, duration, chord)]}, for proving that only marks changed"""
    out = {}
    for pm in re.finditer(r'<part id="([^"]*)">([\s\S]*?)</part>', xml):
        rows = []
        for mm in re.finditer(r'<measure number="(\d+)"[^>]*>([\s\S]*?)</measure>', pm.group(2)):
            for n in re.finditer(r'<note[ >][\s\S]*?</note>', mm.group(2)):
                s = n.group(0)
                p = re.search(r'<step>(\w)</step>(?:\s*<alter>(-?[\d.]+)</alter>)?\s*<octave>(\d+)</octave>', s)
                d = re.search(r'<duration>(\d+)</duration>', s)
                rows.append((int(mm.group(1)), *(p.groups() if p else ('rest', None, None)), d.group(1) if d else None, '<chord/>' in s))
        out[pm.group(1)] = rows
    return out
