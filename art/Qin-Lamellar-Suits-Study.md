# Qin Lamellar Suits (3D characters, klad-textured): study

Own compartment for the nine school suits (docs/SUITS.md). The palace surfaces (art/Qin-Palace-Painted-Study.md) and the cast-bronze props (art/Qin-Bronze-Castings-Study.md) keep their own studies; this one shares only the game camera, the lights, the 256 px/m texel density and the klad method with them. Worker W3, overnight run 25 Nov 2026 (owner asleep): every value below is a proposal until the owner approves a sample.

- Reference, in order (art/OVERNIGHT.md): the GDD (docs/GDD.md lore and the nine-schools table; docs/SUITS.md kits decide outline and props); the research (docs/research/Qin-palace-medieval-tech-fusion.md: small hard plates tied with a binding whose material marks school or rank, after the jade-suit rule; lamellar on the terracotta base; the excavated mineral palette; Qin black for the court; avoid samurai lacing, katanas, torii, Qing clothing, sci-fi panel lines, neon); then two of the owner's own kits as technique reference only (owner 00:15: "it is reference, not telling you to copy"): the Suit Mythology kit (approved sheets: one dominant outline per suit, three-step ramps, light from the upper left, seams as tone changes) and the techno-plate 3D kit (its HANDOFF-3D.md weak points: parts assembled from lathes and spheres, 24-51k triangles, heads need sculpted shells, every character needs its own metal, trim and shapes). No code, sprite or model from either kit is used (repo rule). Licence of the kits: the owner's own.
- ComfyUI concepts (SD 1.5 + LCM LoRA on CPU runners, run 45435893887, 36 images, reference only, never shipped or traced). Source quality: 512 x 768, 6 steps; most images are costumed people with Qing-looking collars and no armour or props despite the negative prompt, so they inform proportions and a few cues only. Picks and alternates per suit are listed under "Concepts".

## What the GDD and SUITS.md ask of the suits
- Nine suits, one per stream (九流), each "hard-surface armour that fights with its school's doctrine"; every kit works solo in a free-for-all; the nine must be told apart in a fight at the game camera.
- Kits decide outline (owner rule for this run: outline first, colour second): 法 bronze sword and pursuit; 儒 sword or bow by range, chariot, bells; 道 open hand and counters; 墨 repeating crossbow, wall, lever (tank, no dash); 阴阳 dark and light orbs (artillery); 杂 orb, a seal and a stored copy (the book no one could change by a word); 名 thrown bronze wheel (marksman); 纵横 the envoy's tally and the link (control); 农 plough-hoe, seeds and sprouts (support).
- Fairness rule: every attack has a tell of at least 0.4 s; the windup must read as a shape change at play size.
- Budget: characters 10-15k triangles with a low LOD (owner rules 36); heaviest scene under 500 draw calls and 0.5M triangles.

## Measured or computed values
| Value | Number | How |
|---|---|---|
| Pixels per metre, fight framing | 110 px/m | FOV 50, 10.5 m, 1080 px: 1080 / (2 x 10.5 x tan 25 deg) |
| Pixels per metre, wide framing | 52 px/m | 22 m |
| Suit body height on screen (fight framing, crown, pitch 40) | 210-219 px | suit_sil.py, round 2 (fa 219, ru 210) |
| Concept fa_5102 (upper body; cropped at the knee) | helmet with mask 16% of frame; shoulder span 2.2 head heights; chin to belt 1.9; crown to hands 3.5 | 5% ruler (cocolito method), read by eye on the 2x image |
| Concept zh_5171 (full figure) | about 8.5 heads with the hat; hands at 50% of height | 5% ruler |
| Model before the concept read (round 1) | shoulders 2.1 heads, chin to belt 1.7, crown to hands 3.66 | builder levels |

