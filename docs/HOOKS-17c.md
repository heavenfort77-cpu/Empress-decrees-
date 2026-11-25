# Batch 17c hook list: sound, painted cards and the options menu (PREP-AV for INT, 25 Nov)

INT is the only writer of index.html and tests/. Everything below is a drop-in: the modules are done and tested on branch prep-av; this file says exactly what INT adds to index.html.
Line numbers are from batches-3-5 ab0473f (before 17b). INT's 17b edits move them, so each place is also named by its function and anchor text.
Checked against 874d217 (17b landed): every function named below still exists, about 19 lines lower (beginMove 5651, hitTarget 2100, guardBegin 6734, reset 7327, pickMode 7150, palEnter 3001). tests/static-check.mjs of 874d217 passes over these src modules (`node tests/static-check.mjs index.html <prep-av>/src`: STATIC PASS, 6 modules, 4 perframe blocks), and tests_draft/fx-map.mjs against 874d217's index.html passes 12 of 13: unit moves, guard moves and stinger keys pass; only "options keys in TEXT" fails until INT pastes the opt_* keys of section 6.

## 0. Modules (on batches-3-5 after the gates pass; nothing else to copy)
| File | What |
|---|---|
| `src/fx/fxevent.js` | `fxEvent(name, x, z, school, opts)`: the ONE dispatcher. It plays the sound and spawns the painted card(s). Also `fxO`, `fxStep`, `fxMove`, `fxRelease`, `fxKill`, `fxSecond`, `fxVoice`, `fxPause`, `fxClear`, `fxIds`, `fxWarm`, `fxSetRoom`, `fxSetCamera`, `fxSetTier`, `fxDispose`, `fxStatus` (allocates: tests only), `fxLive`, `fxEvents` (no allocation: debug line) |
| `src/fx/fxmap.js` | The event table: 97 items, 242 events (`item:phase`). Joins the 86 items of docs/VFX.md to the sounds of docs/AUDIO.md. Also `UNIT_ITEM` (MOVES key to item), `GUARD_ITEM` (GUARD.moves and bootleg key to item), `STINGER_OF` (TEXT voice key to stinger) |
| `src/fx/cards.js` | Card pools: one InstancedBufferGeometry + ShaderMaterial per atlas (3 draws). Ported from art/vfx/cards_reference.js |
| `src/fx/intensity.js` | Music intensity 0-1 and ambience (fire, wind) from game state (section 5) |
| `src/audio/options.js` | Options/pause menu: sliders, mute, CSS, TEXT keys (section 6) |
| `src/audio/sound.js` | Changed: `setMute(on)`, `getVolume(bus)`, `setVolume(bus, v, noSave)`; `status()` adds `mute`, `played`, `sr` and `vol`; `bufferOf(name)` is a read-only test hook. Mute is saved with the volumes in `empressDecrees.audio`. Effects now render straight into the AudioBuffers they play from: no copy, so the old ~42 MB of desktop copy garbage is gone, and the samples are identical (T16). The loop arrays are no longer kept after the loops start (`S.loops` held them) |

Phases per item: `tell` (windup, held), `rel` (release: the move fires), `hit` (lands; x, z = the target), `whiff` (miss), `trail` (flies: follow it with fxMove), `state` (held aura, shield, ring or smoke), `end`.
The callable names are the keys of `fxTable()`; tests_draft/fx-map.mjs lists them all. No call site ever builds a name per event: names are literals, or ids made once at load (section 3).

## 1. Imports, CONFIG and boot (load time)
1. Module imports, after `import * as THREE from 'three';` (line 101):
   ```js
   import * as SND from './src/audio/sound.js';
   import * as FX from './src/fx/fxevent.js';
   import { IN as AUD_IN, INT_CONFIG, stepIntensity, resetIntensity } from './src/fx/intensity.js';
   import { buildOptions, OPT_CSS } from './src/audio/options.js';
   ```
