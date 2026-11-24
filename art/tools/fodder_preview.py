#!/usr/bin/env python3
"""Quick review sheets for the guard and rebel units from the builders' triangle dumps (OUT/preview/*.npz), drawn with the game camera
(FOV 50, pitch 40) and the game sun direction, flat lambert shading, painter's order. A self-check tool for iteration and the silhouette
gates; the review sheets for the owner come from the three.js viewer (art/viewer/fodder.html) on a runner.

Usage: python3 fodder_preview.py PREVIEWDIR OUTDIR UNITS [--schools]
  UNITS: comma list of dump tags in lineup order (e.g. zu,nu,dun,che,wz). Writes lineup_fight.png, lineup_wide.png, lineup_sil.png,
  <unit>_turn.png (yaw 0 / 35 / 90 / 180, rest), <unit>_tell.png (rest | windup), <unit>_lods.png, and prints the silhouette gates:
  pairwise IoU of the flat-black shapes at the wide view (feet aligned) must stay under IOU_MAX.
"""
import sys, os, math, itertools
import numpy as np
from PIL import Image, ImageDraw

D, OUT, UNITS = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
os.makedirs(OUT, exist_ok=True)
# CONFIG
# Pairwise IoU limit of two types' flat-black silhouettes (study gate 10).
IOU_MAX = 0.75
# Camera: FOV deg, pitch deg, distances m (fight framing 0.75 x CAM_DIST 14; wide review 22).
FOV, PITCH, FIGHT, WIDE = 50, 40, 10.5, 22
# Sun direction (design coords x, f, z) from the game's sun position (-30, 60, 25) in three.js (x, y, z) = design (x, z, f).
SUN = np.array([-30, 25, 60], float); SUN /= np.linalg.norm(SUN)
# Floor colour behind units (hall floor mean) and background.
FLOOR, BG = (107, 61, 48), (18, 13, 22)
# Preview colours per material/row (rows of bronze_trim.png and fodder_trim.png; patch = the school colour).
COL = {'gdBronze/plain': '#9a7a48', 'gdBronze/clouds': '#86683c', 'gdBronze/inlay': '#c8ccd0', 'gdBronze/lozenge': '#6e5532', 'gdBronze/flange': '#b2925e',
       'gdBronze/mask': '#86683c', 'gdBronze/mark': '#8a6c40', 'lacquer': '#221c18', 'cord': '#3a6e88', 'blue': '#3a6e88', 'yellow': '#c6a44c',
       'hemp': '#8f8068', 'patch': '#c4c2bc', 'plates': '#5a4632', 'rope': '#a08a5a', 'skin': '#b08a68', 'dark': '#2e2a22', 'metal': '#7e796c', 'rbGlint/glint': '#ffe066'}
SCHOOL = {'ru': 0xb05a2a, 'dao': 0xd5a03a, 'fa': 0x6a6a6a, 'mo': 0x8a2a3a, 'yinyang': 0x3a3a3a, 'za': 0xe8e8f0, 'ming': 0xc060a0, 'zongheng': 0x40c0c0, 'nong': 0x9a6ad5}

def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)

def colour_of(name, school=None):
    if name in COL: return hexc(COL[name])
    row = name.split('/')[-1]
    if row == 'patch' and school: c = SCHOOL[school]; return hexc('#%06x' % c) * 0.9 + 12
    if name.startswith('gdBronze'): return hexc('#9a7a48')
    return hexc(COL.get(row, '#808080'))

def load(tag):
    z = np.load(os.path.join(D, tag + '.npz'), allow_pickle=False)
    return z['tri'].astype(float), z['row'], [str(s) for s in z['rows']]

