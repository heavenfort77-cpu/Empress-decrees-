// Headless checks for the box map. Usage: node tests/run.mjs   (software GPU: correctness and counts only, no real fps)
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }

const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.txt': 'text/plain' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); }
  catch { res.writeHead(404); res.end(); }
}).listen(0);
// bots=0: the map-test checks run with the player alone; the bot checks (56+) set the bots themselves.
// Batch 16 ticket 03 (game changed on purpose): the default pick (儒甲) now has its own kit, so pkit=placeholder keeps the player on the placeholder kit
// the map and match checks were written for; the 儒甲 checks switch it off with __game.setPkitP(false).
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder`;

const results = [], SIMS = [];
function check(name, ok, detail) { results.push({ name, ok: !!ok, detail }); }

const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
const errors = [];
page.on('pageerror', (e) => errors.push(String(e)));
page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
const g = (fn, arg) => page.evaluate(fn, arg);

try {
  await page.goto(URL0);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  check('01 load without errors', errors.length === 0, errors.slice(0, 3).join(' | '));
  // Fixed seed so the marble bags draw the same way every run.
  await g(() => { __game.setSeed(12345); __game.reset(); });

  const base = await g(() => __game.render(true));
  // Batch 14: bot count read from CONFIG (nine schools: player + 8 bots, owner 23 Nov 20:03); NS = suits in a full match.
  const NB = await g(() => __game.config.BOTS.count), NS = NB + 1;
  check('02 budget follow view (calls<500, tris<500k)', base.calls < 500 && base.tris < 500000, `calls ${base.calls}, tris ${base.tris}`);
  await g(() => __game.setView('overview'));
  const ov = await g(() => __game.render(true));
  check('03 budget overview, all sections (calls<500, tris<500k)', ov.calls < 500 && ov.tris < 500000, `calls ${ov.calls}, tris ${ov.tris}`);
  await g(() => __game.setView('follow'));

  const K = await g(() => __game.K);
  const S = (pts) => pts.map(([x, z]) => [x * K, z * K]);

  // 04 Reachability over layers: BFS on (cell, floor) using the real walking rule (drops allowed, climbs only by ramps).
  const reach = await g(() => {
    const G = __game, st = 0.75, x0 = -78, z0 = -80, nx = 210, nz = 175;
    const fl = G.floors(), seen = new Set(), q = [], hit = new Set();
    const sp = G.spawns[G.config.PLAYER_SPAWN];
    const si = Math.round((sp[0] - x0) / st), sj = Math.round((sp[1] - z0) / st);
    const y0 = G.topY(x0 + si * st, z0 + sj * st);
    q.push([si, sj, y0]); seen.add(si + ',' + sj + ',' + G.floorIdx(x0 + si * st, z0 + sj * st, y0));
    while (q.length) {
      const [i, j, y] = q.pop();
      for (const [di, dj] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const a = i + di, b = j + dj; if (a < 0 || b < 0 || a >= nx || b >= nz) continue;
        const x = x0 + a * st, z = z0 + b * st;
        if (!G.canStand(x, z, y)) continue;
        const fi = G.floorIdx(x, z, y), key = a + ',' + b + ',' + fi; if (seen.has(key)) continue;
        seen.add(key); hit.add(fi); q.push([a, b, G.surfAt(fi, x, z)]);
      }
    }
    return fl.map((f, i) => (hit.has(i) ? null : f.sec + '#' + i)).filter(Boolean);
  });
  check('04 every floor (both layers) reachable from the spawn', reach.length === 0, reach.join(' '));
  const voids = await g((pts) => pts.filter(([x, z, y]) => __game.canStand(x, z, y)),
    [...S([[-20, -2], [-20, 10], [20, -2], [8, 12], [-8, 12], [-50, 0], [-8, -23]]).map((p) => [...p, 0]), [0, 32 * K, 4]]);
  check('04b void points are not standable (8 points)', voids.length === 0, JSON.stringify(voids));
  const walls = await g((pts) => pts.filter(([x, z, y]) => __game.canStand(x, z, y)),
    [[-35 * K, -1 * K, 0], [-43 * K, 4 * K, 0], [35 * K, -1 * K, 0], [43 * K, 4 * K, 0]]);
  check('04c terrace and ramp sides are walls from below (4 points)', walls.length === 0, JSON.stringify(walls));

  const walk = async (pts, maxSteps) => g(({ pts, maxSteps }) => {
    const G = __game; let n = 0, k = 0;
    while (k < pts.length && n < maxSteps) {
      const s = G.state(); const dx = pts[k][0] - s.x, dz = pts[k][1] - s.z, d = Math.hypot(dx, dz);
      if (d < 0.6) { k++; continue; }
      G.setMove(dx / d, dz / d); G.step(1); n++;
    }
    G.clearMove(); G.step(30); const s = G.state();
    return { reached: k, of: pts.length, steps: n, x: +s.x.toFixed(2), y: +s.y.toFixed(2), z: +s.z.toFixed(2), zone: s.zone, falling: s.falling, hp: Math.round(s.hp) };
  }, { pts, maxSteps });

  // 05 Bot walk spawn -> south bridge -> centre -> gate -> core hall, no hazard hit.
  await g(() => __game.reset());
  const w1 = await walk(S([[-30, 4], [-20, 4], [-8, 7], [0, -10], [0, -23], [0, -33]]), 5400);
  check('05 bot walk spawn -> bridge -> core hall', w1.reached === w1.of && w1.zone === 'CORE' && w1.hp === 100, JSON.stringify(w1));

  // 06 Roof route: ramp up to y 4, west ramp down to the west courtyard.
  await g((p) => { __game.reset(); __game.teleport(p[0], p[1]); }, [0, 4 * K]);
  const w2a = await walk(S([[0, 12], [0, 22]]), 1800);
  const w2b = await walk(S([[-20, 18], [-34, 18]]), 2400);
  check('06 roof route up and down', w2a.reached === 2 && Math.abs(w2a.y - 4) < 0.01 && w2b.reached === 2 && w2b.zone === 'W2' && w2b.y === 0,
    JSON.stringify({ up: w2a, down: w2b }));
  // 06b Terrace drop: walking off the west terrace lands on the courtyard below with drop damage.
  await g((p) => { __game.reset(); __game.teleport(p[0], p[1]); }, [-33 * K, -3 * K]);
  const drop = await g(() => { const G = __game; G.setMove(0, 1); G.step(90); G.clearMove(); G.step(30); const s = G.state(); return { y: s.y, zone: s.zone, hp: s.hp, falling: s.falling }; });
  const dmg = await g(() => __game.config.DROP_DAMAGE);
  check('06b drop from terrace to courtyard (lands, takes drop damage)', drop.zone === 'W2' && drop.y === 0 && !drop.falling && Math.round(drop.hp) === 100 - dmg, JSON.stringify(drop));
  // 06c Up the west courtyard ramp onto the terrace.
  await g((p) => { __game.reset(); __game.teleport(p[0], p[1]); }, [-43 * K, 10 * K]);
  const w3 = await walk(S([[-43, -3]]), 1200);
  check('06c courtyard ramp up to the terrace', w3.reached === 1 && w3.zone === 'W1' && Math.abs(w3.y - 4) < 0.01, JSON.stringify(w3));
  // 06d Sloped north bridge from the centre up to the terrace.
  await g((p) => { __game.reset(); __game.teleport(p[0], p[1]); }, [-12 * K, -12 * K]);
  const w4 = await walk(S([[-30, -12]]), 1200);
  check('06d sloped bridge centre -> terrace', w4.reached === 1 && w4.zone === 'W1' && Math.abs(w4.y - 4) < 0.01, JSON.stringify(w4));

  // 07 Edge clamp: walking into rails and broken-rail gaps never falls.
  const edges = await g((list) => {
    const G = __game, out = [];
    for (const [x, z, mx, mz] of list) {
      G.reset(); G.teleport(x, z); G.setMove(mx, mz); let fell = false;
      for (let n = 0; n < 240; n++) { G.step(1); if (G.state().falling) fell = true; }
      const s = G.state(), moved = Math.hypot(s.x - x, s.z - z);
      out.push({ x: +s.x.toFixed(2), z: +s.z.toFixed(2), falling: fell, ok: !fell && G.walkable(s.x, s.z, s.y) && moved < 4 });
    }
    G.clearMove(); return out;
  }, [[-20 * K, 4 * K, 0, -1], [-20 * K, 4 * K, 0, 1], [-44 * K, -10 * K, -1, 0], [-36 * K, -19 * K, 0, -1], [0, 26 * K, 0, 1], [8 * K, 26 * K, 0, 1]]);
  check('07 edge clamp (6 edges incl. 3 broken-rail gaps)', edges.every((e) => e.ok), JSON.stringify(edges));

  // 08 Collapse timing: warn shown >= max(0.4, COLLAPSE_WARN_S) before the fall; gone after the fall time.
  await g(() => __game.reset());
  const timing = await g(() => {
    const G = __game, C = G.config, step = C.STEP, out = [];
    const toT = (t) => { const n = Math.round((t - G.state().t) / step); if (n > 0) G.step(n); };
    C.WAVES.forEach((ids, i) => {
      const start = C.FIRST_WAVE_S + i * C.WAVE_INTERVAL_S;
      toT(start - C.COLLAPSE_WARN_S - 0.05); const before = ids.map((id) => G.state().sec[id]);
      toT(start - C.COLLAPSE_WARN_S + 0.05); const warned = ids.map((id) => G.state().sec[id]);
      toT(start - 0.05); const stillWarn = ids.map((id) => G.state().sec[id]);
      toT(start + C.COLLAPSE_FALL_S + 0.1); const s = G.state();
      out.push({ i, ok: before.every((v) => v === 0) && warned.every((v) => v === 1) && stillWarn.every((v) => v === 1)
        && ids.every((id) => s.sec[id] === 3 && !s.inScene[id]) && s.sec.CORE === 0 && s.inScene.CORE });
    });
    return { warnS: C.COLLAPSE_WARN_S, out };
  });
  check('08 collapse warning and removal per wave', timing.warnS >= 0.4 && timing.out.every((o) => o.ok), JSON.stringify(timing));

  // 09 After all waves: core hall and centre north remain, connected.
  const after = await g((K) => {
    const G = __game, s = G.state();
    const left = Object.entries(s.sec).filter(([, v]) => v === 0).map(([k]) => k).sort();
    G.teleport(0, -14 * K); G.setMove(0, -1); G.step(60 * 4); G.clearMove();
    const e = G.state();
    return { left, reachCore: e.zone === 'CORE' && !e.falling };
  }, K);
  check('09 final arena = CORE + C1, reachable', JSON.stringify(after.left) === '["C1","CORE"]' && after.reachCore, JSON.stringify(after));

  // 11 Standing on a falling section: player falls, then respawns in the centre courtyard.
  await g((p) => { __game.reset(); __game.teleport(p[0], p[1]); }, [0, 22 * K]);
  const fall = await g(() => {
    const G = __game, C = G.config, step = C.STEP;
    G.step(Math.round((C.FIRST_WAVE_S + 0.1) / step)); const a = G.state();
    G.step(Math.round((C.RESPAWN_S + 0.1) / step)); const b = G.state();
    return { fellAtCollapse: a.falling, respawnZone: b.zone, fallingAfter: b.falling };
  });
  check('11 fall at collapse then respawn', fall.fellAtCollapse && fall.respawnZone === 'C1' && !fall.fallingAfter, JSON.stringify(fall));

  // 12 New run x3 after full collapses: sections restored, memory flat.
  const mem = await g(() => {
    const G = __game, C = G.config, out = [];
    const end = C.FIRST_WAVE_S + C.WAVES.length * C.WAVE_INTERVAL_S + 2;
    for (let r = 0; r < 3; r++) {
      G.reset(); G.step(Math.round(end / C.STEP)); G.reset();
      const s = G.state(), info = G.render(true);
      out.push({ restored: Object.values(s.sec).every((v) => v === 0) && Object.values(s.inScene).every(Boolean) && s.t === 0 && s.hp === C.MAX_HP, geoms: info.geoms, texs: info.texs });
    }
    return out;
  });
  check('12 new run x3: restored, memory flat', mem.every((m) => m.restored && m.geoms === mem[0].geoms && m.texs === mem[0].texs), JSON.stringify(mem));

  // 18 Tiger statue: tell >= 0.4 s with ring and no damage during it, then strike, damage and knockback; nothing out of range.
  const statue = await g(() => {
    const G = __game, C = G.config, st = G.hazards()[0];
    G.reset(); G.teleport(st.x, st.z + 9); G.step(60); const idle = G.hazards()[0].state;
    G.teleport(st.x, st.z + 4); G.step(1); const tell = G.hazards()[0];
    G.step(Math.round((C.STATUE.windup - 0.05) / C.STEP)); const mid = { hp: G.state().hp, ring: G.hazards()[0].ring };
    G.step(Math.round(0.1 / C.STEP)); const s = G.state();
    G.step(30); const later = G.state();
    return { windup: C.STATUE.windup, idle, tellState: tell.state, tellRing: tell.ring, midHp: mid.hp, midRing: mid.ring, hpAfter: s.hp,
      pushed: Math.hypot(later.x - st.x, later.z - st.z) > 5, ringAfter: G.hazards()[0].ring };
  });
  check('18 statue: tell, strike, knockback, idle out of range', statue.windup >= 0.4 && statue.idle === 0 && statue.tellState === 1 && statue.tellRing
    && statue.midHp === 100 && statue.midRing && statue.hpAfter === 70 && statue.pushed && !statue.ringAfter, JSON.stringify(statue));
  // 19 Stone lion strike.
  const lion = await g(() => {
    const G = __game, C = G.config, l = G.hazards()[1];
    G.reset(); G.teleport(l.x + 2.5, l.z); G.step(1); const t = G.hazards()[1].state;
    G.step(Math.round((C.LION.windup + 0.05) / C.STEP)); return { windup: C.LION.windup, tell: t, hp: G.state().hp };
  });
  check('19 stone lion: tell then strike', lion.windup >= 0.4 && lion.tell === 1 && lion.hp === 80, JSON.stringify(lion));
  // 20 Knockback: through a broken-rail gap into the void (respawn); against a rail stays on the roof.
  const kb = await g((K) => {
    const G = __game, C = G.config;
    G.reset(); G.teleport(0, 40.5); G.knock(0, 14); let fell = false;
    for (let n = 0; n < 60; n++) { G.step(1); if (G.state().falling) fell = true; }
    G.step(Math.round(C.RESPAWN_S / C.STEP) + 5); const a = G.state();
    G.reset(); G.teleport(8 * K, 40.5); G.knock(0, 14); let fell2 = false;
    for (let n = 0; n < 90; n++) { G.step(1); if (G.state().falling) fell2 = true; }
    const b = G.state();
    // Sideways knockback (x axis) through the west terrace gap (added in batch 9a).
    G.reset(); G.teleport(-46 * K + 0.6, -10 * K); G.step(1); const c0 = G.state(); G.knock(-14, 0); let fell3 = false;
    for (let n = 0; n < 60; n++) { G.step(1); if (G.state().falling) fell3 = true; }
    return { gapFell: fell, gapRespawn: a.zone, railFell: fell2, railZone: b.zone, xStart: c0.zone, xFell: fell3 };
  }, K);
  check('20 knockback: broken gaps (z and x) drop into void, rail holds', kb.gapFell && kb.gapRespawn === 'C1' && !kb.railFell && kb.railZone === 'ROOF' && kb.xStart === 'W1' && kb.xFell, JSON.stringify(kb));
  // 21 Altar: heals, a hit pauses healing, empties, refills after the empty time.
  const altar = await g(() => {
    const G = __game, C = G.config, A = C.ALTAR, a = G.altars()[2], sp = (s) => G.step(Math.round(s / C.STEP));
    G.reset(); G.teleport(a.x + 1.2, a.z); G.setHp(50); sp(2); const h1 = G.state().hp;
    G.damage(5); const h2 = G.state().hp; sp(A.hitPauseS - 0.1); const h3 = G.state().hp; sp(0.5); const h4 = G.state().hp;
    G.setHp(1); sp(A.charge / A.rate + 1); const empty = G.altars()[2];
    sp(A.emptyS + 0.2); const refilled = G.altars()[2];
    return { h1: +h1.toFixed(1), h2: +h2.toFixed(1), h3: +h3.toFixed(1), h4: +h4.toFixed(1), emptyOn: empty.on, emptyCharge: empty.charge, refilledOn: refilled.on };
  });
  check('21 altar: heal, hit pause, empty, refill', Math.abs(altar.h1 - 66) < 0.5 && altar.h3 === altar.h2 && altar.h4 > altar.h3
    && !altar.emptyOn && altar.emptyCharge === 0 && altar.refilledOn, JSON.stringify(altar));
  // 22 Death and respawn with full health.
  const death = await g(() => { const G = __game, C = G.config; G.reset(); G.damage(500); const d = G.state().dead; G.step(Math.round((C.RESPAWN_S + 0.1) / C.STEP)); const s = G.state(); return { d, dead: s.dead, hp: s.hp, zone: s.zone }; });
  check('22 death then respawn at full health', death.d && !death.dead && death.hp === 100 && death.zone === 'C1', JSON.stringify(death));
  // 23 Vision: a dummy is seen and drawn inside the vision radius, hidden outside; fog centre follows the player.
  const vis = await g(() => {
    const G = __game, C = G.config, d = G.dummies()[1];
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2); G.render(false); const near = G.dummies()[1], fc = G.fowCenter(), s = G.state();
    G.teleport(d.x, d.z - 5 - C.VISION_R - 6); G.step(2); const far = G.dummies()[1];
    return { nearSeen: near.seen, nearVis: near.visible, farSeen: far.seen, farVis: far.visible, fow: Math.hypot(fc[0] - s.x, fc[2] - s.z) < 0.01 };
  });
  check('23 vision: seen inside radius, hidden outside, fog follows player', vis.nearSeen && vis.nearVis && !vis.farSeen && !vis.farVis && vis.fow, JSON.stringify(vis));
  // 24 Auto-target picks the nearest visible dummy within range only.
  const at = await g(() => {
    const G = __game, C = G.config, d = G.dummies()[1];
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2); const a = G.autoTargetIdx(C.ATTACK.acquire);
    G.teleport(d.x, d.z - 9.5); G.step(2); const b = G.autoTargetIdx(C.ATTACK.acquire);
    return { inRange: a, beyond: b };
  });
  check('24 auto-target: nearest visible in range, none beyond', at.inRange === 1 && at.beyond === -1, JSON.stringify(at));
  // 25 Attack order: chases into range, hits on the interval; broken dummy stands again.
  const atk = await g(() => {
    const G = __game, C = G.config, d = G.dummies()[1], sp = (t) => G.step(Math.round(t / C.STEP));
    G.reset(); G.teleport(d.x, d.z - 6); G.step(2); G.attack(1); sp(3); const hp3 = G.dummies()[1].hp, s = G.state();
    sp(10); const dead = G.dummies()[1].hp; sp(C.DUMMY_RESPAWN_S + 0.2); const back = G.dummies()[1].hp;
    return { hp3, dist: +Math.hypot(s.x - d.x, s.z - d.z).toFixed(2), deadHp: dead, back };
  });
  check('25 attack: chase, hit on interval, dummy stands again', atk.hp3 <= 80 && atk.hp3 % 10 === 0 && atk.dist <= 3 && atk.back === 100, JSON.stringify(atk));
  // 26 Skills: line and circle hit, cooldown blocks recast, delayed ultimate telegraphs then hits, hidden targets are not hit.
  const sk = await g(() => {
    const G = __game, C = G.config, d = G.dummies()[1], sp = (t) => G.step(Math.round(t / C.STEP)), hp = () => G.dummies()[1].hp;
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2);
    const q1 = G.cast(0, d.x, d.z), afterQ = hp(), q2 = G.cast(0, d.x, d.z), cdQ = G.skills()[0];
    sp(C.SKILLS[0].cd + 0.1); const q3 = G.cast(0, d.x, d.z), afterQ2 = hp();
    // Batch 12 (panel, 23 Nov 15:11): W is now a 4 m dash with its burst on landing, so the hit comes when the dash ends (changed on purpose).
    const w = G.cast(1, d.x, d.z); sp(0.3); const afterW = hp();
    // Game changed on purpose (batch 15): R casts only with a full charge meter, so the meter is filled before the cast.
    G.setCharge(-1, C.ULT.full);
    const r = G.cast(2, d.x, d.z), pendNow = G.pending(), beforeR = hp(); sp(C.SKILLS[2].delay + 0.05); const afterR = hp(), pendAfter = G.pending();
    G.reset(); G.teleport(d.x, d.z - C.VISION_R - 2); G.step(2); G.cast(0, d.x, d.z); const hidden = hp();
    return { q1, afterQ, q2, cdQ: +cdQ.toFixed(2), q3, afterQ2, w, afterW, r, pendNow, beforeR, afterR, pendAfter, hidden };
  });
  check('26 skills: hit, cooldown, delayed ultimate, no hit on hidden', sk.q1 && sk.afterQ === 75 && !sk.q2 && sk.cdQ > 5.9 && sk.q3 && sk.afterQ2 === 50
    && sk.w && sk.afterW === 30 && sk.r && sk.pendNow && sk.beforeR === 30 && sk.afterR === 0 && !sk.pendAfter && sk.hidden === 100, JSON.stringify(sk));
  // 27 Pathfinding move orders across layers: spawn -> core hall; centre -> west terrace; west terrace -> roof.
  const nav = await g((K) => {
    const G = __game, C = G.config, out = [];
    const go = (tx, tz, maxS) => {
      const found = G.moveTo(tx, tz), n = G.path().n; let t = 0;
      while (G.path().i < G.path().n && t < maxS) { G.step(30); t += 0.5; }
      const s = G.state(); return { found, n, x: +s.x.toFixed(1), z: +s.z.toFixed(1), y: +s.y.toFixed(1), zone: s.zone, d: +Math.hypot(s.x - tx, s.z - tz).toFixed(2) };
    };
    G.reset(); out.push(go(0, -49.5, 60));
    G.teleport(-12 * K, -12 * K); out.push(go(-45, -15, 60));
    out.push(go(0, 33, 90));
    G.teleport(0, -14 * K); out.push(go(-20 * K, -2 * K, 30));
    return out;
  }, K);
  check('27 pathfinding: core hall, terrace (y 4), roof (y 4); void target ends near it', nav[0].found && nav[0].zone === 'CORE' && nav[0].d < 1
    && nav[1].zone === 'W1' && nav[1].y === 4 && nav[1].d < 1 && nav[2].zone === 'ROOF' && nav[2].y === 4 && nav[2].d < 1 && nav[3].found, JSON.stringify(nav));
  // 28 Cursor ground pick hits flat floors and ramps at the right height.
  const pick = await g((K) => {
    const G = __game, out = [];
    for (const [x, z] of [[0, 33], [-64.5, 6], [-60, 18]]) {
      G.reset(); G.teleport(x, z + 3); G.step(1); G.render(false);
      const y = G.topY(x, z), [nx, ny] = G.project(x, y, z), h = G.ground(nx, ny);
      out.push({ ok: h.ok, err: +Math.hypot(h.x - x, h.y - y, h.z - z).toFixed(3) });
    }
    return out;
  }, K);
  check('28 cursor ground pick: roof, ramp, courtyard (error < 0.1 m)', pick.every((p) => p.ok && p.err < 0.1), JSON.stringify(pick));
  // 29 Desktop key aim: holding Q shows range ring and line, release casts at the cursor; W shows the target circle.
  const key = await g(() => {
    const G = __game, d = G.dummies()[1];
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2); G.render(false);
    const [nx, ny] = G.project(d.x, 1, d.z), a = G.aimKey(0, nx, ny); G.releaseKey(); const hpQ = G.dummies()[1].hp;
    // Batch 12: W dashes 4 m toward the cursor and bursts on landing (changed on purpose): step past the dash before reading.
    const b = G.aimKey(1, nx, ny); G.releaseKey(); G.step(20); const hpW = G.dummies()[1].hp;
    return { q: a.ind, hpQ, w: b.ind, hpW };
  });
  check('29 desktop key aim: indicators, release casts at cursor', key.q[0] && key.q[1] && !key.q[2] && key.hpQ === 75 && key.w[0] && key.w[2] && key.hpW === 55, JSON.stringify(key));
  // 30 Minimap: size, player dot, seen dummy dot, fallen section cleared.
  const mini = await g((K) => {
    const G = __game, C = G.config, d = G.dummies()[1];
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2);
    const size = G.miniSize(), you = G.miniPixel(d.x, d.z - 5), dum = G.miniPixel(d.x, d.z);
    G.teleport(d.x, d.z - 30); G.step(2); const dumHidden = G.miniPixel(d.x, d.z);
    const roofBefore = G.miniPixel(0, 22 * K);
    G.step(Math.round((C.FIRST_WAVE_S + C.COLLAPSE_FALL_S + 0.2) / C.STEP)); const roofAfter = G.miniPixel(0, 22 * K);
    return { size, you, dum, dumHidden, roofBefore, roofAfter, want: C.MINI_W };
  }, K);
  const blue = (p) => p[2] > 200 && p[0] < 120, red = (p) => p[0] > 200 && p[1] < 110;
  check('30 minimap: size, player, seen dummy only, fallen roof cleared', mini.size[0] === mini.want && blue(mini.you) && red(mini.dum) && !red(mini.dumHidden)
    && mini.roofBefore[0] > 120 && mini.roofAfter[0] < 30, JSON.stringify(mini));
  // 31 Desktop UI: 3 skill slots, no full-map button, M does not open the overview.
  await page.keyboard.press('KeyM');
  const ui = await g(() => ({ ...__game.ui(), view: __game.state().view }));
  check('31 desktop: ability bar, no overview for players', ui.bar === 3 && ui.btnMap === 'none' && ui.view === 'follow' && !ui.touch, JSON.stringify(ui));
  // 32 Phone (MLBB): touch layout; tap Q auto-aims and hits; drag W to Cancel does not cast; drag R aims manually.
  {
    const ctx = await browser.newContext({ viewport: { width: 844, height: 390 }, isMobile: true, hasTouch: true });
    const ph = await ctx.newPage(); const perr = []; ph.on('pageerror', (e) => perr.push(String(e)));
    await ph.goto(URL0); await ph.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
    const res = await ph.evaluate(() => {
      const G = __game, d = G.dummies()[1], btns = document.querySelectorAll('#bar .sk');
      G.reset(); G.teleport(d.x, d.z - 5); G.step(2);
      const ev = (el, type, x, y, id) => el.dispatchEvent(new PointerEvent(type, { bubbles: true, pointerId: id, pointerType: 'touch', clientX: x, clientY: y, isPrimary: true }));
      const c = (el) => { const r = el.getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 2]; };
      const [qx, qy] = c(btns[1]); ev(btns[1], 'pointerdown', qx, qy, 11); ev(window, 'pointerup', qx, qy, 11); const tapHp = G.dummies()[1].hp;
      const [wx, wy] = c(btns[2]); ev(btns[2], 'pointerdown', wx, wy, 12);
      const cancel = document.getElementById('cancel'), cancelShown = getComputedStyle(cancel).display !== 'none';
      const [cx, cy] = c(cancel); ev(window, 'pointermove', wx - 30, wy - 30, 12); ev(window, 'pointermove', cx, cy, 12); ev(window, 'pointerup', cx, cy, 12);
      const cdW = G.skills()[1], hpAfterCancel = G.dummies()[1].hp;
      // Game changed on purpose (batch 15): R needs a full charge meter and the cast empties it (no R cooldown in the royale).
      G.setCharge(-1, G.config.ULT.full); const chBefore = G.chargeOf(-1);
      const [rx, ry] = c(btns[3]); ev(btns[3], 'pointerdown', rx, ry, 13); ev(window, 'pointermove', rx, ry - 40, 13); ev(window, 'pointerup', rx, ry - 40, 13);
      return { bar: btns.length, mini: G.miniSize()[0], touch: G.ui().touch, tapHp, cancelShown, cdW, hpAfterCancel, chBefore, chR: G.chargeOf(-1), pend: G.pending() };
    });
    check('32 phone: MLBB buttons, tap auto-aim hits, cancel zone, drag aim casts', res.touch && res.bar === 4 && res.mini === 140 && res.tapHp === 75
      && res.cancelShown && res.cdW === 0 && res.hpAfterCancel === 75 && res.chBefore === 100 && res.chR === 0 && res.pend && perr.length === 0, JSON.stringify(res) + ' ' + perr.join(' | '));
    // 44 Phone: the Hunt button is a 44 px target and a tap starts the hunt.
    const hb = await ph.evaluate(() => {
      const G = __game; G.reset(); const b = document.getElementById('btnHunt'), r = b.getBoundingClientRect();
      const shown = getComputedStyle(b).display !== 'none'; b.click();
      return { shown, w: r.width, h: r.height, phase: G.hunt().phase, hidden: G.huntUi().btn === 'none' };
    });
    check('44 phone: Hunt button 44 px, tap starts the hunt', hb.shown && hb.w >= 44 && hb.h >= 44 && hb.phase === 'wake' && hb.hidden && perr.length === 0, JSON.stringify(hb));
    await ctx.close();
  }

  // ===== Batch 6: apex hunt on boxes (Tiger Demon, 2 minions, skill transfer) =====
  // Helpers inside the page: start a hunt past the wake; mute a unit (all its moves on a long cooldown).
  await g(() => {
    const G = __game, C = G.config;
    window.__h = {
      start() { G.reset(); G.startHunt(); G.step(Math.round(C.APEX.wakeS / C.STEP) + 1); },
      mute(i, except) { for (const k of G.moves) G.unitCd(i, k, k === except ? 0 : 9999); },
      until(cond, max) { let n = 0; while (n < max && !cond(G.hunt())) { G.step(1); n++; } return n; },
    };
  });
  // 33 Hunt start: a warned collapse is called off, statue wakes (mesh and solid gone), gate sealed, player at the entrance, nothing can be hit in the wake.
  const hs = await g(() => {
    const G = __game, C = G.config, K = G.K; G.reset();
    G.step(Math.round((C.FIRST_WAVE_S - 2) / C.STEP)); const warned = G.state().sec.ROOF;
    const blockedBefore = !G.canStand(0, G.hazards()[0].z, 0);
    G.startHunt(); const h0 = G.hunt(), s0 = G.state(), ui0 = G.huntUi();
    const canTarget = G.attackUnit(0); G.hitUnit(0, 50); const hpWake = G.hunt().units[0].hp;
    G.setHp(1e9); G.step(Math.round(10 / C.STEP)); const h1 = G.hunt(), s1 = G.state();
    return { warned, blockedBefore, phase0: h0.phase, roofAfter: s0.sec.ROOF, wave0: s0.waves[0], statue: h0.statue, solid: h0.statueSolid, openNow: G.canStand(0, G.hazards()[0].z, 0), seal: h0.seal,
      atEntry: Math.abs(h0.p.x - C.APEX.entry[0] * K) < 0.01 && Math.abs(h0.p.z - C.APEX.entry[1] * K) < 0.01, hp0: h0.p.hp, canTarget, hpWake, full: C.DEMON.hp,
      boss: ui0.boss, btn: ui0.btn, voice: ui0.voice, phase1: h1.phase, roof10: s1.sec.ROOF, waves10: s1.waves.join(''), inScene: h0.units.every((u) => u.inScene && u.alive) };
  });
  check('33 hunt start: collapse called off, statue wakes, gate sealed, wake is safe', hs.warned === 1 && hs.blockedBefore && hs.phase0 === 'wake' && hs.roofAfter === 0 && hs.wave0 === 0
    && !hs.statue && !hs.solid && hs.openNow && hs.seal && hs.atEntry && hs.hp0 === 100 && !hs.canTarget && hs.hpWake === hs.full && hs.boss === 'block' && hs.btn === 'none'
    && hs.voice.length > 0 && hs.phase1 === 'hunt' && hs.roof10 === 0 && hs.waves10 === '00000' && hs.inScene, JSON.stringify(hs));
  // 34 Tell before every hit: claw shows its ring for the whole windup (>= 0.4 s), no damage before it ends; standing takes the hit, stepping out does not.
  const tell = await g(() => {
    const G = __game, C = G.config, H = window.__h, out = {};
    for (const dodge of [false, true]) {
      H.start(); H.mute(1); H.mute(2); H.mute(0, 'claw'); G.teleport(0, -55 * 1); G.placeUnit(0, 0, -57);
      const n0 = H.until((h) => h.tells.length > 0, 600); const t0 = G.hunt().tells[0];
      let n = 0, early = false, shownAll = true;
      if (dodge) G.setMove(0, 1);
      while (G.hunt().tells.length > 0 && n < 200) { const h = G.hunt(); if (h.p.hp < 100) early = true; if (!h.tells[0].shown) shownAll = false; G.step(1); n++; }
      G.clearMove(); const h = G.hunt();
      out[dodge ? 'dodge' : 'stand'] = { wait: n0, move: t0 && t0.move, look: t0 && t0.look, windupS: n * C.STEP, early, shownAll, hp: h.p.hp, hits: h.hits, minTell: h.minTell };
    }
    out.cfgMin = Math.min(C.DEMON_ULT.windup, ...G.moves.map((k) => C.MOVES[k].windup)); out.claw = C.MOVES.claw.dmg;
    return out;
  });
  check('34 tell before the hit (claw): ring for the whole windup >= 0.4 s, stand = hit, step out = no hit', tell.cfgMin >= 0.4 && tell.stand.move === 'claw' && tell.stand.look === 'D'
    && tell.stand.windupS >= 0.4 && !tell.stand.early && tell.stand.shownAll && tell.stand.hp === 100 - tell.claw && tell.stand.hits === 1 && tell.stand.minTell >= 0.4
    && tell.dodge.hp === 100 && tell.dodge.hits === 0, JSON.stringify(tell));
  // 35 The player's attack and skills damage hunt units; only seen units can be ordered.
  const pd = await g(() => {
    const G = __game, C = G.config, H = window.__h; H.start(); for (let i = 0; i < 3; i++) H.mute(i);
    G.setHp(1e9); G.teleport(0, -50); G.placeUnit(1, 0, -53); G.placeUnit(0, -15, -70); G.placeUnit(2, 15, -70); G.step(1);
    const far = G.attackUnit(0), near = G.attackUnit(1); G.step(Math.round(2 / C.STEP)); const afterAtk = G.hunt().units[1].hp;
    const u = G.hunt().units[1]; G.stop(); const cast = G.cast(0, u.x, u.z); const afterQ = G.hunt().units[1].hp;
    return { far, near, afterAtk, afterQ, cast, full: C.STALKER.hp, q: C.SKILLS[0].dmg };
  });
  check('35 player attack and skill hit hunt units; unseen unit cannot be ordered', !pd.far && pd.near && pd.afterAtk < pd.full && (pd.full - pd.afterAtk) % 10 === 0 && pd.cast && pd.afterQ === pd.afterAtk - pd.q, JSON.stringify(pd));
  // 36 Skill transfer: a broken minion's plate is shown flying, then the demon holds that minion's 2 skills (up to 6), with the minion's tell colour.
  const tr = await g(() => {
    const G = __game, C = G.config, H = window.__h, fly = Math.round(C.APEX.plateS / C.STEP) + 2; H.start(); for (let i = 0; i < 3; i++) H.mute(i); G.setHp(1e9);
    G.hitUnit(1, 1e6); const k = G.hunt(); G.step(fly); const a = G.hunt(), uiA = G.huntUi();
    G.hitUnit(2, 1e6); G.step(fly); const b = G.hunt(), uiB = G.huntUi();
    H.mute(0, 'lunge'); G.teleport(0, -50); G.placeUnit(0, 0, -53.5); H.until((h) => h.tells.length > 0, 600); const t = G.hunt().tells[0];
    return { deadNow: !k.units[1].alive && !k.units[1].inScene, plateFlying: k.units[1].plate, before: k.units[0].skills.join(), platesBefore: k.plates,
      afterA: a.units[0].skills.join(), plateGone: !a.units[1].plate, textA: uiA.bossText, ruleA: uiA.rule, afterB: b.units[0].skills.join(), textB: uiB.bossText, plates: b.plates,
      stolenMove: t && t.move, stolenLook: t && t.look };
  });
  check('36 skill transfer: plate flight shown, demon gains 2 skills per minion (6 total), stolen tell keeps the minion colour', tr.deadNow && tr.plateFlying && tr.before === 'pounce,roar' && tr.platesBefore === 0
    && tr.afterA === 'pounce,roar,lunge,rend' && tr.plateGone && /Lunge/.test(tr.textA) && /Rend/.test(tr.textA) && /Lunge/.test(tr.ruleA) && tr.afterB === 'pounce,roar,lunge,rend,flank,howl'
    && /Flank/.test(tr.textB) && /Howl/.test(tr.textB) && tr.plates === 2 && tr.stolenMove === 'lunge' && tr.stolenLook === 'S', JSON.stringify(tr));
  // 37 Status effects: roar slows, flank stuns (no move, no cast), rend bleeds and stacks to the cap; the HUD names each.
  const fxs = await g(() => {
    const G = __game, C = G.config, H = window.__h, o = {};
    H.start(); H.mute(1); H.mute(2); H.mute(0, 'roar'); G.teleport(0, -55); G.placeUnit(0, 0, -58); H.until((h) => h.p.slow > 0, 900);
    let h = G.hunt(); o.slowK = h.p.slowK; o.slowText = G.huntUi().status; H.mute(0); const x0 = h.p.x; G.setMove(1, 0); G.step(30); G.clearMove(); o.slowDx = G.hunt().p.x - x0;
    H.start(); H.mute(0); H.mute(1); H.mute(2, 'flank'); G.teleport(0, -55); G.placeUnit(2, 0, -59); G.placeUnit(0, -15, -70); G.placeUnit(1, 15, -70);
    H.until((h2) => h2.tells.length > 0, 900); o.flankShape = G.hunt().tells[0].shape; H.until((h2) => h2.p.stun > 0, 200);
    h = G.hunt(); o.stun = h.p.stun; o.stunText = G.huntUi().status; const sx = h.p.x; G.setMove(1, 0); G.step(10); o.stunDx = G.hunt().p.x - sx; o.stunCast = G.cast(0, 0, -60); G.clearMove();
    H.until((h2) => h2.p.stun <= 0, 200); G.setMove(1, 0); G.step(10); G.clearMove(); o.freeDx = G.hunt().p.x - sx;
    H.start(); H.mute(0); H.mute(2); H.mute(1, 'rend'); G.setHp(1e9); G.teleport(0, -55); G.placeUnit(1, 0, -56); G.placeUnit(0, -15, -70); G.placeUnit(2, 15, -70);
    H.until((h2) => h2.p.bleed > 0, 900); o.bleed1 = G.hunt().p.bleed; o.bleedText = G.huntUi().status;
    const hpA = G.hunt().p.hp; H.mute(1); G.step(60); o.bleedPerS = hpA - G.hunt().p.hp;
    for (let i = 0; i < 6; i++) { G.unitCd(1, 'rend', 0); H.until((h2) => h2.tells.length > 0, 300); H.until((h2) => h2.tells.length === 0, 300); }
    o.bleedMax = G.hunt().p.bleed; H.mute(1); G.step(Math.round(C.BLEED.dur / C.STEP) + 5); o.bleedEnd = G.hunt().p.bleed; o.endText = G.huntUi().status;
    o.cap = C.BLEED.max; o.dps = C.BLEED.dps; o.speed = C.PLAYER_SPEED;
    return o;
  });
  check('37 status: roar slow, flank stun (no move, no cast), rend bleed with a stack cap, HUD text', fxs.slowK === 0.4 && /Slowed/.test(fxs.slowText) && Math.abs(fxs.slowDx - fxs.speed * 0.6 * 0.5) < 0.05
    && fxs.flankShape === 'spot' && fxs.stun > 0 && /Stunned/.test(fxs.stunText) && fxs.stunDx === 0 && fxs.stunCast === false && fxs.freeDx > 0.5
    && fxs.bleed1 === 1 && /Bleeding x1/.test(fxs.bleedText) && Math.abs(fxs.bleedPerS - fxs.dps) < 0.05 && fxs.bleedMax === fxs.cap && fxs.bleedEnd === 0 && fxs.endText === '', JSON.stringify(fxs));
  // 38 Demon ultimate (once at half health): told first, frenzy for its set length, never a second time.
  const ult = await g(() => {
    const G = __game, C = G.config, H = window.__h; H.start(); H.mute(1); H.mute(2); G.setHp(1e9); G.teleport(0, -45);
    G.step(60); const before = G.hunt().units[0].frenzy;
    G.hitUnit(0, C.DEMON.hp * 0.5); const n1 = H.until((h) => h.units[0].cur === 'ult' && h.units[0].st === 1, 600), voice = G.huntUi().voice;
    const tellSteps = H.until((h) => h.units[0].frenzy > 0, 600); const f0 = G.hunt().units[0].frenzy;
    const lasted = H.until((h) => h.units[0].frenzy <= 0, 2000) * C.STEP;
    G.step(Math.round(12 / C.STEP)); const again = G.hunt().units[0].frenzy;
    return { before, n1, voice, tellS: tellSteps * C.STEP, f0, lasted, again, dur: C.DEMON_ULT.dur, windup: C.DEMON_ULT.windup, mode: C.DEMON_ULT.mode };
  });
  check('38 demon ultimate: told, frenzy lasts its length, single use', ult.mode === 'once50' && ult.before === 0 && ult.n1 < 600 && ult.voice.length > 0 && ult.tellS >= 0.4
    && Math.abs(ult.tellS - ult.windup) < 0.05 && Math.abs(ult.lasted - ult.dur) < 0.1 && ult.again <= 0, JSON.stringify(ult));
  // 39 Gate seal: the player cannot leave the core hall during the hunt and can again after a new run.
  const seal = await g(() => {
    const G = __game, H = window.__h; H.start(); for (let i = 0; i < 3; i++) H.mute(i);
    G.setMove(0, 1); G.step(300); const z1 = G.hunt().p.z, gz = G.hunt().gateZ;
    G.clearMove(); G.moveTo(0, -30); G.step(300); const z2 = G.hunt().p.z;
    G.reset(); G.teleport(0, -43.5); G.setMove(0, 1); G.step(200); G.clearMove(); const z3 = G.state().z;
    return { z1, z2, z3, gz };
  });
  check('39 gate seal: no way out in the hunt (walk, path order), open after a new run', seal.z1 <= seal.gz + 1e-6 && seal.z2 <= seal.gz + 1e-6 && seal.z3 > seal.gz + 2, JSON.stringify(seal));
  // 40 Win: sim frozen, closing line and time shown, no casting; Retry starts a clean hunt.
  const win = await g(() => {
    const G = __game, C = G.config, H = window.__h, fly = Math.round(C.APEX.plateS / C.STEP) + 2; H.start(); G.setHp(1e9);
    G.hitUnit(1, 1e6); G.step(fly); G.setHp(60); G.hitUnit(0, 1e6);
    const h = G.hunt(), ui = G.huntUi(), t0 = G.state().t; G.step(120); const t1 = G.state().t, cast = G.cast(0, 0, -60);
    G.huntButton(); const r = G.hunt(), ui2 = G.huntUi();
    return { phase: h.phase, voice: ui.voice, rule: ui.rule, btn: ui.btn, btnText: ui.btnText, boss: ui.boss, frozen: t0 === t1, cast, phase2: r.phase, hp2: r.p.hp, plates2: r.plates,
      skills2: r.units.map((u) => u.skills.join()).join('|'), alive2: r.units.every((u) => u.alive && u.inScene && !u.plate), full2: r.units.map((u) => u.hp).join(), btn2: ui2.btn,
      want: [C.DEMON.hp, C.STALKER.hp, C.HOWLER.hp].join(), closing: G.text.voice_won };
  });
  check('40 win: frozen, closing line, retry gives a clean hunt', win.phase === 'won' && win.voice === win.closing && /Victory/.test(win.rule) && win.btn === 'block' && /Retry/.test(win.btnText)
    && win.boss === 'block' && win.frozen && win.cast === false && win.phase2 === 'wake' && win.hp2 === 100 && win.plates2 === 0 && win.skills2 === 'pounce,roar|lunge,rend|flank,howl'
    && win.alive2 && win.full2 === win.want && win.btn2 === 'none', JSON.stringify(win));
  // 41 Loss, then new run x3: frozen on defeat; the royale state is fully back (statue, solid, hazard, UI) and memory and shaders stay flat.
  const loss = await g(() => {
    const G = __game, C = G.config, H = window.__h, out = [];
    for (let r = 0; r < 3; r++) {
      H.start(); G.hitUnit(2, 1e6); G.step(Math.round(C.APEX.plateS / C.STEP) + 2); G.setHp(1);
      const n = H.until((h) => h.phase !== 'hunt', 3000), h = G.hunt(), ui = G.huntUi(), t0 = G.state().t; G.step(120); const frozen = G.state().t === t0;
      G.reset(); const b = G.hunt(), ui2 = G.huntUi(), s = G.state(), info = G.render(true);
      out.push({ n, lost: h.phase === 'lost' && /Defeat/.test(ui.rule) && frozen && h.tells.every((t) => !t.shown),
        back: b.phase === 'royale' && b.statue && b.statueSolid && !b.seal && b.units.every((u) => !u.inScene && !u.alive && !u.plate && !u.seen) && ui2.boss === 'none' && ui2.btn === 'block'
          && /Start/.test(ui2.btnText) && ui2.status === '' && !G.canStand(0, G.hazards()[0].z, 0) && s.hp === 100 && s.t === 0,
        geoms: info.geoms, texs: info.texs, programs: info.programs });
    }
    G.teleport(0, G.hazards()[0].z + 5); G.step(5); const statueTell = G.hazards()[0].state;
    return { out, statueTell };
  });
  check('41 loss, new run x3: defeat frozen, royale state back, statue hazard live, memory and shaders flat', loss.out.every((o) => o.lost && o.back && o.geoms === base.geoms && o.texs === base.texs
    && o.programs === base.programs) && loss.statueTell === 1, JSON.stringify(loss));
  // 42 Bot sweep, 3 skill levels x 3 kill orders, with always-true checks every tick: damage only from a shown tell >= 0.4 s (or its bleed),
  // units on the floor inside the hall, player inside the gate, demon skills = 2 + 2 per plate, finite numbers.
  const sweep = await g(() => {
    const runBot = ({ react, order, maxS }) => {
      const G = __game, C = G.config; window.__h.start();
      const viol = [], bad = (s) => { if (viol.length < 5) viol.push(s); };
      let steps = 0, lastX = 0, lastZ = 0, turn = 0; const max = maxS / C.STEP;
      while (steps < max) {
        const h = G.hunt(), p = h.p; if (h.phase !== 'hunt') break;
        if (Math.abs((C.MAX_HP - p.hp) - (h.hitDmg + h.bleedDmg)) > 1e-6) bad('hp loss without a hit at t=' + h.t.toFixed(2));
        if (h.hits > 0 && h.minTell < 0.4 - 1e-9) bad('tell under 0.4 s: ' + h.minTell);
        if (p.z > h.gateZ + 1e-6) bad('player past the gate');
        if (h.units[0].skills.length !== 2 + 2 * h.plates) bad('demon skill count');
        for (const u of h.units) { if (!u.standOk) bad(u.kind + ' off the floor'); if (!Number.isFinite(u.x + u.z + u.hp)) bad('NaN'); }
        for (const t of h.tells) if (!t.shown) bad('tell not shown: ' + t.move);
        let mx = 0, mz = 0, danger = false;
        for (const t of h.tells) {
          if (t.age < react) continue;
          const qx = p.x - t.x, qz = p.z - t.z, m = 0.4;
          if (t.shape === 'line') {
            const along = qx * t.fx + qz * t.fz, side = qx * t.fz - qz * t.fx;
            if (along >= -m && along <= t.len + m && Math.abs(side) <= t.w / 2 + m) { danger = true; const sg = side >= 0 ? 1 : -1; mx += t.fz * sg; mz -= t.fx * sg; }
          } else { const d = Math.hypot(qx, qz); if (d <= t.r + m) { danger = true; if (d > 0.01) { mx += qx / d; mz += qz / d; } else mx += 1; } }
        }
        if (danger) {
          if (Math.hypot(p.x - lastX, p.z - lastZ) < 0.01) turn++; else turn = 0;
          if (turn > 2) { const t = mx; mx = -mz; mz = t; }
          const l = Math.hypot(mx, mz) || 1; G.setMove(mx / l, mz / l);
          // Batch 12: W is a dash now (changed on purpose); the bot uses it to leave a tell it has seen (the owner's reason for dashes vs the apex).
          if (G.skills()[1] === 0) G.cast(1, p.x + mx / l * 4, p.z + mz / l * 4);
        } else {
          G.clearMove();
          let ti = -1; for (const i of order) if (h.units[i].alive) { ti = i; break; }
          const u = h.units[ti], d = Math.hypot(u.x - p.x, u.z - p.z);
          if (u.seen) {
            G.attackUnit(ti);
            const cd = G.skills();
            for (let s = 0; s < 3; s++) if (s !== 1 && cd[s] === 0 && d <= C.SKILLS[s].range && !(s === 2 && G.pending())) G.cast(s, u.x, u.z);
          } else G.setMove((u.x - p.x) / d, (u.z - p.z) / d);
        }
        lastX = p.x; lastZ = p.z; G.step(1); steps++;
      }
      G.clearMove(); const h = G.hunt();
      return { react, order: order.join(''), phase: h.phase, t: Math.round(h.t), hp: Math.round(h.p.hp), demon: Math.round(h.units[0].hp), plates: h.plates, hits: h.hits, viol };
    };
    const out = [];
    for (const react of [99, 0.3, 0.15]) for (const order of [[0, 1, 2], [1, 2, 0], [2, 1, 0]]) out.push(runBot({ react, order, maxS: 300 }));
    return out;
  });
  const lvl = (r) => sweep.filter((o) => o.react === r);
  check('42 bot sweep 9 runs: 0 broken invariants, every run ends, never-dodge always loses, 0.3 s and 0.15 s reaction each win at least once',
    sweep.every((o) => o.viol.length === 0 && o.phase !== 'hunt') && lvl(99).every((o) => o.phase === 'lost') && lvl(0.3).some((o) => o.phase === 'won') && lvl(0.15).some((o) => o.phase === 'won'),
    sweep.map((o) => `${o.react}/${o.order}:${o.phase} ${o.t}s hp${o.hp} demon${o.demon}${o.viol.length ? ' VIOL ' + o.viol.join(';') : ''}`).join(' | '));
  // 43 Budget and shaders in the hunt with every unit, tell and the seal drawn: under 500 calls / 0.5M tris, no new shader program.
  const hb2 = await g(() => {
    const G = __game, H = window.__h; H.start(); G.setHp(1e9); G.teleport(0, -58); for (let i = 0; i < 3; i++) G.placeUnit(i, (i - 1) * 3, -61);
    let best = null; for (let n = 0; n < 900; n++) { G.step(1); const h = G.hunt(); if (!best || h.tells.length > best.tells) { const r = G.render(true); best = { tells: h.tells.length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; } }
    G.reset(); return best;
  });
  check('43 hunt budget (calls<500, tris<500k) and no shader compile, units and tells drawn', hb2.tells >= 2 && hb2.calls < 500 && hb2.tris < 500000 && hb2.programs === base.programs && hb2.geoms === base.geoms,
    JSON.stringify(hb2) + ` base calls ${base.calls}`);
  // 45 Text keys for every move name.
  const mk = await g(() => __game.moves.filter((k) => !__game.text['move_' + k]));
  check('45 text keys for every move', mk.length === 0, mk.join(' '));

  // ===== Batch 7: royale minions (kennel waves, cubs at camps, plate reward) =====
  await g(() => { const G = __game, C = G.config; window.__k = { sp: (t) => G.step(Math.round(t / C.STEP)), mute: (i, except) => { for (const k of G.moves) G.cubCd(i, k, k === except ? 0 : 9999); },
    until: (cond, max) => { let n = 0; while (n < max && !cond(G.cubs())) { G.step(1); n++; } return n; } }; });
  // 46 Kennel wave: 5 s warning (her line, plain rule with the zone), then one Stalker at the camp; it rests while no suit is inside its aggro radius. Switch off = no cubs.
  const ken = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}; G.reset();
    K.sp(C.KENNEL.firstS - C.KENNEL.warnS - 0.1); let c = G.cubs(); o.early = c.warned || c.list.some((u) => u.alive);
    K.sp(0.2); c = G.cubs(); o.warned = c.warned; o.banner = c.banner; o.voiceOk = c.voice === G.text.voice_kennel; o.rule = c.rule; o.noneYet = !c.list.some((u) => u.alive);
    K.sp(C.KENNEL.warnS); c = G.cubs(); const a = c.list.filter((u) => u.alive); o.n = a.length; o.kind = a[0] && a[0].kind; o.atCamp = a[0] && Math.hypot(a[0].x - G.camps[0][0], a[0].z - G.camps[0][1]) < 0.01;
    o.hp = a[0] && a[0].hp; o.want = C.STALKER.hp * C.CUB.hpK; o.seenFar = a[0] && a[0].seen; o.wave = c.wave;
    G.teleport(G.camps[0][0] + C.CUB.aggro + 2, G.camps[0][1]); K.sp(5); c = G.cubs(); const b = c.list.find((u) => u.alive);
    o.rest = !b.hot && c.tells.length === 0 && Math.hypot(b.x - b.cx, b.z - b.cz) < 0.01 && b.seen; o.warnS = C.KENNEL.warnS;
    C.ROYALE_MINIONS = false; G.reset(); K.sp(C.KENNEL.firstS + 1); c = G.cubs(); o.off = !c.warned && !c.list.some((u) => u.alive); C.ROYALE_MINIONS = true; G.reset();
    return o;
  });
  check('46 kennel wave: warning with zone, Stalker at the camp, rests outside aggro; switch off = none', !ken.early && ken.warned && ken.banner === 'block' && ken.voiceOk && /West courtyard, north/.test(ken.rule)
    && ken.noneYet && ken.warnS >= 0.4 && ken.n === 1 && ken.kind === 'stalker' && ken.atCamp && ken.hp === ken.want && !ken.seenFar && ken.wave === 1 && ken.rest && ken.off, JSON.stringify(ken));
  // 47 Cub fight rules: aggro inside the radius, told bite with scaled damage, leash home and heal; a Flank aimed past a terrace edge never puts the cub over the drop.
  const cf = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}; G.reset(); K.sp(C.KENNEL.firstS + 0.1);
    let c = G.cubs(); const a = c.list.findIndex((u) => u.alive), u = c.list[a]; K.mute(a, 'bite');
    G.teleport(u.x + C.CUB.aggro - 1, u.z); G.step(2); o.hot = G.cubs().list[a].hot;
    K.until((x) => x.tells.length > 0, 600); const t = G.cubs().tells[0]; o.move = t && t.move; let n = 0, early = false;
    while (G.cubs().tells.length > 0 && n < 200) { if (G.state().hp < 100) early = true; G.step(1); n++; }
    o.windupS = n * C.STEP; o.early = early; o.hp = G.state().hp; o.wantHp = 100 - C.MOVES.bite.dmg * C.CUB.dmgK; o.minTell = G.cubs().minTell;
    K.mute(a); G.hitCub(a, 40); const hurtHp = G.cubs().list[a].hp;
    G.teleport(u.cx + 6, u.cz + C.CUB.leash + 4); G.step(30); o.home = G.cubs().list[a].home; K.sp(C.CUB.homeMaxS + 2); c = G.cubs(); const b = c.list[a];
    o.back = Math.hypot(b.x - b.cx, b.z - b.cz) < 0.7 && !b.home && !b.hot; o.healed = hurtHp < b.max && b.hp === b.max;
    const waves = C.KENNEL.waves, leash = C.CUB.leash;
    try {
      C.KENNEL.waves = [[['howler', 0]]]; C.CUB.leash = 40; G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const h = G.cubs().list.findIndex((x) => x.alive); K.mute(h, 'flank'); G.placeCub(h, -54, -5); G.teleport(-54, -0.8); G.step(1);
      K.until((x) => x.tells.length > 0, 300); o.flank = G.cubs().tells[0] && G.cubs().tells[0].move; K.until((x) => x.tells.length === 0 && x.list[h].st !== 2, 300);
      const f = G.cubs().list[h]; o.edge = { z: +f.z.toFixed(2), y: f.y, floor: G.topY(f.x, f.z), ok: f.standOk };
    } finally { C.KENNEL.waves = waves; C.CUB.leash = leash; G.reset(); }
    return o;
  });
  check('47 cub rules: aggro, told bite (>= 0.4 s) at scaled damage, leash home and heal, no flank over a drop', cf.hot && cf.move === 'bite' && cf.windupS >= 0.4 && !cf.early && cf.hp === cf.wantHp && cf.minTell >= 0.4
    && cf.home && cf.back && cf.healed && cf.flank === 'flank' && cf.edge.ok && cf.edge.y === 4 && Math.abs(cf.edge.floor - cf.edge.y) < 0.7, JSON.stringify(cf));
  // 48 Plate reward: plate flies to the player, 45 s buff in one of two slots, ultimate charge (batch 15), Stalker plate = bleed on hits, Howler plate = speed, oldest slot replaced, buff runs out.
  const pl = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}, fly = Math.round(C.PLATE.flyS / C.STEP) + 2; G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
    let c = G.cubs(); const a = c.list.findIndex((u) => u.alive), ua = c.list[a]; K.mute(a);
    // Game changed on purpose (batch 15): the plate gives ULT.plate charge instead of a cooldown cut; the meter starts empty and passive charge during the flight is taken out.
    G.teleport(ua.x + 4, ua.z + 3); G.step(2); G.setCharge(-1, 0); const ch0 = G.chargeOf(-1);
    G.hitCub(a, 1e6); c = G.cubs(); o.dead = !c.list[a].alive && !c.list[a].inScene && !c.list[a].tellIn; o.flying = c.list[a].plate; o.takenBefore = c.taken;
    G.step(fly); c = G.cubs(); o.slot0 = c.plates[0].kind; o.t0 = c.plates[0].t; o.status = c.status; o.rule = c.rule; o.plateGone = !c.list[a].plate; o.taken = c.taken;
    o.gain = G.chargeOf(-1) - ch0 - C.ULT.passive * fly * C.STEP; o.wantGain = C.ULT.plate;
    K.sp(C.KENNEL.intervalS); c = G.cubs(); o.expired = c.plates.every((p) => p.kind === '' && p.t === 0) && c.status === '';
    const h = c.list.findIndex((u) => u.alive && u.kind === 'howler'), uh = c.list[h]; K.mute(h);
    G.teleport(uh.x - 4, uh.z); G.step(2); G.givePlate('stalker'); G.cast(0, uh.x, uh.z); const hp1 = G.cubs().list[h].hp; o.lineHit = uh.hp - hp1; o.bleedOn = G.cubs().list[h].bleed > 0;
    G.step(60); o.bleedLoss = hp1 - G.cubs().list[h].hp; o.wantBleed = C.PLATE.bleedDps;
    G.givePlate('howler'); G.stop(); const z0 = G.state().z; G.setMove(0, 1); G.step(30); G.clearMove(); o.fastDz = G.state().z - z0; o.wantDz = C.PLAYER_SPEED * (1 + C.PLATE.speed) * 0.5;
    G.hitCub(h, 1e6); G.step(fly); c = G.cubs(); o.slots = c.plates.map((p) => p.kind).join(); o.taken2 = c.taken; o.status2 = c.status;
    return o;
  });
  check('48 plate: flight shown, buff slot, ultimate charge, bleed on hits, speed, oldest slot replaced, expiry', pl.dead && pl.flying && pl.takenBefore === 0 && pl.slot0 === 'stalker' && pl.t0 > 44 && /Stalker plate 4\ds/.test(pl.status)
    && /Stalker plate/.test(pl.rule) && pl.plateGone && pl.taken === 1 && Math.abs(pl.gain - pl.wantGain) < 0.05 && pl.expired && pl.lineHit === 25 && pl.bleedOn && Math.abs(pl.bleedLoss - pl.wantBleed) < 0.2
    && Math.abs(pl.fastDz - pl.wantDz) < 0.05 && pl.slots === 'howler,howler' && pl.taken2 === 2 && /Howler plate/.test(pl.status2), JSON.stringify(pl));
  // 49 Collapse: a cub whose section falls is lost and gives no plate; a fallen camp spawns nothing.
  const kc = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}, waves = C.KENNEL.waves;
    try {
      C.KENNEL.waves = [[['stalker', 2]], [['stalker', 2]]]; G.reset(); K.sp(C.KENNEL.firstS + 0.1); let c = G.cubs(); o.onRoof = c.list.filter((u) => u.alive).length;
      K.sp(C.FIRST_WAVE_S - C.KENNEL.firstS + 1.5); c = G.cubs(); o.lost = !c.list.some((u) => u.alive || u.inScene || u.plate || u.tellIn); o.taken = c.taken; o.slots = c.plates.map((p) => p.kind).join('');
      K.sp(C.KENNEL.intervalS); c = G.cubs(); o.wave = c.wave; o.noSpawn = !c.list.some((u) => u.alive); o.banner2 = c.voice === G.text.voice_kennel && c.banner === 'block';
    } finally { C.KENNEL.waves = waves; G.reset(); }
    return o;
  });
  check('49 collapse: cub lost with its section, no plate; fallen camp spawns nothing and is not announced', kc.onRoof === 1 && kc.lost && kc.taken === 0 && kc.slots === '' && kc.wave === 2 && kc.noSpawn && !kc.banner2, JSON.stringify(kc));
  // 50 The wake clears the cubs; a new run restarts the waves; memory and shaders flat with the whole pool out and tells drawn.
  const kr = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}, waves = C.KENNEL.waves;
    G.reset(); K.sp(C.KENNEL.firstS + C.KENNEL.intervalS + 0.1); o.before = G.cubs().list.filter((u) => u.alive).length;
    G.startHunt(); let c = G.cubs(); o.cleared = !c.list.some((u) => u.alive || u.inScene || u.tellIn || u.seen); o.fusing = G.neutrals().fusing; o.fusePlates = c.list.filter((u) => u.plate).length;
    K.sp(C.APEX.wakeS + 0.2); o.noneInHunt = !G.cubs().list.some((u) => u.alive || u.plate) && G.neutrals().fusing === 0;
    G.reset(); c = G.cubs(); o.reset = c.wave === 0 && !c.warned && !c.list.some((u) => u.alive);
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]]; G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      G.teleport(G.camps[0][0], G.camps[0][1] + 4); let best = null;
      for (let n = 0; n < 600; n++) { G.step(1); c = G.cubs(); if (!best || c.tells.length > best.tells) { const r = G.render(true); best = { tells: c.tells.length, alive: c.list.filter((u) => u.alive).length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; } }
      o.best = best;
    } finally { C.KENNEL.waves = waves; G.reset(); }
    return o;
  });
  check('50 wake: live cubs fly home as plates and are gone by the hunt, new run restarts waves; 7 cubs with tells inside budget, no shader compile, memory flat', kr.before === 3 && kr.cleared && kr.fusing === 3 && kr.fusePlates === 3 && kr.noneInHunt && kr.reset && kr.best.alive === 7 && kr.best.tells >= 3
    && kr.best.calls < 500 && kr.best.tris < 500000 && kr.best.programs === base.programs && kr.best.geoms === base.geoms, JSON.stringify(kr));
  // 51 Bot farms the west camp for 170 s (0.3 s reaction) with always-true checks every tick: hits only after a shown tell >= 0.4 s, cubs on their own floor, pool never exceeded.
  const farm = await g(() => {
    const G = __game, C = G.config, viol = [], bad = (s) => { if (viol.length < 5) viol.push(s); }; G.reset(); G.teleport(G.camps[0][0] + 5, G.camps[0][1] + 5);
    let minHp = 100, deaths = 0; const max = Math.round(170 / C.STEP), react = 0.3;
    for (let n = 0; n < max; n++) {
      const c = G.cubs(), s = G.state(); minHp = Math.min(minHp, s.hp); if (s.dead) deaths++;
      if (c.hits > 0 && c.minTell < 0.4 - 1e-9) bad('tell under 0.4 s: ' + c.minTell);
      if (c.list.filter((u) => u.alive).length > c.list.length) bad('pool exceeded');
      for (const u of c.list) if (u.alive) { if (!u.standOk) bad(u.kind + ' off its floor'); if (u.st !== 2 && Math.abs(G.topY(u.x, u.z) - u.y) > 0.7) bad(u.kind + ' not on a floor surface'); if (!Number.isFinite(u.x + u.z + u.hp)) bad('NaN'); }
      for (const t of c.tells) if (!t.shown) bad('tell not shown: ' + t.move);
      let mx = 0, mz = 0, danger = false;
      for (const t of c.tells) {
        if (t.age < react) continue;
        const qx = s.x - t.x, qz = s.z - t.z, m = 0.4;
        if (t.shape === 'line') { const along = qx * t.fx + qz * t.fz, side = qx * t.fz - qz * t.fx; if (along >= -m && along <= t.len + m && Math.abs(side) <= t.w / 2 + m) { danger = true; const sg = side >= 0 ? 1 : -1; mx += t.fz * sg; mz -= t.fx * sg; } }
        else { const d = Math.hypot(qx, qz); if (d <= t.r + m) { danger = true; if (d > 0.01) { mx += qx / d; mz += qz / d; } else mx += 1; } }
      }
      if (danger) { const l = Math.hypot(mx, mz) || 1; G.setMove(mx / l, mz / l); }
      else {
        G.clearMove(); let ti = -1, bd = 1e9;
        c.list.forEach((u, i) => { const d = Math.hypot(u.x - s.x, u.z - s.z); if (u.alive && u.seen && d < bd) { bd = d; ti = i; } });
        if (ti >= 0) { G.attackCub(ti); const cd = G.skills(), u = c.list[ti]; for (let k = 0; k < 2; k++) if (cd[k] === 0 && bd <= C.SKILLS[k].range) G.cast(k, u.x, u.z); }
      }
      G.step(1);
    }
    G.clearMove(); const c = G.cubs();
    return { viol, taken: c.taken, minHp: Math.round(minHp), deaths, hits: c.hits, wave: c.wave };
  });
  check('51 bot farms the west camp 170 s: 0 broken invariants, takes plates, never dies', farm.viol.length === 0 && farm.taken >= 2 && farm.deaths === 0 && farm.wave === 3, JSON.stringify(farm));

  // ===== Batch 8: buff creatures (crab, wanderer) drawn from marble bags; faster cubs and minions =====
  // 52 Marble bags: every cycle is the whole bag in a new order (nothing repeats before the bag is empty); same seed = same draws; another seed differs.
  const bag = await g(() => {
    const G = __game, C = G.config, names = ['times', 'spots', 'crab', 'wander', 'amounts'], o = { cycles: true };
    const seq = (seed) => { G.setSeed(seed); G.reset(); const out = {}; for (const n of names) { const len = n === 'spots' ? C.BAGS.spots.length : C.BAGS[n].length; out[n] = []; if (n === 'times') for (let i = 0; i < len - 2; i++) G.drawBag(n); for (let i = 0; i < len * 3; i++) out[n].push(G.drawBag(n)); } return out; };
    const a = seq(777), b = seq(777), c = seq(778);
    for (const n of names) {
      const src = n === 'spots' ? C.BAGS.spots.map((_, i) => i) : C.BAGS[n], len = src.length, want = JSON.stringify(src.slice().sort());
      for (let k = 0; k < 3; k++) if (JSON.stringify(a[n].slice(k * len, (k + 1) * len).sort()) !== want) o.cycles = false;
    }
    o.same = JSON.stringify(a) === JSON.stringify(b); o.differs = JSON.stringify(a) !== JSON.stringify(c);
    o.spotsOk = G.spots.every(([x, z]) => G.canStand(x, z, G.topY(x, z))); o.speeds = [C.STALKER.speed, C.HOWLER.speed, C.PLAYER_SPEED];
    G.setSeed(12345); G.reset(); return o;
  });
  check('52 marble bags: full cycles without repeats, seeded, all spots standable; cubs and minions faster than the suit', bag.cycles && bag.same && bag.differs && bag.spotsOk
    && bag.speeds[0] > bag.speeds[2] && bag.speeds[1] > bag.speeds[2], JSON.stringify(bag));
  // 53 Appearance: time, place, boon and size all come from the bags; announced with the zone; the creatures never attack; after a kill the next time is drawn again.
  const ne = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}; G.reset(); const n0 = G.neutrals(); o.first = n0.next.slice(); o.noneAt0 = !n0.list.some((u) => u.alive);
    K.sp(Math.min(...n0.next) + 0.1); let n = G.neutrals(); const i = n.next[0] <= n.next[1] ? 0 : 1, u = n.list[i]; o.kind = u.kind; o.alive = u.alive; o.rule = n.rule; o.voice = n.voice;
    o.atSpot = Math.hypot(u.x - G.spots[u.spot][0], u.z - G.spots[u.spot][1]) < 0.5; o.boon = u.boon; o.amt = u.amt; o.secOk = u.sec === 0; o.unseen = !u.seen;
    G.teleport(u.x + 2.5, u.z + 2.5); K.sp(4); n = G.neutrals(); o.passive = G.state().hp === 100 && G.cubs().hits === 0 && n.list[i].alive && n.list[i].standOk && n.list[i].seen;
    o.moved = Math.hypot(n.list[i].x - u.x, n.list[i].z - u.z) > 0.3;
    o.target = G.attackNeutral(i); K.sp(1.5); o.hurt = G.neutrals().list[i].hp < u.max;
    G.hitNeutral(i, 1e6); n = G.neutrals(); o.dead = !n.list[i].alive && !n.list[i].inScene; o.boons = n.boons; o.gap = +(n.next[i] - n.t).toFixed(3);
    o.timesOk = o.first.every((t) => C.BAGS.times.includes(t)) && C.BAGS.times.includes(o.gap); o.boonOk = C.BAGS[i === 0 ? 'crab' : 'wander'].includes(o.boon) && C.BAGS.amounts.includes(o.amt);
    return o;
  });
  check('53 buff creature: bag-drawn time, place, boon and size; announced; passive; next time drawn at the kill', ne.noneAt0 && ne.alive && ne.atSpot && ne.secOk && ne.unseen && ne.voice.length > 0 && /is in: /.test(ne.rule)
    && ne.passive && ne.moved && ne.target && ne.hurt && ne.dead && ne.boons === 1 && ne.timesOk && ne.boonOk, JSON.stringify(ne));
  // 54 Boons: each of the 6 does what its line says at the drawn size, stacks stay under the cap, timed boons run out, and the HUD names them.
  const bo = await g(() => {
    const G = __game, C = G.config, K = window.__k, B = C.BOONS, o = {}, d = G.dummies()[1];
    const give = (i, boon, amt) => { G.forceNeutral(i, 4, boon, amt); G.hitNeutral(i, 1e6); };
    // Game changed on purpose (batch 15): the crab's ult boon gives charge (BOONS.ult.v x amount) instead of a cooldown cut; the kill is instant, so no passive charge is mixed in.
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2); G.setCharge(-1, 0); const ch0 = G.chargeOf(-1); give(0, 'ult', 1.5); o.ult = G.chargeOf(-1) - ch0; o.wantUlt = B.ult.v * 1.5; o.ultRule = G.neutrals().rule;
    G.setHp(40); give(0, 'heal', 0.5); o.heal = G.state().hp - 40; o.wantHeal = B.heal.v * 0.5;
    give(0, 'power', 1); G.cast(0, d.x, d.z); o.powerHit = 100 - G.dummies()[1].hp; o.wantHit = C.SKILLS[0].dmg * (1 + B.power.v); G.step(1); o.status = G.neutrals().status;
    G.setHp(40); give(1, 'regen', 1); const h0 = G.state().hp; G.step(60); o.regen = G.state().hp - h0; o.wantRegen = B.regen.v;
    give(1, 'vision', 1); G.step(1); let n = G.neutrals(); o.visR = n.visR; o.fow = n.fow; o.wantVis = C.VISION_R + B.vision.v;
    G.teleport(d.x, d.z - C.VISION_R - 2); G.step(2); o.seesFar = G.dummies()[1].seen;
    give(1, 'speed', 1.5); G.givePlate('howler'); const x0 = G.state().x; G.setMove(1, 0); G.step(30); G.clearMove(); o.fast = G.state().x - x0; o.wantFast = C.PLAYER_SPEED * Math.min(C.BONUS_CAP, (1 + C.PLATE.speed) * (1 + B.speed.v * 1.5)) * 0.5;
    o.status2 = G.neutrals().status; K.sp(46); n = G.neutrals(); o.ended = n.bT.every((t) => t === 0) && n.visR === C.VISION_R && n.fow === C.VISION_R && n.status === '';
    o.cap = C.BONUS_CAP; o.maxSpeed = (1 + C.PLATE.speed) * (1 + B.speed.v * Math.max(...C.BAGS.amounts)); o.maxPower = 1 + B.power.v * Math.max(...C.BAGS.amounts);
    return o;
  });
  check('54 boons: ultimate charge, heal, power, regen, vision, speed at the drawn size; under the cap; they end; HUD text', Math.abs(bo.ult - bo.wantUlt) < 0.05 && /charge/.test(bo.ultRule) && Math.abs(bo.heal - bo.wantHeal) < 0.01
    && Math.abs(bo.powerHit - bo.wantHit) < 0.01 && /Power \d+s/.test(bo.status) && Math.abs(bo.regen - bo.wantRegen) < 0.05 && bo.visR === bo.wantVis && bo.fow === bo.wantVis && bo.seesFar
    && Math.abs(bo.fast - bo.wantFast) < 0.05 && /Speed \d+s/.test(bo.status2) && /Vision \d+s/.test(bo.status2) && bo.ended && bo.maxSpeed <= bo.cap && bo.maxPower <= bo.cap, JSON.stringify(bo));
  // 55 A creature whose section falls is lost with no boon and comes back later elsewhere; the wake clears both; switch off = none; memory and shaders flat.
  const nl = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}; G.reset(); K.sp(C.FIRST_WAVE_S + C.WAVE_INTERVAL_S - C.COLLAPSE_WARN_S - 1);
    G.forceNeutral(0, 0, 'heal', 1); G.forceNeutral(1, 1, 'regen', 1); K.sp(C.COLLAPSE_WARN_S + 1 + C.WAVE_INTERVAL_S + 0.5); let n = G.neutrals();
    o.lost = n.list.every((u) => !u.alive && !u.inScene); o.boons = n.boons; o.redrawn = n.next.every((t) => t > n.t - 1 && C.BAGS.times.includes(+(t - (C.FIRST_WAVE_S + 2 * C.WAVE_INTERVAL_S)).toFixed(2)));
    K.sp(60); n = G.neutrals(); o.backOnLiveGround = n.list.filter((u) => u.alive).every((u) => u.sec === 0 && u.standOk);
    G.forceNeutral(0, 4, 'heal', 1); G.forceNeutral(1, 5, 'regen', 1); G.teleport(G.spots[4][0], G.spots[4][1] + 3); G.step(2); const r = G.render(true); o.geoms = r.geoms; o.programs = r.programs;
    G.startHunt(); n = G.neutrals(); o.wake = n.list.every((u) => !u.alive && !u.inScene && !u.seen);
    C.NEUTRALS = false; G.reset(); K.sp(60); o.off = !G.neutrals().list.some((u) => u.alive); C.NEUTRALS = true; G.reset();
    return o;
  });
  check('55 buff creatures: lost with a fallen section (no boon, drawn again), cleared by the wake, switch off, memory and shaders flat', nl.lost && nl.boons === 0 && nl.redrawn && nl.backOnLiveGround
    && nl.wake && nl.off && nl.geoms === base.geoms && nl.programs === base.programs, JSON.stringify(nl));

  // ----- Bots (batch 9). Each check sets the bots itself and puts the map test back (0 bots) at the end.
  // 56 The bots (CONFIG.BOTS.count; batch 14 changed 9 -> 8 on purpose: nine schools) spawn at distinct spawns other than the player's and roam 230 s (player parked in the core hall): every tick their centre stays on a floor or they are airborne,
  // never stuck over 3 s, at most one path search per step, seen only inside the player's vision, every bot that is out has a cause. navSearch timing is reported (not gated: wall clock).
  const bw = await g(() => {
    const G = __game, C = G.config, viol = [], bad = (s) => { if (viol.length < 5) viol.push(s); };
    G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset();
    const b0 = G.bots(), spawns = new Set(b0.list.map((q) => q.spawn));
    const o = { n: b0.list.length, distinct: spawns.size === G.config.BOTS.count && !spawns.has(C.PLAYER_SPAWN), inScene: b0.list.every((q) => q.inScene && !q.dead && q.hp === 100) };
    G.teleport(0, -50); const steps = Math.round(230 / C.STEP); const runs0 = G.bots().navRuns;
    for (let t = 0; t < steps; t++) {
      G.step(1);
      if (t % 10) continue;
      const b = G.bots(), s = G.state();
      for (const q of b.list) {
        if (!q.standOk) bad(`t${t} bot${q.id} off floor`);
        // Batch 12: a marked suit is seen from anywhere (panel, 23 Nov 15:11); otherwise only inside the player's vision.
        if (q.seen && q.markT <= 0 && Math.hypot(q.x - s.x, q.z - s.z) > G.neutrals().visR + 1e-6) bad(`t${t} bot${q.id} seen outside vision`);
        if (q.dead && q.inScene) bad(`t${t} bot${q.id} out but drawn`);
      }
    }
    const b = G.bots(); o.navPeak = b.navPeak; o.navPerStep = +((b.navRuns - runs0) / steps).toFixed(4); o.stuck = +Math.max(...b.list.map((q) => q.stuck)).toFixed(2);
    o.out = b.list.filter((q) => q.dead).map((q) => q.cause); o.noCause = o.out.filter((c) => !['hit', 'hazard', 'fall', 'bleed', 'drop'].includes(c)).length;
    const pts = G.spawns.map((s) => [s[0], s[1]]).concat([[0, 30], [-50, -15], [50, -15], [0, -40]]), ms = [];
    for (const a of pts) for (const c of pts) if (a !== c) ms.push(G.navTime(a[0], a[1], c[0], c[1], false).ms);
    ms.push(G.navTime(pts[0][0], pts[0][1], 0, 60, false).ms); ms.sort((x, y) => x - y);
    o.navMs = { median: +ms[ms.length >> 1].toFixed(2), max: +ms[ms.length - 1].toFixed(2) }; o.viol = viol;
    G.setBots(0); G.reset(); return o;
  });
  check(`56 bots: ${NB} at the other spawns, roam 230 s: on a floor every tick, never stuck > 3 s, <= 1 path search per step, seen only in vision, every out has a cause`,
    bw.n === NB && bw.distinct && bw.inScene && bw.viol.length === 0 && bw.stuck <= 3 && bw.navPeak === 1 && bw.noCause === 0, JSON.stringify(bw));
  // 57 Budget with every suit (batch 14: 9 on purpose), 7 cubs and their tells in view (default tier): under 500 calls / 0.5M tris, no new shader program, geometry count flat.
  const bb = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      for (let n = 0; n < 600; n++) {
        for (let i = 0; i < G.config.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5);
        G.step(1); const c = G.cubs();
        if (!best || c.tells.length > best.tells) { const r = G.render(true); best = { tells: c.tells.length, bots: G.bots().list.filter((q) => q.vis).length, cubs: c.list.filter((u) => u.alive && u.seen).length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setBots(0); G.reset(); }
    return best;
  });
  check(`57 budget: ${NS} suits + 7 cubs + tells drawn (calls<500, tris<500k), no shader compile, geometry flat`, bb.bots === NB && bb.cubs === 7 && bb.tells >= 3 && bb.calls < 500 && bb.tris < 500000
    && bb.programs === base.programs && bb.geoms === base.geoms, JSON.stringify(bb));
  // 58 Three runs with bots in the same page: bots respawn full, memory and shaders flat.
  const bm = await g(() => {
    const G = __game, K = window.__k, out = [];
    G.setBots(G.config.BOTS.count);
    for (let r = 0; r < 3; r++) { G.setSeed(100 + r); G.reset(); const b = G.bots(); const fresh = b.list.every((q) => !q.dead && q.hp === 100 && q.inScene && q.plates === 0); K.sp(40); const m = G.render(true); out.push({ fresh, geoms: m.geoms, texs: m.texs, programs: m.programs }); }
    G.setBots(0); G.reset(); return out;
  });
  check('58 new run x3 with bots: fresh bots, memory and shaders flat', bm.every((m) => m.fresh && m.geoms === base.geoms && m.texs === base.texs && m.programs === base.programs), JSON.stringify(bm));
  // 59 Target rule (owner, 23 Nov): a bot answers the suit that hit it; once it sees the player it switches to the player, keeps it while seen, and lets go when the player is out of sight.
  // Batch 10: with the hunter slot (maxHunters 1) either bot may take the slot first, so this check of the switch itself opens a second slot and restores it.
  const rt = await g(() => {
    const G = __game, K = window.__k, o = {}, mh = G.config.BOT.maxHunters; G.config.BOT.maxHunters = 2;
    G.setSeed(12345); G.setBots(2); G.reset(); G.teleport(0, -50); G.setHp(1e9);
    // Game changed on purpose (batch 16): bot 2 now plays 法甲, whose 术 exposes the player it hits (seen from anywhere for 3 s); this check tests the
    // target rule itself, so both bots play the placeholder kit here.
    G.placeholderKit(0); G.placeholderKit(1);
    G.placeBot(0, 0, 10); G.placeBot(1, 2.5, 10); G.hitBy(1, 0, 1); K.sp(0.5); o.first = G.bots().list[0].tgt;
    G.teleport(0, 16); K.sp(0.5); o.onSight = G.bots().list[0].tgt;
    let kept = true; for (let n = 0; n < 8; n++) { K.sp(0.25); if (G.bots().list[0].tgt !== 0) kept = false; } o.kept = kept;
    G.teleport(0, -50); K.sp(0.6); o.away = G.bots().list[0].tgt;
    G.config.BOT.maxHunters = mh; G.setBots(0); G.reset(); return o;
  });
  check('59 bot target: answers its attacker, switches to the player on sight, keeps the player while seen, lets go out of sight', rt.first === 2 && rt.onSight === 0 && rt.kept && rt.away !== 0, JSON.stringify(rt));
  const C0 = await g(() => __game.config);
  // 60 Bots take plates and boons (owner, 23 Nov): a cub broken by a bot sends its plate to that bot (buff slot, ultimate charge since batch 15); a buff creature's boon goes to its last hitter; the player gets neither.
  const bp = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {};
    G.setSeed(12345); G.setBots(1); G.reset(); G.teleport(0, -50); K.sp(C.KENNEL.firstS + 0.1);
    const ci = G.cubs().list.findIndex((u) => u.alive); G.placeBot(0, G.camps[0][0] + 9, G.camps[0][1]);
    // Game changed on purpose (batch 15): the bot's plate gives ULT.plate charge instead of a cooldown cut; passive charge over the flight is taken out.
    G.setCharge(0, 0); const chBefore = G.chargeOf(0), flyN = Math.round((C.PLATE.flyS + 0.1) / C.STEP); G.hitCubBy(ci, 0, 1e4); K.sp(C.PLATE.flyS + 0.1);
    let b = G.bots().list[0]; o.plates = b.plates; o.slot = b.pk[0]; o.gain = +(G.chargeOf(0) - chBefore - C.ULT.passive * flyN * C.STEP).toFixed(3); o.playerPlates = G.player().plates;
    G.forceNeutral(0, 0, 'power', 1); G.hitNeutralBy(0, 0, 1e4); b = G.bots().list[0]; o.boons = b.boons; o.power = b.bT[0] > 0; o.playerBoons = G.player().boons;
    G.setBots(0); G.reset(); return o;
  });
  check('60 bots take plates and boons: plate to the bot that broke the cub (slot, ultimate charge), boon to the last hitter, none to the player', bp.plates === 1 && bp.slot !== '' && Math.abs(bp.gain - C0.ULT.plate) < 0.05
    && bp.boons === 1 && bp.power && bp.playerPlates === 0 && bp.playerBoons === 0, JSON.stringify(bp));
  // 61 Dodge: an average bot (0.3 s reaction) parked by a stone lion for 8 s steps out of every 0.6 s tell: the lion strikes, the bot takes no hazard damage.
  const dg = await g(() => {
    const G = __game, K = window.__k, o = {};
    G.setSeed(12345); G.setBots(1); G.reset(); G.teleport(0, -50);
    const lion = G.hazards().find((h) => h.kind === 'lion'); let tells = 0, prev = 0;
    G.placeBot(0, lion.x + 2.5, lion.z);
    for (let n = 0; n < 8 * 60; n++) { G.step(1); const h = G.hazards().find((q) => q.x === lion.x && q.z === lion.z); if (h.state === 1 && prev !== 1) tells++; prev = h.state; if (n % 60 === 0 && G.bots().list[0].mode !== 'dodge' && Math.hypot(G.bots().list[0].x - lion.x, G.bots().list[0].z - lion.z) > 6) G.placeBot(0, lion.x + 2.5, lion.z); }
    const b = G.bots().list[0]; o.tells = tells; o.hp = b.hp; o.dead = b.dead;
    G.setBots(0); G.reset(); return o;
  });
  check('61 dodge: bot by a stone lion 8 s, lion tells at least twice, bot takes no damage', dg.tells >= 2 && dg.hp === 100 && !dg.dead, JSON.stringify(dg));
  // 62 Flee: two bots fighting on the roof (too tough to break each other) stop when its collapse is warned and walk off before it falls (5 s warning).
  const fl = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {};
    // Batch 13: decrees are paced about one a minute now (panel 23 Nov 16:11), so a heights decree can be in force at 53 s and send both bots off the roof
    // before its collapse is warned; this scene tests the collapse flee alone, so bagged decrees are off here and back on at the end (changed on purpose).
    C.DECREES.on = false;
    G.setSeed(12345); G.setBots(2); G.reset(); G.teleport(0, -50);
    const roof = G.floors().find((f) => f.sec === 'ROOF'), cx = (roof.x0 + roof.x1) / 2, cz = (roof.z0 + roof.z1) / 2;
    K.sp(C.FIRST_WAVE_S - C.COLLAPSE_WARN_S - 1.5);
    G.placeBot(0, cx - 1.5, cz); G.placeBot(1, cx + 1.5, cz); G.setBotHp(0, 1e4); G.setBotHp(1, 1e4); G.hitBy(1, 0, 1); G.hitBy(0, 1, 1); G.step(30);
    const b0 = G.bots().list; o.start = [b0[0].zone, b0[1].zone]; o.fight = [b0[0].mode, b0[1].mode];
    K.sp(C.COLLAPSE_WARN_S + 3); const b = G.bots().list; o.dead = [b[0].dead, b[1].dead]; o.zone = [b[0].zone, b[1].zone];
    C.DECREES.on = true; G.setBots(0); G.reset(); return o;
  });
  check('62 flee: two bots fighting on the roof leave it within the 5 s warning and live', fl.start.every((z) => z === 'ROOF') && fl.fight.every((m) => m === 'fight')
    && !fl.dead[0] && !fl.dead[1] && fl.zone.every((z) => z !== 'ROOF'), JSON.stringify(fl));
  // 63 Heal: a bot at 30 health goes to the nearest charged altar and heals.
  const hl = await g(() => {
    const G = __game, K = window.__k, o = {};
    G.setSeed(12345); G.setBots(1); G.reset(); G.teleport(0, -50);
    const a = G.altars()[0]; G.placeBot(0, a.x + 6, a.z); G.setBotHp(0, 30); let mode = '';
    let top = 0; for (let n = 0; n < 12 * 60; n++) { G.step(1); const q = G.bots().list[0]; if (q.mode === 'heal') mode = 'heal'; top = Math.max(top, q.hp); }
    const b = G.bots().list[0]; o.mode = mode; o.hp = Math.round(top); o.near = +Math.hypot(b.x - a.x, b.z - a.z).toFixed(1);
    G.setBots(0); G.reset(); return o;
  });
  check('63 heal: a bot at 30 health walks to a charged altar and heals past 60', hl.mode === 'heal' && hl.hp >= 60, JSON.stringify(hl));
  // 64 Royale end (batch 9d): in a match H and the Hunt button do nothing; the player broken by a bot = frozen loss banner with the place and New run;
  // New run brings every bot back; a fall into the void in a match is a loss too; the last suit standing starts the hunt by itself.
  const re = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {};
    G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); let r = G.royale();
    o.btnHidden = r.btn === 'none'; G.huntButton(); dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyH' })); o.hNoop = G.royale().phase === 'royale';
    G.hitBy(0, -1, 1e4); r = G.royale(); o.lost = r.phase === 'lost' && r.lostIn === 'royale'; o.place = r.rule; o.voice = r.voice; o.btn = r.btn; o.btnText = r.btnText; o.cause = G.player().cause;
    const t0 = r.t, b0 = JSON.stringify(G.bots().list.map((q) => [q.x, q.z])); G.step(60); o.frozen = G.royale().t === t0 && JSON.stringify(G.bots().list.map((q) => [q.x, q.z])) === b0;
    G.huntButton(); const b1 = G.bots(); o.newRun = G.royale().phase === 'royale' && b1.list.every((q) => !q.dead && q.inScene) && !G.state().dead && G.state().hp === 100;
    G.teleport(0, 40.5); G.knock(0, 14); K.sp(C.RESPAWN_S + 1); r = G.royale(); o.fall = r.phase === 'lost' && G.player().cause === 'fall';
    G.reset(); for (let i = 0; i < G.config.BOTS.count; i++) G.hitBot(i, 1e4); G.step(1); r = G.royale(); const h = G.hunt();
    o.hunt = r.phase === 'wake' && !h.statue && h.seal && G.bots().list.every((q) => q.dead && !q.inScene);
    G.setBots(0); G.reset(); return o;
  });
  check('64 royale end: H off in a match, broken player = frozen loss with place and New run, New run restores bots, void fall = loss, last suit standing starts the hunt',
    re.btnHidden && re.hNoop && re.lost && new RegExp(`Place ${NS} of ${NS}`).test(re.place) && re.voice.length > 0 && re.btn === 'block' && re.btnText === 'New run' && re.cause === 'hit' && re.frozen && re.newRun && re.fall && re.hunt, JSON.stringify(re));
  // 65 Whole matches, 6 seeds (12345, 2, 3, 4, 5, 6), the player driven by the bot brain (autopilot) and the match watched to the end:
  // decided in about 3-4 min (165-255 s), always-true checks every tick, every suit that is out has a cause, bots took plates and boons, no spawn wins more than 3 of 6.
  const ms = await g(() => {
    const G = __game, C = G.config, out = [], viol = [], bad = (s) => { if (viol.length < 5) viol.push(s); }, wins = {}, wins6 = {};
    const CAUSES = ['hit', 'hazard', 'fall', 'bleed', 'drop'];
    let plates = 0, boons = 0;
    // Hunter slot (batch 10): every tick at most maxHunters bots target the player by the on-sight switch; flags, slots and targets agree.
    const hv = [], hbad = (x) => { if (hv.length < 5) hv.push(x); }; let see3 = 0, maxOnP = 0, maxHunt = 0;
    // Batch 11: leader rule every tick (from suit state: held plates + 4 * kills, -1 = out; the previous leader keeps a tie); hunter cap every tick
    // (fighting the player for any reason but hitting back: at most BOT.maxHunters, BOUNTY.maxHunters while the bounty lies on the player);
    // bounty share = bots fighting the leader among bots that see it (sampled every 5 ticks), bounty in force vs not; GDD sim numbers.
    const lv = [], lbad = (x) => { if (lv.length < 5) lv.push(x); }; let lchanges = 0, leadersSeen = 0, preLeadBad = 0;
    const cv = [], cbad = (x) => { if (cv.length < 5) cv.push(x); }; let capOff = 0, capOn = 0, bountyPTicks = 0;
    const sh = { onSee: 0, onFight: 0, offSee: 0, offFight: 0 }, sims = [];
    // Batch 12: decree slot over the matches: every warning >= DECREE.warnS before its start, never begun under a collapse banner, slots never overlap
    // (bagged and bounty), HUD writes only on change; bots off Our heights unless crossing them to leave a warned section; breaks and marks counted.
    const dv = [], dbad = (x) => { if (dv.length < 5) dv.push(x); }; let capMark = 0, markPTicks = 0, hiStay = 0; const dsum = [];
    // Batch 13a (panel 23 Nov 16:11): banners never overlap (no collapse banner and no kennel warning begins during a decree warning);
    // heights breaks within DECREES.warnFreeS of standing on a warned section are counted (must be 0).
    let bannerOv = 0, hiNear = 0, hiBrk = 0;
    const rule = (st, prev) => { let best = -1, bp = 0, bk = 0; st.forEach((v, i) => { if (v < 0) return; const p = v % 4, k = (v - p) / 4; if (p > bp || (p === bp && k > bk)) { best = i; bp = p; bk = k; } });
      if (best >= 0 && prev >= 0 && st[prev] >= 0 && st[prev] === st[best]) best = prev; return best; };
    // Batch 12: 12 seeds (was 6): bagged decrees share the slot with the bounty by design, so bounties are rarer per match; more matches keep the
    // bounty share in 72 at its sample bar. The 6-seed win rule of 65 stays on the first 6; every other rule holds for all 12.
    for (const seed of [12345, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]) {
      G.setSeed(seed); G.setBots(G.config.BOTS.count); G.reset(); G.autoPlayer(true); G.setWatch(true);
      let prevAlive = G.config.BOTS.count + 1, t = 0, prevL = -1; const leadS = {};
      let prevSt = 0, prevKey = '', cur = null, prevKw = false; const iv = [], stay = {}, wsT = {}, brk = {};
      for (; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale();
        const l = G.leader(), st = G.suitsState();
        if (l.phase === 'royale') {
          const want = rule(st, prevL); if (l.id !== want) lbad(`s${seed} t${t} leader ${l.id} want ${want} prev ${prevL} ${st}`);
          if (l.id >= 0 && st.every((v) => v <= 0)) preLeadBad++;
          if (l.id !== prevL) lchanges++; if (l.id >= 0) { leadersSeen++; leadS[l.id] = (leadS[l.id] || 0) + 1; }
          if ((l.crownOn && l.crownId !== l.id) || (!l.crownOn && l.id >= 0)) lbad(`s${seed} t${t} crown on ${l.crownId} leader ${l.id}`);
          prevL = l.id;
        }
        // Batch 12 (panel 23 Nov 15:11): a marked player raises the cap to DECREES.markCap (the bounty's 3 still wins); changed on purpose.
        const hc = G.hunters(); if (hc.bountyP) { bountyPTicks++; if (hc.capOnP > capOn) capOn = hc.capOnP; } else if (hc.markP) { markPTicks++; if (hc.capOnP > capMark) capMark = hc.capOnP; } else if (hc.capOnP > capOff) capOff = hc.capOnP;
        if (hc.capOnP > hc.max || hc.max !== (hc.bountyP ? C.BOUNTY.maxHunters : hc.markP ? C.DECREES.markCap : C.BOT.maxHunters)) cbad(`s${seed} t${t} ${JSON.stringify(hc)}`);
        const dc = G.decree();
        if (dc.st >= 2 && (prevSt < 2 || dc.key !== prevKey)) { if (cur && cur.end < 0) cur.end = G.royale().t; if (l.bw >= 0) dbad(`s${seed} t${t} ${dc.key} warning under a collapse banner`); cur = { key: dc.key, warn: G.royale().t, start: -1, end: -1 }; iv.push(cur); }
        if (cur && dc.st === 3 && cur.start < 0) cur.start = G.royale().t;
        if (cur && dc.st < 2 && cur.end < 0) cur.end = G.royale().t;
        if (dc.st === 2 && (l.bw >= 0 || (dc.kw && !prevKw))) { bannerOv++; dbad(`s${seed} t${t} banner over the ${dc.key} warning`); }
        prevKw = dc.kw;
        if (dc.st >= 2 && dc.key === 'heights') {
          const now = G.royale().t, secSt = G.state().sec;
          for (const q of G.suits()) {
            if (q.floor && secSt[q.floor] === 1) wsT[q.id] = now;
            if (brk[q.id] !== undefined && q.breaks > brk[q.id]) { hiBrk++; if (wsT[q.id] !== undefined && now - wsT[q.id] < C.DECREES.warnFreeS - 1e-6) hiNear++; }
            brk[q.id] = q.breaks;
          }
        } else for (const k in brk) delete brk[k];
        prevSt = dc.st; prevKey = dc.key;
        if (dc.st === 3 && dc.key === 'heights') {
          const bl = G.bots().list;
          for (const q of G.suits()) { if (q.id === 0) continue; const b = bl[q.id - 1]; if (q.hi && b.mode !== 'flee') { stay[q.id] = (stay[q.id] || 0) + C.STEP; if (stay[q.id] > hiStay) hiStay = stay[q.id]; } else stay[q.id] = 0; }
        }
        if (t % 5 === 0 && l.id >= 0) {
          const pl = G.player(), bl = G.bots().list, L = l.id === 0 ? pl : bl[l.id - 1], on = l.dec === 3 && l.decTgt === l.id;
          for (const q of bl) {
            if (q.dead || q.id === l.id || Math.abs(q.y - L.y) >= 2 || Math.hypot(q.x - L.x, q.z - L.z) > C.VISION_R) continue;
            const f = q.tgt === l.id && q.mode === 'fight' ? 1 : 0; if (on) { sh.onSee++; sh.onFight += f; } else { sh.offSee++; sh.offFight += f; }
          }
        }
        if (r.alive > prevAlive) bad(`s${seed} t${t} alive rose`); prevAlive = r.alive;
        const hu = G.hunters();
        if (hu.huntOnP > hu.max || hu.slots > hu.max || hu.flagged !== hu.slots || hu.huntOnP > hu.flagged) hbad(`s${seed} t${t} ${JSON.stringify(hu)}`);
        // Batch 12: on-sight switches are compared with BOT.maxHunters only while the cap is 1 (a mark or a bounty raises it on purpose).
        if (hu.seeP >= 3) see3++; if (hu.onP > maxOnP) maxOnP = hu.onP; if (hu.max === C.BOT.maxHunters && hu.huntOnP > maxHunt) maxHunt = hu.huntOnP;
        if (t % 20 === 0) {
          for (const q of G.bots().list) {
            if (!q.dead && (q.hp <= 0 || q.hp > C.MAX_HP + 1e-6)) bad(`s${seed} t${t} bot${q.id} hp ${q.hp}`);
            if (!q.standOk) bad(`s${seed} t${t} bot${q.id} off floor`);
            if (q.dead && q.inScene) bad(`s${seed} t${t} bot${q.id} out but drawn`);
          }
        }
        if (r.decidedAt >= 0) break;
      }
      const b = G.bots(), p = G.player(), r = G.royale();
      const all = b.list.map((q) => ({ spawn: q.spawn, dead: q.dead, cause: q.cause })).concat([{ spawn: C.PLAYER_SPAWN, dead: p.dead, cause: p.cause }]);
      const win = all.find((q) => !q.dead), nocause = all.filter((q) => q.dead && !CAUSES.includes(q.cause)).length;
      if (win) { wins[win.spawn] = (wins[win.spawn] || 0) + 1; if (out.length < 6) wins6[win.spawn] = (wins6[win.spawn] || 0) + 1; }
      plates += b.list.reduce((a, q) => a + q.plates, 0); boons += b.list.reduce((a, q) => a + q.boons, 0);
      {
        const dd = G.decree(); if (cur && cur.end < 0) cur.end = G.royale().t;
        for (let i = 0; i < iv.length; i++) {
          const a = iv[i]; if (a.start >= 0 && a.start - a.warn < C.DECREE.warnS - 1e-6) dbad(`s${seed} ${a.key} told ${(a.start - a.warn).toFixed(2)} s`);
          if (i > 0 && a.warn < iv[i - 1].end - 1e-6) dbad(`s${seed} overlap ${iv[i - 1].key}/${a.key}`);
        }
        const inForce = iv.filter((a) => a.start >= 0 && a.key !== 'bounty').reduce((x, a) => x + (a.end - a.start), 0), nb = iv.filter((a) => a.key !== 'bounty').length;
        if (dd.writes > inForce + 3 * nb + 2) dbad(`s${seed} HUD writes ${dd.writes} for ${inForce.toFixed(0)} s`);
        dsum.push({ seed, told: iv.length, w: iv.map((a) => +a.warn.toFixed(2)), n: dd.n, keys: iv.map((a) => a.key).join(','), brkP: dd.brkP, brkB: dd.brkB, writes: dd.writes });
      }
      const lw = G.leader(), top = Object.entries(leadS).sort((x, y) => y[1] - x[1])[0], winId = b.list.concat([{ id: 0, dead: p.dead }]).find((q) => !q.dead);
      sims.push({ seed, topLeader: top ? +top[0] : -1, winId: winId ? winId.id : -1, pPlates: p.plates, bounties: lw.n, paid: lw.paid });
      const place = p.dead ? 1 + b.list.filter((q) => !q.dead || q.diedAt > p.diedAt).length : 1, firstOut = Math.min(...b.list.filter((q) => q.dead).map((q) => q.diedAt), p.dead ? p.diedAt : 1e9);
      out.push({ seed, decided: +r.decidedAt.toFixed(1), winner: win ? win.spawn : -1, player: p.dead ? p.cause + '@' + Math.round(p.diedAt) : 'won', place, playerFirst: p.dead && p.diedAt <= firstOut, nocause });
      G.setWatch(false); G.autoPlayer(false);
    }
    G.setBots(0); G.reset(); return { out, viol, wins, wins6, plates, boons, hunt: { hv, see3, maxOnP, maxHunt }, lead: { lv, lchanges, leadersSeen, preLeadBad }, cap: { cv, capOff, capOn, bountyPTicks, capMark, markPTicks }, sh, sims, dec: { dv, hiStay: +hiStay.toFixed(2), dsum, bannerOv, hiNear, hiBrk } };
  });
  // Batch 15: the band is read from CONFIG.ROYALE.band; the owner changed it on purpose (23 Nov 22:05: floor 150 s, was 165).
  check(`65 whole matches x12: decided in ${C0.ROYALE.band[0]}-${C0.ROYALE.band[1]} s, 0 broken invariants, every out has a cause, bots take plates and boons, no spawn wins more than 3 of 6`,
    ms.out.every((m) => m.decided >= C0.ROYALE.band[0] && m.decided <= C0.ROYALE.band[1] && m.nocause === 0) && ms.viol.length === 0 && ms.plates > 0 && ms.boons > 0 && Math.max(...Object.values(ms.wins6)) <= 3, JSON.stringify(ms));
  // 67 Hunter slot over the 6 whole matches of 65 (owner, 23 Nov 14:04): with 3 or more bots seeing the player, at most BOT.maxHunters bots
  // target the player by the on-sight switch at any tick; the case did happen; slot count, flags and targets agree every tick.
  check('67 hunter slot: at most maxHunters bots switch to the player at any tick over 6 matches (3+ bots seeing the player happened)',
    ms.hunt.hv.length === 0 && ms.hunt.see3 > 0 && ms.hunt.maxHunt <= 1 && ms.hunt.maxHunt === 1, JSON.stringify(ms.hunt) + ' places ' + ms.out.map((m) => m.place).join(','));
  // 68 Hunter slot frees and is claimed again: one hunter among 3 fighting bots that see the player; its death frees the slot and another bot claims it;
  // out of sight the slot is held until BOT.hunterLoseS, then freed; back in sight it is claimed again.
  const hs2 = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}, fight = (a, b) => { G.hitBy(a, b, 1); G.hitBy(b, a, 1); };
    G.setSeed(12345); G.setBots(3); G.reset(); G.teleport(0, -50); G.setHp(1e9);
    G.placeBot(0, 0, 10); G.placeBot(1, 2.5, 10); G.placeBot(2, -2.5, 10); for (let i = 0; i < 3; i++) G.setBotHp(i, 1e9); fight(0, 1); G.hitBy(1, 2, 1); G.hitBy(2, 0, 1); K.sp(0.5);
    o.before = G.hunters();
    G.teleport(0, 16); K.sp(0.6); o.one = G.hunters();
    const h1 = o.one.id - 1; G.hitBot(h1, 1e12); const rest = [0, 1, 2].filter((i) => i !== h1); fight(rest[0], rest[1]); K.sp(0.1); o.freed = G.hunters();
    K.sp(0.6); o.two = G.hunters();
    G.teleport(0, -50); K.sp(C.BOT.hunterLoseS - 0.5); o.held = G.hunters(); K.sp(1); o.lost = G.hunters();
    G.teleport(0, 16); fight(rest[0], rest[1]); K.sp(0.6); o.again = G.hunters();
    G.setBots(0); G.reset(); return o;
  });
  check('68 hunter slot: one of 3 switches; frees on hunter death and another claims it; held until hunterLoseS out of sight, then freed; claimed again in sight',
    hs2.before.slots === 0 && hs2.one.seeP === 3 && hs2.one.slots === 1 && hs2.one.onP === 1 && hs2.one.huntOnP === 1 && hs2.freed.slots === 0 && hs2.freed.frees === 1
    && hs2.two.slots === 1 && hs2.two.id !== hs2.one.id && hs2.two.claims === 2 && hs2.held.slots === 1 && hs2.lost.slots === 0 && hs2.lost.frees === 2 && hs2.again.slots === 1 && hs2.again.claims === 3, JSON.stringify(hs2));
  // 69 Leader rule (batch 11) every tick over the 6 matches of 65: the leader equals the rule from suit state (most plates held, then kills; a tie keeps the
  // current leader); no leader while nobody has a plate or a kill; the crown sits on the leader and nowhere else. Leaders did happen.
  check('69 leader: matches the rule every tick over 6 matches, no flip on a tie, none before the first plate or kill, crown on the leader only',
    ms.lead.lv.length === 0 && ms.lead.preLeadBad === 0 && ms.lead.leadersSeen > 0 && ms.lead.lchanges > 6, JSON.stringify(ms.lead));
  // 72 Hunter cap (owner, 23 Nov 14:35) every tick over the 6 matches: bots fighting the player for any reason but hitting back <= BOT.maxHunters,
  // <= BOUNTY.maxHunters while the bounty lies on the player; bots fight the leader more while the bounty is in force (share of bots that see it, in matches
  // and controlled: same scene with BOUNTY.chase 0 as the control).
  const shOn = ms.sh.onFight / Math.max(1, ms.sh.onSee), shOff = ms.sh.offFight / Math.max(1, ms.sh.offSee);
  // Controlled share: a bot leader under a bounty in force before the peace ends, 4 bots 6 m around it that nobody hit; share of bot-ticks fighting it,
  // with BOUNTY.chase as set vs 0 (control). Same seed, same places.
  const bs = await g(() => {
    const G = __game, C = G.config, keep = C.BOUNTY.chase, o = {};
    // Batch 12: bagged decrees off for this controlled bounty scene (they share the slot by design), back on at the end.
    C.DECREES.on = false;
    const one = (ch) => {
      C.BOUNTY.chase = ch; G.setSeed(21); G.setBots(5); G.reset(); G.setHp(1e9); for (let i = 0; i < 5; i++) G.setBotHp(i, 1e9); G.teleport(0, -40);
      const hold = () => { G.placeBot(0, 0, -52); for (let i = 1; i < 5; i++) G.placeBot(i, 6 * Math.cos(i * 1.5708), -52 + 6 * Math.sin(i * 1.5708)); };
      G.setTime(61); G.plateTo(0, 'stalker'); G.plateTo(0, 'howler'); let n = 0, f = 0;
      for (let k = 0; k < 60 / C.STEP && G.leader().dec !== 3; k++) { hold(); G.step(1); }
      const on = G.leader().dec === 3 && G.leader().decTgt === 1;
      for (let k = 0; k < 12 / C.STEP; k++) { hold(); G.step(1); for (const q of G.bots().list.slice(1)) { n++; if (q.tgt === 1 && q.mode === 'fight') f++; } }
      return { on, t: +G.leader().t.toFixed(1), share: +(f / n).toFixed(3) };
    };
    try { o.bounty = one(keep); o.control = one(0); } finally { C.BOUNTY.chase = keep; C.DECREES.on = true; G.setBots(0); G.reset(); }
    return o;
  });
  check('72 cap and bounty in matches: player cap holds every tick (1, or 3 under a bounty on the player), bots fight a seen leader more under the bounty',
    ms.cap.cv.length === 0 && ms.cap.capOff <= C0.BOT.maxHunters && ms.cap.capOn <= C0.BOUNTY.maxHunters && ms.cap.capMark <= C0.DECREES.markCap && ms.sh.onSee > 50 && shOn > shOff
    && bs.bounty.on && bs.control.on && bs.bounty.t < 120 && bs.bounty.share >= 0.15 && bs.control.share === 0,
    JSON.stringify(ms.cap) + ` share on ${shOn.toFixed(2)} (${ms.sh.onSee}) off ${shOff.toFixed(2)} (${ms.sh.offSee}) controlled ${JSON.stringify(bs)}`);
  {
    const sm = ms.sims, lw = sm.filter((x) => x.topLeader >= 0 && x.topLeader === x.winId).length, pp = sm.filter((x) => x.pPlates > 0).length;
    SIMS.push(`leader win share (longest leader wins) ${lw} of ${sm.length}; player >=1 plate ${pp} of ${sm.length}; decided ${ms.out.map((m) => m.decided).join(',')}`,
      `per seed decided/place/player out/winner spawn: ${ms.out.map((m) => `${m.seed} ${m.decided}/${m.place}/${m.player}/${m.winner}`).join('; ')}`,
      `bounties ${sm.map((x) => x.bounties).join(',')} paid ${sm.map((x) => x.paid).join(',')}; fight share on ${shOn.toFixed(2)} off ${shOff.toFixed(2)}; bounty-on-player ticks ${ms.cap.bountyPTicks}, cap max off ${ms.cap.capOff} on ${ms.cap.capOn}`);
  }
  // 70 Crown, HUD and minimap (scripted, 3 bots in the core hall, no fights): no leader at the start; a bot with a plate leads, crown on its head shown
  // only while the player sees it; a tie with a suit earlier in suit order keeps the leader; a kill breaks the tie; the player with 2 plates leads (crown shown, minimap ring);
  // the HUD line is written only on change (no writes over 120 steps with nothing changing).
  const cr = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {};
    G.setSeed(12345); G.setBots(3); G.reset(); G.setHp(1e9); for (let i = 0; i < 3; i++) G.setBotHp(i, 1e9);
    const hold = () => { G.placeBot(0, 0, -50); G.placeBot(1, 3, -50); G.placeBot(2, -3, -50); };
    hold(); G.teleport(0, 0); K.sp(0.1); o.start = G.leader();
    G.plateTo(1, 'stalker'); hold(); K.sp(0.1); o.unseen = G.leader(); G.miniPixel(0, 0); o.unseenMini = G.leader().mini;
    G.teleport(0, -45); hold(); K.sp(0.1); o.seen = G.leader(); G.miniPixel(0, 0); o.seenMini = G.leader().mini;
    G.plateTo(0, 'howler'); hold(); K.sp(0.1); o.tie = G.leader();
    G.hitBy(0, 2, 1e12); hold(); K.sp(0.1); o.kill = G.leader();
    const w0 = G.leader().writes; for (let n = 0; n < 120; n++) { hold(); G.step(1); } o.quietWrites = G.leader().writes - w0;
    G.plateTo(-1, 'stalker'); G.plateTo(-1, 'howler'); hold(); K.sp(0.1); o.player = G.leader(); G.miniPixel(0, 0); o.playerMini = G.leader().mini;
    G.setBots(0); G.reset(); o.after = G.leader(); return o;
  });
  check('70 crown and HUD: none at start; plate = leader with crown shown only in vision; tie keeps; kill breaks the tie; player leader; HUD written only on change',
    cr.start.id === -1 && !cr.start.crownOn && cr.start.hudShown === 'none' && cr.unseen.id === 2 && cr.unseen.crownId === 2 && !cr.unseen.crownShown && !cr.unseenMini
    && /Leader: Fa suit/.test(cr.unseen.hud) && cr.unseen.hudShown === 'block' && cr.seen.crownShown && cr.seenMini && cr.tie.id === 2 && cr.kill.id === 1 && cr.kill.crownId === 1
    && cr.quietWrites === 0 && cr.player.id === 0 && cr.player.crownId === 0 && cr.player.crownShown && cr.playerMini && /Leader: You/.test(cr.player.hud)
    && cr.after.id === -1 && !cr.after.crownOn && cr.after.hudShown === 'none', JSON.stringify(cr));
  // 71 Bounty decree (scripted, 3 bots kept in the core hall at huge health): told >= DECREE.warnS before it starts (voice, banner, countdown), only after
  // BOUNTY.afterS of one leader, never over a collapse banner (queued when a collapse warning is near); lasts durS; breaking the leader in the warning pays nothing;
  // breaking a non-leader pays nothing; breaking the leader in force fills the breaker's charge meter (batch 15) and ends it; a broken leader with no breaker pays nobody;
  // the wake ends it and none in the hunt; new run x3 resets it; text keys exist.
  const bt = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}, B = C.BOUNTY, D = C.DECREE;
    // Batch 12: bagged decrees share the slot by design; this scene tests the bounty alone, so they are switched off here and back on at the end.
    C.DECREES.on = false;
    const hold = () => { G.placeBot(0, 0, -50); G.placeBot(1, 3, -50); G.placeBot(2, -3, -50); };
    const start = (s) => { G.setSeed(s); G.setBots(3); G.reset(); G.setHp(1e9); for (let i = 0; i < 3; i++) G.setBotHp(i, 1e9); G.teleport(0, -45); hold(); };
    const run = (sec, each) => { for (let n = 0; n < Math.round(sec / C.STEP); n++) { hold(); G.step(1); if (each && each()) return true; } return false; };
    let overlap = 0; const watch = () => { const l = G.leader(); if (l.banner && l.bw >= 0) overlap++; return false; };
    // A: leader from t 27; due at 52, within clearS of collapse warning 0 (55 s), so the warning is queued until that banner ends (60 s).
    // Batch 13 (panel 23 Nov 16:11, P1): clearS is 5 s (was 20 s), so the lead starts at 27 s instead of 15 s; changed on purpose.
    start(1); run(27, watch); G.plateTo(0, 'stalker'); const t0 = G.leader().t;
    run(27, watch); G.plateTo(0, 'howler'); o.queued = G.leader().dec;
    run(80, () => { watch(); return G.leader().dec === 2; }); const w = G.leader(); o.warn = { at: w.warnAt, voice: w.voice, rule: w.rule, shown: w.bannerShown, sinceLead: +(w.warnAt - t0).toFixed(2) };
    G.plateTo(0, 'stalker');
    run(10, () => { watch(); return G.leader().dec === 3; }); const s1 = G.leader(); o.on = { startAt: s1.startAt, lead: +(s1.startAt - s1.warnAt).toFixed(2), hud: s1.hud, bannerOff: !s1.banner };
    // C: bot 2 breaks a non-leader in force: nothing paid, bounty goes on; then bot 2 breaks the leader: its ultimate is reset, the bounty ends.
    G.hitBy(1, 2, 1e12); hold(); G.step(1); o.nonLeader = { paid: G.leader().paid, dec: G.leader().dec };
    // Game changed on purpose (batch 15): the bounty fills the breaker's charge meter (ULT.bounty) instead of resetting a cooldown. The breaker starts empty and the leader at 1 hp,
    // so the hit and the kill give only ULT.dealt + ULT.kill (well under full): a full meter after the break proves the bounty paid.
    G.setCharge(1, 0); G.setBotHp(0, 1); G.hitBy(1, 0, 1e12); const chPaid = G.chargeOf(1); hold(); G.step(1); const c = G.leader(); o.paid = { paid: c.paid, to: c.paidTo, ch: chPaid, dec: c.dec, why: c.endWhy, leader: c.id };
    o.overlap = overlap;
    // Natural end: a fresh leader at t 61 (clear window), refreshed plates; the bounty lasts durS.
    start(2); run(61); G.plateTo(1, 'stalker'); run(30); G.plateTo(1, 'howler');
    run(40, () => G.leader().dec === 3); const n0 = G.leader(); G.plateTo(1, 'stalker'); run(B.durS + 1, () => G.leader().dec === 0);
    const n1 = G.leader(); o.natural = { dur: +(n1.endAt - n0.startAt).toFixed(2), why: n1.endWhy, again: false };
    run(B.afterS + D.warnS + 5); o.natural.again = G.leader().n > 1;
    // B: break the leader during the warning: nothing paid, the bounty ends ('out').
    start(3); run(61); G.plateTo(0, 'stalker'); run(60, () => G.leader().dec === 2); G.hitBy(-1, 0, 1e12); hold(); G.step(1);
    const b = G.leader(); o.inWarn = { paid: b.paid, dec: b.dec, why: b.endWhy, wasWarn: b.warnAt > 0 };
    // E: leader broken with no breaker (fall-like): pays nobody.
    start(4); run(61); G.plateTo(2, 'stalker'); run(60, () => G.leader().dec === 3); G.hitBot(2, 1e12); hold(); G.step(1);
    const e = G.leader(); o.noBreaker = { paid: e.paid, dec: e.dec, why: e.endWhy };
    // F: the wake ends it; none in the hunt.
    start(5); run(61); G.plateTo(0, 'stalker'); run(60, () => G.leader().dec === 3); G.startHunt(); const f = G.leader(); o.wake = { dec: f.dec, why: f.endWhy, crown: f.crownOn, hud: f.hudShown };
    let huntDec = 0; run(30, () => { if (G.leader().dec !== 0) huntDec++; return false; }); o.wake.huntDec = huntDec;
    // G: new run x3 resets it.
    o.fresh = [];
    for (let r = 0; r < 3; r++) { G.setSeed(10 + r); G.setBots(3); G.reset(); const l = G.leader(); o.fresh.push(l.dec === 0 && l.n === 0 && l.paid === 0 && l.id === -1 && !l.crownOn && l.endAt === -1 && G.player().kills === 0); }
    o.keys = G.decreeKeys();
    C.DECREES.on = true; G.setBots(0); G.reset(); return o;
  });
  check('71 bounty: queued off collapse banners, told >= 5 s after 25 s of lead, lasts 40 s, pays only for breaking the leader in force, ends on leader out and at the wake, none in the hunt, new run x3 resets, keys',
    bt.queued === 1 && bt.warn.at >= 60 && bt.warn.sinceLead >= 25 && /bounty lieth/.test(bt.warn.voice) && /Bounty on the leader \(Dao suit\) in \d s/.test(bt.warn.rule) && bt.warn.shown === 'block'
    && bt.on.lead >= 5 - 1e-6 && /bounty \d+ s/.test(bt.on.hud) && bt.on.bannerOff && bt.nonLeader.paid === 0 && bt.nonLeader.dec === 3
    && bt.paid.paid === 1 && bt.paid.to === 2 && bt.paid.ch === C0.ULT.full && C0.ULT.dealt + C0.ULT.kill < C0.ULT.full && bt.paid.dec === 0 && bt.paid.why === 'out' && bt.paid.leader === 2 && bt.overlap === 0
    && Math.abs(bt.natural.dur - 40) < 0.1 && bt.natural.why === 'time' && !bt.natural.again
    && bt.inWarn.wasWarn && bt.inWarn.paid === 0 && bt.inWarn.dec === 0 && bt.inWarn.why === 'out' && bt.noBreaker.paid === 0 && bt.noBreaker.dec === 0 && bt.noBreaker.why === 'out'
    && bt.wake.dec === 0 && bt.wake.why === 'wake' && !bt.wake.crown && bt.wake.hud === 'none' && bt.wake.huntDec === 0 && bt.fresh.every((x) => x) && bt.keys.length === 0, JSON.stringify(bt));
  // 84 Bounty paced like a decree (batch 13 P3, panel 23 Nov 16:11): with bagged decrees on, a bounty that comes due during the gap waits for it (G.decNext),
  // and a gap drawn from the gap bag follows the bounty before the next bagged decree is told.
  const bg = await g(() => {
    const G = __game, C = G.config, o = {}, D = C.DECREES;
    const hold = () => { G.placeBot(0, 0, -50); G.placeBot(1, 3, -50); G.placeBot(2, -3, -50); };
    const run = (sec, each) => { for (let n = 0; n < Math.round(sec / C.STEP); n++) { hold(); G.step(1); if (each && each()) return true; } return false; };
    G.setSeed(7); G.setBots(3); G.reset(); G.setHp(1e9); for (let i = 0; i < 3; i++) G.setBotHp(i, 1e9); G.teleport(0, -45); hold(); G.setDecNext(100);
    run(61); G.plateTo(0, 'stalker'); const lead = G.leader().t;
    let early = -1; run(100 - 61 - 0.1, () => { if (G.decree().st !== 0 && early < 0) early = G.royale().t; G.plateTo(0, 'stalker'); return false; });
    o.due = +(lead + C.BOUNTY.afterS).toFixed(2); o.early = early;
    run(10, () => G.leader().dec === 2); const w = G.leader(); o.warnAt = +w.warnAt.toFixed(2); o.key = w.decKey;
    run(C.DECREE.warnS + C.BOUNTY.durS + 2, () => { G.plateTo(0, 'stalker'); return G.leader().dec === 0 && G.leader().endAt > 0; });
    const e = G.leader(), d = G.decree(); o.endAt = +e.endAt.toFixed(2); o.why = e.endWhy; o.next = +d.next.toFixed(2);
    let nextWarn = -1; run(40, () => { const x = G.decree(); if (x.st >= 2 && x.key !== 'bounty') { nextWarn = G.royale().t; return true; } return false; });
    o.nextWarn = +nextWarn.toFixed(2); o.gapMin = Math.min(...D.gap);
    G.setBots(0); G.reset(); return o;
  });
  check('84 bounty paced like a decree: due during the gap it waits for it; a drawn gap follows it before the next decree',
    bg.early < 0 && bg.due < 100 && bg.warnAt >= 100 - 1e-6 && bg.key === 'bounty' && bg.why === 'time' && bg.next >= bg.endAt + bg.gapMin - 1e-6 && bg.nextWarn >= bg.endAt + bg.gapMin - 1e-6, JSON.stringify(bg));
  // 73 Player cap (scripted): after peace, 3 bots near the player that nobody hit: at most 1 fights the player at any tick, and one does;
  // in peace the player hits 2 of them: both answer (hitting back is not capped); a bounty on the player lets up to 3 fight it, back to 1 the tick it ends.
  const pc = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = { near: 0, nearMax: 0, hitMax: 0, onMax: 0, afterMax: 0, afterBad: 0 };
    // Batch 12: bagged decrees off for this bounty scene (they share the slot; a mark would also change the cap), back on at the end.
    C.DECREES.on = false;
    G.setSeed(7); G.setBots(3); G.reset(); G.setHp(1e9); for (let i = 0; i < 3; i++) G.setBotHp(i, 1e9);
    G.setTime(C.BOT.engage.peaceS + C.BOT.engage.rampS + 1); G.teleport(0, -45);
    const near = () => { G.placeBot(0, 2, -45); G.placeBot(1, -2, -45); G.placeBot(2, 0, -43); };
    for (let n = 0; n < 240; n++) { near(); G.step(1); const h = G.hunters(); if (h.capOnP > o.nearMax) o.nearMax = h.capOnP; }
    G.setBots(3); G.reset(); G.setHp(1e9); for (let i = 0; i < 3; i++) G.setBotHp(i, 1e9); G.teleport(0, -45);
    for (let n = 0; n < 60; n++) { near(); G.step(1); }
    G.hitBy(-1, 0, 1); G.hitBy(-1, 1, 1);
    for (let n = 0; n < 30; n++) { near(); G.step(1); const h = G.hunters(), f = G.bots().list.filter((q) => q.tgt === 0 && q.mode === 'fight').length; if (f > o.hitMax) o.hitMax = f; }
    G.setBots(5); G.reset(); G.setHp(1e9); for (let i = 0; i < 5; i++) G.setBotHp(i, 1e9); G.teleport(0, -45);
    const ring = () => { for (let i = 0; i < 5; i++) G.placeBot(i, 3 * Math.cos(i * 1.256), -45 + 3 * Math.sin(i * 1.256)); };
    G.setTime(61); G.plateTo(-1, 'stalker'); G.plateTo(-1, 'howler');
    for (let n = 0; n < 60 / C.STEP && G.leader().dec !== 3; n++) { ring(); G.step(1); }
    o.onP = G.leader().decTgt === 0; G.plateTo(-1, 'stalker'); G.plateTo(-1, 'howler');
    for (let n = 0, ended = false; n < 120 || !ended; n++) {
      ring(); G.step(1); const h = G.hunters();
      if (G.leader().dec === 3) { n = 0; if (h.capOnP > o.onMax) o.onMax = h.capOnP; } else { ended = true; if (h.capOnP > o.afterMax) o.afterMax = h.capOnP; }
      if (n > 1e5) break;
    }
    C.DECREES.on = true; G.setBots(0); G.reset(); return o;
  });
  check('73 player cap: 1 bot by any rule but hitting back, 2 answer the player\'s hits, up to 3 under a bounty on the player and back to 1 after',
    pc.nearMax === 1 && pc.hitMax >= 2 && pc.onP && pc.onMax >= 2 && pc.onMax <= 3 && pc.afterMax <= 1, JSON.stringify(pc));
  // 74 Budget with the crown: heaviest royale (every suit; batch 14: 9 on purpose, 7 cubs, tells) plus the crown on a seen bot leader; no shader compile, geometry flat.
  const bc = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9); G.plateTo(4, 'stalker');
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      for (let n = 0; n < 600; n++) {
        for (let i = 0; i < G.config.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5);
        G.step(1); const c = G.cubs(), l = G.leader();
        if (l.crownShown && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, crown: l.crownShown, cubs: c.list.filter((u) => u.alive && u.seen).length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setBots(0); G.reset(); }
    return best;
  });
  check(`74 budget with the crown: ${NS} suits + cubs + tells + crown (calls<500, tris<500k), no shader compile, geometry flat`,
    !!bc && bc.crown && bc.tells >= 3 && bc.calls < 500 && bc.tris < 500000 && bc.programs === base.programs && bc.geoms === base.geoms, JSON.stringify(bc));
  // ===== Batch 12: five bagged decrees, W dash, silence, heights, mark (panel 23 Nov 15:11) =====
  // Scripted decree scenes: one bot kept in the core hall so the match code runs; bagged requests pushed far away (forced decrees only).
  await g(() => { const G = __game, C = G.config; window.__d = {
    start(n) { G.setSeed(12345); G.setBots(n || 1); G.reset(); G.setDecNext(1e9); G.setHp(1e9); for (let i = 0; i < (n || 1); i++) G.setBotHp(i, 1e9); G.placeBot(0, 0, -50); },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    park() { G.placeBot(0, 0, -50); } }; });
  // 75 Decree bags: every cycle is the whole bag in a new order; same seed = same draws, another seed differs; once the bridges and every high floor have
  // fallen, the bags never pick the bridge or heights decree and no zone that has fallen (gone places skipped).
  const dbg = await g(() => {
    const G = __game, C = G.config, D = C.DECREES, names = ['which', 'first', 'gap', 'len', 'zones'], o = { cycles: true };
    const seq = (seed) => { G.setSeed(seed); G.setBots(1); G.reset(); const out = {}; for (const n of names) { const len = D[n].length; out[n] = []; if (n === 'first') for (let i = 0; i < len - 1; i++) G.drawDecBag(n); for (let i = 0; i < len * 3; i++) out[n].push(G.drawDecBag(n)); } return out; };
    const a = seq(777), b = seq(777), c = seq(778);
    for (const n of names) { const want = JSON.stringify(D[n].slice().sort()), len = D[n].length; for (let k = 0; k < 3; k++) if (JSON.stringify(a[n].slice(k * len, (k + 1) * len).sort()) !== want) o.cycles = false; }
    o.same = JSON.stringify(a) === JSON.stringify(b); o.differs = JSON.stringify(a) !== JSON.stringify(c);
    G.setBots(0); G.reset(); G.step(Math.round((C.FIRST_WAVE_S + 3 * C.WAVE_INTERVAL_S + C.COLLAPSE_FALL_S + 1) / C.STEP));
    const sec = G.state().sec, picks = G.pickDec(30);
    o.picks = [...new Set(picks)].sort().join(' ');
    o.goneOk = picks.every((k) => k !== 'silence' && k !== 'heights' && (!k.startsWith('nodash') || sec[k.split(':')[1]] === 0)) && picks.some((k) => k.startsWith('nodash')) && picks.every((k) => k !== '-');
    G.setSeed(12345); G.reset(); return o;
  });
  check('75 decree bags: full cycles without repeats, seeded, gone places skipped (no bridge, heights or fallen zone after their collapse)', dbg.cycles && dbg.same && dbg.differs && dbg.goneOk, JSON.stringify(dbg));
  // 76 The five decrees each do what their rule line says, only while in force: altars dry (heal in the warning, none in force, empty look, back after);
  // ultimates 2x (charge gains doubled for player and bot, capped at full; batch 15); silence (no new cast on a bridge with the note, status and button look; a cast released before still lands;
  // a bot on a bridge only attacks); heights (no break in the warning, break with slow + mark, again every 2 s, none on low ground; slope top counts, its foot does not;
  // a bot on the terrace at the warning leaves in time); no dash (zone tinted gold and outlined on the minimap, named in her line; a dash in the zone breaks it, outside not).
  const dfx = await g(() => {
    const G = __game, C = G.config, D = C.DECREES, H = window.__d, o = {};
    H.start(); const a = G.altars()[2]; G.teleport(a.x + 1.2, a.z); G.setHp(50);
    G.forceDecree('dry', null, 4); H.hold(0.5, H.park); o.warnHeal = G.state().hp > 50;
    G.teleport(0, -14); H.hold(4.6, H.park); G.teleport(a.x + 1.2, a.z); G.setHp(50); H.hold(2, H.park);
    o.dryHeal = +(G.state().hp - 50).toFixed(3); o.dryLook = G.altars().every((x) => !x.on); o.hud = G.decree().hud; o.hudShown = G.decree().hudShown;
    H.hold(2.2, H.park); o.endSt = G.decree().st; G.setHp(50); H.hold(1, H.park); o.afterHeal = G.state().hp > 50; o.afterLook = G.altars()[2].on; o.hudGone = G.decree().hudShown;
    // Game changed on purpose (batch 15): "Ultimates 2x" doubles every charge gain (was: the R cooldown ticks 2x). Player and bot start empty and gain only passive charge here
    // (nobody fights), so the gain per second over the passive rate is 1 in the warning and 2 in force; a meter near full is capped at full under the decree.
    H.start(); G.teleport(0, -14); G.setCharge(-1, 0); G.setCharge(0, 0); const p0 = G.chargeOf(-1);
    G.forceDecree('ult2x', null, 10); const b0 = G.chargeOf(0); H.hold(5, H.park); const p1 = G.chargeOf(-1), b1 = G.chargeOf(0); H.hold(5, H.park); const p2 = G.chargeOf(-1), b2 = G.chargeOf(0);
    const pr = C.ULT.passive * 5; o.ultWarn = +((p1 - p0) / pr).toFixed(2); o.ultOn = +((p2 - p1) / pr).toFixed(2); o.botWarn = +((b1 - b0) / pr).toFixed(2); o.botOn = +((b2 - b1) / pr).toFixed(2);
    G.setCharge(0, C.ULT.full - 0.2); H.hold(1, H.park); o.botCap = G.chargeOf(0) - C.ULT.full;
    H.start(); G.forceDecree('silence', null, 30); G.teleport(0, -24); H.hold(5.1, H.park);
    const nearB = () => G.placeBot(0, -18, 6); G.setBotHp(0, 1000); G.teleport(-15, 6); H.hold(0.1, nearB);
    // Batch 15: R needs a full charge meter (game changed on purpose).
    G.setCharge(-1, C.ULT.full); o.castOff = G.cast(2, -18, 6); G.teleport(-24, 6); H.hold(1.2, nearB); o.released = 1000 - G.bots().list[0].hp; G.setBotHp(0, 1e9); G.teleport(-30, 6); G.step(1); o.castOn = G.cast(0, -30, -2);
    const dc = G.decree(); o.silNote = dc.voice; o.silStatus = dc.status; o.silBar = dc.barSilenced;
    const atB = () => G.placeBot(0, -28.5, 6); G.hitBy(-1, 0, 1); const hp0 = G.state().hp; H.hold(2, atB);
    o.botCdOn = G.bots().list[0].cd.join(); o.botHit = hp0 - G.state().hp; o.botTgt = G.bots().list[0].tgt;
    G.teleport(14, -14); const offB = () => G.placeBot(0, 17, -14); G.hitBy(-1, 0, 1); H.hold(2, offB); o.botCdOff = G.bots().list[0].cd.some((v) => v > 0); o.barOff = G.decree().barSilenced;
    H.start(); G.teleport(-55, -15); G.placeBot(0, -42, -18); G.forceDecree('heights', null, 10); H.hold(4.9);
    let s = G.suits(); o.warnBrk = s[0].breaks; o.botWarnHi = s[1].hi; H.hold(0.25);
    s = G.suits(); o.brk1 = s[0].breaks; o.mark = +s[0].markT.toFixed(2); o.marker = s[0].marker; o.slow = [+s[0].slowT.toFixed(2), s[0].slowK]; o.markVoice = G.decree().voice;
    o.botHi = s[1].hi; o.botBrk = s[1].breaks;
    H.hold(1); o.brk1b = G.suits()[0].breaks; H.hold(1.1); o.brk2 = G.suits()[0].breaks;
    G.teleport(0, 0); H.hold(3); o.brkLow = G.suits()[0].breaks;
    G.teleport(-37.5, -18); G.step(1); o.slopeTop = G.suits()[0].hi; G.teleport(-25.5, -18); G.step(1); o.slopeFoot = G.suits()[0].hi;
    H.start(); G.teleport(5, 0); G.forceDecree('nodash', 'C2', 20); const z = G.floors().find((f) => f.sec === 'C2');
    o.tint = G.zoneTinted('C2'); o.zone = G.decree().zoneSec; o.zoneVoice = G.decree().voice; o.miniGold = G.miniPixel(z.x0 + 0.8, (z.z0 + z.z1) / 2);
    H.hold(5.1, H.park); G.cast(1, 5, 10); H.hold(0.4, H.park); o.dashBrk = G.suits()[0].breaks; o.dashMark = G.suits()[0].markT > 0;
    H.hold(8.1, H.park); G.teleport(14, -20); G.step(1); G.cast(1, 14, -10); H.hold(0.4, H.park); o.dashOut = G.suits()[0].breaks;
    o.zoneHud = G.decree().hud; H.hold(12, H.park); o.tintEnd = G.zoneTinted('C2'); o.zoneEnd = G.decree().zoneSec;
    G.setBots(0); G.reset(); return o;
  });
  const gold = (p) => p[0] > 200 && p[1] > 150 && p[2] < 120;
  check('76 decrees: dry, ultimates 2x, bridge silence, heights, no dash each do what their line says and only while in force',
    dfx.warnHeal && dfx.dryHeal === 0 && dfx.dryLook && /altars do not heal \(\d+ s\)/.test(dfx.hud) && dfx.hudShown === 'block' && dfx.endSt === 0 && dfx.afterHeal && dfx.afterLook && dfx.hudGone === 'none'
    && Math.abs(dfx.ultWarn - 1) < 0.05 && Math.abs(dfx.ultOn - 2) < 0.05 && Math.abs(dfx.botWarn - 1) < 0.05 && Math.abs(dfx.botOn - 2) < 0.05 && dfx.botCap === 0
    && dfx.castOff && dfx.released === 60 && dfx.castOn === false && /stilled/.test(dfx.silNote) && /Silenced/.test(dfx.silStatus) && dfx.silBar
    && dfx.botCdOn === '0,0,0' && dfx.botHit > 0 && dfx.botTgt === 0 && dfx.botCdOff && !dfx.barOff
    && dfx.warnBrk === 0 && dfx.brk1 === 1 && dfx.mark > 4.5 && dfx.marker && dfx.slow[0] > 1.5 && dfx.slow[1] === 0.3 && dfx.markVoice === 'Thou art marked.' && !dfx.botHi && dfx.botBrk === 0
    && dfx.brk1b === 1 && dfx.brk2 === 2 && dfx.brkLow === 2 && dfx.slopeTop && !dfx.slopeFoot
    && dfx.tint && dfx.zone === 'C2' && /Centre courtyard, south/.test(dfx.zoneVoice) && gold(dfx.miniGold) && dfx.dashBrk === 1 && dfx.dashMark && dfx.dashOut === 1
    && /no dashing in Centre courtyard, south/.test(dfx.zoneHud) && !dfx.tintEnd && dfx.zoneEnd === null, JSON.stringify(dfx));
  // 77 Penalty and mark: slowed 30% for 2 s and marked 5 s; a far bot sees the marked player; the player sees a far marked bot (body and minimap);
  // the marker hides when the mark ends; while the player is marked up to DECREES.markCap bots target it (and that many do), back to 1 the tick it ends.
  const mkp = await g(() => {
    const G = __game, C = G.config, D = C.DECREES, H = window.__d, o = { capMax: 0, afterBad: 0 };
    H.start(); G.teleport(0, 0); G.step(1); o.seesBefore = G.sees(0, -1); G.breakBy(-1);
    let s = G.suits()[0]; o.slow = [s.slowT, s.slowK]; o.mark = s.markT; o.marker = s.marker; o.seesAfter = G.sees(0, -1); o.cap = G.hunters().max;
    const x0 = G.state().x; G.setMove(1, 0); G.step(30); G.clearMove(); o.dx = +(G.state().x - x0).toFixed(3); o.want = +(C.PLAYER_SPEED * (1 - D.slow) * 0.5).toFixed(3);
    G.placeBot(0, 0, -50); G.breakBy(0); G.step(1); const b = G.bots().list[0]; o.botSeen = b.seen; o.botVis = b.vis; const mp = G.miniPixel(b.x, b.z); o.botMini = mp[0] > 200 && mp[1] < 150;
    H.hold(5.1, H.park); s = G.suits()[0]; o.markEnd = s.markT; o.markerEnd = s.marker; o.seesEnd = G.sees(0, -1); o.capEnd = G.hunters().max; o.botSeenEnd = G.bots().list[0].seen;
    H.start(3); G.setTime(C.BOT.engage.peaceS + C.BOT.engage.rampS + 1); G.teleport(0, -45);
    const near = () => { G.placeBot(0, 2, -45); G.placeBot(1, -2, -45); G.placeBot(2, 0, -43); };
    G.breakBy(-1); for (let n = 0; n < 240; n++) { near(); G.step(1); const h = G.hunters(); if (h.capOnP > o.capMax) o.capMax = h.capOnP; }
    for (let n = 0; n < 150; n++) { near(); G.step(1); const h = G.hunters(); if (!h.markP && h.capOnP > 1) o.afterBad++; }
    G.setBots(0); G.reset(); return o;
  });
  check('77 penalty and mark: 30% slow 2 s, mark 5 s seen by every bot and by the player, marker hides at the end, cap 2 while the player is marked and 1 after',
    mkp.slow[0] === 2 && mkp.slow[1] === 0.3 && mkp.mark === 5 && mkp.marker && !mkp.seesBefore && mkp.seesAfter && mkp.cap === 2 && Math.abs(mkp.dx - mkp.want) < 0.05
    && mkp.botSeen && mkp.botVis && mkp.botMini && mkp.markEnd === 0 && !mkp.markerEnd && !mkp.seesEnd && mkp.capEnd === 1 && !mkp.botSeenEnd && mkp.capMax === 2 && mkp.afterBad === 0, JSON.stringify(mkp));
  // 78 Decrees in whole matches (the 12 matches of 65): every warning >= DECREE.warnS before its start, none begun under a collapse banner, never two at once
  // (bagged and bounty), HUD written only on change; bots stay off Our heights while it holds unless crossing them to leave a warned section (<= 1 s);
  // decrees happened in every match. Numbers per match are reported (-sims).
  check('78 decrees in 12 matches: told >= 5 s, not under a collapse banner, never two at once, HUD only on change, bots off the heights, decrees every match',
    ms.dec.dv.length === 0 && ms.dec.hiStay <= 1 && ms.dec.dsum.every((x) => x.n >= 1), JSON.stringify(ms.dec));
  // 83 Decree pacing (batch 13a, panel 23 Nov 16:11; GDD about one a minute, 3-4 per royale): over the 12 matches of 65 every match has 3 or 4 decrees told
  // (warnings begun, the bounty included) before it is decided; no banner over a decree warning; no heights break within warnFreeS of a warned section.
  // "About one a minute": the mean time from one warning to the next over all 12 matches is at most 60 s.
  const wGaps = ms.dec.dsum.flatMap((x) => x.w.slice(1).map((v, i) => v - x.w[i])), wMean = wGaps.reduce((a, v) => a + v, 0) / Math.max(1, wGaps.length);
  check('83 decree pacing: 3-4 decrees told (bounty included) in each of 12 matches, about one a minute (mean warning to warning <= 60 s), no banner over a decree warning, no heights break near a warned section',
    ms.dec.dsum.every((x) => x.told >= 3 && x.told <= 4) && wMean <= 60 && ms.dec.bannerOv === 0 && ms.dec.hiNear === 0,
    `told ${ms.dec.dsum.map((x) => x.seed + ':' + x.told).join(',')}; mean warning to warning ${wMean.toFixed(1)} s (${wGaps.length} gaps); bannerOv ${ms.dec.bannerOv}; heights breaks ${ms.dec.hiBrk}, near warned ${ms.dec.hiNear}`);
  // 85 Kennel autopilot (batch 13b P5, panel 23 Nov 16:11; test proxy, own commit): the autopilot stands in for a player who reads the kennel banner
  // (when not fighting, fleeing or healing it walks to the nearest announced camp and fights the cub there). The whole-match gates above keep the old autopilot;
  // these 12 matches report the GDD plate rate (>= 1 plate in 70% of runs) beside it. Gate: the proxy reaches an announced camp (within 8 m) in at least
  // half of the warnings it is alive and free for, and takes a plate in more matches than the old autopilot (it goes there to fight the cub).
  const kp = await g(() => {
    const G = __game, C = G.config, Kc = C.KENNEL, out = []; let warns = 0, reached = 0;
    for (const seed of [12345, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]) {
      G.setSeed(seed); G.setBots(G.config.BOTS.count); G.reset(); G.autoPlayer(true, true); G.setWatch(true);
      let prevW = false, open = null; const leadS = {};
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const c = G.cubs(), p = G.player(), now = G.royale().t, l = G.leader();
        if (l.id >= 0) leadS[l.id] = (leadS[l.id] || 0) + 1;
        if (c.warned && !prevW) {
          const camps = Kc.waves[c.wave].map((w) => G.camps[w[1]]).filter((cp) => G.state().sec[cp[2]] === 0);
          open = !p.dead && camps.length && !['fight', 'flee', 'heal'].includes(p.mode) ? { camps, until: now + Kc.warnS + 5, best: 1e9 } : null;
          if (open) warns++;
        }
        prevW = c.warned;
        if (open) {
          const st = G.state(); for (const cp of open.camps) open.best = Math.min(open.best, Math.hypot(cp[0] - st.x, cp[1] + 3 - st.z));
          if (now >= open.until || p.dead) { if (open.best <= 8) reached++; open = null; }
        }
        if (G.royale().decidedAt >= 0) break;
      }
      const b = G.bots(), p = G.player(), top = Object.entries(leadS).sort((x, y) => y[1] - x[1])[0], win = b.list.concat([{ id: 0, dead: p.dead }]).find((q) => !q.dead);
      out.push({ seed, decided: +G.royale().decidedAt.toFixed(1), pPlates: p.plates, out: p.dead ? Math.round(p.diedAt) : 'won', topLeader: top ? +top[0] : -1, winId: win ? win.id : -1 });
      G.setWatch(false); G.autoPlayer(false);
    }
    G.setBots(0); G.reset(); return { out, warns, reached };
  });
  check('85 kennel autopilot (test proxy): reaches an announced camp in at least half of its free warnings and takes a plate in more of 12 matches than the old autopilot',
    kp.reached * 2 >= kp.warns && kp.warns > 0 && kp.out.filter((m) => m.pPlates > 0).length > ms.sims.filter((x) => x.pPlates > 0).length, JSON.stringify(kp));
  // 86 Kennel autopilot, fixed scene (batch 13b, closes the 'no cub fight' gap of 85): one bot kept in the core hall away from the statue, decrees off; the proxy walks from its spawn
  // to the first announced camp, fights the cub there (mode 'creature') and takes its plate before 75 s. The autopilot is switched on 1 s before the first warning.
  const kf = await g(() => {
    const G = __game, C = G.config, o = { modes: {} };
    C.DECREES.on = false;
    try {
      G.setSeed(12345); G.setBots(1); G.reset(); G.setWatch(true);
      for (let t = 0; t < 75 / C.STEP; t++) {
        if (t === Math.round((C.KENNEL.firstS - C.KENNEL.warnS - 1) / C.STEP)) G.autoPlayer(true, true);
        if (t % 30 === 0) G.placeBot(0, 0, -45);
        G.step(1); const m = G.player().mode; o.modes[m] = (o.modes[m] || 0) + 1;
        if (G.player().plates > 0) break;
      }
      const p = G.player(); o.plates = p.plates; o.dead = p.dead; o.t = +G.royale().t.toFixed(1);
    } finally { C.DECREES.on = true; G.setWatch(false); G.autoPlayer(false); G.setBots(0); G.reset(); }
    return o;
  });
  check('86 kennel autopilot fixed scene: walks to the announced camp, fights the cub there and takes its plate before 75 s',
    kf.plates >= 1 && !kf.dead && kf.modes.camp > 0 && kf.modes.creature > 0, JSON.stringify(kf));
  SIMS.push(`kennel autopilot (P5 proxy): player >=1 plate ${kp.out.filter((m) => m.pPlates > 0).length} of 12 (old autopilot ${ms.sims.filter((x) => x.pPlates > 0).length} of 12); reached camp ${kp.reached} of ${kp.warns} free warnings; leader win share ${kp.out.filter((m) => m.topLeader >= 0 && m.topLeader === m.winId).length} of 12; decided ${kp.out.map((m) => m.decided).join(',')}; player out ${kp.out.map((m) => m.out).join(',')}`);
  SIMS.push(`decrees per match ${ms.dec.dsum.map((x) => x.n).join(',')}; order ${ms.dec.dsum.map((x) => x.seed + ':' + x.keys).join(' | ')}; breaks player ${ms.dec.dsum.map((x) => x.brkP).join(',')} bots ${ms.dec.dsum.map((x) => x.brkB).join(',')}; player marked ticks ${ms.cap.markPTicks}, cap max ${ms.cap.capMark}; bots on heights max ${ms.dec.hiStay} s`);
  // 79 W dash: 4 m on open ground; stops at a bridge rail and at a core hall wall without falling; never off a sloped bridge; burst on landing (not before).
  const ds = await g(() => {
    const G = __game, H = window.__d, o = {};
    H.start(); G.teleport(14, -20); G.step(1); G.cast(1, 14, -10); H.hold(0.4, H.park); let s = G.state(); o.open = +Math.hypot(s.x - 14, s.z + 20).toFixed(3); o.openZone = s.zone;
    H.start(); G.teleport(-30, 7.5); G.step(1); G.cast(1, -30, 20); H.hold(1.2, H.park); s = G.state(); o.rail = { z: +s.z.toFixed(2), falling: s.falling, zone: s.zone, hp: s.hp };
    H.start(); G.teleport(-16.5, -55); G.step(1); G.cast(1, -30, -55); H.hold(1, H.park); s = G.state(); o.wall = { x: +s.x.toFixed(2), zone: s.zone, falling: s.falling };
    H.start(); G.teleport(-30, -18); G.step(1); G.cast(1, -30, -5); H.hold(1.2, H.park); s = G.state(); o.slope = { z: +s.z.toFixed(2), falling: s.falling, zone: s.zone };
    H.start(); G.teleport(0, -24); G.step(1); G.cast(1, 0, -18); const before = G.dummies()[1].hp; H.hold(0.4, H.park); o.burst = [before, G.dummies()[1].hp]; o.flag = G.config.SKILLS[1].dash === true;
    G.setBots(0); G.reset(); return o;
  });
  check('79 W dash: 4 m on open ground, stops at a rail and a wall without falling, never off a sloped bridge, burst lands on landing',
    Math.abs(ds.open - 4) < 0.05 && ds.openZone === 'C1' && ds.rail.z <= 9 && ds.rail.z > 7.5 && !ds.rail.falling && ds.rail.zone === 'WB2' && ds.wall.x > -20 && ds.wall.x < -16.5 && ds.wall.zone === 'CORE' && !ds.wall.falling
    && !ds.slope.falling && ds.slope.zone === 'WB1' && ds.burst[0] === 100 && ds.burst[1] === 80 && ds.flag, JSON.stringify(ds));
  // 80 The wake ends a decree and its tint, clears marks and the HUD line; none in the hunt; new run x3 resets the slot, the bags and the counts; text keys exist.
  const dw = await g(() => {
    const G = __game, C = G.config, H = window.__d, o = {};
    H.start(); G.forceDecree('nodash', 'C2', 30); H.hold(5.2, H.park); G.forceDecree('dry', null, 30); H.hold(5.2, H.park); o.dryOn = G.decree().key === 'dry' && !G.altars()[0].on;
    G.breakBy(-1); G.breakBy(0); G.startHunt(); let d = G.decree(); const n0 = d.n; o.wake = { st: d.st, zone: d.zoneSec, tint: G.zoneTinted('C2'), marks: G.suits().filter((s) => s.markT > 0 || s.marker).length, hud: d.hudShown, altars: G.altars().every((a) => a.on) };
    G.setHp(1e9); H.hold(60); d = G.decree(); o.hunt = { st: d.st, n: d.n - n0 };
    o.runs = [];
    for (let r = 0; r < 3; r++) { G.setSeed(40 + r); G.setBots(G.config.BOTS.count); G.reset(); d = G.decree(); o.runs.push({ st: d.st, n: d.n, next: d.next, brk: d.brkP + d.brkB, log: d.log.length, marks: G.suits().filter((s) => s.markT > 0).length, hud: d.hudShown }); }
    H.start(); G.forceDecree('nodash', 'W2', 10); o.voice = G.decree().voice; H.hold(5.2, H.park); o.hud = G.decree().hud;
    o.keys = G.decreeKeys(); G.setBots(0); G.reset(); return o;
  });
  check('80 wake ends the decree, tint, marks and HUD; none in the hunt; new run x3 resets slot, bags and counts; zone named; text keys',
    dw.dryOn && dw.wake.st === 0 && dw.wake.zone === null && !dw.wake.tint && dw.wake.marks === 0 && dw.wake.hud === 'none' && dw.wake.altars && dw.hunt.st === 0 && dw.hunt.n === 0
    && dw.runs.every((r) => r.st === 0 && r.n === 0 && C0.DECREES.first.includes(r.next) && r.brk === 0 && r.log === 0 && r.marks === 0 && r.hud === 'none')
    && /West courtyard, south/.test(dw.voice) && /West courtyard, south/.test(dw.hud) && dw.keys.length === 0, JSON.stringify(dw));
  // 81 Budget with every mark and the crown: heaviest royale (every suit; batch 14: 9 on purpose, 7 cubs, tells) with every suit's marker shown and in the scene graph (batch 14: visible alone was not enough), the crown and the gold zone tint; no shader compile, geometry flat.
  const bk = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9); G.plateTo(4, 'stalker'); G.forceDecree('nodash', 'W1', 60);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      for (let n = 0; n < 600; n++) {
        for (let i = 0; i < G.config.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5);
        for (let i = -1; i < G.config.BOTS.count; i++) if (G.suits()[i + 1].markT < 0.5) G.breakBy(i);
        G.step(1); const c = G.cubs(), l = G.leader(), marks = G.suits().filter((s) => s.marker && s.markerIn).length;
        if (l.crownShown && marks === G.config.BOTS.count + 1 && G.zoneTinted('W1') && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, marks, crown: l.crownShown, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setBots(0); G.reset(); }
    return best;
  });
  check(`81 budget with ${NS} marks, the crown and the zone tint: ${NS} suits + cubs + tells (calls<500, tris<500k), no shader compile, geometry flat`,
    !!bk && bk.marks === NS && bk.crown && bk.tells >= 3 && bk.calls < 500 && bk.tris < 500000 && bk.programs === base.programs && bk.geoms === base.geoms, JSON.stringify(bk));
  // 82 Replays (batch 12 fix): a seed played twice in a row in the same page gives the same match (decided time, player out, decree log, breaks).
  // Found in batch 12: an ending heights decree bumped warnGen after the restart and the autopilot kept brain fields, so run 1 and run 2 of one seed differed.
  const rp = await g(() => {
    const G = __game, C = G.config, out = [];
    for (let r = 0; r < 2; r++) {
      G.setSeed(7); G.setBots(G.config.BOTS.count); G.reset(); G.autoPlayer(true); G.setWatch(true); out.push(G.startState());
      for (let t = 0; t < 300 / C.STEP; t++) { G.step(1); if (G.royale().decidedAt >= 0) break; }
      const p = G.player(), d = G.decree(); out.push(JSON.stringify([+G.royale().decidedAt.toFixed(2), p.dead ? +p.diedAt.toFixed(2) : -1, d.log.map((v) => +v.toFixed(2)), d.brkP, d.brkB]));
      G.setWatch(false); G.autoPlayer(false);
    }
    G.setBots(0); G.reset(); return out;
  });
  check('82 replay: a run starts from the same state and one seed played twice in a row gives the same match', rp[0] === rp[2] && rp[1] === rp[3], rp.join(' vs '));
  // 87 Charge sources (batch 15 ticket 02; plate 48, crab 54, bot plate 60, bounty 71 and the 2x decree 76 are checked there): passive per second while alive,
  // per health dealt to a suit and per health taken (any cause, capped at the health actually lost), kill bonus, for the player and a bot; all amounts from CONFIG.ULT.
  // Hits are read in the same step (no passive in between); the passive is read over whole seconds of game time; a broken suit gains nothing.
  const cs = await g(() => {
    const G = __game, C = G.config, U = C.ULT, H = window.__d, o = {}, near = (a, b) => Math.abs(a - b) < 1e-6;
    H.start(2); G.teleport(0, -40); G.placeBot(1, 6, -50);
    const zero = () => { G.setCharge(-1, 0); G.setCharge(0, 0); G.setCharge(1, 0); };
    zero(); H.hold(4, () => { H.park(); G.placeBot(1, 6, -50); });
    o.passive = [G.chargeOf(-1), G.chargeOf(0), G.chargeOf(1)]; o.wantPassive = 4 * U.passive;
    zero(); G.hitBy(-1, 0, 10); o.pDealt = G.chargeOf(-1); o.bTaken = G.chargeOf(0);
    zero(); G.hitBy(0, -1, 8); o.bDealt = G.chargeOf(0); o.pTaken = G.chargeOf(-1);
    zero(); G.damage(6); o.pTakenNoHitter = G.chargeOf(-1);
    zero(); G.setBotHp(1, 5); G.hitBy(0, 1, 10); o.bKill = G.chargeOf(0); o.bKillWant = 5 * U.dealt + U.kill; o.victimDead = G.bots().list[1].dead;
    const victim = G.chargeOf(1); H.hold(2, H.park); o.deadGain = G.chargeOf(1) - victim;
    zero(); G.setBotHp(0, 4); G.hitBy(-1, 0, 10); o.pKill = G.chargeOf(-1); o.pKillWant = 4 * U.dealt + U.kill;
    o.ok = o.passive.every((v) => near(v, o.wantPassive)) && near(o.pDealt, 10 * U.dealt) && near(o.bTaken, 10 * U.taken) && near(o.bDealt, 8 * U.dealt) && near(o.pTaken, 8 * U.taken)
      && near(o.pTakenNoHitter, 6 * U.taken) && near(o.bKill, o.bKillWant) && o.victimDead && o.deadGain === 0 && near(o.pKill, o.pKillWant);
    G.setBots(0); G.reset(); return o;
  });
  check('87 charge sources: passive per second, per health dealt and taken (capped at health lost), kill bonus, player and bot, nothing while broken (CONFIG.ULT)', cs.ok, JSON.stringify(cs));
  // 88 Charge wording (batch 15): every player-facing line about the ultimate's gains says charge, never cooldown.
  const cw = await g(() => ['boon_ult', 'rule_plate_s', 'rule_plate_h', 'rule_dec_ult2x', 'hud_dec_ult2x'].map((k) => [k, __game.text[k] || '']));
  check('88 charge wording: boon, plate and 2x decree lines say charge, not cooldown', cw.every(([, t]) => /charge/i.test(t) && !/cooldown/i.test(t)), JSON.stringify(cw));
  // 89 Meter gate (batch 15 ticket 03): in the royale R casts only with a full meter, for the player and a bot; the cast empties the meter and starts no cooldown.
  // Bot: bot 0 answers bot 1 (hit back) at 40 health (under BOT.ultBelowHp, so it wants R); its charge is held at half for 4 s of fighting (Q or W cast), then filled.
  // Read in the step the bot casts: at most one basic attack may land in that same step after the cast (CONFIG.ATTACK.dmg x ULT.dealt).
  const mg = await g(() => {
    const G = __game, C = G.config, U = C.ULT, H = window.__d, o = {};
    H.start(2); G.teleport(14, -20); G.step(1);
    G.setCharge(-1, U.full - 0.1); o.pUnder = G.cast(2, 14, -14); o.pUnderCh = G.chargeOf(-1); o.pUnderN = G.charge().ultN;
    G.setCharge(-1, U.full); o.pFull = G.cast(2, 14, -14); o.pAfterCh = G.chargeOf(-1); o.pCd = G.skills()[2]; o.pN = G.charge().ultN; o.pAgain = G.cast(2, 14, -14);
    const near = () => { G.placeBot(0, 0, -50); G.placeBot(1, 3, -50); G.setBotHp(0, 40); };
    near(); G.hitBy(1, 0, 1); let fought = false;
    H.hold(4, () => { near(); G.setCharge(0, U.full / 2); const b = G.bots().list[0]; if (b.cd[0] > 0 || b.cd[1] > 0) fought = true; });
    let b = G.bots().list[0], ch = G.charge().bots[0]; o.bFought = fought; o.bUnderN = ch.ultN; o.bUnderCd = b.cd[2]; o.bTgt = b.tgt;
    G.setCharge(0, U.full); let castCh = -1;
    for (let n = 0; n < 180 && castCh < 0; n++) { near(); G.step(1); ch = G.charge().bots[0]; if (ch.ultN > 0) castCh = ch.ch; }
    b = G.bots().list[0]; o.bN = ch.ultN; o.bCastCh = castCh; o.bCd = b.cd[2];
    o.ok = o.pUnder === false && o.pUnderCh === U.full - 0.1 && o.pUnderN === 0 && o.pFull === true && o.pAfterCh === 0 && o.pCd === 0 && o.pN === 1 && o.pAgain === false
      && o.bFought && o.bTgt === 2 && o.bUnderN === 0 && o.bUnderCd === 0 && o.bN === 1 && o.bCastCh >= 0 && o.bCastCh <= C.ATTACK.dmg * U.dealt + 1e-9 && o.bCd === 0;
    G.setBots(0); G.reset(); return o;
  });
  check('89 meter gate: no R under a full meter (player and bot); the cast empties it and starts no cooldown in the royale', mg.ok, JSON.stringify(mg));
  // 90 Wake and hunt (batch 15): the wake fills the player's meter; in the hunt R runs on its cooldown (SKILLS[2].cd) and the meter neither gates it nor gains.
  const wh = await g(() => {
    const G = __game, C = G.config, U = C.ULT, H = window.__h, o = {};
    G.reset(); G.setCharge(-1, 10); G.startHunt(); o.wake = G.charge(); H.start(); for (let i = 0; i < 3; i++) H.mute(i); G.setHp(1e9);
    G.setCharge(-1, 10); o.hunt = G.charge(); o.cast1 = G.cast(2, 0, -60); o.cd1 = G.skills()[2]; o.ch1 = G.chargeOf(-1); o.cast2 = G.cast(2, 0, -60);
    G.step(Math.round((C.SKILLS[2].cd - 0.5) / C.STEP)); o.early = G.cast(2, 0, -60); G.step(Math.round(0.6 / C.STEP)); o.text = G.charge().text;
    o.ready = G.cast(2, 0, -60); o.ch2 = G.chargeOf(-1);
    o.ok = o.wake.p === U.full && !o.wake.meter && !o.hunt.meter && o.hunt.ready && o.cast1 === true && Math.abs(o.cd1 - C.SKILLS[2].cd) < 1e-9 && o.ch1 === 10 && o.cast2 === false
      && o.early === false && o.ready === true && o.ch2 === 10 && o.hunt.ringShown === 'none';
    G.reset(); return o;
  });
  check('90 wake and hunt: the wake fills the meter; in the hunt R keeps its 30 s cooldown, the meter does not gate or gain, ring hidden', wh.ok, JSON.stringify(wh));
  // 91 New run x3 in one page (batch 15): every suit's meter and ultimate count go back to CONFIG.ULT.start, after a royale with charge and after a hunt.
  const nr = await g(() => {
    const G = __game, C = G.config, U = C.ULT, out = [];
    G.setBots(C.BOTS.count);
    for (let r = 0; r < 3; r++) {
      G.setSeed(60 + r); G.reset(); G.step(Math.round(20 / C.STEP));
      for (let i = -1; i < C.BOTS.count; i++) G.setCharge(i, 77);
      if (r === 2) G.startHunt();
      G.reset(); G.step(1); const c = G.charge();
      out.push({ p: c.p, n: c.ultN, bots: c.bots.map((b) => b.ch), bn: c.bots.map((b) => b.ultN), text: c.text, ok: c.ultN === 0 && c.bots.length === C.BOTS.count
        && c.p < U.start + 1 && c.bots.every((b) => b.ch < U.start + 1 && b.ultN === 0) && c.text === String(Math.floor(c.p)) });
    }
    G.setBots(0); G.reset(); return out;
  });
  check('91 new run x3: every suit\'s meter and ultimate count reset (after a charged royale and after a hunt)', nr.every((x) => x.ok), JSON.stringify(nr));
  // 92 HUD charge (batch 15): the R text and ring are written only when the shown whole number changes (none while the meter stays full; one per whole number of passive gain),
  // the text and ring match the meter; budget, shader programs and geometry stay flat with the ring shown.
  const hw = await g(() => {
    const G = __game, C = G.config, U = C.ULT, H = window.__d, o = {};
    H.start(1); G.setCharge(-1, U.full); G.step(1); const w0 = G.charge().writes;
    H.hold(2, () => { H.park(); G.setCharge(-1, U.full); }); o.fullWrites = G.charge().writes - w0; o.fullText = G.charge().text; o.fullCover = G.charge().cover;
    G.setCharge(-1, 10.2); let last = -1, changes = 0; const w1 = G.charge().writes;
    for (let n = 0; n < Math.round(4 / C.STEP); n++) { H.park(); G.step(1); const f = Math.floor(G.chargeOf(-1)); if (f !== last) { changes++; last = f; } }
    const c = G.charge(); o.writes = c.writes - w1; o.changes = changes; o.text = c.text; o.ring = c.ring; o.ringShown = c.ringShown; o.p = c.p;
    const r = G.render(true); o.calls = r.calls; o.programs = r.programs; o.geoms = r.geoms;
    o.ok = o.fullWrites === 0 && o.fullText === '' && o.fullCover === 'none' && o.writes === o.changes && o.changes >= 2 && o.text === String(Math.floor(o.p))
      && o.ring.includes(Math.floor(o.p) + '%') && o.ringShown === 'block';
    G.setBots(0); G.reset(); return o;
  });
  check('92 HUD charge: written only on change (0 writes while full, one per whole number gained), text and ring match the meter; budget, programs and geometry flat',
    hw.ok && hw.calls < 500 && hw.programs === base.programs && hw.geoms === base.geoms, JSON.stringify(hw));
  // ===== Batch 16 ticket 01: kit framework, suit stats, school select, unseen state =====
  // 93 Suit stats (docs/STATS-MATH.md, owner 23 Nov 23:3x): blows from suits and creatures (hit, bleed) pass the armor, taken = raw x (K + Mid) / (K + armor);
  // statue, lions, drops and test damage stay fixed; a Mid suit takes every number unchanged (factor exactly 1); speed tiers move a suit at their m/s.
  const st93 = await g(() => {
    const G = __game, C = G.config, S = C.STATS, H = window.__d, o = {}, f = (a) => (S.K + S.armor[S.yard]) / (S.K + S.armor[a]);
    // Game changed on purpose (batch 16): a built kit plays its own tiers (法甲 from ticket 02), an unbuilt one the placeholder at Mid; every suit is checked against its kit.
    // Batch 16 ticket 03 (game changed on purpose): the checks' placeholder player (pkit, default pick 儒甲) plays the placeholder at Mid, so it is checked against the kit it plays.
    const kitTiers = (q) => { const k = C.KITS[q.school], t = k && k.built && q.kit !== 'placeholder' ? k : { armor: S.yard, speed: S.yard }; return (q.kit === 'placeholder' || (k && k.built)) && q.armor === S.armor[t.armor] && q.spd === S.speed[t.speed] && Math.abs(q.armorK - f(t.armor)) < 1e-12; };
    H.start(3); const s0 = G.schools().suits; o.mid = s0.every(kitTiers) && s0.some((q) => q.armorK === 1 && q.spd === C.PLAYER_SPEED && q.armor === S.armor.Mid);
    // Batch 16 ticket 04 (game changed on purpose): bot 2 plays 墨甲 (High) now, so the Mid control is set to Mid explicitly.
    G.setStats(0, 'Low', 'Mid'); G.setStats(1, 'High', 'Mid'); G.setStats(2, 'Mid', 'Mid'); G.setBotHp(0, 100); G.setBotHp(1, 100); G.setBotHp(2, 100);
    G.hitBy(-1, 0, 25); G.hitBy(-1, 1, 25); G.hitBy(-1, 2, 25); const b = G.bots().list;
    o.low = +(100 - b[0].hp).toFixed(4); o.high = +(100 - b[1].hp).toFixed(4); o.midHit = 100 - b[2].hp; o.wantLow = +(25 * f('Low')).toFixed(4); o.wantHigh = +(25 * f('High')).toFixed(4);
    G.setBotHp(0, 100); G.hitBot(0, 10); o.testFixed = 100 - G.bots().list[0].hp;
    H.start(1); G.setStats(0, 'High', 'Mid'); G.setBotHp(0, 100); G.bleed(0, 2); H.hold(1, H.park); o.bleed = +(100 - G.bots().list[0].hp).toFixed(3); o.wantBleed = +(C.BLEED.dps * 2 * f('High')).toFixed(3);
    H.start(1); G.setHp(100); G.setStats(-1, 'Low', 'Mid'); const l = G.hazards()[1]; G.teleport(l.x + 2.5, l.z); G.step(1); G.step(Math.round((C.LION.windup + 0.05) / C.STEP));
    o.lion = 100 - G.state().hp;
    H.start(1); G.setHp(100); G.setStats(-1, 'High', 'Mid'); G.teleport(-33 * G.K, -3 * G.K); G.setMove(0, 1); G.step(90); G.clearMove(); G.step(30); o.drop = 100 - G.state().hp;
    const run = (tier) => { H.start(1); G.setStats(-1, 'Mid', tier); G.teleport(14, -20); G.step(1); const x0 = G.state().x; G.setMove(1, 0); G.step(30); G.clearMove(); return +(G.state().x - x0).toFixed(3); };
    o.vLow = run('Low'); o.vMid = run('Mid'); o.vHigh = run('High'); o.want = [S.speed.Low * 0.5, S.speed.Mid * 0.5, S.speed.High * 0.5];
    G.reset(); o.back = G.schools().suits.every(kitTiers);
    o.ok = o.mid && Math.abs(o.low - o.wantLow) < 1e-3 && Math.abs(o.high - o.wantHigh) < 1e-3 && o.midHit === 25 && o.wantLow > 25 && o.wantHigh < 25 && o.testFixed === 10
      && Math.abs(o.bleed - o.wantBleed) < 0.05 && o.lion === C.LION.dmg && o.drop === C.DROP_DAMAGE
      && Math.abs(o.vLow - o.want[0]) < 0.01 && Math.abs(o.vMid - o.want[1]) < 0.01 && Math.abs(o.vHigh - o.want[2]) < 0.01 && o.back;
    G.setBots(0); G.reset(); return o;
  });
  check('93 suit stats: armor on hits and bleed (Low takes more, High less, Mid unchanged), statue/lion, drop and test damage fixed, speed tiers in m/s, a new run back to its kit',
    st93.ok, JSON.stringify(st93));
  // 94 School select (owner 23 Nov 23:3x): nine school buttons plus a random one, every one at least 44 px; while it is open nothing steps;
  // keys 1-9 pick, 0 lets Heaven choose, Enter takes the last pick (outlined); the pick is remembered in storage; the player takes it and the bots the other eight
  // in CONFIG.SCHOOLS order with their names and colours; HUD names the player's school; New run opens the select; game keys do nothing while it is open.
  const sel = await g(async () => {
    const G = __game, C = G.config, o = {}, frames = (n) => new Promise((r) => { let k = 0; const f = () => (++k >= n ? r() : requestAnimationFrame(f)); requestAnimationFrame(f); });
    G.setSeed(12345); G.setBots(8); G.reset(); G.setSelectOn(true); G.openSelect();
    let sc = G.schools(); o.open = sc.selecting && sc.shown === 'block'; o.n = sc.buttons.length; o.small = sc.buttons.filter((b) => b.w < 44 || b.h < 44).length; o.last0 = sc.buttons[0].last;
    const t0 = G.state().t; await frames(20); o.frozen = G.state().t === t0;
    dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyN' })); dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyQ' })); o.keysIgnored = G.schools().selecting && G.skills()[0] === 0;
    G.selectKey('Digit3'); sc = G.schools(); const L = C.SCHOOLS;
    o.pick = sc.pick; o.closed = !sc.selecting && sc.shown === 'none'; o.hud = sc.hud; o.player = sc.suits[0].school; o.bots = sc.suits.slice(1).map((q) => q.school).join(',');
    o.wantBots = L.filter((x, i) => i !== 2).join(','); o.names = sc.suits.slice(1).map((q) => q.name).join(','); o.colors = sc.suits.slice(1).every((q) => q.color === C.COL.schools[L.indexOf(q.school)]);
    let stored = null; try { stored = localStorage.getItem(C.SELECT.saveKey); } catch (e) { stored = 'blocked'; } o.stored = stored;
    o.runFresh = G.state().t === 0 && G.royale().phase === 'royale' && G.bots().list.every((q) => !q.dead);
    G.newRun(); o.newRunOpens = G.schools().selecting; o.lastNow = G.schools().buttons[2].last;
    G.selectKey('Enter'); o.enter = G.schools().pick === 2 && !G.schools().selecting;
    G.openSelect(); G.selectKey('Digit0'); sc = G.schools(); o.random = sc.pick >= 0 && sc.pick < 9 && !sc.selecting && sc.suits[0].school === L[sc.pick];
    G.pickSchool(0); o.back = G.schools().suits.slice(1).map((q) => q.name).join(','); try { localStorage.removeItem(C.SELECT.saveKey); } catch (e) { o.cleanFail = true; }
    G.setSelectOn(false); G.setBots(0); G.reset(); return o;
  });
  check('94 school select: 9 schools + random (44 px), frozen while open, keys 1-9 / 0 / Enter, pick stored, bots take the other eight with names and colours, HUD line, New run opens it',
    sel.open && sel.n === 10 && sel.small === 0 && sel.last0 && sel.frozen && sel.keysIgnored && sel.pick === 2 && sel.closed && sel.hud === 'Your school: Fa suit' && sel.player === 'fa'
    && sel.bots === sel.wantBots && sel.names === 'Ru suit,Dao suit,Mo suit,Yinyang suit,Za suit,Ming suit,Zongheng suit,Nong suit' && sel.colors && sel.stored === '2' && sel.runFresh
    && sel.newRunOpens && sel.lastNow && sel.enter && sel.random && sel.back === 'Dao suit,Fa suit,Mo suit,Yinyang suit,Za suit,Ming suit,Zongheng suit,Nong suit', JSON.stringify(sel));
  // 95 Unseen state (minimal, batch 16): an unseen suit is not seen by the player (not drawn, so no auto-target) or by bots beyond UNSEEN.shimmerM, is seen
  // as a shimmer within it, is seen while marked; being hit, attacking (a cast that hits nothing) and its timer end it; a new run clears it; programs and geometry flat with the shimmer drawn.
  const us = await g(() => {
    const G = __game, C = G.config, H = window.__d, o = {}, put = () => { G.placeBot(0, 0, -50); G.placeBot(1, 6, -50); };
    H.start(2); G.teleport(0, -44); put(); G.step(1); o.before = { seen: G.bots().list[0].seen, sees: G.sees(1, 0) };
    o.on = G.unseen(0, 2); put(); G.step(1); let b = G.bots().list[0]; o.far = { seen: b.seen, vis: b.vis, sees: G.sees(1, 0) };
    G.teleport(0, -48); put(); G.step(1); b = G.bots().list[0]; o.near = { seen: b.seen, vis: b.vis }; const r = G.render(true); o.programs = r.programs; o.geoms = r.geoms;
    G.teleport(0, -44); G.hitBy(1, 0, 1); put(); G.step(1); o.hit = { t: G.unseenOf(0).t, seen: G.bots().list[0].seen, shimmer: G.unseenOf(0).shimmer };
    H.start(2); G.teleport(0, -44); put(); G.unseen(0, 1); H.hold(0.5, put); o.mid = G.bots().list[0].seen; H.hold(0.6, put); o.timer = { t: G.unseenOf(0).t, seen: G.bots().list[0].seen };
    G.unseen(-1, 2); put(); G.step(1); o.pHidden = !G.sees(0, -1); G.cast(0, 0, -36); G.step(1); o.pCast = { t: G.unseenOf(-1).t, sees: G.sees(0, -1) };
    G.unseen(0, 3); G.breakBy(0); put(); G.step(1); o.marked = { seen: G.bots().list[0].seen, sees: G.sees(1, 0) };
    G.unseen(0, 3); G.reset(); o.reset = G.unseenOf(0).t;
    o.ok = o.before.seen && o.before.sees && o.on.shimmer && !o.far.seen && !o.far.vis && !o.far.sees && o.near.seen && o.near.vis && o.hit.t === 0 && o.hit.seen && !o.hit.shimmer
      && !o.mid && o.timer.t === 0 && o.timer.seen && o.pHidden && o.pCast.t === 0 && o.pCast.sees && o.marked.seen && o.marked.sees && o.reset === 0;
    G.setBots(0); G.reset(); return o;
  });
  check('95 unseen: hidden from the player and bots beyond 3 m, shimmer within it, mark wins, ends on being hit, casting and its timer, new run clears it; programs and geometry flat',
    us.ok && us.programs === base.programs && us.geoms === base.geoms, JSON.stringify(us));
  // 96 Kit framework (batch 16 ticket 01): nine schools in the docs/SUITS.md order with their stat tiers from its table, every kit unbuilt yet (placeholder at Mid),
  // the default pick (Ru) leaves the bots in today's order and names, skills carry their bot tags, Mid speed equals PLAYER_SPEED, school names and select texts exist.
  const kf96 = await g(() => {
    const G = __game, C = G.config, T = G.text, o = {};
    G.setSeed(12345); G.setBots(8); G.reset(); const sc = G.schools();
    const want = { ru: ['High', 'Mid'], dao: ['Low', 'High'], fa: ['Mid', 'High'], mo: ['High', 'Low'], yinyang: ['Low', 'Mid'], za: ['Mid', 'Mid'], ming: ['Low', 'Mid'], zongheng: ['Mid', 'Mid'], nong: ['High', 'Low'] };
    o.order = C.SCHOOLS.join(','); o.tiers = C.SCHOOLS.every((k) => C.KITS[k].armor === want[k][0] && C.KITS[k].speed === want[k][1]);
    // Game changed on purpose (batch 16): kits are built ticket by ticket (02 法甲); a built school plays its own kit, every other the placeholder at Mid.
    // Batch 16 ticket 03 (game changed on purpose): 儒甲 built too; the checks' placeholder player (pkit, default pick 儒甲) plays the placeholder, every bot its school's kit when built.
    // Batch 16 ticket 04 (game changed on purpose): 墨甲 built too.
    // Batch 16 ticket 05 (game changed on purpose): 名甲 built too.
    // Batch 16 ticket 06 (game changed on purpose): 阴阳甲 built too (ultMode 'lock').
    // Batch 16 ticket 07 (game changed on purpose): 农甲 built too.
    o.unbuilt = C.SCHOOLS.filter((k) => C.KITS[k].built).join(',') === 'ru,fa,mo,yinyang,ming,nong';
    o.placeholder = sc.suits.every((q) => (C.KITS[q.school].built && q.id !== 0 ? q.kit === q.school && q.ultMode === C.KITS[q.school].ultMode : q.kit === 'placeholder' && q.ultMode === 'charge'));
    o.player = sc.suits[0].school; o.bots = sc.suits.slice(1).map((q) => q.name).join(','); o.tags = C.SKILLS.map((k) => k.tag).join(',');
    o.speedMid = C.STATS.speed.Mid === C.PLAYER_SPEED && C.STATS.yard === 'Mid'; o.keys = C.SCHOOLS.map((k) => 'school_' + k).concat(['hud_school', 'sel_title', 'sel_rule', 'sel_random', 'sel_key']).filter((k) => !T[k]);
    G.setBots(0); G.reset(); return o;
  });
  check('96 kit framework: nine schools in order with their stat tiers, all on the placeholder kit at Mid until built, default pick keeps the bots\' order, skill tags, text keys',
    kf96.order === 'ru,dao,fa,mo,yinyang,za,ming,zongheng,nong' && kf96.tiers && kf96.unbuilt && kf96.placeholder && kf96.player === 'ru'
    && kf96.bots === 'Dao suit,Fa suit,Mo suit,Yinyang suit,Za suit,Ming suit,Zongheng suit,Nong suit' && kf96.tags === 'poke,dashIn,ult' && kf96.speedMid && kf96.keys.length === 0, JSON.stringify(kf96));
  // ===== Batch 16 ticket 02: 法甲 · 廷尉 kit (docs/SUITS.md; numbers in CONFIG.KITS.fa) =====
  // Page helper: the player plays 法甲 (school 2) against n placeholder bots at Mid; nothing else happens (decrees pushed away, huge health).
  await g(() => { const G = __game, C = G.config; window.__fa = {
    // Batch 16 ticket 03 (game changed on purpose): 儒甲 is built, so bot 0 would play its kit; the 法甲 checks keep every bot on the placeholder at Mid.
    start(n) { G.setSeed(12345); G.setBots(n); G.pickSchool(2); for (let i = 0; i < n; i++) G.placeholderKit(i); G.setDecNext(1e9); G.setHp(1e9); for (let i = 0; i < n; i++) G.setBotHp(i, 100); },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    lost(i, fn) { G.setBotHp(i, 100); fn(); return +(100 - G.bots().list[i].hp).toFixed(4); },
    end() { G.pickSchool(0); G.setBots(0); G.reset(); } }; });
  // 97 Passive 法不阿贵: 法甲's hits take +law.bonus against the leader and against a marked suit; the two do not stack; another school's hits do not.
  const fa97 = await g(() => {
    const G = __game, F = window.__fa, o = {};
    F.start(3); o.player = G.kitState(-1).school; o.plain = F.lost(0, () => G.strike(-1, 0, 10));
    G.plateTo(1, 'stalker'); o.leaderId = G.leader().id; o.leader = F.lost(1, () => G.strike(-1, 1, 10));
    G.breakBy(2); o.marked = F.lost(2, () => G.strike(-1, 2, 10));
    G.breakBy(1); o.both = F.lost(1, () => G.strike(-1, 1, 10));
    o.other = F.lost(1, () => G.strike(0, 1, 10)); o.bonus = G.config.KITS.fa.law.bonus;
    F.end(); return o;
  });
  check('97 法甲 passive: +bonus on the leader and on a marked suit, no stacking, only 法甲 gets it',
    fa97.player === 'fa' && fa97.plain === 10 && fa97.leaderId === 2 && Math.abs(fa97.leader - 10 * (1 + fa97.bonus)) < 1e-9 && Math.abs(fa97.marked - fa97.leader) < 1e-9
    && Math.abs(fa97.both - fa97.leader) < 1e-9 && fa97.other === 10, JSON.stringify(fa97));
  // 98 Q 刑无等级: a pursuit dash to the target nearest the aim point, stopping short of it, at most range m; longRange against the leader, a marked suit or one
  // under half health; its burst hits on landing. A target 8 m away is reached only in the long cases.
  const fa98 = await g(() => {
    const G = __game, C = G.config, F = window.__fa, sk = C.KITS.fa.skills[0], o = {};
    const run = (prep) => { F.start(1); prep(); G.teleport(14, -20); const park = () => G.placeBot(0, 14, -12); park(); G.step(1); const hp0 = G.bots().list[0].hp;
      const ok = G.cast(0, 14, -12); F.hold(0.6, park); return { ok, travel: +(G.state().z + 20).toFixed(2), lost: +(hp0 - G.bots().list[0].hp).toFixed(2) }; };
    o.plain = run(() => {}); o.leader = run(() => G.plateTo(0, 'stalker')); o.half = run(() => G.setBotHp(0, 40)); o.marked = run(() => G.breakBy(0));
    o.range = sk.range; o.long = sk.longRange; o.dmg = sk.dmg; o.bonus = C.KITS.fa.law.bonus; F.end(); return o;
  });
  check('98 法甲 Q: pursuit dash of range m (no hit at 8 m), longRange against the leader, a marked suit or under half health (lands and hits)',
    fa98.plain.ok && Math.abs(fa98.plain.travel - fa98.range) < 0.05 && fa98.plain.lost === 0
    && fa98.leader.ok && Math.abs(fa98.leader.travel - 7.2) < 0.05 && Math.abs(fa98.leader.lost - fa98.dmg * (1 + fa98.bonus)) < 0.01
    && fa98.half.ok && Math.abs(fa98.half.travel - 7.2) < 0.05 && Math.abs(fa98.half.lost - fa98.dmg) < 0.01
    && fa98.marked.ok && Math.abs(fa98.marked.travel - 7.2) < 0.05 && Math.abs(fa98.marked.lost - fa98.dmg * (1 + fa98.bonus)) < 0.01, JSON.stringify(fa98));
  // 99 W 术·潜御: unseen for dur s (a bot 6 m away loses him; one within the shimmer radius keeps him); his first hit, even from a cast made while unseen,
  // exposes the suit it hits: every suit sees it from anywhere for exposeS s, it is not marked and the hunter cap does not change. A hit after dur + armS s
  // or after being hit exposes nothing.
  const fa99 = await g(() => {
    const G = __game, C = G.config, F = window.__fa, sk = C.KITS.fa.skills[1], o = {};
    const park = () => { G.placeBot(0, 14, -14); G.placeBot(1, 14, -18); G.placeBot(2, -14, 5); };
    F.start(3); G.teleport(14, -20); park(); G.step(1); o.before = G.sees(0, -1);
    o.cast = G.cast(1, 14, -20); G.step(1); o.unseen = +G.unseenOf(-1).t.toFixed(2); o.far = G.sees(0, -1); o.near = G.sees(1, -1);
    G.strike(-1, 2, 10); const k = G.kitState(2); o.expT = +k.expT.toFixed(2); o.seenFar = G.sees(0, 2); o.mark = G.suits()[3].markT; o.cap = G.hunters().max; o.endUnseen = G.unseenOf(-1).t;
    F.hold(sk.exposeS + 0.1, park); o.after = G.sees(0, 2);
    F.start(3); G.teleport(14, -20); park(); G.cast(1, 14, -20); F.hold(sk.dur + sk.armS + 0.1, park); G.strike(-1, 2, 10); o.late = G.kitState(2).expT;
    F.start(3); G.teleport(14, -20); park(); G.cast(1, 14, -20); G.step(1); G.hitBy(0, -1, 1); G.strike(-1, 2, 10); o.hitFirst = G.kitState(2).expT;
    F.start(3); G.teleport(14, -20); park(); G.cast(1, 14, -20); G.step(1); G.cast(0, 14, -14); F.hold(0.6, park); o.combo = +G.kitState(0).expT.toFixed(2);
    o.dur = sk.dur; o.exposeS = sk.exposeS; F.end(); return o;
  });
  check('99 法甲 W: unseen dur s (shimmer within 3 m), first hit (also after a cast from it) exposes the target to every suit for exposeS s, no mark, cap unchanged; late or after being hit no exposure',
    fa99.before && fa99.cast && Math.abs(fa99.unseen - fa99.dur) < 0.05 && !fa99.far && fa99.near && Math.abs(fa99.expT - fa99.exposeS) < 0.01 && fa99.seenFar && fa99.mark === 0
    && fa99.cap === 1 && fa99.endUnseen === 0 && !fa99.after && fa99.late === 0 && fa99.hitFirst === 0 && fa99.combo > fa99.exposeS - 0.7, JSON.stringify(fa99));
  // 100 R 势: a ring of radius m follows him for dur s (drawn and in the scene graph the whole time, gone after); suits inside are slowed and cannot start a dash
  // (the player too: the Q of a 法甲 bot's ring blocks the player's W, status 'Held'); his hits grow by exec x missing health, all bonuses capped at BONUS_CAP;
  // in the hunt the demon inside it moves slower and starts no Pounce until the ring ends.
  const fa100 = await g(() => {
    const G = __game, C = G.config, F = window.__fa, sk = C.KITS.fa.skills[2], o = {};
    const park = () => { G.placeBot(0, 14, -17); G.placeBot(1, 14, -11); };
    F.start(2); G.teleport(14, -20); park(); G.step(1); G.setCharge(-1, 100); o.cast = G.cast(2, 14, -20); o.ch = G.kitState(-1).ch;
    F.hold(0.5, park); const a = G.kitState(-1), s = G.suits(); o.ring = { in: a.ringIn, vis: a.ringVis, r: a.ringR, auraN: a.auraN };
    o.inside = { held: G.kitState(0).heldT > 0, slowK: s[1].slowK }; o.outside = { held: G.kitState(1).heldT > 0, slowT: s[2].slowT };
    G.setBotHp(0, 50); G.strike(-1, 0, 10); o.half = +(50 - G.bots().list[0].hp).toFixed(4);
    G.setBotHp(0, 20); G.strike(-1, 0, 10); o.low = +(20 - G.bots().list[0].hp).toFixed(4);
    G.plateTo(0, 'stalker'); G.setBotHp(0, 50); G.strike(-1, 0, 10); o.capped = +(50 - G.bots().list[0].hp).toFixed(4);
    F.hold(5.3, park); o.at59 = G.kitState(-1).ringIn; F.hold(0.5, park); o.end = { in: G.kitState(-1).ringIn, auraN: G.kitState(-1).auraN, held: G.kitState(0).heldT };
    G.pickSchool(0); G.setBots(2); G.setDecNext(1e9); G.setHp(1e9); G.teleport(14, -20); const near = () => { G.placeBot(1, 14, -17); G.placeBot(0, -14, 5); };
    near(); G.castSelfOf(1, 2); F.hold(0.3, near); o.botRing = G.kitState(1).ringIn; o.playerHeld = G.kitState(-1).heldT > 0; o.playerDash = G.cast(1, 14, -10); G.step(1); o.status = G.cubs().status;
    const far = () => { G.placeBot(1, -14, 5); G.placeBot(0, -10, 5); }; F.hold(0.4, far); o.freeDash = G.cast(1, 14, -10);
    G.pickSchool(2); G.setBots(0); window.__h.start(); G.setHp(1e9); window.__h.mute(1); window.__h.mute(2); window.__h.mute(0); G.teleport(0, -50);
    const hold5 = () => G.placeUnit(0, 0, -55); hold5(); G.step(1); o.huntCast = G.cast(2, 0, -50); G.unitCd(0, 'pounce', 0); let pounce = 0;
    for (let k = 0; k < Math.round((sk.dur - 0.3) / C.STEP); k++) { hold5(); G.step(1); if (G.hunt().tells.some((t) => t.move === 'pounce')) pounce++; }
    o.pounceInRing = pounce; G.step(Math.round(0.5 / C.STEP)); let after = 0; for (let k = 0; k < 180; k++) { hold5(); G.step(1); if (G.hunt().tells.some((t) => t.move === 'pounce')) after++; }
    o.pounceAfter = after; o.slow = sk.slow; o.exec = sk.exec; o.cap = C.BONUS_CAP; o.bonus = C.KITS.fa.law.bonus;
    G.pickSchool(0); G.setBots(0); G.reset(); return o;
  });
  check('100 法甲 R: ring dur s drawn and in the scene, slows and holds suits inside (no dash, player status Held), not outside; hits grow with missing health under the cap; demon held in the hunt',
    fa100.cast && fa100.ch === 0 && fa100.ring.in && fa100.ring.vis && fa100.ring.r === 6 && fa100.ring.auraN === 1 && fa100.inside.held && fa100.inside.slowK === fa100.slow
    && !fa100.outside.held && fa100.outside.slowT <= 0 && Math.abs(fa100.half - 10 * (1 + fa100.exec * 0.5)) < 1e-9 && Math.abs(fa100.low - 10 * (1 + fa100.exec * 0.8)) < 1e-9
    && Math.abs(fa100.capped - 10 * fa100.cap) < 1e-9 && fa100.at59 && !fa100.end.in && fa100.end.auraN === 0 && fa100.end.held === 0
    && fa100.botRing && fa100.playerHeld && fa100.playerDash === false && /Held/.test(fa100.status) && fa100.freeDash === true
    && fa100.huntCast && fa100.pounceInRing === 0 && fa100.pounceAfter > 0, JSON.stringify(fa100));
  // 101 Signature (fog, decrees and the mark): a suit far outside the player's vision is hidden; exposed by 法甲's W hit it is drawn and on the minimap until
  // exposeS ends; a decree breaker (marked) takes the passive bonus and is a long pursuit target.
  const fa101 = await g(() => {
    const G = __game, C = G.config, F = window.__fa, o = {};
    const park = () => { G.placeBot(0, 14, -14); G.placeBot(1, -14, 5); };
    F.start(2); G.teleport(14, -20); park(); G.step(2); const b = G.bots().list[1]; o.before = { seen: b.seen, vis: b.vis, mini: G.miniPixel(b.x, b.z) };
    G.cast(1, 14, -20); G.step(1); G.strike(-1, 1, 10); F.hold(0.2, park); const e = G.bots().list[1]; o.exposed = { seen: e.seen, vis: e.vis, mini: G.miniPixel(e.x, e.z) };
    F.hold(C.KITS.fa.skills[1].exposeS, park); const f = G.bots().list[1]; o.after = { seen: f.seen, vis: f.vis };
    G.breakBy(0); o.markedLost = F.lost(0, () => G.strike(-1, 0, 10)); o.bonus = C.KITS.fa.law.bonus;
    F.end(); return o;
  });
  const orange = (p) => p[0] > 200 && p[1] > 90 && p[1] < 160 && p[2] < 110;
  check('101 法甲 signature: exposure shows a far suit through the fog (body and minimap) for exposeS s; a decree breaker takes the passive bonus',
    !fa101.before.seen && !fa101.before.vis && !orange(fa101.before.mini) && fa101.exposed.seen && fa101.exposed.vis && orange(fa101.exposed.mini) && !fa101.after.seen && !fa101.after.vis
    && Math.abs(fa101.markedLost - 10 * (1 + fa101.bonus)) < 1e-9, JSON.stringify(fa101));
  // 102 法甲 in whole matches: 3 seeds with the 法甲 bot (default pick) and 1 with the player on 法甲 (autopilot), watched to the end: 法甲 on a floor every tick,
  // the hunter cap holds every tick, never stuck over 3 s; over the 3 bot matches it casts Q, W and R at least once each.
  const fa102 = await g(() => {
    const G = __game, C = G.config, o = { viol: [], casts: { q: 0, w: 0, r: 0 }, player: { q: 0, w: 0, r: 0 } }, bad = (x) => { if (o.viol.length < 5) o.viol.push(x); };
    const one = (seed, playerFa) => {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.pickSchool(playerFa ? 2 : 0); G.autoPlayer(true); G.setWatch(true);
      const fi = playerFa ? -1 : G.schools().suits.findIndex((q) => q.school === 'fa') - 1, cnt = playerFa ? o.player : o.casts; let last = [0, 0], ult = 0;
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) break;
        const k = G.kitState(fi), cd = k.bcd;
        if (cd[0] > last[0] + 1e-9) cnt.q++; if (cd[1] > last[1] + 1e-9) cnt.w++; if (k.ultN > ult) cnt.r += k.ultN - ult; last = [cd[0], cd[1]]; ult = k.ultN;
        const h = G.hunters(); if (h.capOnP > h.max) bad(`s${seed} t${t} cap ${h.capOnP}>${h.max}`);
        if (t % 10 === 0 && fi >= 0) { const q = G.bots().list[fi]; if (!q.standOk) bad(`s${seed} t${t} fa off floor`); }
        if (t % 10 === 0 && fi < 0 && !G.player().dead && !G.state().falling && !G.walkable(G.player().x, G.player().z, G.player().y + 0.05)) bad(`s${seed} t${t} player off floor`);
      }
      if (fi >= 0) { const q = G.bots().list[fi]; if (q.stuck > 3) bad(`s${seed} fa stuck ${q.stuck}`); }
      G.setWatch(false); G.autoPlayer(false);
    };
    for (const seed of [12345, 2, 3]) one(seed, false);
    one(4, true);
    G.pickSchool(0); G.setBots(0); G.reset(); return o;
  });
  check('102 法甲 in whole matches: on a floor and never stuck > 3 s, hunter cap every tick, the 法甲 bot casts Q, W and R (player 法甲 autopilot reported)',
    fa102.viol.length === 0 && fa102.casts.q > 0 && fa102.casts.w > 0 && fa102.casts.r > 0, JSON.stringify(fa102));
  // 103 Budget with 法甲's effects: the heaviest royale (every suit, 7 cubs, tells) with the player's 势 ring drawn and an exposed far suit drawn;
  // calls < 500, tris < 500k, no shader compile, geometry flat.
  const fa103 = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(C.BOTS.count); G.pickSchool(2); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      const park = () => { for (let i = 0; i < C.BOTS.count - 1; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); G.placeBot(C.BOTS.count - 1, -14, 5); };
      park(); G.step(1); G.setCharge(-1, 100); G.cast(2, cx, cz); G.cast(1, cx, cz); G.strike(-1, C.BOTS.count - 1, 1);
      for (let n = 0; n < 300; n++) {
        park(); G.step(1); const c = G.cubs(), k = G.kitState(-1), far = G.bots().list[C.BOTS.count - 1];
        if (k.ringIn && far.vis && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, ring: k.ringIn, exposed: far.vis, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.pickSchool(0); G.setBots(0); G.reset(); }
    return best;
  });
  check('103 budget with 法甲 effects: every suit + cubs + tells + 势 ring + exposed suit (calls<500, tris<500k), no shader compile, geometry flat',
    !!fa103 && fa103.ring && fa103.exposed && fa103.tells >= 1 && fa103.calls < 500 && fa103.tris < 500000 && fa103.programs === base.programs && fa103.geoms === base.geoms, JSON.stringify(fa103));
  // ===== Batch 16 ticket 03: 儒甲 · 君子 kit (docs/SUITS.md; numbers in CONFIG.KITS.ru) =====
  // Page helper: the player plays 儒甲 (school 0, the checks' placeholder switch off) against n placeholder bots at Mid; decrees pushed away.
  await g(() => { const G = __game, C = G.config; window.__ru = {
    start(n) { G.setSeed(12345); G.setPkitP(false); G.setBots(n); G.pickSchool(0); for (let i = 0; i < n; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < n; i++) G.setBotHp(i, 100); },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    end() { G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); } }; });
  // 104 Passive 礼·君子之争: his hits take +bonus against the suit that last hit him (within lastS s, not after, not on another suit);
  // he takes duelK of a blow while at most one enemy is within duelM m, full damage with two; High armor on top (taken = raw x (K + Mid) / (K + High) x duelK).
  const ru104 = await g(() => {
    const G = __game, C = G.config, R = window.__ru, J = C.KITS.ru.junzi, S = C.STATS, o = {};
    R.start(2); G.setHp(100); G.teleport(14, -20); const park = () => { G.placeBot(0, 16, -20); G.placeBot(1, 14, -22); }; park(); G.step(1);
    o.kit = G.kitState(-1).kit; o.armorK = G.kitState(-1).armorK;
    G.hitBy(0, -1, 1); park(); G.step(1);
    const at = (j) => { G.setBotHp(j, 100); G.basicAttackBy(-1, j); return +(100 - G.bots().list[j].hp).toFixed(4); };
    o.last = at(0); o.other = at(1);
    const away = () => { G.placeBot(0, 40, -20); G.placeBot(1, 40, -26); };
    R.hold(J.lastS + 0.5, away); park(); o.late = at(0);
    G.step(1); o.duel2 = G.duelOf(-1); G.placeBot(1, 40, -20); G.step(1); o.duel1 = G.duelOf(-1);
    G.setHp(100); G.hitBy(0, -1, 20); o.takenDuel = +(100 - G.state().hp).toFixed(4);
    G.placeBot(1, 14, -22); G.step(1); G.setHp(100); G.hitBy(0, -1, 20); o.takenTwo = +(100 - G.state().hp).toFixed(4);
    o.wantDuel = +(20 * (S.K + S.armor.Mid) / (S.K + S.armor.High) * J.duelK).toFixed(4); o.wantTwo = +(20 * (S.K + S.armor.Mid) / (S.K + S.armor.High)).toFixed(4);
    o.wantLast = C.KITS.ru.attack.closeDmg * (1 + J.bonus);
    R.end(); return o;
  });
  check('104 儒甲 passive: +bonus on the suit that last hit him only within lastS s; takes duelK of a blow with one enemy near, full with two; High armor',
    ru104.kit === 'ru' && Math.abs(ru104.last - ru104.wantLast) < 1e-6 && ru104.other === 10 && ru104.late === 10 && ru104.duel1 === 0.85 && ru104.duel2 === 1
    && Math.abs(ru104.takenDuel - ru104.wantDuel) < 1e-3 && Math.abs(ru104.takenTwo - ru104.wantTwo) < 1e-3, JSON.stringify(ru104));
  // 105 Attack 射+数 (range-switching, owner 20:12): within closeR a sword cut, beyond it an arrow out to range m, no button; an attack order on a dummy at mid
  // range shoots without walking in; every every-th hit is strong: a volley of arrows at mid, a heavy cut that pushes the suit back close.
  const ru105 = await g(() => {
    const G = __game, C = G.config, R = window.__ru, A = C.KITS.ru.attack, o = {};
    R.start(1); G.setHp(1e9); G.teleport(14, -20);
    const seq = (dist) => { G.placeBot(0, 14 + dist, -20); G.step(1); G.setBotHp(0, 1000); const each = []; for (let i = 0; i < A.every; i++) { const h = G.bots().list[0].hp; G.basicAttackBy(-1, 0); each.push(+(h - G.bots().list[0].hp).toFixed(4)); } return each; };
    o.atk0 = G.kitState(-1).atkN; o.close = seq(2); o.pushed = +G.kitState(0).kx.toFixed(2);
    R.end(); R.start(1); G.setHp(1e9); G.teleport(14, -20); o.mid = seq(5); o.atkN = G.kitState(-1).atkN;
    R.end();
    G.setPkitP(false); G.pickSchool(0); G.setBots(0); G.reset(); const d = G.dummies()[1]; G.teleport(d.x, d.z - 5); G.step(2); const p0 = G.state();
    G.attack(1); G.step(Math.round(0.5 / C.STEP)); const p1 = G.state(); o.order = { hp: G.dummies()[1].hp, moved: +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(3) };
    G.stop(); G.setPkitP(true); G.reset(); return o;
  });
  const want105c = Array(C0.KITS.ru.attack.every).fill(C0.KITS.ru.attack.closeDmg); want105c[want105c.length - 1] = C0.KITS.ru.attack.heavyDmg;
  const want105m = Array(C0.KITS.ru.attack.every).fill(C0.KITS.ru.attack.farDmg); want105m[want105m.length - 1] = C0.KITS.ru.attack.farDmg * C0.KITS.ru.attack.volley;
  check('105 儒甲 attack: sword within closeR, arrow beyond to range (an order shoots without walking in), every 6th hit a volley at mid or a heavy cut that pushes close',
    ru105.atk0 === 0 && JSON.stringify(ru105.close) === JSON.stringify(want105c) && ru105.pushed === C0.KITS.ru.attack.heavyKb && JSON.stringify(ru105.mid) === JSON.stringify(want105m) && ru105.atkN === C0.KITS.ru.attack.every
    && ru105.order.hp === 100 - C0.KITS.ru.attack.farDmg && ru105.order.moved < 0.01, JSON.stringify(ru105));
  // 106 Q 御 (chariot charge): a dash of range m by the walking rule; every suit along its path (width m) is hit and driven sideways away from the path;
  // a suit off the path or beyond its end is not hit; the cooldown starts.
  const ru106 = await g(() => {
    const G = __game, C = G.config, R = window.__ru, Q = C.KITS.ru.skills[0], o = {};
    R.start(3); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 16.5, -20.3); G.placeBot(1, 16.5, -23); G.placeBot(2, 21.5, -20); }; park(); G.step(1);
    o.cast = G.cast(0, 24, -20); const z0 = G.bots().list[0].z; R.hold(Q.dashS + 0.1); const b = G.bots().list; o.hit = 100 - b[0].hp; o.off = 100 - b[1].hp; o.beyond = 100 - b[2].hp;
    o.travel = +(G.state().x - 14).toFixed(2); R.hold(0.3); o.side = +(G.bots().list[0].z - z0).toFixed(2); o.cd = +G.kitState(-1).cd[0].toFixed(2);
    R.end(); return o;
  });
  check('106 儒甲 Q: chariot dash of range m, hits every suit along its path and drives it sideways off the path; off-path and beyond-end suits untouched; cooldown',
    ru106.cast && ru106.hit === C0.KITS.ru.skills[0].dmg && ru106.off === 0 && ru106.beyond === 0 && Math.abs(ru106.travel - C0.KITS.ru.skills[0].range) < 0.35 && ru106.side < -0.5
    && ru106.cd > C0.KITS.ru.skills[0].cd - 1, JSON.stringify(ru106));
  // 107 W 书·正名 (seal shot): a suit it hits takes its damage and its plates and boons stop working for seal s (a Howler plate's speed and a speed boon are off),
  // then work again; the sealed player's status line says so, written only on change.
  const ru107 = await g(() => {
    const G = __game, C = G.config, R = window.__ru, W = C.KITS.ru.skills[1], o = {};
    R.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 19, -20); G.placeBot(1, 14, -26); }; park(); G.plateTo(0, 'howler'); G.forceNeutral(1, 4, 'speed', 1); G.hitNeutralBy(1, 0, 1e4); G.step(1);
    o.boon = G.bots().list[0].bT[3] > 0; o.spdPlate = G.kitState(0).spd; o.cast = G.cast(1, 19, -20); o.dmg = 100 - G.bots().list[0].hp; o.sealT = G.kitState(0).sealT; o.spdSealed = G.kitState(0).spd;
    R.hold(W.seal + 0.1, park); o.sealEnd = G.kitState(0).sealT; o.spdAfter = G.kitState(0).spd; o.base = C.STATS.speed.Mid;
    G.seal(-1, 2); G.step(1); o.status = G.huntUi().status; R.hold(2.2); o.statusEnd = G.huntUi().status;
    R.end(); return o;
  });
  check('107 儒甲 W: seal shot hits and turns the target\'s plates and boons off for seal s (Howler speed gone, back after); the player\'s status says Sealed, then not',
    ru107.cast && ru107.boon && ru107.spdPlate > ru107.base * (1 + C0.PLATE.speed) + 0.01 && ru107.dmg === C0.KITS.ru.skills[1].dmg && Math.abs(ru107.sealT - C0.KITS.ru.skills[1].seal) < 0.05 && ru107.spdPlate > ru107.base && ru107.spdSealed === ru107.base
    && ru107.sealEnd === 0 && ru107.spdAfter === ru107.spdPlate && /Sealed/.test(ru107.status) && !/Sealed/.test(ru107.statusEnd), JSON.stringify(ru107));
  // 108 R 乐 (编钟): three rings around him over about 2 s, each shown on the ground (radius m, drawn and in the scene) for >= 0.4 s before it lands; each ring hits
  // a suit inside for dmg and slows it, the last also stuns; a suit outside is untouched; every suit hit heals him heal (control: heal 0); the meter empties;
  // the ring leaves the scene after the last ring.
  const ru108 = await g(() => {
    const G = __game, C = G.config, R = window.__ru, B = C.KITS.ru.skills[2], o = { gaps: [] };
    const run = (heal) => {
      const keep = B.heal; B.heal = heal; const r = { lost: [], at: [] };
      try {
        // Bot 0 stands 4 m away (inside the ring, outside its own attack reach) with its skills held, so no blow of its own feeds 儒甲's passive here.
        R.start(2); G.setHp(50); G.teleport(14, -20); const park = () => { G.placeBot(0, 18, -20); G.placeBot(1, 14, -26); for (let k = 0; k < 3; k++) G.setBotCd(0, k, 99); }; park(); G.step(1); G.setCharge(-1, 100);
        r.cast = G.cast(2, 14, -20); const k = G.kitState(-1); r.ring = { in: k.bellIn, r: k.bellR, n: k.bellN0 }; r.ch = k.ch;
        let prevN = 0, t = 0;
        r.slow = []; r.stun = []; r.vis = [];
        while (t < 3 / C.STEP) {
          park(); G.step(1); t++; const s = G.kitState(-1);
          if (s.bellIn) r.vis.push(s.bellVis);
          const n = s.bellT < 0 ? B.rings.length : s.bellN;
          if (n > prevN) { prevN = n; const q = G.kitState(0); r.lost.push(100 - G.bots().list[0].hp); r.at.push(+(t * C.STEP).toFixed(3)); r.slow.push(+q.slowT.toFixed(2)); r.stun.push(+q.stunT.toFixed(2)); }
          if (prevN >= B.rings.length) break;
        }
        const e = G.kitState(-1); r.end = { in: e.bellIn, n: e.bellN0 }; r.other = 100 - G.bots().list[1].hp; r.hp = G.state().hp;
      } finally { B.heal = keep; }
      R.end(); return r;
    };
    o.on = run(B.heal); o.off = run(0); o.minGap = Math.min(B.rings[0], ...B.rings.slice(1).map((v, i) => v - B.rings[i]));
    return o;
  });
  check('108 儒甲 R: three rings, each told >= 0.4 s on the ground (radius m) before it lands, dmg + slow each, stun on the last, outside untouched, heals per suit hit, meter emptied, ring removed',
    ru108.minGap >= 0.4 && ru108.on.cast && ru108.on.ring.in && ru108.on.ring.r === C0.KITS.ru.skills[2].radius && ru108.on.ch === 0
    && JSON.stringify(ru108.on.lost) === JSON.stringify([1, 2, 3].map((n) => n * C0.KITS.ru.skills[2].dmg))
    && ru108.on.at.every((t, i) => Math.abs(t - C0.KITS.ru.skills[2].rings[i]) < 0.05) && ru108.on.other === 0 && !ru108.on.end.in && ru108.on.end.n === 0
    && ru108.on.slow.every((v) => v > 0) && ru108.on.stun[0] === 0 && ru108.on.stun[1] === 0 && ru108.on.stun[2] > 0 && ru108.on.vis.length > 0 && ru108.on.vis.every((v) => v)
    && Math.abs((ru108.on.hp - ru108.off.hp) - 3 * C0.KITS.ru.skills[2].heal) < 1e-6, JSON.stringify(ru108));
  // 109 Signature (plates, the leader, the bounty): 正名 on the leader turns its plates off (a Howler plate's speed) for seal s, but the leader keeps the lead
  // (it still holds the plates, also when another suit's plate re-checks the lead); the seal ends on time and the plates work again.
  const ru109 = await g(() => {
    const G = __game, C = G.config, R = window.__ru, W = C.KITS.ru.skills[1], o = {};
    R.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 19, -20); G.placeBot(1, 14, -27); }; park(); G.step(1);
    G.plateTo(0, 'howler'); G.plateTo(0, 'howler'); G.step(1); o.leader0 = G.leader().id; o.spd0 = G.kitState(0).spd;
    // A plate for another suit while the leader is sealed re-checks the lead: the sealed leader still holds 2 plates and keeps it.
    o.cast = G.cast(1, 19, -20); G.step(1); G.plateTo(1, 'stalker'); G.step(1); o.leader1 = G.leader().id; o.spd1 = G.kitState(0).spd; o.sealT = +G.kitState(0).sealT.toFixed(2);
    R.hold(W.seal + 0.1, park); o.leader2 = G.leader().id; o.spd2 = G.kitState(0).spd;
    R.end(); return o;
  });
  check('109 儒甲 signature: 正名 on the leader turns its plates off for seal s while it keeps the lead; plates work again after',
    ru109.cast && ru109.leader0 === 1 && ru109.leader1 === 1 && ru109.leader2 === 1 && ru109.spd0 > C0.STATS.speed.Mid && ru109.spd1 === C0.STATS.speed.Mid && ru109.spd2 === ru109.spd0
    && ru109.sealT > C0.KITS.ru.skills[1].seal - 0.1, JSON.stringify(ru109));
  // 110 儒甲 in whole matches: 3 seeds with the 儒甲 bot (the player picks 道甲, still on the placeholder) and 1 with the player on 儒甲 (autopilot), watched to the end:
  // 儒甲 on a floor every tick, the hunter cap holds every tick, never stuck over 3 s; over the 3 bot matches it casts Q, W and R at least once each.
  const ru110 = await g(() => {
    const G = __game, C = G.config, o = { viol: [], casts: { q: 0, w: 0, r: 0 }, player: { q: 0, w: 0, r: 0 }, decided: [] }, bad = (x) => { if (o.viol.length < 5) o.viol.push(x); };
    const one = (seed, playerRu) => {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(!playerRu); G.pickSchool(playerRu ? 0 : 1); G.autoPlayer(true); G.setWatch(true);
      const ri = playerRu ? -1 : G.schools().suits.findIndex((q) => q.school === 'ru') - 1, cnt = playerRu ? o.player : o.casts; let last = [0, 0], ult = 0;
      if (!playerRu && G.schools().suits[ri + 1].kit !== 'ru') bad('ru bot not on its kit');
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) { o.decided.push(+r.decidedAt.toFixed(1)); break; }
        const k = G.kitState(ri), cd = k.bcd;
        if (cd[0] > last[0] + 1e-9) cnt.q++; if (cd[1] > last[1] + 1e-9) cnt.w++; if (k.ultN > ult) cnt.r += k.ultN - ult; last = [cd[0], cd[1]]; ult = k.ultN;
        const h = G.hunters(); if (h.capOnP > h.max) bad(`s${seed} t${t} cap ${h.capOnP}>${h.max}`);
        if (t % 10 === 0 && ri >= 0) { const q = G.bots().list[ri]; if (!q.standOk) bad(`s${seed} t${t} ru off floor`); if (!Number.isFinite(q.x + q.z + q.hp)) bad(`s${seed} t${t} NaN`); }
        if (t % 10 === 0 && ri < 0 && !G.player().dead && !G.state().falling && !G.walkable(G.player().x, G.player().z, G.player().y + 0.05)) bad(`s${seed} t${t} player off floor`);
      }
      if (ri >= 0) { const q = G.bots().list[ri]; if (q.stuck > 3) bad(`s${seed} ru stuck ${q.stuck}`); }
      G.setWatch(false); G.autoPlayer(false);
    };
    for (const seed of [12345, 2, 3]) one(seed, false);
    one(4, true);
    G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); return o;
  });
  check('110 儒甲 in whole matches: on a floor and never stuck > 3 s, hunter cap every tick, the 儒甲 bot casts Q, W and R (player 儒甲 autopilot reported)',
    ru110.viol.length === 0 && ru110.casts.q > 0 && ru110.casts.w > 0 && ru110.casts.r > 0, JSON.stringify(ru110));
  // 111 Budget with 儒甲's effects: the heaviest royale (every suit, 7 cubs, tells) with the player's 编钟 ring drawn; calls < 500, tris < 500k, no shader compile, geometry flat.
  const ru111 = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(C.BOTS.count); G.setPkitP(false); G.pickSchool(0); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      const park = () => { for (let i = 0; i < C.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); };
      park(); G.step(1); G.setCharge(-1, 100); G.cast(2, cx, cz);
      for (let n = 0; n < 110; n++) {
        park(); G.step(1); const c = G.cubs(), k = G.kitState(-1);
        if (k.bellIn && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, ring: k.bellIn, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); }
    return best;
  });
  check('111 budget with 儒甲 effects: every suit + cubs + tells + 编钟 ring (calls<500, tris<500k), no shader compile, geometry flat',
    !!ru111 && ru111.ring && ru111.calls < 500 && ru111.tris < 500000 && ru111.programs === base.programs && ru111.geoms === base.geoms, JSON.stringify(ru111));
  // ===== Batch 16 ticket 04: 墨甲 · 墨守 kit (docs/SUITS.md; numbers in CONFIG.KITS.mo) =====
  // Page helper: the player plays 墨甲 (school 3, the checks' placeholder switch off) against n placeholder bots at Mid; decrees pushed away.
  await g(() => { const G = __game, C = G.config; window.__mo = {
    start(n) { G.setSeed(12345); G.setPkitP(false); G.setBots(n); G.pickSchool(3); for (let i = 0; i < n; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < n; i++) G.setBotHp(i, 100); },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    end() { G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); } }; });
  // 112 Passive 非攻: his hits take +bonus against a suit that attacked someone in the last aggroS s (not one that did not, not after aggroS);
  // after standing still stillS s he takes stillK of a blow (High armor on top), full damage again once he moves; no skill of his dashes (GDD: no dash).
  const mo112 = await g(() => {
    const G = __game, C = G.config, M = window.__mo, F = C.KITS.mo.feigong, S = C.STATS, o = {};
    // Both bots are kept apart and their skills held, so only the scripted blows set who attacked.
    M.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 18, -20); G.placeBot(1, 14, -30); for (let i = 0; i < 2; i++) for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99); }; park(); G.step(1);
    o.kit = G.kitState(-1).kit; o.noDash = C.KITS.mo.skills.every((k) => !k.dash);
    const at = (j) => { G.setBotHp(j, 100); G.basicAttackBy(-1, j); return +(100 - G.bots().list[j].hp).toFixed(4); };
    G.strike(0, 1, 1); park(); G.step(1); o.aggr = at(0); o.calm = at(1);
    M.hold(F.aggroS + 0.2, park); o.late = at(0);
    M.hold(F.stillS + 0.1, park); o.stillK = G.moState(-1).takenK; G.setHp(100); G.hitBy(0, -1, 20); o.takenStill = +(100 - G.state().hp).toFixed(4);
    G.setMove(0, 1); G.step(2); G.clearMove(); o.movedK = G.moState(-1).takenK; G.setHp(100); G.hitBy(0, -1, 20); o.takenMoved = +(100 - G.state().hp).toFixed(4);
    o.wantStill = +(20 * (S.K + S.armor.Mid) / (S.K + S.armor.High) * F.stillK).toFixed(4); o.wantMoved = +(20 * (S.K + S.armor.Mid) / (S.K + S.armor.High)).toFixed(4);
    o.wantAggr = +(C.KITS.mo.attack.dmg * (1 + F.bonus)).toFixed(4);
    M.end(); return o;
  });
  check('112 墨甲 passive: +bonus on a suit that attacked someone within aggroS s only; takes stillK after standing still stillS s, full after moving; High armor; no dash skill',
    mo112.kit === 'mo' && mo112.noDash && Math.abs(mo112.aggr - mo112.wantAggr) < 1e-6 && mo112.calm === C0.KITS.mo.attack.dmg && mo112.late === C0.KITS.mo.attack.dmg
    && mo112.stillK === C0.KITS.mo.feigong.stillK && mo112.movedK === 1 && Math.abs(mo112.takenStill - mo112.wantStill) < 1e-3 && Math.abs(mo112.takenMoved - mo112.wantMoved) < 1e-3, JSON.stringify(mo112));
  // 113 Attack 连弩: bolts of dmg out to range m every interval s; an attack order on a dummy within range shoots without walking in; one beyond range is walked to.
  const mo113 = await g(() => {
    const G = __game, C = G.config, A = C.KITS.mo.attack, o = {};
    G.setPkitP(false); G.pickSchool(3); G.setBots(0); G.reset(); const d = G.dummies()[1]; G.teleport(d.x, d.z - 5); G.step(2); const p0 = G.state();
    G.attack(1); G.step(Math.round((A.interval * 2 + 0.05) / C.STEP)); const p1 = G.state(); o.inRange = { hp: G.dummies()[1].hp, moved: +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(3) };
    G.stop(); G.reset(); G.teleport(d.x, d.z - A.range - 3); G.step(2); const q0 = G.state(); G.attack(1); G.step(Math.round(0.6 / C.STEP)); const q1 = G.state();
    o.far = { moved: +Math.hypot(q1.x - q0.x, q1.z - q0.z).toFixed(3) };
    G.stop(); G.setPkitP(true); G.pickSchool(0); G.reset(); return o;
  });
  check('113 墨甲 attack: crossbow bolts of dmg every interval s out to range m without walking in; beyond range he walks',
    mo113.inRange.hp === 100 - 3 * C0.KITS.mo.attack.dmg && mo113.inRange.moved < 0.01 && mo113.far.moved > 1, JSON.stringify(mo113));
  // 114 Q 距云梯 (the wall): raised at the aim point (clamped to range), len m across the aim and thick m deep, drawn, cooldown started; it stops walking,
  // his own and others' bolts and line skills through it (the line test); not raised over a body (no cast, no cooldown); it comes down after dur s and the way is open.
  const mo114 = await g(() => {
    const G = __game, C = G.config, M = window.__mo, Q = C.KITS.mo.skills[0], o = {};
    M.start(1); G.setHp(1e9); G.teleport(14, -20); G.placeBot(0, 18, -20); G.step(1);
    o.onBody = G.cast(0, 18, -20); o.cdBody = G.kitState(-1).cd[0];
    const park = () => G.placeBot(0, 20, -20); park(); G.step(1);
    o.cast = G.cast(0, 18, -20); const w = G.moState(-1); o.wall = { up: w.up, mesh: w.meshIn, dx: +(w.x1 - w.x0).toFixed(3), dz: +(w.z1 - w.z0).toFixed(3), cx: +((w.x0 + w.x1) / 2).toFixed(3), n: w.wallN };
    o.cd = +G.kitState(-1).cd[0].toFixed(2);
    G.setBotHp(0, 100); G.basicAttackBy(-1, 0); o.bolt = 100 - G.bots().list[0].hp; o.cut = G.wallCut(14, -20, 20, -20); o.clear = G.wallCut(14, -25, 20, -25);
    G.teleport(14, -20); G.setMove(1, 0); M.hold(1, park); G.clearMove(); o.walkX = +G.state().x.toFixed(2);
    M.hold(Q.dur - 1 + 0.1, park); const e = G.moState(-1); o.after = { up: e.up, mesh: e.meshIn, n: e.wallN };
    G.setBotHp(0, 100); G.teleport(14, -20); G.step(1); G.basicAttackBy(-1, 0); o.boltAfter = 100 - G.bots().list[0].hp;
    G.setMove(1, 0); M.hold(1, park); G.clearMove(); o.walkAfter = +G.state().x.toFixed(2);
    M.end(); return o;
  });
  check('114 墨甲 Q: wall at the aim point, len x thick across the aim, drawn, cooldown; stops walking and bolts through it, not around it; not over a body; down after dur s',
    mo114.onBody === false && mo114.cdBody === 0 && mo114.cast && mo114.wall.up && mo114.wall.mesh && mo114.wall.n === 1 && Math.abs(mo114.wall.dx - C0.KITS.mo.skills[0].thick) < 1e-6
    && Math.abs(mo114.wall.dz - C0.KITS.mo.skills[0].len) < 1e-6 && mo114.wall.cx === 18 && mo114.cd > C0.KITS.mo.skills[0].cd - 1 && mo114.bolt === 0 && mo114.cut && !mo114.clear
    && mo114.walkX < 17.71 && !mo114.after.up && !mo114.after.mesh && mo114.after.n === 0 && mo114.boltAfter === C0.KITS.mo.attack.dmg && mo114.walkAfter > 18.5, JSON.stringify(mo114));
  // 115 W 衡 (the lever): the plate is shown (ground tell, radius m) for delay s (>= 0.4) with no damage before it lands; then a suit on it takes dmg and is flung
  // away from him by knockback; a suit off the plate is untouched. Signature (broken rails): a suit flung toward a broken-rail gap falls into the void; flung against a rail it stays.
  const mo115 = await g(() => {
    const G = __game, C = G.config, M = window.__mo, W = C.KITS.mo.skills[1], o = {};
    M.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(1, 14, -26); }; G.placeBot(0, 18, -20); park(); G.step(1);
    // The target is held on the plate for the tell (a bot would otherwise step out of a tell it has seen).
    o.cast = G.cast(1, 18, -20); o.pend = G.pending(); const x0 = 18; let early = false, n = 0;
    while (G.pending() && n < 120) { if (G.bots().list[0].hp < 100) early = true; G.placeBot(0, 18, -20); park(); G.step(1); n++; }
    // The flung bot walks back at once (it answers the hit), so the fling is read as the farthest it got.
    o.tellS = +(n * C.STEP).toFixed(3); o.early = early; o.dmg = 100 - G.bots().list[0].hp; o.kx = +G.kitState(0).kx.toFixed(2); let far = -99; M.hold(0.8, () => { park(); far = Math.max(far, G.bots().list[0].x - x0); });
    o.flung = +far.toFixed(2); o.off = 100 - G.bots().list[1].hp;
    const K = G.K, edge = (x) => {
      M.start(1); G.setHp(1e9); G.teleport(x, 37.5); G.placeBot(0, x, 40.5); G.step(1);
      G.cast(1, x, 40.5); let fell = false; while (G.pending()) { G.placeBot(0, x, 40.5); G.step(1); }
      for (let k = 0; k < 150; k++) { G.step(1); const b = G.bots().list[0]; if (b.dead && b.cause === 'fall') fell = true; }
      const b = G.bots().list[0]; return { fell, dead: b.dead, zone: b.zone };
    };
    o.gap = edge(0); o.rail = edge(8 * K);
    M.end(); return o;
  });
  check('115 墨甲 W: lever shown for delay s (>= 0.4) with no damage before, then dmg and a fling away from him; off the plate untouched; through a broken-rail gap only',
    C0.KITS.mo.skills[1].delay >= 0.4 && mo115.cast && mo115.pend && Math.abs(mo115.tellS - C0.KITS.mo.skills[1].delay) < 0.05 && !mo115.early && mo115.dmg === C0.KITS.mo.skills[1].dmg
    && Math.abs(mo115.kx - C0.KITS.mo.skills[1].fling) < 0.5 && mo115.flung > 1.5 && mo115.off === 0 && mo115.gap.fell && !mo115.rail.fell && !mo115.rail.dead && mo115.rail.zone === 'ROOF', JSON.stringify(mo115));
  // 116 R 九距之 (nine defences): the meter empties; the next hits blows on him do no damage and push the attacker away; the status line counts them down
  // (written only on change) and is gone after the last; the blow after them hurts; unused defences end after dur s.
  const mo116 = await g(() => {
    const G = __game, C = G.config, M = window.__mo, R = C.KITS.mo.skills[2], o = { lost: [], left: [], text: [], kx: [] };
    M.start(1); G.setHp(100); G.teleport(14, -20); G.placeBot(0, 16, -20); G.step(1); G.setCharge(-1, 100);
    o.cast = G.cast(2, 14, -20); o.ch = G.kitState(-1).ch; G.step(1); o.text0 = G.moState(-1).status;
    for (let i = 0; i < R.hits + 1; i++) {
      G.placeBot(0, 16, -20); G.step(1); const k0 = G.kitState(0).kx, h0 = G.state().hp; G.hitBy(0, -1, 10); G.step(1);
      o.lost.push(+(h0 - G.state().hp).toFixed(3)); o.left.push(G.moState(-1).jiuN); o.text.push(G.moState(-1).status); o.kx.push(+(G.kitState(0).kx - k0).toFixed(2));
    }
    M.start(1); G.teleport(14, -20); G.step(1); G.setCharge(-1, 100); G.cast(2, 14, -20); M.hold(R.dur + 0.1, () => G.placeBot(0, 30, -20)); o.timeout = G.moState(-1).jiuN;
    M.end(); return o;
  });
  check('116 墨甲 R: meter emptied; the next nine blows do no damage and push the attacker away, status counts 9 to 0 and clears; the tenth hurts; unused ones end after dur s',
    mo116.cast && mo116.ch === 0 && /Nine defences 9/.test(mo116.text0) && mo116.lost.slice(0, 9).every((v) => v === 0) && mo116.lost[9] > 0
    && JSON.stringify(mo116.left) === JSON.stringify([8, 7, 6, 5, 4, 3, 2, 1, 0, 0]) && mo116.text.slice(0, 8).every((t, i) => t.includes('Nine defences ' + (8 - i))) && !/Nine defences/.test(mo116.text[8])
    && mo116.kx.slice(0, 9).every((v) => v > 0.5) && mo116.timeout === 0, JSON.stringify(mo116));
  // 117 Against the apex (docs/SUITS.md, owner 20:40): his wall stops the demon's Pounce (the dash ends before the wall, the player behind it is not hit;
  // control without the wall: hit) and a minion's Flank (refused while the wall cuts the way).
  const mo117 = await g(() => {
    const G = __game, C = G.config, H = window.__h, o = {};
    const run = (wall) => {
      G.setPkitP(false); G.setSchool(3); H.start(); H.mute(1); H.mute(2); H.mute(0, 'pounce'); G.setHp(100);
      G.teleport(0, -56); G.placeUnit(0, 0, -63); G.placeUnit(1, -15, -70); G.placeUnit(2, 15, -70);
      if (wall) o.cast = G.cast(0, 0, -59.5);
      H.until((h) => h.units[0].st === 3 || h.phase !== 'hunt', 400); const h = G.hunt();
      return { demonZ: +h.units[0].z.toFixed(2), hp: h.p.hp, hits: h.hits };
    };
    o.wall = run(true); o.open = run(false);
    G.setPkitP(false); G.setSchool(3); H.start(); H.mute(0); H.mute(1); H.mute(2, 'flank'); G.setHp(100); G.teleport(0, -56); G.placeUnit(2, 0, -61); G.placeUnit(0, -15, -70); G.placeUnit(1, 15, -70);
    o.flankCast = G.cast(0, 0, -59); H.until((h) => h.tells.length > 0, 50); o.flankTells = G.hunt().tells.length; o.flankCut = G.wallCut(0, -61, 0, -56);
    G.setPkitP(true); G.setSchool(0); G.reset(); return o;
  });
  check('117 墨甲 vs the apex: the wall stops the demon\'s Pounce before it (player behind not hit; control without wall is hit) and refuses a minion\'s Flank through it',
    mo117.cast && mo117.wall.demonZ < -59.7 && mo117.wall.hits === 0 && mo117.wall.hp === 100 && mo117.open.hits >= 1 && mo117.open.hp < 100 && mo117.flankCast && mo117.flankCut && mo117.flankTells === 0, JSON.stringify(mo117));
  // 118 Against the apex: the lever flings a minion unitM m and shoves the demon only demonM m; 九距之 turns a demon's claw back (no damage, one defence spent, demon shoved demonM m).
  const mo118 = await g(() => {
    const G = __game, C = G.config, H = window.__h, W = C.KITS.mo.skills[1], R = C.KITS.mo.skills[2], o = {};
    G.setPkitP(false); G.setSchool(3); H.start(); for (let i = 0; i < 3; i++) H.mute(i); G.setHp(1e9); G.teleport(0, -50);
    // Each unit is held on the plate for the tell (it would chase off it), then measured one step after the fling.
    G.placeUnit(1, 0, -54); G.placeUnit(0, -10, -70); G.placeUnit(2, 10, -70); G.step(1);
    G.cast(1, 0, -54); while (G.pending()) { G.placeUnit(1, 0, -54); G.step(1); } G.step(1); let u = G.hunt().units; o.minion = +(-54 - u[1].z).toFixed(2);
    H.start(); for (let i = 0; i < 3; i++) H.mute(i); G.setHp(1e9); G.teleport(-10, -60); G.placeUnit(0, -10, -66); G.placeUnit(1, 10, -70); G.placeUnit(2, 15, -70); G.step(1);
    G.cast(1, -10, -64); while (G.pending()) { G.placeUnit(0, -10, -66); G.step(1); } G.step(1); u = G.hunt().units; o.demon = +(-66 - u[0].z).toFixed(2);
    H.start(); H.mute(1); H.mute(2); H.mute(0, 'claw'); G.setHp(100); G.teleport(0, -56); G.placeUnit(0, 0, -57.5); G.placeUnit(1, -15, -70); G.placeUnit(2, 15, -70); G.step(1);
    G.cast(2, 0, -56); const d0 = G.hunt().units[0]; H.until((h) => h.units[0].st === 3, 300); const h = G.hunt();
    o.claw = { hp: h.p.hp, left: G.moState(-1).jiuN, shove: +Math.hypot(h.units[0].x - d0.x, h.units[0].z - d0.z).toFixed(2) };
    G.setPkitP(true); G.setSchool(0); G.reset(); return o;
  });
  check('118 墨甲 vs the apex: lever flings a minion about unitM m but the demon only about demonM m; 九距之 turns the demon\'s claw back (no damage, 8 left, demon shoved)',
    Math.abs(mo118.minion - C0.KITS.mo.skills[1].unitM) < 0.3 && mo118.demon > 0.2 && mo118.demon <= C0.KITS.mo.skills[1].demonM + 0.01 && mo118.claw.hp === 100 && mo118.claw.left === C0.KITS.mo.skills[2].hits - 1
    && mo118.claw.shove > 0.2, JSON.stringify(mo118));
  // 119 墨甲 in whole matches: 3 seeds with the 墨甲 bot (the player picks 道甲, still on the placeholder) and 1 with the player on 墨甲 (autopilot), watched to the end:
  // 墨甲 on a floor every tick, the hunter cap holds, nobody stuck over 3 s (walls come down after dur s), no wall stands longer than dur; the bot casts Q, W and R over the 3.
  const mo119 = await g(() => {
    const G = __game, C = G.config, Q = C.KITS.mo.skills[0], o = { viol: [], casts: { q: 0, qFlee: 0, w: 0, r: 0 }, player: { q: 0, qFlee: 0, w: 0, r: 0 }, decided: [], wallMax: 0 }, bad = (x) => { if (o.viol.length < 5) o.viol.push(x); };
    const one = (seed, playerMo) => {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(!playerMo); G.pickSchool(playerMo ? 3 : 1); G.autoPlayer(true); G.setWatch(true);
      const mi = playerMo ? -1 : G.schools().suits.findIndex((q) => q.school === 'mo') - 1, cnt = playerMo ? o.player : o.casts; let last = [0, 0], ult = 0, upT = 0;
      if (!playerMo && G.schools().suits[mi + 1].kit !== 'mo') bad('mo bot not on its kit');
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) { o.decided.push(+r.decidedAt.toFixed(1)); break; }
        const k = G.kitState(mi), cd = k.bcd, m = G.moState(mi);
        // A wall raised while fighting counts as q; one raised on the way to heal (between it and its attacker) as qFlee (reported).
        const mode = mi < 0 ? G.player().mode : G.bots().list[mi].mode;
        if (cd[0] > last[0] + 1e-9) { if (mode === 'heal') cnt.qFlee++; else cnt.q++; } if (cd[1] > last[1] + 1e-9) cnt.w++; if (k.ultN > ult) cnt.r += k.ultN - ult; last = [cd[0], cd[1]]; ult = k.ultN;
        upT = m.up ? upT + C.STEP : 0; if (upT > o.wallMax) o.wallMax = +upT.toFixed(3);
        const h = G.hunters(); if (h.capOnP > h.max) bad(`s${seed} t${t} cap ${h.capOnP}>${h.max}`);
        if (t % 10 === 0 && mi >= 0) { const q = G.bots().list[mi]; if (!q.standOk) bad(`s${seed} t${t} mo off floor`); if (!Number.isFinite(q.x + q.z + q.hp)) bad(`s${seed} t${t} NaN`); }
        if (t % 10 === 0 && mi < 0 && !G.player().dead && !G.state().falling && !G.walkable(G.player().x, G.player().z, G.player().y + 0.05)) bad(`s${seed} t${t} player off floor`);
      }
      for (const q of G.bots().list) if (q.stuck > 3) bad(`s${seed} bot${q.id} stuck ${q.stuck}`);
      G.setWatch(false); G.autoPlayer(false);
    };
    for (const seed of [12345, 2, 3]) one(seed, false);
    one(4, true);
    G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); return o;
  });
  check('119 墨甲 in whole matches: on a floor, nobody stuck > 3 s, walls down after dur, hunter cap every tick, the 墨甲 bot casts Q, W and R (player 墨甲 autopilot reported)',
    mo119.viol.length === 0 && mo119.wallMax <= C0.KITS.mo.skills[0].dur + 0.02 && mo119.casts.q > 0 && mo119.casts.w > 0 && mo119.casts.r > 0, JSON.stringify(mo119));
  // 120 Budget with 墨甲's effects: the heaviest royale (every suit, 7 cubs, tells) with the player's wall raised, the lever plate told and the status count shown;
  // calls < 500, tris < 500k, no shader compile, geometry flat.
  const mo120 = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(C.BOTS.count); G.setPkitP(false); G.pickSchool(3); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      const park = () => { for (let i = 0; i < C.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); };
      park(); G.step(1); G.setCharge(-1, 100); G.cast(2, cx, cz); G.cast(0, cx + 4, cz); park(); G.step(1); G.cast(1, cx, cz + 3);
      for (let n = 0; n < 30; n++) {
        park(); G.step(1); const c = G.cubs(), m = G.moState(-1);
        if (m.up && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, wall: m.meshIn, pend: G.pending(), status: m.status, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); }
    return best;
  });
  check('120 budget with 墨甲 effects: every suit + cubs + tells + wall + lever tell + status count (calls<500, tris<500k), no shader compile, geometry flat',
    !!mo120 && mo120.wall && mo120.calls < 500 && mo120.tris < 500000 && mo120.programs === base.programs && mo120.geoms === base.geoms, JSON.stringify(mo120));
  // ===== Batch 16 ticket 05: 名甲 · 辩者 kit (docs/SUITS.md; numbers in CONFIG.KITS.ming) =====
  // Page helper: the player plays 名甲 (school 6, the checks' placeholder switch off) against n placeholder bots at Mid with their skills held; decrees pushed away.
  await g(() => { const G = __game, C = G.config; window.__mi = {
    start(n) { G.setSeed(12345); G.setPkitP(false); G.setBots(n); G.pickSchool(6); for (let i = 0; i < n; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < n; i++) { G.setBotHp(i, 100); for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99); } },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    end() { G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); } }; });
  // 121 Passive 一尺之棰: his hits in a row on the same target take 0, then max/2, then 3max/4 ... of bonus (never reaching max, so under the game cap);
  // a hit on another target starts again, and so does one more than gapS s after the last; another school's hits get no such bonus. Low armor.
  const mi121 = await g(() => {
    const G = __game, C = G.config, M = window.__mi, H = C.KITS.ming.halving, o = {};
    M.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 18, -20); G.placeBot(1, 14, -30); }; park(); G.step(1);
    o.kit = G.kitState(-1).kit; o.armor = G.kitState(-1).armor;
    const hit = (j) => { G.setBotHp(j, 100); G.strike(-1, j, 10); return +(100 - G.bots().list[j].hp).toFixed(4); };
    o.row = []; for (let k = 0; k < 12; k++) o.row.push(hit(0));
    o.other = hit(1); o.back = hit(0); o.back2 = hit(0); M.hold(H.gapS + 0.2, park); o.late = hit(0);
    o.want = []; let b = 0; for (let k = 0; k < 12; k++) { o.want.push(+(10 * (1 + b)).toFixed(4)); b = k === 0 ? H.max / 2 : b + (H.max - b) / 2; }
    G.setPkitP(true); G.pickSchool(0); G.setBots(2); for (let i = 0; i < 2; i++) G.placeholderKit(i); park(); G.step(1); o.plain = [hit(0), hit(0), hit(0)];
    M.end(); return o;
  });
  check('121 名甲 passive: hits in a row on one target climb 0, max/2, 3max/4 ... toward max (never reached), restart on another target or after gapS s, only 名甲; Low armor',
    mi121.kit === 'ming' && mi121.row.every((v, k) => Math.abs(v - mi121.want[k]) < 1e-3) && mi121.row[11] < 10 * (1 + C0.KITS.ming.halving.max) && mi121.other === 10 && mi121.back === 10
    && Math.abs(mi121.back2 - 10 * (1 + C0.KITS.ming.halving.max / 2)) < 1e-3 && mi121.late === 10 && mi121.plain.every((v) => v === 10), JSON.stringify(mi121));
  // 122 Attack 轮不蹍地 (the wheel): an attack order on a dummy within range throws the wheel without walking in; it is drawn while out, flies out to range m
  // and back to him, and hits the dummy once out and once back (two chances: dmg, then dmg with the passive's max/2); a standing wall turns it back before the dummy.
  const mi122 = await g(() => {
    const G = __game, C = G.config, M = window.__mi, A = C.KITS.ming.attack, H = C.KITS.ming.halving, o = {};
    M.start(0); G.reset(); const d = G.dummies()[1]; G.teleport(d.x, d.z - 6); G.step(2); const p0 = G.state();
    G.attack(1); let seenOut = false, maxGone = 0, hpOut = -1; const hp0 = G.dummies()[1].hp;
    // Watched until the wheel is back (before the next throw is due).
    for (let k = 0, was = false; k < Math.round(1.5 / C.STEP); k++) { G.step(1); const w = G.mingState(-1).wheel; if (w.on && w.out && w.inScene) seenOut = true; if (w.gone > maxGone) maxGone = w.gone; if (hpOut < 0 && G.dummies()[1].hp < hp0 && w.out) hpOut = G.dummies()[1].hp; if (was && !w.on) break; was = w.on; }
    const p1 = G.state(); o.moved = +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(3); o.seenOut = seenOut; o.maxGone = +maxGone.toFixed(2); o.hpOut = hpOut; o.hp = G.dummies()[1].hp;
    o.back = !G.mingState(-1).wheel.on && !G.mingState(-1).wheel.inScene; o.want = +(100 - A.dmg - A.dmg * (1 + H.max / 2)).toFixed(3);
    G.stop();
    // A wall (the 墨甲 bot, school 3 is bot 3 when the player picks 名甲) between him and the dummy: the wheel turns back; the dummy is untouched.
    G.setSeed(12345); G.setBots(4); G.pickSchool(6); for (let i = 0; i < 3; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < 4; i++) for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99); G.teleport(d.x, d.z - 6); G.placeBot(3, d.x + 3, d.z - 3); G.step(2); G.botCast(3, 0, d.x, d.z - 3); o.wall = G.moState(3).up;
    G.attack(1); G.step(Math.round(A.interval * 0.9 / C.STEP)); o.wallHp = G.dummies()[1].hp; o.wallGone = +G.mingState(-1).wheel.gone.toFixed(2);
    G.stop(); M.end(); return o;
  });
  check('122 名甲 attack: the wheel is thrown without walking in, drawn while out, flies out to range and back, hits once out and once back (dmg, then with the passive); a wall turns it back',
    mi122.moved < 0.01 && mi122.seenOut && Math.abs(mi122.maxGone - C0.KITS.ming.attack.range) < 0.3 && mi122.hpOut === 100 - C0.KITS.ming.attack.dmg && Math.abs(mi122.hp - mi122.want) < 1e-3 && mi122.back
    && mi122.wall && mi122.wallHp === 100 && mi122.wallGone < 4, JSON.stringify(mi122));
  // 123 Q 飞鸟之景 (shadow blink): he blinks range m by the walking rule (no hit); his shadow stands where he was for shadowS s (drawn, a fake target):
  // a bot fighting him acts on the shadow for those shadowS s only (he takes no blow), then on him again. A 名甲 bot's blink: the player's auto-target
  // takes its shadow for it, then the bot itself once the shadow is gone.
  const mi123 = await g(() => {
    const G = __game, C = G.config, M = window.__mi, Q = C.KITS.ming.skills[0], o = {};
    M.start(1); G.setHp(100); G.teleport(14, -20); G.placeBot(0, 16, -20); G.step(1); G.hitBy(-1, 0, 1); for (let k = 0; k < 3; k++) G.setBotCd(0, k, 99); G.step(Math.round(0.5 / C.STEP));
    o.before = G.actOf(0); const b0 = G.bots().list[0].hp, p0 = G.state();
    G.cast(0, p0.x, p0.z - 10); o.cd = G.skills()[0]; const hpC = G.state().hp; G.step(1); const ms = G.mingState(-1); o.shadow = { t: +ms.shadowT.toFixed(2), x: +ms.decoy.x.toFixed(2), z: +ms.decoy.z.toFixed(2), in: ms.decoy.inScene, vis: ms.decoy.vis }; o.during = G.actOf(0);
    G.step(Math.round(0.3 / C.STEP)); const p1 = G.state(); o.blink = +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(2); o.at0 = Math.abs(ms.decoy.x - p0.x) < 0.01 && Math.abs(ms.decoy.z - p0.z) < 0.01;
    let hpLow = 100; for (let k = 0; k < Math.round((Q.shadowS - 0.4) / C.STEP); k++) { G.step(1); hpLow = Math.min(hpLow, G.state().hp); if (G.actOf(0) !== 'shadow0') o.lost = (o.lost || 0) + 1; }
    o.hpDuring = hpC - hpLow; o.botHp = b0 - G.bots().list[0].hp; G.step(Math.round(0.2 / C.STEP)); o.after = G.actOf(0); o.gone = !G.mingState(-1).decoy.inScene && G.mingState(-1).shadowN === 0;
    M.end();
    // A 名甲 bot (bot 5 with the default pick) blinks away: the player's auto-target picks its shadow, then the bot once the shadow is gone.
    G.setSeed(12345); G.setPkitP(true); G.setBots(6); G.pickSchool(0); for (let i = 0; i < 5; i++) { G.placeholderKit(i); G.placeBot(i, -60, 10 + i * 2); } G.setDecNext(1e9);
    G.teleport(14, -20); G.placeBot(5, 18, -20); for (let k = 0; k < 3; k++) G.setBotCd(5, k, 99); G.step(1); o.mingBot = G.schools().suits[6].kit;
    o.pickBefore = G.autoPick(12); G.botCast(5, 0, 26, -20); G.step(1); o.pickShadow = G.autoPick(12); G.step(Math.round((Q.shadowS + 0.1) / C.STEP)); o.pickAfter = G.autoPick(12);
    G.setBots(0); G.reset(); return o;
  });
  check('123 名甲 Q: blink of range m (no hit), shadow drawn where he stood for shadowS s; a bot fighting him acts on the shadow only for those s (no blow lands), then on him; the auto-target takes a 名甲 bot\'s shadow for it',
    mi123.before === 0 && mi123.cd > 0 && mi123.shadow.in && mi123.shadow.vis && Math.abs(mi123.shadow.t - C0.KITS.ming.skills[0].shadowS) < 0.05 && mi123.at0 && mi123.during === 'shadow0' && !mi123.lost
    && Math.abs(mi123.blink - C0.KITS.ming.skills[0].range) < 0.15 && mi123.hpDuring === 0 && mi123.botHp === 0 && mi123.after === 0 && mi123.gone
    && mi123.mingBot === 'ming' && mi123.pickBefore === 6 && mi123.pickShadow === 'shadow6' && mi123.pickAfter === 6, JSON.stringify(mi123));
  // 124 W 镞矢之疾 (the hanging arrowheads): the line (range x width m) is shown (drawn, in the scene) for hang s (>= 0.4) with no damage before; a suit
  // touching it then is slowed by touchSlow; when it strikes, every suit in it takes dmg; a suit off the line is untouched; cooldown started.
  const mi124 = await g(() => {
    const G = __game, C = G.config, M = window.__mi, W = C.KITS.ming.skills[1], o = {};
    M.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 14, -24); G.placeBot(1, 17, -24); }; park(); G.step(1);
    G.cast(1, 14, -28); o.cd = G.skills()[1]; let told = 0, early = false;
    for (let k = 0; k < 200; k++) { park(); G.step(1); const h = G.mingState(-1).hang[0]; if (!h.inScene) break; told++; if (G.bots().list[0].hp < 100) early = true; if (k === 0) o.line = { len: h.len, w: h.w, vis: h.vis }; if (k === 5) o.slow = G.kitState(0).slowT > 0; }
    o.toldS = +(told * C.STEP).toFixed(3); o.early = early; o.hit = 100 - G.bots().list[0].hp; o.off = 100 - G.bots().list[1].hp; o.offSlow = G.kitState(1).slowT > 0;
    M.end(); return o;
  });
  check('124 名甲 W: line of range x width shown hang s (>= 0.4) with no damage before; a suit touching it is slowed; then dmg to a suit in it, none off it; cooldown',
    mi124.cd > 0 && mi124.line.len === C0.KITS.ming.skills[1].range && mi124.line.w === C0.KITS.ming.skills[1].width && mi124.line.vis && mi124.toldS >= 0.4 && Math.abs(mi124.toldS - C0.KITS.ming.skills[1].hang) < 0.05
    && !mi124.early && mi124.slow && mi124.hit === C0.KITS.ming.skills[1].dmg && mi124.off === 0 && !mi124.offSlow, JSON.stringify(mi124));
  // 125 R 指不至 (the pointing strike): on a full meter; the very long line is shown hang s (>= 0.4) with no damage before; then every suit along it takes dmg
  // (two at different distances, both seen), one off the line none; the meter empties.
  const mi125 = await g(() => {
    const G = __game, C = G.config, M = window.__mi, R = C.KITS.ming.skills[2], o = {};
    M.start(3); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 14, -23); G.placeBot(1, 14, -29); G.placeBot(2, 18, -24); }; park(); G.step(1);
    o.empty = G.cast(2, 14, -30); G.setCharge(-1, 100); o.cast = G.cast(2, 14, -30); o.ch = G.chargeOf(-1); let told = 0, early = false;
    for (let k = 0; k < 200; k++) { park(); G.step(1); const h = G.mingState(-1).hang[1]; if (!h.inScene) break; told++; if (G.bots().list[0].hp < 100 || G.bots().list[1].hp < 100) early = true; if (k === 0) o.len = h.len; }
    o.toldS = +(told * C.STEP).toFixed(3); o.early = early; o.hits = G.bots().list.slice(0, 3).map((q) => 100 - q.hp);
    M.end(); return o;
  });
  check('125 名甲 R: only on a full meter (emptied); the long line is shown hang s (>= 0.4) with no damage before; then dmg to every suit along it, none off it',
    mi125.empty === false && mi125.cast && mi125.ch === 0 && mi125.len === C0.KITS.ming.skills[2].range && mi125.toldS >= 0.4 && !mi125.early
    && mi125.hits[0] === C0.KITS.ming.skills[2].dmg && mi125.hits[1] === C0.KITS.ming.skills[2].dmg && mi125.hits[2] === 0, JSON.stringify(mi125));
  // 126 Signature (tells and dodging): a bot fighting him in reach (it stands still to hit him) and standing in his W line steps out once it has seen
  // the line for its reaction time and takes no damage; the same bot held in place (control) is hit.
  const mi126 = await g(() => {
    const G = __game, C = G.config, M = window.__mi, o = {};
    const one = (hold) => {
      M.start(1); G.setHp(1e9); G.teleport(14, -20); G.placeBot(0, 14, -22.2); G.step(1); G.hitBy(-1, 0, 1); G.setBotHp(0, 100); for (let k = 0; k < 3; k++) G.setBotCd(0, k, 99);
      G.step(Math.round(0.6 / C.STEP)); G.placeBot(0, 14, -22.2); G.step(1); o.fight = G.actOf(0); G.cast(1, 14, -28);
      for (let k = 0; k < 120; k++) { if (hold) G.placeBot(0, 14, -22.2); G.step(1); }
      const b = G.bots().list[0]; return { hp: +(100 - b.hp).toFixed(3), dx: +Math.abs(b.x - 14).toFixed(2) };
    };
    o.free = one(false); o.held = one(true); M.end(); return o;
  });
  check('126 名甲 signature: a bot reads the hanging line and steps out of it (no damage); held in it, it is hit',
    mi126.fight === 0 && mi126.free.hp === 0 && mi126.free.dx > C0.KITS.ming.skills[1].width / 2 && mi126.held.hp === C0.KITS.ming.skills[1].dmg, JSON.stringify(mi126));
  // 127 名甲 in whole matches: 3 seeds with the 名甲 bot (the player picks 道甲, still on the placeholder) and 1 with the player on 名甲 (autopilot), watched to the end:
  // 名甲 on a floor every tick, the hunter cap holds, nobody stuck over 3 s, no wheel, shadow or line outlives its time; the bot casts Q, W and R over the 3.
  const mi127 = await g(() => {
    const G = __game, C = G.config, K = C.KITS.ming, o = { viol: [], casts: { q: 0, w: 0, r: 0 }, player: { q: 0, w: 0, r: 0 }, decided: [], shadowMax: 0, hangMax: 0 }, bad = (x) => { if (o.viol.length < 5) o.viol.push(x); };
    const one = (seed, playerMi) => {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(!playerMi); G.pickSchool(playerMi ? 6 : 1);
      // Batch 16 ticket 06 (game changed on purpose): 阴阳甲 is built now; its bot keeps the placeholder kit here so these matches stay the ones this check was written for.
      G.placeholderKit(G.schools().suits.findIndex((q) => q.school === 'yinyang') - 1);
      // Batch 16 ticket 07 (game changed on purpose): 农甲 too.
      G.placeholderKit(G.schools().suits.findIndex((q) => q.school === 'nong') - 1);
      G.autoPlayer(true); G.setWatch(true);
      const mi = playerMi ? -1 : G.schools().suits.findIndex((q) => q.school === 'ming') - 1, cnt = playerMi ? o.player : o.casts; let last = [0, 0], ult = 0, sh = 0, hg = 0;
      if (!playerMi && G.schools().suits[mi + 1].kit !== 'ming') bad('ming bot not on its kit');
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) { o.decided.push(+r.decidedAt.toFixed(1)); break; }
        const k = G.kitState(mi), cd = k.bcd, m = G.mingState(mi);
        if (cd[0] > last[0] + 1e-9) cnt.q++; if (cd[1] > last[1] + 1e-9) cnt.w++; if (k.ultN > ult) cnt.r += k.ultN - ult; last = [cd[0], cd[1]]; ult = k.ultN;
        sh = m.decoy.inScene ? sh + C.STEP : 0; if (sh > o.shadowMax) o.shadowMax = +sh.toFixed(3);
        hg = m.hang.some((h) => h.inScene) ? hg + C.STEP : 0; if (hg > o.hangMax) o.hangMax = +hg.toFixed(3);
        const h = G.hunters(); if (h.capOnP > h.max) bad(`s${seed} t${t} cap ${h.capOnP}>${h.max}`);
        if (t % 10 === 0 && mi >= 0) { const q = G.bots().list[mi]; if (!q.standOk) bad(`s${seed} t${t} ming off floor`); if (!Number.isFinite(q.x + q.z + q.hp)) bad(`s${seed} t${t} NaN`); }
        if (t % 10 === 0 && mi < 0 && !G.player().dead && !G.state().falling && !G.walkable(G.player().x, G.player().z, G.player().y + 0.05)) bad(`s${seed} t${t} player off floor`);
      }
      for (const q of G.bots().list) if (q.stuck > 3) bad(`s${seed} bot${q.id} stuck ${q.stuck}`);
      G.setWatch(false); G.autoPlayer(false);
    };
    for (const seed of [12345, 2, 3]) one(seed, false);
    one(4, true);
    G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); const m = G.mingState(-1); o.clean = m.wheelN === 0 && m.shadowN === 0 && m.hangN === 0; return o;
  });
  check('127 名甲 in whole matches: on a floor, nobody stuck > 3 s, shadows and lines end on time, hunter cap every tick, the 名甲 bot casts Q, W and R (player 名甲 autopilot reported)',
    mi127.viol.length === 0 && mi127.shadowMax <= C0.KITS.ming.skills[0].shadowS + 0.02 && mi127.hangMax <= Math.max(C0.KITS.ming.skills[1].hang, C0.KITS.ming.skills[2].hang) * 2 + 0.02
    && mi127.clean && mi127.casts.q > 0 && mi127.casts.w > 0 && mi127.casts.r > 0, JSON.stringify(mi127));
  // 128 Budget with 名甲's effects: the heaviest royale (every suit, 7 cubs, tells) with the player's wheel out, shadow standing and both lines hanging;
  // calls < 500, tris < 500k, no shader compile, geometry flat.
  const mi128 = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(C.BOTS.count); G.setPkitP(false); G.pickSchool(6); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      const park = () => { for (let i = 0; i < C.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); };
      park(); G.step(1); G.setCharge(-1, 100); G.cast(2, cx, cz + 6); G.cast(1, cx + 3, cz); G.cast(0, cx - 3, cz); G.basicAttackBy(-1, 0);
      for (let n = 0; n < 30; n++) {
        park(); G.step(1); const c = G.cubs(), m = G.mingState(-1);
        if (m.wheel.inScene && m.decoy.inScene && m.hang[0].inScene && m.hang[1].inScene && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); }
    return best;
  });
  check('128 budget with 名甲 effects: every suit + cubs + tells + wheel + shadow + both hanging lines (calls<500, tris<500k), no shader compile, geometry flat',
    !!mi128 && mi128.calls < 500 && mi128.tris < 500000 && mi128.programs === base.programs && mi128.geoms === base.geoms, JSON.stringify(mi128));
  // ===== Batch 16 ticket 06: 阴阳甲 · 太极 kit (docs/SUITS.md; numbers in CONFIG.KITS.yinyang; ultMode 'lock') =====
  await g(() => { const G = __game, C = G.config; window.__yy = {
    start(n) { G.setSeed(12345); G.setPkitP(false); G.setBots(n); G.pickSchool(4); for (let i = 0; i < n; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < n; i++) { G.setBotHp(i, 100); for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99); } },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    until(cond, max, fn) { let n = 0; while (n < max && !cond()) { if (fn) fn(); G.step(1); n++; } return n; },
    end() { G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); } }; });
  // 129 Passive 阴阳 (the lock): no meter; R is locked until both halves are full: a landed 阴 (Q) fills the dark half, a landed 阳 (W) the light half,
  // a full half gains nothing more; both full unlock R; casting R empties both and starts its cooldown. The status line and the R button show the taiji
  // symbol of the halves (written only on change: no write over a quiet span). Low armor.
  const yy129 = await g(() => {
    const G = __game, C = G.config, Y = window.__yy, K = C.KITS.yinyang, T = G.text, o = {};
    Y.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 14, -28); G.placeBot(1, 20, -20); }; park(); G.step(2);
    const s0 = G.yyState(-1); o.armor = G.schools().suits[0].armor; o.mode = s0.ultMode; o.start = [s0.yin, s0.yang, s0.unlocked]; o.text0 = [s0.status, s0.rText, s0.rCover];
    o.rLocked = G.cast(2, 14, -27);
    G.cast(0, 14, -28); Y.until(() => G.yyState(-1).yin, 120, park); G.step(2); const s1 = G.yyState(-1); o.afterQ = [s1.yin, s1.yang, s1.unlocked]; o.text1 = [s1.status, s1.rText];
    o.rOne = G.cast(2, 14, -27); const w0 = G.yyState(-1).writes; Y.hold(1, park); o.quiet = G.yyState(-1).writes - w0;
    Y.hold(K.skills[0].cd + 0.1, park); G.cast(0, 14, -28); Y.hold(1.2, park); const s2 = G.yyState(-1); o.again = [s2.yin, s2.yang];
    G.cast(1, 20, -20); Y.until(() => G.yyState(-1).yang, 120, park); G.step(2); const s3 = G.yyState(-1); o.afterW = [s3.yin, s3.yang, s3.unlocked]; o.text3 = [s3.status, s3.rCover];
    o.rCast = G.cast(2, 14, -27); const s4 = G.yyState(-1); o.afterR = [s4.yin, s4.yang, s4.unlocked, s4.cdR, s4.ultN]; o.ch = G.chargeOf(-1);
    o.want = { t0: [T.st_yy.replace('{s}', T.yy_0), T.yy_0], t1: [T.st_yy.replace('{s}', T.yy_1), T.yy_1], t3: T.st_yy.replace('{s}', T.yy_3) };
    Y.end(); return o;
  });
  check('129 阴阳甲 lock: R locked until both halves; 阴 fills dark, 阳 light, a full half gains nothing; R empties both and starts its cooldown (no meter); taiji symbol on status and R button, written only on change; Low armor',
    yy129.armor === C0.STATS.armor.Low && yy129.mode === 'lock' && yy129.start.join() === 'false,false,false' && yy129.text0[0] === yy129.want.t0[0] && yy129.text0[1] === yy129.want.t0[1] && yy129.text0[2] === 'block'
    && yy129.rLocked === false && yy129.afterQ.join() === 'true,false,false' && yy129.text1[0] === yy129.want.t1[0] && yy129.text1[1] === yy129.want.t1[1] && yy129.rOne === false && yy129.quiet === 0
    && yy129.again.join() === 'true,false' && yy129.afterW.join() === 'true,true,true' && yy129.text3[0] === yy129.want.t3 && yy129.text3[1] === 'none'
    && yy129.rCast && yy129.afterR.join() === `false,false,false,${C0.KITS.yinyang.skills[2].cd},1` && yy129.ch === 0, JSON.stringify(yy129));
  // 130 Attack 两仪: an attack order on a dummy within range fires an orb without walking in; it is drawn while it flies, lands on the dummy for dmg; shots
  // alternate dark and light; the attack fills no half; a standing wall (the 墨甲 bot's) stops the orb before the dummy.
  const yy130 = await g(() => {
    const G = __game, C = G.config, Y = window.__yy, A = C.KITS.yinyang.attack, o = {};
    Y.start(0); G.reset(); const d = G.dummies()[1]; G.teleport(d.x, d.z - 7); G.step(2); const p0 = G.state(); const hp0 = G.dummies()[1].hp;
    G.attack(1); let flying = false, looks = [], prevOn = false;
    // Watched for two shots (the third is due at 2 intervals).
    for (let k = 0; k < Math.round(A.interval * 1.9 / C.STEP); k++) { G.step(1); const ob = G.yyState(-1).orbs[0]; if (ob.on && ob.inScene && ob.vis) flying = true; if (ob.on && !prevOn) looks.push(ob.dark); prevOn = ob.on; }
    const p1 = G.state(); o.moved = +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(3); o.flying = flying; o.looks = looks; o.dealt = hp0 - G.dummies()[1].hp; o.halves = [G.yyState(-1).yin, G.yyState(-1).yang];
    G.stop(); G.step(Math.round(1 / C.STEP)); o.clear = !G.yyState(-1).orbs[0].inScene && G.yyState(-1).orbN === 0;
    // A wall (the 墨甲 bot, bot 3 when the player picks 阴阳甲) between him and the dummy: the orb stops; the dummy is untouched.
    G.setSeed(12345); G.setBots(4); G.pickSchool(4); for (let i = 0; i < 3; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < 4; i++) for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99);
    G.teleport(d.x, d.z - 6); G.placeBot(3, d.x + 3, d.z - 3); G.step(2); G.botCast(3, 0, d.x, d.z - 3); o.wall = G.moState(3).up; const hw = G.dummies()[1].hp;
    G.attack(1); G.step(Math.round(A.interval * 0.9 / C.STEP)); o.wallHp = hw - G.dummies()[1].hp; o.wallOrb = G.yyState(-1).orbs[0].on;
    G.stop(); Y.end(); return o;
  });
  check('130 阴阳甲 attack: the orb is fired without walking in, drawn while it flies, lands for dmg; shots alternate dark and light; no half filled; a wall stops it',
    yy130.moved < 0.01 && yy130.flying && yy130.dealt === 2 * C0.KITS.yinyang.attack.dmg && yy130.looks.length === 2 && yy130.looks[0] !== yy130.looks[1] && yy130.halves.join() === 'false,false' && yy130.clear
    && yy130.wall && yy130.wallHp === 0 && !yy130.wallOrb, JSON.stringify(yy130));
  // 131 Q 阴·月: an orb into empty space fills nothing; at a suit: he steps back back m (the walking rule) as it leaves, the slow orb flies at speed m/s
  // (lands about distance / speed s later), then dmg, the suit slowed by slow for slowS s, he heals drain, and the dark half fills; cooldown started.
  const yy131 = await g(() => {
    const G = __game, C = G.config, Y = window.__yy, Q = C.KITS.yinyang.skills[0], o = {};
    Y.start(1); G.teleport(14, -20); const park = () => G.placeBot(0, 14, -28); park(); G.step(2);
    G.cast(0, 24, -20); Y.hold(Q.range / Q.speed + 0.3, park); o.empty = [G.yyState(-1).yin, G.yyState(-1).yang]; Y.hold(Q.cd, park);
    G.setHp(80); const p0 = G.state(); o.cast = G.cast(0, 14, -28); const p1 = G.state(); o.back = +Math.hypot(p1.x - p0.x, p1.z - p0.z).toFixed(3); o.cd = G.skills()[0] > 0;
    // The orb leaves from where he stood before the step back.
    const dist = Math.hypot(14 - p0.x, -28 - p0.z) - 0.45 - Q.radius; let n = 0; for (; n < 200 && G.bots().list[0].hp === 100; n++) { park(); G.step(1); }
    o.landS = +(n * C.STEP).toFixed(3); o.wantS = +(dist / Q.speed).toFixed(3); o.dmg = 100 - G.bots().list[0].hp; o.slow = [G.kitState(0).slowT > 1.4, +G.kitState(0).slowT.toFixed(2)]; o.hp = G.state().hp; o.dark = G.yyState(-1).yin;
    Y.end(); return o;
  });
  check('131 阴阳甲 Q: an orb that hits nothing fills nothing; he steps back back m as it leaves; it lands about distance / speed s later: dmg, slow on the suit, drain to him, dark half filled; cooldown',
    yy131.empty.join() === 'false,false' && yy131.cast && Math.abs(yy131.back - C0.KITS.yinyang.skills[0].back) < 1e-6 && yy131.cd && Math.abs(yy131.landS - yy131.wantS) < 0.1
    && yy131.dmg === C0.KITS.yinyang.skills[0].dmg && yy131.slow[0] && yy131.hp === 80 + C0.KITS.yinyang.skills[0].drain && yy131.dark, JSON.stringify(yy131));
  // 132 W 阳·日: a sunburst at an empty point fills nothing; at a suit it is shown on the ground for delay s (>= 0.4) with no damage before, then dmg to a suit
  // inside its radius, none to one outside, and the light half fills; cooldown started.
  const yy132 = await g(() => {
    const G = __game, C = G.config, Y = window.__yy, W = C.KITS.yinyang.skills[1], o = {};
    Y.start(2); G.setHp(1e9); G.teleport(14, -20); const park = () => { G.placeBot(0, 14, -27); G.placeBot(1, 14 + W.radius + 1.5, -27); }; park(); G.step(2);
    G.cast(1, 20, -14); Y.hold(W.delay + 0.2, park); o.empty = [G.yyState(-1).yin, G.yyState(-1).yang]; Y.hold(W.cd, park);
    o.cast = G.cast(1, 14, -27); o.cd = G.skills()[1] > 0; let told = 0, early = false;
    for (let k = 0; k < 200 && G.pending(); k++) { park(); G.step(1); if (G.pending()) { told++; if (G.bots().list[0].hp < 100) early = true; } }
    o.toldS = +((told + 1) * C.STEP).toFixed(3); o.early = early; o.hit = 100 - G.bots().list[0].hp; o.off = 100 - G.bots().list[1].hp; G.step(2); o.light = G.yyState(-1).yang;
    Y.end(); return o;
  });
  check('132 阴阳甲 W: a sunburst on nothing fills nothing; at a suit it is shown delay s (>= 0.4) with no damage before, then dmg inside its radius, none outside; light half filled; cooldown',
    yy132.empty.join() === 'false,false' && yy132.cast && yy132.cd && yy132.toldS >= 0.4 && Math.abs(yy132.toldS - C0.KITS.yinyang.skills[1].delay) < 0.05 && !yy132.early
    && yy132.hit === C0.KITS.yinyang.skills[1].dmg && yy132.off === 0 && yy132.light, JSON.stringify(yy132));
  // 133 R 太极: locked without both halves; unlocked, the disk (both half disks, radius m) is shown in full for tellS s (>= 0.4) with no burn or pull before;
  // then for phaseS s a suit in the dark half is pulled toward the centre and slowed (no burn) while one in the light half burns burn every pulseS s; then the
  // halves swap for another phaseS s; then the disk is gone; the lock is empty and the cooldown started.
  const yy133 = await g(() => {
    const G = __game, C = G.config, Y = window.__yy, R = C.KITS.yinyang.skills[2], o = { tellHit: false, steps: [0, 0, 0], pullD: [0, 0, 0], pullL: [0, 0, 0], slowD: [0, 0, 0] };
    // Away from the stone lions (C1 lions at x +-9.75, z -27.75): the disk at (5, -16), its dark half east of the cast line.
    Y.start(2); G.setHp(1e9); G.teleport(5, -9); const park = () => { G.placeBot(0, 8, -16); G.placeBot(1, 2, -16); }; park(); G.step(2);
    o.locked = G.cast(2, 5, -16); G.yyFill(-1, true, true); o.cast = G.cast(2, 5, -16); const s0 = G.yyState(-1); o.lock = [s0.yin, s0.yang, s0.cdR];
    // Segments by the disk's state after each step: 0 shown (tell), 1 first phase, 2 turned, 3 gone. Health at each segment's first step is taken just before it.
    const hp = () => [G.bots().list[0].hp, G.bots().list[1].hp], start = [], endHp = []; let seg = 0; start[0] = hp();
    for (let k = 0; k < 600; k++) {
      const before = hp(); park(); G.step(1); const y = G.yyState(-1).taiji;
      const now = !y.inScene ? 3 : y.t < R.tellS - 1e-9 ? 0 : !y.flip ? 1 : 2;
      if (k === 0) o.disk = { in: y.inScene, vis: y.vis, r: y.r };
      if (now !== seg) { endHp[seg] = before; seg = now; start[seg] = before; }
      if (seg === 3) break;
      const a = G.kitState(0), b = G.kitState(1); o.steps[seg]++;
      // Pulled this step: the pull was set at R.pull m/s this step (a pull from an earlier step has decayed below 0.85 of it).
      if (a.kx < -0.85 * R.pull) o.pullD[seg]++; if (b.kx > 0.85 * R.pull) o.pullL[seg]++; if (a.slowT > 0) o.slowD[seg]++;
      if (seg === 0 && (a.kx !== 0 || b.kx !== 0 || a.slowT > 0 || hp()[0] < 100 || hp()[1] < 100)) o.tellHit = true;
    }
    o.toldS = +((o.steps[0] + 1) * C.STEP).toFixed(3); o.seg = seg;
    // A segment that never happened (e.g. the disk never turned) records null, so the check fails instead of the runner crashing (mutation 'R never turns').
    o.dmg = [1, 2].map((k) => (start[k] && endHp[k] ? [+(start[k][0] - endHp[k][0]).toFixed(2), +(start[k][1] - endHp[k][1]).toFixed(2)] : null));
    const s2 = G.yyState(-1); o.gone = !s2.taiji.inScene && s2.taijiN === 0;
    o.phaseSteps = Math.round(R.phaseS / C.STEP); o.burnWant = +(R.burn * Math.round(R.phaseS / R.pulseS)).toFixed(2);
    Y.end(); return o;
  });
  check('133 阴阳甲 R: locked without both halves; the disk is shown in full tellS s (>= 0.4) with no burn or pull; then dark half pulls and slows, light half burns; the halves swap; gone after; lock emptied, cooldown',
    yy133.locked === false && yy133.cast && yy133.lock.join() === `false,false,${C0.KITS.yinyang.skills[2].cd}` && yy133.disk.in && yy133.disk.vis && yy133.disk.r === C0.KITS.yinyang.skills[2].radius
    && yy133.toldS >= 0.4 && Math.abs(yy133.toldS - C0.KITS.yinyang.skills[2].tellS) < 0.05 && !yy133.tellHit && yy133.seg === 3 && !!yy133.dmg[0] && !!yy133.dmg[1]
    && yy133.dmg[0][0] === 0 && Math.abs(yy133.dmg[0][1] - yy133.burnWant) < 1e-6 && yy133.pullD[1] >= yy133.phaseSteps - 2 && yy133.pullL[1] === 0 && yy133.slowD[1] >= yy133.phaseSteps - 2
    && Math.abs(yy133.dmg[1][0] - yy133.burnWant) < 1e-6 && yy133.dmg[1][1] === 0 && yy133.pullD[2] === 0 && yy133.pullL[2] >= yy133.phaseSteps - 2
    && Math.abs(yy133.steps[1] - yy133.phaseSteps) <= 1 && Math.abs(yy133.steps[2] - yy133.phaseSteps) <= 1 && yy133.gone, JSON.stringify(yy133));
  // 134 Lock rules: under "Ultimates 2x" only the cooldown after use runs 2x (1x in the warning, 2x in force) and R stays locked until both halves fill
  // again; the meter's gains do not apply to him. Silenced on a bridge, a 阴 that lands fills nothing (cast off the bridge, landed after he stepped on it);
  // the same cast without the step fills the dark half.
  const yy134 = await g(() => {
    const G = __game, C = G.config, Y = window.__yy, R = C.KITS.yinyang.skills[2], Q = C.KITS.yinyang.skills[0], o = {};
    Y.start(1); G.setHp(1e9); G.teleport(14, -20); G.placeBot(0, 14, -28); G.step(2);
    G.yyFill(-1, true, true); G.cast(2, 14, -27); const c0 = G.yyState(-1).cdR; G.forceDecree('ult2x', null, 20);
    Y.hold(5, () => G.placeBot(0, 14, -28)); const c1 = G.yyState(-1).cdR; Y.hold(2, () => G.placeBot(0, 14, -28)); const c2 = G.yyState(-1).cdR;
    o.warnRate = +((c0 - c1) / 5).toFixed(2); o.onRate = +((c1 - c2) / 2).toFixed(2);
    Y.until(() => G.yyState(-1).cdR <= 0, 2000, () => G.placeBot(0, 14, -28)); o.cd0Locked = G.cast(2, 14, -27); o.ch = G.chargeOf(-1);
    Y.end();
    const one = (step) => {
      // The player beside the west bridge in the centre court (away from its stone lion at -18, 0.75), the bot 6 m east.
      Y.start(1); G.setHp(1e9); G.forceDecree('silence', null, 30); G.teleport(-19, 6); const park = () => G.placeBot(0, -13, 6); park(); Y.hold(5.1, park);
      // The step onto the bridge keeps the bot in his vision (a player's skill hits only what he sees).
      o.silOk = G.decree().key === 'silence' && G.decree().st === 3; const cast = G.cast(0, -13, 6); if (step) G.teleport(-22, 6);
      Y.hold(Q.range / Q.speed + 0.3, park); const r = { cast, hit: 100 - G.bots().list[0].hp, zone: G.state().zone, yin: G.yyState(-1).yin }; Y.end(); return r;
    };
    o.bridge = one(true); o.ground = one(false); return o;
  });
  check('134 阴阳甲 lock rules: "Ultimates 2x" runs only the cooldown after use 2x (1x in the warning) and R stays locked at cooldown 0; no meter; a 阴 landing while he stands silenced on a bridge fills nothing, off the bridge it fills',
    Math.abs(yy134.warnRate - 1) < 0.02 && Math.abs(yy134.onRate - C0.DECREES.ultK) < 0.02 && yy134.cd0Locked === false && yy134.ch === 0 && yy134.silOk
    && yy134.bridge.cast && yy134.bridge.zone === 'WB2' && yy134.bridge.hit === C0.KITS.yinyang.skills[0].dmg && yy134.bridge.yin === false && yy134.ground.cast && yy134.ground.zone === 'C2' && yy134.ground.hit === C0.KITS.yinyang.skills[0].dmg && yy134.ground.yin === true, JSON.stringify(yy134));
  // 135 阴阳甲 in the hunt: the wake fills the lock, so 太极 is ready at the start; cast, it empties the lock and starts the 30 s cooldown; a 阴 landing on a
  // minion fills the dark half again (hunt units count).
  const yy135 = await g(() => {
    const G = __game, C = G.config, H = window.__h, o = {};
    G.setPkitP(false); G.pickSchool(4); G.setBots(0); H.start(); for (let i = 0; i < 3; i++) H.mute(i); G.setHp(1e9);
    const s0 = G.yyState(-1); o.start = [s0.yin, s0.yang, s0.unlocked, G.hunt().phase];
    G.teleport(0, -50); G.placeUnit(1, 0, -56); G.placeUnit(0, -15, -70); G.placeUnit(2, 15, -70); G.step(2);
    o.cast = G.cast(2, 0, -58); const s1 = G.yyState(-1); o.after = [s1.yin, s1.yang, +s1.cdR.toFixed(2)];
    G.cast(0, 0, -56); for (let k = 0; k < 120 && !G.yyState(-1).yin; k++) { G.placeUnit(1, 0, -56); G.step(1); } o.dark = G.yyState(-1).yin; o.minion = G.hunt().units[1].hp < C.STALKER.hp;
    G.setPkitP(true); G.pickSchool(0); G.reset(); return o;
  });
  check('135 阴阳甲 in the hunt: the wake fills the lock (R ready at the start); R empties it and starts its cooldown; 阴 on a minion fills the dark half',
    yy135.start.join() === 'true,true,true,hunt' && yy135.cast && yy135.after[0] === false && yy135.after[1] === false && yy135.after[2] === C0.KITS.yinyang.skills[2].cd && yy135.dark && yy135.minion, JSON.stringify(yy135));
  // 136 阴阳甲 in whole matches: 3 seeds with the 阴阳甲 bot (the player picks 道甲) and 1 with the player on 阴阳甲 (autopilot), watched to the end:
  // 阴阳甲 on a floor every tick, the hunter cap holds, nobody stuck over 3 s, no orb or disk outlives its time; the bot casts Q and W and unlocks and casts R over the 3.
  const yy136 = await g(() => {
    const G = __game, C = G.config, K = C.KITS.yinyang, R = K.skills[2], o = { viol: [], casts: { q: 0, w: 0, r: 0 }, player: { q: 0, w: 0, r: 0 }, decided: [], orbMax: 0, diskMax: 0 }, bad = (x) => { if (o.viol.length < 5) o.viol.push(x); };
    const orbLife = Math.max(K.attack.range / K.attack.speed, K.skills[0].range / K.skills[0].speed);
    const one = (seed, playerYy) => {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(!playerYy); G.pickSchool(playerYy ? 4 : 1); G.autoPlayer(true); G.setWatch(true);
      const yi = playerYy ? -1 : G.schools().suits.findIndex((q) => q.school === 'yinyang') - 1, cnt = playerYy ? o.player : o.casts; let last = [0, 0], ult = 0, ob = [0, 0], dk = 0;
      if (!playerYy && G.schools().suits[yi + 1].kit !== 'yinyang') bad('yinyang bot not on its kit');
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) { o.decided.push(+r.decidedAt.toFixed(1)); break; }
        const k = G.kitState(yi), cd = k.bcd, y = G.yyState(yi);
        if (cd[0] > last[0] + 1e-9) cnt.q++; if (cd[1] > last[1] + 1e-9) cnt.w++; if (y.ultN > ult) cnt.r += y.ultN - ult; last = [cd[0], cd[1]]; ult = y.ultN;
        for (let j = 0; j < 2; j++) { ob[j] = y.orbs[j].inScene ? ob[j] + C.STEP : 0; if (ob[j] > o.orbMax) o.orbMax = +ob[j].toFixed(3); }
        dk = y.taiji.inScene ? dk + C.STEP : 0; if (dk > o.diskMax) o.diskMax = +dk.toFixed(3);
        const h = G.hunters(); if (h.capOnP > h.max) bad(`s${seed} t${t} cap ${h.capOnP}>${h.max}`);
        if (t % 10 === 0 && yi >= 0) { const q = G.bots().list[yi]; if (!q.standOk) bad(`s${seed} t${t} yinyang off floor`); if (!Number.isFinite(q.x + q.z + q.hp)) bad(`s${seed} t${t} NaN`); }
        if (t % 10 === 0 && yi < 0 && !G.player().dead && !G.state().falling && !G.walkable(G.player().x, G.player().z, G.player().y + 0.05)) bad(`s${seed} t${t} player off floor`);
      }
      for (const q of G.bots().list) if (q.stuck > 3) bad(`s${seed} bot${q.id} stuck ${q.stuck}`);
      G.setWatch(false); G.autoPlayer(false);
    };
    for (const seed of [12345, 2, 3]) one(seed, false);
    one(4, true);
    G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); const y = G.yyState(-1); o.clean = y.orbN === 0 && y.taijiN === 0 && !y.yin && !y.yang; o.orbLife = +orbLife.toFixed(3); o.diskLife = R.tellS + 2 * R.phaseS; return o;
  });
  check('136 阴阳甲 in whole matches: on a floor, nobody stuck > 3 s, orbs and disks end on time, hunter cap every tick, the 阴阳甲 bot casts Q and W and unlocks and casts R (player 阴阳甲 autopilot reported)',
    yy136.viol.length === 0 && yy136.orbMax <= yy136.orbLife + 0.05 && yy136.diskMax <= yy136.diskLife + 0.02 && yy136.clean && yy136.casts.q > 0 && yy136.casts.w > 0 && yy136.casts.r > 0, JSON.stringify(yy136));
  // 137 Budget with 阴阳甲's effects: the heaviest royale (every suit, 7 cubs, tells) with both of the player's orbs flying and 太极 shown;
  // calls < 500, tris < 500k, no shader compile, geometry flat.
  const yy137 = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(C.BOTS.count); G.setPkitP(false); G.pickSchool(4); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      const park = () => { for (let i = 0; i < C.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); };
      park(); G.step(1); G.yyFill(-1, true, true); G.cast(2, cx, cz + 6); G.cast(0, cx - 9, cz); G.basicAttackBy(-1, 0);
      for (let n = 0; n < 30; n++) {
        park(); G.step(1); const c = G.cubs(), y = G.yyState(-1);
        if (y.orbs[0].inScene && y.orbs[1].inScene && y.taiji.inScene && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); }
    return best;
  });
  check('137 budget with 阴阳甲 effects: every suit + cubs + tells + both orbs + 太极 (calls<500, tris<500k), no shader compile, geometry flat',
    !!yy137 && yy137.calls < 500 && yy137.tris < 500000 && yy137.programs === base.programs && yy137.geoms === base.geoms, JSON.stringify(yy137));
  // ===== Batch 16 ticket 07: 农甲 · 耕者 kit (docs/SUITS.md; numbers in CONFIG.KITS.nong) =====
  // Page helper: the player plays 农甲 (school 8) against n placeholder bots at Mid; nothing else happens (decrees pushed away, bots' skills on long cooldowns).
  await g(() => { const G = __game, C = G.config; window.__ng = {
    start(n) { G.setSeed(12345); G.setPkitP(false); G.setBots(n); G.pickSchool(8); for (let i = 0; i < n; i++) G.placeholderKit(i); G.setDecNext(1e9); for (let i = 0; i < n; i++) { G.setBotHp(i, 100); for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99); } },
    hold(sec, fn) { for (let k = 0; k < Math.round(sec / C.STEP); k++) { if (fn) fn(); G.step(1); } },
    until(cond, max, fn) { let n = 0; while (n < max && !cond()) { if (fn) fn(); G.step(1); n++; } return n; },
    end() { G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); } }; });
  // 138 Passive 并耕而食 and attack: High armor, Low speed; the plough-hoe hits a dummy in melee for dmg; a grown sprout of his that he walks over is eaten:
  // heal heal and fed feedS s (his hits deal feed more, then back to normal); a seed is not eaten; a bot that walks onto a sprout tramples it and gains nothing.
  const ng138 = await g(() => {
    const G = __game, C = G.config, N = window.__ng, K = C.KITS.nong, T = K.tiller, o = {};
    N.start(1); G.setHp(1e9); G.teleport(14, -20); const park = () => G.placeBot(0, 14, -28); park(); G.step(2);
    const k0 = G.kitState(-1); o.armorK = k0.armorK; o.spd = k0.spd;
    G.nongSow(-1, 17, -20); o.seeds = G.nongState(-1).planted; G.teleport(17 + K.skills[0].spread, -20); G.step(2); o.seedEaten = G.nongState(-1).eatN; o.seedStill = G.nongState(-1).planted;
    G.teleport(14, -20); N.hold(K.skills[0].growS + 0.1, park); const s1 = G.nongState(-1); o.grown = s1.grown; o.green = s1.sprouts.filter((q) => q.st === 2).every((q) => q.green && q.inScene && q.vis);
    G.setHp(50); const sp = s1.sprouts.find((q) => q.st === 2); G.teleport(sp.x, sp.z); G.step(1); const s2 = G.nongState(-1); o.hp = s2.hp; o.eat = s2.eatN; o.feedT = +s2.feedT.toFixed(2);
    G.setHp(1e9); G.basicAttackBy(-1, 0); o.fedHit = +(100 - G.bots().list[0].hp).toFixed(2); N.hold(T.feedS + 0.1, park); o.fedEnd = G.nongState(-1).feedT; G.setBotHp(0, 100); G.basicAttackBy(-1, 0); o.plainHit = +(100 - G.bots().list[0].hp).toFixed(2);
    // A bot tramples one: it is gone, the bot gains nothing.
    G.setBotHp(0, 50); const sp2 = G.nongState(-1).sprouts.find((q) => q.st === 2); const left = G.nongState(-1).planted; G.placeBot(0, sp2.x, sp2.z); G.step(1); const s3 = G.nongState(-1);
    o.trampled = [left - s3.planted, s3.trampN, G.bots().list[0].hp];
    // Melee on a dummy.
    G.reset(); const d = G.dummies()[1]; G.teleport(d.x, d.z - 2); G.step(2); G.attack(1); N.hold(K.attack.interval * 0.5); o.dummy = 100 - G.dummies()[1].hp; G.stop();
    N.end(); return o;
  });
  check('138 农甲 passive and attack: High armor, Low speed; plough-hoe melee dmg; a grown sprout he walks over heals him and feeds him (bonus, then gone); a seed is not eaten; a bot tramples one and gains nothing',
    Math.abs(ng138.armorK - (C0.STATS.K + C0.STATS.armor.Mid) / (C0.STATS.K + C0.STATS.armor.High)) < 1e-9 && ng138.spd === C0.STATS.speed.Low && ng138.seeds === C0.KITS.nong.skills[0].seeds
    && ng138.seedEaten === 0 && ng138.seedStill === ng138.seeds && ng138.grown === ng138.seeds && ng138.green && ng138.hp === 50 + C0.KITS.nong.tiller.heal && ng138.eat === 1
    && Math.abs(ng138.feedT - C0.KITS.nong.tiller.feedS) < 0.05 && Math.abs(ng138.fedHit - C0.KITS.nong.attack.dmg * (1 + C0.KITS.nong.tiller.feed)) < 1e-9 && ng138.fedEnd === 0
    && ng138.plainHit === C0.KITS.nong.attack.dmg && ng138.trampled.join() === '1,1,50' && ng138.dummy === C0.KITS.nong.attack.dmg, JSON.stringify(ng138));
  // 139 Q 播百谷: a cast at a point drops seeds seeds (dark, low) around it within spread m and starts the cooldown; each grows into a green sprout after
  // growS s and is gone lastS s later; the pool never holds more than pool (a new sowing replaces the oldest); a seed over the void is lost.
  const ng139 = await g(() => {
    const G = __game, C = G.config, N = window.__ng, Q = C.KITS.nong.skills[0], o = { maxPlanted: 0 };
    N.start(1); G.setHp(1e9); G.teleport(14, -20); const park = () => G.placeBot(0, 14, -28); park(); G.step(2);
    o.cast = G.cast(0, 18, -20); const s0 = G.nongState(-1); o.cd = G.skills()[0] > 0; o.planted = s0.planted;
    o.ring = s0.sprouts.filter((q) => q.st === 1).every((q) => Math.abs(Math.hypot(q.x - 18, q.z + 20) - Q.spread) < 1e-6 && !q.green && q.inScene);
    const steps = N.until(() => G.nongState(-1).grown > 0, 600, park); o.growS = +((steps + 1) * C.STEP).toFixed(3);
    const lastSteps = N.until(() => G.nongState(-1).planted === 0, 3000, park); o.lastS = +((lastSteps + 1) * C.STEP).toFixed(3); o.sproutN = G.nongState(-1).sproutN;
    // Four sowings in a row (no cast: the pool rule): never more than pool.
    const firstAt = [];
    for (let k = 0; k < 4; k++) { G.nongSow(-1, 10 + k * 2, -16); G.step(1); const s = G.nongState(-1); if (s.planted > o.maxPlanted) o.maxPlanted = s.planted; if (k === 0) firstAt.push(...s.sprouts.filter((q) => q.st > 0).map((q) => q.x)); }
    const s4 = G.nongState(-1); o.after4 = s4.planted; o.oldestGone = !s4.sprouts.some((q) => q.st > 0 && Math.abs(q.x - 10) < Q.spread + 1e-6 && Math.abs(q.z + 16) < Q.spread + 1e-6); o.sproutN4 = s4.sproutN;
    // Over the void (west of the centre court, between the bridges): every seed is lost.
    G.reset(); G.teleport(-20, -2); G.step(1); const before = G.nongState(-1).planted; G.nongSow(-1, -30, -2); o.void = G.nongState(-1).planted - before;
    N.end(); return o;
  });
  check('139 农甲 Q: seeds dark at a point (spread m), cooldown; green after growS s, gone lastS s later; the pool never exceeds pool and replaces the oldest; seeds over the void are lost',
    ng139.cast && ng139.cd && ng139.planted === C0.KITS.nong.skills[0].seeds && ng139.ring && Math.abs(ng139.growS - C0.KITS.nong.skills[0].growS) < 0.05 && Math.abs(ng139.lastS - C0.KITS.nong.skills[0].lastS) < 0.05
    && ng139.sproutN === 0 && ng139.maxPlanted === C0.KITS.nong.skills[0].pool && ng139.after4 === C0.KITS.nong.skills[0].pool && ng139.oldestGone && ng139.sproutN4 === C0.KITS.nong.skills[0].pool && ng139.void === 0, JSON.stringify(ng139));
  // 140 W 并耕: the plough dashes range m and leaves a furrow (width m) along its path for furrowS s; a bot on it is slowed by slow, one beside it is not;
  // a seed on the furrow grows growK times as fast as one off it; the plough itself deals no damage.
  const ng140 = await g(() => {
    const G = __game, C = G.config, N = window.__ng, Q = C.KITS.nong.skills[0], W = C.KITS.nong.skills[1], o = {};
    // Bots in the plough's path (x 7 and 9 on its line): the plough deals no damage.
    N.start(2); G.setHp(1e9); G.teleport(5, -24); const park = () => { G.placeBot(0, 7, -22.5); G.placeBot(1, 9, -25.5); }; park(); G.step(2);
    o.cast = G.cast(1, 15, -24); N.hold(W.dashS + 0.1, park); const p = G.state(), s0 = G.nongState(-1); o.dash = +Math.hypot(p.x - 5, p.z + 24).toFixed(2); o.furrow = s0.furrow;
    o.hits = [100 - G.bots().list[0].hp, 100 - G.bots().list[1].hp];
    // He steps off the furrow (so he eats nothing); bot 0 on the furrow (on its line), bot 1 beside it.
    G.teleport(14, -20); const on = () => { G.placeBot(0, 6, -24); G.placeBot(1, 6, -24 + W.width); }; on(); G.step(2); const a = G.kitState(0), b = G.kitState(1);
    o.slow = [a.slowT > 0, b.slowT > 0, +(a.spd / C.STATS.speed.Mid).toFixed(3)];
    // Seeds at (8, -24) on the furrow's line (only those within width / 2 of it lie on it) and at (8, -17) off it.
    G.nongSow(-1, 8, -24); G.nongSow(-1, 8, -17); const onIdx = G.nongState(-1).sprouts.map((q, i) => (q.st === 1 && Math.abs(q.z + 24) <= W.width / 2 ? i : -1)).filter((i) => i >= 0); o.onN = onIdx.length;
    let fast = -1, slow = -1;
    for (let k = 0; k < 600 && (fast < 0 || slow < 0); k++) { on(); G.step(1); const s = G.nongState(-1).sprouts; if (fast < 0 && onIdx.every((i) => s[i].st === 2)) fast = k + 1; if (slow < 0 && s.some((q, i) => !onIdx.includes(i) && q.st === 2)) slow = k + 1; }
    o.grow = [+(fast * C.STEP).toFixed(2), +(slow * C.STEP).toFixed(2)];
    N.until(() => G.nongState(-1).furrow.t < 0, 600, on); o.gone = !G.nongState(-1).furrow.inScene && G.nongState(-1).furrowN === 0; o.after = G.kitState(0).slowT <= 0.2;
    N.end(); return o;
  });
  check('140 农甲 W: the plough dashes range m and lays a furrow (width) along it; a bot on it is slowed, one beside it is not; seeds on it grow growK times as fast; no damage; the furrow ends after furrowS s',
    ng140.cast && Math.abs(ng140.dash - C0.KITS.nong.skills[1].range) < 0.05 && ng140.furrow.inScene && ng140.furrow.vis && Math.abs(ng140.furrow.len - C0.KITS.nong.skills[1].range) < 0.05 && ng140.furrow.w === C0.KITS.nong.skills[1].width
    && ng140.hits.join() === '0,0' && ng140.slow[0] && !ng140.slow[1] && Math.abs(ng140.slow[2] - (1 - C0.KITS.nong.skills[1].slow)) < 1e-6
    && ng140.onN >= 1 && Math.abs(ng140.grow[0] - C0.KITS.nong.skills[0].growS / C0.KITS.nong.skills[1].growK) < 0.1 && Math.abs(ng140.grow[1] - C0.KITS.nong.skills[0].growS) < 0.1
    && ng140.gone && ng140.after, JSON.stringify(ng140));
  // 141 R 百草生机: locked under a full meter; full, every seed of his ripens, every grown sprout within radius is eaten (harvN), each heals heal and pulses
  // dmg to every target within pulseR (a bot inside takes harvN x dmg, one outside nothing); sprouts beyond radius stay (grown); the ring shows ringS s; the meter emptied
  // (then only the pulses' own damage charge, ULT.dealt per hp dealt).
  const ng141 = await g(() => {
    const G = __game, C = G.config, N = window.__ng, Q = C.KITS.nong.skills[0], R = C.KITS.nong.skills[2], o = {};
    N.start(2); G.setHp(1e9); G.teleport(12, -20); const park = () => { G.placeBot(0, 14, -20); G.placeBot(1, 12 + R.pulseR + 2, -16); }; park(); G.step(2);
    G.setCharge(-1, 50); o.locked = G.cast(2, 12, -20);
    G.nongSow(-1, 9, -18); N.hold(Q.growS + 0.1, park); G.nongSow(-1, 9, -23); G.nongSow(-1, 12 + R.radius + 3, -20);
    const s0 = G.nongState(-1); o.before = [s0.planted, s0.grown];
    G.setHp(40); G.setCharge(-1, C.ULT.full); o.cast = G.cast(2, 12, -20); const s1 = G.nongState(-1);
    o.harvN = s1.harvN; o.hp = s1.hp; o.left = [s1.planted, s1.grown]; o.bots = [100 - G.bots().list[0].hp, 100 - G.bots().list[1].hp]; o.ring = [s1.ringIn, s1.ringR]; o.ch = +G.chargeOf(-1).toFixed(6); o.ultN = G.kitState(-1).ultN;
    const steps = N.until(() => !G.nongState(-1).ringIn, 200, park); o.ringS = +((steps + 1) * C.STEP).toFixed(3);
    N.end(); return o;
  });
  check('141 农甲 R: locked without a full meter; seeds ripen, grown sprouts within radius eaten (heal each, a dmg pulse each within pulseR), those beyond stay grown; ring ringS s; meter emptied',
    ng141.locked === false && ng141.before.join() === '9,3' && ng141.cast && ng141.harvN === 6 && ng141.hp === 40 + 6 * C0.KITS.nong.skills[2].heal && ng141.left.join() === '3,3'
    && ng141.bots[0] === 6 * C0.KITS.nong.skills[2].dmg && ng141.bots[1] === 0 && ng141.ring[0] && ng141.ring[1] === C0.KITS.nong.skills[2].radius && Math.abs(ng141.ch - 6 * C0.KITS.nong.skills[2].dmg * C0.ULT.dealt) < 1e-6 && ng141.ultN === 1
    && Math.abs(ng141.ringS - C0.KITS.nong.skills[2].ringS) < 0.05, JSON.stringify(ng141));
  // 142 Plays with altars and collapses: under "Our altars are dry" an altar does not heal him but a sprout he eats still does; a field on a falling section
  // is lost with it (the roof falls at the first wave).
  const ng142 = await g(() => {
    const G = __game, C = G.config, N = window.__ng, Q = C.KITS.nong.skills[0], o = {};
    N.start(1); G.setHp(1e9); const a = G.altars()[2]; G.teleport(a.x + 4, a.z); const park = () => G.placeBot(0, 14, -28); park(); G.forceDecree('dry', null, 30); N.hold(5.1, park); o.dry = G.decree().key === 'dry' && G.decree().st === 3;
    G.nongSow(-1, a.x + 4, a.z - 3); N.hold(Q.growS + 0.1, park);
    G.teleport(a.x + 1.2, a.z); G.setHp(50); N.hold(1, park); o.altar = G.state().hp;
    const sp = G.nongState(-1).sprouts.find((q) => q.st === 2); G.teleport(sp.x, sp.z); G.step(1); o.eat = G.state().hp;
    // The roof: sown just before the first wave, the player back in the centre court; the section falls and the field is gone.
    G.reset(); G.setHp(1e9); G.setTime(C.FIRST_WAVE_S - C.COLLAPSE_WARN_S - 1); G.teleport(0, 33); G.step(1); G.nongSow(-1, 3, 33); o.roof = [G.nongState(-1).planted, G.nongState(-1).sprouts.filter((q) => q.st > 0).every((q) => q.sec === 'ROOF')];
    G.teleport(14, -20); N.hold(1 + C.COLLAPSE_WARN_S + C.COLLAPSE_FALL_S + 0.2, park); o.roofAfter = [G.nongState(-1).planted, G.nongState(-1).sproutN, G.state().sec.ROOF];
    N.end(); return o;
  });
  check('142 农甲 plays with altars and collapses: under the dry decree an altar does not heal him but an eaten sprout does; a field on a section that falls is lost with it',
    ng142.dry && ng142.altar === 50 && ng142.eat === 50 + C0.KITS.nong.tiller.heal && ng142.roof[0] === C0.KITS.nong.skills[0].seeds && ng142.roof[1] && ng142.roofAfter[0] === 0 && ng142.roofAfter[1] === 0 && ng142.roofAfter[2] >= 2, JSON.stringify(ng142));
  // 143 农甲 in the hunt: R is ready at the start (the hunt keeps the cooldown); with three grown sprouts near, R eats them and pulses a minion within pulseR
  // (3 x dmg), then its 30 s cooldown runs; the wake cleared the royale field.
  const ng143 = await g(() => {
    const G = __game, C = G.config, H = window.__h, Q = C.KITS.nong.skills[0], R = C.KITS.nong.skills[2], o = {};
    G.setPkitP(false); G.pickSchool(8); G.setBots(0); G.reset(); G.nongSow(-1, 0, -14); o.royale = G.nongState(-1).planted;
    G.startHunt(); o.wake = G.nongState(-1).planted; G.step(Math.round(C.APEX.wakeS / C.STEP) + 1); for (let i = 0; i < 3; i++) H.mute(i); G.setHp(1e9);
    G.teleport(0, -50); G.placeUnit(1, 2, -50); G.placeUnit(0, -15, -70); G.placeUnit(2, 15, -70); G.nongSow(-1, 0, -48);
    H.until(() => false, Math.round((Q.growS + 0.1) / C.STEP)); G.placeUnit(1, 2, -50); G.step(1);
    const hp0 = G.hunt().units[1].hp; o.cast = G.cast(2, 0, -50); o.harvN = G.nongState(-1).harvN; o.minion = +(hp0 - G.hunt().units[1].hp).toFixed(2); o.cd = +G.skills()[2].toFixed(2);
    G.setPkitP(true); G.pickSchool(0); G.reset(); return o;
  });
  check('143 农甲 in the hunt: the wake clears the royale field; R ready at the start; it eats the grown sprouts near and pulses a minion within pulseR; then the 30 s cooldown',
    ng143.royale === C0.KITS.nong.skills[0].seeds && ng143.wake === 0 && ng143.cast && ng143.harvN === 3 && ng143.minion === 3 * C0.KITS.nong.skills[2].dmg && ng143.cd === C0.KITS.nong.skills[2].cd, JSON.stringify(ng143));
  // 144 农甲 in whole matches: 3 seeds with the 农甲 bot (the player picks 道甲, still on the placeholder) and 1 with the player on 农甲 (autopilot), watched to the end:
  // on a floor every tick, the hunter cap holds, nobody stuck over 3 s, his pool never above pool and the planted count matches the game's, no furrow or ring
  // outlives its time; the bot sows, ploughs and harvests (R) over the 3, and eats sprouts.
  const ng144 = await g(() => {
    const G = __game, C = G.config, K = C.KITS.nong, o = { viol: [], casts: { q: 0, w: 0, r: 0 }, player: { q: 0, w: 0, r: 0 }, eat: 0, tramp: 0, decided: [], poolMax: 0, furrowMax: 0, ringMax: 0 }, bad = (x) => { if (o.viol.length < 5) o.viol.push(x); };
    const one = (seed, playerNg) => {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(!playerNg); G.pickSchool(playerNg ? 8 : 1); G.autoPlayer(true); G.setWatch(true);
      const ni = playerNg ? -1 : G.schools().suits.findIndex((q) => q.school === 'nong') - 1, cnt = playerNg ? o.player : o.casts; let last = [0, 0], ult = 0, fw = 0, rg = 0, eat = 0, tr = 0;
      if (!playerNg && G.schools().suits[ni + 1].kit !== 'nong') bad('nong bot not on its kit');
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) { o.decided.push(+r.decidedAt.toFixed(1)); break; }
        const k = G.kitState(ni), cd = k.bcd, n = G.nongState(ni);
        if (cd[0] > last[0] + 1e-9) cnt.q++; if (cd[1] > last[1] + 1e-9) cnt.w++; if (k.ultN > ult) cnt.r += k.ultN - ult; last = [cd[0], cd[1]]; ult = k.ultN;
        if (n.planted > o.poolMax) o.poolMax = n.planted; if (n.planted > K.skills[0].pool) bad(`s${seed} t${t} pool ${n.planted}`);
        if (n.sproutN !== n.planted && !playerNg) bad(`s${seed} t${t} sproutN ${n.sproutN} != planted ${n.planted}`);
        if (n.eatN > eat) eat = n.eatN; if (n.trampN > tr) tr = n.trampN;
        fw = n.furrow.inScene ? fw + C.STEP : 0; if (fw > o.furrowMax) o.furrowMax = +fw.toFixed(3); rg = n.ringIn ? rg + C.STEP : 0; if (rg > o.ringMax) o.ringMax = +rg.toFixed(3);
        const h = G.hunters(); if (h.capOnP > h.max) bad(`s${seed} t${t} cap ${h.capOnP}>${h.max}`);
        if (t % 10 === 0 && ni >= 0) { const q = G.bots().list[ni]; if (!q.standOk) bad(`s${seed} t${t} nong off floor`); if (!Number.isFinite(q.x + q.z + q.hp)) bad(`s${seed} t${t} NaN`); }
        if (t % 10 === 0 && ni < 0 && !G.player().dead && !G.state().falling && !G.walkable(G.player().x, G.player().z, G.player().y + 0.05)) bad(`s${seed} t${t} player off floor`);
      }
      for (const q of G.bots().list) if (q.stuck > 3) bad(`s${seed} bot${q.id} stuck ${q.stuck}`);
      if (!playerNg) { o.eat += eat; o.tramp += tr; }
      G.setWatch(false); G.autoPlayer(false);
    };
    for (const seed of [12345, 2, 3]) one(seed, false);
    one(4, true);
    G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); const n = G.nongState(-1); o.clean = n.sproutN === 0 && n.furrowN === 0 && n.harvRingN === 0; return o;
  });
  check('144 农甲 in whole matches: on a floor, nobody stuck > 3 s, pool <= pool, furrows and rings end on time, hunter cap every tick, the 农甲 bot sows, ploughs, harvests and eats (player 农甲 autopilot reported)',
    ng144.viol.length === 0 && ng144.poolMax <= C0.KITS.nong.skills[0].pool && ng144.furrowMax <= C0.KITS.nong.skills[1].furrowS + 0.02 && ng144.ringMax <= C0.KITS.nong.skills[2].ringS + 0.02 && ng144.clean
    && ng144.casts.q > 0 && ng144.casts.w > 0 && ng144.casts.r > 0 && ng144.eat > 0, JSON.stringify(ng144));
  // 145 Budget with 农甲's effects: the heaviest royale (every suit, 7 cubs, tells) with a full pool (seeds and grown sprouts), the furrow and the harvest ring shown;
  // calls < 500, tris < 500k, no shader compile, geometry flat.
  const ng145 = await g(() => {
    const G = __game, C = G.config, K = window.__k, Q = C.KITS.nong.skills[0], waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(C.BOTS.count); G.setPkitP(false); G.pickSchool(8); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      const park = () => { for (let i = 0; i < C.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); };
      // A far field (beyond the harvest's radius) grows; he ploughs west, harvests (the far field stays grown) and sows a new one: seeds, sprouts, furrow and ring at once.
      park(); G.step(1); G.nongSow(-1, cx + 10, cz);
      for (let n = 0; n < Math.round((Q.growS + 0.1) / C.STEP); n++) { park(); G.step(1); }
      G.cast(1, cx - 8, cz);
      for (let n = 0; n < 30; n++) {
        park(); G.step(1); const c = G.cubs();
        // After the plough has landed (its dash takes about dashS + a few steps).
        if (n === 20) { G.setCharge(-1, C.ULT.full); G.cast(2, cx, cz); }
        if (n === 21) G.nongSow(-1, G.state().x, G.state().z - 3);
        const s = G.nongState(-1);
        if (n > 21 && s.furrow.inScene && s.ringIn && s.grown >= 3 && s.planted > s.grown && (!best || c.tells.length >= best.tells)) { const r = G.render(true); best = { tells: c.tells.length, planted: s.planted, grown: s.grown, ring: s.ringIn, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); }
    return best;
  });
  check('145 budget with 农甲 effects: every suit + cubs + tells + seeds, sprouts, furrow and harvest ring (calls<500, tris<500k), no shader compile, geometry flat',
    !!ng145 && ng145.calls < 500 && ng145.tris < 500000 && ng145.programs === base.programs && ng145.geoms === base.geoms, JSON.stringify(ng145));
  // 66 Idle player: standing at the spawn doing nothing loses the royale (frozen loss with a cause) before the last collapse is over.
  const idle = await g(() => {
    const G = __game, C = G.config; G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); let t = 0;
    for (; t < 260 / C.STEP; t++) { G.step(1); if (G.royale().phase !== 'royale') break; }
    const r = G.royale(), o = { phase: r.phase, lostIn: r.lostIn, at: +(t * C.STEP).toFixed(1), cause: G.player().cause };
    G.setBots(0); G.reset(); return o;
  });
  check('66 idle player loses the royale (frozen loss, cause recorded) within 260 s', idle.phase === 'lost' && idle.lostIn === 'royale' && idle.cause !== '', JSON.stringify(idle));

  // 10 No shader compiles across collapses, hazard tells and empty altars.
  const progAfter = await g(() => __game.render(true));
  check('10 no shader compile during play', progAfter.programs === base.programs, `programs load ${base.programs}, after ${progAfter.programs}`);

  // 13 Runtime text keys: each wave voice and each zone exist.
  const tk = await g(() => {
    const G = __game, miss = [];
    G.config.WAVES.forEach((_, i) => { if (!G.text['voice_wave' + i]) miss.push('voice_wave' + i); });
    G.sections.forEach((id) => { if (!G.text['zone_' + id]) miss.push('zone_' + id); });
    return miss;
  });
  check('13 runtime text keys', tk.length === 0, tk.join(' '));

  // 14 Pause on hidden tab: game time frozen over 30 rendered frames, resumes after.
  const pause = await g(async () => {
    const G = __game, waitFrames = (n) => new Promise((r) => { const f0 = G.state().frames; const tick = () => (G.state().frames - f0 >= n ? r() : requestAnimationFrame(tick)); tick(); });
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
    document.dispatchEvent(new Event('visibilitychange'));
    const t0 = G.state().t; await waitFrames(30); const t1 = G.state().t;
    Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
    document.dispatchEvent(new Event('visibilitychange'));
    await waitFrames(30); const t2 = G.state().t;
    return { frozen: t1 === t0, resumed: t2 > t1 };
  });
  check('14 pause when tab hidden', pause.frozen && pause.resumed, JSON.stringify(pause));

  // 15 Graphics context lost and restored: no errors, renders again.
  const errBefore = errors.length;
  const ctx = await g(async () => {
    const G = __game, ext = G.loseContext();
    const waitFor = (cond) => new Promise((r) => { const tick = () => (cond() ? r() : requestAnimationFrame(tick)); tick(); });
    await waitFor(() => G.state().ctxLost);
    ext.restoreContext();
    await waitFor(() => !G.state().ctxLost);
    const f0 = G.state().frames; await waitFor(() => G.state().frames - f0 > 10);
    return G.render(true);
  });
  check('15 context lost and restored', ctx.calls > 0 && errors.length === errBefore, `calls ${ctx.calls}, new errors ${errors.slice(errBefore).join(' | ')}`);

  // 16 OpenGame resolutions: canvas follows the window, no errors.
  const sizes = [[1920, 1080], [1366, 768], [2560, 1440], [3440, 1440], [1024, 640]], bad = [];
  for (const [w, h] of sizes) {
    await page.setViewportSize({ width: w, height: h });
    await g(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
    const [cw, ch] = await g(() => __game.canvasSize());
    if (cw !== w || ch !== h) bad.push(`${w}x${h}->${cw}x${ch}`);
  }
  check('16 resize across 5 OpenGame sizes', bad.length === 0, bad.join(' '));

  check('17 no page errors in whole run', errors.length === 0, errors.slice(0, 3).join(' | '));
} catch (e) {
  check('runner', false, String(e && e.stack || e));
} finally {
  await browser.close(); server.close();
}

const pass = results.filter((r) => r.ok).length;
for (const r of results) if (!r.ok) console.log('FAIL', r.name, '::', r.detail);
console.log(`RUNTIME ${pass} of ${results.length} pass`);
if (process.argv.includes('-sims')) for (const l of SIMS) console.log('SIM', l);
if (process.argv.includes('-v')) for (const r of results) console.log(r.ok ? 'ok  ' : 'FAIL', r.name, r.detail ? ':: ' + String(r.detail).slice(0, 200) : '');
// -vv: full detail of the checks whose number is given after it (e.g. -vv 56,65).
const vv = process.argv.indexOf('-vv'); if (vv > 0) { const want = (process.argv[vv + 1] || '').split(','); for (const r of results) if (want.some((n) => r.name.startsWith(n + ' '))) console.log(r.name, '::', r.detail); }
process.exit(pass === results.length ? 0 : 1);
