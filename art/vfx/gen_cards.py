# Painted attack cards for Empress Decrees (VFXP, 25 Nov). Writes one klad op batch per effect family (greyscale VALUE strokes: the game maps
# value 0..1 through a school's palette ramp, so one atlas serves every school). Shapes and timing follow pixelfx (MIT (c) Patch) effects,
# named per family below, compressed to game durations; nothing of pixelfx is shipped. All drawing is original, seeded, deterministic.
# Usage: python3 -I gen_cards.py <outdir> [family ...]      writes <outdir>/<family>.jsonl and <outdir>/families.json
import sys, json, math, os
import numpy as np

# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
CONFIG = {
    # Value steps of the shared ramp (0 = deep keyline, 0.5 = the school pigment, 1 = pale core). The ramp texture maps these to colour.
    'V': {'K': 0.06, 'D': 0.26, 'B': 0.5, 'L': 0.73, 'P': 0.95},
    # Paint scale: strokes are painted at this multiple of the shipped cell and box-downsampled (the approved slash B was painted at 2x).
    'paintK': 2,
    # Seed of every family's random sparks and jitter (numpy default_rng(seed + family index)).
    'seed': 2511,
}
V = CONFIG['V']; PK = CONFIG['paintK']

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def smooth(a, b, x): t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def outExpo(t): return 1.0 if t >= 1 else 1 - 2 ** (-10 * t)
def outCubic(t): t = clamp(t); return 1 - (1 - t) ** 3
def grey(v): g = int(round(clamp(v) * 255)); return '#%02x%02x%02x' % (g, g, g)

# ---- families: cell (1x px), texel (m per 1x px), pivot (1x px from the cell's top-left), frames, fps, atlas, orient, loop -----------------
# orient: 'bill' = camera-facing card (x right, y up); 'ground' = flat on the floor (x right, y = forward, away from the caster).
# loop = [a, b): tell frames that repeat while the game holds the tell (windup); frames from b on play after the release.
FAM = {
    # slash: pixelfx melee/sword-slash (the approved sample B, run 45467292518): smear A + echo E, sweep/hold/trail, tip glint, sparks.
    'slash':  dict(cell=[212, 156], texel=0.027, pivot=[64, 151], frames=13, fps=30, atlas='soft_a', orient='bill', ref='melee/sword-slash'),
    # thrust: pixelfx melee/thrust: a tapered stab streak out from the caster, tip flash, speed lines, sparks thrown forward.
    'thrust': dict(cell=[144, 40], texel=0.03, pivot=[6, 20], anchorM=1.1, frames=12, fps=30, atlas='soft_a', orient='bill', ref='melee/thrust', unitLenM=4.0),
    # impact: pixelfx impacts/hit-spark: a lopsided cross flare round a core, then a cone of short sparks that fall.
    'impact': dict(cell=[96, 96], texel=0.03, pivot=[48, 48], anchorM=1.0, frames=10, fps=30, atlas='soft_a', orient='bill', ref='impacts/hit-spark'),
    # bolt: pixelfx projectiles/magic-missile (head and trail) and arcane/arcane-orb (wobble): a soft orb head with a tapered wisp trail, loops.
    'bolt':   dict(cell=[136, 60], texel=0.03, pivot=[108, 30], anchorM=1.0, frames=8, fps=24, atlas='soft_a', orient='bill', ref='projectiles/magic-missile', loop=[0, 8]),
    # burst: pixelfx arcane/mana-burst and holy/sunburst: a core flash, an expanding ring of radial dabs and short rays, fading out.
    'burst':  dict(cell=[102, 102], texel=0.04, pivot=[51, 51], anchorM=1.0, frames=12, fps=30, atlas='soft_b', orient='bill', ref='arcane/mana-burst'),
    # shield: pixelfx holy/divine-shield: a dome round the body (front arcs, soft fill, sheen band sweeping), grows in, loops.
    'shield': dict(cell=[100, 116], texel=0.03, pivot=[50, 98], frames=12, fps=20, atlas='soft_b', orient='bill', ref='holy/divine-shield', loop=[4, 12]),
    # aura: pixelfx status/rage and status/haste: wisps rising up both sides of the body and a ring at the feet, loops (face kept clear).
    'aura':   dict(cell=[84, 116], texel=0.03, pivot=[42, 96], frames=12, fps=20, atlas='soft_b', orient='bill', ref='status/rage', loop=[0, 12]),
    # heal: pixelfx holy/heal: a soft column, motes and small leaf-shaped dabs rising and fading; loops for regen.
    'heal':   dict(cell=[80, 112], texel=0.03, pivot=[40, 98], frames=12, fps=20, atlas='soft_b', orient='bill', ref='holy/heal', loop=[0, 12]),
    # smoke: pixelfx explosions/smoke-bomb: puffs that swell, drift up and thin out.
    'smoke':  dict(cell=[94, 84], texel=0.04, pivot=[47, 78], frames=12, fps=15, atlas='soft_b', orient='bill', ref='explosions/smoke-bomb'),
    # ring: pixelfx arcane/magic-circle-cast (circle only, no glyphs): a brush circle drawn round, held with a pulse, a flash on release.
    'ring':   dict(cell=[144, 144], texel=0.0167, pivot=[72, 72], frames=10, fps=30, atlas='ground', orient='ground', ref='arcane/magic-circle-cast', loop=[3, 7], unitRadiusM=1.0),
    # mark: pixelfx holy/smite (target mark): a filled painted disc with a rim and cross strokes, held, a flash on release.
    'mark':   dict(cell=[112, 112], texel=0.0217, pivot=[56, 56], frames=10, fps=30, atlas='ground', orient='ground', ref='holy/smite', loop=[3, 7], unitRadiusM=1.0),
    # strip: pixelfx melee/thrust's lane read on the ground: a painted lane with edge strokes and forward chevrons; held, a flash on release.
    'strip':  dict(cell=[56, 192], texel=0.0125, pivot=[28, 190], frames=10, fps=30, atlas='ground', orient='ground', ref='melee/thrust', loop=[3, 7], unitLenM=2.35, unitWidthM=0.6),
    # crack: pixelfx impacts/ground-slam and nature/quake: radial cracks running out from the centre, held, then fading.
    'crack':  dict(cell=[144, 144], texel=0.0167, pivot=[72, 72], frames=10, fps=20, atlas='ground', orient='ground', ref='impacts/ground-slam', unitRadiusM=1.0),
}

