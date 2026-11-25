# Attack effects: painted cards (VFXP, 25 Nov)

Owner 25 Nov 04:4x: attack effects for ALL attacks in the PAINTED style (the approved 法 slash "B", ci-vfx, run 45467292518). pixelfx (MIT, (c) Patch) gives shape and timing only; every card is repainted as soft painted strokes with klad and only the PNGs ship. School colours = the owner's one mapping (W1a 鼎 pigments); apex glow water-blue; rebels olive / umber / madder; no neon, no readable calligraphy, generic motifs only.

Status: proposal. Not in the game: INT (the only index.html writer) wires it in. Nothing here changes index.html or tests/.

## How it works (one paragraph)
13 shared cards are painted once in grey values (0 = deep keyline, 0.5 = the pigment, 1 = pale core). The game looks the value up in a ramp row (one row per school, the apex, three rebel colours and five neutral rows), so one atlas serves every school and the atlases stay at three. Every attack and tell in the game (86 items, 40 of them tells) maps to those 13 cards (tables below).

## Files
- `assets/vfx/vfx_soft_a.png` 1024 x 956 (slash, impact, bolt, thrust), `vfx_soft_b.png` 1024 x 984 (burst, shield, aura, heal, smoke): blended (premultiplied alpha). Soft painted edges need it.
- `assets/vfx/vfx_ground.png` 1024 x 1020 (ring, mark, strip, crack): alpha-tested at 0.5 with alpha to coverage (MSAA is on in the game). Ground tells and cracks lie flat on the floor, need hard edges to read, and need no sorting.
- Atlas texels: R = value, G = alpha, B = 0, stored as opaque RGB PNGs and uploaded as RG8 (2 bytes per texel, linear filter, no mipmaps; the cards are magnified 3-5x at the play camera, so no minification happens). GPU: 1.87 + 1.92 + 1.99 MB, plus the ramp texture `vfx_ramps.png` (64 x 18, sRGB). Total 5.79 MB on the GPU (runner rows, run 45517911042).
- `assets/vfx/vfx.json` = everything the game needs (atlases, ramp rows and hex, per effect: atlas, blend, faces, frames, fps, tell loop, cell, origin, stride, columns, pivot, texel m, size m, pivot m, anchor height m, unit sizes, alpha per frame). `fx_<card>.json` = the same per card.
- `art/vfx/`: the generator (`gen_cards.py`, its round-1 copy `gen_cards_round1.py`), ramps (`ramps.py`), klad painting (`paint.sh`), packing (`pack.py`), contact sheets (`sheets.py`), gates (`checks.py`), the gate mutation round (`mutate.py`), the effect map (`vfx_map.py` -> `vfx_map.json`), these tables (`doc_tables.py`), the klad sources (`klad/<card>.klad`), the reference card system (`cards_reference.js`), and the peak-frame sheet of every card in every ramp row (`peaks_all_rows.jpg`).
- Branch ci-vfxp (CI only, never merged): the probe `probe/vfxp/index.html` + `cards.js`, `ci_vfxp/perfvfxp.mjs`, workflow `vfxp-run.yml`. Results go to ci-out `out/vfxp/<run>/` (perf.txt, rows.json, shots/ with 72 gallery shots, the B pair and the heavy fight).

Rebuild: build klad (klad-headless-cli skill; klad 0.4.0, 5c60e1d), then `KLAD=<klad> OUT=<work> art/vfx/paint.sh`, `python3 -I art/vfx/pack.py <work>/frames <work>/ops/families.json assets/vfx`, `python3 -I art/vfx/checks.py assets/vfx assets/tex/hall_floor.png art/vfx/vfx_map.json`. A repaint gives byte-identical atlases (checked: soft_a md5 before and after a repaint of thrust).

