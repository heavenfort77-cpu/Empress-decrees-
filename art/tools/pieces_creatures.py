# Buff creatures (PIECES round 4; owner 25 Nov 13:08 and 14:13 "fix them"): the "crab" and the "wanderer" (working names). They never
# attack; the last hit takes a boon (index.html CONFIG.CRAB r 0.7 m, CONFIG.WANDERER r 0.5 m; today two flat-colour boxes each).
# Own designs from the research rule list: small bronze animal machines by animal analogy, a ding / lei vessel hull, chariot running
# gear, segmented castings with a mould-seam flange, stamp bands from the brass trim sheet and inlay lines; no patina (live).
# Round 4 (lead after run 45560766962): bronze, bright like the 鼎: the bodies are brass, dark bronze only on the underside, joints
# and feet. No outline is baked in (round 3's inside-out shell is removed): they are characters, so the game's own renderer outline
# (src/chars.js CHR.outline, 2 px) draws their dark edge; the review viewer simulates that outline with the same shader.
#   crab     = a low covered food vessel (the lid seam is its shell edge; ding-style relief on the lid: two raised stamp bands and a ring
#              of cast studs 乳钉; two upright ear handles; a taotie stamp plate for a mouth) carried sideways on six cast legs hung
#              from two axle rails with hub caps; two raised pincers, each two broad flat fingers open in a V that reads from above;
#              short cast eye stalks with narrow slit inlays (no discs). Low, wide. Move lifts the legs in two tripods and rocks the hull; idle is still.
#   wanderer = a heron-machine: a hu wine jar laid forward for a body (brass, relief bands, a dark underside), the neck rising from the
#              jar's mouth in a deep S, a long dagger bill, two stilt legs hung from cambered spoked chariot wheels set low so the big
#              vessel shows above them, a tail of cast blades. Tall, narrow.
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
# Least share of a creature's surface that is brass: bronze machines, dark only in joints and underside.
BRASS_MIN = 0.55
# Crab hull sections (z, centre f, half width, half depth) m: belly (dark underside) up to C_BELLY_Z, then seam and lid; roundness.
C_HULL = [(0.30, 0.0, 0.30, 0.20), (0.36, 0.0, 0.50, 0.31), (0.47, 0.0, 0.60, 0.385), (0.555, 0.0, 0.62, 0.40), (0.585, 0.0, 0.60, 0.385), (0.68, 0.0, 0.50, 0.31),
          (0.75, 0.0, 0.30, 0.18), (0.77, 0.0, 0.20, 0.11)]
