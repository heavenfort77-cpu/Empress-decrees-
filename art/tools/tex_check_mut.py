#!/usr/bin/env python3
"""Mutation test for the W2 rows of tex_check.py: each mutation breaks one rule on a copy of one texture; the check must print FAIL for
that texture and rule. Prints CAUGHT / MISSED per mutation and 'N of N caught'. Usage: python3 tex_check_mut.py TEXDIR"""
import os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image

SRC = sys.argv[1]; HERE = os.path.dirname(os.path.abspath(__file__))
def load(n): return np.asarray(Image.open(f'{SRC}/{n}.png').convert('RGBA')).astype(float)
def flat(a): b = a.copy(); b[..., :3] = a[..., :3].reshape(-1, 3).mean(0); return b
def shear(a): b = a.copy(); b[:, :512] = np.roll(a[:, :512], 37, axis=0); return b
def grey(a): b = a.copy(); m = a[..., :3].mean(2, keepdims=True); b[..., :3] = m; return b
def faint(a): b = a.copy(); b[..., 3] = np.where(a[..., 3] > 0, 100, 0); return b
def dull(a): b = a.copy(); b[..., :3] = a[..., :3] * 0.6; return b
def blank_band(a): b = a.copy(); b[60:420, :, :3] = np.array([214, 204, 182]); return b
def blank_discs(a): b = a.copy(); b[..., :3] = np.array([87, 86, 84]); return b
def saturate(a): b = a.copy(); b[..., 0] = np.clip(a[..., 0] * 1.6, 0, 255); b[..., 2] = a[..., 2] * 0.4; return b
M = [  # (texture, mutation, rule that must fail)
    ('rammed_earth', flat, 'brush scale'), ('rammed_earth', flat, 'contrast'), ('rammed_earth', shear, 'seam x'),
    ('stone_paving', saturate, 'saturation'), ('black_lake', grey, 'teal tint'), ('garden_plants', faint, 'alpha test'),
    ('mercury_matcap', dull, 'brightest'), ('mural_wall', blank_band, 'mural ink'), ('tile_ends', blank_discs, 'contrast'),
    ('timber', dull, 'value'), ('earth_burnt', grey, 'reddened'), ('wall_burnt', lambda a: load('hall_wall'), 'darker than unburnt'),
]
caught = 0
for name, fn, rule in M:
    d = tempfile.mkdtemp()
    for f in os.listdir(SRC):
        if f.endswith('.png'): shutil.copy(f'{SRC}/{f}', d)
    Image.fromarray(fn(load(name)).clip(0, 255).astype(np.uint8), 'RGBA').save(f'{d}/{name}.png')
    out = subprocess.run([sys.executable, f'{HERE}/tex_check.py', d, '1', '4'], capture_output=True, text=True).stdout
    hit = any(l.startswith('FAIL') and name in l and rule in l for l in out.splitlines())
    caught += hit; print(('CAUGHT ' if hit else 'MISSED ') + f'{name} {fn.__name__} -> {rule}')
    shutil.rmtree(d)
print(f'{caught} of {len(M)} caught')
