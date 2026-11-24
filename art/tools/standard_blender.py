# School emblem standard, round 1 (asset list C12; GDD G1: each school hall must read as that school's). One standard per school hall,
# nine schools, ONE shared mesh: the schools differ only by the banner's UV offset on one atlas (assets/tex/school_standards.png, painted
# in klad by art/tools/standard_tex.py; cell i = CONFIG.SCHOOLS[i], u offset (i % 5) * 0.2, v offset (i // 5) * 0.5, glTF v down).
# Build: a black-lacquer pole in a cast bronze foot, bronze collars, a lacquer crossbar with bronze end points and a bronze leaf finial;
# the banner is one alpha-tested cloth card (glTF alphaMode MASK, cutoff 0.5, double sided) hung in front of the pole from the crossbar.
# Rig: pole bone (everything rigid, 100% weight) and three chained cloth bones; clip 'idle' = gentle sway, 2.0 s loop (sideways swing
# with a lag down the cloth, and a small forward billow that never swings the cloth back into the pole).
# Output: standard_rig + standard_lod0 (skinned), standard_lod1 and standard_lod2 (static, flat card) in one GLB.
# Usage: /path/python-with-bpy standard_blender.py OUT.glb     (STD_MUT=tris|weights|rigid|height|loop|texel|fps breaks one gate on purpose)
import sys, os, math, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy, bmesh
from mathutils import Vector, Quaternion
import prop_kit as K
from prop_kit import P, lathe, sweep

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/standard.glb'
MUT = os.environ.get('STD_MUT', '')

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets: LOD0 rigid parts (asset list C12: 300 + cloth card), the LOD0 cloth card, LOD1 and LOD2 totals (card included).
BUDGET = (300, 130, 45)
CARD_MAX = 48
# Height range for a hall standard, m; the hall wall is 4 m (index.html CONFIG.PALACE.wallH 4, doorH 3.5): the finial stays under the wall top.
HEIGHT = (3.0, 4.0)
WALL_H = 4.0
# Footprint limits across (x) and front-back (f), m.
FOOT_X, FOOT_F = 1.2, 0.6
# Pole radius and top, m; crossbar height, forward offset from the pole axis, half length and radius, m.
POLE_R, POLE_TOP = 0.035, 3.41
BAR_Z, BAR_F, BAR_HALF, BAR_R = 3.30, 0.07, 0.46, 0.026
# Banner card: width, top and bottom z, forward offset (in front of the pole), m; card rows z (cloth bends here) and columns.
BANNER_W, BANNER_TOP, BANNER_BOT, BANNER_F = 0.8, 3.30, 1.30, 0.075
ROWS_Z = [3.30, 2.975, 2.65, 2.30, 1.95, 1.625, 1.30]
COLS = 2
# Atlas: size px, cell size in UV (one school per cell), target texel density px/m (art rule 256 px/m) and tolerance.
ATLAS, CELL_UV, TEXEL, TEXEL_TOL = 1024, (0.2, 0.5), 256, 0.05
# School order (index.html CONFIG.SCHOOLS) = atlas cell order.
SCHOOLS = ['ru', 'dao', 'fa', 'mo', 'yinyang', 'za', 'ming', 'zongheng', 'nong']
# Cloth bone heads and the last tail, z (three cloth bones, chained under the pole bone).
CLOTH_Z = [3.30, 2.65, 1.95, 1.30]
# Sway per cloth bone (the top bone swings least: its edge is tied to the crossbar): (sideways swing deg, forward billow base deg, billow swing deg, phase lag rad); loop length s, fps, keys per loop.
SWAY = [(0.8, 1.0, 1.0, 0.0), (2.5, 1.2, 1.2, 0.6), (3.5, 1.5, 1.5, 1.2)]
LOOP, FPS, KEYS = 2.0, 30, 30
# Gate limits: pole moves at most (m), banner top row moves at most (m), banner bottom sway range (m), loop seam (m), clearance from pole (m).
RIGID_MAX, TOP_MAX, SWAY_RANGE, SEAM_MAX, CLEAR_MIN = 0.001, 0.01, (0.05, 0.35), 0.001, 0.02


