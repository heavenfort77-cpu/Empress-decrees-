"""Scene in the suit style (python3 scene/scene_suitstyle.py): ground, bushes, ore and props drawn with the SAME method as the approved suits
(tianbing96_v5.build): every surface is a polygon part with a 3-step ramp, mid fill, a one-colour seam (#0d1418) on the bottom/right edge, a 2 px light
band on the upper-left edge, the lower-right third shaded, rivet rows and bolt holes on plates. Light from the upper left, like the suits.
Ramps: stone (new, darker than the suit steel so the suits stay the brightest thing), the suits' steel, jade and bronze ramps for bushes and ore.
Tiles: ground x5 (plate layouts), bush, ore, stele, lantern, rubble. Then a 7x5 scene with the approved suits, shadows, light pool and pixel HUD
(same as scene_mock.py). Output: out/suitstyle_tiles_1x.png/_3x.png, out/scene_suitstyle_1x.png/_2x.png, out/scene_compare2_2x.png. Pass/fail only."""
import math, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
sys.argv = [sys.argv[0], "96"]
import scene_mock as SM

S = 96
K = 1.0
def P(x): return int(round(x * K))


class SD:
    """ImageDraw wrapper that plots 96-space coordinates at the current size (whole numbers, no resampling)"""
    def __init__(self, d): self.d = d
    def _c(self, c): return [(P(x), P(y)) for x, y in c] if isinstance(c[0], tuple) else tuple(P(v) for v in c)
    def line(self, c, **kw): self.d.line(self._c(c), **kw)
    def point(self, c, **kw): self.d.point(self._c(c), **kw)
    def rectangle(self, c, **kw): self.d.rectangle(self._c(c), **kw)
    def ellipse(self, c, **kw): self.d.ellipse(self._c(c), **kw)
CONFIG = {
    "SEED": 11,
    "OUT": "#0d1418",
    "RAMP": {"k": ("#1a232b", "#2b3744", "#45566a"),    # stone floor: shade, mid, light (median lum ~55-75, under the suits' 118-161)
             "s": ("#2d3846", "#687a8a", "#aebfcc"),    # suit steel
             "g": ("#1a4541", "#2e7358", "#7bb565"),    # suit lacquer green (bushes)
             "b": ("#8a5a2b", "#c48c3c", "#f2cb6a"),    # suit bronze (ore, lantern)
             "j": ("#0b211b", "#17382d", "#4f9a6c")},   # deep jade for the bush base
    "ACCENT": {"trace": "#4b6a78", "node": "#7bd0c0", "glow": "#fff3b0", "ember": "#ff925c"},
    "LIGHT_BAND": 2, "SHADE_FRAC": 0.66, "SMALL_REGION": 120, "RIVET_STEP": 4,
    "SHADOW_K": 0.78,       # darker contact shadows than scene_mock (the plates are lit)
    "JITTER": 5,            # plate corner jitter px
    "LAYOUTS": [            # plate layouts per ground variant: list of (x0,y0,x1,y1) in a 96 tile; the renderer jitters the corners
        [(0, 0, 48, 48), (48, 0, 96, 48), (0, 48, 48, 96), (48, 48, 96, 96)],
        [(0, 0, 96, 40), (0, 40, 56, 96), (56, 40, 96, 96)],
        [(0, 0, 96, 96)],
        [(0, 0, 36, 60), (36, 0, 96, 30), (36, 30, 96, 60), (0, 60, 96, 96)],
        [(0, 0, 60, 96), (60, 0, 96, 50), (60, 50, 96, 96)],
    ],
    "DETAIL": ["trace", "none", "crack", "bolt", "node"],   # one detail per ground variant
}
hx = SM.hx


def mask(poly, W, H):
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(poly, fill=1); return np.asarray(m) > 0


def diag_dist(M, sy, sx, kmax=16):
    """steps from the region edge along (sy, sx), like the suit renderer"""
    H, W = M.shape; d = np.zeros((H, W), np.int32); cur = M.copy()
    for k in range(1, kmax + 1):
        sh = np.zeros_like(cur); ys = slice(max(0, sy), H + min(0, sy)); xs = slice(max(0, sx), W + min(0, sx))
        yd = slice(max(0, -sy), H + min(0, -sy)); xd = slice(max(0, -sx), W + min(0, -sx))
        sh[ys, xs] = cur[yd, xd]
        cur = cur & sh; d[cur] = k
        if not cur.any(): break
    return d


