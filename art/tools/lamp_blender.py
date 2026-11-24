# Bronze lamp with mercury reflectors, round 1 (asset list C9; study art/Qin-Bronze-Castings-Study.md "Bronze lamp"). Halls and core; the
# game keeps 2-3 real lights, so a lamp's light is faked by emissive cards (a flame card and a soft halo card per dish), never a light.
# Qin first: the Warring States branched "tree" lamp (连盏灯: a stem with arms holding oil dishes on a round base). Our own design and a
# labelled invention: behind each flame a small dished reflector silvered with mercury (Qin tomb mercury lore; the only bright cool
# surface, material palMercRef = the mercury matcap A14), turned toward the room so the flame reads brighter and the lamp sparkles.
# Reference only: ComfyUI round F job 0 (run 45446297299), measured, nothing traced.
# Output: lamp_lod0/1/2 (static) and lamp_flames (cards: palFlame flame, palGlow halo; the 'lit' state, hidden when 'out').
# Usage: /home/claude/bpyenv/bin/python lamp_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, torus, ngon, rect, blade, disc

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/lamp.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (asset list C9: 500; lamps repeat, so LOD1 and LOD2 are small); cards counted apart.
BUDGET = (500, 200, 90)
CARD_MAX = 12
# Height and footprint, m (a hall wall is 4 m; a suit 2.05 m).
HEIGHT = (1.8, 2.4)
FOOT = 0.9
# Stem top z; arms: (angle deg around, start z on the stem, dish centre (radius out, z)); the top dish sits on the stem.
STEM_Z = 2.0
ARMS = [(45, 1.25, (0.42, 1.45)), (135, 1.25, (0.42, 1.45)), (225, 1.55, (0.36, 1.72)), (315, 1.55, (0.36, 1.72))]
# Dish radius, flame card height and width, halo card size, m; reflector radius and its offset behind the flame (toward the stem).
DISH_R, FLAME_H, FLAME_W, HALO = 0.09, 0.26, 0.14, 0.55
REF_R, REF_BACK = 0.12, 0.1
# Base profile (radius, z).
BASE = [(0.4, 0.0), (0.42, 0.05), (0.3, 0.14), (0.12, 0.22), (0.0, 0.24)]


def dishes():
    out = [(0.0, 0.0, STEM_Z + 0.02, 0.0)]
    for a, z0, (rr, z1) in ARMS: out.append((math.cos(math.radians(a)) * rr, math.sin(math.radians(a)) * rr, z1, math.radians(a)))
    return out


def build(detail):
    lathe('base', BASE, 'palBronze', [(0.0, 0.06, 'flange'), (0.06, 0.25, 'clouds')], n=8 if detail else 6)
    sweep('stem', [(0, 0, 0.22), (0, 0, 1.0), (0, 0, 1.6), (0, 0, STEM_Z)] if detail else [(0, 0, 0.22), (0, 0, STEM_Z)], [0.05, 0.035, 0.03, 0.035] if detail else [0.05, 0.035], 'palBronze', 'plain', n=5 if detail else 4)
    for i, ((a, z0, (rr, z1)), d) in enumerate(zip(ARMS, dishes()[1:])):
        c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
        pts = [(c * 0.03, sn * 0.03, z0), (c * rr * 0.55, sn * rr * 0.55, z0 + 0.22), (d[0], d[1], d[2] - 0.05)]
        sweep(f'arm_{i}', pts if detail else pts[::2], [0.025, 0.02, 0.022] if detail else [0.025, 0.022], 'palBronze', 'plain', n=4)
    for i, (x, f, z, a) in enumerate(dishes()):
        prof = [(0.03, z - 0.05), (DISH_R, z + 0.015), (0.0, z)] if detail else [(0.03, z - 0.05), (DISH_R, z + 0.015)]
        lathe(f'dish_{i}', prof, 'palBronze', 'flange', n=6, cx=x, cf=f)
        if detail or i == 0:  # mercury reflector: a small dished mirror behind the flame, facing out to the room, in a bronze rim
            ox, of = (-math.cos(a), -math.sin(a)) if i else (0.0, -1.0)
            rc = (x + ox * REF_BACK, f + of * REF_BACK, z + 0.14)
            n = Vector((-ox, -of, 0.15)).normalized()
            mirror_disc(f'ref_{i}', rc, n, REF_R, rim=detail)


