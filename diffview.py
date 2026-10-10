"""Render a proposed score edit as a visual diff: red = before, green = after, with playback.

The notation equivalent of Claude Code's diff. Deliberately NOT via Sibelius: Sibelius shows an
import dialog every time, opens a NEW document rather than editing in place, and offers no diff to
approve. The .musicxml is the living file; verovio renders it; the user approves or rejects;
xmledit.py applies the change to the source text. See PROJECT.md sections 15-17.

Shows an EXCERPT (the edited bars plus context), not the whole score - Brian: "why is it
reproducing the entire score to just show the section it wants to edit".
"""
import base64, os, re, subprocess, tempfile, warnings

import verovio

import xmledit

# Verovio logs MusicXML import notes to stdout, which corrupts the CLI transcript.
try:
    verovio.enableLog(False)
except Exception:
    pass

SF = '/usr/local/lift/Soundfonts/FluidR3_GM2-2.sf2'

VRV = {'pageWidth': 2400, 'pageHeight': 60000, 'scale': 42, 'adjustPageHeight': True,
       'header': 'none', 'footer': 'none', 'xmlIdSeed': 1, 'breaks': 'auto',
       'svgAdditionalAttribute': ['note@pname', 'note@oct', 'measure@n', 'staff@n']}


def render(xml_text, page=1, width=None, timemap=False, n_parts=1):
    """Render one page. `width` re-engraves narrower rather than scaling the SVG down, which keeps
    the notation legible in a half-width column instead of shrinking it to illegibility.

    With timemap=True also returns verovio's note-to-millisecond map. The same `xmlIdSeed` is used
    for both, so the ids in the timemap are the ids in the SVG - that is what makes a playback
    cursor possible without any extra bookkeeping.
    """
    tk = verovio.toolkit()
    opts = dict(VRV)
    if width:
        opts['pageWidth'] = width
    # A 24-stave system at scale 42 fits ONE bar per line, so four written bars became four
    # enormous systems and Brian could see a single bar at a time. Shrink and widen with part count.
    if n_parts > 12:
        opts['scale'] = 22
        opts['pageWidth'] = int((width or VRV['pageWidth']) * 2.2)
    elif n_parts > 6:
        opts['scale'] = 30
        opts['pageWidth'] = int((width or VRV['pageWidth']) * 1.5)
    tk.setOptions(opts)
    tk.loadData(xml_text)
    svg = tk.renderToSVG(min(page, max(tk.getPageCount(), 1)))
    if timemap:
        return svg, tk.getPageCount(), tk.renderToTimemap()
    return svg, tk.getPageCount()


def _by_measure(svg, cls):
    """{measure: [(element_id, signature)]} for a given verovio class, in document order."""
    out, cur = {}, None
    pat = (r'class="measure"[^>]*data-n="(\d+)"'
           rf'|<g id="([^"]+)" class="{cls}"([^>]*)>')
    for m in re.finditer(pat, svg):
        if m.group(1):
            cur = m.group(1)
            out.setdefault(cur, [])
        elif cur is not None:
            attrs = m.group(3) or ''
            p = re.search(r'data-pname="([a-g])"', attrs)
            o = re.search(r'data-oct="(\d)"', attrs)
            sig = (p.group(1).upper() + o.group(1)) if (p and o) else ''
            out[cur].append((m.group(2), sig))
    return out


def changed(svg_a, svg_b, measure, cls='note'):
    """(ids_in_a, ids_in_b) that differ in that measure: pitch changes, plus added/removed items."""
    a = _by_measure(svg_a, cls).get(str(measure), [])
    b = _by_measure(svg_b, cls).get(str(measure), [])
    ai, bi = [], []
    for i in range(min(len(a), len(b))):
        if a[i][1] != b[i][1]:
            ai.append(a[i][0]); bi.append(b[i][0])
    # anything ADDED (a dynamic that was not there before) or REMOVED
    for i in range(len(b) - len(a)):
        bi.append(b[len(a) + i][0])
    for i in range(len(a) - len(b)):
        ai.append(a[len(b) + i][0])
    return ai, bi


