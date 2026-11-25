# Face masks round 2 (FACES worker; owner GO 25 Nov 10:47 "lacquer mask, menacing", order 10:52 "use the kit method"). SAMPLE ONLY:
# nothing here goes into the game or replaces an asset. Groups: guard 卒 zu and giant 00 (suit 法 fa moved to the SUITS worker).
#   M = the round-2 mask: ONE sculpted shell per group (faces_kit.py height function over the head wrap), cut by marching squares over a
#       signed field (outline, eye slits, mouth), walls down every cut edge to a backing set deep behind the cuts, and a rim (the hood or
#       crown edge) standing proud over the top and sides so the mask sits back under it. No new material: guard lacquer mask on the bronze
#       hood with bronze behind the cuts; giant high-tin (pale) mask on the gold body with dark bronze behind the cuts.
#   T = giant only: the same mask in high-tin bronze (pale) with dark bronze behind the cuts, no new material; M on the giant is glossy
#       black lacquer (new palLacquer material on the fodder_trim lacquer band, +1 draw call per giant) with pale tin behind the cuts. Built side by side so the owner
#       gets the measured play-size contrast of each for the draw-call trade.
#   0 = the current face, built through the same path for the comparison column.
# The real builders run unchanged except for their face function (read-only references): the guard (art/tools/guard_build.py head() on
# art/tools/fodder_base.py) and the giants (art/tools/giant_blender.py face()). Their export call is wrapped so the triangle counts, the
# materials and two probe points (mask cheek, hood or crown above it; rest pose, glTF space) are written to <OUT>/<char>_<opt>_stats.json.
# Usage (bpy Python): python faces_sample.py -- CHAR OPT OUTDIR      CHAR zu | g00, OPT 0 | M (| T giant)
import sys, os, math, json, types
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy, bmesh
from mathutils import Vector
import faces_kit as K

ARGV = sys.argv[sys.argv.index('--') + 1:]
CHAR, OPT, OUTDIR = ARGV[0], ARGV[1], ARGV[2]
os.makedirs(OUTDIR, exist_ok=True)

# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Edges between faces meeting at more than this angle stay hard (cut walls, rim lips), deg.
SHARP = 50
# Rim (hood or crown edge) profile: (outward from the mask edge, forward of the mask surface) per point, as a share of RIM_W.
RIM_PROFILE = [(1.0, -0.3), (0.55, 1.1), (-0.5, 1.4), (-0.85, 0.45)]
# Rim forward projection scale per group (round 3: the guard's hood rim shaded the eyes from the play camera).
RIM_FWD = {'zu': 0.6, 'g00': 1.0}
# Rim width, m, per group.
RIM_W = {'zu': 0.016, 'g00': 0.055}
# Rim path per group: side edge from this t up to the top (both sides), and points along the top at full detail.
RIM_SIDE_T0 = {'zu': 0.02, 'g00': 0.4}
RIM_PTS = {'zu': 10, 'g00': 26}
# Probe points for the play-size contrast gate (mask s, t) and the surface above the mask (design x, f, z).
PROBE_MASK = {'zu': (0.5, 0.42), 'g00': (0.66, 0.36)}
PROBE_HELM = {'zu': (0.0, 0.066, 1.54), 'g00': (0.0, 0.16, 4.39)}

STATS = {'face_tris_lod0': 0, 'parts': [], 'probes': {}}


class Head:
    """the head under the mask: wrap(t) -> (half-width, centre f, half-depth) of the surface the mask lies on (design metres),
    fx(t) = face half-width, fref = height unit (face half-width at the eye line), off = gap above the head surface."""
    def __init__(s, z0, z1, wrap, fx, off, t_eye=0.56):
        s.z0, s.z1, s.wrap, s.fx, s.off = z0, z1, wrap, fx, off
        s.fref = fx(t_eye)

    def z(s, t): return s.z0 + t * (s.z1 - s.z0)

    def point(s, sx, t, height, out=0.0):
        """design (x, f, z) of the mask surface at (s, t): head wrap + gap + relief + an extra forward offset (metres)."""
        tt = K.clamp(t, -0.05, 1.05)
        ww, fc, hd = s.wrap(tt); fx = s.fx(tt)
        x = sx * fx; xr = min(abs(x) / (ww + s.off), 0.999)
        f = fc + (hd + s.off) * (1 - xr ** 2.3) ** (1 / 2.3) + s.fref * height(sx, t) + out
        return (x, f, s.z(t))


