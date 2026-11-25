#!/usr/bin/env python3
"""Review sheet for the W1b props: images side by side in rows, each scaled to the row height, with a label strip under each.
Usage: python3 w1b_sheet.py OUT.png ROWH "label=path[@crop x0,y0,x1,y1]" ... ("|" alone starts a new row)."""
import sys
from PIL import Image, ImageDraw
OUT, RH = sys.argv[1], int(sys.argv[2]); rows = [[]]
for a in sys.argv[3:]:
    if a == '|': rows.append([]); continue
    lab, p = a.split('=', 1); crop = None
    if '@' in p: p, c = p.split('@'); crop = tuple(int(v) for v in c.split(','))
    im = Image.open(p).convert('RGB')
    if crop: im = im.crop(crop)
    rows[-1].append((lab, im.resize((max(1, round(im.width * RH / im.height)), RH))))
W = max(sum(im.width + 6 for _, im in r) for r in rows); H = len(rows) * (RH + 22)
o = Image.new('RGB', (W, H), (24, 20, 26)); d = ImageDraw.Draw(o)
for j, r in enumerate(rows):
    x = 0
    for lab, im in r:
        o.paste(im, (x, j * (RH + 22))); d.text((x + 4, j * (RH + 22) + RH + 4), lab, fill=(230, 220, 200)); x += im.width + 6
o.save(OUT); print(OUT, o.size)
