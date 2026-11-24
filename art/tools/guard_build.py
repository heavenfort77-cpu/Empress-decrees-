# 皇家 guard units (worker W5; study art/Guard-Rebels-Study.md; docs/BURNING-PALACE.md "Cannon fodder"): Kaymuse's household guard,
# bronze soldiers on treads in the court's black and water-blue. One shared base (tread sled, lamellar torso, bronze mask) and data per type:
# 卒 zu (戟, line thrust 0.5 s), 弩手 nu (crossbow, volley 0.8 s), 盾 dun (notched shield, shove 0.5 s), 车 che (canopy chariot, charge 0.9 s),
# 伍长 wz (officer cap, signal banner, sword cut 0.5 s). Windups = CONFIG.GUARD.moves (index.html, read only).
# Materials: gdBronze (assets/tex/bronze_trim.png), gdLacquer (assets/tex/fodder_trim.png: lacquer lamellar, water-blue cord and cloth).
# Usage: BPY guard_build.py OUTDIR [TYPES]   (TYPES comma list, default all five) -> OUTDIR/<type>.glb and OUTDIR/guard_gates.json
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fodder_base as B
from fodder_base import loft, hloft, spheroid, prism, tube, path_tube, rect, ngon, blade, rot_for, addrot, clip, Q

