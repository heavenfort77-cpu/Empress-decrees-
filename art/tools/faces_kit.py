# Face options sample (FACES worker, owner 25 Nov 09:44 "i hate the face"): shared face layout for faces_sample.py (Blender) and
# faces_tex.py (klad textures). Pure Python, no bpy. A face is a patch over the front of a head: s = across (-1 left .. 1 right, share of
# the face half-width Fx(t)), t = up (0 chin .. 1 top of the face area). Feature displacements are in units of the face half-width at the
# eye line, pushed forward (design f). Texture space of painted faces (C, D): u = 0.5 + 0.5 s, v = t (image row from the top = (1 - t) H).
# Own designs; Qin terracotta faces and Warring States bronze masks are reference for technique only.
import math

# ---- CONFIG -------------------------------------------------------------------------------------------------------------------------
# Landmarks as a share of the face height (chin 0, top of the face area 1): mouth line, nose base, eye line, brow line.
T_MOUTH, T_NOSE, T_EYE, T_BROW = 0.2, 0.34, 0.6, 0.73
# Eye centre across the face (share of the half-width) and eye half-length (share of the half-width).
S_EYE, S_EYE_HALF = 0.36, 0.17
# Superellipse exponent of the head wrap under the face.
N_WRAP = 2.3
# Widest share of the face patch (stops short of the side of the head).
S_MAX = 0.97
# Jaw: half-width share at the chin, rising to 1 by JAW_T.
JAW0, JAW_T = 0.74, 0.42
# Visor (option B) bands: (bottom t, top t) from the top down; the eye slit shows between the first and second band.
VISOR_BANDS = [(0.76, 1.03), (0.42, 0.64), (0.2, 0.46), (-0.03, 0.24)]
# Visor band lip: how far each band's lower edge stands proud, share of the half-width.
VISOR_LIP = 0.07


def g(x): return math.exp(-x * x)
def tent(x): return max(0.0, 1.0 - abs(x))
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def sstep(a, b, x): u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u)
def jaw(t): return JAW0 + (1 - JAW0) * sstep(0.0, JAW_T, t)


def brow_t(s):
    """option A brow line: a stern V (lower at the centre, rising outward)."""
    return T_BROW - 0.05 + 0.09 * abs(s)


def feat_A(s, t):
    """bronze war mask: hard planes. Wedge nose, V brow bar, recessed eye plane, cheek ridge, mouth bar, raised border."""
    a = abs(s); d = 0.0
    nose_t = sstep(T_NOSE - 0.04, T_NOSE, t) * (1 - sstep(0.7, 0.76, t))
    d += (0.13 + 0.15 * (1 - sstep(T_NOSE, 0.7, t))) * nose_t * max(0.0, 1 - a / (0.1 + 0.06 * (1 - sstep(T_NOSE, 0.7, t))))
    tb = brow_t(s)
    d += 0.11 * tent((t - tb) / 0.055) * (1 - sstep(0.78, 0.9, a))
    eye = sstep(0.12, 0.17, a) * (1 - sstep(0.62, 0.68, a)) * sstep(T_EYE - 0.1, T_EYE - 0.07, t) * (1 - sstep(tb - 0.06, tb - 0.035, t))
    d -= 0.05 * eye
    # cheek ridge: a line from (0.62, 0.5) down to (0.3, 0.22)
    px, py, qx, qy = 0.62, 0.5, 0.3, 0.22
    k = clamp(((a - px) * (qx - px) + (t - py) * (qy - py)) / ((qx - px) ** 2 + (qy - py) ** 2))
    dist = math.hypot(a - (px + k * (qx - px)), t - (py + k * (qy - py)))
    d += 0.05 * tent(dist / 0.07)
    d -= 0.05 * tent((t - T_MOUTH) / 0.025) * (1 - sstep(0.26, 0.32, a))
    d += 0.035 * tent((t - T_MOUTH - 0.05) / 0.035) * (1 - sstep(0.28, 0.34, a))
    d += 0.04 * tent((t - 0.06) / 0.08) * (1 - sstep(0.28, 0.38, a))
    d += 0.035 * tent((a - 0.95) / 0.05) + 0.03 * tent((t - 0.98) / 0.04)
    return d


def feat_C(s, t):
    """a calm human face (terracotta-warrior reference for proportion only): nose, brow, sockets, eyeballs, cheeks, lips, chin."""
    a = abs(s); d = 0.0
    up = 1 - sstep(T_NOSE, T_BROW, t)
    d += (0.1 + 0.22 * up) * sstep(T_NOSE - 0.06, T_NOSE, t) * (1 - sstep(T_BROW - 0.02, T_BROW + 0.06, t)) * g(s / (0.09 + 0.07 * up))
    d += 0.06 * g((a - 0.13) / 0.06) * g((t - T_NOSE - 0.02) / 0.04)
    d += 0.07 * g((t - T_BROW) / 0.045) * (1 - sstep(0.6, 0.85, a))
    d -= 0.09 * g((a - S_EYE) / 0.16) * g((t - T_EYE) / 0.07)
    d += 0.035 * g((a - S_EYE) / 0.1) * g((t - T_EYE) / 0.035)
    d += 0.05 * g((a - 0.52) / 0.16) * g((t - 0.44) / 0.1)
    d += 0.06 * g(s / 0.26) * g((t - T_MOUTH) / 0.06) - 0.035 * math.exp(-(s / 0.24) ** 4) * g((t - T_MOUTH) / 0.014)
    d += 0.02 * g(s / 0.08) * g((t - T_MOUTH - 0.07) / 0.04)
    d += 0.05 * g(s / 0.25) * g((t - 0.05) / 0.06)
    d -= 0.03 * g((a - 0.75) / 0.12) * g((t - 0.72) / 0.12)
    return d


def feat_D(s, t):
    """lacquer mask: smooth and calm, flatter than C, a soft rim at the edge."""
    a = abs(s); d = 0.0
    up = 1 - sstep(T_NOSE, T_BROW, t)
    d += (0.07 + 0.13 * up) * sstep(T_NOSE - 0.05, T_NOSE, t) * (1 - sstep(T_BROW - 0.02, T_BROW + 0.06, t)) * g(s / (0.1 + 0.05 * up))
    d += 0.05 * g((t - T_BROW) / 0.05) * (1 - sstep(0.6, 0.85, a))
    d -= 0.05 * g((a - S_EYE) / 0.16) * g((t - T_EYE) / 0.07)
    d += 0.03 * g(s / 0.24) * g((t - T_MOUTH) / 0.05)
    d += 0.03 * g((a - 0.95) / 0.04) + 0.025 * g((t - 0.99) / 0.03)
    return d


FEAT = {'A': feat_A, 'C': feat_C, 'D': feat_D, 'B': lambda s, t: 0.0}


def slit_t(s):
    """centre line of an eye slit (A, D): rises toward the outer end."""
    return T_EYE + 0.025 * (abs(s) - S_EYE) / S_EYE_HALF