def render(parts, W=None, H=None, base=None):
    W = W or S; H = H or S
    """parts: (region, ramp, polygon, flat). Returns RGBA; `base` is an RGBA array to draw over (ground under a bush)."""
    img = np.zeros((H, W, 4), np.uint8) if base is None else base.copy()
    ramp_of = np.full((H, W), "", "<U1"); flat_px = np.zeros((H, W), bool); region_of = np.full((H, W), "", "<U12")
    out = hx(CONFIG["OUT"])[:3]
    for region, ramp, poly, flat in parts:
        M = mask([(P(x), P(y)) for x, y in poly], W, H); sh, mid, lit = (hx(c)[:3] for c in CONFIG["RAMP"][ramp])
        img[M, :3] = mid; img[M, 3] = 255; ramp_of[M] = ramp; flat_px[M] = flat; region_of[M] = region
        if not flat:
            dn = np.zeros_like(M); dn[:-1] = M[1:]; rt = np.zeros_like(M); rt[:, :-1] = M[:, 1:]
            seam = M & (~dn | ~rt); img[seam, :3] = out; flat_px[seam] = True
    for region in sorted(set(region_of[region_of != ""].tolist())):
        Rall = region_of == region; R = Rall & ~flat_px
        dul = diag_dist(Rall, -1, -1); ddr = diag_dist(Rall, 1, 1); t = dul / np.maximum(dul + ddr, 1)
        band = CONFIG["LIGHT_BAND"] if Rall.sum() >= CONFIG["SMALL_REGION"] else 1
        for ramp in CONFIG["RAMP"]:
            sel = R & (ramp_of == ramp); sh, mid, lit = (hx(c)[:3] for c in CONFIG["RAMP"][ramp])
            img[sel & (t > CONFIG["SHADE_FRAC"]), :3] = sh; img[sel & (dul <= band), :3] = lit
    return img, region_of, flat_px


def jit(rnd, x, y):
    j = CONFIG["JITTER"]
    jx = 0 if x in (0, 96) else rnd.randrange(-j, j + 1); jy = 0 if y in (0, 96) else rnd.randrange(-j, j + 1)
    return (x + jx, y + jy)


def ground(variant, seed):
    rnd = random.Random(seed); parts = []
    corners = {}
    def c(x, y):
        if (x, y) not in corners: corners[(x, y)] = jit(rnd, x, y)
        return corners[(x, y)]
    for i, (x0, y0, x1, y1) in enumerate(CONFIG["LAYOUTS"][variant]):
        parts.append((f"p{i}", "k", [c(x0, y0), c(x1, y0), c(x1, y1), c(x0, y1)], False))
    img, reg, flat = render(parts)
    img[img[..., 3] == 0] = hx(CONFIG['OUT'])   # gaps between jittered plates are grooves
    pil = Image.fromarray(img); d = SD(ImageDraw.Draw(pil))
    det = CONFIG["DETAIL"][variant]; A = CONFIG["ACCENT"]; sh = hx(CONFIG["RAMP"]["k"][0]); lit = hx(CONFIG["RAMP"]["k"][2])
    if det == "trace":      # one circuit trace with a node, sunk into a plate
        x, y = rnd.randrange(14, 40), rnd.randrange(14, 70); pts = [(x, y), (x + 16, y), (x + 16, y + 12), (x + 34, y + 12)]
        d.line(pts, fill=hx(A["trace"]), width=1); d.line([(px, py + 1) for px, py in pts], fill=hx(CONFIG["OUT"]), width=1)
        d.rectangle((x + 33, y + 11, x + 35, y + 13), fill=hx(A["node"]))
    elif det == "crack":
        x, y = rnd.randrange(20, 60), rnd.randrange(10, 40); pts = [(x, y)]
        for _ in range(5): pts.append((pts[-1][0] + rnd.randrange(-7, 8), pts[-1][1] + rnd.randrange(4, 10)))
        d.line(pts, fill=hx(CONFIG["OUT"]), width=1); d.line([(px - 1, py) for px, py in pts], fill=lit, width=1)
    elif det == "bolt":     # bolt holes in each plate centre, like the suit joints
        for region in sorted(set(reg[reg != ""].tolist())):
            ys, xs = np.nonzero(reg == region); cy, cx = int(ys.mean()), int(xs.mean())
            for xx in (cx - 4, cx, cx + 4): d.point((xx, cy), fill=hx(CONFIG["OUT"]))
    elif det == "node":     # a glowing node ring
        x, y = rnd.randrange(24, 70), rnd.randrange(24, 70)
        d.ellipse((x - 5, y - 3, x + 5, y + 3), outline=hx(A["trace"])); d.point((x, y), fill=hx(A["node"]))
    img = np.asarray(pil).copy()
    # rivets along the top edge of each plate, every RIVET_STEP px, like the suit plates
    for region in sorted(set(reg[reg != ""].tolist())):
        M = reg == region; dt = diag_dist(M, -1, 0); rows = (dt == 3) & M & ~flat
        ys, xs = np.nonzero(rows)
        for yy, xx in zip(ys, xs):
            if xx % max(2, P(CONFIG["RIVET_STEP"])) == 0: img[yy, xx, :3] = hx(CONFIG["RAMP"]["s"][1])[:3]
    return img