ARGS = [a for a in sys.argv[sys.argv.index('--') + 1:]] if '--' in sys.argv else sys.argv[1:]
OUT = ARGS[0] if ARGS else '/tmp/guard'
TYPES = ARGS[1].split(',') if len(ARGS) > 1 else ['zu', 'nu', 'dun', 'che', 'wz']

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Attack windups, s (CONFIG.GUARD.moves windup per type's move: thrust, volley, shove, charge, cut).
WINDUP = {'zu': 0.5, 'nu': 0.8, 'dun': 0.5, 'che': 0.9, 'wz': 0.5}
# Strike and recover lengths after the windup, s.
STRIKE, RECOVER = 0.14, 0.45
# Unit radius from CONFIG.GUARD.types r, m (body half-width gate 0.7-1.4 x r).
RADIUS = {'zu': 0.45, 'nu': 0.45, 'dun': 0.6, 'che': 0.9, 'wz': 0.5}
# Scale of the officer (伍长 reads taller than his squad).
WZ_SCALE = 1.1
# Body height band without weapon or banner, m (study: fodder 1.5-1.85, shorter than the 2.05 m suits).
HEIGHT = (1.45, 1.9)
BR, LQ = 'gdBronze', 'gdLacquer'


# shared base -----------------------------------------------------------------------------------------------------------
def sled(d, w=0.3, tw=0.33):
    """tread sled: a rounded bronze hull like a ding belly, two tread pods (stamp-band plates), a flange rim and a waist collar."""
    hloft('hull', [(-0.44, 0.24, w * 0.8, 0.1, 0), (-0.32, 0.25, w, 0.14, 0), (0.28, 0.25, w, 0.14, 0), (0.44, 0.24, w * 0.75, 0.09, 0)], BR, 'hull', 'plain')
    for s in (-1, 1):
        hloft(f'tread_{s}', [(-0.5, 0.16, 0.09, 0.08, s * tw), (-0.44, 0.16, 0.1, 0.16, s * tw), (0.44, 0.16, 0.1, 0.16, s * tw), (0.5, 0.16, 0.09, 0.08, s * tw)],
              BR, 'hull', 'lozenge', n_exp=3.0, M=12)
        if d:  # hub bosses at both ends of each tread; cast cleats across the belt (the tread reads as linked plates, not a log)
            for f in (-0.36, 0.36):
                prism(f'hub_{s}{f}', ngon(0.07, 8), (s * (tw + 0.09), f, 0.16), (s * (tw + 0.12), f, 0.16), BR, 'hull', 'flange', scale_b=0.7)
            for k in range(7):
                f = -0.36 + k * 0.12
                prism(f'cleat_{s}{k}', [(-0.025, 0), (0.025, 0), (0.012, 0.022), (-0.012, 0.022)], (s * (tw - 0.095), f, 0.315), (s * (tw + 0.095), f, 0.315), BR, 'hull', 'flange', up=(0, 0, 1))
    loft('rim', [(0.33, 0, w + 0.06, 0.44, 0), (0.38, 0, w + 0.05, 0.43, 0)], BR, 'hull', 'flange', n_exp=2.6)
    # a cast mask plate on the hull front (a ding's face): marks the front at any angle
    prism('hmask', [(-0.16, -0.08), (0.16, -0.08), (0.2, 0.05), (0.08, 0.09), (0, 0.05), (-0.08, 0.09), (-0.2, 0.05)], (0, 0.4, 0.24), (0, 0.46, 0.24), BR, 'hull', 'mask', scale_b=0.92)

def torso(d, cw=0.21, skirt=0.29):
    """round 2 (concepts 5103 / 5115, reference only): a long lamellar coat that flares like a bell over the sled, so the figure reads as one
    cast statue riding its treads; Qin-black lacquer plates, water-blue cord at the hem and collar, two tiers of shoulder plates, bronze neck."""
    bw = skirt + 0.09
    loft('coat', [(0.38, 0, bw, bw * 0.9, 0), (0.5, 0, bw - 0.02, bw * 0.88, 0), (0.66, 0.0, skirt, skirt * 0.8, 0), (0.82, 0.01, cw + 0.01, cw * 0.74, 0)],
         LQ, 'torso', 'lacquer', n_exp=2.1, M=18)
    loft('chest', [(0.8, 0.01, cw, cw * 0.72, 0), (1.0, 0.02, cw + 0.02, cw * 0.8, 0), (1.18, 0.01, cw + 0.03, cw * 0.76, 0), (1.27, 0, cw * 0.7, cw * 0.55, 0)],
         LQ, 'torso', 'lacquer', n_exp=2.4)
    loft('hem', [(0.37, 0, bw + 0.012, bw * 0.9 + 0.012, 0), (0.42, 0, bw + 0.006, bw * 0.9 + 0.006, 0)], LQ, 'torso', 'cord', n_exp=2.1, M=18, cap=False)
    loft('belt', [(0.8, 0.01, cw + 0.025, cw * 0.74 + 0.025, 0), (0.86, 0.01, cw + 0.025, cw * 0.76 + 0.025, 0)], LQ, 'torso', 'cord', cap=False)
    if d:
        loft('collar', [(1.22, 0, cw * 0.82, cw * 0.62, 0), (1.29, 0, cw * 0.62, cw * 0.5, 0)], LQ, 'torso', 'cord', cap=False)
        # chest plate: a bronze cast front plate with a workshop mark (segmented casting, research rule)
        prism('chestplate', [(-0.12, -0.1), (0.12, -0.1), (0.14, 0.08), (0, 0.13), (-0.14, 0.08)], (0, cw * 0.78 - 0.01, 1.03), (0, cw * 0.78 + 0.03, 1.04), BR, 'torso', 'mark')
        # a front apron of larger plates down the coat (5115): a bronze-edged centre panel
        prism('apron', [(-0.09, 0), (0.09, 0), (0.12, -0.34), (-0.12, -0.34)], (0, skirt * 0.8 - 0.005, 0.8), (0, skirt * 0.8 + 0.03, 0.8), BR, 'torso', 'clouds')
    for s in (-1, 1):
        b = f'uarm_{"R" if s > 0 else "L"}'
        loft(f'pauldron_{s}', [(0.98, 0, 0.13, 0.14, s * 0.31), (1.1, 0, 0.14, 0.15, s * 0.3), (1.22, 0, 0.12, 0.13, s * 0.27), (1.28, 0, 0.05, 0.06, s * 0.23)],
             LQ, b, 'lacquer', n_exp=2.0, M=12)
        loft(f'pauld2_{s}', [(1.12, 0, 0.1, 0.11, s * 0.29), (1.2, 0, 0.105, 0.115, s * 0.28), (1.3, 0, 0.04, 0.05, s * 0.24)], LQ, b, 'blue', n_exp=2.0, M=10)
        if d:  # a cord edge where the plate skirt ends
            loft(f'pcord_{s}', [(0.96, 0, 0.135, 0.145, s * 0.31), (0.99, 0, 0.135, 0.145, s * 0.31)], LQ, b, 'cord', n_exp=2.0, M=12, cap=False)
    tube('neck', (0, 0, 1.25), (0, 0, 1.34), 0.065, 0.06, BR, 'head', 'plain')

def head(d, cap='knot'):
    """smooth cast bronze face mask (a calm Qin face, no features but brow, eye slits and nose ridge); a side topknot or the officer cap."""
    spheroid('mask', (0, 0.01, 1.44), (0.11, 0.12, 0.14), BR, 'head', 'plain', segs=(12, 9))
    prism('brow', [(-0.09, -0.012), (0.09, -0.012), (0.08, 0.012), (-0.08, 0.012)], (0, 0.09, 1.46), (0, 0.115, 1.455), BR, 'head', 'flange')
    if d:
        for s in (-1, 1):
            prism(f'eye_{s}', blade(0.05, 0.012), (s * 0.042, 0.095, 1.435), (s * 0.042, 0.112, 1.435), BR, 'head', 'inlay')
        prism('nose', [(-0.015, 0), (0.015, 0), (0, 0.03)], (0, 0.105, 1.44), (0, 0.12, 1.4), BR, 'head', 'flange', scale_b=0.8)
    if cap == 'knot':  # Qin foot soldiers' topknot on the right of the crown, bound with a cord
        spheroid('cap', (0, -0.005, 1.5), (0.095, 0.1, 0.06), LQ, 'head', 'lacquer', segs=(10, 6))
        spheroid('knot', (0.05, -0.02, 1.58), (0.045, 0.045, 0.05), BR, 'head', 'plain', segs=(8, 6))
    else:  # officer: the double-tail cap (鹖冠 type, our own shape): a flat crown board and two tails sweeping up at the back
        spheroid('cap', (0, -0.005, 1.5), (0.1, 0.105, 0.06), LQ, 'head', 'lacquer', segs=(10, 6))
        prism('board', rect(0.16, 0.03), (0, 0.06, 1.55), (0, -0.1, 1.6), LQ, 'head', 'blue')
        for s in (-1, 1):
            prism(f'tail_{s}', blade(0.07, 0.03), (s * 0.04, -0.08, 1.58), (s * 0.07, -0.3, 1.68), LQ, 'head', 'lacquer', scale_b=0.35)

def arms(d, r_fore=(0.3, 0.27, 0.86), l_fore=(-0.28, 0.24, 0.9)):
    """lacquer sleeves, bronze bracers and fists; forearm ends where the hands hold the weapon."""
    for side, s, fe in (('R', 1, r_fore), ('L', -1, l_fore)):
        el = (s * 0.31, 0.03, 0.96)
        tube(f'uarm_{side}', (s * 0.27, 0, 1.17), el, 0.075, 0.1, LQ, f'uarm_{side}', 'lacquer')  # the sleeve flares to the elbow (5115)
        tube(f'farm_{side}', el, fe, 0.065, 0.055, BR, f'farm_{side}', 'clouds')
        spheroid(f'fist_{side}', fe, (0.065, 0.07, 0.065), BR, f'farm_{side}', 'plain', segs=(8, 6))

def guard_bones(r_fore=(0.3, 0.27, 0.86), l_fore=(-0.28, 0.24, 0.9), wtip=None, extra=(), dz=0.0):
    b = [('root', (0, 0, 0), (0, 0, 0.2), None), ('hull', (0, -0.3, 0.28), (0, 0.4, 0.28), 'root'), ('torso', (0, 0, 0.5), (0, 0, 1.3), 'hull'),
         ('head', (0, 0, 1.3), (0, 0, 1.6), 'torso')]
    for side, s, fe in (('R', 1, r_fore), ('L', -1, l_fore)):
        b += [(f'uarm_{side}', (s * 0.27, 0, 1.17), (s * 0.31, 0.03, 0.96), 'torso'), (f'farm_{side}', (s * 0.31, 0.03, 0.96), fe, f'uarm_{side}')]
    if wtip: b.append(('weapon', r_fore, wtip, 'farm_R'))
    b = b + list(extra)
    return [x if x[0] in ('root', 'hull') else tuple(x) + (dz,) for x in b]  # dz: torso set lower into the hull (弩手)

def base(d, **k):
    sled(d, k.get('w', 0.3), k.get('tw', 0.33)); Q['zoff'] = k.get('dz', 0.0); torso(d, k.get('cw', 0.21), k.get('skirt', 0.29)); head(d, k.get('cap', 'knot'))
    arms(d, k.get('r_fore', (0.3, 0.27, 0.86)), k.get('l_fore', (-0.28, 0.24, 0.9)))


# shared clips ----------------------------------------------------------------------------------------------------------
def idle_move(arm, extra_idle=None):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p)
    tw = lambda a: R('torso', 'fwd', a, (0.3, 0, 1.2))  # twist: right shoulder forward
    idle = {'torso': [(0, (0, 0, 0)), (1.0, tw(4)), (2.0, (0, 0, 0))], 'head': [(0, (0, 0, 0)), (0.7, R('head', 'right', 10, (0, 0.2, 1.45))), (1.4, R('head', 'left', 6, (0, 0.2, 1.45))), (2.0, (0, 0, 0))]}
    if extra_idle: idle.update(extra_idle)
    move = {'torso': [(0, R('torso', 'fwd', 7)), (0.5, R('torso', 'fwd', 5)), (1.0, R('torso', 'fwd', 7))],
            'hull': [(0, (0, 0, 0)), (0.25, R('hull', 'up', 2)), (0.5, (0, 0, 0)), (0.75, R('hull', 'down', 2)), (1.0, (0, 0, 0))]}
    mloc = {'hull': [(0, (0, 0, 0)), (0.25, (0, 0, 0.015)), (0.5, (0, 0, 0)), (0.75, (0, 0, 0.015)), (1.0, (0, 0, 0))]}
    return clip(arm, 'idle', idle), clip(arm, 'move', move, loc=mloc)

