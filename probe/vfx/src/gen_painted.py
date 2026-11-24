# B (painted): the pixelfx sword-slash's shape and timing repainted as soft klad strokes in the lead-white ramp, at 2x (272x208 per frame).
# The arcs follow the effect's own parameters (src/fx/melee/sword-slash.js create(): smear A and echo E, sweep/hold/trail, taper
# w = W sin(pi v^2.2)^0.6); sparks and motes are taken from A's baked frames (pixels outside the arc band) and painted as short soft strokes.
# Usage: gen_painted.py A_baked.png meta.json ops.jsonl
import sys, json, math, numpy as np
from PIL import Image
K = 2; ORX, ORY = 44, 92; FW, FH = 136, 104; COLS = 5
RAMP = ['#524c40', '#7a7466', '#a49e8f', '#d9d2c3', '#ebe7e0', '#fbfaf8']
FRAMES = range(1, 18)
def clamp(x, a=0, b=1): return max(a, min(b, x))
def smooth(a, b, x): t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t)
def outExpo(t): return 1 if t >= 1 else 1 - 2 ** (-10 * t)
R0, a0, a1 = 42, -2.55, 0.95
A = dict(cx=6, cy=-26, R=R0, sy=0.6, rot=-0.38, a0=a0, a1=a1, W=12, t0=0, sweep=0.06, hold=0.06, trail=0.24)
E = dict(A, R=R0 * 33 / 42, W=R0 * 4.5 / 42, a0=a0 + (a1 - a0) * 0.1, a1=a1 - (a1 - a0) * (0.15 / 3.5), t0=0.017, hold=0.03, trail=0.2)
def onArc(s, r, a):
    lx, ly = math.cos(a) * r, math.sin(a) * r * s['sy']; c, n = math.cos(s['rot']), math.sin(s['rot'])
    return s['cx'] + lx * c - ly * n, s['cy'] + lx * n + ly * c
def P(x, y): return [round(float((ORX + x) * K), 2), round(float((ORY + y) * K), 2)]
def arcs(s, t):
    # (points along the smear centreline with pressure, width, age) or None, plus the trace length
    u = t - s['t0']
    if u < 0: return None, 0, 0
    span = s['a1'] - s['a0']; head = outExpo(clamp(u / s['sweep'])); tail = smooth(s['sweep'] + s['hold'], s['sweep'] + s['hold'] + s['trail'], u)
    age = clamp(u / (s['sweep'] + s['hold'] + s['trail'])); W = s['W'] * (1 - tail * 0.55); L = span * (head - tail)
    th = 0.7 * (1 - clamp((u - s['sweep'] - s['hold']) / (s['trail'] + 0.2)))
    if tail >= 1 or abs(L) < 0.02 or W < 0.3: return None, tail, th
    ta = s['a0'] + span * tail; pts = []
    for i in range(25):
        v = i / 24; w = W * math.sin(math.pi * v ** 2.2) ** 0.6
        pts.append((ta + L * v, w, v))
    return (pts, W, age), tail, th
def band_mask(s, t):
    m = np.zeros((FH, FW), bool); r, _, _ = arcs(s, t)
    if not r: return m
    pts, W, age = r
    for (a, w, v) in pts:
        for k in np.linspace(-1.5, w + 1.5, 8):
            x, y = onArc(s, s['R'] - k, a); xi, yi = int(round(ORX + x)), int(round(ORY + y))
            m[max(0, yi - 2):yi + 3, max(0, xi - 2):xi + 3] = True
    return m
def comps(mask):
    seen = np.zeros_like(mask); out = []
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]: continue
        st = [(y, x)]; seen[y, x] = True; c = []
        while st:
            p = st.pop(); c.append(p)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    q = (p[0] + dy, p[1] + dx)
                    if 0 <= q[0] < FH and 0 <= q[1] < FW and mask[q] and not seen[q]: seen[q] = True; st.append(q)
        out.append(c)
    return out
