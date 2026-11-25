#!/usr/bin/env python3
"""SUITS fa round 5 (owner GO 25 Nov 10:55): the three texture atlases of the rebuilt 法甲 廷尉, drawn the owner's armour-suit kit way
(Techno-Plate-Style-Study.md: engraving = a height picture turned into a colour map plus a normal map). Every surface is a height picture
first (plates, seams, studs, inlay grooves, cloud-scroll engraving), then albedo from the value plan and a tangent-space normal map
(OpenGL / glTF convention: green = up in the image). Light is NOT painted in (the game's sun and hemisphere light the normals);
only cavities (seams, grooves) are darkened, as lacquer pools there.
Atlases (256 px/m everywhere, mask 512 px/m; rows are the builder's UV rows, art/tools/fa_r5.py ROWS):
  suit_fa_armour.png  1024 x 1024 (4 m): lamella strip, big plate field, black lacquer, black silk cord, mask (non-metal)
  suit_fa_metal.png    512 x  512 (2 m): gold inlay band, plain gold, bronze blade, bronze (metal)
  suit_fa_cloth.png    512 x  512 (2 m): lead-white silk, black silk (cloth)
plus *_n.png normal maps. Prints PASS/FAIL sheet gates (density, value bands, saturation, seam share). Usage: python3 fa_tex.py OUTDIR"""
import sys, os, json
import numpy as np
from PIL import Image
from scipy import ndimage

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/fa_tex'
os.makedirs(OUT, exist_ok=True)

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Random seed (all marks are seeded: the same atlas every run).
SEED = 5105
# Texel density, px per metre (palace and suit studies: 256), and the mask's own density (fine engraving at close-up).
PPM, MASK_PPM = 256, 512
# LOOK (kit per-character look table, values from the research palette and the owner's school mapping, 法 = lead white):
# plate = lead-white lacquer (school colour on the plates: the floor-contrast rule needs a pale exterior), dark = Qin black lacquer
# (helm, seams, gauntlets, boots), trim = gold inlay (rank: the empress's own officer), binding = black silk cord (her court's colour).
PLATE, PLATE_DEEP = '#f2ecdd', '#938c7c'
LACQ, LACQ_LIGHT = '#1b1716', '#3a3230'
GOLD, GOLD_DEEP, GOLD_LIGHT = '#d4b25a', '#7a5f26', '#f0d488'
BRONZE, BRONZE_DEEP = '#b08a4e', '#5e482b'
CORD, CORD_LIGHT = '#151213', '#4a4140'
# Mask: lead white (owner research, 法 = lead white), a touch cooler and brighter than the plates so it reads as its own piece.
MASK, MASK_DEEP = '#f1ede2', '#9a958a'
# Cloth (owner 25 Nov: 法 cloth a brighter, creamier lead white; the lit sheet median x tint was #e5e1ca, kept as the silk median).
SILK_W, SILK_B = '#e5e1ca', '#1e1b1c'
# Lamella: plate width and row height, m (study: 8 cm plates, 12.5 cm rows), seam width px, stud radius px, gold edge line px.
LAM_W, LAM_H, SEAM_PX, STUD_R, EDGE_GOLD = 0.08, 0.125, 1.6, 1.7, 2.2
# Normal map strength (height units -> slope) per atlas; the kit used depth 3.2 on a 0-1 height picture.
DEPTH = {'armour': 3.2, 'metal': 2.6, 'cloth': 1.4}
# Brush/wear variation of a plate's lacquer value (fraction), and how much lacquer pools in cavities (albedo darkening).
WEAR, CAVITY = 0.035, 0.55
# Sheet gates: plate field mean value band (0-255 luma), lacquer band, mask band, saturation caps.
BAND = {'plate': (205, 235), 'lacq': (15, 45), 'mask': (210, 245), 'silk_w': (205, 235), 'silk_b': (15, 45), 'gold': (140, 200)}
SAT_CAP = {'plate': 0.12, 'mask': 0.10, 'lacq': 0.25, 'silk_w': 0.15}
# Rows (px, top to bottom) per atlas and atlas sizes: shared with the builder (art/tools/fa_rows.json).
_R = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fa_rows.json')))
ROWS = {k: {r: tuple(v) for r, v in d.items()} for k, d in _R['rows'].items()}
SIZES = {k: tuple(v) for k, v in _R['sizes'].items()}
rng = np.random.default_rng(SEED)