def bush(seed, big=None):
    rnd = random.Random(seed); base = ground(2, seed + 1); parts = []
    big = rnd.random() < 0.5 if big is None else big
    parts.append(("mound", "j", [(14, 90), (24, 62), (48, 54), (72, 62), (82, 90)] if big else [(22, 90), (30, 70), (48, 64), (66, 70), (74, 90)], False))
    for i in range(7 if big else 5):      # leaf blades: tapered polygons leaning away from the centre, lit upper-left like plates
        cx = (20 + i * 9 if big else 28 + i * 10) + rnd.randrange(-3, 4); top = (22 if big else 44) + rnd.randrange(0, 18); lean = (cx - 48) // 6
        parts.append((f"leaf{i}", "g", [(cx - 5, 80), (cx + lean - 1, top), (cx + lean + 1, top), (cx + 6, 80)], False))
    img, _, _ = render(parts, base=base)
    return img


def bush_down(seed):
    """cut bush: the jade mound with short stubs where the blades were"""
    rnd = random.Random(seed); base = ground(2, seed + 1); parts = [("mound", "j", [(22, 90), (30, 72), (48, 66), (66, 72), (74, 90)], False)]
    for i in range(5):
        cx = 28 + i * 10 + rnd.randrange(-3, 4); top = 60 + rnd.randrange(0, 8)
        parts.append((f"stub{i}", "g", [(cx - 4, 76), (cx - 1, top), (cx + 2, top), (cx + 5, 76)], False))
    img, _, _ = render(parts, base=base); return img


def ore_down(seed):
    """depleted ore: the outcrop with the crystals broken to stumps and the glow gone"""
    rnd = random.Random(seed); base = ground(3, seed + 2)
    parts = [("rock", "k", [(20, 92), (28, 70), (50, 64), (74, 72), (80, 92)], False)]
    for i, (cx, w) in enumerate([(40, 8), (54, 10), (66, 7)]):
        parts.append((f"stump{i}", "s", [(cx - w, 84), (cx - w + 3, 74 + rnd.randrange(0, 4)), (cx + w - 3, 76), (cx + w, 84)], False))
    img, _, _ = render(parts, base=base); return img


def ore(seed):
    rnd = random.Random(seed); base = ground(3, seed + 2); parts = []
    parts.append(("rock", "k", [(20, 92), (28, 70), (50, 64), (74, 72), (80, 92)], False))
    for i, (cx, h, w, tilt) in enumerate([(40, 34, 9, -4), (54, 44, 11, 2), (66, 28, 8, 6), (30, 22, 7, -7)]):
        parts.append((f"cry{i}", "b", [(cx - w, 84), (cx + tilt - 2, 84 - h), (cx + tilt + 2, 84 - h - 4), (cx + w, 84)], False))
    img, _, _ = render(parts, base=base)
    pil = Image.fromarray(img); d = SD(ImageDraw.Draw(pil)); A = CONFIG["ACCENT"]
    for cx, h, w, tilt in [(40, 34, 9, -4), (54, 44, 11, 2), (66, 28, 8, 6)]: d.point((cx + tilt, 84 - h - 1), fill=hx(A["glow"]))
    for _ in range(14): d.point((rnd.randrange(14, 84), rnd.randrange(60, 94)), fill=hx(CONFIG["RAMP"]["b"][0]))   # cast amber specks
    return np.asarray(pil).copy()


