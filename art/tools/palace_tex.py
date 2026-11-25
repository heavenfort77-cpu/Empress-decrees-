#!/usr/bin/env python3
"""Palace texture generator for klad (Empress Decrees, sample 01: hall floor, hall wall, pillar, door, stone lion).

Writes one klad `apply` op file per texture: seeded strokes painted in klad (the art is klad paint; this script only places the marks).
Strokes that cross an edge are repeated one tile over on the far side, so a texture wraps without a seam (wrapX / wrapY per texture).

History reference (sources in art/REFERENCES.md):
- floor: 丹地, the cinnabar-painted, pebble-burnished floor of the main hall at 咸阳宫 site No. 1;
- wall: rammed earth under lime plaster, a white-ground band with black lozenges (咸阳宫 No. 1), Qin black dado and cornice, red rules;
- pillar: timber pillar in black lacquer with vermilion bands and cloud scrolls (Qin lacquerware palette), a bronze foot collar;
- door: black lacquer leaves, bronze bands and a bronze mask holding a ring (铺首衔环, Warring States / Han type; our own mask);
- lion stone: grey limestone with chisel marks (stone lions are post-Qin; kept as designed, in plain stone).

Usage: python3 palace_tex.py OUTDIR [SIZE] [NAMES]   (SIZE 1024 desktop, 512 phone; NAMES: comma list of floor,wall,pillar,door,lion_stone)
"""
import json, math, random, sys

OUT = sys.argv[1]
# CONFIG (FIXB 25 Nov, owner 02:1x-02:2x: plaster 'can change but must align to surroundings')
# Plaster value scale on the hall wall's lime-plaster colours (base, mottling, trowel strokes, stains; not the frieze, rules or dado).
# 1.0 = the approved round 2 wall (mean lum 169 in rows 170-750); the env PLASTER_K paints a candidate for the side-by-side only.
PLASTER_K = float(__import__('os').environ.get('PLASTER_K', '1.0'))


def pk(h):
    """a plaster colour scaled by PLASTER_K (unchanged string at 1.0, so the approved ops stay byte-identical)."""
    if PLASTER_K == 1.0: return h
    return '#' + ''.join('%02x' % min(255, round(int(h[i:i + 2], 16) * PLASTER_K)) for i in (1, 3, 5))
# COLOUR 25 Nov (owner 13:1x: 'colour clear, not one mess when a character is on it'; hall floor repainted calmer and less saturated, replaces
# the approved round 2 floor: old texture, bundle and generator kept in art/round2/). Rules and maths: art/Colour-Clarity-Study.md.
# Hall floor base colour: cinnabar 丹地 at a mid value (round 2 of COLOUR, lead verdict 25 Nov: red again, not salmon; hue 8 deg, saturation
# about 0.52, texture relative luminance about 0.185 = 0.14 on screen).
FLOOR_BASE = '#b26155'
# Hall floor value gain on the base and every mark (linear light). The runner's calibration (art/tools/floor_calibrate.py) sets the env; the
# default is the value the shipped texture was painted with.
FLOOR_G = float(__import__('os').environ.get('FLOOR_G', '1.0369'))
# Hall floor mark contrast (1.0 = marks at the tones written in floor(); lower = calmer). Calibrated to the own-marks rule (p95/p5 <= 1.30).
FLOOR_C = float(__import__('os').environ.get('FLOOR_C', '0.2742'))
# Hall floor broad tone-blot opacity scale (lower = less cloud at the 0.5 m scale, shorter stroke correlation).
FLOOR_B = float(__import__('os').environ.get('FLOOR_B', '0.36'))
# Hall floor pebble-burnish dab count.
FLOOR_N = int(__import__('os').environ.get('FLOOR_N', '1910'))
# Hall floor broad burnish drift (floor-only round, lead 25 Nov: wear patches rejected as confetti): amplitude of the large soft value
# drift across 0.5-2 m, like polished cinnabar worn by feet. It carries the luminance sd the palace study asks for (tex_check.py: sd >= 8)
# while the marks inside any 1 m stay calm.
FLOOR_D = float(__import__('os').environ.get('FLOOR_D', '6.0'))
# Hall floor fine burnish scratches (thin dark hairlines; they keep the brush-scale run of tex_check.py inside 4-15 cm).
FLOOR_H = int(__import__('os').environ.get('FLOOR_H', '1600'))
# Colour gain for candidates of other textures (linear light on the background and every stroke colour; 1.0 = approved ops byte-identical).
TEX_GAIN = float(__import__('os').environ.get('TEX_GAIN', '1.0'))
# Mark contrast for candidates of other textures: every stroke colour pulled toward the background colour in linear light (1.0 = unchanged).
TEX_CONTRAST = float(__import__('os').environ.get('TEX_CONTRAST', '1.0'))