def build(level):
    """level 0 = LOD0 (rigid parts only; the card is added apart), 1 = LOD1, 2 = LOD2."""
    if level == 0:
        lathe('base', [(0.24, 0.0), (0.2, 0.07), (0.08, 0.2), (0.05, 0.3)], 'palBronze', [(0.0, 0.08, 'flange'), (0.08, 0.31, 'clouds')], n=24 if MUT == 'tris' else 8)
        lathe('pole', [(POLE_R, 0.28), (POLE_R, POLE_TOP)], 'palLacquerPlain', 'plain', n=8)
        lathe('collar_hi', [(0.044, 3.2), (0.052, 3.3), (0.044, 3.41)], 'palBronze', 'flange', n=8)
        lathe('collar_lo', [(0.044, 1.0), (0.05, 1.06), (0.044, 1.12)], 'palBronze', 'flange', n=8)
        sweep('bar', [(-BAR_HALF, BAR_F, BAR_Z), (BAR_HALF, BAR_F, BAR_Z)], [BAR_R, BAR_R], 'palLacquerPlain', 'plain', n=6)
        for sx in (-1, 1): sweep(f'tip_{sx}', [(sx * BAR_HALF, BAR_F, BAR_Z), (sx * (BAR_HALF + 0.09), BAR_F, BAR_Z)], [0.04, 0.0], 'palBronze', 'plain', n=6)
        top = 3.84 + (1.0 if MUT == 'height' else 0.0)
        lathe('finial', [(0.05, 3.40), (0.07, 3.47), (0.04, 3.52), (0.085, 3.62), (0.0, top)], 'palBronze', 'flange', n=8)
    elif level == 1:
        lathe('base', [(0.24, 0.0), (0.08, 0.2), (0.05, 0.3)], 'palBronze', [(0.0, 0.08, 'flange'), (0.08, 0.31, 'clouds')], n=6)
        lathe('pole', [(POLE_R, 0.28), (POLE_R, POLE_TOP)], 'palLacquerPlain', 'plain', n=6)
        lathe('collar_hi', [(0.048, 3.2), (0.048, 3.41)], 'palBronze', 'flange', n=6)
        sweep('bar', [(-BAR_HALF, BAR_F, BAR_Z), (BAR_HALF, BAR_F, BAR_Z)], [BAR_R, BAR_R], 'palLacquerPlain', 'plain', n=4)
        for sx in (-1, 1): sweep(f'tip_{sx}', [(sx * BAR_HALF, BAR_F, BAR_Z), (sx * (BAR_HALF + 0.09), BAR_F, BAR_Z)], [0.04, 0.0], 'palBronze', 'plain', n=4)
        lathe('finial', [(0.05, 3.40), (0.085, 3.6), (0.0, 3.84)], 'palBronze', 'flange', n=6)
    else:
        lathe('base', [(0.22, 0.0), (0.05, 0.3)], 'palBronze', 'flange', n=6)
        lathe('pole', [(POLE_R, 0.28), (POLE_R, POLE_TOP)], 'palLacquerPlain', 'plain', n=6)
        sweep('bar', [(-BAR_HALF - 0.06, BAR_F, BAR_Z), (BAR_HALF + 0.06, BAR_F, BAR_Z)], [BAR_R, BAR_R], 'palLacquerPlain', 'plain', n=4, cap=False)
        lathe('finial', [(0.06, 3.40), (0.0, 3.84)], 'palBronze', 'flange', n=6)


def banner(name, rows_z, cols):
    """the cloth card: a grid (cols x rows) facing the camera side (+f), UVs on atlas cell 0 (glTF u 0-0.2, v 0-0.5 = Blender v 1-0.5)."""
    bm = bmesh.new(); uvl = bm.loops.layers.uv.new('UVMap')
    w = BANNER_W * (1.5 if MUT == 'texel' else 1.0); xs = [-w / 2 + w * c / cols for c in range(cols + 1)]
    H = BANNER_TOP - BANNER_BOT
    V = [[bm.verts.new(P(x, BANNER_F, z)) for x in xs] for z in rows_z]
    for r in range(len(rows_z) - 1):
        for c in range(cols):
            f = bm.faces.new([V[r + 1][c], V[r + 1][c + 1], V[r][c + 1], V[r][c]])
            f.normal_update()
            if f.normal.y > 0: f.normal_flip()  # front faces the camera side (+f = Blender -y)
            for lp in f.loops:
                co = lp.vert.co; u = (co.x + BANNER_W / 2) / BANNER_W * CELL_UV[0]; v = 1.0 - (BANNER_TOP - co.z) / H * CELL_UV[1]
                lp[uvl].uv = (u, v)
            f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); me.materials.append(K.material('palBanner'))
    return ob


