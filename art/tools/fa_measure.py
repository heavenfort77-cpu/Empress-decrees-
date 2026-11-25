#!/usr/bin/env python3
"""SUITS fa round 5: measures and review sheet from fa_shoot.mjs shots (cocolito method: the same measures for the new fa and the round-4
fa, so they compare like for like; the owner's kit figures are measured the same way by art/tools/fa_compare.py).
Gates (PASS/FAIL):
  floor contrast (palace study rule, art/tools/suit_contrast.py run on the lineup): fa >= 50% of outline pixels at 3:1 vs the hall floor
  mask vs helm at play size (fight framing 110 px/m): median luminance of mask pixels vs helm pixels >= 3:1 (region-ID pass)
  silhouette: fa vs each of the other eight, flat-black at play size, front and 3/4: IoU <= 0.75 (study rule)
  value range: figure luminance P10-P90 spread >= 120 of 255 and dark share (< 40) <= 45% (cause 1: near-black head to toe)
Numbers: luminance P10/P50/P90, dark and bright shares, k-means colour shares, colours at play size.
Usage: python3 fa_measure.py SHOTDIR METRICS.json OUTDIR"""
import sys, os, json, subprocess
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

S, MJ, O = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(O, exist_ok=True)
# CONFIG
# Floor contrast: share of outline pixels at 3:1 (palace study), mask vs helm ratio, silhouette IoU limit (study), value spread and dark cap.
EDGE_SHARE, MASK_RATIO, IOU_MAX, SPREAD_MIN, DARK_MAX = 0.5, 3.0, 0.75, 120, 0.45
# Head band for the helm pixels at play size: rows from this far above the mask top down to the mask bottom, px.
HEAD_UP_PX = 30
TOOLS = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(MJ)); G = []; N = {}
def gate(ok, line): G.append(('PASS ' if ok else 'FAIL ') + 'fa ' + line)
def load(p): return np.asarray(Image.open(p).convert('RGB')).astype(np.float32) / 255
def relY(img):
    lin = np.where(img <= 0.04045, img / 12.92, ((img + 0.055) / 1.055) ** 2.4); return lin @ np.array([0.2126, 0.7152, 0.0722])
def ratio(a, b): return (max(a, b) + 0.05) / (min(a, b) + 0.05)

# 1. floor contrast: the approved tool on the lineups (new fa first; old fa first)
for tag, d in (('new', S), ('old', os.path.join(S, 'old'))):
    r = subprocess.run([sys.executable, os.path.join(TOOLS, 'suit_contrast.py'), d], capture_output=True, text=True); out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if ' fa ' in l and 'outline' in l), 'missing')
    N[f'contrast_{tag}'] = line
    if tag == 'new':
        try: share = float(line.split('outline vs hall floor: ')[1].split('%')[0]) / 100
        except Exception: share = -1
        gate(share >= EDGE_SHARE, f'floor contrast (suit_contrast.py, lineup_play): {line[5:] if share >= 0 else line}')
        N['contrast_all_new'] = out.strip().splitlines()
    else: N['contrast_all_old'] = out.strip().splitlines()

# 2. mask vs helm at play size
def mask_helm(ida, tex):
    red = (ida[..., 0] > 200) & (ida[..., 1] < 60) & (ida[..., 2] < 60); grn = (ida[..., 1] > 200) & (ida[..., 0] < 60) & (ida[..., 2] < 60)
    if red.sum() <= 5: return None
    ys = np.where(red.any(1))[0]; band = np.zeros_like(red); band[max(0, ys.min() - HEAD_UP_PX):ys.max() + 1] = True
    xs = np.where(red.any(0))[0]; band[:, :max(0, xs.min() - 30)] = False; band[:, xs.max() + 30:] = False
    mk = ndimage.binary_erosion(red, iterations=1); hm = ndimage.binary_erosion(grn & band, iterations=1)
    ym, yh = float(np.median(tex[mk])), float(np.median(tex[hm])); return ratio(ym, yh), ym, yh, int(mk.sum()), int(hm.sum()), mk
mh_ok = lambda r: r is not None and r[0] >= MASK_RATIO and r[3] >= 20 and r[4] >= 20
ida = np.asarray(Image.open(f'{S}/fa_matid_play.png').convert('RGB')).astype(int); tex = relY(load(f'{S}/fa_play0.png'))
R2 = mask_helm(ida, tex)
if R2:
    rr, ym, yh, nm_, nh_, MK = R2; N.update(mask_px=nm_, helm_px=nh_, mask_Y=round(ym, 3), helm_Y=round(yh, 3), mask_vs_helm=round(rr, 2))
    gate(mh_ok(R2), f'mask vs helm at play size {rr:.1f}:1 (mask Y {ym:.3f} over {nm_} px, helm Y {yh:.3f} over {nh_} px; min {MASK_RATIO}:1)')
