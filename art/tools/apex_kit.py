# Shared Blender kit for the apex Tiger Demon and its cubs (W4, 25 Nov). Helpers adapted from art/tools/beast_blender.py (loft,
# spheroid, prism, tube, per-face trim-sheet UVs, rigid rig, NLA clips, LODs, gates), extended with:
# - Lofts along a path in design coords (x right, f forward, z up) with a surface sampler, so inlay lines (the tiger's stripes =
#   its crack lines) and sheddable plates can be laid exactly on a body surface.
# - Plates and organs as separate meshes parented to their own bones (the game detaches a plate by re-parenting its node).
# - Poses written as world-space deltas per bone (pitch = forward end up, yaw = nose to +x, location in metres), converted to
#   local bone quaternions; every clip keys every bone at every key time, so a clip fully defines the pose.
# Materials (names are the contract with the viewer and later the game): apexBronze (trim sheet UVs; awake = bronze_trim.png,
# dormant = apex_patina.png, same UVs), apexInlay (gold eyes, claws, fangs), apexCrack (inlay lines: dull gold asleep, glowing
# awake), apexOrgan (weak-point cores), apexDark (mouth).
import bpy, bmesh, math, os, json
from mathutils import Vector, Matrix, Quaternion
from mathutils.bvhtree import BVHTree

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Trim sheet: metres per UV unit (1024 px = 4 m, 256 px/m) and rows in image pixels (art/tools/bronze_tex.py layout).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Bevel width on sharp parts, m (cast chamfer; LOD0 only).
BEVEL = 0.015
# Faces meeting at more than this angle keep a hard edge on round parts, deg.
SHARP_DEG = 50
# Clip frame rate.
FPS = 60

S = {'scale': 1.0, 'seg': 1.0, 'detail': True}  # global scale of the model being built, segment scale per LOD, LOD0 details on/off
PARTS = []      # (object, bone, material, row, round)
EXTRA = []      # separate bone-parented objects: (object, bone, material, row, round)


def P(x, f, z):
    """design coords -> Blender (forward = -Y so the glTF faces +Z), times the model scale."""
    k = S['scale']; return Vector((x * k, -f * k, z * k))


def D(v):
    """Blender vector -> design coords (unscaled)."""
    k = S['scale']; return Vector((v.x / k, -v.y / k, v.z / k))


def seg(n, lo=4):
    return max(lo, round(n * S['seg']))


def _put(name, bm, mat, bone, row, rnd, sep=False):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    if sep: EXTRA.append((ob, bone, mat, row, rnd, name if sep is True else sep))
    else: PARTS.append((ob, bone, mat, row, rnd))
    return ob


def sel(n, e):
    return math.copysign(abs(n) ** (2 / e), n)


class Loft:
    """a rounded mass through sections along a path. pts: centres (x, f, z); sz: (hw, hh) per section. Ring frame: side = design x
    projected off the path tangent, v = side x tangent (up for a forward path, forward for a downward path). t = 0 side +x, 90 = v."""
    def __init__(self, pts, sz, n_exp=2.4):
        self.pts = [Vector(p) for p in pts]; self.sz = sz; self.e = n_exp

    def frame(self, s):
        n = len(self.pts); i = min(int(s), n - 2); u = s - i
        c = self.pts[i].lerp(self.pts[i + 1], u)
        a = self.pts[max(i - 1, 0)] if u < 0.5 and i > 0 else self.pts[i]
        b = self.pts[min(i + 2, n - 1)] if u >= 0.5 and i + 2 < n else self.pts[i + 1]
        d = (self.pts[i + 1] - self.pts[i]).normalized()
        if i > 0 and u < 0.5: d = (d + (self.pts[i] - self.pts[i - 1]).normalized() * (0.5 - u)).normalized()
        if i + 2 < n and u >= 0.5: d = (d + (self.pts[i + 2] - self.pts[i + 1]).normalized() * (u - 0.5)).normalized()
        side = Vector((1, 0, 0)); side = (side - d * side.dot(d)).normalized()
        v = side.cross(d).normalized()
        hw = self.sz[i][0] + (self.sz[i + 1][0] - self.sz[i][0]) * u; hh = self.sz[i][1] + (self.sz[i + 1][1] - self.sz[i][1]) * u
        return c, side, v, hw, hh, d

    def point(self, s, t_deg, off=0.0):
        """surface point (design coords) at path parameter s (0 .. n-1) and ring angle t, pushed out by off metres; and its outward dir."""
        c, side, v, hw, hh, d = self.frame(s); t = math.radians(t_deg)
        q = c + side * (hw * sel(math.cos(t), self.e)) + v * (hh * sel(math.sin(t), self.e))
        nrm = (side * (math.cos(t) / max(hw, 1e-3)) + v * (math.sin(t) / max(hh, 1e-3))).normalized()
        return q + nrm * off, nrm

    def s_at_f(self, f):
        """path parameter where the path's forward coordinate equals f (paths running along f)."""
        for i in range(len(self.pts) - 1):
            a, b = self.pts[i].y, self.pts[i + 1].y
            if min(a, b) <= f <= max(a, b) and a != b: return i + (f - a) / (b - a)
        return 0.0 if abs(f - self.pts[0].y) < abs(f - self.pts[-1].y) else len(self.pts) - 1.0