def mirror_disc(name, c, n, r, rim=True):
    """a slightly dished mirror (centre 2 cm back, palMercRef) facing n (design coords) in a bronze rim band (back face closed)."""
    import bmesh
    N = 8; n = Vector(n).normalized(); u = n.cross(Vector((0, 0, 1))).normalized(); w = n.cross(u)
    ring = lambda rr, back: [Vector(c) + u * (math.cos(k * math.tau / N) * rr) + w * (math.sin(k * math.tau / N) * rr) - n * back for k in range(N)]
    bm = bmesh.new(); cen = bm.verts.new(P(*(Vector(c) - n * 0.02))); ri = [bm.verts.new(P(*v)) for v in ring(r * 0.85, 0.0)]
    for k in range(N): bm.faces.new([cen, ri[k], ri[(k + 1) % N]])
    for fc in bm.faces:
        fc.normal_update()
        if fc.normal.dot(P(*n) - P(0, 0, 0)) < 0: fc.normal_flip()
    K.put(name, bm, 'palMercRef', 'card', True)
    if not rim: return
    bm = bmesh.new(); a = [bm.verts.new(P(*v)) for v in ring(r * 0.85, 0.0)]; b = [bm.verts.new(P(*v)) for v in ring(r, -0.015)]; bk = [bm.verts.new(P(*v)) for v in ring(r, 0.03)]
    for k in range(N):
        k1 = (k + 1) % N; bm.faces.new([a[k], b[k], b[k1], a[k1]]); bm.faces.new([b[k], bk[k], bk[k1], b[k1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(name + '_rim', bm, 'palBronze', 'flange', 'flat')


def build_flames():
    """per dish: a flame card and a larger halo card, both upright and turned to the play camera (pitch 40)."""
    t = math.radians(40)
    for i, (x, f, z, a) in enumerate(dishes()):
        for nm, h, w, z0, mat in (('flame', FLAME_H, FLAME_W, z + 0.0, 'palFlame'), ('halo', HALO, HALO, z + FLAME_H * 0.5 - HALO / 2, 'palGlow')):
            c = Vector((x, f, z0)); up = Vector((0, -math.sin(t), math.cos(t))) * h; rt = Vector((w / 2, 0, 0))
            card(f'{nm}_{i}', [tuple(c - rt), tuple(c + rt), tuple(c + rt + up), tuple(c - rt + up)], mat)
    return K.finish('lamp_flames')


K.reset()
lod0, lod1, lod2 = K.lods('lamp', build, ratio2=0.5)
flames = build_flames()

G = K.Gates()
for ob, lim in zip((lod0, lod1, lod2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
nc = len(flames.data.polygons)
G(nc <= CARD_MAX and {'palFlame', 'palGlow'} <= K.mats(flames), f'light faked by cards: {nc} cards (max {CARD_MAX}), flame + halo per dish, no light object')
G(not [o for o in bpy.data.objects if o.type == 'LIGHT'], 'no lights in the file (game keeps 2-3 real lights)')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(x1 - x0 <= FOOT and y1 - y0 <= FOOT and HEIGHT[0] <= z1 <= HEIGHT[1], f'footprint {x1 - x0:.2f} x {y1 - y0:.2f} m (max {FOOT}), height {z1:.2f} m (range {HEIGHT})')
G('palMercRef' in K.mats(lod0) and 'palMercRef' in K.mats(lod1), f'mercury reflectors (palMercRef): {len(dishes())} on LOD0, the top one kept on LOD1')
G(min(d[2] for d in dishes()) >= 1.4, f'lowest flame {min(d[2] for d in dishes()):.2f} m: above a suit\'s shoulders, reads over a fight (min 1.4)')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
