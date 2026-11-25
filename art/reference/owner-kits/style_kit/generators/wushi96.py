"""巫师 (Wu shaman / necromancer) front sample, 96x96, in the approved 天兵 style (same renderer, light, outline, rivets).
Myth -> structure: the fangxiangshi exorcist (four gold eyes, black over red, ge-lance and shield, bearskin, twelve beasts).
Role: stuns, then raises fallen mechs as followers at about 70% of their stats. The puppet look is an overlay
drawn over ANY fallen unit (not a new character), so it is made here as a function of a sprite's silhouette.
Run: python3 wushi96.py -> out/ws_front_{1x,3x}.png, out/ws_drones_3x.png, out/puppet_tianbing_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V

CONFIG = {
    "PAL": {
        "out": "#0d1418",
        "g1": "#1c1620", "g2": "#3b2f42", "g3": "#75637e",   # black lacquer / bearskin (violet-black)
        "v0": "#6a1a20", "v1": "#b3322b", "v2": "#e8674a",   # red robe and mask
        "b1": "#8a5a2b", "b2": "#c48c3c", "b3": "#f2cb6a",   # ritual bronze and gold (gold eyes)
        "s2": "#687a8a", "s3": "#aebfcc",                    # steel (shade shares the black mid)
        "glow": "#6ff0c8",                                   # soul-fire: chest gem, drones, puppet mark
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "v": ("v0", "v1", "v2"), "b": ("b1", "b2", "b3"),
             "s": ("g2", "s2", "s3"), "f": ("out", "out", "out")},
    "SOUL": "#6ff0c8",
}


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False, region_r=None):
    return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


LEG = [("f", [(36, 66), (44, 66), (43, 88), (36, 88)], True),
       ("g", [(37, 68), (43, 68), (42, 86), (37, 86)], False),
       ("s", [(35, 73), (44, 73), (44, 78), (35, 78)], False),       # knee
       ("g", [(36, 79), (43, 79), (43, 86), (37, 86)], False),       # shin guard
       ("g", [(33, 86), (44, 86), (45, 91), (32, 91)], False),       # boot
       ("b", [(32, 89), (37, 89), (37, 91), (32, 91)], True)]        # gold toe cap

PARTS = []
# ge-lance behind the right arm (image right): leaf spear tip, ge blade, collar, red tassel
PARTS += [
    ("halberd", "s", [(67, 4), (69, 4), (69, 91), (67, 91)], True),
    ("halberd", "s", [(68, 1), (71, 6), (70, 14), (68, 16), (66, 14), (65, 6)], False),
    ("halberd", "s", [(69, 17), (80, 14), (85, 16), (81, 20), (69, 22)], False),
    ("halberd", "b", [(65, 16), (71, 16), (71, 19), (65, 19)], True),
    ("halberd", "v", [(63, 20), (67, 20), (66, 29), (63, 28)], False),
]
for ramp, poly, flat in LEG:
    PARTS += pair("legL", ramp, poly, flat, region_r="legR")
PARTS += [
    ("torso", "f", [(38, 30), (57, 30), (57, 62), (38, 62)], True),                       # inner frame
    ("torso", "v", [(40, 32), (55, 32), (56, 50), (54, 62), (41, 62), (39, 50)], False),  # red robe chest
]
PARTS += pair("skirt", "g", [(36, 53), (43, 53), (42, 72), (35, 70)])                    # black side skirts
PARTS += [
    ("skirt", "v", [(43, 53), (52, 53), (53, 74), (48, 77), (47, 77), (42, 74)], False),  # red front panel
    ("skirt", "b", [(39, 50), (56, 50), (56, 53), (39, 53)], False),                      # belt
    ("torso", "b", [(45, 36), (50, 36), (52, 38), (52, 42), (50, 44), (45, 44), (43, 42), (43, 38)], False),  # bronze rite mirror
]
# bearskin mantle: shoulders and a jagged hem, symmetric
PARTS += [("mantle", "g", [(34, 29), (61, 29), (69, 34), (72, 40), (73, 54), (69, 51), (66, 56), (62, 52), (58, 57), (55, 53),
                            (55, 45), (57, 33), (38, 33), (40, 45),
                            (40, 53), (37, 57), (33, 52), (29, 56), (26, 51), (22, 54), (23, 40), (26, 34)], False)]
# right arm (image right) down to the lance
PARTS += [
    ("armR", "f", [(63, 46), (72, 46), (72, 62), (63, 62)], True),
    ("armR", "g", [(64, 47), (71, 47), (71, 61), (64, 61)], False),
    ("armR", "b", [(64, 55), (71, 55), (71, 57), (64, 57)], True),
    ("armR", "s", [(63, 61), (73, 61), (73, 68), (68, 70), (63, 67)], False),   # fist on the shaft
]
# left arm (image left) bears the round shield
PARTS += [
    ("armL", "s", [(29, 38), (36, 38), (36, 44), (29, 44)], False),            # elbow above the shield rim
    ("shield", "b", [(23, 41), (32, 41), (38, 47), (38, 57), (32, 63), (23, 63), (17, 57), (17, 47)], False),
    ("shield", "v", [(24, 45), (31, 45), (34, 48), (34, 56), (31, 59), (24, 59), (21, 56), (21, 48)], False),
]
# head: bearskin hood with ears, red four-eyed mask plate
PARTS += [
    ("head", "g", [(36, 14), (40, 8), (44, 10), (51, 10), (55, 8), (59, 14), (60, 24), (56, 30), (39, 30), (35, 24)], False),
    ("head", "v", [(39, 15), (56, 15), (57, 22), (52, 28), (43, 28), (38, 22)], False),
]
PARTS += pair("head", "v", [(39, 10), (41, 9), (43, 12), (40, 13)], True)          # inner ears

DETAILS = [
    ("b3", 42, 18, 43, 19), ("b3", 52, 18, 53, 19),          # four gold eyes: upper pair
    ("b3", 43, 22, 44, 23), ("b3", 51, 22, 52, 23),          # lower pair
    ("out", 41, 16, 45, 16), ("out", 50, 16, 54, 16),        # taotie brows
    ("out", 45, 26, 50, 26), ("b3", 45, 27, 45, 27), ("b3", 50, 27, 50, 27),   # mouth and fangs
    ("glow", 47, 39, 48, 41),                                # soul gem in the rite mirror
    ("out", 47, 55, 48, 74),                                 # front panel seam
    ("b3", 27, 49, 28, 50), ("b3", 24, 53, 24, 53), ("b3", 31, 53, 31, 53), ("b3", 27, 55, 28, 55),   # shield boss and studs
    ("out", 44, 61, 51, 61),
]
STUDS = [("s3", 69, 7), ("s3", 76, 16), ("b3", 37, 31), ("b3", 58, 31), ("g3", 28, 37), ("g3", 67, 37),
         ("b3", 44, 51), ("b3", 51, 51), ("s3", 39, 75), ("s3", 56, 75), ("g3", 44, 31), ("g3", 51, 31),
         ("s3", 66, 63), ("b3", 33, 88), ("b3", 62, 88), ("g3", 38, 12), ("g3", 57, 12), ("v2", 40, 36), ("v2", 41, 46),
         ("g3", 25, 42), ("g3", 70, 42), ("g3", 29, 48), ("g3", 31, 34), ("g3", 64, 34), ("g3", 24, 50), ("g3", 71, 50),
         ("s3", 31, 40), ("s3", 37, 74), ("s3", 58, 74), ("v2", 41, 18), ("v2", 54, 18), ("b3", 47, 30), ("b3", 48, 30),
         ("g3", 38, 81), ("g3", 57, 81), ("v2", 44, 60), ("v2", 50, 65), ("g3", 37, 58), ("g3", 58, 58), ("s3", 67, 50),
         ("g3", 23, 44), ("g3", 72, 44), ("g3", 27, 52), ("g3", 68, 52), ("g3", 30, 54), ("g3", 65, 54),
         ("b3", 20, 52), ("b3", 35, 52), ("v2", 22, 47), ("s3", 41, 84), ("s3", 54, 84), ("v2", 46, 20), ("v2", 49, 20)]

VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(67, 47), fist=(68, 65), hipfix=False)


def drones():
    """two of the twelve drone-beasts, a separate overlay sprite (they orbit the unit; not part of the body check)"""
    beast = [("drone", "g", [(0, 2), (2, 0), (6, 0), (8, 2), (8, 5), (6, 7), (2, 7), (0, 5)], False),
             ("drone", "b", [(2, 7), (3, 9), (5, 9), (6, 7)], False)]
    parts, det = [], []
    for ox, oy in ((10, 18), (78, 30)):
        parts += [(r, rp, [(x + ox, y + oy) for x, y in pl], fl) for r, rp, pl, fl in beast]
        det += [("glow", ox + 3, oy + 3, ox + 3, oy + 3), ("glow", ox + 5, oy + 3, ox + 5, oy + 3)]
    return dict(parts=parts, details=det, studs=[], flip=False, shoulder=(0, 0), fist=(0, 0), hipfix=False)


def puppet_overlay(sprite, soul=CONFIG["SOUL"]):
    """status overlay for a raised follower: a soul-fire rim one pixel outside the silhouette and
    three threads rising to the frame top (broken every third pixel). Works on any unit's 96 sprite (alpha only)."""
    A = sprite[..., 3] > 0
    H, W = A.shape
    ring = np.zeros_like(A)
    ring[1:] |= A[:-1]; ring[:-1] |= A[1:]; ring[:, 1:] |= A[:, :-1]; ring[:, :-1] |= A[:, 1:]
    ring &= ~A
    ov = np.zeros((H, W, 4), np.uint8)
    rgb = F.hexrgb(soul)
    ov[ring, :3] = rgb; ov[ring, 3] = 255
    ys, xs = np.nonzero(A)
    cx = int(round(xs[ys <= ys.min() + 20].mean()))
    top = max(0, ys.min() - 1)
    # threads: from the shoulders and the head up to the frame top, broken every 3 px
    for x0 in (cx - 12, cx, cx + 12):
        col = A[:, x0]
        y_end = int(np.argmax(col)) if col.any() else top
        for y in range(0, y_end):
            if y % 3 != 2 and not A[y, x0]:
                ov[y, x0, :3] = rgb; ov[y, x0, 3] = 255
    return ov