## The 13 cards
| Card | Atlas (draw) | Faces | Frames @ fps (s) | Tell loop | Size m (w x h) | Pivot m from left, bottom | Anchor m | pixelfx reference (shape, timing) |
|---|---|---|---|---|---|---|---|---|
| slash | soft_a (blend) | camera | 13 @ 30 (0.433) | - | 5.724 x 4.212 | 1.728, 0.135 | 0.0 | melee/sword-slash |
| impact | soft_a (blend) | camera | 10 @ 30 (0.333) | - | 2.88 x 2.88 | 1.44, 1.44 | 1.0 | impacts/hit-spark |
| bolt | soft_a (blend) | camera | 8 @ 24 (0.333) | [0, 8] | 4.08 x 1.8 | 3.24, 0.9 | 1.0 | projectiles/magic-missile |
| thrust | soft_a (blend) | camera | 12 @ 30 (0.4) | - | 4.32 x 1.2 (unitLenM 4.0) | 0.18, 0.6 | 1.1 | melee/thrust |
| shield | soft_b (blend) | camera | 12 @ 20 (0.6) | [4, 12] | 3.0 x 3.48 | 1.5, 0.54 | 0.0 | holy/divine-shield |
| aura | soft_b (blend) | camera | 12 @ 20 (0.6) | [0, 12] | 2.52 x 3.48 | 1.26, 0.6 | 0.0 | status/rage |
| heal | soft_b (blend) | camera | 12 @ 20 (0.6) | [0, 12] | 2.4 x 3.36 | 1.2, 0.42 | 0.0 | holy/heal |
| burst | soft_b (blend) | camera | 12 @ 30 (0.4) | - | 4.08 x 4.08 | 2.04, 2.04 | 1.0 | arcane/mana-burst |
| smoke | soft_b (blend) | camera | 12 @ 15 (0.8) | - | 3.76 x 3.36 | 1.88, 0.24 | 0.0 | explosions/smoke-bomb |
| strip | ground (cut) | ground | 10 @ 30 (0.333) | [3, 7] | 0.7 x 2.4 (unitLenM 2.35, unitWidthM 0.6) | 0.35, 0.025 | 0.0 | melee/thrust |
| ring | ground (cut) | ground | 10 @ 30 (0.333) | [3, 7] | 2.405 x 2.405 (unitRadiusM 1.0) | 1.202, 1.202 | 0.0 | arcane/magic-circle-cast |
| crack | ground (cut) | ground | 10 @ 20 (0.5) | - | 2.405 x 2.405 (unitRadiusM 1.0) | 1.202, 1.202 | 0.0 | impacts/ground-slam |
| mark | ground (cut) | ground | 10 @ 30 (0.333) | [3, 7] | 2.43 x 2.43 (unitRadiusM 1.0) | 1.215, 1.215 | 0.0 | holy/smite |

## Ramp rows (vfx_ramps.png; stops at value 0 / .25 / .5 / .75 / 1 = deep, dark, pigment, light, pale, mixed in OKLab toward #0e0b0a and #fffaf0)
| Row | Name | Pigment | Used by |
|---|---|---|---|
| 0 | ru | #b8862e | the ru suit (player or bot) |
| 1 | dao | #e2b84a | the dao suit (player or bot) |
| 2 | fa | #d9d2c3 | the fa suit (player or bot) |
| 3 | mo | #a8321e | the mo suit (player or bot) |
| 4 | yinyang | #1a1614 | the yinyang suit (player or bot) |
| 5 | za | #c8ccd0 | the za suit (player or bot) |
| 6 | ming | #5b3f8c | the ming suit (player or bot) |
| 7 | zongheng | #2f8a5c | the zongheng suit (player or bot) |
| 8 | nong | #2e5a9c | the nong suit (player or bot) |
| 9 | apex | #3a8fd0 | Tiger Demon, Stalker, Howler, cubs, plates |
| 10 | rebel_olive | #6f6a34 | 反贼 variant 0 |
| 11 | rebel_umber | #6a4a32 | 反贼 variant 1 |
| 12 | rebel_madder | #8e5a52 | 反贼 variant 2 |
| 13 | guard | #6e737a | 皇家 guard |
| 14 | bronze | #c9a050 | statue, guardian beasts, 十二金人 |
| 15 | jade | #5e9c7c | 鼎 / altar heal, boons |
| 16 | water | #2a6a9a | 门海 vats |
| 17 | ash | #8c8a86 | burning wings, dust |

