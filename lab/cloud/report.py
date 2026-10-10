"""Turn the cloud training log into the run report page (inline SVG chart, both themes).
usage: python cloud/report.py <train_cloud.log> <out.html> [benchmark_block.html]"""
import re, sys, json, html

log = open(sys.argv[1]).read()
out = sys.argv[2]
bench = open(sys.argv[3]).read() if len(sys.argv) > 3 else ''

evals = [(int(a), float(b)) for a, b in re.findall(r'EVAL@(\d+): ([0-9.]+)', log)]
train = [(int(a), float(b)) for a, b in re.findall(r'e1 (\d+)/\d+ loss ([0-9.]+)', log)]
kinds_last = re.findall(r'\| (.*)$', [l for l in log.split('\n') if re.search(r'e1 \d+/\d+ loss', l)][-1])[0] if train else ''
kinds = dict(re.findall(r'(\w+):([0-9.]+)', kinds_last))
final = re.search(r'EPOCH 1: train ([0-9.]+) eval ([0-9.]+)', log)
total = int(re.search(r'e1 \d+/(\d+)', log).group(1)) if train else 0
best = min(v for _, v in evals) if evals else None
LAPTOP = 0.313

W, H, L, R, T, B = 900, 380, 64, 24, 20, 44
xmax = total or (evals[-1][0] if evals else 1)
ymin, ymax = 0.10, 0.50
def X(s): return L + (W - L - R) * s / xmax
def Y(v): return T + (H - T - B) * (ymax - v) / (ymax - ymin)
ev_path = ' '.join(f"{'M' if i == 0 else 'L'}{X(s):.1f},{Y(v):.1f}" for i, (s, v) in enumerate(evals))
tr_path = ' '.join(f"{'M' if i == 0 else 'L'}{X(s):.1f},{Y(min(v, ymax)):.1f}" for i, (s, v) in enumerate(train[3:]))
gridy = ''.join(f'<line x1="{L}" x2="{W-R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" class="grid"/><text x="{L-10}" y="{Y(v)+4:.1f}" class="tick" text-anchor="end">{v:.2f}</text>' for v in (0.1, 0.2, 0.3, 0.4, 0.5))
xt = ''.join(f'<text x="{X(s):.1f}" y="{H-B+22}" class="tick" text-anchor="middle">{s//1000}K</text>' for s in range(0, xmax + 1, 50000))
lap = f'<line x1="{L}" x2="{W-R}" y1="{Y(LAPTOP):.1f}" y2="{Y(LAPTOP):.1f}" class="ref"/><text x="{W-R}" y="{Y(LAPTOP)-6:.1f}" class="reflabel" text-anchor="end">laptop best 0.313</text>'
dots = ''.join(f'<circle cx="{X(s):.1f}" cy="{Y(v):.1f}" r="3.5" class="dot" data-s="{s}" data-v="{v:.4f}"/>' for s, v in evals)
end_ev = evals[-1] if evals else (0, 0)
end_tr = train[-1] if train else (0, 0)
rows = ''.join(f'<tr><td>{s:,}</td><td>{v:.4f}</td></tr>' for s, v in evals if s % 20000 == 0 or s == evals[-1][0])
kind_rows = ''.join(f'<tr><td>{k.replace("_", " ")}</td><td>{float(v):.3f}</td></tr>' for k, v in sorted(kinds.items(), key=lambda kv: float(kv[1])))
cost = float(sys.argv[4]) if len(sys.argv) > 4 else (3.49 * (train[-1][0] * 0.1 / 3600 + 0.4) if train else 0)

