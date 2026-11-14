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
    """one state of the score: per part its measures, transposition and staves"""

    def __init__(self, xml):
        self.names = dict(re.findall(r'<score-part id="([^"]+)">\s*<part-name>([^<]*)</part-name>', xml))
        self.parts, self.staves = {}, []
        for pid in re.findall(r'<score-part id="([^"]+)"', xml):
            body = re.search(rf'<part id="{pid}">(.*?)</part>', xml, re.S).group(1)
            t = re.search(r'<transpose\b.*?</transpose>', body, re.S)
            tx = t.group(0) if t else ''
            g = lambda tag: int(m.group(1)) if (m := re.search(rf'<{tag}>(-?\d+)</{tag}>', tx)) else 0
            tr = (g('diatonic') + 7 * g('octave-change'), g('chromatic') + 12 * g('octave-change'))
            n = int((re.search(r'<staves>(\d+)</staves>', body) or [0, 1])[1])
            bars = {int(m.group(1)): m.group(2) for m in re.finditer(r'<measure number="(\d+)"[^>]*>(.*?)</measure>', body, re.S)}
            div = re.findall(r'<divisions>(\d+)</divisions>', body)
            self.parts[pid] = (bars, tr, int(div[0]) if div else 1)
            self.staves += [(pid, s) for s in range(1, n + 1)]

    def items(self, pid, bar, staff=1):
        """[(onset, 'Rest' or [concert names, top first], tied from before, tied on)], voice by voice in file order"""
        bars, tr, div = self.parts[pid]
        t, out = 0, []
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
                out.append([Fraction(t, div), 'Rest', False, False])
            elif mine:
                p = re.search(PITCH, s)
                out.append([Fraction(t, div), [shift((p.group(1), int(p.group(2) or 0), int(p.group(3))), *tr)],
                            '<tie type="stop"/>' in s, '<tie type="start"/>' in s])
            t += d
        for it in out:
            if it[1] != 'Rest':
                it[1] = [name(p) for p in sorted(it[1], key=lambda p: -(12 * (p[2] + 1) + PC[p[0]] + p[1]))]
        return out

    def nav(self, pid, bar, staff=1):
        """the items the arrows stop at: a tie continuation belongs to the chain that started earlier"""
        return [it for it in self.items(pid, bar, staff) if not it[2]]

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
        if b1 == b2:
            return k2 - k1
        return len(self.cur.nav(pid, b1, staff)) - k1 + sum(len(self.cur.nav(pid, b, staff)) for b in range(b1 + 1, b2)) + k2

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
        for b in range(bar, max(bar - 8, 0), -1):
            if not self.unchanged(pid, b):
                continue
            its = self.cur.nav(pid, b, staff)
            for j in range(len(its) - 1 if b < bar else k - 1, -1, -1):
                if its[j][1] != 'Rest':
                    return dict(target=self.short(self.spec(pid, b, its[j][0], staff)), moves=self.walk(pid, staff, (b, j), (bar, k)))
        for b in range(bar, max(bar - 4, 0), -1):
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
        if b1 == b0:
            return k1 - k0
        return len(self.cur.nav(pid, b0, staff)) - k0 + sum(len(self.cur.nav(pid, b, staff)) for b in range(b0 + 1, b1)) + k1

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
        if to:
            n = self.span(pid, bar, s['item'], to[0], to[1], staff)
            if n:
                st['extend'].append(f'EventEdit.NavigateRightExtend*{n}')
                k1 = self.cur.index(pid, to[0], to[1], staff)
                st['range'] = [bar, self.cur.chain_end(pid, to[0], self.cur.nav(pid, to[0], staff)[k1][0], staff)]
        if down:
            st['extend'].append(f'EventEdit.NavigateDownExtend*{down}')
        st['plain'], st['edits'] = list(plain), list(edits)
        self.steps.append(st)
        keeps = not st['extend'] and all(e.split('?')[0] in KEEPS for e in st['edits'])
        self.cursor = (pid, staff, bar, s['item']) if keeps else None
        return st

    def notes(self, pid, bar, onset, events, staff=1):
        """note entry from the caret: events = [(names or None for a rest, quarters[, 'tie'])];
        the caret starts at a note with an ID (same staff, or the nearest staff above it) and moves"""
        z = self.cur.staves.index((pid, staff))
        start = None
        for b in range(bar, max(bar - 12, 0), -1):
            for i in [z] + list(range(z - 1, -1, -1)):
                vp, vs = self.cur.staves[i]
                if not self.unchanged(vp, b):
                    continue
                its = [it for it in self.cur.nav(vp, b, vs) if it[1] != 'Rest' and (b < bar or it[0] <= Fraction(onset))]
                if i != z:
                    its = [it for it in its if it[0] == 0]
                if its:
                    it = its[-1] if i == z else its[0]
                    start = (vp, vs, b, it[0], i)
                    break
            if start:
                break
        if not start:
            raise ValueError(f'{self.who(pid)} bar {bar}: no note with an ID to start the caret from')
        vp, vs, vb, von, vi = start
        moves = [f'NoteInput.MoveDown*{z - vi}'] if vi != z else []
        if bar > vb:
            moves.append(f'NoteInput.MoveRightBar*{bar - vb}')
            pos = Fraction(onset)
        else:
            pos = Fraction(onset) - von
        if pos % self.grid:
            raise ValueError(f'{self.who(pid)} bar {bar}: onset {onset} is off the caret grid')
        if pos:
            moves.append(f'NoteInput.MoveRight*{int(pos / self.grid)}')
        edits = []
        for ev in events:
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

    def after_notes(self, xml, pid, bar, onset, staff=1):
        """the score with the notes typed, and where the last typed note is (it stays selected)"""
        self.use(xml)
        self.cursor = (pid, staff, bar, self.cur.index(pid, bar, onset, staff))

    def dynamic(self, pid, bar, onset, mark, staff=1):
        return self.step(f'{mark} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=[f'NoteInput.CreateDynamic?Definition={mark}&UseLocalOverride=0'])

    def articulation(self, pid, bar, onset, value='kStaccatoTenuto', staff=1):
        return self.step(f'{value[1:]} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=[f'NoteInput.SetArticulation?Value={value}'])

    def technique(self, pid, bar, onset, text='pizz.', staff=1):
        """Dorico takes the popover text here (pizz., arco, con sord.), not an ID like pt.pizzicato"""
        return self.step(f'{text} for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=[f'NoteInput.CreatePlayingTechnique?Definition={text}'])

    def slur(self, pid, start, end, staves=1, staff=1):
        return self.step(f'slur for {self.who(pid)} bars {start[0]}-{end[0]}', pid, *start, staff, to=end, down=staves - 1, edits=['NoteInput.SlurStart'])

    def hairpin(self, pid, start, end, up=True, staves=1, staff=1):
        kind = 'Up' if up else 'Down'
        return self.step(f'{"cresc" if up else "dim"} for {self.who(pid)} bars {start[0]}-{end[0]}', pid, *start, staff, to=end, down=staves - 1,
                         edits=[f'NoteInput.HairpinStart?Type=kGradualDynamic{kind}&GradualDynamicType=kCrescOrDim'])

    def tie(self, pid, bar, onset, staff=1):
        s = self.step(f'tie for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=['NoteInput.Tie'])
        self.tied.add((pid, staff, bar, Fraction(onset)))
        self.cursor = None
        return s

    def split_beam(self, pid, bar, onset, staff=1):
        return self.step(f'beam split for {self.who(pid)} in bar {bar}', pid, bar, onset, staff, edits=['Edit.SplitBeam'])

    def respell(self, pid, bar, onset, up=True, staff=1):
        return self.step(f'respell {self.who(pid)} bar {bar}', pid, bar, onset, staff,
                         edits=[f'NoteEdit.RespellUsingNoteName{"Above" if up else "Below"}'])

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
            walk = s['rel'] if s.get('rel') is not None else (['select'] if s['target'] else ['select'] + s['via']['moves'])
            n += count(walk) + count(s['extend'] + s['plain'] + s['edits'])
        return n

    def save(self, path):
        json.dump(dict(format=2, steps=self.steps, commands=self.commands()), open(path, 'w'), indent=1)
