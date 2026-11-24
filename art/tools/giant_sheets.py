#!/usr/bin/env python3
"""Review sheets and silhouette gates for the twelve bronze giants, from giant_shoot.mjs 'full' shots.
Usage: python3 giant_sheets.py SHOTDIR OUTDIR
Writes: lineup_awake.png, lineup_dormant.png, lineup_slam_windup.png, sil_lineup.png (flat black, fight framing), sil_lineup_wide_lod2.png
(flat black, wide framing, LOD2), giant_NN.png (per giant: play awake, dormant, 3/4, back, slam windup), clips_g00.png, lods_g00.png.
Gates (printed PASS/FAIL, 'N of M pass'): pairwise silhouette IoU of the twelve at the fight framing (whole figure, and the top region where
the head, beam and most motifs are) and at the wide framing on LOD2; LOD2 keeps LOD0's wide silhouette (IoU with LOD0).
Same camera and position for every giant, so the masks compare pixel for pixel.
"""
import sys, os, json, itertools
import numpy as np
from PIL import Image, ImageDraw

D, O = sys.argv[1], sys.argv[2]
os.makedirs(O, exist_ok=True)
# Gate thresholds: twelve distinct figures on one shared body (task: not recolours). Whole figure max pairwise IoU, top region max IoU,
# wide LOD2 top region max IoU; LOD2 vs LOD0 wide silhouette min IoU.
IOU_FULL, IOU_TOP, IOU_TOP_WIDE, IOU_LOD = 0.92, 0.8, 0.85, 0.8
NAMES = ['Han a', 'Han b', 'Zhao a', 'Zhao b', 'Wei a', 'Wei b', 'Chu a', 'Chu b', 'Yan a', 'Yan b', 'Qi a', 'Qi b']
G = [i for i in range(12) if os.path.exists(f'{D}/g{i:02d}_play_awake.png')]

def mask(f): return np.asarray(Image.open(f).convert('L')) < 128

def bbox(ms):
    u = np.zeros_like(ms[0])
    for m in ms: u |= m
    ys, xs = np.where(u); return xs.min(), ys.min(), xs.max(), ys.max()

def tiles(files, labels, box, tw, cols, out, pad=8):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; th = int(tw * h / w)
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (tw + pad) + pad, rows * (th + 24 + pad) + pad), (24, 20, 28)); d = ImageDraw.Draw(sheet)
    for k, (f, lab) in enumerate(zip(files, labels)):
        if not os.path.exists(f): continue
        im = Image.open(f).convert('RGB').crop(box).resize((tw, th), Image.LANCZOS)
        x, y = pad + (k % cols) * (tw + pad), pad + (k // cols) * (th + 24 + pad)
        sheet.paste(im, (x, y + 24)); d.text((x + 4, y + 6), lab, fill=(235, 225, 200))
    sheet.save(f'{O}/{out}')

fails = checks = 0
def gate(ok, line):
    global fails, checks
    checks += 1; fails += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + line)

lab = [f'{i:02d} {NAMES[i]}' for i in G]
# fight framing silhouettes
sil = {i: mask(f'{D}/g{i:02d}_sil.png') for i in G}
x0, y0, x1, y1 = bbox(list(sil.values())); m = 30
box = (max(0, x0 - m), max(0, y0 - m), x1 + m, y1 + m)
tiles([f'{D}/g{i:02d}_sil.png' for i in G], lab, box, 300, 6, 'sil_lineup.png')
for name in ('play_awake', 'play_dormant', 'slam_windup'):
    tiles([f'{D}/g{i:02d}_{name}.png' for i in G], lab, box, 300, 6, f'lineup_{name.replace("play_", "")}.png')
