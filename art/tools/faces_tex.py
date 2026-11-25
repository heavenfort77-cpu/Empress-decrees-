#!/usr/bin/env python3
"""Face options sample (FACES worker, owner 25 Nov 09:44): the painted face textures, written as klad stroke ops and painted in klad.
  C  face_skin.png        a calm painted face (skin, brows, eyes, upturned moustache, lips); terracotta-warrior faces are reference only
  D  face_lacq_<c>.png    black lacquer with line work in one colour (own design: eye frames with a temple sweep, forehead lozenge with two
                          cloud scrolls, nose line, cheek lines, mouth, chin dots, border); not a copy of any opera face; no text
Layout = art/tools/faces_kit.py: u = 0.5 + 0.5 s, v = t (image row from the top = (1 - t) * SIZE).
Usage: python3 faces_tex.py OPSDIR                                   (write the op files)
       python3 faces_tex.py --paint KLAD OPSDIR SRCDIR OUTDIR STRIPDIR  (paint in klad, export PNGs and a passes strip per texture)
Ships only exported PNGs (klad licence: no klad code in the game)."""
import json, math, os, random, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import faces_kit as K

# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Texture size, px.
SIZE = 512
# Skin colours: base, shadow, blush, deep shadow (sRGB).
SKIN = dict(base='#c39a7f', shade='#a77a62', blush='#c4806c', deep='#8e6450')
# Dark paint for brows, moustache and lid lines; eye white; iris; lips; lip line; glint.
INK, EYE_W, IRIS, LIPS, LIP_LINE, GLINT = '#2a201c', '#ddd2c0', '#21160f', '#995a4c', '#5e342c', '#f1ebdf'
# Lacquer base (black with a little red-brown).
LACQ = '#19130f'
# Line colour per lacquer variant: 法 lead white (school pigment map), the court's water-blue (guards), cinnabar (giants).
LINES = {'fa': '#e6e0cf', 'court': '#6fa6c4', 'cinnabar': '#c0452e'}
# Line width of the lacquer motif, px at SIZE.
LW = 8


def X(s): return 256 + 256 * s * SIZE / 512
def Y(t): return (1 - t) * SIZE


class Tex:
    def __init__(s, name, bg, seed):
        s.name, s.bg, s.r, s.ops, s.stage = name, bg, random.Random(seed), [], 0

    def st(s, pts_st, brush, size, color, opacity=1.0, taper=None, mirror=True):
        """pts in (s, t) face coordinates; mirror = also paint the other side (s -> -s)."""
        for m in ((1, -1) if mirror else (1,)):
            d = 'M' + ' L'.join(f'{X(m * a):.1f} {Y(b):.1f}' for a, b in pts_st)
            op = {"op": "stroke", "layer": "l1", "brush": brush, "size": size, "color": color, "opacity": opacity, "path": d,
                  "seed": s.r.randrange(1, 1 << 30)}
            if taper is not None: op["taper"] = [round(taper * 6), round(taper * 10)]
            s.ops.append((s.stage, op))

    def write(s, out):
        with open(f'{out}/{s.name}.jsonl', 'w') as f:
            for st, op in s.ops: f.write(json.dumps(op) + '\n')
        cuts, names = [], ['base', 'tone', 'marks', 'detail']
        for i, (st, op) in enumerate(s.ops):
            if i + 1 == len(s.ops) or s.ops[i + 1][0] != st: cuts.append([names[st], i + 1])
        json.dump(cuts, open(f'{out}/{s.name}.passes.json', 'w'))
        open(f'{out}/{s.name}.bg', 'w').write(s.bg)
        return len(s.ops)


def arc(a, b, c, n=8):
    """quadratic curve through control point b (s, t)."""
    return [tuple((1 - u) ** 2 * a[i] + 2 * (1 - u) * u * b[i] + u * u * c[i] for i in range(2)) for u in [k / n for k in range(n + 1)]]


