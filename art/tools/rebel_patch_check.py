#!/usr/bin/env python3
"""Rebel colour and tell check (FIX-A, 25 Nov; owner: rebels use colours not used by the nine schools; the 死士 glint must read at play
size). Reads the CONFIG values from rebel_build.py and ding_blender.py as text (no Blender). Usage: python3 rebel_patch_check.py [--mutate]
Checks: every rebel patch colour is at least DE_SCHOOL (CIELAB 1976) from every school colour, both the W1a ding pigment mapping (owner
02:1x: the one mapping) and the game's current CONFIG.COL.schools; at least DE_HEMP from the hemp cloth (a patch must read as a patch);
the patch colours differ from each other by DE_SELF; the glint star is at least GLINT_PX pixels across at the fight framing."""
import ast, math, os, re, sys

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Minimum colour distances (CIELAB dE76): to any school colour, to the hemp cloth, between patch colours.
DE_SCHOOL, DE_HEMP, DE_SELF = 20.0, 15.0, 10.0
# The game's school colours today (index.html CONFIG.COL.schools, read only) and the hemp cloth preview colour (fodder_preview.py).
GAME_SCHOOLS = [0xb05a2a, 0xd5a03a, 0x6a6a6a, 0x8a2a3a, 0x3a3a3a, 0xe8e8f0, 0xc060a0, 0x40c0c0, 0x9a6ad5]
HEMP = 0x8f8068
# Glint readable size at the fight framing (110 px/m), px.
GLINT_PX, PX_PER_M = 60, 110

D = os.path.dirname(os.path.abspath(__file__))


def const(path, name):
    for node in ast.parse(open(path, encoding='utf-8').read()).body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name: return ast.literal_eval(node.value)
                if isinstance(t, ast.Tuple) and name in [e.id for e in t.elts if isinstance(e, ast.Name)]:
                    return ast.literal_eval(node.value)[[e.id for e in t.elts].index(name)]
    raise KeyError(name)


def lab(c):
    if isinstance(c, str): c = int(c.lstrip('#'), 16)
    rgb = [((c >> s) & 255) / 255 for s in (16, 8, 0)]
    rgb = [((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in rgb]
    X = (0.4124 * rgb[0] + 0.3576 * rgb[1] + 0.1805 * rgb[2]) / 0.95047; Y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    Z = (0.0193 * rgb[0] + 0.1192 * rgb[1] + 0.9505 * rgb[2]) / 1.08883
    f = lambda t: t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    return (116 * f(Y) - 16, 500 * (f(X) - f(Y)), 200 * (f(Y) - f(Z)))


def de(a, b): return math.dist(lab(a), lab(b))


def check(patch, accents, glint_w):
    rows = []; schools = [('ding ' + str(i), a) for i, a in enumerate(accents)] + [('game ' + str(i), g) for i, g in enumerate(GAME_SCHOOLS)]
    for c in patch:
        n, s = min(((n, de(c, s)) for n, s in schools), key=lambda t: t[1])
        rows.append((s >= DE_SCHOOL, f'patch #{c:06x}: nearest school colour ({n}) dE {s:.1f} (min {DE_SCHOOL})'))
        h = de(c, HEMP); rows.append((h >= DE_HEMP, f'patch #{c:06x}: dE {h:.1f} from the hemp (min {DE_HEMP})'))
    sd = min((de(a, b) for i, a in enumerate(patch) for b in patch[i + 1:]), default=99)
    rows.append((sd >= DE_SELF, f'patch colours apart from each other: min dE {sd:.1f} (min {DE_SELF})'))
    px = glint_w * PX_PER_M; rows.append((px >= GLINT_PX, f'死士 glint star {glint_w:.2f} m = {px:.0f} px at the fight framing (min {GLINT_PX})'))
    return rows


if __name__ == '__main__':
    patch = const(os.path.join(D, 'rebel_build.py'), 'PATCH_COL'); accents = const(os.path.join(D, 'ding_blender.py'), 'ACCENTS')
    gw = const(os.path.join(D, 'rebel_build.py'), 'GLINT_W')
    rows = check(patch, accents, gw)
    for ok, line in rows: print(('PASS ' if ok else 'FAIL ') + line)
    print(f'rebel patch check: {sum(ok for ok, _ in rows)} of {len(rows)} pass')
    if '--mutate' in sys.argv:
        muts = [('patch = ru ochre', [int(accents[0].lstrip('#'), 16)] + patch[1:], gw), ('patch = game cinnabar', patch[:1] + [0x8a2a3a] + patch[2:], gw),
                ('patch = hemp', patch[:2] + [HEMP], gw), ('two equal patches', [patch[0], patch[0], patch[2]], gw), ('round 5 glint 0.36 m', patch, 0.36)]
        caught = 0
        for name, p, g in muts:
            bad = [l for ok, l in check(p, accents, g) if not ok]; caught += bool(bad)
            print(('PASS ' if bad else 'FAIL ') + f'mutation {name} caught: {bad[0] if bad else "-"}')
        print(f'rebel patch mutations: {caught} of {len(muts)} caught')
