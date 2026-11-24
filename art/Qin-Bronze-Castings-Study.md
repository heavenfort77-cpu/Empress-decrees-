# Qin Bronze Castings (3D props, klad-textured): study

Own compartment for cast-bronze props and machines (asset list A13, C1-C11). The palace surfaces stay in their own study (art/Qin-Palace-Painted-Study.md, round 2 approved 24 Nov 21:03); this study shares only its texel density and klad method. Style Library not available in this Project: entry number <next number>, nearest neighbour "not checked".

- Reference: the GDD (docs/GDD.md, docs/BURNING-PALACE.md) decides what each piece is and must do; the research rule list (docs/research/Qin-palace-medieval-tech-fusion.md) and the reference report (docs/research/Sketchfab-Qin-palace-references.md: museum scans of Warring States bronzes, CC0, reference only) decide how it looks. Technique reference only; every model and texture is our own (owner 24 Nov 22:00-22:01). No image was copied or traced.
- Owner decisions in force: segmented bronze guardian beasts with silver inlay replace the stone lions (21:03); round where a form is round, sharp where it is sharp, never square and blocky (22:30); textures painted in klad (22:32); ComfyUI only if needed (22:32: not used in round 2, see Open).

## Studies this one builds on (owner 24 Nov 22:34: "add in these study")
Both uploads match the repo copies: the research report is identical to docs/research/Qin-palace-medieval-tech-fusion.md; the palace study upload is the first part of art/Qin-Palace-Painted-Study.md (the repo copy adds the round 2 sections).

From the research report (Sourced / Inference as marked there):
- Qin workshop craft is the look: the two Qin bronze chariots have more than 3,500 parts each, cast, welded, drawn, inlaid and polished, with gold and silver ornament and copper wire about 0.5 mm thick [S]; batch-cast crossbow triggers with filing marks and inscriptions [S]; Eastern Zhou bronze brassy and corrosion-free when new, ornament from master pattern stamps, gold, silver and copper inlay [S]; inlay (错金银) is wire pressed into grooves and polished flush [S].
- Legend gives the waking, never the look: Yan Shi's automaton organs (heart, liver, kidneys) for weak points [legend]; that rule belongs to the apex tiger, not to the guardian beasts.
- Props are re-made in Qin materials and labelled as invention: stone lions become segmented bronze guardian beasts with silver inlay; the 鼎 follows the Ne Zha 2 method (real Warring States proportions, deconstructed taotie) [I].
- Machines move by animal analogy (big cat for the tiger; oxen or tortoises for tread machines) [I]; fresh brass-gold on live machines, patina on dormant or sunk ones [I]; a workshop mark on every plate; deconstructed taotie, cloud scroll and invented sigils, no readable calligraphy [I].
- Palette starting values [I]: fresh bronze #C9A050 / high-tin #D8CDA8, verdigris #4F7A62, inlay gold #E2B84A / silver #C8CCD0, reserved hazard hue #3FE6F0 never used in decoration; cinnabar is decoration, never a hazard colour.
- Avoid: sci-fi panel lines, neon, glowing circuitry; green patina on live machines.
- Albedo-only klad painting (flat colour, shadow, gradient, detail, one light direction) [S]; one trim atlas per material family [S/I].

