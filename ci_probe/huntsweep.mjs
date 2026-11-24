// Per-school hunt sweep (batch 16 close-out): check 42's sweep bot (reaction 99 = never dodges, 0.3 s, 0.15 s; kill orders demon-first, stalker-first,
// howler-first; same always-true checks) with the player on each school's kit, plus the placeholder. The bot dashes out of seen tells with the school's
// escape skill (escapeOf) and casts its other skills at its target in their kit range. Flags: TRIVIAL = never loses, IMPOSSIBLE = never wins at 0.15 s.
// Usage: node ci_probe/huntsweep.mjs [entries, e.g. placeholder,ru,fa]
import { open } from './harness.mjs';
const only = (process.argv[2] || '').split(',').filter(Boolean);
const { page, errors, close } = await open();
const res = await page.evaluate((only) => {
  const G = __game, C = G.config, SC = C.SCHOOLS, out = [];
  const start = () => { G.reset(); G.startHunt(); G.step(Math.round(C.APEX.wakeS / C.STEP) + 1); };
  const runBot = (react, order, ranges, esc) => {
    start();
    const viol = [], bad = (s) => { if (viol.length < 3) viol.push(s); };
    let steps = 0, lastX = 0, lastZ = 0, turn = 0, pHp = C.MAX_HP, pDmg = 0; const max = 300 / C.STEP;
    while (steps < max) {
      const h = G.hunt(), p = h.p; if (h.phase !== 'hunt') break;
      // Every health drop this step is matched by hit or bleed damage this step (heals from a kit raise health and are not a drop).
      const dmg = h.hitDmg + h.bleedDmg; if (pHp - p.hp > dmg - pDmg + 1e-6) bad('hp loss without a hit t=' + h.t.toFixed(1)); pHp = p.hp; pDmg = dmg;
      if (h.hits > 0 && h.minTell < 0.4 - 1e-9) bad('tell under 0.4 s');
      if (p.z > h.gateZ + 1e-6) bad('player past the gate');
      for (const u of h.units) { if (!u.standOk) bad(u.kind + ' off the floor'); if (!Number.isFinite(u.x + u.z + u.hp)) bad('NaN'); }
      for (const t of h.tells) if (!t.shown) bad('tell not shown');
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
        if (esc >= 0 && G.skills()[esc] === 0) G.cast(esc, p.x + mx / l * 4, p.z + mz / l * 4);
      } else {
        G.clearMove();
        let ti = -1; for (const i of order) if (h.units[i].alive) { ti = i; break; }
        const u = h.units[ti], d = Math.hypot(u.x - p.x, u.z - p.z);
        if (u.seen) {
          G.attackUnit(ti);
          const cd = G.skills();
          for (let s = 0; s < 3; s++) if (s !== esc && cd[s] === 0 && d <= ranges[s] && !(s === 2 && G.pending())) G.cast(s, u.x, u.z);
        } else G.setMove((u.x - p.x) / d, (u.z - p.z) / d);
      }
      lastX = p.x; lastZ = p.z; G.step(1); steps++;
    }
    G.clearMove(); const h = G.hunt();
    return { react, order: order.join(''), phase: h.phase, t: Math.round(h.t), demon: Math.round(h.units[0].hp), viol };
  };
  const entries = ['placeholder'].concat(SC);
  for (const e of entries) {
    if (only.length && !only.includes(e)) continue;
    const ph = e === 'placeholder', kit = ph ? null : C.KITS[e], built = ph || !!(kit && kit.built);
    G.setBots(0); G.setPkitP(ph); G.setSchool(ph ? 0 : SC.indexOf(e));
    const sk = ph || !built ? C.SKILLS : kit.skills, ranges = sk.map((q) => (q.range > 0 ? q.range : 3));
    const esc = ph || !built ? 1 : G.escapeOf(e);
    const runs = [];
    for (const react of [99, 0.3, 0.15]) for (const order of [[0, 1, 2], [1, 2, 0], [2, 1, 0]]) runs.push(runBot(react, order, ranges, esc));
    out.push({ e, built, esc, runs });
  }
  G.setPkitP(true); G.setSchool(0); G.setBots(0); G.reset();
  return out;
}, only);
for (const r of res) {
  const lv = (x) => r.runs.filter((o) => o.react === x), w = (x) => lv(x).filter((o) => o.phase === 'won').length;
  const flags = [];
  if (r.runs.every((o) => o.phase === 'won')) flags.push('TRIVIAL');
  if (w(0.15) === 0) flags.push('IMPOSSIBLE');
  if (lv(99).some((o) => o.phase === 'won')) flags.push('never-dodge wins');
  const v = r.runs.flatMap((o) => o.viol);
  console.log(`${r.e}${r.built ? '' : ' (not built)'} esc=${r.esc}: wins 99:${w(99)}/3 0.3:${w(0.3)}/3 0.15:${w(0.15)}/3 ${flags.join(' ')}${v.length ? ' VIOL ' + v.slice(0, 2).join(';') : ''} | ${r.runs.map((o) => `${o.react}/${o.order}:${o.phase[0]}${o.t}s d${o.demon}`).join(' ')}`);
}
console.log('ERRORS ' + errors.length + (errors.length ? ' ' + errors.slice(0, 2).join(' | ') : ''));
await close();
