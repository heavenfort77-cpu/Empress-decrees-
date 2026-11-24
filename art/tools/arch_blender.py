# Palace architecture pieces B1-B11 (art/ASSET-LIST.md) and the small dressing meshes for A16, A19, A20: own designs, built in Blender
# from hard planes and prisms (round where round: pillars, rafters, posts, tile ridges; sharp where sharp: walls, terraces, frames).
# Sizes follow the game's CONFIG.PALACE (walls 4 m high and 0.5 m thick, doors 4 x 3.5 m, pillar radius 0.6 m footprint, the black lake
# at -6 m) and real proportions from the research (docs/research/Qin-palace-medieval-tech-fusion.md: stepped rammed-earth terraces on
# river-stone footings, timber halls, grey tile with round tile ends, hollow-brick parapets, paired 阙, timber trestle bridge); the
# research is reference only, nothing is copied.
#
# Every piece is one GLB in OUTDIR (Y up, north = -Z in three.js), one mesh primitive per material (one draw call each); single props
# carry <piece>_lod0/1/2 nodes. Material names map to textures in art/viewer/arch.html (and later CONFIG.TEX.files):
#   palWall hall_wall, palFloor hall_floor, palTileEnd tile_ends, palPillar pillar, palDoor door, palBronze bronze_trim (approved A1-A4, A13 by its owner);
#   palEarth rammed_earth, palEarthCore rammed_earth_core, palRiver river_stone, palStone stone_paving, palTiles floor_tiles,
#   palBrick hollow_brick, palMural mural_wall, palRoof roof_tile, palTimber timber, palLacquer timber x lacquer tint, palGround
#   garden_ground, palPlant garden_plants, palFlag signal_flags, palSlips slips, palStars star_ceiling.
#   Burnt state (A18) is a material swap in the viewer: palTimber/palLacquer/palPillar/palDoor -> timber_burnt, palEarth -> earth_burnt,
#   palWall/palMural -> wall_burnt, palSlips -> slips_burnt.
# UVs: 4 m per UV unit (1024 px = 256 px/m) on every axis; walls span their 4 m height once (as the game's PALUV); timber grain runs
# along each member's long axis (v); pillars wrap once around; door leaves map the door image over the whole 4 x 3.5 m face.
# Gates printed PASS/FAIL: triangles per piece and LOD against the budget, texel density 205-320 px/m on 95% of the surface (both
# principal directions), key dimensions against CONFIG.
# Usage: python arch_blender.py OUTDIR   (bpy 5.3)
import bpy, bmesh, math, sys, os, json
from mathutils import Vector, Matrix

OUT = sys.argv[-1] if not sys.argv[-1].endswith('.py') else '/tmp/arch'
os.makedirs(OUT, exist_ok=True)

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Game sizes (index.html CONFIG.PALACE): wall height, low wall height, wall thickness, door width and height, lake height, m.
WALL_H, LOW_H, WALL_T, DOOR_W, DOOR_H, LAKE_Y = 4.0, 0.8, 0.5, 4.0, 3.5, -6.0
# Segment length of every instanced run (walls, eaves, terraces, parapets, bridge bays), m.
SEG = 4.0
# Metres per UV unit (1024 px texture = 4 m: 256 px/m).
M_UV = 4.0
# Texel density gate: px/m range (0.8x-1.25x of 256) and the share of surface that must be inside it.
DENS = (204.8, 320.0, 0.95)
# Triangle budgets: an instanced repeat, and a single prop's LOD0/1/2 (palace study).
INST_BUDGET, SINGLE_BUDGET = 300, (7000, 2500, 800)
# Pillar: shaft radius, base plinth size and heights, sleeve band height (the bronze trim sheet's 'clouds' row is 0.25 m).
PIL_R, PIL_PLINTH, PIL_BASE_H, SLEEVE_H = 0.55, 1.5, 0.45, 0.25
# Eave: overhang beyond the wall face, rise over the wall, cover-tile pitch (texture: 0.5 m pairs, cover tile centre at 0.418 m).
EAVE_OUT, EAVE_RISE, TILE_PITCH, TILE_X0 = 1.0, 0.55, 0.5, 99 / 256
# Tile-end disc radius (texture atlas: 26 px), m.
TILE_END_R = 0.1
# Terrace edge profile (y outward = +y like every edge piece (three.js -z), z): coping, first face, ledge, second face, river-stone footing into the lake.
TERRACE = [(0.0, 0.0), (0.05, -0.25), (0.4, -2.6), (1.4, -2.6), (1.8, -5.0), (2.0, -5.0), (2.4, -6.5)]
# Bridge: bay length, deck widths of the two variants, post radius, rail height (CONFIG lowH).
BRIDGE_W = (8.0, 12.0)
# 阙 tower: earth base footprint and height, gallery height, roof rise, passage between the pair, m.
QUE_BASE, QUE_H, QUE_GAL, QUE_ROOF, QUE_GAP = (6.0, 5.0), 7.0, 2.6, 2.2, 8.0
# Throne dais tiers (w, d, h) and throne couch, m (the game's dais block is 12 x 6 x 1.5; this one is out of reach at 2.2 m).
DAIS = [(12.0, 7.0, 1.0), (9.0, 5.0, 1.0), (7.0, 3.6, 0.8)]
# Lacquer tint over the timber texture (palLacquer): material colour, applied in the viewer.
LACQUER_TINT = '#5a4f4a'

# geometry ------------------------------------------------------------------------------------------------------------
PARTS = []   # (object, material, uv function)

def new_obj(name, bm, mat, uvf):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, mat, uvf))
    return ob

