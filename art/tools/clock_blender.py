# 铜壶滴漏 bronze water clock, round 1 (asset list C5; study art/Qin-Bronze-Castings-Study.md "铜壶滴漏 water clock"). One per wing; its
# water level counts down to her next burning of that wing (the timer in the scene as well as the HUD; CONFIG.PIECES2.clock.steps 48:
# the water is written only when its step changes) (docs/BURNING-PALACE.md "Palace pieces"). Box clock in index.html: plinth 1.4 x 0.3 x
# 1.4 m, two posts and a beam to 2.4 m, a water column 0.9 x 2 m scaled to the time left; solid 1.4 x 1.4 m.
# Qin first: the Qin and Western Han outflow clepsydra (泄水型沉箭漏): a tall cylindrical bronze pot on short legs that drains through a
# spout at the bottom; a float carries an indicator rod (箭) up through the lid, which sinks as the water falls. That is a countdown by
# nature. Our own design and one labelled invention for readability: a cast sight slot down the front of the pot (flanged edges) shows
# the water column inside, so the level reads at play size like the box column did; the rod's gold graduation rings sink into the lid.
# Stacked in steps: the pot stands on a two-tier bronze stand; the spout drips into a catch basin in front, whose water rises.
# Reference only: ComfyUI round E job 2 (run 45441170013): pick 5305 (a tall bronze cylinder with ring flanges on a footed tray),
# alternates 5301 (stacked round pots), 5308 (vessels with indicator rods); read by eye on 5305: the cylinder about 0.8 of the height and
# 0.25 of it wide, three ring flanges, the tray about 0.75 of the height wide. Built: pot 1.6 m of 2.25 m, 0.72 m wide (0.32), three
# flanges, stand 1.3 m wide.
# Output: clock_lod0/1/2 (static body), clock_water (origin at the pot floor: scale Z = level 1..0), clock_arrow (float and rod: moves
# with the water top), clock_catch (catch-basin water: scale Z rises 0..1), clock_drip (thin stream card); clip 'countdown' (1 s:
# t 0 = full, t 1 = empty) on the three moving nodes; extras give the heights. Usage: python clock_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Matrix
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, torus, ngon, rect, blade, disc

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/clock.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (asset list C5: 1.5k / 500), moving nodes included in LOD0.
BUDGET = (1500, 500, 200)
# Game fit: solid 1.4 x 1.4 m; height near the box frame's 2.4 m.
FOOT = 1.4
HEIGHT = (2.1, 3.0)
# Pot: centre f (pushed back so the catch basin fits in front), radius, bottom and rim z; ring flanges z; sight slot half angle deg
# (facing the camera, +f) and its flange width.
POT_F, POT_R, POT_Z = -0.18, 0.36, (0.62, 2.22)
POT_FLANGES = (1.0, 1.5, 2.0)
SLOT_HALF = 32
# Water inside: radius, floor z (the clock_water origin), full height m.
WATER_R, WATER_Z0, WATER_H = 0.33, 0.66, 1.5
# Rod (箭): length m, float radius, graduation rings every m (gold inlay), ring width m (>= 6 cm reads at the fight framing).
ROD_L, ROD_R, FLOAT_R, GRAD, GRAD_W = 0.75, 0.03, 0.2, 0.18, 0.06
# Stand: two tiers (radius, z top), octagonal.
STAND = [(0.68, 0.0), (0.68, 0.16), (0.64, 0.2), (0.0, 0.2)]
# Catch basin: centre (x, f), radius, rim z; its water full height m.
BASIN = (-0.3, 0.32, 0.22, 0.25)
CATCH_H = 0.2
# Readability: the water top must move at least this many metres from full to empty (48 steps: 3 cm per step at 1.5 m).
MIN_TRAVEL = 1.2


