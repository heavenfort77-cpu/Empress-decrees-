"""冥将 (Underworld General, assassin) front sample v3, 96x96 (shadow-cloak redraw), in the approved style (same renderer, light, outline, rivets).
Ideal: judgement that arrives unseen. Structure: a light, narrow frame (the thinnest of the suits so far); a blank pale mask under a
pointed hood (no face), and the chest sensor as the face (a vertical eye in a ribcage ring) so the face is where nobody looks;
one short reverse-grip sickle (a reaper's hook, not a chopper); tattered cloak and hem for the cloaked state later. Asymmetric: the axe arm and the open hand.
Run: python3 mingjiang96.py -> out/mj_front_{1x,3x}.png, out/mj_lineup_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#0b0e14",
        "g1": "#1c1a33", "g2": "#38345a", "g3": "#6f6a9a",   # shadow cloak: violet slate, lighter than the suit beneath
        "b1": "#7d7766", "b2": "#bdb6a2", "b3": "#ece6d4",   # bone: ribs, toe caps, grip
        "s2": "#6a7488", "s3": "#aab4c8",                    # steel: axe blade, joints
        "v0": "#4e2a8c", "v1": "#8a52e0", "v2": "#c9a0ff",   # cold violet glow: the chest sensor
        "glow": "#efe2ff",                                   # sensor core
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("g1", "s2", "s3"),
             "u": ("out", "g1", "g2"),                       # the dark suit under the cloak
             "v": ("v0", "v1", "v2"), "f": ("out", "out", "out")},
}


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False, region_r=None):
    return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


PARTS = []
# back of the cloak: wide, ragged hem of long points (the shadow that trails the assassin)
PARTS += [("cloak", "g", [(38, 29), (57, 29), (66, 36), (70, 50), (74, 68), (70, 74), (73, 86), (66, 80), (63, 91), (57, 82), (52, 90),
                          (47, 83), (44, 91), (39, 82), (34, 90), (31, 80), (24, 86), (25, 74), (21, 68), (25, 50), (29, 36)], False)]
# crouched legs: knees out, shins in, inside the cloak
LEG = [("f", [(41, 58), (48, 58), (44, 76), (36, 76)], True),
       ("u", [(42, 60), (47, 60), (43, 74), (38, 74)], False),
       ("s", [(35, 74), (44, 74), (44, 79), (35, 79)], False),
       ("u", [(37, 79), (43, 79), (43, 87), (38, 87)], False),
       ("u", [(34, 87), (44, 87), (47, 91), (33, 91)], False),
       ("b", [(33, 89), (37, 89), (37, 91), (33, 91)], True)]
for ramp, poly, flat in LEG:
    PARTS += pair("legL", ramp, poly, flat, region_r="legR")
PARTS += [
    ("torso", "f", [(42, 32), (53, 32), (53, 58), (42, 58)], True),
    ("torso", "u", [(43, 33), (52, 33), (52, 56), (47, 58), (43, 56)], False),               # the suit seen through the opening
    ("torso", "b", [(43, 37), (52, 37), (52, 38), (43, 38)], True),
    ("torso", "b", [(43, 47), (52, 47), (52, 48), (43, 48)], True),
    ("torso", "s", [(44, 39), (51, 39), (52, 43), (52, 47), (50, 51), (45, 51), (43, 47), (43, 43)], False),   # sensor ring
    ("torso", "v", [(45, 40), (50, 40), (51, 44), (50, 49), (45, 49), (44, 44)], False),                      # the vertical eye
    ("skirt", "b", [(43, 54), (52, 54), (52, 57), (43, 57)], True),                                           # belt
]
# front flaps of the cloak, held open at the chest: lighter, with ragged lower edges
PARTS += pair("pauL", "g", [(36, 31), (43, 32), (43, 56), (41, 72), (36, 68), (32, 80), (28, 70), (27, 52), (30, 38)], region_r="pauR")
# left arm tucked under the flap (open hand shows below it); right arm out, reverse-grip axe, blade down
PARTS += [
    ("armL", "s", [(28, 70), (36, 70), (38, 76), (35, 80), (31, 79), (27, 75)], False),                     # open hand
    ("armR", "f", [(58, 38), (64, 38), (69, 58), (63, 60)], True),
    ("armR", "u", [(59, 39), (63, 39), (67, 55), (63, 57)], False),
    ("armR", "s", [(62, 53), (68, 53), (69, 58), (63, 58)], False),
    ("axe", "s", [(68, 50), (71, 50), (72, 72), (69, 72)], True),                                            # short haft, butt up
    ("axe", "v", [(67, 48), (72, 48), (72, 51), (67, 51)], False),                                           # butt cap glow
    ("axe", "s", [(69, 66), (77, 66), (84, 69), (88, 75), (87, 82), (82, 88), (77, 89), (80, 83), (82, 77), (79, 73), (72, 73), (69, 72)], False),  # sickle blade, hooked
    ("axe", "f", [(74, 68), (80, 69), (84, 74), (83, 79)], True),
    ("axe", "b", [(68, 58), (73, 58), (73, 62), (68, 62)], True),                                            # grip wrap
    ("armR", "s", [(65, 56), (73, 56), (74, 63), (70, 65), (65, 62)], False),                               # fist
]
# head: deep pointed hood, the opening is a void (the face is on the chest)
PARTS += [
    ("head", "g", [(39, 26), (41, 17), (45, 11), (48, 8), (50, 11), (54, 17), (56, 26), (53, 32), (42, 32)], False),
    ("head", "f", [(43, 18), (52, 18), (54, 25), (50, 31), (45, 31), (41, 25)], True),
]

DETAILS = [
    ("v2", 47, 41, 48, 47), ("glow", 47, 43, 48, 45),        # eye: bright edge and core
    ("out", 47, 59, 48, 74),                                 # hem seam on the back
    ("out", 40, 40, 41, 52), ("out", 54, 40, 55, 52),        # flap folds
    ("b1", 45, 19, 50, 19),                                  # one faint bone line deep in the hood: the mask edge
    ("out", 38, 78, 40, 78), ("out", 55, 78, 57, 78),
]
STUDS = [("g3", 38, 31), ("g3", 57, 31), ("b3", 45, 37), ("b3", 50, 37), ("s3", 36, 76), ("s3", 59, 76),
         ("g3", 32, 44), ("g3", 63, 44), ("g3", 28, 56), ("g3", 67, 56), ("g3", 24, 72), ("g3", 71, 72),
         ("g3", 31, 84), ("g3", 64, 84), ("g3", 47, 88), ("g3", 40, 86), ("g3", 55, 86), ("v2", 70, 45),
         ("s3", 85, 76), ("s3", 83, 86), ("b3", 36, 90), ("b3", 59, 90), ("g3", 44, 13), ("g3", 52, 14),
         ("g3", 41, 22), ("g3", 55, 22), ("s3", 32, 77), ("g3", 34, 60), ("g3", 61, 60), ("b3", 45, 47),
         ("b3", 50, 47), ("g3", 38, 66), ("g3", 56, 66), ("s3", 67, 61), ("g3", 29, 41), ("g3", 66, 41),
         ("g3", 34, 36), ("g3", 61, 36), ("g3", 26, 62), ("g3", 69, 62), ("g3", 50, 78), ("g3", 45, 80),
         ("g3", 30, 48), ("g3", 65, 48), ("g3", 27, 66), ("g3", 68, 66), ("g3", 33, 74), ("g3", 62, 74), ("g3", 36, 56), ("g3", 59, 56),
         ("g3", 41, 20), ("g3", 54, 28), ("g3", 40, 30), ("g3", 56, 30), ("s3", 69, 74), ("s3", 86, 82), ("g3", 22, 72), ("g3", 73, 72),
         ("g3", 26, 80), ("g3", 69, 80), ("g3", 36, 84), ("g3", 59, 84), ("g3", 43, 90), ("g3", 52, 88), ("g3", 31, 52), ("g3", 64, 52)]

VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(61, 40), fist=(70, 62), hipfix=False)


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
    fails, rep = V.idle_checks("冥将 front", img)
    A = img[..., 3] > 0
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum())
    rep["mirror_iou"] = round(iou, 2)
    ys, xs = np.nonzero(A)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save("out/mj_front_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/mj_front_3x.png")
    names = ["approved/tianbing96/views_idle_front_1x.png", "approved/wushi/ws_idle_front_1x.png", "approved/tianlong/tl_idle_front_1x.png"]
    sheet = Image.new("RGBA", (96 * 4, 96), (58, 62, 72, 255))
    sheet.alpha_composite(Image.fromarray(img, "RGBA"), (0, 0))
    for i, n in enumerate(names):
        sheet.alpha_composite(Image.open(n).convert("RGBA"), ((i + 1) * 96, 0))
    sheet.resize((96 * 12, 288), Image.NEAREST).save("out/mj_lineup_3x.png")
    print(rep)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
