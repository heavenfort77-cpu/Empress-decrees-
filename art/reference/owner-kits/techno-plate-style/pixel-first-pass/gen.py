#!/usr/bin/env python3
"""Techno-plate armour suit style: four base samples, 64 px, front view.
Run: python3 gen.py   -> out/*.png
Each character is data (PARTS). Half shapes are drawn on the viewer's left and mirrored on axis 31.5."""
import os
import numpy as np
from PIL import Image, ImageDraw

# ---------------- CONFIG: tune by hand ----------------
CONFIG = {
    'frame': 64,
    'light': (0.65, 0.35),      # weight of x and y in the shade ramp (light from upper left)
    'bands': (0.35, 0.75),      # where light->mid and mid->dark switch
    'big_scale': 3,
    'lineup_scale': 4,
    'lineup_bg': '#7d838c',
    # ramps: [rim, light, mid, dark, outline]
    'ramps': {
        'steel':  ['#e6ecef', '#aab4bc', '#737d88', '#474f5a', '#1b1e25'],
        'dsteel': ['#8d97a3', '#5d6672', '#414853', '#2a2f38', '#121419'],
        'brass':  ['#f3d98a', '#c9a14a', '#8f6a2a', '#553c17', '#2a1c0a'],
        'under':  ['#565a63', '#3a3d44', '#2b2d33', '#17181c', '#0b0c0e'],
        'green':  ['#6f9a66', '#4c7549', '#335233', '#1e3323', '#0f1a12'],
        'violet': ['#8f7fc4', '#6a5aa3', '#493d7a', '#2c2450', '#16122a'],
        'red':    ['#c0584f', '#963a3a', '#6b2630', '#431823', '#200b12'],
        'glow':   ['#e8ffff', '#7af0f6', '#2bb7c9', '#127a8c', '#0c3f4a'],
    },
}
# -------------------------------------------------------
F = CONFIG['frame']

def R(x0, y0, x1, y1):
    return ('rect', x0, y0, x1, y1)

def rast(shape):
    im = Image.new('L', (F, F), 0)
    d = ImageDraw.Draw(im)
    if isinstance(shape, tuple) and shape[0] == 'rect':
        d.rectangle(shape[1:], fill=255)
    else:
        d.polygon(shape, fill=255)
    return np.array(im) > 0

def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def shade(mask, mat, mode, rgb, matmap, alpha):
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    Y, X = np.mgrid[0:F, 0:F]
    u = (X - x0) / max(1, x1 - x0)
    v = (Y - y0) / max(1, y1 - y0)
    s = CONFIG['light'][0] * u + CONFIG['light'][1] * v
    b0, b1 = CONFIG['bands']
    idx = np.where(s < b0, 1, np.where(s < b1, 2, 3))
    if mode.startswith('flat'):
        idx = np.full((F, F), int(mode.split(':')[1]))
    else:
        if mode == 'flute':
            idx = np.where((X - x0) % 2 == 1, np.minimum(idx + 1, 3), idx)
        if mode == 'lames':
            idx = np.where((Y - y0) % 3 == 2, 3, idx)
        if mode == 'ribs':
            idx = np.where((Y - y0) % 2 == 1, 3, 2)
        p = np.pad(mask, 1)
        left, up = p[1:-1, :-2], p[:-2, 1:-1]
        right, down = p[1:-1, 2:], p[2:, 1:-1]
        if mode != 'ribs':
            idx = np.where(mask & (~left | ~up) & (s < 0.5), 0, idx)
        idx = np.where(mask & (~right | ~down), 3, idx)
    ramp = [hexrgb(c) for c in CONFIG['ramps'][mat]]
    for i in range(4):
        sel = mask & (idx == i)
        rgb[sel] = ramp[i]
    matmap[mask] = list(CONFIG['ramps']).index(mat)
    alpha[mask] = True

