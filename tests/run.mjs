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
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium`;

const results = [];
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
    return { gapFell: fell, gapRespawn: a.zone, railFell: fell2, railZone: b.zone };
  }, K);
  check('20 knockback: broken gap drops into void, rail holds', kb.gapFell && kb.gapRespawn === 'C1' && !kb.railFell && kb.railZone === 'ROOF', JSON.stringify(kb));
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
    const w = G.cast(1, d.x, d.z), afterW = hp();
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
    const b = G.aimKey(1, nx, ny); G.releaseKey(); const hpW = G.dummies()[1].hp;
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
        } else {
          G.clearMove();
          let ti = -1; for (const i of order) if (h.units[i].alive) { ti = i; break; }
          const u = h.units[ti], d = Math.hypot(u.x - p.x, u.z - p.z);
          if (u.seen) {
            G.attackUnit(ti);
            const cd = G.skills();
            for (let s = 0; s < 3; s++) if (cd[s] === 0 && d <= C.SKILLS[s].range && !(s === 2 && G.pending())) G.cast(s, u.x, u.z);
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
if (process.argv.includes('-v')) for (const r of results) console.log(r.ok ? 'ok  ' : 'FAIL', r.name, r.detail ? ':: ' + String(r.detail).slice(0, 200) : '');
process.exit(pass === results.length ? 0 : 1);
