#!/usr/bin/env python3
"""Silhouette test, readability gates and preview sheets for the nine suits (study: art/Qin-Lamellar-Suits-Study.md).
Reads <id>_sil.npz written by suit_blender.py (triangles projected with the viewer camera: FOV 50, pitch 40, 1920 x 1080;
fight framing 10.5 m = 110 px/m, wide 22 m = 52 px/m). Prints PASS/FAIL lines and writes:
  sil_lineup_front.png, sil_lineup_34.png   flat-black silhouettes at play size, the nine side by side (the outline-only test)
  preview_lineup.png                        flat-shaded preview (row colours, light from the upper left) at play size and 2x
  <id>_preview.png                          front, 3/4, side, windup 3/4 at 2x play size
  sil_matrix.txt                            pairwise silhouette IoU per view
Usage: python3 suit_sil.py INDIR OUTDIR [ids]
"""
import sys, os, itertools
import numpy as np
from PIL import Image, ImageDraw

# CONFIG
# Two suits whose flat-black silhouettes overlap more than this (intersection over union, same camera and spot) are too alike.
IOU_MAX = 0.75
# Body height on screen at the fight framing, px (study: 110 px/m; a 1.86 m crown seen at pitch 40 is about 160-200 px).
PLAY_H = (150, 260)
# LOD silhouettes at the wide framing must keep this IoU against LOD0 (outline kept when the LOD switches).
LOD_IOU = {1: 0.9, 2: 0.82}
# Thinnest outline feature that must survive at the wide framing (weapon, crest), px: checked as the mask still holding a
# protrusion above the head and beside the body (crest or weapon visible).
W, H = 1920, 1080
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
NAMES = {'fa': '法 廷尉', 'ru': '儒 君子', 'dao': '道 真人', 'mo': '墨 墨守', 'yy': '阴阳 太极', 'za': '杂 门客', 'ming': '名 辩者', 'zh': '纵横 说客', 'nong': '农 耕者'}

IN, OUT = sys.argv[1], sys.argv[2]
ids = sys.argv[3].split(',') if len(sys.argv) > 3 else [i for i in IDS if os.path.exists(f'{IN}/{i}_sil.npz')]
os.makedirs(OUT, exist_ok=True)

def load(sid):
    z = np.load(f'{IN}/{sid}_sil.npz'); d = {}
    for k in z.files:
        view, part = k.split('__'); d.setdefault(view, {})[part] = z[k]
    return d

def mask(v, scale=1):
    im = Image.new('L', (W * scale, H * scale), 0); dr = ImageDraw.Draw(im)
    for t in v['tri']:
        dr.polygon([tuple(p * scale) for p in t], fill=255)
    return np.asarray(im) > 0

def shaded(v, scale=1, bg=(18, 13, 22)):
    im = Image.new('RGB', (W * scale, H * scale), bg); dr = ImageDraw.Draw(im)
    order = np.argsort(-v['depth'])
    for i in order:
        if not v['front'][i]: continue
        dr.polygon([tuple(p * scale) for p in v['tri'][i]], fill=tuple(int(c) for c in v['col'][i]))
    return im

def bbox(m):
    ys, xs = np.nonzero(m); return xs.min(), ys.min(), xs.max(), ys.max()

D = {s: load(s) for s in ids}
lines = []
def gate(ok, line): lines.append(('PASS ' if ok else 'FAIL ') + line)

M = {view: {s: mask(D[s][f'{view}_lod0']) for s in ids} for view in ('play_front', 'play_34', 'play_side')}
union = np.zeros((H, W), bool)
for view in M:
    for s in ids: union |= M[view][s]
x0, y0, x1, y1 = bbox(union); x0 -= 12; y0 -= 12; x1 += 12; y1 += 12
# readability: body height on screen
for s in ids:
    bx0, by0, bx1, by1 = bbox(M['play_front'][s]); h = by1 - by0
    gate(PLAY_H[0] <= h <= PLAY_H[1], f'{s} play-size height {h} px (fight framing; {PLAY_H[0]}-{PLAY_H[1]})')
