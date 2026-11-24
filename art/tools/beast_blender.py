# Bronze guardian beast, round 2 (asset list C1; study art/Qin-Bronze-Castings-Study.md).
# Owner 24 Nov 21:03: segmented bronze guardian beasts with silver inlay replace the stone lions. Owner 22:30: round where the form is
# round, sharp where it is sharp, never square and blocky. Our own design in headless Blender (no sculpt, scan or trace).
# Round: haunches, torso, chest, skull, cheeks, snout, paws, mane curls, tail (smooth-shaded spheroids and tapered tubes).
# Sharp: claws, fangs, ear tips, brow ridge, flanges, breast plate, collar, plinth (flat faces, bevelled, split normals).
# Pose: seated upright on a stone plinth (taller inside the same 1.8 x 2.2 m collision footprint). Facing cues forward: face, chest plate,
# front paws and claws; behind: mane curls, haunches, tail. Ears point up and out, never backward.
# Round 1 is kept in art/beast/round1/ (script, GLB, trim sheet).
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

def build(detail):
    PARTS.clear()
    # plinth: two stepped stone tiers (sharp)
    prism('plinth_a', rect(1.8, 2.2), (0, 0, 0), (0, 0, 0.35), 'palStone', 'root')
    prism('plinth_b', rect(1.6, 2.0), (0, 0, 0.35), (0, 0, Z0), 'palStone', 'root')
    # haunches and hind paws (round, behind)
    for s in (-1, 1):
        spheroid(f'haunch_{s}', (s * 0.36, -0.5, Z0 + 0.38), (0.3, 0.52, 0.4), 'palBronze', 'body', 'plain', tilt=-8, segs=(12, 8))
        spheroid(f'hindpaw_{s}', (s * 0.46, -0.06, Z0 + 0.09), (0.15, 0.24, 0.09), 'palBronze', 'body', 'plain', segs=(10, 6))
        if detail:
            for k in (-1, 0, 1):
                prism(f'hclaw_{s}{k}', blade(0.06, 0.05), (s * 0.46 + k * 0.07, 0.15, Z0 + 0.05), (s * 0.46 + k * 0.07, 0.25, Z0 + 0.02), 'palInlay', 'body', scale_b=0.1)
    # torso (round, leaning forward) and the chest mass
    spheroid('torso', (0, -0.15, Z0 + 0.85), (0.4, 0.4, 0.72), 'palBronze', 'body', 'plain', tilt=18)
    spheroid('chest', (0, 0.2, Z0 + 1.02), (0.42, 0.3, 0.42), 'palBronze', 'body', 'plain')
    # breast plate (sharp): a shield on the chest with the mask band; silver ridge line
    prism('breastplate', [(-0.3, -0.3), (0.3, -0.3), (0.34, 0.16), (0, 0.3), (-0.34, 0.16)], (0, 0.44, Z0 + 1.0), (0, 0.53, Z0 + 1.0), 'palBronze', 'body', 'mask')
    if detail:
        prism('breast_inlay', rect(0.07, 0.5), (0, 0.53, Z0 + 1.0), (0, 0.555, Z0 + 1.0), 'palInlay', 'body')
    # forelegs (round tubes, front), elbow flange (sharp), round paw with sharp claws
    for s in (-1, 1):
        side = 'R' if s < 0 else 'L'; x = s * 0.27
        tube(f'upper_{side}', (x, 0.34, Z0 + 1.02), (x, 0.4, Z0 + 0.46), 0.17, 0.14, 'palBronze', f'leg_{side}')
        prism(f'flange_{side}', ngon(0.19, 8, math.pi / 8), (x, 0.4, Z0 + 0.5), (x, 0.41, Z0 + 0.42), 'palBronze', f'fore_{side}', 'flange')
        tube(f'lower_{side}', (x, 0.41, Z0 + 0.44), (x, 0.45, Z0 + 0.16), 0.13, 0.12, 'palBronze', f'fore_{side}')
        spheroid(f'paw_{side}', (x, 0.52, Z0 + 0.12), (0.17, 0.25, 0.12), 'palBronze', f'paw_{side}', 'plain', segs=(12, 8))
        if detail:
            prism(f'legband_{side}', ngon(0.165, 10), (x, 0.37, Z0 + 0.8), (x, 0.375, Z0 + 0.74), 'palInlay', f'leg_{side}')
            for k in (-1, 0, 1):
                prism(f'claw_{side}{k}', blade(0.07, 0.06), (x + k * 0.085, 0.7, Z0 + 0.08), (x + k * 0.085, 0.82, Z0 + 0.02), 'palInlay', f'paw_{side}', scale_b=0.1)
    # collar (sharp octagonal flange) with a silver ring
    prism('collar', ngon(0.36, 8, math.pi / 8), (0, 0.3, Z0 + 1.32), (0, 0.42, Z0 + 1.4), 'palBronze', 'head', 'flange')
    if detail:
        prism('collar_inlay', ngon(0.365, 8, math.pi / 8), (0, 0.35, Z0 + 1.35), (0, 0.37, Z0 + 1.365), 'palInlay', 'head')
    # head: round skull, cheeks, snout and nose bump; sharp brow ridge; round silver eyes; jaw on its own bone; sharp fangs; ears up and out
    H = Z0 + 1.68
    spheroid('skull', (0, 0.52, H), (0.36, 0.34, 0.32), 'palBronze', 'head', 'plain')
    spheroid('snout', (0, 0.82, H - 0.14), (0.22, 0.2, 0.15), 'palBronze', 'head', 'plain', segs=(12, 8))
    prism('brow', [(-0.32, -0.04), (0.32, -0.04), (0.26, 0.06), (0, 0.02), (-0.26, 0.06)], (0, 0.74, H + 0.11), (0, 0.86, H + 0.08), 'palBronze', 'head', 'flange')
    spheroid('jaw', (0, 0.74, H - 0.3), (0.18, 0.22, 0.07), 'palBronze', 'jaw', 'lozenge', segs=(10, 6))
    for s in (-1, 1):
        prism(f'ear_{s}', blade(0.18, 0.05), (s * 0.26, 0.44, H + 0.24), (s * 0.4, 0.4, H + 0.42), 'palBronze', 'head', 'plain', scale_b=0.15)
    if detail:
        spheroid('nose', (0, 0.99, H - 0.08), (0.1, 0.06, 0.07), 'palBronze', 'head', 'plain', segs=(8, 6))
        for s in (-1, 1):
            spheroid(f'cheek_{s}', (s * 0.22, 0.66, H - 0.12), (0.14, 0.14, 0.12), 'palBronze', 'head', 'plain', segs=(10, 6))
            spheroid(f'eye_{s}', (s * 0.15, 0.84, H + 0.02), (0.075, 0.05, 0.065), 'palInlay', 'head', segs=(8, 6))
            for k in (0.07, 0.14):
                prism(f'fang_{s}{k}', blade(0.05, 0.04), (s * k, 0.95, H - 0.2), (s * k, 0.96, H - 0.32), 'palInlay', 'head', scale_b=0.1)
    # mane: rows of round curls on a shell behind and around the head and neck, each flattened outward
    rows = [(0.47, H + 0.02, 0.46, 9, 0.12), (0.34, H - 0.28, 0.44, 7, 0.13)] if detail else [(0.47, H + 0.02, 0.46, 6, 0.14), (0.34, H - 0.28, 0.44, 5, 0.15)]
    for ri, (fc, zc, rad, n, cr) in enumerate(rows):
        for i in range(n):
            a = math.radians(-110 + 220 * i / (n - 1))  # around the back: 0 = straight behind
            dx, df = math.sin(a), -math.cos(a)
            spheroid(f'curl_{ri}_{i}', (dx * rad, fc + df * rad * 0.8, zc + (0.1 if ri == 0 else 0)), (cr, 0.055, cr), 'palBronze', 'head' if ri == 0 else 'body', 'clouds',
                     segs=(8, 6), axis=(dx, df, 0.25))
    # tail: round segments curling up behind, a sharp flame tuft at the end
    pts = [(0, -0.9, Z0 + 0.3), (0, -1.0, Z0 + 0.55), (0, -0.98, Z0 + 0.85), (0, -0.88, Z0 + 1.05)]
    for i in range(3):
        tube(f'tail_{i}', pts[i], pts[i + 1], 0.09 - i * 0.012, 0.08 - i * 0.012, 'palBronze', f'tail_{i}', 'plain', sides=8)
    spheroid('tail_curl', (0, -0.86, Z0 + 1.1), (0.1, 0.1, 0.1), 'palBronze', 'tail_2', 'clouds', segs=(8, 6))
    if detail:
        for k in (-1, 0, 1):
            prism(f'tuft_{k}', blade(0.12, 0.04), (k * 0.06, -0.86, Z0 + 1.12), (k * 0.12, -0.78, Z0 + 1.34), 'palBronze', 'tail_2', 'flange', scale_b=0.1)