def hexc(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
def lerp(a, b, t): return a + (b - a) * t[..., None]
def blur(x, s): return ndimage.gaussian_filter(x, s, mode='wrap')
def noise(h, w, s, amp=1.0):
    n = blur(rng.standard_normal((h, w)).astype(np.float32), s); n /= (n.std() + 1e-6); return n * amp

def normal_from_height(hgt, depth):
    # OpenGL convention: +x right, +y up in the image (row 0 = top), +z out
    gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5; gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
    n = np.stack([-gx * depth, gy * depth, np.ones_like(hgt)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return ((n * 0.5 + 0.5) * 255).round().clip(0, 255).astype(np.uint8)

def bevel(dist, w):
    """rounded bevel profile: 0 at the edge, 1 inside past w px."""
    t = np.clip(dist / w, 0, 1); return np.sin(t * np.pi / 2)

# cloud-scroll engraving (云纹): seeded spirals as groove height (deconstructed ornament, no writing) ------------------------------
def scroll_mask(h, w, cx, cy, r, turns=1.6, width=1.1, sign=1):
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); dx, dy = xx - cx, yy - cy
    rr = np.hypot(dx, dy); th = np.arctan2(dy, dx) * sign
    # an Archimedean spiral r = r * phase / (2 pi turns); distance to the nearest arm
    k = r / (2 * np.pi * turns); ph = (th % (2 * np.pi))
    best = np.full((h, w), 1e9, np.float32)
    for n in range(int(turns) + 2):
        rs = k * (ph + 2 * np.pi * n); ok = rs <= r
        best = np.where(ok, np.minimum(best, np.abs(rr - rs)), best)
    return np.clip(1 - best / width, 0, 1) * (rr <= r + width)

# ---------------------------------------------------------------------------------------------------------------------
def lamella_strip(W, H, y0=0.0, ph=None):
    """one lamellar row: plates LAM_W wide, ph px tall starting at row y0 (the builder's vz UVs: 'lam' rows hang down from v 0 with the
    folded lip below; 'lamu' belly rows start with a 3 px lip at the top). Height: plate body with bevels, seams 0, two studs per plate,
    a gold inlay line along the lower edge (a groove filled with gold); above y0 and below the plate: dark lacquer lip."""
    ph = ph or LAM_H * PPM; pw = LAM_W * PPM; n = int(round(W / pw)); pw = W / n
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); yy = yy - y0
    lx = xx % pw; col = (xx // pw).astype(int)
    dl, dr = lx, pw - lx; dt, db = yy, ph - yy
    d = np.minimum(np.minimum(dl, dr) - SEAM_PX / 2, np.minimum(dt, db) - 0.6)
    body = (yy < ph) & (d > 0)
    hgt = np.where(body, 0.35 + 0.65 * bevel(d, 3.0), 0.0).astype(np.float32)
    # each plate slightly convex across, and its top bevel broad (upper edge faces up: catches the sun from above)
    hgt += np.where(body, 0.12 * np.sin(np.clip(lx / pw, 0, 1) * np.pi), 0)
    top = np.clip(1 - dt / (ph * 0.32), 0, 1); hgt -= np.where(body, 0.25 * top ** 1.5, 0)
    # studs: two per plate, near the top
    st = np.zeros_like(hgt)
    for fx in (0.3, 0.7):
        sd = np.hypot(lx - pw * fx, yy - ph * 0.24); st = np.maximum(st, np.clip(1 - sd / STUD_R, 0, 1))
    stud = st > 0.05
    hgt = np.where(stud & body, hgt + 0.35 * np.sqrt(st), hgt)
    # gold inlay line along the lower edge (groove 1 px deep relief)
    gl = body & (db > 2.0) & (db < 2.0 + EDGE_GOLD)
    hgt = np.where(gl, hgt - 0.12, hgt)
    # lip (folded under, below the row): dark lacquer, falls away
    lip = (yy >= ph) | (yy < 0)
    hgt = np.where(lip, 0.15, hgt)
    # albedo
    wear = 1 + noise(H, W, 6, WEAR) + noise(H, W, 1.2, WEAR * 0.4)
    pv = (rng.random(n) - 0.5) * 0.05; wear = wear + pv[col]
    alb = lerp(hexc(PLATE_DEEP), hexc(PLATE), np.clip((0.55 + 0.45 * bevel(d, 2.0)) * wear, 0, 1.06))
    alb = np.where(body[..., None], alb, hexc(LACQ)[None, None])
    alb = np.where((stud & body)[..., None], lerp(hexc(GOLD_DEEP), hexc(GOLD_LIGHT), np.clip(st, 0, 1)), alb)
    alb = np.where(gl[..., None], hexc(GOLD)[None, None], alb)
    alb = np.where(lip[..., None], hexc(LACQ_LIGHT)[None, None] * 0.8, alb)
    kind = np.where(body, np.where(gl | stud, 2, 1), 0)
    return hgt, alb, kind

def plate_field(W, H, scroll=True):
    """big plates (breastplate, pauldron caps, bracers, greaves, horn): lead-white lacquer with fine brush wear and a band of
    cloud-scroll engraving every 25 cm along u (rim zones use the band near the top of the field)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    hgt = 0.6 + noise(H, W, 10, 0.03) + noise(H, W, 2, 0.01)
    if scroll:
        eng = np.zeros((H, W), np.float32); p = 64
        for cx in np.arange(p / 2, W, p):
            for cy, s in ((22, 1), (H - 22, -1)):
                eng = np.maximum(eng, scroll_mask(H, W, cx + (8 if s > 0 else -8), cy, 12, 1.5, 1.0, s))
        hgt -= 0.25 * eng
    wear = 1 + noise(H, W, 5, WEAR) + noise(H, W, 1, WEAR * 0.3)
    alb = lerp(hexc(PLATE_DEEP), hexc(PLATE), np.clip(0.97 * wear, 0, 1.05))
    if scroll: alb = lerp(alb, hexc(GOLD), np.clip(eng * 1.2, 0, 1) * 0.85)
    return hgt.astype(np.float32), alb, np.ones((H, W), int)

def lacquer(W, H, gloss=True):
    hgt = 0.5 + noise(H, W, 8, 0.02)
    v = np.clip(0.5 + noise(H, W, 7, 0.25) + noise(H, W, 1.5, 0.08), 0, 1)
    alb = lerp(hexc(LACQ), hexc(LACQ_LIGHT), v * 0.45)
    return hgt.astype(np.float32), alb, np.zeros((H, W), int)

def cord(W, H):
    """black silk cord: twisted strands (diagonal ridges)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    tw = 0.5 + 0.5 * np.sin((xx + yy * 0.9) * 2 * np.pi / 7.0)
    edge = np.clip(np.minimum(yy, H - 1 - yy) / 4, 0, 1)
    hgt = 0.3 + 0.5 * tw * edge
    alb = lerp(hexc(CORD), hexc(CORD_LIGHT), tw * edge * 0.6)
    return hgt.astype(np.float32), alb, np.zeros((H, W), int)

def mask_field(W, H):
    """mask row: lead white, polished, with cloud-scroll engraving over the brow and cheeks (the shell's planar UVs put the face here at
    MASK_PPM: x -0.15..0.15 m -> u 0..153 px from the row's left, z chin..brow -> v). The rest of the row is plain mask lacquer."""
    hgt = 0.6 + noise(H, W, 8, 0.015)
    eng = np.zeros((H, W), np.float32)
    cx0 = 0.15 * MASK_PPM      # face centre u (px)
    # brow scrolls (both sides, mirrored) and cheek scrolls; rows: v 0 = top of the face window (brow), increases toward the chin
    for m in (1, -1):
        for (fx, fy, r, s) in ((0.075, 0.03, 11, 1), (0.105, 0.115, 9, -1), (0.055, 0.15, 7, 1)):
            eng = np.maximum(eng, scroll_mask(H, W, cx0 + m * fx * MASK_PPM, fy * MASK_PPM, r, 1.4, 1.0, s * m))
    hgt -= 0.3 * eng
    alb = lerp(hexc(MASK_DEEP), hexc(MASK), np.clip(0.98 + noise(H, W, 6, 0.015), 0, 1.03))
    alb = lerp(alb, hexc(GOLD), np.clip(eng * 1.3, 0, 1) * 0.9)
    return hgt.astype(np.float32), alb, np.ones((H, W), int)

def gold_band(W, H, lozenge=True):
    """gold inlay band (plate rims, belt, collar): polished gold with a lozenge (菱纹) groove pattern."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    hgt = 0.6 + noise(H, W, 6, 0.02)
    if lozenge:
        p = H * 1.0; u = (xx % p) / p; v = yy / max(H - 1, 1)
        lz = np.abs(np.abs(u - 0.5) * 2 - v) < 0.09
        hgt = np.where(lz, hgt - 0.3, hgt)
    edge = np.clip(np.minimum(yy, H - 1 - yy) / 2.5, 0, 1); hgt *= 0.6 + 0.4 * edge
    alb = lerp(hexc(GOLD_DEEP), hexc(GOLD), np.clip(0.85 + 0.15 * edge + noise(H, W, 4, 0.04), 0, 1.05))
    if lozenge: alb = np.where(lz[..., None], lerp(hexc(GOLD_DEEP), hexc(GOLD), np.full((H, W), 0.4)), alb)
    return hgt.astype(np.float32), alb, np.full((H, W), 2)

def blade(W, H):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = yy / max(H - 1, 1); ridge = 1 - np.abs(v - 0.5) * 2
    hgt = 0.3 + 0.7 * ridge
    alb = lerp(hexc(BRONZE_DEEP), hexc(GOLD_LIGHT), np.clip(0.35 + 0.6 * ridge + noise(H, W, 5, 0.04), 0, 1))
    return hgt.astype(np.float32), alb, np.full((H, W), 2)

def bronze(W, H):
    hgt = 0.5 + noise(H, W, 5, 0.03)
    alb = lerp(hexc(BRONZE_DEEP), hexc(BRONZE), np.clip(0.8 + noise(H, W, 4, 0.06), 0, 1))
    return hgt.astype(np.float32), alb, np.full((H, W), 2)

def silk(W, H, col, deep):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    weave = 0.5 + 0.25 * np.sin(xx * np.pi) * np.sin(yy * np.pi)
    fold = noise(H, W, 14, 0.5)
    hgt = 0.5 + 0.12 * weave + 0.25 * fold
    alb = lerp(hexc(deep), hexc(col), np.clip(0.93 + 0.05 * fold + 0.02 * weave, 0, 1.04))
    return hgt.astype(np.float32), alb, np.zeros((H, W), int)

def assemble(name, parts):
    W, H, M = SIZES[name]
    hgt = np.zeros((H, W), np.float32); alb = np.zeros((H, W, 3), np.float32)
    for row, (h_, a_, _) in parts.items():
        y0, y1 = ROWS[name][row]; hgt[y0:y1] = h_; alb[y0:y1] = a_
    # cavity: lacquer pools where the height picture dips (seams, grooves, engraving)
    cav = np.clip((ndimage.gaussian_filter(hgt, 1.5) - hgt) * 4, 0, 1)
    alb = alb * (1 - CAVITY * cav[..., None])
    nm = normal_from_height(hgt * (1.0 if name != 'faA' else 1.0), DEPTH[{'faA': 'armour', 'faM': 'metal', 'faC': 'cloth'}[name]])
    Image.fromarray(alb.clip(0, 255).astype(np.uint8)).save(os.path.join(OUT, f'{FILES[name]}.png'))
    Image.fromarray(nm).save(os.path.join(OUT, f'{FILES[name]}_n.png'))
    return alb

FILES = {'faA': 'suit_fa_armour', 'faM': 'suit_fa_metal', 'faC': 'suit_fa_cloth'}

def luma(a): return (a @ np.array([0.299, 0.587, 0.114], np.float32))
def sat(a):
    mx, mn = a.max(-1), a.min(-1); return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)

if __name__ == '__main__':
    A = {'lam': lamella_strip(1024, 40, 0, 34.5), 'lamu': lamella_strip(1024, 40, 3, 32.5), 'plate': plate_field(1024, 256), 'lacq': lacquer(1024, 192), 'cord': cord(1024, 24),
         'mask': mask_field(1024, 256), 'plate2': plate_field(1024, 216, scroll=False)}
    Mt = {'gold': gold_band(512, 32), 'goldp': gold_band(512, 128, lozenge=False), 'blade': blade(512, 64), 'bronze': bronze(512, 128),
          'goldb': gold_band(512, 160, lozenge=False)}
    C = {'silk_w': silk(512, 256, SILK_W, '#a9a492'), 'silk_b': silk(512, 256, SILK_B, '#0c0a0a')}
    aA = assemble('faA', A); aM = assemble('faM', Mt); aC = assemble('faC', C)
    # region ID sheet for the viewer's matid mode (mask-vs-helm measure): mask red, black lacquer green, everything else blue
    W_, H_, _ = SIZES['faA']; idm = np.zeros((H_, W_, 3), np.uint8); idm[..., 2] = 255
    for r_, c_ in (('mask', (255, 0, 0)), ('lacq', (0, 255, 0))):
        y0, y1 = ROWS['faA'][r_]; idm[y0:y1] = c_
    Image.fromarray(idm).save(os.path.join(OUT, f"{FILES['faA']}_id.png"))
    G = []
    def gate(ok, line): G.append(('PASS ' if ok else 'FAIL ') + 'fa_tex ' + line)
    for nm_, (W, H, M) in SIZES.items(): gate(abs(W / M - PPM) < 1e-6, f'{FILES[nm_]} density {W / M:.0f} px/m (study {PPM})')
    def band(a, k):
        lo, hi = BAND[k]; v = float(np.median(luma(a))); return lo <= v <= hi, v
    reg = lambda a, n, r, k=None: a[ROWS[n][r][0]:ROWS[n][r][1]]
    for k, a in (('plate', reg(aA, 'faA', 'plate')), ('lacq', reg(aA, 'faA', 'lacq')), ('mask', reg(aA, 'faA', 'mask')), ('silk_w', reg(aC, 'faC', 'silk_w')),
                 ('silk_b', reg(aC, 'faC', 'silk_b')), ('gold', reg(aM, 'faM', 'goldp'))):
        ok, v = band(a, k); gate(ok, f'{k} median value {v:.0f} (band {BAND[k]})')
        if k in SAT_CAP: s = float(np.median(sat(a / 255))); gate(s <= SAT_CAP[k], f'{k} median saturation {s:.2f} (cap {SAT_CAP[k]})')
    lam = reg(aA, 'faA', 'lam')[:34]; dark = float((luma(lam) < 60).mean()); gold = float((sat(lam / 255) > 0.35).mean())
    gate(0.06 <= dark <= 0.25, f'lamella seams: {dark:.1%} dark (6-25%: plates, seams and bindings told apart)')
    gate(0.03 <= gold <= 0.15, f'lamella gold inlay and studs: {gold:.1%} (3-15%)')
    # mutations: a flat-filled lamella strip (no seams, no inlay) and a black plate field must fail their gates
    flat = np.full_like(lam, hexc(PLATE)); bl = np.full_like(reg(aA, 'faA', 'plate'), hexc(LACQ))
    m1 = not (0.06 <= float((luma(flat) < 60).mean()) <= 0.25); m2 = not band(bl, 'plate')[0]
    G.append(f"MUT {'caught' if m1 else 'MISSED'} fa_tex lamella seams: flat-filled strip"); G.append(f"MUT {'caught' if m2 else 'MISSED'} fa_tex plate value: black plate field")
    for g in G: print(g)
    nf = sum(g.startswith('FAIL') for g in G); ng = sum(g[:4] in ('PASS', 'FAIL') for g in G); print(f'fa_tex {ng - nf} of {ng} pass')
