"""墨将 (Mo General, defender and builder) front sample, 96x96, in the approved style (same renderer, light, outline, rivets).
Ideal: care for all, defence only; strong where it stands. Structure: a low, wide, planted chassis; splayed anchor feet with toe stakes;
paired post-mounted bows on the shoulders (the repeating-crossbow cart); a winch-drum rack on the back, drums showing over the
shoulders; a faceless helm with a visor slit and a compass-ring mast; the ink-line emblem (a plumb line with tick marks) on the chest.
Builder kit: a square-faced stake mallet planted at the right side; a rope coil at the left hip. Palette: matte ink, aged timber and rope,
verdigris bronze (no source for Mohist colours; the ink is the pun on 墨).
Run: python3 mojiang96.py -> out/mo_front_{1x,3x}.png, out/mo_lineup_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#0a0c10",
        "g1": "#151a22", "g2": "#2a3240", "g3": "#52607a",   # matte ink: cool black-slate
        "b1": "#5a3d28", "b2": "#8f6340", "b3": "#cf9a62",   # aged timber and rope
        "s2": "#5f6c7c", "s3": "#aab8c8",                    # steel: mallet face, joints
        "v0": "#2a5f55", "v1": "#3f9a87", "v2": "#8fe0c8",   # verdigris bronze: bands, ink-line, compass ring
        "glow": "#e8fff6",                                   # sensor core
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("g1", "s2", "s3"),
             "v": ("v0", "v1", "v2"), "f": ("out", "out", "out")},
}


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False, region_r=None):
    return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


PARTS = []
# rounded pauldrons first, then the crossbows mounted on them
PARTS += pair("pauL", "g", [(20, 37), (27, 32), (36, 33), (40, 40), (36, 48), (25, 48), (19, 43)], region_r="pauR")
PARTS += pair("pauL", "v", [(21, 41), (37, 41), (37, 43), (21, 43)], True, region_r="pauR")           # bronze band
# repeating crossbows: arched limbs, a string across the tips, a loaded bolt, a magazine box on the shoulder
PARTS += pair("bow", "b", [(10, 31), (11, 24), (16, 19), (23, 17), (29, 19), (32, 24), (33, 31), (29, 31), (28, 26), (25, 22),
                           (23, 21), (20, 22), (16, 26), (14, 31)], False)
PARTS += pair("bow", "s", [(10, 31), (33, 31), (33, 32), (10, 32)], True)                          # string
PARTS += pair("bow", "s", [(22, 21), (24, 21), (24, 33), (22, 33)], True)                          # bolt
PARTS += pair("bow", "s", [(21, 18), (25, 18), (23, 14)], True)                                    # bolt head
PARTS += pair("bow", "b", [(17, 33), (28, 33), (28, 40), (17, 40)], False)                         # magazine box
PARTS += pair("bow", "v", [(17, 36), (28, 36), (28, 37), (17, 37)], True)
# legs: tapered shins, wide anchor feet with toe stakes, knee plates
LEG = [("g", [(31, 74), (44, 74), (42, 86), (32, 86)], False),
       ("s", [(30, 73), (44, 73), (43, 78), (31, 78)], False),                  # knee plate
       ("v", [(32, 81), (43, 81), (43, 83), (32, 83)], True),                   # bronze strap
       ("g", [(26, 86), (45, 86), (47, 90), (47, 91), (24, 91), (24, 89)], False),
       ("b", [(21, 88), (27, 89), (27, 91), (20, 91)], True)]                   # toe stake
for ramp, poly, flat in LEG:
    PARTS += pair("legL", ramp, poly, flat, region_r="legR")
# skirt as a rampart: a-line plates, crenellated hem
PARTS += [("skirt", "g", [(37, 58), (58, 58), (66, 70), (29, 70)], False),
          ("skirt", "b", [(40, 56), (55, 56), (55, 59), (40, 59)], True)]               # timber belt
for x0, x1 in ((29, 33), (37, 41), (45, 50), (54, 58), (62, 66)):
    PARTS += [("skirt", "g", [(x0, 69), (x1, 69), (x1, 74), (x0, 74)], False)]
PARTS += [
    ("torso", "f", [(32, 36), (63, 36), (60, 50), (55, 58), (40, 58), (35, 50)], True),
    ("torso", "g", [(33, 37), (62, 37), (59, 50), (54, 56), (41, 56), (36, 50)], False),     # V-shaped chest
    ("torso", "b", [(36, 43), (59, 43), (59, 44), (36, 44)], True),                   # lames
    ("torso", "b", [(38, 49), (57, 49), (56, 50), (39, 50)], True),
    ("torso", "v", [(47, 38), (48, 38), (48, 57), (47, 57)], True),                   # the ink line, plumb
    ("torso", "v", [(38, 39), (40, 39), (40, 47), (45, 47), (45, 49), (38, 49)], False),   # carpenter's square
    ("neck", "g", [(42, 34), (53, 34), (53, 40), (42, 40)], False),
]
# plumb bob on its line, hanging over the skirt
PARTS += [("torso", "v", [(47, 58), (48, 58), (48, 65), (47, 65)], True),
          ("torso", "v", [(47, 64), (51, 69), (47, 75), (44, 69)], False)]
# left arm: rope coil at the hip; right arm: grips a banded wooden mallet planted at the side
PARTS += [
    ("armL", "g", [(21, 46), (30, 46), (30, 56), (22, 56)], False),
    ("armL", "s", [(21, 55), (31, 55), (32, 60), (21, 60)], False),
    ("armL", "b", [(19, 61), (32, 61), (34, 71), (20, 72)], False),                  # rope coil
    ("armR", "g", [(65, 46), (74, 46), (73, 56), (65, 56)], False),
    ("armR", "s", [(64, 55), (74, 55), (74, 60), (64, 60)], False),
    ("mallet", "b", [(69, 58), (72, 58), (72, 88), (69, 88)], True),
    ("mallet", "b", [(63, 74), (79, 74), (79, 88), (63, 88)], False),                # cylinder head, axis horizontal
    ("mallet", "s", [(61, 75), (64, 75), (64, 87), (61, 87)], False),
    ("mallet", "s", [(78, 75), (81, 75), (81, 87), (78, 87)], False),
    ("mallet", "v", [(64, 78), (78, 78), (78, 79), (64, 79)], True),
    ("mallet", "v", [(64, 83), (78, 83), (78, 84), (64, 84)], True),
    ("armR", "s", [(66, 60), (76, 60), (76, 66), (66, 66)], False),                  # fist round the haft
]
# head: domed helm with a crenellated crown, visor slit, compass crest rising from it
PARTS += [
    ("head", "v", [(46, 6), (48, 6), (42, 19), (40, 19)], False), ("head", "v", [(47, 6), (49, 6), (55, 19), (53, 19)], False),
    ("head", "v", [(45, 3), (50, 3), (52, 6), (50, 9), (45, 9), (43, 6)], False),     # compass hinge ring
    ("head", "g", [(37, 38), (37, 29), (40, 24), (44, 21), (47, 20), (48, 20), (51, 21), (55, 24), (58, 29), (58, 38)], False),
    ("head", "f", [(39, 30), (56, 30), (56, 35), (39, 35)], True),                   # visor slit
]
for x0, x1 in ((39, 41), (43, 45), (50, 52), (54, 56)):
    PARTS += [("head", "s", [(x0, 18), (x1, 18), (x1, 24), (x0, 24)], False)]       # merlons
PARTS += [("head", "b", [(37, 36), (58, 36), (58, 38), (37, 38)], True)]               # chin band

DETAILS = [
    ("glow", 47, 5, 48, 7), ("out", 47, 6, 48, 6),            # compass ring eye
    ("v2", 40, 32, 55, 32),                                   # visor light
    ("v1", 46, 41, 46, 41), ("v1", 49, 41, 49, 41), ("v1", 46, 45, 46, 45), ("v1", 49, 45, 49, 45),
    ("v1", 46, 52, 46, 52), ("v1", 49, 52, 49, 52),           # ticks on the ink line
    ("glow", 47, 68, 48, 70),                                 # plumb bob glint
    ("out", 33, 60, 33, 72), ("out", 62, 60, 62, 72),
    ("b1", 71, 60, 71, 86),                                   # haft shade
    ("out", 34, 76, 34, 76), ("out", 61, 76, 61, 76),
]
STUDS = [("g3", 34, 38), ("g3", 61, 38), ("g3", 31, 36), ("g3", 64, 36), ("b3", 39, 44), ("b3", 56, 44), ("b3", 41, 50),
         ("b3", 54, 50), ("s3", 31, 75), ("s3", 64, 75), ("g3", 38, 62), ("g3", 57, 62), ("v2", 35, 82), ("v2", 60, 82),
         ("g3", 24, 36), ("g3", 71, 36), ("b3", 12, 28), ("b3", 83, 28), ("s3", 23, 19), ("s3", 72, 19), ("b3", 19, 38),
         ("b3", 76, 38), ("g3", 40, 27), ("g3", 55, 27), ("s3", 40, 20), ("s3", 55, 20), ("b3", 22, 64), ("b3", 29, 66),
         ("s3", 65, 78), ("s3", 79, 86), ("s3", 62, 84), ("b3", 71, 72), ("g3", 24, 44), ("g3", 70, 44), ("g3", 40, 66),
         ("g3", 55, 66), ("s3", 33, 76), ("s3", 62, 76), ("g3", 34, 84), ("g3", 61, 84), ("g3", 29, 88), ("g3", 66, 88),
         ("v2", 44, 5), ("v2", 51, 5), ("g3", 44, 36), ("g3", 51, 36), ("b3", 25, 90), ("b3", 70, 90), ("g3", 44, 54),
         ("g3", 51, 54), ("g3", 28, 50), ("g3", 67, 50), ("s3", 75, 62), ("b3", 21, 66), ("s3", 14, 25), ("s3", 81, 25),
         ("v2", 21, 42), ("v2", 74, 42), ("g3", 36, 68), ("g3", 59, 68), ("s3", 46, 16), ("g3", 38, 33), ("g3", 57, 33),
         ("b3", 14, 27), ("b3", 81, 27), ("b3", 19, 22), ("b3", 76, 22), ("s3", 23, 27), ("s3", 72, 27), ("b3", 20, 35), ("b3", 75, 35),
         ("g3", 31, 62), ("g3", 64, 62), ("g3", 36, 72), ("g3", 59, 72), ("s3", 43, 47), ("s3", 52, 47), ("g3", 40, 79), ("g3", 55, 79)]

VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(69, 48), fist=(71, 63), hipfix=False)


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
    fails, rep = V.idle_checks("墨将 front", img)
    A = img[..., 3] > 0
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum())
    rep["mirror_iou"] = round(iou, 2)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save("out/mo_front_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/mo_front_3x.png")
    names = ["approved/mingjiang/mj_idle_front_1x.png", "approved/tianbing96/views_idle_front_1x.png",
             "approved/wushi/ws_idle_front_1x.png", "approved/tianlong/tl_idle_front_1x.png"]
    sheet = Image.new("RGBA", (96 * 5, 96), (58, 62, 72, 255))
    sheet.alpha_composite(Image.fromarray(img, "RGBA"), (0, 0))
    for i, n in enumerate(names):
        sheet.alpha_composite(Image.open(n).convert("RGBA"), ((i + 1) * 96, 0))
    sheet.resize((96 * 15, 288), Image.NEAREST).save("out/mo_lineup_3x.png")
    print(rep)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
