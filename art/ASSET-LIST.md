# Burning Palace: asset list (palace and props)

Written 24 Nov 2026 22:0x with the cocolito method. Scope: the palace and its props only. Characters (suits, 皇家 guard, 反贼, apex, cubs) wait until their models are decided (owner 24 Nov 17:01).
Style: "Qin Palace Painted" (art/Qin-Palace-Painted-Study.md); round 2 textures approved by the owner 24 Nov 21:03. Rules from docs/research/Qin-palace-medieval-tech-fusion.md (one-page rule list at the end).

## Source order (owner 24 Nov 22:01)
The GDD decides what exists and what it must do (docs/GDD.md, docs/BURNING-PALACE.md); the research (docs/research/, reports/) is reference only for how it looks. Each item below names its GDD line.

## What the GDD asks of the palace
- G1 The burning is her burning of the books; the courts are the nine schools' halls, which burn wave by wave and collapse for good (GDD Lore, "The burning"). So each school hall must read as that school's, and the burning must read as books and halls burning (A18, A20, C12).
- G2 The core hall is never destroyed: Kaymuse's throne on a high dais, out of reach, with the tiger statue (the apex, the tiger tally made beast) crouched under it; its floor is the apex arena (GDD Lore and Palace arena). Throne and dais are B10; the tiger statue is a character and waits for the character models (owner 24 Nov 17:01).
- G3 Every hazard piece hits every side and shows a tell of at least 0.4 s (BURNING-PALACE "Palace pieces"): the look must carry the tell (C1, C3, C5, C6, C7, C8).
- G4 Decree states change how pieces look: dry altars look empty (the 鼎 needs a lit and a dry state), the no-dash zone is tinted gold, bridges silence skills (GDD decrees).
- G5 The palace stands over the black lake of the Qin water virtue; fallen rooms drop into it (BURNING-PALACE "The palace").
- G6 Budget: instancing, merged static props, 2-3 lights, under 500 calls and 0.5M triangles (GDD Palace arena, Perf).

## Rules every asset follows
- Look: Qin first. Black lacquer, cinnabar accents, red 丹 floors, lime plaster, rammed earth, grey unglazed tile, fresh brass-gold bronze on live pieces, verdigris only on dormant or sunk ones, gold or silver inlay as panel lines. No glazed roofs, roof beasts, brick walls, neon or readable calligraphy.
- Bronze pieces are segmented castings: mould seams, flanges, stamp bands from one trim sheet, a workshop mark per plate.
- Textures: klad-painted albedo, 256 px per metre on desktop and 128 on phone, brush runs 4-15 cm, luminance sd 8-30, saturation cap 0.55 (0.6 accents), 1024 max (512 phone), KTX2 when step 3 lands, anisotropy 4 max. Checked by art/tools/tex_check.py.
- Meshes and textures: own designs only. Every model, scan, photo and texture found in research is a reference (proportion, silhouette, ornament layout, material colour), never copied 1:1 or shipped (owner 24 Nov 22:00). References with non-commercial licences are still only looked at, never traced (the DailyArt lion).
- Budget: heaviest room on tier medium under 500 draw calls and 0.5M triangles (today 24-30 calls, about 2k triangles); repeats instanced, static props merged per material, single props get THREE.LOD (2-3 levels, distances in CONFIG), dispose on leaving the palace. Very dark surfaces matte; vertex colours linear.
- One sample at play size per new asset, screenshot from the exact build, wait for the owner's approval. Never replace an approved asset without telling the owner; sources (.klad, .blend, scripts) kept in art/.

## Status key
APPROVED = owner approved. SAMPLE NEXT = the next one to make. TODO = needed, not started. RETIRE = replaced on the owner's word, kept in art/.

