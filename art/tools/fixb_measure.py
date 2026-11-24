#!/usr/bin/env python3
"""FIXB 25 Nov on-screen gates for the owner's 02:1x-02:2x picks, from art/tools/fixb_shoot.mjs shots and unlit masks (same camera).
Prints PASS/FAIL lines with numbers, then 'N of N pass'. With 'mut' as the 2nd argument it breaks each gate's input in memory and prints
CAUGHT/MISSED per mutation (every gate must fail on its broken input). Usage: python3 fixb_measure.py SHOTDIR [mut] [R1_MERC_DIR]"""
import json, os, sys
import numpy as np
from PIL import Image

D = sys.argv[1]; MUT = len(sys.argv) > 2 and sys.argv[2] == 'mut'; R1 = sys.argv[3] if len(sys.argv) > 3 else 'art/merc/round1'
ST = json.load(open(f'{D}/stats.json'))
# CONFIG: gate thresholds (owner 02:2x wording in brackets)
# brass sheet everywhere (bronze = brass): texture files a shot may never load
NOT_BRASS = ('bronze_trim.png', 'bronze_trim_patina.png')
# fuller planting / bigger racks: on-screen share of the tagged mask at the wide camera, after over before (min ratio)
PLANT_GAIN, RACK_GAIN = 1.8, 1.8
# throne larger: screen height of the throne above the dais top, after over before (min ratio)
THRONE_GAIN = 1.25
# pond: mean lum at the wide camera not more than POND_BELOW under the garden ground, the 1 m margin at least POND_EDGE over the open water
POND_BELOW, POND_EDGE = 25, 8
# star inlay: floor region colour change with the inlay (CIELAB dE, max) and mean lum change (max); the inlay seen at play (min mean
# |lum step| on inlay pixels); hazard ring contrast with the inlay at least RING_KEEP x the contrast without it
INLAY_DE, INLAY_DL, INLAY_SEEN, RING_KEEP = 4.0, 5.0, 8.0, 0.9
# mercury: warn minus idle mean lum on the mercury surface (min), hot minus warn (min), shimmer = mean |diff| between two warn stills
# 0.15 s apart (min), and idle calmer than warn
MERC_WARN, MERC_HOT, MERC_SHIM = 40, 8, 4.0
# budgets per shot (CLAUDE.md): calls, triangles
CALLS, TRIS = 500, 500000

def img(n): return np.asarray(Image.open(f'{D}/{n}.png').convert('RGB')).astype(float)
def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
def mask(n): return lum(img(n)) > 30
def lab(rgb):
    """CIELAB of one sRGB colour (0-255)."""
    c = np.asarray(rgb, float) / 255; c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    X, Y, Z = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]) @ c / np.array([0.9505, 1.0, 1.089])
    f = lambda t: np.cbrt(t) if t > 0.008856 else 7.787 * t + 16 / 116
    return np.array([116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))])
def dE(a, b): return float(np.linalg.norm(lab(a) - lab(b)))
def erode(m, k):
    o = m.copy()
    for _ in range(k): o = o & np.roll(o, 1, 0) & np.roll(o, -1, 0) & np.roll(o, 1, 1) & np.roll(o, -1, 1)
    return o
def dilate(m, k):
    o = m.copy()
    for _ in range(k): o = o | np.roll(o, 1, 0) | np.roll(o, -1, 0) | np.roll(o, 1, 1) | np.roll(o, -1, 1)
    return o