class Painter:
    """Collects klad stroke ops for one family; positions in metres from the pivot (x right, y up / forward), sizes in metres."""
    def __init__(s, fam):
        s.fam = fam; s.ppm = PK / fam['texel']; s.ops = []; s.W = fam['cell'][0] * PK; s.H = fam['cell'][1] * PK
        s.px, s.py = fam['pivot'][0] * PK, fam['pivot'][1] * PK
    def P(s, x, y, p=1.0): return [round(s.px + x * s.ppm, 2), round(s.py - y * s.ppm, 2), round(clamp(p, 0.02, 1), 3)]
    def st(s, f, brush, size_m, v, pts, op=1.0):
        if len(pts) < 2 or op <= 0.01 or size_m * s.ppm < 0.6: return
        s.ops.append({'op': 'stroke', 'layer': 'l1', 'frame': f + 1, 'brush': brush, 'size': round(size_m * s.ppm, 2), 'color': grey(v),
                      'opacity': round(clamp(op), 3), 'points': [s.P(*q) for q in pts]})
    def st2(s, f, brush, size_m, v, pts, op=1.0):
        # a marker stroke lays alpha 0.7 (measured 25 Nov: '#f2f2f2' size 12 opacity 1 -> alpha 178); two passes reach 0.91 so a pale
        # line keeps its value where it crosses a darker stroke
        s.st(f, brush, size_m, v, pts, op); s.st(f, brush, size_m, v, pts, op)
    def dab(s, f, brush, size_m, v, x, y, op=1.0, dx=0.004):
        s.st(f, brush, size_m, v, [(x - dx, y, 1), (x + dx, y, 1)], op)

def arcpts(cx, cy, r, a0, a1, n, sy=1.0, press=lambda u: 1.0):
    return [(cx + math.cos(a0 + (a1 - a0) * i / (n - 1)) * r, cy + math.sin(a0 + (a1 - a0) * i / (n - 1)) * r * sy, press(i / (n - 1))) for i in range(n)]

