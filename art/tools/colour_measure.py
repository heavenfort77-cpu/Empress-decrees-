#!/usr/bin/env python3
"""COLOUR measures and sheets (art/Colour-Clarity-Study.md) on the shots of colour_shoot.mjs.
Per figure and shot: share of outline pixels (the 2 px border of the figure's ID mask, outline hull included) whose contrast against the
floor right behind them (floor pixels within about 10 px, shadows included) is >= 3:1 (WCAG relative luminance), the same share against the
ring median (the suit_contrast.py formula), the body median contrast against the floor ring, and the share of school-coloured pixels.
Per shot: the floor's on-screen luminance and its own p95/p5 contrast in the figure-free lower band.
Gates (PASS/FAIL): the proposal (variant new_a) at both distances, per figure (outline rule; body median >= 2.5:1; school colour share for the
nine suits); the floor on-screen rules per floor.
Control (the measure's mutation): the old floor with the game's current dark outline must fail the outline rule, else MUT MISSED.
Usage: python3 colour_measure.py SHOTDIR SHEETDIR"""
import json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
# CONFIG
# Contrast ratio an outline pixel must reach against the floor behind it.
RATIO = 3.0
# Share of a figure's outline pixels that must reach RATIO.
EDGE_SHARE = 0.5
# On-screen floor luminance band (study: black body >= 2.5:1 needs >= 0.125; pale rim >= 3:1 with margin needs <= 0.20).
FLOOR_Y = (0.125, 0.20)
# Largest contrast between the floor's own light and dark marks on screen (p95 against p5).
FLOOR_MARKS = 1.30
# Variant that is the proposal (gated); the control that must fail.
PROPOSAL, CONTROL = 'new_a', 'old_cur'
# The even floor's variant and the median body contrast the new floor must keep (lead 25 Nov: not below the even floor, body >= 3.0:1).
EVEN, BODY_MED = 'even_a', 3.0
# Body median contrast against the floor each figure must reach on the hall floor (FINAL, lead 25 Nov).
BODY = 2.5
# Share of a suit's pixels that must be in its school colour at play size (round 2, lead 25 Nov).
SCHOOL_SHARE = 0.08
# School colour per suit: a hue (degrees, +- HUE_TOL, chroma >= 0.12, luminance >= 0.03), or 'pale' (lead white / silver: HSV saturation <= 0.40
# and luminance >= 0.18; FINAL, set once: round 2's chroma <= 0.16 rejected lead white lit by the game's warm sun, where a white card shows a
# saturation of 0.23 flat and about 0.37 on a sunlit upright face), or 'black' (阴阳 bone black: luminance <= 0.035; always met by a black suit, printed for completeness).
SCHOOLS = {'fa': 'pale', 'ru': 34, 'dao': 44, 'mo': 10, 'yy': 'black', 'za': 'pale', 'ming': 260, 'zh': 150, 'nong': 216}
HUE_TOL = 28
S, OUT = sys.argv[1], sys.argv[2]
man = json.load(open(f'{S}/manifest.json')); IDS = man['ids']
def load(n): return np.asarray(Image.open(f'{S}/{n}.png').convert('RGB')).astype(float) / 255
def relY(img): lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4); return lin @ [0.2126, 0.7152, 0.0722]
def cr(a, b): return (np.maximum(a, b) + 0.05) / (np.minimum(a, b) + 0.05)
idc = {}
def idmask(n):
    if n not in idc: idc[n] = np.rint(load(n)[..., 0] * 255 / 20).astype(int)
    return idc[n]
