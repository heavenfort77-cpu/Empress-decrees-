# 门海 bronze water vat, round 1 (asset list C3; study art/Qin-Bronze-Castings-Study.md "门海 water vat"). In the palace: break one to
# flood a spot: it cracks (tell CONFIG.PIECES2.vat.crackS = 0.5 s, the red ring), then splashes: douses the burning there and knocks back
# anyone in it (docs/BURNING-PALACE.md "Palace pieces"). Sized to the game's box vat (index.html: cylinder radius 0.8, height 1.4, solid
# 1.6 x 1.6 m, splash radius 3.5 m).
# Shape: a Warring States 鉴-style wide water basin (Qin first; reference only: ComfyUI round D concept 4207, run 45434186975, measured:
# rim about 1.5 x the height, tapering to about half the rim at the base, a low foot ring, raised horizontal bands). Our own design:
# lathe-turned tub (round), sharp rim lip and raised flange rings, stamp bands from the trim sheet (lozenge low, cloud scroll high),
# four 铺首 mask-and-ring handles, dark water inside.
#
# Output (one GLB, Y up): vat_body_lod0/1/2 (intact and cracked), vat_water (surface), vat_cracks (the crack tell: dark jagged cracks over
# the front and sides with water spurts), vat_shards_00.. (pooled pieces: each its own node so the game can throw them; laid out here as
# they land) and vat_puddle. Materials palBronze (trim sheet UVs), palDark, palWater, palSpray (light water spray). Usage: /home/claude/bpyenv/bin/python vat_blender.py OUT.glb
import bpy, bmesh, math, sys, os, random
from mathutils import Vector, Matrix

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/vat.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel on sharp parts, m (LOD0 only); hard edge angle on lathe parts, deg.
BEVEL = 0.012
SHARP_DEG = 50
# Trim sheet: metres per UV unit and rows in image pixels (art/tools/bronze_tex.py layout).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Lathe segments around (LOD0; LOD1 half).
SEG = 24
# Body profile (radius, height) m: outside from the foot up to the rim lip, then the inside down to the inner floor.
# Round 1 draft (straight taper from rim to foot) read as a flowerpot: now a bulging belly, a drawn-in neck and a flared lip (鉴 basin).
OUTER = [(0.0, 0.01), (0.5, 0.01), (0.52, 0.12), (0.48, 0.16), (0.62, 0.3), (0.75, 0.55), (0.78, 0.76), (0.73, 0.96), (0.75, 1.03), (0.8, 1.08)]
INNER = [(0.74, 1.1), (0.68, 0.96), (0.7, 0.7), (0.5, 0.3), (0.0, 0.22)]
# Stamp bands on the outside by height (z0, z1, row) and raised flange rings (z), m.
BANDS = [(0.28, 0.48, 'lozenge'), (0.82, 0.96, 'clouds'), (0.98, 1.12, 'flange')]
FLANGES = [0.5, 0.8]
# Water surface height, m (rim 1.14).
WATER_Z = 0.98
# Cracks: count, width m (>= 6 cm reads at the fight framing: 110 px/m x 0.06 = 6.6 px), angles they cover (deg, 90 = facing the camera).
CRACKS, CRACK_W = 5, 0.06
CRACK_ANGLES = (20, 160)
# Shards: count, landing ring radii m (inside the splash radius CONFIG.PIECES2.vat.radius 3.5).
SHARDS, SHARD_R = 10, (1.0, 2.2)
SPLASH_R = 3.5
# Triangle budgets per LOD (asset list C3: 1.5k / 500; LOD2 far); shards and the crack overlay share LOD0's budget each.
BUDGET = (1500, 500, 200)
SHARD_BUDGET = 1500
CRACK_BUDGET = 600
# Game fit: box vat solid 1.6 x 1.6 m.
FOOT = 1.6
LOD2_RATIO = 0.4
SEED = 1205

PARTS = []
Q = {'seg': 1.0}

def P(x, f, z): return Vector((x, -f, z))

def put(name, bm, mat, row, rnd):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, mat, row, rnd)); return ob

def radius_at(z, prof=OUTER):
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if min(z0, z1) <= z <= max(z0, z1) and r0 > 0 and r1 > 0: return r0 + (r1 - r0) * (z - z0) / ((z1 - z0) or 1e-6)
    return prof[-1][0]