# ---- slash: the approved B, rewritten in values (B's lead-white ramp steps map to K..P); geometry in B's 1x px (0.054 m) ----------
def fam_slash(Pn, rng):
    BM = 2.05 / 38  # B's metres per 1x px
    R0, a0, a1 = 42, -2.55, 0.95
    A = dict(cx=6, cy=-26, R=R0, sy=0.6, rot=-0.38, a0=a0, a1=a1, W=12, t0=0, sweep=0.06, hold=0.06, trail=0.24)
    E = dict(A, R=R0 * 33 / 42, W=R0 * 4.5 / 42, a0=a0 + (a1 - a0) * 0.1, a1=a1 - (a1 - a0) * (0.15 / 3.5), t0=0.017, hold=0.03, trail=0.2)
    RV = [V['K'] + 0.1, V['D'], 0.38, V['B'], V['L'], V['P']]  # B RAMP[0..5] -> values (RAMP[3] = the pigment)
    def onArc(s_, r, a):
        lx, ly = math.cos(a) * r, math.sin(a) * r * s_['sy']; c, n = math.cos(s_['rot']), math.sin(s_['rot'])
        return (s_['cx'] + lx * c - ly * n) * BM, -(s_['cy'] + lx * n + ly * c) * BM
    def arcs(s_, t):
        u = t - s_['t0']
        if u < 0: return None, 0, 0
        span = s_['a1'] - s_['a0']; head = outExpo(clamp(u / s_['sweep'])); tail = smooth(s_['sweep'] + s_['hold'], s_['sweep'] + s_['hold'] + s_['trail'], u)
        age = clamp(u / (s_['sweep'] + s_['hold'] + s_['trail'])); W = s_['W'] * (1 - tail * 0.55); L = span * (head - tail)
        th = 0.7 * (1 - clamp((u - s_['sweep'] - s_['hold']) / (s_['trail'] + 0.2)))
        if tail >= 1 or abs(L) < 0.02 or W < 0.3: return None, tail, th
        ta = s_['a0'] + span * tail
        pts = [(ta + L * (i / 24), W * math.sin(math.pi * (i / 24) ** 2.2) ** 0.6, i / 24) for i in range(25)]
        return (pts, W, age), tail, th
    for f in range(Pn.fam['frames']):
        t = (f + 1) / 30
        if t < 0.3:
            hx, hy = onArc(A, A['R'] - 4, A['a0'] + (A['a1'] - A['a0']) * outExpo(clamp(t / A['sweep'])))
            Pn.dab(f, 'airbrush', 34 * BM, RV[3], hx, hy, 0.35 * (1 - t / 0.3), dx=BM)
        for s_ in (E, A):
            r, tail, th = arcs(s_, t)
            if tail > 0.02 and th > 0:
                n = max(2, int(24 * tail))
                Pn.st(f, 'airbrush', 2.2 * BM, RV[1], [onArc(s_, s_['R'] - 0.5, s_['a0'] + (s_['a1'] - s_['a0']) * tail * i / (n - 1)) + (0.4 + 0.6 * i / (n - 1),) for i in range(n)], 0.55 * th)
            if not r: continue
            pts, W, age = r
            Pn.st(f, 'airbrush', (5 + W) * BM, RV[3], [onArc(s_, s_['R'] - W * 0.4, a) + (0.3 + 0.7 * v,) for a, w, v in pts if v >= 0.1], 0.45 * (1 - age))
            col = RV[4] if age < 0.25 else RV[3] if age < 0.55 else RV[2]
            Pn.st(f, 'marker', W * BM, col, [onArc(s_, s_['R'] - w * 0.5, a) + (clamp(w / W) ** (1 / 1.5),) for a, w, v in pts if v >= 0.2], 0.95)
            if age < 0.6:
                Pn.st(f, 'ink', W * 0.38 * BM, RV[5], [onArc(s_, s_['R'] - w * 0.18, a) + (clamp(w / W) ** (1 / 1.5) * 0.9,) for a, w, v in pts], 1.0 - age)
            Pn.st(f, 'airbrush', W * 0.5 * BM, RV[1], [onArc(s_, s_['R'] - w * 0.85, a) + (clamp(w / W) ** (1 / 1.5) * 0.6,) for a, w, v in pts], 0.5)
            # a dark keyline under the outer edge while the smear is young (reads on the red floor for light and dark ramps alike)
            if age < 0.5:
                Pn.st(f, 'airbrush', W * 0.3 * BM, V['K'], [onArc(s_, s_['R'] + 1.2, a) + (clamp(w / W) * 0.8,) for a, w, v in pts if v >= 0.15], 0.45 * (1 - age * 2))
        gg = t - A['sweep'] * 0.6
        if 0 < gg < 0.22:
            x0, y0 = onArc(A, A['R'] - A['W'] * 0.3, A['a1']); k = 9 * min(1, gg / 0.05) * (1 - gg / 0.22) * BM
            if k > BM:
                Pn.st(f, 'ink', 1.6 * BM, RV[5], [(x0 - k, y0, 0.1), (x0, y0, 1), (x0 + k, y0, 0.1)])
                Pn.st(f, 'ink', 1.6 * BM, RV[5], [(x0, y0 - k, 0.1), (x0, y0, 1), (x0, y0 + k, 0.1)])
                Pn.dab(f, 'airbrush', 6 * BM, RV[4], x0, y0, 0.6, dx=0.5 * BM)
    # sparks thrown off the head of the swing (sword-slash's spark spray): seeded, each a short soft stroke that flies and cools
    sp = []
    for i in range(14):
        tb = rng.uniform(0.02, 0.12); a = A['a0'] + (A['a1'] - A['a0']) * outExpo(clamp(tb / A['sweep']))
        x, y = onArc(A, A['R'] + rng.uniform(-3, 2), a); tang = a + math.pi / 2
        c, n = math.cos(A['rot']), math.sin(A['rot']); dxl, dyl = -math.sin(a), math.cos(a) * A['sy']
        vx, vy = (dxl * c - dyl * n), -(dxl * n + dyl * c); nv = math.hypot(vx, vy); sp.append((tb, x, y, vx / nv * rng.uniform(2.5, 5), vy / nv * rng.uniform(2.5, 5) + rng.uniform(-0.5, 1.5), rng.uniform(0.15, 0.3)))
    for f in range(Pn.fam['frames']):
        t = (f + 1) / 30
        for tb, x, y, vx, vy, life in sp:
            u = t - tb
            if u <= 0 or u > life: continue
            x1, y1 = x + vx * u, y + vy * u - 4 * u * u; x2, y2 = x1 - vx * 0.025, y1 - (vy - 8 * u) * 0.025
            Pn.st(f, 'ink', 2.0 * BM * (1 - u / life * 0.5), RV[5] if u < life * 0.4 else RV[4], [(x2, y2, 0.3), (x1, y1, 1)])

