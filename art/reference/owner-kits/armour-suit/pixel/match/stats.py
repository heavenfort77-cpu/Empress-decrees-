#!/usr/bin/env python3
"""The same measurements for the reference and for the new sprites, so a match is claimed by numbers."""
import sys
import numpy as np
from PIL import Image
INK = (0x1b, 0x1d, 0x2e); STEEL = [(0x3a, 0x45, 0x60), (0x5f, 0x6d, 0x8c), (0x8f, 0x9d, 0xb8), (0xc5, 0xcf, 0xdd), (0xf4, 0xf7, 0xfb)]
for f in sys.argv[1:]:
    a = np.array(Image.open(f).convert('RGBA')); s = a[..., 3] > 0; ys, xs = np.nonzero(s); H, W = s.shape
    semi = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()); cols = {tuple(p) for p in a[s][:, :3]}
    iso = sum(not any(0 <= y + dy < H and 0 <= x + dx < W and s[y + dy, x + dx] and (a[y + dy, x + dx, :3] == a[y, x, :3]).all() for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))) for y, x in zip(ys, xs))
    p = np.pad(s, 1); edge = s & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]); ink = (a[..., :3] == INK).all(-1) & s
    st = [int(((a[..., :3] == c).all(-1) & s).sum()) for c in STEEL]; tot = max(1, sum(st))
    print(f"{f}: {xs.max() - xs.min() + 1}x{ys.max() - ys.min() + 1} px, {len(cols)} colours, isolated {100 * iso / len(xs):.1f}%, semi-transparent {semi}, ink {100 * ink.sum() / len(xs):.0f}% of pixels, outline dark on {100 * (edge & ink).sum() / edge.sum():.0f}% of the edge, steel tones dark-to-light {'/'.join(str(round(100 * v / tot)) for v in st)}%")
