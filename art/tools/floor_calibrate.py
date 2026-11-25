#!/usr/bin/env python3
"""Paint the hall floor in klad to the written targets (art/Colour-Clarity-Study.md): palace_tex.py floor() is painted, measured
(floor_rule_check.measure), and its CONFIG scalars are corrected until the targets are met (each scalar is tied to one measure:
FLOOR_G to the relative luminance, FLOOR_C to the own-marks contrast, FLOOR_B to the autocorrelation / 50 cm blocks, FLOOR_W, the wear patch count, to the light-outlier share, FLOOR_E, the patch lightness, to the luminance sd, FLOOR_H, the scratch count, to the brush-scale run).
Seeds and mark positions never change. Prints one line per pass and the chosen values; writes calib.json.
Usage: python3 floor_calibrate.py KLAD WORKDIR SRCDIR OUTDIR STRIPDIR"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import floor_rule_check as F
# CONFIG
# Targets: texture relative luminance and tolerance (0.187 = 0.14 on screen); own marks p95/p5 and tolerance (rule: at most 1.30).
Y_T, Y_TOL = 0.187, 0.007
MK_T, MK_TOL = 1.24, 0.035
# Luminance sd window (tex_check.py needs >= 8; the wear patch count is corrected toward the target).
SD_LO, SD_T, SD_HI = 8.3, 8.9, 10.5
# Share of pixels lighter than the median by 1.5:1 (the wear patches): window for the patch count (study rule: at most 5%).
LT_LO, LT_HI = 0.02, 0.04
# Brush-scale run of tex_check.py (same-tone step 6, rule 4-15 cm): more scratches when above this.
RUN_MAX = 13.5
# Autocorrelation half-width px and 50 cm block sd above which the broad tone blots are thinned.
AC_MAX, BLK_MAX = 18, 3.0
# Passes at most.
PASSES = 10
K, WORK, SRC, OUT, STRIP = sys.argv[1:6]
p = dict(FLOOR_G=1.0, FLOOR_C=1.0179, FLOOR_B=0.36, FLOOR_N=1910, FLOOR_W=26, FLOOR_E=1.0, FLOOR_H=420); done = None
for i in range(PASSES):
    env = dict(os.environ, **{k: str(v) for k, v in p.items()})
    for cmd in ([sys.executable, f'{HERE}/palace_tex.py', WORK, '1024', 'floor'], [sys.executable, f'{HERE}/paint_palace.py', K, WORK, SRC, OUT, STRIP, 'hall_floor']):
        pr = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if pr.returncode: print('FAIL hall_floor calibration: command failed:', ' '.join(cmd[1:3]), (pr.stderr or pr.stdout)[-600:]); sys.exit(1)
    m = F.measure(f'{OUT}/hall_floor.png')
    ok = (abs(m['Y'] - Y_T) <= Y_TOL and abs(m['marks'] - MK_T) <= MK_TOL and SD_LO <= m['sd'] <= SD_HI and m['light'] <= LT_HI + 0.005 and m['run_cm'] <= RUN_MAX and max(m['acx'], m['acy']) <= AC_MAX
          and m['blk'] <= BLK_MAX and m['sat'] <= 0.545)
    print(f"pass {i + 1}: G {p['FLOOR_G']:.4f} C {p['FLOOR_C']:.4f} B {p['FLOOR_B']:.3f} N {p['FLOOR_N']} W {p['FLOOR_W']} E {p['FLOOR_E']:.3f} H {p['FLOOR_H']} -> Y {m['Y']:.4f} marks {m['marks']:.3f} sd {m['sd']:.2f} run {m['run_cm']:.1f} cm ac {m['acx']} x {m['acy']} px blk {m['blk']:.2f} sat {m['sat']:.3f} dark {m['dark']:.3f} light {m['light']:.3f} {'OK' if ok else ''}", flush=True)
    if ok: done = dict(p); break
    q = dict(p)
    if abs(m['Y'] - Y_T) > Y_TOL * 0.5: q['FLOOR_G'] = round(p['FLOOR_G'] * Y_T / m['Y'], 4)
    if abs(m['marks'] - MK_T) > MK_TOL * 0.5: q['FLOOR_C'] = round(p['FLOOR_C'] * min(1.4, max(0.6, (MK_T - 1) / max(m['marks'] - 1, 0.02))), 4)
    if not LT_LO <= m['light'] <= LT_HI: q['FLOOR_W'] = max(4, int(round(p['FLOOR_W'] * min(2.0, max(0.5, 0.03 / max(m['light'], 0.005))))))
    elif not SD_LO <= m['sd'] <= SD_HI: q['FLOOR_E'] = round(min(1.5, max(0.6, p['FLOOR_E'] * ((SD_T ** 2 - 20) / max(m['sd'] ** 2 - 20, 4)) ** 0.5)), 3)
    if max(m['acx'], m['acy']) > AC_MAX or m['blk'] > BLK_MAX: q['FLOOR_B'] = round(p['FLOOR_B'] * 0.6, 3)
    if m['run_cm'] > RUN_MAX: q['FLOOR_H'] = int(p['FLOOR_H'] * min(2.0, m['run_cm'] / 11.0))
    p = q
json.dump(dict(values=done or p, met=done is not None, last=m), open(f'{WORK}/calib.json', 'w'))
print(('PASS' if done else 'FAIL') + f" hall_floor calibration: {'targets met' if done else 'targets not met in %d passes' % PASSES} with " + ' '.join(f'{k}={v}' for k, v in p.items()))