# ---- thrust: unit length 4 m along +x from the caster; the game stretches x to the move's range ----------------------------------
def fam_thrust(Pn, rng):
    L = Pn.fam['unitLenM']; lines = [(rng.uniform(-0.18, 0.18), rng.uniform(0.5, 0.9), rng.uniform(0.0, 0.03)) for _ in range(4)]
    sparks = [(rng.uniform(0.06, 0.12), rng.uniform(-0.25, 0.25), rng.uniform(4, 9), rng.uniform(0.12, 0.22)) for _ in range(9)]
    for f in range(Pn.fam['frames']):
        t = (f + 1) / 30
        head = outExpo(clamp(t / 0.08)) * L * 0.94; tail = smooth(0.1, 0.3, t) * L * 0.9; age = clamp(t / 0.3)
        if head - tail > 0.08:
            n = 14; W = 0.34 * (1 - age * 0.5)
            body = [(tail + (head - tail) * i / (n - 1), 0, math.sin(math.pi * (i / (n - 1)) ** 0.6) ** 0.7) for i in range(n)]
            Pn.st(f, 'airbrush', W * 2.2, V['B'], body, 0.4 * (1 - age))
            Pn.st(f, 'airbrush', W * 1.1, V['K'], [(x, -W * 0.45, p * 0.7) for x, _, p in body], 0.35 * (1 - age))
            Pn.st(f, 'marker', W, V['L'] if age < 0.4 else V['B'], body, 0.95)
            Pn.st(f, 'ink', W * 0.35, V['P'], [(x, W * 0.08, p) for x, _, p in body], 1 - age)
            for oy, ln, d in lines:
                x1 = head - 0.15; x0 = max(tail, x1 - ln * L * 0.45)
                if x1 - x0 > 0.1: Pn.st(f, 'ink', 0.05, V['L'], [(x0, oy, 0.2), (x1, oy, 0.8)], 0.8 * (1 - age))
        if 0.02 < t < 0.17:
            k = 0.45 * min(1, (t - 0.02) / 0.04) * (1 - (t - 0.02) / 0.15); x0 = head
            Pn.dab(f, 'airbrush', 0.5, V['L'], x0, 0, 0.6)
            Pn.st(f, 'ink', 0.07, V['P'], [(x0 - k, 0, 0.1), (x0, 0, 1), (x0 + k * 1.3, 0, 0.1)])
            Pn.st(f, 'ink', 0.07, V['P'], [(x0, -k * 0.7, 0.1), (x0, 0, 1), (x0, k * 0.7, 0.1)])
        for tb, oy, v, life in sparks:
            u = t - tb
            if u <= 0 or u > life: continue
            x1 = L * 0.9 + v * u * 0.35; y1 = oy + oy * v * u - 3 * u * u
            Pn.st(f, 'ink', 0.06 * (1 - u / life * 0.5), V['P'] if u < life * 0.4 else V['L'], [(x1 - 0.12, y1 + 0.02, 0.3), (x1, y1, 1)])

# ---- impact: centred on the hit point; the long ray points along +x (the game turns it along the blow) --------------------------
def fam_impact(Pn, rng):
    rays = [(0.0, 1.3, 0.17), (math.pi, 0.35, 0.16), (-math.pi / 2, 0.62, 0.18), (math.pi / 2, 0.42, 0.17), (-math.pi / 4, 0.26, 0.09)]
    tilt = rng.uniform(-0.1, 0.1)
    sparks = [(rng.uniform(-0.75, 0.6), rng.uniform(5, 8), rng.uniform(0.12, 0.22), rng.uniform(0, 0.03)) for _ in range(13)]
    for f in range(Pn.fam['frames']):
        t = f / 30
        if t < 0.1:
            k = 1 if t < 0.034 else 0.55 if t < 0.067 else 0.25
            Pn.dab(f, 'airbrush', 1.3 * k + 0.4, V['B'], 0, 0, 0.55 * k)
            for a, L, w in rays:
                a += tilt; L *= (0.6 + 0.4 * k)
                pts = [(math.cos(a) * L * i / 6, math.sin(a) * L * i / 6, (1 - i / 6) ** 1.3 + 0.05) for i in range(7)]
                Pn.st(f, 'marker', w * 1.4, V['K'], pts, 0.35 * k)
                Pn.st(f, 'marker', w, V['L'], pts, 0.95)
                Pn.st(f, 'ink', w * 0.45, V['P'], pts, 1.0)
            Pn.dab(f, 'marker', 0.24 * k + 0.08, V['P'], 0, 0, 1)
        for a, v, life, tb in sparks:
            u = t - 0.02 - tb
            if u <= 0 or u > life: continue
            x1 = math.cos(a) * v * u; y1 = math.sin(a) * v * u - 6 * u * u; vx, vy = math.cos(a) * v, math.sin(a) * v - 12 * u
            Pn.st(f, 'ink', 0.08 * (1 - u / life * 0.4), V['P'] if u < life * 0.35 else V['L'] if u < life * 0.7 else V['B'], [(x1 - vx * 0.02, y1 - vy * 0.02, 0.3), (x1, y1, 1)])