C_N, C_BELLY_Z = 2.5, 0.36
# Crab stamp bands by height on the hull (trim sheet rows).
C_BANDS = [(0.0, 0.47, 'plain'), (0.47, 0.555, 'clouds'), (0.555, 0.9, 'plain')]
# Crab lid relief: two raised bands (z0, z1, stamp row), how far they stand proud m; studs: count, height on the lid, size m.
C_RELIEF, C_PROUD, C_STUDS = [(0.60, 0.635, 'clouds'), (0.70, 0.728, 'lozenge')], 0.012, (12, 0.665, 0.032)
# Crab legs: f of the three hips per side; hip x and z, knee (x, z), foot x; the f spread factor at knee and foot; leg widths (thigh, shin) m.
C_LEG_F, C_HIP, C_KNEE, C_FOOT_X, C_SPREAD, C_LEG_W = (-0.27, 0.0, 0.25), (0.64, 0.45), (0.84, 0.68), 0.97, (1.25, 1.5), (0.13, 0.075)
# Crab claw: shoulder, elbow, wrist (x outward, f, z) m.
C_CLAW = [(0.48, 0.30, 0.50), (0.70, 0.50, 0.64), (0.62, 0.70, 0.80)]
# Crab pincer: the two fingers as paths (x outward, f, z) with half widths m: broad and flat, open in a V seen from above.
C_FINGER_A, C_FINGER_A_R = [(0.63, 0.78, 0.83), (0.62, 0.96, 0.85), (0.50, 1.10, 0.83)], [0.085, 0.07, 0.0]
C_FINGER_B, C_FINGER_B_R = [(0.58, 0.78, 0.81), (0.46, 0.90, 0.81), (0.34, 0.97, 0.80)], [0.07, 0.055, 0.0]
# Pincer gates: least gap between the two finger tips m, least finger half width m.
C_GAP_MIN, C_FINGER_MIN = 0.12, 0.05
# Crab size gates: width range m, most height m, width over height at least.
C_WIDTH, C_HEIGHT, C_WIDE = (1.6, 2.2), 1.2, 1.6
# Crab idle: seconds, claw raise deg, body bob m. Crab move: seconds, leg lift deg, leg swing deg, body sway m, hull rock deg, claws carried raised deg.
C_IDLE, C_MOVE = (2.4, 4.0, 0.012), (0.6, 22.0, 14.0, 0.07, 4.0, 16.0)
# The move clip must lift a leg at least this many times as far as idle moves it (they must read apart), and at least LEG_MOVE_MIN m.
C_MOVE_RATIO, LEG_MOVE_MIN = 3.0, 0.08
# Wanderer jar, upright about (0, W_CF), then laid forward by W_TILT deg about W_PIVOT: profiles (radius, z) m of its castings
# (round 4: 1.2 x wider and 1.15 x longer, so the vessel reads from the game camera).
W_FOOT = [(0.0, 0.96), (0.192, 0.96), (0.222, 1.006), (0.18, 1.052)]
W_LOW = [(0.18, 1.052), (0.36, 1.259), (0.386, 1.3165)]
W_BELT = [(0.396, 1.3165), (0.425, 1.443), (0.396, 1.5695)]
W_UP = [(0.385, 1.5695), (0.372, 1.627), (0.252, 1.788), (0.174, 1.88)]
W_BAND2 = [(0.355, 1.6615), (0.314, 1.7305)]
W_LIP = [(0.178, 1.88), (0.204, 1.972), (0.21, 2.0065), (0.12, 2.058), (0.0, 2.07)]
W_CF, W_TILT, W_PIVOT = -0.05, 40, (0.0, -0.05, 1.42)
# Wanderer neck: lower path and radii (bone neck), upper path and radii (bone head), m: a deep S.
W_NECK, W_NECK_R = [(0.0, 0.325, 1.865), (0.0, 0.555, 2.025), (0.0, 0.575, 2.245), (0.0, 0.415, 2.425)], [0.11, 0.085, 0.07, 0.062]
W_NECK2, W_NECK2_R = [(0.0, 0.415, 2.425), (0.0, 0.415, 2.565), (0.0, 0.515, 2.645)], [0.062, 0.06, 0.065]
# Wanderer head centre (x, f, z) m.
W_HEAD = (0.0, 0.575, 2.665)
# Wanderer bill: base and tip (x, f, z), width and depth at the base m; least length m (it must read in every facing).
W_BILL, W_BILL_W, W_BILL_MIN = ((0.0, 0.635, 2.65), (0.0, 1.115, 2.385)), (0.10, 0.075), 0.45
# Wanderer legs: hip (x, f, z), hock, ankle, m; leg widths (thigh, shin, toe) m.
W_HIP, W_HOCK, W_ANKLE, W_LEG_W = (0.56, -0.05, 1.28), (0.56, -0.26, 0.70), (0.56, 0.0, 0.07), (0.16, 0.10, 0.075)
# Wanderer hip wheels: centre x, radius, rim thickness, camber deg (the top leans in, so the face shows from above), spokes, hub cap length, m.
W_WHEEL = (0.47, 0.22, 0.035, 15, 6, 0.14)
# Vessel gate: the jar's widest diameter over the wheel's diameter, at least (the body must show over its running gear).
W_BODY_OVER_WHEEL = 1.6
# Wanderer size gates: height range m, height over width at least.
W_HEIGHT, W_TALL = (2.2, 2.9), 2.0
# Wanderer clips: idle seconds, head look deg, head nod deg; move seconds (slow), thigh swing deg, shin fold deg, body bob m.
W_IDLE, W_MOVE = (3.2, 9.0, 6.0), (1.6, 18.0, 20.0, 0.02)
BR, INL, CIN, DK, GOLD = 'palBronze', 'palInlay', 'palCinnabar', 'pcDarkBronze', 'palGold'
SIDE = ((1, 'L'), (-1, 'R'))
PK.mutate(globals())