def acts(arm, attack_keys, w, loc=None, scl=None, extra_idle=None):
    i, m = idle_move(arm, extra_idle)
    a = clip(arm, 'attack', attack_keys, loc=loc, scl=scl)
    return {'idle': i, 'move': m, 'attack': a}


# 卒 foot soldier: 戟 (halberd: spear point plus a side 戈 blade), held diagonal forward; thrust -------------------------------------------
# Weapons stand upright or lean outward at rest: the camera looks down 40 deg at units facing the player, so a forward lean foreshortens into the body.
ZU_TIP = (0.48, 0.3, 2.36)  # the 戟 is a long pole arm (terracotta ones about 2.8 m): the 卒's mark is the tall pike
def ji(d, grip, tip):
    gx, gf, gz = grip; tx, tf, tz = tip; L = math.dist(grip, tip)
    u = [(t - g) / L for g, t in zip(grip, tip)]
    butt = tuple(g - c * 0.55 for g, c in zip(grip, u)); neck = tuple(t - c * 0.26 for t, c in zip(tip, u))
    tube('shaft', butt, neck, 0.04, 0.036, LQ, 'weapon', 'lacquer', sides=6)
    prism('point', blade(0.16, 0.035), neck, tip, BR, 'weapon', 'flange', scale_b=0.05)
    side = tuple(n + c * 0.06 for n, c in zip(neck, u))
    prism('ge', blade(0.1, 0.025), side, (side[0] + 0.05, side[1] - 0.3, side[2] - 0.05), BR, 'weapon', 'flange', scale_b=0.15)  # the 戈 blade, backward hook
    if d:
        tube('ferrule', butt, tuple(b + c * 0.06 for b, c in zip(butt, u)), 0.028, 0.026, BR, 'weapon', 'plain', sides=6)
        prism('tassel', blade(0.08, 0.04), tuple(n - c * 0.02 for n, c in zip(neck, u)), tuple(n - c * 0.14 for n, c in zip(neck, u)), LQ, 'weapon', 'blue', scale_b=0.4)

