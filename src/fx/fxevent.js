// fxEvent: the ONE dispatcher every attack, tell, hit and state calls (PREP-AV 25 Nov; docs/HOOKS-17c.md, docs/VFX.md, docs/AUDIO.md).
// It plays the sound (src/audio/sound.js) and spawns the painted card(s) (src/fx/cards.js) of one event of the table in src/fx/fxmap.js.
// Rules: one instanced draw per atlas (3 in all); fixed pools; no allocation, traversal, name lookup or DOM in fxEvent / fxStep / fxMove;
// nothing runs while paused (fxStep holds the card clock; fxEvent returns -1; sound.js suspends its context); dt in seconds, clamped.
// API (load time): initFx(o), loadFx(), fxWarm(renderer, camera), fxIds(item), fxSetTier(t), fxSetRoom(x, z, r), fxSetCamera(fx, fz), fxDispose().
// API (play): fxEvent(name, x, z, school, opts) -> card handle or -1; fxO(dx, dz, a, b, hold, rate, y) -> the shared opts object;
//             fxStep(dt, paused); fxMove(h, x, z, y); fxRelease(h); fxKill(h); fxSecond(); fxVoice(textKey); fxPause(on); fxClear(); fxStatus().
import { makeCards, loadCards } from './cards.js';
import { parseFx, STINGER_OF, PHASES } from './fxmap.js';

export const FX_CONFIG = {
  // Largest frame step the card clock takes, s (the game's MAX_DT; a long stall never skips a tell).
  dtMax: 0.05,
  // Upright cards sit this far toward the camera from their anchor, m (the swing draws in front of its own caster).
  cardFwd: 0.6,
  // Sine of the play camera pitch (CAM_PITCH_DEG 40): ground directions foreshorten by this on screen (thrust and bolt angles).
  pitchSin: 0.643,
  // Card pools per atlas on desktop tiers (the heavy fight peaked at 100 live of 160, run 45520502493); the low tier halves them.
  pool: { soft_a: 64, soft_b: 48, ground: 48 },
  // Culling sphere radius round the current room, m (moved by fxSetRoom).
  sphereR: 40,
  // Where the cards load from (static files, OpenGame rules).
  base: './assets/vfx/',
  // Feature switch: painted cards on. Off = sounds only (the event table still runs).
  cards: true,
};

const F = { THREE: null, scene: null, snd: null, C: null, meta: null, ev: null, rowIdx: null, t: 0, paused: false, tier: 'medium',
  h2: -1, unknown: 0, events: 0, sounds: 0, spawned: 0, camFx: 0, camFz: 1, ready: false, warmProg: -1, unitR: null, errs: null };
// The one opts object every call site fills through fxO (no object literal per event).
const OPTS = { dx: 0, dz: 1, a: 0, b: 0, hold: 0, rate: 0, y: 0 };
const NONE = { dx: 0, dz: 1, a: 0, b: 0, hold: 0, rate: 0, y: 0 };

