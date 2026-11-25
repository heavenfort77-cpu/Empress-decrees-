"""蛊师 erosion trail tiles (蚀迹), 96 x 96, transparent, top-down ground overlay: dark segmented residue left by the abdomen pods,
a row of chitin-brown segments on a sinuous path (not a cloud, not green, not poison), small eaten pits around it, a few amber specks only
while fresh. The path leaves the left edge and the right edge at the same row so tiles chain. Three states: fresh, old, fading.
Run: python3 gushi_trail.py -> out/gs_trail_{1x,4x}.png, out/gs_trail_chain_3x.png (pass/fail only)
"""
import math
import random
import numpy as np
from PIL import Image, ImageDraw
import gushi96 as G

CONFIG = {"SEED": 11, "N": 96, "Y0": 48, "AMP": 9, "STEP": 12, "SEG": (12, 8),
          "STATES": {"fresh": dict(keep=1.0, amber=0.55, pits=14, bone=True), "old": dict(keep=0.7, amber=0.0, pits=9, bone=False),
                     "fading": dict(keep=0.35, amber=0.0, pits=5, bone=False)}}


def rgb(k): return tuple(int(G.CONFIG["PAL"][k][i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def ypath(x, N, Y0, AMP): return Y0 + AMP * math.sin(2 * math.pi * x / N)


def tile(state, seed):
    c = CONFIG; N = c["N"]; st = c["STATES"][state]
    rnd = random.Random(seed)
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    out, g1, g2, b1, b2, v0, v1 = rgb("out"), rgb("g1"), rgb("g2"), rgb("b1"), rgb("b2"), rgb("v0"), rgb("v1")
    # pits first (under the segments)
    for _ in range(st["pits"]):
        x = rnd.randrange(3, N - 6); y = int(ypath(x, N, c["Y0"], c["AMP"]) + rnd.choice([-1, 1]) * rnd.randrange(8, 20))
        if 2 <= y < N - 4:
            d.rectangle([x, y, x + rnd.randrange(2, 4), y + rnd.randrange(1, 3)], fill=out if rnd.random() < 0.7 else g1)
    # eaten ground: a dithered halo of dark specks along the path
    for x in range(N):
        yc = ypath(x, N, c["Y0"], c["AMP"])
        for dy in range(-8, 9):
            y = round(yc) + dy
            if 0 <= y < N and (x + y) % 2 == 0 and rnd.random() < st["keep"] * 0.18 * (1 - abs(dy) / 9):
                d.point((x, y), fill=g1 if rnd.random() < 0.5 else out)
    for i, x in enumerate(range(0, N + 1, c["STEP"])):
        if x not in (0, N) and rnd.random() > st["keep"]: continue
        y = ypath(x, N, c["Y0"], c["AMP"])
        ang = math.atan2(c["AMP"] * 2 * math.pi / N * math.cos(2 * math.pi * x / N), 1)
        w, h = c["SEG"]; w2, h2 = w / 2, h / 2
        pts = [(-w2 + 2, -h2), (w2 - 2, -h2), (w2, -h2 + 2), (w2, h2 - 2), (w2 - 2, h2), (-w2 + 2, h2), (-w2, h2 - 2), (-w2, -h2 + 2)]
        rot = [(round(x + px * math.cos(ang) - py * math.sin(ang)), round(y + px * math.sin(ang) + py * math.cos(ang))) for px, py in pts]
        d.polygon(rot, fill=g1, outline=out)
        cx, cy = round(x), round(y)
        d.line([(round(x - 2 * math.cos(ang)), round(y - 2 * math.sin(ang))), (round(x + 2 * math.cos(ang)), round(y + 2 * math.sin(ang)))], fill=g2)
        if st["bone"]:
            d.point((cx - 4, cy - 2), fill=b1)
        if rnd.random() < st["amber"]:
            d.point((cx + 1, cy), fill=v1); d.point((cx, cy + 1), fill=v0)
    return np.asarray(im)


def checks(tiles):
    fails = []
    N = CONFIG["N"]
    for n, t in tiles.items():
        A = t[..., 3] > 0
        if A.all() or A.sum() == 0: fails.append(f"{n}: empty or full")
        cov = A.mean() * 100
        print(n, "coverage", round(cov, 1), "percent, colours", len(set(map(tuple, t[A][:, :3]))))
    # chain: the open rows on the left and right edge of the tile must match (the path leaves at the same row)
    for n in ("fresh", "old"):
        A = tiles[n][..., 3] > 0
        L = np.where(A[:, :3].any(axis=1))[0]; R = np.where(A[:, -3:].any(axis=1))[0]
        if L.size and R.size and abs(L.mean() - R.mean()) > 4: fails.append(f"{n}: edge rows differ ({L.mean():.0f} vs {R.mean():.0f})")
    return fails


if __name__ == "__main__":
    tiles = {n: tile(n, CONFIG["SEED"] + i) for i, n in enumerate(CONFIG["STATES"])}
    fails = checks(tiles)
    N = CONFIG["N"]
    row = Image.new("RGBA", (N * 3 + 8, N), (0, 0, 0, 0))
    bg = Image.new("RGBA", (N * 3 + 8, N), (92, 80, 62, 255))
    for i, n in enumerate(tiles):
        bg.alpha_composite(Image.fromarray(tiles[n], "RGBA"), (i * (N + 4), 0))
    bg.save("out/gs_trail_1x.png"); bg.resize((bg.width * 4, bg.height * 4), Image.NEAREST).save("out/gs_trail_4x.png")
    chain = Image.new("RGBA", (N * 4, N), (92, 80, 62, 255))
    for i in range(4): chain.alpha_composite(Image.fromarray(tiles["fresh" if i < 2 else "old"], "RGBA"), (i * N, 0))
    chain.resize((chain.width * 3, chain.height * 3), Image.NEAREST).save("out/gs_trail_chain_3x.png")
    print("PASS" if not fails else "FAILING:\n" + "\n".join(fails))


# ---------- straight and turning tiles (the crawl leaves S-curves, so the map needs all three) ----------
def path_pts(shape, N=None):
    N = N or CONFIG["N"]; M = N // 2
    """list of (x, y, angle) every STEP px of arc length. straight: left edge to right edge at row 48. turn: left edge (row 48) to bottom edge (column 48)."""
    pts = []
    if shape == "straight":
        for x in range(0, N + 1, CONFIG["STEP"]): pts.append((x, M, 0.0))
    else:
        R = M; L = R * math.pi / 2; n = int(L // CONFIG["STEP"])
        for i in range(n + 1):
            t = (i * CONFIG["STEP"]) / R
            pts.append((R * math.sin(t), N - R * math.cos(t), t))
        pts.append((M, N, math.pi / 2))
    return pts


def tile_shape(shape, state, seed):
    c = CONFIG; N = c["N"]; st = c["STATES"][state]
    rnd = random.Random(seed)
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    out, g1, g2, b1, v0, v1 = rgb("out"), rgb("g1"), rgb("g2"), rgb("b1"), rgb("v0"), rgb("v1")
    pts = path_pts(shape)
    for _ in range(st["pits"]):
        p = rnd.choice(pts); x = int(p[0] + rnd.choice([-1, 1]) * rnd.randrange(8 * N // 96, 18 * N // 96)); y = int(p[1] + rnd.choice([-1, 1]) * rnd.randrange(8 * N // 96, 18 * N // 96))
        if 1 <= x < N - 4 and 1 <= y < N - 3:
            d.rectangle([x, y, x + rnd.randrange(2, 4), y + rnd.randrange(1, 3)], fill=out if rnd.random() < 0.7 else g1)
    for k, (x, y, ang) in enumerate(pts):
        if k not in (0, len(pts) - 1) and rnd.random() > st["keep"]: continue
        w, h = c["SEG"]; w2, h2 = w / 2, h / 2
        poly = [(-w2 + 2, -h2), (w2 - 2, -h2), (w2, -h2 + 2), (w2, h2 - 2), (w2 - 2, h2), (-w2 + 2, h2), (-w2, h2 - 2), (-w2, -h2 + 2)]
        rot = [(round(x + px * math.cos(ang) - py * math.sin(ang)), round(y + px * math.sin(ang) + py * math.cos(ang))) for px, py in poly]
        d.polygon(rot, fill=g1, outline=out)
        d.line([(round(x - 2 * math.cos(ang)), round(y - 2 * math.sin(ang))), (round(x + 2 * math.cos(ang)), round(y + 2 * math.sin(ang)))], fill=g2)
        if st["bone"]: d.point((round(x) - 4, round(y) - 2), fill=b1)
        if rnd.random() < st["amber"]:
            d.point((round(x) + 1, round(y)), fill=v1); d.point((round(x), round(y) + 1), fill=v0)
    return np.asarray(im)


def make_shapes():
    N = CONFIG["N"]; fails = []
    sheet = Image.new("RGBA", (N * 6 + 20, N), (92, 80, 62, 255)); x = 0
    for shape in ("straight", "turn"):
        for i, state in enumerate(CONFIG["STATES"]):
            t = tile_shape(shape, state, CONFIG["SEED"] + 7 + i)
            sheet.alpha_composite(Image.fromarray(t, "RGBA"), (x, 0)); x += N + 4
            if state != "fading":
                A = t[..., 3] > 0
                if shape == "straight":
                    L = np.where(A[:, :3].any(axis=1))[0]; Rr = np.where(A[:, -3:].any(axis=1))[0]
                    if abs(L.mean() - Rr.mean()) > 3: fails.append(f"straight/{state}: edge rows differ")
                else:
                    L = np.where(A[:, :3].any(axis=1))[0]; B = np.where(A[-3:, :].any(axis=0))[0]
                    if not (L.size and B.size) or abs(L.mean() - N / 2) > 6 or abs(B.mean() - N / 2) > 6: fails.append(f"turn/{state}: exits not at the tile mid-edges")
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save(f"out/{CONFIG.get('PFX','gs')}_trail_shapes_3x.png")
    # a short road: straight, turn, then a turn rotated to go up (turn rotated 180/90 as data)
    road = Image.new("RGBA", (N * 3, N * 2), (92, 80, 62, 255))
    s = Image.fromarray(tile_shape("straight", "fresh", 21), "RGBA"); tn = Image.fromarray(tile_shape("turn", "fresh", 22), "RGBA")
    road.alpha_composite(s, (0, N)); road.alpha_composite(s, (N, N)); road.alpha_composite(tn.transpose(Image.FLIP_TOP_BOTTOM), (N * 2, N)) if False else None
    road.alpha_composite(tn.transpose(Image.FLIP_TOP_BOTTOM), (N * 2, 0))      # turn flipped: enters at the left, leaves at the top
    road.resize((road.width * 3, road.height * 3), Image.NEAREST).save(f"out/{CONFIG.get('PFX','gs')}_trail_road_3x.png")
    print("shapes", "PASS" if not fails else "FAILING: " + "; ".join(fails))
    return fails


if __name__ == "__main__":
    make_shapes()