def lathe(name, prof, mat, row, dr=0.0):
    M = max(10, round(SEG * Q['seg'])); bm = bmesh.new(); rings = []
    for rr, z in prof:
        if rr <= 1e-6: rings.append([bm.verts.new(P(0, 0, z))] * M)
        else: rings.append([bm.verts.new(P(math.cos(i * math.tau / M) * (rr + dr), math.sin(i * math.tau / M) * (rr + dr), z)) for i in range(M)])
    for a, b in zip(rings, rings[1:]):
        for i in range(M):
            vs = [a[i], a[(i + 1) % M], b[(i + 1) % M], b[i]]; vs = [v for k, v in enumerate(vs) if v not in vs[:k]]
            if len(vs) >= 3: bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, row, True)

def spheroid(name, c, r, mat, row='plain', segs=(10, 6)):
    u = max(6, round(segs[0] * Q['seg'])); v = max(4, round(segs[1] * Q['seg']))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    for vv in bm.verts: vv.co = P(c[0] + vv.co.x * r[0], c[1] - vv.co.y * r[1], c[2] + vv.co.z * r[2])
    return put(name, bm, mat, row, True)

def torus(name, c, axis, R, r, mat, row='flange', segs=(12, 6)):
    """a cast ring (handle ring) around 'axis' (design coords) centred at c."""
    n1, n2 = max(8, round(segs[0] * Q['seg'])), max(4, round(segs[1] * Q['seg']))
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
    a, b = P(*a), P(*b); d = (b - a).normalized()
    upv = Vector(up) if up else (Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0)))
    u = d.cross(upv).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + u * p[0] + v * p[1]) for p in prof]; r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    for i in range(len(prof)): bm.faces.new([r0[i], r0[(i + 1) % len(prof)], r1[(i + 1) % len(prof)], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, row, rnd)

def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]

def disc(name, r, z, mat, n=24):
    n = max(10, round(n * Q['seg'])); bm = bmesh.new()
    f = bm.faces.new([bm.verts.new(P(math.cos(i * math.tau / n) * r, math.sin(i * math.tau / n) * r, z)) for i in range(n)])
    f.normal_update()
    if f.normal.z < 0: f.normal_flip()  # water faces up (the round 1 draft's disc faced down and was culled from above)
    return put(name, bm, mat, 'plain', True)

def build_body(detail):
    PARTS.clear()
    lathe('body', OUTER + INNER, 'palBronze', BANDS)
    for z in FLANGES:  # raised flange rings: sharp lips dividing the stamp bands (segmented casting)
        r0 = radius_at(z - 0.03); r1 = radius_at(z + 0.03)
        lip = [(radius_at(z) + 0.025, z - 0.01), (radius_at(z) + 0.025, z + 0.01)] if detail else [(radius_at(z) + 0.025, z)]
        lathe(f'fl_{z}', [(r0, z - 0.03)] + lip + [(r1, z + 0.03)], 'palBronze', 'flange')
    for k in range(4):  # 铺首 mask-and-ring handles at 45 deg off the camera axis (two face the player)
        a = math.radians(45 + 90 * k); cx, cf = math.cos(a), math.sin(a)
        rm = radius_at(0.66)
        if detail:
            spheroid(f'mask_{k}', (cx * (rm + 0.0), cf * (rm + 0.0), 0.66), (0.11, 0.11, 0.09), 'palBronze', 'mask', segs=(8, 5))
            torus(f'ring_{k}', (cx * (rm + 0.04), cf * (rm + 0.04), 0.54), (cx, cf, 0), 0.085, 0.02, 'palBronze', 'flange', segs=(10, 4))

def build_water():
    PARTS.clear(); disc('water', radius_at(WATER_Z, INNER) - 0.005, WATER_Z, 'palWater', 28); return finish('vat_water', False)