def pot_wall(detail):
    """the pot wall as a turned shell with the sight slot cut out (a partial lathe, outside and inside), flanged slot edges."""
    M = K.segs(20, 10); a0 = math.radians(90 + SLOT_HALF); a1 = math.radians(90 - SLOT_HALF + 360)
    import bmesh
    bm = bmesh.new(); prof_o = [(POT_R, POT_Z[0]), (POT_R, POT_Z[1])]; prof_i = [(POT_R - 0.03, POT_Z[1]), (POT_R - 0.03, POT_Z[0] + 0.04)]
    rings = []
    for rr, z in prof_o + prof_i:
        rings.append([bm.verts.new(P(math.cos(a0 + (a1 - a0) * i / M) * rr, POT_F + math.sin(a0 + (a1 - a0) * i / M) * rr, z)) for i in range(M + 1)])
    for a, b in zip(rings, rings[1:]):
        for i in range(M): bm.faces.new([a[i], a[i + 1], b[i + 1], b[i]])
    for i in (0, M): bm.faces.new([rings[0][i], rings[1][i], rings[2][i], rings[3][i]])  # slot edge faces
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put('pot', bm, 'palBronze', [(POT_Z[0], POT_Z[0] + 0.3, 'lozenge'), (POT_Z[0] + 0.3, POT_Z[1] - 0.2, 'plain'), (POT_Z[1] - 0.2, POT_Z[1] + 0.1, 'clouds')], True)
    # dark inside (back wall seen through the slot) and the floor
    lathe('inside', [(POT_R - 0.035, POT_Z[0] + 0.04), (POT_R - 0.035, POT_Z[1])], 'palDark', 'plain', n=12, cf=POT_F)
    for s in (-1, 1):  # flanged slot edges: sharp cast lips the full height
        a = math.radians(90 + s * SLOT_HALF); x, f = math.cos(a) * (POT_R + 0.01), POT_F + math.sin(a) * (POT_R + 0.01)
        prism(f'slot_{s}', rect(0.05, 0.035), (x, f, POT_Z[0] + 0.05), (x, f, POT_Z[1] - 0.02), 'palBronze', 'flange', up=(math.cos(a), math.sin(a), 0))


