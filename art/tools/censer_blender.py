# 香炉 bronze censer, round 1 (asset list C4; study art/Qin-Bronze-Castings-Study.md "铜鹤 crane and 香炉 censer"). In the palace a
# smoke source: incense smoke makes a cloud that blocks sight; anyone can hide in it (docs/BURNING-PALACE.md "Palace pieces";
# CONFIG.PIECES.smoke). Few, small smoke cards. Box censer in index.html: 1.2 x 1.0 x 1.2 m plus 0.8 x 0.5 x 0.8 m, 1.5 m tall; solid
# 1.2 x 1.2 m.
# Qin first: a Warring States 豆-form incense burner (round foot, stem, bowl, domed lid pierced for the smoke). The Han 博山炉 mountain lid
# is later; our lid is our own design: a dome of flame-cloud tongues (they rhyme with the guardian beast's mane) with dark smoke holes
# between them, a bird-knob finial. Reference only: ComfyUI round E concepts (run 45441170013, job 1), measured, nothing traced.
# Output: censer_lod0/1/2, censer_smoke (4 cards, palSmoke), censer_smoke_src (empty at the lid top). Usage: python censer_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, torus, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/censer.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (asset list C4: 1.5k / 500 each).
BUDGET = (1500, 500, 200)
# Game fit: solid 1.2 x 1.2 m; height near the box censer's 1.5 m.
FOOT = 1.2
HEIGHT = (1.3, 1.9)
# Outside profile (radius, z) m from the foot up over the lid; bands by height.
PROF = [(0.55, 0.0), (0.55, 0.06), (0.44, 0.13), (0.2, 0.34), (0.1, 0.6), (0.17, 0.68), (0.12, 0.76), (0.36, 0.88), (0.5, 1.0),
        (0.53, 1.1), (0.55, 1.12), (0.55, 1.18), (0.0, 1.18)]
# Lid dome (inside the openwork: dark, so the gaps between the tongues read as pierced; draft: bronze dome with round black holes read as
# rivets on a sea mine).
DOME = [(0.52, 1.18), (0.44, 1.34), (0.24, 1.53), (0.0, 1.61)]
BANDS = [(0.0, 0.14, 'lozenge'), (0.6, 0.78, 'flange'), (0.86, 1.07, 'clouds'), (1.1, 1.19, 'flange')]
# Lid tongues (lower tier; the upper has two fewer), length m.
TONGUES, TONGUE_L = 8, 0.3
# Smoke cards: sizes m, rise above the lid top m, tilt toward the camera deg; max cards.
SMOKE_SIZES, SMOKE_RISE, SMOKE_TILT, SMOKE_MAX = (0.8, 1.1, 1.4, 1.8), (0.25, 0.7, 1.2, 1.8), 40, 4


def r_at(z):
    for (r0, z0), (r1, z1) in zip(PROF, PROF[1:]):
        if z0 <= z <= z1 and z1 > z0: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.0


def dome_r(z):
    for (r0, z0), (r1, z1) in zip(DOME, DOME[1:]):
        if z0 <= z <= z1: return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.0