class Adapter:
    def __init__(s, to_b, put, lod0=lambda: True, segf=lambda: 1.0, outward=None):
        s.to_b, s._put, s.lod0, s.segf, s.out = to_b, put, lod0, segf, outward

    def emit(s, name, pts, faces, mat, row, bone, sharp=SHARP):
        bm = bmesh.new(); V = [bm.verts.new(s.to_b(*p)) for p in pts]
        F = []
        for fi in faces:
            try: F.append(bm.faces.new([V[i] for i in fi]))
            except ValueError: pass
        bm.normal_update()
        avg = Vector((0, 0, 0))
        for f in F: avg += f.normal * f.calc_area()
        if avg.dot(s.out) < 0: bmesh.ops.reverse_faces(bm, faces=F)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bm.normal_update()
        for f in bm.faces: f.smooth = True
        lim = math.radians(sharp)
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > lim: e.smooth = False
        n = sum(len(f.verts) - 2 for f in bm.faces)
        if s.lod0(): STATS['face_tris_lod0'] += n; STATS['parts'].append((name, n))
        return s._put(name, bm, mat, row, bone)


def march(U, T, field):
    """marching squares over a rectilinear (s, t) grid (positive field = kept); returns points, CCW triangles and the directed
    boundary edges (one triangle only). Edge crossings sit where the field interpolates to zero, so cuts get smooth edges."""
    Fv = [[field(u, t) for u in U] for t in T]
    pts, cache, tris = [], {}, []
    def vert(key, s, t):
        if key not in cache: cache[key] = len(pts); pts.append((s, t))
        return cache[key]
    def edge(i0, j0, i1, j1):
        fa, fb = Fv[j0][i0], Fv[j1][i1]; k = fa / (fa - fb)
        key = ('e', min(i0, i1), min(j0, j1), i0 == i1)
        return vert(key, U[i0] + (U[i1] - U[i0]) * k, T[j0] + (T[j1] - T[j0]) * k)
    for j in range(len(T) - 1):
        for i in range(len(U) - 1):
            cs = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]; poly = []
            for q in range(4):
                a, b = cs[q], cs[(q + 1) % 4]; fa, fb = Fv[a[1]][a[0]], Fv[b[1]][b[0]]
                if fa > 0: poly.append(vert(('c', a[0], a[1]), U[a[0]], T[a[1]]))
                if (fa > 0) != (fb > 0): poly.append(edge(a[0], a[1], b[0], b[1]))
            for q in range(1, len(poly) - 1): tris.append((poly[0], poly[q], poly[q + 1]))
    count = {}
    for tr in tris:
        for q in range(3):
            a, b = tr[q], tr[(q + 1) % 3]; k = (min(a, b), max(a, b)); count[k] = count.get(k, 0) + 1
    bnd = [(tr[q], tr[(q + 1) % 3]) for tr in tris for q in range(3) if count[(min(tr[q], tr[(q + 1) % 3]), max(tr[q], tr[(q + 1) % 3]))] == 1]
    return pts, tris, bnd


def build_mask(A, head, group, M, bone):
    """M: (mat, row) per role: shell, back, rim."""
    hgt, fld, holes = K.SHAPES[group]; k = A.segf()
    U, T = K.axes(group, k); depth = K.DEPTH[group]; F = head.fref
    # the shell (one piece) and its walls: every boundary edge (outline and cuts) steps back by the backing depth
    st, tris, bnd = march(U, T, fld)
    P = [head.point(s, t, hgt) for s, t in st]
    n = len(P); P += [(x, f - depth * F, z) for x, f, z in P]
    faces = [tuple(tr) for tr in tris] + [(b, a, a + n, b + n) for a, b in bnd]
    used = sorted({i for fc in faces for i in fc}); remap = {o: i for i, o in enumerate(used)}
    A.emit(f'fc_mask_{group}', [P[i] for i in used], [tuple(remap[i] for i in fc) for fc in faces], *M['shell'], bone)
    # the backing behind the cuts (inside the outline, a margin beyond each cut)
    mg = K.BACK_MARGIN[group]
    st2, tris2, _ = march(U, T, lambda s, t: mg - holes(s, t))
    if tris2:
        P2 = [head.point(s, t, lambda a, b: hgt(a, b) - depth + K.bulge(group, a, b)) for s, t in st2]
        A.emit(f'fc_back_{group}', P2, tris2, *M['back'], bone)
    # the rim: up one side, along the top, down the other side, standing proud over the mask edge
    S = K.DOMAIN[group][0]; top = K.g_top if group == 'g00' else (lambda a: 1.0)
    smax = 0.95 if group == 'zu' else 1.18
    n_top = max(6, round(RIM_PTS[group] * k)); n_side = max(2, round(n_top * 0.3))
    t0 = RIM_SIDE_T0[group]
    path = [(-smax, t0 + (top(smax) - t0) * i / n_side, (-1, 0)) for i in range(n_side)]
    path += [(-smax + 2 * smax * i / n_top, top(abs(-smax + 2 * smax * i / n_top)), (0, 1)) for i in range(n_top + 1)]
    path += [(smax, top(smax) - (top(smax) - t0) * i / n_side, (1, 0)) for i in range(1, n_side + 1)]
    W = RIM_W[group]; tspan = head.z1 - head.z0; pts, rf = [], []
    for s, t, (ds, dt) in path:
        for po, pf in RIM_PROFILE:
            fx = head.fx(K.clamp(t, -0.05, 1.05))
            pts.append(head.point(s + ds * po * W / fx, t + dt * po * W / tspan, hgt, pf * W * RIM_FWD[group]))
    m = len(RIM_PROFILE)
    for i in range(len(path) - 1):
        for q in range(m - 1): rf.append((i * m + q, i * m + q + 1, (i + 1) * m + q + 1, (i + 1) * m + q))
    A.emit(f'fc_rim_{group}', pts, rf, *M['rim'], bone)


