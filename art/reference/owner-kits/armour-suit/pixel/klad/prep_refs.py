#!/usr/bin/env python3
"""Cut the knight out of the two 3D captures: the flat matt one (clean material colours) and the full render (light and shade)."""
import numpy as np
from PIL import Image
src = np.array(Image.open('../src_knight.png').convert('RGB')); s = src.astype(int)
fg = ~((s[..., 0] - s[..., 1] > 80) & (s[..., 2] - s[..., 1] > 80) & (s[..., 0] > 150) & (s[..., 2] > 150))
p = np.pad(fg, 2); core = fg & p[:-4, 2:-2] & p[4:, 2:-2] & p[2:-2, :-4] & p[2:-2, 4:]      # drop the magenta-tinted fringe
ys, xs = np.nonzero(fg); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
ref = np.array(Image.open('../ref_knight.png').convert('RGB'))
Image.fromarray(np.dstack([src, (core * 255).astype(np.uint8)])[y0:y1, x0:x1], 'RGBA').save('flat_knight_alpha.png')
Image.fromarray(np.dstack([ref, (fg * 255).astype(np.uint8)])[y0:y1, x0:x1], 'RGBA').save('ref_knight_alpha.png')
