#!/usr/bin/env python3
"""School emblem standard banners (asset list C12), painted in klad (art is klad paint; this script only places the marks).

One 1024 x 1024 alpha atlas, 5 x 2 cells of 204.8 x 512 px (0.8 x 2.0 m at 256 px/m); cell i = school i in CONFIG.SCHOOLS order
(ru dao fa mo yinyang za ming zongheng nong), cell 9 left empty. One shared banner mesh; the game picks a school by UV offset
(u = (i % 5) * 0.2, v = (i // 5) * 0.5, glTF v down).
Each banner: the school's accent as the field (the owner's one school mapping, 25 Nov: the 鼎 accents), a Qin-black
heading band with bronze ties, black side hems and a hem over three tongues (alpha cut), shallow cloth folds, and an invented sigil in
black or bone (whichever contrasts with the field). Sigils are pictures and abstract marks drawn as filled shapes (no calligraphy, no
characters): ru a ritual cauldron, dao a spiral, fa a balance, mo a wall with a gate, yinyang a sun disc over a moon ring, za nine dots,
ming a diamond holding a point, zongheng two crossed arrows, nong a ripe grain ear with two leaves.
Usage: python3 standard_tex.py OPSDIR   then  python3 paint_palace.py KLAD OPSDIR SRCDIR OUTDIR STRIPDIR school_standards
Checked by art/tools/standard_check.py.
"""
import math, os, sys
OPS = sys.argv[1]
sys.argv = [sys.argv[0], OPS, '1024']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Atlas grid (columns, rows) and cell size in px (1024 px atlas; cell = 0.8 x 2.0 m at 256 px/m).
GRID = (5, 2)
CW, CH = 1024 / 5, 1024 / 2
# Transparent margin inside every cell, px (no bleed between schools under filtering).
MARGIN = 6
# School order = index.html CONFIG.SCHOOLS; accents = the owner's one mapping for every school item (25 Nov 02:1x: W1a's 鼎 accents,
# art/tools/ding_blender.py ACCENTS): ru ochre, dao gold, fa lead white, mo cinnabar, yinyang bone black, za silver, ming Han purple,
# zongheng malachite, nong azurite.
SCHOOLS = [('ru', '#b8862e'), ('dao', '#e2b84a'), ('fa', '#d9d2c3'), ('mo', '#a8321e'), ('yinyang', '#1a1614'), ('za', '#c8ccd0'),
           ('ming', '#5b3f8c'), ('zongheng', '#2f8a5c'), ('nong', '#2e5a9c')]
# Qin black (hems, heading, dark sigils), bone (light sigils), bronze ties on the heading band.
QIN_BLACK = '#1e1916'
BONE = '#e9dfca'
BRONZE = '#b08a4a'
# Hems and heading on a near-black field (L* below HEM_DARK_BELOW) in dark bronze-brown, so the frame still shows.
HEM_ON_DARK = '#4a3c2e'
HEM_DARK_BELOW = 20
# Field L* above this takes a black sigil, else bone.
SIGIL_DARK_ABOVE = 52
# Heading band, side hem and tongue hem widths, px; tongue length and gap between tongues, px.
HEAD_H, HEM_W, HEM_H = 30, 9, 8
TONGUE_L, TONGUE_GAP = 78, 12
# Sigil centre (fraction of cell height) and half size, px.
SIGIL_Y, SIGIL_HALF = 0.40, 74


def lstar(hx):
    c = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]
    y = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
    return 116 * (y ** (1 / 3) if y > 0.008856 else 7.787 * y + 16 / 116) - 16


