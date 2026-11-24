# FIX-A report: character models after the owner's picks (25 Nov 02:1x-02:2x)

Branch `ci-art-fixa` (from batches-3-5 916292f). Art only: index.html and tests/ untouched. CI files (.github, ci_art) are on this branch only.
Runs (workflow art-run, results on ci-out `out/art/ci-art-fixa/<run>/`):

| Run | Commit | What it showed |
|---|---|---|
| 45462439103 (A1) | 0f81ebd | cubs crashed (Howler bell: freed bmesh verts); giants 108 of 109 (02 fall: ruff 0.65 m into the floor); rest green |
| 45467314311 (A2) | a0d304f | Howler LOD0 4516 tris (over 4000); giants 108 of 109 (slam hit beam 0.77 m in front, min 0.8); rest green |
| 45471050221 (A3, final) | 6417ac3 | **every gate passes**; all GLBs, shots and sheets in this report come from this run |

Process note: A3 changed gate values only (Howler ring counts; one giant slam pose value). For the Howler, A1 built nothing (crash), so A2 and A3 are its two rounds. For the giants, A3 is a third run. It changed one pose number (`SLAM_HIT pelvis_f` -0.1 to -0.05) to fix a gate that A2 broke. The lead should know this goes past the two-round limit.

## Gates (run 45471050221; N of N)

| Asset | Gates |
|---|---|
| Stalker + Howler (cubs_gates) | 23 of 23 (new: tread scroll gate per cub) |
| Guard zu / nu / dun / che / wz | 12/12, 12/12, 12/12, 11/11, 13/13 (each one more than round 5: the new tread scroll gate) |
| Rebels ls / fs / ss / qs | 10/10, 10/10, 11/11, 11/11 (unchanged counts, as asked) |
| Guard + rebel GLB re-read | 45 of 45 |
| Fodder silhouettes | guard 10 of 10 pairs (closest zu/nu 0.65), rebels 6 of 6, all 36 of 36, school weapons 36 of 36 |
| Giants builder | 109 of 109, patina texture 6 of 6, silhouettes 4 of 4 |
| Suits builder | 135 of 135 (new: 7.5-heads gate per suit), silhouettes 30 of 30 |
| Tread strip (tread_tex.py) | 5 of 5; mutations 4 of 4 caught |
| Tread geometry and gate (tread_kit.py selftest) | 8 of 8 (including 4 mutations caught and 2 orientation checks; the A1 orientation bug, re-run as a mutation, fails 16 faces) |
| Rebel colours and glint (rebel_patch_check.py) | 8 of 8; mutations 5 of 5 caught |
| Viewer shots | apex 43 of 43, fodder 65, giants 138, suits 104 without errors (software GL: look only, no frame rate) |


## Items

### 1. Howler cub (apex_cubs.py): reshaped. Verdict: PASS (look: owner)
- Body: a round cauldron belly made of true oval sections, with a lipped rim, a domed lid with a gold knob, two upright ding handles and a cloud band. From the 40 deg camera it reads as a round pot-bellied beast, not a box (`art/apex/round4/play.jpg`; round 3 for comparison: `art/apex/round3/play.jpg`).
- Head: a real beast head on a thick neck, with a domed skull tapering to the muzzle, a V brow, gold eyes, swept gold horns and ears. The flared bell mouth is a solid cup tilted up, with a dark throat plate. A glowing water-blue core (apexOrgan) sits inside and shows from the game camera. Round 3's open bell showed back faces and read as a dark disc.
- Kept: budgets (3812 / 1490 / 428 tris), the rig (21 bones, every vertex on one bone), clips idle / move / attack with a 0.5 s tell (head tip 0.44 m, jaw 42 deg), and size 0.98 w x 1.68 l x 1.80 h m.
- Silhouette vs Stalker: height ratio 1.84 (min 1.4), Howler L/H 0.93 (max 1.0).
- Honest look: from the front the glowing core can read as one big blue eye. At play size the head sits close in front of the belly. The legs are long columns under a round pot, "pot on stilts" more than animal.
- Stalker: shape unchanged. Its belts are now scrolling treads (below).

### 2. Treads: scroll by a texture (guard and cubs). Verdict: PASS
- New strip `assets/tex/tread_belt.png` is 128 x 64 px and holds one repeat = 0.5 m of belt at 256 px/m. It has four cast links per repeat with dark lacquer gaps, in brass-sheet colours. Made by `art/tools/tread_tex.py`.
- Every belt face uses material **treadBelt**, with UVs from `art/tools/tread_kit.py`:
  - **U axis = along the belt loop.** U grows forward along the bottom run (rear to front), up the front, back along the top run and down the rear.
  - U = metres along the loop / metres per repeat. The repeat length is snapped per belt so the loop holds a whole number of repeats (no seam).
  - **V = across the belt**: image rows 0-12 are one side edge, 12-52 the link face, 52-64 the other side edge.
