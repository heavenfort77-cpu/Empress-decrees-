# Buff creatures (PIECES round 1; owner 25 Nov 13:08): the "crab" and the "wanderer" (working names). They never attack; the last hit
# takes a boon (index.html CONFIG.CRAB r 0.7 m, CONFIG.WANDERER r 0.5 m; today two flat-colour boxes each).
# Own designs from the research rule list: small bronze animal machines by animal analogy, a ding / lei vessel hull, chariot running
# gear, segmented castings with a mould-seam flange, stamp bands from the brass trim sheet and silver inlay lines; no patina (live).
#   crab     = a low covered food vessel (the lid seam is its shell edge, two upright ear handles, a taotie stamp plate for a mouth)
#              carried sideways on six cast legs hung from two axle rails with hub caps; two raised pincers, two stalk eyes. Low, wide.
#   wanderer = a hu wine jar laid forward like a heron's body: the neck rises out of the jar's mouth, a long dagger bill, two stilt legs
#              hung from small spoked chariot wheels, a tail of three cast blades at the foot ring, and a chariot parasol carried over
#              its back (the traveller). Tall, narrow.
# The two read apart by outline alone (gate in pieces_measure.py: silhouette IoU <= 0.6). Each: LOD0 skinned (rigid parts), LOD1 and
# LOD2 static, clips idle and move (loops). The units face +Z in three.js. Usage: python pieces_creatures.py OUTDIR
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prop_kit as K
import pieces_kit as PK
from prop_kit import lathe, spheroid, sweep, prism, torus, loft, ngon, rect, blade

OUTDIR = sys.argv[-1] if os.path.isdir(sys.argv[-1]) else '/tmp/pieces'

# CONFIG ---------------------------------------------------------------------------------------------------------------
# Triangle budgets LOD0/1/2 (task: 1.5-3k LOD0 plus a low LOD) and the LOD0 floor.
BUDGET = (3000, 1200, 450)
TRIS_MIN = 1500
# Game body radius m (index.html CONFIG.CRAB.r, CONFIG.WANDERER.r): the hull stays inside it, legs may reach past it.
CRAB_R, WAND_R = 0.7, 0.5
# Crab hull sections (z, centre f, half width, half depth) m: belly, seam, lid.
C_HULL = [(0.30, 0.0, 0.30, 0.20), (0.36, 0.0, 0.50, 0.31), (0.47, 0.0, 0.60, 0.385), (0.555, 0.0, 0.62, 0.40), (0.585, 0.0, 0.60, 0.385), (0.68, 0.0, 0.50, 0.31),
          (0.75, 0.0, 0.30, 0.18), (0.77, 0.0, 0.20, 0.11)]
# Crab stamp bands by height (trim sheet rows).
C_BANDS = [(0.0, 0.46, 'plain'), (0.46, 0.555, 'clouds'), (0.555, 0.60, 'flange'), (0.60, 0.9, 'plain')]
# Crab legs: f of the three hips per side; hip x and z, knee (x, z), foot x; the f spread factor at knee and foot.
C_LEG_F, C_HIP, C_KNEE, C_FOOT_X, C_SPREAD = (-0.27, 0.0, 0.25), (0.64, 0.45), (0.84, 0.68), 0.97, (1.25, 1.5)
# Crab claw: shoulder, elbow, wrist (x outward, f, z) m.
C_CLAW = [(0.48, 0.30, 0.50), (0.70, 0.50, 0.64), (0.62, 0.70, 0.80)]
# Crab size gates: width range m, most height m, width over height at least.
C_WIDTH, C_HEIGHT, C_WIDE = (1.6, 2.2), 1.2, 1.6
# Crab clips: idle seconds, claw raise deg, body bob m; move seconds, leg lift deg, leg swing deg, body sway m.
C_IDLE, C_MOVE = (2.4, 5.0, 0.012), (0.8, 12.0, 8.0, 0.03)
# Wanderer jar profile (radius, z) m, built upright about (0, W_CF), then laid forward by W_TILT deg about W_PIVOT.
W_JAR = [(0.0, 1.02), (0.16, 1.02), (0.185, 1.06), (0.15, 1.10), (0.30, 1.28), (0.345, 1.44), (0.31, 1.60), (0.21, 1.74), (0.145, 1.82), (0.17, 1.90),
         (0.175, 1.93), (0.10, 1.975), (0.0, 1.985)]
