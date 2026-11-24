# Apex Tiger Demon (兵家 bronze tiger; GDD Lore, "Tiger Demon (apex)", research rule list; W4 overnight 25 Nov).
# The tiger tally 虎符 made beast: a long, low bronze tiger, chariot-grade segmented casting (hind, mid and fore body castings joined
# at flange seams; legs in segments with flange lips at every joint), gold inlay lines that are both its stripes and its crack
# lines (dull gold under patina asleep; glowing on waking), a dorsal inlay seam nose to tail (the split line of the tally).
# Not the door guardian: no mane, no curls, long horizontal body, flat broad skull, cheek fins, long ringed tail.
# Six sheddable outer plates (shoulders, flanks, haunches): separate nodes, each on its own bone (the game re-parents the node to
# detach it; wake peels plates 0 and 1 as the two apex minions; each Pounce sheds the next).
# Three organ weak points (Yan Shi logic, research): throat core = roar (neck underside, shown by the roar windup), eye core =
# sight (forehead), haunch cores = legs (top of the rump, both sides). Gold inlay ring around each core, no neon.
# Material states: same mesh and UVs; awake = bronze_trim.png, dormant = apex_patina.png (art/tools/apex_tex.py); apexCrack and
# apexOrgan glow only awake. School colour for the ending = a material variant (art/viewer/apex_mat.js), not a new mesh.
# Output: assets/models/apex/tiger.glb (LOD0 skinned + plates/organs; LOD1, LOD2 skinned to the same rig with their own plates and
# organs); clips dormant, wake (3 s), idle, pounce (0.5 s tell), roar (0.5 s tell). Gates printed PASS/FAIL and written to JSON.
# Usage: python apex_tiger.py OUT.glb [GATES.json]
import bpy, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
import apex_kit as K
from apex_kit import P, Loft, floft, loft, spheroid, prism, tube, ring, strip, shell, blade, ngon, rect

args = [a for a in sys.argv if a.endswith('.glb') or a.endswith('.json')]
OUT = next((a for a in args if a.endswith('.glb')), '/tmp/tiger.glb')
GJ = next((a for a in args if a.endswith('.json')), OUT.replace('.glb', '_gates.json'))

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Model scale over the design numbers below (design: 4.1 m nose to rump, 1.9 m to the ear tips; the box statue is 2.6 x 2.55 x 5.2 m, its solid 3.2 x 5.0 m).
SCALE = 1.15
# Triangle budgets per LOD (owner brief: 15k / 3k / 1k; character rule 10-15k).
BUDGET = (15000, 3000, 1000)
# Segment scale per LOD (1 = full).
SEGS = (1.0, 0.5, 0.34)
# Inlay line (stripe / crack) width, m (study: details meant to read are at least 6 cm).
STRIPE_W = 0.065
# Statue solid in the game (index.html statue solid 3.2 x 5.0 m) and its box height (2.55 m): dormant pose limits.
SOLID_W, SOLID_L, STATUE_H = 3.2, 5.0, 2.55
# Clip timing, s: wake (CONFIG.APEX.wakeS 3), pounce windup (GDD: 0.5 s telegraph), roar windup.
WAKE_S, POUNCE_WIND, ROAR_WIND = 3.0, 0.5, 0.5
# Tell gates: minimum time (fairness rule 0.4 s), hip drop and tail rise at the pounce windup, jaw angle at the roar windup (m, m, deg).
TELL_MIN, HIP_DROP_MIN, TAIL_RISE_MIN, JAW_MIN = 0.4, 0.25, 0.3, 25
# Plates peeled at the wake (the two apex minions) and how far they must travel during it (m).
PEEL = (0, 1); PEEL_MIN = 0.4

K.S['scale'] = SCALE
TORSO_SECS = [(-1.82, 1.12, .20, .22), (-1.66, 1.16, .38, .38), (-1.40, 1.19, .47, .46), (-1.05, 1.19, .44, .43), (-0.70, 1.17, .39, .39),
              (-0.30, 1.18, .37, .37), (0.15, 1.21, .42, .44), (0.50, 1.23, .48, .52), (0.85, 1.27, .48, .52), (1.08, 1.32, .40, .42), (1.24, 1.38, .30, .32)]
