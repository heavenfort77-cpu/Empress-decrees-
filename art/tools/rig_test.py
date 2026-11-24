# CPU-only rigging test (no GPU): proves two routes in headless Blender (bpy 5.3).
# A) rigid segments: each cast bronze segment is bound 100% to one bone (no skinning model needed).
# B) automatic weights (Blender bone heat) on one smooth joined mesh.
# Both get a 1 s walk-like clip and are exported to GLB; the GLB is re-imported and checked.
import bpy, math, sys, os

OUT = os.path.dirname(os.path.abspath(__file__))

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def box(name, size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    return o

def armature(bones):
    # bones: list of (name, head, tail, parent)
    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm = bpy.context.active_object; arm.name = 'rig'
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm.data.edit_bones
    eb.remove(eb[0])
    for n, h, t, p in bones:
        b = eb.new(n); b.head = h; b.tail = t
        if p: b.parent = eb[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

# A four-legged beast: body, head, four legs (upper + lower). Units: metres, z up.
BONES = [('body', (0, 0, 1.0), (0, 0.8, 1.0), None), ('head', (0, 0.8, 1.2), (0, 1.3, 1.4), 'body')]
for side, x in (('L', 0.35), ('R', -0.35)):
    for end, y in (('f', 0.6), ('b', -0.6)):
        BONES.append((f'leg_{end}{side}', (x, y, 0.95), (x, y, 0.5), 'body'))
        BONES.append((f'shin_{end}{side}', (x, y, 0.5), (x, y, 0.05), f'leg_{end}{side}'))

def parts():
    ps = [('body', box('body', (0.9, 1.6, 0.5), (0, 0, 1.0))), ('head', box('head', (0.5, 0.6, 0.45), (0, 1.05, 1.3)))]
    for side, x in (('L', 0.35), ('R', -0.35)):
        for end, y in (('f', 0.6), ('b', -0.6)):
            ps.append((f'leg_{end}{side}', box(f'leg_{end}{side}', (0.22, 0.22, 0.45), (x, y, 0.72))))
            ps.append((f'shin_{end}{side}', box(f'shin_{end}{side}', (0.18, 0.18, 0.45), (x, y, 0.27))))
    return ps

def animate(arm):
    bpy.context.scene.frame_start = 1; bpy.context.scene.frame_end = 61; bpy.context.scene.render.fps = 60
    bpy.context.view_layer.objects.active = arm; bpy.ops.object.mode_set(mode='POSE')
    for f, s in ((1, 1), (31, -1), (61, 1)):
        for side, ph in (('L', 1), ('R', -1)):
            for end, e in (('f', 1), ('b', -1)):
                pb = arm.pose.bones[f'leg_{end}{side}']; pb.rotation_mode = 'XYZ'
                pb.rotation_euler = (math.radians(25) * s * ph * e, 0, 0); pb.keyframe_insert('rotation_euler', frame=f)
    bpy.ops.object.mode_set(mode='OBJECT')

def bind_rigid(arm, ps):
    for bone, o in ps:
        o.parent = arm
        vg = o.vertex_groups.new(name=bone); vg.add([v.index for v in o.data.vertices], 1.0, 'REPLACE')
        m = o.modifiers.new('arm', 'ARMATURE'); m.object = arm
    # one mesh per material in the game: join after binding (groups survive the join)
    bpy.ops.object.select_all(action='DESELECT')
    for _, o in ps: o.select_set(True)
    bpy.context.view_layer.objects.active = ps[0][1]; bpy.ops.object.join()
    return bpy.context.active_object

def bind_auto(arm, ps):
    bpy.ops.object.select_all(action='DESELECT')
    for _, o in ps: o.select_set(True)
    bpy.context.view_layer.objects.active = ps[0][1]; bpy.ops.object.join(); mesh = bpy.context.active_object
    # smooth one piece: remesh-free, subdivide so heat weights have vertices to spread over
    sub = mesh.modifiers.new('sub', 'SUBSURF'); sub.levels = 2
    bpy.ops.object.modifier_apply(modifier='sub')
    bpy.ops.object.select_all(action='DESELECT'); mesh.select_set(True); arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    return mesh

def check(mesh, label):
    vs = mesh.data.vertices; bad = 0; unw = 0
    for v in vs:
        s = sum(g.weight for g in v.groups)
        if not v.groups: unw += 1
        elif abs(s - 1) > 0.02: bad += 1
    print(f'{label}: verts {len(vs)} tris {sum(len(p.vertices) - 2 for p in mesh.data.polygons)} groups {len(mesh.vertex_groups)} unweighted {unw} sum!=1 {bad}')
    return unw

for mode in ('rigid', 'auto'):
    reset(); ps = parts(); arm = armature(BONES)
    mesh = bind_rigid(arm, ps) if mode == 'rigid' else bind_auto(arm, ps)
    if mode == 'auto':
        # normalise (heat weights can leave sums off 1); glTF keeps 4 influences
        bpy.context.view_layer.objects.active = mesh; bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.object.vertex_group_normalize_all(lock_active=False); bpy.ops.object.mode_set(mode='OBJECT')
    unw = check(mesh, mode)
    animate(arm)
    p = os.path.join(OUT, f'beast_{mode}.glb')
    bpy.ops.export_scene.gltf(filepath=p, export_format='GLB', export_animations=True)
    reset(); bpy.ops.import_scene.gltf(filepath=p)
    sk = [o for o in bpy.data.objects if o.type == 'MESH' and o.find_armature()]
    print(f'{mode}: GLB {os.path.getsize(p)} bytes, skinned meshes {len(sk)}, actions {len(bpy.data.actions)}, frames {[tuple(a.frame_range) for a in bpy.data.actions]}')
    print(f'RESULT {mode} ' + ('PASS' if unw == 0 and sk and bpy.data.actions else 'FAIL'))
