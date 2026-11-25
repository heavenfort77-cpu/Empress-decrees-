# Small objects (PIECES round 1; owner 25 Nov 13:08), each under 500 triangles, static, LOD0/1/2 (index.html draws all four as plain shapes):
#   plate        the plate pickup: a shed bronze armour plate of the tiger, 0.7 m (flat 0.7 x 0.15 x 0.7 box today). A curved cast shell
#                segment lying dome up, flange rim, two silver inlay lines and a workshop mark (as the tiger's own plates), two torn lugs.
#   leader_crown the leader's marker (gold hexagon at CONFIG.LEADER crownY 2.95, crownR 0.3 today): a Qin martial cap crown (鹖冠 idea,
#                own design): a gold band with three pointed tablets in front and two tall swept tail feathers, a cinnabar stone.
#                Origin = the band's base centre (the game places it at crownY).
#   mo_wall      the 墨 wall a suit raises (unit box scaled to len 4 x h 2.4 x thick 0.6 today): a Mohist mantlet at true size: battered
#                rammed-earth core with layer lines on a river-stone footing, timber posts, rails and braces, a timber cap, bronze sleeves at
#                the joints, a cinnabar school plaque with a carpenter's-square sigil (invented mark, no script). Extras give its size so
#                the game can scale per cast.
#   decree_mark  the marker over a marked suit (0.3 x 0.9 box at markY 3.5 today): a hanging tally tablet pointing down at the suit: black
#                lacquer, gold frame, a cinnabar seal square with an invented gold sigil, a ring on top. Origin = the tip (lowest point).
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
PL_R, PL_ARC, PL_LEN, PL_TH, PL_SIZE = 0.56, (37, 27), 0.64, 0.035, 0.7
# Leader crown: band radius (index.html CONFIG.LEADER.crownR), band height, feather tip height, m.
CR_R, CR_BAND, CR_TOP = 0.30, 0.13, 0.88
# 墨 wall at true size (index.html mo Q: len 4, h 2.4, thick 0.6), m; post x places.
MW_LEN, MW_H, MW_T = 4.0, 2.4, 0.6
MW_POSTS = (-1.88, -0.94, 0.0, 0.94, 1.88)
# Decree mark: width and height m (index.html CONFIG.DECREES markW 0.3, markH 0.9).
DM_W, DM_H = 0.30, 0.90
# Decree mark: the gold frame's width over the tablet's.
DM_FRAME = 1.16
BR, INL, CIN, GOLD, LAC = 'palBronze', 'palInlay', 'palCinnabar', 'palGold', 'palLacquerPlain'
EARTH, TIMBER, STONE = 'moEarth', 'moTimber', 'moStone'
PK.mutate(globals())


def plate_pt(u, v, k):
    arc = math.radians(PL_ARC[0] + (PL_ARC[1] - PL_ARC[0]) * v); ph = (u - 0.5) * 2 * arc; r = PL_R - k * PL_TH
    return (r * math.sin(ph), (v - 0.5) * PL_LEN, r * math.cos(ph) - (PL_R - PL_TH) * math.cos(math.radians(PL_ARC[0])))

def plate_build(detail):
    PK.shell('shell', plate_pt, 8, 3, BR, 'plain')
    for q, v in enumerate((0.0, 1.0)):  # flange rim along the two curved ends
        sweep(f'rim_{q}', [plate_pt(i / 6, v, -0.3) for i in range(7)], [0.026] * 7, BR, 'flange', n=4)
    for q, u in enumerate((0.0, 1.0)):  # and the two straight sides
        prism(f'side_{q}', ngon(0.026, 4), plate_pt(u, 0.0, -0.3), plate_pt(u, 1.0, -0.3), BR, 'flange', rnd=True)
    for q, v in enumerate((0.36, 0.64)):  # two silver inlay lines over the dome (the tiger's plates carry the same pair)
        sweep(f'inlay_{q}', [plate_pt(0.08 + 0.84 * i / 6, v, -0.25) for i in range(7)], [0.013] * 7, INL, 'plain', n=3)
    c = plate_pt(0.5, 0.5, 0.0)
    prism('mark', rect(0.11, 0.11), (c[0], c[1], c[2] - 0.01), (c[0], c[1], c[2] + 0.014), BR, 'mark', rnd=False)
    if detail:
        for q, u in enumerate((0.25, 0.75)):  # torn strap lugs on the wide end
            a = plate_pt(u, 0.0, 0.2); prism(f'lug_{q}', rect(0.07, 0.03), a, (a[0], a[1] - 0.07, a[2] - 0.012), BR, 'flange', scale_b=0.6, rnd=True, up=(0, 0, 1))

