"""Do the tests actually FAIL when the code is broken? A test that cannot fail is decoration.

Each mutation is a plausible regression. Any that survives means nothing is guarding that behaviour.
"""
import re, subprocess, shutil, sys, os

SRC = 'xmledit.py'
PY_ = '/Users/bdogellis/miniforge3/envs/whisperer/bin/python'
MUTATIONS = [
    ('find_note counts rests too',
     "        if '<rest' in t:\n            continue\n", "        if False:\n            continue\n"),
    ('tie guard removed from set_pitch',
     "    if not allow_tied:\n        st = tie_state(b)\n        if st:",
     "    if False:\n        st = tie_state(b)\n        if st:"),
    ('tie guard removed from split_note',
     "    st = tie_state(blk)\n    if st:\n        raise ValueError(f'that note is tied ({st}); splitting",
     "    st = tie_state(blk)\n    if False:\n        raise ValueError(f'that note is tied ({st}); splitting"),
    ('validate_edit always passes',
     "    a, b = totals(before), totals(after)\n    bad = []",
     "    a, b = totals(before), totals(before)\n    bad = []"),
    ('chord members default to voice 1',
     "    return (int(s.group(1)) if s else last[0], int(v.group(1)) if v else last[1])",
     "    return (int(s.group(1)) if s else 1, int(v.group(1)) if v else 1)"),
    ('articulation whitelist disabled',
     "    if kind not in ARTICULATIONS:", "    if False and kind not in ARTICULATIONS:"),
    ('slur applied start-first (offsets shift)',
     "    out = raw[:b[0]] + _ensure_notations(raw[b[0]:b[1]],\n"
     "                                         f'<slur type=\"stop\" number=\"{n}\" />') + raw[b[1]:]\n"
     "    out = out[:a[0]] + _ensure_notations(out[a[0]:a[1]],\n"
     "                                         f'<slur type=\"start\" number=\"{n}\" />') + out[a[1]:]",
     "    out = raw[:a[0]] + _ensure_notations(raw[a[0]:a[1]],\n"
     "                                         f'<slur type=\"start\" number=\"{n}\" />') + raw[a[1]:]\n"
     "    out = out[:b[0]] + _ensure_notations(out[b[0]:b[1]],\n"
     "                                         f'<slur type=\"stop\" number=\"{n}\" />') + out[b[1]:]"),
    ('slur numbers always 1',
     "    n = 1\n    while n in used:\n        n += 1\n    return n",
     "    return 1"),
    ('excerpt skips attributes merge',
     "                    missing = [v for t in ('divisions', 'key', 'time', 'staves', 'clef')",
     "                    missing = [] or [v for t in ()\n                               ] or [v for t in ('divisions',"),
    ('notations rebuild drops existing children',
     "        kids.append(inner.strip())", "        kids = [inner.strip()]"),
    ('write_notes skips the bar-length check',
     "    if total != target:", "    if False and total != target:"),
    ('tuplet time-modification not emitted',
     "    if tup:\n        body.append('<time-modification>')",
     "    if False and tup:\n        body.append('<time-modification>')"),
    # The REAL bug: voice/instrument emitted AFTER <type>, which makes music21 ignore
    # <time-modification>. Must reorder, not delete - deleting them is a different (silent) bug.
    ('note children emitted in the wrong order (voice after type)',
     "    body += keep_pre\n    tt = dur_to_type",
     "    tt = dur_to_type"),
    ('note children: voice appended at the end instead',
     "    body += keep_post\n    if tup and tup_pos", "    body += keep_pre + keep_post\n    if tup and tup_pos"),
    ('tuplet rounding dropped (85/85/85 instead of 85/85/86)',
     "        for k in range(want - sum(durs)):\n            durs[-(k + 1)] += 1",
     "        for k in range(0):\n            durs[-(k + 1)] += 1"),
    ('measure_span ignores the part (the orchestral bug)',
     "    i = part_index(raw, part)\n    lo, hi = ps[i][3], ps[i][4]",
     "    lo, hi = 0, len(raw)"),
    ('part_index always returns 0',
     "    w = str(want).strip().lower()", "    return 0\n    w = str(want).strip().lower()"),
    ('duration words no longer accepted',
     "    q = DURWORD[d] if d in DURWORD else float(d)", "    q = float(d)"),
]

orig = open(SRC).read()
shutil.copy(SRC, SRC + '.bak')
caught = survived = skipped = 0
try:
    for name, old, new in MUTATIONS:
        if old not in orig:
            print(f'  SKIP    {name}  (pattern not found - update this mutation)')
            skipped += 1
            continue
        open(SRC, 'w').write(orig.replace(old, new, 1))
        r = subprocess.run([PY_, 'test_xmledit.py'], capture_output=True, text=True)
        if r.returncode:
            print(f'  caught  {name}')
            caught += 1
        else:
            print(f'  SURVIVED {name}   <-- nothing tests this')
            survived += 1
finally:
    shutil.move(SRC + '.bak', SRC)
print(f'\n{caught} caught, {survived} survived, {skipped} skipped')
sys.exit(1 if survived else 0)