def render(view):
    keep_pal, keep_ramp = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = CONFIG["PAL"]; F.CONFIG["RAMP"] = CONFIG["RAMP"]
    try:
        return V.crop96(V.build(view, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep_pal, keep_ramp


def over(base, top):
    out = base.copy(); a = top[..., 3] > 0
    out[a] = top[a]
    return out


def main():
    import os
    os.makedirs("out", exist_ok=True)
    img = render(VIEW)
    fails, rep = V.idle_checks("巫师 front", img)
    A = img[..., 3] > 0
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum())
    rep["mirror_iou"] = round(iou, 2)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save("out/ws_front_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/ws_front_3x.png")
    # drones preview (overlay on the body)
    dr = render(drones())
    prev = over(img, dr)
    bg = Image.new("RGBA", (96, 96), (58, 62, 72, 255)); bg.alpha_composite(Image.fromarray(prev, "RGBA"))
    bg.resize((288, 288), Image.NEAREST).save("out/ws_drones_3x.png")
    # puppet overlay on the approved 天兵 front
    tb = np.asarray(Image.open("approved/tianbing96/views_idle_front_1x.png").convert("RGBA"))
    pup = over(tb, puppet_overlay(tb))
    # lineup: 巫师, 天兵, 天兵 as a raised follower
    sheet = Image.new("RGBA", (96 * 3, 96), (58, 62, 72, 255))
    for i, im in enumerate((prev, tb, pup)):
        sheet.alpha_composite(Image.fromarray(im, "RGBA"), (i * 96, 0))
    sheet.resize((96 * 9, 288), Image.NEAREST).save("out/ws_lineup_3x.png")
    print(rep)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
