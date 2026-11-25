"""剑仙 sword ride (dash) sample frame, right view: the suit stands on 断锋 laid flat, tip forward and tassel trailing, the held sword
having left the hand; the other three swords stay in the fan behind the back; a thin silver line marks the whole path behind it.
Blade sprite is the approved art rotated 90 degrees as data (no resizing). One frame, no animation yet.
Run: python3 jianxian_ride.py -> out/jx_ride_{1x,4x}.png (pass/fail only)"""
import numpy as np
from PIL import Image
from scipy import ndimage
import tianbing96_v5 as F, tianbing96_views as V, jianxian96 as J, jianxian_views as JV

CONFIG = {"W": 192, "H": 140, "SUIT_AT": (62, 8), "GAP": 1, "LINE": ["#c6cde2", "#7c8499"], "LINE_LEN": 52, "SHADOW": "#4a5063"}


def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def suit_right():
    JV.setup()
    v = dict(JV.side_right())
    v["parts"] = [p for p in v["parts"] if p[0] != "sword"]
    v["details"] = [d for d in v["details"] if d[0] != "out" or d[1] < 50]
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = J.CONFIG["PAL"]; F.CONFIG["RAMP"] = J.CONFIG["RAMP"]
    try:
        return V.crop96(V.build(v, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def build():
    c = CONFIG
    cv = Image.new("RGBA", (c["W"], c["H"]), (0, 0, 0, 0))
    suit = suit_right()
    A = suit[..., 3] > 0
    feet = np.where(A.any(axis=1))[0].max()                       # lowest suit row
    sx, sy = c["SUIT_AT"]
    blade = np.rot90(np.asarray(Image.open("out/jx_blade_duanfeng_1x.png").convert("RGBA")), k=-1)   # tip right, tassel left
    Ab = blade[..., 3] > 0
    top = np.where(Ab.any(axis=1))[0].min()
    # the blade's flat edge sits just under the soles; centre the blade body on the soles
    cols = np.where(A[feet - 1])[0]; mid = int(cols.mean())
    bx = sx + mid - 38
    colb = np.where(Ab[:, 38])[0]                                   # the blade body under the soles (not the guard)
    by = sy + feet + c["GAP"] - colb.min()
    px = np.zeros((c["H"], c["W"], 4), np.uint8)
    # path line behind the tassel, at blade level, and a dim ground shadow under it
    ymid = by + int(colb.mean())
    x0 = bx - 2
    for i in range(c["LINE_LEN"]):
        x = x0 - i
        if x >= 0 and i % 4 != 3:
            px[ymid, x] = hexrgb(c["LINE"][0] if i % 2 == 0 else c["LINE"][1]) + (255,)
    sh = by + blade.shape[0] + 6
    for x in range(bx + 8, bx + blade.shape[1] - 8):
        px[sh, x] = hexrgb(c["SHADOW"]) + (255,)
    cv.alpha_composite(Image.fromarray(px, "RGBA"))
    cv.alpha_composite(Image.fromarray(blade, "RGBA"), (bx, by))
    cv.alpha_composite(Image.fromarray(suit, "RGBA"), (sx, sy))
    return np.asarray(cv), (bx, by, blade.shape)


if __name__ == "__main__":
    a, info = build()
    A = a[..., 3] > 0
    ys, xs = np.where(A)
    lab, n = ndimage.label(A, structure=np.ones((3, 3)))
    k = int((np.bincount(lab.ravel())[1:] > 20).sum())               # pieces bigger than 20 px: suit+blade, ground shadow
    print("size", a.shape[1], "x", a.shape[0], "content", xs.max() - xs.min() + 1, "x", ys.max() - ys.min() + 1, "colours", len(set(map(tuple, a[A][:, :3]))), "pieces", k)
    Image.fromarray(a, "RGBA").save("out/jx_ride_1x.png")
    bg = Image.new("RGBA", (a.shape[1], a.shape[0]), (58, 62, 72, 255)); bg.alpha_composite(Image.fromarray(a, "RGBA"))
    bg.resize((a.shape[1] * 4, a.shape[0] * 4), Image.NEAREST).save("out/jx_ride_4x.png")
    edge = xs.min() == 0 or ys.min() == 0 or xs.max() == a.shape[1] - 1 or ys.max() == a.shape[0] - 1
    fails = []
    if edge: fails.append("content touches the canvas edge")
    # pieces: suit+blade must be one piece (the path line and shadow are separate by design: at most 3)
    if k > 2: fails.append(f"{k} big pieces (suit and blade should be one)")
    print("PASS" if not fails else "FAILING: " + "; ".join(fails))
