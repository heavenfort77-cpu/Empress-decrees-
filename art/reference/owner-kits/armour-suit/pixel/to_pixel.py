#!/usr/bin/env python3
"""Method 1: turn a 3D capture (magenta backdrop) into a pixel sprite.
Run: python3 to_pixel.py knight   -> m1_knight_1x.png, m1_knight_3x.png, prints PASS/FAIL checks."""
import sys
import numpy as np
from PIL import Image

# ---------------- CONFIG: tune by hand ----------------
CONFIG = {
    'frame': 96,            # sprite frame in px
    'char_height': 85,      # character height in px, before the outline
    'colours': 18,          # colours picked from the render (glow colours are added on top)
    'contrast': 1.12,       # >1 separates the metal tones
    'saturation': 1.5,
    'alpha_cut': 0.45,      # coverage above this becomes a solid pixel
    'outline': '#14161c',
    'glow': {'knight': ['#e8ffff', '#5fe6f0'], 'mage': ['#efe6ff', '#b48cff'], 'rogue': ['#ffd9d2', '#ff4a3a'], 'beast': ['#fff0c8', '#ffa62b']},
    'orphan_passes': 2,
}
# -------------------------------------------------------
def hexrgb(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)

def convert(name):
    F = CONFIG['frame']
    src = np.array(Image.open(f'src_{name}.png').convert('RGB')).astype(float)
    r, g, b = src[..., 0], src[..., 1], src[..., 2]
    fg = ~((r - g > 80) & (b - g > 80) & (r > 150) & (b > 150))
    p = np.pad(fg, 1)                                         # drop the magenta-tinted fringe when averaging colour
    core = fg & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    ys, xs = np.nonzero(fg); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    s = CONFIG['char_height'] / (y1 - y0); w, h = max(1, round((x1 - x0) * s)), CONFIG['char_height']
    box = lambda a: np.array(Image.fromarray(a.astype(np.float32), 'F').resize((w, h), Image.BOX))
    cov = box(fg[y0:y1, x0:x1] * 1.0); cc = box(core[y0:y1, x0:x1] * 1.0)
    rgb = np.dstack([box(src[y0:y1, x0:x1, c] * core[y0:y1, x0:x1]) for c in range(3)]) / np.maximum(cc, 1e-4)[..., None]
    alpha = (cov > CONFIG['alpha_cut']) & (cc > 0.02)
    # tone: contrast and saturation so the plates read at this size
    v = rgb / 255; lum = v.mean(axis=2, keepdims=True)
    v = lum + (v - lum) * CONFIG['saturation']; v = 0.5 + (v - 0.5) * CONFIG['contrast']; rgb = np.clip(v, 0, 1) * 255
    # palette: median cut on the sprite's own pixels, plus the glow colours
    px = rgb[alpha].astype(np.uint8)
    q = Image.fromarray(px.reshape(1, -1, 3), 'RGB').quantize(colors=CONFIG['colours'], method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = np.array(q.getpalette()[:CONFIG['colours'] * 3], float).reshape(-1, 3)
    pal = np.unique(pal, axis=0); glow = np.array([hexrgb(c) for c in CONFIG['glow'][name]]); pal = np.vstack([pal, glow])
    d = ((rgb[..., None, :] - pal[None, None]) ** 2 * np.array([0.3, 0.59, 0.11])).sum(-1); idx = d.argmin(-1)
    nglow = len(glow); isglow = idx >= len(pal) - nglow
    H, W = alpha.shape
    for _ in range(CONFIG['orphan_passes']):                 # merge single stray pixels into their neighbours
        new = idx.copy()
        for y in range(H):
            for x in range(W):
                if not alpha[y, x] or isglow[y, x]: continue
                same = any(0 <= y + dy < H and 0 <= x + dx < W and alpha[y + dy, x + dx] and idx[y + dy, x + dx] == idx[y, x] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)))
                if same: continue
                nb = [idx[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy) and 0 <= y + dy < H and 0 <= x + dx < W and alpha[y + dy, x + dx]]
                if nb: new[y, x] = max(set(nb), key=nb.count)
        idx = new
    out = np.zeros((F, F, 4), np.uint8)
    ox, oy = (F - W) // 2, F - 2 - H                          # feet on row F-3, outline on row F-2
    out[oy:oy + H, ox:ox + W, :3] = pal[idx].astype(np.uint8) * alpha[..., None]; out[oy:oy + H, ox:ox + W, 3] = alpha * 255
    a = out[..., 3] > 0; pa = np.pad(a, 1)
    edge = ~a & (pa[:-2, 1:-1] | pa[2:, 1:-1] | pa[1:-1, :-2] | pa[1:-1, 2:])
    out[edge] = list(hexrgb(CONFIG['outline']).astype(np.uint8)) + [255]
    im = Image.fromarray(out, 'RGBA'); im.save(f'm1_{name}_1x.png'); im.resize((F * 3, F * 3), Image.NEAREST).save(f'm1_{name}_3x.png')
    return im

if __name__ == '__main__':
    for n in sys.argv[1:] or ['knight']: convert(n)
