# Empress Kaymuse, seated (PIECES round 2; owner 25 Nov 13:08 and 13:1x: a human empress in black Qin court robes with a 冕 crown whose
# bead curtain hides the face; lead pick: no face is modelled). Replaces the two cream boxes on the throne.
# Round 2 (lead verdict on run 45555140630: blank white head, a cage of bead balls, flat sleeves, stray collar chips, lost against the
# dark throne): the head, neck and hair are dark (nothing light near the head from any side); the 冕 board is longer front to back and
# carries twelve thin bead STRINGS in front and twelve behind (small beads on a cord, gaps between the cords); the collar is three
# layers laid ON the chest (white inner, cinnabar, gold edge) closing to her right (右衽); the sleeves are deep hanging masses with fold
# ridges, a cinnabar lining and a white inner sleeve at the mouth, and gold borders along their upper and lower edges; the skirt is wide
# and pleated over a white inner layer that shows at the floor, a gold-inlay hem and a cinnabar band. The light borders sit on the
# outline (hem, sleeve edges, sleeve mouths, board edge, bead strings) so she separates from the dark throne.
# Own design from the research rule list (Qin black = court dress and lacquer only; cinnabar = the one warm accent; gold inlay lines;
# wide contrasting borders on a robe's collar, cuffs and hem). She kneels on the couch the Qin way; her sleeves lie over her own two low
# lacquer armrests (凭几): the throne couch is 4.06 m wide, its own arms are out of a sitter's reach.
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
# LOD0 floor (task: about 6k: the bead strings and the robe folds are modelled, not painted).
TRIS_MIN = 5000
# Throne seat in throne_dais.glb (measured from the GLB): top y, half width x, front z and back z (three.js axes), m.
SEAT_Y, SEAT_HW, SEAT_Z = 2.16, 2.03, (-1.75, 0.07)
# Lower robe sections (z, centre f, half width, half depth), m: pooled hem to the waist.
SKIRT = [(0.0, 0.10, 1.00, 0.66), (0.06, 0.10, 1.02, 0.68), (0.20, 0.08, 0.86, 0.58), (0.40, 0.04, 0.60, 0.42), (0.58, 0.0, 0.40, 0.29), (0.66, 0.0, 0.36, 0.26)]
# Roundness of the robe sections (2 = ellipse, higher = squarer): skirt, torso.
SKIRT_N, TORSO_N = 3.2, 3.0
# White inner layer showing at the floor: how far it stands out past the black robe, m; its height m.
UNDER_OUT, UNDER_H = 0.085, 0.035
# Upper robe sections (z, centre f, half width, half depth), m: waist, chest, shoulders, neck root.
TORSO = [(0.60, 0.0, 0.37, 0.27), (0.72, -0.01, 0.39, 0.27), (0.95, -0.02, 0.45, 0.26), (1.10, -0.02, 0.47, 0.24), (1.18, -0.02, 0.40, 0.21), (1.23, -0.02, 0.20, 0.15)]
# Fold ridges round the lower robe: count each side of the front, degrees between them, ridge width and height m.
PLEATS, PLEAT_DEG, PLEAT_W, PLEAT_T = 6, 15, 0.10, 0.06
# Sleeve path from the shoulder to the mouth (x outward, f, z) and the section radius at each point, m.
SLEEVE = [(0.40, -0.02, 1.08), (0.60, 0.0, 0.90), (0.82, 0.04, 0.68), (1.06, 0.10, 0.50), (1.22, 0.14, 0.42)]
SLEEVE_R = [0.15, 0.21, 0.29, 0.34, 0.35]
# How far the sleeve's centre line drops below the arm per metre of added radius (the cloth hangs under the arm); section depth over height.
SLEEVE_DROP, SLEEVE_FLAT = 0.4, 0.62
# Gold border piping along the sleeve's upper and lower edges: radius m.
PIPE_R = 0.034
# Armrest (凭几): x of the bar, its f range, top height, m.
REST_X, REST_F, REST_Z = 0.98, (-0.38, 0.52), 0.42
# Head centre and radii (x, f, z), m; dark, no face modelled. HEAD_MAT is its material (a light one must fail the head gate).
HEAD_C, HEAD_R, HEAD_MAT = (0.0, 0.02, 1.42), (0.12, 0.135, 0.165), 'pcBlack'
# 冕 board: centre, half width, rear length, front arc centre offset and radius (= half width), forward tip deg, m.
BOARD_C, BOARD_HW, BOARD_REAR, BOARD_ARC, BOARD_TIP = (0.0, 0.0, 1.66), 0.23, 0.50, 0.22, 8
# Bead strings: count front and back (twelve each), arc radius the front ones hang on m, degrees between them, cord width m.
STRINGS, STR_ARC_R, STR_DEG, CORD_W = 12, 0.215, 10, 0.008
# Front strings: length m, beads per string, bead radius m, first bead and pitch m. Back strings: length, beads.
STR_LEN, STR_BEADS, BEAD_R, BEAD_0, BEAD_PITCH = 0.35, 6, 0.012, 0.045, 0.055
STR_LEN_B, STR_BEADS_B = 0.24, 4
# Idle clip: seconds, front sway deg (fore-aft, sideways), back sway deg, min string travel m.
IDLE_S, SWAY_F, SWAY_B, SWAY_MIN = 4.0, (5.0, 2.0), 3.0, 0.01
ROBE, CIN, GOLD, JADE, BLACK, LAC, BR = 'kmRobe', 'palCinnabar', 'palGold', 'kmJade', 'pcBlack', 'palLacquerPlain', 'palBronze'
# Light materials (the head gate: none of these within HEAD_CLEAR m of the head's axis between the collar and the cap).
LIGHT, HEAD_CLEAR = ('kmJade', 'kmSkin', 'palInlay'), 0.2
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
    back = [board_pt((k - (STRINGS - 1) / 2) * 0.0345, BOARD_REAR - 0.02, -0.03) for k in range(STRINGS)]
    return front, back

