# Small objects (PIECES round 3; owner 25 Nov 13:08 and 14:13 "fix them"), each under 500 triangles with its outline shell, static,
# LOD0/1/2 built per level (index.html draws all four as plain shapes). Round 3 follows the lead's notes on run 45557912570. Outlines on
# the floor come from the baked dark outline shell (pieces_kit.outline; owner option A) or from black lacquer.
#   plate        the plate pickup: a shed armour plate of the tiger, 0.7 m (flat box today). One thick lamellar plate: a long trapezoid,
#                gently domed, a raised brass border, pairs of lacing holes down both sides and across the top, three gold tiger-stripe
#                inlays, a workshop boss, a torn cinnabar lacing strap trailing from it; it lies tilted, one end off the ground.
#   leader_crown the leader's marker (gold hexagon at CONFIG.LEADER crownY 2.95, crownR 0.3 today): a gold crown read from above: a ring
#                with five rising cloud / mountain points leaning outward (tallest in front), a cinnabar stone on the front point, jade
#                studs beside it. No lid, no blades. Origin = the ring's base centre.
#   mo_wall      the 墨 wall a suit raises (unit box scaled to len 4 x h 2.4 x thick 0.6 today), at true size: rammed-earth panels with
#                modelled layer lines between four upright dark posts at three uneven spacings, one rail, a river-stone footing, a
#                lighter timber cap, bronze sleeves on the posts, the school's cinnabar plaque with a carpenter's-square sigil on the
#                widest panel. No braces, no even lattice. Extras give its size so the game can scale per cast.
#   decree_mark  the marker over a marked suit (0.3 x 0.9 box at markY 3.5 today): a hanging black lacquer tally tablet pointing down, a
#                gold inlay line inside its edge, a square cinnabar seal cut with a squared thunder-scroll (雷纹 idea, own strokes: one
#                unequal spiral, not mirrored, no script, no face), a ring on top. Origin = the tip.
# Usage: python pieces_small.py OUTDIR
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import prop_kit as K
import pieces_kit as PK
from prop_kit import lathe, spheroid, sweep, prism, torus, ngon, rect, blade

OUTDIR = sys.argv[-1] if os.path.isdir(sys.argv[-1]) else '/tmp/pieces'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 with the outline shell (task: under 500 each).
BUDGET = (499, 400, 220)
# Dark outline shell width per piece, m (plate, crown, wall).
SHELL_W = {'plate': 0.03, 'leader_crown': 0.03, 'mo_wall': 0.045, 'decree_mark': 0.0}
# Plate: half width at the wide and narrow end, length, thickness, dome height m; tilt deg (one end off the ground); the game's size.
PL_HW, PL_LEN, PL_TH, PL_DOME, PL_TILT, PL_SIZE = (0.29, 0.22), 0.68, 0.06, 0.03, 12, 0.7
# Plate: lacing hole pairs down each side, holes across the top, tiger stripes.
PL_HOLES, PL_TOP_HOLES, PL_STRIPES = 2, 2, 3
# Leader crown: ring radius (index.html CONFIG.LEADER.crownR), ring height m; points as (angle from the front deg, width, height) m; outward lean deg.
CR_R, CR_BAND = 0.30, 0.12
CR_POINTS, CR_LEAN = [(0, 0.17, 0.30), (-38, 0.14, 0.22), (38, 0.14, 0.22), (-66, 0.10, 0.14), (66, 0.10, 0.14)], 12
# Leader crown size gates: height range, most width and length, m. A lid is not allowed (CR_LID must stay 0: a lid reads as a tray).
CR_SIZE, CR_LID = ((0.3, 0.5), 0.7, 0.75), 0
# 墨 wall at true size (index.html mo Q: len 4, h 2.4, thick 0.6), m; post x places (uneven spacings); rail height; layer line heights.
MW_LEN, MW_H, MW_T = 4.0, 2.4, 0.6
MW_POSTS, MW_RAILS, MW_LINES = (-1.88, -0.9, 0.55, 1.88), (1.3,), (0.62, 0.95, 1.62, 1.92)
# 墨 wall: diagonal braces (must stay 0: a brace reads as European half-timber). Spacings must differ by at least MW_UNEVEN m.
MW_BRACES, MW_UNEVEN = 0, 0.1
# Decree mark: width and height m (index.html CONFIG.DECREES markW 0.3, markH 0.9); gold line and inner panel as a share of the tablet.
DM_W, DM_H, DM_LINE, DM_INNER = 0.30, 0.90, 0.80, 0.69
# Decree seal: side m; strokes as (centre x, centre z, width, height, turn deg) in the seal's own square, m: one squared spiral
# (top, right, bottom, left, inner top, inner right, inner bottom), unequal arms.
DM_SEAL = 0.19
DM_SIGIL = [(0.0, 0.066, 0.15, 0.018, 0), (0.066, 0.0, 0.018, 0.15, 0), (0.0, -0.066, 0.15, 0.018, 0), (-0.066, -0.018, 0.018, 0.114, 0),
            (-0.018, 0.03, 0.114, 0.018, 0), (0.03, 0.0, 0.018, 0.078, 0), (0.004, -0.03, 0.07, 0.018, 0)]
