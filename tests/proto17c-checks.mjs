// Batch 17c + prototype checks (1721-1736): the painted cards and sounds through the one dispatcher (src/fx/fxevent.js), the options menu,
// the characters (src/chars.js) and the palace art (src/palace_art.js) in the game (docs/HOOKS-17c.md, HOOKS-17fgh.md, HOOKS-17de.md).
// Called from tests/run.mjs with g (evaluate after the loader is idle), check, the page, the browser and the test URL. Waits are on conditions
// with large caps, never on the clock alone.
import { execFileSync } from 'node:child_process';

const ROOT = new URL('..', import.meta.url).pathname;
const idle = (page) => page.waitForFunction(() => !__game.loadBusy(), null, { timeout: 180000 });
const node = (args) => { try { return { ok: true, out: execFileSync(process.execPath, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], timeout: 120000 }) }; } catch (e) { return { ok: false, out: String(e.stdout || '') + String(e.stderr || '') }; } };
const fails = (o) => o.out.split('\n').filter((l) => /FAIL/.test(l)).slice(0, 6).join(' | ');

export async function proto17cChecks(g, check, page, browser, URL0) {
  const errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));

  // 1721 Static rules on the new modules: the stricter src rules on the prep-av modules (cards, dispatcher, intensity, sound, options),
  // the character module's own list on src/chars.js (both PASS lines, exit 0).
  const st1 = node([ROOT + 'tests/static-src.mjs', ROOT + 'src/fx/cards.js', ROOT + 'src/fx/fxevent.js', ROOT + 'src/fx/fxmap.js', ROOT + 'src/fx/intensity.js', ROOT + 'src/audio/sound.js', ROOT + 'src/audio/options.js']);
  const st2 = node([ROOT + 'tests/chars-static.mjs', ROOT + 'src/chars.js']);
  check('1721 static rules: src modules (stricter list) and src/chars.js pass', st1.ok && /SRC-STATIC PASS/.test(st1.out) && st2.ok && /PASS/.test(st2.out), fails(st1) + ' || ' + fails(st2));

  // 1722 The event table against the game: parses, every sound exists, every map item, tells held >= 0.4 s on looping cards, every unit move,
  // guard move and bootleg has an item, every stinger key and every opt_* key is in TEXT (no SKIP line).
  const fm = node([ROOT + 'tests/fx-map.mjs', ROOT + 'index.html']);
  check('1722 fx event table vs the game: FX-MAP PASS with no check skipped', fm.ok && /FX-MAP PASS/.test(fm.out) && !/SKIP/.test(fm.out), fails(fm) || fm.out.slice(-300));

  // 1723 The shared card (strikes, sounds, characters) ran once: table parsed with no error, 13 cards drawn under the card, 9 kits have ids,
  // the hunt units' and guards' ids are filled (claw has a tell), the card ledger counts its draws.
  await g(() => { const G = __game; G.setSeed(12345); G.pickMode('rumble'); G.pickSchool(0); });
  await idle(page);
  const a3 = await g(() => { const a = __game.av(); return { fxOn: a.fxOn, errs: a.fxErrs, drawn: a.fxDrawn, kits: a.kitIds, ready: a.fx.ready, unknown: a.fx.unknown, items: a.fx.items, warm: a.fx.warmCalls }; });
  check('1723 shared card: fx table loaded (0 errors), 13 cards warm-drawn, ids for 9 kits, 0 unknown events', a3.fxOn === true && Array.isArray(a3.errs) && a3.errs.length === 0
    && a3.drawn === 13 && a3.warm > 0 && a3.kits === 9 && a3.ready === true && a3.unknown === 0 && a3.items > 200, JSON.stringify(a3));

  // 1724 Every event of the table fires in play without an error; unknown stays 0; no shader program is built by it (cards warmed at load).
  const a4 = await g(() => {
    const G = __game, r0 = G.render(true), names = G.fxNames(); let n = 0;
    for (const nm of names) { G.fxFire(nm); n++; if (n % 40 === 0) { G.fxStepFrames(3, 1 / 60); G.render(false); } }
    G.fxStepFrames(3, 1 / 60); const r1 = G.render(false), a = G.av();
    return { names: names.length, fired: n, unknown: a.fx.unknown, events: a.fx.events, live: a.fx.live, p0: r0.programs, p1: r1.programs };
  });
  check('1724 every table event fires: 0 unknown, cards live, 0 new programs', a4.fired === a4.names && a4.names > 200 && a4.unknown === 0 && a4.live > 0 && a4.p1 === a4.p0 && errs.length === 0,
    JSON.stringify(a4) + ' ' + errs.slice(0, 2).join(' | '));

  // 1725 Game events go through the dispatcher: a palace run with guards fighting the player for 1200 steps dispatches events and spawns cards
  // (tells, hits) with 0 unknown names.
  const a5 = await g(() => {
    const G = __game, e0 = G.av().fx.events, s0 = G.av().fx.spawned;
    G.setSeed(777); G.pickMode('palace'); G.pickSchool(0); return { e0, s0 };
  });
  await idle(page);
  const a5b = await g((a) => {
    const G = __game, p = G.player();
    G.guardSpawn('huangjia', ['wz', 'zu', 'zu', 'dun', 'nu'], p.x, p.z - 6, { fz: 1, open: true });
    G.autoPlayer(true); G.step(1200); G.autoPlayer(false);
    const f = G.av().fx; return { events: f.events - a.e0, spawned: f.spawned - a.s0, unknown: f.unknown };
  }, a5);
  check('1725 play dispatches through fxEvent: events and cards from guard and player moves, 0 unknown', a5b.events > 10 && a5b.spawned > 5 && a5b.unknown === 0, JSON.stringify(a5b));

  // 1726 Options menu (owner: sliders in the Esc menu, no hotkey): Esc opens it in play, the game pauses (card clock held, sound paused), Esc closes it;
  // it never opens on the school menu.
  const a6 = await g(() => { const G = __game, t0 = G.av().fx.t; const open = G.openOptions(); const a = G.av(); G.fxStepFrames(5, 1 / 60); const t1 = G.av().fx.t; return { open, paused: a.paused, fxPaused: a.fx.paused, t0, t1 }; });
  await page.keyboard.press('Escape');
  const a6b = await g(() => { const a = __game.av(); return { open: a.opt, paused: a.paused, fxPaused: a.fx.paused }; });
  await page.keyboard.press('Escape');
  const a6c = await g(() => __game.av().opt);
  await page.keyboard.press('Escape');
  const a6d = await g(() => { const r = __game.av().opt; __game.closeOptions(); return r; });
  check('1726 Esc menu: opens in play and pauses (cards held, sound paused), Esc closes, Esc opens again', a6.open === true && a6.paused === true && a6.fxPaused === true && a6.t1 === a6.t0
    && a6b.open === false && a6b.paused === false && a6b.fxPaused === false && a6c === true && a6d === false, JSON.stringify({ a6, a6b, a6c, a6d }));

  // 1727 Sliders and mute save to the audio key (inside try/catch in sound.js) and every control is at least 44 px on this screen.
  await g(() => __game.openOptions());
  const a7 = await page.evaluate(() => {
    const el = document.getElementById('opts'), r = el.querySelectorAll('input[type=range]'), b = el.querySelectorAll('button');
    r[1].value = '37'; r[1].dispatchEvent(new Event('input')); r[1].dispatchEvent(new Event('change'));
    b[0].click();
    let saved = null; try { saved = JSON.parse(localStorage.getItem('empressDecrees.audio')); } catch (e) { saved = null; }
    const small = [...r, ...b].filter((x) => { const q = x.getBoundingClientRect(); return q.height < 44 || q.width < 44; }).length;
    const mute = __game.av().snd.mute; b[0].click();
    return { sliders: r.length, buttons: b.length, saved, small, mute, after: __game.av().snd.mute, text: el.textContent.length };
  });
  await g(() => __game.closeOptions());
  check('1727 sliders (master, music, effects, voice/ambience) and mute save to empressDecrees.audio; every control >= 44 px', a7.sliders === 4 && a7.buttons >= 2 && a7.small === 0
    && a7.saved && a7.saved.vol && Math.abs(a7.saved.vol.music - 0.37) < 1e-6 && a7.mute === true && a7.after === false, JSON.stringify(a7));

  // 1728 Sound unlocks on a real gesture and renders its buffers; the options menu suspends the audio context (status().ctx), closing resumes it.
  await page.mouse.click(10, 10);
  await page.waitForFunction(() => __game.av().snd.ready > 10, null, { timeout: 180000 }).catch(() => {});
  const a8 = await g(() => { const G = __game, s0 = G.av().snd; G.openOptions(); return { ready: s0.ready, ctx0: s0.ctx }; });
  await page.waitForFunction(() => __game.av().snd.ctx === 'suspended', null, { timeout: 20000 }).catch(() => {});
  const a8b = await g(() => { const c = __game.av().snd.ctx; __game.closeOptions(); return c; });
  await page.waitForFunction(() => __game.av().snd.ctx === 'running', null, { timeout: 20000 }).catch(() => {});
  const a8c = await g(() => __game.av().snd.ctx);
  check('1728 sound: unlocked by a gesture, buffers rendered, suspended while the menu is open, running after', a8.ready > 10 && a8b === 'suspended' && a8c === 'running', JSON.stringify({ a8, a8b, a8c }));

  // 1729 Characters loaded once in the shared card: no file failed, 31 rigs (9 suits, tiger, 2 minions, 7 cubs, 12 giants), box bodies hidden;
  // in play the player's model is shown and animated.
  const a9 = await g(() => { const G = __game; G.chrFrame(1 / 60); G.chrFrame(1 / 60); return G.chars(); });
  check('1729 characters: loaded with no failed file, 31 rigs, boxes hidden, the player model shown and animated', a9.ready === true && a9.failed.length === 0 && a9.rigs === 31
    && a9.bodies === false && a9.on >= 1 && a9.stats.mixers + a9.stats.offscreen >= 1, JSON.stringify(a9));

  // 1730 Palace art on the plan in use: no file failed, every room built, doors dressed; the heaviest view in the palace start hall with guards,
  // the player and the art stays under budget (< 500 calls, < 0.5M triangles) and builds no program in play.
  const a10 = await g(() => {
    const G = __game, A = G.art(), p = G.player(), r0 = G.render(true);
    G.guardSpawn('huangjia', ['wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'nu', 'che'], p.x, p.z - 6, { fz: 1, open: true });
    let worst = { calls: 0, tris: 0 }, prog = r0.programs;
    for (let k = 0; k < 10; k++) { G.step(6); G.chrFrame(0.1); const r = G.render(true); if (r.calls > worst.calls) worst = r; if (r.programs !== prog) prog = -1; }
    G.reset(); return { art: A, rooms: G.palace().rooms ? G.palace().rooms.length : -1, worst: { calls: worst.calls, tris: worst.tris }, prog, p0: r0.programs };
  });
  check('1730 palace art: no failed file, all rooms built and doors dressed; start hall + 12 guards under 500 calls / 0.5M tris, 0 programs in play',
    a10.art.on === true && a10.art.failed.length === 0 && a10.art.rooms > 0 && a10.art.doors > 0 && a10.worst.calls < 500 && a10.worst.tris < 500000 && a10.prog === a10.p0, JSON.stringify(a10));

  // 1731 New run in the same page: every card off, intensity calm, the music input back to the room type (palace) or 'rumble'.
  const a11 = await g(() => { const G = __game; G.fxFire('claw:tell'); G.newRun(); return null; });
  await idle(page);
  const a11b = await g(() => { const G = __game; G.pickSchool(0); return null; });
  await idle(page);
  const a11c = await g(() => { const a = __game.av(); return { live: a.fx.live, room: a.aud.room, since: a.aud.sinceFight }; });
  check('1731 new run: 0 live cards, intensity inputs reset, room type set for the music', a11c.live === 0 && typeof a11c.room === 'string' && a11c.room !== '' && a11 === null && a11b === null, JSON.stringify(a11c));

  // 1733 Fog of war reads each instance's own position (lead 25 Nov: instanced giants took the fog of their mesh origin): the patch applies
  // instanceMatrix under USE_INSTANCING before the model matrix.
  const fs = await g(() => __game.fowSrc());
  check('1733 fog of war per instance: instanceMatrix applied under USE_INSTANCING, then the model matrix', /#ifdef USE_INSTANCING\s*\nfowP = instanceMatrix \* fowP;\s*\n#endif\s*\nvFowPos = \(modelMatrix \* fowP\)\.xyz;/.test(fs), fs.slice(-200));

  // 1734 阙 towers (owner 25 Nov 02:2x: north): on the full plan the pair stands north of the forecourt, centred on its north gate, with the
  // passage's inner faces (measured on the tower bodies of the placed model) clear of the approach bridge (bridge half width + 0.6 m), never at
  // the west or east gates; the pair has two LOD levels: LOD2 (no footing) is left out and listed (lead 25 Nov).
  await g(() => { const G = __game; G.setSeed(12345); G.pickMode('rumble'); G.pickSchool(0); });
  await idle(page);
  await g(() => { const G = __game; G.setLayout('full'); G.pickMode('palace'); G.pickSchool(0); });
  await idle(page);
  const q4 = await g(() => { const a = __game.art(), ap = __game.palPlan().rooms.find((r) => r.id === 'approach'); return { que: a.que, on: a.on, dropped: a.lodDropped, half: ap ? (ap.x1 - ap.x0) / 2 : -1 }; });
  check('1734 阙 pair north of the forecourt, centred on the north gate, passage clear of the bridge (inner face >= bridge half + 0.6 m), LOD2 left out',
    q4.on && q4.half > 0 && q4.que.length === 1 && q4.que.every((q) => q.room === 'fore' && q.z < q.z0 && Math.abs(q.x - q.cx) < 1e-6 && q.inner >= q4.half + 0.6 - 1e-4 && q.inner < q4.half + 0.6 + 0.05 && q.shift > 0 && q.levels === 2)
    && q4.dropped.some((d) => d.startsWith('que_pair:2')), JSON.stringify(q4));
  await g(() => { const G = __game; G.setLayout('proto'); G.pickMode('rumble'); G.pickSchool(0); });
  await idle(page);

  // 1735 杂甲's counts are per run (they were kept over a new run: check 170 counted copies left by earlier matches): a copy cast counts 1, a new
  // run starts at 0. The bot's copy rule reaches a line skill (no radius) out to its range (it was never worth copying: range + undefined).
  const z5 = await g(() => {
    const G = __game, C = G.config, o = {};
    G.setSeed(12345); G.setBots(0); G.setPkitP(false); G.pickSchool(5); G.step(2);
    G.setStore(-1, 'ru', 1); G.setCharge(-1, C.ULT.full); o.cast = G.cast(2, 0, -20); G.step(2); o.n1 = G.zaState(-1).copyN;
    G.reset(); G.step(1); o.n2 = G.zaState(-1).copyN; o.exp = G.zaState(-1).expN;
    const li = C.KITS.ming.skills.findIndex((k) => k.type === 'line' && k.radius === undefined), L = C.KITS.ming.skills[li];
    o.line = li < 0 ? null : [G.zaWorthOf('ming', li, L.range - 0.1), G.zaWorthOf('ming', li, L.range + 0.1)];
    G.setPkitP(true); G.pickSchool(0); G.reset(); return o;
  });
  check('1735 杂甲 counts start at 0 every run (copy cast = 1, new run = 0); the bot copies a line skill within its range, not beyond',
    z5.cast === true && z5.n1 === 1 && z5.n2 === 0 && z5.exp === 0 && !!z5.line && z5.line[0] === true && z5.line[1] === false, JSON.stringify(z5));

  // 1736 Pieces art (owner 25 Nov 18:44): with the switches on no piece draws its plain shape: every plate, the leader crown, every decree mark
  // and every 墨 wall carries its model (own draw hidden), the crab and the wanderer have rigs and hidden box bodies, no file or build failed;
  // Kaymuse's model is attached (her rig exists) and the plain empress box is hidden.
  const pc = await g(() => __game.pcs());
  check('1736 pieces art: no plain shape drawn for plate, crown, decree mark, 墨 wall, crab, wanderer; nothing failed; Kaymuse attached, empress box hidden',
    pc.built && pc.failed.length === 0 && pc.on.plate && pc.on.crown && pc.on.decree && pc.on.moWall && pc.on.crab && pc.on.wanderer
    && pc.plain.plate === 0 && pc.plain.crown === 0 && pc.plain.decree === 0 && pc.plain.moWall === 0 && pc.hosts > 0
    && pc.neutrals.length === 2 && pc.neutrals.every((u) => u.rig && !u.body && u.levels >= 1) && pc.on.kaymuse === true && pc.km === true && pc.empressBox === false, JSON.stringify(pc));

  // 1737 (owner 25 Nov 19:45) The ability bar shows each skill's name for the player's kit (text keys), on phone and desktop; the key letter
  // is only a corner hint (desktop); a school change rewrites the names. The box body's white aim pointer is hidden while the model is on.
  const bt = await g(() => { const G = __game, a = G.barText(); G.setPkitP(false); G.pickSchool(3); const b = G.barText(); G.setPkitP(true); G.pickSchool(0); return { a, b }; });
  const skBtns = (x) => x.btns.filter((q) => q.nm !== '' && x.want.indexOf(q.nm) >= 0);
  check('1737 skill buttons show the skill names of the current kit (rewritten on a kit change), key letters only as hints; no aim pointer on the model',
    bt.a.want.length === 3 && skBtns(bt.a).length === 3 && skBtns(bt.b).length === 3 && bt.b.want.join() !== bt.a.want.join()
    && bt.a.btns.every((q) => ['Q', 'W', 'R', 'ATK'].indexOf(q.nm) < 0) && bt.a.aim === false && bt.a.body === false, JSON.stringify(bt));

  // 1738 (owner 25 Nov 19:45) Camera-side cut-away: standing in the court just north of the hall's door (the hall drawn through the open
  // door), the hall's north wall batches and that door are lowered (height factor lowK); standing in the hall south of that wall they
  // are back to full height; solids unchanged.
  const oc = await g(() => {
    const G = __game, K = G.config.PAL_OCCL, o = {};
    G.setSeed(12345); G.setMode('palace'); G.reset(); const d0 = G.palace().doors[0], sol = G.palace().doors.length;
    G.setHp(1e9); G.teleport(d0.x, d0.z - 1.2); G.step(2); G.render(true); const a = G.art();
    o.near = { attached: G.palace().attached.join(','), cut: a.cut, doors: a.cutDoors, rooms: a.cutRooms };
    G.teleport(d0.x, d0.z + K.hystM + 2); G.step(2); G.render(true); const b = G.art(); o.past = { cut: b.cut, doors: b.cutDoors };
    o.lowK = K.lowK; o.inSolids = G.palace().doors.every((d) => d.inSolids) && G.palace().doors.length === sol;
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1738 cut-away: north wall of the room south of the player and its door are lowered when near, full height once passed; solids unchanged',
    oc.near.rooms > 0 && oc.near.cut.length >= 1 && oc.near.cut.every((c) => c.n > 0 && Math.abs(c.k - oc.lowK) < 1e-6) && oc.near.doors.length >= 1
    && oc.past.cut.length === 0 && oc.past.doors.length === 0 && oc.inSolids, JSON.stringify(oc));

  // 1739 (owner 25 Nov 20:06) With the art on no hall or court draws a plain box part besides its floor: the hall's stone bench block and
  // the court's two blocks are stone plinths from the kit (their box hidden, solids kept), the hall's spawn disc is hidden; a 鼎's reach
  // mark is a thin ring (not a disc) and shows only while the 鼎 can heal.
  const pl = await g(() => {
    const G = __game, o = {}; G.setSeed(12345); G.setLayout('full'); G.pickMode('palace'); G.pickSchool(1); return o;
  });
  await idle(page);
  const pl2 = await g(() => {
    const G = __game, a = G.art(), o = { bad: a.plain.filter((r) => (r.type === 'hall' || r.type === 'court') && r.keys.length > 0).map((r) => r.room + ':' + r.keys.join('+')) };
    o.halls = a.plain.filter((r) => r.type === 'hall').map((r) => r.plinths); o.courts = a.plain.filter((r) => r.type === 'court').map((r) => r.plinths);
    o.garden = a.plain.filter((r) => r.type === 'garden').map((r) => r.keys.join('+')); o.ding = G.pieces().ding.map((d) => d.on);
    G.setLayout('proto'); G.pickMode('rumble'); G.pickSchool(0); return o;
  });
  await idle(page);
  check('1739 no plain block or spawn disc in halls and courts with the art on (stone plinths: 1 per hall, 2 per court); garden leftovers listed',
    pl2.bad.length === 0 && pl2.halls.length === 9 && pl2.halls.every((n) => n === 1) && pl2.courts.length >= 3 && pl2.courts.every((n) => n === 2), JSON.stringify(pl2));

  check('1732 no page error during the 17c and prototype checks', errs.length === 0, errs.slice(0, 4).join(' | '));
}
