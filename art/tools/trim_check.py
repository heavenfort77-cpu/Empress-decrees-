#!/usr/bin/env python3
"""Trim rules on the Qin proposal suit sheet with the per-school material tint (art/Colour-Clarity-Study.md, round 2).
Usage: python3 trim_check.py suit_lamellar_qin.png [--mutate APPROVED.png]
Rules: each school's cord row (band rows y0+9..y0+23) x its tint reaches relative luminance >= 0.21 at the 70th percentile (3:1 on a black
plate on screen; 阴阳 by its lead-white binding); every lamella row carries the binding cord (rows y0+14..y0+20, median relative luminance
>= 0.5); the former brown plate and lamella rows are black lacquer (mean lum 20-45 outside the binding, mean saturation <= 0.42); the black
plate rows keep their value (20-60). --mutate: the approved sheet must fail three of these."""
import sys
import numpy as np
from PIL import Image
# CONFIG
# Cord brightness (sheet x tint) the 70th percentile of the cord band must reach.
TRIM_Y = 0.21
# Binding cord brightness on the lamella rows (sheet only).
BIND_Y = 0.5
# Lacquer value band for the former brown rows (mean sRGB luminance) and their saturation cap (brown-black, not brown).
LACQUER = (20, 45)
LACQUER_SAT = 0.42
# Per-school material tint (the study's tint table; the viewer's SCHOOL table).
TINT = {'fa': '#efe9dc', 'ru': '#c88c3e', 'dao': '#f0c450', 'mo': '#e66044', 'yy': '#efe9dc', 'za': '#c4cede', 'ming': '#9c7ae0', 'zh': '#3cac74', 'nong': '#5a92e4'}
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
def lin(n): return np.where(n <= 0.04045, n / 12.92, ((n + 0.055) / 1.055) ** 2.4)


def check(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float); s = a.shape[0] / 1024; A = lin(a / 255)
    Y = A @ [0.2126, 0.7152, 0.0722]; L = a @ [0.2126, 0.7152, 0.0722]; res = []
    for i, sid in enumerate(IDS):
        t = lin(np.array([int(TINT[sid][k:k + 2], 16) for k in (1, 3, 5)]) / 255)
        y0 = int((736 + 32 * i + 9) * s); y1 = int((736 + 32 * i + 23) * s); v = float(np.percentile((A[y0:y1] * t) @ [0.2126, 0.7152, 0.0722], 70))
        res.append((f'{sid} cord', v >= TRIM_Y, f'sheet x tint p70 relative luminance {v:.3f} (min {TRIM_Y})'))
    for nm, y0 in (('lam_black', 512), ('lam_brown', 544), ('lam_cinnabar', 576), ('lam_white', 608)):
        v = float(np.median(Y[int((y0 + 14) * s):int((y0 + 20) * s)])); res.append((f'{nm} binding', v >= BIND_Y, f'median relative luminance {v:.2f} (min {BIND_Y})'))
    for nm, rows in (('plate_brown', [(156, 300)]), ('lam_brown', [(546, 556), (566, 574)])):
        b = np.concatenate([a[int(ya * s):int(yb * s)] for ya, yb in rows]); v = float((b @ [0.2126, 0.7152, 0.0722]).mean()); st = float(((b.max(2) - b.min(2)) / np.maximum(b.max(2), 1)).mean())
        res.append((f'{nm} lacquer value', LACQUER[0] <= v <= LACQUER[1] and st <= LACQUER_SAT, f'mean lum {v:.0f} ({LACQUER[0]}-{LACQUER[1]}), saturation {st:.2f} (max {LACQUER_SAT})'))
    v = float(L[int(4 * s):int(148 * s)].mean()); res.append(('plate_black value', 20 <= v <= 60, f'mean lum {v:.0f} (20-60)'))
    return res


if __name__ == '__main__':
    res = check(sys.argv[1]); f = 0
    for r, ok, val in res: f += 0 if ok else 1; print(f"{'PASS' if ok else 'FAIL'} suit_lamellar_qin {r}: {val}")
    print(f'{len(res) - f} of {len(res)} pass')
    if '--mutate' in sys.argv:
        old = {r: ok for r, ok, _ in check(sys.argv[sys.argv.index('--mutate') + 1])}; c = 0
        for r in ('ming cord', 'lam_black binding', 'plate_brown lacquer value'):
            hit = not old[r]; c += hit; print(('MUT caught ' if hit else 'MUT MISSED ') + f'approved sheet -> {r}')
        print(f'{c} of 3 mutations caught')