- **Game rule (later, no game code here):** `belt.material.map.offset.x += metres travelled forward / mpr`. Reversing subtracts. Wrap is RepeatWrapping on both axes, and the map loads with flipY false (glTF UVs).
- **Metres per repeat, measured from each built mesh by the gate (world metres):**

| Unit | mpr (m) | Repeats per loop |
|---|---|---|
| Stalker | 0.554 | 2 |
| Howler | 0.477 | 2 |
| zu / nu / dun | 0.540 | 4 |
| che | 0.527 | 8 |
| wz (1.1 scale) | 0.594 | 4 |

- Shape: the guard's separate link prisms are replaced by one belt band, which is also cheaper. The dark core and spoked wheels are kept. The cub belts are the same stadium solids as before, with their running surface on treadBelt.
- Wheels still roll on their bones in the move clip (cubs). Guard wheels are on the hull bone, as before.
- Proof of the scroll: the che belt shot at scroll 0, half a link and one link (`art/guard/round6/viewer/che_scroll_*.jpg`). Belt-strip pixel difference from scroll 0 is 12.5 at half a link and 0.0 at one link: the links move and the loop has no seam.

### 3. War chariot 车: no canopy. Verdict: PASS
- Removed: the canopy, pole, ribs, finial and the canopy bone, plus its idle, move and attack keys.
- The driver sways back a little in the move clip instead.
- Top 2.08 m. Gates 11 of 11 (length 1.9+ m, top under 2.2, tell 0.9 s).

### 4. Twelve giants (giant_blender.py): one shared body, slimmer and taller-reading. Verdict: PASS with notes
- **Longer legs at the same height.** Every mesh vertex and bone is remapped in height:
  - legs 0.3-1.95 m stretch so the hip rises 0.28 m;
  - pelvis, belt and abdomen (1.95-3.1 m) shorten by the same amount;
  - chest, arms, beam and head do not move, so grips, beam, the tells and the walk targets are untouched.
- **Narrower:**
  - waist 0.6 to 0.47 half width;
  - skirt flare 0.64-0.89 to 0.53-0.66, with the hem at 1.76 m (was 1.42);
  - lips only at the hem (less stacked-cylinder look);
  - thighs, shins and boots about 14% slimmer;
  - pauldrons and arms about 12% slimmer.
- **Kept:**
  - carried height 4.63-5.13 m, the same as round 3. g01, g04 and g07 are 5.12-5.13 m because of their hats, 2-3 cm over the owner's 5.1; this was true in round 3 too;
  - width 3.90-4.39 m;
  - body radius 0.74-1.07 (max 1.12);
  - hands on the beam (worst 0.004 m), feet planted (0.000 m), walk 3.20 m/s;
  - slam tell 0.67 m by 0.4 s, sweep tell 1.47 m;
  - every vertex on one bone.
- Comparison at play size: `art/giants/round4/compare_g00_round3_A1_A2.jpg` (round 3 / A1 / final). The skirt no longer reads as a bell and the legs show longer. **Honest look:** at the 40 deg pitch the broad chest, shoulders and beam still dominate, so the body reads less squat but still heavy. Going further needs a narrower shoulder span, which the beam grip (GRIP_X 1.35) fixes. That is the owner's call.

### 5. Giants 02, 05, 07, 08: stronger melted-weapon motifs. Verdict: PASS with notes
- **02**: ruff spearheads 0.62 to 0.95 m and wider, splayed up and out as a sunburst collar. The front three were dropped: they went 0.65 m into the floor in the fall (A1), and dropping them keeps the face clear.
- **05**: apron halberds 0.85 to 1.1 m, fanned out. Hip halberds are raised outward past the arms (1.25 m).
- **07**: hem swords 0.78 to 0.95 m and wider, splayed out from the hem.
- **08**: bigger chest scales, plus a crest of six upright arrowheads fanned on each shoulder.
- All four: melt pools x1.6.
- Silhouette IoU (fight framing; gate max 0.80 top region, 0.92 whole). Each giant's most alike partner:

