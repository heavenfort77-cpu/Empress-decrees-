#!/usr/bin/env python3
"""Side-by-side at the same scale: the reference, then my side, front and back."""
from PIL import Image, ImageDraw, ImageFont
BG = '#7d838c'; S = 6; W = 64 * S
try: font = ImageFont.load_default(size=17)
except TypeError: font = ImageFont.load_default()
ref = Image.open('ref_native.png').convert('RGBA'); canvas = Image.new('RGBA', (64, 64), (0, 0, 0, 0)); canvas.paste(ref, (18, 1))
panels = [('reference (other user), side', canvas), ('front', Image.open('out/knight_front_1x.png')), ('back', Image.open('out/knight_back_1x.png'))]
strip = Image.new('RGB', (W * 3, 28 + W + 24 + 70), BG); d = ImageDraw.Draw(strip)
for i, (label, im) in enumerate(panels):
    im = im.convert('RGBA'); big = im.resize((W, W), Image.NEAREST); strip.paste(big, (i * W, 28), big); d.text((i * W + 8, 5), label, fill='#14161c', font=font)
    strip.paste(im, (i * W + (W - 64) // 2, 28 + W + 24), im)
    if i: d.line([(i * W, 0), (i * W, strip.height)], fill='#5d6672', width=1)
d.text((8, 28 + W + 2), 'real size (64 px)', fill='#14161c', font=font)
strip.save('out/compare_strip_views.png'); print(strip.size)
