"""天兵 (Heavenly Soldier) front sample v5, 96x96. Original art; references are shape language and measured style only.
Changes from v4: shading per body REGION (large calm light planes), bevelled helmet with brim and cheek guards,
vertical halberd shaft with a large crescent blade, limb slopes fixed at 1:1 / 1:2 / 1:4, hand-placed highlights and rivets.
Run: python3 tianbing96_v5.py -> out/tb5_front_{1x,3x,4x}.png, out/tb5_sil_1x.png, pass/fail report.
Everything tunable is in CONFIG; every shape is data in PARTS (region, ramp, polygon, flat).
"""
import os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

CONFIG = {
    "W": 96, "H": 96,
    "PAL": {
        "out": "#0d1418",                                   # outline, seams and inner frame (one dark colour)
        "g1": "#1a4541", "g2": "#2e7358", "g3": "#7bb565",  # lacquer green: cool teal shade, mid, warm light
        "b1": "#8a5a2b", "b2": "#c48c3c", "b3": "#f2cb6a",  # bronze
        "s1": "#2d3846", "s2": "#687a8a", "s3": "#aebfcc",  # steel
        "v1": "#c8432c", "v2": "#ff925c",                   # vermilion accent
        "glow": "#c2fff1",                                  # visor
    },
    "RAMP": {   # (shade, mid, light)
        "g": ("g1", "g2", "g3"), "b": ("b1", "b2", "b3"), "s": ("s1", "s2", "s3"),
        "v": ("v1", "v1", "v2"), "f": ("out", "out", "out"),
    },
    "LIGHT_BAND": 2, "RIVET_ROWS": True, "BOLT_HOLES": True, "RIVET_STEP": 3, "SHADE_FRAC": 0.66, "SMALL_REGION": 120,   # regions under this area get a 1 px light band
    "LIM": {"height": (72, 94), "feet_gap_min": 3, "head_share": (0.12, 0.20),
            "lone_pct": (4.6, 10.2), "colours": (9, 13),
            "seam_pct": (23.2, 31.5), "dark_pct": (37.4, 77.5), "mirror_iou_max": 0.9},
    "HEAD_ROWS": (14, 30),   # dome top to chin; ridge plate excluded
}