def zu_build(d):
    base(d); ji(d, (0.3, 0.27, 0.86), ZU_TIP)

def zu_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['zu']
    lvl = R('weapon', 'fwd', 62)  # spear comes down to about level, pointing at the target
    back = R('uarm_R', 'back', 40); fb = R('farm_R', 'back', 25)
    keys = {'weapon': [(0, (0, 0, 0)), (w, lvl), (w + STRIKE, lvl), (w + STRIKE + RECOVER, (0, 0, 0))],
            'uarm_R': [(0, (0, 0, 0)), (w, back), (w + STRIKE, R('uarm_R', 'fwd', 35)), (w + STRIKE + RECOVER, (0, 0, 0))],
            'farm_R': [(0, (0, 0, 0)), (w, fb), (w + STRIKE, R('farm_R', 'fwd', 20)), (w + STRIKE + RECOVER, (0, 0, 0))],
            'torso': [(0, (0, 0, 0)), (w, R('torso', 'back', 14, (0.3, 0, 1.2))), (w + STRIKE, R('torso', 'fwd', 12, (0.3, 0, 1.2))), (w + STRIKE + RECOVER, (0, 0, 0))]}
    loc = {'hull': [(0, (0, 0, 0)), (w, (0, -0.08, 0)), (w + STRIKE, (0, 0.25, 0)), (w + STRIKE + RECOVER, (0, 0, 0))]}
    return acts(arm, keys, w, loc), None, w, 'weapon'