def cam_basis(yaw, pitch, dist, look):
    y, p = math.radians(yaw), math.radians(pitch)
    eye = look + dist * np.array([math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p)])
    fwd = look - eye; fwd /= np.linalg.norm(fwd); right = np.cross(fwd, [0, 0, 1.0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    return eye, fwd, right, up

def draw(img, items, yaw, pitch, dist, look, mode='shade', W=None, H=None):
    """items: list of (tri, rowid, rownames, offset xyz, school). mode shade | sil."""
    W, H = img.size; eye, fwd, right, up = cam_basis(yaw, pitch, dist, look); f = (H / 2) / math.tan(math.radians(FOV / 2))
    polys = []
    for tri, row, names, off, school in items:
        T = tri + off; rel = T - eye; zc = rel @ fwd; xs = rel @ right; ys = rel @ up
        n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0]); nl = np.linalg.norm(n, axis=1, keepdims=True); n = n / np.maximum(nl, 1e-12)
        cen = T.mean(1); facing = ((eye - cen) * n).sum(1)
        n = np.where(facing[:, None] < 0, -n, n)
        lam = np.clip(n @ SUN, 0, 1); hemi = 0.5 + 0.25 * n[:, 2]
        px = W / 2 + xs / zc * f; py = H / 2 - ys / zc * f; depth = zc.mean(1)
        cols = {}
        for i in range(len(T)):
            if mode == 'sil': c = (0, 0, 0)
            else:
                k = row[i]
                if k not in cols: cols[k] = colour_of(names[k], school)
                c = tuple(int(v) for v in np.clip(cols[k] * (hemi[i] + 0.8 * lam[i]), 0, 255))
            polys.append((depth[i], [(px[i, j], py[i, j]) for j in range(3)], c))
    polys.sort(key=lambda p: -p[0])
    d = ImageDraw.Draw(img)
    for _, pts, c in polys: d.polygon(pts, fill=c)
    return img

def floor(img, yaw, pitch, dist, look, half=12):
    if True:
        W, H = img.size; eye, fwd, right, up = cam_basis(yaw, pitch, dist, look); f = (H / 2) / math.tan(math.radians(FOV / 2))
        P = np.array([[-half, -half, 0], [half, -half, 0], [half, half, 0], [-half, half, 0]], float) + np.array([look[0], look[1], 0])
        rel = P - eye; zc = rel @ fwd
        pts = [(W / 2 + (rel[i] @ right) / zc[i] * f, H / 2 - (rel[i] @ up) / zc[i] * f) for i in range(4)]
        ImageDraw.Draw(img).polygon(pts, fill=FLOOR)
    return img

def unit_items(tag, pose='rest', school=None):
    tri, row, names = load(f'{tag}_{pose}')
    return (tri, row, names, np.zeros(3), school)

def tag_school(tag):
    for s in SCHOOL:
        if tag.endswith('_' + s): return s
    return None

# lineups: fight framing and wide, then flat black on white
SP = 2.4
xs = [-(i - (len(UNITS) - 1) / 2) * SP for i in range(len(UNITS))]  # first unit on the screen's left (camera in front: +x is screen left)
for name, dist, size in (('lineup_fight', FIGHT, (1920, 1080)), ('lineup_wide', WIDE, (1920, 1080))):
    img = Image.new('RGB', size, BG); look = np.array([0, 0, 0.9]); floor(img, 0, PITCH, dist, look)
    items = []
    for x, u in zip(xs, UNITS):
        tri, row, names, _, _ = unit_items(u); items.append((tri, row, names, np.array([x, 0, 0]), tag_school(u)))
    draw(img, items, 0, PITCH, dist, look).save(os.path.join(OUT, name + '.png'))
img = Image.new('RGB', (1920, 1080), (255, 255, 255)); items = []
for x, u in zip(xs, UNITS):
    tri, row, names, _, _ = unit_items(u); items.append((tri, row, names, np.array([x, 0, 0]), None))
draw(img, items, 35, PITCH, WIDE, np.array([0, 0, 0.9]), 'sil').save(os.path.join(OUT, 'lineup_sil.png'))

