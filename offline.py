"""Run the loop with NO OpenRouter spend: dump the context to a file, read edits back from a file.

Brian: "why can't you spin up individual Sonnet agents on my Claude Code plan instead of using
OpenRouter API credits?" No reason at all - that was my mistake. The model in the loop can be
Claude Code itself (or a subagent), with files as the interface.

    python offline.py context "Orchestral Idea" 18 20     -> writes context.md
    ...an agent reads context.md and writes edits.json...
    python offline.py apply "Orchestral Idea" edits.json  -> validates, gates, applies, renders
"""
import json, os, sys

import diffview, scorewright as sw, xmledit

OUT = '/private/tmp/claude-502/-Users-bdogellis-repos/4f969902-2eed-4359-8d3b-6b221b5d03bf/scratchpad/'


def context(stem, lo, hi):
    path = sw.source_path(stem)
    raw = open(path).read()
    cf = sw.computed_facts(path, raw, stem)
    cc = sw.corpus_context(stem, f'bars {lo} {hi}') or '(no corpus matches)'
    body = f'''# Continue `{stem}`, bars {lo}-{hi}

{sw.system_prompt(False, True)}

## [COMPUTED]
{cf}

## {cc}

## Task
Write bars {lo}-{hi}. The music must CONTINUE, not conclude. Match the TEXTURE TARGET above.
Emit ONLY a JSON array of ops to `edits.json` - no prose, no fences. Example:
[{{"op":"append_measures","count":3,"why":"..."}},
 {{"op":"write_notes","measure":{lo},"part":"Violin I","staff":1,"voice":1,
   "events":["B-5:1","r:2","G5:0.5","F5:0.5"],"why":"..."}}]
'''
    p = OUT + 'context.md'
    open(p, 'w').write(body)
    print(f'{p}  ({len(body):,} chars)')
    return p


def apply(stem, edits_path, context_bars=2, force=False):
    """Apply an edit set to the working copy.

    GUARD: source_path() prefers the working copy, so re-running the same edits applies them TWICE
    to an already-edited score. That happened, and the give-away was a "before" audio identical in
    length to the "after". Refuse unless the working copy still matches the pristine export, or
    --force is passed for a genuine incremental edit.
    """
    path = sw.source_path(stem)
    raw = open(path).read()
    pristine = sw.XML_DIR + stem + '.musicxml'
    if not force and path != pristine and os.path.exists(pristine):
        if open(pristine).read() != raw:
            print(f'REFUSED: the working copy already differs from the pristine export.\n'
                  f'  Re-applying the same edits would double them. Either\n'
                  f'    cp "{pristine}" "{path}"     to start clean, or\n'
                  f'    pass --force                  for a genuine incremental edit.')
            return 1
    edits = json.load(open(edits_path))
    try:
        new, notes = sw.apply_edits(raw, edits)
    except ValueError as e:
        print('REJECTED: ' + str(e))
        return 1
    for m, d, w in notes:
        print(f'  bar {m:>3}  {d[:88]}')
    html = diffview.build(raw, new, notes, stem, context=context_bars)
    open(OUT + 'sw_diff.html', 'w').write(html)
    dst = '/Users/bdogellis/Documents/Score Exports/working/' + stem + '.musicxml'
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w').write(new)
    print(f'\nACCEPTED -> {dst}\ndiff -> {OUT}sw_diff.html')
    _show(OUT + 'sw_diff.html')
    return 0


def _show(path):
    """Reuse the SAME Chrome tab. Opening a new one each iteration left 34 tabs holding several MB
    of embedded audio apiece and put the machine into heavy swap."""
    import subprocess
    js = f'''
    tell application "Google Chrome"
      set found to false
      repeat with w in windows
        repeat with t in tabs of w
          if URL of t contains "sw_diff.html" then
            tell t to reload
            set found to true
          end if
        end repeat
      end repeat
      if not found then open location "file://{path}"
      activate
    end tell'''
    subprocess.run(['osascript', '-e', js], capture_output=True)


if __name__ == '__main__':
    if sys.argv[1] == 'context':
        context(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]))
    else:
        sys.exit(apply(sys.argv[2], sys.argv[3], force='--force' in sys.argv))
