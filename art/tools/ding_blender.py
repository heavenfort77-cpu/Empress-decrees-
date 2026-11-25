# 鼎 cauldron, round 1 (asset list C2; study art/Qin-Bronze-Castings-Study.md "鼎 cauldron"). Nine in the palace, one per school hall
# (the 九鼎), replacing the healing altars (docs/BURNING-PALACE.md "Palace pieces"); a lit state and a dry state (GDD decree "Our altars
# are dry": dry altars look empty).
# Shape: a Warring States ding without its lid (reference only: ComfyUI round D concept 4101, run 45434186975, measured: belly widest
# about 0.9 of the height at 0.40 of it, legs the lowest 0.28; real Warring States ding are wide, round-bellied, on three hoof legs with
# two upright handles attached outside the rim). Our own design: lathe-turned belly (round), sharp rim lip, six vertical flanges and a
# deconstructed taotie band from the trim sheet's mask row (sharp), a 6 cm school-accent inlay band, hoof legs with mask knees.
# Sized to the game's box ding (index.html: body radius 0.85, rim 1.36 m, solid 1.8 x 1.8 m).
#
# Output (one GLB, Y up): ding_lod0 / ding_lod1 / ding_lod2 static (shared by all nine halls), ding_lit (ember bed, ember lumps, glow cards)
# and ding_dry (ash crust with cracks), placed inside LOD0's bowl. Materials: palBronze (trim sheet UVs at 256 px/m), palAccent (the hall's
# school colour: one material per hall, colours in the GLB extras 'accents', CONFIG.SCHOOLS order), palDark, palEmber, palGlow (additive
# card, no light), palAsh. Usage: /home/claude/bpyenv/bin/python ding_blender.py OUT.glb
import bpy, bmesh, math, sys, os
from mathutils import Vector

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/ding.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel width on sharp parts, m (LOD0 only).
BEVEL = 0.015
# Faces meeting at more than this angle keep a hard edge on lathe parts, deg.
SHARP_DEG = 50
# Trim sheet: metres per UV unit and rows in image pixels (art/tools/bronze_tex.py layout).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Lathe segments around (LOD0; LOD1 uses half).
SEG = 28
# Body profile (radius, height) m, outside from the bottom centre up to the rim, then the inside wall down to the inner floor.
OUTER = [(0.0, 0.4), (0.4, 0.42), (0.66, 0.56), (0.75, 0.8), (0.7, 1.04), (0.62, 1.18), (0.64, 1.22), (0.67, 1.26)]
INNER = [(0.6, 1.27), (0.58, 1.2), (0.61, 0.95), (0.42, 0.66), (0.0, 0.6)]
# Ornament bands on the outside (z0, z1, row): cloud band low on the belly, taotie mask band at the shoulder, flange row on the rim.
BANDS = [(0.56, 0.68, 'clouds'), (0.98, 1.12, 'mask'), (1.17, 1.3, 'flange')]
# School-accent inlay band (z0, z1), m: 6 cm, under the mask band.
ACCENT_Z = (0.9, 0.96)
# Ember bed height (lit) and ash crust height (dry), m; the dry bowl reads deeper and empty.
EMBER_Z, ASH_Z = 1.0, 0.78
# School accents in CONFIG.SCHOOLS order (ru dao fa mo yinyang za ming zongheng nong): the research palette (docs/research/
# Qin-palace-medieval-tech-fusion.md "School accents") assigned to the game's school colours (CONFIG.COL.schools) by least total Lab
# distance (W1a, 25 Nov; total 236): ochre, gold, lead white, cinnabar, bone black, silver, Han purple, malachite, azurite.
ACCENTS = ['#b8862e', '#e2b84a', '#d9d2c3', '#a8321e', '#1a1614', '#c8ccd0', '#5b3f8c', '#2f8a5c', '#2e5a9c']
# Accent material per hall: metal inlays (gold, silver) shine, pigment inlays are matte (round 1 draft measured lead white vs silver at
# dE 6.9 on screen when all nine shared one finish). Metalness per accent, same order; roughness 0.35 metal, 0.85 pigment. Gold is laid
# matte: as metal (0.6) it measured dE 7.3 from the brass bronze under the game lights (no environment map, metal reads dark).
ACCENT_METAL = [0, 0, 0, 0, 0, 0.6, 0, 0, 0]
# Triangle budgets per LOD (asset list C2: 2k / 600; LOD2 far).
BUDGET = (2000, 600, 250)
# Game fit: box ding solid 1.8 x 1.8 m (index.html palSolid), rim height range m; ember bed visible from the play camera pitch (deg) >= 50%.
FOOT = 1.8
RIM_RANGE = (1.1, 1.45)
PITCH = 40
LOD2_RATIO = 0.35

