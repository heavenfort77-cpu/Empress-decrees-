"""冥将 animations at 96, all four views: the shadow-assassination strike (reverse-grip sickle plunge), the cloaked state
(dither out to a faint outline with the sensor eye as the last light, then back), and the shadow-step dash (sink low,
vanish to an outline, ground-hugging violet curve, re-emerge). Same part-moving renderer as the approved factions;
fade and outline are per-frame post-processes on the rendered pixels (no resampling).
Run: python3 mingjiang_anims.py -> out/mj_{strike,cloak,dash}_4views_2x.gif and sheets (pass/fail only)
"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import tianbing96_v5 as F
import tianbing96_views as V
import mingjiang_views as MV
import anim_runner as R

CONFIG = {
    # name, body dy, forward lean (side views), arm step (index into ANG, None = rest), smear-from step, burst, ms
    "STRIKE": [("idle", 0, 0, None, None, False, 120), ("windup", 2, -6, 0, None, False, 140),
               ("slash", 0, 8, 1, 0, False, 60), ("impact", 1, 12, 2, 1, True, 170), ("recover", 0, 4, 3, 2, False, 110)],
    "ANG": {"front": (-110, -200, -300, -340), "back": (-110, -200, -300, -340),
            "right": (150, 250, 320, 345), "left": (150, 250, 320, 345)},
    # per view (96 grid, data space): shoulder pivot, blade tip, blade belly
    "PTS": {"front": ((61, 40), (77, 89), (88, 77)), "back": ((61, 40), (77, 89), (88, 77)),
            "right": ((50, 40), (67, 87), (76, 75)), "left": ((40, 44), (27, 87), (18, 75))},
    "HIP": (48, 58),
    # cloak: name, fade fraction (dither), mode, phase shift, ms
    "CLOAK": [("idle", 0.0, "dither", 0, 400), ("fade1", 0.3, "dither", 0, 110), ("fade2", 0.65, "dither", 0, 110),
              ("shadow", 1.0, "outline", 0, 380), ("shimmer", 1.0, "outline_b", 0, 160),
              ("rev1", 0.65, "dither", 2, 110), ("rev2", 0.3, "dither", 2, 110)],
    # dash (shadow step): name, body dy, lean, post, streak length (0-3), ms
    # dash: name, body dy, lean, post, streak length (0-3), slide dx (side views; front/back use +-dx/2 as a sideways slide), ms
    "DASH": [("idle", 0, 0, None, 0, 0, 100), ("sink", 4, 14, None, 0, 0, 60), ("step1", 8, 34, "outline", 1, 6, 45),
             ("step2", 8, 40, "outline", 3, 14, 45), ("emerge", 3, 10, "dither", 2, 3, 140), ("settle", 1, 3, None, 0, 0, 100)],
    "COL": {"hot": "#efe2ff", "mid": "#8a52e0", "dim": "#4e2a8c", "cloakline": "#6f6a9a"},
    "MAX_CHANGE": 25.0,
}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
SIZE = ["96"]
K64 = 59 / 90


def K():
    return 1.0 if SIZE[0] == "96" else K64


def P(pt):
    if SIZE[0] == "64":
        import tianbing64_views as T64
        return (T64.Xf(pt[0]), T64.Yf(pt[1]))
    return (float(pt[0]), float(pt[1]))


BODYR = ["torso", "head", "skirt", "pauL", "pauR", "cloak", "armL"]


def kind(name):
    return "front" if name in ("front", "back") else "side"


def body_ops(name, dy, lean):
    dy = dy * K()
    ops = [("mov", 0, dy)]
    if lean and kind(name) == "side":
        hx, hy = P(CONFIG["HIP"])
        ops.append(("rot", hx, hy + dy, lean))
    return ops


def strike_T(name, dy, lean, step):
    bo = body_ops(name, dy, lean)
    T = {r: list(bo) for r in BODYR if r != "cloak"}
    if step is not None:
        sx, sy = P(CONFIG["PTS"][name][0])
        arm = [("rot", sx, sy, CONFIG["ANG"][name][step])] + bo
        T["armR"] = arm; T["axe"] = arm
    else:
        T["armR"] = list(bo); T["axe"] = list(bo)
    return T


def hex2rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def strike_overlay(name, dy, lean, step, frm, burst):
    col = CONFIG["COL"]

    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        sh, tip, belly = (P(p) for p in CONFIG["PTS"][name])
        bo = body_ops(name, dy, lean)
        k = K()
        if frm is not None and step is not None:
            a0, a1 = CONFIG["ANG"][name][frm], CONFIG["ANG"][name][step]
            n = 8
            for pt, cols in ((tip, (col["dim"], col["mid"], col["hot"])), (belly, (col["dim"], col["mid"], col["mid"]))):
                prev = None
                for i in range(n + 1):
                    a = a0 + (a1 - a0) * i / n
                    p = V.apply_ops([("rot", *sh, a)] + bo, *pt)
                    if prev is not None:
                        c = cols[0] if i < n / 3 else cols[1] if i < 2 * n / 3 else cols[2]
                        d.line([V.to_canvas(view, *prev), V.to_canvas(view, *p)], fill=c)
                    prev = p
        if burst:
            tx, ty = V.apply_ops([("rot", *sh, CONFIG["ANG"][name][step])] + bo, *tip)
            for k in range(8):
                ang = math.radians(k * 45 + 22.5); r0, r1 = (3 * K(), 9 * K()) if k % 2 == 0 else (3 * K(), 7 * K())
                d.line([V.to_canvas(view, tx + r0 * math.cos(ang), ty + r0 * math.sin(ang)),
                        V.to_canvas(view, tx + r1 * math.cos(ang), ty + r1 * math.sin(ang))],
                       fill=col["hot"] if k % 2 == 0 else col["mid"])
        a = np.array(ov)
        a[V.CONFIG["OFF"][1] + int(round(P((0, 84))[1])):] = 0          # the trail never paints over the feet rows
        return a
    return fn


# ---------- post-processes on the rendered pixels ----------
def boundary(A):
    er = ndimage.binary_erosion(A, structure=np.ones((3, 3)))
    return A & ~er


def eye_pixels(img):
    A = img[..., 3] > 0
    return A & (img[..., :3] == np.array(hex2rgb(F.CONFIG["PAL"]["glow"]))).all(axis=2)


def post_dither(frac, shift):
    def fn(img):
        out = img.copy()
        H, W = out.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        t = BAYER[(yy + shift) % 4, (xx + shift) % 4]
        gone = (img[..., 3] > 0) & (t < frac) & ~eye_pixels(img)
        out[gone] = 0
        return out
    return fn


def post_outline(variant):
    def fn(img):
        A = img[..., 3] > 0
        B = boundary(A)
        out = np.zeros_like(img)
        line = np.array(hex2rgb(CONFIG["COL"]["cloakline"]) + (255,), np.uint8)
        yy, xx = np.mgrid[0:A.shape[0], 0:A.shape[1]]
        keep = B if variant == "outline" else B & (((xx + yy) % 2) == 0)
        out[keep] = line
        eye = eye_pixels(img)
        out[eye] = np.array(hex2rgb(CONFIG["COL"]["hot"]) + (255,), np.uint8)    # the sensor eye is the last light
        if variant == "outline_b":   # shimmer: a few dim pixels just inside the outline
            inner = A & ~B & ((xx * 3 + yy * 5) % 17 == 0)
            out[inner] = np.array(hex2rgb(CONFIG["COL"]["dim"]) + (255,), np.uint8)
        return out
    return fn


# ---------- dash streak ----------
def streak_overlay(name, length, dy):
    col = CONFIG["COL"]

    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        if length == 0:
            return np.asarray(ov)
        n = (10, 18, 28)[min(length, 3) - 1] if length <= 3 else 28
        k = K(); pts = []
        if kind(name) == "front":   # a low arc round the feet, left to right
            for i in range(n):
                a = math.radians(200 + 140 * i / 27.0)
                pts.append(P((47.5 + 36 * math.cos(a), 89 - 5 * math.sin(a) - 1)) if False else
                           (P((47.5, 89))[0] + 36 * k * math.cos(a), P((47.5, 89))[1] - 5 * k * math.sin(a) - 1))
        else:                        # side: a long low curve from behind up to the feet
            for i in range(n):
                t = i / 27.0
                pts.append((P((8, 90))[0] + 40 * k * t, P((8, 90))[1] - 2.5 * k * math.sin(math.pi * t) - 1))
        for i, (x, y) in enumerate(pts):
            if i % 3 == 2:
                continue            # dashed
            c = col["hot"] if i % 7 == 0 else col["mid"] if i % 2 == 0 else col["dim"]
            d.point(V.to_canvas(view, x, y), fill=c)
        return np.asarray(ov)
    return fn


def frame_fn(name, spec, size):
    if len(spec) == 1 or spec[0] == "idle":
        return dict(T=None)
    if spec in CONFIG["STRIKE"]:
        _, dy, lean, step, frm, burst, _ms = spec
        T = strike_T(name, dy, lean, step)
        ov = strike_overlay(name, dy, lean, step, frm, burst) if (frm is not None or burst) else None
        return dict(T=T, overlay=ov, overlay_front=True)
    if spec in CONFIG["CLOAK"]:
        _, frac, mode, shift, _ms = spec
        post = post_dither(frac, shift) if mode == "dither" else post_outline(mode)
        return dict(T=None, post=post, no_feet_check=True)
    _, dy, lean, post, length, dx, _ms = spec
    bo = body_ops(name, dy, lean)
    sx = dx if kind(name) == "side" else (-dx // 2 if dx == 6 else dx // 2)   # front/back: slide one way, then the other
    sx = sx * K()
    T = {r: list(bo) + [("mov", sx, 0)] for r in BODYR + ["armR", "axe"]}
    if sx:
        for r in ("legL", "legR"):
            T[r] = [("mov", sx, 0)]
    if kind(name) == "side" and lean:
        cx, cy = P((48, 30))
        T["cloak"] = bo + [("rot", cx, cy, lean * 0.8), ("mov", sx, 0)]          # the cloak trails behind
    pf = None if post is None else (post_outline("outline") if post == "outline" else post_dither(0.4, 1))
    return dict(T=T, post=pf, overlay=streak_overlay(name, length, dy), overlay_front=False, no_feet_check=True)


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    SIZE[0] = size
    MV.setup(size)
    R.run(V.CONFIG["PREFIX"], size, {"strike": CONFIG["STRIKE"], "cloak": CONFIG["CLOAK"], "dash": CONFIG["DASH"]}, frame_fn)