2. CONFIG entries (static-check rule 6: a comment line above each value):
   ```js
     // Sound (batch 17c, owner 25 Nov 04:4x: wire src/audio/sound.js in): on = sounds play; profile '' = by pointer (coarse = phone).
     SND: { on: true, profile: '' },
     // Painted attack cards (batch 17c, owner 25 Nov 04:4x: painted cards for all attacks): on = cards drawn (off = sounds only);
     // pool per atlas (low tier halves it); dtMax s; cardFwd m toward the camera; pitchSin = sin(CAM_PITCH_DEG); sphereR m round the room.
     FX: { on: true, base: './assets/vfx/', pool: { soft_a: 64, soft_b: 48, ground: 48 }, dtMax: 0.05, cardFwd: 0.6, pitchSin: 0.643, sphereR: 40 },
     // Music intensity levels and ambience (docs/HOOKS-17c.md section 5; a proposal from docs/AUDIO.md made concrete, not tuned): levels 0-1,
     // fightS s a fight lasts after the last blow, lowHp share, lastSuits = peak at or under this many suits, holdS s before a level falls.
     INTENSITY: { explore: 0.1, near: 0.3, fight: 0.5, danger: 0.7, peak: 1.0, fightS: 4, lowHp: 0.5, lastSuits: 2, holdS: 3 },
     // Options menu (owner 25 Nov 07:5x "follow lol or dota"): Esc opens it in play and pauses; no sound hotkey (B dropped, M stays the debug overview).
     OPTIONS: { on: true },
   ```
3. At boot, after the renderer and scene exist and before the first frame:
   ```js
   Object.assign(INT_CONFIG, CONFIG.INTENSITY);
   if (CONFIG.SND.on) SND.init({ unlockEl: window, profile: CONFIG.SND.profile || (TOUCH ? 'phone' : 'desktop') });
   FX.initFx({ THREE, scene, snd: CONFIG.SND.on ? SND : null, tier, cfg: { cards: CONFIG.FX.on, base: CONFIG.FX.base, pool: CONFIG.FX.pool, dtMax: CONFIG.FX.dtMax, cardFwd: CONFIG.FX.cardFwd, pitchSin: CONFIG.FX.pitchSin, sphereR: CONFIG.FX.sphereR } });
   ```
4. Card load and warm-up under 17b's loader (LD, LD_JOBS, ldStart, ldNeed in 874d217). The painted cards are one shared set for both modes, loaded once and kept: never dispose them on a mode switch (ldDispose leaves them alone). Call `FX.fxDispose()` only on page teardown.
   `FX.loadFx()` fetches the atlases (fetch + createImageBitmap, never `<img>`), parses the table and builds the 3 pools; it resolves to the parse error list (must be empty: a check). It is one promise, so calling it again returns the same load. `FX.fxWarm(renderer, camera)` uploads the 4 textures, compiles and draws all 13 cards once, then clears them; it returns 13, and `renderer.info.render.calls` right after it is that draw (3 calls).
   One job, next to ldCompile:
   ```js
   // Painted cards (17c): load once, then upload, compile and draw all 13 under the card; the draw goes to the ledger. Re-runs on 'restore'.
   function ldFx() {
     if (!CONFIG.FX.on || (LD.fx && LD.kind !== 'restore')) return true;
     if (!LD.started) { LD.started = true; ldWait(FX.loadFx().then((e) => { LD.fxErrs = e; })); }
     if (!LD.waitDone) return false;
     LD.fx = FX.fxWarm(renderer, camera) > 0; LD.led.draws += renderer.info.render.calls; LD.led.n++;
     return true;
   }
   ```
   - LD fields: add `fx: false, fxErrs: null` to `const LD = {...}`.
   - LD_JOBS: `{ key: 'fx', run: ldFx }` as the first job of `palace` and the last job of `restore`, plus a card of its own: `fx: [{ key: 'fx', run: ldFx }]`.
   - ldNeed(): after the palace line, `if (CONFIG.FX.on && !LD.fx && !LD.jobs) ldStart('fx');` (covers Royal Rumble and a palace run with CONFIG.TEX off; when the palace card runs, its own fx job does it).
   - TEXT: `load_fx: 'Painting the strikes'` and `load_step_fx: 'Painting the strikes'` (the loader builds both keys at runtime, so static-check rule 6 cannot see them: add them by hand).
   - A check: `LD.fxErrs` is an empty array and `LD.fx` is true after the first card (window.__game hook).
5. Unlock (inside the gesture handlers; init also hooks the first pointerdown, touchend and keydown): add `SND.unlock();` as the first line of `pickMode(m)` (line 7130), `pickSchool(i)` (line 7102) and the `#btnHunt` click handler.
6. Event ids for the kits, once at load after CONFIG.KITS is final (the `nameKey` 'sk_ru_q' gives item 'ru_q'; the attack item is '<prefix>_atk'):
   ```js
   const FX_PRE = { ru: 'ru', dao: 'dao', fa: 'fa', mo: 'mo', yinyang: 'yy', za: 'za', ming: 'ming', zongheng: 'zh', nong: 'nong' };
   for (const sc of CONFIG.SCHOOLS) { const k = CONFIG.KITS[sc]; k.attack.fx = FX.fxIds(FX_PRE[sc] + '_atk'); for (const sk of k.skills) sk.fx = FX.fxIds(sk.nameKey.slice(3)); }
   ```
   `fxIds` returns `{ tell, rel, hit, whiff, trail, state, end }`, with '' for a missing phase. `fxEvent('')` counts as unknown, so guard each call with `if (sk.fx.tell)`.
   This needs `loadFx()` to have run (the table is parsed there). If the kit ids are needed before the cards load, call `FX.loadFx()` first: it is the same promise the card waits on.

