#!/usr/bin/env python3
"""Palace surfaces A6-A12 and A14-A20 (art/ASSET-LIST.md), painted in klad like the approved round 2 textures (A1-A4).

Reuses art/tools/palace_tex.py by import (class Tex, band, cloud) like bronze_tex.py does; writes one klad `apply` op file per texture
(seeded strokes; the paint is klad's). Every texture is 1024 px = 4 x 4 m at 256 px/m unless its docstring says otherwise.
Style values (art/Qin-Palace-Painted-Study.md): brush runs 4-15 cm, luminance sd 8-30, saturation cap 0.55 (0.6 accents), the study's
value plan and ramps, one light (no light or shadow painted into tiling textures). Colours from the study ramps and the research palette
(docs/research/Qin-palace-medieval-tech-fusion.md, one-page rule list). All motifs are our own drawing; nothing is traced.

Alpha cards (garden_plants, signal_flags) use the background 'none': paint_palace.py then exports a transparent PNG.

Usage: python3 arch_tex.py OUTDIR [SIZE] [NAMES]   (NAMES: comma list, default all)
"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P  # reads OUTDIR and SIZE from argv

CM = 2.56  # px per cm at 256 px/m

# Ramps (study ramps; research palette where the study has none)
EARTH = dict(base='#9b8b6f', lines='#7a6b55', dark='#786953', light='#b2a487', mid='#8f7f63')           # loess, research #A88A5E / #8C6F48 (round 3: earth grey-ochre, away from timber's orange-brown; rounds 1-2 read as wood)
CORE = dict(base='#8e7553', lines='#735c3e', dark='#5f4b35', light='#a88f6a', mid='#836b4b')            # core chamber earth: darker, smoke-dulled
BURNT = dict(base='#8e5a45', lines='#6a3d2e', dark='#5c3629', light='#a26c55', mid='#83503e')           # reddened by fire (Xianyang finds)
STONE = ['#7b786f', '#88857d', '#939087', '#a9a59b', '#8e8a80']
SLAB = ['#8b877e', '#908c83', '#868279', '#8e8a80', '#928e85']  # paving slab tones: narrow on purpose (repeat)
LACQ = ['#15100d', '#1d1612', '#231a15', '#2c2320']
VERM = ['#742d1e', '#86281a', '#9a4a34']
PLASTER = ['#b0a48b', '#b8ac94', '#d2c8b2']
# FIXB 25 Nov (owner 02:2x: 'mercury brighter texture + shimmer'): matcap value ramp = (floor of the bright middle and lower half, peak of
# the bright middle, top band start, lower-half peak); round 3 was (70, 150, 66, 90) at mean lum 130.
MERC_LIFT = (92, 150, 84, 120)
# FIXB pond water (owner 02:2x: 'garden ponds lighter water, blue-green with a pale edge'; the black lake A15 stays black): base, ripple
# crest, trough, glint. Painted light: the pond mesh darkens the open water with vertex colours and leaves the 1 m margin pale.
POND = dict(base='#5f8f88', crest='#86b2aa', trough='#4a7872', glint='#d4e6e0', sand='#9fb3a2')
# FIXB star-map inlay (owner 02:2x: A17 becomes a core floor inlay, subtle lines at 256 px/m, must not fight the 丹 floor or hide tells):
# brass inlay tones (lines, studs, highlight), line and stud widths px, number of asterisms, single studs, margin kept clear px (the
# tile can then be turned 0/90/180/270 deg per 4 m cell without a seam).
# Round 2: lines 7 -> 11 px, studs 13 -> 18, ring 5 -> 8 (round 1: 0.24 of drawn pixels lost at the alpha test; nearly unseen at play).
INLAY = dict(tones=['#a8864c', '#9a7a44', '#b8965a'], line=11, stud=18, ring=8, asterisms=11, singles=46, margin=24)


def layered_earth(name, R, seed, lmin, lmax, soot=False, pocks=3200, thick=0.18):
    """Rammed earth 夯土. Round 3 (lead review 25 Nov: the terrace sides read as wooden planks: even stripes, straight dark seams): tamped
    lifts of uneven thickness (lmin-lmax cm, now and then a thick lift of 15-25 cm), slightly wavy beds (whole sine cycles per tile, so it
    wraps), each lift its own earth tone drawn along its wave, beds marked by a soft change of tone (no dark seam line), tamping pits in
    rows along each lift, crumbled patches and runnels that cross the beds."""
    t = P.Tex(name, R['base'], True, True, seed)
    r = t.r
    t.stage = 1
    for _ in range(70):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(60, 150), 'sponge', r.uniform(60, 120), r.choice([R['dark'], R['light'], R['mid']]), r.uniform(0.2, 0.35), 3)
    hs = []
    while sum(hs) < 400: hs.append(r.uniform(15, 25) if r.random() < thick else r.uniform(lmin, lmax))
    k = 400 / sum(hs); hs = [h * k * CM for h in hs]
    waves = [(r.choice([1, 2, 3]), r.uniform(0, math.tau), r.uniform(2, 6), r.choice([4, 5, 7]), r.uniform(0, math.tau), r.uniform(0.6, 1.6)) for _ in hs]
    def bed(i, x):  # y offset of bed i at x: two whole-cycle sines (wrap-safe)
        k1, p1, a1, k2, p2, a2 = waves[i % len(waves)]
        return a1 * math.sin(math.tau * k1 * x / 1024 + p1) + a2 * math.sin(math.tau * k2 * x / 1024 + p2)
    def along(i, y, x0, x1):
        return [(x, y + bed(i, x)) for x in [x0 + (x1 - x0) * j / 8 for j in range(9)]]
    t.stage = 2
    y = 0.0
    tones = [R['base'], R['mid'], R['light'], R['base'], R['dark']]
    for i, h in enumerate(hs):
        tone = r.choice(tones)
        # the lift's own tone: one continuous stroke along its wave, sampled on a fixed 32 px grid past both edges so the wrap matches
        # (stroke ends read as wood grain)
        for dy in (0, 1024, -1024):  # the vertical wrap by hand (wrap=False above turns off both directions)
            if -h - 8 < y + dy + h * 0.5 < 1024 + h + 8:
                t.stroke([(x, y + dy + h * 0.5 + bed(i, x)) for x in range(-64, 1089, 32)], 'marker', h * 0.95, tone, 0.55, taper=[0, 0], wrap=False)
        for _ in range(int(14 * h / 25)):  # mottling inside the lift: round sponge dabs, not streaks
            px = r.uniform(0, 1024); py = y + h * r.uniform(0.2, 0.8) + bed(i, px)
            t.stroke([(px, py), (px + r.uniform(8, 30), py + r.uniform(-1, 1))], 'sponge', h * r.uniform(0.5, 0.9), r.choice(tones), r.uniform(0.25, 0.4), taper=[0, 0])
        x = r.uniform(0, 1024)  # the bed: only sparse short dashes where a tamped layer edge shows (round 2b: continuous bed strokes
        # still drew fine regular lines at the wide camera, the plank look)
        while x < 1024 + 200:
            L = r.uniform(5, 15) * CM
            t.stroke(along(i, y + h, x, x + L)[:3], 'pencil', 2, R['dark'], 0.25, taper=[0, 0])
            x += L + r.uniform(40, 120) * CM
        for _ in range(int(h * 1.1)):  # tamping pits in the lift: round dents in loose rows
            px = r.uniform(0, 1024); py = y + h * r.uniform(0.25, 0.8) + bed(i, px)
            s = r.uniform(5, 11)
            t.stroke([(px, py), (px + 0.6, py + 0.4)], 'ink', s * 0.6, r.choice([R['dark'], R['lines']]), r.uniform(0.3, 0.5), taper=[0, 0])
            t.stroke([(px - s * 0.25, py - s * 0.3), (px + s * 0.25, py - s * 0.3)], 'pencil', 1.5, R['light'], 0.35, taper=[0, 0])
        y += h
    for _ in range(int(pocks * 1.6)):  # grit and small pits (the earth's grain at 1-3 cm)
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + 0.6, y + 0.4)], 'ink', r.uniform(3, 6), r.choice([R['dark'], R['light'], R['lines']]), r.uniform(0.35, 0.55), taper=[0, 0])
    t.stage = 3
    for _ in range(45):  # crumbled patches that break the beds
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(20, 55), 'oil', r.uniform(18, 36), r.choice([R['dark'], R['light']]), r.uniform(0.25, 0.4), 3)
    for _ in range(5):  # put-log holes in a loose row (formwork poles), dark
        x, y = r.uniform(0, 1024), r.choice([256, 640, 896]) + r.uniform(-20, 20)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(14, 20), '#3e3020' if not soot else '#1c1512', 0.85, taper=[0, 0])
    for _ in range(40):  # runnels down the face, crossing the beds
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke(t.wobble(x, y, x + r.uniform(-8, 8), y + r.uniform(60, 180), 5, 2), 'oil', r.uniform(4, 8), r.choice([R['dark'], R['mid']]), r.uniform(0.2, 0.35))
    if soot:  # smoke and soot: soft vertical stains rising up the face
        for _ in range(45):
            x, y = r.uniform(0, 1024), r.uniform(0, 1024)
            t.stroke(t.wobble(x, y, x + r.uniform(-20, 20), y - r.uniform(120, 300), 5, 8), 'soft', r.uniform(30, 70), r.choice(['#2a2220', '#3a2e28']), r.uniform(0.15, 0.3), pressure=[1, 0.6, 0.15])
    return t


def rammed_earth(): return layered_earth('rammed_earth', EARTH, 601, 10, 30)   # round 2b: thick uneven lifts (lead review)
def rammed_earth_core(): return layered_earth('rammed_earth_core', CORE, 602, 5, 6, soot=True, thick=0.0)   # the core's 5-6 cm layers (asset list), no thick lifts
def earth_burnt(): return layered_earth('earth_burnt', BURNT, 603, 10, 30, soot=True)


def river_stone():
    """River-stone footing under rammed-earth walls and terraces: rounded cobbles 10-25 cm in earth mortar."""
    t = P.Tex('river_stone', '#5b5246', True, True, 611)
    r = t.r
    placed = []
    for _ in range(20000):
        if len(placed) >= 700: break
        x, y, rad = r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(5, 12.5) * CM
        ok = True
        for px, py, pr in placed:
            dx = min(abs(x - px), 1024 - abs(x - px)); dy = min(abs(y - py), 1024 - abs(y - py))
            if dx * dx + dy * dy < (rad + pr + 2) ** 2: ok = False; break
        if ok: placed.append((x, y, rad))
    t.stage = 1
    for _ in range(40):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(50, 120), 'sponge', 80, r.choice(['#4c443a', '#6a5f50']), 0.4, 3)
    t.stage = 2
    for x, y, rad in placed:  # each cobble: a solid rounded body of its own tone, a lighter worn crown, a dark bedding line under it
        c = r.choice(STONE); sq = r.uniform(0.7, 1.0); a0 = r.uniform(-0.4, 0.4)
        L = rad * (1 - sq) * 1.2
        t.stroke([(x - math.cos(a0) * L, y - math.sin(a0) * L), (x + math.cos(a0) * L + 0.5, y + math.sin(a0) * L)], 'ink', rad * 2 * sq, c, 1.0, taper=[0, 0])
        t.stroke([(x - math.cos(a0) * L * 0.6, y - math.sin(a0) * L * 0.6), (x + math.cos(a0) * L * 0.6 + 0.5, y + math.sin(a0) * L * 0.6)], 'oil', rad * 1.1 * sq, r.choice(STONE), 0.5, taper=[0, 0])
    t.stage = 3
    for _ in range(260):  # grit and lichen-free wear specks
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(-8, 8), y + r.uniform(-8, 8))], 'chalk', r.uniform(3, 6), r.choice(['#a9a59b', '#5c564c']), 0.45)
    return t


def stone_paving():
    """Court paving: rough-dressed limestone slabs in running courses (0.5-0.7 m deep, 0.8-1.3 m long), 1.5 cm joints."""
    t = P.Tex('stone_paving', '#8e8a80', True, True, 621)
    r = t.r
    rows = []
    while sum(rows) < 400: rows.append(r.choice([50, 60, 70]))
    k = 400 / sum(rows); rows = [h * k * CM for h in rows]
    slabs, y = [], 0.0
    for h in rows:
        x = r.uniform(0, 1024); start = x; ws = []
        while sum(ws) < 400: ws.append(r.uniform(80, 130))
        kk = 400 / sum(ws)
        for w in ws:
            w = w * kk * CM; slabs.append((x, y, w, h)); x += w
        y += h
    t.stage = 1
    for x, y, w, h in slabs:  # each slab its own tone, filled with horizontal strokes
        # round 2 (lead review: the 4 m repeat read as a grid across the court): slab tones from a narrow ramp (lum spread ~10, was ~45:
        # a few very light and very dark slabs made the same blocks show every 4 m); the slab's life is in the chisel work, not its tone
        c = r.choice(SLAB); yy = y + 6
        while yy < y + h - 4:
            t.stroke(t.wobble(x + 4, yy, x + w - 4, yy, 4, 1.2), 'flat-bristle', 16, c, 0.9, taper=[0, 0]); yy += 11
    t.stage = 2
    for x, y, w, h in slabs:  # chisel dressing: short parallel strokes in patches, a different angle per slab
        a = r.uniform(-0.6, 0.6) + r.choice([0, math.pi / 2])
        for _ in range(int(w * h / 550)):
            cx, cy = r.uniform(x + 8, x + w - 8), r.uniform(y + 8, y + h - 8); L = r.uniform(4, 12) * CM
            t.stroke([(cx, cy), (cx + math.cos(a) * L, cy + math.sin(a) * L)], 'chalk', r.uniform(3, 6), r.choice(['#67645c', '#aeaaa0', '#77746b']), r.uniform(0.35, 0.6))
    t.stage = 3
    for x, y, w, h in slabs:  # joints: dark mortar line on the top and left edge of each slab (tiles cover every edge once)
        t.stroke(t.wobble(x, y, x + w, y, 5, 0.8), 'marker', 5, '#47433c', 0.9, taper=[0, 0])
        t.stroke(t.wobble(x, y, x, y + h, 4, 0.8), 'marker', 5, '#47433c', 0.9, taper=[0, 0])
        for _ in range(2):  # chipped arrises
            ex = r.uniform(x, x + w)
            t.stroke([(ex, y + 3), (ex + r.uniform(6, 16), y + 4)], 'chalk', 4, '#5e5a52', 0.5)
    for _ in range(260):  # pitting in the stone, spread evenly (fine detail does not show a repeat)
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 6), '#5f5b53', r.uniform(0.5, 0.8), taper=[0, 0])
    for _ in range(40):  # wear and stains (faint: broad marks are what a repeat shows)
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(20, 60), 'sponge', 40, r.choice(['#7a766c', '#a19d92']), 0.12, 2)
    return t


def floor_tiles():
    """Corridor floor: square fired-clay tiles 40 cm (10 per 4 m) with stamped patterns, lozenge, 米-grid and square grid, on a diagonal
    rotation; grey earthenware, incised pattern lines (no light painted in)."""
    t = P.Tex('floor_tiles', '#76726a', True, True, 631)
    r = t.r
    S = 102.4
    G = '#5c5951'; L = '#8b877e'
    t.stage = 1
    for i in range(10):
        for j in range(10):
            x, y = i * S, j * S; c = r.choice(['#7a766e', '#6f6b63', '#827e75', '#74706a'])
            for k in range(6):
                yy = y + 10 + k * 15
                t.stroke(t.wobble(x + 6, yy, x + S - 6, yy, 3, 1.0), 'flat-bristle', 18, c, 0.85, taper=[0, 0])
    t.stage = 2
    for i in range(10):
        for j in range(10):
            x, y = i * S, j * S; kind = (i + 2 * j) % 3; m = 12
            x0, y0, x1, y1 = x + m, y + m, x + S - m, y + S - m
            t.stroke([(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)], 'pencil', 3, G, 0.7, taper=[0, 0])   # stamped border
            cx, cy = x + S / 2, y + S / 2
            if kind == 0:  # lozenge lattice: 2 x 2 lozenges and a centre lozenge
                t.stroke([(x0, cy), (cx, y0), (x1, cy), (cx, y1), (x0, cy)], 'pencil', 3, G, 0.75, taper=[0, 0])
                h = (x1 - x0) / 4
                t.stroke([(cx - h, cy), (cx, cy - h), (cx + h, cy), (cx, cy + h), (cx - h, cy)], 'pencil', 3, G, 0.75, taper=[0, 0])
                t.stroke([(x0 + 1.5, cy + 1.5), (cx + 1.5, y0 + 1.5)], 'pencil', 2, L, 0.5, taper=[0, 0])
            elif kind == 1:  # 米 grid
                for (a, b, c2, d) in ((x0, cy, x1, cy), (cx, y0, cx, y1), (x0, y0, x1, y1), (x0, y1, x1, y0)):
                    t.stroke([(a, b), (c2, d)], 'pencil', 3, G, 0.75, taper=[0, 0])
                    t.stroke([(a + 1.5, b + 1.5), (c2 + 1.5, d + 1.5)], 'pencil', 2, L, 0.45, taper=[0, 0])
            else:  # square grid: nested squares 回
                for f in (0.62, 0.3):
                    h = (x1 - x0) / 2 * f
                    t.stroke([(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx - h, cy - h)], 'pencil', 3, G, 0.75, taper=[0, 0])
                t.stroke([(cx - 2, cy), (cx + 2, cy)], 'ink', 6, G, 0.8, taper=[0, 0])
    t.stage = 3
    for i in range(11):  # joints
        x0 = r.uniform(0, 1024)
        t.stroke([(i * S, 0), (i * S, 1024)], 'marker', 5, '#45423c', 0.9, taper=[0, 0], wrap=i in (0, 10))
        t.stroke([(0, i * S), (1024, i * S)], 'marker', 5, '#45423c', 0.9, taper=[0, 0], wrap=i in (0, 10))
    for _ in range(220):  # wear: footfall polish and chips
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); a = r.uniform(0, math.tau); Ln = r.uniform(10, 34)
        t.stroke([(x, y), (x + math.cos(a) * Ln, y + math.sin(a) * Ln)], 'chalk', r.uniform(4, 9), r.choice(['#8d8980', '#5f5c55']), r.uniform(0.3, 0.5))
    return t


def dragon(t, x0, x1, yc, amp, d, c_dark, c_light):
    """our own stamped dragon for the hollow bricks: an S-body with scale dabs, a long head with open jaws, three hooked legs, a curl tail."""
    r = t.r
    n = 30; pts = []
    for i in range(n + 1):
        a = i / n
        pts.append((x0 + (x1 - x0) * a, yc + math.sin(a * math.pi * 2.2) * amp))
    if d < 0: pts = [(x0 + x1 - x, y) for x, y in pts]
    t.stroke(pts, 'ink', 20, c_dark, 0.85, taper=[6, 20])
    t.stroke([(x + 1.5, y - 3) for x, y in pts], 'ink', 6, c_light, 0.6, taper=[6, 20])
    for i in range(3, n - 4, 2):  # scales
        x, y = pts[i]
        t.stroke([(x - 3, y - 3), (x, y + 2), (x + 3, y - 3)], 'pencil', 2, c_light, 0.5, taper=[0, 0])
    hx, hy = pts[0]; s = -d  # head at the start, facing outward
    t.stroke([(hx - s * 4, hy), (hx + s * 6, hy)], 'ink', 26, c_dark, 0.9, taper=[0, 0])                            # head mass
    t.stroke([(hx, hy - 4), (hx + s * 22, hy - 10), (hx + s * 36, hy - 6)], 'ink', 10, c_dark, 0.9, taper=[0, 4])   # upper jaw
    t.stroke([(hx, hy + 6), (hx + s * 20, hy + 14), (hx + s * 32, hy + 18)], 'ink', 7, c_dark, 0.9, taper=[0, 4])   # lower jaw
    t.stroke([(hx - s * 2, hy - 6), (hx - s * 12, hy - 20), (hx - s * 20, hy - 22)], 'ink', 4, c_dark, 0.8, taper=[0, 6])  # horn
    t.stroke([(hx + s * 10, hy - 4), (hx + s * 11, hy - 3)], 'ink', 4, c_light, 0.9, taper=[0, 0])  # eye
    for i in (8, 16, 23):  # legs with three-claw feet
        x, y = pts[i]; dn = 1 if r.random() < 0.6 else -1
        fx, fy = x + s * 8, y + dn * 22
        t.stroke([(x, y), (x + s * 4, y + dn * 12), (fx, fy)], 'ink', 5, c_dark, 0.8, taper=[0, 2])
        for k in (-1, 0, 1):
            t.stroke([(fx, fy), (fx + s * 6 + k * 4, fy + dn * 5)], 'pencil', 2, c_dark, 0.8, taper=[0, 0])
    tx, ty = pts[-1]  # tail curl
    curl = [(tx + math.cos(a) * 10 * (1 - a / 12) * -s, ty - 10 + math.sin(a) * 10 * (1 - a / 12)) for a in [k * 0.5 for k in range(14)]]
    t.stroke(curl, 'ink', 4, c_dark, 0.8, taper=[0, 6])


def hollow_brick():
    """Hollow-brick parapet and stair-tread faces 空心砖: grey earthenware bricks 133 x 40 cm, staggered, each with a stamped frame of
    dot rings and our own dragon. Rows wrap; 10 rows per 4 m."""
    t = P.Tex('hollow_brick', '#86827a', True, True, 641)
    r = t.r
    H, W = 102.4, 1024 / 3
    D, Lt = '#5d5951', '#a29e94'
    t.stage = 1
    for j in range(10):
        off = (W / 2) * (j % 2)
        for i in range(3):
            x, y = off + i * W, j * H; c = r.choice(['#8a867e', '#7f7b73', '#918d84', '#858178'])
            for k in range(5):
                yy = y + 12 + k * 19
                t.stroke(t.wobble(x + 6, yy, x + W - 6, yy, 6, 1.0), 'flat-bristle', 22, c, 0.85, taper=[0, 0])
    t.stage = 2
    for j in range(10):
        off = (W / 2) * (j % 2)
        for i in range(3):
            x, y = off + i * W, j * H
            m = 9
            t.stroke([(x + m, y + m), (x + W - m, y + m), (x + W - m, y + H - m), (x + m, y + H - m), (x + m, y + m)], 'pencil', 3, D, 0.75, taper=[0, 0])
            for k in range(14):  # stamped dot rings along top and bottom borders
                px = x + 18 + k * (W - 36) / 13
                for py in (y + 17, y + H - 17):
                    t.stroke([(px - 3, py), (px, py - 3), (px + 3, py), (px, py + 3), (px - 3, py)], 'pencil', 2, D, 0.65, taper=[0, 0])
            dragon(t, x + 60, x + W - 40, y + H / 2, 18, 1 if (i + j) % 2 else -1, D, Lt)
    t.stage = 3
    for j in range(11):  # bed joints
        t.stroke([(0, j * H), (1024, j * H)], 'marker', 5, '#4d4943', 0.9, taper=[0, 0], wrap=j in (0, 10))
    for j in range(10):  # head joints
        off = (W / 2) * (j % 2)
        for i in range(3):
            x = off + i * W
            t.stroke([(x, j * H), (x, j * H + H)], 'marker', 5, '#4d4943', 0.9, taper=[0, 0])
    for _ in range(150):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(-12, 12), y + r.uniform(-4, 4))], 'chalk', r.uniform(4, 8), r.choice([Lt, '#6c6860']), 0.4)
    return t


def plaster_body(t, y0, y1, burnt=False):
    """lime plaster mottling and trowel strokes between rows y0-y1 (as the approved hall wall, our own pass)."""
    r = t.r
    cols = [P.pk(c) for c in ['#9f927a', '#c9bea7', '#a89a80', '#bdb099']] if not burnt else ['#7d7262', '#958a78', '#6e6456', '#8a7f6d']
    for _ in range(int(80 * (y1 - y0) / 590)):
        t.blot(r.uniform(0, 1024), r.uniform(y0, y1), r.uniform(40, 110), 'sponge', r.uniform(50, 110), r.choice(cols), r.uniform(0.35, 0.55), 3)
    tr = [P.pk(c) for c in ['#9a8d75', '#d0c5ae', '#a99c83']] if not burnt else ['#6a6052', '#a09583', '#7a6f60']
    for _ in range(int(700 * (y1 - y0) / 590)):
        x, y = r.uniform(0, 1024), r.uniform(y0, y1); a = r.uniform(-0.6, 0.6); L = r.uniform(25, 80)
        t.stroke(t.wobble(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 3, 2), 'oil', r.uniform(10, 24), r.choice(tr), r.uniform(0.4, 0.6))


def chariot(t, x, base, s=1.0):
    """a four-horse chariot with a canopy and a driver, side view, facing right (our own brush drawing)."""
    K_, R_, O_ = '#1b1714', '#8a3020', '#9c6a36'
    for h in range(4):  # horses, overlapping, alternately black and ochre
        hx = x + 30 * s + h * 14 * s; c = K_ if h % 2 == 0 else O_
        body = [(hx, base - 70 * s), (hx + 70 * s, base - 74 * s)]
        t.stroke(body, 'flat-bristle', 30 * s, c, 0.95, taper=[6, 6])
        t.stroke([(hx + 66 * s, base - 80 * s), (hx + 82 * s, base - 112 * s), (hx + 96 * s, base - 108 * s)], 'ink', 12 * s, c, 0.95, taper=[0, 6])  # neck and head
        for lx, kx in ((hx + 6 * s, -8), (hx + 18 * s, 6), (hx + 56 * s, 10), (hx + 66 * s, -6)):
            t.stroke([(lx, base - 62 * s), (lx + kx * s * 0.6, base - 30 * s), (lx + kx * s, base)], 'ink', 5 * s, c, 0.95, taper=[0, 2])
        t.stroke([(hx - 2, base - 74 * s), (hx - 12 * s, base - 50 * s)], 'ink', 4 * s, c, 0.9, taper=[0, 4])  # tail
    t.stroke([(x + 30 * s, base - 86 * s), (x - 40 * s, base - 70 * s)], 'ink', 4 * s, K_, 0.9, taper=[0, 0])  # shaft and reins
    cx = x - 70 * s  # car, wheel, canopy, driver
    t.stroke([(cx - 34 * s, base - 64 * s), (cx + 34 * s, base - 64 * s)], 'flat-bristle', 26 * s, R_, 0.95, taper=[0, 0])
    wheel = [(cx + math.cos(a) * 34 * s, base - 34 * s + math.sin(a) * 34 * s) for a in [k * math.tau / 24 for k in range(25)]]
    t.stroke(wheel, 'ink', 5 * s, K_, 0.95, taper=[0, 0])
    for k in range(6):
        a = k * math.pi / 6
        t.stroke([(cx - math.cos(a) * 32 * s, base - 34 * s - math.sin(a) * 32 * s), (cx + math.cos(a) * 32 * s, base - 34 * s + math.sin(a) * 32 * s)], 'pencil', 2.5 * s, K_, 0.85, taper=[0, 0])
    t.stroke([(cx, base - 64 * s), (cx, base - 150 * s)], 'pencil', 3 * s, K_, 0.9, taper=[0, 0])  # canopy pole
    t.stroke([(cx - 46 * s, base - 140 * s), (cx, base - 158 * s), (cx + 46 * s, base - 140 * s)], 'flat-bristle', 12 * s, O_, 0.95, taper=[4, 4])
    figure(t, cx + 10 * s, base - 76 * s, 0.6 * s, K_, R_)


def figure(t, x, foot, s, c1, c2, weapon=False):
    """a standing figure in a long robe, side view: head, cap, robe as a tapering block, arms; our own drawing."""
    t.stroke([(x, foot - 150 * s), (x, foot - 151 * s)], 'ink', 22 * s, c1, 0.95, taper=[0, 0])                      # head
    t.stroke([(x - 8 * s, foot - 164 * s), (x + 10 * s, foot - 168 * s)], 'ink', 8 * s, c1, 0.95, taper=[0, 0])       # cap
    t.stroke([(x, foot - 136 * s), (x - 2 * s, foot - 70 * s), (x - 6 * s, foot - 4 * s)], 'flat-bristle', 34 * s, c2, 0.95, taper=[0, 0])  # robe
    t.stroke([(x - 18 * s, foot - 6 * s), (x + 16 * s, foot - 6 * s)], 'ink', 8 * s, c2, 0.95, taper=[0, 0])
    t.stroke([(x + 4 * s, foot - 120 * s), (x + 22 * s, foot - 96 * s)], 'ink', 9 * s, c1, 0.95, taper=[0, 3])         # arm
    t.stroke([(x - 14 * s, foot - 110 * s), (x + 12 * s, foot - 110 * s)], 'pencil', 3 * s, c1, 0.8, taper=[0, 0])     # belt line
    if weapon:  # a halberd 戟: shaft, side blade
        t.stroke([(x + 22 * s, foot), (x + 22 * s, foot - 230 * s)], 'pencil', 4 * s, '#1b1714', 0.95, taper=[0, 0])
        t.stroke([(x + 22 * s, foot - 205 * s), (x + 44 * s, foot - 212 * s), (x + 22 * s, foot - 196 * s)], 'ink', 5 * s, '#1b1714', 0.95, taper=[0, 0])
        t.stroke([(x + 22 * s, foot - 230 * s), (x + 22 * s, foot - 250 * s)], 'ink', 5 * s, '#1b1714', 0.95, taper=[0, 6])


def strange_beast(t, x, base, s):
    """a winged long-tailed beast (the murals' 'strange animals'), our own drawing: deer legs, tiger body, wing, curled tail."""
    G_, K_ = '#4d6a55', '#1b1714'
    t.stroke([(x, base - 60 * s), (x + 80 * s, base - 64 * s)], 'flat-bristle', 30 * s, G_, 0.95, taper=[8, 8])
    for lx in (x + 6 * s, x + 20 * s, x + 64 * s, x + 76 * s):
        t.stroke([(lx, base - 52 * s), (lx + 4 * s, base - 22 * s), (lx, base)], 'ink', 5 * s, K_, 0.95, taper=[0, 2])
    t.stroke([(x + 78 * s, base - 72 * s), (x + 96 * s, base - 100 * s), (x + 114 * s, base - 96 * s)], 'ink', 11 * s, G_, 0.95, taper=[0, 6])
    t.stroke([(x + 96 * s, base - 104 * s), (x + 90 * s, base - 128 * s), (x + 100 * s, base - 140 * s)], 'pencil', 3 * s, K_, 0.9, taper=[0, 4])  # antler
    t.stroke([(x + 30 * s, base - 72 * s), (x + 20 * s, base - 120 * s), (x + 60 * s, base - 106 * s), (x + 50 * s, base - 76 * s)], 'ink', 8 * s, '#8a3020', 0.95, taper=[0, 4])  # wing
    tail = [(x - math.cos(a) * 26 * s * (1 - a / 10), base - 70 * s - 26 * s + math.sin(a) * 26 * s * (1 - a / 10)) for a in [k * 0.45 for k in range(16)]]
    t.stroke([(x, base - 62 * s)] + tail, 'ink', 6 * s, K_, 0.95, taper=[0, 6])
    t.stroke([(x + 104 * s, base - 98 * s), (x + 105 * s, base - 97 * s)], 'ink', 4 * s, '#d6ccb6', 1.0, taper=[0, 0])


def wall_rows(t, burnt=False, mural=False):
    """the approved hall wall's rows (A2): black cornice 0-40, a band, red rule, lime plaster 170-760, red rule, black dado 772-1024.
    mural True: a 1.5 m mural band 50-430 (corridor walls, A10); burnt True: soot, spalls to the reddened earth, a charred dado (A18)."""
    r = t.r
    t.stage = 1
    plaster_body(t, 442 if mural else 170, 760, burnt)
    if mural:
        P.band(t, 50, 430, '#d6ccb6', 'flat-bristle', 40, 1.0, 26, 1.5)   # white ground
        for _ in range(60):
            x, y = r.uniform(0, 1024), r.uniform(60, 420)
            t.stroke(t.wobble(x, y, x + r.uniform(30, 70), y + r.uniform(-4, 4), 3, 1.5), 'oil', r.uniform(10, 20), r.choice(['#cfc4ad', '#ddd4c0']), 0.5)
        t.stage = 2
        base = 400
        chariot(t, 360, base, 1.0)
        figure(t, 470, base, 0.95, '#1b1714', '#1b1714', weapon=True)
        figure(t, 540, base, 0.95, '#1b1714', '#8a3020', weapon=True)
        figure(t, 640, base, 0.9, '#1b1714', '#9c6a36')
        figure(t, 700, base, 0.9, '#1b1714', '#4d6a55')
        strange_beast(t, 790, base, 1.15)
        figure(t, 990, base, 0.95, '#1b1714', '#1b1714', weapon=True)
        x0 = r.uniform(0, 1024)
        t.stroke(t.wobble(x0, base + 6, x0 + 1100, base + 6, 12, 1.5), 'dry-brush', 6, '#9c6a36', 0.8, taper=[0, 0])  # ground line
        for i in range(8):  # a row of cloud scrolls above the procession
            P.cloud(t, 64 + i * 128, 110, 30, '#9c6a36')
        figure(t, 40, base, 0.9, '#1b1714', '#8a3020')
        figure(t, 100, base, 0.9, '#1b1714', '#1b1714')
        strange_beast(t, 140, base, 0.85)
        P.band(t, 40, 52, '#7e271b', 'marker', 12, 1.0, 12, 0.8)
        P.band(t, 430, 442, '#7e271b', 'marker', 12, 1.0, 12, 0.8)
    else:
        P.band(t, 40, 150, '#d6ccb6' if not burnt else '#8f8472', 'flat-bristle', 40, 1.0, 26, 1.5)
        w = 1024 / 16
        for i in range(16):
            cx, yc, hh = (i + 0.5) * w, 95, 42
            t.stroke([(cx - w / 2 + 4, yc), (cx, yc - hh), (cx + w / 2 - 4, yc), (cx, yc + hh), (cx - w / 2 + 4, yc)], 'marker', 7, '#1b1714', 0.9, taper=[0, 0])
            t.stroke([(cx - w / 4, yc), (cx, yc - hh / 2), (cx + w / 4, yc), (cx, yc + hh / 2), (cx - w / 4, yc)], 'marker', 9, '#1b1714', 0.9, taper=[0, 0])
        P.band(t, 150, 162, '#7e271b' if not burnt else '#4e2018', 'marker', 12, 1.0, 12, 0.8)
    P.band(t, 0, 40, '#17120f', 'flat-bristle', 30, 1.0, 14, 1)
    P.band(t, 760, 772, '#7e271b' if not burnt else '#4e2018', 'marker', 12, 1.0, 12, 0.8)
    P.band(t, 772, 1024, '#1a1512' if not burnt else '#100d0c', 'flat-bristle', 50, 1.0, 26, 2)
    t.stage = 3
    for _ in range(60):
        x, y = r.uniform(0, 1024), r.uniform(790, 1010)
        t.stroke(t.wobble(x, y, x + r.uniform(40, 160), y + r.uniform(-4, 4), 4, 1.5), 'dry-brush', r.uniform(6, 14), r.choice(['#2e2722', '#262019']), r.uniform(0.3, 0.6))
    if burnt:
        for _ in range(6):  # spalled plaster: a jagged patch of fire-reddened earth with its layer lines, a pale broken plaster edge
            cx, cy, w, h = r.uniform(0, 1024), r.uniform(280, 660), r.uniform(90, 190), r.uniform(60, 130)
            edge = [(cx + math.cos(a) * w * 0.5 * r.uniform(0.55, 1.0), cy + math.sin(a) * h * 0.5 * r.uniform(0.55, 1.0)) for a in [k * math.tau / 11 for k in range(11)]]
            edge.append(edge[0])
            y = cy - h / 2
            while y < cy + h / 2:  # fill the patch row by row inside the jagged outline
                xs = []
                for (x1, y1), (x2, y2) in zip(edge, edge[1:]):
                    if (y1 - y) * (y2 - y) < 0: xs.append(x1 + (x2 - x1) * (y - y1) / (y2 - y1))
                xs.sort()
                for xa, xb in zip(xs[0::2], xs[1::2]):
                    t.stroke([(xa, y), (xb, y)], 'oil', 9, r.choice(['#7e5444', '#74493b', '#6c4538']), 0.95, taper=[0, 0])
                y += 6
            for k in range(int(h / 16)):
                yy = cy - h / 2 + 8 + k * 16
                t.stroke([(cx - w * 0.25, yy), (cx + w * 0.25, yy)], 'pencil', 2, '#4e2f25', 0.6, taper=[0, 0])
            t.stroke(edge, 'chalk', 4, '#b3a894', 0.65, taper=[0, 0])
        for k in range(5):  # soot collected under the cornice and over the band: overlapping washes, heaviest at the top
            y = 40 + k * 14
            while y < 420:
                for _ in range(6):
                    x0 = r.uniform(0, 1024)
                    t.stroke(t.wobble(x0, y, x0 + 300, y, 4, 6), 'soft', 60, '#1c1714', 0.5 * (1 - (y - 40) / 420), taper=[0, 0])
                y += 36
        for _ in range(16):  # plumes of soot rising from the dado, widening and fading as they rise
            x = r.uniform(0, 1024)
            for k in range(9):
                y = 750 - k * 50; x += r.uniform(-12, 12)
                t.blot(x, y, 20 + k * 7, 'oil', 30 + k * 8, '#1c1714', 0.3 - k * 0.028, 3)
        for _ in range(80):  # heat crazing in the plaster
            x, y = r.uniform(0, 1024), r.uniform(180, 740); pts = [(x, y)]
            for _ in range(4): x += r.uniform(-18, 18); y += r.uniform(-18, 18); pts.append((x, y))
            t.stroke(pts, 'pencil', 2, '#3a322b', 0.55)
        for _ in range(500):  # ash and soot flecks
            x, y = r.uniform(0, 1024), r.uniform(175, 745)
            t.stroke([(x, y), (x + r.uniform(-6, 6), y + r.uniform(-3, 3))], 'chalk', r.uniform(4, 8), r.choice(['#2a2420', '#a59a88']), 0.45)
        for _ in range(40):  # soot plumes rising from the dado and from the door gaps
            x = r.uniform(0, 1024); y = r.uniform(600, 800)
            t.stroke(t.wobble(x, y, x + r.uniform(-30, 30), y - r.uniform(200, 560), 6, 12), 'soft', r.uniform(40, 90), '#211b18', r.uniform(0.18, 0.35), pressure=[1, 0.7, 0.2])
        for _ in range(140):  # char crazing on the dado
            x, y = r.uniform(0, 1024), r.uniform(780, 1020)
            t.stroke([(x, y), (x + r.uniform(-14, 14), y + r.uniform(4, 12))], 'pencil', 2, '#050404', 0.7)
            t.stroke([(x + 3, y + 1), (x + r.uniform(6, 20), y + 1)], 'dry-brush', 4, '#3a302a', 0.45)
    else:
        for _ in range(26):
            x = r.uniform(0, 1024); y = r.uniform(445 if mural else 160, 470 if mural else 220)
            t.stroke(t.wobble(x, y, x + r.uniform(-6, 6), y + r.uniform(80, 260), 5, 2), 'soft', r.uniform(8, 18), '#8f8068', r.uniform(0.12, 0.25), pressure=[1, 0.6, 0.1])
    return t


def mural_wall(): return wall_rows(P.Tex('mural_wall', P.pk('#b9ad95'), True, False, 651), mural=True)   # plaster follows A2 (P.PLASTER_K)
def wall_burnt(): return wall_rows(P.Tex('wall_burnt', '#857a69', True, False, 652), burnt=True)


def tile_end(t, cx, cy, rad, kind):
    """瓦当 tile end, our own cloud designs: rim, a cross dividing four fields, a cloud curl in each, a centre boss."""
    D, Lt = '#353433', '#8c8a86'
    t.stroke([(cx, cy), (cx + 0.5, cy)], 'ink', rad * 2, '#575654', 1.0, taper=[0, 0])
    ring = [(cx + math.cos(a) * rad * 0.9, cy + math.sin(a) * rad * 0.9) for a in [k * math.tau / 28 for k in range(29)]]
    t.stroke(ring, 'pencil', 3, Lt, 0.9, taper=[0, 0])
    ring2 = [(cx + math.cos(a) * rad * 0.74, cy + math.sin(a) * rad * 0.74) for a in [k * math.tau / 24 for k in range(25)]]
    t.stroke(ring2, 'pencil', 2, D, 0.8, taper=[0, 0])
    if kind % 2 == 0:
        for a in (0, math.pi / 2):
            t.stroke([(cx - math.cos(a) * rad * 0.74, cy - math.sin(a) * rad * 0.74), (cx + math.cos(a) * rad * 0.74, cy + math.sin(a) * rad * 0.74)], 'pencil', 2, D, 0.8, taper=[0, 0])
    for q in range(4):
        a = q * math.pi / 2 + math.pi / 4 + (0.3 if kind >= 2 else 0)
        qx, qy = cx + math.cos(a) * rad * 0.46, cy + math.sin(a) * rad * 0.46
        curl = [(qx + math.cos(a + 2 + k * 0.6) * rad * 0.2 * (1 - k / 14), qy + math.sin(a + 2 + k * 0.6) * rad * 0.2 * (1 - k / 14)) for k in range(12)]
        t.stroke(curl, 'pencil', 2.2, Lt, 0.9, taper=[0, 3])
    t.stroke([(cx, cy), (cx + 0.5, cy)], 'ink', rad * 0.32, Lt, 0.95, taper=[0, 0])


def roof_tile():
    """Grey unglazed roof tile (A11), the tile field: the slope runs down the image: concave pan tiles 板瓦 (34 cm) and round cover tiles
    筒瓦 (16 cm) in 50 cm pairs, courses every 40 cm (10 per 4 m); wraps both ways (round 2 of the mesh work: a slope longer than one
    repeat must tile, so the tile ends moved to their own sheet, tile_ends)."""
    t = P.Tex('roof_tile', '#4c4b4b', True, True, 661)
    r = t.r
    pitch = 128; pan = 87; off = -8  # off: no dark line on the wrap edge
    t.stage = 1
    for i in range(8):
        x = i * pitch + off
        for y in range(0, 1024, 12):  # pan tile: mid grey, a little lighter to its middle (curvature by value, no light direction)
            t.stroke([(x + 6, y), (x + pan - 6, y)], 'flat-bristle', 14, r.choice(['#4e4d4c', '#53524f', '#4a4949']), 0.85, taper=[0, 0])
        t.stroke([(x + pan / 2, -20), (x + pan / 2, 1044)], 'soft', 34, '#595856', 0.35, taper=[0, 0])
    t.stage = 2
    for i in range(8):
        x = i * pitch + pan + off
        t.stroke([(x - 3, -20), (x - 3, 1044)], 'marker', 6, '#2d2c2c', 0.9, taper=[0, 0])          # gap shadow (occlusion) beside the cover tile
        t.stroke([(x + 20, -20), (x + 20, 1044)], 'marker', 34, '#5c5b58', 1.0, taper=[0, 0])  # cover tile
        t.stroke([(x + 20, -20), (x + 20, 1044)], 'oil', 12, '#6a6864', 0.6, taper=[0, 0])
        t.stroke([(x + 43, -20), (x + 43, 1044)], 'marker', 5, '#2d2c2c', 0.9, taper=[0, 0])
    for k in range(10):  # course laps: each course's lower edge over the next (102.4 px = 40 cm, so the field wraps)
        y = 90 + k * 102.4
        for i in range(8):
            x = i * pitch + off
            t.stroke(t.wobble(x + 4, y, x + pan - 4, y, 4, 1), 'marker', 4, '#323131', 0.85, taper=[0, 0])
            t.stroke([(x + pan + 4, y - 3), (x + pitch - 4, y - 3)], 'marker', 4, '#3a3938', 0.8, taper=[0, 0])
    t.stage = 3
    for _ in range(180):  # firing clouds and a few chips (soft, so the tile reads as one fired body)
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); a = r.uniform(-0.3, 0.3) + math.pi / 2; L = r.uniform(15, 40)
        t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'oil', r.uniform(8, 16), r.choice(['#454443', '#5c5a57']), r.uniform(0.3, 0.5))
    return t


