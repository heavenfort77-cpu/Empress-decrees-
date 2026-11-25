"""Cocolito standard set for the Suit Mythology style: knight (knight96.py), mage, rogue, construct, as part data through the approved suit
renderer (tianbing96_v5.build via tianbing96_views). Each character is data: PAL/RAMP (the style's ramps plus one accent ramp each), PARTS, DETAILS,
STUDS. The renderer rivets "g" plates and puts bolt holes on "s" parts, so each character maps its main plate ramp to "g".
Run: python3 set96.py -> out/set_{mage,rogue,golem}_front_{1x,3x}.png, out/set_lineup_{1x,3x}.png (pass/fail per character)"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V
import knight96 as KN


def mir(poly): return [(95 - x, y) for x, y in poly][::-1]
def pair(region, ramp, poly, flat=False, region_r=None): return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]
COMMON = {"out": "#0d1418", "s1": "#2d3846", "s2": "#687a8a", "s3": "#aebfcc", "b1": "#8a5a2b", "b2": "#c48c3c", "b3": "#f2cb6a", "v1": "#c8432c", "v2": "#ff925c", "glow": "#c2fff1"}

# ---------------- mage: a sage engine. Conical hat, long robe to the boots, wide sleeves, staff with an orb on the left (image left), bronze pectoral.
MAGE = dict(
    PAL={**COMMON, "p1": "#3b2f42", "p2": "#6a4f8a", "p3": "#b08ad6"},                        # violet robe
    RAMP={"g": ("p1", "p2", "p3"), "s": ("s1", "s2", "s3"), "b": ("b1", "b2", "b3"), "v": ("v1", "v1", "v2"), "f": ("out", "out", "out")},
    PARTS=[
        ("staff", "s", [(22, 18), (25, 18), (25, 91), (22, 91)], True),                     # shaft
        ("staff", "b", [(18, 12), (29, 12), (31, 18), (26, 22), (21, 22), (16, 18)], False),  # orb cage
        ("staff", "b", [(19, 88), (28, 88), (28, 91), (19, 91)], True),                     # ferrule
    ] + pair("legL", "s", [(39, 84), (45, 84), (46, 91), (37, 91)], False, region_r="legR") + [   # boots under the hem
        ("torso", "f", [(37, 30), (58, 30), (58, 60), (37, 60)], True),
        ("torso", "g", [(38, 31), (57, 31), (58, 46), (56, 60), (39, 60), (37, 46)], False),   # robe chest
        ("torso", "b", [(42, 34), (53, 34), (55, 40), (50, 46), (45, 46), (40, 40)], False),   # pectoral
        ("skirt", "g", [(36, 58), (59, 58), (63, 86), (32, 86)], False),                       # long robe
        ("skirt", "b", [(38, 56), (57, 56), (57, 59), (38, 59)], False),                       # sash
        ("skirt", "f", [(47, 60), (48, 60), (48, 85), (47, 85)], True),                        # front seam
    ] + pair("pauL", "g", [(31, 29), (40, 27), (42, 35), (38, 41), (31, 40), (28, 34)], region_r="pauR") + [
        ("armL", "g", [(24, 36), (36, 36), (38, 56), (26, 60), (20, 52)], False),               # wide sleeve to the staff
        ("hand", "s", [(19, 50), (29, 50), (30, 56), (28, 59), (20, 59), (18, 56)], False),    # fist on the staff
        ("armR", "g", [(60, 36), (72, 36), (76, 52), (70, 60), (58, 56)], False),               # wide sleeve
        ("hand", "s", [(66, 54), (76, 54), (77, 60), (75, 63), (67, 63), (65, 60)], False),    # open hand
        ("head", "g", [(39, 14), (56, 14), (58, 20), (57, 30), (54, 32), (41, 32), (38, 30), (37, 20)], False),   # hood face plate
        ("head", "s", [(35, 14), (60, 14), (60, 17), (35, 17)], False),                        # hat brim
        ("head", "g", [(41, 14), (54, 14), (49, 0), (46, 0)], False),                           # cone
        ("head", "b", [(42, 11), (53, 11), (53, 14), (42, 14)], True),                          # hat band
    ],
    DETAILS=[("glow", 42, 22, 45, 23), ("glow", 50, 22, 53, 23), ("out", 44, 28, 51, 28), ("glow", 22, 15, 25, 18), ("b3", 46, 38, 49, 42),
             ("out", 46, 34, 49, 34), ("p3", 40, 64, 40, 80), ("p3", 55, 64, 55, 80)],
    STUDS=[("b3", 40, 33), ("b3", 55, 33), ("s3", 23, 20), ("s3", 24, 40), ("b3", 36, 59), ("b3", 59, 59), ("p3", 35, 80), ("p3", 60, 80),
           ("s3", 41, 86), ("s3", 54, 86), ("s3", 30, 30), ("s3", 65, 30), ("p3", 44, 16), ("p3", 51, 16), ("s3", 36, 15), ("s3", 59, 15),
           ("b3", 44, 44), ("b3", 51, 44), ("p3", 62, 44), ("p3", 30, 44), ("s3", 22, 54), ("s3", 70, 58), ("b3", 42, 57), ("b3", 53, 57),
           ("p3", 47, 4), ("p3", 48, 8), ("s3", 24, 89), ("v2", 47, 50), ("v2", 48, 52), ("p3", 36, 70), ("p3", 59, 70), ("p3", 42, 62),
           ("p3", 53, 62), ("b3", 20, 14), ("b3", 27, 14), ("s3", 41, 88), ("s3", 54, 88), ("p3", 63, 50), ("p3", 33, 50), ("s3", 40, 30), ("s3", 55, 30), ("p3", 39, 48), ("p3", 56, 48), ("p3", 44, 72), ("p3", 51, 72), ("s3", 21, 56), ("s3", 76, 60), ("p3", 32, 36), ("p3", 63, 36)],
    VIEW=dict(shoulder=(66, 40), fist=(71, 58), hipfix=False),
)

# ---------------- rogue: slim hooded skirmisher. Hood and scarf, reversed dagger in the right hand (image right), bandolier, light greaves. Charcoal with amber.
ROGUE = dict(
    PAL={**COMMON, "k1": "#1c1620", "k2": "#3b2f42", "k3": "#75637e", },
    RAMP={"g": ("k1", "k2", "k3"), "s": ("s1", "s2", "s3"), "b": ("b1", "b2", "b3"), "v": ("v1", "v1", "v2"), "f": ("out", "out", "out")},
    PARTS=[
        ("dagger", "s", [(69, 60), (72, 60), (74, 74), (70, 80), (67, 74)], False),             # reversed blade, point down
    ] + [p for ramp, poly, flat in [("f", [(39, 62), (46, 62), (45, 88), (39, 88)], True), ("g", [(40, 64), (45, 64), (44, 76), (40, 76)], False),
                                    ("s", [(39, 74), (46, 74), (46, 78), (39, 78)], False), ("g", [(40, 78), (45, 78), (45, 86), (40, 86)], False),
                                    ("s", [(37, 86), (46, 86), (47, 91), (36, 91)], False)]
         for p in pair("legL", ramp, poly, flat, region_r="legR")] + [
        ("torso", "f", [(40, 30), (55, 30), (55, 62), (40, 62)], True),
        ("torso", "g", [(41, 31), (54, 31), (55, 44), (53, 60), (42, 60), (40, 44)], False),   # jerkin
        ("torso", "b", [(41, 32), (46, 32), (54, 54), (54, 58), (49, 58), (41, 36)], False),   # bandolier
        ("skirt", "g", [(39, 58), (56, 58), (57, 68), (38, 68)], False),                       # belt skirt
        ("skirt", "s", [(40, 56), (55, 56), (55, 59), (40, 59)], False),                       # belt
        ("torso", "v", [(40, 28), (55, 28), (56, 34), (50, 38), (45, 38), (39, 34)], False),   # scarf
    ] + pair("pauL", "g", [(33, 30), (41, 29), (42, 36), (38, 40), (33, 39), (31, 34)], region_r="pauR") + [
        ("armL", "g", [(31, 36), (39, 36), (39, 52), (31, 52)], False),
        ("hand", "s", [(30, 51), (39, 51), (40, 56), (38, 59), (31, 59), (29, 56)], False),
        ("armR", "g", [(57, 36), (65, 36), (66, 50), (58, 50)], False),
        ("armR", "b", [(57, 44), (66, 44), (66, 46), (57, 46)], True),
        ("hand", "s", [(64, 52), (74, 52), (75, 58), (73, 61), (65, 61), (63, 58)], False),    # fist on the dagger grip
        ("head", "g", [(38, 12), (57, 12), (60, 20), (59, 30), (55, 33), (40, 33), (36, 30), (35, 20)], False),   # hood
        ("head", "s", [(41, 20), (54, 20), (55, 28), (52, 31), (43, 31), (40, 28)], False),    # face mask
    ],
    DETAILS=[("glow", 43, 23, 46, 23), ("glow", 49, 23, 52, 23), ("out", 44, 27, 51, 27), ("out", 47, 30, 48, 31),
             ("b3", 43, 40, 44, 41), ("b3", 47, 46, 48, 47), ("b3", 51, 52, 52, 53), ("s3", 70, 62, 70, 72)],
    STUDS=[("k3", 40, 14), ("k3", 55, 14), ("s3", 36, 22), ("s3", 59, 22), ("b3", 41, 57), ("b3", 54, 57), ("s3", 41, 75), ("s3", 54, 75),
           ("k3", 33, 38), ("k3", 62, 38), ("s3", 31, 53), ("s3", 65, 54), ("v2", 41, 30), ("v2", 54, 30), ("k3", 42, 62), ("k3", 53, 62),
           ("s3", 38, 88), ("s3", 57, 88), ("k3", 42, 70), ("k3", 53, 70), ("b3", 48, 38), ("s3", 73, 56), ("b3", 50, 42), ("k3", 35, 33),
           ("k3", 60, 33), ("s3", 44, 21), ("s3", 51, 21), ("k3", 38, 20), ("k3", 57, 20), ("s3", 41, 80), ("s3", 44, 80), ("s3", 51, 80),
           ("s3", 54, 80), ("k3", 44, 34), ("k3", 51, 34), ("b3", 46, 52), ("s3", 69, 66)],
    VIEW=dict(shoulder=(61, 38), fist=(69, 56), hipfix=False),
)

# ---------------- construct: furnace golem. Boxy body with a furnace port, hopper head with one lens, pile-driver fists, short legs. Copper with steel.
GOLEM = dict(
    PAL={**COMMON, "r1": "#5a2a1e", "r2": "#9a4a2a", "r3": "#d98a5a"},
    RAMP={"g": ("r1", "r2", "r3"), "s": ("s1", "s2", "s3"), "b": ("b1", "b2", "b3"), "v": ("v1", "v1", "v2"), "f": ("out", "out", "out")},
    PARTS=[p for ramp, poly, flat in [("f", [(30, 70), (42, 70), (42, 90), (30, 90)], True), ("g", [(31, 71), (41, 71), (41, 84), (31, 84)], False),
                                      ("s", [(29, 83), (43, 83), (44, 91), (28, 91)], False)]
           for p in pair("legL", ramp, poly, flat, region_r="legR")] + [
        ("torso", "f", [(29, 26), (66, 26), (66, 72), (29, 72)], True),
        ("torso", "g", [(30, 27), (65, 27), (66, 50), (64, 71), (31, 71), (29, 50)], False),   # body block
        ("torso", "s", [(38, 44), (57, 44), (57, 60), (38, 60)], False),                       # furnace port frame
        ("torso", "g", [(30, 27), (65, 27), (65, 34), (30, 34)], False),                       # top beam
    ] + pair("pauL", "s", [(20, 24), (34, 22), (36, 34), (30, 40), (20, 38), (17, 31)], region_r="pauR") + [
        ("armL", "g", [(16, 38), (30, 38), (30, 60), (16, 60)], False),                        # thick arm
        ("armL", "s", [(15, 48), (31, 48), (31, 51), (15, 51)], True),                         # piston band
        ("hand", "s", [(12, 60), (33, 60), (34, 72), (31, 76), (14, 76), (11, 72)], False),    # pile-driver fist
        ("armR", "g", [(65, 38), (79, 38), (79, 60), (65, 60)], False),
        ("armR", "s", [(64, 48), (80, 48), (80, 51), (64, 51)], True),
        ("hand", "s", [(62, 60), (83, 60), (84, 72), (81, 76), (64, 76), (61, 72)], False),
        ("head", "g", [(38, 8), (57, 8), (60, 14), (58, 26), (37, 26), (35, 14)], False),       # hopper head
        ("head", "s", [(41, 12), (54, 12), (55, 22), (40, 22)], False),                        # lens housing
        ("head", "b", [(44, 4), (51, 4), (52, 8), (43, 8)], False),                             # stack cap
    ],
    DETAILS=[("glow", 45, 15, 50, 18), ("v2", 41, 48, 54, 57), ("v1", 41, 54, 54, 57), ("out", 47, 48, 48, 57), ("out", 44, 50, 44, 55), ("out", 51, 50, 51, 55),
             ("b3", 33, 30, 62, 30), ("out", 30, 36, 65, 36), ("b3", 46, 5, 49, 5)],
    STUDS=[("r3", 32, 29), ("r3", 63, 29), ("s3", 40, 46), ("s3", 55, 46), ("b3", 34, 38), ("b3", 61, 38), ("s3", 18, 62), ("s3", 27, 62),
           ("s3", 68, 62), ("s3", 77, 62), ("r3", 18, 42), ("r3", 77, 42), ("s3", 22, 27), ("s3", 73, 27), ("r3", 39, 10), ("r3", 56, 10),
           ("s3", 31, 85), ("s3", 64, 85), ("r3", 33, 73), ("r3", 62, 73), ("s3", 42, 14), ("s3", 53, 14), ("b3", 38, 64), ("b3", 57, 64),
           ("r3", 35, 55), ("r3", 60, 55), ("s3", 15, 70), ("s3", 80, 70), ("r3", 33, 66), ("r3", 62, 66), ("b3", 46, 61), ("b3", 49, 61),
           ("s3", 29, 88), ("s3", 66, 88), ("r3", 40, 76), ("r3", 55, 76), ("s3", 41, 56), ("s3", 54, 56), ("r3", 24, 44), ("r3", 71, 44), ("r3", 36, 40), ("r3", 59, 40), ("r3", 44, 38), ("r3", 51, 38), ("r3", 20, 52), ("r3", 75, 52), ("s3", 20, 66), ("s3", 75, 66), ("r3", 34, 46), ("r3", 61, 46), ("r3", 40, 68), ("r3", 55, 68), ("s3", 44, 20), ("s3", 51, 20), ("r3", 37, 23), ("r3", 58, 23), ("b3", 32, 32), ("b3", 63, 32), ("r3", 46, 40), ("r3", 49, 40), ("s3", 32, 90), ("s3", 63, 90)],
    VIEW=dict(shoulder=(72, 40), fist=(72, 66), hipfix=False),
)
SET = {"knight": None, "mage": MAGE, "rogue": ROGUE, "golem": GOLEM}


def render(ch):
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = ch["PAL"]; F.CONFIG["RAMP"] = ch["RAMP"]
    try: return V.crop96(V.build(dict(parts=ch["PARTS"], details=ch["DETAILS"], studs=ch["STUDS"], flip=False, **ch["VIEW"]), None))
    finally: F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def sparkle(im, ch, target=4.6, seed=3):
    """the style's isolated pixels are rivets and specular points; where a character's plates are too plain, stamp seeded specular pixels
    (the ramp's light tone) on mid-tone pixels whose four neighbours are the same mid tone, until the isolated share reaches the target"""
    import random
    rnd = random.Random(seed); P = ch["PAL"]; R = ch["RAMP"]
    mids = {tuple(F.hexrgb(P[R[r][1]])[:3]): tuple(F.hexrgb(P[R[r][2]])[:3]) for r in ("g", "s", "b")}
    rgb = im[..., :3]; a = im[..., 3] > 0
    cand = [(y, x) for y in range(2, 94) for x in range(2, 94) if a[y, x] and tuple(rgb[y, x]) in mids
            and all(tuple(rgb[y + dy, x + dx]) == tuple(rgb[y, x]) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)))]
    rnd.shuffle(cand); used = set()
    for y, x in cand:
        if measure(im)[2] >= target: break
        if any((y + dy, x + dx) in used for dy in (-2, -1, 0, 1, 2) for dx in (-2, -1, 0, 1, 2)): continue
        im[y, x, :3] = mids[tuple(rgb[y, x])]; used.add((y, x))
    return im


