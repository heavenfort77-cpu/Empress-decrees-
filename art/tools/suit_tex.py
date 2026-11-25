#!/usr/bin/env python3
"""Suit trim sheets for the nine school suits, painted in klad (study: art/Qin-Lamellar-Suits-Study.md). This script only places
seeded marks as klad stroke ops; klad paints them (suit_paint.py). All ornament is our own drawing; nothing is traced.

Research rules (docs/research/Qin-palace-medieval-tech-fusion.md): small hard plates tied with a binding whose colour marks the school;
lacquer over a dark ground in the excavated mineral palette (bone black, cinnabar, lead white, ochre, malachite, azurite, Han purple),
gold and silver inlay as lines; no samurai lacing, no sci-fi panel lines, no neon. Light is painted from the upper left (albedo with
form painted in, as the palace sheets).

Sheets (256 px/m everywhere; every row wraps across x):
suit_lamellar 1024 x 1024 = 4 x 4 m. Rows (px):
  0-152 plate_black (Qin black lacquer)   152-304 plate_brown (lacquer on the brown ground)   304-408 plate_cinnabar   408-512 plate_white
  512-544 lam_black   544-576 lam_brown   576-608 lam_cinnabar   608-640 lam_white   (one row of lamellae, 8 cm plates, 12.5 cm tall)
  640-672 rim (cinnabar edge line on black)   672-704 gold inlay band   704-736 silver inlay band
  736-1024 nine cord rows, 32 px each, in school order fa ru dao mo yy za ming zh nong (twisted cord in the school's binding colour)
suit_bronze 512 x 512 = 2 x 2 m: 0-192 plain fresh bronze, 192-224 gold inlay, 224-256 silver inlay, 256-320 blade (bright edges, ridge),
  320-352 rivet row, 352-416 dark bronze (gauntlets), 416-512 mask (face plates)
suit_cloth 512 x 512 = 2 x 2 m: light neutral silk and hemp (tinted per school in the material), weave and vertical folds.
Usage: python3 suit_tex.py OUTDIR   (writes <name>.jsonl / .passes.json / .bg / .size for suit_paint.py)
"""
import json, math, random, sys

OUT = sys.argv[1]

# CONFIG -----------------------------------------------------------------------------------------------------------------
# Lacquer ramps (deep, shadow, base, light, polish highlight) per lacquer colour.
LAC = {'black': ('#120f0f', '#1d1918', '#2a2524', '#3e3533', '#5e504a'), 'brown': ('#22140d', '#331f15', '#45291b', '#5e3a26', '#80583a'),
       'cinnabar': ('#5a1d13', '#7e2a1c', '#a33a28', '#bd4e34', '#d6765a'), 'white': ('#8c8577', '#b3ab9b', '#d2cab9', '#e2dccd', '#f1ece0')}
# School binding colours (cord rows in this order).
# owner 25 Nov: the ONE school colour mapping (W1a 鼎 pigments; 儒 #94622c and 杂 #b2bccb as on the banners and effects); was the study palette.
CORDS = [('fa', '#d9d2c3'), ('ru', '#94622c'), ('dao', '#e2b84a'), ('mo', '#a8321e'), ('yy', '#1a1614'), ('za', '#b2bccb'), ('ming', '#5b3f8c'), ('zh', '#2f8a5c'), ('nong', '#2e5a9c')]
# Bronze ramp for suit fittings (fresh, live pieces: no patina) and inlay metals.
BR = ('#3a2b1a', '#5e482b', '#8a6a3c', '#a88a52', '#c8a86a')
GOLD, GOLD_D, SILVER, SILVER_D = '#d4b25a', '#9c7c34', '#c8ccd0', '#8e9396'
# Cloth: light neutral ground so the material tint sets the school colour (final = tint x texture).
CLOTH = ('#bdb7ac', '#d4cfc5', '#e6e2da', '#f2efe9')