def tile_ends():
    """瓦当 tile ends (A11), their own small atlas: two rows of eight 20 cm discs (our own cloud designs: rim, cross, four curls, boss)
    at rows 128 and 384, column centres 64 + 128 i; the rest is the dark eave board the disc rims map onto."""
    t = P.Tex('tile_ends', '#2a2624', True, False, 662)
    r = t.r
    t.stage = 1
    P.band(t, 0, 1024, '#2a2624', 'flat-bristle', 40, 1.0, 22, 1.5)
    for _ in range(200):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke(t.wobble(x, y, x + r.uniform(30, 90), y, 3, 1), 'oil', r.uniform(8, 16), r.choice(['#332e2b', '#221f1d']), 0.5)
    t.stage = 2
    for i in range(8):
        tile_end(t, 64 + i * 128, 128, 26, i % 4)
        tile_end(t, 64 + i * 128, 384, 26, (i + 2) % 4)
    return t


def timber():
    """Timber (A12): weathered oiled softwood for beams, trestles and posts; grain runs down the image (v), so meshes map v along each
    member's long axis; 4 m per repeat both ways."""
    t = P.Tex('timber', '#6b5039', True, True, 671)
    r = t.r
    t.stage = 1
    for _ in range(26):  # boards of different tone
        x = r.uniform(0, 1024); w = r.uniform(30, 90)
        t.stroke(t.wobble(x, -40, x + r.uniform(-6, 6), 1064, 8, 3), 'oil', w, r.choice(['#5a4230', '#7a5d42', '#523d2c', '#836446']), 0.6, taper=[0, 0])
    t.stage = 2
    for _ in range(420):  # grain: broad oil strokes along v (4-15 cm across the grain), broken into 20-60 cm pieces
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); L = r.uniform(20, 60) * CM
        t.stroke(t.wobble(x, y, x + r.uniform(-4, 4), y + L, 5, 1.2), 'oil', r.uniform(12, 30), r.choice(['#4a3625', '#8a6b4c', '#553f2c', '#7e6044']), r.uniform(0.45, 0.7))
    for _ in range(160):  # fine grain lines
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); L = r.uniform(20, 60) * CM
        t.stroke(t.wobble(x, y, x + r.uniform(-3, 3), y + L, 5, 0.8), 'pencil', 2, '#3e2d1e', r.uniform(0.3, 0.5))
    for _ in range(16):  # knots
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); a, b = r.uniform(6, 12), r.uniform(12, 24)
        ring = [(x + math.cos(k * math.tau / 16) * a, y + math.sin(k * math.tau / 16) * b) for k in range(17)]
        t.stroke(ring, 'ink', 4, '#3a2a1c', 0.8, taper=[0, 0])
        t.stroke([(x, y), (x + 0.5, y + 0.5)], 'ink', a, '#4a3624', 0.8, taper=[0, 0])
    t.stage = 3
    for _ in range(60):  # checks (drying cracks) along the grain
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke(t.wobble(x, y, x + r.uniform(-3, 3), y + r.uniform(40, 160), 5, 0.8), 'pencil', 2.2, '#2e2116', r.uniform(0.5, 0.8))
    for _ in range(120):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(-4, 4), y + r.uniform(8, 24))], 'chalk', r.uniform(3, 6), r.choice(['#957556', '#4a3626']), 0.4)
    return t


