#!/usr/bin/env python3
"""Measure the new sprites against the reference frame and build a side-by-side strip at the same scale."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
def stats(a):
    al = a[..., 3] > 0; ys, xs = np.nonzero(al); H, W = al.shape
    iso = sum(not any(0 <= x + dx < W and 0 <= y + dy < H and al[y + dy, x + dx] and (a[y + dy, x + dx, :3] == a[y, x, :3]).all() for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))) for y, x in zip(ys, xs))
    cols = {tuple(p) for p in a[al][:, :3]}
    return dict(frame=f'{W}x{H}', height=int(ys.max() - ys.min() + 1), width=int(xs.max() - xs.min() + 1), bottom_row=int(ys.max()), colours=len(cols), isolated=round(100 * iso / len(xs), 1), semi=int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum())), cols
ref, refc = stats(np.array(Image.open('ref_native_0.png').convert('RGBA'))); print('reference', ref)
for v in ('side', 'front', 'back'):
    s, c = stats(np.array(Image.open(f'out/knight_{v}_1x.png').convert('RGBA'))); print(v, s, 'colours not in the reference palette:', len(c - refc))
try: font = ImageFont.load_default(size=17)
except TypeError: font = ImageFont.load_default()
S = 6; C = 64 * S; items = [('reference (side)', 'ref_native_0.png'), ('klad: side', 'out/knight_side_1x.png'), ('klad: front', 'out/knight_front_1x.png'), ('klad: back', 'out/knight_back_1x.png')]
strip = Image.new('RGB', (C * 4, C + 28 + 70), '#7d838c'); d = ImageDraw.Draw(strip)
for i, (label, p) in enumerate(items):
    im = Image.open(p).convert('RGBA'); d.text((i * C + 8, 5), label, fill='#14161c', font=font)
    big = im.resize((C, C), Image.NEAREST); strip.paste(big, (i * C, 28), big); strip.paste(im, (i * C + (C - 64) // 2, C + 30), im)
strip.save('out/compare_reference_side_front_back.png')
