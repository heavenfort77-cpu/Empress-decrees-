"""Suit Mythology ground tiles at 96x96 or 64x64 (python3 tiles96.py 96|64) (desktop, primary). Drawn natively, never resized. Seeded; every tunable is in CONFIG.
Run: python3 tiles96.py  -> out/tiles96_sheet_1x.png, out/tiles96_sheet_3x.png, out/tiles96_context_2x.png ; prints pass/fail checks only.
Terrain tiles are fully opaque; wreck and storm are overlays with alpha 0 or 255 only (no semi-transparent pixels)."""
import math, random, sys
import numpy as np
from PIL import Image, ImageDraw
SIZE = sys.argv[1] if len(sys.argv) > 1 else '96'
S = int(SIZE)
K = S / 96.0   # geometry is plotted natively at S, never resized
def k(v): return v * K
def ki(v): return max(1, round(v * K))
CONFIG = {
    "SEED": 7,
    "OUT": "#0d1418",
    "GROUND": ["#171d23", "#212a32", "#2e3944", "#3d4c5a"],       # dark, base, light, highlight (light from upper left)
    "TRACE": "#4b6a78", "NODE": "#7bd0c0",
    "JADE": ["#0b211b", "#17382d", "#2a6150", "#4f9a6c", "#9ad47a"],  # bush ramp, dark to tip
    "AMBER": ["#5c3a18", "#8a5a2b", "#c48c3c", "#f2cb6a", "#fff3b0"], # ore ramp
    "STEEL": ["#222c37", "#445468", "#687a8a", "#aebfcc"], "RUST": "#c8432c",
    "STORM": ["#2a1040", "#5a2a8a", "#a15fd6"],
    "PLATE": 32,            # ground plate size; seams every PLATE px, plus the tile border
    "SPECKLE": 70 * (int(sys.argv[1]) / 96.0) ** 2 if len(sys.argv) > 1 else 70,          # speckle clusters per ground tile
    "BLADES": 16, "STUMPS": 6, "CRYSTALS": 4,
    "LIMITS": {"colours": (6, 18)},
}
def hx(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
C = CONFIG

def ground(seed, trace=True):
    rnd = random.Random(seed); a = np.zeros((S, S, 4), np.uint8); a[:] = hx(C["GROUND"][1])
    P = C["PLATE"]
    for y in range(S):                      # plates: light top/left edge row, dark seam bottom/right (tile border is a seam, so tiles abut cleanly)
        for x in range(S):
            if x % P == P - 1 or y % P == P - 1: a[y, x] = hx(C["OUT"])
            elif x % P == 0 or y % P == 0: a[y, x] = hx(C["GROUND"][2])
            elif x % P == P - 2 or y % P == P - 2: a[y, x] = hx(C["GROUND"][0])
    for _ in range(int(C["SPECKLE"])):           # speckle: 1 px and 2x1 marks, light or dark, inside plates only
        x, y = rnd.randrange(2, S - 3), rnd.randrange(2, S - 3)
        if x % P in (0, P - 2, P - 1) or y % P in (0, P - 2, P - 1): continue
        col = hx(rnd.choice([C["GROUND"][0], C["GROUND"][2], C["GROUND"][2], C["GROUND"][3]]))
        a[y, x] = col
        if rnd.random() < 0.4 and x % P < P - 3: a[y, x + 1] = col
    if trace:                               # circuit traces: orthogonal runs with a node at the end
        for _ in range(2):
            x, y = rnd.randrange(ki(6), S - ki(6)), rnd.randrange(ki(6), S - ki(6)); d = rnd.choice([(1, 0), (0, 1)])
            for _s in range(rnd.randrange(3, 6)):
                for _k in range(ki(rnd.randrange(6, 14))):
                    x += d[0]; y += d[1]
                    if not (2 <= x < S - 3 and 2 <= y < S - 3): break
                    if x % P in (P - 1, 0) or y % P in (P - 1, 0): continue
                    a[y, x] = hx(C["TRACE"])
                d = (d[1], d[0]) if rnd.random() < 0.5 else (-d[1], -d[0])
            if 2 <= x < S - 3 and 2 <= y < S - 3: a[y, x] = hx(C["NODE"])
    return a

def outline_mask(m):                         # m bool; returns edge bool (inside pixels touching outside)
    e = np.zeros_like(m)
    e[1:-1, 1:-1] = m[1:-1, 1:-1] & ~(m[:-2, 1:-1] & m[2:, 1:-1] & m[1:-1, :-2] & m[1:-1, 2:])
    return e
def paint(a, m, shade, outline=True):        # shade(x,y)->hex ; draws mask with 1 px dark outline
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs): a[y, x] = hx(shade(x, y))
    if outline:
        for y, x in zip(*np.nonzero(outline_mask(m))): a[y, x] = hx(C["OUT"])

