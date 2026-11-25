# Small objects (PIECES round 4; owner 25 Nov 13:08 and 14:13 "fix them"), each under 500 triangles, static, LOD0/1/2 built per level
# (index.html draws all four as plain shapes). Round 4 follows the lead's notes on run 45560766962: no baked outline (round 3's shell is
# removed); static props carry no outline at all and must read by their own values like the 鼎 (bright tops, dark undersides, shadow).
#   plate        the plate pickup: a shed armour plate of the tiger, 0.7 m (flat box today). One curved cast plate (a strong arc), its
#                lower edge scalloped, three tapered claw-mark stripes in raised gold raking diagonally across it (all one way: not
#                chevrons), a rolled top edge with lacing holes, a torn cinnabar strap; it lies dome up, the top end off the ground.
#   leader_crown the leader's marker (gold hexagon at CONFIG.LEADER crownY 2.95, crownR 0.3 today): a gold crown read from above: a ring
#                with five rising cloud / mountain points leaning outward (tallest in front), a cinnabar stone on the front point, jade
#                studs beside it. No lid, no blades. Origin = the ring's base centre.
#   mo_wall      the 墨 wall a suit raises (unit box scaled to len 4 x h 2.4 x thick 0.6 today), at true size: loess-yellow rammed-earth
#                panels with modelled layer lines between four upright posts at three uneven spacings, one rail, a river-stone footing,
#                a lighter timber cap, bronze sleeves on the posts, the school's cinnabar plaque with a carpenter's-square sigil on the
#                widest panel. No braces, no even lattice. Extras give its size so the game can scale per cast.
#   decree_mark  the marker over a marked suit (0.3 x 0.9 box at markY 3.5 today): a hanging black lacquer tally tablet pointing down, a
#                gold inlay line inside its edge, a round cinnabar seal bearing a gold tiger tally (a crouching tiger outline, split
#                along its back as a tally is: the empress's authority; no strokes, no script, no letter shape), a ring on top.
#                Origin = the tip.
# Usage: python pieces_small.py OUTDIR
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import prop_kit as K
import pieces_kit as PK
from prop_kit import lathe, spheroid, sweep, prism, torus, ngon, rect, blade

OUTDIR = sys.argv[-1] if os.path.isdir(sys.argv[-1]) else '/tmp/pieces'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (task: under 500 each).
BUDGET = (499, 400, 220)
# Plate: half width at the top and lower end, length, thickness, arc height m (a curved plate); tilt deg (the top end off the ground); the game's size.
PL_HW, PL_LEN, PL_TH, PL_DOME, PL_TILT, PL_SIZE = (0.30, 0.27), 0.60, 0.05, 0.10, 8, 0.7
# Plate: scallops on the lower edge and their depth m; claw-mark stripes: count, rake across (u) and along (v) the plate, ridge width and height m, tip taper.
PL_SCALLOPS, PL_SCALLOP_D, PL_STRIPES, PL_RAKE, PL_RIDGE, PL_TAPER = 3, 0.07, 3, (0.22, 0.62), (0.075, 0.032), 0.12
# Plate: lacing holes along the top edge.
PL_HOLES = 4
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
# Decree seal: round, radius m, sides. The tiger tally on it: a crouching tiger's outline (x, z) in the seal's own frame, m (nose to the
# left, ear, back, tail curl, hind leg, belly, fore leg, jaw), and the split along its back (z, x0, x1, width).
DM_SEAL_R, DM_SEAL_N = 0.095, 12
DM_TIGER = [(-0.075, 0.005), (-0.06, 0.035), (-0.045, 0.052), (-0.035, 0.035), (0.0, 0.04), (0.04, 0.035), (0.06, 0.052), (0.078, 0.04), (0.066, 0.02), (0.055, 0.005),
            (0.058, -0.035), (0.03, -0.035), (0.03, -0.012), (-0.02, -0.012), (-0.02, -0.035), (-0.055, -0.035), (-0.05, -0.012), (-0.07, -0.012)]
