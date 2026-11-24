#!/usr/bin/env python3
"""Review sheets from the viewer shots (suit_shoot.mjs): per suit one sheet (front, 3/4, side, back | windup, strike, LODs | passes
sil, flat, shade, tex), labelled; plus the lineups copied. Usage: python3 suit_sheet.py SHOTDIR OUTDIR"""
import sys, os
from PIL import Image, ImageDraw
S, O = sys.argv[1], sys.argv[2]; os.makedirs(O, exist_ok=True)
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
def tile(p, w=320, h=320):
    if not os.path.exists(p): return Image.new('RGB', (w, h), (80, 0, 80))
    im = Image.open(p).convert('RGB'); im.thumbnail((w, h)); t = Image.new('RGB', (w, h), (18, 13, 22)); t.paste(im, ((w - im.width) // 2, (h - im.height) // 2)); return t
for sid in IDS:
    if not os.path.exists(f'{S}/{sid}_front.png'): continue
    rows = [['front', '34', 'side', 'back'], ['windup', 'strike', 'pass_sil', 'pass_flat'], ['pass_shade', '34']]
    sh = Image.new('RGB', (4 * 320, 3 * 336 + 330), (18, 13, 22)); d = ImageDraw.Draw(sh)
    for r, names in enumerate(rows):
        for c, n in enumerate(names):
            sh.paste(tile(f'{S}/{sid}_{n}.png'), (c * 320, r * 336 + 16)); d.text((c * 320 + 6, r * 336 + 2), n, fill=(230, 230, 230))
    lods = Image.open(f'{S}/{sid}_lods.png').convert('RGB') if os.path.exists(f'{S}/{sid}_lods.png') else Image.new('RGB', (1280, 640))
    lods.thumbnail((640, 320)); sh.paste(lods, (640, 2 * 336 + 16)); d.text((646, 2 * 336 + 2), 'LOD0 / LOD1 / LOD2', fill=(230, 230, 230))
    play = Image.open(f'{S}/{sid}_play.png').convert('RGB'); w, h = play.size; crop = play.crop((w // 2 - 640, h // 2 - 165, w // 2 + 640, h // 2 + 165))
    sh.paste(crop, (0, 3 * 336)); d.text((6, 3 * 336 + 4), 'fight framing 110 px/m (1:1 crop)', fill=(230, 230, 230))
    sh.save(f'{O}/{sid}_sheet.png')
for n in ('lineup_play', 'lineup_wide', 'lineup_sil_front', 'lineup_sil_34'):
    if os.path.exists(f'{S}/{n}.png'): Image.open(f'{S}/{n}.png').save(f'{O}/{n}.png')
print('sheets', O)