# ---- bolt: head at the pivot, trail along -x (the game turns +x to the flight direction); 8-frame loop ----------------------------
def fam_bolt(Pn, rng):
    n = Pn.fam['frames']; ph = [rng.uniform(0, 6.28) for _ in range(3)]
    for f in range(n):
        u = f / n; w = 2 * math.pi * u
        for j, amp in enumerate((0.06, 0.09, 0.05)):
            pts = [(-3.1 * i / 10, 1.8 * amp * math.sin(w * (1 + j) + ph[j] + i * 0.9) * (i / 10) + (j - 1) * 0.06 * i / 10, (1 - i / 10) ** 1.2) for i in range(11)]
            Pn.st(f, 'airbrush', 0.62 - j * 0.1, V['B'] if j != 1 else V['D'], pts, 0.75)
        Pn.st(f, 'marker', 0.3, V['L'], [(-2.0 * i / 6, 0.04 * math.sin(w + i), (1 - i / 6) ** 1.5) for i in range(7)], 0.9)
        Pn.dab(f, 'airbrush', 1.35 + 0.1 * math.sin(w * 2), V['B'], 0, 0, 0.6)
        Pn.dab(f, 'marker', 0.8, V['K'], 0, -0.04, 0.6)
        Pn.dab(f, 'marker', 0.66, V['L'], 0, 0, 1)
        Pn.dab(f, 'marker', 0.34, V['P'], 0.05, 0.05, 1); Pn.dab(f, 'marker', 0.34, V['P'], 0.05, 0.05, 1)
        for k in range(3):
            a = w + k * 2.1; Pn.dab(f, 'ink', 0.08, V['P'], -0.4 - 0.45 * ((u + k / 3) % 1), 0.24 * math.sin(a), 0.8)

# ---- burst: centred; core flash, ring of radial dabs, short rays; one-shot ----------------------------------------------------------
def fam_burst(Pn, rng):
    N = 16; angs = [2 * math.pi * i / N + rng.uniform(-0.12, 0.12) for i in range(N)]; lens = [rng.uniform(0.35, 1.15) for _ in range(N)]; gaps = sorted(rng.uniform(0, 2 * math.pi, 5))
    for f in range(Pn.fam['frames']):
        t = f / 30; e = outCubic(t / 0.3); fade = 1 - smooth(0.12, 0.4, t)
        if t < 0.1:
            k = 1 - t / 0.1; Pn.dab(f, 'airbrush', 1.8 * (0.5 + e), V['L'], 0, 0, 0.7 * k); Pn.dab(f, 'marker', 0.5 * k + 0.1, V['P'], 0, 0, 1)
        r = 0.25 + 1.2 * e
        if fade > 0.02:
            Pn.st(f, 'airbrush', 0.5 * fade + 0.1, V['K'], arcpts(0, 0, r + 0.12, 0, 2 * math.pi, 40), 0.3 * fade)
            for j in range(5):
                g0 = gaps[j] + 0.18; g1 = gaps[(j + 1) % 5] + (2 * math.pi if j == 4 else 0) - 0.05
                Pn.st(f, 'marker', 0.24 * fade + 0.05, V['B'], arcpts(0, 0, r, g0, g1, 14, press=lambda u: math.sin(math.pi * u) ** 0.5), 0.9 * fade)
                Pn.st(f, 'ink', 0.08 * fade + 0.02, V['P'] if t < 0.15 else V['L'], arcpts(0, 0, r - 0.05, g0 + 0.05, g1 - 0.1, 12, press=lambda u: math.sin(math.pi * u)), fade)
            for a, l in zip(angs, lens):
                r0 = r * 0.7; r1 = r * (0.95 + 0.35 * l)
                Pn.st(f, 'marker', 0.1 * fade + 0.03, V['L'], [(math.cos(a) * r0, math.sin(a) * r0, 0.4), (math.cos(a) * r1, math.sin(a) * r1, 1)], fade)

# ---- shield: dome round a 2.05 m body (feet at the pivot); intro 4 frames, loop 8 (sheen band sweeping) --------------------------
def fam_shield(Pn, rng):
    cx, cy, rx, ry = 0, 1.2, 1.25, 1.35
    for f in range(Pn.fam['frames']):
        g = 0.8 + 0.2 * outCubic((f + 1) / 4) if f < 4 else 1.0; u = (f - 4) / 8 if f >= 4 else 0
        R = (rx * g, ry * g)
        Pn.dab(f, 'airbrush', 2.2 * g + 0.1, V['D'], cx, cy, 0.3)
        Pn.st(f, 'airbrush', 0.36, V['K'], arcpts(cx, cy, R[0] + 0.08, -0.15 * math.pi, 1.15 * math.pi, 30, sy=R[1] / max(R[0], 0.01)), 0.5)
        Pn.st(f, 'marker', 0.2, V['L'], arcpts(cx, cy, R[0], -0.15 * math.pi, 1.15 * math.pi, 30, sy=R[1] / max(R[0], 0.01), press=lambda s: 0.5 + 0.5 * math.sin(s * math.pi)), 0.95)
        Pn.st(f, 'ink', 0.05, V['P'], arcpts(cx, cy, R[0] * 0.96, 0.55 * math.pi, 0.95 * math.pi, 12, sy=R[1] / max(R[0], 0.01)), 0.9)
        # ground ellipse
        Pn.st(f, 'marker', 0.08, V['L'], arcpts(cx, 0.02, R[0] * 0.95, math.pi, 2 * math.pi, 20, sy=0.3), 0.8)
        Pn.st(f, 'airbrush', 0.12, V['K'], arcpts(cx, -0.03, R[0] * 1.0, math.pi, 2 * math.pi, 20, sy=0.3), 0.45)
        if f >= 4:
            # sheen band sweeping across (a meridian arc moving left to right), and two glints
            k = u * 2 - 1
            Pn.st(f, 'airbrush', 0.22, V['L'], [(cx + R[0] * k * math.sin(math.pi * i / 10), cy + R[1] * math.cos(math.pi * i / 10) * 0.98, math.sin(math.pi * i / 10)) for i in range(11)], 0.55)
            a = 2 * math.pi * u
            for j in range(2):
                gx, gy = cx + R[0] * 0.8 * math.cos(a + j * 3.1), cy + R[1] * 0.8 * math.sin(a + j * 3.1) * 0.9
                Pn.st(f, 'ink', 0.04, V['P'], [(gx - 0.09, gy, 0.1), (gx, gy, 1), (gx + 0.09, gy, 0.1)]); Pn.st(f, 'ink', 0.04, V['P'], [(gx, gy - 0.09, 0.1), (gx, gy, 1), (gx, gy + 0.09, 0.1)])