# Most strokes that may have a mirror twin across the seal's middle (a mirrored sigil reads as a face).
DM_MIRROR_MAX = 0.5
BR, INL, CIN, GOLD, LAC, BLK, JADE = 'palBronze', 'palInlay', 'palCinnabar', 'palGold', 'palLacquerPlain', 'pcBlack', 'kmJade'
EARTH, EARTH_LINE, TIMBER, TIMBER_LT, STONE = 'moEarth', 'moEarthLine', 'moTimber', 'moTimberLight', 'moStone'
PK.mutate(globals())


def plate_pt(u, v, k, lift=0.0):
    """the plate before it is tilted: u across, v along (0 = wide end), k 0 top face, 1 bottom face."""
    hw = PL_HW[0] + (PL_HW[1] - PL_HW[0]) * v; x = (2 * u - 1) * hw; b = PL_DOME * (1 - (2 * u - 1) ** 2)
    return (x, (v - 0.5) * PL_LEN, (b * 0.7 if k else PL_TH + b) + lift)

def plate_build(detail):
    lv = PK.LEVEL['n']; n0 = len(K.PARTS); PK.outline(0)
    PK.shell('body', plate_pt, 6 if lv == 0 else 8, 2, BR, 'plain')
    PK.outline(-1)
    if lv < 2:
        for q, u in enumerate((0.0, 1.0)):  # raised border down both sides and across both ends
            prism(f'border_{q}', rect(0.045, 0.03), plate_pt(u * 0.94 + 0.03, 0.0, 0, 0.004), plate_pt(u * 0.94 + 0.03, 1.0, 0, 0.004), BR, 'flange', rnd=True, up=(0, 0, 1))
        for q, v in enumerate((0.03, 0.97)): prism(f'end_{q}', rect(0.045, 0.03), plate_pt(0.03, v, 0, 0.004), plate_pt(0.97, v, 0, 0.004), BR, 'flange', rnd=True, up=(0, 0, 1))
        for q in range(PL_STRIPES):  # tiger stripes: gold inlays raking across, each thinning to a point
            v0 = 0.24 + 0.24 * q; a, m, b = plate_pt(0.14, v0 + 0.07, 0, 0.002), plate_pt(0.5, v0 - 0.03, 0, 0.002), plate_pt(0.86 - 0.1 * (q % 2), v0 + 0.09, 0, 0.002)
            prism(f'stripe_{q}a', rect(0.02, 0.012), a, m, GOLD, 'plain', scale_b=2.4, rnd=True, up=(0, 0, 1))
            prism(f'stripe_{q}b', rect(0.048, 0.012), m, b, GOLD, 'plain', scale_b=0.3, rnd=True, up=(0, 0, 1))
    if detail:
        holes = [(u, 0.3 + 0.4 * i / max(PL_HOLES - 1, 1) + dv) for u in (0.11, 0.89) for i in range(PL_HOLES) for dv in (-0.035, 0.035)] + [(0.36 + 0.28 * i / max(PL_TOP_HOLES - 1, 1), 0.11) for i in range(PL_TOP_HOLES)]
        for q, (u, v) in enumerate(holes):  # lacing holes
            c = plate_pt(u, v, 0, -0.004); prism(f'hole_{q}', ngon(0.017, 4), c, (c[0], c[1], c[2] + 0.008), BLK, 'plain', rnd=True)
        c = plate_pt(0.5, 0.9, 0, -0.002); prism('boss', rect(0.08, 0.05), c, (c[0], c[1], c[2] + 0.012), BR, 'mark', rnd=True)
    parts = [p[0] for p in K.PARTS[n0:]]; PK.tilt(parts, (0.0, 0.5 * PL_LEN, 0.0), (1, 0, 0), PL_TILT)   # the narrow end stays down, the wide end lifts
    if lv < 2:  # the torn lacing strap: from a hole on the raised end down onto the floor
        lift = PL_LEN * math.sin(math.radians(PL_TILT)); a = (-0.2, -0.30, lift * 0.9 + PL_TH)
        sweep('strap', [a, (-0.33, -0.36, 0.05), (-0.42, -0.26, 0.016), (-0.36, -0.12, 0.014)], [0.014, 0.014, 0.014, 0.012], CIN, 'plain', n=4, flat=(1.0, 0.45))

