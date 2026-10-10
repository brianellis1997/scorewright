"""Write a MIDI file directly from a music21 score. ~60 lines, fully under our control.

music21's own exporter kept losing parts and overriding program changes: 422 of 458 notes collapsed
onto one channel (the whole orchestra played as contrabass), and every workaround lost the first
part. MIDI is a simple format; writing it ourselves removes the whole class of problem.

Format 1: track 0 is tempo, then one track per part, each with its own channel and GM program.
"""
import struct


def _vlq(n):
    """MIDI variable-length quantity."""
    out = bytearray([n & 0x7F])
    n >>= 7
    while n:
        out.insert(0, (n & 0x7F) | 0x80)
        n >>= 7
    return bytes(out)


def _track(events, tpq):
    """events: [(tick, status_byte, d1, d2)] -> a MTrk chunk."""
    events.sort(key=lambda e: (e[0], 0 if e[1] & 0xF0 == 0x80 else 1))
    body, last = bytearray(), 0
    for tick, status, d1, d2 in events:
        body += _vlq(max(0, tick - last))
        body += bytes([status, d1, d2]) if d2 is not None else bytes([status, d1])
        last = tick
    body += _vlq(0) + b'\xFF\x2F\x00'
    return b'MTrk' + struct.pack('>I', len(body)) + bytes(body)


def write(score, path, part_channel, part_program, bpm=120, tpq=480, velocity=88):
    """part_channel/part_program: list, one entry per score.parts, aligned by index."""
    chunks = []
    tempo = int(60_000_000 / bpm)
    meta = bytearray(_vlq(0)) + b'\xFF\x51\x03' + struct.pack('>I', tempo)[1:]
    meta += _vlq(0) + b'\xFF\x2F\x00'
    chunks.append(b'MTrk' + struct.pack('>I', len(meta)) + bytes(meta))

    for i, part in enumerate(score.parts):
        ch = part_channel[i]
        prog = part_program[i]
        ev = [(0, 0xC0 | ch, prog, None)]
        for n in part.recurse().notes:
            start = int(round(float(n.offset if n.activeSite is part else
                                    n.getOffsetInHierarchy(part)) * tpq))
            dur = max(1, int(round(float(n.quarterLength) * tpq)))
            for p in n.pitches:
                m = int(p.midi)
                if not 0 <= m <= 127:
                    continue
                ev.append((start, 0x90 | ch, m, velocity))
                ev.append((start + dur, 0x80 | ch, m, 0))
        if len(ev) > 1:
            chunks.append(_track(ev, tpq))

    head = b'MThd' + struct.pack('>IHHH', 6, 1, len(chunks), tpq)
    open(path, 'wb').write(head + b''.join(chunks))
    return len(chunks)
