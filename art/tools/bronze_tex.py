#!/usr/bin/env python3
"""Bronze trim sheet for every cast-bronze palace piece (asset list A13), painted in klad like the round 2 palace textures.

Research rule list (docs/research/Qin-palace-medieval-tech-fusion.md): machines and props are segmented castings with mould seams,
flanges, gold or silver inlay lines as panel lines, stamp-band ornament repeated per segment from one trim sheet, and a workshop mark
on every plate; fresh brass-gold on live pieces, verdigris only on dormant or sunk ones. All ornament is our own drawing (cloud scroll,
hooked lozenge, a broken-up mask motif, invented sigils); nothing is traced from a reference.

Layout, 1024 x 1024 = 4 x 4 m at 256 px/m (rows in 1024 px; every row wraps across x):
  0-384    plain cast bronze, fresh brass-gold (large plates)            broad region checked by tex_check.py
  384-448  stamp band A: cloud scrolls
  448-512  silver inlay panel lines on dark bronze
  512-576  stamp band B: hooked lozenge
  576-640  flange: raised lip (light) over a dark mould seam
  640-704  stamp band C: broken-up mask motif (eyes, brows, scrolls)
  704-768  workshop marks: square cartouches with invented sigils
  768-1024 dormant bronze: verdigris over dark bronze (sunk or sleeping pieces)

Usage: python3 bronze_tex.py OUTDIR [SIZE]   (writes bronze_trim.jsonl / .passes.json / .bg for paint_palace.py)
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P  # reads OUTDIR and SIZE from argv like this script

# Bronze ramps (style study ramp extended with the research's fresh brass-gold; saturation under the 0.6 accent cap)
# Round 2: base darkened to the palace study's bronze value plan (mean luminance 70-110; round 1 measured 122).
DEEP, SHADOW, BASE, LIGHT, HI = '#3a2b1a', '#5e482b', '#82653a', '#a4844f', '#c0a066'
SILVER, SILVER_D = '#c8ccd0', '#8e9396'
VERD, VERD_D, VERD_L = '#4f7a62', '#3f5a4c', '#6f927c'


def bronze_trim():
    t = P.Tex('bronze_trim', BASE, True, False, 711)
    r = t.r
    # base pass: the rows' ground colours
    t.stage = 0
    P.band(t, 0, 384, BASE, 'flat-bristle', 60, 1.0, 30, 3)
    for y0, y1, c in ((384, 448, SHADOW), (448, 512, DEEP), (512, 576, SHADOW), (576, 640, BASE), (640, 704, SHADOW), (704, 768, BASE), (768, 1024, SHADOW)):
        P.band(t, y0, y1, c, 'flat-bristle', 40 if y1 - y0 <= 64 else 60, 1.0, 20, 2)
    # tone pass: cast-metal mottling (sand-casting texture) on the plain plate; patina blooms on the dormant row
    t.stage = 1
    for _ in range(140):
        t.blot(r.uniform(0, 1024), r.uniform(40, 344), r.uniform(30, 70), 'sponge', r.uniform(40, 80), r.choice([LIGHT, SHADOW, '#735834', '#8e7042']), r.uniform(0.3, 0.5), 3)
    for _ in range(90):
        t.blot(r.uniform(0, 1024), r.uniform(810, 1014), r.uniform(30, 60), 'sponge', r.uniform(40, 80), r.choice([VERD, VERD_D, VERD_L, DEEP]), r.uniform(0.45, 0.7), 3)
    # marks pass: stamp bands, inlay lines, flange, cartouches (our own ornament)
    t.stage = 2
    for i in range(8):  # band A: cloud scrolls, 128 px pitch = 0.5 m
        P.cloud(t, 64 + i * 128, 416, 46, LIGHT)
    x0 = r.uniform(0, 1024)  # inlay: one silver panel band 16 px (6 cm, readable at play size) with dark keylines
    t.stroke([(x0, 470), (x0 + 1100, 470)], 'marker', 26, '#241a10', 1.0, taper=[0, 0])
    t.stroke([(x0, 470), (x0 + 1100, 470)], 'marker', 16, SILVER, 1.0, taper=[0, 0])
    t.stroke([(x0, 494), (x0 + 1100, 494)], 'marker', 8, SILVER_D, 1.0, taper=[0, 0])
    for i in range(16):  # band B: hooked lozenge, 64 px pitch
        cx = 32 + i * 64
        t.stroke([(cx - 26, 544), (cx, 522), (cx + 26, 544), (cx, 566), (cx - 26, 544)], 'ink', 12, LIGHT, 0.95, taper=[0, 0])
        t.stroke([(cx, 534), (cx + 9, 544), (cx, 554)], 'ink', 8, DEEP, 0.9, taper=[0, 4])
    x0 = r.uniform(0, 1024)  # flange: light lip on top, dark mould seam under it
    t.stroke([(x0, 590), (x0 + 1100, 590)], 'marker', 14, HI, 1.0, taper=[0, 0])
    t.stroke([(x0, 606), (x0 + 1100, 606)], 'marker', 8, LIGHT, 1.0, taper=[0, 0])
    t.stroke([(x0, 628), (x0 + 1100, 628)], 'marker', 6, DEEP, 1.0, taper=[0, 0])
    for i in range(4):  # band C: a broken-up mask motif per 256 px: two eyes, brows, side scrolls (our own drawing)
        cx = 128 + i * 256
        for s in (-1, 1):
            ex = cx + s * 38
            t.stroke([(ex - 16, 672), (ex, 660), (ex + 16, 672), (ex, 684), (ex - 16, 672)], 'ink', 12, LIGHT, 0.95, taper=[0, 0])
            t.stroke([(ex - 4, 672), (ex + 4, 672)], 'ink', 12, SILVER, 1.0, taper=[0, 0])
            t.stroke([(ex - s * 22, 652), (ex, 648), (ex + s * 26, 654)], 'ink', 10, LIGHT, 0.9, taper=[2, 6])
            P.cloud(t, cx + s * 96, 674, 22, LIGHT)
        t.stroke([(cx, 650), (cx, 696)], 'ink', 5, LIGHT, 0.9, taper=[0, 0])
    for i in range(8):  # workshop marks: cartouche and an invented sigil per 128 px (no script, no real characters)
        cx = 64 + i * 128
        t.stroke([(cx - 22, 714), (cx + 22, 714), (cx + 22, 758), (cx - 22, 758), (cx - 22, 714)], 'ink', 5, DEEP, 0.95, taper=[0, 0])
        a = r.uniform(0, math.pi)
        for k in range(3):
            ang = a + k * math.pi / 3
            t.stroke([(cx - math.cos(ang) * 13, 736 - math.sin(ang) * 13), (cx + math.cos(ang) * 13, 736 + math.sin(ang) * 13)], 'ink', 4, DEEP, 0.9, taper=[0, 0])
        t.stroke([(cx - 4, 736), (cx + 4, 736)], 'ink', 6, HI, 1.0, taper=[0, 0])
    # detail pass: casting pits and a few bright wear touches on the plain plate; pits in the patina
    t.stage = 3
    for _ in range(140):
        x, y = r.uniform(0, 1024), r.uniform(0, 380)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 6), DEEP, r.uniform(0.5, 0.8), taper=[0, 0])
    for _ in range(40):
        x, y = r.uniform(0, 1024), r.uniform(0, 380); a = r.uniform(-0.3, 0.3); L = r.uniform(20, 50)
        t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'chalk', r.uniform(4, 8), HI, r.uniform(0.35, 0.55))
    for _ in range(80):
        x, y = r.uniform(0, 1024), r.uniform(776, 1020)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 7), '#2c3a31', r.uniform(0.5, 0.8), taper=[0, 0])
    return t


if __name__ == '__main__':
    t = bronze_trim(); print(t.name, t.write(), 'ops')
