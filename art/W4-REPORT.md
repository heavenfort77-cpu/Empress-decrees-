# W4 report: apex Tiger Demon and cubs (overnight run, 25 Nov 2026 00:18-01:3x, owner asleep)

Scope (art/OVERNIGHT.md, lead brief): the apex Tiger Demon (兵家 bronze tiger, patina asleep / brass awake, three inlaid organ weak points, plates that shed), its cubs Stalker and Howler (four-legged tread machines), and the school-colour variant rule for the ending. Nothing went into the game; no game code changed. Branch `ci-art-w4`.

## Runs (all GitHub runners; local work was only short Blender builds and one klad paint under the heavy-job lock)
| Run | What | Result |
|---|---|---|
| ComfyUI 45435750508 (branch ci-comfy-w4) | 32 concepts: tiger side and 3/4 (5101-5118), tortoise and ox tread machines (5201-5218) | 32 of 32 images |
| art 45439899275 | round 1 | gates tiger 15/15, cubs 21/21, tex 10/11 (patina lum 110), shots 39/39; ci-out commit FAILED (job left tracked .pyc files modified); fixed in job.sh |
| art 45443002962 | round 1b | tex 11/11, tiger 15/15, cubs 21/21, shots 39/39 (art/apex/round1/) |
| art 45445789712 | round 2 | tex 11/11, tiger 15/15, cubs 21/21, shots 41/41 (art/apex/round2/) |
| art 45446620414 | round 3 (final files) | tex 11/11, tiger 15/15, cubs 21/21, shots 43/43 (art/apex/round3/) |
Gate mutations (local, bpy 5.3): 5 of 5 caught (pounce windup 0.3 s, a plate removed, tail tell flattened, cub windup 0.3 s, wheels not rolling).

## Concepts (reference only, never shipped or traced; art/apex/concepts/)
- Tiger pick **5107** (crouched bronze cat, head carried below the shoulder hump, heavy forearms). Alternates for the owner: **5101** (long standing side view), **5108** (standing gold tiger, open mouth). Measured on 5107: head length 0.48 and nose height 0.52 of the shoulder height; on 5101/5108: body length 1.24 of the shoulder height, belly at 0.45-0.49. Model: head 0.49 (matches), body 1.62 (kept longer: a tiger, not a bulky cat), belly 0.40.
- Stalker pick **5208** (tortoise with a segmented shell), alternates **5216** (low hull, cast seam lines; hull L/H 1.96, legs 0.37 of the height), **5202**. Howler pick **5218** (ding cauldron on four column legs; legs 0.49 of the height, rim lip, side lugs), alternate **5213** (ox with ornament bands and ringed leg joints).
- None of the concepts shows segment seams, inlay or treads: those come from the research rule list and the bronze study.

