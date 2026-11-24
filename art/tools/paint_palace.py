#!/usr/bin/env python3
"""Paint the palace textures in klad from the op files palace_tex.py wrote, pass by pass, and export the final PNGs plus a
passes strip per texture (each pass at 1/4 size, side by side). Usage:
  python3 paint_palace.py KLAD OPSDIR SRCDIR OUTDIR STRIPDIR
KLAD = the klad binary; OPSDIR = palace_tex.py output; SRCDIR = where the .klad bundles go (art/src); OUTDIR = final PNGs
(assets/tex); STRIPDIR = passes strips. Ships only exported PNGs (klad licence: no klad code in the game).
"""
import json, os, shutil, subprocess, sys
from PIL import Image

K, OPS, SRC, OUT, STRIP = sys.argv[1:6]
for d in (SRC, OUT, STRIP):
    os.makedirs(d, exist_ok=True)
for name in ('hall_floor', 'hall_wall', 'pillar', 'door', 'lion_stone'):
    bundle = os.path.join(SRC, name + '.klad')
    shutil.rmtree(bundle, ignore_errors=True)
    bg = open(os.path.join(OPS, name + '.bg')).read().strip()
    subprocess.run([K, 'new', bundle, '--width', '1024', '--height', '1024', '--background', bg], check=True, capture_output=True)
    ops = open(os.path.join(OPS, name + '.jsonl')).read().splitlines()
    cuts = json.load(open(os.path.join(OPS, name + '.passes.json')))
    frames, done = [], 0
    for label, upto in cuts:
        chunk = os.path.join(OPS, name + '.chunk.jsonl')
        open(chunk, 'w').write('\n'.join(ops[done:upto]) + '\n')
        subprocess.run([K, 'apply', bundle, '--file', chunk], check=True, capture_output=True)
        done = upto
        png = os.path.join(STRIP, f'{name}_{len(frames)}_{label}.png')
        subprocess.run([K, 'export', bundle, '--background', '-o', png], check=True, capture_output=True)
        frames.append((label, png))
    shutil.copy(frames[-1][1], os.path.join(OUT, name + '.png'))
    cache = os.path.join(bundle, '.cache')
    shutil.rmtree(cache, ignore_errors=True)
    tiles = [Image.open(p).convert('RGB').resize((256, 256)) for _, p in frames]
    strip = Image.new('RGB', (len(tiles) * 262, 256), (255, 255, 255))
    for i, t in enumerate(tiles):
        strip.paste(t, (i * 262, 0))
    strip.save(os.path.join(STRIP, name + '_passes.png'))
    for _, p in frames:
        os.remove(p)
    print(name, 'passes', ' > '.join(l for l, _ in frames))