def timber_burnt():
    """Charred timber (A18): alligator char, blocks 4-9 cm split by deep cracks across and along the grain, ash-grey highlights on the
    blocks, a few patches of scorched brown; same layout and grain direction as timber (a material swap)."""
    t = P.Tex('timber_burnt', '#2a2320', True, True, 672)
    r = t.r
    t.stage = 1
    for _ in range(40):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(50, 120), 'sponge', 80, r.choice(['#3a302b', '#1d1816', '#4a3629']), 0.4, 3)
    t.stage = 2
    ws = []
    while sum(ws) < 1024: ws.append(r.uniform(14, 22) * CM)
    k = 1024 / sum(ws); ws = [w * k for w in ws]
    x = 0.0
    for w in ws:  # columns of char blocks along the grain (alligator char), each block a tone with a grey sheen
        y = r.uniform(0, 30)
        while y < 1024 + 30:
            h = r.uniform(7, 14) * CM
            t.stroke([(x + w * 0.5, y + h * 0.15), (x + w * 0.5 + r.uniform(-2, 2), y + h * 0.85)], 'marker', w * 1.0, r.choice(['#3b322d', '#362e29', '#3f352f', '#332b26']), 0.85, taper=[0, 0])
            t.stroke([(x + w * 0.35, y + h * 0.3), (x + w * 0.45, y + h * 0.6)], 'soft', w * 0.4, r.choice(['#4e4640', '#58504a']), 0.3, taper=[0, 0])
            t.stroke(t.wobble(x, y + h, x + w, y + h, 3, 2), 'ink', 5, '#0b0908', 0.95, taper=[0, 0])  # cross crack
            y += h
        t.stroke(t.wobble(x, -20, x + r.uniform(-3, 3), 1044, 10, 1.5), 'ink', 4, '#0b0908', 0.9, taper=[0, 0])  # long crack
        x += w
    t.stage = 3
    for _ in range(30):  # scorched brown where the char is thin
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(20, 50), 'sponge', 40, '#5a3e2a', 0.35, 2)
    for _ in range(60):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(-3, 3), y + r.uniform(4, 12))], 'chalk', 3, '#77706a', 0.4)
    return t