## Values (the builder art/tools/suit_blender.py holds every one in its CONFIG and SUITS data)
### Proportions (H = 1.0; each suit scales height H, shoulders W, girth G, limbs L)
- Crown 1.86 m; head (chin to crown) 0.29 m = 6.4 heads. The concepts are realistic (7.5-8.5 heads); 6.4 is chosen for play-size readability (the head and crest carry the school read at 25-30 px) and is a stylisation, not a measurement.
- Levels: ankle 0.09, knee 0.50, hip joint 0.92, belt 1.03 (round 2: lowered from 1.07 so chin to belt is 1.86 heads, concept 1.9), chest 1.30, shoulder joint 1.45, neck 1.52, chin 1.57.
- Shoulder joint at x 0.20 W; hip joint x 0.095 G; arms hang 5-8 cm out from the body; hands at 0.80-0.91 m (crown to hands 3.6 heads, concept 3.5).
- Builds: 法 H1.0 W0.92 G0.9 (lean); 儒 1.02/1.1/1.05 (broad, upright); 道 0.98/0.9/0.88 (slight); 墨 0.9/1.3/1.3 (short, massive); 阴阳 1.0/1.0/0.95; 杂 1.0/1.0/1.0; 名 1.0/0.95/0.88 (slim); 纵横 1.0/1.0/0.98; 农 0.96/1.15/1.15 (sturdy).

### Construction (answers the techno-plate weak points)
- Every part is a loft of superellipse sections (exponent 2 = round, 2.4-3 = rounded square for plates), resampled with Catmull-Rom at most 4.5 cm apart: round where round, sharp only where a blade or prong is (split normals over 48 deg). No boxes, no lathe-and-sphere assembly.
- Lamellar = stacked rows 12.5 cm tall, each flaring 1.4 cm at its lower edge and folding back under (the overlap reads as a stepped outline); one row = one 32 px strip of the sheet with 8 cm plates (2.5 px wide at the wide framing, 9 px at the fight framing). A cord band (3.5 cm, 6 mm proud) in the school's binding colour ties every second row, the collar and the belt. No mail anywhere, no samurai cross-lacing (the cords run horizontally, as tied lamellar).
- Head: a lacquer helmet shell and a bronze face mask with stern slanting eye slits (the suit is armour; no skin anywhere, which also keeps the colour count low). The crest is the school's main outline cue.

### Outline per suit (the silhouette test checks these)
| Suit | Crest | Shoulder mass | Weapon or prop | Lower body | Back |
|---|---|---|---|---|---|
| 法 廷尉 | one tall 獬豸 horn hooking forward, cheek prongs (concept fa_5102) | small two-row caps | long bronze jian held low and out | split tassets with a long front apron plate (fa_5102) | none |
| 儒 君子 | tall slanted board cap rising to the back | wide three-row layered pauldrons | jian in the right hand, tall recurved bow in the left | long five-row skirt | quiver |
| 道 真人 | small crown on a topknot, hairpin, two long ribbons | none: huge sleeves | empty hands | bell robe to the ground | ribbons |
| 墨 墨守 | low wide dome with a broad brim | two huge domes | repeating crossbow at the hip | short skirt, thick legs | none |
| 阴阳 太极 | moon horns (one white, one black) and a gold sun disc | one white dome, one black dome | a dark orb and a light orb, one per hand | narrow column robe | none |
| 杂 门客 | soft cap with two hanging side flaps | mixed: a Mohist dome left, Confucian rows right (兼儒墨) | bronze orb | knee robe in azurite | fan of bamboo slips |
| 名 辩者 | one long pale plume swept back | one big round guard on the off shoulder | spoked, toothed bronze wheel at the side, face to the front | short tassets, slim legs | none |
| 纵横 说客 | twin long purple plumes | cape over the left shoulder | envoy's staff with three tiers of purple tufts | knee robe in Han purple | cape |
| 农 耕者 | conical hat-helmet | medium domes | two-pronged bronze hoe over the shoulder | short skirt | seed basket with sprouts |