# ---- aura: wisps rising up both sides of the body, ring at the feet; 12-frame loop; nothing over the head/face (x within +-0.35 above 1.4 m)
def fam_aura(Pn, rng):
    n = Pn.fam['frames']; W = [(s, rng.uniform(0.45, 0.85), rng.uniform(0, 1), rng.uniform(1.0, 1.8), rng.uniform(0.14, 0.22)) for s in (-1, 1) for _ in range(7)]
    for f in range(n):
        u = f / n
        Pn.st(f, 'airbrush', 0.22, V['K'], arcpts(0, -0.02, 0.85, 0, 2 * math.pi, 28, sy=0.32), 0.4)
        Pn.st(f, 'marker', 0.09, V['B'], arcpts(0, 0.02, 0.8, 0, 2 * math.pi, 28, sy=0.3, press=lambda s: 0.5 + 0.5 * math.sin(s * 6.28 * 3 + u * 6.28)), 0.9)
        for s, x0, ph, h, w in W:
            p = (u + ph) % 1; y0 = p * h; y1 = y0 + 0.55; op = math.sin(math.pi * p)
            pts = [(s * (x0 + 0.08 * math.sin(6.28 * (p + i / 6))), y0 + (y1 - y0) * i / 6, (1 - i / 6) ** 0.8) for i in range(7)]
            Pn.st(f, 'marker', w, V['B'], pts, 0.85 * op)
            Pn.st(f, 'airbrush', w * 2, V['L'], pts, 0.25 * op)
            Pn.st(f, 'ink', w * 0.5, V['P'] if p < 0.6 else V['L'], [(x + s * 0.01, y, q) for x, y, q in pts], op)

# ---- heal: column glow, motes and leaf dabs rising; loop 12 frames ----------------------------------------------------------------
def fam_heal(Pn, rng):
    n = Pn.fam['frames']; M = [((1 if i % 2 else -1) * rng.uniform(0.38, 0.8), rng.uniform(0, 1), rng.uniform(1.4, 2.3), rng.uniform(0.18, 0.28), i % 3 == 0) for i in range(16)]
    for f in range(n):
        u = f / n
        Pn.st(f, 'airbrush', 1.3, V['L'], [(0, 0.05, 1), (0, 1.7, 0.3)], 0.32)
        Pn.st(f, 'marker', 0.08, V['L'], arcpts(0, 0.02, 0.7, 0, 2 * math.pi, 24, sy=0.3, press=lambda s: 0.6 + 0.4 * math.sin(s * 6.28 * 2 - u * 6.28)), 0.8)
        for x, ph, h, sz, leaf in M:
            p = (u + ph) % 1; y = p * h; op = math.sin(math.pi * p) ** 0.7; xx = x * (1 - 0.3 * p) + 0.06 * math.sin(6.28 * (p * 2 + ph))
            if leaf:
                a = 0.6 * math.sin(6.28 * (p + ph)); dx, dy = math.cos(a) * sz, math.sin(a) * sz
                Pn.st(f, 'marker', sz * 0.7, V['B'], [(xx - dx, y - dy, 0.2), (xx, y, 1), (xx + dx, y + dy, 0.2)], op)
                Pn.st(f, 'ink', sz * 0.2, V['L'], [(xx - dx * 0.8, y - dy * 0.8, 0.2), (xx + dx * 0.8, y + dy * 0.8, 0.2)], op)
            else:
                Pn.dab(f, 'airbrush', sz * 2.2, V['B'], xx, y, 0.5 * op); Pn.dab(f, 'marker', sz * 0.7, V['P'], xx, y, op)