def box(name, x0, x1, y0, y1, z0, z1, mat, uvf, skip=()):
    """axis box; skip = faces left out where nothing sees them ('-z' bottom, '+y' back...)."""
    bm = bmesh.new()
    v = {}
    for i, x in enumerate((x0, x1)):
        for j, y in enumerate((y0, y1)):
            for k, z in enumerate((z0, z1)): v[i, j, k] = bm.verts.new((x, y, z))
    F = {'-x': [(0, 0, 0), (0, 0, 1), (0, 1, 1), (0, 1, 0)], '+x': [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],
         '-y': [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], '+y': [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
         '-z': [(0, 0, 0), (0, 1, 0), (1, 1, 0), (1, 0, 0)], '+z': [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]}
    for k, f in F.items():
        if k not in skip: bm.faces.new([v[c] for c in f])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    return new_obj(name, bm, mat, uvf)

def frustum(name, cx, cy, z0, z1, w0, d0, w1, d1, mat, uvf, skip_bottom=True):
    """a battered block: rectangle w0 x d0 at z0 tapering to w1 x d1 at z1."""
    bm = bmesh.new()
    lo = [bm.verts.new((cx + sx * w0 / 2, cy + sy * d0 / 2, z0)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    hi = [bm.verts.new((cx + sx * w1 / 2, cy + sy * d1 / 2, z1)) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for i in range(4): bm.faces.new([lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]])
    bm.faces.new(hi)
    if not skip_bottom: bm.faces.new(list(reversed(lo)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mat, uvf)

def profile_x(name, prof, x0, x1, mats, uvf, side=1):
    """extrude a (y, z) profile along x; one quad per profile edge; mats = material per edge (list) -> one object per material.
    side 1: the face normal is (dz, -dy) of each profile edge (a profile walked outward and down, e.g. the terrace); -1 the other way
    (a cap walked left to right)."""
    groups = {}
    for i in range(len(prof) - 1): groups.setdefault(mats[i], []).append(i)
    for m, idx in groups.items():
        bm = bmesh.new()
        for i in idx:
            (ya, za), (yb, zb) = prof[i], prof[i + 1]
            q = [bm.verts.new((x0, ya, za)), bm.verts.new((x0, yb, zb)), bm.verts.new((x1, yb, zb)), bm.verts.new((x1, ya, za))]
            bm.faces.new(q)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bm.normal_update()
        for f, i in zip(bm.faces, idx):  # orient each face by its profile edge
            (ya, za), (yb, zb) = prof[i], prof[i + 1]
            want = Vector((0, (zb - za) * side, -(yb - ya) * side))
            if f.normal.dot(want) < 0: f.normal_flip()
        new_obj(f'{name}_{m}', bm, m, uvf)

def cyl(name, cx, cy, z0, z1, r0, r1, n, mat, uvf, caps=(False, True), smooth=True):
    bm = bmesh.new()
    lo = [bm.verts.new((cx + math.cos(i * math.tau / n) * r0, cy + math.sin(i * math.tau / n) * r0, z0)) for i in range(n)]
    hi = [bm.verts.new((cx + math.cos(i * math.tau / n) * r1, cy + math.sin(i * math.tau / n) * r1, z1)) for i in range(n)]
    for i in range(n):
        f = bm.faces.new([lo[i], lo[(i + 1) % n], hi[(i + 1) % n], hi[i]]); f.smooth = smooth
    if caps[0]: bm.faces.new(list(reversed(lo)))
    if caps[1]: bm.faces.new(hi)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return new_obj(name, bm, mat, uvf)

def tube(name, a, b, r, n, mat, uvf, caps=True, half=False):
    """a round member from a to b (rafters, posts, braces); half = only the upper half (cover tiles)."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(up).normalized(); w = u.cross(d).normalized()
    if w.z < 0: w = -w
    angs = [math.pi * i / n for i in range(n + 1)] if half else [math.tau * i / n for i in range(n)]
    bm = bmesh.new()
    ra = [bm.verts.new(a + (u * math.cos(t) + w * math.sin(t)) * r) for t in angs]
    rb = [bm.verts.new(b + (u * math.cos(t) + w * math.sin(t)) * r) for t in angs]
    m = len(angs)
    for i in range(m - 1 if half else m):
        f = bm.faces.new([ra[i], ra[(i + 1) % m], rb[(i + 1) % m], rb[i]]); f.smooth = True
    if caps and not half: bm.faces.new(list(reversed(ra))); bm.faces.new(rb)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if half:
        for f in bm.faces:
            if f.normal.z < -0.2: f.normal_flip()
    return new_obj(name, bm, mat, uvf)

def quad(name, pts, mat, uvf, two_sided=False):
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in pts]; bm.faces.new(vs)
    if two_sided: bm.faces.new(list(reversed([bm.verts.new(p) for p in pts])))
    return new_obj(name, bm, mat, uvf)

def rock(name, c, r, mat, uvf, seed):
    """an irregular rubble stone: a low icosphere, scaled and pushed per vertex (seeded)."""
    import random
    rnd = random.Random(seed)
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    for v in bm.verts: v.co = Vector((v.co.x * r[0], v.co.y * r[1], v.co.z * r[2])) * rnd.uniform(0.8, 1.15) + Vector(c)
    for f in bm.faces: f.smooth = False
    return new_obj(name, bm, mat, uvf)

# UV mappings -----------------------------------------------------------------------------------------------------------
def _uv(ob):
    me = ob.data
    return me, (me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap'))

def UV_WORLD(zoff=0.0, m=M_UV, ox=0.0, oy=0.0):
    """dominant-axis projection, m metres per UV unit; v = (z - zoff) / m on side faces (walls span their height once with m = 4)."""
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            n = p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co
                if ax == 2: uv = ((c.x - ox) / m, (c.y - oy) / m)
                elif ax == 1: uv = ((c.x - ox) / m, (c.z - zoff) / m)
                else: uv = ((c.y - oy) / m, (c.z - zoff) / m)
                uvl.data[li].uv = uv
    return f

def UV_GRAIN(axis):
    """timber: v along the member's long axis (0 x, 1 y, 2 z), u across; end grain faces get a plain projection."""
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            n = p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
            plane = [i for i in range(3) if i != ax]
            if axis in plane: va = axis; ua = plane[0] if plane[1] == axis else plane[1]
            else: ua, va = plane
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = (c[ua] / M_UV, c[va] / M_UV)
    return f

def UV_ALONG(a, b, r, v0=0.0, vs=1.0):
    """a round member of radius r from a to b: v = v0 + vs x (metres along / 4), u around (arc metres / 4); end caps planar."""
    a, b = Vector(a), Vector(b); d = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0)); u = d.cross(up).normalized(); w = u.cross(d).normalized()
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            if abs(p.normal.dot(d)) > 0.9:  # cap: planar across the member
                for li in p.loop_indices:
                    c = me.vertices[me.loops[li].vertex_index].co - a; uvl.data[li].uv = (c.dot(u) / M_UV, v0 + vs * c.dot(w) / M_UV)
                continue
            vals = []
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co - a
                vals.append([li, math.atan2(c.dot(w), c.dot(u)) % math.tau, c.dot(d)])
            if max(v[1] for v in vals) - min(v[1] for v in vals) > math.pi:
                for v in vals:
                    if v[1] < math.pi: v[1] += math.tau
            for li, ang, al in vals: uvl.data[li].uv = (ang * r / M_UV, v0 + vs * al / M_UV)
    return f

def UV_FACE():
    """each face projected on its own plane (exact 256 px/m at any tilt): rubble, debris, drums."""
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            n = p.normal; tng = n.cross(Vector((0, 0, 1))) if abs(n.z) < 0.95 else Vector((1, 0, 0))
            tng.normalize(); bt = n.cross(tng)
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = (c.dot(tng) / M_UV, c.dot(bt) / M_UV)
    return f

NOOP = lambda ob: None

def bake_uv(ob):
    """apply a part's UVs now (local coordinates, before it is moved), so moving it keeps the texel density."""
    for i, (o, m, uvf) in enumerate(PARTS):
        if o is ob: uvf(o); PARTS[i] = (o, m, NOOP)

def UV_CYL(cx, cy, z0, z1, u_per_turn, rows=(0, 1024)):
    """around a vertical axis: u = turns x u_per_turn, v from z0 (image row rows[1]) to z1 (row rows[0]); caps planar."""
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            ls = list(p.loop_indices)
            if abs(p.normal.z) > 0.9:
                for li in ls:
                    c = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = ((c.x - cx) / M_UV, (c.y - cy) / M_UV)
                continue
            vals = []
            for li in ls:
                c = me.vertices[me.loops[li].vertex_index].co
                t = (math.atan2(c.y - cy, c.x - cx) % math.tau) / math.tau
                if rows is None: vals.append([li, t, (c.z - z0) / M_UV]); continue
                k = (c.z - z0) / (z1 - z0); row = rows[1] - k * (rows[1] - rows[0])
                vals.append([li, t, 1 - row / 1024])
            ts = [v[1] for v in vals]
            if max(ts) - min(ts) > 0.5:
                for v in vals:
                    if v[1] < 0.5: v[1] += 1
            for li, t, vv in vals: uvl.data[li].uv = (t * u_per_turn, vv)
    return f

def UV_ROWS(r0, r1):
    """trim sheet rows r0-r1 (image px): each face maps from its own lowest edge (z on sides, y on tops) up the rows at 256 px/m;
    u along x (or y on x-facing faces). A face taller than the row runs on past r0 into the rows above (reported by the density gate
    only if it leaves the sheet), never squeezed."""
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            n = p.normal; ax = max(range(3), key=lambda i: abs(n[i]))
            ua, va = [(1, 2), (0, 2), (0, 1)][ax]
            cs = [me.vertices[me.loops[li].vertex_index].co for li in p.loop_indices]; vmin = min(c[va] for c in cs)
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co
                row = r1 - (c[va] - vmin) / M_UV * 1024
                uvl.data[li].uv = (c[ua] / M_UV, 1 - row / 1024)
    return f

def UV_DOOR(x0, w, z0, h):
    """door leaves: the door image over the whole opening (u over the width, v over the height); edges take the nearest column."""
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            ax = max(range(3), key=lambda i: abs(p.normal[i]))
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co
                uu, vv = (c.x - x0) / w, (c.z - z0) / h
                if ax == 0: uu = c.y / M_UV + (0.005 if c.x > x0 + w / 2 else 0.0)   # leaf edges: the bronze edge strip, at 256 px/m
                if ax == 2: vv = c.y / M_UV + (0.03 if c.z < z0 + h / 2 else 0.97)   # top and bottom edges
                uvl.data[li].uv = (uu, vv)
    return f

def UV_DISC(cx_px, cy_px, centre, axis=(0, 1, 0)):
    """tile end: the face looking along axis maps onto the atlas disc (centre px, tile_ends.png); rim faces map onto the dark board
    (rows 600-1000) around and along, all at 256 px/m."""
    ax = Vector(axis)
    def f(ob):
        me, uvl = _uv(ob)
        for p in me.polygons:
            face = abs(p.normal.dot(ax)) > 0.7
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co - Vector(centre)
                if face: uvl.data[li].uv = ((cx_px + c.x / M_UV * 1024) / 1024, 1 - (cy_px - c.z / M_UV * 1024) / 1024)
                else:
                    ang = math.atan2(c.z, c.x) % math.tau
                    uvl.data[li].uv = (ang * TILE_END_R / M_UV, 1 - (700 + c.dot(ax) / M_UV * 1024) / 1024)
    return f

def UV_CELL(x0, y0, w, h, ax_u=0):
    """a card: its bounding box maps onto an atlas cell (px rect, top-left origin)."""
    def f(ob):
        me, uvl = _uv(ob)
        cs = [v.co for v in me.vertices]
        umin = min(c[ax_u] for c in cs); umax = max(c[ax_u] for c in cs); zmin = min(c.z for c in cs); zmax = max(c.z for c in cs)
        for p in me.polygons:
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co
                a = (c[ax_u] - umin) / max(umax - umin, 1e-6); b = (c.z - zmin) / max(zmax - zmin, 1e-6)
                uvl.data[li].uv = ((x0 + a * w) / 1024, 1 - (y0 + (1 - b) * h) / 1024)
    return f

# assembly, gates, export ------------------------------------------------------------------------------------------------
def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

def finish(name, sharp_deg=40):
    """apply UVs and materials, join every part into one object (one primitive per material), smooth round parts only."""
    for ob, mat, uvf in PARTS:
        uvf(ob)
        ob.data.materials.append(material(mat))
        bm = bmesh.new(); bm.from_mesh(ob.data)
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(sharp_deg): e.smooth = False
        bm.to_mesh(ob.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0][0]
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    PARTS.clear()
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

RESULTS = []; FAILS = [0]; REPORT = {}
def gate(ok, line):
    RESULTS.append(('PASS ' if ok else 'FAIL ') + line); FAILS[0] += 0 if ok else 1; print(RESULTS[-1])

def density(ob, skip_mats=()):
    """share of surface area whose texel density (both principal directions of the UV map) is inside DENS; min and max seen."""
    me = ob.data; uvl = me.uv_layers['UVMap']
    me.calc_loop_triangles()
    good = total = 0.0; lo, hi = 1e9, 0
    for lt in me.loop_triangles:
        if me.materials[lt.material_index].name in skip_mats: continue
        P_ = [me.vertices[v].co for v in lt.vertices]; U = [uvl.data[l].uv * 1024 for l in lt.loops]
        e1, e2 = P_[1] - P_[0], P_[2] - P_[0]; area = e1.cross(e2).length / 2
        if area < 1e-4: continue
        # orthonormal frame in the triangle plane
        ax = e1.normalized(); ay = e1.cross(e2).cross(e1).normalized()
        a = (e1.dot(ax), e1.dot(ay)); b = (e2.dot(ax), e2.dot(ay))
        du1, du2 = U[1] - U[0], U[2] - U[0]
        det = a[0] * b[1] - a[1] * b[0]
        if abs(det) < 1e-12: continue
        # Jacobian J (uv per metre): J @ [a b] = [du1 du2]
        inv = ((b[1] / det, -b[0] / det), (-a[1] / det, a[0] / det))
        J = [[du1.x * inv[0][0] + du2.x * inv[1][0], du1.x * inv[0][1] + du2.x * inv[1][1]],
             [du1.y * inv[0][0] + du2.y * inv[1][0], du1.y * inv[0][1] + du2.y * inv[1][1]]]
        p_ = J[0][0] ** 2 + J[1][0] ** 2; q_ = J[0][1] ** 2 + J[1][1] ** 2; r_ = J[0][0] * J[0][1] + J[1][0] * J[1][1]
        tr, dt = p_ + q_, p_ * q_ - r_ * r_
        s1 = math.sqrt(max(0, (tr + math.sqrt(max(0, tr * tr / 4 - dt) * 4)) / 2)); s2 = math.sqrt(max(0, (tr - math.sqrt(max(0, tr * tr / 4 - dt) * 4)) / 2))
        total += area
        if DENS[0] <= s2 and s1 <= DENS[1]: good += area
        lo = min(lo, s2); hi = max(hi, s1)
    return (good / total if total else 1.0), lo, hi

def check(ob, budget, dens_skip=()):
    t = tris(ob)
    gate(t <= budget, f'{ob.name} tris {t} (budget {budget})')
    share, lo, hi = density(ob, dens_skip)
    gate(share >= DENS[2], f'{ob.name} texel density {share:.0%} of surface in {DENS[0]:.0f}-{DENS[1]:.0f} px/m (min {DENS[2]:.0%}); range {lo:.0f}-{hi:.0f}')
    REPORT[ob.name] = dict(tris=t, budget=budget, dens_share=round(share, 3), mats=[m.name for m in ob.data.materials])
    return t

def export(fname, objs):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
        for c in o.children_recursive: c.select_set(True)
    path = os.path.join(OUT, fname + '.glb')
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_materials='EXPORT', export_image_format='NONE', export_apply=True)
    REPORT.setdefault('_files', []).append(fname + '.glb')
    for o in list(bpy.data.objects): bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes): bpy.data.meshes.remove(m)

