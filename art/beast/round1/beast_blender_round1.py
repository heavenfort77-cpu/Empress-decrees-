# Bronze guardian beast (asset list C1; owner 24 Nov 21:03: segmented bronze guardian beasts with silver inlay replace the stone lions).
# Our own design, built in headless Blender from hard planes (no sculpt, no scan, nothing traced). Rule list: a segmented casting with
# flanges at the joints, silver inlay as panel lines, stamp bands from the bronze trim sheet (assets/tex/bronze_trim.png), fresh
# brass-gold because it is a live hazard. Facing cues all point forward: head, chest plate, paws and claws in front; mane plates, haunches
# and the curled tail behind.
#
# Output (one GLB, Y up, faces +Z in three.js):
#   beast_lod0  skinned to a rigid rig (each segment 100% on one bone), clips 'idle' (1 s) and 'strike' (CONFIG.LION windup 0.6 s tell:
#               jaw opens, right paw rises; 0.15 s swipe; 0.5 s back)
#   beast_lod1  static, no bevels or small details
#   beast_lod2  static, decimated LOD1
# Materials: palBronze (trim sheet UVs, 256 px/m), palInlay (silver), palStone (plinth, the round 2 stone texture by world UVs).
# Usage: /home/claude/bpyenv/bin/python beast_blender.py OUT.glb
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/beast.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel width on every hard edge, m (cast chamfer; LOD0 only).
BEVEL = 0.025
# Texel density of the trim sheet, metres per UV unit (1024 px = 4 m).
M_PER_UV = 4.0
# Trim sheet rows in image pixels (bronze_tex.py layout): name -> (y0, y1).
ROWS = {'plain': (8, 376), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Strike clip timing, s (windup = CONFIG.LION.windup, the 0.6 s tell).
WINDUP, SWIPE, BACK = 0.6, 0.15, 0.5
FPS = 60
# LOD2 decimate ratio of LOD1.
LOD2_RATIO = 0.3

# helpers -------------------------------------------------------------------------------------------------------------
def P(x, f, z):
    """design coords (x right, f forward, z up) -> Blender (forward = -Y, so glTF +Z)."""
    return Vector((x, -f, z))

PARTS = []  # (object, bone, material, row)

def new_obj(name, bm, mat, bone, row):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, bone, mat, row))
    return ob

