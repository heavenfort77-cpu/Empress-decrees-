"""猿魔 (Ape Demon, late-game juggernaut) stage 1 front sample, 96x96, approved renderer, light, outline and rivets.
Ideal: breaking every restraint. Structure: hunched domed back hump, head sunk between two huge round shoulders, a gold fillet band across the
sensor head (the restraint it strains against, with a small crest), arms long enough that the fists hang near knee height, short thick legs.
Declared asymmetry: the right fist holds a telescoped staff (iron shaft, gold caps and bands) planted beside it; the left wrist carries a gold
cuff and the left shoulder a bigger stud cluster. Stage 1 of 3: stands about 66 px tall and 46 px wide, later stages get heavier not taller.
Palette: burnt vermilion lacquer, gold, dark iron, bright gold eyes. Invented, no source colours.
Run: python3 yuanmo96.py -> out/ym1_front_{1x,3x,5x}.png, out/ym_lineup_3x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V
import gushi96 as G

CONFIG = {
    "PAL": {
        "out": "#1a0d0a",
        "g1": "#4a1a12", "g2": "#8c3a1e", "g3": "#d1773a",   # burnt vermilion lacquer
        "b1": "#7a5412", "b2": "#d29a2a", "b3": "#ffe28a",   # gold: fillet, caps, cuffs
        "s2": "#6a625a", "s3": "#b7ada0",                    # dark iron: staff shaft, joints
        "v0": "#9a6a10", "v1": "#ffcf40", "v2": "#fff3b0",   # gold eyes
        "glow": "#fff8d0",
    },
    "RAMP": {"g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("g1", "s2", "s3"),
             "v": ("v0", "v1", "v2"), "f": ("out", "out", "out")},
    "HEIGHT": (58, 68),
}
seg, circ_at = G.seg, G.circ_at


def mir(poly): return [(95 - x, y) for x, y in poly][::-1]
def sym(half): return half + mir(half)
def pair(region, ramp, poly, flat=False, region_r=None): return [(region, ramp, poly, flat), (region_r or region, ramp, mir(poly), flat)]


PARTS = []
# legs: short, thick, planted wide
PARTS += pair("legL", "g", [(36, 70), (47, 70), (47, 87), (33, 87)], False, "legR")
PARTS += pair("legL", "g", [(29, 86), (47, 86), (47, 91), (28, 91)], False, "legR")
PARTS += pair("legL", "b", [(37, 76), (46, 76), (46, 79), (37, 79)], True, "legR")
# hips
PARTS += [("skirt", "g", sym([(47, 66), (37, 66), (33, 70), (34, 76), (40, 79), (47, 79)]), False),
          ("skirt", "b", [(36, 71), (59, 71), (59, 72), (36, 72)], True)]
# domed hump torso, wide at the shoulders
PARTS += [("torso", "f", sym([(47, 34), (40, 35), (35, 40), (32, 50), (32, 62), (35, 70), (40, 74), (47, 75)]), True),
          ("torso", "g", sym([(47, 35), (40, 36), (36, 41), (33, 50), (33, 62), (36, 69), (40, 73), (47, 74)]), False),
          ("torso", "b", sym([(47, 52), (42, 54), (40, 60), (42, 66), (47, 68)]), False),
          ("torso", "v", sym([(47, 56), (45, 57), (44, 60), (45, 63), (47, 64)]), False)]
# shoulders: two huge round pauldrons
PARTS += [("pauL", "g", circ_at(29, 41, 9, 20), False), ("pauL", "b", circ_at(29, 41, 4, 14), False),
          ("pauR", "g", circ_at(66, 41, 9, 20), False), ("pauR", "b", circ_at(66, 41, 4, 14), False)]
# staff first (the fist wraps it), then arms
PARTS += [("staff", "s", seg((77, 42), (77, 90), 3), False),
          ("staff", "b", [(75, 38), (79, 38), (80, 43), (74, 43)], False),
          ("staff", "b", [(75, 56), (79, 56), (79, 58), (75, 58)], True),
          ("staff", "b", [(75, 70), (79, 70), (79, 72), (75, 72)], True),
          ("staff", "b", [(75, 88), (79, 88), (80, 91), (74, 91)], False)]
PARTS += [("armL", "g", seg((29, 48), (25, 68), 9), False), ("armL", "g", seg((25, 68), (23, 82), 8), False),
          ("armL", "b", [(19, 75), (28, 75), (28, 79), (19, 79)], False),                    # gold cuff
          ("hand", "g", circ_at(23, 85, 6, 18), False), ("hand", "b", [(18, 83), (28, 83), (28, 84), (18, 84)], True),
          ("armR", "g", seg((66, 48), (70, 68), 9), False), ("armR", "g", seg((70, 68), (72, 82), 8), False),
          ("hand", "g", circ_at(72, 84, 6, 18), False), ("hand", "b", [(67, 82), (77, 82), (77, 83), (67, 83)], True)]
# head: dome sunk between the shoulders, visor, gold fillet band with ear clasps and a small crest
PARTS += [("head", "g", [(42, 47), (41, 41), (44, 36), (51, 36), (54, 41), (53, 47)], False),
          ("head", "f", [(43, 40), (52, 40), (52, 45), (43, 45)], True),
          ("head", "v", [(44, 41), (47, 41), (47, 44), (44, 44)], False), ("head", "v", [(48, 41), (51, 41), (51, 44), (48, 44)], False),
          ("head", "b", [(40, 37), (55, 37), (56, 39), (39, 39)], False),
          ("head", "b", [(37, 35), (40, 35), (40, 41), (37, 41)], False), ("head", "b", [(55, 35), (58, 35), (58, 41), (55, 41)], False),
          ("head", "b", [(46, 31), (49, 31), (50, 37), (45, 37)], False)]
DETAILS = [("out", 47, 55, 48, 66), ("glow", 44, 42, 45, 42), ("glow", 49, 42, 50, 42)]
STUDS = [("b3", 27, 47), ("b3", 68, 47), ("g3", 22, 40), ("g3", 30, 41), ("g3", 65, 41), ("g3", 73, 42), ("g3", 24, 53), ("g3", 71, 53),
         ("g3", 34, 56), ("g3", 61, 56), ("g3", 36, 66), ("g3", 59, 66), ("g3", 40, 74), ("g3", 55, 74), ("g3", 34, 80), ("g3", 61, 80),
         ("g3", 38, 88), ("g3", 57, 88), ("b3", 47, 24), ("b3", 37, 30), ("b3", 58, 30), ("g3", 22, 70), ("g3", 73, 70),
         ("b3", 20, 76), ("b3", 76, 53), ("g3", 20, 84), ("g3", 76, 83), ("g3", 28, 44), ("g3", 40, 56), ("g3", 55, 56)]
# ---- evolution line (user: each evolution bigger). The drawing above is the BASE (63 tall at 96); each stage re-plots its polygons about the
# mirror axis and the ground row (feet stay on row 91, like the 64 re-plot), nothing is resampled. Eyes keep one 3x3 stamp at every stage.
# Signature = gold bands, multiplying 1 / 3 / 5: stage 1 has the fillet only; stage 2 adds the cuffs (3 with the staff caps' band); stage 3 the rest.
import math
STAGE = {1: dict(K=0.74, gold=1, height=(44, 50)), 2: dict(K=1.0, gold=3, height=(60, 66)), 3: dict(K=1.30, gold=5, height=(78, 86))}
EYES = [("head", "v", [(44, 41), (47, 41), (47, 44), (44, 44)], False), ("head", "v", [(48, 41), (51, 41), (51, 44), (48, 44)], False)]


def sx(x, K):
    d = (x - 47.5) * K
    return 48 + math.floor(d) if d >= 0 else 47 - math.floor(-d)


def sy(y, K): return 91 - int(math.floor((91 - y) * K + 0.5))


def is_extra_gold(p):
    r, ramp, poly, flat = p
    return ramp == "b" and (r in ("armL", "pauL", "pauR", "skirt", "hand") or (r == "staff" and flat))


def stage_view(n):
    st = STAGE[n]; K = st["K"]
    parts = [p for p in PARTS if p[:3] not in [e[:3] for e in EYES] and (st["gold"] >= 3 or not is_extra_gold(p))]
    out = [(r, rp, [(sx(x, K), sy(y, K)) for x, y in pl], fl) for r, rp, pl, fl in parts]
    a, b = sx(44, K), sy(41, K)
    left = [(a, b), (a + 3, b), (a + 3, b + 3), (a, b + 3)]
    out += [("head", "v", left, False), ("head", "v", mir(left), False)]
    details = [(c, sx(x0, K), sy(y0, K), sx(x1, K), sy(y1, K)) for c, x0, y0, x1, y1 in DETAILS if c != "glow"]
    details += [("glow", a + 1, b + 1, a + 1, b + 1), ("glow", 94 - a - 1, b + 1, 94 - a - 1, b + 1)]
    keep = lambda s_: st["gold"] >= 3 or s_[0] != "b3"
    studs = list(dict.fromkeys((c, sx(x, K), sy(y, K)) for c, x, y in STUDS if keep((c, x, y))))
    hx = sx(47, K); studs += [("b3", hx, sy(32, K)), ("b3", sx(38, K), sy(37, K)), ("b3", sx(57, K), sy(37, K))] if st["gold"] == 1 else []
    return dict(parts=out, details=details, studs=studs, flip=False, shoulder=(sx(66, K), sy(41, K)), fist=(sx(72, K), sy(84, K)), hipfix=False)


VIEW = stage_view(1)


def render(view):
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = CONFIG["PAL"]; F.CONFIG["RAMP"] = CONFIG["RAMP"]
    try:
        return V.crop96(V.build(view, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def main(n=1):
    import os
    os.makedirs("out", exist_ok=True)
    V.CONFIG["HEIGHT"] = STAGE[n]["height"]
    img = render(stage_view(n))
    fails, rep = V.idle_checks("猿魔 stage1 front", img)
    A = img[..., 3] > 0
    ys, xs = np.where(A)
    rep["width"] = int(xs.max() - xs.min() + 1)
    iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum()); rep["mirror_iou"] = round(iou, 2)
    if not 0.4 <= iou <= 0.9: fails.append(f"mirror IoU {iou:.2f}")
    Image.fromarray(img, "RGBA").save(f"out/ym{n}_front_1x.png")
    bg = Image.new("RGBA", (96, 96), (58, 62, 72, 255)); bg.alpha_composite(Image.fromarray(img, "RGBA"))
    for s in (3, 5): bg.resize((96 * s, 96 * s), Image.NEAREST).save(f"out/ym{n}_front_{s}x.png")
    names = ["approved/jianxian/jx_idle_front_1x.png", "approved/mojiang/mo_idle_front_1x.png", "approved/mingjiang/mj_idle_front_1x.png",
             "approved/tianbing96/views_idle_front_1x.png", "approved/wushi/ws_idle_front_1x.png", "approved/tianlong/tl_idle_front_1x.png", "approved/gushi/gs_idle_front_1x.png"]
    sheet = Image.new("RGBA", (96 * 8, 96), (58, 62, 72, 255))
    sheet.alpha_composite(Image.fromarray(img, "RGBA"), (0, 0))
    for i, n in enumerate(names):
        try: sheet.alpha_composite(Image.open(n).convert("RGBA"), ((i + 1) * 96, 0))
        except FileNotFoundError: pass
    sheet.resize((96 * 24, 288), Image.NEAREST).save("out/ym_lineup_3x.png")
    print(rep); print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1)