ytop = y0 + int((y1 - y0) * 0.42)  # head, beam, shoulders and most motifs sit in the top 42% of the figure at this framing
def iou(a, b): return (a & b).sum() / max(1, (a | b).sum())
pairs = list(itertools.combinations(G, 2))
full = {(a, b): iou(sil[a], sil[b]) for a, b in pairs}
top = {(a, b): iou(sil[a][:ytop], sil[b][:ytop]) for a, b in pairs}
fa, fb = max(full, key=full.get); ta, tb = max(top, key=top.get)
gate(full[(fa, fb)] <= IOU_FULL, f'whole silhouette most alike pair {fa:02d}-{fb:02d} IoU {full[(fa, fb)]:.3f} (max {IOU_FULL}); mean {np.mean(list(full.values())):.3f}')
gate(top[(ta, tb)] <= IOU_TOP, f'top region (head, beam, motif) most alike pair {ta:02d}-{tb:02d} IoU {top[(ta, tb)]:.3f} (max {IOU_TOP}); mean {np.mean(list(top.values())):.3f}')
# wide framing, LOD2 vs LOD0
if all(os.path.exists(f'{D}/g{i:02d}_sil_wide_lod2.png') for i in G):
    w2 = {i: mask(f'{D}/g{i:02d}_sil_wide_lod2.png') for i in G}
    x0, y0, x1, y1 = bbox(list(w2.values())); m = 16; wbox = (max(0, x0 - m), max(0, y0 - m), x1 + m, y1 + m)
    tiles([f'{D}/g{i:02d}_sil_wide_lod2.png' for i in G], lab, wbox, 200, 6, 'sil_lineup_wide_lod2.png')
    tiles([f'{D}/g{i:02d}_wide_lod2.png' for i in G], lab, wbox, 200, 6, 'lineup_wide_lod2.png')
    yt = y0 + int((y1 - y0) * 0.42)
    tw = {(a, b): iou(w2[a][:yt], w2[b][:yt]) for a, b in pairs}; wa, wb = max(tw, key=tw.get)
    gate(tw[(wa, wb)] <= IOU_TOP_WIDE, f'wide LOD2 top region most alike pair {wa:02d}-{wb:02d} IoU {tw[(wa, wb)]:.3f} (max {IOU_TOP_WIDE})')
    if all(os.path.exists(f'{D}/g{i:02d}_sil_wide.png') for i in G):
        lo = {i: iou(w2[i], mask(f'{D}/g{i:02d}_sil_wide.png')) for i in G}; k = min(lo, key=lo.get)
        gate(lo[k] >= IOU_LOD, f'LOD2 keeps the LOD0 silhouette at the wide framing: lowest IoU {lo[k]:.3f} (giant {k:02d}; min {IOU_LOD})')
# per-giant sheets
for i in G:
    p = f'{D}/g{i:02d}'; ims = []
    for f, crop in ((f'{p}_play_awake.png', box), (f'{p}_play_dormant.png', box), (f'{p}_slam_windup.png', box), (f'{p}_turn_34.png', None), (f'{p}_turn_back.png', None)):
        if os.path.exists(f):
            im = Image.open(f).convert('RGB'); im = im.crop(crop) if crop else im; ims.append(im.resize((int(420 * im.width / im.height), 420)))
    sh = Image.new('RGB', (sum(im.width for im in ims) + 8 * (len(ims) + 1), 460), (24, 20, 28)); x = 8
    for im in ims: sh.paste(im, (x, 32)); x += im.width + 8
    ImageDraw.Draw(sh).text((10, 10), f'giant {i:02d} {NAMES[i]}: awake (brass) | dormant (patina) | slam windup 1.0 s | 3/4 | back', fill=(235, 225, 200))
    sh.save(f'{O}/giant_{i:02d}.png')
# clips and LODs of giant 0
cl = sorted([f for f in os.listdir(D) if f.startswith(f'g{G[0]:02d}_clip_')], key=lambda f: (f.split('_')[2], float(f.split('_')[3][:-4])))
if cl: tiles([f'{D}/{f}' for f in cl], [f[4:-4].replace('clip_', '') for f in cl], box, 300, 6, f'clips_g{G[0]:02d}.png')
lods = [f'{D}/g{G[0]:02d}_lod{l}.png' for l in (0, 1, 2)]
if all(os.path.exists(f) for f in lods): tiles(lods, ['LOD0', 'LOD1', 'LOD2'], (0, 0, 640, 640), 400, 3, f'lods_g{G[0]:02d}.png')
info = json.load(open(f'{D}/shots.json')) if os.path.exists(f'{D}/shots.json') else {}
print('draw info (three.js, one giant + floor + boxes):', {k: v for k, v in info.items() if k.endswith('_play_awake')} if info else 'none')
print(f'{checks - fails} of {checks} pass')