def probes(head, group, to_b, zmap=lambda z: z):
    """rest-pose probe points in glTF space (Blender (x, y, z) -> glTF (x, z, -y)) for the viewer's contrast gate."""
    hgt = K.SHAPES[group][0]
    es, et = K.EYE_C[group]
    eh = lambda a, b: hgt(a, b) - K.DEPTH[group] + K.bulge(group, a, b)
    for key, p in (('mask', head.point(*PROBE_MASK[group], hgt)), ('helm', PROBE_HELM[group]), ('eye', head.point(es, et, eh)), ('eye2', head.point(-es, et, eh))):
        v = to_b(*p); STATS['probes'][key] = [round(v.x, 5), round(zmap(v.z), 5), round(-v.y, 5)]


# ---- export hook: triangle counts, materials, probes --------------------------------------------------------------------------------
def fc_export(**kw):
    rep = {'char': CHAR, 'opt': OPT, 'face_tris_lod0': STATS['face_tris_lod0'], 'face_parts': STATS['parts'], 'probes': STATS['probes'], 'meshes': {}}
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        rep['meshes'][ob.name] = dict(tris=sum(len(p.vertices) - 2 for p in ob.data.polygons), mats=[m.name for m in ob.data.materials if m])
    json.dump(rep, open(os.path.join(OUTDIR, f'{CHAR}_{OPT}_stats.json'), 'w'), indent=1, ensure_ascii=False)
    print('FACES stats', CHAR, OPT, 'face tris lod0', STATS['face_tris_lod0'], 'probes', STATS['probes'])
    return bpy.ops.export_scene.gltf(**kw)


def interp(table, z):
    """linear interpolation in a list of (z, ...) rows."""
    if z <= table[0][0]: return table[0][1:]
    for a, b in zip(table, table[1:]):
        if z <= b[0]:
            u = (z - a[0]) / (b[0] - a[0]); return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return table[-1][1:]


# ---- guard 卒 zu -------------------------------------------------------------------------------------------------------------------------
GB = None
def face_guard(d, cap='knot'):
    B = sys.modules['fodder_base']; Q = B.Q
    zo, zk = Q['zoff'], Q['zk']; Q['zoff'] = GB.ZPIV + (1.44 + zo - GB.ZPIV) * zk - 1.44; Q['zk'] = 1.0
    B.spheroid('mask', (0, 0.01, 1.44), (0.094, 0.103, GB.MASK_RZ), GB.BR, 'head', 'plain', segs=(12, 9))
    z0, z1 = 1.335, 1.5
    def wrap(t):
        z = z0 + t * (z1 - z0); r = math.sqrt(max(0.0, 1 - ((z - 1.44) / 0.12) ** 2)); r = max(r, 0.74)
        return (0.094 * r, 0.01, 0.103 * r)
    fxw = lambda t: 0.85 * wrap(t)[0]
    head = Head(z0, z1, wrap, fxw, 0.006)
    def put(name, bm, mat, row, bone): return B.put(name, bm, mat, bone, row, True)
    lod0 = lambda: Q['detail'] and Q['seg'] >= 1.0
    A = Adapter(B.P, put, lod0=lod0, segf=lambda: Q['seg'], outward=B.P(0, 1, 0) - B.P(0, 0, 0))
    build_mask(A, head, 'zu', dict(shell=(GB.LQ, 'lacquer'), back=(GB.BR, 'flange'), rim=(GB.BR, 'flange')), 'head')
    if lod0(): probes(head, 'zu', B.P)
    if cap == 'knot':
        B.spheroid('cap', (0, -0.005, 1.49), (0.082, 0.088, 0.052), GB.LQ, 'head', 'lacquer', segs=(10, 6))
        B.spheroid('knot', (0.045, -0.02, 1.555), (0.04, 0.04, 0.042), GB.BR, 'head', 'plain', segs=(8, 6))
    Q['zoff'], Q['zk'] = zo, zk