def prop(kind, seed):
    rnd = random.Random(seed); parts = []
    if kind == "stele":
        parts = [("base", "k", [(24, 94), (28, 82), (68, 82), (72, 94)], False), ("slab", "s", [(34, 86), (36, 28), (44, 18), (52, 26), (58, 20), (62, 30), (60, 86)], False),
                 ("panel", "k", [(41, 40), (41, 74), (55, 74), (55, 40)], False), ("chip", "k", [(36, 28), (44, 18), (46, 24), (40, 30)], False),
                 ("moss", "j", [(30, 86), (36, 78), (46, 82), (52, 86)], False)]
    elif kind == "lantern":
        parts = [("post", "s", [(42, 88), (42, 70), (54, 70), (54, 88)], False), ("box", "k", [(40, 70), (40, 52), (56, 52), (56, 70)], False),
                 ("roof", "s", [(34, 52), (38, 44), (58, 44), (62, 52)], False), ("cap", "s", [(42, 44), (48, 34), (54, 44)], False),
                 ("flame", "b", [(44, 66), (44, 56), (52, 56), (52, 66)], True)]
    else:
        parts.append(("mound", "k", [(14, 92), (26, 68), (50, 60), (74, 68), (84, 92)], False))
        n, lo, hlo = (12, 8, 6) if K == 1.0 else (6, 16, 10)      # at 64 fewer, larger, taller chunks on a loose grid so their edges still read
        for i in range(n):
            if K == 1.0: x, y = 16 + rnd.randrange(0, 56), 54 + rnd.randrange(0, 32)
            else: x, y = 14 + (i % 3) * 22 + rnd.randrange(-3, 4), 56 + (i // 3) * 16 + rnd.randrange(-3, 4)
            w, h = (rnd.randrange(8, 22), rnd.randrange(6, 14)) if K == 1.0 else (rnd.randrange(lo, 24), rnd.randrange(hlo, 15))   # 96 keeps the approved draws
            parts.append((f"r{i}", "s" if i % 3 else "k", [(x, y + h), (x + 2, y), (x + w - 1, y + 1), (x + w, y + h - 1)], False))
    img, _, _ = render(parts)
    if kind == "stele":
        pil = Image.fromarray(img); d = SD(ImageDraw.Draw(pil))
        for yy in range(44, 72, 6): d.line((44, yy, 52, yy), fill=hx(CONFIG["RAMP"]["k"][2]))   # carved rows on the panel
        d.line((37, 86, 38, 32), fill=hx(CONFIG["RAMP"]["s"][2])); d.line((48, 50, 56, 60), fill=hx(CONFIG["OUT"]))   # edge light; a crack
        img = np.asarray(pil).copy()
    if kind == "lantern":
        img[P(59):P(63), P(46):P(50), :3] = hx(CONFIG["ACCENT"]["glow"])[:3]
    return img


def tile_sheet():
    tiles = [("ground0", ground(0, 1)), ("ground1", ground(1, 2)), ("ground2", ground(2, 3)), ("ground3", ground(3, 4)), ("ground4", ground(4, 5)),
             ("bush", bush(7, True)), ("bush_s", bush(8, False)), ("bush_down", bush_down(7)), ("ore", ore(9)), ("ore_down", ore_down(9)), ("stele", prop("stele", 1)), ("lantern", prop("lantern", 1)), ("rubble", prop("rubble", 1))]
    sheet = Image.new("RGBA", (S * len(tiles), S), (0, 0, 0, 0))
    for i, (n, t) in enumerate(tiles): sheet.alpha_composite(Image.fromarray(t), (i * S, 0))
    return tiles, sheet


def scene(tiles):
    d = dict(tiles); cfg = SM.CONFIG; cols, rows = cfg["COLS"], cfg["ROWS"]; rnd = random.Random(CONFIG["SEED"])
    sc = np.zeros((rows * S, cols * S, 4), np.uint8); last = {}; cfg["SHADOW"]["k"] = CONFIG["SHADOW_K"]
    for r in range(rows):
        for c in range(cols):
            t = cfg["LAYOUT"][r][c]
            if t == "g":
                v = rnd.randrange(5)
                while v == last.get((c - 1, r)) or v == last.get((c, r - 1)): v = rnd.randrange(5)
                last[(c, r)] = v; tile = ground(v, 100 + r * 31 + c * 7)
            else: tile = bush(100 + r * 31 + c * 7) if t == "b" else ore(100 + r * 31 + c * 7)
            sc[r * S:(r + 1) * S, c * S:(c + 1) * S] = tile
    for r in range(rows):
        for c in range(cols):
            t = cfg["LAYOUT"][r][c]
            if t == "b": SM.shadow(sc, c * S + 48, r * S + 84, *cfg["SHADOW"]["bush"])
            if t == "o": SM.shadow(sc, c * S + 50, r * S + 86, *cfg["SHADOW"]["ore"])
    for kind, (c, r) in cfg["PROPS"].items():
        SM.shadow(sc, c * S + 48, r * S + 88, 26, 7); SM.paste(sc, d[kind], c * S, r * S)
    pc, pr = cfg["PLAYER"]; SM.ring(sc, pc * S + 48, pr * S + 90)
    for (c, r), fn in cfg["SUITS"].items():
        img = np.asarray(Image.open(os.path.join(SM.APPROVED, fn)).convert("RGBA")); ys, xs = np.nonzero(img[..., 3])
        SM.shadow(sc, c * S + (xs.min() + xs.max()) / 2, r * S + ys.max(), *cfg["SHADOW"]["suit"])
    for (c, r), fn in cfg["SUITS"].items():
        SM.paste(sc, np.asarray(Image.open(os.path.join(SM.APPROVED, fn)).convert("RGBA")), c * S, r * S)
    for r in range(rows):
        for c in range(cols):
            dch = max(abs(c - pc), abs(r - pr)); step = next(s for lim, s in cfg["VISION"] if dch <= lim)
            if step: m = np.zeros(sc.shape[:2], bool); m[r * S:(r + 1) * S, c * S:(c + 1) * S] = True; SM.darken(sc, m, step)
    for i, ((c, r), fn) in enumerate(cfg["SUITS"].items()): SM.hud_bar(sc, c * S + 48, r * S + 2, [1.0, 0.8, 0.3, 0.6, 1.0, 0.5][i])
    return sc


def checks(tiles, sc):
    fails = []
    for n, t in tiles:
        al = t[..., 3]
        if ((al > 0) & (al < 255)).any(): fails.append(f"{n}: semi-transparent pixels")
        if n.startswith(("ground", "bush", "ore")) and (al != 255).any(): fails.append(f"{n}: not fully opaque")
        cols = len(np.unique(t[al > 0][:, :3], axis=0))
        on = al > 0; iso = 0
        if on.sum():
            rgb = t[..., :3]; same = np.zeros_like(on)
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                sh = np.roll(np.roll(rgb, dy, 0), dx, 1); same |= (sh == rgb).all(2)
            iso = round(float((on & ~same).sum() / on.sum() * 100), 1)
        print(f"{n}: colours {cols}, isolated {iso}%")
        if cols > 16: fails.append(f"{n}: {cols} colours > 16")
    if (sc[..., 3] != 255).any(): fails.append("scene: not fully opaque")
    return fails


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    size = os.environ.get("SIZE", "96"); S = int(size); K = S / 96.0; CONFIG["LIGHT_BAND"] = 2 if S == 96 else 1; tag = "" if S == 96 else "64"
    tiles, sheet = tile_sheet(); sheet.save(f"out/suitstyle{tag}_tiles_1x.png")
    bg = Image.new("RGBA", sheet.size, (58, 62, 72, 255)); bg.alpha_composite(sheet); bg.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(f"out/suitstyle{tag}_tiles_3x.png")
    if S == 96:
        sc = scene(tiles); Image.fromarray(sc).save("out/scene_suitstyle_1x.png")
        Image.fromarray(sc).resize((sc.shape[1] * 2, sc.shape[0] * 2), Image.NEAREST).save("out/scene_suitstyle_2x.png")
    else:
        sc = np.zeros((S, S, 4), np.uint8); sc[:] = 255
    f = checks(tiles, sc); print("PASS" if not f else "FAILING:\n" + "\n".join(f))
