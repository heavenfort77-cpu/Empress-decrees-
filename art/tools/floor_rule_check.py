#!/usr/bin/env python3
"""Walkable-floor rules (art/Colour-Clarity-Study.md, COLOUR 25 Nov): a floor a black-lacquer figure and its pale rim both read on.
Prints PASS/FAIL per floor and rule. Usage: python3 floor_rule_check.py TEXDIR [--mutate] [name=path ...]
  TEXDIR holds hall_floor.png, stone_paving.png, floor_tiles.png, garden_ground.png, bridge_deck.png (the bridge's own deck texture); name=path adds a candidate measured by the
  rules of floor `name` (printed as name_cand). --mutate: three broken copies of the hall floor must each fail their rule."""
import os, sys
import numpy as np
from PIL import Image
# CONFIG
# Texture relative luminance band for every walkable floor (on screen x 0.75 under the game's lights: 0.125-0.195).
FLOOR_Y = (0.167, 0.26)
# Largest contrast between a floor's own light and dark marks (p95 against p5 of the texture's relative luminance).
MARKS = 1.30
# Mean HSV saturation cap for every walkable floor; the hall floor's own band (still cinnabar, not grey).
SAT_CAP = 0.55
HALL_SAT = (0.48, 0.55)
# Hall floor luminance sd band (sRGB luminance 0-255). FINAL round, set once: the lower bound is the palace study's own (tex_check.py: sd >= 8,
# never to be lowered); the upper bound 12 keeps the floor well under the walls and doors (17 to 65). An evenly painted floor cannot meet
# sd >= 8 and the marks rule together (run 45557070732: sd 4.4 at marks 1.26), so the sd is carried by sparse wear patches and scratches.
HALL_SD = (8.0, 12.0)
# Hall floor outliers: share of pixels darker than the median by 1.5:1 or more (dark flecks read as debris next to black figures), and share
# lighter by 1.5:1 or more (wear patches), each at most this.
HALL_DARK, HALL_LIGHT = 0.025, 0.05
# Hall floor stroke scale: half-width of the luminance autocorrelation along x and y, px at 256 px/m (20 px = 8 cm), and the largest x:y ratio.
HALL_AC = 20
HALL_ANISO = 2.0
# Which rules a floor carries: the hall floor all of them (repainted on purpose), the others the luminance band and the saturation cap only
# (their mark contrast is printed as NOTE: tile joints and gravel are drawn detail, judged on the rendered sheets).
FLOORS = {'hall_floor': 'all', 'stone_paving': 'value', 'floor_tiles': 'value', 'garden_ground': 'value', 'bridge_deck': 'value'}


