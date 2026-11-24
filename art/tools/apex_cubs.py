# Cubs and hunt minions: Stalker (正) and Howler (奇) (GDD "Minions 奇正", "Cubs and minions: body and speed"; research: chariot running
# gear, ox or tortoise movement, ding or lei hull; W4 overnight 25 Nov). Each cub is one of the Tiger Demon's shed plates grown legs, so
# its hull is cast like the tiger's plates: the same bronze trim sheet, flange rims and cast seams, gold inlay crack lines (apexCrack,
# glowing while alive), a workshop mark on the hull; feet are tread bogies (track belt over chariot wheels).
# Concepts (ComfyUI run 45435750508, reference only, nothing traced): Stalker from 5208 (segmented tortoise shell; alt 5216 low hull: L/H 1.96,
# legs 0.37 of the height); Howler from 5218 (ding hull on tall legs: legs 0.49 of the height, rim flange, side lugs); ringed leg
# joints and ornament bands from 5213.
# Stalker: low tortoise dome on four short splayed legs, long tread bogies with two wheels, a low wedge head that bites straight ahead.
# Howler: a ding cauldron hull on four thick column legs (knee flanges; round 2: bigger hull, narrower rim, thicker legs), short bogies with one big spoked chariot wheel, a raised head with a
# flared bell mouth (the howl) and two sharp back-swept horns.
# Output: assets/models/apex/stalker.glb, howler.glb (LOD0/1/2 skinned to one rig; clips idle, move (wheels roll), attack (0.5 s tell)).
# Usage: python apex_cubs.py OUTDIR [GATES.json]
import bpy, math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathutils import Vector
import apex_kit as K
from apex_kit import P, Loft, floft, loft, spheroid, prism, tube, ring, strip, blade, ngon, rect

args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
OUTDIR = next((a for a in args if not a.endswith('.json') and not a.endswith('.py')), '/tmp/cubs')
GJ = next((a for a in args if a.endswith('.json')), os.path.join(OUTDIR, 'cubs_gates.json'))

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets per LOD (owner brief: 4k / 1.5k / 500).
BUDGET = (4000, 1500, 500)
# Segment scale per LOD.
SEGS = (1.0, 0.5, 0.3)
# Game sizes: cub hit radius (CONFIG.STALKER.r / HOWLER.r 0.5 m), suit box 2.05 m tall.
CUB_R, SUIT_H = 0.5, 2.05
# Attack clip: windup (tell; fairness rule >= 0.4 s), strike, recover (s).
WIND, STRIKE, BACK = 0.5, 0.15, 0.35
# Tell gates at the windup end: head tip moved (m) and jaw open (deg).
TIP_MIN, JAW_MIN, TELL_MIN = 0.15, 25, 0.4
# Inlay line width (m, study minimum 6 cm).
STRIPE_W = 0.06
# Move clip length (s) and wheel turns per clip.
MOVE_S, TURNS = 1.0, 1


def bogie(nm, x, f, z, L, r_wheel, n_wheels, bone, wheel_bones, det, spoked=False):
    """a tread bogie: a stadium track belt (lozenge tread row) around n wheels; hubs and wheels on the outer side on their own bones."""
    h = r_wheel * 2 + 0.04
    prof = []
    for k in range(8):  # stadium in the (f, z) plane, extruded along x
        a = -math.pi / 2 + math.pi * k / 7; prof.append((L / 2 - h / 2 + math.cos(a) * h / 2, math.sin(a) * h / 2))
    for k in range(8):
        a = math.pi / 2 + math.pi * k / 7; prof.append((-L / 2 + h / 2 + math.cos(a) * h / 2, math.sin(a) * h / 2))
    sx = 1 if x > 0 else -1
    prism(nm + '_belt', [(-p[1], p[0]) for p in prof], (x - sx * 0.06, f, z), (x + sx * 0.06, f, z), 'apexBronze', bone, 'lozenge', up=(0, 1, 0), rnd=True)
    cs = [f] if n_wheels == 1 else [f - L / 2 + h / 2, f + L / 2 - h / 2]
    for k, (cf, wb) in enumerate(zip(cs, wheel_bones)):
        rw = r_wheel * (1.35 if spoked else 0.85)
        prism(f'{nm}_wheel{k}', ngon(rw, K.seg(14, 6)), (x + sx * 0.06, cf, z), (x + sx * 0.085, cf, z), 'apexBronze', wb, 'flange', rnd=True)
        prism(f'{nm}_hub{k}', ngon(0.045, 6), (x + sx * 0.085, cf, z), (x + sx * 0.13, cf, z), 'apexInlay', wb, scale_b=0.6)
        if spoked and det:
            for sp in range(6):
                a = sp * math.pi / 3
                prism(f'{nm}_spoke{k}{sp}', rect(0.025, 0.025), (x + sx * 0.09, cf, z), (x + sx * 0.09, cf + math.cos(a) * rw * 0.92, z + math.sin(a) * rw * 0.92), 'apexBronze', wb, rnd=True)


