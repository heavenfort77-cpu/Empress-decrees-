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
# Round 4 proportions: everything above the pivot (the coat base) is stretched by ZK (taller torso and coat, head kept small): body top
# about 1.8 m, about 7 heads (round 3: 1.63 m, about 5).
ZK = 1.17
ZPIV = 0.38
# Shoulder and elbow joints (x, f, z design, before the stretch); round 3 had x 0.27 / 0.31 (broad, toy-like).
SHOULDER = (0.24, 0, 1.17)
ELBOW = (0.27, 0.04, 0.95)
# Track unit: centre offset tw, link width lw (m); end wheel radius, half wheelbase, link thickness are track() defaults.
TRACK = {'tw': 0.3, 'lw': 0.15}
# Mask half-height (chin to crown centre), m; proportion gate: body at least this many heads tall incl. cap (soldier read, not a toy).
MASK_RZ = 0.12
HEADS_MIN = 6.0
BR, LQ = 'gdBronze', 'gdLacquer'
Q['zpiv'] = ZPIV


# shared base -----------------------------------------------------------------------------------------------------------
# Round 4 (lead review 25 Nov: treads read as log rafts): each side is a cast-bronze track unit in the chariot running-gear language:
# a loop of separate cast links (gaps between them), spoked end wheels with a bronze rim and a dark lacquer web, axle-end caps (軎) standing
# out of the hubs, small road wheels, and a fender plate with a down-turned flange over the top run.
def track(d, s, tw, hl=0.32, R=0.12, lw=0.15, lt=0.04, fc=0.0, n=None, spokes=4, cap=0.07, pitch=0.12):
    """one track unit on side s, centred at x = s * tw, f = fc; end wheels of radius R at f = fc +- hl; link loop lt thick, lw wide."""
    x0 = s * tw; zc = R + lt; Rp = R + lt / 2; arc = math.pi * Rp; tot = 4 * hl + 2 * arc
    n = n or (int(round(tot / pitch)) if d else int(round(tot / (pitch * 2.2))))  # link pitch; LOD1/2 links twice as long
    def at(u):  # point, tangent and outward normal along the loop (bottom run forward, front arc up, top run back, rear arc down)
        u %= tot
        if u < 2 * hl: return (fc - hl + u, zc - Rp), (1, 0), (0, -1)
        u -= 2 * hl
        if u < arc: a = -math.pi / 2 + u / Rp; return (fc + hl + Rp * math.cos(a), zc + Rp * math.sin(a)), (-math.sin(a), math.cos(a)), (math.cos(a), math.sin(a))
        u -= arc
        if u < 2 * hl: return (fc + hl - u, zc + Rp), (-1, 0), (0, 1)
        u -= 2 * hl; a = math.pi / 2 + u / Rp
        return (fc - hl + Rp * math.cos(a), zc + Rp * math.sin(a)), (-math.sin(a), math.cos(a)), (math.cos(a), math.sin(a))
    L = tot / n * 0.74
    for i in range(n):
        (f, z), (tf, tz), (nf, nz) = at((i + 0.5) * tot / n)
        prism(f'link_{s}{i}', rect(lw, lt), (x0, f - tf * L / 2, z - tz * L / 2), (x0, f + tf * L / 2, z + tz * L / 2), BR, 'hull', 'flange', rnd=True, up=tuple(B.Pd(0, nf, nz)))
    m = 12 if d else 7; xo = x0 + s * (lw / 2 - 0.012)
    for f in (fc - hl, fc + hl):  # end wheels: bronze rim disc, dark web, bronze spokes and hub, axle-end cap
        prism(f'wheel_{s}{f}', ngon(R - 0.012, m), (x0 - s * (lw / 2 - 0.02), f, zc), (xo, f, zc), BR, 'hull', 'plain', rnd=True, up=(0, 0, 1))
        if d: prism(f'web_{s}{f}', ngon(R - 0.034, m), (xo, f, zc), (xo + s * 0.008, f, zc), LQ, 'hull', 'dark', rnd=True, up=(0, 0, 1))
        if d:
            for k in range(spokes):
                a = k * math.pi / spokes * 2 + math.pi / 4
                c, sn = math.cos(a), math.sin(a)
                prism(f'spoke_{s}{f}{k}', rect(0.022, 0.012), (xo + s * 0.012, f + c * 0.03, zc + sn * 0.03), (xo + s * 0.012, f + c * (R - 0.03), zc + sn * (R - 0.03)), BR, 'hull', 'flange', rnd=True, up=tuple(B.Pd(1, 0, 0)))
        tube(f'axcap_{s}{f}', (xo, f, zc), (x0 + s * (lw / 2 + cap), f, zc), 0.036, 0.03, BR, 'hull', 'flange', sides=8)
        if d: tube(f'axring_{s}{f}', (x0 + s * (lw / 2 + cap - 0.018), f, zc), (x0 + s * (lw / 2 + cap), f, zc), 0.042, 0.042, BR, 'hull', 'plain', sides=8)
    rr = (zc - lt) * 0.62
    for f in ((fc - hl / 3, fc + hl / 3) if d else ()):  # road wheels on the bottom run (LOD0 only)
        prism(f'rwheel_{s}{f}', ngon(rr, m - 2), (x0 - s * (lw / 2 - 0.02), f, lt + rr), (xo, f, lt + rr), BR, 'hull', 'plain', rnd=True, up=(0, 0, 1))
        if d: prism(f'rhub_{s}{f}', ngon(rr * 0.45, 6), (xo, f, lt + rr), (xo + s * 0.02, f, lt + rr), BR, 'hull', 'flange', rnd=True, up=(0, 0, 1))
    # fender (the track housing): a plate over the top run with a down-turned outer flange and sloped mudguard ends
    zf = zc + Rp + lt / 2 + 0.018; fl = hl + R * 0.55
    prism(f'fender_{s}', rect(lw + 0.05, 0.022), (x0, fc - fl, zf), (x0, fc + fl, zf), BR, 'hull', 'clouds', rnd=True)
    prism(f'flange_{s}', rect(0.014, 0.075), (x0 + s * (lw / 2 + 0.03), fc - fl, zf - 0.03), (x0 + s * (lw / 2 + 0.03), fc + fl, zf - 0.03), BR, 'hull', 'flange', rnd=True)
    for e in ((-1, 1) if d else ()):
        prism(f'guard_{s}{e}', rect(lw + 0.05, 0.02), (x0, fc + e * fl, zf), (x0, fc + e * (fl + R * 0.7), zf - R * 0.75), BR, 'hull', 'clouds', rnd=True)

