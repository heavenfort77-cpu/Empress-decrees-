# Empress Kaymuse, seated (PIECES round 4; owner 25 Nov 13:08, 13:1x and 14:13 "kaymuse is female"): a woman, an empress, in black Qin
# court robes with a 冕 crown whose bead strings veil her eyes. Replaces the two cream boxes on the throne.
# Round 3 (lead after run 45557912570): she must read as a woman close up and at play size: narrow shoulders, a defined waist under a
# wide cinnabar sash with a gold knot, hanging ribbons and jade pendants, a long wide trailing hem; long hair in a high coiled bun
# behind the crown with two gold hairpins and their drops showing beside it; a slender neck and a modelled lower face (jaw, chin, a
# small nose, cinnabar lips, ears with jade drops, cheek locks, closed lash lines): the strings cover the eyes and upper face only.
# The 冕 is a short thin board with a gold inlay field, three gold cloud points and a small gold phoenix on top (a crown with a bead
# veil, not a block). Sleeves: deep masses pooling on the seat, draped fold swags, an open cuff (gold rim, cinnabar lining, the white
# inner sleeve) and hands with long fingers on her own two low lacquer armrests (凭几; the throne couch is 4.06 m wide).
# Outline against the throne: the white inner layer at the floor, cuffs and under-sleeve edges, gold borders along the sleeve tops,
# gold crown points and hairpins. No face detail is painted: forms only, own design from the research rule list.
# Round 4 (lead after run 45560766962): the face is simple modelled planes (brow, nose bridge, cheeks, lips) in a warm skin tone; the
# hands have joined fingers with a slight curl; the collar is two smooth crossed bands (swept, not stepped); the inner layer is a
# brighter white with folds at the floor; the strings hang 11 degrees apart (the veil gate's clear gap).
# Scale: about 1.3 x a suit (guess, lead to judge). Model origin = the middle of her seat place; extras 'seat' = where that sits in
# throne_dais.glb (three.js x, y, z). Clip 'idle' (4 s loop): the bead strings sway. LOD0 skinned (rigid), LOD1 / LOD2 static.
# Usage: python pieces_kaymuse.py OUT.glb   (inside Blender's Python)
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_kit as K
import pieces_kit as PK
from prop_kit import lathe, spheroid, sweep, prism, torus, loft, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/kaymuse.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (task: about 6-10k LOD0 plus a low LOD).
BUDGET = (10000, 2600, 900)
# LOD0 floor (task: about 6k: face, hands, bead strings and folds are modelled, not painted).
TRIS_MIN = 5000
# Throne seat in throne_dais.glb (measured from the GLB): top y, half width x, front z and back z (three.js axes), m.
SEAT_Y, SEAT_HW, SEAT_Z = 2.16, 2.03, (-1.75, 0.07)
# Lower robe sections (z, centre f, half width, half depth), m: the long trailing hem to the waist.
SKIRT = [(0.0, 0.10, 1.16, 0.70), (0.06, 0.10, 1.18, 0.71), (0.20, 0.08, 0.92, 0.60), (0.40, 0.04, 0.58, 0.42), (0.56, 0.0, 0.34, 0.26), (0.64, 0.0, 0.27, 0.20)]
# Roundness of the robe sections (2 = ellipse, higher = squarer): skirt, torso.
SKIRT_N, TORSO_N = 3.0, 2.6
# White inner layer showing at the floor: how far it stands out past the black robe, m; its height m.
UNDER_OUT, UNDER_H = 0.085, 0.035
# Upper robe sections (z, centre f, half width, half depth), m: waist, ribs, bust, shoulders, neck root (narrow shoulders, a defined waist).
TORSO = [(0.60, 0.0, 0.25, 0.19), (0.78, 0.0, 0.26, 0.20), (0.98, 0.01, 0.33, 0.235), (1.10, -0.01, 0.36, 0.21), (1.19, -0.02, 0.30, 0.17), (1.235, -0.02, 0.12, 0.11)]
# Sash at the waist: z range, how far it stands proud m.
SASH_Z, SASH_OUT = (0.60, 0.77), 0.022
# Fold ridges round the lower robe: count each side of the front, degrees between them, ridge width and height m.
PLEATS, PLEAT_DEG, PLEAT_W, PLEAT_T = 6, 15, 0.10, 0.06
# Sleeve centre line from the shoulder to the cuff (x outward, f, z) and the section half height at each point, m; section depth over height.
SLEEVE = [(0.34, -0.02, 1.08), (0.50, 0.0, 0.90), (0.74, 0.06, 0.60), (0.90, 0.20, 0.36), (0.98, 0.38, 0.29)]
SLEEVE_R, SLEEVE_FLAT = [0.13, 0.21, 0.30, 0.29, 0.24], 0.7
# Border piping radius m: gold along the sleeve's upper edge, the white inner sleeve showing along its lower edge.
PIPE_R = 0.034
# Armrest (凭几): x of the bar, its f range, top height, m. Hand: palm centre (x, f, z), finger length m.
REST_X, REST_F, REST_Z = 0.98, (-0.38, 0.52), 0.42
HAND_C, FINGER = (0.98, 0.50, 0.462), 0.12
# Head centre and radii (x, f, z), m. Heights of the lash line, nose tip, lips and chin, m. LIPS_MAT is the lips' material.
HEAD_C, HEAD_R = (0.0, 0.02, 1.43), (0.105, 0.12, 0.145)
EYE_Z, NOSE_Z, LIPS_Z, CHIN_Z, LIPS_MAT = 1.452, 1.405, 1.35, 1.29, 'palCinnabar'
# 冕 board: centre, half width, rear length, front arc centre offset (arc radius = half width), forward tip deg, m.
BOARD_C, BOARD_HW, BOARD_REAR, BOARD_ARC, BOARD_TIP = (0.0, 0.01, 1.655), 0.20, 0.26, 0.08, 8
# Bead strings: count front and back (twelve each), arc radius the front ones hang on m, degrees between them, cord width m.
STRINGS, STR_ARC_R, STR_DEG, CORD_W = 12, 0.185, 11, 0.007
# Front strings: length m (to the nose: the lips stay clear), beads per string, bead radius m, first bead and pitch m. Back strings: length, beads.
STR_LEN, STR_BEADS, BEAD_R, BEAD_0, BEAD_PITCH = 0.19, 4, 0.011, 0.04, 0.045
STR_LEN_B, STR_BEADS_B = 0.14, 3
# Bun: centre and radii m; hairpin half span m.
BUN_C, BUN_R, PIN_SPAN = (0.0, -0.30, 1.66), (0.105, 0.095, 0.10), 0.29
# Idle clip: seconds, front sway deg (fore-aft, sideways), back sway deg, min string travel m.
IDLE_S, SWAY_F, SWAY_B, SWAY_MIN = 4.0, (6.0, 2.5), 4.0, 0.008
ROBE, CIN, GOLD, JADE, BLACK, LAC, BR, SKIN, WHITE = 'kmRobe', 'palCinnabar', 'palGold', 'kmJade', 'pcBlack', 'palLacquerPlain', 'palBronze', 'kmSkin', 'kmWhite'
PK.mutate(globals())
TIP = math.radians(BOARD_TIP)


