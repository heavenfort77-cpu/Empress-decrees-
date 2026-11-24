# Bronze guardian beast, round 4 (asset list C1; study art/Qin-Bronze-Castings-Study.md "Samples, round 4").
# Face from ComfyUI round C concept 3129 (run 45432241899; art/beast/concepts/roundC/, reference only, nothing traced). Measured on its
# front view (figure height H = 449 px, mane included): mane width 0.79 H at mid height; eyes 0.23 H below the top at +-0.15 H; nose
# 0.28-0.42 H; mouth open 0.46-0.69 H, about 0.45 H wide; beard tuft to 1.0 H. Here H = HM (head with mane) = 1.05 m.
# What round 4 changes against round 3b (owner: brow reads as a helmet visor, the face is a mask, body and back are plain):
# - mane = a rounded hood mass behind the head with a ring of sharp flame tongues around the face (round 3b: disc curls read as ear muffs);
# - brow = two separate slanted ridges meeting over the nose bridge in a V, a forehead knot and snarl wrinkles (round 3b: one bar = visor);
# - face depth: muzzle, nose, whisker pads and cheeks stand 0.15-0.3 m in front of the eyes; deep-set eyes with dark pupils;
# - body: two cast segment flanges with silver inlay bands around the torso, haunch roundels with silver rims, a tail laid up the
#   spine with flange cuffs and a flame fan, a pendant bell; forelegs with shoulder masses, elbow and wrist flanges, two inlay bands.
# Round where round (lofted superellipse masses, spheroids), sharp where sharp (flame tongues, brows, fangs, claws, flanges, plinth).
# Rounds 1-3b are kept in art/beast/round1/ .. round3b/.
#
# Output (one GLB, Y up, faces +Z in three.js): beast_lod0 skinned to a rigid rig beast_rig (clips 'idle' 1 s, 'strike' with the 0.6 s
# windup tell), beast_lod1 and beast_lod2 static. Materials palBronze (trim sheet UVs at 256 px/m), palInlay (silver), palDark (mouth,
# pupils, nostrils), palStone (plinth, world UVs).
# Usage: /home/claude/bpyenv/bin/python beast_blender.py OUT.glb
import bpy, bmesh, math, sys, os
from mathutils import Vector, Matrix

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/beast.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel width on sharp parts, m (cast chamfer; LOD0 only).
BEVEL = 0.02
# Faces meeting at more than this angle keep a hard edge on round parts (split normals), deg.
SHARP_DEG = 50
# Trim sheet: metres per UV unit (1024 px = 4 m) and rows in image pixels (art/tools/bronze_tex.py layout).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Plinth top height, m.
Z0 = 0.6
# Head with mane: height HM, m (concept 3129 unit); its top T above the floor.
HM = 1.05
T = Z0 + 2.2
# Strike clip timing, s (windup = CONFIG.LION.windup, the 0.6 s tell); study gates: paw rise >= 0.4 m, jaw open >= 25 deg at the windup.
WINDUP, SWIPE, BACK = 0.6, 0.15, 0.5
PAW_RISE_MIN, JAW_DEG, JAW_MIN = 0.4, 32, 25
# Windup pose of the striking (right) foreleg, local Euler deg: the shoulder swings the leg up and out to the side (LEG_ROT), the elbow bends
# the paw forward (FORE_ROT). Round 4 draft: raising the leg straight forward (75 / -55 about X) lifted the paw 0.54 m toward the camera,
# foreshortened at the 40 deg play pitch; up and out it shows in silhouette beside the head. Picked from the POSE_SEARCH=1 grid.
LEG_ROT, FORE_ROT = (-30, 0, 110), (0, 0, 0)
FPS = 60
# Triangle budgets per LOD (palace study: 7k / 2.5k / 800).
BUDGET = (7000, 2500, 800)
# LOD2 decimate ratio of LOD1.
LOD2_RATIO = 0.3
# Collision footprint (index.html palace lion palSolid) and minimum height (box lion), m.
FOOT = (1.8, 2.2)
H_MIN = 2.6

# helpers -------------------------------------------------------------------------------------------------------------
def P(x, f, z):
    """design coords (x right, f forward, z up) -> Blender (forward = -Y, so the glTF faces +Z)."""
    return Vector((x, -f, z))

PARTS = []  # (object, bone, material, row, shade) shade: True = smooth round part, False = sharp bevelled, 'flat' = sharp, no bevel
Q = {'seg': 1.0}  # segment scale: 1 for LOD0, lower for LOD1

def put(name, bm, mat, bone, row, rnd):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, bone, mat, row, rnd))
    return ob

