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
### Verdict against the study's criteria (owner 22:43: "the figure is still bad"): does NOT meet them
| Criterion | Round 2 | Result |
|---|---|---|
| A guardian (fierce, imperial) that reads at play size | friendly face: big round eyes, round cheeks, small snout; reads as a toy lion or teddy | FAIL |
| Segmented casting: seams, flanges, stamp bands, inlay visible | flanges at elbows and collar only; body masses are plain spheroids; stamp bands not readable at play size | FAIL |
| Round where round, sharp where sharp (owner 22:30) | rounded, but forms are generic spheres and tubes, not anatomy (no shoulder mass, no wrist, no muscle planes) | FAIL (shape quality) |
| Fresh brass-gold bronze on a live hazard | reads dark brown under the game lights | FAIL (value 104 passes the number, the look misses) |
| Not the apex tiger's silhouette | lion mane and seated pose | PASS |
| Size, footprint, tell, budget, rig | gates 8 of 8 | PASS |
Cause: the build method (spheres and tubes placed by hand, no reference drawn first) gives volume but no design.
### Concept references from ComfyUI (reference only, never shipped or traced)
- Round A (run 45417469651, SD 1.5, 28 steps, 512 x 768): 12 images, 486-804 s each on a 4-core runner. None usable: silver horses, griffins, trophy shapes, one texture. Cause: the prompt was far over CLIP's 77-token limit, and "silver inlay" pulled the material to silver.
- Round B (run 45424065546, SD 1.5 + LCM LoRA, 6 steps): 32 images, 117-132 s each. Seated guardian lions in most; fierce faces and curl manes in several. Lead's shortlist for shape (not material): 2109, 2118, 2123, 2116, 2131, 2111, 2107 (art/beast/concepts/). Still off: most read as carved stone or clay, not cast bronze; no segment seams or inlay; several read South or Southeast Asian rather than Qin. Material and ornament come from this study and the klad trim sheet, not from the concepts. Next: concept references from ComfyUI with the study's values as the prompt (run 45417469651 on branch ci-comfy, reference only), the owner picks one, its proportions are measured, then the model is rebuilt to it.