HEAD_SECS = [(1.45, 1.70, .30, .30), (1.62, 1.72, .40, .33), (1.80, 1.73, .41, .30), (1.98, 1.71, .33, .24), (2.12, 1.67, .23, .18), (2.25, 1.64, .17, .14), (2.32, 1.62, .10, .08)]
TAIL = [(0, -1.76, 1.18), (0, -2.02, 1.04), (0, -2.26, 0.82), (0, -2.46, 0.58), (0.04, -2.64, 0.42), (0.1, -2.80, 0.40)]
TORSO = Loft([(0, f, z) for f, z, _, _ in TORSO_SECS], [(w, h) for _, _, w, h in TORSO_SECS], 2.4)
# Plates: (name, bone it rides, f0, f1, t0, t1) on the torso surface; t = 0 is the +x side, 90 the top.
PLATES = [('plate_0', 'chest', 0.42, 1.0, -25, 55), ('plate_1', 'chest', 0.42, 1.0, 125, 205),
          ('plate_2', 'spine', -0.62, 0.08, -20, 50), ('plate_3', 'spine', -0.62, 0.08, 130, 200),
          ('plate_4', 'hips', -1.62, -1.0, -35, 45), ('plate_5', 'hips', -1.62, -1.0, 135, 215)]
PLATE_OUT, PLATE_T = 0.03, 0.05

ORGANS = {}  # name -> (bone, design point, normal)


def organ(name, bone, c, n, lod):
    """a weak-point core: a lens boss (apexOrgan) seated in a gold inlay ring (apexInlay)."""
    n = Vector(n).normalized(); c = Vector(c)
    if lod < 2:
        spheroid(name, tuple(c + n * 0.02), (0.1, 0.05, 0.1), 'apexOrgan', bone, axis=tuple(n), segs=(10, 6), sep=name)
        ring(name + '_ring', tuple(c + n * 0.01), tuple(n), 0.14, 0.04, 'apexInlay', bone, 'inlay', sides=12, sep=name)
    else:
        prism(name, ngon(0.12, 6), tuple(c), tuple(c + n * 0.04), 'apexOrgan', bone, sep=True)
    ORGANS[name] = (bone, c, n)


