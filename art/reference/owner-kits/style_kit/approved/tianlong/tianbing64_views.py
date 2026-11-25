"""天兵 64x64 (phone rung): four views and the halberd thrust, redrawn at 64.
Not a bitmap resize: the 96 part polygons are re-plotted on the 64 grid (x mirrored round axis 31.5, feet on row 61)
and rasterised natively, with detail settings retuned for 64. Run: python3 tianbing64_views.py -> out/v64_*
"""
import math
import numpy as np
from PIL import Image, ImageDraw
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG64 = {
    "K": 59 / 90,               # geometry ratio: 96 span rows 1-91 -> 64 rows 1-60
    "FEET_ROW": 60,             # 96 feet row 91 -> 60 (outline on 61, feet gap 2)
    "LIGHT_BAND": 1, "SMALL_REGION": 53, "RIVET_STEP": 4,
    "STUD_KEEP": 1.0,           # share of the 96 studs kept (1.0 = all)
}
K = CONFIG64["K"]


def X(x):
    """x on the 96 grid -> 64 grid, symmetric round the axis (47.5 -> 31.5) so mirrored pairs stay mirrored"""
    d = (x - 47.5) * K
    return 32 + math.floor(d) if d >= 0 else 31 - math.floor(-d)


def Y(y):
    return CONFIG64["FEET_ROW"] - int(math.floor((91 - y) * K + 0.5))


def Xf(x):
    return 31.5 + (x - 47.5) * K


def Yf(y):
    return CONFIG64["FEET_ROW"] - (91 - y) * K


def parts64(parts):
    return [(r, rp, [(X(x), Y(y)) for x, y in pl], fl) for r, rp, pl, fl in parts]


def details64(details):
    return [(k, X(x0), Y(y0), X(x1), Y(y1)) for k, x0, y0, x1, y1 in details]


def studs64(studs):
    seen, out = set(), []
    for k, x, y in studs:
        p = (X(x), Y(y))
        if p not in seen:
            seen.add(p); out.append((k,) + p)
    return out


def view64(v):
    w = dict(v)
    w["parts"] = parts64(v["parts"]); w["details"] = details64(v["details"]); w["studs"] = studs64(v["studs"])
    w["shoulder"] = (Xf(v["shoulder"][0]), Yf(v["shoulder"][1])); w["fist"] = (Xf(v["fist"][0]), Yf(v["fist"][1]))
    w["fx0"] = v["fist"][0]   # the 96 shaft column, for the smear source points
    return w


_orig_head = V.spear_head


def spear_head64(fx, fy, size):
    rel = _orig_head(0, 2, size)   # offsets round the fist on the 96 grid
    return [(r, rp, [(int(round(fx + x * K)), int(round(fy - 2 * K + y * K))) for x, y in pl], fl) for r, rp, pl, fl in rel]


def smear64(view, kind, frm, to):
    C = V.CONFIG["CANVAS"]
    ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if kind == "streak":
        fx0 = view["fx0"]   # the 96 shaft column
        for pt, col in (((fx0, 2), V.CONFIG["SMEAR"][0]), ((fx0 + 12, 5), V.CONFIG["SMEAR"][1]), ((fx0 + 8, 26), V.CONFIG["SMEAR"][1])):
            p = (Xf(pt[0]), Yf(pt[1]))
            a = V.apply_ops(frm[0], *p); b = V.apply_ops(to[0], *p)
            d.line([V.to_canvas(view, *a), V.to_canvas(view, *b)], fill=col, width=1)
        if V.CONFIG.get("TIP_BURST"):
            tx, ty = V.apply_ops(to[0], Xf(fx0), Yf(2))
            for k in range(8):
                ang = math.radians(k * 45 + 22.5); r0, r1 = (3, 6) if k % 2 == 0 else (3, 5)
                p0 = (tx + r0 * math.cos(ang), ty + r0 * math.sin(ang)); p1 = (tx + r1 * math.cos(ang), ty + r1 * math.sin(ang))
                d.line([V.to_canvas(view, *p0), V.to_canvas(view, *p1)], fill=V.CONFIG["SMEAR"][0] if k % 2 == 0 else V.CONFIG["SMEAR"][1], width=1)
    elif kind == "burst":
        fx, fy = to[1]
        for k in range(8):
            ang = math.radians(k * 45 + 22.5)
            r0, r1 = (8, 12) if k % 2 == 0 else (8, 10)
            a = (fx + r0 * math.cos(ang), fy - 1 + r0 * math.sin(ang)); b = (fx + r1 * math.cos(ang), fy - 1 + r1 * math.sin(ang))
            d.line([V.to_canvas(view, *a), V.to_canvas(view, *b)], fill=V.CONFIG["SMEAR"][0] if k % 2 == 0 else V.CONFIG["SMEAR"][1], width=1)
    return np.asarray(ov)


def setup():
    V.CONFIG.update({
        "N": 64, "CANVAS": 150, "OFF": (43, 32),
        "HIP": (Y(55), Y(67), X(31), X(41) + 1), "FEET_ROWS": (Y(86) - 1, 63), "TOE_ROWS": (Y(87), Y(91)),
        "HEAD_ROWS": (Y(14), Y(31)), "HEIGHT": (56, 62), "FEET_GAP": 2, "PREFIX": "v64",
        "SCALE_GIF": 3, "SCALE_LINEUP": 4,
    })
    for key in ("ATTACK_FRONT", "ATTACK_SIDE"):
        V.CONFIG[key] = [(n, dy, arm, (int(round(sx * K)), int(round(sy * K))), hal, ms, sm)
                         for n, dy, arm, (sx, sy), hal, ms, sm in V.CONFIG[key]]
    F.CONFIG.update({"LIGHT_BAND": CONFIG64["LIGHT_BAND"], "SMALL_REGION": CONFIG64["SMALL_REGION"],
                     "RIVET_STEP": CONFIG64["RIVET_STEP"]})
    for name in list(V.VIEWS):
        V.VIEWS[name] = view64(V.VIEWS[name])
    V.spear_head = spear_head64
    V.smear = smear64


if __name__ == "__main__":
    setup()
    V.main()
