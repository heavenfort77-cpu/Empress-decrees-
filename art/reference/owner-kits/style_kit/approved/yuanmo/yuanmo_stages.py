"""猿魔 growth line, three stages, front view at 96 (each stage re-plotted at its own size, never resized as pixels).
Rules from the user's Evolution-Asset-Tips: same eye stamp at every stage (the head is a fixed-size stamp; the body grows around it),
same ramps and light, feet on the same row, ~1.3x height per stage, one new feature per stage hinted a stage early, one signature that
multiplies 1 -> 3 -> 5, at least 3 px side margin.
  signature: gold glow-studs on the hump (1, 3, 5)
  staff: telescopes longer every stage (its nature, not a new feature)
  stage 2 new: shoulder horns (stage 1 has nubs)   stage 3 new: swept crest blades on the head (stage 2 has a nub)
Body geometry is drawn once in stage-3 coordinates (96 grid, feet row 91, axis 47.5) and re-plotted per stage with factor K about the feet.
Run: python3 yuanmo_stages.py -> out/ym_s{1,2,3}_front_1x.png, out/ym_stages_4x.png (pass/fail only)
"""
import math
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V
import gushi96 as G
import yuanmo96 as Y1

CONFIG = {
    "PAL": Y1.CONFIG["PAL"], "RAMP": Y1.CONFIG["RAMP"],
    # stage: body factor K, staff top (stage-3 y before K), studs kept, target height range
    "STAGES": {1: dict(K=0.58, staff=34, studs=1, H=(48, 56)), 2: dict(K=0.76, staff=22, studs=3, H=(64, 72)),
               3: dict(K=1.0, staff=10, studs=5, H=(84, 92))},
    "MARGIN": 3, "GROWTH": (1.2, 1.42),
}


def mir(p): return [(95 - x, y) for x, y in p][::-1]
def sym(h): return h + mir(h)
def pair(rg, rp, p, flat=False, rr=None): return [(rg, rp, p, flat), (rr or rg, rp, mir(p), flat)]


def BX(x, K):
    d = (x - 47.5) * K
    return 48 + math.floor(d) if d >= 0 else 47 - math.floor(-d)


def BY(y, K): return 91 - int(math.floor((91 - y) * K + 0.5))


def body3(stage):
    """stage-3 geometry (ape body plan): trapezius hump up beside the head, broad V chest, narrow waist, short bowed legs,
    arms longer than the legs with fists knuckled on the ground; features gated by stage"""
    P = []
    # short bowed legs: thigh out to the knee, shin back in, wide flat foot
    P += pair("legL", "g", G.seg((39, 64), (30, 76), 11), False, "legR")
    P += pair("legL", "g", G.seg((30, 76), (33, 86), 10), False, "legR")
    P += pair("legL", "g", [(25, 85), (42, 85), (43, 91), (24, 91)], False, "legR")
    if stage >= 2: P += pair("legL", "b", [(26, 75), (34, 75), (34, 78), (26, 78)], True, "legR")          # stage 2+: gold knee caps
    P += [("skirt", "g", sym([(47, 62), (37, 60), (35, 66), (39, 71), (47, 72)]), False),
          ("skirt", "b", [(36, 63), (59, 63), (59, 64), (36, 64)], True)]
    # V torso with the trapezius hump rising beside the head
    P += [("torso", "g", sym([(47, 16), (38, 13), (27, 13), (18, 20), (14, 30), (18, 42), (27, 52), (34, 60), (47, 62)]), False),
          ("torso", "g", sym([(46, 30), (36, 28), (28, 33), (29, 42), (37, 47), (46, 48)]), False),          # pectoral plates
          *([("torso", "b", sym([(46, 29), (36, 27), (27, 32), (28, 34), (37, 29), (46, 31)]), True)] if stage == 3 else []),   # stage 3: gold pectoral rims
          *([("torso", "b", [(29, 15), (33, 15), (32, 5), (30, 5)], False), ("torso", "b", [(62, 15), (66, 15), (65, 5), (63, 5)], False),
             ("torso", "b", [(37, 13), (41, 13), (40, 3), (38, 3)], False), ("torso", "b", [(54, 13), (58, 13), (57, 3), (55, 3)], False)] if stage == 3 else []),   # stage 3: dorsal ridge spikes
          ("torso", "b", sym([(47, 56), (43, 58), (42, 62), (44, 65), (47, 66)]), False),
          ("torso", "v", sym([(47, 59), (45, 60), (45, 62), (47, 63)]), False)]
    for cx, pr in ((18, "pauL"), (77, "pauR")):           # deltoid masses
        P += [(pr, "g", G.circ_at(cx, 28, 9, 20), False), (pr, "b", G.circ_at(cx, 28, 4, 12), False)]
        s_ = -1 if cx < 47 else 1
        if stage == 1:
            P += [(pr, "b", [(cx + s_ * 2, 20), (cx + s_ * 6, 20), (cx + s_ * 5, 17), (cx + s_ * 3, 17)], False)]
        else:
            P += [(pr, "b", [(cx + s_ * 1, 21), (cx + s_ * 8, 20), (cx + s_ * 12, 9), (cx + s_ * 9, 11)], False)]
    # staff first so the right fist wraps it
    P += [("staff", "s", G.seg((84, 12), (84, 90), 5), False),
          ("staff", "b", [(81, 70), (87, 70), (87, 73), (81, 73)], True)]
    # long arms, forearms thicker than upper arms, fists knuckled on the ground
    P += [("armL", "g", G.seg((17, 32), (10, 54), 11), False), ("armL", "g", G.circ_at(10, 55, 6, 16), False), ("armL", "g", G.seg((10, 56), (14, 82), 13), False),
          ("armL", "b", [(6, 66), (20, 66), (20, 70), (6, 70)], False),
          *([("armL", "b", [(7, 74), (20, 74), (20, 76), (7, 76)], True)] if stage >= 2 else []),                      # stage 2+: second bracer band
          ("hand", "g", [(7, 81), (20, 81), (21, 88), (19, 91), (8, 91), (6, 88)], False),
          ("hand", "b", [(8, 88), (19, 88), (19, 89), (8, 89)], True),
          ("armR", "g", G.seg((78, 32), (85, 44), 11), False), ("armR", "g", G.circ_at(85, 45, 6, 16), False), ("armR", "g", G.seg((85, 46), (84, 56), 12), False),
          *([("armR", "b", [(80, 50), (90, 50), (90, 52), (80, 52)], True)] if stage >= 2 else []),                    # stage 2+: right bracer band
          ("hand", "g", [(78, 54), (90, 54), (91, 60), (89, 63), (79, 63), (77, 60)], False),
          ("hand", "b", [(79, 58), (89, 58), (89, 59), (79, 59)], True),
          ("staff", "b", [(81, 88), (87, 88), (88, 91), (80, 91)], False)]
    return P


