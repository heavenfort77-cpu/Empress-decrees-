#!/usr/bin/env python3
"""Paint the suit trim sheets in klad from the op files suit_tex.py wrote, pass by pass; export the final PNGs and a passes strip
per sheet (each pass at 256 px, side by side). Sheet size comes from <name>.size (suit_bronze and suit_cloth are 512 px = 2 m).
Usage: python3 suit_paint.py KLAD OPSDIR SRCDIR OUTDIR STRIPDIR   (SRCDIR gets the .klad bundles: art/src; OUTDIR: assets/tex)
Ships only exported PNGs (klad licence: no klad code in the game)."""
import json, os, shutil, subprocess, sys
from PIL import Image

K, OPS, SRC, OUT, STRIP = sys.argv[1:6]
# optional 6th argument: comma list of sheets to paint (default all three)
NAMES = sys.argv[6].split(',') if len(sys.argv) > 6 else ['suit_lamellar', 'suit_bronze', 'suit_cloth']
for d in (SRC, OUT, STRIP): os.makedirs(d, exist_ok=True)
for name in NAMES:
    size = open(os.path.join(OPS, name + '.size')).read().strip()
    bundle = os.path.join(SRC, name + '.klad'); shutil.rmtree(bundle, ignore_errors=True)
    bg = open(os.path.join(OPS, name + '.bg')).read().strip()
    subprocess.run([K, 'new', bundle, '--width', size, '--height', size, '--background', bg], check=True, capture_output=True)
    ops = open(os.path.join(OPS, name + '.jsonl')).read().splitlines(); cuts = json.load(open(os.path.join(OPS, name + '.passes.json')))
    frames, done = [], 0
    for label, upto in cuts:
        chunk = os.path.join(OPS, name + '.chunk.jsonl'); open(chunk, 'w').write('\n'.join(ops[done:upto]) + '\n')
        subprocess.run([K, 'apply', bundle, '--file', chunk], check=True, capture_output=True); done = upto
        png = os.path.join(STRIP, f'{name}_{len(frames)}_{label}.png')
        subprocess.run([K, 'export', bundle, '--background', '-o', png], check=True, capture_output=True); frames.append((label, png))
    shutil.copy(frames[-1][1], os.path.join(OUT, name + '.png'))
    shutil.rmtree(os.path.join(bundle, '.cache'), ignore_errors=True)
    tiles = [Image.open(p).convert('RGB').resize((256, 256)) for _, p in frames]
    strip = Image.new('RGB', (len(tiles) * 262, 256), (255, 255, 255))
    for i, im in enumerate(tiles): strip.paste(im, (i * 262, 0))
    strip.save(os.path.join(STRIP, name + '_passes.png'))
    for _, p in frames: os.remove(p)
    print(name, size, 'passes', ' > '.join(l for l, _ in frames))
