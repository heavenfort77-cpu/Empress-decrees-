// Headless checks for the box map. Usage: node tests/run.mjs   (software GPU: correctness and counts only, no real fps)
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }

const ROOT = new URL('../', import.meta.url).pathname;
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
  const run = (school, seed, pin) => {
    G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(true); G.pickSchool(1); G.placeholderKit(-1);
    for (const s of pin) G.placeholderKit(G.schools().suits.findIndex((q) => q.school === s) - 1);
    G.autoPlayer(true); G.setWatch(true);
    const bi = G.schools().suits.findIndex((q) => q.school === school) - 1, R = C.KITS[school].skills[2];
    const o = { school, seed, fullAt: -1, diedAt: -1, cast: 0, samples: 0, modes: {}, why: {}, dHist: {}, near: {}, ult0: G.kitState(bi).ultN };
    for (let t = 0; t < 300 / C.STEP; t++) {
      G.step(1); if (G.royale().decidedAt >= 0) break;
      const b = G.bots().list[bi]; if (b.dead) { if (o.diedAt < 0) o.diedAt = +G.royale().t.toFixed(1); break; }
      const ch = G.chargeOf(bi), k = G.kitState(bi);
      if (k.ultN > o.ult0) { o.cast += k.ultN - o.ult0; o.ult0 = k.ultN; }
      if (ch < 100) continue; if (o.fullAt < 0) o.fullAt = +G.royale().t.toFixed(1);
      if (t % 15) continue; o.samples++;
      o.modes[b.mode] = (o.modes[b.mode] || 0) + 1;
      if (b.tgt !== -1) {
        const L = b.tgt === 0 ? G.player() : b.tgt > 0 ? G.bots().list[b.tgt - 1] : null;
        if (L) { const d = Math.hypot(L.x - b.x, L.z - b.z), bk = d < 3 ? '<3' : d < 6 ? '3-6' : d < 11 ? '6-11' : '11+'; o.dHist[bk] = (o.dHist[bk] || 0) + 1; }
      } else o.dHist.none = (o.dHist.none || 0) + 1;
      if (school === 'nong') { const n = G.nongState(bi), near = n.sprouts.filter((sp) => sp.st > 0 && Math.hypot(sp.x - b.x, sp.z - b.z) <= R.radius).length; o.near[near] = (o.near[near] || 0) + 1; o.planted = n.planted; }
    }
    G.setWatch(false); G.autoPlayer(false); out.push(o);
  };
  for (const seed of [12345, 2, 3]) run('ming', seed, ['yinyang', 'nong']);
  for (const seed of [12345, 2, 3]) run('nong', seed, []);
  return out;
});
for (const o of res) console.log(JSON.stringify(o));
await browser.close(); server.close();