def build(lod):
    det = lod == 0; K.S['seg'] = SEGS[lod]; K.S['detail'] = det; sub = 2 if lod == 0 else 1
    sfx = '' if lod == 0 else f'_lod{lod}'
    # body castings: hind, mid, fore (each its own bone), flange seams between them
    for nm, bone, a, b in (('hind', 'hips', 0, 4), ('mid', 'spine', 4, 6), ('fore', 'chest', 6, 10)):
        floft('body_' + nm, TORSO_SECS[a:b + 1], 'apexBronze', bone, 'plain', M=24, sub=sub)
    for f, bone in ((-0.70, 'spine'), (0.15, 'chest')):
        s = TORSO.s_at_f(f); c, side, v, hw, hh, d = TORSO.frame(s)
        floft('seam_%s' % bone, [(f - 0.035, c.z, hw + 0.03, hh + 0.03), (f + 0.035, c.z, hw + 0.03, hh + 0.03)], 'apexBronze', bone, 'flange', M=24)
    # neck and head
    NECK = Loft([(0, 1.10, 1.36), (0, 1.32, 1.48), (0, 1.55, 1.62)], [(.32, .34), (.30, .30), (.27, .27)], 2.4)
    loft('neck', NECK, 'apexBronze', 'neck', 'clouds', M=20, sub=sub)
    head, HEAD = floft('head', HEAD_SECS, 'apexBronze', 'head', 'plain', n_exp=2.6, M=24, sub=sub)
    floft('jaw', [(1.68, 1.46, .26, .09), (1.92, 1.44, .23, .09), (2.12, 1.44, .16, .07), (2.24, 1.45, .10, .05)], 'apexBronze', 'jaw', 'lozenge', M=16)
    floft('mouth', [(1.80, 1.50, .21, .045), (2.0, 1.50, .19, .045), (2.2, 1.50, .11, .03)], 'apexDark', 'head', M=12)
    prism('nose', [(-0.07, -0.03), (0.07, -0.03), (0.045, 0.03), (-0.045, 0.03)], (0, 2.04, 1.86), (0, 2.34, 1.66), 'apexBronze', 'head', 'flange', scale_b=1.4)
    for s in (-1, 1):
        h = K.hit(head, (s * 0.16, 3.0, 1.83), (0, -1, 0))
        e, n = h if h else (Vector((s * 0.16, 2.05, 1.83)), Vector((0, 1, 0)))
        spheroid(f'eye_{s}', tuple(e - n * 0.01), (0.085, 0.03, 0.045), 'apexInlay', 'head', axis=tuple(n), segs=(10, 6))
        prism(f'pupil_{s}', rect(0.018, 0.07), tuple(e + n * 0.005), tuple(e + n * 0.03), 'apexDark', 'head', up=(0, 0, 1)) if det else None
        prism(f'brow_{s}', blade(0.07, 0.06), tuple(e + Vector((-s * 0.11, 0.02, 0.09))), tuple(e + Vector((s * 0.15, -0.1, 0.07))), 'apexBronze', 'head', 'flange')
        q, nq = HEAD.point(HEAD.s_at_f(1.55), 90 - s * 35, 0.0)
        prism(f'ear_{s}', [(-0.1, -0.03), (0.1, -0.03), (0.06, 0.03), (-0.06, 0.03)], tuple(q - nq * 0.04), tuple(q + nq * 0.2 + Vector((0, -0.04, 0.04))), 'apexBronze', 'head', 'flange', scale_b=0.2)
        for k, t in enumerate((-20, 0, 20) if det else (0,)):
            q, nq = HEAD.point(HEAD.s_at_f(1.74), (t if s > 0 else 180 - t), -0.02)
            prism(f'fin_{s}{k}', blade(0.11, 0.035), tuple(q), tuple(q + Vector((s * 0.15, -0.24, -0.05 + t * 0.003))), 'apexBronze', 'head', 'flange', scale_b=0.12)
        if det:
            prism(f'fang_{s}', blade(0.05, 0.045), (s * 0.09, 2.2, 1.52), (s * 0.09, 2.22, 1.37), 'apexInlay', 'head', scale_b=0.1)
            prism(f'lfang_{s}', blade(0.04, 0.035), (s * 0.07, 2.17, 1.47), (s * 0.07, 2.19, 1.57), 'apexInlay', 'jaw', scale_b=0.1)
    # legs: segmented castings with flange lips at every joint, round masses, sharp claws
    for side, s in (('L', 1), ('R', -1)):
        x = s * 0.42
        loft(f'fl_up_{side}', Loft([(s * .42, .86, 1.45), (s * .44, .80, 1.08), (x, .72, .76)], [(.19, .27), (.17, .2), (.14, .15)]), 'apexBronze', f'fl_up_{side}', M=16, sub=sub)
        ring(f'elbow_{side}', (x, .72, .74), (0, .13, -1), .165, .05, 'apexBronze', f'fl_lo_{side}')
        loft(f'fl_lo_{side}', Loft([(x, .72, .76), (x, .76, .46), (x, .80, .22)], [(.14, .15), (.13, .14), (.12, .12)]), 'apexBronze', f'fl_lo_{side}', 'flange', M=16, sub=sub)
        ring(f'wrist_{side}', (x, .80, .21), (0, .1, -1), .14, .045, 'apexBronze', f'fl_paw_{side}')
        floft(f'fl_paw_{side}', [(.66, .11, .13, .10), (.80, .12, .17, .12), (.96, .10, .17, .10), (1.06, .07, .13, .07)], 'apexBronze', f'fl_paw_{side}', x=x, M=16)
        loft(f'hl_up_{side}', Loft([(s * .40, -1.36, 1.36), (s * .44, -1.20, 1.0), (x, -1.03, .72)], [(.2, .34), (.17, .25), (.13, .15)]), 'apexBronze', f'hl_up_{side}', M=16, sub=sub)
        ring(f'knee_{side}', (x, -1.03, .71), (0, -.43, -.32), .14, .05, 'apexBronze', f'hl_lo_{side}')
        loft(f'hl_lo_{side}', Loft([(x, -1.03, .72), (x, -1.25, .54), (x, -1.45, .40)], [(.12, .13), (.10, .11), (.09, .10)]), 'apexBronze', f'hl_lo_{side}', 'flange', M=14, sub=sub)
        ring(f'hock_{side}', (x, -1.45, .39), (0, .15, -.28), .105, .04, 'apexBronze', f'hl_ft_{side}')
        loft(f'hl_ft_{side}', Loft([(x, -1.45, .40), (x, -1.38, .24), (x, -1.31, .12)], [(.08, .09), (.08, .085), (.085, .085)]), 'apexBronze', f'hl_ft_{side}', M=12)
        floft(f'hl_paw_{side}', [(-1.42, .09, .13, .09), (-1.28, .10, .16, .10), (-1.13, .09, .15, .09), (-1.05, .06, .11, .06)], 'apexBronze', f'hl_paw_{side}', x=x, M=16)
        if det:
            for pre, f0 in (('fl', 1.04), ('hl', -1.07)):
                for k in range(4):
                    tx = x + (k - 1.5) * 0.08
                    spheroid(f'{pre}toe_{side}{k}', (tx, f0, .065), (.045, .06, .055), 'apexBronze', f'{pre}_paw_{side}', segs=(8, 5))
                    prism(f'{pre}claw_{side}{k}', blade(0.04, 0.035), (tx, f0 + .04, .07), (tx, f0 + .13, .015), 'apexInlay', f'{pre}_paw_{side}', scale_b=0.1)
        # thigh and upper-arm stripes (inlay = crack lines), on the outer face of each leg
        TH = Loft([(s * .40, -1.36, 1.36), (s * .44, -1.20, 1.0), (x, -1.03, .72)], [(.2, .34), (.17, .25), (.13, .15)])
        to = 0 if s > 0 else 180
        for k, sv in enumerate((0.5, 0.9, 1.3) if lod < 2 else (0.9,)):
            strip(f'thst_{side}{k}', TH, [(sv + 0.12 * abs(t) / 60, to + t) for t in range(-60, 61, 20 if det else 40)], STRIPE_W, 'apexCrack', f'hl_up_{side}')
        if lod < 2:
            FU = Loft([(s * .42, .86, 1.45), (s * .44, .80, 1.08), (x, .72, .76)], [(.19, .27), (.17, .2), (.14, .15)])
            for k, sv in enumerate((0.9, 1.4)):
                strip(f'fust_{side}{k}', FU, [(sv + 0.1 * abs(t) / 60, to + t) for t in range(-60, 61, 20 if det else 40)], STRIPE_W, 'apexCrack', f'fl_up_{side}')
    # tail: ringed segments, flange lips, a sharp finial
    for i in range(5):
        r0 = 0.1 - i * 0.012
        tube(f'tail_{i}', TAIL[i], TAIL[i + 1], r0, r0 - 0.01, 'apexBronze', f'tail_{i}', 'plain' if i % 2 else 'flange', sides=10)
        if i > 0: ring(f'tring_{i}', TAIL[i], tuple(Vector(TAIL[i + 1]) - Vector(TAIL[i])), r0 + 0.025, 0.035, 'apexBronze', f'tail_{i}', sides=10)
    prism('finial', blade(0.12, 0.08), TAIL[5], (0.14, -2.92, 0.54), 'apexInlay', 'tail_4', scale_b=0.1)
    # stripes over the back (between the plates) and the dorsal tally seam; stripe ends slant back toward the sides
    fs = [-1.55, -1.3, -1.05, -0.85, -0.5, -0.2, 0.05, 0.35, 0.6, 0.85, 1.05] if lod < 2 else [-1.3, -0.85, -0.2, 0.35, 0.85]
    for k, f in enumerate(fs):
        strip(f'stripe_{k}', TORSO, [(TORSO.s_at_f(f - 0.12 * abs(math.cos(math.radians(t)))), t) for t in range(50, 131, 10 if det else 40)],
              STRIPE_W, 'apexCrack', 'hips' if f < -0.7 else 'spine' if f < 0.15 else 'chest')
    for a, b, bone in ((-1.8, -0.7, 'hips'), (-0.7, 0.15, 'spine'), (0.15, 1.2, 'chest')):
        n = 8 if det else 3
        strip(f'seam_line_{bone}', TORSO, [(TORSO.s_at_f(a + (b - a) * i / n), 90) for i in range(n + 1)], 0.05, 'apexCrack', bone)
    strip('seam_line_head', HEAD, [(HEAD.s_at_f(1.46 + 0.5 * i / 4), 90) for i in range(5)], 0.05, 'apexCrack', 'head')
    if lod < 2:
        for s in (-1, 1):
            strip(f'cheek_st_{s}', HEAD, [(HEAD.s_at_f(1.7 + 0.04 * i), (10 if s > 0 else 170) + s * 12 * i) for i in range(4)], STRIPE_W, 'apexCrack', 'head')
    # plates (sheddable; separate nodes on their own bones) with a workshop mark and two inlay lines each
    for nm, bone, f0, f1, t0, t1 in PLATES:
        s0, s1 = TORSO.s_at_f(f0), TORSO.s_at_f(f1)
        shell(nm + sfx, TORSO, s0, s1, t0, t1, PLATE_OUT, PLATE_T, 'apexBronze', 'b_' + nm, 'clouds', ns=6, nt=6, sep=nm + sfx)
        if lod < 2:
            for k, u in enumerate((0.3, 0.7)):
                sv = s0 + (s1 - s0) * u
                strip(f'{nm}_st{k}{sfx}', TORSO, [(sv, t0 + (t1 - t0) * j / 4) for j in range(5)], STRIPE_W, 'apexCrack', 'b_' + nm, off=PLATE_OUT + PLATE_T + 0.004, sep=nm + sfx)
            q, n = TORSO.point((s0 + s1) / 2, (t0 + t1) / 2, PLATE_OUT + PLATE_T)
            prism(f'{nm}_mark{sfx}', rect(0.16, 0.16), tuple(q - n * 0.01), tuple(q + n * 0.02), 'apexBronze', 'b_' + nm, 'mark', up=(0, 1, 0), sep=nm + sfx)
    # organs: throat (roar), eye (sight), haunches (legs)
    q, n = NECK.point(1.0, -90, 0.0); organ('organ_throat' + sfx, 'neck', q, n, lod)
    q, n = HEAD.point(HEAD.s_at_f(1.74), 90, 0.0); organ('organ_eye' + sfx, 'head', q, n, lod)
    for side, t in (('L', 52), ('R', 128)):
        q, n = TORSO.point(TORSO.s_at_f(-1.28), t, 0.0); organ(f'organ_legs_{side}' + sfx, 'hips', q, n, lod)


