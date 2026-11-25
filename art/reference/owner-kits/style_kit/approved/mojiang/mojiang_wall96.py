"""墨将 wall prop (intact), 96x96 tile, in the approved style and the 墨将 palette. A prop, not a suit.
Timber palisade with a battlement top (alternating tall and short planks), two bronze bands, a vertical arrow slit and a compass
emblem on the middle plank, on a stone plinth. Sits on the tile ground row (feet gap 3).
Run: python3 mojiang_wall96.py -> out/mowall_{1x,3x}.png, out/mowall_scale_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import tianbing96_v5 as F
import tianbing96_views as V
import mojiang96 as M

PARTS = []
PLANKS = [(9, 24, 44), (24, 39, 52), (39, 56, 44), (56, 71, 52), (71, 86, 44)]    # x0, x1, top row: tall, short, tall, short, tall
for x0, x1, top in PLANKS:
    PARTS.append(("wall", "b", [(x0, top), (x1, top), (x1, 82), (x0, 82)], False))
PARTS += [
    ("band", "v", [(9, 59), (86, 59), (86, 62), (9, 62)], True),
    ("band", "v", [(9, 72), (86, 72), (86, 75), (9, 75)], True),
    ("slit", "f", [(45, 63), (50, 63), (50, 71), (45, 71)], True),                       # arrow slit
    ("emblem", "v", [(44, 47), (51, 47), (53, 50), (51, 53), (44, 53), (42, 50)], False),   # compass ring
    ("emblem", "v", [(46, 53), (47, 53), (44, 58), (43, 58)], True),
    ("emblem", "v", [(48, 53), (49, 53), (52, 58), (51, 58)], True),
    ("plinth", "s", [(5, 82), (90, 82), (93, 91), (2, 91)], False),                      # stone plinth
]
DETAILS = [
    ("glow", 47, 49, 48, 50), ("out", 47, 50, 47, 50),
    ("v2", 47, 65, 48, 65),
    ("out", 12, 85, 20, 85), ("out", 30, 85, 38, 85), ("out", 50, 85, 58, 85), ("out", 68, 85, 76, 85),   # plinth courses
    ("out", 24, 83, 24, 90), ("out", 47, 83, 47, 90), ("out", 71, 83, 71, 90),
    ("b1", 16, 64, 16, 71), ("b1", 32, 64, 32, 71), ("b1", 63, 64, 63, 71), ("b1", 79, 64, 79, 71),     # grain
]
STUDS = [("b3", 12, 47), ("b3", 27, 55), ("b3", 42, 47), ("b3", 59, 55), ("b3", 74, 47), ("b3", 20, 50), ("b3", 52, 47),
         ("b3", 82, 50), ("b3", 15, 66), ("b3", 33, 69), ("b3", 60, 67), ("b3", 76, 69), ("b3", 21, 78), ("b3", 36, 79),
         ("b3", 66, 78), ("b3", 83, 79), ("v2", 12, 60), ("v2", 30, 60), ("v2", 60, 60), ("v2", 82, 60), ("v2", 12, 73),
         ("v2", 30, 73), ("v2", 66, 73), ("v2", 82, 73), ("s3", 8, 84), ("s3", 28, 88), ("s3", 55, 84), ("s3", 72, 88),
         ("s3", 85, 85), ("s3", 15, 89), ("s3", 40, 87), ("s3", 63, 89), ("b1", 18, 56), ("b1", 46, 78), ("b1", 70, 56),
         ("b3", 11, 80), ("b3", 44, 80), ("b3", 80, 80), ("s3", 36, 83), ("s3", 78, 83)]
# wood grain flecks and stone speckle: seeded, so the sprite is reproducible (tune GRAIN to taste)
GRAIN = {"seed": 7, "wood": 190, "stone": 40}
_rs = np.random.RandomState(GRAIN["seed"])


def _free(x, y):
    return not (59 <= y <= 62 or 72 <= y <= 75 or (45 <= x <= 50 and 63 <= y <= 71) or (42 <= x <= 53 and 47 <= y <= 58))


_n = 0
while _n < GRAIN["wood"]:
    x, y = int(_rs.randint(10, 86)), int(_rs.randint(45, 82))
    top = [t for a, b, t in PLANKS if a <= x < b][0]
    if y >= top + 2 and _free(x, y) and x not in (24, 39, 56, 71):
        STUDS.append(("b3" if _rs.rand() < 0.6 else "b1", x, y)); _n += 1
_n = 0
while _n < GRAIN["stone"]:
    x, y = int(_rs.randint(6, 88)), int(_rs.randint(83, 90))
    STUDS.append(("s3" if _rs.rand() < 0.7 else "g3", x, y)); _n += 1
VIEW = dict(parts=PARTS, details=DETAILS, studs=STUDS, flip=False, shoulder=(0, 0), fist=(0, 0), hipfix=False)


def render():
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = M.CONFIG["PAL"]; F.CONFIG["RAMP"] = M.CONFIG["RAMP"]
    try:
        return V.crop96(V.build(VIEW, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def main():
    import os
    os.makedirs("out", exist_ok=True)
    img = render()
    A = img[..., 3] > 0
    ys, xs = np.nonzero(A)
    fails = []
    cols = len(set(map(tuple, img[A][:, :3].tolist())))
    iso = V.isolated_pct(img)
    lab, n = ndimage.label(A, structure=np.ones((3, 3)))
    gap = 95 - ys.max()
    if gap != 3: fails.append(f"ground gap {gap}")
    if not 9 <= cols <= 13: fails.append(f"colours {cols}")
    if not 4.0 <= iso <= 10.2: fails.append(f"isolated {iso:.1f}%")
    if n != 1: fails.append(f"{n} pieces")
    if xs.min() < 1 or xs.max() > 94: fails.append("touches tile edge")
    Image.fromarray(img, "RGBA").save("out/mowall_1x.png")
    Image.fromarray(img, "RGBA").resize((288, 288), Image.NEAREST).save("out/mowall_3x.png")
    mo = Image.open("approved/mojiang/mo_idle_front_1x.png").convert("RGBA")
    sheet = Image.new("RGBA", (96 * 2, 96), (58, 62, 72, 255))
    sheet.alpha_composite(mo, (0, 0)); sheet.alpha_composite(Image.fromarray(img, "RGBA"), (96, 0))
    sheet.resize((96 * 2 * 3, 288), Image.NEAREST).save("out/mowall_scale_3x.png")
    print({"height": int(ys.max() - ys.min() + 1), "width": int(xs.max() - xs.min() + 1), "colours": cols, "isolated": round(iso, 1)})
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
