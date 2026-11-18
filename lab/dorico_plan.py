"""Map a suggestion for Brian's open Dorico project to remote-control steps when it is made, so that
his Accept runs them at once (app/dorico_apply.py). The playbook behind it: app/DORICO.md.

Targets are named musically: part, staff, bar, onset and pitch. At run time the runner finds the
target's internal IDs in Dorico's autosave (lab/dorico_file.py) and selects it with one command,
EventEdit.Select. That works in any score and any layout. A note that the plan itself writes has no
ID yet (Dorico refuses a forced autosave), so a target like that is reached from a note that has
one: the plan names that note (via) and the arrow moves from it, counted in the score as it is at
that step. After note entry the last typed note stays selected, so the next step can also start
there (rel).

Counting follows Dorico: a tie chain is one item, a chord is one item with one stop per note for
the up and down arrows, and a rest is one item. Note values use the names in Dorico's key-command
file (kSemiQuaver, not kSemiquaver: an unknown name types whole notes). A new note value clears
the dot, and SetDotted toggles it, so every note sends its value, then the dot only if it has one.

usage:
    p = Plan(export_xml)                       # the score Dorico has now (a fresh export)
    p.tie('P10', 14, 0)                        # existing note: selected by its ID
    p.explode('P5', 24, 31, staves=3)          # copy, then paste-explode onto the staves below
    p.use(xml_after_that)                      # the score as the next steps find it
    p.respell('P6', 25, 0)                     # a pasted note: reached via a note with an ID
    p.notes('P3', 18, 0, [('G4', 1), ('A4', 1, 'tie')])   # note entry; durations in quarters
    p.dynamic('P3', 24, 0, 'pp'); p.slur('P3', (21, 0), (24, 0))
    p.save('S6.dorico.json')"""
import json, re
from fractions import Fraction

STEPS = 'CDEFGAB'
PC = dict(C=0, D=2, E=4, F=5, G=7, A=9, B=11)
PITCH = r'<step>(\w)</step>(?:\s*<alter>(-?\d+)</alter>)?\s*<octave>(\d+)</octave>'
KEEPS = ('NoteInput.SetArticulation', 'Edit.SplitBeam', 'NoteEdit.RespellUsingNoteNameAbove', 'NoteEdit.RespellUsingNoteNameBelow')
VALUE = {Fraction(1, 8): ('kDemiSemiQuaver', 0), Fraction(1, 4): ('kSemiQuaver', 0), Fraction(3, 8): ('kSemiQuaver', 1), Fraction(1, 2): ('kQuaver', 0), Fraction(3, 4): ('kQuaver', 1), Fraction(1): ('kCrotchet', 0),
         Fraction(3, 2): ('kCrotchet', 1), Fraction(2): ('kMinim', 0), Fraction(3): ('kMinim', 1), Fraction(4): ('kSemibreve', 0)}


def count(specs):
    return sum(int(c.partition('*')[2] or 1) for c in specs)


def shift(p, d, c):
    step, alter, octave = p
    di = octave * 7 + STEPS.index(step) + d
    mi = 12 * (octave + 1) + PC[step] + alter + c
    s, o = STEPS[di % 7], di // 7
    return s, mi - (12 * (o + 1) + PC[s]), o


def squeeze(moves):
    out = []
    for m in moves:
        name, _, n = m.partition('*')
        n = int(n or 1)
        if n <= 0:
            continue
        if out and out[-1][0] == name:
            out[-1][1] += n
        else:
            out.append([name, n])
    return [f'{a}*{n}' for a, n in out]


def name(p):
    step, alter, octave = p
    return step + ('#' * alter if alter > 0 else 'b' * -alter) + str(octave)


def midi(n):
    m = re.match(r'([A-G])(#*|b*)(-?\d+)$', n)
    return 12 * (int(m.group(3)) + 1) + PC[m.group(1)] + len(m.group(2)) * (1 if '#' in m.group(2) else -1)