def plate_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = PK.bounds(l0)
    G(abs(max(x1 - x0, y1 - y0) - PL_SIZE) <= 0.06 and min(x1 - x0, y1 - y0) >= 0.5, f'plate {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1 - z0:.2f} m high (game pickup {PL_SIZE} m)')
    G(z0 >= -0.012 and 0.14 <= z1 <= 0.32, f'plate lies tilted on the ground: lowest z {z0:.3f}, raised end {z1:.2f} m high (0.14-0.32)')
    G({BR, GOLD, CIN, BLK, PK.OUTLINE} <= K.mats(l0), f'plate materials {sorted(K.mats(l0))} (brass, gold stripes, cinnabar strap, lacing holes, outline)')
    G(PL_HW[1] >= 0.7 * PL_HW[0] and PL_TH >= 0.05 and 2 * PL_HOLES * 2 + PL_TOP_HOLES >= 8 and PL_STRIPES >= 3 and PL_TILT >= 8,
      f'plate reads as armour, not a fan: trapezoid {2 * PL_HW[0]:.2f} to {2 * PL_HW[1]:.2f} m (narrow end >= 70% of the wide), {PL_TH * 100:.0f} cm thick, {2 * PL_HOLES * 2 + PL_TOP_HOLES} lacing holes, {PL_STRIPES} tiger stripes, a torn strap, tilted {PL_TILT} deg')


def crown_build(detail):
    lv = PK.LEVEL['n']; PK.outline(1)
    lathe('ring', [(CR_R - 0.03, 0.0), (CR_R, 0.0), (CR_R, CR_BAND), (CR_R - 0.03, CR_BAND), (CR_R - 0.03, 0.0)], GOLD, 'plain', n=10)
    PK.outline(-1)
    if lv < 2: lathe('ring_line', [(CR_R + 0.006, 0.045), (CR_R + 0.006, 0.07)], LAC, 'plain', n=10)
    for q in range(CR_LID): prism(f'lid_{q}', ngon(CR_R, 8), (0, 0, CR_BAND + 0.08), (0, 0, CR_BAND + 0.1), GOLD, 'plain', rnd=True)   # CONFIG keeps this at 0 (mutation only)
    le = math.radians(CR_LEAN)
    for q, (deg, w, h) in enumerate(CR_POINTS):  # rising cloud / mountain points, leaning outward
        if lv == 2 and q > 2: continue
        a = math.radians(deg); rx, rf = math.sin(a), math.cos(a); r0 = CR_R - 0.012
        pr = [(-w / 2, 0.0), (w / 2, 0.0), (w * 0.65, h * 0.6), (0.0, h), (-w * 0.65, h * 0.6)]
        d = (rx * math.cos(le), rf * math.cos(le), -math.sin(le)); base = (rx * r0, rf * r0, CR_BAND - 0.03)
        PK.outline(0)
        prism(f'point_{q}', pr, base, tuple(base[i] + d[i] * 0.024 for i in range(3)), GOLD, 'plain', rnd=True, up=(0, 0, 1))
        PK.outline(-1)
        if lv < 2 and q < 3:  # a cinnabar stone on the front point, jade studs on the two beside it
            sz = 0.04 if q == 0 else 0.028; zc = CR_BAND - 0.03 + h * 0.52; out = math.sin(le) * h * 0.52
            c = (rx * (r0 + 0.024 + out), rf * (r0 + 0.024 + out), zc)
            prism(f'stone_{q}', ngon(sz, 6), c, (c[0] + rx * 0.02, c[1] + rf * 0.02, c[2]), CIN if q == 0 else JADE, 'plain', scale_b=0.6, rnd=True)

