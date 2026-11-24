#!/usr/bin/env python3
"""Checks for the dormant giants' patina sheet (assets/tex/bronze_trim_patina.png), the same rules as tex_check.py (palace study) plus
a patina value and hue rule. Prints PASS/FAIL per rule and 'N of M pass'. Usage: python3 giant_tex_check.py PNG
Rules: density 256 px/m (1024 px = 4 m); brush scale 4-15 cm (mean same-tone run on the plain plate rows 0-384); contrast lum sd 8-30;
saturation <= 0.6 (bronze accent cap); value: plain plate mean luminance 80-125 (verdigris #4F7A62 is lum 111; dormant giants must stay
darker than the awake brass, plate lum 137); hue: mean hue 120-170 deg (green, not the brass 36-46 or the bronze 29-36).
"""
import sys
import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert('RGB')
s = 1024 / im.width
a = np.asarray(im).astype(float)[0:int(384 / s)]
lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
mx, mn = a.max(2), a.min(2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).mean()
eq = (np.abs(np.diff(lum, axis=1)) < 6).mean()
du = im.width / 4.0 * s
run_cm = (1 / (1 - eq) if eq < 1 else 1e9) / (du / s) * 100
d = np.maximum(mx - mn, 1)
hue = np.where(mx == a[..., 0], 60 * ((a[..., 1] - a[..., 2]) / d % 6), np.where(mx == a[..., 1], 60 * ((a[..., 2] - a[..., 0]) / d + 2), 60 * ((a[..., 0] - a[..., 1]) / d + 4)))
res = [('density', 0.8 * 256 <= du <= 1.25 * 256, f'{du:.0f} px/m'), ('brush scale', 4 <= run_cm <= 15, f'{run_cm:.1f} cm'),
       ('contrast', 8 <= lum.std() <= 30, f'lum sd {lum.std():.1f}'), ('saturation', sat <= 0.6, f'{sat:.2f} (cap 0.6)'),
       ('value', 80 <= lum.mean() <= 125, f'mean lum {lum.mean():.0f} (80-125)'), ('hue', 120 <= hue.mean() <= 170, f'mean hue {hue.mean():.0f} deg (120-170)')]
fails = 0
for rule, ok, val in res:
    fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'} patina {rule}: {val}")
print(f'{len(res) - fails} of {len(res)} pass')
