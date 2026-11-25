#!/usr/bin/env python3
"""Comparison strip: 3D model, method 1 (3D to pixel), method 2 (klad). Top row enlarged 3x, bottom row real size."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
BG = '#7d838c'; W = 312; n = 'knight'
src = np.array(Image.open(f'src_{n}.png').convert('RGB')).astype(int)
fg = ~((src[..., 0] - src[..., 1] > 80) & (src[..., 2] - src[..., 1] > 80) & (src[..., 0] > 150) & (src[..., 2] > 150))
ys, xs = np.nonzero(fg); m = 20
ref = Image.open(f'ref_{n}.png').convert('RGB').crop((xs.min() - m, ys.min() - m, xs.max() + m, ys.max() + m))
ref = ref.resize((round(ref.width * 288 / ref.height), 288), Image.LANCZOS)
panels = [('3D model', ref, None), ('1: drawn in code (cocolito)', Image.open(f'm1_{n}_3x.png'), Image.open(f'm1_{n}_1x.png')), ('2a: klad, first version', Image.open(f'klad/m2v1_{n}_3x.png'), Image.open(f'klad/m2v1_{n}_1x.png')), ('2b: klad, from the 3D render', Image.open(f'klad/m2_{n}_3x.png'), Image.open(f'klad/m2_{n}_1x.png'))]
try: font = ImageFont.load_default(size=17)
except TypeError: font = ImageFont.load_default()
strip = Image.new('RGB', (W * 4, 30 + 300 + 26 + 108), BG); d = ImageDraw.Draw(strip)
for i, (label, big, small) in enumerate(panels):
    x = i * W; d.text((x + 10, 6), label, fill='#14161c', font=font)
    big = big.convert('RGBA'); strip.paste(big, (x + (W - big.width) // 2, 36), big)
    if small is not None:
        small = small.convert('RGBA'); strip.paste(small, (x + (W - 96) // 2, 30 + 300 + 26 + 6), small)
    if i: d.line([(x, 0), (x, strip.height)], fill='#5d6672', width=1)
d.text((10, 30 + 300 + 4), 'real size (96 px)', fill='#14161c', font=font)
strip.save('compare_strip_knight.png'); print(strip.size)
