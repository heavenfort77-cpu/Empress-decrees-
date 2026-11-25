# Suit Mythology style kit (cocolito entry 1), v2 2026-11-06

Everything needed to draw new art in this style in a future chat. Upload this zip (or the files you need) and say "use the Suit Mythology style kit".

## What is in it
- `Style-Library-additions.md`: the entry's new sections (defeat, walk, 猿魔 attack, scene set, build rules). The full entry is `claude/Style-Library.md` in the Project; paste these additions under entry 1 when you update it.
- `HANDOFF_batch11.md`: batches 11-15 of the game handoff (what is in the build, what is next).
- `generators/`: every generator script. All are Python 3 with Pillow, numpy and scipy. Every tunable is in each script's CONFIG block.
- `approved/`: the frozen approved samples (1x PNG sheets and GIFs) per suit and set. These are the reference; new art must match them by measurement.
- `suit_game.html`: the build as of this kit.

## How the style is drawn (the method every script shares)
1. A sprite is a list of parts: `(region, ramp, polygon, flat)`. Polygons are in a 96-space; the 64 rung re-plots the same polygons with `tianbing64_views.Xf/Yf`, never resizes.
2. `tianbing96_v5.build()` renders parts: mid fill, then a one-colour seam (#0d1418) on each part's bottom/right edge, a 2 px light band on the upper-left edge (1 px at 64), the lower-right third in the shade colour, rivet rows and bolt holes. Light from the upper left.
3. Ramps are three steps (shade, mid, light). Suit ramps: green #1a4541/#2e7358/#7bb565, bronze #8a5a2b/#c48c3c/#f2cb6a, steel #2d3846/#687a8a/#aebfcc, vermilion #c8432c/#ff925c, visor #c2fff1. Scene stone ramp #1a232b/#2b3744/#45566a. Outline #0d1418 everywhere.
4. Views: `*_views.py` builds front, left, back, right (left and right are separate drawings; back = mirrored front plus back-only parts).
5. Animation: `anim_runner.run(prefix, size, {anim: specs}, frame_fn)`. `frame_fn(view, spec, size)` returns part transforms `T` (`mov`, `rot` about a pivot, `mirx`) plus optional `overlay`, `post`, `hide`, `extra`, `no_feet_check`, `recolour`. The runner runs the checks (height, feet, head share, isolated %, colours, one piece, frame change under 25%) and writes GIFs and sheets to `out/`.
6. Alpha is 0 or 255 only. No semi-transparent pixel anywhere, including shadows (checkerboards) and light levels (baked sheets).

## Running
```
python3 tianbing96_views.py            # 天兵 four views + thrust at 96 (tianbing64_views.py for 64)
python3 mingjiang_anims.py 64          # a suit's own animations at a size
python3 suit_hit.py wushi 96           # hit set from the approved sample      (suit_defeat.py, suit_walk.py likewise; add a stage for yuanmo: suit_walk.py yuanmo 64 2)
python3 yuanmo_attack.py 2 96          # 猿魔 attack for a stage and size
python3 tiles/tiles96.py 64            # ground tile sheet (approved set)
python3 scene/scene_suitstyle.py       # suit-style scene set at 96 (SIZE=64 python3 scene/scene_suitstyle.py for 64)
python3 pack_anims.py                  # packs hit/defeat/walk and the action anims into game/anims_block.js (one worker per suit/size)
cd game && python3 pack_sprites.py && python3 pack_scene.py && python3 build_game.py && node game_test.js
```
Scripts expect to run from the folder that holds them (the game scripts from `game/`, with `../out`, `../approved`, `../proto` beside it).

## Adding a new suit
Copy `tianbing96_v5.py` for the parts and palette, `tianbing96_views.py` for the views, then add the suit to `suit_hit.py` CONFIG (MODULE, PLANTED, PREFIX); hit, defeat and walk then come from the shared samples. Draw one sample at play size and wait for approval before the rest.

## Added in v2
- `generators/knight96.py`, `generators/set96.py`: the cocolito standard set (knight, mage, rogue, furnace golem) as part data through the same renderer; `python3 set96.py` draws all four fronts and the lineup. Samples in `approved/standard_set/` (drawn, not yet approved).
- `generators/blender/`: the 3D route. `prep3d.py` exports any character's part data to JSON; `set3d_render.py` builds quad-remeshed models and renders them in Cycles (`python3 -I set3d_render.py -- set3d.json OUT all|lineup|levels knight`); `skin3d.py` makes one skinned all-quad mesh per character with a 16-bone skeleton, weights, rigid props, a test pose and a GLB (`python3 -I skin3d.py -- set3d.json OUT tianbing`). Needs `pip install --break-system-packages bpy`.
- `suit_game.html` is now the B.O.I release build (same as the itch zip); `generators/game/shell_template.html` is its source.
- The game build alone is NOT enough to make new art: it holds finished pictures, not the generators. Always bring this kit.