def mix(hx, k, to=(0, 0, 0)):
    c = [int(hx[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(a + (b - a) * k):02x}' for a, b in zip(c, to))


def fill(t, polys, color, size=5, step=3.0, brush='ink', op=1.0):
    """even-odd scanline fill of one or more closed polygons with short horizontal strokes inset by half the brush size."""
    ys = [y for p in polys for _, y in p]; y = min(ys) + size / 2
    while y <= max(ys) - size / 2 + 0.01:
        xs = []
        for p in polys:
            for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]):
                if (y0 <= y < y1) or (y1 <= y < y0): xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            a, b = a + size / 2, b - size / 2
            if b > a: t.stroke([(a, y), (b, y)], brush, size, color, op, taper=[0, 0], wrap=False)
            elif b > a - size: t.stroke([((a + b) / 2, y), ((a + b) / 2 + 0.5, y)], brush, max(1.5, b - a + size), color, op, taper=[0, 0], wrap=False)
        y += step


def circle(cx, cy, r, n=40, a0=0.0, a1=math.tau):
    return [(cx + math.cos(a0 + (a1 - a0) * k / n) * r, cy + math.sin(a0 + (a1 - a0) * k / n) * r) for k in range(n + (0 if a1 - a0 >= math.tau else 1))]


def banner_outline(x0, y0, x1, y1):
    """the cloth: a rectangle down to the tongue line, then three pointed tongues with gaps (polygons in px)."""
    yt = y1 - TONGUE_L; w = (x1 - x0 - 2 * TONGUE_GAP) / 3
    body = [(x0, y0), (x1, y0), (x1, yt + 1), (x0, yt + 1)]
    tongues = []
    for k in range(3):
        a = x0 + k * (w + TONGUE_GAP); b = a + w
        tongues.append([(a, yt), (b, yt), (b, y1 - 26), ((a + b) / 2, y1), (a, y1 - 26)])
    return body, tongues, yt


