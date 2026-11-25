#!/usr/bin/env python3
"""Front and back views of the knight, drawn as planned pixel art in the measured style of the reference sprite,
then held, outlined, checked and exported by klad.
Style rules read off the reference (64 px frame, 13 colours): every plate is its own shape with a dark line round it;
light runs left to right across a plate in three flat bands (light, mid, dark); the bottom row of a plate is its dark
tone; a short highlight sits on the top row near the light; lower plates use the next darker set of tones.
Run: python3 draw_views.py"""
import os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw

# ---------------- CONFIG: measured from the reference, tune by hand ----------------
K = os.environ.get('KLAD', '/home/claude/klad/src/target/linux/release/klad')
F = 64
PALETTE = [('ink', '#1b1d2e'), ('steel-1', '#3a4560'), ('steel-2', '#5f6d8c'), ('steel-3', '#8f9db8'), ('steel-4', '#c5cfdd'), ('steel-5', '#f4f7fb'),
           ('brass-1', '#8c5a1e'), ('brass-2', '#d99a2b'), ('brass-3', '#ffd765'), ('cloth-1', '#25503a'), ('cloth-2', '#3f8454'), ('glow-1', '#a8f4ee'), ('leather-1', '#b8403a')]
STEEL = ['steel-5', 'steel-4', 'steel-3', 'steel-2', 'steel-1']       # highlight, then light to dark
BANDS = (0.45, 0.8)          # across a plate: light up to here, mid up to here, dark after
HILITE = (0.12, 0.42)        # the highlight run on a plate's top row
FAR_SIDE = 1                 # plates on the side away from the light use tones this many steps darker
# -------------------------------------------------------
def R(x0, y0, x1, y1): return ('rect', x0, y0, x1, y1)
def rast(shape):
    im = Image.new('L', (F, F), 0); d = ImageDraw.Draw(im)
    d.rectangle(shape[1:], fill=255) if isinstance(shape, tuple) else d.polygon(shape, fill=255)
    return np.array(im) > 0
def draw(parts):
    g = np.full((F, F), '', dtype='<U12')
    def put(mask, mat, opt):
        if not mask.any(): return
        if 'noline' not in opt:                                # a dark line round the plate, where it lies on other plates
            p = np.pad(mask, 1); ring = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]) & ~mask
            g[ring & (g != '')] = 'ink'
        ys, xs = np.nonzero(mask); x0, x1, y0 = xs.min(), xs.max(), ys.min(); s = opt.get('shift', 0)
        for y, x in zip(ys, xs):
            t = (x - x0) / (x1 - x0 + 1); bottom = y + 1 >= F or not mask[y + 1, x]
            if mat == 'steel':
                i = 1 if t < BANDS[0] else 2 if t < BANDS[1] else 3
                if opt.get('flute') and (x - x0) % 2 == 1: i += 1
                if bottom and y > y0: i = 3
                if y == y0 and HILITE[0] <= t <= HILITE[1] and x1 - x0 >= 4: i = 0
                g[y, x] = STEEL[min(4, i + s)]
            elif mat == 'brass': g[y, x] = 'brass-3' if HILITE[0] <= t <= HILITE[1] and x1 - x0 >= 4 else 'brass-1' if t >= 0.8 else 'brass-2'
            elif mat == 'cloth': g[y, x] = 'cloth-1' if x == x0 or bottom else 'cloth-2'
            else: g[y, x] = mat                                # a palette name used flat
    for kind, mat, shape, *o in parts:
        opt = o[0] if o else {}; k = rast(shape)
        if kind == 'sym': put(k | k[:, ::-1], mat, opt)
        elif kind == 'pair': put(k, mat, opt); put(k[:, ::-1], mat, dict(opt, shift=opt.get('shift', 0) + (FAR_SIDE if mat == 'steel' else 0)))
        else: put(k, mat, opt)
    return g
