// Ticket 10 probe (report only, deleted before commit): the hunt sweep of check 42 with the player on 杂甲 (school 5): dodges seen tells with W (blink),
// Q at the target in range, R (the stored skill) at the target when one is stored. 3 reaction levels x 3 kill orders; prints one line per run.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': extname(p) === '.html' ? 'text/html' : 'text/javascript' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0`);
await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
const out = await page.evaluate(() => {
  const G = __game, C = G.config, K = C.KITS.za;
  const runBot = ({ react, order, maxS }) => {
    G.setPkitP(false); G.setSchool(5); G.reset(); G.startHunt(); G.step(Math.round(C.APEX.wakeS / C.STEP) + 1);
    const viol = [], bad = (s) => { if (viol.length < 5) viol.push(s); };
    let steps = 0, lastX = 0, lastZ = 0, turn = 0, copies = 0, stores = {}; const max = maxS / C.STEP;
    while (steps < max) {
      const h = G.hunt(), p = h.p; if (h.phase !== 'hunt') break;
      if (h.hits > 0 && h.minTell < 0.4 - 1e-9) bad('tell under 0.4 s: ' + h.minTell);
      for (const u of h.units) { if (!u.standOk) bad(u.kind + ' off the floor'); if (!Number.isFinite(u.x + u.z + u.hp)) bad('NaN'); }
      const zs = G.zaState(-1); if (zs.store) stores[zs.store] = 1;
      let mx = 0, mz = 0, danger = false;
      for (const t of h.tells) {
        if (t.age < react) continue;
        const qx = p.x - t.x, qz = p.z - t.z, m = 0.4;
        if (t.shape === 'line') { const along = qx * t.fx + qz * t.fz, side = qx * t.fz - qz * t.fx; if (along >= -m && along <= t.len + m && Math.abs(side) <= t.w / 2 + m) { danger = true; const sg = side >= 0 ? 1 : -1; mx += t.fz * sg; mz -= t.fx * sg; } }
        else { const d = Math.hypot(qx, qz); if (d <= t.r + m) { danger = true; if (d > 0.01) { mx += qx / d; mz += qz / d; } else mx += 1; } }
      }
      if (danger) {
        if (Math.hypot(p.x - lastX, p.z - lastZ) < 0.01) turn++; else turn = 0;
        if (turn > 2) { const t = mx; mx = -mz; mz = t; }
        const l = Math.hypot(mx, mz) || 1; G.setMove(mx / l, mz / l);
        if (G.skills()[1] === 0) G.cast(1, p.x + mx / l * 4, p.z + mz / l * 4);
      } else {
        G.clearMove();
        let ti = -1; for (const i of order) if (h.units[i].alive) { ti = i; break; }
        const u = h.units[ti], d = Math.hypot(u.x - p.x, u.z - p.z);
        if (u.seen) {
          G.attackUnit(ti); const cd = G.skills();
          if (cd[0] === 0 && d <= K.skills[0].range) G.cast(0, u.x, u.z);
          if (cd[2] === 0 && zs.store && d <= 7) { const n0 = G.zaState(-1).copyN; G.cast(2, u.x, u.z); if (G.zaState(-1).copyN > n0) copies++; }
        } else G.setMove((u.x - p.x) / d, (u.z - p.z) / d);
      }
      lastX = p.x; lastZ = p.z; G.step(1); steps++;
    }
    G.clearMove(); const h = G.hunt();
    return { react, order: order.join(''), phase: h.phase, t: Math.round(h.t), hp: Math.round(h.p.hp), demon: Math.round(h.units[0].hp), plates: h.plates, copies, stores: Object.keys(stores).join('/'), viol };
  };
  const res = [];
  for (const react of [99, 0.3, 0.15]) for (const order of [[0, 1, 2], [1, 2, 0], [2, 1, 0]]) res.push(runBot({ react, order, maxS: 300 }));
  return res;
});
for (const o of out) console.log(`HUNT-ZA ${o.react}/${o.order}: ${o.phase} ${o.t}s hp${o.hp} demon${o.demon} plates${o.plates} copies${o.copies} stored[${o.stores}]${o.viol.length ? ' VIOL ' + o.viol.join(';') : ''}`);
console.log('HUNT-ZA wins', out.filter((o) => o.phase === 'won').length, 'of', out.length, 'errors', errors.length, errors.slice(0, 2).join(' | '));
await browser.close(); server.close();