def hull_marks(nm, L, s_mid, det, bone='hull'):
    q, n = L.point(s_mid, 90, 0.0)
    prism(nm + '_mark', rect(0.13, 0.13), tuple(q - n * 0.01), tuple(q + n * 0.02), 'apexBronze', bone, 'mark', up=(0, 1, 0))


def build_stalker(lod):
    det = lod == 0; K.S['seg'] = SEGS[lod]; K.S['detail'] = det; sub = 2 if lod == 0 else 1
    secs = [(-0.62, 0.62, .22, .14), (-0.48, 0.64, .42, .24), (-0.15, 0.66, .5, .3), (0.2, 0.66, .49, .29), (0.45, 0.64, .38, .22), (0.58, 0.62, .22, .12)]
    _, H = floft('hull', secs, 'apexBronze', 'hull', 'plain', n_exp=2.3, M=22, sub=sub)
    floft('skirt', [(-0.6, 0.47, .5, .035), (-0.2, 0.47, .58, .04), (0.25, 0.47, .57, .04), (0.56, 0.47, .45, .035)], 'apexBronze', 'hull', 'flange', n_exp=3, M=20)
    for f in (-0.2, 0.22):  # cast seams across the dome (concept 5216)
        s = H.s_at_f(f); strip(f'seam{f}', H, [(s, t) for t in range(0, 181, 20 if det else 45)], 0.035, 'apexBronze', 'hull')
    prism('keel', blade(0.08, 0.06), (0, -0.55, 0.9), (0, 0.5, 0.94), 'apexBronze', 'hull', 'flange', up=(0, 0, 1)) if det else None
    for k, f in enumerate((-0.38, -0.05, 0.3) if lod < 2 else (-0.05,)):
        strip(f'crack{k}', H, [(H.s_at_f(f - 0.1 * abs(math.cos(math.radians(t)))), t) for t in range(30, 151, 15 if det else 60)], STRIPE_W, 'apexCrack', 'hull')
    if lod < 2: hull_marks('hull', H, H.s_at_f(0.05), det)
    # head: low wedge forward, sharp crest, gold slit eyes, jaw on its own bone
    _, HD = floft('head', [(0.5, 0.6, .17, .14), (0.72, 0.56, .16, .12), (0.9, 0.52, .11, .08), (0.98, 0.5, .05, .04)], 'apexBronze', 'head', 'plain', n_exp=2.6, M=16)
    floft('jaw', [(0.58, 0.44, .13, .05), (0.8, 0.43, .11, .045), (0.95, 0.44, .05, .03)], 'apexBronze', 'jaw', 'lozenge', M=12)
    prism('crest', blade(0.07, 0.05), (0, 0.55, 0.76), (0, 0.92, 0.6), 'apexBronze', 'head', 'flange', scale_b=0.3, up=(0, 0, 1))
    for s in (-1, 1):
        spheroid(f'eye{s}', (s * 0.11, 0.8, 0.6), (0.05, 0.03, 0.025), 'apexInlay', 'head', segs=(8, 5))
        if det: prism(f'fang{s}', blade(0.035, 0.03), (s * 0.06, 0.9, 0.48), (s * 0.06, 0.92, 0.38), 'apexInlay', 'head', scale_b=0.1)

    # legs and bogies: short splayed legs, long tread bogies with two wheels
    for nm, sx, sf in (('FL', 1, 1), ('FR', -1, 1), ('BL', 1, -1), ('BR', -1, -1)):
        hip = (sx * 0.36, sf * 0.32, 0.55); foot = (sx * 0.46, sf * 0.36, 0.2)
        tube(f'leg{nm}', hip, foot, 0.09, 0.07, 'apexBronze', f'leg_{nm}', 'flange', sides=10)
        ring(f'ank{nm}', foot, (sx * 0.12, 0.04, -0.35), 0.085, 0.035, 'apexBronze', f'bogie_{nm}', sides=10)
        bogie(f'bg{nm}', sx * 0.46, sf * 0.36, 0.1, 0.44, 0.08, 2, f'bogie_{nm}', [f'wheel_{nm}0', f'wheel_{nm}1'], det)
    tube('tail', (0, -0.6, 0.62), (0, -0.82, 0.55), 0.05, 0.02, 'apexBronze', 'tail', 'flange', sides=8)
    prism('tailtip', blade(0.06, 0.04), (0, -0.82, 0.55), (0, -0.94, 0.5), 'apexInlay', 'tail', scale_b=0.1)


