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
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0`;

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
      const [rx, ry] = c(btns[3]); ev(btns[3], 'pointerdown', rx, ry, 13); ev(window, 'pointermove', rx, ry - 40, 13); ev(window, 'pointerup', rx, ry - 40, 13);
      return { bar: btns.length, mini: G.miniSize()[0], touch: G.ui().touch, tapHp, cancelShown, cdW, hpAfterCancel, cdR: G.skills()[2], pend: G.pending() };
    });
    check('32 phone: MLBB buttons, tap auto-aim hits, cancel zone, drag aim casts', res.touch && res.bar === 4 && res.mini === 140 && res.tapHp === 75
      && res.cancelShown && res.cdW === 0 && res.hpAfterCancel === 75 && res.cdR > 0 && res.pend && perr.length === 0, JSON.stringify(res) + ' ' + perr.join(' | '));
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
  // 48 Plate reward: plate flies to the player, 45 s buff in one of two slots, ultimate cooldown cut, Stalker plate = bleed on hits, Howler plate = speed, oldest slot replaced, buff runs out.
  const pl = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {}, fly = Math.round(C.PLATE.flyS / C.STEP) + 2; G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
    let c = G.cubs(); const a = c.list.findIndex((u) => u.alive), ua = c.list[a]; K.mute(a);
    G.teleport(ua.x + 4, ua.z + 3); G.step(2); G.cast(2, ua.x + 40, ua.z + 3); const cd0 = G.cubs().ultCd;
    G.hitCub(a, 1e6); c = G.cubs(); o.dead = !c.list[a].alive && !c.list[a].inScene && !c.list[a].tellIn; o.flying = c.list[a].plate; o.takenBefore = c.taken;
    G.step(fly); c = G.cubs(); o.slot0 = c.plates[0].kind; o.t0 = c.plates[0].t; o.status = c.status; o.rule = c.rule; o.plateGone = !c.list[a].plate; o.taken = c.taken;
    o.cut = cd0 - c.ultCd - fly * C.STEP; o.wantCut = C.PLATE.ultCut * C.SKILLS[2].cd;
    K.sp(C.KENNEL.intervalS); c = G.cubs(); o.expired = c.plates.every((p) => p.kind === '' && p.t === 0) && c.status === '';
    const h = c.list.findIndex((u) => u.alive && u.kind === 'howler'), uh = c.list[h]; K.mute(h);
    G.teleport(uh.x - 4, uh.z); G.step(2); G.givePlate('stalker'); G.cast(0, uh.x, uh.z); const hp1 = G.cubs().list[h].hp; o.lineHit = uh.hp - hp1; o.bleedOn = G.cubs().list[h].bleed > 0;
    G.step(60); o.bleedLoss = hp1 - G.cubs().list[h].hp; o.wantBleed = C.PLATE.bleedDps;
    G.givePlate('howler'); G.stop(); const z0 = G.state().z; G.setMove(0, 1); G.step(30); G.clearMove(); o.fastDz = G.state().z - z0; o.wantDz = C.PLAYER_SPEED * (1 + C.PLATE.speed) * 0.5;
    G.hitCub(h, 1e6); G.step(fly); c = G.cubs(); o.slots = c.plates.map((p) => p.kind).join(); o.taken2 = c.taken; o.status2 = c.status;
    return o;
  });
  check('48 plate: flight shown, buff slot, ultimate cooldown cut, bleed on hits, speed, oldest slot replaced, expiry', pl.dead && pl.flying && pl.takenBefore === 0 && pl.slot0 === 'stalker' && pl.t0 > 44 && /Stalker plate 4\ds/.test(pl.status)
    && /Stalker plate/.test(pl.rule) && pl.plateGone && pl.taken === 1 && Math.abs(pl.cut - pl.wantCut) < 0.05 && pl.expired && pl.lineHit === 25 && pl.bleedOn && Math.abs(pl.bleedLoss - pl.wantBleed) < 0.2
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
    G.reset(); G.teleport(d.x, d.z - 5); G.step(2); G.cast(2, d.x + 40, d.z - 5); const cd0 = G.neutrals().ultCd; give(0, 'ult', 1.5); o.ult = cd0 - G.neutrals().ultCd; o.wantUlt = B.ult.v * 1.5 * C.SKILLS[2].cd; o.ultRule = G.neutrals().rule;
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
  check('54 boons: ultimate cut, heal, power, regen, vision, speed at the drawn size; under the cap; they end; HUD text', Math.abs(bo.ult - bo.wantUlt) < 0.05 && /cooldown/.test(bo.ultRule) && Math.abs(bo.heal - bo.wantHeal) < 0.01
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
  // 56 Nine bots spawn at the other spawns and roam 230 s (player parked in the core hall): every tick their centre stays on a floor or they are airborne,
  // never stuck over 3 s, at most one path search per step, seen only inside the player's vision, every bot that is out has a cause. navSearch timing is reported (not gated: wall clock).
  const bw = await g(() => {
    const G = __game, C = G.config, viol = [], bad = (s) => { if (viol.length < 5) viol.push(s); };
    G.setSeed(12345); G.setBots(9); G.reset();
    const b0 = G.bots(), spawns = new Set(b0.list.map((q) => q.spawn));
    const o = { n: b0.list.length, distinct: spawns.size === 9 && !spawns.has(C.PLAYER_SPAWN), inScene: b0.list.every((q) => q.inScene && !q.dead && q.hp === 100) };
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
  check('56 bots: 9 at the other spawns, roam 230 s: on a floor every tick, never stuck > 3 s, <= 1 path search per step, seen only in vision, every out has a cause',
    bw.n === 9 && bw.distinct && bw.inScene && bw.viol.length === 0 && bw.stuck <= 3 && bw.navPeak === 1 && bw.noCause === 0, JSON.stringify(bw));
  // 57 Budget with 10 suits, 7 cubs and their tells in view (default tier): under 500 calls / 0.5M tris, no new shader program, geometry count flat.
  const bb = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(9); G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      for (let n = 0; n < 600; n++) {
        for (let i = 0; i < 9; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5);
        G.step(1); const c = G.cubs();
        if (!best || c.tells.length > best.tells) { const r = G.render(true); best = { tells: c.tells.length, bots: G.bots().list.filter((q) => q.vis).length, cubs: c.list.filter((u) => u.alive && u.seen).length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setBots(0); G.reset(); }
    return best;
  });
  check('57 budget: 10 suits + 7 cubs + tells drawn (calls<500, tris<500k), no shader compile, geometry flat', bb.bots === 9 && bb.cubs === 7 && bb.tells >= 3 && bb.calls < 500 && bb.tris < 500000
    && bb.programs === base.programs && bb.geoms === base.geoms, JSON.stringify(bb));
  // 58 Three runs with bots in the same page: bots respawn full, memory and shaders flat.
  const bm = await g(() => {
    const G = __game, K = window.__k, out = [];
    G.setBots(9);
    for (let r = 0; r < 3; r++) { G.setSeed(100 + r); G.reset(); const b = G.bots(); const fresh = b.list.every((q) => !q.dead && q.hp === 100 && q.inScene && q.plates === 0); K.sp(40); const m = G.render(true); out.push({ fresh, geoms: m.geoms, texs: m.texs, programs: m.programs }); }
    G.setBots(0); G.reset(); return out;
  });
  check('58 new run x3 with bots: fresh bots, memory and shaders flat', bm.every((m) => m.fresh && m.geoms === base.geoms && m.texs === base.texs && m.programs === base.programs), JSON.stringify(bm));
  // 59 Target rule (owner, 23 Nov): a bot answers the suit that hit it; once it sees the player it switches to the player, keeps it while seen, and lets go when the player is out of sight.
  // Batch 10: with the hunter slot (maxHunters 1) either bot may take the slot first, so this check of the switch itself opens a second slot and restores it.
  const rt = await g(() => {
    const G = __game, K = window.__k, o = {}, mh = G.config.BOT.maxHunters; G.config.BOT.maxHunters = 2;
    G.setSeed(12345); G.setBots(2); G.reset(); G.teleport(0, -50); G.setHp(1e9);
    G.placeBot(0, 0, 10); G.placeBot(1, 2.5, 10); G.hitBy(1, 0, 1); K.sp(0.5); o.first = G.bots().list[0].tgt;
    G.teleport(0, 16); K.sp(0.5); o.onSight = G.bots().list[0].tgt;
    let kept = true; for (let n = 0; n < 8; n++) { K.sp(0.25); if (G.bots().list[0].tgt !== 0) kept = false; } o.kept = kept;
    G.teleport(0, -50); K.sp(0.6); o.away = G.bots().list[0].tgt;
    G.config.BOT.maxHunters = mh; G.setBots(0); G.reset(); return o;
  });
  check('59 bot target: answers its attacker, switches to the player on sight, keeps the player while seen, lets go out of sight', rt.first === 2 && rt.onSight === 0 && rt.kept && rt.away !== 0, JSON.stringify(rt));
  const C0 = await g(() => __game.config);
  // 60 Bots take plates and boons (owner, 23 Nov): a cub broken by a bot sends its plate to that bot (buff slot, ultimate cut); a buff creature's boon goes to its last hitter; the player gets neither.
  const bp = await g(() => {
    const G = __game, C = G.config, K = window.__k, o = {};
    G.setSeed(12345); G.setBots(1); G.reset(); G.teleport(0, -50); K.sp(C.KENNEL.firstS + 0.1);
    const ci = G.cubs().list.findIndex((u) => u.alive); G.placeBot(0, G.camps[0][0] + 9, G.camps[0][1]);
    G.setBotCd(0, 2, C.SKILLS[2].cd); const ultBefore = G.bots().list[0].ult; G.hitCubBy(ci, 0, 1e4); K.sp(C.PLATE.flyS + 0.1);
    let b = G.bots().list[0]; o.plates = b.plates; o.slot = b.pk[0]; o.ultCut = +(ultBefore - b.ult).toFixed(2); o.playerPlates = G.player().plates;
    G.forceNeutral(0, 0, 'power', 1); G.hitNeutralBy(0, 0, 1e4); b = G.bots().list[0]; o.boons = b.boons; o.power = b.bT[0] > 0; o.playerBoons = G.player().boons;
    G.setBots(0); G.reset(); return o;
  });
  check('60 bots take plates and boons: plate to the bot that broke the cub (slot, ultimate cut), boon to the last hitter, none to the player', bp.plates === 1 && bp.slot !== '' && Math.abs(bp.ultCut - C0.PLATE.ultCut * C0.SKILLS[2].cd - C0.PLATE.flyS - 0.1) < 0.1
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
    G.setSeed(12345); G.setBots(9); G.reset(); let r = G.royale();
    o.btnHidden = r.btn === 'none'; G.huntButton(); dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyH' })); o.hNoop = G.royale().phase === 'royale';
    G.hitBy(0, -1, 1e4); r = G.royale(); o.lost = r.phase === 'lost' && r.lostIn === 'royale'; o.place = r.rule; o.voice = r.voice; o.btn = r.btn; o.btnText = r.btnText; o.cause = G.player().cause;
    const t0 = r.t, b0 = JSON.stringify(G.bots().list.map((q) => [q.x, q.z])); G.step(60); o.frozen = G.royale().t === t0 && JSON.stringify(G.bots().list.map((q) => [q.x, q.z])) === b0;
    G.huntButton(); const b1 = G.bots(); o.newRun = G.royale().phase === 'royale' && b1.list.every((q) => !q.dead && q.inScene) && !G.state().dead && G.state().hp === 100;
    G.teleport(0, 40.5); G.knock(0, 14); K.sp(C.RESPAWN_S + 1); r = G.royale(); o.fall = r.phase === 'lost' && G.player().cause === 'fall';
    G.reset(); for (let i = 0; i < 9; i++) G.hitBot(i, 1e4); G.step(1); r = G.royale(); const h = G.hunt();
    o.hunt = r.phase === 'wake' && !h.statue && h.seal && G.bots().list.every((q) => q.dead && !q.inScene);
    G.setBots(0); G.reset(); return o;
  });
  check('64 royale end: H off in a match, broken player = frozen loss with place and New run, New run restores bots, void fall = loss, last suit standing starts the hunt',
    re.btnHidden && re.hNoop && re.lost && /Place 10 of 10/.test(re.place) && re.voice.length > 0 && re.btn === 'block' && re.btnText === 'New run' && re.cause === 'hit' && re.frozen && re.newRun && re.fall && re.hunt, JSON.stringify(re));
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
      G.setSeed(seed); G.setBots(9); G.reset(); G.autoPlayer(true); G.setWatch(true);
      let prevAlive = 10, t = 0, prevL = -1; const leadS = {};
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
  check('65 whole matches x6: decided in 165-255 s, 0 broken invariants, every out has a cause, bots take plates and boons, no spawn wins more than 3 of 6',
    ms.out.every((m) => m.decided >= 165 && m.decided <= 255 && m.nocause === 0) && ms.viol.length === 0 && ms.plates > 0 && ms.boons > 0 && Math.max(...Object.values(ms.wins6)) <= 3, JSON.stringify(ms));
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
  // breaking a non-leader pays nothing; breaking the leader in force resets the breaker's ultimate and ends it; a broken leader with no breaker pays nobody;
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
    G.setBotCd(1, 2, 30); G.hitBy(1, 0, 1e12); hold(); G.step(1); const c = G.leader(); o.paid = { paid: c.paid, to: c.paidTo, ult: G.ultOf(1), dec: c.dec, why: c.endWhy, leader: c.id };
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
    && bt.paid.paid === 1 && bt.paid.to === 2 && bt.paid.ult === 0 && bt.paid.dec === 0 && bt.paid.why === 'out' && bt.paid.leader === 2 && bt.overlap === 0
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
  // 74 Budget with the crown: heaviest royale (10 suits, 7 cubs, tells) plus the crown on a seen bot leader; no shader compile, geometry flat.
  const bc = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(9); G.reset(); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9); G.plateTo(4, 'stalker');
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      for (let n = 0; n < 600; n++) {
        for (let i = 0; i < 9; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5);
        G.step(1); const c = G.cubs(), l = G.leader();
        if (l.crownShown && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, crown: l.crownShown, cubs: c.list.filter((u) => u.alive && u.seen).length, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setBots(0); G.reset(); }
    return best;
  });
  check('74 budget with the crown: 10 suits + cubs + tells + crown (calls<500, tris<500k), no shader compile, geometry flat',
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
  // ultimates 2x (player and bot, clamped at 0); silence (no new cast on a bridge with the note, status and button look; a cast released before still lands;
  // a bot on a bridge only attacks); heights (no break in the warning, break with slow + mark, again every 2 s, none on low ground; slope top counts, its foot does not;
  // a bot on the terrace at the warning leaves in time); no dash (zone tinted gold and outlined on the minimap, named in her line; a dash in the zone breaks it, outside not).
  const dfx = await g(() => {
    const G = __game, C = G.config, D = C.DECREES, H = window.__d, o = {};
    H.start(); const a = G.altars()[2]; G.teleport(a.x + 1.2, a.z); G.setHp(50);
    G.forceDecree('dry', null, 4); H.hold(0.5, H.park); o.warnHeal = G.state().hp > 50;
    G.teleport(0, -14); H.hold(4.6, H.park); G.teleport(a.x + 1.2, a.z); G.setHp(50); H.hold(2, H.park);
    o.dryHeal = +(G.state().hp - 50).toFixed(3); o.dryLook = G.altars().every((x) => !x.on); o.hud = G.decree().hud; o.hudShown = G.decree().hudShown;
    H.hold(2.2, H.park); o.endSt = G.decree().st; G.setHp(50); H.hold(1, H.park); o.afterHeal = G.state().hp > 50; o.afterLook = G.altars()[2].on; o.hudGone = G.decree().hudShown;
    H.start(); G.teleport(0, -14); G.cast(2, 0, -5); G.setBotCd(0, 2, 30); H.hold(5, H.park); const p0 = G.ultOf(-1), b0 = G.ultOf(0);
    H.hold(0.001, H.park); G.forceDecree('ult2x', null, 10); H.hold(5, H.park); const p1 = G.ultOf(-1), b1 = G.ultOf(0); H.hold(5, H.park); const p2 = G.ultOf(-1), b2 = G.ultOf(0);
    o.ultWarn = +((p0 - p1) / 5).toFixed(2); o.ultOn = +((p1 - p2) / 5).toFixed(2); o.botOn = +((b1 - b2) / 5).toFixed(2); G.setBotCd(0, 2, 0.5); H.hold(1, H.park); o.botClamp = G.ultOf(0);
    H.start(); G.forceDecree('silence', null, 30); G.teleport(0, -24); H.hold(5.1, H.park);
    const nearB = () => G.placeBot(0, -18, 6); G.setBotHp(0, 1000); G.teleport(-15, 6); H.hold(0.1, nearB);
    o.castOff = G.cast(2, -18, 6); G.teleport(-24, 6); H.hold(1.2, nearB); o.released = 1000 - G.bots().list[0].hp; G.setBotHp(0, 1e9); G.teleport(-30, 6); G.step(1); o.castOn = G.cast(0, -30, -2);
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
    && Math.abs(dfx.ultWarn - 1) < 0.05 && Math.abs(dfx.ultOn - 2) < 0.05 && Math.abs(dfx.botOn - 2) < 0.05 && dfx.botClamp === 0
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
      G.setSeed(seed); G.setBots(9); G.reset(); G.autoPlayer(true, true); G.setWatch(true);
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
    for (let r = 0; r < 3; r++) { G.setSeed(40 + r); G.setBots(9); G.reset(); d = G.decree(); o.runs.push({ st: d.st, n: d.n, next: d.next, brk: d.brkP + d.brkB, log: d.log.length, marks: G.suits().filter((s) => s.markT > 0).length, hud: d.hudShown }); }
    H.start(); G.forceDecree('nodash', 'W2', 10); o.voice = G.decree().voice; H.hold(5.2, H.park); o.hud = G.decree().hud;
    o.keys = G.decreeKeys(); G.setBots(0); G.reset(); return o;
  });
  check('80 wake ends the decree, tint, marks and HUD; none in the hunt; new run x3 resets slot, bags and counts; zone named; text keys',
    dw.dryOn && dw.wake.st === 0 && dw.wake.zone === null && !dw.wake.tint && dw.wake.marks === 0 && dw.wake.hud === 'none' && dw.wake.altars && dw.hunt.st === 0 && dw.hunt.n === 0
    && dw.runs.every((r) => r.st === 0 && r.n === 0 && C0.DECREES.first.includes(r.next) && r.brk === 0 && r.log === 0 && r.marks === 0 && r.hud === 'none')
    && /West courtyard, south/.test(dw.voice) && /West courtyard, south/.test(dw.hud) && dw.keys.length === 0, JSON.stringify(dw));
  // 81 Budget with every mark and the crown: heaviest royale (10 suits, 7 cubs, tells) with all 10 markers shown, the crown and the gold zone tint; no shader compile, geometry flat.
  const bk = await g(() => {
    const G = __game, C = G.config, K = window.__k, waves = C.KENNEL.waves; let best = null;
    try {
      C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
      G.setSeed(12345); G.setBots(9); G.reset(); G.setDecNext(1e9); K.sp(C.KENNEL.firstS + 0.1); G.setHp(1e9); G.plateTo(4, 'stalker'); G.forceDecree('nodash', 'W1', 60);
      const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
      for (let n = 0; n < 600; n++) {
        for (let i = 0; i < 9; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5);
        for (let i = -1; i < 9; i++) if (G.suits()[i + 1].markT < 0.5) G.breakBy(i);
        G.step(1); const c = G.cubs(), l = G.leader(), marks = G.suits().filter((s) => s.marker).length;
        if (l.crownShown && marks === 10 && G.zoneTinted('W1') && (!best || c.tells.length > best.tells)) { const r = G.render(true); best = { tells: c.tells.length, marks, crown: l.crownShown, calls: r.calls, tris: r.tris, programs: r.programs, geoms: r.geoms }; }
      }
    } finally { C.KENNEL.waves = waves; G.setBots(0); G.reset(); }
    return best;
  });
  check('81 budget with 10 marks, the crown and the zone tint: 10 suits + cubs + tells (calls<500, tris<500k), no shader compile, geometry flat',
    !!bk && bk.marks === 10 && bk.crown && bk.tells >= 3 && bk.calls < 500 && bk.tris < 500000 && bk.programs === base.programs && bk.geoms === base.geoms, JSON.stringify(bk));
  // 82 Replays (batch 12 fix): a seed played twice in a row in the same page gives the same match (decided time, player out, decree log, breaks).
  // Found in batch 12: an ending heights decree bumped warnGen after the restart and the autopilot kept brain fields, so run 1 and run 2 of one seed differed.
  const rp = await g(() => {
    const G = __game, C = G.config, out = [];
    for (let r = 0; r < 2; r++) {
      G.setSeed(7); G.setBots(9); G.reset(); G.autoPlayer(true); G.setWatch(true); out.push(G.startState());
      for (let t = 0; t < 300 / C.STEP; t++) { G.step(1); if (G.royale().decidedAt >= 0) break; }
      const p = G.player(), d = G.decree(); out.push(JSON.stringify([+G.royale().decidedAt.toFixed(2), p.dead ? +p.diedAt.toFixed(2) : -1, d.log.map((v) => +v.toFixed(2)), d.brkP, d.brkB]));
      G.setWatch(false); G.autoPlayer(false);
    }
    G.setBots(0); G.reset(); return out;
  });
  check('82 replay: a run starts from the same state and one seed played twice in a row gives the same match', rp[0] === rp[2] && rp[1] === rp[3], rp.join(' vs '));
  // 66 Idle player: standing at the spawn doing nothing loses the royale (frozen loss with a cause) before the last collapse is over.
  const idle = await g(() => {
    const G = __game, C = G.config; G.setSeed(12345); G.setBots(9); G.reset(); let t = 0;
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
