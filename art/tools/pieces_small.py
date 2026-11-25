# Small objects (PIECES round 2; owner 25 Nov 13:08), each under 500 triangles, static, LOD0/1/2 built per level (index.html draws all
# four as plain shapes). Round 2 follows the lead's verdict on run 45555140630; every outline is black lacquer so it reads on the floor.
#   plate        the plate pickup: a shed armour plate of the tiger, 0.7 m (flat box today). Three overlapping curved lames narrowing to
#                one end (a segmented edge), a black flange rim, a row of rivets on the wide end, three silver claw-stripe inlays, two
#                torn strap lugs. Lies dome up.
#   leader_crown the leader's marker (gold hexagon at CONFIG.LEADER crownY 2.95, crownR 0.3 today): a small court crown token, read
#                from above: a black lacquer ring with a gold line, a short flat board on four posts (black border, gold inlay field,
#                cinnabar underside), three short bead strings in front and three behind. No long blades. Origin = the ring's base centre.
#   mo_wall      the 墨 wall a suit raises (unit box scaled to len 4 x h 2.4 x thick 0.6 today), at true size: a rammed-earth panel with
#                its horizontal layer lines between upright dark timber posts and horizontal rails, a river-stone footing, a timber
#                cap, bronze sleeves at the joints, a cinnabar school plaque with a carpenter's-square sigil. No diagonal braces.
#                Extras give its size so the game can scale per cast.
#   decree_mark  the marker over a marked suit (0.3 x 0.9 box at markY 3.5 today): a hanging black lacquer tally tablet pointing down, a
#                gold inlay line inside its edge, a square cinnabar seal cut with an abstract beast mask (two eyes, brow horns, nose,
#                jaw, fangs: no script, no letter shape), a ring on top. Origin = the tip.
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
# Plate: shell radius m, half arc deg at the wide and narrow end, length m, thickness m; size the game expects (index.html plateGeo).
PL_R, PL_ARC, PL_LEN, PL_TH, PL_SIZE = 0.56, (37, 15), 0.64, 0.035, 0.7
# Plate lames: count, overlap (share of the length), step down per lame m; rivets on the wide end; claw stripes.
PL_LAMES, PL_LAP, PL_STEP, PL_RIVETS, PL_CLAWS = 3, 0.035, 0.014, 4, 3
# Leader crown: ring radius (index.html CONFIG.LEADER.crownR), ring height, board height over the base, board half width and half length, m.
CR_R, CR_BAND, CR_BOARD_Z, CR_BOARD = 0.30, 0.12, 0.21, (0.19, 0.33)
# Leader crown: bead strings per end, string length m. Size gates: height range, most width and length, m.
CR_STRINGS, CR_STR_LEN, CR_SIZE = 3, 0.15, ((0.2, 0.5), 0.7, 0.75)
# 墨 wall at true size (index.html mo Q: len 4, h 2.4, thick 0.6), m; post x places; rail heights.
MW_LEN, MW_H, MW_T = 4.0, 2.4, 0.6
MW_POSTS, MW_RAILS = (-1.88, -0.94, 0.0, 0.94, 1.88), (0.85, 1.45)
# 墨 wall: diagonal braces (must stay 0: a brace reads as European half-timber).
MW_BRACES = 0
# Decree mark: width and height m (index.html CONFIG.DECREES markW 0.3, markH 0.9); gold line and inner panel as a share of the tablet.
DM_W, DM_H, DM_LINE, DM_INNER = 0.30, 0.90, 0.80, 0.69
# Decree seal: side m; sigil parts as (centre x, centre z, width, height, turn deg) in the seal's own square, m: eyes, brow horns, nose, jaw, fangs.
DM_SEAL = 0.19
DM_SIGIL = [(-0.045, 0.028, 0.034, 0.034, 0), (0.045, 0.028, 0.034, 0.034, 0), (-0.052, 0.066, 0.06, 0.018, 28), (0.052, 0.066, 0.06, 0.018, -28),
            (0.0, -0.006, 0.02, 0.07, 0), (0.0, -0.066, 0.13, 0.02, 0), (-0.05, -0.042, 0.02, 0.03, 0), (0.05, -0.042, 0.02, 0.03, 0)]