def sled(d, w=0.3, tw=0.3, lw=0.15):
    """a narrow boxy cast chassis between two track units, a collar plate under the coat and a cast mask on the chassis front."""
    ci = tw - lw / 2 - 0.004
    hloft('hull', [(-0.38, 0.22, ci * 0.85, 0.08, 0), (-0.32, 0.22, ci, 0.11, 0), (0.3, 0.22, ci, 0.11, 0), (0.38, 0.22, ci * 0.85, 0.08, 0)], BR, 'hull', 'plain', n_exp=4.0, M=12)
    for s in (-1, 1): track(d, s, tw, lw=lw)
    loft('rim', [(0.33, 0, tw - 0.02, 0.36, 0), (0.38, 0, tw - 0.03, 0.35, 0)], BR, 'hull', 'flange', n_exp=2.6)
    # a cast mask plate on the chassis front (a ding's face): marks the front at any angle
    prism('hmask', [(-0.13, -0.07), (0.13, -0.07), (0.16, 0.04), (0.07, 0.08), (0, 0.04), (-0.07, 0.08), (-0.16, 0.04)], (0, 0.37, 0.22), (0, 0.42, 0.22), BR, 'hull', 'mask', scale_b=0.92)

def torso(d, cw=0.19, skirt=0.25):
    """round 2 (concepts 5103 / 5115, reference only): a long lamellar coat that flares like a bell over the sled, so the figure reads as one
    cast statue riding its treads; Qin-black lacquer plates, water-blue cord at the hem and collar, two tiers of shoulder plates, bronze neck."""
    bw = skirt + 0.05  # round 4: a slimmer bell (was + 0.09; the squat read at the fight framing)
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
        loft(f'pauldron_{s}', [(1.0, 0, 0.09, 0.105, s * 0.255), (1.1, 0, 0.1, 0.115, s * 0.25), (1.22, 0, 0.09, 0.1, s * 0.225), (1.28, 0, 0.04, 0.05, s * 0.2)],
             LQ, b, 'lacquer', n_exp=2.0, M=12)
        loft(f'pauld2_{s}', [(1.12, 0, 0.075, 0.09, s * 0.24), (1.2, 0, 0.08, 0.095, s * 0.23), (1.3, 0, 0.035, 0.045, s * 0.205)], LQ, b, 'blue', n_exp=2.0, M=10)
        if d:  # a cord edge where the plate skirt ends
            loft(f'pcord_{s}', [(0.98, 0, 0.095, 0.11, s * 0.255), (1.01, 0, 0.095, 0.11, s * 0.255)], LQ, b, 'cord', n_exp=2.0, M=12, cap=False)
    tube('neck', (0, 0, 1.25), (0, 0, 1.38), 0.058, 0.052, BR, 'head', 'plain')

