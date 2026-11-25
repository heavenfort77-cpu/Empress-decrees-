# Empress Kaymuse, seated (PIECES round 5; owner 25 Nov 13:08, 13:1x, 14:13 "kaymuse is female" and 18:42 "she must look feminine"):
# a woman, an empress, in black Qin court robes with a phoenix crown whose bead strings veil her eyes. Replaces the two cream boxes on
# the throne. Round 5 changes the shapes (rounds 3-4 still read blocky and neutral to the owner):
#   face     a soft oval, a small jaw, full cinnabar lips, cheeks, a slim neck, warm fair skin; the chin is raised 8 degrees (haughty).
#            The veil is lifted: twelve short bead strings hang from a gold diadem to the nose bridge, so the eyes are veiled and the
#            lower half of the face shows from the front and from the game pitch.
#   hair     a tall coiled bun (three coils and a knot), two long hair lengths falling over the shoulders to the chest (smooth tapered
#            forms), a gold hairpin each side with hanging tassels (步摇) that sway.
#   body     slim shoulders, a narrow high waist under a wide cinnabar sash, a bust-waist-hip curve under a crossed collar; the robe
#            flows from the waist into a wide soft skirt with curved pleats; long sleeves with round (12-sided) sections, their ends
#            hanging off the armrest and over the lap in a rounded drape.
#   posture  upright; her right hand rests on her armrest (凭几) with joined slender fingers, her left lies on her lap holding a small
#            jade and gold tally.
#   colour   the black court robe stays; a cinnabar inner robe shows at the collar, cuffs and hem, a white under-layer edges it, gold
#            phoenix-tail lines are embroidered (modelled, thin) on the chest and sleeves; the crown is a light gold phoenix on a diadem
#            (no board).
# Own design from the research rule list (Qin black = court dress; cinnabar = the one warm accent; gold inlay lines). No face detail
# is painted: forms only. Scale: about 1.3 x a suit (guess, lead to judge). Model origin = the middle of her seat place; extras 'seat'
# = where that sits in throne_dais.glb (three.js x, y, z). Clip 'idle' (4 s loop): slow breathing, the bead strings and the hairpin
# tassels sway. LOD0 skinned (rigid parts), LOD1 / LOD2 static. Usage: python pieces_kaymuse.py OUT.glb   (inside Blender's Python)
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_kit as K
import pieces_kit as PK
from prop_kit import lathe, spheroid, sweep, prism, torus, loft, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/kaymuse.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (task: about 6-10k LOD0 plus a low LOD) and the LOD0 floor.
BUDGET = (10000, 2600, 900)
TRIS_MIN = 5000
# Throne seat in throne_dais.glb (measured from the GLB): top y, half width x, front z and back z (three.js axes), m.
SEAT_Y, SEAT_HW, SEAT_Z = 2.16, 2.03, (-1.75, 0.07)
# Lower robe sections (z, centre f, half width, half depth), m: the wide soft hem, knees, hips, waist. Roundness (2 = ellipse).
SKIRT = [(0.0, 0.10, 1.10, 0.70), (0.05, 0.10, 1.12, 0.71), (0.16, 0.09, 0.95, 0.62), (0.30, 0.07, 0.72, 0.50), (0.44, 0.04, 0.50, 0.37), (0.56, 0.01, 0.36, 0.27), (0.64, 0.0, 0.25, 0.19)]
SKIRT_N, TORSO_N = 2.4, 2.2
# Upper body sections (z, centre f, half width, half depth), m: waist, ribs, bust, upper chest, slim shoulders, neck root.
TORSO = [(0.62, 0.0, 0.19, 0.15), (0.80, 0.0, 0.215, 0.17), (0.96, 0.035, 0.25, 0.20), (1.06, 0.01, 0.26, 0.17), (1.14, -0.01, 0.27, 0.15), (1.20, -0.02, 0.10, 0.09)]
# Section indices in TORSO of the waist, bust and shoulders, and the SKIRT index of the hips (the curve gate).
I_WAIST, I_BUST, I_SHOULDER, I_HIP = 0, 2, 4, 5
# Sash at the waist: z range, how far it stands proud m.
SASH_Z, SASH_OUT = (0.60, 0.77), 0.02
# White under-layer at the floor: how far it stands out past the robe m, height m. Cinnabar inner robe band above it: top z, proud m.
UNDER_OUT, UNDER_H, INNER_Z, INNER_OUT = 0.06, 0.03, 0.115, 0.03
# Curved pleats down the skirt: count each side of the front, degrees between them, swirl deg (how far a pleat curves sideways on its way down).
PLEATS, PLEAT_DEG, PLEAT_SWIRL = 7, 13, 9
# Sleeve sections: sides (round forms: at least 10) and depth over height.
SLEEVE_N, SLEEVE_FLAT = 12, 0.75
# Her right arm (design -x) lies on the armrest: centre line (x outward, f, z) and half heights m; then the sleeve end hanging off the armrest.
ARM_REST, ARM_REST_R = [(0.27, -0.02, 1.10), (0.42, 0.0, 0.92), (0.62, 0.04, 0.68), (0.80, 0.20, 0.56), (0.90, 0.36, 0.53)], [0.10, 0.15, 0.21, 0.19, 0.15]
TAIL_REST, TAIL_REST_R = [(0.72, 0.10, 0.50), (0.98, 0.10, 0.34), (1.10, 0.06, 0.13), (1.30, -0.02, 0.055)], [0.17, 0.19, 0.125, 0.045]
# Her left arm (design +x) comes to her lap: centre line and half heights; then the sleeve end draped over her knee.
ARM_LAP, ARM_LAP_R = [(0.27, -0.02, 1.10), (0.40, 0.02, 0.92), (0.46, 0.12, 0.72), (0.30, 0.28, 0.62), (0.14, 0.36, 0.61)], [0.10, 0.15, 0.19, 0.16, 0.12]
TAIL_LAP, TAIL_LAP_R = [(0.36, 0.26, 0.56), (0.50, 0.44, 0.36), (0.56, 0.60, 0.15), (0.66, 0.72, 0.055)], [0.15, 0.17, 0.12, 0.045]
# Gold border piping radius m. CHEST_LINES: gold phoenix-tail lines embroidered on the chest.
PIPE_R, CHEST_LINES = 0.028, True
# Armrest (凭几): x of the bar, its f range, top height, m. Hands: palm centres (x on its own side, f, z), finger length m. TALLY: she holds one.
REST_X, REST_F, REST_Z = 0.90, (-0.38, 0.52), 0.42
HAND_REST, HAND_LAP, FINGER, TALLY = (0.90, 0.47, 0.455), (0.04, 0.40, 0.535), 0.115, True
# Head centre and radii (x, f, z), m (a soft oval); heights of the lash line, nose tip, lips and chin, m; the lips' material.
HEAD_C, HEAD_R = (0.0, 0.02, 1.43), (0.095, 0.11, 0.135)
EYE_Z, NOSE_Z, LIPS_Z, CHIN_Z, LIPS_MAT = 1.452, 1.395, 1.344, 1.285, 'palCinnabar'
# The head is raised about this point by this many degrees (negative = chin up).
HEAD_PIVOT, HEAD_TILT = (0.0, 0.0, 1.27), -8
# Diadem the bead strings hang from: radius round the head axis m, height m. Strings: count, degrees between them, length m (to the nose
# bridge), beads per string, bead radius, cord width m.
DIADEM_R, DIADEM_Z, STRINGS, STR_DEG, STR_LEN, STR_BEADS, BEAD_R, CORD_W = 0.125, 1.535, 12, 11, 0.10, 2, 0.006, 0.005
# Hair: HAIR_FALL = two long lengths over the shoulders to the chest (path x outward, f, z; radii) m. Bun coils (z, ring radius, tube radius) m.
HAIR_FALL = True
HAIR_PATH, HAIR_R = [(0.10, 0.02, 1.40), (0.125, 0.09, 1.27), (0.15, 0.19, 1.12), (0.14, 0.235, 0.98), (0.12, 0.25, 0.88)], [0.035, 0.04, 0.038, 0.03, 0.012]
BUN = [(1.60, 0.085, 0.04), (1.67, 0.07, 0.036), (1.735, 0.052, 0.03)]
# Hairpins (步摇): tip (x outward, f, z) m, tassel strands, tassel length m.
PIN_TIP, TASSELS, TASSEL_LEN = (0.21, -0.09, 1.70), 3, 0.14
# Idle clip: seconds, bead sway deg, tassel sway deg, breathing rise m and lean deg, min bead travel m.
IDLE_S, SWAY, SWAY_T, BREATH, SWAY_MIN = 4.0, 7.0, 8.0, (0.004, 0.5), 0.004
ROBE, CIN, GOLD, JADE, BLACK, LAC, BR, SKIN, WHITE = 'kmRobe', 'palCinnabar', 'palGold', 'kmJade', 'pcBlack', 'palLacquerPlain', 'palBronze', 'kmSkin', 'kmWhite'
# Sides: her right (design -x) rests on the armrest, her left (design +x) lies on her lap.
S_REST, S_LAP = -1, 1
PK.mutate(globals())


