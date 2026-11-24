# Bronze guardian beast, round 3 (asset list C1; study art/Qin-Bronze-Castings-Study.md).
# Shape follows ComfyUI concept 2130 (owner pick 24 Nov 23:51; art/beast/concepts/, reference only, nothing traced): a compact seated
# guardian, frontal and massive; a big broad head (0.37 of the figure height) on a low neck; a collar of mane tufts under and around the
# face; forelegs built of stacked rings (read as segmented castings, with silver inlay bands between rings); big paws side by side.
# Measured on the concept (front view, 512 x 768): figure height H = 535 px; head 0.37 H; forehead width 0.48 H, mane collar 0.56 H;
# body 0.63 H; paws 0.61 H. Built from lofted rounded-square sections (superellipses), not spheres: round where round, sharp where
# sharp (owner 22:30). Material and ornament from the study and the klad bronze sheet (the concept reads as stone).
# Rounds 1 and 2 are kept in art/beast/round1/ and round2/.
#
# Output (one GLB, Y up, faces +Z in three.js): beast_lod0 skinned to a rigid rig (clips 'idle' 1 s, 'strike' with the 0.6 s windup tell),
# beast_lod1 and beast_lod2 static. Materials palBronze (trim sheet UVs at 256 px/m), palInlay (silver), palStone (plinth, world UVs).
# Usage: /home/claude/bpyenv/bin/python beast_blender.py OUT.glb
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/beast.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel width on sharp parts, m (cast chamfer; LOD0 only).
BEVEL = 0.02
# Faces meeting at more than this angle keep a hard edge on round parts (split normals), deg.
SHARP_DEG = 50
# Trim sheet: metres per UV unit (1024 px = 4 m) and rows in image pixels (art/tools/bronze_tex.py layout).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Plinth top height, m.
Z0 = 0.6
# Strike clip timing, s (windup = CONFIG.LION.windup, the 0.6 s tell); study gates: paw rise >= 0.4 m, jaw open >= 25 deg at the windup.
WINDUP, SWIPE, BACK = 0.6, 0.15, 0.5
PAW_RISE_MIN, JAW_DEG = 0.4, 30
FPS = 60
# Triangle budgets per LOD (palace study: 7k / 2.5k / 800).
BUDGET = (7000, 2500, 800)
# LOD2 decimate ratio of LOD1.
LOD2_RATIO = 0.3

# helpers -------------------------------------------------------------------------------------------------------------
def P(x, f, z):
    """design coords (x right, f forward, z up) -> Blender (forward = -Y, so the glTF faces +Z)."""
    return Vector((x, -f, z))

PARTS = []  # (object, bone, material, row, round)
Q = {'seg': 1.0}  # segment scale: 1 for LOD0, lower for LOD1

def put(name, bm, mat, bone, row, rnd):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, bone, mat, row, rnd))
    return ob

def spheroid(name, c, r, mat, bone, row='plain', tilt=0.0, segs=(14, 10), axis=None):
    """a rounded mass: UV sphere scaled to radii r=(x, f, z); tilt = forward lean in degrees; axis = flatten direction (design coords) for curls."""
    u = max(6, round(segs[0] * Q['seg'])); v = max(4, round(segs[1] * Q['seg']))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    S = Matrix.Diagonal((r[0], r[1], r[2], 1.0))
    R = Matrix.Rotation(math.radians(tilt), 4, 'X')
    if axis is not None:  # turn the sphere's local Y (its flat axis) to point along the given direction
        d = P(*axis) - P(0, 0, 0); R = d.to_track_quat('Y', 'Z').to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(P(*c)) @ R @ S, verts=bm.verts)
    return put(name, bm, mat, bone, row, True)