def render(parts, frame=64):
    global F
    F = frame
    rgb = np.zeros((F, F, 3), np.uint8)
    matmap = np.zeros((F, F), np.int16)
    alpha = np.zeros((F, F), bool)
    for kind, mat, mode, shape in parts:
        m = rast(shape)
        if kind == 'sym':
            shade(m | m[:, ::-1], mat, mode, rgb, matmap, alpha)
        elif kind == 'pair':
            shade(m, mat, mode, rgb, matmap, alpha)
            shade(m[:, ::-1], mat, mode, rgb, matmap, alpha)
        else:
            shade(m, mat, mode, rgb, matmap, alpha)
    # outside outline, 1 px, in the darkest tone of the touching material
    names = list(CONFIG['ramps'])
    out = alpha.copy()
    for y in range(F):
        for x in range(F):
            if alpha[y, x]:
                continue
            for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < F and 0 <= yy < F and alpha[yy, xx]:
                    m = names[matmap[yy, xx]]
                    if m == 'glow':
                        m = 'steel'
                    rgb[y, x] = hexrgb(CONFIG['ramps'][m][4])
                    out[y, x] = True
                    break
    return Image.fromarray(np.dstack([rgb, (out * 255).astype(np.uint8)]), 'RGBA')

KNIGHT = [
    ('pair', 'dsteel', 'plain', R(22, 13, 25, 17)),                                   # power pack vents
    ('pair', 'glow', 'flat:1', R(23, 14, 24, 14)),
    ('pair', 'steel', 'flute', [(24, 38), (30, 38), (30, 47), (25, 47)]),             # thighs
    ('pair', 'steel', 'plain', [(24, 50), (30, 50), (30, 57), (25, 57)]),             # greaves
    ('pair', 'brass', 'plain', [(24, 46), (30, 46), (30, 50), (24, 50)]),             # knees
    ('pair', 'glow', 'flat:1', R(27, 48, 27, 48)),
    ('pair', 'dsteel', 'lames', [(22, 57), (30, 57), (30, 61), (21, 61)]),            # sabatons
    ('pair', 'steel', 'lames', R(16, 24, 21, 30)),                                    # upper arms
    ('pair', 'under', 'ribs', R(17, 30, 21, 32)),                                     # elbow undersuit
    ('sym', 'steel', 'flute', [(24, 18), (31, 18), (31, 31), (26, 31), (24, 28)]),    # breastplate
    ('sym', 'dsteel', 'flat:2', R(27, 17, 31, 18)),                                   # gorget
    ('sym', 'brass', 'flat:1', R(25, 31, 31, 32)),                                    # belt
    ('sym', 'steel', 'lames', [(24, 33), (31, 33), (31, 38), (23, 38)]),              # fauld
    ('sym', 'green', 'flute', [(28, 38), (31, 38), (31, 46), (29, 45)]),              # cloth
    ('pair', 'steel', 'plain', [(15, 19), (18, 16), (24, 16), (26, 18), (26, 24), (22, 26), (16, 25), (14, 22)]),  # pauldrons
    ('pair', 'brass', 'flat:0', R(19, 20, 20, 21)),
    ('pair', 'steel', 'flute', [(14, 32), (21, 32), (22, 40), (20, 44), (15, 44), (13, 40)]),  # gauntlets
    ('one', 'brass', 'flat:1', R(13, 49, 21, 50)),                                    # sword guard
    ('one', 'steel', 'plain', [(16, 51), (19, 51), (19, 57), (18, 61), (17, 61), (16, 57)]),   # blade
    ('one', 'glow', 'flat:1', R(17, 52, 18, 58)),
    ('pair', 'dsteel', 'flute', R(15, 44, 21, 48)),                                   # fists
    ('sym', 'steel', 'plain', [(27, 9), (29, 7), (31, 7), (31, 16), (28, 16), (27, 14)]),      # helmet
    ('sym', 'dsteel', 'flat:3', R(28, 11, 31, 14)),                                   # visor
    ('sym', 'glow', 'flat:1', R(28, 11, 31, 11)),
    ('sym', 'glow', 'flat:1', R(29, 13, 31, 13)),
    ('sym', 'brass', 'flat:0', R(31, 7, 31, 10)),                                     # crest ridge
]