def bones_stalker():
    B = [('root', (0, 0, 0), (0, 0.3, 0), None), ('hull', (0, -0.4, 0.62), (0, 0.4, 0.62), 'root'), ('head', (0, 0.5, 0.58), (0, 0.98, 0.5), 'hull'),
         ('jaw', (0, 0.58, 0.45), (0, 0.95, 0.44), 'head'), ('tail', (0, -0.6, 0.62), (0, -0.94, 0.5), 'hull')]
    for nm, sx, sf in (('FL', 1, 1), ('FR', -1, 1), ('BL', 1, -1), ('BR', -1, -1)):
        f0, f1 = sf * 0.36 - 0.22 + 0.1, sf * 0.36 + 0.22 - 0.1
        B += [(f'leg_{nm}', (sx * 0.36, sf * 0.32, 0.55), (sx * 0.46, sf * 0.36, 0.2), 'hull'), (f'bogie_{nm}', (sx * 0.46, sf * 0.36, 0.2), (sx * 0.46, sf * 0.36 + 0.2, 0.1), f'leg_{nm}'),
              (f'wheel_{nm}0', (sx * 0.46, f0, 0.1), (sx * 0.58, f0, 0.1), f'bogie_{nm}'), (f'wheel_{nm}1', (sx * 0.46, f1, 0.1), (sx * 0.58, f1, 0.1), f'bogie_{nm}')]
    return B