def join(obs, name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]; bpy.ops.object.join()
    ob = bpy.context.active_object; ob.name = name; ob.data.name = name; return ob


def make_rig():
    bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = 'standard_rig'; arm.data.name = 'standard_rig'
    bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
    b = eb.new('pole'); b.head = P(0, 0, 0); b.tail = P(0, 0, BAR_Z); b.roll = 0.0; prev = 'pole'
    for i, (z0, z1) in enumerate(zip(CLOTH_Z, CLOTH_Z[1:])):
        b = eb.new(f'cloth_{i + 1}'); b.head = P(0, BANNER_F, z0); b.tail = P(0, BANNER_F, z1); b.roll = 0.0; b.parent = eb[prev]; prev = b.name
    bpy.ops.object.mode_set(mode='OBJECT')
    return arm


def cloth_weights(z):
    """piecewise-linear blend between the cloth bones' midpoints (max 2 influences, sum 1)."""
    mids = [(a + b) / 2 for a, b in zip(CLOTH_Z, CLOTH_Z[1:])]
    if z >= mids[0]: return {'cloth_1': 1.0}
    for i in range(len(mids) - 1):
        if mids[i + 1] <= z < mids[i]:
            k = (mids[i] - z) / (mids[i] - mids[i + 1]); return {f'cloth_{i + 1}': 1 - k, f'cloth_{i + 2}': k}
    return {f'cloth_{len(mids)}': 1.0}


def sway(arm):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'  # dense keys, linear: no ease at the loop seam
    arm.animation_data_create(); act = bpy.data.actions.new('idle'); arm.animation_data.action = act
    lat_ax = P(0, 1, 0) - P(0, 0, 0); x_ax = Vector((1, 0, 0))
    for k in range(KEYS + 1):
        t = LOOP * k / KEYS; w = math.tau * t / LOOP
        for i, (la, fb, fa, ph) in enumerate(SWAY):
            nm = f'cloth_{i + 1}'; pb = arm.pose.bones[nm]; pb.rotation_mode = 'QUATERNION'
            Mi = arm.data.bones[nm].matrix_local.to_3x3().inverted()
            lat = math.radians(la) * math.sin(w - ph) + (0.3 if MUT == 'loop' and k == KEYS else 0.0)
            fwd = math.radians(fb + fa * (0.5 + 0.5 * math.sin(w - ph + 0.8)))
            pb.rotation_quaternion = Quaternion(Mi @ lat_ax, lat) @ Quaternion(Mi @ x_ax, -fwd)  # -fwd: billow toward the camera side
            pb.keyframe_insert('rotation_quaternion', frame=round(t * FPS))
    for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0)
    # glTF key times = frame / scene fps: keys from frame 0 at the clip fps, so the exported clip starts at 0 s and lasts LOOP s
    sc = bpy.context.scene; sc.render.fps = 24 if MUT == 'fps' else FPS; sc.render.fps_base = 1.0; sc.frame_start = 0; sc.frame_end = KEYS
    return act


def posed(ob, arm, act, frame):
    arm.animation_data.action = act; bpy.context.scene.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get(); ev = ob.evaluated_get(dg); me = ev.to_mesh()
    co = [v.co.copy() for v in me.vertices]; ev.to_mesh_clear(); return co


