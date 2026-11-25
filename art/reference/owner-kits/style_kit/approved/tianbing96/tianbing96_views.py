"""天兵 96x96: four views (front, left, back, right) and a 5-frame halberd strike on each.
Parts are polygons; each frame moves parts about joints and redraws at native pixels (no resampling).
Left view is drawn facing right and mirrored as data before shading, so light stays upper-left.
Back view is the front data mirrored plus back-only parts, minus face parts.
Run: python3 tianbing96_views.py  -> out/views_*  (reports pass/fail only)
"""
import math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import tianbing96_v5 as F

CONFIG = {
    "CANVAS": 224, "OFF": (64, 48),          # padded canvas for attack frames; sprite box is 96 at OFF
    # name, body dy, arm deg (about the shoulder), arm shift (dx, dy), halberd, ms, smear
    # halberd: "rNN" = roll the halberd half a turn (blade up) then rotate NN; a number = rotate the halberd about the fist; "far" / "near" = swap in the foreshortened head (pointing at the camera)
    "ATTACK_FRONT": [
        ("idle", 0, 0, (0, 0), 0, 120, None), ("windup", 1, -12, (0, 0), "far", 120, None),
        ("thrust", 0, 12, (-3, -10), "near", 70, "burst"), ("impact", 1, 12, (-3, -10), "near", 160, None),
        ("recover", 0, 0, (0, 0), 20, 100, None)],
    "ATTACK_SIDE": [   # total halberd angle = arm + halberd; 90 = level, blade forward
        ("idle", 0, 0, (0, 0), 0, 120, None), ("windup", 1, 15, (-3, -10), "r75", 120, None),
        ("thrust", 0, -45, (0, 0), "r135", 70, "streak"), ("impact", 1, -50, (0, 0), "r140", 160, None),
        ("recover", 0, -15, (0, 0), 55, 100, None)],
    # frame-size settings (96 = approved desktop rung); a 64 run overrides these from tianbing64_views.py
    "N": 96, "HIP": (55, 67, 31, 42), "FEET_ROWS": (86, 93), "TOE_ROWS": (87, 91), "HEAD_ROWS": (14, 31),
    "HEIGHT": (72, 94), "FEET_GAP": 3, "ISO": (4.0, 10.2), "PREFIX": "views",
    "MAX_CHANGE": 25.0, "SCALE_SHEET": 1, "SCALE_GIF": 2, "SCALE_LINEUP": 3,
    "BG": (58, 62, 72, 255),
}
LAST = {}
BODY = ["torso", "head", "skirt", "pauR", "pauL", "armL", "pagoda"]


def shift(poly, dx, dy):
    return [(x + dx, y + dy) for x, y in poly]


# ---------- back view: front data mirrored at render, face parts out, back parts in ----------
BACK_PARTS = [p for p in F.PARTS if not (p[0] == "torso" and p[1] in ("s", "v"))] + [
    ("torso", "b", [(46, 34), (50, 34), (50, 52), (46, 52)], False),               # spine ridge
    ("head", "s", [(41, 26), (54, 26), (54, 30), (41, 30)], False),                # neck guard, inside the head box
]
BACK_DETAILS = [d for d in F.DETAILS if d not in (("out", 43, 22, 51, 25), ("glow", 44, 23, 50, 24), ("v1", 47, 13, 48, 13))] + [
    ("out", 40, 38, 44, 38), ("out", 52, 38, 56, 38),      # back vents
    ("out", 40, 41, 44, 41), ("out", 52, 41, 56, 41),
]
BACK_STUDS = [s for s in F.STUDS if not (s[1] in (44, 50) and s[2] == 28)] + [("b3", 48, 36), ("b3", 48, 46), ("s3", 42, 28), ("s3", 53, 28)]


# ---------- side view template, facing right ----------
def halberd(fx):
    return [
        ("halberd", "s", [(fx - 1, 4), (fx + 1, 4), (fx + 1, 91), (fx - 1, 91)], True),
        ("halberd", "s", [(fx, 1), (fx + 3, 5), (fx + 2, 12), (fx - 2, 12), (fx - 3, 5)], False),
        ("halberd", "s", [(fx + 2, 8), (fx + 11, 4), (fx + 20, 8), (fx + 23, 16), (fx + 18, 25), (fx + 9, 27), (fx + 2, 21)], False),
        ("halberd", "f", [(fx + 5, 11), (fx + 15, 10), (fx + 16, 18), (fx + 11, 22), (fx + 6, 18)], True),
        ("halberd", "b", [(fx - 4, 12), (fx + 5, 12), (fx + 5, 15), (fx - 4, 15)], True),
        ("halberd", "v", [(fx + 2, 15), (fx + 6, 15), (fx + 7, 26), (fx + 3, 26)], False),
    ]