def build_howler(lod):
    det = lod == 0; K.S['seg'] = SEGS[lod]; K.S['detail'] = det; sub = 2 if lod == 0 else 1
    # ding hull: rounded-square cauldron, rim flange on top, side lugs, a cloud band under the rim
    secs = [(-0.38, 0.8, .34, .1), (-0.34, 0.84, .42, .24), (-0.12, 0.86, .46, .33), (0.14, 0.87, .46, .33), (0.34, 0.86, .42, .26), (0.4, 0.84, .34, .12)]
    _, H = floft('hull', secs, 'apexBronze', 'hull', 'plain', n_exp=3.2, M=22, sub=sub)
    floft('rim', [(-0.38, 1.18, .42, .03), (0.0, 1.19, .47, .035), (0.4, 1.18, .42, .03)], 'apexBronze', 'hull', 'flange', n_exp=3.4, M=20)
    floft('band', [(-0.38, 1.07, .45, .045), (0.0, 1.07, .48, .05), (0.4, 1.07, .45, .045)], 'apexBronze', 'hull', 'clouds', n_exp=3.2, M=20)
    for s in (-1, 1):
        tube(f'lug{s}', (s * 0.44, 0.0, 0.98), (s * 0.55, 0.0, 1.0), 0.05, 0.045, 'apexBronze', 'hull', 'flange', sides=8)
        ring(f'lugr{s}', (s * 0.565, 0.0, 1.0), (1, 0, 0), 0.07, 0.03, 'apexInlay', 'hull', sides=10)
    for k, t in enumerate((20, 160) if lod < 2 else (20,)):
        strip(f'crack{k}', H, [(H.s_at_f(-0.25 + 0.5 * i / 4), t + (12 if i % 2 else -12)) for i in range(5)], STRIPE_W, 'apexCrack', 'hull')
    if lod < 2:
        strip('crackT', H, [(H.s_at_f(-0.3 + 0.6 * i / 4), 90) for i in range(5)], STRIPE_W, 'apexCrack', 'hull')
        q, n = H.point(H.s_at_f(-0.05), 0, 0.0)
        prism('hull_mark', rect(0.13, 0.13), tuple(q - n * 0.01), tuple(q + n * 0.02), 'apexBronze', 'hull', 'mark', up=(0, 0, 1))
    # neck and head: raised ox head with a flared bell mouth (the howl) and sharp back-swept horns
    tube('neck', (0, 0.34, 0.95), (0, 0.46, 1.2), 0.15, 0.13, 'apexBronze', 'head', 'flange', sides=12)
    _, HD = floft('head', [(0.38, 1.24, .17, .16), (0.52, 1.28, .19, .16), (0.62, 1.28, .16, .13)], 'apexBronze', 'head', 'plain', n_exp=2.4, M=16)
    floft('bell', [(0.6, 1.3, .13, .08), (0.72, 1.32, .18, .1), (0.82, 1.34, .24, .12)], 'apexBronze', 'head', 'flange', M=16, cap=False)
    floft('bellin', [(0.6, 1.32, .1, .05), (0.76, 1.33, .16, .08)], 'apexDark', 'head', M=12)  # recessed throat (round 1: a flat dark disc read as a pan)
    floft('jaw', [(0.58, 1.18, .11, .05), (0.72, 1.19, .15, .06), (0.82, 1.21, .21, .06)], 'apexBronze', 'jaw', 'lozenge', M=14, cap=True)
    for s in (-1, 1):
        spheroid(f'eye{s}', (s * 0.15, 0.57, 1.36), (0.04, 0.03, 0.03), 'apexInlay', 'head', segs=(8, 5))
        prism(f'horn{s}', blade(0.08, 0.07), (s * 0.13, 0.46, 1.38), (s * 0.4, 0.2, 1.6), 'apexInlay', 'head', scale_b=0.1, up=(0, 0, 1))
        prism(f'ear{s}', blade(0.09, 0.03), (s * 0.17, 0.42, 1.3), (s * 0.32, 0.34, 1.28), 'apexBronze', 'head', 'flange', scale_b=0.2)
        if det: prism(f'fang{s}', blade(0.04, 0.035), (s * 0.12, 0.8, 1.25), (s * 0.12, 0.83, 1.14), 'apexInlay', 'head', scale_b=0.1)
    # ox legs: upper and lower with a knee flange, short bogie with one big spoked chariot wheel
    for nm, sx, sf in (('FL', 1, 1), ('FR', -1, 1), ('BL', 1, -1), ('BR', -1, -1)):
        hip = (sx * 0.32, sf * 0.24, 0.8); knee = (sx * 0.36, sf * 0.27, 0.48); foot = (sx * 0.4, sf * 0.25, 0.24)
        tube(f'up{nm}', hip, knee, 0.12, 0.1, 'apexBronze', f'leg_{nm}', 'plain', sides=10)
        ring(f'knee{nm}', knee, (0, 0, 1), 0.12, 0.045, 'apexBronze', f'low_{nm}', sides=10)
        tube(f'lo{nm}', knee, foot, 0.095, 0.085, 'apexBronze', f'low_{nm}', 'flange', sides=10)
        ring(f'ank{nm}', foot, (0, 0, 1), 0.1, 0.04, 'apexBronze', f'bogie_{nm}', sides=10)
        bogie(f'bg{nm}', sx * 0.4, sf * 0.25, 0.13, 0.32, 0.1, 1, f'bogie_{nm}', [f'wheel_{nm}0'], det, spoked=True)
    tube('tail', (0, -0.42, 0.85), (0, -0.6, 0.65), 0.04, 0.025, 'apexBronze', 'tail', 'flange', sides=8)
    prism('tailtip', blade(0.08, 0.04), (0, -0.6, 0.65), (0, -0.66, 0.5), 'apexInlay', 'tail', scale_b=0.15)


