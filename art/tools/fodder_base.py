# Shared Blender base for the 皇家 guard and 反贼 rebel units (worker W5; study art/Guard-Rebels-Study.md).
# Helpers adapted from art/tools/beast_blender.py (loft, spheroid, prism, tube, trim UVs, rigid rig, NLA clips, LODs, gates) and
# art/tools/rig_test.py (automatic weights). One unit = one GLB: <key>_lod0 skinned (rigid segments; cloth by automatic weights),
# <key>_lod1 and <key>_lod2 static, clips idle / move / attack (attack windup = the CONFIG windup of the unit's move).
# Design coords: x right, f forward, z up (metres); the GLB faces +Z in three.js.
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel width on sharp parts, m (LOD0 only).
BEVEL = 0.012
# Faces meeting at more than this angle keep a hard edge on round parts, deg.
SHARP_DEG = 50
# Trim sheets: metres per UV unit (1024 px = 4 m).
M_PER_UV = 4.0
# Rows in image pixels: bronze_trim.png (art/tools/bronze_tex.py) and fodder_trim.png (art/tools/fodder_tex.py).
ROWS_BRONZE = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
ROWS_FODDER = {'lacquer': (8, 248), 'cord': (256, 320), 'blue': (320, 384), 'dark': (384, 448), 'yellow': (448, 512), 'hemp': (512, 704),
               'patch': (712, 824), 'plates': (832, 928), 'metal': (928, 960), 'rope': (960, 992), 'skin': (992, 1024)}
# Material -> sheet (bronze or fodder); materials not listed are plain colours in the viewer (glint).
SHEET = {'gdBronze': 'bronze', 'gdLacquer': 'fodder', 'rbCloth': 'fodder', 'rbPatch': 'fodder'}
# Clip frame rate.
FPS = 60
# Triangle budgets per LOD (task: about 4k / 1.5k / 500, drawn as instances).
BUDGET = (4000, 1500, 500)
# LOD1 segment scale; LOD2 decimate ratio of LOD1 (raised to stay in budget).
LOD1_SEG = 0.5
LOD2_RATIO = 0.3
# Tell gate: the weapon tip moves at least this far by the end of the windup, m (33 px at the fight framing).
TIP_MIN = 0.3

# helpers -------------------------------------------------------------------------------------------------------------
def P(x, f, z):
    k = Q['scale']; z = z + Q['zoff']
    z = Q['zpiv'] + (z - Q['zpiv']) * Q['zk']  # round 4 (guard): upper body stretched about the pivot; zk 1 (rebels) changes nothing
    return Vector((-x * k, -f * k, z * k))  # a proper rotation (x right of a figure facing +f): glTF faces +Z, right hand on -X

PARTS = []   # dict(ob, bone, mat, row, rnd, cloth, group)
def Pd(x, f, z): return Vector((-x, -f, z))  # a direction (no offset, no scale)

Q = {'seg': 1.0, 'detail': True, 'group': 'body', 'scale': 1.0, 'zoff': 0.0, 'zk': 1.0, 'zpiv': 0.0}

def put(name, bm, mat, bone, row, rnd, cloth=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append(dict(ob=ob, bone=bone, mat=mat, row=row, rnd=rnd, cloth=cloth, group=Q['group']))
    return ob

def spheroid(name, c, r, mat, bone, row, segs=(12, 8), tilt=0.0, cloth=False):
    u = max(6, round(segs[0] * Q['seg'])); v = max(4, round(segs[1] * Q['seg']))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(P(*c)) @ Matrix.Rotation(math.radians(tilt), 4, 'X') @ Matrix.Diagonal((r[0], r[1], r[2], 1.0)), verts=bm.verts)
    return put(name, bm, mat, bone, row, True, cloth)

