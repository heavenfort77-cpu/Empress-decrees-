#!/usr/bin/env python3
"""Method 2, version 2: build the knight sprite from the 3D model inside klad's palette.
- Material of each pixel: from klad's pixelise of the flat matt capture (stdin, klad pixels --plain), so trims and plates keep clean edges.
- Light and shade: the full 3D render's brightness, slightly smoothed, cut into the steps of that material's ramp
  at the render's own percentiles, so the sprite carries the render's light instead of an invented one.
- Lights: wherever the render glows, the pixel is a light.
Writes the grid on stdout for klad pixel --grid."""
import sys
import numpy as np
from PIL import Image
# ---------------- CONFIG: tune by hand ----------------
AT = (23, 2); SIZE = (50, 92)          # where the render sits in the 96 px frame, and its size there
STEPS = {'steel': 5, 'gun': 3, 'brass': 4, 'cloth': 3, 'leather': 2}
CUTS = {5: (7, 22, 46, 76), 4: (15, 42, 75), 3: (30, 72), 2: (50,)}   # percentiles of brightness where a ramp steps up
CLOTH_BOX = (40, 50, 56, 72)           # cloth is only real inside this box (x0, y0, x1, y1); elsewhere it is noise
LEATHER_BOX = (44, 26, 52, 48)
SMOOTH = 0.5                           # 0 = raw brightness, 1 = fully averaged with the 8 neighbours
GLOW_COVER = 0.2                       # a pixel becomes a light when this share of it glows in the render
# -------------------------------------------------------
lines = sys.stdin.read().split('\n'); k = lines.index('')
legend = {l.split(' = ')[0]: l.split(' = ')[1].split()[0] for l in lines[:k] if ' = ' in l}
rows = [r for r in lines[k + 1:] if r]; H, W = len(rows), len(rows[0])
fam = np.array([['' if c == '.' else legend[c].split('-')[0] for c in r] for r in rows], dtype='<U8')
fam[fam == 'ink'] = 'gun'; fam[fam == 'glow'] = 'steel'
def nb(a, y, x): return [a[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy) and 0 <= y + dy < H and 0 <= x + dx < W and a[y + dy, x + dx]]
for y in range(H):                      # colours that only snapped there by accident
    for x in range(W):
        f = fam[y, x]
        bad = (f == 'cloth' and not (CLOTH_BOX[0] <= x <= CLOTH_BOX[2] and CLOTH_BOX[1] <= y <= CLOTH_BOX[3])) or (f == 'leather' and not (LEATHER_BOX[0] <= x <= LEATHER_BOX[2] and LEATHER_BOX[1] <= y <= LEATHER_BOX[3]))
        if bad:
            n = [v for v in nb(fam, y, x) if v not in ('cloth', 'leather')]; fam[y, x] = max(set(n), key=n.count) if n else 'steel'
for _ in range(2):                      # a single pixel of a material joins its neighbours (brass trim lines stay)
    new = fam.copy()
    for y in range(H):
        for x in range(W):
            if not fam[y, x] or fam[y, x] == 'brass': continue
            n = nb(fam, y, x)
            if n and n.count(fam[y, x]) == 0: new[y, x] = max(set(n), key=n.count)
    fam = new
ref = np.array(Image.open('ref_knight_alpha.png').convert('RGBA')).astype(np.float32)
a = ref[..., 3] / 255; lum = (0.3 * ref[..., 0] + 0.59 * ref[..., 1] + 0.11 * ref[..., 2])
box = lambda v: np.array(Image.fromarray(v.astype(np.float32), 'F').resize(SIZE, Image.BOX))
L = np.zeros((H, W), np.float32); L[AT[1]:AT[1] + SIZE[1], AT[0]:AT[0] + SIZE[0]] = box(lum * a) / np.maximum(box(a), 1e-3)
solid = fam != ''
Ls = L.copy()                           # light smoothing so tones form clusters, not specks
for y in range(H):
    for x in range(W):
        if not solid[y, x]: continue
        v = [L[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= y + dy < H and 0 <= x + dx < W and solid[y + dy, x + dx] and fam[y + dy, x + dx] == fam[y, x]]
        Ls[y, x] = (1 - SMOOTH) * L[y, x] + SMOOTH * float(np.mean(v))
g = np.full((H, W), '', dtype='<U12')
for f, n in STEPS.items():
    m = fam == f
    if not m.any(): continue
    cuts = np.percentile(Ls[m], CUTS[n]); step = 1 + sum((Ls > c).astype(int) for c in cuts)
    for y, x in zip(*np.nonzero(m)): g[y, x] = f'{f}-{step[y, x]}'
for _ in range(3):                      # merge single stray pixels into their neighbours
    new = g.copy()
    for y in range(H):
        for x in range(W):
            if not g[y, x]: continue
            if any(0 <= y + dy < H and 0 <= x + dx < W and g[y + dy, x + dx] == g[y, x] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): continue
            n = [v for v in nb(g, y, x) if v.split('-')[0] == g[y, x].split('-')[0]] or nb(g, y, x)
            if n: new[y, x] = max(set(n), key=n.count)
    g = new
r_, g_, b_ = ref[..., 0], ref[..., 1], ref[..., 2]
glow = ((np.minimum(g_, b_) - r_ > 18) & (g_ > 190) & (b_ > 190) & (ref[..., 3] > 0)).astype(np.float32)
cov = box(glow)
for yy in range(SIZE[1]):
    for xx in range(SIZE[0]):
        y, x = yy + AT[1], xx + AT[0]
        if cov[yy, xx] >= GLOW_COVER and g[y, x]: g[y, x] = 'glow-2' if cov[yy, xx] >= 0.45 else 'glow-1'
names = sorted({n for n in g.flatten() if n}); chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGH'; code = {n: chars[i] for i, n in enumerate(names)}
print('\n'.join(f'{code[n]} = {n}' for n in names)); print()
print('\n'.join(''.join(code[g[y, x]] if g[y, x] else '.' for x in range(W)) for y in range(H)))