STUD_SPOTS = [(47, 61), (35, 38), (60, 38), (27, 20), (68, 20)]      # signature studs (the first is the belly core)


def head_stamp(stage, top):
    """ape head: the EYES are a fixed stamp (same pixels, same place relative to the brow) at every stage, but the skull, brow and
    muzzle grow with the stage (the tips say grow the body round the eyes; the muzzle is body). top = dome top row. g = growth 0/1/2"""
    g = stage - 1
    o = top - 31
    sh = lambda p: [(x, y + o) for x, y in p]
    mw, md = 6 + g, 9 + g * 2                 # muzzle half-width and depth
    H = [("head", "g", sh([(41 - g, 46), (40 - g, 38), (43 - g, 33), (47, 31), (48, 31), (52 + g, 33), (55 + g, 38), (54 + g, 46)]), False),
         ("head", "f", sh([(41, 39), (54, 39), (54, 44), (41, 44)]), True),
         ("head", "g", sh([(40 - g, 36), (55 + g, 36), (56 + g, 39), (39 - g, 39)]), False),                         # brow ledge
         ("head", "s", sh([(47 - mw, 44), (48 + mw, 44), (50 + mw, 48), (48 + mw - 2, 44 + md), (47 - mw + 2, 44 + md), (45 - mw, 48)]), False),
         ("head", "f", sh([(44 - g, 44 + md - 3), (51 + g, 44 + md - 3), (51 + g, 44 + md - 2), (44 - g, 44 + md - 2)]), True),   # mouth slit
         ("head", "b", sh([(41 - g, 34), (54 + g, 34), (55 + g, 36), (40 - g, 36)]), False),                           # gold fillet
         ("head", "b", sh([(37 - g, 35), (40 - g, 35), (40 - g, 41), (37 - g, 41)]), False), ("head", "b", sh([(55 + g, 35), (58 + g, 35), (58 + g, 41), (55 + g, 41)]), False)]
    if stage == 2:
        H += [("head", "b", sh([(46, 28), (49, 28), (50, 32), (45, 32)]), False)]
    if stage == 3:
        H += [("head", "b", sh([(45, 32), (50, 32), (49, 24), (48, 21), (47, 21), (46, 24)]), False)]
    eyes = [("v1", 43, 40 + o, 45, 42 + o), ("v1", 50, 40 + o, 52, 42 + o), ("v0", 45, 42 + o, 45, 42 + o), ("v0", 52, 42 + o, 52, 42 + o),
            ("glow", 43, 40 + o, 43, 40 + o), ("glow", 50, 40 + o, 50, 40 + o),
            ("out", 46 - g, 46 + o, 46 - g, 46 + o), ("out", 49 + g, 46 + o, 49 + g, 46 + o)]
    return H, eyes