base = np.array(Image.open(sys.argv[1]).convert('RGBA'))
ops = [{'op': 'timeline', 'frames': 18}]
for f in FRAMES: ops.append({'op': 'cel', 'new': 'l1', 'frame': f, 'id': f'f{f}'})
for f in FRAMES:
    t = f / 30; L = []
    def st(brush, size, col, pts, op=1.0):
        L.append({'op': 'stroke', 'layer': 'l1', 'frame': f, 'brush': brush, 'size': round(size * K, 2), 'color': col, 'opacity': round(op, 3), 'points': pts})
    # light riding the head of the swing (pixelfx glow 40 px, k 0.5 fading by 0.3 s)
    if t < 0.3:
        hx_, hy_ = onArc(A, A['R'] - 4, A['a0'] + (A['a1'] - A['a0']) * outExpo(clamp(t / A['sweep'])))
        st('airbrush', 34, RAMP[3], [P(hx_ - 1, hy_) + [1], P(hx_ + 1, hy_) + [1]], 0.35 * (1 - t / 0.3))
    for s, main in ((E, False), (A, True)):
        r, tail, th = arcs(s, t)
        # the lingering trace of the blade's path: a faint thin line where the dotted trace was
        if tail > 0.02 and th > 0:
            n = max(2, int(24 * tail)); tr = [P(*onArc(s, s['R'] - 0.5, s['a0'] + (s['a1'] - s['a0']) * tail * i / (n - 1))) + [0.4 + 0.6 * i / (n - 1)] for i in range(n)]
            st('airbrush', 2.2, RAMP[1], tr, 0.55 * th)
        if not r: continue
        pts, W, age = r
        # soft glow under the smear
        g = [P(*onArc(s, s['R'] - W * 0.4, a)) + [0.3 + 0.7 * v] for a, w, v in pts if v >= 0.1]
        st('airbrush', 5 + W, RAMP[3], g, 0.45 * (1 - age))
        # body: mid tone cooling with age, a brighter rim on the outer edge while young
        body = [P(*onArc(s, s['R'] - w * 0.5, a)) + [round(clamp(w / W) ** (1 / 1.5), 3)] for a, w, v in pts if v >= 0.2]
        col = RAMP[4] if age < 0.25 else RAMP[3] if age < 0.55 else RAMP[2]
        st('marker', W, col, body, 0.95)
        if age < 0.6:
            rim = [P(*onArc(s, s['R'] - w * 0.18, a)) + [round(clamp(w / W) ** (1 / 1.5) * 0.9, 3)] for a, w, v in pts]
            st('ink', W * 0.38, RAMP[5], rim, 1.0 - age)
        # the darker inner edge (the ramp's lower steps inward)
        inner = [P(*onArc(s, s['R'] - w * 0.85, a)) + [round(clamp(w / W) ** (1 / 1.5) * 0.6, 3)] for a, w, v in pts]
        st('airbrush', W * 0.5, RAMP[1], inner, 0.5)
    # tip glint (pixelfx sparkle, 0 < g < 0.22 s)
    gg = t - A['sweep'] * 0.6
    if 0 < gg < 0.22:
        x0, y0 = onArc(A, A['R'] - A['W'] * 0.3, A['a1']); k = 9 * min(1, gg / 0.05) * (1 - gg / 0.22)
        if k > 1:
            st('ink', 1.6, RAMP[5], [P(x0 - k, y0) + [0.1], P(x0, y0) + [1], P(x0 + k, y0) + [0.1]])
            st('ink', 1.6, RAMP[5], [P(x0, y0 - k) + [0.1], P(x0, y0) + [1], P(x0, y0 + k) + [0.1]])
            st('airbrush', 6, RAMP[4], [P(x0 - 0.5, y0) + [1], P(x0 + 0.5, y0) + [1]], 0.6)
    # sparks and motes: A's baked pixels outside both arc bands, one short soft stroke per piece
    x0, y0 = (f % COLS) * FW, (f // COLS) * FH; fr = base[y0:y0 + FH, x0:x0 + FW]
    rest = (fr[..., 3] > 0) & ~band_mask(A, t) & ~band_mask(E, t)
    for c in comps(rest):
        ys = np.array([p[0] for p in c]); xs = np.array([p[1] for p in c]); col = '#%02x%02x%02x' % tuple(fr[c[0]][:3])
        if len(c) == 1: pts = [P(xs[0] - ORX - 0.2, ys[0] - ORY) + [1], P(xs[0] - ORX + 0.2, ys[0] - ORY) + [1]]
        else:
            i, j = (xs + ys).argmin(), (xs + ys).argmax()
            if np.ptp(xs) > np.ptp(ys): i, j = xs.argmin(), xs.argmax()
            pts = [P(xs[i] - ORX, ys[i] - ORY) + [1], P(xs[j] - ORX, ys[j] - ORY) + [0.3]]
        st('ink', 2.0, col, pts)
    ops += L
open(sys.argv[3], 'w').write('\n'.join(json.dumps(o) for o in ops) + '\n')
print('ops', len(ops), 'frames', len(list(FRAMES)))
