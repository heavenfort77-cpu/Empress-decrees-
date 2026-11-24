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
    # W2 surfaces (art/tools/arch_tex.py; 4 m per repeat = 256 px/m); extra rules in X below
    'rammed_earth': (256, 256, (0, 1024), 0.55),
    'rammed_earth_core': (256, 256, (0, 1024), 0.55),
    'earth_burnt': (256, 256, (0, 1024), 0.55),
    'river_stone': (256, 256, (0, 1024), 0.55),
    'stone_paving': (256, 256, (0, 1024), 0.55),
    'floor_tiles': (256, 256, (0, 1024), 0.55),
    'hollow_brick': (256, 256, (0, 1024), 0.55),
    'mural_wall': (256, 256, (450, 750), 0.55),
    'wall_burnt': (256, 256, (170, 750), 0.55),
    'roof_tile': (256, 256, (0, 1024), 0.55),
    'tile_ends': (256, 256, (0, 1024), 0.55),
    'timber': (256, 256, (0, 1024), 0.55),
    'timber_burnt': (256, 256, (0, 1024), 0.55),
    'mercury_matcap': (None, None, (212, 812), 0.12),
    'black_lake': (256, 256, (0, 1024), 0.55),
    'garden_ground': (256, 256, (0, 1024), 0.55),
    'garden_plants': (256, 256, (0, 1024), 0.55),
    'star_ceiling': (256, 256, (0, 1024), 0.55),
    'signal_flags': (256, 256, (0, 1024), 0.6),
    'slips': (256, 256, (0, 512), 0.55),
    'slips_burnt': (256, 256, (0, 512), 0.55),
}
# Extra rules per W2 texture: value = mean luminance range of the broad region (study value plan; research palette), wrap = edges that
# must tile (edge step <= 1.5x the inside step), alpha = opaque share range per atlas cell (alpha cards), plus named checks below.
X = {
    'rammed_earth': dict(value=(105, 145), wrap='xy'), 'rammed_earth_core': dict(value=(80, 120), wrap='xy'),
    'earth_burnt': dict(value=(60, 105), wrap='xy', redder='rammed_earth'), 'river_stone': dict(value=(90, 140), wrap='xy'),
    'stone_paving': dict(value=(115, 150), wrap='xy'), 'floor_tiles': dict(value=(95, 130), wrap='xy'), 'hollow_brick': dict(value=(100, 135), wrap='xy'),
    'mural_wall': dict(value=(150, 185), wrap='x', ink=(60, 420)), 'wall_burnt': dict(value=(70, 125), wrap='x', darker='hall_wall'),
    'roof_tile': dict(value=(60, 95), wrap='xy'), 'tile_ends': dict(discs=True), 'timber': dict(value=(65, 100), wrap='xy'), 'timber_burnt': dict(value=(25, 55), wrap='xy'),
    'mercury_matcap': dict(value=(110, 190), matcap=True), 'black_lake': dict(value=(12, 35), wrap='xy', teal=True),
    'garden_ground': dict(value=(85, 125), wrap='xy'), 'garden_plants': dict(alpha=(0.06, 0.6), cells=4),
    'star_ceiling': dict(value=(22, 50), wrap='xy'), 'signal_flags': dict(alpha=(0.25, 0.7), cells=3), 'slips': dict(value=(120, 165), wrap='x'),
    'slips_burnt': dict(value=(28, 70), wrap='x'),
}
fails = 0
checks = 0
import os
T = {k: v for k, v in T.items() if os.path.exists(f'{D}/{k}.png')}
def lum_of(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
MEANS = {}; HI = {}
for n, (du, dv, (y0, y1), scap) in T.items():
    x = X.get(n, {})
    rgba = np.asarray(Image.open(f'{D}/{n}.png').convert('RGBA')).astype(float)
    s = 1024 / rgba.shape[1]
    full = rgba[..., :3]
    a = full[int(y0 / s):int(y1 / s)]
    op = rgba[int(y0 / s):int(y1 / s), :, 3] > 127 if 'alpha' in x else np.ones(a.shape[:2], bool)
    if x.get('discs'):  # tile-end atlas: rules apply inside the disc faces (16 discs, radius 22 px), the board is only rim colour
        yy, xx = np.mgrid[0:rgba.shape[0], 0:rgba.shape[1]]; m = np.zeros(rgba.shape[:2], bool)
        for i in range(8):
            for cy in (128, 384): m |= (xx - (64 + 128 * i) / s) ** 2 + (yy - cy / s) ** 2 < (22 / s) ** 2
        op = m[int(y0 / s):int(y1 / s)]
    if x.get('matcap'):  # inside the disc only
        yy, xx = np.mgrid[0:rgba.shape[0], 0:rgba.shape[1]]
        op = ((xx - 512 / s) ** 2 + (yy - 512 / s) ** 2 < (480 / s) ** 2)[int(y0 / s):int(y1 / s)]
    if not op.any():  # nothing left to measure (e.g. an alpha card with no pixel over the alpha test): every rule of this texture fails
        checks += 1; fails += 1; print(f'FAIL {n} alpha test: no opaque pixel'); continue
    lum = lum_of(a)
    mx, mn = a.max(2), a.min(2)
    satm = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    sat = satm[op].mean()
    stepok = op[:, 1:] & op[:, :-1]
    eq = (np.abs(np.diff(lum, axis=1)) < 6)[stepok].mean()
    sd = lum[op].std()
    MEANS[n] = lum[op].mean(); HI[n] = np.percentile(lum[op], 95)
    if x.get('discs'):  # ornament atlas: fine detail may run under 4 cm (study: rules, lozenges, masks); no brush-scale rule
        res = [('density', 0.8 * 256 <= du <= 1.25 * 256 and 0.8 * 256 <= dv <= 1.25 * 256, f'{du:.0f} x {dv:.0f} px/m'),
               ('contrast', 8 <= sd <= 30, f'lum sd {sd:.1f} inside the discs'), ('saturation', sat <= scap, f'{sat:.2f} (cap {scap})')]
    elif du is None:  # matcap: no texel density or brush run (it is a lighting lookup, not a surface)
        res = [('contrast', 30 <= sd <= 80, f'lum sd {sd:.1f} (matcap 30-80: a mirror shows hard reflections)'), ('saturation', sat <= scap, f'{sat:.2f} (cap {scap}, cool grey)')]
    else:
        run_cm = (1 / (1 - eq) if eq < 1 else 1e9) / (du / s) * 100
        res = [
            ('density', 0.8 * 256 <= du <= 1.25 * 256 and 0.8 * 256 <= dv <= 1.25 * 256, f'{du:.0f} x {dv:.0f} px/m'),
            ('brush scale', 4 <= run_cm <= 15, f'{run_cm:.1f} cm'),
            ('contrast', 8 <= sd <= 30, f'lum sd {sd:.1f}'),
            ('saturation', sat <= scap, f'{sat:.2f} (cap {scap})'),
        ]
    if 'value' in x:
        lo, hi = x['value']; v = lum[op].mean(); res.append(('value', lo <= v <= hi, f'mean lum {v:.0f} ({lo}-{hi})'))
    if 'wrap' in x:  # seam: the step across the wrapped edge against the mean step inside
        L = lum_of(full)
        for ax_name, ax in (('x', 1), ('y', 0)):
            if ax_name not in x['wrap']: continue
            steps = np.abs(np.diff(L, axis=ax)).mean(axis=1 - ax)  # mean step per line across the image
            inside = steps.mean(); p99 = np.percentile(steps, 99)
            edge = np.abs(L.take(0, axis=ax) - L.take(-1, axis=ax)).mean()
            # a seam is an outlier step: edge <= 1.5x the mean step, or no worse than the 1% of inside lines that sit on drawn joints
            res.append((f'seam {ax_name}', edge <= max(1.5 * inside, p99), f'edge step {edge:.1f} vs inside mean {inside:.1f}, p99 {p99:.1f}'))
    if 'alpha' in x:
        lo, hi = x['alpha']; c = x['cells']; A = rgba[..., 3] > 127; h = A.shape[0] // c; w = A.shape[1] // c
        shares = [A[j * h:(j + 1) * h, i * w:(i + 1) * w].mean() for j in range(c) for i in range(c)]
        res.append(('coverage', all(lo <= v <= hi for v in shares), f'opaque share per cell {min(shares):.2f}-{max(shares):.2f} ({lo}-{hi})'))
        lost = ((rgba[..., 3] > 0) & (rgba[..., 3] < 128)).sum() / max(1, (rgba[..., 3] > 0).sum())
        res.append(('alpha test', lost <= 0.2, f'{lost:.2f} of drawn pixels fall under the 0.5 alpha test (max 0.2)'))
    if x.get('matcap'):
        b_r = (a[..., 2] - a[..., 0])[op].mean()
        res.append(('cool', b_r >= 4, f'blue minus red {b_r:.1f} (min 4)'))
        hz = np.array([0x3F, 0xE6, 0xF0], float); dist = np.sqrt(((a[op] - hz) ** 2).sum(-1)).min()
        res.append(('not hazard cyan', dist >= 80, f'nearest pixel to #3FE6F0 at distance {dist:.0f} (min 80)'))
    if x.get('teal'):
        g_r = (a[..., 1] - a[..., 0]).mean(); res.append(('teal tint', g_r >= 4, f'green minus red {g_r:.1f} (min 4; not cloth black)'))
    if 'ink' in x:
        b = lum_of(full[x['ink'][0]:x['ink'][1]]); cov = (b < 110).mean()
        res.append(('mural ink', 0.08 <= cov <= 0.4, f'figure share {cov:.2f} of the band (0.08-0.4)'))
    if 'redder' in x and os.path.exists(f"{D}/{x['redder']}.png"):
        o = np.asarray(Image.open(f"{D}/{x['redder']}.png").convert('RGB')).astype(float)
        d0 = (o[..., 0] - o[..., 1]).mean(); d1 = (full[..., 0] - full[..., 1]).mean()
        res.append(('reddened', d1 >= d0 + 8, f'red minus green {d1:.0f} vs unburnt {d0:.0f} (min +8)'))
    if 'darker' in x and os.path.exists(f"{D}/{x['darker']}.png"):
        o = lum_of(np.asarray(Image.open(f"{D}/{x['darker']}.png").convert('RGB')).astype(float)[170:750]).mean()
        res.append(('darker than unburnt', lum[op].mean() <= o - 25, f'mean lum {lum[op].mean():.0f} vs {o:.0f} (at least 25 darker)'))
    if n == 'bronze_trim':  # bronze value plan (palace study): mean luminance 70-110 on the plain plate
        res.append(('value', 70 <= lum.mean() <= 110, f'mean lum {lum.mean():.0f}'))
    checks += len(res)
    for rule, ok, val in res:
        if not ok:
            fails += 1
        print(f"{'PASS' if ok else 'FAIL'} {n} {rule}: {val}")
if 'mercury_matcap' in HI:  # mercury is the only bright cool surface: its highlights (95th percentile) are the brightest of every palace texture
    # (round 2: was 'mean brightest'; a light disc passed it and read as white paint on screen, a chrome matcap is dark with bright highlights)
    others = {k: v for k, v in HI.items() if k != 'mercury_matcap'}; top = max(others, key=others.get); ok = HI['mercury_matcap'] > others[top] + 10
    checks += 1; fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'} mercury_matcap brightest highlights: p95 {HI['mercury_matcap']:.0f} vs next {top} {others[top]:.0f} (min +10)")
print(f'{checks - fails} of {checks} pass')