def run_guard():
    global GB
    path = os.path.join(HERE, 'fodder_base.py'); src = open(path).read().replace('bpy.ops.export_scene.gltf(', 'FC_EXPORT(')
    mod = types.ModuleType('fodder_base'); mod.__file__ = path; mod.FC_EXPORT = fc_export
    exec(compile(src, path, 'exec'), mod.__dict__); sys.modules['fodder_base'] = mod
    sys.argv = ['guard_build.py', '--', OUTDIR, CHAR]
    import guard_build as gb
    GB = gb
    if OPT != '0': gb.head = face_guard
    build, bones, clips_fn, sc = gb.UNITS[CHAR]
    gb.Q['scale'] = sc; gb.MPR.clear()
    sub = os.path.join(OUTDIR, f'tmp_{CHAR}_{OPT}'); os.makedirs(sub, exist_ok=True)
    out = os.path.join(sub, f'{CHAR}_{OPT}.glb')
    res = mod.build_unit(CHAR, build, bones(), clips_fn, out, gb.extra(CHAR))
    for ok, line in res['gates']: print(('PASS ' if ok else 'FAIL ') + f'{CHAR} {line}')
    print(f"SUMMARY {CHAR} {OPT} {res['passed']} of {res['checks']} tris {res['tris']}")
    os.replace(out, os.path.join(OUTDIR, f'{CHAR}_{OPT}.glb'))


# ---- giant 00 ----------------------------------------------------------------------------------------------------------------------------
GNS = {}
def face_giant(g, H, lod):
    ns = GNS; HEAD = ns['HEAD']; j, sk = H.get('jaw', 1.0), H.get('skull', 1.0)
    secs = [(z, cf, hw * (j if z < 3.96 else sk), hd, cx) for z, cf, hw, hd, cx in HEAD]
    ns['loft'](f'{g}_cranium', secs, 'palBronze', 'head', 'plain', n_exp=2.3, M=20)
    z0, z1 = 3.74, 4.28
    tab = [(z, hw, cf, hd) for z, cf, hw, hd, cx in secs]
    def wrap(t): return interp(tab, z0 + t * (z1 - z0))
    fxw = lambda t: 0.95 * wrap(t)[0]
    head = Head(z0, z1, wrap, fxw, 0.02)
    def put(name, bm, mat, row, bone): return ns['put'](name, bm, mat, bone, row, True)
    Q = ns['Q']
    A = Adapter(ns['P'], put, lod0=lambda: Q['lod'] == 0, segf=lambda: Q['seg'], outward=ns['P'](0, 1, 0))
    M = dict(shell=('palLacquer', 'lacquer'), back=('palTin', 'plain'), rim=('palBronze', 'flange')) if OPT == 'M' else \
        dict(shell=('palTin', 'plain'), back=('palBronze', 'inlay'), rim=('palBronze', 'flange'))
    build_mask(A, head, 'g00', M, 'head')
    if lod == 0: probes(head, 'g00', ns['P'], ns['Wz'])


def run_giant():
    path = os.path.join(HERE, 'giant_blender.py'); src = open(path).read()
    if OPT != '0':
        src = src.replace('def face(g, H, lod):', 'def face(g, H, lod): return FACE_GIANT(g, H, lod)\ndef _face_orig(g, H, lod):', 1)
    src = src.replace('bpy.ops.export_scene.gltf(', 'FC_EXPORT(')
    # the lacquer mask (M) takes the lacquer band of the guards' fodder_trim sheet (rows 8-248), same 256 px/m trim mapping
    src = src.replace("ROWS = {'plain': (40, 344),", "ROWS = {'lacquer': (8, 248), 'plain': (40, 344),", 1)
    os.environ['GIANTS'] = str(int(CHAR[1:]))
    out = os.path.join(OUTDIR, f'{CHAR}_{OPT}.glb')
    sys.argv = ['giant_blender.py', out]
    GNS.update({'__name__': 'giant_faces', '__file__': path, 'FC_EXPORT': fc_export, 'FACE_GIANT': face_giant})
    exec(compile(src, path, 'exec'), GNS)


if __name__ == '__main__':
    {'zu': run_guard, 'g00': run_giant}[CHAR]()
    print('FACES done', CHAR, OPT)
