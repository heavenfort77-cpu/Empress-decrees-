# Empress Kaymuse, seated (PIECES round 1; owner 25 Nov 13:08 and 13:1x: a human empress in black Qin court robes with a 冕 crown whose
# bead curtain hides the face; lead pick: no face is modelled, faces failed review twice). Replaces the two cream boxes on the throne.
# Own design from the research rule list (Qin black = court dress and lacquer only; cinnabar = the one warm accent; gold inlay lines):
# she sits the Qin way, kneeling on the couch (no chair legs), so the robe pools into a wide base; a black upper robe with a cinnabar
# knee panel (蔽膝) and hem band, gold hem and belt, a crossed collar closing to her right (右衽) over a white inner collar; huge sleeves
# lying over her own two low lacquer armrests (凭几) -- the throne couch is 4.06 m wide, its own arms are out of a sitter's reach; the 冕:
# a board black above and cinnabar below, round in front and square behind, tipped forward, twelve jade bead strings round the front arc
# (they stand in front of the blank head) and eight behind, a jade hairpin, cinnabar cords. Silhouette: a flat board over a wide triangle.
# Scale: about 1.3 x a suit (guess, lead to judge): she is seen from 15 m and more on a 1.5 m dais; crown top 1.7 m over the seat.
# Model origin = the middle of her seat place; extras 'seat' = where that sits in throne_dais.glb (three.js x, y, z).
# Clip 'idle' (4 s loop): the three front bead groups and the back curtain sway. LOD0 skinned (rigid), LOD1 / LOD2 static.
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
# LOD0 floor (task: about 6k: the bead curtain and the robe folds are modelled, not painted).
TRIS_MIN = 5000
# Throne seat in throne_dais.glb (measured from the GLB): top y, half width x, front z and back z (three.js axes), m.
SEAT_Y, SEAT_HW, SEAT_Z = 2.16, 2.03, (-1.75, 0.07)
# Lower robe sections (z, centre f, half width, half depth), m: pooled hem to the waist.
SKIRT = [(0.0, 0.10, 1.00, 0.66), (0.06, 0.10, 1.02, 0.68), (0.20, 0.08, 0.86, 0.58), (0.40, 0.04, 0.60, 0.42), (0.58, 0.0, 0.40, 0.29), (0.66, 0.0, 0.36, 0.26)]
# Roundness of the robe sections (2 = ellipse, higher = squarer).
SKIRT_N = 3.2
# Upper robe sections (z, centre f, half width, half depth), m: waist, chest, shoulders, neck root.
TORSO = [(0.60, 0.0, 0.37, 0.27), (0.72, -0.01, 0.39, 0.27), (0.95, -0.02, 0.45, 0.26), (1.10, -0.02, 0.47, 0.24), (1.18, -0.02, 0.40, 0.21), (1.23, -0.02, 0.20, 0.15)]
# Fold ridges round the lower robe: count each side of the front, degrees between them, ridge width and height m.
PLEATS, PLEAT_DEG, PLEAT_W, PLEAT_T = 6, 15, 0.10, 0.055
# Sleeve path from the shoulder to the mouth (x outward, f, z) and the section radius at each point, m.
SLEEVE = [(0.40, -0.02, 1.08), (0.60, 0.0, 0.90), (0.82, 0.04, 0.68), (1.06, 0.10, 0.50), (1.22, 0.14, 0.42)]
SLEEVE_R = [0.15, 0.20, 0.28, 0.33, 0.34]
# How far the sleeve's centre line drops below the arm per metre of added radius (the cloth hangs under the arm).
SLEEVE_DROP = 0.4
# Armrest (凭几): x of the bar, its f range, top height, m.
REST_X, REST_F, REST_Z = 0.98, (-0.38, 0.52), 0.42
# Head centre and radii (x, f, z), m; no face is modelled.
HEAD_C, HEAD_R = (0.0, 0.02, 1.42), (0.13, 0.145, 0.17)
# 冕 board: centre, half width, rear length, front arc centre offset and radius, forward tip deg, m.
BOARD_C, BOARD_HW, BOARD_REAR, BOARD_ARC, BOARD_TIP = (0.0, 0.03, 1.66), 0.23, 0.36, 0.13, 8
# Bead strings: front count, arc radius they hang on m, degrees between strings, beads per string, bead radius and pitch m.
BEADS_F, BEAD_ARC_R, BEAD_DEG, BEAD_N, BEAD_R, BEAD_PITCH = 12, 0.215, 12, 7, 0.023, 0.043
# Back curtain: strings, beads per string.
BEADS_B, BEAD_BN = 8, 4
# Face cover gate: share of the head's front (seen level from the front) that the front beads cover, min.
COVER_MIN = 0.55
# Idle clip: seconds, front sway deg (fore-aft, sideways), back sway deg, min bead travel m.
IDLE_S, SWAY_F, SWAY_B, SWAY_MIN = 4.0, (5.0, 2.0), 3.0, 0.01
ROBE, CIN, GOLD, JADE, SKIN, LAC, BR = 'kmRobe', 'palCinnabar', 'palGold', 'kmJade', 'kmSkin', 'palLacquerPlain', 'palBronze'
PK.mutate(globals())
TIP = math.radians(BOARD_TIP)


