"""Show the 天龙 dash as movement across tiles (the engine moves the unit; the sprite animation plays on top).
Four lanes: right view dashing right, left view dashing left, front view dashing toward the camera (down), back view away (up).
Run: python3 dash_scene.py -> out/tl_dash_scene_2x.gif (96 px tiles, 3 tiles of travel)"""
import numpy as np
from PIL import Image, ImageDraw
import tianlong_views as TL
import anim_runner as R
import tianbing96_views as V

TL.setup("96")
V.CONFIG["PREFIX"] = "tl"
TILE, TRAVEL, S = 96, 3, 2
specs = {s[0]: s for s in TL.CONFIG["DASH"]}
poses = {n: {} for n in V.ORDER}
for n in V.ORDER:
    for name in ("idle", "crouch", "burst", "burst2", "settle"):
        img, *_ = R.build_frame(n, specs[name], "96", TL.frame_fn)
        poses[n][name] = img
# union bounding box of every pose in every view (so every lane crops the same way)
A = np.zeros(poses["front"]["idle"].shape[:2], bool)
for n in V.ORDER:
    for im in poses[n].values():
        A |= im[..., 3] > 0
ys, xs = np.nonzero(A); y0, y1, x0, x1 = ys.min() - 2, ys.max() + 3, xs.min() - 2, xs.max() + 3
ox, oy = V.CONFIG["OFF"]
foot_x, foot_y = ox + 48 - x0, 91 + oy - y0     # feet centre inside the crop

BG = (46, 50, 60, 255); G1 = (58, 62, 74, 255); G2 = (66, 70, 84, 255)
LANE_W, LANE_H = TILE * (TRAVEL + 2), TILE * 2
def lane_bg(vertical):
    W, H = (TILE * 2, TILE * (TRAVEL + 2)) if vertical else (LANE_W, TILE)
    im = Image.new("RGBA", (W, H), BG); d = ImageDraw.Draw(im)
    for i in range(0, W // TILE + 1):
        for j in range(0, H // TILE + 1):
            if (i + j) % 2 == 0:
                d.rectangle([i * TILE, j * TILE, i * TILE + TILE - 1, j * TILE + TILE - 1], fill=G1)
    # destination tile marker
    return im

def tint(img, alpha):
    out = img.copy(); a = out[..., 3] > 0
    out[a, 3] = alpha
    out[a, :3] = (out[a, :3] * 0.5 + np.array([120, 200, 232]) * 0.5).astype(np.uint8)
    return out

def place(lane, pose, tile_pos, view, ghost=None):
    """paste a pose with its feet centred on the tile position (in tiles, along the travel axis)"""
    crop = Image.fromarray(pose, "RGBA").crop((x0, y0, x1, y1))
    vertical = view in ("front", "back")
    if vertical:
        cx = TILE; cy = int(TILE * (tile_pos + 1.0) + TILE * 0.9)   # feet row inside tile
    else:
        cx = int(TILE * (tile_pos + 1.0) + TILE * 0.5); cy = int(TILE * 0.9)
    lane.alpha_composite(crop, (cx - foot_x, cy - foot_y))

# timeline: (pose, start tile, end tile, ms); travel along the lane over the two burst poses with afterimages
T0, T1 = 0.0, float(TRAVEL)
steps = [("idle", 0, 0, 400), ("crouch", 0, 0, 120)]
N = 6
for i in range(N):
    a, b = T0 + (T1 - T0) * (i / N) ** 1.4, T0 + (T1 - T0) * ((i + 1) / N) ** 1.4
    steps.append(("burst" if i % 2 == 0 else "burst2", a, b, 55))
steps += [("settle", T1, T1, 140), ("idle", T1, T1, 400)]
frames, durs = [], []
for pose_name, a, b, ms in steps:
    pos = b
    # facing: right view and back/front lanes move toward +; left view moves toward the start
    lanes = []
    for n in V.ORDER:
        vertical = n in ("front", "back")
        base = lane_bg(vertical)
        sign = {"right": 1, "left": -1, "front": 1, "back": -1}[n]
        p = pos if sign > 0 else (T1 - pos)
        p_prev = a if sign > 0 else (T1 - a)
        if pose_name in ("burst", "burst2"):
            for k, al in ((3, 70), (2, 110), (1, 160)):    # afterimages trailing behind the unit
                q = p - (p - p_prev) * k * 0.9 - (0.12 * k) * sign * (1 if sign > 0 else -1) * 0
                ghost = tint(poses[n][pose_name], al)
                place(base, ghost, p_prev - (p - p_prev) * (k - 1) * 0.0 - 0.28 * k * (1 if sign > 0 else -1), n)
        place(base, poses[n][pose_name], p, n)
        lanes.append(base)
    W = lanes[0].width + lanes[1].width
    sheet_w = max(lanes[0].width, lanes[1].width)
    # layout: right lane, left lane stacked; vertical lanes side by side below
    hz = [lanes[V.ORDER.index("right")], lanes[V.ORDER.index("left")]]
    vt = [lanes[V.ORDER.index("front")], lanes[V.ORDER.index("back")]]
    total_w = max(hz[0].width, vt[0].width + vt[1].width + 8)
    total_h = hz[0].height + hz[1].height + 8 + vt[0].height + 8
    canvas = Image.new("RGBA", (total_w, total_h), (30, 32, 40, 255))
    y = 0
    for im in hz:
        canvas.alpha_composite(im, (0, y)); y += im.height + 8
    canvas.alpha_composite(vt[0], (0, y)); canvas.alpha_composite(vt[1], (vt[0].width + 8, y))
    frames.append(canvas.resize((canvas.width * S, canvas.height * S), Image.NEAREST).convert("P", palette=Image.ADAPTIVE))
    durs.append(ms)
frames[0].save("out/tl_dash_scene_2x.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0, disposal=2)
print(frames[0].size, len(frames), "frames", sum(durs), "ms per loop")
frames[4].convert("RGBA").save("out/dbg_dash_scene.png")
