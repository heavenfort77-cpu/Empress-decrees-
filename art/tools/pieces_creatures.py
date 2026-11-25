# Buff creatures (PIECES round 2; owner 25 Nov 13:08): the "crab" and the "wanderer" (working names). They never attack; the last hit
# takes a boon (index.html CONFIG.CRAB r 0.7 m, CONFIG.WANDERER r 0.5 m; today two flat-colour boxes each).
# Own designs from the research rule list: small bronze animal machines by animal analogy, a ding / lei vessel hull, chariot running
# gear, segmented castings with a mould-seam flange, stamp bands from the brass trim sheet and inlay lines; no patina (live).
# Round 2 (lead verdict on run 45555140630): the brass of round 1 sat at the floor's own value (body 1.2-1.4:1), so the limbs and the
# outer flanges are now black-lacquered bronze with gold inlay lines and the vessel hull stays brass: the outline is dark on the floor.
#   crab     = a low covered food vessel (the lid seam is its shell edge; ding-style relief on the lid: two raised stamp bands and a ring
#              of cast studs 乳钉; two upright ear handles; a taotie stamp plate for a mouth) carried sideways on six cast legs hung
#              from two axle rails with hub caps; two raised pincers; cast eye stalks with a gold inlay slit (no ball eyes). Low, wide.
#              Its move clip lifts the legs high in two tripods, rocks the hull and carries the pincers raised; idle keeps them low.
#   wanderer = a hu wine jar laid forward like a heron's body: the neck rises out of the jar's mouth, a long dagger bill, two stilt legs
#              hung from spoked chariot wheels, a tail of cast blades at the foot ring. Tall, narrow. The parasol of round 1 is gone (it
#              hid the neck and bill from the game camera); limbs are thick enough to hold 3 px at play size; LOD2 is built, not decimated.
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
# Thinnest limb allowed, m (3 px at the game camera: 14 m, FOV 50, 1080 px high = 1.2 cm per px).
LIMB_MIN = 0.045
# Crab hull sections (z, centre f, half width, half depth) m: belly, seam, lid; its roundness.
C_HULL = [(0.30, 0.0, 0.30, 0.20), (0.36, 0.0, 0.50, 0.31), (0.47, 0.0, 0.60, 0.385), (0.555, 0.0, 0.62, 0.40), (0.585, 0.0, 0.60, 0.385), (0.68, 0.0, 0.50, 0.31),
          (0.75, 0.0, 0.30, 0.18), (0.77, 0.0, 0.20, 0.11)]