W_CF, W_TILT, W_PIVOT = -0.05, 40, (0.0, -0.05, 1.42)
# Wanderer stamp bands by height on the upright jar.
W_BANDS = [(1.0, 1.37, 'plain'), (1.37, 1.52, 'clouds'), (1.52, 1.60, 'inlay'), (1.60, 1.80, 'lozenge'), (1.80, 2.0, 'flange')]
# Wanderer neck: lower path and radii (bone neck), upper path and radii (bone head), m.
W_NECK, W_NECK_R = [(0.0, 0.27, 1.80), (0.0, 0.40, 1.98), (0.0, 0.43, 2.16), (0.0, 0.38, 2.34)], [0.10, 0.075, 0.06, 0.052]
W_NECK2, W_NECK2_R = [(0.0, 0.38, 2.34), (0.0, 0.40, 2.48), (0.0, 0.48, 2.56)], [0.052, 0.05, 0.055]
# Wanderer legs: hip (x, f, z), hock, ankle, m; hip wheel radius.
W_HIP, W_HOCK, W_ANKLE, W_WHEEL = (0.41, -0.05, 1.40), (0.41, -0.26, 0.76), (0.41, 0.0, 0.07), 0.17
# Wanderer parasol: centre f, top profile (radius, z), m.
W_CAN_F, W_CAN = -0.26, [(0.0, 2.40), (0.14, 2.385), (0.30, 2.33), (0.42, 2.25), (0.42, 2.232), (0.0, 2.295)]
# Wanderer size gates: height range m, height over width at least.
W_HEIGHT, W_TALL = (2.2, 2.9), 2.0
# Wanderer clips: idle seconds, head look deg, head nod deg; move seconds (slow), thigh swing deg, shin fold deg, body bob m.
W_IDLE, W_MOVE = (3.2, 9.0, 6.0), (1.6, 18.0, 20.0, 0.02)
BR, INL, CIN, DARK = 'palBronze', 'palInlay', 'palCinnabar', 'palDark'
SIDE = ((1, 'L'), (-1, 'R'))
PK.mutate(globals())