def head(d, cap='knot'):
    """smooth cast bronze face mask (a calm Qin face, no features but brow, eye slits and nose ridge); a side topknot or the officer cap.
    Round 4: the head is placed on the stretched neck but not stretched itself (a smaller head on a taller body)."""
    zo, zk = Q['zoff'], Q['zk']; Q['zoff'] = ZPIV + (1.44 + zo - ZPIV) * zk - 1.44; Q['zk'] = 1.0
    # round 4: a smaller head on the stretched body (about 7 heads tall, concepts 5103 / 5105 / 5115)
    spheroid('mask', (0, 0.01, 1.44), (0.094, 0.103, MASK_RZ), BR, 'head', 'plain', segs=(12, 9))
    prism('brow', [(-0.08, -0.011), (0.08, -0.011), (0.07, 0.011), (-0.07, 0.011)], (0, 0.075, 1.46), (0, 0.1, 1.455), BR, 'head', 'flange')
    if d:
        for s in (-1, 1):
            prism(f'eye_{s}', blade(0.045, 0.011), (s * 0.036, 0.08, 1.435), (s * 0.036, 0.097, 1.435), BR, 'head', 'inlay')
        prism('nose', [(-0.013, 0), (0.013, 0), (0, 0.026)], (0, 0.09, 1.44), (0, 0.104, 1.405), BR, 'head', 'flange', scale_b=0.8)
    if cap == 'knot':  # Qin foot soldiers' topknot on the right of the crown, bound with a cord
        spheroid('cap', (0, -0.005, 1.49), (0.082, 0.088, 0.052), LQ, 'head', 'lacquer', segs=(10, 6))
        spheroid('knot', (0.045, -0.02, 1.555), (0.04, 0.04, 0.042), BR, 'head', 'plain', segs=(8, 6))
    else:  # officer: the double-tail cap (鹖冠 type, our own shape): a flat crown board and two tails sweeping up at the back
        spheroid('cap', (0, -0.005, 1.49), (0.088, 0.093, 0.054), LQ, 'head', 'lacquer', segs=(10, 6))
        prism('board', rect(0.14, 0.028), (0, 0.05, 1.53), (0, -0.09, 1.57), LQ, 'head', 'blue')
        for s in (-1, 1):
            prism(f'tail_{s}', blade(0.065, 0.028), (s * 0.035, -0.07, 1.54), (s * 0.07, -0.28, 1.59), LQ, 'head', 'lacquer', scale_b=0.35)
    Q['zoff'], Q['zk'] = zo, zk

def arms(d, r_fore=(0.3, 0.27, 0.86), l_fore=(-0.28, 0.24, 0.9)):
    """lacquer sleeves, bronze bracers and fists; forearm ends where the hands hold the weapon."""
    for side, s, fe in (('R', 1, r_fore), ('L', -1, l_fore)):
        el = (s * ELBOW[0], ELBOW[1], ELBOW[2])
        tube(f'uarm_{side}', (s * SHOULDER[0], 0, SHOULDER[2]), el, 0.062, 0.085, LQ, f'uarm_{side}', 'lacquer')  # the sleeve flares to the elbow (5115)
        tube(f'farm_{side}', el, fe, 0.056, 0.048, BR, f'farm_{side}', 'clouds')
        spheroid(f'fist_{side}', fe, (0.056, 0.06, 0.056), BR, f'farm_{side}', 'plain', segs=(8, 6))