# per unit: turnaround, tell (rest | windup), LODs
for u in UNITS:
    sch = tag_school(u); base = u.split('_')[0]
    sheet = Image.new('RGB', (4 * 480, 520), BG)
    for i, yaw in enumerate((0, 35, 90, 180)):
        im = Image.new('RGB', (480, 520), BG); tri, row, names, _, _ = unit_items(u)
        draw(im, [(tri, row, names, np.zeros(3), sch)], yaw, 15, 4.6, np.array([0, 0, 1.0])); sheet.paste(im, (i * 480, 0))
    sheet.save(os.path.join(OUT, f'{u}_turn.png'))
    sheet = Image.new('RGB', (2 * 640, 600), BG)
    for i, pose in enumerate(('rest', 'windup')):
        im = Image.new('RGB', (640, 600), BG); floor(im, 35, PITCH, FIGHT * 0.55, np.array([0, 0.4, 0.9]), half=2.5)
        tri, row, names, _, _ = unit_items(u, pose); draw(im, [(tri, row, names, np.zeros(3), sch)], 35, PITCH, FIGHT * 0.55, np.array([0, 0.4, 0.9]))
        sheet.paste(im, (i * 640, 0))
    sheet.save(os.path.join(OUT, f'{u}_tell.png'))
    if os.path.exists(os.path.join(D, f'{base}_lod1.npz')) and base == u:
        sheet = Image.new('RGB', (3 * 480, 520), BG)
        for i, tag in enumerate((f'{u}_rest', f'{base}_lod1', f'{base}_lod2')):
            z = np.load(os.path.join(D, tag + '.npz')); im = Image.new('RGB', (480, 520), BG)
            draw(im, [(z['tri'].astype(float), z['row'], [str(s) for s in z['rows']], np.zeros(3), sch)], 35, 15, 4.6, np.array([0, 0, 1.0])); sheet.paste(im, (i * 480, 0))
        sheet.save(os.path.join(OUT, f'{u}_lods.png'))

# silhouette gate: each unit alone, flat black at the wide view (yaw 35), cropped to its box, feet centred, compared pairwise
def sil(u):
    im = Image.new('L', (900, 900), 255); tri, row, names, _, _ = unit_items(u)
    rgb = Image.new('RGB', im.size, (255, 255, 255)); draw(rgb, [(tri, row, names, np.zeros(3), None)], 35, PITCH, WIDE, np.array([0, 0, 0.9]), 'sil')
    a = np.asarray(rgb.convert('L')) < 128; ys, xs_ = np.nonzero(a)
    return a, (xs_.min(), xs_.max(), ys.min(), ys.max())
S = {u: sil(u) for u in UNITS}
Hh = max(b[3] - b[2] + 1 for _, b in S.values()); Ww = max(b[1] - b[0] + 1 for _, b in S.values()) * 2
def placed(u):
    a, (x0, x1, y0, y1) = S[u]; c = np.zeros((Hh, Ww), bool); h, w = y1 - y0 + 1, x1 - x0 + 1
    ox = Ww // 2 - w // 2; c[Hh - h:, ox:ox + w] = a[y0:y1 + 1, x0:x1 + 1]; return c
PL = {u: placed(u) for u in UNITS}
fails = 0; n = 0; worst = (0, None)
for a, b in itertools.combinations(UNITS, 2):
    i = (PL[a] & PL[b]).sum() / max(1, (PL[a] | PL[b]).sum()); n += 1
    ok = i < IOU_MAX; fails += not ok; worst = max(worst, (i, f'{a}/{b}'))
    if not ok: print(f'FAIL silhouette {a} vs {b} IoU {i:.2f} (max {IOU_MAX})')
print(f'{"PASS" if fails == 0 else "FAIL"} lineup silhouettes: {n - fails} of {n} pairs under IoU {IOU_MAX} (closest {worst[1]} {worst[0]:.2f})')
for u in UNITS:
    a, (x0, x1, y0, y1) = S[u]; print(f'INFO {u} wide-view size {x1 - x0 + 1} x {y1 - y0 + 1} px')