## A. Surfaces (textures and materials)
| # | Surface | Where | Status |
|---|---|---|---|
| A1 | Red 丹 hall floor | 10 school halls, core | APPROVED (round 2) |
| A2 | Lime plaster wall, lozenge frieze, Qin-black dado | hall and corridor walls | APPROVED (round 2) |
| A3 | Black lacquer pillar, vermilion bands, cloud scrolls | halls | APPROVED (round 2) |
| A4 | Black lacquer door, bronze bands, 铺首 masks | every door | APPROVED (round 2) |
| A5 | Grey stone lion | lions | RETIRE (owner 21:03: bronze beasts); file kept |
| A6 | Rammed earth 夯土 with 5-10 cm layer lines | terrace sides, court walls, core walls (5-6 cm layers) | TODO |
| A7 | Stone paving | courts, forecourt | TODO |
| A8 | Floor tiles, lozenge / 米 / square grid | corridors | TODO |
| A9 | Hollow-brick parapet with dragon pattern (own design) | corridor edges, stair treads | TODO |
| A10 | Mural band on white plaster (chariots, guards, attendants, strange animals; own drawing) | corridor walls | TODO |
| A11 | Grey roof tile and round cloud-pattern 瓦当 tile ends | eave edges seen from the camera | TODO |
| A12 | Timber (beams, trestle, posts) | bridges, eaves, gardens | TODO |
| A13 | Bronze trim sheet: stamp bands, inlay lines, workshop marks; fresh brass-gold and verdigris variants | every bronze prop | SAMPLE round 2 (24 Nov 22:5x): darker base (value 104), 6 cm inlay; tex_check 25 of 25; waiting for approval |
| A14 | Mercury: the only bright cool reflective surface (matcap) | mercury channels | TODO (today a flat colour) |
| A15 | Black lake, blue-green near-black | under the platform | TODO |
| A16 | Garden ground and sparse alpha-tested planting (wheat-ear motif) | 3 gardens | TODO |
| A17 | Star-map ceiling | core hall | TODO |
| A18 | Burnt variants: charred timber, reddened earth (material swap, no new meshes) | wings that burn | TODO |
| A19 | Signal flags (school accents) | courts, gates | TODO |
| A20 | Bamboo-slip (竹简) bundles and racks, own design, no readable text; burnt variant | each school hall (G1: the burning of the books) | TODO |

## B. Architecture meshes (box geometry today; replace per room type)
Room types in the plan: hall, court, corridor, garden, bridge, core. Walls 4 m high and 0.5 m thick, doors 4 x 3.5 m (CONFIG.PALACE).
| # | Piece | Where | Notes | Status |
|---|---|---|---|---|
| B1 | Stepped terrace edge (rammed earth, river-stone footing) | rim of every room over the lake | instanced segments | TODO |
| B2 | Wall segment with dado and frieze; low wall | all rooms | merged per room per material | box + approved textures |
| B3 | Door frame and leaf (opens, locks) | all doors | locked state needs a visible bar | box + approved texture |
| B4 | Pillar with stone base and bronze 釭 sleeve | halls | instanced | box + approved texture; base and sleeve TODO |
| B5 | Eave edge with tile ends (the camera sees no full roofs) | hall and corridor walls | instanced tile ends | TODO |
| B6 | 阙 gate towers, paired | forecourt / outer gate | single prop with LOD | TODO |
| B7 | Crenellated wall-walk | courts | instanced | TODO |
| B8 | Corridor parapet and covered walkway posts | 8 corridors | instanced | TODO |
| B9 | Timber trestle bridge (the "Milky Way" crossing), no drawbridge | 7 bridges | instanced bents | TODO |
| B10 | Throne and dais | core hall | single, LOD | TODO |
| B11 | Lake edge and fallen-room debris | lake | burnt wings sink into the lake | TODO |