def mercury_matcap():
    """Mercury (A14): a chrome matcap (a lit sphere seen head-on), the only bright cool reflective surface. Disc radius 500 px on black.
    Round 3: at the game camera (pitch 40) a floor-level pool samples the matcap's upper part (normals tilted toward the camera's up),
    so that part holds what the pool mirrors in a dark hall: the dark ceiling with bright lamp streaks; the middle is bright silver
    (normals facing the eye), the lower half darker, a cool rim light at the bottom. Rounds 1-2 (a light disc, then a pale sky top)
    read as white paint on screen."""
    t = P.Tex('mercury_matcap', '#0a0c0e', False, False, 681)
    r = t.r
    def ring(rad, c, size, op, brush='oil', a0=0.0, a1=math.tau, cx=512, cy=512):
        n = max(12, int(rad / 6)); pts = [(cx + math.cos(a0 + (a1 - a0) * k / n) * rad, cy + math.sin(a0 + (a1 - a0) * k / n) * rad) for k in range(n + 1)]
        t.stroke(pts, brush, size, c, op, taper=[0, 0], wrap=False)
    def row(y, c, size, op, brush='soft'):
        half = math.sqrt(max(0, 492 ** 2 - (y - 512) ** 2))
        if half > 4: t.stroke([(512 - half, y), (512 + half, y)], brush, size, c, op, taper=[0, 0], wrap=False)
    t.stage = 0
    t.stroke([(512, 512), (512.5, 512)], 'ink', 1000, '#3c4046', 1.0, taper=[0, 0], wrap=False)
    for y in range(24, 1000, 10):  # value down the disc: dark ceiling band on top, bright silver middle, darker floor half
        f = y / 1024
        v = MERC_LIFT[0] + MERC_LIFT[1] * math.exp(-((f - 0.5) / 0.17) ** 2) if f > 0.28 else MERC_LIFT[2] + 24 * f
        if f > 0.62: v = MERC_LIFT[0] + MERC_LIFT[3] * math.exp(-((f - 0.5) / 0.2) ** 2)
        v = min(v, 246)
        row(y, '#%02x%02x%02x' % (int(v - 4), int(v), int(v + 5)), 22, 1.0, 'marker')
    t.stage = 1
    for k, y in enumerate((70, 110, 150, 196, 236, 268)):  # lamp streaks reflected from the ceiling (ripples sweep the pool across them)
        half = math.sqrt(max(0, 470 ** 2 - (y - 512) ** 2)) * r.uniform(0.35, 0.8); cx = 512 + r.uniform(-80, 80)
        t.stroke([(cx - half, y), (cx + half, y)], 'soft', r.uniform(10, 18), '#f2f5f8', 0.95, taper=[0, 0], wrap=False)
    t.stage = 2
    t.stroke([(400, 430), (400.5, 430)], 'ink', 90, '#f4f6f8', 1.0, taper=[0, 0], wrap=False)    # the main highlight
    for rad in range(50, 200, 10):
        ring(rad, '#e8edf1', 22, 0.55 * (1 - rad / 210), 'soft', cx=400, cy=430)
    ring(462, '#d6dee6', 24, 0.9, 'soft', math.radians(35), math.radians(145))  # cool rim light along the bottom
    ring(494, '#2a3038', 16, 1.0, 'marker')                                       # dark outer rim
    t.stage = 3
    for _ in range(30):  # soft ripples
        a = r.uniform(0, math.tau); rr = r.uniform(120, 440)
        ring(rr, r.choice(['#9aa2aa', '#d2d8de']), r.uniform(4, 8), 0.3, 'soft', a, a + r.uniform(0.2, 0.6))
    return t