BONES = [('root', (0, 0, 0), (0, 0.4, 0), None), ('hips', (0, -1.3, 1.18), (0, -0.6, 1.18), 'root'), ('spine', (0, -0.6, 1.18), (0, 0.2, 1.2), 'hips'),
         ('chest', (0, 0.2, 1.2), (0, 1.05, 1.3), 'spine'), ('neck', (0, 1.1, 1.38), (0, 1.5, 1.6), 'chest'), ('head', (0, 1.5, 1.64), (0, 2.25, 1.62), 'neck'),
         ('jaw', (0, 1.72, 1.48), (0, 2.2, 1.44), 'head')]
for side, s in (('L', 1), ('R', -1)):
    x = s * 0.42
    BONES += [(f'fl_up_{side}', (x, .85, 1.38), (x, .72, .74), 'chest'), (f'fl_lo_{side}', (x, .72, .74), (x, .80, .20), f'fl_up_{side}'),
              (f'fl_paw_{side}', (x, .80, .20), (x, 1.08, .06), f'fl_lo_{side}'),
              (f'hl_up_{side}', (x, -1.35, 1.22), (x, -1.02, .70), 'hips'), (f'hl_lo_{side}', (x, -1.02, .70), (x, -1.45, .38), f'hl_up_{side}'),
              (f'hl_ft_{side}', (x, -1.45, .38), (x, -1.30, .10), f'hl_lo_{side}'), (f'hl_paw_{side}', (x, -1.30, .10), (x, -1.06, .05), f'hl_ft_{side}')]
