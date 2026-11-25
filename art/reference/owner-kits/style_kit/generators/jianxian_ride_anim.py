"""剑仙 sword ride (dash) animation at 96, all four views. The held sword leaves the hand and lies flat under the feet (断锋, the
approved sprite rotated as data); the suit sinks, launches, glides leaning forward and stops. The three floating swords swing out
behind and fan wide while moving. A three-line silver path trails behind the blade. Tip points toward the travel side (right in the data;
the left and back views are the mirrored data).
Run: python3 jianxian_ride_anim.py -> out/jx_ride_4views_2x.gif and out/jx_ride_sheet_1x.png (pass/fail only)
"""
import sys
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V
import jianxian_views as JV
import jianxian96 as J
import anim_runner as R

CONFIG = {
    # name, body dy, lean toward the tip (upper body only, legs stay planted), slide dx toward the tip, fan swing (deg, negative = back),
    # path length, arm swing back (deg), ms
    "RIDE": [("idle", 0, 0, 0, 0, 0, 0, 120), ("sink", 4, -6, 0, -8, 0, -6, 90), ("launch", 2, 14, 6, -28, 12, 8, 70),
             ("glide1", 0, 12, 16, -40, 34, 12, 90), ("glide2", 2, 7, 26, -46, 46, 26, 90), ("glide3", 0, 11, 34, -40, 46, 16, 90),
             ("stop", 2, -2, 40, -14, 18, -4, 160)],
    "HIP": (48, 58), "FEET_Y": 91,
    "PIVOT": {"front": (66, 44), "back": (66, 44), "right": (41, 43), "left": (41, 43)},
    "CX": {"front": 47, "back": 47, "right": 50, "left": 50},          # feet centre in data space
    "SHOULDER": {"front": {"armL": (28, 40), "hand": (28, 40), "armR": (69, 40), "handR": (69, 40)},
                 "back": {"armL": (28, 40), "hand": (28, 40), "armR": (69, 40), "handR": (69, 40)},
                 "right": {r: (50, 40) for r in ("armL", "armR", "hand", "handR")}, "left": {r: (50, 40) for r in ("armL", "armR", "hand", "handR")}},
    "COL": {"l0": "#7c8499", "l1": "#c6cde2", "l2": "#ffffff"},
}


SIZE = ["96"]
K64 = 59 / 90


def K():
    return 1.0 if SIZE[0] == "96" else K64


def P(pt):
    if SIZE[0] == "64":
        import tianbing64_views as T64
        return (T64.Xf(pt[0]), T64.Yf(pt[1]))
    return (float(pt[0]), float(pt[1]))


def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def kind(name): return "front" if name in ("front", "back") else "side"


def ops_for(name, dy, lean, dx, part="upper", arm=0, region=None):
    """legs only slide and dip; the skirt follows half the lean; everything above the hips leans about the hip joint"""
    ops = []
    hx, hy = P(CONFIG["HIP"])
    dx, dy = dx * K(), dy * K()
    if part == "arm" and arm:
        sh = P(CONFIG["SHOULDER"][name][region])
        ops.append(("rot", sh[0], sh[1], arm if region in ("armL", "hand") or kind(name) == "side" else -arm))
    if part in ("upper", "arm") and lean:
        ops.append(("rot", hx, hy, lean))
    elif part == "skirt" and lean:
        ops.append(("rot", hx, hy, lean * 0.5))
    ops.append(("mov", dx, dy))
    return ops


def overlay(name, dy, lean, dx, line, fan):
    col = CONFIG["COL"]
    blade = np.rot90(np.asarray(Image.open("out/jx_blade_duanfeng_1x.png" if SIZE[0] == "96" else "out/jx64_blade_duanfeng_1x.png").convert("RGBA")), k=-1)   # tip right (data space)

    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = np.zeros((C, C, 4), np.uint8)
        fx, fy = V.apply_ops(ops_for(name, dy, lean, dx, part="legs"), *P((CONFIG["CX"][name], CONFIG["FEET_Y"])))
        Ab = blade[..., 3] > 0
        colc = int(round(38 * K()))
        body_rows = np.where(Ab[:, colc])[0]
        bx = int(round(fx)) - colc
        by = int(round(fy)) + 1 - body_rows.min()
        for yy, xx in zip(*np.nonzero(Ab)):
            cx_, cy_ = V.to_canvas(view, bx + xx, by + yy)
            ov[cy_, cx_] = blade[yy, xx]
        ym = by + int(body_rows.mean())
        k_ = K(); o1, o2 = max(2, round(4 * k_)), max(4, round(8 * k_)); LL = int(line * k_)
        spec = ((0, LL, 5, 1, "l1"), (-o1, int(LL * 0.6), 6, 3, "l0"), (o1, int(LL * 0.6), 6, 3, "l0"),
                (-o2, int(LL * 0.3), 6, 2, "l1"), (o2, int(LL * 0.3), 6, 2, "l1"))
        for off, L, per, on, c in spec:
            start = bx - 2 - (0 if off == 0 else round(6 * k_) + abs(off))
            for i in range(L):
                if i % per < on or off == 0 and i % 5 != 4:
                    cx_, cy_ = V.to_canvas(view, start - i, ym + off)
                    ov[cy_, cx_] = hexrgb(col["l2"] if (off == 0 and i % 7 == 0) else col[c])
        if line >= 30:   # spark at the blade tip while gliding
            for ddx, ddy in ((0, 0), (1, 0), (0, -1), (0, 1), (2, 0)):
                cx_, cy_ = V.to_canvas(view, bx + blade.shape[1] + ddx, ym + ddy)
                ov[cy_, cx_] = hexrgb(col["l2"])
        return ov
    return fn


def frame_fn(name, spec, size):
    if spec[0] == "idle":
        return dict(T=None)
    _, dy, lean, dx, fan, line, arm, _ms = spec
    view = V.VIEWS[name]
    regions = {p[0] for p in view["parts"]} - {"sword"}
    T = {}
    for r in regions:
        if r in ("legL", "legR"):
            T[r] = ops_for(name, dy, lean, dx, part="legs")
        elif r == "skirt":
            T[r] = ops_for(name, dy, lean, dx, part="skirt")
        elif r in ("armL", "armR", "hand", "handR"):
            T[r] = ops_for(name, dy, lean, dx, part="arm", arm=arm, region=r)
        else:
            T[r] = ops_for(name, dy, lean, dx)
    px, py = P(CONFIG["PIVOT"][name])
    f = fan if kind(name) == "side" else fan * 0.4
    for r in JV.FLOAT_R:
        T[r] = [("rot", px, py, f)] + ops_for(name, dy, lean, dx)
    return dict(T=T, hide=("sword",), overlay=overlay(name, dy, lean, dx, line, fan), overlay_front=False, no_feet_check=True)


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    SIZE[0] = size
    JV.setup(size)
    R.run(V.CONFIG["PREFIX"], size, {"ride": CONFIG["RIDE"]}, frame_fn)