def crown_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = PK.bounds(l0); (h0, h1), wmax, lmax = CR_SIZE
    G(abs(z0) <= 0.01 and h0 <= z1 <= h1 and x1 - x0 <= wmax and y1 - y0 <= lmax,
      f'leader crown {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1:.2f} m high (height {h0}-{h1}, width <= {wmax}, length <= {lmax}; ring radius {CR_R} as CONFIG.LEADER.crownR)')
    G({GOLD, CIN, JADE, PK.OUTLINE} <= K.mats(l0), f'leader crown materials {sorted(K.mats(l0))} (gold, cinnabar stone, jade studs, outline)')
    hs = [p[2] for p in CR_POINTS]
    G(len(CR_POINTS) >= 5 and CR_LID == 0 and hs[0] == max(hs) and hs[0] >= 2 * CR_BAND and CR_LEAN >= 8, f'leader crown reads as a crown from above: an open ring, {len(CR_POINTS)} points leaning out {CR_LEAN} deg, the front one tallest ({hs[0]} m over a {CR_BAND} m ring), no lid ({CR_LID})')


def wall_build(detail):
    lv = PK.LEVEL['n']; h = MW_LEN / 2; PK.outline(0)
    prism('footing', [(-0.36, 0.0), (0.36, 0.0), (0.33, 0.30), (-0.33, 0.30)], (-h, 0, 0), (h, 0, 0), STONE, 'tile4', rnd=True)
    prism('earth', [(-0.30, 0.30), (0.30, 0.30), (0.24, 2.16), (-0.24, 2.16)], (-h + 0.04, 0, 0), (h - 0.04, 0, 0), EARTH, 'tile4', rnd=True)
    prism('cap', [(-0.40, 2.16), (0.40, 2.16), (0.40, 2.31), (-0.40, 2.31)], (-h - 0.04, 0, 0), (h + 0.04, 0, 0), TIMBER_LT, 'tile4', rnd=True)
    prism('ridge', [(-0.44, 2.305), (0.44, 2.305), (0.0, MW_H)], (-h - 0.06, 0, 0), (h + 0.06, 0, 0), TIMBER_LT, 'tile4', rnd=True)
    for q, x in enumerate(MW_POSTS):  # upright posts clasp the panel through its thickness; a bronze sleeve under the cap
        PK.outline(0)
        prism(f'post_{q}', rect(0.2, 0.72), (x, 0, 0.26), (x, 0, 2.2), TIMBER, 'tile4', scale_b=0.86, rnd=True)
        PK.outline(-1)
        if lv < 2: prism(f'sleeve_{q}', rect(0.25, 0.70), (x, 0, 1.97), (x, 0, 2.1), BR, 'lozenge', scale_b=0.97, rnd=True)
    for s in (-1, 1):
        for q, z in enumerate(MW_RAILS): prism(f'rail_{s}{q}', rect(0.1, 0.13), (-h, s * 0.345, z), (h, s * 0.345, z), TIMBER, 'tile4', rnd=True)
        if lv < 2:
            for q, z in enumerate(MW_LINES):  # rammed layer lines: thin darker courses standing just proud of the earth
                f = 0.30 - 0.06 * (z - 0.30) / 1.86 + 0.004
                if detail or q % 2 == 0: prism(f'line_{s}{q}', rect(0.012, 0.03), (-h + 0.05, s * f, z), (h - 0.05, s * f, z), EARTH_LINE, 'tile4', rnd=True)
        for q in range(MW_BRACES):  # CONFIG keeps this at 0 (mutation only)
            prism(f'brace_{s}{q}', rect(0.09, 0.05), (MW_POSTS[q] + 0.1, s * 0.335, 0.42), (MW_POSTS[q + 1] - 0.1, s * 0.3, 2.02), TIMBER, 'tile4', rnd=True, up=(0, s, 0))
        px = (MW_POSTS[1] + MW_POSTS[2]) / 2   # the school's plaque on the widest panel, both faces: cinnabar disc, black carpenter's square
        if lv < 2: prism(f'plaque_{s}', ngon(0.24, 8, math.pi / 8), (px, s * 0.25, 1.75), (px, s * 0.335, 1.75), CIN, 'plain', rnd=True)
        if detail:
            prism(f'sq_a_{s}', rect(0.06, 0.26), (px + 0.085, s * 0.33, 1.76), (px + 0.085, s * 0.346, 1.76), LAC, 'plain', rnd=True)
            prism(f'sq_b_{s}', rect(0.23, 0.06), (px, s * 0.33, 1.66), (px, s * 0.346, 1.66), LAC, 'plain', rnd=True)
    PK.outline(-1)