## Tells (windups)
- A tell card plays its intro (3 frames, 0.1 s), then loops frames [3, 7) for exactly the move's windup (`hold` = the CONFIG windup, e.g. MOVES.claw.windup 0.45), then plays its release frames (7-9) and ends empty. So the tell is visible for the whole windup, never shorter; every windup in the map is >= 0.4 s (gate `map`).
- The tell card sits on top of the game's own tell shape (the coloured ring or strip the code draws today) and is sized from the same CONFIG numbers. INT decides whether the old flat tell mesh stays under it.
- Floor read: on the 丹 floor (relative luminance 0.08) no dark colour can reach 3:1, so every tell is a pale brush line (the ramp's pale stop, painted twice so it keeps its value) with a thin dark keyline outside it and the pigment inside. Gate `floor_read`: in every tell card x ramp row that uses it (48 pairs), at least 25% of the drawn pixels reach 3:1 against the floor under them (worst 0.29, smoke on ash). The school colour therefore shows mostly in the inner strokes of a tell and fully in the release and hit cards.
- The burning wing's 5 s warning uses smoke one-shots repeated every 0.6 s at the wing's doors (smoke is not a loop).

## Card system (spec for the game writer; reference code art/vfx/cards_reference.js, measured on ci-vfxp)
1. Load (under the loading card, with the other textures): fetch + createImageBitmap(blob, { premultiplyAlpha: 'none', colorSpaceConversion: 'none' }) per atlas (no <img>: it holds the page load event); THREE.Texture with format RGFormat, flipY false, generateMipmaps false, Linear min/mag, NoColorSpace. The ramp PNG: sRGB, Linear, no mipmaps. Then renderer.initTexture for all four and renderer.compile with the three card meshes in the scene (warm-up proven by "new programs during play = 0" in every runner row).
2. Pools, built once: one InstancedBufferGeometry (a unit quad, 4 vertices) + one ShaderMaterial + one Mesh per atlas, instanceCount fixed = the pool (soft_a 64, soft_b 48, ground 48 in the probe; the heavy fight peaked at 100 live, the 4x stress at 130, of 160). Three draw calls in all, whatever the number of live cards. Per instance three vec4 attributes (DynamicDrawUsage): iA = anchor x y z + start time; iB = hold end time, rotation, width m, height m; iC = card index, ramp row v, alpha, spare. Per card constants (atlas origin, cell, stride, columns, frames, pivot, fps, loop) are uniform vec4 arrays indexed by the card index (13 entries).
3. Vertex shader does the work: frame = floor((uTime - start) x fps); inside the hold it wraps in the tell loop; after the hold it plays the release frames; past the last frame (or alpha 0) the vertex is pushed outside the clip box, so a finished card costs four vertices and no fragments. Upright cards are offset in view space (always face the camera, rotation in the screen plane); ground cards are laid on the floor 2 cm up, yaw rot, forward = (sin rot, 0, -cos rot).
4. Fragment: va = texture(atlas).rg; colour = ramp(va.r, row) (fog mixed in before the output conversion); soft atlases output premultiplied (colour x a, a) with NormalBlending + premultipliedAlpha, depthWrite off, depthTest on, renderOrder 3; the ground atlas alpha-tests at 0.5 with alphaToCoverage (fwidth band), depthWrite on, polygonOffset -2, renderOrder 1. side DoubleSide (negative width mirrors a card).
5. spawn(name, x, y, z, row, sx, sy, rot, hold, alpha) writes one instance (no allocation; first free slot after a moving cursor, else the oldest) and calls addUpdateRange for those 12 floats. Sizes: upright sx = sy = scale (sx < 0 mirrors); ring / mark / crack sx = sy = radius / unitRadiusM; strip sx = width / unitWidthM, sy = length / unitLenM; thrust sx = range / unitLenM. Upright cards sit `cardFwd` 0.6 m toward the camera from their anchor so the swing draws in front of its own caster; the anchor height (vfx.json anchorHeightM: hit cards 1.0 m, thrust 1.1 m) is added by spawn.
6. Per frame: one uniform (uTime = game time, so pause freezes every card and dt 0 holds them); move(handle, x, y, z) only for cards that follow something (a bolt in flight, an aura or shield on a walking suit, 法's 势 ring); release(handle) when a tell ends early (stance broken, caster killed); kill(handle) for loops (auras, heals) when the state ends. Nothing else runs per frame: no traversal, no allocation, no DOM.
7. Culling stays on: each card geometry gets a bounding sphere round the current room (set on a room change), never frustumCulled = false. Dispose the three geometries, materials and four textures only when the palace is left for good (they are shared, keep-flagged otherwise). Context loss: the textures are re-uploaded by three; the pools keep their arrays.
8. Phone tier (dialled down from desktop): the same atlases (RG8 is already small); pool sizes halved; smoke and heal loops skipped on low; no other change needed.

## Gates (art/vfx/checks.py, local, light) and their mutation round
| Gate | What | Result (final assets) |
|---|---|---|
| atlases | at most 3, each side <= 1024, R value G alpha B empty | PASS: 3, 1024 x 956 / 984 / 1020 |
| cells | every frame inside its atlas, nothing cut at a cell border, gutters empty | PASS: 13 cards, 143 frames |
| json | 16 fields x 13 cards, fx_<card>.json present | PASS |
| timing | one-shots end empty (last frame <= 3% of the peak's alpha), tell loop frames >= 25% of the peak, intro <= 0.2 s | PASS |
| map | every item's cards and ramp row exist; every tell has windup >= 0.4 s and a looping (or repeated) card | PASS: 86 items, 40 tells |
| floor_read | tell cards >= 25% of pixels at 3:1 on the 丹 floor, every ramp row that uses them | PASS: 48 pairs, worst 0.29 |
| face | aura / heal / shield / smoke: alpha <= 0.5 inside the face box (x +-0.22 m, 1.5-1.95 m) | PASS |
Mutation round (art/vfx/mutate.py): 8 of 8 caught (blank loop frame, alpha on a cell border, windup 0.3, darkened tell, alpha on the face, smoke not ending empty, a missing fx json, a tell without a card).

## Real-GPU measurement (macOS runner, Apple M1 (Virtual), ANGLE Metal, 1920 x 1080, pixel ratio 1.25, vsync off; 6 s settle + 20 s timed per scene; scenes run forward then reversed in one job)
Run 45517911042 on ci-vfxp 2f37a6e (the final atlases). Stage = the game camera (FOV 50, pitch 40, 10.5 m), the 丹 floor, hemi + sun with a 2048 shadow map, fog 45-85 m, 10 suit boxes + 37 fodder boxes + the apex box. heavy = every suit attacking (slash + impact or a flying bolt + impact every 0.6 s, a ring / strip / mark tell held 0.6-0.8 s then its release every 3 s), 20 fodder units with strip tells and thrusts, the apex with its aura, claw rings and pounce strips, smoke: 42 live cards on average (peak 100). heavy_x4 = 4x the rate (114-117 live, peak 130), a stress case.
| Scene | fps | p95 ms | worst ms | frames > 20 ms | card pass GPU ms mean / p95 | stage GPU ms | live cards mean / max | calls | tris | new programs | card textures MB |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ref | 178.4 | 11.8 | 43.2 | 44 | - | 1.82 | 0 | 4 | 578 | 0 | - |
| heavy | 183.7 | 11.6 | 42.2 | 4 | 0.99 / 1.46 | 1.75 | 42 / 100 | 7 | 898 | 0 | 5.79 |
| heavy_x4 | 169.0 | 12.7 | 117.7 | 63 | 1.37 / 1.73 | 1.87 | 117 / 130 | 7 | 898 | 0 | 5.79 |
| heavy_x4 #2 | 173.2 | 12.1 | 66.3 | 26 | 1.37 / 1.75 | 1.98 | 114 / 130 | 7 | 898 | 0 | 5.79 |
| heavy #2 | 151.1 | 14.6 | 53.1 | 52 | 1.08 / 2.02 | 2.28 | 42 / 100 | 7 | 898 | 0 | 5.79 |
| ref #2 | 175.0 | 12.1 | 50.9 | 30 | - | 1.91 | 0 | 4 | 578 | 0 | - |
- 19 of 19 gates PASS, 0 FAIL lines (warm-up: 0 new programs in every scene; budget: 7 calls, 898 tris; 0 page errors in 6 scenes and 81 shots).
- Read: the heavy fight costs about 1.0-1.1 ms of GPU per frame for its cards (three draws). Its fps (183.7 / 151.1) sits around the reference's (178.4 / 175.0) inside this runner's spread (the reference alone read 149.7-200.7 fps in runs 45514584178 and 45516360904), so the rAF numbers show no cost beyond the noise; the card pass GPU time is the number to trust. No frame over 100 ms in heavy. The x4 stress had two frames of 111 and 118 ms (at 1.4 s and 6.5 s into timing) and none in its second pass; not traced (stress case, 2.7x the realistic card count).
- For comparison (ci-vfx, run 45467292518): 40 approved B slashes alone cost 1.59 ms with a 4.48 MB RGBA atlas for one effect; the 13 cards here cost 0.99-1.08 ms at 42 mixed cards with 5.79 MB for all of them.
- Runs on ci-vfxp: 45514584178 (first build: 31 live cards, small bolt / impact / aura / heal / smoke), 45516360904 (round 2: 42.6 live), 45517911042 (final, above).

## Look (honest, from the play-size shots of run 45517911042 and the contact sheets; not seen by the owner)
- Slash: reads as the approved B. Side by side at play size (shots pairB_f00-f12) the new value-plus-ramp slash in the fa row matches B's shape, timing and tone; its sparks are fainter than B's.
- Impact, thrust, burst, shield: read at play size in every row. The burst (a broken ring with radial strokes) is the weakest painted shape: it reads a little like a gear or a clock face, and in the heavy fight the overlapping bursts are the busiest thing on screen.
- Bolt: small in round 1; round 2 (its last) made it readable as an orb with a trail.
- Aura, heal, smoke: thin and small in round 1; round 2 (their last) made them larger and denser. They still read modestly at play size, mostly at the sides of a body. The smoke puffs in a school colour look like three coloured balls rather than smoke; smoke is meant for the ash row and dust, where it reads as a soft puff.
- Ground tells (ring, mark, strip): read strongly in all 18 rows, but they are the least "painted": the 3:1 floor rule makes them pale brush lines with a dark keyline, and the alpha test gives them hard edges, so they look graphic next to the soft upright cards. Their school colour shows only in the inner strokes.
- Colours: every school is distinct except fa (lead white) vs za (silver), which are nearly the same on every card (the known dE 7 pair from the banners). Bone black (阴阳) reads as an ink-wash style, dark body with pale cores.
- Not done: no in-game check (INT wires it in); no phone run; no animation viewed at play size other than single frozen frames on the runner (the local contact sheets show every frame).

## Effect map
### Suits (CONFIG.KITS; ramp = the caster's school row)

| id | Who | Move | CONFIG | Windup s | Tell | Release | Hit | Trail | State | Ramp | Sizes | Sounds (AUDIO.md) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ru_atk | ru 儒甲 | attack 射+数 (cut close, arrow far; every 6th a 3-arrow volley or heavy cut) | KITS.ru.attack | - | - | slash | impact | bolt | - | caster | slash x1 (heavy cut x1.25); bolt per arrow (3 for the volley) | ru_atk / ru_hit |
| ru_q | ru 儒甲 | Q 御·五驭 chariot charge (dash) | KITS.ru.skills[0] | - | - | thrust | impact | - | smoke | caster | thrust length = range 5, width 1.8; smoke = dust at the start | ru_q |
| ru_w | ru 儒甲 | W 书·六书·正名 brush-seal shot (line) | KITS.ru.skills[1] | - | - | thrust | impact | - | aura | caster | thrust length = range 8; aura on a sealed suit for seal 4 s | ru_w |
| ru_r | ru 儒甲 | R 乐·六乐·编钟 bells (3 rings land at 0.6 / 1.3 / 2.0 s) | KITS.ru.skills[2] | 0.6 | ring | burst | impact | - | - | caster | ring radius 4.5, held until each ring lands (holds 0.6, 0.7, 0.7 s); burst radius 4.5 | ru_r |
| dao_atk | dao 道甲 | attack 水 open-hand strike | KITS.dao.attack | - | - | slash | impact | - | - | caster | slash x0.8, mirrored | dao_atk / dao_hit |
| dao_q | dao 道甲 | Q 柔 stance (counter to basic attacks) | KITS.dao.skills[0] | - | - | - | burst | - | shield | caster | shield held stance 0.8 s; burst x0.5 on a successful counter | dao_q / dao_counter |
| dao_w | dao 道甲 | W 不争 stance (counter to skills), flow dash on success | KITS.dao.skills[1] | - | - | thrust | - | - | shield | caster | shield held 0.8 s; thrust length = the flow (max 8) | dao_w / dao_counter |
| dao_r | dao 道甲 | R 反 buff (8 s, grows with counters) | KITS.dao.skills[2] | - | - | - | - | - | aura | caster | aura held dur 8 s | dao_r |
| dao_p | dao 道甲 | passive 无为 unseen after 2 s still | KITS.dao.wuwei | - | - | - | - | - | smoke | caster | smoke x0.6 when he turns unseen (the shimmer stays the game's) | - |
| fa_atk | fa 法甲 | attack bronze sword (the approved sample B) | KITS.fa.attack | - | - | slash | impact | - | - | caster | slash x1 | fa_atk / fa_hit |
| fa_q | fa 法甲 | Q 刑无等级 pursuit dash + landing burst | KITS.fa.skills[0] | - | - | thrust | burst | - | - | caster | thrust length = dash (5 / 7.5); burst radius 1.6 | fa_q / fa_hit |
| fa_w | fa 法甲 | W 术·潜御 unseen, first hit exposes | KITS.fa.skills[1] | - | - | - | ring | - | smoke | caster | smoke x0.8 at the cast; ring radius 0.8 under the exposed target for exposeS 3 s | fa_w |
| fa_r | fa 法甲 | R 势 ring that follows him (6 s) | KITS.fa.skills[2] | - | - | - | - | - | ring | caster | ring radius 6 held dur 6 s, follows him; aura on him | fa_r |
| mo_atk | mo 墨甲 | attack 连弩 repeating crossbow bolts | KITS.mo.attack | - | - | - | impact | bolt | - | caster | bolt x0.8 | mo_atk / mo_hit |
| mo_q | mo 墨甲 | Q 距云梯 the wall (4 s) | KITS.mo.skills[0] | - | - | crack | - | - | smoke | caster | crack radius 2 at the wall base when raised; smoke at raise and fall | mo_q |
| mo_w | mo 墨甲 | W 墨经·衡 the lever (plate shown 0.6 s, then fling) | KITS.mo.skills[1] | 0.6 | mark | burst | impact | - | - | caster | mark radius 2.2; burst radius 2.2 | mo_w_tell / mo_w |
| mo_r | mo 墨甲 | R 九距之 nine defences (8 s or 9 blows) | KITS.mo.skills[2] | - | - | - | impact | - | shield | caster | shield held dur 8 s; impact at each blocked blow | mo_r |
| yy_atk | yinyang 阴阳甲 | attack 两仪 orb (dark / light alternate) | KITS.yinyang.attack | - | - | - | impact | bolt | - | caster | bolt x1 | yy_atk / yy_hit |
| yy_q | yinyang 阴阳甲 | Q 阴·月 slow orb (slow + drain) | KITS.yinyang.skills[0] | - | - | - | burst | bolt | - | caster | bolt x1.4; burst radius 0.9 | yy_q |
| yy_w | yinyang 阴阳甲 | W 阳·日 sunburst (shown 0.8 s) | KITS.yinyang.skills[1] | 0.8 | mark | burst | impact | - | - | caster | mark radius 2.5; burst radius 2.5 | yy_w_tell / yy_w |
| yy_r | yinyang 阴阳甲 | R 太极 disk (shown 1 s, then 2 x 1.5 s halves) | KITS.yinyang.skills[2] | 1.0 | mark | - | impact | - | ring | caster | mark radius 5 for tellS; ring radius 5 held 3 s; impact per burn pulse (0.25 s) | yy_r_tell / yy_r |
| za_atk | za 杂甲 | attack 议 orb | KITS.za.attack | - | - | - | impact | bolt | - | caster | bolt x1 | za_atk / za_hit |
| za_q | za 杂甲 | Q 兼儒墨 seal shot (line) | KITS.za.skills[0] | - | - | thrust | impact | - | aura | caster | thrust length = range 8; aura on a sealed suit for seal 2 s | za_q |
| za_w | za 杂甲 | W 合名法 blink | KITS.za.skills[1] | - | - | - | - | - | smoke | caster | smoke x0.8 at both ends | za_w |
| za_r | za 杂甲 | R 一字千金 casts the stored skill | KITS.za.skills[2] | - | - | - | - | - | - | caster | plays the stored skill's own cards in that skill's own ramp row (a unit move keeps its unit's row) | za_r |
| ming_atk | ming 名甲 | attack 轮不蹍地 wheel out and back | KITS.ming.attack | - | - | - | impact | bolt | - | caster | bolt x1 (both ways) | ming_atk / ming_hit |
| ming_q | ming 名甲 | Q 飞鸟之景 shadow blink | KITS.ming.skills[0] | - | - | - | - | - | smoke | caster | smoke x0.8 at the start (the shadow stays the game's) | ming_q |
| ming_w | ming 名甲 | W 镞矢之疾 hanging arrowheads (line shown 1 s) | KITS.ming.skills[1] | 1.0 | strip | thrust | impact | - | - | caster | strip 8 x 1.2; thrust length 8 | ming_w |
| ming_r | ming 名甲 | R 指不至 pointing never arrives (30 m line, 1 s) | KITS.ming.skills[2] | 1.0 | strip | thrust | impact | - | - | caster | strip 30 x 1.4; thrust length 30 | ming_r |
| zh_atk | zongheng 纵横甲 | attack 符节 token shot | KITS.zongheng.attack | - | - | - | impact | bolt | - | caster | bolt x0.8 | zh_atk / zh_hit |
| zh_q | zongheng 纵横甲 | Q 合纵 the link (cord 5 s) | KITS.zongheng.skills[0] | - | - | - | impact | - | aura | caster | impact on both at the tie; aura on both for dur 5 s; burst x0.5 on both when it snaps (the cord line stays the game's) | zh_q |
| zh_w | zongheng 纵横甲 | W 连横 the swap | KITS.zongheng.skills[1] | - | - | - | - | - | smoke | caster | smoke x0.8 at both places | zh_w |
| zh_r | zongheng 纵横甲 | R 不攻自破 circle (shown 5 s) | KITS.zongheng.skills[2] | - | - | - | - | - | ring | caster | ring radius 6 held dur 5 s | zh_r |
| nong_atk | nong 农甲 | attack 耒 plough-hoe | KITS.nong.attack | - | - | slash | impact | - | - | caster | slash x0.9 | nong_atk / nong_hit |
| nong_q | nong 农甲 | Q 播百谷 sow | KITS.nong.skills[0] | - | - | - | - | - | smoke | caster | smoke x0.4 per seed (sprouts stay models) | nong_q |
| nong_w | nong 农甲 | W 并耕 plough charge (furrow 4 s) | KITS.nong.skills[1] | - | - | thrust | - | - | strip | caster | thrust length = range 5; strip = the furrow, range x width 1.6, held furrowS 4 s | nong_w |
| nong_r | nong 农甲 | R 百草生机 harvest (ring 0.4 s, pulses) | KITS.nong.skills[2] | - | - | burst | heal | - | ring | caster | ring radius 8 held ringS 0.4; burst radius 3 per pulse; heal on him per sprout | nong_r |
| nong_p | nong 农甲 | passive 并耕而食 eats a sprout | KITS.nong.tiller | - | - | - | heal | - | - | caster | heal x0.8 one loop | - |

### Tiger Demon and its minions (CONFIG.APEX, MOVES, DEMON_ULT, PLATE; ramp apex)

| id | Who | Move | CONFIG | Windup s | Tell | Release | Hit | Trail | State | Ramp | Sizes | Sounds (AUDIO.md) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| apex_wake | Tiger Demon | wakes (3 s) | APEX.wakeS | 3.0 | aura | crack | - | - | - | apex | aura x1.6 held 3 s; crack radius 3 | demon_wake |
| claw | Tiger Demon | claw | MOVES.claw | 0.45 | ring | slash | impact | - | - | apex | ring radius 2.6; slash x1.3 | demon_claw_tell / demon_claw |
| pounce | Tiger Demon | pounce (dash line) | MOVES.pounce | 0.5 | strip | thrust | impact | - | - | apex | strip 7.5 x 2.2; thrust length 7.5; crack radius 1.5 on landing | demon_pounce_tell / demon_pounce |
| roar | Tiger Demon | roar (slow) | MOVES.roar | 0.7 | ring | burst | - | - | - | apex | ring radius 6; burst radius 6 | demon_roar_tell / demon_roar |
| demon_ult | Tiger Demon | Shed the limit (frenzy 8 s) | DEMON_ULT | 0.8 | aura | burst | - | - | aura | apex | aura x1.6 held windup then dur 8; burst radius 3 | demon_ult_tell |
| bite | Stalker / Howler / cubs | bite | MOVES.bite | 0.4 | ring | slash | impact | - | - | apex | ring radius 1.7; slash x0.6 | cub_bite_tell / cub_bite |
| lunge | Stalker / Howler / cubs | lunge (dash line) | MOVES.lunge | 0.45 | strip | thrust | impact | - | - | apex | strip 4.5 x 1.4; thrust length 4.5 | cub_lunge_tell / cub_lunge |
| rend | Stalker / Howler / cubs | rend (bleed) | MOVES.rend | 0.5 | ring | slash | impact | - | - | apex | ring radius 1.9; slash x0.6; impact x0.5 per bleed tick | cub_rend_tell / cub_rend |
| flank | Stalker / Howler / cubs | flank (spot behind, stun) | MOVES.flank | 0.6 | mark | burst | impact | - | - | apex | mark radius 2.2; burst radius 2.2 | cub_flank_tell / cub_flank |
| howl | Stalker / Howler / cubs | howl (slow) | MOVES.howl | 0.7 | ring | burst | - | - | - | apex | ring radius 7.5; burst radius 7.5 | cub_howl_tell / cub_howl |
| plate | cub plate reward | plate flies to the suit | PLATE.flyS | - | - | - | heal | bolt | - | apex | bolt x1 for flyS 0.7; heal x0.8 | plate_take |

### 皇家 guard and 反贼 rebels (CONFIG.GUARD, FANZEI)

| id | Who | Move | CONFIG | Windup s | Tell | Release | Hit | Trail | State | Ramp | Sizes | Sounds (AUDIO.md) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| g_thrust | 卒 guard | thrust (line) | GUARD.moves.thrust | 0.5 | strip | thrust | impact | - | - | guard | strip 2.6 x 0.8; thrust length 2.6 | g_thrust_tell / g_thrust |
| g_volley | 弩 guard | volley (mark on the target) | GUARD.moves.volley | 0.8 | mark | burst | impact | bolt | - | guard | mark radius 1.6; 3 bolts falling in; burst radius 1.6 | g_volley_tell / g_volley |
| g_shove | 盾 guard | shove (circle, push) | GUARD.moves.shove | 0.5 | ring | burst | impact | - | - | guard | ring radius 1.8; burst radius 1.8 | g_shove_tell / g_shove |
| g_charge | 车 guard | charge (dash line) | GUARD.moves.charge | 0.9 | strip | thrust | impact | - | smoke | guard | strip 10 x 1.8; thrust length 10; smoke = dust | g_charge_tell / g_charge |
| g_cut | 伍长 guard | cut (line) | GUARD.moves.cut | 0.5 | strip | slash | impact | - | - | guard | strip 2.4 x 1.0; slash x0.9 | g_cut_tell / g_cut |
| g_buff | 伍长 guard | squad buff while the 伍长 lives | GUARD.buff | - | - | - | - | - | aura | guard | aura x1 on the 伍长 only | - |
| g_break | 伍长 guard | the 伍长 breaks (buff ends) | GUARD.leaderBoon | - | - | burst | - | - | smoke | guard | burst x0.6; smoke x1 | g_break |
| g_block | 盾 guard | block (blow from the front) | GUARD.block | - | - | - | impact | - | shield | guard | impact x0.8; shield frames 0-3 once | - |
| unit_break | guard / rebel unit | a unit breaks | GUARD.types | - | - | - | - | - | smoke | guard | smoke x0.8 (rebels: their own row) | unit_break |
| r_talisman | 符水道人 rebel | talisman (heal mark on allies) | GUARD.moves.talisman | 0.8 | mark | heal | - | - | - | rebel_olive | mark radius 2.5; heal x1 on each mended ally | r_talisman_tell / r_talisman |
| r_lunge | 死士 rebel | lunge (line, the yellow glint) | GUARD.moves.lunge | 0.6 | strip | thrust | impact | - | - | rebel_umber | strip 7 x 1.0; impact x0.6 as the glint at the tell start; thrust length 7 | r_lunge_tell / r_lunge |
| r_cleave | 渠帅 rebel | cleave (circle) | GUARD.moves.cleave | 0.6 | ring | slash | impact | - | - | rebel_madder | ring radius 2.2; slash x1 | r_cleave_tell / r_cleave |
| bl_ru | 力士 rebel | bootleg ru move (line) | FANZEI.bootleg.ru | 0.8 | strip | thrust | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_dao | 力士 rebel | bootleg dao move (circle) | FANZEI.bootleg.dao | 0.8 | ring | burst | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_fa | 力士 rebel | bootleg fa move (line) | FANZEI.bootleg.fa | 0.8 | strip | thrust | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_mo | 力士 rebel | bootleg mo move (mark) | FANZEI.bootleg.mo | 1.0 | mark | burst | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_yinyang | 力士 rebel | bootleg yinyang move (mark) | FANZEI.bootleg.yinyang | 1.0 | mark | burst | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_za | 力士 rebel | bootleg za move (line) | FANZEI.bootleg.za | 0.8 | strip | thrust | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_ming | 力士 rebel | bootleg ming move (line) | FANZEI.bootleg.ming | 0.8 | strip | thrust | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_zongheng | 力士 rebel | bootleg zongheng move (circle) | FANZEI.bootleg.zongheng | 0.9 | ring | burst | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| bl_nong | 力士 rebel | bootleg nong move (line) | FANZEI.bootleg.nong | 0.8 | strip | thrust | impact | - | - | rebel_olive | tell and release sized from the move (range x width or radius); rebel row of the unit's variant, never the school's | r_bootleg_tell |
| r_stall | 力士 rebel | bootleg 甲 stalls (spark flash) | FANZEI.stallN | - | - | - | impact | - | smoke | rebel_umber | impact x0.8; smoke x0.6 | r_stall |
| r_charge | player (渠帅 charge) | the taken bootleg charge (school move x chargeK) | FANZEI.chargeK | - | - | - | - | - | - | caster | plays the school move's own cards in the player's school row | plate_take |

### Palace pieces, hazards, heals (CONFIG.STATUE, LION, PIECES, PIECES2, BURN, ALTAR, BOONS)

| id | Who | Move | CONFIG | Windup s | Tell | Release | Hit | Trail | State | Ramp | Sizes | Sounds (AUDIO.md) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| statue | tiger statue (royale) | strike | STATUE | 0.6 | ring | crack | burst | - | - | bronze | ring radius 6.5; crack radius 6.5; burst x1 | statue_tell / statue_strike |
| lion | 石狮 / bronze guardian beasts | strike | LION | 0.6 | ring | crack | burst | - | - | bronze | ring radius 4; crack radius 4 | lion_tell / lion_strike |
| giant_wake | 十二金人 giant | wakes (2 s) | PIECES2.giant.wakeS | 2.0 | aura | - | - | - | smoke | bronze | aura x2.4 held 2 s; smoke x1.5 when it steps off | giant_wake |
| giant_slam | 十二金人 giant | slam (ring round itself) | PIECES2.giant.slam | 1.0 | ring | crack | burst | - | smoke | bronze | ring radius 4; crack radius 4; burst x1.5; smoke x1.5 | giant_slam_tell / giant_slam |
| giant_sweep | 十二金人 giant | sweep (line ahead) | PIECES2.giant.sweep | 1.2 | strip | slash | impact | - | - | bronze | strip 7 x 3; slash x2.5 | giant_sweep_tell / giant_sweep |
| giant_fall | 十二金人 giant | breaks and falls (0.8 s) | PIECES2.giant.fallS | - | - | crack | - | - | smoke | bronze | crack radius 3; smoke x2 | giant_fall |
| vat | 门海 vat | cracks then splashes | PIECES2.vat | 0.5 | ring | burst | - | - | smoke | water | ring radius 3.5; burst radius 3.5 (the flood stays the game's) | vat_crack / vat_splash |
| burn_warn | burning wing | warning (5 s) before the wing falls | BURN.warnS | 5.0 | smoke | - | - | - | - | ash | smoke x2 at each door of the wing, one every 0.6 s (pooled one-shots); repeat every 0.6 s | st_burn |
| burn_fall | burning wing | the wing falls (1.2 s) | BURN.fallS | - | - | crack | - | - | smoke | ash | crack radius 3 at each door; smoke x2 | burn_fall |
| mercury | 水银 channels | warn 0.6 s, on 1.2 s | PIECES.mercury | - | - | - | - | - | - | ash | no card: owner 25 Nov 02:2x, the warning is a brighter texture + shimmer (game material) | merc_warn / merc_on |
| huabiao | 华表 | marking | PIECES.huabiao | - | - | - | - | - | - | bronze | no card: owner 25 Nov 02:25, decoration only | - |
| ding | 鼎 / altar | heal while standing in it | ALTAR | - | - | - | - | - | heal | jade | heal x1.2 held while healing | ding_heal |
| boon | crab / wanderer boon | boon taken | BOONS | - | - | - | burst | - | heal | jade | burst x0.6; heal for heal/regen; aura (bronze row) for power/speed/vision for s | boon |
| suit_break | any suit | a suit breaks | MAX_HP | - | - | burst | - | - | smoke | caster | burst x1; smoke x1.2 | - |

Items: 86; tells (windup): 40; no card: 4


## Credits (for CREDITS.md)
- pixelfx by Patch (https://github.com/patch-gg/pixelfx), MIT: effect shapes and timing used as reference for all 13 cards (melee/sword-slash, melee/thrust, impacts/hit-spark, projectiles/magic-missile, arcane/mana-burst, holy/divine-shield, status/rage, holy/heal, explosions/smoke-bomb, arcane/magic-circle-cast, holy/smite, impacts/ground-slam); no pixelfx code or pixels ship.
- Sprite Fusion VFX by Hugo Duprez, MIT: the slash's crescent and the hit spark's spray recipes, through the pixelfx effects that adapt them (sword-slash, hit-spark).
- klad (klad.studio, klad-app/klad 0.4.0): all cards painted with its CLI; only the exported PNGs ship (klad itself is not distributed).

## Needs owner
1. Look of the full set: the slash matches B; bursts read like a gear, smoke in school colours reads as coloured balls, aura / heal are modest; ground tells are graphic (pale lines, hard edges) because of the 3:1 floor rule. Approve, or name the cards to redo.
2. fa (lead white) and za (silver) cards are nearly identical: keep the mapping, or use a cooler silver for za's effects (like the banner-only #b2bccb).
3. Tells: keep the game's flat tell mesh under the painted tell card, or replace it (INT's integration choice).