def colour(svg, ids, css):
    """Recolour specific elements. MUST be a regex: svgAdditionalAttribute injects data-* into the
    tag, so an exact-string replace silently no-ops and yields an uncoloured diff that looks fine."""
    for i in ids:
        svg = re.sub(rf'(<g id="{re.escape(i)}" class="[a-zA-Z]+"[^>]*?)color="#[0-9a-fA-F]{{6}}"'
                     rf'([^>]*?)fill="#[0-9a-fA-F]{{6}}"',
                     rf'\1color="{css}"\2fill="{css}"', svg)
        # dynamics render as <g class="dynam"> whose glyphs carry no explicit fill
        svg = re.sub(rf'<g id="{re.escape(i)}" class="(dynam|hairpin|dir)"',
                     rf'<g id="{i}" fill="{css}" color="{css}" class="\1"', svg)
    return svg


# General MIDI programs by part name. Brian's MusicXML carries NO <midi-program> elements, so
# music21 exports program 0 for every part and a 30-piece orchestra plays back as 30 pianos.
# Longest key first, so "Bass Clarinet" beats "Clarinet" and "Bass Trombone" beats "Trombone".
GM = {
    'piccolo': 72, 'alto flute': 73, 'flute': 73, 'english horn': 69, 'oboe': 68,
    'bass clarinet': 71, 'clarinet': 71, 'contrabassoon': 70, 'bassoon': 70,
    'soprano saxophone': 64, 'alto saxophone': 65, 'tenor saxophone': 66,
    'baritone saxophone': 67, 'saxophone': 65,
    'horn': 60, 'trumpet': 56, 'bass trombone': 57, 'trombone': 57, 'tuba': 58,
    'timpani': 47, 'glockenspiel': 9, 'xylophone': 13, 'vibraphone': 11, 'marimba': 12,
    'celesta': 8, 'harp': 46, 'organ': 19, 'piano': 0, 'guitar': 24,
    'violin': 40, 'viola': 41, 'violoncello': 42, 'cello': 42,
    'contrabass': 43, 'double bass': 43, 'string': 48, 'choir': 52, 'voice': 52,
}
PERCUSSION = ('cymbal', 'gong', 'tam-tam', 'snare', 'bass drum', 'percussion', 'triangle',
              'tambourine', 'woodblock', 'crash', 'drum')
_GM_KEYS = sorted(GM, key=len, reverse=True)


def assign_instruments(score):
    """Give every part a real GM program AND AN EXPLICIT MIDI CHANNEL.

    Setting only the program is not enough and produced the worst bug in the project: with 24 parts
    music21 collapsed 422 of 458 notes onto CHANNEL 0, so the whole orchestra played through one
    patch (contrabass). It rendered, it had program-change events, and it sounded like mud. Checking
    that programs EXIST is not the same as checking which channel the notes are ON.

    Parts are grouped BY PROGRAM - all flutes share a channel, all horns share a channel - which is
    musically correct and fits an orchestra into the 15 melodic channels. Channel 9 is percussion.
    """
    from music21 import instrument
    by_prog, order = {}, []
    for p in score.parts:
        name = (p.partName or p.id or '').lower()
        if any(k in name for k in PERCUSSION):
            prog = 'perc'
        else:
            prog = next((GM[k] for k in _GM_KEYS if k in name), None)
        by_prog.setdefault(prog, []).append(p)
        if prog not in order:
            order.append(prog)
    # Channel 0 is allocated LAST. Notes written on channel 0 were silently dropped by the
    # writer/reader round trip - the flutes vanished (48 of 420 notes) while every other channel
    # was perfect. Rather than debug music21's writer, keep 0 out of the common path.
    free = [c for c in range(1, 16) if c != 9] + [0]
    chan = {}
    for prog in order:
        if prog == 'perc':
            chan[prog] = 9
        elif free:
            chan[prog] = free.pop(0)
    for prog, ps in by_prog.items():
        if prog is None or prog not in chan:
            continue
        for p in ps:
            ins = instrument.Instrument()
            ins.midiProgram = 0 if prog == 'perc' else prog
            ins.midiChannel = chan[prog]
            ins.partName = p.partName
            p.insert(0, ins)
    return score