DM_SPLIT = (0.012, -0.045, 0.05, 0.007)
BR, INL, CIN, GOLD, LAC, BLK, JADE = 'palBronze', 'palInlay', 'palCinnabar', 'palGold', 'palLacquerPlain', 'pcBlack', 'kmJade'
EARTH, EARTH_LINE, TIMBER, TIMBER_LT, STONE = 'moEarth', 'moEarthLine', 'moTimber', 'moTimberLight', 'moStone'
PK.mutate(globals())


def plate_pt(u, v, k, lift=0.0):
    """the plate before it is tilted: u across, v along (0 = top edge, 1 = the scalloped lower edge), k 0 top face, 1 bottom face."""
    hw = PL_HW[0] + (PL_HW[1] - PL_HW[0]) * v; x = (2 * u - 1) * hw; b = PL_DOME * (1 - (2 * u - 1) ** 2)
    L = PL_LEN + PL_SCALLOP_D * abs(math.sin(PL_SCALLOPS * math.pi * u))
    return (x, -PL_LEN / 2 + v * L, (b * 0.75 if k else PL_TH + b) + lift)

def plate_build(detail):
    lv = PK.LEVEL['n']; n0 = len(K.PARTS)
    PK.shell('body', plate_pt, 12, 2, BR, 'plain')
    if lv < 2:
        for q in range(PL_STRIPES):  # claw marks: raised gold ridges raking diagonally, all one way, each thinning to a point
            u0 = 0.16 + (0.62 - PL_RAKE[0]) * q / max(PL_STRIPES - 1, 1); v0 = 0.14 + 0.05 * q
            pts = [plate_pt(u0 + PL_RAKE[0] * t, v0 + PL_RAKE[1] * t, 0, 0.004) for t in (0.0, 0.5, 1.0)]
            prism(f'claw_{q}a', blade(PL_RIDGE[0], PL_RIDGE[1]), pts[0], pts[1], GOLD, 'plain', scale_b=0.6, rnd=True, up=(pts[0][0] * 0.6, 0, 1))
            prism(f'claw_{q}b', blade(PL_RIDGE[0] * 0.6, PL_RIDGE[1] * 0.6), pts[1], pts[2], GOLD, 'plain', scale_b=PL_TAPER / 0.6, rnd=True, up=(pts[1][0] * 0.6, 0, 1))
        sweep('top_roll', [plate_pt(i / 6, 0.0, 0, -0.012) for i in range(7)], [0.024] * 7, BR, 'flange', n=4)   # rolled top edge
    if detail:
        for q in range(PL_HOLES):  # lacing holes under the rolled edge
            c = plate_pt((q + 0.5) / PL_HOLES, 0.1, 0, -0.004); prism(f'hole_{q}', ngon(0.018, 4), c, (c[0] * 1.02, c[1], c[2] + 0.009), BLK, 'plain', rnd=True)
    parts = [p[0] for p in K.PARTS[n0:]]; PK.tilt(parts, (0.0, PL_LEN / 2 + PL_SCALLOP_D, 0.0), (1, 0, 0), PL_TILT)   # the scalloped end stays down, the top end lifts
    if lv < 2:  # the torn lacing strap: from a hole on the raised end down onto the floor
        lift = (PL_LEN + PL_SCALLOP_D) * math.sin(math.radians(PL_TILT)); c = plate_pt(0.5 / PL_HOLES, 0.1, 0)
        sweep('strap', [(c[0], c[1], c[2] + lift * 0.9), (c[0] - 0.1, c[1] - 0.08, 0.05), (c[0] - 0.15, c[1] + 0.02, 0.016), (c[0] - 0.1, c[1] + 0.14, 0.014)], [0.014, 0.014, 0.014, 0.012], CIN, 'plain', n=4, flat=(1.0, 0.45))

