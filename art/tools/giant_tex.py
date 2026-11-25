#!/usr/bin/env python3
"""Patina variant of the bronze trim sheet for the dormant twelve bronze giants (asset list C8; W1c overnight 25 Nov).

Research rule list (docs/research/Qin-palace-medieval-tech-fusion.md): fresh brass-gold on live machines, patina on dormant ones; a
dormant giant wears verdigris and the patina cracks away to fresh brass-gold when she wakes it. The giant meshes use the shared trim
sheet rows (art/tools/bronze_tex.py layout), so this sheet keeps every row in place and paints it in patina: the same stamp bands,
inlay line, flange and workshop marks (our own ornament, same placement), read as raised relief under verdigris; worn bronze shows
through on the raised lips only. Awake giants use bronze_trim_brass.png (or the default sheet; the owner picks, see W1a's Needs owner).

Layout: identical to bronze_trim (1024 x 1024 = 4 x 4 m at 256 px/m). Writes bronze_trim_patina.jsonl / .passes.json / .bg for
paint_palace.py (klad).
Usage: python3 giant_tex.py OUTDIR [SIZE]
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P  # reads OUTDIR and SIZE from argv

# Patina ramps (research verdigris #4F7A62 with the study's #3f5a4c / #6f927c), raised relief lighter and bluer, worn bronze on lips.
DEEP, SHADOW, BASE, LIGHT, HI = '#26332b', '#3f5a4c', '#4f7a62', '#6f927c', '#8fae98'
CRUST, BRONZE_WORN, BRONZE_D = '#5d8a70', '#7a6440', '#4a3a24'


def patina_trim():
    t = P.Tex('bronze_trim_patina', BASE, True, False, 713)
    r = t.r
    t.stage = 0
    P.band(t, 0, 384, BASE, 'flat-bristle', 60, 1.0, 30, 3)
    for y0, y1, c in ((384, 448, SHADOW), (448, 512, DEEP), (512, 576, SHADOW), (576, 640, BASE), (640, 704, SHADOW), (704, 768, BASE), (768, 1024, SHADOW)):
        P.band(t, y0, y1, c, 'flat-bristle', 40 if y1 - y0 <= 64 else 60, 1.0, 20, 2)
    # tone pass: crusty patina blooms (lighter crust, darker pits, a few dark bronze islands) over every row
    t.stage = 1
    for _ in range(130):
        t.blot(r.uniform(0, 1024), r.uniform(40, 344), r.uniform(30, 70), 'sponge', r.uniform(40, 80), r.choice([LIGHT, SHADOW, CRUST, CRUST, BRONZE_D]), r.uniform(0.3, 0.55), 3)
    for _ in range(90):
        t.blot(r.uniform(0, 1024), r.uniform(810, 1014), r.uniform(30, 60), 'sponge', r.uniform(40, 80), r.choice([BASE, SHADOW, LIGHT, DEEP]), r.uniform(0.45, 0.7), 3)
    # marks pass: the same ornament as the brass sheet, in raised relief under the patina (lighter green), inlay dulled to grey-green
    t.stage = 2
    for i in range(8):
        P.cloud(t, 64 + i * 128, 416, 46, LIGHT)
    x0 = r.uniform(0, 1024)
    t.stroke([(x0, 470), (x0 + 1100, 470)], 'marker', 26, '#1b241f', 1.0, taper=[0, 0])
    t.stroke([(x0, 470), (x0 + 1100, 470)], 'marker', 16, '#9fb3a6', 1.0, taper=[0, 0])
    t.stroke([(x0, 494), (x0 + 1100, 494)], 'marker', 8, '#71857a', 1.0, taper=[0, 0])
    for i in range(16):
        cx = 32 + i * 64
        t.stroke([(cx - 26, 544), (cx, 522), (cx + 26, 544), (cx, 566), (cx - 26, 544)], 'ink', 12, LIGHT, 0.95, taper=[0, 0])
        t.stroke([(cx, 534), (cx + 9, 544), (cx, 554)], 'ink', 8, DEEP, 0.9, taper=[0, 4])
    x0 = r.uniform(0, 1024)
    t.stroke([(x0, 590), (x0 + 1100, 590)], 'marker', 14, BRONZE_WORN, 1.0, taper=[0, 0])  # worn lip: bronze shows through
    t.stroke([(x0, 606), (x0 + 1100, 606)], 'marker', 8, LIGHT, 1.0, taper=[0, 0])
    t.stroke([(x0, 628), (x0 + 1100, 628)], 'marker', 6, DEEP, 1.0, taper=[0, 0])
    for i in range(4):
        cx = 128 + i * 256
        for s in (-1, 1):
            ex = cx + s * 38
            t.stroke([(ex - 16, 672), (ex, 660), (ex + 16, 672), (ex, 684), (ex - 16, 672)], 'ink', 12, LIGHT, 0.95, taper=[0, 0])
            t.stroke([(ex - 4, 672), (ex + 4, 672)], 'ink', 12, HI, 1.0, taper=[0, 0])
            t.stroke([(ex - s * 22, 652), (ex, 648), (ex + s * 26, 654)], 'ink', 10, LIGHT, 0.9, taper=[2, 6])
            P.cloud(t, cx + s * 96, 674, 22, LIGHT)
        t.stroke([(cx, 650), (cx, 696)], 'ink', 5, LIGHT, 0.9, taper=[0, 0])
    for i in range(8):
        cx = 64 + i * 128
        t.stroke([(cx - 22, 714), (cx + 22, 714), (cx + 22, 758), (cx - 22, 758), (cx - 22, 714)], 'ink', 5, DEEP, 0.95, taper=[0, 0])
        a = r.uniform(0, math.pi)
        for k in range(3):
            ang = a + k * math.pi / 3
            t.stroke([(cx - math.cos(ang) * 13, 736 - math.sin(ang) * 13), (cx + math.cos(ang) * 13, 736 + math.sin(ang) * 13)], 'ink', 4, DEEP, 0.9, taper=[0, 0])
        t.stroke([(cx - 4, 736), (cx + 4, 736)], 'ink', 6, HI, 1.0, taper=[0, 0])
    # detail pass: pits, pale crust flecks, a few hairline cracks (the cracks the patina breaks along when she wakes the giant)
    t.stage = 3
    for _ in range(120):
        x, y = r.uniform(0, 1024), r.uniform(0, 380)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 6), DEEP, r.uniform(0.5, 0.8), taper=[0, 0])
    for _ in range(30):
        x, y = r.uniform(0, 1024), r.uniform(0, 380)
        t.stroke([(x, y), (x + 1, y + 1)], 'chalk', r.uniform(5, 9), HI, r.uniform(0.35, 0.6), taper=[0, 0])
    for _ in range(14):
        x, y = r.uniform(0, 1024), r.uniform(30, 350); pts = [(x, y)]
        for _k in range(5):
            x += r.uniform(10, 26); y += r.uniform(-12, 12); pts.append((x, y))
        t.stroke(pts, 'ink', 4, DEEP, 0.8, taper=[2, 4])
    for _ in range(80):
        x, y = r.uniform(0, 1024), r.uniform(776, 1020)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 7), '#1e2a23', r.uniform(0.5, 0.8), taper=[0, 0])
    return t


if __name__ == '__main__':
    t = patina_trim(); print(t.name, t.write(), 'ops')