def bones_howler():
    B = [('root', (0, 0, 0), (0, 0.3, 0), None), ('hull', (0, -0.3, 0.86), (0, 0.3, 0.86), 'root'), ('head', (0, 0.34, 0.95), (0, 0.82, 1.32), 'hull'),
         ('jaw', (0, 0.56, 1.2), (0, 0.82, 1.2), 'head'), ('tail', (0, -0.42, 0.85), (0, -0.66, 0.5), 'hull')]
    for nm, sx, sf in (('FL', 1, 1), ('FR', -1, 1), ('BL', 1, -1), ('BR', -1, -1)):
        B += [(f'leg_{nm}', (sx * 0.32, sf * 0.24, 0.8), (sx * 0.36, sf * 0.27, 0.48), 'hull'), (f'low_{nm}', (sx * 0.36, sf * 0.27, 0.48), (sx * 0.4, sf * 0.25, 0.24), f'leg_{nm}'),
              (f'bogie_{nm}', (sx * 0.4, sf * 0.25, 0.24), (sx * 0.4, sf * 0.25 + 0.15, 0.13), f'low_{nm}'), (f'wheel_{nm}0', (sx * 0.4, sf * 0.25, 0.13), (sx * 0.52, sf * 0.25, 0.13), f'bogie_{nm}')]
    return B


LEGS = ('FL', 'FR', 'BL', 'BR')


