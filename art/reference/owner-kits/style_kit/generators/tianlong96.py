"""天龙 (Heavenly Dragon, artillery) front sample, 96x96, in the approved style (same renderer, light, outline, rivets).
Myth -> structure: antler crown on a snake-neck sensor mast (the spotter), the flaming pearl as the reactor that fires,
heavy back thrusters (the dash), a wide planted stance, a segmented serpent tail. Four claws, never five (imperial rank).
Run: python3 tianlong96.py -> out/tl_front_{1x,3x}.png, out/tl_lineup_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#0d1418",
        "g1": "#173a5e", "g2": "#2f6fa8", "g3": "#7cc4e8",   # azure scale armour
        "b1": "#8c7a5c", "b2": "#c9b88c", "b3": "#f0e6c4",   # ivory: antlers, claws, tail bands
        "s2": "#6d7f90", "s3": "#b8c6d2",                    # steel (shade shares the azure shade)
        "v0": "#a33a1c", "v1": "#e8702a", "v2": "#ffc05a",   # pearl flame, thruster fire
        "glow": "#e9fbff",                                   # pearl core, sensor eyes
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("g1", "s2", "s3"),
             "v": ("v0", "v1", "v2"), "f": ("out", "out", "out"),
             "p": ("s3", "glow", "glow")},   # pearl: flat glow fill (not region-shaded), shade added as detail
}


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False, region_r=None):
    return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


PARTS = []
# back thrusters, behind everything, nozzles pointing down and out
PARTS += pair("thrust", "s", [(22, 12), (30, 16), (36, 40), (28, 44), (19, 30)])     # tall thruster pods rise behind the shoulders
PARTS += pair("thrust", "g", [(21, 13), (25, 10), (29, 16), (24, 20)])              # pod intake caps
PARTS += pair("thrust", "v", [(24, 42), (30, 44), (29, 50), (23, 47)])
# serpent tail from behind the right hip (image right), curling on the ground
PARTS += [
    ("tail", "g", [(56, 60), (64, 62), (68, 72), (60, 72)], False),
    ("tail", "b", [(60, 70), (68, 70), (70, 74), (61, 75)], True),
    ("tail", "g", [(62, 74), (70, 73), (76, 82), (68, 85)], False),
    ("tail", "b", [(69, 82), (76, 80), (78, 84), (71, 87)], True),
    ("tail", "g", [(72, 85), (79, 82), (86, 84), (84, 90), (74, 91)], False),
    ("tail", "b", [(84, 82), (91, 77), (90, 85), (86, 89)], False),          # tail fin
]
LEG = [("g", [(36, 58), (46, 58), (42, 72), (32, 72)], False),             # thigh
       ("s", [(30, 70), (41, 70), (41, 76), (30, 76)], False),             # knee
       ("g", [(31, 76), (40, 76), (39, 86), (32, 86)], False),             # shin
       ("s", [(28, 86), (42, 86), (43, 89), (27, 89)], False),             # foot
       ("b", [(27, 89), (30, 89), (29, 91), (26, 91)], True),              # three toe claws
       ("b", [(33, 89), (36, 89), (36, 91), (33, 91)], True),
       ("b", [(39, 89), (42, 89), (43, 91), (40, 91)], True)]
for ramp, poly, flat in LEG:
    PARTS += pair("legL", ramp, poly, flat, region_r="legR")
PARTS += [
    ("skirt", "g", [(38, 52), (57, 52), (58, 61), (37, 61)], False),
    ("skirt", "b", [(39, 52), (56, 52), (56, 55), (39, 55)], True),
    ("torso", "f", [(38, 30), (57, 30), (57, 54), (38, 54)], True),
    ("torso", "g", [(36, 32), (59, 32), (61, 38), (56, 50), (48, 55), (47, 55), (39, 50), (34, 38)], False),   # keel breastplate
]
PARTS += [("neck", "s", [(44, 16), (51, 16), (52, 31), (43, 31)], False)]           # snake-neck sensor mast
for y in (20, 24, 28):
    PARTS += [("neck", "b", [(43, y), (52, y), (52, y + 1), (43, y + 1)], True)]      # ivory rings
PARTS += pair("pauL", "g", [(28, 30), (36, 27), (40, 32), (38, 40), (30, 41), (26, 36)], region_r="pauR")
# arms: both claws bring the pearl in front of the belly
ARM = [("g", [(27, 38), (34, 38), (35, 50), (28, 50)], False),
       ("s", [(27, 49), (35, 49), (35, 54), (27, 54)], False),
       ("g", [(29, 53), (35, 51), (42, 56), (38, 61)], False),
       ("s", [(37, 51), (43, 51), (43, 60), (37, 60)], False)]
for ramp, poly, flat in ARM:
    PARTS += pair("armL", ramp, poly, flat, region_r="armR")
# flaming pearl (the reactor that fires), in front
PARTS += [
    ("pearl", "v", [(42, 48), (43, 36), (47, 44)], False),           # flame tongues
    ("pearl", "v", [(47, 44), (51, 33), (54, 46)], False),
    ("pearl", "v", [(52, 47), (57, 40), (56, 50)], False),
    ("pearl", "p", [(45, 43), (50, 43), (55, 48), (55, 56), (50, 61), (45, 61), (40, 56), (40, 48)], False),
]
PARTS += pair("armL", "b", [(40, 49), (44, 48), (43, 53)], True, region_r="armR")   # claw tips on the pearl
PARTS += pair("armL", "b", [(40, 57), (44, 58), (42, 61)], True, region_r="armR")
# head: faceless dragon sensor head on the mast, barbels, antler crown
PARTS += [("head", "g", [(38, 9), (57, 9), (58, 12), (55, 15), (52, 19), (43, 19), (40, 15), (37, 12)], False)]   # skull, tapering to the muzzle
PARTS += [("head", "s", [(43, 15), (52, 15), (51, 19), (44, 19)], False)]           # muzzle plate
PARTS += pair("head", "b", [(36, 8), (40, 8), (47, 11), (47, 12), (44, 12)], True)   # brow ridge, slanting down to the centre
PARTS += pair("head", "b", [(43, 19), (45, 19), (44, 22)], True)                     # fangs
PARTS += pair("head", "b", [(42, 17), (43, 17), (39, 21), (38, 21)], True)           # barbels from the muzzle (short)
PARTS += pair("head", "b", [(41, 9), (43, 8), (39, 2), (37, 2)], False)               # antler beam
PARTS += pair("head", "b", [(38, 5), (39, 6), (34, 5), (32, 3)], False)               # antler tine

DETAILS = [
    ("out", 39, 11, 45, 13), ("out", 50, 11, 56, 13),        # eye sockets under the brows
    ("glow", 40, 11, 41, 11), ("glow", 42, 12, 44, 12),      # eye slits slanting down to the centre
    ("glow", 54, 11, 55, 11), ("glow", 51, 12, 53, 12),
    ("out", 45, 17, 45, 17), ("out", 50, 17, 50, 17),        # nostrils
    ("s3", 53, 52, 53, 56), ("s3", 50, 59, 52, 59), ("s3", 52, 57, 52, 58),   # pearl shade, lower right
    ("v1", 44, 50, 46, 50), ("v1", 46, 51, 46, 52), ("v1", 47, 53, 49, 53),   # flame swirl inside the pearl
    ("v2", 43, 40, 43, 41), ("v2", 50, 37, 50, 38),
    ("out", 37, 38, 42, 38), ("out", 53, 38, 58, 38),        # scale rows on the breastplate
    ("out", 39, 43, 44, 43), ("out", 51, 43, 56, 43),
    ("out", 34, 78, 37, 78), ("out", 58, 78, 61, 78),        # shin seams
    ("out", 40, 57, 55, 57),                                 # skirt seam
]
STUDS = [("g3", 37, 35), ("g3", 58, 35), ("b3", 30, 33), ("b3", 65, 33), ("s3", 33, 72), ("s3", 62, 72),
         ("g3", 39, 47), ("g3", 56, 47), ("b3", 46, 22), ("b3", 49, 26), ("s3", 29, 30), ("s3", 66, 30),
         ("g3", 41, 14), ("g3", 54, 14), ("s3", 47, 16), ("g3", 64, 66), ("g3", 73, 78), ("g3", 80, 86),
         ("b3", 34, 87), ("b3", 61, 87), ("s3", 43, 47), ("glow", 44, 49), ("g3", 31, 44), ("g3", 64, 44),
         ("s3", 30, 52), ("s3", 65, 52), ("g3", 35, 80), ("g3", 60, 80), ("v2", 26, 44), ("v2", 69, 44),
         ("g3", 41, 60), ("g3", 54, 60), ("s3", 33, 24), ("s3", 62, 24), ("g3", 48, 34)]

VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(31, 39), fist=(40, 56), hipfix=False)


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
    fails, rep = V.idle_checks("天龙 front", img)
    A = img[..., 3] > 0
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum())
    rep["mirror_iou"] = round(iou, 2)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save("out/tl_front_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/tl_front_3x.png")
    tb = np.asarray(Image.open("approved/tianbing96/views_idle_front_1x.png").convert("RGBA"))
    ws = np.asarray(Image.open("approved/wushi/ws_idle_front_1x.png").convert("RGBA"))
    sheet = Image.new("RGBA", (96 * 3, 96), (58, 62, 72, 255))
    for i, im in enumerate((img, tb, ws)):
        sheet.alpha_composite(Image.fromarray(im, "RGBA"), (i * 96, 0))
    sheet.resize((96 * 9, 288), Image.NEAREST).save("out/tl_lineup_3x.png")
    print(rep)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
