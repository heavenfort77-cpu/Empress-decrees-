# 虎符 split tiger tally (asset list C11; study art/Qin-Bronze-Castings-Study.md "虎符 tiger tally"). A lore prop in the core hall: the
# tiger tally made beast is the apex (GDD: the tiger statue under her throne), so the tally foreshadows it - a walking bronze tiger cut
# lengthwise into two halves that only match each other (the emperor's half and the general's). No gameplay.
# Qin first: Qin bronze tiger tallies (杜虎符, 新郪虎符): a small tiger in profile, split along the spine, inlaid lines on the flank.
# Ours is a display piece scaled up to read in the hall, the two halves laid apart on a black-lacquer stand. The inlaid lines are tiger
# stripes (no script, never readable). Reference only: ComfyUI round F job 2 (run 45446297299), nothing traced.
# Round 3 (FIXB 25 Nov, owner 02:2x: 'raise the budget to about 1.5k so the two halves read as a tiger at play size'): a longer, leaner
# walking tiger (1.7 m), rounded masses (chest, shoulder, haunch, big head with ear, muzzle and jaw), striding legs with paws, a long
# tail curling up, and dark inlaid stripes that follow the rounded flank (the brass sheet makes gold inlay vanish: W1a measured gold dE
# 7.3 from brass, so the inlay is dark). Rounds 1-2 (500 tris) read as a faceted cat.
# Output: tally_lod0/1/2 (both halves and the stand). Usage: python tally_blender.py OUT.glb   (TALLY_MUT=budget|stripes: gate mutations)
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import prop_kit as K
from prop_kit import P, spheroid, sweep, prism, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/tally.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (owner 25 Nov 02:2x: about 1.5k; asset list round 1-2: 500).
BUDGET = (1500, 600, 260)
# Tiger length m (display scale; the design units below are for 1.3 m), half thickness m, gap between the halves m, offset along x m.
L, HALF_T, GAP, SHIFT = 1.7, 0.12, 0.24, 0.3
# Stand: length, depth, height m (black lacquer, cinnabar edge).
STAND = (2.7, 1.05, 0.55)
# Inlaid stripe width m (>= 6 cm reads at the fight framing), how far it stands proud of the surface m, and the inlay material.
STRIPE_W, STRIPE_PROUD, STRIPE_MAT = 0.065, 0.006, 'palDark'
# Body centre line (x, z, vertical radius) in design units (1.3 m tiger, z above the stand top): rump to chest.
BODY = [(-0.6, 0.40, 0.16), (-0.42, 0.42, 0.17), (-0.22, 0.40, 0.15), (-0.02, 0.39, 0.145), (0.16, 0.41, 0.16), (0.32, 0.44, 0.18), (0.44, 0.47, 0.15)]
# Rounded masses (centre x, z; radius x, z): haunch, shoulder, head.
HAUNCH, SHOULDER, HEAD = (-0.44, 0.36, 0.17, 0.17), (0.3, 0.37, 0.13, 0.17), (0.62, 0.5, 0.15, 0.13)
# Stripes: (x, top z offset, bottom z offset as fractions of the local radius, lean in design units); on the body, shoulder, haunch, head.
STRIPES = [(-0.54, 0.9, -0.35, 0.03), (-0.36, 0.95, -0.4, 0.04), (-0.2, 0.92, -0.3, 0.04), (-0.05, 0.9, -0.3, 0.04), (0.09, 0.92, -0.3, 0.03),
           (0.22, 0.94, -0.45, 0.02), (0.36, 0.9, -0.2, 0.0), (0.56, 0.95, 0.35, -0.02), (0.64, 0.98, 0.45, -0.02)]
MUT = os.environ.get('TALLY_MUT', '')
if MUT == 'budget': BUDGET = (100, 50, 20)
if MUT == 'stripes': STRIPES = STRIPES[:3]


def body_at(x):
    """centre z and vertical radius of the body section at x (linear between the BODY points), or None outside it."""
    for (xa, za, ra), (xb, zb, rb) in zip(BODY, BODY[1:]):
        if xa <= x <= xb:
            k = (x - xa) / (xb - xa); return za + (zb - za) * k, ra + (rb - ra) * k
    return None


def surf(x, z, th):
    """outer half-thickness of the relief at (x, z): the largest of the body section and the rounded masses (ellipses squashed to th)."""
    best = 0.0
    b = body_at(x)
    if b and abs(z - b[0]) < b[1]: best = th * math.sqrt(1 - ((z - b[0]) / b[1]) ** 2)
    for cx, cz, rx, rz in (HAUNCH, SHOULDER, HEAD):
        q = ((x - cx) / rx) ** 2 + ((z - cz) / rz) ** 2
        if q < 1: best = max(best, th * math.sqrt(1 - q))
    return best