# (region, ramp, polygon, flat) drawn in order, back to front
PARTS = [
    # halberd (behind the right arm)
    ("halberd", "s", [(68, 4), (70, 4), (70, 91), (68, 91)], True),               # shaft
    ("halberd", "s", [(69, 1), (72, 5), (71, 12), (67, 12), (66, 5)], False),     # spear tip
    ("halberd", "s", [(71, 8), (80, 4), (89, 8), (92, 16), (87, 25), (78, 27), (71, 21)], False),   # crescent blade
    ("halberd", "f", [(74, 11), (84, 10), (85, 18), (80, 22), (75, 18)], True),   # blade cut-out (dark)
    ("halberd", "b", [(65, 12), (74, 12), (74, 15), (65, 15)], True),             # collar
    ("halberd", "v", [(71, 15), (75, 15), (76, 26), (72, 26)], False),            # ribbon
    # right leg (image right), planted; 1:4 thigh slope
    ("legR", "f", [(50, 56), (60, 56), (64, 76), (54, 76)], True),
    ("legR", "g", [(48, 58), (58, 58), (62, 74), (52, 74)], False),                # thigh plate
    ("legR", "s", [(52, 73), (63, 73), (64, 79), (53, 79)], False),                # knee
    ("legR", "f", [(54, 78), (63, 78), (63, 89), (54, 89)], True),
    ("legR", "g", [(53, 80), (63, 80), (63, 88), (54, 88)], False),                # shin guard
    ("legR", "b", [(52, 86), (66, 86), (68, 91), (52, 91)], False),                # boot
    # left leg (image left), stepping out; 1:2 thigh slope
    ("legL", "f", [(36, 56), (48, 56), (40, 76), (28, 76)], True),
    ("legL", "g", [(38, 58), (48, 58), (40, 74), (30, 74)], False),
    ("legL", "s", [(29, 73), (40, 73), (41, 79), (30, 79)], False),
    ("legL", "f", [(29, 78), (40, 78), (40, 89), (29, 89)], True),
    ("legL", "g", [(30, 80), (40, 80), (39, 88), (30, 88)], False),
    ("legL", "b", [(24, 86), (40, 86), (42, 91), (24, 91)], False),
    # pelvis, belt, skirt
    ("skirt", "f", [(38, 52), (58, 52), (58, 62), (38, 62)], True),
    ("skirt", "b", [(40, 52), (56, 52), (56, 55), (40, 55)], False),               # belt
    ("skirt", "g", [(31, 56), (41, 56), (40, 66), (32, 66)], False),               # left tasset (right one is its exact mirror)
    ("skirt", "g", [(54, 56), (64, 56), (63, 66), (55, 66)], False),               # right tasset = mirror of left on axis 47.5
    ("skirt", "g", [(41, 55), (54, 55), (54, 66), (48, 70), (47, 70), (41, 66)], False),   # front tasset, centred on 47.5
    # torso
    ("torso", "f", [(43, 29), (53, 29), (53, 34), (43, 34)], True),                # neck
    ("torso", "f", [(37, 33), (59, 33), (59, 54), (37, 54)], True),                # inner frame
    ("torso", "g", [(36, 33), (60, 33), (62, 38), (59, 50), (50, 54), (46, 54), (37, 50), (34, 38)], False),   # chest
    ("torso", "s", [(44, 38), (52, 38), (53, 44), (48, 47), (43, 44)], False),     # core ring
    ("torso", "v", [(46, 40), (50, 40), (50, 43), (46, 43)], True),                # core
    # right pauldron (large) and right arm, fist on shaft
    ("pauR", "g", [(56, 30), (61, 25), (74, 26), (78, 31), (77, 40), (70, 44), (59, 42), (55, 36)], False),
    ("pauR", "b", [(58, 28), (61, 25), (74, 26), (77, 29), (74, 29), (62, 28)], True),   # rim
    ("pauR", "g", [(60, 40), (76, 39), (75, 45), (62, 46)], False),                # lower lame
    ("armR", "f", [(62, 42), (72, 42), (76, 56), (65, 57)], True),
    ("armR", "g", [(63, 43), (71, 43), (74, 54), (66, 55)], False),                # upper arm (1:4)
    ("armR", "s", [(65, 53), (74, 53), (75, 58), (66, 59)], False),                # elbow
    ("armR", "g", [(66, 58), (74, 58), (73, 68), (65, 68)], False),                # forearm
    ("armR", "b", [(66, 61), (74, 61), (74, 63), (66, 63)], True),                 # band
    ("armR", "s", [(64, 68), (75, 68), (76, 75), (70, 77), (64, 74)], False),      # fist
    # left arm raised (1:1 upper arm), pagoda in hand
    ("pauL", "g", [(26, 33), (32, 27), (41, 30), (41, 38), (34, 41), (27, 39)], False),
    ("pauL", "b", [(28, 31), (32, 27), (41, 30), (39, 31), (32, 29)], True),
    ("armL", "f", [(26, 41), (36, 41), (28, 30), (18, 30)], True),
    ("armL", "g", [(27, 40), (34, 40), (26, 32), (19, 32)], False),                # upper arm, slanting up-left
    ("armL", "s", [(18, 28), (28, 28), (28, 33), (18, 33)], False),                # elbow
    ("armL", "g", [(20, 21), (27, 21), (27, 29), (20, 29)], False),                # forearm up
    ("armL", "b", [(20, 24), (27, 24), (27, 26), (20, 26)], True),
    ("armL", "s", [(18, 16), (29, 16), (29, 21), (18, 21)], False),                # hand
    ("pagoda", "b", [(14, 15), (17, 13), (30, 13), (33, 15), (30, 16), (17, 16)], False),   # eave 1
    ("pagoda", "g", [(18, 9), (29, 9), (29, 13), (18, 13)], False),                # body 1
    ("pagoda", "b", [(16, 8), (19, 6), (28, 6), (31, 8), (28, 9), (19, 9)], False),         # eave 2
    ("pagoda", "g", [(20, 4), (27, 4), (27, 6), (20, 6)], False),                  # body 2
    ("pagoda", "b", [(18, 3), (21, 2), (26, 2), (29, 3), (26, 4), (21, 4)], False),         # eave 3
    # head: bevelled dome, ridge plate, brim, cheek guards
    ("head", "g", [(41, 20), (43, 16), (46, 14), (49, 14), (52, 16), (54, 20), (54, 28), (52, 30), (42, 30), (40, 28)], False),
    ("head", "b", [(45, 14), (47, 12), (48, 12), (50, 14), (50, 15), (45, 15)], False),     # ridge plate
    ("head", "b", [(40, 20), (54, 20), (54, 21), (40, 21)], True),                 # brim band
    ("head", "s", [(40, 22), (42, 22), (42, 29), (40, 28)], False),                # cheek guard L
    ("head", "s", [(52, 22), (54, 22), (54, 28), (52, 29)], False),                # cheek guard R
]

