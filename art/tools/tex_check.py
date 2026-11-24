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
    checks += len(res)
    for rule, ok, val in res:
        if not ok:
            fails += 1
        print(f"{'PASS' if ok else 'FAIL'} {n} {rule}: {val}")
# Suit trim sheets (art/Qin-Lamellar-Suits-Study.md, W3 25 Nov; proposals until the owner approves): run when they are in TEXDIR.
# name: (native px, metres across); fields: (rows y0..y1 at native px, brush run cm range, lum sd range, saturation cap, mean lum range)
SUIT = {
    'suit_lamellar': (1024, 4.0, {'plate_black': ((4, 148), (4, 25), (2, 15), 0.6, (20, 60)), 'plate_brown': ((156, 300), (4, 25), (4, 20), 0.6, (35, 100)),
                                  'plate_cinnabar': ((308, 404), (4, 25), (4, 22), 0.8, (60, 120)), 'plate_white': ((412, 508), (4, 25), (4, 20), 0.2, (170, 230))}),
    'suit_bronze': (512, 2.0, {'plain': ((4, 188), (4, 15), (6, 30), 0.6, (85, 135))}),
    'suit_cloth': (512, 2.0, {'cloth': ((0, 512), (2, 30), (3, 25), 0.12, (180, 240))}),
}
# school binding colours (cord rows of suit_lamellar, 32 px each from y 736, school order) and the largest RGB distance of the row median
CORD = [('fa', '#b0402c'), ('ru', '#c9a54a'), ('dao', '#e4ded0'), ('mo', '#b8862e'), ('yy', '#1e1b1a'), ('za', '#2e5a9c'), ('ming', '#bfc3c6'), ('zh', '#5b3f8c'), ('nong', '#2f8a5c')]
CORD_DIST = 50
# lamella width (the plate pitch across a lamellar row), cm
LAM_CM = (7, 9)
for n, (npx, metres, fields) in SUIT.items():
    if not os.path.exists(f'{D}/{n}.png'):
        continue
    im = Image.open(f'{D}/{n}.png').convert('RGB'); s = npx / im.width; A = np.asarray(im).astype(float)
    dens = im.width / metres * s
    res = [('density', 0.8 * 256 <= dens <= 1.25 * 256, f'{dens:.0f} px/m')]
    for fn, ((y0, y1), runr, sdr, scap, lumr) in fields.items():
        a = A[int(y0 / s):int(y1 / s)]
        lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        mx, mn = a.max(2), a.min(2); sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0).mean()
        eq = (np.abs(np.diff(lum, axis=1)) < 6).mean(); run_cm = (1 / (1 - eq) if eq < 1 else 1e9) / (256 / s) * 100
        res += [(f'{fn} brush scale', runr[0] <= run_cm <= runr[1], f'{run_cm:.1f} cm'), (f'{fn} contrast', sdr[0] <= lum.std() <= sdr[1], f'lum sd {lum.std():.1f}'),
                (f'{fn} saturation', sat <= scap, f'{sat:.2f} (cap {scap})'), (f'{fn} value', lumr[0] <= lum.mean() <= lumr[1], f'mean lum {lum.mean():.0f}')]
    if n == 'suit_lamellar':
        for i, (sid, hx) in enumerate(CORD):
            y = (736 + 32 * i) / s; a = A[int(y + 10 / s):int(y + 22 / s)].reshape(-1, 3)
            med = np.median(a, 0); want = np.array([int(hx[j:j + 2], 16) for j in (1, 3, 5)]); dist = np.linalg.norm(med - want)
            res.append((f'cord {sid} colour', dist <= CORD_DIST, f'median #{int(med[0]):02x}{int(med[1]):02x}{int(med[2]):02x} vs {hx}, distance {dist:.0f}'))
        for k, y in enumerate((512, 544, 576, 608)):
            lum = (A[int((y + 8) / s):int((y + 24) / s)] @ [0.2126, 0.7152, 0.0722]).mean(0); lum = lum - lum.mean()
            P = np.abs(np.fft.rfft(lum)) ** 2; fr = np.fft.rfftfreq(len(lum)); per = np.where(fr > 0, 1 / np.maximum(fr, 1e-9), 0)
            ok_ = (per >= 8 / s) & (per <= 80 / s); pitch = per[ok_][np.argmax(P[ok_])] * s   # dominant plate period in 8-80 px (mutation: doubled width caught)
            cm = pitch / 256 * 100
            res.append((f'lamella row {k} width', LAM_CM[0] <= cm <= LAM_CM[1], f'{cm:.1f} cm'))
    checks += len(res)
    for rule, ok, val in res:
        if not ok:
            fails += 1
        print(f"{'PASS' if ok else 'FAIL'} {n} {rule}: {val}")
print(f'{checks - fails} of {checks} pass')