PARTS = []  # (object, material, rowmap or row, shade) shade True smooth, False sharp bevelled, 'flat' sharp no bevel
Q = {'seg': 1.0}

def P(x, f, z): return Vector((x, -f, z))

def put(name, bm, mat, row, rnd):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, mat, row, rnd)); return ob

def lathe(name, prof, mat, row, close_axis=True, dr=0.0):
    """turn a (radius, height) profile around the vertical axis; points at radius 0 become one pole. dr pushes the whole profile out."""
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

def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]

def quad(name, corners, mat):
    bm = bmesh.new(); bm.faces.new([bm.verts.new(P(*c)) for c in corners]); return put(name, bm, mat, 'card', 'flat')

def radius_at(z):
    for (r0, z0), (r1, z1) in zip(OUTER, OUTER[1:]):
        if z0 <= z <= z1: return r0 + (r1 - r0) * (z - z0) / max(z1 - z0, 1e-6)
    return OUTER[-1][0]

def build(detail):
    PARTS.clear()
    rowmap = [(z0, z1, row) for z0, z1, row in BANDS]
    lathe('body', OUTER + INNER, 'palBronze', rowmap)
    # school accent: a 6 cm inlay band set just proud of the belly
    z0, z1 = ACCENT_Z
    lathe('accent', [(radius_at(z0), z0), (radius_at((z0 + z1) / 2), (z0 + z1) / 2), (radius_at(z1), z1)], 'palAccent', 'plain', dr=0.008)
    if detail:  # dark keylines (1.5 cm) above and below the accent band, so ochre and gold still part from the bronze
        for zk in (z0 - 0.015, z1):
            lathe(f'key_{zk}', [(radius_at(zk), zk), (radius_at(zk + 0.015), zk + 0.015)], 'palDark', 'plain', dr=0.01)
    # six vertical flanges (扉棱) across the mask band and the accent band: sharp blades, the mask band reads as three taotie faces
    if detail:
        for k in range(6):
            a = math.radians(k * 60 + 30)
            for zz0, zz1 in ((0.86, 1.16),):
                rr = radius_at((zz0 + zz1) / 2)
                c0 = (math.cos(a) * (rr + 0.01), math.sin(a) * (rr + 0.01), zz0); c1 = (math.cos(a) * (rr + 0.01), math.sin(a) * (rr + 0.01), zz1)
                prism(f'flange_{k}', [(-0.03, 0.0), (0.03, 0.0), (0.016, 0.09), (-0.016, 0.09)], c0, c1, 'palBronze', 'flange', up=(math.cos(a), -math.sin(a), 0))
    # two upright handles (附耳) attached outside the rim on the x axis, flaring out: rounded-square posts and a top bar (sharp, bevelled)
    for s in (-1, 1):
        x0, x1 = s * 0.66, s * 0.76
        for fz in (-0.17, 0.17):
            prism(f'post_{s}{fz}', rect(0.11, 0.08), (x0, fz, 1.08), (x1, fz * 1.05, 1.58), 'palBronze', 'flange')
        prism(f'bar_{s}', rect(0.11, 0.1), (x1, -0.23, 1.58), (x1, 0.23, 1.58), 'palBronze', 'lozenge')
        if detail: prism(f'barinlay_{s}', rect(0.084, 0.03), (x1, -0.18, 1.6), (x1, 0.18, 1.6), 'palAccent', 'plain')
    # three hoof legs (蹄足): mask knee bulge where the leg meets the belly, tapered round leg, flared hoof
    for k in range(3):
        a = math.radians(90 + k * 120)
        kx, kf = math.cos(a), math.sin(a)
        knee = (kx * 0.5, kf * 0.5, 0.46); foot = (kx * 0.6, kf * 0.6, 0.06)
        if detail: spheroid(f'knee_{k}', knee, (0.15, 0.15, 0.13), 'palBronze', 'mask', segs=(10, 6))
        prism(f'leg_{k}', ngon(0.09, max(6, round(10 * Q['seg']))), knee, (foot[0], foot[1], 0.1), 'palBronze', 'plain', scale_b=0.72, rnd=True)
        prism(f'hoof_{k}', ngon(0.075, max(6, round(10 * Q['seg']))), (foot[0], foot[1], 0.12), (foot[0] * 1.03, foot[1] * 1.03, 0.0), 'palBronze', 'flange', scale_b=1.45, rnd=True)

