"""天兵 hit reaction at 96 (sample for the whole set; python3 tianbing_hit.py [96|64]). Three frames: flash (whole suit in the visor colour,
one palette colour, outline kept), recoil (upper body shoved 3 px away from its facing and the head rolled back), recover (half recoil).
Feet stay planted. Reuses the approved views and the part-moving renderer; nothing is resampled.
Run -> out/tb_hit_4views_2x.gif, out/tb_hit_sheet_1x.png (pass/fail only)"""
import sys
import numpy as np
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R

CONFIG = {
    # name, shove px (away from facing), head roll deg, flash, ms
    "HIT": [("idle", 0, 0, False, 120), ("flash", 0, 0, True, 60), ("recoil", 3, -10, False, 90), ("recover", 1, -4, False, 90)],
    "UPPER": ("torso", "head", "armL", "armR", "pauL", "pauR", "pagoda"),
    "NECK": {"front": (47.5, 36), "back": (47.5, 36), "left": (50, 36), "right": (45, 36)},
    "FLASH": "glow",
}
AWAY = {"front": (0, -1), "back": (0, 1), "left": (1, 0), "right": (-1, 0)}
SZ = {"k": 1.0}


def flash_post(body):
    out = F.hexrgb(F.CONFIG["PAL"]["out"]); col = F.hexrgb(F.CONFIG["PAL"][CONFIG["FLASH"]])
    a = body.copy(); on = a[..., 3] > 0
    keep = on & (a[..., :3] == np.array(out[:3])).all(axis=2)
    a[on & ~keep] = tuple(col[:3]) + (255,)
    return a


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, shove, roll, flash, _ms = spec
    ax, ay = AWAY[name]; k = SZ["k"]
    T = {r: [("mov", ax * shove * k, ay * shove * k)] for r in CONFIG["UPPER"]}
    nx, ny = CONFIG["NECK"][name]
    if size == "64":
        import tianbing64_views as T64; nx, ny = T64.Xf(nx), T64.Yf(ny)
    T["head"] = [("rot", nx, ny, roll if name != "left" else -roll), ("mov", ax * shove * k, ay * shove * k)]
    return dict(T=T, post=flash_post if flash else None, recolour=flash)


if __name__ == "__main__":
    size = sys.argv[1] if len(sys.argv) > 1 else "96"
    SZ["k"] = 1.0 if size == "96" else 59 / 90
    if size == "64":
        import tianbing64_views as T64; T64.setup()
    R.run("tb" if size == "96" else "tb64", size, {"hit": CONFIG["HIT"]}, frame_fn)
