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
# winch-drum rack on the back: drums show over the shoulders
for ramp, poly, flat in [("b", [(31, 20), (41, 20), (41, 36), (31, 36)], False), ("v", [(31, 24), (41, 24), (41, 25), (31, 25)], True),
                         ("v", [(31, 31), (41, 31), (41, 32), (31, 32)], True), ("s", [(32, 17), (40, 17), (41, 20), (31, 20)], False)]:
    PARTS += pair("rack", ramp, poly, flat)
# paired post-mounted bows on the shoulders
PARTS += pair("bow", "b", [(28, 12), (24, 19), (21, 32), (24, 45), (28, 52), (26, 45), (24, 32), (26, 19)], False)
PARTS += pair("bow", "s", [(28, 12), (29, 12), (29, 52), (28, 52)], True)                      # bowstring
LEG = [("g", [(31, 60), (46, 60), (44, 72), (27, 72)], False),             # thigh
       ("s", [(26, 70), (44, 70), (44, 76), (26, 76)], False),             # knee plate
       ("g", [(28, 76), (42, 76), (41, 86), (29, 86)], False),             # shin
       ("v", [(29, 80), (42, 80), (42, 82), (29, 82)], True),              # bronze strap
       ("g", [(23, 86), (45, 86), (48, 89), (48, 91), (21, 91), (21, 89)], False),   # wide anchor foot
       ("b", [(20, 88), (25, 89), (25, 91), (19, 91)], True),              # toe stakes
       ("b", [(30, 89), (33, 89), (33, 91), (30, 91)], True)]
for ramp, poly, flat in LEG:
    PARTS += pair("legL", ramp, poly, flat, region_r="legR")
PARTS += [
    ("skirt", "g", [(34, 54), (61, 54), (64, 64), (31, 64)], False),
    ("skirt", "b", [(34, 54), (61, 54), (61, 57), (34, 57)], True),        # timber belt
    ("torso", "f", [(30, 34), (65, 34), (65, 58), (30, 58)], True),
    ("torso", "g", [(31, 36), (64, 36), (67, 44), (63, 56), (32, 56), (28, 44)], False),
    ("torso", "b", [(36, 41), (59, 41), (59, 43), (36, 43)], True),        # cross-braces
    ("torso", "b", [(36, 51), (59, 51), (59, 53), (36, 53)], True),
    ("torso", "v", [(47, 37), (48, 37), (48, 55), (47, 55)], True),        # the ink line, plumb
    ("neck", "g", [(41, 34), (54, 34), (54, 40), (41, 40)], False),
]
PARTS += pair("pauL", "g", [(21, 32), (36, 30), (38, 40), (31, 47), (21, 43)], region_r="pauR")
PARTS += pair("pauL", "b", [(25, 27), (30, 27), (30, 34), (25, 34)], True, region_r="pauR")     # bow post
# left arm: rope coil at the hip; right arm: grips the stake mallet
PARTS += [
    ("armL", "g", [(21, 42), (30, 42), (30, 54), (22, 54)], False),
    ("armL", "s", [(21, 53), (30, 53), (31, 58), (21, 58)], False),
    ("armL", "g", [(22, 57), (31, 57), (33, 64), (23, 65)], False),
    ("armL", "b", [(21, 62), (32, 62), (34, 70), (21, 71)], False),         # rope coil
    ("armR", "g", [(65, 42), (74, 42), (73, 54), (65, 54)], False),
    ("armR", "s", [(65, 53), (74, 53), (74, 58), (64, 58)], False),
    ("mallet", "b", [(70, 56), (73, 56), (73, 88), (70, 88)], True),        # haft, planted
    ("mallet", "s", [(62, 74), (82, 74), (82, 89), (62, 89)], False),       # square mallet head
    ("mallet", "v", [(62, 78), (82, 78), (82, 79), (62, 79)], True),
    ("mallet", "v", [(62, 85), (82, 85), (82, 86), (62, 86)], True),
    ("armR", "g", [(66, 56), (75, 56), (76, 64), (68, 66), (65, 62)], False),
    ("armR", "s", [(67, 61), (76, 61), (76, 66), (67, 66)], False),         # fist round the haft
]
# head: wide flat helm, visor slit, compass-ring mast
PARTS += [
    ("head", "s", [(47, 20), (49, 20), (49, 25), (47, 25)], False),         # mast
    ("head", "v", [(44, 11), (51, 11), (53, 15), (51, 20), (44, 20), (42, 15)], False),   # compass ring
    ("head", "g", [(38, 24), (57, 24), (61, 30), (60, 37), (35, 37), (34, 30)], False),
    ("head", "b", [(36, 26), (59, 26), (59, 28), (36, 28)], True),          # brim band
    ("head", "f", [(38, 31), (57, 31), (57, 35), (38, 35)], True),          # visor slit
]

DETAILS = [
    ("glow", 46, 12, 49, 18), ("out", 47, 14, 48, 16),         # compass ring: bright edge, dark eye
    ("v2", 41, 33, 54, 33),                                    # visor light
    ("v1", 45, 40, 50, 40), ("v1", 45, 45, 50, 45), ("v1", 45, 49, 50, 49), ("v1", 45, 53, 50, 53),   # ink-line ticks
    ("glow", 47, 46, 48, 47),
    ("out", 33, 61, 33, 70), ("out", 62, 61, 62, 70),
    ("out", 38, 80, 40, 80), ("out", 55, 80, 57, 80),
    ("b1", 71, 60, 72, 86),                                    # haft shade
]
STUDS = [("g3", 33, 38), ("g3", 62, 38), ("g3", 31, 44), ("g3", 64, 44), ("b3", 39, 42), ("b3", 56, 42), ("b3", 39, 52),
         ("b3", 56, 52), ("s3", 29, 74), ("s3", 66, 74), ("g3", 36, 62), ("g3", 59, 62), ("v2", 34, 81), ("v2", 61, 81),
         ("g3", 25, 33), ("g3", 70, 33), ("b3", 27, 28), ("b3", 68, 28), ("s3", 36, 18), ("s3", 59, 18), ("b3", 34, 22),
         ("b3", 62, 22), ("g3", 40, 26), ("g3", 55, 26), ("g3", 37, 33), ("g3", 58, 33), ("b3", 22, 64), ("b3", 28, 66),
         ("s3", 64, 78), ("s3", 80, 84), ("s3", 66, 87), ("b3", 71, 70), ("g3", 24, 47), ("g3", 70, 47), ("g3", 38, 58),
         ("g3", 57, 58), ("s3", 27, 72), ("s3", 66, 72), ("g3", 32, 82), ("g3", 63, 82), ("g3", 28, 88), ("g3", 67, 88),
         ("v2", 44, 15), ("v2", 51, 15), ("g3", 43, 34), ("g3", 52, 34), ("b3", 24, 90), ("b3", 71, 90), ("g3", 40, 66),
         ("g3", 55, 66), ("g3", 30, 54), ("g3", 66, 54), ("s3", 75, 60)]

VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(69, 44), fist=(72, 63), hipfix=False)


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
