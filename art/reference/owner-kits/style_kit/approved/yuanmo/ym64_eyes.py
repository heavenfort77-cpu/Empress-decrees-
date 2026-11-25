"""猿魔 at 64: the 96 eyes are 3x3 blocks; the native replot left 1 px slivers (4 v1 px) that do not read. This stamps a fixed 2x2 eye at 64
(3 x #ffcf40 plus one #fff3b0 catch-light at top-left) at the two eye positions found in the front view, then rebuilds the lineup.
Run after yuanmo_views.py <stage> 64:  python3 ym64_eyes.py <stage>   (keeps ym<stage>_64_idle_front_1x_v1.png as the unpatched backup)"""
import sys, shutil
import numpy as np
from PIL import Image
CFG = {"V1": (0xff, 0xcf, 0x40), "GLOW": (0xff, 0xf3, 0xb0), "BG": (52, 56, 68)}
st = sys.argv[1] if len(sys.argv) > 1 else "1"
p = f"out/ym{st}_64_idle_front_1x.png"
bak = p.replace("_1x.png", "_v1_1x.png")
try: open(bak, "rb").close()
except FileNotFoundError: shutil.copy(p, bak)
a = np.asarray(Image.open(bak).convert("RGBA")).copy()
m = (a[..., :3] == np.array(CFG["V1"])).all(2) & (a[..., 3] > 0)
ys, xs = np.nonzero(m)
left = xs <= xs.min() + 2
x_l, x_r = xs[left].min(), xs[~left].min()
y0 = ys.min()
for x0 in (x_l, x_r):
    for dy in (0, 1):
        for dx in (0, 1): a[y0 + dy, x0 + dx] = CFG["V1"] + (255,)
    a[y0, x0] = CFG["GLOW"] + (255,)
Image.fromarray(a).save(p)
views = [Image.open(f"out/ym{st}_64_idle_{v}_1x.png").convert("RGBA") for v in ("front", "left", "back", "right")]
L = Image.new("RGBA", (64 * 4 + 30, 64), CFG["BG"] + (255,))
for i, v in enumerate(views): L.alpha_composite(v, (i * 74, 0))
L.save(f"out/ym{st}_64_lineup_1x.png"); L.resize((L.width * 4, L.height * 4), Image.NEAREST).save(f"out/ym{st}_64_lineup_4x.png")
print("eyes at", (x_l, y0), (x_r, y0), "PASS")