# ---------------------------------------------------------------------------------------------------------------- crab
def crab_build(detail):
    PK.bone('body')
    loft('hull', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in C_HULL], BR, C_BANDS, n_exp=2.5, M=24)
    loft('seam', [(0.548, 0.0, 0.645, 0.425, 0.0), (0.578, 0.0, 0.645, 0.425, 0.0)], BR, 'flange', n_exp=2.5, M=24)
    loft('seam_inlay', [(0.607, 0.0, 0.592, 0.378, 0.0), (0.622, 0.0, 0.58, 0.368, 0.0)], INL, 'plain', n_exp=2.5, M=24, cap=False)
    for q, (xa, xb) in enumerate(((-0.34, -0.13), (-0.1, 0.1), (0.13, 0.34))):  # the lid's cast crest (the mould seam), in three notched lengths
        prism(f'crest_{q}', rect(0.04, 0.10), (xa, 0.0, 0.765 - abs(xa + xb) * 0.03), (xb, 0.0, 0.765 - abs(xa + xb) * 0.03), BR, 'flange', rnd=False)
    for s, n in SIDE:  # upright ear handles on the lid ends, like a vessel's
        torus(f'ear_{n}', (s * 0.44, 0.0, 0.715), (0, 1, 0), 0.078, 0.021, BR, 'flange', sg=(10, 4))
    prism('mask', rect(0.38, 0.13), (0.0, 0.375, 0.465), (0.0, 0.415, 0.465), BR, 'mask', rnd=False)
    for s, n in SIDE:
        sweep(f'stalk_{n}', [(s * 0.20, 0.33, 0.62), (s * 0.23, 0.44, 0.80), (s * 0.25, 0.48, 0.94)], [0.042, 0.032, 0.03], BR, 'flange', n=6)
        spheroid(f'eye_{n}', (s * 0.25, 0.49, 0.975), (0.062, 0.062, 0.062), INL, 'plain', sg=(8, 5))
        if detail: spheroid(f'pupil_{n}', (s * 0.25, 0.538, 0.98), (0.028, 0.02, 0.028), DARK, 'plain', sg=(6, 4))
        # axle rail along the hull side with a hub cap at each end: the legs hang from it (chariot running gear)
        prism(f'rail_{n}', ngon(0.045, 6), (s * 0.63, -0.34, 0.45), (s * 0.63, 0.32, 0.45), BR, 'flange', rnd=True)
        for q, f in enumerate((-0.37, 0.31)):
            prism(f'hub_{n}{q}', ngon(0.08, 8), (s * 0.63, f, 0.45), (s * 0.63, f + 0.045, 0.45), BR, 'mark', rnd=False)
    for s, n in SIDE:
        for i, f in enumerate(C_LEG_F):
            PK.bone(f'leg_{n}{i}')
            hip = (s * C_HIP[0], f, C_HIP[1]); knee = (s * C_KNEE[0], f * C_SPREAD[0], C_KNEE[1]); foot = (s * C_FOOT_X, f * C_SPREAD[1], 0.0)
            prism(f'femur_{n}{i}', blade(0.12, 0.085), hip, knee, BR, 'plain', scale_b=0.8, rnd=False, up=(0, 0, 1))
            prism(f'tibia_{n}{i}', blade(0.105, 0.075), knee, foot, BR, 'flange', scale_b=0.1, rnd=False, up=(s, 0, 0.35))
            spheroid(f'knee_{n}{i}', knee, (0.062, 0.062, 0.062), BR, 'lozenge', sg=(6, 4))
            if detail:
                prism(f'leg_inlay_{n}{i}', rect(0.022, 0.012), (hip[0] + s * 0.03, hip[1], hip[2] + 0.062), (knee[0] - s * 0.02, knee[1], knee[2] + 0.04), INL, 'plain', rnd=True, up=(0, 0, 1))
    for s, n in SIDE:
        PK.bone(f'claw_{n}')
        sh, el, wr = [(s * x, f, z) for x, f, z in C_CLAW]
        prism(f'arm_{n}', ngon(0.062, 6), sh, el, BR, 'plain', rnd=False)
        spheroid(f'elbow_{n}', el, (0.072, 0.072, 0.072), BR, 'lozenge', sg=(6, 4))
        prism(f'fore_{n}', ngon(0.062, 6), el, wr, BR, 'plain', scale_b=1.35, rnd=False)
        spheroid(f'palm_{n}', (s * 0.60, 0.745, 0.835), (0.105, 0.115, 0.095), BR, 'plain', sg=(8, 5))
        sweep(f'finger_up_{n}', [(s * 0.60, 0.78, 0.885), (s * 0.50, 0.92, 0.99), (s * 0.36, 0.97, 1.0)], [0.078, 0.058, 0.0], BR, 'flange', n=4, flat=(1.0, 0.5), side=(0, 0, 1))
        sweep(f'finger_lo_{n}', [(s * 0.60, 0.80, 0.80), (s * 0.50, 0.93, 0.845), (s * 0.375, 0.97, 0.905)], [0.058, 0.046, 0.0], BR, 'flange', n=4, flat=(1.0, 0.5), side=(0, 0, 1))
        if detail: torus(f'wrist_{n}', (s * 0.635, 0.665, 0.77), (-s * 0.08, 0.2, 0.16), 0.088, 0.015, INL, 'plain', sg=(8, 3))
    PK.bone('root')

def crab_bones():
    out = [('root', (0, 0, 0), (0, 0, 0.2), None), ('body', (0, 0, 0.45), (0, 0, 0.75), 'root')]
    for s, n in SIDE:
        for i, f in enumerate(C_LEG_F):
            out.append((f'leg_{n}{i}', (s * C_HIP[0], f, C_HIP[1]), (s * C_KNEE[0], f * C_SPREAD[0], C_KNEE[1]), 'body'))
        out.append((f'claw_{n}', (s * C_CLAW[0][0], C_CLAW[0][1], C_CLAW[0][2]), (s * C_CLAW[2][0], C_CLAW[2][1], C_CLAW[2][2]), 'body'))
    return out

