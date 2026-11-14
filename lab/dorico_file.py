"""Read the notes of a Dorico project (.dorico) with the IDs Dorico itself uses for them, from the file alone.

A .dorico file is a zip whose score.dtn member holds the project as one tree of records: a name table, a
value pool and a stream of LEB128 records (see _locate and _tokenize). Each note comes back with the triple
EventEdit.Select takes (FlowID, EventBlockID, EventID), its position and duration in quarter notes from the
start of its flow, its sounding MIDI pitch, its instrument (the player's name, which is also the MusicXML part
name), staff and voice, and its bar and onset when the flow's time signatures make them derivable.

The record layout follows DoricoUse (github.com/Delsin-Yu/DoricoUse, ProjectFileScoreReader*.cs). Checked on
a Dorico 4.0.31 project against its MusicXML export.

usage: python dorico_file.py <project.dorico> [notes per instrument]
"""
import struct
import sys
import time
import zipfile
from array import array
from bisect import bisect_right
from dataclasses import dataclass, field
from fractions import Fraction

NODE_BIT = 0x02
MARKER_MASK = 0xFC
MAX_CANDIDATES = 64
NAME_MARKUP = {'{@flat@}': '\u266d', '{@sharp@}': '\u266f', '{@natural@}': '\u266e'}
PITCH_NAMES = ('C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B')
NATURALS = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


class FormatError(ValueError):
    pass


