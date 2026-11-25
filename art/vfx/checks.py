# Pass/fail gates for the painted card atlases (VFXP, 25 Nov). Prints one line per gate (PASS/FAIL + numbers) and the failing items only.
# Usage: python3 -I checks.py <assets dir> <floor png> <vfx_map.json>
import sys, json, os, math
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ramps

# ---- CONFIG ----
# Texture cap per side, most atlases, and the clear gutter (texels) that must stay empty round each cell.
CAP, MAX_ATLASES, GUTTER = 1024, 3, 2
# A one-shot must end empty: its last frame's alpha sum at most this share of its peak frame's.
END_EMPTY = 0.03
# A tell's loop frames must each keep at least this share of the peak alpha sum (it stays visible all through the windup),
# and its intro (frames before the loop) must last at most INTRO_MAX s so the shortest windup (MIN_WINDUP) still shows the loop.
LOOP_KEEP, INTRO_MAX, MIN_WINDUP = 0.25, 0.2, 0.4
# Floor read: share of a tell card's drawn pixels at WCAG contrast >= READ_RATIO against the floor under it, at least READ_SHARE, per ramp row.
READ_RATIO, READ_SHARE = 3.0, 0.25
# Face clearance for cards drawn round a body (feet at the pivot): max alpha inside the face box (x +-FACE_X m, FACE_Y m above the feet).
FACE_X, FACE_Y, FACE_MAX, FACE_FAMS = 0.22, (1.5, 1.95), 0.5, ('aura', 'heal', 'shield', 'smoke')
# Distinct effects (owner 25 Nov): every pair of these rows at least PAIR_DE apart (CIE76 Lab, D65, as art/tools/standard_check.py) in play:
# the mean colour of each PAIR_CARDS card at its peak frame blended over the 丹 floor (pixels with alpha >= PAIR_ALPHA).
PAIR_ROWS, PAIR_DE, PAIR_CARDS, PAIR_ALPHA = ('ru', 'dao', 'fa', 'mo', 'yinyang', 'za', 'ming', 'zongheng', 'nong', 'apex'), 10, ('slash', 'burst', 'impact', 'bolt'), 0.5
# Floor texture metres per tile (CONFIG.TEX.tileM.palFloor), for sampling the floor at the card's scale.
FLOOR_TILE_M = 4

A, FLOOR, MAP = sys.argv[1], sys.argv[2], sys.argv[3]
M = json.load(open(f'{A}/vfx.json')); MP = json.load(open(MAP))
ATL = {n: np.array(Image.open(f'{A}/{a["file"]}')).astype(float) / 255 for n, a in M['atlases'].items()}
# the shipped ramp texture (what the game samples), as 256-entry sRGB lookups per row
RT = np.array(Image.open(f'{A}/{M["ramps"]["file"]}').convert('RGB')).astype(float) / 255
def lutp(row):
    x = np.linspace(0, 1, RT.shape[1]); v = np.linspace(0, 1, 256); return np.stack([np.interp(v, x, RT[row, :, c]) for c in range(3)], -1)
res = []
def gate(name, ok, info, fails=()):
    res.append(ok); print(f'GATE {name} {"PASS" if ok else "FAIL"} {info}')
    for f in list(fails)[:40]: print('   ', f)