def poly_mask(pts):
    im = Image.new("L", (S, S), 0); ImageDraw.Draw(im).polygon([(round(x * K), round(y * K)) for x, y in pts], fill=1); return np.asarray(im) > 0

def bush(seed):
    a = ground(seed, trace=False); rnd = random.Random(seed + 1); J = C["JADE"]
    blades = []
    for i in range(C["BLADES"]):
        bx = 14 + (i * 68 / (C["BLADES"] - 1)) + rnd.uniform(-3, 3); by = rnd.randrange(78, 90)  # 96-space
        h = rnd.randrange(30, 62) if 3 < i < C["BLADES"] - 4 else rnd.randrange(22, 44)
        lean = rnd.uniform(-9, 9); w = rnd.choice([4, 5, 5, 6]); w = w if S == 96 else rnd.choice([6, 7, 7, 8]); blades.append((by, bx, h, lean, w))
    for by, bx, h, lean, w in sorted(blades):
        tipx, tipy = bx + lean, by - h; bxs, bys, txs, tys, ws = k(bx), k(by), k(tipx), k(tipy), (w if S == 96 else w); mid = (bx + lean * 0.35, by - h * 0.55)
        pts = [(bx - w / 2, by), (mid[0] - w * 0.55, mid[1]), (tipx, tipy), (mid[0] + w * 0.55, mid[1]), (bx + w / 2, by)]
        m = poly_mask(pts)
        def shade(x, y, bx=bxs, tipx=txs, tipy=tys, by=bys, w=ws):
            u = (x - (bx + (tipx - bx) * (by - y) / max(1, by - tipy))) / max(1.0, w / 2)  # -1 left .. +1 right
            if y < tipy + ki(4): return J[4]
            if y < tipy + ki(9): return J[3]
            return J[3] if u < -0.35 else J[2] if u < 0.25 else J[1]
        paint(a, m, shade)
    for _ in range(10):                      # roots/shadow pixels at the base
        x, y = rnd.randrange(ki(8), ki(88)), rnd.randrange(ki(86), ki(93))
        a[y, x] = hx(J[0])
    return a

def bush_down(seed):
    a = ground(seed, trace=True); rnd = random.Random(seed + 2); J = C["JADE"]
    for i in range(C["STUMPS"]):
        bx = 16 + i * 13 + rnd.randrange(-3, 4); by = rnd.randrange(70, 88); h = rnd.randrange(6, 12); w = rnd.choice([5, 6])
        m = poly_mask([(bx - w / 2, by), (bx - w / 2 + 1, by - h), (bx + w / 2 - 1, by - h - rnd.randrange(0, 3)), (bx + w / 2, by)])
        paint(a, m, lambda x, y, bx=k(bx), by=k(by), h=k(h): J[3] if y < by - h + ki(2) else J[2] if x < bx else J[1])
    for _ in range(9):                       # cut leaf scraps: 3x1 and 2x1 flecks
        x, y = rnd.randrange(ki(8), ki(84)), rnd.randrange(ki(60), ki(92)); L = rnd.choice([2, 3]); col = hx(rnd.choice([J[1], J[2]]))
        for q in range(L): a[y, x + q] = col
    return a

def crystal(a, cx, by, h, w, tilt):
    A = C["AMBER"]; tx = cx + tilt; cxs, bys, hs, ws, ts = k(cx), k(by), k(h), k(w), k(tilt)
    pts = [(cx - w / 2, by), (cx - w / 2 + tilt * 0.3, by - h * 0.7), (tx, by - h), (cx + w / 2 + tilt * 0.3, by - h * 0.7), (cx + w / 2, by)]
    m = poly_mask(pts)
    def shade(x, y):
        u = (x - cxs - ts * (bys - y) / hs * 0.8) / (ws / 2)
        if y < bys - hs + ki(5) and u > -0.4: return A[4]
        if u < -0.45: return A[3]
        if u < 0.15: return A[2]
        if u < 0.6: return A[1]
        return A[0]
    paint(a, m, shade)