def dims(ob):
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    return [max(c[i] for c in bb) - min(c[i] for c in bb) for i in range(3)], [min(c[i] for c in bb) for i in range(3)], [max(c[i] for c in bb) for i in range(3)]

# Mutation hook for the gate test (ARCH_MUT=uv: UVs at 2 m per unit, density must fail; budget: 10-triangle budgets, budgets must fail;
# dims: walls built 3.5 m high, the CONFIG dimension gates must fail). Off unless the variable is set.
MUT = os.environ.get('ARCH_MUT', '')
if MUT == 'uv': M_UV = 2.0
if MUT == 'budget': INST_BUDGET, SINGLE_BUDGET = 10, (10, 10, 10)
WALL_GATE_H = WALL_H
if MUT == 'dims': WALL_H = 3.5
bpy.ops.wm.read_factory_settings(use_empty=True)
W = UV_WORLD()
def GR(a): return UV_GRAIN(a)

# B1 terrace edge ----------------------------------------------------------------------------------------------------------
mats = ['palStone', 'palEarth', 'palEarth', 'palEarth', 'palEarth', 'palRiver']
profile_x('terrace', TERRACE, 0, SEG, mats, W, side=-1)
ob = finish('terrace_edge'); check(ob, INST_BUDGET)
d, lo, hi = dims(ob); gate(abs(d[0] - SEG) < 1e-4 and lo[2] <= LAKE_Y - 0.2, f'terrace_edge {d[0]:.2f} m long, foot at {lo[2]:.2f} m (lake {LAKE_Y}: footing goes under water)')
export('terrace_edge', [ob])

