#!/usr/bin/env python3
"""Checks for the C12 standard banner atlas (art/tools/standard_tex.py) and its play-size shots. PASS/FAIL per rule.
  tex ATLAS.png        : size 1024 RGBA; nine painted cells and an empty tenth; no paint in the cell margins (no bleed between schools);
                         alpha-tested cloth (solid inside, partial alpha only on the antialiased edge); three tongues per banner;
                         field colour = the school accent (dE <= 8); sigil contrast with the field (L* >= 30) and size; nine schools
                         distinct: field colour dE >= 10 and sigil silhouette IoU < 0.75 (max over +-8 px shifts) for all 36 pairs.
  crops SHOTDIR        : the lineup play shot (FOV 50, pitch 40, 10.5 m) and its banner corners (lineup.json from the viewer): each
                         banner is rectified from its projected quad back to cell shape at play resolution (round 1 compared the
                         sheared banner with the upright cell and so misaligned them); sigil box at least 24 px tall; the sigil
                         survives at play size (IoU with the painted sigil >= 0.75); rendered
                         field dE >= 10 and rendered sigil IoU < 0.75 for all 36 pairs; writes crops_<school>.png for the sheet.
  --mut dup|blend|flat|bleed|tongue (tex), dup|blur (crops)  breaks the input on purpose (must FAIL). --shot NAME: another lineup shot.
Usage: python3 standard_check.py tex ATLAS.png [--mut X] | python3 standard_check.py crops SHOTDIR ATLAS.png [--mut dup|blur] [--shot NAME]
"""
import itertools, json, os, sys
import numpy as np
from PIL import Image, ImageFilter

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Atlas layout (standard_tex.py): 5 x 2 cells, 6 px margin, heading band 30 px, tongues 78 px, sigil centre 0.40 of the cell, half 74 px.
GRID, MARGIN, HEAD_H, TONGUE_L, SIGIL_Y, SIGIL_HALF = (5, 2), 6, 30, 78, 0.40, 74
# Field accents per school (standard_tex.py SCHOOLS; za banner #b2bccb by owner decision 25 Nov 02:4x).
SCHOOLS = [('ru', '#b8862e'), ('dao', '#e2b84a'), ('fa', '#d9d2c3'), ('mo', '#a8321e'), ('yinyang', '#1a1614'), ('za', '#b2bccb'),
           ('ming', '#5b3f8c'), ('zongheng', '#2f8a5c'), ('nong', '#2e5a9c')]
# Limits: field vs accent dE, pairwise field dE, sigil L* contrast, sigil coverage of its box, IoU, partial-alpha share, play-size rules.
ACC_DE, PAIR_DE, SIG_CONTRAST, SIG_COVER, IOU_MAX, PARTIAL_MAX = 8, 10, 30, (0.08, 0.5), 0.75, 0.06
# Play-size rules: sigil box px; sigil IoU with the painted sigil after rectifying (round 2: raised 0.45 -> 0.75 once the banners were
# registered; a 3 px blur of the shot must fail it).
PLAY_SIG_PX, PLAY_FIDELITY = 24, 0.75

MUT = sys.argv[sys.argv.index('--mut') + 1] if '--mut' in sys.argv else ''
SHOT = sys.argv[sys.argv.index('--shot') + 1] if '--shot' in sys.argv else 'lineup'
fails = n = 0
def rule(ok, line):
    global fails, n
    n += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + line)

def lab(rgb):
    c = np.asarray(rgb, float) / 255; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    M = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    x = c @ M.T / np.array([0.95047, 1, 1.08883]); f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
def hexlab(h): return lab([int(h[i:i + 2], 16) for i in (1, 3, 5)])

def iou_shift(a, b, sh, step):
    best = 0.0
    for dy in range(-sh, sh + 1, step):
        for dx in range(-sh, sh + 1, step):
            bb = np.roll(np.roll(b, dy, 0), dx, 1); u = (a | bb).sum(); best = max(best, (a & bb).sum() / u if u else 0)
    return best

def rectify(img, quad, w, h):
    """the banner's projected quad (tl, tr, bl, br on screen) resampled (nearest) to an upright w x h cell-shaped image."""
    src = [(0, 0), (w, 0), (0, h), (w, h)]; A = []; b = []
    for (u, v), (x, y) in zip(src, quad):
        A.append([u, v, 1, 0, 0, 0, -u * x, -v * x]); b.append(x); A.append([0, 0, 0, u, v, 1, -u * y, -v * y]); b.append(y)
    co = np.linalg.solve(np.array(A, float), np.array(b, float))
    return np.asarray(img.transform((w, h), Image.PERSPECTIVE, tuple(co), Image.NEAREST))