def prism(name, prof, a, b, mat, bone, row='plain', scale_b=1.0):
    """extrude a closed 2D profile (list of (u, v) in the plane normal to a->b) from point a to point b; the end cap scaled by scale_b."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + u * p[0] + v * p[1]) for p in prof]
    r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    n = len(prof)
    for i in range(n):
        bm.faces.new([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mat, bone, row)

def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def octo(w, h, c=0.3):
    cw, ch = w / 2 * c, h / 2 * c
    return [(-w / 2 + cw, -h / 2), (w / 2 - cw, -h / 2), (w / 2, -h / 2 + ch), (w / 2, h / 2 - ch), (w / 2 - cw, h / 2), (-w / 2 + cw, h / 2), (-w / 2, h / 2 - ch), (-w / 2, -h / 2 + ch)]
def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]

def build(detail):
    """the beast as parts; detail False drops the small pieces (LOD1)."""
    PARTS.clear()
    # plinth: two stepped tiers (stone; Qin stone pillar bases as the reference for a stone foot)
    prism('plinth_a', rect(1.8, 2.2), P(0, 0, 0), P(0, 0, 0.3), 'palStone', 'root')
    prism('plinth_b', rect(1.6, 2.0), P(0, 0, 0.3), P(0, 0, 0.5), 'palStone', 'root')
    # haunches (behind): octagonal blocks either side
    for s in (-1, 1):
        prism(f'haunch_{s}', octo(0.5, 0.62, 0.45), P(s * 0.34, -0.95, 0.82), P(s * 0.34, 0.05, 0.82), 'palBronze', 'body', 'plain', 0.9)
        prism(f'hindpaw_{s}', rect(0.3, 0.14), P(s * 0.42, -0.2, 0.57), P(s * 0.42, 0.25, 0.57), 'palBronze', 'body', 'plain')
    # torso core rising to the chest (seated posture), then three overlapping back plates (lamellar)
    prism('torso', octo(0.72, 0.6, 0.4), P(0, -0.55, 0.95), P(0, 0.3, 1.55), 'palBronze', 'body', 'plain', 0.92)
    for i, (f0, z0) in enumerate(((-0.6, 1.18), (-0.25, 1.42), (0.08, 1.66))):
        prism(f'backplate_{i}', rect(0.84, 0.08), P(0, f0, z0), P(0, f0 + 0.42, z0 + 0.2), 'palBronze', 'body', 'clouds')
    # chest plate (front): a shield with a ridge, stamped mask band; inlay ridge line
    prism('chest', [(-0.38, -0.32), (0.38, -0.32), (0.42, 0.2), (0, 0.36), (-0.42, 0.2)], P(0, 0.34, 1.38), P(0, 0.5, 1.38), 'palBronze', 'body', 'mask')
    if detail:
        prism('chest_inlay', rect(0.05, 0.6), P(0, 0.5, 1.4), P(0, 0.53, 1.4), 'palInlay', 'body')
    # forelegs (front, straight down): upper and lower tapered hexagonal segments, a flange at the elbow, a paw with claws
    for s in (-1, 1):
        side = 'R' if s < 0 else 'L'
        x = s * 0.27
        prism(f'upper_{side}', ngon(0.19, 6), P(x, 0.38, 1.5), P(x, 0.4, 1.02), 'palBronze', f'leg_{side}', 'plain', 0.85)
        prism(f'flange_{side}', ngon(0.21, 8, math.pi / 8), P(x, 0.4, 1.06), P(x, 0.4, 0.98), 'palBronze', f'fore_{side}', 'flange')
        prism(f'lower_{side}', ngon(0.15, 6), P(x, 0.4, 1.0), P(x, 0.42, 0.64), 'palBronze', f'fore_{side}', 'plain', 0.9)
        prism(f'paw_{side}', octo(0.3, 0.14, 0.4), P(x, 0.3, 0.57), P(x, 0.68, 0.57), 'palBronze', f'paw_{side}', 'lozenge')
        if detail:
            for k in (-1, 0, 1):
                prism(f'claw_{side}{k}', [(-0.03, -0.04), (0.03, -0.04), (0, 0.04)], P(x + k * 0.09, 0.66, 0.55), P(x + k * 0.09, 0.78, 0.53), 'palInlay', f'paw_{side}', scale_b=0.2)
            prism(f'legband_{side}', ngon(0.195, 8, math.pi / 8), P(x, 0.39, 1.3), P(x, 0.39, 1.25), 'palInlay', f'leg_{side}')
    # neck collar: an octagonal flange with an inlay ring
    prism('collar', ngon(0.4, 8, math.pi / 8), P(0, 0.42, 1.7), P(0, 0.46, 1.84), 'palBronze', 'head', 'flange')
    if detail:
        prism('collar_inlay', ngon(0.405, 8, math.pi / 8), P(0, 0.44, 1.76), P(0, 0.44, 1.79), 'palInlay', 'head')
    # head: a big square mask block, a heavy brow, the snout; separate jaw; round inlay eyes; swept-back ears; mane plates behind
    prism('head', octo(0.66, 0.5, 0.35), P(0, 0.32, 2.0), P(0, 0.82, 2.0), 'palBronze', 'head', 'mask', 0.9)
    prism('brow', [(-0.36, -0.05), (0.36, -0.05), (0.3, 0.07), (-0.3, 0.07)], P(0, 0.62, 2.17), P(0, 0.9, 2.15), 'palBronze', 'head', 'flange')
    prism('snout', octo(0.42, 0.22, 0.4), P(0, 0.8, 1.9), P(0, 1.06, 1.88), 'palBronze', 'head', 'plain', 0.85)
    prism('jaw', rect(0.38, 0.1), P(0, 0.55, 1.73), P(0, 1.0, 1.73), 'palBronze', 'jaw', 'lozenge', 0.85)
    if detail:
        for s in (-1, 1):
            prism(f'eye_{s}', ngon(0.07, 8), P(s * 0.16, 0.87, 2.05), P(s * 0.16, 0.9, 2.05), 'palInlay', 'head')
            for k in (0.09, 0.15):
                prism(f'fang_{s}{k}', [(-0.025, 0), (0.025, 0), (0, -0.01)], P(s * k, 1.0, 1.82), P(s * k, 1.0, 1.73), 'palInlay', 'head', scale_b=0.15)
    for s in (-1, 1):
        prism(f'ear_{s}', [(-0.1, 0), (0.1, 0), (0.0, 0.03)], P(s * 0.3, 0.5, 2.22), P(s * 0.38, 0.2, 2.36), 'palBronze', 'head', 'plain', 0.3)
    for i in range(4):  # mane: overlapping scale plates lying flat down the back of the neck (round 1 plates stuck out backward like spikes)
        f0, z0 = 0.34 - i * 0.17, 2.2 - i * 0.16
        prism(f'mane_{i}', rect(0.72 - i * 0.04, 0.06), P(0, f0, z0), P(0, f0 - 0.2, z0 - 0.17), 'palBronze', 'head' if i < 2 else 'body', 'clouds')
    # tail: four segments curling up behind, each with a small flange
    pts = [P(0, -1.0, 0.85), P(0, -1.18, 1.05), P(0, -1.22, 1.32), P(0, -1.1, 1.55), P(0, -0.95, 1.68)]
    for i in range(4):
        prism(f'tail_{i}', ngon(0.08 - i * 0.012, 6), pts[i], pts[i + 1], 'palBronze', f'tail_{i}', 'flange' if i % 2 else 'plain', 0.9)

BONES = [('root', P(0, 0, 0), P(0, 0, 0.5), None), ('body', P(0, -0.3, 0.9), P(0, 0.3, 1.5), 'root'),
         ('head', P(0, 0.4, 1.75), P(0, 0.9, 2.1), 'body'), ('jaw', P(0, 0.55, 1.73), P(0, 1.0, 1.73), 'head')]
for side, s in (('R', -1), ('L', 1)):
    x = s * 0.27
    BONES += [(f'leg_{side}', P(x, 0.38, 1.5), P(x, 0.4, 1.02), 'body'), (f'fore_{side}', P(x, 0.4, 1.02), P(x, 0.42, 0.64), f'leg_{side}'),
              (f'paw_{side}', P(x, 0.42, 0.62), P(x, 0.7, 0.57), f'fore_{side}')]
BONES += [('tail_0', P(0, -1.0, 0.85), P(0, -1.18, 1.05), 'body'), ('tail_1', P(0, -1.18, 1.05), P(0, -1.22, 1.32), 'tail_0'),
          ('tail_2', P(0, -1.22, 1.32), P(0, -1.1, 1.55), 'tail_1'), ('tail_3', P(0, -1.1, 1.55), P(0, -0.95, 1.68), 'tail_2')]

def uv_trim(ob, row):
    """per-face planar UVs at 256 px/m on the dominant axis; v placed inside the part's trim-sheet row (image rows -> Blender v = 1 - y)."""
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    y0, y1 = ROWS.get(row, ROWS['plain']); h_img = (y1 - y0) / 1024.0
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        vmin = min(c[va] for c in cs); vmax = max(c[va] for c in cs)
        span = max(vmax - vmin, 1e-6) / M_PER_UV
        k = min(1.0, h_img / span)  # keep the face inside its row (a band squeezes to fit a tall face)
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            u = c[ua] / M_PER_UV
            vi = y0 / 1024.0 + (c[va] - vmin) / M_PER_UV * k
            uvl.data[li].uv = (u, 1.0 - vi)