def black_lake():
    """Black lake (A15): near-black with a blue-green tint (#0E1A1C), never the black of cloth; short ripple strokes, a few cool glints."""
    t = P.Tex('black_lake', '#0f1b1d', True, True, 691)
    r = t.r
    t.stage = 1
    for _ in range(60):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(70, 160), 'sponge', 120, r.choice(['#0b1517', '#13252a', '#102022']), 0.5, 3)
    t.stage = 2
    for _ in range(2600):  # ripples: short, mostly horizontal, 4-15 cm; crests lighter, troughs darker
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); L = r.uniform(4, 15) * CM; a = r.uniform(-0.15, 0.15)
        t.stroke(t.wobble(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 3, 1.0), 'ink', r.uniform(3, 7), r.choice(['#25403f', '#050b0b', '#2b4848', '#060d0e']), r.uniform(0.6, 0.9), taper=[2, 2])
    t.stage = 3
    for _ in range(140):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(6, 18), y)], 'chalk', 3, '#3b5a5e', r.uniform(0.4, 0.7))
    return t


def garden_ground():
    """Garden ground (A16): beaten loess with fine gravel, sparse grass tufts and damp patches near the ponds."""
    t = P.Tex('garden_ground', '#7a6a50', True, True, 701)
    r = t.r
    t.stage = 1
    for _ in range(80):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(50, 140), 'sponge', r.uniform(60, 120), r.choice(['#6c5d45', '#86765a', '#5f5a42', '#71634a']), r.uniform(0.3, 0.5), 3)
    t.stage = 2
    for _ in range(2400):  # gravel: solid little stones
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(-3, 3), y + r.uniform(-2, 2))], 'ink', r.uniform(3, 7), r.choice(['#a5957a', '#54483a', '#b3a68e', '#665a48']), r.uniform(0.7, 0.95), taper=[0, 0])
    for _ in range(150):  # grass tufts
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); c = r.choice(['#5d6a3e', '#6d7746', '#58603a'])
        for _ in range(r.randint(4, 7)):
            a = -math.pi / 2 + r.uniform(-0.7, 0.7); L = r.uniform(10, 24)
            t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'ink', r.uniform(2, 3.5), c, 0.85, taper=[0, 6])
    t.stage = 3
    for _ in range(30):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(20, 60), y + r.uniform(-6, 6))], 'pencil', 2, '#4b3f30', 0.5)
    return t