def build_cracks():
    """the crack tell: jagged dark cracks (CRACK_W wide) set just proud of the outside, from the rim down, over the camera side, and short
    water spurts where they open."""
    PARTS.clear(); rnd = random.Random(SEED)
    for k in range(CRACKS):
        a = math.radians(CRACK_ANGLES[0] + (CRACK_ANGLES[1] - CRACK_ANGLES[0]) * k / (CRACKS - 1)); z = 1.1; pts = []
        while z > 0.28:
            rr = radius_at(z) + 0.012; pts.append((math.cos(a) * rr, math.sin(a) * rr, z))
            z -= rnd.uniform(0.12, 0.2); a += math.radians(rnd.uniform(-9, 9))
        for j in range(len(pts) - 1):
            out = (pts[j][0], pts[j][1], 0)
            prism(f'crack_{k}{j}', [(-CRACK_W / 2, 0), (CRACK_W / 2, 0), (0, 0.012)], pts[j], pts[j + 1], 'palDark', 'plain', rnd='flat', up=(out[0], -out[1], 0))
        mid = pts[len(pts) // 2]; d = Vector((mid[0], mid[1], 0)).normalized()
        # water spray fanning out of the crack (widens and droops; the draft's narrow blue cones read as thorns)
        prism(f'spurt_{k}', [(math.cos(i * math.tau / 6) * 0.03, math.sin(i * math.tau / 6) * 0.012) for i in range(6)], mid,
              (mid[0] + d.x * 0.3, mid[1] + d.y * 0.3, mid[2] - 0.16), 'palSpray', 'plain', scale_b=3.0, rnd=True)
    return finish('vat_cracks', False)

def shard_patch(name, a0, a1, z0, z1, th=0.035, na=4, nz=3):
    """a curved piece of the vat wall (outside on the profile, inside th thinner), built in place."""
    bm = bmesh.new(); outer = []; inner = []
    for i in range(nz):
        z = z0 + (z1 - z0) * i / (nz - 1); ro = radius_at(z); row_o = []; row_i = []
        for j in range(na):
            a = a0 + (a1 - a0) * j / (na - 1)
            row_o.append(bm.verts.new(P(math.cos(a) * ro, math.sin(a) * ro, z))); row_i.append(bm.verts.new(P(math.cos(a) * (ro - th), math.sin(a) * (ro - th), z)))
        outer.append(row_o); inner.append(row_i)
    for i in range(nz - 1):
        for j in range(na - 1):
            bm.faces.new([outer[i][j], outer[i][j + 1], outer[i + 1][j + 1], outer[i + 1][j]])
            bm.faces.new([inner[i][j], inner[i + 1][j], inner[i + 1][j + 1], inner[i][j + 1]])
    edge = [(0, j) for j in range(na)] + [(i, na - 1) for i in range(1, nz)] + [(nz - 1, j) for j in range(na - 2, -1, -1)] + [(i, 0) for i in range(nz - 2, 0, -1)]
    for (i0, j0), (i1, j1) in zip(edge, edge[1:] + edge[:1]): bm.faces.new([outer[i0][j0], inner[i0][j0], inner[i1][j1], outer[i1][j1]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, 'palBronze', BANDS, True)

def build_shards():
    """SHARDS wall pieces plus the foot ring, each its own object (pooled in the game), laid out as they land."""
    rnd = random.Random(SEED + 1); objs = []
    zs = [(0.2, 0.62), (0.62, 1.12)]
    for k in range(SHARDS):
        PARTS.clear()
        a0 = math.radians(k * 360 / (SHARDS / 2)); z0, z1 = zs[k % 2]
        ob = shard_patch(f's{k}', a0, a0 + math.radians(360 / (SHARDS / 2)) * 0.9, z0, z1)
        o = finish(f'vat_shards_{k:02d}', False)
        # move the piece from its place on the wall to where it lands: centred, tipped over outward, out on the ring, on the floor
        me = o.data; cen = sum((v.co for v in me.vertices), Vector()) / len(me.vertices)
        ang = math.atan2(cen.y, cen.x) + rnd.uniform(-0.3, 0.3); land = rnd.uniform(*SHARD_R)
        tip = Matrix.Rotation(rnd.uniform(1.2, 1.5), 4, Vector((-math.sin(ang), math.cos(ang), 0)))
        spin = Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, 'Z')
        me.transform(spin @ tip @ Matrix.Translation(-cen))
        zmin = min(v.co.z for v in me.vertices)
        me.transform(Matrix.Translation(Vector((math.cos(ang) * land, math.sin(ang) * land, -zmin))))
        objs.append(o)
    PARTS.clear()
    lathe('base', [(0.0, 0.01), (0.5, 0.01), (0.53, 0.12), (0.49, 0.15), (0.52, 0.2), (0.45, 0.22), (0.0, 0.22)], 'palBronze', 'plain')
    objs.append(finish('vat_shards_base', False))
    PARTS.clear(); disc('puddle', 1.2, 0.015, 'palWater', 28); puddle = finish('vat_puddle', False)
    return objs, puddle

def uv_trim(ob, row):
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        cz = sum(me.vertices[v].co.z for v in poly.vertices) / len(poly.vertices)
        rw = row
        if isinstance(row, list): rw = next((r for z0, z1, r in row if z0 <= cz <= z1), 'plain')
        y0, y1 = ROWS.get(rw, ROWS['plain']); h_img = (y1 - y0) / 1024.0
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        if ax != 2:  # sides of turned parts: u = arc length around, v = height (bands wrap the vessel)
            angs = [math.atan2(c.y, c.x) for c in cs]; ref = angs[0]
            angs = [a + math.tau if a - ref < -math.pi else a - math.tau if a - ref > math.pi else a for a in angs]
            vmin = min(c.z for c in cs); span = max(max(c.z for c in cs) - vmin, 1e-6) / M_PER_UV; k = min(1.0, h_img / span)
            rr = max(math.hypot(c.x, c.y) for c in cs)
            for li, c, a in zip(poly.loop_indices, cs, angs): uvl.data[li].uv = (a * rr / M_PER_UV, 1.0 - (y0 / 1024.0 + (c.z - vmin) / M_PER_UV * k))
            continue
        ua, va = 0, 1
        vmin = min(c[va] for c in cs); span = max(max(c[va] for c in cs) - vmin, 1e-6) / M_PER_UV; k = min(1.0, h_img / span)
        for li, c in zip(poly.loop_indices, cs): uvl.data[li].uv = (c[ua] / M_PER_UV, 1.0 - (y0 / 1024.0 + (c[va] - vmin) / M_PER_UV * k))

def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

def finish(name, bevel):
    for ob, mat, row, rnd in PARTS:
        uv_trim(ob, row); ob.data.materials.append(material(mat))
        bm = bmesh.new(); bm.from_mesh(ob.data)
        if bevel and rnd is False: bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
        for f in bm.faces: f.smooth = rnd is True
        if rnd is True:
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
        bm.to_mesh(ob.data); bm.free()
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0][0]
    if len(PARTS) > 1: bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

