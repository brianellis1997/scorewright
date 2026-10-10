"""Show ONE score with a bar range marked as new, plus audio. No diff.

Diffing the NotaGen output against the original is meaningless: the ABC round trip drops the
percussion staves, so the original has 30 parts and the output has 24, and comparing them by index
lines Violin I up against a completely different instrument. Everything from bar 17 on is new
anyway, so mark that range and render the score itself.
"""
import json, re, sys, diffview, xmledit


def bar_seconds(xml_text, lo, hi):
    """Start time of each bar within the rendered excerpt, so a click can seek to it.

    The audio is the EXCERPT, not the whole piece, so bar `lo` is at t=0. Opening the standalone
    m4a instead played from bar 1 and then let Music.app autoplay Brian's library.
    """
    from music21 import converter
    s = converter.parse(xmledit.excerpt(xml_text, lo, hi, None))
    mm = s.recurse().getElementsByClass('MetronomeMark')
    bpm = mm[0].number if mm else 120
    out, t = [], 0.0
    for m in s.parts[0].getElementsByClass('Measure'):
        out.append((m.number, round(t, 3)))
        t += float(m.barDuration.quarterLength) / bpm * 60
    return out


def build(xml_text, first, last, new_from, title, rationale='', context=3, max_parts=14,
          want=None):
    lo, hi = max(1, first), last
    allp = xmledit.parts(xml_text)
    if want:
        keep = [i for i, _p, n, _a, _b in allp if n in want]
        ex = xmledit.excerpt(xml_text, lo, hi, keep)
        svg, _, tm = diffview.render(ex, width=1500, timemap=True, n_parts=len(keep))
        au = diffview.audio(xmledit.excerpt(xml_text, lo, hi, None), 'showcase')
        names = [n for i, _p, n, _a, _b in allp if i in keep]
        return TPL.replace('__TITLE__', title).replace('__SVG__', svg) \
            .replace('__AUDIO__', au or '').replace('__RAT__', rationale) \
            .replace('__BARS__', json.dumps(list(range(new_from, hi + 1)))) \
            .replace('__PARTS__', ', '.join(names)).replace('__HID__', str(len(allp) - len(keep))) \
            .replace('__SEEK__', json.dumps(bar_seconds(xml_text, lo, hi))) \
            .replace('__RANGE__', f'{lo}\u2013{hi}')
    # keep the parts that actually PLAY in the new bars, so 24 staves do not become unreadable
    keep = []
    for i, _pid, _n, _a, _b in allp:
        for m in range(new_from, hi + 1):
            if [b for _, b in xmledit.measure_notes(xml_text, m, part=i)]:
                keep.append(i); break
    if not keep or len(keep) > max_parts:
        keep = (keep or [i for i, *_ in allp])[:max_parts]
    hidden = len(allp) - len(keep)
    ex = xmledit.excerpt(xml_text, lo, hi, keep)
    svg, _, tm = diffview.render(ex, width=1500, timemap=True, n_parts=len(keep))
    au = diffview.audio(ex, 'showcase')
    names = [n for i, _p, n, _a, _b in allp if i in keep]
    bands = list(range(new_from, hi + 1))
    return TPL.replace('__TITLE__', title).replace('__SVG__', svg) \
        .replace('__AUDIO__', au or '').replace('__RAT__', rationale) \
        .replace('__BARS__', json.dumps(bands)).replace('__PARTS__', ', '.join(names)) \
        .replace('__HID__', str(hidden)).replace('__SEEK__', json.dumps(bar_seconds(xml_text, lo, hi))) \
        .replace('__RANGE__', f'{lo}\u2013{hi}')


