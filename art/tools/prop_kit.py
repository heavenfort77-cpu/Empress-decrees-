# Shared Blender helpers for the cast-bronze palace props of W1b (asset list C4-C7, C9-C11; study art/Qin-Bronze-Castings-Study.md).
# Copied from W1a's builders (art/tools/vat_blender.py, ding_blender.py, beast_blender.py: lathe, spheroid, torus, prism, loft, trim-sheet
# UVs, finish) and gathered in one module so every prop uses the same UV rules, smoothing and gates. Adds sweep() (a round tube along a
# curved path with tapering radii: necks, legs, arms, stems) and card() (an upright or flat quad with 0-1 UVs for glow and smoke cards).
# Design coordinates: x right, f toward the camera (glTF +Z), z up. Run only inside Blender's Python (bpy venv).
import bpy, bmesh, math, os
from mathutils import Vector, Matrix

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel on sharp parts, m (LOD0 only); hard edge angle on rounded parts, deg.
BEVEL = 0.01
SHARP_DEG = 50
# Trim sheet: metres per UV unit and rows in image pixels (art/tools/bronze_tex.py layout, 1024 px = 4 m).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704),
        'mark': (704, 768), 'patina': (800, 1000)}

PARTS = []
Q = {'seg': 1.0}

def P(x, f, z): return Vector((x, -f, z))
def V(*a): return Vector(a)

def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)

def put(name, bm, mat, row, rnd):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, mat, row, rnd)); return ob

def segs(n, lo=6): return max(lo, round(n * Q['seg']))

def lathe(name, prof, mat, row, n=24, dr=0.0, cx=0.0, cf=0.0):
    """a turned (round) part: profile [(radius, z)] around the vertical axis at (cx, cf); radius 0 closes on the axis."""
    M = segs(n, 8); bm = bmesh.new(); rings = []
    for rr, z in prof:
        if rr <= 1e-6: rings.append([bm.verts.new(P(cx, cf, z))] * M)
        else: rings.append([bm.verts.new(P(cx + math.cos(i * math.tau / M) * (rr + dr), cf + math.sin(i * math.tau / M) * (rr + dr), z)) for i in range(M)])
    for a, b in zip(rings, rings[1:]):
        for i in range(M):
            vs = [a[i], a[(i + 1) % M], b[(i + 1) % M], b[i]]; vs = [v for k, v in enumerate(vs) if v not in vs[:k]]
            if len(vs) >= 3: bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, row, True)

def spheroid(name, c, r, mat, row='plain', sg=(10, 6)):
    u = segs(sg[0], 5); v = segs(sg[1], 3)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    for vv in bm.verts: vv.co = P(c[0] + vv.co.x * r[0], c[1] - vv.co.y * r[1], c[2] + vv.co.z * r[2])
    return put(name, bm, mat, row, True)