class Score:
    """one state of the score: per part its measures, transposition and staves, and the divisions to
    the quarter in each bar (a part with tuplets may change them between bars)"""

    def __init__(self, xml):
        self.names = dict(re.findall(r'<score-part id="([^"]+)">\s*<part-name>([^<]*)</part-name>', xml))
        self.parts, self.staves, self.slurs, self.wedges, self.dyns = {}, [], {}, {}, {}
        for pid in re.findall(r'<score-part id="([^"]+)"', xml):
            body = re.search(rf'<part id="{pid}">(.*?)</part>', xml, re.S).group(1)
            t = re.search(r'<transpose\b.*?</transpose>', body, re.S)
            tx = t.group(0) if t else ''
            g = lambda tag: int(m.group(1)) if (m := re.search(rf'<{tag}>(-?\d+)</{tag}>', tx)) else 0
            tr = (g('diatonic') + 7 * g('octave-change'), g('chromatic') + 12 * g('octave-change'))
            n = int((re.search(r'<staves>(\d+)</staves>', body) or [0, 1])[1])
            bars = {int(m.group(1)): m.group(2) for m in re.finditer(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', body, re.S)}
            divs, cur = {}, 1
            for b in sorted(bars):
                d = re.findall(r'<divisions>(\d+)</divisions>', bars[b])
                cur = int(d[-1]) if d else cur
                divs[b] = cur
            self.parts[pid] = (bars, tr, divs)
            self.staves += [(pid, s) for s in range(1, n + 1)]
            self.read_slurs(pid)

    def read_slurs(self, pid):
        """self.slurs[(pid, staff)]: [((bar, onset), last bar)] for each slur in the file (the bar before,
        when it ends on a note that starts a bar: Dorico's status bar counts a slur up to where its last
        note starts, S26 Nov 17: a slur to a downbeat of bar 72 read "Bars 70-71"), and
        self.wedges[(pid, staff)]: [((bar, onset), (bar, onset))] from start to stop of each hairpin"""
        bars, tr, divs = self.parts[pid]
        open_, wedge = {}, {}
        for b in sorted(bars):
            t = on = 0
            div = divs[b]
            for ev in re.finditer(r'<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>|<direction[ >].*?</direction>', bars[b], re.S):
                s = ev.group(0)
                if s.startswith('<direction'):
                    staff = int((re.search(r'<staff>(\d+)</staff>', s) or [0, 1])[1])
                    if '<dynamics>' in s:
                        self.dyns.setdefault((pid, staff), set()).add((b, Fraction(t, div)))
                    for kind, num in re.findall(r'<wedge type="(\w+)"(?: number="(\d+)")?', s):
                        key = (num or '1', staff)
                        if kind == 'stop' and key in wedge:
                            self.wedges.setdefault((pid, staff), []).append((wedge.pop(key), (b, Fraction(t, div))))
                        elif kind != 'stop':
                            wedge[key] = (b, Fraction(t, div))
                    continue
                d = int((re.search(r'<duration>(\d+)</duration>', s) or [0, 0])[1])
                if s.startswith('<backup'):
                    t -= d
                    continue
                if s.startswith('<forward'):
                    t += d
                    continue
                staff = int((re.search(r'<staff>(\d+)</staff>', s) or [0, 1])[1])
                if '<chord/>' not in s:
                    on, t = Fraction(t, div), t + d
                for tag in re.findall(r'<slur\b[^>]*>', s):
                    kind = re.search(r'type="(\w+)"', tag).group(1)
                    key = ((re.search(r'number="(\d+)"', tag) or [0, '1'])[1], staff)
                    if kind == 'start':
                        open_[key] = (b, on)
                    elif kind == 'stop' and key in open_:
                        a = open_.pop(key)
                        tied_on = '<tie type="start"/>' in s
                        last = b - 1 if on == 0 and '<tie type="stop"/>' not in s and not tied_on and b > a[0] else b
                        self.slurs.setdefault((pid, staff), []).append((a, last))

    def items(self, pid, bar, staff=1):
        """[(onset, 'Rest' or [concert names, top first], tied from before, tied on, in a tuplet)], voice by voice
        in file order"""
        bars, tr, divs = self.parts[pid]
        t, out, div = 0, [], divs[bar]
        for ev in re.finditer(r'<note[ >].*?</note>|<backup>.*?</backup>|<forward>.*?</forward>', bars[bar], re.S):
            s = ev.group(0)
            d = int((re.search(r'<duration>(\d+)</duration>', s) or [0, 0])[1])
            if s.startswith('<backup'):
                t -= d
                continue
            if s.startswith('<forward'):
                t += d
                continue
            mine = int((re.search(r'<staff>(\d+)</staff>', s) or [0, 1])[1]) == staff and '<grace' not in s
            if '<chord/>' in s:
                if mine and out and out[-1][1] != 'Rest':
                    p = re.search(PITCH, s)
                    out[-1][1].append(shift((p.group(1), int(p.group(2) or 0), int(p.group(3))), *tr))
                continue
            if mine and '<rest' in s:
                out.append([Fraction(t, div), 'Rest', False, False, False])
            elif mine:
                p = re.search(PITCH, s)
                out.append([Fraction(t, div), [shift((p.group(1), int(p.group(2) or 0), int(p.group(3))), *tr)],
                            '<tie type="stop"/>' in s, '<tie type="start"/>' in s, '<time-modification>' in s])
            t += d
        for it in out:
            if it[1] != 'Rest':
                it[1] = [name(p) for p in sorted(it[1], key=lambda p: -(12 * (p[2] + 1) + PC[p[0]] + p[1]))]
        return out

    def nav(self, pid, bar, staff=1):
        """the items the arrows stop at: a tie continuation belongs to the chain that started earlier"""
        return [it for it in self.items(pid, bar, staff) if not it[2]]

    def stops(self, pid, bar, staff=1):
        """the items the RIGHT arrow stops at: those of nav, plus a note tied into a tuplet from a note
        outside it, which Dorico keeps as a second event. The left arrow skips it. (S24, Nov 17: a range
        from a quarter tied into a sextuplet ended one note short; going left over such a tie, the
        spelling steps counted right)"""
        out, prev = [], None
        for it in self.items(pid, bar, staff):
            if not it[2] or (it[4] and prev is not None and not prev[4]):
                out.append(it)
            prev = it
        return out

    def forward(self, pid, staff, a, z):
        """right-arrow moves from (bar, onset) a to the later (bar, onset) z"""
        return sum(1 for b in range(a[0], z[0] + 1) for it in self.stops(pid, b, staff) if a < (b, it[0]) <= z)

    def index(self, pid, bar, onset=None, staff=1):
        its = self.nav(pid, bar, staff)
        if onset is None:
            return len(its) - 1
        return next(i for i, it in enumerate(its) if it[0] == Fraction(onset).limit_denominator(64))

    def chain_end(self, pid, bar, onset, staff=1):
        """the bar where the item at (bar, onset) ends, following its ties over bar lines"""
        it = next(x for x in self.items(pid, bar, staff) if x[0] == Fraction(onset).limit_denominator(64) and not x[2])
        b = bar
        while it[3] and b + 1 in self.parts[pid][0]:
            nxt = self.items(pid, b + 1, staff)
            if not nxt or not nxt[0][2]:
                break
            b, it = b + 1, nxt[0]
        return b

    def item_end(self, pid, bar, onset, staff=1):
        """(bar, onset) where the item at (bar, onset) stops sounding, after its whole tie chain"""
        on = Fraction(onset).limit_denominator(64)
        its = self.items(pid, bar, staff)
        k = next(i for i, x in enumerate(its) if x[0] == on)
        b = bar
        while its[k][3] and b + 1 in self.parts[pid][0]:
            nxt = self.items(pid, b + 1, staff)
            if not nxt or not nxt[0][2]:
                break
            b, its, k = b + 1, nxt, 0
        later = [x[0] for x in its[k + 1:] if x[0] > its[k][0]]
        return (b, later[0]) if later else (b + 1, Fraction(0))

    def chain_start(self, pid, bar, onset, staff=1):
        """(bar, onset) where the tie chain through (bar, onset) starts: a range that ends on a held note
        is selected up to the note that starts it, and covers the rest of the chain"""
        on = Fraction(onset).limit_denominator(64)
        it = next(x for x in self.items(pid, bar, staff) if x[0] == on)
        while it[2] and bar - 1 in self.parts[pid][0]:
            bar -= 1
            it = self.items(pid, bar, staff)[-1]
        return bar, it[0]

    def height(self, i, bar):
        pid, staff = self.staves[i]
        first = self.items(pid, bar, staff)[0]
        if first[2]:
            raise ValueError(f'{pid} bar {bar} starts with a tied note; no walk passes it')
        return 1 if first[1] == 'Rest' else len(first[1])


class Plan:
    def __init__(self, xml, grid=Fraction(1, 2)):
        self.base = self.cur = Score(xml)
        self.grid = grid
        self.steps, self.cursor, self.tied = [], None, set()
        self.slurs = {k: list(v) for k, v in self.base.slurs.items()}
        self.wedges = {k: list(v) for k, v in self.base.wedges.items()}
        self.dyns = {k: set(v) for k, v in self.base.dyns.items()}
        self.hairpins = {}

    def use(self, xml):
        self.cur = Score(xml)
        self.cursor, self.tied = None, set()

    def who(self, pid):
        return self.cur.names.get(pid, pid)

    def unchanged(self, pid, bar):
        return self.base.parts[pid][0].get(bar) == self.cur.parts[pid][0].get(bar)

    def spec(self, pid, bar, onset, staff=1):
        its = self.cur.nav(pid, bar, staff)
        k = self.cur.index(pid, bar, onset, staff)
        target = its[k][1]
        if any(t[:3] == (pid, staff, bar) and t[3] < its[k][0] for t in self.tied):
            raise ValueError(f'{self.who(pid)} bar {bar}: an earlier tie in this bar merges two items; put ties last, or call use()')
        expect = ['Rest'] if target == 'Rest' else [f'Note: {n} ' for n in target] + ([f'Chord: {", ".join(reversed(target))} '] if len(target) > 1 else [])
        return dict(pid=pid, part=self.who(pid), staff=staff, bar=bar, onset=str(its[k][0]), item=k,
                    names=None if target == 'Rest' else target, expect=[bar, expect])

    def landing(self, pid, staff, bar, k):
        """where NavigateRightBar goes from item k of a bar: Dorico jumps to the first item of the first
        bar after the item ends, so from a note tied over the bar line it skips the bars it covers"""
        its = self.cur.nav(pid, bar, staff)
        b = self.cur.chain_end(pid, bar, its[k][0], staff) + 1
        while b in self.cur.parts[pid][0]:
            if self.cur.nav(pid, b, staff):
                return (b, 0)
            b += 1
        return None

    def between(self, pid, staff, a, z):
        (b1, k1), (b2, k2) = a, z
        return self.cur.forward(pid, staff, (b1, self.cur.nav(pid, b1, staff)[k1][0]), (b2, self.cur.nav(pid, b2, staff)[k2][0]))

    def walk(self, pid, staff, a, z):
        """arrow moves along one staff from item a = (bar, k) to the later item z"""
        moves, pos = [], a
        while pos != z:
            land = self.landing(pid, staff, *pos)
            if land and land <= z:
                moves.append('EventEdit.NavigateRightBar')
                pos = land
            else:
                moves.append(f'EventEdit.NavigateRight*{self.between(pid, staff, pos, z)}')
                pos = z
        return squeeze(moves)

    @staticmethod
    def short(s):
        return {k: s[k] for k in ('part', 'staff', 'bar', 'onset', 'names')}

    def via(self, s):
        """a note with an ID (unchanged since the export) and the arrow moves from it to s"""
        pid, staff, bar, k = s['pid'], s['staff'], s['bar'], s['item']
        z = self.cur.staves.index((pid, staff))
        for b in range(bar, max(bar - 24, 0), -1):
            if not self.unchanged(pid, b):
                continue
            its = self.cur.nav(pid, b, staff)
            for j in range(len(its) - 1 if b < bar else k - 1, -1, -1):
                if its[j][1] != 'Rest':
                    return dict(target=self.short(self.spec(pid, b, its[j][0], staff)), moves=self.walk(pid, staff, (b, j), (bar, k)))
        for b in range(bar, max(bar - 8, 0), -1):
            for i in range(z - 1, -1, -1):
                vp, vs = self.cur.staves[i]
                if not self.unchanged(vp, b):
                    continue
                first = self.cur.items(vp, b, vs)[0]
                if first[1] == 'Rest' or first[2] or first[0] != 0 or self.cur.items(pid, b, staff)[0][2]:
                    continue
                try:
                    down = sum(self.cur.height(j, b) for j in range(i, z))
                except ValueError:
                    break
                moves = [f'EventEdit.NavigateDown*{down}'] + self.walk(pid, staff, (b, 0), (bar, k))
                return dict(target=self.short(self.spec(vp, b, 0, vs)), moves=squeeze(moves))
        for b in range(bar, max(bar - 8, 0), -1):
            for i in range(z + 1, len(self.cur.staves)):
                vp, vs = self.cur.staves[i]
                if not self.unchanged(vp, b):
                    continue
                first = self.cur.items(vp, b, vs)[0]
                if first[1] == 'Rest' or first[2] or first[0] != 0 or self.cur.items(pid, b, staff)[0][2]:
                    continue
                try:
                    up = 1 + sum(self.cur.height(j, b) for j in range(z + 1, i))
                except ValueError:
                    break
                moves = [f'EventEdit.NavigateUp*{up}'] + self.walk(pid, staff, (b, 0), (bar, k))
                return dict(target=self.short(self.spec(vp, b, 0, vs)), moves=squeeze(moves))
        raise ValueError(f'{self.who(pid)} bar {bar}: no note with an ID near it')

    def rel(self, s):
        """the arrow moves from the selection the step before left, when it is known"""
        if not self.cursor or self.cursor[:2] != (s['pid'], s['staff']):
            return None
        _, staff, b1, k1 = self.cursor
        b, k = s['bar'], s['item']
        if (b, k) == (b1, k1):
            return []
        if (b, k) > (b1, k1):
            return self.walk(s['pid'], staff, (b1, k1), (b, k))
        n = k1 - k if b == b1 else k1 + sum(len(self.cur.nav(s['pid'], x, staff)) for x in range(b + 1, b1)) + len(self.cur.nav(s['pid'], b, staff)) - k
        return [f'EventEdit.NavigateLeft*{n}']

    def span(self, pid, b0, k0, b1, o1=None, staff=1):
        k1 = self.cur.index(pid, b1, o1, staff)
        if any(t[:2] == (pid, staff) and b0 <= t[2] <= b1 for t in self.tied):
            raise ValueError(f'{self.who(pid)} bars {b0}-{b1}: a tie in the range merges two items; put ties last, or call use()')
        return self.cur.forward(pid, staff, (b0, self.cur.nav(pid, b0, staff)[k0][0]), (b1, self.cur.nav(pid, b1, staff)[k1][0]))

    def step(self, label, pid, bar, onset, staff=1, to=None, down=0, edits=(), plain=()):
        s = self.spec(pid, bar, onset, staff)
        st = dict(label=label, target=self.short(s), expect=s['expect'], extend=[])
        r = self.rel(s)
        if s['names'] is None or not self.unchanged(pid, bar):
            st['target'] = None
            try:
                st['via'] = self.via(s)
            except ValueError:
                if r is None:
                    raise
                st['via'] = None
            if r is not None and st['via'] and 1 + count(st['via']['moves']) < count(r):
                r = None
        elif r:
            r = None
        if r is not None:
            st['rel'] = r
        if to and to[1] is not None:
            to = self.cur.chain_start(pid, to[0], to[1], staff)
        if to:
            n = self.span(pid, bar, s['item'], to[0], to[1], staff)
            if n:
                st['extend'].append(f'EventEdit.NavigateRightExtend*{n}')
                k1 = self.cur.index(pid, to[0], to[1], staff)
                st['end'] = self.cur.chain_end(pid, to[0], self.cur.nav(pid, to[0], staff)[k1][0], staff)
                first = (bar, Fraction(s['onset']))
                ends = self.dyns.get((pid, staff), set())
                over = [(a, e) for a, e in self.hairpins.get((pid, staff), []) + self.wedges.get((pid, staff), [])
                        if a < first < e or (first == e and e in ends)]
                st['range'] = [min([bar] + [a[0] for a, e in over]),
                               max([st['end']] + [e for a, e in self.slurs.get((pid, staff), []) if a == first]
                                   + [(e[0] if e[1] else e[0] - 1) for a, e in over])]
        if down:
            st['extend'].append(f'EventEdit.NavigateDownExtend*{down}')
        st['plain'], st['edits'] = list(plain), list(edits)
        keeps = not st['extend'] and all(e.split('?')[0] in KEEPS for e in st['edits'])
        if not keeps and st['target'] is None and not down and st['edits'] and 'Edit.Delete' not in st['edits'] and 'Edit.PasteExplode' not in st['edits']:
            st['restore'] = True
        self.steps.append(st)
        self.cursor = (pid, staff, bar, s['item']) if keeps or st.get('restore') else None
        return st

    def notes(self, pid, bar, onset, events, staff=1, start=None):
        """note entry from the caret: events = [(names or None for a rest, quarters[, 'tie'])];
        ('tuplet', '6:4') and ('end tuplet', '6:4') go around tuplet notes, which are given at their
        written value (a sextuplet sixteenth is 1/4) and never as rests; the tuplet takes the note value
        set when it starts, so the first tuplet note's value is sent before StartTupletRun;
        the caret starts at a note with an ID (same staff, or the nearest staff above it) and moves.
        start = (pid, staff, bar, onset) names that note when the search cannot know its ID is still
        good (the other staff of a harp after one staff was retyped)"""
        z = self.cur.staves.index((pid, staff))
        order = sorted(range(len(self.cur.staves)), key=lambda i: (abs(i - z), i > z))
        if start:
            start = start[:3] + (Fraction(start[3]), self.cur.staves.index(start[:2]))
        for b in [] if start else list(range(bar, max(bar - 12, 0), -1)) + list(range(bar + 1, bar + 13)):
            for i in order:
                vp, vs = self.cur.staves[i]
                if b not in self.cur.parts[vp][0] or not self.unchanged(vp, b):
                    continue
                its = [it for it in self.cur.nav(vp, b, vs) if it[1] != 'Rest']
                its = [it for it in its if it[0] <= Fraction(onset)] if (i, b) == (z, bar) else [it for it in its if it[0] == 0]
                if its:
                    start = (vp, vs, b, its[-1][0], i)
                    break
            if start:
                break
        if not start:
            raise ValueError(f'{self.who(pid)} bar {bar}: no note with an ID to start the caret from')
        vp, vs, vb, von, vi = start
        moves = [f'NoteInput.MoveDown*{z - vi}'] if vi < z else [f'NoteInput.MoveUp*{vi - z}'] if vi > z else []
        if bar > vb:
            moves.append(f'NoteInput.MoveRightBar*{bar - vb}')
            pos = Fraction(onset)
        elif bar < vb:
            moves.append(f'NoteInput.MoveLeftBar*{vb - bar}')
            pos = Fraction(onset)
        else:
            pos = Fraction(onset) - von
        if pos % self.grid:
            raise ValueError(f'{self.who(pid)} bar {bar}: onset {onset} is off the caret grid')
        if pos:
            moves.append(f'NoteInput.MoveRight*{int(pos / self.grid)}')
        self.check_rests(pid, bar, onset, events, staff)
        self.drop_hairpins(pid, bar, onset, events, staff)
        edits = []
        for i, ev in enumerate(events):
            if ev[0] == 'tuplet':
                nxt = next(e for e in events[i + 1:] if e[0] not in ('tuplet', 'end tuplet'))
                edits.append(f'NoteInput.NoteValue?LogDuration={VALUE[Fraction(nxt[1]).limit_denominator(64)][0]}&Set=true')
            if ev[0] in ('tuplet', 'end tuplet'):
                edits.append(f'NoteInput.StartTupletRun?Definition={ev[1]}&Set={"true" if ev[0] == "tuplet" else "false"}')
                continue
            names, q, tie = (list(ev) + [None])[:3]
            q = Fraction(q).limit_denominator(64)
            if names is None:
                if q % self.grid:
                    raise ValueError(f'a rest of {q} quarters is off the caret grid')
                edits.append(f'NoteInput.MoveRight*{int(q / self.grid)}')
                continue
            v, d = VALUE[q]
            edits.append(f'NoteInput.NoteValue?LogDuration={v}&Set=true')
            if d:
                edits.append('NoteInput.SetDotted?Value=1&Set=true')
            names = [names] if isinstance(names, str) else names
            edits.append('NoteInput.MIDINoteInput?MIDIPitches=' + '\\,'.join(str(midi(n)) for n in names))
            if tie:
                edits.append('NoteInput.Tie')
        edits.append('NoteInput.Exit')
        sp = self.spec(vp, vb, von, vs)
        st = dict(label=f'{self.who(pid)}: notes from bar {bar}', caret=dict(start=self.short(sp), expect=sp['expect'], moves=moves), edits=edits)
        self.steps.append(st)
        self.cursor = None
        return st

    @staticmethod
    def timed(events):
        """[(names, sounding quarters, event)]: tuplet notes at their real length (a sextuplet sixteenth
        is 1/6)"""
        out, ratio = [], Fraction(1)
        for ev in events:
            if ev[0] == 'tuplet':
                actual, normal = ev[1].split(':')
                ratio = Fraction(int(normal), int(actual))
            elif ev[0] == 'end tuplet':
                ratio = Fraction(1)
            else:
                out.append((ev[0], Fraction(ev[1]).limit_denominator(64) * ratio, ev))
        return out

    def drop_hairpins(self, pid, bar, onset, events, staff=1):
        """Dorico takes a hairpin away (or cuts it) when the note it starts or ends on is typed over (S31,
        Nov 17: S30's Violin I crescendo ended on the note S31's run replaced, and a range from bar 85
        then read "Bars 85-86", not 82-86); so do the plan's records"""
        per_bar = Fraction(2)
        t0 = (bar - 1) * per_bar + Fraction(onset)
        t1 = t0 + sum(q for _, q, _ in self.timed(events))
        pos = lambda p: (p[0] - 1) * per_bar + Fraction(p[1])
        for store in (self.hairpins, self.wedges):
            kept = [(a, e) for a, e in store.get((pid, staff), []) if not (t0 <= pos(a) < t1 or t0 < pos(e) <= t1)]
            if (pid, staff) in store:
                store[(pid, staff)] = kept

    def check_rests(self, pid, bar, onset, events, staff=1):
        """a rest in note entry only moves the caret, so an old note under it stays, and the caret can
        stop on it and shift every note after (S30, Nov 17: his viola double stops on the downbeats
        of bars 79-85 stayed under the new eighth rests and the sixteenths came in a sixteenth off):
        the region must be cleared first"""
        per_bar = Fraction(2)
        t = (bar - 1) * per_bar + Fraction(onset)
        spans = []
        for names, q, _ in self.timed(events):
            if names is None:
                spans.append((t, t + q))
            t += q
        for a, z in spans:
            for b in range(int(a // per_bar) + 1, int((z - Fraction(1, 64)) // per_bar) + 2):
                if b not in self.cur.parts[pid][0]:
                    continue
                for it in self.cur.items(pid, b, staff):
                    pos = (b - 1) * per_bar + it[0]
                    if it[1] != 'Rest' and a <= pos < z:
                        raise ValueError(f'{self.who(pid)} bar {b}: a note at {it[0]} lies under a rest of the new line; delete the region first')

    def after_notes(self, xml, pid, bar, onset, staff=1):
        """the score with the notes typed, and where the last typed note is (it stays selected)"""
        self.use(xml)
        self.cursor = (pid, staff, bar, self.cur.index(pid, bar, onset, staff))

    def dynamic(self, pid, bar, onset, mark, staff=1):
        self.dyns.setdefault((pid, staff), set()).add((bar, Fraction(onset).limit_denominator(64)))
        return self.step(f'{mark} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=[f'NoteInput.CreateDynamic?Definition={mark}&UseLocalOverride=0'])

    def articulation(self, pid, bar, onset, value='kStaccatoTenuto', staff=1):
        return self.step(f'{value[1:]} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=[f'NoteInput.SetArticulation?Value={value}'])

    def technique(self, pid, bar, onset, text='pizz.', staff=1):
        """Dorico takes the popover text here (pizz., arco, con sord.), not an ID like pt.pizzicato"""
        return self.step(f'{text} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=[f'NoteInput.CreatePlayingTechnique?Definition={text}'])

    def slur(self, pid, start, end, staves=1, staff=1):
        """Dorico's status bar counts a slur that starts on the first selected note as part of a range
        (S12: a 42-43 range read "Bars 42-44"), so each slur is remembered for the ranges after it"""
        st = self.step(f'slur for {self.who(pid)} bars {start[0]}-{end[0]}', pid, *start, staff, to=end, down=staves - 1, edits=['NoteInput.SlurStart'])
        last = st.get('end', end[0])
        b, on = self.cur.chain_start(pid, end[0], end[1], staff) if end[1] is not None else (end[0], None)
        tied_on = on is not None and any(it[0] == on and it[3] for it in self.cur.items(pid, b, staff))
        if on == 0 and last == b and b > start[0] and not tied_on:
            last = b - 1
        self.slurs.setdefault((pid, staff), []).append(((start[0], Fraction(start[1]).limit_denominator(64)), last))
        return st

    def hairpin(self, pid, start, end, up=True, staves=1, staff=1):
        kind = 'Up' if up else 'Down'
        st = self.step(f'{"cresc" if up else "dim"} for {self.who(pid)} bars {start[0]}-{end[0]}', pid, *start, staff, to=end, down=staves - 1,
                       edits=[f'NoteInput.HairpinStart?Type=kGradualDynamic{kind}&GradualDynamicType=kCrescOrDim'])
        if st.pop('restore', None):
            self.cursor = None
        last = self.cur.chain_start(pid, end[0], end[1], staff) if end[1] is not None else end
        self.hairpins.setdefault((pid, staff), []).append(((start[0], Fraction(start[1]).limit_denominator(64)), self.cur.item_end(pid, *last, staff)))
        return st

    def text(self, pid, bar, onset, words, staff=1):
        """staff text such as 'div.' (Dorico 4 has no such playing technique): NoteInput.CreateText opens
        Dorico's text box at the note, the runner types the words only if a text field has the focus,
        then NoteInput.TextCreateFinished. The selection is unknown afterwards, so the next step starts
        from an ID; put text steps last"""
        st = self.step(f'text "{words}" for {self.who(pid)} in bar {bar}', pid, bar, onset, staff,
                       edits=['NoteInput.CreateText?ParagraphStyleID=paragraph.defaulttext'])
        st.pop('restore', None)
        st['type_text'] = words
        self.cursor = None
        return st

    def articulate(self, pid, start, end, value='kAccent', staff=1):
        """one articulation on every note of a range (rests in it are left alone); like a hairpin, no
        return to a typed note after it, so the next step starts from a note with an ID"""
        st = self.step(f'{value[1:]} on {self.who(pid)} bars {start[0]}-{end[0]}', pid, *start, staff, to=end,
                       edits=[f'NoteInput.SetArticulation?Value={value}'])
        if st.pop('restore', None):
            self.cursor = None
        return st

    def tie(self, pid, bar, onset, staff=1):
        s = self.step(f'tie for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=['NoteInput.Tie'])
        self.tied.add((pid, staff, bar, Fraction(onset)))
        self.cursor = None
        return s

    def spell(self, pid, bar, onset, staff=1, group=1):
        """MIDI input picks the spelling itself (68 came in as A flat in S6, as G sharp in S8): the runner
        reads the note and respells it only when Dorico shows the other name. group=k: the note starts k
        repeated notes typed one after the other, which Dorico spells alike, so a wrong first note means
        all k are respelled at once (a respell of a right note would make B double sharp of C sharp)"""
        s = self.spec(pid, bar, onset, staff)
        (n,) = s['names']
        m = re.match(r'([A-G])(#|b)(-?\d+)$', n)
        i = STEPS.index(m.group(1))
        other = STEPS[(i + 1) % 7] + 'b' if m.group(2) == '#' else STEPS[(i - 1) % 7] + '#'
        octv = int(m.group(3)) + (1 if m.group(1) == 'B' and m.group(2) == '#' else -1 if m.group(1) == 'C' and m.group(2) == 'b' else 0)
        st = self.step(f'spelling of {n} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff,
                       edits=[f'NoteEdit.RespellUsingNoteName{"Below" if m.group(2) == "#" else "Above"}'])
        st['spell'] = f'Note: {other}{octv} '
        st['expect'][1].append(st['spell'])
        if group > 1:
            st['group'] = [f'EventEdit.NavigateRightExtend*{group - 1}']
            self.cursor = None
        return st

    def pitch(self, pid, bar, onset, steps, staff=1, chromatic=False):
        """move an existing note by scale steps (NoteEdit.PitchUp is Alt+Up), or by semitones with
        chromatic=True (G sharp to G): it keeps its ID, ties and slurs"""
        cmd = ('NoteEdit.PitchUp' if steps > 0 else 'NoteEdit.PitchDown') + ('Chromatic' if chromatic else '')
        return self.step(f'{self.who(pid)} bar {bar} {abs(steps)} step(s) {"up" if steps > 0 else "down"}', pid, bar, onset, staff, edits=[cmd] * abs(steps))

    def shorten(self, pid, bar, onset, steps, staff=1):
        """EventEdit.DurationShortenByGrid `steps` times (the rhythmic grid is an eighth): the note keeps
        its ID, ties and slurs. Dorico shortens the selected note only, and a selection by ID is one
        note, so each note of a chord gets its own step (S23, Nov 17: the violas' G sharp ended on beat
        2 and their E and B held on)"""
        s = self.spec(pid, bar, onset, staff)
        out = []
        for n in s['names']:
            st = self.step(f'{self.who(pid)} bar {bar}: {n} {steps} grid step(s) shorter', pid, bar, onset, staff,
                           edits=['EventEdit.DurationShortenByGrid'] * steps)
            if not st['target']:
                raise ValueError(f'{self.who(pid)} bar {bar}: shorten a note with an ID, not a typed one')
            st['target'] = dict(st['target'], names=[n])
            st['expect'] = [bar, [f'Note: {n} ']]
            out.append(st)
        return out

    def split_beam(self, pid, bar, onset, staff=1):
        return self.step(f'beam split for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=['Edit.SplitBeam'])

    def respell(self, pid, bar, onset, up=True, staff=1):
        return self.step(f'respell {self.who(pid)} bar {bar}', pid, bar, onset, staff,
                         edits=[f'NoteEdit.RespellUsingNoteName{"Above" if up else "Below"}'])

    def insert_bars(self, at_bar, count, check, flow=0):
        """insert count empty bars before bar at_bar (all staves), then check that the note at check =
        (pid, bar, onset) moved count bars later; Dorico takes the time in quarters, as 'n, d' fractions"""
        m = re.search(r'<beats>(\d+)</beats>\s*<beat-type>(\d+)</beat-type>', next(iter(self.cur.parts.values()))[0][1])
        per_bar = Fraction(int(m.group(1)) * 4, int(m.group(2)))
        pos, dur = per_bar * (at_bar - 1), per_bar * count
        s = self.spec(*check)
        st = dict(label=f'insert {count} bar(s) before bar {at_bar}',
                  insert=[f'NoteInput.CreateBarLine?Duration={dur.numerator}\\, {dur.denominator}&RhythmicPosition={pos.numerator}\\, {pos.denominator}'
                          f'&RhythmicPositionIncludesLeftOfNotes=1&FlowID={flow}'],
                  then=self.short(s), expect=[s['bar'] + count, s['expect'][1]])
        self.steps.append(st)
        self.cursor = None
        return st

    def explode(self, pid, b0, b1, staves, staff=1):
        """copy the chords of bars b0-b1 and paste-explode them onto this staff and the staves-1 below"""
        self.step(f'copy {self.who(pid)} bars {b0}-{b1}', pid, b0, 0, staff, to=(b1, None), plain=['Edit.Copy'])
        s = self.step(f'spread over {staves} staves', pid, b0, 0, staff, down=staves - 1, edits=['Edit.PasteExplode'])
        self.cursor = None
        return s

    def commands(self):
        n = 0
        for s in self.steps:
            if 'caret' in s:
                n += 2 + count(s['caret']['moves']) + count(s['edits'])
                continue
            if 'insert' in s:
                n += len(s['insert']) + 1
                continue
            walk = s['rel'] if s.get('rel') is not None else (['select'] if s['target'] else ['select'] + s['via']['moves'])
            n += count(walk) + count(s['extend'] + s['plain'] + s['edits'])
        return n

    def save(self, path, requires=()):
        """requires: the suggestions this one builds on (like ['S7']); the Accept hook runs their plans first"""
        json.dump(dict(format=2, steps=self.steps, commands=self.commands(), requires=list(requires)), open(path, 'w'), indent=1)