def wheat(t, x, foot, h, lean, c_stalk, c_ear):
    """one wheat stalk with an ear of paired grains and awns (the wheat-ear mural motif, our own drawing)."""
    r = t.r
    top = (x + lean * h * 0.3, foot - h)
    mid = (x + lean * h * 0.08, foot - h * 0.5)
    t.stroke([(x, foot), mid, top], 'ink', 3, c_stalk, 1.0, taper=[0, 2])
    for k in range(7):  # grains climbing the ear
        f = k / 7; gx = top[0] + lean * 4 * f; gy = top[1] - 4 - f * h * 0.28
        for s in (-1, 1):
            t.stroke([(gx, gy), (gx + s * 6, gy - 6)], 'ink', 6, c_ear, 1.0, taper=[0, 3])
            t.stroke([(gx + s * 6, gy - 6), (gx + s * 11, gy - 22)], 'pencil', 1.5, c_ear, 1.0, taper=[0, 0])
    for s in (-1, 1):  # two leaves
        y0 = foot - h * r.uniform(0.2, 0.4)
        t.stroke([(x, y0), (x + s * h * 0.18, y0 - h * 0.12), (x + s * h * 0.3, y0 - h * 0.05)], 'ink', 5, c_stalk, 1.0, taper=[0, 10])