def torus(name, c, axis, R, r, mat, row='flange', sg=(12, 6)):
    """a cast ring around 'axis' (design coords) centred at c."""
    n1, n2 = segs(sg[0], 8), segs(sg[1], 4)
    ax = Vector(axis).normalized(); u = ax.cross(Vector((0, 0, 1))); u = u.normalized() if u.length > 1e-6 else Vector((1, 0, 0)); w = ax.cross(u)
    bm = bmesh.new(); rings = []
    for i in range(n1):
        t = i * math.tau / n1; cen = u * (math.cos(t) * R) + w * (math.sin(t) * R); dirc = cen.normalized()
        rings.append([bm.verts.new(P(*(Vector(c) + cen + dirc * (math.cos(k * math.tau / n2) * r) + ax * (math.sin(k * math.tau / n2) * r)))) for k in range(n2)])
    for i in range(n1):
        a, b = rings[i], rings[(i + 1) % n1]
        for k in range(n2): bm.faces.new([a[k], a[(k + 1) % n2], b[(k + 1) % n2], b[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, row, True)

def prism(name, prof, a, b, mat, row='plain', scale_b=1.0, rnd=False, up=None):
    """a straight extrusion of a 2D profile from a to b (design coords); sharp unless rnd."""
    a, b = P(*a), P(*b); d = (b - a).normalized()
    upv = P(*up) if up else (Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0)))
    u = d.cross(upv).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + u * p[0] + v * p[1]) for p in prof]; r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    for i in range(len(prof)): bm.faces.new([r0[i], r0[(i + 1) % len(prof)], r1[(i + 1) % len(prof)], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, row, rnd)

def sweep(name, pts, radii, mat, row='plain', n=8, flat=None, cap=True, rnd=True, side=None):
    """a round tube along a path (design coords) with a radius per point (tapers to a point when a radius is 0);
    flat = (sx, sy) squashes the section (sx along 'side', sy across it); side = design-coords direction of the section's first axis at the
    start (default: horizontal, perpendicular to the path). Parallel-transport frames, so it never twists."""
    M = segs(n, 4); pts = [P(*p) for p in pts]; bm = bmesh.new(); rings = []
    t0 = (pts[1] - pts[0]).normalized(); ref = Vector((0, 0, 1)) if abs(t0.z) < 0.9 else Vector((1, 0, 0))
    u = t0.cross(ref).normalized(); prev = t0
    if side is not None:
        sv = P(*side); u = (sv - t0 * sv.dot(t0)).normalized()
    for i, (p, r) in enumerate(zip(pts, radii)):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        ax = prev.cross(t)
        if ax.length > 1e-6: u = Matrix.Rotation(prev.angle(t), 3, ax.normalized()) @ u
        prev = t; v = t.cross(u).normalized()
        sx, sy = flat or (1.0, 1.0)
        if r <= 1e-6: rings.append([bm.verts.new(p)] * M)
        else: rings.append([bm.verts.new(p + u * (math.cos(k * math.tau / M) * r * sx) + v * (math.sin(k * math.tau / M) * r * sy)) for k in range(M)])
    for a, b in zip(rings, rings[1:]):
        for k in range(M):
            vs = [a[k], a[(k + 1) % M], b[(k + 1) % M], b[k]]; vs = [x for j, x in enumerate(vs) if x not in vs[:j]]
            if len(vs) >= 3: bm.faces.new(vs)
    if cap:
        for ring, rev in ((rings[0], True), (rings[-1], False)):
            if len(set(ring)) == M: bm.faces.new(list(reversed(ring)) if rev else ring)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, row, rnd)

def loft(name, secs, mat, row='plain', n_exp=2.6, M=24, cap=True):
    """a rounded-square mass lofted through sections (z, cf, hw, hd, cx): superellipse rings, smooth sides (beast_blender.py)."""
    M = segs(M, 8); bm = bmesh.new(); rings = []
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
    return put(name, bm, mat, row, True)

def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def blade(w, t): return [(-w / 2, -t / 2), (w / 2, -t / 2), (0, t / 2)]

def card(name, corners, mat):
    """a quad (four design-coord corners, counter-clockwise seen from its front) with 0-1 UVs (glow, flame and smoke cards)."""
    bm = bmesh.new(); bm.faces.new([bm.verts.new(P(*c)) for c in corners]); return put(name, bm, mat, 'card', 'flat')

def disc(name, r, z, mat, n=24, cx=0.0, cf=0.0, row='plain', up=True):
    n = segs(n, 8); bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(P(cx + math.cos(i * math.tau / n) * r, cf + math.sin(i * math.tau / n) * r, z)) for i in range(n)])
    f.normal_update()
    if (f.normal.z < 0) == up: f.normal_flip()
    return put(name, bm, mat, row, True)