BONES = [('root', P(0, 0, 0), P(0, 0, Z0), None), ('body', P(0, -0.3, Z0 + 0.4), P(0, 0.2, Z0 + 1.2), 'root'),
         ('head', P(0, 0.36, Z0 + 1.36), P(0, 0.6, Z0 + 1.9), 'body'), ('jaw', P(0, 0.6, Z0 + 1.42), P(0, 0.92, Z0 + 1.38), 'head')]
for side, s in (('R', -1), ('L', 1)):
    x = s * 0.27
    BONES += [(f'leg_{side}', P(x, 0.34, Z0 + 1.02), P(x, 0.41, Z0 + 0.46), 'body'), (f'fore_{side}', P(x, 0.41, Z0 + 0.46), P(x, 0.45, Z0 + 0.16), f'leg_{side}'),
              (f'paw_{side}', P(x, 0.45, Z0 + 0.16), P(x, 0.8, Z0 + 0.06), f'fore_{side}')]
BONES += [('tail_0', P(0, -0.9, Z0 + 0.3), P(0, -1.0, Z0 + 0.55), 'body'), ('tail_1', P(0, -1.0, Z0 + 0.55), P(0, -0.98, Z0 + 0.85), 'tail_0'),
          ('tail_2', P(0, -0.98, Z0 + 0.85), P(0, -0.88, Z0 + 1.05), 'tail_1')]

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

Q['seg'] = 0.65; build(False); lod1 = finish('beast_lod1', False)
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
