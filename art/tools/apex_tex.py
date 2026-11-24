#!/usr/bin/env python3
"""Dormant sheet for the apex Tiger Demon and its cubs (W4, 25 Nov): apex_patina, painted in klad like bronze_trim.

The apex wears the shared bronze trim sheet (assets/tex/bronze_trim.png) when awake. Asleep under the throne it wears this sheet:
the same layout, the same ornament ops (bronze_tex.bronze_trim, seed 711), then green patina painted over every row, so the
dormant state is a material swap on the same UVs, not a new mesh (research rule: patina = dormant, fresh brass-gold = alive).
Stamp bands, flanges and marks stay faintly readable under the patina (a buried bronze keeps its relief).

Usage: python3 apex_tex.py OUTDIR [SIZE]   (writes apex_patina.jsonl / .passes.json / .bg for paint_palace.py)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palace_tex as P
import bronze_tex as B

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Patina colours (study: dormant patina #4f7a62 / #3f5a4c / #6f927c) and the dark bronze that shows through.
PATINA = (B.VERD, B.VERD_D, B.VERD_L, '#5a6e4e')
# Patina blots over the ornament rows (0-768): count, radius range (px), opacity range. Lower opacity on the bands keeps their relief.
BLOTS_PLATE, BLOTS_BANDS = 260, 160
RAD = (24, 60)
OP_PLATE, OP_BANDS = (0.55, 0.8), (0.3, 0.5)
# Pale crust specks (lead carbonate bloom) and dark pits: counts.
CRUST, PITS = 120, 160


def apex_patina():
    t = B.bronze_trim()
    t.name = 'apex_patina'
    r = t.r
    t.stage = 3
    for _ in range(BLOTS_PLATE):
        t.blot(r.uniform(0, 1024), r.uniform(20, 364), r.uniform(*RAD), 'sponge', r.uniform(50, 90), r.choice(PATINA), r.uniform(*OP_PLATE), 4)
    for _ in range(BLOTS_BANDS):
        t.blot(r.uniform(0, 1024), r.uniform(384, 768), r.uniform(16, 30), 'sponge', r.uniform(30, 50), r.choice(PATINA), r.uniform(*OP_BANDS), 3)
    for _ in range(CRUST):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + r.uniform(4, 14), y + r.uniform(-3, 3))], 'chalk', r.uniform(5, 10), '#9db7a2', r.uniform(0.3, 0.5))
    for _ in range(PITS):
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 7), '#26322a', r.uniform(0.5, 0.8), taper=[0, 0])
    return t


if __name__ == '__main__':
    t = apex_patina(); print(t.name, t.write(), 'ops')
