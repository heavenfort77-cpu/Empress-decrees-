#!/usr/bin/env python3
"""SUITS fa round 5: side by side at the same scale with the owner's armour-suit kit (cocolito: measure reference and result the same way).
Kit figures (sheet_knight / sheet_rogue front views, 3D renders, perspective, read on a 5% ruler) and the new and round-4 fa front views
(fa_shoot.mjs turn yaw 0) are masked by background difference (kit) or the silhouette pass (fa), scaled to the same figure height and
placed on one baseline with a 5% ruler; a play-size row puts the kit figures at 110 px/m (1.9 m tall, kit HANDOFF) beside the 1:1 fa crops.
Measures per figure (same code for all): shoulder span / height, figure luminance P10/P50/P90, dark (< 40) and bright (> 200) shares,
k-means colours. Heads tall: kit read by eye on the ruler (labelled), fa from the mesh (fa_r5_metrics.json).
Runs locally (light PIL work; the kit images are the owner's uploads and are not in the repo). Usage:
python3 fa_compare.py KITDIR SHOTDIR METRICS.json OUTDIR"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

K, S, MJ, O = sys.argv[1:5]; os.makedirs(O, exist_ok=True)
# CONFIG
# Kit front-view boxes in the sheet images (x0, y0, x1, y1 = sole line, read on the ruler), background colour, by-eye head and heads tall.
KIT = {'kit knight': ('sheet_knight.png', (90, 20, 450, 586), (125, 131, 140), 'by eye: crown y68, mask chin y140, sole y585 -> 7.2 heads'),
       'kit rogue': ('sheet_rogue.png', (100, 20, 440, 562), (125, 131, 140), 'by eye: hood top y42, mask chin y130, sole y560 -> 6.7 heads (hood)')}
# Shown figure height on the close-up row, px; kit height in metres (kit HANDOFF: about 1.9 m); fight framing px per metre.
FIG_H, KIT_M, PPM = 560, 1.9, 110
M = json.load(open(MJ))

def kmeans(px, k=6, it=12, seed=1):
    rng = np.random.default_rng(seed); c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(it):
        a = ((px[:, None] - c[None]) ** 2).sum(-1).argmin(1)
        c = np.array([px[a == j].mean(0) if (a == j).any() else c[j] for j in range(k)])
    return c, np.bincount(a, minlength=k) / len(a)

def measure(img, m):
    ys, xs = np.where(m); h = ys.max() - ys.min() + 1; top = ys.min()
    widths = [(np.where(m[y])[0].ptp() + 1) if m[y].any() else 0 for y in range(top, top + int(h * 0.4))]
    px = img[ndimage.binary_erosion(m, iterations=1)].astype(np.float32); lum = px @ np.array([0.299, 0.587, 0.114])
    c, sh = kmeans(px[::max(1, len(px) // 5000)])
    return dict(h_px=int(h), span_over_h=round(max(widths) / h, 3), p10=round(float(np.percentile(lum, 10))), p50=round(float(np.median(lum))),
                p90=round(float(np.percentile(lum, 90))), dark=round(float((lum < 40).mean()), 3), bright=round(float((lum > 200).mean()), 3),
                colours=[('#%02x%02x%02x' % tuple(int(v) for v in cc), round(float(s), 2)) for cc, s in sorted(zip(c, sh), key=lambda t: -t[1])])

figs = []
for name, (f, box, bg, note) in KIT.items():
    im = np.asarray(Image.open(os.path.join(K, f)).convert('RGB'))[box[1]:box[3], box[0]:box[2]]
    m = np.abs(im.astype(int) - np.array(bg)).sum(2) > 30
    m = ndimage.binary_opening(m, iterations=1); lab, n = ndimage.label(m); big = np.argmax(np.bincount(lab.ravel())[1:]) + 1; m = lab == big
    figs.append((name, im, m, note))
for tag, d in (('fa round 5 (new)', S), ('fa round 4 (rejected)', os.path.join(S, 'old'))):
    im = np.asarray(Image.open(f'{d}/fa_front.png').convert('RGB')); m = np.asarray(Image.open(f'{d}/fa_sil_front.png').convert('L')) < 128
    note = f"mesh: {M['heads']} heads (helmet top {M['helm_top']:.2f} m, mask chin {M['mask_chin']:.2f} m)" if 'new' in tag else 'round 4 by eye: 6.4 heads (brief)'
    figs.append((tag, im, m, note))
res = {}
cols = []
for name, im, m, note in figs:
    r = measure(im, m); r['heads_note'] = note; res[name] = r
    ys, xs = np.where(m); crop = Image.fromarray(im[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    k = FIG_H / crop.height; cols.append((name, crop.resize((max(1, round(crop.width * k)), FIG_H), Image.LANCZOS), r))
W = sum(c[1].width for c in cols) + 60 * (len(cols) + 1); sheet = Image.new('RGB', (max(W, 1600), FIG_H + 520), (40, 40, 46)); d = ImageDraw.Draw(sheet)
x = 60; base = 40 + FIG_H
for i in range(21):
    y = base - FIG_H * i / 20; d.line([(10, y), (W - 10, y)], fill=(70, 70, 80) if i % 2 else (95, 95, 110)); d.text((12, y - 12), f'{i * 5}%', fill=(160, 160, 170))
for name, im, r in cols:
    sheet.paste(im, (x, base - FIG_H)); d.text((x, base + 6), name, fill=(255, 255, 255))
    d.text((x, base + 22), f"span/height {r['span_over_h']}  P10/50/90 {r['p10']}/{r['p50']}/{r['p90']}", fill=(220, 220, 220))
    d.text((x, base + 38), f"dark {r['dark']:.0%} bright {r['bright']:.0%}", fill=(220, 220, 220))
    d.text((x, base + 54), r['heads_note'][:60], fill=(200, 200, 160))
    x += im.width + 60
# play-size row: kit figures at 1.9 m x 110 px/m beside the 1:1 crops of the round-4 and round-5 fa from the same fight-framing shot
y0 = base + 90; d.text((60, y0), f'play size (fight framing {PPM} px/m): kit figures scaled to {KIT_M} m, fa 1:1 crops (left round 4, right round 5)', fill=(255, 255, 255))
x = 60
for name, im, m, note in figs[:2]:
    ys, xs = np.where(m); crop = Image.fromarray(im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]); hh = round(KIT_M * PPM)
    sheet.paste(crop.resize((max(1, round(crop.width * hh / crop.height)), hh), Image.LANCZOS), (x, y0 + 30 + 230 - hh)); x += 200
pp = f'{S}/pair_play.png'
if os.path.exists(pp):
    im = Image.open(pp).convert('RGB'); cx, cy = im.width // 2, im.height // 2 - 40
    sheet.paste(im.crop((cx - 300, cy - 150, cx + 300, cy + 140)), (x + 20, y0 + 20))
sheet.save(os.path.join(O, 'fa_r5_vs_kit.jpg'), quality=90)
json.dump(res, open(os.path.join(O, 'fa_r5_vs_kit.json'), 'w'), indent=1)
for k, v in res.items(): print(k, {kk: vv for kk, vv in v.items() if kk != 'colours'})