def arc_band(name, rr, z0, z1, row):
    """a turned band around the pot that stops at the sight slot (outer face, top and bottom lips)."""
    import bmesh
    M = K.segs(20, 10); a0 = math.radians(90 + SLOT_HALF); a1 = math.radians(90 - SLOT_HALF + 360); bm = bmesh.new(); rings = []
    for r_, z in ((POT_R, z0), (rr, z0), (rr, z1), (POT_R, z1)):
        rings.append([bm.verts.new(P(math.cos(a0 + (a1 - a0) * i / M) * r_, POT_F + math.sin(a0 + (a1 - a0) * i / M) * r_, z)) for i in range(M + 1)])
    for a, b in zip(rings, rings[1:]):
        for i in range(M): bm.faces.new([a[i], a[i + 1], b[i + 1], b[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    K.put(name, bm, 'palBronze', row, True)


def build(detail):
    # stand in two steps: a low octagonal tier under everything, a round upper tier under the pot (the basin stands on the low tier in front)
    lathe('stand', STAND, 'palBronze', [(0.0, 0.17, 'lozenge'), (0.17, 0.2, 'flange')], n=8)
    lathe('tier', [(0.42, 0.2), (0.42, 0.4), (0.38, 0.44), (0.0, 0.44)], 'palBronze', [(0.18, 0.45, 'flange')], n=14, cf=POT_F)
    for k in range(3):  # three short hoof legs under the pot
        a = math.radians(90 + 120 * k); x, f = math.cos(a) * 0.28, POT_F + math.sin(a) * 0.28
        prism(f'leg_{k}', ngon(0.06, 6), (x, f, POT_Z[0] + 0.02), (x * 1.08, f + (f - POT_F) * 0.08, 0.44), 'palBronze', 'flange', scale_b=1.3, rnd=True)
    pot_wall(detail)
    lathe('floor', [(POT_R, POT_Z[0]), (0.0, POT_Z[0] - 0.03)], 'palBronze', 'plain', n=12, cf=POT_F)
    for i, z in enumerate(POT_FLANGES):  # ring flanges (segmented casting), cut at the slot (draft: full rings crossed the window like cage bars)
        if not detail and i != 1: continue
        arc_band(f'flange_{i}', POT_R + 0.04, z - 0.03, z + 0.03, 'flange')
    # lid ring and a crossbar holding the rod guide (the rod passes through its centre); silver inlay on the lid ring
    lathe('lid', [(POT_R + 0.05, POT_Z[1]), (POT_R + 0.05, POT_Z[1] + 0.06), (POT_R - 0.06, POT_Z[1] + 0.06), (POT_R - 0.06, POT_Z[1] + 0.01)], 'palBronze', 'flange', n=20, cf=POT_F)
    prism('bar', rect(0.07, 0.06), (-POT_R, POT_F, POT_Z[1] + 0.09), (POT_R, POT_F, POT_Z[1] + 0.09), 'palBronze', 'lozenge')
    if detail:
        lathe('lid_inlay', [(POT_R + 0.052, POT_Z[1] + 0.0), (POT_R + 0.052, POT_Z[1] + 0.06)], 'palInlay', 'plain', n=20, cf=POT_F)
        torus('guide', (0, POT_F, POT_Z[1] + 0.13), (0, 0, 1), 0.06, 0.018, 'palBronze', 'flange', sg=(8, 3))
    # spout: a dragon-head spout low on the pot toward the basin, open mouth (sharp upper jaw)
    a = math.atan2(BASIN[1] - POT_F, BASIN[0]); c, sn = math.cos(a), math.sin(a)
    s0 = (c * POT_R, POT_F + sn * POT_R, 0.78); s1 = (c * (POT_R + 0.2), POT_F + sn * (POT_R + 0.2), 0.74)
    sweep('spout', [s0, s1], [0.06, 0.04], 'palBronze', 'mask', n=6)
    if detail:
        prism('spout_jaw', blade(0.06, 0.03), s1, (s1[0] + c * 0.06, s1[1] + sn * 0.06, s1[2] + 0.02), 'palBronze', 'flange', scale_b=0.2)
        spheroid('spout_head', (c * (POT_R + 0.12), POT_F + sn * (POT_R + 0.12), 0.8), (0.07, 0.07, 0.05), 'palBronze', 'mask', sg=(6, 3))
    # catch basin: a shallow turned bronze bowl on the floor in front
    bx, bf, br, bz = BASIN
    zb = 0.2  # on the low tier
    lathe('basin', [(br * 0.7, zb), (br, zb + 0.06), (br + 0.02, zb + bz), (br - 0.02, zb + bz), (br - 0.03, zb + 0.06), (0.0, zb + 0.05)], 'palBronze', [(0.0, 0.6, 'clouds')], n=14, cx=bx, cf=bf)
    return s1


def nodes():
    """the moving parts, each its own object: water column (origin on the pot floor), rod and float (origin at the float), catch water,
    drip stream."""
    K.PARTS.clear(); lathe('w', [(WATER_R, 0.0), (WATER_R, WATER_H), (0.0, WATER_H)], 'palWater', 'plain', n=14, cf=POT_F)
    water = K.finish('clock_water'); water.location = (0, 0, WATER_Z0)
    lathe('fl', [(FLOAT_R, -0.03), (FLOAT_R, 0.02), (0.0, 0.03)], 'palBronze', 'flange', n=10, cf=POT_F)
    lathe('rod', [(ROD_R, 0.0), (ROD_R, ROD_L), (0.0, ROD_L + 0.06)], 'palBronze', 'plain', n=6, cf=POT_F)
    z = GRAD
    while z < ROD_L - 0.05:
        lathe(f'grad_{z:.2f}', [(ROD_R + 0.008, z), (ROD_R + 0.008, z + GRAD_W)], 'palGold', 'plain', n=6, cf=POT_F); z += GRAD
    arrow = K.finish('clock_arrow'); arrow.location = (0, 0, WATER_Z0 + WATER_H)
    bx, bf, br, bz = BASIN
    lathe('c', [(br - 0.035, 0.0), (br - 0.035, CATCH_H), (0.0, CATCH_H)], 'palWater', 'plain', n=12, cx=bx, cf=bf)
    catch = K.finish('clock_catch'); catch.location = (0, 0, 0.26)
    return water, arrow, catch


K.reset()
K.Q['seg'] = 0.5; build(False); lod1 = K.finish('clock_lod1')
build(False); lod2 = K.decimate(K.finish('clock_lod2'), 0.36)
K.Q['seg'] = 1.0; spout = build(True); lod0 = K.finish('clock_lod0', True)
water, arrow, catch = nodes()
bx, bf, br, bz = BASIN
sx, sf, sz = spout
K.PARTS.clear(); card('drip', [(sx + 0.06 - 0.012, sf, sz), (sx + 0.06 + 0.012, sf, sz), (bx + 0.012, bf, 0.32), (bx - 0.012, bf, 0.32)], 'palSpray')
drip = K.finish('clock_drip')
for ob in (water, arrow, catch, drip): ob.parent = lod0
water['level'] = 'scale Z = level (1 full .. 0 empty); origin on the pot floor at %.2f m, full height %.2f m' % (WATER_Z0, WATER_H)
arrow['level'] = 'position Z = %.2f + %.2f x level (rides the water top)' % (WATER_Z0, WATER_H)
catch['level'] = 'scale Z = 1 - level (the catch basin fills)'

# countdown clip: t 0 full, t 1 empty (the game sets the level directly from its step; the clip is for the viewer and as a reference)
bpy.context.scene.render.fps = 60
for f, lv in ((1, 1.0), (61, 0.02)):
    water.scale = (1, 1, lv); water.keyframe_insert('scale', frame=f)
    arrow.location = (0, 0, WATER_Z0 + WATER_H * lv); arrow.keyframe_insert('location', frame=f)
    catch.scale = (1, 1, max(0.02, 1 - lv)); catch.keyframe_insert('scale', frame=f)
for ob in (water, arrow, catch):
    for fc in ob.animation_data.action.fcurves if hasattr(ob.animation_data.action, 'fcurves') else []:
        for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
water.scale = (1, 1, 1); arrow.location = (0, 0, WATER_Z0 + WATER_H); catch.scale = (1, 1, 0.02)
for ob, nm in ((water, 'countdown_water'), (arrow, 'countdown_arrow'), (catch, 'countdown_catch')): ob.animation_data.action.name = nm

G = K.Gates()
movers = (water, arrow, catch, drip)
t0 = K.tris(lod0) + sum(K.tris(o) for o in movers)
G(t0 <= BUDGET[0], f'clock lod0 + moving nodes tris {t0} (budget {BUDGET[0]})')
for ob, lim in ((lod1, BUDGET[1]), (lod2, BUDGET[2])): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(x1 - x0 <= FOOT + 1e-6 and y1 - y0 <= FOOT + 1e-6, f'footprint {x1 - x0:.2f} x {y1 - y0:.2f} m (solid {FOOT} x {FOOT})')
top = z1 + 0  # rod top at full
rod_top = WATER_Z0 + WATER_H + ROD_L + 0.06
G(HEIGHT[0] <= max(z1, rod_top) <= HEIGHT[1], f'height {max(z1, rod_top):.2f} m at full (pot rim {POT_Z[1]:.2f} m; range {HEIGHT}; box frame 2.4 m)')
G(WATER_H >= MIN_TRAVEL and WATER_Z0 + WATER_H <= POT_Z[1], f'water top travels {WATER_H:.2f} m full to empty (min {MIN_TRAVEL}: {WATER_H / 48 * 100:.1f} cm per step of 48), stays inside the pot')
# the slot faces the camera: its chord width and that the water column shows through it
chord = 2 * math.sin(math.radians(SLOT_HALF)) * POT_R
G(chord >= 0.3 and WATER_R > POT_R * math.cos(math.radians(SLOT_HALF)) - 0.2, f'sight slot {chord:.2f} m wide facing the camera (min 0.3 m = 33 px at the fight framing), water column r {WATER_R} inside it')
sink = ROD_L - (POT_Z[1] - WATER_Z0)  # rod top above the rim when empty (negative = hidden in the pot)
G(GRAD_W >= 0.06 and sink < 0.3, f'rod: gold graduation rings {GRAD_W * 100:.0f} cm every {GRAD} m; at empty the rod top is {sink:+.2f} m from the rim (sinks into the pot)')
acts = [o.animation_data.action.name for o in (water, arrow, catch)]
G(all(o.parent == lod0 for o in movers) and len(acts) == 3, f'moving nodes parented to clock_lod0; clips {acts}')
G({'palWater', 'palGold'} <= K.mats(water) | K.mats(arrow) and 'palInlay' in K.mats(lod0), 'water (game colour), gold rod rings, silver inlay lid ring')
G(K.smooth_share(lod0) >= 0.5, f'smooth-shaded share {K.smooth_share(lod0):.0%} (min 50%)')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
