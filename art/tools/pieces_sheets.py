#!/usr/bin/env python3
"""Review sheets for the PIECES round from pieces_shoot.mjs shots: every piece at close-up AND at play size on the hall floor beside
in-game art at the same scale (labelled, JPG). Usage: python3 pieces_sheets.py SHOTDIR OUTDIR"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
S, O = sys.argv[1:3]; os.makedirs(O, exist_ok=True)

def cell(path, h, crop=None, zoom=1):
    im = Image.open(path).convert('RGB')
    if crop: im = im.crop(crop)
    return im.resize((round(im.width * h / im.height), h), Image.NEAREST if zoom > 1 else Image.LANCZOS)

def sheet(name, rows, h=480):
    """rows: lists of (label, shot name, crop or None)"""
    cells = [[(l, cell(f'{S}/{p}.png', h, c, 2 if c else 1)) for l, p, c in r if os.path.exists(f'{S}/{p}.png')] for r in rows]; cells = [r for r in cells if r]
    if not cells: print('FAIL sheet', name, 'has no shots'); return
    W = max(sum(im.width for _, im in r) for r in cells); out = Image.new('RGB', (W, len(cells) * (h + 24)), (20, 20, 20)); d = ImageDraw.Draw(out)
    for j, r in enumerate(cells):
        x = 0
        for l, im in r:
            out.paste(im, (x, j * (h + 24) + 24)); d.text((x + 6, j * (h + 24) + 6), l, fill=(255, 255, 255)); x += im.width
    out.save(f'{O}/{name}.jpg', quality=86); print('sheet', name, out.size)

def box(mask_name, pad=60):
    p = f'{S}/{mask_name}.png'
    if not os.path.exists(p): return None
    m = np.asarray(Image.open(p).convert('L')) > 128
    if not m.any(): return None
    ys, xs = np.where(m); H, W = m.shape
    return (max(0, xs.min() - pad), max(0, ys.min() - pad), min(W, xs.max() + pad), min(H, ys.max() + pad))

turn = lambda i: [(f'{i} close: {n}', f'{i}_turn_{n}', None) for n in ('front', '34', 'side', 'back')]
sheet('kaymuse_close', [[('on the throne: front', 'throne_close_front', None), ('3/4', 'throne_close_34', None), ('side', 'throne_close_side', None), ('at the game pitch (40 deg)', 'throne_close_cam', None)],
                        [('bead curtain: front', 'beads_front', None), ('3/4', 'beads_34', None), ('idle t=1 s', 'beads_idle_1', None), ('idle t=3 s', 'beads_idle_3', None), ('outline', 'kaymuse_sil', None)]])
sheet('kaymuse_play', [[('PLAY SIZE: game camera 14 m, looking at the dais (suit and guard at its foot, same scale)', 'throne_play', None)],
                       [('PLAY SIZE: a player 7 m south of the throne', 'throne_approach', None)],
                       [('wide 24 m', 'throne_wide', None)]], h=720)
kb = box('mask_kaymuse_approach', 90)
sheet('kaymuse_play_crop', [[('approach framing, 2x pixels', 'throne_approach', kb), ('LOD0 / LOD1 / LOD2', 'kaymuse_lods', None)]], h=600)
for i in ('crab', 'wanderer'):
    sheet(f'{i}_close', [turn(i), [(f'{i} at the game pitch', f'{i}_top', None), ('outline', f'{i}_sil', None), ('LOD0 / LOD1 / LOD2', f'{i}_lods', None)],
                         [(f'move pose {k}', f'{i}_move_{k}', None) for k in range(4)], [(f'idle pose {k}', f'{i}_idle_{k}', None) for k in range(4)]], h=420)
sheet('small_close', [[(f'{i}: 3/4', f'{i}_turn_34', None), ('front', f'{i}_turn_front', None), ('game pitch', f'{i}_top', None), ('outline', f'{i}_sil', None), ('LODs', f'{i}_lods', None)]
                      for i in ('plate', 'leader_crown', 'mo_wall', 'decree_mark')], h=380)
sheet('play_lineup', [[('PLAY SIZE (CAM_DIST 14, 1080p): ding, mo suit + leader crown, crab, wanderer, zu guard, plate, fa suit + decree mark; mo wall behind', 'lineup_play', None)],
                      [('same on the calm stand-in floor (#7a2a1c)', 'lineup_calm', None)], [('creatures in their move clip', 'lineup_move', None)], [('wide 22 m', 'lineup_wide', None)]], h=720)
sheet('play_crops', [[(f'{i}: play size, 2x pixels', 'lineup_play', box(f'mask_{i}')) for i in ('crab', 'wanderer', 'plate')],
                     [(f'{i}: play size, 2x pixels', 'lineup_play', box(f'mask_{i}')) for i in ('leader_crown', 'decree_mark', 'mo_wall')]], h=440)