def gates(I, S):
    """I(name) -> image, S = stats; returns [(name, ok, line)]"""
    R = []
    M = lambda n: lum(I(n)) > 30
    bad = [n for n, v in S.items() if not n.startswith('mut_') and any(t in NOT_BRASS for t in v['textures'])]
    R.append(('brass only', not bad, f'{len([n for n in S if not n.startswith("mut_")])} shots, none loads {"/".join(NOT_BRASS)}' if not bad else 'bronze sheet loaded in ' + ', '.join(bad[:6])))
    errs = [n for n, v in S.items() if v['errs']]
    R.append(('shots clean', not errs, f'{len(S)} shots without page errors' if not errs else 'errors in ' + ', '.join(errs[:6])))
    over = [n for n, v in S.items() if v['stats'] and 'totalCalls' in v['stats'] and (v['stats']['totalCalls'] >= CALLS or v['stats']['totalTris'] >= TRIS)]
    heavy = max((v['stats']['totalCalls'], v['stats']['totalTris'], n) for n, v in S.items() if v['stats'] and 'totalCalls' in v['stats'])
    R.append(('budget', not over, f'heaviest {heavy[2]} {heavy[0]} calls, {heavy[1]} tris (under {CALLS} / {TRIS})' if not over else 'over: ' + ', '.join(over)))
    g0, g1 = S['garden_wide_r2']['stats'], S['garden_wide']['stats']
    R.append(('garden calls', g1['totalCalls'] <= g0['totalCalls'], f"garden_wide calls {g0['totalCalls']} -> {g1['totalCalls']} (no more), tris {g0['totalTris']} -> {g1['totalTris']}"))
    p0, p1 = M('mask_garden_wide_plants_r2').mean(), M('mask_garden_wide_plants').mean()
    R.append(('planting fuller', p1 >= PLANT_GAIN * p0, f'plant cards cover {p0:.3f} -> {p1:.3f} of the wide shot (x{p1 / max(p0, 1e-6):.2f}, min x{PLANT_GAIN})'))
    r0, r1 = M('mask_hall_wide_racks_r2').mean(), M('mask_hall_wide_racks').mean()
    R.append(('racks bigger', r1 >= RACK_GAIN * r0, f'racks and bundles cover {r0:.4f} -> {r1:.4f} of hall_wide (x{r1 / max(r0, 1e-6):.2f}, min x{RACK_GAIN})'))
    t0, t1 = S['mask_core_wide_throne_r2']['stats']['throneBox'], S['mask_core_wide_throne']['stats']['throneBox']
    R.append(('throne larger', t1['h'] >= THRONE_GAIN * t0['h'] and t1['w'] >= t0['w'], f"throne above the dais at core_wide {t0['w']} x {t0['h']} px -> {t1['w']} x {t1['h']} px (height x{t1['h'] / max(t0['h'], 1):.2f}, min x{THRONE_GAIN})"))
    g = I('garden_wide'); pm, gm = M('mask_garden_wide_pond'), M('mask_garden_wide_ground')
    pl, gl = lum(g)[pm].mean(), lum(g)[gm].mean(); inner = erode(pm, 12); edge = pm & ~erode(pm, 5)
    el, cl = lum(g)[edge].mean(), lum(g)[inner].mean()
    R.append(('pond not a hole', pl >= gl - POND_BELOW, f'pond mean lum {pl:.0f} vs ground {gl:.0f} at garden_wide (max {POND_BELOW} under)'))
    R.append(('pond pale edge', el >= cl + POND_EDGE, f'pond margin lum {el:.0f} vs open water {cl:.0f} (min +{POND_EDGE})'))
    for v in ('wide', 'play'):
        fm = M(f'mask_core_{v}_floor'); a, b = I(f'core_{v}'), I(f'core_{v}_noinlay')
        de = dE(a[fm].mean(0), b[fm].mean(0)); dl = lum(a)[fm].mean() - lum(b)[fm].mean()
        R.append((f'inlay keeps floor ({v})', de <= INLAY_DE and abs(dl) <= INLAY_DL, f'core_{v} floor colour dE {de:.2f} (max {INLAY_DE}), lum {dl:+.1f} (max {INLAY_DL}) with the inlay'))
        rm = M(f'mask_core_{v}_tell'); sur = dilate(rm, 8) & ~dilate(rm, 2) & fm
        def rc(x): return dE(x[rm].mean(0), x[sur].mean(0))
        c1, c0 = rc(I(f'core_{v}_tell')), rc(I(f'core_{v}_tell_noinlay'))
        R.append((f'tells kept ({v})', c1 >= RING_KEEP * c0, f'hazard ring vs floor dE {c0:.1f} -> {c1:.1f} with the inlay (min x{RING_KEEP})'))
    im_ = M('mask_core_play_inlay'); seen = np.abs(lum(I('core_play')) - lum(I('core_play_noinlay')))[im_].mean() if im_.any() else 0
    R.append(('inlay seen at play', seen >= INLAY_SEEN, f'inlay pixels differ by mean lum {seen:.1f} from the bare floor (min {INLAY_SEEN}; subtle, still there)'))
    mm = M('mask_merc_play'); L = {k: lum(I(f'merc_play_{k}'))[mm].mean() for k in ('idle', 'warn', 'hot')}
    R.append(('mercury warn brighter', L['warn'] - L['idle'] >= MERC_WARN and L['hot'] - L['warn'] >= MERC_HOT,
              f"mercury mean lum idle {L['idle']:.0f}, warn {L['warn']:.0f} (+{L['warn'] - L['idle']:.0f}, min +{MERC_WARN}), hot {L['hot']:.0f} (+{L['hot'] - L['warn']:.0f} over warn, min +{MERC_HOT})"))
    sw = np.abs(lum(I('merc_play_warn')) - lum(I('merc_play_warn_t2')))[mm].mean(); si = np.abs(lum(I('merc_play_idle')) - lum(I('merc_play_idle_t2')))[mm].mean()
    R.append(('mercury shimmer', sw >= MERC_SHIM and si < sw, f'warn still t 0.40 vs 0.55 differs by {sw:.1f} lum (min {MERC_SHIM}); idle {si:.1f} (calmer)'))
    return R

