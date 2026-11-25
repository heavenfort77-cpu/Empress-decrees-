"""Scene pass mock at 96 (python3 scene/scene_mock.py): a 7x5 tile field drawn from the approved tile generator plus new, additive layers:
ground wear in five kinds (moss, crack, ink splash, scuff, rubble) seeded per tile; contact shadows under suits, bushes and ore (palette-step
darkening, no alpha); stepped vision falloff by distance from the player; a 2 px block HUD and a ground ring under the player; three props
(broken stele, lantern, rubble heap). Approved suits are pasted unchanged. Every tunable is in CONFIG. Output: out/scene_mock_1x.png, _2x.png,
out/scene_compare_2x.png (current build crop beside the mock). Prints pass/fail checks only."""
import math, random, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tiles"))
sys.argv = [sys.argv[0], "96"]
import numpy as np
from PIL import Image, ImageDraw
import tiles96 as T

S = 96; C = T.C; hx = T.hx
CONFIG = {
    "SEED": 3, "COLS": 7, "ROWS": 5, "PLAYER": (3, 2),
    "WEAR": {"moss": 7, "crack": 5, "splash": 6, "scuff": 10, "rubble": 4, "slab": 1},   # marks per tile of that kind
    "WEAR_MIX": ["slab", "moss", "scuff", "splash", "crack", "slab", "moss", "rubble", "plain", "splash", "slab"],
    "INK": ["#0d1418", "#121a20"],                                            # ink splash tones (outline and one up)
    "MOSS": ["#17382d", "#2a6150"],
    "SHADOW": {"suit": (36, 10), "bush": (40, 10), "ore": (30, 8), "offset": (3, 2), "k": 0.62},  # ellipse half-axes, offset to lower right
    "VISION": [(1, -0.14), (2, -0.07), (3, 0.12), (4, 0.35), (6, 0.58), (99, 0.75)],   # negative = lit (toward the highlight), positive = toward OUT                   # chebyshev distance limit, darkening toward OUT
    "HUD": {"px": 2, "w": 72, "h": 6, "ok": "#4f9a6c", "low": "#c8432c", "back": "#171d23"},
    "RING": {"col": "#7bd0c0", "dim": "#4b6a78", "rx": 36, "ry": 11},
    "PROPS": {"stele": (1, 0), "lantern": (5, 3), "rubble": (0, 4)},
    "SUITS": {(2, 1): "tianbing96/views_idle_front_1x.png", (3, 2): "jianxian/jx_idle_front_1x.png", (5, 1): "mingjiang/mj_idle_left_1x.png",
              (4, 3): "mojiang/mo_idle_front_1x.png", (1, 3): "tianlong/tl_idle_left_1x.png", (6, 0): "gushi/gs_idle_front_1x.png"},
    "LAYOUT": [["g", "g", "b", "g", "g", "g", "g"], ["g", "g", "g", "g", "b", "g", "o"], ["b", "g", "g", "g", "g", "g", "g"],
               ["g", "g", "g", "g", "g", "g", "b"], ["g", "o", "g", "g", "g", "g", "g"]],
}
APPROVED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "approved")


def darken(a, mask, step):
    """palette-step darkening: move the colour toward OUT by `step` (0..1), rounded, on mask pixels. Opaque in, opaque out."""
    out = np.array(hx(C["OUT"] if step >= 0 else C["GROUND"][3])[:3], np.float32); step = abs(step)
    rgb = a[..., :3].astype(np.float32)
    rgb[mask] = np.round(rgb[mask] + (out - rgb[mask]) * step)
    a[..., :3] = rgb.astype(np.uint8)