def _lin(v): v /= 255.0; return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
def _srgb(l): l = min(1.0, max(0.0, l)); return round(255 * (12.92 * l if l <= 0.0031308 else 1.055 * l ** (1 / 2.4) - 0.055))


def gain(h, g, toward=None, k=1.0):
    """a colour scaled by g in linear light, after pulling it toward colour `toward` by 1 - k (unchanged string at g 1.0, k 1.0)."""
    if (g == 1.0 and k == 1.0) or not h.startswith('#'): return h
    v = [_lin(int(h[i:i + 2], 16)) for i in (1, 3, 5)]
    if toward and k != 1.0: b = [_lin(int(toward[i:i + 2], 16)) for i in (1, 3, 5)]; v = [q + (x - q) * k for x, q in zip(v, b)]
    return '#' + ''.join('%02x' % _srgb(x * g) for x in v)
S = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
K = S / 1024.0  # every coordinate below is written for 1024 px and scaled


class Tex:
    def __init__(self, name, bg, wrap_x, wrap_y, seed):
        self.name, self.bg0, self.bg, self.wx, self.wy = name, bg, gain(bg, TEX_GAIN), wrap_x, wrap_y
        self.r = random.Random(seed)
        self.ops = []
        self.stage = 0  # paint stage for the passes strip: 0 base, 1 tone, 2 marks, 3 detail

    def stroke(self, pts, brush, size, color, opacity=1.0, pressure=None, taper=None, flow=None, wrap=True):
        """pts in 1024 space; repeated across wrapped edges when the stroke leaves the tile (wrap False: strokes that already span the tile)."""
        pts = [(x * K, y * K) for x, y in pts]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        pad = size * K
        offs_x = [0]; offs_y = [0]
        if self.wx and wrap:
            if min(xs) - pad < 0: offs_x.append(S)
            if max(xs) + pad > S: offs_x.append(-S)
        if self.wy and wrap:
            if min(ys) - pad < 0: offs_y.append(S)
            if max(ys) + pad > S: offs_y.append(-S)
        seed = self.r.randrange(1, 1 << 30)
        for ox in offs_x:
            for oy in offs_y:
                d = 'M' + ' L'.join(f'{x + ox:.1f} {y + oy:.1f}' for x, y in pts)
                op = {"op": "stroke", "layer": "l1", "brush": brush, "size": round(size * K, 2), "color": gain(color, TEX_GAIN, self.bg0, TEX_CONTRAST), "opacity": opacity, "path": d, "seed": seed}
                if pressure: op["pressure"] = pressure
                if taper is not None: op["taper"] = taper
                if flow is not None: op["flow"] = flow
                self.ops.append((self.stage, op))

    def wobble(self, x0, y0, x1, y1, n=6, amp=4):
        pts = []
        for i in range(n + 1):
            t = i / n
            pts.append((x0 + (x1 - x0) * t + self.r.uniform(-amp, amp), y0 + (y1 - y0) * t + self.r.uniform(-amp, amp)))
        return pts

    def blot(self, cx, cy, rad, brush, size, color, opacity, n=5):
        """a small cluster of short strokes (a patch of stain or wear)."""
        for _ in range(n):
            a = self.r.uniform(0, math.tau); L = self.r.uniform(0.3, 1) * rad
            x0, y0 = cx + self.r.uniform(-rad, rad) * 0.6, cy + self.r.uniform(-rad, rad) * 0.6
            self.stroke(self.wobble(x0, y0, x0 + math.cos(a) * L, y0 + math.sin(a) * L, 3, rad * 0.15), brush, size, color, opacity)

    def write(self):
        with open(f'{OUT}/{self.name}.jsonl', 'w') as f:
            for st, op in self.ops: f.write(json.dumps(op, ensure_ascii=False) + '\n')
        # passes strip: op counts where one paint stage block ends (paint order kept), labelled by the stage
        cuts, names = [], ['base', 'tone', 'marks', 'detail']
        for i, (st, op) in enumerate(self.ops):
            if i + 1 == len(self.ops) or self.ops[i + 1][0] != st: cuts.append([names[st], i + 1])
        with open(f'{OUT}/{self.name}.passes.json', 'w') as f: json.dump(cuts, f)
        with open(f'{OUT}/{self.name}.bg', 'w') as f: f.write(self.bg)
        return len(self.ops)