def plate_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(max(x1 - x0, y1 - y0) - PL_SIZE) <= 0.06 and min(x1 - x0, y1 - y0) >= 0.5, f'plate {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1 - z0:.2f} m high (game pickup {PL_SIZE} m)')
    G(z0 >= -0.012 and 0.14 <= z1 <= 0.32, f'plate lies on the ground, dome up, the top end raised: lowest z {z0:.3f}, highest {z1:.2f} m (0.14-0.32)')
    G({BR, GOLD, CIN, BLK} <= K.mats(l0) and 'pcOutline' not in K.mats(l0), f'plate materials {sorted(K.mats(l0))} (brass, gold claw marks, cinnabar strap, lacing holes; no outline)')
    G(PL_DOME >= 0.06 and PL_SCALLOPS >= 3 and PL_STRIPES >= 3 and min(PL_RAKE) >= 0.15 and PL_TAPER <= 0.2 and PL_RIDGE[1] >= 0.025,
      f'plate reads as a curved armour plate: arc {PL_DOME * 100:.0f} cm high, {PL_SCALLOPS} scallops on the lower edge, {PL_STRIPES} claw marks raking {PL_RAKE[0]:.2f} across and {PL_RAKE[1]:.2f} along (one diagonal, not chevrons), {PL_RIDGE[1] * 100:.1f} cm proud, tapering to {PL_TAPER:.0%}')


def crown_build(detail):
    lv = PK.LEVEL['n']
    lathe('ring', [(CR_R - 0.03, 0.0), (CR_R, 0.0), (CR_R, CR_BAND), (CR_R - 0.03, CR_BAND), (CR_R - 0.03, 0.0)], GOLD, 'plain', n=10)
    if lv < 2: lathe('ring_line', [(CR_R + 0.006, 0.045), (CR_R + 0.006, 0.07)], LAC, 'plain', n=10)
    for q in range(CR_LID): prism(f'lid_{q}', ngon(CR_R, 8), (0, 0, CR_BAND + 0.08), (0, 0, CR_BAND + 0.1), GOLD, 'plain', rnd=True)   # CONFIG keeps this at 0 (mutation only)
    le = math.radians(CR_LEAN)
    for q, (deg, w, h) in enumerate(CR_POINTS):  # rising cloud / mountain points, leaning outward
        if lv == 2 and q > 2: continue
        a = math.radians(deg); rx, rf = math.sin(a), math.cos(a); r0 = CR_R - 0.012
        pr = [(-w / 2, 0.0), (w / 2, 0.0), (w * 0.65, h * 0.6), (0.0, h), (-w * 0.65, h * 0.6)]
        d = (rx * math.cos(le), rf * math.cos(le), -math.sin(le)); base = (rx * r0, rf * r0, CR_BAND - 0.03)
        prism(f'point_{q}', pr, base, tuple(base[i] + d[i] * 0.024 for i in range(3)), GOLD, 'plain', rnd=True, up=(0, 0, 1))
        if lv < 2 and q < 3:  # a cinnabar stone on the front point, jade studs on the two beside it
            sz = 0.04 if q == 0 else 0.028; zc = CR_BAND - 0.03 + h * 0.52; out = math.sin(le) * h * 0.52
            c = (rx * (r0 + 0.024 + out), rf * (r0 + 0.024 + out), zc)
            prism(f'stone_{q}', ngon(sz, 6), c, (c[0] + rx * 0.02, c[1] + rf * 0.02, c[2]), CIN if q == 0 else JADE, 'plain', scale_b=0.6, rnd=True)

def crown_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0); (h0, h1), wmax, lmax = CR_SIZE
    G(abs(z0) <= 0.01 and h0 <= z1 <= h1 and x1 - x0 <= wmax and y1 - y0 <= lmax,
      f'leader crown {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1:.2f} m high (height {h0}-{h1}, width <= {wmax}, length <= {lmax}; ring radius {CR_R} as CONFIG.LEADER.crownR)')
    G({GOLD, CIN, JADE} <= K.mats(l0) and 'pcOutline' not in K.mats(l0), f'leader crown materials {sorted(K.mats(l0))} (gold, cinnabar stone, jade studs; no outline)')
    hs = [p[2] for p in CR_POINTS]
    G(len(CR_POINTS) >= 5 and CR_LID == 0 and hs[0] == max(hs) and hs[0] >= 2 * CR_BAND and CR_LEAN >= 8, f'leader crown reads as a crown from above: an open ring, {len(CR_POINTS)} points leaning out {CR_LEAN} deg, the front one tallest ({hs[0]} m over a {CR_BAND} m ring), no lid ({CR_LID})')