def _sounding(score):
    """MIDI MUST be written at SOUNDING pitch.

    THE WORST BUG IN THIS PROJECT. `part.recurse().notes` returns WRITTEN pitch, so every
    transposing instrument was sent to fluidsynth untransposed: clarinets and trumpets a whole tone
    sharp, horns a fifth sharp, bass clarinet a MAJOR NINTH sharp, contrabass an octave sharp. Half
    the orchestra in the wrong key, in every render this project ever produced - including Brian's
    own unaltered bars. Every "it sounds like dog shit" was partly this, and I kept looking at the
    notes I had written instead of at the pipeline that played them.
    """
    try:
        if getattr(score, 'atSoundingPitch', False) is True:
            return score
        return score.toSoundingPitch()
    except Exception:
        return score



def _bpm(score):
    """the score's own first metronome mark (quarter = N); 120 only if it has none."""
    try:
        for mm in score.recurse().getElementsByClass('MetronomeMark'):
            q = mm.getQuarterBPM()
            if q: return float(q)
    except Exception:
        pass
    return 120

def _write_midi(score, path):
    score = score.stripTies()
    """One track per part, each on its own channel with its own GM program.

    Uses our own writer (midiwrite.py) rather than music21's: music21's collapsed 422 of 458 notes
    onto a single channel so the entire orchestra played through one contrabass patch, and every
    attempt to correct it lost a part. See midiwrite.py.
    """
    import midiwrite
    score = _sounding(score)
    parts = list(score.parts)
    progs = []
    for p in parts:
        name = (p.partName or p.id or '').lower()
        if any(k in name for k in PERCUSSION):
            progs.append('perc')
        else:
            progs.append(next((GM[k] for k in _GM_KEYS if k in name), 0))
    order = []
    for pr in progs:
        if pr not in order:
            order.append(pr)
    free = [c for c in range(16) if c != 9]
    chan = {}
    for pr in order:
        chan[pr] = 9 if pr == 'perc' else (free.pop(0) if free else 15)
    return midiwrite.write(score, path,
                           [chan[pr] for pr in progs],
                           [0 if pr == 'perc' else pr for pr in progs], bpm=_bpm(score))


def audio(xml_text, out_stem):
    """Excerpt -> MIDI -> m4a -> base64 data URI, so the diff page can play it."""
    if not os.path.exists(SF):
        return None
    try:
        from music21 import converter
        d = tempfile.mkdtemp()
        mid, wav, m4a = (os.path.join(d, out_stem + e) for e in ('.mid', '.wav', '.m4a'))
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            sc = converter.parse(xml_text, format='musicxml')
            _write_midi(sc, mid)
        subprocess.run(['fluidsynth', '-ni', '-F', wav, '-r', '44100', SF, mid],
                       check=True, capture_output=True, timeout=120)
        subprocess.run(['afconvert', '-f', 'm4af', '-d', 'aac', '-b', '48000', wav, m4a],
                       check=True, capture_output=True, timeout=120)
        return 'data:audio/mp4;base64,' + base64.b64encode(open(m4a, 'rb').read()).decode()
    except Exception:
        return None


