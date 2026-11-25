"""Techno-plate Knight, 64 px, four views. Original shapes drawn in code (not a scaled 3D render).
Each view is a function that paints onto a pxkit canvas. Used by model 1 (gen_m1.py) and model 2 (gen_m2.py).
"""
import numpy as np
from pxkit import Cv, AX, W, H


# ======================================================================= FRONT
def sword_front(c):
    """two-handed, tip up at 45 degrees toward the knight's left (viewer's right)"""
    P = 'new'
    for i in range(9):                                  # grip (red), two diagonals
        c.px([(33 - i, 28 + i)], 'grip', 3, P); P = c.n
        c.px([(34 - i, 28 + i)], 'grip', 1, P)
    c.px([(23, 37), (24, 37), (23, 38), (24, 38)], 'brass', 3, 'new')   # pommel
    c.px([(23, 37)], 'brass', 4); c.px([(24, 38)], 'brass', 2)
    P = 'new'                                           # blade: light edge / cyan fuller / shaded edge
    for i in range(18):
        x, y = 35 + i, 26 - i
        c.px([(x, y - 1)], 'steel', 6 if i < 16 else 5, P); P = c.n
        c.px([(x, y)], 'glow' if i < 13 else 'steel', 2 if i < 13 else 5, P)
        if i < 17:
            c.px([(x + 1, y)], 'steel', 3, P)
    c.px([(53, 8)], 'steel', 6, P)
    P = 'new'                                           # crossguard across the blade
    for i in range(8):
        c.px([(31 + i, 24 + i)], 'brass', 4 if i < 5 else 3, P); P = c.n
    for i in range(7):
        c.px([(31 + i, 25 + i)], 'brass', 2, P)


FIST = [".bcb.", "bdcdb", "acbca", ".aba."]                  # 4x4 fist of round fingers


def hands_front(c):
    for (x0, y0) in ((29, 28), (25, 32)):
        rows = [r.replace('X', '.') for r in FIST]
        c.grid(rows, x0, y0)


def legs_front(c, back=False):
    for s in (-1, 1):
        cx = AX + s * 5.5
        m, lat, u = c.cap((cx, 41), (cx, 46), 3.7, 3.5)
        th = c.put(m, 'steel', c.i_cap(lat, u))
        c.shift(m & (c.yy == 44) & (c.xx % 2 == 0), -1)
        m, lat, u = c.cap((cx, 50.5), (cx, 56.2), 3.5, 3.1)
        g = c.put(m, 'steel', c.i_cap(lat, u))
        if back:
            c.px([(cx - 2, y) for y in range(51, 56)] + [(cx + 2, y) for y in range(51, 56)], 'brass', 3 if s < 0 else 2, g)
        else:
            c.px([(cx, y) for y in (51, 52, 53, 54)], 'glow', 2, g)
        c.px([(cx - 3, 56), (cx + 3, 56)], 'brass', 2, g)
        pts = [(cx - 3.7, 56.6), (cx + 3.7, 56.6), (cx + 4.4, 59.2), (cx + 0.6, 61.6), (cx - 0.6, 61.6), (cx - 4.4, 59.2)]
        m = c.poly(pts)                                   # sabaton, point toward the viewer
        c.put(m, 'steel', c.i_cylv(cx, 4.8, tilt=-0.2))
        c.shift(m & (c.yy == 58), -1); c.shift(m & (c.yy == 60), -1)
        if not back:
            c.px([(cx, 59), (cx, 61)], 'steel', 6)
        else:                                           # from behind: square heel, no toe point
            hm = c.rect(cx - 3.6, 59.5, cx + 3.6, 61.4)
            c.put(hm, 'steel', c.i_cylv(cx, 4.8), part=None); c.shift(hm & (c.yy == 61), -1)
        m = c.ell(cx, 48.2, 4.0, 2.6)                     # round knee cop
        k = c.put(m, 'steel', c.i_sphere(cx, 48.2, 4.2, 3.0))
        if not back:
            c.px([(cx, 48)], 'glow', 3, k)
        else:
            c.shift(m, -1)
        c.px([(cx + s * 4, 48), (cx + s * 4, 49)], 'brass', 3 if s < 0 else 2, k)
        c.px([(cx + s * 5, 48)], 'steel', 5 if s < 0 else 3, k)


