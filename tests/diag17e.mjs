// Diagnostic only (not a check, not committed): check 170's 杂甲 matches on the HEAD build (idx_head.html) and the WIP build, timeline compared.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
const { chromium } = await import('playwright');
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => { const u = decodeURIComponent(req.url.split('?')[0]); const p = normalize(join(ROOT, u === '/' ? 'index.html' : u)); try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); } }).listen(0);
const Q = '?lock&tier=medium&bots=0&pkit=placeholder&layout=proto', BASEU = `http://127.0.0.1:${server.address().port}/`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const file of ['idx_head.html', 'index.html']) {
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  page.on('pageerror', (e) => console.log(file + ' PAGEERR ' + String(e).slice(0, 300)));
  const g = async (fn, a) => { await page.waitForFunction(() => !window.__game || !__game.loadBusy || !__game.loadBusy(), null, { timeout: 180000 }); return page.evaluate(fn, a); };
  await page.goto(BASEU + file + Q); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  const out = await g(() => {
    const G = __game, C = G.config, res = [];
    for (const seed of [12345, 2, 3]) {
      G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(true); G.pickSchool(0); G.autoPlayer(true); G.setWatch(true);
      const zi = G.schools().suits.findIndex((q) => q.school === 'za') - 1, ev = []; let last = '', cn = 0, en = 0, dead = false, hpSum = 0;
      for (let t = 0; t < 300 / C.STEP; t++) {
        G.step(1); const r = G.royale(); if (r.decidedAt >= 0) { ev.push('end@' + r.decidedAt.toFixed(1)); break; }
        const z = G.zaState(zi), q = G.bots().list[zi]; hpSum += q.hp;
        if (z.store !== last) { ev.push('st ' + z.store + '@' + (t * C.STEP).toFixed(2)); last = z.store; }
        if (z.copyN !== cn) { ev.push('copy@' + (t * C.STEP).toFixed(2)); cn = z.copyN; }
        if (z.expN !== en) { ev.push('exp' + z.expN + '@' + (t * C.STEP).toFixed(2)); en = z.expN; }
        if (q.dead && !dead) { ev.push('dead@' + (t * C.STEP).toFixed(2)); dead = true; }
        if (t % 600 === 0) ev.push('hp' + q.hp.toFixed(0) + ' ch' + (q.ch === undefined ? '?' : q.ch.toFixed(0)) + ' x' + q.x.toFixed(1) + '@' + (t * C.STEP).toFixed(0));
      }
      G.setWatch(false); G.autoPlayer(false); res.push({ seed, zi, hpSum: Math.round(hpSum), ev });
    }
    return res;
  });
  for (const r of out) console.log(`${file} seed ${r.seed} zi ${r.zi} hpSum ${r.hpSum} :: ${r.ev.join(' ')}`.slice(0, 3000));
  await page.close();
}
await browser.close(); server.close();