class Tex:
    def __init__(s, name, size, bg, seed, wx=True, wy=False):
        s.name, s.S, s.bg, s.wx, s.wy = name, size, bg, wx, wy
        s.r = random.Random(seed); s.ops = []; s.stage = 0

    def stroke(s, pts, brush, size, color, opacity=1.0, taper=None, wrap=True):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]; S = s.S
        ox = [0]; oy = [0]
        if s.wx and wrap:
            if min(xs) - size < 0: ox.append(S)
            if max(xs) + size > S: ox.append(-S)
        if s.wy and wrap:
            if min(ys) - size < 0: oy.append(S)
            if max(ys) + size > S: oy.append(-S)
        seed = s.r.randrange(1, 1 << 30)
        for a in ox:
            for b in oy:
                d = 'M' + ' L'.join(f'{x + a:.1f} {y + b:.1f}' for x, y in pts)
                op = {"op": "stroke", "layer": "l1", "brush": brush, "size": round(size, 2), "color": color, "opacity": opacity, "path": d, "seed": seed}
                if taper is not None: op["taper"] = taper
                s.ops.append((s.stage, op))

    def wob(s, x0, y0, x1, y1, n=6, amp=3):
        return [(x0 + (x1 - x0) * i / n + s.r.uniform(-amp, amp), y0 + (y1 - y0) * i / n + s.r.uniform(-amp, amp)) for i in range(n + 1)]

    def band(s, y0, y1, color, brush='flat-bristle', size=None, op=1.0, jitter=2):
        """solid marker under-pass, then overlapping horizontal brush strokes across the full width (start at random x, wrap)."""
        size = size or min(40, max(8, (y1 - y0) * 0.7))
        y = y0 + 3
        while y <= y1 + 1:
            x0 = s.r.uniform(0, s.S); s.stroke([(x0, y), (x0 + s.S * 1.08, y)], 'marker', 8, color, 1.0, taper=[0, 0]); y += 5
        y = y0 + size / 2 - 2
        while y <= y1 - size / 2 + 3:
            x0 = s.r.uniform(0, s.S); s.stroke(s.wob(x0, y, x0 + s.S * 1.08, y, 8, jitter), brush, size, color, op, taper=[0, 0]); y += size * 0.55

    def write(s):
        s.ops.sort(key=lambda o: o[0])   # stable: paint order kept inside a stage; rows never overlap, so stages can be grouped
        with open(f'{OUT}/{s.name}.jsonl', 'w') as f:
            for st, op in s.ops: f.write(json.dumps(op) + '\n')
        cuts, names = [], ['base', 'tone', 'marks', 'detail']
        for i, (st, op) in enumerate(s.ops):
            if i + 1 == len(s.ops) or s.ops[i + 1][0] != st: cuts.append([names[st], i + 1])
        json.dump(cuts, open(f'{OUT}/{s.name}.passes.json', 'w'))
        open(f'{OUT}/{s.name}.bg', 'w').write(s.bg); open(f'{OUT}/{s.name}.size', 'w').write(str(s.S))
        return len(s.ops)


def cloud(t, cx, cy, sz, color, w=5):
    """cloud scroll (our own): an S-curve with two curls."""
    pts = [(cx - sz + 2 * sz * a, cy + math.sin(a * math.pi * 2) * sz * 0.3) for a in [i / 20 for i in range(21)]]
    t.stroke(pts, 'ink', w, color, 0.95, taper=[3, 3])
    for e, d in ((-1, 1), (1, -1)):
        ex = cx + e * sz
        t.stroke([(ex + math.cos(a) * sz * 0.26 * (1 - a / 9) * d, cy - sz * 0.26 * d + math.sin(a) * sz * 0.26 * (1 - a / 9)) for a in [k * 0.5 for k in range(14)]],
                 'ink', w * 0.8, color, 0.95, taper=[1, 6])