def build_states():
    """lit and dry contents, LOD0 detail; joined per state."""
    PARTS.clear()
    rb = radius_at(EMBER_Z) - 0.12
    lathe('coal', [(rb, EMBER_Z - 0.03), (rb * 0.8, EMBER_Z + 0.03), (0.0, EMBER_Z + 0.06)], 'palCoal', 'plain')
    for k in range(16):  # coals: dark lumps, every third one glowing; golden-angle spread, sizes varied (round 1 draft: 9 even hexagons read as stickers)
        a = k * 2.39996; rr = 0.08 + 0.42 * math.sqrt((k + 0.5) / 16); sz = 0.05 + 0.03 * ((k * 0.618) % 1.0)
        spheroid(f'ember_{k}', (math.cos(a) * rr, math.sin(a) * rr, EMBER_Z + 0.045), (sz, sz * 0.8, sz * 0.55), 'palEmber' if k % 3 == 0 else 'palCoal', segs=(6, 4))
    quad('glow_disc', [(-0.55, -0.55, EMBER_Z + 0.08), (0.55, -0.55, EMBER_Z + 0.08), (0.55, 0.55, EMBER_Z + 0.08), (-0.55, 0.55, EMBER_Z + 0.08)], 'palGlow')
    for k in range(2):  # two crossed vertical glow cards rising out of the bowl (warmth above the rim, no light)
        a = math.radians(45 + 90 * k); c, s = math.cos(a) * 0.5, math.sin(a) * 0.5
        quad(f'glow_card_{k}', [(-c, -s, EMBER_Z), (c, s, EMBER_Z), (c, s, EMBER_Z + 0.7), (-c, -s, EMBER_Z + 0.7)], 'palGlow')
    lit = finish('ding_lit', False)
    PARTS.clear()
    ra = radius_at(ASH_Z) - 0.17
    lathe('ash', [(ra, ASH_Z - 0.02), (ra * 0.7, ASH_Z + 0.015), (0.0, ASH_Z + 0.02)], 'palAsh', 'plain')
    for k in range(7):  # dry cracks in the crust: short jagged runs of three pieces (round 1 draft: straight radial lines read as a pie)
        a = math.radians(k * 51 + 10); r0 = 0.1 + 0.25 * ((k * 0.43) % 1.0); pts = []
        for j in range(4):
            aa = a + (0.18 if j % 2 else -0.08) * (j > 0); rr = min(ra * 0.92, r0 + j * 0.1); pts.append((math.cos(aa) * rr, math.sin(aa) * rr, ASH_Z + 0.02))
        for j in range(3): prism(f'crack_{k}{j}', rect(0.022, 0.01), pts[j], pts[j + 1], 'palDark', 'plain', rnd='flat')
    dry = finish('ding_dry', False)
    return lit, dry

def uv_trim(ob, row):
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    if row == 'card':  # glow cards: the whole 0-1 square (the radial glow texture), corners in build order
        for poly in me.polygons:
            for li, uv in zip(poly.loop_indices, ((0, 0), (1, 0), (1, 1), (0, 1))): uvl.data[li].uv = uv
        return
    for poly in me.polygons:
        cz = sum(me.vertices[v].co.z for v in poly.vertices) / len(poly.vertices)
        rw = row
        if isinstance(row, list): rw = next((r for z0, z1, r in row if z0 <= cz <= z1), 'plain')
        y0, y1 = ROWS.get(rw, ROWS['plain']); h_img = (y1 - y0) / 1024.0
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        if ax != 2 and isinstance(row, list):  # lathe sides: u = arc length around, v = height (bands wrap the vessel)
            cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
            angs = [math.atan2(c.y, c.x) for c in cs]; ref = angs[0]
            angs = [a + math.tau if a - ref < -math.pi else a - math.tau if a - ref > math.pi else a for a in angs]
            vmin = min(c.z for c in cs); span = max(max(c.z for c in cs) - vmin, 1e-6) / M_PER_UV; k = min(1.0, h_img / span)
            rr = max(math.hypot(c.x, c.y) for c in cs)
            for li, c, a in zip(poly.loop_indices, cs, angs):
                uvl.data[li].uv = (a * rr / M_PER_UV, 1.0 - (y0 / 1024.0 + (c.z - vmin) / M_PER_UV * k))
            continue
        ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        cs = [me.vertices[me.loops[li].vertex_index].co for li in poly.loop_indices]
        vmin = min(c[va] for c in cs); span = max(max(c[va] for c in cs) - vmin, 1e-6) / M_PER_UV; k = min(1.0, h_img / span)
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co
            uvl.data[li].uv = (c[ua] / M_PER_UV, 1.0 - (y0 / 1024.0 + (c[va] - vmin) / M_PER_UV * k))

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
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