def lid_at(z):
    for a, b in zip(C_HULL, C_HULL[1:]):
        if a[0] <= z <= b[0]:
            k = (z - a[0]) / (b[0] - a[0]); return a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k
    return C_HULL[-1][2], C_HULL[-1][3]

def brass_share(ob):
    """share of the piece's surface area in brass."""
    names = [m.name for m in ob.data.materials]; a = {}
    for p in ob.data.polygons: a[names[p.material_index]] = a.get(names[p.material_index], 0.0) + p.area
    own = sum(a.values())
    return a.get(BR, 0.0) / max(own, 1e-9)

# ---------------------------------------------------------------------------------------------------------------- crab
def crab_build(detail):
    lv = PK.LEVEL['n']; PK.bone('body')
    belly = [h for h in C_HULL if h[0] <= C_BELLY_Z]; top = [h for h in C_HULL if h[0] >= C_BELLY_Z]
    loft('belly', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in belly], DK, 'plain', n_exp=C_N, M=18)
    loft('hull', [(z, cf, hw, hd, 0.0) for z, cf, hw, hd in top], BR, C_BANDS, n_exp=C_N, M=18)
    loft('seam', [(0.545, 0.0, 0.66, 0.44, 0.0), (0.58, 0.0, 0.66, 0.44, 0.0)], BR, 'flange', n_exp=C_N, M=18)
    if lv < 2:  # ding-style relief on the lid: raised stamp bands
        for q, (z0, z1, row) in enumerate(C_RELIEF):
            (w0, d0), (w1, d1) = lid_at(z0), lid_at(z1)
            loft(f'relief_{q}', [(z0, 0.0, w0 + C_PROUD, d0 + C_PROUD, 0.0), (z1, 0.0, w1 + C_PROUD, d1 + C_PROUD, 0.0)], BR, row, n_exp=C_N, M=18, cap=False)
    if detail:  # a ring of cast studs between the bands
        n, z, sz = C_STUDS; w, d = lid_at(z); e = 2 / C_N
        for q in range(n):
            a = (q + 0.5) * math.tau / n; s, c = math.sin(a), math.cos(a)
            p = (w * math.copysign(abs(s) ** e, s), d * math.copysign(abs(c) ** e, c), z)
            prism(f'stud_{q}', ngon(sz, 3), (p[0] * 0.98, p[1] * 0.98, p[2] - 0.006), (p[0] * 1.03 + s * 0.012, p[1] * 1.03 + c * 0.012, p[2] + 0.03), BR, 'plain', scale_b=0.35, rnd=True)
    for q, (xa, xb) in enumerate(((-0.34, -0.13), (-0.1, 0.1), (0.13, 0.34))):  # the lid's cast crest (the mould seam), in three notched lengths
        if lv < 2: prism(f'crest_{q}', rect(0.04, 0.10), (xa, 0.0, 0.765 - abs(xa + xb) * 0.03), (xb, 0.0, 0.765 - abs(xa + xb) * 0.03), BR, 'flange', rnd=True)
    if lv < 2:
        for s, n in SIDE: torus(f'ear_{n}', (s * 0.44, 0.0, 0.715), (0, 1, 0), 0.078, 0.021, BR, 'flange', sg=(8, 4))  # upright ear handles, like a vessel's
        prism('mask', rect(0.38, 0.13), (0.0, 0.375, 0.465), (0.0, 0.415, 0.465), BR, 'mask', rnd=False)
    for s, n in SIDE:
        # short cast eye stalks: a faceted stem, a small hexagonal housing, a narrow silver slit inlaid across its face (no discs)
        if lv < 2:
            prism(f'stalk_{n}', ngon(0.04, 6), (s * 0.20, 0.33, 0.62), (s * 0.235, 0.43, 0.84), BR, 'flange', scale_b=0.85, rnd=True)
            prism(f'eye_house_{n}', ngon(0.05, 6), (s * 0.235, 0.43, 0.835), (s * 0.243, 0.455, 0.895), BR, 'mark', rnd=True)
            prism(f'slit_{n}', rect(0.014, 0.012), (s * 0.24 - 0.036, 0.494, 0.872), (s * 0.24 + 0.036, 0.494, 0.872), INL, 'plain', rnd=True)
        # axle rail along the hull side with a hub cap at each end: the legs hang from it (chariot running gear)
        if lv < 2: prism(f'rail_{n}', ngon(0.045, 6), (s * 0.63, -0.34, 0.45), (s * 0.63, 0.32, 0.45), BR, 'flange', rnd=True)
        if lv < 2:
            for q, f in enumerate((-0.37, 0.31)): prism(f'hub_{n}{q}', ngon(0.08, 8), (s * 0.63, f, 0.45), (s * 0.63, f + 0.045, 0.45), BR, 'mark', rnd=True)
    for s, n in SIDE:
        for i, f in enumerate(C_LEG_F):
            PK.bone(f'leg_{n}{i}')
            hip = (s * C_HIP[0], f, C_HIP[1]); knee = (s * C_KNEE[0], f * C_SPREAD[0], C_KNEE[1]); foot = (s * C_FOOT_X, f * C_SPREAD[1], 0.0)
            prism(f'femur_{n}{i}', blade(C_LEG_W[0], 0.09), hip, knee, BR, 'plain', scale_b=0.85, rnd=False, up=(0, 0, 1))
            prism(f'tibia_{n}{i}', blade(C_LEG_W[1], 0.06), knee, foot, DK, 'plain', scale_b=0.25, rnd=False, up=(s, 0, 0.35))
            if lv < 2: prism(f'knee_{n}{i}', ngon(0.064, 6), (knee[0], knee[1] - 0.06, knee[2]), (knee[0], knee[1] + 0.06, knee[2]), DK, 'plain', rnd=True)
    for s, n in SIDE:
        PK.bone(f'claw_{n}')
        sh, el, wr = [(s * x, f, z) for x, f, z in C_CLAW]
        prism(f'arm_{n}', ngon(0.065, 6), sh, el, BR, 'plain', rnd=True)
        prism(f'fore_{n}', ngon(0.065, 6), el, wr, BR, 'lozenge', scale_b=1.35, rnd=True)
        spheroid(f'palm_{n}', (s * 0.61, 0.745, 0.825), (0.105, 0.10, 0.08), BR, 'plain', sg=(8, 5))
        sweep(f'finger_a_{n}', [(s * x, f, z) for x, f, z in C_FINGER_A], C_FINGER_A_R, BR, 'flange', n=4, flat=(1.0, 0.5), side=(1, 0, 0))
        sweep(f'finger_b_{n}', [(s * x, f, z) for x, f, z in C_FINGER_B], C_FINGER_B_R, BR, 'flange', n=4, flat=(1.0, 0.5), side=(1, 0, 0))
        if lv < 2:
            prism(f'elbow_{n}', ngon(0.078, 6), (el[0] - s * 0.05, el[1] - 0.03, el[2] + 0.03), (el[0] + s * 0.05, el[1] + 0.03, el[2] - 0.03), DK, 'plain', rnd=True)
            prism(f'hinge_{n}', ngon(0.05, 6), (s * 0.60, 0.775, 0.77), (s * 0.60, 0.775, 0.89), DK, 'plain', rnd=True)
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
    m = K.mats(l0); sh = brass_share(l0)
    G({BR, DK, INL} <= m and not ({'pcBlack', 'pcOutline'} & m) and sh >= BRASS_MIN, f'crab is bronze: {sh:.0%} of its surface brass (min {BRASS_MIN:.0%}), dark bronze on the underside, joints and feet, no black and no baked outline; materials {sorted(m)}')
    G(K.tris(l0) >= TRIS_MIN, f'crab_lod0 tris {K.tris(l0)} (min {TRIS_MIN})')
    G(len(C_RELIEF) >= 2 and C_STUDS[0] >= 12 and C_PROUD >= 0.01, f'crab lid relief: {len(C_RELIEF)} raised bands ({C_PROUD * 100:.1f} cm proud), {C_STUDS[0]} cast studs')
    gap = math.dist(C_FINGER_A[-1], C_FINGER_B[-1]); fw = min(C_FINGER_A_R[0], C_FINGER_B_R[0])
    G(gap >= C_GAP_MIN and fw >= C_FINGER_MIN, f'crab pincers: two fingers each, tips {gap:.2f} m apart (min {C_GAP_MIN}), fingers {2 * fw * 100:.0f} cm broad at the root (min {2 * C_FINGER_MIN * 100:.0f} cm)')
    acts = {a.name: a for a in __import__('bpy').data.actions}; mi = PK.motion(arm, acts['idle'], 'leg_L0', C_IDLE[0]); mm = PK.motion(arm, acts['move'], 'leg_L0', C_MOVE[0])
    G(mm >= C_MOVE_RATIO * max(mi, 1e-4), f'crab move reads apart from idle: a leg travels {mm:.3f} m in move against {mi:.3f} m in idle (at least {C_MOVE_RATIO} x)')
    G(min(C_LEG_W) >= LIMB_MIN, f'crab legs {min(C_LEG_W) * 100:.0f} cm wide (min {LIMB_MIN * 100:.1f} cm = 3 px at play size)')
    G(C_LEG_W[1] <= 0.08, f'crab lower legs slim: {C_LEG_W[1] * 100:.1f} cm (max 8 cm)')