def plate_field(t, y0, y1, ramp, k=1.0):
    """lacquer plate ground: smooth coats with soft mottled depth (short sponge blots, no long streaks: round 1 read as wood grain),
    sheen patches from the upper left, polish wipes and a few nicks. k scales the tone opacity (pale lacquer shows marks more)."""
    deep, sh, base, li, hi = ramp; r = t.r
    t.stage = 0; t.band(y0, y1, base, brush='marker', size=8)
    t.stage = 1
    for _ in range(int((y1 - y0) * 2.2)):
        x, y = r.uniform(0, t.S), r.uniform(y0 + 8, y1 - 8); L = r.uniform(6, 22); a = r.uniform(0, math.pi)
        t.stroke(t.wob(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 2, 1.5), 'sponge', r.uniform(10, 24), r.choice([sh, li, sh, deep]), r.uniform(0.3, 0.55) * k)
    t.stage = 2
    for _ in range(int((y1 - y0) * 0.25)):   # polish wipes: short light arcs (lacquer sheen)
        x, y = r.uniform(0, t.S), r.uniform(y0 + 6, y1 - 10); L = r.uniform(14, 40)
        t.stroke([(x, y), (x + L * 0.5, y - 3), (x + L, y)], 'chalk', r.uniform(3, 6), hi, r.uniform(0.25, 0.45))
    t.stage = 3
    for _ in range(int((y1 - y0) * 0.35)):   # pits and nicks
        x, y = r.uniform(0, t.S), r.uniform(y0 + 4, y1 - 4)
        t.stroke([(x, y), (x + r.uniform(1, 5), y + r.uniform(-1, 1))], 'ink', r.uniform(2, 4), r.choice([deep, hi]), r.uniform(0.4, 0.7), taper=[0, 0])


