"""天兵 walk cycle sample at 96 (python3 tianbing_walk.py [96|64]). Four frames: contact L, pass, contact R, pass. Side views: legs swing about the
hips (the lifted foot forward, the planted one back), arms swing opposite, body bobs 1 px up on the passes; the halberd stays with the arm that
holds it but does not swing. Front and back: the stepping leg lifts 2 px and tilts, the other plants, shoulders dip. Same part-moving renderer;
nothing resampled. One sample for approval; the other suits follow from the same data. Run -> out/tb_walk_4views_2x.gif, out/tb_walk_sheet_1x.png"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R

CONFIG = {
    # name, leg swing deg (side: L forward +, R back; front/back: the lifted leg), lifted leg (L/R/None), body dy, arm swing deg, ms
    "WALK": [("contactL", 14, "L", 0, 8, 140), ("passL", 4, "L", -1, 2, 120), ("contactR", -14, "R", 0, -8, 140), ("passR", -4, "R", -1, -2, 120)],
    "HIP": {"front": ((40, 60), (55, 60)), "back": ((40, 60), (55, 60)), "right": ((48, 60), (46, 60)), "left": ((48, 60), (46, 60))},
    "SHOULDER": {"front": ((31, 42), (66, 45)), "back": ((31, 42), (66, 45)), "right": ((55, 45), (55, 45)), "left": ((37, 45), (37, 45))},
    "LIFT_PX": 2, "FRONT_TILT": 0.35,
    "UPPER": ("torso", "head", "armL", "armR", "pauL", "pauR", "pagoda", "halberd"),
}
SZ = {"k": 1.0}


def P(x, y, size):
    if size == "64":
        import tianbing64_views as T64; return T64.Xf(x), T64.Yf(y)
    return float(x), float(y)


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, swing, lifted, dy, arm, _ms = spec; k = SZ["k"]; dy *= k
    side = name in ("left", "right"); sgn = 1 if name != "left" else -1
    (lx, ly), (rx, ry) = [P(*h, size) for h in CONFIG["HIP"][name]]
    (sl, sr) = [P(*h, size) for h in CONFIG["SHOULDER"][name]]
    T = {r: [("mov", 0, dy)] for r in CONFIG["UPPER"]}
    if side:
        import math
        lift = round(31 * k * (1 - math.cos(math.radians(swing))))   # a leg swung about the hip arcs down; lift it back onto the ground row
        T["legL"] = [("rot", lx, ly, sgn * swing), ("mov", 0, dy - lift)]
        T["legR"] = [("rot", rx, ry, -sgn * swing), ("mov", 0, dy - lift)]
        T["armL"] = [("rot", sl[0], sl[1], -sgn * arm), ("mov", 0, dy)]
        T["armR"] = [("rot", sr[0], sr[1], sgn * arm * 0.5), ("mov", 0, dy)]   # the halberd arm swings half; the halberd itself rides with the body
    else:
        up, down = ("legL", "legR") if lifted == "L" else ("legR", "legL")
        hx_, hy_ = (lx, ly) if lifted == "L" else (rx, ry)
        T[up] = [("rot", hx_, hy_, abs(swing) * CONFIG["FRONT_TILT"] * (1 if lifted == "L" else -1)), ("mov", 0, dy - CONFIG["LIFT_PX"] * k * (abs(swing) / 14))]
        T[down] = [("mov", 0, dy)]
        T["armL"] = [("rot", sl[0], sl[1], arm * 0.6), ("mov", 0, dy)]; T["armR"] = [("rot", sr[0], sr[1], arm * 0.3), ("mov", 0, dy)]
        T["pauL"] = [("mov", 0, dy + (1 if lifted == "L" else 0))]; T["pauR"] = [("mov", 0, dy + (1 if lifted == "R" else 0))]
    return dict(T=T, no_feet_check=True)


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"; SZ["k"] = 1.0 if size == "96" else 59 / 90
    if size == "64":
        import tianbing64_views as T64; T64.setup()
    R.run("tbw" if size == "96" else "tbw64", size, {"walk": CONFIG["WALK"]}, frame_fn)