def cell_geom(i, W=1024, H=1024):
    cw, ch = W / GRID[0], H / GRID[1]; return (i % GRID[0]) * cw, (i // GRID[0]) * ch, cw, ch

def analyse(rgba, cw, ch, k=1.0):
    """one banner (cell-sized RGBA array, k = scale vs the 1024 atlas): field Lab, sigil mask (in its box), sigil L*, field zone mask."""
    al = rgba[..., 3] / 255.0; L = lab(rgba[..., :3])
    hem = 9 * k + 4
    fz = np.zeros(al.shape, bool); fz[int(ch * 0.62):int(ch - (TONGUE_L + 20) * k), int(MARGIN * k + hem):int(cw - MARGIN * k - hem)] = True
    fz &= al > 0.9
    field = np.median(L[fz], 0) if fz.any() else np.array([0, 0, 0.0])
    cy = ch * SIGIL_Y; hh = (SIGIL_HALF + 10) * k; cx = cw / 2
    y0, y1, x0, x1 = int(cy - hh), int(cy + hh), int(cx - hh), int(cx + hh)
    box = L[y0:y1, x0:x1, 0]; ab = al[y0:y1, x0:x1] > 0.5
    far = np.abs(box - field[0]); sig = ab & (far > 15)
    sl = float(np.median(box[sig])) if sig.any() else field[0]
    mask = ab & (np.abs(box - field[0]) > 0.5 * abs(sl - field[0]))
    return field, mask, sl, fz

if sys.argv[1] == 'tex':
    im = Image.open(sys.argv[2]); rule(im.size == (1024, 1024) and im.mode == 'RGBA', f'atlas size {im.size} {im.mode} (1024 RGBA, max 1024)')
    a = np.asarray(im.convert('RGBA')).copy()
    if MUT == 'dup':
        x, y, cw, ch = cell_geom(0); x2, y2, _, _ = cell_geom(1); w = int(cw) - 1
        a[int(round(y2)):int(round(y2)) + int(ch), int(round(x2)):int(round(x2)) + w] = a[int(round(y)):int(round(y)) + int(ch), int(round(x)):int(round(x)) + w]
    if MUT == 'blend': x, y, cw, ch = cell_geom(2); a[int(y):int(y + ch), int(x):int(x + cw), 3] = (a[int(y):int(y + ch), int(x):int(x + cw), 3] * 0.6).astype(np.uint8)
    if MUT == 'flat': x, y, cw, ch = cell_geom(3); a[int(y + ch * 0.2):int(y + ch * 0.6), int(x + 20):int(x + cw - 20), :3] = [int(SCHOOLS[3][1][k:k + 2], 16) for k in (1, 3, 5)]
    if MUT == 'bleed': x, y, cw, ch = cell_geom(4); a[int(y + 100):int(y + 300), int(x):int(x + 3), 3] = 255
    if MUT == 'tongue': x, y, cw, ch = cell_geom(5); a[int(y + ch - 60):int(y + ch - 30), int(x + 10):int(x + cw - 10)] = a[int(y + ch - 120), int(x + cw / 2)]
    fields, masks = [], []
    for i in range(10):
        x, y, cw, ch = cell_geom(i); c = a[int(round(y)):int(round(y + ch)), int(round(x)):int(round(x + cw))]; al = c[..., 3] / 255.0
        if i == 9: rule(al.max() < 0.05, f'cell 9 empty (alpha max {al.max():.2f})'); continue
        nm, acc = SCHOOLS[i]
        m = MARGIN - 2; edge = np.concatenate([al[:m].ravel(), al[-m:].ravel(), al[:, :m].ravel(), al[:, -m:].ravel()])
        cov = (al > 0.5).mean()
        rule(edge.max() < 0.1 and 0.7 <= cov <= 0.97, f'{nm} cell: margin alpha max {edge.max():.2f} (< 0.1, no bleed), cloth covers {cov:.0%} (70-97%)')
        vis = al > 0.02; part = ((al > 0.02) & (al < 0.98)).sum() / max(1, vis.sum())
        inner = al[int(MARGIN + 8):int(ch - MARGIN - TONGUE_L - 8), int(MARGIN + 8):int(cw - MARGIN - 8)]
        rule(part < PARTIAL_MAX and inner.min() >= 0.98, f'{nm} alpha-tested cloth: partial alpha {part:.1%} of painted px (< {PARTIAL_MAX:.0%}), body alpha min {inner.min():.2f} (>= 0.98)')
        row = al[int(ch - MARGIN - 40)] > 0.5; runs = int(np.sum(row[1:] & ~row[:-1]) + row[0])
        rule(runs == 3, f'{nm} tongues: {runs} (3)')
        field, mask, sl, fz = analyse(c, cw, ch)
        de = float(np.linalg.norm(field - hexlab(acc)))
        rule(de <= ACC_DE, f'{nm} field = accent {acc}: dE {de:.1f} (<= {ACC_DE})')
        cov_s = mask.mean(); con = abs(sl - field[0])
        rule(con >= SIG_CONTRAST and SIG_COVER[0] <= cov_s <= SIG_COVER[1], f'{nm} sigil contrast L* {con:.0f} (>= {SIG_CONTRAST}), covers {cov_s:.0%} of its box ({SIG_COVER[0]:.0%}-{SIG_COVER[1]:.0%})')
        fields.append(field); masks.append(mask)
    worst_de = min((float(np.linalg.norm(fields[i] - fields[j])), SCHOOLS[i][0], SCHOOLS[j][0]) for i, j in itertools.combinations(range(9), 2))
    nde = sum(float(np.linalg.norm(fields[i] - fields[j])) >= PAIR_DE for i, j in itertools.combinations(range(9), 2))
    rule(nde == 36, f'field colours distinct: {nde} of 36 pairs dE >= {PAIR_DE} (closest {worst_de[1]}-{worst_de[2]} {worst_de[0]:.1f})')
    ious = sorted(((iou_shift(masks[i], masks[j], 8, 2), SCHOOLS[i][0], SCHOOLS[j][0]) for i, j in itertools.combinations(range(9), 2)), reverse=True)
    nio = sum(v < IOU_MAX for v, _, _ in ious)
    rule(nio == 36, f'sigil silhouettes distinct: {nio} of 36 pairs IoU < {IOU_MAX} (max {ious[0][1]}-{ious[0][2]} {ious[0][0]:.2f}, next {ious[1][1]}-{ious[1][2]} {ious[1][0]:.2f})')
else:
    D = sys.argv[2]; atlas = np.asarray(Image.open(sys.argv[3]).convert('RGBA'))
    shot = np.asarray(Image.open(os.path.join(D, SHOT + '.png')).convert('RGBA')).copy(); dump = json.load(open(os.path.join(D, SHOT + '.json')))
    boxes, quads = dump['boxes'], dump['quads']
    if MUT == 'dup':
        b0, b1 = boxes[0], boxes[1]; w, h = int(b0[2] - b0[0]), int(b0[3] - b0[1])
        shot[int(b1[1]):int(b1[1]) + h, int(b1[0]):int(b1[0]) + w] = shot[int(b0[1]):int(b0[1]) + h, int(b0[0]):int(b0[0]) + w]
    if MUT == 'blur': shot = np.asarray(Image.fromarray(shot).filter(ImageFilter.GaussianBlur(3))).copy()
    shot_im = Image.fromarray(shot); pre = '' if SHOT == 'lineup' else SHOT + '_'
    fields, masks = [], []
    for i, (nm, acc) in enumerate(SCHOOLS):
        x0, y0, x1, y1 = [int(round(v)) for v in boxes[i]]
        Image.fromarray(shot[y0:y1, x0:x1]).save(os.path.join(D, f'{pre}crop_{nm}.png'))
        q = quads[i]; ch = int(round(np.hypot((q[2][0] + q[3][0] - q[0][0] - q[1][0]) / 2, (q[2][1] + q[3][1] - q[0][1] - q[1][1]) / 2)))
        x, y, acw, ach = cell_geom(i); cw = int(round(ch * acw / ach))
        crop = rectify(shot_im, q, cw, ch); Image.fromarray(crop).save(os.path.join(D, f'{pre}rect_{nm}.png'))
        cell = atlas[int(round(y)):int(round(y + ach)), int(round(x)):int(round(x + acw))]
        ref = np.asarray(Image.fromarray(cell).resize((cw, ch), Image.NEAREST))
        k = ch / ach
        rf, rmask, rsl, fz = analyse(ref, cw, ch, k)
        rgba = crop.copy(); rgba[..., 3] = ref[..., 3]  # the shot is opaque: the painted alpha marks where the cloth is
        field, mask, sl, _ = analyse(rgba, cw, ch, k)
        sig_px = mask.shape[0]
        fid = (mask & rmask).sum() / max(1, (mask | rmask).sum())
        rule(sig_px >= PLAY_SIG_PX and fid >= PLAY_FIDELITY, f'play {nm}: sigil box {sig_px} px tall (>= {PLAY_SIG_PX}), sigil vs painted IoU {fid:.2f} (>= {PLAY_FIDELITY}), contrast L* {abs(sl - field[0]):.0f}')
        fields.append(field); masks.append(np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).resize((40, 40), Image.NEAREST)) > 127)
    worst = min((float(np.linalg.norm(fields[i] - fields[j])), SCHOOLS[i][0], SCHOOLS[j][0]) for i, j in itertools.combinations(range(9), 2))
    nde = sum(float(np.linalg.norm(fields[i] - fields[j])) >= PAIR_DE for i, j in itertools.combinations(range(9), 2))
    ifa, iza = [k_ for k_, (nm_, _) in enumerate(SCHOOLS) if nm_ in ('fa', 'za')]
    print(f'INFO {SHOT} fa-za field dE {float(np.linalg.norm(fields[ifa] - fields[iza])):.1f} in play')
    rule(nde == 36, f'play field colours distinct: {nde} of 36 pairs dE >= {PAIR_DE} (closest {worst[1]}-{worst[2]} {worst[0]:.1f})')
    ious = sorted(((iou_shift(masks[i], masks[j], 2, 1), SCHOOLS[i][0], SCHOOLS[j][0]) for i, j in itertools.combinations(range(9), 2)), reverse=True)
    nio = sum(v < IOU_MAX for v, _, _ in ious)
    rule(nio == 36, f'play sigils distinct: {nio} of 36 pairs IoU < {IOU_MAX} (max {ious[0][1]}-{ious[0][2]} {ious[0][0]:.2f})')
print(f'{n - fails} of {n} pass')