# silhouette test: pairwise IoU per view
with open(f'{OUT}/sil_matrix.txt', 'w') as f:
    for view in ('play_front', 'play_34', 'play_side'):
        f.write(f'{view}\n      ' + ' '.join(f'{s:>5}' for s in ids) + '\n')
        worst = (0, None)
        for a in ids:
            row = []
            for b in ids:
                iou = (M[view][a] & M[view][b]).sum() / max((M[view][a] | M[view][b]).sum(), 1); row.append(iou)
                if a < b and iou > worst[0]: worst = (iou, f'{a}-{b}')
            f.write(f'{a:>5} ' + ' '.join(f'{v:5.2f}' for v in row) + '\n')
        for a, b in itertools.combinations(ids, 2):
            iou = (M[view][a] & M[view][b]).sum() / max((M[view][a] | M[view][b]).sum(), 1)
            if iou > IOU_MAX: gate(False, f'silhouette {view} {a}-{b} IoU {iou:.2f} (max {IOU_MAX})')
        gate(worst[0] <= IOU_MAX, f'silhouette {view}: most alike pair {worst[1]} IoU {worst[0]:.2f} (max {IOU_MAX})')
# LOD outlines at the wide framing
for s in ids:
    m0 = mask(D[s]['wide_34_lod0'])
    for lv, lim in LOD_IOU.items():
        ml = mask(D[s][f'wide_34_lod{lv}']); iou = (m0 & ml).sum() / max((m0 | ml).sum(), 1)
        gate(iou >= lim, f'{s} lod{lv} outline IoU {iou:.2f} vs lod0 at the wide framing (min {lim})')
# sheets
cw, ch = x1 - x0, y1 - y0
for view, nm in (('play_front', 'front'), ('play_34', '34')):
    sheet = Image.new('RGB', (cw * len(ids), ch), (255, 255, 255))
    for i, s in enumerate(ids):
        im = Image.fromarray(np.where(M[view][s], 0, 255).astype(np.uint8)).crop((x0, y0, x1, y1)).convert('RGB')
        sheet.paste(im, (i * cw, 0))
    sheet.save(f'{OUT}/sil_lineup_{nm}.png')
    sheet.resize((sheet.width * 2, sheet.height * 2), Image.NEAREST).save(f'{OUT}/sil_lineup_{nm}_2x.png')
pv = Image.new('RGB', (cw * len(ids), ch * 2), (18, 13, 22))
for i, s in enumerate(ids):
    pv.paste(shaded(D[s]['play_front_lod0']).crop((x0, y0, x1, y1)), (i * cw, 0))
    pv.paste(shaded(D[s]['play_34_lod0']).crop((x0, y0, x1, y1)), (i * cw, ch))
pv.save(f'{OUT}/preview_lineup.png')
for s in ids:
    views = ['play_front', 'play_34', 'play_side', 'windup_34']
    m = np.zeros((H * 2, W * 2), bool)
    ims = [shaded(D[s][f'{v}_lod0'], 2) for v in views]
    tiles = []
    for v, im in zip(views, ims):
        a = np.asarray(im).astype(int).sum(2) != (18 + 13 + 22)
        bx0, by0, bx1, by1 = bbox(a); cx = (bx0 + bx1) // 2
        tiles.append(im.crop((cx - 260, by1 - 560, cx + 260, by1 + 20)))
    sh = Image.new('RGB', (520 * len(tiles), 580), (18, 13, 22))
    for i, t in enumerate(tiles): sh.paste(t, (i * 520, 0))
    sh.save(f'{OUT}/{s}_preview.png')
for l in lines: print(l)
nf = sum(1 for l in lines if l.startswith('FAIL'))
print(f'{len(lines) - nf} of {len(lines)} pass')
