# Shared helpers for the PIECES round (owner 25 Nov 13:08: art for everything still drawn as plain shapes: Kaymuse, the buff creatures,
# the small objects). Built on the approved prop pipeline (art/tools/prop_kit.py: lathe, loft, sweep, prism, torus, trim-sheet UVs, bevel,
# LODs, gates) and the guard rig pattern (art/tools/fodder_base.py: rigid parts 100% on one bone, clips on NLA tracks, LOD0 skinned,
# LOD1 and LOD2 static). Adds: a bone tag per part, whole-texture tile UVs (cloth, earth, timber, stone at 256 px/m), a curved shell
# (plates), part tilting, quaternion clips about design axes, and clip motion measures.
# Design coordinates as prop_kit: x right, f toward the camera (glTF +Z, the way a unit faces), z up. Run only inside Blender's Python.
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix, Quaternion
import prop_kit as K
from prop_kit import P

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Clip frame rate.
FPS = 30
# Whole-texture tile rows: metres per texture repeat (1024 px sheets at 256 px/m = 4 m; the 512 px cloth sheet = 2 m).
TILE_M = {'tile4': 4.0, 'tile2': 2.0}
# LOD2 decimate ratio of LOD1 when no budget forces a lower one.
LOD2_RATIO = 0.5

BONE = {'cur': 'root'}
# Which LOD is being built (0, 1, 2): builders drop parts by level, so LOD2 is built lean and keeps thin limbs (round 1: decimating LOD1
# to LOD2 ate the wanderer's legs and the wall's posts; decimation is now only the fallback when a LOD is over its budget).
LEVEL = {'n': 0}
_put = K.put

def _tagged_put(name, bm, mat, row, rnd):
    ob = _put(name, bm, mat, row, rnd); ob['bone'] = BONE['cur']; return ob

K.put = _tagged_put

def mutate(ns):
    """mutation runs (ci_art/job.sh): PIECES_MUT='NAME=value;NAME=value' overrides CONFIG values of the calling builder, so its gates can
    be shown to fail on a wrong build. Unset = nothing changes."""
    for kv in filter(None, os.environ.get('PIECES_MUT', '').split(';')):
        k, v = kv.split('=', 1); assert k in ns, k; ns[k] = eval(v); print('MUTATED', k, '=', v)

def bone(n):
    """parts built after this call ride on bone n (rigid, weight 1)."""
    BONE['cur'] = n

def uv_tile(ob, m):
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = (c[ua] / m, 1.0 - c[va] / m)

def finish(name, bevel=False, width=None):
    """as prop_kit.finish, plus tile rows and one vertex group per part (its bone); joins PARTS into one object. (Round 3's baked
    inside-out outline shell is removed: lead round 4, the outline is the game's own renderer outline, src/chars.js CHR.outline.)"""
    for ob, mat, row, rnd in K.PARTS:
        if ob.data.uv_layers: pass  # UVs made before a tilt (pre_uv)
        elif isinstance(row, str) and row in TILE_M: uv_tile(ob, TILE_M[row])
        else: K.uv_trim(ob, row)
        ob.data.materials.append(K.material(mat))
        bm = bmesh.new(); bm.from_mesh(ob.data)
        if bevel and rnd is False: bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width or K.BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
        for f in bm.faces: f.smooth = rnd is True
        if rnd is True:
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(K.SHARP_DEG): e.smooth = False
        bm.to_mesh(ob.data); bm.free()
        vg = ob.vertex_groups.new(name=ob['bone']); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in K.PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = K.PARTS[0][0]
    if len(K.PARTS) > 1: bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    K.PARTS.clear(); BONE['cur'] = 'root'
    return ob

def unskin(ob):
    for vg in list(ob.vertex_groups): ob.vertex_groups.remove(vg)
    return ob

def fit(ob, limit, ratio=1.0):
    """decimate to the ratio, then further until the triangle limit holds."""
    n = K.tris(ob)
    if n <= limit and ratio >= 1.0: return ob
    r = min(ratio, limit * 0.97 / max(n, 1))
    for _ in range(6):
        if r >= 0.999 and n <= limit: break
        K.decimate(ob, min(r, 0.999)); n = K.tris(ob)
        if n <= limit: break
        r = limit * 0.9 / n
    return ob

def pre_uv(obs):
    """trim UVs now, in the upright build pose (finish then leaves them alone): for parts tilted afterwards."""
    rows = {id(o): r for o, m, r, rn in K.PARTS}
    for ob in obs: K.uv_trim(ob, rows[id(ob)])