## Tiger Demon
Files: `assets/models/apex/tiger.glb` (1.9 MB), builder `art/tools/apex_tiger.py` + shared `art/tools/apex_kit.py`, dormant sheet `assets/tex/apex_patina.png` (klad source `art/src/apex_patina.klad`, ops `art/tools/apex_tex.py`, passes `art/apex/round3/apex_patina_passes.png`), viewer `art/viewer/apex.html` + material rule `art/viewer/apex_mat.js`, shots `art/apex/round3/` (tiger_sheet.png, play_sheet.png, schools_sheet.png).
- Build: hind, mid and fore body castings on hips/spine/chest bones with flange seams; legs in three or four segments with flange lips at every joint; long ringed tail with a gold finial; flat broad skull, cheek fins, gold almond eyes, scowl brows, small sharp ears; gold inlay lines that are both its stripes and its crack lines, plus a dorsal inlay seam nose to tail (the split line of the tally). No mane or curls (the door guardians are lions).
- Plates: six sheddable plates (shoulders 0/1, flanks 2/3, haunches 4/5), each a separate node parented to its own bone `b_plate_N`, with two inlay lines and a workshop mark. Wake peels plates 0 and 1 (the two hunt minions); the game detaches a plate by re-parenting its node (three.js `attach`).
- Organs (Yan Shi logic): `organ_throat` (neck underside, roar; shown by the roar windup), `organ_eye` (forehead, sight), `organ_legs_L/R` (top of the rump, legs). Each a lens core (`apexOrgan`) in a gold inlay ring; separate nodes for hit flashes; hit-testing should use simple shapes (rule 42).
- Clips: dormant (crouch), wake (3.0 s: still, head lifts and jaw opens at 1.4 s, rises at 2.1 s, steps and peels plates 2.6-3.0 s), idle (2 s), pounce (0.5 s windup tell), roar (0.5 s windup tell). The exporter starts keys at 1/60 s, so clip lengths read 1/60 s longer (wake 3.02 s).
- Gates, run 45446620414, 15 of 15: LOD tris 14218 / 2806 / 957 (budget 15000 / 3000 / 1000, plates and organs counted); every vertex on one bone (3 skinned LODs, 30 bone-parented plate/organ nodes); plates 6 per LOD on own bones, 6 marks; 3 organs on neck/head/hips bones; standing 2.52 m tall (band 2.2-2.7), 6.07 m with tail; dormant crouch 1.54 x 4.86 m, 1.94 m tall (statue solid 3.2 x 5.0); feet on the floor (dormant lowest -0.04 m); wake 3.0 s with plates 0/1 moving 0.80 m; pounce tell 0.5 s, hips drop 0.37 m, tail tip rise 0.49 m; roar tell 0.5 s, jaw 42 deg, throat core up 0.75 m; smooth share 93% of area; crack inlay 6.5 cm wide; GLB has all five clips. Draw calls (counted in the GLB): 24 at LOD0 and LOD1, 14 at LOD2.
- Measured look (mean luminance inside the silhouette, 3/4 view, 0-255): study bronze (metalness 0.4, roughness 0.6) 42; brass option A (0.25, colour x1.3) 51; option B (0.1, x1.8) 62; dormant patina 39.

