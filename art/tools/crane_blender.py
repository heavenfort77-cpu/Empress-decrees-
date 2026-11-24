# 铜鹤 bronze crane, round 1 (asset list C4; study art/Qin-Bronze-Castings-Study.md "铜鹤 crane and 香炉 censer"). In the palace a
# smoke source: incense smoke rises from its beak and makes a cloud that blocks sight; anyone can hide in it (docs/BURNING-PALACE.md
# "Palace pieces"; CONFIG.PIECES.smoke: cloud radius 3 m, opacity 0.55, two points within 2.5 m see each other). Few, small smoke cards
# (transparency budget). Box crane in index.html: 0.8 m base, legs, body at 2.3 m, neck to 3.5 m; solid 1.2 x 1.2 m.
# Qin first: the bronze waterfowl of the First Emperor's tomb (pit K0007: cranes, one pecking a worm) is the reference for a Qin crane
# (reference only; ComfyUI round E concepts, run 45441170013, job 0, measured, nothing traced). Our own design: standing crane in profile
# (faces +x, so the long neck and beak read from the play camera), egg body, S-neck, sharp beak and toes, folded wings of cast feather
# plates with silver inlay edges, a cinnabar crown (decoration, never a hazard colour), on a turned bronze plinth with a cloud band.
# Output: crane_lod0/1/2 and crane_smoke (3 cards, material palSmoke, smoke_card.png), node crane_smoke_src (an empty at the beak tip:
# where the game's cloud and puffs start). Usage: /home/claude/bpyenv/bin/python crane_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, torus, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/crane.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (asset list C4: 1.5k / 500 each; LOD2 far).
BUDGET = (1500, 500, 200)
# Game fit: solid 1.2 x 1.2 m (index.html palSolid for smoke pieces): the plinth stands within it; the bird may overhang it only above
# OVER_Z (over the heads' reach of the solid edge, so nothing pokes out at body height) and by at most OVER m.
FOOT = 1.2
OVER_Z, OVER = 1.25, 0.45
# Height range m: taller than a suit (2.05 m) so it reads as a monument and the smoke starts above heads; the box crane reached 3.5 m.
HEIGHT = (2.6, 3.4)
# Smoke cards: count (few: transparency budget), sizes m (bottom to top), rise m, tilt toward the camera deg (play pitch 40).
SMOKE_N, SMOKE_SIZES, SMOKE_RISE, SMOKE_TILT = 3, (0.9, 1.3, 1.8), (0.35, 0.9, 1.6), 40
SMOKE_MAX = 4
# Plinth profile (radius, z) m, cloud band height range on it.
PLINTH = [(0.56, 0.0), (0.56, 0.08), (0.48, 0.12), (0.46, 0.24), (0.42, 0.3), (0.0, 0.3)]
PLINTH_BANDS = [(0.1, 0.24, 'clouds'), (0.24, 0.31, 'flange')]
# Main points of the bird (x forward, f toward the camera, z up), m.
BODY_C, BODY_R = (0.0, 0.0, 1.62), (0.42, 0.25, 0.27)
NECK = [(0.3, 0.0, 1.72), (0.44, 0.0, 1.98), (0.4, 0.0, 2.28), (0.36, 0.0, 2.52), (0.44, 0.0, 2.72), (0.54, 0.0, 2.8)]
NECK_R = [0.12, 0.075, 0.06, 0.055, 0.055, 0.06]
HEAD_C, HEAD_R = (0.58, 0.0, 2.82), (0.11, 0.07, 0.075)
BEAK = ((0.66, 0.0, 2.8), (1.0, 0.0, 2.68))
LEG_F = 0.1
SEED = 4101


