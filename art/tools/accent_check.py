#!/usr/bin/env python3
"""School accent check for the 鼎 review shots (art/viewer/beast.html ?model=ding&school=0-8, shoot_viewer.mjs school_N.png).
The accent region = pixels that change between the nine shots; its mean colour per school in CIELAB.
Rules (W1a, 25 Nov, study "鼎 cauldron"): every pair of schools at least dE 10 apart on screen; every accent at least dE 12 from the bronze
just above it. Prints PASS/FAIL and the numbers. Usage: python3 accent_check.py SHOTDIR"""
import sys, math, itertools
import numpy as np
from PIL import Image
D = sys.argv[1]
NAMES = ['ru', 'dao', 'fa', 'mo', 'yinyang', 'za', 'ming', 'zongheng', 'nong']
def lab(c):
    r, g, b = [x / 255 for x in c]; f = lambda v: ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92; r, g, b = f(r), f(g), f(b)
    X = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047; Y = 0.2126 * r + 0.7152 * g + 0.0722 * b; Z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883
    t = lambda v: v ** (1 / 3) if v > 0.008856 else 7.787 * v + 16 / 116
    return (116 * t(Y) - 16, 500 * (t(X) - t(Y)), 200 * (t(Y) - t(Z)))
ims = [np.asarray(Image.open(f'{D}/school_{i}.png').convert('RGB')).astype(float) for i in range(9)]
mask = np.stack(ims).std(0).max(2) > 12
up = np.roll(mask, -14, axis=0) & ~mask
L = [lab(im[mask].mean(0)) for im in ims]
fails = 0
d, a, b = min((math.dist(L[i], L[j]), NAMES[i], NAMES[j]) for i, j in itertools.combinations(range(9), 2))
ok = d >= 10; fails += not ok; print(f"{'PASS' if ok else 'FAIL'} closest pair {a} / {b} dE {d:.1f} (min 10)")
for n, im, l in zip(NAMES, ims, L):
    e = math.dist(l, lab(im[up].mean(0))); ok = e >= 12; fails += not ok
    print(f"{'PASS' if ok else 'FAIL'} {n} vs bronze dE {e:.1f} (min 12)")
print(f'{10 - fails} of 10 pass')