# ------------------------------------------------------------------------------------------------------------ wanderer
def wheel_frame(s):
    c = (s * W_WHEEL[0], W_HIP[1], W_HIP[2]); a = math.radians(W_WHEEL[3]); n = (s * math.cos(a), 0.0, math.sin(a)); e2 = (-math.sin(a), 0.0, s * math.cos(a))
    return c, n, e2

def wand_build(detail):
    lv = PK.LEVEL['n']; PK.bone('body')
    n0 = len(K.PARTS)
    lathe('jar_foot', W_FOOT, DK, 'plain', n=16, cf=W_CF)
    lathe('jar_low', W_LOW, BR, 'plain', n=16, cf=W_CF)
    lathe('jar_belt', W_BELT, BR, 'clouds', n=16, cf=W_CF)
    lathe('jar_up', W_UP, BR, 'plain', n=16, cf=W_CF)
    lathe('jar_lip', W_LIP, BR, 'flange', n=16, cf=W_CF)
    if lv < 2:
        lathe('jar_band2', W_BAND2, BR, 'lozenge', n=16, cf=W_CF)
        lathe('jar_inlay', [(0.401, 1.563), (0.401, 1.579)], INL, 'plain', n=16, cf=W_CF)
        lathe('jar_inlay2', [(0.401, 1.303), (0.401, 1.319)], INL, 'plain', n=16, cf=W_CF)
    jar = [p[0] for p in K.PARTS[n0:]]; PK.pre_uv(jar); PK.tilt(jar, W_PIVOT, (1, 0, 0), W_TILT)
    for k in ((-1, 0, 1) if lv < 2 else (0,)):  # tail: cast blades at the jar's foot ring
        prism(f'tail_{k}', blade(0.14, 0.035), (k * 0.08, -0.34, 1.09), (k * 0.22, -0.72 + abs(k) * 0.05, 0.89 + abs(k) * 0.03), BR, 'flange', scale_b=0.2, rnd=True, up=(0, 0, 1))
    for s, n in SIDE:  # hip wheels: large spoked chariot wheels, cambered so their face shows from above, long hub caps
        c, ax, e2 = wheel_frame(s); R, rim, _, spokes, cap = W_WHEEL[1], W_WHEEL[2], W_WHEEL[3], W_WHEEL[4], W_WHEEL[5]
        if lv < 2: torus(f'wheel_{n}', c, ax, R, rim, BR, 'flange', sg=(14, 4))
        spheroid(f'nave_{n}', c, (0.07, 0.085, 0.085), DK, 'plain', sg=(8, 5))
        if lv < 2:
            e = tuple(c[i] + ax[i] * cap for i in range(3))
            prism(f'axle_cap_{n}', ngon(0.045, 6), c, e, BR, 'mark', scale_b=0.8, rnd=True)
            prism(f'linch_{n}', ngon(0.07, 8), tuple(c[i] + ax[i] * (cap - 0.03) for i in range(3)), e, BR, 'flange', rnd=True)
        if detail:
            for q in range(spokes):
                a = q * math.tau / spokes + 0.3; ca, sa = math.cos(a), math.sin(a)
                prism(f'spoke_{n}{q}', rect(0.035, 0.035), c, (c[0] + e2[0] * sa * R, c[1] + ca * R, c[2] + e2[2] * sa * R), BR, 'plain', rnd=True, up=ax)
    # neck in two cast lengths rising from the jar's mouth in a deep S, a silver collar at the mouth, a dark ring at the joint
    if lv < 2: torus('mouth_ring', (0.0, 0.345, 1.895), (0, 0.64, 0.77), 0.15, 0.03, INL, 'plain', sg=(10, 4))
    PK.bone('neck')
    sweep('neck', W_NECK, W_NECK_R, BR, 'plain', n=8)
    if lv < 2: torus('neck_ring', W_NECK[-1], (0, -0.1, 1), 0.068, 0.022, DK, 'plain', sg=(8, 4))
    PK.bone('head')
    sweep('neck2', W_NECK2, W_NECK2_R, BR, 'plain', n=8)
    spheroid('head', W_HEAD, (0.075, 0.12, 0.08), BR, 'plain', sg=(8, 5))
    prism('bill', blade(W_BILL_W[0], W_BILL_W[1]), W_BILL[0], W_BILL[1], BR, 'flange', scale_b=0.1, rnd=False, up=(0, 0, 1))
    prism('crest', blade(0.08, 0.03), (0.0, W_HEAD[1] - 0.05, W_HEAD[2] + 0.065), (0.0, W_HEAD[1] - 0.33, W_HEAD[2] + 0.185), CIN, 'plain', scale_b=0.2, rnd=True, up=(0, 0, 1))
    if lv < 2:
        for s, n in SIDE: prism(f'eye_{n}', rect(0.05, 0.012), (s * 0.066, W_HEAD[1] + 0.035, W_HEAD[2] + 0.015), (s * 0.08, W_HEAD[1] + 0.04, W_HEAD[2] + 0.017), INL, 'plain', rnd=True, up=(0, 0, 1))
    if detail: prism('bill_inlay', rect(0.016, 0.012), (0.0, W_BILL[0][1] + 0.02, W_BILL[0][2] + 0.036), (0.0, W_BILL[1][1] - 0.09, W_BILL[1][2] + 0.093), GOLD, 'plain', rnd=True, up=(0, 0, 1))
    for s, n in SIDE:
        hip, hock, ank = [(s * x, f, z) for x, f, z in (W_HIP, W_HOCK, W_ANKLE)]
        PK.bone(f'thigh_{n}')
        prism(f'thigh_{n}', blade(W_LEG_W[0], 0.12), hip, hock, BR, 'plain', scale_b=0.6, rnd=False, up=(0, -1, 0))
        if detail: prism(f'thigh_inlay_{n}', rect(0.022, 0.012), (hip[0] + s * 0.045, hip[1] - 0.06, hip[2] - 0.12), (hock[0] + s * 0.03, hock[1] - 0.005, hock[2] + 0.1), GOLD, 'plain', rnd=True, up=(s, 0, 0))
        PK.bone(f'shin_{n}')
        if lv < 2: prism(f'hock_{n}', ngon(0.07, 6), (hock[0] - 0.06, hock[1], hock[2]), (hock[0] + 0.06, hock[1], hock[2]), DK, 'plain', rnd=True)
        prism(f'shin_{n}', blade(W_LEG_W[1], 0.085), hock, ank, BR, 'plain', scale_b=0.85, rnd=False, up=(0, 1, 0))
        toes = ((-0.07, 0.27), (0.0, 0.31), (0.07, 0.27), (0.0, -0.16)) if lv < 2 else ((0.0, 0.31),)
        for q, (dx, df) in enumerate(toes):
            prism(f'toe_{n}{q}', blade(W_LEG_W[2], 0.045), (ank[0], ank[1], 0.04), (ank[0] + dx, ank[1] + df, 0.006), DK, 'plain', scale_b=0.2, rnd=True, up=(0, 0, 1))
    PK.bone('root')