# B2 wall segment and low wall ----------------------------------------------------------------------------------------------
t = WALL_T / 2
box('wall', 0, SEG, -t, t, 0.2, WALL_H, 'palWall', W, skip=('-z', '-x', '+x'))
box('plinth', 0, SEG, -t - 0.06, t + 0.06, 0, 0.2, 'palStone', W, skip=('-z', '-x', '+x'))
box('pilaster', 0, 0.35, -t - 0.1, t + 0.1, 0.2, WALL_H, 'palLacquer', GR(2), skip=('-z',))
ob = finish('wall_seg'); check(ob, INST_BUDGET)
d, lo, hi = dims(ob); gate(abs(hi[2] - WALL_GATE_H) < 1e-4 and abs(d[0] - SEG) < 1e-4, f'wall_seg height {hi[2]:.2f} m (CONFIG wallH {WALL_GATE_H}), length {d[0]:.2f}, body thickness {WALL_T}')
export('wall_seg', [ob])
box('wall', 0, SEG, -t, t, 0.2, WALL_H, 'palMural', W, skip=('-z', '-x', '+x'))
box('plinth', 0, SEG, -t - 0.06, t + 0.06, 0, 0.2, 'palStone', W, skip=('-z', '-x', '+x'))
box('pilaster', 0, 0.35, -t - 0.1, t + 0.1, 0.2, WALL_H, 'palLacquer', GR(2), skip=('-z',))
ob = finish('wall_mural_seg'); check(ob, INST_BUDGET); export('wall_mural_seg', [ob])
box('foot', 0, SEG, -t - 0.12, t + 0.12, 0, 0.45, 'palRiver', W, skip=('-z', '-x', '+x'))
box('wall', 0, SEG, -t, t, 0.45, WALL_H, 'palEarthCore', W, skip=('-z', '-x', '+x'))
ob = finish('wall_earth_seg'); check(ob, INST_BUDGET); export('wall_earth_seg', [ob])
box('low', 0, SEG, -t, t, 0.15, LOW_H, 'palWall', W, skip=('-z', '-x', '+x'))
box('plinth', 0, SEG, -t - 0.06, t + 0.06, 0, 0.15, 'palStone', W, skip=('-z', '-x', '+x'))
profile_x('lowcap', [(-t - 0.08, LOW_H), (0, LOW_H + 0.16), (t + 0.08, LOW_H)], 0, SEG, ['palRoof', 'palRoof'], W, side=-1)
ob = finish('wall_low'); check(ob, INST_BUDGET)
d, lo, hi = dims(ob); gate(abs(hi[2] - (LOW_H + 0.16)) < 1e-3, f'wall_low height {hi[2]:.2f} m (CONFIG lowH {LOW_H} + tile cap 0.16)')
export('wall_low', [ob])

# B3 door: frame (lacquer), sill (stone), transom (wall), two leaves (door image; pivots at the hinges), locked bar (bronze) -----
hw = DOOR_W / 2
box('jambL', -hw - 0.3, -hw, -t - 0.08, t + 0.08, 0, DOOR_H + 0.35, 'palLacquer', GR(2), skip=('-z',))
box('jambR', hw, hw + 0.3, -t - 0.08, t + 0.08, 0, DOOR_H + 0.35, 'palLacquer', GR(2), skip=('-z',))
box('lintel', -hw - 0.45, hw + 0.45, -t - 0.12, t + 0.12, DOOR_H, DOOR_H + 0.35, 'palLacquer', GR(0))
box('sill', -hw, hw, -t - 0.1, t + 0.1, 0, 0.1, 'palStone', W, skip=('-z',))
box('transom', -hw - 0.3, hw + 0.3, -t, t, DOOR_H + 0.35, WALL_H, 'palWall', W, skip=('-z',))
frame = finish('door_frame')
LT = 0.12
box('leafL', -hw, 0, -LT / 2, LT / 2, 0.1, DOOR_H, 'palDoor', UV_DOOR(-hw, DOOR_W, 0.0, DOOR_H))
leafL = finish('door_leaf_L'); leafL.data.transform(Matrix.Translation((hw, 0, 0))); leafL.location = (-hw, 0, 0)
box('leafR', 0, hw, -LT / 2, LT / 2, 0.1, DOOR_H, 'palDoor', UV_DOOR(-hw, DOOR_W, 0.0, DOOR_H))
leafR = finish('door_leaf_R'); leafR.data.transform(Matrix.Translation((-hw, 0, 0))); leafR.location = (hw, 0, 0)
BY = -LT / 2 - 0.1
BZ = 0.55  # bar height offset above the 1.55 m first try: the door image's masks sit at 1.2-1.7 m, the bar goes above them
box('bar', -hw - 0.2, hw + 0.2, BY - 0.08, BY + 0.08, 1.55 + BZ, 1.75 + BZ, 'palBronze', UV_ROWS(576, 640))
for k, x in enumerate((-1.4, -0.5, 0.5, 1.4)):  # staples holding the bar, one pair per leaf
    box(f'stapleA{k}', x - 0.12, x - 0.06, BY - 0.12, -LT / 2, 1.45 + BZ, 1.85 + BZ, 'palBronze', UV_ROWS(40, 344))
    box(f'stapleB{k}', x + 0.06, x + 0.12, BY - 0.12, -LT / 2, 1.45 + BZ, 1.85 + BZ, 'palBronze', UV_ROWS(40, 344))
box('lockplate', -0.18, 0.18, BY - 0.12, BY - 0.08, 1.53 + BZ, 1.78 + BZ, 'palBronze', UV_ROWS(704, 768))
bar = finish('door_bar')
n = sum(check(o, INST_BUDGET if o is not frame else 400) for o in (frame, leafL, leafR, bar))
gate(n <= 600, f'door total tris {n} (one door, 5 materials)')
gate(abs(DOOR_W - (dims(leafL)[0][0] + dims(leafR)[0][0])) < 1e-4 and abs(dims(leafL)[2][2] - DOOR_H) < 1e-4, f'door leaves {dims(leafL)[0][0] + dims(leafR)[0][0]:.2f} x {dims(leafL)[2][2]:.2f} m (CONFIG doorW {DOOR_W} x doorH {DOOR_H})')
root = bpy.data.objects.new('door', None); bpy.context.collection.objects.link(root)
for o in (frame, leafL, leafR, bar): o.parent = root
export('door', [root])

# B4 pillar: stone plinth and drum, lacquer shaft (pillar image once around), bronze sleeve under the painted capital ------------
box('plinth', -PIL_PLINTH / 2, PIL_PLINTH / 2, -PIL_PLINTH / 2, PIL_PLINTH / 2, 0, 0.2, 'palStone', W, skip=('-z',))
cyl('drum', 0, 0, 0.2, PIL_BASE_H, 0.72, 0.64, 16, 'palStone', UV_CYL(0, 0, 0.2, PIL_BASE_H, 2 * math.pi * 0.68 / M_UV, None), smooth=True)
cyl('shaft', 0, 0, PIL_BASE_H, WALL_H, PIL_R, PIL_R, 16, 'palPillar', UV_CYL(0, 0, PIL_BASE_H, WALL_H, 1.0), caps=(False, True))
SZ = 3.15
cyl('sleeve', 0, 0, SZ, SZ + SLEEVE_H, PIL_R + 0.035, PIL_R + 0.035, 16, 'palBronze', UV_CYL(0, 0, SZ, SZ + SLEEVE_H, 2 * math.pi * (PIL_R + 0.035) / M_UV, (384, 448)), caps=(True, True))
for k, z in enumerate((SZ - 0.05, SZ + SLEEVE_H)):
    cyl(f'flange{k}', 0, 0, z, z + 0.05, PIL_R + 0.06, PIL_R + 0.06, 16, 'palBronze', UV_CYL(0, 0, z, z + 0.05, 2 * math.pi * (PIL_R + 0.06) / M_UV, (576, 589)), caps=(True, True))
ob = finish('pillar'); check(ob, INST_BUDGET)
d, lo, hi = dims(ob); gate(d[0] <= 1.5 + 1e-4 and abs(hi[2] - WALL_GATE_H) < 1e-4, f'pillar footprint {d[0]:.2f} m, height {hi[2]:.2f} m (game pillar: 1.2 m solid, {WALL_GATE_H} m)')
export('pillar', [ob])

