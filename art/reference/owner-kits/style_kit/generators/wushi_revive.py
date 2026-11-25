"""巫师 revival animation: he raises one arm and soul-fire rises from the ground to his hand.
Two variants for choosing: "lance" (raises the ge-lance arm, lance held upright overhead) and "shield" (raises the shield arm).
All four views, 96 or 64, same part-moving renderer as the attacks. The soul-fire is a separate overlay.
Run: python3 wushi_revive.py [96|64]  -> out/wushi{size}_revive_{lance,shield}_4views_{S}x.gif (pass/fail only)
"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import tianbing96_views as V
import wushi_views as WV

CONFIG = {
    # name, body dy, raise share (0 = arm down, 1 = fully up), soul stage (None, "hand", 0..1 rising), ms
    "FRAMES": [("idle", 0, 0.0, None, 150), ("gather", 1, 0.45, None, 120), ("raise", 0, 1.0, "hand", 120),
               ("channel1", 0, 1.0, 0.0, 200), ("channel2", 0, 1.0, 0.5, 200), ("channel3", 0, 1.0, 1.0, 200),
               ("lower", 1, 0.45, None, 120)],
    # per view: raise pivots (96 grid) and full raise angle in degrees.
    # lance: (shoulder, fist, arm deg); the lance counter-rotates so it stays upright. shield: (shoulder, deg)
    "LANCE": {"front": ((67, 47), (68, 65), -160), "back": ((67, 47), (68, 65), -160),
              "right": ((59, 45), (67, 64), -160), "left": ((39, 45), (36, 64), 170)},
    "SHIELD": {"front": ((33, 37), 120), "back": ((33, 37), 120),
               "right": ((56, 38), -100), "left": ((55, 40), -100)},
    "SOUL": ("#6ff0c8", "#aebfcc"),
    "MAX_CHANGE": 25.0,
}


def P(x, y, size):
    if size == "64":
        import tianbing64_views as T64
        return T64.Xf(x), T64.Yf(y)
    return float(x), float(y)


def frame_T(name, variant, dy, share, size):
    T = {r: [("mov", 0, dy)] for r in V.BODY}
    T["armR"] = [("mov", 0, dy)]; T["halberd"] = [("mov", 0, dy)]
    hand = None
    if variant == "lance":
        sh, fi, deg = CONFIG["LANCE"][name]
        sh = P(*sh, size); fi = P(*fi, size)
        a = deg * share
        arm = [("mov", 0, dy), ("rot", sh[0], sh[1] + dy, a)]
        fx, fy = V.apply_ops(arm, *fi)
        T["armR"] = arm
        T["halberd"] = arm + [("rot", fx, fy, -a)]   # keep the lance upright in the raised fist
        hand = (fx, fy)
    else:
        sh, deg = CONFIG["SHIELD"][name]
        sh = P(*sh, size)
        a = deg * share
        ops = [("mov", 0, dy), ("rot", sh[0], sh[1] + dy, a)]
        T["armL"] = ops; T["shield"] = ops
        # hand = the shield's centre after the raise
        cx, cy = {"front": (27, 52), "back": (27, 52), "right": (60, 51), "left": (61, 51)}[name]
        hand = V.apply_ops(ops, *P(cx, cy, size))
    return T, hand


def soul(view, size, hand, stage):
    C = V.CONFIG["CANVAS"]
    ov = Image.new("RGBA", (C, C), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    bright, mid = CONFIG["SOUL"]
    k = 1.0 if size == "96" else 59 / 90
    if stage == "hand" or stage is not None:   # glow ring round the raised hand
        hx, hy = hand
        for i in range(8):
            ang = math.radians(i * 45 + 22.5)
            r0, r1 = (5 * k, 9 * k) if i % 2 == 0 else (5 * k, 7 * k)
            d.line([V.to_canvas(view, hx + r0 * math.cos(ang), hy + r0 * math.sin(ang)),
                    V.to_canvas(view, hx + r1 * math.cos(ang), hy + r1 * math.sin(ang))], fill=bright if i % 2 == 0 else mid)
    if isinstance(stage, float):   # motes rising from the ground in two streams that meet at the hand
        gy = (91 if size == "96" else 60)
        for side in (-1, 1):
            gx = (47.5 if size == "96" else 31.5) + side * 22 * k
            for j in range(8):
                t = (j / 8 + stage * 0.12) % 1.0
                x = gx + (hand[0] - gx) * t + side * 4 * k * math.sin(t * math.pi * 2)
                y = gy + (hand[1] - gy) * t
                px, py = V.to_canvas(view, x, y)
                col = bright if j % 2 == 0 else mid
                d.point((px, py), fill=col)
                if j % 2 == 0:
                    d.point((px, py - 1), fill=mid)
    return np.asarray(ov)


def run(size):
    WV.setup(size)
    C = V.CONFIG["CANVAS"]
    S = 2 if size == "96" else 3
    fails = []
    for variant in ("lance", "shield"):
        allf = {}
        for name in V.ORDER:
            view = V.VIEWS[name]
            frames, ms, legmaps = [], [], []
            for fname, dy, share, stage, dur in CONFIG["FRAMES"]:
                T, hand = frame_T(name, variant, dy, share, size)
                extra = ()
                if variant == "lance" and name == "left" and share:   # far upper arm, only needed once the arm lifts
                    pl = [(35, 44), (42, 44), (41, 61), (34, 61)]
                    if size == "64":
                        import tianbing64_views as T64
                        pl = [(T64.X(x), T64.Y(y)) for x, y in pl]
                    extra = (("armR", "g", pl, False),)
                body = V.build(view, T if (dy or share) else None, extra=extra, extra_front=False)
                legmaps.append(np.isin(V.LAST["region"], ["legL", "legR"]))
                img = body
                if stage is not None:
                    img = V.composite(body, soul(view, size, hand, stage), over_in_front=True)
                frames.append(img); ms.append(dur)
                lab, n = ndimage.label(body[..., 3] > 0, structure=np.ones((3, 3)))
                if n != 1: fails.append(f"{variant}/{name}/{fname}: {n} pieces")
                if img[0].any() or img[-1].any() or img[:, 0].any() or img[:, -1].any():
                    fails.append(f"{variant}/{name}/{fname}: touches canvas edge")
            ox, oy = V.CONFIG["OFF"]; r0, r1 = V.CONFIG["FEET_ROWS"]
            legs0 = legmaps[0][r0 + oy:r1 + oy]
            for fr, lm in zip(frames[1:], legmaps[1:]):
                m = legs0 & lm[r0 + oy:r1 + oy]
                if not np.array_equal(frames[0][r0 + oy:r1 + oy][m], fr[r0 + oy:r1 + oy][m]):
                    fails.append(f"{variant}/{name}: feet move"); break
            for i in range(len(frames)):
                j = (i + 1) % len(frames)
                c = float((frames[i] != frames[j]).any(axis=2).mean()) * 100
                if c == 0: fails.append(f"{variant}/{name}: frames {i},{j} identical")
                if c > CONFIG["MAX_CHANGE"]: fails.append(f"{variant}/{name}: frames {i},{j} change {c:.1f}%")
            allf[name] = (frames, ms)
        # one GIF, four views side by side
        A = np.zeros((C, C), bool)
        for fr, _ in allf.values():
            for f in fr:
                A |= f[..., 3] > 0
        ys, xs = np.nonzero(A); pad = 3
        y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
        w, h = x1 - x0, y1 - y0; lab_h = 12
        out = []
        for i in range(len(CONFIG["FRAMES"])):
            sh = Image.new("RGBA", (w * 4, h + lab_h), (58, 62, 72, 255)); d = ImageDraw.Draw(sh)
            for k, name in enumerate(V.ORDER):
                sh.alpha_composite(Image.fromarray(allf[name][0][i], "RGBA").crop((x0, y0, x1, y1)), (k * w, lab_h))
                d.text((k * w + 3, 1), name, fill=(200, 210, 220, 255))
            out.append(sh.resize((sh.width * S, sh.height * S), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
        dur = [f[4] for f in CONFIG["FRAMES"]]; dur[0] = 400
        fn = f"out/wushi{size}_revive_{variant}_4views_{S}x.gif"
        out[0].save(fn, save_all=True, append_images=out[1:], duration=dur, loop=0, disposal=2)
        # contact sheet, 1x
        sheet = Image.new("RGBA", (w * len(CONFIG["FRAMES"]), h * 4), (58, 62, 72, 255))
        for r, name in enumerate(V.ORDER):
            for i, fr in enumerate(allf[name][0]):
                sheet.alpha_composite(Image.fromarray(fr, "RGBA").crop((x0, y0, x1, y1)), (i * w, r * h))
        sheet.save(f"out/wushi{size}_revive_{variant}_sheet_1x.png")
        print(fn)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails[:20]))


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "96")