# 弩手 crossbowman: crossbow level at the chest (wide horizontal), bolt case on the back; volley raises the bow ------------------------------
NU_R, NU_L = (0.12, 0.34, 0.95), (-0.1, 0.42, 0.98)
NU_TIP = (0.0, 0.75, 0.98)
NU_DZ = -0.12
def nu_build(d):
    base(d, r_fore=NU_R, l_fore=NU_L, dz=NU_DZ)
    # stock from the right fist forward, prod (bow) across, string; bronze trigger box (batch-cast Qin trigger)
    prism('stock', rect(0.05, 0.06), (0.04, 0.1, 0.97), NU_TIP, LQ, 'weapon', 'lacquer')
    arc = [(math.sin(a) * 0.56, 0.68 - (1 - math.cos(a)) * 0.3, 0.98) for a in [math.radians(x) for x in range(-70, 71, 20 if d else 35)]]
    path_tube('prod', arc, 0.035, BR, 'weapon', 'flange', sides=6)  # the prod spans 1.05 m, wider than the hull: the 弩手 reads wide and low
    if d:
        prism('trigger', rect(0.06, 0.08), (0.04, 0.3, 0.94), (0.04, 0.4, 0.94), BR, 'weapon', 'mark')
        tube('string_l', arc[0], (0.0, 0.42, 0.98), 0.006, 0.006, LQ, 'weapon', 'cord', sides=4)
        tube('string_r', arc[-1], (0.0, 0.42, 0.98), 0.006, 0.006, LQ, 'weapon', 'cord', sides=4)
    # bolt case on the back: a tall rounded lacquer box with a cord strap and bolt fletchings at the top
    # tall bolt case slung on the back, tilted out over the left shoulder: its fan of fletchings is the 弩手's mark above the head line
    # bolt case slung low on the back (below the head line, so the 卒's pike stays the only spike in the squad)
    loft('case', [(0.62, -0.26, 0.1, 0.07, -0.02), (1.1, -0.3, 0.11, 0.075, -0.1), (1.32, -0.31, 0.1, 0.07, -0.13), (1.36, -0.31, 0.08, 0.06, -0.14)], LQ, 'torso', 'lacquer', n_exp=3.0, M=10)
    loft('caseband', [(1.0, -0.29, 0.115, 0.08, -0.08), (1.06, -0.3, 0.115, 0.08, -0.09)], LQ, 'torso', 'cord', n_exp=3.0, M=10, cap=False)
    for k in range(4 if d else 2):
        a = -0.5 + k * (1.0 / (3 if d else 1))
        prism(f'fletch_{k}', blade(0.06, 0.02), (-0.14 + a * 0.06, -0.31, 1.34), (-0.14 + a * 0.12, -0.31, 1.46), LQ, 'torso', 'blue', scale_b=0.35)

def nu_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['nu']
    up = R('weapon', 'up', 30); s = w + STRIKE
    keys = {'torso': [(0, (0, 0, 0)), (w, R('torso', 'back', 12)), (s, R('torso', 'back', 15)), (s + RECOVER, (0, 0, 0))],
            'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 30)), (s, R('uarm_R', 'up', 24)), (s + RECOVER, (0, 0, 0))],
            'uarm_L': [(0, (0, 0, 0)), (w, R('uarm_L', 'up', 30)), (s, R('uarm_L', 'up', 24)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, up), (s, R('weapon', 'up', 40)), (s + RECOVER, (0, 0, 0))]}
    return acts(arm, keys, w), None, w, 'weapon'


# 盾 shieldbearer: wider sled and torso, a tall notched-top shield in front on the left arm; shove -----------------------------------------
DUN_L = (-0.12, 0.36, 0.95)
DUN_TIP = (-0.05, 0.42, 1.62)
def dun_build(d):
    base(d, w=0.38, tw=0.43, cw=0.25, skirt=0.33, l_fore=DUN_L, r_fore=(0.24, 0.32, 0.9))
    # shield: Qin type with a notched top (two shoulders, a raised centre), bronze rim, lacquer face with a cloud band
    prof = [(-0.3, -0.62), (0, -0.66), (0.3, -0.62), (0.38, -0.5), (0.4, 0.3), (0.34, 0.44), (0.2, 0.5), (0.1, 0.46), (0, 0.66), (-0.1, 0.46), (-0.2, 0.5), (-0.34, 0.44), (-0.4, 0.3), (-0.38, -0.5)]
    prism('shield', prof, (-0.04, 0.42, 1.0), (-0.04, 0.47, 1.0), LQ, 'weapon', 'lacquer')
    for sx in (-1, 1):  # side panels angled back: a curved shield, not a flat slab
        prism(f'wing_{sx}', [(-0.05, -0.6), (0.05, -0.6), (0.05, 0.3), (-0.05, 0.3)], (-0.04 + sx * 0.42, 0.42, 1.0), (-0.04 + sx * 0.47, 0.32, 1.0), BR, 'weapon', 'flange', up=(0, 0, 1))
    if d:
        prism('boss', ngon(0.1, 10), (-0.04, 0.46, 1.02), (-0.04, 0.5, 1.02), BR, 'weapon', 'mask', scale_b=0.6)
        for z in (0.5, 1.3):
            prism(f'band_{z}', rect(0.78, 0.07), (-0.04, 0.455, z), (-0.04, 0.475, z), BR, 'weapon', 'clouds')

