#!/usr/bin/env python3
"""Paint the hall floor in klad to the written targets (art/Colour-Clarity-Study.md): palace_tex.py floor() is painted, measured
(floor_rule_check.measure), and its CONFIG scalars are corrected until the targets are met (each scalar is tied to one measure:
FLOOR_G to the relative luminance, FLOOR_C to the own-marks contrast, FLOOR_B to the autocorrelation / 50 cm blocks, FLOOR_D, the broad drift amplitude, to the luminance sd, FLOOR_H, the scratch count, to the brush-scale run).
Seeds and mark positions never change. Prints one line per pass and the chosen values; writes calib.json.
Usage: python3 floor_calibrate.py KLAD WORKDIR SRCDIR OUTDIR STRIPDIR"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import floor_rule_check as F
# CONFIG
# Targets: texture relative luminance and tolerance (0.187 = 0.14 on screen); own marks inside 1 m (p95/p5) and tolerance (rule: at most 1.30).
Y_T, Y_TOL = 0.187, 0.007
MK_T, MK_TOL = 1.25, 0.035
# Luminance sd window (tex_check.py needs >= 8; the drift amplitude is corrected toward the target).
SD_LO, SD_T, SD_HI = 8.3, 8.9, 10.0
# Brush-scale run of tex_check.py (same-tone step 6, rule 4-15 cm): more fine scratches when above this; scratch count cap.
RUN_MAX, H_MAX = 13.5, 1600
# Passes at most.
PASSES = 10
K, WORK, SRC, OUT, STRIP = sys.argv[1:6]
p = dict(FLOOR_G=0.9787, FLOOR_C=0.8589, FLOOR_B=0.36, FLOOR_N=1910, FLOOR_D=1.0, FLOOR_H=420); done = None
for i in range(PASSES):
    env = dict(os.environ, **{k: str(v) for k, v in p.items()})
    for cmd in ([sys.executable, f'{HERE}/palace_tex.py', WORK, '1024', 'floor'], [sys.executable, f'{HERE}/paint_palace.py', K, WORK, SRC, OUT, STRIP, 'hall_floor']):
        pr = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if pr.returncode: print('FAIL hall_floor calibration: command failed:', ' '.join(cmd[1:3]), (pr.stderr or pr.stdout)[-600:]); sys.exit(1)
    m = F.measure(f'{OUT}/hall_floor.png')
    ok = (abs(m['Y'] - Y_T) <= Y_TOL and abs(m['lmarks'] - MK_T) <= MK_TOL and SD_LO <= m['sd'] <= SD_HI and m['run_cm'] <= RUN_MAX and m['pale'] <= 0.003 and m['sat'] <= 0.545)
    print(f"pass {i + 1}: G {p['FLOOR_G']:.4f} C {p['FLOOR_C']:.4f} D {p['FLOOR_D']:.3f} H {p['FLOOR_H']} -> Y {m['Y']:.4f} marks in 1 m {m['lmarks']:.3f} (tile {m['marks']:.3f}) sd {m['sd']:.2f} (without drift {m['lsd']:.2f}) run {m['run_cm']:.1f} cm ac {m['acx']} x {m['acy']} px blk {m['blk']:.2f} sat {m['sat']:.3f} pale {m['pale']:.4f} dark {m['dark']:.4f} {'OK' if ok else ''}", flush=True)
    if ok: done = dict(p); break
    q = dict(p)
    if abs(m['Y'] - Y_T) > Y_TOL * 0.5: q['FLOOR_G'] = round(p['FLOOR_G'] * Y_T / m['Y'], 4)
    if abs(m['lmarks'] - MK_T) > MK_TOL * 0.5: q['FLOOR_C'] = round(p['FLOOR_C'] * min(1.4, max(0.6, (MK_T - 1) / max(m['lmarks'] - 1, 0.02))), 4)
    if not SD_LO <= m['sd'] <= SD_HI:
        dv = m['sd'] ** 2 - m['lsd'] ** 2; need = SD_T ** 2 - m['lsd'] ** 2
        q['FLOOR_D'] = round(min(6.0, p['FLOOR_D'] * (2.0 if dv < 1 else min(2.0, max(0.5, (max(need, 1) / dv) ** 0.5)))), 3)
    if m['run_cm'] > RUN_MAX: q['FLOOR_H'] = min(H_MAX, int(p['FLOOR_H'] * min(2.0, m['run_cm'] / 11.0)))
    p = q
json.dump(dict(values=done or p, met=done is not None, last=m), open(f'{WORK}/calib.json', 'w'))
print(('PASS' if done else 'FAIL') + f" hall_floor calibration: {'targets met' if done else 'targets not met in %d passes' % PASSES} with " + ' '.join(f'{k}={v}' for k, v in p.items()))
