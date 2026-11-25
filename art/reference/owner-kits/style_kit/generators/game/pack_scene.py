"""Packs the approved suit-style scene set (approved/scene, from scene/scene_suitstyle.py) for the game: python3 pack_scene.py (after pack_sprites.py).
Per size (96, 64): a terrain sheet in game order [ground0-4, bush, bush_s, bush_down, ore, ore_down, wreck, storm, stele, lantern, rubble] baked at
four light levels (lit, normal, dim, dark: palette steps toward the highlight or the outline, opaque), plus an FX sheet with alpha 0/255 only:
checkerboard contact shadows (suit, bush, ore, prop) and the player ring. Verifies the 96 source is byte-identical to the approved sheet.
Appends SCENE_DATA to sprites_block.js."""
import io, json, base64, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "../scene")

ORDER = ["ground0", "ground1", "ground2", "ground3", "ground4", "bush", "bush_s", "bush_down", "ore", "ore_down", "stele", "lantern", "rubble"]
LEVELS = [-0.14, 0.0, 0.35, 0.65]        # lit, normal, dim, dark (negative = toward the highlight)
OUT, HI, SHADE = (13, 20, 24), (69, 86, 106), (26, 35, 43)
SHADOWS = {"suit": (36, 10), "bush": (40, 10), "ore": (30, 8), "prop": (26, 7)}   # half-axes at 96


def darken(a, step):
    a = a.copy(); on = a[..., 3] > 0; tgt = np.array(OUT if step >= 0 else HI, np.float32); k = abs(step)
    rgb = a[..., :3].astype(np.float32); rgb[on] = np.round(rgb[on] + (tgt - rgb[on]) * k); a[..., :3] = rgb.astype(np.uint8); return a


def url(im):
    b = io.BytesIO(); im.save(b, "PNG", optimize=True); return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode(), len(b.getvalue())


out = {}
for S in (96, 64):
    tag = "" if S == 96 else "64"
    src = Image.open(f"../out/suitstyle{tag}_tiles_1x.png").convert("RGBA")
    ap = Image.open(f"../approved/scene/suitstyle{tag}_tiles_1x.png").convert("RGBA")
    a = np.asarray(src); 
    if a.shape[:2] != (S, S * len(ORDER)): print("FAIL size", S, a.shape); sys.exit(1)
    # the approved sheet was frozen before bush_down/ore_down were added at indices 7 and 9: compare the shared tiles by name
    ap_a = np.asarray(ap); ap_names = [n for n in ORDER if n not in ("bush_down", "ore_down")]
    for n in ap_names:
        i, j = ORDER.index(n), ap_names.index(n)
        if not np.array_equal(a[:, i * S:(i + 1) * S], ap_a[:, j * S:(j + 1) * S]): print("FAIL", S, n, "differs from approved"); sys.exit(1)
    old = np.asarray(Image.open(f"../tiles/out/tiles{S}_sheet_1x.png").convert("RGBA"))   # approved wreck and storm overlays stay
    storm = old[:, 8 * S:9 * S]
    # the approved wreck was drawn over the old ground: lift its overlay (pixels that differ from the old ground_a) onto the new slab ground
    ow = old[:, 7 * S:8 * S]; m = (ow[..., :3] != np.array([0x14, 0x11, 0x0f])).any(axis=2)   # the sheet filled the overlay's empty pixels with #14110f
    wreck = a[:, 2 * S:3 * S].copy(); wreck[m] = ow[m]
    sheet = np.concatenate([a[:, :10 * S], wreck, storm, a[:, 10 * S:]], axis=1)
    al = sheet[..., 3]
    if ((al > 0) & (al < 255)).any(): print("FAIL semi-transparent", S); sys.exit(1)
    k = S / 96.0; sheets = []; total = 0
    for lv in LEVELS:
        u, n = url(Image.fromarray(darken(sheet, lv))); sheets.append(u); total += n
    # fx sheet: shadows (checkerboard of the stone shade, opaque pixels only) and the player ring
    fx = np.zeros((S, S * 5, 4), np.uint8); yy, xx = np.mgrid[0:S, 0:S]
    for i, (name, (rx, ry)) in enumerate(SHADOWS.items()):
        cx, cy = S / 2, S / 2; e = ((xx - cx) / (rx * k)) ** 2 + ((yy - cy) / (ry * k)) ** 2
        m = ((e <= 0.6) & ((xx + yy) % 2 == 0)) | ((e > 0.6) & (e <= 1.0) & ((xx + yy) % 4 == 0))
        fx[:, i * S:(i + 1) * S][m] = SHADE + (255,)
    e = ((xx - S / 2) / (36 * k)) ** 2 + ((yy - S / 2) / (11 * k)) ** 2; band = (e > 0.8) & (e <= 1.0)
    ring = fx[:, 4 * S:5 * S]; ring[band & ((xx + yy) % 2 == 0)] = (123, 208, 192, 255); ring[band & ((xx + yy) % 2 == 1)] = (75, 106, 120, 255)
    u, n = url(Image.fromarray(fx)); total += n
    out[str(S)] = {"sheets": sheets, "fx": u, "n": len(ORDER) + 2}
    print("scene", S, "PASS", total, "bytes")
json.dump({"ORDER": ORDER[:10] + ["wreck", "storm"] + ORDER[10:], "FX": list(SHADOWS) + ["ring"]}, open("scene_order.json", "w"))
open("sprites_block.js", "a").write("const SCENE_DATA = " + json.dumps(out) + ";\n")
