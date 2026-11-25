"""Defeat for every suit from the approved 天兵 sample (tianbing_defeat.py): python3 suit_defeat.py <suit> [96|64] [stage]
Same frames (flash, stagger, sag, fall, down): the upper body drops, the head rolls back, the legs fold under the body (knees knock in; side views:
knees forward), the held prop tips over about the fist. Hip pivots are measured from each view's leg mask; the neck from the head mask.
CONFIG: TIP_PROPS (what falls, per suit; floating blades drop instead), ROLL_K and DROP_K per suit (long necks, low bodies)."""
import sys, importlib
import numpy as np
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R
import tianbing_hit as H
import tianbing_defeat as D
import suit_hit as SH

CONFIG = {
    "TIP_PROPS": {"tianbing": ("halberd",), "wushi": ("halberd",), "mojiang": ("mallet",), "mingjiang": ("axe",), "yuanmo": ("staff",),
                  "jianxian": (), "tianlong": (), "gushi": ()},
    "DROP_PROPS": {"jianxian": ("bladeA", "bladeB", "bladeC", "ringC", "sword"), "tianlong": ("pearl",)},   # floating things fall to the ground
    "ROLL_K": {"tianlong": 0.5, "mingjiang": 0.0, "yuanmo1": 0.4, "yuanmo2": 0.6, "gushi": 0.7},
    "DROP_K": {"yuanmo1": 0.6, "yuanmo2": 0.8, "gushi": 0.8},
    "FOLD_K": {"yuanmo1": 0.6, "yuanmo2": 0.8, "yuanmo3": 1.0},
}
SUIT, KEY = "tianbing", "tianbing"
HIP, NECK = {}, {}


def measure_hips(size):
    """hip pivot per leg = top centre of that leg's mask in the idle view"""
    for name in V.ORDER:
        img, body, legs, heads = R.build_frame(name, ("idle",), size, lambda n, s, z: dict(T=None))
        reg = V.LAST["region"]
        for leg in ("legL", "legR"):
            ys, xs = np.nonzero(reg == leg)
            if len(ys): HIP[(name, leg)] = to_data(name, float(xs.mean()), float(ys.min()) + 2)
    for name in V.ORDER: NECK[name] = to_data(name, *SH.NECK[name])


def to_data(name, cx, cy):
    """canvas pixel -> the view's data space (the inverse of V.to_canvas: subtract the pad, undo the flip)"""
    ox, oy = V.CONFIG["OFF"]; x, y = cx - ox, cy - oy
    if V.VIEWS[name]["flip"]: x = V.CONFIG["N"] - 1 - x
    return x, y


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, shove, drop, roll, fold, tip, flash, _ms = spec
    k = H.SZ["k"]; drop *= CONFIG["DROP_K"].get(KEY, 1) * k; shove = min(shove, SH.CONFIG["SHOVE"].get(KEY, 9)) * k
    fold *= CONFIG["FOLD_K"].get(KEY, 1)
    ax, ay = H.AWAY[name]
    view = V.VIEWS[name]; regions = {p[0] for p in view["parts"]}
    tips = set(CONFIG["TIP_PROPS"].get(SUIT, ())) & regions; drops = set(CONFIG["DROP_PROPS"].get(SUIT, ())) & regions
    body_ops = [("mov", ax * shove, ay * shove + drop)]
    T = {r: list(body_ops) for r in regions - {"legL", "legR"} - tips - drops}
    nx, ny = NECK[name]
    T["head"] = [("rot", nx, ny, roll * SH.CONFIG["ROLL_SIGN"].get(name, 1) * CONFIG["ROLL_K"].get(KEY, 1))] + body_ops
    sl, sr = D.CONFIG["FOLD"][name]; legdy = drop * 0.35
    for leg, sg in (("legL", sl), ("legR", sr)):
        if (name, leg) in HIP:
            hx, hy = HIP[(name, leg)]; T[leg] = [("rot", hx, hy, sg * fold), ("mov", 0, legdy)]
    if "skirt" in regions: T["skirt"] = [("mov", ax * shove, ay * shove + drop * 0.5)]
    fx, fy = view.get("fist", (48, 60))
    for r in tips: T[r] = list(body_ops) + [("rot", fx + ax * shove, fy + ay * shove + drop, D.CONFIG["TIP"][name] * tip)]
    for r in drops: T[r] = [("mov", 0, min(drop * 1.6, 30 * k))]
    return dict(T=T, post=H.flash_post if flash else None, recolour=flash, no_feet_check=True)


if __name__ == "__main__":
    SUIT = sys.argv[1]; size = sys.argv[2] if len(sys.argv) > 2 else "96"; stage = int(sys.argv[3]) if len(sys.argv) > 3 else None
    KEY = SUIT + (str(stage) if stage else ""); SH.SUIT = SUIT; SH.KEY = KEY
    H.SZ["k"] = 1.0 if size == "96" else 59 / 90
    if SUIT == "tianbing":
        if size == "64":
            import tianbing64_views as T64; T64.setup()
    else:
        m = importlib.import_module(SH.CONFIG["MODULE"][SUIT])
        if SUIT == "yuanmo": m.setup(stage, size)
        else:
            try: m.setup(size)
            except TypeError: m.setup()
    SH.measure_necks(size); measure_hips(size)
    prefix = SH.CONFIG["PREFIX"].get(SUIT, "tb") + (str(stage) if stage else "") + ("" if size == "96" else "64") + "_defeat"
    R.run(prefix, size, {"defeat": D.CONFIG["DEFEAT"]}, frame_fn)
