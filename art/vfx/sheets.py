# Contact sheets of the packed card atlases (VFXP, 25 Nov): every frame of every effect, coloured by one ramp row, composited over the
# approved 丹 hall floor at one scale (PX_PER_M), with a suit-sized box (0.9 x 2.05 m, front view) beside each upright card. Ground cards
# are squashed by sin(pitch) as the play camera sees them. Also measures the floor read (see GATES in checks.py).
# Usage: python3 -I sheets.py <assets dir> <floor png> <out dir> [row ...]
import sys, json, os, math
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ramps

# ---- CONFIG ----
# Sheet scale (pixels per metre; the play camera at 1080p shows about 110) and the play camera pitch (deg).
PX_PER_M, PITCH = 66, 40
# Floor texture metres per tile (CONFIG.TEX.tileM.palFloor) and the suit box colour.
FLOOR_TILE_M, BOX = 4, (58, 123, 213)

A, FLOOR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(OUT, exist_ok=True)
M = json.load(open(f'{A}/vfx.json')); ATL = {n: np.array(Image.open(f'{A}/{a["file"]}')).astype(float) / 255 for n, a in M['atlases'].items()}
fl = Image.open(FLOOR).convert('RGB'); fs = int(FLOOR_TILE_M * PX_PER_M); fl = np.array(fl.resize((fs, fs), Image.LANCZOS)).astype(float) / 255