| Giant | Top region now | Top region round 3 | Whole figure |
|---|---|---|---|
| 02 | 0.765 (with 11) | not reported | 0.870 |
| 05 | 0.780 (with 11) | 0.785 (the gate's closest pair) | 0.846 |
| 07 | 0.763 (with 05) | not reported | 0.845 |
| 08 | 0.747 (with 00) | not reported | 0.874 |

- Wide LOD2 top region: 05-07 0.836 (max 0.85; round 3 0.839). LOD2 keeps the LOD0 silhouette at 0.873 (min 0.8).
- **Margin:** under 0.80 for all four, but only a little wider than before: 05-11 is still the closest pair at 0.780. 05's apron hangs below the "top 42%" region the gate measures. A wider margin needs a change in 05's or 11's top region (head, beam or shoulders): Needs owner.
- At play size the melt pools read as round knobs (bronze on bronze), not as melt. The drips are LOD0 detail.

### 6. Rebels 反贼: patch colours not used by the schools. Verdict: PASS
- `PATCH_COL` = olive #6f6a34, umber #6a4a32, madder #8e5a52. Variant i wears `[i % 3]` (patchwork, not a school code).
- Colour distances (CIELAB dE):
  - nearest school colour 24.1-31.3 (min 20), checked against both W1a's ding pigments and the game's current CONFIG.COL.schools;
  - hemp 20.2-22.2;
  - between each other 15.0 minimum.
- The GLB extras key `schoolColours` is now `patchColours`. The viewer and the preview use the new colours.

### 7. 死士 glint larger. Verdict: PASS
- The four-point star is now 0.62 m across with 0.11 m arms (was 0.36 x 0.07). That is 68 px at the fight framing (was 40).
- Shown from 0.2 s to the 0.6 s windup, so 0.4 s of tell. The ss show/hide gate passes.
- Shot: `art/guard/round6/viewer/ss_tell.jpg`.

### 8. Suits: about 7.5 heads. Verdict: PASS
- Heights up to the chin are x1.118 and the head x0.93 (height and width). At H 1.0 the crown is 2.02 m and the head 0.27 m (study: 1.86 m and 0.29 m).
- 7.51 heads for all nine. The new gate fails the round 3 proportions (6.41) as its mutation.
- Height with crest 1.87-2.46 m (gate 1.7-2.9). All other suit gates are kept (135 of 135, silhouettes 30 of 30).
- Not repainted for floor contrast (owner: 2 px outline later). The suit_contrast report line was not run this round.

### Other owner decisions applied in the viewers (art tools only)
- Brass sheet: the apex and fodder viewers now use `bronze_trim_brass.png` for awake bronze. The giants viewer already did.
- One school mapping: `art/viewer/apex_mat.js` SCHOOLS is now W1a's ding pigments, so the tiger school variants follow it.

## Files
- **Tools:** `art/tools/tread_kit.py` (new), `tread_tex.py` (new), `rebel_patch_check.py` (new), `apex_kit.py` (`tread()`; tread rows keep their UVs), `apex_cubs.py`, `fodder_base.py` (`tread()`), `guard_build.py`, `rebel_build.py`, `fodder_preview.py`, `giant_blender.py`, `giant_sheets.py` (MEASURE lines), `suit_blender.py`, `shoot_fodder.mjs` (scroll shots).
- **Viewers:** `art/viewer/apex_mat.js`, `art/viewer/fodder.html` (`&scroll=` and `&mpr=` parameters).
- **Assets (final run, replacing the round 3 and 5 GLBs on this branch only; the previous versions stay in batches-3-5):** `assets/tex/tread_belt.png`, `assets/models/apex/{stalker,howler}.glb`, `assets/models/guard/*.glb`, `assets/models/rebels/*.glb`, `assets/models/giants/giants.glb`, `assets/models/suits/*.glb`.
- **Shots and gate logs:** `art/apex/round4/`, `art/guard/round6/` (includes `checks: tread_tex.txt`, `tread_kit.txt`, `rebel_patch.txt`), `art/giants/round4/`, `art/suits/round4/`.

## Needs owner
1. Howler look: is a round lidded pot with a horned beast head right? From the front the glowing throat core can read as one big blue eye.
2. Giants: slimmer but still heavy at 40 deg. A narrower shoulder or beam span is the next lever (it changes the beam and grips).
3. Giants 01, 04 and 07 are 5.12-5.13 m with their hats (owner said 5.1; the gate allows 5.3). Trim the hats or accept?
4. Giant top-region margin: 05-11 at 0.780 is the closest pair. To widen it, change 05's or 11's head, beam or shoulders.
5. Melt pools read as knobs at play size. A colour change (darker or tinted melt) would read better than more size.
6. Suits' cloth colours do not follow the one school mapping (outside this brief, not changed). za's cloth is #2e5a9c (azurite, which is nong in the ding mapping) and zh's is #5b3f8c (Han purple, which is ming). Cords were not checked.
7. The game wiring for tread scroll later: offset.x += metres forward / mpr (values above).