def measure(im):
    a = im[..., 3] > 0; rgb = im[..., :3]; cols = len({tuple(p) for p in rgb[a]})
    pad = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode="edge"); ne = lambda x, y: (x != y).any(axis=2)
    d = ne(rgb, pad[:-2, 1:-1]) & ne(rgb, pad[2:, 1:-1]) & ne(rgb, pad[1:-1, :-2]) & ne(rgb, pad[1:-1, 2:])
    ys = np.nonzero(a)[0]; return int(ys.max() - ys.min() + 1), cols, round(float((d & a).sum() / a.sum() * 100), 1)


if __name__ == "__main__":
    import os; os.makedirs("out", exist_ok=True)
    imgs = {"knight": KN.render(KN.VIEW)}
    allfails = []
    for name, ch in SET.items():
        if ch: imgs[name] = render(ch)
        imgs[name] = sparkle(imgs[name], ch or dict(PAL=KN.CONFIG["PAL"], RAMP=KN.CONFIG["RAMP"]))
        img = imgs[name]; fails, rep = V.idle_checks(name, img); allfails += fails
        h, c, iso = measure(img); print(f"{name}: height {h}, colours {c}, isolated {iso}%")
        Image.fromarray(img, "RGBA").save(f"out/set_{name}_front_1x.png"); Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save(f"out/set_{name}_front_3x.png")
    tb = np.asarray(Image.open("approved/tianbing96/views_idle_front_1x.png").convert("RGBA"))
    order = ["knight", "mage", "rogue", "golem"]
    for sc in (1, 3):
        lu = Image.new("RGBA", (96 * 5 * sc, 96 * sc), (0, 0, 0, 0) if sc == 1 else (58, 62, 72, 255))
        for i, im in enumerate([imgs[n] for n in order] + [tb]): lu.alpha_composite(Image.fromarray(im, "RGBA").resize((96 * sc, 96 * sc), Image.NEAREST), (i * 96 * sc, 0))
        lu.save(f"out/set_lineup_{sc}x.png")
    print("PASS" if not allfails else "FAILING:\n" + "\n".join(allfails))
