#!/usr/bin/env python3
"""Animation gates. Prints PASS/FAIL per animation and only the failing lines."""
import sys
import numpy as np
from PIL import Image
ANIMS = [('idle', 4), ('walk_left', 4), ('walk_right', 4), ('battle', 1)]
LIM = dict(colours=26, isolated=7.5, change=(0, 85), height=(72, 94))
ok_all = True
for anim, n in ANIMS:
    fr = [np.array(Image.open(f'out/{anim}_{i}.png').convert('RGBA')) for i in range(n)]; fails = []; info = []
    bottoms = set()
    for i, a in enumerate(fr):
        al = a[..., 3] > 0; ys, xs = np.nonzero(al); H, W = al.shape
        if a.shape[:2] != (96, 96): fails.append(f'frame {i}: size {a.shape[1]}x{a.shape[0]}')
        semi = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())
        if semi: fails.append(f'frame {i}: semi-transparent pixels {semi}')
        cols = len({tuple(p) for p in a[al][:, :3]})
        if cols > LIM['colours']: fails.append(f'frame {i}: colours {cols}')
        GLOW = {(70, 215, 230), (117, 245, 250)}      # single-pixel lights are meant, so they are not counted as stray
        iso = sum(tuple(a[y, x, :3]) not in GLOW and not any(0 <= x + dx < W and 0 <= y + dy < H and al[y + dy, x + dx] and (a[y + dy, x + dx, :3] == a[y, x, :3]).all() for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))) for y, x in zip(ys, xs))
        pct = 100 * iso / len(xs)
        if pct > LIM['isolated']: fails.append(f'frame {i}: isolated {pct:.1f}%')
        h = ys.max() - ys.min() + 1
        if not LIM['height'][0] <= h <= LIM['height'][1]: fails.append(f'frame {i}: height {h}')
        if xs.min() == 0 or xs.max() == W - 1 or ys.min() == 0 or ys.max() == H - 1: fails.append(f'frame {i}: touches the frame edge')
        seen = np.zeros_like(al); st = [(ys[0], xs[0])]; seen[ys[0], xs[0]] = True; c = 0
        while st:
            y, x = st.pop(); c += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W and al[yy, xx] and not seen[yy, xx]: seen[yy, xx] = True; st.append((yy, xx))
        if c != len(xs): fails.append(f'frame {i}: not one piece ({len(xs) - c} px loose)')
        bottoms.add(int(ys.max())); info.append(f'{h}px/{cols}c/{pct:.1f}%')
    if len(bottoms) > 1: fails.append(f'feet not on one ground row: {sorted(bottoms)}')
    ch = []
    for i in range(n if n > 1 else 0):
        a, b = fr[i], fr[(i + 1) % n]; u = (a[..., 3] > 0) | (b[..., 3] > 0); d = (a != b).any(axis=2) & u; ch.append(100 * d.sum() / u.sum())
    if ch and max(ch) > LIM['change'][1]: fails.append(f'frame-to-frame change up to {max(ch):.0f}%')
    print(anim, 'PASS' if not fails else 'FAIL: ' + '; '.join(fails), '[' + ' '.join(info) + ']', ('change ' + '/'.join(f'{c:.0f}%' for c in ch)) if ch else ''); ok_all &= not fails
sys.exit(0 if ok_all else 1)
