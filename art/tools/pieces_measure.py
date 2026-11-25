#!/usr/bin/env python3
"""Play-size measures for the PIECES round, from pieces_shoot.mjs shots (same camera for the lit shot and its mask):
  floor contrast   per piece: the share of its outline pixels whose contrast (WCAG relative luminance) against what is beside it at the
                   game camera is >= 3:1 (the rule of art/tools/suit_contrast.py), its body median contrast, and its size on screen;
                   Kaymuse is measured on the throne (play and approach framings); the calm-floor stand-in is reported as INFO only.
  silhouettes      crab against wanderer at the game camera, front and side: IoU at the same scale and place, and IoU after scaling
                   both to one height (bottom-centre aligned); every one must be <= 0.6.
--mutate: contrast gate against the piece repainted in its surround's median colour; visibility gate against an empty mask; silhouette
gate against the crab compared with itself. Usage: python3 pieces_measure.py SHOTDIR [--mutate]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

# CONFIG
# Contrast the outline must reach against what is beside it, and the share of outline pixels that must reach it.
RATIO, EDGE_SHARE = 3.0, 0.5
# Fewest mask pixels for a piece to count as visible at play size (1920 x 1080).
AREA_MIN = 150
# Most silhouette overlap allowed between the crab and the wanderer.
IOU_MAX = 0.6
S = sys.argv[1]
FLOOR = ['crab', 'wanderer', 'plate', 'leader_crown', 'mo_wall', 'decree_mark']

def lum(path):
    img = np.asarray(Image.open(path).convert('RGB')).astype(float) / 255
    lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4); return img, lin @ [0.2126, 0.7152, 0.0722]

def contrast(Y, m):
    """-> (ok, outline share, body median ratio, area px, height px)"""
    area = int(m.sum())
    if area < AREA_MIN: return False, 0.0, 0.0, area, 0
    ring = ndimage.binary_dilation(m, iterations=10) & ~ndimage.binary_dilation(m, iterations=2)
    edge = m & ~ndimage.binary_erosion(m, iterations=2); fl = np.median(Y[ring]); ys = np.median(Y[m])
    er = (np.maximum(Y[edge], fl) + 0.05) / (np.minimum(Y[edge], fl) + 0.05); share = float((er >= RATIO).mean())
    rows = np.where(m.any(1))[0]
    return share >= EDGE_SHARE, share, float((max(ys, fl) + 0.05) / (min(ys, fl) + 0.05)), area, int(rows[-1] - rows[0] + 1)

def mask(name): return np.asarray(Image.open(f'{S}/{name}.png').convert('L')) > 128

def sil(name): return np.asarray(Image.open(f'{S}/{name}.png').convert('L')) < 128

def fit(m, h=400):
    """crop to the outline, scale to height h, paste bottom-centre on a wide canvas."""
    if not m.any(): return np.zeros((h, 4 * h), bool)
    ys, xs = np.where(m); c = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; w = max(1, round(c.shape[1] * h / c.shape[0]))
    im = np.asarray(Image.fromarray((c * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)) > 128; out = np.zeros((h, 4 * h), bool)
    w = min(w, 4 * h); x0 = (4 * h - w) // 2; out[:, x0:x0 + w] = im[:, :w]; return out

def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))

n = fails = 0
def gate(ok, line):
    global n, fails
    n += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + line)

_, Y = lum(f'{S}/lineup_play.png'); _, Yc = lum(f'{S}/lineup_calm.png')
for pid in FLOOR:
    m = mask(f'mask_{pid}'); ok, share, med, area, hpx = contrast(Y, m)
    gate(ok, f'{pid} at play size (CAM_DIST 14, 1080p; {hpx} px high, {area} px): {share:.0%} of outline pixels >= {RATIO}:1 against what is beside it on the hall floor (min {EDGE_SHARE:.0%}); body median {med:.1f}:1')
    _, s2, m2, _, _ = contrast(Yc, m); print(f'INFO {pid} on the calm stand-in floor (#7a2a1c): outline {s2:.0%}, body median {m2:.1f}:1')
for view in ('play', 'approach'):
    _, Yt = lum(f'{S}/throne_{view}.png'); m = mask(f'mask_kaymuse_{view}'); ok, share, med, area, hpx = contrast(Yt, m)
    gate(ok, f'kaymuse on the throne, {view} framing ({hpx} px high, {area} px): {share:.0%} of outline pixels >= {RATIO}:1 against the throne behind her (min {EDGE_SHARE:.0%}); body median {med:.1f}:1')
for yaw in (0, 90):
    a, b = sil(f'sil_crab_{yaw}'), sil(f'sil_wanderer_{yaw}'); raw = iou(a, b); nor = iou(fit(a), fit(b))
    gate(a.sum() >= AREA_MIN and b.sum() >= AREA_MIN and raw <= IOU_MAX and nor <= IOU_MAX, f'crab against wanderer, game camera yaw {yaw}: silhouette IoU {raw:.2f} at the same scale, {nor:.2f} scaled to one height (max {IOU_MAX})')
print(f'{n - fails} of {n} pass')

if '--mutate' in sys.argv:
    res = []
    img, _ = lum(f'{S}/lineup_play.png'); m = mask('mask_wanderer'); ring = ndimage.binary_dilation(m, iterations=10) & ~ndimage.binary_dilation(m, iterations=2)
    img2 = img.copy(); img2[m] = np.median(img[ring], axis=0); lin = np.where(img2 <= 0.04045, img2 / 12.92, ((img2 + 0.055) / 1.055) ** 2.4)
    ok, share, *_ = contrast(lin @ [0.2126, 0.7152, 0.0722], m); res.append((not ok, f'contrast gate against the wanderer repainted in its surround colour -> outline {share:.0%}'))
    ok, _, _, area, _ = contrast(Y, np.zeros_like(m)); res.append((not ok, f'visibility gate against an empty mask -> {area} px'))
    a = sil('sil_crab_0'); v = iou(a, a); res.append((v > IOU_MAX, f'silhouette gate against the crab compared with itself -> IoU {v:.2f}'))
    v2 = iou(fit(a), fit(a)); res.append((v2 > IOU_MAX, f'scaled silhouette gate against the crab compared with itself -> IoU {v2:.2f}'))
    for hit, line in res: print(('MUT caught: ' if hit else 'MUT MISSED: ') + line)
    print(f'{sum(h for h, _ in res)} of {len(res)} mutations caught')
