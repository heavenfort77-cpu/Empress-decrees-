// Dull-time probe (audit, report only). For 12 seeds of the royale (autopilot and kennel autopilot) and the hunt,
// sample every 0.25 s game time whether the player has "something to do". Prints a compact table.
import { open } from './harness.mjs';
const { page, errors, close } = await open();
const SEEDS = [12345, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
const res = await page.evaluate(({ SEEDS }) => {
  const G = __game, C = G.config, STEP = Math.round(0.25 / C.STEP), R = 12;
  const near = (p, x, z, y, r) => Math.hypot(x - p.x, z - p.z) <= r && Math.abs((y || 0) - p.y) < 3;
  function busy(p, lastHp, hp) {
    const why = [];
    if (hp < lastHp - 1e-6) why.push('hit');
    if (p.mode === 'fight' || p.mode === 'creature') why.push('fight');
    for (const b of G.bots().list) if (!b.dead && near(p, b.x, b.z, b.y, R)) { why.push('suit'); break; }
    for (const u of G.cubs().list) if (u.alive && near(p, u.x, u.z, u.y, R)) { why.push('cub'); break; }
    for (const u of G.neutrals().list) if (u.alive && near(p, u.x, u.z, u.y, R)) { why.push('creature'); break; }
    for (const h of G.hazards()) if (h.state === 1 && near(p, h.x, h.z, h.y, 9)) { why.push('tell'); break; }
    for (const t of G.cubs().tells) if (near(p, t.x, t.z, p.y, R)) { why.push('tell'); break; }
    const s = G.state(); if (s.zone && s.sec[s.zone] === 1) why.push('collapse');
    const d = G.decree();
    if (d.st === 2) why.push('decree-warning');
    if (d.st === 3) {
      const me = G.suits()[0];
      if ((d.key === 'heights' && me.hi) || (d.key === 'nodash' && d.zone === s.zone) || (d.key === 'silence' && /Silenced/.test(d.status))) why.push('decree');
    }
    return why;
  }
  function royale(seed, kennel) {
    G.setSeed(seed); G.setBots(8); G.reset(); G.autoPlayer(true, kennel); G.setWatch(false);
    let t = 0, idle = 0, run = 0, longest = 0, over10 = 0, first = -1, samples = 0, lastHp = G.state().hp; const reasons = {};
    for (let n = 0; n < 300 / 0.25; n++) {
      G.step(STEP); t += 0.25;
      const r = G.royale(), p = G.player(); if (p.dead || r.phase !== 'royale') break;
      const hp = G.state().hp, why = busy(p, lastHp, hp); lastHp = hp; samples++;
      if (why.length) { if (first < 0 && why.some((w) => w !== 'decree-warning' && w !== 'collapse' && w !== 'decree')) first = t; if (run > 10) over10++; run = 0; for (const w of why) reasons[w] = (reasons[w] || 0) + 1; }
      else { idle++; run += 0.25; if (run > longest) longest = run; }
      if (r.decidedAt >= 0) break;
    }
    if (run > 10) over10++;
    G.autoPlayer(false);
    return { seed, t: +t.toFixed(1), idlePct: Math.round(100 * idle / Math.max(1, samples)), longest: +longest.toFixed(1), over10, first: +first.toFixed(1), out: G.player().dead ? 'out' : 'alive', reasons };
  }
  function hunt(seed) {
    G.setSeed(seed); G.setBots(0); G.reset(); G.setHp(1e9); G.startHunt();
    let idle = 0, samples = 0, run = 0, longest = 0;
    for (let n = 0; n < 60 / 0.25; n++) {
      G.step(STEP); const h = G.hunt(); if (h.phase !== 'hunt' && h.phase !== 'wake') break;
      if (h.phase === 'wake') continue;
      samples++;
      const busyNow = h.units.some((u) => u.alive && Math.hypot(u.x - h.p.x, u.z - h.p.z) <= R) || h.tells.length > 0;
      if (busyNow) run = 0; else { idle++; run += 0.25; if (run > longest) longest = run; }
    }
    return { seed, idlePct: Math.round(100 * idle / Math.max(1, samples)), longest: +longest.toFixed(1) };
  }
  const out = { auto: [], kennel: [], hunt: [] };
  for (const s of SEEDS) out.auto.push(royale(s, false));
  for (const s of SEEDS) out.kennel.push(royale(s, true));
  for (const s of SEEDS.slice(0, 4)) out.hunt.push(hunt(s));
  G.setBots(0); G.reset();
  return out;
}, { SEEDS });
const sum = (rows, k) => rows.reduce((a, r) => a + r[k], 0);
for (const mode of ['auto', 'kennel']) {
  const rows = res[mode];
  console.log(`== ${mode}: idle% mean ${Math.round(sum(rows, 'idlePct') / rows.length)}, longest max ${Math.max(...rows.map((r) => r.longest))} s, stretches>10s total ${sum(rows, 'over10')}, first contact mean ${(sum(rows, 'first') / rows.length).toFixed(1)} s`);
  for (const r of rows) console.log(`${r.seed}: t ${r.t} ${r.out} idle ${r.idlePct}% longest ${r.longest}s >10s ${r.over10} first ${r.first}s ${JSON.stringify(r.reasons)}`);
}
console.log('== hunt (player standing, 60 s): ' + res.hunt.map((r) => `${r.seed}: idle ${r.idlePct}% longest ${r.longest}s`).join('; '));
console.log('errors ' + errors.length + (errors.length ? ' ' + errors.slice(0, 2).join(' | ') : ''));
await close();
