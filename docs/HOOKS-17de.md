# HOOKS 17d/17e: how index.html calls src/palace_art.js (PREP-PAL, 25 Nov 2026)

For the integration writer (INT). This module never touches index.html, tests/ or game state: it builds render objects and changes their looks when told.
Collision stays on index.html's box solids. The only new solids are those of the new decorative props (racks, lamps, bell stands, standards); they come back in `art.solids` and the integrator adds them (step 6).
Proof: ci-out `out/prep-pal/<run>/` (see the end of this file). Line numbers below are for batches-3-5 at 874d217.

## 0. Import and switches
```js
import * as PA from './src/palace_art.js';                     // after the KTX2Loader import (line ~106); 'three' comes from the importmap
import { GLTFLoader } from './lib/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from './lib/jsm/libs/meshopt_decoder.module.js';
```
- `PA.PAL_ART` holds every tunable, with a comment line above each value. Copy the two master switches into CONFIG with a comment line each, then apply them once at boot:
  `Object.assign(PA.PAL_ART, { arch: CONFIG.PAL_ART.arch, props: CONFIG.PAL_ART.props })`.
- Per-feature switches are in `PA.PAL_ART.on`: terrace, eaves, racks, plants, flags, que, inlay, throne, lamps, bells, tally, standards, lake.
- The phone link importmap needs the same two addon paths on jsdelivr three@0.171.0. The module itself imports only `three`.

## 1. At boot: keep handles to the box meshes the art hides (no other boot change)
The box palace stays built at boot as today. It is the fallback if the card fails or is capped.
- Room loop (line ~2621):
  - store each part mesh: `r.box = r.box || {}; r.box[key] = mesh;`.
  - In `pillar()` (line ~2609), record the spot: `(r.spots || (r.spots = { pillars: [], dais: null })).pillars.push([x, z]);`.
  - For the core dais block (line ~2617), record `r.spots.dais = [r.cx, r.z0 + 4];`.
- Pieces loop (line ~2742):
  - keep the merged piece meshes per key: `r.pieceBox = r.pieceBox || {}; r.pieceBox[k] = still(...)`. Keys: palLion (lions), stone (华表), bronze (鼎 and smoke boxes).
  - On each entry, keep its source item: `PIECE_HAZ[i].src = p`, `PIECE_MERC[i].src = p`, `PIECE_DING[i].src = p`. This is so step 4 can attach the art handle to the game object.
- P2 build (line ~3779): nothing new. The clock box (p2Static bronze plus `c.water`) and `v.body` are hidden in step 5.

## 2. Card P jobs (LD_JOBS.palace, line ~7466): four new jobs between 'apply' and 'compile'
Texture route: the existing `ldOne(name)`, so the files are KTX2 desk or phone, then the manifest PNG, then the PNG source. Reuse the five images already in `LD.files` by name (hall_wall, hall_floor, pillar, door, lion_stone); do not fetch them twice.
```js
{ key: 'art_fetch', run() {            // GLBs (meshopt) and the art textures, in parallel; failures listed in the ledger
  if (!LD.started) { LD.started = true; const g = LD.gen, gl = {}, tx = {}, ld = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    const have = Object.values(CONFIG.TEX.files); have.forEach((n, i) => { if (LD.files[i] && LD.files[i].t) tx[n] = LD.files[i].t; });
    ldWait(Promise.all([...PA.files('./').map((f) => ld.loadAsync(f.url).then((x) => { gl[f.key] = x; }, () => LD.led.failed.push(f.key))),
      ...PA.textureNames().filter((n) => !tx[n]).map((n) => ldOne(n).then((f) => { if (f.t) tx[n] = f.t; else LD.led.failed.push(n); LD.led.fmt.push(n + ':' + f.how); }))])
      .then(() => { if (g === LD.gen) LD.art = { gl, tx, it: null, kit: null, ri: 0, arts: [] }; })); }
  return LD.waitDone; } },
{ key: 'art_kit', run() {              // shared materials and baked geometry, one file per step inside the slice
  const A = LD.art; if (!A.it) A.it = PA.kitSteps(A.gl, (n) => A.tx[n] || null, { fow: FOW, schools: CONFIG.SCHOOLS, phone: TOUCH, maxAniso: renderer.capabilities.getMaxAnisotropy() });
  const s = A.it.next(); if (!s.done) return false; A.kit = s.value; return true; } },
{ key: 'art_rooms', run() {            // one room per step: architecture, props, doors (section 3)
  const A = LD.art; if (A.ri < PAL.rooms.length) { artRoom(PAL.rooms[A.ri++]); return false; } artDoors(); artApply(); return true; } },
```
- loadTick asks a job again inside the same slice until sliceMs is spent. So "false" in art_kit and art_rooms means "more to do", not "waiting".
- Measured on Node (local probe, no GPU), for scale only:
  - 42 GLB parses: 54-76 ms.
  - makeKit total: 213-216 ms over 42 steps.
  - All 29 rooms: 67-68 ms, so about 2.3 ms per room.
  - The runner's card times decide.