bpy.ops.wm.read_factory_settings(use_empty=True)
Q['seg'] = 0.5; build_body(False); lod1 = finish('vat_body_lod1', False)
build_body(False); lod2 = finish('vat_body_lod2', False)
dm = lod2.modifiers.new('dec', 'DECIMATE'); dm.ratio = LOD2_RATIO
bpy.context.view_layer.objects.active = lod2; bpy.ops.object.modifier_apply(modifier='dec')
Q['seg'] = 1.0; build_body(True); lod0 = finish('vat_body_lod0', True)
water = build_water(); cracks = build_cracks(); shards, puddle = build_shards()

fails = 0; n_checks = 0
def gate(ok, line):
    global fails, n_checks
    n_checks += 1; fails += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + line)
for ob, lim in zip((lod0, lod1, lod2), BUDGET): gate(tris(ob) <= lim, f'{ob.name} tris {tris(ob)} (budget {lim})')
st = sum(tris(o) for o in shards)
gate(st <= SHARD_BUDGET, f'shards {len(shards)} pieces, {st} tris together (budget {SHARD_BUDGET})')
gate(tris(cracks) <= CRACK_BUDGET, f'cracks overlay {tris(cracks)} tris (budget {CRACK_BUDGET})')
bb = [lod0.matrix_world @ Vector(c) for c in lod0.bound_box]
w, d, h = max(c.x for c in bb) - min(c.x for c in bb), max(c.y for c in bb) - min(c.y for c in bb), max(c.z for c in bb)
gate(w <= FOOT + 1e-6 and d <= FOOT + 1e-6, f'footprint {w:.2f} x {d:.2f} m, height {h:.2f} m (solid {FOOT} x {FOOT}; box vat 1.4 m)')
gate(CRACK_W >= 0.06 and CRACKS >= 3, f'crack tell: {CRACKS} cracks {CRACK_W * 100:.0f} cm wide over {CRACK_ANGLES[0]}-{CRACK_ANGLES[1]} deg (camera side), spurts present')
far = max(max(math.hypot(v.co.x, v.co.y) for v in o.data.vertices) for o in shards)
low = all(min(v.co.z for v in o.data.vertices) >= -1e-4 for o in shards)
gate(len(shards) >= 8 and far <= SPLASH_R and low, f'{len(shards)} shard nodes (pooled), all within {far:.2f} m of the centre (splash {SPLASH_R}) and on or above the floor: {low}')
up = all(p.normal.z > 0.99 for o in (water, puddle) for p in o.data.polygons)
gate(WATER_Z < max(z for r, z in INNER) and tris(water) > 0 and up, f'water surface at {WATER_Z} m under the rim {max(z for r, z in INNER):.2f} m; water and puddle face up: {up}')
share = sum(1 for p in lod0.data.polygons if p.use_smooth) / len(lod0.data.polygons)
gate(share >= 0.5, f'smooth-shaded share {share:.0%} (turned vessel, min 50%)')
print(f'{n_checks - fails} of {n_checks} pass')
lod1.location.x = 3; lod2.location.x = 6
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_materials='EXPORT', export_image_format='NONE', export_extras=True)
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
