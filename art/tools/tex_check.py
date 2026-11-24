#!/usr/bin/env python3
"""Palace texture checks against the style study (art/Qin-Palace-Painted-Study.md). Prints PASS/FAIL per texture and rule,
and the failing numbers only. Usage: python3 tex_check.py TEXDIR [pillarU] [lionTileM]

Rules (study, proposal 24 Nov):
- texel density 256 px/m on every axis, within 0.8x to 1.25x;
- brush scale: mean same-tone run along rows (|lum step| < 6) 4 to 15 cm inside the broad region;
- local contrast: luminance sd 8 to 30 inside the broad region (bands excluded);
- saturation cap: mean HSV saturation <= 0.55 on floors, walls and stone (lacquer and bronze accents up to 0.6).
"""
import sys
import numpy as np
from PIL import Image

D = sys.argv[1]
PU = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
LT = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
CIRC = 2 * np.pi * 0.6
# name: (px per metre u, v, broad region rows y0..y1 in a 1024 image, saturation cap)
T = {
    'hall_floor': (1024 / 4, 1024 / 4, (0, 1024), 0.55),
    'hall_wall': (1024 / 4, 1024 / 4, (170, 750), 0.55),
    'pillar': (1024 / (CIRC / PU), 1024 / 4, (140, 860), 0.6),
    'door': (1024 / 4, 1024 / 3.5, (80, 470), 0.6),
    'lion_stone': (1024 / LT, 1024 / LT, (0, 1024), 0.55),
    'bronze_trim': (1024 / 4, 1024 / 4, (0, 384), 0.6),
    'fodder_trim': (1024 / 4, 1024 / 4, (512, 704), 0.55),
}
fails = 0
checks = 0
import os
T = {k: v for k, v in T.items() if os.path.exists(f'{D}/{k}.png')}
for n, (du, dv, (y0, y1), scap) in T.items():
    im = Image.open(f'{D}/{n}.png').convert('RGB')
    s = 1024 / im.width
    a = np.asarray(im).astype(float)[int(y0 / s):int(y1 / s)]
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    mx, mn = a.max(2), a.min(2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).mean()
    eq = (np.abs(np.diff(lum, axis=1)) < 6).mean()
    run_cm = (1 / (1 - eq) if eq < 1 else 1e9) / (du / s) * 100
    sd = lum.std()
    res = [
        ('density', 0.8 * 256 <= du <= 1.25 * 256 and 0.8 * 256 <= dv <= 1.25 * 256, f'{du:.0f} x {dv:.0f} px/m'),
        ('brush scale', 4 <= run_cm <= 15, f'{run_cm:.1f} cm'),
        ('contrast', 8 <= sd <= 30, f'lum sd {sd:.1f}'),
        ('saturation', sat <= scap, f'{sat:.2f} (cap {scap})'),
    ]
    if n == 'bronze_trim':  # bronze value plan (palace study): mean luminance 70-110 on the plain plate
        res.append(('value', 70 <= lum.mean() <= 110, f'mean lum {lum.mean():.0f}'))
    if n == 'fodder_trim':  # guard and rebel sheet (art/Guard-Rebels-Study.md value plan): mean lum per row band, saturation caps for accents
        full = np.asarray(im).astype(float)
        for rn, ya, yb, lo, hi, sc in (('lacquer', 0, 256, 22, 45, 0.6), ('blue cloth', 320, 384, 70, 110, 0.6), ('headband', 448, 512, 140, 180, 0.62),
                                       ('hemp', 512, 704, 90, 130, 0.55), ('patch', 704, 832, 160, 210, 0.12)):
            b = full[int(ya / s):int(yb / s)]; bl = 0.2126 * b[..., 0] + 0.7152 * b[..., 1] + 0.0722 * b[..., 2]
            bx, bn = b.max(2), b.min(2); bs = np.where(bx > 0, (bx - bn) / np.maximum(bx, 1), 0).mean()
            res.append((f'{rn} value', lo <= bl.mean() <= hi, f'mean lum {bl.mean():.0f} ({lo}-{hi})'))
            res.append((f'{rn} saturation', bs <= sc, f'{bs:.2f} (cap {sc})'))
    checks += len(res)
    for rule, ok, val in res:
        if not ok:
            fails += 1
        print(f"{'PASS' if ok else 'FAIL'} {n} {rule}: {val}")
print(f'{checks - fails} of {checks} pass')
