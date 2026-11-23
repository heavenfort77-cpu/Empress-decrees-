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
    await ctx.close();
  }

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