def dun_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['dun']; s = w + STRIKE
    keys = {'torso': [(0, (0, 0, 0)), (w, R('torso', 'back', 14)), (s, R('torso', 'fwd', 14)), (s + RECOVER, (0, 0, 0))],
            'uarm_L': [(0, (0, 0, 0)), (w, R('uarm_L', 'back', 25)), (s, R('uarm_L', 'fwd', 25)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, R('weapon', 'back', 25)), (s, R('weapon', 'fwd', 12)), (s + RECOVER, (0, 0, 0))]}
    loc = {'hull': [(0, (0, 0, 0)), (w, (0, -0.15, 0)), (s, (0, 0.35, 0)), (s + RECOVER, (0, 0, 0))]}
    return acts(arm, keys, w, loc), None, w, 'weapon'


# 车 chariot: long low hull on four treads, a round water-blue canopy on a pole, a bronze driver, a ram pole with a beast-head finial ------
CHE_TIP = (0, 1.42, 0.62)
def che_build(d):
    hloft('hull', [(-0.95, 0.42, 0.5, 0.14, 0), (-0.85, 0.44, 0.6, 0.22, 0), (0.7, 0.44, 0.6, 0.22, 0), (0.95, 0.42, 0.45, 0.14, 0)], BR, 'hull', 'plain', M=16)
    for s in (-1, 1):
        for f0 in (-0.5, 0.5):
            hloft(f'tread_{s}{f0}', [(f0 - 0.48, 0.18, 0.1, 0.08, s * 0.62), (f0 - 0.42, 0.18, 0.11, 0.18, s * 0.62), (f0 + 0.42, 0.18, 0.11, 0.18, s * 0.62),
                                     (f0 + 0.48, 0.18, 0.1, 0.08, s * 0.62)], BR, 'hull', 'lozenge', n_exp=3.0, M=12)
        # side rails: bronze lattice boards with a cloud band
        prism(f'rail_{s}', [(-0.02, 0), (0.02, 0), (0.02, 0.32), (-0.02, 0.32)], (s * 0.56, -0.85, 0.62), (s * 0.56, 0.6, 0.62), BR, 'hull', 'clouds', up=(0, 0, 1))
    prism('front', [(-0.5, 0), (0.5, 0), (0.42, 0.36), (-0.42, 0.36)], (0, 0.6, 0.62), (0, 0.66, 0.62), BR, 'hull', 'mask')
    # canopy: a pole and a round shallow dome (the bronze chariot's parasol), water-blue lacquer with a bronze rim
    tube('pole', (0, -0.25, 0.62), (0, -0.25, 1.95), 0.03, 0.025, BR, 'canopy', 'plain', sides=6)
    loft('canopy', [(1.86, -0.25, 0.78, 0.78, 0), (1.95, -0.25, 0.62, 0.62, 0), (2.02, -0.25, 0.3, 0.3, 0), (2.04, -0.25, 0.06, 0.06, 0)], LQ, 'canopy', 'blue', n_exp=2.0, M=18)
    if d:
        loft('crim', [(1.84, -0.25, 0.8, 0.8, 0), (1.88, -0.25, 0.79, 0.79, 0)], BR, 'canopy', 'flange', n_exp=2.0, M=18, cap=False)
    # driver: a kneeling bronze figure, mask and lamellar back, reins to the ram
    loft('dbody', [(0.62, 0.2, 0.18, 0.13, 0), (0.95, 0.22, 0.17, 0.12, 0), (1.06, 0.22, 0.1, 0.08, 0)], LQ, 'driver', 'lacquer')
    spheroid('dhead', (0, 0.24, 1.16), (0.09, 0.1, 0.11), BR, 'driver', 'plain', segs=(10, 7))
    spheroid('dcap', (0, 0.23, 1.22), (0.085, 0.09, 0.05), LQ, 'driver', 'lacquer', segs=(8, 5))
    for s in (-1, 1):
        tube(f'darm_{s}', (s * 0.15, 0.22, 0.98), (s * 0.1, 0.48, 0.86), 0.04, 0.035, BR, 'driver', 'clouds', sides=6)
    # ram pole (辀 curving forward) with a bronze beast-head finial: the charge leads with it
    tube('ram', (0, 0.66, 0.6), (0, 1.25, 0.62), 0.06, 0.05, BR, 'ram', 'flange', sides=8)
    spheroid('rhead', (0, 1.3, 0.64), (0.1, 0.14, 0.1), BR, 'ram', 'mask', segs=(10, 7))
    prism('rhorn', blade(0.08, 0.03), (0, 1.36, 0.7), CHE_TIP, BR, 'ram', 'flange', scale_b=0.1)
    if d:
        for s in (-1, 1):
            prism(f'rear_{s}', blade(0.05, 0.02), (s * 0.06, 1.24, 0.72), (s * 0.12, 1.18, 0.84), BR, 'ram', 'flange', scale_b=0.1)

