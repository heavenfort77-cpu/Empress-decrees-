# Shape match per frame: A's opaque mask vs B's alpha >= 0.5 box-downsampled to 1x (136x104). Reports IoU per frame and the mean.
import numpy as np
from PIL import Image
A = np.array(Image.open('/home/claude/vfx/out/A_slash_baked.png'))[..., 3] > 0; r = []
for f in range(1, 18):
    a = A[(f // 5) * 104:(f // 5 + 1) * 104, (f % 5) * 136:(f % 5 + 1) * 136]
    b = np.array(Image.open(f'/home/claude/vfx/out/Bf/f{f}.png'))[..., 3].reshape(104, 2, 136, 2).mean((1, 3)) >= 128
    u = (a | b).sum(); r.append(round((a & b).sum() / u, 2) if u else 1.0)
print('IoU per frame', r, 'mean', round(float(np.mean(r)), 2))