def band(t, y0, y1, color, brush='flat-bristle', size=60, opacity=1.0, step=None, jitter=3):
    """a horizontal band painted with overlapping horizontal strokes across the full width (wraps)."""
    step = step or size * 0.6
    # Each band stroke starts at a random x and runs 1100 px, past the tile edge; its wrapped copy finishes it on the other side, so the
    # tile edge falls mid-stroke (round 2: full-width strokes left a seam where their start met their end).
    if brush != 'marker':  # a solid marker pass first, so the band is opaque under the bristle texture
        y = y0 + 6
        while y <= y1 + 2:
            x0 = t.r.uniform(0, 1024)
            t.stroke([(x0, y), (x0 + 1100, y)], 'marker', 14, color, 1.0, taper=[0, 0])
            y += 9
    y = y0 + size / 2 - 4
    while y <= y1 - size / 2 + 6:
        x0 = t.r.uniform(0, 1024)
        t.stroke(t.wobble(x0, y, x0 + 1100, y, 8, jitter), brush, size, color, opacity, taper=[0, 0])
        y += step


def floor():
    # 丹地: cinnabar earth floor, burnished with pebbles; one continuous painted surface (no tiles). 4 m per repeat (256 px/m).
    # Round 4 (COLOUR round 2 and FINAL, 25 Nov, art/Colour-Clarity-Study.md): a mid-value cinnabar floor a black-lacquer figure reads on: texture
    # relative luminance 0.185, saturation 0.50-0.55, own marks p95/p5 <= 1.30, calm broad burnish strokes (shorter and less one-way than
    # round 2), pebble dabs, a broad soft value drift; no grit specks and no pale wear patches (both rejected). Seed 101 kept. Round 2 (value 80, sd 9.1): art/round2/.
    c0 = [_lin(int(FLOOR_BASE[i:i + 2], 16)) * FLOOR_G for i in (1, 3, 5)]
    def col(d, warm=0.0):
        """the base scaled by 1 + FLOOR_C x d in linear light; warm > 0 leans to the earth under the paint (less red)."""
        k = 1 + FLOOR_C * d
        v = [c0[0] * k, c0[1] * k * (1 + warm), c0[2] * k * (1 + warm * 0.6)]
        return '#' + ''.join('%02x' % _srgb(x) for x in v)
    t = Tex('hall_floor', col(0), True, True, 101)
    r = t.r
    t.stage = 1
    drift = [col(-0.30 * FLOOR_D), col(0.34 * FLOOR_D), col(-0.20 * FLOOR_D), col(0.22 * FLOOR_D)]
    for k in range(64):  # broad burnish drift: big soft sponge fields, 0.5-2 m, darker and lighter in turn, same hue
        cx, cy = r.uniform(0, 1024), r.uniform(0, 1024); rad = r.uniform(110, 300); a = r.uniform(0, math.pi); L = r.uniform(0.4, 1.2) * rad
        pts = t.wobble(cx - math.cos(a) * L, cy - math.sin(a) * L, cx + math.cos(a) * L, cy + math.sin(a) * L, 4, rad * 0.2)
        t.stroke(pts, 'sponge', rad, drift[k % 4], r.uniform(0.3, 0.45), pressure=[0.5, 1, 0.5])
    tones = [col(-0.22), col(0.20), col(-0.14), col(0.26)]
    for _ in range(90):  # broad tone variation (kept low: nothing a figure edge can be lost in)
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(60, 160), 'sponge', r.uniform(70, 140), r.choice(tones), r.uniform(0.2, 0.34) * FLOOR_B, 3)
    t.stage = 2
    burn = [col(0.42), col(0.55), col(-0.40)]
    for _ in range(240):  # burnish passes: broad calm strokes, 20-55 cm, a loose common direction (round 2: 80-260 px, one way, read busy)
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); a = r.uniform(-0.7, 0.7); L = r.uniform(55, 140)
        t.stroke(t.wobble(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 5, 3), 'dry-brush', r.uniform(16, 30), r.choice(burn), r.uniform(0.2, 0.34), pressure=[0.3, 1, 0.3])
    dabs = [col(0.45), col(-0.42), col(-0.22), col(0.26)]
    for _ in range(FLOOR_N):  # pebble-burnish dabs, 4-12 cm
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); a = r.uniform(0, math.tau); L = r.uniform(10, 30)
        t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'chalk', r.uniform(6, 11), r.choice(dabs), r.uniform(0.3, 0.45))
    t.stage = 3
    for _ in range(8):  # hairline cracks
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); pts = [(x, y)]
        for _ in range(r.randint(5, 9)):
            x += r.uniform(-30, 30); y += r.uniform(-30, 30); pts.append((x, y))
        t.stroke(pts, 'pencil', 2.4, col(-0.75), 0.6)
    for _ in range(FLOOR_H):  # fine burnish scratches, 3-9 cm, every direction (last, so the count can change without moving a mark above)
        x, y = r.uniform(0, 1024), r.uniform(0, 1024); a = r.uniform(0, math.tau); L = r.uniform(8, 24)
        t.stroke([(x, y), (x + math.cos(a) * L, y + math.sin(a) * L)], 'pencil', 1.8, col(-0.6), r.uniform(0.45, 0.7))
    return t


