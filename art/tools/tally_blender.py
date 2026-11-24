# 虎符 split tiger tally, round 1 (asset list C11, optional; study art/Qin-Bronze-Castings-Study.md "虎符 tiger tally"). A lore prop in the
# core hall: the tiger tally made beast is the apex (GDD: the tiger statue under her throne), so the tally echoes it - a crouching bronze
# tiger cut lengthwise into two halves that only match each other (the emperor's half and the general's). No gameplay.
# Qin first: Qin bronze tiger tallies (杜虎符, 新郪虎符): a small crouching tiger in profile, split along the spine, inlaid gold lines.
# Ours is a display piece scaled up to read in the hall (1.3 m long), the two halves laid apart on a black-lacquer stand. The gold
# lines are invented sigil strokes, never readable script. Reference only: ComfyUI round F job 2 (run 45446297299), nothing traced.
# Output: tally_lod0/1/2 (both halves and the stand). Usage: /home/claude/bpyenv/bin/python tally_blender.py OUT.glb
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import prop_kit as K
from prop_kit import P, lathe, spheroid, sweep, prism, card, ngon, rect, blade

OUT = sys.argv[-1] if sys.argv[-1].endswith('.glb') else '/tmp/tally.glb'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (asset list C11: 500).
BUDGET = (500, 200, 90)
# Tiger length m (display scale), half thickness m, gap between the halves m, the back half's offset along x m (laid apart, not matched).
L, HALF_T, GAP, SHIFT = 1.3, 0.09, 0.22, 0.25
# Stand: length, depth, height m (black lacquer, cinnabar edge).
STAND = (1.9, 0.9, 0.55)
# Gold inlay stroke width m (>= 6 cm reads at the fight framing; the study's inlay band).
INLAY_W = 0.06


def half(side, x0, detail):
    """one half of the tiger: a flat-backed relief (split face toward the other half). Round 2: rounded masses after concept 6304 (deep
    chest, heavy shoulder and haunch, big round head, thick tail curling up); round 1's plank legs and striped ball head read as a
    blocky cat. side +1 = the half toward the camera (+f), -1 = the back half."""
    zb = STAND[2]; f0 = side * GAP / 2; fc = f0 + side * HALF_T / 2  # centre of the half's thickness
    s = L / 1.3; th = HALF_T / 2
    body = [(x0 - 0.5 * s, fc, zb + 0.3 * s), (x0 - 0.15 * s, fc, zb + 0.32 * s), (x0 + 0.2 * s, fc, zb + 0.34 * s), (x0 + 0.42 * s, fc, zb + 0.38 * s)]
    sweep(f'body_{side}', body, [0.15 * s, 0.17 * s, 0.19 * s, 0.15 * s], 'palBronze', 'plain', n=6 if detail else 4, flat=(1.0, th / (0.17 * s)), side=(0, 0, 1))
    if detail: spheroid(f'haunch_{side}', (x0 - 0.38 * s, fc, zb + 0.26 * s), (0.17 * s, th, 0.18 * s), 'palBronze', 'plain', sg=(6, 4) if detail else (5, 3))
    spheroid(f'head_{side}', (x0 + 0.58 * s, fc, zb + 0.4 * s), (0.16 * s, th, 0.15 * s), 'palBronze', 'plain', sg=(7, 4) if detail else (5, 3))
    if detail:
        prism(f'ear_{side}', blade(0.07, HALF_T * 0.8), (x0 + 0.52 * s, fc, zb + 0.52 * s), (x0 + 0.48 * s, fc, zb + 0.62 * s), 'palBronze', 'flange', scale_b=0.2, rnd='flat')
        sweep(f'muzzle_{side}', [(x0 + 0.68 * s, fc, zb + 0.36 * s), (x0 + 0.78 * s, fc, zb + 0.33 * s)], [0.08 * s, 0.06 * s], 'palBronze', 'plain', n=4, flat=(1.0, th / (0.08 * s)), side=(0, 0, 1))
    for k, (lx, r0) in enumerate(((-0.38, 0.1), (0.28, 0.12))):  # crouched legs: thick, rounded, paws forward (front leg carries the shoulder)
        pts = [(x0 + lx * s, fc, zb + 0.2 * s), (x0 + (lx + 0.06) * s, fc, zb + 0.06 * s), (x0 + (lx + 0.18) * s, fc, zb + 0.035)]
        sweep(f'leg_{side}{k}', pts if detail else [pts[0], pts[2]],
              [r0 * s, 0.07 * s, 0.05 * s] if detail else [r0 * s, 0.05 * s], 'palBronze', 'plain', n=4, flat=(1.0, th / (r0 * s)), side=(0, 0, 1))
    tp = [(x0 - 0.62 * s, fc, zb + 0.3 * s), (x0 - 0.8 * s, fc, zb + 0.4 * s), (x0 - 0.74 * s, fc, zb + 0.58 * s), (x0 - 0.62 * s, fc, zb + 0.62 * s)]
    sweep(f'tail_{side}', tp if detail else [tp[0], tp[2]], [0.05 * s, 0.045 * s, 0.04 * s, 0.0] if detail else [0.05 * s, 0.0], 'palBronze', 'flange', n=4 if detail else 3)
    if detail:  # gold inlay: two invented sigil strokes along the outer side (no script), set just proud of the face
        fo = f0 + side * (HALF_T + 0.004)
        for zz, xa, xb in ((0.34, -0.42, 0.36),):
            prism(f'gold_{side}{zz}', rect(INLAY_W, 0.008), (x0 + xa * s, fo, zb + zz * s), (x0 + xb * s, fo, zb + zz * s), 'palGold', 'plain', rnd='flat', up=(0, side, 0))


def build(detail):
    prism('stand', rect(STAND[1], STAND[2]), (-STAND[0] / 2, 0, STAND[2] / 2), (STAND[0] / 2, 0, STAND[2] / 2), 'palLacquerPlain', 'plain', rnd='flat')
    if detail: prism('edge', rect(STAND[1] + 0.02, 0.06), (-STAND[0] / 2 - 0.01, 0, STAND[2] - 0.05), (STAND[0] / 2 + 0.01, 0, STAND[2] - 0.05), 'palCinnabar', 'plain', rnd='flat')
    half(+1, -SHIFT / 2, detail); half(-1, SHIFT / 2, detail)


K.reset()
lod0, lod1, lod2 = K.lods('tally', build, ratio2=0.42)
G = K.Gates()
for ob, lim in zip((lod0, lod1, lod2), BUDGET): G(K.tris(ob) <= lim, f'{ob.name} tris {K.tris(ob)} (budget {lim})')
G(GAP >= 0.15 and SHIFT >= 0.15, f'split reads: halves {GAP:.2f} m apart and offset {SHIFT:.2f} m along the body (min 0.15 each)')
G(INLAY_W >= 0.06 and 'palGold' in K.mats(lod0), f'gold inlay strokes {INLAY_W * 100:.0f} cm wide on both outer faces (invented sigils, no script)')
(x0, x1), (y0, y1), (z0, z1) = K.bounds(lod0)
G(z1 - STAND[2] >= 0.4 and x1 - x0 <= 2.0, f'tiger {z1 - STAND[2]:.2f} m tall on a {STAND[2]} m stand (reads in the hall, min 0.4), footprint {x1 - x0:.2f} x {y1 - y0:.2f} m')
G({'palBronze', 'palLacquerPlain'} <= K.mats(lod1), 'bronze halves on a lacquer stand at LOD1')
G.done()
K.export(OUT, ((lod1, 3), (lod2, 6)))
