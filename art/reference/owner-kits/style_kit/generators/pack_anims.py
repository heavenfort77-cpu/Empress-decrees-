"""Re-renders approved animations on the full padded canvas and packs them for the game: python3 pack_anims.py
Output game/anims_block.js: ANIM_DATA[key][size][anim] = {w, h, ox, oy, n, ms:[...], src: data-url}; sheet rows = front, left, back, right,
columns = frames. (ox, oy) is where the tile's top-left sits inside a cell, so the game draws at (tileX - ox, tileY - oy). Nothing is resampled.
Frames keep their approved pixels; the cell is the union bbox over all views and frames, so every frame of one animation shares one anchor."""
import sys, io, json, base64, importlib
import numpy as np
from PIL import Image
import tianbing96_views as V
import anim_runner as R
import tianbing_hit as H
import suit_hit as SH

ANIMS = {"hit": H.CONFIG["HIT"]}
SUITS = [("tianbing", None), ("wushi", None), ("tianlong", None), ("jianxian", None), ("mingjiang", None), ("mojiang", None), ("gushi", None), ("yuanmo", 1), ("yuanmo", 2), ("yuanmo", 3)]
out = {}

def setup(suit, stage, size):
    H.SZ["k"] = 1.0 if size == "96" else 59 / 90
    if suit == "tianbing":   # its views are the module globals of tianbing96_views, already loaded
        if size == "64":
            import tianbing64_views as T64; T64.setup()
        return H.frame_fn
    SH.SUIT = suit; SH.KEY = suit + (str(stage) if stage else "")
    m = importlib.import_module(SH.CONFIG["MODULE"][suit])
    if suit == "yuanmo": m.setup(stage, size)
    else:
        try: m.setup(size)
        except TypeError: m.setup()
    SH.measure_necks(size)
    return SH.frame_fn

def stamp_eyes(a):
    """猿魔 at 64: the approved idle views got native 2x2 eyes with a catch-light (ym64_eyes.py); apply the same stamp to every hit frame"""
    V1, GLOW = (0xff, 0xcf, 0x40), (0xff, 0xf3, 0xb0)
    m = (a[..., :3] == np.array(V1)).all(2) & (a[..., 3] > 0)
    if m.sum() < 2: return a
    ys, xs = np.nonzero(m); left = xs <= xs.min() + 2
    if (~left).sum() == 0: return a
    y0 = ys.min()
    for x0 in (xs[left].min(), xs[~left].min()):
        for dy in (0, 1):
            for dx in (0, 1): a[y0 + dy, x0 + dx] = V1 + (255,)
        a[y0, x0] = GLOW + (255,)
    return a


def work(suit, stage, size, mode="hit"):
    key = suit + (str(stage) if stage else "")
    if mode == "act":
        import anim_actions as AA
        items = [(a, sp, f) for a, sp, f in AA.prepare(suit, stage, size)]
    else:
        fn = setup(suit, stage, size); items = [(a, sp, fn) for a, sp in ANIMS.items()]
        import suit_defeat as SD, tianbing_defeat as TD
        SD.SUIT = suit; SD.KEY = key; SH.SUIT = suit; SH.KEY = key; SH.measure_necks(size); SD.measure_hips(size); items.append(("defeat", TD.CONFIG["DEFEAT"], SD.frame_fn))
        import suit_walk as SW, tianbing_walk as TW
        SW.SUIT = suit; SW.KEY = key; SW.measure(size); items.append(("walk", TW.CONFIG["WALK"], SW.frame_fn))
    S = int(size); ox0, oy0 = V.CONFIG["OFF"]
    for anim, specs, fn in items:
        frames = {name: [R.build_frame(name, sp, size, fn)[0] for sp in specs] for name in V.ORDER}
        if suit == "yuanmo" and size == "64": frames = {n: ([stamp_eyes(f) for f in fr] if n == "front" else fr) for n, fr in frames.items()}
        alls = np.stack([f for name in V.ORDER for f in frames[name]])
        on = alls[..., 3].any(axis=0); ys, xs = np.nonzero(on)
        x0, y0, x1, y1 = min(xs.min(), ox0), min(ys.min(), oy0), max(xs.max() + 1, ox0 + S), max(ys.max() + 1, oy0 + S)
        w, h = int(x1 - x0), int(y1 - y0)
        sheet = Image.new("RGBA", (w * len(specs), h * 4), (0, 0, 0, 0))
        for r, name in enumerate(V.ORDER):
            for i, f in enumerate(frames[name]): sheet.paste(Image.fromarray(f, "RGBA").crop((x0, y0, x1, y1)), (i * w, r * h))
        al = np.asarray(sheet)[..., 3]; assert not ((al > 0) & (al < 255)).any()
        b = io.BytesIO(); sheet.save(b, "PNG", optimize=True)
        out.setdefault(key, {}).setdefault(size, {})[anim] = {"w": w, "h": h, "ox": int(ox0 - x0), "oy": int(oy0 - y0), "n": len(specs), "ms": [sp[-1] for sp in specs], "src": "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()}
        print(key, size, anim, "cell", w, h, "anchor", int(ox0 - x0), int(oy0 - y0), len(b.getvalue()), "bytes")

if __name__ == "__main__":
    if len(sys.argv) > 1:   # worker: one suit, stage, size, in its own process (the 64 setup mutates module state one way)
        suit, stage, size = sys.argv[1], (int(sys.argv[2]) if sys.argv[2] != "-" else None), sys.argv[3]
        mode = sys.argv[4] if len(sys.argv) > 4 else "hit"
        work(suit, stage, size, mode); json.dump(out, open(f"out/anim_{mode}_{sys.argv[1]}{sys.argv[2]}_{size}.json", "w"))
    else:
        import subprocess
        import anim_actions as AA
        for suit, stage in SUITS:
            modes = ["hit"] + (["act"] if AA.CONFIG["MAP"][suit] else [])
            for size in ("96", "64"):
                for mode in modes:
                    r = subprocess.run([sys.executable, "pack_anims.py", suit, str(stage) if stage else "-", size, mode], capture_output=True, text=True)
                    print(r.stdout.strip() or r.stderr.strip()[-400:])
                    if r.returncode: sys.exit(1)
                    for k, v in json.load(open(f"out/anim_{mode}_{suit}{stage if stage else '-'}_{size}.json")).items():
                        for sz, an in v.items(): out.setdefault(k, {}).setdefault(sz, {}).update(an)
        open("game/anims_block.js", "w").write("const ANIM_DATA = " + json.dumps(out) + ";\n")
        print("PASS")