def build(detail):
    lathe('body', PROF, 'palBronze', BANDS, n=16)
    lathe('dome', DOME, 'palDark', 'plain', n=12)
    # two ring handles on the bowl (on x: they read from the camera side), each from a small mask boss
    for s in (-1, 1):  # at 45 deg off the camera axis, hanging flat on the bowl (铺首衔环; draft rings stood out past the solid)
        a = math.radians(90 - s * 45); c, sn = math.cos(a), math.sin(a)
        if detail: spheroid(f'boss_{s}', (c * 0.52, sn * 0.52, 1.0), (0.06, 0.06, 0.06), 'palBronze', 'mask', sg=(6, 4))
        torus(f'ring_{s}', (c * 0.54, sn * 0.54, 0.92), (c, sn, 0), 0.075, 0.018, 'palBronze', 'flange', sg=(10, 3))
    # lid: flame-cloud tongues rising and curling outward from the dome; dark smoke holes between them (silver rims on LOD0)
    # two tiers of broad leaf tongues lying on the dome, tips curling out (draft: the section was squashed the wrong way and made spikes)
    for tier, (zt, nt, w) in enumerate(((1.19, TONGUES, 0.15), (1.36, TONGUES - 2, 0.12))):  # (LOD1: lower tier only)
        if not detail and tier: continue
        nt = nt if detail else 6
        for k in range(nt):
            a = math.radians(k * 360 / nt + 22.5 * tier); c, sn = math.cos(a), math.sin(a)
            r0 = dome_r(zt) + 0.01; r1 = dome_r(zt + TONGUE_L * 0.6) + 0.04
            base = (c * r0, sn * r0, zt); mid = (c * r1, sn * r1, zt + TONGUE_L * 0.6); tip = (c * (r1 + 0.13), sn * (r1 + 0.13), zt + TONGUE_L * 0.92)  # tip curls out and over (a cloud tongue)
            hi = (c * (r1 + 0.05), sn * (r1 + 0.05), zt + TONGUE_L * 0.9)
            pts, rad = ([base, mid, hi, tip], [w, w * 0.8, w * 0.45, 0.0]) if detail else ([base, mid, tip], [w, w * 0.7, 0.0])
            sweep(f'tongue_{tier}{k}', pts, rad, 'palBronze', 'flange', n=4, flat=(1.0, 0.3), rnd=True, side=(-sn, c, 0))
    if detail:
        torus('lid_inlay', (0.0, 0.0, 1.2), (0, 0, 1), 0.535, 0.014, 'palInlay', 'plain', sg=(20, 3))
    # finial: a crouching bird knob on the lid top, sharp beak and tail
    spheroid('knob', (0.0, 0.0, 1.66), (0.09, 0.07, 0.07), 'palBronze', 'plain', sg=(7, 4))
    prism('knob_beak', blade(0.04, 0.03), (0.07, 0.0, 1.7), (0.17, 0.0, 1.68), 'palBronze', 'flange', scale_b=0.1)
    prism('knob_tail', blade(0.08, 0.03), (-0.06, 0.0, 1.68), (-0.18, 0.0, 1.76), 'palBronze', 'flange', scale_b=0.2)


def build_smoke():
    top = max(z for r, z in DOME) + 0.15
    for k, (sz, rise) in enumerate(zip(SMOKE_SIZES, SMOKE_RISE)):
        sz /= 2; c = Vector((0.06 * (k % 2) - 0.03, 0.0, top + rise)); t = math.radians(SMOKE_TILT)
        up = Vector((0, -math.sin(t), math.cos(t))) * sz; rt = Vector((sz, 0, 0))
        cs = [c - rt - up, c + rt - up, c + rt + up, c - rt + up]
        card(f'puff_{k}', [(v.x, v.y, v.z) for v in cs], 'palSmoke')
    return K.finish('censer_smoke')


K.reset()
lod0, lod1, lod2 = K.lods('censer', build, ratio2=0.38)
smoke = build_smoke()
src = bpy.data.objects.new('censer_smoke_src', None); bpy.context.collection.objects.link(src); src.location = P(0, 0, max(z for r, z in DOME) + 0.15)

G = K.Gates()
for ob, lim in zip((lod0, lod1, lod2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(x1 - x0 <= FOOT + 1e-6 and y1 - y0 <= FOOT + 1e-6, f'footprint {x1 - x0:.2f} x {y1 - y0:.2f} m (solid {FOOT} x {FOOT})')
G(HEIGHT[0] <= z1 <= HEIGHT[1], f'height {z1:.2f} m (range {HEIGHT}; box censer 1.5 m)')
n_cards = len(smoke.data.polygons)
G(n_cards <= SMOKE_MAX and 'palSmoke' in K.mats(smoke), f'smoke: {n_cards} cards (max {SMOKE_MAX}), palSmoke, from the lid top')
G(K.smooth_share(lod0) >= 0.5, f'smooth-shaded share {K.smooth_share(lod0):.0%} (min 50%: turned body)')
sharp = sum(1 for p in lod0.data.polygons if not p.use_smooth)
# changed with the design (draft: spiky flat tongues read as a sea mine; now rounded cloud tongues with curled tips): the tips must stand
# clear of the dome so the openwork silhouette reads, and the finial, foot and rim keep sharp parts
curl = max(math.hypot(v.co.x, v.co.y) - dome_r(v.co.z) for v in lod0.data.vertices if 1.25 < v.co.z < 1.6)
G(curl >= 0.1 and sharp >= 30, f'lid tongue tips stand {curl:.2f} m clear of the dome (min 0.1); sharp faces {sharp} (finial beak and tail, min 30)')
G('palDark' in K.mats(lod0) and 'palDark' in K.mats(lod1) and 'palInlay' in K.mats(lod0), 'openwork lid (dark dome under the tongues) on LOD0 and LOD1; silver inlay lid ring on LOD0')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
