#!/usr/bin/env python3
"""Cut the side 3D render out of its background and base, face it right, and hand it to klad pixelize at sprite size."""
import subprocess, shutil, sys
import numpy as np
from PIL import Image
K = '/home/claude/klad/src/target/linux/release/klad'
SRC = '/mnt/user-data/uploads/79bfa46a-image.png'; H = 58
HEX = {'ink': '#1b1d2e', 'steel-1': '#3a4560', 'steel-2': '#5f6d8c', 'steel-3': '#8f9db8', 'steel-4': '#c5cfdd', 'steel-5': '#f4f7fb', 'brass-1': '#8c5a1e',
       'brass-2': '#d99a2b', 'brass-3': '#ffd765', 'cloth-1': '#25503a', 'cloth-2': '#3f8454', 'glow-1': '#a8f4ee', 'leather-1': '#b8403a'}
a = np.array(Image.open(SRC).convert('RGB')).astype(int); bg = a[5, 5]
fig = np.abs(a - bg).sum(-1) > 40
warm = a[..., 0] - a[..., 2]; yy = np.arange(a.shape[0])[:, None]
fig &= ~((warm > 8) & (warm < 60) & (yy > 1650))                       # the brown base and its shadow
ys = np.nonzero(fig.sum(1) > 6)[0]; top = ys.min()
rows = fig.sum(1); bot = max(y for y in ys if y < 1960 and rows[y] > 150)   # last wide row of the soles
fig[bot + 1:] = False; xs = np.nonzero(fig.any(0))[0]
rgba = np.dstack([a, fig * 255]).astype('uint8')[top:bot + 1, xs.min():xs.max() + 1][:, ::-1]
Image.fromarray(rgba).save('side/render_cut.png'); print('cut', rgba.shape, 'rows', top, bot)
b = 'side/render_px.klad'; shutil.rmtree(b, ignore_errors=True); subprocess.run([K, 'new', b, '--pixel', '64x64'])
for n, h in HEX.items(): subprocess.run([K, 'palette', b, '--add', h, '--name', n], capture_output=True)
w = round(rgba.shape[1] * H / rgba.shape[0])
r = subprocess.run([K, 'pixelize', b, '--image', 'side/render_cut.png', '--to', 'l1', '--size', str(H), '--at', f'{(64 - w) // 2},{61 - H}'], capture_output=True, text=True); print(r.stdout[:200], r.stderr[:200])
subprocess.run([K, 'export', b, '--scale', '1', '-o', 'side/render_px_1x.png'], capture_output=True)
code = {v.lstrip('#'): k for k, v in zip('#12345abcgG*r', HEX.values())}
im = Image.open('side/render_px_1x.png').convert('RGBA')
for y in range(64):
    row = ''.join('.' if im.getpixel((x, y))[3] < 128 else code.get('%02x%02x%02x' % im.getpixel((x, y))[:3], '?') for x in range(64))
    if row.strip('.'): print('%02d %s' % (y, row[14:52]))
