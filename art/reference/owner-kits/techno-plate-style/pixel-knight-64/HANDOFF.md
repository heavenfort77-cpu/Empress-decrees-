# Techno-plate Knight, 64 px, four views: handoff

Status (2026-11-12): model 1 and model 2 drawn, waiting for approval. Nothing is in the Style Library. Nothing approved was replaced.

## What exists
- `model1_cocolito/`: `knight_<front|left|back|right>_1x.png`, `knight_4view_1x.png` (transparent strip, order front, left, back, right), `_3x`, `_8x` (grey background).
- `model2_klad/`: same file names, exported by klad 0.1.22 (main, which now holds the merged pixel-art branch, PR #24). `knight.klad` is the klad drawing (4 frames = 4 views), `knight.aseprite` the Aseprite export.
- `compare_3d_m1_m2.png`: 3D reference (front and side), model 1 (top row), model 2 (bottom row).
- `scripts/`: `knight.py` (the knight: shapes plus hand-placed head rows), `pxkit.py` (painter), `gen_m1.py`, `gen_m2.py`, `klad_clean.py`, `check.py`.

## How to run
- Model 1: `python3 gen_m1.py && python3 check.py out_m1` (Pillow, numpy).
- Model 2: `python3 gen_m2.py && python3 klad_clean.py` (needs the klad CLI; set `KLAD=/path/to/klad`).
- Tuning: the CONFIG block at the top of `gen_m1.py` / `gen_m2.py` (light, tone range, ramps, outline). Head pixels: `HEAD_FRONT` and `HEAD_SIDE` rows in `knight.py`.

## Design decisions
- Pose changed from the 3D (sword planted) to two hands on the grip, blade up at 45 degrees toward the knight's left, clear of the helm.
- Drawn from original shapes in code; no 3D render was scaled down.
- Model 1 and model 2 share the same shapes. Model 2 differs in palette (klad's hue-shifted ramps, 19 colours against 26), tone steps, and a clean-up driven by `klad check` (2 lone pixels, 29 one-pixel bands merged).

## Checks (code tool only, not seen on a phone)
- Both models, all four views: PASS (64x64, 0 semi-transparent pixels, one piece, feet on the same row, isolated pixels 1.9 to 4.8 %).
- Facing (side views): snout, toes, chest, hands and sword point forward; horns, pack and stacks sit behind.

## Known weak points
- The sprite uses rows 0 to 62: the crest and horn outline touch the top edge of the frame.
- Front view: the helm reads as a horned beast; the dragon read is stronger in the side views.
- Left view is the side drawing mirrored with the antenna moved to the far side and the blade one tone lighter, not a fully separate drawing.
- Fists are 5x4 px; the red grip shows only between and below them.
- Front view: the left fist and pommel overlap the top of the left hip plate.
- klad check still lists 45 doubled corners (steps in the outline and hand-placed face lines) and 2 jagged runs; left as they are.

## Next (only after approval)
1. Pick model 1 or model 2 (or name what to change).
2. Idle animation, then walk, for the chosen one.
3. Library entry for the 64 px rung.