From the palace study (art/Qin-Palace-Painted-Study.md):
- Texel density 256 px/m desktop, 128 phone; brush runs 4-15 cm on screen, no flat fills over 20 cm; luminance sd 8-30 per material region; saturation cap 0.55, accents to 0.6; one light (the game's sun and hemisphere).
- Value plan: bronze mean luminance 70 to 110 (0-255); characters must stay readable at 3:1 against what is behind them.
- Props: klad materials from the ramps at 256 px/m, never a source model's photo textures; triangle budget 7k / 2.5k / 800 (LOD0/1/2); lion footprint 1.6 x 2.2 m, 2.4 to 2.6 m tall.

Where the two studies and later owner decisions differ, the later owner decision wins:
- "Props carved hard-edged, bevelled planes" (palace study) is replaced for living forms by the owner's 22:30 rule: round where the form is round, sharp where it is sharp. Planes and cut grooves stay for plinths, flanges, plates and ornament.
- "Scanned or downloaded models: geometry only, decimated, re-materialled" (palace study) is replaced by the owner's 22:00 rule: every found model is reference only, never shipped or decimated.
- Triangle budget: this study takes the palace study's 7k / 2.5k / 800 (the asset list's 3k / 1k / 300 was the lead's guess); rounded forms need the extra triangles. The heaviest room stays under 500 calls and 0.5M triangles.

## What the GDD asks of these pieces
- Hazards that hit every side, each with a tell of at least 0.4 s carried by the look (BURNING-PALACE "Palace pieces"): the guardian beast's 0.6 s windup (CONFIG.LION.windup) must read as a shape change, not only the red ring.
- Kaymuse's palace, Qin first: bronze, lacquer, rammed earth; the beasts guard her halls' doors in pairs.
- The apex is a bronze tiger under the throne (the tiger tally made beast): the guardian beasts must not read as that tiger (different head, mane and pose), so the apex keeps its own silhouette.
- Budget: heaviest room under 500 calls and 0.5M triangles; single props 7k / 2.5k / 800 triangles over three LODs (palace study).

## Measured or computed values (from the game's CONFIG and round 1)
| Value | Number | How |
|---|---|---|
| Pixels per metre at the fight framing | 110 px/m | CAM_FOV 50, distance 0.75 x CAM_DIST 14 = 10.5 m, 1080 px tall: 1080 / (2 x 10.5 x tan 25 deg) |
| Pixels per metre at the wide framing | 52 px/m | 22 m distance (review viewer wide view) |
| Smallest feature that reads (6 px) | 5.5 cm fight / 11.5 cm wide | 6 px / px per m |
| Round 1 inlay line width | 1.6 cm (4 px at 256 px/m) | bronze_tex.py: 4 px marker |
| Round 1 inlay on screen | 1.8 px fight framing | 1.6 cm x 110 px/m: does not read |
| Box lion it replaces | 2.6 m tall, 1.6 x 2.2 m | index.html palace lion boxes |
| Collision footprint (gameplay, unchanged) | 1.8 x 2.2 m | palSolid in the lion build |
| Round 1 beast height | 2.37 m | beast_blender.py print |

## Values (rules for every cast-bronze piece)
- Shape language (owner 22:30): round = bodies, haunches, chests, skulls, snouts, paws, mane curls, tail; sharp = claws, fangs, ear tips, brow ridge, flanges, inlay bands, mould seams, plinth edges. Round parts use smooth normals on curved cages (spheroids and tapered tubes, 10-12 sides); sharp parts use flat faces and split normals at edges over 50 deg. No part may be a plain box except the plinth.
- Segmented casting: visible flanges at joints (elbow, collar, tail segments), a workshop mark on large plates, ornament in bands from the trim sheet.
- Palette: bronze ramp deep #3a2b1a, shadow #6a5233, base #9a7a48, light #b2925e, highlight #c7aa72; inlay silver #c8ccd0 (dark #8e9396); dormant patina #4f7a62 / #3f5a4c / #6f927c. Fresh bronze on live hazards, patina only on dormant or sunk pieces. Saturation cap 0.6.
- Texture: klad-painted trim sheet, 1024 px = 4 m (256 px/m), rows as in art/tools/bronze_tex.py; brush runs 4-15 cm, luminance sd 8-30 (tex_check.py).
- Readability at play size: any detail meant to be seen is at least 6 cm wide (6.6 px at the fight framing): inlay bands 6 cm (16 px on the sheet), ornament strokes at least 12 px on the sheet, eyes at least 12 cm across.
- Size: a guardian beast is at least as tall as the box lion (2.6 m with its plinth) inside the 1.8 x 2.2 m collision footprint (upright seated pose rather than longer).
- Tell: the windup moves the striking paw at least 0.4 m (44 px at the fight framing) and opens the jaw at least 25 deg by 0.6 s.
- Facing cues: head, chest, front paws and claws forward; mane curls, haunches and the tail behind; no plate or spike points backward.
- Light and material: MeshStandardMaterial, bronze metalness 0.4 roughness 0.6, inlay metalness 0.6 roughness 0.35, stone plinth matte; the game's two lights only.
- LOD: LOD0 up to 7k (full), LOD1 up to 2.5k (no small parts, no bevels), LOD2 up to 800 (decimated); rigid rig, each segment 100% on one bone.
- Value: bronze mean luminance 70 to 110 on the plain plate region of the sheet (palace study value plan).

## Sizes
3D props have no sprite ladder. Texture sizes: 1024 desktop (measured, this study), 512 phone (proposed).

## Samples, round 1 (24 Nov 2026 22:2x, not approved)
- Files: art/beast/round1/ (shots and the round 1 script and GLB), assets/tex/bronze_trim.png, art/src/bronze_trim.klad.
- Owner 22:30: blocky; round what should be round, sharp what should be sharp. Lead's notes: robot-dog read; haunches plain blocks; torso a ramp from the side; smaller than the box lion; windup pose not confirmed; LOD view bug (the skinned LOD0 cannot be moved by its mesh position).

## Samples, round 2 (24 Nov 2026 22:5x, not approved)
### Figure (original)
| Figure | Parts | What it shows |
|---|---|---|
| Bronze guardian beast, seated upright on a two-tier stone plinth | 60 parts in LOD0, 15 bones | round masses (spheroids, tapered tubes) for body, haunches, head, paws, 16 mane curls and tail; sharp claws, fangs, ears, brow, flanges, breast plate, collar, plinth; silver inlay eyes, claws, fangs, collar ring, leg bands, breast ridge |
### Files
- assets/models/beast.glb (LOD0 skinned with clips idle and strike, LOD1, LOD2); art/tools/beast_blender.py (run with the bpy venv: python beast_blender.py OUT.glb).
- assets/tex/bronze_trim.png round 2 (art/src/bronze_trim.klad, art/tools/bronze_tex.py; passes art/beast/round2/bronze_trim_passes.png).
- Shots (software GL, review viewer art/viewer/beast.html, game FOV/pitch/lights/floor): art/beast/round2/play.png, wide.png, strike_windup.png, turn_*.png, pass_*.png, lods.png; comparison art/beast/round2/beast_round1_vs_round2.png. Round 1 kept in art/beast/round1/.
### Checks run (code tool only)
- beast_blender.py 8 of 8: tris 5440 / 1426 / 424 (budget 7000 / 2500 / 800); every vertex on a bone; windup paw rise 0.64 m (min 0.4); height 2.70 m (min 2.6); footprint 1.80 x 2.20 m (max 1.8 x 2.2); smooth-shaded share 72% (min 50%).
- tex_check.py 25 of 25 (bronze_trim: density 256 px/m, brush 10.1 cm, lum sd 9.6, saturation 0.54, value mean lum 104 in 70-110; the five approved palace textures unchanged).
- Inlay band 16 px on the sheet = 6 cm, about 7 px at the fight framing (study minimum 6 px); stamp strokes 10-12 px.
### Open
- Look (lead's read of the shots, code tool only): rounded and lion-like now; the face reads friendly (big round eyes and cheeks) rather than fierce; the bronze reads dark brown and the stamp bands are hard to see at play size; mane curls read as discs from the back.
- Not done: phone texture (512), KTX2, game integration (THREE.LOD, pooled, warmed), real-GPU and phone screenshots, the jaw opening measured only in Blender (paw rise is gated; jaw angle 30 deg is keyed, not gated).
- Supersedes round 1 (art/beast/round1/).

## Open
- ComfyUI: huggingface.co and pip are reachable from the session shell, but there is no GPU (2 CPU cores, 7 GB); SD 1.5 class models on CPU would take minutes per image. Not used unless round 2's shape still misses; then a CPU job on a GitHub runner, reference images only, never shipped.
- Phone texture set (512) and KTX2 with texture step 3.