def make(name, builder, bones, attack):
    bpy.ops.wm.read_factory_settings(use_empty=True); bpy.context.scene.render.fps = K.FPS
    lods = []
    for lod in (2, 1, 0):
        builder(lod); body, _ = K.finish(f'{name}_lod{lod}', lod == 0); lods.insert(0, body)
    for i in (1, 2):
        if K.tris(lods[i]) > BUDGET[i] - 10: K.decimate(lods[i], (BUDGET[i] - 10) / K.tris(lods[i]))
    arm = K.make_rig(f'{name}_rig', bones)
    for b in lods: K.skin(b, arm)

    def ext():
        pts = K.world_pts([lods[0]]); xs = [p.x for p in pts]; fs = [p.y for p in pts]; zs = [p.z for p in pts]
        return dict(w=max(xs) - min(xs), l=max(fs) - min(fs), h=max(zs), zmin=min(zs))
    rest = ext()
    def jaw_ang():
        a = K.bone_pt(arm, 'jaw') - K.bone_pt(arm, 'jaw', False); h = K.bone_pt(arm, 'head') - K.bone_pt(arm, 'head', False)
        return math.degrees(math.atan2(h.z, h.y) - math.atan2(a.z, a.y))  # signed, in the side plane: + = jaw dropped
    j0 = jaw_ang(); tip0 = K.bone_pt(arm, 'head')
    wb = [b.name for b in arm.data.bones if b.name.startswith('wheel_')]
    K.clip(arm, 'idle', [(0, {}), (1.0, {'hull': {'loc': (0, 0, 0.015)}, 'head': {'p': 4, 'y': 8}, 'tail': {'y': 15}}), (2.0, {})])
    mv = []
    for k in range(5):
        u = k / 4; bob = 0.02 * math.sin(u * math.tau * 2)
        sp = {'hull': {'loc': (0, 0, bob)}}
        for i, lg in enumerate(LEGS):
            ph = 1 if lg in ('FL', 'BR') else -1
            sp['leg_' + lg] = {'p': 6 * ph * math.sin(u * math.tau)}; sp['bogie_' + lg] = {'p': 0}
        for w in wb: sp[w] = {'p': -360 * TURNS * u}
        mv.append((MOVE_S * u, sp))
    w_rest = arm.pose.bones[wb[0]].matrix.to_quaternion()
    meas = K.clip(arm, 'move', mv, linear=True, measure={0.25: lambda: arm.pose.bones[wb[0]].matrix.to_quaternion()})
    wind, strike = attack
    at = K.clip(arm, 'attack', [(0, {}), (WIND, wind), (WIND + STRIKE, strike), (WIND + STRIKE + BACK, {})],
                measure={WIND: lambda: ((K.bone_pt(arm, 'head') - tip0).length, jaw_ang() - j0)})[WIND]
    K.unmute_all(arm); bpy.context.scene.frame_set(1)
    G = K.Gates()
    for i, (ob, lim) in enumerate(zip(lods, BUDGET)): G(K.tris(ob) <= lim, f'{name} LOD{i} tris {K.tris(ob)} (budget {lim})')
    G(all(len(v.groups) == 1 and abs(v.groups[0].weight - 1) < 1e-6 for ob in lods for v in ob.data.vertices), f'{name} every vertex on one bone (3 skinned LODs, {len(arm.data.bones)} bones)')
    G(WIND >= TELL_MIN and at[0] >= TIP_MIN and at[1] >= JAW_MIN, f'{name} attack tell {WIND} s (min {TELL_MIN}): head tip moved {at[0]:.2f} m (min {TIP_MIN}), jaw {at[1]:.0f} deg (min {JAW_MIN})')
    turn = math.degrees(w_rest.rotation_difference(meas[0.25]).angle)
    G(len(wb) >= 4 and turn >= 60, f'{name} move: {len(wb)} wheel bones roll {360 * TURNS} deg per {MOVE_S} s (quarter clip turn {turn:.0f} deg)')
    G(rest['w'] <= 2 * CUB_R + 0.25 and rest['h'] < SUIT_H and abs(rest['zmin']) <= 0.03,
      f"{name} size {rest['w']:.2f} w x {rest['l']:.2f} l x {rest['h']:.2f} h m (width <= hit circle {2 * CUB_R} + 0.25; under the {SUIT_H} m suit), lowest {rest['zmin']:+.3f} m")
    mats = {m.name for m in lods[0].data.materials}
    G({'apexBronze', 'apexCrack', 'apexInlay'} <= mats, f'{name} shares the tiger casting language: materials {sorted(mats)} (bronze trim, crack inlay, gold inlay), mark and flanges')
    polys = lods[0].data.polygons; share = sum(p.area for p in polys if p.use_smooth) / sum(p.area for p in polys)
    G(share >= 0.5, f'{name} smooth-shaded share {share:.0%} of surface area (round forms, min 50%)')
    path = os.path.join(OUTDIR, f'{name}.glb'); K.export(path)
    anims, nodes, gm, _ = K.glb_info(path)
    G({'idle', 'move', 'attack'} <= set(anims), f'{name} GLB clips {sorted(anims)}')
    return G, rest


STALK_ATK = ({'hull': {'p': -4, 'loc': (0, -0.08, -0.05)}, 'head': {'p': -12}, 'jaw': {'p': -46}, 'leg_BL': {'p': 10}, 'leg_BR': {'p': 10}},
             {'hull': {'p': 3, 'loc': (0, 0.18, 0)}, 'head': {'p': 6}, 'jaw': {'p': -4}})
HOWL_ATK = ({'hull': {'p': 6}, 'head': {'p': 28}, 'jaw': {'p': -14}, 'leg_FL': {'p': 12}, 'leg_FR': {'p': 12}},
            {'hull': {'p': -4, 'loc': (0, 0.12, 0)}, 'head': {'p': -16}, 'jaw': {'p': -6}})
res = {}
Gs, rs = make('stalker', build_stalker, bones_stalker(), STALK_ATK)
Gh, rh = make('howler', build_howler, bones_howler(), HOWL_ATK)
G = K.Gates(); G.rows = Gs.rows + Gh.rows
G(rh['h'] / rs['h'] >= 1.4 and rs['l'] / rs['h'] >= 1.5 and rh['l'] / rh['h'] <= 1.0,
  f"distinct silhouettes: height Howler/Stalker {rh['h'] / rs['h']:.2f} (min 1.4); Stalker L/H {rs['l'] / rs['h']:.2f} (min 1.5); Howler L/H {rh['l'] / rh['h']:.2f} (max 1.0)")
G.summary('cubs'); G.dump(GJ, {'stalker': rs, 'howler': rh})