PAGE = """<style>
 :root{{--bg:#fbfaf7;--fg:#1c1a17;--line:#dcd6cc;--add:#0b8a3e;--del:#c02626;--panel:#fff}}
 @media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#16151a;--fg:#eceaf2;--line:#33313c;--panel:#1f1e25}}}}
 :root[data-theme="dark"]{{--bg:#16151a;--fg:#eceaf2;--line:#33313c;--panel:#1f1e25}}
 body{{background:var(--bg);color:var(--fg);font:14px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;margin:0;padding:22px}}
 h1{{font-size:19px;margin:0 0 2px;font-weight:600}}
 .sub{{opacity:.62;margin-bottom:20px;font-size:13px}}
 .card{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:15px 17px;margin-bottom:14px}}
 /* Side by side. Brian: "it's kinda hard, I have to scroll up and see what the red before is,
    then scroll down." Each column is engraved narrower rather than scaled down. */
 .pair{{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}}
 /* Stack only when genuinely too narrow. A 1100px breakpoint fired on a normal un-maximised
    Chrome window and silently reverted to the stacked layout it was meant to replace. */
 @media (max-width:820px){{.pair{{grid-template-columns:1fr}}}}
 .pair .card{{margin-bottom:0}}
 .hd{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
 .lbl{{font:600 11px/1 ui-monospace,Menlo,monospace;letter-spacing:.08em;text-transform:uppercase;opacity:.55}}
 /* Verovio draws in BLACK: the score keeps a light ground in BOTH themes or it is invisible. */
 .scroll{{overflow-x:auto;background:#fdfcf9;border-radius:6px;padding:8px 4px}}
 svg{{max-width:100%;height:auto}}
 .del .lbl{{color:var(--del)}} .add .lbl{{color:var(--add)}}
 .prop{{border-left:3px solid var(--add)}}
 code{{font:13px ui-monospace,Menlo,monospace;background:rgba(128,128,128,.13);padding:1px 6px;border-radius:4px}}
 audio{{height:30px;vertical-align:middle}}
 .btns{{display:flex;gap:10px;margin-top:13px;flex-wrap:wrap}}
 button{{font:600 13px inherit;padding:8px 17px;border-radius:7px;border:1px solid var(--line);cursor:pointer;background:var(--panel);color:var(--fg)}}
 .ok{{background:var(--add);border-color:var(--add);color:#fff}}
 .note{{opacity:.6;font-size:12.5px;margin-top:10px}}
 /* playback: a moving cursor line, plus a ring on the sounding notes. Deliberately NOT a recolour -
    that would fight with the red/green edit highlighting. */
 .cursor{{position:absolute;top:0;width:2px;background:#2563eb;opacity:.75;pointer-events:none;transition:left .05s linear}}
 .scroll{{position:relative}}
 g.playing{{filter:drop-shadow(0 0 3px #2563eb)}}
 /* Claude-Code-style block highlight. A recoloured notehead is far too easy to miss on a busy
    page - Brian: "I have to squint and see which notes are green versus red". */
 /* A BAND behind the whole added region, the way Claude Code shades an added line - not colour
    on individual noteheads, which is the equivalent of tinting single characters. */
 .hl{{position:absolute;border-radius:3px;pointer-events:none;z-index:0}}
 .hl.del{{background:rgba(192,38,38,.16);border-left:3px solid rgba(192,38,38,.75)}}
 .hl.add{{background:rgba(11,138,62,.16);border-left:3px solid rgba(11,138,62,.75)}}
 .scroll svg{{position:relative;z-index:1}}
 .legend{{display:inline-flex;gap:14px;align-items:center;margin-left:auto;font-size:12px;opacity:.8}}
 /* Click a staff to see why THAT instrument got what it got. Brian: "instead of a huge block of
    reasoning, an overall summary, and then I click into the highlighted parts for each instrument
    and see the reasoning for that part." */
 .why{{position:fixed;right:18px;bottom:18px;max-width:380px;background:var(--panel);
   border:1px solid var(--line);border-left:3px solid var(--add);border-radius:10px;
   padding:13px 15px;box-shadow:0 6px 24px rgba(0,0,0,.18);font-size:13px;display:none;z-index:9}}
 .why h4{{margin:0 0 6px;font-size:13px}}
 .why .close{{float:right;cursor:pointer;opacity:.5}}
 .staffrow{{cursor:pointer}}
 .staffrow:hover{{background:rgba(11,138,62,.09)}}
 .sumline{{display:flex;gap:10px;padding:3px 0;font-size:13px}}
 .sumline b{{min-width:210px}}
 .swatch{{display:inline-block;width:11px;height:11px;border-radius:3px;vertical-align:-1px;margin-right:5px}}
</style>
<h1>{title}</h1>
<div class="sub">{sub}</div>
<div class="card prop"><div class="lbl">Proposed change</div>{desc}
<div class="btns"><button class="ok">Approve</button><button>Reject</button><button>Ask for something else</button></div></div>
<div class="pair" {pair_style}>
<div class="card del" {hide_before}><div class="hd"><span class="lbl">Before</span>{audio_a}
  <span class="legend"><span><span class="swatch" style="background:rgba(192,38,38,.45)"></span>removed / replaced</span></span></div>
  <div class="scroll" data-hl='{hl_a}' data-bars='{bars_a}' data-cls="del">{before}</div></div>
<div class="card add"><div class="hd"><span class="lbl">After</span>{audio_b}
  <span class="legend"><span><span class="swatch" style="background:rgba(11,138,62,.45)"></span>added / changed</span></span></div>
  <div class="scroll" data-hl='{hl_b}' data-bars='{bars_b}' data-cls="add">{after}</div></div>
</div>
<div class="why" id="why"><span class="close" onclick="document.getElementById('why').style.display='none'">&times;</span>
<h4 id="whyTitle"></h4><div id="whyBody"></div></div>
<div class="note">Click any staff in the score to see why that instrument got what it got.
Excerpt rendered with Verovio straight from the MusicXML. No Sibelius import, no new document, no dialog.
Press play to follow along &mdash; the cursor tracks the audio.</div>
<script>
(function(){{
  // Draw a translucent block behind every changed element. Done in JS because the bounding box of
  // a glyph is only known once the SVG has been laid out by the browser.
  function drawHighlights(){{
    document.querySelectorAll('.scroll[data-hl]').forEach(function(box){{
      var ids; try{{ ids = JSON.parse(box.getAttribute('data-hl')); }}catch(e){{ return; }}
      var cls = box.getAttribute('data-cls'), svg = box.querySelector('svg');
      // NOT `if (!ids.length) return` - the per-note list is deliberately empty when a whole bar
      // is banded, and that guard returned before the band code ever ran. The bands never drew
      // once because of it.
      if(!svg) return;
      ids = ids || [];
      box.querySelectorAll('.hl').forEach(function(n){{ n.remove(); }});
      var b = box.getBoundingClientRect();
      // Measure-level BANDS first: shade the whole added bar across every staff, the way Claude
      // Code shades an added line. Colouring noteheads was the wrong metaphor - that is tinting
      // individual characters.
      var bars = [];
      try {{ bars = JSON.parse(box.getAttribute('data-bars') || '[]'); }} catch(e) {{}}
      bars.forEach(function(n){{
        var m = svg.querySelector('g.measure[data-n="' + n + '"]');
        if(!m) return;
        var r = m.getBoundingClientRect();
        if(!r.width) return;
        var d = document.createElement('div');
        d.className = 'hl ' + cls;
        d.style.left   = (r.left - b.left + box.scrollLeft) + 'px';
        d.style.top    = (r.top  - b.top  + box.scrollTop - 6) + 'px';
        d.style.width  = r.width + 'px';
        d.style.height = (r.height + 12) + 'px';
        box.appendChild(d);
      }});
      // one union box per GROUP; a group is everything that changed in one bar
      // If the whole bar is banded, per-note boxes are redundant and just make it look mottled.
      if(bars && bars.length) ids = [];
      ids.forEach(function(group){{
        if(!Array.isArray(group)) group = [group];
        var x0=null,y0=null,x1=null,y1=null;
        group.forEach(function(id){{
          var el = svg.querySelector('[id="' + id + '"]');
          if(!el) return;
          var r = el.getBoundingClientRect();
          if(!r.width && !r.height) return;
          var L = r.left - b.left + box.scrollLeft, T = r.top - b.top + box.scrollTop;
          if(x0===null){{ x0=L; y0=T; x1=L+r.width; y1=T+r.height; }}
          else {{ x0=Math.min(x0,L); y0=Math.min(y0,T);
                 x1=Math.max(x1,L+r.width); y1=Math.max(y1,T+r.height); }}
        }});
        if(x0===null) return;
        var pad = 6;
        var d = document.createElement('div');
        d.className = 'hl ' + cls;
        d.style.left   = (x0 - pad) + 'px';
        d.style.top    = (y0 - pad) + 'px';
        d.style.width  = (x1 - x0 + pad * 2) + 'px';
        d.style.height = (y1 - y0 + pad * 2) + 'px';
        box.appendChild(d);
      }});
    }});
  }}
  drawHighlights();
  window.addEventListener('resize', drawHighlights);

  // per-instrument reasoning, keyed by the part name shown on the staff
  var WHY = {why_map};
  document.querySelectorAll('.scroll svg g').forEach(function(g){{
    if(g.getAttribute('class') !== 'staff') return;
  }});
  (function(){{
    var box = document.querySelector('.scroll');
    if(!box) return;
    box.addEventListener('click', function(e){{
      var svg = box.querySelector('svg'); if(!svg) return;
      var pt = svg.createSVGPoint ? svg.createSVGPoint() : null;
      // find the nearest staff group to the click and read its label
      var best = null, bd = 1e9, r0 = box.getBoundingClientRect();
      svg.querySelectorAll('g[class="staff"]').forEach(function(st){{
        var r = st.getBoundingClientRect();
        var d = (e.clientY < r.top) ? r.top - e.clientY
              : (e.clientY > r.bottom ? e.clientY - r.bottom : 0);
        if(d < bd){{ bd = d; best = st; }}
      }});
      if(!best || bd > 40) return;
      // the instrument label is the nearest preceding <text> in the system
      var names = Object.keys(WHY), hit = null;
      var rb = best.getBoundingClientRect();
      svg.querySelectorAll('text').forEach(function(t){{
        var rt = t.getBoundingClientRect();
        if(Math.abs((rt.top+rt.bottom)/2 - (rb.top+rb.bottom)/2) < 26){{
          var s = (t.textContent||'').trim();
          names.forEach(function(n){{
            if(s && (n.indexOf(s) === 0 || s.indexOf(n) === 0)) hit = n;
          }});
        }}
      }});
      if(!hit) return;
      document.getElementById('whyTitle').textContent = hit;
      document.getElementById('whyBody').innerHTML = WHY[hit];
      document.getElementById('why').style.display = 'block';
    }});
  }})();

  var MAPS = {maps};
  document.querySelectorAll('.card').forEach(function(card){{
    var audio = card.querySelector('audio'), box = card.querySelector('.scroll');
    if(!audio || !box) return;
    var tm = MAPS[card.classList.contains('del') ? 'before' : 'after'];
    if(!tm || !tm.length) return;
    var svg = box.querySelector('svg');
    var cur = document.createElement('div');
    cur.className = 'cursor'; cur.style.display = 'none';
    box.appendChild(cur);
    var lit = [];
    function clear(){{ lit.forEach(function(e){{ e.classList.remove('playing'); }}); lit = []; }}
    function frame(){{
      if(audio.paused){{ return; }}
      var ms = audio.currentTime * 1000, i = 0;
      while(i + 1 < tm.length && tm[i+1].tstamp <= ms) i++;
      var ids = [];
      for(var k = 0; k <= i; k++){{
        (tm[k].on  || []).forEach(function(x){{ if(ids.indexOf(x) < 0) ids.push(x); }});
        (tm[k].off || []).forEach(function(x){{ var j = ids.indexOf(x); if(j >= 0) ids.splice(j,1); }});
      }}
      clear();
      var minX = null, el0 = null;
      ids.forEach(function(id){{
        var el = svg.querySelector('[id="' + id + '"]');
        if(!el) return;
        el.classList.add('playing'); lit.push(el);
        try{{
          var r = el.getBoundingClientRect(), b = box.getBoundingClientRect();
          var x = r.left - b.left + box.scrollLeft;
          if(minX === null || x < minX){{ minX = x; el0 = el; }}
        }}catch(e){{}}
      }});
      if(minX !== null){{
        cur.style.display = 'block';
        cur.style.left = minX + 'px';
        cur.style.height = box.scrollHeight + 'px';
        if(el0){{
          var r = el0.getBoundingClientRect();
          if(r.top < 80 || r.bottom > window.innerHeight - 40){{
            el0.scrollIntoView({{block:'center', behavior:'smooth'}});
          }}
        }}
      }}
      requestAnimationFrame(frame);
    }}
    audio.addEventListener('play', function(){{ requestAnimationFrame(frame); }});
    audio.addEventListener('pause', function(){{ clear(); cur.style.display='none'; }});
    audio.addEventListener('ended', function(){{ clear(); cur.style.display='none'; }});
    // only one panel plays at a time
    audio.addEventListener('play', function(){{
      document.querySelectorAll('audio').forEach(function(o){{ if(o !== audio) o.pause(); }});
    }});
  }});
}})();
</script>
"""