else: gate(False, 'mask vs helm: no mask pixels in the ID pass')

# 3. silhouettes at play size (lineup order fa, ru, dao, mo, yy, za, ming, zh, nong)
IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
def blobs(p):
    sil = np.asarray(Image.open(p).convert('L')) < 128
    lab, n = ndimage.label(ndimage.binary_closing(sil, iterations=3))
    bl = sorted([(ndimage.center_of_mass(lab == i)[1], i) for i in range(1, n + 1) if (lab == i).sum() > 800])
    out = []
    for _, i in bl:
        m = (lab == i) & sil; ys, xs = np.where(m); cx = int(round(xs.mean()))
        c = np.zeros((420, 420), bool); y1 = ys.max()
        for y, x in zip(ys, xs):
            yy, xx = 410 - (y1 - y), 210 + (x - cx)
            if 0 <= yy < 420 and 0 <= xx < 420: c[yy, xx] = True
        out.append(c)
    return out
def worst_iou(B):
    ious = {IDS[k]: float((B[0] & B[k]).sum() / max((B[0] | B[k]).sum(), 1)) for k in range(1, 9)}; return ious
SIL = {}
for view in ('front', '34'):
    B = blobs(f'{S}/lineup_sil_{view}.png'); SIL[view] = B
    if len(B) != 9: gate(False, f'silhouette {view}: {len(B)} figures found, 9 expected'); continue
    ious = worst_iou(B); worst = max(ious, key=ious.get); N[f'iou_{view}'] = {k: round(v, 3) for k, v in ious.items()}
    gate(ious[worst] <= IOU_MAX, f'silhouette {view} at play size: most alike {worst} IoU {ious[worst]:.2f} (max {IOU_MAX})')

# 4. value range and colours (front close-up, figure masked by the silhouette pass at the same camera), new and old
def kmeans(px, k=7, it=12, seed=1):
    rng = np.random.default_rng(seed); c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(it):
        d = ((px[:, None] - c[None]) ** 2).sum(-1); a = d.argmin(1)
        c = np.array([px[a == j].mean(0) if (a == j).any() else c[j] for j in range(k)])
    return c, np.bincount(a, minlength=k) / len(a)