def hanging_arm(ax, big, fist_dx=0):
    pau = ("pauR" if big else "pauL")
    if big:
        p = [(pau, "g", [(ax - 11, 30), (ax - 6, 25), (ax + 6, 26), (ax + 10, 31), (ax + 9, 40), (ax + 2, 44), (ax - 8, 42), (ax - 12, 36)], False),
             (pau, "b", [(ax - 9, 28), (ax - 6, 25), (ax + 6, 26), (ax + 9, 29), (ax + 6, 29), (ax - 5, 28)], True),
             (pau, "g", [(ax - 9, 40), (ax + 7, 39), (ax + 6, 45), (ax - 7, 46)], False)]
    else:
        p = [(pau, "g", [(ax - 8, 32), (ax - 4, 27), (ax + 6, 29), (ax + 7, 38), (ax + 1, 41), (ax - 7, 39)], False),
             (pau, "b", [(ax - 6, 30), (ax - 4, 27), (ax + 6, 29), (ax + 4, 30), (ax - 3, 29)], True)]
    f = fist_dx
    return p + [
        ("armR", "f", [(ax - 5, 42), (ax + 5, 42), (ax + 6, 56), (ax - 4, 57)], True),
        ("armR", "g", [(ax - 4, 43), (ax + 4, 43), (ax + 5, 54), (ax - 3, 55)], False),
        ("armR", "s", [(ax - 4, 53), (ax + 5, 53), (ax + 6, 58), (ax - 3, 59)], False),
        ("armR", "g", [(ax - 3, 58), (ax + 5, 58), (ax + 5, 68), (ax - 3, 68)], False),
        ("armR", "b", [(ax - 3, 61), (ax + 5, 61), (ax + 5, 63), (ax - 3, 63)], True),
        ("armR", "s", [(ax - 4 + f, 68), (ax + 7 + f, 68), (ax + 8 + f, 75), (ax + 2 + f, 77), (ax - 4 + f, 74)], False),
    ]


def pagoda(dx):
    return [(r, rp, shift(pl, dx, 0), fl) for r, rp, pl, fl in F.PARTS if r == "pagoda"]


def raised_arm_near(ax):   # pagoda arm nearest the camera, raised forward-up
    return [
        ("pauL", "g", [(ax - 8, 32), (ax - 4, 27), (ax + 6, 29), (ax + 7, 38), (ax + 1, 41), (ax - 7, 39)], False),
        ("pauL", "b", [(ax - 6, 30), (ax - 4, 27), (ax + 6, 29), (ax + 4, 30), (ax - 3, 29)], True),
        ("armL", "f", [(ax - 3, 41), (ax + 6, 41), (ax + 12, 31), (ax + 3, 31)], True),
        ("armL", "g", [(ax - 2, 40), (ax + 5, 40), (ax + 11, 32), (ax + 4, 32)], False),
        ("armL", "s", [(ax + 5, 27), (ax + 15, 27), (ax + 15, 33), (ax + 5, 33)], False),
        ("armL", "g", [(ax + 7, 20), (ax + 14, 20), (ax + 14, 28), (ax + 7, 28)], False),
        ("armL", "b", [(ax + 7, 23), (ax + 14, 23), (ax + 14, 25), (ax + 7, 25)], True),
        ("armL", "s", [(ax + 5, 15), (ax + 16, 15), (ax + 16, 21), (ax + 5, 21)], False),
    ] + pagoda(ax + 10 - 23)


def raised_arm_far(ax):    # pagoda arm on the far side, raised up-back (drawn before the torso)
    return [
        ("pauL", "g", [(ax - 8, 33), (ax - 4, 28), (ax + 6, 30), (ax + 7, 38), (ax + 1, 41), (ax - 7, 39)], False),
        ("armL", "f", [(ax - 7, 41), (ax + 2, 41), (ax - 6, 30), (ax - 15, 30)], True),
        ("armL", "g", [(ax - 6, 40), (ax, 40), (ax - 7, 32), (ax - 14, 32)], False),
        ("armL", "s", [(ax - 16, 28), (ax - 6, 28), (ax - 6, 33), (ax - 16, 33)], False),
        ("armL", "g", [(ax - 14, 21), (ax - 7, 21), (ax - 7, 29), (ax - 14, 29)], False),
        ("armL", "b", [(ax - 14, 24), (ax - 7, 24), (ax - 7, 26), (ax - 14, 26)], True),
        ("armL", "s", [(ax - 16, 16), (ax - 5, 16), (ax - 5, 21), (ax - 16, 21)], False),
    ] + pagoda(ax - 10 - 23)