## C. Props (gameplay pieces already built in code, box shapes today)
| # | Prop | In game | Look (research rule list) | Mesh budget, LOD | Status |
|---|---|---|---|---|---|
| C1 | Bronze guardian beast, a pair beside big doors | 石狮 hazard (0.6 s red ring, 3.5 m strike) | segmented bronze beast, silver inlay, own design; strike pose readable | 7k / 2.5k / 800 tris (palace study budget; was 3k / 1k / 300) | SAMPLE round 3 (25 Nov 00:0x): from ComfyUI concept 2130 (owner pick), 6932 / 2426 / 726 tris, gates 8 of 8, shots art/beast/round3/; study art/Qin-Bronze-Castings-Study.md; waiting for approval; not in the game yet |
| C2 | 鼎 cauldron, 9 (one per school hall, the 九鼎) | replaces the healing altar; lit and dry states (G4) | real Warring States proportions, deconstructed taotie; school accent inlay | 2k / 600 | TODO |
| C3 | 门海 water vat | breakable: floods, douses fire, knockback | cast bronze, stamp bands; intact, cracked, pooled shards | 1.5k / 500 | TODO |
| C4 | 铜鹤 crane and 香炉 censer | smoke clouds for hiding | cast bronze; smoke as few small cards | 1.5k / 500 each | TODO |
| C5 | 铜壶滴漏 water clock, one per wing | water level counts to the next burning | stacked bronze pots; animated water level | 1.5k / 500 | TODO |
| C6 | 华表 pillar with a watching beast | marks a passer for 5 s | bronze-banded timber or earth pillar, cloud-scroll trim; eye cue not neon | 1.5k / 500 | TODO |
| C7 | Mercury channel | damage between pulses, shimmer tell | channel lip in bronze, matcap mercury | flat, instanced | TODO |
| C8 | 十二金人 twelve bronze giants | killable mini-bosses, wake one per burnt wing | one shared body cast, 12 distinct heads, shoulder beams and weapon motifs; patina dormant, brass awake; needs a rig (movement-2d-3d skill) | about 15-20k with a low LOD | TODO (largest job) |
| C9 | Bronze lamps with mercury reflectors | halls, core | lights faked with emissive cards (2-3 real lights max) | 500 | TODO |
| C10 | Bell stand (编钟) | core approach, gives the giants context | bronze, instanced bells | 2k / 600 | TODO (optional) |
| C11 | Split tiger tally 虎符 | lore prop, core | inlaid lines, echoes the apex | 500 | TODO (optional) |
| C12 | School emblem standard, one per hall (school accent colour, own sigil, no readable calligraphy) | each school hall: tells which school's hall it is (G1) | lacquer pole, bronze finial, cloth alpha-tested | 300 + cloth card | TODO |

## D. Effects that change assets (no new meshes)
Burning wing (char swap A18, steady fire cards, smoke), room falling into the lake, vat flood, mercury pulse shimmer, giant waking (patina cracks to brass). All pooled and warmed under the loading card.

## E. Routes for making a mesh (pick per asset, say which in the sample hand-back)
1. Own Blender script (bpy venv, recreate: python3 -m venv /home/claude/bpyenv && /home/claude/bpyenv/bin/pip install bpy==5.3.0) with hard carved planes, then klad texture: works in this session (the lion-sample-01 dog-like lion showed the method needs hard planes).
2. Tripo: SKIPPED (owner 24 Nov 21:58: the API account has no credit).
3. References (Sketchfab models, museum scans and photos): looked at and measured for proportions, silhouette and ornament, then modelled our own way (route 1). Never copied 1:1, decimated or shipped (owner 24 Nov 22:00). List: reports/Sketchfab Qin palace assets.md (session disk; copied to docs/research/ when delivered).
4. Rigging without a GPU (owner 21:58: UniRig needs an NVIDIA card, find another way). Proven 24 Nov 22:1x in headless Blender, CPU only, art/tools/rig_test.py:
   - rigid segments: each cast bronze segment bound 100% to one bone, then joined into one mesh per material: 80 verts, 0 unweighted, GLB with a 1 s clip re-imported as 1 skinned mesh + 1 action: PASS. Fits every bronze piece (beasts, giants, water clock, vat lids), since the art direction makes them segmented castings.
   - Blender automatic weights (bone heat) on one smooth mesh: 980 verts, 0 unweighted, weights normalised, GLB re-imported: PASS. For cloth or soft parts.
   - Not proven, not offered: a free UniRig demo on Hugging Face (ZeroGPU Space) could be called from a runner; quota and output terms unchecked.
Checks for every mesh: triangle count against the budget above, texel density 256 px/m, LOD switch distances, screenshot at play size beside the box version, the perf gate in the heaviest room; rigged meshes also: 0 unweighted vertices, weights sum to 1, max 4 influences, clip length matches the timing table.

## F. Order
1. A13 bronze trim sheet, then C1 bronze guardian beast (one sample, wait for approval).
2. After approval: C2 鼎, C3 vat, C5 clock, C6 华表, C4 crane/censer (each one sample, approval).
3. A6-A12 surfaces with the texture step 3 work (KTX2, phone set, per-level loading), B pieces per room type.
4. C8 giants last among props (rig).
Open item (g) (a long frame in the heaviest room) is paused; the perf gate runs before and after each batch.