page = f'''<title>GPU Day One</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{{--bg:#f2f4f7;--bg2:#ffffff;--ink:#14181f;--ink2:#4c5563;--ink3:#7b8494;--line:#d6dbe3;--s1:#2a78d6;--s2:#eb6834;--ref:#9aa3b2;}}
@media (prefers-color-scheme: dark){{:root:not([data-theme="light"]){{--bg:#16191e;--bg2:#1e2228;--ink:#f5f6f8;--ink2:#b7bcc6;--ink3:#7f8794;--line:#2f353e;--s1:#3987e5;--s2:#d95926;--ref:#5d6572;}}}}
:root[data-theme="dark"]{{--bg:#16191e;--bg2:#1e2228;--ink:#f5f6f8;--ink2:#b7bcc6;--ink3:#7f8794;--line:#2f353e;--s1:#3987e5;--s2:#d95926;--ref:#5d6572;}}
body{{background:var(--bg);color:var(--ink);font:16px/1.55 "Source Sans 3",system-ui,sans-serif;margin:0}}
main{{max-width:960px;margin:0 auto;padding:40px 24px 64px}}
h1{{font:500 44px/1.05 Fraunces,Georgia,serif;letter-spacing:-.01em;margin:0 0 6px;text-wrap:balance}}
.sub{{color:var(--ink2);max-width:66ch;margin:0 0 28px}}
h2{{font:700 22px/1.2 Fraunces,Georgia,serif;margin:36px 0 10px}}
.eyebrow{{font:600 12px/1 "Source Sans 3",sans-serif;letter-spacing:.08em;text-transform:uppercase;color:var(--ink3)}}
.hero{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin:0 0 28px}}
.tile{{background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:16px 18px}}
.tile .n{{font:500 40px/1 "JetBrains Mono",monospace;font-variant-numeric:tabular-nums;margin:6px 0 4px}}
.tile .d{{color:var(--ink2);font-size:14px}}
figure{{margin:0;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:12px 8px 6px;position:relative;overflow-x:auto}}
svg{{display:block;width:100%;height:auto;max-width:900px;margin:0 auto}}
.grid{{stroke:var(--line);stroke-width:1}} .tick{{fill:var(--ink3);font:12px "JetBrains Mono",monospace}}
.ev{{fill:none;stroke:var(--s1);stroke-width:2;stroke-linejoin:round}} .tr{{fill:none;stroke:var(--s2);stroke-width:2;stroke-linejoin:round;opacity:.9}}
.dot{{fill:var(--s1);stroke:var(--bg2);stroke-width:2}} .ref{{stroke:var(--ref);stroke-dasharray:4 4}} .reflabel{{fill:var(--ink3);font:12px "Source Sans 3",sans-serif}}
.lbl{{font:600 13px "Source Sans 3",sans-serif;fill:var(--ink2)}}
.legend{{display:flex;gap:18px;padding:8px 12px 4px;font-size:14px;color:var(--ink2)}} .legend i{{display:inline-block;width:14px;height:3px;vertical-align:middle;margin-right:6px;border-radius:2px}}
.tip{{position:absolute;pointer-events:none;background:var(--ink);color:var(--bg);font:13px "JetBrains Mono",monospace;padding:6px 8px;border-radius:4px;display:none;white-space:nowrap}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}} td,th{{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}} td:last-child,th:last-child{{text-align:right;font-family:"JetBrains Mono",monospace;font-size:14px}}
.wrap{{overflow-x:auto}} .cfg td:last-child{{text-align:left;font-family:inherit;font-size:15px}} .small{{font-size:14px;color:var(--ink2)}} .mono{{font-family:"JetBrains Mono",monospace;font-size:14px}}
p{{max-width:68ch}}
</style>
<main>
<div class="eyebrow">Scorewright, Copilot for Composers</div>
<h1>GPU Day One</h1>
<p class="sub">One H100, one pass over 280,658 instructed-edit documents at full 32K-character context, every parameter trainable. Held-out loss is measured on 1,100 documents built from Brian's own scores that the model never trained on.</p>
<div class="hero">
  <div class="tile"><div class="eyebrow">Held-out loss, final</div><div class="n">{(float(final.group(2)) if final else end_ev[1]):.3f}</div><div class="d">on all 1,100 held-out docs{'' if final else ' (latest 300-doc sample)'}</div></div>
  <div class="tile"><div class="eyebrow">Laptop best</div><div class="n">0.313</div><div class="d">his corpus only, 7,500 steps, 6.5K-char window</div></div>
  <div class="tile"><div class="eyebrow">Cost</div><div class="n">${cost:.0f}</div><div class="d">of the $60 loaded; H100 at $3.49/h for 11 h plus storage</div></div>
</div>
<h2>Loss over the run</h2>
<figure id="fig">
<div class="legend"><span><i style="background:var(--s1)"></i>held-out eval (300-doc sample every 5K steps)</span><span><i style="background:var(--s2)"></i>training loss (running mean)</span></div>
<svg viewBox="0 0 {W} {H}" role="img" aria-label="Held-out and training loss versus step">
{gridy}{xt}{lap}
<path d="{tr_path}" class="tr"/>
<path d="{ev_path}" class="ev"/>
{dots}
<text x="{X(end_ev[0])-6:.1f}" y="{Y(end_ev[1])+18:.1f}" class="lbl" text-anchor="end">eval {end_ev[1]:.3f}</text>
<text x="{X(end_tr[0])-6:.1f}" y="{Y(min(end_tr[1], ymax))-12:.1f}" class="lbl" text-anchor="end">train {end_tr[1]:.3f}</text>
<text x="{(L+W-R)/2:.0f}" y="{H-4}" class="tick" text-anchor="middle">step</text>
</svg>
<div class="tip" id="tip"></div>
</figure>
<p class="small" style="margin-top:10px">Eval fell at every 5K-step checkpoint for the first 40K steps, then kept descending in a noisy band. It passed the laptop's best by step 10K and roughly halved it by the end. The curve had not flattened when the pass ended.</p>
<div class="cols">
<div><h2>Held-out eval, every 20K steps</h2><div class="wrap"><table><tr><th>step</th><th>eval loss</th></tr>{rows}</table></div></div>
<div><h2>Training loss by task, end of run</h2><div class="wrap"><table><tr><th>task</th><th>loss</th></tr>{kind_rows}</table></div>
<p class="small">Copy-with-transformation tasks (doubling, harmony fill) are easy; writing new material (continue, infill) stays hardest, about three times the loss of a doubling.</p></div>
</div>
{bench}
<h2>Run configuration</h2>
<table class="cfg">
<tr><td>Model</td><td>Text2Score decoder (NotaGen architecture) + ModernBERT instruction encoder, 232M trainable</td></tr>
<tr><td>Data</td><td>PDMX 172K edits + 60K markings, OpenScore 15K, Brian's 8K x3 + 5.8K marks x2</td></tr>
<tr><td>Tasks</td><td>continue, infill, doubling, harmony fill, dynamics, articulation, pedal</td></tr>
<tr><td>Context</td><td>2,048 patches (32K chars); loss on the answer only</td></tr>
<tr><td>Optimizer</td><td>AdamW, lr 5e-5, grad accumulation 4, one pass</td></tr>
<tr><td>Machine</td><td>RunPod secure cloud, NVIDIA H100 80GB, $3.49/h</td></tr>
</table>
</main>
<script>
(function(){{
 var ev={json.dumps(evals)}; var fig=document.getElementById('fig'); var svg=fig.querySelector('svg'); var tip=document.getElementById('tip');
 var L={L},R={R},W={W},xmax={xmax};
 svg.addEventListener('mousemove',function(e){{
   var r=svg.getBoundingClientRect(); var x=(e.clientX-r.left)*W/r.width; var s=(x-L)/(W-L-R)*xmax;
   var best=null,bd=1e18; for(var i=0;i<ev.length;i++){{var d=Math.abs(ev[i][0]-s); if(d<bd){{bd=d;best=ev[i];}}}}
   if(!best){{return;}} tip.style.display='block'; tip.textContent='step '+best[0].toLocaleString()+'  eval '+best[1].toFixed(4);
   tip.style.left=(e.clientX-fig.getBoundingClientRect().left+12)+'px'; tip.style.top=(e.clientY-fig.getBoundingClientRect().top-10)+'px';
 }});
 svg.addEventListener('mouseleave',function(){{tip.style.display='none';}});
}})();
</script>
'''
open(out, 'w').write(page)
print('REPORT', out, 'evals', len(evals), 'best', best)
