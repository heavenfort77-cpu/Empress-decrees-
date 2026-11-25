# Face masks round 2 (FACES worker; owner GO 25 Nov 10:47, order 10:52): the mask shapes, pure Python (no bpy), used by faces_sample.py.
# Method (owner's armour-suit kit, technique only, re-implemented): ONE continuous sculpted shell per mask, its relief a height function
# over the head wrap, cut by marching squares over a signed field (outline, eye slits, mouth); a pale or dark backing sits deep behind the
# cuts, joined to the shell by walls, so the slits read as sockets, not paint. Guard 卒 zu and giant 00 only (suit 法 fa moved to SUITS).
# Mask space: s across (-1 left .. 1 right, share of the face half-width fx(t)); t up (0 chin .. 1 top of the face span).
# Heights are in units of the face half-width at the eye line, pushed forward. Fields are in t units (positive = metal, negative = cut).
import math

# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Per group: s half-range of the shell domain, t range, grid columns and rows at full detail (rows are packed around the eye band).
DOMAIN = {'zu': (0.96, -0.14, 1.03, 12, 13), 'g00': (1.2, -0.32, 1.1, 44, 44)}
# t of the eye band centre and its half-width, where grid rows are packed (share of rows packed there).
EYE_BAND = {'zu': (0.585, 0.1, 0.4), 'g00': (0.4, 0.3, 0.45)}
# Metres per s unit / metres per t unit (set by the builder from the head; only scales s into t units for the fields).
ASPECT = {'zu': 0.5, 'g00': 0.65}
# How far the backing sits behind the shell, height units (also the wall depth of every cut edge and the outline).
DEPTH = {'zu': 0.09, 'g00': 0.14}
# Eyeball bulge of the backing behind the eye slits, height units at the eye centre (round 3: the eyes must show from the play camera).
BULGE = {'zu': 0.14, 'g00': 0.2}
# Backing margin beyond each cut, t units (so the wall always lands on the backing).
BACK_MARGIN = {'zu': 0.03, 'g00': 0.03}


