"""One GIF with the attack in all four views side by side. Usage: python3 combo_gif.py [96|64]"""
import sys
import numpy as np
from PIL import Image, ImageDraw
import tianbing96_views as V

size = sys.argv[1] if len(sys.argv) > 1 else "96"
if size == "64":
    import tianbing64_views as T64
    T64.setup()
S = 2 if size == "96" else 3
C = V.CONFIG["CANVAS"]
allf = {}
for name in V.ORDER:
    view = V.VIEWS[name]; spec = V.CONFIG[view["attack"]]; frames, ms, wind = [], [], None
    for fname, dy, arm, shf, hal, dur, sm in spec:
        T, fist, arm_ops, hide, extra = V.ops_for(view, dy, arm, shf, hal)
        if fname == "windup":
            wind = (arm_ops, fist, hal)
        moving = dy or arm or hal or shf != (0, 0)
        img = V.build(view, T if moving else None, hide=hide, extra=extra, extra_front=view.get("spear_front", True))
        if sm:
            img = V.composite(img, V.smear(view, sm, wind, (arm_ops, fist, hal)), over_in_front=(sm == "burst" and view.get("spear_front", True)))
        frames.append(img); ms.append(dur)
    allf[name] = (frames, ms)
A = np.zeros((C, C), bool)
for fr, _ in allf.values():
    for f in fr:
        A |= f[..., 3] > 0
ys, xs = np.nonzero(A); pad = 3
y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
w, h = x1 - x0, y1 - y0; lab = 12
out = []
for i in range(len(allf["front"][1])):
    sh = Image.new("RGBA", (w * 4, h + lab), (58, 62, 72, 255)); d = ImageDraw.Draw(sh)
    for k, name in enumerate(V.ORDER):
        sh.alpha_composite(Image.fromarray(allf[name][0][i], "RGBA").crop((x0, y0, x1, y1)), (k * w, lab))
        d.text((k * w + 3, 1), name, fill=(200, 210, 220, 255))
    out.append(sh.resize((sh.width * S, sh.height * S), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
dur = list(allf["front"][1]); dur[0] = 400
fn = f"out/tianbing{size}_thrust_4views_{S}x.gif"
out[0].save(fn, save_all=True, append_images=out[1:], duration=dur, loop=0, disposal=2)
print(fn, out[0].size)