def prism(name, prof, a, b, mat, bone, row, scale_b=1.0, rnd=False, up=None, cloth=False):
    """extrude a closed 2D profile (u = right of the a->b line, v = up) from a to b; end cap scaled by scale_b."""
    a, b = P(*a), P(*b); d = (b - a).normalized()
    upv = Vector(up) if up else (Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0)))
    u = d.cross(upv).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + u * p[0] + v * p[1]) for p in prof]
    r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    n = len(prof)
    for i in range(n): bm.faces.new([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, rnd, cloth)

def tube(name, a, b, r0, r1, mat, bone, row, sides=8, cloth=False):
    n = max(5, round(sides * Q['seg']))
    return prism(name, ngon(r0, n), a, b, mat, bone, row, r1 / r0, rnd=True, cloth=cloth)

def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def blade(w, t): return [(-w / 2, 0), (0, -t / 2), (w / 2, 0), (0, t / 2)]  # a diamond section: sharp edges both sides

def loft(name, secs, mat, bone, row, n_exp=2.4, M=16, cap=True, cloth=False):
    """rounded mass through sections (z, cf, hw, hd, cx) in design coords: superellipse rings, smooth sides."""
    M = max(8, round(M * Q['seg']))
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
    return put(name, bm, mat, bone, row, True, cloth)

def hloft(name, secs, mat, bone, row, n_exp=2.6, M=14, cap=True):
    """a lofted mass along the forward axis: sections (f, z, hw, hh, cx) -> rounded hulls and tread pods."""
    M = max(8, round(M * Q['seg']))
    bm = bmesh.new(); rings = []
    for f, z, hw, hh, cx in secs:
        ring = []
        for i in range(M):
            t = i * math.tau / M; c, sn = math.cos(t), math.sin(t)
            ring.append(bm.verts.new(P(cx + hw * math.copysign(abs(c) ** (2 / n_exp), c), f, z + hh * math.copysign(abs(sn) ** (2 / n_exp), sn))))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(M): bm.faces.new([a[i], a[(i + 1) % M], b[(i + 1) % M], b[i]])
    if cap: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, True)

def path_tube(name, pts, r, mat, bone, row, sides=6):
    """a tube along a polyline (bow, wheel rim, headband tails)."""
    for i in range(len(pts) - 1):
        tube(f'{name}_{i}', pts[i], pts[i + 1], r, r, mat, bone, row, sides)

# UVs and joining ------------------------------------------------------------------------------------------------------
def uv_trim(ob, rows):
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        y0, y1 = rows[poly.material_index] if isinstance(rows, list) else rows
        h_img = (y1 - y0) / 1024.0
        vmin = min(c[va] for c in cs); span = max(max(c[va] for c in cs) - vmin, 1e-6) / M_PER_UV
        k = min(1.0, h_img / span)
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (c[ua] / M_PER_UV, 1.0 - (y0 / 1024.0 + (c[va] - vmin) / M_PER_UV * k))

def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

ROW_IDS = {}  # 'mat/row' -> int, stored per face (attribute row_id) for the preview renderer

def row_id(mat, row):
    k = f'{mat}/{row}'
    if k not in ROW_IDS: ROW_IDS[k] = len(ROW_IDS)
    return ROW_IDS[k]

def prep(p, bevel):
    ob = p['ob']; sheet = SHEET.get(p['mat'])
    rows = ROWS_BRONZE if sheet == 'bronze' else ROWS_FODDER
    uv_trim(ob, rows.get(p['row'], list(rows.values())[0]))
    ob.data.materials.append(material(p['mat']))
    bm = bmesh.new(); bm.from_mesh(ob.data)
    if bevel and not p['rnd']:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
    for f in bm.faces: f.smooth = p['rnd']
    lay = bm.faces.layers.int.get('row_id') or bm.faces.layers.int.new('row_id'); rid = row_id(p['mat'], p['row'])
    for f in bm.faces: f[lay] = rid
    if p['rnd']:
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
    bm.to_mesh(ob.data); bm.free()

