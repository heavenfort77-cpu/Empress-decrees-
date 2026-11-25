# Klad knight 2b, animated: handoff

Status (2026-11-12): batch 17 done, waiting for approval. Nothing is in the Style Library.

## What was asked
Animate klad knight 2b frame by frame: idle, walk left, walk right, and a battle pose. The user chose "same way as 2b": pose the 3D model for each frame, then make every frame in klad exactly as 2b was made (2b exists only as a front view, so side views had to be new frames).

## Files (in `out/`)
- `knight_2b_animation_sheet_3x.png`: every frame, enlarged 3x, labelled.
- `idle_3x.gif` (4 frames), `walk_left_3x.gif` (6), `walk_right_3x.gif` (6): 8 fps, exported by klad. `battle_3x.png`: the battle pose (1 frame).
- `idle_sheet_1x.png`, `walk_left_sheet_1x.png`, `walk_right_sheet_1x.png`, `battle_sheet_1x.png`: sprite sheets at real size, 96 px frames in a row.
- `<anim>_<n>.png`: single frames at real size. `<anim>.klad`: the klad animations (one pixel layer, one drawing per frame).
- Scripts: `capture.py` (run from the `3d` folder; captures each pose twice: plain material colours, and the full render), `build_anim.py` (CONFIG block at the top; cut at a fixed scale and ground line, `klad pixelize` for materials, light from the render, lights, grid into klad, outline, corner fix, check, export), `check_anim.py` (gates), `make_sheet.py`.

## How the frames are made
- The 3D knight gained movable parts (`3d/main.js`, previous script `3d/main_v18_backup.js`): upper body pivoting at the pelvis, each leg with hip and knee pivots, and the sword as its own group. Poses are in `POSES` near the end of `main.js`; `window.__pose(name, i)` applies one and puts the lowest foot on the ground.
- Idle: breathing, a slight knee bend, sword planted. Walk: six frames, sword carried upright with the blade's flat toward the camera. Battle: lunge with the sword raised, body turned.
- Captures use a level camera with no perspective, and the lights turn with the camera so the light stays on the viewer's upper left in every view.
- Brightness thresholds for the ramps are measured once on idle frame 0 and reused for every frame, so tones do not flicker between frames.

## Sizes
- Frame 96 px, 38 sprite px per metre: the knight is 79 px tall here (2b alone was 92 px) so the raised sword fits; with the sword raised the sprite is 88 to 90 px tall. Feet stand on row 91 in every frame.

## Gates (`check_anim.py`)
- idle PASS, walk_right PASS, battle PASS.
- walk_left FAIL on 4 of 6 frames: isolated pixels 7.7 to 7.8% against a 7.5% limit (lights are not counted). Not fixed.
- 15 to 18 colours per frame, no semi-transparent pixels, one piece, feet on one ground row.
- Frame-to-frame change: idle 23 to 37% (the whole body moves 1 px when it breathes), walks 61 to 76%.
- `klad check` over all 17 frames: 573 stray pixels (mostly the single-pixel lights), 418 doubled corners, 126 banding, 35 jagged lines. These are places to look at, not fixed by hand.

## Known weak points
- Checked as still frames only; the GIFs were not watched in motion, so foot sliding or flicker is unverified.
- Each frame is converted on its own, so static areas can change a few pixels between frames (shimmer), most likely on the torso during the walk.
- Arms do not swing: both hands stay on the sword in every pose.
- Feet tilt with the shin, so toes point down on the back swing.
- The battle pose is one frame; the face is hidden behind the raised sword.
- Idle is smaller than sprite 2b (79 px against 92 px).

## Next (only after approval)
1. Watch the GIFs and fix sliding or shimmer.
2. Front and back walk, attack frames.
3. The same for the other three characters.
