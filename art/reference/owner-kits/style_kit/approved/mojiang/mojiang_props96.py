"""墨将 props at 96x96, one tile each, in the approved style and the 墨将 palette (no new colours): the timber wall and the crossbow turret,
each in three states: intact, half-built (scaffold, loose planks, driven posts) and damaged (snapped planks, hanging band, scorch, debris).
Props, not suits. Wall intact = the sample drawn in mojiang_wall96.py (same data). Grain and speckle are seeded flecks (GRAIN block).
Run: python3 mojiang_props96.py -> out/mo_props_{1x,3x}.png (one sheet: wall x3 states over turret x3 states) and out/moprop_<name>_1x.png
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import tianbing96_v5 as F
import tianbing96_views as V
import mojiang96 as M
import mojiang_wall96 as W0

GRAIN = {"seed": 7, "wood": 190, "stone": 40}
N = 96


def mir(poly):
    return [(95 - x, y) for x, y in poly][::-1]


def pair(region, ramp, poly, flat=False):
    return [(region, ramp, poly, flat), (region, ramp, mir(poly), flat)]


def wall(state):
    P = []
    planks = {"intact": W0.PLANKS, "half": [(9, 24, 44), (24, 39, 52), (39, 56, 66)],
              "damaged": [(9, 24, 44), (24, 39, 52), (71, 86, 44)]}[state]
    for x0, x1, top in planks:
        P.append(("wall", "b", [(x0, top), (x1, top), (x1, 82), (x0, 82)], False))
    D, bands = [], []
    if state == "intact":
        bands = [(9, 86, 59), (9, 86, 72)]
        P += [("slit", "f", [(45, 63), (50, 63), (50, 71), (45, 71)], True),
              ("emblem", "v", [(44, 47), (51, 47), (53, 50), (51, 53), (44, 53), (42, 50)], False),
              ("emblem", "v", [(46, 53), (47, 53), (44, 58), (43, 58)], True), ("emblem", "v", [(48, 53), (49, 53), (52, 58), (51, 58)], True)]
        D += [("glow", 47, 49, 48, 50), ("out", 47, 50, 47, 50), ("v2", 47, 65, 48, 65)]
    if state == "half":
        bands = [(9, 39, 59), (9, 56, 72)]
        for x0, x1, top in ((58, 62, 60), (66, 70, 56), (78, 82, 64)):      # driven posts
            P.append(("post", "b", [(x0, top), (x1, top), (x1, 82), (x0, 82)], False))
        P += [("scaf", "b", [(60, 38), (63, 38), (72, 82), (68, 82)], False), ("scaf", "b", [(82, 38), (85, 38), (80, 82), (76, 82)], False),
              ("scaf", "b", [(62, 46), (84, 46), (84, 49), (62, 49)], False), ("scaf", "b", [(70, 58), (82, 58), (82, 60), (70, 60)], False),
              ("loose", "b", [(70, 74), (88, 74), (88, 78), (70, 78)], False), ("loose", "b", [(72, 70), (86, 70), (86, 74), (72, 74)], False),
              ("loose", "b", [(45, 62), (56, 62), (56, 64), (45, 64)], False)]
        D += [("out", 66, 56, 66, 82), ("v1", 62, 62, 63, 62)]
    if state == "damaged":
        bands = [(9, 56, 72), (9, 39, 59)]
        P += [("wall", "b", [(39, 60), (43, 55), (47, 61), (51, 56), (56, 62), (56, 82), (39, 82)], False),     # snapped middle plank
              ("slit", "f", [(45, 66), (50, 66), (50, 74), (45, 74)], True),
              ("wall", "b", [(58, 70), (64, 65), (70, 82), (58, 82)], False),                                     # a splinter left of the missing plank
              ("band", "v", [(56, 59), (61, 59), (62, 69), (58, 69)], True),                                      # band hanging off
              ("debris", "b", [(62, 79), (68, 77), (70, 82), (62, 82)], False), ("debris", "b", [(30, 79), (36, 78), (37, 82), (29, 82)], False),
              ("debris", "b", [(46, 80), (52, 79), (53, 82), (45, 82)], False)]
        D += [("out", 14, 48, 15, 52), ("out", 16, 53, 15, 58), ("out", 16, 59, 15, 62), ("out", 30, 56, 31, 60), ("out", 31, 61, 30, 66),
              ("g1", 10, 45, 22, 48), ("g1", 72, 45, 85, 49), ("g1", 41, 63, 45, 70), ("g1", 51, 66, 55, 72), ("g1", 74, 52, 83, 56),
              ("v2", 13, 40, 13, 40)]
        bands.append((71, 86, 72))
    for x0, x1, y in bands:
        P.append(("band", "v", [(x0, y), (x1, y), (x1, y + 3), (x0, y + 3)], True))
    P.append(("plinth", "s", [(5, 82), (90, 82), (93, 91), (2, 91)], False))
    D += [("out", 12, 85, 20, 85), ("out", 30, 85, 38, 85), ("out", 50, 85, 58, 85), ("out", 68, 85, 76, 85),
          ("out", 24, 83, 24, 90), ("out", 47, 83, 47, 90), ("out", 71, 83, 71, 90)]
    return P, D, [(a, b, t) for a, b, t in planks]


def turret(state):
    P, D = [], []
    P.append(("plinth", "s", [(22, 84), (73, 84), (76, 91), (19, 91)], False))
    P.append(("post", "b", [(42, 56), (53, 56), (54, 84), (41, 84)], False))
    P.append(("band", "v", [(41, 70), (54, 70), (54, 72), (41, 72)], True))
    P.append(("ring", "v", [(36, 56), (59, 56), (59, 60), (36, 60)], False))
    P.append(("post", "b", [(44, 48), (51, 48), (51, 57), (44, 57)], False))               # cradle joining the post to the bow
    D += [("out", 24, 87, 40, 87), ("out", 55, 87, 70, 87), ("out", 47, 85, 47, 90)]
    if state in ("intact", "damaged"):
        P += [("crank", "s", [(60, 62), (70, 62), (70, 64), (60, 64)], False), ("crank", "b", [(69, 58), (72, 58), (72, 68), (69, 68)], False)]
    limb = [(47, 50), (36, 52), (24, 48), (14, 40), (10, 32), (14, 34), (22, 40), (34, 45), (47, 45)]
    if state == "intact":
        P += pair("bow", "b", limb)
        P += [("string", "s", [(10, 32), (11, 32), (48, 44), (47, 44)], True), ("string", "s", [(85, 32), (84, 32), (47, 44), (48, 44)], True)]
        P += [("mag", "b", [(41, 22), (54, 22), (54, 37), (41, 37)], False), ("mag", "s", [(42, 19), (53, 19), (54, 22), (41, 22)], False),
              ("mag", "v", [(41, 26), (54, 26), (54, 27), (41, 27)], True), ("mag", "v", [(41, 32), (54, 32), (54, 33), (41, 33)], True),
              ("bolt", "s", [(47, 37), (48, 37), (52, 42), (52, 44), (48, 48), (47, 48), (43, 44), (43, 42)], False),
              ("bolt", "b", [(44, 46), (51, 46), (51, 49), (44, 49)], True)]
        D += [("glow", 47, 22, 48, 23), ("v2", 44, 27, 51, 27)]
    if state == "half":
        P += [("bow", "b", limb, False)]                                                       # only the left limb is mounted
        P += [("scaf", "b", [(58, 20), (61, 20), (70, 84), (66, 84)], False), ("scaf", "b", [(82, 20), (85, 20), (78, 84), (74, 84)], False),
              ("scaf", "b", [(60, 40), (84, 40), (84, 43), (60, 43)], False),
              ("loose", "b", [(56, 76), (90, 76), (88, 81), (58, 82)], False),                 # the other limb lying on the plinth
              ("loose", "s", [(60, 72), (80, 72), (80, 75), (60, 75)], False)]
        D += [("v1", 63, 41, 64, 41)]
    if state == "damaged":
        P += [("bow", "b", limb, False),
              ("bow", "b", [(48, 50), (59, 52), (68, 49), (72, 44), (70, 42), (66, 44), (58, 46), (48, 45)], False)]    # right limb snapped short
        P += [("string", "s", [(10, 32), (11, 32), (48, 44), (47, 44)], True), ("string", "s", [(70, 42), (71, 43), (66, 62), (65, 62)], True),
              ("mag", "b", [(43, 26), (56, 24), (57, 38), (44, 40)], False), ("mag", "s", [(44, 22), (55, 20), (56, 24), (43, 26)], False),
              ("mag", "v", [(43, 31), (56, 30), (56, 31), (43, 32)], True),
              ("bolt", "s", [(47, 39), (48, 39), (52, 43), (52, 44), (48, 48), (47, 48), (43, 44), (43, 43)], False),   # the loaded bolt, still seated
              ("bolt", "s", [(56, 82), (72, 84), (72, 85), (56, 83)], True), ("bolt", "s", [(26, 84), (40, 83), (40, 84), (26, 85)], True),
              ("bolt", "s", [(30, 82), (44, 83), (44, 84), (30, 83)], True)]                       # spilled bolts
        D += [("g1", 42, 60, 52, 66), ("g1", 43, 74, 52, 80), ("g1", 24, 44, 28, 46), ("out", 47, 26, 49, 36), ("v2", 12, 33, 12, 33)]
    P = P + []
    return P, D, None


def studs_for(P, state_seed, kind, wood=None):
    rs = np.random.RandomState(GRAIN["seed"] + state_seed)
    body = np.zeros((N, N), bool); skip = np.zeros((N, N), bool); stone = np.zeros((N, N), bool)
    for r, rp, pl, fl in P:
        m = F.mask(pl, N, N)
        if r in ("wall", "post", "scaf", "loose", "debris", "mag", "bow") and rp == "b": body |= m
        if r == "plinth": stone |= m
        if fl or rp == "v" or rp == "f": skip |= m
    body &= ~skip
    S = []
    ys, xs = np.nonzero(body)
    for i in rs.permutation(len(xs))[:(wood or GRAIN["wood"])]:
        S.append(("b3" if rs.rand() < 0.6 else "b1", int(xs[i]), int(ys[i])))
    ys, xs = np.nonzero(stone)
    for i in rs.permutation(len(xs))[:GRAIN["stone"]]:
        S.append(("s3" if rs.rand() < 0.7 else "g3", int(xs[i]), int(ys[i])))
    return S


def render(P, D, S):
    view = dict(parts=P, details=D, studs=S, flip=False, shoulder=(0, 0), fist=(0, 0), hipfix=False)
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = M.CONFIG["PAL"]; F.CONFIG["RAMP"] = M.CONFIG["RAMP"]
    try:
        return V.crop96(V.build(view, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def main():
    import os
    os.makedirs("out", exist_ok=True)
    fails, rows, imgs = [], {}, {}
    for kind, fn in (("wall", wall), ("turret", turret)):
        for i, state in enumerate(("intact", "half", "damaged")):
            P, D, _ = fn(state)
            S = studs_for(P, i + (10 if kind == "turret" else 0), kind, wood=(270 if (kind, state) == ("wall", "half") else None))
            img = render(P, D, S)
            name = f"{kind}_{state}"
            A = img[..., 3] > 0; ys, xs = np.nonzero(A)
            cols = len(set(map(tuple, img[A][:, :3].tolist()))); iso = V.isolated_pct(img)
            lab, n = ndimage.label(A, structure=np.ones((3, 3)))
            if 95 - ys.max() != 3: fails.append(f"{name}: ground gap {95 - ys.max()}")
            if not 9 <= cols <= 13: fails.append(f"{name}: colours {cols}")
            if not 4.0 <= iso <= 10.2: fails.append(f"{name}: isolated {iso:.1f}%")
            if n != 1: fails.append(f"{name}: {n} pieces")
            if xs.min() < 1 or xs.max() > 94 or ys.min() < 1: fails.append(f"{name}: touches tile edge")
            rows[name] = dict(h=int(ys.max() - ys.min() + 1), w=int(xs.max() - xs.min() + 1), colours=cols, isolated=round(iso, 1))
            imgs[name] = img
            Image.fromarray(img, "RGBA").save(f"out/moprop_{name}_1x.png")
    sheet = Image.new("RGBA", (96 * 3, 96 * 2), (58, 62, 72, 255))
    for r, kind in enumerate(("wall", "turret")):
        for c, state in enumerate(("intact", "half", "damaged")):
            sheet.alpha_composite(Image.fromarray(imgs[f"{kind}_{state}"], "RGBA"), (c * 96, r * 96))
    sheet.save("out/mo_props_1x.png"); sheet.resize((96 * 3 * 3, 96 * 2 * 3), Image.NEAREST).save("out/mo_props_3x.png")
    for k, v in rows.items(): print(k, v)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
