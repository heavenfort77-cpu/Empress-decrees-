#!/usr/bin/env python3
"""SUITANIM review sheets from suitanim_shoot.mjs: per suit the contact strips (run side carried at ground speed, run front, hit, death)
and 1:1 crops of the play-size shots (fight framing 110 px/m: run, hit, death end); lineups copied. JPEG out.
Usage: python3 suitanim_sheet.py SHOTDIR OUTDIR"""
import sys, os
from PIL import Image, ImageDraw
S, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
WID = 2400
def load(p, w=None):
    if not os.path.exists(p): return Image.new('RGB', (w or 400, 200), (80, 0, 80))
    im = Image.open(p).convert('RGB')
    if w and im.width != w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    return im
n = 0
for sid in IDS:
    if not os.path.exists(f'{S}/{sid}_strip_run.png'): continue
    rows = [load(f'{S}/{sid}_strip_{k}.png', WID) for k in ('run', 'run_front', 'hit', 'death')]
    crops = []
    for k in ('run', 'hit', 'death'):
        im = load(f'{S}/{sid}_play_{k}.png'); w, h = im.size; crops.append(im.crop((w // 2 - 400, h // 2 - 260, w // 2 + 400, h // 2 + 260)))
    H = sum(r.height for r in rows) + 520 + 20 * 5
    sh = Image.new('RGB', (WID, H), (18, 13, 22)); d = ImageDraw.Draw(sh); y = 0
    for lab, r in zip(('run (side, carried at ground speed: a planted foot keeps its floor tile)', 'run (front)', 'hit', 'death'), rows):
        d.text((6, y + 4), f'{sid} {lab}', fill=(235, 235, 235)); y += 20; sh.paste(r, (0, y)); y += r.height
    d.text((6, y + 4), 'play size (FOV 50, pitch 40, 10.5 m; 1:1 crops): run, hit, death end', fill=(235, 235, 235)); y += 20
    for i, c in enumerate(crops): sh.paste(c, (i * 800, y))
    sh.save(f'{O}/{sid}_anim_sheet.jpg', quality=82); n += 1
for k in ('lineup_run', 'lineup_death'):
    if os.path.exists(f'{S}/{k}.png'): Image.open(f'{S}/{k}.png').convert('RGB').save(f'{O}/{k}.jpg', quality=85); n += 1
print('sheets', n, '->', O)