def ore(seed):
    a = ground(seed, trace=False); rnd = random.Random(seed + 3); A = C["AMBER"]
    cx, cy = k(48), k(70)
    for y in range(S):                       # opaque glow: dither of dark amber on the ground, denser near the cluster
        for x in range(S):
            d = math.hypot((x - cx) / 1.6, y - cy) / K
            if d < 30 and ((x + y) % 2 == 0 or (x % 2 == 0 and y % 2 == 0 and d < 18)) and tuple(a[y, x][:3]) != hx(C["OUT"])[:3]:
                if d < 13: a[y, x] = hx(A[0]) if (x + y) % 2 == 0 else a[y, x]
                elif d < 22 and (x + y) % 4 == 0: a[y, x] = hx(A[0])
                elif d < 30 and (x % 4 == 0 and y % 4 == 0): a[y, x] = hx(A[0])
    for cxx, by, h, w, t in [(30, 82, 22, 9, -3), (66, 83, 26, 10, 3), (40, 86, 36, 13, -2), (56, 87, 44, 15, 2), (48, 90, 30, 12, 0)][:C["CRYSTALS"] + 1]:
        crystal(a, cxx, by, h, w, t)
    for _ in range(10):                      # sparks
        x, y = rnd.randrange(ki(14), ki(82)), rnd.randrange(ki(18), ki(60)); a[y, x] = hx(A[3] if rnd.random() < 0.6 else A[4])
    return a
def ore_down(seed):
    a = ground(seed, trace=True); rnd = random.Random(seed + 4); A = C["AMBER"]; G = C["GROUND"]
    m = poly_mask([(22, 74), (34, 62), (62, 60), (76, 72), (66, 84), (34, 85)])
    paint(a, m, lambda x, y: G[0] if (x + y) % 5 else hx(C["OUT"]) and C["OUT"])
    for _ in range(24):                      # rubble
        x, y = rnd.randrange(ki(20), ki(78)), rnd.randrange(ki(58), ki(88)); a[y, x] = hx(rnd.choice([A[0], A[0], G[2], G[0]]))
    for x, y in [(44, 72), (45, 72), (50, 74)]: a[ki(y), ki(x)] = hx(A[1])   # last embers
    a[ki(73), ki(45)] = hx(A[2])
    for dx in range(0, 22, 3): a[ki(64 + dx // 3 * 2), ki(30 + dx)] = hx(C["OUT"])  # crack
    return a

def wreck():
    a = np.zeros((S, S, 4), np.uint8); St = C["STEEL"]; rnd = random.Random(C["SEED"] + 9)
    parts = [([(24, 86), (22, 70), (34, 60), (58, 58), (72, 68), (74, 86)], "torso"), ([(10, 88), (14, 80), (34, 78), (36, 88)], "limb"),
             ([(70, 88), (74, 82), (88, 80), (90, 88)], "limb"), ([(36, 62), (40, 48), (52, 46), (56, 60)], "head")]
    for pts, kind in parts:
        m = poly_mask(pts)
        paint(a, m, lambda x, y: St[3] if (y < k(64) and x < k(48)) else St[2] if x < k(56) else St[1] if y < k(80) else St[0])
        for yy in range(S):
            for xx in range(S):
                if m[yy, xx] and (xx * 3 + yy * 5) % (17 if S == 96 else 23) == 0 and kind == "torso": a[yy, xx] = hx(St[0])
    for x in range(ki(40), ki(58)): a[ki(70) + (x % 3 if S == 96 else x % 2), x] = hx(C["OUT"])   # split seam
    for x, y in [(46, 52), (47, 52)]: a[ki(y), ki(x)] = hx(C["RUST"])      # dead visor
    a[ki(66), ki(30)] = hx(C["RUST"]); a[ki(75), ki(62)] = hx(C["RUST"]); a[ki(84), ki(20)] = hx(C["RUST"])
    return a

def storm():
    a = np.zeros((S, S, 4), np.uint8); B = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]
    for y in range(S):
        for x in range(S):
            v = B[y % 4][x % 4]
            if v < 5: a[y, x] = hx(C["STORM"][1])
            if v == 0 and (x // 4 + y // 4) % 3 == 0: a[y, x] = hx(C["STORM"][2])
    return a

def sheet(tiles):
    sh = Image.new("RGBA", (S * len(tiles), S), (20, 17, 15, 255))
    for i, (n, t) in enumerate(tiles): sh.alpha_composite(Image.fromarray(t), (i * S, 0))
    return sh

def checks(tiles):
    fails = []
    for n, t in tiles:
        al = t[..., 3]; semi = int(((al > 0) & (al < 255)).sum())
        if semi: fails.append(f"{n}: {semi} semi-transparent px")
        if n not in ("wreck", "storm") and (al < 255).any(): fails.append(f"{n}: terrain not opaque")
        px = t[al == 255][:, :3]; cols = len({tuple(p) for p in px}); lo, hi = C["LIMITS"]["colours"]
        iso = 0; m = (al == 255)
        for y in range(1, S - 1):
            for x in range(1, S - 1):
                if m[y, x] and not any(np.array_equal(t[y + dy, x + dx][:3], t[y, x][:3]) for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1))): iso += 1
        print(f"  {n:9s} colours {cols:2d}  isolated {100 * iso / max(1, m.sum()):4.1f}%")
        if n != "storm" and not lo <= cols <= hi: fails.append(f"{n}: colours {cols} outside {lo}-{hi}")
    return fails

