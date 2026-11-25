#!/usr/bin/env python3
"""Measure a pixel-art reference: frames, integer upscale and phase, native sprite, palette, outline, isolated pixels."""
import sys
import numpy as np
from PIL import Image
im = Image.open(sys.argv[1]); n = getattr(im, 'n_frames', 1); print('size', im.size, 'frames', n, 'mode', im.mode)
a = np.array(im.convert('RGBA')); H, W = a.shape[:2]
bg = tuple(a[0, 0]); print('corner pixel', bg)
best = None
for s in range(1, 17):                       # which grid rebuilds the picture with the fewest mismatches
    for py in range(s):
        for px in range(s):
            sub = a[py::s, px::s][: (H - py) // s, : (W - px) // s]
            if sub.shape[0] < 8: continue
            up = np.repeat(np.repeat(sub, s, 0), s, 1)
            ref = a[py:py + up.shape[0], px:px + up.shape[1]]
            mis = float((up != ref).any(-1).mean())
            if best is None or mis < best[0] - 1e-9 or (abs(mis - best[0]) < 1e-9 and s > best[1]): best = (mis, s, px, py)
mis, s, px, py = best; print(f'scale {s} phase {px},{py} mismatch {mis * 100:.2f}%')
hs, ws = (H - py) // s, (W - px) // s; nat = np.zeros((hs, ws, 4), np.uint8)
for y in range(hs):                          # most common colour in each block
    for x in range(ws):
        blk = a[py + y * s: py + (y + 1) * s, px + x * s: px + (x + 1) * s].reshape(-1, 4)
        u, c = np.unique(blk, axis=0, return_counts=True); nat[y, x] = u[c.argmax()]
solid = ~((nat == np.array(bg)).all(-1)) & (nat[..., 3] > 0)
ys, xs = np.nonzero(solid); print('native canvas', ws, 'x', hs, 'sprite box', xs.min(), ys.min(), xs.max(), ys.max(), 'w', xs.max() - xs.min() + 1, 'h', ys.max() - ys.min() + 1)
out = nat.copy(); out[~solid] = 0; Image.fromarray(out, 'RGBA').crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)).save('ref_native.png')
cols, cnt = np.unique(nat[solid][:, :3], axis=0, return_counts=True); order = cnt.argsort()[::-1]
print('colours', len(cols)); print(' '.join(f'#{r:02x}{g:02x}{b:02x}:{c}' for (r, g, b), c in zip(cols[order], cnt[order])))
iso = 0
for y, x in zip(ys, xs):
    if not any(0 <= y + dy < hs and 0 <= x + dx < ws and solid[y + dy, x + dx] and (nat[y + dy, x + dx] == nat[y, x]).all() for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): iso += 1
print(f'isolated {100 * iso / len(xs):.1f}%  solid px {len(xs)}')
p = np.pad(solid, 1); edge = solid & ~(p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:])
ec, en = np.unique(nat[edge][:, :3], axis=0, return_counts=True); o = en.argsort()[::-1][:4]
print('edge colours', ' '.join(f'#{r:02x}{g:02x}{b:02x}:{c}' for (r, g, b), c in zip(ec[o], en[o])), 'of', int(edge.sum()))
