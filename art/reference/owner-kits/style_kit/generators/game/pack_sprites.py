# Packs APPROVED idle views into one sheet per (suit, size): 4 frames side by side (front, left, back, right), copied pixel for pixel (no resize).
# Verifies every frame is exactly SxS and that the packed sheet round-trips to the source bytes. Writes sprites_block.js.
import base64, io, json, sys
from PIL import Image
import numpy as np
A = "../approved/"
VIEWS = ["front", "left", "back", "right"]
SRC = {  # key -> {size: path pattern with {v}}
    "tianbing": {96: A + "tianbing96/views_idle_{v}_1x.png", 64: A + "tianbing64/v64_idle_{v}_1x.png"},
    "wushi": {96: A + "wushi/ws_idle_{v}_1x.png", 64: A + "wushi/ws64_idle_{v}_1x.png"},
    "tianlong": {96: A + "tianlong/tl_idle_{v}_1x.png", 64: A + "tianlong/tl64_idle_{v}_1x.png"},
    "jianxian": {96: A + "jianxian/jx_idle_{v}_1x.png", 64: A + "jianxian/jx64_idle_{v}_1x.png"},
    "gushi": {96: A + "gushi/gs_idle_{v}_1x.png", 64: A + "gushi/gs64_idle_{v}_1x.png"},
    "mingjiang": {96: A + "mingjiang/mj_idle_{v}_1x.png", 64: A + "mingjiang/mj64_idle_{v}_1x.png"},
    "mojiang": {96: A + "mojiang/mo_idle_{v}_1x.png", 64: A + "mojiang/mo64_idle_{v}_1x.png"},
    "yuanmo1": {96: A + "yuanmo/ym1_idle_{v}_1x.png", 64: A + "yuanmo/ym1_64_idle_{v}_1x.png"},
    "yuanmo2": {96: A + "yuanmo/ym2_idle_{v}_1x.png", 64: A + "yuanmo/ym2_64_idle_{v}_1x.png"},
    "yuanmo3": {96: A + "yuanmo/ym3_idle_{v}_1x.png", 64: A + "yuanmo/ym3_64_idle_{v}_1x.png"},
}
out, bad, total = {}, [], 0
for key, sizes in SRC.items():
    for S, pat in sizes.items():
        frames = [Image.open(pat.format(v=v)).convert("RGBA") for v in VIEWS]
        for v, f in zip(VIEWS, frames):
            if f.size != (S, S): bad.append(f"{key} {S} {v}: size {f.size}")
        sheet = Image.new("RGBA", (S * 4, S), (0, 0, 0, 0))
        for i, f in enumerate(frames): sheet.paste(f, (i * S, 0))
        a = np.asarray(sheet)
        for i, f in enumerate(frames):
            if not np.array_equal(a[:, i * S:(i + 1) * S], np.asarray(f)): bad.append(f"{key} {S} frame {i} not identical")
        b = io.BytesIO(); sheet.save(b, "PNG", optimize=True)
        out.setdefault(key, {})[str(S)] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
        total += len(b.getvalue())
print("sheets", sum(len(v) for v in out.values()), "bytes", total, "FAIL" if bad else "PASS", *bad, sep="\n" if bad else " ")
if bad: sys.exit(1)
open("sprites_block.js", "w").write("const SPRITE_DATA = " + json.dumps(out) + ";\n")

# ---- approved ground tiles: one sheet per size, 9 tiles of SxS in a row: ground a/b/c, bush, cut bush, ore, depleted ore, wreck (overlay), storm (overlay)
tiles = {}
for S in (96, 64):
    im = Image.open(f"../tiles/out/tiles{S}_sheet_1x.png").convert("RGBA")
    if im.size != (S * 9, S): print("FAIL tiles", S, im.size); sys.exit(1)
    al = np.asarray(im)[..., 3]
    if ((al > 0) & (al < 255)).any(): print("FAIL tiles", S, "semi-transparent"); sys.exit(1)
    if S == 96:  # the 96 sheet must be the approved one, byte for byte
        ap = Image.open("../approved/tiles/tiles96_sheet_1x.png").convert("RGBA")
        if not np.array_equal(np.asarray(im), np.asarray(ap)): print("FAIL tiles 96 differs from approved"); sys.exit(1)
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); tiles[str(S)] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
    print("tiles", S, "PASS", len(b.getvalue()), "bytes")
open("sprites_block.js", "a").write("const TILE_DATA = " + json.dumps(tiles) + ";\n")

# ---- approved props: 墨将 crossbow turret (intact, half, damaged) and 蛊师 erosion trail (straight/turn x fresh/old/fading), per size
PROPS = {
    "turret": {96: A + "mojiang/moprop_turret_{s}_1x.png", 64: A + "mojiang/moprop64_turret_{s}_1x.png"},
    "trail": {96: A + "gushi/gs_trail_{s}_1x.png", 64: A + "gushi/gs64_trail_{s}_1x.png"},
    "decay": {96: A + "decay/decay96_{s}_1x.png", 64: A + "decay/decay64_{s}_1x.png"},
}
STATES = {"decay": ["rot", "plant"], "turret": ["intact", "half", "damaged"], "trail": ["straight_fresh", "straight_old", "straight_fading", "turn_fresh", "turn_old", "turn_fading"]}
props = {}
for key, sizes in PROPS.items():
    for S, pat in sizes.items():
        frames = [Image.open(pat.format(s=st)).convert("RGBA") for st in STATES[key]]
        bad = [st for st, f in zip(STATES[key], frames) if f.size != (S, S)]
        al = [np.asarray(f)[..., 3] for f in frames]
        if bad or any(((x > 0) & (x < 255)).any() for x in al): print("FAIL props", key, S, bad); sys.exit(1)
        sheet = Image.new("RGBA", (S * len(frames), S), (0, 0, 0, 0))
        for i, f in enumerate(frames): sheet.paste(f, (i * S, 0))
        b = io.BytesIO(); sheet.save(b, "PNG", optimize=True); props.setdefault(key, {})[str(S)] = "data:image/png;base64," + base64.b64encode(b.getvalue()).decode()
        print("props", key, S, "PASS", len(b.getvalue()), "bytes")
open("sprites_block.js", "a").write("const PROP_DATA = " + json.dumps(props) + ";\n")