BONES += [(f'tail_{i}', TAIL[i], TAIL[i + 1], 'hips' if i == 0 else f'tail_{i - 1}') for i in range(5)]
for nm, bone, f0, f1, t0, t1 in PLATES:
    q, n = TORSO.point(TORSO.s_at_f((f0 + f1) / 2), (t0 + t1) / 2, PLATE_OUT)
    BONES.append(('b_' + nm, tuple(q), tuple(q + n * 0.25), bone))

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps = K.FPS
G = K.Gates()
lods, extras = [], []
for lod in (2, 1, 0):
    ORGANS.clear(); build(lod)
    body, ex = K.finish('tiger_lod%d' % lod if lod else 'tiger_lod0', lod == 0)
    lods.insert(0, body); extras.insert(0, ex)
organs0 = dict(ORGANS)

# LOD1 and LOD2 bodies decimated to fit beside their plates and organs (vertex groups survive: parts are separate islands)
for i in (1, 2):
    rest = sum(K.tris(o) for o, _ in extras[i]); room = BUDGET[i] - rest - 20
    if K.tris(lods[i]) > room: K.decimate(lods[i], room / K.tris(lods[i]))
arm = K.make_rig('tiger_rig', BONES)
for body in lods: K.skin(body, arm)
for ex in extras:
    for ob, bone in ex: K.bone_parent(ob, arm, bone)