def build(detail):
    # plinth: turned bronze drum, cloud band, flange lip on top
    lathe('plinth', PLINTH, 'palBronze', PLINTH_BANDS, n=18)
    # legs: hip in the body, hock (bent backward) at 0.95 m, foot on the plinth; thin, round, tapering
    for s in (-1, 1):
        f = s * LEG_F
        sweep(f'leg_{s}', [(0.02, f, 1.45), (-0.06, f, 1.2), (-0.1, f, 0.98), (-0.02, f, 0.7), (0.04, f, 0.32)], [0.06, 0.045, 0.045, 0.033, 0.03], 'palBronze', 'plain', n=6)
        if detail: spheroid(f'hock_{s}', (-0.1, f, 0.98), (0.055, 0.05, 0.06), 'palBronze', 'flange', sg=(5, 3))
        for k, (dx, df) in enumerate(((0.2, 0.0), (0.15, 0.08 * s), (0.15, -0.08 * s))):  # three toes forward: sharp
            if detail: prism(f'toe_{s}{k}', blade(0.04, 0.03), (0.04, f, 0.31), (0.04 + dx, f + df, 0.3), 'palBronze', 'flange', scale_b=0.15)
    # body: egg, tilted up at the breast (two overlapping spheroids)
    spheroid('body', BODY_C, BODY_R, 'palBronze', 'plain', sg=(12, 6))
    spheroid('breast', (0.22, 0.0, 1.7), (0.2, 0.2, 0.2), 'palBronze', 'plain', sg=(8, 5))
    # neck: S-curve, a silver inlay collar at its base; head with a sharp long beak, slightly open (the smoke comes out of it)
    sweep('neck', NECK, NECK_R, 'palBronze', 'plain', n=8)
    torus('collar', (0.33, 0.0, 1.8), (0.4, 0.0, 0.92), 0.105, 0.016, 'palInlay', 'plain', sg=(12, 3))
    spheroid('head', HEAD_C, HEAD_R, 'palBronze', 'plain', sg=(8, 5))
    prism('beak_up', blade(0.07, 0.05), BEAK[0], BEAK[1], 'palBronze', 'flange', scale_b=0.08, up=(0, 0, 1))
    if detail:
        prism('beak_lo', blade(0.05, 0.035), (BEAK[0][0], 0.0, BEAK[0][2] - 0.035), (BEAK[1][0] - 0.06, 0.0, BEAK[1][2] - 0.07), 'palBronze', 'flange', scale_b=0.1, up=(0, 0, -1))
        spheroid('crown', (0.56, 0.0, 2.89), (0.05, 0.04, 0.025), 'palCinnabar', 'plain', sg=(6, 3))
        for s in (-1, 1): spheroid(f'eye_{s}', (0.63, s * 0.062, 2.84), (0.02, 0.012, 0.02), 'palInlay', 'plain', sg=(5, 3))
    # folded wings: a flattened lofted plate on each side, silver inlay along the top edge, cast primary feathers fanning down at the back
    for s in (-1, 1):
        f = s * 0.2
        # round 1b: plain cast plates sweeping back to a long point like concept 5103 (draft: lozenge-stamped short wings read as scales)
        sweep(f'wing_{s}', [(0.3, f * 0.9, 1.78), (0.05, f * 1.15, 1.8), (-0.3, f * 1.05, 1.68), (-0.62, f * 0.6, 1.45), (-0.82, f * 0.2, 1.3)], [0.13, 0.2, 0.16, 0.08, 0.0],
              'palBronze', 'plain', n=6, flat=(0.35, 1.0))  # upright plates on the body's sides (draft: flat shelves)
        if detail:
            sweep(f'wing_inlay_{s}', [(0.25, f * 0.95, 1.89), (0.0, f * 1.18, 1.98), (-0.28, f * 1.12, 1.88)], [0.022, 0.025, 0.02], 'palInlay', 'plain', n=4)
        for k in range(2 if detail else 1):
            a = math.radians(-8 - k * 6)
            x0, z0 = -0.38 - k * 0.04, 1.66 - k * 0.03
            prism(f'prim_{s}{k}', blade(0.12, 0.03), (x0, f * (0.95 - k * 0.08), z0), (x0 - math.cos(a) * 0.36, f * (0.85 - k * 0.1), z0 + math.sin(a) * 0.36),
                  'palBronze', 'flange', scale_b=0.2, up=(0, s, 0))
    # tail: short sharp tuft
    prism('tail', blade(0.16, 0.05), (-0.36, 0.0, 1.62), (-0.68, 0.0, 1.52), 'palBronze', 'flange', scale_b=0.25, up=(0, 0, 1))


def build_smoke():
    """SMOKE_N cards rising from the beak tip, tilted toward the camera, growing as they rise."""
    tip = BEAK[1]
    for k in range(SMOKE_N):
        sz = SMOKE_SIZES[k] / 2; c = Vector((tip[0] - 0.1 * k, 0.0, tip[2] + SMOKE_RISE[k])); t = math.radians(SMOKE_TILT)
        up = Vector((0, -math.sin(t), math.cos(t))) * sz; rt = Vector((sz, 0, 0))  # card faces the camera at the play pitch
        cs = [c - rt - up, c + rt - up, c + rt + up, c - rt + up]
        card(f'puff_{k}', [(v.x, v.y, v.z) for v in cs], 'palSmoke')
    return K.finish('crane_smoke')


K.reset()
lod0, lod1, lod2 = K.lods('crane', build, ratio2=0.4)
smoke = build_smoke()
src = bpy.data.objects.new('crane_smoke_src', None); bpy.context.collection.objects.link(src); src.location = P(*BEAK[1])

G = K.Gates()
for ob, lim in zip((lod0, lod1, lod2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
low = [v.co for v in lod0.data.vertices if v.co.z < OVER_Z]; lw = max(abs(c.x) for c in low) * 2; ld = max(abs(c.y) for c in low) * 2
ov = max(max(abs(v.co.x), abs(v.co.y)) for v in lod0.data.vertices) - FOOT / 2
G(lw <= FOOT + 1e-6 and ld <= FOOT + 1e-6 and ov <= OVER, f'footprint below {OVER_Z} m {lw:.2f} x {ld:.2f} m (solid {FOOT} x {FOOT}); overhang above it {ov:.2f} m (max {OVER})')
G(HEIGHT[0] <= z1 <= HEIGHT[1], f'height {z1:.2f} m (range {HEIGHT}; suit 2.05 m, box crane 3.5 m)')
n_cards = len(smoke.data.polygons)
G(n_cards <= SMOKE_MAX and 'palSmoke' in K.mats(smoke), f'smoke: {n_cards} cards (max {SMOKE_MAX}), material palSmoke, from the beak tip at {BEAK[1][2]:.2f} m')
G(BEAK[1][2] > 2.05 + 0.4, f'smoke starts {BEAK[1][2]:.2f} m up, above a suit\'s head (2.05 m) by at least 0.4 m')
G(K.smooth_share(lod0) >= 0.5, f'smooth-shaded share {K.smooth_share(lod0):.0%} (min 50%: round body, neck, legs)')
sharp = sum(1 for p in lod0.data.polygons if not p.use_smooth)
G(sharp >= 100, f'sharp faces {sharp} (beak, toes, feathers, tail, plinth lip; min 100)')
G({'palInlay', 'palCinnabar'} <= K.mats(lod0) and 'palInlay' in K.mats(lod1), 'silver inlay (collar, wing edges, eyes) and cinnabar crown on LOD0; inlay collar kept on LOD1')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