def sleeve_frame(s):
    """per sleeve point: (centre, up-in-the-hanging-plane unit vector, radius)."""
    pts = [(s * x, f, z - (r - SLEEVE_R[0]) * SLEEVE_DROP) for (x, f, z), r in zip(SLEEVE, SLEEVE_R)]; out = []
    for i, (p, r) in enumerate(zip(pts, SLEEVE_R)):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]; t = [b[j] - a[j] for j in range(3)]; L = math.sqrt(sum(c * c for c in t)); t = [c / L for c in t]
        u = [-t[2] * t[0], -t[2] * t[1], 1 - t[2] * t[2]]; L = math.sqrt(sum(c * c for c in u)); out.append((p, [c / L for c in u], r))
    return out

def band(name, path, w, t, mat, out):
    """a flat border laid on the upper robe along path [(a_deg, z)]."""
    pts = [robe_pt(TORSO, a, z, out, TORSO_N) for a, z in path]
    for j, (p, q) in enumerate(zip(pts, pts[1:])):
        a = math.radians(path[j][0]); prism(f'{name}_{j}', rect(w, t), p, q, mat, 'plain', rnd=True, up=(math.sin(a), math.cos(a), 0.35))


def build(detail):
    lv = PK.LEVEL['n']; PK.bone('root')
    # lower robe: white inner layer at the floor, the black pooled skirt, a gold-inlay hem and a cinnabar band above it
    loft('under', [(0.0, 0.10, SKIRT[0][2] + UNDER_OUT, SKIRT[0][3] + UNDER_OUT, 0.0), (UNDER_H, 0.10, SKIRT[0][2] + UNDER_OUT, SKIRT[0][3] + UNDER_OUT, 0.0)], JADE, 'plain', n_exp=SKIRT_N, M=32)
    loft('skirt', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in SKIRT], ROBE, 'tile2', n_exp=SKIRT_N, M=32)
    loft('hem_gold', [(UNDER_H, 0.10, 1.045, 0.705, 0.0), (0.115, 0.094, 0.99, 0.668, 0.0)], GOLD, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    loft('hem_cin', [(0.115, 0.094, 0.975, 0.655, 0.0), (0.17, 0.086, 0.915, 0.615, 0.0)], CIN, 'plain', n_exp=SKIRT_N, M=32, cap=False)
    # carved fold ridges fanning from the waist to the hem band
    zs = (0.62, 0.42, 0.26, 0.175) if detail else (0.62, 0.26, 0.175)
    for i in range(-PLEATS, PLEATS + 1):
        if i == 0 or (lv == 2 and i % 2): continue
        for j, (z0, z1) in enumerate(zip(zs, zs[1:])):
            a0 = i * PLEAT_DEG * (0.75 + 0.25 * (0.62 - z0) / 0.5); a1 = i * PLEAT_DEG * (0.75 + 0.25 * (0.62 - z1) / 0.5)
            w = PLEAT_W * (0.55 + 0.9 * (0.62 - z0)); k = (0.55 + 0.9 * (0.62 - z1)) / (0.55 + 0.9 * (0.62 - z0))
            n = (math.sin(math.radians(a0)), math.cos(math.radians(a0)), 0.45)
            prism(f'pleat_{i}_{j}', blade(w, PLEAT_T), robe_pt(SKIRT, a0, z0), robe_pt(SKIRT, a1, z1), ROBE, 'tile2', scale_b=k, rnd=True, up=n)
    # 蔽膝 knee panel: cinnabar with gold edge lines and one gold centre line, down the front over the lap
    bz = (0.62, 0.42, 0.26, 0.18)
    for j, (z0, z1) in enumerate(zip(bz, bz[1:])):
        w0 = 0.26 + 0.34 * (0.62 - z0); w1 = 0.26 + 0.34 * (0.62 - z1)
        prism(f'bixi_{j}', rect(w0, 0.03), robe_pt(SKIRT, 0, z0, 0.03), robe_pt(SKIRT, 0, z1, 0.03), CIN, 'plain', scale_b=w1 / w0, rnd=False, up=(0, 1, 0.5))
        a, b = robe_pt(SKIRT, 0, z0, 0.05), robe_pt(SKIRT, 0, z1, 0.05)
        for s in ((-1, 1, 0) if detail else (-1, 1)):
            prism(f'bixi_edge_{j}{s}', rect(0.03 if s else 0.018, 0.02), (s * w0 / 2, a[1], a[2]), (s * w1 / 2, b[1], b[2]), GOLD, 'plain', rnd=True, up=(0, 1, 0.5))
    # upper robe, the gold belt with its bronze hook
    loft('torso', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in TORSO], ROBE, 'tile2', n_exp=TORSO_N, M=24)
    loft('belt', [(0.615, 0.0, 0.392, 0.292, 0.0), (0.71, -0.008, 0.405, 0.288, 0.0)], GOLD, 'plain', n_exp=TORSO_N, M=24, cap=False)
    prism('belt_hook', ngon(0.045, 6), (0.0, 0.285, 0.662), (0.0, 0.315, 0.662), BR, 'mark', rnd=False)
    # layered crossed collar laid on the chest: her left border over her right (右衽): white inner collar, cinnabar border, gold edge
    T5 = [i / 4 for i in range(5)] if lv < 2 else [0.0, 0.5, 1.0]
    pa = [(38 - 70 * t, 1.165 - 0.445 * t) for t in T5]; pb = [(-38 + 33 * t, 1.165 - 0.25 * t) for t in T5]
    band('collar_b', pb, 0.08, 0.02, CIN, 0.004)
    band('collar_b_in', [(a + 10, z) for a, z in pb[:-1]], 0.05, 0.016, JADE, 0.002)
    band('collar_a', pa, 0.08, 0.026, CIN, 0.012)
    band('collar_a_in', [(a - 10, z) for a, z in pa[:len(pa) // 2 + 1]], 0.05, 0.02, JADE, 0.008)
    if detail: band('collar_a_gold', [(a + 7.5, z) for a, z in pa], 0.024, 0.02, GOLD, 0.022)
    lathe('neck', [(0.088, 1.19), (0.082, 1.31)], BLACK, 'plain', n=10)
    lathe('collar_stand_in', [(0.128, 1.19), (0.108, 1.255), (0.098, 1.255)], JADE, 'plain', n=12)
    lathe('collar_stand', [(0.155, 1.185), (0.132, 1.238), (0.122, 1.238)], CIN, 'plain', n=12)
    # sleeves: deep hanging masses over the armrests, fold ridges, gold borders on the upper and lower edges, cinnabar lining and a white
    # inner sleeve at the mouth
    for s in (-1, 1):
        fr = sleeve_frame(s); pts = [p for p, u, r in fr]
        sweep(f'sleeve_{s}', pts, SLEEVE_R, ROBE, 'tile2', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        e0, e1 = pts[-2], pts[-1]; d = [(e1[i] - e0[i]) for i in range(3)]; L = math.sqrt(sum(c * c for c in d)); d = [c / L for c in d]
        at = lambda k: tuple(e1[i] + d[i] * k for i in range(3)); R = SLEEVE_R[-1]
        sweep(f'sleeve_rim_{s}', [at(-0.03), at(0.012)], [R + 0.014] * 2, GOLD, 'plain', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        sweep(f'sleeve_lin_{s}', [at(-0.02), at(0.04)], [R - 0.012, R - 0.02], CIN, 'plain', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        sweep(f'sleeve_in_{s}', [at(-0.02), at(0.10)], [R - 0.045, R - 0.06], JADE, 'plain', n=10, flat=(1.0, SLEEVE_FLAT), side=(0, 0, 1))
        for q, sg in enumerate((1, -1)):  # gold borders: upper edge toward the back, lower edge toward the front (where the outline runs from the game camera)
            pp = [(p[0] + u[0] * 0.89 * r * sg, p[1] + u[1] * 0.89 * r * sg - sg * 0.28 * r, max(p[2] + u[2] * 0.89 * r * sg, PIPE_R + 0.004)) for p, u, r in fr]
            sweep(f'sleeve_pipe_{s}{q}', pp, [PIPE_R] * len(pp), GOLD, 'plain', n=5)
        if lv < 2:  # fold ridges fanning down the front of the sleeve
            for q, k in enumerate((0.5, 0.05, -0.4)):
                fp = []
                for i, (p, u, r) in enumerate(fr[1:]):
                    kk = k * (1 + 0.25 * i); df = SLEEVE_FLAT * r * math.sqrt(max(1 - kk * kk, 0.05)) * 0.97
                    fp.append((p[0] + u[0] * kk * r, p[1] + u[1] * kk * r + df, p[2] + u[2] * kk * r))
                for j, (a, b) in enumerate(zip(fp, fp[1:])):
                    if detail or j % 2 == 0: prism(f'sleeve_fold_{s}{q}{j}', blade(0.07 + 0.025 * j, 0.05), a, b, ROBE, 'tile2', scale_b=1.25, rnd=True, up=(0, 1, 0))
        # armrest: a black lacquer bar on two legs, bronze end caps (the sleeve lies over its middle)
        x = s * REST_X
        prism(f'rest_{s}', rect(0.11, 0.075), (x, REST_F[0], REST_Z - 0.04), (x, REST_F[1], REST_Z - 0.04), LAC, 'plain', rnd=False)
        for q, f in enumerate(REST_F):
            f0 = f - 0.01 if q == 0 else f - 0.06
            if lv < 2: prism(f'rest_cap_{s}{q}', rect(0.13, 0.095), (x, f0, REST_Z - 0.04), (x, f0 + 0.07, REST_Z - 0.04), BR, 'lozenge', rnd=False)
            fl = REST_F[0] + 0.1 if q == 0 else REST_F[1] - 0.1
            prism(f'rest_leg_{s}{q}', rect(0.075, 0.06), (x, fl, REST_Z - 0.07), (x + s * 0.03, fl, 0.0), LAC, 'plain', scale_b=1.25, rnd=False)
    # head: dark all round (no face, nothing light), hair in a bun behind, the crown's gold cap
    spheroid('head', HEAD_C, HEAD_R, HEAD_MAT, 'plain', sg=(12, 8))
    spheroid('hair', (0.0, -0.04, 1.455), (0.132, 0.145, 0.16), BLACK, 'plain', sg=(12, 8))
    spheroid('bun', (0.0, -0.185, 1.37), (0.09, 0.08, 0.095), BLACK, 'plain', sg=(8, 5))
    if detail: prism('bun_pin', ngon(0.012, 5), (-0.16, -0.19, 1.385), (0.16, -0.19, 1.365), GOLD, 'plain', rnd=True)
    lathe('cap', [(0.118, 1.535), (0.126, 1.59), (0.122, 1.645), (0.0, 1.645)], GOLD, 'plain', n=12)
    lathe('cap_band', [(0.13, 1.55), (0.132, 1.575)], CIN, 'plain', n=12)
    # 冕 board: black above, gold edge, cinnabar below; long front to back, round in front, square behind, tipped forward
    arc = [(BOARD_HW * math.cos(k * math.pi / 8), -BOARD_ARC - BOARD_HW * math.sin(k * math.pi / 8)) for k in range(9)]
    prof = [(-BOARD_HW, BOARD_REAR), (BOARD_HW, BOARD_REAR)] + arc
    for nm, mat, z0, z1, k in (('board_top', LAC, 0.0, 0.022, 1.0), ('board_edge', GOLD, -0.014, 0.0, 1.05), ('board_under', CIN, -0.028, -0.014, 0.985)):
        a = (BOARD_C[0], BOARD_C[1] + z0 * math.sin(TIP), BOARD_C[2] + z0 * math.cos(TIP)); b = (BOARD_C[0], BOARD_C[1] + z1 * math.sin(TIP), BOARD_C[2] + z1 * math.cos(TIP))
        prism(nm, [(p0 * k, p1 * k) for p0, p1 in prof], a, b, mat, 'plain', rnd=False)
    # gold hairpin through the cap, cinnabar cords to the chin
    prism('pin', ngon(0.013, 6), (-0.34, 0.0, 1.60), (0.34, 0.0, 1.60), GOLD, 'plain', rnd=True)
    for s in (-1, 1): prism(f'cord_{s}', rect(0.02, 0.012), (s * 0.15, 0.01, 1.595), (s * 0.118, 0.10, 1.25), CIN, 'plain', rnd=True, up=(s, 0.3, 0))
    # bead strings: a thin cord with small jade beads spaced along it, the last bead gold; twelve in front (three groups, each sways on
    # its own bone), twelve behind
    front, back = string_tops()
    for tops, L, nb, tag in ((front, STR_LEN, STR_BEADS, 'f'), (back, STR_LEN_B, STR_BEADS_B, 'b')):
        for k, top in enumerate(tops):
            PK.bone(f'beads_f{k * 3 // STRINGS}' if tag == 'f' else 'beads_b')
            upv = (top[0], 0.3 if tag == 'f' else -0.3, 0)
            if lv == 2:  # far: one flat strip per three strings
                if k % 3 == 1: prism(f'strip_{tag}{k}', rect(0.1, 0.012), top, (top[0], top[1], top[2] - L), JADE, 'plain', rnd=True, up=upv)
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

def light_near_head(ob):
    """faces of a light material within HEAD_CLEAR m of the head's axis between the collar top and the cap (must be none)."""
    names = [m.name for m in ob.data.materials]; n = 0
    for p in ob.data.polygons:
        c = p.center
        if names[p.material_index] in LIGHT and 1.27 < c.z < 1.56 and math.hypot(c.x - HEAD_C[0], -c.y - HEAD_C[1]) < HEAD_CLEAR: n += 1
    return n

def gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(K.tris(l0) >= TRIS_MIN, f'kaymuse_lod0 tris {K.tris(l0)} (min {TRIS_MIN}: bead strings and folds modelled)')
    d = SEAT_Z[1] - SEAT_Z[0]
    G(x1 - x0 <= 2 * SEAT_HW and -y0 <= d / 2 and y1 <= d / 2 and -0.02 < z0 < 0.01,
      f'kaymuse sits within the throne seat: {x1 - x0:.2f} m wide (seat {2 * SEAT_HW:.2f}), f {-y1:.2f}..{-y0:.2f} m (seat half depth {d / 2:.2f}), base z {z0:.2f}')
    G(1.5 <= z1 <= 2.1, f'kaymuse crown top {z1:.2f} m over the seat (range 1.5-2.1; a suit stands 2.05-2.4 m)')
    # round 2 (lead: strings, not a cage; a dark head): the round 1 gate 'beads cover 55% of a blank head' is replaced by these two
    front, back = string_tops(); span = max(t[0] for t in front) - min(t[0] for t in front); gap = STR_ARC_R * math.radians(STR_DEG) - 2 * BEAD_R
    G(len(front) == 12 and len(back) == 12 and span >= 2 * HEAD_R[0] and STR_LEN >= 2 * HEAD_R[2] and gap >= BEAD_R and BEAD_PITCH >= 3 * BEAD_R,
      f'kaymuse 冕: {len(front)} + {len(back)} bead strings, front span {span:.2f} m (head {2 * HEAD_R[0]:.2f}), length {STR_LEN} m (head {2 * HEAD_R[2]:.2f}), {gap * 100:.1f} cm clear between strings, bead pitch {BEAD_PITCH / BEAD_R:.1f} radii (strings, not a cage)')
    n = light_near_head(l0); G(n == 0 and HEAD_MAT not in LIGHT, f'kaymuse head dark from every side: {n} light faces within {HEAD_CLEAR} m of the head (head material {HEAD_MAT}; no face modelled)')
    L = BOARD_REAR + BOARD_ARC + BOARD_HW; G(L >= 1.8 * 2 * BOARD_HW, f'kaymuse 冕 board {L:.2f} m long x {2 * BOARD_HW:.2f} m wide (length >= 1.8 x width)')
    m = K.mats(l0); G({ROBE, CIN, GOLD, JADE, BLACK} <= m and 'kmSkin' not in m, f'kaymuse materials {sorted(m)} (black robe, cinnabar, gold, white inner layer; no skin)')
    G({CIN, GOLD, JADE} <= K.mats(l1) and {GOLD, JADE} <= K.mats(l2), 'kaymuse LOD1 keeps cinnabar, gold and the white layer; LOD2 keeps gold and white')


if __name__ == '__main__':
    seat = [0.0, SEAT_Y, (SEAT_Z[0] + SEAT_Z[1]) / 2]
    PK.build_rigged('kaymuse', build, bones(), clips, OUT, BUDGET, 4.0, extras={'seat': seat, 'clips': 'idle'}, extra_gates=gates)
    sys.exit(0)