BR, INL, CIN, GOLD, LAC, BLK, JADE = 'palBronze', 'palInlay', 'palCinnabar', 'palGold', 'palLacquerPlain', 'pcBlack', 'kmJade'
EARTH, TIMBER, STONE = 'moEarth', 'moTimber', 'moStone'
PK.mutate(globals())


def plate_pt(u, v, k, dr=0.0):
    arc = math.radians(PL_ARC[0] + (PL_ARC[1] - PL_ARC[0]) * v); ph = (u - 0.5) * 2 * arc; r = PL_R - k * PL_TH - dr
    return (r * math.sin(ph), (v - 0.5) * PL_LEN, r * math.cos(ph) - (PL_R - PL_TH) * math.cos(math.radians(PL_ARC[0])) + 0.012)

def plate_build(detail):
    lv = PK.LEVEL['n']; n = PL_LAMES if lv < 2 else 1
    for j in range(n):  # overlapping lames, each a step lower, narrowing toward the far end
        v0, v1 = max(0.0, j / n - PL_LAP), (j + 1) / n
        PK.shell(f'lame_{j}', lambda u, v, k, v0=v0, v1=v1, j=j: plate_pt(u, v0 + (v1 - v0) * v, k, PL_STEP * j), 6 if lv == 0 else 8, 1, BR, 'plain')
        for q, u in enumerate((0.0, 1.0)):  # black flange along each lame's side: the stepped, segmented edge
            prism(f'side_{j}{q}', ngon(0.022, 4), plate_pt(u, v0, -0.2, PL_STEP * j), plate_pt(u, v1, -0.2, PL_STEP * j), BLK, 'plain', rnd=True)
    for q, (v, dr) in enumerate(((0.0, 0.0), (1.0, PL_STEP * (n - 1)))):  # black flange rim along the two curved ends
        sweep(f'rim_{q}', [plate_pt(i / 5, v, -0.2, dr) for i in range(6)], [0.022] * 6, BLK, 'plain', n=3)
    if lv < 2:
        for q in range(PL_CLAWS):  # claw-stripe inlays raking down the plate, as the tiger's own stripes
            u0 = 0.26 + 0.24 * q; pts = [plate_pt(u0 + 0.06 * t, 0.12 + 0.76 * t, -0.12, PL_STEP * min(int((0.12 + 0.76 * t) * n), n - 1)) for t in (0.0, 0.5, 1.0)]
            for j, (a, b) in enumerate(zip(pts, pts[1:])): prism(f'claw_{q}{j}', rect(0.034 - 0.012 * j, 0.012), a, b, INL, 'plain', scale_b=0.6, rnd=True, up=(a[0], 0, 0.56))
    if detail:
        for q in range(PL_RIVETS):  # rivets along the wide end
            a = plate_pt(0.14 + 0.72 * q / (PL_RIVETS - 1), 0.07, 0.0); prism(f'rivet_{q}', ngon(0.022, 5), a, (a[0] * 1.03, a[1], a[2] + 0.018), INL, 'plain', scale_b=0.6, rnd=True)
        for q, u in enumerate((0.25, 0.75)):  # torn strap lugs on the wide end
            a = plate_pt(u, 0.0, 0.2); prism(f'lug_{q}', rect(0.07, 0.03), a, (a[0], a[1] - 0.06, a[2] - 0.012), BR, 'flange', scale_b=0.6, rnd=True, up=(0, 0, 1))