def measure(src):
    a = (np.asarray(Image.open(src).convert('RGB')).astype(float) if isinstance(src, str) else src[..., :3].astype(float)) / 255
    lin = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4); Y = lin @ [0.2126, 0.7152, 0.0722]
    L = (a @ [0.2126, 0.7152, 0.0722]) * 255; mx, mn = a.max(2), a.min(2)
    F = np.fft.fft2(L - L.mean()); ac = np.fft.ifft2(F * np.conj(F)).real; ac /= max(ac[0, 0], 1e-9)
    hx = next((i for i in range(1, 400) if ac[0, i] < 0.5), 400); hy = next((i for i in range(1, 400) if ac[i, 0] < 0.5), 400)
    eq = (np.abs(np.diff(L, axis=1)) < 6).mean(); eq4 = (np.abs(np.diff(L, axis=1)) < 4).mean()
    med = np.median(Y); dark = float(((med + 0.05) / (Y + 0.05) >= 1.5).mean()); light = float(((Y + 0.05) / (med + 0.05) >= 1.5).mean())
    return dict(dark=dark, light=light, Y=float(Y.mean()), lum=float(L.mean()), sd=float(L.std()), sat=float(((mx - mn) / np.maximum(mx, 1e-6)).mean()),
                marks=float((np.percentile(Y, 95) + 0.05) / (np.percentile(Y, 5) + 0.05)), acx=hx, acy=hy,
                run_cm=float((1 / (1 - eq) if eq < 1 else 1e9) / 2.56), run4_cm=float((1 / (1 - eq4) if eq4 < 1 else 1e9) / 2.56), blk=float(L.reshape(8, L.shape[0] // 8, 8, L.shape[1] // 8).mean((1, 3)).std()))


def rules(name, m, kind):
    r = [('floor luminance', FLOOR_Y[0] <= m['Y'] <= FLOOR_Y[1], f"texture relative luminance {m['Y']:.3f} ({FLOOR_Y[0]}-{FLOOR_Y[1]}); mean lum {m['lum']:.0f}")]
    if kind == 'all':
        r += [('own marks', m['marks'] <= MARKS, f"p95/p5 contrast {m['marks']:.2f}:1 (max {MARKS})"),
              ('contrast', HALL_SD[0] <= m['sd'] <= HALL_SD[1], f"lum sd {m['sd']:.1f} ({HALL_SD[0]}-{HALL_SD[1]})"),
              ('stroke scale', max(m['acx'], m['acy']) <= HALL_AC and max(m['acx'], m['acy']) / max(1, min(m['acx'], m['acy'])) <= HALL_ANISO,
               f"autocorrelation half-width {m['acx']} x {m['acy']} px (max {HALL_AC}, x:y max {HALL_ANISO})"),
              ('saturation', HALL_SAT[0] <= m['sat'] <= HALL_SAT[1], f"{m['sat']:.2f} ({HALL_SAT[0]}-{HALL_SAT[1]})"),
              ('outliers', m['dark'] <= HALL_DARK and m['light'] <= HALL_LIGHT, f"dark {m['dark']:.1%} (max {HALL_DARK:.1%}), light {m['light']:.1%} (max {HALL_LIGHT:.0%})")]
    else:
        r += [('saturation', m['sat'] <= SAT_CAP, f"{m['sat']:.2f} (cap {SAT_CAP})")]
    return r


if __name__ == '__main__':
    D = sys.argv[1]; extra = [a.split('=', 1) for a in sys.argv[2:] if '=' in a]; fails = checks = 0
    todo = [(n, f'{D}/{n}.png', k) for n, k in FLOORS.items()] + [(n + '_cand', p, FLOORS[n]) for n, p in extra]
    for n, p, k in todo:
        if not os.path.exists(p): checks += 1; fails += 1; print(f'FAIL {n} file: missing {p}'); continue
        m = measure(p)
        for rule, ok, val in rules(n, m, k):
            checks += 1; fails += 0 if ok else 1; print(f"{'PASS' if ok else 'FAIL'} {n} {rule}: {val}")
        if k != 'all': print(f"NOTE {n} own marks p95/p5 {m['marks']:.2f}:1, lum sd {m['sd']:.1f}, autocorrelation {m['acx']} x {m['acy']} px")
    print(f'{checks - fails} of {checks} pass')
    if '--mutate' in sys.argv:
        a = np.asarray(Image.open(f'{D}/hall_floor.png').convert('RGB')).astype(float); rng = np.random.default_rng(7)
        dark = a * 0.62                                                                   # back at the round 2 value
        noisy = np.clip(a + np.repeat(np.repeat(rng.normal(0, 16, (128, 128)), 8, 0), 8, 1)[..., None], 0, 255)   # busy 3 cm blotches
        streak = np.clip(a + np.repeat(rng.normal(0, 9, (1024 // 16, 1)), 16, 0).repeat(1024, 1)[..., None], 0, 255)   # long one-way grain
        caught = 0
        for label, img, rule in (('dark', dark, 'floor luminance'), ('noisy', noisy, 'own marks'), ('streak', streak, 'stroke scale')):
            hit = any(r == rule and not ok for r, ok, _ in rules('hall_floor', measure(img), 'all')); caught += hit
            print(('MUT caught ' if hit else 'MUT MISSED ') + f'hall_floor {label} -> {rule}')
        print(f'{caught} of 3 mutations caught')