def build(raw, new, notes, title, context=2, with_audio=True, side_by_side=True,
          only_parts=None, max_parts=10, rationale=None):
    """notes: [(measure, description, why)]. Returns the HTML.

    `only_parts` limits the rendered staves. On a 30-part orchestral score the diff is unreadable
    otherwise - Brian: "the score is almost impossible to read". If not given, the parts that
    CHANGED are detected automatically.
    """
    ms = [m for m, _, _ in notes] or [1]
    lo, hi = max(1, min(ms) - context), max(ms) + context
    allp = xmledit.parts(raw)
    hidden = 0
    if only_parts is None and len(allp) > max_parts:
        only_parts = []
        for i, _pid, _n, _a, _b in allp:
            for m in range(lo, hi + 1):
                a_ = [b for _, b in xmledit.measure_notes(raw, m, part=i)]
                b_ = [b for _, b in xmledit.measure_notes(new, m, part=i)]
                if a_ != b_:
                    only_parts.append(i)
                    break
        hidden = len(allp) - len(only_parts)
        if not only_parts:
            only_parts = list(range(min(len(allp), max_parts)))
            hidden = len(allp) - len(only_parts)
    ex_a = xmledit.excerpt(raw, lo, hi, only_parts)
    ex_b = xmledit.excerpt(new, lo, hi, only_parts)
    # Narrower engraving for two columns. Both sides use the SAME width so the system breaks match
    # and bar N sits opposite bar N; different widths would misalign the comparison.
    w = 1150 if side_by_side else None
    npv = len(only_parts) if only_parts else len(allp)
    a, _, tm_a = render(ex_a, width=w, timemap=True, n_parts=npv)
    b, _, tm_b = render(ex_b, width=w, timemap=True, n_parts=npv)
    # Highlights are GROUPED PER MEASURE and drawn as one region. A box per notehead reads as
    # confetti - Brian: "from bar 91 to 93 that whole thing should be highlighted in green, not
    # the individual notes". One group = one union bounding box.
    hl_a, hl_b = [], []
    for m in ms:
        ga, gb = [], []
        for cls in ('note', 'dynam', 'hairpin'):
            ai, bi = changed(a, b, m, cls)
            ga += ai
            gb += bi
            a = colour(a, ai, '#c02626')
            b = colour(b, bi, '#0b8a3e')
        if ga:
            hl_a.append(ga)
        if gb:
            hl_b.append(gb)
    aa = ab = ''
    if with_audio:
        da, db = audio(ex_a, 'before'), audio(ex_b, 'after')
        if da:
            aa = f'<audio controls preload="none" src="{da}"></audio>'
        if db:
            ab = f'<audio controls preload="none" src="{db}"></audio>'
    # Group by reason. A 97-op orchestration printed 97 near-identical lines and buried the score.
    import collections as _c
    groups = _c.OrderedDict()
    for m, d, w in notes:
        inst = d.split(' - ')[0] if ' - ' in d else ''
        key = (w or d)
        g = groups.setdefault(key, {'bars': set(), 'insts': [], 'sample': d})
        g['bars'].add(m)
        if inst and inst not in g['insts']:
            g['insts'].append(inst)
    # Lead with WHY, in musical terms. The per-op list is detail and belongs behind a click -
    # Brian: "instead of a huge block of reasoning, an overall summary, and then I click into the
    # highlighted parts for each instrument."
    lead = f'<p style="font-size:14px">{rationale}</p>' if rationale else ''
    why_map = {}
    for m, d, w in notes:
        inst = d.split(' - ')[0] if ' - ' in d else ''
        if not inst:
            continue
        what = d.split(' - ', 1)[1] if ' - ' in d else d
        why_map.setdefault(inst, [])
        why_map[inst].append(f'<div style="margin:4px 0"><b>bar {m}</b> &mdash; {what}'
                             + (f'<br><span style="opacity:.75">{w}</span>' if w else '') + '</div>')
    why_map = {k: ''.join(v[:6]) for k, v in why_map.items()}
    desc = ''
    for why, g in groups.items():
        bs = sorted(g['bars'])
        span = f'bar {bs[0]}' if len(bs) == 1 else f'bars {bs[0]}&ndash;{bs[-1]}'
        who = (', '.join(g['insts'][:6]) + (f' +{len(g["insts"]) - 6} more'
                                            if len(g['insts']) > 6 else '')) if g['insts'] else ''
        head = f'{span}' + (f' &middot; {who}' if who else f' &middot; {g["sample"][:60]}')
        desc += f'<p><b>{head}</b> &mdash; {why}</p>'
    if len(notes) > len(groups):
        desc += f'<p style="opacity:.6">{len(notes)} operations, grouped by intent. '
        desc += 'Click any staff in the score below for that instrument\'s reasoning.</p>'
    desc = lead + ('<details style="margin-top:6px"><summary style="cursor:pointer;opacity:.7;'
                   'font-size:13px">what changed, part by part</summary>' + desc + '</details>'
                   if lead else desc)
    src = xmledit.diff(raw, new)
    add = sum(1 for l in src.splitlines() if l.startswith('+') and not l.startswith('+++'))
    rem = sum(1 for l in src.splitlines() if l.startswith('-') and not l.startswith('---'))
    extra = (f', showing only the {len(only_parts)} changed part(s) of {len(allp)} '
             f'({hidden} unchanged staves hidden)') if hidden else ''
    desc += (f'<p style="opacity:.7">Source diff: {add} added / {rem} removed lines. '
             f'Showing bars {lo}&ndash;{hi}{extra}.</p>')
    import json as _json
    # If the shown bars did not exist before, a "Before" panel of empty staves is noise.
    # Brian: "the before makes no sense because we're just adding measures."
    before_bars = {int(m.group(1)) for m in xmledit.MEASURE_RE.finditer(
        raw[xmledit.parts(raw)[0][3]:xmledit.parts(raw)[0][4]] if xmledit.parts(raw) else raw)}
    # Ignore the append_measures marker, which is logged against the LAST EXISTING bar and would
    # otherwise make a set of entirely-new bars look as though it touched existing music.
    written_ms = [m for m, d, _ in notes if 'append ' not in d] or ms
    appended_only = not any(m in before_bars for m in written_ms)
    hide_before = 'style="display:none"' if appended_only else ''
    pair_style = 'style="grid-template-columns:1fr"' if appended_only else ''
    if appended_only:
        hl_b = []          # the per-note boxes are redundant once the whole bar is banded
        desc += ('<p style="opacity:.7">These bars are NEW - there is nothing to compare them '
                 'against, so the whole passage is the change and nothing is highlighted.</p>')
    return PAGE.format(title=title, sub=f'Proposed edit &middot; bars {lo}&ndash;{hi}',
                       hide_before=hide_before, pair_style=pair_style,
                       desc=desc, before=a, after=b, audio_a=aa, audio_b=ab,
                       why_map=_json.dumps(why_map),
                       maps=_json.dumps({'before': tm_a, 'after': tm_b}),
                       hl_a=_json.dumps(hl_a), hl_b=_json.dumps(hl_b),
                       bars_a=_json.dumps([]), bars_b=_json.dumps(sorted(set(written_ms))))
