"""Hit reaction for every suit from the approved 天兵 sample (tianbing_hit.py): python3 suit_hit.py <suit> [96|64] [stage]
Same three frames (flash in the suit's glow colour, 3 px recoil with a 10 degree head roll, recover). Upper body = every region except
legs, skirt and planted ground props (listed in CONFIG["PLANTED"]); the neck pivot is measured from the idle head pixels (centre x, bottom row)."""
import sys, importlib
import numpy as np
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R
import tianbing_hit as H

CONFIG = {
    "MODULE": {"tianbing": None, "wushi": "wushi_views", "tianlong": "tianlong_views", "jianxian": "jianxian_views", "mingjiang": "mingjiang_views",
               "mojiang": "mojiang_views", "gushi": "gushi_views", "yuanmo": "yuanmo_views"},
    "PLANTED": {"wushi": ("halberd",), "mojiang": ("mallet",), "yuanmo": (), "jianxian": ("bladeA", "bladeB", "bladeC", "ringC"), "tianlong": (), "mingjiang": ("cloak",)},
    "SHOVE": {"yuanmo1": 2},
    "ROLL_SIGN": {"left": -1}, "ROLL_K": {"tianlong": 0.5, "mingjiang": 0.0, "yuanmo1": 0.4},   # long necks: half the roll keeps the head attached   # stage 1 ape: its knuckled arm rests on the ground, so 3 px splits it
    "PREFIX": {"wushi": "ws", "tianlong": "tl", "jianxian": "jx", "mingjiang": "mj", "mojiang": "mo", "gushi": "gs", "yuanmo": "ym"},
}
NECK = {}


def measure_necks(size):
    for name in V.ORDER:
        img, body, legs, heads = R.build_frame(name, ("idle",), size, lambda n, s, z: dict(T=None))
        ys, xs = np.nonzero(heads)
        NECK[name] = (float(xs.mean()), float(ys.max()) - 2)


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, shove, roll, flash, _ms = spec; shove = min(shove, CONFIG["SHOVE"].get(KEY, 9))
    ax, ay = H.AWAY[name]; k = H.SZ["k"]
    regions = {p[0] for p in V.VIEWS[name]["parts"]} - {"legL", "legR", "skirt"} - set(CONFIG["PLANTED"].get(SUIT, ()))
    T = {r: [("mov", ax * shove * k, ay * shove * k)] for r in regions}
    nx, ny = NECK[name]
    T["head"] = [("rot", nx, ny, roll * CONFIG["ROLL_SIGN"].get(name, 1) * CONFIG["ROLL_K"].get(KEY, 1)), ("mov", ax * shove * k, ay * shove * k)]
    return dict(T=T, post=H.flash_post if flash else None, recolour=flash)


if __name__ == "__main__":
    SUIT = sys.argv[1]; KEY = SUIT + (sys.argv[3] if len(sys.argv) > 3 else ""); size = sys.argv[2] if len(sys.argv) > 2 else "96"; stage = int(sys.argv[3]) if len(sys.argv) > 3 else None
    H.SZ["k"] = 1.0 if size == "96" else 59 / 90
    m = importlib.import_module(CONFIG["MODULE"][SUIT])
    if SUIT == "yuanmo": m.setup(stage, size)
    else:
        try: m.setup(size)
        except TypeError: m.setup()
    measure_necks(size)
    prefix = CONFIG["PREFIX"][SUIT] + (str(stage) if stage else "") + ("" if size == "96" else "64")
    R.run(prefix, size, {"hit": H.CONFIG["HIT"]}, frame_fn)
