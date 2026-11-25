# Face options sample (FACES worker; owner 25 Nov 09:44 "i hate the face": the suits, guards/rebels and giants have plain brown
# featureless oval faces; he wants to SEE four options before choosing). SAMPLE ONLY: nothing here goes into the game or replaces an asset.
#   A bronze war mask (cast brass mask, eye slits, inlaid brow line)   B closed visor (brass lamellar bands, one dark eye slit)
#   C painted face (calm human face, painted skin texture from klad)    D lacquer mask (black lacquer, painted lines in the school colour)
#   0 = the current face, built through the same path for the comparison.
# The real builders run unchanged except for their face function (read-only references): the suit builder (art/tools/suit_blender.py,
# c_helm minus its mask / eyes / brows / nose), the guard (art/tools/guard_build.py head() on art/tools/fodder_base.py) and the giants
# (art/tools/giant_blender.py face()). Their export call is wrapped so the painted faces get their texture UVs (front projection,
# faces_kit.py layout) and the triangle counts are written to <OUT>/<char>_<opt>_stats.json.
# Usage (bpy Python): python faces_sample.py -- CHAR OPT OUTDIR      CHAR fa | zu | g00, OPT 0 | A | B | C | D
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
# Face grid quads (across, down) at full detail per character; lower LODs scale by the builder's segment factor.
GRID = {'fa': (24, 20), 'zu': (12, 10), 'g00': (26, 22)}
# Rim loop points (across, up) per edge at full detail; rims are built at LOD0 only (guard budget 4000 tris).
RIM_PTS = {'fa': (12, 10), 'zu': (7, 5), 'g00': (12, 10)}
# Edges between faces meeting at more than this angle stay hard (option A: sharp where sharp), deg.
SHARP_A = 32
# Rim tube radius around a mask or visor edge, as a share of the face half-width.
RIM_R = 0.055
# Under-jaw rows: how far below the chin the patch turns back toward the neck (share of the face height).
UNDER = 0.12

FRAME = {}          # painted-face projection: z0, z1 (Blender), xs (Blender x per design x), fx (design half-width per t)
STATS = {'face_tris_lod0': 0, 'parts': []}


class Head:
    """the head under a face patch: wrap(t) -> (half-width, centre f, half-depth) of the surface the face lies on (design metres),
    fx(t) = face half-width, fref = feature depth unit, off = gap above the head surface."""
    def __init__(s, z0, z1, wrap, fx, off):
        s.z0, s.z1, s.wrap, s.fx, s.off = z0, z1, wrap, fx, off
        s.fref = fx(K.T_EYE)

    def z(s, t): return s.z0 + t * (s.z1 - s.z0)

    def point(s, sx, t, feat, out=0.0):
        """design (x, f, z) of the face surface at (s, t) plus feature relief and an extra outward offset (metres)."""
        tt = K.clamp(t, -0.05, 1.05)
        ww, fc, hd = s.wrap(tt); fx = s.fx(tt)
        x = sx * fx; xr = min(abs(x) / (ww + s.off), 0.999)
        f = fc + (hd + s.off) * (1 - xr ** K.N_WRAP) ** (1 / K.N_WRAP) + s.fref * feat(sx, tt) + out
        return (x, f, s.z(t))

    def under(s, sx, q, feat):
        """under-jaw rows below the chin edge: q 0 (the chin edge) .. 1 (tucked back toward the neck)."""
        e = s.point(sx, 0.0, feat); ww, fc, hd = s.wrap(0.0)
        tgt = (sx * s.fx(0.0) * 0.7, fc + hd * 0.3, s.z(-UNDER))
        return tuple(e[i] + (tgt[i] - e[i]) * q for i in range(3))


def s_bias(w, smax=K.S_MAX): return math.copysign(abs(w) ** 1.25, w) * smax