def wear(a, kind, seed):
    rnd = random.Random(seed); d = ImageDraw.Draw(Image.fromarray(a)); n = CONFIG["WEAR"].get(kind, 0)
    img = Image.fromarray(a); d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rnd.randrange(4, S - 4), rnd.randrange(4, S - 4)
        if kind == "slab":        # one unbroken plate: paint over the inner seams, keep the tile border
            P = C["PLATE"]; g = hx(C["GROUND"][1])
            for yy in range(1, S - 1):
                for xx in range(1, S - 1):
                    if (xx % P in (0, P - 2, P - 1) and xx not in (0, S - 2, S - 1)) or (yy % P in (0, P - 2, P - 1) and yy not in (0, S - 2, S - 1)): d.point((xx, yy), g)
            for _ in range(6): x, y = rnd.randrange(4, S - 14), rnd.randrange(4, S - 6); d.line((x, y, x + 9, y - 3), fill=hx(C["GROUND"][2]))
        elif kind == "moss":      # dithered patch of jade, two tones
            w, h = rnd.randrange(8, 18), rnd.randrange(4, 9)
            for yy in range(y, min(S - 2, y + h)):
                for xx in range(x, min(S - 2, x + w)):
                    if (xx + yy) % 2 == 0 and rnd.random() < 0.8: d.point((xx, yy), hx(CONFIG["MOSS"][0 if rnd.random() < 0.7 else 1]))
        elif kind == "crack":     # dark broken line with a light edge on the upper-left side
            pts = [(x, y)]
            for _ in range(rnd.randrange(3, 7)): pts.append((pts[-1][0] + rnd.randrange(-6, 7), pts[-1][1] + rnd.randrange(2, 8)))
            pts = [(max(2, min(S - 3, px)), max(2, min(S - 3, py))) for px, py in pts]
            d.line(pts, fill=hx(C["GROUND"][3]), width=1)
            d.line([(px + 1, py + 1) for px, py in pts], fill=hx(C["OUT"]), width=1)
        elif kind == "splash":    # ink splash: a blob with spatter dots
            r = rnd.randrange(4, 10); d.ellipse((x - r, y - r // 2, x + r, y + r // 2), fill=hx(CONFIG["INK"][0]))
            for _ in range(rnd.randrange(4, 10)):
                ang = rnd.random() * 6.283; dd = r + rnd.randrange(2, 9)
                d.point((x + int(dd * math.cos(ang)), y + int(dd * math.sin(ang) * 0.6)), fill=hx(CONFIG["INK"][0]))
        elif kind == "scuff":     # light diagonal strokes
            L = rnd.randrange(4, 12); d.line((x, y, x + L, y - L // 3), fill=hx(C["GROUND"][2 if rnd.random() < 0.7 else 3]), width=1)
        elif kind == "rubble":    # small steel chunks with outline
            w, h = rnd.randrange(3, 7), rnd.randrange(2, 5)
            d.rectangle((x, y, x + w, y + h), fill=hx(C["STEEL"][1]), outline=hx(C["OUT"]))
            d.line((x + 1, y + 1, x + w - 1, y + 1), fill=hx(C["STEEL"][2]))
    return np.asarray(img).copy()


def prop(kind, seed):
    rnd = random.Random(seed); img = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(img); ST = C["STEEL"]; A = C["AMBER"]
    if kind == "stele":       # broken stone slab, leaning, top snapped off
        pts = [(34, 86), (38, 30), (52, 24), (62, 34), (60, 86)]
        d.polygon(pts, fill=hx(ST[1]), outline=hx(C["OUT"]))
        d.polygon([(38, 30), (52, 24), (54, 32), (40, 36)], fill=hx(ST[2]))
        for yy in range(40, 80, 8): d.line((44, yy, 54, yy + 2), fill=hx(ST[0]))   # worn inscription rows
        d.line((36, 86, 38, 32), fill=hx(ST[2]))
    elif kind == "lantern":   # stone lantern with an amber flame
        d.rectangle((42, 70, 54, 88), fill=hx(ST[1]), outline=hx(C["OUT"]))
        d.polygon([(34, 52), (62, 52), (58, 44), (38, 44)], fill=hx(ST[2]), outline=hx(C["OUT"]))
        d.rectangle((40, 52, 56, 70), fill=hx(ST[0]), outline=hx(C["OUT"]))
        d.rectangle((44, 56, 52, 66), fill=hx(A[3])); d.rectangle((46, 58, 50, 62), fill=hx(A[4]))
        d.polygon([(48, 36), (54, 44), (42, 44)], fill=hx(ST[1]), outline=hx(C["OUT"]))
        for (xx, yy) in ((36, 60), (60, 58), (38, 68), (58, 66)): d.point((xx, yy), fill=hx(A[2]))   # cast glow specks
    else:                     # rubble heap
        for i in range(7):
            x, y = 30 + rnd.randrange(0, 36), 58 + rnd.randrange(0, 26); w, h = rnd.randrange(5, 12), rnd.randrange(3, 8)
            d.rectangle((x, y, x + w, y + h), fill=hx(ST[1 if i % 3 else 0]), outline=hx(C["OUT"]))
            d.line((x + 1, y + 1, x + w - 1, y + 1), fill=hx(ST[2]))
    return np.asarray(img)


def shadow(scene, cx, cy, rx, ry):
    ox, oy = CONFIG["SHADOW"]["offset"]; H, W = scene.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    e = ((xx - cx - ox) / rx) ** 2 + ((yy - cy - oy) / ry) ** 2
    core = e <= 0.6; rim = (e > 0.6) & (e <= 1.0) & (((xx + yy) % 2) == 0)
    darken(scene, core, CONFIG["SHADOW"]["k"]); darken(scene, rim, CONFIG["SHADOW"]["k"])


def paste(scene, img, x, y):
    h, w = img.shape[:2]; on = img[..., 3] > 0
    y0, x0 = max(0, y), max(0, x); y1, x1 = min(scene.shape[0], y + h), min(scene.shape[1], x + w)
    sub = scene[y0:y1, x0:x1]; src = img[y0 - y:y1 - y, x0 - x:x1 - x]; m = on[y0 - y:y1 - y, x0 - x:x1 - x]
    sub[m] = src[m]


def hud_bar(scene, cx, top, frac):
    H = CONFIG["HUD"]; p = H["px"]; w, h = H["w"], H["h"]; x0 = cx - w // 2
    scene[top - p:top + h + p, x0 - p:x0 + w + p] = hx(C["OUT"])
    scene[top:top + h, x0:x0 + w] = hx(H["back"])
    fw = int(round(frac * w / p)) * p
    scene[top:top + h, x0:x0 + fw] = hx(H["ok"] if frac > 0.35 else H["low"])
    scene[top:top + p, x0:x0 + fw] = tuple(min(255, c + 40) for c in hx(H["ok"] if frac > 0.35 else H["low"])[:3]) + (255,)


def ring(scene, cx, cy):
    R = CONFIG["RING"]; H, W = scene.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
    e = ((xx - cx) / R["rx"]) ** 2 + ((yy - cy) / R["ry"]) ** 2
    band = (e > 0.8) & (e <= 1.0)
    scene[band & ((xx + yy) % 2 == 0)] = hx(R["col"]); scene[band & ((xx + yy) % 2 == 1)] = hx(R["dim"])


def build():
    rnd = random.Random(CONFIG["SEED"]); cols, rows = CONFIG["COLS"], CONFIG["ROWS"]
    scene = np.zeros((rows * S, cols * S, 4), np.uint8)
    kinds = {}
    for r in range(rows):
        for c in range(cols):
            t = CONFIG["LAYOUT"][r][c]; seed = 100 + r * 31 + c * 7
            base = T.ground(seed, trace=(c + r) % 3 == 0) if t == "g" else T.bush(seed) if t == "b" else T.ore(seed)
            if t == "g":
                kind = CONFIG["WEAR_MIX"][(c * 3 + r * 5 + rnd.randrange(0, 2)) % len(CONFIG["WEAR_MIX"])]
                while kinds.get((c - 1, r)) == kind or kinds.get((c, r - 1)) == kind: kind = rnd.choice(CONFIG["WEAR_MIX"])
                kinds[(c, r)] = kind; base = wear(base, kind, seed)
            scene[r * S:(r + 1) * S, c * S:(c + 1) * S] = base
    # shadows under bushes and ore (before suits)
    for r in range(rows):
        for c in range(cols):
            t = CONFIG["LAYOUT"][r][c]
            if t == "b": shadow(scene, c * S + 48, r * S + 78, *CONFIG["SHADOW"]["bush"])
            if t == "o": shadow(scene, c * S + 48, r * S + 80, *CONFIG["SHADOW"]["ore"])
    for kind, (c, r) in CONFIG["PROPS"].items():
        shadow(scene, c * S + 48, r * S + 84, 26, 7); paste(scene, prop(kind, 5), c * S, r * S)
    # player ring, suit shadows, suits, HUD
    pc, pr = CONFIG["PLAYER"]; ring(scene, pc * S + 48, pr * S + 90)
    for (c, r), fn in CONFIG["SUITS"].items():
        img = np.asarray(Image.open(os.path.join(APPROVED, fn)).convert("RGBA"))
        ys, xs = np.nonzero(img[..., 3]); fy = ys.max(); fx = (xs.min() + xs.max()) / 2
        shadow(scene, c * S + fx, r * S + fy, *CONFIG["SHADOW"]["suit"])
    for i, ((c, r), fn) in enumerate(CONFIG["SUITS"].items()):
        img = np.asarray(Image.open(os.path.join(APPROVED, fn)).convert("RGBA")); paste(scene, img, c * S, r * S)
    # vision falloff by chebyshev tile distance from the player (applied after everything, so suits and props darken with their tiles)
    for r in range(rows):
        for c in range(cols):
            dcheb = max(abs(c - pc), abs(r - pr)); step = next(s for lim, s in CONFIG["VISION"] if dcheb <= lim)
            if step: m = np.zeros(scene.shape[:2], bool); m[r * S:(r + 1) * S, c * S:(c + 1) * S] = True; darken(scene, m, step)
    for i, ((c, r), fn) in enumerate(CONFIG["SUITS"].items()):
        hud_bar(scene, c * S + 48, r * S + 2, [1.0, 0.8, 0.3, 0.6, 1.0, 0.5][i])
    return scene, kinds


def checks(scene, kinds):
    fails = []
    if (scene[..., 3] != 255).any(): fails.append("semi-transparent or empty pixels in the scene")
    cols = len(np.unique(scene.reshape(-1, 4), axis=0)); print("scene colours", cols)
    for (c, r), k in kinds.items():
        if kinds.get((c + 1, r)) == k or kinds.get((c, r + 1)) == k: fails.append(f"neighbours share wear {k} at {c},{r}")
    print("wear kinds", {k: list(kinds.values()).count(k) for k in set(kinds.values())})
    return fails


if __name__ == "__main__":
    os.makedirs("out", exist_ok=True)
    scene, kinds = build()
    Image.fromarray(scene).save("out/scene_mock_1x.png")
    Image.fromarray(scene).resize((scene.shape[1] * 2, scene.shape[0] * 2), Image.NEAREST).save("out/scene_mock_2x.png")
    f = checks(scene, kinds); print("PASS" if not f else "FAILING:\n" + "\n".join(f))
