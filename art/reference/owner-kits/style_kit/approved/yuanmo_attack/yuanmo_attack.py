"""猿魔 attack sample: the staff pound (python3 yuanmo_attack.py [stage] [96|64]). The ape lifts both arms and the staff straight up, stands tall,
then drives them down; a gold shock burst breaks at the staff base (front/back: at the base; side views: in front of the feet). The whole body
rises and drops with the pound; feet stay planted. Same part-moving renderer; nothing is resampled. One sample (stage 1 at 96) for approval.
Run -> out/ym1_attack_4views_2x.gif, out/ym1_attack_sheet_1x.png (pass/fail only)"""
import sys, math
import numpy as np
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R
import yuanmo_stages as Y
import yuanmo_views as YV

CONFIG = {
    # name, body dy, arm+staff lift px (negative = up), staff tilt deg (side views, about the fist; back on the rise, forward on the slam), burst (0 none, 1 small, 2 full), ms
    "ATTACK": [("idle", 0, 0, 0, 0, 120), ("rise", -2, -12, -18, 0, 130), ("peak", -3, -16, -26, 0, 80),
               ("slam", 3, 2, 14, 2, 70), ("impact", 2, 1, 10, 1, 150), ("recover", 1, 0, 3, 0, 100)],
    "LIFT": ("armL", "armR", "hand", "staff"),
    "BODY": ("torso", "head", "hump", "crest", "horns", "nub", "ridge", "pauL", "pauR", "studs"),
    "BASE": {"front": (84, 91), "back": (84, 91), "right": (86, 91), "left": (63, 91)},   # stage-3 coordinates: staff base (front, right; back is mirrored by the view flip), knuckle fist (left view, no staff)
    "COL": ("#ffcf40", "#fff3b0", "#b86a1e"),
}
SZ = {"k": 1.0, "s": "96"}


def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def burst(name, level, dy):
    col = [hexrgb(c) for c in CONFIG["COL"]]
    def fn(view):
        C = V.CONFIG["CANVAS"]; ov = np.zeros((C, C, 4), np.uint8)
        bx, by = CONFIG["BASE"][name]; bx, by = Y.BX(bx, YV.K()), Y.BY(by, YV.K())
        n = 7 if level == 2 else 4; r0 = round((7 if level == 2 else 4) * SZ["k"]); r1 = r0 + round((9 if level == 2 else 5) * SZ["k"])
        for i in range(n):
            a = math.pi + i * math.pi / (n - 1)          # upper half ring (the ground hides the lower half)
            for t in range(r0, r1 + 1):
                x, y = bx + round(t * math.cos(a)), by - 1 + round(t * math.sin(a) * 0.6)
                ox, oy = V.to_canvas(view, x, y)
                ov[oy, ox] = col[1] if t == r1 else col[0]
        for t in (-r1 - 2, r1 + 2):                     # ground sparks either side
            ox, oy = V.to_canvas(view, bx + t, by); ov[oy, ox] = col[2]
        return ov
    return fn


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, dy, lift, tilt, bl, _ms = spec
    k = SZ["k"]; dy *= k; lift *= k
    regions = {p[0] for p in V.VIEWS[name]["parts"]}
    T = {r: [("mov", 0, dy)] for r in regions if r not in ("legL", "legR")}
    for r in CONFIG["LIFT"]:
        if r in regions: T[r] = [("mov", 0, lift)]
    if name in ("left", "right") and "staff" in regions:
        fx, fy = V.VIEWS[name]["fist"]
        T["staff"] = [("rot", fx, fy, tilt if name == "right" else -tilt), ("mov", 0, lift)]
    return dict(T=T, overlay=burst(name, bl, dy) if bl else None, overlay_front=False)


if __name__ == "__main__":
    stage = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    size = sys.argv[2] if len(sys.argv) > 2 else "96"
    SZ["s"] = size; SZ["k"] = 1.0 if size == "96" else 59 / 90
    YV.setup(stage, size)
    R.run(V.CONFIG["PREFIX"], size, {"attack": CONFIG["ATTACK"]}, frame_fn)