def plate_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(max(x1 - x0, y1 - y0) - PL_SIZE) <= 0.06 and min(x1 - x0, y1 - y0) >= 0.55, f'plate {x1 - x0:.2f} x {y1 - y0:.2f} m, {z1 - z0:.2f} m high (game pickup {PL_SIZE} m)')
    G(z0 >= -0.01 and 0.08 <= z1 <= 0.2, f'plate lies on the ground, dome {z1:.2f} m high (0.08-0.2)')
    G({BR, INL} <= K.mats(l0), f'plate materials {sorted(K.mats(l0))}')


def crown_build(detail):
    lathe('band', [(CR_R - 0.035, 0.0), (CR_R, 0.0), (CR_R + 0.012, 0.045), (CR_R, CR_BAND), (CR_R - 0.035, CR_BAND), (CR_R - 0.035, 0.0)], GOLD, 'plain', n=12)
    lathe('band_line', [(CR_R + 0.014, 0.055), (CR_R + 0.014, 0.08)], LAC, 'plain', n=12)
    for q, (x, w, h) in enumerate(((0.0, 0.15, 0.36), (-0.15, 0.11, 0.25), (0.15, 0.11, 0.25))):  # three pointed tablets in front
        f = math.sqrt(max(CR_R ** 2 - x * x, 0.01)) - 0.012
        pr = [(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h * 0.72), (0.0, h), (-w / 2, h * 0.72)]
        prism(f'tablet_{q}', pr, (x, f, 0.02), (x, f + 0.035, 0.02), GOLD, 'plain', rnd=True)
    spheroid('stone', (0.0, CR_R + 0.03, 0.2), (0.04, 0.025, 0.05), CIN, 'plain', sg=(6, 4))
    for s in (-1, 1):  # two tall tail feathers swept up and back
        pts = [(s * 0.22, -0.16, 0.08), (s * 0.34, -0.26, 0.40), (s * 0.40, -0.25, 0.66), (s * 0.37, -0.10, CR_TOP)]
        sweep(f'feather_{s}', pts, [0.04, 0.062, 0.05, 0.0], GOLD, 'plain', n=4, flat=(1.0, 0.3), side=(s, 0, 0))
        if detail: sweep(f'quill_{s}', [(p[0] + s * 0.022, p[1] - 0.004, p[2]) for p in pts[:3]], [0.012, 0.014, 0.01], LAC, 'plain', n=3)

def crown_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(z0) <= 0.01 and 0.7 <= z1 <= 1.0, f'leader crown {z1:.2f} m high from its base (0.7-1.0; the band is {CR_BAND} m, radius {CR_R} as CONFIG.LEADER.crownR)')
    G(x1 - x0 <= 1.0, f'leader crown {x1 - x0:.2f} m wide (max 1.0: stays over one suit)')
    G({GOLD, CIN} <= K.mats(l0), f'leader crown materials {sorted(K.mats(l0))} (gold, cinnabar stone)')


def wall_build(detail):
    h = MW_LEN / 2
    prism('footing', [(-0.36, 0.0), (0.36, 0.0), (0.33, 0.30), (-0.33, 0.30)], (-h, 0, 0), (h, 0, 0), STONE, 'tile4', rnd=True)
    prism('earth', [(-0.30, 0.30), (0.30, 0.30), (0.24, 2.16), (-0.24, 2.16)], (-h + 0.04, 0, 0), (h - 0.04, 0, 0), EARTH, 'tile4', rnd=True)
    for q, x in enumerate(MW_POSTS):  # posts clasp the wall through its thickness
        prism(f'post_{q}', rect(0.2, 0.72), (x, 0, 0.26), (x, 0, 2.2), TIMBER, 'tile4', scale_b=0.86, rnd=True)
        prism(f'sleeve_{q}', rect(0.25, 0.70), (x, 0, 1.93), (x, 0, 2.1), BR, 'lozenge', scale_b=0.97, rnd=True)
    prism('cap', [(-0.40, 2.16), (0.40, 2.16), (0.40, 2.31), (-0.40, 2.31)], (-h - 0.04, 0, 0), (h + 0.04, 0, 0), TIMBER, 'tile4', rnd=True)
    prism('ridge', [(-0.44, 2.305), (0.44, 2.305), (0.0, MW_H)], (-h - 0.06, 0, 0), (h + 0.06, 0, 0), TIMBER, 'tile4', rnd=True)
    for s in (-1, 1):
        prism(f'rail_{s}', rect(0.1, 0.12), (-h, s * 0.33, 1.2), (h, s * 0.33, 1.2), TIMBER, 'tile4', rnd=True)
        for q in range(4):  # one brace per bay, leaning alternately
            xa, xb = MW_POSTS[q] + 0.1, MW_POSTS[q + 1] - 0.1
            if q % 2: xa, xb = xb, xa
            if detail or q in (0, 3): prism(f'brace_{s}{q}', rect(0.09, 0.05), (xa, s * 0.335, 0.42), (xb, s * 0.3, 2.02), TIMBER, 'tile4', rnd=True, up=(0, s, 0))
    for s in (-1, 1):  # the school's plaque on both faces: cinnabar disc, black carpenter's square
        prism(f'plaque_{s}', ngon(0.21, 8, math.pi / 8), (0, s * 0.355, 1.62), (0, s * 0.39, 1.62), CIN, 'plain', rnd=True)
        prism(f'sq_a_{s}', rect(0.05, 0.22), (0.07, s * 0.385, 1.63), (0.07, s * 0.40, 1.63), LAC, 'plain', rnd=True)
        prism(f'sq_b_{s}', rect(0.19, 0.05), (0.0, s * 0.385, 1.545), (0.0, s * 0.40, 1.545), LAC, 'plain', rnd=True)