def skin():
    T = Tex('face_skin', SKIN['base'], 11)
    T.stage = 0   # base: broad skin strokes so the field is not flat
    for k in range(14):
        t = 1.05 - k * 0.085
        T.st([(-1.1, t + T.r.uniform(-0.01, 0.01)), (0, t), (1.1, t + T.r.uniform(-0.01, 0.01))], 'flat-bristle', 60, SKIN['base'], 0.5, mirror=False)
    T.stage = 1   # tone: side shade, eye sockets, under the brow, blush, under the nose and lip, under the chin
    for x in (0.86, 0.95):
        T.st([(x, 1.05), (x, -0.05)], 'soft', 70, SKIN['shade'], 0.45)
    T.st(arc((K.S_EYE - 0.2, K.T_EYE + 0.02), (K.S_EYE, K.T_EYE + 0.07), (K.S_EYE + 0.22, K.T_EYE + 0.02)), 'soft', 34, SKIN['shade'], 0.55)
    T.st([(K.S_EYE - 0.12, K.T_EYE - 0.05), (K.S_EYE + 0.14, K.T_EYE - 0.05)], 'soft', 22, SKIN['shade'], 0.35)
    T.st([(0.42, 0.45), (0.58, 0.4)], 'soft', 60, SKIN['blush'], 0.4)
    T.st([(-0.06, K.T_NOSE - 0.02), (0.06, K.T_NOSE - 0.02)], 'soft', 22, SKIN['shade'], 0.5, mirror=False)
    T.st([(-0.12, K.T_MOUTH - 0.06), (0.12, K.T_MOUTH - 0.06)], 'soft', 22, SKIN['shade'], 0.4, mirror=False)
    T.st([(-0.6, -0.02), (0.6, -0.02)], 'soft', 50, SKIN['deep'], 0.5, mirror=False)
    T.st([(0.08, K.T_EYE + 0.02), (0.06, K.T_NOSE + 0.04)], 'soft', 14, SKIN['shade'], 0.35)
    T.stage = 2   # marks: brows, eyes (white, iris, upper lid, lower lid), moustache, lips, nostrils
    T.st(arc((0.13, K.T_BROW - 0.03), (0.33, K.T_BROW + 0.03), (0.58, K.T_BROW - 0.01)), 'ink', 13, INK, 1.0, taper=0.6)
    T.st([(K.S_EYE - 0.12, K.T_EYE - 0.003), (K.S_EYE + 0.12, K.T_EYE)], 'marker', 18, EYE_W, 1.0)
    T.st([(K.S_EYE - 0.015, K.T_EYE), (K.S_EYE + 0.015, K.T_EYE)], 'marker', 21, IRIS, 1.0)
    T.st(arc((K.S_EYE - 0.17, K.T_EYE - 0.01), (K.S_EYE, K.T_EYE + 0.045), (K.S_EYE + 0.17, K.T_EYE + 0.01)), 'ink', 7, INK, 1.0, taper=0.4)
    T.st(arc((K.S_EYE - 0.12, K.T_EYE - 0.012), (K.S_EYE, K.T_EYE - 0.03), (K.S_EYE + 0.14, K.T_EYE - 0.005)), 'ink', 3, SKIN['deep'], 0.8)
    T.st(arc((0.03, K.T_MOUTH + 0.085), (0.2, K.T_MOUTH + 0.06), (0.31, K.T_MOUTH + 0.115)), 'ink', 13, INK, 1.0, taper=0.7)
    T.st([(-0.17, K.T_MOUTH + 0.006), (0, K.T_MOUTH + 0.012), (0.17, K.T_MOUTH + 0.006)], 'marker', 12, LIPS, 0.9, mirror=False)
    T.st([(-0.17, K.T_MOUTH + 0.004), (0, K.T_MOUTH - 0.002), (0.17, K.T_MOUTH + 0.004)], 'ink', 3, LIP_LINE, 1.0, mirror=False)
    T.st([(0.08, K.T_NOSE + 0.005), (0.1, K.T_NOSE + 0.005)], 'marker', 7, SKIN['deep'], 0.9)
    T.stage = 3   # detail: eye glints, a tuft under the lip
    T.st([(K.S_EYE + 0.02, K.T_EYE + 0.008), (K.S_EYE + 0.025, K.T_EYE + 0.01)], 'marker', 4, GLINT, 1.0)
    T.st([(0, K.T_MOUTH - 0.035), (0, K.T_MOUTH - 0.08)], 'ink', 8, INK, 0.9, taper=0.8, mirror=False)
    return T