def plate_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(max(x1 - x0, y1 - y0) - PL_SIZE) <= 0.06 and min(x1 - x0, y1 - y0) >= 0.55, f'plate {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1 - z0:.2f} m high (game pickup {PL_SIZE} m)')
    G(z0 >= -0.01 and 0.08 <= z1 <= 0.2, f'plate lies on the ground, dome {z1:.2f} m high (0.08-0.2)')
    G({BR, INL, BLK} <= K.mats(l0), f'plate materials {sorted(K.mats(l0))}')
    G(PL_LAMES >= 3 and PL_RIVETS >= 4 and PL_CLAWS >= 3 and PL_ARC[1] <= 0.5 * PL_ARC[0], f'plate reads as armour: {PL_LAMES} lames, {PL_RIVETS} rivets, {PL_CLAWS} claw stripes, narrow end {PL_ARC[1]} deg against {PL_ARC[0]} deg')


def crown_build(detail):
    lv = PK.LEVEL['n']; hw, hl = CR_BOARD
    lathe('ring', [(CR_R - 0.03, 0.0), (CR_R, 0.0), (CR_R, CR_BAND), (CR_R - 0.03, CR_BAND), (CR_R - 0.03, 0.0)], BLK, 'plain', n=12)
    if lv < 2: lathe('ring_line', [(CR_R + 0.008, 0.04), (CR_R + 0.008, 0.08)], GOLD, 'plain', n=12)
    # the short board: square behind, cut corners in front; black border, a gold inlay field on top, cinnabar underneath
    prof = [(-hw, hl), (hw, hl), (hw, -hl * 0.6), (hw * 0.5, -hl), (-hw * 0.5, -hl), (-hw, -hl * 0.6)]
    for nm, mat, z0, z1, k in (('board', BLK, 0.0, 0.024, 1.0), ('board_field', GOLD, 0.02, 0.03, 0.72), ('board_under', CIN, -0.012, 0.0, 0.9)):
        if lv == 2 and nm == 'board_under': continue
        prism(nm, [(a * k, b * k) for a, b in prof], (0, 0, CR_BOARD_Z + z0), (0, 0, CR_BOARD_Z + z1), mat, 'plain', rnd=True)
    if lv < 2:
        for sx in (-1, 1):
            for sf in (-1, 1): prism(f'post_{sx}{sf}', ngon(0.02, 4), (sx * 0.2, sf * 0.2, CR_BAND - 0.01), (sx * 0.14, sf * 0.2, CR_BOARD_Z), GOLD, 'plain', rnd=True)
        prism('stone', ngon(0.035, 6), (0.0, CR_R - 0.005, CR_BAND * 0.5), (0.0, CR_R + 0.025, CR_BAND * 0.5), CIN, 'plain', rnd=True)
    for sf in (1, -1):  # bead strings front and back: a cord, a jade bead, a gold end bead
        for q in range(CR_STRINGS):
            x = (q - (CR_STRINGS - 1) / 2) * 0.09 * (1.0 if sf > 0 else 1.6); f = sf * (hl - 0.005); top = (x, f, CR_BOARD_Z - 0.01)
            if lv == 2:
                if q == 1: prism(f'strip_{sf}', rect(0.2, 0.012), top, (x, f, top[2] - CR_STR_LEN), JADE, 'plain', rnd=True, up=(0, sf, 0))
                continue
            prism(f'cord_{sf}{q}', rect(0.014, 0.014), top, (x, f, top[2] - CR_STR_LEN), JADE, 'plain', rnd=True, up=(0, sf, 0))
            if detail:
                prism(f'bead_{sf}{q}', ngon(0.024, 4), (x, f, top[2] - 0.05), (x, f, top[2] - 0.09), JADE, 'plain', rnd=True, up=(0, sf, 0))
                prism(f'end_{sf}{q}', ngon(0.028, 4), (x, f, top[2] - CR_STR_LEN + 0.01), (x, f, top[2] - CR_STR_LEN - 0.03), GOLD, 'plain', rnd=True, up=(0, sf, 0))