# Poses -----------------------------------------------------------------------------------------------------------------
# Standing stance for the clips: head carried below the shoulder hump (concept 5107: head 0.52 of the shoulder height, forward).
REST = {'neck': {'p': -16}, 'head': {'p': -4}}
DORMANT = {'hips': {'loc': (0, 0, -0.52)}, 'spine': {'p': 0}, 'neck': {'p': 4}, 'head': {'p': 10},
           'fl_up_L': {'p': -24}, 'fl_lo_L': {'p': 72}, 'fl_paw_L': {'p': 22}, 'fl_up_R': {'p': -24}, 'fl_lo_R': {'p': 72}, 'fl_paw_R': {'p': 22},
           'hl_up_L': {'p': 33}, 'hl_lo_L': {'p': -20}, 'hl_ft_L': {'p': 20}, 'hl_paw_L': {'p': 7},
           'hl_up_R': {'p': 33}, 'hl_lo_R': {'p': -20}, 'hl_ft_R': {'p': 20}, 'hl_paw_R': {'p': 7},
           'tail_0': {'p': 56}, 'tail_1': {'p': 0, 'y': 80}, 'tail_2': {'p': -50, 'y': 135}, 'tail_3': {'p': -42, 'y': 165}, 'tail_4': {'p': -7, 'y': 180}}
STAND_STEP = {'fl_up_L': {'p': 22}, 'fl_lo_L': {'p': 30}, 'fl_paw_L': {'p': 10}, 'neck': {'p': -8}, 'head': {'p': 2}}
peel = lambda k: {f'b_plate_{i}': {'loc': (0.0, 0.0, 0.0)} for i in PEEL} if k == 0 else {
    f'b_plate_{i}': {'loc': ((1 if i == 0 else -1) * 0.55 * k, 0.15 * k, 0.4 * k), 'r': (1 if i == 0 else -1) * 25 * k} for i in PEEL}
WINDUP = {'hips': {'loc': (0, -0.12, -0.32)}, 'spine': {'p': -6}, 'neck': {'p': -2}, 'head': {'p': 4}, 'jaw': {'p': -16},
          'fl_up_L': {'p': -22}, 'fl_lo_L': {'p': 26}, 'fl_up_R': {'p': -22}, 'fl_lo_R': {'p': 26},
          'hl_up_L': {'p': 34}, 'hl_lo_L': {'p': -26}, 'hl_ft_L': {'p': 24}, 'hl_up_R': {'p': 34}, 'hl_lo_R': {'p': -26}, 'hl_ft_R': {'p': 24},
          'tail_0': {'p': -55}, 'tail_1': {'p': -45}, 'tail_2': {'p': -35}, 'tail_3': {'p': -20}, 'tail_4': {'p': -5}}
LEAP = {'hips': {'loc': (0, 0.45, 0.18)}, 'spine': {'p': 6}, 'head': {'p': 2}, 'jaw': {'p': -32},
        'fl_up_L': {'p': 70}, 'fl_lo_L': {'p': 75}, 'fl_up_R': {'p': 66}, 'fl_lo_R': {'p': 70},
        'hl_up_L': {'p': -40}, 'hl_ft_L': {'p': -30}, 'hl_up_R': {'p': -38}, 'hl_ft_R': {'p': -30}, 'tail_0': {'p': -12}}
LAND = {'hips': {'loc': (0, 0.35, -0.14)}, 'spine': {'p': -4}, 'jaw': {'p': -10}, 'fl_up_L': {'p': 18}, 'fl_up_R': {'p': 14}, 'hl_up_L': {'p': 15}, 'hl_up_R': {'p': 15}}
ROAR_UP = {'spine': {'p': 7}, 'chest': {'p': 14}, 'neck': {'p': 42}, 'head': {'p': 28}, 'jaw': {'p': -14}, 'fl_up_L': {'p': 0}, 'fl_up_R': {'p': 0}, 'hl_up_L': {'p': 0}, 'hl_up_R': {'p': 0}}
ROAR_HOLD = {'spine': {'p': 4}, 'chest': {'p': 8}, 'neck': {'p': 22}, 'head': {'p': 10}, 'jaw': {'p': -26}, 'fl_up_L': {'p': 0}, 'fl_up_R': {'p': 0}, 'hl_up_L': {'p': 0}, 'hl_up_R': {'p': 0}}

def M_all(objs):
    pts = K.world_pts(objs); xs = [p.x for p in pts]; fs = [p.y for p in pts]; zs = [p.z for p in pts]
    return dict(w=max(xs) - min(xs), l=max(fs) - min(fs), h=max(zs), zmin=min(zs))