def glb_mask(path):
    """the exporter does not write alphaMode without an image node: set MASK (cutoff 0.5) and doubleSided on palBanner in the GLB JSON."""
    b = open(path, 'rb').read(); jl = struct.unpack_from('<I', b, 12)[0]; js = json.loads(b[20:20 + jl]); rest = b[20 + jl:]
    for m in js.get('materials', []):
        if m.get('name') == 'palBanner': m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
    j = json.dumps(js, separators=(',', ':')).encode(); j += b' ' * ((4 - len(j) % 4) % 4)
    open(path, 'wb').write(struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + len(rest)) + struct.pack('<II', len(j), 0x4E4F534A) + j + rest)


K.reset()
# static LODs first (prop_kit joins PARTS), each with its flat card
build(1); l1 = join([K.finish('standard_lod1_rigid'), banner('card1', [BANNER_TOP, 2.3, 1.3], 1)], 'standard_lod1')
build(2); l2 = join([K.finish('standard_lod2_rigid'), banner('card2', [BANNER_TOP, BANNER_BOT], 1)], 'standard_lod2')
# LOD0: rigid parts on the pole bone, the card on the cloth bones
build(0); rigid = K.finish('standard_lod0_rigid', True); n_rigid = K.tris(rigid)
rigid.vertex_groups.new(name='pole').add(list(range(len(rigid.data.vertices))), 1.0, 'REPLACE')
if MUT == 'rigid':
    rigid.vertex_groups['pole'].add([v.index for v in rigid.data.vertices if v.co.z > 3.15], 0.5, 'REPLACE')
    rigid.vertex_groups.new(name='cloth_1').add([v.index for v in rigid.data.vertices if v.co.z > 3.15], 0.5, 'REPLACE')
card = banner('card0', ROWS_Z, COLS); n_card = K.tris(card)
uvs = [tuple(l.uv) for l in card.data.uv_layers['UVMap'].data]
for v in card.data.vertices:
    for g, w in cloth_weights(v.co.z).items(): (card.vertex_groups.get(g) or card.vertex_groups.new(name=g)).add([v.index], w, 'REPLACE')
if MUT == 'weights':
    for g in card.vertex_groups: g.remove([0])
arm = make_rig()
lod0 = join([rigid, card], 'standard_lod0')
lod0.parent = arm; md = lod0.modifiers.new('arm', 'ARMATURE'); md.object = arm
arm['schools'] = ','.join(SCHOOLS); arm['atlas'] = 'assets/tex/school_standards.png'; arm['cell_uv'] = list(CELL_UV); arm['alpha_test'] = 0.5
act = sway(arm)

G = K.Gates()
G(n_rigid <= BUDGET[0], f'lod0 rigid tris {n_rigid} (budget {BUDGET[0]})')
G(n_card <= CARD_MAX, f'lod0 cloth card tris {n_card} (max {CARD_MAX})')
for ob, lim in ((l1, BUDGET[1]), (l2, BUDGET[2])): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} incl. card (budget {lim})')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(HEIGHT[0] <= z1 <= HEIGHT[1] and z1 < WALL_H and z0 >= -0.001, f'height {z1:.2f} m (range {HEIGHT}, under the {WALL_H} m hall wall), foot at {z0:.3f}')
G(x1 - x0 <= FOOT_X and y1 - y0 <= FOOT_F, f'footprint {x1 - x0:.2f} x {y1 - y0:.2f} m (max {FOOT_X} x {FOOT_F})')
us = [u for u, v in uvs]; vs = [1 - v for u, v in uvs]
G(min(us) >= -1e-6 and max(us) <= CELL_UV[0] + 1e-6 and min(vs) >= -1e-6 and max(vs) <= CELL_UV[1] + 1e-6,
  f'banner UVs inside atlas cell 0: u {min(us):.3f}-{max(us):.3f}, v {min(vs):.3f}-{max(vs):.3f} (cell {CELL_UV}); one shared mesh, school = UV offset')
