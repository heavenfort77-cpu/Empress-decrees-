#!/usr/bin/env python3
"""Trim rules on the Qin proposal suit sheet (art/Colour-Clarity-Study.md, FINAL). Usage: python3 trim_check.py suit_lamellar_qin.png [--mutate APPROVED.png]
Rules: each school's cord row (band rows y0+9..y0+23) reaches texture relative luminance >= 0.21 at its 70th percentile (3:1 on a black
plate on screen; 阴阳 is bone black and exempt); no light binding across the lamella rows (rows y0+14..y0+20 of the black and brown rows:
median relative luminance <= 0.10); the former brown plate and lamella rows are black lacquer (mean lum 20-45, mean saturation <= 0.42);
the black plate rows keep their value (20-60). --mutate: the approved sheet must fail three of these."""
import sys
import numpy as np
from PIL import Image
# CONFIG
# Cord brightness the 70th percentile of the cord band must reach (texture relative luminance).
TRIM_Y = 0.21
# Largest median relative luminance across the middle of a black or brown lamella row (no light binding stripe).
STRIPE_Y = 0.10
# Lacquer value band for the former brown rows (mean sRGB luminance) and their saturation cap (brown-black, not brown).
LACQUER = (20, 45)
LACQUER_SAT = 0.42
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']


def check(path):
    a = np.asarray(Image.open(path).convert('RGB')).astype(float); s = a.shape[0] / 1024; n = a / 255
    Y = np.where(n <= 0.04045, n / 12.92, ((n + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]; L = a @ [0.2126, 0.7152, 0.0722]; res = []
    for i, sid in enumerate(IDS):
        if sid == 'yy': continue
        y0 = int((736 + 32 * i + 9) * s); y1 = int((736 + 32 * i + 23) * s); v = float(np.percentile(Y[y0:y1], 70))
        res.append((f'{sid} cord', v >= TRIM_Y, f'p70 relative luminance {v:.3f} (min {TRIM_Y})'))
    for nm, y0 in (('lam_black', 512), ('lam_brown', 544)):
        v = float(np.median(Y[int((y0 + 14) * s):int((y0 + 20) * s)])); res.append((f'{nm} no stripe', v <= STRIPE_Y, f'median relative luminance {v:.3f} (max {STRIPE_Y})'))
    for nm, ya, yb in (('plate_brown', 156, 300), ('lam_brown', 546, 574)):
        b = a[int(ya * s):int(yb * s)]; v = float(L[int(ya * s):int(yb * s)].mean()); st = float(((b.max(2) - b.min(2)) / np.maximum(b.max(2), 1)).mean())
        res.append((f'{nm} lacquer value', LACQUER[0] <= v <= LACQUER[1] and st <= LACQUER_SAT, f'mean lum {v:.0f} ({LACQUER[0]}-{LACQUER[1]}), saturation {st:.2f} (max {LACQUER_SAT})'))
    v = float(L[int(4 * s):int(148 * s)].mean()); res.append(('plate_black value', 20 <= v <= 60, f'mean lum {v:.0f} (20-60)'))
    return res


if __name__ == '__main__':
    res = check(sys.argv[1]); f = 0
    for r, ok, val in res: f += 0 if ok else 1; print(f"{'PASS' if ok else 'FAIL'} suit_lamellar_qin {r}: {val}")
    print(f'{len(res) - f} of {len(res)} pass')
    if '--mutate' in sys.argv:
        old = {r: ok for r, ok, _ in check(sys.argv[sys.argv.index('--mutate') + 1])}; c = 0
        for r in ('mo cord', 'ming cord', 'plate_brown lacquer value'):
            hit = not old[r]; c += hit; print(('MUT caught ' if hit else 'MUT MISSED ') + f'approved sheet -> {r}')
        print(f'{c} of 3 mutations caught')
