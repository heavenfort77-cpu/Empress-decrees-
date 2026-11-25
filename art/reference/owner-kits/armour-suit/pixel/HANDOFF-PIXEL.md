# Techno-plate in pixel art, two methods: handoff

Status (2026-11-12): batch 16 done, knight only, waiting for the user to pick a method. Nothing is in the Style Library.

## What was asked
Do the techno-plate style in pixel art two ways with the cocolito flow, and show them in a strip to compare:
1. Pixel art made in code.
2. Pixel art made with klad, following klad's three skills (`klad skill`, `klad skill drawing`, `klad skill pixel`).
Only the knight was made, as the one sample to approve before the other three.

## Files
- `compare_strip_knight.png`: 3D model, method 1, method 2; enlarged 3x on top, real size (96 px) underneath.
- Method 1 (changed in batch 15 at the user's request): the knight is now drawn in code with the cocolito passes, not converted from a 3D render. `m1_knight_1x.png`, `m1_knight_3x.png`, script `cocolito_knight.py` (Pillow; passes: silhouette, flat colours, each plate lit as a rounded form from the upper left with reflected light on its far edge, cast shadows, outline in the darkest tone of the touching material, seeded wear; hand-written ramps and all values in its CONFIG block).
- `knight_shapes.py`: the knight as flat shapes, shared by both methods so they draw the same design.
- Dropped from the strip, kept for the record: the 3D-render-to-pixel try, `render_to_pixel_knight_1x.png` and `_3x.png`. Scripts: `render_src.py` (captures the 3D knight on a magenta backdrop with flat matt materials and one key light; run from the `3d` folder), `to_pixel.py` (area-average down to 85 px tall, median-cut palette of 18 plus 2 glow colours, hard alpha, stray-pixel merge, 1 px dark outline). CONFIG block at the top of `to_pixel.py`.
- Method 2: `klad/m2_knight_1x.png`, `klad/m2_knight_3x.png`, `klad/knight.klad` (the klad drawing), `klad/knight.grid` (the sprite as klad grid text). Scripts: `klad/knight_grid.py` (plans the knight as flat material shapes with one light from the upper left, shadow shapes under overhangs, small highlights; CONFIG block at the top), `klad/build_knight.sh` (new 96x96 pixel drawing, hue-shifted ramps with `klad palette --ramp`, grid in, `--outline`, corner fix, export), `klad/fix_corners.py` (erases doubled corners in the outline until `klad check` finds none there).
- `check_px.py`: the pixel gates (96 px frame, height 72 to 94, feet gap 1 to 2, no semi-transparent pixels, 26 colours or fewer, 6% isolated pixels or fewer, one piece). Both sprites PASS.
- `make_strip.py`: builds the strip.
- The 3D page gained `window.__sprite(true/false)` for the capture (`3d/main.js`; previous script `3d/main_v17_backup.js`).

## Batch 16: klad version 2, closer to the 3D render (user request)
- Version 1 is kept: `klad/m2v1_knight_1x.png`, `_3x.png`, drawing `klad/knight_v1.klad`, built by `klad/build_knight.sh`.
- Version 2 is now `klad/m2_knight_1x.png`, `_3x.png`, drawing `klad/knight.klad`, built by `klad/build_knight_v2.sh`:
  1. `klad/prep_refs.py` cuts the knight out of the two 3D captures (flat matt, and the full render).
  2. `klad pixelize --image flat_knight_alpha.png --size 92` puts the flat capture on a pixel layer in the sprite's own palette; that gives each pixel its material.
  3. `klad/finish_from_render.py` (CONFIG block at the top) keeps the material, takes light and shade from the full render's brightness (lightly smoothed, cut into each ramp's steps at the render's own percentiles), merges stray pixels, and makes a pixel a light wherever the render glows.
  4. Back into klad as a grid, `--outline`, corner fix, `klad check`, export.
- Measured with `klad compare` against the render shrunk to the same 96 px frame (`klad/ref96.png`), figure area only: mean colour difference 6.5 for version 1 and 2.7 for version 2 (OKLab x100); version 1 was darker by 6 L, version 2 by 3 L. Both are still busier and sharper-edged than the render, as pixel art is.
- Version 2: 92 px tall, 50 px wide (the render's proportions; version 1 is about 66 px wide), 20 colours, 4.1% isolated pixels, PASS. `klad check`: 51 stray pixels (mostly the single-pixel lights, which are meant), 43 doubled corners, 9 banding.
- The strip now has four panels: 3D model, method 1 (code), klad version 1, klad version 2.

## klad
- Built from the `feature/pixelart` branch (klad 0.1.19, commit 2214ac6), because `klad skill pixel` and the pixel-layer commands are only on that branch; `main` (0.1.17) lacks them. Build: `CARGO_TARGET_DIR=target/linux cargo build --release -p klad-cli`, about 12 minutes, started detached.
- Licence: source-available, not open source. Do not distribute the klad build or put klad code in a game; ship only exported PNGs and credit klad in CREDITS if its output is used.
- `klad check` on the knight after fixes: 28 doubled corners (in small details such as the brow, horns and cheek blades), 10 banding (the fluting and light strips, which are meant), 2 jagged lines (outline at the elbows). No stray pixels.

## Measured
- Method 1 (code-drawn): 94 px tall, 23 colours, 2.1% isolated pixels.
- Method 2: 94 px tall, 18 colours (20 palette entries), 1.8% isolated pixels.

## Known weak points
- Method 1: strong light-to-dark contrast makes the plates look round and metallic, but the pure grey ramp is colder and the busy shading on the legs and torso reads noisier at real size. 23 colours, near the 26 limit.
- klad version 1: clean and readable, but flatter and more toy-like than the 3D model; only the front view exists, and every other view is a new drawing.
- klad version 2: closest to the render in proportion, light and trim, but busier at real size; the mask's face is hard to read at 96 px; hands and sword grip merge; more stray-pixel and corner findings than version 1.
- Both sprites now come from the same shapes and are the same height, so the strip is like-for-like; only the shading rules, ramps and outline differ.

## Next (only after the user picks)
1. The other three characters with the chosen method.
2. Side and back views.