# B5 eave edge (instanced) and the tile end (instanced, 8 per segment) ---------------------------------------------------------
ez0 = WALL_H + 0.05
box('plate', 0, SEG, -t - 0.05, t + 0.05, WALL_H - 0.2, ez0, 'palTimber', GR(0), skip=('-z',))
y_edge, z_edge, y_top, z_top = t + EAVE_OUT, ez0 + 0.12, -t - 0.1, ez0 + 0.12 + EAVE_RISE
for i in range(9):  # round rafters under the tiles, ends showing past the eave
    x = 0.22 + i * 0.445
    tube(f'raft{i}', (x, y_top + 0.2, ez0 + EAVE_RISE * 0.85), (x, y_edge + 0.1, ez0 + 0.02), 0.07, 5, 'palTimber', UV_ALONG((x, y_top + 0.2, ez0 + EAVE_RISE * 0.85), (x, y_edge + 0.1, ez0 + 0.02), 0.07))
SLOPE = math.hypot(y_edge - y_top, z_top - z_edge)
def uv_slope(ob):  # v down the slope from row 300 (top) to the eave, u along x; 4 m per unit
    me, uvl = _uv(ob)
    for p in me.polygons:
        for li in p.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            s = (y_top - c.y) / (y_top - y_edge) * SLOPE if abs(p.normal.z) > 0.3 else SLOPE + (z_edge - c.z)
            uvl.data[li].uv = (c.x / M_UV, -s / M_UV)
quad('slope', [(0, y_top, z_top), (SEG, y_top, z_top), (SEG, y_edge, z_edge), (0, y_edge, z_edge)], 'palRoof', uv_slope)
quad('edgeboard', [(0, y_edge, z_edge), (SEG, y_edge, z_edge), (SEG, y_edge, z_edge - 0.08), (0, y_edge, z_edge - 0.08)], 'palRoof', uv_slope)
for i in range(8):  # cover-tile ridges over the painted cover stripes
    x = TILE_X0 + i * TILE_PITCH
    tube(f'cover{i}', (x, y_top, z_top + 0.0), (x, y_edge, z_edge), 0.075, 4, 'palRoof', UV_ALONG((x, y_top, z_top), (x, y_edge, z_edge), 0.075), caps=False, half=True)
ob = finish('eave_seg'); check(ob, INST_BUDGET); export('eave_seg', [ob])
# tile end: disc facing +y (outward) at the origin; UV onto atlas disc 0 (row 836); instances pick the atlas disc by uv offset in the viewer
bm = bmesh.new(); n = 10
front = [bm.verts.new((math.cos(i * math.tau / n) * TILE_END_R, 0.0, math.sin(i * math.tau / n) * TILE_END_R)) for i in range(n)]
back = [bm.verts.new((math.cos(i * math.tau / n) * TILE_END_R, -0.04, math.sin(i * math.tau / n) * TILE_END_R)) for i in range(n)]
bm.faces.new(list(reversed(front)))
for i in range(n): bm.faces.new([front[i], front[(i + 1) % n], back[(i + 1) % n], back[i]])
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
new_obj('tile_end', bm, 'palTileEnd', UV_DISC(64, 128, (0, 0, 0)))
ob = finish('tile_end'); check(ob, 60, dens_skip=()); export('tile_end', [ob])

# B6 阙 gate towers, paired (single prop, LOD0/1/2) --------------------------------------------------------------------------
LOD2 = [False]  # far LOD: masses only (no posts, beams, ridges)

def hip_roof(nm, cx, cy, z, w, d, rise, over, detail):
    """hip roof with straight eaves (no upturn, no beasts), grey tile; cover-tile ridges and tile ends at LOD0."""
    W2, D2 = w / 2 + over, d / 2 + over; rl = max(0.0, (W2 - D2))
    e = [(cx - W2, cy - D2, z), (cx + W2, cy - D2, z), (cx + W2, cy + D2, z), (cx - W2, cy + D2, z)]
    r0, r1 = (cx - rl, cy, z + rise), (cx + rl, cy, z + rise)
    def uvr(ob):  # each slope: u along its eave, v up the slope, 4 m per unit, rows 0-768 (tile field)
        me, uvl = _uv(ob)
        for p in me.polygons:
            nrm = p.normal; hz = Vector((nrm.x, nrm.y, 0)); hz = hz.normalized() if hz.length > 1e-6 else Vector((0, -1, 0))
            side = Vector((-hz.y, hz.x, 0))
            for li in p.loop_indices:
                c = me.vertices[me.loops[li].vertex_index].co
                vv = ((c.z - z) / rise) * math.hypot(rise, D2) if rise else 0
                uvl.data[li].uv = (Vector((c.x, c.y, 0)).dot(side) / M_UV, vv / M_UV)
        return
    quad(nm + 's', [e[0], e[1], r1, r0], 'palRoof', uvr); quad(nm + 'n', [e[2], e[3], r0, r1], 'palRoof', uvr)
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in (e[1], e[2], r1)]; bm.faces.new(vs); new_obj(nm + 'e', bm, 'palRoof', uvr)
    bm = bmesh.new(); vs = [bm.verts.new(p) for p in (e[3], e[0], r0)]; bm.faces.new(vs); new_obj(nm + 'w', bm, 'palRoof', uvr)
    if LOD2[0]: return
    ra, rb = (r0[0] - 0.2, r0[1], r0[2]), (r1[0] + 0.2, r1[1], r1[2])
    tube(nm + 'ridge', ra, rb, 0.14, 6 if detail else 4, 'palRoof', UV_ALONG(ra, rb, 0.14))
    for a, b in ((e[0], r0), (e[1], r1), (e[2], r1), (e[3], r0)):
        tube(nm + 'hip', a, b, 0.1, 5 if detail else 3, 'palRoof', UV_ALONG(a, b, 0.1), caps=False)
    if detail:  # cover-tile ridges on the long slopes, tile ends along the eave (merged: this is a single prop)
        nx = int((2 * W2 - 1.0) / TILE_PITCH)
        for sgn, ye in ((-1, cy - D2), (1, cy + D2)):
            for i in range(nx):
                x = cx - W2 + 0.5 + i * TILE_PITCH
                frac = 1 - abs(x - cx) / W2
                ztop = z + rise * min(1.0, (W2 - abs(x - cx)) / D2) if abs(x - cx) > rl else z + rise
                ytop = cy + sgn * (D2 - (ztop - z) / rise * D2)
                tube(nm + f'cv{sgn}{i}', (x, ytop, ztop + 0.02), (x, ye, z + 0.02), 0.07, 3, 'palRoof', UV_ALONG((x, ytop, ztop), (x, ye, z), 0.07), caps=False, half=True)
                bm = bmesh.new(); k = 8
                ring = [bm.verts.new((x + math.cos(j * math.tau / k) * TILE_END_R, ye + sgn * 0.01, z + math.sin(j * math.tau / k) * TILE_END_R)) for j in range(k)]
                f = bm.faces.new(ring if sgn > 0 else list(reversed(ring)))
                new_obj(nm + f'te{sgn}{i}', bm, 'palTileEnd', UV_DISC(64 + 128 * (i % 8), 128 if sgn < 0 else 384, (x, ye, z)))