# ---- mesh building: one adapter per builder (coordinate map, put(), UVs) --------------------------------------------------------------
class Adapter:
    def __init__(s, to_b, put, uv=None, lod0=lambda: True, segf=lambda: 1.0, outward=None):
        s.to_b, s._put, s.uv, s.lod0, s.segf = to_b, put, uv, lod0, segf
        s.out = outward  # Blender vector pointing out of the face (design +f)

    def emit(s, name, pts, faces, mat, row, bone, sharp=None, closed=False):
        bm = bmesh.new(); V = [bm.verts.new(s.to_b(*p)) for p in pts]
        F = []
        for fi in faces:
            try: F.append(bm.faces.new([V[i] for i in fi]))
            except ValueError: pass
        bm.normal_update()
        avg = Vector((0, 0, 0))
        for f in F: avg += f.normal * f.calc_area()
        if closed: bmesh.ops.recalc_face_normals(bm, faces=F)
        elif avg.dot(s.out) < 0: bmesh.ops.reverse_faces(bm, faces=F)
        if s.uv:
            uvl = bm.loops.layers.uv.new('UVMap'); co = {v: p for v, p in zip(V, pts)}
            zs = [p[2] for p in pts]; zmax, zmin = max(zs), min(zs)
            for f in F:
                for lp in f.loops: lp[uvl].uv = s.uv(mat, row, co[lp.vert], zmax, zmax - zmin)
        bm.normal_update()
        for f in F: f.smooth = True
        lim = math.radians(sharp) if sharp else None
        for e in bm.edges:
            if lim and len(e.link_faces) == 2 and e.calc_face_angle(0) > lim: e.smooth = False
        n = sum(len(f.verts) - 2 for f in F)
        if s.lod0(): STATS['face_tris_lod0'] += n; STATS['parts'].append((name, n))
        return s._put(name, bm, mat, row, bone)


def grid(head, ns, nt, feat, t0=0.0, t1=1.0, smax=K.S_MAX, out=lambda sx, t: 0.0, under=True):
    """the face patch: (ns x nt) quads over s -smax..smax (denser at the centre), t t0..t1, plus 2 under-jaw rows."""
    pts, faces, rows = [], [], []
    ts = [t0 + (t1 - t0) * i / nt for i in range(nt + 1)]
    ss = [s_bias(-1 + 2 * j / ns, smax) for j in range(ns + 1)]
    if under and t0 <= 0.0:
        for q in (1.0, 0.5):
            rows.append([head.under(sx, q, feat) for sx in ss])
    for t in ts: rows.append([head.point(sx, t, feat, head.off * 0 + out(sx, t)) for sx in ss])
    for r in rows: pts += r
    W = ns + 1
    for i in range(len(rows) - 1):
        for j in range(ns): faces.append((i * W + j, i * W + j + 1, (i + 1) * W + j + 1, (i + 1) * W + j))
    return pts, faces


def patch(head, feat, s_lo, s_hi, t_fn, h_fn, nu, nv, out):
    """a strip lying on the face surface: u across s_lo..s_hi, v across t_fn(s) -/+ h_fn(p) (eye slits, inlay lines, visor bars)."""
    pts, faces = [], []
    for i in range(nu + 1):
        p = i / nu; sx = s_lo + (s_hi - s_lo) * p; h = h_fn(p); tc = t_fn(sx)
        for j in range(nv + 1):
            t = tc - h + 2 * h * j / nv
            pts.append(head.point(sx, t, feat, out))
    for i in range(nu):
        for j in range(nv):
            a = i * (nv + 1) + j; faces.append((a, a + 1, a + nv + 2, a + nv + 1))
    return pts, faces


def tube_pts(loop, r, sides=6):
    """a closed tube along a closed design-space loop (rim)."""
    pts, faces = [], []
    n = len(loop)
    for i in range(n):
        p0, p1, pm = Vector(loop[(i + 1) % n]), Vector(loop[i - 1]), Vector(loop[i])
        d = (p0 - p1).normalized(); up = Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((0, 0, 1))
        a = d.cross(up).normalized(); b = d.cross(a).normalized()
        for k in range(sides):
            th = math.tau * k / sides
            pts.append(tuple(pm + a * (r * math.cos(th)) + b * (r * math.sin(th))))
    for i in range(n):
        for k in range(sides):
            i2, k2 = (i + 1) % n, (k + 1) % sides
            faces.append((i * sides + k, i * sides + k2, i2 * sides + k2, i2 * sides + k))
    return pts, faces


