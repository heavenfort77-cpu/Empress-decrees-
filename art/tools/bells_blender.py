# 编钟 bell stand, round 1 (asset list C10, optional; study art/Qin-Bronze-Castings-Study.md "编钟 bell stand"). Core approach: gives the
# twelve bronze giants context (the First Emperor melted the realm's weapons into bells and the twelve 金人). No gameplay of its own.
# Qin first: Warring States 编钟 sets hang on a lacquered timber frame (簨虡: posts, an upper and a lower beam with bronze end fittings);
# small loop-hung bells (钮钟) on the upper beam, larger shank bells (甬钟) on the lower. Our own design: black-lacquer posts on cast
# bronze crouching-beast feet, beams with cinnabar bands and bronze dragon-head caps, almond-section bells (合瓦形) with a stamp band and
# a boss row from the trim sheet. Bells share one mesh per LOD (linked duplicates: glTF nodes reuse one mesh, so the game can draw them
# as one InstancedMesh). Reference only: ComfyUI round F job 1 (run 45446297299), nothing traced.
# Output: bells_lod0/1/2 (frame), bell_lod0_00.. / bell_lod1_00.. (shared bell meshes, children of their frame), LOD2 merged.
# Usage: /home/claude/bpyenv/bin/python bells_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, torus, loft, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/bells.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 incl. every bell drawn (asset list C10: 2k / 600).
BUDGET = (2000, 600, 250)
# Frame: half width m, post height, beam heights, beam section m.
HALF_W, POST_H, BEAMS, BEAM_S = 1.75, 2.7, (2.45, 1.55), (0.16, 0.2)
# Bells per beam (upper small, lower large): count, bell height m at the beam's centre and at its ends (sizes step down outward).
UPPER, LOWER = (6, 0.42, 0.3), (5, 0.8, 0.58)
# Footprint m (core approach; it stands against a wall).
FOOT = (4.4, 1.2)


def bell_mesh(name, detail):
    """one bell, 1 m tall, mouth at z 0, loop at the top: almond section (hd 0.62 of hw) flaring to an arched mouth."""
    K.PARTS.clear()
    secs = [(1.0, 0.0, 0.24, 0.15, 0.0), (0.78, 0.0, 0.3, 0.19, 0.0), (0.4, 0.0, 0.37, 0.23, 0.0), (0.06, 0.0, 0.42, 0.26, 0.0)]
    if not detail: secs = [secs[0], secs[2], secs[3]]
    loft('body', secs, 'palBronze', [(0.0, 0.38, 'mask'), (0.38, 0.8, 'lozenge'), (0.8, 1.1, 'flange')], n_exp=2.0, M=10 if detail else 6)
    if detail: sweep('loop', [(-0.08, 0, 1.0), (0.0, 0, 1.12), (0.08, 0, 1.0)], [0.03, 0.03, 0.03], 'palBronze', 'flange', n=4)
    if detail:  # the mouth's two arched points (于): sharp
        for s in (-1, 1): prism(f'tip_{s}', blade(0.1, 0.05), (s * 0.4, 0, 0.12), (s * 0.44, 0, -0.06), 'palBronze', 'flange', scale_b=0.2, rnd='flat')
    return K.finish(name)


def frame(detail):
    for s in (-1, 1):
        x = s * HALF_W
        loft(f'foot_{s}', [(0.0, 0.0, 0.42, 0.5, x), (0.18, 0.02, 0.36, 0.42, x), (0.34, 0.04, 0.2, 0.24, x), (0.42, 0.04, 0.12, 0.12, x)], 'palBronze', [(0.0, 0.2, 'mask'), (0.2, 0.5, 'clouds')], n_exp=2.3, M=10 if detail else 6)
        if detail:  # the crouching beast's head and horns on the front of each foot
            spheroid(f'head_{s}', (x, 0.42, 0.22), (0.16, 0.12, 0.13), 'palBronze', 'mask', sg=(6, 3))
            for h in (-1, 1): prism(f'horn_{s}{h}', blade(0.05, 0.04), (x + h * 0.08, 0.42, 0.32), (x + h * 0.16, 0.36, 0.48), 'palBronze', 'flange', scale_b=0.1, rnd='flat')
        lathe(f'post_{s}', [(0.1, 0.4), (0.09, POST_H)], 'palLacquerPlain', 'plain', n=8 if detail else 6, cx=x)
        cap = [(0.13, POST_H - 0.02), (0.13, POST_H + 0.06), (0.05, POST_H + 0.14), (0.0, POST_H + 0.15)]
        lathe(f'cap_{s}', cap if detail else [cap[0], cap[3]], 'palBronze', 'flange', n=8 if detail else 6, cx=x)
    for j, z in enumerate(BEAMS):
        prism(f'beam_{j}', rect(BEAM_S[0], BEAM_S[1]), (-HALF_W - 0.15, 0, z), (HALF_W + 0.15, 0, z), 'palLacquerPlain', 'plain')
        if detail:
            for k in (-1, 0, 1):  # cinnabar bands on the lacquer (decoration)
                prism(f'band_{j}{k}', rect(BEAM_S[0] + 0.01, BEAM_S[1] + 0.01), (k * 1.1 - 0.06, 0, z), (k * 1.1 + 0.06, 0, z), 'palCinnabar', 'plain', rnd='flat')
        for s in (-1, 1):  # bronze dragon-head end caps: a sleeve and a curled snout (sharp)
            x = s * (HALF_W + 0.15)
            prism(f'sleeve_{j}{s}', rect(BEAM_S[0] + 0.04, BEAM_S[1] + 0.04), (x - s * 0.22, 0, z), (x, 0, z), 'palBronze', 'flange', rnd='flat')
            if detail: sweep(f'snout_{j}{s}', [(x, 0, z), (x + s * 0.1, 0, z + 0.06), (x + s * 0.12, 0, z + 0.2)], [0.08, 0.06, 0.0], 'palBronze', 'flange', n=4, rnd='flat')