TPL = r'''<!doctype html><meta charset=utf-8><title>__TITLE__</title>
<style>
 body{margin:0;background:#0d1117;color:#c9d1d9;font:14px/1.55 -apple-system,BlinkMacSystemFont,sans-serif}
 header{padding:18px 26px;border-bottom:1px solid #21262d;position:sticky;top:0;background:#0d1117;z-index:9}
 h1{margin:0 0 4px;font-size:17px;font-weight:600;color:#e6edf3}
 .sub{color:#8b949e;font-size:12px}
 .rat{margin:14px 26px;padding:14px 18px;background:#161b22;border-left:3px solid #2ea043;border-radius:4px;max-width:1100px}
 .wrap{position:relative;margin:10px 26px 60px;background:#fff;border-radius:6px;overflow:auto}
 svg{display:block}
 audio{width:400px;height:32px;vertical-align:middle}
 .play{display:flex;align-items:center;gap:10px;margin-top:10px;flex-wrap:wrap}
 .from{color:#8b949e;font-size:12px}
 #jump button{background:#21262d;color:#c9d1d9;border:1px solid #30363d;border-radius:5px;
   padding:3px 9px;margin-right:5px;font:12px ui-monospace,Menlo,monospace;cursor:pointer}
 #jump button:hover{background:#30363d;border-color:#8b949e}
 #jump button.new{border-color:#2ea043;color:#7ee2a8}
 .panel{margin:14px 26px;padding:14px 18px;background:#161b22;border:1px solid #30363d;border-radius:8px;max-width:1100px}
 .q{font-weight:600;color:#e6edf3;margin-bottom:9px}
 .btn{border:1px solid #30363d;border-radius:6px;padding:6px 16px;margin-right:8px;font:600 13px -apple-system,sans-serif;cursor:pointer}
 .ok{background:#1f6f3f;color:#eafff1;border-color:#2ea043}
 .no{background:#6f2020;color:#ffecec;border-color:#c02626}
 .go{background:#21262d;color:#c9d1d9}
 .btn:hover{filter:brightness(1.25)}
 .state{margin-left:10px;color:#7ee2a8;font-size:12px}
 .reply{margin-top:12px;padding:12px 14px;background:#0d1117;border:1px solid #30363d;
   border-left:3px solid #58a6ff;border-radius:6px;color:#c9d1d9;line-height:1.55}
 .reply b{color:#e6edf3}
 .ask{margin-top:12px;display:flex;gap:8px;align-items:flex-start}
 textarea{flex:1;background:#0d1117;color:#c9d1d9;border:1px solid #30363d;border-radius:6px;padding:8px;font:13px -apple-system,sans-serif;resize:vertical}
 .legend{display:inline-block;width:11px;height:11px;background:#2ea043;opacity:.22;border:1px solid #2ea043;vertical-align:-1px;margin-right:5px}
</style>
<header>
 <h1>__TITLE__</h1>
 <div class=sub><span class=legend></span>green = written by the model &nbsp;·&nbsp; staves shown: __PARTS__ &nbsp;·&nbsp; __HID__ silent staves hidden</div>
 <div class=play>
   <audio id=a controls src="__AUDIO__"></audio>
   <span class=from>play from bar</span><span id=jump></span>
 </div>
 <div class=sub style="margin-top:6px">audio is bars __RANGE__ only, all 24 parts &mdash; not the whole piece</div>
</header>
<div class=rat>__RAT__</div>
<div class=panel>
  <div class=q>Keep these bars?</div>
  <button class="btn ok" onclick="sw('accept')">Accept</button>
  <button class="btn no" onclick="sw('reject')">Reject</button>
  <span id=state class=state></span>
  <div id=reply class=reply hidden></div>
  <div class=ask>
    <textarea id=msg rows=2 placeholder="or tell me what to do instead - e.g. don't end here, develop the motif for 8 more bars"></textarea>
    <button class="btn go" onclick="sw('prompt', document.getElementById('msg').value)">Send</button>
  </div>
</div>
<div class=wrap id=w>__SVG__</div>
<script>
// Draw ONE green band per NEW measure, behind the notation. Measure-level, not per notehead:
// Claude Code highlights the changed block, not individual letters.
(function(){
 var bars=__BARS__, svg=document.querySelector('#w svg');
 if(!svg) return;
 var ns='http://www.w3.org/2000/svg', n=0;
 bars.forEach(function(bn){
   document.querySelectorAll('#w g.measure[data-n="'+bn+'"]').forEach(function(m){
     var b; try{ b=m.getBBox(); }catch(e){ return; }
     if(!b || !b.width) return;
     // Insert into the MEASURE'S OWN PARENT, immediately before it. getBBox() reports
     // coordinates in the element's own user space; verovio nests its content inside an inner
     // <svg class="definition-scale"> with its own viewBox, so a rect appended to the OUTER
     // <svg> lands in a different coordinate system entirely - drawn, sized, and invisible.
     // That is why the previous version reported 3 rects and showed no green at all.
     var r=document.createElementNS(ns,'rect');
     r.setAttribute('x', b.x-40); r.setAttribute('y', b.y-200);
     r.setAttribute('width', b.width+80); r.setAttribute('height', b.height+400);
     r.setAttribute('fill','#2ea043'); r.setAttribute('opacity','0.17');
     m.parentNode.insertBefore(r, m);
     n++;
   });
 });
 window.__bands=n;
 // The decision channel. The page cannot write files, but Chrome runs with remote debugging on
 // 9222, so Scorewright reads this key back over CDP. Browser-based, so it works the same no
 // matter which notation program the score is open in - no Sibelius plugin, nothing to rot.
 window.sw=function(action, text){
   var rec={action:action, text:text||'', bars:bars, at:new Date().toISOString(), seq:Date.now()};
   try{ localStorage.setItem('scorewright_action', JSON.stringify(rec)); }catch(e){}
   document.title='SW:'+action+' | '+document.title.replace(/^SW:[^|]*\| /,'');
   var s=document.getElementById('state');
   if(s) s.textContent = action==='prompt' ? 'sent, Scorewright is reading it'
                                           : action+'ed - Scorewright is reading it';
 };
 // click a bar number to hear from THAT bar. Bar `lo` is t=0 in this audio because the clip is
 // the excerpt, not the piece.
 var seek=__SEEK__, au=document.getElementById('a'), jw=document.getElementById('jump');
 seek.forEach(function(p){
   var btn=document.createElement('button');
   btn.textContent=p[0];
   if(bars.indexOf(p[0])>=0) btn.className='new';
   btn.onclick=function(){ au.currentTime=p[1]; au.play(); };
   jw.appendChild(btn);
 });
})();
</script>'''