// Load time: o = { THREE, scene, snd (the sound.js namespace), tier ('low' | 'medium'), base, pool }. Sounds work at once; cards after loadFx().
export function initFx(o) {
  F.THREE = o.THREE; F.scene = o.scene; F.snd = o.snd || null; F.tier = o.tier || 'medium';
  // The game's CONFIG.FX (one CONFIG block in index.html) overrides these defaults key by key.
  if (o.cfg) for (const k in o.cfg) FX_CONFIG[k] = o.cfg[k];
  if (o.base) FX_CONFIG.base = o.base;
}
// Fetch the atlases and build the pools (under the loading card). Resolves with the table's parse errors (an empty array when clean).
export async function loadFx() {
  const L = await loadCards(F.THREE, FX_CONFIG.base);
  F.meta = L.meta;
  const rowIdx = {};
  L.meta.ramps.rows.forEach((r, i) => { rowIdx[r] = i; });
  const cardIdx = {};
  Object.keys(L.meta.effects).forEach((n, i) => { cardIdx[n] = i; });
  const P = parseFx(cardIdx, rowIdx);
  F.ev = P.ev; F.rowIdx = rowIdx; F.errs = P.errs;
  // Unit sizes per card (radius, length, width) read once from vfx.json.
  F.unitR = new Float32Array(Object.keys(cardIdx).length); F.unitL = new Float32Array(F.unitR.length); F.unitW = new Float32Array(F.unitR.length);
  Object.keys(cardIdx).forEach((n, i) => { const e = L.meta.effects[n]; F.unitR[i] = e.unitRadiusM || e.sizeM[0] / 2; F.unitL[i] = e.unitLenM || e.sizeM[0]; F.unitW[i] = e.unitWidthM || e.sizeM[1]; });
  if (FX_CONFIG.cards) {
    const low = F.tier === 'low', pool = {};
    for (const k in FX_CONFIG.pool) pool[k] = low ? Math.max(8, FX_CONFIG.pool[k] >> 1) : FX_CONFIG.pool[k];
    F.C = makeCards(F.THREE, L.meta, L.tex, L.ramp, { pool, sphereR: FX_CONFIG.sphereR });
    for (const m of F.C.meshes) F.scene.add(m);
    F.C.uTime.value = F.t;
  }
  F.ready = true;
  return P.errs;
}
// Warm-up under the loading card: upload the four textures, draw every card once (so its program and state are met), then clear.
// Returns the number of cards drawn (> 0 proves the warm-up ran).
export function fxWarm(renderer, camera) {
  if (!F.C) return 0;
  const C = F.C;
  for (const p of C.pools) renderer.initTexture(p.mesh.material.uniforms.map.value);
  renderer.initTexture(C.pools[0].mesh.material.uniforms.ramp.value);
  const n = C.kW.length, tx = camera.position.x, tz = camera.position.z - 6;
  for (let k = 0; k < n; k++) C.spawnK(k, tx, 0, tz, 0, 1, 1, 0, 0.2, 1);
  renderer.compile(F.scene, camera);
  renderer.render(F.scene, camera);
  F.warmProg = renderer.info.programs ? renderer.info.programs.length : -1;
  C.clear();
  return n;
}
// Event ids of one item, for call sites that hold them (e.g. sk.fx = fxIds(sk.nameKey.slice(3)) at load). Missing phases are ''.
export function fxIds(item) {
  const o = {};
  for (const ph of PHASES) o[ph] = F.ev && F.ev[item + ':' + ph] ? item + ':' + ph : '';
  return o;
}
export function fxSetTier(t) { F.tier = t; }
// Culling sphere round the room the player is in (room change only).
export function fxSetRoom(x, z, r) { if (F.C) F.C.setSphere(x, 0, z, r || FX_CONFIG.sphereR); }
// Horizontal direction from the camera's target to the camera (unit; on a camera yaw change only). Default: the camera sits at +z.
export function fxSetCamera(fx, fz) { F.camFx = fx; F.camFz = fz; }
export function fxDispose() { if (F.C) { F.C.dispose(); F.C = null; } F.ready = false; }