def sigil(t, kind, cx, cy, s, c):
    """invented school sigils as filled shapes (unit coords -1..1 scaled by s)."""
    U = lambda pts: [(cx + x * s, cy + y * s) for x, y in pts]
    line = lambda pts, w: t.stroke(U(pts), 'ink', w * s, c, 1.0, taper=[0, 0], wrap=False)
    disc = lambda x, y, r: fill(t, [circle(cx + x * s, cy + y * s, r * s, 36)], c)
    ring = lambda x, y, r, w: t.stroke(circle(cx + x * s, cy + y * s, r * s, 40) + [circle(cx + x * s, cy + y * s, r * s, 40)[0]], 'ink', w * s, c, 1.0, taper=[0, 0], wrap=False)
    if kind == 'ru':  # ritual cauldron: rim, round belly, two upright ears, three legs
        fill(t, [U([(-0.78, -0.18)] + [(math.cos(a) * 0.78, -0.18 + math.sin(a) * 0.62) for a in [k * math.pi / 16 for k in range(17)]])], c)
        line([(-0.92, -0.2), (0.92, -0.2)], 0.16)
        for sx in (-1, 1): line([(sx * 0.66, -0.2), (sx * 0.66, -0.7), (sx * 0.36, -0.7), (sx * 0.36, -0.2)], 0.13)
        for x0_, x1_ in ((-0.45, -0.62), (0.0, 0.0), (0.45, 0.62)): line([(x0_, 0.3), (x1_, 0.92)], 0.17)
    elif kind == 'dao':  # one bold spiral opening outward
        line([(math.cos(k * 0.22) * (0.08 + 0.82 * k / 64), math.sin(k * 0.22) * (0.08 + 0.82 * k / 64)) for k in range(65)], 0.17)
    elif kind == 'fa':  # balance: post on a foot, beam, cords, two pans
        line([(0, -0.72), (0, 0.86)], 0.15); line([(-0.42, 0.88), (0.42, 0.88)], 0.17); line([(-0.86, -0.52), (0.86, -0.52)], 0.13)
        disc(0, -0.76, 0.13)
        for sx in (-1, 1):
            line([(sx * 0.74, -0.52), (sx * 0.95, 0.06)], 0.06); line([(sx * 0.74, -0.52), (sx * 0.53, 0.06)], 0.06)
            fill(t, [U([(sx * 0.74 + math.cos(a) * 0.27, 0.06 + math.sin(a) * 0.22) for a in [k * math.pi / 12 for k in range(13)]])], c)
    elif kind == 'mo':  # defended wall: four merlons over a wall with an arched gate (the gate is a hole)
        wall = [(-0.92, -0.2), (0.92, -0.2), (0.92, 0.62), (-0.92, 0.62)]
        gate = [(-0.27, 0.62), (0.27, 0.62), (0.27, 0.22)] + [(math.cos(a) * 0.27, 0.22 - math.sin(a) * 0.27) for a in [k * math.pi / 10 for k in range(11)]] + [(-0.27, 0.22)]
        fill(t, [U(wall), U(gate)], c)
        for a in (-0.92, -0.42, 0.12, 0.62): fill(t, [U([(a, -0.58), (a + 0.3, -0.58), (a + 0.3, -0.18), (a, -0.18)])], c)
    elif kind == 'yinyang':  # sun disc over a moon ring
        disc(0, -0.46, 0.46); ring(0, 0.5, 0.4, 0.17)
    elif kind == 'za':  # nine dots
        for i in (-1, 0, 1):
            for j in (-1, 0, 1): disc(i * 0.62, j * 0.62, 0.19)
    elif kind == 'ming':  # a diamond holding a point
        line([(0, -0.92), (0.8, 0), (0, 0.92), (-0.8, 0), (0, -0.92), (0.8, 0)], 0.14)
        fill(t, [U([(0, -0.3), (0.26, 0), (0, 0.3), (-0.26, 0)])], c)
    elif kind == 'zongheng':  # two crossed arrows, heads up
        for sx in (-1, 1):
            line([(-sx * 0.72, 0.8), (sx * 0.62, -0.62)], 0.13)
            hx, hy = sx * 0.86, -0.86
            fill(t, [U([(hx, hy), (hx - sx * 0.12, hy + 0.48), (hx - sx * 0.48, hy + 0.12)])], c)
        for sx in (-1, 1): line([(-sx * 0.72, 0.8), (-sx * 0.92, 0.62)], 0.09); line([(-sx * 0.72, 0.8), (-sx * 0.55, 0.98)], 0.09)
    elif kind == 'nong':  # a ripe grain ear drooping right from a curved stalk, two long leaves
        line([(-0.1, 0.95), (-0.06, 0.3), (-0.02, -0.3), (0.12, -0.66), (0.36, -0.8)], 0.14)
        for k in range(6):
            u = k / 5; x = 0.1 + 0.7 * u; y = -0.78 + 0.62 * u * u
            fill(t, [[(cx + (x + math.cos(q) * 0.21) * s, cy + (y + math.sin(q) * 0.15) * s) for q in [j * math.tau / 18 for j in range(18)]]], c)
        def leaf(bx, by, tx, ty, wd):
            n = 10; nx, ny = -(ty - by), tx - bx; L = math.hypot(nx, ny); nx, ny = nx / L, ny / L
            up = [(bx + (tx - bx) * k / n + nx * wd * math.sin(math.pi * k / n), by + (ty - by) * k / n + ny * wd * math.sin(math.pi * k / n)) for k in range(n + 1)]
            dn = [(bx + (tx - bx) * k / n - nx * wd * 0.4 * math.sin(math.pi * k / n), by + (ty - by) * k / n - ny * wd * 0.4 * math.sin(math.pi * k / n)) for k in range(n, -1, -1)]
            fill(t, [U(up + dn)], c)
        leaf(-0.07, 0.42, -0.86, -0.16, 0.22); leaf(-0.05, 0.66, 0.8, 0.16, 0.22)


