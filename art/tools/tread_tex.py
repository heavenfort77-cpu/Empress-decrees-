#!/usr/bin/env python3
"""Tread belt strip (FIX-A, 25 Nov): assets/tex/tread_belt.png for the scrolling treads of the guard and the apex cubs (tread_kit.py).
One repeat = 0.5 m of belt along U (128 px = 256 px/m, the trim-sheet density), four cast links per repeat; V across the belt:
rows 0-12 side edge (link pins), 12-52 link face (cast plate with a raised cleat), 52-64 the other side edge. Colours from the brass
sheet (owner: brass for every bronze piece) and the dark lacquer of fodder_trim.png in the gaps, so links read apart while scrolling.
Usage: python3 tread_tex.py OUT.png        (writes, then checks)      python3 tread_tex.py --check PNG [--mutate]
Checks: size; seamless in U (wrap step no bigger than the largest step inside the strip); four links per repeat (dark gaps by column
luminance); gaps darker than plates by at least GAP_DL; plate mean within PLATE_TOL of the brass sheet flange row."""
import sys
import numpy as np
from PIL import Image

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Strip size, px (U along the belt, V across).
W, H = 128, 64
# Links per repeat and the plate share of a link (the rest is the dark gap).
LINKS, FILL = 4, 0.66
# Rows of the side edges, px from the top and bottom (tread_kit.V_SIDE = 12 / 64).
SIDE = 12
# Brass plate (brass sheet flange row mean, measured 169 140 78), cleat highlight, shadow, gap (fodder_trim dark row 58 53 42, darker).
PLATE, CLEAT, SHADE, GAP = (169, 140, 78), (196, 166, 98), (118, 95, 52), (34, 30, 24)
# Check limits: gap vs plate luminance difference, plate colour distance to PLATE.
GAP_DL, PLATE_TOL = 60, 18


def make():
    rng = np.random.default_rng(5); im = np.zeros((H, W, 3), float); L = W // LINKS; P = int(round(L * FILL))
    for x in range(W):
        k = x % L
        for y in range(H):
            if k >= P: c = GAP
            else:
                edge = y < SIDE or y >= H - SIDE
                c = SHADE if (k == 0 or k == P - 1) else PLATE
                if edge: c = tuple(v * 0.82 for v in c)
                if not edge and abs(k - P // 2) <= 2: c = CLEAT if abs(k - P // 2) <= 1 else PLATE
                if edge and abs(k - P // 2) <= 3 and abs((y if y < SIDE else H - 1 - y) - SIDE // 2) <= 3: c = CLEAT  # link pin boss
            im[y, x] = c
    # cast grain: low noise, the same in every link column offset so the strip stays periodic per link
    n = rng.normal(0, 4, (H, L, 1)); im += np.tile(n, (1, LINKS, 3))
    return Image.fromarray(np.clip(im, 0, 255).astype(np.uint8))


def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def check(img):
    a = np.asarray(img.convert('RGB')).astype(float); rows = []
    rows.append((a.shape[:2] == (H, W), f'size {a.shape[1]}x{a.shape[0]} (want {W}x{H}; 0.5 m per repeat at 256 px/m)'))
    steps = np.abs(np.diff(a, axis=1)).mean(axis=(0, 2)); wrap = np.abs(a[:, 0] - a[:, -1]).mean()
    rows.append((wrap <= steps.max() + 1e-6, f'seamless in U: wrap step {wrap:.1f} (largest inner step {steps.max():.1f})'))
    face = lum(a[SIDE:H - SIDE]).mean(axis=0); dark = face < face.mean() - 30
    runs = int(np.sum(dark & ~np.roll(dark, 1)))
    rows.append((runs == LINKS, f'links per repeat {runs} (want {LINKS}; dark gap columns)'))
    dl = face[~dark].mean() - face[dark].mean() if dark.any() else 0
    rows.append((dl >= GAP_DL, f'gap darker than plate by {dl:.0f} luminance (min {GAP_DL})'))
    pm = a[SIDE:H - SIDE][:, ~dark].reshape(-1, 3).mean(0); d = float(np.linalg.norm(pm - np.array(PLATE)))
    rows.append((d <= PLATE_TOL, f'plate colour {pm.round().astype(int).tolist()} within {PLATE_TOL} of the brass flange {list(PLATE)} ({d:.1f})'))
    return rows


def report(rows, label):
    for ok, line in rows: print(('PASS ' if ok else 'FAIL ') + line)
    print(f'{label}: {sum(ok for ok, _ in rows)} of {len(rows)} pass'); return all(ok for ok, _ in rows)


if __name__ == '__main__':
    if sys.argv[1] == '--check':
        img = Image.open(sys.argv[2]); ok = report(check(img), 'tread_belt')
        if '--mutate' in sys.argv:  # each mutation must turn at least one check to FAIL
            a = np.asarray(img.convert('RGB')).copy(); muts = []
            b = np.roll(a, 5, axis=1); b[:, :5] = a[:, :5]; muts.append(('seam (columns 0-4 not shifted)', b))
            b = a.copy(); b[:, :] = np.maximum(b, 120); muts.append(('gaps lifted', b))
            b = a.copy(); b[..., 2] = 200; muts.append(('blue plate', b))
            b = np.concatenate([a, a[:, :32]], axis=1); muts.append(('five links', b))
            caught = 0
            for name, m in muts:
                bad = [l for good, l in check(Image.fromarray(m)) if not good]; caught += bool(bad)
                print(('PASS ' if bad else 'FAIL ') + f'mutation {name} caught: {bad[0] if bad else "-"}')
            print(f'tread_belt mutations: {caught} of {len(muts)} caught')
    else:
        img = make(); img.save(sys.argv[1]); print('wrote', sys.argv[1]); report(check(img), 'tread_belt')
