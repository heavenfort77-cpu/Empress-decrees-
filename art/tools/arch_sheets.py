#!/usr/bin/env python3
"""Room scene sheets (W2): per room type the wide (room fit) and play (fight framing) shots side by side at the game camera, with the
draw calls and triangles the viewer counted (main pass + one shadow call per caster). Usage: python3 arch_sheets.py SHOTSDIR OUTDIR"""
import json, os, sys
from PIL import Image, ImageDraw
S, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
st = json.load(open(f'{S}/stats.json'))
rows = [('hall', ['hall_wide', 'hall_play']), ('hall_burnt', ['hall_burnt_wide', 'hall_burnt_play']), ('hall_locked', ['hall_wide', 'hall_locked_play']),
        ('court', ['court_wide', 'court_play']), ('corridor', ['corridor_wide', 'corridor_play']), ('garden', ['garden_wide', 'garden_play']),
        ('bridge', ['bridge_wide', 'bridge_play']), ('core', ['core_wide', 'core_play', 'core_up'])]
for room, shots in rows:
    w = 960; sheet = Image.new('RGB', (w * len(shots), 540 + 30), (20, 20, 20)); d = ImageDraw.Draw(sheet)
    for i, n in enumerate(shots):
        sheet.paste(Image.open(f'{S}/{n}.png').convert('RGB').resize((w, 540)), (i * w, 30))
        s = st.get(n) or {}
        d.text((i * w + 6, 8), f"{n}: {s.get('totalCalls')} calls ({s.get('calls')} main + {s.get('shadowCalls')} shadow), {s.get('totalTris')} tris, lights {s.get('lights')}", fill=(255, 255, 255))
    sheet.save(f'{O}/sheet_{room}.png')
    print(room, 'max calls', max((st.get(n) or {}).get('totalCalls', 0) for n in shots), 'max tris', max((st.get(n) or {}).get('totalTris', 0) for n in shots))
