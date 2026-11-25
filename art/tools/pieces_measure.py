#!/usr/bin/env python3
"""Play-size measures for the PIECES round, from pieces_shoot.mjs shots (same camera for the lit shot and its masks), judged on the
lighter floor candidate (branch ci-art-colour, copy at art/pieces/floor_candidate.png). Round 4 (lead):
  characters       crab and wanderer, drawn WITH the game's renderer outline (simulated in the viewer by the game's own shader, 2 px):
                   the share of outline pixels whose contrast (WCAG relative luminance) against what is beside them is >= 3:1 must be
                   >= 50% (the rule of art/tools/suit_contrast.py). The same share without the outline is printed as INFO.
  static props     plate, leader crown, 墨 wall, decree mark: NO outline. They must read by their own values like the 鼎 in the same shot:
                   bright part (85th percentile of the body) and dark part (15th percentile) against the floor beside it; the stronger
                   of the two must reach at least READ_K x the 鼎's. Their outline share is printed as INFO only.
  brass            mean colour of the brass pixels (material mask) of the crab, wanderer and plate, and of the crown's gold, beside
                   the 鼎's brass in the same shot: relative luminance within BRASS_BAND of the 鼎's.
  kaymuse          on the throne (play and approach framings), no outline: outline share >= 50% at 3:1 against the throne behind her.
  silhouettes      crab against wanderer at the game camera, front and side: IoU at the same scale and scaled to one height, <= 0.6.
--mutate: one mutation per gate (MUT caught / MUT MISSED). Usage: python3 pieces_measure.py SHOTDIR [--mutate]"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

# CONFIG
# Contrast the outline must reach against what is beside it, and the share of outline pixels that must reach it.
RATIO, EDGE_SHARE = 3.0, 0.5
# Fewest mask pixels for a piece to count as visible at play size (1920 x 1080).
AREA_MIN = 150
# Most silhouette overlap allowed between the crab and the wanderer.
IOU_MAX = 0.6
# A static prop reads like the 鼎 when its stronger part-against-floor ratio is at least this share of the 鼎's (worker's threshold, not the lead's).
READ_K = 0.9
# Brass renders like the 鼎's when its mean relative luminance is within this band of the 鼎's brass (x lower, x upper).
BRASS_BAND = (0.75, 1.33)
S = sys.argv[1]
CHARS, PROPS = ['crab', 'wanderer'], ['plate', 'leader_crown', 'mo_wall', 'decree_mark']

def load(name):
    img = np.asarray(Image.open(f'{S}/{name}.png').convert('RGB')).astype(float) / 255
    lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4); return img, lin @ [0.2126, 0.7152, 0.0722]

def mask(name): return np.asarray(Image.open(f'{S}/{name}.png').convert('L')) > 128

def sil(name): return np.asarray(Image.open(f'{S}/{name}.png').convert('L')) < 128

def ring_of(m): return ndimage.binary_dilation(m, iterations=10) & ~ndimage.binary_dilation(m, iterations=2)

def contrast(Y, m):
    """-> (ok, outline share, body median ratio, area px, height px)"""
    area = int(m.sum())
    if area < AREA_MIN: return False, 0.0, 0.0, area, 0
    edge = m & ~ndimage.binary_erosion(m, iterations=2); fl = np.median(Y[ring_of(m)]); ys = np.median(Y[m])
    er = (np.maximum(Y[edge], fl) + 0.05) / (np.minimum(Y[edge], fl) + 0.05); share = float((er >= RATIO).mean())
    rows = np.where(m.any(1))[0]
    return share >= EDGE_SHARE, share, float((max(ys, fl) + 0.05) / (min(ys, fl) + 0.05)), area, int(rows[-1] - rows[0] + 1)

def reads(Y, m):
    """-> (bright part ratio, dark part ratio, body median ratio, floor luminance): 85th and 15th percentile of the body against the floor beside it."""
    if m.sum() < AREA_MIN: return 0.0, 0.0, 0.0, 0.0
    fl = float(np.median(Y[ring_of(m)])); hi, lo, md = np.percentile(Y[m], 85), np.percentile(Y[m], 15), np.median(Y[m])
    r = lambda v: float((max(v, fl) + 0.05) / (min(v, fl) + 0.05))
    return (r(hi) if hi > fl else 1.0), (r(lo) if lo < fl else 1.0), r(md), fl

def brass(img, Y, name):
    m = mask(name)
    if m.sum() < 50: return None
    return img[m].mean(0) * 255, float(Y[m].mean()), int(m.sum())

def fit(m, h=400):
    """crop to the outline, scale to height h, paste bottom-centre on a wide canvas."""
    if not m.any(): return np.zeros((h, 4 * h), bool)
    ys, xs = np.where(m); c = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; w = max(1, round(c.shape[1] * h / c.shape[0]))
    im = np.asarray(Image.fromarray((c * 255).astype(np.uint8)).resize((w, h), Image.NEAREST)) > 128; out = np.zeros((h, 4 * h), bool)
    w = min(w, 4 * h); x0 = (4 * h - w) // 2; out[:, x0:x0 + w] = im[:, :w]; return out

def iou(a, b): return float((a & b).sum() / max((a | b).sum(), 1))

n = fails = 0
def gate(ok, line):
    global n, fails
    n += 1; fails += not ok; print(('PASS ' if ok else 'FAIL ') + line)

img, Y = load('lineup_light'); _, Yn = load('lineup_noline'); _, Yc = load('lineup_play')
allm = np.any([mask(f'mask_{p}') for p in CHARS + PROPS + ['ding']], axis=0)
print(f'INFO floor on screen (lineup, relative luminance, median of the lower third): lighter candidate {np.median(Y[720:][~allm[720:]]):.3f}, current {np.median(Yc[720:][~allm[720:]]):.3f}')
for pid in CHARS:
    m = mask(f'mask_{pid}'); ok, share, med, area, hpx = contrast(Y, m)
    gate(ok, f'{pid} with the game renderer outline (simulated, 2 px) at play size ({hpx} px high, {area} px): {share:.0%} of outline pixels >= {RATIO}:1 on the lighter floor (min {EDGE_SHARE:.0%}); body median {med:.1f}:1')
    _, s2, m2, _, _ = contrast(Yn, m & ndimage.binary_erosion(m, iterations=2)); print(f'INFO {pid} without the outline (body only): outline share {s2:.0%}, body median {m2:.1f}:1')
dk = reads(Y, mask('mask_ding')); dbest = max(dk[0], dk[1])
print(f'INFO ding (the reference prop, no outline) on the lighter floor: bright part {dk[0]:.1f}:1, dark part {dk[1]:.1f}:1, body median {dk[2]:.1f}:1 (floor {dk[3]:.3f})')
for pid in PROPS:
    m = mask(f'mask_{pid}'); b, d, md, fl = reads(Y, m); _, share, _, area, hpx = contrast(Y, m)
    gate(area >= AREA_MIN and max(b, d) >= READ_K * dbest, f'{pid} reads like the ding ({hpx} px high, {area} px, no outline): bright part {b:.1f}:1, dark part {d:.1f}:1, body median {md:.1f}:1 against the ding {dk[0]:.1f} / {dk[1]:.1f} / {dk[2]:.1f} (stronger part >= {READ_K} x the ding: {max(b, d):.1f} against {READ_K * dbest:.1f})')
    print(f'INFO {pid} outline share at 3:1 (not a gate for static props): {share:.0%}')
ref = brass(img, Y, 'mat_ding')
if ref is None: gate(False, 'ding brass mask empty: nothing to compare the brass with')
else:
    print(f'INFO ding brass mean colour rgb({ref[0][0]:.0f}, {ref[0][1]:.0f}, {ref[0][2]:.0f}), relative luminance {ref[1]:.3f} ({ref[2]} px)')
    for pid, what in (('crab', 'brass'), ('wanderer', 'brass'), ('plate', 'brass'), ('leader_crown', 'gold')):
        b = brass(img, Y, f'mat_{pid}')
        if b is None: gate(False, f'{pid} {what} mask empty'); continue
        k = b[1] / ref[1]; warm = b[0][0] > b[0][1] > b[0][2]
        gate(BRASS_BAND[0] <= k <= BRASS_BAND[1] * (1.6 if what == 'gold' else 1.0) and warm, f'{pid} {what} mean colour rgb({b[0][0]:.0f}, {b[0][1]:.0f}, {b[0][2]:.0f}), luminance {b[1]:.3f} = {k:.2f} x the ding brass (band {BRASS_BAND[0]}-{BRASS_BAND[1]}{", gold up to 1.6 x that" if what == "gold" else ""}), warm (r > g > b): {warm}')
for view in ('play', 'approach'):
    _, Yt = load(f'throne_{view}_light'); m = mask(f'mask_kaymuse_{view}'); ok, share, med, area, hpx = contrast(Yt, m)
    gate(ok, f'kaymuse on the throne, {view} framing ({hpx} px high, {area} px, no outline): {share:.0%} of outline pixels >= {RATIO}:1 against the throne behind her (min {EDGE_SHARE:.0%}); body median {med:.1f}:1')
for yaw in (0, 90):
    a, b = sil(f'sil_crab_{yaw}'), sil(f'sil_wanderer_{yaw}'); raw = iou(a, b); nor = iou(fit(a), fit(b))
    gate(a.sum() >= AREA_MIN and b.sum() >= AREA_MIN and raw <= IOU_MAX and nor <= IOU_MAX, f'crab against wanderer, game camera yaw {yaw}: silhouette IoU {raw:.2f} at the same scale, {nor:.2f} scaled to one height (max {IOU_MAX})')
print(f'{n - fails} of {n} pass')

if '--mutate' in sys.argv:
    res = []; lin = lambda im: np.where(im <= 0.04045, im / 12.92, ((im + 0.055) / 1.055) ** 2.4) @ [0.2126, 0.7152, 0.0722]
    m = mask('mask_wanderer'); ok0, share0, *_ = contrast(Y, m); im2 = img.copy(); im2[m] = np.median(img[ring_of(m)], axis=0)
    ok, share, *_ = contrast(lin(im2), m); res.append((not ok and share < share0, f'character outline gate against the wanderer repainted in its surround colour -> outline {share:.0%} (unmutated {share0:.0%}{"" if ok0 else ": the unmutated piece fails too, so this proves less"})'))
    ok, _, _, area, _ = contrast(Y, np.zeros_like(m)); res.append((not ok, f'visibility gate against an empty mask -> {area} px'))
    m = mask('mask_plate'); im2 = img.copy(); im2[m] = np.median(img[ring_of(m)], axis=0); b, d, *_ = reads(lin(im2), m)
    res.append((max(b, d) < READ_K * dbest, f'reads-like-the-ding gate against the plate repainted in its surround colour -> stronger part {max(b, d):.1f}:1 (needs {READ_K * dbest:.1f})'))
    if ref is not None:
        mm = mask('mat_crab'); k = float(lin(img * 0.5)[mm].mean()) / ref[1] if mm.sum() else 0.0
        res.append((not (BRASS_BAND[0] <= k <= BRASS_BAND[1]), f'brass gate against the crab brass at half value -> {k:.2f} x the ding brass'))
    a = sil('sil_crab_0'); v = iou(a, a); res.append((v > IOU_MAX, f'silhouette gate against the crab compared with itself -> IoU {v:.2f}'))
    v2 = iou(fit(a), fit(a)); res.append((v2 > IOU_MAX, f'scaled silhouette gate against the crab compared with itself -> IoU {v2:.2f}'))
    for hit, line in res: print(('MUT caught: ' if hit else 'MUT MISSED: ') + line)
    print(f'{sum(h for h, _ in res)} of {len(res)} mutations caught')
