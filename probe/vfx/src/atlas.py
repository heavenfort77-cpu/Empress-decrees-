# Pack frames 1..17 of A (1x, baked) and B (2x, klad) into atlases over one shared crop box (union of both effects' pixels, 1x units),
# 4 columns x 5 rows (B stays within the 1024 texture cap). Writes out/probe/fx_a.png, fx_b.png and fx.json (crop box, pivot, texel metres). Gate: A atlas 0 semi-transparent px.
import json, numpy as np
from PIL import Image
FW, FH, C, FR = 136, 104, 5, list(range(1, 18))
A = np.array(Image.open('out/A_slash_baked.png'))
Bs = {f: np.array(Image.open(f'out/Bf/f{f}.png')) for f in FR}
m = np.zeros((FH, FW), bool)
for f in FR:
    m |= A[(f // C) * FH:(f // C + 1) * FH, (f % C) * FW:(f % C + 1) * FW, 3] > 0
    m |= Bs[f][..., 3].reshape(FH, 2, FW, 2).max((1, 3)) > 8
ys, xs = np.nonzero(m); x0, x1, y0, y1 = xs.min() - 1, xs.max() + 2, ys.min() - 1, ys.max() + 2
cw, ch = int(x1 - x0), int(y1 - y0); COLS, ROWS = 4, 5
a = np.zeros((ROWS * ch, COLS * cw, 4), np.uint8); b = np.zeros((ROWS * ch * 2, COLS * cw * 2, 4), np.uint8)
for i, f in enumerate(FR):
    cx, cy = i % COLS, i // COLS
    a[cy * ch:(cy + 1) * ch, cx * cw:(cx + 1) * cw] = A[(f // C) * FH + y0:(f // C) * FH + y1, (f % C) * FW + x0:(f % C) * FW + x1]
    b[cy * ch * 2:(cy + 1) * ch * 2, cx * cw * 2:(cx + 1) * cw * 2] = Bs[f][y0 * 2:y1 * 2, x0 * 2:x1 * 2]
import os; os.makedirs('out/probe', exist_ok=True)
Image.fromarray(a).save('out/probe/fx_a.png', optimize=True); Image.fromarray(b).save('out/probe/fx_b.png', optimize=True)
semi = int(((a[..., 3] > 0) & (a[..., 3] < 255)).sum()); semib = int(((b[..., 3] > 0) & (b[..., 3] < 255)).sum())
cols = len({tuple(p) for p in a[a[..., 3] > 0][:, :3]})
meta = dict(frames=len(FR), fps=30, cols=COLS, rows=ROWS, cellPx=[cw, ch], crop=[int(x0), int(y0)], pivotPx=[int(44 - x0), int(92 - y0)], texelM=round(2.05 / 38, 5),
            a=dict(size=list(a.shape[1::-1]), colours=cols, semi=semi), b=dict(size=list(b.shape[1::-1]), semi=semib))
json.dump(meta, open('out/probe/fx.json', 'w'), indent=1); print(meta)
print('GATE A semi-transparent px', semi, 'PASS' if semi == 0 else 'FAIL')