MAGE = [
    ('one', 'brass', 'flat:2', R(41, 12, 42, 61)),                                    # staff
    ('one', 'steel', 'plain', [(39, 8), (41, 4), (42, 4), (44, 8), (42, 12), (41, 12)]),       # emitter
    ('one', 'glow', 'flat:1', R(41, 6, 42, 10)),
    ('one', 'glow', 'flat:0', R(41, 7, 42, 9)),
    ('pair', 'dsteel', 'plain', [(25, 59), (30, 59), (30, 61), (24, 61)]),            # feet
    ('sym', 'violet', 'flute', [(24, 32), (31, 32), (31, 59), (21, 59)]),             # robe
    ('sym', 'brass', 'flat:2', R(22, 58, 31, 59)),                                    # hem
    ('sym', 'steel', 'lames', [(29, 32), (31, 32), (31, 52), (30, 54)]),              # front strip
    ('sym', 'glow', 'flat:1', R(31, 36, 31, 36)),
    ('sym', 'glow', 'flat:1', R(31, 42, 31, 42)),
    ('sym', 'glow', 'flat:1', R(31, 48, 31, 48)),
    ('pair', 'under', 'ribs', R(20, 24, 23, 31)),                                     # upper arms
    ('sym', 'steel', 'flute', [(25, 20), (31, 20), (31, 30), (26, 30)]),              # chest
    ('sym', 'brass', 'flat:1', R(25, 30, 31, 31)),                                    # belt
    ('pair', 'steel', 'plain', [(19, 20), (24, 19), (25, 24), (20, 25)]),             # shoulders
    ('pair', 'steel', 'flute', [(19, 31), (24, 31), (24, 39), (20, 39)]),             # bracers
    ('pair', 'dsteel', 'flute', R(20, 39, 24, 42)),                                   # hands
    ('sym', 'brass', 'plain', [(24, 18), (27, 15), (31, 17), (31, 20), (25, 20)]),    # collar
    ('sym', 'steel', 'plain', [(28, 10), (29, 6), (31, 3), (31, 16), (28, 16), (27, 13)]),     # helm
    ('sym', 'glow', 'flat:1', R(29, 11, 31, 11)),                                     # T visor
    ('sym', 'glow', 'flat:1', R(31, 12, 31, 14)),
]

ROGUE = [
    ('one', 'red', 'plain', [(37, 23), (41, 24), (46, 30), (47, 38), (44, 36), (42, 31), (38, 28)]),  # scarf tail
    ('pair', 'under', 'ribs', [(26, 41), (30, 41), (29, 49), (25, 49)]),              # thighs
    ('pair', 'steel', 'plain', [(25, 51), (29, 51), (28, 58), (25, 58)]),             # greaves
    ('pair', 'steel', 'plain', R(25, 48, 29, 51)),                                    # knees
    ('pair', 'dsteel', 'plain', [(23, 58), (28, 58), (28, 61), (22, 61)]),            # feet
    ('sym', 'under', 'ribs', [(26, 24), (31, 24), (31, 37), (27, 37)]),               # torso
    ('sym', 'dsteel', 'flute', [(27, 25), (31, 25), (31, 31), (29, 32), (27, 29)]),   # chest plate
    ('sym', 'glow', 'flat:1', R(31, 27, 31, 28)),
    ('sym', 'brass', 'flat:2', R(26, 36, 31, 37)),                                    # belt
    ('one', 'brass', 'plain', R(27, 37, 29, 39)),                                     # pouch
    ('sym', 'dsteel', 'lames', [(26, 38), (31, 38), (31, 41), (26, 42)]),             # tassets
    ('pair', 'under', 'ribs', R(21, 27, 24, 35)),                                     # arms
    ('one', 'steel', 'plain', [(19, 23), (25, 22), (26, 27), (20, 28)]),              # single pauldron
    ('one', 'dsteel', 'plain', R(37, 23, 42, 26)),                                    # small cap
    ('pair', 'steel', 'flute', [(20, 34), (24, 34), (24, 40), (21, 40)]),             # bracers
    ('pair', 'dsteel', 'plain', R(21, 40, 24, 43)),                                   # hands
    ('pair', 'steel', 'plain', [(21, 44), (24, 44), (20, 55), (18, 54)]),             # daggers
    ('pair', 'brass', 'flat:1', R(20, 43, 25, 43)),
    ('sym', 'red', 'plain', [(26, 22), (31, 23), (31, 25), (27, 25)]),                # scarf wrap
    ('sym', 'red', 'plain', [(26, 15), (27, 12), (30, 10), (31, 8), (31, 22), (27, 22), (25, 19)]),  # hood
    ('sym', 'dsteel', 'flat:3', [(28, 15), (31, 15), (31, 20), (29, 20)]),            # face plate
    ('pair', 'glow', 'flat:1', R(29, 17, 30, 17)),                                    # eyes
]

