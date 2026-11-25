# Palette ramps for the painted cards (VFXP, 25 Nov). One row per owner: the nine schools (the owner's 25 Nov 02:1x mapping = W1a's 鼎
# pigments, art/tools/ding_blender.py ACCENTS, CONFIG.SCHOOLS order), the apex (water-blue, art/viewer/apex_mat.js WATER), the rebels
# (olive, umber, madder: art/FIXA-REPORT.md PATCH_COL, non-school), and neutral rows for the guard, bronze pieces, healing and ash.
# A card's grey value v (0..1) is looked up along its row: stops at v = 0, .25, .5, .75, 1 are deep, dark, pigment, light, pale.
import numpy as np

# ---- CONFIG ----
# Row order of the ramp texture (the game passes the row index per card).
ROWS = [
    # effects only (owner 25 Nov, the look-alike pairs): ru a browner ochre (#94622c, apart from dao gold), za the cooler banner silver
    # #b2bccb with a cool white end (PALE_ROW), apex a brighter cyan-leaning water-blue (#2ea8e8, apart from nong azurite); the 鼎 and suits keep W1a's.
    ('ru', '#94622c'), ('dao', '#e2b84a'), ('fa', '#d9d2c3'), ('mo', '#a8321e'), ('yinyang', '#1a1614'), ('za', '#b2bccb'),
    ('ming', '#5b3f8c'), ('zongheng', '#2f8a5c'), ('nong', '#2e5a9c'),
    # apex Tiger Demon and its cubs/minions (owner 25 Nov 02:2x: apex glow water-blue; brighter, cyan-leaning on the effects, owner 25 Nov)
    ('apex', '#2ea8e8'),
    # 反贼 rebels: olive, umber, madder (non-school; variant i wears [i % 3])
    ('rebel_olive', '#6f6a34'), ('rebel_umber', '#6a4a32'), ('rebel_madder', '#8e5a52'),
    # 皇家 guard: iron (no school, no rebel colour; a cool dark grey that the pale stops keep readable)
    ('guard', '#6e737a'),
    # bronze pieces (giants, guardian beasts, statue, vats): the brass trim sheet hue (bronze_trim_brass, hue 32)
    ('bronze', '#c9a050'),
    # healing at the 鼎 / altars and boons (jade, not the old neon altar green)
    ('jade', '#5e9c7c'),
    # 门海 vat water (CONFIG.PIECES2.colors.water)
    ('water', '#2a6a9a'),
    # smoke, dust and ash of the burning wings
    ('ash', '#8c8a86'),
]
# Endpoints the dark and light stops mix toward (OKLab), and how far.
DEEP, PALE = '#0e0b0a', '#fffaf0'
MIX = {'K': 0.85, 'D': 0.45, 'L': 0.5, 'P': 0.85}
# Rows whose light and pale stops mix toward their own white (effects only; owner 25 Nov: separate the look-alike pairs).
PALE_ROW = {'za': '#e6eefa'}
# Width of the ramp texture (samples along v).
WIDTH = 64

def hex2rgb(h): h = h.lstrip('#'); return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255
def s2l(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def l2s(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566], [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099], [0.0259040371, 0.7827717662, -0.8086757660]])
def oklab(rgb_s):
    l = s2l(np.asarray(rgb_s, float)) @ M1.T; return np.cbrt(l) @ M2.T
def from_oklab(lab):
    l = np.asarray(lab) @ np.linalg.inv(M2).T; return l2s((l ** 3) @ np.linalg.inv(M1).T)

def stops(hexc, pale=None):
    p = oklab(hex2rgb(hexc)); d = oklab(hex2rgb(DEEP)); w = oklab(hex2rgb(pale or PALE))
    return [p + (d - p) * MIX['K'], p + (d - p) * MIX['D'], p, p + (w - p) * MIX['L'], p + (w - p) * MIX['P']]

def ramp_rgb(hexc, n=WIDTH, pale=None):
    S = stops(hexc, pale); out = []
    for i in range(n):
        v = i / (n - 1) * 4; k = min(3, int(v)); u = v - k; out.append(from_oklab(S[k] + (S[k + 1] - S[k]) * u))
    return np.array(out)

def ramp_table():
    return np.stack([ramp_rgb(r[1], pale=PALE_ROW.get(r[0])) for r in ROWS])  # rows x WIDTH x 3, sRGB 0..1

def lut(row):
    """256-entry sRGB lookup for value bytes (for previews)."""
    r = ramp_table()[row]; x = np.linspace(0, 1, WIDTH); v = np.linspace(0, 1, 256)
    return np.stack([np.interp(v, x, r[:, c]) for c in range(3)], -1)
