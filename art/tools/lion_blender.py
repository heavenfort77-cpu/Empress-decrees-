"""Palace stone lion (Empress Decrees), modelled in Blender by script. Our own design: a seated guardian lion of the Eastern Han
tomb-guardian type (bold, simple carving, chest out, curled mane knobs, tail curled up the back) on a plinth.

Same size and footprint as the box lion it replaces: 1.6 m wide (x) x 2.2 m deep (z) x about 2.6 m high (y), facing +z, origin at
the floor centre. Shape only: the game maps the klad stone texture (assets/tex/lion_stone.png) by world position.

Build: metaballs (positive for the body, negative for eyes and mouth), converted to a mesh, voxel remeshed, smoothed, decimated to
the target triangle counts (LOD0 / LOD1 / LOD2), plinth added as bevelled boxes, exported as GLB (Y up, no materials).

Run: python lion_blender.py OUTDIR   (with the bpy module, Blender 5.3)
"""
import math, sys, os
import bpy, bmesh
from mathutils import Vector

OUT = sys.argv[-1]
os.makedirs(OUT, exist_ok=True)
# Triangle targets per LOD (LOD0 close-up, LOD1 a few metres away, LOD2 far).
TRIS = {'lod0': 7000, 'lod1': 2500, 'lod2': 800}
PLINTH_H = 0.45

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

# Blender works Z-up; the glTF exporter turns Z-up into Y-up. So here: x = width, y = depth (front is -y, becomes +z in game), z = up.
mb = bpy.data.metaballs.new('lionMB')
mb.resolution = 0.03
mb.render_resolution = 0.03
mbo = bpy.data.objects.new('lionMB', mb)
scn.collection.objects.link(mbo)

def ball(x, y, z, r, kind='BALL', size=(1, 1, 1), neg=False, stiff=2.0, rot=None):
    e = mb.elements.new()
    e.type = kind
    e.co = (x, y, z)
    e.radius = r
    e.stiffness = stiff
    e.use_negative = neg
    if kind in ('ELLIPSOID', 'CAPSULE', 'CUBE'):
        e.size_x, e.size_y, e.size_z = size
    if rot is not None:
        e.rotation = rot
    return e

F = -1  # front direction along y (becomes +z in game)
Z0 = PLINTH_H  # the lion sits on the plinth top

# Han guardian proportions: compact and heavy, big chest, short thick legs, a big head set low in a ruff.
for sx in (-1, 1):
    ball(0.38 * sx, 0.45, Z0 + 0.42, 0.52, 'ELLIPSOID', (0.8, 1.1, 0.85))           # haunches (seated back legs)
    ball(0.42 * sx, 0.05, Z0 + 0.12, 0.27, 'ELLIPSOID', (0.8, 1.5, 0.55))           # back paws, flat on the plinth
ball(0, 0.15, Z0 + 0.78, 0.62, 'ELLIPSOID', (0.9, 1.1, 1.1))                        # torso
ball(0, -0.35, Z0 + 1.02, 0.62, 'ELLIPSOID', (1.0, 0.8, 1.15))                      # chest pushed out
for sx in (-1, 1):
    ball(0.3 * sx, -0.6, Z0 + 0.45, 0.23, 'CAPSULE', (0.3, 1, 1), rot=(0.7071, 0, 0.7071, 0))  # front legs, short pillars
    ball(0.3 * sx, -0.78, Z0 + 0.12, 0.25, 'ELLIPSOID', (1.0, 1.4, 0.6))            # front paws
    for k in (-1, 0, 1):
        ball(0.3 * sx + 0.1 * k, -1.0, Z0 + 0.08, 0.085)                              # toes
ball(0, -0.42, Z0 + 1.45, 0.64, 'ELLIPSOID', (1.1, 0.95, 0.95))                     # ruff (the mane mass)
hx = 0.06                                                                             # head turned a little to one side
ball(hx, -0.62, Z0 + 1.72, 0.48, 'ELLIPSOID', (1.05, 1.0, 0.95))                    # head
ball(hx, -0.95, Z0 + 1.6, 0.27, 'ELLIPSOID', (1.2, 1.0, 0.85))                      # muzzle
ball(hx, -0.95, Z0 + 1.42, 0.2, 'ELLIPSOID', (1.1, 0.9, 0.6))                       # lower jaw
ball(hx, -1.08, Z0 + 1.68, 0.09)                                                      # nose
for sx in (-1, 1):
    ball(hx + 0.3 * sx, -0.5, Z0 + 2.05, 0.12, 'ELLIPSOID', (1, 0.6, 1.2))          # ears
    ball(hx + 0.18 * sx, -0.93, Z0 + 1.8, 0.09, neg=True, stiff=2.5)                 # eye hollows (carved)
    ball(hx + 0.17 * sx, -0.95, Z0 + 1.89, 0.09, 'ELLIPSOID', (1.4, 0.6, 0.5))      # brow ridges