def wall_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs((x1 - x0) - MW_LEN) <= 0.15 and abs(z1 - MW_H) <= 0.02 and MW_T <= y1 - y0 <= MW_T + 0.3, f'墨 wall {x1 - x0:.2f} x {z1:.2f} x {y1 - y0:.2f} m (game cast {MW_LEN} x {MW_H} x {MW_T}; the timber and footing stand proud of the solid)')
    G({EARTH, TIMBER, STONE, BR, CIN} <= K.mats(l0), f'墨 wall materials {sorted(K.mats(l0))} (rammed earth, timber, river stone, bronze sleeves, cinnabar plaque)')


def mark_build(detail):
    w, top, sh = DM_W / 2 - 0.02, DM_H - 0.085, 0.30
    body = [(-w, top), (w, top), (w, sh), (0.0, 0.03), (-w, sh)]
    prism('tablet', body, (0, -0.03, 0), (0, 0.03, 0), LAC, 'plain', rnd=True)
    prism('frame', [(p0 * DM_FRAME, (p1 - 0.45) * 1.07 + 0.45) for p0, p1 in body], (0, -0.014, 0), (0, 0.014, 0), GOLD, 'plain', rnd=True)
    prism('seal', rect(0.19, 0.19), (0, -0.045, top - 0.14), (0, 0.045, top - 0.14), CIN, 'plain', rnd=True)
    for q, (x, z, bw, bh) in enumerate(((0.0, top - 0.085, 0.13, 0.022), (0.0, top - 0.14, 0.13, 0.022), (0.0, top - 0.195, 0.13, 0.022), (-0.05, top - 0.14, 0.022, 0.13))):  # invented sigil
        prism(f'sigil_{q}', rect(bw, bh), (x, -0.052, z), (x, 0.052, z), GOLD, 'plain', rnd=True)
    prism('line', rect(0.022, 0.2), (0, -0.036, 0.29), (0, 0.036, 0.29), GOLD, 'plain', rnd=True)
    torus('ring', (0.0, 0.0, DM_H - 0.062), (0, 1, 0), 0.044, 0.017, BR, 'flange', sg=(8, 4))

def mark_gates(G, l0):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0)
    G(abs(z1 - DM_H) <= 0.03 and abs((x1 - x0) - DM_W) <= 0.04 and z0 >= 0.0, f'decree mark {x1 - x0:.2f} m wide x {z1:.2f} m high (game marker {DM_W} x {DM_H}), tip down at z {z0:.2f}')
    G({LAC, GOLD, CIN} <= K.mats(l0), f'decree mark materials {sorted(K.mats(l0))} (black lacquer, gold, cinnabar seal)')


PIECES = [('plate', plate_build, plate_gates, 1.2, {'size': PL_SIZE}), ('leader_crown', crown_build, crown_gates, 1.4, {'r': CR_R}),
          ('mo_wall', wall_build, wall_gates, 5.0, {'size': [MW_LEN, MW_H, MW_T]}), ('decree_mark', mark_build, mark_gates, 0.8, {'size': [DM_W, DM_H]})]

if __name__ == '__main__':
    for key, build, gates, gap, extras in PIECES:
        K.reset(); K.PARTS.clear()
        l0, l1, l2 = PK.lods_static(key, build, BUDGET)
        G = K.Gates()
        for ob, lim in zip((l0, l1, l2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
        gates(G, l0)
        l1.location.x = gap; l2.location.x = 2 * gap
        G.done()
        root = bpy.data.objects.new(key, None); bpy.context.collection.objects.link(root)
        PK.export(os.path.join(OUTDIR, f'{key}.glb'), extras, root)
