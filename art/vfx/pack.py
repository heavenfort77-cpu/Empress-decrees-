# Pack the painted klad frames into the card atlases (VFXP, 25 Nov). Per frame: premultiplied box downsample from the paint scale to the
# cell, value = grey (R), alpha; values dilated into empty texels so linear filtering never darkens edges. Atlas texels: R = value,
# G = alpha, B = 0 (opaque RGB PNG, uploaded as RG8 so no browser premultiplies it). Writes assets/vfx/*.png, *.json and a ramp texture.
# Usage: python3 -I pack.py <frames dir> <families.json> <out dir>
import sys, json, os, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ramps

# ---- CONFIG ----
# Atlas width (texture cap 1024 per side) and the clear gutter around every cell, texels.
ATLAS_W, MAX_H, GUTTER = 1024, 1024, 2
# How each atlas is drawn in the game: blend = premultiplied alpha blending (soft painted edges), cut = alpha test at CUT with alpha to coverage.
ATLAS_MODE = {'soft_a': 'blend', 'soft_b': 'blend', 'ground': 'cut'}
CUT = 0.5

FR, FAMF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
FAM = json.load(open(FAMF)); os.makedirs(OUT, exist_ok=True)

def load_frame(k, i, fam):
    a = np.array(Image.open(f'{FR}/{k}/f{i + 1}.png').convert('RGBA')).astype(float) / 255
    K = fam['paintK']; H, W = a.shape[0] // K, a.shape[1] // K
    a = a[:H * K, :W * K].reshape(H, K, W, K, 4)
    al = a[..., 3].mean((1, 3)); pv = (a[..., 0] * a[..., 3]).mean((1, 3))
    val = np.where(al > 1e-4, pv / np.maximum(al, 1e-4), 0)
    return val, al

def dilate(val, al, it=6):
    v = val.copy(); m = al > 1 / 255
    for _ in range(it):
        acc = np.zeros_like(v); cnt = np.zeros_like(v)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sv = np.roll(np.roll(v, dy, 0), dx, 1); sm = np.roll(np.roll(m, dy, 0), dx, 1)
            acc += sv * sm; cnt += sm
        new = (~m) & (cnt > 0); v[new] = acc[new] / cnt[new]; m = m | new
    return v

atl = {}
for k, fam in FAM.items():
    atl.setdefault(fam['atlas'], []).append(k)
meta_all = {'version': 1, 'atlases': {}, 'effects': {}, 'ramps': {'file': 'vfx_ramps.png', 'rows': [n for n, _ in ramps.ROWS], 'hex': {n: h for n, h in ramps.ROWS}, 'width': ramps.WIDTH}}
report = []
for name, ks in atl.items():
    ks = sorted(ks, key=lambda k: -FAM[k]['cell'][1])
    img = np.zeros((MAX_H, ATLAS_W, 3), np.uint8); x = y = rowh = 0; used_h = 0
    for k in ks:
        fam = FAM[k]; cw, ch = fam['cell']; sw, sh = cw + 2 * GUTTER, ch + 2 * GUTTER
        cols = max(1, min(fam['frames'], (ATLAS_W - x) // sw)) if x + sw <= ATLAS_W else 0
        if cols < fam['frames']:  # start the family on a fresh shelf so its frames sit in one block
            if x > 0: x = 0; y += rowh; rowh = 0
            cols = min(fam['frames'], ATLAS_W // sw)
        rows_ = math.ceil(fam['frames'] / cols); x0, y0 = x, y
        if y0 + rows_ * sh > MAX_H: sys.exit(f'OVERFLOW {name} {k} at y {y0}')
        empty = []
        for i in range(fam['frames']):
            val, al = load_frame(k, i, fam)
            if val.shape != (ch, cw): sys.exit(f'size {k} {val.shape} vs cell {cw}x{ch}')
            v = dilate(val, al); cx, cy = x0 + (i % cols) * sw + GUTTER, y0 + (i // cols) * sh + GUTTER
            img[cy:cy + ch, cx:cx + cw, 0] = np.round(np.clip(v, 0, 1) * 255); img[cy:cy + ch, cx:cx + cw, 1] = np.round(np.clip(al, 0, 1) * 255)
            # edge texels of the cell carry no alpha (clipping check: painted alpha on the cell border means the effect is cut off)
            empty.append(float(al.sum()))
            border = max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max())
            if border > 0.1: report.append(f'CLIP {k} f{i} border alpha {border:.2f}')
        blockw = cols * sw
        if rows_ == 1: x = x0 + blockw; rowh = max(rowh, sh)
        else: x = 0; y = y0 + rows_ * sh; rowh = 0
        used_h = max(used_h, y0 + rows_ * sh)
        tex = fam['texel']; piv = fam['pivot']
        e = {'name': k, 'atlas': name, 'blend': ATLAS_MODE[name], 'orient': fam['orient'], 'frames': fam['frames'], 'fps': fam['fps'],
             'loop': fam.get('loop'), 'cellPx': [cw, ch], 'originPx': [x0 + GUTTER, y0 + GUTTER], 'stridePx': [sw, sh], 'cols': cols,
             'pivotPx': piv, 'texelM': tex, 'sizeM': [round(cw * tex, 3), round(ch * tex, 3)],
             'pivotM': [round(piv[0] * tex, 3), round((ch - piv[1]) * tex, 3)], 'durationS': round(fam['frames'] / fam['fps'], 3),
             'alphaSum': [round(s, 1) for s in empty], 'ref': 'pixelfx ' + fam['ref'] + ' (shape and timing only)'}
        e['anchorHeightM'] = fam.get('anchorM', 0.0)
        # share of the ash row mixed over the caster's row (smoke: a grey body with the school colour as a tint; owner 25 Nov)
        e['ashMix'] = fam.get('ashMix', 0.0)
        for u in ('unitLenM', 'unitWidthM', 'unitRadiusM'):
            if u in fam: e[u] = fam[u]
        meta_all['effects'][k] = e
    H = int(math.ceil(used_h / 4) * 4); img = img[:H]
    Image.fromarray(img, 'RGB').save(f'{OUT}/vfx_{name}.png', optimize=True)
    meta_all['atlases'][name] = {'file': f'vfx_{name}.png', 'size': [ATLAS_W, H], 'blend': ATLAS_MODE[name], 'cut': CUT if ATLAS_MODE[name] == 'cut' else None,
                                 'format': 'RG8 (R value, G alpha), linear filter, no mipmaps', 'gpuMB': round(ATLAS_W * H * 2 / 1048576, 2)}
    for k in ks: meta_all['effects'][k]['atlasSize'] = [ATLAS_W, H]
rt = np.round(ramps.ramp_table() * 255).astype(np.uint8)
Image.fromarray(rt, 'RGB').save(f'{OUT}/vfx_ramps.png')
json.dump(meta_all, open(f'{OUT}/vfx.json', 'w'), indent=1, ensure_ascii=False)
for k, e in meta_all['effects'].items():
    json.dump(e, open(f'{OUT}/fx_{k}.json', 'w'), indent=1, ensure_ascii=False)
for n, a in meta_all['atlases'].items(): print('ATLAS', n, a['size'], a['blend'], a['gpuMB'], 'MB')
for r in report: print(r)