## 2. Per frame (inside the existing PERFRAME blocks)
| Where | Add | Why |
|---|---|---|
| end of `step(dt)` (the fixed step, inside its PERFRAME block) | `FX.fxStep(dt, false);` | card clock = game time in fixed steps. A paused frame returns before step() (`if (G.paused ...) return;` line 7455), so cards freeze while paused |
| `frame()` after the step loop, before `renderer.render` (line 7461) | `SND.setListener(P.x, P.z); stepIntensity(dt, SND);` | listener = the player (the camera focus if 17b makes one); intensity calls sound.js only on change |
| the inputs to intensity: where the game already updates them, or in one block before `stepIntensity` | the `AUD_IN.*` assignments of section 5 | numbers only, no objects |
| room change: `palEnter(r)` (line 2982), after `PAL.cur = r` | `FX.fxSetRoom(r.cx, r.cz, r.radius); AUD_IN.room = r.type;` (use the room's centre and half-diagonal fields as they exist) | culling sphere round the room; wind per room type |
| Rumble start (`reset()` when `!PAL.on`) | `FX.fxSetRoom(0, 0, 60); AUD_IN.room = 'rumble';` | |
| camera yaw (only if 17b adds a camera yaw; today the camera sits at +z) | `FX.fxSetCamera(fx, fz)` on change | upright cards sit toward the camera |

PERFRAME rules hold: every call above is in a PERFRAME block of a module (tests_draft/static-src.mjs checks them), and none allocates.

## 3. Call sites: every attack, tell, hit and state goes through fxEvent (one home)
Shared opts: `FX.fxO(dx, dz, a, b, hold, rate, y)`. Here a = radius or length m, b = width m, and hold = the CONFIG windup or duration.
Always pass the CONFIG numbers (radius, range, width, windup), so the card matches the hit shape and shows for exactly the windup. The table's sizes are only defaults.
`school` = the caster's school (`s.school`), its rebel variant row (`'rebel_olive' | 'rebel_umber' | 'rebel_madder'`), or '' for fixed-row items (apex, guard, bronze, water, ash, jade).

### 3a. Units: Tiger Demon, Stalker, Howler, cubs (MOVES; 2 places cover all 9 moves)
Item = `UNIT_ITEM[k]` (claw, pounce, roar, bite, lunge, rend, flank, howl, ult -> demon_ult). Store the ids once per move key at load: `const UEV = {}; for (const k in UNIT_ITEM) UEV[k] = FX.fxIds(UNIT_ITEM[k]);`.
| Function (line) | Anchor | Add |
|---|---|---|
| `beginMove(u, k, dx, dz)` (5632), before `return true` | `u.fx = dx; u.fz = dz; u.st = 1;` | `u.fxH = FX.fxEvent(UEV[k].tell, m.shape === 'line' ? u.x : u.tx, m.shape === 'line' ? u.z : u.tz, 'apex', FX.fxO(dx, dz, m.shape === 'line' ? u.tl : m.radius, m.width, m.windup, u.cub ? 1.15 : 0, u.y));` |
| `resolveMove(u)` (5656), after `hideTell(u)` | `hideTell(u);` | `FX.fxRelease(u.fxH); u.fxH = -1; FX.fxEvent(UEV[k].rel, u.x, u.z, 'apex', FX.fxO(u.fx, u.fz, m.shape === 'line' ? u.tl : m.radius, m.width, 0, u.cub ? 1.15 : 0, u.y));` (for k === 'ult': `UEV.ult.rel`, then `u.ultH = FX.fxEvent(UEV.ult.state, u.x, u.z, 'apex', FX.fxO(0, 1, 0, 0, CONFIG.DEMON_ULT.dur))`; follow with fxMove) |
| `resolveMove`, inside the suit loop at `if (dmg > 0) { u.atkAt = G.time; const lost = hurtSuit(...)` | `hurtSuit(s, dmg, 'hit', null, u)` | `FX.fxEvent(UEV[k].hit, s.x, s.z, 'apex', FX.fxO(u.fx, u.fz, 0, 0, 0, 0, s.y));` (slow, stun and bleed play through the hit's own sound: p_slow, p_stun, p_bleed) |
| pounce landing (where `u.st === 2` ends the dash) | | `FX.fxEvent('pounce:end', u.x, u.z, 'apex', FX.fxO(0, 1, 0, 0, 0, 0, u.y));` |
| a unit killed mid-windup (`killUnit`, 5792) and `clearMarks`/scene change | | `FX.fxKill(u.fxH); u.fxH = -1;` |
| apex wake (`startHunt`/wake, 7016-7046) | `setText(el.voice, T('voice_wake'))` | `FX.fxEvent('apex_wake:tell', D.x, D.z, 'apex', FX.fxO(0, 1, 0, 0, CONFIG.APEX.wakeS));` and at the end of the wake `FX.fxEvent('apex_wake:rel', ...)` |
| plate flies (`grantPlate`, 5801 / `addPlate`, 5905) | | `trail` at the cub with fxMove for PLATE.flyS, then `FX.fxEvent('plate:hit', s.x, s.z, 'apex', FX.fxO())` on arrival |

### 3b. 皇家 guard and 反贼 rebels (GUARD.moves + FANZEI.bootleg; 3 places)
Item = `GUARD_ITEM[u.cur]` (thrust, volley, shove, charge, cut, talisman, lunge, cleave, bl_<school>). At load: `const GEV = {}; for (const k in GUARD_ITEM) GEV[k] = FX.fxIds(GUARD_ITEM[k]);`. Row: the guard faction gives 'guard'; a rebel passes its variant row (`u.fxRow`, set once at spawn from the unit's variant: 'rebel_olive' / 'rebel_umber' / 'rebel_madder').
| Function (line) | Anchor | Add |
|---|---|---|
| `guardBegin(u, q, dx, dz)` (6715), before `return true` | `u.fx = dx; u.fz = dz; u.st = 1; u.cur = u.atk;` | `u.fxH = FX.fxEvent(GEV[u.atk].tell, m.shape === 'line' ? u.x : u.tx, m.shape === 'line' ? u.z : u.tz, u.fxRow, FX.fxO(dx, dz, m.shape === 'line' ? u.tl : m.radius, m.width, m.windup, 0, u.ty));`. For lunge (死士) the glint card comes with it: `u.fxH2 = FX.fxSecond();` |
| `guardResolve(u)` (6743), after `guardHideTell(u)` | `guardHideTell(u);` | `FX.fxRelease(u.fxH); u.fxH = -1; FX.fxEvent(GEV[u.cur].rel, u.x, u.z, u.fxRow, FX.fxO(u.fx, u.fz, m.shape === 'line' ? u.tl : m.radius, m.width, 0, 0, u.ty));` |
| `guardResolve`, suit loop at `if (dmg > 0) { u.atkAt = G.time; hurtSuit(s, dmg, 'hit', null, u); }` | | `FX.fxEvent(GEV[u.cur].hit, s.x, s.z, u.fxRow, FX.fxO(u.fx, u.fz, 0, 0, 0, 0, s.y));` |
| `fzMend(u, m)` (6899), per mended ally | | `FX.fxEvent('r_talisman:hit', o.x, o.z, u.fxRow, FX.fxO());` |
| `fzWear(u)` (6908), when it stalls | | `FX.fxEvent('r_stall:rel', u.x, u.z, u.fxRow, FX.fxO()); FX.fxEvent('r_stall:state', u.x, u.z, u.fxRow, FX.fxO());` |
| `guardDown(u, rewarded)` (6785), after `guardHideTell(u)` | | `FX.fxKill(u.fxH); FX.fxEvent('unit_break:rel', u.x, u.z, u.fxRow, FX.fxO());` and for the 伍长 (`lead`): `FX.fxEvent('g_break:rel', ...)` plus `FX.fxKill(sq.buffH)` |
| squad buff on (squad spawn with a 伍长) | | `sq.buffH = FX.fxEvent('g_buff:state', L.x, L.z, 'guard', FX.fxO());`, then fxMove it with the 伍长 in the guard step |
| 盾 block (`guardTakenK`, 6775, where `G.guardBlocks++`) | | `FX.fxEvent('g_block:hit', u.x, u.z, 'guard', FX.fxO());` |
| player takes a rebel charge (`fzGrant`, 6914) | | `FX.fxEvent('r_charge:rel', s.x, s.z, s.school, FX.fxO());` |
| `clearGuards()` | | `FX.fxKill(u.fxH)` per unit (or one `FX.fxClear()` in reset, section 4) |

### 3c. Suits (KITS; the player and the bots share one path per kind)
| Function (line) | Anchor | Add |
|---|---|---|
| `hitTarget(by, d, n, basic, sk)` (2081): the one home for every suit blow that lands | after `if (d.kind === 'suit' && counterHit(...)) return false;` | `if (by.kit) FX.fxEvent(sk && sk.fx ? sk.fx.hit : by.kit.attack.fx.hit, d.x, d.z, by.school, FX.fxO(d.x - by.x, d.z - by.z, 0, 0, 0, 0, d.y));` |
| `skillHit(s, sk, d, dx, dz)` (6424): skill landings that skip hitTarget | first line | the same hit call with `sk.fx.hit` (only if skillHit does not call hitTarget; INT checks once) |
| `basicAttack(s, d)` (4666): the swing | after `s.castAt = G.time;` | melee kits (`at.closeR` within range, or `at.range <= CONFIG.MELEE_M`): `FX.fxEvent(at.fx.rel, s.x, s.z, s.school, FX.fxO(d.x - s.x, d.z - s.z, 0, 0, 0, 0, s.y));`. Ranged (ru far, mo, yinyang, za, ming wheel, zongheng): `s.fxBolt = FX.fxEvent(at.fx.trail, ...)`, then `fxMove(s.fxBolt, x, z, y)` from the orb, wheel or arrow step, and `fxKill` when it lands or drops |
| `castSkill(slot, tx, tz)` (2016) and `botUseSkills` (6264): the two cast dispatch chains | just before `if (sk.self) castSelf(...)` (2041 and 6312) | `fxCast(P or b, sk, x, z, dx, dz)`: one new helper (below), so the player and the bots share it |
| delayed skills (`PEND` 2048 / `b.pend` 6324; mo W 0.6 s, yy W 0.8 s) | where the delay ends and the skill applies | `FX.fxRelease(s.fxTellH); FX.fxEvent(sk.fx.rel, x, z, s.school, FX.fxO(dx, dz, sk.radius))` |
| `counterHit(s, basic, by, src, n)` (4591): a 道 counter succeeds | where it returns true | `FX.fxEvent(s.rouT > 0 ? 'dao_q:hit' : 'dao_w:hit', s.x, s.z, s.school, FX.fxO());` |
| stances and states that end early: `endAura`, `endBells`, `hideStance`, `endCircle`, `endFurrow`, `endTaiji`, `endCord`, `lowerWall` | | `FX.fxKill(s.fxStateH); s.fxStateH = -1;` (one field per suit, since one state is shown at a time; 法 R keeps its aura in `FX.fxSecond()` -> `s.fxStateH2`) |
| 儒 R rings land (`placeBell` / the bell step, rings 0.6/1.3/2.0) | per ring | `FX.fxEvent('ru_r:rel', s.x, s.z, s.school, FX.fxO(0, 1, sk.radius));` and re-arm the ring tell for the next ring: `FX.fxEvent('ru_r:tell', ..., FX.fxO(0, 1, sk.radius, 0, nextGap))` with a sound-free copy (item `ru_r` plays its bells once at the cast; see 3e) |
| `suitDown(s, cause, by)` (4341) | | `FX.fxKill(s.fxStateH); FX.fxEvent('suit_break:rel', s.x, s.z, s.school, FX.fxO()); FX.fxEvent('suit_break:state', ...)` |
| 道 passive turns unseen (wuwei on) | | `FX.fxEvent('dao_p:state', s.x, s.z, 'dao', FX.fxO())` |
| 农 passive eats a sprout | | `FX.fxEvent('nong_p:hit', s.x, s.z, 'nong', FX.fxO())` |
| `gainCharge(s, v)` (2120): the player's meter reaches full | when `s === P` and it crosses `CONFIG.ULT.full` | `FX.fxEvent('ult_ready:rel', P.x, P.z, '', null);` |
| `hurtSuit(s, n, ...)` (4322), for the player | after `const lost = ...` | `if (s === P && lost > 0) FX.fxEvent('p_hurt:hit', P.x, P.z, '', null);` |

The helper (index.html, next to castSelf; "one home" for both cast chains; no allocation):
```js
// One home for a cast's cue (player and bots): the tell for delayed or windup skills, else the release, plus the skill's state card.
function fxCast(s, sk, x, z, dx, dz) {
  const f = sk.fx, o = FX.fxO(dx, dz, sk.type === 'line' ? sk.range : sk.radius, sk.width, sk.delay || sk.tellS || 0, 0, s.y);
  if (f.tell) s.fxTellH = FX.fxEvent(f.tell, sk.type === 'line' ? s.x : x, sk.type === 'line' ? s.z : z, s.school, o);
  else if (f.rel) FX.fxEvent(f.rel, s.x, s.z, s.school, o);
  if (f.state) { s.fxStateH = FX.fxEvent(f.state, s.x, s.z, s.school, FX.fxO(dx, dz, sk.radius, sk.width, sk.dur || sk.stance || 0, 0, s.y)); s.fxStateH2 = FX.fxSecond(); }
}
```
Following states (aura, shield, the 势 ring) move with the suit in its step: `if (s.fxStateH >= 0) FX.fxMove(s.fxStateH, s.x, s.z, s.y);`.

### 3d. Palace pieces and hazards (fixed rows)
| Function (line) | Anchor | Add |
|---|---|---|
| `hazardStep(h, dt)` (2745), state 0 -> 1 | `h.state = 1; h.t = 0; h.ring.visible = true;` | `h.fxH = FX.fxEvent(h.statue ? 'statue:tell' : 'lion:tell', h.x, h.z, '', FX.fxO(0, 1, c.radius, 0, c.windup, 0, h.y));` |
| `hazardStep`, state 1 -> 2 (the strike) | `if (h.mark) hazardMark(h); else hazardStrike(h);` | `FX.fxRelease(h.fxH); FX.fxEvent(h.statue ? 'statue:rel' : 'lion:rel', h.x, h.z, '', FX.fxO(0, 1, c.radius, 0, 0, 0, h.y));` (华表 `h.mark`: no card, owner 25 Nov 02:25) |
| `p2Wake()` (3801) | `g.st = 1; g.t = G2.wakeS;` | `FX.fxEvent('giant_wake:tell', g.x, g.z, '', FX.fxO(0, 1, 0, 0, G2.wakeS));` and when it steps off: `giant_wake:state` |
| `p2Begin(g, k, dx, dz)` (3941) | end of function | `g.fxH = FX.fxEvent(k === 'slam' ? 'giant_slam:tell' : 'giant_sweep:tell', g.x, g.z, '', FX.fxO(dx, dz, k === 'slam' ? m.radius : m.len, m.width, m.windup));` |
| `p2Resolve(g)` (3948) | after `scene.remove(...)` | `FX.fxRelease(g.fxH); FX.fxEvent(k === 'slam' ? 'giant_slam:rel' : 'giant_sweep:rel', g.x, g.z, '', FX.fxO(g.fx, g.fz, k === 'slam' ? m.radius : m.len, m.width));` plus `giant_slam:state` (dust) for the slam; a suit hit: `giant_slam:hit` / `giant_sweep:hit` at the suit |
| `hitGiant` (3822): the giant breaks | `g.st = 6; g.t = G2.fallS;` | `FX.fxKill(g.fxH); FX.fxEvent('giant_fall:rel', g.x, g.z, '', FX.fxO()); FX.fxEvent('giant_fall:state', g.x, g.z, '', FX.fxO());` |
| `hitVat(v, n)` (3812): cracks | `v.st = 1; v.t = C2.vat.crackS;` | `v.fxH = FX.fxEvent('vat:tell', v.x, v.z, '', FX.fxO(0, 1, C2.vat.r, 0, C2.vat.crackS));` (use the vat's CONFIG radius field) |
| `p2Splash(v)` (3848) | first line | `FX.fxRelease(v.fxH); FX.fxEvent('vat:rel', v.x, v.z, '', FX.fxO(0, 1, C2.vat.r)); FX.fxEvent('vat:state', v.x, v.z, '', FX.fxO());` |
| burn warning: `BURN.st = 1` (3624) | after `BURN.warnAt = G.time` | `FX.fxEvent('burn_warn:tell', d.x, d.z, '', null)` at the first door (it plays her stinger st_burn once). Then `burn_warn:state` every 0.6 s at each door of the wing, from the burn step (a timer in BURN, no allocation) until the fall |
| wing falls: `onWingFall(w)` (3635) | | `FX.fxEvent('burn_fall:rel', d.x, d.z, '', null); FX.fxEvent('burn_fall:state', d.x, d.z, '', null);` per door; `AUD_IN.burnFalling = 1` while the player is in the wing |
| mercury channel look (the state step that sets `M.mercWarn` / `M.mercHot`) | on the change only | `FX.fxEvent(warn ? 'mercury:tell' : 'mercury:rel', m.x, m.z, '', null);` (sound only; the look is the game material) |
| doors: `palDoorLocks()` (3301) and the door open line (2980) | on lock / on open | `FX.fxEvent('door:end', d.x, d.z, '', null)` (lock) / `FX.fxEvent('door:rel', d.x, d.z, '', null)` (open) |
| 鼎 / altar heal starts (altar step, where the heal begins for a suit) | start only | `s.fxHealH = FX.fxEvent('ding:state', a.x, a.z, '', FX.fxO());`, then `FX.fxKill(s.fxHealH)` when the heal stops |
| boons: `grantBoon(u)` (5960) | | `FX.fxEvent('boon:rel', s.x, s.z, '', null)`, plus `boon:state` (heal, regen) or `boon_buff:state` (power, speed, vision; hold = the boon's s) |

### 3e. Her voice: stingers under her lines (9 places, one call each)
`FX.fxVoice(key)` plays the stinger of `STINGER_OF[key]` (docs/AUDIO.md table). Keys with no stinger play nothing. Add it next to each `setText(el.voice, T(key ...))`:
3046 (`pal_voice_core` / `pal_voice_lost`), 3324 (announcements: `e.v` or `e.k`), 3631 (`burn_voice`), 4093 (`voice_wave<i>`: pass the key, not `w.voice`; store `w.voiceKey` at load), 4465 (`DECREES[DEC.key].voice`), 5551 (`showNote(voiceKey, ...)`: covers voice_guard_break, voice_marked, voice_silenced and the rest), 7046 (`voice_wake`), 7056 (`voice_won` / `voice_lost`), 7153 (`voice_royale_lost`).

## 4. Pause, menus, new run, visibility
| Where | Add |
|---|---|
| options menu open / close (section 6) | `G.paused = true; clearInput(); FX.fxPause(true);` / `G.paused = document.hidden; FX.fxPause(G.paused);` |
| `visibilitychange` (7385): `G.paused = document.hidden` | becomes `G.paused = document.hidden \|\| OPT.isOpen();` (sound.js suspends on hidden by itself; cards hold because step() does not run) |
| end screens (`G.phase` won / lost / palend) and the mode and school menus (`G.selecting`) | `FX.fxPause(true)` on show, `FX.fxPause(false)` when play starts again |
| `reset()` (7303) (new run, same page) | `FX.fxClear(); resetIntensity();` plus every `fxH` field set to -1 in the per-unit resets (`clearGuards`, the unit and suit resets) |
| graphics context restored (17b's restore card) | `FX.fxWarm(renderer, camera)` under the card (three re-uploads the textures; the pools keep their arrays) |
| tier change (17b's adjusting card) | `FX.fxSetTier(tier)`. Pools keep their size until the next load; the low tier's skips apply at once |

## 5. Intensity: what drives 0-1 (src/fx/intensity.js, CONFIG.INTENSITY)
Level = the highest condition that holds. It rises at once and falls only after `holdS` (3 s) at the higher level. sound.js smooths it (tau 1.2 s).
| Level | Condition (AUD_IN field, where the game has it) |
|---|---|
| 1.0 peak | `apex` = G.phase is 'wake' or 'hunt'; `burnFalling` = the player's wing is falling with the player inside (`BURN.st === 2` and `PAL.cur` in `BURN.rooms[BURN.wing]`); `suitsLeft` <= 2 (count of SUITS not dead) |
| 0.7 danger | `hpFrac` = P.hp / CONFIG.MAX_HP < 0.5; `giantsAwake` = P2.awake (in the player's room); `burnMine` = BURN.st === 1 and the player's room is in the warned wing |
| 0.5 fight | `sinceFight` = G.time - max(P.castAt, P.hurtAt) < 4 s (add `P.hurtAt = G.time` in hurtSuit for the player; castAt exists) |
| 0.3 near | `rivalsNear` = suits seen in the player's room (palace) or within VISION_R (Rumble); `unitsNear` = guard, rebel or cub units seen there |
| 0.1 explore | none of the above |
Ambience: `fire` = 0.4 + 0.6 x `burnProgress` while `burnMine` (`burnProgress` = (G.time - BURN.warnAt) / CONFIG.BURN.warnS), 0.3 when `burnNear` (any wing warned or burning), else 0. `wind` per room type: bridge 1, court 0.7, garden 0.6, corridor 0.4, hall 0.2, core 0.1, Rumble 0.5.
The inputs are plain numbers written where the game already computes them. stepIntensity reads them once per frame.

## 6. Options / pause menu (owner: "follow lol or dota")
- Build at boot: `const OPT = buildOptions(document.body, T, SND, closeOptions);` with `function openOptions() { if (!CONFIG.OPTIONS.on) return; OPT.open(); G.paused = true; clearInput(); FX.fxPause(true); }` and `function closeOptions() { OPT.close(); G.paused = document.hidden; FX.fxPause(G.paused); }`. Wire `OPT.openBtn.addEventListener('click', openOptions)`; it is the touch button (`#btnOpts`, 44 px, shown on `body.touch` only).
- Esc (keydown handler, line 1873): `if (e.code === 'Escape') { if (aiming) { cancelAim(); ORD.attackMove = false; } else if (OPT.isOpen()) closeOptions(); else if (canOpenMenu) openOptions(); }`. In LoL, Esc cancels an aim first, then opens the menu. Ignore `e.repeat`. Not on the mode or school menus.
- CSS: append `OPT_CSS` (src/audio/options.js) to the one `<style>` block as text. Do not inject it at runtime.
- Controls: Master volume, Music, Effects, and Voice and ambience (one slider drives sound.js `voice` and `amb`); Mute all / Sound on; Resume. Values save on release (`change`) in `empressDecrees.audio` (try/catch in sound.js). Every control is at least 44 px. The arrow keys move a focused slider.
- New TEXT keys (copy into TEXT; tests_draft/fx-map.mjs fails until they exist):
  | Key | Text |
  |---|---|
  | opt_title | Options |
  | opt_sound | Sound |
  | opt_master | Master volume |
  | opt_music | Music |
  | opt_sfx | Effects |
  | opt_voice | Voice and ambience |
  | opt_mute | Mute all |
  | opt_unmute | Sound on |
  | opt_resume | Resume |
  | opt_btn | Menu |
  | opt_hint | Esc returns to the game |
- Dropped from INTEGRATION.md section 8: key B and the snd_mode_* keys (owner 25 Nov: no hotkey). `SND.cycleMode()` stays for debugging only.

## 7. Tests for INT to copy into tests/ (drafts on prep-av: tests_draft/)
| File | What | Result on prep-av |
|---|---|---|
| `static-src.mjs` | The PERFRAME rules of tests/static-check.mjs over src/**/*.js, unchanged, plus a stricter list inside src PERFRAME blocks: object and array literals, closures, template strings, copies, string concatenation, timers. Also mid-line comments, unseeded random and syntax. INT's 17b src scan can take these rules | see the report |
| `fx-map.mjs` | The table parses; every sound exists in SOUNDS; every VFX map item is present (华表 dropped); tells are held >= 0.4 s on a looping card; every tell has a cue; the options keys have text. With index.html: every MOVES, GUARD.moves and bootleg key has an item, every stinger key and every opt_* key is in TEXT | 4 index.html checks SKIP on prep-av (no TEXT keys yet) |
| `fx-runtime.mjs` | Headless Chromium (Linux) on probe/prepav: T1 unlock, T2 render, T3 sound + card, T4 pause, T5 hidden tab, T6 dt clamp, T7 every event and 0 new programs after the warm-up, T8 intensity levels and hold, T9 Esc/slider/save/mute, T10 reload, T12 errors, T13 storage blocked, T14 44 px on phone, T15 low tier, T16 played buffers equal the renders | see the report |
| `mutate.mjs` | 31 mutants, each named to the check that must catch it: every check of static-src, fx-map (the 9 that run without index.html) and fx-runtime has at least one, and 'software GPU' proves the perf gate 'gpu real' fails on a software renderer. Runs on a runner only | see the report |
| `ci_prepav/perfprepav.mjs` | Real-GPU timing (macOS runner): probe reference vs the heavy fight (40-60 live cards, about 70 sounds/s), forward and reversed in one job. Gates: frames measured, errors, budget, 0 new programs, fps/p95/worst, card pass GPU <= 2 ms, cards add <= 3 calls, heavy/ref fps ratio >= 0.85, and the renderer is a real GPU. A failed gate fails the step | see the report |
After wiring, INT points fx-runtime at index.html (the same checks through `window.__game` hooks: `fxStatus`, `SND.status`, the menu), and the T9/T14 selectors stay the same.

## 8. Open items (not decided here)
1. Giant sweep: the owner's hit area (2.5 m over 120 degrees, 25 Nov) has no cone card. The table's default is a strip 2.5 m deep and 4.33 m wide (the 120-degree chord), which shows only the front. The call site passes CONFIG `len` and `width`, so today's 7 x 3 m line shows until 17h changes the hit shape. A cone card would match exactly: a VFX item for the art queue.
2. The 华表 has no card and no sound (decoration only).
3. Smoke stays faint at play size (owner accepted, 25 Nov).
4. The ru R bells: the ru_r sound holds all three rings timed at 0.6/1.3/2.0 s, so the per-ring tells re-armed after the first need a sound-free event. Proposal: INT calls the ring card with `ru_r:rel` only (burst) and keeps the single tell from the cast. The ring stays the game's own mesh between rings, as today.
5. Not run on a real phone or an iPhone (silent switch): first build on a phone, ask which sound is clean.