def wall_gates(G, l0, l2=None):
    (x0, x1), (y0, y1), (z0, z1) = PK.bounds(l0)
    G(abs((x1 - x0) - MW_LEN) <= 0.15 and abs(z1 - MW_H) <= 0.02 and MW_T <= y1 - y0 <= MW_T + 0.3, f'墨 wall {x1 - x0:.2f} x {z1:.2f} x {y1 - y0:.2f} m (game cast {MW_LEN} x {MW_H} x {MW_T}; the timber and footing stand proud of the solid)')
    G({EARTH, EARTH_LINE, TIMBER, TIMBER_LT, STONE, BR, CIN, PK.OUTLINE} <= K.mats(l0), f'墨 wall materials {sorted(K.mats(l0))} (rammed earth with layer lines, dark posts, lighter cap, river stone, bronze sleeves, cinnabar plaque, outline)')
    gaps = [b - a for a, b in zip(MW_POSTS, MW_POSTS[1:])]; un = min(abs(a - b) for i, a in enumerate(gaps) for b in gaps[i + 1:])
    G(MW_BRACES == 0 and len(gaps) == 3 and un >= MW_UNEVEN and len(MW_RAILS) <= 1 and len(MW_LINES) >= 3,
      f'墨 wall frame: posts at spacings {[round(g, 2) for g in gaps]} m (3, uneven by at least {MW_UNEVEN}: {un:.2f}), {len(MW_RAILS)} rail, {len(MW_LINES)} layer lines a face, {MW_BRACES} diagonal braces (must be 0): no even lattice')
    if l2 is not None:  # LOD2 keeps the posts
        tm = [i for i, m in enumerate(l2.data.materials) if m.name == TIMBER]; vs = [l2.data.vertices[v].co for p in l2.data.polygons if p.material_index in tm for v in p.vertices]
        ok = bool(vs) and min(c.z for c in vs) <= 0.3 and max(c.z for c in vs) >= 2.15 and min(c.x for c in vs) <= MW_POSTS[0] and max(c.x for c in vs) >= MW_POSTS[-1]
        mid = sum(1 for c in vs if abs(c.x - MW_POSTS[1]) <= 0.11 and c.z < 1.0)
        G(ok and mid > 0, f'墨 wall LOD2 keeps the posts (dark timber from the footing to the cap, end to end; {mid} vertices on an inner post below 1 m)')


