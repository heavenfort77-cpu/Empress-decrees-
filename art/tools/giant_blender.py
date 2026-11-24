# The twelve bronze giants 十二金人 (asset list C8; W1c overnight 25 Nov 2026; study art/Qin-Bronze-Castings-Study.md method).
# GDD (docs/BURNING-PALACE.md "Palace pieces"): they stand along the approach to the core; she wakes one each time a wing burns; a woken giant
# slowly hunts the nearest suit with slow, big tells and heavy hits; killable mini-bosses with health and a bar; every side hurts it.
# Research (docs/research/Qin-palace-medieval-tech-fusion.md): bell-stand bearers cast from the conquered states' melted weapons (Shiji);
# about 11.5 m in a later source, no image survives. One shared skeleton and body cast (on-lore for batch-cast Qin bronze), a distinct head,
# shoulder beam (the bell-stand beam they bear) and weapon-fragment motif per giant, two per conquered state; patina dormant, brass awake.
# Size follows the game, not the 11.5 m source: index.html PIECES2.giant r 1.1 m, box giant 4.9 m tall, health bar at y 5.4, the fore
# giants stand 5 m apart (PAL_FULL_PIECES), slam windup 1 s radius 4 m, sweep windup 1.2 s line 7 x 3 m, wakeS 2, fallS 0.8, speed 3.2.
# Our own design throughout; ComfyUI concepts (run 45441111768) are reference only, nothing traced.
#
# Output (one GLB, Y up, faces +Z in three.js): giant_rig (one armature, clips below), giant_body_lod0/1/2 (the shared cast body) and
# giant_gNN_lod0/1/2 (head, beam, motif of giant NN), all skinned rigid to giant_rig (every vertex 100% on one bone); giant_flakes (the
# patina flakes that fall in the wake clip, LOD0 only). Materials: palBronze (trim sheet UVs at 256 px/m; the game swaps the sheet:
# bronze_trim_patina.png dormant, bronze_trim_brass.png or bronze_trim.png awake), palTin (high-tin bronze weapon edges and eyes; pale
# verdigris when dormant), palPatina (flakes). Two materials per giant: two draw calls per giant per LOD.
# Clips: dormant (beam held overhead, still), wake (2 s), carry (awake idle), walk (1 s loop, in place, 3.2 m/s), slam (1 s windup),
# sweep (1.2 s windup), hit, fall (0.8 s, ends lying).
# Usage: /home/claude/bpyenv/bin/python giant_blender.py OUT.glb   (env GIANTS=0,3 builds a subset; GATES_ONLY=1 skips the export)
import bpy, bmesh, math, sys, os, json, random
from mathutils import Vector, Matrix, Quaternion

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/giants.glb'
ONLY = [int(s) for s in os.environ['GIANTS'].split(',')] if os.environ.get('GIANTS') else list(range(12))

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Bevel width on sharp parts, m (cast chamfer; LOD0 only).
BEVEL = 0.015
# Faces meeting at more than this angle keep a hard edge on round parts (split normals), deg.
SHARP_DEG = 50
# Trim sheet: metres per UV unit (1024 px = 4 m) and rows in image pixels (art/tools/bronze_tex.py layout).
M_PER_UV = 4.0
ROWS = {'plain': (40, 344), 'clouds': (384, 448), 'inlay': (448, 512), 'lozenge': (512, 576), 'flange': (576, 640), 'mask': (640, 704), 'mark': (704, 768)}
# Animation frame rate and the key step (frames between sampled keys).
FPS, KEY_STEP = 60, 2
# Triangle budgets per giant (shared body + its head, beam and motif) for LOD0 / LOD1 / LOD2 (task: 15k / 3k / 1k).
BUDGET = (15000, 3000, 1000)
# Segment scale per LOD (1 = full round sections).
SEG = (1.0, 0.45, 0.26)
# Heights, m: carried pose top under the game's health bar (index.html bar at y 5.4); dormant pose (beam overhead, no bar) top; minimum
# (the game's box giant is 4.9 m).
H_CARRY_MAX, H_DORM_MAX, H_MIN = 5.3, 5.8, 4.5
# Body radius below Z_BODY (CONFIG.PIECES2.giant.r = 1.1 m) and the widest giant (fore giants stand 5 m apart), m.
R_BODY, Z_BODY, W_MAX = 1.12, 2.6, 4.4
# Game timings (CONFIG.PIECES2.giant): speed m/s, slam and sweep windups s, wake s, fall s.
SPEED, SLAM_W, SWEEP_W, WAKE_S, FALL_S = 3.2, 1.0, 1.2, 2.0, 0.8
# Walk cycle s (two steps); stance foot speed must match SPEED (in-place clip, the game moves the giant).
WALK_T = 1.0
# Tell gates: by 0.4 s into a windup the beam has moved at least TELL_EARLY m; at the windup it has risen / swung at least these.
TELL_EARLY, SLAM_RISE, SWEEP_ARC = 0.5, 0.9, 60
# Hands stay on the beam within this distance at every sampled frame, m.
GRIP_TOL = 0.08
# FIX-A (owner 25 Nov: stronger melted-weapon motifs on 02, 05, 07, 08 that read at play size): melt pool size multiplier on those motifs.
MOTIF_MELT = 1.6

# FIX-A (owner 25 Nov 02:1x: keep one shared body, slimmer and taller-reading at the 40 deg game camera): longer legs at the same
# height. Every mesh vertex and bone is remapped in height: WARP_Z0..WARP_HIP (legs) stretch so the hip rises by LEG_ADD, WARP_HIP..WARP_Z1
# (pelvis, belt, abdomen) shorten by the same amount, below WARP_Z0 (feet) and above WARP_Z1 (chest, arms, beam, head) nothing moves, so
# grips, beam, heights and the walk targets stay where they were. Applied in put() and to the rig; directions are never remapped.
WARP_Z0, WARP_HIP, WARP_Z1, LEG_ADD = 0.3, 1.95, 2.8, 0.2
def Wz(z):
    if z <= WARP_Z0 or z >= WARP_Z1: return z
    if z <= WARP_HIP: return WARP_Z0 + (z - WARP_Z0) * (WARP_HIP + LEG_ADD - WARP_Z0) / (WARP_HIP - WARP_Z0)
    return WARP_HIP + LEG_ADD + (z - WARP_HIP) * (WARP_Z1 - WARP_HIP - LEG_ADD) / (WARP_Z1 - WARP_HIP)

# design coordinates (x right, f forward, z up) -> Blender (forward = -Y, so the glTF faces +Z)
def P(x, f, z): return Vector((x, -f, z))
def PW(x, f, z): return Vector((x, -f, Wz(z)))  # a remapped position (rig bones)
def V(*a): return Vector(a)

PARTS = []
Q = {'seg': 1.0, 'lod': 0}

def put(name, bm, mat, bone, row, rnd):
    for v in bm.verts: v.co.z = Wz(v.co.z)  # FIX-A height remap (longer legs)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob)
    PARTS.append((ob, bone, mat, row, rnd)); return ob

def spheroid(name, c, r, mat, bone, row='plain', segs=(12, 8)):
    u = max(6, round(segs[0] * Q['seg'])); v = max(4, round(segs[1] * Q['seg']))
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(P(*c)) @ Matrix.Diagonal((r[0], r[1], r[2], 1.0)), verts=bm.verts)
    return put(name, bm, mat, bone, row, True)

def ngon(r, n, rot=0.0): return [(math.cos(rot + i * math.tau / n) * r, math.sin(rot + i * math.tau / n) * r) for i in range(n)]
def flutes(r, n): return [(math.cos(i * math.tau / n) * r * (1 if i % 2 else 0.86), math.sin(i * math.tau / n) * r * (1 if i % 2 else 0.86)) for i in range(n)]
def rect(w, h): return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
def sides(n): return max(4, round(n * Q['seg']))

def sweep(name, pts, profs, mat, bone, row='plain', rnd=True, closed=False, up=(0, 0, 1), cap=True):
    """a tube along pts (design coords) with a 2D profile per point (or one profile); parallel-transported frames, so rings do not twist."""
    pts = [V(*p) for p in pts]; n = len(pts)
    if not isinstance(profs[0][0], (tuple, list)): profs = [profs] * n
    bm = bmesh.new(); rings = []; u = None
    for i, p in enumerate(pts):
        a = pts[(i - 1) % n] if (closed or i > 0) else p; b = pts[(i + 1) % n] if (closed or i < n - 1) else p
        t = (b - a).normalized()
        if u is None:
            u = t.cross(V(*up)); u = u.normalized() if u.length > 1e-6 else t.cross(V(1, 0, 0)).normalized()
        else:
            u = (u - t * u.dot(t)); u = u.normalized() if u.length > 1e-6 else t.cross(V(*up)).normalized()
        v = t.cross(u).normalized()
        rings.append([bm.verts.new(P(*(p + u * q[0] + v * q[1]))) for q in profs[i]])
    m = len(rings[0])
    for k in range(n if closed else n - 1):
        a, b = rings[k], rings[(k + 1) % n]
        for i in range(m): bm.faces.new([a[i], a[(i + 1) % m], b[(i + 1) % m], b[i]])
    if not closed and cap: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, rnd)

def tube(name, a, b, r0, r1, mat, bone, row='plain', n=10):
    k = sides(n); return sweep(name, [a, b], [ngon(r0, k), ngon(r1, k)], mat, bone, row)

def torus(name, c, axis, R, r, mat, bone, row='flange', n=14, m=6):
    c = V(*c); ax = V(*axis).normalized(); e1 = ax.cross(V(0, 0, 1)) if abs(ax.z) < 0.9 else ax.cross(V(1, 0, 0)); e1.normalize(); e2 = ax.cross(e1)
    k = sides(n); pts = [tuple(c + (e1 * math.cos(i * math.tau / k) + e2 * math.sin(i * math.tau / k)) * R) for i in range(k)]
    return sweep(name, pts, ngon(r, max(4, sides(m))), mat, bone, row, closed=True, up=tuple(ax))