def crown_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0); (h0, h1), wmax, lmax = CR_SIZE
    G(abs(z0) <= 0.01 and h0 <= z1 <= h1 and x1 - x0 <= wmax and y1 - y0 <= lmax,
      f'leader crown {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1:.2f} m high (height {h0}-{h1}, width <= {wmax}, length <= {lmax}; ring radius {CR_R} as CONFIG.LEADER.crownR): a compact token, no long blades')
    G({GOLD, CIN, BLK, JADE} <= K.mats(l0), f'leader crown materials {sorted(K.mats(l0))} (black lacquer, gold inlay, cinnabar, jade beads)')
    G(CR_STRINGS >= 3 and 2 * CR_BOARD[1] >= 1.5 * 2 * CR_BOARD[0], f'leader crown: a board {2 * CR_BOARD[1]:.2f} x {2 * CR_BOARD[0]:.2f} m with {CR_STRINGS} + {CR_STRINGS} bead strings')


def wall_build(detail):
    lv = PK.LEVEL['n']; h = MW_LEN / 2
    prism('footing', [(-0.36, 0.0), (0.36, 0.0), (0.33, 0.30), (-0.33, 0.30)], (-h, 0, 0), (h, 0, 0), STONE, 'tile4', rnd=True)
    prism('earth', [(-0.30, 0.30), (0.30, 0.30), (0.24, 2.16), (-0.24, 2.16)], (-h + 0.04, 0, 0), (h - 0.04, 0, 0), EARTH, 'tile4', rnd=True)
    for q, x in enumerate(MW_POSTS):  # upright posts clasp the panel through its thickness; a bronze sleeve under the cap
        prism(f'post_{q}', rect(0.2, 0.72), (x, 0, 0.26), (x, 0, 2.2), TIMBER, 'tile4', scale_b=0.86, rnd=True)
        if lv < 2: prism(f'sleeve_{q}', rect(0.25, 0.70), (x, 0, 1.95), (x, 0, 2.1), BR, 'lozenge', scale_b=0.97, rnd=True)
    prism('cap', [(-0.40, 2.16), (0.40, 2.16), (0.40, 2.31), (-0.40, 2.31)], (-h - 0.04, 0, 0), (h + 0.04, 0, 0), TIMBER, 'tile4', rnd=True)
    prism('ridge', [(-0.44, 2.305), (0.44, 2.305), (0.0, MW_H)], (-h - 0.06, 0, 0), (h + 0.06, 0, 0), TIMBER, 'tile4', rnd=True)
    for s in (-1, 1):
        for q, z in enumerate(MW_RAILS):  # horizontal rails, front and back
            if lv < 2 or q == 1: prism(f'rail_{s}{q}', rect(0.1, 0.13), (-h, s * 0.345, z), (h, s * 0.345, z), TIMBER, 'tile4', rnd=True)
        for q in range(MW_BRACES):  # CONFIG keeps this at 0 (mutation only)
            prism(f'brace_{s}{q}', rect(0.09, 0.05), (MW_POSTS[q] + 0.1, s * 0.335, 0.42), (MW_POSTS[q + 1] - 0.1, s * 0.3, 2.02), TIMBER, 'tile4', rnd=True, up=(0, s, 0))
        if detail:
            for q in (0, 2, 4):  # bronze sleeves where the upper rail crosses the end and middle posts
                prism(f'joint_{s}{q}', rect(0.26, 0.19), (MW_POSTS[q], s * 0.385, MW_RAILS[1]), (MW_POSTS[q], s * 0.41, MW_RAILS[1]), BR, 'lozenge', rnd=True)
        if lv < 2:  # the school's plaque on both faces: cinnabar disc, black carpenter's square
            prism(f'plaque_{s}', ngon(0.19, 8, math.pi / 8), (0, s * 0.355, 1.8), (0, s * 0.395, 1.8), CIN, 'plain', rnd=True)
        if detail:
            prism(f'sq_a_{s}', rect(0.05, 0.2), (0.065, s * 0.39, 1.81), (0.065, s * 0.405, 1.81), LAC, 'plain', rnd=True)
            prism(f'sq_b_{s}', rect(0.18, 0.05), (0.0, s * 0.39, 1.735), (0.0, s * 0.405, 1.735), LAC, 'plain', rnd=True)