def wand_bones():
    out = [('root', (0, 0, 0), (0, 0, 0.2), None), ('body', W_PIVOT, (0, -0.05, 1.8), 'root'), ('neck', W_NECK[0], W_NECK[-1], 'body'), ('head', W_NECK2[0], W_HEAD, 'neck')]
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
    rj = max(r for r, z in W_FOOT + W_LOW + W_BELT + W_UP + W_LIP); G(rj <= WAND_R, f'wanderer jar radius {rj:.2f} m inside the game radius {WAND_R} (legs at {W_HIP[0]:.2f})')
    G(-0.02 <= z0 <= 0.01, f'wanderer feet on the ground (lowest z {z0:.3f})')
    m = K.mats(l0); sh = brass_share(l0)
    G({BR, DK, INL, CIN} <= m and not ({'pcBlack', 'pcOutline'} & m) and sh >= BRASS_MIN, f'wanderer is bronze: {sh:.0%} of its surface brass (min {BRASS_MIN:.0%}), dark bronze on the underside, joints and feet, no black and no baked outline; materials {sorted(m)}')
    G(K.tris(l0) >= TRIS_MIN, f'wanderer_lod0 tris {K.tris(l0)} (min {TRIS_MIN})')
    thin = min(min(W_LEG_W), 2 * min(W_NECK_R + W_NECK2_R), W_BILL_W[0])
    G(thin >= LIMB_MIN, f'wanderer limbs: thinnest of legs, neck and bill base {thin * 100:.1f} cm (min {LIMB_MIN * 100:.1f} cm = 3 px at play size)')
    (_, _), (_, _), (a0, a1) = K.bounds(l2); (_, _), (_, _), (b0, b1) = K.bounds(l1)
    G(a0 <= 0.03 and b0 <= 0.03 and a1 >= z1 - 0.15, f'wanderer LOD1 and LOD2 keep the legs and the head: lowest z {b0:.3f} / {a0:.3f}, LOD2 top {a1:.2f} m (LOD0 {z1:.2f})')
    bl = math.dist(*W_BILL); drop = W_BILL[0][2] - W_BILL[1][2]; sway = max(p[1] for p in W_NECK) - min(W_NECK[0][1], W_NECK[-1][1])
    G(bl >= W_BILL_MIN and drop >= 0.2 and sway >= 0.15, f'wanderer bill {bl:.2f} m long (min {W_BILL_MIN}), dropping {drop:.2f} m (so it shows when it faces the camera); neck S swings {sway:.2f} m forward of its ends (min 0.15)')
    G(rj / W_WHEEL[1] >= W_BODY_OVER_WHEEL and W_HIP[2] < W_PIVOT[2] and W_WHEEL[3] >= 10 and W_WHEEL[5] >= 0.12, f'wanderer vessel over its running gear: jar {2 * rj:.2f} m across against {2 * W_WHEEL[1]:.2f} m wheels ({rj / W_WHEEL[1]:.1f} x, min {W_BODY_OVER_WHEEL}), wheel hubs at {W_HIP[2]} m below the jar centre {W_PIVOT[2]} m, camber {W_WHEEL[3]} deg, hub caps {W_WHEEL[5]} m')


if __name__ == '__main__':
    PK.build_rigged('crab', crab_build, crab_bones(), crab_clips, os.path.join(OUTDIR, 'crab.glb'), BUDGET, 2.6, extras={'r': CRAB_R, 'clips': 'idle,move'}, extra_gates=crab_gates)
    PK.build_rigged('wanderer', wand_build, wand_bones(), wand_clips, os.path.join(OUTDIR, 'wanderer.glb'), BUDGET, 2.2, extras={'r': WAND_R, 'clips': 'idle,move'}, extra_gates=wand_gates)
