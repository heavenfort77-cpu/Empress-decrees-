"""蛊师 decay zone tiles (python3 decay96.py 96|64): 'rot' ground tile (fills the radius-2 area, 5x5) and 'plant' centre tile (the planted
node an enemy clears by stepping on it). Same style as the approved trail (gushi_trail.py colours: umber pits, bone flecks, amber on the fresh).
Opaque overlays with alpha 0/255 only; drawn natively per size. Output: out/decay{S}_rot_1x.png, out/decay{S}_plant_1x.png, out/decay{S}_context_2x.png"""
import math, random, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "..")
import tiles96 as T
S = T.S; K = T.K; ki = T.ki
CONFIG = {"SEED": 31, "PIT": "#2a1a10", "RIM": "#5c3a1e", "ROT": "#3a2a22", "LINE": "#7a5a43", "BONE": "#cbbf9a", "AMBER": "#e0a030", "OUT": "#120d0a",
          "PITS": 7, "FLECKS": 18, "VEIN_STEPS": 6, "WASH": "#1e1410", "JAR": 11}
def hx(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
C = CONFIG

def pit(a, cx, cy, rx, ry, rnd):
    for y in range(S):
        for x in range(S):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if d <= 1: a[y, x] = hx(C["PIT"]) if d < 0.55 else hx(C["RIM"] if y < cy else C["ROT"])
    for y in range(max(0, int(cy - ry) - 1), min(S, int(cy + ry) + 2)):      # 1 px outline on the lower-right
        for x in range(max(0, int(cx - rx) - 1), min(S, int(cx + rx) + 2)):
            d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if 1 < d <= 1.45 and (x > cx or y > cy): a[y, x] = hx(C["OUT"])

def rot(seed):
    rnd = random.Random(seed); a = np.zeros((S, S, 4), np.uint8)
    for y in range(S):                              # rot wash: a 2x2-block checker of dark umber so the whole zone reads as sick ground, still 0/255 alpha
        for x in range(S):
            if ((x // 2) + (y // 2)) % 2 == 0: a[y, x] = hx(C["WASH"])
    for _ in range(C["PITS"]):
        cx, cy = rnd.randrange(ki(10), S - ki(10)), rnd.randrange(ki(10), S - ki(10)); rx, ry = ki(rnd.randrange(9, 17)), ki(rnd.randrange(4, 8))
        pit(a, cx, cy, rx, ry, rnd)
    for _ in range(C["FLECKS"]):                     # bone flecks and dark rot specks between the pits
        x, y = rnd.randrange(2, S - 3), rnd.randrange(2, S - 3)
        col = hx(C["BONE"]) if rnd.random() < 0.4 else hx(C["ROT"])
        a[y, x] = col
        if rnd.random() < 0.5: a[y, x + 1] = col
    return a

def plant(seed):
    a = rot(seed); rnd = random.Random(seed + 1); M = S // 2
    pit(a, M, M + ki(8), ki(22), ki(10), rnd)      # the socket
    for i in range(6):                                # amber veins out of the socket, orthogonal runs that fade to umber
        ang = i * math.pi / 3 + 0.3; x, y = M, M + ki(6)
        for k in range(C["VEIN_STEPS"]):
            x += math.cos(ang) * ki(6); y += math.sin(ang) * ki(4)
            xi, yi = int(round(x)), int(round(y))
            if 1 <= xi < S - 1 and 1 <= yi < S - 1: a[yi, xi] = hx(C["AMBER"] if k < 2 else C["LINE"])
    R = ki(C["JAR"]); cy = M + ki(2)                   # the node: a sealed jar, lit upper left, bone cap, amber eye, 1 px outline
    for y in range(S):
        for x in range(S):
            d = (x - M) ** 2 / (R * R) + (y - cy) ** 2 / ((R * 0.85) ** 2)
            if d <= 1: a[y, x] = hx(C["RIM"] if (x - M) + (y - cy) < -R * 0.3 else C["ROT"] if (x - M) + (y - cy) < R * 0.5 else C["PIT"])
            elif d <= 1.35 and (x > M or y > cy): a[y, x] = hx(C["OUT"])
    for dx in range(-ki(5), ki(5) + 1): a[cy - int(R * 0.85), M + dx] = hx(C["BONE"]); a[cy - int(R * 0.85) - 1, M + dx] = hx(C["BONE"])
    for dx in range(-ki(2), ki(2)): a[cy, M + dx] = hx(C["AMBER"]); a[cy - 1, M + dx] = hx(C["AMBER"])
    a[cy - 1, M - ki(2)] = hx("#fff3b0")
    return a

if __name__ == "__main__":
    tiles = {"rot": rot(C["SEED"]), "plant": plant(C["SEED"])}
    fails = []
    for n, t in tiles.items():
        al = t[..., 3]; semi = int(((al > 0) & (al < 255)).sum()); cov = (al == 255).mean() * 100
        cols = len({tuple(p) for p in t[al == 255][:, :3]})
        print(f"  {n:5s} coverage {cov:4.1f}%  colours {cols}")
        if semi: fails.append(f"{n}: {semi} semi-transparent px")
        if not 15 <= cov <= 80: fails.append(f"{n}: coverage {cov:.0f}% outside 15-70")
        Image.fromarray(t, "RGBA").save(f"out/decay{S}_{n}_1x.png")
    g = T.ground(11); ctx = Image.new("RGBA", (S * 5, S * 5), (0, 0, 0, 255))
    for r in range(5):
        for c in range(5):
            ctx.alpha_composite(Image.fromarray(T.ground(11 + r * 5 + c)), (c * S, r * S))
            ctx.alpha_composite(Image.fromarray(tiles["plant" if (r, c) == (2, 2) else "rot"]), (c * S, r * S))
    A = "../approved/"; ctx.alpha_composite(Image.open(A + ("gushi/gs_idle_right_1x.png" if S == 96 else "gushi/gs64_idle_right_1x.png")).convert("RGBA"), (S, S))
    ctx.resize((ctx.width * 2, ctx.height * 2), Image.NEAREST).save(f"out/decay{S}_context_2x.png")
    print("PASS" if not fails else "FAIL\n" + "\n".join(fails))
