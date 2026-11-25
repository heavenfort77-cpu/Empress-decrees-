# Batch 17: assets into the game (INT, planning hour, 25 Nov 2026)

Owner order (25 Nov 04:4x): the (g) lag is fixed (d4a076c); NOW the assets go into the game; the real-size map comes after. Audio approved: wire src/audio/sound.js in. Attack VFX (painted cards) come in a later batch from the VFXP worker.
This is the plan only. No game code is written until the lead says go for 17a.
Every number below carries its run, file or measurement; anything else is marked GUESS or TARGET.

## 0. Readings (assumed, one line each; the lead corrects any)
1. "Assets go in" = every merged overnight round plus the FIXA/FIXB picks (art/ASSET-LIST.md A, B, C, G, H) goes in, each behind its own CONFIG switch. Screenshots from the exact build go to the owner per batch. Items still waiting on a pick go in as they are, flagged: A19 flags (contrast 30.5, parked), C12 fa/mo sigils.
2. The approved stone lion (A5, palLion) is replaced by the bronze beast C1 on the owner's word (24 Nov 21:03). The owner is told when the swap lands. The stone source stays in art/. A1-A4 (approved) are unchanged except PNG to KTX2, proven identical by measurement (17b).
3. The characters (suits, apex, cubs) are shared code, so their models show in Royal Rumble too. The Rumble map stays boxes (parked, no new work).
4. Collision stays on the simple box shapes. Models are render-only (rule 42). Hit areas change only where the owner said: tiger, cubs, giant sweep.
5. 华表 = decoration only: the marking hazard, its TEXT keys and check 804 are removed. That game change is on purpose, so 804 goes and 703/800 keep their counts. If the 17e perf gate shows any cost, the pillar is removed entirely.
6. Bronze = brass sheet (bronze_trim_brass) on every live bronze piece, patina sheet on dormant ones. The school colour mapping is W1a's pigment mapping everywhere: 鼎 accents, suit cloth, flags, standards. FIXA notes za and zh suit cloth are not yet on it; that is fixed in material tints, no re-render.

## 1. Baseline (before any change; numbers from runs)
- Real GPU (macOS runner, ANGLE Metal; runs 45363816937 / 45363877121, game 6c5642d):
  - palace_heavy medium: 210.4 / 203.5 fps, p95 11.3 / 11.8 ms, 24-28 calls, 1.6-1.9k tris.
  - Memory: programs 7, geometries 257, textures 1.
  - (g) fixed since then (45474454556: 0 frames > 100 ms on the fix arms).
- Suite 45474090100: 273 of 274; only 42 fails, a known balance item. Static PASS (12 perframe blocks, 275 text keys; local run today).
- 17b repeats this baseline in its own job, with a noise band (same build measured twice), before judging anything.

