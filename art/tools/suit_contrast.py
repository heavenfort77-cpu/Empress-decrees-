#!/usr/bin/env python3
"""Readability against the approved hall floor (palace study: characters readable at 3:1 against what is behind them).
Uses the viewer lineups (same camera): lineup_sil_front.png gives each suit's mask, lineup_play.png the lit pixels.
Per suit: contrast ratio (WCAG relative luminance) of the suit's median against the floor ring around it, and the share of outline
pixels whose own contrast against the floor next to them is >= 3:1 (the 'rim or ink' rule). Usage: python3 suit_contrast.py SHOTDIR [lineup image name, default lineup_play]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage
# CONFIG
# Contrast ratio the outline must reach against the floor beside it (palace study).
RATIO = 3.0
# Share of outline pixels that must reach RATIO.
EDGE_SHARE = 0.5
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
S = sys.argv[1]
sil = np.asarray(Image.open(f'{S}/lineup_sil_front.png').convert('L')) < 128
PLAY = sys.argv[2] if len(sys.argv) > 2 else 'lineup_play'
img = np.asarray(Image.open(f'{S}/{PLAY}.png').convert('RGB')).astype(float) / 255
lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4); Y = lin @ [0.2126, 0.7152, 0.0722]
lab, n = ndimage.label(ndimage.binary_closing(sil, iterations=3))
blobs = sorted([(ndimage.center_of_mass(lab == i)[1], i) for i in range(1, n + 1) if (lab == i).sum() > 800])
out = []
for sid, (cx, i) in zip(IDS, blobs):
    m = (lab == i) & sil; ring = ndimage.binary_dilation(m, iterations=8) & ~ndimage.binary_dilation(sil, iterations=2)
    ys, s_ = np.median(Y[m]), np.median(Y[ring]); r = (max(ys, s_) + 0.05) / (min(ys, s_) + 0.05)
    edge = m & ~ndimage.binary_erosion(m, iterations=2)
    fl = np.median(Y[ring])
    er = (np.maximum(Y[edge], fl) + 0.05) / (np.minimum(Y[edge], fl) + 0.05); share = (er >= RATIO).mean()
    ok = share >= EDGE_SHARE
    out.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {sid} {PLAY} outline vs hall floor: {share:.0%} of outline pixels >= {RATIO}:1 (min {EDGE_SHARE:.0%}); body median {r:.1f}:1")
print(f'{sum(out)} of {len(out)} pass')