def fauld_front(c, back=False):
    dx = c.xx - AX
    w = 8.4 + (c.yy - 34) * 0.52
    ybot = 40.4 + 2.2 * (1 - (dx / 12.6) ** 2)
    m = (np.abs(dx) <= w) & (c.yy >= 34.5) & (c.yy <= ybot)
    f = c.put(m, 'steel', c.i_cylv(AX, w + 0.6, tilt=-0.18))
    for y0, k in ((36.6, 1.2), (38.9, 1.7)):              # lames bow down in the middle: a round skirt
        yl = np.round(y0 + k * (1 - (dx / 12.5) ** 2))
        c.shift(m & (c.yy == yl), -2)
        c.shift(m & (c.yy == yl + 1), +1)
    c.shift(m & (c.yy >= ybot - 1.0), -1)
    for s in (-1, 1):
        x = AX + s * 6.5
        c.px([(x - 1, 40), (x, 41), (x + 1, 40)], 'glow', 2, f)
    t = c.rect(29, 34.5, 34, 45.4)                        # tabard
    tp = c.put(t, 'cloth', tone=3)
    c.px([(29, y) for y in range(35, 46)], 'cloth', 4, tp)
    c.px([(34, y) for y in range(35, 46)], 'cloth', 2, tp)
    c.px([(32, y) for y in range(37, 45)], 'cloth', 2, tp)
    c.px([(x, 45) for x in range(29, 35)], 'cloth', 2, tp)
    if back:                                              # pale cross on the back cloth
        c.px([(31, y) for y in range(37, 44)] + [(32, y) for y in range(37, 44)] + [(30, 39), (33, 39)], 'steel', 6, tp)
        c.px([(32, y) for y in range(37, 44)] + [(33, 39)], 'steel', 5, tp)


def torso_front(c, back=False):
    dx = c.xx - AX
    hw = 8.4 - np.clip(c.yy - 24, 0, 99) * 0.22
    m = (np.abs(dx) <= hw) & (c.yy >= 16.5) & (c.yy <= 33.4)
    t = c.put(m, 'steel', c.i_cylv(AX, 10.5, tilt=-0.25))
    c.shift(m & (c.yy >= 19) & (c.yy <= 32) & (c.xx % 2 == 0), -1)     # fluting
    b = c.rect(25, 32.5, 38, 34.4)
    c.put(b, 'brass', c.i_cylv(AX, 8.5))
    c.shift(b & (c.yy == 34), -1)
    if back:
        return
    g = c.ell(AX, 18.4, 6.6, 2.0)                         # gorget
    c.put(g, 'steel', c.i_sphere(AX, 19.5, 8, 4), bias=0.15)
    r = c.ell(AX, 22.5, 2.1, 2.1)                         # reactor
    rp = c.put(r, 'brass', c.i_sphere(AX, 22.5, 2.6, 2.6), lo=2)
    c.px([(31, 22), (32, 22), (31, 23), (32, 23)], 'glow', 3, rp)
    c.px([(31, 22)], 'glow', 4, rp)
    for s in (-1, 1):                                     # chest emblems
        x = AX + s * 5.5
        c.px([(x, 21), (x - 1, 22), (x + 1, 22), (x, 23)], 'brass', 3 if s < 0 else 2, t)
        c.px([(x, 22)], 'glow', 2, t)


def pauldrons_front(c):
    for s in (-1, 1):
        cx = AX + s * 11.8
        rx, ry = 6.6, 6.8
        dx = c.xx - cx
        arc = np.sqrt(np.clip(1 - (dx / rx) ** 2, 0, 1))
        yrim = 21.6 + 1.7 * arc
        dome = (c.ell(cx, 21.5, rx, ry) & (c.yy <= 21.5)) | ((np.abs(dx) <= rx) & (c.yy > 21.5) & (c.yy <= yrim + 1.2))
        p = c.put(dome, 'steel', c.i_sphere(cx, 22.2, rx + 0.5, ry + 1.0))
        yr = np.round(yrim)
        c.put(dome & (c.yy >= yr), 'brass', c.i_cylv(cx, rx + 0.5), part=p, lo=1)
        c.put(dome & (c.yy == yr - 2) & (np.abs(dx) < rx * 0.75), 'glow', tone=2, part=p)
        ye = np.round(17.4 + 1.6 * arc)                   # engraved band following the dome
        c.shift(dome & (c.yy == ye) & (np.abs(dx) < rx * 0.8), -1)


