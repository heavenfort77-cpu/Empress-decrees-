#!/usr/bin/env python3
"""Animate klad knight 2b: every frame is made the way 2b was made.
For each captured frame: cut the figure out at a fixed scale and ground line, let klad pixelise the flat capture into the
sprite's palette (materials), take light and shade from the full render, put the lights back, write the frame into a klad
animation, outline it, clear doubled corners, check, then export GIFs and sprite sheets.
Run: python3 build_anim.py   (after ../../3d: python3 ../pixel/anim/capture.py)"""
import json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image

# ---------------- CONFIG: tune by hand ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F = 96                                  # sprite frame in px
PX_PER_M = 38                           # sprite pixels per metre of the model (the knight is about 1.95 m: 74 px; the raised sword reaches about 86 px)
GROUND_ROW = 91                         # the feet stand on this row in every frame
FPS = 8
ANIMS = [('idle', 4), ('walk_left', 6), ('walk_right', 6), ('battle', 1)]
RAMPS = [('steel', '#8f99a6', 5), ('gun', '#3e4550', 3), ('brass', '#b8923e', 4), ('cloth', '#2f4a33', 3), ('leather', '#8a2f24', 2), ('glow', '#5fe6f0', 2)]
CUTS = {5: (7, 22, 46, 76), 4: (15, 42, 75), 3: (30, 72), 2: (50,)}   # brightness percentiles where a ramp steps up (measured once, on idle frame 0)
SMOOTH = 0.72                           # 0 = raw brightness, 1 = fully averaged with the neighbours
GLOW_COVER = 0.2                        # a pixel becomes a light when this share of it glows in the render
SMALL = 5                               # cloth or leather patches smaller than this many pixels are noise
# -------------------------------------------------------
def run(*a, inp=None): return subprocess.run([K, *a], capture_output=True, text=True, input=inp)
proj = json.load(open('cap/proj.json'))

def cut(name):
    """Both captures as 768 px RGBA pictures that line up with the 96 px frame (8 screen samples per sprite pixel)."""
    ox, oy, ppm = proj[name]; s = PX_PER_M / ppm; x0 = ox - (F / 2) / s; y0 = oy - (GROUND_ROW + 1) / s; side = F / s; pad = 200
    flat = np.array(Image.open(f'cap/{name}_flat.png').convert('RGB')); ref = np.array(Image.open(f'cap/{name}_ref.png').convert('RGB')); v = flat.astype(int)
    fg = ~((v[..., 0] - v[..., 1] > 80) & (v[..., 2] - v[..., 1] > 80) & (v[..., 0] > 150) & (v[..., 2] > 150))
    p = np.pad(fg, 2); core = fg & p[:-4, 2:-2] & p[4:, 2:-2] & p[2:-2, :-4] & p[2:-2, 4:]
    out = []
    for rgb, m in ((flat, core), (ref, fg)):
        im = Image.fromarray(np.pad(np.dstack([rgb, (m * 255).astype(np.uint8)]), ((pad, pad), (pad, pad), (0, 0))), 'RGBA')
        out.append(im.resize((F * 8, F * 8), Image.BOX, box=(x0 + pad, y0 + pad, x0 + pad + side, y0 + pad + side)))
    return out

def nb(a, y, x): return [a[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dx or dy) and 0 <= y + dy < F and 0 <= x + dx < F and a[y + dy, x + dx]]

