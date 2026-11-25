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
| A6 | Rammed earth 夯土 with 5-10 cm layer lines | terrace sides, court walls, core walls (5-6 cm layers) | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; rammed earth round 2b: 10-30 cm uneven lifts, grey-ochre (round 1 read as planks); still horizontal bands |
| A7 | Stone paving | courts, forecourt | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; round 2: narrow slab ramp, block sd 1.8 (round 1 showed a 4 m grid); new 'repeat' gate |
| A8 | Floor tiles, lozenge / 米 / square grid | corridors | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A9 | Hollow-brick parapet with dragon pattern (own design) | corridor edges, stair treads | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A10 | Mural band on white plaster (chariots, guards, attendants, strange animals; own drawing) | corridor walls | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A11 | Grey roof tile and round cloud-pattern 瓦当 tile ends | eave edges seen from the camera | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A12 | Timber (beams, trestle, posts) | bridges, eaves, gardens | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A13 | Bronze trim sheet: stamp bands, inlay lines, workshop marks; fresh brass-gold and verdigris variants | every bronze prop | SAMPLE round 2 (24 Nov 22:5x): darker base (value 104), 6 cm inlay; tex_check 25 of 25; waiting for approval; brass variant bronze_trim_brass.png (25 Nov, W1a: mean lum 137, hue 41; on screen hue 32 lum 79 vs 29 / 65) for the owner to pick |
| A14 | Mercury: the only bright cool reflective surface (matcap) | mercury channels | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; matcap reads as liquid silver after 3 rounds |
| A15 | Black lake, blue-green near-black | under the platform | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A16 | Garden ground and sparse alpha-tested planting (wheat-ear motif) | 3 gardens | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; planting sparse, pond reads as a dark hole at the wide camera |
| A17 | Star-map ceiling | core hall | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; never seen at the game camera (no ceilings): placement is an owner question |
| A18 | Burnt variants: charred timber, reddened earth (material swap, no new meshes) | wings that burn | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game |
| A19 | Signal flags (school accents) | courts, gates | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; school colour mapping is a proposal |
| A20 | Bamboo-slip (竹简) bundles and racks, own design, no readable text; burnt variant | each school hall (G1: the burning of the books) | SAMPLE round 1-2 (25 Nov, W2 overnight; klad, 1024 px, 256 px/m; tex_check 173 of 173, run 45452899575); shots art/arch/round1-2/; waiting for approval; not in the game; racks too small to read as the burning of the books at the wide camera |

## B. Architecture meshes (box geometry today; replace per room type)
Room types in the plan: hall, court, corridor, garden, bridge, core. Walls 4 m high and 0.5 m thick, doors 4 x 3.5 m (CONFIG.PALACE).
| # | Piece | Where | Notes | Status |
|---|---|---|---|---|
| B1 | Stepped terrace edge (rammed earth, river-stone footing) | rim of every room over the lake | instanced segments | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B2 | Wall segment with dado and frieze; low wall | all rooms | merged per room per material | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B3 | Door frame and leaf (opens, locks) | all doors | locked state needs a visible bar | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game; locked state: separate bronze bar node |
| B4 | Pillar with stone base and bronze 釭 sleeve | halls | instanced | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B5 | Eave edge with tile ends (the camera sees no full roofs) | hall and corridor walls | instanced tile ends | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B6 | 阙 gate towers, paired | forecourt / outer gate | single prop with LOD | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game; pair 1852 / 412 / 100; placed north for now (owner: outer gate on the camera side would block the view) |
| B7 | Crenellated wall-walk | courts | instanced | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B8 | Corridor parapet and covered walkway posts | 8 corridors | instanced | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B9 | Timber trestle bridge (the "Milky Way" crossing), no drawbridge | 7 bridges | instanced bents | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game |
| B10 | Throne and dais | core hall | single, LOD | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game; throne 434 tris, small at the wide camera; dais 2.8 m vs game block 1.5 m (owner) |
| B11 | Lake edge and fallen-room debris | lake | burnt wings sink into the lake | SAMPLE round 1 (25 Nov, W2 overnight; Blender, 45 GLBs in assets/models/arch/; mesh gates 100 of 100; room sheets art/arch/round1/, heaviest room 68 calls / 28.3k tris); waiting for approval; not in the game; debris 484 tris |