LEG_FAR = [
    ("legL", "f", [(36, 56), (47, 56), (44, 76), (34, 76)], True),
    ("legL", "g", [(37, 58), (46, 58), (43, 74), (35, 74)], False),
    ("legL", "s", [(34, 73), (44, 73), (44, 79), (35, 79)], False),
    ("legL", "f", [(35, 78), (44, 78), (44, 89), (35, 89)], True),
    ("legL", "g", [(36, 80), (44, 80), (44, 88), (36, 88)], False),
    ("legL", "b", [(32, 86), (46, 86), (49, 91), (32, 91)], False),
]
LEG_NEAR = [
    ("legR", "f", [(46, 56), (58, 56), (60, 76), (48, 76)], True),
    ("legR", "g", [(47, 58), (57, 58), (59, 74), (49, 74)], False),
    ("legR", "s", [(48, 73), (60, 73), (60, 79), (49, 79)], False),
    ("legR", "f", [(49, 78), (59, 78), (59, 89), (49, 89)], True),
    ("legR", "g", [(50, 80), (59, 80), (59, 88), (50, 88)], False),
    ("legR", "b", [(47, 86), (62, 86), (66, 91), (47, 91)], False),
]
SKIRT = [
    ("skirt", "f", [(40, 52), (58, 52), (58, 62), (40, 62)], True),
    ("skirt", "b", [(40, 52), (59, 52), (59, 55), (40, 55)], False),
    ("skirt", "g", [(36, 56), (41, 56), (41, 65), (37, 65)], False),      # rear tasset
    ("skirt", "g", [(40, 56), (56, 56), (55, 66), (41, 66)], False),      # side tasset
    ("skirt", "g", [(55, 55), (61, 55), (60, 66), (55, 66)], False),      # front tasset edge
]
TORSO = [
    ("torso", "f", [(45, 29), (53, 29), (53, 34), (45, 34)], True),
    ("torso", "f", [(40, 33), (58, 33), (58, 54), (40, 54)], True),
    ("torso", "g", [(39, 33), (58, 33), (62, 38), (61, 46), (58, 51), (50, 54), (44, 54), (40, 50), (38, 40)], False),
    ("torso", "v", [(59, 40), (62, 40), (62, 43), (59, 43)], True),      # core seen edge-on
]
HEAD = [   # same box as the front head: 15 wide (x 42-56), rows 12-30; visor at the facing edge
    ("head", "g", [(42, 20), (44, 16), (47, 14), (51, 14), (54, 16), (56, 20), (56, 28), (54, 30), (44, 30), (42, 28)], False),
    ("head", "b", [(46, 14), (48, 12), (51, 12), (53, 14), (53, 15), (46, 15)], False),   # ridge plate front to back
    ("head", "b", [(42, 20), (56, 20), (56, 21), (42, 21)], True),                       # brim band, same length as the front
    ("head", "s", [(49, 22), (53, 22), (53, 29), (49, 29)], False),                      # cheek guard
    ("head", "s", [(42, 25), (44, 25), (44, 30), (42, 30)], False),                      # neck guard at the back
]
SIDE_DETAILS = [
    ("out", 52, 22, 56, 25), ("glow", 53, 23, 56, 24),      # visor slot at the front edge
    ("out", 44, 17, 54, 17),                                # helm bevel
    ("out", 41, 44, 47, 44), ("out", 42, 48, 48, 48),       # chest panel lines
    ("out", 44, 61, 52, 61), ("out", 41, 66, 55, 66),       # skirt seam, thigh line
    ("out", 51, 84, 58, 84), ("out", 37, 84, 43, 84),       # shin seams
]
SIDE_STUDS = [("s3", 54, 76), ("s3", 40, 76), ("b3", 56, 54), ("g3", 52, 46), ("b3", 48, 64), ("s3", 44, 27), ("b3", 57, 89), ("g3", 40, 86), ("b3", 42, 36), ("b3", 42, 50), ("s3", 50, 39), ("b3", 44, 58), ("b3", 54, 58), ("s3", 50, 75),
              ("s3", 38, 75), ("b3", 52, 82), ("b3", 38, 82), ("g3", 46, 42), ("b3", 60, 89), ("b3", 44, 89)]