def school_standards():
    """stages run outer and schools inner, so the passes strip has four frames (base, tone, marks, all nine schools each)."""
    t = P.Tex('school_standards', 'none', False, False, 1201); r = t.r
    cells = []
    for i, (kind, acc) in enumerate(SCHOOLS):
        cx0, cy0 = (i % GRID[0]) * CW, (i // GRID[0]) * CH
        x0, y0, x1, y1 = cx0 + MARGIN, cy0 + MARGIN, cx0 + CW - MARGIN, cy0 + CH - MARGIN
        body, tongues, yt = banner_outline(x0, y0, x1, y1)
        cells.append((kind, acc, cy0, x0, y0, x1, y1, body, tongues, yt, QIN_BLACK if lstar(acc) > SIGIL_DARK_ABOVE else BONE,
                      HEM_ON_DARK if lstar(acc) < HEM_DARK_BELOW else QIN_BLACK))
    t.stage = 0  # base: the accent field over the whole cloth
    for kind, acc, cy0, x0, y0, x1, y1, body, tongues, yt, sig, hem in cells:
        fill(t, [body], acc, size=6, step=4)
        for tg in tongues: fill(t, [tg], acc, size=6, step=4)
    t.stage = 1  # tone: shallow vertical folds (darker hollows, lighter ridges), faint weave, worn flecks; all inside the cloth
    for kind, acc, cy0, x0, y0, x1, y1, body, tongues, yt, sig, hem in cells:
        for k in range(6):
            fx = x0 + 22 + k * (x1 - x0 - 44) / 5 + r.uniform(-5, 5); dark = k % 2 == 0
            t.stroke(t.wobble(fx, y0 + HEAD_H + 18, fx + r.uniform(-4, 4), yt - 18, 5, 2), 'soft', r.uniform(16, 24),
                     mix(acc, 0.22) if dark else mix(acc, 0.1, (255, 255, 255)), 0.35, taper=[0, 0], wrap=False)
        for _ in range(26):
            yy = r.uniform(y0 + HEAD_H + 6, yt - 6)
            t.stroke([(x0 + HEM_W + 4, yy), (x1 - HEM_W - 4, yy + r.uniform(-1, 1))], 'pencil', 1.2, mix(acc, 0.3), 0.12, taper=[0, 0], wrap=False)
        for _ in range(10):
            fx, fy = r.uniform(x0 + 20, x1 - 20), r.uniform(y0 + HEAD_H + 20, yt - 30)
            t.stroke(t.wobble(fx, fy, fx + r.uniform(-10, 10), fy + r.uniform(8, 20), 3, 2), 'soft', r.uniform(6, 10), mix(acc, 0.15, (255, 255, 255)), 0.18, taper=[0, 0], wrap=False)
    t.stage = 2  # marks: heading band with bronze ties, side hems, tongue hem, the sigil
    for kind, acc, cy0, x0, y0, x1, y1, body, tongues, yt, sig, hem in cells:
        fill(t, [[(x0, y0), (x1, y0), (x1, y0 + HEAD_H), (x0, y0 + HEAD_H)]], hem, size=6, step=4)
        for xx in (x0 + 26, (x0 + x1) / 2, x1 - 26): fill(t, [[(xx - 8, y0 + 4), (xx + 8, y0 + 4), (xx + 8, y0 + HEAD_H - 4), (xx - 8, y0 + HEAD_H - 4)]], BRONZE, size=4, step=3)
        for a in (x0, x1 - HEM_W): fill(t, [[(a, y0 + HEAD_H), (a + HEM_W, y0 + HEAD_H), (a + HEM_W, yt), (a, yt)]], hem, size=5, step=3)
        fill(t, [[(x0, yt - HEM_H), (x1, yt - HEM_H), (x1, yt), (x0, yt)]], hem, size=5, step=3)
        sigil(t, kind, (x0 + x1) / 2, cy0 + CH * SIGIL_Y, SIGIL_HALF, sig)
    return t


if __name__ == '__main__':
    os.makedirs(OPS, exist_ok=True)
    t = school_standards(); print(t.name, t.write(), 'ops')