def garden_plants():
    """Planting cards (A16), alpha-tested: a 4 x 4 atlas of 1 m cells (256 px). Row 0 wheat clumps, row 1 millet and reeds, row 2 low
    shrubs, row 3 grass tufts. Opaque strokes on transparent ground; the bottom of each cell is the ground line."""
    t = P.Tex('garden_plants', 'none', False, False, 711)
    r = t.r
    straw, olive, dark, green = '#b39a5e', '#6b7442', '#3f4629', '#7d8550'
    for cx in range(4):
        x0 = cx * 256
        t.stage = 2
        for _ in range(9):  # wheat
            wheat(t, x0 + 128 + r.uniform(-60, 60), 250, r.uniform(150, 220), r.uniform(-0.5, 0.5), r.choice([olive, '#8a8048']), r.choice([straw, '#c2a868', '#a68c50']))
        for _ in range(6):  # millet stalks with drooping heads, and reeds
            x = x0 + 128 + r.uniform(-80, 80); h = r.uniform(170, 230); lean = r.choice([-1, 1])
            top = (x + lean * 40, 506 - h)
            t.stroke([(x, 506), (x + lean * 10, 506 - h * 0.6), top], 'ink', 3, olive, 1.0, taper=[0, 2])
            t.stroke([top, (top[0] + lean * 20, top[1] + 10), (top[0] + lean * 26, top[1] + 50)], 'ink', 10, r.choice([straw, '#9c8a52']), 1.0, taper=[4, 8])
            for s in (-1, 1):
                y0 = 506 - h * r.uniform(0.2, 0.5)
                t.stroke([(x, y0), (x + s * 40, y0 - 50), (x + s * 70, y0 - 30)], 'ink', 6, r.choice([olive, green]), 1.0, taper=[0, 12])
        for _ in range(14):  # low shrub: clustered leaf dabs on short stems
            x = x0 + 128 + r.uniform(-90, 90); y = 762 - r.uniform(20, 120)
            t.stroke([(x0 + 128 + r.uniform(-20, 20), 762), (x, y)], 'ink', 3, dark, 1.0, taper=[0, 2])
            for _ in range(10):
                a = r.uniform(0, math.tau); L = r.uniform(8, 18)
                t.stroke([(x + r.uniform(-14, 14), y + r.uniform(-14, 14)), (x + math.cos(a) * L, y + math.sin(a) * L)], 'ink', r.uniform(5, 8), r.choice([olive, dark, green]), 1.0, taper=[2, 4])
        for _ in range(26):  # grass tuft
            x = x0 + 128 + r.uniform(-90, 90); a = -math.pi / 2 + r.uniform(-0.6, 0.6); L = r.uniform(40, 110)
            t.stroke([(x, 1020), (x + math.cos(a) * L * 0.5 + r.uniform(-6, 6), 1020 + math.sin(a) * L * 0.6), (x + math.cos(a) * L, 1020 + math.sin(a) * L)], 'ink', r.uniform(3, 5), r.choice([olive, green, straw]), 1.0, taper=[0, 8])
    return t


def star_ceiling():
    """Star-map ceiling (A17), core hall: lacquer-black ground, a pale Milky Way wash on the diagonal, gold and silver stars, lodge
    asterisms joined by fine gold lines with vermilion lodge rings; our own arrangement (no real chart copied)."""
    t = P.Tex('star_ceiling', '#18161c', True, True, 721)
    r = t.r
    t.stage = 1
    for _ in range(900):  # lacquer brushwork, 4-15 cm
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke(t.wobble(x, y, x + r.uniform(10, 38), y + r.uniform(-4, 4), 3, 1.5), 'oil', r.uniform(10, 24), r.choice(['#24212a', '#0f0d12', '#2b2832']), 0.6)
    for k in range(70):  # the Milky Way band
        f = r.uniform(0, 1); x = f * 1024; y = 200 + f * 600 + r.uniform(-90, 90)
        t.blot(x, y, r.uniform(30, 70), 'sponge', r.uniform(50, 90), r.choice(['#35343f', '#43424d', '#2c2b35']), r.uniform(0.3, 0.5), 3)
    t.stage = 2
    for _ in range(1000):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + 0.5, y + 0.5)], 'ink', r.uniform(2, 5), r.choice(['#c8ccd0', '#c9a95e', '#9a9ca2']), r.uniform(0.6, 0.95), taper=[0, 0])
    for _ in range(14):  # asterisms
        cx, cy = r.uniform(0, 1024), r.uniform(0, 1024); n = r.randint(3, 6)
        pts = [(cx, cy)]
        for _ in range(n - 1):
            a = r.uniform(0, math.tau); L = r.uniform(30, 70); pts.append((pts[-1][0] + math.cos(a) * L, pts[-1][1] + math.sin(a) * L))
        t.stroke(pts, 'pencil', 2, '#a08050', 0.7, taper=[0, 0])
        for x, y in pts:
            t.stroke([(x, y), (x + 0.5, y)], 'ink', 9, '#c9a95e', 1.0, taper=[0, 0])
        lx, ly = pts[0]
        ring = [(lx + math.cos(a) * 14, ly + math.sin(a) * 14) for a in [k * math.tau / 18 for k in range(19)]]
        t.stroke(ring, 'pencil', 2.5, '#86281a', 0.85, taper=[0, 0])
    return t


def pond_water():
    """Garden pond water (A16, FIXB 25 Nov, owner: lighter blue-green with a pale edge; the black lake stays black): a light blue-green
    tiling water, soft ripple bands, crests and troughs 4-15 cm, a few pale glints and sunk sand patches. The pond mesh (viewer: vertex
    colours, linear) darkens the open water toward the centre and keeps the 1 m margin at full value: the pale edge."""
    t = P.Tex('pond_water', POND['base'], True, True, 761)
    r = t.r
    t.stage = 1
    for _ in range(70):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(70, 160), 'sponge', 120, r.choice([POND['trough'], POND['crest'], POND['base']]), 0.14, 3)   # round 2: 0.3 with sand made 50 cm blocks (sd 4.7)
    t.stage = 2
    for _ in range(2400):  # ripples: short, mostly horizontal, 4-15 cm
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); L = r.uniform(4, 15) * CM; a = r.uniform(-0.2, 0.2)
        t.stroke(t.wobble(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 3, 1.0), 'ink', r.uniform(3, 7), r.choice([POND['crest'], POND['trough'], POND['crest'], POND['trough'], POND['base']]), r.uniform(0.5, 0.8), taper=[2, 2])
    t.stage = 3
    for _ in range(160):  # glints
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(6, 18), y)], 'chalk', 3, POND['glint'], r.uniform(0.4, 0.7))
    return t


def star_inlay():
    """Star-map floor inlay (A17 moved to the core floor, FIXB 25 Nov, owner 02:2x): an alpha-tested decal of brass inlay lines laid over the
    approved 丹 floor (A1 itself is not repainted). Lodge asterisms of 3-6 studs joined by thin lines, a lodge ring on the first star of each,
    scattered single studs; our own arrangement (no real chart copied). Nothing within INLAY margin px of the edge, so each 4 m cell can be
    turned 0/90/180/270 deg (8 looks with mirroring) without a seam: the map does not show a 4 m repeat."""
    t = P.Tex('star_inlay', 'none', False, False, 771)
    r = t.r; I = INLAY; m = I['margin'] + I['stud']
    def inside(x, y): return m <= x <= 1024 - m and m <= y <= 1024 - m
    t.stage = 2
    placed = []
    for _ in range(I['asterisms']):
        for _try in range(60):
            cx, cy = r.uniform(m + 40, 1024 - m - 40), r.uniform(m + 40, 1024 - m - 40)
            if all(math.hypot(cx - a, cy - b) > 190 for a, b in placed): break
        placed.append((cx, cy)); pts = [(cx, cy)]
        for _ in range(r.randint(2, 5)):
            for _try in range(30):
                a = r.uniform(0, math.tau); L = r.uniform(45, 110); q = (pts[-1][0] + math.cos(a) * L, pts[-1][1] + math.sin(a) * L)
                if inside(*q): break
            else: continue
            pts.append(q)
        if len(pts) > 1: t.stroke(pts, 'marker', I['line'], r.choice(I['tones'][:2]), 1.0, taper=[0, 0], wrap=False)
        for x, y in pts: t.stroke([(x, y), (x + 0.5, y)], 'ink', I['stud'], I['tones'][2], 1.0, taper=[0, 0], wrap=False)
        lx, ly = pts[0]
        t.stroke([(lx + math.cos(a) * 26, ly + math.sin(a) * 26) for a in [k * math.tau / 24 for k in range(25)]], 'marker', I['ring'], I['tones'][0], 1.0, taper=[0, 0], wrap=False)
    for _ in range(I['singles']):
        x, y = r.uniform(m, 1024 - m), r.uniform(m, 1024 - m)
        t.stroke([(x, y), (x + 0.5, y)], 'ink', I['stud'] * r.uniform(0.6, 0.9), r.choice(I['tones']), 1.0, taper=[0, 0], wrap=False)
    return t


# School accents for the flags in CONFIG.SCHOOLS order (flag_i = school i): the owner's one mapping for every school item (25 Nov 02:1x:
# W1a's 鼎 accents, art/tools/ding_blender.py ACCENTS): ru ochre, dao gold, fa lead white, mo cinnabar, yinyang bone black, za silver,
# ming Han purple, zongheng malachite, nong azurite. Ground stays Qin black (banners black).
SCHOOLS = [('ru', '#b8862e'), ('dao', '#e2b84a'), ('fa', '#d9d2c3'), ('mo', '#a8321e'), ('yinyang', '#1a1614'), ('za', '#c8ccd0'),
           ('ming', '#5b3f8c'), ('zongheng', '#2f8a5c'), ('nong', '#2e5a9c')]
# Accents darker than this luminance (bone black on Qin black) get bone keylines (KEYLINE colour, px each side) so band and sigil still read.
# Band and sigil stroke width px (round 2: 8 -> 6, the light accents pushed the flag lum sd to 35.4 over the study's 30).
KEY_LUM, KEYLINE, KEY_W, BAND_W = 45, '#e9dfca', 2, 6