def finish(grid, ref, cuts):
    lines = grid.split('\n'); k = lines.index('')
    legend = {l.split(' = ')[0]: l.split(' = ')[1].split()[0] for l in lines[:k] if ' = ' in l}
    rows = [r for r in lines[k + 1:] if r]
    fam = np.array([['' if c == '.' else legend[c].split('-')[0] for c in r] for r in rows], dtype='<U8')
    fam[fam == 'ink'] = 'gun'; fam[fam == 'glow'] = 'steel'
    for f in ('cloth', 'leather'):       # small patches of cloth or leather are colours that only snapped there by accident
        seen = np.zeros((F, F), bool)
        for y, x in zip(*np.nonzero(fam == f)):
            if seen[y, x]: continue
            comp = [(y, x)]; seen[y, x] = True; q = [(y, x)]
            while q:
                cy, cx = q.pop()
                for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    yy, xx = cy + dy, cx + dx
                    if 0 <= yy < F and 0 <= xx < F and fam[yy, xx] == f and not seen[yy, xx]: seen[yy, xx] = True; comp.append((yy, xx)); q.append((yy, xx))
            if len(comp) < SMALL:
                for cy, cx in comp:
                    n = [v for v in nb(fam, cy, cx) if v not in ('cloth', 'leather')]; fam[cy, cx] = max(set(n), key=n.count) if n else 'steel'
    for _ in range(2):                   # a single pixel of a material joins its neighbours (brass trim lines stay)
        new = fam.copy()
        for y in range(F):
            for x in range(F):
                if not fam[y, x] or fam[y, x] == 'brass': continue
                n = nb(fam, y, x)
                if n and n.count(fam[y, x]) == 0: new[y, x] = max(set(n), key=n.count)
        fam = new
    r = np.array(ref).astype(np.float32); a = r[..., 3] / 255; lum = 0.3 * r[..., 0] + 0.59 * r[..., 1] + 0.11 * r[..., 2]
    box = lambda v: np.array(Image.fromarray(v.astype(np.float32), 'F').resize((F, F), Image.BOX))
    L = box(lum * a) / np.maximum(box(a), 1e-3); solid = fam != ''; Ls = L.copy()
    for y in range(F):
        for x in range(F):
            if not solid[y, x]: continue
            v = [L[y + dy, x + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1) if 0 <= y + dy < F and 0 <= x + dx < F and fam[y + dy, x + dx] == fam[y, x]]
            Ls[y, x] = (1 - SMOOTH) * L[y, x] + SMOOTH * float(np.mean(v))
    steps = {f: n for f, _, n in RAMPS if f != 'glow'}
    if cuts is None: cuts = {f: [float(c) for c in np.percentile(Ls[fam == f], CUTS[n])] for f, n in steps.items() if (fam == f).any()}
    g = np.full((F, F), '', dtype='<U12')
    for f, n in steps.items():
        c = cuts.get(f) or [80.0 * (i + 1) / n for i in range(n - 1)]
        for y, x in zip(*np.nonzero(fam == f)): g[y, x] = f'{f}-{1 + sum(Ls[y, x] > t for t in c)}'
    for _ in range(3):                   # merge single stray pixels into their neighbours
        new = g.copy()
        for y in range(F):
            for x in range(F):
                if not g[y, x]: continue
                if any(0 <= y + dy < F and 0 <= x + dx < F and g[y + dy, x + dx] == g[y, x] for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0))): continue
                n = [v for v in nb(g, y, x) if v.split('-')[0] == g[y, x].split('-')[0]] or nb(g, y, x)
                if n: new[y, x] = max(set(n), key=n.count)
        g = new
    cov = box(((np.minimum(r[..., 1], r[..., 2]) - r[..., 0] > 18) & (r[..., 1] > 190) & (r[..., 2] > 190) & (r[..., 3] > 0)).astype(np.float32))
    for y in range(F):
        for x in range(F):
            if cov[y, x] >= GLOW_COVER and g[y, x]: g[y, x] = 'glow-2' if cov[y, x] >= 0.45 else 'glow-1'
    names = sorted({n for n in g.flatten() if n}); chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGH'; code = {n: chars[i] for i, n in enumerate(names)}
    return '\n'.join(f'{code[n]} = {n}' for n in names) + '\n\n' + '\n'.join(''.join(code[g[y, x]] if g[y, x] else '.' for x in range(F)) for y in range(F)) + '\n', cuts

def template(path, frames=1):
    shutil.rmtree(path, ignore_errors=True); run('new', path, '--pixel', f'{F}x{F}', '--frames', str(frames), '--fps', str(FPS))
    run('palette', path, '--add', '#14161c', '--name', 'ink')
    for n, base, steps in RAMPS: run('palette', path, '--ramp', n, '--base', base, '--steps', str(steps))

os.makedirs('out', exist_ok=True); os.makedirs('tmp', exist_ok=True); cuts = None; report = []
for anim, n in ANIMS:
    bundle = f'out/{anim}.klad'; template(bundle, n)
    for i in range(n):
        flat, ref = cut(f'{anim}_{i}'); flat.save('tmp/flat.png')
        template('tmp/m.klad'); r = run('pixelize', 'tmp/m.klad', '--image', 'tmp/flat.png', '--to', 'l1', '--size', str(F), '--at', '0,0')
        grid, cuts = finish(run('pixels', 'tmp/m.klad', 'l1', '--plain').stdout, ref, cuts)
        open(f'tmp/{anim}_{i}.grid', 'w').write(grid)
        if i: run('add', bundle, 'cel', '--in', 'l1', f'frame={i}')
        a = run('pixel', bundle, 'l1', '--frame', str(i), '--grid', f'tmp/{anim}_{i}.grid'); b = run('pixel', bundle, 'l1', '--frame', str(i), '--color', 'ink', '--outline')
        if a.returncode or b.returncode: print('klad error', anim, i, (a.stderr or b.stderr)[:300]); sys.exit(1)
        for _ in range(6):               # doubled corners in the outline
            f = json.loads(run('check', bundle, '--frame', str(i), '--json').stdout)['findings']
            c = [x['at'] for x in f if x['kind'] == 'corner' and x['color'] == 'ink']
            if not c: break
            run('pixel', bundle, 'l1', '--frame', str(i), '--erase', '--cells', ' '.join(f'{x},{y}' for x, y in c))
        kinds = {}
        for x in json.loads(run('check', bundle, '--frame', str(i), '--json').stdout)['findings']: kinds[x['kind']] = kinds.get(x['kind'], 0) + 1
        report.append((anim, i, kinds))
        run('export', bundle, '--frame', str(i), '--scale', '1', '-o', f'out/{anim}_{i}.png')
    if n > 1: e = run('export', bundle, '--gif', 'all', '--scale', '3', '-o', f'out/{anim}_3x.gif'); print(anim, 'gif:', (e.stdout + e.stderr).strip()[:120])
for anim, i, kinds in report: print(f'{anim}_{i} klad check:', kinds or 'nothing to look at')