## C. Props (gameplay pieces already built in code, box shapes today)
| # | Prop | In game | Look (research rule list) | Mesh budget, LOD | Status |
|---|---|---|---|---|---|
| C1 | Bronze guardian beast, a pair beside big doors | 石狮 hazard (0.6 s red ring, 3.5 m strike) | segmented bronze beast, silver inlay, own design; strike pose readable | 7k / 2.5k / 800 tris (palace study budget; was 3k / 1k / 300) | SAMPLE round 4 (25 Nov, W1a overnight): face from ComfyUI concept 3129 (round C; alternates 3120, 3111), flame-tongue mane, V brows, segment flanges, roundels, raised-claw windup; 6988 / 2422 / 708 tris, gates 9 of 9; brass sheet variant (bronze_trim_brass.png) proposed; shots art/beast/round4/; study 'Samples, round 4'; waiting for approval; not in the game |
| C2 | 鼎 cauldron, 9 (one per school hall, the 九鼎) | replaces the healing altar; lit and dry states (G4) | real Warring States proportions, deconstructed taotie; school accent inlay | 2k / 600 | SAMPLE round 1 (25 Nov, W1a overnight): lidless ding, mask band and flanges, hoof legs, handles; lit (coals, glow cards) and dry (ash crust) states; nine accents on one mesh (accent_check 10 of 10); 1972 / 556 / 188 tris, gates 11 of 11; shots art/ding/round1/; study '鼎 cauldron'; waiting for approval; not in the game |
| C3 | 门海 water vat | breakable: floods, douses fire, knockback | cast bronze, stamp bands; intact, cracked, pooled shards | 1.5k / 500 | SAMPLE round 1 (25 Nov, W1a overnight): bulging 鉴-style basin, flange rings, lozenge and cloud bands, mask-and-ring handles; water surface; crack tell (6 cm cracks, sprays); 11 pooled shard nodes and a puddle; body 1488 / 408 / 162 tris, gates 10 of 10; shots art/vat/round1/; study '门海 water vat'; waiting for approval; not in the game |
| C4 | 铜鹤 crane and 香炉 censer | smoke clouds for hiding | cast bronze; smoke as few small cards | 1.5k / 500 each | SAMPLE round 1 (25 Nov, W1b overnight): crane from ComfyUI concept 5103 (alt 5102, 5106; Qin tomb waterfowl as reference), profile pose, S-neck, open beak, long wing plates, inlay collar, cinnabar crown, cloud-band plinth, 3 smoke cards from the beak; 1362 / 417 / 161 tris, gates 10 of 10; censer from 5208 (alt 5205, 5202): 豆 form, openwork lid of cloud tongues over a dark dome, mask-and-ring handles, 4 smoke cards; 1234 / 462 / 160 tris, gates 9 of 9; klad smoke_card.png (card_check 14 of 14 with flame_card); shots art/crane/round1/, art/censer/round1/; study 'W1b props'; waiting for approval; not in the game |
| C5 | 铜壶滴漏 water clock, one per wing | water level counts to the next burning | stacked bronze pots; animated water level | 1.5k / 500 | SAMPLE round 1 (25 Nov, W1b overnight): concept 5305 (alt 5301, 5308); Qin/Han outflow clepsydra on a two-step stand: slotted pot (sight slot = invention, shows the water), sinking rod with gold graduations, dragon spout, catch basin; moving nodes clock_water / clock_arrow / clock_catch, clips countdown_*; 1412 (with nodes) / 438 / 153 tris, gates 11 of 11; shots art/clock/round1/; waiting for approval; not in the game |
| C6 | 华表 pillar with a watching beast | marks a passer for 5 s | bronze-banded timber or earth pillar, cloud-scroll trim; eye cue not neon | 1.5k / 500 | SAMPLE round 1 (25 Nov, W1b overnight): concept 5403 (alt 5405, 5408); lacquer column (A3 texture), three bronze 釭 sleeves with 6 cm inlay, cloud board, dew disc, seated maned beast; head node turns (clip watch: 22 deg dip, 35 deg turn in 0.5 s); eyes inlay material palEye (dark asleep, gold awake, no neon); 1284 / 428 / 144 tris, gates 10 of 10; shots art/huabiao/round1/; waiting for approval; not in the game |
| C7 | Mercury channel | damage between pulses, shimmer tell | channel lip in bronze, matcap mercury | flat, instanced | SAMPLE round 1 (25 Nov, W1b overnight): 1 m bronze lip with 6 cm inlay, end, post, 1 m mercury tiles (W2's matcap A14, shading normals tilted 38 deg to the camera: the matcap's top band is dark); 2 x 6 m demo 592 tris from 4 shared meshes, gates 9 of 9; warn tell weak in a still (needs motion in the game); shots art/merc/round1/; waiting for approval; not in the game |
| C8 | 十二金人 twelve bronze giants | killable mini-bosses, wake one per burnt wing | one shared body cast, 12 distinct heads, shoulder beams and weapon motifs; patina dormant, brass awake; needs a rig (movement-2d-3d skill) | about 15-20k with a low LOD | SAMPLE round 3 (25 Nov, W1c overnight): shared body and rig, 12 heads / beams / melted-weapon motifs; 6.6-7.8k / 2.8-3.0k / ~990 tris; gates 119 of 119 (run 45452564180); clips dormant, wake (12 flakes fall), carry, walk, slam, sweep, hit, fall; 4.6-5.1 m (game box, not the 11.5 m source); klad patina sheet bronze_trim_patina.png; all twelve share one squat body (owner to judge); motifs 02, 05, 07, 08 weak at play size; shots art/giants/round3/; waiting for approval; not in the game |
| C9 | Bronze lamps with mercury reflectors | halls, core | lights faked with emissive cards (2-3 real lights max) | 500 | SAMPLE round 1 (25 Nov, W1b overnight): Warring States tree lamp, five dishes, mercury reflectors (invention), 10 flame and halo cards (klad flame_card.png), no lights; 462 / 170 / 78 tris, gates 8 of 8; concept 6103 (alt 6107, 6102); shots art/lamp/round1/; waiting for approval; not in the game |
| C10 | Bell stand (编钟) | core approach, gives the giants context | bronze, instanced bells | 2k / 600 | SAMPLE round 1 (25 Nov, W1b overnight): lacquer frame on bronze beast feet, dragon-head caps, 11 bells on one shared mesh per LOD; drawn 1840 / 548 / 180 tris, gates 7 of 7; shots art/bells/round1/; waiting for approval; not in the game |
| C11 | Split tiger tally 虎符 | lore prop, core | inlaid lines, echoes the apex | 500 | NEEDS OWNER (25 Nov, W1b overnight): 2 rounds, gates 7 of 7 but the look fails: at 500 tris the two halves read as a faceted cat, not a tiger; raise the budget (about 1.5k, one core prop) or drop it; round 2 in art/tally/round2/, assets/models/tally.glb |
| C12 | School emblem standard, one per hall (school accent colour, own sigil, no readable calligraphy) | each school hall: tells which school's hall it is (G1) | lacquer pole, bronze finial, cloth alpha-tested | 300 + cloth card | SAMPLE round 3 (25 Nov, W6, ci-art-w6 c78fbd4, run 45464846183): owner 02:4x: za banner #b2bccb, fa sigil = Qin 权 steelyard weight, mo sigil = rammed-earth wall under a gate tower; other seven sigils approved; 224+24 / 94 / 40 tris, 3.84 m; gates atlas 49/49, build 18/18, GLB 13/13, play 11/11; mutations 20/20; lead look: fa may read as a bell, mo as a stepped gate house; shots art/standard/round3/; waiting for approval of the fa and mo sigils; not in the game |