- Compile, upload and draw: the existing jobs.
  - `ldWarmOn()` adds `PA.warmOn(LD.art.kit, scene, camera, LD.art.arts)`. That is the warm rack: one triangle per material, plain and instanced, in front of the warm camera. It also shows every state: lit and dry, cracked and shards, windup, bars.
  - `ldWarmOff()` adds `PA.warmOff(LD.art.kit, scene, LD.art.arts)`, which puts every state back to rest.
  - `ldUpload()` adds `for (const t of LD.art.kit.texList) renderer.initTexture(t)`.
  - The ledger's draws, programs and textures then include the art. P11 proves 0 links in play after this warm.
- Failure policy (TEX rule): if any art file failed, run `PA.disposeKit` and keep the box palace, never half the art. The card cap follows the same rule (ldCapped: art not yet applied, so the boxes stay).

## 3. Per room (artRoom) and doors (artDoors)
```js
function artRoom(r) {
  const K = LD.art.kit, art = PA.buildRoom(K, r, PAL.rooms, { pillars: r.spots ? r.spots.pillars : [], dais: r.spots ? r.spots.dais : null,
    blocked: PAL.solids.filter((b) => b.s === r) });
  const si = r.school ? CONFIG.SCHOOLS.indexOf(r.school) : 0;
  for (const h of PIECE_HAZ) if (h.s === r && h.kind === 'lion') h.art = PA.addTo(art, PA.prop(K, 'beast', h.x, h.z, (h.src && h.src.fz || 1) > 0 ? 0 : Math.PI));
  for (const h of PIECE_HAZ) if (h.s === r && h.kind === 'huabiao') h.art = PA.addTo(art, PA.prop(K, 'huabiao', h.x, h.z, 0));
  for (const a of PIECE_DING) if (a.s === r) { a.art = PA.addTo(art, PA.ding(K, a.x, a.z, si)); PA.standard(K, art, r, a.x, a.z, si, PAL.solids.filter((b) => b.s === r)); }
  for (const s of PIECE_SMOKE) if (s.s === r) s.art = PA.addTo(art, PA.prop(K, s.src === 'crane' ? 'crane' : 'censer', s.x, s.z, 0));  // keep the src in step 1
  for (const m of PIECE_MERC) if (m.s === r) m.art = PA.addTo(art, PA.mercury(K, m.x0, m.x1, m.z0, m.z1));
  for (const c of P2.sets[PAL.layout].clocks) if (c.room === r) c.art = PA.addTo(art, PA.prop(K, 'clock', c.x, c.z, 0));   // keep x, z on the clock in step 1
  for (const v of P2_VATS) if (v.lay === PAL.layout && v.r0 === r) v.art = PA.addTo(art, PA.prop(K, 'vat', v.x, v.z, 0));
  r.art = art; LD.art.arts.push(art);
}
function artDoors() { for (const d of PAL.doors) { d.art = PA.door(LD.art.kit, d); PA.addTo(d.ra.art, d.art); } }
```
- Build the rooms of the plan in use (`PAL.rooms`). A second plan (proto) is built only when it is used.
- PIECE_SMOKE needs `src` stored at build, and P2 clocks need `x`, `z` stored at build (one field each, step 1).