def uv_world(ob):
    """stone plinth: world-position UVs at 256 px/m like the game's palLion mapping."""
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (c[ua] / M_PER_UV, c[va] / M_PER_UV)

def material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    return m

def finish(name, bevel):
    """UVs, materials and bevels per part, then join every part into one mesh (vertex groups = bones)."""
    for ob, bone, mat, row in PARTS:
        (uv_world if mat == 'palStone' else uv_trim)(ob, row) if mat != 'palStone' else uv_world(ob)
        ob.data.materials.append(material(mat))
        vg = ob.vertex_groups.new(name=bone); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
        if bevel:
            bm = bmesh.new(); bm.from_mesh(ob.data)
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
            bm.to_mesh(ob.data); bm.free()
            for li, poly in enumerate(ob.data.polygons): poly.use_smooth = False
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0][0]
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = FPS

# LOD1 and LOD2 first (static), then LOD0 with the rig
build(False); lod1 = finish('beast_lod1', False)
for vg in list(lod1.vertex_groups): lod1.vertex_groups.remove(vg)
build(False); lod2 = finish('beast_lod2', False)
for vg in list(lod2.vertex_groups): lod2.vertex_groups.remove(vg)
dm = lod2.modifiers.new('dec', 'DECIMATE'); dm.ratio = LOD2_RATIO
bpy.context.view_layer.objects.active = lod2; bpy.ops.object.modifier_apply(modifier='dec')
build(True); lod0 = finish('beast_lod0', True)

bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = 'beast_rig'
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
for n, h, t, p in BONES:
    b = eb.new(n); b.head = h; b.tail = t
    if p: b.parent = eb[p]
bpy.ops.object.mode_set(mode='OBJECT')
lod0.parent = arm; mod = lod0.modifiers.new('arm', 'ARMATURE'); mod.object = arm

def key(bone, f, rot):
    pb = arm.pose.bones[bone]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot; pb.keyframe_insert('rotation_euler', frame=f)

def clip(name, keys):
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for bone, frames in keys.items():
        for f, rot in frames: key(bone, f, rot)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act)
    arm.animation_data.action = None

r = math.radians
f_w, f_s, f_b = 1 + round(WINDUP * FPS), 1 + round((WINDUP + SWIPE) * FPS), 1 + round((WINDUP + SWIPE + BACK) * FPS)
clip('strike', {
    'jaw': [(1, (0, 0, 0)), (f_w, (r(28), 0, 0)), (f_s, (r(30), 0, 0)), (f_b, (0, 0, 0))],
    'head': [(1, (0, 0, 0)), (f_w, (r(-8), 0, 0)), (f_s, (r(10), 0, 0)), (f_b, (0, 0, 0))],
    'leg_R': [(1, (0, 0, 0)), (f_w, (r(-70), 0, 0)), (f_s, (r(20), 0, 0)), (f_b, (0, 0, 0))],
    'fore_R': [(1, (0, 0, 0)), (f_w, (r(40), 0, 0)), (f_s, (r(-10), 0, 0)), (f_b, (0, 0, 0))],
})
clip('idle', {'tail_3': [(1, (0, 0, 0)), (31, (0, r(12), 0)), (61, (0, 0, 0))], 'tail_2': [(1, (0, 0, 0)), (31, (0, r(-6), 0)), (61, (0, 0, 0))]})

for ob, lim in ((lod0, 3000), (lod1, 1000), (lod2, 300)):
    print(f'{"PASS" if tris(ob) <= lim else "FAIL"} {ob.name} tris {tris(ob)} (budget {lim})')
unw = sum(1 for v in lod0.data.vertices if not v.groups)
print(f'{"PASS" if unw == 0 else "FAIL"} beast_lod0 unweighted vertices {unw}')
bb = [lod0.matrix_world @ Vector(c) for c in lod0.bound_box]
print('size m (x, depth, height):', round(max(c.x for c in bb) - min(c.x for c in bb), 2), round(max(c.y for c in bb) - min(c.y for c in bb), 2), round(max(c.z for c in bb), 2))
lod1.location.x = 3; lod2.location.x = 6  # side by side in the file; the game places them through THREE.LOD
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_nla_strips=True, export_materials='EXPORT', export_image_format='NONE')
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