C_N = 2.5
# Crab stamp bands by height on the hull (trim sheet rows).
C_BANDS = [(0.0, 0.46, 'plain'), (0.46, 0.555, 'clouds'), (0.555, 0.9, 'plain')]
# Crab lid relief: two raised bands (z0, z1, stamp row), how far they stand proud m; studs: count, height on the lid, size m.
C_RELIEF, C_PROUD, C_STUDS = [(0.60, 0.635, 'clouds'), (0.70, 0.728, 'lozenge')], 0.012, (16, 0.665, 0.03)
# Crab legs: f of the three hips per side; hip x and z, knee (x, z), foot x; the f spread factor at knee and foot; leg widths (thigh, shin) m.
C_LEG_F, C_HIP, C_KNEE, C_FOOT_X, C_SPREAD, C_LEG_W = (-0.27, 0.0, 0.25), (0.64, 0.45), (0.84, 0.68), 0.97, (1.25, 1.5), (0.13, 0.11)
# Crab claw: shoulder, elbow, wrist (x outward, f, z) m.
C_CLAW = [(0.48, 0.30, 0.50), (0.70, 0.50, 0.64), (0.62, 0.70, 0.80)]
# Crab size gates: width range m, most height m, width over height at least.
C_WIDTH, C_HEIGHT, C_WIDE = (1.6, 2.2), 1.2, 1.6
# Crab idle: seconds, claw raise deg, body bob m. Crab move: seconds, leg lift deg, leg swing deg, body sway m, hull rock deg, claws carried raised deg.
C_IDLE, C_MOVE = (2.4, 4.0, 0.012), (0.6, 22.0, 14.0, 0.07, 4.0, 16.0)
# The move clip must lift a leg at least this many times as far as idle moves it (they must read apart), and at least LEG_MOVE_MIN m.
C_MOVE_RATIO, LEG_MOVE_MIN = 3.0, 0.08
# Wanderer jar, upright about (0, W_CF), then laid forward by W_TILT deg about W_PIVOT: profiles (radius, z) m of its four castings.
W_LOW = [(0.0, 1.02), (0.16, 1.02), (0.185, 1.06), (0.15, 1.10), (0.30, 1.28), (0.322, 1.33)]
W_BELT = [(0.328, 1.33), (0.351, 1.44), (0.327, 1.55)]
W_UP = [(0.321, 1.55), (0.31, 1.60), (0.21, 1.74), (0.145, 1.82)]
W_LIP = [(0.148, 1.82), (0.17, 1.90), (0.175, 1.93), (0.10, 1.975), (0.0, 1.985)]
W_CF, W_TILT, W_PIVOT = -0.05, 40, (0.0, -0.05, 1.42)
# Wanderer neck: lower path and radii (bone neck), upper path and radii (bone head), m.
W_NECK, W_NECK_R = [(0.0, 0.27, 1.80), (0.0, 0.40, 1.98), (0.0, 0.43, 2.16), (0.0, 0.38, 2.34)], [0.11, 0.085, 0.07, 0.062]
W_NECK2, W_NECK2_R = [(0.0, 0.38, 2.34), (0.0, 0.40, 2.48), (0.0, 0.48, 2.56)], [0.062, 0.06, 0.065]
# Wanderer bill: base and tip (x, f, z), width and depth at the base m.
W_BILL, W_BILL_W = ((0.0, 0.63, 2.58), (0.0, 1.02, 2.40)), (0.09, 0.07)
# Wanderer legs: hip (x, f, z), hock, ankle, m; hip wheel radius and rim thickness; leg widths (thigh, shin, toe) m.
W_HIP, W_HOCK, W_ANKLE, W_WHEEL, W_LEG_W = (0.44, -0.05, 1.40), (0.44, -0.26, 0.76), (0.44, 0.0, 0.07), (0.22, 0.03), (0.16, 0.10, 0.075)
# Wanderer size gates: height range m, height over width at least.
W_HEIGHT, W_TALL = (2.2, 2.9), 2.0
# Wanderer clips: idle seconds, head look deg, head nod deg; move seconds (slow), thigh swing deg, shin fold deg, body bob m.
W_IDLE, W_MOVE = (3.2, 9.0, 6.0), (1.6, 18.0, 20.0, 0.02)
BR, INL, CIN, BLK, GOLD = 'palBronze', 'palInlay', 'palCinnabar', 'pcBlack', 'palGold'
SIDE = ((1, 'L'), (-1, 'R'))
PK.mutate(globals())