Verdict (worker's read of the shots, software GL):
| Criterion | Round 3 | Result |
|---|---|---|
| Reads as a tiger, not the guardian lion | long low body, striped, flat skull, no mane; reads tiger-like at play size | PASS |
| Segmented casting: seams, flanges, plates, marks, inlay | body seams, joint flanges, six plates with marks, inlay lines all visible at play size | PASS |
| Round where round, sharp where sharp | lofted round masses (93% smooth area), sharp claws, fangs, fins, ears, flanges; plates read a little boxy over the shoulders | PASS with note |
| Fresh brass-gold awake | study values read dark brown (lum 42); option B reads brass at the fight framing (play_sheet.png right) | NOT MET with the study values; needs the owner's material choice |
| Glow is inlay, not neon | round 1 (1.4) read neon; round 3 (0.3 on a gold base) reads as pale blue-white lines; still blue-first, not gold | PASS with note |
| Dormant patina vs awake brass | clear green statue vs brass beast (dormant_34, wake frames) | PASS |
| Tells >= 0.4 s readable as shape change | pounce crouch + raised tail, roar head-up exposing the throat core | PASS |
| Size vs the game | fits the statue solid asleep; 2.52 m vs the 2.05 m suit | PASS; but CONFIG.DEMON.r 0.9 m is small for a 1.5 m wide, 4.9 m long body (game number, not changed) |
Overall: gates 15 of 15, look 6 of 8 criteria fully met; three rounds used. Parked under Needs owner for the bronze value (and the glow colour).

## Cubs: Stalker (正) and Howler (奇)
Files: `assets/models/apex/stalker.glb`, `howler.glb` (0.6 MB each), builder `art/tools/apex_cubs.py`; shots `art/apex/round3/cubs_sheet.png`, play_sheet.png.
- Both are the tiger's plates grown legs: same bronze trim sheet, flange rims and cast seams, gold-inlay crack lines (`apexCrack`, glowing while alive), workshop mark, tread bogies (track belt over chariot wheels; wheel bones roll in the move clip).
- Stalker: low tortoise dome (segmented shell seams, keel, skirt flange) on four short splayed legs, long two-wheel bogies, low wedge head that bites straight ahead. Howler: ding cauldron hull with rim lip, cloud band and ring lugs, on four column legs with knee flanges, one big spoked chariot wheel per foot, raised head with a bell mouth (dark throat) and sharp back-swept horns.
- Clips: idle 2 s, move 1 s loop (wheels 360 deg, diagonal leg sway, body bob), attack (0.5 s windup tell: Stalker draws back and opens the jaw; Howler rears and opens the bell).
- Gates, run 45446620414, 21 of 21: Stalker tris 3566 / 1208 / 450, Howler 3442 / 1392 / 434 (budget 4000 / 1500 / 500); every vertex on one bone (21 bones each); attack tells 0.5 s with head tip 0.24 / 0.35 m and jaw 34 / 42 deg; wheels roll 90 deg per quarter clip; Stalker 1.18 w x 1.93 l x 0.98 h m, Howler 1.16 x 1.51 x 1.60 m (width within the 0.5 m hit circle + 0.25, under the 2.05 m suit); smooth share 93% / 97%; distinct silhouettes (height ratio 1.64, Stalker L/H 1.97, Howler L/H 0.94). Draw calls 3 (Stalker) and 4 (Howler).
Verdict: Stalker reads as a bronze tortoise machine on treads (PASS). Howler: round 1 read as a table with a dog head (FAIL); rounds 2-3 (bigger hull, narrower rim, thick legs, recessed throat) read as a horned cauldron beast on wheels; the head is still box-like, the bell throat still shows as a dark disc and the rim reads flat from the 3/4 view (PASS with note). Both: same dark-bronze issue as the tiger (follows the owner's material choice). Stalker is 1.93 m long against a 0.5 m hit circle (game number, not changed).

## School-colour variant (ending; GDD WINNER_STATUE)
Rule in `art/viewer/apex_mat.js` (`apexMaterials(THREE, tex, state, school, brass)`), same mesh and UVs: bronze map tinted toward COL.schools[i] (0.4 awake, 0.25 asleep); crack lines and organs take the school colour (glowing awake; unlit inlay asleep), lifted so the brightest channel is 1 (阴阳 0x3a3a3a still shows as grey-white). Shots: schools_sheet.png (nine variants awake and as the dormant statue). Not built: the emblem decal (needs emblem art).

## For the morning (not done tonight, by scope)
- Game integration: swap the box statue and demon for tiger.glb (THREE.LOD over the three skinned bodies, plates/organs per LOD by name suffix), pools for detached plates, compile under the loading card, KTX2 and a 512 phone sheet. Not done: phone texture, KTX2, real-GPU shots.
- CI files on this branch (`ci_art/job.sh`, `.github/workflows/art-run.yml`) are not deliverables; leave them out of batches-3-5. `art/tools/tex_check.py` gained the apex_patina rules (patina hue, value 55-105).

## Needs owner
1. Bronze value: study values (metalness 0.4, roughness 0.6) read dark brown (lum 42); option A (lum 51) or option B (lum 62, reads brass at play size) in apex_mat.js. Same question as the guardian beast round 2 note.
2. Crack glow colour: water-blue per docs/SUITS.md (current, intensity 0.3 on gold inlay) or gold-warm glow (closer to "fresh brass-gold" and further from the cyan hazard hue).
3. Design approval of tiger (concept 5107; alternates 5101, 5108), Stalker (5208; alternates 5216, 5202), Howler (5218; alternate 5213).
4. Game numbers (not changed): CONFIG.DEMON.r 0.9 m vs a 1.5 x 4.9 m tiger; cub r 0.5 m vs a 1.93 m long Stalker.
5. Emblem decal for the winner's school (variant rule ready, emblem art missing).