def arms_front(c, back=False):
    for s, wrist in (((-1, (20.0, 32.0)), (1, (43.0, 32.0))) if back else ((-1, (24.6, 33.4)), (1, (36.4, 30.8)))):
        ex, ey = AX + s * 14.6, 28.0
        m = c.ell(ex, ey, 2.7, 2.7)
        e = c.put(m, 'gun', c.i_sphere(ex, ey, 3.0, 3.0), lo=1)
        c.px([(ex + s * 2, ey)], 'brass', 3, e)
        m, lat, u = c.cap((ex - s * 2.2, ey + 0.8), wrist, 2.2, 3.2)
        a = c.put(m, 'steel', c.i_cap(lat, u))
        d = np.hypot(c.xx - wrist[0], c.yy - wrist[1])
        c.put(m & (((c.xx - wrist[0]) * u[0] + (c.yy - wrist[1]) * u[1]) >= -0.2) & (d <= 3.3), 'brass', c.i_cap(lat, u), part=a, lo=2)
        mx, my = (ex - s * 2.2 + wrist[0]) / 2, (ey + 0.8 + wrist[1]) / 2
        if not back:
            c.px([(mx, my), (mx + s, my - (0.45 if s < 0 else 0.2))], 'glow', 2, a)


HEAD_FRONT = [   # 24 wide, x 20..43, rows y 1..19; hand-placed. horns a-d, steel 1-6, glow g-j
    "..c........6.........b..",
    ".db......i.64........ba.",
    ".db......a.64........ba.",
    ".dca.....a.64.......bba.",
    "..dcba...a.64.....cbba..",
    "...dccba.445444.cbbaa...",
    ".....dcba55ji54cbaa.....",
    ".......4555hh4443.......",
    "......466666555544......",
    "...444211114311112333...",
    "......3hjj1431jjh2......",
    "..5444431hi43ih1233334..",
    "......443245442323......",
    "......443456443233......",
    "....44...416413...33....",
    ".........6a66a5.........",
    ".........hihhih.........",
    "..........5224..........",
    "...........53...........",
]

def head_back_rows():
    """back of the helm: the front silhouette mirrored, face replaced by a smooth skull, spine ridge and neck guard"""
    out = []
    for j, row in enumerate(HEAD_FRONT):
        row = row[::-1]
        new = ''
        for i, ch in enumerate(row):
            skull = (j >= 5) and (ch in '123456ghij') and 6 <= i <= 17
            if j >= 15:
                new += '.'
            elif j >= 12 and 7 <= i <= 16:                    # neck guard lames
                new += ('2' if j == 13 else ('4' if i < 12 else '3'))
            elif j >= 12:
                new += ch if ch in '345' and not (6 <= i <= 17) else '.'
            elif skull:
                t = 5 if i < 10 else (4 if i < 14 else 3)
                if i in (11, 12):
                    t = 6 if i == 11 else 3                   # spine ridge
                if j == 8:
                    t -= 1                                    # band round the skull
                new += str(max(2, t))
            elif ch in 'abcd':
                new += {'d': 'a', 'c': 'b', 'b': 'c', 'a': 'd'}[ch] if i > 12 else ch
            else:
                new += ch
        out.append(new)
    return out


def head_front(c, back=False):
    c.put(c.rect(27, 14.5, 36, 18.4), 'gun', c.i_cylv(AX, 6), lo=1, hi=2)      # dark neck under the jaw
    rows = head_back_rows() if back else HEAD_FRONT
    c.grid(rows, 20, 1)
    ax = 34 if back else 29                                # antenna: thin, no outline of its own
    for y in range(2, 6):
        c.thin[y, ax] = True


def front(c):
    legs_front(c)
    fauld_front(c)
    torso_front(c)
    pauldrons_front(c)
    head_front(c)
    arms_front(c)
    sword_front(c)
    hands_front(c)


