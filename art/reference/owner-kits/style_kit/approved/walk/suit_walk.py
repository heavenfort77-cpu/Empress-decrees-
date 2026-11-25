"""Walk cycle for every suit from the approved 天兵 sample (tianbing_walk.py): python3 suit_walk.py <suit> [96|64] [stage]
Same four frames and timings. Hips and shoulders are measured from each view's leg and arm masks (top centre, in data space); held props ride with
the body (PLANTED props in suit_hit stay put as in the hit set); floating parts (blades, pearl, pods) ride with the body. Front/back: the stepping
leg lifts and tilts; side: legs scissor about the hips, lifted back onto the ground row. CONFIG: SWING_K and LIFT_K per suit for short or long legs."""
import sys, importlib, math
import numpy as np
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R
import tianbing_hit as H
import tianbing_walk as TW
import suit_hit as SH
import suit_defeat as SD

CONFIG = {
    "SWING_K": {"yuanmo1": 0.7, "yuanmo2": 0.85, "gushi": 0.8, "mojiang": 0.8},
    "LIFT_K": {"yuanmo1": 0.6, "yuanmo2": 0.8},
    "RIDE": ("halberd", "mallet", "axe", "staff", "sword", "bladeA", "bladeB", "bladeC", "ringC", "pearl", "shield", "cloak", "pauL", "pauR", "mantle", "bow"),
}
SUIT, KEY = "tianbing", "tianbing"
PIV = {}


def measure(size):
    for name in V.ORDER:
        R.build_frame(name, ("idle",), size, lambda n, s, z: dict(T=None)); reg = V.LAST["region"]
        for part in ("legL", "legR", "armL", "armR"):
            ys, xs = np.nonzero(reg == part)
            if len(ys): PIV[(name, part)] = SD.to_data(name, float(xs.mean()), float(ys.min()) + 2)
        ys, xs = np.nonzero(np.isin(reg, ["legL", "legR"])); PIV[(name, "leglen")] = float(ys.max() - ys.min()) if len(ys) else 30


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, swing, lifted, dy, arm, _ms = spec; k = H.SZ["k"]; dy *= k
    swing *= CONFIG["SWING_K"].get(KEY, 1); lift_px = TW.CONFIG["LIFT_PX"] * k * CONFIG["LIFT_K"].get(KEY, 1)
    side = name in ("left", "right"); sgn = 1 if name != "left" else -1
    regions = {p[0] for p in V.VIEWS[name]["parts"]}
    T = {r: [("mov", 0, dy)] for r in regions if r not in ("legL", "legR")}
    def piv(part): return PIV.get((name, part))
    if side:
        L = PIV[(name, "leglen")]; lift = round(L * (1 - math.cos(math.radians(swing))))
        for leg, sg in (("legL", 1), ("legR", -1)):
            if piv(leg): hx, hy = piv(leg); T[leg] = [("rot", hx, hy, sgn * sg * swing), ("mov", 0, dy - lift)]
        for armn, sg, f in (("armL", -1, 1.0), ("armR", 1, 0.5)):
            if piv(armn) and armn in regions: sx, sy = piv(armn); T[armn] = [("rot", sx, sy, sgn * sg * arm * f), ("mov", 0, dy)]
    else:
        up, down = ("legL", "legR") if lifted == "L" else ("legR", "legL")
        if piv(up):
            hx, hy = piv(up); T[up] = [("rot", hx, hy, abs(swing) * TW.CONFIG["FRONT_TILT"] * (1 if lifted == "L" else -1)), ("mov", 0, dy - lift_px * (abs(swing) / 14))]
        T[down] = [("mov", 0, dy)]
        for armn, f in (("armL", 0.6), ("armR", 0.3)):
            if piv(armn) and armn in regions: sx, sy = piv(armn); T[armn] = [("rot", sx, sy, arm * f), ("mov", 0, dy)]
        for pau, side_ in (("pauL", "L"), ("pauR", "R")):
            if pau in regions: T[pau] = [("mov", 0, dy + (1 if lifted == side_ else 0))]
    return dict(T=T, no_feet_check=True)


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
    measure(size)
    prefix = SH.CONFIG["PREFIX"].get(SUIT, "tb") + (str(stage) if stage else "") + ("" if size == "96" else "64") + "_walk"
    R.run(prefix, size, {"walk": TW.CONFIG["WALK"]}, frame_fn)
