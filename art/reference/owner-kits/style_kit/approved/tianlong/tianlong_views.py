"""天龙: four views (front, left, back, right) with its two approved animations, the channelled bombardment and the dash.
Front = the approved front (tianlong96.py). Side template faces right; the body is symmetric, so left = the same
template mirrored (the tail trails behind in both). Back = front mirrored, minus face and pearl, with the thruster
pods and tail now in front. Animations move parts about joints; flames, beam and speed lines are overlays.
Run: python3 tianlong_views.py [96|64] -> out/tl_* or out/tl64_* (pass/fail only)
"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw
import tianbing96_v5 as F
import tianbing96_views as V
import tianlong96 as D
import anim_runner as R

CONFIG = {
    # channel: name, body dy, raise share, effect, ms
    "CHANNEL": [("idle", 0, 0.0, None, 120), ("brace", 1, 0.5, None, 120), ("charge1", 0, 1.0, "charge1", 150),
                ("charge2", 0, 1.0, "charge2", 150), ("fire", 0, 1.0, "fire", 90), ("recover", 1, 0.4, None, 140)],
    # dash: name, body dy, lean share, plume size (0-2), ms
    "DASH": [("idle", 0, 0.0, 0, 100), ("crouch", 2, 0.5, 1, 100), ("burst", 0, 1.0, 2, 80),
             ("burst2", 0, 1.0, 3, 80), ("settle", 1, 0.5, 1, 100)],
    "RAISE": {   # arm pivots and full angles, pearl lift (96 grid)
        "front": dict(armL=((31, 39), -20), armR=((64, 39), 20), pearl=(0, -6)),
        "side": dict(armL=((49, 39), -35), armR=((47, 40), -35), pearl=None),
    },
    "LEAN_SIDE": ((48, 58), -18),    # hip pivot and full lean for the side-view dash
    "NOZZLES": {"front": [((27, 47), 1), ((68, 47), -1)], "side": [((31, 48), 1)]},   # (point, outward x sign)
    "FIRE_ANGLE_SIDE": -70,          # beam direction in the side views (degrees from +x; up-forward)
    "COL": {"hot": "#e9fbff", "mid": "#ffc05a", "flame": "#e8702a", "dark": "#a33a1c"},
}
BODY_UP = ["torso", "head", "skirt", "pauL", "pauR", "armL", "armR", "pearl", "neck", "thrust", "tail"]


def pair(region, ramp, poly, flat=False):
    return [(region, ramp, poly, flat)]


# ---------- side template (facing right) ----------
SIDE = [
    ("head", "b", [(46, 9), (48, 8), (44, 3), (42, 3)], False),                          # far antler
    ("thrust", "s", [(30, 12), (37, 16), (42, 38), (36, 42), (28, 30)], False),          # far pod
    ("thrust", "s", [(25, 14), (32, 18), (40, 40), (33, 45), (23, 32)], False),          # near pod
    ("thrust", "g", [(24, 15), (28, 12), (32, 18), (27, 21)], False),                    # intake cap
    ("thrust", "v", [(29, 42), (35, 44), (33, 50), (27, 47)], False),                    # nozzle fire
    ("tail", "g", [(38, 58), (42, 60), (36, 70), (31, 68)], False),
    ("tail", "b", [(31, 66), (37, 68), (35, 72), (29, 70)], True),
    ("tail", "g", [(30, 70), (35, 72), (28, 82), (23, 79)], False),
    ("tail", "b", [(22, 78), (28, 81), (26, 85), (20, 82)], True),
    ("tail", "g", [(20, 82), (26, 85), (22, 91), (14, 90), (13, 86)], False),
    ("tail", "b", [(14, 86), (6, 80), (8, 88), (12, 91)], False),
    ("legL", "g", [(42, 58), (50, 58), (47, 72), (39, 72)], False),
    ("legL", "s", [(37, 70), (47, 70), (47, 76), (37, 76)], False),
    ("legL", "g", [(38, 76), (46, 76), (45, 86), (38, 86)], False),
    ("legL", "s", [(36, 86), (48, 86), (50, 89), (36, 89)], False),
    ("legL", "b", [(44, 89), (47, 89), (48, 91), (44, 91)], True),
    ("legL", "b", [(48, 89), (51, 89), (52, 91), (49, 91)], True),
    ("legL", "b", [(36, 89), (38, 89), (37, 91), (35, 91)], True),
    ("legR", "g", [(49, 58), (58, 58), (57, 72), (48, 72)], False),
    ("legR", "s", [(47, 70), (58, 70), (58, 76), (47, 76)], False),
    ("legR", "g", [(48, 76), (57, 76), (56, 86), (49, 86)], False),
    ("legR", "s", [(46, 86), (59, 86), (61, 89), (46, 89)], False),
    ("legR", "b", [(55, 89), (58, 89), (59, 91), (55, 91)], True),
    ("legR", "b", [(59, 89), (62, 89), (63, 91), (60, 91)], True),
    ("legR", "b", [(46, 89), (48, 89), (47, 91), (45, 91)], True),
    ("skirt", "g", [(40, 52), (56, 52), (58, 61), (39, 61)], False),
    ("skirt", "b", [(40, 52), (56, 52), (56, 55), (40, 55)], True),
    ("torso", "f", [(40, 30), (55, 30), (55, 54), (40, 54)], True),
    ("torso", "g", [(39, 32), (55, 32), (60, 38), (59, 46), (54, 54), (42, 54), (38, 46)], False),
    ("neck", "s", [(43, 16), (50, 16), (51, 31), (44, 31)], False),
    ("neck", "b", [(43, 20), (50, 20), (50, 21), (43, 21)], True),
    ("neck", "b", [(43, 24), (51, 24), (51, 25), (43, 25)], True),
    ("neck", "b", [(44, 28), (51, 28), (51, 29), (44, 29)], True),
    ("armL", "g", [(46, 38), (52, 38), (55, 49), (49, 50)], False),                      # far arm
    ("armL", "g", [(50, 49), (56, 48), (62, 54), (57, 58)], False),
    ("armL", "s", [(58, 49), (64, 49), (64, 57), (58, 57)], False),
    ("pearl", "v", [(56, 48), (57, 38), (60, 45)], False),
    ("pearl", "v", [(60, 45), (63, 35), (66, 47)], False),
    ("pearl", "p", [(58, 46), (62, 46), (66, 50), (66, 57), (62, 61), (58, 61), (55, 57), (55, 50)], False),
    ("armR", "g", [(43, 39), (50, 39), (52, 50), (46, 51)], False),                      # near arm
    ("armR", "s", [(44, 49), (52, 49), (52, 54), (44, 54)], False),
    ("armR", "g", [(47, 53), (53, 51), (59, 56), (55, 60)], False),
    ("armR", "s", [(55, 53), (61, 53), (61, 61), (55, 61)], False),
    ("armR", "b", [(61, 54), (64, 55), (62, 57)], True),
    ("armR", "b", [(61, 58), (64, 59), (61, 61)], True),
    ("pauR", "g", [(40, 30), (48, 27), (53, 32), (51, 40), (43, 41), (39, 36)], False),
    ("head", "g", [(40, 9), (50, 8), (56, 11), (60, 13), (60, 17), (52, 19), (42, 19), (38, 14)], False),   # skull, same box as the front
    ("head", "s", [(52, 13), (60, 13), (60, 17), (52, 18)], False),                      # muzzle
    ("head", "b", [(44, 8), (48, 8), (54, 11), (54, 12), (50, 12)], True),               # brow ridge
    ("head", "b", [(57, 18), (59, 18), (58, 21)], True),                                 # fang
    ("head", "b", [(55, 17), (56, 17), (53, 21), (52, 21)], True),                       # barbel (short)
    ("head", "b", [(42, 9), (44, 8), (38, 2), (36, 2)], False),                          # near antler
    ("head", "b", [(40, 5), (41, 6), (35, 5), (33, 3)], False),
]
SIDE_DETAILS = [
    ("out", 48, 11, 53, 13), ("glow", 49, 11, 50, 11), ("glow", 51, 12, 52, 12),   # eye, slanting down to the front
    ("out", 59, 14, 59, 14),                                                        # nostril
    ("out", 41, 38, 46, 38), ("out", 42, 43, 48, 43), ("out", 41, 57, 56, 57),
    ("out", 40, 78, 43, 78), ("out", 50, 78, 54, 78),
    ("s3", 63, 52, 63, 56), ("s3", 60, 59, 62, 59), ("v1", 57, 50, 59, 50), ("v1", 59, 51, 59, 53),
]
SIDE_STUDS = [("g3", 41, 35), ("g3", 52, 35), ("b3", 46, 22), ("b3", 48, 26), ("s3", 40, 72), ("s3", 51, 72),
              ("g3", 44, 47), ("g3", 56, 44), ("g3", 46, 14), ("s3", 55, 15), ("g3", 33, 69), ("g3", 25, 80),
              ("g3", 18, 88), ("b3", 40, 87), ("b3", 50, 87), ("s3", 30, 25), ("s3", 34, 35), ("v2", 31, 45),
              ("g3", 41, 80), ("g3", 52, 80), ("g3", 44, 60), ("g3", 54, 60), ("s3", 47, 51), ("g3", 45, 31)]


def back():
    face = {("head", "s"), ("head", "b")}
    parts = []
    later = []
    for r, rp, pl, fl in D.PARTS:
        if r == "pearl":
            continue
        if r == "head" and rp == "s":
            continue                                   # muzzle faces forward
        if r == "head" and rp == "b" and len(pl) in (3, 5):
            continue                                   # brows and fangs face forward
        if r == "armL" and rp == "b" or r == "armR" and rp == "b":
            continue                                   # claw tips on the pearl
        if r in ("thrust", "tail"):
            later.append((r, rp, pl, fl)); continue    # on the back: now in front
        parts.append((r, rp, pl, fl))
    parts += [("torso", "g", [(37, 31), (58, 31), (59, 52), (36, 52)], False)]          # back plate over the arms' inner ends
    parts += later
    details = [("out", 47, 32, 48, 51), ("out", 39, 37, 44, 37), ("out", 51, 37, 56, 37), ("out", 39, 44, 44, 44),
               ("out", 51, 44, 56, 44), ("out", 44, 13, 51, 13), ("out", 40, 57, 55, 57),
               ("out", 22, 24, 26, 24), ("out", 69, 24, 73, 24), ("out", 23, 30, 28, 30), ("out", 67, 30, 72, 30)]
    studs = [s for s in D.STUDS if not (40 <= s[1] <= 56 and 8 <= s[2] <= 20) and not (40 <= s[1] <= 55 and 42 <= s[2] <= 61)] + [
        ("g3", 41, 34), ("g3", 54, 34), ("g3", 41, 48), ("g3", 54, 48), ("s3", 25, 20), ("s3", 70, 20), ("g3", 46, 11), ("g3", 49, 11)]
    return dict(parts=parts, details=details, studs=studs, flip=True, shoulder=(31, 39), fist=(40, 56), hipfix=False)


def setup(size="96"):
    F.CONFIG["PAL"] = dict(D.CONFIG["PAL"]); F.CONFIG["RAMP"] = dict(D.CONFIG["RAMP"])
    V.VIEWS.clear()
    side = dict(parts=SIDE, details=SIDE_DETAILS, studs=SIDE_STUDS, shoulder=(47, 40), fist=(58, 57), hipfix=False)
    V.VIEWS.update({
        "front": dict(parts=D.PARTS, details=D.DETAILS, studs=D.STUDS, flip=False, shoulder=(31, 39), fist=(40, 56), hipfix=False),
        "left": dict(side, flip=True), "back": back(), "right": dict(side, flip=False),
    })
    V.CONFIG["PREFIX"] = "tl"
    if size == "64":
        import tianbing64_views as T64
        T64.setup()
        V.CONFIG["PREFIX"] = "tl64"


# ---------- animation frames ----------
def P(x, y, size):
    if size == "64":
        import tianbing64_views as T64
        return T64.Xf(x), T64.Yf(y)
    return float(x), float(y)


def K(size):
    return 1.0 if size == "96" else 59 / 90


def kind(name):
    return "front" if name in ("front", "back") else "side"


def raise_T(name, dy, share, size):
    T = {r: [("mov", 0, dy)] for r in BODY_UP}
    cfg = CONFIG["RAISE"][kind(name)]
    for arm in ("armL", "armR"):
        (px, py), deg = cfg[arm]
        px, py = P(px, py, size)
        T[arm] = [("mov", 0, dy), ("rot", px, py + dy, deg * share)]
    if cfg["pearl"] is not None:
        dx, ddy = cfg["pearl"]
        T["pearl"] = [("mov", dx * share * K(size), dy + ddy * share * K(size))]
    else:   # side: the pearl follows the near claw
        hx, hy = P(58, 57, size)
        nx, ny = V.apply_ops(T["armR"], hx, hy)
        T["pearl"] = [("mov", nx - hx, ny - hy)]
    return T


def pearl_centre(name, T, size):
    c = (47.5, 52) if kind(name) == "front" else (60.5, 53.5)
    return V.apply_ops(T["pearl"], *P(*c, size))


def channel_overlay(name, T, stage, size):
    col = CONFIG["COL"]; k = K(size)

    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        cx, cy = pearl_centre(name, T, size)
        if stage in ("charge1", "charge2"):
            r = (11 if stage == "charge1" else 13) * k
            n = 10
            for i in range(n):
                a = math.radians(i * 360 / n + (18 if stage == "charge2" else 0))
                px, py = V.to_canvas(view, cx + r * math.cos(a), cy + r * math.sin(a))
                d.point((px, py), fill=col["mid"] if i % 2 else col["hot"])
                if i % 2 == 0:
                    px2, py2 = V.to_canvas(view, cx + (r - 2 * k) * math.cos(a), cy + (r - 2 * k) * math.sin(a))
                    d.point((px2, py2), fill=col["flame"])
        if stage == "fire":
            if kind(name) == "front":
                ang = -90.0
            else:
                ang = CONFIG["FIRE_ANGLE_SIDE"]
            a = math.radians(ang)
            L = (cy + V.CONFIG["OFF"][1] - 3) / max(abs(math.sin(a)), 0.2)   # stop 3 px short of the canvas top
            x1, y1 = cx + L * math.cos(a), cy + L * math.sin(a)
            nx, ny = -math.sin(a), math.cos(a)
            for off, c in ((-2, col["flame"]), (-1, col["mid"]), (0, col["hot"]), (1, col["mid"]), (2, col["flame"])):
                p0 = V.to_canvas(view, cx + off * nx, cy + off * ny); p1 = V.to_canvas(view, x1 + off * nx, y1 + off * ny)
                d.line([p0, p1], fill=c, width=1)
            for i in range(8):
                b = math.radians(i * 45)
                r0, r1 = 7 * k, (12 if i % 2 == 0 else 10) * k
                d.line([V.to_canvas(view, cx + r0 * math.cos(b), cy + r0 * math.sin(b)),
                        V.to_canvas(view, cx + r1 * math.cos(b), cy + r1 * math.sin(b))], fill=col["hot"] if i % 2 == 0 else col["mid"])
        # antler-tip glow while charging (the spotter locks on)
        if stage in ("charge1", "charge2", "fire"):
            tips = [(37, 2), (58, 2), (32, 3), (63, 3)] if kind(name) == "front" else [(36, 2), (33, 3), (42, 3)]
            hd = T.get("head", [])
            for tx, ty in tips:
                px, py = V.to_canvas(view, *V.apply_ops(hd, *P(tx, ty, size)))
                d.point((px, py - 1), fill=col["hot"])
                if stage != "charge1":
                    d.point((px, py - 2), fill=col["mid"])
        return np.asarray(ov)
    return fn


def dash_overlay(name, T, plume, size):
    col = CONFIG["COL"]; k = K(size)

    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        if plume == 0:
            return np.asarray(ov)
        length = (6, 14, 24, 20)[plume] * k
        ops = T.get("thrust", [])
        for (nx, ny), sx in CONFIG["NOZZLES"][kind(name)]:
            x0, y0 = V.apply_ops(ops, *P(nx, ny, size))
            if kind(name) == "front":
                dirx, diry = -0.9 * sx, 1.0      # down and out, clear of the legs
            else:
                dirx, diry = -1.0, 0.45          # down and back
            nrm = math.hypot(dirx, diry); dirx, diry = dirx / nrm, diry / nrm
            px, py = -diry, dirx
            for w, c in ((3.5, col["dark"]), (2.4, col["flame"]), (1.2, col["mid"]), (0.0, col["hot"])):
                tipx, tipy = x0 + dirx * length * (1 - w / 4), y0 + diry * length * (1 - w / 4)
                poly = [V.to_canvas(view, x0 + px * w * k, y0 + py * w * k), V.to_canvas(view, tipx, tipy),
                        V.to_canvas(view, x0 - px * w * k, y0 - py * w * k)]
                d.polygon(poly, fill=c)
        if plume >= 2:   # speed lines
            if kind(name) == "front":
                for x, y in ((14, 30), (16, 52), (80, 30), (78, 52)):
                    p0 = V.to_canvas(view, *P(x, y, size)); p1 = V.to_canvas(view, *P(x, y + 10, size))
                    d.line([p0, p1], fill=col["mid"])
            else:
                for y in (22, 40, 58):
                    p0 = V.to_canvas(view, *P(8, y, size)); p1 = V.to_canvas(view, *P(20, y, size))
                    d.line([p0, p1], fill=col["mid"])
        return np.asarray(ov)
    return fn


def frame_fn(name, spec, size):
    if spec[0] == "idle" or len(spec) == 1:
        return dict(T=None)
    if spec in CONFIG["CHANNEL"]:
        _, dy, share, stage, _ = spec
        T = raise_T(name, dy, share, size)
        return dict(T=T, overlay=channel_overlay(name, T, stage, size) if stage else None,
                    overlay_front=(name != "back"))
    _, dy, lean, plume, _ = spec
    T = {r: [("mov", 0, dy)] for r in BODY_UP}
    if kind(name) == "side" and lean:
        (hx, hy), deg = CONFIG["LEAN_SIDE"]
        hx, hy = P(hx, hy, size)
        T = {r: [("mov", 0, dy), ("rot", hx, hy + dy, deg * lean)] for r in BODY_UP}
    return dict(T=T, overlay=dash_overlay(name, T, plume, size), overlay_front=(name == "back"))


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    setup(size)
    V.CONFIG["PREFIX"] = "tl" if size == "96" else "tl64"
    R.run(V.CONFIG["PREFIX"], size, {"channel": CONFIG["CHANNEL"], "dash": CONFIG["DASH"]}, frame_fn)
