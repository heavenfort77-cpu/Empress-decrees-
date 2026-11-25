"""剑仙 (Sword Immortal, offensive duellist) front sample, 96x96, in the approved style (same renderer, light, outline, rivets).
Ideal: one purpose perfected; the blade is the self, mastery needs less. Structure first: tall, narrow, raked shoulders (nothing boxy);
one long blade slung on the back that breaks the outline; four hanging sheath plates instead of robes, one per array blade, each with
its own tip (定锋 short broad, 断锋 long straight, 引锋 hooked, 归锋 ringed); a faceless slit visor under a tiny sword hairpin.
Behaviour: the left hand, held out clear of the body, makes the sword-finger gesture (two straight fingers, silver glow at the tips) that commands the blades; the right hand is empty. The spirit blade floats behind the back, held by nothing.
Palette: pearl armour, crimson cord and sling, cold steel, silver-white qi. No name, likeness or sword from any existing novel.
Run: python3 jianxian96.py -> out/jx_front_{1x,3x}.png, out/jx_lineup_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#0f1217",
        "g1": "#59617c", "g2": "#a3acc6", "g3": "#e6ebf6",   # pewter-pearl armour (mid-light, so plates separate)
        "b1": "#5e1b24", "b2": "#a8323f", "b3": "#e8737b",   # crimson cord, sling, tassel
        "s2": "#7e8ea8", "s3": "#d4e4f6",                    # cold steel: blades, joints
        "v0": "#7c8499", "v1": "#c6cde2", "v2": "#ffffff",   # silver-white qi
        "glow": "#eaf4ff",                                   # core, visor light
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("g1", "s2", "s3"),
             "v": ("v0", "v1", "v2"), "f": ("out", "out", "out")},
}


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False, region_r=None):
    return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


PARTS = []
import math


def sw(base, ang, pts, du=0):
    """local (v across, u along the blade) -> 96-grid polygon; ang 0 = straight up, + = clockwise on screen"""
    a = math.radians(ang); bx, by = base
    return [(round(bx + u * math.sin(a) + v * math.cos(a), 1), round(by - u * math.cos(a) + v * math.sin(a), 1)) for v, u in [(v, u + du) for v, u in pts]]


# three swords float behind the shoulders (hilts hidden behind the body), each its own silhouette:
#   定锋 broad leaf blade (right, steep), 引锋 narrow with a hooked tip (right, wide), 归锋 straight with a floating steel ring (left)
# three whole swords (pommel, crimson grip, steel guard, blade) float in a fan beside the right shoulder, clear of the body.
# Hilts point in toward one centre that sits just off the pauldron; blades spread out. Inner 归锋 (ring), middle 定锋 (leaf),
# outer 引锋 (hooked). Crimson only on the thin grips, so they read as three separate ribs, not one red blob.
FAN = dict(centre=(66, 44), r0=8, du=3)
FC = dict(base=FAN["centre"], ang=-6)
FA = dict(base=FAN["centre"], ang=20)
FB = dict(base=FAN["centre"], ang=46)


def hilt(F, region):
    r = FAN["r0"]
    return [(region, "b", sw(F["base"], F["ang"], [(-1.2, r + 1.5), (1.2, r + 1.5), (1.2, r + 7), (-1.2, r + 7)]), True),      # grip
            (region, "s", sw(F["base"], F["ang"], [(0, r - 0.5), (1.8, r + 1), (0, r + 2.5), (-1.8, r + 1)]), False),            # pommel
            (region, "s", sw(F["base"], F["ang"], [(-3, r + 7), (3, r + 7), (2.5, r + 9), (-2.5, r + 9)]), False)]              # guard


PARTS += [
    # outer: 引锋, narrow with a hooked tip
    ("bladeB", "s", sw(FB["base"], FB["ang"], [(-2, 13), (2, 13), (2, 22), (3.5, 25), (6, 29), (2.5, 28), (-0.5, 26), (-2, 22)], du=FAN["du"]), False),
    ("bladeB", "f", sw(FB["base"], FB["ang"], [(-0.5, 15), (0.5, 15), (0.5, 22), (-0.5, 22)], du=FAN["du"]), True),
] + hilt(FB, "bladeB") + [
    # middle: 定锋, broad leaf
    ("bladeA", "s", sw(FA["base"], FA["ang"], [(-2.5, 13), (2.5, 13), (3.5, 22), (3, 30), (0, 37), (-3, 30), (-3.5, 22)], du=FAN["du"]), False),
    ("bladeA", "f", sw(FA["base"], FA["ang"], [(-0.5, 15), (0.5, 15), (0.5, 31), (-0.5, 31)], du=FAN["du"]), True),
] + hilt(FA, "bladeA") + [
    # inner: 归锋, straight, with a floating steel ring
    ("bladeC", "s", sw(FC["base"], FC["ang"], [(-2, 13), (2, 13), (2, 33), (0, 38), (-2, 33)], du=FAN["du"]), False),
    ("ringC", "s", sw(FC["base"], FC["ang"], [(-5.5, 26), (-3, 23), (3, 23), (5.5, 26), (5.5, 31), (3, 34), (-3, 34), (-5.5, 31)], du=FAN["du"]), False),
    ("ringC", "f", sw(FC["base"], FC["ang"], [(-3.5, 26.5), (-2, 25), (2, 25), (3.5, 26.5), (3.5, 30.5), (2, 32), (-2, 32), (-3.5, 30.5)], du=FAN["du"]), True),
    ("bladeC", "s", sw(FC["base"], FC["ang"], [(-2, 22), (2, 22), (2, 33), (0, 38), (-2, 33)], du=FAN["du"]), False),
    ("bladeC", "f", sw(FC["base"], FC["ang"], [(-0.5, 15), (0.5, 15), (0.5, 22), (-0.5, 22)], du=FAN["du"]), True),
] + hilt(FC, "bladeC")
LEG = [("g", [(38, 58), (46, 58), (45, 73), (39, 73)], False),
       ("s", [(38, 71), (46, 71), (45, 77), (39, 77)], False),                        # knee
       ("g", [(39, 77), (45, 77), (44, 87), (40, 87)], False),
       ("g", [(35, 87), (46, 87), (49, 90), (49, 91), (34, 91), (34, 89)], False),    # pointed foot
       ("v", [(34, 90), (37, 90), (36, 91), (34, 91)], True)]
for ramp, poly, flat in LEG:
    PARTS += pair("legL", ramp, poly, flat, region_r="legR")
PARTS += [
    ("torso", "f", [(36, 29), (59, 29), (56, 40), (53, 54), (42, 54), (39, 40)], True),     # hourglass: wide shoulders, narrow waist
    ("torso", "g", [(37, 30), (58, 30), (55, 40), (52, 52), (43, 52), (40, 40)], False),
    ("torso", "v", [(41, 38), (54, 38), (54, 39), (41, 39)], True),                          # layered lames
    ("torso", "v", [(42, 45), (53, 45), (53, 46), (42, 46)], True),
    ("torso", "v", [(47, 40), (48, 40), (50, 43), (48, 47), (47, 47), (45, 43)], False),    # the core
    ("skirt", "v", [(41, 52), (54, 52), (54, 55), (41, 55)], True),                          # silver waist ring
]
# skirt: three plain tassets over a dark underlay (the swords float behind, nothing is sheathed)
PARTS += [("skirt", "f", [(31, 55), (64, 55), (64, 80), (31, 80)], True)]
PARTS += [
    ("skirt", "g", [(42, 55), (53, 55), (53, 79), (50, 85), (45, 85), (42, 79)], False),                       # centre tasset, long
]
PARTS += pair("skirt", "g", [(31, 55), (41, 55), (41, 73), (38, 78), (34, 74), (31, 69)], region_r="skirt")      # side tassets
PARTS += [
    ("skirt", "v", [(31, 55), (64, 55), (64, 57), (31, 57)], True),                                           # silver trim
    ("skirt", "b", [(46, 78), (49, 78), (49, 84), (46, 84)], True),                                           # tassel on the centre tasset
]

# raked, layered pauldrons
PARTS += pair("pauL", "g", [(31, 28), (29, 21), (35, 25), (41, 27), (41, 33), (32, 33)], region_r="pauR")
PARTS += pair("pauL", "g", [(30, 32), (41, 31), (41, 40), (35, 43), (30, 39)], region_r="pauR")
# wide hanging sleeve plates with scalloped hems (the robe, as plates)
PARTS += [
    ("armR", "g", [(61, 38), (66, 38), (68, 50), (62, 50)], False),
    ("armR", "g", [(60, 48), (70, 48), (71, 63), (69, 68), (66, 65), (64, 70), (61, 65), (60, 64)], False),   # right sleeve
    ("armR", "v", [(60, 48), (70, 48), (70, 50), (60, 50)], True),
    ("armL", "g", [(25, 38), (31, 38), (28, 50), (22, 50)], False),
    ("armL", "g", [(15, 49), (26, 49), (26, 63), (24, 66), (22, 64), (20, 68), (17, 64), (15, 63)], False),   # left sleeve
    ("armL", "v", [(15, 49), (26, 49), (26, 51), (15, 51)], True),
    ("armL", "g", [(18, 43), (25, 43), (26, 50), (19, 50)], False),                                           # forearm, vertical
]
# right hand: relaxed open hand hanging below the sleeve, fingers separate
PARTS += [
    ("handR", "s", [(62, 64), (69, 64), (70, 71), (67, 77), (63, 77), (61, 71)], False),
    ("handR", "s", [(62, 76), (64, 76), (64, 80), (62, 80)], False), ("handR", "s", [(65, 77), (67, 77), (67, 82), (65, 82)], False),
    ("handR", "s", [(68, 74), (70, 74), (70, 79), (68, 79)], False),
]
# 断锋: the one sword he really holds, upright in the near fist (long, narrow, a clear point, a jian guard, a crimson tassel)
PARTS += [
    ("sword", "s", [(15, 31), (21, 31), (21, 22), (20, 10), (18, 1), (16, 10), (15, 22)], False),             # blade
    ("sword", "v", [(17.5, 5), (18.5, 5), (18.5, 29), (17.5, 29)], True),                                    # fuller
    ("sword", "s", [(8, 31), (13, 29), (23, 29), (28, 31), (28, 34), (23, 32), (13, 32), (8, 34)], False),   # guard, tips curling up
    ("hand", "b", [(16, 43), (25, 43), (25, 46), (16, 46)], True),                                           # cuff
    ("hand", "s", [(12, 35), (24, 35), (25, 38), (25, 42), (22, 44), (14, 44), (11, 41), (11, 37)], False),  # fist closed round the grip
    ("hand", "g", [(13, 36), (23, 36), (24, 38), (13, 38)], False),                                          # knuckle row
    ("hand", "s", [(19, 33), (25, 33), (26, 37), (21, 38)], False),                                          # thumb over the fingers
    ("sword", "s", [(16, 45), (20, 45), (20, 48), (16, 48)], False),                                         # pommel
    ("sword", "b", [(17, 48), (19, 48), (19, 61), (17, 61)], True),                                          # tassel
]
# head: blank pearl face with a forehead sensor, lotus crown, short hairpin
PARTS += [
    ("head", "s", [(41, 7), (54, 7), (54, 9), (41, 9)], True),
    ("head", "b", [(40, 9), (41, 9), (41, 14), (40, 14)], True), ("head", "b", [(54, 9), (55, 9), (55, 14), (54, 14)], True),
    ("head", "s", [(42, 11), (44, 11), (42, 5)], False), ("head", "s", [(46, 11), (49, 11), (47, 1), (48, 1)], False),
    ("head", "s", [(51, 11), (53, 11), (53, 5)], False),
    ("head", "v", [(42, 11), (53, 11), (53, 14), (42, 14)], True),
    ("head", "f", [(44, 24), (51, 24), (51, 30), (44, 30)], True),                                     # short neck, in shadow
    ("head", "g", [(43, 14), (52, 14), (54, 18), (53, 22), (50, 25), (45, 25), (42, 22), (41, 18)], False),   # shorter, rounder face
    ("head", "v", [(47, 16), (48, 16), (50, 18), (48, 21), (47, 21), (45, 18)], False),                # smaller forehead sensor
]
DETAILS = [
    ("glow", 47, 18, 48, 19), ("v2", 47, 17, 48, 17),
    ("glow", 47, 42, 48, 45), ("out", 47, 31, 48, 32),
    ("out", 40, 41, 42, 41), ("out", 53, 41, 55, 41), ("out", 42, 49, 53, 49),
    ("out", 67, 70, 67, 76), ("out", 69, 70, 69, 76),
    ("out", 12, 40, 22, 40),                                                                                       # finger line across the fist
    ("out", 47, 60, 48, 76),                                                                                       # centre tasset crease
    ("v1", 73, 6, 73, 7), ("v1", 86, 14, 86, 15),                  # qi dashes by the floating swords
    ("glow", 18, 1, 18, 2),                                                                                        # tip of the held sword
    ("v1", 65, 40, 65, 46), ("v1", 63, 60, 63, 63),
]
STUDS = [("g3", 39, 32), ("g3", 56, 33), ("g3", 33, 27), ("g3", 62, 27), ("g3", 41, 42), ("g3", 54, 42), ("g3", 43, 50), ("g3", 52, 50),
         ("s3", 39, 74), ("s3", 45, 74), ("g3", 39, 82), ("g3", 56, 82), ("v2", 34, 56), ("v2", 60, 56), ("g3", 34, 61), ("g3", 60, 61),
         ("g3", 44, 66), ("g3", 50, 66), ("s3", 25, 33), ("s3", 70, 33), ("b3", 72, 20), ("b3", 72, 28), ("v2", 66, 14), ("v2", 45, 85),
         ("v2", 24, 82), ("s3", 66, 19), ("s3", 56, 36), ("g3", 44, 17), ("g3", 51, 17), ("g3", 44, 26), ("g3", 51, 26), ("s3", 47, 6),
         ("g3", 39, 80), ("g3", 58, 80), ("g3", 36, 62), ("g3", 43, 70), ("s3", 36, 76), ("s3", 59, 76), ("g3", 38, 84), ("g3", 56, 85),
         ("b3", 40, 12), ("b3", 55, 12), ("g3", 20, 56), ("g3", 22, 60), ("g3", 66, 55), ("g3", 69, 60), ("s3", 18, 36), ("s3", 23, 40),
         ("v2", 35, 38), ("s3", 62, 14), ("s3", 28, 78), ("s3", 18, 26), ("s3", 23, 24), ("g3", 19, 40), ("g3", 24, 34), ("g3", 32, 36),
         ("s3", 20, 56), ("g3", 64, 53), ("g3", 66, 36), ("g3", 36, 31), ("g3", 59, 31), ("s3", 69, 70), ("s3", 67, 79), ("s3", 59, 78),
         ("g3", 35, 61), ("g3", 61, 63), ("g3", 52, 62), ("g3", 52, 70), ("s3", 44, 80)]

# shift the right arm and hand 3 px outward so the ring plate is not covered by the sleeve
PARTS = [(r, rp, [(x + 3, y) for x, y in pl], fl) if r in ("armR", "handR") else (r, rp, pl, fl) for r, rp, pl, fl in PARTS]
VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(66, 40), fist=(68, 70), hipfix=False)


def render(view):
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = CONFIG["PAL"]; F.CONFIG["RAMP"] = CONFIG["RAMP"]
    try:
        return V.crop96(V.build(view, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def main():
    import os
    os.makedirs("out", exist_ok=True)
    img = render(VIEW)
    fails, rep = V.idle_checks("剑仙 front", img)
    A = img[..., 3] > 0
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum())
    rep["mirror_iou"] = round(iou, 2)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save("out/jx_front_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/jx_front_3x.png")
    names = ["approved/mojiang/mo_idle_front_1x.png", "approved/mingjiang/mj_idle_front_1x.png", "approved/tianbing96/views_idle_front_1x.png",
             "approved/wushi/ws_idle_front_1x.png", "approved/tianlong/tl_idle_front_1x.png"]
    sheet = Image.new("RGBA", (96 * 6, 96), (58, 62, 72, 255))
    sheet.alpha_composite(Image.fromarray(img, "RGBA"), (0, 0))
    for i, n in enumerate(names):
        sheet.alpha_composite(Image.open(n).convert("RGBA"), ((i + 1) * 96, 0))
    sheet.resize((96 * 18, 288), Image.NEAREST).save("out/jx_lineup_3x.png")
    print(rep)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