def g(x): return math.exp(-x * x)
def tent(x): return max(0.0, 1.0 - abs(x))
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def sstep(a, b, x): u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u)
def seg_dist(px, py, ax, ay, bx, by):
    k = clamp(((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2))
    return math.hypot(px - ax - k * (bx - ax), py - ay - k * (by - ay))
def tri_wave(x, period): return abs((x / period) % 2 - 1) * 2 - 1


# ---- guard 卒 zu (concept face_6204, run 45537264508: a cast war face set in the hood rim): stern human war face in black lacquer, angry
# brows meeting low over the nose, almond slits, long straight nose, high cheekbones, upturned Qin moustache and chin tuft in relief --------
def zu_eye_t(a): return 0.585 + 0.09 * (a - 0.36)


def zu_eye_r(s, t): a = abs(s); return math.hypot((a - 0.37) / 0.19, (t - zu_eye_t(a)) / 0.08)


def zu_holes(s, t):
    """signed field of the cuts only (negative inside a cut): two almond eye slits (inner end pressed down by the brow)."""
    a = abs(s); A = ASPECT['zu']
    u, v = (a - 0.37) * A, t - zu_eye_t(a)
    hh = 0.075 * (1 - 0.45 * clamp(abs(a - 0.37) / 0.19)) * (1 - 0.2 * (a < 0.37))
    return (math.hypot(u / (0.19 * A), v / hh) - 1) * hh


def zu_field(s, t):
    a = abs(s); A = ASPECT['zu']
    jaw = -0.04 + 0.3 * a * a
    jaw = min(jaw, -0.13 + 0.9 * a) if a < 0.12 else jaw                       # chin tuft hangs below the jaw
    out = min((0.95 - a) * A, 1.0 - t, t - jaw)
    return min(out, zu_holes(s, t))


def zu_height(s, t):
    a = abs(s); d = 0.0
    d += 0.06 * (1 - sstep(0.75, 0.98, t)) * sstep(0.68, 0.8, t) * (1 - sstep(0.6, 0.95, a))         # forehead, set back under the rim
    d += 0.11 * tent(seg_dist(a, t, 0.05, 0.69, 0.62, 0.78) / 0.055)                                    # angry brows, inner ends low
    d -= 0.04 * tent(s / 0.025) * sstep(0.66, 0.7, t) * (1 - sstep(0.76, 0.82, t))                    # frown crease between them
    r = math.hypot((a - 0.37) / 0.24, (t - zu_eye_t(a)) / 0.11)
    d -= 0.07 * (1 - sstep(0.5, 1.0, r))                                                                  # eye sockets
    up = clamp((t - 0.36) / 0.32)
    d += (0.26 - 0.13 * up) * sstep(0.32, 0.37, t) * (1 - sstep(0.66, 0.71, t)) * tent(s / (0.11 - 0.035 * up))   # long straight nose
    d += 0.07 * g((a - 0.12) / 0.05) * g((t - 0.355) / 0.035)                                            # nostril wings
    d += 0.09 * tent(seg_dist(a, t, 0.72, 0.5, 0.36, 0.44) / 0.09)                                       # high cheekbones
    d -= 0.06 * g((a - 0.5) / 0.15) * g((t - 0.27) / 0.08)                                                # hollow cheeks
    d += 0.08 * tent(seg_dist(a, t, 0.04, 0.3, 0.22, 0.265) / 0.035) + 0.07 * tent(seg_dist(a, t, 0.22, 0.265, 0.36, 0.305) / 0.03)  # moustache, tips up
    d -= 0.05 * tent((t - (0.21 - 0.12 * a * a)) / 0.02) * (1 - sstep(0.18, 0.24, a))                   # closed grim mouth
    d += 0.03 * g(s / 0.16) * g((t - 0.18) / 0.025)                                                       # lower lip
    d += 0.08 * tent(s / 0.07) * sstep(-0.12, -0.04, t) * (1 - sstep(0.12, 0.17, t))                   # chin tuft
    d += 0.05 * g(s / 0.28) * g((t - 0.03) / 0.07)                                                        # chin
    d -= 0.12 * sstep(0.72, 0.95, a)                                                                      # sides turn back into the hood
    return d


# ---- giant 00 (concept face_6303, run 45537264508: a cast temple-guardian war mask): mask wider than the head with cheek flanges hanging
# past the jaw, furrowed V brows over wide glaring slits, broad bulb nose, wide snarl cut with a row of teeth, ridged beard, forehead flange -----
def g_top(a): return 1.02 + 0.06 * a
def g_eye_t(a): return 0.57 + 0.12 * (a - 0.37)
def g_mouth_t(a): return 0.15 + 0.06 * a * a


def g00_eye_r(s, t): a = abs(s); return math.hypot((a - 0.38) / 0.21, (t - g_eye_t(a)) / 0.1)


def g00_holes(s, t):
    a = abs(s); A = ASPECT['g00']
    u, v = (a - 0.38) * A, t - g_eye_t(a)
    hh = 0.09 * (1 - 0.4 * clamp(abs(a - 0.38) / 0.2))
    eye = (math.hypot(u / (0.21 * A), v / hh) - 1) * hh
    mouth = 1.0
    if a < 0.52:
        top = g_mouth_t(a) + 0.055 - 0.03 * max(0.0, tri_wave(a, 0.09))      # upper teeth hang into the cut
        bot = g_mouth_t(a) - 0.06 + 0.03 * max(0.0, -tri_wave(a + 0.045, 0.09))
        mouth = min(top - t, t - bot, (0.52 - a) * A)
        mouth = -mouth
    return min(eye, mouth)


def g00_field(s, t):
    a = abs(s); A = ASPECT['g00']
    jaw = -0.12 + 0.12 * a * a
    jaw -= 0.17 * sstep(0.78, 1.05, a)                                     # cheek flanges hang past the jaw
    out = min((1.18 - a) * A, g_top(a) - t, t - jaw)
    return min(out, g00_holes(s, t))


def g00_height(s, t):
    a = abs(s); d = 0.0
    d += 0.2 * tent(seg_dist(a, t, 0.05, 0.71, 0.72, 0.82) / 0.07)                                        # furrowed V brows
    d += 0.05 * tent(seg_dist(a, t, 0.1, 0.8, 0.6, 0.88) / 0.04)                                           # second furrow above
    d += 0.14 * tent(s / 0.06) * sstep(0.74, 0.8, t)                                                        # forehead flange up to the rim
    r = math.hypot((a - 0.38) / 0.26, (t - g_eye_t(a)) / 0.13)
    d += 0.08 * tent((r - 1.0) / 0.35) * (t < g_eye_t(a))                                                  # lower lids / socket rims
    d += 0.28 * g(s / 0.19) * g((t - 0.36) / 0.08)                                                          # broad bulb nose
    d += 0.13 * tent(s / 0.11) * sstep(0.38, 0.44, t) * (1 - sstep(0.62, 0.7, t))                           # nose bridge
    d += 0.17 * g((a - 0.62) / 0.17) * g((t - 0.36) / 0.12)                                                 # cheek masses
    d += 0.08 * tent((t - (g_mouth_t(a) + 0.075)) / 0.03) * (1 - sstep(0.45, 0.58, a))                     # upper lip roll over the snarl
    d += 0.1 * g(s / 0.42) * g((t + 0.02) / 0.07) * (0.7 + 0.3 * abs(math.cos(s * 22)))                   # ridged beard on the jaw
    d -= 0.12 * sstep(0.95, 1.18, a)                                                                        # cheek flanges sweep back
    return d


SHAPES = {'zu': (zu_height, zu_field, zu_holes), 'g00': (g00_height, g00_field, g00_holes)}
EYE_R = {'zu': zu_eye_r, 'g00': g00_eye_r}
# Eye probe (s, t) per group: the eyeball centre.
EYE_C = {'zu': (0.37, 0.585), 'g00': (0.38, 0.57)}


def bulge(group, s, t):
    """backing relief: the eyeball under each eye slit, domed toward the slit."""
    r = EYE_R[group](s, t); return BULGE[group] * max(0.0, 1 - r * r)


def axes(group, k=1.0):
    """grid columns (s) and rows (t) for marching squares; rows packed around the eye band, columns denser at the centre third."""
    S, t0, t1, nx, ny = DOMAIN[group]; nx = max(8, int(round(nx * k / 2)) * 2); ny = max(8, int(round(ny * k)))
    te, hw, share = EYE_BAND[group]
    nb = max(3, round(ny * share)); rest = ny - nb
    a, b = te - hw, te + hw
    lo = max(1, round(rest * (a - t0) / ((a - t0) + (t1 - b))))
    T = [t0 + (a - t0) * i / lo for i in range(lo)] + [a + (b - a) * i / nb for i in range(nb)] + [b + (t1 - b) * i / (rest - lo) for i in range(rest - lo + 1)]
    U = [S * math.copysign(abs(w) ** 1.15, w) for w in [-1 + 2 * i / nx for i in range(nx + 1)]]
    return U, T