def crab_clips(arm):
    tau = math.tau; dur, raise_, bob = C_IDLE
    rot = {f'claw_{n}': PK.wave(dur, 8, lambda p, s=s: [((1, 0, 0), -raise_ * (1 + math.sin(tau * p + (0 if s > 0 else math.pi)))), ((0, 0, 1), s * 3 * math.sin(tau * p))]) for s, n in SIDE}
    idle = PK.clip(arm, 'idle', rot, {'body': PK.wave(dur, 8, lambda p: (0, 0, bob * math.sin(tau * p)))})
    dur2, lift, swing, sway = C_MOVE; rot = {}
    for s, n in SIDE:
        for i in range(3):
            ph = 0.0 if (i + (s > 0)) % 2 == 0 else 0.5  # two tripods: L0 R1 L2 against R0 L1 R2
            rot[f'leg_{n}{i}'] = PK.wave(dur2, 8, lambda p, s=s, ph=ph: [((0, 1, 0), s * lift * max(0.0, math.sin(tau * (p + ph)))), ((0, 0, 1), swing * math.cos(tau * (p + ph)))])
        rot[f'claw_{n}'] = PK.wave(dur2, 8, lambda p, s=s: [((1, 0, 0), -4 - 2 * math.sin(2 * tau * p + s))])
    rot['body'] = PK.wave(dur2, 8, lambda p: [((0, 1, 0), 2 * math.sin(tau * p))])
    move = PK.clip(arm, 'move', rot, {'body': PK.wave(dur2, 8, lambda p: (sway * math.sin(tau * p), 0, 0.015 * math.cos(2 * tau * p)))})
    return [(idle, dur, 'claw_L', 0.02), (move, dur2, 'leg_L0', 0.03)]

def crab_gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0); w = x1 - x0
    G(C_WIDTH[0] <= w <= C_WIDTH[1] and z1 <= C_HEIGHT and w >= C_WIDE * z1, f'crab {w:.2f} m wide x {z1:.2f} m high (width {C_WIDTH}, height <= {C_HEIGHT}, width >= {C_WIDE} x height): low and wide')
    G(max(h[2] for h in C_HULL) <= CRAB_R + 0.01, f'crab hull half width {max(h[2] for h in C_HULL):.2f} m inside the game radius {CRAB_R} (legs reach {w / 2:.2f})')
    G(-0.02 <= z0 <= 0.01, f'crab feet on the ground (lowest z {z0:.3f})')
    G({BR, INL} <= K.mats(l0) and BR in K.mats(l2), f'crab materials {sorted(K.mats(l0))} (brass bronze + silver inlay)')
    G(K.tris(l0) >= TRIS_MIN, f'crab_lod0 tris {K.tris(l0)} (min {TRIS_MIN})')


