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
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
await page.goto(URL0); await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
const res = await page.evaluate(() => {
  const G = __game, C = G.config, out = [];
  for (const seed of [12345, 2, 3]) {
    G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(true); G.pickSchool(1); G.placeholderKit(-1); G.autoPlayer(true); G.setWatch(true);
    const ni = G.schools().suits.findIndex((q) => q.school === 'nong') - 1;
    const o = { seed, heals: [], eat: 0, harv: 0, sowN: 0, diedAt: -1, grownMax: 0, lowNoSprout: 0, lowGrown: 0 };
    let prev = '', cur = null, lastCd0 = 0;
    for (let t = 0; t < 300 / C.STEP; t++) {
      G.step(1); if (G.royale().decidedAt >= 0) break;
      const b = G.bots().list[ni]; if (b.dead) { o.diedAt = +G.royale().t.toFixed(1); break; }
      const n = G.nongState(ni), k = G.kitState(ni), dbg = G.botDbg(ni);
      if (k.bcd[0] > lastCd0 + 1e-9) o.sowN++; lastCd0 = k.bcd[0];
      if (n.grown > o.grownMax) o.grownMax = n.grown;
      o.eat = n.eatN; o.harv = n.harvN;
      if (b.mode === 'heal' && prev !== 'heal') {
        const gs = n.sprouts.filter((sp) => sp.st === 2), goalSprout = gs.some((sp) => Math.hypot(sp.x - dbg.gx, sp.z - dbg.gz) < 0.8);
        const dmin = gs.length ? Math.min(...gs.map((sp) => Math.hypot(sp.x - b.x, sp.z - b.z))) : -1;
        cur = { t: +G.royale().t.toFixed(1), hp: Math.round(b.hp), grown: gs.length, planted: n.planted, goalSprout, dNearest: +dmin.toFixed(1), eat0: n.eatN, endT: -1, eat1: -1 };
        o.heals.push(cur);
      }
      if (cur && b.mode !== 'heal' && prev === 'heal') { cur.endT = +G.royale().t.toFixed(1); cur.eat1 = n.eatN; cur = null; }
      prev = b.mode;
    }
    G.setWatch(false); G.autoPlayer(false); out.push(o);
  }
  return out;
});
for (const o of res) console.log(JSON.stringify(o));
await browser.close(); server.close();