def lam_row(t, y0, ramp):
    """one row of lamellae: 8 cm plates (20 px) overlapping to the right, rounded top corners, two tie holes, lower edge in shadow."""
    deep, sh, base, li, hi = ramp; r = t.r; y1 = y0 + 32
    t.stage = 0; t.band(y0, y1, sh, brush='marker', size=8)
    t.stage = 2
    for i in range(t.S // 20 + 1):
        x = i * 20 + r.uniform(-1, 1)
        t.stroke([(x + 3, y1 - 3), (x + 3, y0 + 6), (x + 6, y0 + 3), (x + 18, y0 + 3), (x + 21, y0 + 6), (x + 21, y1 - 3)], 'marker', 8, base, 1.0, taper=[0, 0])
        t.stroke([(x + 8, y0 + 8), (x + 9, y1 - 8)], 'marker', 6, base, 1.0, taper=[0, 0])
        t.stroke([(x + 16, y0 + 8), (x + 16, y1 - 8)], 'marker', 6, base, 1.0, taper=[0, 0])
        t.stroke([(x + 5, y0 + 6), (x + 17, y0 + 5)], 'chalk', 3, hi, 0.6, taper=[1, 1])          # lit upper edge
        t.stroke([(x + 4, y0 + 6), (x + 4, y1 - 4)], 'ink', 2.5, li, 0.7, taper=[0, 0])            # lit left edge
        t.stroke([(x + 21, y0 + 6), (x + 21, y1 - 3)], 'ink', 3, deep, 0.9, taper=[0, 0])          # overlap shadow on the right
        for hx in (x + 9, x + 15): t.stroke([(hx, y0 + 9), (hx + 1, y0 + 9)], 'ink', 3, deep, 0.95, taper=[0, 0])  # tie holes
    t.stage = 3
    x0 = r.uniform(0, t.S); t.stroke([(x0, y1 - 2), (x0 + t.S * 1.05, y1 - 2)], 'marker', 4, deep, 1.0, taper=[0, 0])


def cord_row(t, y0, col):
    """a twisted cord in the binding colour: diagonal twists with light and shadow sides, dark gaps above and below."""
    c = col.lstrip('#'); rgb = [int(c[i:i + 2], 16) for i in (0, 2, 4)]
    hexs = lambda k: '#%02x%02x%02x' % tuple(int(max(0, min(255, v * k))) for v in rgb)
    dark, light = hexs(0.55), hexs(1.25) if sum(rgb) < 600 else hexs(1.05)
    y1 = y0 + 32; t.stage = 0; t.band(y0, y1, hexs(0.4), brush='marker', size=8)
    t.stage = 1; t.band(y0 + 7, y1 - 7, col, brush='marker', size=8)
    t.stage = 2
    for i in range(t.S // 8 + 1):
        x = i * 8
        t.stroke([(x, y1 - 8), (x + 8, y0 + 8)], 'ink', 2.5, dark, 0.85, taper=[0, 0])
        t.stroke([(x + 2, y1 - 10), (x + 7, y0 + 10)], 'ink', 2, light, 0.6, taper=[0, 0])


def lamellar():
    t = Tex('suit_lamellar', 1024, '#1d1918', 901)
    for (y0, y1), k in (((0, 152), 'black'), ((152, 304), 'brown'), ((304, 408), 'cinnabar'), ((408, 512), 'white')): plate_field(t, y0, y1, LAC[k], {'white': 0.55, 'brown': 1.45}.get(k, 1.0))
    for y0, k in ((512, 'black'), (544, 'brown'), (576, 'cinnabar'), (608, 'white')): lam_row(t, y0, LAC[k])
    # rim: black lacquer with a cinnabar edge line and small cloud scrolls (Qin lacquerware)
    t.stage = 0; t.band(640, 672, LAC['black'][2], brush='marker', size=8)
    t.stage = 2
    x0 = t.r.uniform(0, 1024); t.stroke([(x0, 646), (x0 + 1100, 646)], 'marker', 4, LAC['cinnabar'][2], 1.0, taper=[0, 0])
    t.stroke([(x0, 667), (x0 + 1100, 667)], 'marker', 3, LAC['cinnabar'][2], 1.0, taper=[0, 0])
    for i in range(16): cloud(t, 32 + i * 64, 657, 18, LAC['cinnabar'][3], 3)
    # gold and silver inlay bands: dark bronze ground, inlaid lines and lozenges, polished flush
    for y0, (m, md) in ((672, (GOLD, GOLD_D)), (704, (SILVER, SILVER_D))):
        t.stage = 0; t.band(y0, y0 + 32, BR[0], brush='marker', size=8)
        t.stage = 2
        x0 = t.r.uniform(0, 1024)
        t.stroke([(x0, y0 + 6), (x0 + 1100, y0 + 6)], 'marker', 3, m, 1.0, taper=[0, 0]); t.stroke([(x0, y0 + 26), (x0 + 1100, y0 + 26)], 'marker', 3, m, 1.0, taper=[0, 0])
        for i in range(32):
            cx = 16 + i * 32
            t.stroke([(cx - 11, y0 + 16), (cx, y0 + 10), (cx + 11, y0 + 16), (cx, y0 + 22), (cx - 11, y0 + 16)], 'ink', 3, m, 0.95, taper=[0, 0])
            t.stroke([(cx - 2, y0 + 16), (cx + 2, y0 + 16)], 'ink', 3, md, 0.95, taper=[0, 0])
    for i, (sid, col) in enumerate(CORDS): cord_row(t, 736 + 32 * i, col)
    return t


def bronze():
    t = Tex('suit_bronze', 512, BR[2], 902); r = t.r
    deep, sh, base, li, hi = BR
    t.stage = 0; t.band(0, 192, base, size=30)
    for y0, y1, c in ((192, 224, deep), (224, 256, deep), (256, 320, li), (320, 352, base), (352, 416, sh), (416, 512, base)): t.band(y0, y1, c, brush='marker', size=8)
    t.stage = 1
    for _ in range(120):   # sand-cast mottling on the plain plate
        x, y = r.uniform(0, 512), r.uniform(8, 184); L = r.uniform(10, 30)
        t.stroke(t.wob(x, y, x + L, y + r.uniform(-6, 6), 3, 2), 'sponge', r.uniform(20, 34), r.choice([li, sh, '#6e522e', '#a2824e']), r.uniform(0.35, 0.5))
    for _ in range(50):
        x, y = r.uniform(0, 512), r.uniform(420, 508); L = r.uniform(10, 30)
        t.stroke(t.wob(x, y, x + L, y, 3, 2), 'sponge', r.uniform(10, 20), r.choice([li, sh]), r.uniform(0.25, 0.4))
    t.stage = 2
    for y0, m in ((192, GOLD), (224, SILVER)):
        x0 = r.uniform(0, 512); t.stroke([(x0, y0 + 9), (x0 + 560, y0 + 9)], 'marker', 4, m, 1.0, taper=[0, 0]); t.stroke([(x0, y0 + 23), (x0 + 560, y0 + 23)], 'marker', 4, m, 1.0, taper=[0, 0])
        for i in range(16): cloud(t, 16 + i * 32, y0 + 16, 10, m, 2.5)
    x0 = r.uniform(0, 512)   # blade: bright ground edges, a darker central ridge, fine grind lines along the blade
    t.stroke([(x0, 262), (x0 + 560, 262)], 'marker', 8, hi, 1.0, taper=[0, 0]); t.stroke([(x0, 314), (x0 + 560, 314)], 'marker', 8, hi, 1.0, taper=[0, 0])
    t.stroke([(x0, 288), (x0 + 560, 288)], 'marker', 6, sh, 1.0, taper=[0, 0])
    for _ in range(40):
        x, y = r.uniform(0, 512), r.uniform(266, 310); t.stroke([(x, y), (x + r.uniform(30, 90), y)], 'chalk', 2, hi, 0.35, taper=[0, 0])
    for i in range(16):    # rivets: domed heads, lit from the upper left
        cx = 16 + i * 32
        t.stroke([(cx - 1, 336), (cx + 1, 336)], 'marker', 14, sh, 1.0, taper=[0, 0]); t.stroke([(cx - 3, 333), (cx - 1, 332)], 'marker', 6, hi, 1.0, taper=[0, 0])
    for i in range(32):    # gauntlet bands on the dark bronze
        x = i * 16; t.stroke([(x, 356), (x, 412)], 'ink', 3, deep, 0.8, taper=[0, 0]); t.stroke([(x + 3, 356), (x + 3, 412)], 'ink', 2, base, 0.6, taper=[0, 0])
    t.stage = 3
    for _ in range(60):
        x, y = r.uniform(0, 512), r.uniform(0, 190); t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(2, 4), deep, r.uniform(0.5, 0.8), taper=[0, 0])
    for _ in range(20):
        x, y = r.uniform(0, 512), r.uniform(0, 190); a = r.uniform(-0.3, 0.3); L = r.uniform(10, 30)
        t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'chalk', r.uniform(3, 5), hi, r.uniform(0.3, 0.5))
    return t


