# Techno-plate set, 3D samples: handoff

Status (2026-11-12): batch 13 done, waiting for approval. Nothing is in the Style Library.

## Files
- `techno_plate_set.html`: one self-contained page (Three.js r158 inlined) with all four characters. Buttons at the top switch between Knight, Mage, Rogue and Beast. Drag to rotate, pinch to zoom, Spin on/off, Export GLB (exports the character on screen). An fps readout is at the top.
- `techno_plate_knight.glb`, `_mage.glb`, `_rogue.glb`, `_beast.glb`: exported by the page in the headless check.
- `sheet_knight.png`, `sheet_mage.png`, `sheet_rogue.png`, `sheet_beast.png`: front, three-quarter, side and back captures. `lineup_3d.png`: all four at three-quarter.
- `main.js`: the source. Colours, roughness, flute count, wear, glow and engraving depth are in the CONFIG block at the top.
- `shot_set.py`: headless check for all four (console errors, 4 views each, GLB export each). Prints PASS/FAIL. Takes about 2 to 3 minutes.
- `techno_plate_knight.html`: the earlier knight-only page (kept, not updated).
- Backups: `main_v1_backup.js` to `main_v12_backup.js` (knight history), `main_v13_backup_knight_only.js` (last knight-only script), `main_v14_backup.js` (four characters before the new rogue and dragon heads), `main_v15_backup.js` (long-neck dragon, all four in the same steel), `main_v16_backup.js` (before own shapes per character and the dragon body).

## Rebuild
`npm install three@0.158.0 esbuild`, then `npx esbuild main.js --bundle --minify --format=iife --outfile=bundle.js`, then replace the contents of the page's script tag with `bundle.js`, then `python3 shot_set.py`.

## How the script is laid out
- Shared parts: `torsoParts`, `packParts`, `legParts` (taken from the knight), `armParts`, `gripHand`, `pauldronParts`, `coreParts`, `humanoid(o)` (width, limb bulk, leg spacing, pack size, cloth colour, arm pose).
- `buildKnight`, `buildMage`, `buildRogue`, `buildBeast`: one function per character. A fifth two-legged character is a new `humanoid({...})` call plus its own helmet and props.
- Engraving: `engrave()` makes a colour map and a normal map from a drawn height picture; both export to GLB.
- Knight mask: `maskZ` (surface), `maskF` (outline and holes), built by marching squares.
- Rogue mask and dragon head: the general `shell(parent, bounds, NX, NY, posFn, ff, material, name)` helper plus `engravedMaterial()`.
- `zoom.py`: close-up captures of the rogue head (`rogue_head_zoom.png`). `beast_head_zoom.png` is a three-angle close-up of the dragon head.

## The four characters
- Knight (about 51,000 triangles): Maximilian fluted plate, sculpted beast mask with scrollwork, greatsword planted in front, reactor pack.
- Mage (about 38,000): narrower plate, violet robe with engraved stole, high engraved collar, tall pointed helm with a glowing cross slit, crown of spikes and halo, emitter staff held in both hands.
- Rogue: light plate, sculpted raven mask (one shell: hooked beak, brow, slanted glowing eye slits, engraved feather strokes) in dark steel, deep red hood with a rolled edge drawn back to a hanging point, cloth mantle, half cape on one shoulder, scarf, bandolier of throwing knives, twin daggers in reverse grip, small pack.
- Beast: four-legged carnivore construct with a dragon head on a short neck (the long neck was rejected). The head follows the user's three dragon references in spirit (technique reference only, licence not stated; original design): broad deep wedge, heavy spiked brows, crown of swept-back horns, five-blade cheek frills, nasal and jaw spikes. The skull and lower jaw are sculpted shells with carved scales, brow ridges, slanted glowing eyes, nostrils, a serrated jaw edge, brass teeth and fangs, a glowing throat and tongue, two pairs of swept-back horns, cheek frills, a nose horn and crest fins. Body: fluted barrel chest, lamed waist, engraved shoulder and hip plates, clawed paws, reactor drum with exhaust stacks, segmented tail ending in a blade.

## Per-character look (batch 12)
The user said the armour was too similar across the four. Each character now has its own metal, trim, glow and fluting, set in the `LOOK` table near the end of `main.js` and applied by `applyLook()` before a character is built:
- Knight: bright fluted steel, brass trim, cyan glow.
- Mage: smooth (unfluted) midnight-blue plate, silver trim, violet glow.
- Rogue: matt blackened steel with fine shallow ribs, copper trim, red glow.
- Beast: crimson lacquer, black horns, gold trim, amber glow.

## Batch 13: own shapes per character, dragon body
- Mage (`style: 'sleeve'`): three stacked spaulder plates under a brass spire with a light, cloth upper sleeves, wide trumpet cuffs.
- Rogue (`style: 'bracer'`): faceted pointed shoulder plates with spikes, bare upper arms with one band, pointed elbows, slim bracers with two blades each, no thigh plates or knee fans, knee spikes, greave blades, soft split-toe boots (`rogueLeg` hides the knight parts and adds these).
- Knight keeps the domed pauldrons, bell cuffs, thigh plates, knee fans and plated feet.
- Beast: carved scales on every body plate (`body_scale_steel`), thicker legs splayed outward, spikes on elbows, hocks, shoulders and hips, four long claws per paw, taller black dorsal spines, a thicker and longer tail with a spike at each joint. No wings (user decision).
- Dragon eyes: large amber eyes with slit pupils on the forward slope under the brow. Lower jaw: less mirror-like metal so it shows crimson (pure metal facing the floor reflected only dark and read black). A light from below was also added for all characters.
- The klad skill was loaded at the user's request but not used.

## User decisions so far
- Realistic sci-fi mecha armour with a medieval feel; 3D preferred over pixel art for this style.
- Helmet: beastly, not limited to wolf, fangs optional; the vibe and sense of danger matter most.
- Rejected on the knight's hands: sphere, mitten bands, ring fingers, flat jointed plates (read as ball, sleeve, coils, claws). Current: closed fist of thick round fingers.
- Construct must be a carnivore, with a dragon head (the first hound-like head was rejected as weak, as was the rogue's first cone-beak head).

## Known weak points
- All four are assembled from lathes, spheres and rings; plates overlap but are not sculpted into each other.
- Mage helmet is still simple shapes, not a sculpted shell like the other three heads.
- Rogue: the hood is smooth cloth with no folds.
- Beast: the dragon eyes are large and round, which reads a little cartoonish; the legs are thicker but still simple tapered plates.
- Mage and rogue still share the knight's torso, hands and greaves; the mage also shares the knight's feet (mostly hidden by the robe).
- Rogue: the soft boots are small plain wedges.
- Engraving repeats four times round each plate; it pinches at the top of the pauldron domes.
- Not rigged, no animation. Phone frame rate is untested (fps readout is on the page).
- 24,000 to 51,000 triangles each is heavy for game characters.

## Next (only after approval)
1. Sculpted-shell helmet for the mage (same `shell()` helper the rogue mask and dragon head use).
2. Cut triangle counts for game use.
3. Render pixel sprites from the models.