def spheroid(name, c, r, mat, bone, row='plain', segs=(12, 8)):
    """a rounded mass: UV sphere scaled to radii r = (x, f, z)."""
    u = max(6, round(segs[0] * Q['seg'])); v = max(4, round(segs[1] * Q['seg']))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(P(*c)) @ Matrix.Diagonal((r[0], r[1], r[2], 1.0)), verts=bm.verts)
    return put(name, bm, mat, bone, row, True)

def prism(name, prof, a, b, mat, bone, row='plain', scale_b=1.0, rnd=False, flat=False):
    """extrude a closed 2D profile from a to b (design coords); end cap scaled by scale_b. rnd True = smooth sides (a tapered tube)."""
    a, b = P(*a), P(*b); d = (b - a).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((0, 1, 0))
    u = d.cross(up).normalized(); v = u.cross(d).normalized()
    bm = bmesh.new()
    r0 = [bm.verts.new(a + u * p[0] + v * p[1]) for p in prof]
    r1 = [bm.verts.new(b + (u * p[0] + v * p[1]) * scale_b) for p in prof]
    bm.faces.new(list(reversed(r0))); bm.faces.new(r1)
    n = len(prof)
    for i in range(n): bm.faces.new([r0[i], r0[(i + 1) % n], r1[(i + 1) % n], r1[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, 'flat' if flat else rnd)

def tube(name, a, b, r0, r1, mat, bone, row='plain', sides=10):
    n = max(6, round(sides * Q['seg']))
    return prism(name, ngon(r0, n), a, b, mat, bone, row, r1 / r0, rnd=True)

def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def blade(w, t): return [(-w / 2, -t / 2), (w / 2, -t / 2), (0, t / 2)]  # a sharp sliver (claw, fang) when tapered to a point

def loft(name, secs, mat, bone, row='plain', n_exp=2.6, M=24, cap=True):
    """a rounded-square mass lofted through sections (z, cf, hw, hd, cx) in design coords: superellipse rings (exponent n_exp: 2 = ellipse,
    higher = squarer), quads between rings, caps at both ends; smooth sides, hard caps."""
    M = max(10, round(M * Q['seg']))
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
    return put(name, bm, mat, bone, row, True)

def V(*a): return Vector(a)

def tongue(name, base, d, u, L, w, t, bend, bone, mat='palBronze', row='flange'):
    """a sharp cast flame tongue (mane, beard, tail fan): diamond section at the base, bent at mid length toward 'bend', pointed tip.
    base, d (direction), u (width direction), bend in design coords. Flat shaded, no bevel (budget)."""
    d = V(*d).normalized(); u = V(*u); u = (u - d * u.dot(d)).normalized(); v = d.cross(u).normalized(); k = V(*bend)
    b = V(*base)
    def ring(c, s): return [c + u * (w / 2 * s), c + v * (t / 2 * s), c - u * (w / 2 * s), c - v * (t / 2 * s)]
    mid = b + d * (L * 0.55) + k * (L * 0.12); tip = b + d * L + k * (L * 0.35)
    bm = bmesh.new()
    r0 = [bm.verts.new(P(*p)) for p in ring(b, 1.0)]; r1 = [bm.verts.new(P(*p)) for p in ring(mid, 0.7)]; tp = bm.verts.new(P(*tip))
    bm.faces.new(list(reversed(r0)))
    for i in range(4):
        bm.faces.new([r0[i], r0[(i + 1) % 4], r1[(i + 1) % 4], r1[i]]); bm.faces.new([r1[i], r1[(i + 1) % 4], tp])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, 'flat')

def ridge(name, pts, w, h, fwd, bone, row='flange'):
    """a sharp ridge (brow, snarl wrinkle) along pts (design coords): triangle sections back-bottom, front-bottom, crest; the crest leans by
    fwd (design-coords offset per unit height); tapered to 0.5 at both ends."""
    bm = bmesh.new(); rings = []; n = len(pts)
    for i, p in enumerate(pts):
        s = 0.5 + 0.5 * math.sin(math.pi * i / (n - 1)) if n > 2 else 1.0
        p = V(*p); f = V(*fwd)
        rings.append([bm.verts.new(P(*(p + V(0, -w / 2 * s, 0)))), bm.verts.new(P(*(p + V(0, w / 2 * s, -0.01)))), bm.verts.new(P(*(p + V(0, 0, h * s) + f * (h * s))))])
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    for a, b in zip(rings, rings[1:]):
        for i in range(3): bm.faces.new([a[i], a[(i + 1) % 3], b[(i + 1) % 3], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, 'palBronze', bone, row, 'flat')

def sec_at(secs, z):
    """the torso section (cf, hw, hd) interpolated at height z."""
    for a, b in zip(secs, secs[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * k for i in (1, 2, 3))
    return secs[-1][1:4]

def band(name, secs, z, bone, cx=0.0, lip=0.035, inlay=True, M=24):
    """a cast segment flange around a lofted mass at height z: a sharp lip 0.1 m tall (flange row) over a 6 cm silver inlay band."""
    cf, hw, hd = sec_at(secs, z)
    loft(name, [(z - 0.05, cf, hw + 0.004, hd + 0.004, cx), (z - 0.03, cf, hw + lip, hd + lip, cx), (z + 0.03, cf, hw + lip, hd + lip, cx), (z + 0.05, cf, hw + 0.004, hd + 0.004, cx)],
         'palBronze', bone, 'flange', M=M, cap=False)
    if inlay:
        cf2, hw2, hd2 = sec_at(secs, z - 0.09)
        loft(name + '_inlay', [(z - 0.12, cf2, hw2 + 0.012, hd2 + 0.012, cx), (z - 0.06, cf2, hw2 + 0.012, hd2 + 0.012, cx)], 'palInlay', bone, cap=False)

# mane hood (z, cf, hw, hd, cx): widest over the shoulders and set back, rounding over the crown just under the face top
HOOD = [(Z0 + 1.0, -0.2, 0.52, 0.46, 0), (Z0 + 1.3, -0.1, 0.5, 0.4, 0), (T - 0.55, 0.0, 0.44, 0.34, 0), (T - 0.32, 0.04, 0.38, 0.28, 0),
        (T - 0.16, 0.06, 0.28, 0.22, 0), (T - 0.09, 0.07, 0.14, 0.11, 0)]
TORSO = [(Z0, -0.28, 0.6, 0.66, 0), (Z0 + 0.3, -0.25, 0.64, 0.68, 0), (Z0 + 0.6, -0.15, 0.6, 0.6, 0), (Z0 + 0.9, -0.02, 0.52, 0.5, 0),
         (Z0 + 1.15, 0.08, 0.46, 0.42, 0), (Z0 + 1.35, 0.1, 0.36, 0.34, 0)]

def build(detail):
    PARTS.clear()
    # plinth: two stepped stone tiers (sharp; the collision footprint 1.8 x 2.2 m)
    prism('plinth_a', rect(1.8, 2.2), (0, 0, 0), (0, 0, 0.35), 'palStone', 'root')
    prism('plinth_b', rect(1.6, 2.0), (0, 0, 0.35), (0, 0, Z0), 'palStone', 'root')
    # torso: one lofted mass, rump low and behind, chest high and forward; two cast segment flanges with silver inlay below each
    loft('torso', TORSO, 'palBronze', 'body')
    for k, z in enumerate((Z0 + 0.45, Z0 + 0.9)): band(f'seg_{k}', TORSO, z, 'body', inlay=True)
    # haunches: thigh masses on the flanks, each with a cast roundel (silver rim, cloud-band face, spiral boss)
    for s in (-1, 1):
        spheroid(f'haunch_{s}', (s * 0.5, -0.38, Z0 + 0.38), (0.26, 0.5, 0.36), 'palBronze', 'body')
        x0 = s * 0.74
        prism(f'rim_{s}', ngon(0.25, 14 if detail else 8), (x0, -0.38, Z0 + 0.42), (x0 + s * 0.03, -0.38, Z0 + 0.42), 'palInlay', 'body', rnd=True)
        prism(f'roundel_{s}', ngon(0.19, 14 if detail else 8), (x0 + s * 0.02, -0.38, Z0 + 0.42), (x0 + s * 0.06, -0.38, Z0 + 0.42), 'palBronze', 'body', 'clouds', rnd=True)
        prism(f'boss_{s}', ngon(0.08, 8), (x0 + s * 0.05, -0.38, Z0 + 0.42), (x0 + s * 0.11, -0.38, Z0 + 0.42), 'palBronze', 'body', 'flange', scale_b=0.6, rnd=True)
        # hind paws beside the forelegs, toes and claws forward
        loft(f'hpaw_{s}', [(Z0, 0.2, 0.15, 0.24, s * 0.62), (Z0 + 0.08, 0.2, 0.16, 0.25, s * 0.62), (Z0 + 0.17, 0.12, 0.13, 0.2, s * 0.62)], 'palBronze', 'body', n_exp=2.4, M=16)
        for k in range(3):
            tx = s * 0.62 + (k - 1) * 0.09
            if detail: spheroid(f'htoe_{s}{k}', (tx, 0.42, Z0 + 0.07), (0.05, 0.06, 0.06), 'palBronze', 'body', segs=(6, 4))
            if detail: prism(f'hclaw_{s}{k}', blade(0.045, 0.035), (tx, 0.46, Z0 + 0.06), (tx, 0.53, Z0 + 0.01), 'palInlay', 'body', scale_b=0.1, flat=True)
    # forelegs: shoulder mass, upper leg, elbow flange, forearm with two 6 cm silver bands, wrist flange, paw with four toes and claws
    for s in (-1, 1):
        side = 'R' if s < 0 else 'L'; x = s * 0.3
        spheroid(f'shoulder_{side}', (s * 0.34, 0.3, Z0 + 1.02), (0.2, 0.24, 0.28), 'palBronze', f'leg_{side}')
        UP = [(Z0 + 0.72, 0.45, 0.165, 0.15, x), (Z0 + 0.86, 0.43, 0.18, 0.17, x), (Z0 + 1.0, 0.4, 0.19, 0.18, x)]
        loft(f'upper_{side}', UP, 'palBronze', f'leg_{side}', n_exp=2.2, M=18)
        FA = [(Z0 + 0.22, 0.5, 0.13, 0.12, x), (Z0 + 0.46, 0.48, 0.14, 0.13, x), (Z0 + 0.72, 0.46, 0.16, 0.15, x)]
        loft(f'fore_{side}', FA, 'palBronze', f'fore_{side}', n_exp=2.2, M=18)
        if detail: band(f'elbow_{side}', FA, Z0 + 0.7, f'fore_{side}', cx=x, lip=0.03, inlay=False, M=16)
        if detail:
            for k, z in enumerate((Z0 + 0.56, Z0 + 0.4)):
                cf, hw, hd = sec_at(FA, z)
                loft(f'fband_{side}{k}', [(z - 0.03, cf, hw + 0.012, hd + 0.012, x), (z + 0.03, cf, hw + 0.012, hd + 0.012, x)], 'palInlay', f'fore_{side}', M=18, cap=False)
        if detail: band(f'wrist_{side}', FA, Z0 + 0.27, f'fore_{side}', cx=x, lip=0.03, inlay=False, M=16)
        loft(f'paw_{side}', [(Z0, 0.6, 0.18, 0.26, x), (Z0 + 0.1, 0.6, 0.19, 0.27, x), (Z0 + 0.22, 0.52, 0.14, 0.18, x)], 'palBronze', f'paw_{side}', n_exp=2.4, M=18)
        for k in range(4):
            tx = x + (k - 1.5) * 0.095
            if detail: spheroid(f'toe_{side}{k}', (tx, 0.83, Z0 + 0.08), (0.052, 0.07, 0.07), 'palBronze', f'paw_{side}', segs=(6, 4))
            if detail: prism(f'claw_{side}{k}', blade(0.05, 0.04), (tx, 0.88, Z0 + 0.07), (tx, 0.97, Z0 + 0.01), 'palInlay', f'paw_{side}', scale_b=0.1, flat=True)
    # pendant bell on a short strap in front of the chest (imperial guardian: the collar; the tiger has none)
    spheroid('bell', (0, 0.56, Z0 + 0.98), (0.11, 0.09, 0.12), 'palBronze', 'body', 'mask', segs=(10, 6))
    tube('strap', (0, 0.52, Z0 + 1.16), (0, 0.56, Z0 + 1.08), 0.035, 0.03, 'palInlay', 'body', sides=8)
    if detail: tube('bell_lip', (0, 0.56, Z0 + 0.88), (0, 0.56, Z0 + 0.86), 0.1, 0.1, 'palInlay', 'body', sides=12)
    # tail laid up the spine: three round segments with flange cuffs, a fan of flame tongues at the top (up and sideways, never backward)
    pts = [(0, -0.98, Z0 + 0.12), (0, -1.0, Z0 + 0.36), (0, -0.94, Z0 + 0.58), (0, -0.84, Z0 + 0.76)]
    for i in range(3):
        tube(f'tail_{i}', pts[i], pts[i + 1], 0.085 - i * 0.01, 0.075 - i * 0.01, 'palBronze', f'tail_{i}', sides=10)
        if detail and i: tube(f'tcuff_{i}', (pts[i][0], pts[i][1] - 0.0, pts[i][2] - 0.02), (pts[i][0], pts[i][1], pts[i][2] + 0.03), 0.1 - i * 0.01, 0.1 - i * 0.01, 'palBronze', f'tail_{i}', 'flange', sides=10)
    nf = 5 if detail else 3
    for k in range(nf):
        a = math.radians(-60 + 120 * k / (nf - 1))
        tongue(f'fan_{k}', (0, -0.86, Z0 + 0.74), (math.sin(a), 0.1, math.cos(a)), (math.cos(a), 0, -math.sin(a)), 0.32, 0.15, 0.06, (math.sin(a) * 0.5, 0, 0.3), 'tail_2')
    # ---- head (concept 3129 rows; z relative to the mane top T, sizes in metres with HM = 1.05) ----
    # mane hood: a rounded mass behind the face, spreading over the shoulders (the back of the head is mane, not a dome)
    loft('hood', HOOD, 'palBronze', 'head', 'plain', n_exp=2.3)  # draft 2: the clouds row made it read as a patterned cloth hood
    # face mass (cranium) in front of the hood
    loft('cranium', [(T - 0.74, 0.24, 0.2, 0.18, 0), (T - 0.55, 0.21, 0.29, 0.26, 0), (T - 0.35, 0.19, 0.31, 0.28, 0), (T - 0.18, 0.16, 0.3, 0.27, 0),
                     (T - 0.06, 0.13, 0.24, 0.23, 0), (T - 0.01, 0.11, 0.13, 0.13, 0)], 'palBronze', 'head', 'plain', n_exp=2.4)
    # brows: two slanted sharp ridges rising from the bridge to the temples (a V scowl, not one bar), the forehead knot, snarl wrinkles
    for s in (-1, 1):
        ridge(f'brow_{s}', [(s * 0.04, 0.47, T - 0.2), (s * 0.15, 0.45, T - 0.15), (s * 0.27, 0.38, T - 0.08)], 0.09, 0.07, (0, 0.6, 0), 'head')
        if detail: ridge(f'brow2_{s}', [(s * 0.07, 0.42, T - 0.11), (s * 0.15, 0.4, T - 0.07), (s * 0.23, 0.34, T - 0.02)], 0.06, 0.04, (0, 0.4, 0), 'head')
    spheroid('knot', (0, 0.43, T - 0.1), (0.065, 0.05, 0.06), 'palBronze', 'head', 'flange', segs=(8, 5))
    loft('bridge', [(T - 0.32, 0.5, 0.075, 0.06, 0), (T - 0.25, 0.48, 0.07, 0.06, 0), (T - 0.18, 0.45, 0.06, 0.05, 0)], 'palBronze', 'head', n_exp=2.2, M=12)
    if detail:
        for k, z in enumerate((T - 0.24, T - 0.28)):
            ridge(f'wrinkle_{k}', [(-0.08, 0.53 + k * 0.02, z), (0, 0.55 + k * 0.02, z + 0.01), (0.08, 0.53 + k * 0.02, z)], 0.05, 0.035, (0, 0.5, 0), 'head')
    # eyes: deep-set silver almonds under the brows with dark pupils (at least 12 cm across)
    for s in (-1, 1):
        spheroid(f'eye_{s}', (s * 0.15, 0.44, T - 0.24), (0.075, 0.035, 0.032), 'palInlay', 'head', segs=(10, 6))
        spheroid(f'pupil_{s}', (s * 0.14, 0.468, T - 0.245), (0.036, 0.012, 0.026), 'palDark', 'head', segs=(6, 4))
        ridge(f'lid_{s}', [(s * 0.07, 0.47, T - 0.235), (s * 0.15, 0.48, T - 0.215), (s * 0.24, 0.44, T - 0.19)], 0.06, 0.04, (0, 0.7, -0.3), 'head')
    # nose: broad bulb with flared nostrils, 0.28-0.42 HM below the top, the most forward part of the face
    spheroid('nose', (0, 0.6, T - 0.35), (0.13, 0.1, 0.08), 'palBronze', 'head', segs=(12, 8))
    for s in (-1, 1):
        if detail: spheroid(f'nflare_{s}', (s * 0.1, 0.6, T - 0.38), (0.055, 0.06, 0.045), 'palBronze', 'head', segs=(6, 4))
        if detail: spheroid(f'nostril_{s}', (s * 0.065, 0.675, T - 0.39), (0.035, 0.02, 0.022), 'palDark', 'head', segs=(6, 4))
        # whisker pads (the upper lip mass) and cheeks sweeping back into the mane
        spheroid(f'pad_{s}', (s * 0.12, 0.55, T - 0.44), (0.14, 0.1, 0.075), 'palBronze', 'head', segs=(12, 8))
        spheroid(f'cheek_{s}', (s * 0.25, 0.4, T - 0.42), (0.12, 0.13, 0.17), 'palBronze', 'head', segs=(10, 7))
    # open mouth (dark), upper fangs and incisors; lower jaw on its own bone with lower fangs and the beard tuft
    loft('mouth', [(T - 0.68, 0.4, 0.19, 0.12, 0), (T - 0.57, 0.42, 0.2, 0.13, 0), (T - 0.47, 0.42, 0.18, 0.12, 0)], 'palDark', 'head', n_exp=2.2, M=14)
    for s in (-1, 1):
        prism(f'fang_{s}', blade(0.06, 0.05), (s * 0.13, 0.58, T - 0.48), (s * 0.13, 0.6, T - 0.63), 'palInlay', 'head', scale_b=0.1, flat=True)
        if detail:
            for xk in (0.035, 0.08):
                prism(f'inc_{s}{xk}', blade(0.035, 0.03), (s * xk, 0.6, T - 0.5), (s * xk, 0.61, T - 0.56), 'palInlay', 'head', scale_b=0.2, flat=True)
    loft('jaw', [(T - 0.77, 0.42, 0.16, 0.12, 0), (T - 0.71, 0.45, 0.21, 0.15, 0), (T - 0.65, 0.46, 0.22, 0.14, 0)], 'palBronze', 'jaw', 'lozenge', n_exp=2.2, M=16)
    for s in (-1, 1):
        prism(f'lfang_{s}', blade(0.05, 0.045), (s * 0.11, 0.56, T - 0.67), (s * 0.11, 0.57, T - 0.56), 'palInlay', 'jaw', scale_b=0.1, flat=True)
    for k, xs in enumerate((-0.08, 0.0, 0.08)):
        tongue(f'beard_{k}', (xs, 0.46, T - 0.74), (xs * 1.5, 0.15, -1), (1, 0, 0), 0.26 if xs else 0.3, 0.12, 0.06, (0, 0.25, 0), 'jaw')
    # mane: a ring of sharp flame tongues around the face (outer and inner ring), tips curling outward and up; none under the chin (beard)
    FC = (0, 0.36, T - 0.4)
    for ring, (n, rx, rz, L, w, ff) in enumerate(((14, 0.33, 0.4, 0.2, 0.17, 0.3), (12, 0.38, 0.45, 0.2, 0.16, 0.16)) if detail else ((9, 0.35, 0.42, 0.22, 0.2, 0.25),)):
        for i in range(n):
            th = math.radians(-145 + 290 * (i + 0.5 * ring) / (n - 1 + ring))
            dx, dz = math.sin(th), math.cos(th)
            base = (FC[0] + dx * rx, ff, FC[2] + dz * rz)
            top = dz > 0.75  # over the crown the tongues sweep back over the head (the round 4 draft's upright tongues read as a sunburst crown)
            tongue(f'mane{ring}_{i}', base, (dx * 0.75, -1.1 if top else -0.6, dz * (0.35 if top else 0.75)), (dz, 0, -dx), L, w, 0.07, (dx * 0.35, -0.2 if top else 0.1, dz * 0.35), 'head')
    # back mane: rows of tongues falling down the back of the hood (pointing down, never backward)
    rows = ((5, T - 0.2), (6, T - 0.48), (5, T - 0.76), (6, Z0 + 1.2)) if detail else ((3, T - 0.3), (3, T - 0.7))
    for ri, (m, z) in enumerate(rows):
        cf, hw, hd = sec_at(HOOD, z)
        for i in range(m):
            a = math.radians(-80 + 160 * (i + 0.5 * (ri % 2)) / (m - 1 + (ri % 2)))
            base = (math.sin(a) * hw * 0.97, cf - math.cos(a) * hd * 0.97, z)
            tongue(f'bmane{ri}_{i}', base, (math.sin(a) * 0.6, -0.6 * math.cos(a), -0.8), (math.cos(a), math.sin(a), 0), 0.26, 0.16, 0.07, (math.sin(a) * 0.4, -0.4 * math.cos(a), 0.15), 'head' if ri < 3 else 'body')

BONES = [('root', P(0, 0, 0), P(0, 0, Z0), None), ('body', P(0, -0.2, Z0 + 0.3), P(0, 0.08, Z0 + 1.2), 'root'),
         ('head', P(0, 0.1, Z0 + 1.2), P(0, 0.25, T), 'body'), ('jaw', P(0, 0.3, T - 0.62), P(0, 0.6, T - 0.7), 'head')]
for side, s in (('R', -1), ('L', 1)):
    x = s * 0.3
    BONES += [(f'leg_{side}', P(x, 0.36, Z0 + 1.05), P(x, 0.45, Z0 + 0.72), 'body'), (f'fore_{side}', P(x, 0.45, Z0 + 0.72), P(x, 0.5, Z0 + 0.22), f'leg_{side}'),
              (f'paw_{side}', P(x, 0.5, Z0 + 0.22), P(x, 0.95, Z0 + 0.05), f'fore_{side}')]
BONES += [('tail_0', P(0, -0.98, Z0 + 0.12), P(0, -1.0, Z0 + 0.36), 'body'), ('tail_1', P(0, -1.0, Z0 + 0.36), P(0, -0.94, Z0 + 0.58), 'tail_0'),
          ('tail_2', P(0, -0.94, Z0 + 0.58), P(0, -0.84, Z0 + 0.76), 'tail_1')]

def uv_trim(ob, row):
    """per-face planar UVs at 256 px/m on the dominant axis; v inside the part's trim-sheet row. glTF keeps image rows top-down (flipY false)."""
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

def uv_world(ob):
    me = ob.data; uvl = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        n = poly.normal; ax = max(range(3), key=lambda i: abs(n[i])); ua, va = [(1, 2), (0, 2), (0, 1)][ax]
        for li in poly.loop_indices:
            c = me.vertices[me.loops[li].vertex_index].co; uvl.data[li].uv = (c[ua] / M_PER_UV, c[va] / M_PER_UV)

def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

TALLY = {}
def finish(name, bevel):
    TALLY.clear()
    for ob, bone, mat, row, rnd in PARTS:
        if mat == 'palStone': uv_world(ob)
        else: uv_trim(ob, row)
        ob.data.materials.append(material(mat))
        vg = ob.vertex_groups.new(name=bone); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
        bm = bmesh.new(); bm.from_mesh(ob.data)
        if bevel and rnd is False:
            bmesh.ops.bevel(bm, geom=list(bm.edges), offset=BEVEL, segments=1, affect='EDGES', clamp_overlap=True)
        for f in bm.faces: f.smooth = rnd is True
        if rnd is True:  # hard edges only where faces fold sharply (tube caps, flange lips); the rounded sides stay smooth
            for e in bm.edges:
                if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(SHARP_DEG): e.smooth = False
        bm.to_mesh(ob.data); bm.free()
        fam = ob.name.split('_')[0].rstrip('0123456789'); TALLY[fam] = TALLY.get(fam, 0) + sum(len(p.vertices) - 2 for p in ob.data.polygons)
    print(name, 'tris by part family:', TALLY)
    bpy.ops.object.select_all(action='DESELECT')
    for ob, *_ in PARTS: ob.select_set(True)
    bpy.context.view_layer.objects.active = PARTS[0][0]
    bpy.ops.object.join(); ob = bpy.context.active_object; ob.name = name; ob.data.name = name
    return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = FPS

Q['seg'] = 0.5; build(False); lod1 = finish('beast_lod1', False)
for vg in list(lod1.vertex_groups): lod1.vertex_groups.remove(vg)
build(False); lod2 = finish('beast_lod2', False)
for vg in list(lod2.vertex_groups): lod2.vertex_groups.remove(vg)
dm = lod2.modifiers.new('dec', 'DECIMATE'); dm.ratio = LOD2_RATIO
bpy.context.view_layer.objects.active = lod2; bpy.ops.object.modifier_apply(modifier='dec')
Q['seg'] = 1.0; build(True); lod0 = finish('beast_lod0', True)
PART_COUNT = len(PARTS)

bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = 'beast_rig'
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
for n, h, t, p in BONES:
    b = eb.new(n); b.head = h; b.tail = t
    if p: b.parent = eb[p]
bpy.ops.object.mode_set(mode='OBJECT')
lod0.parent = arm; mod = lod0.modifiers.new('arm', 'ARMATURE'); mod.object = arm

r = math.radians
def tip(lr, fr):
    """world position of the right paw tip with the leg and forearm bones at the given local Euler rotations (radians)."""
    for b, rr in (('leg_R', lr), ('fore_R', fr)):
        pb = arm.pose.bones[b]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rr
    bpy.context.view_layer.update(); t = arm.matrix_world @ arm.pose.bones['paw_R'].tail
    for b in ('leg_R', 'fore_R'): arm.pose.bones[b].rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update(); return t
if os.environ.get('POSE_SEARCH'):  # print a grid of windup poses (right paw tip), then stop
    t0 = tip((0, 0, 0), (0, 0, 0)); print('rest tip', tuple(round(v, 2) for v in t0))
    for lx in (-60, -30, 0, 30, 60):
        for lz in (-110, -80, 80, 110):
            for fx in (-40, 0, 40):
                t = tip((r(lx), 0, r(lz)), (r(fx), 0, 0)); print('leg', lx, lz, 'fore', fx, 'tip', tuple(round(v, 2) for v in t))
    sys.exit(0)
LEG_W, FORE_W = tuple(r(a) for a in LEG_ROT), tuple(r(a) for a in FORE_ROT)
t_rest, t_up = tip((0, 0, 0), (0, 0, 0)), tip(LEG_W, FORE_W)
rise = t_up.z - t_rest.z; out = abs(t_up.x) - abs(t_rest.x)

def jaw_dir(a):
    pb = arm.pose.bones['jaw']; pb.rotation_mode = 'XYZ'; pb.rotation_euler = (a, 0, 0); bpy.context.view_layer.update()
    d = (arm.matrix_world @ pb.tail) - (arm.matrix_world @ pb.head); pb.rotation_euler = (0, 0, 0); bpy.context.view_layer.update(); return d
JS = 1 if jaw_dir(r(JAW_DEG)).z < jaw_dir(-r(JAW_DEG)).z else -1  # the chin end of the jaw must go down
jaw_open = math.degrees(jaw_dir(0).angle(jaw_dir(JS * r(JAW_DEG))))
jaw_down = jaw_dir(JS * r(JAW_DEG)).z < jaw_dir(0).z

def key(bone, f, rot):
    pb = arm.pose.bones[bone]; pb.rotation_mode = 'XYZ'; pb.rotation_euler = rot; pb.keyframe_insert('rotation_euler', frame=f)

def clip(name, keys):
    arm.animation_data_create(); act = bpy.data.actions.new(name); arm.animation_data.action = act
    for bone, frames in keys.items():
        for f, rot in frames: key(bone, f, rot)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act)
    arm.animation_data.action = None

f_w, f_s, f_b = 1 + round(WINDUP * FPS), 1 + round((WINDUP + SWIPE) * FPS), 1 + round((WINDUP + SWIPE + BACK) * FPS)
clip('strike', {
    'jaw': [(1, (0, 0, 0)), (f_w, (JS * r(JAW_DEG), 0, 0)), (f_s, (JS * r(JAW_DEG + 4), 0, 0)), (f_b, (0, 0, 0))],
    'leg_R': [(1, (0, 0, 0)), (f_w, LEG_W), (f_s, (r(-20), 0, 0)), (f_b, (0, 0, 0))],
    'fore_R': [(1, (0, 0, 0)), (f_w, FORE_W), (f_s, (0, 0, 0)), (f_b, (0, 0, 0))],
})
clip('idle', {'tail_2': [(1, (0, 0, 0)), (31, (0, r(6), 0)), (61, (0, 0, 0))], 'tail_1': [(1, (0, 0, 0)), (31, (0, r(-3), 0)), (61, (0, 0, 0))]})

fails = 0; n_checks = 0
def gate(ok, line):
    global fails, n_checks
    n_checks += 1; fails += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + line)
for ob, lim in zip((lod0, lod1, lod2), BUDGET): gate(tris(ob) <= lim, f'{ob.name} tris {tris(ob)} (budget {lim})')
gate(all(v.groups for v in lod0.data.vertices), 'beast_lod0 every vertex on a bone')
gate(rise >= PAW_RISE_MIN, f'strike windup paw rise {rise:.2f} m, {out:.2f} m out to the side (min rise {PAW_RISE_MIN})')
gate(jaw_open >= JAW_MIN and jaw_down, f'strike windup jaw open {jaw_open:.0f} deg, chin down {jaw_down} (min {JAW_MIN})')
bb = [lod0.matrix_world @ Vector(c) for c in lod0.bound_box]
w, d, h = max(c.x for c in bb) - min(c.x for c in bb), max(c.y for c in bb) - min(c.y for c in bb), max(c.z for c in bb)
gate(h >= H_MIN, f'height {h:.2f} m (min {H_MIN}, box lion)')
gate(w <= FOOT[0] + 1e-6 and d <= FOOT[1] + 1e-6, f'footprint {w:.2f} x {d:.2f} m (max {FOOT[0]} x {FOOT[1]})')
share = sum(1 for p in lod0.data.polygons if p.use_smooth) / len(lod0.data.polygons)
gate(share >= 0.5, f'smooth-shaded share {share:.0%} (round forms, min 50%)')
print(f'parts {PART_COUNT}, bones {len(BONES)}')
print(f'{n_checks - fails} of {n_checks} pass')
lod1.location.x = 3; lod2.location.x = 6
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_nla_strips=True, export_materials='EXPORT', export_image_format='NONE')
print('wrote', OUT, os.path.getsize(OUT), 'bytes')