def loft(name, L, mat, bone, row='plain', M=24, cap=True, sub=1, sep=False):
    """mesh a Loft: M ring verts, sub rings between sections; smooth sides, capped ends."""
    M = seg(M, 8); bm = bmesh.new(); rings = []
    n = len(L.pts); steps = [i + k / sub for i in range(n - 1) for k in range(sub)] + [n - 1.0]
    for s in steps:
        rings.append([bm.verts.new(P(*L.point(s, i * 360.0 / M)[0])) for i in range(M)])
    for a, b in zip(rings, rings[1:]):
        for i in range(M): bm.faces.new([a[i], a[(i + 1) % M], b[(i + 1) % M], b[i]])
    if cap: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _put(name, bm, mat, bone, row, True, sep)


def floft(name, secs, mat, bone, row='plain', n_exp=2.4, M=24, cap=True, x=0.0, sub=1, sep=False):
    """loft along forward f: secs = (f, z, hw, hh); returns (object, Loft)."""
    L = Loft([(x, f, z) for f, z, _, _ in secs], [(hw, hh) for _, _, hw, hh in secs], n_exp)
    return loft(name, L, mat, bone, row, M, cap, sub, sep), L


def spheroid(name, c, r, mat, bone, row='plain', segs=(12, 8), axis=None, sep=False):
    """UV sphere scaled to radii r=(x, f, z); axis = direction (design) its local Y (flat axis) points to."""
    u = seg(segs[0], 6); v = seg(segs[1], 4)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    k = S['scale']; Sm = Matrix.Diagonal((r[0] * k, r[1] * k, r[2] * k, 1.0)); R = Matrix.Identity(4)
    if axis is not None:
        d = P(*axis) - P(0, 0, 0); R = d.to_track_quat('Y', 'Z').to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation(P(*c)) @ R @ Sm, verts=bm.verts)
    return _put(name, bm, mat, bone, row, True, sep)