### Colour (second; school accents from the research palette)
- Plate lacquer per suit: 法 black, 儒 brown, 道 lead white, 墨 brown, 阴阳 black with one white shoulder, 杂 brown, 名 brown, 纵横 black, 农 brown. Qin black stays the court's colour and 法's (the empress's own doctrine).
- Binding colour (cord rows): 法 cinnabar #B0402C, 儒 gold #C9A54A, 道 lead white #E4DED0, 墨 ochre #B8862E, 阴阳 bone black #1E1B1A, 杂 azurite #2E5A9C, 名 silver #BFC3C6, 纵横 Han purple #5B3F8C, 农 malachite #2F8A5C.
- Cloth tint (material colour over the neutral cloth sheet): 法 #2B2422, 儒 #DDD5C3, 道 #D9D3C4, 墨 #6B5634, 阴阳 #26232A, 杂 #2E5A9C, 名 #4A4440, 纵横 #5B3F8C, 农 #6E6A4A.
- Inlay trim: gold on 儒 墨 杂 纵横 农; silver on 法 道 阴阳 名.
- Lacquer ramps (deep, shadow, base, light, polish): black #120F0F #1D1918 #2A2524 #3E3533 #5E504A; brown #2E1B12 #462A1C #5C3A26 #744C32 #94683F; cinnabar #5A1D13 #7E2A1C #A33A28 #BD4E34 #D6765A; white #8C8577 #B3AB9B #D2CAB9 #E2DCCD #F1ECE0. Bronze fittings #3A2B1A #5E482B #8A6A3C #A88A52 #C8A86A (fresh, no patina on live suits); gold inlay #D4B25A, silver inlay #C8CCD0.
- Not used: neon, the reserved hazard cyan #3FE6F0, glow of any kind.

### Sheets (klad, 256 px/m; art/tools/suit_tex.py places marks, klad paints them, art/tools/suit_paint.py)
- suit_lamellar 1024 x 1024 (4 x 4 m): plate fields black 0-152, brown 152-304, cinnabar 304-408, white 408-512; lamellar rows 512-640 (black, brown, cinnabar, white); rim, gold, silver bands 640-736; nine cord rows 736-1024.
- suit_bronze 512 x 512 (2 x 2 m): plain 0-192, gold 192-224, silver 224-256, blade 256-320, rivets 320-352, dark bronze 352-416, mask 416-512.
- suit_cloth 512 x 512 (2 x 2 m): neutral silk and hemp with folds and weave; tinted per suit.
- Three materials per suit (lamellar, bronze, cloth): 3 draw calls per suit and LOD, 27 for all nine.
- Light painted from the upper left (lit upper and left plate edges, overlap shadow on the right of each lamella).

### Rig and clips
- Bones: root, hips, spine, chest, neck, head, upper_arm/forearm/hand, thigh/shin/foot per side, and a weapon bone (child of hand.R, along the weapon). Plates, helmets and props are rigid (100% on one bone); robes, long skirts, sleeves, capes and ribbons get Blender automatic (bone heat) weights restricted to the bones each may follow (a robe follows hips and legs, never the arms). At most 4 influences.
- Clips: idle 1.0 s loop (breath on chest, hips and arms); attack = windup (the kit's tell) -> strike -> 6-frame hold -> recover. Windups: 法 thrust 0.45 s, 儒 overhead cut 0.5 s, 道 palm 0.42 s, 墨 crossbow raise 0.5 s, 阴阳 both orbs overhead 0.6 s, 杂 orb drawn back 0.45 s, 名 wheel drawn back 0.5 s, 纵横 staff raised 0.45 s, 农 hoe overhead 0.5 s.

### Gates (printed PASS/FAIL by suit_blender.py, suit_sil.py and tex_check.py)
- Triangles: LOD0 10,000-15,000; LOD1 2,000-3,000; LOD2 300-999. LOD outline at the wide framing: IoU against LOD0 >= 0.90 (LOD1), >= 0.82 (LOD2).
- Rig: no unweighted vertex; weight sums 1 (+-0.02); <= 4 influences; cloth heat weights solved without fallback; GLB re-imports with 3 skinned meshes and both clips.
- Tell: windup >= 0.4 s and the weapon tip moves >= 0.3 m from rest by the end of the windup.
- Materials (draw calls) <= 3 per suit; texel density on every part >= 0.8 of 256 px/m (long thin parts run along the sheet's wrapping axis).
- Readability: body height 150-260 px at the fight framing.
- Silhouette test (the nine told apart by outline alone): flat-black silhouettes from the same camera and spot; every pair's intersection over union <= 0.75 in the front, 3/4 and side views. Mutation-tested: a copied suit gives 1.00 and fails; a LOD1 with two thirds of its triangles cut gives 0.68 and fails.
- Sheets (tex_check.py, suit rules): density 256 px/m +-20%; plate fields brush run 4-25 cm, contrast and value bands per lacquer (brown value band 35-100: lowered from 45 on purpose in round 3 when the brown lacquer was darkened away from the floor value), saturation cap 0.6 (cinnabar 0.8, white 0.2); bronze plain brush run 4-15 cm and mean luminance 85-135; cloth mean luminance 180-240 and saturation <= 0.12; each cord row median within RGB distance 50 of its school colour; lamella width 7-9 cm (dominant period by FFT). Mutation-tested: a wrong cord colour, a flat-filled plate field, lamellae stretched to twice the width and a tinted cloth sheet each fail.
- Floor contrast (suit_contrast.py, palace study rule): at least 50% of each suit.s outline pixels reach 3:1 against the approved hall floor beside them in the fight-framing lineup.

## Concepts (run 45435893887; reference only; art/suits/concepts/<id>_concepts.jpg shows the pick and two alternates)
Criteria, in order: the kit's outline cue is present (crest, shoulder mass, weapon); Qin-compatible materials (plates, not Qing collars and buttons); full figure for proportions. Honest read: SD 1.5 at 6 steps gave costumed people for most prompts; no image shows the requested prop except fa_5102 (horn), ming_5162 (round guard) and za_5151 (flap cap).
| Suit | Pick | Alternates | What was taken |
|---|---|---|---|
| 法 | fa_5102 | fa_5103, fa_5101 | horned helmet with full bronze mask, long front apron between split tassets, cheek prongs; upper-body ratios |
| 儒 | ru_5111 | ru_5112, ru_5113 | lamellar torso over a long skirt (confirms the layered build) |
| 道 | dao_5122 | dao_5121, dao_5120 | wide sleeves and a long robe with a plated centre panel |
| 墨 | mo_5133 | mo_5130, mo_5132 | squat heavy build; 5130's massive shoulder plates |
| 阴阳 | yy_5142 | yy_5141, yy_5143 | narrow white column robe with a black and white split (round 2 narrowed the robe from a bell) |
| 杂 | za_5151 | za_5153, za_5150 | cap with hanging side flaps, azurite cloth, lamellar skirt |
| 名 | ming_5162 | ming_5161, ming_5163 | one big round guard on the off side, slim build |
| 纵横 | zh_5171 | zh_5173, zh_5170 | tall figure in purple; full-figure proportions (about 8.5 heads) |
| 农 | nong_5182 | nong_5181, nong_5183 | sturdy build, short pleated skirt, rope belt |

## Samples, rounds 1-3 (25 Nov 2026, not approved)
Rounds are runner rounds with shots (local Blender builds before them were probes): round 1 run 45440123875, round 2 run 45443383613, round 3 run 45444757353 (final code). Review sheets: art/suits/roundN/<id>_sheet.jpg (front, 3/4, side, back, windup, strike, passes, LODs, a 1:1 crop at the fight framing), lineups lineup_play.jpg, lineup_wide.jpg, lineup_play_rim.jpg, the flat-black silhouette lineups sil_lineup_front.png and sil_lineup_34.png (same spot, play size), sil_matrix.txt, gate logs.
What changed per round: round 1 -> 2: lacquer as blots instead of streaks (round 1 read as wood grain), darker brown lacquer (round 1 brown sat at the floor's value), per-school eyes and brows (round 1 shared one mask), viewer rim option and the floor contrast measure. Round 2 -> 3: brown and bronze sheet contrast, 法's off arm in the strike. Before round 1, local probes fixed: weapon in the left hand (axis flip), twisted lamellar lips and domes (frame flip), a hanging sword that read as a cane, a horn that read as a topknot, ru's hidden back bow (now in hand), 名's edge-on wheel (now face on), 阴阳 and 道 sharing a bell robe.

### Budget (round 3)
| Suit | LOD0 / LOD1 / LOD2 tris | Materials (calls) | GLB KB | Tell s | Tip travel m | Height with crest m | Height on screen px |
|---|---|---|---|---|---|---|---|
| 法 | 12,572 / 2,600 / 899 | 3 | 779 | 0.45 | 1.13 | 2.25 | 219 |
| 儒 | 13,464 / 2,600 / 900 | 3 | 838 | 0.50 | 2.70 | 2.25 | 224 |
| 道 | 10,168 / 2,600 / 899 | 3 | 611 | 0.42 | 0.73 (hand) | 1.89 | 191 |
| 墨 | 11,264 / 2,599 / 899 | 3 | 705 | 0.50 | 0.53 | 1.73 | 161 |
| 阴阳 | 13,440 / 2,599 / 900 | 3 | 728 | 0.60 | 1.45 | 2.13 | 196 |
| 杂 | 13,644 / 2,600 / 900 | 3 | 794 | 0.45 | 1.33 | 1.95 | 192 |
| 名 | 10,680 / 2,600 / 900 | 3 | 702 | 0.50 | 1.53 | 1.99 | 204 |
| 纵横 | 13,140 / 2,600 / 899 | 3 | 755 | 0.45 | 1.30 | 2.33 | 234 |
| 农 | 11,444 / 2,600 / 900 | 3 | 728 | 0.50 | 1.36 | 2.28 | 224 |
All nine at LOD0 on screen at once: 109,816 triangles and 27 draw calls (a royale with nine suits in view stays well inside 500 calls and 0.5M triangles). Sheets: 1024² + 512² + 512² (one set shared by all nine).

### Silhouette test (round 3)
Most alike pairs: front za-zh 0.73, 3/4 ru-yy 0.71, side ru-za 0.70 (limit 0.75): 30 of 30 silhouette and LOD gates pass. LOD outline IoU at the wide framing: LOD1 0.95-0.99, LOD2 0.92-0.97. Read by eye on sil_lineup_front.png and sil_lineup_34.png: each of the nine is named from its outline alone (horn; board cap and bow; bell robe; brimmed dome and domes; moon horns and orbs; slip fan; wheel; staff tufts and twin plumes; cone hat and hoe). Viewer silhouettes: lineup_sil_front.png; the viewer's 3/4 lineup puts the row on a diagonal and crops 农 at the edge (use sil_lineup_34.png for the test).

### Verdict per suit (round 3; honest)
Gates per suit: 14 build gates + 3 readability/LOD gates + 1 floor contrast = 18. Shared: silhouette pairs 3 of 3, sheets 39 of 40.
| Suit | Gates | Verdict | What a person would still see is wrong |
|---|---|---|---|
| 法 | 17 of 18 | outline passes; fails floor contrast | black on the cinnabar floor is 1.9:1; arms are plain tubes; the mask's eyes are 2-3 px at play size |
| 儒 | 17 of 18 | outline passes; fails floor contrast | brown body 1.8:1 on the floor; the bow is thin at the wide framing |
| 道 | 17 of 18 | outline passes; fails floor contrast (closest: 23% of outline at 3:1, body 2.4:1) | the topknot crown is small; empty hands, so the tell is the arm only (0.73 m) |
| 墨 | 17 of 18 | outline passes; fails floor contrast | brown 1.6:1; the crossbow is mostly hidden from the front |
| 阴阳 | 17 of 18 | outline passes; fails floor contrast | black robe 1.7:1 on the floor |
| 杂 | 17 of 18 | outline passes; fails floor contrast | brown 1.6:1; closest silhouette pair (with 纵横, 0.73) |
| 名 | 17 of 18 | outline passes; fails floor contrast | brown 1.6:1 |
| 纵横 | 17 of 18 | outline passes; fails floor contrast | lowest contrast (1.4:1, black and purple) |
| 农 | 17 of 18 | outline passes; fails floor contrast | brown 1.6:1; the seed basket is hidden from the front |
Known limits of the method: parts are lofts joined by overlap, not one sculpted surface; hands are mitts; the clips are two-key poses (windup, strike) with no follow-through on cloth beyond the bone-heat weights; no walk or run clip was in scope.

### Open (Needs owner)
1. Floor contrast. On the approved hall floor (relative luminance 0.06 in the viewer at the fight framing) a dark suit cannot reach the palace study's 3:1: pure black ink tops out at 2.2:1, and 3:1 needs a light edge of luminance 0.28 or more. Measured options: (a) a pale view-facing rim in the suit material (viewer &rim=1): outline pixels at 3:1 rise from 0-23% to 23-48% per suit, but the lamella lips catch it as white specks; (b) a 2 px lead-white outline drawn by the game's renderer (derived: 7:1 against the floor; game code and one mask pass, not done tonight); (c) light plates (ochre plates about 0.27 luminance, near 2.9:1; loses Qin black); (d) accept dark suits below 3:1 (body medians now 1.4-2.4:1).
2. suit_bronze plain field: brush run 3.9 cm against the 4 cm minimum after three sheet rounds (the sand-cast mottle is finer than the palace rule's lower bound).
3. 6.4-head proportions are a readability stylisation against the concepts' 7.5-8.5 heads.
4. School colour mapping (accent per school, lacquer per suit) is the worker's proposal from the research palette.