def wall():
    # 4 m wide x 4 m high (image top = wall top). Black cornice, white-ground band of black lozenges, red rule, lime plaster, red rule, black dado.
    t = Tex('hall_wall', pk('#b9ad95'), True, False, 202)
    r = t.r
    t.stage = 1
    for _ in range(80):  # plaster mottling (round 2: stronger)
        cx, cy = r.uniform(0, 1024), r.uniform(170, 760)
        t.blot(cx, cy, r.uniform(40, 110), 'sponge', r.uniform(50, 110), pk(r.choice(['#9f927a', '#c9bea7', '#a89a80', '#bdb099'])), r.uniform(0.35, 0.55), 3)
    t.stage = 2
    for _ in range(700):  # trowel strokes in the lime plaster, 4-15 cm
        x, y = r.uniform(0, 1024), r.uniform(170, 750); a = r.uniform(-0.6, 0.6); L = r.uniform(25, 80)
        t.stroke(t.wobble(x, y, x + math.cos(a) * L, y + math.sin(a) * L, 3, 2), 'oil', r.uniform(10, 24), pk(r.choice(['#9a8d75', '#d0c5ae', '#a99c83'])), r.uniform(0.4, 0.6))
    t.stage = 3
    for _ in range(26):  # faint drips and water stains from the cornice
        x = r.uniform(0, 1024); y = r.uniform(160, 220)
        t.stroke(t.wobble(x, y, x + r.uniform(-6, 6), y + r.uniform(80, 300), 5, 2), 'soft', r.uniform(8, 18), pk('#8f8068'), r.uniform(0.12, 0.25), pressure=[1, 0.6, 0.1])
    # the band: white ground with two rows of black lozenges (咸阳宫 No. 1: 白地黑色菱形图案)
    band(t, 40, 150, '#d6ccb6', 'flat-bristle', 40, 1.0, 26, 1.5)
    w = 1024 / 16  # 16 lozenges per 4 m
    for row, (yc, hh) in enumerate([(95, 42)]):
        for i in range(16):
            cx = (i + 0.5) * w
            outer = [(cx - w / 2 + 4, yc), (cx, yc - hh), (cx + w / 2 - 4, yc), (cx, yc + hh), (cx - w / 2 + 4, yc)]
            t.stroke(outer, 'marker', 7, '#1b1714', 0.95, taper=[0, 0])
            inner = [(cx - w / 4, yc), (cx, yc - hh / 2), (cx + w / 4, yc), (cx, yc + hh / 2), (cx - w / 4, yc)]
            t.stroke(inner, 'marker', 9, '#1b1714', 0.95, taper=[0, 0])
            for sx in (-1, 1):  # small dots in the gaps between lozenges
                t.stroke([(cx + sx * w / 2, yc - 30), (cx + sx * w / 2 + 0.5, yc - 29)], 'ink', 6, '#1b1714', 0.9, taper=[0, 0])
                t.stroke([(cx + sx * w / 2, yc + 30), (cx + sx * w / 2 + 0.5, yc + 31)], 'ink', 6, '#1b1714', 0.9, taper=[0, 0])
    band(t, 0, 40, '#17120f', 'flat-bristle', 30, 1.0, 14, 1)          # black cornice
    band(t, 150, 162, '#7e271b', 'marker', 12, 1.0, 12, 0.8)          # red rule
    band(t, 760, 772, '#7e271b', 'marker', 12, 1.0, 12, 0.8)          # red rule
    band(t, 772, 1024, '#1a1512', 'flat-bristle', 50, 1.0, 26, 2)     # black lacquer dado
    for _ in range(60):  # lacquer sheen and scuffs on the dado
        x, y = r.uniform(0, 1024), r.uniform(790, 1010)
        t.stroke(t.wobble(x, y, x + r.uniform(40, 160), y + r.uniform(-4, 4), 4, 1.5), 'dry-brush', r.uniform(6, 14), r.choice(['#2e2722', '#262019']), r.uniform(0.3, 0.6))
    for _ in range(25):
        x, y = r.uniform(0, 1024), r.uniform(900, 1020)
        t.stroke([(x, y), (x + r.uniform(-20, 20), y + r.uniform(-6, 6))], 'chalk', 3, '#5a4a3e', 0.4)
    return t