# ======================================================================= BACK
def pack_back(c):
    # exhaust stacks rising behind the shoulders
    for s in (-1, 1):
        m, lat, u = c.cap((AX + s * 4.6, 21), (AX + s * 6.6, 12.4), 1.5, 1.5)
        p = c.put(m, 'gun', c.i_cap(lat, u), lo=1)
        c.px([(AX + s * 6.5 - 0.5, 12), (AX + s * 6.5 + 0.5, 12)], 'brass', 3 if s < 0 else 2, p)
    # hoses from the drum to the waist
    for s in (-1, 1):
        for (x, y) in ((8.5, 23), (9.5, 24), (10.5, 25), (10.5, 26), (10.5, 27), (9.5, 28), (8.5, 29), (7.5, 30)):
            c.px([(AX + s * x, y)], 'gun', 1 if s > 0 else 2, None)
    # reactor drum lying across the back, round ends
    m, lat, u = c.cap((AX - 5.0, 23.5), (AX + 5.0, 23.5), 3.6, 3.6)
    d = c.put(m, 'gun', c.i_cylh(23.5, 4.0), lo=1)
    for x in (27, 36):
        c.put(m & (c.xx == x), 'brass', c.i_cylh(23.5, 4.0), part=d, lo=1)
    c.px([(31, 23), (32, 23), (31, 24), (32, 24)], 'glow', 3, d)
    c.px([(31, 22), (32, 22)], 'glow', 2, d)


def back(c):
    legs_front(c, back=True)
    fauld_front(c, back=True)
    torso_front(c, back=True)
    # blade tip showing past the knight's left shoulder (viewer's left from behind)
    P = 'new'
    for i in range(11, 18):
        x, y = 63 - (35 + i), 26 - i
        c.px([(x, y - 1)], 'steel', 6 if i < 16 else 5, P); P = c.n
        c.px([(x, y)], 'glow' if i < 13 else 'steel', 2 if i < 13 else 5, P)
        if i < 17:
            c.px([(x - 1, y)], 'steel', 3, P)
    c.px([(10, 8)], 'steel', 6, P)
    arms_front(c, back=True)
    pauldrons_front(c)
    pack_back(c)
    head_front(c, back=True)


# ======================================================================= SIDE (drawn facing right)
HEAD_SIDE = [    # 20 wide, x 21..40, rows y 1..19. wedge snout, heavy brow, fanged jaw, two horns swept back
    "dc..a...............",
    ".dcbab..............",
    "..dcbab.6...........",
    "...dcbab64..i.......",
    "....dcba.64.a.......",
    ".....dcb565454......",
    "......dc556655554...",
    "......455566666655..",
    ".....4455541111a456.",
    "..44444555431jji1455",
    ".....44544431hh13415",
    ".5444344343333344443",
    ".....3344343322222a.",
    "...443343321h6h6h66.",
    "..4....bbaa2ihihi6..",
    ".......bbaa244445...",
    ".......bbaa.2332....",
    ".......bbaa...53....",
    "..............4.....",
]