def che_bones():
    return [('root', (0, 0, 0), (0, 0, 0.2), None), ('hull', (0, -0.6, 0.42), (0, 0.6, 0.42), 'root'), ('canopy', (0, -0.25, 0.62), (0, -0.25, 1.95), 'hull'),
            ('driver', (0, 0.22, 0.62), (0, 0.22, 1.2), 'hull'), ('ram', (0, 0.66, 0.6), CHE_TIP, 'hull')]

def che_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['che']; s = w + 0.3
    idle = {'canopy': [(0, (0, 0, 0)), (1.0, R('canopy', 'right', 2)), (2.0, (0, 0, 0))], 'driver': [(0, (0, 0, 0)), (1.0, R('driver', 'fwd', 3)), (2.0, (0, 0, 0))]}
    move = {'hull': [(0, (0, 0, 0)), (0.25, R('hull', 'up', 1.5)), (0.5, (0, 0, 0)), (0.75, R('hull', 'down', 1.5)), (1.0, (0, 0, 0))],
            'canopy': [(0, R('canopy', 'back', 3)), (0.5, R('canopy', 'back', 5)), (1.0, R('canopy', 'back', 3))]}
    mloc = {'hull': [(0, (0, 0, 0)), (0.25, (0, 0, 0.012)), (0.5, (0, 0, 0)), (0.75, (0, 0, 0.012)), (1.0, (0, 0, 0))]}
    att = {'hull': [(0, (0, 0, 0)), (w, R('hull', 'up', 10)), (s, R('hull', 'down', 3)), (s + RECOVER, (0, 0, 0))],
           'driver': [(0, (0, 0, 0)), (w, R('driver', 'back', 12)), (s, R('driver', 'fwd', 15)), (s + RECOVER, (0, 0, 0))],
           'canopy': [(0, (0, 0, 0)), (w, R('canopy', 'fwd', 6)), (s, R('canopy', 'back', 10)), (s + RECOVER, (0, 0, 0))],
           'ram': [(0, (0, 0, 0)), (w, R('ram', 'up', 12)), (s, R('ram', 'down', 4)), (s + RECOVER, (0, 0, 0))]}
    aloc = {'hull': [(0, (0, 0, 0)), (w, (0, -0.35, 0)), (s, (0, 0.8, 0)), (s + RECOVER, (0, 0, 0))]}
    return {'idle': clip(arm, 'idle', idle), 'move': clip(arm, 'move', move, loc=mloc), 'attack': clip(arm, 'attack', att, loc=aloc)}, None, w, 'ram'


# 伍长 squad leader: 1.1 x base, officer cap, tall signal banner on the back pole (water-blue), long bronze sword; cut -------------------------
WZ_TIP = (0.36, 0.36, 1.66)
def wz_build(d):
    base(d, cap='officer')
    tube('blade', (0.3, 0.32, 0.88), WZ_TIP, 0.02, 0.008, BR, 'weapon', 'flange', sides=4)
    prism('guard', rect(0.12, 0.03), (0.3, 0.27, 0.87), (0.3, 0.31, 0.875), BR, 'weapon', 'plain')
    if d:
        spheroid('pommel', (0.3, 0.17, 0.85), (0.03, 0.03, 0.03), BR, 'weapon', 'plain', segs=(6, 4))
    # banner pole from the back plate, crossbar at the top, a long water-blue banner with a bronze finial (a sigil band, no script)
    tube('bpole', (-0.12, -0.2, 0.85), (-0.12, -0.2, 2.5), 0.03, 0.025, LQ, 'banner', 'lacquer', sides=6)
    prism('bar', rect(0.045, 0.045), (-0.12, -0.2, 2.43), (-0.56, -0.2, 2.43), LQ, 'banner', 'lacquer')
    prism('flag', rect(0.42, 0.02), (-0.34, -0.2, 2.41), (-0.34, -0.2, 1.6), LQ, 'banner', 'blue', up=(0, -1, 0))
    prism('finial', blade(0.08, 0.04), (-0.12, -0.2, 2.5), (-0.12, -0.2, 2.66), BR, 'banner', 'flange', scale_b=0.1)
    if d:
        for z in (2.15, 1.85):
            prism(f'fband_{z}', rect(0.43, 0.03), (-0.34, -0.2, z), (-0.34, -0.2, z - 0.06), BR, 'banner', 'mark', up=(0, -1, 0))