def lerp_secs(secs, z):
    for a, b in zip(secs, secs[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return [a[i] + (b[i] - a[i]) * k for i in range(4)]
    return list(secs[-1] if z > secs[-1][0] else secs[0])

def robe_pt(secs, a_deg, z, out=0.0):
    """a point on the robe's surface: a_deg from the front (positive toward +x), height z, pushed outward by out."""
    _, cf, hw, hd = lerp_secs(secs, z); a = math.radians(a_deg); s, c = math.sin(a), math.cos(a); e = 2 / SKIRT_N
    return ((hw + out) * math.copysign(abs(s) ** e, s), cf + (hd + out) * math.copysign(abs(c) ** e, c), z)

def board_pt(p0, p1, dz=0.0):
    """board-local (across, toward the rear) -> design point on the tipped board."""
    return (BOARD_C[0] - p0, BOARD_C[1] - p1 * math.cos(TIP), BOARD_C[2] + p1 * math.sin(TIP) + dz)

def bead_tops():
    """(x, f, z) where each front string hangs from the board's front arc, and each back string from the rear edge."""
    front = []
    for k in range(BEADS_F):
        ph = math.radians((k - (BEADS_F - 1) / 2) * BEAD_DEG)
        front.append(board_pt(BEAD_ARC_R * math.sin(ph), -BOARD_ARC - BEAD_ARC_R * math.cos(ph), -0.035))
    back = [board_pt((k - (BEADS_B - 1) / 2) * 0.052, BOARD_REAR - 0.02, -0.035) for k in range(BEADS_B)]
    return front, back


def build(detail):
    PK.bone('root')
    # lower robe: a wide pooled base rising to the waist; gold hem, cinnabar band above it
    loft('skirt', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in SKIRT], ROBE, 'tile2', n_exp=SKIRT_N, M=32)
    loft('hem_gold', [(0.0, 0.10, 1.03, 0.69, 0.0), (0.05, 0.10, 1.036, 0.696, 0.0)], GOLD, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    loft('hem_cin', [(0.05, 0.10, 1.034, 0.694, 0.0), (0.115, 0.094, 0.972, 0.652, 0.0)], CIN, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    # carved fold ridges fanning from the waist to the hem (sharp, not painted)
    zs = (0.62, 0.42, 0.22, 0.12) if detail else (0.62, 0.22, 0.12)
    for i in range(-PLEATS, PLEATS + 1):
        if i == 0: continue
        for j, (z0, z1) in enumerate(zip(zs, zs[1:])):
            a0 = i * PLEAT_DEG * (0.75 + 0.25 * (0.62 - z0) / 0.5); a1 = i * PLEAT_DEG * (0.75 + 0.25 * (0.62 - z1) / 0.5)
            w = PLEAT_W * (0.55 + 0.9 * (0.62 - z0)); k = (0.55 + 0.9 * (0.62 - z1)) / (0.55 + 0.9 * (0.62 - z0))
            n = (math.sin(math.radians(a0)), math.cos(math.radians(a0)), 0.45)
            prism(f'pleat_{i}_{j}', blade(w, PLEAT_T), robe_pt(SKIRT, a0, z0), robe_pt(SKIRT, a1, z1), ROBE, 'tile2', scale_b=k, rnd=True, up=n)
    # 蔽膝 knee panel: cinnabar, gold edge lines, down the front over the lap
    bz = (0.62, 0.42, 0.22, 0.125)
    for j, (z0, z1) in enumerate(zip(bz, bz[1:])):
        w0 = 0.26 + 0.34 * (0.62 - z0); w1 = 0.26 + 0.34 * (0.62 - z1)
        prism(f'bixi_{j}', rect(w0, 0.03), robe_pt(SKIRT, 0, z0, 0.03), robe_pt(SKIRT, 0, z1, 0.03), CIN, 'plain', scale_b=w1 / w0, rnd=False, up=(0, 1, 0.5))
        for s in (-1, 1):
            a, b = robe_pt(SKIRT, 0, z0, 0.05), robe_pt(SKIRT, 0, z1, 0.05)
            prism(f'bixi_edge_{j}{s}', rect(0.03, 0.02), (s * w0 / 2, a[1], a[2]), (s * w1 / 2, b[1], b[2]), GOLD, 'plain', rnd=True, up=(0, 1, 0.5))
    if detail:  # three gold bars across the panel: an invented court mark, no readable script
        for z in (0.50, 0.36, 0.24):
            c = robe_pt(SKIRT, 0, z, 0.052); w = 0.12 + 0.3 * (0.62 - z)
            prism(f'bixi_bar_{z}', rect(0.035, 0.016), (-w / 2, c[1], c[2]), (w / 2, c[1], c[2]), GOLD, 'plain', rnd=True, up=(0, 1, 0.5))
    # upper robe, the belt with its bronze hook, jade pendants at the hips
    loft('torso', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in TORSO], ROBE, 'tile2', n_exp=3.0, M=24)
    loft('belt', [(0.615, 0.0, 0.392, 0.292, 0.0), (0.71, -0.008, 0.405, 0.288, 0.0)], GOLD, 'plain', n_exp=3.0, M=24, cap=False)
    prism('belt_hook', ngon(0.045, 6), (0.0, 0.285, 0.662), (0.0, 0.315, 0.662), BR, 'mark', rnd=False)
    if detail:
        for s in (-1, 1):
            prism(f'pend_cord_{s}', rect(0.022, 0.012), (s * 0.34, 0.20, 0.62), (s * 0.47, 0.44, 0.30), CIN, 'plain', rnd=True, up=(s, 1, 0.6))
            prism(f'pend_{s}', ngon(0.05, 6), (s * 0.47, 0.435, 0.30), (s * 0.485, 0.455, 0.29), JADE, 'plain', rnd=True)
            prism(f'pend_drop_{s}', blade(0.05, 0.016), (s * 0.48, 0.45, 0.26), (s * 0.52, 0.52, 0.14), JADE, 'plain', scale_b=0.3, rnd=True, up=(s, 1, 0.6))
    # crossed collar: the outer cinnabar band runs from her left shoulder to her right waist (右衽); white inner collar under it
    prism('collar_out', rect(0.085, 0.035), (0.14, 0.165, 1.205), (-0.19, 0.275, 0.73), CIN, 'plain', rnd=False, up=(0, 1, 0.25))
    prism('collar_in', rect(0.07, 0.03), (-0.13, 0.16, 1.205), (0.035, 0.24, 0.95), JADE, 'plain', rnd=False, up=(0, 1, 0.25))
    if detail: prism('collar_gold', rect(0.02, 0.02), (0.185, 0.175, 1.20), (-0.145, 0.288, 0.73), GOLD, 'plain', rnd=True, up=(0, 1, 0.25))
    lathe('neck', [(0.115, 1.19), (0.10, 1.29)], JADE, 'plain', n=10, cf=0.0)
    # sleeves: faceted hanging masses from the shoulder over the armrest; cinnabar lining and a gold rim at the mouth
    for s in (-1, 1):
        pts = [(s * x, f, z - (r - SLEEVE_R[0]) * SLEEVE_DROP) for (x, f, z), r in zip(SLEEVE, SLEEVE_R)]
        sweep(f'sleeve_{s}', pts, SLEEVE_R, ROBE, 'tile2', n=8, flat=(1.0, 0.5), side=(0, 0, 1))
        e0, e1 = pts[-2], pts[-1]; d = [(e1[i] - e0[i]) for i in range(3)]; L = math.sqrt(sum(c * c for c in d)); d = [c / L for c in d]
        m0 = tuple(e1[i] - d[i] * 0.02 for i in range(3)); m1 = tuple(e1[i] + d[i] * 0.035 for i in range(3)); m2 = tuple(e1[i] + d[i] * 0.05 for i in range(3))
        sweep(f'sleeve_rim_{s}', [m0, m1], [SLEEVE_R[-1] + 0.012] * 2, GOLD, 'plain', n=8, flat=(1.0, 0.5), side=(0, 0, 1), cap=False)
        sweep(f'sleeve_lin_{s}', [m0, m2], [SLEEVE_R[-1] - 0.03, SLEEVE_R[-1] - 0.05], CIN, 'plain', n=8, flat=(1.0, 0.5), side=(0, 0, 1))
        if detail:  # two fold ridges along the top of the sleeve
            for q, off in enumerate((0.05, -0.04)):
                prism(f'sleeve_fold_{s}{q}', blade(0.09, 0.05), (pts[1][0], pts[1][1] + off + 0.02, pts[1][2] + SLEEVE_R[1] * 0.82),
                      (pts[3][0], pts[3][1] + off * 2.2 + 0.02, pts[3][2] + SLEEVE_R[3] * 0.8), ROBE, 'tile2', scale_b=1.5, rnd=True, up=(0, 0.4 if off > 0 else -0.4, 1))
        # armrest: a black lacquer bar on two legs, bronze end caps (the sleeve lies over its middle)
        x = s * REST_X
        prism(f'rest_{s}', rect(0.11, 0.075), (x, REST_F[0], REST_Z - 0.04), (x, REST_F[1], REST_Z - 0.04), LAC, 'plain', rnd=False)
        for q, f in enumerate(REST_F):
            f0 = f - 0.01 if q == 0 else f - 0.06
            prism(f'rest_cap_{s}{q}', rect(0.13, 0.095), (x, f0, REST_Z - 0.04), (x, f0 + 0.07, REST_Z - 0.04), BR, 'lozenge', rnd=False)
            fl = REST_F[0] + 0.1 if q == 0 else REST_F[1] - 0.1
            prism(f'rest_leg_{s}{q}', rect(0.075, 0.06), (x, fl, REST_Z - 0.07), (x + s * 0.03, fl, 0.0), LAC, 'plain', scale_b=1.25, rnd=False)
            if detail: prism(f'rest_line_{s}{q}', rect(0.115, 0.012), (x, fl - 0.04, REST_Z - 0.012), (x, fl + 0.04, REST_Z - 0.012), CIN, 'plain', rnd=True)
    # head: blank (the beads stand in front of it), black hair, the crown's gold cap
    spheroid('head', HEAD_C, HEAD_R, SKIN, 'plain', sg=(12, 8))
    spheroid('hair', (0.0, -0.045, 1.455), (0.142, 0.15, 0.165), LAC, 'plain', sg=(12, 8))
    spheroid('bun', (0.0, -0.17, 1.36), (0.085, 0.07, 0.09), LAC, 'plain', sg=(8, 5))
    lathe('cap', [(0.118, 1.535), (0.126, 1.59), (0.122, 1.645), (0.0, 1.645)], GOLD, 'plain', n=12, cf=0.0)
    lathe('cap_band', [(0.13, 1.55), (0.132, 1.575)], CIN, 'plain', n=12, cf=0.0)
    # 冕 board: black above, gold edge, cinnabar below; round in front, square behind, tipped forward
    arc = [(BOARD_HW * math.cos(k * math.pi / 8), -BOARD_ARC - BOARD_HW * math.sin(k * math.pi / 8)) for k in range(9)]
    prof = [(-BOARD_HW, BOARD_REAR), (BOARD_HW, BOARD_REAR)] + arc
    for nm, mat, z0, z1, k in (('board_top', LAC, 0.0, 0.022, 1.0), ('board_edge', GOLD, -0.012, 0.0, 1.035), ('board_under', CIN, -0.026, -0.012, 0.985)):
        pr = [(p0 * k, (p1 - 0.0) * k) for p0, p1 in prof]
        a = (BOARD_C[0], BOARD_C[1] + z0 * math.sin(TIP), BOARD_C[2] + z0 * math.cos(TIP)); b = (BOARD_C[0], BOARD_C[1] + z1 * math.sin(TIP), BOARD_C[2] + z1 * math.cos(TIP))
        prism(nm, pr, a, b, mat, 'plain', rnd=False)
    # jade hairpin through the cap, cinnabar cords to the chin, jade ear drops
    prism('pin', ngon(0.013, 6), (-0.34, 0.0, 1.60), (0.34, 0.0, 1.60), JADE, 'plain', rnd=True)
    for s in (-1, 1):
        prism(f'cord_{s}', rect(0.02, 0.012), (s * 0.15, 0.01, 1.595), (s * 0.115, 0.09, 1.25), CIN, 'plain', rnd=True, up=(s, 0.3, 0))
        if detail: spheroid(f'ear_drop_{s}', (s * 0.165, 0.03, 1.40), (0.026, 0.026, 0.034), JADE, 'plain', sg=(6, 4))
    # bead strings: jade, the last bead of each gold; the front twelve in three groups (each sways on its own bone), eight behind
    front, back = bead_tops()
    for k, top in enumerate(front):
        PK.bone(f'beads_f{k * 3 // BEADS_F}')
        if detail:
            for j in range(BEAD_N):
                spheroid(f'bead_f{k}_{j}', (top[0], top[1], top[2] - BEAD_R - j * BEAD_PITCH), (BEAD_R,) * 3, GOLD if j == BEAD_N - 1 else JADE, 'plain', sg=(6, 4))
        elif k % 2 == 0:  # low LOD: one flat jade strip per two strings
            nx = front[k + 1]; mx = ((top[0] + nx[0]) / 2, (top[1] + nx[1]) / 2, (top[2] + nx[2]) / 2); w = math.dist(top[:2], nx[:2]) * 1.9
            prism(f'strip_f{k}', rect(w, 0.014), mx, (mx[0], mx[1], mx[2] - BEAD_N * BEAD_PITCH), JADE, 'plain', rnd=True, up=(mx[0], mx[1] - 0.16, 0))
    PK.bone('beads_b')
    for k, top in enumerate(back):
        if detail:
            for j in range(BEAD_BN):
                spheroid(f'bead_b{k}_{j}', (top[0], top[1], top[2] - BEAD_R - j * BEAD_PITCH), (BEAD_R,) * 3, GOLD if j == BEAD_BN - 1 else JADE, 'plain', sg=(5, 3))
    if not detail:
        bx = (back[0][0] + back[-1][0]) / 2
        prism('strip_b', rect(BEADS_B * 0.052, 0.014), (bx, back[0][1], back[0][2]), (bx, back[0][1], back[0][2] - BEAD_BN * BEAD_PITCH), JADE, 'plain', rnd=True, up=(0, -1, 0))
    PK.bone('root')


def bones():
    front, back = bead_tops(); out = [('root', (0, 0, 0), (0, 0, 0.3), None)]
    for g in range(3):
        grp = front[g * 4:(g + 1) * 4]; c = [sum(p[i] for p in grp) / len(grp) for i in range(3)]
        out.append((f'beads_f{g}', tuple(c), (c[0], c[1], c[2] - BEAD_N * BEAD_PITCH), 'root'))
    c = [sum(p[i] for p in back) / len(back) for i in range(3)]
    out.append(('beads_b', tuple(c), (c[0], c[1], c[2] - BEAD_BN * BEAD_PITCH), 'root'))
    return out

def clips(arm):
    tau = math.tau; rot = {}
    for g in range(3):
        ph = g * 0.17
        rot[f'beads_f{g}'] = PK.wave(IDLE_S, 8, lambda p, ph=ph: [((1, 0, 0), SWAY_F[0] * math.sin(tau * (p + ph))), ((0, 1, 0), SWAY_F[1] * math.sin(tau * (p + ph) + 1.3))])
    rot['beads_b'] = PK.wave(IDLE_S, 8, lambda p: [((1, 0, 0), -SWAY_B * math.sin(tau * (p + 0.1)))])
    return [(PK.clip(arm, 'idle', rot), IDLE_S, 'beads_f1', SWAY_MIN)]

def cover():
    """share of the head's front disc (level view from the front) that lies behind a front bead."""
    front, _ = bead_tops(); cs = [(t[0], t[2] - BEAD_R - j * BEAD_PITCH) for t in front for j in range(BEAD_N)]
    n = hit = 0
    for i in range(41):
        for j in range(41):
            x = (i / 20 - 1) * HEAD_R[0]; z = HEAD_C[2] + (j / 20 - 1) * HEAD_R[2]
            if (x / HEAD_R[0]) ** 2 + ((z - HEAD_C[2]) / HEAD_R[2]) ** 2 > 1 or z > 1.535: continue
            n += 1; hit += any((x - cx) ** 2 + (z - cz) ** 2 <= BEAD_R ** 2 for cx, cz in cs)
    return hit / max(n, 1)

def gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(K.tris(l0) >= TRIS_MIN, f'kaymuse_lod0 tris {K.tris(l0)} (min {TRIS_MIN}: beads and folds modelled)')
    d = SEAT_Z[1] - SEAT_Z[0]
    G(x1 - x0 <= 2 * SEAT_HW and -y0 <= d / 2 and y1 <= d / 2 and -0.02 < z0 < 0.01,
      f'kaymuse sits within the throne seat: {x1 - x0:.2f} m wide (seat {2 * SEAT_HW:.2f}), f {-y1:.2f}..{-y0:.2f} m (seat half depth {d / 2:.2f}), base z {z0:.2f}')
    G(1.5 <= z1 <= 2.1, f'kaymuse crown top {z1:.2f} m over the seat (range 1.5-2.1; a suit stands 2.05-2.4 m)')
    c = cover(); G(c >= COVER_MIN, f'kaymuse bead curtain covers {c:.0%} of the head front, level view (min {COVER_MIN:.0%}); no face modelled')
    m = K.mats(l0); G({ROBE, CIN, GOLD, JADE, LAC} <= m and SKIN in m, f'kaymuse materials {sorted(m)} (black robe, cinnabar, gold, jade, lacquer)')
    G({CIN, GOLD} <= K.mats(l1), 'kaymuse LOD1 keeps cinnabar and gold')


if __name__ == '__main__':
    seat = [0.0, SEAT_Y, (SEAT_Z[0] + SEAT_Z[1]) / 2]
    fails = PK.build_rigged('kaymuse', build, bones(), clips, OUT, BUDGET, 4.0, extras={'seat': seat, 'clips': 'idle'}, extra_gates=gates)
    sys.exit(0)