def side(c, near='right'):
    CX = 29.5
    # --- pack on the back: stacks, drum end with lens, hose
    for (x0, y0, x1, y1) in ((19.6, 22.0, 16.4, 13.6), (22.4, 21.0, 19.6, 12.4)):
        m, lat, u = c.cap((x0, y0), (x1, y1), 1.5, 1.5)
        p = c.put(m, 'gun', c.i_cap(lat, u), lo=1)
        c.px([(x1 - 0.4, y1 - 0.6), (x1 + 0.6, y1 - 0.2)], 'brass', 3, p)
    c.put(c.rect(19, 20.5, 24, 30.4), 'gun', c.i_cylv(21.5, 3.5), lo=1, hi=3)
    m = c.ell(17.8, 26.2, 4.2, 4.4)
    d = c.put(m, 'gun', c.i_sphere(17.8, 26.2, 4.6, 4.8), lo=1)
    ring = m & ~c.ell(17.8, 26.2, 3.0, 3.2)
    c.put(c.ell(17.8, 26.2, 3.0, 3.2) & ~c.ell(17.8, 26.2, 1.9, 2.0), 'brass', c.i_sphere(17.8, 26.2, 3.4, 3.4), part=d, lo=1)
    c.put(c.ell(17.8, 26.2, 1.9, 2.0), 'glow', c.i_sphere(17.8, 26.2, 2.4, 2.4), part=d, lo=1, hi=3)
    for (x, y) in ((16, 31), (17, 32), (18, 33), (19, 34), (20, 34), (21, 34)):
        c.px([(x, y)], 'gun', 1, None)
    # --- far leg, a step ahead, one tone down
    far = np.zeros((H, W), bool)
    m, lat, u = c.cap((31.5, 41), (32, 46), 3.4, 3.2); c.put(m, 'steel', c.i_cap(lat, u)); far |= m
    m, lat, u = c.cap((32, 50), (32, 56), 3.3, 3.0); c.put(m, 'steel', c.i_cap(lat, u)); far |= m
    m = c.poly([(29, 56.6), (35.5, 56.6), (38, 58), (42.6, 60.6), (42.6, 61.6), (29, 61.6)])
    c.put(m, 'steel', c.i_cylh(59, 3.2)); far |= m
    c.shift(far, -1)
    # --- torso in profile: round chest
    m = (c.ell(CX, 25, 6.0, 9.0) | c.ell(31.2, 23.6, 5.6, 6.2)) & (c.yy >= 16.5) & (c.yy <= 33.4)
    t = c.put(m, 'steel', c.i_sphere(30.5, 24, 8.5, 11))
    for k in (0, 1, 2):                                     # flutes curve round the chest
        xs = 33.0 + k * 1.6 - ((c.yy - 24) / 9.0) ** 2 * 2.2
        c.shift(m & (np.round(xs) == c.xx) & (c.yy >= 19), -1)
    b = c.rect(24, 32.5, 35, 34.4)
    c.put(b, 'brass', c.i_cylv(CX, 7.0)); c.shift(b & (c.yy == 34), -1)
    # --- near leg
    m, lat, u = c.cap((28, 41), (28.2, 46), 3.9, 3.6)
    c.put(m, 'steel', c.i_cap(lat, u)); c.shift(m & (c.yy == 44) & (c.xx % 2 == 0), -1)
    m, lat, u = c.cap((28.2, 50.5), (28.2, 56.2), 3.7, 3.2)
    g = c.put(m, 'steel', c.i_cap(lat, u))
    c.px([(31, y) for y in (51, 52, 53, 54)], 'glow', 2, g)
    c.px([(25, 56), (26, 56), (30, 56), (31, 56)], 'brass', 2, g)
    m = c.poly([(24.4, 56.6), (31.8, 56.6), (34.4, 58), (39.6, 60.6), (39.6, 61.6), (24.4, 61.6)])
    sb = c.put(m, 'steel', c.i_cylh(58.6, 3.4))
    for x in (30, 33, 36):                                  # sabaton lames
        c.shift(m & (c.xx == x), -2)
    c.shift(m & (c.yy == 61), -1)
    c.px([(38, 60), (39, 60)], 'steel', 6, sb)
    m = c.ell(28.6, 48.2, 4.0, 2.9)
    k = c.put(m, 'steel', c.i_sphere(28.6, 48.2, 4.2, 3.2))
    c.put(c.ell(28.6, 48.2, 2.3, 2.2), 'brass', c.i_sphere(28.6, 48.2, 2.6, 2.6), part=k, lo=1)
    c.px([(28, 48), (29, 48), (28, 49), (29, 49)], 'gun', 1, k); c.px([(28, 48)], 'glow', 4, k)
    c.px([(33, 47), (34, 46)], 'steel', 5, k)               # knee fan toward the front
    # --- fauld: round skirt, lames bow down
    dx = c.xx - CX
    w = 6.6 + (c.yy - 34) * 0.55
    ybot = 40.8 + 2.0 * (1 - (dx / 11.0) ** 2)
    m = (np.abs(dx) <= w) & (c.yy >= 34.5) & (c.yy <= ybot)
    f = c.put(m, 'steel', c.i_cylv(CX, w + 0.6, tilt=-0.18))
    for y0, k in ((36.6, 1.1), (38.9, 1.5)):
        yl = np.round(y0 + k * (1 - (dx / 10.5) ** 2))
        c.shift(m & (c.yy == yl), -2); c.shift(m & (c.yy == yl + 1), +1)
    c.shift(m & (c.yy >= ybot - 1.0), -1)
    c.px([(CX - 0.5 + i, 40 + (1 if i == 1 else 0)) for i in (0, 1, 2)], 'glow', 2, f)
    # tabard edges, front and back
    tp = c.put(c.rect(36, 35.5, 37, 45.4), 'cloth', tone=3)
    c.px([(37, y) for y in range(36, 46)], 'cloth', 4, tp)
    tb = c.put(c.rect(21, 35.5, 22, 44.4), 'cloth', tone=2)
    # --- far forearm, sword, far fist
    m, lat, u = c.cap((33.5, 27.6), (38.6, 28.6), 2.2, 2.6)
    fa = c.put(m, 'steel', c.i_cap(lat, u)); c.shift(m, -1)
    P = 'new'
    for i in range(9):
        c.px([(41 - i, 28 + i)], 'grip', 3, P); P = c.n
        c.px([(42 - i, 28 + i)], 'grip', 1, P)
    c.px([(31, 37), (32, 37), (31, 38), (32, 38)], 'brass', 3, 'new'); c.px([(31, 37)], 'brass', 4); c.px([(32, 38)], 'brass', 2)
    P = 'new'
    dk = 1 if near == 'right' else 0                       # blade leans to the knight's left: far side in the right view
    for i in range(16):
        x, y = 43 + i, 26 - i
        c.px([(x, y - 1)], 'steel', (6 if i < 14 else 5) - dk, P); P = c.n
        c.px([(x, y)], 'glow' if i < 11 else 'steel', 2 if i < 11 else 5 - dk, P)
        if i < 15:
            c.px([(x + 1, y)], 'steel', 3 - dk, P)
    c.px([(59, 10)], 'steel', 6 - dk, P)
    P = 'new'
    for i in range(8):
        c.px([(39 + i, 24 + i)], 'brass', 4 if i < 5 else 3, P); P = c.n
    for i in range(7):
        c.px([(39 + i, 25 + i)], 'brass', 2, P)
    c.grid(FIST, 37, 28)
    # --- head
    hp = c.grid(HEAD_SIDE, 21, 1)
    if near != 'right':                                     # antenna is on the far side in the left view: shorter, further in
        c.m[4, 33] = -1; c.m[5, 33] = -1
        c.px([(32, 4)], 'glow', 3, hp); c.px([(32, 5)], 'gun', 1, hp)
        c.thin[4, 32] = c.thin[5, 32] = True
    else:
        c.thin[4, 33] = c.thin[5, 33] = True
    # --- near pauldron: full dome with rim
    cx, cy, rx, ry = 28.0, 21.8, 6.5, 6.7
    dxp = c.xx - cx
    arc = np.sqrt(np.clip(1 - (dxp / rx) ** 2, 0, 1))
    yrim = cy + 0.2 + 1.8 * arc
    dome = (c.ell(cx, cy, rx, ry) & (c.yy <= cy)) | ((np.abs(dxp) <= rx) & (c.yy > cy) & (c.yy <= yrim + 1.2))
    p = c.put(dome, 'steel', c.i_sphere(cx, cy + 0.6, rx + 0.5, ry + 1.0))
    yr = np.round(yrim)
    c.put(dome & (c.yy >= yr), 'brass', c.i_cylv(cx, rx + 0.5), part=p, lo=1)
    c.put(dome & (c.yy == yr - 2) & (np.abs(dxp) < rx * 0.75), 'glow', tone=2, part=p)
    ye = np.round(17.6 + 1.6 * arc)
    c.shift(dome & (c.yy == ye) & (np.abs(dxp) < rx * 0.8), -1)
    # --- near arm: ball elbow with disc, bell cuff, fist on the grip
    m = c.ell(29.4, 28.8, 2.9, 2.9)
    e = c.put(m, 'gun', c.i_sphere(29.4, 28.8, 3.2, 3.2), lo=1)
    c.px([(29, 28), (30, 28), (29, 29), (30, 29)], 'brass', 2, e); c.px([(29, 28)], 'glow', 4, e)
    wrist = (34.6, 32.4)
    m, lat, u = c.cap((31.0, 30.0), wrist, 2.3, 3.2)
    a = c.put(m, 'steel', c.i_cap(lat, u))
    d = np.hypot(c.xx - wrist[0], c.yy - wrist[1])
    c.put(m & (((c.xx - wrist[0]) * u[0] + (c.yy - wrist[1]) * u[1]) >= -0.2) & (d <= 3.3), 'brass', c.i_cap(lat, u), part=a, lo=2)
    c.px([(32, 30), (33, 31)], 'glow', 2, a)
    c.grid(FIST, 34, 31)


def right(c):
    side(c, 'right')


def left(c):
    side(c, 'left')
    c.flip()