def join(obs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in obs: ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

# rig -----------------------------------------------------------------------------------------------------------------
def make_rig(name, bones):
    bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = name
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
    for bone in bones:
        n, h, t, p = bone[:4]; Q['zoff'] = bone[4] if len(bone) > 4 else 0.0; zk = Q['zk']; Q['zk'] = bone[5] if len(bone) > 5 else 1.0
        b = eb.new(n); b.head = P(*h); b.tail = P(*t); b.roll = 0.0
        Q['zoff'] = 0.0; Q['zk'] = zk
        if p: b.parent = eb[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm

def skin(arm, parts, name):
    """rigid parts: 100% on their bone; cloth parts: Blender bone heat (automatic weights), unsolved vertices fall back to the nearest bone.
    Returns the joined skinned mesh and the share of cloth vertices the bone heat solved."""
    rigid = [p['ob'] for p in parts if not p['cloth']]; cloth = [p['ob'] for p in parts if p['cloth']]
    for p in parts:
        if not p['cloth']:
            vg = p['ob'].vertex_groups.new(name=p['bone']); vg.add(list(range(len(p['ob'].data.vertices))), 1.0, 'REPLACE')
    solved = 1.0
    if cloth:
        c = join(cloth, name + '_cloth') if len(cloth) > 1 else cloth[0]
        bm = bmesh.new(); bm.from_mesh(c.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.002); bm.to_mesh(c.data); bm.free()
        bpy.ops.object.select_all(action='DESELECT'); c.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
        bpy.ops.object.parent_set(type='ARMATURE_AUTO')
        for m in list(c.modifiers): c.modifiers.remove(m)
        c.parent = None
        vs = c.data.vertices; got = sum(1 for v in vs if v.groups and sum(g.weight for g in v.groups) > 1e-3)
        solved = got / max(1, len(vs))
        heads = {b.name: (arm.matrix_world @ b.head_local, arm.matrix_world @ b.tail_local) for b in arm.data.bones}
        def near(co):
            best, bd = None, 1e9
            for n, (h, t) in heads.items():
                d = t - h; s = max(0.0, min(1.0, (co - h).dot(d) / max(d.length_squared, 1e-9))); dd = (h + d * s - co).length
                if dd < bd: best, bd = n, dd
            return best
        for v in vs:
            if not v.groups or sum(g.weight for g in v.groups) <= 1e-3:
                n = near(v.co); vg = c.vertex_groups.get(n) or c.vertex_groups.new(name=n); vg.add([v.index], 1.0, 'REPLACE')
        rigid.append(c)
    ob = join(rigid, name) if len(rigid) > 1 else rigid[0]
    ob.name = name; ob.data.name = name
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT'); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.vertex_group_limit_total(limit=4); bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    ob.parent = arm; mod = ob.modifiers.new('arm', 'ARMATURE'); mod.object = arm
    return ob, solved

def static(parts, name, ratio=None, limit=None):
    ob = join([p['ob'] for p in parts], name)
    for vg in list(ob.vertex_groups): ob.vertex_groups.remove(vg)
    if ratio:
        r = ratio
        for _ in range(8):
            dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = r
            dg = bpy.context.evaluated_depsgraph_get(); n = sum(len(p.vertices) - 2 for p in ob.evaluated_get(dg).data.polygons)
            if limit is None or n <= limit: break
            ob.modifiers.remove(dm); r *= 0.85
        bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='dec')
    return ob

# poses and clips -----------------------------------------------------------------------------------------------------
DIRS = {'fwd': (0, 1, 0), 'back': (0, -1, 0), 'up': (0, 0, 1), 'down': (0, 0, -1), 'right': (1, 0, 0), 'left': (-1, 0, 0)}

def rot_for(arm, bone, want, deg, probe=None):
    """euler (local XYZ) that turns the bone by deg so the probe point (design coords; default its tail) moves toward the design direction
    want. Picks the local axis whose rotation moves the probe most along want (rest pose, analytic)."""
    b = arm.data.bones[bone]; M = b.matrix_local; head = M.translation
    p = P(*probe) if probe else b.tail_local
    w = Pd(*DIRS[want]) if isinstance(want, str) else Pd(*want)
    best = None
    for i in range(3):
        ax = Vector(M.col[i][:3]).normalized(); vel = ax.cross(p - head)
        s = vel.dot(w)
        if best is None or abs(s) > abs(best[1]): best = (i, s)
    e = [0.0, 0.0, 0.0]; e[best[0]] = math.copysign(math.radians(deg), best[1])
    return tuple(e)

def addrot(*rs): return tuple(sum(r[i] for r in rs) for i in range(3))

def clip(arm, name, keys, loc=None, scl=None):
    """keys: {bone: [(t_seconds, euler)]}; loc: {bone: [(t, (x, f, z) offset in the bone's parent space, design axes)]};
    scl: {bone: [(t, s)]}. Pushed to its own NLA track (exported as one glTF animation)."""
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for bone, frames in keys.items():
        pb = arm.pose.bones[bone]; pb.rotation_mode = 'XYZ'
        for t, e in frames:
            pb.rotation_euler = e; pb.keyframe_insert('rotation_euler', frame=1 + round(t * FPS))
    for bone, frames in (loc or {}).items():
        pb = arm.pose.bones[bone]; Mi = arm.data.bones[bone].matrix_local.to_3x3().inverted()
        for t, o in frames:
            pb.location = Mi @ (Pd(*o) * Q['scale']); pb.keyframe_insert('location', frame=1 + round(t * FPS))
    for bone, frames in (scl or {}).items():
        pb = arm.pose.bones[bone]
        for t, s in frames:
            pb.scale = (s, s, s); pb.keyframe_insert('scale', frame=1 + round(t * FPS))
    for pb in arm.pose.bones: pb.rotation_euler = (0, 0, 0); pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    return act

def push(arm, act):
    tr = arm.animation_data.nla_tracks.new(); tr.name = act.name; tr.strips.new(act.name, 1, act)
    arm.animation_data.action = None

def tip_motion(arm, act, bone, t):
    """distance the bone's tail (the weapon tip) travels from frame 1 to time t of the action (other tracks muted)."""
    for tr in arm.animation_data.nla_tracks: tr.mute = True
    arm.animation_data.action = act; sc = bpy.context.scene
    sc.frame_set(1); a = (arm.matrix_world @ arm.pose.bones[bone].tail).copy()
    sc.frame_set(1 + round(t * FPS)); b = (arm.matrix_world @ arm.pose.bones[bone].tail).copy()
    peak = 0.0; peak_t = 0.0
    for f in range(1, 1 + round(t * FPS) + 30):
        sc.frame_set(f); d = ((arm.matrix_world @ arm.pose.bones[bone].tail) - a).length
        if d > peak + 1e-4 and f <= 1 + round(t * FPS) + 2: peak, peak_t = d, (f - 1) / FPS
    sc.frame_set(1); arm.animation_data.action = None
    for tr in arm.animation_data.nla_tracks: tr.mute = False
    return (b - a).length, peak_t

# preview dump (triangles in design coords + row ids; art/tools/fodder_preview.py draws them) --------------------------------
import numpy as np
def dump(obs, path, arm=None, act=None, t=0.0):
    if arm is not None:
        for tr in arm.animation_data.nla_tracks: tr.mute = True
        arm.animation_data.action = act
    bpy.context.scene.frame_set(1 + round(t * FPS)); dg = bpy.context.evaluated_depsgraph_get()
    T, R = [], []
    for ob in obs:
        ev = ob.evaluated_get(dg); me = ev.to_mesh(); me.calc_loop_triangles(); Mw = ob.matrix_world
        att = me.attributes.get('row_id')
        for lt in me.loop_triangles:
            T.append([tuple(Mw @ me.vertices[i].co) for i in lt.vertices]); R.append(att.data[lt.polygon_index].value if att else 0)
        ev.to_mesh_clear()
    T = np.array(T, dtype=np.float32); T = T * np.array([-1, -1, 1], dtype=np.float32)  # back to design coords (x, f, z)
    np.savez_compressed(path, tri=T, row=np.array(R, dtype=np.int16), rows=np.array(list(ROW_IDS)))
    bpy.context.scene.frame_set(1)
    if arm is not None:
        arm.animation_data.action = None
        for tr in arm.animation_data.nla_tracks: tr.mute = False

# gates ---------------------------------------------------------------------------------------------------------------
class Gates:
    def __init__(self, unit): self.unit = unit; self.rows = []
    def __call__(self, ok, line):
        self.rows.append((bool(ok), line)); print(('PASS ' if ok else 'FAIL ') + f'{self.unit} ' + line)
    def summary(self):
        n = len(self.rows); p = sum(1 for ok, _ in self.rows if ok); print(f'{self.unit}: {p} of {n} pass'); return p, n

def bounds(ob, exclude_bones=()):
    """world bounds of the skinned LOD0 at rest, optionally without the vertices of some bones (weapon, banner)."""
    skip = {g.index for g in ob.vertex_groups if g.name in exclude_bones}; pts = []
    for v in ob.data.vertices:
        if skip and v.groups and max(v.groups, key=lambda g: g.weight).group in skip: continue
        pts.append(ob.matrix_world @ v.co)
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

def build_unit(key, build, bones, clips_fn, out, extra_gates=None, weapons=None, extras=None):
    """build(detail) fills PARTS; bones = rig list; clips_fn(arm) -> {name: action}, plus the attack action and windup for the tip gate.
    weapons: optional {school: fn(detail)} built as separate skinned meshes on the 'weapon' bone (rebel 力士 variants)."""
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = FPS
    G = Gates(key)
    # LOD1 and LOD2 (static, no detail, lower segments)
    lods = []
    for k, (seg, ratio) in enumerate(((LOD1_SEG, None), (LOD1_SEG * 0.8, LOD2_RATIO))):
        PARTS.clear(); Q['seg'] = seg; Q['detail'] = False; Q['group'] = 'body'; Q['zoff'] = 0.0; Q['zk'] = 1.0; build(False); Q['zoff'] = 0.0; Q['zk'] = 1.0
        for p in PARTS: prep(p, False)
        lods.append(static(PARTS, f'{key}_lod{k + 1}', ratio, BUDGET[k + 1] if ratio else None))
    # LOD0
    PARTS.clear(); Q['seg'] = 1.0; Q['detail'] = True; Q['group'] = 'body'; Q['zoff'] = 0.0; Q['zk'] = 1.0; build(True); Q['zoff'] = 0.0; Q['zk'] = 1.0
    for p in PARTS: prep(p, True)
    arm = make_rig(f'{key}_rig', bones)
    for k, v in (extras or {}).items(): arm[k] = json.dumps(v, ensure_ascii=False)
    lod0, solved = skin(arm, list(PARTS), f'{key}_lod0')
    wobs = {}
    if weapons:
        for school, fn in weapons.items():
            for k, (seg, det) in enumerate(((1.0, True), (LOD1_SEG, False))):
                PARTS.clear(); Q['seg'] = seg; Q['detail'] = det; fn(det)
                for p in PARTS: prep(p, det)
                if k == 0:
                    w, _ = skin(arm, list(PARTS), f'{key}_w_{school}')
                else:
                    w = static(PARTS, f'{key}_w_{school}_lod1')
                wobs[(school, k)] = w
    acts, attack, windup, tipbone = clips_fn(arm)
    attack = attack or acts['attack']
    dist, peak_t = tip_motion(arm, attack, tipbone, windup)
    prev = os.path.join(os.path.dirname(out), 'preview'); os.makedirs(prev, exist_ok=True)
    base_w = [w for (s, k), w in wobs.items() if k == 0]
    for sch in ([None] if not wobs else [s for (s, k) in wobs if k == 0]):
        wl = [wobs[(sch, 0)]] if sch else []; tag = f'{key}_{sch}' if sch else key
        dump([lod0] + wl, os.path.join(prev, f'{tag}_rest.npz'), arm, acts['idle'], 0.0)
        dump([lod0] + wl, os.path.join(prev, f'{tag}_windup.npz'), arm, attack, windup)
        if sch:  # the weapon alone (the school's shape cue), for the variant silhouette gate
            for pose, a_, t_ in (('rest', acts['idle'], 0.0), ('windup', attack, windup)): dump(wl, os.path.join(prev, f'{tag}_wonly_{pose}.npz'), arm, a_, t_)
    for i, l in enumerate(lods): dump([l], os.path.join(prev, f'{key}_lod{i + 1}.npz'))
    for a in acts.values(): push(arm, a)
    # gates
    n0 = tris(lod0); wmax0 = max([tris(w) for (s, k), w in wobs.items() if k == 0] or [0]); wmax1 = max([tris(w) for (s, k), w in wobs.items() if k == 1] or [0])
    G(n0 + wmax0 <= BUDGET[0], f'lod0 tris {n0}' + (f' + weapon {wmax0}' if wobs else '') + f' (budget {BUDGET[0]})')
    G(tris(lods[0]) + wmax1 <= BUDGET[1], f'lod1 tris {tris(lods[0])}' + (f' + weapon {wmax1}' if wobs else '') + f' (budget {BUDGET[1]})')
    G(tris(lods[1]) <= BUDGET[2], f'lod2 tris {tris(lods[1])} (budget {BUDGET[2]}; weapons drop at LOD2)')
    allw = [lod0] + [w for (s, k), w in wobs.items() if k == 0]
    unw = sum(1 for o in allw for v in o.data.vertices if not v.groups or abs(sum(g.weight for g in v.groups) - 1) > 0.02)
    G(unw == 0, f'every lod0 vertex weighted, sum 1 ({unw} bad)')
    G(set(acts) >= {'idle', 'move', 'attack'}, f'clips {sorted(acts)}')
    G(windup >= 0.4, f'attack windup {windup:.2f} s (tell >= 0.4)')
    G(abs(peak_t - windup) <= 2.5 / FPS, f'weapon tip peaks at {peak_t:.2f} s = windup {windup:.2f} s')
    G(dist >= TIP_MIN, f'weapon tip moves {dist:.2f} m by the windup (min {TIP_MIN})')
    info = dict(solved=solved, tris=[n0, tris(lods[0]), tris(lods[1])], weapon_tris=[wmax0, wmax1], tip=dist, windup=windup)
    bpy.context.view_layer.update()
    if extra_gates: extra_gates(G, lod0, arm, info)
    p, n = G.summary()
    for i, l in enumerate(lods): l.location.x = 2.5 * (i + 1)
    for (s, k), w in wobs.items():
        if k == 1: w.location.x = 2.5; w.hide_set(False)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=out, export_format='GLB', export_animations=True, export_nla_strips=True, export_materials='EXPORT',
                              export_image_format='NONE', export_extras=True)
    print('wrote', out, os.path.getsize(out), 'bytes')
    return dict(unit=key, passed=p, checks=n, gates=[(ok, l) for ok, l in G.rows], **info)