N = {'noline': 1}
# Shapes sit on the viewer's left and are mirrored about the middle (between x = 31 and 32). Rows: head 8-17, shoulders 17-27,
# hands 27-33, belt 34-35, skirt 36-41, legs 41-55, boots 56-60. The sword is carried upright in front, as in the reference.
LOWER = [                                                      # shared by both views
 ('pair', 'steel', [(24, 41), (29, 41), (29, 48), (25, 48)], {'shift': 1}),                       # thighs
 ('pair', 'steel', [(24, 50), (29, 50), (29, 55), (25, 55)], {'shift': 1}),                       # greaves
 ('pair', 'brass', R(24, 49, 29, 49)),                                                            # knee bands
 ('pair', 'steel', [(22, 56), (29, 56), (29, 60), (21, 60)]),                                     # boots
 ('sym', 'steel', [(25, 36), (31, 36), (31, 40), (24, 40)]),                                      # skirt
 ('sym', 'brass', R(26, 34, 31, 35)),                                                             # belt
]
SHOULDERS = [
 ('pair', 'steel', [(15, 22), (17, 18), (23, 17), (27, 19), (27, 25), (22, 27), (16, 26)]),       # pauldrons
 ('pair', 'brass', R(17, 26, 22, 26), N),                                                         # pauldron rims
 ('pair', 'steel', [(25, 10), (27, 9), (26, 4), (24, 2), (23, 3), (24, 7)], {'shift': 2}),        # horns
]
FRONT = LOWER + [
 ('pair', 'steel-1', R(24, 41, 24, 41), N),
 ('sym', 'cloth', R(30, 41, 31, 47)),                                                             # cloth between the legs
 ('pair', 'glow-1', R(27, 51, 27, 53), N),                                                        # shin lights
 ('pair', 'steel', R(17, 26, 22, 31), {'shift': 1}),                                              # upper arms
 ('sym', 'steel', [(27, 19), (31, 19), (31, 33), (28, 33), (27, 30)], {'flute': 1}),              # fluted breastplate
 ('sym', 'brass', R(29, 20, 31, 23)), ('sym', 'glow-1', R(30, 21, 31, 22), N),                    # chest core
 ('sym', 'steel-1', R(28, 18, 31, 18), N),                                                        # gorget
] + SHOULDERS + [
 ('pair', 'glow-1', R(17, 22, 20, 22), N),                                                        # pauldron light strips
 ('pair', 'brass', R(25, 20, 26, 21)),                                                            # rondels
 ('pair', 'steel', [(18, 30), (24, 28), (28, 28), (28, 33), (22, 34), (18, 33)]),                 # forearms and cuffs
 ('pair', 'brass', R(24, 28, 24, 33), N),                                                         # cuff rims
 ('pair', 'steel', [(26, 13), (23, 10), (26, 15)], {'shift': 1}),                                 # cheek blades
 ('sym', 'steel', [(27, 10), (29, 8), (31, 8), (31, 17), (29, 17), (27, 15)]),                    # helmet
 ('sym', 'ink', [(28, 11), (31, 12), (31, 12), (28, 11)], N),                                     # brow
 ('pair', 'glow-1', R(29, 12, 30, 12), N),                                                        # eyes
 ('pair', 'ink', R(28, 15, 28, 15), N), ('pair', 'ink', R(30, 15, 30, 15), N),                    # bared teeth: dark gaps
 ('pair', 'steel-5', R(29, 15, 29, 15), N),
 ('sym', 'steel', R(29, 27, 31, 33), {'shift': 2}),                                               # hands on the grip
 ('sym', 'brass', R(27, 26, 31, 26)),                                                             # sword guard
 ('one', 'steel-5', R(31, 1, 31, 25), N), ('one', 'steel-3', R(32, 1, 32, 25), N),                # blade, edge on: light side and dark side
 ('one', 'ink', R(31, 0, 32, 0), N),
 ('sym', 'leather-1', R(31, 34, 31, 34), N),                                                      # grip
]
BACK = LOWER + [
 ('sym', 'cloth', R(29, 41, 31, 48)),                                                             # cloth at the back
 ('sym', 'glow-1', R(31, 43, 31, 45), N),
 ('pair', 'brass', R(27, 50, 27, 54), N),                                                         # calf pistons
 ('pair', 'steel', R(17, 26, 23, 33), {'shift': 1}),                                              # arms from behind
 ('pair', 'brass', R(19, 30, 20, 31)),                                                            # elbow fans
 ('sym', 'steel', [(27, 19), (31, 19), (31, 33), (28, 33), (27, 30)], {'shift': 1}),              # backplate
 ('sym', 'glow-1', R(31, 27, 31, 31), N),                                                         # spine light
 ('sym', 'steel', R(27, 20, 31, 25), {'shift': 2}),                                               # reactor drum
 ('pair', 'brass', R(28, 20, 28, 25), N), ('sym', 'brass', R(31, 20, 31, 25), N),                 # drum ribs
 ('pair', 'glow-1', R(26, 21, 26, 24), N),                                                        # drum end lights
 ('pair', 'steel', R(23, 10, 25, 18), {'shift': 2}),                                              # exhaust stacks
 ('pair', 'brass', R(23, 9, 25, 9), N),
] + SHOULDERS + [
 ('one', 'steel-5', R(31, 1, 31, 8), N), ('one', 'steel-3', R(32, 1, 32, 8), N), ('one', 'ink', R(31, 0, 32, 0), N),   # blade tip above the head
 ('sym', 'steel', [(27, 10), (29, 8), (31, 8), (31, 17), (29, 17), (27, 15)]),                    # helmet from behind
 ('sym', 'ink', R(31, 10, 31, 11), N), ('sym', 'ink', R(31, 14, 31, 15), N),                      # fins down the back of the helmet
 ('sym', 'steel-1', R(28, 18, 31, 18), N),
]
def run(*a): return subprocess.run([K, *a], capture_output=True, text=True)
os.makedirs('out', exist_ok=True); os.makedirs('tmp', exist_ok=True)
for name, parts in (('front', FRONT), ('back', BACK)):
    g = draw(parts)
    for y in range(F):                                          # skirt hem: alternate dark notches, as on the reference
        for x in range(F):
            if y == 40 and g[y, x].startswith('steel') and x % 2 == 0: g[y, x] = 'ink'
    names = sorted({n for n in g.flatten() if n}); chars = 'abcdefghijklmnopqrstuvwxyz'; code = {n: chars[i] for i, n in enumerate(names)}
    open(f'tmp/{name}.grid', 'w').write('\n'.join(f'{code[n]} = {n}' for n in names) + '\n\n' + '\n'.join(''.join(code[g[y, x]] if g[y, x] else '.' for x in range(F)) for y in range(F)) + '\n')
    b = f'out/knight_{name}.klad'; shutil.rmtree(b, ignore_errors=True); run('new', b, '--pixel', f'{F}x{F}')
    for n, h in PALETTE: run('palette', b, '--add', h, '--name', n)
    a = run('pixel', b, 'l1', '--grid', f'tmp/{name}.grid'); o = run('pixel', b, 'l1', '--color', 'ink', '--outline')
    if a.returncode or o.returncode: print('klad error', name, (a.stderr or o.stderr)[:300]); sys.exit(1)
    run('export', b, '--scale', '1', '-o', f'out/knight_{name}_1x.png'); run('export', b, '--scale', '6', '-o', f'out/knight_{name}_6x.png')
    print(name, run('check', b).stdout.split('\n')[0])