def turned(cx, cz, w, h, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [(cx + x * c - z * s, cz + x * s + z * c) for x, z in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]

def mark_build(detail):
    lv = PK.LEVEL['n']; w, top, sh = DM_W / 2, DM_H - 0.085, 0.30; zc = top - 0.215
    body = [(-w, top), (w, top), (w, sh), (0.0, 0.0), (-w, sh)]; cz = 0.47
    scaled = lambda k: [(p0 * k, (p1 - cz) * k + cz) for p0, p1 in body]
    prism('tablet', body, (0, -0.03, 0), (0, 0.03, 0), BLK, 'plain', rnd=True)
    prism('line', scaled(DM_LINE), (0, -0.035, 0), (0, 0.035, 0), GOLD, 'plain', rnd=True)   # a gold inlay line inside the black edge
    if lv < 2: prism('inner', scaled(DM_INNER), (0, -0.04, 0), (0, 0.04, 0), BLK, 'plain', rnd=True)
    prism('seal', rect(DM_SEAL, DM_SEAL), (0, -0.047, zc), (0, 0.047, zc), CIN, 'plain', rnd=True)
    for q, (cx, dz, bw, bh, deg) in enumerate(DM_SIGIL):  # the seal's scroll (gold, through both faces); far LODs keep less
        if lv == 2 or (lv == 1 and q > 3): continue
        prism(f'sigil_{q}', turned(cx, dz, bw, bh, deg), (0, -0.054, zc), (0, 0.054, zc), GOLD, 'plain', rnd=True)
    if detail: torus('ring', (0.0, 0.0, DM_H - 0.062), (0, 1, 0), 0.044, 0.017, BR, 'flange', sg=(8, 4))
    else: prism('ring', rect(0.09, 0.07), (0, -0.012, DM_H - 0.045), (0, 0.012, DM_H - 0.045), BR, 'flange', rnd=True)

def mirrored_share():
    """share of the sigil's strokes with a mirror twin across the seal's middle (a stroke on the middle line is its own twin)."""
    def twin(p): return any(abs(q[0] + p[0]) < 0.006 and abs(q[1] - p[1]) < 0.006 and abs(q[2] - p[2]) < 0.006 and abs(q[3] - p[3]) < 0.006 and (q[4] + p[4]) % 180 == 0 for q in DM_SIGIL)
    return sum(1 for p in DM_SIGIL if twin(p)) / max(len(DM_SIGIL), 1)

def mark_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = PK.bounds(l0)
    G(abs(z1 - DM_H) <= 0.03 and abs((x1 - x0) - DM_W) <= 0.04 and z0 >= -0.001, f'decree mark {x1 - x0:.2f} m wide x {z1:.2f} m high (game marker {DM_W} x {DM_H}), tip down at z {z0:.2f}')
    G({BLK, GOLD, CIN} <= K.mats(l0), f'decree mark materials {sorted(K.mats(l0))} (black lacquer, gold, cinnabar seal)')
    ms = mirrored_share(); G(len(DM_SIGIL) >= 6 and ms <= DM_MIRROR_MAX, f'decree seal sigil: {len(DM_SIGIL)} strokes, {ms:.0%} with a mirror twin (max {DM_MIRROR_MAX:.0%}): one unequal scroll, not a face (whether it reads as a letter is judged on the sheet, not here)')


PIECES = [('plate', plate_build, plate_gates, 1.2, {'size': PL_SIZE}), ('leader_crown', crown_build, crown_gates, 1.4, {'r': CR_R}),
          ('mo_wall', wall_build, wall_gates, 5.0, {'size': [MW_LEN, MW_H, MW_T]}), ('decree_mark', mark_build, mark_gates, 0.8, {'size': [DM_W, DM_H]})]

if __name__ == '__main__':
    for key, build, gates, gap, extras in PIECES:
        K.reset(); K.PARTS.clear()
        l0, l1, l2 = PK.lods_static(key, build, BUDGET, SHELL_W[key])
        G = K.Gates()
        for ob, lim in zip((l0, l1, l2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
        G(K.tris(l0) > K.tris(l1) > K.tris(l2) > 0, f'{key} LODs ordered: {K.tris(l0)} > {K.tris(l1)} > {K.tris(l2)} tris')
        if key == 'mo_wall': gates(G, l0, l2)
        else: gates(G, l0)
        l1.location.x = gap; l2.location.x = 2 * gap
        G.done()
        root = bpy.data.objects.new(key, None); bpy.context.collection.objects.link(root)
        PK.export(os.path.join(OUTDIR, f'{key}.glb'), extras, root)