## 4. Apply (artApply, once, after the last room) and revert (Royal Rumble)
```js
function artApply() {
  const K = LD.art.kit;
  for (const r of PAL.rooms) { const a = r.art; r.group.add(a.group);
    for (const k of a.replaces) if (r.box[k]) r.box[k].visible = false;                          // walls, pillars, the core dais and throne boxes, drawn floors
    if (a.floorMeshes.length) { r.boxFloor = [r.floorMeshes, r.floorMats]; r.floorMeshes = a.floorMeshes; r.floorMats = a.floorMats; }
    if (PA.PAL_ART.props) for (const k of ['palLion', 'stone', 'bronze']) if (r.pieceBox && r.pieceBox[k]) r.pieceBox[k].visible = false; }
  for (const m of PIECE_MERC) if (m.art) m.mesh.visible = false;
  for (const c of P2.sets[PAL.layout].clocks) if (c.art) { c.water.visible = false; c.boxMesh.visible = false; }  // keep p2Static's mesh as c.boxMesh in step 1
  for (const v of P2_VATS) if (v.art) v.body.visible = false;
  for (const d of PAL.doors) if (d.art) { d.group.add(d.art.root); d.panel.visible = false; }
  PA.lakeApply(K, PAL.lake); artSolids(true);
}
```
- On Royal Rumble (ldDispose), undo in reverse:
  - box meshes visible again;
  - `r.floorMeshes` and `r.floorMats` back from `r.boxFloor`;
  - door panels back (`d.panel.visible = !d.open`);
  - `artSolids(false)`;
  - for each room, `PA.disposeRoom(r.art); r.art = null`;
  - `PA.disposeKit(kit)`, which also puts the lake material back.
  - P14 proves GL buffers, textures, geometries and textures in renderer.info are flat over two build and dispose cycles.
- The vat ring, the flood disk, the 鼎 heal disc, mercury damage, smoke puffs (the hiding mechanic) and the lion ring stay the game's own. The art only replaces looks.

## 5. State hooks (each one line beside the existing code; every PA.set* is allocation-free and inside the module's PERFRAME block)
| Where (line) | Game event | Add |
|---|---|---|
| palDoor (2999) | door opens or shuts | `PA.setDoor(d.art, open, d.locked)`. The art leaves replace `d.panel`, so keep `d.panel.visible = false` while the art is on. |
| palDoorLocks (3324) | lock changes | `PA.setDoor(d.art, d.open, d.locked)` (the bronze bar shows while locked) |
| enterPalace (3026) | doors reset | `PA.setDoor(d.art, false, false)` |
| onWingWarn (~3646) | wing warned (burning) | `PA.setBurnt(r.art, true)` (A18: timber, earth, plaster, lacquer, slips, door) |
| burnReset (~3685) | new run | `PA.resetRoom(r.art)` (fresh materials, doors shut, 鼎 lit, vats whole, clocks full, beasts idle, mercury calm) |
| hazard step (2767 / 2771) | lion windup starts / strike ends | `if (h.art) PA.setBeast(h.art, true)` / `PA.setBeast(h.art, false)` (the raised-claw pose; the red ring stays the tell) |
| 鼎 (2818, 2827, 2834, altarLooks 4524) | charge empty / refilled / dry decree | `PA.setDing(a.art, !(dry or a.charge <= 0))` |
| mercury step (2844) | state changes | `PA.setMerc(kit, m.art, st === 0 ? 'idle' : st === 1 ? 'warn' : 'hot')` |
| hitVat (3835) / p2Splash (3868) / vat reset (3900) | cracked / broken / whole | `PA.setVat(v.art, 1)` / `PA.setVat(v.art, 2)` / `PA.setVat(v.art, 0)` |
| stepPieces2 (4028) | clock step changes | `PA.setClock(c.art, c.level)` (PA.PAL_ART.clockSteps = CONFIG.PIECES2.clock.steps = 48: keep them equal) |
| the palace frame (PERFRAME, while PAL.on and the art applied) | every frame | `PA.tick(kit, dt)` (mercury shimmer: 3 texture offsets) |
- Shadows: call `renderer.shadowMap.needsUpdate = true` after setDoor, setVat and setBurnt, as the box code already does for doors.