def lacquer(key, col):
    T = Tex(f'face_lacq_{key}', LACQ, 23)
    T.stage = 0   # base: lacquer brush strokes (very low contrast)
    for k in range(12):
        t = 1.05 - k * 0.095
        T.st([(-1.1, t), (1.1, t + T.r.uniform(-0.02, 0.02))], 'flat-bristle', 70, '#221a15', 0.35, mirror=False)
    T.stage = 2   # marks: the motif (both sides mirrored)
    e0, e1 = K.S_EYE - K.S_EYE_HALF - 0.03, K.S_EYE + K.S_EYE_HALF + 0.03
    T.st(arc((e0, K.T_EYE), (K.S_EYE, K.T_EYE + 0.11), (e1, K.T_EYE + 0.045)) + [(0.82, K.T_EYE + 0.17)], 'ink', LW, col, 1.0, taper=0.3)
    T.st(arc((e0, K.T_EYE), (K.S_EYE, K.T_EYE - 0.08), (e1, K.T_EYE + 0.045)), 'ink', LW - 2, col, 1.0)
    T.st([(0, 0.95), (0.075, 0.86), (0, 0.77), (-0.075, 0.86), (0, 0.95)], 'ink', LW - 1, col, 1.0, mirror=False)
    sp = []
    for k in range(25):
        a = k / 24 * math.pi * 3.0; r = 0.075 * (1 - k / 30)
        sp.append((0.27 + r * math.cos(a + math.pi), 0.87 + r * math.sin(a + math.pi) * 0.9))
    T.st(sp, 'ink', LW - 2, col, 1.0)
    T.st([(0, 0.76), (0, K.T_NOSE + 0.08)], 'ink', LW - 3, col, 1.0, mirror=False)
    T.st(arc((0.4, 0.5), (0.47, 0.38), (0.56, 0.24)), 'ink', LW - 2, col, 1.0, taper=0.5)
    T.st(arc((0.5, 0.5), (0.57, 0.39), (0.66, 0.27)), 'ink', LW - 2, col, 1.0, taper=0.5)
    T.st([(-0.2, K.T_MOUTH + 0.02), (-0.17, K.T_MOUTH), (0.17, K.T_MOUTH), (0.2, K.T_MOUTH + 0.02)], 'ink', LW - 2, col, 1.0, mirror=False)
    T.st([(0.065, 0.08), (0.08, 0.08)], 'marker', LW + 8, col, 1.0)
    T.st([(0.9, 0.05), (0.92, 0.5), (0.9, 0.95)], 'ink', LW - 3, col, 1.0)
    T.st([(-0.9, 0.97), (0, 0.975), (0.9, 0.97)], 'ink', LW - 3, col, 1.0, mirror=False)
    return T


def all_tex(): return [skin()] + [lacquer(k, c) for k, c in LINES.items()]


def paint(KL, OPS, SRC, OUT, STRIP):
    from PIL import Image
    for d in (SRC, OUT, STRIP): os.makedirs(d, exist_ok=True)
    n = 0
    for T in all_tex():
        name = T.name; bundle = os.path.join(SRC, name + '.klad'); shutil.rmtree(bundle, ignore_errors=True)
        subprocess.run([KL, 'new', bundle, '--width', str(SIZE), '--height', str(SIZE), '--background', open(os.path.join(OPS, name + '.bg')).read().strip()], check=True, capture_output=True)
        ops = open(os.path.join(OPS, name + '.jsonl')).read().splitlines(); cuts = json.load(open(os.path.join(OPS, name + '.passes.json')))
        frames, done = [], 0
        for label, upto in cuts:
            chunk = os.path.join(OPS, name + '.chunk.jsonl'); open(chunk, 'w').write('\n'.join(ops[done:upto]) + '\n')
            subprocess.run([KL, 'apply', bundle, '--file', chunk], check=True, capture_output=True); done = upto
            png = os.path.join(STRIP, f'{name}_{len(frames)}_{label}.png')
            subprocess.run([KL, 'export', bundle, '--background', '-o', png], check=True, capture_output=True); frames.append(png)
        shutil.copy(frames[-1], os.path.join(OUT, name + '.png')); shutil.rmtree(os.path.join(bundle, '.cache'), ignore_errors=True)
        tiles = [Image.open(p).convert('RGB').resize((256, 256)) for p in frames]
        strip = Image.new('RGB', (len(tiles) * 262, 256), (255, 255, 255))
        for i, t in enumerate(tiles): strip.paste(t, (i * 262, 0))
        strip.save(os.path.join(STRIP, f'{name}_passes.png')); n += 1
        print('painted', name, len(ops), 'ops', len(frames), 'passes')
    return n


if __name__ == '__main__':
    if sys.argv[1] == '--paint':
        n = paint(*sys.argv[2:7]); print(f'FACES tex painted {n} of {len(LINES) + 1}')
    else:
        os.makedirs(sys.argv[1], exist_ok=True)
        for T in all_tex(): print(T.name, T.write(sys.argv[1]), 'ops')
