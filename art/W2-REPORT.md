# W2 report: palace surfaces A6-A12, A14-A20 and architecture B1-B11 (overnight 25 Nov 2026, owner asleep)

Branch ci-art-w2. Nothing is in the game: no change to index.html or tests/. All are samples waiting for the owner. A1-A4 (approved) and A13 (W1's bronze) were not changed. They are only used as materials.
Method (cocolito): build, then gates, then shots at the game camera, then an honest verdict against GDD G1-G6 and the palace study. No ComfyUI round was run: every form here is architecture taken from the research rule list, so the form was clear.

## Files
- Textures: `art/tools/arch_tex.py` (imports `palace_tex.py`: Tex, band, cloud) paints 21 textures. Pipeline: `paint_palace.py` (klad, NAMES argument). PNGs in `assets/tex/` (1024 px = 4 m, 256 px/m). Sources in `art/src/<name>.klad`. Pass strips in `art/arch/round1/passes/`.
- Meshes: `art/tools/arch_blender.py` (bpy 5.3) writes `assets/models/arch/*.glb` (45 GLB files) and `art/arch/arch_report.json`.
- Viewer: `art/viewer/arch.html` (FOV 50, pitch 40, game lights, shadows, InstancedMesh for repeats, THREE.LOD for single props) and `art/tools/shoot_arch.mjs`. Sheets come from `art/tools/arch_sheets.py`.
- Sheets: `art/arch/round1/sheet_<room>.jpg` (hall, hall_burnt, hall_locked, court, corridor, garden, bridge, core), `pieces.jpg` (each piece alone) and `stats.json`.
- Checks: `art/tools/tex_check.py` (new rows plus new rules: value, seam, alpha test, matcap, mural ink, reddened, darker) and `art/tools/tex_check_mut.py` (mutation test). Mesh gates are inside `arch_blender.py`, with the mutation hook `ARCH_MUT=uv|budget|dims`.
- Runner: `ci_art/job.sh` rebuilds everything from source on a clean runner. The results are in ci-out `out/art/ci-art-w2/<run>/`.

Shared tools changed (lead, please check when merging):
- `paint_palace.py`: a background `none` gives a transparent export (alpha cards). Old textures behave the same: the approved rows still pass 25 of 25, and they were not repainted.
- `tex_check.py`: the new rows and rules only touch W2 names. An alpha card with no opaque pixel now prints FAIL instead of crashing.

## Gates (numbers)
- Textures: tex_check passes 165 of 165 (25 approved rows and 140 W2 rows). The mutation test catches 12 of 12.
- Meshes: arch_blender passes 100 of 100 gates (triangles, texel density on 95% of the surface in 205-320 px/m in both principal directions, CONFIG dimensions). Mesh-gate mutations: uv gives 28 FAIL lines, budget 27, dims 3. The gates are not blind.
- Room sheets (local swiftshader). Calls are the main pass plus one shadow call per caster (renderer.info counts the main pass only); 2 lights:

| Room | Max calls | Max triangles | Budget (500 calls / 0.5M tris) |
|---|---|---|---|
| hall (6 pillars, 3 slip racks, eaves, terrace) | 60 (62 locked) | 27.8k (28.3k locked) | PASS |
| court (forecourt 48 x 30, 阙 pair, wall-walk, flags) | 68 | 9.9k | PASS |
| corridor | 55 | 9.4k | PASS |
| garden (170 plant cards) | 41 | 3.0k | PASS |
| bridge (8 m bays, landings, debris) | 29 | 5.0k | PASS |
| core (throne, mercury) | 61 | 6.7k | PASS |

### Textures (W2 rows: brush run, lum sd, saturation, mean lum)
| Texture | Run | sd | Sat | Lum | Rules |
|---|---|---|---|---|---|
| A6 rammed_earth | 7.2 cm | 10.2 | 0.34 | 137 | 7 of 7 |
| A6 rammed_earth_core (5-6 cm layers) | 12.0 | 8.1 | 0.42 | 116 | 7 of 7 |
| B1 footing river_stone | 5.6 | 28.9 | 0.17 | 106 | 7 of 7 |
| A7 stone_paving | 11.2 | 11.3 | 0.09 | 137 | 7 of 7 |
| A8 floor_tiles (lozenge, 米 and square grid) | 4.0 | 9.2 | 0.10 | 112 | 7 of 7 |
| A9 hollow_brick (own dragon) | 5.5 | 13.8 | 0.10 | 124 | 7 of 7 |
| A10 mural_wall (plaster region; band ink 0.10) | 13.6 | 10.5 | 0.20 | 168 | 7 of 7 |
| A11 roof_tile | 7.7 | 8.4 | 0.02 | 78 | 7 of 7 |
| A11 tile_ends (disc faces) | n/a | 10.3 | 0.04 | - | 3 of 3 |
| A12 timber | 4.4 | 11.3 | 0.47 | 83 | 7 of 7 |
| A14 mercury_matcap (p95 202, the brightest) | n/a | 42.9 | 0.08 | 130 | 6 of 6 |
| A15 black_lake (green minus red 13) | 13.2 | 10.3 | 0.50 | 28 | 8 of 8 |
| A16 garden_ground | 9.1 | 8.5 | 0.34 | 106 | 7 of 7 |
| A16 garden_plants (alpha) | 4.5 | 25.9 | 0.44 | - | 6 of 6 |
| A17 star_ceiling | 13.1 | 14.9 | 0.21 | 29 | 7 of 7 |
| A18 timber_burnt / earth_burnt / wall_burnt | 4.9 / 9.4 / 12.1 | 11.9 / 8.7 / 21.5 | ≤ 0.51 | 38 / 96 / 76 | all pass |
| A19 signal_flags (alpha) | 8.6 | 29.3 | 0.22 | - | 6 of 6 |
| A20 slips / slips_burnt | 4.9 / 4.2 | 15.4 / 10.6 | ≤ 0.44 | 149 / 46 | all pass |

### Meshes (triangles against budget; texel density share)
| Piece | Triangles | Materials (= calls) | Notes |
|---|---|---|---|
| B1 terrace_edge (4 m, instanced) | 12 / 300 | 3 | 6.5 m stepped face; the river-stone footing goes into the lake |
| B2 wall_seg, wall_mural_seg, wall_earth_seg, wall_low | 22, 22, 12, 16 / 300 | 2-3 | 4 m high, 0.5 m thick; lacquer pilaster; low wall gets a tile cap |
| B3 door (frame, leaf L/R with pivots at the hinges, bar) | 196 in all | 5 | leaves 4.00 x 3.50 m; the `door_bar` node shows the locked state |
| B4 pillar | 282 / 300 | 3 | stone plinth and drum, shaft r 0.55, bronze 釭 sleeve under the painted capital |
| B5 eave_seg + tile_end (8 per segment, instanced) | 222 + 28 / 300 | 2 + 1 | straight eave, rafters, cover-tile ridges; no beasts, no glaze |
| B6 que_pair (paired 阙) | 1852 / 412 / 100 (7k / 2.5k / 800) | 9 | 14.2 m high, 8 m passage, 子阙 attached, flag on the gallery |
| B7 wall_walk_seg | 108 / 300 | 3 | earth wall on river stone, merlons, timber walk at 3 m |
| B8 parapet_seg, walk_post, walk_beam | 18, 72, 12 / 300 | 3, 4, 2 | hollow-brick parapet, covered walkway |
| B9 bridge_bay_8 / bridge_bay_12 | 194 / 208 / 300 | 1 | trestle bent per 4 m, posts to -6.6 m, rails 0.8 m |
| B10 throne_dais | 434 / 182 / 182 | 5 | 12 x 7 m, top at 2.8 m, couch, four-panel screen, balustrade |
| B11 lake_rubble, debris | 140 / 300; 484 / 88 / 88 | 1; 6 | debris spans -7.4 to -3.9 m (half sunk) |
| A16/A19/A20 dressing: plant cards x4, flag x9, flag_pole, slip_rack, slip_bundle | 8-88 | 1 | instanced |

## Verdicts (honest, from the sheets at the game camera)
| Item | Verdict | Why |
|---|---|---|
| A6 rammed earth | PARTIAL | Round 1 read as wood grain and round 2 as plywood. Round 3 (greyer, softer layers, pocks) reads as a layered earth terrace at the wide camera. Close up it is still more striped than real tamped earth. |
| A7 stone paving | PASS with note | Reads as dressed slabs. The 4 m repeat is visible across a 48 m court. |
| A8 floor tiles | PASS | The three stamp patterns read close up and as a grid at the wide camera. |
| A9 hollow brick | PASS with note | Round 2 made the dragons bolder. They read as creatures at play size, and as texture at the wide camera. |
| A10 mural | PASS | Chariot, guards, attendants and strange beasts read in the play shot; the band is small in the wide shot. |
| A11 roof tile + tile ends | PASS with note | Eaves read as grey tile with round ends. Every tile end shows disc 0, because the game needs a per-instance UV offset for variety. |
| A12 timber | PASS | Bridge, eaves and racks read as timber. |
| A14 mercury | PASS (round 3) | Rounds 1-2 read as white paint on screen. The round 3 chrome matcap on a rippled strip reads as liquid silver with glints. |
| A15 black lake | PASS | Near-black teal; it holds the rooms above it. |
| A16 garden | PARTIAL | Ground and plant cards read at play size. At the wide camera the planting is small and sparse, and the pond reads as a dark hole (black-lake material). |
| A17 star ceiling | NEEDS OWNER | The texture passes, but the game camera never sees a ceiling (no roofs are drawn). It is only seen in `core_up`. |
| A18 burnt swap | PASS with note | Walls (soot, spalled reddened earth), pillars and timber swap; floors stay. The burnt timber looks like a basket weave close up. Fire and smoke are effects (D), not W2. |
| A19 flags | PASS with note | Qin-black flags with an accent border and an invented sigil per school (shape first, colour second). The colour assignment is a proposal. |
| A20 slips and racks | PARTIAL for G1 | Racks and bundles exist and swap to burnt, but at the wide camera they are small and dark against the wall, so "burning of the books" does not read yet. |
| B1 terrace | PASS (round 2) | Round 1 faced inward, so it was invisible. Round 2 gives a stepped earth platform over the lake under every room (G5). There is no corner piece: runs meet at corners. |
| B2 walls / B3 door / B4 pillar / B5 eave | PASS | Read as Qin hall walls with pilasters, a lacquered door, a lacquer pillar with a stone base and bronze sleeve, and grey eaves. The locked bar shows at play size (round 2 moved it above the door masks). |
| B6 阙 | PASS with owner question | Reads as paired gate towers. Placement is the owner's question (below). |
| B7-B9 | PASS | Wall-walk with merlons, covered corridor, trestle bridge (no drawbridge). |
| B10 throne | PARTIAL | Reads as a stepped platform with a screen. At the wide camera the throne is small. There is no space marked yet for the tiger statue (a character, later). |
| B11 lake edge, debris | PASS with note | The debris pile sinks into the lake. It is static: the room-falling motion is D (effects). |
| G6 budget | PASS | Heaviest room: 68 calls, 28k triangles. |

## Rules I changed during the night (my own new rules, before any pass, with the reason)
- Seam: a pass now also allows an edge step up to the 99th-percentile line step, so drawn joints that fall on the edge (paving rows) are allowed. A real seam is still caught: the shear mutation is CAUGHT.
- Mercury "brightest": the rule was the mean, it is now the 95th percentile. The round 1 disc passed the mean rule and read as white paint on screen.
- Mural value range: 150-185, to match the approved A2 wall, which measures 169. The study's plaster plan (120-150) does not fit the approved wall (see Needs owner).
- Alpha cards: the rule now counts pixels that would vanish at the 0.5 alpha test, instead of all partial alpha (klad antialiases every edge).

## Open items
- KTX2 and the 512 px phone set are not made (texture step 3).
- Not integrated into the game (tonight's reading 2). The game would need CONFIG.TEX.files entries, PALUV for the new materials, and an instanced UV offset for tile ends.
- No corner pieces for terrace, eave or wall-walk.
- The pillar plinth is 1.5 m wide while the game's collision box is 1.2 m: the plinth sticks out 0.15 m.
- Shots are from a software GPU (look, counts and correctness only; no fps).

## Needs owner
1. A17 star-map ceiling: the camera never sees a ceiling. Options: put it on the core floor around the arena as an inlaid map, on the upper band of the core walls, or keep it for a cutscene.
2. B6 阙 placement: history puts the pair at the outer gate, which is on the camera side (south) of the forecourt. There, 14 m towers would block the view, so the sheet puts them on the north side. Choose: north side, outer gate with see-through, or a lower pair.
3. A19 school colours: proposed 儒 cinnabar, 道 lead white, 阴阳 grey/bone, 法 azurite, 名 Han purple, 墨 ochre, 纵横 silver, 杂 gold, 农 malachite (each with its own sigil).
4. Study value plan against the approved wall: A2 plaster measures mean lum 169, while the study says 120-150. Should the study be updated to the approved value?
5. B10 dais height: 2.8 m here, while the game's dais block is 1.5 m. Which height should the game use?
6. A16 pond: keep the black-lake water, or give garden ponds a lighter reflective water?
