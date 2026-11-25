#!/usr/bin/env python3
"""Suit colour gates (owner 25 Nov: recolour the nine suits to the ONE school colour mapping). Art tool, not shipped.
1. cloth: per suit, the cloth albedo median (GLB material tint x suit_cloth sheet, linear) within dE 10 of the school colour;
2. floor: on the lineup at play size over the red hall floor (game lights), each suit's cloth median (masks from the clothid render),
   every school pair at least dE 10 apart;
3. cords: each school's cord row on suit_lamellar (centre band median) within RGB 50 (tex_check) and dE 10 of the school colour;
4. sheet: suit_lamellar outside the cord rows, suit_cloth and suit_bronze byte-identical to the approved sheets.
--mutate: za tint set to fa's (gate 1), the shot with za's tint copied from fa (gate 2), za's cord row copied from fa's (gate 3), one pixel
outside the cord rows changed (gate 4); each must fail. dE = CIE76 (as accent_check.py and standard_check.py).
Usage: python3 suit_colour_check.py GLBDIR TEXDIR APPROVED_TEXDIR SHOTDIR [--mutate]"""
import sys, os, json, struct, itertools
import numpy as np
from PIL import Image

# CONFIG -----------------------------------------------------------------------------------------------------------------
# School colours (owner's one mapping: W1a 鼎 pigments; 儒 #94622c and 杂 #b2bccb as on banners and effects), lineup order.
SCHOOL = {'fa': '#d9d2c3', 'ru': '#94622c', 'dao': '#e2b84a', 'mo': '#a8321e', 'yy': '#1a1614', 'za': '#b2bccb', 'ming': '#5b3f8c', 'zh': '#2f8a5c', 'nong': '#2e5a9c'}
IDS = list(SCHOOL)
# Max dE of a suit's cloth albedo median from its school colour.
CLOTH_DE = 10.0
# Min dE between any two suits' lit cloth medians on the red floor at play size.
PAIR_DE = 10.0
# Max RGB distance of a cord row's centre median from its school colour (tex_check.py CORD_DIST).
CORD_DIST = 50.0
# ... and within this dE of it (lead 25 Nov: tighter, RGB 50 could not tell fa's lead white from za's silver; run 45525874094 mutant).
CORD_DE = 10.0
# Cord rows: first row y, row height, school order (suit_tex.py).
CORD_Y0, CORD_H, CORD_ORDER = 736, 32, ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong']
# Mask pixels per suit needed for a lit median (after a 1 px erosion), and the ID colour tolerance (RGB, max channel).
MIN_PX, ID_TOL = 30, 24

G, T, A, S = sys.argv[1:5]; MUT = '--mutate' in sys.argv
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
srgb = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 0, None), 1 / 2.4) - 0.055)
hexrgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float) / 255
def lab(rgb01):
    r = lin(np.asarray(rgb01, float)); X = (0.4124 * r[0] + 0.3576 * r[1] + 0.1805 * r[2]) / 0.95047; Y = 0.2126 * r[0] + 0.7152 * r[1] + 0.0722 * r[2]
    Z = (0.0193 * r[0] + 0.1192 * r[1] + 0.9505 * r[2]) / 1.08883; f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return np.array([116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z))])
dE = lambda a, b: float(np.linalg.norm(lab(a) - lab(b)))
def tint(sid):
    b = open(os.path.join(G, sid + '.glb'), 'rb').read(); n = struct.unpack('<I', b[12:16])[0]; j = json.loads(b[20:20 + n])
    m = [x for x in j['materials'] if x['name'] == 'sCloth_' + sid][0]; return np.array(m['pbrMetallicRoughness'].get('baseColorFactor', [1, 1, 1, 1])[:3])
cloth_med = np.median(lin(np.asarray(Image.open(os.path.join(T, 'suit_cloth.png')).convert('RGB')).astype(float) / 255).reshape(-1, 3), 0)

def g_cloth(tints):
    out = []
    for sid in IDS:
        alb = srgb(tints[sid] * cloth_med); d = dE(alb, hexrgb(SCHOOL[sid]))
        out.append((d <= CLOTH_DE, f'{sid} cloth albedo median #{"".join(f"{int(round(x * 255)):02x}" for x in alb)} vs school {SCHOOL[sid]}: dE {d:.1f} (max {CLOTH_DE})'))
    return out
def lit_medians(shot, idimg):
    img = np.asarray(Image.open(shot).convert('RGB')).astype(float) / 255; ids = np.asarray(Image.open(idimg).convert('RGB')).astype(float)
    med = {}
    for i, sid in enumerate(IDS):
        c = np.array([int(round(x * 255)) for x in __import__('colorsys').hls_to_rgb((i * 40) / 360, 0.5, 1.0)], float)
        m0 = np.abs(ids - c).max(2) <= ID_TOL; m = m0.copy(); m[1:-1, 1:-1] &= m0[:-2, 1:-1] & m0[2:, 1:-1] & m0[1:-1, :-2] & m0[1:-1, 2:]; m[[0, -1], :] = False; m[:, [0, -1]] = False   # 1 px erosion (no scipy on the runner)
        med[sid] = (np.median(img[m], 0) if m.sum() >= MIN_PX else None, int(m.sum()))
    return med