@dataclass(slots=True)
class Note:
    flow_id: int
    block_id: int
    event_id: int
    position: Fraction
    duration: Fraction
    pitch: int | None
    instrument: str | None = None
    staff: int | None = None
    voice: int | None = None
    bar: int | None = None
    onset: Fraction | None = None
    spelling: str | None = None

    @property
    def select_command(self):
        return f'EventEdit.Select?FlowID={self.flow_id}&EventID={self.event_id}&EventBlockID={self.block_id}'

    @property
    def pitch_name(self):
        if self.pitch is None:
            return None
        letter = (self.spelling or '')[:1].upper()
        if letter in NATURALS:
            octave = (self.pitch - NATURALS[letter] - 6) // 12
            shift = self.pitch - 12 * octave - 12 - NATURALS[letter]
            if -2 <= shift <= 2:
                return letter + ('#' * shift if shift > 0 else 'b' * -shift) + str(octave)
        return PITCH_NAMES[self.pitch % 12] + str(self.pitch // 12 - 1)


@dataclass(slots=True)
class Flow:
    flow_id: int
    name: str | None
    instruments: list[str] = field(default_factory=list)
    time_signatures: list[tuple[Fraction, int | None, int | None]] = field(default_factory=list)
    notes: list[Note] = field(default_factory=list)


@dataclass(slots=True)
class Project:
    path: str
    file_version: str | None
    flows: list[Flow]
    stats: dict


class _Tree:
    """The record stream as flat arrays. Record 0 is the root, a node's children follow it in order, and
    ends[i] is the record after i's subtree."""

    __slots__ = ('names', 'pool', 'keys', 'vals', 'ends', 'node')

    def __init__(self, names, pool, keys, vals, ends, node):
        self.names, self.pool, self.keys, self.vals, self.ends, self.node = names, pool, keys, vals, ends, node

    def name(self, i):
        return self.names[self.keys[i]]

    def children(self, i):
        j, end, ends = i + 1, self.ends[i], self.ends
        while j < end:
            yield j
            j = ends[j]

    def fields(self, i):
        return {self.names[self.keys[j]]: self.vals[j] for j in self.children(i) if not self.node[j]}

    def text(self, i):
        return {} if i is None else {key: self.pool[v] for key, v in self.fields(i).items()}

    def child(self, i, name):
        if i is not None:
            for j in self.children(i):
                if self.node[j] and self.names[self.keys[j]] == name:
                    return j
        return None

    def items(self, i):
        """A collection's objects: Dorico writes some as wrapper -> array -> objects, others as wrapper -> objects."""
        if i is None or not self.node[i]:
            return []
        kids = list(self.children(i))
        if len(kids) == 1 and self.node[kids[0]] and self.name(kids[0]) == 'array':
            kids = list(self.children(kids[0]))
        return [j for j in kids if self.node[j]]


def _u32(data, pos):
    return struct.unpack_from('<I', data, pos)[0]


def _strings(data, pos, count):
    out = []
    for _ in range(count):
        end = data.index(b'\0', pos)
        out.append(data[pos:end].decode('utf-8', 'replace'))
        pos = end + 1
    return out, pos


def _locate(data):
    """Yield (names, pool, stream start, record count or None) for each way the tables may be laid out.

    Dorico 4.0.31 writes u32 4, u32 1, u32 name count, the names (NUL-terminated), u32 pool count, the pool
    (NUL-terminated, entry 0 empty), u32 record count, then the stream, and a leaf's value is a 0-based pool
    index. DoricoUse reads the same bytes without the counts: names up to an empty string, then the first
    node record with key 0 and aux 0 that parses to the last byte. That is the fallback here."""
    if len(data) < 16:
        raise FormatError('score.dtn is shorter than its header')
    try:
        names, pos = _strings(data, 12, _u32(data, 8))
        count = _u32(data, pos)
        if count <= len(data) - pos:
            pool, pos = _strings(data, pos + 4, count)
            yield names, pool, pos + 4, _u32(data, pos)
    except (ValueError, struct.error):
        pass
    names, pos = [], 12
    while pos < len(data) and data[pos] != 0:
        end = data.index(b'\0', pos)
        names.append(data[pos:end].decode('utf-8', 'replace'))
        pos = end + 1
    while pos < len(data) and data[pos] == 0:
        pos += 1
    start, tried = pos, 0
    for p in range(start, len(data) - 2):
        if data[p] & NODE_BIT and data[p + 1] == 0 and data[p + 2] == 0:
            tried += 1
            if tried > MAX_CANDIDATES:
                break
            pool = [''] + [b.decode('utf-8', 'replace') for b in data[start:p].split(b'\0')[:-1]]
            yield names, pool, p, None


def _varint(data, pos):
    result = shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if b < 0x80:
            return result, pos
        shift += 7


def _tokenize(data, pos):
    """Parse the record stream at pos. A record is a tag byte, then LEB128 varints: a leaf is key, value; a
    node is key, aux, count, count record numbers (its children's), then its count children. The tag's bit 1
    marks a node, bit 0 is a variant, and the other bits are the same in every record of a file."""
    marker = data[pos] & MARKER_MASK
    keys, vals, ends, node = array('I'), array('I'), array('I'), bytearray()
    stack = []
    idx = max_key = max_val = 0
    try:
        while True:
            tag = data[pos]
            if tag & MARKER_MASK != marker:
                raise FormatError(f'unexpected tag {tag:#x} at byte {pos}')
            key = data[pos + 1]
            if key < 0x80:
                pos += 2
            else:
                key, pos = _varint(data, pos + 1)
            v = data[pos]
            if v < 0x80:
                pos += 1
            else:
                v, pos = _varint(data, pos)
            if stack:
                stack[-1][1] -= 1
            keys.append(key)
            ends.append(idx + 1)
            max_key = max(max_key, key)
            if tag & NODE_BIT:
                count = data[pos]
                if count < 0x80:
                    pos += 1
                else:
                    count, pos = _varint(data, pos)
                for _ in range(count):
                    while data[pos] & 0x80:
                        pos += 1
                    pos += 1
                vals.append(count)
                node.append(1)
                if count:
                    stack.append([idx, count])
            else:
                vals.append(v)
                node.append(0)
                max_val = max(max_val, v)
            idx += 1
            while stack and stack[-1][1] == 0:
                ends[stack.pop()[0]] = idx
            if not stack:
                break
    except IndexError:
        raise FormatError('the record stream ends inside a record') from None
    except OverflowError:
        raise FormatError(f'a number near byte {pos} does not fit 32 bits') from None
    if pos != len(data):
        raise FormatError(f'the root ends at byte {pos} of {len(data)}')
    return keys, vals, ends, node, max_key, max_val


def _parse(data):
    reasons = []
    for names, pool, start, records in _locate(data):
        if not names or names[0] != 'kScore' or start >= len(data) or not data[start] & NODE_BIT:
            reasons.append(f'no kScore node at byte {start}')
            continue
        try:
            keys, vals, ends, node, max_key, max_val = _tokenize(data, start)
        except FormatError as e:
            reasons.append(str(e))
            continue
        if keys[0] != 0 or max_key >= len(names) or max_val >= len(pool):
            reasons.append(f'the stream at byte {start} indexes past the tables')
        elif records is not None and records != len(keys):
            reasons.append(f'the stream at byte {start} has {len(keys)} records, the header says {records}')
        else:
            return _Tree(names, pool, keys, vals, ends, node), start
    raise FormatError('score.dtn is not a Dorico score this reader understands: ' + '; '.join(reasons[:4]))


def _int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def _display(name):
    for token, sign in NAME_MARKUP.items():
        name = name.replace(token, sign) if name else name
    return name


def _entries(tree, event):
    return [tree.text(e) for e in tree.items(tree.child(tree.child(event, 'propertyTable'), 'entries'))]


def _spelling(entries):
    for t in entries:
        if t.get('propertyType') == 'kNoteSpelling' and ':' in t.get('value', ''):
            return t['value'].split(':', 1)[1].strip().strip('"') or None
    return None


def _plain(names):
    """False for the bar-division fields and properties Dorico 4 names for a pickup or irregular bar, open
    metre or a bar number change (irregularBarLength, timeSignatureOpenAppearance, barNumberChangeIfAny...)."""
    return not any(word in name.lower() for name in names for word in ('irregular', 'open', 'barnumberchange'))


def _signature(tree, element):
    """(numerator, denominator) of a bar-division element, or None when it is anything but one plain time
    signature that starts a new bar: a pickup, an aggregate or interchangeable metre, a barline alone."""
    data = tree.child(element, 'barDivisionData')
    if data is None or not _plain(tree.name(j) for j in tree.children(data)):
        return None
    parts = tree.items(tree.child(tree.child(data, 'timeSignature'), 'timeSignaturesAndDivisions'))
    if len(parts) != 1 or tree.text(parts[0]).get('behaviour') != 'kNewBar':
        return None
    inter = tree.child(data, 'interchangeableTimeSignatures')
    if inter is not None and any(tree.node[j] for j in tree.children(inter)):
        return None
    sig = tree.text(tree.child(parts[0], 'timeSignature'))
    num, den = _int(sig.get('numerator')), _int(sig.get('denominator'))
    return (num, den) if num and den and num > 0 and den > 0 else None


def _bar_spans(divisions):
    """(start, its bar number, bar length or None) per time signature. A bar cut short by the next time
    signature still counts as a bar, and nothing is derived from a division this reader cannot read on."""
    spans = []
    for position, sig in divisions:
        if spans:
            start, bar, length = spans[-1]
            if length is None:
                break
            bar += -(-(position - start) // length)
        elif position != 0:
            break
        else:
            bar = 1
        spans.append((position, bar, None if sig is None else Fraction(4 * sig[0], sig[1])))
    return spans


def _locate_bar(spans, starts, position):
    k = bisect_right(starts, position) - 1
    if k < 0 or spans[k][2] is None:
        return None, None
    start, bar, length = spans[k]
    whole = (position - start) // length
    return bar + whole, position - start - whole * length


def _read_flow(tree, f, player_names, fractions):
    info = tree.text(f)
    flow = Flow(_int(info.get('flowID')), info.get('flowName'))
    pool = tree.pool

    def frac(v):
        r = fractions.get(v)
        if r is None:
            try:
                r = fractions[v] = Fraction(pool[v] or 0)
            except ValueError:
                raise FormatError(f'not a rational: {pool[v]!r}') from None
        return r

    staves, streams, voice_lists = {}, {}, []
    for fp in tree.items(tree.child(f, 'flowPlayers')):
        d = tree.text(fp)
        pid = _int(d.get('playerID'))
        name = player_names.get(pid)
        flow.instruments.append(name)
        streams[_int(d.get('eventStreamID'))] = (name, None, None, pid, None)
        for fpi in tree.items(tree.child(fp, 'flowPlayerInstruments')):
            iid = _int(tree.text(fpi).get('instrumentID'))
            for s in tree.items(tree.child(fpi, 'staveStreamInfos')):
                d = tree.text(s)
                nth = _int(d.get('nthStaveInInstrument'))
                staves[_int(d.get('staveID'))] = (pid, iid, None if nth is None else nth + 1)
                streams[_int(d.get('staveStreamID'))] = (name, staves[_int(d.get('staveID'))][2], None, pid, iid)
            voice_lists.append((name, pid, iid, tree.items(tree.child(fpi, 'voiceStreamInfos'))))
    staves.pop(None, None)
    per_staff = {}
    for name, pid, iid, voices in voice_lists:
        for s in voices:
            d = tree.text(s)
            home = staves.get(_int(d.get('defaultLogicalStaveID')), (None, None, None))
            staff = home[2] if home[:2] == (pid, iid) else None
            k = per_staff[pid, iid, staff] = per_staff.get((pid, iid, staff), 0) + 1
            streams[_int(d.get('voiceStreamID'))] = (name, staff, k, pid, iid)
    streams.pop(None, None)

    block_stream = {}
    for bi in tree.items(tree.child(f, 'blockInstances')):
        d = tree.text(bi)
        block_stream[_int(d.get('blockID'))] = _int(d.get('streamID'))

    signatures = {}
    for table in tree.items(tree.child(f, 'elementTables')):
        if tree.name(table) == 'BarDivisionElementTableDefinition':
            for element in tree.items(table):
                signatures[_int(tree.text(element).get('elementID'))] = _signature(tree, element)

    divisions, notes = [], []
    local_metre = False
    nowhere = (None, None, None, None, None)
    for b in tree.items(tree.child(f, 'blocks')):
        block = tree.text(b)
        block_id = _int(block.get('blockID'))
        name, staff, voice, pid, iid = streams.get(block_stream.get(block_id), nowhere)
        for e in tree.items(tree.child(b, 'events')):
            kind = tree.name(e)
            if kind == 'NoteEventDefinition':
                d = tree.fields(e)
                cross = staves.get(_int(pool[d.get('logicalStaveIDOverride', 0)]))
                notes.append(Note(flow.flow_id, block_id, _int(pool[d.get('eventID', 0)]),
                                  frac(d.get('position', 0)), frac(d.get('duration', 0)),
                                  _int(pool[d.get('pitch', 0)]), name,
                                  cross[2] if cross and cross[:2] == (pid, iid) else staff, voice,
                                  spelling=_spelling(_entries(tree, e))))
            elif kind == 'BarDivisionEventDefinition':
                d = tree.fields(e)
                sig = signatures.get(_int(pool[d.get('barDivisionElementID', 0)]))
                plain = _plain(t.get('propertyType', '') for t in _entries(tree, e))
                divisions.append((frac(d.get('position', 0)), sig if plain else None))
                local_metre |= block.get('parentEventStreamType') != 'kGlobalTimebaseStream'

    divisions.sort(key=lambda x: x[0])
    flow.time_signatures = [(p, *(sig or (None, None))) for p, sig in divisions]
    spans = [] if local_metre else _bar_spans(divisions)
    starts = [s[0] for s in spans]
    order = {name: k for k, name in reversed(list(enumerate(flow.instruments)))}
    for note in notes:
        note.bar, note.onset = _locate_bar(spans, starts, note.position)
    notes.sort(key=lambda n: (n.position, order.get(n.instrument, len(order)), n.staff or 0, n.voice or 0,
                              -1 if n.pitch is None else n.pitch, n.event_id))
    flow.notes = notes
    return flow


def read(path):
    """Read a .dorico file into a Project whose flows hold their notes in score order."""
    t0 = time.perf_counter()
    with zipfile.ZipFile(path) as z:
        if 'score.dtn' not in z.namelist():
            raise FormatError(f'{path} has no score.dtn, so it is not a Dorico project')
        data = z.read('score.dtn')
    tree, start = _parse(data)
    players = {}
    for p in tree.items(tree.child(0, 'scorePlayers')):
        d = tree.text(p)
        players[_int(d.get('playerID'))] = _display(d.get('displayName') or d.get('baseName'))
    fractions = {}
    flows = [_read_flow(tree, f, players, fractions) for f in tree.items(tree.child(0, 'flows'))]
    stats = {'names': len(tree.names), 'values': len(tree.pool), 'records': len(tree.keys),
             'stream_start': start, 'seconds': time.perf_counter() - t0}
    return Project(str(path), tree.text(0).get('fileVersion'), flows, stats)


def _q(value):
    return '-' if value is None else str(value)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip().splitlines()[-1])
        return 2
    per = int(argv[1]) if len(argv) > 1 else 6
    project = read(argv[0])
    s = project.stats
    print(f'{project.path}\nfile version {project.file_version}: {s["names"]} names, {s["values"]} values, '
          f'{s["records"]} records, read in {s["seconds"]:.2f} s')
    for flow in project.flows:
        sigs = ', '.join(f'{n}/{d} at {p}' if n else f'unreadable at {p}' for p, n, d in flow.time_signatures)
        sounding = {n.instrument for n in flow.notes}
        playing = [name for name in dict.fromkeys(flow.instruments) if name in sounding]
        print(f'\nflow {flow.flow_id} "{flow.name}": {len(flow.notes)} notes, {len(playing)} of '
              f'{len(flow.instruments)} instruments play; time signatures: {sigs or "none"}')
        for name in playing:
            mine = [n for n in flow.notes if n.instrument == name]
            print(f'  {name}: {len(mine)} notes')
            for n in mine[:per]:
                at = f'bar {n.bar} +{n.onset}' if n.bar is not None else f'pos {n.position}'
                print(f'    {at:<12} {n.pitch_name or "?":<4} {_q(n.pitch):>3}  dur {_q(n.duration):<4}  '
                      f'staff {_q(n.staff)} voice {_q(n.voice)}  flow {n.flow_id} block {n.block_id} '
                      f'event {n.event_id}')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
