#!/usr/bin/env python3
"""Paint the hall floor in klad to the written targets (art/Colour-Clarity-Study.md): palace_tex.py floor() is painted, measured
(floor_rule_check.measure), and its four CONFIG scalars are corrected until the targets are met (each scalar is tied to one measure:
FLOOR_G to the relative luminance, FLOOR_C to the luminance sd, FLOOR_B to the autocorrelation / 50 cm blocks, FLOOR_N to the brush-scale run).
Seeds and mark positions never change. Prints one line per pass and the chosen values; writes calib.json.
Usage: python3 floor_calibrate.py KLAD WORKDIR SRCDIR OUTDIR STRIPDIR"""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import floor_rule_check as F
# CONFIG
# Targets: texture relative luminance and tolerance; luminance sd and tolerance.
Y_T, Y_TOL = 0.200, 0.008
SD_T, SD_TOL = 6.6, 0.7
# Brush-scale run (tex_check.py rule 4-15 cm): corrected when above this.
RUN_MAX = 13.5
# Autocorrelation half-width px and 50 cm block sd above which the broad tone blots are thinned.
AC_MAX, BLK_MAX = 16, 3.0
# Passes at most.
PASSES = 8
K, WORK, SRC, OUT, STRIP = sys.argv[1:6]
# Start values (the values the shipped round 3 floor was painted with, run 45553818769).
p = dict(FLOOR_G=0.9794, FLOOR_C=1.1366, FLOOR_B=1.0, FLOOR_N=2600); done = None
for i in range(PASSES):
    env = dict(os.environ, **{k: str(v) for k, v in p.items()})
    for cmd in ([sys.executable, f'{HERE}/palace_tex.py', WORK, '1024', 'floor'], [sys.executable, f'{HERE}/paint_palace.py', K, WORK, SRC, OUT, STRIP, 'hall_floor']):
        pr = subprocess.run(cmd, env=env, capture_output=True, text=True)
        if pr.returncode: print('FAIL hall_floor calibration: command failed:', ' '.join(cmd[1:3]), (pr.stderr or pr.stdout)[-600:]); sys.exit(1)
    m = F.measure(f'{OUT}/hall_floor.png')
    ok = abs(m['Y'] - Y_T) <= Y_TOL and abs(m['sd'] - SD_T) <= SD_TOL and m['run_cm'] <= RUN_MAX and max(m['acx'], m['acy']) <= AC_MAX and m['blk'] <= BLK_MAX
    print(f"pass {i + 1}: G {p['FLOOR_G']:.4f} C {p['FLOOR_C']:.4f} B {p['FLOOR_B']:.3f} N {p['FLOOR_N']} -> Y {m['Y']:.4f} sd {m['sd']:.2f} run {m['run_cm']:.1f} cm ac {m['acx']} x {m['acy']} px blk {m['blk']:.2f} sat {m['sat']:.3f} marks {m['marks']:.3f} {'OK' if ok else ''}", flush=True)
    if ok: done = dict(p); break
    q = dict(p)
    if abs(m['Y'] - Y_T) > Y_TOL * 0.5: q['FLOOR_G'] = round(p['FLOOR_G'] * Y_T / m['Y'], 4)
    if abs(m['sd'] - SD_T) > SD_TOL * 0.5: q['FLOOR_C'] = round(p['FLOOR_C'] * min(1.6, max(0.6, SD_T / m['sd'])), 4)
    if max(m['acx'], m['acy']) > AC_MAX or m['blk'] > BLK_MAX: q['FLOOR_B'] = round(p['FLOOR_B'] * 0.6, 3)
    if m['run_cm'] > RUN_MAX: q['FLOOR_N'] = int(p['FLOOR_N'] * min(2.0, m['run_cm'] / 11.0))
    p = q
json.dump(dict(values=done or p, met=done is not None, last=m), open(f'{WORK}/calib.json', 'w'))
print(('PASS' if done else 'FAIL') + f" hall_floor calibration: {'targets met' if done else 'targets not met in %d passes' % PASSES} with FLOOR_G={p['FLOOR_G']} FLOOR_C={p['FLOOR_C']} FLOOR_B={p['FLOOR_B']} FLOOR_N={p['FLOOR_N']}")