def tilt(obs, pivot, axis, deg):
    """rotate built parts about a design-coords axis through a design-coords pivot (a vessel hull laid at an angle)."""
    a = Vector((axis[0], -axis[1], axis[2])).normalized(); p = P(*pivot)
    M = Matrix.Translation(p) @ Matrix.Rotation(math.radians(deg), 4, a) @ Matrix.Translation(-p)
    for ob in obs: ob.data.transform(M); ob.data.update()

def shell(name, fn, nu, nv, mat, row='plain', rnd=True):
    """a curved cast plate: fn(u, v, k) -> design point, u and v in 0-1, k 0 = outer face, 1 = inner face; closed around the rim."""
    nu, nv = K.segs(nu, 3), K.segs(nv, 1); bm = bmesh.new()
    g = [[[bm.verts.new(P(*fn(i / nu, j / nv, k))) for j in range(nv + 1)] for i in range(nu + 1)] for k in (0, 1)]
    for i in range(nu):
        for j in range(nv):
            bm.faces.new([g[0][i][j], g[0][i + 1][j], g[0][i + 1][j + 1], g[0][i][j + 1]])
            bm.faces.new([g[1][i][j + 1], g[1][i + 1][j + 1], g[1][i + 1][j], g[1][i][j]])
    for i in range(nu):
        bm.faces.new([g[0][i][0], g[1][i][0], g[1][i + 1][0], g[0][i + 1][0]])
        bm.faces.new([g[0][i + 1][nv], g[1][i + 1][nv], g[1][i][nv], g[0][i][nv]])
    for j in range(nv):
        bm.faces.new([g[0][0][j + 1], g[1][0][j + 1], g[1][0][j], g[0][0][j]])
        bm.faces.new([g[0][nu][j], g[1][nu][j], g[1][nu][j + 1], g[0][nu][j + 1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return K.put(name, bm, mat, row, rnd)

def lods_static(prefix, build, budget):
    """LOD0 (full detail, bevels), LOD1 (half segments, no small parts), LOD2 (LOD1 decimated); all static."""
    LEVEL['n'] = 1; K.Q['seg'] = 0.5; build(False); l1 = unskin(finish(prefix + '_lod1')); fit(l1, budget[1])
    LEVEL['n'] = 2; K.Q['seg'] = 0.35; build(False); l2 = unskin(finish(prefix + '_lod2')); fit(l2, budget[2])
    LEVEL['n'] = 0; K.Q['seg'] = 1.0; build(True); l0 = unskin(finish(prefix + '_lod0', True))
    return l0, l1, l2

# rig and clips -------------------------------------------------------------------------------------------------------
def make_rig(name, bones):
    """bones: (name, head, tail, parent) in design coords."""
    bpy.ops.object.select_all(action='DESELECT')
    bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = name
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
    for n, h, t, p in bones:
        b = eb.new(n); b.head = P(*h); b.tail = P(*t); b.roll = 0.0
        if p: b.parent = eb[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def skin(arm, ob):
    names = {b.name for b in arm.data.bones}; stray = [g.name for g in ob.vertex_groups if g.name not in names]
    ob.parent = arm; mod = ob.modifiers.new('arm', 'ARMATURE'); mod.object = arm
    bad = sum(1 for v in ob.data.vertices if not v.groups or abs(sum(g.weight for g in v.groups) - 1) > 0.02)
    return stray, bad

def turn(arm, bname, axis, deg):
    """the bone-local quaternion for a turn of deg about a design-coords axis. Signs (figure facing +f): about x (1,0,0) positive = the
    front dips; about f (0,1,0) positive = the +x side lifts; about z (0,0,1) positive = the front swings toward +x."""
    M = arm.data.bones[bname].matrix_local.to_3x3(); a = Vector((axis[0], -axis[1], axis[2])).normalized()
    return (M.inverted() @ Matrix.Rotation(math.radians(deg), 3, a) @ M).to_quaternion()

def clip(arm, name, rot=None, loc=None):
    """rot: {bone: [(t_seconds, [(axis, deg), ...])]}; loc: {bone: [(t, (dx, df, dz))]} (offset in design axes).
    Quaternion keys, kept on one hemisphere (no sign flips)."""
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for b, frames in (rot or {}).items():
        pb = arm.pose.bones[b]; pb.rotation_mode = 'QUATERNION'; prev = None
        for t, rs in frames:
            q = Quaternion()
            for ax, dg in rs: q = turn(arm, b, ax, dg) @ q
            if prev is not None and q.dot(prev) < 0: q.negate()
            pb.rotation_quaternion = q; pb.keyframe_insert('rotation_quaternion', frame=1 + round(t * FPS)); prev = q.copy()
    for b, frames in (loc or {}).items():
        pb = arm.pose.bones[b]; Mi = arm.data.bones[b].matrix_local.to_3x3().inverted()
        for t, o in frames:
            pb.location = Mi @ Vector((o[0], -o[1], o[2])); pb.keyframe_insert('location', frame=1 + round(t * FPS))
    for pb in arm.pose.bones: pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0)
    return act

def wave(dur, n, fn):
    """n + 1 evenly spaced keys over dur seconds (first = last: a loop); fn(phase 0-1) -> key value."""
    return [(dur * i / n, fn((i % n) / n)) for i in range(n + 1)]

def assign(arm, act):
    """make act the armature's action, with its slot (slotted actions: an action without its slot plays nothing)."""
    arm.animation_data.action = act
    try:
        if getattr(arm.animation_data, 'action_slot', 1) is None and len(act.slots): arm.animation_data.action_slot = act.slots[0]
    except Exception as e: print('slot note:', e)

def motion(arm, act, bname, dur):
    """how far the bone's tail travels from its rest place over the clip (max, m), measured in its parent bone's space (so a moving body
    alone does not count as the limb moving: run 45554531198, the crab's legs frozen still passed on the body's sway), sampled every
    other frame, before the NLA push. A bone without a parent is measured in the armature's space."""
    sc = bpy.context.scene; assign(arm, act); b = arm.data.bones[bname]; best = 0.0
    rest = (b.parent.matrix_local.inverted() @ b.tail_local) if b.parent else b.tail_local.copy()
    for fr in range(1, 2 + round(dur * FPS), 2):
        sc.frame_set(fr); bpy.context.view_layer.update(); pb = arm.pose.bones[bname]
        cur = (pb.parent.matrix.inverted() @ pb.tail) if pb.parent else pb.tail
        best = max(best, (cur - rest).length)
    sc.frame_set(1)
    return best

def push(arm, acts):
    for act in acts:
        tr = arm.animation_data.nla_tracks.new(); tr.name = act.name; st = tr.strips.new(act.name, 1, act)
        try:
            if getattr(st, 'action_slot', 1) is None and len(act.slots): st.action_slot = act.slots[0]
        except Exception as e: print('slot note:', e)
    arm.animation_data.action = None
    for pb in arm.pose.bones: pb.rotation_quaternion = Quaternion(); pb.location = (0, 0, 0)

def export(path, extras=None, root=None):
    if extras and root is not None:
        for k, v in extras.items(): root[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_animations=True, export_nla_strips=True, export_materials='EXPORT',
                              export_image_format='NONE', export_extras=True)
    print('wrote', path, os.path.getsize(path), 'bytes')

def build_rigged(key, build, bones, clips_fn, out, budget, gap, extras=None, extra_gates=None):
    """build(detail) fills prop_kit.PARTS (each part tagged by bone()); clips_fn(arm) -> [(action, seconds, probe bone, min travel m)].
    Writes <key>_lod0 skinned to <key>_rig, <key>_lod1 and <key>_lod2 static (moved aside by gap, 2 x gap). Returns the gate fail count."""
    K.reset(); K.PARTS.clear(); bpy.context.scene.render.fps = FPS
    LEVEL['n'] = 1; K.Q['seg'] = 0.5; build(False); l1 = unskin(finish(f'{key}_lod1')); fit(l1, budget[1])
    LEVEL['n'] = 2; K.Q['seg'] = 0.35; build(False); l2 = unskin(finish(f'{key}_lod2')); fit(l2, budget[2])
    LEVEL['n'] = 0; K.Q['seg'] = 1.0; build(True); l0 = finish(f'{key}_lod0', True)
    arm = make_rig(f'{key}_rig', bones); stray, bad = skin(arm, l0)
    G = K.Gates()
    for ob, lim in zip((l0, l1, l2), budget): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
    G(not stray and bad == 0, f'{key} skin: every lod0 vertex on one rig bone ({bad} bad, stray groups {stray})')
    clips = clips_fn(arm)
    for act, dur, probe, lo in clips:
        d = motion(arm, act, probe, dur); G(d >= lo, f'{key} clip {act.name}: {dur:.1f} s, {probe} travels {d:.3f} m (min {lo})')
    if extra_gates: extra_gates(G, l0, l1, l2, arm)
    push(arm, [c[0] for c in clips])
    l1.location.x = gap; l2.location.x = 2 * gap
    fails = G.done()
    export(out, extras, arm)
    return fails