def frame(e, i):
    a = ATL[e['atlas']]; cw, ch = e['cellPx']; x = e['originPx'][0] + (i % e['cols']) * e['stridePx'][0]; y = e['originPx'][1] + (i // e['cols']) * e['stridePx'][1]
    return a[y:y + ch, x:x + cw, 0], a[y:y + ch, x:x + cw, 1]

def card_img(e, i, row):
    v, al = frame(e, i); am = e.get('ashMix', 0); L = ramps.lut(row) * (1 - am) + ramps.lut(M['ramps']['rows'].index('ash')) * am
    rgb = L[np.clip(np.round(v * 255), 0, 255).astype(int)]
    if e['blend'] == 'cut': al = (al >= M['atlases'][e['atlas']]['cut']).astype(float)
    s = e['texelM'] * PX_PER_M; w, h = max(1, round(v.shape[1] * s)), max(1, round(v.shape[0] * s * (math.sin(math.radians(PITCH)) if e['orient'] == 'ground' else 1)))
    im = Image.fromarray(np.uint8(np.clip(np.dstack([rgb, al]), 0, 1) * 255), 'RGBA').resize((w, h), Image.BILINEAR)
    a = np.array(im).astype(float) / 255
    if e['blend'] == 'cut': a[..., 3] = (a[..., 3] >= 0.5).astype(float)
    a[..., :3] *= a[..., 3:4]
    return a  # premultiplied rgb, alpha

def floor_patch(w, h, ox=0, oy=0):
    reps = (h + oy) // fl.shape[0] + 2, (w + ox) // fl.shape[1] + 2
    return np.tile(fl, (reps[0], reps[1], 1))[oy:oy + h, ox:ox + w].copy()

def sheet(row, name):
    rowsimg = []; W = 0
    for k, e in M['effects'].items():
        cells = []
        for i in range(e['frames']):
            c = card_img(e, i, row); ch, cw = c.shape[:2]
            box = e['orient'] == 'bill'; bw = int(0.9 * PX_PER_M); pad = 8; boxh = int(2.05 * PX_PER_M)
            pvx, pvy = int(e['pivotPx'][0] * e['texelM'] * PX_PER_M), int(e['pivotPx'][1] * e['texelM'] * PX_PER_M * (1 if box else math.sin(math.radians(PITCH))))
            lift = int(e.get('anchorHeightM', 0) * PX_PER_M)
            Wc = max(cw + 2 * pad, pvx + pad + bw); Hc = max(ch + lift, boxh + 4) + 2 * pad
            bg = floor_patch(Wc, Hc, (i * 37) % 200, (i * 53) % 200)
            gy = Hc - pad - max(0, (ch - pvy) - lift) if box else Hc // 2
            if box:
                bx0 = pad + pvx - bw // 2; bg[max(0, gy - boxh):gy, max(0, bx0):bx0 + bw] = np.array(BOX) / 255
                ox, oy = pad, gy - lift - pvy
            else: ox, oy = pad, gy - pvy
            oy = max(0, min(oy, Hc - ch)); ox = max(0, min(ox, Wc - cw))
            reg = bg[oy:oy + ch, ox:ox + cw]; reg[:] = c[..., :3] + reg * (1 - c[..., 3:4]); cells.append(bg)
        H = max(c.shape[0] for c in cells); strip = np.zeros((H + 14, sum(c.shape[1] + 2 for c in cells) + 70, 3)) + 0.07
        x = 70
        for c in cells: strip[14:14 + c.shape[0], x:x + c.shape[1]] = c; x += c.shape[1] + 2
        im = Image.fromarray(np.uint8(np.clip(strip, 0, 1) * 255)); d = ImageDraw.Draw(im); d.text((2, 16), k, fill=(230, 230, 230))
        d.text((70, 1), f"{e['frames']}f {e['fps']}fps {e['durationS']}s loop {e['loop']} {e['blend']} {e['orient']}", fill=(200, 200, 200))
        rowsimg.append(np.array(im)); W = max(W, im.width)
    out = np.zeros((sum(r.shape[0] + 4 for r in rowsimg) + 20, W, 3), np.uint8) + 18; y = 20
    for r in rowsimg: out[y:y + r.shape[0], :r.shape[1]] = r; y += r.shape[0] + 4
    im = Image.fromarray(out); ImageDraw.Draw(im).text((4, 4), f'ramp {name} ({M["ramps"]["hex"][name]}) on the hall floor, {PX_PER_M} px/m, suit box 0.9 x 2.05 m', fill=(240, 240, 240))
    im.save(f'{OUT}/sheet_{name}.png'); return im.size


def peaks(out_name='peaks_all_rows.png', px=44):
    """One sheet: a row per ramp row, a column per card at its peak (tells: mid loop) frame, same floor, same scale."""
    global PX_PER_M
    keep = PX_PER_M; PX_PER_M = px; tiles = []
    for r, name in enumerate(M['ramps']['rows']):
        row = []
        for k, e in M['effects'].items():
            i = e['loop'][0] + 1 if e['loop'] and e['loop'][1] < e['frames'] else int(np.argmax(e['alphaSum']))
            c = card_img(e, i, r); h, w = c.shape[:2]; bg = floor_patch(max(w, 40) + 8, max(h, 40) + 8, r * 17, r * 29)
            reg = bg[4:4 + h, 4:4 + w]; reg[:] = c[..., :3] + reg * (1 - c[..., 3:4]); row.append(bg)
        H = max(t.shape[0] for t in row); strip = np.zeros((H, sum(t.shape[1] + 2 for t in row) + 90, 3)) + 0.07; x = 90
        for t in row: strip[:t.shape[0], x:x + t.shape[1]] = t; x += t.shape[1] + 2
        im = Image.fromarray(np.uint8(np.clip(strip, 0, 1) * 255)); ImageDraw.Draw(im).text((4, 4), name, fill=(235, 235, 235)); tiles.append(np.array(im))
    W = max(t.shape[1] for t in tiles); out = np.zeros((sum(t.shape[0] + 3 for t in tiles) + 18, W, 3), np.uint8) + 18; y = 18
    for t in tiles: out[y:y + t.shape[0], :t.shape[1]] = t; y += t.shape[0] + 3
    im = Image.fromarray(out); ImageDraw.Draw(im).text((90, 3), '  '.join(M['effects']) + f'   ({px} px/m, peak frames, ground cards squashed by sin 40)', fill=(240, 240, 240))
    im.save(f'{OUT}/{out_name}', optimize=True); PX_PER_M = keep; return im.size

if __name__ == '__main__':
    rows = M['ramps']['rows']; want = sys.argv[4:] or rows
    if want == ['peaks']: print('peaks', peaks())
    else:
        for n in want: print(n, sheet(rows.index(n), n))
