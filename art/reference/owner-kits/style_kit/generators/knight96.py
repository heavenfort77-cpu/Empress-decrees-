"""Knight (cocolito standard set, character 1 of 4) front sample at 96 in the Suit Mythology style: same renderer, light, outline, rivets as the
approved suits (tianbing96_v5.build through tianbing96_views). Original design: a great helm with a cross visor slit, bevelled breastplate,
cobalt tabard and plume, kite shield on the left arm, a long tapered sword raised in the right hand, greaves and sabatons.
Run: python3 knight96.py -> out/kn_front_1x.png, out/kn_front_3x.png, out/kn_vs_tianbing_3x.png (pass/fail only)"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#0d1418",
        "s1": "#2d3846", "s2": "#687a8a", "s3": "#aebfcc",   # plate steel (main body)
        "c1": "#1e2f5a", "c2": "#3a5aa0", "c3": "#7fa4e0",   # cobalt heraldry: tabard, shield field, plume base
        "b1": "#8a5a2b", "b2": "#c48c3c", "b3": "#f2cb6a",   # bronze trim, rivets, pommel
        "v1": "#c8432c", "v2": "#ff925c",                    # plume, shield chevron
        "glow": "#c2fff1",                                   # visor slit
    },
    "RAMP": {"g": ("s1", "s2", "s3"), "s": ("c1", "c2", "c3"), "b": ("b1", "b2", "b3"), "v": ("v1", "v1", "v2"), "f": ("out", "out", "out")},   # the renderer rivets "g" plates: steel is "g" here, cobalt is "s"
}


def mir(poly): return [(95 - x, y) for x, y in poly][::-1]
def pair(region, ramp, poly, flat=False, region_r=None): return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


LEG = [("f", [(36, 64), (45, 64), (44, 88), (36, 88)], True),
       ("s", [(37, 66), (44, 66), (43, 74), (37, 74)], False),        # cuisse
       ("b", [(35, 73), (45, 73), (45, 77), (35, 77)], False),        # knee cop, bronze
       ("s", [(36, 78), (44, 78), (44, 86), (37, 86)], False),        # greave
       ("s", [(33, 86), (45, 86), (46, 91), (32, 91)], False),        # sabaton
       ("b", [(32, 89), (36, 89), (36, 91), (32, 91)], True)]         # toe cap

PARTS = []
# sword (image right), raised: tapered blade, cross guard, grip, pommel; drawn first so the fist wraps it
PARTS += [
    ("sword", "g", [(66, 2), (71, 2), (72, 10), (72, 56), (65, 56), (65, 10)], False),     # blade 7 px wide, tapers to the tip at the top
    ("sword", "g", [(68, 0), (69, 0), (72, 10), (65, 10)], False),                         # point
    ("sword", "f", [(68, 10), (69, 10), (69, 52), (68, 52)], True),                        # fuller
    ("sword", "b", [(60, 56), (77, 56), (77, 59), (60, 59)], False),                       # cross guard
    ("sword", "b", [(66, 66), (71, 66), (71, 70), (66, 70)], False),                       # pommel
]
for ramp, poly, flat in LEG:
    PARTS += pair("legL", {"s": "g", "c": "s"}.get(ramp, ramp), poly, flat, region_r="legR")
PARTS += [
    ("torso", "f", [(37, 30), (58, 30), (58, 62), (37, 62)], True),                        # inner frame
    ("torso", "g", [(38, 31), (57, 31), (58, 44), (56, 58), (39, 58), (37, 44)], False),   # breastplate
    ("torso", "g", [(40, 32), (55, 32), (54, 40), (41, 40)], False),                       # upper chest bevel
]
PARTS += pair("skirt", "g", [(36, 56), (42, 56), (42, 70), (35, 68)])                     # tassets
PARTS += [
    ("skirt", "s", [(42, 54), (53, 54), (53, 74), (48, 77), (47, 77), (42, 74)], False),  # tabard front
    ("skirt", "b", [(38, 52), (57, 52), (57, 55), (38, 55)], False),                      # belt
    ("torso", "s", [(43, 42), (52, 42), (52, 52), (43, 52)], False),                      # tabard upper panel
]
# pauldrons: rounded, pointing up and out
PARTS += pair("pauL", "g", [(30, 28), (40, 26), (42, 34), (38, 40), (30, 38), (27, 33)], region_r="pauR")
# right arm (image right): raised with the sword, vambrace and gauntlet
PARTS += [
    ("armR", "f", [(62, 36), (72, 36), (72, 62), (62, 62)], True),
    ("armR", "g", [(63, 37), (71, 37), (71, 50), (63, 50)], False),                        # upper arm
    ("armR", "b", [(62, 48), (72, 48), (72, 51), (62, 51)], True),                         # elbow band
    ("armR", "g", [(63, 51), (71, 51), (71, 60), (63, 60)], False),                        # vambrace
    ("hand", "g", [(62, 59), (73, 59), (74, 66), (72, 68), (63, 68), (61, 66)], False),    # gauntlet on the grip
]
# left arm (image left) with the kite shield
PARTS += [
    ("armL", "g", [(28, 36), (36, 36), (36, 48), (28, 48)], False),                        # upper arm above the shield
    ("armL", "b", [(28, 42), (36, 42), (36, 44), (28, 44)], True),                         # elbow band
    ("hand", "g", [(27, 46), (36, 46), (37, 50), (36, 53), (28, 53), (26, 50)], False),    # gauntlet gripping the rim
    ("shield", "g", [(14, 50), (34, 50), (35, 64), (31, 76), (24, 84), (17, 76), (13, 64)], False),    # kite shield plate, held lower
    ("shield", "s", [(17, 53), (31, 53), (32, 63), (29, 73), (24, 80), (19, 73), (16, 63)], False),    # field
    ("shield", "v", [(19, 58), (24, 64), (29, 58), (29, 63), (24, 69), (19, 63)], True),               # chevron
]
# head: great helm, flat top with a slight taper, neck guard
PARTS += [
    ("head", "g", [(39, 10), (56, 10), (58, 14), (58, 27), (55, 31), (40, 31), (37, 27), (37, 14)], False),
    ("head", "g", [(40, 8), (55, 8), (57, 10), (38, 10)], False),                           # crown ridge
    ("head", "b", [(37, 20), (58, 20), (58, 22), (37, 22)], True),                          # brow band
    ("head", "v", [(45, 0), (50, 0), (52, 4), (51, 9), (44, 9), (43, 4)], False),            # plume
]

DETAILS = [
    ("glow", 41, 17, 46, 17), ("glow", 49, 17, 54, 17),      # visor slit, broken by the nasal bar
    ("out", 47, 15, 48, 27),                                  # nasal bar
    ("out", 41, 24, 43, 24), ("out", 44, 24, 46, 24), ("out", 49, 24, 51, 24), ("out", 52, 24, 54, 24),   # breaths
    ("out", 47, 42, 48, 76),                                  # tabard seam
    ("b3", 46, 46, 49, 46), ("b3", 46, 48, 49, 48),           # tabard emblem bars
    ("v2", 24, 65, 24, 66),                                   # chevron highlight
    ("out", 44, 61, 51, 61),
    ("s3", 65, 12, 65, 54), ("s1", 72, 12, 72, 54),           # blade edges: lit left, shaded right
]
STUDS = [("b3", 40, 33), ("b3", 55, 33), ("b3", 39, 57), ("b3", 56, 57), ("s3", 30, 30), ("s3", 65, 30), ("s3", 44, 11), ("s3", 51, 11),
         ("s3", 38, 69), ("s3", 57, 69), ("s3", 40, 80), ("s3", 55, 80), ("b3", 33, 88), ("b3", 62, 88), ("s3", 64, 39), ("s3", 64, 53),
         ("s3", 16, 54), ("s3", 32, 54), ("b3", 18, 73), ("b3", 30, 73), ("s3", 66, 60), ("v2", 46, 2), ("b3", 67, 67), ("b3", 61, 57), ("b3", 76, 57),
         ("s3", 69, 4), ("s3", 67, 30), ("s3", 36, 15), ("s3", 36, 26), ("b3", 44, 53), ("b3", 51, 53), ("s3", 42, 33), ("s3", 53, 33), ("s3", 39, 45), ("s3", 56, 45), ("b3", 37, 75), ("b3", 58, 75), ("s3", 21, 56), ("s3", 27, 56), ("s3", 70, 44), ("c3", 22, 60), ("c3", 26, 72), ("s3", 43, 83), ("s3", 52, 83), ("s3", 66, 14), ("s3", 66, 24), ("b3", 42, 56), ("b3", 53, 56), ("s3", 48, 12), ("s3", 37, 18), ("s3", 58, 18), ("s3", 30, 38), ("s3", 64, 42), ("b3", 46, 36), ("b3", 49, 36), ("s3", 41, 70), ("s3", 54, 70), ("s3", 20, 70), ("s3", 28, 70)]

VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(67, 40), fist=(68, 63), hipfix=False)


def render(view):
    keep_pal, keep_ramp = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = CONFIG["PAL"]; F.CONFIG["RAMP"] = CONFIG["RAMP"]
    try: return V.crop96(V.build(view, None))
    finally: F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep_pal, keep_ramp


def main():
    import os; os.makedirs("out", exist_ok=True)
    img = render(VIEW)
    fails, rep = V.idle_checks("knight front", img)
    A = img[..., 3] > 0; iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum()); rep["mirror_iou"] = round(iou, 2)
    Image.fromarray(img, "RGBA").save("out/kn_front_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/kn_front_3x.png")
    tb = np.asarray(Image.open("approved/tianbing96/views_idle_front_1x.png").convert("RGBA"))
    sheet = Image.new("RGBA", (96 * 2, 96), (58, 62, 72, 255))
    for i, im in enumerate((img, tb)): sheet.alpha_composite(Image.fromarray(im, "RGBA"), (i * 96, 0))
    sheet.resize((96 * 6, 288), Image.NEAREST).save("out/kn_vs_tianbing_3x.png")
    for name, im in (("knight", img), ("tianbing", tb)):
        a = im[..., 3] > 0; rgb = im[..., :3]; cols = len({tuple(p) for p in rgb[a]})
        pad = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode="edge"); ne = lambda x, y: (x != y).any(axis=2)
        d = ne(rgb, pad[:-2, 1:-1]) & ne(rgb, pad[2:, 1:-1]) & ne(rgb, pad[1:-1, :-2]) & ne(rgb, pad[1:-1, 2:])
        ys = np.nonzero(a)[0]; print(f"{name}: height {ys.max() - ys.min() + 1}, colours {cols}, isolated {(d & a).sum() / a.sum() * 100:.1f}%")
    print(rep); print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
