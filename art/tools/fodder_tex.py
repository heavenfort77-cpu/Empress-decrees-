#!/usr/bin/env python3
"""Trim sheet for the 皇家 guard and the 反贼 rebels (worker W5; study art/Guard-Rebels-Study.md), painted in klad like the palace textures.

Guard bronze (hulls, masks, treads) uses the approved assets/tex/bronze_trim.png; this sheet holds everything else: Qin-black lacquer
lamellar, water-blue cord and lacquer cloth, the 太平道 yellow headband, rebel hemp, the neutral patch cloth (tinted per school by instance
colour), bootleg plates, rope and skin. All marks are our own (plate rows, weave, stitching, folds); nothing traced.

Layout, 1024 x 1024 = 4 x 4 m at 256 px/m; every row wraps across x:
  0-256     Qin-black lacquer lamellar: small plates 32 x 48 px (12.5 x 19 cm) in staggered rows, water-blue lacing at the plate tops
  256-320   water-blue cord binding (braided)
  320-384   water-blue lacquer cloth (banner, canopy, cap board)
  384-448   dark dyed cloth (死士 wraps and hood, hair)
  448-512   yellow headband cloth (ochre yellow, folds)
  512-704   undyed hemp cloth (rebel robes, trousers, hoods)              broad region checked by tex_check.py
  704-832   patch cloth, neutral light grey with dark stitching (multiplied by the school colour in the game and viewer)
  832-928   bootleg plates: mismatched scuffed leather and raw wood plates, rope ties
  928-960   scrap metal: dull iron-bronze (rebel blades, axe, wheel)
  960-992   rope
  992-1024  skin (hands, faces) with a shadow side

Usage: python3 fodder_tex.py OUTDIR [SIZE]   (writes fodder_trim.jsonl / .passes.json / .bg for paint_palace.py)
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P

# Values (study value plan; lacquer lum 25-40, cord blue 70-110, yellow 140-175, hemp 90-130, patch 160-210 neutral)
LAC, LAC_D, LAC_L = '#1c1714', '#0f0c0a', '#3a2e26'
BLUE, BLUE_D, BLUE_L = '#3a6e88', '#24485a', '#5d8ea6'
YEL, YEL_D, YEL_L = '#c6a44c', '#9a7c34', '#dcc078'
HEMP, HEMP_D, HEMP_L = '#887962', '#6a5e4c', '#a39478'  # round 2: one step darker (run 45442633307: hemp mean lum 131 > 130)
PATCH, PATCH_D, PATCH_L = '#c4c2bc', '#a3a19b', '#dad8d2'
STITCH = '#3a342c'
LEATH, WOOD, ROPE = '#5a4632', '#7a6448', '#a08a5a'
SKIN, SKIN_D = '#b08a68', '#8a6a4e'
DARK, DARK_L = '#2e2a22', '#463f32'
METAL, METAL_L, METAL_D = '#6e6a5e', '#9a9484', '#46433a'


def fodder_trim():
    t = P.Tex('fodder_trim', HEMP, True, False, 905)
    r = t.r
    t.stage = 0
    for y0, y1, c in ((0, 256, LAC), (256, 320, BLUE_D), (320, 384, BLUE), (384, 448, DARK), (448, 512, YEL), (512, 704, HEMP), (704, 832, PATCH),
                      (832, 928, LEATH), (928, 960, METAL), (960, 992, ROPE), (992, 1024, SKIN)):
        P.band(t, y0, y1, c, 'flat-bristle', 40 if y1 - y0 <= 64 else 60, 1.0, 20, 2)
    # tone pass: lacquer sheen, cloth mottling and dust
    t.stage = 1
    for _ in range(60):
        t.blot(r.uniform(0, 1024), r.uniform(10, 246), r.uniform(20, 50), 'sponge', r.uniform(30, 60), r.choice([LAC_D, LAC_L, '#2a221c']), r.uniform(0.3, 0.5), 3)
    for _ in range(30):
        t.blot(r.uniform(0, 1024), r.uniform(326, 378), r.uniform(15, 30), 'sponge', r.uniform(24, 40), r.choice([BLUE_D, BLUE_L]), r.uniform(0.3, 0.5), 3)
    for _ in range(30):
        t.blot(r.uniform(0, 1024), r.uniform(390, 442), r.uniform(15, 30), 'sponge', r.uniform(24, 40), r.choice([DARK_L, '#24201a']), r.uniform(0.3, 0.5), 3)
    for _ in range(110):
        t.blot(r.uniform(0, 1024), r.uniform(520, 696), r.uniform(25, 60), 'sponge', r.uniform(40, 70), r.choice([HEMP_D, HEMP_L, '#857660', '#9a8a70']), r.uniform(0.3, 0.5), 3)
    for _ in range(50):
        t.blot(r.uniform(0, 1024), r.uniform(712, 824), r.uniform(20, 40), 'sponge', r.uniform(30, 50), r.choice([PATCH_D, PATCH_L]), r.uniform(0.3, 0.45), 3)
    # marks pass
    t.stage = 2
    # lamellar: staggered plate rows, 48 px tall; plate gaps dark, a light lacquer edge on top, two blue lacing dots per plate
    for row in range(5):
        y = 8 + row * 48; off = 16 if row % 2 else 0
        t.stroke([(0, y + 46), (1100, y + 46)], 'marker', 5, LAC_D, 1.0, taper=[0, 0])
        for i in range(33):
            x = off + i * 32
            t.stroke([(x, y + 4), (x, y + 44)], 'pencil', 3, LAC_D, 0.9, taper=[0, 0])
            t.stroke([(x + 4, y + 6), (x + 28, y + 6)], 'dry-brush', 4, LAC_L, 0.6, taper=[0, 0])
            for dx in (10, 22):
                t.stroke([(x + dx, y + 12), (x + dx + 1, y + 13)], 'ink', 5, BLUE_L, 0.95, taper=[0, 0])
    # braided cord: diagonal twists every 16 px
    for i in range(66):
        x = i * 16
        t.stroke([(x, 262), (x + 14, 314)], 'flat-bristle', 9, BLUE_L, 0.7, taper=[2, 2])
        t.stroke([(x + 6, 262), (x + 20, 314)], 'pencil', 2.5, '#16303c', 0.7, taper=[0, 0])
    # lacquer cloth folds: long soft vertical-ish folds
    for _ in range(40):
        x = r.uniform(0, 1024)
        t.stroke(t.wobble(x, 322, x + r.uniform(-10, 10), 382, 3, 2), 'dry-brush', r.uniform(10, 22), r.choice([BLUE_D, BLUE_L]), r.uniform(0.35, 0.55))
        t.stroke(t.wobble(x, 386, x + r.uniform(-10, 10), 446, 3, 2), 'dry-brush', r.uniform(8, 18), r.choice([DARK_L, '#1e1b16']), r.uniform(0.35, 0.55))
    # headband: folds and a darker hem at both edges
    for y in (452, 508):
        t.stroke([(0, y), (1100, y)], 'marker', 6, YEL_D, 0.9, taper=[0, 0])
    for _ in range(70):
        x = r.uniform(0, 1024)
        t.stroke(t.wobble(x, 456, x + r.uniform(-14, 14), 504, 3, 2), 'dry-brush', r.uniform(6, 14), r.choice([YEL_D, YEL_L]), r.uniform(0.4, 0.6))
    # hemp: weave (short horizontal and vertical ticks, 4-12 cm patches)
    for _ in range(380):  # round 2: fewer, longer ticks (run 45442633307: brush run 3.7 cm < 4)
        x, y = r.uniform(0, 1024), r.uniform(516, 700); L = r.uniform(16, 40)
        if r.random() < 0.5: t.stroke([(x, y), (x + L, y)], 'chalk', r.uniform(3, 6), r.choice([HEMP_D, HEMP_L]), r.uniform(0.35, 0.55))
        else: t.stroke([(x, y), (x, y + L)], 'chalk', r.uniform(3, 6), r.choice([HEMP_D, HEMP_L]), r.uniform(0.35, 0.55))
    # patches: stitched squares every 128 px, cross stitches on the seams
    for i in range(8):
        x0 = i * 128 + r.uniform(4, 10)
        for ya, yb in ((712, 824),):
            t.stroke([(x0, ya), (x0 + 116, ya), (x0 + 116, yb), (x0, yb), (x0, ya)], 'pencil', 3, STITCH, 0.85, taper=[0, 0])
            for k in range(12):
                sx = x0 + 6 + k * 9.5
                for sy in (ya, yb):
                    t.stroke([(sx - 3, sy - 4), (sx + 3, sy + 4)], 'pencil', 2.5, STITCH, 0.9, taper=[0, 0])
    # bootleg plates: uneven plates of leather and wood, 40-70 px, with rope ties
    x = 0
    while x < 1024:
        w = r.uniform(40, 72); c = r.choice([LEATH, WOOD, '#4a3a2a', '#6a5640'])
        for y0, y1 in ((834, 880), (882, 926)):
            yy0, yy1 = y0 + r.uniform(0, 4), y1 - r.uniform(0, 4)
            t.stroke([(x + w / 2, yy0), (x + w / 2, yy1)], 'flat-bristle', w - 6, c, 1.0, taper=[0, 0])
            t.stroke([(x + 4, yy0 + 3), (x + w - 6, yy0 + 3)], 'dry-brush', 4, '#8e7a5c', 0.6, taper=[0, 0])
            t.stroke([(x + w / 2 - 6, yy0 + 10), (x + w / 2 + 6, yy0 + 14)], 'ink', 4, ROPE, 0.95, taper=[0, 0])
        x += w
    # scrap metal: hammer marks and a bright worn edge
    t.stroke([(0, 932), (1100, 932)], 'marker', 5, METAL_L, 0.8, taper=[0, 0])
    for _ in range(160):
        x, y = r.uniform(0, 1024), r.uniform(936, 958)
        t.stroke([(x, y), (x + r.uniform(4, 12), y + r.uniform(-1, 1))], 'chalk', r.uniform(3, 5), r.choice([METAL_D, METAL_L]), r.uniform(0.4, 0.6))
    # rope twists
    for i in range(86):
        t.stroke([(i * 12, 962), (i * 12 + 10, 990)], 'flat-bristle', 7, '#c0a874', 0.6, taper=[2, 2])
    # skin: shadow side on the lower half
    t.stroke([(0, 1012), (1100, 1012)], 'marker', 16, SKIN_D, 0.6, taper=[0, 0])
    # detail pass: wear on lacquer edges, dust and stains on cloth, scratches on plates
    t.stage = 3
    for _ in range(120):
        x, y = r.uniform(0, 1024), r.uniform(0, 250)
        t.stroke([(x, y), (x + r.uniform(3, 10), y + r.uniform(-1, 1))], 'chalk', r.uniform(2, 4), '#4a3c30', r.uniform(0.4, 0.6))
    for _ in range(90):
        x, y = r.uniform(0, 1024), r.uniform(520, 700)
        t.stroke([(x, y), (x + r.uniform(4, 14), y + r.uniform(-3, 3))], 'chalk', r.uniform(3, 7), r.choice(['#5e5242', '#b8aa8c']), r.uniform(0.35, 0.5))
    for _ in range(70):
        x, y = r.uniform(0, 1024), r.uniform(836, 924); a = r.uniform(0, math.tau); L = r.uniform(8, 22)
        t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'pencil', 2, '#2a2018', 0.6)
    return t


if __name__ == '__main__':
    t = fodder_trim(); print(t.name, t.write(), 'ops')
