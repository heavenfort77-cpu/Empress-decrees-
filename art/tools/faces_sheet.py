#!/usr/bin/env python3
"""Face options sample (FACES worker): one sheet per character, options side by side (now, A, B, C, D), labelled.
Row 1: close-up (head and shoulders, 3/4). Row 2: play size at 1:1 pixels (FOV 50, pitch 40, 10.5 m, 1920 x 1080, the 丹 floor).
Row 3: the play-size head at 4x (giant 2x), nearest neighbour, so the owner sees what the pixels are. Triangle counts from the builds.
Usage: python3 faces_sheet.py SHOTDIR STATSDIR OUTDIR
Gates: every shot present and measured (a missing one FAILS), painted options have face UVs, LOD0 triangles within the budget."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

SHOT, STATS, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)
# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Options in sheet order with their labels.
OPTS = [('0', 'now (current face)'), ('A', 'A  bronze war mask'), ('B', 'B  closed visor'), ('C', 'C  painted face'), ('D', 'D  lacquer mask')]
# Characters: title, LOD0 mesh names counted, LOD0 triangle budget, head crop half-size at play size (px), head zoom.
CHARS = {'fa': ('suit 法 fa (法甲 廷尉)', ['fa_lod0'], 15000, 30, 4),
         'zu': ('guard 卒 zu', ['zu_lod0'], 4000, 22, 4),
         'g00': ('giant 00', ['giant_body_lod0', 'giant_g00_lod0'], 15000, 60, 2)}
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
for c, (title, meshes, budget, hh, zoom) in CHARS.items():
    st = {}
    for o, _ in OPTS:
        p = os.path.join(STATS, f'{c}_{o}_stats.json')
        st[o] = json.load(open(p)) if os.path.exists(p) else None
        gate(st[o] is not None, f'{c} {o} build stats present')
    tri = {o: (sum(st[o]['meshes'].get(m, {}).get('tris', 0) for m in meshes) if st[o] else 0) for o, _ in OPTS}
    for o, _ in OPTS:
        if st[o]:
            gate(0 < tri[o] <= budget, f'{c} {o} LOD0 tris {tri[o]} (budget {budget})')
            if o in ('C', 'D'): gate(st[o]['uv_fixed_polys'] > 0, f"{c} {o} painted face polygons projected {st[o]['uv_fixed_polys']} (> 0)")
            if o != '0': gate(st[o]['face_tris_lod0'] > 0, f"{c} {o} face parts built, {st[o]['face_tris_lod0']} tris at LOD0")
    # play crop: union of the screen boxes over the options, plus a margin
    bx = [shots.get(f'{c}_{o}_play', {}).get('bbox') for o, _ in OPTS]; bx = [b for b in bx if b]
    gate(len(bx) == len(OPTS), f'{c} play shots measured {len(bx)} of {len(OPTS)}')
    if not bx: continue
    x0 = max(0, min(b[0] for b in bx) - 24); y0 = max(0, min(b[1] for b in bx) - 24); x1 = min(1920, max(b[2] for b in bx) + 24); y1 = min(1080, max(b[3] for b in bx) + 24)
    pw, ph = x1 - x0, y1 - y0
    colw = max(CELL, pw, 2 * hh * zoom)
    W = 30 + len(OPTS) * (colw + 20); Hh = 90 + 40 + CELL + 30 + ph + 30 + 2 * hh * zoom + 80
    sheet = Image.new('RGB', (W, Hh), (24, 20, 26)); d = ImageDraw.Draw(sheet)
    d.text((30, 20), f'{title}: face options, SAMPLE ONLY (not in the game)', font=font(30, True), fill=(240, 236, 228))
    d.text((30, 58), 'row 1 close-up 3/4 | row 2 play size 1:1 (FOV 50, pitch 40, 10.5 m) | row 3 play-size head x%d nearest' % zoom, font=font(18), fill=(190, 186, 180))
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
        Y += ph + 30 + 2 * hh * zoom + 10
        dt = tri[o] - tri['0'] if st[o] and st['0'] else 0
        calls = shots.get(f'{c}_{o}_play', {}).get('calls')
        mats = sorted({m for k in meshes for m in (st[o]['meshes'].get(k, {}).get('mats', []) if st[o] else [])})
        d.text((X, Y), f'LOD0 {tri[o]:,} tris ({dt:+,} vs now)', font=font(18), fill=(230, 230, 230))
        d.text((X, Y + 24), f'face parts {st[o]["face_tris_lod0"] if st[o] else 0:,} tris | {len(mats)} materials | draw calls {calls}', font=font(16), fill=(170, 170, 170))
        rec[o] = dict(tris_lod0=tri[o], delta=dt, face_tris=st[o]['face_tris_lod0'] if st[o] else None, materials=mats, calls=calls)
    sheet.save(os.path.join(OUT, f'faces_{c}.png')); sheet.convert('RGB').save(os.path.join(OUT, f'faces_{c}.jpg'), quality=90)
    summary[c] = rec
json.dump(summary, open(os.path.join(OUT, 'faces_summary.json'), 'w'), indent=1, ensure_ascii=False)
print(f'{checks - len(fails)} of {checks} pass' + ('' if checks else ' (FAIL: nothing measured)'))
sys.exit(1 if fails or not checks else 0)