def value_nums(img, sil):
    m = ndimage.binary_erosion(sil, iterations=1); px = img[m]; lum = (px @ np.array([0.299, 0.587, 0.114])) * 255
    c, sh = kmeans(px[::max(1, len(px) // 6000)] * 255)
    return dict(p10=round(float(np.percentile(lum, 10)), 1), p50=round(float(np.median(lum)), 1), p90=round(float(np.percentile(lum, 90)), 1),
                dark=round(float((lum < 40).mean()), 3), bright=round(float((lum > 200).mean()), 3),
                kmeans=[('#%02x%02x%02x' % tuple(int(v) for v in cc), round(float(s_), 3)) for cc, s_ in sorted(zip(c, sh), key=lambda t: -t[1])])
val_ok = lambda o: o['p90'] - o['p10'] >= SPREAD_MIN and o['dark'] <= DARK_MAX
def values(d, tag):
    img = load(f'{d}/fa_front.png'); sil = np.asarray(Image.open(f'{d}/fa_sil_front.png').convert('L')) < 128
    o = value_nums(img, sil); N[f'values_{tag}'] = o; return o, img, sil
(vn, IMG, SILF), (vo, _, _) = values(S, 'new'), values(os.path.join(S, 'old'), 'old')
gate(val_ok(vn), f"value range P10 {vn['p10']} / P50 {vn['p50']} / P90 {vn['p90']} (spread min {SPREAD_MIN}), "
     f"dark share {vn['dark']:.0%} (max {DARK_MAX:.0%}); round 4 fa: P10 {vo['p10']} / P50 {vo['p50']} / P90 {vo['p90']}, dark {vo['dark']:.0%}")
# mutations (each must fail its gate): mask painted helm-dark; fa's silhouette replaced by ru's; the figure darkened to the round-4 values;
# floor contrast on the round-4 lineup (the rejected fa)
if '--mutate' in sys.argv:
    MU = []
    if R2:
        t2 = tex.copy(); t2[MK] = R2[2]; MU.append(('mask_vs_helm', 'mask painted to the helm value', not mh_ok(mask_helm(ida, t2))))
    if len(SIL.get('front', [])) == 9:
        B2 = list(SIL['front']); B2[0] = B2[1].copy(); MU.append(('silhouette', 'fa outline replaced by ru', max(worst_iou(B2).values()) > IOU_MAX))
    MU.append(('value_range', 'figure darkened x0.25', not val_ok(value_nums(IMG * 0.25, SILF))))
    old_line = N.get('contrast_old', '')
    try: osh = float(old_line.split('outline vs hall floor: ')[1].split('%')[0]) / 100
    except Exception: osh = 1.0
    MU.append(('floor_contrast', 'round-4 fa lineup', osh < EDGE_SHARE))
    for n_, what, caught in MU: print(f"MUT {'caught' if caught else 'MISSED'} fa {n_}: {what}")
    print(f'fa_measure mutations {sum(c for _, _, c in MU)} of {len(MU)} caught')
for g in G: print(g)
nf = sum(g.startswith('FAIL') for g in G); print(f'fa_measure {len(G) - nf} of {len(G)} pass')
json.dump(dict(metrics=M, measures=N, gates=G), open(os.path.join(O, 'fa_r5_measures.json'), 'w'), ensure_ascii=False, indent=1)

# 5. review sheet: close-up row, head close-ups and clips, passes and LODs, play size crop 1:1; old fa beside new at the same camera
def tile(p, w, h, label):
    im = Image.open(p).convert('RGB') if os.path.exists(p) else Image.new('RGB', (w, h), (80, 0, 80))
    if im.size != (w, h): im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im); d.rectangle([0, 0, len(label) * 7 + 8, 16], fill=(0, 0, 0)); d.text((4, 2), label, fill=(255, 255, 255)); return im
T = 400
rows = [
    [(f'{S}/fa_front.png', 'new front'), (f'{S}/fa_34.png', 'new 3/4'), (f'{S}/fa_side.png', 'new side'), (f'{S}/fa_back.png', 'new back'), (f'{S}/old/fa_34.png', 'round 4 3/4 (same camera)')],
    [(f'{S}/fa_head_front.png', 'new head front'), (f'{S}/fa_head_34.png', 'new head 3/4'), (f'{S}/fa_windup.png', f'windup {M.get("tell", "")}'), (f'{S}/fa_strike.png', 'strike'),
     (f'{S}/old/fa_head_34.png', 'round 4 head 3/4')],
    [(f'{S}/fa_pass_sil.png', 'pass sil'), (f'{S}/fa_pass_flat.png', 'pass flat'), (f'{S}/fa_pass_shade.png', 'pass shade'), (f'{S}/old/fa_front.png', 'round 4 front'),
     (f'{S}/old/fa_sil_front.png', 'round 4 sil')],
]
sheet = Image.new('RGB', (T * 5, T * 3 + 540), (18, 13, 22))
for r, row in enumerate(rows):
    for c, (p, l) in enumerate(row): sheet.paste(tile(p, T, T, l), (c * T, r * T))
pp = f'{S}/pair_play.png'
if os.path.exists(pp):
    im = Image.open(pp).convert('RGB'); cx, cy = im.width // 2, im.height // 2 - 40
    crop = im.crop((cx - 500, cy - 260, cx + 500, cy + 260)); d = ImageDraw.Draw(crop)
    d.text((8, 6), 'fight framing 110 px/m, 1:1 crop: round 4 fa (left) and round 5 fa (right)', fill=(255, 255, 255))
    sheet.paste(crop, (0, T * 3 + 10))
d = ImageDraw.Draw(sheet); y = T * 3 + 20
for g in G + [f"visual heads {M.get('heads')} | span {M.get('span')} m | bracer {M.get('bracer')} m | greave {M.get('greave')} m"]:
    d.text((1010, y), g[:150], fill=(255, 255, 255) if g.startswith('PASS') else (255, 140, 120)); y += 18
sheet.save(os.path.join(O, 'fa_r5_sheet.jpg'), quality=90)
for n in ('lineup_play', 'lineup_wide', 'lineup_sil_front', 'lineup_sil_34', 'pair_play', 'pair_turn', 'fa_lods', 'fa_head_front', 'fa_head_34', 'fa_play'):
    if os.path.exists(f'{S}/{n}.png'): Image.open(f'{S}/{n}.png').convert('RGB').save(os.path.join(O, f'{n}.jpg'), quality=90)
for n in ('lineup_play', 'lineup_sil_front', 'fa_head_34', 'fa_play'):
    if os.path.exists(f'{S}/old/{n}.png'): Image.open(f'{S}/old/{n}.png').convert('RGB').save(os.path.join(O, f'old_{n}.jpg'), quality=90)