def cloud(t, cx, cy, s, color):
    """one cloud scroll (云纹): an S-curve ending in two curls; our own drawing."""
    pts = []
    for i in range(29):
        a = i / 28
        pts.append((cx - s + 2 * s * a, cy + math.sin(a * math.pi * 2) * s * 0.35))
    t.stroke(pts, 'ink', 7, color, 0.95, taper=[6, 6])
    for end, d in ((-1, 1), (1, -1)):
        ex, ey = cx + end * s, cy
        curl = [(ex + math.cos(a) * s * 0.28 * (1 - a / 9) * d, ey - s * 0.28 * d + math.sin(a) * s * 0.28 * (1 - a / 9)) for a in [k * 0.45 for k in range(16)]]
        t.stroke(curl, 'ink', 6, color, 0.95, taper=[2, 10])


def pillar():
    # Wraps around (two repeats per pillar); spans the pillar height once (image top = pillar top).
    t = Tex('pillar', '#1a1310', True, False, 303)
    r = t.r
    t.stage = 2
    for _ in range(170):  # vertical lacquer brushwork (round 2: broad oil strokes, smooth like lacquer, 4-15 cm across, more contrast; once around)
        x = r.uniform(0, 1024)
        t.stroke(t.wobble(x, r.uniform(110, 400), x + r.uniform(-4, 4), r.uniform(600, 900), 6, 1.5), 'oil', r.uniform(20, 45), r.choice(['#30251e', '#100c0a', '#3a2c23', '#241b16']), r.uniform(0.45, 0.8))
    t.stage = 0
    band(t, 0, 120, '#86281a', 'flat-bristle', 36, 1.0, 20, 1.2)      # vermilion capital band
    for i in range(4):
        cloud(t, (i + 0.5) * 256, 62, 58, '#16110e')
    band(t, 118, 130, '#7a6040', 'marker', 12, 1.0, 12, 0.6)          # bronze-coloured rule
    for x0 in (0, 512):  # thin vermilion lines running down (lacquer decoration)
        for dx in (-10, 10):
            t.stroke([(x0 + 128 + dx, 140), (x0 + 128 + dx, 860)], 'pencil', 3, '#7e271b', 0.55, taper=[0, 0])
    band(t, 870, 960, '#86281a', 'flat-bristle', 30, 1.0, 18, 1.2)    # lower vermilion band
    for i in range(8):
        cx = (i + 0.5) * 128
        t.stroke([(cx - 30, 915), (cx, 892), (cx + 30, 915), (cx, 938), (cx - 30, 915)], 'marker', 6, '#16110e', 0.95, taper=[0, 0])
    band(t, 960, 1024, '#5d4a33', 'flat-bristle', 30, 1.0, 16, 1)     # bronze foot collar
    for _ in range(40):
        x = r.uniform(0, 1024)
        t.stroke([(x, r.uniform(966, 980)), (x + r.uniform(10, 40), r.uniform(966, 980))], 'dry-brush', 5, '#8a7050', 0.5)
        t.stroke([(x, r.uniform(995, 1018)), (x + r.uniform(5, 20), r.uniform(995, 1018))], 'chalk', 5, '#3f5a4c', 0.35)  # verdigris
    return t