DETAILS = [  # (colour, x0, y0, x1, y1) on top, only where the sprite exists
    ("out", 43, 22, 51, 25), ("glow", 44, 23, 50, 24),      # visor slot and slit
    ("v1", 47, 13, 48, 13),                                 # ridge gem
    ("out", 47, 33, 48, 37), ("out", 47, 47, 48, 53),       # chest centre seam
    ("out", 37, 44, 42, 44), ("out", 54, 44, 59, 44),       # chest panel lines
    ("out", 38, 48, 41, 48), ("out", 55, 48, 58, 48),
    ("out", 47, 55, 48, 66), ("out", 34, 61, 38, 61), ("out", 57, 61, 61, 61),   # skirt seams (mirrored pair)
    ("out", 33, 84, 37, 84), ("out", 56, 84, 60, 84),       # shin seams
    ("out", 36, 66, 44, 66), ("out", 52, 66, 60, 66),       # thigh lines
    ("out", 64, 34, 72, 34), ("out", 62, 37, 70, 37),       # pauldron lines
    ("out", 30, 34, 37, 34),
    ("out", 43, 17, 51, 17),                                # helm bevel line
    ("v2", 22, 11, 22, 11), ("v2", 25, 11, 25, 11), ("v1", 28, 11, 28, 11),   # pagoda lamp windows
    ("v2", 23, 5, 23, 5), ("v1", 26, 5, 26, 5), ("b3", 23, 1, 24, 1),         # top windows, finial
    ("s3", 76, 10, 76, 10), ("s3", 73, 7, 73, 7),           # blade glints
]
STUDS = [  # single pixels: rivets (b3) and specular (s3 / g3)
    ("b3", 38, 36), ("b3", 58, 36), ("b3", 40, 50), ("b3", 56, 50), ("s3", 45, 39), ("s3", 51, 39),
    ("b3", 32, 58), ("b3", 64, 59), ("b3", 43, 57), ("b3", 53, 57), ("s3", 31, 75), ("s3", 54, 75),
    ("b3", 32, 82), ("b3", 61, 82), ("b3", 39, 62), ("b3", 57, 62), ("s3", 66, 55), ("s3", 20, 30),
    ("b3", 59, 31), ("b3", 75, 31), ("b3", 63, 42), ("b3", 29, 32), ("b3", 38, 32), ("b3", 29, 38),
    ("b3", 68, 46), ("b3", 68, 65), ("s3", 66, 70), ("s3", 20, 18), ("b3", 22, 27), ("s3", 44, 28),
    ("s3", 50, 28), ("b3", 27, 89), ("b3", 60, 89), ("b3", 35, 70), ("b3", 59, 70), ("s3", 69, 16),
    ("g3", 39, 42), ("g3", 57, 42), ("g3", 35, 63), ("g3", 61, 63), ("g3", 20, 10), ("b3", 44, 52),
    ("b3", 52, 52), ("s3", 48, 45), ("b3", 36, 86), ("b3", 57, 86), ("g3", 68, 60), ("g3", 23, 23),
]


def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mask(poly, W, H):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255, outline=255)
    return np.array(m) > 0


