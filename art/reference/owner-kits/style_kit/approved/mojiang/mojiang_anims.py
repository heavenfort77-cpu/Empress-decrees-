"""墨将 build animation at 96, all four views: lift the mallet, raise it overhead, drive a post, a crenellated timber wall segment
rises at the strike point. Same part-moving renderer as the approved factions; the post, wall and sparks are overlays drawn behind
the body (so the feet never change). Defence only: nothing here attacks.
Run: python3 mojiang_anims.py -> out/mo_build_4views_2x.gif and out/mo_build_sheet_1x.png (pass/fail only)
"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw
import tianbing96_v5 as F
import tianbing96_views as V
import mojiang_views as MV
import anim_runner as R

CONFIG = {
    # name, body dy, mallet step (index into ANG, None = planted at rest), effect (None, "post", "wall"), smear-from step, ms
    "BUILD": [("idle", 0, None, None, None, 120), ("lift", 0, 0, None, None, 120), ("raise", 1, 1, None, None, 160),
              ("drive", 2, 2, "post", 1, 90), ("settle", 1, None, "wall", None, 220)],
    "ANG": {"front": (-70, -150, -20), "back": (-70, -150, -20), "right": (-70, -150, -20), "left": (70, 150, 20)},
    # per view (96 grid, data space): shoulder pivot, bottom of the mallet head at rest
    "PTS": {"front": ((69, 48), (72, 88)), "back": ((69, 48), (72, 88)), "right": ((50, 48), (58, 88)), "left": ((38, 48), (31, 88))},
    "COL": {"hot": "#e8fff6", "mid": "#3f9a87", "dim": "#2a5f55", "t1": "#5a3d28", "t2": "#8f6340", "t3": "#cf9a62",
            "ink": "#0a0c10", "bronze": "#3f9a87"},
}
BODYR = ["torso", "head", "skirt", "pauL", "pauR", "armL", "bow", "neck", "rack"]


def build_T(name, dy, step):
    bo = [("mov", 0, dy)]
    T = {r: list(bo) for r in BODYR}
    if step is None:
        T["armR"] = list(bo); T["mallet"] = list(bo)
    else:
        sx, sy = CONFIG["PTS"][name][0]
        arm = [("rot", sx, sy, CONFIG["ANG"][name][step])] + bo
        T["armR"] = arm; T["mallet"] = arm
    return T, bo


def hexc(h):
    return h


def overlay(name, dy, step, fx, frm):
    col = CONFIG["COL"]

    def fn(view):
        C = V.CONFIG["CANVAS"]
        ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        sh, bot = CONFIG["PTS"][name]
        T, bo = build_T(name, dy, 2)                 # where the mallet lands at the drive frame
        px, py = V.apply_ops([("rot", *sh, CONFIG["ANG"][name][2])] + [("mov", 0, 2)], *bot)
        px = int(round(px))

        def poly(pts, fill):
            d.polygon([V.to_canvas(view, x, y) for x, y in pts], fill=fill, outline=col["ink"])
        if fx == "post":
            poly([(px - 2, 82), (px + 2, 82), (px + 2, 90), (px - 2, 90)], col["t2"])
            poly([(px - 2, 80), (px + 2, 80), (px + 2, 82), (px - 2, 82)], col["t3"])
        if fx == "wall":
            x0, x1 = px - 9, px + 9
            poly([(x0, 76), (x1, 76), (x1, 90), (x0, 90)], col["t2"])
            for a, b in ((x0, x0 + 4), (px - 2, px + 2), (x1 - 4, x1)):
                poly([(a, 72), (b, 72), (b, 76), (a, 76)], col["t2"])          # merlons
            d.line([V.to_canvas(view, x0 + 1, 84), V.to_canvas(view, x1 - 1, 84)], fill=col["bronze"])
            d.line([V.to_canvas(view, x0 + 1, 80), V.to_canvas(view, x1 - 1, 80)], fill=col["t3"])
        if fx in ("post", "wall"):
            for k in range(6):
                a = math.radians(200 + k * 28)
                r0, r1 = (3, 8) if k % 2 == 0 else (3, 6)
                cx, cy = px, 88
                d.line([V.to_canvas(view, cx + r0 * math.cos(a), cy + r0 * math.sin(a)),
                        V.to_canvas(view, cx + r1 * math.cos(a), cy + r1 * math.sin(a))],
                       fill=col["hot"] if k % 2 == 0 else col["mid"])
        if frm is not None and step is not None:    # trail of the mallet head from the overhead frame down to the strike
            a0, a1 = CONFIG["ANG"][name][frm], CONFIG["ANG"][name][step]
            prev = None
            for i in range(9):
                a = a0 + (a1 - a0) * i / 8
                p = V.apply_ops([("rot", *sh, a)] + bo, *bot)
                if prev is not None:
                    d.line([V.to_canvas(view, *prev), V.to_canvas(view, *p)], fill=col["dim"] if i < 4 else col["mid"])
                prev = p
        return ov

    return lambda view: np.asarray(fn(view))


def frame_fn(name, spec, size):
    if len(spec) == 1 or spec[0] == "idle":
        return dict(T=None)
    _, dy, step, fx, frm, _ms = spec
    T, bo = build_T(name, dy, step)
    ov = overlay(name, dy, step, fx, frm) if (fx or frm is not None) else None
    return dict(T=T, overlay=ov, overlay_front=False)


if __name__ == "__main__":
    MV.setup("96")
    R.run("mo", "96", {"build": CONFIG["BUILD"]}, frame_fn)