def pushou(t, cx, cy, s):
    """our own bronze beast mask holding a ring (铺首衔环 type)."""
    B, H, D = '#7b5f3a', '#b2925e', '#3a2b1a'
    for k in range(7):  # mask body: a broad shield shape filled with strokes
        yy = cy - s * 0.55 + k * s * 0.17
        half = s * (0.75 - abs(k - 2.5) * 0.08)
        t.stroke([(cx - half, yy), (cx + half, yy)], 'flat-bristle', s * 0.22, B, 1.0, taper=[0, 0])
    for sx in (-1, 1):
        horn = [(cx + sx * (s * 0.55 + math.sin(a) * s * 0.25), cy - s * 0.55 - (1 - math.cos(a)) * s * 0.35) for a in [k * 0.25 for k in range(12)]]
        t.stroke(horn, 'ink', s * 0.12, B, 1.0, taper=[4, 14])
        t.stroke([(cx + sx * s * 0.28, cy - s * 0.18), (cx + sx * s * 0.29, cy - s * 0.17)], 'ink', s * 0.2, D, 1.0, taper=[0, 0])   # eye
        t.stroke([(cx + sx * s * 0.28, cy - s * 0.22), (cx + sx * s * 0.285, cy - s * 0.215)], 'ink', s * 0.06, H, 1.0, taper=[0, 0])
        brow = [(cx + sx * s * 0.08, cy - s * 0.34), (cx + sx * s * 0.3, cy - s * 0.42), (cx + sx * s * 0.5, cy - s * 0.3)]
        t.stroke(brow, 'ink', s * 0.05, H, 0.9, taper=[4, 8])
    t.stroke([(cx, cy - s * 0.1), (cx, cy + s * 0.35)], 'ink', s * 0.1, D, 0.9, taper=[0, 6])        # nose ridge
    t.stroke([(cx - s * 0.35, cy + s * 0.3), (cx, cy + s * 0.45), (cx + s * 0.35, cy + s * 0.3)], 'ink', s * 0.06, D, 0.9, taper=[6, 6])
    ring = [(cx + math.cos(a) * s * 0.5, cy + s * 0.95 + math.sin(a) * s * 0.5) for a in [k * math.tau / 40 for k in range(41)]]
    t.stroke(ring, 'ink', s * 0.11, B, 1.0, taper=[0, 0])
    hl = [(cx + math.cos(a) * s * 0.5, cy + s * 0.95 + math.sin(a) * s * 0.5) for a in [math.pi * 1.1 + k * 0.08 for k in range(14)]]
    t.stroke(hl, 'ink', s * 0.04, H, 0.9, taper=[6, 6])


