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
    'bronze_trim_brass': (1024 / 4, 1024 / 4, (0, 384), 0.6),
    'apex_patina': (1024 / 4, 1024 / 4, (0, 384), 0.6),
    'fodder_trim': (1024 / 4, 1024 / 4, (512, 704), 0.55),
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
    # FIXB 25 Nov (owner 02:2x): garden pond water and the core floor star-map inlay decal
    'pond_water': (256, 256, (0, 1024), 0.55),
    'star_inlay': (256, 256, (0, 1024), 0.6),
}
# Extra rules per W2 texture: value = mean luminance range of the broad region (study value plan; research palette), wrap = edges that
# must tile (edge step <= 1.5x the inside step), alpha = opaque share range per atlas cell (alpha cards), plus named checks below.
# Walkable floors have their own two limits; every other surface keeps the original ones (contrast sd >= 8, brush scale <= 15 cm).
FLOORS = ('hall_floor', 'stone_paving', 'floor_tiles', 'garden_ground', 'bridge_deck')
# Owner decision 25 Nov 14:4x: a walkable floor's contrast (luminance sd) is at least this (calm floors, so figures read on them).
FLOOR_SD_MIN = 4
# Owner decision 25 Nov 14:4x: a walkable floor's brush scale (mean same-tone run) is at most this, cm.
FLOOR_BRUSH_MAX_CM = 40
X = {
    'rammed_earth': dict(repeat=True, value=(105, 145), wrap='xy'), 'rammed_earth_core': dict(repeat=True, value=(80, 120), wrap='xy'),
    'earth_burnt': dict(repeat=True, value=(60, 105), wrap='xy', redder='rammed_earth'), 'river_stone': dict(repeat=True, value=(90, 140), wrap='xy'),
    'stone_paving': dict(repeat=True, value=(115, 150), wrap='xy'), 'floor_tiles': dict(repeat=True, value=(95, 130), wrap='xy'), 'hollow_brick': dict(value=(100, 135), wrap='xy'),
    'mural_wall': dict(value=(150, 185), wrap='x', ink=(60, 420)), 'wall_burnt': dict(value=(70, 125), wrap='x', darker='hall_wall'),
    'roof_tile': dict(value=(60, 95), wrap='xy'), 'tile_ends': dict(discs=True), 'timber': dict(value=(65, 100), wrap='xy'), 'timber_burnt': dict(value=(25, 55), wrap='xy'),
    'mercury_matcap': dict(value=(145, 190), matcap=True), 'black_lake': dict(repeat=True, value=(12, 35), wrap='xy', teal=True),
    'garden_ground': dict(repeat=True, value=(85, 125), wrap='xy'), 'garden_plants': dict(alpha=(0.06, 0.6), cells=4),
    'star_ceiling': dict(value=(22, 50), wrap='xy'), 'signal_flags': dict(alpha=(0.25, 0.7), cells=3), 'slips': dict(value=(120, 165), wrap='x'),
    'slips_burnt': dict(value=(28, 70), wrap='x'),
    'hall_wall': dict(value=(150, 185)),   # FIXB 25 Nov: approved A2 plaster value kept (owner 02:2x), study range updated to it
    'pond_water': dict(repeat=True, value=(115, 155), wrap='xy', teal=True), 'star_inlay': dict(alpha=(0.01, 0.08), cells=2, decal='hall_floor'),
}
# FIXB 25 Nov: mercury value raised from 110-190 to 145-190 (owner 02:2x 'mercury brighter'; round 3 measured 130).
# The owner's one school colour mapping (25 Nov 02:1x, W1a's 鼎 accents) in CONFIG.SCHOOLS order: signal_flags cell i must carry school i's
# accent on its top border band (median within FLAG_DIST RGB), and the band must read on the black field (p95 band lum - field median >= 30).
SCHOOL_MAP = [('ru', '#b8862e'), ('dao', '#e2b84a'), ('fa', '#d9d2c3'), ('mo', '#a8321e'), ('yinyang', '#1a1614'), ('za', '#c8ccd0'),
              ('ming', '#5b3f8c'), ('zongheng', '#2f8a5c'), ('nong', '#2e5a9c')]
