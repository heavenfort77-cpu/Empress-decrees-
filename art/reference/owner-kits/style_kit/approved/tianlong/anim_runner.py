"""Shared runner for faction animations: builds every frame of every view through the approved renderer,
runs the checks, and writes one four-view GIF and one contact sheet per animation, plus the idle lineup.
A faction module supplies: setup(size), VIEWS via tianbing96_views, and per animation a list of frame specs
and frame_fn(view_name, spec, size) -> dict(T=..., extra=(), hide=(), overlay=None or fn(view) -> RGBA array,
overlay_front=bool, feet_fixed=bool).
"""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import tianbing96_views as V


def build_frame(name, spec, size, frame_fn):
    view = V.VIEWS[name]
    f = frame_fn(name, spec, size)
    T = f.get("T") or None
    body = V.build(view, T, hide=f.get("hide", ()), extra=f.get("extra", ()), extra_front=f.get("extra_front", True))
    legs = np.isin(V.LAST["region"], ["legL", "legR"])
    heads = V.LAST["region"] == "head"
    img = body
    if f.get("overlay") is not None:
        img = V.composite(body, f["overlay"](view), over_in_front=f.get("overlay_front", True))
    return img, body, legs, heads


def run(prefix, size, anims, frame_fn, max_change=25.0, scale=None):
    C = V.CONFIG["CANVAS"]
    S = scale or (2 if size == "96" else 3)
    fails, report, idle = [], {}, {}
    # idle views and their checks
    for name in V.ORDER:
        img, body, legs, heads = build_frame(name, ("idle",), size, frame_fn)
        idle[name] = V.crop96(img)
        f, rep = V.idle_checks(name, idle[name]); fails += f; report[name] = rep
        if name in ("left", "right"):
            fails += V.facing_check(name, idle[name], V.crop96(legs), V.crop96(heads), face_right=(name == "right"))
        Image.fromarray(idle[name], "RGBA").save(f"out/{prefix}_idle_{name}_1x.png")
    fa = idle["front"][..., 3] > 0; ba = idle["back"][..., 3] > 0; fm = fa[:, ::-1]
    report["back"]["iou_vs_mirrored_front"] = round(float((ba & fm).sum() / (ba | fm).sum()), 2)
    N = V.CONFIG["N"]; L = 3 if size == "96" else 4
    for sc in (1, L):
        lu = Image.new("RGBA", (N * sc * 4, N * sc), (0, 0, 0, 0) if sc == 1 else V.CONFIG["BG"])
        for i, name in enumerate(V.ORDER):
            lu.alpha_composite(Image.fromarray(idle[name], "RGBA").resize((N * sc, N * sc), Image.NEAREST), (i * N * sc, 0))
        lu.save(f"out/{prefix}_lineup_{sc}x.png")
    # animations
    for anim, frames_spec in anims.items():
        allf = {}
        for name in V.ORDER:
            frames, legmaps = [], []
            for spec in frames_spec:
                img, body, legs, heads = build_frame(name, spec, size, frame_fn)
                frames.append(img); legmaps.append(legs)
                lab, n = ndimage.label(body[..., 3] > 0, structure=np.ones((3, 3)))
                if n != 1: fails.append(f"{anim}/{name}/{spec[0]}: {n} pieces")
                if img[0].any() or img[-1].any() or img[:, 0].any() or img[:, -1].any():
                    fails.append(f"{anim}/{name}/{spec[0]}: touches canvas edge")
            ox, oy = V.CONFIG["OFF"]; r0, r1 = V.CONFIG["FEET_ROWS"]
            for fr, lm in zip(frames[1:], legmaps[1:]):
                m = legmaps[0][r0 + oy:r1 + oy] & lm[r0 + oy:r1 + oy]
                if not np.array_equal(frames[0][r0 + oy:r1 + oy][m], fr[r0 + oy:r1 + oy][m]):
                    fails.append(f"{anim}/{name}: feet move"); break
            ch = []
            for i in range(len(frames)):
                j = (i + 1) % len(frames)
                c = float((frames[i] != frames[j]).any(axis=2).mean()) * 100
                ch.append(round(c, 1))
                if c == 0: fails.append(f"{anim}/{name}: frames {i},{j} identical")
                if c > max_change: fails.append(f"{anim}/{name}: frames {i},{j} change {c:.1f}%")
            report[name][f"{anim}_change"] = ch
            allf[name] = frames
        A = np.zeros((C, C), bool)
        for fr in allf.values():
            for f in fr:
                A |= f[..., 3] > 0
        ys, xs = np.nonzero(A); pad = 3
        y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
        w, h = x1 - x0, y1 - y0; lab_h = 12
        out = []
        for i in range(len(frames_spec)):
            sh = Image.new("RGBA", (w * 4, h + lab_h), (58, 62, 72, 255)); d = ImageDraw.Draw(sh)
            for k, name in enumerate(V.ORDER):
                sh.alpha_composite(Image.fromarray(allf[name][i], "RGBA").crop((x0, y0, x1, y1)), (k * w, lab_h))
                d.text((k * w + 3, 1), name, fill=(200, 210, 220, 255))
            out.append(sh.resize((sh.width * S, sh.height * S), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
        dur = [sp[-1] for sp in frames_spec]; dur[0] = max(dur[0], 400)
        out[0].save(f"out/{prefix}_{anim}_4views_{S}x.gif", save_all=True, append_images=out[1:], duration=dur, loop=0, disposal=2)
        sheet = Image.new("RGBA", (w * len(frames_spec), h * 4), (58, 62, 72, 255))
        for r, name in enumerate(V.ORDER):
            for i, fr in enumerate(allf[name]):
                sheet.alpha_composite(Image.fromarray(fr, "RGBA").crop((x0, y0, x1, y1)), (i * w, r * h))
        sheet.save(f"out/{prefix}_{anim}_sheet_1x.png")
    for name in V.ORDER:
        print(name, {k: (float(v) if hasattr(v, "item") else v) for k, v in report[name].items()})
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails[:25]))
    return fails