def lerp_secs(secs, z):
    for a, b in zip(secs, secs[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return [a[i] + (b[i] - a[i]) * k for i in range(4)]
    return list(secs[-1] if z > secs[-1][0] else secs[0])

def robe_pt(secs, a_deg, z, out=0.0, n=None):
    """a point on the robe's surface: a_deg from the front (positive toward +x), height z, pushed outward by out."""
    _, cf, hw, hd = lerp_secs(secs, z); a = math.radians(a_deg); s, c = math.sin(a), math.cos(a); e = 2 / (n or SKIRT_N)
    return ((hw + out) * math.copysign(abs(s) ** e, s), cf + (hd + out) * math.copysign(abs(c) ** e, c), z)

def unit(v):
    L = math.sqrt(sum(c * c for c in v)); return [c / L for c in v]

def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

def raised(p):
    """a head point after the chin is raised (the same turn pieces_kit.tilt gives the head's parts)."""
    a = math.radians(HEAD_TILT); f, z = p[1] - HEAD_PIVOT[1], p[2] - HEAD_PIVOT[2]
    return (p[0], HEAD_PIVOT[1] + f * math.cos(a) + z * math.sin(a), HEAD_PIVOT[2] - f * math.sin(a) + z * math.cos(a))

def head_f(z, x=0.0):
    """f of the head's front surface at height z and offset x (before the chin is raised)."""
    k = 1 - ((z - HEAD_C[2]) / HEAD_R[2]) ** 2 - (x / HEAD_R[0]) ** 2; return HEAD_C[1] + HEAD_R[1] * math.sqrt(max(k, 0.0))

def string_tops():
    """(x, f, z) where each bead string hangs from the diadem's front, after the chin is raised."""
    out = []
    for k in range(STRINGS):
        ph = math.radians((k - (STRINGS - 1) / 2) * STR_DEG)
        out.append(raised((DIADEM_R * math.sin(ph) * HEAD_R[0] / HEAD_R[1], HEAD_C[1] + DIADEM_R * math.cos(ph), DIADEM_Z - 0.012)))
    return out

def pin_tip(s): return raised((s * PIN_TIP[0], PIN_TIP[1], PIN_TIP[2]))

def frames(path, radii, s):
    """per sleeve point: (centre, up unit vector in the hanging plane, outward unit vector across the cloth, half height)."""
    pts = [(s * x, f, z) for x, f, z in path]; out = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]; t = unit([b[j] - a[j] for j in range(3)])
        u = unit([-t[2] * t[0], -t[2] * t[1], 1 - t[2] * t[2] + 1e-6]); v = unit(cross(t, u))
        if v[0] * s + v[1] < 0: v = [-c for c in v]
        out.append((p, u, v, r))
    return out

def on_sleeve(fr, i, k, lift=0.0):
    """a point on a sleeve's outer face: at path index i (may be fractional), k = -1 lower edge .. 1 upper edge."""
    i0 = min(int(i), len(fr) - 2); w = i - i0; (p, u, v, r), (q, u2, v2, r2) = fr[i0], fr[i0 + 1]
    P_ = [p[j] + (q[j] - p[j]) * w for j in range(3)]; U = unit([u[j] + (u2[j] - u[j]) * w for j in range(3)]); V = unit([v[j] + (v2[j] - v[j]) * w for j in range(3)]); R = r + (r2 - r) * w
    d = SLEEVE_FLAT * R * math.sqrt(max(1 - k * k, 0.0)) + lift
    return tuple(P_[j] + U[j] * k * R + V[j] * d for j in range(3))

def band(name, path, w, t, mat, out):
    """a smooth flat border swept over the upper body along path [(a_deg, z)]."""
    pts = [robe_pt(TORSO, a, z, out, TORSO_N) for a, z in path]
    sweep(name, pts, [w / 2] * len(pts), mat, 'plain', n=6, flat=(1.0, max(t / w * 1.4, 0.3)), side=(1, 0, 0))

def hand(name, c, d, lv, detail, ts=1):
    """a slim hand: palm at c, four joined slender fingers along unit direction d curling down at the tips, a thumb beside them (ts = which side)."""
    side = unit(cross(d, (0, 0, 1)))
    spheroid(f'{name}_palm', c, (0.04, 0.055, 0.018), SKIN, 'plain', sg=(8, 5))
    if lv == 2: return
    for q, o in enumerate((-0.024, -0.008, 0.008, 0.024)):
        L = FINGER * (1.0 - 0.1 * abs(q - 1.4)); b0 = [c[j] + side[j] * o + d[j] * 0.036 for j in range(3)]
        k1 = [b0[j] + d[j] * L * 0.55 for j in range(3)]; k1[2] -= 0.004; k2 = [b0[j] + d[j] * L * 0.95 for j in range(3)]; k2[2] -= 0.04
        if detail:
            prism(f'{name}_f{q}a', ngon(0.011, 4, math.pi / 4), tuple(b0), tuple(k1), SKIN, 'plain', scale_b=0.9, rnd=True, up=(0, 0, 1))
            prism(f'{name}_f{q}b', ngon(0.01, 4, math.pi / 4), tuple(k1), tuple(k2), SKIN, 'plain', scale_b=0.6, rnd=True, up=(0, 0, 1))
        else: prism(f'{name}_f{q}', ngon(0.011, 4, math.pi / 4), tuple(b0), tuple(k2), SKIN, 'plain', scale_b=0.6, rnd=True, up=(0, 0, 1))
    t0 = [c[j] + side[j] * 0.036 * ts for j in range(3)]; t1 = [c[j] + side[j] * 0.045 * ts + d[j] * 0.06 for j in range(3)]; t1[2] -= 0.004
    prism(f'{name}_thumb', ngon(0.012, 4, math.pi / 4), tuple(t0), tuple(t1), SKIN, 'plain', scale_b=0.7, rnd=True, up=(0, 0, 1))


def build(detail):
    lv = PK.LEVEL['n']; PK.bone('root')
    # lower robe: a white under-layer and the cinnabar inner robe showing at the floor, a gold line, the black skirt flowing wide from the waist
    hw0, hd0 = SKIRT[1][2], SKIRT[1][3]
    loft('under', [(0.0, 0.10, hw0 + INNER_OUT + UNDER_OUT, hd0 + INNER_OUT + UNDER_OUT, 0.0), (UNDER_H, 0.10, hw0 + INNER_OUT + UNDER_OUT, hd0 + INNER_OUT + UNDER_OUT, 0.0)], WHITE, 'plain', n_exp=SKIRT_N, M=32)
    loft('skirt', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in SKIRT], ROBE, 'tile2', n_exp=SKIRT_N, M=32)
    (_, c1, w1, d1) = lerp_secs(SKIRT, INNER_Z)
    loft('inner_hem', [(UNDER_H, 0.10, hw0 + INNER_OUT, hd0 + INNER_OUT, 0.0), (INNER_Z, c1, w1 + INNER_OUT * 0.6, d1 + INNER_OUT * 0.6, 0.0)], CIN, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    (_, c2, w2, d2) = lerp_secs(SKIRT, INNER_Z + 0.025)
    loft('hem_gold', [(INNER_Z, c1, w1 + INNER_OUT * 0.6 + 0.004, d1 + INNER_OUT * 0.6 + 0.004, 0.0), (INNER_Z + 0.025, c2, w2 + 0.012, d2 + 0.012, 0.0)], GOLD, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    zs = (0.60, 0.46, 0.32, 0.20, 0.145) if detail else (0.60, 0.40, 0.145)
    for i in range(-PLEATS, PLEATS + 1):  # curved pleats: soft rounded folds swirling down from the waist
        if i == 0 or (lv >= 1 and i % 2): continue
        pts = [robe_pt(SKIRT, i * PLEAT_DEG * (0.7 + 0.3 * (0.60 - z) / 0.455) + math.copysign(PLEAT_SWIRL, i) * math.sin(math.pi * (0.60 - z) / 0.455), z, -0.004) for z in zs]
        sweep(f'pleat_{i}', pts, [0.022 + 0.05 * (0.60 - z) for z in zs], ROBE, 'tile2', n=5 if detail else 4, flat=(1.0, 0.7))
    # the wide cinnabar sash at the high waist: gold edges, a gold knot, two white ribbons with gold ends falling down the front
    (_, c0, w0, d0), (_, c1, w1, d1) = lerp_secs(TORSO, SASH_Z[0]), lerp_secs(TORSO, SASH_Z[1])
    loft('sash', [(SASH_Z[0], c0, w0 + SASH_OUT, d0 + SASH_OUT, 0.0), (SASH_Z[1], c1, w1 + SASH_OUT, d1 + SASH_OUT, 0.0)], CIN, 'plain', n_exp=TORSO_N, M=24, cap=False)
    for q, z in enumerate(SASH_Z):
        _, c, w, d = lerp_secs(TORSO, z); zz = z if q == 0 else z - 0.016
        loft(f'sash_edge_{q}', [(zz, c, w + SASH_OUT + 0.007, d + SASH_OUT + 0.007, 0.0), (zz + 0.016, c, w + SASH_OUT + 0.007, d + SASH_OUT + 0.007, 0.0)], GOLD, 'plain', n_exp=TORSO_N, M=24, cap=False)
    kf = lerp_secs(TORSO, 0.685)[3] + SASH_OUT
    spheroid('knot', (0.0, kf + 0.012, 0.685), (0.05, 0.03, 0.045), GOLD, 'plain', sg=(8, 5))
    if lv < 2:
        for s in (-1, 1):
            rp = [robe_pt(SKIRT, s * (5 + 3 * j), z, 0.014) for j, z in enumerate((0.60, 0.48, 0.36, 0.27))]
            sweep(f'ribbon_{s}', [(kf * 0 + s * 0.02, kf + 0.01, 0.66)] + rp, [0.028, 0.03, 0.032, 0.034, 0.03], WHITE, 'plain', n=4, flat=(1.0, 0.25), side=(1, 0, 0))
            e = rp[-1]; prism(f'ribbon_end_{s}', blade(0.07, 0.016), (e[0], e[1] + 0.004, e[2] + 0.005), (e[0] + s * 0.012, e[1] + 0.045, e[2] - 0.075), GOLD, 'plain', scale_b=0.25, rnd=True, up=(0, 1, 0.5))
    PK.bone('upper')
    # upper body: slim shoulders, bust, narrow waist; the crossed collar (右衽): cinnabar inner robe, a white under-collar, a gold edge
    loft('torso', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in TORSO], ROBE, 'tile2', n_exp=TORSO_N, M=24)
    T = [i / 8 for i in range(9)] if lv == 0 else [i / 4 for i in range(5)] if lv == 1 else [0.0, 0.5, 1.0]
    pa = [(34 - 62 * t, 1.13 - 0.35 * t) for t in T]; pb = [(-34 + 30 * t, 1.13 - 0.20 * t) for t in T]
    band('collar_b', pb, 0.06, 0.018, CIN, 0.004)
    band('collar_b_in', [(a + 11, z) for a, z in pb[:-1]], 0.035, 0.014, WHITE, 0.002)
    band('collar_a', pa, 0.06, 0.022, CIN, 0.01)
    band('collar_a_in', [(a - 11, z) for a, z in pa[:len(pa) // 2 + 1]], 0.035, 0.016, WHITE, 0.007)
    if lv < 2: band('collar_a_gold', [(a + 8, z) for a, z in pa], 0.018, 0.016, GOLD, 0.018)
    lathe('collar_stand', [(0.10, 1.17), (0.082, 1.21), (0.074, 1.21)], CIN, 'plain', n=12)
    lathe('collar_stand_in', [(0.078, 1.175), (0.064, 1.225), (0.057, 1.225)], WHITE, 'plain', n=12)
    lathe('neck', [(0.052, 1.19), (0.046, 1.32)], SKIN, 'plain', n=10)
    if lv < 2 and CHEST_LINES:  # gold phoenix-tail lines embroidered on the chest, either side of the collar
        for s in (-1, 1):
            for q, (a0, a1, a2) in enumerate(((52, 30, 40), (64, 46, 58))):
                pts = [robe_pt(TORSO, s * a, z, 0.006, TORSO_N) for a, z in ((a0, 0.84 + 0.03 * q), (a1, 0.95 + 0.02 * q), (a2, 1.05))]
                sweep(f'chest_line_{s}{q}', pts, [0.008, 0.01, 0.004], GOLD, 'plain', n=3)
    if HAIR_FALL:  # two long hair lengths falling over the shoulders to the chest: smooth tapered forms
        for s in (-1, 1):
            sweep(f'hair_fall_{s}', [(s * x, f, z) for x, f, z in HAIR_PATH], HAIR_R, BLACK, 'plain', n=8, flat=(1.0, 0.6), side=(1, 0, 0))
            if lv < 2: torus(f'hair_tie_{s}', (s * HAIR_PATH[3][0], HAIR_PATH[3][1], HAIR_PATH[3][2]), (0, 0.2, 1), HAIR_R[3] * 0.85, 0.008, GOLD, 'plain', sg=(8, 3))
    PK.bone('root')
    # sleeves: long, round in section, flowing; the arm on the armrest ends in a drape hanging off it, the other is draped over her knee
    for s, arm, arm_r, tail, tail_r, key in ((S_REST, ARM_REST, ARM_REST_R, TAIL_REST, TAIL_REST_R, 'rest'), (S_LAP, ARM_LAP, ARM_LAP_R, TAIL_LAP, TAIL_LAP_R, 'lap')):
        fr = frames(arm, arm_r, s); pts = [p for p, u, v, r in fr]
        sweep(f'sleeve_{key}', pts, arm_r, ROBE, 'tile2', n=SLEEVE_N, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        tp = [(s * x, f, z) for x, f, z in tail]
        sweep(f'sleeve_tail_{key}', tp, tail_r, ROBE, 'tile2', n=SLEEVE_N, flat=(1.0, 0.55), side=(0, 0, 1))
        if lv < 2: sweep(f'tail_edge_{key}', [(p[0], p[1], max(p[2] - r * 0.7, 0.03)) for p, r in zip(tp[1:], tail_r[1:])], [0.02, 0.02, 0.016], CIN, 'plain', n=4)
        e1 = pts[-1]; d = unit([e1[i] - pts[-2][i] for i in range(3)]); R = arm_r[-1]
        at = lambda k: tuple(e1[i] + d[i] * k for i in range(3))
        # open cuff: gold rim, the cinnabar inner robe's sleeve, the white under-sleeve, the wrist
        sweep(f'cuff_rim_{key}', [at(-0.025), at(0.008)], [R + 0.01] * 2, GOLD, 'plain', n=SLEEVE_N, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        sweep(f'cuff_inner_{key}', [at(-0.02), at(0.035)], [R - 0.012, R - 0.03], CIN, 'plain', n=SLEEVE_N, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        sweep(f'cuff_white_{key}', [at(0.0), at(0.06)], [R - 0.05, R - 0.07], WHITE, 'plain', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        pp = [tuple(p[j] + u[j] * 0.9 * r - v[j] * 0.18 * r for j in range(3)) for p, u, v, r in fr]
        sweep(f'sleeve_gold_{key}', pp, [PIPE_R] * len(pp), GOLD, 'plain', n=5)
        if lv < 2:  # gold phoenix-tail lines on the sleeve's outer face
            for q, ks in enumerate(((0.35, -0.05, 0.15, 0.5), (-0.15, -0.5, -0.3, 0.05))):
                sweep(f'sleeve_line_{key}{q}', [on_sleeve(fr, 1.1 + 0.75 * j, k, 0.006) for j, k in enumerate(ks)], [0.007, 0.01, 0.01, 0.004], GOLD, 'plain', n=3)
    # armrests: black lacquer bars on two legs, bronze end caps
    for s in (-1, 1):
        x = s * REST_X
        prism(f'rest_{s}', rect(0.11, 0.075), (x, REST_F[0], REST_Z - 0.04), (x, REST_F[1], REST_Z - 0.04), LAC, 'plain', rnd=False)
        for q, f in enumerate(REST_F):
            f0 = f - 0.01 if q == 0 else f - 0.06
            if lv < 2: prism(f'rest_cap_{s}{q}', rect(0.13, 0.095), (x, f0, REST_Z - 0.04), (x, f0 + 0.07, REST_Z - 0.04), BR, 'lozenge', rnd=False)
            fl = REST_F[0] + 0.1 if q == 0 else REST_F[1] - 0.1
            prism(f'rest_leg_{s}{q}', rect(0.075, 0.06), (x, fl, REST_Z - 0.07), (x + s * 0.03, fl, 0.0), LAC, 'plain', scale_b=1.25, rnd=False)
    # hands: her right on the armrest, her left on her lap holding a small jade tally with a gold cap and a cinnabar cord
    hand('hand_rest', (S_REST * HAND_REST[0], HAND_REST[1], HAND_REST[2]), (0.0, 1.0, 0.0), lv, detail, ts=-S_REST)
    hl = (S_LAP * HAND_LAP[0], HAND_LAP[1], HAND_LAP[2])
    hand('hand_lap', hl, unit((-S_LAP * 0.35, 0.8, -0.45)), lv, detail)
    if TALLY:
        a = (hl[0] - S_LAP * 0.03, hl[1] + 0.03, hl[2] + 0.012); b = (a[0] - S_LAP * 0.05, a[1] + 0.07, a[2] + 0.13)
        prism('tally', rect(0.045, 0.014), a, b, JADE, 'plain', rnd=False, up=(0, 1, -0.4))
        prism('tally_cap', rect(0.052, 0.02), b, (b[0] - S_LAP * 0.012, b[1] + 0.016, b[2] + 0.03), GOLD, 'plain', rnd=True, up=(0, 1, -0.4))
        if lv < 2: prism('tally_cord', rect(0.01, 0.01), a, (a[0] + S_LAP * 0.01, a[1] + 0.05, a[2] - 0.09), CIN, 'plain', rnd=True, up=(1, 0, 0))
    PK.bone('upper')
    # head (all of it raised, chin up): a soft oval face, a small jaw, full cinnabar lips, cheeks, a small nose, lash lines, ears with jade drops
    n0 = len(K.PARTS)
    spheroid('head', HEAD_C, HEAD_R, SKIN, 'plain', sg=(14, 9))
    spheroid('jaw', (0.0, 0.055, CHIN_Z + 0.04), (0.055, 0.055, 0.045), SKIN, 'plain', sg=(10, 6))
    prism('nose', blade(0.026, 0.032), (0.0, head_f(EYE_Z + 0.004) - 0.012, EYE_Z + 0.004), (0.0, head_f(NOSE_Z) + 0.018, NOSE_Z), SKIN, 'plain', scale_b=1.15, rnd=True, up=(0, 1, 0.3))
    fl = head_f(LIPS_Z)
    spheroid('lip_up', (0.0, fl - 0.003, LIPS_Z + 0.008), (0.03, 0.017, 0.01), LIPS_MAT, 'plain', sg=(8, 4))
    spheroid('lip_low', (0.0, fl - 0.006, LIPS_Z - 0.008), (0.026, 0.018, 0.012), LIPS_MAT, 'plain', sg=(8, 4))
    for s in (-1, 1):
        spheroid(f'cheek_{s}', (s * 0.045, head_f(1.39, 0.045) - 0.02, 1.39), (0.032, 0.028, 0.03), SKIN, 'plain', sg=(8, 5))
        spheroid(f'ear_{s}', (s * 0.093, 0.0, 1.42), (0.011, 0.022, 0.03), SKIN, 'plain', sg=(6, 4))
        if lv < 2:
            fe = head_f(EYE_Z, 0.04)
            prism(f'lash_{s}', rect(0.034, 0.006), (s * 0.022, fe + 0.004, EYE_Z + 0.003), (s * 0.06, fe - 0.008, EYE_Z - 0.003), BLACK, 'plain', rnd=True, up=(0, 1, 0))
            spheroid(f'ear_drop_{s}', (s * 0.098, 0.004, 1.372), (0.011, 0.011, 0.02), JADE, 'plain', sg=(6, 4))
    # hair drawn up from a soft hairline into a tall coiled bun: three coils and a knot
    spheroid('hair', (0.0, -0.01, 1.47), (0.106, 0.125, 0.125), BLACK, 'plain', sg=(14, 8))
    spheroid('bun_core', (0.0, -0.105, 1.66), (0.07, 0.07, 0.11), BLACK, 'plain', sg=(8, 6))
    for q, (z, R, r) in enumerate(BUN): torus(f'bun_{q}', (0.0, -0.10 - 0.008 * q, z), (0, 0, 1), R, r, BLACK, 'plain', sg=(12, 5) if detail else (10, 4))
    spheroid('bun_knot', (0.0, -0.12, BUN[-1][0] + 0.055), (0.04, 0.04, 0.042), BLACK, 'plain', sg=(8, 5))
    # the phoenix crown: a slim gold diadem round the brow, a small gold phoenix rising from it (wings spread, tail plumes sweeping back over the bun)
    dp = [(DIADEM_R * math.sin(math.radians(a)) * HEAD_R[0] / HEAD_R[1], HEAD_C[1] + DIADEM_R * math.cos(math.radians(a)), DIADEM_Z - 0.01 * abs(a) / 95) for a in range(-95, 96, 19)]
    sweep('diadem', dp, [0.016] * len(dp), GOLD, 'plain', n=4, flat=(1.0, 0.5), side=(0, 0, 1))
    c = (0.0, HEAD_C[1] + DIADEM_R - 0.02, DIADEM_Z + 0.045)
    spheroid('phx_body', c, (0.026, 0.04, 0.03), GOLD, 'plain', sg=(6, 4))
    prism('phx_neck', ngon(0.011, 4), (c[0], c[1] + 0.02, c[2] + 0.015), (c[0], c[1] + 0.045, c[2] + 0.075), GOLD, 'plain', rnd=True)
    prism('phx_beak', blade(0.02, 0.016), (c[0], c[1] + 0.04, c[2] + 0.078), (c[0], c[1] + 0.09, c[2] + 0.062), GOLD, 'plain', scale_b=0.15, rnd=True, up=(0, 0, 1))
    for s in (-1, 1):
        sweep(f'phx_wing_{s}', [(c[0] + s * 0.015, c[1], c[2] + 0.005), (c[0] + s * 0.08, c[1] - 0.03, c[2] + 0.05), (c[0] + s * 0.15, c[1] - 0.08, c[2] + 0.09)], [0.022, 0.026, 0.0], GOLD, 'plain', n=4, flat=(1.0, 0.3), side=(0, 0, 1))
        if lv < 2: spheroid(f'phx_pearl_{s}', (s * DIADEM_R * 0.78, HEAD_C[1] + DIADEM_R * 0.62, DIADEM_Z + 0.004), (0.014, 0.014, 0.014), JADE, 'plain', sg=(6, 4))
    for k in (-1, 0, 1):
        sweep(f'phx_tail_{k}', [(c[0], c[1] - 0.03, c[2] + 0.01), (c[0] + k * 0.05, c[1] - 0.12, c[2] + 0.11 + 0.03 * (k == 0)), (c[0] + k * 0.1, c[1] - 0.24, c[2] + 0.17 + 0.07 * (k == 0))], [0.014, 0.016, 0.0], GOLD, 'plain', n=4, flat=(1.0, 0.4))
    # gold hairpins through the bun, a flower head each side (their tassels hang below, built after the head is raised)
    for s in (-1, 1):
        prism(f'hairpin_{s}', ngon(0.009, 5), (s * 0.02, -0.11, 1.655), (s * PIN_TIP[0], PIN_TIP[1], PIN_TIP[2]), GOLD, 'plain', rnd=True)
        prism(f'pin_flower_{s}', ngon(0.03, 6), (s * PIN_TIP[0], PIN_TIP[1], PIN_TIP[2]), (s * (PIN_TIP[0] + 0.022), PIN_TIP[1], PIN_TIP[2] + 0.008), GOLD, 'plain', scale_b=0.55, rnd=True)
    PK.tilt([p[0] for p in K.PARTS[n0:]], HEAD_PIVOT, (1, 0, 0), HEAD_TILT)
    # the lifted veil: twelve short bead strings from the diadem to the nose bridge (three groups, each sways on its own bone)
    for k, top in enumerate(string_tops()):
        PK.bone(f'beads_f{k * 3 // STRINGS}')
        if lv == 2:
            if k % 3 == 1: prism(f'strip_{k}', rect(0.05, 0.008), top, (top[0], top[1], top[2] - STR_LEN), JADE, 'plain', rnd=True, up=(top[0], 0.3, 0))
            continue
        w = CORD_W if detail else CORD_W * 2.4
        prism(f'cord_{k}', rect(w, w), top, (top[0], top[1], top[2] - STR_LEN), JADE, 'plain', rnd=True, up=(top[0], 0.3, 0))
        if detail:
            for j in range(STR_BEADS + 1):
                last = j == STR_BEADS
                spheroid(f'bead_{k}_{j}', (top[0], top[1], top[2] - STR_LEN * (j + 1) / (STR_BEADS + 1)), (BEAD_R * (1.35 if last else 1.0),) * 3, GOLD if last else JADE, 'plain', sg=(5, 3))
    # 步摇 tassels hanging from each hairpin: gold cords, jade beads, a gold drop
    for s, nm in ((-1, 'R'), (1, 'L')):
        PK.bone(f'tassel_{nm}'); tip = pin_tip(s)
        for q in range(TASSELS if lv < 2 else 1):
            x = tip[0] + s * 0.012 + (q - (TASSELS - 1) / 2) * 0.016; L = TASSEL_LEN * (1.0 - 0.18 * abs(q - (TASSELS - 1) / 2))
            prism(f'tassel_{nm}{q}', rect(0.006 if detail else 0.012, 0.006 if detail else 0.012), (x, tip[1], tip[2]), (x, tip[1], tip[2] - L), GOLD, 'plain', rnd=True, up=(s, 0, 0))
            if detail:
                spheroid(f'tassel_bead_{nm}{q}', (x, tip[1], tip[2] - L * 0.5), (0.008, 0.008, 0.008), JADE, 'plain', sg=(5, 3))
                spheroid(f'tassel_drop_{nm}{q}', (x, tip[1], tip[2] - L - 0.012), (0.009, 0.009, 0.016), GOLD, 'plain', sg=(5, 3))
    PK.bone('root')


def bones():
    tops = string_tops(); out = [('root', (0, 0, 0), (0, 0, 0.3), None), ('upper', (0, 0, 0.66), (0, 0, 1.1), 'root')]; n = STRINGS // 3
    for g in range(3):
        grp = tops[g * n:(g + 1) * n]; c = [sum(p[i] for p in grp) / len(grp) for i in range(3)]
        out.append((f'beads_f{g}', tuple(c), (c[0], c[1], c[2] - STR_LEN), 'upper'))
    for s, nm in ((-1, 'R'), (1, 'L')):
        t = pin_tip(s); out.append((f'tassel_{nm}', t, (t[0], t[1], t[2] - TASSEL_LEN), 'upper'))
    return out

def clips(arm):
    tau = math.tau; rot = {}
    for g in range(3):
        ph = g * 0.17
        rot[f'beads_f{g}'] = PK.wave(IDLE_S, 8, lambda p, ph=ph: [((1, 0, 0), SWAY * math.sin(tau * (p + ph))), ((0, 1, 0), 2.5 * math.sin(tau * (p + ph) + 1.3))])
    for i, nm in enumerate(('R', 'L')):
        rot[f'tassel_{nm}'] = PK.wave(IDLE_S, 8, lambda p, i=i: [((0, 1, 0), SWAY_T * math.sin(tau * (p + 0.3 * i))), ((1, 0, 0), 3.0 * math.sin(tau * (p + 0.3 * i) + 0.9))])
    rot['upper'] = PK.wave(IDLE_S, 8, lambda p: [((1, 0, 0), -BREATH[1] * math.sin(tau * p))])   # slow breathing: the chest rises and leans back a little
    idle = PK.clip(arm, 'idle', rot, {'upper': PK.wave(IDLE_S, 8, lambda p: (0, 0, BREATH[0] * (0.5 + 0.5 * math.sin(tau * p))))})
    return [(idle, IDLE_S, 'beads_f1', SWAY_MIN)]

def count(ob, mats, test):
    """faces of the named materials whose centre (x, f, z) passes test."""
    names = [m.name for m in ob.data.materials]
    return sum(1 for p in ob.data.polygons if names[p.material_index] in mats and test(p.center.x, -p.center.y, p.center.z))

def gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(K.tris(l0) >= TRIS_MIN, f'kaymuse_lod0 tris {K.tris(l0)} (min {TRIS_MIN}: face, hands, hair, bead strings and folds modelled)')
    d = SEAT_Z[1] - SEAT_Z[0]
    G(x1 - x0 <= 2 * SEAT_HW and -y0 <= d / 2 and y1 <= d / 2 and -0.02 < z0 < 0.01,
      f'kaymuse sits within the throne seat: {x1 - x0:.2f} m wide (seat {2 * SEAT_HW:.2f}), f {-y1:.2f}..{-y0:.2f} m (seat half depth {d / 2:.2f}), base z {z0:.2f}')
    G(1.5 <= z1 <= 2.1, f'kaymuse crown top {z1:.2f} m over the seat (range 1.5-2.1; a suit stands 2.05-2.4 m)')
    # round 5 (owner 18:42 'she must look feminine'; lead: shapes, not details): the gates below replace round 4's veil, face, woman and crown gates
    span = 2 * DIADEM_R * math.sin(math.radians((STRINGS - 1) / 2 * STR_DEG)) * HEAD_R[0] / HEAD_R[1]; gap = DIADEM_R * math.radians(STR_DEG) * HEAD_R[0] / HEAD_R[1] - 2 * BEAD_R; bot = DIADEM_Z - 0.012 - STR_LEN
    G(STRINGS == 12 and span >= 0.085 and gap >= BEAD_R and NOSE_Z + 0.02 <= bot <= EYE_Z - 0.005,
      f'kaymuse veil lifted: {STRINGS} bead strings spanning {span:.2f} m (both eyes, 0.085), {gap * 1000:.0f} mm clear between strings (min {BEAD_R * 1000:.0f}), ending at z {bot:.3f}: below the eyes ({EYE_Z}), above the nose tip ({NOSE_Z}), lips ({LIPS_Z}) and chin clear')
    hz = lambda z: z + 0.02   # the raised head sits a little higher in front
    lips = count(l0, (CIN,), lambda x, f, z: abs(x) < 0.04 and f > 0.1 and LIPS_Z - 0.02 < z < hz(LIPS_Z) + 0.03)
    chin = count(l0, (SKIN,), lambda x, f, z: f > 0.04 and CHIN_Z - 0.02 < z < hz(CHIN_Z) + 0.04 and abs(x) < 0.06)
    cheek = count(l0, (SKIN,), lambda x, f, z: 0.03 < abs(x) < 0.08 and f > 0.07 and 1.36 < z < 1.45)
    G(min(lips, chin, cheek) > 0 and HEAD_R[0] <= 0.1 and HEAD_R[2] >= 1.35 * HEAD_R[0] and HEAD_TILT <= -5,
      f'kaymuse face: a soft oval {2 * HEAD_R[0]:.2f} x {2 * HEAD_R[2]:.2f} m, {lips} cinnabar lip faces, {chin} chin faces, {cheek} cheek faces, chin raised {-HEAD_TILT} deg')
    sh, wa, bu, hip = TORSO[I_SHOULDER][2], TORSO[I_WAIST][2], TORSO[I_BUST][2], SKIRT[I_HIP][2]
    G(sh <= 0.28 and wa <= 0.72 * sh and bu >= 1.25 * wa and hip >= 1.6 * wa and SKIRT[1][2] >= 3.5 * sh and SASH_Z[1] - SASH_Z[0] >= 0.15 and TORSO[I_BUST][1] > TORSO[I_WAIST][1],
      f'kaymuse figure: shoulders {2 * sh:.2f} m, waist {wa / sh:.0%} of them under a {(SASH_Z[1] - SASH_Z[0]) * 100:.0f} cm sash, bust {bu / wa:.2f} x and hips {hip / wa:.2f} x the waist, hem {SKIRT[1][2] / sh:.1f} x the shoulders')
    fall = count(l0, (BLACK,), lambda x, f, z: 0.08 < abs(x) < 0.2 and f > 0.12 and 0.86 < z < 1.2); bun = count(l0, (BLACK,), lambda x, f, z: z > 1.6 and f < 0.0)
    tas = count(l0, (GOLD, JADE), lambda x, f, z: abs(x) > 0.17 and f < 0.0 and 1.45 < z < 1.75)
    G(HAIR_FALL and fall >= 16 and bun >= 60 and tas >= 12 and len(BUN) >= 3, f'kaymuse hair: two lengths falling to the chest ({fall} faces), a tall bun of {len(BUN)} coils ({bun} faces above 1.6 m), hairpin tassels each side ({tas} faces)')
    hr = count(l0, (SKIN,), lambda x, f, z: x * S_REST > 0.8 and f > 0.4 and z < 0.6); hlp = count(l0, (SKIN,), lambda x, f, z: abs(x) < 0.2 and 0.3 < f < 0.6 and 0.4 < z < 0.65)
    ta = count(l0, (JADE,), lambda x, f, z: abs(x) < 0.2 and 0.38 < f < 0.6 and 0.5 < z < 0.75)
    G(hr >= 30 and hlp >= 30 and TALLY and ta > 0, f'kaymuse posture: her right hand on the armrest ({hr} skin faces), her left on her lap ({hlp}) holding a jade tally ({ta} faces)')
    G(SLEEVE_N >= 10 and SKIRT_N <= 2.6 and TORSO_N <= 2.6 and count(l0, (LAC,), lambda x, f, z: z > 1.5) == 0,
      f'kaymuse round forms: sleeves {SLEEVE_N}-sided, robe sections roundness {SKIRT_N} / {TORSO_N} (max 2.6), no crown board')
    inner = count(l0, (CIN,), lambda x, f, z: z < INNER_Z + 0.01) + count(l0, (CIN,), lambda x, f, z: z > 0.78 and z < 1.25); emb = count(l0, (GOLD,), lambda x, f, z: 0.82 < z < 1.0 and 0.12 < abs(x) < 0.27 and f > 0.05)
    G(inner >= 60 and emb >= 8, f'kaymuse colour: cinnabar inner robe at hem and collar ({inner} faces), gold embroidery lines on the chest ({emb} faces)')
    act = __import__('bpy').data.actions['idle']; tm = PK.motion(arm, act, 'tassel_L', IDLE_S); um = PK.motion(arm, act, 'upper', IDLE_S)
    G(tm >= SWAY_MIN and 0.002 <= um <= 0.02, f'kaymuse idle: hairpin tassels sway {tm * 1000:.0f} mm, slow breathing moves the chest {um * 1000:.0f} mm (2-20 mm)')
    m = K.mats(l0); G({ROBE, CIN, GOLD, JADE, WHITE, BLACK, SKIN} <= m, f'kaymuse materials {sorted(m)}')
    G({CIN, GOLD, WHITE, SKIN, BLACK} <= K.mats(l1) and {CIN, GOLD, SKIN} <= K.mats(l2), 'kaymuse LOD1 keeps cinnabar, gold, white, skin and hair; LOD2 keeps cinnabar, gold and skin')


if __name__ == '__main__':
    seat = [0.0, SEAT_Y, (SEAT_Z[0] + SEAT_Z[1]) / 2]
    PK.build_rigged('kaymuse', build, bones(), clips, OUT, BUDGET, 4.0, extras={'seat': seat, 'clips': 'idle'}, extra_gates=gates)
    sys.exit(0)