bpy.ops.wm.read_factory_settings(use_empty=True)
Q['seg'] = 0.5; build(False); lod1 = finish('ding_lod1', False)
build(False); lod2 = finish('ding_lod2', False)
dm = lod2.modifiers.new('dec', 'DECIMATE'); dm.ratio = LOD2_RATIO
bpy.context.view_layer.objects.active = lod2; bpy.ops.object.modifier_apply(modifier='dec')
Q['seg'] = 1.0; build(True); lod0 = finish('ding_lod0', True)
lit, dry = build_states()
lod0['accents'] = ACCENTS  # glTF extras: the nine hall colours and their metalness
lod0['accentMetal'] = ACCENT_METAL

fails = 0; n_checks = 0
def gate(ok, line):
    global fails, n_checks
    n_checks += 1; fails += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + line)
for ob, lim in zip((lod0, lod1, lod2), BUDGET): gate(tris(ob) <= lim, f'{ob.name} tris {tris(ob)} (budget {lim})')
print(f'state tris: lit {tris(lit)}, dry {tris(dry)}')
bb = [lod0.matrix_world @ Vector(c) for c in lod0.bound_box]
w, d, h = max(c.x for c in bb) - min(c.x for c in bb), max(c.y for c in bb) - min(c.y for c in bb), max(c.z for c in bb)
gate(w <= FOOT + 1e-6 and d <= FOOT + 1e-6, f'footprint {w:.2f} x {d:.2f} m (solid {FOOT} x {FOOT})')
rim = max(z for r, z in OUTER + INNER)
gate(RIM_RANGE[0] <= rim <= RIM_RANGE[1], f'rim height {rim:.2f} m (box ding 1.36; range {RIM_RANGE}); handles to {h:.2f} m')
def visible(zc):  # share of the bowl contents' diameter seen over the near rim from the play pitch
    rin = radius_at(rim) - 0.03; need = (rim - zc) / math.tan(math.radians(PITCH)); return max(0.0, (2 * rin - need) / (2 * rin))
gate(visible(EMBER_Z) >= 0.5, f'lit ember bed seen over the rim from {PITCH} deg: {visible(EMBER_Z):.0%} of its width (min 50%)')
gate(EMBER_Z - ASH_Z >= 0.15, f'dry crust {EMBER_Z - ASH_Z:.2f} m below the lit bed (empty look; min 0.15); seen {visible(ASH_Z):.0%}')
mats = lambda ob: {m.name for m in ob.data.materials}
gate('palAccent' in mats(lod0) and 'palAccent' in mats(lod1), 'school accent material on LOD0 and LOD1 (one shared mesh, colour per hall)')
gate(len(set(ACCENTS)) == 9, f'nine distinct accent colours in the GLB extras ({len(set(ACCENTS))})')
gate('palGlow' in mats(lit) and 'palEmber' in mats(lit) and 'palGlow' not in mats(dry), 'lit state glows (ember + glow cards, no light); dry state has no glow')
share = sum(1 for p in lod0.data.polygons if p.use_smooth) / len(lod0.data.polygons)
gate(share >= 0.5, f'smooth-shaded share {share:.0%} (round vessel, min 50%)')
print(f'{n_checks - fails} of {n_checks} pass')
lod1.location.x = 3; lod2.location.x = 6
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_materials='EXPORT', export_image_format='NONE', export_extras=True)
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
