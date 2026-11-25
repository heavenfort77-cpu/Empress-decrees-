"""剑仙 array effect sample: the four blades standing point-up, tassel end on the ground line, at the corners of a diamond round the suit, joined by a dashed
silver-white qi line. The suit stands with its hand empty (the held sword is one of the four) and no floating fan.
Run: python3 jianxian_array.py -> out/jx_array_{1x,4x}.png (pass/fail only)"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
import tianbing96_v5 as F, tianbing96_views as V, jianxian96 as J, jianxian_views as JV

CONFIG = {"W": 192, "H": 176, "GROUND": 150,
          "TIPS": {"dingfeng": (50, 132), "yinfeng": (142, 132), "guifeng": (22, 166), "duanfeng": (170, 166)},   # where each tip meets the ground
          "BACK": ("dingfeng", "yinfeng"), "LINE": ["#c6cde2", "#7c8499"], "GLOW": "#ffffff"}


def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


SIZE = ["96"]


def casting_suit():
    JV.setup(SIZE[0])
    if SIZE[0] == "64":
        import tianbing64_views as T64
        src = T64.view64(J.VIEW)
        thumb0 = (T64.X(19), T64.Y(33)); gl = T64.Y(1)
    else:
        src = J.VIEW; thumb0 = (19, 33); gl = 1
    parts = [p for p in src["parts"] if p[0] not in JV.FLOAT_R and p[0] != "sword"]
    parts = [p for p in parts if not (p[0] == "hand" and p[1] == "s" and p[2][0] == thumb0)]     # thumb that wrapped the grip
    v = dict(src); v["parts"] = parts
    v["details"] = [d for d in src["details"] if not (d[0] == "glow" and d[2] == gl)]
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = J.CONFIG["PAL"]; F.CONFIG["RAMP"] = J.CONFIG["RAMP"]
    try:
        return V.crop96(V.build(v, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def paste(canvas, img, x, y):
    im = Image.fromarray(img, "RGBA"); canvas.alpha_composite(im, (x, y))


def build():
    c = CONFIG
    k = 1.0 if SIZE[0] == "96" else 59 / 90
    pre = "jx" if SIZE[0] == "96" else "jx64"
    W, H, G = (c["W"], c["H"], c["GROUND"]) if k == 1.0 else (128, 118, 100)
    cv = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tips = c["TIPS"] if k == 1.0 else {n: (round(x * k), round(y * k)) for n, (x, y) in c["TIPS"].items()}
    c = dict(c, W=W, H=H, GROUND=G)
    # dashed qi line round the four tips (ground level)
    order = ["dingfeng", "yinfeng", "duanfeng", "guifeng"]
    px = np.zeros((c["H"], c["W"], 4), np.uint8)
    n = 0
    for i in range(4):
        (x0, y0), (x1, y1) = tips[order[i]], tips[order[(i + 1) % 4]]
        L = int(max(abs(x1 - x0), abs(y1 - y0)))
        for t in range(L + 1):
            x = round(x0 + (x1 - x0) * t / L); y = round(y0 + (y1 - y0) * t / L)
            if n % 3 != 2:
                px[y, x] = hexrgb(c["LINE"][0] if n % 2 == 0 else c["LINE"][1]) + (255,)
            n += 1
    cv.alpha_composite(Image.fromarray(px, "RGBA"))
    blades = {n_: np.asarray(Image.open(f"out/{pre}_blade_{n_}_1x.png").convert("RGBA")) for n_ in tips}      # point up, tassel end on the ground line
    suit = casting_suit()
    def put(n_):
        b = blades[n_]; x, y = tips[n_]
        A = b[..., 3] > 0; tipy = np.where(A.any(axis=1))[0].max(); tipx = int(np.where(A[tipy])[0].mean())
        paste(cv, b, x - tipx, y - tipy)
    for n_ in c["BACK"]: put(n_)
    paste(cv, suit, c["W"] // 2 - suit.shape[1] // 2, c["GROUND"] - (91 if k == 1.0 else 60))
    for n_ in tips:
        if n_ not in c["BACK"]: put(n_)
    return np.asarray(cv)


if __name__ == "__main__":
    SIZE[0] = sys.argv[1] if len(sys.argv) > 1 else "96"
    pre = "jx" if SIZE[0] == "96" else "jx64"
    a = build()
    A = a[..., 3] > 0
    ys, xs = np.where(A); print("size", a.shape[1], "x", a.shape[0], "content", xs.max() - xs.min() + 1, "x", ys.max() - ys.min() + 1,
                                  "colours", len(set(map(tuple, a[A][:, :3]))))
    Image.fromarray(a, "RGBA").save(f"out/{pre}_array_1x.png")
    bg = Image.new("RGBA", (a.shape[1], a.shape[0]), (58, 62, 72, 255)); bg.alpha_composite(Image.fromarray(a, "RGBA"))
    bg.resize((a.shape[1] * 4, a.shape[0] * 4), Image.NEAREST).save(f"out/{pre}_array_4x.png")
    ok = xs.min() > 0 and ys.min() > 0 and xs.max() < a.shape[1] - 1 and ys.max() < a.shape[0] - 1
    print("PASS" if ok else "FAILING: content touches the canvas edge")