def half(side, x0, detail):
    """one half of the tiger: a relief rounded on the outside, flat on the split face (toward the other half). side +1 = the half toward the
    camera (+f), -1 = the back half."""
    zb = STAND[2]; f0 = side * GAP / 2; fc = f0 + side * HALF_T / 2; s = L / 1.3; th = HALF_T / 2
    def Pt(x, z): return (x0 + x * s, fc, zb + z * s)
    sweep(f'body_{side}', [Pt(x, z) for x, z, _ in BODY], [r * s for _, _, r in BODY], 'palBronze', 'plain', n=8, flat=(1.0, th / (0.16 * s)), side=(0, 0, 1))
    for nm, (cx, cz, rx, rz), sg in (('haunch', HAUNCH, (7, 5)), ('shoulder', SHOULDER, (7, 5)), ('head', HEAD, (9, 6))):
        spheroid(f'{nm}_{side}', Pt(cx, cz), (rx * s, th, rz * s), 'palBronze', 'plain', sg=sg)
    sweep(f'muzzle_{side}', [Pt(0.7, 0.47), Pt(0.78, 0.45), Pt(0.82, 0.42)], [0.08 * s, 0.065 * s, 0.045 * s], 'palBronze', 'plain', n=6, flat=(1.0, th * 0.8 / (0.08 * s)), side=(0, 0, 1))
    if detail:
        sweep(f'jaw_{side}', [Pt(0.6, 0.42), Pt(0.76, 0.39)], [0.06 * s, 0.035 * s], 'palBronze', 'plain', n=5, flat=(1.0, th * 0.8 / (0.06 * s)), side=(0, 0, 1))
        prism(f'ear_{side}', blade(0.09 * s, HALF_T * 0.7), Pt(0.56, 0.6), Pt(0.53, 0.7), 'palBronze', 'flange', scale_b=0.25, rnd='flat')
    # striding legs: front leg forward under the shoulder, hind leg with the hock back; flattened paws
    for k, pts, rr in ((0, [(0.32, 0.3), (0.37, 0.14), (0.39, 0.04)], [0.08, 0.055, 0.045]), (1, [(-0.44, 0.3), (-0.52, 0.15), (-0.46, 0.04)], [0.095, 0.05, 0.045])):
        sweep(f'leg_{side}{k}', [Pt(*p) for p in pts], [r * s for r in rr], 'palBronze', 'plain', n=5, flat=(1.0, th * 0.85 / (rr[0] * s)), side=(1, 0, 0))
        spheroid(f'paw_{side}{k}', Pt(pts[-1][0] + 0.04, 0.035), (0.075 * s, th * 0.85, 0.035 * s), 'palBronze', 'plain', sg=(6, 3))
    tp = [(-0.66, 0.44), (-0.8, 0.4), (-0.92, 0.32), (-1.0, 0.36), (-1.0, 0.5), (-0.92, 0.57)]
    sweep(f'tail_{side}', [Pt(*p) for p in tp], [0.05 * s, 0.045 * s, 0.04 * s, 0.04 * s, 0.035 * s, 0.0], 'palBronze', 'flange', n=5 if detail else 4)
    # inlaid stripes following the rounded flank (each point set STRIPE_PROUD outside the relief surface)
    for i, (x, top, bot, lean) in enumerate(STRIPES):
        b = body_at(x)
        if x > 0.5: zc, r = HEAD[1], HEAD[3]
        else: zc, r = b
        zs = [zc + r * (top + (bot - top) * q) for q in (0.0, 0.33, 0.66, 1.0)]
        xs = [x + lean * q for q in (0.0, 0.33, 0.66, 1.0)]
        pts = [(x0 + xx * s, f0 + side * (HALF_T / 2 + surf(xx, zz, th) + STRIPE_PROUD), zb + zz * s) for xx, zz in zip(xs, zs)]
        w = STRIPE_W / 2
        sweep(f'stripe_{side}{i}', pts, [w * 0.7, w, w * 0.8, 0.0], STRIPE_MAT, 'plain', n=3, flat=(1.0, 0.3), side=(1, 0, 0))
    if detail:  # inlaid eye
        ex, ez = 0.66, 0.53
        sweep(f'eye_{side}', [(x0 + ex * s, f0 + side * (HALF_T / 2 + surf(ex, ez, th) + STRIPE_PROUD), zb + ez * s),
                              (x0 + (ex + 0.05) * s, f0 + side * (HALF_T / 2 + surf(ex + 0.05, ez - 0.01, th) + STRIPE_PROUD), zb + (ez - 0.01) * s)],
              [0.018 * s, 0.0], STRIPE_MAT, 'plain', n=3, flat=(1.0, 0.3), side=(0, 0, 1))


def build(detail):
    prism('stand', rect(STAND[1], STAND[2]), (-STAND[0] / 2, 0, STAND[2] / 2), (STAND[0] / 2, 0, STAND[2] / 2), 'palLacquerPlain', 'plain', rnd='flat')
    if detail: prism('edge', rect(STAND[1] + 0.02, 0.06), (-STAND[0] / 2 - 0.01, 0, STAND[2] - 0.05), (STAND[0] / 2 + 0.01, 0, STAND[2] - 0.05), 'palCinnabar', 'plain', rnd='flat')
    half(+1, -SHIFT / 2, detail); half(-1, SHIFT / 2, detail)


K.reset()
lod0, lod1, lod2 = K.lods('tally', build, ratio2=0.42)
G = K.Gates()
for ob, lim in zip((lod0, lod1, lod2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
G(K.tris(lod0) >= 900, f'tally_lod0 uses the raised budget: {K.tris(lod0)} tris (min 900; rounds 1-2 had 456)')
G(GAP >= 0.15 and SHIFT >= 0.15, f'split reads: halves {GAP:.2f} m apart and offset {SHIFT:.2f} m along the body (min 0.15 each)')
G(len(STRIPES) >= 8 and STRIPE_W >= 0.06 and STRIPE_MAT in K.mats(lod0) and STRIPE_MAT in K.mats(lod1),
  f'{len(STRIPES)} inlaid stripes per half, {STRIPE_W * 100:.1f} cm wide, on LOD0 and LOD1 (min 8 stripes, 6 cm; no script)')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(z1 - STAND[2] >= 0.6 and 2.0 <= x1 - x0 <= 2.9, f'tiger {z1 - STAND[2]:.2f} m tall on a {STAND[2]} m stand (min 0.6), footprint {x1 - x0:.2f} x {y1 - y0:.2f} m (2.0-2.9)')
G({'palBronze', 'palLacquerPlain'} <= K.mats(lod1), 'bronze halves (brass sheet in the viewer) on a lacquer stand at LOD1')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
