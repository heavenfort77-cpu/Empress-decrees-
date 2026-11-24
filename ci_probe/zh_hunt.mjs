// Batch 16 ticket 09 hunt probe (report only; deleted before commit): the player on 纵横甲 in the hunt, units active, Q/W/R used whenever ready.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
let chromium; try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const server = createServer(async (req, res) => { const u = decodeURIComponent(req.url.split('?')[0]); try { const b = await readFile(join(ROOT, u === '/' ? 'index.html' : u)); if (u.endsWith('.html') || u === '/') res.setHeader('Content-Type', 'text/html'); if (u.endsWith('.js') || u.endsWith('.mjs')) res.setHeader('Content-Type', 'text/javascript'); res.end(b); } catch { res.statusCode = 404; res.end(); } });
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage(); const errs = [];
page.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));
await page.goto(`http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder`);
await page.waitForFunction(() => !!window.__game, null, { timeout: 120000 });
for (const seed of [1, 2, 3]) {
  const r = await page.evaluate((seed) => {
    const G = __game, C = G.config, o = { seed, casts: [0, 0, 0] };
    G.setSeed(seed); G.setPkitP(false); G.setSchool(7); G.reset(); G.startHunt(); G.step(Math.round(C.APEX.wakeS / C.STEP) + 1); G.setHp(1e9);
    for (let t = 0; t < 60 / C.STEP; t++) {
      const h = G.hunt(); if (G.royale().phase !== 'hunt' && h.phase !== 'hunt' && t > 10) break;
      if (t % 30 === 0) { const u = h.units.find((x) => x.alive); if (u) { G.setCharge(-1, C.ULT.full); for (let k = 0; k < 3; k++) if (G.cast(k, u.x, u.z)) o.casts[k]++; } }
      G.step(1);
    }
    const s = G.zhState(-1); o.unitPers = s.unitPersN; o.waits = s.persN; o.links = s.linkN; o.swaps = s.swapN;
    o.units = G.hunt().units.map((u) => [u.alive, Math.round(u.hp)]).join('|'); o.demonSkills = G.zhUnit('demon').skills; o.phase = G.royale().phase;
    G.setPkitP(true); G.setSchool(0); G.reset(); return o;
  }, seed);
  console.log('PROBE', JSON.stringify(r));
}
console.log('PROBE errors', errs.length, errs.slice(0, 3).join(' | '));
await browser.close(); server.close();