def prism(name, prof, a, b, mat, bone, row='plain', scale_b=1.0, rnd=False):
    """extrude a closed 2D profile from a to b (design coords); end cap scaled by scale_b. rnd True = smooth sides (a tapered tube)."""
    a, b = P(*a), P(*b); d = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + u * p[0] + v * p[1]) for p in prof]
    r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    n = len(prof)
    for i in range(n): bm.faces.new([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, rnd)

def tube(name, a, b, r0, r1, mat, bone, row='plain', sides=10):
    n = max(6, round(sides * Q['seg']))
    return prism(name, ngon(r0, n), a, b, mat, bone, row, r1 / r0, rnd=True)

def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def blade(w, t): return [(-w / 2, -t / 2), (w / 2, -t / 2), (0, t / 2)]  # a sharp sliver (claw, fang, ear) when tapered to a point

def loft(name, secs, mat, bone, row='plain', n_exp=2.6, M=24, cap=True):
    """a rounded-square mass lofted through sections (z, cf, hw, hd, cx) in design coords: superellipse rings (exponent n_exp: 2 = ellipse,
    higher = squarer), quads between rings, caps at both ends; smooth sides, hard caps."""
    M = max(10, round(M * Q['seg']))
    bm = bmesh.new(); rings = []
    for z, cf, hw, hd, cx in secs:
        ring = []
        for i in range(M):
            t = i * math.tau / M; c, sn = math.cos(t), math.sin(t)
            ring.append(bm.verts.new(P(cx + hw * math.copysign(abs(c) ** (2 / n_exp), c), cf + hd * math.copysign(abs(sn) ** (2 / n_exp), sn), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(M): bm.faces.new([a[i], a[(i + 1) % M], b[(i + 1) % M], b[i]])
    if cap: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, True)

def curl(name, c, r, axis, bone):
    """a cast spiral curl of the mane: a short disc with a sharp rim and a raised centre boss (round 3b: puffy lobes read as fur)."""
    a = Vector(axis).normalized(); c = Vector(c)
    prism(name, ngon(r, 9), tuple(c - a * 0.03), tuple(c + a * 0.03), 'palBronze', bone, 'clouds', rnd=True)  # hard rim from the cap angle, no bevel (budget)
    prism(name + '_boss', ngon(r * 0.45, 6), tuple(c + a * 0.03), tuple(c + a * 0.06), 'palBronze', bone, 'flange', scale_b=0.7, rnd=True)

# figure proportions (concept 2130, figure height FH on the plinth top)
FH = 2.1

def build(detail):
    PARTS.clear()
    # plinth: two stepped stone tiers (sharp; the collision footprint 1.8 x 2.2 m)
    prism('plinth_a', rect(1.8, 2.2), (0, 0, 0), (0, 0, 0.35), 'palStone', 'root')
    prism('plinth_b', rect(1.6, 2.0), (0, 0, 0.35), (0, 0, Z0), 'palStone', 'root')
    # body: one lofted rounded-square mass, haunches behind and low, chest high and forward (body width 0.63 FH = 1.32 m)
    loft('body', [(Z0, -0.22, 0.6, 0.72, 0), (Z0 + 0.25, -0.2, 0.66, 0.74, 0), (Z0 + 0.55, -0.14, 0.66, 0.66, 0),
                  (Z0 + 0.85, -0.04, 0.6, 0.54, 0), (Z0 + 1.1, 0.04, 0.54, 0.46, 0), (Z0 + 1.32, 0.08, 0.46, 0.38, 0)], 'palBronze', 'body')
    # haunch rolls on the flanks behind (the concept's stacked rolls), three per side
    for s in (-1, 1):
        for k in range(3):
            spheroid(f'roll_{s}{k}', (s * 0.6, -0.42 + k * 0.1, Z0 + 0.22 + k * 0.2), (0.12, 0.34, 0.1), 'palBronze', 'body', 'clouds', segs=(10, 6))
    # forelegs: four stacked rings each (segmented castings) with silver inlay bands between, from the chest down to the paws
    for s in (-1, 1):
        side = 'R' if s < 0 else 'L'; x = s * 0.3
        zs = [Z0 + 1.05, Z0 + 0.82, Z0 + 0.6, Z0 + 0.4, Z0 + 0.2]
        for k in range(4):
            z1, z0 = zs[k], zs[k + 1]; r = 0.2 - k * 0.006; bone = f'leg_{side}' if k < 2 else f'fore_{side}'
            loft(f'ring_{side}{k}', [(z0 + 0.01, 0.42, r * 0.86, r * 0.8, x), ((z0 + z1) / 2, 0.43, r, r * 0.93, x), (z1 - 0.01, 0.44, r * 0.86, r * 0.8, x)],
                 'palBronze', bone, 'flange' if k % 2 else 'plain', n_exp=2.2, M=18)
            if detail and k > 0:
                prism(f'band_{side}{k}', ngon(r * 0.9, 12), (x, 0.43, z1 + 0.012), (x, 0.43, z1 - 0.012), 'palInlay', bone)
        # paw: a rounded box reaching forward with four toe lobes and sharp claws
        loft(f'paw_{side}', [(Z0, 0.56, 0.2, 0.3, x), (Z0 + 0.1, 0.56, 0.22, 0.32, x), (Z0 + 0.2, 0.5, 0.18, 0.26, x)], 'palBronze', f'paw_{side}', n_exp=2.4, M=18)
        for k in range(4):
            tx = x + (k - 1.5) * 0.1
            spheroid(f'toe_{side}{k}', (tx, 0.82, Z0 + 0.09), (0.055, 0.07, 0.07), 'palBronze', f'paw_{side}', segs=(8, 5))
            if detail:
                prism(f'claw_{side}{k}', blade(0.05, 0.04), (tx, 0.88, Z0 + 0.07), (tx, 0.96, Z0 + 0.02), 'palInlay', f'paw_{side}', scale_b=0.1)
    # head: a broad rounded-square loft (0.37 FH tall), flat face plane, low neck
    HB = Z0 + 1.22
    loft('head', [(HB, 0.2, 0.42, 0.36, 0), (HB + 0.18, 0.18, 0.52, 0.42, 0), (HB + 0.44, 0.14, 0.5, 0.42, 0),
                  (HB + 0.62, 0.1, 0.44, 0.38, 0), (HB + 0.74, 0.07, 0.36, 0.3, 0), (HB + 0.82, 0.05, 0.22, 0.19, 0), (HB + 0.85, 0.04, 0.08, 0.07, 0)], 'palBronze', 'head', 'plain', n_exp=2.8)  # domed crown (round 3a: the flat cap read as a box)
    # muzzle and jaw (the jaw on its own bone for the strike tell), sharp nose wedge, sharp brow ridge, almond silver eyes, small round ears
    loft('muzzle', [(HB + 0.12, 0.5, 0.24, 0.16, 0), (HB + 0.22, 0.56, 0.26, 0.18, 0), (HB + 0.32, 0.52, 0.22, 0.14, 0)], 'palBronze', 'head', 'plain', n_exp=2.4, M=18)
    loft('jaw', [(HB - 0.16, 0.42, 0.15, 0.13, 0), (HB - 0.08, 0.5, 0.18, 0.15, 0), (HB - 0.02, 0.52, 0.17, 0.14, 0)], 'palBronze', 'jaw', 'lozenge', n_exp=2.2, M=16)  # round 3b: dropped open (a roar at rest; round 3 closed mouth read as a cat)
    loft('mouth', [(HB - 0.04, 0.46, 0.16, 0.08, 0), (HB + 0.04, 0.5, 0.2, 0.1, 0), (HB + 0.1, 0.48, 0.18, 0.09, 0)], 'palDark', 'head', 'plain', n_exp=2.2, M=14)
    prism('nose', [(-0.16, -0.05), (0.16, -0.05), (0.08, 0.07), (-0.08, 0.07)], (0, 0.68, HB + 0.3), (0, 0.78, HB + 0.22), 'palBronze', 'head', 'flange', scale_b=0.8)  # broad, flared
    prism('brow', [(-0.44, -0.02), (-0.06, -0.08), (0.06, -0.08), (0.44, -0.02), (0.4, 0.1), (0, 0.0), (-0.4, 0.1)], (0, 0.5, HB + 0.5), (0, 0.66, HB + 0.47), 'palBronze', 'head', 'flange')  # scowl: dips to the centre
    loft('bridge', [(HB + 0.3, 0.58, 0.09, 0.07, 0), (HB + 0.4, 0.57, 0.08, 0.06, 0), (HB + 0.5, 0.55, 0.1, 0.06, 0)], 'palBronze', 'head', 'plain', n_exp=2.2, M=12)
    for s in (-1, 1):
        spheroid(f'cheek_{s}', (s * 0.2, 0.55, HB + 0.22), (0.14, 0.09, 0.12), 'palBronze', 'head', 'plain', segs=(10, 6))
    for s in (-1, 1):
        spheroid(f'eye_{s}', (s * 0.17, 0.585, HB + 0.4), (0.075, 0.035, 0.045), 'palInlay', 'head', segs=(8, 5))  # round 3b: smaller, deep under the brow
        if detail:
            for k in (0.06, 0.13):
                prism(f'fang_{s}{k}', blade(0.06, 0.05), (s * k, 0.6, HB + 0.13), (s * k, 0.62, HB - 0.03), 'palInlay', 'head', scale_b=0.1)
                prism(f'lfang_{s}{k}', blade(0.05, 0.04), (s * k, 0.55, HB - 0.06), (s * k, 0.56, HB + 0.04), 'palInlay', 'jaw', scale_b=0.1)
    # mane collar: tuft lobes around the sides of the face and under the chin, then two rows down the back of the head and neck
    n = 15 if detail else 7
    for i in range(n):
        a = math.radians(-120 + 240 * i / (n - 1))  # 0 = under the chin, +-120 = up the sides of the face
        lx, lz = math.sin(a) * 0.56, -math.cos(a) * 0.34
        big = 1.25 if abs(a) < 0.8 else 1.0  # the ruff under the chin is the biggest part of the collar (concept 2130)
        curl(f'tuft_{i}', (lx, 0.42, HB + 0.3 + lz), 0.12 * big, (math.sin(a), 0.6, -math.cos(a)), 'head')
    for ri in range(2):
        m = 5 if detail else 2
        for i in range(m):
            a = math.radians(-80 + 160 * i / (m - 1))
            curl(f'mane_{ri}_{i}', (math.sin(a) * 0.4, -0.18 - ri * 0.12, HB + 0.5 - ri * 0.32), 0.13, (math.sin(a), -1, 0.2), 'head' if ri == 0 else 'body')
    # tail: round segments curling up the back, a sharp flame tuft
    pts = [(0, -0.9, Z0 + 0.15), (0, -0.98, Z0 + 0.45), (0, -0.92, Z0 + 0.8), (0, -0.82, Z0 + 1.0)]
    for i in range(3):
        tube(f'tail_{i}', pts[i], pts[i + 1], 0.09 - i * 0.012, 0.08 - i * 0.012, 'palBronze', f'tail_{i}', 'plain', sides=8)
    if detail:
        for k in (-1, 0, 1):
            prism(f'flame_{k}', blade(0.12, 0.04), (k * 0.06, -0.82, Z0 + 1.02), (k * 0.12, -0.74, Z0 + 1.24), 'palBronze', 'tail_2', 'flange', scale_b=0.1)

BONES = [('root', P(0, 0, 0), P(0, 0, Z0), None), ('body', P(0, -0.2, Z0 + 0.3), P(0, 0.08, Z0 + 1.2), 'root'),
         ('head', P(0, 0.15, Z0 + 1.2), P(0, 0.2, Z0 + 1.9), 'body'), ('jaw', P(0, 0.4, Z0 + 1.28), P(0, 0.6, Z0 + 1.28), 'head')]
for side, s in (('R', -1), ('L', 1)):
    x = s * 0.3
    BONES += [(f'leg_{side}', P(x, 0.42, Z0 + 1.05), P(x, 0.43, Z0 + 0.6), 'body'), (f'fore_{side}', P(x, 0.43, Z0 + 0.6), P(x, 0.44, Z0 + 0.2), f'leg_{side}'),
              (f'paw_{side}', P(x, 0.44, Z0 + 0.2), P(x, 0.9, Z0 + 0.05), f'fore_{side}')]
BONES += [('tail_0', P(0, -0.9, Z0 + 0.15), P(0, -0.98, Z0 + 0.45), 'body'), ('tail_1', P(0, -0.98, Z0 + 0.45), P(0, -0.92, Z0 + 0.8), 'tail_0'),
          ('tail_2', P(0, -0.92, Z0 + 0.8), P(0, -0.82, Z0 + 1.0), 'tail_1')]

def uv_trim(ob, row):
    """per-face planar UVs at 256 px/m on the dominant axis; v inside the part's trim-sheet row. glTF keeps image rows top-down (flipY false)."""
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    y0, y1 = ROWS.get(row, ROWS['plain']); h_img = (y1 - y0) / 1024.0
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        vmin = min(c[va] for c in cs); span = max(max(c[va] for c in cs) - vmin, 1e-6) / M_PER_UV
        k = min(1.0, h_img / span)
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (c[ua] / M_PER_UV, 1.0 - (y0 / 1024.0 + (c[va] - vmin) / M_PER_UV * k))

def uv_world(ob):
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = (c[ua] / M_PER_UV, c[va] / M_PER_UV)

def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

def finish(name, bevel):
    for ob, bone, mat, row, rnd in PARTS:
        if mat == 'palStone': uv_world(ob)
        else: uv_trim(ob, row)
        ob.data.materials.append(material(mat))
        vg = ob.vertex_groups.new(name=bone); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
        bm = bmesh.new(); bm.from_mesh(ob.data)
        if bevel and not rnd:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
        for f in bm.faces: f.smooth = rnd
        if rnd:  # hard edges only where faces fold sharply (tube caps); the rounded sides stay smooth
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
        bm.to_mesh(ob.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0][0]
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = FPS

Q['seg'] = 0.5; build(False); lod1 = finish('beast_lod1', False)
for vg in list(lod1.vertex_groups): lod1.vertex_groups.remove(vg)
build(False); lod2 = finish('beast_lod2', False)
for vg in list(lod2.vertex_groups): lod2.vertex_groups.remove(vg)
dm = lod2.modifiers.new('dec', 'DECIMATE'); dm.ratio = LOD2_RATIO
bpy.context.view_layer.objects.active = lod2; bpy.ops.object.modifier_apply(modifier='dec')
Q['seg'] = 1.0; build(True); lod0 = finish('beast_lod0', True)

bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = 'beast_rig'
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
for n, h, t, p in BONES:
    b = eb.new(n); b.head = h; b.tail = t
    if p: b.parent = eb[p]
bpy.ops.object.mode_set(mode='OBJECT')
lod0.parent = arm; mod = lod0.modifiers.new('arm', 'ARMATURE'); mod.object = arm

def paw_z(rot_leg, rot_fore):
    """world height of the right paw tip with the upper and lower leg rotated about their local X."""
    for b, rr in (('leg_R', rot_leg), ('fore_R', rot_fore)):
        pb = arm.pose.bones[b]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (rr, 0, 0)
    bpy.context.view_layer.update()
    z = (arm.matrix_world @ arm.pose.bones['paw_R'].tail).z
    for b in ('leg_R', 'fore_R'): arm.pose.bones[b].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    return z

r = math.radians
z_rest = paw_z(0, 0)
SIGN = 1 if paw_z(r(60), r(-50)) > paw_z(r(-60), r(50)) else -1  # which way lifts the paw forward-up (bone roll decides)
rise = paw_z(SIGN * r(75), -SIGN * r(55)) - z_rest

def jaw_tip_z(a):
    pb = arm.pose.bones['jaw']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (a, 0, 0); bpy.context.view_layer.update()
    z = (arm.matrix_world @ pb.tail).z; pb.rotation_euler = (0, 0, 0); bpy.context.view_layer.update(); return z
JS = 1 if jaw_tip_z(r(JAW_DEG)) < jaw_tip_z(-r(JAW_DEG)) else -1  # the snout end of the jaw must go down

def key(bone, f, rot):
    pb = arm.pose.bones[bone]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot; pb.keyframe_insert('rotation_euler', frame=f)

def clip(name, keys):
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for bone, frames in keys.items():
        for f, rot in frames: key(bone, f, rot)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act)
    arm.animation_data.action = None

f_w, f_s, f_b = 1 + round(WINDUP * FPS), 1 + round((WINDUP + SWIPE) * FPS), 1 + round((WINDUP + SWIPE + BACK) * FPS)
clip('strike', {
    'jaw': [(1, (0, 0, 0)), (f_w, (JS * r(JAW_DEG), 0, 0)), (f_s, (JS * r(JAW_DEG + 4), 0, 0)), (f_b, (0, 0, 0))],
    'leg_R': [(1, (0, 0, 0)), (f_w, (SIGN * r(75), 0, 0)), (f_s, (-SIGN * r(15), 0, 0)), (f_b, (0, 0, 0))],
    'fore_R': [(1, (0, 0, 0)), (f_w, (-SIGN * r(55), 0, 0)), (f_s, (SIGN * r(5), 0, 0)), (f_b, (0, 0, 0))],
})
clip('idle', {'tail_2': [(1, (0, 0, 0)), (31, (0, r(10), 0)), (61, (0, 0, 0))], 'tail_1': [(1, (0, 0, 0)), (31, (0, r(-5), 0)), (61, (0, 0, 0))]})

fails = 0; n_checks = 0
def gate(ok, line):
    global fails, n_checks
    n_checks += 1; fails += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + line)
for ob, lim in zip((lod0, lod1, lod2), BUDGET): gate(tris(ob) <= lim, f'{ob.name} tris {tris(ob)} (budget {lim})')
gate(all(v.groups for v in lod0.data.vertices), 'beast_lod0 every vertex on a bone')
gate(rise >= PAW_RISE_MIN, f'strike windup paw rise {rise:.2f} m (min {PAW_RISE_MIN})')
bb = [lod0.matrix_world @ Vector(c) for c in lod0.bound_box]
w, d, h = max(c.x for c in bb) - min(c.x for c in bb), max(c.y for c in bb) - min(c.y for c in bb), max(c.z for c in bb)
gate(h >= 2.6, f'height {h:.2f} m (min 2.6, box lion)')
gate(w <= 1.8 + 1e-6 and d <= 2.2 + 1e-6, f'footprint {w:.2f} x {d:.2f} m (max 1.8 x 2.2)')
share = sum(1 for p in lod0.data.polygons if p.use_smooth) / len(lod0.data.polygons)
gate(share >= 0.5, f'smooth-shaded share {share:.0%} (round forms, min 50%)')
print(f'{n_checks - fails} of {n_checks} pass')
lod1.location.x = 3; lod2.location.x = 6
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_nla_strips=True, export_materials='EXPORT', export_image_format='NONE')
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
