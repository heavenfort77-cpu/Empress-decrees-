#!/usr/bin/env python3
"""Contact sheet of every frame at 3x, and 1x sprite sheets per animation."""
from PIL import Image, ImageDraw, ImageFont
BG = '#7d838c'; S = 3; C = 96 * S
try: font = ImageFont.load_default(size=16)
except TypeError: font = ImageFont.load_default()
sheet = Image.new('RGB', (6 * C, 3 * (C + 22)), BG); d = ImageDraw.Draw(sheet)
def put(anim, i, col, row):
    im = Image.open(f'out/{anim}_{i}.png').convert('RGBA').resize((C, C), Image.NEAREST); sheet.paste(im, (col * C, row * (C + 22) + 22), im)
d.text((6, 3), 'idle (4 frames)', fill='#14161c', font=font); [put('idle', i, i, 0) for i in range(4)]
d.text((4 * C + 6, 3), 'battle pose', fill='#14161c', font=font); put('battle', 0, 4, 0)
d.text((6, C + 22 + 3), 'walk left (6 frames)', fill='#14161c', font=font); [put('walk_left', i, i, 1) for i in range(6)]
d.text((6, 2 * (C + 22) + 3), 'walk right (6 frames)', fill='#14161c', font=font); [put('walk_right', i, i, 2) for i in range(6)]
sheet.save('out/knight_2b_animation_sheet_3x.png')
for anim, n in (('idle', 4), ('walk_left', 6), ('walk_right', 6), ('battle', 1)):
    s = Image.new('RGBA', (96 * n, 96), (0, 0, 0, 0))
    for i in range(n): s.paste(Image.open(f'out/{anim}_{i}.png').convert('RGBA'), (96 * i, 0))
    s.save(f'out/{anim}_sheet_1x.png')