def wall_build(detail):
    lv = PK.LEVEL['n']; h = MW_LEN / 2
    prism('footing', [(-0.36, 0.0), (0.36, 0.0), (0.33, 0.30), (-0.33, 0.30)], (-h, 0, 0), (h, 0, 0), STONE, 'tile4', rnd=True)
    prism('earth', [(-0.30, 0.30), (0.30, 0.30), (0.24, 2.16), (-0.24, 2.16)], (-h + 0.04, 0, 0), (h - 0.04, 0, 0), EARTH, 'tile4', rnd=True)
    prism('cap', [(-0.40, 2.16), (0.40, 2.16), (0.40, 2.31), (-0.40, 2.31)], (-h - 0.04, 0, 0), (h + 0.04, 0, 0), TIMBER_LT, 'tile4', rnd=True)
    prism('ridge', [(-0.44, 2.305), (0.44, 2.305), (0.0, MW_H)], (-h - 0.06, 0, 0), (h + 0.06, 0, 0), TIMBER_LT, 'tile4', rnd=True)
    for q, x in enumerate(MW_POSTS):  # upright posts clasp the panel through its thickness; a bronze sleeve under the cap
        prism(f'post_{q}', rect(0.2, 0.72), (x, 0, 0.26), (x, 0, 2.2), TIMBER, 'tile4', scale_b=0.86, rnd=True)
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

def wall_gates(G, l0, l2=None):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs((x1 - x0) - MW_LEN) <= 0.15 and abs(z1 - MW_H) <= 0.02 and MW_T <= y1 - y0 <= MW_T + 0.3, f'墨 wall {x1 - x0:.2f} x {z1:.2f} x {y1 - y0:.2f} m (game cast {MW_LEN} x {MW_H} x {MW_T}; the timber and footing stand proud of the solid)')
    G({EARTH, EARTH_LINE, TIMBER, TIMBER_LT, STONE, BR, CIN} <= K.mats(l0) and 'pcOutline' not in K.mats(l0), f'墨 wall materials {sorted(K.mats(l0))} (loess rammed earth with layer lines, posts, lighter cap, river stone, bronze sleeves, cinnabar plaque; no outline)')
    gaps = [b - a for a, b in zip(MW_POSTS, MW_POSTS[1:])]; un = min(abs(a - b) for i, a in enumerate(gaps) for b in gaps[i + 1:])
    G(MW_BRACES == 0 and len(gaps) == 3 and un >= MW_UNEVEN and len(MW_RAILS) <= 1 and len(MW_LINES) >= 3,
      f'墨 wall frame: posts at spacings {[round(g, 2) for g in gaps]} m (3, uneven by at least {MW_UNEVEN}: {un:.2f}), {len(MW_RAILS)} rail, {len(MW_LINES)} layer lines a face, {MW_BRACES} diagonal braces (must be 0): no even lattice')
    if l2 is not None:  # LOD2 keeps the posts
        tm = [i for i, m in enumerate(l2.data.materials) if m.name == TIMBER]; vs = [l2.data.vertices[v].co for p in l2.data.polygons if p.material_index in tm for v in p.vertices]
        ok = bool(vs) and min(c.z for c in vs) <= 0.3 and max(c.z for c in vs) >= 2.15 and min(c.x for c in vs) <= MW_POSTS[0] and max(c.x for c in vs) >= MW_POSTS[-1]
        mid = sum(1 for c in vs if abs(c.x - MW_POSTS[1]) <= 0.11 and c.z < 1.0)
        G(ok and mid > 0, f'墨 wall LOD2 keeps the posts (dark timber from the footing to the cap, end to end; {mid} vertices on an inner post below 1 m)')