def frame(e, i):
    a = ATL[e['atlas']]; cw, ch = e['cellPx']; x = e['originPx'][0] + (i % e['cols']) * e['stridePx'][0]; y = e['originPx'][1] + (i // e['cols']) * e['stridePx'][1]
    return a[y:y + ch, x:x + cw, 0], a[y:y + ch, x:x + cw, 1], (x, y)

# 1. atlases: count, size cap, format (R value, G alpha, B empty)
bad = [f'{n} {a["size"]}' for n, a in M['atlases'].items() if max(a['size']) > CAP or list(ATL[n].shape[1::-1]) != a['size']]
bad += [f'{n} B channel not empty' for n, t in ATL.items() if t[..., 2].max() > 0]
gate('atlases', len(ATL) <= MAX_ATLASES and not bad, f'{len(ATL)} atlases ' + ', '.join(f'{n} {a["size"][0]}x{a["size"][1]} {a["blend"]}' for n, a in M['atlases'].items()), bad)

# 2. every effect's frames inside its atlas, nothing on the cell border, gutters empty
bad = []; used = {n: np.zeros(t.shape[:2], bool) for n, t in ATL.items()}
for k, e in M['effects'].items():
    for i in range(e['frames']):
        v, al, (x, y) = frame(e, i)
        if al.shape != (e['cellPx'][1], e['cellPx'][0]): bad.append(f'{k} f{i} outside the atlas'); continue
        b = max(al[0].max(), al[-1].max(), al[:, 0].max(), al[:, -1].max())
        if b > 0.1: bad.append(f'{k} f{i} cut off at the cell border (alpha {b:.2f})')
        used[e['atlas']][y:y + al.shape[0], x:x + al.shape[1]] = True
for n, t in ATL.items():
    stray = int(((t[..., 1] > 0) & ~used[n]).sum())
    if stray: bad.append(f'{n}: {stray} alpha texels outside every cell (gutter)')
gate('cells', not bad, f'{len(M["effects"])} effects, {sum(e["frames"] for e in M["effects"].values())} frames', bad)

# 3. JSON fields the game needs
need = ('atlas', 'blend', 'orient', 'frames', 'fps', 'loop', 'cellPx', 'originPx', 'stridePx', 'cols', 'pivotPx', 'texelM', 'sizeM', 'pivotM', 'anchorHeightM', 'atlasSize')
bad = [f'{k} missing {f}' for k, e in M['effects'].items() for f in need if f not in e]
bad += [f'fx_{k}.json missing' for k in M['effects'] if not os.path.exists(f'{A}/fx_{k}.json')]
gate('json', not bad, f'{len(need)} fields x {len(M["effects"])} effects', bad)

# 4. one-shots end empty; tells stay visible through the loop and their intro is short
bad = []; sums = {k: [frame(e, i)[1].sum() for i in range(e['frames'])] for k, e in M['effects'].items()}
for k, e in M['effects'].items():
    s = sums[k]; pk = max(s)
    lp = e['loop']
    if not lp or lp[1] < e['frames']:
        if s[-1] > END_EMPTY * pk: bad.append(f'{k}: last frame alpha {s[-1] / pk:.2f} of peak (one-shot must end empty)')
    if lp:
        lo = [s[i] / pk for i in range(lp[0], lp[1])]
        if min(lo) < LOOP_KEEP: bad.append(f'{k}: loop frame at {min(lo):.2f} of peak')
        if lp[0] / e['fps'] > INTRO_MAX: bad.append(f'{k}: intro {lp[0] / e["fps"]:.2f} s')
gate('timing', not bad, f'end empty <= {END_EMPTY}, loop >= {LOOP_KEEP} of peak, intro <= {INTRO_MAX} s', bad)

# 5. the map: every attack and tell has a card that exists, a ramp row that exists, and tells have windup >= 0.4 s and a looping card
bad = []; rows = M['ramps']['rows']; nt = 0
for it in MP['items']:
    for slot in ('tell', 'release', 'hit', 'trail', 'state'):
        c = it.get(slot)
        if c and c not in M['effects']: bad.append(f'{it["id"]} {slot} card {c} missing')
    if it['ramp'] not in rows and it['ramp'] != 'caster': bad.append(f'{it["id"]} ramp {it["ramp"]} missing')
    if it.get('windup') is not None:
        nt += 1
        if it['windup'] < MIN_WINDUP: bad.append(f'{it["id"]} windup {it["windup"]} s < {MIN_WINDUP}')
        if not it.get('tell'): bad.append(f'{it["id"]} has a windup but no tell card')
        elif not M['effects'][it['tell']]['loop'] and not it.get('repeatS'): bad.append(f'{it["id"]} tell card {it["tell"]} neither loops nor repeats')
gate('map', not bad, f'{len(MP["items"])} items, {nt} tells', bad)

# 6. floor read of every tell card in every ramp row it is used with
fl = np.array(Image.open(FLOOR).convert('RGB')).astype(float) / 255
def Y(c): c = ramps.s2l(c); return c[..., 0] * 0.2126 + c[..., 1] * 0.7152 + c[..., 2] * 0.0722
bad = []; info = []
def rowsof(r): return rows[:9] if r == 'caster' else [x for x in rows if x.startswith('rebel')] if r.startswith('rebel') else [r]
pairs = sorted({(it['tell'], r) for it in MP['items'] if it.get('tell') for r in rowsof(it['ramp'])})
worst = (9, ''); pairw = {}
for k, r in pairs:
    e = M['effects'][k]; am = e.get('ashMix', 0); L = lutp(rows.index(r)) * (1 - am) + lutp(rows.index('ash')) * am; fpx = fl.shape[0] / FLOOR_TILE_M * e['texelM']
    fr = range(e['loop'][0], e['loop'][1]) if e['loop'] else [i for i, x in enumerate(sums[k]) if x >= 0.5 * max(sums[k])]
    for i in fr:
        v, al, _ = frame(e, i); m = al >= (0.5 if e['blend'] == 'cut' else 0.35)
        ys, xs = np.nonzero(m)
        fy = (ys * fpx).astype(int) % fl.shape[0]; fx = (xs * fpx).astype(int) % fl.shape[1]
        cy = Y(L[np.round(v[ys, xs] * 255).astype(int)]); fy_ = Y(fl[fy, fx])
        ratio = (np.maximum(cy, fy_) + 0.05) / (np.minimum(cy, fy_) + 0.05); share = float((ratio >= READ_RATIO).mean())
        if share < worst[0]: worst = (share, f'{k}/{r} f{i}')
        pw = pairw.get((k, r), (9, 0)); pairw[(k, r)] = (min(pw[0], share), i if share < pw[0] else pw[1])
for (k, r), (sh, i) in sorted(pairw.items(), key=lambda x: x[1][0]):
    if sh < READ_SHARE: bad.append(f'{k} on {r}: worst frame f{i} {sh:.2f} of pixels at {READ_RATIO}:1')
gate('floor_read', not bad, f'{len(pairs)} tell-card x ramp pairs, worst {worst[0]:.2f} ({worst[1]}), need {READ_SHARE}', bad)

# 7. face clearance round a body
bad = []
for k in FACE_FAMS:
    e = M['effects'][k]; t = e['texelM']
    x0, x1 = int(e['pivotPx'][0] - FACE_X / t), int(e['pivotPx'][0] + FACE_X / t); y0, y1 = int(e['pivotPx'][1] - FACE_Y[1] / t), int(e['pivotPx'][1] - FACE_Y[0] / t)
    for i in range(e['frames']):
        al = frame(e, i)[1][max(0, y0):y1, max(0, x0):x1]
        if al.size and al.max() > FACE_MAX: bad.append(f'{k} f{i} face box alpha {al.max():.2f}')
gate('face', not bad, f'{len(FACE_FAMS)} body cards, face box alpha <= {FACE_MAX}', bad)

# 8. the nine schools and the apex stay apart on the effects, in play on the floor
def lab(c):
    c = ramps.s2l(np.asarray(c, float)); M_ = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]])
    x = c @ M_.T / np.array([0.95047, 1, 1.08883]); f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)
