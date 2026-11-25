# Face masks round 2 (FACES worker; owner GO 25 Nov 10:47, order 10:52): the mask shapes, pure Python (no bpy), used by faces_sample.py.
# Method (owner's armour-suit kit, technique only, re-implemented): ONE continuous sculpted shell per mask, its relief a height function
# over the head wrap, cut by marching squares over a signed field (outline, eye slits, mouth); a pale or dark backing sits deep behind the
# cuts, joined to the shell by walls, so the slits read as sockets, not paint. Guard 卒 zu and giant 00 only (suit 法 fa moved to SUITS).
# Mask space: s across (-1 left .. 1 right, share of the face half-width fx(t)); t up (0 chin .. 1 top of the face span).
# Heights are in units of the face half-width at the eye line, pushed forward. Fields are in t units (positive = metal, negative = cut).
import math

# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Per group: s half-range of the shell domain, t range, grid columns and rows at full detail (rows are packed around the eye band).
DOMAIN = {'zu': (1.0, -0.12, 1.06, 14, 14), 'g00': (1.2, -0.2, 1.45, 44, 44)}
# t of the eye band centre and its half-width, where grid rows are packed (share of rows packed there).
EYE_BAND = {'zu': (0.56, 0.12, 0.45), 'g00': (0.56, 0.14, 0.35)}
# Metres per s unit / metres per t unit (set by the builder from the head; only scales s into t units for the fields).
ASPECT = {'zu': 0.5, 'g00': 0.65}
# How far the backing sits behind the shell, height units (also the wall depth of every cut edge and the outline).
DEPTH = {'zu': 0.16, 'g00': 0.2}
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


# ---- guard 卒 zu: broad brutal mask, flat brow shelf, angry slits, flat wide nose, jagged grimace ---------------------------------------
def zu_eye_t(a): return 0.56 + 0.16 * (a - 0.36)
def zu_mouth_t(a): return 0.16 + 0.05 * a


def zu_holes(s, t):
    """signed field of the cuts only (negative inside a cut): two angry eye slits and a jagged grimace."""
    a = abs(s); A = ASPECT['zu']
    u, v = (a - 0.36) * A, t - zu_eye_t(a)
    taper = 0.055 * (1 - 0.55 * clamp(abs(a - 0.36) / 0.2))
    eye = (math.hypot(u / (0.2 * A), v / taper) - 1) * taper
    mouth = 1.0
    if a < 0.46:
        mouth = abs(t - (zu_mouth_t(a) + 0.018 * tri_wave(a, 0.115))) - 0.028 * (1 - (a / 0.46) ** 2)
    return min(eye, mouth)


def zu_field(s, t):
    a = abs(s); A = ASPECT['zu']
    jaw = -0.06 + 0.12 * a ** 3
    out = min((0.98 - a) * A, 1.0 - t, t - jaw)
    return min(out, zu_holes(s, t))


def zu_height(s, t):
    a = abs(s); d = 0.0
    d += 0.17 * sstep(0.62, 0.68, t) * (1 - sstep(0.8, 0.92, t)) * (1 - sstep(0.82, 0.98, a))        # flat brow shelf, sharp underside
    d -= 0.05 * tent((t - 0.56) / 0.1)                                                                  # eye band set back under it
    nz = sstep(0.28, 0.33, t) * (1 - sstep(0.58, 0.65, t))
    d += (0.13 + 0.07 * (1 - clamp((t - 0.3) / 0.3))) * nz * (1 - sstep(0.1, 0.17, a))                # flat wide nose wedge
    d += 0.08 * (1 - sstep(0.6, 0.9, a)) * sstep(0.26, 0.32, t) * (1 - sstep(0.46, 0.52, t))           # cheek planes
    d += 0.07 * (1 - sstep(0.42, 0.62, a)) * tent((t - 0.16) / 0.13)                                  # mouth guard bulge
    d += 0.04 * (1 - sstep(0.5, 0.7, a)) * (1 - sstep(-0.02, 0.06, t))                                  # square chin
    d -= 0.06 * sstep(0.8, 1.0, a)                                                                      # sides turn back
    return d


# ---- giant 00: colossal taotie-like mask wider than the head, horned brow corners, round deep sockets, fanged snarl ----------------------
def g_top(a): return 1.04 + 0.36 * sstep(0.55, 1.2, a)
def g_eye_t(a): return 0.56 + 0.14 * (a - 0.36)
def g_mouth_t(a): return 0.13 + 0.13 * a * a


def g00_holes(s, t):
    a = abs(s); A = ASPECT['g00']
    u, v = (a - 0.37) * A, t - g_eye_t(a)
    eye = (math.hypot(u / (0.19 * A), v / 0.085) - 1) * 0.085
    mouth = 1.0
    if a < 0.62:
        mouth = abs(t - (g_mouth_t(a) + 0.02 * tri_wave(a, 0.13))) - 0.04 * (1 - (a / 0.62) ** 2)
    return min(eye, mouth)


def g00_field(s, t):
    a = abs(s); A = ASPECT['g00']
    jaw = -0.17 + 0.14 * a * a
    out = min((1.18 - a) * A, g_top(a) - t, t - jaw)
    return min(out, g00_holes(s, t))


def g00_height(s, t):
    a = abs(s); d = 0.0
    d += 0.26 * tent(seg_dist(a, t, 0.03, 0.68, 0.8, 0.92) / 0.075)                                       # V brow ridges into the horns
    d += 0.15 * tent(s / 0.05) * sstep(0.66, 0.72, t)                                                       # central flange up the forehead
    d += 0.26 * g(s / 0.17) * g((t - 0.35) / 0.08)                                                          # broad nose bulb
    d += 0.13 * tent(s / 0.1) * sstep(0.36, 0.42, t) * (1 - sstep(0.6, 0.68, t))                            # nose bridge
    d += 0.16 * g((a - 0.62) / 0.18) * g((t - 0.36) / 0.12)                                                 # cheek masses
    r = math.hypot((a - 0.37) / 0.19, (t - g_eye_t(a)) / 0.085)
    d += 0.08 * tent((r - 1.25) / 0.35)                                                                     # raised socket rims
    d += 0.09 * g(s / 0.42) * g((t + 0.05) / 0.09)                                                          # heavy lower jaw
    d -= 0.28 * sstep(0.88, 1.18, a)                                                                        # flaring wings sweep back
    return d


SHAPES = {'zu': (zu_height, zu_field, zu_holes), 'g00': (g00_height, g00_field, g00_holes)}


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
