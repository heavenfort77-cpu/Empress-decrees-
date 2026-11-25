#!/usr/bin/env python3
"""Method 1 (cocolito): the knight drawn in code with Pillow, in passes: silhouette, flat colours,
shading from one light, outline, details. Same shapes as the klad version (knight_shapes.py).
Run: python3 cocolito_knight.py   -> m1_knight_1x.png, m1_knight_3x.png"""
import random
import numpy as np
from PIL import Image
from knight_shapes import F, rast, P, SHADOWS

# ---------------- CONFIG: tune by hand ----------------
CONFIG = {
    'seed': 7,
    'light': (0.75, 0.5),        # light from the upper left (x weight, y weight)
    'side': 0.2,                 # how much darker the side of the figure away from the light is
    'steps': (0.80, 0.58, 0.34, 0.14),   # value above which a pixel is highlight, light, mid, dark (else deep)
    'bounce': 0.78,              # reflected light on the far edge of a round plate (0 to 1 across the part; 1 = off)
    'wear': 7,                   # small worn patches on the steel
    'scale': 3,
    # ramps: outline, deep, dark, mid, light, highlight
    'ramps': {
        'S': ['#20242c', '#454d5a', '#6c7684', '#98a2ad', '#c9d0d6', '#f1f4f5'],
        'D': ['#101216', '#23272f', '#353b45', '#4b525d', '#666e79', '#8d95a0'],
        'B': ['#2a1c0a', '#553c17', '#86632a', '#b98f3f', '#e2bf66', '#f8e6a6'],
        'U': ['#0a0b0d', '#131418', '#1e2026', '#2c2f37', '#3d414b', '#555a65'],
        'C': ['#0f1a12', '#1b2e20', '#2b4630', '#3f6242', '#598058', '#7da078'],
        'L': ['#200b08', '#431812', '#6b261c', '#93392a', '#b8553f', '#d98468'],
        'G': ['#0c3f4a', '#127a8c', '#2bb7c9', '#5fe6f0', '#b4f8fb', '#f0ffff'],
    },
}
# -------------------------------------------------------
def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
mat = np.full((F, F), '', dtype='<U1'); tone = np.zeros((F, F), int)
Y, X = np.mgrid[0:F, 0:F]

def put(mask, m, mode):
    ys, xs = np.nonzero(mask)
    if not len(xs): return
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if mode.startswith('flat'): t = np.full((F, F), min(5, int(mode[4]) + 1))
    else:
        # pass 3: treat each plate as a rounded form and light it from one direction
        nx = (X - (x0 + x1) / 2) / max(1, (x1 - x0) / 2); ny = (Y - (y0 + y1) / 2) / max(1, (y1 - y0) / 2)
        lx, ly = CONFIG['light']; v = 0.5 - 0.5 * (nx * lx + ny * ly) / (lx + ly) - CONFIG['side'] * (X - 47.5) / 48
        a, b, c, d = CONFIG['steps']; t = np.where(v > a, 5, np.where(v > b, 4, np.where(v > c, 3, np.where(v > d, 2, 1))))
        t = np.where((nx > CONFIG['bounce']) & (t <= 2), t + 1, t)                       # reflected light on the far edge
        if m not in 'SB': t = np.minimum(t, 4)                                           # only metal gets a highlight
        if mode == 'flute': t = np.where((X - x0) % 3 == 2, np.maximum(t - 1, 1), t)     # grooves
        if mode == 'lames': t = np.where((Y - y0) % 4 == 3, np.maximum(t - 2, 1), t)     # plate seams
        if mode == 'ribs': t = np.where((Y - y0) % 2 == 1, 1, 2)
        # where this part lies over the same material, a darker line on its far edge keeps the two apart
        p = np.pad(mask, 1); right, down = p[1:-1, 2:], p[2:, 1:-1]
        mr = np.pad(mat, 1, constant_values='')
        same = ((~right) & (mr[1:-1, 2:] == m)) | ((~down) & (mr[2:, 1:-1] == m))
        t = np.where(mask & same, np.maximum(t - 1, 1), t)
    mat[mask] = m; tone[mask] = t[mask]

for kind, m, mode, shape in P:                                # passes 1 and 2: silhouette and flat material, back to front
    k = rast(shape)
    if kind == 'sym': put(k | k[:, ::-1], m, mode)
    else: put(k, m, mode); put(k[:, ::-1], m, mode)
for sh in SHADOWS:                                            # cast shadows under overhangs
    k = rast(sh) & (mat != '') & (mat != 'G'); tone[k] = np.maximum(tone[k] - 1, 1)
rnd = random.Random(CONFIG['seed'])                           # pass 5: a few worn patches, two pixels each
for _ in range(CONFIG['wear']):
    for _try in range(40):
        x, y = rnd.randrange(22, 73), rnd.randrange(24, 88)
        if mat[y, x] == 'S' and mat[y, x + 1] == 'S' and tone[y, x] >= 3 and tone[y, x + 1] >= 3:
            tone[y, x] -= 1; tone[y, x + 1] -= 1; break
for _ in range(3):                                            # merge single stray pixels (glow pixels are meant)
    new = tone.copy()
    for y in range(F):
        for x in range(F):
            if not mat[y, x] or mat[y, x] == 'G': continue
            if any(0 <= y + dy < F and 0 <= x + dx < F and mat[y + dy, x + dx] == mat[y, x] and tone[y + dy, x + dx] == tone[y, x] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): continue
            nb = [tone[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy) and 0 <= y + dy < F and 0 <= x + dx < F and mat[y + dy, x + dx] == mat[y, x]]
            if nb: new[y, x] = max(set(nb), key=nb.count)
    tone = new
out = np.zeros((F, F, 4), np.uint8)
for y in range(F):
    for x in range(F):
        if mat[y, x]: out[y, x] = hexrgb(CONFIG['ramps'][mat[y, x]][tone[y, x]]) + (255,)
solid = mat != ''
for y in range(F):                                            # pass 4: 1 px outline in the darkest tone of the material it touches
    for x in range(F):
        if solid[y, x]: continue
        for dx, dy in ((0, -1), (-1, 0), (1, 0), (0, 1)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < F and 0 <= yy < F and solid[yy, xx]:
                m = 'S' if mat[yy, xx] == 'G' else mat[yy, xx]; out[y, x] = hexrgb(CONFIG['ramps'][m][0]) + (255,); break
im = Image.fromarray(out, 'RGBA'); im.save('m1_knight_1x.png')
s = CONFIG['scale']; im.resize((F * s, F * s), Image.NEAREST).save(f'm1_knight_{s}x.png')