def lid_at(z):
    for a, b in zip(C_HULL, C_HULL[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k
    return C_HULL[-1][2], C_HULL[-1][3]

# ---------------------------------------------------------------------------------------------------------------- crab
def crab_build(detail):
    lv = PK.LEVEL['n']; PK.bone('body')
    loft('hull', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in C_HULL], BR, C_BANDS, n_exp=C_N, M=20)
    loft('seam', [(0.545, 0.0, 0.66, 0.44, 0.0), (0.58, 0.0, 0.66, 0.44, 0.0)], BLK, 'plain', n_exp=C_N, M=20)
    if lv < 2:  # ding-style relief on the lid: raised stamp bands, a gold inlay line on the seam
        for q, (z0, z1, row) in enumerate(C_RELIEF):
            (w0, d0), (w1, d1) = lid_at(z0), lid_at(z1)
            loft(f'relief_{q}', [(z0, 0.0, w0 + C_PROUD, d0 + C_PROUD, 0.0), (z1, 0.0, w1 + C_PROUD, d1 + C_PROUD, 0.0)], BR, row, n_exp=C_N, M=20, cap=False)
        loft('seam_inlay', [(0.556, 0.0, 0.664, 0.444, 0.0), (0.569, 0.0, 0.664, 0.444, 0.0)], GOLD, 'plain', n_exp=C_N, M=20, cap=False)
    if detail:  # a ring of cast studs between the bands
        n, z, sz = C_STUDS; w, d = lid_at(z); e = 2 / C_N
        for q in range(n):
            a = (q + 0.5) * math.tau / n; s, c = math.sin(a), math.cos(a)
            p = (w * math.copysign(abs(s) ** e, s), d * math.copysign(abs(c) ** e, c), z)
            prism(f'stud_{q}', ngon(sz, 4), (p[0] * 0.98, p[1] * 0.98, p[2] - 0.006), (p[0] * 1.03 + s * 0.012, p[1] * 1.03 + c * 0.012, p[2] + 0.03), BR, 'plain', scale_b=0.35, rnd=True)
    for q, (xa, xb) in enumerate(((-0.34, -0.13), (-0.1, 0.1), (0.13, 0.34))):  # the lid's cast crest (the mould seam), in three notched lengths
        if lv < 2 or q == 1: prism(f'crest_{q}', rect(0.04, 0.10), (xa, 0.0, 0.765 - abs(xa + xb) * 0.03), (xb, 0.0, 0.765 - abs(xa + xb) * 0.03), BLK, 'plain', rnd=False)
    if lv < 2:
        for s, n in SIDE: torus(f'ear_{n}', (s * 0.44, 0.0, 0.715), (0, 1, 0), 0.078, 0.021, BLK, 'plain', sg=(8, 4))  # upright ear handles, like a vessel's
        prism('mask', rect(0.38, 0.13), (0.0, 0.375, 0.465), (0.0, 0.415, 0.465), BR, 'mask', rnd=False)
    for s, n in SIDE:
        # cast eye stalks: a faceted stem, a hexagonal housing, a gold inlay slit (no ball eyes)
        prism(f'stalk_{n}', ngon(0.042, 6), (s * 0.20, 0.33, 0.62), (s * 0.25, 0.47, 0.93), BLK, 'plain', scale_b=0.8, rnd=True)
        if lv < 2: prism(f'eye_{n}', ngon(0.058, 6), (s * 0.25, 0.465, 0.925), (s * 0.262, 0.50, 1.0), BR, 'mark', rnd=True)
        if lv < 2: prism(f'slit_{n}', rect(0.014, 0.02), (s * 0.256 - 0.04, 0.542, 0.972), (s * 0.256 + 0.04, 0.542, 0.972), GOLD, 'plain', rnd=True)
        # axle rail along the hull side with a hub cap at each end: the legs hang from it (chariot running gear)
        if lv < 2: prism(f'rail_{n}', ngon(0.045, 6), (s * 0.63, -0.34, 0.45), (s * 0.63, 0.32, 0.45), BLK, 'plain', rnd=True)
        if lv < 2:
            for q, f in enumerate((-0.37, 0.31)): prism(f'hub_{n}{q}', ngon(0.08, 8), (s * 0.63, f, 0.45), (s * 0.63, f + 0.045, 0.45), BR, 'mark', rnd=True)
    for s, n in SIDE:
        for i, f in enumerate(C_LEG_F):
            PK.bone(f'leg_{n}{i}')
            hip = (s * C_HIP[0], f, C_HIP[1]); knee = (s * C_KNEE[0], f * C_SPREAD[0], C_KNEE[1]); foot = (s * C_FOOT_X, f * C_SPREAD[1], 0.0)
            prism(f'femur_{n}{i}', blade(C_LEG_W[0], 0.09), hip, knee, BLK, 'plain', scale_b=0.85, rnd=False, up=(0, 0, 1))
            prism(f'tibia_{n}{i}', blade(C_LEG_W[1], 0.08), knee, foot, BLK, 'plain', scale_b=0.2, rnd=False, up=(s, 0, 0.35))
            if lv < 2: prism(f'knee_{n}{i}', ngon(0.062, 6), (knee[0], knee[1] - 0.06, knee[2]), (knee[0], knee[1] + 0.06, knee[2]), BR, 'lozenge', rnd=True)
            if detail: prism(f'leg_inlay_{n}{i}', rect(0.024, 0.012), (hip[0] + s * 0.03, hip[1], hip[2] + 0.066), (knee[0] - s * 0.03, knee[1], knee[2] + 0.05), GOLD, 'plain', rnd=True, up=(0, 0, 1))
    for s, n in SIDE:
        PK.bone(f'claw_{n}')
        sh, el, wr = [(s * x, f, z) for x, f, z in C_CLAW]
        prism(f'arm_{n}', ngon(0.065, 6), sh, el, BLK, 'plain', rnd=True)
        if lv < 2: prism(f'elbow_{n}', ngon(0.075, 6), (el[0] - s * 0.05, el[1] - 0.03, el[2] + 0.03), (el[0] + s * 0.05, el[1] + 0.03, el[2] - 0.03), BR, 'lozenge', rnd=True)
        prism(f'fore_{n}', ngon(0.065, 6), el, wr, BLK, 'plain', scale_b=1.35, rnd=True)
        spheroid(f'palm_{n}', (s * 0.60, 0.745, 0.835), (0.105, 0.115, 0.095), BLK, 'plain', sg=(8, 5))
        sweep(f'finger_up_{n}', [(s * 0.60, 0.78, 0.885), (s * 0.50, 0.92, 0.99), (s * 0.36, 0.97, 1.0)], [0.078, 0.058, 0.0], BLK, 'plain', n=4, flat=(1.0, 0.5), side=(0, 0, 1))
        if lv < 2: sweep(f'finger_lo_{n}', [(s * 0.60, 0.80, 0.80), (s * 0.50, 0.93, 0.845), (s * 0.375, 0.97, 0.905)], [0.058, 0.046, 0.0], BLK, 'plain', n=4, flat=(1.0, 0.5), side=(0, 0, 1))
        if detail: prism(f'claw_inlay_{n}', rect(0.02, 0.012), (el[0] + s * 0.0, el[1] + 0.04, el[2] + 0.1), (wr[0], wr[1] - 0.03, wr[2] + 0.085), GOLD, 'plain', rnd=True, up=(0, 0, 1))
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
    for s, n in SIDE:  # legs barely shift in idle (a small settle), so the move clip reads apart from it
        for i in range(3): rot[f'leg_{n}{i}'] = PK.wave(dur, 8, lambda p, s=s, i=i: [((0, 1, 0), s * 1.2 * math.sin(tau * p + i))])
    idle = PK.clip(arm, 'idle', rot, {'body': PK.wave(dur, 8, lambda p: (0, 0, bob * math.sin(tau * p)))})
    dur2, lift, swing, sway, rock, carry = C_MOVE; rot = {}
    for s, n in SIDE:
        for i in range(3):
            ph = 0.0 if (i + (s > 0)) % 2 == 0 else 0.5  # two tripods: L0 R1 L2 against R0 L1 R2
            rot[f'leg_{n}{i}'] = PK.wave(dur2, 12, lambda p, s=s, ph=ph: [((0, 1, 0), s * lift * max(0.0, math.sin(tau * (p + ph)))), ((0, 0, 1), swing * math.cos(tau * (p + ph)))])
        rot[f'claw_{n}'] = PK.wave(dur2, 12, lambda p, s=s: [((1, 0, 0), -carry - 5 * math.sin(2 * tau * p + s)), ((0, 0, 1), s * 8.0)])
    rot['body'] = PK.wave(dur2, 12, lambda p: [((0, 1, 0), rock * math.sin(tau * p))])
    move = PK.clip(arm, 'move', rot, {'body': PK.wave(dur2, 12, lambda p: (sway * math.sin(tau * p), 0, 0.03 * abs(math.sin(tau * p))))})
    return [(idle, dur, 'claw_L', 0.02), (move, dur2, 'leg_L0', LEG_MOVE_MIN)]

def crab_gates(G, l0, l1, l2, arm):
    (x0, x1), (y0, y1), (z0, z1) = K.bounds(l0); w = x1 - x0
    G(C_WIDTH[0] <= w <= C_WIDTH[1] and z1 <= C_HEIGHT and w >= C_WIDE * z1, f'crab {w:.2f} m wide x {z1:.2f} m high (width {C_WIDTH}, height <= {C_HEIGHT}, width >= {C_WIDE} x height): low and wide')
    G(max(h[2] for h in C_HULL) <= CRAB_R + 0.01, f'crab hull half width {max(h[2] for h in C_HULL):.2f} m inside the game radius {CRAB_R} (legs reach {w / 2:.2f})')
    G(-0.02 <= z0 <= 0.01, f'crab feet on the ground (lowest z {z0:.3f})')
    G({BR, BLK, GOLD} <= K.mats(l0) and {BR, BLK} <= K.mats(l2) and 'palDark' not in K.mats(l0), f'crab materials {sorted(K.mats(l0))} (brass hull, black-lacquered limbs, gold inlay; no ball eyes)')
    G(K.tris(l0) >= TRIS_MIN, f'crab_lod0 tris {K.tris(l0)} (min {TRIS_MIN})')
    G(len(C_RELIEF) >= 2 and C_STUDS[0] >= 12 and C_PROUD >= 0.01, f'crab lid relief: {len(C_RELIEF)} raised bands ({C_PROUD * 100:.1f} cm proud), {C_STUDS[0]} cast studs')
    # move against idle: the same leg, measured in the hull's space, before the clips are pushed
    acts = {a.name: a for a in __import__('bpy').data.actions}; mi = PK.motion(arm, acts['idle'], 'leg_L0', C_IDLE[0]); mm = PK.motion(arm, acts['move'], 'leg_L0', C_MOVE[0])
    G(mm >= C_MOVE_RATIO * max(mi, 1e-4), f'crab move reads apart from idle: a leg travels {mm:.3f} m in move against {mi:.3f} m in idle (at least {C_MOVE_RATIO} x)')
    G(min(C_LEG_W) >= LIMB_MIN, f'crab legs {min(C_LEG_W) * 100:.0f} cm wide (min {LIMB_MIN * 100:.1f} cm = 3 px at play size)')


# ------------------------------------------------------------------------------------------------------------ wanderer
def wand_build(detail):
    lv = PK.LEVEL['n']; PK.bone('body')
    n0 = len(K.PARTS)
    lathe('jar_low', W_LOW, BLK, 'plain', n=20, cf=W_CF)
    lathe('jar_belt', W_BELT, BR, 'clouds', n=20, cf=W_CF)
    lathe('jar_up', W_UP, BLK, 'plain', n=20, cf=W_CF)
    lathe('jar_lip', W_LIP, BR, 'flange', n=20, cf=W_CF)
    if lv < 2:
        lathe('jar_inlay', [(0.331, 1.546), (0.331, 1.562)], INL, 'plain', n=20, cf=W_CF)
        lathe('jar_inlay2', [(0.331, 1.318), (0.331, 1.334)], INL, 'plain', n=20, cf=W_CF)
    jar = [p[0] for p in K.PARTS[n0:]]; PK.pre_uv(jar); PK.tilt(jar, W_PIVOT, (1, 0, 0), W_TILT)
    for k in ((-2, -1, 0, 1, 2) if detail else (-1, 0, 1) if lv == 1 else (0,)):  # tail: cast blades at the jar's foot ring
        prism(f'tail_{k}', blade(0.12, 0.035), (k * 0.06, -0.30, 1.13), (k * 0.17, -0.66 + abs(k) * 0.05, 0.93 + abs(k) * 0.03), BLK, 'plain', scale_b=0.2, rnd=False, up=(0, 0, 1))
    for s, n in SIDE:  # hip wheels: spoked chariot wheels the legs hang from
        c = (s * (W_HIP[0] - 0.045), W_HIP[1], W_HIP[2])
        if lv < 2: torus(f'wheel_{n}', c, (1, 0, 0), W_WHEEL[0], W_WHEEL[1], BLK, 'plain', sg=(12, 4))
        spheroid(f'nave_{n}', c, (0.06, 0.075, 0.075), BR, 'lozenge', sg=(8, 5))
        if lv < 2: prism(f'axle_cap_{n}', ngon(0.04, 6), c, (c[0] + s * 0.11, c[1], c[2]), BR, 'mark', rnd=True)
        if detail:
            for q in range(8):
                a = q * math.tau / 8 + 0.3
                prism(f'spoke_{n}{q}', rect(0.026, 0.026), c, (c[0], c[1] + math.cos(a) * W_WHEEL[0], c[2] + math.sin(a) * W_WHEEL[0]), BR, 'plain', rnd=True, up=(1, 0, 0))
    # neck in two cast lengths rising from the jar's mouth, a silver collar at the mouth, a brass ring at the joint
    if lv < 2: torus('mouth_ring', (0.0, 0.30, 1.84), (0, 0.64, 0.77), 0.13, 0.028, INL, 'plain', sg=(10, 4))
    PK.bone('neck')
    sweep('neck', W_NECK, W_NECK_R, BLK, 'plain', n=8)
    if lv < 2: torus('neck_ring', W_NECK[-1], (0, -0.1, 1), 0.068, 0.022, BR, 'flange', sg=(8, 4))
    PK.bone('head')
    sweep('neck2', W_NECK2, W_NECK2_R, BLK, 'plain', n=8)
    spheroid('head', (0.0, 0.55, 2.585), (0.075, 0.12, 0.08), BLK, 'plain', sg=(8, 5))
    prism('bill', blade(W_BILL_W[0], W_BILL_W[1]), W_BILL[0], W_BILL[1], BLK, 'plain', scale_b=0.1, rnd=False, up=(0, 0, 1))
    prism('crest', blade(0.08, 0.03), (0.0, 0.50, 2.65), (0.0, 0.22, 2.81), CIN, 'plain', scale_b=0.2, rnd=True, up=(0, 0, 1))
    if detail:
        prism('bill_inlay', rect(0.016, 0.012), (0.0, 0.64, 2.618), (0.0, 0.93, 2.47), GOLD, 'plain', rnd=True, up=(0, 0, 1))
        for s, n in SIDE: prism(f'eye_{n}', rect(0.012, 0.018), (s * 0.068, 0.57, 2.60), (s * 0.068, 0.63, 2.598), GOLD, 'plain', rnd=True, up=(s, 0, 0))
    for s, n in SIDE:
        hip, hock, ank = [(s * x, f, z) for x, f, z in (W_HIP, W_HOCK, W_ANKLE)]
        PK.bone(f'thigh_{n}')
        prism(f'thigh_{n}', blade(W_LEG_W[0], 0.12), hip, hock, BLK, 'plain', scale_b=0.6, rnd=False, up=(0, -1, 0))
        if detail: prism(f'thigh_inlay_{n}', rect(0.022, 0.012), (hip[0] + s * 0.045, hip[1] - 0.06, hip[2] - 0.12), (hock[0] + s * 0.03, hock[1] - 0.005, hock[2] + 0.1), GOLD, 'plain', rnd=True, up=(s, 0, 0))
        PK.bone(f'shin_{n}')
        if lv < 2: prism(f'hock_{n}', ngon(0.07, 6), (hock[0] - 0.06, hock[1], hock[2]), (hock[0] + 0.06, hock[1], hock[2]), BR, 'lozenge', rnd=True)
        prism(f'shin_{n}', blade(W_LEG_W[1], 0.085), hock, ank, BLK, 'plain', scale_b=0.85, rnd=False, up=(0, 1, 0))
        toes = ((-0.13, 0.27), (0.0, 0.31), (0.13, 0.27), (0.0, -0.16)) if lv < 2 else ((0.0, 0.31),)
        for q, (dx, df) in enumerate(toes):
            prism(f'toe_{n}{q}', blade(W_LEG_W[2], 0.045), (ank[0], ank[1], 0.04), (ank[0] + dx, ank[1] + df, 0.006), BLK, 'plain', scale_b=0.2, rnd=False, up=(0, 0, 1))
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
    rj = max(r for r, z in W_LOW + W_BELT + W_UP + W_LIP); G(rj <= WAND_R, f'wanderer jar radius {rj:.2f} m inside the game radius {WAND_R} (legs at {W_HIP[0]:.2f})')
    G(-0.02 <= z0 <= 0.01, f'wanderer feet on the ground (lowest z {z0:.3f})')
    G({BR, BLK, INL, CIN} <= K.mats(l0) and {BR, BLK} <= K.mats(l2), f'wanderer materials {sorted(K.mats(l0))} (black-lacquered limbs and jar, brass belt and lip, silver inlay, cinnabar crest)')
    G(K.tris(l0) >= TRIS_MIN, f'wanderer_lod0 tris {K.tris(l0)} (min {TRIS_MIN})')
    thin = min(min(W_LEG_W), 2 * min(W_NECK_R + W_NECK2_R), W_BILL_W[0])
    G(thin >= LIMB_MIN, f'wanderer limbs: thinnest of legs, neck and bill base {thin * 100:.1f} cm (min {LIMB_MIN * 100:.1f} cm = 3 px at play size)')
    # LOD2 keeps the legs: its lowest point is the feet, and it is as tall as LOD0
    (_, _), (_, _), (a0, a1) = K.bounds(l2); (_, _), (_, _), (b0, b1) = K.bounds(l1)
    G(a0 <= 0.03 and b0 <= 0.03 and a1 >= z1 - 0.15, f'wanderer LOD1 and LOD2 keep the legs and the head: lowest z {b0:.3f} / {a0:.3f}, LOD2 top {a1:.2f} m (LOD0 {z1:.2f})')
    top = max(v.co.z for v in l0.data.vertices if abs(v.co.x) < 0.3 and -0.6 < -v.co.y < 0.15 and v.co.z > 2.0) if any(abs(v.co.x) < 0.3 and -0.6 < -v.co.y < 0.15 and v.co.z > 2.0 for v in l0.data.vertices) else 0.0
    G(top == 0.0, f'wanderer: nothing over the back above 2.0 m (the parasol is gone; found {top:.2f}): the neck and bill read from the game camera')


if __name__ == '__main__':
    PK.build_rigged('crab', crab_build, crab_bones(), crab_clips, os.path.join(OUTDIR, 'crab.glb'), BUDGET, 2.6, extras={'r': CRAB_R, 'clips': 'idle,move'}, extra_gates=crab_gates)
    PK.build_rigged('wanderer', wand_build, wand_bones(), wand_clips, os.path.join(OUTDIR, 'wanderer.glb'), BUDGET, 2.2, extras={'r': WAND_R, 'clips': 'idle,move'}, extra_gates=wand_gates)