def loft(name, secs, mat, bone, row='plain', n_exp=2.6, M=24, cap=True):
    """a rounded-square mass lofted through sections (z, cf, hw, hd, cx) (superellipse rings); smooth sides."""
    M = max(8, round(M * Q['seg'])); bm = bmesh.new(); rings = []
    for z, cf, hw, hd, cx in secs:
        ring = []
        for i in range(M):
            t = i * math.tau / M; c, s = math.cos(t), math.sin(t)
            ring.append(bm.verts.new(P(cx + hw * math.copysign(abs(c) ** (2 / n_exp), c), cf + hd * math.copysign(abs(s) ** (2 / n_exp), s), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(M): bm.faces.new([a[i], a[(i + 1) % M], b[(i + 1) % M], b[i]])
    if cap: bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, True)

def tongue(name, base, d, u, L, w, t, bend, bone, mat='palBronze', row='flange'):
    """a sharp cast blade or flame tongue: diamond section, bent toward 'bend', pointed tip; flat shaded."""
    d = V(*d).normalized(); u = V(*u); u = (u - d * u.dot(d)).normalized(); v = d.cross(u).normalized(); k = V(*bend); b = V(*base)
    def ring(c, s): return [c + u * (w / 2 * s), c + v * (t / 2 * s), c - u * (w / 2 * s), c - v * (t / 2 * s)]
    mid = b + d * (L * 0.55) + k * (L * 0.12); tip = b + d * L + k * (L * 0.35)
    bm = bmesh.new(); r0 = [bm.verts.new(P(*p)) for p in ring(b, 1.0)]; r1 = [bm.verts.new(P(*p)) for p in ring(mid, 0.75)]; tp = bm.verts.new(P(*tip))
    bm.faces.new(list(reversed(r0)))
    for i in range(4): bm.faces.new([r0[i], r0[(i + 1) % 4], r1[(i + 1) % 4], r1[i]]); bm.faces.new([r1[i], r1[(i + 1) % 4], tp])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, 'flat')

def plate(name, outline, c, u, v, th, mat, bone, row='plain'):
    """a flat cast plate (blade, chime stone, fin, flake): a 2D outline in the (u, v) plane at c, thickness th; flat shaded."""
    c = V(*c); u = V(*u).normalized(); v = V(*v); v = (v - u * v.dot(u)).normalized(); n = u.cross(v)
    bm = bmesh.new()
    a = [bm.verts.new(P(*(c + u * p[0] + v * p[1] + n * th / 2))) for p in outline]
    b = [bm.verts.new(P(*(c + u * p[0] + v * p[1] - n * th / 2))) for p in outline]
    bm.faces.new(a); bm.faces.new(list(reversed(b))); m = len(outline)
    for i in range(m): bm.faces.new([a[i], b[i], b[(i + 1) % m], a[(i + 1) % m]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, 'flat')

def ridge(name, pts, w, h, fwd, bone, row='flange', mat='palBronze'):
    """a sharp ridge (brow, lip, collar edge) along pts; triangle sections leaning by fwd; tapered at both ends."""
    bm = bmesh.new(); rings = []; n = len(pts)
    for i, p in enumerate(pts):
        s = 0.5 + 0.5 * math.sin(math.pi * i / (n - 1)) if n > 2 else 1.0; p = V(*p); f = V(*fwd)
        rings.append([bm.verts.new(P(*(p + V(0, -w / 2 * s, 0)))), bm.verts.new(P(*(p + V(0, w / 2 * s, -0.01)))), bm.verts.new(P(*(p + V(0, 0, h * s) + f * (h * s))))])
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    for a, b in zip(rings, rings[1:]):
        for i in range(3): bm.faces.new([a[i], a[(i + 1) % 3], b[(i + 1) % 3], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return put(name, bm, mat, bone, row, 'flat')

def sec_at(secs, z):
    for a, b in zip(secs, secs[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return tuple(a[i] + (b[i] - a[i]) * k for i in (1, 2, 3))
    return secs[-1][1:4] if z > secs[-1][0] else secs[0][1:4]

def surf(secs, z, deg, out=0.0, n_exp=2.6):
    """point on a lofted section at height z and angle deg (90 = front, 0 = +x), pushed out by 'out'; and its outward direction."""
    cf, hw, hd = sec_at(secs, z); t = math.radians(deg); c, s = math.cos(t), math.sin(t)
    x = hw * math.copysign(abs(c) ** (2 / n_exp), c); f = cf + hd * math.copysign(abs(s) ** (2 / n_exp), s)
    nrm = V(c / max(hw, 1e-3), s / max(hd, 1e-3), 0).normalized()
    return V(x, f, z) + nrm * out, nrm

def band(name, secs, z, bone, lip=0.03, n_exp=2.6, M=24, row='flange'):
    """a cast segment flange around a lofted mass at height z (sharp lip, flange row)."""
    cf, hw, hd = sec_at(secs, z)
    return loft(name, [(z - 0.05, cf, hw + 0.004, hd + 0.004, 0), (z - 0.03, cf, hw + lip, hd + lip, 0), (z + 0.03, cf, hw + lip, hd + lip, 0), (z + 0.05, cf, hw + 0.004, hd + 0.004, 0)],
                'palBronze', bone, row, n_exp=n_exp, M=M, cap=False)

# ---------------------------------------------------------------------------------------------------------------------
# Body layout (design coords, m). Rest pose = the carried pose: beam across the shoulders behind the neck, hands gripping it.
# FIX-A slimmer: waist 0.6 -> 0.47 half width, skirt flare 0.64-0.89 -> 0.53-0.66 and its hem 1.42 -> 1.6 m (before the height remap;
# 1.76 m after), chest a little narrower; broad shoulders kept (a V taper reads taller than a column).
TORSO_LO = [(2.12, 0.0, 0.5, 0.4, 0), (2.4, 0.02, 0.47, 0.38, 0), (2.66, 0.04, 0.58, 0.44, 0)]
TORSO_HI = [(2.56, 0.04, 0.6, 0.45, 0), (2.8, 0.05, 0.72, 0.5, 0), (3.02, 0.06, 0.78, 0.52, 0), (3.24, 0.03, 0.78, 0.48, 0), (3.42, -0.02, 0.62, 0.38, 0), (3.56, -0.04, 0.3, 0.27, 0)]
SKIRT = [[(2.34, 0.0, 0.53, 0.42, 0), (2.18, 0.02, 0.57, 0.45, 0), (2.04, 0.03, 0.6, 0.48, 0)],
         [(2.1, 0.03, 0.59, 0.47, 0), (1.94, 0.04, 0.62, 0.5, 0), (1.8, 0.05, 0.64, 0.52, 0)],
         [(1.86, 0.05, 0.63, 0.51, 0), (1.72, 0.06, 0.65, 0.53, 0), (1.6, 0.06, 0.66, 0.54, 0)]]
SHOULDER = {s: V(s * 0.86, -0.02, 3.32) for s in (-1, 1)}
BC = V(0, -0.36, 3.66)  # beam centre, behind the neck on the trapezius
BEAM_R = 0.17
GRIP_X = 1.35
GRIP = {s: BC + V(s * GRIP_X, 0, 0) for s in (-1, 1)}
UA, FA = 0.78, 0.76  # upper arm, forearm (elbow to fist centre) lengths
HIP = {s: V(s * 0.38, 0.0, 1.95) for s in (-1, 1)}
KNEE = {s: V(s * 0.4, 0.06, 1.08) for s in (-1, 1)}
ANKLE = {s: V(s * 0.42, 0.0, 0.22) for s in (-1, 1)}
TOE = {s: V(s * 0.42, 0.45, 0.06) for s in (-1, 1)}
NECK0, HEAD_PIV = 3.5, 3.62
ROOT_PIVOT = V(0, 0.55, 0.0)  # the fall pivots over the toes

def two_bone(S, T, a, b, pole):
    """elbow / knee position for a two-bone chain from S toward T (lengths a, b), bending toward pole (a direction)."""
    d = T - S; L = d.length; L = min(max(L, abs(a - b) + 1e-4), a + b - 1e-4); n = d.normalized()
    ca = (a * a + L * L - b * b) / (2 * a * L); sa = math.sqrt(max(0.0, 1 - ca * ca))
    p = pole - n * pole.dot(n); p = p.normalized() if p.length > 1e-6 else n.orthogonal().normalized()
    return S + n * (a * ca) + p * (a * sa)

POLE_ARM = {s: V(s * 1.0, 0.25, -0.8) for s in (-1, 1)}
ELBOW = {s: two_bone(SHOULDER[s], GRIP[s], UA, FA, POLE_ARM[s]) for s in (-1, 1)}

def build_body(lod):
    d0, d1 = lod == 0, lod <= 1
    # torso: lower (spine bone) and upper (chest bone) masses with a cast segment flange where they meet, robe crossover collar
    loft('abdomen', TORSO_LO, 'palBronze', 'spine', 'plain', n_exp=2.4, M=24)
    loft('chest', TORSO_HI, 'palBronze', 'chest', 'plain', n_exp=2.4, M=24)
    band('chest_flange', TORSO_HI, 2.62, 'chest', lip=0.035, n_exp=2.4)
    if d1:
        # mould seams down both flanks (piece-mould casting) and a workshop mark plate on the back (research: a mark on every plate)
        for s in (-1, 1):
            ridge(f'seam_hi_{s}', [tuple(surf(TORSO_HI, z, 90 - s * 90, 0.005, 2.4)[0]) for z in (2.66, 2.9, 3.15, 3.38)], 0.05, 0.035, (s * 0.6, 0, 0), 'chest')
            for k, tier in enumerate(SKIRT):
                ridge(f'seam_sk{k}_{s}', [tuple(surf(tier, z, 90 - s * 90, 0.005, 2.2)[0]) for z in (tier[0][0] - 0.04, (tier[0][0] + tier[-1][0]) / 2, tier[-1][0] + 0.04)], 0.05, 0.035, (s * 0.6, 0, 0), 'pelvis')
        p_, n_ = surf(TORSO_HI, 2.95, 270, 0.012, 2.4)
        plate('mark_back', rect(0.36, 0.36), tuple(p_), (1, 0, 0), (0, 0, 1), 0.03, 'palBronze', 'chest', 'mark')
    if d1:
        for s in (-1, 1):  # crossed robe collar (交领), left over right, sharp cast edge
            pts = [tuple(surf(TORSO_HI, z, 90 + s * a, 0.01, 2.4)[0]) for z, a in ((3.46, 55), (3.3, 40), (3.12, 22), (2.94, 6 if s > 0 else 2))]
            ridge(f'collar_{s}', pts, 0.12, 0.05, (0, 0.5, 0), 'chest')
    # belt with a belt hook (带钩) and the skirt in three cast tiers, each with a flange lip at its hem (segmented casting)
    loft('belt', [(2.26, 0.01, 0.52, 0.41, 0), (2.44, 0.02, 0.5, 0.4, 0)], 'palBronze', 'pelvis', 'lozenge', n_exp=2.4, M=24, cap=False)
    if d1:
        tube('hook', (0, 0.42, 2.3), (0, 0.54, 2.42), 0.05, 0.025, 'palTin', 'pelvis', 'plain', n=8)
        spheroid('hook_boss', (0, 0.43, 2.33), (0.07, 0.03, 0.06), 'palBronze', 'pelvis', 'flange', segs=(8, 5))
    for k, tier in enumerate(SKIRT if d1 else [[SKIRT[0][0], SKIRT[1][1], SKIRT[2][-1]]]):
        loft(f'skirt_{k}', tier, 'palBronze', 'pelvis', 'plain' if k != 1 else 'clouds', n_exp=2.2, M=28, cap=False)
        if d1 and k == len(SKIRT) - 1: band(f'skirt_lip_{k}', tier, tier[-1][0] + 0.04, 'pelvis', lip=0.03, n_exp=2.2, M=28)  # FIX-A: hem lip only (less stacked)
    # legs: thigh (mostly under the skirt), knee guard, shin with a boot flange, boot
    for s in (-1, 1):
        side = 'L' if s > 0 else 'R'
        # legs as fluted columns (concept 6105: a pleated column under the tunic), so the standing giant reads columnar and still walks
        # FIX-A slimmer legs: thigh 0.29 -> 0.25, shin 0.27 -> 0.23, boot 0.24 -> 0.21 half width
        tube(f'thigh_{side}', tuple(HIP[s]), tuple(KNEE[s]), 0.25, 0.22, 'palBronze', f'thigh_{side}', n=10)
        if d1: spheroid(f'knee_{side}', tuple(KNEE[s] + V(0, 0.08, 0.02)), (0.19, 0.15, 0.18), 'palBronze', f'shin_{side}', 'flange', segs=(10, 6))
        nf = sides(16) // 2 * 2
        sweep(f'shin_{side}', [tuple(KNEE[s]), tuple(ANKLE[s] + V(0, 0, 0.05))], [flutes(0.23, nf), flutes(0.2, nf)], 'palBronze', f'shin_{side}', 'plain')
        if d1: tube(f'boot_top_{side}', tuple(ANKLE[s] + V(0, 0, 0.3)), tuple(ANKLE[s] + V(0, 0, 0.38)), 0.235, 0.235, 'palBronze', f'shin_{side}', 'flange', n=12)
        x = s * 0.42
        loft(f'boot_{side}', [(0.0, 0.12, 0.21, 0.44, x), (0.12, 0.1, 0.22, 0.42, x), (0.26, 0.02, 0.21, 0.28, x), (0.36, 0.0, 0.2, 0.24, x)], 'palBronze', f'foot_{side}', 'plain', n_exp=2.3, M=16)
        if d0: spheroid(f'toecap_{side}', (x, 0.44, 0.1), (0.13, 0.12, 0.1), 'palBronze', f'foot_{side}', 'flange', segs=(8, 5))
    # arms (built along the rest pose's IK chain): shoulder mass, upper arm, elbow, banded forearm, fist around the beam
    for s in (-1, 1):
        side = 'L' if s > 0 else 'R'; S, E, G = SHOULDER[s], ELBOW[s], GRIP[s]
        # cast pauldron: a domed plate over the shoulder with a flange rim (not a ball)
        if d1: spheroid(f'shoulder_{side}', tuple(S + V(s * 0.02, 0, -0.02)), (0.24, 0.24, 0.22), 'palBronze', f'upper_{side}', segs=(10, 7))
        loft(f'pauldron_{side}', [(S.z - 0.17, S.y, 0.26, 0.29, S.x + s * 0.08), (S.z + 0.02, S.y, 0.26, 0.28, S.x + s * 0.05), (S.z + 0.15, S.y, 0.17, 0.2, S.x + s * 0.02), (S.z + 0.21, S.y, 0.05, 0.07, S.x)],
             'palBronze', f'upper_{side}', 'plain', n_exp=2.4, M=18, cap=True)
        if d1: loft(f'pauldron_rim_{side}', [(S.z - 0.21, S.y, 0.29, 0.32, S.x + s * 0.09), (S.z - 0.15, S.y, 0.29, 0.32, S.x + s * 0.08)], 'palBronze', f'upper_{side}', 'flange', n_exp=2.4, M=18, cap=False)
        tube(f'upper_{side}', tuple(S), tuple(E), 0.2, 0.17, 'palBronze', f'upper_{side}', n=10)
        if d1: spheroid(f'elbow_{side}', tuple(E), (0.17, 0.17, 0.17), 'palBronze', f'fore_{side}', segs=(8, 6))
        dirv = (G - E).normalized(); W = G - dirv * 0.14
        tube(f'fore_{side}', tuple(E), tuple(W), 0.17, 0.13, 'palBronze', f'fore_{side}', n=10)
        if d1:
            for k, t in enumerate((0.3, 0.62)):
                c = E + (W - E) * t; rr = 0.17 + (0.13 - 0.17) * t
                tube(f'bracer_{side}{k}', tuple(c - dirv * 0.03), tuple(c + dirv * 0.03), rr + 0.03, rr + 0.03, 'palBronze', f'fore_{side}', 'flange', n=10)
        spheroid(f'fist_{side}', tuple(G + V(0, 0.03, -0.02)), (0.16, 0.17, 0.17), 'palBronze', f'fore_{side}', segs=(10, 7))
        if d0: spheroid(f'thumb_{side}', tuple(G + V(-s * 0.1, 0.12, 0.08)), (0.06, 0.08, 0.05), 'palBronze', f'fore_{side}', segs=(6, 4))
    # neck (moves with the head)
    tube('neck', (0, -0.02, NECK0 - 0.05), (0, 0.0, 3.86), 0.25, 0.23, 'palBronze', 'head', n=12)

# ---- heads ---------------------------------------------------------------------------------------------------------
HEAD = [(3.7, 0.12, 0.2, 0.15, 0), (3.8, 0.06, 0.3, 0.27, 0), (3.95, 0.02, 0.34, 0.32, 0), (4.12, 0.0, 0.34, 0.34, 0), (4.28, -0.02, 0.3, 0.31, 0),
        (4.38, -0.03, 0.2, 0.22, 0), (4.43, -0.03, 0.08, 0.09, 0)]

def face(g, H, lod):
    """the shared face plan with the giant's own proportions: jaw width, brow, nose, ears; cast eyes in high-tin bronze."""
    d0, d1 = lod == 0, lod <= 1
    j, sk = H.get('jaw', 1.0), H.get('skull', 1.0)
    secs = [(z, cf, hw * (j if z < 3.96 else sk), hd, cx) for z, cf, hw, hd, cx in HEAD]
    loft(f'{g}_cranium', secs, 'palBronze', 'head', 'plain', n_exp=2.3, M=20)
    brow = H.get('brow', 'v')
    for s in (-1, 1):
        if brow == 'v': pts = [(s * 0.03, 0.36, 4.1), (s * 0.13, 0.355, 4.14), (s * 0.25, 0.3, 4.19)]
        elif brow == 'heavy': pts = [(s * 0.02, 0.38, 4.13), (s * 0.13, 0.38, 4.15), (s * 0.27, 0.31, 4.14)]
        elif brow == 'arch': pts = [(s * 0.04, 0.35, 4.12), (s * 0.14, 0.35, 4.18), (s * 0.26, 0.3, 4.14)]
        else: pts = [(s * 0.03, 0.36, 4.13), (s * 0.14, 0.355, 4.14), (s * 0.26, 0.3, 4.13)]
        ridge(f'{g}_brow_{s}', pts, 0.08, 0.08 if brow == 'heavy' else 0.06, (0, 0.6, 0), 'head')
        if d1:
            spheroid(f'{g}_eye_{s}', (s * 0.13, 0.325, 4.05), (0.075, 0.035, 0.04), 'palTin', 'head', segs=(10, 6))
            if d0: spheroid(f'{g}_pupil_{s}', (s * 0.13, 0.352, 4.05), (0.03, 0.014, 0.03), 'palBronze', 'head', 'flange', segs=(6, 4))
            ridge(f'{g}_lid_{s}', [(s * 0.05, 0.34, 4.07), (s * 0.13, 0.36, 4.085), (s * 0.21, 0.32, 4.07)], 0.05, 0.035, (0, 0.8, -0.3), 'head')
            if d0: ridge(f'{g}_under_{s}', [(s * 0.07, 0.33, 4.015), (s * 0.13, 0.34, 4.005), (s * 0.2, 0.31, 4.02)], 0.03, 0.02, (0, 0.6, 0), 'head')
            er = H.get('ears', 1.0)
            spheroid(f'{g}_ear_{s}', (s * 0.31 * sk, 0.0, 4.02), (0.05, 0.09 * er, 0.13 * er), 'palBronze', 'head', segs=(8, 5))
        if d0: spheroid(f'{g}_cheek_{s}', (s * 0.18 * j, 0.24, 3.94), (0.1, 0.08, 0.07), 'palBronze', 'head', segs=(8, 5))
    nw = H.get('nose', 1.0)
    loft(f'{g}_nose', [(3.9, 0.39, 0.085 * nw, 0.065, 0), (3.98, 0.38, 0.06 * nw, 0.055, 0), (4.1, 0.36, 0.045, 0.04, 0), (4.16, 0.35, 0.05, 0.035, 0)], 'palBronze', 'head', n_exp=2.2, M=10)
    if d1:
        ridge(f'{g}_lip', [(-0.12 * j, 0.3, 3.83), (0, 0.335, 3.825), (0.12 * j, 0.3, 3.83)], 0.05, 0.035, (0, 0.6, 0), 'head')
        ridge(f'{g}_lip2', [(-0.09 * j, 0.3, 3.785), (0, 0.325, 3.78), (0.09 * j, 0.3, 3.785)], 0.05, 0.03, (0, 0.6, -0.2), 'head')
    beard(g, H.get('beard', 'none'), lod)

def beard(g, kind, lod):
    if kind == 'mous':
        for s in (-1, 1): tongue(f'{g}_mous_{s}', (s * 0.04, 0.37, 3.86), (s * 1, 0.25, -0.5), (0, 0, 1), 0.24, 0.07, 0.04, (s * 0.2, 0, -0.3), 'head')
    elif kind == 'long':
        for k, x in enumerate((-0.09, 0.0, 0.09)): tongue(f'{g}_beard_{k}', (x, 0.22, 3.74), (x, 0.3, -1), (1, 0, 0), 0.5 if x == 0 else 0.4, 0.13, 0.07, (0, 0.15, 0), 'head')
    elif kind == 'chin':
        tongue(f'{g}_beard', (0, 0.22, 3.73), (0, 0.4, -1), (1, 0, 0), 0.28, 0.12, 0.07, (0, 0.3, 0), 'head')
    elif kind == 'forked':
        for s in (-1, 1): tongue(f'{g}_fork_{s}', (s * 0.05, 0.22, 3.74), (s * 0.35, 0.35, -1), (1, 0, 0), 0.42, 0.11, 0.07, (s * 0.15, 0.2, 0), 'head')
    elif kind == 'full':
        spheroid(f'{g}_jawbeard', (0, 0.15, 3.76), (0.27, 0.2, 0.13), 'palBronze', 'head', 'lozenge', segs=(10, 6))
        for k, x in enumerate((-0.12, 0.0, 0.12)): tongue(f'{g}_beard_{k}', (x, 0.22, 3.7), (x * 0.6, 0.25, -1), (1, 0, 0), 0.24, 0.12, 0.06, (0, 0.2, 0), 'head')
    elif kind == 'braid':
        pts = [(0, 0.24, 3.74), (0, 0.33, 3.6), (0, 0.36, 3.44), (0, 0.34, 3.28), (0.0, 0.3, 3.16)]
        sweep(f'{g}_braid', pts, [ngon(r, sides(8)) for r in (0.1, 0.085, 0.075, 0.065, 0.03)], 'palBronze', 'head', 'lozenge')
        if lod <= 1:
            for k, z in enumerate((3.55, 3.38)): torus(f'{g}_braidring_{k}', (0, 0.355, z), (0.1, 0.0, 1), 0.085, 0.025, 'palTin', 'head', n=10, m=4)

def cap_shell(g, z0, out, row='plain', top=4.47):
    """hair or cap shell over the skull from z0 up (offset 'out')."""
    secs = [(z, cf, hw + out, hd + out, cx) for z, cf, hw, hd, cx in HEAD if z >= z0 - 0.01]
    secs[-1] = (top, secs[-1][1], secs[-1][2] * 0.6, secs[-1][3] * 0.6, 0)
    return loft(f'{g}_shell', secs, 'palBronze', 'head', row, n_exp=2.3, M=20)

def head(i, g, lod):
    H = HEADS[i]; face(g, H, lod); kind = H['kind']; d1 = lod <= 1
    if kind == 'topknot':
        cap_shell(g, 4.12, 0.025, 'lozenge')
        spheroid(f'{g}_bun', (0.15, -0.1, 4.5), (0.14, 0.14, 0.13), 'palBronze', 'head', 'clouds', segs=(10, 7))
        if d1: torus(f'{g}_bunband', (0.15, -0.1, 4.44), (0.25, 0, 1), 0.13, 0.03, 'palTin', 'head', n=12, m=4)
        tongue(f'{g}_ribbon', (0.2, -0.16, 4.48), (0.4, -0.6, -0.4), (0, 0, 1), 0.42, 0.12, 0.03, (0, 0, -0.3), 'head')
    elif kind == 'pointed':
        pts = [(0, -0.02, 4.2), (0, -0.0, 4.5), (0, 0.06, 4.78), (0, 0.16, 5.0), (0, 0.3, 5.12)]
        sweep(f'{g}_cap', pts, [ngon(r, sides(14)) for r in (0.35, 0.3, 0.2, 0.1, 0.02)], 'palBronze', 'head', 'clouds')
        if d1: torus(f'{g}_capband', (0, -0.02, 4.22), (0, 0, 1), 0.34, 0.035, 'palBronze', 'head', n=16)
        for s in (-1, 1): plate(f'{g}_flap_{s}', [(0, 0), (0.16, 0), (0.12, -0.3), (0.02, -0.34)], (s * 0.33, 0.0, 4.15), (0, 1, 0), (0, 0, 1), 0.04, 'palBronze', 'head', 'flange')
    elif kind == 'board':
        cap_shell(g, 4.15, 0.02, 'plain')
        tube(f'{g}_post', (0, -0.04, 4.4), (0, -0.06, 4.56), 0.08, 0.06, 'palBronze', 'head', n=8)
        plate(f'{g}_board', rect(0.42, 0.7), (0, -0.04, 4.6), (1, 0, 0), (0, 1, 0.3), 0.06, 'palBronze', 'head', 'clouds')
        for s in (-1, 1): ridge(f'{g}_strap_{s}', [(s * 0.3, 0.05, 4.18), (s * 0.27, 0.1, 3.95), (s * 0.18, 0.16, 3.74)], 0.05, 0.03, (s * 0.5, 0, 0), 'head')
    elif kind == 'plumes':
        cap_shell(g, 4.15, 0.03, 'clouds')
        for s in (-1, 1):
            tongue(f'{g}_plume_{s}', (s * 0.12, -0.08, 4.38), (s * 0.25, -0.35, 1), (1, 0, 0), 0.82, 0.14, 0.06, (s * 0.15, -0.5, 0), 'head', 'palBronze', 'lozenge')
            if d1: tongue(f'{g}_plume2_{s}', (s * 0.2, -0.06, 4.34), (s * 0.6, -0.3, 1), (0, 1, 0), 0.5, 0.1, 0.05, (s * 0.3, -0.3, 0), 'head', 'palBronze', 'lozenge')
    elif kind == 'widehat':
        prism_disc(g, 'brim', (0, -0.02, 4.33), 0.66, 0.045, 16)
        spheroid(f'{g}_crown', (0, -0.02, 4.4), (0.3, 0.31, 0.2), 'palBronze', 'head', 'clouds', segs=(14, 7))
        if d1: spheroid(f'{g}_knob', (0, -0.02, 4.62), (0.07, 0.07, 0.07), 'palTin', 'head', segs=(8, 5))
    elif kind == 'bald':
        spheroid(f'{g}_dome', (0, -0.02, 4.25), (0.32, 0.34, 0.3), 'palBronze', 'head', 'plain', segs=(14, 8))
        ridge(f'{g}_scalp', [(0, 0.28, 4.4), (0, 0.05, 4.56), (0, -0.25, 4.45)], 0.08, 0.12, (0, 0, 0), 'head')
        for s in (-1, 1): torus(f'{g}_earring_{s}', (s * 0.4, 0.0, 3.74), (1, 0, 0), 0.19, 0.04, 'palTin', 'head', n=14, m=5)
    elif kind == 'spikes':
        cap_shell(g, 4.2, 0.02, 'lozenge')
        loft(f'{g}_crownband', [(4.2, 0.0, 0.34, 0.36, 0), (4.34, 0.0, 0.33, 0.35, 0)], 'palBronze', 'head', 'flange', n_exp=2.3, M=20, cap=False)
        for k, (x, L, tilt) in enumerate(((0, 0.6, 0), (0.18, 0.44, 0.35), (-0.18, 0.44, -0.35), (0.3, 0.3, 0.8), (-0.3, 0.3, -0.8))):
            if k >= 3 and not d1: continue
            tongue(f'{g}_spike_{k}', (x, 0.28 - abs(x) * 0.4, 4.3), (tilt, 0.15, 1), (1, 0, 0), L, 0.14, 0.06, (0, 0, 0), 'head')
    elif kind == 'hood':
        secs = [(3.82, -0.02, 0.38, 0.38, 0), (4.0, -0.03, 0.38, 0.39, 0), (4.2, -0.04, 0.36, 0.38, 0), (4.38, -0.06, 0.28, 0.32, 0), (4.52, -0.1, 0.12, 0.16, 0), (4.58, -0.14, 0.03, 0.05, 0)]
        loft(f'{g}_hood', secs, 'palBronze', 'head', 'clouds', n_exp=2.3, M=20)
        loft(f'{g}_hoodrim', [(4.24, 0.27, 0.27, 0.05, 0), (4.2, 0.32, 0.25, 0.06, 0)], 'palBronze', 'head', 'flange', n_exp=3, M=12)
        # crescent crest across the hood (round 2: the round 1 hood read as a plain dome)
        o = [(-0.55 + 1.1 * k / 10, 0.12 + 0.42 * (abs(-1 + 2 * k / 10) ** 1.6)) for k in range(11)] + [(0.55 - 1.1 * k / 10, 0.12 + 0.2 * (abs(1 - 2 * k / 10) ** 2.2) - 0.02) for k in range(11)]
        plate(f'{g}_crescent', o, (0, -0.06, 4.4), (1, 0, 0), (0, 0, 1), 0.06, 'palBronze', 'head', 'clouds')
        for s in (-1, 1): plate(f'{g}_lappet_{s}', [(-0.12, 0), (0.12, 0), (0.1, -0.55), (0, -0.62), (-0.1, -0.55)], (s * 0.36, 0.14, 3.88), (0, 1, 0), (0, 0, 1), 0.05, 'palBronze', 'head', 'lozenge')
    elif kind == 'helmet':
        spheroid(f'{g}_dome', (0, -0.02, 4.2), (0.37, 0.39, 0.3), 'palBronze', 'head', 'lozenge', segs=(14, 8))
        sweep(f'{g}_guard', [(-0.36, -0.1, 4.0), (-0.25, -0.35, 3.92), (0, -0.44, 3.88), (0.25, -0.35, 3.92), (0.36, -0.1, 4.0)], rect(0.04, 0.24), 'palBronze', 'head', 'flange', rnd='flat')
        plate(f'{g}_nasal', [(-0.03, 0.1), (0.03, 0.1), (0.025, -0.16), (-0.025, -0.16)], (0, 0.38, 4.05), (1, 0, 0), (0, 0, 1), 0.04, 'palTin', 'head')
        ridge(f'{g}_crest', [(0, 0.3, 4.3), (0, 0.12, 4.47), (0, -0.12, 4.47), (0, -0.32, 4.3)], 0.06, 0.14, (0, 0, 0), 'head')
    elif kind == 'horns':
        cap_shell(g, 4.15, 0.03, 'lozenge')
        for s in (-1, 1):
            pts = [(s * 0.26, 0.02, 4.32), (s * 0.48, 0.05, 4.36), (s * 0.66, 0.08, 4.48), (s * 0.74, 0.12, 4.66), (s * 0.72, 0.2, 4.8)]
            sweep(f'{g}_horn_{s}', pts, [ngon(r, sides(10)) for r in (0.11, 0.09, 0.07, 0.045, 0.012)], 'palBronze', 'head', 'flange')
    elif kind == 'tallcap':
        cap_shell(g, 4.15, 0.02, 'plain')
        loft(f'{g}_tall', [(4.3, -0.02, 0.15, 0.27, 0), (4.55, 0.0, 0.14, 0.25, 0), (4.85, 0.04, 0.28, 0.24, 0), (5.05, 0.07, 0.42, 0.22, 0), (5.12, 0.07, 0.4, 0.2, 0)], 'palBronze', 'head', 'clouds', n_exp=3.2, M=16)
        if d1: ridge(f'{g}_tallrib', [(0, 0.26, 4.32), (0, 0.27, 4.66), (0, 0.29, 4.98)], 0.05, 0.05, (0, 0.6, 0), 'head')
        for s in (-1, 1): plate(f'{g}_ribbon_{s}', [(-0.04, 0), (0.04, 0), (0.03, -0.5), (-0.03, -0.5)], (s * 0.3, -0.12, 4.2), (0, 1, 0), (0, 0, 1), 0.03, 'palBronze', 'head', 'flange')
    elif kind == 'twinbuns':
        cap_shell(g, 4.1, 0.025, 'lozenge')
        for s in (-1, 1):
            spheroid(f'{g}_bun_{s}', (s * 0.36, -0.04, 4.46), (0.2, 0.2, 0.2), 'palBronze', 'head', 'clouds', segs=(10, 7))
            if d1: torus(f'{g}_bunring_{s}', (s * 0.27, -0.04, 4.4), (s * 0.7, 0, 0.7), 0.15, 0.035, 'palTin', 'head', n=12, m=4)
        torus(f'{g}_toploop', (0, -0.04, 4.55), (1, 0, 0), 0.12, 0.04, 'palBronze', 'head', n=12, m=5)

def prism_disc(g, n, c, r, th, k):
    return sweep(f'{g}_{n}', [tuple(V(*c) - V(0, 0, th / 2)), tuple(V(*c) + V(0, 0, th / 2))], ngon(r, sides(k)), 'palBronze', 'head', 'flange', rnd=True)

# ---- beams (the bell-stand beam each giant bears) --------------------------------------------------------------------
def beam(i, g, lod):
    B = BEAMS[i]; d1 = lod <= 1; L = B.get('L', 1.75); arch = B.get('arch', 0.0); r = B.get('r', BEAM_R); n = 9 if d1 else 5
    xs = [-L + 2 * L * k / (n - 1) for k in range(n)]
    path = [(x, BC.y, BC.z + arch * (x / L) ** 2) for x in xs]
    prof = B.get('prof', 'round')
    if prof == 'double':
        for k, dz in enumerate((-0.12, 0.12)): sweep(f'{g}_bar_{k}', [(x, y, z + dz) for x, y, z in path], ngon(0.1, sides(10)), 'palBronze', 'beam', 'flange')
        for k, x in enumerate((-1.6, -0.6, 0.6, 1.6)): sweep(f'{g}_spacer_{k}', [(x - 0.06, BC.y, BC.z + arch * (x / L) ** 2), (x + 0.06, BC.y, BC.z + arch * (x / L) ** 2)], rect(0.2, 0.36), 'palBronze', 'beam', 'mask', rnd='flat')
    elif prof == 'twist':
        m = 4; pr = [[(math.cos(k * 0.6 + j * math.tau / m) * r * 1.15, math.sin(k * 0.6 + j * math.tau / m) * r * 1.15) for j in range(m)] for k in range(n * 2 - 1)]
        xs2 = [-L + 2 * L * k / (2 * n - 2) for k in range(2 * n - 1)]
        sweep(f'{g}_shaft', [(x, BC.y, BC.z + arch * (x / L) ** 2) for x in xs2], pr, 'palBronze', 'beam', 'lozenge', rnd='flat')
    else:
        pr = {'round': ngon(r, sides(12)), 'oct': ngon(r, 8, math.pi / 8), 'square': rect(2 * r * 0.9, 2 * r * 1.1)}[prof]
        sweep(f'{g}_shaft', path, pr, 'palBronze', 'beam', B.get('row', 'clouds'), rnd=prof == 'round')
    if d1:
        for k, x in enumerate(B.get('bands', (-1.0, 1.0))):
            z = BC.z + arch * (x / L) ** 2
            sweep(f'{g}_band_{k}', [(x - 0.05, BC.y, z), (x + 0.05, BC.y, z)], ngon(r + 0.04, sides(12)), 'palBronze', 'beam', 'flange')
    for s in (-1, 1): finial(g, B['ends'], s, V(s * L, BC.y, BC.z + arch), arch, lod)
    hang = B.get('hang')
    if hang:
        for k, x in enumerate(B['hang_x']):
            z0 = BC.z + arch * (x / L) ** 2 - r
            tube(f'{g}_strap_{k}', (x, BC.y, z0 + 0.02), (x, BC.y, z0 - 0.12), 0.035, 0.035, 'palBronze', 'beam', n=6)
            if hang == 'bells': bell(f'{g}_bell_{k}', V(x, BC.y, z0 - 0.12), B.get('bell', 0.42), lod)
            else: plate(f'{g}_chime_{k}', [(-0.42, -0.06), (-0.04, 0.0), (0.04, 0.0), (0.46, -0.08), (0.44, -0.2), (0.02, -0.12), (-0.02, -0.12), (-0.4, -0.18)],
                        (x, BC.y, z0 - 0.12), (1, 0, 0), (0, 0, 1), 0.05, 'palBronze', 'beam', 'clouds')
    crest = B.get('crest')
    if crest == 'fin':
        o = [(-1.1, 0.0)] + [(-1.1 + 2.2 * k / 12, 0.2 + 0.1 * math.sin(k * 1.6)) for k in range(13)] + [(1.1, 0.0)]
        plate(f'{g}_fin', o, (0, BC.y, BC.z + r - 0.02), (1, 0, 0), (0, 0, 1), 0.05, 'palBronze', 'beam', 'clouds')
    elif crest == 'teeth':
        for k in range(9 if d1 else 5):
            x = -1.6 + 3.2 * k / ((9 if d1 else 5) - 1)
            if abs(x) < 0.45: continue
            tongue(f'{g}_tooth_{k}', (x, BC.y, BC.z + r - 0.03), (0, 0, 1), (1, 0, 0), 0.34, 0.18, 0.08, (0, 0, 0), 'beam', 'palTin', 'plain')

def bell(name, top, h, lod):
    """a cast bell (yongzhong type, almond section) hanging under the beam; mask band row."""
    z = top.z; x, y = top.x, top.y
    loft(name, [(z - h, y, 0.2 * h / 0.42, 0.13 * h / 0.42, x), (z - h * 0.5, y, 0.17 * h / 0.42, 0.11 * h / 0.42, x), (z, y, 0.13 * h / 0.42, 0.085 * h / 0.42, x)],
         'palBronze', 'beam', 'mask', n_exp=1.7, M=14)
    if lod == 0:
        for k in range(3):
            for s in (-1, 1): spheroid(f'{name}_boss_{k}{s}', (x + s * 0.06 * h / 0.42, y + 0.11 * h / 0.42, z - h * (0.3 + 0.18 * k)), (0.025, 0.025, 0.025), 'palTin', 'beam', segs=(6, 4))

def finial(g, kind, s, E, arch, lod):
    d1 = lod <= 1; x, y, z = E
    if kind == 'dragon':
        pts = [(x, y, z), (x + s * 0.12, y, z + 0.08), (x + s * 0.2, y + 0.02, z + 0.22)]
        sweep(f'{g}_dneck_{s}', pts, [ngon(rr, sides(10)) for rr in (0.16, 0.14, 0.13)], 'palBronze', 'beam', 'lozenge')
        loft(f'{g}_dhead_{s}', [(z + 0.18, y + 0.1, 0.13, 0.2, x + s * 0.24), (z + 0.3, y + 0.12, 0.12, 0.22, x + s * 0.24), (z + 0.38, y + 0.08, 0.08, 0.14, x + s * 0.24)], 'palBronze', 'beam', 'mask', n_exp=2.4, M=12)
        tongue(f'{g}_djaw_{s}', (x + s * 0.24, y + 0.2, z + 0.2), (0, 1, -0.4), (1, 0, 0), 0.22, 0.16, 0.06, (0, 0, -0.2), 'beam')
        for k in (-1, 1): tongue(f'{g}_dhorn_{s}{k}', (x + s * 0.24 + k * 0.06, y + 0.02, z + 0.36), (k * 0.3, -0.6, 1), (1, 0, 0), 0.3, 0.07, 0.05, (0, -0.4, 0), 'beam')
        if d1: spheroid(f'{g}_deye_{s}', (x + s * 0.3, y + 0.22, z + 0.3), (0.04, 0.04, 0.04), 'palTin', 'beam', segs=(6, 4))
    elif kind == 'ring':
        sweep(f'{g}_cap_{s}', [(x, y, z), (x + s * 0.08, y, z)], ngon(BEAM_R + 0.05, sides(12)), 'palBronze', 'beam', 'flange')
        torus(f'{g}_ring_{s}', (x + s * 0.22, y, z), (0, 1, 0), 0.15, 0.05, 'palBronze', 'beam', n=14, m=6)
    elif kind == 'spade':
        plate(f'{g}_spade_{s}', [(0, -0.14), (0.26, -0.4), (0.34, -0.38), (0.34, 0.38), (0.26, 0.4), (0, 0.14)], (x, y, z), (s, 0, 0), (0, 0, 1), 0.07, 'palBronze', 'beam', 'mask')
    elif kind == 'scroll':
        pts = [(x + s * (0.12 + 0.18 * math.sin(a)), y, z + 0.18 - 0.18 * math.cos(a) * (1 - a / 9)) for a in [k * 0.6 for k in range(11 if d1 else 6)]]
        sweep(f'{g}_scroll_{s}', [(x, y, z)] + pts, ngon(0.08, sides(8)), 'palBronze', 'beam', 'flange')
    elif kind == 'tiger':
        spheroid(f'{g}_thead_{s}', (x + s * 0.18, y + 0.04, z - 0.04), (0.2, 0.22, 0.2), 'palBronze', 'beam', 'mask', segs=(12, 7))
        spheroid(f'{g}_tmuz_{s}', (x + s * 0.2, y + 0.22, z - 0.1), (0.11, 0.09, 0.08), 'palBronze', 'beam', segs=(8, 5))
        for k in (-1, 1): tongue(f'{g}_tear_{s}{k}', (x + s * 0.18 + k * 0.1, y, z + 0.12), (k * 0.4, -0.2, 1), (0, 1, 0), 0.14, 0.09, 0.04, (0, 0, 0), 'beam')
        if d1:
            for k in (-1, 1): spheroid(f'{g}_teye_{s}{k}', (x + s * 0.18 + k * 0.08, y + 0.2, z + 0.02), (0.035, 0.03, 0.03), 'palTin', 'beam', segs=(6, 4))
    elif kind == 'bird':
        pts = [(x, y, z), (x + s * 0.12, y, z + 0.12), (x + s * 0.14, y + 0.02, z + 0.34), (x + s * 0.1, y + 0.06, z + 0.5)]
        sweep(f'{g}_bneck_{s}', pts, [ngon(rr, sides(8)) for rr in (0.12, 0.08, 0.06, 0.06)], 'palBronze', 'beam', 'flange')
        spheroid(f'{g}_bhead_{s}', (x + s * 0.1, y + 0.08, z + 0.55), (0.08, 0.1, 0.08), 'palBronze', 'beam', segs=(8, 5))
        tongue(f'{g}_beak_{s}', (x + s * 0.1, y + 0.16, z + 0.55), (0, 1, -0.2), (1, 0, 0), 0.28, 0.06, 0.05, (0, 0, 0), 'beam', 'palTin', 'plain')
    elif kind == 'knob':
        spheroid(f'{g}_knob_{s}', (x + s * 0.14, y, z), (0.2, 0.2, 0.2), 'palBronze', 'beam', 'mask', segs=(12, 8))
        if d1: sweep(f'{g}_knobring_{s}', [(x - s * 0.02, y, z), (x + s * 0.03, y, z)], ngon(BEAM_R + 0.05, sides(12)), 'palBronze', 'beam', 'flange')
    elif kind == 'mask':
        loft(f'{g}_mblock_{s}', [(z - 0.2, y, 0.16, 0.2, x + s * 0.14), (z + 0.2, y, 0.16, 0.2, x + s * 0.14)], 'palBronze', 'beam', 'mask', n_exp=3.5, M=12)
        for k in (-1, 1): tongue(f'{g}_mhorn_{s}{k}', (x + s * 0.14 + k * 0.1, y + 0.05, z + 0.18), (k * 0.6, 0.2, 1), (0, 1, 0), 0.26, 0.09, 0.05, (k * 0.4, 0, -0.2), 'beam')
        if d1:
            for k in (-1, 1): spheroid(f'{g}_meye_{s}{k}', (x + s * 0.14 + k * 0.07, y + 0.2, z + 0.04), (0.045, 0.03, 0.035), 'palTin', 'beam', segs=(6, 4))
    elif kind == 'flare':
        sweep(f'{g}_flare_{s}', [(x, y, z), (x + s * 0.22, y, z)], [ngon(BEAM_R, sides(12)), ngon(BEAM_R + 0.13, sides(12))], 'palBronze', 'beam', 'flange')

# ---- melted-weapon motifs (high-tin bronze edges, palTin) -------------------------------------------------------------
# Round 3: the fragments read as melted into the cast (research: cast from the conquered states' melted weapons), not hung on it:
# a fused pool of bronze where each fragment enters the body, a drip running down from it (LOD0), long blades slightly bent.
MELT = {'n': 0}
def melt(n, at, bone, r=0.09):
    if Q['lod'] > 1: return
    a = V(*at); MELT['n'] += 1; r *= MELT.get('k', 1.0)
    spheroid(f'{n}_melt', tuple(a), (r, r, r * 0.7), 'palBronze', bone, 'plain', segs=(8, 5))
    if Q['lod'] == 0: tongue(f'{n}_drip', tuple(a + V(0, 0.02, -r * 0.4)), (0, 0.15, -1), (1, 0, 0), r * 2.2, r * 0.9, r * 0.6, (0, 0, 0), bone, 'palBronze', 'plain')

def sword(n, base, d, u, bone, L=1.05, w=0.1):
    d = V(*d).normalized(); b = V(*base)
    sag = V(0, 0, -0.18) if abs(d.z) < 0.9 else V(0.12, 0, 0)
    tongue(f'{n}_blade', tuple(b + d * 0.1), tuple(d), u, L, w, 0.035, tuple(sag), bone, 'palTin', 'plain')
    melt(n, tuple(b), bone, 0.1)
    if Q['lod'] <= 1:
        tube(f'{n}_guard', tuple(b + d * 0.05), tuple(b + d * 0.11), 0.07, 0.07, 'palBronze', bone, 'flange', n=6)
        tube(f'{n}_grip', tuple(b - d * 0.12), tuple(b + d * 0.05), 0.035, 0.03, 'palBronze', bone, n=6)

def spearhead(n, base, d, u, bone, L=0.45, w=0.15):
    d = V(*d).normalized(); b = V(*base)
    tongue(f'{n}_head', tuple(b + d * 0.08), tuple(d), u, L, w, 0.05, (0, 0, -0.06), bone, 'palTin', 'plain')
    melt(n, tuple(b), bone, 0.075)
    if Q['lod'] <= 1: tube(f'{n}_socket', tuple(b - d * 0.05), tuple(b + d * 0.1), 0.04, 0.035, 'palBronze', bone, n=6)

def ge(n, c, along, up, bone, L=0.6, mat='palTin'):
    """dagger-axe (戈) blade with its hooked lower edge (胡): a flat plate."""
    o = [(0, 0.06), (L * 0.75, 0.055), (L, 0.0), (L * 0.75, -0.05), (0.1, -0.05), (0.1, -0.28), (0.04, -0.32), (0, -0.3)]
    plate(f'{n}_ge', o, c, along, up, 0.04, mat, bone)
    melt(n, c, bone, 0.09)

def ji(n, base, d, side, bone, L=0.55):
    """halberd (戟) head: spear tip and a side ge blade."""
    spearhead(n, base, d, side, bone, L)
    dd = V(*d).normalized(); ge(n + 'g', tuple(V(*base) + dd * 0.12), side, tuple(dd), bone, L=0.4)

def prod(n, c, a0, a1, R, e1, e2, bone, r=0.045):
    """a crossbow prod (bow arm) arc, centre c, radius R from angle a0 to a1 in the (e1, e2) plane, tapered ends with nocks."""
    c, e1, e2 = V(*c), V(*e1).normalized(), V(*e2).normalized(); k = 9 if Q['lod'] <= 1 else 5
    pts = [tuple(c + (e1 * math.cos(a0 + (a1 - a0) * j / (k - 1)) + e2 * math.sin(a0 + (a1 - a0) * j / (k - 1))) * R) for j in range(k)]
    rr = [r * (0.6 + 0.4 * math.sin(math.pi * j / (k - 1))) for j in range(k)]
    sweep(n, pts, [ngon(q, sides(8)) for q in rr], 'palTin', bone, 'plain')
    melt(n, pts[len(pts) // 2], bone, 0.1)
    if Q['lod'] == 0:
        for j, p in enumerate((pts[0], pts[-1])): spheroid(f'{n}_nock{j}', p, (0.05, 0.05, 0.05), 'palBronze', bone, 'flange', segs=(6, 4))

def trigger(n, c, bone):
    sweep(f'{n}_lock', [tuple(V(*c) - V(0, 0.04, 0)), tuple(V(*c) + V(0, 0.05, 0))], rect(0.1, 0.14), 'palTin', bone, rnd='flat')
    if Q['lod'] == 0: tongue(f'{n}_trig', tuple(V(*c) + V(0, 0.05, -0.05)), (0, 0.3, -1), (1, 0, 0), 0.12, 0.04, 0.03, (0, 0, 0), bone, 'palTin', 'plain')

def motif(i, g, lod):
    m = MOTIFS[i]; d1 = lod <= 1
    if m == 'prods_chest':
        for k, a in enumerate((-0.55, 0.55)):  # two prods bowed round the chest, crossed in an X
            prod(f'{g}_prod{k}', (0, 0.64 - 0.85, 2.98), math.radians(-44), math.radians(44), 0.85, (0, 1, 0), (math.cos(a), 0, math.sin(a)), 'chest', r=0.07)
        for k, a in enumerate((60, 75, 90, 105, 120) if d1 else (75, 105)):
            p, nrm = surf(TORSO_LO, 2.35, a, 0.04, 2.4); trigger(f'{g}_trig{k}', tuple(p), 'pelvis')
    elif m == 'prods_shoulder':
        for s in (-1, 1):
            side = 'L' if s > 0 else 'R'; c = SHOULDER[s] + V(s * 0.04, 0, 0.02)
            for k, R in enumerate((0.38, 0.47) if d1 else (0.42,)):
                prod(f'{g}_sprod{s}{k}', tuple(c), math.radians(-10), math.radians(150), R, (s, 0, 0), (0, 0, 1), f'upper_{side}', r=0.05)
        for k, z in enumerate((3.15, 2.95, 2.75) if d1 else (2.95,)):
            p, _ = surf(TORSO_HI, z, 90, 0.03, 2.4); trigger(f'{g}_ctrig{k}', tuple(p), 'chest')
    elif m == 'spear_ruff':  # FIX-A: longer, wider heads splayed up and out (a sunburst collar at play size), bigger melt pools
        nn = 12 if d1 else 8; MELT['k'] = MOTIF_MELT
        for k in range(nn):
            a = 90 + 360 * k / nn
            p, nrm = surf(TORSO_HI, 3.38, a, -0.02, 2.4); d = nrm + V(0, 0, 0.3)
            if abs(math.sin(math.radians(a)) + 1) < 0.2: continue  # straight back: the beam rests there
            spearhead(f'{g}_ruff{k}', tuple(p), tuple(d), (0, 0, 1), 'chest', L=0.95, w=0.22)
        MELT['k'] = 1.0
    elif m == 'spear_bundle':
        for k in range(4 if d1 else 2):
            o = V(0.12 * k - 0.18, 0, 0)
            a = V(0.55, -0.5, 2.5) + o; b = V(-0.78, -0.62, 4.3) + o + V(0, 0, 0.06 * k)
            tube(f'{g}_shaft{k}', tuple(a), tuple(b), 0.045, 0.04, 'palBronze', 'chest', 'plain', n=6)
            spearhead(f'{g}_bhead{k}', tuple(b), tuple((b - a).normalized()), (0, 1, 0), 'chest', L=0.6)
        for k, a in enumerate((70, 90, 110) if d1 else (90,)):
            p, nrm = surf(TORSO_LO, 2.3, a, 0.0, 2.4); spearhead(f'{g}_belt{k}', tuple(p), (0, 0.4, -1), (1, 0, 0), 'pelvis', L=0.34)
    elif m == 'ji_shoulder':
        for s in (-1, 1):
            side = 'L' if s > 0 else 'R'; c = SHOULDER[s] + V(s * 0.22, -0.04, 0.22)
            ji(f'{g}_ji{s}', tuple(c), (s * 0.45, 0, 1), (0, 1, 0), f'upper_{side}', L=0.6)
        p, _ = surf(TORSO_HI, 3.05, 90, 0.0, 2.4); ji(f'{g}_jic', tuple(p + V(0, 0, 0.12)), (0, 0.15, -1), (1, 0, 0), 'chest', L=0.4)
    elif m == 'ji_apron':  # FIX-A: apron heads longer and fanned out, hip halberds raised like wings, bigger melt pools
        MELT['k'] = MOTIF_MELT
        for k, a in enumerate((-30, -15, 0, 15, 30) if d1 else (-20, 0, 20)):
            t = math.radians(a); p, nrm = surf(SKIRT[0], 2.1, 90 + a * 1.2, 0.02, 2.2)
            ji(f'{g}_ap{k}', tuple(p), (math.sin(t) * 0.9, 0.45, -1), (1, 0, 0), 'pelvis', L=1.1)
        for s in (-1, 1):
            p, nrm = surf(TORSO_LO, 2.32, 90 - s * 90, 0.0, 2.4); ji(f'{g}_hip{s}', tuple(p), (s * 0.6, 0.1, 1), (0, 1, 0), 'pelvis', L=1.2)
        MELT['k'] = 1.0
    elif m == 'sword_fan':
        c = V(0, -0.46, 3.25)
        for k in range(7 if d1 else 5):
            a = math.radians(-80 + 160 * k / ((7 if d1 else 5) - 1)); d = V(math.sin(a), -0.2, math.cos(a))
            sword(f'{g}_fan{k}', tuple(c + d * 0.3), tuple(d), (0, 1, 0), 'chest', L=1.45 if abs(a) < 1 else 1.25, w=0.15)
    elif m == 'sword_hem':  # FIX-A: blades longer and wider, splayed out from the hem (a skirt of swords at play size), bigger melt pools
        nn = 11 if d1 else 7; MELT['k'] = MOTIF_MELT; zh = SKIRT[2][-1][0] + 0.1
        for k in range(nn):
            a = 130 + 280 * k / (nn - 1)
            p, nrm = surf(SKIRT[2], zh, a, 0.04, 2.2)
            sword(f'{g}_hem{k}', tuple(p + V(0, 0, 0.08) - nrm * 0.03), tuple(nrm * 0.35 + V(0, 0, -1)), (-nrm.y, nrm.x, 0), 'pelvis', L=0.95, w=0.14)
        MELT['k'] = 1.0
    elif m == 'arrow_scales':  # FIX-A: bigger chest scales and melt pools, and a crest of upright arrowheads fanned on each shoulder
        rows = ((3.22, 9), (3.02, 10), (2.82, 9)) if d1 else ((3.1, 6),)
        for r_i, (z, nn) in enumerate(rows):
            for k in range(nn):
                a = 90 + (k - (nn - 1) / 2) * 13
                p, nrm = surf(TORSO_HI, z, a, -0.01, 2.4)
                tongue(f'{g}_ah{r_i}_{k}', tuple(p + V(0, 0, 0.1)), tuple(nrm * 0.35 + V(0, 0, -1)), tuple(V(-nrm.y, nrm.x, 0)), 0.28, 0.17, 0.05, (0, 0, 0), 'chest', 'palTin', 'plain')
                if k % 3 == 1: melt(f'{g}_ahm{r_i}_{k}', tuple(p + V(0, 0, 0.1)), 'chest', 0.08 * MOTIF_MELT)
        for s in (-1, 1):
            side = 'L' if s > 0 else 'R'
            for k in range(6 if d1 else 3):
                a = math.radians(10 + 30 * k * (4 if d1 else 2) / (6 if d1 else 3)); c = SHOULDER[s] + V(s * 0.04, 0, 0.02); d = V(s * math.cos(a), 0, math.sin(a))
                tongue(f'{g}_sah{s}{k}', tuple(c + d * 0.27), tuple(d + V(0, 0, 0.3)), (0, 1, 0), 0.42, 0.16, 0.05, (0, 0, 0), f'upper_{side}', 'palTin', 'plain')
            melt(f'{g}_sahm{s}', tuple(SHOULDER[s] + V(s * 0.2, 0, 0.22)), f'upper_{side}', 0.09 * MOTIF_MELT)
    elif m == 'quiver':
        a, b = V(-0.45, -0.52, 2.5), V(0.5, -0.6, 3.6)
        tube(f'{g}_quiver', tuple(a), tuple(b), 0.13, 0.16, 'palBronze', 'chest', 'lozenge', n=10)
        melt(f'{g}_qm0', tuple(a + (b - a) * 0.15), 'chest', 0.14); melt(f'{g}_qm1', tuple(a + (b - a) * 0.6), 'chest', 0.12)
        for k in range(8 if d1 else 4):
            o = V(math.cos(k * 2.4) * 0.08, math.sin(k * 2.4) * 0.06, 0); d = (b - a).normalized() + V(0.06 * math.cos(k), 0, 0.1 * math.sin(k))
            d = d + V(0.25 * math.cos(k * 2.4), 0, 0); top = b + o + d * (0.85 + 0.08 * (k % 3))
            tube(f'{g}_arrow{k}', tuple(b + o), tuple(top), 0.03, 0.025, 'palBronze', 'chest', n=5)
            tongue(f'{g}_ahd{k}', tuple(top), tuple(d), (1, 0, 0), 0.28, 0.14, 0.06, (0, 0, 0), 'chest', 'palTin', 'plain')
    elif m == 'ge_bracers':
        for s in (-1, 1):
            side = 'L' if s > 0 else 'R'; E, G = ELBOW[s], GRIP[s]; dirv = (G - E).normalized()
            out = V(s, 0, 0); out = (out - dirv * out.dot(dirv)).normalized()
            for k, t in enumerate((0.3, 0.62) if d1 else (0.45,)):
                c = E + (G - E) * t + out * 0.12
                ge(f'{g}_br{s}{k}', tuple(c), tuple(out), tuple(dirv), f'fore_{side}', L=0.6)
    elif m == 'ge_chest':
        p, _ = surf(TORSO_HI, 2.98, 90, 0.03, 2.4)
        ge(f'{g}_bigge', tuple(p + V(-0.5, 0, 0.1)), (1, 0, 0), (0, 0, 1), 'chest', L=1.0)
        for s in (-1, 1):
            side = 'L' if s > 0 else 'R'
            ge(f'{g}_knee{s}', tuple(KNEE[s] + V(s * 0.2, 0.04, 0.05)), (s, 0.3, 0), (0, 0, 1), f'shin_{side}', L=0.42)

# Twelve giants: two per conquered state in conquest order 韩 赵 魏 楚 燕 齐 (230-221 BCE); each state's weapon family is its motif.
# head: kind + face plan (jaw, skull, brow, nose, ears, beard); beam: profile, arch, ends, hangings, crest.
STATES = ['Han 韩', 'Han 韩', 'Zhao 赵', 'Zhao 赵', 'Wei 魏', 'Wei 魏', 'Chu 楚', 'Chu 楚', 'Yan 燕', 'Yan 燕', 'Qi 齐', 'Qi 齐']
HEADS = [dict(kind='topknot', brow='v', beard='mous', jaw=1.05), dict(kind='pointed', brow='flat', beard='long', jaw=0.95, nose=1.2),
         dict(kind='widehat', brow='arch', beard='none', jaw=1.1), dict(kind='horns', brow='heavy', beard='chin', jaw=1.15, skull=1.05),
         dict(kind='plumes', brow='v', beard='full', jaw=1.0), dict(kind='hood', brow='heavy', beard='long', jaw=0.95),
         dict(kind='spikes', brow='v', beard='forked', jaw=1.0), dict(kind='tallcap', brow='flat', beard='long', jaw=0.9, nose=0.9),
         dict(kind='bald', brow='heavy', beard='braid', jaw=1.1, ears=1.4, skull=1.05), dict(kind='helmet', brow='v', beard='mous', jaw=1.05),
         dict(kind='board', brow='arch', beard='chin', jaw=0.95, nose=1.1), dict(kind='twinbuns', brow='flat', beard='forked', jaw=1.1)]
BEAMS = [dict(prof='square', arch=0.22, ends='dragon', row='clouds'), dict(prof='round', ends='ring', hang='chimes', hang_x=(-1.68, 1.68)),
         dict(prof='double', ends='scroll'), dict(prof='round', ends='knob', hang='bells', hang_x=(-1.8, 1.8), bell=0.5),
         dict(prof='oct', arch=0.0, ends='spade', row='lozenge'), dict(prof='square', ends='flare', crest='teeth', row='flange'),
         dict(prof='round', arch=-0.32, ends='knob', row='clouds', bands=(-1.2, -0.6, 0.6, 1.2)), dict(prof='square', ends='tiger', row='mask'),
         dict(prof='oct', arch=0.12, ends='bird', row='clouds'), dict(prof='twist', ends='ring', hang='bells', hang_x=(-1.7, -1.94, 1.7, 1.94), bell=0.26, L=1.76),
         dict(prof='round', arch=0.34, ends='flare', crest='fin', row='lozenge'), dict(prof='square', arch=-0.12, ends='mask', row='clouds', L=1.7)]
MOTIFS = ['prods_chest', 'prods_shoulder', 'spear_ruff', 'spear_bundle', 'ji_shoulder', 'ji_apron', 'sword_fan', 'sword_hem',
          'arrow_scales', 'quiver', 'ge_bracers', 'ge_chest']
MOTIF_WORDS = {'prods_chest': 'crossbow prods crossed on the chest, trigger locks on the belt', 'prods_shoulder': 'crossbow prods arched over the shoulders, trigger locks down the chest',
               'spear_ruff': 'a ruff of spearheads round the neck', 'spear_bundle': 'a bundle of spears across the back, spearheads on the belt',
               'ji_shoulder': 'halberd heads rising from the shoulders', 'ji_apron': 'an apron of halberd heads down the skirt',
               'sword_fan': 'a fan of swords behind the shoulders', 'sword_hem': 'swords hanging round the skirt hem',
               'arrow_scales': 'arrowheads laid like scales on chest and shoulders', 'quiver': 'a quiver of arrows over the shoulder',
               'ge_bracers': 'dagger-axe blades on both forearms', 'ge_chest': 'a great dagger-axe blade across the chest, dagger-axes on the knees'}

# ---- flakes (the dormant patina cracking away in the wake clip) ------------------------------------------------------
FLAKES = [('hi', 3.05, 60), ('hi', 3.1, 118), ('hi', 3.0, 250), ('hi', 3.05, 290), ('hi', 2.75, 90), ('sk0', 2.18, 70), ('sk1', 1.95, 112),
          ('sk2', 1.68, 80), ('sk2', 1.7, 260), ('sk1', 1.94, 0), ('sk1', 1.94, 180), ('sk0', 2.2, 230)]  # FIX-A: skirt tiers end higher
def flake_spec(k):
    w, z, a = FLAKES[k]; secs = {'hi': TORSO_HI, 'sk0': SKIRT[0], 'sk1': SKIRT[1], 'sk2': SKIRT[2]}[w]
    p, nrm = surf(secs, z, a, 0.02, 2.4 if w == 'hi' else 2.2); return p, nrm

def build_flakes():
    rnd = random.Random(7)
    for k in range(len(FLAKES)):
        p, nrm = flake_spec(k); u = V(-nrm.y, nrm.x, 0).normalized(); v = V(0, 0, 1)
        o = [(math.cos(j * math.tau / 7) * rnd.uniform(0.16, 0.28), math.sin(j * math.tau / 7) * rnd.uniform(0.14, 0.26)) for j in range(7)]
        plate(f'flake_{k}', o, tuple(p), tuple(u), tuple(v), 0.03, 'palPatina', f'flake_{k}')

# ---------------------------------------------------------------------------------------------------------------------
def uv_trim(ob, row):
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

def material(name): return bpy.data.materials.get(name) or bpy.data.materials.new(name)

def finish(name, bevel):
    for ob, bone, mat, row, rnd in PARTS:
        uv_trim(ob, row); ob.data.materials.append(material(mat))
        vg = ob.vertex_groups.new(name=bone); vg.add(list(range(len(ob.data.vertices))), 1.0, 'REPLACE')
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
    PARTS.clear(); return ob

def tris(ob): return sum(len(p.vertices) - 2 for p in ob.data.polygons)

def decimate_to(ob, limit):
    t = tris(ob)
    if t <= limit: return
    dm = ob.modifiers.new('dec', 'DECIMATE'); dm.ratio = limit / t * 0.98
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='dec')

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.render.fps = FPS
MESHES = {}  # name -> object
for lod in (0, 1, 2):
    Q['seg'], Q['lod'] = SEG[lod], lod
    build_body(lod); MESHES[f'giant_body_lod{lod}'] = finish(f'giant_body_lod{lod}', lod == 0)
    for i in ONLY:
        g = f'g{i:02d}'; head(i, g, lod); beam(i, g, lod); motif(i, g, lod)
        MESHES[f'giant_{g}_lod{lod}'] = finish(f'giant_{g}_lod{lod}', lod == 0)
Q['seg'], Q['lod'] = 1.0, 0
build_flakes(); MESHES['giant_flakes'] = finish('giant_flakes', False)
# LOD2 cap: the shared body takes 62% of the budget, a giant's own parts the rest (decimated only if over)
print('pre-decimation tris lod1/lod2: body', tris(MESHES['giant_body_lod1']), tris(MESHES['giant_body_lod2']), 'giants', [(tris(MESHES[f'giant_g{i:02d}_lod1']), tris(MESHES[f'giant_g{i:02d}_lod2'])) for i in ONLY])
decimate_to(MESHES['giant_body_lod2'], int(BUDGET[2] * 0.62))
for i in ONLY: decimate_to(MESHES[f'giant_g{i:02d}_lod2'], BUDGET[2] - tris(MESHES['giant_body_lod2']))
decimate_to(MESHES['giant_body_lod1'], int(BUDGET[1] * 0.62))
for i in ONLY: decimate_to(MESHES[f'giant_g{i:02d}_lod1'], BUDGET[1] - tris(MESHES['giant_body_lod1']))

# ---- rig ------------------------------------------------------------------------------------------------------------
BONES = [('root', V(0, 0, 0), V(0, 0, 0.5), None), ('pelvis', V(0, 0, 1.95), V(0, 0, 2.3), 'root'), ('spine', V(0, 0, 2.3), V(0, 0, 2.8), 'pelvis'),
         ('chest', V(0, 0, 2.8), V(0, 0, 3.45), 'spine'), ('head', V(0, 0, HEAD_PIV), V(0, 0.05, 4.3), 'chest'), ('beam', BC, BC + V(0.5, 0, 0), 'chest')]
for s, side in ((-1, 'R'), (1, 'L')):
    BONES += [(f'upper_{side}', SHOULDER[s], ELBOW[s], 'chest'), (f'fore_{side}', ELBOW[s], GRIP[s], f'upper_{side}'),
              (f'thigh_{side}', HIP[s], KNEE[s], 'pelvis'), (f'shin_{side}', KNEE[s], ANKLE[s], f'thigh_{side}'), (f'foot_{side}', ANKLE[s], TOE[s], f'shin_{side}')]
for k in range(len(FLAKES)):
    p, nrm = flake_spec(k); BONES.append((f'flake_{k}', p, p + nrm * 0.15, 'root'))
CONNECT = {'fore_R', 'fore_L', 'shin_R', 'shin_L'}
bpy.ops.object.armature_add(location=(0, 0, 0)); arm = bpy.context.active_object; arm.name = 'giant_rig'
bpy.ops.object.mode_set(mode='EDIT'); eb = arm.data.edit_bones; eb.remove(eb[0])
for n, h, t, p in BONES:
    b = eb.new(n); b.head = PW(*h); b.tail = PW(*t); b.roll = 0
    if p: b.parent = eb[p]; b.use_connect = n in CONNECT
bpy.ops.object.mode_set(mode='OBJECT')
NAMES = [b[0] for b in BONES]; PAR = {b[0]: b[3] for b in BONES}
REST = {n: arm.data.bones[n].matrix_local.copy() for n in NAMES}
RINV = {n: REST[n].inverted() for n in NAMES}
def blen(n): return arm.data.bones[n].length

def R3(pitch=0.0, yaw=0.0, roll=0.0):
    """rotation in rest axes: pitch + = lean forward (top toward the face), yaw + = turn, roll + = lean to the giant's left."""
    r = math.radians; return (Matrix.Rotation(r(yaw), 4, 'Z') @ Matrix.Rotation(r(pitch), 4, 'X') @ Matrix.Rotation(r(roll), 4, 'Y'))
def about(h, M): return Matrix.Translation(h) @ M @ Matrix.Translation(-h)
def rest_head(n): return REST[n].translation.copy()

def solve(ctl):
    """pose matrices (armature space) for one frame from the clip controls."""
    POSE = {}
    def fk(n, D): p = PAR[n]; POSE[n] = (POSE[p] @ RINV[p] @ D @ REST[n]) if p else D @ REST[n]
    def ik(up, lo, T, pole):
        p = PAR[up]; base = POSE[p] @ RINV[p] @ REST[up]; S = base.translation.copy()
        E = two_bone(S, T, blen(up), blen(lo), pole)
        d0 = (base.to_3x3() @ V(0, 1, 0)); Rm = d0.rotation_difference(E - S).to_matrix().to_4x4()
        POSE[up] = about(S, Rm) @ base
        b2 = POSE[up] @ RINV[up] @ REST[lo]; d1 = b2.to_3x3() @ V(0, 1, 0)
        POSE[lo] = about(E, d1.rotation_difference(T - E).to_matrix().to_4x4()) @ b2
    rp = P(*ROOT_PIVOT)
    fk('root', Matrix.Translation(P(*ctl.get('root_off', (0, 0, 0)))) @ about(rp, R3(ctl.get('root_pitch', 0))))
    h = rest_head('pelvis')
    fk('pelvis', Matrix.Translation(P(0, ctl.get('pelvis_f', 0), -ctl.get('pelvis_drop', 0))) @ about(h, R3(ctl.get('pelvis_pitch', 0), ctl.get('pelvis_yaw', 0), ctl.get('pelvis_roll', 0))))
    fk('spine', about(rest_head('spine'), R3(ctl.get('spine_pitch', 0), ctl.get('spine_yaw', 0))))
    fk('chest', about(rest_head('chest'), R3(ctl.get('chest_pitch', 0), ctl.get('chest_yaw', 0), ctl.get('chest_roll', 0))))
    fk('head', about(rest_head('head'), R3(ctl.get('head_pitch', 0), ctl.get('head_yaw', 0))))
    bo = ctl.get('beam_off', (0, 0, 0))
    fk('beam', Matrix.Translation(P(*bo)) @ about(rest_head('beam'), R3(ctl.get('beam_pitch', 0), ctl.get('beam_yaw', 0), ctl.get('beam_roll', 0))))
    Rc = (POSE['chest'] @ RINV['chest']).to_3x3()
    for s, side in ((-1, 'R'), (1, 'L')):
        G = POSE['beam'] @ RINV['beam'] @ P(*GRIP[s])
        ik(f'upper_{side}', f'fore_{side}', G, Rc @ P(*POLE_ARM[s]))
    Rr = (POSE['root'] @ RINV['root'])
    for s, side in ((-1, 'R'), (1, 'L')):
        fo = ctl.get('feet', {}).get(side, (0, 0, 0)); fp = ctl.get('foot_pitch', {}).get(side, 0)
        A = Rr @ P(*(ANKLE[s] + V(*fo)))
        ik(f'thigh_{side}', f'shin_{side}', A, Rr.to_3x3() @ P(s * 0.15, 1, 0))
        POSE[f'foot_{side}'] = Matrix.Translation(A) @ (Rr.to_3x3().to_4x4() @ R3(fp)) @ Matrix.Translation(-P(*ANKLE[s])) @ REST[f'foot_{side}']
    fl = ctl.get('flakes')
    for k in range(len(FLAKES)):
        n = f'flake_{k}'
        if fl: off, axis, ang, sc_ = fl[k]; c = rest_head(n); D = Matrix.Translation(P(*off)) @ about(c, Matrix.Rotation(math.radians(ang), 4, P(*axis).normalized()) @ Matrix.Diagonal((sc_, sc_, sc_, 1)))
        else: D = Matrix.Identity(4)
        fk(n, D)
    return POSE

def basis(POSE, n):
    p = PAR[n]; return (POSE[p] @ RINV[p] @ REST[n]).inverted() @ POSE[n] if p else RINV[n] @ POSE[n]

# ---- clips: control functions of t ----------------------------------------------------------------------------------
def ease(x): x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
def lerp(a, b, k): return a + (b - a) * k
def mix(A, B, k):
    out = {}
    for key in set(A) | set(B):
        a, b = A.get(key, 0), B.get(key, 0)
        if isinstance(a, dict) or isinstance(b, dict): out[key] = {s: tuple(lerp(x, y, k) for x, y in zip((a or {}).get(s, (0, 0, 0)), (b or {}).get(s, (0, 0, 0)))) for s in set(a or {}) | set(b or {})}
        elif isinstance(a, tuple) or isinstance(b, tuple):
            a = a if isinstance(a, tuple) else (0, 0, 0); b = b if isinstance(b, tuple) else (0, 0, 0); out[key] = tuple(lerp(x, y, k) for x, y in zip(a, b))
        else: out[key] = lerp(a, b, k)
    return out

CARRY = {}
# dormant: the beam held up overhead behind the head (a bell stand), head level, feet planted
DORM = {'beam_off': (0, 0.11, 1.02), 'chest_pitch': -3, 'head_pitch': -4}
# slam: windup = beam high overhead, leaning back, up on the chest; hit = folded forward, knees bent, beam crashing down in front
SLAM_UP = {'beam_off': (0, 0.3, 1.1), 'chest_pitch': -8, 'spine_pitch': -4, 'head_pitch': -10}
SLAM_HIT = {'beam_off': (0, 1.6, -0.7), 'beam_pitch': 0, 'chest_pitch': 34, 'spine_pitch': 18, 'pelvis_pitch': 12, 'pelvis_drop': 0.42, 'pelvis_f': -0.1, 'head_pitch': -20}
# sweep: windup = turned 80 deg to the right, beam low on that side; hit = swung across to the left, leaning in
SWEEP_UP = {'pelvis_yaw': -20, 'spine_yaw': -25, 'chest_yaw': -35, 'beam_roll': -14, 'beam_off': (0, 0.0, -0.1), 'chest_roll': 6, 'pelvis_drop': 0.18, 'head_yaw': 25}
SWEEP_HIT = {'pelvis_yaw': 25, 'spine_yaw': 30, 'chest_yaw': 40, 'beam_roll': 12, 'beam_off': (0, 0.05, -0.2), 'chest_pitch': 14, 'chest_roll': -6, 'pelvis_drop': 0.25, 'head_yaw': -20}
HIT = {'chest_pitch': -11, 'spine_pitch': -5, 'head_pitch': -14, 'pelvis_f': -0.12, 'beam_roll': 6, 'chest_roll': 4}

def walk_ctl(t):
    p = (t / WALK_T) % 1.0; ctl = {'feet': {}, 'foot_pitch': {}}
    step = SPEED * WALK_T / 2  # foot travel during one stance (half the cycle)
    for side, ph in (('L', 0.0), ('R', 0.5)):
        q = (p + ph) % 1.0
        if q < 0.5: f = step / 2 - step * (q / 0.5); z = 0.0; fp = 0
        else:
            k = (q - 0.5) / 0.5; f = -step / 2 + step * ease(k); z = 0.32 * math.sin(math.pi * k); fp = -12 * math.sin(math.pi * k)
        ctl['feet'][side] = (0, f, z); ctl['foot_pitch'][side] = fp
    ctl.update({'pelvis_drop': 0.08 + 0.13 * (0.5 + 0.5 * math.cos(4 * math.pi * p)),
                'pelvis_roll': 4 * math.sin(2 * math.pi * p), 'pelvis_yaw': 6 * math.sin(2 * math.pi * p), 'chest_yaw': -8 * math.sin(2 * math.pi * p),
                'chest_pitch': 6, 'head_pitch': -6, 'beam_roll': -3 * math.sin(2 * math.pi * p), 'chest_roll': -2 * math.sin(2 * math.pi * p)})
    return ctl

def flakes_at(t):
    """wake: 0.3-0.9 s the patina cracks (flakes lift 3 cm, jitter), 0.7-1.5 s they fall to the floor tumbling, 1.5-2.0 s they shrink away."""
    rnd = random.Random(11); out = []
    for k in range(len(FLAKES)):
        p, nrm = flake_spec(k); ax = (rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.3)); delay = rnd.uniform(0, 0.2)
        if t < 0.3: out.append(((0, 0, 0), ax, 0, 1)); continue
        if t < 0.7 + delay:
            k1 = (t - 0.3) / (0.4 + delay); j = 2.5 * math.sin(t * 70 + k)
            out.append((tuple(nrm * 0.03 * k1), ax, j * k1, 1)); continue
        u = min(1.0, (t - 0.7 - delay) / 0.6); drop = Wz(p.z) - 0.05
        off = nrm * (0.03 + 0.6 * u) + V(0, 0, -drop * u * u)
        sc_ = 1.0 if t < 1.5 else max(0.01, 1 - (t - 1.5) / 0.45)
        out.append((tuple(off), ax, 2.5 + 140 * u, sc_))
    return out

def wake_ctl(t):
    tremor = 1.6 * math.sin(t * 55) * (1 - ease((t - 0.8) / 0.3)) if t < 1.1 else 0
    c = mix(DORM, CARRY, ease((t - 0.9) / 1.0))
    c['chest_roll'] = c.get('chest_roll', 0) + tremor
    c['head_pitch'] = c.get('head_pitch', 0) + 14 * math.sin(math.pi * min(1, max(0, (t - 0.9) / 1.1)))
    c['chest_pitch'] = c.get('chest_pitch', 0) + 5 * math.sin(math.pi * min(1, max(0, (t - 0.9) / 1.1)))
    c['flakes'] = flakes_at(t); return c

def ease_out(x): x = min(1.0, max(0.0, x)); return 1 - (1 - x) ** 2
def slam_ctl(t):
    if t < SLAM_W: return mix(CARRY, SLAM_UP, ease_out(t / SLAM_W))
    if t < SLAM_W + 0.18: return mix(SLAM_UP, SLAM_HIT, ((t - SLAM_W) / 0.18) ** 2)
    if t < SLAM_W + 0.45: return dict(SLAM_HIT)
    return mix(SLAM_HIT, CARRY, ease((t - SLAM_W - 0.45) / 0.9))

def sweep_ctl(t):
    if t < SWEEP_W: return mix(CARRY, SWEEP_UP, ease_out(t / SWEEP_W))
    if t < SWEEP_W + 0.28: return mix(SWEEP_UP, SWEEP_HIT, ease((t - SWEEP_W) / 0.28))
    if t < SWEEP_W + 0.45: return dict(SWEEP_HIT)
    return mix(SWEEP_HIT, CARRY, ease((t - SWEEP_W - 0.45) / 0.85))

def hit_ctl(t):
    return mix(CARRY, HIT, ease(t / 0.1)) if t < 0.1 else mix(HIT, CARRY, ease((t - 0.1) / 0.4))

FALL_KNEEL = {'pelvis_drop': 0.55, 'chest_pitch': 22, 'spine_pitch': 10, 'head_pitch': 15, 'pelvis_f': -0.15, 'beam_roll': 10}
def fall_ctl(t):
    if t < 0.3: return mix(CARRY, FALL_KNEEL, ease(t / 0.3))
    c = dict(FALL_KNEEL); k = ((t - 0.3) / (FALL_S - 0.3)); c['root_pitch'] = 82 * min(1.0, k * k); c['beam_roll'] = 10 * (1 - k)
    c['head_pitch'] = 15 - 30 * k; return c

def carry_ctl(t):
    b = math.sin(2 * math.pi * t / 2.0); return {'chest_pitch': 1.5 * b, 'beam_off': (0, 0, 0.02 * b), 'head_pitch': -1.0 * b, 'pelvis_drop': 0.02 + 0.015 * b}

CLIPS = [('dormant', 1.0, lambda t: dict(DORM)), ('wake', WAKE_S, wake_ctl), ('carry', 2.0, carry_ctl), ('walk', WALK_T, walk_ctl),
         ('slam', SLAM_W + 1.35, slam_ctl), ('sweep', SWEEP_W + 1.3, sweep_ctl), ('hit', 0.5, hit_ctl), ('fall', FALL_S, fall_ctl)]

# ---- keys -----------------------------------------------------------------------------------------------------------
arm.animation_data_create()
for b in arm.pose.bones: b.rotation_mode = 'QUATERNION'
SAMPLES = {}  # clip -> list of (t, POSE)
for name, dur, fn in CLIPS:
    act = bpy.data.actions.new(name); arm.animation_data.action = act
    nf = round(dur * FPS); frames = list(range(0, nf + 1, KEY_STEP)) + ([nf] if nf % KEY_STEP else [])
    prevq = {}; SAMPLES[name] = []
    for f in frames:
        t = f / FPS; POSE = solve(fn(t)); SAMPLES[name].append((t, POSE))
        for n in NAMES:
            pb = arm.pose.bones[n]; M = basis(POSE, n)
            loc, rot, scl = M.decompose()
            if n in prevq and prevq[n].dot(rot) < 0: rot = -rot
            prevq[n] = rot
            pb.location = loc; pb.rotation_quaternion = rot; pb.scale = scl
            pb.keyframe_insert('location', frame=f + 1); pb.keyframe_insert('rotation_quaternion', frame=f + 1)
            if n.startswith('flake'): pb.keyframe_insert('scale', frame=f + 1)
    tr = arm.animation_data.nla_tracks.new(); tr.name = name; tr.strips.new(name, 1, act)
    arm.animation_data.action = None
for pb in arm.pose.bones: pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)

# ---- gates ----------------------------------------------------------------------------------------------------------
fails = 0; n_checks = 0
def gate(ok, line):
    global fails, n_checks
    n_checks += 1; fails += 0 if ok else 1; print(('PASS ' if ok else 'FAIL ') + line)
def bone_verts(ob):
    names = {vg.index: vg.name for vg in ob.vertex_groups}; out = {}
    for v in ob.data.vertices:
        if v.groups: out.setdefault(names[v.groups[0].group], []).append(v.co.copy())
    return out
BV = {k: bone_verts(o) for k, o in MESHES.items()}
def posed(key, POSE, bones=None):
    pts = []
    for b, vs in BV[key].items():
        if bones and b not in bones: continue
        M = POSE[b] @ RINV[b]; pts += [M @ v for v in vs]
    return pts
def design(v): return V(v.x, -v.y, v.z)
def pose_at(clip, t): return min(SAMPLES[clip], key=lambda s: abs(s[0] - t))[1]
REST_POSE = solve({})

for i in ONLY:
    g = f'g{i:02d}'
    for lod in (0, 1, 2):
        tt = tris(MESHES[f'giant_body_lod{lod}']) + tris(MESHES[f'giant_{g}_lod{lod}'])
        gate(tt <= BUDGET[lod], f'{g} lod{lod} tris {tt} (budget {BUDGET[lod]})')
    pts = [design(p) for p in posed('giant_body_lod0', REST_POSE) + posed(f'giant_{g}_lod0', REST_POSE)]
    top = max(p.z for p in pts); wid = max(abs(p.x) for p in pts) * 2
    gate(H_MIN <= top <= H_CARRY_MAX, f'{g} carried height {top:.2f} m ({H_MIN}-{H_CARRY_MAX}; health bar at 5.4)')
    gate(wid <= W_MAX, f'{g} width {wid:.2f} m (max {W_MAX}; giants stand 5 m apart)')
    low = [p for p in pts if p.z < Z_BODY]; rr = max(math.hypot(p.x, p.y) for p in low)
    gate(rr <= R_BODY, f'{g} body radius below {Z_BODY} m: {rr:.2f} (max {R_BODY}; CONFIG giant.r 1.1)')
    dp = [design(p) for p in posed('giant_body_lod0', pose_at('dormant', 0)) + posed(f'giant_{g}_lod0', pose_at('dormant', 0))]
    gate(max(p.z for p in dp) <= H_DORM_MAX, f'{g} dormant height {max(p.z for p in dp):.2f} m (max {H_DORM_MAX}, beam overhead)')
    fp = [design(p) for p in posed('giant_body_lod0', SAMPLES['fall'][-1][1]) + posed(f'giant_{g}_lod0', SAMPLES['fall'][-1][1])]
    if os.environ.get('DEBUG_FALL'):
        for key in ('giant_body_lod0', f'giant_{g}_lod0'):
            for b in BV[key]:
                zz = [design(p).z for p in posed(key, SAMPLES['fall'][-1][1], {b})]
                print('  fall', g, key[-9:], b, f'{min(zz):.2f} {max(zz):.2f}')
    gate(max(p.z for p in fp) <= 1.7 and min(p.z for p in fp) >= -0.25, f'{g} fall end lies down: top {max(p.z for p in fp):.2f} m (max 1.7), lowest {min(p.z for p in fp):.2f} (min -0.25)')
for lod in (0, 1, 2):
    for key in [f'giant_body_lod{lod}'] + [f'giant_g{i:02d}_lod{lod}' for i in ONLY]:
        ob = MESHES[key]
        if not all(len(v.groups) == 1 for v in ob.data.vertices): gate(False, f'{key} every vertex on exactly one bone')
gate(all(all(len(v.groups) == 1 for v in o.data.vertices) for o in MESHES.values()), 'every vertex of every mesh on exactly one bone (rigid)')
# hands on the beam at every sampled frame of every clip
worst = (0, '')
for clip, ss in SAMPLES.items():
    for t, POSE in ss:
        for s, side in ((-1, 'R'), (1, 'L')):
            G = POSE['beam'] @ RINV['beam'] @ P(*GRIP[s]); F = POSE[f'fore_{side}'] @ V(0, blen(f'fore_{side}'), 0)
            d = (G - F).length
            if d > worst[0]: worst = (d, f'{clip} t {t:.2f} {side}')
gate(worst[0] <= GRIP_TOL, f'hands on the beam: worst {worst[0]:.3f} m at {worst[1]} (max {GRIP_TOL})')
# feet planted outside walk and fall; walk stance speed = game speed
worst = 0
for clip in ('dormant', 'carry', 'slam', 'sweep', 'hit', 'wake'):
    for t, POSE in SAMPLES[clip]:
        for s, side in ((-1, 'R'), (1, 'L')):
            A = POSE[f'shin_{side}'] @ V(0, blen(f'shin_{side}'), 0); worst = max(worst, (A - P(*ANKLE[s])).length)
gate(worst <= 0.05, f'feet planted (ankle drift {worst:.3f} m, max 0.05) in dormant, carry, slam, sweep, hit, wake')
ss = SAMPLES['walk']; speeds = []
for (t0, A0), (t1, A1) in zip(ss, ss[1:]):
    for side in ('L', 'R'):
        a0 = A0[f'shin_{side}'] @ V(0, blen(f'shin_{side}'), 0); a1 = A1[f'shin_{side}'] @ V(0, blen(f'shin_{side}'), 0)
        if a0.z < 0.25 and a1.z < 0.25: speeds.append((design(a0).y - design(a1).y) / (t1 - t0))
sp = sum(speeds) / len(speeds) if speeds else 0.0
gate(abs(sp - SPEED) <= 0.1 * SPEED, f'walk stance foot speed {sp:.2f} m/s (game speed {SPEED}, +-10%)')
worst = 0
for t, POSE in ss:
    c = walk_ctl(t)
    for s_, side in ((-1, 'R'), (1, 'L')):
        A = POSE[f'shin_{side}'] @ V(0, blen(f'shin_{side}'), 0); worst = max(worst, (A - P(*(ANKLE[s_] + V(*c['feet'][side])))).length)
gate(worst <= 0.05, f'walk feet reach their gait targets (worst {worst:.3f} m, max 0.05)')
# tells: the beam (its centre) moves early and far before the hit
def bc(clip, t): return design(pose_at(clip, t)['beam'] @ RINV['beam'] @ P(*BC))
b0, b4, bw = bc('slam', 0), bc('slam', 0.4), bc('slam', SLAM_W)
bh = min((bc('slam', t) for t, _ in SAMPLES['slam'] if t >= SLAM_W), key=lambda v: v.z)
gate((b4 - b0).length >= TELL_EARLY and bw.z - b0.z >= SLAM_RISE, f'slam tell: beam moved {(b4 - b0).length:.2f} m by 0.4 s (min {TELL_EARLY}), risen {bw.z - b0.z:.2f} m by the {SLAM_W} s windup (min {SLAM_RISE})')
gate(bw.z - bh.z >= 2.0 and bh.y >= 0.8, f'slam hit: beam drops {bw.z - bh.z:.2f} m (min 2.0) to {bh.z:.2f} m, {bh.y:.2f} m in front (min 0.8)')
def beam_dir(clip, t): M = pose_at(clip, t)['beam'] @ RINV['beam']; d = design(M.to_3x3() @ V(1, 0, 0)); return math.degrees(math.atan2(d.y, d.x))
y0, y4, yw = beam_dir('sweep', 0), beam_dir('sweep', 0.4), beam_dir('sweep', SWEEP_W)
yh = beam_dir('sweep', SWEEP_W + 0.28)
e0, e4 = bc('sweep', 0), bc('sweep', 0.4)
L_end = 1.9
gate(abs(y4 - y0) * math.pi / 180 * L_end >= TELL_EARLY and abs(yw - y0) >= SWEEP_ARC, f'sweep tell: beam end moved {abs(y4 - y0) * math.pi / 180 * L_end:.2f} m by 0.4 s (min {TELL_EARLY}), turned {abs(yw - y0):.0f} deg by the {SWEEP_W} s windup (min {SWEEP_ARC})')
gate(abs(yh - yw) >= 2 * SWEEP_ARC, f'sweep swing {abs(yh - yw):.0f} deg in 0.28 s (min {2 * SWEEP_ARC})')
h0, h1 = design(pose_at('hit', 0)['chest'] @ V(0, blen('chest'), 0)), design(pose_at('hit', 0.1)['chest'] @ V(0, blen('chest'), 0))
gate((h1 - h0).length >= 0.15, f'hit react: chest top moves {(h1 - h0).length:.2f} m (min 0.15)')
fl_end = [design(pose_at('wake', 1.5)[f'flake_{k}'].translation) for k in range(len(FLAKES))]
gate(max(p.z for p in fl_end) <= 0.3, f'wake: every patina flake on the floor by 1.5 s (highest {max(p.z for p in fl_end):.2f} m, max 0.3)')
d_end = (design(pose_at('wake', WAKE_S)['beam'].translation) - design(REST_POSE['beam'].translation)).length
gate(d_end <= 0.02, f'wake ends in the carried pose (beam {d_end:.3f} m from it; walk, slam and sweep start there)')
# Blender evaluates our keys the same way (one clip, all other tracks muted)
for tr in arm.animation_data.nla_tracks: tr.mute = tr.name != 'slam'
sc.frame_set(1 + round(0.6 * FPS)); bpy.context.view_layer.update()
mine = pose_at('slam', 0.6); err = max((arm.pose.bones[n].matrix.translation - mine[n].translation).length for n in ('beam', 'fore_L', 'head', 'shin_R'))
gate(err <= 0.01, f'Blender pose matches the solver at slam 0.6 s ({err * 1000:.1f} mm, max 10)')
for tr in arm.animation_data.nla_tracks: tr.mute = False
sc.frame_set(1)
print(f'bones {len(NAMES)}, clips {", ".join(c[0] for c in CLIPS)}')
print(f'{n_checks - fails} of {n_checks} pass')
GATE_LOG = os.environ.get('GATE_LOG')

# ---- export ---------------------------------------------------------------------------------------------------------
if not os.environ.get('GATES_ONLY'):
    for key, ob in MESHES.items():
        ob.parent = arm; mod = ob.modifiers.new('arm', 'ARMATURE'); mod.object = arm
    arm['giants'] = json.dumps([{'i': i, 'state': STATES[i], 'head': HEADS[i]['kind'], 'beam': BEAMS[i]['ends'] + '/' + BEAMS[i].get('prof', 'round'), 'motif': MOTIFS[i]} for i in ONLY])
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_animations=True, export_nla_strips=True, export_materials='EXPORT',
                              export_image_format='NONE', export_extras=True)
    print('wrote', OUT, os.path.getsize(OUT), 'bytes')