fails = 0; rows = {}; floorrows = {}
for sh in man['shots']:
    img = load(sh['shot']); Y = relY(img); lab = idmask(sh['id']); fig = lab > 0
    notfig = ~ndimage.binary_dilation(fig, iterations=2) & (Y > 0.012)
    w = ndimage.gaussian_filter(notfig.astype(float), 5); loc = ndimage.gaussian_filter(np.where(notfig, Y, 0.0), 5) / np.maximum(w, 1e-6)
    band = np.zeros_like(fig); band[int(Y.shape[0] * 0.78):int(Y.shape[0] * 0.97)] = True; fb = band & ~ndimage.binary_dilation(fig, iterations=12) & (Y > 0.012)
    fy = float(np.median(Y[fb])); marks = float((np.percentile(Y[fb], 95) + 0.05) / (np.percentile(Y[fb], 5) + 0.05))
    mx, mn = img.max(2), img.min(2); ch = mx - mn; dd = np.maximum(ch, 1e-6); R_, G_, B_ = img[..., 0], img[..., 1], img[..., 2]
    hue = np.where(mx == R_, 60 * (((G_ - B_) / dd) % 6), np.where(mx == G_, 60 * ((B_ - R_) / dd + 2), 60 * ((R_ - G_) / dd + 4)))
    def school(m, sid):
        k = SCHOOLS.get(sid)
        if k is None: return None
        if k == 'pale': return float((((ch / np.maximum(mx, 1e-6))[m] <= 0.40) & (Y[m] >= 0.18)).mean())
        if k == 'black': return float((Y[m] <= 0.035).mean())
        dh = np.abs((hue[m] - k + 180) % 360 - 180); return float(((dh <= HUE_TOL) & (ch[m] >= 0.12) & (Y[m] >= 0.03)).mean())
    floorrows[sh['shot']] = (fy, marks, float(((mx - mn) / np.maximum(mx, 1e-6))[fb].mean()))
    res = []
    for i, sid in enumerate(IDS):
        m = lab == i + 1
        if m.sum() < 200: res.append((sid, None)); continue
        ring = ndimage.binary_dilation(m, iterations=8) & notfig
        fl = float(np.median(Y[ring])) if ring.any() else fy
        edge = m & ~ndimage.binary_erosion(m, iterations=2)
        lf = np.where(w[edge] > 0.02, loc[edge], fl)
        share = float((cr(Y[edge], lf) >= RATIO).mean()); legacy = float((cr(Y[edge], fl) >= RATIO).mean())
        body = float(cr(np.median(Y[m]), fl)); area = float((cr(Y[m], fl) >= RATIO).mean())
        col = school(ndimage.binary_erosion(m, iterations=3), sid)   # the rim is not counted as school colour
        res.append((sid, dict(share=share, legacy=legacy, body=body, area=area, col=col, px=int(m.sum()))))
    rows[sh['shot']] = res
    tag = f"{sh['variant']} {sh['kind']} {sh['dist']} m"
    gate = sh['variant'] == PROPOSAL
    for sid, d in res:
        if d is None:
            if gate: fails += 1; print(f'FAIL {tag} {sid}: figure not found in the ID mask')
            continue
        ok = d['share'] >= EDGE_SHARE
        head = ('PASS' if ok else 'FAIL') if gate else ('CONTROL' if sh['variant'] == CONTROL else 'OPTION')
        if gate and not ok: fails += 1
        print(f"{head} {tag} {sid} outline >= {RATIO}:1 vs floor behind: {d['share']:.0%} (min {EDGE_SHARE:.0%}); ring formula {d['legacy']:.0%}; body median {d['body']:.2f}:1; area >= 3:1 {d['area']:.0%}" + (f"; school colour px {d['col']:.0%}" if d['col'] is not None else ''))
        if gate and sh['kind'] == 'hall':
            okb = d['body'] >= BODY; fails += 0 if okb else 1
            print(f"{'PASS' if okb else 'FAIL'} {tag} {sid} body median vs floor: {d['body']:.2f}:1 (min {BODY}:1)")
        if gate and sh['kind'] == 'hall' and d['col'] is not None:
            oks = d['col'] >= SCHOOL_SHARE; fails += 0 if oks else 1
            print(f"{'PASS' if oks else 'FAIL'} {tag} {sid} school colour: {d['col']:.0%} of the figure's pixels (min {SCHOOL_SHARE:.0%})")
    if sh['variant'] == CONTROL:
        nf = sum(1 for _, d in res if d and d['share'] < EDGE_SHARE)
        ok = nf >= 6   # the owner's screenshot case: most figures must fail on the old floor with the dark outline
        if not ok: fails += 1
        print(f"{'MUT caught' if ok else 'MUT MISSED'} {tag}: {nf} of {len(res)} figures fail the outline rule on the old floor with the dark outline (control, min 6)")
    if gate or sh['variant'] == CONTROL:
        isnew = gate
        oky = FLOOR_Y[0] <= fy <= FLOOR_Y[1]; okm = marks <= FLOOR_MARKS
        if isnew and not oky: fails += 1
        if isnew and not okm: fails += 1
        h = (lambda ok: 'PASS' if ok else 'FAIL') if isnew else (lambda ok: 'CONTROL')
        print(f"{h(oky)} {tag} floor on-screen luminance {fy:.3f} ({FLOOR_Y[0]}-{FLOOR_Y[1]})")
        print(f"{h(okm)} {tag} floor own marks p95/p5 contrast {marks:.2f}:1 (max {FLOOR_MARKS}); on-screen saturation {floorrows[sh['shot']][2]:.2f}")