## G. Characters (overnight 25 Nov; models only, none in the game)
| Set | Worker / branch | Status |
|---|---|---|
| Nine school suits 甲 | W3, ci-art-w3 a7e0b36 (merged) | 17 of 18 gates each; all fail floor contrast (red floor too dark: even black reaches 2.2:1 of 3:1); 6.4 heads tall vs concepts 7.5-8.5; suit_bronze brush 3.9 cm; waiting for the owner |
| Apex Tiger Demon, cubs Stalker and Howler | W4, ci-art-w4 4c45ba7 (merged) | tiger 15 of 15, cubs 21 of 21, tex 11 of 11, shots 43 of 43 (run 45447534120); tiger reads heavy and bear-like; Howler reads as a box on legs; bronze material and glow colour for the owner |
| 皇家 guard (卒, 弩手, 盾, 车, 伍长) and 反贼 rebels | W5/W5b, ci-art-w5 16618bd (merged) | guard round 5 gates 11/11/11/10/12, rebels 10/10/11/11 (run 45451027192); treads fixed; still compact and dark at the game camera; chariot canopy round |

## H. Fix round after the owner's 25 Nov 02:1x-02:4x picks (merged; nothing in the game)
| Item | Run | Result |
|---|---|---|
| Brass for every bronze piece (viewers) | FIXB 45467670225, FIXA 45471050221 | PASS: no shot loads the old bronze sheet |
| A19 flags in the owner's school mapping | FIXB 45467670225 | PARKED after 2 rounds: colours 9 of 9 match, contrast lum sd 30.5 vs max 30 (fix: BAND_W 6 to 5) |
| A2 plaster | FIXB | KEPT unchanged: a darker candidate failed brush scale and sat below the floor; study range now 150-185; candidate in art/arch/round3/plaster_candidate/ |
| Garden ponds lighter water | FIXB | PASS (9 of 9 texture, 2 of 2 on screen) |
| A17 star map as core floor inlay | FIXB | PASS; subtle at play, unseen at the wide camera |
| B10 dais 1.5 m; throne larger | FIXB | dais PASS; throne x1.34 on screen, still small at the wide camera |
| Bamboo-slip racks bigger | FIXB | PASS with note: screen share x5.5; 6 of 9 racks moved to the north wall |
| Garden planting fuller | FIXB | PASS: calls 41 to 41, tris 3.7k to 8.9k |
| C7 mercury brighter + shimmer | FIXB | PASS with notes: idle 140, warn 211, hot 236; tile seams show close up |
| C11 tiger tally ~1.5k | FIXB | PASS: 1468 tris, reads as a striped walking tiger |
| Howler reshaped | FIXA | PASS: lidded cauldron with horned head, water-blue throat core; 3812 / 1490 / 428 |
| Treads scroll (UV strip) | FIXA | PASS: game rule map.offset.x += metres / mpr (Stalker 0.554, Howler 0.477, zu/nu/dun 0.540, che 0.527, wz 0.594) |
| Chariot without canopy | FIXA | PASS |
| Giants slimmer, motifs 02/05/07/08 | FIXA (third run on one pose value: rule break, logged) | PASS with notes: still heavy from 40 deg; 05-11 closest pair IoU 0.78 |
| Rebels in non-school colours, larger 死士 glint | FIXA | PASS: olive, umber, madder; glint 0.62 m |
| Suits ~7.5 heads | FIXA | PASS: 7.51 heads; cloth colours not yet on the 鼎 mapping (za, zh) |

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