## 6. New solids (racks, lamps, bell stands, standards)
These are a gameplay-visible change: new collision in halls and the core. Each has its own switch in `PA.PAL_ART.on`.
`art.solids` lists boxes `{ x0, x1, z0, z1 }`. They are already checked against the room's solids and never overlap one (P16).
```js
function artSolids(on) {
  const live = SOLIDS.indexOf(PAL.solids[0]), n0 = PAL.solids.length;
  if (on) { for (const r of PAL.rooms) for (const b of r.art.solids) PAL.solids.push(Object.assign({ s: r, art: true }, b)); }
  else for (let i = PAL.solids.length - 1; i >= 0; i--) if (PAL.solids[i].art) PAL.solids.splice(i, 1);
  if (live >= 0) { SOLIDS.splice(live, n0); for (const b of PAL.solids) SOLIDS.push(b); }   // enterPalace's block stays contiguous
}
```
- Risk: bots do not route around the new solids (NAV is built at boot). The walking rule stops them, so a bot can stall at a rack. If that matters, keep racks, lamps and bells switched off until the nav covers them.

## 7. What is built where (17d / 17e), and the numbers each piece uses
- Walls: they stand on index.html's box walls. The centre sits wallT/2 = 0.25 m inside the edge, with the same door gaps. The pieces are whole 4 m segments stretched over a run (scale 0.67-1.5).
  - Tall (north, west, east): hall wall_seg, core wall_earth_seg, court wall_walk_seg, corridor wall_mural_seg, garden wall_seg.
  - South (camera side): wall_low.
  - Bridges: wall_low on the short ends. The long sides are the bays' rails.
  - P5 proves length and centre line against every box wall.
- Floors: court A7 stone paving, corridor A8 tiles, garden A16 ground, bridge timber deck (bays 2 cm under it). They carry the warn tint through r.floorMeshes.
  - Hall and core keep the game's approved A1 floor (unchanged mapping).
