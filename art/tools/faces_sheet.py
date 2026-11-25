#!/usr/bin/env python3
"""Face masks round 2 (FACES worker): one sheet per character, now and the round-2 mask side by side, labelled.
Row 1: close-up (head and shoulders, 3/4). Row 2: play size at 1:1 pixels (FOV 50, pitch 40, 10.5 m, 1920 x 1080, the 丹 floor).
Row 3: the play-size head at 4x (giant 2x), nearest neighbour, so the owner sees what the pixels are. Triangle counts from the builds.
Usage: python3 faces_sheet.py SHOTDIR STATSDIR OUTDIR
Gates: every shot present and measured (a missing one FAILS); LOD0 and LOD1 triangles within the budget; no material added over now;
play-size contrast mask vs hood/crown and eye vs mask >= CONTRAST_MIN for M and T (now is measured the same way and printed as INFO: the mutation case, a face
in the head's own material, must come out under the line). Probe spots are ticked beside the zoomed head (row 3)."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

SHOT, STATS, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Options in sheet order with their labels.
OPTS_ALL = {'0': 'now (current face)', 'M': 'round 2: sculpted mask', 'T': 'round 2, tin variant (no new material)'}
# Columns per character.
COLS = {'zu': ['0', 'M'], 'g00': ['0', 'M', 'T']}
# Materials allowed over now, per character and option (owner decision pending; printed on the sheet).
EXTRA_OK = {('g00', 'M'): {'palLacquer'}}
# Characters: title, LOD0 meshes, LOD0 budget, LOD1 meshes, LOD1 budget, head crop half-size at play size (px), head zoom.
CHARS = {'zu': ('guard 卒 zu', ['zu_lod0'], 4000, ['zu_lod1'], 1500, 22, 4),
         'g00': ('giant 00', ['giant_body_lod0', 'giant_g00_lod0'], 15000, ['giant_body_lod1', 'giant_g00_lod1'], 3000, 60, 2)}
# Play-size contrast ratio mask vs the surface above it, minimum (palace study 3:1).
CONTRAST_MIN = 3.0
# Close-up cell size, px.
CELL = 420
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
CJK = ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc']


def font(sz, cjk=False):
    for f in (CJK if cjk else []) + [FONT]:
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


shots = json.load(open(os.path.join(SHOT, 'shots.json')))
fails, checks = [], 0
def gate(ok, line):
    global checks
    checks += 1; print(('PASS ' if ok else 'FAIL ') + line)
    if not ok: fails.append(line)

summary = {}
for c, (title, meshes, budget, meshes1, budget1, hh, zoom) in CHARS.items():
    OPTS = [(o, OPTS_ALL[o]) for o in COLS[c]]
    st = {}
    for o, _ in OPTS:
        p = os.path.join(STATS, f'{c}_{o}_stats.json')
        st[o] = json.load(open(p)) if os.path.exists(p) else None
        gate(st[o] is not None, f'{c} {o} build stats present')
    tri = {o: (sum(st[o]['meshes'].get(m, {}).get('tris', 0) for m in meshes) if st[o] else 0) for o, _ in OPTS}
    tri1 = {o: (sum(st[o]['meshes'].get(m, {}).get('tris', 0) for m in meshes1) if st[o] else 0) for o, _ in OPTS}
    mats = {o: sorted({m for k in meshes for m in (st[o]['meshes'].get(k, {}).get('mats', []) if st[o] else [])}) for o, _ in OPTS}
    for o, _ in OPTS:
        if st[o]:
            gate(0 < tri[o] <= budget, f'{c} {o} LOD0 tris {tri[o]} (budget {budget})')
            gate(0 < tri1[o] <= budget1, f'{c} {o} LOD1 tris {tri1[o]} (budget {budget1})')
            ex = EXTRA_OK.get((c, o), set())
            gate(set(mats[o]) <= set(mats['0']) | ex, f"{c} {o} materials {mats[o]} (no new one over now {mats['0']}" + (f"; allowed {sorted(ex)}: +{len(ex)} draw call per unit, owner decision)" if ex else ")"))
            if o != '0': gate(st[o]['face_tris_lod0'] > 0 and len(st[o].get('probes', {})) == 4, f"{c} {o} mask built, {st[o]['face_tris_lod0']} tris at LOD0, probes {sorted(st[o].get('probes', {}))}")
        pr = shots.get(f'{c}_{o}_play', {}).get('probe', {})
        line = f"{c} {o} play contrast mask {pr.get('mask', {}).get('L')} vs above {pr.get('helm', {}).get('L')}: ratio {pr.get('ratio')} (min {CONTRAST_MIN})"
        eline = f"{c} {o} play contrast brighter eye {pr.get('eye', {}).get('L')} vs mask {pr.get('mask', {}).get('L')}: ratio {pr.get('eye_ratio')} (min {CONTRAST_MIN}; shadowed eye {pr.get('eye_shadow_ratio')})"
        if o != '0': gate((pr.get('eye_ratio') or 0) >= CONTRAST_MIN, eline)
        if o == '0': print('INFO ' + line + (' under the line (mutation case caught)' if (pr.get('ratio') or 0) < CONTRAST_MIN else ' NOT under the line'))
        else: gate((pr.get('ratio') or 0) >= CONTRAST_MIN, line)
    # play crop: union of the screen boxes over the options, plus a margin
    bx = [shots.get(f'{c}_{o}_play', {}).get('bbox') for o, _ in OPTS]; bx = [b for b in bx if b]
    gate(len(bx) == len(OPTS), f'{c} play shots measured {len(bx)} of {len(OPTS)}')
    if not bx: continue
    x0 = max(0, min(b[0] for b in bx) - 24); y0 = max(0, min(b[1] for b in bx) - 24); x1 = min(1920, max(b[2] for b in bx) + 24); y1 = min(1080, max(b[3] for b in bx) + 24)
    pw, ph = x1 - x0, y1 - y0
    colw = max(CELL, pw, 2 * hh * zoom)
    W = 30 + len(OPTS) * (colw + 20); Hh = 90 + 40 + CELL + 30 + ph + 30 + 2 * hh * zoom + 80
    sheet = Image.new('RGB', (W, Hh), (24, 20, 26)); d = ImageDraw.Draw(sheet)
    d.text((30, 20), f'{title}: face mask round 2, SAMPLE ONLY (not in the game)', font=font(30, True), fill=(240, 236, 228))
    d.text((30, 58), 'row 1 close-up 3/4 | row 2 play size 1:1 (FOV 50, pitch 40, 10.5 m) | row 3 play-size head x%d nearest (ticks: contrast probes, cyan mask, pink above, yellow eye)' % zoom, font=font(18), fill=(190, 186, 180))
    rec = {}
    for i, (o, lab) in enumerate(OPTS):
        X = 30 + i * (colw + 20); Y = 100
        d.text((X, Y), lab, font=font(24), fill=(250, 220, 150) if o != '0' else (200, 200, 200)); Y += 40
        cp = os.path.join(SHOT, f'{c}_{o}_close.png'); pp = os.path.join(SHOT, f'{c}_{o}_play.png')
        gate(os.path.exists(cp) and os.path.exists(pp), f'{c} {o} close and play shots present')
        if os.path.exists(cp): sheet.paste(Image.open(cp).convert('RGB').resize((CELL, CELL), Image.LANCZOS), (X, Y))
        Y += CELL + 30
        if os.path.exists(pp):
            im = Image.open(pp).convert('RGB'); sheet.paste(im.crop((x0, y0, x1, y1)), (X, Y))
            hx, hy = shots.get(f'{c}_{o}_play', {}).get('head', [0, 0])
            hd = im.crop((hx - hh, hy - hh, hx + hh, hy + hh)).resize((2 * hh * zoom, 2 * hh * zoom), Image.NEAREST)
            sheet.paste(hd, (X, Y + ph + 30))
            for k, colr in (('mask', (80, 220, 255)), ('helm', (255, 120, 220)), ('eye', (255, 235, 60))):
                q = shots.get(f'{c}_{o}_play', {}).get('probe', {}).get(k)
                if q:
                    qx = X + (q['px'][0] - (hx - hh)) * zoom; qy = Y + ph + 30 + (q['px'][1] - (hy - hh)) * zoom
                    d.line((qx - 6 * zoom, qy, qx - 3 * zoom, qy), fill=colr, width=2); d.line((qx + 3 * zoom, qy, qx + 6 * zoom, qy), fill=colr, width=2)
        Y += ph + 30 + 2 * hh * zoom + 10
        dt = tri[o] - tri['0'] if st[o] and st['0'] else 0
        calls = shots.get(f'{c}_{o}_play', {}).get('calls')
        ratio = shots.get(f'{c}_{o}_play', {}).get('probe', {}).get('ratio')
        d.text((X, Y), f'LOD0 {tri[o]:,} tris ({dt:+,} vs now) | LOD1 {tri1[o]:,}', font=font(18), fill=(230, 230, 230))
        d.text((X, Y + 24), f'mask {st[o]["face_tris_lod0"] if st[o] else 0:,} tris | {len(mats[o])} mats | calls {calls} | contrast {ratio}:1, eye {shots.get(f"{c}_{o}_play", {}).get("probe", {}).get("eye_ratio")}:1', font=font(16), fill=(170, 170, 170))
        rec[o] = dict(tris_lod0=tri[o], tris_lod1=tri1[o], delta=dt, face_tris=st[o]['face_tris_lod0'] if st[o] else None, materials=mats[o], calls=calls, contrast=ratio)
    sheet.save(os.path.join(OUT, f'faces_{c}.png')); sheet.convert('RGB').save(os.path.join(OUT, f'faces_{c}.jpg'), quality=90)
    summary[c] = rec
json.dump(summary, open(os.path.join(OUT, 'faces_summary.json'), 'w'), indent=1, ensure_ascii=False)
print(f'{checks - len(fails)} of {checks} pass' + ('' if checks else ' (FAIL: nothing measured)'))
sys.exit(1 if fails or not checks else 0)