def wz_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['wz']; s = w + STRIKE
    sway = {'banner': [(0, (0, 0, 0)), (1.0, R('banner', 'left', 4)), (2.0, (0, 0, 0))]}
    keys = {'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 100)), (s, R('uarm_R', 'fwd', 30)), (s + RECOVER, (0, 0, 0))],
            'farm_R': [(0, (0, 0, 0)), (w, R('farm_R', 'up', 30)), (s, (0, 0, 0)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, R('weapon', 'back', 50)), (s, R('weapon', 'fwd', 90)), (s + RECOVER, (0, 0, 0))],
            'torso': [(0, (0, 0, 0)), (w, R('torso', 'back', 10)), (s, R('torso', 'fwd', 12)), (s + RECOVER, (0, 0, 0))]}
    return acts(arm, keys, w, extra_idle=sway), None, w, 'weapon'


UNITS = {
    'zu': (zu_build, lambda: guard_bones(wtip=ZU_TIP), zu_clips, 1.0),
    'nu': (nu_build, lambda: guard_bones(NU_R, NU_L, wtip=NU_TIP, dz=NU_DZ), nu_clips, 1.0),
    'dun': (dun_build, lambda: guard_bones((0.24, 0.32, 0.9), DUN_L, extra=[('weapon', DUN_L, DUN_TIP, 'farm_L')]), dun_clips, 1.0),
    'che': (che_build, che_bones, che_clips, 1.0),
    'wz': (wz_build, lambda: guard_bones(wtip=WZ_TIP, extra=[('banner', (-0.12, -0.2, 0.85), (-0.12, -0.2, 2.5), 'torso')]), wz_clips, WZ_SCALE),
}

def extra(key):
    def g(G, lod0, arm, info):
        ex = ('ram',) if key == 'che' else ('weapon', 'banner')
        x0, x1, y0, y1, z0, z1 = B.bounds(lod0, ex)
        hw = max(-x0, x1); r = RADIUS[key]
        G(0.7 * r <= hw <= 1.4 * r, f'body half-width {hw:.2f} m (0.7-1.4 x radius {r})')
        if key != 'che':
            G(HEIGHT[0] <= z1 <= HEIGHT[1] * (WZ_SCALE if key == 'wz' else 1), f'body height {z1:.2f} m (band {HEIGHT[0]}-{HEIGHT[1] * (WZ_SCALE if key == "wz" else 1):.2f})')
        else:
            G(y1 - y0 >= 1.9 and z1 <= 2.2, f'chariot body length {y1 - y0:.2f} m (>= 1.9), top {z1:.2f} m (<= 2.2)')
        X0, X1, Y0, Y1, Z0, Z1 = B.bounds(lod0)
        info.update(top=Z1, body_top=z1, half_width=hw, length=Y1 - Y0)
    return g

if __name__ == '__main__':
    res = {}
    for k in TYPES:
        build, bones, clips_fn, sc = UNITS[k]
        Q['scale'] = sc
        res[k] = B.build_unit(k, build, bones(), clips_fn, os.path.join(OUT, f'{k}.glb'), extra(k))
        Q['scale'] = 1.0
    if 'wz' in res:
        others = [res[k]['top'] for k in res if k != 'wz']
        if others:
            ok = res['wz']['top'] >= 1.15 * max(others)
            line = f'leader banner top {res["wz"]["top"]:.2f} m >= 1.15 x tallest squad member {max(others):.2f} m'
            print(('PASS ' if ok else 'FAIL ') + 'wz ' + line); res['wz']['gates'].append((ok, line)); res['wz']['passed'] += ok; res['wz']['checks'] += 1
    json.dump(res, open(os.path.join(OUT, 'guard_gates.json'), 'w'), indent=1, ensure_ascii=False)
    for k, v in res.items(): print(f'SUMMARY {k} {v["passed"]} of {v["checks"]} tris {v["tris"]} top {v["top"]:.2f}')
