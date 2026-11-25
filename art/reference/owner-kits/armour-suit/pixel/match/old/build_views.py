#!/usr/bin/env python3
"""Front and back views of the knight in the measured style of the reference sprite (64 px frame, 13 colours).
klad does the picture-to-pixels step into the reference's own palette, holds the drawings, draws the outline and checks them.
Run: python3 build_views.py   (after, from ../../3d: python3 ../pixel/match/capture_views.py)"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image

# ---------------- CONFIG: measured from the reference, tune by hand ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F = 64                                   # reference frame: 64 px (it is shown enlarged exactly 6x)
PX_PER_M = 27                            # sprite pixels per metre of the model, so the body is the reference's size
GROUND_ROW = 60                          # feet on this row; the outline sits on row 61, as in the reference
PALETTE = [('ink', '#1b1d2e'), ('steel-1', '#3a4560'), ('steel-2', '#5f6d8c'), ('steel-3', '#8f9db8'), ('steel-4', '#c5cfdd'), ('steel-5', '#f4f7fb'),
           ('brass-1', '#8c5a1e'), ('brass-2', '#d99a2b'), ('brass-3', '#ffd765'), ('cloth-1', '#25503a'), ('cloth-2', '#3f8454'), ('glow-1', '#a8f4ee'), ('leather-1', '#b8403a')]
STEPS = {'steel': ['steel-1', 'steel-2', 'steel-3', 'steel-4', 'steel-5'], 'dark': ['ink', 'steel-1'], 'brass': ['brass-1', 'brass-2', 'brass-3'], 'cloth': ['cloth-1', 'cloth-2'], 'leather': ['leather-1']}
CUTS = {'steel': (15.7, 48.3, 78.6, 96.5), 'dark': (70,), 'brass': (27, 86), 'cloth': (41,), 'leather': ()}   # share of each tone in the reference
SMOOTH = 0.6                             # 0 = raw brightness, 1 = fully averaged with the neighbours
GLOW_COVER = 0.22                        # a pixel becomes a light when this share of it glows in the render
OPEN_ANY = ('steel-4', 'steel-5', 'brass-3', 'glow-1')   # no outline beside these light tones, on any side (the reference's outline is dark on 58% of its edge)
OPEN_LIT = ('steel-3', 'brass-2')        # and none beside these on the lit side (left and top)
VIEWS = ['side', 'front', 'back']        # side is made only to compare against the reference
# -------------------------------------------------------
def run(*a): return subprocess.run([K, *a], capture_output=True, text=True)
proj = json.load(open('cap/proj.json'))
def cut(name):
    ox, oy, ppm = proj[name]; s = PX_PER_M / ppm; x0 = ox - (F / 2) / s; y0 = oy - (GROUND_ROW + 1) / s; side = F / s; pad = 300
    flat = np.array(Image.open(f'cap/{name}_flat.png').convert('RGB')); ref = np.array(Image.open(f'cap/{name}_ref.png').convert('RGB')); v = flat.astype(int)
    fg = ~((v[..., 0] - v[..., 1] > 80) & (v[..., 2] - v[..., 1] > 80) & (v[..., 0] > 150) & (v[..., 2] > 150))
    p = np.pad(fg, 2); core = fg & p[:-4, 2:-2] & p[4:, 2:-2] & p[2:-2, :-4] & p[2:-2, 4:]; out = []
    for rgb, m in ((flat, core), (ref, fg)):
        im = Image.fromarray(np.pad(np.dstack([rgb, (m * 255).astype(np.uint8)]), ((pad, pad), (pad, pad), (0, 0))), 'RGBA')
        out.append(im.resize((F * 8, F * 8), Image.BOX, box=(x0 + pad, y0 + pad, x0 + pad + side, y0 + pad + side)))
    return out
def nb(a, y, x): return [a[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy) and 0 <= y + dy < F and 0 <= x + dx < F and a[y + dy, x + dx]]
FAM = {'steel': 'steel', 'ink': 'dark', 'brass': 'brass', 'cloth': 'cloth', 'glow': 'steel', 'leather': 'leather'}
def finish(grid, ref, cuts):
    lines = grid.split('\n'); k = lines.index('')
    legend = {l.split(' = ')[0]: l.split(' = ')[1].split()[0] for l in lines[:k] if ' = ' in l}
    fam = np.array([['' if c == '.' else FAM[legend[c].split('-')[0]] for c in r] for r in lines[k + 1:] if r], dtype='<U8')
    for _ in range(2):                    # a single pixel of a material joins its neighbours (brass and leather details stay)
        new = fam.copy()
        for y in range(F):
            for x in range(F):
                if not fam[y, x] or fam[y, x] in ('brass', 'leather'): continue
                n = nb(fam, y, x)
                if n and n.count(fam[y, x]) == 0: new[y, x] = max(set(n), key=n.count)
        fam = new
    r = np.array(ref).astype(np.float32); a = r[..., 3] / 255; lum = 0.3 * r[..., 0] + 0.59 * r[..., 1] + 0.11 * r[..., 2]
    box = lambda v: np.array(Image.fromarray(v.astype(np.float32), 'F').resize((F, F), Image.BOX))
    L = box(lum * a) / np.maximum(box(a), 1e-3); Ls = L.copy()
    for y in range(F):
        for x in range(F):
            if not fam[y, x]: continue
            v = [L[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= y + dy < F and 0 <= x + dx < F and fam[y + dy, x + dx] == fam[y, x]]
            Ls[y, x] = (1 - SMOOTH) * L[y, x] + SMOOTH * float(np.mean(v))
    if cuts is None: cuts = {f: [float(c) for c in np.percentile(Ls[fam == f], CUTS[f])] if (fam == f).any() and CUTS[f] else [] for f in STEPS}
    g = np.full((F, F), '', dtype='<U12')
    for f, names in STEPS.items():
        for y, x in zip(*np.nonzero(fam == f)): g[y, x] = names[sum(Ls[y, x] > t for t in cuts[f])]
    new = g.copy()                        # one pass: a pixel with no side neighbour of its colour joins the majority around it
    for y in range(F):
        for x in range(F):
            if not g[y, x] or g[y, x].startswith(('brass', 'leather')): continue
            if any(0 <= y + dy < F and 0 <= x + dx < F and g[y + dy, x + dx] == g[y, x] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): continue
            n = nb(g, y, x)
            if n: new[y, x] = max(set(n), key=n.count)
    g = new
    cov = box(((np.minimum(r[..., 1], r[..., 2]) - r[..., 0] > 18) & (r[..., 1] > 190) & (r[..., 2] > 190) & (r[..., 3] > 0)).astype(np.float32))
    for y in range(F):
        for x in range(F):
            if cov[y, x] >= GLOW_COVER and g[y, x]: g[y, x] = 'glow-1'
    names = sorted({n for n in g.flatten() if n}); chars = 'abcdefghijklmnopqrstuvwxyz'; code = {n: chars[i] for i, n in enumerate(names)}
    return '\n'.join(f'{code[n]} = {n}' for n in names) + '\n\n' + '\n'.join(''.join(code[g[y, x]] if g[y, x] else '.' for x in range(F)) for y in range(F)) + '\n', cuts, g
def template(path):
    shutil.rmtree(path, ignore_errors=True); run('new', path, '--pixel', f'{F}x{F}')
    for n, h in PALETTE: run('palette', path, '--add', h, '--name', n)
cuts = None
for v in VIEWS:
    flat, ref = cut(v); flat.save('tmp/flat.png'); template('tmp/m.klad')
    run('pixelize', 'tmp/m.klad', '--image', 'tmp/flat.png', '--to', 'l1', '--size', str(F), '--at', '0,0')
    grid, cuts, g = finish(run('pixels', 'tmp/m.klad', 'l1', '--plain').stdout, ref, cuts); open(f'tmp/{v}.grid', 'w').write(grid)
    b = f'out/knight_{v}.klad'; template(b)
    a = run('pixel', b, 'l1', '--grid', f'tmp/{v}.grid'); o = run('pixel', b, 'l1', '--color', 'ink', '--outline')
    if a.returncode or o.returncode: print('klad error', v, (a.stderr or o.stderr)[:300]); sys.exit(1)
    cells = []                            # leave the outline open where light hits, as measured on the reference
    for y in range(F):
        for x in range(F):
            if g[y, x]: continue
            n4 = {d: (g[y + dy, x + dx] if 0 <= y + dy < F and 0 <= x + dx < F else '') for d, (dx, dy) in {'right': (1, 0), 'below': (0, 1), 'left': (-1, 0), 'above': (0, -1)}.items()}
            touching = [v for v in n4.values() if v]
            if not touching: continue
            lit_side = all(v in OPEN_ANY or (v in OPEN_LIT and d in ('right', 'below')) for d, v in n4.items() if v)
            if lit_side: cells.append(f'{x},{y}')
    if cells: run('pixel', b, 'l1', '--erase', '--cells', ' '.join(cells))
    run('export', b, '--scale', '1', '-o', f'out/knight_{v}_1x.png'); run('export', b, '--scale', '6', '-o', f'out/knight_{v}_6x.png')
    print(v, run('check', b).stdout.split('\n')[0])