def view(stage):
    st = CONFIG["STAGES"][stage]; K = st["K"]
    parts = []
    for rg, rp, poly, fl in body3(stage):
        if rg == "staff" and rp == "s":
            poly = [(x, max(y, st["staff"])) if y < 30 else (x, y) for x, y in poly]
        parts.append((rg, rp, [(BX(x, K), BY(y, K)) for x, y in poly], fl))
    t = BY(st["staff"], K); cx = BX(84, K)
    parts.insert([i for i, p in enumerate(parts) if p[0] == "staff"][1] + 1, ("staff", "b", [(cx - 2, t - 4), (cx + 2, t - 4), (cx + 3, t + 1), (cx - 3, t + 1)], False))
    studs, details = [], []
    for i, (x, y) in enumerate(STUD_SPOTS[:st["studs"]]):
        X, Yy = BX(x, K), BY(y, K)
        if i:
            parts.append(("torso", "b", G.circ_at(X + (0.5 if x > 47 else -0.5), Yy, 2.2, 10), False))
        studs.append(("v2", X, Yy))
    for x, y in [(18, 28), (77, 28), (30, 76), (65, 76), (13, 86), (85, 58), (22, 46), (73, 46), (10, 55), (85, 45), (34, 89), (61, 89)]:
        studs.append(("g3", BX(x, K), BY(y, K)))
    H, eyes = head_stamp(stage, BY(14, K) + (2 if stage == 1 else 4))
    parts += H; details += eyes
    return dict(parts=parts, details=details, studs=studs, flip=False, shoulder=(BX(77, K), BY(28, K)), fist=(BX(85, K), BY(58, K)), hipfix=False)


def render(v):
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = CONFIG["PAL"]; F.CONFIG["RAMP"] = CONFIG["RAMP"]
    try:
        return V.crop96(V.build(v, None))
    finally:
        F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep


def main():
    fails, imgs, eyes = [], {}, []
    for s in (1, 2, 3):
        V.CONFIG["HEIGHT"] = CONFIG["STAGES"][s]["H"]
        img = render(view(s)); imgs[s] = img
        f, rep = V.idle_checks(f"stage {s}", img); fails += f
        A = img[..., 3] > 0; ys, xs = np.nonzero(A)
        if xs.min() < CONFIG["MARGIN"] or 95 - xs.max() < CONFIG["MARGIN"]: fails.append(f"stage {s}: side margin {min(xs.min(), 95 - xs.max())}")
        iou = float((A & A[:, ::-1]).sum() / (A | A[:, ::-1]).sum()); rep["mirror_iou"] = round(iou, 2)
        if not 0.4 <= iou <= 0.9: fails.append(f"stage {s}: mirror IoU {iou:.2f}")
        glow = np.array(F.hexrgb(CONFIG["PAL"]["glow"])[:3])
        gy, gx = np.nonzero((img[..., :3] == glow).all(axis=2) & A)
        eyes.append(img[gy.min():gy.min() + 3, 43:53].tobytes())
        rep["feet_row"] = int(ys.max()); print(s, rep)
        Image.fromarray(img, "RGBA").save(f"out/ym_s{s}_front_1x.png")
    hs = [int(np.ptp(np.nonzero(imgs[s][..., 3].any(axis=1))[0]) + 1) for s in (1, 2, 3)]
    for a, b in ((0, 1), (1, 2)):
        r = hs[b] / hs[a]
        if not CONFIG["GROWTH"][0] <= r <= CONFIG["GROWTH"][1]: fails.append(f"growth {a + 1}->{b + 1}: {r:.2f}x")
    print("heights", hs, "growth", [round(hs[1] / hs[0], 2), round(hs[2] / hs[1], 2)])
    if len(set(eyes)) != 1: fails.append("eye stamp differs between stages")
    sheet = Image.new("RGBA", (96 * 3 + 8, 96), (58, 62, 72, 255))
    for i, s in enumerate((1, 2, 3)): sheet.alpha_composite(Image.fromarray(imgs[s], "RGBA"), (i * 100, 0))
    sheet.resize((sheet.width * 4, 96 * 4), Image.NEAREST).save("out/ym_stages_4x.png")
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
