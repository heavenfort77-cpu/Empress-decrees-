"""蛊师 (Gu Master, survivor and area-denier) front sample, 96x96, in the approved style (same renderer, light, outline, rivets).
Ideal: only what survives is kept, and everything is fed. Structure: a barrel-shaped sealed chamber torso with a round bone-rimmed window
and ONE amber survivor unit curled inside; a small domed head with two compound-eye lenses, bone mandibles and segmented antennae;
a ringed, insect-abdomen skirt; pincer hands. Declared asymmetry: the left shoulder carries a cluster of two round pods (single-function
pods, each with a hatch ring and an amber slot), the right shoulder carries one three-tube drone rack. No jar, no green cloud, no snake,
no Miao silver or indigo; the trail is a dark erosion residue (later).
Palette: chitin umber, bone ivory, dull iron, amber (the one live thing). Invented, no source colours.
Run: python3 gushi96.py -> out/gs_front_{1x,3x,5x}.png, out/gs_lineup_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#120d0a",
        "g1": "#3a2a22", "g2": "#7a5a43", "g3": "#b88d62",   # chitin umber
        "b1": "#6b6454", "b2": "#b3a88d", "b3": "#efe6cf",   # bone ivory: rims, mandibles, pincers
        "s2": "#8a7a66", "s3": "#d6c6a6",                    # dull iron: joints, caps
        "v0": "#8a5a14", "v1": "#e0a030", "v2": "#ffe27a",   # amber: the survivor, lenses, pod slots
        "glow": "#fff6c8",
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("g1", "s2", "s3"),
             "v": ("v0", "v1", "v2"), "f": ("out", "out", "out")},
}


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False, region_r=None):
    return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


import math


def circ(cy, r, n=28):
    """a circle centred on the mirror axis (47.5, cy): exact mirror pairs"""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        dx = r * math.cos(a)
        x = 48 + int(abs(dx)) if dx >= 0 else 47 - int(abs(dx))
        p = (x, round(cy + r * math.sin(a)))
        if not pts or pts[-1] != p: pts.append(p)
    return pts


def circ_at(cx, cy, r, n=16):
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        p = (round(cx + r * math.cos(a)), round(cy + r * math.sin(a)))
        if not pts or pts[-1] != p: pts.append(p)
    return pts


def seg(p0, p1, w):
    """a straight limb segment of width w from p0 to p1"""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    return [(round(p0[0] + nx), round(p0[1] + ny)), (round(p1[0] + nx), round(p1[1] + ny)),
            (round(p1[0] - nx), round(p1[1] - ny)), (round(p0[0] - nx), round(p0[1] - ny))]


PARTS = []
# legs: reverse-knee insect legs splayed out, thin and long (a different stance from the plated humanoids)
for pts, ramp, flat in [(seg((40, 70), (31, 79), 7), "g", False), (seg((31, 79), (26, 88), 5), "g", False),
                        ([(21, 88), (30, 88), (31, 91), (20, 91)], "g", False),
                        ([(19, 90), (22, 90), (21, 91), (19, 91)], "b", True), ([(24, 90), (27, 90), (26, 91), (24, 91)], "b", True)]:
    PARTS += pair("legL", ramp, pts, flat, region_r="legR")
PARTS += pair("legL", "b", [(28, 77), (34, 77), (33, 80), (28, 80)], True, region_r="legR")        # bone knee cap
# abdomen sac with ring bands (hangs below the vessel)
PARTS += [
    ("skirt", "g", [(37, 62), (58, 62), (60, 68), (57, 76), (50, 81), (45, 81), (38, 76), (35, 68)], False),
    ("skirt", "b", [(36, 66), (59, 66), (59, 67), (36, 67)], True),
    ("skirt", "b", [(38, 71), (57, 71), (57, 72), (38, 72)], True),
    ("skirt", "b", [(41, 76), (54, 76), (54, 77), (41, 77)], True),
]
# pods on the abdomen: left a cluster of three, right one big pod (declared asymmetry), each with a hatch ring and an amber slot
PARTS += [("pauL", "g", circ_at(31, 70, 5), False), ("pauL", "b", circ_at(31, 70, 3), False), ("pauL", "v", circ_at(31, 70, 1.5), False),
          ("pauL", "g", circ_at(25, 75, 4), False), ("pauL", "b", circ_at(25, 75, 2.4), False), ("pauL", "v", circ_at(25, 75, 1), False),
          ("pauL", "g", circ_at(33, 78, 3.4), False), ("pauL", "v", circ_at(33, 78, 1.2), False),
          ("pauR", "g", circ_at(66, 71, 7), False), ("pauR", "b", circ_at(66, 71, 4.6), False), ("pauR", "v", circ_at(66, 71, 2.4), False)]
# lower arms: hang down, thin, pincer claws
PARTS += [("armL", "g", seg((33, 52), (22, 58), 4), False), ("armL", "g", seg((22, 58), (20, 70), 4), False),
          ("hand", "b", seg((20, 70), (17, 78), 3), False), ("hand", "b", seg((20, 70), (23, 78), 3), False),
          ("armR", "g", seg((62, 52), (73, 58), 4), False), ("armR", "g", seg((73, 58), (76, 69), 4), False),
          ("hand", "b", seg((76, 69), (73, 77), 3), False), ("hand", "b", seg((76, 69), (79, 77), 3), False)]
# the sealed chamber: a big round vessel, bone-rimmed window, one amber survivor
PARTS += [
    ("torso", "f", circ(46, 18), True),
    ("torso", "g", circ(46, 17), False),
    ("torso", "b", circ(46, 11), False),
    ("torso", "f", circ(46, 9), True),
    ("torso", "v", [(44, 41), (51, 41), (54, 46), (51, 51), (44, 51), (41, 46)], False),
    ("torso", "v", [(46, 38), (49, 38), (51, 41), (44, 41)], False),
    ("torso", "b", [(42, 29), (53, 29), (55, 33), (40, 33)], True),                                  # bone collar
]
# upper arms: thin, raised, ending in open pincers (the right one lower: asymmetry)
PARTS += [("armL", "g", seg((35, 40), (22, 34), 4), False), ("armL", "g", seg((22, 34), (15, 23), 4), False),
          ("hand", "b", seg((15, 23), (11, 14), 3), False), ("hand", "b", seg((15, 23), (20, 14), 3), False),
          ("armR", "g", seg((60, 40), (72, 36), 4), False), ("armR", "g", seg((72, 36), (79, 29), 4), False),
          ("hand", "b", seg((79, 29), (75, 21), 3), False), ("hand", "b", seg((79, 29), (84, 22), 3), False)]
# head: small dome, visor, two lenses, mandibles, antennae
PARTS += pair("head", "b", seg((45, 11), (41, 5), 2), True) + pair("head", "b", seg((41, 5), (36, 2), 2), True)
PARTS += [
    ("head", "f", [(45, 22), (50, 22), (50, 30), (45, 30)], True),
    ("head", "g", [(42, 22), (41, 15), (44, 10), (51, 10), (54, 15), (53, 22)], False),
    ("head", "f", [(43, 14), (52, 14), (52, 19), (43, 19)], True),
    ("head", "v", [(44, 15), (47, 15), (47, 18), (44, 18)], False), ("head", "v", [(48, 15), (51, 15), (51, 18), (48, 18)], False),
] + pair("head", "b", [(43, 21), (46, 21), (45, 26), (44, 25)])
DETAILS = [
    ("out", 47, 43, 48, 50), ("glow", 45, 44, 46, 45), ("glow", 49, 44, 50, 45), ("v1", 40, 43, 40, 43), ("v1", 40, 47, 40, 47), ("v1", 55, 43, 55, 43), ("v1", 55, 47, 55, 47),
    ("glow", 45, 16, 46, 16), ("glow", 49, 16, 50, 16),
]
STUDS = [("g3", 39, 36), ("g3", 56, 36), ("g3", 34, 46), ("g3", 61, 46), ("g3", 38, 56), ("g3", 57, 56), ("g3", 42, 64), ("g3", 52, 64),
         ("g3", 44, 74), ("g3", 52, 73), ("g3", 40, 68), ("g3", 56, 69), ("g3", 22, 33), ("g3", 72, 35), ("g3", 21, 58), ("g3", 74, 57),
         ("g3", 28, 80), ("g3", 66, 80), ("g3", 47, 12), ("g3", 44, 12), ("b3", 38, 3), ("b3", 57, 3), ("g3", 31, 84), ("g3", 63, 84),
         ("g3", 47, 78), ("v2", 46, 43), ("v2", 50, 48), ("g3", 36, 49), ("g3", 59, 49), ("b3", 15, 17), ("b3", 80, 24)]
VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(66, 38), fist=(76, 70), hipfix=False)


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
    fails, rep = V.idle_checks("蛊师 front", img)
    A = img[..., 3] > 0
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum())
    rep["mirror_iou"] = round(iou, 2)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save("out/gs_front_1x.png")
    bg = Image.new("RGBA", (96, 96), (58, 62, 72, 255)); bg.alpha_composite(Image.fromarray(img, "RGBA"))
    for s in (3, 5):
        bg.resize((96 * s, 96 * s), Image.NEAREST).save(f"out/gs_front_{s}x.png")
    names = ["approved/jianxian/jx_idle_front_1x.png", "approved/mojiang/mo_idle_front_1x.png", "approved/mingjiang/mj_idle_front_1x.png",
             "approved/tianbing96/views_idle_front_1x.png", "approved/wushi/ws_idle_front_1x.png", "approved/tianlong/tl_idle_front_1x.png"]
    sheet = Image.new("RGBA", (96 * 7, 96), (58, 62, 72, 255))
    sheet.alpha_composite(Image.fromarray(img, "RGBA"), (0, 0))
    for i, n in enumerate(names):
        sheet.alpha_composite(Image.open(n).convert("RGBA"), ((i + 1) * 96, 0))
    sheet.resize((96 * 21, 288), Image.NEAREST).save("out/gs_lineup_3x.png")
    print(rep)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