def sigil(t, kind, cx, cy, s, c, w=8):
    """invented school sigils (shapes differ first, colour second; no calligraphy)."""
    sq = lambda h: [(cx - h, cy - h), (cx + h, cy - h), (cx + h, cy + h), (cx - h, cy + h), (cx - h, cy - h)]
    circ = lambda rr, ox=0, oy=0, a0=0, a1=math.tau: [(cx + ox + math.cos(a0 + (a1 - a0) * k / 24) * rr, cy + oy + math.sin(a0 + (a1 - a0) * k / 24) * rr) for k in range(25)]
    if kind == 'ru': t.stroke(sq(s), 'marker', w, c, 1, taper=[0, 0]); t.stroke(sq(s * 0.5), 'marker', w, c, 1, taper=[0, 0])
    elif kind == 'dao': t.stroke([(cx + math.cos(k * 0.4) * s * k / 30, cy + math.sin(k * 0.4) * s * k / 30) for k in range(31)], 'marker', w, c, 1, taper=[0, 0])
    elif kind == 'yinyang': t.stroke(circ(s * 0.5, -s * 0.45), 'marker', w, c, 1, taper=[0, 0]); t.stroke(circ(s * 0.5, s * 0.45), 'marker', w * 1.6, c, 1, taper=[0, 0])
    elif kind == 'fa': t.stroke([(cx, cy - s), (cx, cy + s)], 'marker', w, c, 1, taper=[0, 0]); t.stroke([(cx - s, cy - s * 0.5), (cx + s, cy - s * 0.5)], 'marker', w, c, 1, taper=[0, 0]); t.stroke([(cx - s, cy - s * 0.5), (cx - s * 0.8, cy + s * 0.2)], 'marker', w * 0.7, c, 1, taper=[0, 0]); t.stroke([(cx + s, cy - s * 0.5), (cx + s * 0.8, cy + s * 0.2)], 'marker', w * 0.7, c, 1, taper=[0, 0])
    elif kind == 'ming': t.stroke([(cx - s, cy), (cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], 'marker', w, c, 1, taper=[0, 0]); t.stroke([(cx - s * 1.2, cy - s * 1.1), (cx + s * 1.2, cy + s * 1.1)], 'marker', w * 0.7, c, 1, taper=[0, 0])
    elif kind == 'mo':
        pts = [(cx - s, cy + s * 0.6)]
        for k in range(4):
            x = cx - s + k * s / 2; pts += [(x, cy - s * 0.4), (x + s / 4, cy - s * 0.4), (x + s / 4, cy + 0.0), (x + s / 2, cy)]
        t.stroke(pts + [(cx + s, cy + s * 0.6), (cx - s, cy + s * 0.6)], 'marker', w, c, 1, taper=[0, 0])
    elif kind == 'zongheng':
        for a in (math.pi / 4, -math.pi / 4):
            x1, y1 = cx + math.cos(a) * s, cy + math.sin(a) * s
            t.stroke([(cx - math.cos(a) * s, cy - math.sin(a) * s), (x1, y1)], 'marker', w, c, 1, taper=[0, 0])
            t.stroke([(x1 - math.cos(a - 0.5) * s * 0.4, y1 - math.sin(a - 0.5) * s * 0.4), (x1, y1), (x1 - math.cos(a + 0.5) * s * 0.4, y1 - math.sin(a + 0.5) * s * 0.4)], 'marker', w * 0.8, c, 1, taper=[0, 0])
    elif kind == 'za':
        for i in range(3):
            for j in range(3):
                t.stroke([(cx + (i - 1) * s * 0.7, cy + (j - 1) * s * 0.7), (cx + (i - 1) * s * 0.7 + 0.5, cy + (j - 1) * s * 0.7)], 'ink', s * 0.35 + (w - 8), c, 1, taper=[0, 0])
    elif kind == 'nong':
        t.stroke([(cx, cy + s), (cx, cy - s)], 'marker', w * 0.8, c, 1, taper=[0, 0])
        for k in range(4):
            y = cy - s * 0.8 + k * s * 0.4
            for sx in (-1, 1): t.stroke([(cx, y + s * 0.15), (cx + sx * s * 0.45, y - s * 0.1)], 'marker', w * 1.2, c, 1, taper=[0, 4])


def signal_flags():
    """Signal flags (A19), alpha-tested: a 3 x 3 atlas of 1.33 m cells, one per school: a Qin-black swallow-tailed flag (court banners
    were black), the school's accent as a border band and an invented sigil; the left edge sits on the pole, cloth folds by value."""
    t = P.Tex('signal_flags', 'none', False, False, 731)
    r = t.r
    C = 1024 / 3
    for i, (kind, acc) in enumerate(SCHOOLS):
        x0, y0 = (i % 3) * C + 12, (i // 3) * C + 40; w, h = C - 30, C * 0.62
        t.stage = 0
        y = y0
        while y <= y0 + h:  # black field; the swallow-tail notch cut from the fly
            notch = w * 0.22 * (1 - abs((y - y0) / h - 0.5) * 2)
            t.stroke([(x0, y), (x0 + w - notch, y)], 'ink', 8, '#302a27', 1.0, taper=[0, 0], wrap=False); y += 5
        t.stage = 1
        for k in range(5):  # cloth folds: darker and lighter vertical swathes
            fx = x0 + (k + 0.5) * w / 5.5
            t.stroke([(fx, y0 + 4), (fx + r.uniform(-6, 6), y0 + h - 4)], 'oil', r.uniform(14, 26), r.choice(['#2b2521', '#0f0c0b']), 0.6, taper=[0, 0], wrap=False)
        t.stage = 2
        lum = sum(k * int(acc[j:j + 2], 16) for k, j in ((0.2126, 1), (0.7152, 3), (0.0722, 5)))
        layers = [(KEYLINE, BAND_W + 2 * KEY_W), (acc, BAND_W)] if lum < KEY_LUM else [(acc, BAND_W)]
        for col, bw in layers:  # accent border bands top and bottom, and along the pole edge (dark accents over a bone keyline)
            for yy in (y0 + 8, y0 + h - 8):
                t.stroke([(x0, yy), (x0 + w * 0.8, yy)], 'ink', bw, col, 1.0, taper=[0, 0], wrap=False)
            t.stroke([(x0 + 5, y0), (x0 + 5, y0 + h)], 'ink', bw, col, 1.0, taper=[0, 0], wrap=False)
            sigil(t, kind, x0 + w * 0.42, y0 + h / 2, h * 0.24, col, bw)
    return t


def slips_rows(t, burnt):
    """bamboo slips 竹简 (A20): rows 0-512 slips 1.2 cm wide laid side by side (columns), unreadable ink dashes, two cords;
    rows 512-768 rolled bundle ends (spirals); rows 768-1024 a silk wrapping cloth. Wraps across x."""
    r = t.r
    tones = ['#b39a66', '#af9662', '#b69d69', '#b0975f'] if not burnt else ['#3c2e24', '#3a2d23', '#3f3126', '#392b21']
    ink = '#2b2018' if not burnt else '#0c0908'
    t.stage = 1
    x = 0.0
    while x < 1024:
        w = 1.2 * CM
        t.stroke([(x + w / 2, 0), (x + w / 2, 512)], 'marker', w + 0.6, r.choice(tones), 1.0, taper=[0, 0], wrap=False); x += w
    for _ in range(90):  # broad tone of the bundle (handling, ageing, scorch for the burnt set)
        t.blot(r.uniform(0, 1024), r.uniform(20, 490), r.uniform(40, 90), 'sponge', 70, r.choice(['#9a8250', '#c6ad7a', '#a48a56'] if not burnt else ['#141010', '#6a5038', '#1c1613', '#5e4632']), 0.5 if burnt else 0.4, 2)
    t.stage = 2
    x = 1.5
    while x < 1024:  # writing: short unreadable dashes down every second slip
        if r.random() < 0.6:
            y = r.uniform(20, 60)
            while y < 500:
                L = r.uniform(4, 10); t.stroke([(x, y), (x, y + L)], 'pencil', 1.8, ink, 0.55, taper=[0, 0], wrap=False); y += L + r.uniform(6, 16)
        x += 2 * 1.2 * CM
    for cy in (120, 392):  # the binding cords across the slips
        t.stroke(t.wobble(0, cy, 1024, cy, 16, 1.5), 'ink', 7, '#5a3e26' if not burnt else '#120e0c', 0.95, taper=[0, 0], wrap=False)
    P.band(t, 512, 768, '#3a2c20' if not burnt else '#141110', 'flat-bristle', 40, 1.0, 22, 1.5)
    for i in range(16):  # bundle ends
        for j in range(4):
            cx, cy = 32 + i * 64, 544 + j * 64; rr = 26
            t.stroke([(cx, cy), (cx + 0.5, cy)], 'ink', rr * 2, r.choice(tones), 1.0, taper=[0, 0])
            spiral = [(cx + math.cos(k * 0.45) * rr * k / 40, cy + math.sin(k * 0.45) * rr * k / 40) for k in range(41)]
            t.stroke(spiral, 'pencil', 2, '#5a4630' if not burnt else '#0c0908', 0.8, taper=[0, 0])
    silk = ['#8a6a3a', '#7c5e32', '#97764a'] if not burnt else ['#2a221c', '#1f1915', '#352a22']
    P.band(t, 768, 1024, silk[0], 'flat-bristle', 50, 1.0, 26, 2)
    for _ in range(160):
        x, y = r.uniform(0, 1024), r.uniform(780, 1015)
        t.stroke(t.wobble(x, y, x + r.uniform(30, 90), y + r.uniform(-8, 8), 3, 2), 'oil', r.uniform(8, 18), r.choice(silk), 0.5)
    t.stage = 3
    if burnt:
        for _ in range(120):  # ash and the last scorched tan at the edges
            x, y = r.uniform(0, 1024), r.uniform(0, 1024)
            t.stroke([(x, y), (x + r.uniform(-10, 10), y + r.uniform(-10, 10))], 'chalk', r.uniform(3, 7), r.choice(['#7a726a', '#6b4a2e']), 0.5)
    return t


def slips(): return slips_rows(P.Tex('slips', '#b09763', True, False, 741), False)
def slips_burnt(): return slips_rows(P.Tex('slips_burnt', '#33281f', True, False, 742), True)


ALL = [rammed_earth, rammed_earth_core, earth_burnt, river_stone, stone_paving, floor_tiles, hollow_brick, mural_wall, wall_burnt, roof_tile, tile_ends,
       timber, timber_burnt, mercury_matcap, black_lake, garden_ground, garden_plants, star_ceiling, signal_flags, slips, slips_burnt,
       pond_water, star_inlay]

if __name__ == '__main__':
    want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    for f in ALL:
        if want and f.__name__ not in want: continue
        t = f(); print(t.name, t.write(), 'ops')