CONSTRUCT = [
    ('pair', 'brass', 'plain', R(21, 8, 23, 15)),                                     # exhaust pipes
    ('pair', 'dsteel', 'flat:3', R(21, 8, 23, 8)),
    ('pair', 'steel', 'flute', [(22, 47), (29, 47), (29, 56), (21, 56)]),             # legs
    ('pair', 'dsteel', 'lames', [(19, 56), (30, 56), (30, 61), (18, 61)]),            # feet
    ('sym', 'under', 'ribs', R(24, 40, 31, 43)),                                      # waist
    ('sym', 'steel', 'plain', [(22, 43), (31, 43), (31, 47), (23, 48)]),              # pelvis
    ('pair', 'under', 'ribs', R(11, 26, 17, 32)),                                     # upper arms
    ('sym', 'steel', 'flute', [(18, 16), (31, 14), (31, 40), (22, 40), (17, 34), (16, 22)]),   # barrel torso
    ('sym', 'brass', 'plain', R(28, 23, 31, 31)),                                     # reactor ring
    ('sym', 'glow', 'flat:1', R(29, 25, 31, 29)),
    ('sym', 'glow', 'flat:0', R(30, 26, 31, 28)),
    ('sym', 'dsteel', 'plain', [(28, 9), (31, 9), (31, 16), (27, 16)]),               # head
    ('sym', 'brass', 'flat:1', R(28, 10, 31, 10)),
    ('sym', 'glow', 'flat:1', R(30, 12, 31, 13)),                                     # single eye
    ('pair', 'steel', 'plain', [(8, 18), (12, 13), (18, 13), (20, 17), (19, 26), (10, 27)]),   # shoulders
    ('pair', 'brass', 'flat:0', R(11, 19, 11, 19)),
    ('pair', 'brass', 'flat:0', R(15, 16, 15, 16)),
    ('pair', 'brass', 'flat:0', R(16, 22, 16, 22)),
    ('pair', 'steel', 'lames', [(7, 32), (18, 32), (19, 44), (16, 49), (9, 49), (6, 44)]),     # forearms
    ('pair', 'glow', 'flat:1', R(12, 34, 13, 35)),
    ('pair', 'dsteel', 'flute', R(8, 49, 17, 55)),                                    # fists
]