# ---- smoke: puffs swell, drift up, thin; one-shot 12 frames at 15 fps --------------------------------------------------------------
def fam_smoke(Pn, rng):
    B_ = [(rng.uniform(-0.8, 0.8), rng.uniform(0.0, 0.4), rng.uniform(0.55, 0.85), rng.uniform(0, 0.12)) for _ in range(11)]
    for f in range(Pn.fam['frames']):
        t = f / 15
        for x, y, r, tb in B_:
            u = clamp((t - tb) / 0.6)
            if t < tb or u >= 1: continue
            rr = r * (0.4 + 0.8 * outCubic(u)); yy = y + 0.6 * u + rr * 0.6; op = (1 - u) ** 1.2
            Pn.dab(f, 'airbrush', rr * 2.4, V['D'], x * (1 + 0.5 * u), yy, 0.55 * op)
            Pn.dab(f, 'marker', rr * 1.3, V['B'], x * (1 + 0.5 * u), yy + rr * 0.1, 0.75 * op)
            Pn.dab(f, 'marker', rr * 0.8, V['L'], x * (1 + 0.5 * u) - rr * 0.15, yy + rr * 0.3, 0.8 * op)
            Pn.dab(f, 'marker', rr * 0.4, V['P'], x * (1 + 0.5 * u) - rr * 0.25, yy + rr * 0.4, 0.7 * op)
            Pn.st(f, 'airbrush', rr * 0.4, V['K'], arcpts(x * (1 + 0.5 * u), yy, rr * 0.75, -2.6, -0.5, 8), 0.35 * op)

# ---- ground: ring (unit radius 1 m), mark (unit radius 1 m), strip (unit length along +y from the caster), crack (unit radius 1 m) -
def fam_ring(Pn, rng):
    # tell = a dark keyline outside, a pale brush ring (the 3:1 read on the 丹 floor), the pigment inside it; release = ticks inward, then gone
    jit = [rng.uniform(-0.03, 0.03) for _ in range(48)]
    for f in range(Pn.fam['frames']):
        if f == 9:
            for i in range(4):
                a = 2 * math.pi * i / 4 + 0.6; Pn.dab(f, 'marker', 0.05, V['L'], math.cos(a) * 0.9, math.sin(a) * 0.9, 1)
            continue
        sweep = outCubic((f + 1) / 3) if f < 3 else 1.0; rel = f >= 7
        a1 = -math.pi / 2 + 2 * math.pi * sweep; n = max(3, int(48 * sweep))
        pts = [(math.cos(-math.pi / 2 + (a1 + math.pi / 2) * i / (n - 1)) * (1 + jit[i % 48]), math.sin(-math.pi / 2 + (a1 + math.pi / 2) * i / (n - 1)) * (1 + jit[i % 48]), 1) for i in range(n)]
        k = 1.0 if f < 8 else 0.5
        Pn.st(f, 'marker', 0.1 * k, V['K'], [(x * 1.05, y * 1.05, p) for x, y, p in pts], 1)
        Pn.st(f, 'marker', 0.07 * k, V['B'], [(x * 0.84, y * 0.84, p) for x, y, p in pts], 1)
        Pn.st2(f, 'marker', 0.13 * k, V['P'], [(x * 0.935, y * 0.935, p) for x, y, p in pts], 1)
        if 3 <= f < 7:
            r = 1 - 0.7 * (f - 3) / 4
            Pn.st(f, 'marker', 0.06, V['K'], arcpts(0, 0, r + 0.065, 0, 2 * math.pi, 40), 1)
            Pn.st2(f, 'marker', 0.07, V['P'], arcpts(0, 0, r, 0, 2 * math.pi, 40), 1)
        if rel:
            kk = (f - 6) / 2
            for i in range(10):
                a = 2 * math.pi * i / 10 + 0.2; Pn.st2(f, 'marker', 0.08, V['P'], [(math.cos(a) * (1 - 0.5 * kk), math.sin(a) * (1 - 0.5 * kk), 0.4), (math.cos(a) * 0.88, math.sin(a) * 0.88, 1)], 1)

def fam_mark(Pn, rng):
    hatch = [(-0.62 + 0.31 * i, V['B'] if i % 2 else V['L']) for i in range(5)]
    for f in range(Pn.fam['frames']):
        if f == 9:
            Pn.dab(f, 'marker', 0.1, V['L'], 0, 0, 1); continue
        g = outCubic((f + 1) / 3) if f < 3 else 1.0; rel = f >= 7; pulse = (f - 3) / 4 if 3 <= f < 7 else 0
        r = 0.95 * g * (1 if f < 8 else 0.6)
        Pn.st(f, 'marker', 0.11, V['K'], arcpts(0, 0, r + 0.075, 0, 2 * math.pi, 40), 1)
        Pn.st2(f, 'marker', 0.13, V['P'], arcpts(0, 0, r - 0.05, 0.2, 0.2 + 2 * math.pi, 40, press=lambda u: 0.85 + 0.15 * math.sin(u * 19)), 1)
        for c, v in hatch:
            c *= r; h = math.sqrt(max(0.0, (r * 0.8) ** 2 - c * c))
            if h > 0.05:
                d = 0.7071; Pn.st(f, 'marker', 0.11, v, [(c * d - h * d, c * -d - h * d, 0.5), (c * d + h * d, c * -d + h * d, 1)], 1)
        if 3 <= f < 7:
            rr = r * (0.85 - 0.6 * pulse)
            Pn.st(f, 'marker', 0.06, V['K'], arcpts(0, 0, rr + 0.07, 0, 2 * math.pi, 30), 1)
            Pn.st2(f, 'marker', 0.08, V['P'], arcpts(0, 0, rr, 0, 2 * math.pi, 30), 1)
        Pn.dab(f, 'marker', 0.2 if not rel else 0.5 + 0.3 * (f - 7), V['P'], 0, 0, 1); Pn.dab(f, 'marker', 0.2 if not rel else 0.5 + 0.3 * (f - 7), V['P'], 0, 0, 1)