def guard_bones(r_fore=(0.3, 0.27, 0.86), l_fore=(-0.28, 0.24, 0.9), wtip=None, extra=(), dz=0.0):
    b = [('root', (0, 0, 0), (0, 0, 0.2), None), ('hull', (0, -0.3, 0.28), (0, 0.4, 0.28), 'root'), ('torso', (0, 0, 0.5), (0, 0, 1.3), 'hull'),
         ('head', (0, 0, 1.3), (0, 0, 1.6), 'torso')]
    for side, s, fe in (('R', 1, r_fore), ('L', -1, l_fore)):
        el = (s * ELBOW[0], ELBOW[1], ELBOW[2])
        b += [(f'uarm_{side}', (s * SHOULDER[0], 0, SHOULDER[2]), el, 'torso'), (f'farm_{side}', el, fe, f'uarm_{side}')]
    if wtip: b.append(('weapon', r_fore, wtip, 'farm_R'))
    b = b + list(extra)
    return [x if x[0] in ('root', 'hull') else tuple(x) + (dz, ZK) for x in b]  # dz: torso set lower into the hull (弩手); ZK: the round 4 stretch

def base(d, **k):
    Q['zk'] = 1.0; sled(d, k.get('w', 0.3), k.get('tw', TRACK['tw']), k.get('lw', TRACK['lw'])); Q['zoff'] = k.get('dz', 0.0); Q['zk'] = ZK
    torso(d, k.get('cw', 0.19), k.get('skirt', 0.25)); head(d, k.get('cap', 'knot'))
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
NU_DZ = -0.06  # round 4: -0.16 -> -0.06 (taller archer; the prod carries the read). round 3: lower still (the kneeling archer read; run 45445673747 zu/nu IoU 0.75 at the limit)
def nu_build(d):
    base(d, r_fore=NU_R, l_fore=NU_L, dz=NU_DZ)
    # stock from the right fist forward, prod (bow) across, string; bronze trigger box (batch-cast Qin trigger)
    prism('stock', rect(0.05, 0.06), (0.04, 0.1, 0.97), NU_TIP, LQ, 'weapon', 'lacquer')
    arc = [(math.sin(a) * 0.64, 0.68 - (1 - math.cos(a)) * 0.3, 0.98) for a in [math.radians(x) for x in range(-70, 71, 20 if d else 35)]]
    path_tube('prod', arc, 0.035, BR, 'weapon', 'flange', sides=6)  # the prod spans 1.2 m, wider than the hull: the 弩手 reads wide and low
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
    up = R('weapon', 'up', 45); s = w + STRIKE
    keys = {'torso': [(0, (0, 0, 0)), (w, R('torso', 'back', 18)), (s, R('torso', 'back', 20)), (s + RECOVER, (0, 0, 0))],
            'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 30)), (s, R('uarm_R', 'up', 24)), (s + RECOVER, (0, 0, 0))],
            'uarm_L': [(0, (0, 0, 0)), (w, R('uarm_L', 'up', 30)), (s, R('uarm_L', 'up', 24)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, up), (s, R('weapon', 'up', 40)), (s + RECOVER, (0, 0, 0))]}
    return acts(arm, keys, w), None, w, 'weapon'


# 盾 shieldbearer: wider sled and torso, a tall notched-top shield in front on the left arm; shove -----------------------------------------
DUN_L = (-0.12, 0.36, 0.95)
DUN_TIP = (-0.05, 0.42, 1.62)
def dun_build(d):
    base(d, w=0.38, tw=0.43, lw=0.17, cw=0.23, skirt=0.29, l_fore=DUN_L, r_fore=(0.24, 0.32, 0.9))
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
    keys = {'torso': [(0, (0, 0, 0)), (w, R('torso', 'back', 18, (-0.3, 0, 1.2))), (s, R('torso', 'fwd', 16)), (s + RECOVER, (0, 0, 0))],
            'uarm_L': [(0, (0, 0, 0)), (w, R('uarm_L', 'back', 35)), (s, R('uarm_L', 'fwd', 30)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, R('weapon', 'back', 40)), (s, R('weapon', 'fwd', 15)), (s + RECOVER, (0, 0, 0))]}
    loc = {'hull': [(0, (0, 0, 0)), (w, (0, -0.15, 0)), (s, (0, 0.35, 0)), (s + RECOVER, (0, 0, 0))]}
    return acts(arm, keys, w, loc), None, w, 'weapon'