def side_right():   # right view: the character's right side faces the camera (halberd arm near)
    parts = (halberd(31) * 0) + raised_arm_far(40) + LEG_FAR + LEG_NEAR + SKIRT + TORSO + HEAD + halberd(68) + hanging_arm(55, True, fist_dx=3)   # shaft plants beside the toe, not over it
    studs = SIDE_STUDS + [("b3", 48, 31), ("b3", 62, 31), ("b3", 56, 65), ("s3", 55, 70), ("s3", 69, 16), ("s3", 76, 10),
                          ("s3", 28, 18), ("b3", 30, 27), ("g3", 31, 10), ("b3", 33, 89), ("s3", 72, 16), ("s3", 79, 10),
                          ("b3", 50, 46), ("s3", 57, 56), ("b3", 36, 62), ("s3", 50, 28), ("g3", 56, 83), ("b3", 46, 70),
                          ("s3", 60, 72), ("b3", 46, 36), ("g3", 34, 70), ("s3", 29, 30)]
    return dict(parts=parts, details=SIDE_DETAILS + [("v2", 28, 11, 28, 11), ("v2", 31, 11, 31, 11), ("v1", 34, 11, 34, 11),
                                                      ("v2", 29, 5, 29, 5), ("v1", 32, 5, 32, 5), ("b3", 29, 1, 30, 1),
                                                      ("out", 46, 34, 60, 34), ("out", 44, 37, 58, 37)],
                studs=studs, flip=False, shoulder=(55, 45), fist=(68, 72), hipfix=False, attack="ATTACK_SIDE")


def side_left():    # left view: the character's left side faces the camera (pagoda arm near); drawn facing right, mirrored
    parts = halberd(31) + LEG_FAR + hanging_arm(37, True, fist_dx=-3) + LEG_NEAR + SKIRT + TORSO + HEAD + raised_arm_near(52)
    studs = SIDE_STUDS + [("b3", 46, 31), ("b3", 56, 31), ("s3", 60, 18), ("b3", 62, 27), ("g3", 63, 10), ("b3", 35, 89), ("s3", 36, 56), ("b3", 46, 70),
                          ("s3", 50, 28), ("g3", 56, 83), ("b3", 59, 36), ("s3", 55, 17), ("b3", 42, 62), ("s3", 38, 20)]
    return dict(parts=parts, details=SIDE_DETAILS + [("v2", 61, 11, 61, 11), ("v2", 64, 11, 64, 11), ("v1", 67, 11, 67, 11),
                                                      ("v2", 62, 5, 62, 5), ("v1", 65, 5, 65, 5), ("b3", 62, 1, 63, 1),
                                                      ("out", 46, 34, 57, 34)],
                studs=studs, flip=True, shoulder=(37, 45), fist=(31, 72), hipfix=False, attack="ATTACK_SIDE")


VIEWS = {
    "front": dict(parts=F.PARTS, details=F.DETAILS, studs=F.STUDS, flip=False, shoulder=(66, 45), fist=(69, 72), hipfix=True, attack="ATTACK_FRONT"),
    "left": side_left(),
    "back": dict(parts=BACK_PARTS, details=BACK_DETAILS, studs=BACK_STUDS, flip=True, shoulder=(66, 45), fist=(69, 72), hipfix=True, attack="ATTACK_FRONT", spear_front=False),
    "right": side_right(),
}
ORDER = ["front", "left", "back", "right"]


# ---------- transforms and rendering ----------
def apply_ops(ops, x, y):
    for op in ops:
        if op[0] == "mirx":     # mirror across a vertical line (the halberd rolled half a turn in the hand)
            x = 2 * op[1] - x
        elif op[0] == "rot":
            _, cx, cy, deg = op
            a = math.radians(deg)
            dx, dy = x - cx, y - cy
            x, y = cx + dx * math.cos(a) - dy * math.sin(a), cy + dx * math.sin(a) + dy * math.cos(a)
        else:
            x, y = x + op[1], y + op[2]
    return x, y


def place(view, T, x, y, region):
    nx, ny = apply_ops(T.get(region, []), x, y)
    nx, ny = int(round(nx)), int(round(ny))
    if view["flip"]:
        nx = CONFIG["N"] - 1 - nx
    return nx + CONFIG["OFF"][0], ny + CONFIG["OFF"][1]