def mark_build(detail):
    lv = PK.LEVEL['n']; w, top, sh = DM_W / 2, DM_H - 0.085, 0.30; zc = top - 0.215
    body = [(-w, top), (w, top), (w, sh), (0.0, 0.0), (-w, sh)]; cz = 0.47
    scaled = lambda k: [(p0 * k, (p1 - cz) * k + cz) for p0, p1 in body]
    prism('tablet', body, (0, -0.03, 0), (0, 0.03, 0), BLK, 'plain', rnd=True)
    prism('line', scaled(DM_LINE), (0, -0.035, 0), (0, 0.035, 0), GOLD, 'plain', rnd=True)   # a gold inlay line inside the black edge
    if lv < 2: prism('inner', scaled(DM_INNER), (0, -0.04, 0), (0, 0.04, 0), BLK, 'plain', rnd=True)
    prism('seal', ngon(DM_SEAL_R, DM_SEAL_N), (0, -0.047, zc), (0, 0.047, zc), CIN, 'plain', rnd=True)   # the round seal, through both faces
    if lv < 2:  # the tiger tally: one gold outline shape, split along its back
        prism('tiger', list(DM_TIGER), (0, -0.054, zc), (0, 0.054, zc), GOLD, 'plain', rnd=True)
    if detail:
        z, x0, x1, t = DM_SPLIT
        prism('split', [(x0, z - t / 2), (x1, z - t / 2), (x1, z + t / 2), (x0, z + t / 2)], (0, -0.057, zc), (0, 0.057, zc), BLK, 'plain', rnd=True)
        torus('ring', (0.0, 0.0, DM_H - 0.062), (0, 1, 0), 0.044, 0.017, BR, 'flange', sg=(8, 4))
    else: prism('ring', rect(0.09, 0.07), (0, -0.012, DM_H - 0.045), (0, 0.012, DM_H - 0.045), BR, 'flange', rnd=True)

def tiger_shape():
    """(points, width / height, concave corners, fits the seal): a tally animal is a long, many-cornered, concave outline; a letter cut
    from bars is not this shape."""
    xs = [p[0] for p in DM_TIGER]; zs = [p[1] for p in DM_TIGER]; n = len(DM_TIGER); conc = 0
    area = sum(DM_TIGER[i][0] * DM_TIGER[(i + 1) % n][1] - DM_TIGER[(i + 1) % n][0] * DM_TIGER[i][1] for i in range(n)); sg = 1 if area > 0 else -1
    for i in range(n):
        a, b, c = DM_TIGER[i - 1], DM_TIGER[i], DM_TIGER[(i + 1) % n]
        if ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])) * sg < 0: conc += 1
    return n, (max(xs) - min(xs)) / (max(zs) - min(zs)), conc, max(math.hypot(*p) for p in DM_TIGER) <= DM_SEAL_R

def mark_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(z1 - DM_H) <= 0.03 and abs((x1 - x0) - DM_W) <= 0.04 and z0 >= -0.001, f'decree mark {x1 - x0:.2f} m wide x {z1:.2f} m high (game marker {DM_W} x {DM_H}), tip down at z {z0:.2f}')
    G({BLK, GOLD, CIN} <= K.mats(l0) and 'pcOutline' not in K.mats(l0), f'decree mark materials {sorted(K.mats(l0))} (black lacquer, gold, cinnabar seal; no outline)')
    n, ar, conc, fits = tiger_shape()
    G(DM_SEAL_N >= 10 and n >= 14 and ar >= 1.5 and conc >= 5 and fits, f'decree seal: round ({DM_SEAL_N} sides), a tiger tally outline of {n} points, {ar:.1f} x as long as high, {conc} concave corners, inside the seal: one animal shape, no strokes (whether it reads as a tiger is judged on the sheet)')


PIECES = [('plate', plate_build, plate_gates, 1.2, {'size': PL_SIZE}), ('leader_crown', crown_build, crown_gates, 1.4, {'r': CR_R}),
          ('mo_wall', wall_build, wall_gates, 5.0, {'size': [MW_LEN, MW_H, MW_T]}), ('decree_mark', mark_build, mark_gates, 0.8, {'size': [DM_W, DM_H]})]

if __name__ == '__main__':
    for key, build, gates, gap, extras in PIECES:
        K.reset(); K.PARTS.clear()
        l0, l1, l2 = PK.lods_static(key, build, BUDGET)
        G = K.Gates()
        for ob, lim in zip((l0, l1, l2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
        G(K.tris(l0) > K.tris(l1) > K.tris(l2) > 0, f'{key} LODs ordered: {K.tris(l0)} > {K.tris(l1)} > {K.tris(l2)} tris')
        if key == 'mo_wall': gates(G, l0, l2)
        else: gates(G, l0)
        l1.location.x = gap; l2.location.x = 2 * gap
        G.done()
        root = bpy.data.objects.new(key, None); bpy.context.collection.objects.link(root)
        PK.export(os.path.join(OUTDIR, f'{key}.glb'), extras, root)