# 车 chariot (round 4: a war chariot, not a cart). Qin bronze chariot No. 1 language (reference only): an open box (舆) with a high front
# breastwork and side rails, a standing armoured driver, a small round canopy on a bronze frame (black lacquer, water-blue edge, bronze ribs and
# finial), a 戟 in the rear rack and a shield hung on the side rail; the draught pole (辀) curves forward to a yoke bar (衡) with two yoke
# saddles (轭) and ends in the bronze beast-head ram. Running gear: one long track unit per side with big spoked end wheels and axle caps.
CHE_TIP = (0, 1.42, 0.62)
# Chariot track units: centre offset, link width, half wheelbase, end wheel radius, link thickness, centre f, spokes per wheel.
CHE_TRACK = dict(tw=0.6, lw=0.2, hl=0.7, R=0.2, lt=0.05, fc=-0.05, spokes=6, cap=0.1, pitch=0.18)
# Canopy: centre f, underside z, radius (round 3: 0.8 m radius at 2.04 m, read as a blue parasol).
CHE_CANOPY = dict(f=-0.22, z=1.66, r=0.52)
def che_build(d):
    T = CHE_TRACK; ci = T['tw'] - T['lw'] / 2 - 0.004
    hloft('hull', [(-0.82, 0.34, ci * 0.9, 0.12, 0), (-0.74, 0.34, ci, 0.17, 0), (0.6, 0.34, ci, 0.17, 0), (0.7, 0.34, ci * 0.85, 0.12, 0)], BR, 'hull', 'plain', n_exp=4.0, M=12)
    for s in (-1, 1):
        track(d, s, T['tw'], hl=T['hl'], R=T['R'], lw=T['lw'], lt=T['lt'], fc=T['fc'], spokes=T['spokes'], cap=T['cap'], pitch=T['pitch'])
    # box (舆): floor, side rails (bronze lattice, black lacquer top rail with a water-blue stripe), high front breastwork, rear corner posts
    prism('floor', rect(1.0, 0.05), (0, -0.8, 0.56), (0, 0.46, 0.56), BR, 'hull', 'plain', rnd=True)
    for s in (-1, 1):
        prism(f'rail_{s}', rect(0.03, 0.3), (s * 0.5, -0.78, 0.73), (s * 0.5, 0.42, 0.73), BR, 'hull', 'clouds', rnd=True)
        prism(f'toprail_{s}', rect(0.06, 0.04), (s * 0.5, -0.8, 0.9), (s * 0.5, 0.46, 0.9), LQ, 'hull', 'lacquer', rnd=True)
        prism(f'stripe_{s}', rect(0.065, 0.02), (s * 0.5, -0.8, 0.86), (s * 0.5, 0.46, 0.86), LQ, 'hull', 'blue', rnd=True)
        prism(f'post_{s}', rect(0.06, 0.06), (s * 0.47, -0.76, 0.56), (s * 0.47, -0.76, 1.0), LQ, 'hull', 'lacquer', rnd=True, up=(0, -1, 0))
    prism('front', [(-0.5, 0), (0.5, 0), (0.46, 0.44), (0.2, 0.5), (-0.2, 0.5), (-0.46, 0.44)], (0, 0.42, 0.58), (0, 0.47, 0.58), BR, 'hull', 'mask')
    prism('fbar', rect(1.0, 0.05), (0, 0.4, 1.06), (0, 0.5, 1.06), LQ, 'hull', 'lacquer', rnd=True)
    # canopy: bronze pole and collar, black lacquer dome, water-blue edge band, bronze ribs and finial (smaller and lower than round 3)
    C = CHE_CANOPY; cf, cz, cr = C['f'], C['z'], C['r']
    tube('pole', (0, cf, 0.58), (0, cf, cz + 0.13), 0.03, 0.026, BR, 'canopy', 'plain', sides=6)
    loft('canopy', [(cz, cf, cr, cr, 0), (cz + 0.06, cf, cr * 0.8, cr * 0.8, 0), (cz + 0.11, cf, cr * 0.38, cr * 0.38, 0), (cz + 0.125, cf, 0.05, 0.05, 0)], LQ, 'canopy', 'lacquer', n_exp=2.0, M=16)
    loft('cband', [(cz - 0.012, cf, cr + 0.015, cr + 0.015, 0), (cz + 0.025, cf, cr * 0.93 + 0.012, cr * 0.93 + 0.012, 0)], LQ, 'canopy', 'blue', n_exp=2.0, M=16, cap=False)
    spheroid('finial', (0, cf, cz + 0.15), (0.045, 0.045, 0.05), BR, 'canopy', 'flange', segs=(8, 5))
    if d:
        tube('collar', (0, cf, cz - 0.06), (0, cf, cz + 0.01), 0.045, 0.06, BR, 'canopy', 'flange', sides=8)
        prof = [(0.0, cz + 0.135), (cr * 0.38, cz + 0.122), (cr * 0.8, cz + 0.068), (cr + 0.02, cz + 0.006)]
        for k in range(6):
            a = k * math.tau / 6 + math.pi / 6; c, sn = math.cos(a), math.sin(a)
            path_tube(f'rib_{k}', [(c * r, cf + sn * r, z) for r, z in prof], 0.012, BR, 'canopy', 'flange', sides=4)
    # driver: a standing armoured figure (coat, chest, small pauldrons, mask and cap), hands on the breastwork
    df = 0.1
    loft('dcoat', [(0.58, df, 0.17, 0.14, 0), (0.8, df, 0.16, 0.13, 0), (1.0, df, 0.14, 0.11, 0)], LQ, 'driver', 'lacquer', n_exp=2.2)
    loft('dchest', [(0.98, df, 0.14, 0.11, 0), (1.18, df, 0.16, 0.12, 0), (1.3, df, 0.1, 0.08, 0)], LQ, 'driver', 'lacquer', n_exp=2.4)
    loft('dbelt', [(0.98, df, 0.155, 0.125, 0), (1.03, df, 0.155, 0.125, 0)], LQ, 'driver', 'cord', cap=False)
    tube('dneck', (0, df, 1.28), (0, df, 1.36), 0.045, 0.04, BR, 'driver', 'plain')
    spheroid('dhead', (0, df + 0.01, 1.42), (0.08, 0.088, 0.1), BR, 'driver', 'plain', segs=(10, 7))
    spheroid('dcap', (0, df - 0.005, 1.47), (0.072, 0.078, 0.045), LQ, 'driver', 'lacquer', segs=(8, 5))
    for s in (-1, 1):
        loft(f'dpaul_{s}', [(1.14, df, 0.07, 0.08, s * 0.17), (1.24, df, 0.075, 0.085, s * 0.16), (1.3, df, 0.03, 0.04, s * 0.13)], LQ, 'driver', 'blue', n_exp=2.0, M=8)
        tube(f'darm_{s}', (s * 0.18, df, 1.22), (s * 0.17, df + 0.16, 1.04), 0.04, 0.045, LQ, 'driver', 'lacquer', sides=6)
        tube(f'dfore_{s}', (s * 0.17, df + 0.16, 1.04), (s * 0.13, 0.4, 1.08), 0.036, 0.03, BR, 'driver', 'clouds', sides=6)
    # weapons carried: a 戟 in the rear right rack (leaning back and out), a notched shield hung on the left rail
    tube('jshaft', (0.44, -0.7, 0.58), (0.58, -0.98, 1.92), 0.024, 0.022, LQ, 'hull', 'lacquer', sides=6)
    prism('jpoint', blade(0.11, 0.025), (0.58, -0.98, 1.92), (0.6, -1.02, 2.08), BR, 'hull', 'flange', scale_b=0.05)
    prism('jge', blade(0.08, 0.02), (0.58, -0.97, 1.9), (0.66, -0.78, 1.86), BR, 'hull', 'flange', scale_b=0.15)
    sh = [(-0.16, -0.2), (0.16, -0.2), (0.18, 0.12), (0.08, 0.16), (0, 0.22), (-0.08, 0.16), (-0.18, 0.12)]
    prism('shield', sh, (-0.52, -0.2, 0.76), (-0.56, -0.2, 0.76), LQ, 'hull', 'lacquer', up=(0, 0, 1))
    if d: prism('sboss', ngon(0.05, 8), (-0.56, -0.2, 0.77), (-0.585, -0.2, 0.77), BR, 'hull', 'mask', scale_b=0.6, up=(0, 0, 1))
    # draught pole (辀) curving forward and up, yoke bar (衡) with two yoke saddles (轭), beast-head ram finial: the charge leads with it
    path_tube('ram', [(0, 0.6, 0.44), (0, 0.95, 0.54), (0, 1.25, 0.62)], 0.05, BR, 'ram', 'flange', sides=8)
    tube('yoke', (-0.48, 1.04, 0.66), (0.48, 1.04, 0.66), 0.028, 0.028, BR, 'ram', 'plain', sides=6)
    for s in (-1, 1):
        for e in (-1, 1):
            prism(f'saddle_{s}{e}', blade(0.05, 0.025), (s * 0.26, 1.04, 0.67), (s * 0.26 + e * 0.09, 1.04, 0.47), BR, 'ram', 'flange', scale_b=0.5)
        spheroid(f'yend_{s}', (s * 0.5, 1.04, 0.66), (0.04, 0.04, 0.04), BR, 'ram', 'flange', segs=(6, 4))
    spheroid('rhead', (0, 1.3, 0.64), (0.1, 0.14, 0.1), BR, 'ram', 'mask', segs=(10, 7))
    prism('rhorn', blade(0.08, 0.03), (0, 1.36, 0.7), CHE_TIP, BR, 'ram', 'flange', scale_b=0.1)  # round 4: ears dropped (triangle budget)