FLAG_DIST = 40
# Game tell colours the floor inlay must stay clear of (index.html CONFIG: hazard ring 0xff2a10; minimap warned room #b33a2a), min RGB distance.
TELLS = [('hazard ring', '#ff2a10', 120), ('warned', '#b33a2a', 60)]
def hx(h): return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)
def hue_of(c):
    mx, mn = c.max(-1), c.min(-1); d = np.maximum(mx - mn, 1e-6); R, G, B = c[..., 0], c[..., 1], c[..., 2]
    return np.where(mx == R, 60 * (((G - B) / d) % 6), np.where(mx == G, 60 * ((B - R) / d + 2), 60 * ((R - G) / d + 4)))
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
    elif x.get('decal'):  # line decal (star inlay): thin inlay lines, no brush field to measure; read is judged over the floor below
        res = [('density', 0.8 * 256 <= du <= 1.25 * 256 and 0.8 * 256 <= dv <= 1.25 * 256, f'{du:.0f} x {dv:.0f} px/m'), ('saturation', sat <= scap, f'{sat:.2f} (cap {scap})')]
    elif du is None:  # matcap: no texel density or brush run (it is a lighting lookup, not a surface)
        res = [('contrast', 30 <= sd <= 80, f'lum sd {sd:.1f} (matcap 30-80: a mirror shows hard reflections)'), ('saturation', sat <= scap, f'{sat:.2f} (cap {scap}, cool grey)')]
    else:
        run_cm = (1 / (1 - eq) if eq < 1 else 1e9) / (du / s) * 100
        res = [
            ('density', 0.8 * 256 <= du <= 1.25 * 256 and 0.8 * 256 <= dv <= 1.25 * 256, f'{du:.0f} x {dv:.0f} px/m'),
            ('brush scale', 4 <= run_cm <= (FLOOR_BRUSH_MAX_CM if n in FLOORS else 15), f'{run_cm:.1f} cm' + (f' (floor max {FLOOR_BRUSH_MAX_CM})' if n in FLOORS else '')),
            ('contrast', (FLOOR_SD_MIN if n in FLOORS else 8) <= sd <= 30, f'lum sd {sd:.1f}' + (f' (floor min {FLOOR_SD_MIN})' if n in FLOORS else '')),
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
    if x.get('repeat'):  # repeat visibility: sd of 50 cm block means (what still shows at the wide camera, where a 4 m repeat becomes a
        # grid); the approved hall floor measures 3.3 and shows no grid, stone paving round 1 measured 6.1 and did (lead review 25 Nov)
        B = lum_of(full); blk = B.reshape(8, B.shape[0] // 8, 8, B.shape[1] // 8).mean((1, 3)).std()
        res.append(('repeat', blk <= 3.5, f'50 cm block sd {blk:.1f} (max 3.5)'))
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
    if x.get('decal') and os.path.exists(f"{D}/{x['decal']}.png"):  # inlay over the approved floor: keeps the floor read, subtle, no tell colour
        fl = np.asarray(Image.open(f"{D}/{x['decal']}.png").convert('RGB').resize(rgba.shape[1::-1])).astype(float); A = rgba[..., 3] > 127
        comp = np.where(A[..., None], full, fl)
        dl = lum_of(comp).mean() - lum_of(fl).mean(); dh = abs(hue_of(comp.reshape(-1, 3).mean(0)) - hue_of(fl.reshape(-1, 3).mean(0)))
        res.append(('floor read', abs(dl) <= 8 and dh <= 6, f'mean lum {dl:+.1f} (max 8), mean hue shift {dh:.1f} deg (max 6) over {x["decal"]}'))
        ic = full[A]; con = lum_of(ic).mean() - lum_of(fl[A]).mean()
        res.append(('subtle', 25 <= con <= 75, f'inlay minus floor lum {con:.0f} (25-75: seen, not loud)'))
        for tn, th, tmin in TELLS:
            dmin = np.sqrt(((ic - hx(th)) ** 2).sum(-1)).min(); res.append((f'not {tn}', dmin >= tmin, f'nearest inlay pixel to {th} at {dmin:.0f} (min {tmin})'))
        mg = 24 * rgba.shape[0] // 1024; edge = np.concatenate([A[:mg].ravel(), A[-mg:].ravel(), A[:, :mg].ravel(), A[:, -mg:].ravel()]).mean()
        res.append(('edge clear', edge == 0, f'opaque share in the {mg} px border {edge:.4f} (0: cells turn without a seam)'))
    if n == 'signal_flags':
        C = rgba.shape[1] / 3; L_ = lum_of(full); bad = []; weak = []
        for i, (sid, h) in enumerate(SCHOOL_MAP):
            x0, y0 = int((i % 3) * C + 12 / s), int((i // 3) * C + 40 / s); w = C - 30 / s; hh = C * 0.62
            band = full[y0 + int(6 / s):y0 + int(10 / s), x0 + int(30 / s):x0 + int(0.7 * w)].reshape(-1, 3)
            med = np.median(band, 0); dist = np.linalg.norm(med - hx(h))
            if dist > FLAG_DIST: bad.append(f'{sid} {dist:.0f}')
            win = L_[y0:y0 + int(18 / s), x0 + int(30 / s):x0 + int(0.7 * w)]; fld = L_[y0 + int(hh * 0.3):y0 + int(hh * 0.4), x0 + int(0.62 * w):x0 + int(0.75 * w)]
            rd = np.percentile(win, 95) - np.median(fld)
            if rd < 30: weak.append(f'{sid} {rd:.0f}')
        res.append(('school colours', not bad, 'owner mapping, all 9 within %d' % FLAG_DIST if not bad else 'off: ' + ', '.join(bad)))
        res.append(('band reads', not weak, 'all 9 bands >= 30 over the field' if not weak else 'weak: ' + ', '.join(weak)))
    if 'redder' in x and os.path.exists(f"{D}/{x['redder']}.png"):
        o = np.asarray(Image.open(f"{D}/{x['redder']}.png").convert('RGB')).astype(float)
        d0 = (o[..., 0] - o[..., 1]).mean(); d1 = (full[..., 0] - full[..., 1]).mean()
        res.append(('reddened', d1 >= d0 + 8, f'red minus green {d1:.0f} vs unburnt {d0:.0f} (min +8)'))
    if 'darker' in x and os.path.exists(f"{D}/{x['darker']}.png"):
        o = lum_of(np.asarray(Image.open(f"{D}/{x['darker']}.png").convert('RGB')).astype(float)[170:750]).mean()
        res.append(('darker than unburnt', lum[op].mean() <= o - 25, f'mean lum {lum[op].mean():.0f} vs {o:.0f} (at least 25 darker)'))
    if n == 'bronze_trim':  # bronze value plan (palace study): mean luminance 70-110 on the plain plate
        res.append(('value', 70 <= lum.mean() <= 110, f'mean lum {lum.mean():.0f}'))
    if n == 'bronze_trim_brass':  # brass variant (beast round 4): fresh brass-gold plate, mean luminance 120-160 and mean hue 36-46 deg
        hh = a[..., :3]; mxh, mnh = hh.max(2), hh.min(2); dd = np.maximum(mxh - mnh, 1)
        hue = np.where(mxh == hh[..., 0], 60 * ((hh[..., 1] - hh[..., 2]) / dd % 6), np.where(mxh == hh[..., 1], 60 * ((hh[..., 2] - hh[..., 0]) / dd + 2), 60 * ((hh[..., 0] - hh[..., 1]) / dd + 4)))
        res.append(('value', 120 <= lum.mean() <= 160, f'mean lum {lum.mean():.0f}'))
        res.append(('hue', 36 <= hue.mean() <= 46, f'mean hue {hue.mean():.0f} deg'))
    if n == 'apex_patina':  # W4: dormant apex sheet reads as patina (green over red on the plain plate), darker than the live bronze
        g_r = a[..., 1].mean() - a[..., 0].mean()
        res.append(('patina hue', g_r > 4, f'mean G - R {g_r:.1f} (min 4)'))
        res.append(('patina value', 55 <= lum.mean() <= 105, f'mean lum {lum.mean():.0f} (55-105)'))
    if n == 'fodder_trim':  # guard and rebel sheet (art/Guard-Rebels-Study.md value plan): mean lum per row band, saturation caps for accents
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
# Suit trim sheets (art/Qin-Lamellar-Suits-Study.md, W3 25 Nov; proposals until the owner approves): run when they are in TEXDIR.
# name: (native px, metres across); fields: (rows y0..y1 at native px, brush run cm range, lum sd range, saturation cap, mean lum range)
SUIT = {
    'suit_lamellar': (1024, 4.0, {'plate_black': ((4, 148), (4, 25), (2, 15), 0.6, (20, 60)), 'plate_brown': ((156, 300), (4, 25), (4, 20), 0.6, (35, 100)),
                                  'plate_cinnabar': ((308, 404), (4, 25), (4, 22), 0.8, (60, 120)), 'plate_white': ((412, 508), (4, 25), (4, 20), 0.2, (170, 230))}),
    'suit_bronze': (512, 2.0, {'plain': ((4, 188), (4, 15), (6, 30), 0.6, (85, 135))}),
    'suit_cloth': (512, 2.0, {'cloth': ((0, 512), (2, 30), (3, 25), 0.12, (180, 240))}),
}
# school binding colours (cord rows of suit_lamellar, 32 px each from y 736, school order) and the largest RGB distance of the row median
CORD = [('fa', '#d9d2c3'), ('ru', '#94622c'), ('dao', '#e2b84a'), ('mo', '#a8321e'), ('yy', '#1a1614'), ('za', '#b2bccb'), ('ming', '#5b3f8c'), ('zh', '#2f8a5c'), ('nong', '#2e5a9c')]
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
if 'mercury_matcap' in HI:  # mercury is the only bright cool surface: its highlights (95th percentile) are the brightest of every palace texture
    # (round 2: was 'mean brightest'; a light disc passed it and read as white paint on screen, a chrome matcap is dark with bright highlights)
    others = {k: v for k, v in HI.items() if k != 'mercury_matcap'}; top = max(others, key=others.get); ok = HI['mercury_matcap'] > others[top] + 10
    checks += 1; fails += 0 if ok else 1
    print(f"{'PASS' if ok else 'FAIL'} mercury_matcap brightest highlights: p95 {HI['mercury_matcap']:.0f} vs next {top} {others[top]:.0f} (min +10)")
print(f'{checks - fails} of {checks} pass')