def summ(shot):
    r = [d for _, d in rows[shot] if d]
    return (min(d['share'] for d in r), float(np.mean([d['share'] for d in r])), float(np.median([d['body'] for d in r])), sum(d['share'] >= EDGE_SHARE for d in r), len(r),
            min(d['col'] for d in r if d['col'] is not None))
print('TABLE variant | dist | figures >= 50% | min outline share | mean outline share | median body contrast | floor Y | floor marks | min school colour px')
for sh in man['shots']:
    a = summ(sh['shot']); f = floorrows[sh['shot']]
    print(f"TABLE {sh['variant']} {sh['kind']} | {sh['dist']} | {a[3]} of {a[4]} | {a[0]:.0%} | {a[1]:.0%} | {a[2]:.2f}:1 | {f[0]:.3f} | {f[1]:.2f}:1 | {a[5]:.0%}")
# floor-only round (lead 25 Nov): the new floor must not read worse than the even floor (variant even_a) with the same characters
for d_ in (10.5, 14):
    e = [s_ for s_ in man['shots'] if s_['variant'] == EVEN and s_['dist'] == d_]; n_ = [s_ for s_ in man['shots'] if s_['variant'] == PROPOSAL and s_['kind'] == 'hall' and s_['dist'] == d_]
    if e and n_:
        ae, an = summ(e[0]['shot']), summ(n_[0]['shot']); ok = an[3] >= ae[3] and an[2] >= BODY_MED
        fails += 0 if ok else 1
        print(f"{'PASS' if ok else 'FAIL'} new floor vs even floor at {d_} m: figures passing the outline rule {an[3]} (even floor {ae[3]}), median body {an[2]:.2f}:1 (even floor {ae[2]:.2f}:1, min {BODY_MED}:1)")
# sheets (JPEG): same scale, same camera, stacked
def bandcrop(shot, idn, pad=40):
    lab = idmask(idn); ys = np.where((lab > 0).any(1))[0]; y0, y1 = max(0, ys[0] - pad), min(lab.shape[0], ys[-1] + pad + 60)
    return Image.open(f'{S}/{shot}.png').convert('RGB').crop((0, y0, lab.shape[1], y1))
def stack(items, path):
    ims = [(t, im) for t, im in items]; Wd = max(im.width for _, im in ims); Ht = sum(im.height + 26 for _, im in ims)
    sheet = Image.new('RGB', (Wd, Ht), (255, 255, 255)); d = ImageDraw.Draw(sheet); y = 0
    for t, im in ims: d.text((6, y + 6), t, fill=(0, 0, 0)); sheet.paste(im, (0, y + 26)); y += im.height + 26
    sheet.save(path, quality=88)
def label(sh):
    a = summ(sh['shot']); f = floorrows[sh['shot']]
    return f"{sh['variant']} ({sh['kind']}) at {sh['dist']} m: {a[3]} of {a[4]} figures pass, min outline share {a[0]:.0%}, median body {a[2]:.2f}:1, floor Y {f[0]:.3f}, marks {f[1]:.2f}:1, min school colour {a[5]:.0%}"
by = {(s['variant'], s['kind'], s['dist']): s for s in man['shots']}
for d in (10.5, 14):
    stack([(label(by[(v, 'hall', d)]), bandcrop(by[(v, 'hall', d)]['shot'], by[(v, 'hall', d)]['id'])) for v in (CONTROL, PROPOSAL)], f'{OUT}/sheet_play{d}_old_vs_new.jpg')
    stack([(label(s), bandcrop(s['shot'], s['id'])) for s in man['shots'] if s['kind'] == 'hall' and s['dist'] == d], f'{OUT}/sheet_play{d}_all_variants.jpg')
if any(s['kind'] != 'hall' for s in man['shots']): stack([(label(s), bandcrop(s['shot'], s['id'])) for s in man['shots'] if s['kind'] != 'hall'], f'{OUT}/sheet_play10.5_other_floors.jpg')
for tag, nm in (('hall mock, 14 m, pitch 40', 'hall'), ('hall mock, low camera (pitch 14, 12 m)', 'hall_low')):
    stack([(f'{tag}: {v}', Image.open(f'{S}/{nm}_{v}.png').convert('RGB')) for v in (CONTROL, PROPOSAL)], f'{OUT}/sheet_{nm}_old_vs_new.jpg')
for i in range(len(man['groups'])):
    stack([(f'close-up, {v}: ' + ' '.join(man['groups'][i]), Image.open(f'{S}/close_{v}_{i}.png').convert('RGB').crop((0, 120, 1920, 1000))) for v in (CONTROL, PROPOSAL)], f'{OUT}/sheet_close_old_vs_new_{i}.jpg')
print(f'FAIL lines: {fails}' if fails else 'all colour gates pass')