def uv_trim(ob, row):
    """trim-sheet UVs: turned and swept sides wrap the band around (u = arc length, v = height within the row); flat faces project on
    their main plane; a list row picks the row by face height [(z0, z1, row)]; 'card' = the whole 0-1 square."""
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    if row == 'wrap':  # the approved pillar texture (A3): u once around the column, v = height / 4 m
        for poly in me.polygons:
            cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
            us = [(math.atan2(c.y, c.x) / math.tau) % 1.0 for c in cs]
            if max(us) - min(us) > 0.5: us = [u + 1.0 if u < 0.5 else u for u in us]
            for li, c, u in zip(poly.loop_indices, cs, us): uvl.data[li].uv = (u, c.z / 4.0)
        return
    if row == 'card':
        for poly in me.polygons:
            for li, uv in zip(poly.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))): uvl.data[li].uv = uv
        return
    for poly in me.polygons:
        cz = sum(me.vertices[v].co.z for v in poly.vertices) / len(poly.vertices)
        rw = row
        if isinstance(row, list): rw = next((r for z0, z1, r in row if z0 <= cz <= z1), 'plain')
        y0, y1 = ROWS.get(rw, ROWS['plain']); h_img = (y1 - y0) / 1024.0
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        if ax != 2 and isinstance(row, list):
            cen = Vector((0, 0, 0))
            angs = [math.atan2(c.y - cen.y, c.x - cen.x) for c in cs]; ref = angs[0]
            angs = [a + math.tau if a - ref < -math.pi else a - math.tau if a - ref > math.pi else a for a in angs]
            vmin = min(c.z for c in cs); span = max(max(c.z for c in cs) - vmin, 1e-6) / M_PER_UV; k = min(1.0, h_img / span)
            rr = max(math.hypot(c.x, c.y) for c in cs)
            for li, c, a in zip(poly.loop_indices, cs, angs): uvl.data[li].uv = (a * rr / M_PER_UV, 1.0 - (y0 / 1024.0 + (c.z - vmin) / M_PER_UV * k))
            continue
        ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        vmin = min(c[va] for c in cs); span = max(max(c[va] for c in cs) - vmin, 1e-6) / M_PER_UV; k = min(1.0, h_img / span)
        for li, c in zip(poly.loop_indices, cs): uvl.data[li].uv = (c[ua] / M_PER_UV, 1.0 - (y0 / 1024.0 + (c[va] - vmin) / M_PER_UV * k))

def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

def finish(name, bevel=False):
    """UVs, materials, bevel on sharp parts (LOD0), smooth rounded parts with split edges over SHARP_DEG; joins PARTS into one object."""
    for ob, mat, row, rnd in PARTS:
        uv_trim(ob, row); ob.data.materials.append(material(mat))
        bm = bmesh.new(); bm.from_mesh(ob.data)
        if bevel and rnd is False: bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
        for f in bm.faces: f.smooth = rnd is True
        if rnd is True:
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
        bm.to_mesh(ob.data); bm.free()
    if os.environ.get('PARTS_REPORT'):  # tris per part (budget work)
        import collections; c = collections.Counter()
        for ob, *_ in PARTS: c[ob.name.rstrip('0123456789_-.')] += sum(len(p.vertices) - 2 for p in ob.data.polygons)
        print(name, c.most_common())
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0][0]
    if len(PARTS) > 1: bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    PARTS.clear()
    return ob

def decimate(ob, ratio):
    dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = ratio
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='dec')
    ob.data.validate(); ob.data.update()  # decimation can leave degenerate faces (exporter warned 'not valid')
    return ob

def lods(prefix, build, ratio2=0.4, lod1_seg=0.5):
    """LOD0 (full detail, bevels), LOD1 (half segments, no small parts), LOD2 (LOD1 decimated by ratio2)."""
    Q['seg'] = lod1_seg; build(False); l1 = finish(prefix + '_lod1')
    build(False); l2 = decimate(finish(prefix + '_lod2'), ratio2)
    Q['seg'] = 1.0; build(True); l0 = finish(prefix + '_lod0', True)
    return l0, l1, l2

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def bounds(ob):
    bb = [ob.matrix_world @ v.co for v in ob.data.vertices]
    return (min(c.x for c in bb), max(c.x for c in bb)), (min(c.y for c in bb), max(c.y for c in bb)), (min(c.z for c in bb), max(c.z for c in bb))

def smooth_share(ob): return sum(1 for p in ob.data.polygons if p.use_smooth) / max(1, len(ob.data.polygons))

def mats(ob): return {m.name for m in ob.data.materials}

class Gates:
    def __init__(self): self.n = 0; self.fails = 0; self.lines = []
    def __call__(self, ok, line):
        self.n += 1; self.fails += 0 if ok else 1; s = ('PASS ' if ok else 'FAIL ') + line; print(s); self.lines.append(s)
    def done(self): s = f'{self.n - self.fails} of {self.n} pass'; print(s); self.lines.append(s); return self.fails

def export(path, spread=()):
    """spread: objects moved aside along x (LOD1 at +3 m, LOD2 at +6 m, as W1a's GLBs; the viewer places LODs itself)."""
    for ob, dx in spread: ob.location.x = dx
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', export_materials='EXPORT', export_image_format='NONE', export_extras=True,
                              export_animations=True)
    import os; print('wrote', path, os.path.getsize(path), 'bytes')
