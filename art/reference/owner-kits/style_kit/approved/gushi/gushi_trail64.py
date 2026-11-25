"""蛊师 erosion trail tiles at 64 x 64 (redrawn at 64 geometry, not resized): straight + turn, fresh/old/fading.
Run: python3 gushi_trail64.py -> out/gs64_trail_shapes_3x.png, gs64_trail_road_3x.png, gs64_trail_straight_{state}_1x.png"""
import numpy as np
from PIL import Image
import gushi_trail as T
T.CONFIG.update({"N": 64, "STEP": 8, "SEG": (8, 6), "PFX": "gs64"})
fails = T.make_shapes()
for shape in ("straight", "turn"):
    for i, st in enumerate(T.CONFIG["STATES"]):
        Image.fromarray(T.tile_shape(shape, st, T.CONFIG["SEED"] + 7 + i), "RGBA").save(f"out/gs64_trail_{shape}_{st}_1x.png")