## 2. What goes in (measured from the files on batches-3-5 at 6612e01)
| Set | Files | Size now | LOD0 / LOD1 / LOD2 tris | Clips | Draw calls per copy (LOD0 primitives) |
|---|---|---|---|---|---|
| Suits x9 | assets/models/suits/*.glb | 0.65-0.86 MB each | ru 13,576 / 2,599 / 886 | attack, idle only | 3 |
| Tiger | apex/tiger.glb | 1.95 MB | 11,146 body + shed plates | dormant, wake, idle, pounce, roar | 5 materials |
| Cubs | apex/stalker, howler | 0.58 / 0.62 MB | 3,598 / 3,812 (FIXA: Howler 3,812 / 1,490 / 428) | idle, move, attack | 4 / 6 |
| Guard x5 | guard/*.glb | 0.41-0.48 MB | zu 3,400 / 1,186 / 332 | attack, idle, move | 3 |
| Rebels x4 | rebels/*.glb | 0.22-0.49 MB | ls 1,634 + one weapon per school | attack, idle, move | 2-3 |
| Giants | giants/giants.glb | 6.57 MB | body 3,640 / 1,504 / 606 + head 2.8-3.4k per giant | 8 | 3 materials |
| Props C1-C12 | assets/models/*.glb | 13 KB-0.84 MB | beast 6,988 / 2,422 / 674; 鼎 1,972 / 556 / 184 | beast idle/strike, clock countdown, 华表 watch (dropped), standard idle | 1-6 |
| Architecture B1-B11 | assets/models/arch/*.glb (35) | 0.53 MB together | wall_seg 22; throne_dais 434 / 182 / 182 | none | 1-9 |
| Textures | assets/tex/*.png (44) | 27 MB | 1024 px | | |

- Giants: 111k vertices in float32 (position, normal, uv, weights) = 6.3 MB. Clips are only 0.28 MB. So meshopt plus quantising fixes the size. No GLB embeds an image: materials are mapped by name to the sheets in assets/tex, so KTX2 applies to the sheets, not inside the GLBs.
- GPU memory, computed (not measured): 1024 px RGBA PNG with mips = 5.6 MB per texture, so about 37 palace textures = about 207 MB. KTX2 at 1 byte per pixel (BC7 / ASTC 4x4 / ETC2 RGBA) is about 1.4 MB each, about 52 MB. The 512 px phone set is about 13 MB.
- Art gap (Needs owner, art): the suits have only attack and idle clips. There is no walk, cast, hit or death clip, so a moving suit glides in idle. Options: an art round for walk plus hit (Blender worker), or glide for now.
- Not built today: lib/ has only three.module.min.js and three.core.min.js. We vendor the following from three r171 (MIT; the transcoder is Apache-2.0), with each added to CREDITS:
  - GLTFLoader.js
  - KTX2Loader.js
  - libs/meshopt_decoder.module.js
  - libs/basis/basis_transcoder.{js,wasm}
  - utils/SkeletonUtils.js
  - utils/BufferGeometryUtils.js
  - The phone link importmap gets the same paths on jsdelivr three@0.171.0.

## 3. The ONE loading plan (decided once; card times are TARGETS until 17b measures them)
| Moment | Waits for | Real work done there | Budget / cap | If late or failed |
|---|---|---|---|---|
| Page load to the mode menu | what it waits for today (three, the Rumble map, font warm-up, today's warm-up draws) | unchanged; no GLB or KTX2 | today's load (recorded in 17b) | as today |
| First tap (mode or school menu) | nothing | SND.unlock(); audio renders in its own order (tells, stingers, effects, loops; async, yields between sounds); fetch-only prefetch of the shared set (bytes, no decode) | none (background) | play() returns false until a sound is ready (silent, never an error) |
| Card P: mode = palace (first time in this page) | shared set + palace set | (1) fetch; (2) decode: meshopt; KTX2 in the transcoder worker; (3) build in a job queue at most CONFIG.LOAD.sliceMs (6 ms) per frame: materials from the name table, THREE.LOD objects, instanced and merged room pieces, pools filled (SkeletonUtils.clone per pooled unit here, never in play); (4) compileAsync per material group (KHR_parallel_shader_compile when present, printed); (5) renderer.initTexture for every texture; (6) one draw of every piece, pool member and state variant (lit/dry, cracked, burnt, dormant/awake) on the current tier under the opaque card; the card ledger counts draws, programs and textures | TARGET 4 s desktop, 8 s phone; cap CONFIG.LOAD.capS 15 / 25 s of visible time (the clock stops while the tab is hidden) | per asset: the box shape it has today (already built), logged in the ledger; never a blank or half-textured set (TEX rule kept: one set of a material family or none) |
| Card R: mode = Rumble | shared set | dispose the palace set if loaded (section 5); shared set kept | TARGET 1 s; cap 5 s | as above |
| New run, same mode | nothing new | reset() plus the per-set reset list (section 5); no card | 0 long frames (gate) | n/a |
| Apex wake / hunt | already in the shared set, compiled and drawn under card P or R | none | 0 programs built in play | n/a |
| Context restored | card "restore" | re-upload (initTexture all), compileAsync, warm draw (CPU copies of geometry and compressed mips are kept for this) | cap 10 s | as above |
| Tier change (auto step-down or setting) | short card "adjusting" | three.js releases unused programs, so both shadow variants cannot be kept warm. The recompile freeze happens under the card | measured in 17b; cap 3 s | n/a |

- Gates for every card:
  - (a) 0 shader programs and 0 new textures built during play after a card. The whole journey is counted with the first-draw ledger: programs, geometries and textures sampled once a second.
  - (b) No frame over 100 ms outside cards.
  - (c) The card's proof counts are printed: draws, programs, textures, ms per step.
  - (d) The warm-up is proven to have run (draws > 0 under the card), so a no-op warm-up fails.
- The card is one DOM element. Its text comes from TEXT keys (load_title, load_step_*), written only when the step changes; the spinner is CSS only. Nothing renders behind it except the warm draw.
- Hooks: __game.load() returns { phase, step, ms, draws, programs, textures, failed[] }. Checks wait on phase === 'done' with a large cap, never on the clock.

## 4. Formats and the encoder route (proved on a runner first: 17a)
- Textures: KTX2 Basis.
  - ETC1S for the albedo sheets and cards.
  - UASTC + zstd only where ETC1S fails the gate (flat gradients: floors, mercury matcap, water).
  - Desktop 1024 px; phone 512 px (resized from the source PNG before encoding).
  - The runner job installs KTX-Software (toktx, release .deb) and encodes. In headless Chromium it decodes with KTX2Loader + the basis transcoder, reads back pixels and compares with the PNG.
  - Gates: PSNR >= 35 dB and mean dE2000 <= 2 per texture; tex_check.py's metrics on the decoded image within its bands; alpha cards keep their alpha-test edge (pixels flipping across 0.5 <= 1%).
  - Each gate gets a mutant that must fail it: a quality-1 encode, a channel swap, a missing mip.
  - If toktx fails on the runner: the npm basis encoder (wasm) on the runner, the same gates. If both fail: PNG stays (today's route) and the owner hears it at once.
- Models: glTF-Transform on the runner: dedup, prune, quantise (position 14 bit, normal 10, uv 12, weights 8), meshopt compress.
  - Gates against the source GLB: triangle count equal per mesh; bounds within 2 mm; clip names and durations equal; joint count and names equal; skinned vertex positions at frame 0 and mid-clip within 2 mm (decoded in Chromium); size reported (giants 6.57 MB to TARGET under 1.5 MB).
  - Mutants: a decimated mesh, a dropped clip, a shifted bone.
- File layout:
  - Sources stay where they are (assets/models, assets/tex, art/src); the owner can reach them.
  - Encoded outputs go to assets/c/ (desktop) and assets/c/phone/ (textures). The game reads assets/c only.
  - A manifest (assets/c/manifest.json: file, bytes, hash, source hash) is checked by a test, so a stale encode fails.
- Fallback per file: the KTX2 file fails, then the PNG source; then the box colour. Each step is logged. The release test serves the zip with one file blocked (section 7).

## 5. Per-level load, keep and dispose (renderer.info.memory flat)
- Two sets:
  - Shared (suits, tiger, cubs, outline material, audio): loaded once, kept, never disposed.
  - Palace (architecture, props, guards, rebels, giants, palace textures): disposed when the player picks Royal Rumble. Rooms stay built once and kept while in palace mode (today's rule).
- Every created geometry, material, texture, mixer and pool object is registered in its set's list at build time. dispose(set) walks that list. Nothing is found by traversal. Shared items are never in a palace list (a check proves the lists do not overlap).
- What a rebuild used to reset is now reset explicitly on a new run. Each item below gets a check: N runs plus a new run in the same page.
  - mixer time and clip (dormant pose for giants and the tiger);
  - LOD levels;
  - burnt material swaps back to fresh;
  - 鼎 lit / dry;
  - vat intact, shards hidden and parked;
  - clock water level;
  - tread UV offsets;
  - pool members hidden, out of the scene graph (idle pooled items leave the graph so matrix updates skip them);
  - outline uniforms;
  - shadow needsUpdate.
- Gate: renderer.info.memory geometries and textures, the program count and the JS heap equal after cycle 1 and after cycle N. A cycle is palace run, Rumble, palace, new run x3, over 5 cycles. Mutation-tested: skipping one dispose must fail it.
- The real-size map (150 rooms, after this batch): room pieces use one InstancedMesh per piece type per room, sharing geometry, so GPU memory grows with instances, not with copies. This is a design choice now, so the map step needs no rebuild.

## 6. Scene building (render-only; boxes stay for collision)
- One material table, CONFIG.MATS (material name in the GLBs -> texture key, metalness, roughness, tint, phone texture), with a comment line per entry.
  - Very dark surfaces are matte. Vertex colours are linear.
  - Standard materials on props. No zero-intensity lights.
  - Lights stay 2-3 real; lamps (C9) are emissive cards only.
- Fog of war: every new material gets addFow (one shared program key 'fow1'). Skinned and instanced variants each add one program per material family; the count is reported.
- Rooms (17d):
  - Repeats (pillars, wall and walk segments, tile ends, parapets, bridge bents, plants) become one InstancedMesh per piece per room, with static matrices frozen (matrixAutoUpdate false).
  - Unique per-room shells are merged per material at card time (BufferGeometryUtils.mergeGeometries, time-sliced).
  - Star map = core floor inlay (FIXB). Dais model at 1.5 m to match the game block. Burnt wings are material swaps (A18), no new meshes. Small props castShadow off.
- THREE.LOD for single props and characters. CONFIG.LOD distances in metres, each with a comment giving its on-screen height.
  - Lens: vertical FOV 50 at 1080p, so the focal length is 1158 px and height in px = h x 1158 / d.
  - TARGET switch points: LOD0 while the object is over 200 px tall, LOD2 under 70 px.
    - suit (2.4 m): 14 / 40 m
    - guard (about 1.8 m): 10 / 30 m
    - beast (about 2 m): 12 / 33 m
    - giant (about 5 m): 29 / 83 m
  - Phone: distances x CONFIG.LOD.phoneK 0.6.
  - The camera floor keeps the player at 120 px or more (PAL_CAM.minPx), so the switch points are judged on side-by-side shots at play size before they are fixed.
- Never frustumCulled = false. Skinned meshes get enlarged bounding spheres, set once at build.
- Treads (ASSET-LIST H): map.offset.x += metres moved / mpr per unit. mpr per kit: Stalker 0.554, Howler 0.477, zu/nu/dun 0.540, che 0.527, wz 0.594. Instanced units carry the offset as an instanced attribute, not as a material per unit.

## 7. Characters
- Suits (17f):
  - One SkinnedMesh per suit (9 pooled, cloned under card P/R), cloth tint from the school mapping.
  - Owner pick: 2 px outline. Built as a screen-space inverted hull: back faces pushed out along the normal in clip space by 2 px x pixel ratio, drawn with the same skeleton. It costs +1 draw call per suit material and no full-screen pass. A post-process outline would add a full-resolution pass (fill cost on phones), so it is not used unless the look differs; the look is judged on screenshots.
  - The outline width uniform is updated on resize and tier change only.
- Guards and rebels (17g; up to 37 units in palace_heavy):
  - Route decided by measurement in 17a, on the macOS runner, against the reference in the same job.
  - Arm A: per-unit SkinnedMesh pool (cloned under the card; mixers only on visible units; far units at CONFIG.ANIM.farHz 10).
  - Arm B: one InstancedMesh per type x LOD x material, with clips baked into a bone texture (per-instance clip and time attributes).
  - LOD2 is a static pose for both.
  - Pick B only if A misses a gate (fps vs the reference, p95, calls under 500 with shadows, the matrix node count). A is simpler and keeps exact clips.
- Tiger and cubs (17h): models plus clips. Hit areas fitted to the models (owner 02:2x): capsules along facing, from the measured bounds.
  - Tiger: 1.5 x 4.9 m, so r 0.75, half-length 1.7 (was r 0.9).
  - Stalker: 1.93 m long, r 0.45 (was 0.5); Howler from its bounds.
  - Tells keep their shapes. Check 42 (hunt sweep) is re-run and reported; nothing is tuned (owner: balance later).
- Giants (17h): compressed GLB, shared body, 12 heads.
  - Dormant giants are instanced statics at LOD1/2. Awake giants (2-3) are skinned.
  - Sweep becomes an arc fitted to the beam. Owner picks the radius within his "about 2.2-3 m": default proposal 3.0 m, 150 deg; the tell sector is drawn from the same CONFIG value.
  - Checks bp09 sweep lines update on purpose (game changed on purpose; the sweep check keeps "hits only inside the shown shape").
- Animation rules:
  - Mixers update in the drawing pass from the clamped frame dt and stop when paused.
  - Gameplay timing (hit frames) comes from the fixed-step timers, never from clip events, so 30 and 60 fps play the same.
  - Off-screen units do not animate.

## 8. Audio (17c)
- Wiring:
  - `import * as SND from './src/audio/sound.js'`.
  - SND.init once at boot (profile from pointer: coarse). unlock() in the mode and school menu handlers.
  - setListener per frame in PERFRAME (camera focus). setIntensity and setAmb only on change, using AUDIO.md's proposed mapping (in CONFIG.SND with comments).
  - pause() / resume() on G.paused, hidden tab, end screens and menus.
- One home per behaviour: every game event in AUDIO.md's tables goes through one dispatcher, fxEvent(kind, x, z, dirX, dirZ). Today it calls SND.play. The VFXP painted-card pool attaches there later, with no second set of call sites. That is the only VFX hook.
- Stingers: a CONFIG map from her TEXT voice keys to stinger names (AUDIO.md table). Sound mode: a 44 px button on the mode and school menus and key B in play (M stays the debug overview). New TEXT keys snd_mode_*.
- Gates:
  - every sound name the game uses exists in SOUNDS (check; mutant: one wrong name);
  - static-check also scans src/audio/sound.js's PERFRAME block (a stricter check, nothing loosened);
  - no audio node is created per event except the one-shot source;
  - audio is suspended while paused or hidden (status().ctx);
  - perf unchanged within the noise band.

## 9. Budget forecast for the heaviest room (GUESS until 17d-17h measure it; shadow-pass calls and tris count in renderer.info)
- Calls:
  - architecture 68 (W2 room sheet, art only)
  - 4 suits x 3, plus outline: 24
  - giants 6 x 4: 24
  - guards and rebels: Arm A 37 x 3 = 111, Arm B about 30
  - props about 40
  - shadow-pass casters roughly double the casters
  - Total about 300-400 with Arm A: under 500, but close.
- Triangles:
  - suits at LOD0: 54k (plus the hull 54k)
  - guards at LOD1: about 44k
  - giants: about 42k
  - architecture: 28k
  - plus the shadow pass
  - Total about 300-450k: close to 0.5M.
- Levers, in order (look unchanged first): characters cast shadows from LOD1/LOD2 geometry; small props castShadow off; guards at LOD1 beyond 10 m; outline on LOD1 geometry. Then owner options with the measured gain each.

## 10. Premortem (each item: guard in the game plus a check, in the batch that touches it)
| Risk | Guard | Check |
|---|---|---|
| Context lost and restored (title, mid-card, palace play, heavy fight) | restore card (section 3); CPU copies kept | WEBGL_lose_context in CI at each point: frame drawn, calls > 0, texture count equal, no page error |
| Tier change mid-game (auto step-down, setting) | applyTier marks every registered material needsUpdate; "adjusting" card | step-down forced in heavy play: no frame > 100 ms outside the card, programs settle |
| New run in the same page | per-set reset list (section 5) | 3 new runs plus mode switches; pose, pool, LOD and swap state equal to a fresh page |
| Old saves | keys unchanged (empressDecrees.mode, the school pick, empressDecrees.audio); every read in try/catch | load with stored values from 6612e01 and garbage values: no error, defaults used |
| Long soak, memory flat | sets registered; pools; no per-frame allocation (static check) | 20 min soak with a mode switch every 2 min: heap and renderer.info flat after cycle 1 |
| Resize and orientation | renderer size, outline px, LOD bias on change only | resize and rotate mid-card and in play: no error, outline uniform updated once |
| Tab hidden mid-load | card cap counts visible time; queue resumes; audio suspended | hide at each card step, show: the card finishes, ledger complete |
| First sound before ready | play() returns false | play every event at t = 0 after unlock: no error, false counted |
| Checks waiting on the clock | __game.load(); conditions with caps | grep in tests: no fixed sleep before load-dependent asserts |
| A file blocked or slow (release) | retry once, then PNG or box fallback | release zip served statically under a subpath, one .ktx2 and one .glb blocked: playable, ledger lists both |
| Warm-up that does nothing | ledger draws and programs under the card | mutant: skip the warm draw, so the gate (0 programs in play) must fail |
| Programs explode (skinned x instanced x fog x shadow variants) | one feature set per family | programs counted per card; first-draw ledger 0 in play |
| Matrix pass grows (GLB node trees, bones) | static props matrixAutoUpdate false; idle pools out of the graph | per-frame matrix node counter behind ?perf=1, gated against a CONFIG cap |

## 11. Batches (one scope each; back up index.html outside the repo first; HANDOFF at the end of each; static check locally; full suite and mutation rounds on ci-run; real-GPU on ci-perf against the reference in the same job)
| Batch | Scope | Gate (all must pass) |
|---|---|---|
| 17a | Route proofs, no game code. Runner jobs: KTX2 encode/decode round trip (desktop and phone sets); meshopt/quantise of every GLB (giants included); capability probe (KHR_parallel_shader_compile, BC7/ASTC/ETC2 on the Mac runner and SwiftShader); guard Arm A vs Arm B probe page with 37 units on the Mac runner. Outputs: assets/c + manifest | texture and model gates N of N, mutants all caught, A/B numbers vs the reference in one job, route decision written |
| 17b | Loader and cards in index.html: vendored libs plus CREDITS, CONFIG.LOAD / MATS / LOD, card DOM and TEXT keys, job queue, sets and dispose, ledger hooks, restore and adjusting cards; the 4 approved palace textures move PNG to KTX2 (look identical) | suite 273+ of 274+ (only 42); new checks (ledger, 0 programs in play, memory flat over 5 cycles, fallback with a blocked file, context loss, tier change, hidden tab, old saves) mutation-tested; perf within the noise band of the baseline; screenshot dE vs PNG <= 2 |
| 17c | Audio wiring through fxEvent | section 8 gates; suite; perf within the noise band |
| 17d | Architecture and surfaces per room (B1-B11, A6-A20), instancing/merging, LOD, inlay, dais 1.5 m, burnt swaps | heaviest room calls/tris vs the budget on medium and low; 0 programs in play; memory flat; side-by-side shots at play size |
| 17e | Props C1-C12 (beast replaces the stone lion: owner told), 鼎 lit/dry, vat states, clock level, smoke cards, lamps as cards, 华表 decoration (hazard, TEXT keys, check 804 removed) | perf gate; the 华表 cost measured (any cost means removed); checks 703/800 green; tells still >= 0.4 s and drawn = hit shape |
| 17f | Suits: 9 models, school tints, 2 px outline | outline cost measured; floor contrast >= 3:1 on screen (W3's failing gate re-measured with the outline); perf gate |
| 17g | Guards and rebels by the 17a route; treads scroll | 37-unit heavy scene vs the reference: fps, p95, calls, tris, matrix nodes; pool reset over N runs |
| 17h | Tiger, cubs, giants (compressed); fitted hit areas; sweep arc | hit-area checks (hit at the model edge, miss 0.3 m beside it); sweep only inside the drawn arc; 42 re-run and reported; fairness invariants (tell >= 0.4 s) |
| 17i | Close-out: whole journey on the Mac runner (page load, menus, card P, every room type, heavy fight, apex, end, new run, Rumble switch, returning player) on medium and low, twice; full suite; soak; release zip with a blocked file; phone link republish; HANDOFF; shots from the exact build for the owner | 0 FAIL lines in every log; verdict SHIP / SHIP WITH NOTES / NO-SHIP |

## 12. Owner answers (25 Nov, go for 17a-17i in order; each batch passes its gate before the next; report to the lead after each)
1. Giant sweep hit area = 2.5 m radius over 120 deg in front of the giant (CONFIG comment with the date). Replaces the 3.0 m / 150 deg default above.
2. Suit walk/hit/death clips: an art round runs on a separate branch; 17f waits for its GLBs (the lead says when). 17a-17e go first.
3. Sound: no hotkey ("follow lol or dota"). Sound lives in an options/pause menu (Esc) as in LoL/Dota: master, music, effects, voice/ambience sliders plus mute, saved in try/catch storage, 44 px targets on phone. Key B dropped (section 8 changes accordingly).
4. Section 0 readings confirmed: new art behind switches; suits also in Royal Rumble.
5. Tell the owner when the bronze beast replaces the approved stone lion (17e).

## 13. Batch 17a results (25 Nov; route proofs, no game code)
- Encoder route: KTX-Software toktx 4.3 on the art runner (release .deb by fixed URL; the GitHub API answered 403 on the runner). glTF-Transform 4.5.1 meshopt (position 14, normal 10, texcoord 14 bits (it skips UVs outside 0-1), weights 16).
- Final gates: run 45523438520, 15 of 15, a re-check of round 3's exact files (run 45516776477).
  - T1: 228 of 228 encodes load.
  - T2: desk 38 of 38 within PSNR >= 35 dB and dE2000 <= 2.
  - T3: phone 38 of 38. phone/garden_plants ships as its 512 px PNG because no KTX2 mode kept it within the gate (ETC1S 26.8 dB, UASTC 31.8, UASTC q4 32.0; dE 1.04-1.32).
  - T4: alpha flips at most 0.26 %.
  - T5: no new tex_check rule fails on any pick.
  - T6: 75 of 75 KTX2 picks load through KTX2Loader with full mips (SwiftShader picks BC7 and ASTC).
  - Models M1-M7: 60 of 60 files. Worst vertex 1.54 mm in any pose; worst UV 0.00004.
  - Mutants caught: textures 5 of 5 by their named gate; models 3 of 3.
  - The quality-1 ETC1S mutant on hall_floor is NOT caught: 38.8 dB, dE 1.83, against 40.3 dB, dE 1.73 at quality 255. The gates cannot tell those two apart on that texture; reported, not hidden.
- Picks:
  - 28 textures ETC1S, 47 UASTC, 1 PNG.
  - UASTC wherever ETC1S broke a tex_check rule (brush runs and seams) or the PSNR/dE gate.
  - Sizes: desk 16.8 MB, phone 5.55 MB, against 27.8 MB of PNG. Models 22.72 MB to 6.19 MB without the suits; giants 6.57 MB to 2.24 MB.
- Orientation: KTX2 rows are top-first (glTF convention). The palace materials mapped by world UVs (palFloor, palWall, palPillar, palDoor, palLion) flip v by texture repeat.y = -1, offset.y = 1 (17b). The PNG fallback is loaded top-first as well, so both routes map the same.
- Files: assets/c/desk, assets/c/phone, assets/c/models.
  - assets/c/manifest.json holds bytes, sha256, source and source sha256 for each file. A stale encode will fail a 17b check.
  - Tools in art/tools/int17/: prep, encode, check page and driver, metrics, mutants, assemble.
  - Suits are left out: SUITANIM (64b7bd5) changed their sources, so they are encoded in 17f with these tools.
- Capabilities (macOS runner, run 45514003926): KHR_parallel_shader_compile yes; KTX2 targets ASTC, BC7, ETC2, S3TC. SwiftShader: no parallel compile.
- Guards and rebels: Arm B is chosen, by measurement on the macOS runner (run 45514003926, 37 units, reference in the same job, two passes):

  | Arm | fps | p95 (ms) | calls | tris |
  |---|---|---|---|---|
  | Reference | 205.2 / 163.4 | 12.1 / 17.7 | | |
  | A0 (per-unit skinned clones) | 64.1 / 59.8 | 33.1 / 36.3 | 105 | 105.9k |
  | B0 (baked bone texture, one InstancedMesh per type and material) | 189.5 / 155.3 | 12.1 / 17.8 | 23 | 105.9k (same geometry) |
  | Alod (skinned within 20 m, else the art's static LOD1) | 141.4 | 15.3 | 45 | |

  - Cause of A0's cost: SkeletonUtils.clone gives every primitive its own skeleton. That makes 105 bone textures uploaded per frame, plus 37 mixers and 705 scene nodes against B0's 27.
  - Arm A misses the gate (p95 2x the reference). B0 matches the reference within its spread.
  - The guard and rebel art has static LOD1 and LOD2 (only LOD0 is skinned), so B0's baked clips carry the animation.
- Note for suits, tiger and giants (17f/17h): a per-unit skinned clone must share one skeleton across its primitives (one bone texture per unit), and the cost is measured in that batch.