def boundary(head, feat, t0, t1, smax, out, n_s, n_t):
    """the closed edge loop of a face patch (bottom, right side, top, left side) at the patch surface plus out."""
    L = [head.point(s_bias(-1 + 2 * j / n_s, smax), t0, feat, out) for j in range(n_s)]
    L += [head.point(smax, t0 + (t1 - t0) * i / n_t, feat, out) for i in range(n_t)]
    L += [head.point(s_bias(1 - 2 * j / n_s, smax), t1, feat, out) for j in range(n_s)]
    L += [head.point(-smax, t1 - (t1 - t0) * i / n_t, feat, out) for i in range(n_t)]
    return L


def ears(A, head, mat, row, bone):
    """option C ears: flattened spheres at the side of the head on the eye-to-nose band (painted skin)."""
    t = (K.T_EYE + K.T_NOSE) / 2; ww, fc, hd = head.wrap(t); F = head.fref
    for sd in (1, -1):
        c = (sd * (ww + head.off + 0.1 * F), fc + 0.05 * F, head.z(t)); r = (0.16 * F, 0.28 * F, 0.5 * F)
        pts, faces = [], []
        nu, nv = max(6, round(10 * A.segf())), max(4, round(6 * A.segf()))
        for i in range(nv + 1):
            ph = math.pi * i / nv
            for j in range(nu):
                th = math.tau * j / nu
                pts.append((c[0] + r[0] * math.sin(ph) * math.cos(th), c[1] + r[1] * math.sin(ph) * math.sin(th), c[2] + r[2] * math.cos(ph)))
        for i in range(nv):
            for j in range(nu):
                faces.append((i * nu + j, i * nu + (j + 1) % nu, (i + 1) * nu + (j + 1) % nu, (i + 1) * nu + j))
        A.emit(f'fc_ear{sd}', pts, faces, mat, row, bone, closed=True)