body0 = [lods[0]] + [o for o, _ in extras[0]]
rest_m = M_all(body0)
hips_rest = K.bone_pt(arm, 'hips', False).z; tail_rest = K.bone_pt(arm, 'tail_4').z; throat_rest = K.bone_pt(arm, 'neck', False).z
plate_rest = {i: K.bone_pt(arm, f'b_plate_{i}', False) for i in PEEL}
def jaw_ang():
    a = K.bone_pt(arm, 'jaw') - K.bone_pt(arm, 'jaw', False); h = K.bone_pt(arm, 'head') - K.bone_pt(arm, 'head', False)
    return math.degrees(math.atan2(h.z, h.y) - math.atan2(a.z, a.y))  # signed, side plane: + = jaw dropped
jaw_rest = jaw_ang()
throat_obj = [o for o, _ in extras[0] if o.name == 'organ_throat'][0]
throat_rest_z = max(p.z for p in K.world_pts([throat_obj]))

def low_parts():
    dg = bpy.context.evaluated_depsgraph_get(); oe = lods[0].evaluated_get(dg); me = oe.to_mesh(); low = {}
    names = [g.name for g in lods[0].vertex_groups]
    for v in me.vertices:
        w = K.Mm(oe.matrix_world @ v.co); g = names[v.groups[0].group] if v.groups else '?'
        a = low.setdefault(g, [9, 9, -9]); a[0] = min(a[0], w.z); a[1] = min(a[1], w.y); a[2] = max(a[2], w.y)
    oe.to_mesh_clear()
    return ('low', sorted((v[0], g) for g, v in low.items())[:4], 'back', sorted((v[1], g) for g, v in low.items())[:4], 'front', sorted((v[2], g) for g, v in low.items())[-3:])
dm = K.clip(arm, 'dormant', [(0, DORMANT), (1.0, DORMANT)], measure={0.0: lambda: (M_all(body0), print('dormant lowest parts', low_parts()))[0]})[0.0]
wk = K.clip(arm, 'wake', [(0, DORMANT), (0.8, DORMANT), (1.4, {**DORMANT, 'neck': {'p': 6}, 'head': {'p': 10}, 'jaw': {'p': -20}}),
                          (2.1, ('blend', DORMANT, {**STAND_STEP, **peel(0.3)}, 0.55)), (2.6, {**STAND_STEP, **peel(0.6)}), (WAKE_S, {**REST, **peel(1.0)})],
            measure={WAKE_S: lambda: {i: K.bone_pt(arm, f'b_plate_{i}', False) for i in PEEL}})[WAKE_S]
K.clip(arm, 'idle', [(0, REST), (1.0, {'chest': {'loc': (0, 0, 0.025)}, 'neck': {'p': -13}, 'head': {'p': -1, 'y': 6}, 'tail_3': {'y': 10}, 'tail_4': {'y': 16}}), (2.0, REST)])
pw = K.clip(arm, 'pounce', [(0, REST), (POUNCE_WIND, WINDUP), (POUNCE_WIND + 0.35, LEAP), (POUNCE_WIND + 0.65, LAND), (POUNCE_WIND + 1.0, REST)],
            measure={POUNCE_WIND: lambda: (K.bone_pt(arm, 'hips', False).z, K.bone_pt(arm, 'tail_4').z)})[POUNCE_WIND]
def jaw_deg(): return jaw_ang() - jaw_rest
rw = K.clip(arm, 'roar', [(0, REST), (ROAR_WIND, ROAR_UP), (ROAR_WIND + 0.4, ROAR_HOLD), (ROAR_WIND + 0.9, REST)],
            measure={ROAR_WIND: lambda: (jaw_deg(), K.bone_pt(arm, 'neck', False).z, max(p.z for p in K.world_pts([o for o, _ in extras[0] if o.name.startswith('organ_throat')])))})[ROAR_WIND]
K.unmute_all(arm); bpy.context.scene.frame_set(1)

# Gates -----------------------------------------------------------------------------------------------------------------
for i, (ob, lim) in enumerate(zip(lods, BUDGET)):
    n = K.tris(ob) + sum(K.tris(o) for o, _ in extras[i])
    G(n <= lim, f'tiger LOD{i} tris {n} (body {K.tris(ob)} + plates/organs {n - K.tris(ob)}; budget {lim})')