if __name__ == "__main__":
    T = [("ground_a", ground(11)), ("ground_b", ground(23)), ("ground_c", ground(37)), ("bush", bush(5)), ("bush_down", bush_down(5)),
         ("ore", ore(5)), ("ore_down", ore_down(5)), ("wreck", wreck()), ("storm", storm())]
    f = checks(T)
    # tiles must abut: the right/bottom border column/row is the seam colour on every terrain tile
    for n, t in T:
        if n in ("wreck", "storm"): continue
        if not (all(tuple(t[y, S - 1][:3]) == hx(C["OUT"])[:3] for y in range(S)) and all(tuple(t[S - 1, x][:3]) == hx(C["OUT"])[:3] for x in range(S))): f.append(f"{n}: border seam broken")
    sh = sheet(T); sh.save(f"out/tiles{SIZE}_sheet_1x.png"); sh.resize((sh.width * 3, sh.height * 3), Image.NEAREST).save(f"out/tiles{SIZE}_sheet_3x.png")
    # context: a 7x4 patch of mixed ground with approved suits standing on it (readability check)
    A = "../approved/"; ctx = Image.new("RGBA", (S * 7, S * 4), (0, 0, 0, 255)); rnd = random.Random(3)
    layout = [["ground_a", "ground_b", "bush", "bush", "ground_c", "ore", "ground_a"], ["ground_c", "bush", "bush", "ground_b", "ground_a", "ground_b", "ore_down"],
              ["ground_b", "ground_a", "ground_c", "wreck", "ground_b", "bush_down", "ground_c"], ["ore", "ground_c", "ground_a", "ground_b", "bush", "bush", "ground_a"]]
    d = dict(T)
    for r, row in enumerate(layout):
        for c, n in enumerate(row):
            base = d["ground_a"] if n == "wreck" else d[n]; ctx.alpha_composite(Image.fromarray(base), (c * S, r * S))
            if n == "wreck": ctx.alpha_composite(Image.fromarray(d["wreck"]), (c * S, r * S))
    P = {"96": ["tianbing96/views_idle_front_1x.png", "gushi/gs_idle_left_1x.png", "yuanmo/ym2_idle_right_1x.png", "wushi/ws_idle_front_1x.png", "jianxian/jx_idle_back_1x.png"],
         "64": ["tianbing64/v64_idle_front_1x.png", "gushi/gs64_idle_left_1x.png", "tianlong/tl64_idle_right_1x.png", "wushi/ws64_idle_front_1x.png", "jianxian/jx64_idle_back_1x.png"]}[SIZE]
    for (c, r), p in zip([(1, 0), (4, 1), (5, 2), (3, 3), (0, 1)], [A + q for q in P]):
        ctx.alpha_composite(Image.open(p).convert("RGBA"), (c * S, r * S))
    st = Image.fromarray(d["storm"])
    for c in range(5, 7): 
        for r in range(0, 2): ctx.alpha_composite(st, (c * S, r * S)) if (c, r) != (5, 0) else None
    ctx.resize((ctx.width * 2, ctx.height * 2), Image.NEAREST).save(f"out/tiles{SIZE}_context_2x.png")
    print("PASS" if not f else "FAIL\n" + "\n".join(f))