# ------------------------------------------------------------------------------------------------------------ wanderer
def wand_build(detail):
    PK.bone('body')
    n0 = len(K.PARTS)
    lathe('jar', W_JAR, BR, W_BANDS, n=16, cf=W_CF)
    lathe('jar_inlay', [(0.352, 1.425), (0.354, 1.452)], INL, 'plain', n=16, cf=W_CF)
    lathe('jar_seam', [(0.19, 1.925), (0.20, 1.94), (0.19, 1.955)], BR, 'flange', n=16, cf=W_CF)
    jar = [p[0] for p in K.PARTS[n0:]]; PK.pre_uv(jar); PK.tilt(jar, W_PIVOT, (1, 0, 0), W_TILT)
    for k in (-1, 0, 1):  # tail: three cast blades at the jar's foot ring
        prism(f'tail_{k}', blade(0.13, 0.03), (k * 0.07, -0.30, 1.13), (k * 0.21, -0.66, 0.93), BR, 'flange', scale_b=0.2, rnd=False, up=(0, 0, 1))
    for s, n in SIDE:  # hip wheels: small spoked chariot wheels the legs hang from
        c = (s * (W_HIP[0] - 0.04), W_HIP[1], W_HIP[2])
        torus(f'wheel_{n}', c, (1, 0, 0), W_WHEEL, 0.026, BR, 'flange', sg=(12, 4))
        spheroid(f'nave_{n}', c, (0.06, 0.07, 0.07), BR, 'lozenge', sg=(8, 5))
        prism(f'axle_cap_{n}', ngon(0.036, 6), c, (c[0] + s * 0.1, c[1], c[2]), BR, 'mark', rnd=False)
        if detail:
            for q in range(6):
                a = q * math.tau / 6 + 0.3
                prism(f'spoke_{n}{q}', rect(0.024, 0.024), c, (c[0], c[1] + math.cos(a) * W_WHEEL, c[2] + math.sin(a) * W_WHEEL), BR, 'plain', rnd=True, up=(1, 0, 0))
    # parasol: a turned bronze canopy on a pole over the back, cinnabar underneath, silver ribs
    prism('pole', ngon(0.024, 6), (0.0, -0.10, 1.62), (0.0, W_CAN_F, 2.30), BR, 'plain', rnd=True)
    lathe('canopy', W_CAN, BR, [(2.2, 2.27, 'inlay'), (2.27, 2.45, 'plain')], n=12, cf=W_CAN_F)
    lathe('canopy_under', [(0.0, 2.29), (0.40, 2.228), (0.40, 2.22), (0.0, 2.283)], CIN, 'plain', n=12, cf=W_CAN_F)  # a closed lining disc just under the bronze
    spheroid('finial', (0.0, W_CAN_F, 2.425), (0.04, 0.04, 0.045), INL, 'plain', sg=(6, 4))
    if detail:
        for q in range(12):
            a = q * math.tau / 12; ca, sa = math.cos(a), math.sin(a)
            for j, ((r0, z0), (r1, z1)) in enumerate((((0.05, 2.404), (0.30, 2.338)), ((0.30, 2.338), (0.435, 2.256)))):
                prism(f'rib_{q}{j}', rect(0.018, 0.014), (ca * r0, W_CAN_F + sa * r0, z0), (ca * r1, W_CAN_F + sa * r1, z1), INL, 'plain', rnd=True, up=(0, 0, 1))
    # neck in two cast lengths rising from the jar's mouth, silver collars at the joints
    torus('mouth_ring', (0.0, 0.30, 1.84), (0, 0.64, 0.77), 0.125, 0.026, INL, 'plain', sg=(10, 4))
    PK.bone('neck')
    sweep('neck', W_NECK, W_NECK_R, BR, 'plain', n=6)
    torus('neck_ring', W_NECK[-1], (0, -0.1, 1), 0.062, 0.02, BR, 'flange', sg=(8, 4))
    PK.bone('head')
    sweep('neck2', W_NECK2, W_NECK2_R, BR, 'plain', n=6)
    spheroid('head', (0.0, 0.55, 2.585), (0.068, 0.115, 0.072), BR, 'plain', sg=(8, 5))
    prism('bill', blade(0.075, 0.06), (0.0, 0.63, 2.58), (0.0, 1.0, 2.40), BR, 'flange', scale_b=0.08, rnd=False, up=(0, 0, 1))
    prism('crest', blade(0.055, 0.022), (0.0, 0.50, 2.645), (0.0, 0.26, 2.77), CIN, 'plain', scale_b=0.2, rnd=True, up=(0, 0, 1))
    for s, n in SIDE: spheroid(f'eye_{n}', (s * 0.06, 0.60, 2.60), (0.02, 0.022, 0.022), INL, 'plain', sg=(6, 4))
    for s, n in SIDE:
        hip, hock, ank = [(s * x, f, z) for x, f, z in (W_HIP, W_HOCK, W_ANKLE)]
        PK.bone(f'thigh_{n}')
        prism(f'thigh_{n}', blade(0.12, 0.10), hip, hock, BR, 'plain', scale_b=0.6, rnd=False, up=(0, -1, 0))
        if detail: prism(f'thigh_inlay_{n}', rect(0.02, 0.012), (hip[0] + s * 0.035, hip[1] - 0.06, hip[2] - 0.12), (hock[0] + s * 0.025, hock[1] - 0.005, hock[2] + 0.1), INL, 'plain', rnd=True, up=(s, 0, 0))
        PK.bone(f'shin_{n}')
        spheroid(f'hock_{n}', hock, (0.06, 0.065, 0.065), BR, 'lozenge', sg=(6, 4))
        prism(f'shin_{n}', blade(0.07, 0.06), hock, ank, BR, 'plain', scale_b=0.85, rnd=False, up=(0, 1, 0))
        for q, (dx, df) in enumerate(((-0.12, 0.27), (0.0, 0.30), (0.12, 0.27), (0.0, -0.15))):
            prism(f'toe_{n}{q}', blade(0.055, 0.04), (ank[0], ank[1], 0.06), (ank[0] + dx, ank[1] + df, 0.02), BR, 'flange', scale_b=0.15, rnd=False, up=(0, 0, 1))
    PK.bone('root')