def build(view, T=None, canvas=None, hide=(), extra=(), extra_front=True):
    T = T or {}
    C = canvas or CONFIG["CANVAS"]
    W = H = C
    P = F.CONFIG["PAL"]
    N = CONFIG["N"]
    base = np.full((N, N), "", dtype="<U8")
    for region, ramp, poly, flat in view["parts"]:
        base[F.mask(poly, N, N)] = region
    src = [p for p in view["parts"] if p[0] not in hide]
    src = (src + list(extra)) if extra_front else (list(extra) + src)
    parts = [(r, rp, [place(view, T, x, y, r) for x, y in pl], fl) for r, rp, pl, fl in src]

    def mv(x, y):
        r = base[y, x] if 0 <= y < N and 0 <= x < N else ""
        return place(view, T, x, y, r)
    details = []
    for key, x0, y0, x1, y1 in view["details"]:
        for yy in range(y0, y1 + 1):
            for xx in range(x0, x1 + 1):
                if not (0 <= yy < N and 0 <= xx < N and base[yy, xx] in hide):
                    details.append((key,) + mv(xx, yy))
    studs = [(k,) + mv(x, y) for k, x, y in view["studs"] if not (0 <= y < N and 0 <= x < N and base[y, x] in hide)]

    img = np.zeros((H, W, 4), np.uint8)
    ramp_of = np.full((H, W), "", dtype="<U1")
    flat_px = np.zeros((H, W), bool)
    region_of = np.full((H, W), "", dtype="<U8")
    out = F.hexrgb(P["out"])
    full = {}   # each region's own full mask (before occlusion), so shading does not shift when a prop passes in front
    for region, ramp, poly, flat in parts:
        M = F.mask(poly, W, H)
        full[region] = full.get(region, np.zeros((H, W), bool)) | M
        sh, mid, lit = (F.hexrgb(P[k]) for k in F.CONFIG["RAMP"][ramp])
        img[M, :3] = mid; img[M, 3] = 255
        ramp_of[M] = ramp; flat_px[M] = flat or ramp == "f"; region_of[M] = region
        if not flat and ramp != "f":
            dn = np.zeros_like(M); dn[:-1] = M[1:]
            rt = np.zeros_like(M); rt[:, :-1] = M[:, 1:]
            seam = M & (~dn | ~rt)
            img[seam, :3] = out
            flat_px[seam] = True
    for region in sorted(set(region_of[region_of != ""].tolist())):
        R = (region_of == region) & ~flat_px
        Rall = full[region]
        dul = F.diag_dist(Rall, -1, -1)
        ddr = F.diag_dist(Rall, 1, 1)
        t = dul / np.maximum(dul + ddr, 1)
        band = F.CONFIG["LIGHT_BAND"] if Rall.sum() >= F.CONFIG["SMALL_REGION"] else 1
        for ramp in ("g", "b", "s", "v"):
            sel = R & (ramp_of == ramp)
            sh, mid, lit = (F.hexrgb(P[k]) for k in F.CONFIG["RAMP"][ramp])
            img[sel & (t > F.CONFIG["SHADE_FRAC"]), :3] = sh
            img[sel & (dul <= band), :3] = lit
    if F.CONFIG["RIVET_ROWS"]:
        b3 = F.hexrgb(P["b3"])
        for region, ramp, poly, flat in parts:
            if flat or ramp != "g":
                continue
            M = F.mask(poly, W, H)
            if M.sum() < 60:
                continue
            dt = F.diag_dist(M, -1, 0); db = F.diag_dist(M, 1, 0)
            rows = (dt == 3) | (db == 3)
            ys_, xs_ = np.nonzero(rows & M & ~flat_px)
            for y, x in zip(ys_, xs_):
                if (x + y // 7) % F.CONFIG["RIVET_STEP"] == 0 and (region_of[y, x] == region):
                    img[y, x, :3] = b3
    if F.CONFIG["BOLT_HOLES"]:
        for region, ramp, poly, flat in parts:
            if flat or ramp != "s":
                continue
            M = F.mask(poly, W, H)
            if M.sum() < 40:
                continue
            ys_, xs_ = np.nonzero(M)
            cy, cx = int(round(ys_.mean())), int(round(xs_.mean()))
            for x in (cx - 3, cx, cx + 3):
                if 0 <= x < W and M[cy, x] and not flat_px[cy, x]:
                    img[cy, x, :3] = out
    for key, x, y in details + studs:
        if 0 <= y < H and 0 <= x < W and img[y, x, 3] > 0:
            img[y, x, :3] = F.hexrgb(P[key])
    if view["hipfix"]:
        ox, oy = CONFIG["OFF"]
        hdy = int(round(sum(op[2] for op in T.get("skirt", []) if op[0] == "mov")))
        hy0, hy1, hx0, hx1 = CONFIG["HIP"]
        for y in range(hy0 + hdy + oy, hy1 + hdy + oy):
            for x in range(hx0 + ox, hx1 + ox):
                xm = N - 1 + 2 * ox - x
                if img[y, x, 3] > 0 and region_of[y, x] == "skirt" and region_of[y, xm] == "skirt":
                    img[y, xm] = img[y, x]
    A = img[..., 3] > 0
    nb = np.zeros_like(A)
    nb[1:] |= A[:-1]; nb[:-1] |= A[1:]; nb[:, 1:] |= A[:, :-1]; nb[:, :-1] |= A[:, 1:]
    ol = nb & ~A
    img[ol, :3] = out; img[ol, 3] = 255
    LAST["region"] = region_of
    return img


def crop96(img):
    ox, oy = CONFIG["OFF"]
    N = CONFIG["N"]
    return img[oy:oy + N, ox:ox + N]


def ops_for(view, dy, arm, shift_xy, hal):
    T = {r: [("mov", 0, dy)] for r in BODY}
    arm_ops = [("mov", 0, dy), ("rot", *view["shoulder"], arm)]
    if shift_xy != (0, 0):
        arm_ops.append(("mov", *shift_xy))
    fx, fy = apply_ops(arm_ops, *view["fist"])
    T["armR"] = arm_ops
    if hal in ("far", "near"):
        return T, (fx, fy), arm_ops, ("halberd",), spear_head(fx, fy, hal)
    if isinstance(hal, str):   # "r135": roll so the crescent faces up once the shaft is level, then rotate
        cx = view["fist"][0]
        T["halberd"] = [("mirx", cx)] + arm_ops + [("rot", fx, fy, float(hal[1:]))]
    else:
        T["halberd"] = arm_ops + [("rot", fx, fy, hal)]
    return T, (fx, fy), T["halberd"], (), ()


def spear_head(fx, fy, size):
    """halberd pointing at the camera: tip seen point-on (diamond), collar ring, crescent blade seen edge-on (a bar)"""
    fx, fy = int(round(fx)), int(round(fy)) - 2
    if size == "far":
        return [
            ("spear", "v", [(fx - 6, fy + 2), (fx - 3, fy + 2), (fx - 3, fy + 7), (fx - 6, fy + 7)], False),
            ("spear", "b", [(fx - 4, fy - 2), (fx - 2, fy - 4), (fx + 2, fy - 4), (fx + 4, fy - 2), (fx + 4, fy + 2), (fx + 2, fy + 4), (fx - 2, fy + 4), (fx - 4, fy + 2)], False),
            ("spear", "s", [(fx + 4, fy - 1), (fx + 12, fy - 2), (fx + 12, fy), (fx + 4, fy + 1)], False),
            ("spear", "s", [(fx, fy - 3), (fx + 3, fy), (fx, fy + 3), (fx - 3, fy)], False),
        ]
    return [
        ("spear", "v", [(fx - 10, fy + 4), (fx - 5, fy + 4), (fx - 4, fy + 15), (fx - 9, fy + 14)], False),
        ("spear", "b", [(fx - 7, fy - 3), (fx - 3, fy - 7), (fx + 3, fy - 7), (fx + 7, fy - 3), (fx + 7, fy + 3), (fx + 3, fy + 7), (fx - 3, fy + 7), (fx - 7, fy + 3)], False),
        ("spear", "s", [(fx + 7, fy - 3), (fx + 24, fy - 2), (fx + 26, fy), (fx + 24, fy + 2), (fx + 7, fy + 3)], False),
        ("spear", "s", [(fx, fy - 6), (fx + 6, fy), (fx, fy + 6), (fx - 6, fy)], False),
    ]


def to_canvas(view, x, y):
    x, y = int(round(x)), int(round(y))
    if view["flip"]:
        x = CONFIG["N"] - 1 - x
    return x + CONFIG["OFF"][0], y + CONFIG["OFF"][1]


def smear(view, kind, frm, to):
    """placeholder overlays, drawn behind the body. frm / to: (arm_ops, fist, halberd deg) of the wind-up and the thrust frame"""
    C = CONFIG["CANVAS"]
    ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    if kind == "streak":   # speed lines from where three blade points were at the wind-up to where they are now
        fx0 = 68 if not view["flip"] else 31
        for pt, col in (((fx0, 2), "#c2fff1"), ((fx0 + 12, 5), "#aebfcc"), ((fx0 + 20, 22), "#687a8a"), ((fx0 + 8, 26), "#aebfcc")):
            a = apply_ops(frm[0], *pt)
            b = apply_ops(to[0], *pt)
            d.line([to_canvas(view, *a), to_canvas(view, *b)], fill=col, width=1)
    elif kind == "burst":  # short radial lines round the head that points at the camera
        fx, fy = to[1]
        for k in range(8):
            ang = math.radians(k * 45 + 22.5)
            r0, r1 = (12, 17) if k % 2 == 0 else (12, 15)
            a = (fx + r0 * math.cos(ang), fy - 2 + r0 * math.sin(ang)); b = (fx + r1 * math.cos(ang), fy - 2 + r1 * math.sin(ang))
            d.line([to_canvas(view, *a), to_canvas(view, *b)], fill="#c2fff1" if k % 2 == 0 else "#aebfcc", width=1)
    return np.asarray(ov)


def composite(body, over, over_in_front=False):
    out = np.zeros_like(body)
    for layer in ((body, over) if over_in_front else (over, body)):
        a = layer[..., 3:4] > 0
        out = np.where(a, layer, out)
    return out


# ---------- checks ----------
def isolated_pct(img):
    A = img[..., 3] > 0
    rgb = img[..., :3].astype(int)
    same = np.zeros(A.shape, int)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        sh = np.roll(np.roll(rgb, dy, 0), dx, 1); shA = np.roll(np.roll(A, dy, 0), dx, 1)
        same += ((sh == rgb).all(axis=2) & shA)
    return float((A & (same == 0)).sum()) / max(A.sum(), 1) * 100


def idle_checks(name, img96):
    fails = []
    A = img96[..., 3] > 0
    ys, xs = np.nonzero(A)
    h = ys.max() - ys.min() + 1
    lo, hi = CONFIG["HEIGHT"]
    if not lo <= h <= hi: fails.append(f"{name}: height {h}")
    gap = CONFIG["N"] - 1 - ys.max()
    if gap != CONFIG["FEET_GAP"]: fails.append(f"{name}: feet gap {gap}")
    cols = len(set(map(tuple, img96[A][:, :3].tolist())))
    if not 9 <= cols <= 13: fails.append(f"{name}: colours {cols}")
    iso = isolated_pct(img96)
    if not CONFIG["ISO"][0] <= iso <= CONFIG["ISO"][1]: fails.append(f"{name}: isolated {iso:.1f}%")
    lab, n = ndimage.label(A, structure=np.ones((3, 3)))
    if n != 1: fails.append(f"{name}: {n} pieces")
    return fails, dict(height=h, colours=cols, isolated=round(iso, 1), width=int(xs.max() - xs.min() + 1))


def facing_check(name, img96, legs96, head96, face_right):
    """toes and visor must point the facing way (toes measured on leg pixels only)"""
    fails = []
    A = img96[..., 3] > 0
    t0, t1 = CONFIG["TOE_ROWS"]
    row_top = np.nonzero(legs96[t0])[0]; row_bot = np.nonzero(legs96[t1])[0]
    toe_ok = (row_bot.max() > row_top.max()) if face_right else (row_bot.min() < row_top.min())
    if not toe_ok: fails.append(f"{name}: toes do not point the facing way")
    glow = F.hexrgb(F.CONFIG["PAL"]["glow"])
    g = np.nonzero((img96[..., :3] == glow).all(axis=2) & A)
    hc = np.nonzero(head96)[1].mean()   # centre of the head's own pixels (a pauldron beside it does not count)
    if len(g[1]) == 0 or ((g[1].mean() > hc) != face_right): fails.append(f"{name}: visor not on the facing side")
    return fails


def main():
    import os
    os.makedirs("out", exist_ok=True)
    S = CONFIG["SCALE_SHEET"]; C = CONFIG["CANVAS"]
    fails, report = [], {}
    idle = {}
    all_frames = {}
    for name in ORDER:
        view = VIEWS[name]
        frames, ms, legmaps = [], [], []
        spec = CONFIG[view["attack"]]
        wind = None
        for fname, dy, arm, shf, hal, dur, sm in spec:
            T, fist, arm_ops, hide, extra = ops_for(view, dy, arm, shf, hal)
            if fname == "windup":
                wind = (arm_ops, fist, hal)
            moving = dy or arm or hal or shf != (0, 0)
            body = build(view, T if moving else None, hide=hide, extra=extra, extra_front=view.get("spear_front", True))
            legs_f = np.isin(LAST["region"], ["legL", "legR"])
            if fname == "idle":
                legs = legs_f
                heads = LAST["region"] == "head"
            legmaps.append(legs_f)
            img = body
            if sm:
                # a burst round a head pointing at the camera sits in front; a burst behind the back view is hidden by the body anyway
                img = composite(body, smear(view, sm, wind, (arm_ops, fist, hal)), over_in_front=(sm == "burst" and view.get("spear_front", True)))
            frames.append(img); ms.append(dur)
            if img[0].any() or img[-1].any() or img[:, 0].any() or img[:, -1].any():
                fails.append(f"{name}/{fname}: touches canvas edge")
            lab, n = ndimage.label(body[..., 3] > 0, structure=np.ones((3, 3)))
            if n != 1: fails.append(f"{name}/{fname}: {n} pieces")
        idle[name] = crop96(frames[0])
        f, rep = idle_checks(name, idle[name]); fails += f; report[name] = rep
        if name in ("left", "right"):
            fails += facing_check(name, idle[name], crop96(legs), crop96(heads), face_right=(name == "right"))
        ox, oy = CONFIG["OFF"]
        r0, r1 = CONFIG["FEET_ROWS"]
        feet0 = frames[0][r0 + oy:r1 + oy]
        # feet must not move: compare pixels that are leg pixels in both frames (a prop passing in front is not a foot move)
        if not all(np.array_equal(feet0[legs[r0 + oy:r1 + oy] & lm[r0 + oy:r1 + oy]], fr[r0 + oy:r1 + oy][legs[r0 + oy:r1 + oy] & lm[r0 + oy:r1 + oy]]) for fr, lm in zip(frames[1:], legmaps[1:])):
            fails.append(f"{name}: feet move between frames")
        ch = []
        for i in range(len(frames)):
            j = (i + 1) % len(frames)
            c = float((frames[i] != frames[j]).any(axis=2).mean()) * 100
            ch.append(round(c, 1))
            if c == 0: fails.append(f"{name}: frames {i},{j} identical")
            if c > CONFIG["MAX_CHANGE"]: fails.append(f"{name}: frames {i},{j} change {c:.1f}%")
        report[name]["change_pct"] = ch
        all_frames[name] = (frames, ms)
        gs = CONFIG["SCALE_GIF"]
        gif = []
        for fr in frames:
            bg = Image.new("RGBA", (C, C), CONFIG["BG"]); bg.alpha_composite(Image.fromarray(fr, "RGBA"))
            gif.append(bg.resize((C * gs, C * gs), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
        gif[0].save(f"out/{CONFIG['PREFIX']}_attack_{name}_{gs}x.gif", save_all=True, append_images=gif[1:], duration=ms, loop=0, disposal=2)
    # back vs mirrored front silhouette
    fa = idle["front"][..., 3] > 0; ba = idle["back"][..., 3] > 0; fm = fa[:, ::-1]
    report["back"]["iou_vs_mirrored_front"] = round(float((ba & fm).sum() / (ba | fm).sum()), 2)
    # sheets
    n = len(CONFIG["ATTACK_FRONT"])
    sheet = Image.new("RGBA", (C * S * n, C * S * len(ORDER)), CONFIG["BG"])
    for r, name in enumerate(ORDER):
        for i, fr in enumerate(all_frames[name][0]):
            sheet.alpha_composite(Image.fromarray(fr, "RGBA").resize((C * S, C * S), Image.NEAREST), (i * C * S, r * C * S))
    sheet.save(f"out/{CONFIG['PREFIX']}_attack_sheet_{S}x.png")
    L = CONFIG["SCALE_LINEUP"]
    for sc, fn in ((1, f"out/{CONFIG['PREFIX']}_lineup_1x.png"), (L, f"out/{CONFIG['PREFIX']}_lineup_{L}x.png")):
        N = CONFIG["N"]
        lu = Image.new("RGBA", (N * sc * 4, N * sc), (0, 0, 0, 0) if sc == 1 else CONFIG["BG"])
        for i, name in enumerate(ORDER):
            lu.alpha_composite(Image.fromarray(idle[name], "RGBA").resize((N * sc, N * sc), Image.NEAREST), (i * N * sc, 0))
        lu.save(fn)
        Image.fromarray(idle[ORDER[i]], "RGBA")
    for name in ORDER:
        Image.fromarray(idle[name], "RGBA").save(f"out/{CONFIG['PREFIX']}_idle_{name}_1x.png")
    for name in ORDER:
        print(name, report[name])
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