## Lead art review 25 Nov 11:0x (owner rule 10:46: would the lead ship it?)
Judged from the latest sheets at close-up and play size (boards in session disk /home/claude/audit/). FAIL = same problem as faces A-D (passes gates, does not look right).
| Asset | Verdict | Why |
|---|---|---|
| C1 guardian beast round 4 | FAIL | a Ming/Qing foo lion on a stone plinth: the look the owner retired 24 Nov 21:03 (stone lions are post-Qin; asked for a segmented bronze beast with silver inlay) |
| C8 twelve giants | FAIL (heads) | flat face plate on a round head (faces round 2 covers g00 only); heads near-identical at play size (05-11 IoU 0.78). Shared body = owner's choice, kept |
| C7 mercury channel | FAIL | reads as frosted glass/ice with a zigzag print, not liquid metal; idle/warn/hot look alike at play size |
| C11 tiger tally | FAIL | faceted lumpy cat on a black box at close-up |
| G suits | FAIL at play size | dark lumps on the red floor (outline fix = owner pick, in prep-chr); 6.4 heads tall vs concepts 7.5-8.5 reads toy-like; faces in faces round 2 |
| G guards / rebels | WEAK | small and dark at the game camera; rebels' beige melts into the floor; faces in faces round 2 |
| Cubs Stalker / Howler | WEAK | read as a box on legs and a turtle shell at play size |
| C2 ding, C3 vat, C4 crane/censer, C5 clock, C6 huabiao, C9 lamp, C10 bells, C12 standards, apex tiger, A1-A4 textures | PASS | read at play size, fit Qin/tech fusion |
| B rooms | NOTE | court and garden floors are large and empty at the wide camera; props arrive in 17d/17e, judge again in-game |
| Faces round 2 (zu, g00; run 45542918403, sheets out/art/faces-sample/45542918403/sheets/) | FAIL (lead 25 Nov 12:0x, not sent) | sculpted shells from SDXL concepts zu face_6204 / g00 face_6303; gates 33 of 36. g00 lacquer mask reads at play size (3.18:1, eyes 4.77:1) but close-up is smeared and the head stays tiny on the body; zu black visor on a featureless egg head, eyes 2.13:1. Cause: a mask cannot fix the head under it. Next: fold guard and giant heads into a full head/helmet rebuild once the suit fa rebuild proves the kit method |