def wand_bones():
    out = [('root', (0, 0, 0), (0, 0, 0.2), None), ('body', W_PIVOT, (0, -0.05, 1.8), 'root'), ('neck', W_NECK[0], W_NECK[-1], 'body'), ('head', W_NECK2[0], (0.0, 0.55, 2.58), 'neck')]
    for s, n in SIDE:
        hip, hock, ank = [(s * x, f, z) for x, f, z in (W_HIP, W_HOCK, W_ANKLE)]
        out += [(f'thigh_{n}', hip, hock, 'body'), (f'shin_{n}', hock, ank, f'thigh_{n}')]
    return out

def wand_clips(arm):
    tau = math.tau; dur, look, nod = W_IDLE
    rot = {'neck': PK.wave(dur, 8, lambda p: [((1, 0, 0), 3 * math.sin(tau * p))]),
           'head': PK.wave(dur, 8, lambda p: [((1, 0, 0), nod * math.sin(tau * p + 1.0)), ((0, 0, 1), look * math.sin(tau * p))])}
    idle = PK.clip(arm, 'idle', rot, {'body': PK.wave(dur, 8, lambda p: (0, 0, 0.008 * math.sin(2 * tau * p)))})
    dur2, sw, fold, bob = W_MOVE; rot = {}
    for s, n in SIDE:
        ph = 0.0 if s > 0 else 0.5
        rot[f'thigh_{n}'] = PK.wave(dur2, 12, lambda p, ph=ph: [((1, 0, 0), -sw * math.sin(tau * (p + ph)))])
        rot[f'shin_{n}'] = PK.wave(dur2, 12, lambda p, ph=ph: [((1, 0, 0), fold * max(0.0, math.cos(tau * (p + ph))))])
    rot['body'] = PK.wave(dur2, 12, lambda p: [((1, 0, 0), 1.5 * math.sin(2 * tau * p))])
    rot['neck'] = PK.wave(dur2, 12, lambda p: [((1, 0, 0), 4 * math.sin(2 * tau * p + 0.6))])
    rot['head'] = PK.wave(dur2, 12, lambda p: [((1, 0, 0), -4 * math.sin(2 * tau * p + 0.6))])
    move = PK.clip(arm, 'move', rot, {'body': PK.wave(dur2, 12, lambda p: (0, 0, bob * math.cos(2 * tau * p)))})
    return [(idle, dur, 'head', 0.03), (move, dur2, 'shin_L', 0.1)]

def wand_gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0); w = x1 - x0
    G(W_HEIGHT[0] <= z1 <= W_HEIGHT[1] and z1 >= W_TALL * w, f'wanderer {z1:.2f} m high x {w:.2f} m wide (height {W_HEIGHT}, height >= {W_TALL} x width): tall and narrow')
    G(max(r for r, z in W_JAR) <= WAND_R, f'wanderer jar radius {max(r for r, z in W_JAR):.2f} m inside the game radius {WAND_R} (legs at {W_HIP[0]:.2f})')
    G(-0.02 <= z0 <= 0.01, f'wanderer feet on the ground (lowest z {z0:.3f})')
    G({BR, INL, CIN} <= K.mats(l0) and BR in K.mats(l2), f'wanderer materials {sorted(K.mats(l0))} (brass bronze, silver inlay, cinnabar)')
    G(K.tris(l0) >= TRIS_MIN, f'wanderer_lod0 tris {K.tris(l0)} (min {TRIS_MIN})')


if __name__ == '__main__':
    PK.build_rigged('crab', crab_build, crab_bones(), crab_clips, os.path.join(OUTDIR, 'crab.glb'), BUDGET, 2.6, extras={'r': CRAB_R, 'clips': 'idle,move'}, extra_gates=crab_gates)
    PK.build_rigged('wanderer', wand_build, wand_bones(), wand_clips, os.path.join(OUTDIR, 'wanderer.glb'), BUDGET, 2.2, extras={'r': WAND_R, 'clips': 'idle,move'}, extra_gates=wand_gates)