def diag_dist(M, sy, sx, kmax=16):
    H, W = M.shape
    d = np.zeros(M.shape, int)
    alive = M.copy()
    for k in range(1, kmax + 1):
        sh = np.zeros_like(M)
        ys = slice(max(0, sy * k), H + min(0, sy * k)); yd = slice(max(0, -sy * k), H + min(0, -sy * k))
        xs = slice(max(0, sx * k), W + min(0, sx * k)); xd = slice(max(0, -sx * k), W + min(0, -sx * k))
        sh[yd, xd] = M[ys, xs]
        d[alive & ~sh] = k
        alive &= sh
    d[alive] = kmax
    return d


def build():
    W, H, P = CONFIG["W"], CONFIG["H"], CONFIG["PAL"]
    img = np.zeros((H, W, 4), np.uint8)
    ramp_of = np.full((H, W), "", dtype="<U1")
    flat_px = np.zeros((H, W), bool)
    region_of = np.full((H, W), "", dtype="<U8")
    out = hexrgb(P["out"])
    # pass 1: flat mid fills with part seams
    for region, ramp, poly, flat in PARTS:
        M = mask(poly, W, H)
        sh, mid, lit = (hexrgb(P[k]) for k in CONFIG["RAMP"][ramp])
        img[M, :3] = mid; img[M, 3] = 255
        ramp_of[M] = ramp; flat_px[M] = flat or ramp == "f"; region_of[M] = region
        if not flat and ramp != "f":
            dn = np.zeros_like(M); dn[:-1] = M[1:]
            rt = np.zeros_like(M); rt[:, :-1] = M[:, 1:]
            seam = M & (~dn | ~rt)
            img[seam, :3] = out
            flat_px[seam] = True
    # pass 2: region light and shade
    for region in sorted(set(region_of[region_of != ""].tolist())):
        R = (region_of == region) & ~flat_px
        Rall = region_of == region
        dul = diag_dist(Rall, -1, -1)
        ddr = diag_dist(Rall, 1, 1)
        t = dul / np.maximum(dul + ddr, 1)
        band = CONFIG["LIGHT_BAND"] if Rall.sum() >= CONFIG["SMALL_REGION"] else 1
        for ramp in ("g", "b", "s", "v"):
            sel = R & (ramp_of == ramp)
            sh, mid, lit = (hexrgb(P[k]) for k in CONFIG["RAMP"][ramp])
            img[sel & (t > CONFIG["SHADE_FRAC"]), :3] = sh
            img[sel & (dul <= band), :3] = lit
    # rivet rows: bronze studs every RIVET_STEP px, 3 rows inside the top and bottom edge of each green plate
    if CONFIG["RIVET_ROWS"]:
        b3 = hexrgb(P["b3"])
        for region, ramp, poly, flat in PARTS:
            if flat or ramp != "g":
                continue
            M = mask(poly, W, H)
            if M.sum() < 60:
                continue
            dt = diag_dist(M, -1, 0); db = diag_dist(M, 1, 0)
            rows = (dt == 3) | (db == 3)
            ys_, xs_ = np.nonzero(rows & M & ~flat_px)
            for y, x in zip(ys_, xs_):
                if (x + y // 7) % CONFIG["RIVET_STEP"] == 0 and (region_of[y, x] == region):
                    img[y, x, :3] = b3
    # bolt holes: dark single pixels on steel joint parts (centre and 3 px either side)
    if CONFIG["BOLT_HOLES"]:
        for region, ramp, poly, flat in PARTS:
            if flat or ramp != "s":
                continue
            M = mask(poly, W, H)
            if M.sum() < 40:
                continue
            ys_, xs_ = np.nonzero(M)
            cy, cx = int(round(ys_.mean())), int(round(xs_.mean()))
            for x in (cx - 3, cx, cx + 3):
                if M[cy, x] and not flat_px[cy, x]:
                    img[cy, x, :3] = out
    for key, x0, y0, x1, y1 in DETAILS:
        blk = img[y0:y1 + 1, x0:x1 + 1]
        blk[blk[..., 3] > 0, :3] = hexrgb(P[key])
    for key, x, y in STUDS:
        if img[y, x, 3] > 0:
            img[y, x, :3] = hexrgb(P[key])
    # hip plates: right tasset is an exact pixel mirror of the left (axis 47.5, x' = 95 - x)
    for y in range(55, 67):
        for x in range(31, 42):
            if img[y, x, 3] > 0:
                img[y, 95 - x] = img[y, x]
    A = img[..., 3] > 0
    nb = np.zeros_like(A)
    nb[1:] |= A[:-1]; nb[:-1] |= A[1:]; nb[:, 1:] |= A[:, :-1]; nb[:, :-1] |= A[:, 1:]
    ol = nb & ~A
    img[ol, :3] = out; img[ol, 3] = 255
    return img


def checks(img):
    L = CONFIG["LIM"]
    A = img[..., 3] > 0
    ys, xs = np.where(A)
    height = ys.max() - ys.min() + 1
    res = {}
    res["height"] = (L["height"][0] <= height <= L["height"][1], f"{height} px {L['height']}")
    gap = img.shape[0] - 1 - ys.max()
    res["feet gap"] = (gap >= L["feet_gap_min"], f"{gap} rows")
    h0, h1 = CONFIG["HEAD_ROWS"]
    hs = (h1 - h0 + 1) / height
    res["head share"] = (L["head_share"][0] <= hs <= L["head_share"][1], f"{hs:.2f} {L['head_share']}")
    rgb = img[..., :3].astype(int)
    cols = {tuple(p) for p in rgb[A]}
    res["colours"] = (L["colours"][0] <= len(cols) <= L["colours"][1], f"{len(cols)} {L['colours']}")
    pad = np.pad(rgb, ((1, 1), (1, 1), (0, 0)), mode="edge")
    ne = lambda a, b: (a != b).any(axis=2)
    d = ne(rgb, pad[:-2, 1:-1]) & ne(rgb, pad[2:, 1:-1]) & ne(rgb, pad[1:-1, :-2]) & ne(rgb, pad[1:-1, 2:])
    lone = (d & A).sum() / A.sum() * 100
    res["isolated px"] = (L["lone_pct"][0] <= lone <= L["lone_pct"][1], f"{lone:.1f}% {L['lone_pct']}")
    n = ndi.label(A, structure=np.ones((3, 3)))[1]
    res["one piece"] = (n == 1, f"{n}")
    out = np.array(hexrgb(CONFIG["PAL"]["out"]))
    pA = np.pad(A, 1)
    interior = A & pA[:-2, 1:-1] & pA[2:, 1:-1] & pA[1:-1, :-2] & pA[1:-1, 2:]
    seam = ((rgb == out).all(axis=2) & interior).sum() / A.sum() * 100
    res["seam lines"] = (L["seam_pct"][0] <= seam <= L["seam_pct"][1], f"{seam:.1f}% {L['seam_pct']}")
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    dark = ((lum < 60) & A).sum() / A.sum() * 100
    res["dark share"] = (L["dark_pct"][0] <= dark <= L["dark_pct"][1], f"{dark:.1f}% {L['dark_pct']}")
    sub = A[:, xs.min():xs.max() + 1]
    iou = (sub & sub[:, ::-1]).sum() / (sub | sub[:, ::-1]).sum()
    res["mirror IoU"] = (iou <= L["mirror_iou_max"], f"{iou:.2f} (ref 0.4-0.9)")
    return res


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    img = build()
    W = CONFIG["W"]
    Image.fromarray(img, "RGBA").save(f"{out}/tb5_front_1x.png")
    for s in (3, 4):
        Image.fromarray(img, "RGBA").resize((W * s, W * s), Image.NEAREST).save(f"{out}/tb5_front_{s}x.png")
    sil = np.zeros_like(img); sil[img[..., 3] > 0] = (30, 30, 30, 255)
    Image.fromarray(sil, "RGBA").save(f"{out}/tb5_sil_1x.png")
    res = checks(img)
    bad = [k for k, (ok, _) in res.items() if not ok]
    for k, (ok, msg) in res.items():
        print(("PASS " if ok else "FAIL ") + k + ": " + msg)
    print("ALL PASS" if not bad else "FAILING: " + ", ".join(bad))


if __name__ == "__main__":
    main()
