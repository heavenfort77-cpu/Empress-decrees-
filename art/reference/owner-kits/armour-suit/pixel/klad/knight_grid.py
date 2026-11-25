#!/usr/bin/env python3
"""Method 2 (klad): plan the knight as flat material shapes with one light, and write it as a klad pixel grid.
klad then supplies the hue-shifted ramps (palette), the outline, the checks and the export.
Run: python3 knight_grid.py > knight.grid"""
import numpy as np
from PIL import Image, ImageDraw
F = 96
# ---------------- CONFIG: tune by hand ----------------
LIGHT = (0.65, 0.35)       # light from the upper left: weight of x and of y in the ramp
BANDS = (0.34, 0.74)       # where light -> mid and mid -> dark switch
SIDE = 0.22                # how much darker the side away from the light is
RIM = 0.3                  # highlights only on the part of an edge this close to the light (small, not a full rim)
# ramp steps per material, dark to light, as klad palette names
RAMP = {'S': ['steel-1', 'steel-2', 'steel-3', 'steel-4', 'steel-5'], 'D': ['gun-1', 'gun-1', 'gun-2', 'gun-3', 'gun-3'],
        'B': ['brass-1', 'brass-1', 'brass-2', 'brass-3', 'brass-4'], 'U': ['ink', 'under-1', 'under-1', 'under-2', 'under-2'],
        'C': ['cloth-1', 'cloth-1', 'cloth-2', 'cloth-3', 'cloth-3'], 'L': ['leather-1', 'leather-1', 'leather-2', 'leather-2', 'leather-2'],
        'G': ['glow-1', 'glow-1', 'glow-1', 'glow-2', 'glow-2']}
# -------------------------------------------------------
import sys; sys.path.insert(0, '..')
from knight_shapes import R, rast, P, SHADOWS
mat = np.full((F, F), '', dtype='<U1'); tone = np.zeros((F, F), int)
def put(mask, m, mode):
    ys, xs = np.nonzero(mask)
    if not len(xs): return
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max(); Y, X = np.mgrid[0:F, 0:F]
    s = LIGHT[0] * (X - x0) / max(1, x1 - x0) + LIGHT[1] * (Y - y0) / max(1, y1 - y0) + SIDE * (X - 47.5) / 48   # the far side of the figure sits darker
    t = np.where(s < BANDS[0], 3, np.where(s < BANDS[1], 2, 1))
    if mode.startswith('flat'): t = np.full((F, F), int(mode[4]))
    else:
        if mode == 'flute': t = np.where((X - x0) % 3 == 2, np.maximum(t - 1, 1), t)
        if mode == 'lames': t = np.where((Y - y0) % 4 == 3, 1, t)
        if mode == 'ribs': t = np.where((Y - y0) % 2 == 1, 1, 2)
        p = np.pad(mask, 1); left, up, right, down = p[1:-1, :-2], p[:-2, 1:-1], p[1:-1, 2:], p[2:, 1:-1]
        if mode != 'ribs': t = np.where(mask & (~left | ~up) & (s < RIM), 4, t)            # small highlight near the light only
    mat[mask] = m; tone[mask] = t[mask]
for kind, m, mode, shape in P:
    k = rast(shape)
    if kind == 'sym': put(k | k[:, ::-1], m, mode)
    else: put(k, m, mode); put(k[:, ::-1], m, mode)
for sh in SHADOWS:
    k = rast(sh) & (mat != '') & (mat != 'G'); tone[k] = np.maximum(tone[k] - 1, 0)
# merge single stray pixels into their neighbours (glow pixels are meant, so they stay)
name = np.full((F, F), '', dtype='<U12')
for y in range(F):
    for x in range(F):
        if mat[y, x]: name[y, x] = RAMP[mat[y, x]][tone[y, x]]
for _ in range(3):
    new = name.copy()
    for y in range(F):
        for x in range(F):
            n = name[y, x]
            if not n or n.startswith('glow'): continue
            if any(0 <= y + dy < F and 0 <= x + dx < F and name[y + dy, x + dx] == n for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): continue
            nb = [name[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy) and 0 <= y + dy < F and 0 <= x + dx < F and name[y + dy, x + dx] and not name[y + dy, x + dx].startswith('glow')]
            if nb: new[y, x] = max(set(nb), key=nb.count)
    name = new
names = sorted({n for n in name.flatten() if n})
chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGH'; code = {n: chars[i] for i, n in enumerate(names)}
for n in names: print(f'{code[n]} = {n}')
print()
for y in range(F): print(''.join(code[name[y, x]] if name[y, x] else '.' for x in range(F)))
raise SystemExit
names = sorted({RAMP[m][t] for m, t in zip(mat[mat != ''], tone[mat != ''])})
chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGH'; code = {n: chars[i] for i, n in enumerate(names)}
for n in names: print(f'{code[n]} = {n}')
print()
for y in range(F): print(''.join(code[RAMP[mat[y, x]][tone[y, x]]] if mat[y, x] else '.' for x in range(F)))
