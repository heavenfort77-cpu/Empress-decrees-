"""剑仙 standalone blade sprites (array blades). Sample: 断锋, upright, the same drawing as the held sword plus its own grip.
Run: python3 jianxian_blade.py -> out/jx_blade_duanfeng_{1x,8x}.png (pass/fail only)"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F, tianbing96_views as V, jianxian96 as J, jianxian_views as JV


SIZE = ["96"]
PREFIX = ["jx"]


def render(parts, details, studs):
    if SIZE[0] == "64":
        import tianbing64_views as T64
        parts, details, studs = T64.parts64(parts), T64.details64(details), T64.studs64(studs)
    else:
        JV.setup()
    view = dict(parts=parts, details=details, studs=studs, flip=False, shoulder=(18, 40), fist=(18, 40), hipfix=False)
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = J.CONFIG["PAL"]; F.CONFIG["RAMP"] = J.CONFIG["RAMP"]
    try:
        img = V.crop96(V.build(view, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep
    A = img[..., 3] > 0; ys, xs = np.where(A)
    return img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def st(poly, y0, k, dy=0):
    """stretch a polygon vertically about y0 (blade parts only), then move down by dy"""
    return [(x, round(y0 - (y0 - y) * k, 1) + dy) for x, y in poly]


def hilt(reg, y, dy=0):
    """short grip, pommel cap and a short tassel, starting under the guard at y"""
    return [(reg, "b", [(17, y), (19, y), (19, y + 6), (17, y + 6)], True),
            (reg, "s", [(16, y + 6), (20, y + 6), (19, y + 9), (17, y + 9)], False),
            (reg, "b", [(17, y + 9), (19, y + 9), (19, y + 17), (17, y + 17)], True)]


def duanfeng():
    k, y0, dy = 1.4, 32, 14
    ps = [("g", "s", st([(15, 31), (21, 31), (21, 22), (20, 10), (18, 1), (16, 10), (15, 22)], y0, k, dy), False),
          ("g", "v", st([(17.5, 5), (18.5, 5), (18.5, 29), (17.5, 29)], y0, k, dy), True),
          ("g", "s", st([(8, 31), (13, 29), (23, 29), (28, 31), (28, 34), (23, 32), (13, 32), (8, 34)], y0, 1.0, dy), False)]
    ps += hilt("g", 34 + dy)
    return render(ps, [("glow", 18, 1 + 2, 18, 1 + 3), ("out", 16, 36 + dy, 20, 36 + dy), ("out", 16, 38 + dy, 20, 38 + dy)],
                  [("s3", 17, 12 + dy), ("s3", 19, 24 + dy), ("b3", 17, 36 + dy)])


def others():
    """定锋, 引锋, 归锋 upright: 44 px of blade above the guard (guard at y 44, tip at y 0), short grip"""
    k, y0 = 44 / 32, 44
    S = lambda p: st(p, y0, k)
    B = {"dingfeng": [("g", "s", S([(15, 45), (21, 45), (22, 36), (21, 24), (18, 12), (15, 24), (14, 36)]), False),
                      ("g", "f", S([(17.5, 20), (18.5, 20), (18.5, 40), (17.5, 40)]), True),
                      ("g", "s", [(10, 47), (11, 44), (25, 44), (26, 47), (24, 47), (12, 47)], False)],
         "yinfeng": [("g", "s", S([(16, 45), (20, 45), (20, 25), (22, 20), (26, 16), (27, 12), (22, 14), (17, 18), (16, 25)]), False),
                     ("g", "f", S([(17.5, 28), (18.5, 28), (18.5, 40), (17.5, 40)]), True),
                     ("g", "s", [(10, 49), (12, 44), (24, 44), (26, 49), (24, 47), (12, 47)], False)],
         "guifeng": [("g", "s", S([(16, 45), (20, 45), (20, 18), (18, 12), (16, 18)]), False),
                     ("g", "s", S([(12, 27), (15, 23), (21, 23), (24, 27), (24, 33), (21, 37), (15, 37), (12, 33)]), False),
                     ("g", "f", S([(14, 28), (16, 25), (20, 25), (22, 28), (22, 32), (20, 35), (16, 35), (14, 32)]), True),
                     ("g", "s", S([(16, 45), (20, 45), (20, 18), (18, 12), (16, 18)]), False),
                     ("g", "s", [(12, 43), (24, 43), (27, 46), (24, 49), (12, 49), (9, 46)], False)]}
    out = {}
    for name, ps in B.items():
        out[name] = render(ps + hilt("g", 46), [("out", 17, 48, 19, 48), ("out", 17, 50, 19, 50)], [("s3", 17, 30), ("b3", 18, 56)])
    return out


if __name__ == "__main__":
    c = duanfeng()
    Image.fromarray(c, "RGBA").save("out/jx_blade_duanfeng_1x.png")
    bg = Image.new("RGBA", (c.shape[1], c.shape[0]), (58, 62, 72, 255)); bg.alpha_composite(Image.fromarray(c, "RGBA"))
    bg.resize((c.shape[1] * 8, c.shape[0] * 8), Image.NEAREST).save("out/jx_blade_duanfeng_8x.png")
    A = c[..., 3] > 0
    from scipy import ndimage
    n = ndimage.label(A, structure=np.ones((3, 3)))[1]
    cols = len(set(map(tuple, c[A][:, :3])))
    print("size", c.shape[1], "x", c.shape[0], "colours", cols, "pieces", n)
    print("PASS" if n == 1 else "FAILING: pieces %d" % n)


def sheet():
    d = {"duanfeng": duanfeng(), **others()}
    names = ["duanfeng", "dingfeng", "yinfeng", "guifeng"]
    H = max(v.shape[0] for v in d.values()); W = sum(v.shape[1] + 4 for v in d.values())
    bg = Image.new("RGBA", (W, H + 2), (58, 62, 72, 255)); x = 2
    for n in names:
        v = d[n]; Image.fromarray(v, "RGBA").save(f"out/{PREFIX[0]}_blade_{n}_1x.png")
        bg.alpha_composite(Image.fromarray(v, "RGBA"), (x, H + 1 - v.shape[0])); x += v.shape[1] + 4
    bg.resize((W * 6, (H + 2) * 6), Image.NEAREST).save(f"out/{PREFIX[0]}_blades_6x.png")
    from scipy import ndimage
    bad = []
    for n in names:
        A = d[n][..., 3] > 0
        k = ndimage.label(A, structure=np.ones((3, 3)))[1]
        print(n, d[n].shape[1], "x", d[n].shape[0], "colours", len(set(map(tuple, d[n][A][:, :3]))), "pieces", k)
        if k != 1: bad.append(n)
    print("PASS" if not bad else "FAILING: " + ", ".join(bad))
