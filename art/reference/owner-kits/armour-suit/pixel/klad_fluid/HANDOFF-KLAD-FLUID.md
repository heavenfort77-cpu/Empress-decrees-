# Sprite 2b, fluid animation with klad only: handoff

Status (2026-11-12): batch 19 done, waiting for approval. Nothing is in the Style Library.

## What was asked
"Using only klad to do the animation of 2b, make it fluid; current version is mechanical."

## Method: klad commands only (`klad_only.sh`, CONFIG block at the top)
- Sprite 2b (`base_2b.grid`) is written into seven pixel layers and each is trimmed to one body part with `klad pixel --erase --rect`: leg_l, leg_r, hips (a plain band drawn with klad, seen when the sword lifts), body, sword, shoulders, head.
- Each part has its own outline layer (`klad pixel --outline --ref <part>`) placed under all the part layers, so the visible outline is always the outline of the whole figure, and it moves with the parts.
- Motion is klad's own layer keys with `--ease in-out` (`klad key`). Parts start their moves one or two frames apart (body, then shoulders, then head; the sword a frame behind the body), so the figure flows instead of stepping all at once.
- Timeline: 24 frames at 12 frames a second; the exported loop is frames 12 to 23.
- No Python or 3D is used to make the frames. Python is only used afterwards for my gates, the contact sheet and the player page.

## Animations (in `out/`)
- `idle_3x.gif`: body sinks and rises 1 px, shoulders a frame later, head two frames later; sword planted.
- `walk_left_3x.gif`, `walk_right_3x.gif`: each foot lifts 3 px with easing and swings 1 px the way it walks; the body bobs on each footfall with shoulders, head and sword following late; the sword is carried 4 px off the ground. Front-facing: 2b has no side view.
- `battle_3x.gif`: legs 2 px apart each, body 2 to 3 px low and breathing, sword raised 10 px and swaying 1 px side to side.
- `knight_2b_fluid_sheet_2x.png`: every frame. `<anim>_sheet_1x.png`: real-size sheets (12 frames in a row). `<anim>_<n>.png`: single frames. `<anim>.klad`: the klad animations.
- `../knight_2b_animations.html`: plays this set and the two earlier sets.

## Gates (`check_anim.py`): all four PASS
- 89 to 92 px tall, 18 to 20 colours, 3.2 to 3.7% isolated pixels (lights not counted), no semi-transparent pixels, one piece, feet on one ground row.
- Frame-to-frame change: idle 0 to 17% (three moving frames, then a hold, twice a loop), walks 11 to 28% on every frame, battle 0 to 23%.

## What I found out about klad on the way
- `klad pixel --outline --ref all` does not follow keyed layer offsets; it outlines the layers where they were drawn. That is why each part carries its own outline layer.
- Keys may sit past the last frame of the timeline.
- Keyed pixel layers move by whole pixels; in-between values are rounded.

## Known weak points
- Checked as still frames and by the numbers only; the motion itself was not watched.
- All moves are 1 to 3 px, so "fluid" here means staggered and eased, not large sweeping motion. The idle holds still for six frames of every twelve.
- The walk still faces the viewer; left and right differ by a 1 px lean and which foot leads.
- Arms do not move apart from the shoulders layer; the hands stay on the grip while the sword layer moves, so the grip and guard separate by a few pixels when the sword is raised.
- The doubled-corner clean-up of the outline was not done for this set.