## Samples, round 3 (25 Nov 2026 00:0x, not approved)
- Shape from concept 2130 (owner pick 24 Nov 23:51; measured on the front view: figure height H 535 px, head 0.37 H, forehead width 0.48 H, mane collar 0.56 H, body 0.63 H, paws 0.61 H). Built from lofted rounded-square sections (superellipses): compact seated mass, big broad domed head, cheeks and nose bridge, almond silver eyes, a collar of mane tufts, forelegs of four stacked rings with silver inlay bands (the segmented-casting cue), paws with four toes and sharp claws, haunch rolls, tail with a sharp flame tuft.
- Gates (beast_blender.py) 8 of 8: tris 6932 / 2426 / 726 (budget 7000 / 2500 / 800); every vertex on a bone; windup paw rise above 0.4 m; height 2.70 m; footprint 1.80 x 2.20 m; smooth-shaded share above 50%.
- Files: art/beast/round3/ (round3_sheet.png with the concept beside the model, play, wide, strike_windup, turn_*, pass_*, lods); rounds 1-2 kept.
- Against the criteria (lead's read, code tool only): mass, proportions, ringed segmented legs and the brass bronze now follow the concept and the study (better); the face still reads as a simple mask (no carved lids, lips or whisker pads like the concept), the chin ruff barely shows from the front, and the back is a plain dome: the guardian-face criterion is still not met.

## Samples, round 4 (25 Nov 2026, overnight worker W1a; owner asleep, not approved)
Owner on round 3b: the brow reads as a helmet visor, the face is a mask, body and back are plain; "if you know it will fail, do it again".
### Concept (ComfyUI round C, run 45432241899, SD 1.5 + LCM, 6 steps; reference only, nothing traced)
- 24 face concepts were back when picked (job 0's 8 were still running). Picked by the round 4 criteria: **3129** (brass-gold, lion, flame-tongue mane framing the face, V brows from the nose bridge, deep slit eyes, big open mouth, beard tuft); alternates for the owner **3120** (cast curl-disc mane, lion face) and **3111** (dark, heavy brows, mane locks). Files art/beast/concepts/roundC/ (the three picks and round_C_all.jpg).
- Measured on 3129 (numpy, figure height H = 449 px incl. mane): mane width 0.79 H at 0.45-0.55 H; eyes 0.23 H below the top at +-0.15 H; nose 0.28-0.42 H; mouth open 0.46-0.69 H, about 0.45 H wide; beard tuft to 1.0 H. Built with H = 1.05 m (head with mane).
### What changed (art/tools/beast_blender.py, round 4)
- Face: two slanted brow ridges meeting over the nose bridge in a V (no bar), a forehead knot, snarl wrinkles, deep-set silver almond eyes with dark irises under angry upper lids, a bulb nose with flared nostrils 0.25 m in front of the eyes, whisker pads, cheeks sweeping into the mane, open dark mouth with silver fangs and incisors, jaw on its own bone, a flame beard.
- Mane: a rounded hood mass sloping down the back to the shoulders, a double ring of sharp flame tongues framing the face (swept back over the crown), four rows of tongues falling down the back.
- Body: two cast segment flanges with 6 cm silver inlay bands around the torso; haunch masses with roundels (silver rim, cloud-band face, boss); forelegs with shoulder masses, elbow and wrist flanges and two 6 cm inlay bands; a pendant bell on a strap; a tail laid up the spine with flange cuffs and a flame fan.
- Strike windup: the right foreleg swings up and out (local Euler (-30, 0, 110) at the shoulder, chosen from a printed pose grid, POSE_SEARCH=1); the round 4 draft's forward raise (0.54 m) was foreshortened at the 40 deg play pitch.
- Colour: measured cause of "dark brown": under the game lights the bronze shows on screen (play view, beast pixels from the silhouette pass) as #533e29, hue 29, mean lum 65 from a sheet of mean lum 104; metalness 0.1 / 0.2 / 0.4 / 0.6 gives 70 / 70 / 66 / 59 (material is not the cause; light and sheet value are). New sheet variant **assets/tex/bronze_trim_brass.png** (bronze_tex.py `brass`, klad, art/src/bronze_trim_brass.klad, passes art/beast/round4/bronze_trim_brass_passes.png): plain plate mean lum 137, hue 41 (research fresh bronze #C9A050). On screen: #644c30, hue 32, mean lum 79, p90 110. The default sheet is unchanged; the beast shots use `&sheet=brass`; play_default_sheet.png shows the same model on the current sheet.
### Checks run
- beast_blender.py 9 of 9: tris 6988 / 2422 / 708 (budget 7000 / 2500 / 800); every vertex on a bone; windup paw rise 1.49 m, 0.77 m out to the side (min 0.4); jaw open 32 deg, chin down (new gate, min 25); height 2.92 m (min 2.6); footprint 1.80 x 2.20 m; smooth-shaded share 80%. 160 parts, 13 bones.
- tex_check.py 31 of 31 (adds bronze_trim_brass: density 256 px/m, brush 8.5 cm, lum sd 10.7, saturation 0.56, value mean lum 137 in 120-160, hue 41 in 36-46). New value and hue rules mutation-tested: the default sheet copied in as the brass file fails both (lum 104, hue 36).
- Viewer: art/viewer/beast.html now takes ?model= (beast default, ding, vat), &state=, &school=, &sheet=, &metal=/&rough=; the round 3b beast shots re-shot through it are pixel-identical (play, turn, strike, silhouette: 0 px differ; lods mean diff 0.05, LOD2 decimation).
### Files
art/beast/round4/: round4_sheet.png (concept, 3b, round 4 turns, play size, windup, old sheet), face.png, play.png, wide.png, strike_windup.png, turn_*.png, pass_*.png, lods.png, play_default_sheet.png, beast_blender_round4.py, beast_round4.glb; assets/models/beast.glb (round 4); round 3b script and GLB kept in art/beast/round3b/.
### Verdict against the round 4 criteria (lead's read of the shots, software GL, not a real GPU)
| Criterion | Round 4 | Result |
|---|---|---|
| Fierce imperial guardian that reads at play size | open fanged mouth, V brows, flame mane, bell collar read at play size (play.png); at play size the crown tongues still read a little like a sunburst | PASS (owner to judge the crown) |
| Not a cat, not a teddy, not a robot dog, not a helmet visor | no bar brow, no ears or whiskers, mane and fangs; whisker pads and cheeks are round and could read soft close up | PASS |
| Lion-like, clearly not the apex bronze tiger | mane hood, seated upright, bell collar, flame tail fan | PASS |
| Segmented-casting cues visible at play size | torso flanges with 6 cm silver bands, banded forelegs, silver-rimmed haunch roundels visible in play.png | PASS |
| Brass-gold, not dark brown | brass sheet: hue 32 lum 79 on screen (was hue 29 lum 65); reads gold-ochre, not brown, in play.png; needs the owner's pick of the sheet variant (all bronze props share it) | PASS with the brass sheet only |
| Round where round, sharp where sharp | lofted masses smooth (80%), tongues, brows, fangs, claws, flanges sharp | PASS |
| Body and back no longer plain | side: roundel, bands, tail; back: tongue rows on the mane, bands, tail fan; the back of the mane reads busy (pine-cone like) in turn_back.png | PASS (weakest view: back) |
| Strike tell (paw rise >= 0.4 m, jaw open) | 1.49 m up and 0.77 m out, jaw 32 deg; reads clearly in strike_windup.png | PASS |
| Footprint 1.8 x 2.2 m, height >= 2.6 m | 1.80 x 2.20, 2.92 m | PASS |
### Open (round 4)
- Owner: pick the bronze sheet (current or brass); the beast's look depends on it. Concept alternates 3120 and 3111 kept.
- LOD2 (decimated) loses the mane tongues; fine at distance, not checked in the game.
- Not done tonight: game integration (THREE.LOD, pooled, warmed), phone texture (512), KTX2, real-GPU and phone shots.

## 鼎 cauldron (C2), round 1 (25 Nov 2026, overnight worker W1a; not approved)
GDD: nine 鼎 replace the healing altars in the palace, one per school hall (the 九鼎 Qin lost); heal by CONFIG.ALTAR; decree "Our altars are dry" makes them look empty (BURNING-PALACE "Palace pieces", asset list G4).
### Concept (ComfyUI round D, run 45434186975, jobs 0-1, 16 images; reference only)
- SD 1.5 does not know a ding well: most images are lidded pots, urns or bowls on stands. Picked **4101** (round belly on three legs, lid, proportions closest to a Warring States ding); alternates **4115** (ornament bands, loop handles, legs) and **4106** (ornament band, legs). Files art/ding/concepts/ (picks, round_D_all.jpg).
- Measured on 4101 (numpy row widths, H = 412 px incl. lid; the right-hand shadow inflates widths): belly widest about 0.9 H at 0.40 H, belly bottom about 0.72 H, legs the lowest 0.28 H, lid the top 0.15 H. Without the lid: legs about 0.33 of the height. Built: rim 1.27 m, belly 1.5 m wide at 0.8 m, legs 0.4 m (0.31 of the rim height).
### Build (art/tools/ding_blender.py, our own design)
- Lathe-turned belly and hollow bowl (round), sharp rim lip; bands from the brass trim sheet rows by height: cloud band low, deconstructed taotie mask band at the shoulder divided by six vertical flanges (扉棱), flange row on the rim; two upright handles (附耳) outside the rim with an accent inlay on the bar; three hoof legs with mask knees.
- School accent: a 6 cm inlay band (material palAccent, one shared mesh; one material per hall) with dark keylines; colours in the GLB extras `accents` / `accentMetal` in CONFIG.SCHOOLS order. The research palette was matched to the game's school colours (CONFIG.COL.schools) by least total Lab distance: ru ochre, dao gold, fa lead white, mo cinnabar, yinyang bone black, za silver, ming Han purple, zongheng malachite, nong azurite (W1a's assignment; owner to confirm). Silver is the one metal finish; gold is laid matte (as metal it measured dE 7.3 from the brass).
- States: `ding_lit` = coal bed 0.27 m under the rim, 16 coals (every third glowing, palEmber), an additive glow disc and two crossed glow cards (no real light, no neon); `ding_dry` = grey ash crust 0.49 m under the rim with jagged dark cracks (empty, deeper bowl).
### Checks run
- ding_blender.py 11 of 11: tris 1972 / 556 / 188 (budget 2000 / 600 / 250; asset list 2k / 600); state objects lit 666, dry 336 tris; footprint 1.63 x 1.61 m (solid 1.8 x 1.8); rim 1.27 m (box ding 1.36), handles to 1.63 m; lit bed seen over the rim from the 40 deg play pitch: 75% of its width (min 50%); dry crust 0.22 m below the lit bed, 54% seen; accent material on LOD0 and LOD1; nine distinct accents in the extras; lit glows, dry has no glow; smooth share 66%.
- art/tools/accent_check.py on the nine school shots 10 of 10: closest pair ru / dao dE 12.4 (min 10); each accent vs the bronze above it dE 13.5 (ru) to 48.6 (nong) (min 12). The check failed the first draft (lead white / silver dE 6.9, all nine one finish) and the second (gold metal vs bronze dE 7.3), so it catches what it is for.
### Files
art/ding/round1/: ding_round1_sheet.png, ding_schools_sheet.png, play_lit.png, play_dry.png, play_lit_default_sheet.png, wide.png, turn_*.png, top_lit.png, top_dry.png, pass_*.png, lods.png, school_0-8.png, gates.txt, accent_check.txt; assets/models/ding.glb.
### Verdict (lead's read of the shots, software GL)
| Criterion | Round 1 | Result |
|---|---|---|
| Real Warring States proportions (reference only) | lidless ding: wide round belly, three hoof legs, two upright attached handles; leg share 0.31 vs concept 0.33 | PASS |
| Deconstructed taotie ornament via the trim sheet | mask band between six flanges; at play size it reads as a band of eye marks, the flanges as small pegs | PASS (weak at play size) |
| Readable as a healing station at play size | lit bowl glows warm in play_lit.png; the game's green altar ring stays the gameplay cue | PASS |
| Lit state (glow card or ember, no neon) and dry state (empty) | glow cards + coals; dry grey crust deep in the bowl, no glow; clear difference at play size. The crossed cards make a bright vertical spike where they meet (reads like a flame) | PASS |
| Nine school accents on one shared mesh | one mesh, palAccent per hall; accent_check 10 of 10 | PASS |
### Open
- Owner: confirm the school-to-pigment assignment; pick the bronze sheet (shots use the brass variant; play_lit_default_sheet.png shows the current sheet).
- Integration (not tonight): nine materials (one per hall, each hall is its own room, so no extra calls per room), glow cards pooled and warmed, the state swap on the dry decree, the green ring kept.

## 门海 water vat (C3), round 1 (25 Nov 2026, overnight worker W1a; not approved)
GDD: break one to flood a spot: it cracks (CONFIG.PIECES2.vat.crackS 0.5 s tell with the red ring), then splashes (radius 3.5 m): douses the burning there and knocks back anyone in it (BURNING-PALACE "Palace pieces"). Box vat in index.html: radius 0.8, height 1.4, solid 1.6 x 1.6 m.
### Concept (ComfyUI round D, run 45434186975, jobs 2-3, 16 images; reference only)
- Picked **4207** (wide deep basin, raised horizontal bands, small ring knobs: Qin-first 鉴 basin rather than the Ming/Qing 门海 tub); alternates **4203** (banded rim, foot) and **4212** (ringed bands, stamp). Files art/vat/concepts/.
- Measured on 4207 (numpy row widths, H = 343 px; the bowl touches the frame, so the rim width is a lower bound): rim at least 1.5 H, tapering to about 0.75 H near the bottom, a low foot. The first build kept that straight taper and read as a flowerpot; round 1 final has a bulging belly (0.78 m radius at 0.76 m), a drawn-in neck and a flared lip (rim radius 0.8 m), height 1.10 m.
### Build (art/tools/vat_blender.py, our own design)
- Lathe-turned tub (round), sharp flared lip and two raised flange rings (segmented casting); stamp bands by height from the brass trim sheet (hooked lozenge low, cloud scroll high, flange row on the lip); four 铺首 mask-and-ring handles at 45 deg off the camera axis.
- vat_water: the surface 0.12 m under the rim (the game's water colour in the viewer). vat_cracks (the tell overlay on the intact body): five jagged dark cracks 6 cm wide from the lip down over the camera side (20-160 deg) and light water sprays fanning out. vat_shards_00-09 plus vat_shards_base: wall pieces (each its own node, pooled in the game) laid out as they land 1.0-2.5 m out, and vat_puddle.
### Checks run
- vat_blender.py 10 of 10: body tris 1488 / 408 / 162 (budget 1500 / 500 / 200; asset list 1.5k / 500); shards 11 pieces 680 tris together (budget 1500); crack overlay 276 tris (budget 600); footprint 1.60 x 1.60 m, height 1.10 m (solid 1.6 x 1.6); crack tell 5 cracks 6 cm wide (6.6 px at the fight framing); 11 shard nodes all within 2.47 m (splash 3.5) and on the floor; water 0.98 m under the rim 1.10 m, water and puddle facing up (the first draft's discs faced down and were culled: the gate now checks it); smooth share 100%.
### Files
art/vat/round1/: vat_round1_sheet.png, play_intact.png, play_cracked.png, play_shards.png, play_intact_default_sheet.png, wide.png, turn_*.png (incl. turn_cracked, turn_shards), top_intact.png, pass_*.png, lods.png, gates.txt; assets/models/vat.glb.
### Verdict (lead's read of the shots, software GL)
| Criterion | Round 1 | Result |
|---|---|---|
| Cast bronze with stamp bands | lozenge and cloud bands, flange rings, mask-and-ring handles read at play size | PASS |
| Breakable: intact, cracked, pooled shards | three states; shards are separate nodes for pooling; the cracked state reads at play size (dark cracks, white sprays); the sprays read as stiff cones close up | PASS (sprays weak) |
| Water surface | visible from the play pitch (play_intact.png) | PASS |
| Footprint fits the vat config | 1.60 x 1.60 m inside the 1.6 x 1.6 solid; 1.10 m tall against the box's 1.4 (the box was a placeholder; owner may want it taller) | PASS |
### Open
- Owner: height (1.10 m now), sheet pick. Integration (not tonight): shards thrown on the splash from a pool, body hidden, cracks shown for crackS, all warmed under the loading card.

## W1b props: shared method (25 Nov 2026, overnight worker W1b; owner asleep, nothing approved, nothing in the game)
- Same route as W1a: ComfyUI concept round (reference only) -> measure -> own Blender script -> klad textures -> gates PASS/FAIL -> viewer shots -> honest verdict. Helpers from beast_blender.py, ding_blender.py and vat_blender.py are gathered in **art/tools/prop_kit.py** (lathe, spheroid, torus, prism, loft, trim-sheet UVs, finish, LODs, gates) plus sweep() (round tube along a curved path with a radius per point and an optional side axis) and card() (0-1 UV quads).
- ComfyUI round E (run 45441170013, SD 1.5 + LCM, 6 steps, 32 images; branch ci-comfy-w1b): job 0 crane, job 1 censer, job 2 water clock, job 3 huabiao. Picks and two alternates per asset in art/<asset>/concepts/ with the full contact sheet. Measuring: numpy segmentation failed on the gradient backgrounds, so proportions were read by eye off the contact sheets (labelled so below).
- Cards (new textures, klad): **assets/tex/smoke_card.png** and **flame_card.png**, 256 px RGBA, painted on a 1024 canvas by art/tools/w1b_tex.py (sources art/src/smoke_card.klad, flame_card.klad). Checked by **art/tools/card_check.py** (own rules, not tex_check: soft edge, coverage 15-60%, smoke warm grey luminance 120-200 and saturation <= 0.12, flame core luminance >= 200, body hue 20-50, rim saturation <= 0.75 so not neon): **14 of 14 PASS**. Mutation-tested: the flame copied in as smoke fails 2 rules; a hard-edged square card fails soft edge and coverage. Draft 1 failed 4 rules (smoke too small; flame read as a cone, rim too saturated); the first smoke draft's two mirrored curls read as a pair of eyes (now one curl, off centre).
- Viewer: art/viewer/beast.html takes the W1b models (crane, censer, huabiao, clock, lamp, bells, tally, merc) with materials palSmoke, palFlame, palCinnabar, palLacquer (approved pillar texture A3), palEye (asleep dark / &eye=awake gold), palGold, palMerc (matcap); cards show only in the textured view. shoot_viewer.mjs takes a 5th argument ONLY (shot names). The beast, ding and vat specs are unchanged.
- Sheet: every play shot uses &sheet=brass (as W1a's); play_default_sheet.png shows the current sheet. Same owner choice as W1a's.

## 铜鹤 crane (C4), round 1 (W1b; not approved)
GDD: smoke source; the cloud blocks sight, anyone can hide in it, few small smoke cards (BURNING-PALACE "Palace pieces"; CONFIG.PIECES.smoke r 3 m, opacity 0.55). Box crane: base 0.8 m, body at 2.3 m, neck to 3.5 m; solid 1.2 x 1.2 m.
- Concept: pick **5103** (slender standing crane, long legs, upright neck, long sweeping wing point); alternates **5102** (wings raised, round plinth), **5106** (round body on long legs). Read by eye on 5103: legs about 0.4 of the height, body 0.25, neck and head 0.35. Built: plinth 0.10, legs 0.37, body 0.19, neck and head 0.34 of 2.91 m. Qin reference: the bronze waterfowl of the First Emperor's tomb (pit K0007), reference only.
- Build (art/tools/crane_blender.py): standing crane in profile (faces +x so neck and beak read from the play camera), egg body, S-neck sweep, sharp open beak (smoke comes out of it), thin legs with hock joints and sharp toes, upright wing plates sweeping to a long point (round 1b; the draft's lozenge-stamped short wings read as scales or a pineapple, the first draft's were flat shelves), silver inlay collar, wing edges and eyes, a cinnabar crown (decoration), turned plinth with cloud band. Node crane_smoke (3 cards, 0.9 / 1.3 / 1.8 m, tilted 40 deg to the play camera) and empty crane_smoke_src at the beak tip (where the game's cloud starts).
- Gates (crane_blender.py) **10 of 10**: tris 1362 / 417 / 161 (budget 1500 / 500 / 200); footprint below 1.25 m 1.12 x 1.10 (solid 1.2), overhang above it 0.40 m (max 0.45); height 2.91 m; 3 smoke cards from 2.68 m (above a suit's head); smooth 67%; sharp faces 260; inlay and cinnabar on LOD0, inlay on LOD1.
- Files: art/crane/round1/ (crane_round1_sheet.png, play, play_default_sheet, wide, turn_*, pass_*, lods, gates.txt), assets/models/crane.glb.
| Criterion | Round 1 | Result |
|---|---|---|
| Reads as a cast-bronze crane at play size | neck, beak, legs and plinth read in play.png; Qin waterfowl proportions | PASS |
| Smoke source, few small cards | 3 cards rising from the beak; reads as a soft column of puffs, still three separate puffs at play size | PASS (puffs separate) |
| Round where round, sharp where sharp | body, neck, legs smooth; beak, toes, feather points, plinth lip sharp | PASS |
| Segmented casting cues | inlay collar, wing-edge inlay, cloud band on the plinth; body plates plain; the neck sweep shows small kinks from the side | PASS (weak: plain body) |
| Fits the solid, above-head smoke | gates | PASS |
- Open: the hide cloud itself (r 3 m) is still the game's icosahedra; a cloud made of 4-5 large smoke cards would match the plume (integration decision). Not done: game integration, phone texture, real-GPU shots.

## 香炉 censer (C4), round 1 (W1b; not approved)
- Concept: pick **5208** (豆-form bowl on stem and foot); alternates **5205** (lidded pot with finial on a stepped stand), **5202** (lidded bowl on a stand). Qin first: Warring States 豆-form incense burner; the Han 博山炉 mountain lid is later, so our lid is our own: two tiers of flame-cloud tongues over a dark dome (reads as pierced openwork), a bird-knob finial.
- Build (art/tools/censer_blender.py): turned foot (lozenge band), stem with knot, bowl (cloud band), flange lid ring with silver inlay, two 铺首 mask-and-ring handles at 45 deg; censer_smoke (4 cards) and censer_smoke_src. Drafts: spiky flat tongues with round black holes read as a sea mine; the tongues' section was squashed the wrong way (fixed: sweep side axis).
- Gates (censer_blender.py) **9 of 9**: tris 1234 / 472 / 164; footprint 1.16 x 1.16 (solid 1.2); height 1.76 m (box 1.5); 4 smoke cards; smooth 94%; tongue tips 0.27 m clear of the dome, sharp faces 40 (this gate replaced the draft's "sharp faces >= 80" when the tongues changed on purpose from spikes to rounded cloud tongues: stated here, not hidden); openwork dark dome on LOD0 and LOD1, inlay ring on LOD0.
- Files: art/censer/round1/ (censer_round1_sheet.png and shots, gates.txt), assets/models/censer.glb.
| Criterion | Round 1 | Result |
|---|---|---|
| Reads as a bronze incense burner at play size | foot, stem, bowl, openwork lid read in play.png | PASS |
| Smoke source, few small cards | 4 cards from the lid top | PASS |
| Qin-first look, not Ming/Qing | 豆 form, cloud band, mask-and-ring handles; the lid reads a little like a lotus crown | PASS (lid: owner to judge) |
| Round where round, sharp where sharp | turned body smooth; tongue tips, finial beak and tail sharp | PASS |

## 华表 pillar with a watching beast (C6), round 1 (W1b; not approved)
GDD: the beast on top watches its room; passing it marks you (CONFIG.PIECES.huabiao: range 3 m, radius 3.5 m, windup 0.5 s with the red ring and its eyes, markS 5 s). Box: base 1.4 x 0.4 x 1.4 m, column r 0.45 to 5.4 m, crossbar 4.4 m, beast box at 5.7 m, eyes 5.85 m; solid 1.4 x 1.4 m.
- Concept: pick **5403** (a beast on a black column); alternates **5405** (bronze ring bands on a black column), **5408** (relief panels). SD 1.5 gave mostly plain columns. Read by eye: on 5405 the ring bands are about 1.7 x the column width (built 1.35 x: sleeves r 0.405 on r 0.3); on 5403 the beast is about 2 x the column width long (built 0.65 m body on 0.6 m column, plus mane).
- Build (art/tools/huabiao_blender.py): turned octagonal stone plinth; black-lacquer timber column with the approved pillar texture (A3, u once around); three cast bronze 釭 sleeves (flange lips, cloud band, 6 cm silver inlay ring); a bronze cloud board through the column with curled ends; a dew disc; a seated bronze beast facing the room (haunches, straight forelegs, sharp claws, mane tongues down the back). The head is its own node (huabiao_head, child of huabiao_lod0; huabiao_head_lod1 on LOD1; LOD2 merged), pivot at the neck; clip **watch** dips it 22 deg and turns it 35 deg in the 0.5 s windup. Eyes are inlay material **palEye**: dark bronze asleep, gold inlay with a low warm emissive awake (viewer &eye=awake) - not neon. Round 1b head: broad skull, short snout, V brows, a collar of flame tongues, short swept horns (the draft's long snout and tall horns read as a jackal).
- Gates (huabiao_blender.py) **10 of 10**: tris LOD0 + head 1284, LOD1 + head 496, LOD2 168 (budget 1500 / 500 / 200); footprint below 2.2 m 1.36 x 1.36 (solid 1.4), cloud board overhang 0.35 m above heads (max 0.5); height 6.2 m; palEye on LOD0 and LOD1 heads, eyes 13 cm across (min 12); head nodes parented, clip watch 30 frames to the windup at 60 fps; watch moves the eyes 14 cm sideways and 9 cm down; lacquer, bronze, inlay and stone materials; smooth 80%.
- Files: art/huabiao/round1/ (huabiao_round1_sheet.png, play, play_awake (t 0.5, eyes awake), play_default_sheet, head_asleep, head_awake, wide, turn_*, pass_*, lods, gates.txt), assets/models/huabiao.glb, art/huabiao/concepts/.
| Criterion | Round 1 | Result |
|---|---|---|
| A watching beast that reads at play size | seated maned beast facing the room on top of the column; the head turn reads in play_awake.png | PASS |
| Eye cue is inlay, not neon | gold inlay awake vs dark asleep; at the fight framing the eyes are about 14 px across, visible but small - the head turn carries most of the tell | PASS (small) |
| Bronze-banded timber pillar, cloud-scroll trim | lacquer column, three bronze sleeves with inlay, cloud board with curled ends | PASS |
| Not the guardian beast or the apex tiger | small, seated on a disc, horns and a tongue collar; the mane collar reads a little like a sunburst (same note as the guardian beast's crown) | PASS (owner to judge) |
| Fits the solid and the box height | gates | PASS |
- Open: the game's eye colour (CONFIG.PIECES.col.eyeOn 0xff5020 at emissive 2) is the neon the asset list rules out; the asset expects a gold inlay with a low warm glow (integration decision, not changed tonight). The red ring stays the gameplay tell.

## 铜壶滴漏 water clock (C5), round 1 (W1b; not approved)
GDD: one per wing; its water level counts down to her next burning in that wing (the scene timer beside the HUD; CONFIG.PIECES2.clock.steps 48, written only when the step changes). Box: plinth 1.4 x 0.3 x 1.4 m, posts and a beam to 2.4 m, a 0.9 x 2 m water column scaled to the time left; solid 1.4 x 1.4 m.
- Concept: pick **5305** (a tall bronze cylinder with ring flanges on a footed tray); alternates **5301** (stacked round pots), **5308** (vessels with indicator rods). Read by eye on 5305: cylinder about 0.8 of the height and 0.25 of it wide, three flanges. Built: pot 1.6 m of 2.22 m to the rim, 0.72 m wide, three flanges.
- Qin first: the Qin / Western Han outflow clepsydra (泄水型沉箭漏): a tall pot drains through a bottom spout and a float carries an indicator rod (箭) that sinks as the water falls - a countdown by nature. **Invention (labelled)**: a cast sight slot down the front (64 deg, 0.38 m wide, flanged edges) shows the water column, so the level reads at play size the way the box column did.
- Build (art/tools/clock_blender.py): octagonal low tier, round upper tier under the pot, three hoof legs, slotted pot (dark inside), three ring flanges cut at the slot (the draft's full rings crossed the window like cage bars), lid ring with silver inlay, crossbar and rod guide, dragon-head spout, catch basin on the low tier (the draft's basin sat inside the stand). Moving nodes (children of clock_lod0): **clock_water** (origin on the pot floor; scale Z = level), **clock_arrow** (float and rod with 6 cm gold graduation rings; position Z rides the water top), **clock_catch** (basin water; scale Z = 1 - level), clock_drip (stream card). Clips countdown_water / _arrow / _catch (1 s: t 0 full, t 1 empty); extras on each node give the mapping. The viewer takes &level=.
- Gates (clock_blender.py) **11 of 11**: tris LOD0 + moving nodes 1430, LOD1 468, LOD2 164 (budget 1500 / 500 / 200); footprint 1.36 x 1.36 (solid 1.4); height 2.97 m at full (rod up), rim 2.22 m; water top travels 1.50 m (3.1 cm per step of 48) inside the pot; slot 0.38 m wide (33 px at the fight framing); rod sinks 0.81 m below the rim at empty; nodes parented, three clips; water, gold rod rings, inlay; smooth 85%. A draft failed the height gate (rod 1.1 m: 3.32 m at full); the rod was shortened to 0.75 m, the range kept.
- Files: art/clock/round1/ (clock_round1_sheet.png, play_full, play_half, play_empty, play_half_default_sheet, wide, turn_*, top, pass_*, lods, gates.txt), assets/models/clock.glb, art/clock/concepts/.
| Criterion | Round 1 | Result |
|---|---|---|
| The water level reads as a countdown at play size | full, half and empty are clearly different in play_full / play_half / play_empty (blue column in the slot, rod up or sunk, basin filling) | PASS |
| Stacked bronze pots, Qin first | pot on a two-step stand dripping into a basin; outflow clepsydra form; the slot is our invention | PASS (slot: owner to judge) |
| Animatable water level | node transforms per level (no skinning), clips for review | PASS |
| Cast bronze cues | flanges, lid inlay, stamp bands on the stand and basin, dragon spout | PASS |
- Open: LOD1 and LOD2 carry no water (the moving nodes hang under LOD0); in the game the water, rod and basin nodes must stay shown at every LOD (parent them to the LOD group, not to LOD0). The game's own water column (p2WaterMat box) is replaced by clock_water at integration.

## Open
- ComfyUI (owner 22:43: use it): CPU job on GitHub runners, branch ci-comfy (ci_comfy/prompts.json, gen.py, .github/workflows/comfy.yml), SD 1.5 emaonly (CreativeML OpenRAIL-M, commercial use allowed), 512 x 768, 28 steps; output to ci-out out/comfy/<run>/. Prompt = this study's values in words (Qin bronze, segmented casting, silver inlay, cloud-scroll bands, brass-gold, fierce face, spiral-curl mane, round masses, sharp claws and fangs, stepped stone plinth) with the avoid list as the negative prompt. Reference only, never shipped or traced.
- Phone texture set (512) and KTX2 with texture step 3.