def cloth():
    t = Tex('suit_cloth', 512, CLOTH[2], 903, wx=True, wy=True); r = t.r
    t.stage = 0; t.band(0, 512, CLOTH[2], size=30)
    t.stage = 1
    for _ in range(90):    # vertical folds (v runs down the garment): soft shadow and light streaks
        x = r.uniform(0, 512); y = r.uniform(0, 512); L = r.uniform(80, 220)
        t.stroke(t.wob(x, y, x + r.uniform(-8, 8), y + L, 5, 3), 'flat-bristle', r.uniform(10, 24), r.choice([CLOTH[0], CLOTH[1], CLOTH[3]]), r.uniform(0.3, 0.5))
    t.stage = 2
    for i in range(0, 512, 6):  # weave: faint cross threads
        t.stroke([(0, i), (520, i)], 'ink', 1.2, CLOTH[1], 0.25, taper=[0, 0], wrap=False)
    for i in range(0, 512, 8):
        t.stroke([(i, 0), (i, 520)], 'ink', 1.2, CLOTH[3], 0.2, taper=[0, 0], wrap=False)
    t.stage = 3
    for _ in range(80):
        x, y = r.uniform(0, 512), r.uniform(0, 512); t.stroke([(x, y), (x + r.uniform(4, 12), y + r.uniform(-1, 1))], 'chalk', 2, CLOTH[0], 0.35, taper=[0, 0])
    return t


if __name__ == '__main__':
    for f in (lamellar, bronze, cloth):
        t = f(); print(t.name, t.write(), 'ops')