def que_tower(nm, cx, sgn, detail):
    bw, bd = QUE_BASE
    if not LOD2[0]: box(nm + 'foot', cx - bw / 2 - 0.3, cx + bw / 2 + 0.3, -bd / 2 - 0.3, bd / 2 + 0.3, 0, 0.5, 'palRiver', W, skip=('-z',))
    frustum(nm + 'base', cx, 0, 0.5, QUE_H, bw, bd, bw - 0.9, bd - 0.9, 'palEarth', W)
    box(nm + 'cope', cx - (bw - 0.9) / 2 - 0.1, cx + (bw - 0.9) / 2 + 0.1, -(bd - 0.9) / 2 - 0.1, (bd - 0.9) / 2 + 0.1, QUE_H, QUE_H + 0.2, 'palStone', W, skip=('-z',))
    gw, gd = bw - 1.6, bd - 1.6; z0 = QUE_H + 0.2
    box(nm + 'gal', cx - gw / 2, cx + gw / 2, -gd / 2, gd / 2, z0, z0 + QUE_GAL, 'palWall', UV_ROWS(170, 760), skip=('-z', '+z'))
    nposts = 0 if LOD2[0] else 3 if detail else 2
    for i in range(nposts):
        for j in range(nposts):
            if 0 < i < nposts - 1 and 0 < j < nposts - 1: continue
            px = cx - gw / 2 - 0.05 + i * (gw + 0.1) / (nposts - 1); py = -gd / 2 - 0.05 + j * (gd + 0.1) / (nposts - 1)
            if detail or (i in (0, nposts - 1) and j in (0, nposts - 1)):
                cyl(nm + f'post{i}{j}', px, py, z0, z0 + QUE_GAL, 0.16, 0.16, 8 if detail else 5, 'palLacquer', UV_CYL(px, py, z0, z0 + QUE_GAL, 2 * math.pi * 0.16 / M_UV, None))
    if not LOD2[0]: box(nm + 'beam', cx - gw / 2 - 0.25, cx + gw / 2 + 0.25, -gd / 2 - 0.25, gd / 2 + 0.25, z0 + QUE_GAL, z0 + QUE_GAL + 0.3, 'palTimber', GR(0))
    if detail:
        for i in range(4):  # cantilevered bracket arms under the eaves
            x = cx - gw / 2 + 0.4 + i * (gw - 0.8) / 3
            for sy in (-1, 1):
                box(nm + f'arm{i}{sy}', x - 0.1, x + 0.1, sy * gd / 2 - (0.1 if sy > 0 else 0.9), sy * gd / 2 + (0.9 if sy > 0 else 0.1), z0 + QUE_GAL - 0.25, z0 + QUE_GAL, 'palTimber', GR(1))
    hip_roof(nm + 'roof', cx, 0, z0 + QUE_GAL + 0.3, gw + 0.5, gd + 0.5, QUE_ROOF, 1.1, detail)
    # 子阙: the lower attached tower on the outer side
    sx = cx + sgn * (bw / 2 + 1.6)
    if not LOD2[0]: box(nm + 'sfoot', sx - 1.9, sx + 1.9, -1.9, 1.9, 0, 0.5, 'palRiver', W, skip=('-z',))
    frustum(nm + 'sbase', sx, 0, 0.5, 4.6, 3.4, 3.4, 2.8, 2.8, 'palEarth', W)
    hip_roof(nm + 'sroof', sx, 0, 4.6, 2.8, 2.8, 1.3, 0.7, detail)
    if detail:  # a signal flag on the gallery (A19)
        fx = cx + sgn * (gw / 2 - 0.3)
        cyl(nm + 'pole', fx, -gd / 2 - 0.3, z0, z0 + QUE_GAL + QUE_ROOF + 2.2, 0.05, 0.04, 6, 'palTimber', UV_CYL(fx, -gd / 2 - 0.3, z0, z0 + 7, 2 * math.pi * 0.045 / M_UV, None))
        zf = z0 + QUE_GAL + QUE_ROOF + 1.0
        quad(nm + 'flag', [(fx, -gd / 2 - 0.3, zf), (fx + sgn * 1.17, -gd / 2 - 0.3, zf), (fx + sgn * 1.17, -gd / 2 - 0.3, zf + 0.78), (fx, -gd / 2 - 0.3, zf + 0.78)],
             'palFlag', UV_CELL(2 * 1024 / 3 + 12, 40, 1024 / 3 - 30, 1024 / 3 * 0.62), two_sided=True)

lods = []
for li, detail in enumerate((True, False)):
    for sgn in (-1, 1):
        que_tower(f'q{sgn}', sgn * (QUE_GAP / 2 + QUE_BASE[0] / 2), sgn, detail)
    lods.append(finish(f'que_pair_lod{li}'))
LOD2[0] = True
que_tower('q-1', -(QUE_GAP / 2 + QUE_BASE[0] / 2), -1, False); que_tower('q1', QUE_GAP / 2 + QUE_BASE[0] / 2, 1, False)
LOD2[0] = False
lods.append(finish('que_pair_lod2'))
for o, b in zip(lods, SINGLE_BUDGET): check(o, b)
d, lo, hi = dims(lods[0]); gate(hi[2] >= 12, f'que_pair height {hi[2]:.1f} m (towers read above the 4 m walls), width {d[0]:.1f} m, passage {QUE_GAP} m')
root = bpy.data.objects.new('que_pair', None); bpy.context.collection.objects.link(root)
for o in lods: o.parent = root
export('que_pair', [root])

# B7 crenellated wall-walk (instanced): rammed-earth wall on a river-stone footing, merlons, timber walk on the court side ---------
box('foot', 0, SEG, -t - 0.15, t + 0.15, 0, 0.5, 'palRiver', W, skip=('-z', '-x', '+x'))
box('wall', 0, SEG, -t, t, 0.5, WALL_H, 'palEarth', W, skip=('-z', '-x', '+x'))
for i in range(4):
    x = 0.2 + i * 1.0
    box(f'merlon{i}', x, x + 0.6, -t, t, WALL_H, WALL_H + 0.7, 'palEarth', W, skip=('-z',))
box('deck', 0, SEG, -t - 1.1, -t, 3.0, 3.12, 'palTimber', GR(1), skip=())
for x in (0.6, 3.4):
    box(f'joist{x}', x - 0.08, x + 0.08, -t - 1.15, -t, 2.84, 3.0, 'palTimber', GR(1), skip=('+y',))
    tube(f'strut{x}', (x, -t - 0.9, 2.86), (x, -t - 0.02, 2.0), 0.06, 4, 'palTimber', UV_ALONG((x, -t - 0.9, 2.86), (x, -t - 0.02, 2.0), 0.06))
ob = finish('wall_walk_seg'); check(ob, INST_BUDGET)
d, lo, hi = dims(ob); gate(abs(hi[2] - (WALL_H + 0.7)) < 1e-4, f'wall_walk_seg wall {WALL_H} m + merlons 0.7 m, walk at 3.0 m (1.0 m to the merlon tops: cover)')
export('wall_walk_seg', [ob])

# B8 corridor parapet (hollow brick on a stone sill, timber rail) and covered-walkway post and beam (instanced) ---------------------
box('sill', 0, SEG, -0.22, 0.22, 0, 0.15, 'palStone', W, skip=('-z', '-x', '+x'))
box('bricks', 0, SEG, -0.17, 0.17, 0.15, 0.95, 'palBrick', UV_WORLD(zoff=0.15 - M_UV), skip=('-z', '-x', '+x'))
box('rail', 0, SEG, -0.12, 0.12, 0.95, 1.07, 'palTimber', GR(0), skip=('-z', '-x', '+x'))
ob = finish('parapet_seg'); check(ob, INST_BUDGET); export('parapet_seg', [ob])
box('base', -0.25, 0.25, -0.25, 0.25, 0, 0.25, 'palStone', W, skip=('-z',))
cyl('post', 0, 0, 0.25, 3.2, 0.14, 0.13, 8, 'palLacquer', UV_CYL(0, 0, 0.25, 3.2, 2 * math.pi * 0.135 / M_UV, None))
box('arm', -0.6, 0.6, -0.1, 0.1, 3.0, 3.2, 'palTimber', GR(0))
cyl('band', 0, 0, 2.75, 3.0, 0.15, 0.15, 8, 'palBronze', UV_CYL(0, 0, 2.75, 3.0, 2 * math.pi * 0.15 / M_UV, (384, 448)), caps=(True, True))
ob = finish('walk_post'); check(ob, INST_BUDGET); export('walk_post', [ob])
box('beam', 0, SEG, -0.12, 0.12, 3.2, 3.5, 'palTimber', GR(0), skip=('-x', '+x'))
profile_x('walkroof', [(-1.2, 3.55), (0, 3.95), (1.2, 3.55)], 0, SEG, ['palRoof', 'palRoof'], W, side=-1)
ob = finish('walk_beam'); check(ob, INST_BUDGET); export('walk_beam', [ob])