def fam_strip(Pn, rng):
    L, Wd = Pn.fam['unitLenM'], Pn.fam['unitWidthM']; hw = Wd / 2
    for f in range(Pn.fam['frames']):
        if f == 9:
            Pn.dab(f, 'marker', 0.06, V['L'], 0, L * 0.5, 1); continue
        g = outCubic((f + 1) / 3) if f < 3 else 1.0; rel = f >= 7; ph = (f - 3) / 4 if 3 <= f < 7 else 0
        y1 = L * g; k = 1.0 if f < 8 else 0.5
        for s_ in (-1, 1):
            Pn.st(f, 'marker', 0.075 * k, V['K'], [(s_ * (hw - 0.04), 0.03, 1), (s_ * (hw - 0.04), y1 - 0.03, 1)], 1)
            Pn.st2(f, 'marker', 0.055 * k, V['P'], [(s_ * (hw - 0.1), 0.03, 1), (s_ * (hw - 0.1), y1 - 0.03, 1)], 1)
        Pn.st(f, 'marker', 0.08 * k, V['B'], [(0, 0.05, 1), (0, y1 - 0.05, 1)], 1)
        for i in range(5):
            y = (i + ph) * L / 5 + 0.12
            if y + 0.16 < y1:
                Pn.st(f, 'marker', 0.05 * k, V['K'], [(-hw * 0.62, y - 0.045, 1), (0, y + 0.125, 1), (hw * 0.62, y - 0.045, 1)], 1)
                Pn.st2(f, 'marker', 0.05 * k, V['P'], [(-hw * 0.55, y + 0.01, 1), (0, y + 0.18, 1), (hw * 0.55, y + 0.01, 1)], 1)
        if rel and f == 7: Pn.st(f, 'marker', hw * 0.9, V['P'], [(0, 0.1, 1), (0, L - 0.1, 1)], 1)

def fam_crack(Pn, rng):
    cracks = []
    for i in range(9):
        a = 2 * math.pi * i / 9 + rng.uniform(-0.2, 0.2); pts = [(0.0, 0.0)]; r = 0.0; aa = a
        for k in range(6):
            r += rng.uniform(0.13, 0.2); aa += rng.uniform(-0.3, 0.3); pts.append((math.cos(aa) * r, math.sin(aa) * r))
        br = (len(pts) // 2, a + rng.choice([-0.7, 0.7]), rng.uniform(0.18, 0.3))
        cracks.append((pts, br))
    for f in range(Pn.fam['frames']):
        t = f / 20; g = outCubic(t / 0.15); fade = 1 - smooth(0.22, 0.42, t)
        if fade <= 0.03: continue
        Pn.dab(f, 'marker', 0.45 * g, V['D'], 0, 0, fade)
        for pts, (bi, ba, bl) in cracks:
            n = max(2, int(round(len(pts) * g)))
            seg = [(x, y, 1 - i / len(pts) * 0.8) for i, (x, y) in enumerate(pts[:n])]
            Pn.st(f, 'marker', 0.09, V['K'], seg, fade)
            Pn.st(f, 'marker', 0.035, V['L'] if t < 0.2 else V['B'], [(x + 0.012, y + 0.012, p) for x, y, p in seg], fade)
            if n > bi:
                bx, by = pts[bi]; Pn.st(f, 'marker', 0.05, V['K'], [(bx, by, 0.8), (bx + math.cos(ba) * bl, by + math.sin(ba) * bl, 0.2)], fade)
        if t < 0.15:
            for i in range(12):
                a = 2 * math.pi * i / 12; r = 0.3 + 0.7 * g
                Pn.dab(f, 'marker', 0.08, V['B'], math.cos(a) * r, math.sin(a) * r, fade)

FUN = {k: globals()['fam_' + k] for k in FAM}

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True); want = sys.argv[2:] or list(FAM)
    for i, k in enumerate(FAM):
        if k not in want: continue
        fam = FAM[k]; Pn = Painter(fam); FUN[k](Pn, np.random.default_rng(CONFIG['seed'] + i))
        ops = [{'op': 'timeline', 'frames': fam['frames'] + 1}] + [{'op': 'cel', 'new': 'l1', 'frame': f + 1, 'id': f'f{f + 1}'} for f in range(fam['frames'])] + Pn.ops
        open(f'{out}/{k}.jsonl', 'w').write('\n'.join(json.dumps(o) for o in ops) + '\n')
        print(k, 'ops', len(Pn.ops), 'canvas', Pn.W, Pn.H)
    json.dump({k: dict(v, paintK=PK) for k, v in FAM.items()}, open(f'{out}/families.json', 'w'), indent=1)
