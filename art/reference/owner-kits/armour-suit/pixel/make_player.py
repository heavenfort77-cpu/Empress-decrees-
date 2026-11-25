#!/usr/bin/env python3
"""One self-contained page that plays every animation set from its real-size sprite sheets."""
import base64, json
def b64(p): return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
sets = [
 ('Fluid version: klad only, layered parts with eased keys', 12, 'klad_fluid/out', [('Idle', 'idle', 12), ('Walk left', 'walk_left', 12), ('Walk right', 'walk_right', 12), ('Battle stance', 'battle', 12)]),
 ('Earlier: klad frame by frame, whole steps', 6, 'klad_anim/out', [('Idle', 'idle', 4), ('Walk left', 'walk_left', 4), ('Walk right', 'walk_right', 4), ('Battle pose', 'battle', 1)]),
 ('Earlier: posed from the 3D model', 8, 'anim/out', [('Idle', 'idle', 4), ('Walk left', 'walk_left', 6), ('Walk right', 'walk_right', 6), ('Battle pose', 'battle', 1)]),
]
data = [{'title': t, 'fps': f, 'anims': [{'name': n, 'src': b64(f'{d}/{a}_sheet_1x.png'), 'frames': k} for n, a, k in an]} for t, f, d, an in sets]
html = '''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Knight 2b animations</title>
<style>body{margin:0;padding:14px;background:#7d838c;color:#14161c;font-family:system-ui,sans-serif}
h1{font-size:18px;margin:4px 0 10px}h2{font-size:15px;margin:18px 0 8px}
.row{display:flex;flex-wrap:wrap;gap:10px}.card{background:#8b919a;border-radius:10px;padding:8px;text-align:center;font-size:13px}
canvas{display:block;width:192px;height:192px;image-rendering:pixelated;image-rendering:crisp-edges}
p{font-size:13px;margin:6px 0}</style></head><body>
<h1>Knight 2b animations</h1><p>Each box plays on its own. Shown at twice real size (real size is 96 px).</p>
<div id="root"></div>
<script>
const DATA = ''' + json.dumps(data) + ''';
const root = document.getElementById('root');
for (const set of DATA) {
  const h = document.createElement('h2'); h.textContent = set.title + ' (' + set.fps + ' frames a second)'; root.appendChild(h);
  const row = document.createElement('div'); row.className = 'row'; root.appendChild(row);
  for (const a of set.anims) {
    const card = document.createElement('div'); card.className = 'card';
    const c = document.createElement('canvas'); c.width = 96; c.height = 96; const g = c.getContext('2d'); g.imageSmoothingEnabled = false;
    const label = document.createElement('div'); label.textContent = a.name + (a.frames > 1 ? ' (' + a.frames + ' frames)' : ' (1 frame)');
    card.appendChild(c); card.appendChild(label); row.appendChild(card);
    const img = new Image(); let i = 0;
    const draw = () => { g.clearRect(0, 0, 96, 96); g.drawImage(img, i * 96, 0, 96, 96, 0, 0, 96, 96); i = (i + 1) % a.frames; };
    img.onload = () => { draw(); if (a.frames > 1) setInterval(draw, 1000 / set.fps); };
    img.src = a.src;
  }
}
</script></body></html>'''
open('knight_2b_animations.html', 'w').write(html); print(len(html) // 1024, 'KB')