# B9 timber trestle bridge bay (instanced per 4 m), 8 m and 12 m decks ------------------------------------------------------------
for BW in BRIDGE_W:
    h2 = BW / 2
    box('deck', 0, SEG, -h2, h2, -0.2, 0, 'palTimber', GR(1), skip=('-x', '+x'))
    for y in (-h2 + 0.6, 0, h2 - 0.6):
        box(f'str{y}', 0, SEG, y - 0.15, y + 0.15, -0.6, -0.2, 'palTimber', GR(0), skip=('-x', '+x', '+z'))
    box('cap', -0.2, 0.2, -h2 - 0.4, h2 + 0.4, -1.0, -0.6, 'palTimber', GR(1))
    posts = [-h2 + 0.8, -h2 / 3, h2 / 3, h2 - 0.8] if BW < 10 else [-h2 + 0.8, -h2 / 2.4, 0, h2 / 2.4, h2 - 0.8]
    for y in posts:
        tube(f'post{y}', (0, y, LAKE_Y - 0.6), (0, y, -1.0), 0.18, 7, 'palTimber', UV_ALONG((0, y, LAKE_Y - 0.6), (0, y, -1.0), 0.18), caps=False)
    for a, b in ((posts[0], posts[1]), (posts[-2], posts[-1])):  # X bracing in the outer bays
        tube(f'brA{a}', (0.12, a, LAKE_Y + 0.6), (0.12, b, -1.4), 0.07, 4, 'palTimber', UV_ALONG((0.12, a, LAKE_Y + 0.6), (0.12, b, -1.4), 0.07))
        tube(f'brB{a}', (0.12, b, LAKE_Y + 0.6), (0.12, a, -1.4), 0.07, 4, 'palTimber', UV_ALONG((0.12, b, LAKE_Y + 0.6), (0.12, a, -1.4), 0.07))
    for sy in (-1, 1):
        y = sy * (h2 - 0.12)
        box(f'rp{sy}', -0.08, 0.08, y - 0.08, y + 0.08, 0, LOW_H + 0.1, 'palTimber', GR(2), skip=('-z',))
        box(f'rail{sy}', 0, SEG, y - 0.06, y + 0.06, LOW_H - 0.05, LOW_H + 0.07, 'palTimber', GR(0), skip=('-x', '+x'))
        box(f'mid{sy}', 0, SEG, y - 0.04, y + 0.04, 0.38, 0.46, 'palTimber', GR(0), skip=('-x', '+x'))
    ob = finish(f'bridge_bay_{int(BW)}'); check(ob, INST_BUDGET)
    d, lo, hi = dims(ob); gate(abs(d[1] - (BW + 0.8)) < 0.01 and lo[2] <= LAKE_Y, f'bridge_bay_{int(BW)} deck {BW} m wide, posts from {lo[2]:.1f} m (into the lake), rails {LOW_H} m')
    export(f'bridge_bay_{int(BW)}', [ob])

# B10 throne and dais (single prop with LOD): three tiers (stone, lacquer with bronze edging, lacquer), the red 丹 top, couch, screen --
def throne(detail):
    z = 0.0
    for i, (w, d_, h) in enumerate(DAIS):
        yc = 0.4 * i  # tiers step back toward the north
        mat = 'palStone' if i == 0 else 'palLacquer'
        box(f'tier{i}', -w / 2, w / 2, yc - d_ / 2, yc + d_ / 2, z, z + h, mat, W if i == 0 else GR(0), skip=('-z', '+z'))
        box(f'top{i}', -w / 2, w / 2, yc - d_ / 2, yc + d_ / 2, z + h - 0.001, z + h, 'palFloor', W, skip=('-z', '-x', '+x', '-y', '+y'))
        if detail and i > 0:  # bronze edging strips on the tier's front and side arrises
            box(f'edge{i}', -w / 2 - 0.03, w / 2 + 0.03, yc - d_ / 2 - 0.03, yc - d_ / 2 + 0.06, z + h - 0.12, z + h, 'palBronze', UV_ROWS(448, 512))
            box(f'foot{i}', -w / 2 - 0.03, w / 2 + 0.03, yc - d_ / 2 - 0.03, yc - d_ / 2 + 0.06, z, z + 0.12, 'palBronze', UV_ROWS(448, 512))
        z += h
    top = z; yb = 0.8
    w, d_, _ = DAIS[-1]; yc = 0.8
    if detail:  # a low lacquer balustrade along the top tier's front, bronze-capped posts (reads as a platform from above)
        box('rail', -w / 2 + 0.2, w / 2 - 0.2, yc - d_ / 2 + 0.1, yc - d_ / 2 + 0.22, top + 0.5, top + 0.62, 'palLacquer', GR(0))
        for k in range(8):
            x = -w / 2 + 0.25 + k * (w - 0.5) / 7
            box(f'bp{k}', x - 0.07, x + 0.07, yc - d_ / 2 + 0.09, yc - d_ / 2 + 0.23, top, top + 0.7, 'palBronze', UV_ROWS(40, 344))
    box('couch', -1.6, 1.6, yb - 0.8, yb + 0.8, top, top + 0.42, 'palLacquer', GR(0), skip=('-z',))
    box('seat', -1.45, 1.45, yb - 0.65, yb + 0.65, top + 0.42, top + 0.47, 'palFloor', W, skip=('-z',))
    for sx in (-1, 1):
        box(f'arm{sx}', sx * 1.6 - (0.12 if sx > 0 else 0), sx * 1.6 + (0.12 if sx < 0 else 0), yb - 0.7, yb + 0.8, top + 0.45, top + 0.85, 'palLacquer', GR(1))
    box('back', -1.6, 1.6, yb + 0.68, yb + 0.8, top + 0.45, top + 0.95, 'palLacquer', GR(0))
    for k, x in enumerate((-1.5, -0.5, 0.5, 1.5)):  # screen 屏风: four lacquer panels framed in bronze, tall behind the couch
        box(f'scr{k}', x - 0.5, x + 0.5, yb + 1.0, yb + 1.1, top, top + 2.1, 'palPillar', UV_ROWS(140, 860))
        box(f'scb{k}', x - 0.5, x + 0.5, yb + 1.0, yb + 1.1, top + 2.1, top + 2.6, 'palPillar', UV_ROWS(0, 120))  # the vermilion cloud band
        if detail:
            box(f'sfr{k}', x - 0.52, x + 0.52, yb + 0.97, yb + 1.0, top + 2.5, top + 2.62, 'palBronze', UV_ROWS(576, 640))
    if detail:
        for sx in (-1, 1):  # bronze corner fittings on the couch
            for sy in (-1, 1):
                box(f'cf{sx}{sy}', sx * 1.6 - 0.1, sx * 1.6 + 0.1, yb + sy * 0.8 - 0.1, yb + sy * 0.8 + 0.1, top, top + 0.47, 'palBronze', UV_ROWS(40, 344))
lods = []
for li, detail in enumerate((True, False, False)):
    throne(detail); lods.append(finish(f'throne_dais_lod{li}'))
for o, b in zip(lods, SINGLE_BUDGET): check(o, b)
d, lo, hi = dims(lods[0]); gate(sum(h for _, _, h in DAIS) >= 2.0 and d[0] <= 12.2, f'throne_dais footprint {d[0]:.1f} x {d[1]:.1f} m, dais top {sum(h for _, _, h in DAIS):.1f} m (out of reach), screen top {hi[2]:.1f} m')
root = bpy.data.objects.new('throne_dais', None); bpy.context.collection.objects.link(root)
for o in lods: o.parent = root
export('throne_dais', [root])

