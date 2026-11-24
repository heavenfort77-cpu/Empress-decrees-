# Batch 17a: source images for the encoder. Usage: prep.py TEXDIR STAGE_SRC "skip names"
# desk = the PNG as painted (opaque sheets saved as RGB: their alpha is 255 everywhere); phone = at most 512 px (Lanczos); mut = mutant inputs.
import sys, os, glob
import numpy as np
from PIL import Image
T, S, skip = sys.argv[1], sys.argv[2], sys.argv[3].split()
os.makedirs(S + '/desk', exist_ok=True); os.makedirs(S + '/phone', exist_ok=True); os.makedirs(S + '/mut', exist_ok=True)
for f in sorted(glob.glob(T + '/*.png')):
    n = os.path.basename(f)[:-4]
    if n in skip: continue
    im = Image.open(f)
    im = im.convert('RGBA') if im.mode in ('RGBA', 'LA', 'P') else im.convert('RGB')
    if im.mode == 'RGBA' and np.asarray(im)[..., 3].min() == 255: im = im.convert('RGB')
    im.save(f'{S}/desk/{n}.png')
    w, h = im.size; k = min(1.0, 512 / max(w, h))
    (im.resize((int(w * k), int(h * k)), Image.LANCZOS) if k < 1 else im).save(f'{S}/phone/{n}.png')
    print('PREP', n, im.mode, im.size)
a = np.asarray(Image.open(f'{S}/desk/hall_wall.png').convert('RGB')).copy(); Image.fromarray(a[..., ::-1].copy()).save(f'{S}/mut/swap__hall_wall.png')
Image.open(f'{S}/desk/smoke_card.png').convert('RGB').save(f'{S}/mut/noalpha__smoke_card.png')
p = np.asarray(Image.open(f'{S}/desk/hall_floor.png').convert('RGB')).astype(int); Image.fromarray(((p // 64) * 64 + 32).astype(np.uint8)).save(f'{S}/mut/poster__hall_floor.png')