def door():
    # One image over the whole door face (4 m wide x 3.5 m high): two black lacquer leaves, bronze bands, two masks with rings.
    t = Tex('door', '#16110e', False, False, 404)
    r = t.r
    for _ in range(160):  # vertical plank grain under lacquer
        x = r.uniform(0, 1024)
        t.stroke(t.wobble(x, r.uniform(0, 300), x + r.uniform(-3, 3), r.uniform(700, 1024), 6, 1.2), 'flat-bristle', r.uniform(10, 26), r.choice(['#211913', '#1c1511', '#281e17']), r.uniform(0.35, 0.7))
    for x in (256, 768):  # plank seams
        t.stroke([(x, 0), (x, 1024)], 'pencil', 3, '#0c0907', 0.7, taper=[0, 0])
    t.stroke([(512, 0), (512, 1024)], 'marker', 10, '#080605', 1.0, taper=[0, 0])  # the gap between the leaves
    for y0, y1 in ((0, 70), (954, 1024), (480, 520)):  # bronze bands
        band(t, y0, y1, '#6a5234', 'flat-bristle', 24, 1.0, 14, 0.8)
        t.stroke([(0, y0 + 8), (1024, y0 + 8)], 'dry-brush', 6, '#a0814f', 0.6, taper=[0, 0])
    for x0 in (0, 1004):
        t.stroke([(x0 + 10, 0), (x0 + 10, 1024)], 'flat-bristle', 22, '#5e482e', 1.0, taper=[0, 0])
    for cx in (412, 612):
        pushou(t, cx, 590, 70)
    for _ in range(50):  # verdigris and wear on the bronze
        x, y = r.uniform(0, 1024), r.choice([r.uniform(4, 66), r.uniform(958, 1020), r.uniform(482, 518)])
        t.stroke([(x, y), (x + r.uniform(4, 14), y + r.uniform(-2, 2))], 'chalk', 4, r.choice(['#3f5a4c', '#a08050']), 0.45)
    return t


def lion_stone():
    # Grey limestone with chisel marks, wraps both ways. Round 2: 4 m per repeat (256 px/m, as every surface), stronger mottling and chisel work.
    t = Tex('lion_stone', '#8a877f', True, True, 505)
    r = t.r
    t.stage = 1
    for _ in range(110):
        t.blot(r.uniform(0, 1024), r.uniform(0, 1024), r.uniform(50, 130), 'sponge', r.uniform(60, 120), r.choice(['#6f6c64', '#a29e94', '#7d7a71', '#97938a']), r.uniform(0.35, 0.55), 3)
    t.stage = 2
    for _ in range(150):  # patches of parallel chisel strokes
        cx, cy = r.uniform(0, 1024), r.uniform(0, 1024); a = r.uniform(0, math.pi); n = r.randint(4, 9)
        for k in range(n):
            ox, oy = -math.sin(a) * k * 10, math.cos(a) * k * 10
            L = r.uniform(24, 50)
            x0, y0 = cx + ox + r.uniform(-3, 3), cy + oy + r.uniform(-3, 3)
            t.stroke([(x0, y0), (x0 + math.cos(a) * L, y0 + math.sin(a) * L)], 'chalk', r.uniform(4, 7), r.choice(['#5a5750', '#b2aea4']), r.uniform(0.45, 0.7))
    t.stage = 3
    for _ in range(160):  # pits
        x, y = r.uniform(0, 1024), r.uniform(0, 1024)
        t.stroke([(x, y), (x + 1, y + 1)], 'ink', r.uniform(3, 7), '#55524b', r.uniform(0.5, 0.8), taper=[0, 0])
    return t


if __name__ == '__main__':
    want = sys.argv[3].split(',') if len(sys.argv) > 3 else None
    for f in (floor, wall, pillar, door, lion_stone):
        if want and f.__name__ not in want: continue
        t = f(); n = t.write(); print(t.name, n, 'ops')
