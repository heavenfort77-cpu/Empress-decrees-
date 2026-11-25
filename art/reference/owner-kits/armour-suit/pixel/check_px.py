#!/usr/bin/env python3
"""Pixel gates for 96 px sprites. Prints PASS/FAIL per file and only the failing lines. Usage: python3 check_px.py file.png ..."""
import sys
import numpy as np
from PIL import Image
LIM = dict(hmin=72, hmax=94, gap=(1, 2), colours=26, isolated=6.0)
ok_all = True
for f in sys.argv[1:]:
    a = np.array(Image.open(f).convert('RGBA')); al = a[..., 3] > 0; fails = []
    semi = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())
    ys, xs = np.nonzero(al); H, W = al.shape
    h = ys.max() - ys.min() + 1; gap = H - 1 - ys.max()
    if a.shape[0] != 96 or a.shape[1] != 96: fails.append(f'frame {a.shape[1]}x{a.shape[0]}')
    if semi: fails.append(f'semi-transparent pixels {semi}')
    if not LIM['hmin'] <= h <= LIM['hmax']: fails.append(f'height {h}')
    if not LIM['gap'][0] <= gap <= LIM['gap'][1]: fails.append(f'feet gap {gap}')
    if xs.min() == 0 or xs.max() == W - 1 or ys.min() == 0: fails.append('touches frame edge')
    cols = {tuple(p) for p in a[al][:, :3]}
    if len(cols) > LIM['colours']: fails.append(f'colours {len(cols)}')
    iso = 0
    for y, x in zip(ys, xs):
        if not any(0 <= x + dx < W and 0 <= y + dy < H and al[y + dy, x + dx] and (a[y + dy, x + dx, :3] == a[y, x, :3]).all() for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): iso += 1
    pct = 100 * iso / len(xs)
    if pct > LIM['isolated']: fails.append(f'isolated {pct:.1f}%')
    seen = np.zeros_like(al); st = [(ys[0], xs[0])]; seen[ys[0], xs[0]] = True; c = 0
    while st:
        y, x = st.pop(); c += 1
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and al[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; st.append((yy, xx))
    if c != len(xs): fails.append(f'not one piece ({len(xs) - c} px loose)')
    print(f, 'PASS' if not fails else 'FAIL: ' + '; '.join(fails), f'[h={h} colours={len(cols)} iso={pct:.1f}% semi={semi}]'); ok_all &= not fails
sys.exit(0 if ok_all else 1)