def wall_gates(G, l0, l2=None):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs((x1 - x0) - MW_LEN) <= 0.15 and abs(z1 - MW_H) <= 0.02 and MW_T <= y1 - y0 <= MW_T + 0.3, f'墨 wall {x1 - x0:.2f} x {z1:.2f} x {y1 - y0:.2f} m (game cast {MW_LEN} x {MW_H} x {MW_T}; the timber and footing stand proud of the solid)')
    G({EARTH, TIMBER, STONE, BR, CIN} <= K.mats(l0), f'墨 wall materials {sorted(K.mats(l0))} (rammed earth, timber, river stone, bronze sleeves, cinnabar plaque)')
    G(MW_BRACES == 0 and len(MW_RAILS) >= 2 and len(MW_POSTS) >= 4, f'墨 wall frame: {len(MW_POSTS)} upright posts, {len(MW_RAILS)} horizontal rails a face, {MW_BRACES} diagonal braces (must be 0)')
    if l2 is not None:  # LOD2 keeps the posts: timber still spans the wall's height and both ends
        tm = [i for i, m in enumerate(l2.data.materials) if m.name == TIMBER]; vs = [l2.data.vertices[v].co for p in l2.data.polygons if p.material_index in tm for v in p.vertices]
        ok = bool(vs) and min(c.z for c in vs) <= 0.3 and max(c.z for c in vs) >= MW_H - 0.02 and min(c.x for c in vs) <= MW_POSTS[0] and max(c.x for c in vs) >= MW_POSTS[-1]
        mid = sum(1 for c in vs if abs(c.x - MW_POSTS[2]) <= 0.11 and c.z < 1.0)
        G(ok and mid > 0, f'墨 wall LOD2 keeps the posts (timber from the footing to the ridge, end to end; {mid} vertices on the middle post below 1 m)')


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
    for q, (cx, dz, bw, bh, deg) in enumerate(DM_SIGIL):  # the beast mask cut in the seal (gold, through both faces); far LODs keep less
        if lv == 2 or (lv == 1 and q not in (0, 1, 5)): continue
        prism(f'sigil_{q}', turned(cx, dz, bw, bh, deg), (0, -0.054, zc), (0, 0.054, zc), GOLD, 'plain', rnd=True)
    if detail: torus('ring', (0.0, 0.0, DM_H - 0.062), (0, 1, 0), 0.044, 0.017, BR, 'flange', sg=(8, 4))
    else: prism('ring', rect(0.09, 0.07), (0, -0.012, DM_H - 0.045), (0, 0.012, DM_H - 0.045), BR, 'flange', rnd=True)

def sigil_like_letter():
    """True when the sigil could pass for a Latin letter: fewer than 6 strokes, or all strokes axis-aligned bars joined to one stem
    (E, F, H, I, L, T, U shapes: one upright and its cross bars). A mask needs separate eyes and turned brow strokes."""
    turned_n = sum(1 for p in DM_SIGIL if p[4] % 90 != 0); squares = sum(1 for p in DM_SIGIL if abs(p[2] - p[3]) < 0.005)
    return len(DM_SIGIL) < 6 or turned_n < 2 or squares < 2

def mark_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(z1 - DM_H) <= 0.03 and abs((x1 - x0) - DM_W) <= 0.04 and z0 >= -0.001, f'decree mark {x1 - x0:.2f} m wide x {z1:.2f} m high (game marker {DM_W} x {DM_H}), tip down at z {z0:.2f}')
    G({BLK, GOLD, CIN} <= K.mats(l0), f'decree mark materials {sorted(K.mats(l0))} (black lacquer, gold, cinnabar seal)')
    G(not sigil_like_letter(), f'decree seal sigil: {len(DM_SIGIL)} strokes, {sum(1 for p in DM_SIGIL if p[4] % 90 != 0)} turned, {sum(1 for p in DM_SIGIL if abs(p[2] - p[3]) < 0.005)} square eyes (a mask, not a letter shape)')


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
