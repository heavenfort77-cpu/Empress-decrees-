#!/usr/bin/env python3
"""Prints PASS/FAIL per character and only the failing lines."""
import sys
import numpy as np
from PIL import Image
LIM = {64: dict(hmin=48, hmax=62), 96: dict(hmin=72, hmax=93)}
LIMITS = dict(gap=(1, 2), colours=26, isolated=6.0)
ok_all = True
for n in ['knight', 'mage', 'rogue', 'construct', 'knight96']:
    a = np.array(Image.open(f'out/{n}_1x.png').convert('RGBA'))
    al = a[..., 3] > 0
    ys, xs = np.nonzero(al)
    fails = []
    LIMITS.update(LIM[a.shape[0]])
    h = ys.max() - ys.min() + 1
    gap = a.shape[0] - 1 - ys.max()
    if not LIMITS['hmin'] <= h <= LIMITS['hmax']: fails.append(f'height {h}')
    if not LIMITS['gap'][0] <= gap <= LIMITS['gap'][1]: fails.append(f'feet gap {gap}')
    if xs.min() == 0 or xs.max() == a.shape[1] - 1 or ys.min() == 0: fails.append('touches frame edge')
    cols = {tuple(p) for p in a[al][:, :3]}
    if len(cols) > LIMITS['colours']: fails.append(f'colours {len(cols)}')
    iso = 0
    H, W = al.shape
    for y, x in zip(ys, xs):
        same = False
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            xx, yy = x + dx, y + dy
            if 0 <= xx < W and 0 <= yy < H and al[yy, xx] and (a[yy, xx, :3] == a[y, x, :3]).all():
                same = True; break
        iso += not same
    pct = 100 * iso / len(xs)
    if pct > LIMITS['isolated']: fails.append(f'isolated {pct:.1f}%')
    seen = np.zeros_like(al); st = [(ys[0], xs[0])]; seen[ys[0], xs[0]] = True; c = 0
    while st:
        y, x = st.pop(); c += 1
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                yy, xx = y + dy, x + dx
                if 0 <= yy < H and 0 <= xx < W and al[yy, xx] and not seen[yy, xx]:
                    seen[yy, xx] = True; st.append((yy, xx))
    if c != len(xs): fails.append(f'not one piece ({len(xs) - c} px loose)')
    print(n, 'PASS' if not fails else 'FAIL: ' + '; '.join(fails), f'[h={h} colours={len(cols)} iso={pct:.1f}%]')
    ok_all &= not fails
sys.exit(0 if ok_all else 1)
