# Techno-plate (sci-fi mecha armour with a medieval feel): study

Saved 2026-11-12 at the user's request. Status: proposal. The samples have been reviewed round by round but not formally approved, and nothing has been added to `Style-Library.md`.

- Reference: user's Pinterest and web screenshots (mecha design sheets, Chinese model-kit photos, museum plate armour, motorcycle armour, wolf-knight and demon masks, dragon heads). Several are franchise art. Licence: not stated. Technique reference only; all art here is original.
- Measured: nothing. The references are photos and paintings, not pixel art, so there was no grid, palette or frame size to measure.
- Not measurable, described: real Maximilian plate shapes (fluted breastplate, thigh and waist plates; bell gauntlet cuffs that open toward the elbow; narrow wrist; overlapping lames at every joint; rolled rims) carrying sci-fi parts placed where armour carries ornament (chest core, light strips, energy rings, reactor pack with exhaust stacks, cables, pistons). Heads are sculpted masks with glowing eye slits; the look aims for danger, not a specific animal.
- Nearest neighbour: none known in the library (not checked; `Style-Library.md` was not in this chat).
- Medium: 3D, built in code with Three.js r158 and exported as GLB. A first 64 px and 96 px pixel-art pass was tried and judged too weak for "realistic"; it is kept in `pixel-first-pass/` for the record.

## Values (from `3d/main.js`)
- Materials, shared: undersuit `#15171b` (matt), grip leather `#8a2f24`, cloth green `#2f4a33`, cloth violet `#3b2f63`, cloth red `#6b1f24`. Metals are metalness 1 with a procedural wear roughness map (wear 0.28).
- Per character (`LOOK` table):

| Character | Plate | Dark metal | Trim | Glow | Fluting |
|---|---|---|---|---|---|
| Knight | `#9aa3ad` bright steel | `#565e69` | `#b8923e` brass | `#5fe6f0` cyan | 26 flutes, depth 0.07 |
| Mage | `#2b3760` midnight blue | `#151b33` | `#dfe3ea` silver | `#b48cff` violet | none (smooth) |
| Rogue | `#2c2f34` blackened, matt | `#16181b` | `#b5673a` copper | `#ff4a3a` red | 44 fine ribs, depth 0.03 |
| Beast | `#8f1b1b` crimson lacquer | `#1e1a1a` | `#d4a544` gold | `#ffa62b` amber | 26 flutes, depth 0.07 |

- Proportions: two-legged characters are about 1.9 m tall in model units, roughly 7 heads. Width factor: knight 1.0, mage 0.86, rogue 0.78. Limb bulk: knight 1.0, mage 0.8, rogue 0.72.
- Light: one key light from upper front-left with soft shadows, two back fill lights, a hemisphere light, a light from below, and a studio environment map for reflections. Tone mapping ACES, exposure 1.0. Background `#7d838c`.
- Engraving: drawn as a height picture on a canvas, turned into a colour map plus a normal map (depth 3.2). Scrollwork on the knight's mask, a vine-and-lozenge border on plate rims, feather strokes on the rogue's mask, scales on the beast.
- Sculpted heads: one continuous shell from a height function, cut by marching squares over a signed field (outline, eye slits, mouth).
- Animation: none. Models are static and not rigged.

## Sizes
Not applicable as a pixel ladder. Triangles: knight about 51,000, mage 38,600, rogue 36,900, beast 42,800. GLB sizes 1.6 to 2.9 MB.

## Sample set
Knight, mage, rogue, and a four-legged dragon-headed carnivore construct, all in `3d/techno_plate_set.html` (buttons at the top switch character; Export GLB saves the one on screen).

## Draft library entry (proposal until approved)

## <N>. Techno-plate (3D sci-fi plate armour, medieval shapes), proposal
- Type: single
- Where: not used in a game yet
- Source: user's reference screenshots, licence not stated. Technique reference only; all art is original.
- Look: real plate-armour construction (flutes, lames, bell cuffs, rolled rims) with glowing tech set where armour carries ornament, and sculpted menacing masks. Differs from flat-cel mecha sheets by relying on metal reflections and overlapping plates, not line art.
- Palette: see the per-character table above; one glow colour per character; cloth is one colour per character.
- Grid, canvas, scale: 3D; one model unit is one metre.
- Proportions: about 7 heads; width and limb bulk per character as above.
- Outline and light: no outline; lighting as above.
- Animation: none yet.
- Sizes: not applicable (3D). Triangle counts above.
- Technique: `3d/main.js` builds every part from lathes, spheres, rings and sculpted shells; shared parts plus one build function per character; all tunables in the CONFIG block and the `LOOK` table. Rebuild and check steps are in `3d/HANDOFF-3D.md`.
- Samples (not yet approved): `3d/techno_plate_set.html`; `3d/techno_plate_knight.glb`, `_mage.glb`, `_rogue.glb`, `_beast.glb`; `3d/lineup_3d.png`; `3d/sheet_*.png`; head close-ups.
- Open: not rigged or animated; phone frame rate untested; heavy for game use; mage helmet not sculpted; parts still assembled from simple shapes; never checked on a real phone.
- Build notes: none yet.