def che_bones():
    C = CHE_CANOPY
    return [('root', (0, 0, 0), (0, 0, 0.2), None), ('hull', (0, -0.6, 0.42), (0, 0.6, 0.42), 'root'), ('canopy', (0, C['f'], 0.58), (0, C['f'], C['z'] + 0.13), 'hull'),
            ('driver', (0, 0.1, 0.58), (0, 0.1, 1.5), 'hull'), ('ram', (0, 0.6, 0.44), CHE_TIP, 'hull')]

def che_clips(arm):
    R = lambda b, w, a, p=None: rot_for(arm, b, w, a, p); w = WINDUP['che']; s = w + 0.3
    idle = {'canopy': [(0, (0, 0, 0)), (1.0, R('canopy', 'right', 2)), (2.0, (0, 0, 0))], 'driver': [(0, (0, 0, 0)), (1.0, R('driver', 'fwd', 3)), (2.0, (0, 0, 0))]}
    move = {'hull': [(0, (0, 0, 0)), (0.25, R('hull', 'up', 1.5)), (0.5, (0, 0, 0)), (0.75, R('hull', 'down', 1.5)), (1.0, (0, 0, 0))],
            'canopy': [(0, R('canopy', 'back', 3)), (0.5, R('canopy', 'back', 5)), (1.0, R('canopy', 'back', 3))]}
    mloc = {'hull': [(0, (0, 0, 0)), (0.25, (0, 0, 0.012)), (0.5, (0, 0, 0)), (0.75, (0, 0, 0.012)), (1.0, (0, 0, 0))]}
    att = {'hull': [(0, (0, 0, 0)), (w, R('hull', 'up', 16)), (s, R('hull', 'down', 4)), (s + RECOVER, (0, 0, 0))],
           'driver': [(0, (0, 0, 0)), (w, R('driver', 'back', 12)), (s, R('driver', 'fwd', 15)), (s + RECOVER, (0, 0, 0))],
           'canopy': [(0, (0, 0, 0)), (w, R('canopy', 'fwd', 6)), (s, R('canopy', 'back', 10)), (s + RECOVER, (0, 0, 0))],
           'ram': [(0, (0, 0, 0)), (w, R('ram', 'up', 22)), (s, R('ram', 'down', 6)), (s + RECOVER, (0, 0, 0))]}
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
    keys = {'uarm_R': [(0, (0, 0, 0)), (w, R('uarm_R', 'up', 85)), (s, R('uarm_R', 'fwd', 30)), (s + RECOVER, (0, 0, 0))],
            'farm_R': [(0, (0, 0, 0)), (w, R('farm_R', 'up', 30)), (s, (0, 0, 0)), (s + RECOVER, (0, 0, 0))],
            'weapon': [(0, (0, 0, 0)), (w, R('weapon', 'back', 30)), (s, R('weapon', 'fwd', 90)), (s + RECOVER, (0, 0, 0))],
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
            # round 4 proportion gate: head height = body top (cap, knot or officer tails) minus the mask chin (build constants, unit scale)
            sc = WZ_SCALE if key == 'wz' else 1.0; dz = NU_DZ if key == 'nu' else 0.0
            chin = (ZPIV + (1.44 + dz - ZPIV) * ZK - MASK_RZ) * sc; heads = z1 / max(z1 - chin, 1e-6)
            G(heads >= HEADS_MIN, f'body {heads:.1f} heads tall (head {z1 - chin:.2f} m incl. cap; min {HEADS_MIN}; round 3 about 4.9)')
            info.update(heads=heads)
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
