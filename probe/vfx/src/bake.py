# Bake a pixelfx sheet per pixel-vfx rule 2(b): hard alpha cut at 0.5, snap kept pixels to a ramp in OKLab,
# orphan merge (a pixel with no same-colour 4-neighbour that touches other effect pixels takes their most common colour;
# isolated sparks stay). Gate: 0 pixels with 0 < alpha < 255. Usage: bake.py in.png in.json out.png ramp_hex,...
import sys, json, numpy as np
from PIL import Image
sys.path.insert(0, '/home/claude/vfx/scripts')
from oklab import rgb2lab, hx
src, meta, dst, ramp = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(',')
im = np.array(Image.open(src).convert('RGBA')); m = json.load(open(meta))['meta']['pixelfx']
fw, fh = m['frameSize']; cols = m['columns']; n = m['frames']
R = np.array([hx(h) for h in ramp], np.uint8); RL = rgb2lab(R)
out = np.zeros_like(im); stats = []
for f in range(n):
    x0, y0 = (f % cols) * fw, (f // cols) * fh
    fr = im[y0:y0 + fh, x0:x0 + fw]; keep = fr[..., 3] >= 128
    idx = np.full((fh, fw), -1, int)
    if keep.any():
        lab = rgb2lab(fr[keep][:, :3]); d = ((lab[:, None, :] - RL[None]) ** 2).sum(-1); idx[keep] = d.argmin(1)
    orph0 = orph = spark = 0; new = idx.copy()
    for y, x in zip(*np.nonzero(idx >= 0)):
        nb = [idx[yy, xx] for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)) if 0 <= yy < fh and 0 <= xx < fw and idx[yy, xx] >= 0]
        if idx[y, x] in nb: continue
        orph0 += 1
        if not nb: spark += 1; continue
        new[y, x] = max(set(nb), key=nb.count)
    idx = new
    for y, x in zip(*np.nonzero(idx >= 0)):
        nb = [idx[yy, xx] for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)) if 0 <= yy < fh and 0 <= xx < fw and idx[yy, xx] >= 0]
        if nb and idx[y, x] not in nb: orph += 1
    o = out[y0:y0 + fh, x0:x0 + fw]; k = idx >= 0
    o[k, :3] = R[idx[k]]; o[k, 3] = 255
    tot = int(k.sum()); stats.append((f, tot, orph0, orph, spark, len(set(idx[k].tolist()))))
semi = int(((out[..., 3] > 0) & (out[..., 3] < 255)).sum())
Image.fromarray(out).save(dst)
pk = max(stats, key=lambda s: s[1]); f, tot, o0, o1, sp, nc = pk
print(f'{dst} frames {n} peak frame {f} px {tot} colours {nc} orphans before {100*o0/max(tot,1):.1f}% after {100*o1/max(tot,1):.1f}% sparks {100*sp/max(tot,1):.1f}%')
print(f'GATE semi-transparent pixels {semi} ->', 'PASS' if semi == 0 else 'FAIL')
print('opaque px per frame', [s[1] for s in stats])
