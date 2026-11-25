"""墨将 props at 64x64 (wall and crossbow turret, intact / half-built / damaged). Redrawn at 64: the 96 shape data is re-plotted
on the 64 grid (K = 59/90) with the same helpers as the suits, and the grain is regenerated at 64 (never resized).
Run: python3 mojiang_props64.py -> out/mo64_props_{1x,4x}.png and out/moprop64_<kind>_<state>_1x.png (pass/fail only)
"""
import numpy as np
from PIL import Image
from scipy import ndimage
import tianbing96_v5 as F
import tianbing96_views as V
import tianbing64_views as T64
import mojiang96 as M
import mojiang_props96 as P96

GRAIN64 = {"seed": 7, "wood": 80, "stone": 18, "wood_half": 110, "wood_wall": 100}
N = 64


def studs64(P, seed, wood):
    rs = np.random.RandomState(GRAIN64["seed"] + seed)
    body = np.zeros((N, N), bool); skip = np.zeros((N, N), bool); stone = np.zeros((N, N), bool)
    for r, rp, pl, fl in P:
        m = F.mask(pl, N, N)
        if r in ("wall", "post", "scaf", "loose", "debris", "mag", "bow") and rp == "b": body |= m
        if r == "plinth": stone |= m
        if fl or rp in ("v", "f"): skip |= m
    body &= ~skip
    S = []
    ys, xs = np.nonzero(body)
    for i in rs.permutation(len(xs))[:wood]:
        S.append(("b3" if rs.rand() < 0.6 else "b1", int(xs[i]), int(ys[i])))
    ys, xs = np.nonzero(stone)
    for i in rs.permutation(len(xs))[:GRAIN64["stone"]]:
        S.append(("s3" if rs.rand() < 0.7 else "g3", int(xs[i]), int(ys[i])))
    return S


def main():
    import os
    os.makedirs("out", exist_ok=True)
    T64.setup()
    fails, rows, imgs = [], {}, {}
    keep = dict(F.CONFIG["PAL"]), dict(F.CONFIG["RAMP"])
    F.CONFIG["PAL"] = M.CONFIG["PAL"]; F.CONFIG["RAMP"] = M.CONFIG["RAMP"]
    for kind, fn in (("wall", P96.wall), ("turret", P96.turret)):
        for i, state in enumerate(("intact", "half", "damaged")):
            P, D, _ = fn(state)
            P6 = T64.parts64(P); D6 = T64.details64(D)
            wood = GRAIN64["wood_half"] if (kind, state) == ("wall", "half") else (GRAIN64["wood_wall"] if kind == "wall" else GRAIN64["wood"])
            S6 = studs64(P6, i + (10 if kind == "turret" else 0), wood)
            view = dict(parts=P6, details=D6, studs=S6, flip=False, shoulder=(0, 0), fist=(0, 0), hipfix=False)
            img = V.crop96(V.build(view, None))
            name = f"{kind}_{state}"
            A = img[..., 3] > 0; ys, xs = np.nonzero(A)
            cols = len(set(map(tuple, img[A][:, :3].tolist()))); iso = V.isolated_pct(img)
            lab, n = ndimage.label(A, structure=np.ones((3, 3)))
            if 63 - ys.max() != 2: fails.append(f"{name}: ground gap {63 - ys.max()}")
            if not 9 <= cols <= 13: fails.append(f"{name}: colours {cols}")
            if not 4.0 <= iso <= 10.2: fails.append(f"{name}: isolated {iso:.1f}%")
            if n != 1: fails.append(f"{name}: {n} pieces")
            if xs.min() < 1 or xs.max() > 62 or ys.min() < 1: fails.append(f"{name}: touches tile edge")
            rows[name] = dict(h=int(ys.max() - ys.min() + 1), w=int(xs.max() - xs.min() + 1), colours=cols, isolated=round(iso, 1))
            imgs[name] = img
            Image.fromarray(img, "RGBA").save(f"out/moprop64_{name}_1x.png")
    F.CONFIG["PAL"], F.CONFIG["RAMP"] = keep
    sheet = Image.new("RGBA", (64 * 3, 64 * 2), (58, 62, 72, 255))
    for r, kind in enumerate(("wall", "turret")):
        for c, state in enumerate(("intact", "half", "damaged")):
            sheet.alpha_composite(Image.fromarray(imgs[f"{kind}_{state}"], "RGBA"), (c * 64, r * 64))
    sheet.save("out/mo64_props_1x.png"); sheet.resize((64 * 3 * 4, 64 * 2 * 4), Image.NEAREST).save("out/mo64_props_4x.png")
    for k, v in rows.items(): print(k, v)
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


if __name__ == "__main__":
    main()
