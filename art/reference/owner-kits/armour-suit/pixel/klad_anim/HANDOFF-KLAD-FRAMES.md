# Sprite 2b animated frame by frame in klad: handoff

Status (2026-11-12): batch 18 done, waiting for approval. Nothing is in the Style Library.

## What was asked
"Use klad to do 2b frame by frame": animate sprite 2b itself in klad, not new frames from the 3D model. (The 3D-posed set from batch 17 is kept in `../anim/`.)

## Method (klad's pixel skill, Animation part)
- Source: sprite 2b's own pixels, `base_2b.grid` (the 92 px front view, before the outline).
- Each frame is made from the drawing by moving whole clusters by whole pixels (`klad_frames.py`, CONFIG block at the top), written to its own frame of a klad animation with `klad pixel --frame N --grid`, then klad redraws the outline, doubled corners in the outline are erased, and `klad check` runs on every frame.
- Moves used: `sink` (body above the waist drops 1 px), `lift` (a foot lifts 3 px, the leg shortens at the knee, and the shin shifts 1 px the way it walks), `lean` (body shifts 1 px sideways), `raise_sword` (blade ends in a taper above the ground), `spread` (legs 2 px apart each), `brighten` (dim lights become bright).

## Animations (in `out/`, 6 fps)
- `idle_3x.gif`, 4 frames: stand, sink 1 px, sink with the lights flaring, sink.
- `walk_left_3x.gif`, `walk_right_3x.gif`, 4 frames each: sink, step with the leading foot lifted and the body leaning that way, sink, step with the other foot. The knight faces the viewer in both; 2b has no side view.
- `battle_3x.png`, 1 frame: legs apart, body 2 px lower, sword off the ground, lights flared.
- `knight_2b_klad_frames_sheet_3x.png`: every frame. `<anim>_sheet_1x.png`: real-size sheets. `<anim>.klad`: the klad animations.

## Gates (`check_anim.py`): all four PASS
- 90 to 92 px tall, 19 to 20 colours, 3.4 to 3.9% isolated pixels (lights not counted), no semi-transparent pixels, one piece, feet on one ground row.
- Frame-to-frame change: idle 7 to 31%, walks 48 to 49%.
- `klad check` over all 13 frames: 651 stray pixels (mostly the single-pixel lights), 550 doubled corners, 129 banding, 9 jagged lines; inherited from sprite 2b, not fixed by hand.

## Known weak points
- Checked as still frames only; the GIFs were not watched in motion.
- Walk left and walk right are front-facing steps that differ only by a 1 px lean and which foot leads; they do not read strongly as left or right.
- The foot lift is 3 px and subtle; arms and sword do not move apart from sinking with the body.
- The battle pose is a braced stance, not a swing; the sword is not raised.
