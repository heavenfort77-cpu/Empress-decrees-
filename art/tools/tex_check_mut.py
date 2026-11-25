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
def blocks(a): b = a.copy(); yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]; b[..., :3] += (16 * (((xx // 256) + (yy // 128)) % 2) - 8)[..., None]; return b
def saturate(a): b = a.copy(); b[..., 0] = np.clip(a[..., 0] * 1.6, 0, 255); b[..., 2] = a[..., 2] * 0.4; return b
# FIXB 25 Nov mutations (new rows and rules): flags with two schools swapped, flags without the bone keyline, inlay shifted into the border,
# inlay in hazard red, inlay in white, pond dulled, pond grey, mercury back at round 3 value.
def swap01(a): b = a.copy(); C = a.shape[1] // 3; b[:C, :C], b[:C, C:2 * C] = a[:C, C:2 * C].copy(), a[:C, :C].copy(); return b
def nokey(a):
    b = a.copy(); C = a.shape[1] // 3; y0, x0 = C + 40 * a.shape[0] // 1024, C + 12 * a.shape[1] // 1024; blk = b[y0 - 4:y0 + 30, x0:x0 + C - 30]
    L = 0.2126 * blk[..., 0] + 0.7152 * blk[..., 1] + 0.0722 * blk[..., 2]; blk[L > 60, :3] = np.array([26, 22, 20]); return b   # keylines and their soft edges painted over
def roll20(a): b = a.copy(); b[500:520, 4:16] = np.array([168, 134, 76, 255]); return b   # a stud set into the border
def tellred(a): b = a.copy(); b[a[..., 3] > 127, :3] = np.array([224, 48, 26]); return b
def white(a): b = a.copy(); b[a[..., 3] > 127, :3] = 245; return b
def r3(a): b = a.copy(); b[..., :3] = a[..., :3] * 0.82; return b
def busy(a): b = a.copy(); yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]; b[..., :3] += (26 * (((xx // 24) + (yy // 24)) % 2) - 13)[..., None]; return b
M = [  # (texture, mutation, rule that must fail)
    ('hall_floor', dull, 'value'), ('hall_floor', busy, 'contrast'), ('hall_floor', flat, 'contrast'), ('hall_floor', shear, 'seam x'),   # COLOUR 25 Nov: the re-based hall floor row
    ('hall_wall', dull, 'value'), ('signal_flags', swap01, 'school colours'), ('signal_flags', nokey, 'band reads'), ('star_inlay', roll20, 'edge clear'), ('star_inlay', tellred, 'not hazard ring'),
    ('star_inlay', white, 'subtle'), ('pond_water', dull, 'value'), ('pond_water', grey, 'teal tint'), ('mercury_matcap', r3, 'value'),
    ('rammed_earth', flat, 'brush scale'), ('rammed_earth', flat, 'contrast'), ('rammed_earth', shear, 'seam x'),
    ('stone_paving', saturate, 'saturation'), ('stone_paving', blocks, 'repeat'), ('rammed_earth', blocks, 'repeat'), ('black_lake', grey, 'teal tint'), ('garden_plants', faint, 'alpha test'),
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