bad = []; worst = (999, '')
for k in PAIR_CARDS:
    e = M['effects'][k]; i = int(np.argmax(sums[k])); v, al, _ = frame(e, i); m = al >= PAIR_ALPHA; ys, xs = np.nonzero(m)
    fpx = fl.shape[0] / FLOOR_TILE_M * e['texelM']; fb = fl[(ys * fpx).astype(int) % fl.shape[0], (xs * fpx).astype(int) % fl.shape[1]]
    means = {}
    for r in PAIR_ROWS:
        L = lutp(rows.index(r)); c = L[np.round(v[ys, xs] * 255).astype(int)]; a = al[ys, xs][:, None]
        means[r] = lab(ramps.l2s(ramps.s2l(c) * a + ramps.s2l(fb) * (1 - a))).mean(0)
    for x_ in range(len(PAIR_ROWS)):
        for y_ in range(x_ + 1, len(PAIR_ROWS)):
            a_, b_ = PAIR_ROWS[x_], PAIR_ROWS[y_]; d = float(np.linalg.norm(means[a_] - means[b_]))
            if d < worst[0]: worst = (d, f'{a_}/{b_} on {k}')
            if d < PAIR_DE: bad.append(f'{a_} vs {b_} on {k}: dE {d:.1f}')
gate('school_pairs', not bad, f'{len(PAIR_ROWS)} rows, {len(PAIR_CARDS)} cards, worst dE {worst[0]:.1f} ({worst[1]}), need {PAIR_DE}', bad)

print(f'SUMMARY {sum(res)} of {len(res)} PASS')
sys.exit(0 if all(res) else 1)