// PERFRAME-BEGIN (fxO, fxEvent, fxStep, fxMove, fxRelease, fxKill: no allocation, no traversal, no lookup by object name, no DOM)
// Fill the shared opts: dx, dz = facing or aim (unit); a = radius or length m; b = width m; hold = windup or duration s; rate = sound rate; y = floor height.
export function fxO(dx, dz, a, b, hold, rate, y) {
  OPTS.dx = dx === undefined ? 0 : dx; OPTS.dz = dz === undefined ? 1 : dz; OPTS.a = a || 0; OPTS.b = b || 0;
  OPTS.hold = hold || 0; OPTS.rate = rate || 0; OPTS.y = y || 0;
  return OPTS;
}
// One event: its sound at x, z (spatial) and its card(s). school = the caster's school or row name (ignored by fixed-row items).
// Returns the first card's handle (-1 when none); the second card's handle is read with fxSecond().
export function fxEvent(name, x, z, school, opts) {
  F.h2 = -1;
  if (F.paused || !F.ev) return -1;
  const e = F.ev[name];
  if (e === undefined) { F.unknown++; return -1; }
  F.events++;
  const o = opts || NONE;
  if (e.snd !== '' && F.snd !== null && F.snd.play(e.snd, x, z, o.rate > 0 ? o.rate : e.rate)) F.sounds++;
  if (F.C === null || e.cards.length === 0) return -1;
  const r = e.rowFixed || !school ? e.row : F.rowIdx[school];
  const row = r === undefined ? e.row : r;
  const h = spawnCard(e.cards[0], e.phase, x, z, row, o);
  if (e.cards.length > 1) F.h2 = spawnCard(e.cards[1], e.phase, x, z, row, o);
  return h;
}
function spawnCard(c, phase, x, z, row, o) {
  const C = F.C, k = c.k, y = o.y, ground = C.kGround[k] === 1;
  const hold = o.hold > 0 ? o.hold : c.h;
  // The low tier skips smoke states and endless heal loops (docs/VFX.md phone tier).
  if (F.tier === 'low' && ((c.card === 'smoke' && phase === 'state') || (c.card === 'heal' && hold === 0))) return -1;
  F.spawned++;
  if (ground) {
    if (c.card === 'strip') {
      const len = o.a > 0 ? o.a : c.l, w = o.b > 0 ? o.b : c.w;
      return C.spawnK(k, x, y, z, row, w / F.unitW[k], len / F.unitL[k], Math.atan2(o.dx, -o.dz), hold, 1);
    }
    const rad = o.a > 0 ? o.a : (c.r > 0 ? c.r : 1);
    return C.spawnK(k, x, y, z, row, rad / F.unitR[k], rad / F.unitR[k], Math.atan2(o.dx, -o.dz), hold, 1);
  }
  // Upright: toward the camera by cardFwd; screen direction of the ground direction (dx, dz) for thrust, bolt and mirroring.
  const ux = x + F.camFx * FX_CONFIG.cardFwd, uz = z + F.camFz * FX_CONFIG.cardFwd;
  const scx = o.dx * F.camFz - o.dz * F.camFx, scy = -(o.dx * F.camFx + o.dz * F.camFz) * FX_CONFIG.pitchSin;
  if (c.card === 'thrust' || c.card === 'bolt') {
    const len = o.a > 0 ? o.a : c.l, sx = len > 0 ? len / F.unitL[k] : c.s, w = o.b > 0 ? o.b : c.w, sy = w > 0 ? w / C.kH[k] : (c.card === 'bolt' ? c.s : 1);
    return C.spawnK(k, ux, y, uz, row, sx, sy, Math.atan2(scy, scx), hold, 1);
  }
  if (c.card === 'burst' && (c.r > 0 || o.a > 0)) {
    const sc = (o.a > 0 ? o.a : c.r) / F.unitR[k];
    return C.spawnK(k, ux, y, uz, row, sc, sc, 0, hold, 1);
  }
  const mir = c.card === 'slash' && scx < 0 ? -1 : 1;
  return C.spawnK(k, ux, y, uz, row, c.s * mir, c.s < 0 ? -c.s : c.s, 0, hold, 1);
}
// Advance the card clock by the frame's dt (s, clamped); paused (menu, hidden tab, end screen) holds it, so every card freezes.
export function fxStep(dt, paused) {
  if (paused || F.paused) return;
  F.t += dt > FX_CONFIG.dtMax ? FX_CONFIG.dtMax : (dt > 0 ? dt : 0);
  if (F.C !== null) F.C.uTime.value = F.t;
}
// Follow a body (bolt in flight, aura on a walking suit). Upright cards keep their offset toward the camera.
export function fxMove(h, x, z, y) {
  if (F.C === null || h < 0) return;
  const g = F.C.kGround[F.C.pools[h >> 8].kc[h & 255]] === 1;
  F.C.move(h, g ? x : x + F.camFx * FX_CONFIG.cardFwd, y || 0, g ? z : z + F.camFz * FX_CONFIG.cardFwd);
}
export function fxRelease(h) { if (F.C !== null) F.C.release(h); }
export function fxKill(h) { if (F.C !== null) F.C.kill(h); }
export function fxSecond() { return F.h2; }
// Her stinger for a TEXT voice key (keys with no stinger stay silent). Returns true when it played.
export function fxVoice(key) {
  const s = STINGER_OF[key];
  if (s === undefined || F.paused || F.snd === null) return false;
  return F.snd.play(s);
}
// PERFRAME-END

// Pause menu, end screens: the card clock holds and the audio context suspends (sound.js); resume undoes both.
export function fxPause(on) {
  F.paused = !!on;
  if (F.snd !== null) { if (F.paused) F.snd.pause(); else F.snd.resume(); }
}
// New run or scene change: every card off, counters kept.
export function fxClear() { if (F.C !== null) F.C.clear(); F.h2 = -1; }
// Read-only state for tests and the debug line (allocates: never per frame).
export function fxStatus() {
  return { ready: F.ready, t: F.t, paused: F.paused, tier: F.tier, live: F.C ? F.C.live() : 0, events: F.events, sounds: F.sounds, spawned: F.spawned,
    unknown: F.unknown, errs: F.errs ? F.errs.length : -1, items: F.ev ? Object.keys(F.ev).length : 0, draws: F.C ? F.C.meshes.length : 0, warmProg: F.warmProg };
}
// For tests: the parsed table (names, sounds, cards) and the three meshes.
export function fxTable() { return F.ev; }
export function fxMeshes() { return F.C ? F.C.meshes : []; }