def prism(name, prof, a, b, mat, bone, row='plain', scale_b=1.0, rnd=False, up=None, sep=False):
    """extrude a closed 2D profile (metres) from a to b (design coords); end cap scaled by scale_b."""
    a, b = P(*a), P(*b); d = (b - a).normalized(); k = S['scale']
    upv = (P(*up) - P(0, 0, 0)).normalized() if up else (Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, -1, 0)))
    u = d.cross(upv).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + (u * p[0] + v * p[1]) * k) for p in prof]
    r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * k * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1); n = len(prof)
    for i in range(n): bm.faces.new([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _put(name, bm, mat, bone, row, rnd, sep)


def tube(name, a, b, r0, r1, mat, bone, row='plain', sides=10, sep=False):
    return prism(name, ngon(r0, seg(sides, 6)), a, b, mat, bone, row, r1 / r0, rnd=True, sep=sep)


def ring(name, c, axis, r, w, mat, bone, row='flange', sides=14, sep=False):
    """a sharp flange ring (cast joint lip) of radius r and width w around axis at c."""
    a = Vector(axis).normalized(); c = Vector(c)
    return prism(name, ngon(r, seg(sides, 6)), tuple(c - a * w / 2), tuple(c + a * w / 2), mat, bone, row, rnd=True, sep=sep)


def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def blade(w, t): return [(-w / 2, -t / 2), (w / 2, -t / 2), (0, t / 2)]


def strip(name, L, pts_st, width, mat, bone, off=0.008, h=0.014, sep=False):
    """an inlay line laid on a Loft surface: pts_st = [(s, t_deg), ...] along the line; width in metres; raised h above the surface.
    Built as a closed ribbon (top, bottom and walls) so it reads from any side."""
    bm = bmesh.new(); top, bot = [], []
    qs = [L.point(s, t, off) for s, t in pts_st]; n = len(qs)
    for k, (q, nrm) in enumerate(qs):
        q2 = qs[min(k + 1, n - 1)][0]; q0 = qs[max(k - 1, 0)][0]
        tan = (q2 - q0).normalized() if (q2 - q0).length > 1e-6 else Vector((0, 1, 0))
        wv = nrm.cross(tan).normalized() * (width / 2)
        top += [bm.verts.new(P(*(q + wv + nrm * h))), bm.verts.new(P(*(q - wv + nrm * h)))]
        bot += [bm.verts.new(P(*(q + wv - nrm * 0.004))), bm.verts.new(P(*(q - wv - nrm * 0.004)))]
    n = len(pts_st)
    for k in range(n - 1):
        a, b, c, d = top[2 * k], top[2 * k + 1], top[2 * k + 3], top[2 * k + 2]
        bm.faces.new([a, b, c, d])
        if S['detail']:
            for X in (0, 1):
                bm.faces.new([top[2 * k + X], top[2 * k + 2 + X], bot[2 * k + 2 + X], bot[2 * k + X]])
    if S['detail']:
        bm.faces.new([top[0], bot[0], bot[1], top[1]]); bm.faces.new([top[-2], top[-1], bot[-1], bot[-2]])
    else:
        for v in bot: bm.verts.remove(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _put(name, bm, mat, bone, 'inlay', False, sep)


def shell(name, L, s0, s1, t0, t1, out, thick, mat, bone, row='plain', ns=6, nt=6, sep=True):
    """a cast plate: a patch of the Loft surface between (s0..s1, t0..t1) lifted out by `out`, `thick` metres thick, with walls."""
    ns = seg(ns, 2); nt = seg(nt, 2); bm = bmesh.new(); O, I = [], []
    for i in range(ns + 1):
        s = s0 + (s1 - s0) * i / ns; ro, ri = [], []
        for j in range(nt + 1):
            t = t0 + (t1 - t0) * j / nt
            ro.append(bm.verts.new(P(*L.point(s, t, out + thick)[0]))); ri.append(bm.verts.new(P(*L.point(s, t, out)[0])))
        O.append(ro); I.append(ri)
    for i in range(ns):
        for j in range(nt):
            bm.faces.new([O[i][j], O[i + 1][j], O[i + 1][j + 1], O[i][j + 1]])
            bm.faces.new([I[i][j], I[i][j + 1], I[i + 1][j + 1], I[i + 1][j]])
    edge = [(i, 0) for i in range(ns)] + [(ns, j) for j in range(nt)] + [(i, nt) for i in range(ns, 0, -1)] + [(0, j) for j in range(nt, 0, -1)]
    for k in range(len(edge)):
        (a1, b1), (a2, b2) = edge[k], edge[(k + 1) % len(edge)]
        bm.faces.new([O[a1][b1], I[a1][b1], I[a2][b2], O[a2][b2]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _put(name, bm, mat, bone, row, True, sep)


def tread(name, loop, x0, x1, bone, cap_mat='apexBronze', cap_row='lozenge', thick=None):
    """a scrolling tread belt (tread_kit.py): band faces on material treadBelt with belt UVs, flat side caps on the trim sheet.
    Returns the belt's metres per texture repeat."""
    import tread_kit as T
    G = T.geometry(loop, x0, x1, thick, seg=S['seg'])
    band, caps = T.build_bm(G, P, T.outward_for(G, loop, x0, x1))
    _put(name + '_belt', band, 'treadBelt', bone, 'tread', True)
    if caps is not None:
        _put(name + '_caps', caps, cap_mat, bone, cap_row, False)
    return G['mpr']


# UVs, materials, joining ---------------------------------------------------------------------------------------------
def uv_trim(ob, row):
    """per-face planar UVs at 256 px/m on the dominant axis; v inside the part's trim-sheet row (glTF image rows top-down)."""
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


def material(name):
    return bpy.data.materials.get(name) or bpy.data.materials.new(name)


def _prep(ob, bone, mat, row, rnd, bevel):
    if row != 'tread': uv_trim(ob, row)  # tread belts keep their own scrolling UVs (tread_kit.py)
    ob.data.materials.append(material(mat))
    vg = ob.vertex_groups.new(name=bone); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
    bm = bmesh.new(); bm.from_mesh(ob.data)
    if bevel and not rnd and len(bm.faces) > 4:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL * S['scale'], segments=1, affect='EDGES', clamp_overlap=True)
    for f in bm.faces: f.smooth = rnd
    if rnd:
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
    bm.to_mesh(ob.data); bm.free()


def finish(name, bevel):
    """UV, material and one vertex group per part, then join PARTS into one mesh `name`. EXTRA parts are prepared but kept separate
    (renamed with the LOD suffix by the caller)."""
    for ob, bone, mat, row, rnd in PARTS: _prep(ob, bone, mat, row, rnd, bevel)
    for ob, bone, mat, row, rnd, grp in EXTRA: _prep(ob, bone, mat, row, rnd, bevel)
    ob = _join([o for o, *_ in PARTS], name)
    groups = {}
    for o, b, *_, grp in EXTRA: groups.setdefault(grp, (b, []))[1].append(o)
    extra = [(_join(obs, grp), b) for grp, (b, obs) in groups.items()]  # one node per plate / organ (its stripes, mark, ring joined)
    PARTS.clear(); EXTRA.clear()
    return ob, extra


def _join(obs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    if len(obs) > 1: bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob


def decimate(ob, ratio):
    dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = ratio
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='dec')
    ob.data.validate(clean_customdata=False)  # drop degenerate faces left by the collapse (glTF exporter warned on howler_lod2)


def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# Rig -------------------------------------------------------------------------------------------------------------------
def make_rig(name, bones):
    """bones: [(name, head (design), tail (design), parent)] in parent-first order."""
    bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = name
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
    for n, h, t, p in bones:
        b = eb.new(n); b.head = P(*h); b.tail = P(*t)
        if p: b.parent = eb[p]
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def skin(ob, arm):
    ob.parent = arm; m = ob.modifiers.new('arm', 'ARMATURE'); m.object = arm


def bone_parent(ob, arm, bone):
    """parent a separate part to a bone and keep it where it is (vertices stay in world coords via the parent inverse)."""
    for vg in list(ob.vertex_groups): ob.vertex_groups.remove(vg)
    mw = ob.matrix_world.copy()
    ob.parent = arm; ob.parent_type = 'BONE'; ob.parent_bone = bone
    bpy.context.view_layer.update(); ob.matrix_world = mw


def _rot(p=0.0, y=0.0, r=0.0):
    rr = math.radians
    return (Matrix.Rotation(rr(y), 3, 'Z') @ Matrix.Rotation(-rr(p), 3, 'X') @ Matrix.Rotation(rr(r), 3, 'Y'))


def local_pose(arm, spec):
    """spec: {bone: dict(p=, y=, r=, loc=(x, f, z))} world deltas from rest; unlisted bones follow their parent.
    Returns {bone: (local quaternion, local location)}."""
    W = {}; out = {}
    for pb in arm.pose.bones:  # Blender keeps parents before children
        b = pb.bone; par = b.parent.name if b.parent else None
        Wp = W.get(par, Matrix.Identity(3)); sp = spec.get(b.name)
        Wb = _rot(sp.get('p', 0), sp.get('y', 0), sp.get('r', 0)) if sp and any(k in sp for k in ('p', 'y', 'r')) else Wp
        W[b.name] = Wb
        B = b.matrix_local.to_3x3()
        q = (B.inverted() @ Wp.inverted() @ Wb @ B).to_quaternion()
        loc = sp.get('loc') if sp else None
        out[b.name] = (q, (B.inverted() @ Wp.inverted() @ (P(*loc) - P(0, 0, 0))) if loc else Vector((0, 0, 0)))
    return out


def set_local(arm, L):
    for pb in arm.pose.bones:
        q, l = L[pb.name]; pb.rotation_mode = 'QUATERNION'; pb.rotation_quaternion = q; pb.location = l
    bpy.context.view_layer.update()


def apply_pose(arm, spec):
    """spec = a pose dict, or ('blend', specA, specB, u): local-space slerp between two poses."""
    if isinstance(spec, tuple):
        _, a, b, u = spec; A = local_pose(arm, a); Bp = local_pose(arm, b)
        L = {n: (A[n][0].slerp(Bp[n][0], u), A[n][1].lerp(Bp[n][1], u)) for n in A}
    else:
        L = local_pose(arm, spec)
    set_local(arm, L)


def clip(arm, name, keys, linear=False, measure=None):
    """keys: [(time_s, spec)]; every bone keyed at every time. measure = {t: fn}: fn() runs with the clip evaluated at t.
    Returns {t: fn()}. Pushed to its own NLA track (one glTF animation per track)."""
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for tr in arm.animation_data.nla_tracks: tr.mute = True
    out = {}
    for t, spec in keys:
        apply_pose(arm, spec); f = 1 + round(t * FPS)
        for pb in arm.pose.bones:
            pb.keyframe_insert('rotation_quaternion', frame=f); pb.keyframe_insert('location', frame=f)
    if linear:
        for fc in _fcurves(act):
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
    if measure:
        for t, fn in measure.items():
            bpy.context.scene.frame_set(1 + round(t * FPS)); bpy.context.view_layer.update(); out[t] = fn()
    arm.animation_data.action = None
    for tr in arm.animation_data.nla_tracks: tr.mute = False
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act)
    tr.mute = True  # muted while later clips are built and measured; unmuted by unmute_all() before export
    apply_pose(arm, {})
    return out


def unmute_all(arm):
    for tr in arm.animation_data.nla_tracks: tr.mute = False


def _fcurves(act):
    try:
        return list(act.fcurves)
    except AttributeError:  # Blender 5 layered actions
        fcs = []
        for layer in act.layers:
            for strip in layer.strips:
                for cb in strip.channelbags: fcs += list(cb.fcurves)
        return fcs


def Mm(v):
    """Blender vector -> design axes in metres (scaled model, for gates)."""
    return Vector((v.x, -v.y, v.z))


def world_pts(objs):
    """evaluated world vertex positions (design axes, metres) of meshes in the current pose."""
    dg = bpy.context.evaluated_depsgraph_get(); pts = []
    for ob in objs:
        oe = ob.evaluated_get(dg); me = oe.to_mesh()
        pts += [Mm(oe.matrix_world @ v.co) for v in me.vertices]; oe.to_mesh_clear()
    return pts


def bone_pt(arm, bone, tail=True):
    pb = arm.pose.bones[bone]; return Mm(arm.matrix_world @ (pb.tail if tail else pb.head))


# Gates and export ------------------------------------------------------------------------------------------------------
class Gates:
    def __init__(self): self.rows = []
    def __call__(self, ok, line):
        self.rows.append((bool(ok), line)); print(('PASS ' if ok else 'FAIL ') + line)
    def summary(self, label):
        n = len(self.rows); p = sum(1 for ok, _ in self.rows if ok); print(f'{label}: {p} of {n} pass'); return p, n
    def dump(self, path, extra=None):
        json.dump({'gates': [{'ok': ok, 'line': l} for ok, l in self.rows], **(extra or {})}, open(path, 'w'), indent=1, ensure_ascii=False)


def export(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kw = dict(filepath=path, export_format='GLB', export_animations=True, export_materials='EXPORT', export_image_format='NONE')
    try:
        bpy.ops.export_scene.gltf(**kw, export_animation_mode='NLA_TRACKS')
    except TypeError:
        bpy.ops.export_scene.gltf(**kw, export_nla_strips=True)
    print('wrote', path, os.path.getsize(path), 'bytes')


def hit(ob, origin, direction):
    """ray from origin along direction (design coords) against a built part's mesh; returns (point, normal) in design coords or None."""
    me = ob.data; bvh = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    loc, nrm, _, _ = bvh.ray_cast(P(*origin), (P(*direction) - P(0, 0, 0)).normalized())
    if loc is None: return None
    n = Vector((nrm.x, -nrm.y, nrm.z)).normalized()
    return D(loc), n


def glb_info(path):
    """animations, node names and material names inside an exported GLB (reads the JSON chunk)."""
    import struct
    b = open(path, 'rb').read(); ln = struct.unpack_from('<I', b, 12)[0]; j = json.loads(b[20:20 + ln])
    return ([a.get('name') for a in j.get('animations', [])], [n.get('name') for n in j.get('nodes', [])], [m.get('name') for m in j.get('materials', [])], j)