# B11 lake edge rubble (instanced) and fallen-room debris (single prop, burnt materials, half sunk) --------------------------------
for i in range(7):
    rock(f'r{i}', (0.3 + i * 0.55, 2.4 + (i % 3) * 0.35, LAKE_Y - 0.1 + (i % 2) * 0.15), (0.45, 0.35, 0.3), 'palStone', UV_FACE(), 50 + i)
ob = finish('lake_rubble'); check(ob, INST_BUDGET); export('lake_rubble', [ob])
def debris(detail):
    import random
    rnd = random.Random(77)
    zs = LAKE_Y
    slab = box('slab', -2.5, 2.5, -2, 2, -0.6, 0.6, 'palFloor', W); bake_uv(slab)
    slab.rotation_euler = (math.radians(14), math.radians(-9), 0.3); slab.location = (0, 0, zs + 0.3)
    wall = box('wallchunk', -1.8, 1.8, -0.25, 0.25, -1.5, 2.2, 'palWall', UV_WORLD(zoff=-1.5)); bake_uv(wall)
    wall.rotation_euler = (math.radians(-28), 0, math.radians(20)); wall.location = (1.6, 1.4, zs)
    for k in range(3 if detail else 2):  # broken pillars, charred (burnt swap: palPillar -> timber_burnt)
        p = cyl(f'pil{k}', 0, 0, -1.4, 1.4 - k * 0.5, PIL_R, PIL_R, 12 if detail else 6, 'palPillar', UV_CYL(0, 0, -1.4, 2.15, 1.0), caps=(True, True)); bake_uv(p)
        p.rotation_euler = (math.radians(rnd.uniform(70, 95)), 0, math.radians(rnd.uniform(0, 180))); p.location = (rnd.uniform(-3, 3), rnd.uniform(-3, 3), zs + 0.2)
    for k in range(5 if detail else 2):  # beams
        L = rnd.uniform(2.5, 4.5)
        b = box(f'beam{k}', -L / 2, L / 2, -0.15, 0.15, -0.18, 0.18, 'palTimber', GR(0)); bake_uv(b)
        b.rotation_euler = (rnd.uniform(-0.4, 0.4), rnd.uniform(-0.5, 0.5), rnd.uniform(0, 3.1)); b.location = (rnd.uniform(-3.5, 3.5), rnd.uniform(-3, 3), zs + rnd.uniform(0.1, 0.9))
    if detail:
        for k in range(14):  # broken roof tiles
            tl = box(f'tile{k}', -0.2, 0.2, -0.17, 0.17, 0, 0.03, 'palRoof', W); bake_uv(tl)
            tl.rotation_euler = (rnd.uniform(-0.6, 0.6), rnd.uniform(-0.6, 0.6), rnd.uniform(0, 3)); tl.location = (rnd.uniform(-3, 3), rnd.uniform(-3, 3), zs + rnd.uniform(0.2, 1.1))
        for k in range(5):
            rock(f'rb{k}', (rnd.uniform(-3, 3), rnd.uniform(-3, 3), zs + 0.1), (0.5, 0.4, 0.35), 'palEarth', UV_FACE(), 90 + k)
    for ob, *_ in PARTS:  # bake the placement into the vertices (world UVs read world positions)
        ob.data.transform(ob.matrix_basis); ob.matrix_basis = Matrix.Identity(4)
lods = []
for li, detail in enumerate((True, False, False)):
    debris(detail); lods.append(finish(f'debris_lod{li}'))
for o, b in zip(lods, SINGLE_BUDGET): check(o, b)
d, lo, hi = dims(lods[0]); gate(lo[2] < LAKE_Y and hi[2] > LAKE_Y + 0.5, f'debris spans {lo[2]:.1f} to {hi[2]:.1f} m (lake {LAKE_Y}: half sunk)')
root = bpy.data.objects.new('debris', None); bpy.context.collection.objects.link(root)
for o in lods: o.parent = root
export('debris', [root])

# dressing: A20 slip rack and bundle, A19 flag, A16 plant cards (instanced) -----------------------------------------------------
for i, (x, y) in enumerate(((0, 0), (1.6, 0), (0, 0.5), (1.6, 0.5))):
    box(f'leg{i}', x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0, 1.8, 'palLacquer', GR(2), skip=('-z',))
for k in range(4):
    box(f'shelf{k}', -0.04, 1.64, -0.04, 0.54, 0.2 + k * 0.45, 0.24 + k * 0.45, 'palLacquer', GR(0))
ob = finish('slip_rack'); check(ob, INST_BUDGET); export('slip_rack', [ob])
L, R_ = 0.3, 0.05
def uv_roll(ob):  # side: slips run along the roll (columns), v along x inside rows 20-492 (cords included); ends: the bundle-end atlas disc
    me, uvl = _uv(ob)
    for p in me.polygons:
        ls = list(p.loop_indices)
        if abs(p.normal.x) > 0.9:
            for li in ls:
                c = me.vertices[me.loops[li].vertex_index].co
                uvl.data[li].uv = ((32 + c.y / M_UV * 1024) / 1024, 1 - (544 - c.z / M_UV * 1024) / 1024)
            continue
        vals = []
        for li in ls:
            c = me.vertices[me.loops[li].vertex_index].co; a = math.atan2(c.z, c.y) % math.tau
            vals.append([li, a * R_ / M_UV, 1 - (60 + c.x / M_UV * 1024) / 1024, a])
        if max(v[3] for v in vals) - min(v[3] for v in vals) > math.pi:
            for v in vals:
                if v[3] < math.pi: v[1] += math.tau * R_ / M_UV
        for li, u, vv, _ in vals: uvl.data[li].uv = (u, vv)
tube('roll', (0, 0, 0), (L, 0, 0), R_, 8, 'palSlips', uv_roll)
ob = finish('slip_bundle'); check(ob, 60); export('slip_bundle', [ob])
cyl('pole', 0, 0, 0, 4.0, 0.05, 0.04, 6, 'palTimber', UV_CYL(0, 0, 0, 4, 2 * math.pi * 0.045 / M_UV, None))
ob = finish('flag_pole'); check(ob, 60); export('flag_pole', [ob])
C3 = 1024 / 3
for i in range(9):
    pts = []
    xs = [0, 0.3, 0.6, 0.9, 1.17]
    bm = bmesh.new(); top = []; bot = []
    for k, x in enumerate(xs):  # a little wave in the cloth
        yw = 0.06 * math.sin(k * 1.4)
        top.append(bm.verts.new((x, yw, 0.78))); bot.append(bm.verts.new((x, yw, 0)))
    for k in range(len(xs) - 1): bm.faces.new([bot[k], bot[k + 1], top[k + 1], top[k]])
    new_obj(f'flag{i}', bm, 'palFlag', UV_CELL((i % 3) * C3 + 12, (i // 3) * C3 + 40, C3 - 30, C3 * 0.62))
    ob = finish(f'flag_{i}'); check(ob, 60); export(f'flag_{i}', [ob])
for row, kind in enumerate(('wheat', 'millet', 'shrub', 'grass')):
    for a in (0, math.pi / 2):  # crossed cards, 1 m
        ca, sa = math.cos(a) * 0.5, math.sin(a) * 0.5
        quad(f'{kind}{a}', [(-ca, -sa, 0), (ca, sa, 0), (ca, sa, 1), (-ca, -sa, 1)], 'palPlant', UV_CELL(0, row * 256, 256, 256, ax_u=0 if a == 0 else 1), two_sided=True)
    ob = finish(f'plant_{kind}'); check(ob, 60); export(f'plant_{kind}', [ob])

print(f'{len(RESULTS) - FAILS[0]} of {len(RESULTS)} pass')
json.dump(REPORT, open(os.path.join(OUT, 'arch_report.json'), 'w'), indent=1)
