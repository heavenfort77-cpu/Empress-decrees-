"""天兵 defeat sample at 96 (one sample for approval; python3 tianbing_defeat.py). Frames: flash (visor colour, as the approved hit), stagger (the hit recoil),
sag (upper body drops, head rolls back, legs begin to splay), fall (deeper), down (lying low; the wreck tile takes over after this).
Same part-moving renderer; nothing resampled. Run -> out/tb_defeat_4views_2x.gif, out/tb_defeat_sheet_1x.png (pass/fail only)"""
import sys
import tianbing96_v5 as F
import tianbing96_views as V
import anim_runner as R
import tianbing_hit as H

CONFIG = {
    # name, shove px (away from facing), drop px (upper body), head roll deg, leg fold deg (knees knock in; side views: knees forward), halberd tip deg, flash, ms
    "DEFEAT": [("idle", 0, 0, 0, 0, 0, False, 120), ("flash", 0, 0, 0, 0, 0, True, 60), ("stagger", 3, 2, -10, 0, 0, False, 90),
               ("sag", 3, 9, -25, 10, 15, False, 120), ("fall", 2, 18, -40, 20, 50, False, 130), ("down", 0, 26, -55, 28, 88, False, 260)],
    "HIP": {"front": ((40, 60), (55, 60)), "back": ((40, 60), (55, 60)), "right": ((48, 60), (46, 60)), "left": ((48, 60), (46, 60))},
    "FOLD": {"front": (-1, 1), "back": (-1, 1), "right": (1, 1), "left": (-1, -1)},    # rotation sign per leg so the feet gather under the body
    "TIP": {"front": 1, "back": -1, "right": 1, "left": -1},                           # halberd falls toward the facing side
}


def frame_fn(name, spec, size):
    if spec[0] == "idle": return dict(T=None)
    nm, shove, drop, roll, fold, tip, flash, _ms = spec
    ax, ay = H.AWAY[name]
    T = {r: [("mov", ax * shove, ay * shove + drop)] for r in H.CONFIG["UPPER"]}
    nx, ny = H.CONFIG["NECK"][name]
    T["head"] = [("rot", nx, ny, roll if name != "left" else -roll), ("mov", ax * shove, ay * shove + drop)]
    (lx, ly), (rx, ry) = CONFIG["HIP"][name]; sl, sr = CONFIG["FOLD"][name]
    legdy = drop * 0.35
    T["legL"] = [("rot", lx, ly, sl * fold), ("mov", 0, legdy)]
    T["legR"] = [("rot", rx, ry, sr * fold), ("mov", 0, legdy)]
    view = V.VIEWS[name]; fx, fy = V.apply_ops(T["armR"], *view["fist"])
    T["halberd"] = list(T["armR"]) + [("rot", fx, fy, CONFIG["TIP"][name] * tip)]
    return dict(T=T, post=H.flash_post if flash else None, recolour=flash, no_feet_check=True)


if __name__ == "__main__":
    R.run("tbd", "96", {"defeat": CONFIG["DEFEAT"]}, frame_fn)
