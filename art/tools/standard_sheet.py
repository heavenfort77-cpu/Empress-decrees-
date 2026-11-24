#!/usr/bin/env python3
"""Review sheets for the C12 school standard (art tool). From the viewer shots (art/tools/shoot_viewer.mjs OUT standard sheet=brass):
  standard_play_sheet.png : the nine standards at the play camera (lineup), the nine banner crops enlarged under it with the school names,
                            and the sway frames (t = 0, 0.5, 1.0, 1.5 s) beside the single play shot;
  standard_detail_sheet.png: turns, passes and LODs.
Usage: python3 standard_sheet.py SHOTDIR OUTDIR
"""
import os, sys
from PIL import Image, ImageDraw

D, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
NAMES = ['ru', 'dao', 'fa', 'mo', 'yinyang', 'za', 'ming', 'zongheng', 'nong']
op = lambda n: Image.open(os.path.join(D, n)).convert('RGB')
BG = (24, 20, 26)

line = op('lineup.png')
crops = [op(f'crop_{n}.png') for n in NAMES if os.path.exists(os.path.join(D, f'crop_{n}.png'))]
ch = 300
crops = [c.resize((max(1, round(c.width * ch / c.height)), ch), Image.NEAREST) for c in crops]
cw = sum(c.width for c in crops) + 12 * len(crops)
sway = [op(f'sway_{t}.png').resize((320, 320)) for t in ('0', '0.5', '1', '1.5')]
W = max(1920, cw); sheet = Image.new('RGB', (W, 1080 + 40 + ch + 40 + 340), BG); g = ImageDraw.Draw(sheet)
sheet.paste(line, (0, 0)); g.text((10, 8), 'C12 school standards at the play camera (FOV 50, pitch 40, 10.5 m), brass sheet; player box right', fill=(230, 220, 200))
x = 0
for n, c in zip(NAMES, crops):
    sheet.paste(c, (x, 1120)); g.text((x + 2, 1100), f'{n} (play crop, enlarged, nearest)', fill=(230, 220, 200)); x += c.width + 12
y = 1120 + ch + 30
play = op('play.png').resize((569, 320)); sheet.paste(play, (0, y)); g.text((4, y - 18), 'play: standard (ru) beside the player box', fill=(230, 220, 200))
for i, (t, s) in enumerate(zip(('0', '0.5', '1.0', '1.5'), sway)):
    sheet.paste(s, (600 + i * 330, y)); g.text((600 + i * 330, y - 18), f'idle sway t={t} s (2.0 s loop)', fill=(230, 220, 200))
sheet.save(os.path.join(O, 'standard_play_sheet.png'))

names = ['turn_front', 'turn_34', 'turn_side', 'turn_back', 'pass_sil', 'pass_flat', 'pass_shade', 'pass_tex']
tiles = [op(n + '.png').resize((400, 400)) for n in names]
lods = op('lods.png'); wide = op('wide_lineup.png').resize((960, 540))
det = Image.new('RGB', (1640, 840 + 30 + max(540, lods.height)), BG); g = ImageDraw.Draw(det)
for i, (n, t) in enumerate(zip(names, tiles)):
    det.paste(t, ((i % 4) * 410, (i // 4) * 420 + 20)); g.text(((i % 4) * 410 + 4, (i // 4) * 420 + 2), n, fill=(230, 220, 200))
yy = 870; det.paste(wide, (0, yy)); g.text((4, yy - 16), 'wide camera (22 m), nine standards', fill=(230, 220, 200))
det.paste(lods.resize((660, 330)), (975, yy)); g.text((975, yy - 16), 'LOD0 (skinned), LOD1, LOD2', fill=(230, 220, 200))
det.save(os.path.join(O, 'standard_detail_sheet.png'))
print('sheets', os.listdir(O))