- Eaves and tile ends: hall tall edges (8 tile ends per segment). Corridors get eaves only.
- Terrace: only stretches that face the lake (P17).
- Pillars: on the game's pillar spots (P6). The plinth is 1.5 m against the 1.2 m box (W2 note).
- Throne and dais: on the core dais block (12 x 6 m, top 1.5 m).
- Star inlay: 4 m cells in front of the dais.
- 阙 pairs: at the forecourt's west and east bridge gates, turned 90 deg. This is an owner question: W2 put them north, where the 12 m approach bridge is wider than their 8 m passage.
- Racks: hall north wall, clear of doors (2.6 m) and solids. Bundles: about 94 per rack.
- Plants: a 3.2 m band along garden walls, 4.5 m clear of doors, away from planters. Seeded, so replays match.
- Flags: court north wall at centre ±12 / ±20 m.
- Lamps: hall north corners, and 7.4 m either side of the core dais.
- Bells: core side walls.
- Tally: on the dais top.
- Standard: 2.2 m from the 鼎 toward the room centre.
- Props (C1-C12) are THREE.LOD with the 17a GLBs' LOD1/LOD2 spread (+3 / +6 m in x) undone (P3). Every level is merged per material, and the state objects sit beside the LOD.
  - Beast: the idle pose and the strike windup (raised claw, clip time from the paws' highest point) are baked at card time. No skeleton or mixer runs in play.
  - Clock: 49 precomputed matrices per moving node.
- LOD distances follow INTEGRATION section 6's rule: height x 1158 / 200 px for LOD1 and / 70 px for LOD2, times 0.6 on phones. Metres (LOD1 / LOD2), from `PA.info(kit).lodDist`:

  | Prop | LOD1 (m) | LOD2 (m) |
  |---|---|---|
  | beast | 16.9 | 48.4 |
  | ding | 9.4 | 27.0 |
  | vat | 6.3 | 18.0 |
  | crane | 16.9 | 48.2 |
  | censer | 10.2 | 29.1 |
  | clock | 13.7 | 39.2 |
  | huabiao | 35.9 | 102.6 |
  | lamp | 13.2 | 37.7 |
  | bells | 16.5 | 47.1 |
  | tally | 8.5 | 24.3 |
  | standard | 22.2 | 63.5 |
  | throne_dais | 29.9 | 85.5 |
  | que_pair | 82.2 | 234.9 |
- Shadows: walls, pillars, doors, eaves and props at or over 2.0 m tall cast. Cards, tile ends, bundles, plants, flags, terraces, inlay, 鼎, vat, censer and tally do not (P15).
- Fog of war: the module's own hook (key 'pafow1'). It uses instanceMatrix and works on matcap materials.
  - Finding for the lead: the game's addFow writes `modelMatrix * position` only. Any InstancedMesh with a 'fow1' material (for example P2.dorm and P2.wake giants with M.bronze) gets the fog of war of the mesh origin, not of each instance. Not fixed here (index.html is the integrator's).
- Lights: none added (P8). Lamps and 鼎 coals are emissive or additive cards.

## 8. Not done here (reasons)
- Garden pond (FIXB light water): the game's garden has no pond area, and its centre holds the curtains. Not placed.
- Lake rubble and fallen-room debris (B11) are effects (section D), not 17d/e.
- Giants (C8) are characters (17h).
- The 华表 hazard, TEXT keys and check 804 removal is index.html work (INT).
- Mercury channel lips are drawn only on the channel boxes listed in PAL_FULL_PIECES. The proto plan's PIECES_01 channels use the same call.

## 9. Proof (run 45540525097, code at e82e902 on prep-pal; ci-out out/prep-pal/45540525097/)
- Linux (SwiftShader, counts and correctness): P0 static PASS plus P1-P20 = 21 of 21. Mutants: 21 of 21 caught, each by its named check.
- macOS real GPU (Apple M1 virtual, ANGLE Metal): 12 of 12. The heaviest view is corr_w with all its neighbours attached, in the frame that redraws shadows.
  - Reference measured twice in the same job: 222.2 / 211.6 fps, p95 10.9 / 11.4 ms.

  | View | fps | p95 (ms) | Worst frame (ms) | GL draws | Triangles |
  |---|---|---|---|---|---|
  | Medium | 206.9 | 11.1 | 27.4 | 200 (105 with no shadow redraw) | 132k |
  | Low | 261.3 | 10.8 | 29.1 | 105 | 89k |

  - In play, 0 programs are linked.
  - Memory over two builds and disposes is flat: 146 GL buffers, 5 textures, 36 geometries before and after.
- Heap item: CLOSED.
  - Over 20 s of play, measured through DevTools after full GCs: medium 12.71 -> 12.83 MB, low 12.15 -> 12.23 MB. The reference went 8.17 -> 8.25 MB.
  - The earlier "growth" (rounds 3-4) came from reading a single window.gc(), which is noisy: one reading showed 68.1 MB after GC against 66.1 MB before it. The sampling profiler found 0.06-0.16 MB of live allocations over the window.
- Art notes for the owner:
  - que_pair LOD2 floats 0.50 m (no footing), so it is not used. LOD1 stays to the end, and 235 m is beyond the 90 m far plane anyway.
  - 阙 placement is an owner question (section 7).