def g_pairs(med):
    out = []; worst = (1e9, '')
    for sid in IDS:
        if med[sid][0] is None: out.append((False, f'{sid} lit cloth: only {med[sid][1]} mask pixels (min {MIN_PX})'))
    ok = [s for s in IDS if med[s][0] is not None]
    for a, b in itertools.combinations(ok, 2):
        d = dE(med[a][0], med[b][0]); worst = min(worst, (d, f'{a}-{b}'))
        if d < PAIR_DE: out.append((False, f'floor pair {a}-{b}: dE {d:.1f} (min {PAIR_DE})'))
    out.append((worst[0] >= PAIR_DE and len(ok) == len(IDS), f'floor pairs: closest {worst[1]} dE {worst[0]:.1f} (min {PAIR_DE}); lit medians ' +
                ' '.join(f'{s} #{"".join(f"{int(round(x * 255)):02x}" for x in med[s][0])}({med[s][1]}px)' for s in ok)))
    return out
def g_cords(L):
    out = []
    for i, sid in enumerate(CORD_ORDER):
        y = CORD_Y0 + CORD_H * i; med = np.median(L[y + 10:y + 22].reshape(-1, 3), 0); want = hexrgb(SCHOOL[sid]) * 255; dist = np.linalg.norm(med - want)
        d = dE(med / 255, want / 255)
        out.append((dist <= CORD_DIST and d <= CORD_DE, f'cord {sid} median #{"".join(f"{int(x):02x}" for x in med)} vs {SCHOOL[sid]}: RGB distance {dist:.0f} (max {CORD_DIST:.0f}), dE {d:.1f} (max {CORD_DE:.0f})'))
    return out
def g_sheets(L):
    out = []; L0 = np.asarray(Image.open(os.path.join(A, 'suit_lamellar.png')).convert('RGB'))
    n = int((L[:CORD_Y0] != L0[:CORD_Y0]).any(2).sum()); out.append((n == 0, f'suit_lamellar outside the cord rows: {n} pixels differ from the approved sheet'))
    for f in ('suit_cloth.png', 'suit_bronze.png'):
        same = open(os.path.join(T, f), 'rb').read() == open(os.path.join(A, f), 'rb').read(); out.append((same, f'{f} byte-identical to the approved sheet: {same}'))
    return out

tints = {sid: tint(sid) for sid in IDS}
Lam = np.asarray(Image.open(os.path.join(T, 'suit_lamellar.png')).convert('RGB'))
# lead RULE: gates that measure nothing fail (9 tints, a 1024 px sheet with all cord rows, a non-empty cloth sheet)
pre = [(len(tints) == len(IDS), f'{len(tints)} cloth tints read (9 needed)'), (Lam.shape[0] >= CORD_Y0 + CORD_H * len(CORD_ORDER), f'suit_lamellar {Lam.shape[0]} px tall (cord rows need {CORD_Y0 + CORD_H * len(CORD_ORDER)})'),
       (bool(np.isfinite(cloth_med).all()), 'cloth sheet median measured')]
res = [('inputs', pre), ('cloth', g_cloth(tints)), ('floor', g_pairs(lit_medians(os.path.join(S, 'lineup_colour.png'), os.path.join(S, 'lineup_clothid.png')))),
       ('cords', g_cords(Lam)), ('sheets', g_sheets(Lam))]
allr = [r for _, rs in res for r in rs]
for _, rs in res:
    for ok, line in rs: print(('PASS ' if ok else 'FAIL ') + line)
print(f'{sum(ok for ok, _ in allr)} of {len(allr)} pass')
if MUT:
    caught = []
    t2 = dict(tints); t2['za'] = tints['fa']; caught.append(('cloth', 'za tint = fa tint', not all(ok for ok, _ in g_cloth(t2))))
    mp = os.path.join(S, 'lineup_colour_mut.png')   # lead RULE: a missing mutant target is MISSED
    caught.append(('floor', 'shot with za cloth tinted as fa' + ('' if os.path.exists(mp) else ' (target missing)'),
                   os.path.exists(mp) and not all(ok for ok, _ in g_pairs(lit_medians(mp, os.path.join(S, 'lineup_clothid.png'))))))
    L2 = Lam.copy(); i_fa, i_za = CORD_ORDER.index('fa'), CORD_ORDER.index('za'); L2[CORD_Y0 + CORD_H * i_za:CORD_Y0 + CORD_H * (i_za + 1)] = Lam[CORD_Y0 + CORD_H * i_fa:CORD_Y0 + CORD_H * (i_fa + 1)]
    caught.append(('cords', 'za cord row copied from fa', not all(ok for ok, _ in g_cords(L2))))
    L3 = Lam.copy(); L3[10, 10] = (L3[10, 10].astype(int) + 40) % 256; caught.append(('sheets', 'one pixel outside the cord rows changed', not all(ok for ok, _ in g_sheets(L3))))
    for g, what, c in caught: print(f"MUT {'caught' if c else 'MISSED'} {g}: {what}")
    print(f'colour mutations {sum(c for *_, c in caught)} of {len(caught)} caught')