ok = all(len(v.groups) == 1 and abs(v.groups[0].weight - 1) < 1e-6 for ob in lods for v in ob.data.vertices)
ok2 = all(o.parent == arm and o.parent_type == 'BONE' and o.parent_bone for ex in extras for o, _ in ex)
G(ok and ok2, f'every vertex on one bone (3 skinned LOD bodies rigid 100%; {sum(len(e) for e in extras)} plate/organ nodes bone-parented)')
pl = [[o for o, _ in ex if o.name.split('_lod')[0] in [p[0] for p in PLATES]] for ex in extras]
marks = [o for o in pl[0] if any(m.name == 'apexBronze' for m in o.data.materials) and len(o.data.polygons) > 60]
G(all(len(p) == 6 for p in pl[:1]) and all(len(p) == 6 for p in pl) and len(marks) == 6 and all(o.parent_bone.startswith('b_plate_') for p in pl for o in p),
  f'sheddable plates: {[len(p) for p in pl]} per LOD, each on its own plate bone, {len(marks)} workshop marks')
G(set(organs0) == {'organ_throat', 'organ_eye', 'organ_legs_L', 'organ_legs_R'} and organs0['organ_throat'][0] == 'neck' and organs0['organ_eye'][0] == 'head',
  'three organs: throat (neck bone, roar), eye (head, sight), haunches L+R (hips, legs), each in a gold inlay ring')
G(2.2 <= rest_m['h'] <= 2.7, f"standing height {rest_m['h']:.2f} m (over the 2.05 m suit box, at most the 2.55 m box statue + 0.15: band 2.2-2.7), length {rest_m['l']:.2f} m incl. tail, width {rest_m['w']:.2f} m")
G(dm['w'] <= SOLID_W and dm['l'] <= SOLID_L and dm['h'] <= STATUE_H + 0.05, f"dormant crouch {dm['w']:.2f} x {dm['l']:.2f} m, {dm['h']:.2f} m tall (statue solid {SOLID_W} x {SOLID_L}, box {STATUE_H} m)")
G(abs(rest_m['zmin']) <= 0.03 and dm['zmin'] >= -0.06, f"feet on the floor: standing lowest {rest_m['zmin']:+.3f} m, dormant lowest {dm['zmin']:+.3f} m")
mv = min((wk[i] - plate_rest[i]).length for i in PEEL)
G(abs(WAKE_S - 3.0) < 1e-6 and mv >= PEEL_MIN, f'wake {WAKE_S:.1f} s (CONFIG.APEX.wakeS 3); plates {PEEL} peel {mv:.2f} m (min {PEEL_MIN})')
hd, tr = hips_rest - pw[0], pw[1] - tail_rest
G(POUNCE_WIND >= TELL_MIN and hd >= HIP_DROP_MIN and tr >= TAIL_RISE_MIN, f'pounce tell {POUNCE_WIND} s (min {TELL_MIN}): hips drop {hd:.2f} m (min {HIP_DROP_MIN}), tail tip rise {tr:.2f} m (min {TAIL_RISE_MIN})')
G(ROAR_WIND >= TELL_MIN and rw[0] >= JAW_MIN and rw[2] - throat_rest_z >= 0.15, f'roar tell {ROAR_WIND} s: jaw open {rw[0]:.0f} deg (min {JAW_MIN}), throat core up {rw[2] - throat_rest_z:.2f} m (min 0.15)')
polys = lods[0].data.polygons; share = sum(p.area for p in polys if p.use_smooth) / sum(p.area for p in polys)
G(share >= 0.5, f'smooth-shaded share {share:.0%} of surface area (round forms, min 50%)')
mats = {m.name for ob in lods for m in ob.data.materials}
crack = sum(1 for p in polys if lods[0].data.materials[p.material_index].name == 'apexCrack')
G({'apexBronze', 'apexInlay', 'apexCrack', 'apexDark'} <= mats and crack > 0 and STRIPE_W >= 0.06,
  f'material slots {sorted(mats)}; crack inlay faces {crack}, line width {STRIPE_W * 100:.1f} cm (min 6)')

lods[1].location.x = 0; lods[2].location.x = 0
K.export(OUT)
anims, nodes, gm, _ = K.glb_info(OUT)
need = {'dormant', 'wake', 'idle', 'pounce', 'roar'}
G(need <= set(anims) and all(f'plate_{i}' in nodes for i in range(6)) and 'organ_eye' in nodes, f'GLB: clips {sorted(anims)}; plate and organ nodes present; materials {sorted(gm)}')
p, n = G.summary('tiger')
G.dump(GJ, {'tris': [K.tris(o) + sum(K.tris(x) for x, _ in extras[i]) for i, o in enumerate(lods)], 'rest': rest_m, 'dormant': dm})
