"""蛊师 vessel crawl (dash) at 96, all four views. The suit sinks onto its abdomen: the vessel, head and arms drop (the vessel settles into the
abdomen sac), the legs splay out wide and low, the pods swing out and down to the ground, then it snakes forward in an S (side to side in
the front and back views, forward with a bob in the side views) leaving erosion-trail segments behind. Same part-moving renderer as the
approved suits; the trail is an overlay drawn behind the body.
Run: python3 gushi_crawl.py -> out/gs_crawl_4views_2x.gif and out/gs_crawl_sheet_1x.png (pass/fail only)
"""
import math
import sys
import numpy as np
from PIL import Image
import tianbing96_v5 as F
import tianbing96_views as V
import gushi_views as GV
import gushi96 as G
import anim_runner as R

CONFIG = {
    # name, torso/head/arm drop, leg splay (deg), slide dx (side: forward; front/back: sideways, mirrored by flip), arm bob, pod swing (deg), trail count, ms
    "CRAWL": [("idle", 0, 0, 0, 0, 0, 0, 120), ("sink", 8, 25, 0, 0, 10, 0, 90), ("crawl1", 14, 45, 4, 2, 22, 1, 100),
              ("crawl2", 14, 45, 10, 0, 22, 2, 100), ("crawl3", 14, 45, 16, 2, 22, 3, 100), ("crawl4", 14, 45, 22, 0, 22, 4, 100),
              ("rise", 5, 15, 26, 0, 6, 4, 160)],
    "SWAY": [0, 0, -4, 4, -4, 4, 0],                    # front/back sideways S
    "HIP": {"front": ((40, 70), (55, 70)), "back": ((40, 70), (55, 70)), "right": ((48, 72), (44, 72)), "left": ((48, 72), (44, 72))},
    "POD": {"front": (47.5, 70), "back": (47.5, 70), "right": (40, 72), "left": (40, 72)},
    "COL": {"seg": "#3a2a22", "line": "#7a5a43", "ink": "#120d0a", "amber": "#e0a030"},
}
SZ = {"k": 1.0, "s": "96"}
def PX(x): return x if SZ["s"] == "96" else round(__import__("tianbing64_views").Xf(x))
def PY(y): return y if SZ["s"] == "96" else round(__import__("tianbing64_views").Yf(y))
KIND = lambda n: "front" if n in ("front", "back") else "side"


def hexrgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def frame_fn(name, spec, size):
    if spec[0] == "idle":
        return dict(T=None)
    nm, drop, splay, dx, bob, pod, trail, _ms = spec
    idx = [s[0] for s in CONFIG["CRAWL"]].index(nm)
    sway = CONFIG["SWAY"][idx] if KIND(name) == "front" else 0
    sx = (sway if KIND(name) == "front" else dx) * SZ["k"]; drop *= SZ["k"]; bob *= SZ["k"]
    legdy = 19 * SZ["k"] * (1 - math.cos(math.radians(splay)))
    view = V.VIEWS[name]
    regions = {p[0] for p in view["parts"]}
    T = {}
    body = [("mov", sx, drop + (bob if KIND(name) == "side" else 0))]
    for r in ("torso", "head", "armL", "armR", "hand"):
        if r in regions: T[r] = list(body)
    T["skirt"] = [("mov", sx, drop * 0.5)]
    (hl, hr) = [tuple((PX(a), PY(b)) for a, b in h) if False else (PX(h[0]), PY(h[1])) for h in CONFIG["HIP"][name]]
    sign = 1 if name != "back" else 1
    T["legL"] = [("rot", hl[0], hl[1], splay), ("mov", sx, legdy)]
    T["legR"] = [("rot", hr[0], hr[1], -splay), ("mov", sx, legdy)]
    if KIND(name) == "side":                       # both side legs splay forward/back instead of left/right
        T["legL"] = [("rot", hl[0], hl[1], splay), ("mov", sx, legdy)]
        T["legR"] = [("rot", hr[0], hr[1], -splay * 0.6), ("mov", sx, legdy)]
    cx, cy = [PX(CONFIG["POD"][name][0]), PY(CONFIG["POD"][name][1])]
    T["pauL"] = [("rot", cx, cy, splay * 0 - pod), ("mov", sx, drop * 0.5 + 1)]
    T["pauR"] = [("rot", cx, cy, pod), ("mov", sx, drop * 0.5 + 1)]
    return dict(T=T, overlay=trail_overlay(name, idx, trail, sx), overlay_front=False, no_feet_check=True)


def trail_overlay(name, idx, n, sx):
    """erosion trail drawn in the approved tile look: octagon segments, dark outline, umber fill, pale centre line, amber on the newest"""
    col = CONFIG["COL"]
    def seg_px(ov, view, cx, cy, ang):
        w2, h2 = (5, 2) if SZ["s"] == "96" else (4, 1)
        poly = [(-w2 + 2, -h2), (w2 - 2, -h2), (w2, -h2 + 2), (w2, h2 - 2), (w2 - 2, h2), (-w2 + 2, h2), (-w2, h2 - 2), (-w2, -h2 + 2)]
        from PIL import Image, ImageDraw
        m = Image.new("L", (40, 40), 0); d = ImageDraw.Draw(m)
        pts = [(20 + round(px * math.cos(ang) - py * math.sin(ang)), 20 + round(px * math.sin(ang) + py * math.cos(ang))) for px, py in poly]
        d.polygon(pts, fill=1)
        a = np.asarray(m) > 0
        for yy in range(40):
            for xx in range(40):
                if not a[yy, xx]: continue
                edge = not (a[yy - 1, xx] and a[yy + 1, xx] and a[yy, xx - 1] and a[yy, xx + 1])
                gx, gy = cx + xx - 20, cy + yy - 20
                ox, oy = V.to_canvas(view, gx, gy)
                ov[oy, ox] = hexrgb(col["ink"] if edge else col["seg"])
        for t in (-1, 0, 1):
            gx, gy = round(cx + t * math.cos(ang)), round(cy + t * math.sin(ang))
            ox, oy = V.to_canvas(view, gx, gy); ov[oy, ox] = hexrgb("#7a5a43")
    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = np.zeros((C, C, 4), np.uint8)
        side = KIND(name) == "side"
        for k in range(n):
            if side:
                cx = int(PX(26) + sx - (n - k) * 11 * SZ["k"]); cy = PY(90) + (1 if k % 2 else 0); ang = 0.0
            else:
                cx = int(PX(48) + [-30, -20, -10, 0][k % 4] * SZ["k"] * (1 if k % 2 == 0 else -1) + sx * 0.5)
                cy = PY(91) + (k % 2); ang = 0.35 * (1 if k % 2 else -1)
            seg_px(ov, view, cx, cy, ang)
            if k == n - 1:
                ox, oy = V.to_canvas(view, cx + 1, cy); ov[oy, ox] = hexrgb(col["amber"])
        return ov
    return fn


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    SZ["s"] = size; SZ["k"] = 1.0 if size == "96" else 59 / 90
    GV.setup(size)
    R.run("gs" if size == "96" else "gs64", size, {"crawl": CONFIG["CRAWL"]}, frame_fn)
