# Style Library

## 1. Suit Mythology (xianxia-cyberpunk suit sprites), in use: all eight suits approved at 96 and 64 with idle, hit, defeat, walk; scene set approved (2026-11-06)
- Type: single
- Where: B.O.I: Battle of Ideal (Project "hunter or hunt"; suit battle royale on a grid). Desktop first, phone second. Style kit: suit_style_kit.zip (generators + approved samples + README).
- Source: study in claude/Suit-Mythology-Study.md (web research, 11 concept images, 3 pixel-art images; reference only, licences not stated). Technique reference only; all art is original.
- Look: nine factions (天兵, 猿魔, 巫师, 墨将, 剑仙, 冥将, 天龙, 蛊师, 虎魔), each with its own colours, shapes and role. Myth must change structure, not just surface. Faceless sensor head, visible joints and pistons. Dark-dominant values with seam lines, measured on the pixel reference sheet. Standalone: it inherits from no other style.
- Palette (天兵): outline #0d1418; green #1a4541 / #2e7358 / #7bb565; bronze #8a5a2b / #c48c3c / #f2cb6a; steel #2d3846 / #687a8a / #aebfcc; vermilion #c8432c / #ff925c; visor #c2fff1. 12-13 colours per sprite. No anti-aliasing. Scene stone ramp #1a232b / #2b3744 / #45566a.
- Outline and light: 1 px outline in #0d1418; light from the upper left, shaded per body region (2 px light band at 96, 1 px at 64), shade on the far third, outline-colour seams on lower-right part edges; rivet rows and bolt holes as the source of isolated pixels. The scene (ground plates, bushes, ore, props) uses the same renderer rules.
- Animation: parts move per frame (rotate about joints), redrawn at native pixels. Attack = halberd thrust, 5 frames, 570 ms (idle 120, wind-up 120, thrust 70, impact 160, recover 100). Hit 4 frames (flash, recoil 3 px with a 10 deg head roll, recover). Defeat 6 frames (flash, stagger, sag, fall, down; legs fold under, prop tips over). Walk 4 frames at 140/120 ms (contact, pass, contact, pass; feet on one ground row). Frames overflow the tile on a padded canvas anchored at the feet.
- Sizes:
| Frame | Height | Feet gap | Colours | Outline | Texture | Status | Files |
|---|---|---|---|---|---|---|---|
| 96x96 (desktop, primary) | 93 | 3 | 12-13 | 1 px | rivet rows every 3 px | approved 2026-11-06, all eight suits, idle + hit + defeat + walk; actions for seven | approved/ (per suit), tianbing96_views.py |
| 64x64 (phone; shown at whole-number scale 2 on dense screens) | 62 | 2 | 12-13 | 1 px | rivet rows every 4 px | approved 2026-11-06, same sets | approved/ (per suit, *64*), tianbing64_views.py |
- Technique: Python + Pillow + numpy + scipy. Parts are polygon data (region, ramp, polygon, flat); views and frames are data. 64 is re-plotted from the 96 polygons and rasterised natively, never resized. Shared animation sets (hit, defeat, walk) are drawn once as a 天兵 sample and derived for every suit by measuring each suit's own masks (suit_hit.py, suit_defeat.py, suit_walk.py).
- Samples, approved 2026-11-06: per suit in approved/<suit>/ (idle four views at 96 and 64, own animations), approved/hits/, approved/defeat/, approved/walk/, approved/yuanmo_attack/, approved/tiles/, approved/decay/, approved/scene/. All in suit_style_kit.zip.
## Additions to entry 1 (Suit Mythology), 2026-11-06, batches 11-15

- Game renamed B.O.I: Battle of Ideal (entry name stays Suit Mythology; Usage row: B.O.I).
- Defeat set APPROVED 2026-11-06: 天兵 sample (tianbing_defeat.py: flash, stagger, sag, fall, down; legs fold under the body, held prop tips over about the fist, 6 frames x 4 views) and the derived set for all suits at 96 and 64 (suit_defeat.py: hips and necks measured from the masks and converted to data space; TIP_PROPS fall, floating blades and pearl drop). Frozen in approved/defeat/.
- 猿魔 attack APPROVED 2026-11-06: stage 1 sample (yuanmo_attack.py: staff pound, both arms and the staff lift 16 px, body rises 3 px, drive down with a gold shock burst at the staff base; 6 frames x 4 views), stages 2-3 at 96 and 1-3 at 64 from the same data. Frozen in approved/yuanmo_attack/.
- Walk set APPROVED 2026-11-06: 天兵 sample (tianbing_walk.py: contact, pass, contact, pass at 140/120 ms; side legs scissor about the hips and are lifted back onto the ground row; front/back the stepping leg lifts 2 px and tilts; arms swing opposite; halberd rides with the body) and the derived set for all suits at 96 and 64 (suit_walk.py; SWING_K/LIFT_K per suit). Frozen in approved/walk/.
- Scene set APPROVED 2026-11-06 (scene/scene_suitstyle.py, frozen in approved/scene/): ground x5 plate layouts (jittered corners, grooves), bush tall/short, cut bush, ore, depleted ore, stele, lantern, rubble, at 96 and 64. Drawn with the suit renderer method (polygon parts, 3-step ramps, seam #0d1418 on the bottom/right edge, 2 px light band upper-left (1 px at 64), lower-right third shaded, rivet rows, bolt holes). New stone ramp #1a232b / #2b3744 / #45566a (median lum 52, the suits stay at 118-161). Tiles 5-11 colours, isolated under 2%, all opaque.
- Build rules added: contact shadows are checkerboards of the stone shade (#1a232b), alpha 0/255; light levels are baked sheets (lit toward #45566a by 0.14; dim/dark toward #0d1418 by 0.35/0.65), never a translucent fill; HUD bars are 2 px blocks with a #0d1418 outline; the wordmark "B.O.I" is a 7x9 pixel font in the bronze ramp with the suit bevel.
- Build notes: 2026-11-06 a wreck tile frozen with its empty pixels filled (#14110f) drew as a dark square in the game; lift overlays by their fill colour before packing. 2026-11-06 measuring pivots from masks gives canvas coordinates; subtract the pad and undo the flip (suit_defeat.to_data) before using them in part transforms. 2026-11-06 on dense phones the 64 art is shown at whole-number scale 2 (6x13 tiles visible); the title field and the match use one canvas transform.
- Open: 剑仙 array, 巫师 revive and 蛊师 skill frames are drawn but not in the game; 墨将 wins 1.9% (design fix); idle breathing animation not drawn.

## Usage
| Game | Style used | Size | Status |
|---|---|---|---|
| B.O.I: Battle of Ideal (hunter or hunt) | 1. Suit Mythology | 96 desktop, 64 phone (scale 2 on dense phones) | all eight suits approved with idle, hit, defeat, walk; actions for seven; scene set approved |