ball(hx, -1.08, Z0 + 1.5, 0.12, 'ELLIPSOID', (1.6, 0.8, 0.45), neg=True, stiff=3.0)  # open mouth (carved)
# mane curls: separate knobs half sunk into the ruff, around the back and sides of the head (no ring above the head)
for ring, (rz, rr, n) in enumerate([(Z0 + 1.2, 0.56, 7), (Z0 + 1.45, 0.6, 8), (Z0 + 1.7, 0.55, 7)]):
    for i in range(n):
        a = math.pi * (0.08 + 0.84 * (i + 0.5 * (ring % 2)) / n)
        ball(math.cos(a) * rr, -0.42 + math.sin(a) * rr * 0.8, rz, 0.12, stiff=3.0)
# tail: lying up the back, curled at the top
for i in range(14):
    t = i / 13
    ball(0.05, 0.68 - 0.08 * t, Z0 + 0.25 + 0.85 * t + 0.05 * math.sin(t * 6), 0.14 - 0.03 * t)
ball(0.05, 0.56, Z0 + 1.15, 0.17)                                                     # tail tuft

# metaballs -> mesh
dg = bpy.context.evaluated_depsgraph_get()
me = bpy.data.meshes.new_from_object(mbo.evaluated_get(dg))
body = bpy.data.objects.new('lion', me)
scn.collection.objects.link(body)
bpy.data.objects.remove(mbo)
bpy.context.view_layer.objects.active = body
body.select_set(True)

# clean surface: voxel remesh, then a light smooth
m = body.modifiers.new('remesh', 'REMESH'); m.mode = 'VOXEL'; m.voxel_size = 0.022
s = body.modifiers.new('smooth', 'SMOOTH'); s.factor = 0.5; s.iterations = 4
bpy.ops.object.modifier_apply(modifier='remesh'); bpy.ops.object.modifier_apply(modifier='smooth')

# keep only the biggest connected part (drops small loose bits), then cut at the plinth top (metaballs can dip under it)
bm = bmesh.new(); bm.from_mesh(body.data)
seen, parts = set(), []
for v in bm.verts:
    if v.index in seen: continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        u = stack.pop(); comp.append(u)
        for e in u.link_edges:
            w = e.other_vert(u)
            if w.index not in seen: seen.add(w.index); stack.append(w)
    parts.append(comp)
parts.sort(key=len, reverse=True)
print('islands', len(parts), 'kept', len(parts[0]), 'dropped verts', sum(len(c) for c in parts[1:]))
bmesh.ops.delete(bm, geom=[u for c in parts[1:] for u in c], context='VERTS')
bm.to_mesh(body.data); bm.free()
# keep only what stands above the plinth top (metaballs can dip under it)
bm = bmesh.new(); bm.from_mesh(body.data)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, 0, Z0 - 0.02), plane_no=(0, 0, 1), clear_inner=True)
bm.to_mesh(body.data); bm.free()

def tri_count(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)

def plinth():
    """two bevelled boxes: the plinth (1.6 x 2.2) and a thin step on it."""
    bm = bmesh.new()
    for (w, d, h, z) in ((1.6, 2.2, 0.3, 0.15), (1.4, 2.0, 0.15, 0.375)):
        r = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(w, d, h), verts=r['verts'])
        bmesh.ops.translate(bm, vec=(0, 0, z), verts=r['verts'])
    bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.025, segments=1, affect='EDGES')
    me = bpy.data.meshes.new('plinth'); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new('plinth', me); scn.collection.objects.link(o)
    return o

report = []
src = body.data.copy()
for lod, target in TRIS.items():
    o = bpy.data.objects.new('lion_' + lod, src.copy()); scn.collection.objects.link(o)
    pl = plinth()
    body_target = target - tri_count(pl)
    # triangulate, then decimate the body to its share
    bpy.ops.object.select_all(action='DESELECT'); bpy.context.view_layer.objects.active = o; o.select_set(True)
    t = o.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier='tri')
    ratio = min(1.0, body_target / max(1, tri_count(o)))
    d = o.modifiers.new('dec', 'DECIMATE'); d.ratio = ratio; bpy.ops.object.modifier_apply(modifier='dec')
    # join the plinth, smooth-shade the body only (the plinth keeps hard edges through split normals)
    pl.select_set(True); bpy.ops.object.join()
    for p in o.data.polygons:
        c = p.center
        p.use_smooth = c.z > PLINTH_H + 0.01
    t = o.modifiers.new('tri', 'TRIANGULATE'); bpy.ops.object.modifier_apply(modifier='tri')
    # export this LOD alone
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o
    path = os.path.join(OUT, f'lion_{lod}.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_materials='NONE', export_texcoords=False,
                              export_normals=True, export_yup=True, export_apply=True)
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    mn = [min(v[i] for v in bb) for i in range(3)]; mx = [max(v[i] for v in bb) for i in range(3)]
    report.append(f'{lod} tris {tri_count(o)} verts {len(o.data.vertices)} size x {mx[0]-mn[0]:.2f} depth {mx[1]-mn[1]:.2f} height {mx[2]-mn[2]:.2f} bytes {os.path.getsize(path)}')

# keep the Blender source for the owner
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'lion.blend'))
print('\n'.join(report))