# 96 px frame, axis 47.5. Sword planted in front, both hands on the grip.
KNIGHT96 = [
    ('pair', 'dsteel', 'plain', R(33, 17, 38, 24)),                                   # power pack vents
    ('pair', 'glow', 'flat:1', R(34, 19, 37, 19)),
    ('pair', 'steel', 'flute', [(35, 52), (44, 52), (44, 66), (36, 66)]),             # thighs
    ('pair', 'steel', 'plain', [(36, 71), (44, 71), (43, 86), (37, 86)]),             # greaves
    ('pair', 'steel', 'plain', [(35, 64), (44, 64), (45, 68), (44, 72), (36, 72), (34, 68)]),  # knees
    ('pair', 'brass', 'flat:2', R(36, 72, 44, 72)),
    ('pair', 'glow', 'flat:1', R(39, 67, 40, 68)),
    ('pair', 'dsteel', 'lames', [(33, 86), (44, 86), (44, 93), (31, 93)]),            # sabatons
    ('sym', 'green', 'flute', [(42, 52), (47, 52), (47, 64), (44, 62)]),              # cloth
    ('pair', 'steel', 'lames', [(27, 34), (34, 34), (34, 45), (28, 45)]),             # upper arms
    ('pair', 'under', 'ribs', R(28, 45, 34, 47)),                                     # elbow undersuit
    ('sym', 'steel', 'flute', [(36, 24), (47, 24), (47, 42), (39, 42), (36, 37)]),    # breastplate
    ('sym', 'dsteel', 'plain', [(41, 21), (47, 21), (47, 24), (40, 24)]),             # gorget
    ('sym', 'brass', 'plain', R(38, 42, 47, 44)),                                     # belt
    ('sym', 'steel', 'lames', [(36, 45), (47, 45), (47, 52), (34, 52)]),              # fauld
    ('pair', 'steel', 'plain', [(22, 29), (26, 23), (35, 22), (39, 25), (39, 33), (34, 37), (24, 36), (21, 33)]),  # pauldrons
    ('pair', 'steel', 'plain', [(23, 33), (34, 34), (34, 37), (24, 36)]),             # lower pauldron plate
    ('pair', 'brass', 'flat:0', R(29, 28, 30, 29)),
    ('pair', 'brass', 'plain', [(36, 27), (38, 26), (40, 28), (39, 31), (37, 31)]),   # rondels
    ('sym', 'steel', 'plain', [(45, 54), (47, 54), (47, 93), (46, 90), (45, 86)]),    # blade
    ('sym', 'glow', 'flat:1', R(47, 56, 47, 87)),
    ('sym', 'brass', 'plain', [(36, 51), (47, 51), (47, 53), (37, 53)]),              # guard
    ('pair', 'steel', 'plain', [(27, 47), (33, 44), (42, 43), (42, 50), (34, 52), (28, 52)]),  # forearms
    ('pair', 'steel', 'plain', [(26, 43), (31, 42), (33, 46), (30, 50), (26, 48)]),   # elbow cops
    ('sym', 'dsteel', 'flute', R(41, 43, 47, 50)),                                    # hands
    ('sym', 'brass', 'plain', R(46, 39, 47, 42)),                                     # pommel
    ('sym', 'steel', 'plain', [(42, 13), (44, 10), (47, 9), (47, 21), (43, 21), (42, 18)]),    # helmet
    ('sym', 'dsteel', 'flat:2', [(43, 14), (47, 14), (47, 20), (44, 20)]),            # bellows visor
    ('sym', 'glow', 'flat:1', R(44, 15, 47, 15)),
    ('sym', 'glow', 'flat:2', R(44, 17, 47, 17)),
    ('sym', 'glow', 'flat:2', R(45, 19, 47, 19)),
    ('sym', 'brass', 'flat:0', R(47, 9, 47, 13)),                                     # crest ridge
]

CHARS = {'knight': KNIGHT, 'mage': MAGE, 'rogue': ROGUE, 'construct': CONSTRUCT}

if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    frames = []
    for name, parts in CHARS.items():
        im = render(parts, 64)
        im.save(f'out/{name}_1x.png')
        s = CONFIG['big_scale']
        im.resize((F * s, F * s), Image.NEAREST).save(f'out/{name}_{s}x.png')
        frames.append(im)
    F = 64
    k = render(KNIGHT96, 96)
    k.save('out/knight96_1x.png')
    k.resize((288, 288), Image.NEAREST).save('out/knight96_3x.png')
    F = 64
    line = Image.new('RGBA', (F * len(frames), F), CONFIG['lineup_bg'])
    for i, im in enumerate(frames):
        line.alpha_composite(im, (i * F, 0))
    line.save('out/lineup_1x.png')
    s = CONFIG['lineup_scale']
    line.resize((line.width * s, F * s), Image.NEAREST).save(f'out/lineup_{s}x.png')