tx = (max(us) - min(us)) * ATLAS / (BANNER_W * (1.5 if MUT == 'texel' else 1.0)); ty = (max(vs) - min(vs)) * ATLAS / (BANNER_TOP - BANNER_BOT)
G(abs(tx / TEXEL - 1) <= TEXEL_TOL and abs(ty / TEXEL - 1) <= TEXEL_TOL, f'banner texel density {tx:.0f} x {ty:.0f} px/m (target {TEXEL} +-{TEXEL_TOL:.0%})')
G(K.mats(lod0) >= {'palBronze', 'palLacquerPlain', 'palBanner'}, f'materials {sorted(K.mats(lod0))}: bronze fittings, lacquer pole, banner card')
bones = [b.name for b in arm.data.bones]
G(len(bones) == 4 and bones[0] == 'pole', f'bones {bones}: rigid pole + 3 cloth bones')
bad = 0; maxinf = 0; names = set(bones)
for v in lod0.data.vertices:
    gs = [(lod0.vertex_groups[g.group].name, g.weight) for g in v.groups if g.weight > 1e-6]; maxinf = max(maxinf, len(gs))
    if not gs or abs(sum(w for _, w in gs) - 1) > 0.01 or any(n not in names for n, _ in gs): bad += 1
G(bad == 0 and maxinf <= 4, f'weights: every lod0 vertex on bones, sum 1 ({bad} bad of {len(lod0.data.vertices)}), max {maxinf} influences (limit 4)')
pole_ix = [v.index for v in lod0.data.vertices if any(lod0.vertex_groups[g.group].name == 'pole' for g in v.groups)]
cloth_ix = [v.index for v in lod0.data.vertices if v.index not in set(pole_ix)]
rest = [v.co.copy() for v in lod0.data.vertices]
top_ix = [i for i in cloth_ix if rest[i].z >= BANNER_TOP - 1e-4]; bot_ix = [i for i in cloth_ix if rest[i].z <= BANNER_BOT + 1e-4]
pm = tm = 0.0; bmax = 0.0; clear = 9.0
last = LOOP * FPS
for fr in range(0, int(last) + 1, 2):
    co = posed(lod0, arm, act, fr)
    pm = max(pm, max((co[i] - rest[i]).length for i in pole_ix)); tm = max(tm, max((co[i] - rest[i]).length for i in top_ix))
    bmax = max(bmax, max((co[i] - rest[i]).length for i in bot_ix))
    clear = min(clear, min(-co[i].y for i in cloth_ix) - POLE_R)  # design f = -y: cloth stays in front of the pole
c1 = posed(lod0, arm, act, 0); c2 = posed(lod0, arm, act, int(last)); seam = max((c1[i] - c2[i]).length for i in cloth_ix)
arm.animation_data.action = None
for pb in arm.pose.bones: pb.rotation_quaternion = (1, 0, 0, 0)
G(pm <= RIGID_MAX, f'pole rigid through the clip: max move {pm * 1000:.2f} mm (max {RIGID_MAX * 1000:.0f})')
G(tm <= TOP_MAX, f'banner top edge stays on the crossbar: max move {tm * 1000:.1f} mm (max {TOP_MAX * 1000:.0f})')
G(SWAY_RANGE[0] <= bmax <= SWAY_RANGE[1], f'banner foot sway {bmax:.3f} m (gentle: {SWAY_RANGE})')
G(clear >= CLEAR_MIN, f'cloth clears the pole by {clear:.3f} m through the clip (min {CLEAR_MIN})')
G(seam <= SEAM_MAX, f'idle loop seamless: t=0 vs t={LOOP} max {seam * 1000:.2f} mm (max {SEAM_MAX * 1000:.0f}); loop {LOOP} s')
sc = bpy.context.scene; fr0, fr1 = act.frame_range; secs = (fr1 - fr0) / (sc.render.fps / sc.render.fps_base)
G(abs(fr0) < 1e-6 and abs(secs - LOOP) <= 0.02, f'clip keys from frame {fr0:.0f} to {fr1:.0f} at {sc.render.fps / sc.render.fps_base:.0f} fps = {secs:.2f} s from 0 s (loop {LOOP} s)')
G(not [o for o in bpy.data.objects if o.type == 'LIGHT'], 'no lights in the file')
G.done()
tr = arm.animation_data.nla_tracks.new(); tr.name = 'idle'; tr.strips.new('idle', 0, act)
K.export(OUT, ((l1, 3), (l2, 6)))
glb_mask(OUT)
print('INFO tris', n_rigid, n_card, K.tris(l1), K.tris(l2), 'sway', round(bmax, 3), 'clear', round(clear, 3))
