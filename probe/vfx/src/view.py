# Side-by-side check: A frames (nearest x2) and B frames on the floor's mean red, frames 1..17 in rows of 6.
import sys, numpy as np
from PIL import Image
A = Image.open('out/A_slash_baked.png').convert('RGBA'); FW, FH, C = 136, 104, 5
fr = list(range(1, 18)); W, H = FW * 2, FH * 2
out = Image.new('RGBA', (W * 6, H * 2 * 3), (116, 49, 34, 255))
for i, f in enumerate(fr):
    a = A.crop(((f % C) * FW, (f // C) * FH, (f % C + 1) * FW, (f // C + 1) * FH)).resize((W, H), Image.NEAREST)
    b = Image.open(f'out/Bf/f{f}.png').convert('RGBA')
    x, y = (i % 6) * W, (i // 6) * H * 2
    out.alpha_composite(a, (x, y)); out.alpha_composite(b, (x, y + H))
out.save(sys.argv[1])