def places():
    out = []
    for (n, h0, h1), z in zip((UPPER, LOWER), BEAMS):
        for i in range(n):
            u = (i - (n - 1) / 2) / ((n - 1) / 2); x = u * (HALF_W - 0.4); h = h0 + (h1 - h0) * abs(u)
            out.append((x, z - BEAM_S[1] / 2 - h * 1.13, h))  # hang under the beam by the loop (loop top at 1.13 x the bell height)
    return out


K.reset()
bell0 = bell_mesh('bellmesh_lod0', True); bell1 = bell_mesh('bellmesh_lod1', False)
K.Q['seg'] = 0.5; frame(False); lod1 = K.finish('bells_lod1')
frame(False); lod2f = K.finish('bells_lod2')
K.Q['seg'] = 1.0; frame(True); lod0 = K.finish('bells_lod0', True)
inst = {0: [], 1: []}
for k, (x, z, h) in enumerate(places()):
    for lv, (src, parent) in enumerate(((bell0, lod0), (bell1, lod1))):
        ob = bpy.data.objects.new(f'bell_lod{lv}_{k:02d}' if lv else f'bell_{k:02d}', src.data); bpy.context.collection.objects.link(ob)
        ob.location = (x, 0, z); ob.scale = (h, h, h); ob.parent = parent; inst[lv].append(ob)
# LOD2: frame plus the LOD1 bells merged, decimated
bpy.ops.object.select_all(action='DESELECT')
copies = []
for k, (x, z, h) in enumerate(places()):
    me = bell1.data.copy(); ob = bpy.data.objects.new(f'b2_{k}', me); bpy.context.collection.objects.link(ob); ob.location = (x, 0, z); ob.scale = (h, h, h); copies.append(ob)
for ob in copies: ob.select_set(True)
bpy.context.view_layer.objects.active = copies[0]; bpy.ops.object.transform_apply(location=True, scale=True)
lod2f.select_set(True); bpy.context.view_layer.objects.active = lod2f; bpy.ops.object.join(); lod2 = bpy.context.active_object; lod2.name = 'bells_lod2'
K.decimate(lod2, 0.35)
for b in (bell0, bell1): bpy.data.objects.remove(b)  # the meshes stay (used by the instances)
lod0['instances'] = 'bell_NN nodes share one mesh (bellmesh_lod0): draw as one InstancedMesh'

G = K.Gates()
bt0, bt1 = K.tris(inst[0][0]), K.tris(inst[1][0]); nb = len(places())
d0 = K.tris(lod0) + bt0 * nb; d1 = K.tris(lod1) + bt1 * nb
G(d0 <= BUDGET[0], f'LOD0 drawn tris {d0} = frame {K.tris(lod0)} + {nb} bells x {bt0} (budget {BUDGET[0]})')
G(d1 <= BUDGET[1], f'LOD1 drawn tris {d1} = frame {K.tris(lod1)} + {nb} bells x {bt1} (budget {BUDGET[1]})')
G(K.tris(lod2) <= BUDGET[2], f'bells_lod2 tris {K.tris(lod2)} (budget {BUDGET[2]})')
shared = len({o.data.name for o in inst[0]}) == 1 and len({o.data.name for o in inst[1]}) == 1
G(shared, f'bells instanced: {nb} nodes per LOD share one mesh each ({inst[0][0].data.name}, {inst[1][0].data.name})')
bpy.context.view_layer.update()
lowest = min((o.matrix_world @ v.co).z for o in inst[0] for v in o.data.vertices)
G(lowest >= 0.2, f'lowest bell mouth {lowest:.2f} m above the floor (min 0.2: bells hang free)')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(x1 - x0 <= FOOT[0] and y1 - y0 <= FOOT[1], f'footprint {x1 - x0:.2f} x {y1 - y0:.2f} m (max {FOOT[0]} x {FOOT[1]}), height {z1:.2f} m')
G({'palLacquerPlain', 'palCinnabar', 'palBronze'} <= K.mats(lod0), 'black lacquer posts and beams, cinnabar bands, bronze feet, caps and bells')
G.done()
K.export(OUT, ((lod1, 0), (lod2, 0)))