def report(R, quiet=False):
    f = 0
    for n, ok, line in R:
        f += not ok
        if not quiet: print(f"{'PASS' if ok else 'FAIL'} {n}: {line}")
    return f

if not MUT:
    cache = {}
    I = lambda n: cache.setdefault(n, img(n))
    R = gates(I, ST); f = report(R); print(f'{len(R) - f} of {len(R)} pass')
    if os.path.exists(f'{R1}/play_idle.png'):
        mm = mask('mask_merc_play')
        r1 = {k: lum(np.asarray(Image.open(f'{R1}/play_{k}.png').convert('RGB')).astype(float))[mm].mean() for k in ('idle', 'warn', 'hot')}
        print(f"INFO mercury round 1 (same camera and mesh): idle {r1['idle']:.0f}, warn {r1['warn']:.0f}, hot {r1['hot']:.0f}")
else:
    base = {}
    def I0(n): return base.setdefault(n, img(n))
    def swap(m): return lambda n: I0(m.get(n, n))
    def darken(name, k):  # the pond pixels only (darkening the whole shot darkens the ground too: round 1 MISSED)
        def f(n):
            a = I0(n)
            if n != name: return a
            b = a.copy(); pm = mask('mask_garden_wide_pond'); b[pm] *= k; return b
        return f
    def bright(name, d): return lambda n: np.clip(I0(n) + (d if n == name else 0), 0, 255)
    def flat_pond(n):
        a = I0(n)
        if n != 'garden_wide': return a
        b = a.copy(); pm = mask('mask_garden_wide_pond'); b[pm] = a[pm].mean(0); return b
    S_mut = json.loads(json.dumps(ST)); S_mut['tally_play']['textures'] = S_mut['mut_bronze_tally_play']['textures']
    S_calls = json.loads(json.dumps(ST)); S_calls['garden_wide']['stats']['totalCalls'] += 4
    S_thr = json.loads(json.dumps(ST)); S_thr['mask_core_wide_throne']['stats']['throneBox'] = S_thr['mask_core_wide_throne_r2']['stats']['throneBox']
    MUTS = [('brass only', I0, S_mut), ('garden calls', I0, S_calls), ('throne larger', I0, S_thr),
            ('planting fuller', swap({'mask_garden_wide_plants': 'mask_garden_wide_plants_r2'}), ST), ('racks bigger', swap({'mask_hall_wide_racks': 'mask_hall_wide_racks_r2'}), ST),
            ('pond not a hole', darken('garden_wide', 0.45), ST), ('pond pale edge', flat_pond, ST), ('inlay keeps floor (wide)', bright('core_wide', 14), ST),
            ('tells kept (play)', swap({'core_play_tell': 'core_play_noinlay'}), ST), ('inlay seen at play', swap({'core_play': 'core_play_noinlay'}), ST),
            ('mercury warn brighter', swap({'merc_play_warn': 'merc_play_idle'}), ST), ('mercury shimmer', swap({'merc_play_warn_t2': 'merc_play_warn'}), ST)]
    c = 0
    for gate, I, S in MUTS:
        R = gates(I, S); hit = any(n == gate and not ok for n, ok, _ in R); c += hit
        print(('CAUGHT ' if hit else 'MISSED ') + gate)
    print(f'{c} of {len(MUTS)} caught')