def build_face(A, head, opt, M, bone):
    """M: material/row per role: face (A/C/D surface), slit, inlay, band, bar, rim (each (mat, row) or None)."""
    ns, nt = GRID[CHAR]; k = A.segf(); ns = max(8, int(round(ns * k / 2)) * 2); nt = max(6, round(nt * k))
    feat = K.FEAT[opt]; F = head.fref
    if opt in ('A', 'C', 'D'):
        pts, faces = grid(head, ns, nt, feat)
        A.emit(f'fc_face_{opt}', pts, faces, *M['face'], bone, sharp=SHARP_A if opt == 'A' else 60)
        if opt in ('A', 'D'):
            for sd in (1, -1):
                lo, hi = (K.S_EYE - K.S_EYE_HALF, K.S_EYE + K.S_EYE_HALF)
                s_lo, s_hi = (lo, hi) if sd > 0 else (-hi, -lo)
                hh = 0.045 if opt == 'A' else 0.04
                pts, faces = patch(head, feat, s_lo, s_hi, K.slit_t, lambda p: hh * max(0.12, math.sin(math.pi * p)) ** 0.7, 6, 2, 0.0025 * F / 0.09)
                A.emit(f'fc_slit{sd}', pts, faces, *M['slit'], bone)
        if opt == 'A' and M.get('inlay') and A.lod0():
            for sd in (1, -1):
                s_lo, s_hi = (0.06, 0.8) if sd > 0 else (-0.8, -0.06)
                pts, faces = patch(head, feat, s_lo, s_hi, K.brow_t, lambda p: 0.012, 10, 1, 0.0015 * F / 0.09)
                A.emit(f'fc_inlay{sd}', pts, faces, *M['inlay'], bone)
        if M.get('rim') and A.lod0():
            loop = boundary(head, feat, 0.0, 1.0, K.S_MAX, 0.0, *RIM_PTS[CHAR])
            pts, faces = tube_pts(loop, RIM_R * F, 4)
            A.emit(f'fc_rim_{opt}', pts, faces, *M['rim'], bone, closed=True)
        if opt == 'C' and M.get('ears'): ears(A, head, *M['face'], bone)
    elif opt == 'B':
        # the dark field behind the eye slit (and the whole visor back), then the bands from the top down, each lower edge proud
        pts, faces = grid(head, ns, max(6, nt // 2), K.FEAT['B'], t0=K.VISOR_BANDS[1][1] - 0.04, t1=K.VISOR_BANDS[0][0] + 0.04, under=False)
        A.emit('fc_visor_slit', pts, faces, *M['slit'], bone)
        lip = K.VISOR_LIP * F
        for bi, (tb, tt) in enumerate(K.VISOR_BANDS):
            n_t = max(3, round(nt * (tt - tb)))
            def out(sx, t, tb=tb, tt=tt, bi=bi): return 0.006 * F / 0.09 + lip * (1 - K.clamp((t - tb) / (tt - tb))) + 0.004 * bi * 0
            pts, faces = grid(head, ns, n_t, K.FEAT['B'], t0=tb, t1=tt, out=out, under=(bi == 3))
            # the lip return: a row at the band bottom stepping back to the head surface
            W = ns + 1; base = len(pts)
            pts += [head.point(s_bias(-1 + 2 * j / ns), tb, K.FEAT['B'], 0.0) for j in range(ns + 1)]
            off0 = 2 * W if bi == 3 else 0
            for j in range(ns): faces.append((base + j, base + j + 1, off0 + j + 1, off0 + j))
            A.emit(f'fc_band{bi}', pts, faces, *M['band'], bone)
        # the nasal bar down the centre over the bands
        top = lambda sx: (0.24 + 1.0) / 2
        pts, faces = patch(head, K.FEAT['B'], -0.07, 0.07, top, lambda p: 0.39, 2, max(6, nt // 2), lip + 0.012 * F / 0.09)
        A.emit('fc_visor_bar', pts, faces, *M['bar'], bone)
        if M.get('rim') and A.lod0():
            loop = boundary(head, K.FEAT['B'], -0.03, 1.03, K.S_MAX, lip * 0.5, *RIM_PTS[CHAR])
            pts, faces = tube_pts(loop, RIM_R * F, 4)
            A.emit('fc_rim_B', pts, faces, *M['rim'], bone, closed=True)


# ---- export hook: painted-face UVs, triangle counts -----------------------------------------------------------------------------------
def fix_face_uvs(ob):
    me = ob.data
    names = [m.name if m else '' for m in me.materials]
    if not any(n.startswith('fcFace') for n in names) or not FRAME: return 0
    uvl = me.uv_layers.get('UVMap') or me.uv_layers.active
    z0, z1, xs, fx = FRAME['z0'], FRAME['z1'], FRAME['xs'], FRAME['fx']; n = 0
    for p in me.polygons:
        if not names[p.material_index].startswith('fcFace'): continue
        for li in p.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            t = (c.z - z0) / (z1 - z0); sx = (c.x / xs) / fx(K.clamp(t, 0.0, 1.0))
            uvl.data[li].uv = (0.5 + 0.5 * sx, t)
        n += 1
    return n


def fc_export(**kw):
    rep = {'char': CHAR, 'opt': OPT, 'face_tris_lod0': STATS['face_tris_lod0'], 'face_parts': STATS['parts'], 'meshes': {}, 'uv_fixed_polys': 0}
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        rep['uv_fixed_polys'] += fix_face_uvs(ob)
        rep['meshes'][ob.name] = dict(tris=sum(len(p.vertices) - 2 for p in ob.data.polygons), mats=[m.name for m in ob.data.materials if m])
    json.dump(rep, open(os.path.join(OUTDIR, f'{CHAR}_{OPT}_stats.json'), 'w'), indent=1, ensure_ascii=False)
    print('FACES stats', CHAR, OPT, 'face tris lod0', STATS['face_tris_lod0'], 'uv fixed polys', rep['uv_fixed_polys'])
    return bpy.ops.export_scene.gltf(**kw)


def interp(table, z):
    """linear interpolation in a list of (z, ...) rows."""
    if z <= table[0][0]: return table[0][1:]
    for a, b in zip(table, table[1:]):
        if z <= b[0]:
            u = (z - a[0]) / (b[0] - a[0]); return tuple(x + (y - x) * u for x, y in zip(a[1:], b[1:]))
    return table[-1][1:]


# ---- suit 法 fa --------------------------------------------------------------------------------------------------------------------------
NS = {}
def face_suit(b, S, hz):
    ns = NS; z0, z1 = hz(0.0), hz(0.78)
    shell = [(hz(-0.05), 0.12, -0.01, 0.13), (hz(0.25), 0.13, -0.01, 0.145), (hz(0.6), 0.13, 0.0, 0.14), (hz(0.85), 0.11, 0.0, 0.12), (hz(1.0), 0.06, 0.0, 0.065)]
    def wrap(t): w, fc, hd = interp(shell, z0 + t * (z1 - z0)); return (w, fc, hd)
    fxw = lambda t: 0.092 * K.jaw(t)
    head = Head(z0, z1, wrap, fxw, 0.008)
    def put(name, bm, mat, row, bone): return ns['put'](name, bm, mat, bone)
    def uv(mat, row, p, zmax, vspan): return ns['uvmap'](mat, row, p[0] + 1.0 + 0.3 * p[1], zmax - p[2], vspan)
    A = Adapter(ns['D'], put, uv=uv, outward=ns['D'](0, 1, 0))
    FRAME.update(z0=z0, z1=z1, xs=-b.hk, fx=fxw)
    lac, trim = S['lac'], S['trim']
    M = {'A': dict(face=('fcBrass', 'plain'), slit=('sLam', 'plate_black'), inlay=('sLam', trim), rim=('fcBrass', 'plain')),
         'B': dict(slit=('sLam', 'plate_black'), band=('fcBrass', 'plain'), bar=('sLam', trim), rim=('sLam', f'plate_{lac}')),
         'C': dict(face=('fcFace', 'face'), rim=('sLam', f'plate_{lac}')),
         'D': dict(face=('fcFace', 'face'), slit=('sLam', 'plate_black'), rim=('sLam', f'plate_{lac}'))}[OPT]
    build_face(A, head, OPT, M, 'head')


def run_suit():
    path = os.path.join(HERE, 'suit_blender.py'); src = open(path).read()
    src = src.replace('bpy.ops.export_scene.gltf(', 'FC_EXPORT(')
    if OPT != '0':
        a = src.index("    loft('mask', [((0, 0.11, hz(0.02))"); b = src.index('    brim = lambda r0, r1')
        src = src[:a] + '    FACE_SUIT(b, S, hz)\n' + src[b:]
        i = src.index("        loft('nose', [((0, 0.17, hz(0.62))"); j = src.index('\n', i)
        src = src[:i] + '        pass' + src[j:]
    sub = os.path.join(OUTDIR, f'tmp_{CHAR}_{OPT}'); os.makedirs(sub, exist_ok=True)   # parallel builds must not share the builder's outputs
    sys.argv = ['suit_blender.py', '--', sub, CHAR]
    NS.update({'__name__': 'suit_faces', '__file__': path, 'FC_EXPORT': fc_export, 'FACE_SUIT': face_suit})
    exec(compile(src, path, 'exec'), NS)
    NS['SHEETS'].update({'fcBrass': (1024, 1024, 4.0), 'fcFace': (512, 512, 1.0)})
    NS['ROWS'].update({'fcBrass': {'plain': (40, 344)}, 'fcFace': {'face': (0, 512)}})
    G, info = NS['build_suit'](CHAR)
    for g in G: print(g)
    os.replace(os.path.join(sub, f'{CHAR}.glb'), os.path.join(OUTDIR, f'{CHAR}_{OPT}.glb'))


# ---- guard 卒 zu -------------------------------------------------------------------------------------------------------------------------
GB = None
def face_guard(d, cap='knot'):
    B = sys.modules['fodder_base']; Q = B.Q
    zo, zk = Q['zoff'], Q['zk']; Q['zoff'] = GB.ZPIV + (1.44 + zo - GB.ZPIV) * zk - 1.44; Q['zk'] = 1.0
    skull = (GB.LQ, 'lacquer') if OPT == 'C' else (GB.BR, 'plain')
    B.spheroid('mask', (0, 0.01, 1.44), (0.094, 0.103, GB.MASK_RZ), *skull, 'head', segs=(12, 9))
    z0, z1 = 1.335, 1.5
    def wrap(t):
        z = z0 + t * (z1 - z0); r = math.sqrt(max(0.0, 1 - ((z - 1.44) / 0.12) ** 2)); r = max(r, 0.74)
        return (0.094 * r, 0.01, 0.103 * r)
    fxw = lambda t: 0.92 * wrap(t)[0]
    head = Head(z0, z1, wrap, fxw, 0.006)
    def put(name, bm, mat, row, bone): return B.put(name, bm, mat, bone, row, True)
    A = Adapter(B.P, put, lod0=lambda: Q['detail'] and Q['seg'] >= 1.0, segf=lambda: Q['seg'], outward=B.P(0, 1, 0) - B.P(0, 0, 0))
    if Q['detail'] and Q['seg'] >= 1.0:
        o, x1 = B.P(0, 0, 0), B.P(1, 0, 0); FRAME.update(z0=B.P(0, 0, z0).z, z1=B.P(0, 0, z1).z, xs=x1.x - o.x, fx=fxw)
    M = {'A': dict(face=(GB.BR, 'plain'), slit=(GB.LQ, 'lacquer'), inlay=(GB.LQ, 'blue'), rim=(GB.BR, 'flange')),
         'B': dict(slit=(GB.LQ, 'lacquer'), band=(GB.BR, 'plain'), bar=(GB.LQ, 'blue'), rim=None),
         'C': dict(face=('fcFace', 'plain'), ears=True),
         'D': dict(face=('fcFace', 'plain'), slit=(GB.LQ, 'lacquer'), rim=(GB.BR, 'flange'))}[OPT]
    build_face(A, head, OPT, M, 'head')
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
    fxw = lambda t: 0.86 * wrap(t)[0]
    head = Head(z0, z1, wrap, fxw, 0.02)
    def put(name, bm, mat, row, bone): return ns['put'](name, bm, mat, bone, row, True)
    Q = ns['Q']
    A = Adapter(ns['P'], put, lod0=lambda: Q['lod'] == 0, segf=lambda: Q['seg'], outward=ns['P'](0, 1, 0))
    if lod == 0: FRAME.update(z0=z0, z1=z1, xs=1.0, fx=fxw)
    M = {'A': dict(face=('palBronze', 'plain'), slit=('fcDark', 'plain'), inlay=('palTin', 'plain'), rim=('palBronze', 'flange')),
         'B': dict(slit=('fcDark', 'plain'), band=('palBronze', 'plain'), bar=('palTin', 'plain'), rim=('palBronze', 'flange')),
         'C': dict(face=('fcFace', 'plain'), ears=True),
         'D': dict(face=('fcFace', 'plain'), slit=('fcDark', 'plain'), rim=('palBronze', 'flange'))}[OPT]
    build_face(A, head, OPT, M, 'head')


def run_giant():
    path = os.path.join(HERE, 'giant_blender.py'); src = open(path).read()
    if OPT != '0':
        src = src.replace('def face(g, H, lod):', 'def face(g, H, lod): return FACE_GIANT(g, H, lod)\ndef _face_orig(g, H, lod):', 1)
    src = src.replace('bpy.ops.export_scene.gltf(', 'FC_EXPORT(')
    os.environ['GIANTS'] = str(int(CHAR[1:]))
    out = os.path.join(OUTDIR, f'{CHAR}_{OPT}.glb')
    sys.argv = ['giant_blender.py', out]
    GNS.update({'__name__': 'giant_faces', '__file__': path, 'FC_EXPORT': fc_export, 'FACE_GIANT': face_giant})
    exec(compile(src, path, 'exec'), GNS)


if __name__ == '__main__':
    {'fa': run_suit, 'zu': run_guard, 'g00': run_giant}[CHAR]()
    print('FACES done', CHAR, OPT)
