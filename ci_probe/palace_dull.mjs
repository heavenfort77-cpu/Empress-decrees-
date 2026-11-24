// Burning Palace pacing and dull-time probe (integration, report only; not shipped). 12 seeds of the full palace with 8 rivals, the guard,
// 反贼, pieces, giants and the burning. Player policy: the autopilot fights while an enemy is in its room; otherwise it walks to the least
// visited neighbour room (never into a warned or fallen room or through a locked door; the core once it opens). Every 0.25 s of game time
// the player is "busy" when it was hit, fights, an enemy stands within 12 m, a tell is near, its room is warned, it is locked in, or a door
// card is shown (a choice). Prints idle %, longest idle stretch, stretches over 5 s and 10 s, run length and how the run ended.
import { open } from './harness.mjs';
const { page, errors, close } = await open();
const SEEDS = [12345, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const res = await page.evaluate(({ SEEDS }) => {
  const G = __game, C = G.config, STEP = Math.round(0.25 / C.STEP), R = 12;
  function run(seed) {
    G.setSeed(seed); G.setMode('palace'); G.setBots(8); G.reset();
    const plan = G.palPlan(), byId = {}, adj = {}, visits = {};
    for (const r of plan.rooms) { byId[r.id] = r; adj[r.id] = []; visits[r.id] = 0; }
    plan.doors.forEach((d, i) => { adj[d.a].push({ to: d.b, i }); adj[d.b].push({ to: d.a, i }); });
    let t = 0, idle = 0, runS = 0, longest = 0, over5 = 0, over10 = 0, samples = 0, lastHp = G.state().hp, goal = null, rooms = 0, last = '';
    const why = {};
    for (let n = 0; n < 330 / 0.25; n++) {
      const p = G.palace(); if (p.phase !== 'palace') break;
      const me = G.player(); if (me.dead) break;
      if (p.cur !== last) { last = p.cur; visits[p.cur] = (visits[p.cur] || 0) + 1; rooms++; goal = null; }
      const s = G.palSim(), b = G.burnState(), gs = G.guards().list, q2 = G.pieces2State(), pc = G.pieces();
      const st = {}; for (const r of b.rooms) st[r.id] = r;
      const inRoom = (x, z) => { const r = byId[p.cur]; return x >= r.x0 && x <= r.x1 && z >= r.z0 && z <= r.z1; };
      const foes = gs.filter((u) => u.alive && inRoom(u.x, u.z)).length + s.recs.filter((r) => r.st === 'live' && !r.dead && inRoom(r.x, r.z)).length
        + q2.giants.filter((g) => g.st >= 1 && g.st <= 4 && inRoom(g.x, g.z)).length;
      if (foes > 0 || s.locked.indexOf(p.cur) >= 0) { G.autoPlayer(true); goal = null; }
      else {
        G.autoPlayer(false);
        if (!goal) {
          let best = null;
          for (const e of adj[p.cur]) {
            const o = st[e.to]; if (s.doorsLocked[e.i] || o.warned || o.fallen) continue;
            const core = byId[e.to].type === 'core';
            if (core && !s.open) continue;
            const score = (core ? -100 : 0) + visits[e.to] * 10 + ((seed * 7 + e.i * 13) % 10);
            if (!best || score < best.score) best = { id: e.to, score };
          }
          if (best) { goal = best.id; G.palMoveTo(byId[goal].cx, byId[goal].cz); }
        }
      }
      G.step(STEP); t += 0.25;
      const me2 = G.player(), hp = G.state().hp, w = [];
      if (hp < lastHp - 1e-6) w.push('hit'); lastHp = hp;
      if (me2.mode === 'fight' || me2.mode === 'creature') w.push('fight');
      const near = (x, z) => Math.hypot(x - me2.x, z - me2.z) <= R;
      if (gs.some((u) => u.alive && near(u.x, u.z)) || s.recs.some((r) => r.st === 'live' && !r.dead && near(r.x, r.z)) || q2.giants.some((g) => g.st >= 1 && g.st <= 4 && near(g.x, g.z))) w.push('enemy');
      if (pc.haz.some((h) => h.state === 1 && Math.hypot(h.x - me2.x, h.z - me2.z) <= 9) || pc.merc.some((m) => m.state >= 1 && me2.x >= m.x0 - 3 && me2.x <= m.x1 + 3 && me2.z >= m.z0 - 3 && me2.z <= m.z1 + 3)
        || q2.giants.some((g) => (g.ring || g.line) && Math.hypot(g.x - me2.x, g.z - me2.z) <= 12)) w.push('tell');
      const p2 = G.palace(); if (p2.cur && st[p2.cur] && st[p2.cur].warned) w.push('burning');
      if (s.locked.indexOf(p2.cur) >= 0) w.push('locked');
      if (p2.cardShown !== 'none' && p2.cardShown !== '') w.push('choose');
      samples++;
      if (w.length) { if (runS > 5) over5++; if (runS > 10) over10++; runS = 0; for (const k of w) why[k] = (why[k] || 0) + 1; }
      else { idle++; runS += 0.25; if (runS > longest) longest = runS; }
    }
    if (runS > 5) over5++; if (runS > 10) over10++;
    G.autoPlayer(false);
    const p = G.palace(), me = G.player(), s = G.palSim();
    return { seed, t: +t.toFixed(1), end: p.phase === 'palace' ? (me.dead ? 'dead:' + me.cause : 'time') : p.phase, idlePct: Math.round(100 * idle / Math.max(1, samples)),
      longest: +longest.toFixed(1), over5, over10, rooms, rivalsOut: s.outN, falls: G.burnState().falls, why };
  }
  const out = [];
  for (const sd of SEEDS) out.push(run(sd));
  G.setBots(0); G.setMode('rumble'); G.reset();
  return out;
}, { SEEDS });
const sum = (k) => res.reduce((a, r) => a + r[k], 0);
console.log(`== palace (full, 8 rivals): idle% mean ${Math.round(sum('idlePct') / res.length)} (range ${Math.min(...res.map((r) => r.idlePct))}-${Math.max(...res.map((r) => r.idlePct))}), longest idle max ${Math.max(...res.map((r) => r.longest))} s, stretches >5 s total ${sum('over5')}, >10 s total ${sum('over10')}, run length ${Math.min(...res.map((r) => r.t))}-${Math.max(...res.map((r) => r.t))} s`);
for (const r of res) console.log(`${r.seed}: t ${r.t} end ${r.end} idle ${r.idlePct}% longest ${r.longest}s >5s ${r.over5} >10s ${r.over10} rooms ${r.rooms} rivalsOut ${r.rivalsOut} falls ${r.falls} ${JSON.stringify(r.why)}`);
console.log('errors ' + errors.length + (errors.length ? ' ' + errors.slice(0, 2).join(' | ') : ''));
await close();