def lerp_secs(secs, z):
    for a, b in zip(secs, secs[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return [a[i] + (b[i] - a[i]) * k for i in range(4)]
    return list(secs[-1] if z > secs[-1][0] else secs[0])

def robe_pt(secs, a_deg, z, out=0.0, n=None):
    """a point on the robe's surface: a_deg from the front (positive toward +x), height z, pushed outward by out."""
    _, cf, hw, hd = lerp_secs(secs, z); a = math.radians(a_deg); s, c = math.sin(a), math.cos(a); e = 2 / (n or SKIRT_N)
    return ((hw + out) * math.copysign(abs(s) ** e, s), cf + (hd + out) * math.copysign(abs(c) ** e, c), z)

def board_pt(p0, p1, dz=0.0):
    """board-local (across, toward the rear) -> design point on the tipped board."""
    return (BOARD_C[0] - p0, BOARD_C[1] - p1 * math.cos(TIP), BOARD_C[2] + p1 * math.sin(TIP) + dz)

def string_tops():
    """(x, f, z) where each front string hangs from the board's front arc, and each back string from the rear edge."""
    front = []
    for k in range(STRINGS):
        ph = math.radians((k - (STRINGS - 1) / 2) * STR_DEG)
        front.append(board_pt(STR_ARC_R * math.sin(ph), -BOARD_ARC - STR_ARC_R * math.cos(ph), -0.03))
    back = [board_pt((k - (STRINGS - 1) / 2) * 0.03, BOARD_REAR - 0.015, -0.03) for k in range(STRINGS)]
    return front, back

def unit(v):
    L = math.sqrt(sum(c * c for c in v)); return [c / L for c in v]

def cross(a, b): return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]

def sleeve_frame(s):
    """per sleeve point: (centre, up unit vector in the hanging plane, outward unit vector across the cloth, half height)."""
    pts = [(s * x, f, z) for x, f, z in SLEEVE]; out = []
    for i, (p, r) in enumerate(zip(pts, SLEEVE_R)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]; t = unit([b[j] - a[j] for j in range(3)])
        u = unit([-t[2] * t[0], -t[2] * t[1], 1 - t[2] * t[2]]); v = unit(cross(t, u))
        if v[0] * s + v[1] < 0: v = [-c for c in v]   # the face turned away from the body (outward and forward)
        out.append((p, u, v, r))
    return out

def on_sleeve(fr, i, k, lift=0.0):
    """a point on the sleeve's outer face: at path index i (may be fractional), k = -1 lower edge .. 1 upper edge."""
    i0 = min(int(i), len(fr) - 2); w = i - i0; (p, u, v, r), (q, u2, v2, r2) = fr[i0], fr[i0 + 1]
    P_ = [p[j] + (q[j] - p[j]) * w for j in range(3)]; U = unit([u[j] + (u2[j] - u[j]) * w for j in range(3)]); V = unit([v[j] + (v2[j] - v[j]) * w for j in range(3)]); R = r + (r2 - r) * w
    d = SLEEVE_FLAT * R * math.sqrt(max(1 - k * k, 0.0)) + lift
    return tuple(P_[j] + U[j] * k * R + V[j] * d for j in range(3))

def band(name, path, w, t, mat, out):
    """a smooth flat border swept over the upper robe along path [(a_deg, z)] (round 4: one swept band, not stepped blocks)."""
    pts = [robe_pt(TORSO, a, z, out, TORSO_N) for a, z in path]
    sweep(name, pts, [w / 2] * len(pts), mat, 'plain', n=6, flat=(1.0, max(t / w * 1.4, 0.3)), side=(1, 0, 0))

def head_f(z, x=0.0):
    """f of the head's front surface at height z and offset x."""
    k = 1 - ((z - HEAD_C[2]) / HEAD_R[2]) ** 2 - (x / HEAD_R[0]) ** 2; return HEAD_C[1] + HEAD_R[1] * math.sqrt(max(k, 0.0))


def build(detail):
    lv = PK.LEVEL['n']; PK.bone('root')
    # lower robe: the white inner layer at the floor, the black skirt spreading into a long wide hem, a gold-inlay hem band and a cinnabar band
    hw0, hd0 = SKIRT[0][2] + UNDER_OUT, SKIRT[0][3] + UNDER_OUT
    loft('under', [(0.0, 0.10, hw0, hd0, 0.0), (UNDER_H, 0.10, hw0, hd0, 0.0)], WHITE, 'plain', n_exp=SKIRT_N, M=32)
    if detail:  # folds in the white layer where it shows at the floor (cloth, not a plate)
        for i in range(-11, 12):
            a = i * 15.5 + 4
            prism(f'under_fold_{i}', blade(0.085, 0.03), robe_pt(SKIRT, a, UNDER_H - 0.004, 0.02), robe_pt(SKIRT, a, UNDER_H - 0.012, UNDER_OUT + 0.012), WHITE, 'plain', scale_b=1.3, rnd=True, up=(0, 0, 1))
    loft('skirt', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in SKIRT], ROBE, 'tile2', n_exp=SKIRT_N, M=32)
    loft('hem_gold', [(UNDER_H, 0.10, 1.195, 0.728, 0.0), (0.10, 0.094, 1.13, 0.69, 0.0)], GOLD, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    loft('hem_cin', [(0.10, 0.094, 1.12, 0.685, 0.0), (0.15, 0.088, 1.03, 0.645, 0.0)], CIN, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    zs = (0.60, 0.42, 0.26, 0.16) if detail else (0.60, 0.26, 0.16)
    for i in range(-PLEATS, PLEATS + 1):  # carved fold ridges fanning from the waist to the hem band
        if i == 0 or (lv == 2 and i % 2): continue
        for j, (z0, z1) in enumerate(zip(zs, zs[1:])):
            a0 = i * PLEAT_DEG * (0.75 + 0.25 * (0.60 - z0) / 0.5); a1 = i * PLEAT_DEG * (0.75 + 0.25 * (0.60 - z1) / 0.5)
            w = PLEAT_W * (0.55 + 0.9 * (0.60 - z0)); k = (0.55 + 0.9 * (0.60 - z1)) / (0.55 + 0.9 * (0.60 - z0))
            n = (math.sin(math.radians(a0)), math.cos(math.radians(a0)), 0.45)
            prism(f'pleat_{i}_{j}', blade(w, PLEAT_T), robe_pt(SKIRT, a0, z0), robe_pt(SKIRT, a1, z1), ROBE, 'tile2', scale_b=k, rnd=True, up=n)
    # 蔽膝 knee panel: cinnabar with gold edge lines, down the front; over it two white sash ribbons with gold ends
    bz = (0.60, 0.42, 0.26, 0.165)
    for j, (z0, z1) in enumerate(zip(bz, bz[1:])):
        w0 = 0.22 + 0.32 * (0.60 - z0); w1 = 0.22 + 0.32 * (0.60 - z1)
        prism(f'bixi_{j}', rect(w0, 0.03), robe_pt(SKIRT, 0, z0, 0.03), robe_pt(SKIRT, 0, z1, 0.03), CIN, 'plain', scale_b=w1 / w0, rnd=False, up=(0, 1, 0.5))
        a, b = robe_pt(SKIRT, 0, z0, 0.05), robe_pt(SKIRT, 0, z1, 0.05)
        for s in (-1, 1): prism(f'bixi_edge_{j}{s}', rect(0.026, 0.02), (s * w0 / 2, a[1], a[2]), (s * w1 / 2, b[1], b[2]), GOLD, 'plain', rnd=True, up=(0, 1, 0.5))
        if j < 2 and lv < 2:
            a, b = robe_pt(SKIRT, 0, z0, 0.062), robe_pt(SKIRT, 0, z1, 0.062)
            for s in (-1, 1): prism(f'ribbon_{j}{s}', rect(0.05, 0.014), (s * (0.035 + 0.02 * j), a[1], a[2]), (s * (0.055 + 0.02 * j), b[1], b[2]), JADE, 'plain', rnd=True, up=(0, 1, 0.5))
    if detail:
        e = robe_pt(SKIRT, 0, 0.26, 0.064)
        for s in (-1, 1): prism(f'ribbon_end_{s}', blade(0.06, 0.016), (s * 0.075, e[1], e[2] + 0.005), (s * 0.085, e[1] + 0.035, e[2] - 0.07), GOLD, 'plain', scale_b=0.25, rnd=True, up=(0, 1, 0.5))
    # upper robe: narrow shoulders, a defined waist under a wide cinnabar sash with gold edges and a gold knot
    loft('torso', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in TORSO], ROBE, 'tile2', n_exp=TORSO_N, M=24)
    (_, c0, w0, d0), (_, c1, w1, d1) = lerp_secs(TORSO, SASH_Z[0]), lerp_secs(TORSO, SASH_Z[1])
    loft('sash', [(SASH_Z[0], c0, w0 + SASH_OUT, d0 + SASH_OUT, 0.0), (SASH_Z[1], c1, w1 + SASH_OUT, d1 + SASH_OUT, 0.0)], CIN, 'plain', n_exp=TORSO_N, M=24, cap=False)
    for q, z in enumerate(SASH_Z):
        _, c, w, d = lerp_secs(TORSO, z); zz = z + (0.0 if q == 0 else -0.018)
        loft(f'sash_edge_{q}', [(zz, c, w + SASH_OUT + 0.008, d + SASH_OUT + 0.008, 0.0), (zz + 0.018, c, w + SASH_OUT + 0.008, d + SASH_OUT + 0.008, 0.0)], GOLD, 'plain', n_exp=TORSO_N, M=24, cap=False)
    kf = lerp_secs(TORSO, 0.685)[3] + SASH_OUT
    prism('knot', ngon(0.062, 6), (0.0, kf - 0.005, 0.685), (0.0, kf + 0.035, 0.685), GOLD, 'plain', rnd=False)
    if lv < 2:  # jade pendants hanging from the sash at each hip: a cinnabar cord and three jade pieces
        for s in (-1, 1):
            zc = (0.58, 0.47, 0.38, 0.30); pc = [robe_pt(SKIRT, s * (40 + 4 * i), z, 0.03) for i, z in enumerate(zc)]
            for j, (a, b) in enumerate(zip(pc, pc[1:])):
                prism(f'cord_{s}{j}', rect(0.014, 0.012), a, b, CIN, 'plain', rnd=True, up=(s, 1, 0.5))
                if detail or j == 1: prism(f'jade_{s}{j}', ngon(0.042 - 0.006 * j, 6), b, (b[0] + s * 0.012, b[1] + 0.014, b[2] + 0.006), JADE, 'plain', rnd=True)
    # layered crossed collar laid on the chest: her left border over her right (右衽): white inner collar, cinnabar border, gold edge
    T5 = [i / 8 for i in range(9)] if lv == 0 else [i / 4 for i in range(5)] if lv == 1 else [0.0, 0.5, 1.0]
    pa = [(38 - 70 * t, 1.17 - 0.40 * t) for t in T5]; pb = [(-38 + 33 * t, 1.17 - 0.24 * t) for t in T5]
    band('collar_b', pb, 0.07, 0.02, CIN, 0.004)
    band('collar_b_in', [(a + 10, z) for a, z in pb[:-1]], 0.045, 0.016, WHITE, 0.002)
    band('collar_a', pa, 0.07, 0.026, CIN, 0.012)
    band('collar_a_in', [(a - 10, z) for a, z in pa[:len(pa) // 2 + 1]], 0.045, 0.02, WHITE, 0.008)
    if detail: band('collar_a_gold', [(a + 7.5, z) for a, z in pa], 0.022, 0.02, GOLD, 0.022)
    lathe('collar_stand', [(0.125, 1.195), (0.104, 1.238), (0.094, 1.238)], CIN, 'plain', n=12)
    lathe('collar_stand_in', [(0.10, 1.20), (0.08, 1.255), (0.071, 1.255)], WHITE, 'plain', n=12)
    lathe('neck', [(0.064, 1.22), (0.058, 1.31)], SKIN, 'plain', n=10)
    # sleeves: deep masses pooling on the seat, draped fold swags, a gold border above and the white inner sleeve showing below,
    # an open cuff (gold rim, cinnabar lining, white inner sleeve) and a hand with long fingers on the armrest
    for s in (-1, 1):
        fr = sleeve_frame(s); pts = [p for p, u, v, r in fr]
        sweep(f'sleeve_{s}', pts, SLEEVE_R, ROBE, 'tile2', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        e1 = pts[-1]; d = unit([e1[i] - pts[-2][i] for i in range(3)]); u = fr[-1][1]; R = SLEEVE_R[-1]
        at = lambda k, up=0.0: tuple(e1[i] + d[i] * k + u[i] * up for i in range(3))
        sweep(f'cuff_rim_{s}', [at(-0.03), at(0.012)], [R + 0.014] * 2, WHITE, 'plain', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        sweep(f'cuff_lining_{s}', [at(-0.02), at(0.024)], [R - 0.012, R - 0.035], CIN, 'plain', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        hc = (s * HAND_C[0], HAND_C[1], HAND_C[2])
        sweep(f'cuff_inner_{s}', [at(-0.04, R - 0.10), (hc[0], hc[1] - 0.05, hc[2] + 0.012)], [0.088, 0.058], WHITE, 'plain', n=8)
        pp = [(p[0] + u_[0] * 0.89 * r - v_[0] * 0.2 * r, p[1] + u_[1] * 0.89 * r - v_[1] * 0.2 * r, p[2] + u_[2] * 0.89 * r - v_[2] * 0.2 * r) for p, u_, v_, r in fr]
        sweep(f'sleeve_gold_{s}', pp, [PIPE_R] * len(pp), GOLD, 'plain', n=5)
        pw = [(p[0] - u_[0] * 0.9 * r + v_[0] * 0.2 * r, p[1] - u_[1] * 0.9 * r + v_[1] * 0.2 * r, max(p[2] - u_[2] * 0.9 * r + v_[2] * 0.2 * r, PIPE_R + 0.012)) for p, u_, v_, r in fr[1:]]
        sweep(f'sleeve_white_{s}', pw, [PIPE_R + 0.008] * len(pw), WHITE, 'plain', n=5)
        if lv < 2:  # draped folds: swags hanging across the sleeve's outer face
            for q, ks in enumerate(((0.62, 0.05, -0.22, 0.42), (0.4, -0.3, -0.52, 0.15), (0.18, -0.62, -0.78, -0.2))):
                sp = [on_sleeve(fr, 1 + 0.9 * j, k, 0.012) for j, k in enumerate(ks)]
                if detail or q != 1: sweep(f'swag_{s}{q}', sp, [0.03, 0.042, 0.042, 0.028], ROBE, 'tile2', n=4)
        # armrest: a black lacquer bar on two legs, bronze end caps
        x = s * REST_X
        prism(f'rest_{s}', rect(0.11, 0.075), (x, REST_F[0], REST_Z - 0.04), (x, REST_F[1], REST_Z - 0.04), LAC, 'plain', rnd=False)
        for q, f in enumerate(REST_F):
            f0 = f - 0.01 if q == 0 else f - 0.06
            if lv < 2: prism(f'rest_cap_{s}{q}', rect(0.13, 0.095), (x, f0, REST_Z - 0.04), (x, f0 + 0.07, REST_Z - 0.04), BR, 'lozenge', rnd=False)
            fl = REST_F[0] + 0.1 if q == 0 else REST_F[1] - 0.1
            prism(f'rest_leg_{s}{q}', rect(0.075, 0.06), (x, fl, REST_Z - 0.07), (x + s * 0.03, fl, 0.0), LAC, 'plain', scale_b=1.25, rnd=False)
        # hand: a slim palm on the armrest, four joined fingers curling over its end, a thumb laid beside them
        spheroid(f'palm_{s}', hc, (0.045, 0.062, 0.02), SKIN, 'plain', sg=(8, 5))
        if lv < 2:
            for q, dx in enumerate((-0.027, -0.009, 0.009, 0.027)):
                L = FINGER * (1.0 - 0.1 * abs(q - 1.4)); k0 = (hc[0] + dx, hc[1] + 0.04, hc[2] + 0.002); k1 = (hc[0] + dx, hc[1] + 0.04 + L * 0.55, hc[2] - 0.006); k2 = (hc[0] + dx, hc[1] + 0.04 + L * 0.95, hc[2] - 0.05)
                if detail:
                    prism(f'finger_{s}{q}a', ngon(0.0125, 4, math.pi / 4), k0, k1, SKIN, 'plain', scale_b=0.9, rnd=True, up=(0, 0, 1))
                    prism(f'finger_{s}{q}b', ngon(0.0112, 4, math.pi / 4), k1, k2, SKIN, 'plain', scale_b=0.7, rnd=True, up=(0, 0, 1))
                else: prism(f'finger_{s}{q}', ngon(0.0125, 4, math.pi / 4), k0, k2, SKIN, 'plain', scale_b=0.65, rnd=True, up=(0, 0, 1))
            t0 = (hc[0] - s * 0.04, hc[1] - 0.005, hc[2]); t1 = (hc[0] - s * 0.05, hc[1] + 0.06, hc[2] - 0.004)
            prism(f'thumb_{s}', ngon(0.014, 4, math.pi / 4), t0, t1, SKIN, 'plain', scale_b=0.7, rnd=True, up=(0, 0, 1))
    # head: a woman's face in simple planes (brow, nose bridge, cheeks, jaw and chin, cinnabar lips), ears with jade drops, closed
    # lash lines, hair with cheek locks
    spheroid('head', HEAD_C, HEAD_R, SKIN, 'plain', sg=(14, 9))
    spheroid('jaw', (0.0, 0.07, CHIN_Z + 0.04), (0.068, 0.062, 0.052), SKIN, 'plain', sg=(10, 6))
    prism('nose', blade(0.034, 0.042), (0.0, head_f(EYE_Z + 0.02) - 0.016, EYE_Z + 0.02), (0.0, head_f(NOSE_Z) + 0.022, NOSE_Z), SKIN, 'plain', scale_b=1.2, rnd=True, up=(0, 1, 0.3))
    spheroid('brow', (0.0, head_f(EYE_Z + 0.032) - 0.014, EYE_Z + 0.032), (0.078, 0.022, 0.015), SKIN, 'plain', sg=(8, 4))
    for s in (-1, 1): spheroid(f'cheek_{s}', (s * 0.05, head_f(1.398, 0.05) - 0.02, 1.398), (0.036, 0.03, 0.034), SKIN, 'plain', sg=(8, 5))
    fl = head_f(LIPS_Z)
    spheroid('lip_up', (0.0, fl - 0.004, LIPS_Z + 0.008), (0.03, 0.016, 0.008), LIPS_MAT, 'plain', sg=(8, 4))
    spheroid('lip_low', (0.0, fl - 0.006, LIPS_Z - 0.007), (0.024, 0.016, 0.009), LIPS_MAT, 'plain', sg=(8, 4))
    for s in (-1, 1):
        spheroid(f'ear_{s}', (s * 0.103, 0.005, 1.43), (0.013, 0.026, 0.036), SKIN, 'plain', sg=(6, 4))
        if lv < 2:
            fe = head_f(EYE_Z, 0.045)
            prism(f'lash_{s}', rect(0.036, 0.006), (s * 0.026, fe + 0.004, EYE_Z + 0.002), (s * 0.066, fe - 0.008, EYE_Z - 0.003), BLACK, 'plain', rnd=True, up=(0, 1, 0))
            prism(f'brow_{s}', rect(0.04, 0.007), (s * 0.022, head_f(EYE_Z + 0.03, 0.03) + 0.004, EYE_Z + 0.028), (s * 0.07, head_f(EYE_Z + 0.03, 0.06) - 0.002, EYE_Z + 0.036), BLACK, 'plain', rnd=True, up=(0, 1, 0))
            spheroid(f'ear_drop_{s}', (s * 0.108, 0.005, 1.375), (0.013, 0.013, 0.02), JADE, 'plain', sg=(6, 4))
            prism(f'lock_{s}', rect(0.022, 0.03), (s * 0.099, 0.075, 1.49), (s * 0.088, 0.088, 1.325), BLACK, 'plain', scale_b=0.6, rnd=True, up=(s, 0.4, 0))
    spheroid('hair', (0.0, -0.005, 1.48), (0.116, 0.135, 0.135), BLACK, 'plain', sg=(14, 8))
    spheroid('hair_back', (0.0, -0.19, 1.565), (0.092, 0.11, 0.09), BLACK, 'plain', sg=(8, 5))
    # the high coiled bun behind the crown, two gold hairpins through it with jade drops showing beside the crown
    spheroid('bun', BUN_C, BUN_R, BLACK, 'plain', sg=(10, 6))
    torus('bun_coil', (BUN_C[0], BUN_C[1], BUN_C[2] + 0.01), (0, 0.5, 1), 0.085, 0.034, BLACK, 'plain', sg=(10, 4))
    spheroid('bun_top', (0.0, BUN_C[1] - 0.02, BUN_C[2] + 0.10), (0.066, 0.062, 0.06), BLACK, 'plain', sg=(8, 5))
    for s in (-1, 1):
        a = (-s * PIN_SPAN, BUN_C[1], BUN_C[2] - 0.05); b = (s * PIN_SPAN, BUN_C[1] - 0.01, BUN_C[2] + 0.09)
        prism(f'hairpin_{s}', ngon(0.012, 5), a, b, GOLD, 'plain', rnd=True)
        prism(f'pin_head_{s}', ngon(0.034, 6), b, (b[0] + s * 0.03, b[1], b[2] + 0.012), GOLD, 'plain', scale_b=0.6, rnd=True)
        if lv < 2:
            prism(f'pin_cord_{s}', rect(0.008, 0.008), (b[0] + s * 0.01, b[1], b[2]), (b[0] + s * 0.01, b[1], b[2] - 0.11), GOLD, 'plain', rnd=True, up=(s, 0, 0))
            spheroid(f'pin_drop_{s}', (b[0] + s * 0.01, b[1], b[2] - 0.125), (0.016, 0.016, 0.022), JADE, 'plain', sg=(6, 4))
    # the crown: a gold cap, a short thin board (black border, gold inlay field, gold edge, cinnabar underside), three gold cloud
    # points behind and a small gold phoenix in front on top
    lathe('cap', [(0.10, 1.555), (0.108, 1.60), (0.104, 1.642), (0.0, 1.642)], GOLD, 'plain', n=12)
    lathe('cap_band', [(0.111, 1.568), (0.113, 1.59)], CIN, 'plain', n=12)
    arc = [(BOARD_HW * math.cos(k * math.pi / 8), -BOARD_ARC - BOARD_HW * math.sin(k * math.pi / 8)) for k in range(9)]
    prof = [(-BOARD_HW, BOARD_REAR), (BOARD_HW, BOARD_REAR)] + arc
    for nm, mat, z0, z1, k in (('board_top', LAC, 0.0, 0.016, 1.0), ('board_field', GOLD, 0.014, 0.021, 0.8), ('board_edge', GOLD, -0.012, 0.0, 1.05), ('board_under', CIN, -0.024, -0.012, 0.985)):
        a = (BOARD_C[0], BOARD_C[1] + z0 * math.sin(TIP), BOARD_C[2] + z0 * math.cos(TIP)); b = (BOARD_C[0], BOARD_C[1] + z1 * math.sin(TIP), BOARD_C[2] + z1 * math.cos(TIP))
        prism(nm, [(p0 * k, p1 * k) for p0, p1 in prof], a, b, mat, 'plain', rnd=nm == 'board_field')
    for q, (x, w, h) in enumerate(((0.0, 0.12, 0.17), (-0.115, 0.09, 0.12), (0.115, 0.09, 0.12))):  # cloud points
        c = board_pt(x, 0.13, 0.016); pr = [(-w * 0.3, 0.0), (w * 0.3, 0.0), (w * 0.62, h * 0.55), (w * 0.3, h * 0.82), (0.0, h), (-w * 0.3, h * 0.82), (-w * 0.62, h * 0.55)]
        prism(f'cloud_{q}', pr, (c[0], c[1] - 0.009, c[2]), (c[0], c[1] + 0.009, c[2]), GOLD, 'plain', rnd=True)
    if lv < 2:  # phoenix: body, raised head, two swept wings, three tail plumes
        c = board_pt(0.0, -0.09, 0.05)
        spheroid('phx_body', c, (0.03, 0.05, 0.03), GOLD, 'plain', sg=(6, 4))
        prism('phx_neck', ngon(0.013, 4), (c[0], c[1] + 0.035, c[2] + 0.01), (c[0], c[1] + 0.07, c[2] + 0.075), GOLD, 'plain', rnd=True)
        prism('phx_beak', blade(0.022, 0.018), (c[0], c[1] + 0.065, c[2] + 0.078), (c[0], c[1] + 0.12, c[2] + 0.06), GOLD, 'plain', scale_b=0.15, rnd=True, up=(0, 0, 1))
        for s in (-1, 1): prism(f'phx_wing_{s}', blade(0.06, 0.012), (c[0] + s * 0.015, c[1], c[2] + 0.01), (c[0] + s * 0.15, c[1] - 0.07, c[2] + 0.075), GOLD, 'plain', scale_b=0.2, rnd=True, up=(0, 0.3, 1))
        for k in (-1, 0, 1): sweep(f'phx_tail_{k}', [(c[0], c[1] - 0.04, c[2] + 0.01), (c[0] + k * 0.05, c[1] - 0.11, c[2] + 0.09 + 0.02 * (k == 0)), (c[0] + k * 0.1, c[1] - 0.2, c[2] + 0.11 + 0.05 * (k == 0))], [0.014, 0.014, 0.0], GOLD, 'plain', n=4, flat=(1.0, 0.4))
    # bead strings: a thin cord with small jade beads, the last bead gold; twelve in front (three groups, each sways on its own bone)
    # to the nose, twelve short ones behind
    front, back = string_tops()
    for tops, L, nb, tag in ((front, STR_LEN, STR_BEADS, 'f'), (back, STR_LEN_B, STR_BEADS_B, 'b')):
        for k, top in enumerate(tops):
            PK.bone(f'beads_f{k * 3 // STRINGS}' if tag == 'f' else 'beads_b')
            upv = (top[0], 0.3 if tag == 'f' else -0.3, 0)
            if lv == 2:  # far: one flat strip per three strings
                if k % 3 == 1: prism(f'strip_{tag}{k}', rect(0.085, 0.012), top, (top[0], top[1], top[2] - L), JADE, 'plain', rnd=True, up=upv)
                continue
            w = CORD_W if detail else CORD_W * 2.2
            prism(f'cord_{tag}{k}', rect(w, w), top, (top[0], top[1], top[2] - L), JADE, 'plain', rnd=True, up=upv)
            if detail:
                for j in range(nb):
                    last = j == nb - 1
                    spheroid(f'bead_{tag}{k}_{j}', (top[0], top[1], top[2] - BEAD_0 - j * BEAD_PITCH), (BEAD_R * (1.3 if last else 1.0),) * 3, GOLD if last else JADE, 'plain', sg=(5, 3))
    PK.bone('root')


def bones():
    front, back = string_tops(); out = [('root', (0, 0, 0), (0, 0, 0.3), None)]; n = STRINGS // 3
    for g in range(3):
        grp = front[g * n:(g + 1) * n]; c = [sum(p[i] for p in grp) / len(grp) for i in range(3)]
        out.append((f'beads_f{g}', tuple(c), (c[0], c[1], c[2] - STR_LEN), 'root'))
    c = [sum(p[i] for p in back) / len(back) for i in range(3)]
    out.append(('beads_b', tuple(c), (c[0], c[1], c[2] - STR_LEN_B), 'root'))
    return out

def clips(arm):
    tau = math.tau; rot = {}
    for g in range(3):
        ph = g * 0.17
        rot[f'beads_f{g}'] = PK.wave(IDLE_S, 8, lambda p, ph=ph: [((1, 0, 0), SWAY_F[0] * math.sin(tau * (p + ph))), ((0, 1, 0), SWAY_F[1] * math.sin(tau * (p + ph) + 1.3))])
    rot['beads_b'] = PK.wave(IDLE_S, 8, lambda p: [((1, 0, 0), -SWAY_B * math.sin(tau * (p + 0.1)))])
    return [(PK.clip(arm, 'idle', rot), IDLE_S, 'beads_f1', SWAY_MIN)]

def count(ob, mats, test):
    """faces of the named materials whose centre (x, f, z) passes test."""
    names = [m.name for m in ob.data.materials]
    return sum(1 for p in ob.data.polygons if names[p.material_index] in mats and test(p.center.x, -p.center.y, p.center.z))

def gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(K.tris(l0) >= TRIS_MIN, f'kaymuse_lod0 tris {K.tris(l0)} (min {TRIS_MIN}: face, hands, bead strings and folds modelled)')
    d = SEAT_Z[1] - SEAT_Z[0]
    G(x1 - x0 <= 2 * SEAT_HW and -y0 <= d / 2 and y1 <= d / 2 and -0.02 < z0 < 0.01,
      f'kaymuse sits within the throne seat: {x1 - x0:.2f} m wide (seat {2 * SEAT_HW:.2f}), f {-y1:.2f}..{-y0:.2f} m (seat half depth {d / 2:.2f}), base z {z0:.2f}')
    G(1.5 <= z1 <= 2.1, f'kaymuse crown top {z1:.2f} m over the seat (range 1.5-2.1; a suit stands 2.05-2.4 m)')
    # round 3 (owner 14:13: she is a woman; lead: a modelled lower face under the strings): the round 2 'dark head' gate is replaced
    front, back = string_tops(); span = max(t[0] for t in front) - min(t[0] for t in front); gap = STR_ARC_R * math.radians(STR_DEG) - 2 * BEAD_R; bot = front[STRINGS // 2][2] - STR_LEN
    G(len(front) == 12 and len(back) == 12 and span >= 2 * HEAD_R[0] and gap >= BEAD_R and BEAD_PITCH >= 3 * BEAD_R and LIPS_Z + 0.02 <= bot <= EYE_Z - 0.03,
      f'kaymuse 冕 veil: {len(front)} + {len(back)} bead strings, front span {span:.2f} m (head {2 * HEAD_R[0]:.2f}), {gap * 100:.1f} cm clear between strings, ends at z {bot:.3f}: below the eyes ({EYE_Z}) and above the lips ({LIPS_Z})')
    lips = count(l0, (CIN,), lambda x, f, z: abs(x) < 0.04 and f > 0.1 and LIPS_Z - 0.02 < z < LIPS_Z + 0.02)
    chin = count(l0, (SKIN,), lambda x, f, z: f > 0.05 and z < CHIN_Z + 0.03 and z > CHIN_Z - 0.02 and abs(x) < 0.07)
    ears = count(l0, (SKIN,), lambda x, f, z: abs(x) > 0.1 and 1.39 < z < 1.47)
    locks = count(l0, (BLACK,), lambda x, f, z: abs(x) > 0.08 and f > 0.06 and 1.32 < z < 1.48)
    G(min(lips, chin, ears, locks) > 0, f'kaymuse lower face modelled: {lips} lip faces in cinnabar, {chin} chin faces, {ears} ear faces, {locks} cheek-lock faces (no blank head from any side)')
    sh = max(t[2] for t in TORSO); wa = min(t[2] for t in TORSO[:2]); hem = SKIRT[1][2]
    bun_top = BUN_C[2] + 0.10 + 0.06; board_rear_z = BOARD_C[2] + BOARD_REAR * math.sin(TIP) + 0.02
    G(sh <= 0.37 and wa <= 0.75 * sh and hem >= 3.0 * sh and bun_top > board_rear_z and PIN_SPAN > BOARD_HW + 0.05 and SASH_Z[1] - SASH_Z[0] >= 0.15,
      f'kaymuse reads as a woman: shoulders {2 * sh:.2f} m, waist {wa / sh:.0%} of them under a {(SASH_Z[1] - SASH_Z[0]) * 100:.0f} cm sash, hem {hem / sh:.1f} x the shoulders, bun top {bun_top:.2f} m over the board rear {board_rear_z:.2f}, hairpins {2 * PIN_SPAN:.2f} m past the {2 * BOARD_HW:.2f} m board')
    L = BOARD_REAR + BOARD_ARC + BOARD_HW; G(L <= 0.6 and count(l0, (GOLD,), lambda x, f, z: z > BOARD_C[2] + 0.06 and abs(x) < 0.25 and -0.3 < f < 0.3) > 20,
      f'kaymuse crown: board {L:.2f} m long (max 0.6: not a block) x {2 * BOARD_HW:.2f} m, gold cloud points and phoenix above it')
    hands = count(l0, (SKIN,), lambda x, f, z: abs(x) > 0.8 and f > 0.4 and z < 0.6)
    G(hands >= 40, f'kaymuse hands on the armrests: {hands} skin faces (palms, fingers, thumbs)')
    m = K.mats(l0); G({ROBE, CIN, GOLD, JADE, WHITE, BLACK, SKIN} <= m, f'kaymuse materials {sorted(m)} (black robe, cinnabar, gold, white inner layer, hair, skin)')
    G({CIN, GOLD, WHITE, SKIN} <= K.mats(l1) and {GOLD, WHITE} <= K.mats(l2), 'kaymuse LOD1 keeps cinnabar, gold, the white layer and skin; LOD2 keeps gold and white')


if __name__ == '__main__':
    seat = [0.0, SEAT_Y, (SEAT_Z[0] + SEAT_Z[1]) / 2]
    PK.build_rigged('kaymuse', build, bones(), clips, OUT, BUDGET, 4.0, extras={'seat': seat, 'clips': 'idle'}, extra_gates=gates)
    sys.exit(0)
