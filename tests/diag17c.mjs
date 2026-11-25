// Diagnostic only (not a check): GPU texture count over Rumble/palace cycles with the palace art off, then on.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
const { chromium } = await import('playwright');
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => { const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0]))); try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); } }).listen(0);
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder&layout=proto`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
await page.addInitScript(() => { const L = window.__tl = new Map(); window.__tlOn = false; const P = WebGL2RenderingContext.prototype, oc = P.createTexture, od = P.deleteTexture;
  P.createTexture = function () { const t = oc.apply(this, arguments); if (window.__tlOn) L.set(t, (new Error().stack || '').split('\n').slice(2, 12).map((x) => x.trim().replace(/https?:\/\/[^/]+\//, '')).join(' < ')); return t; };
  P.deleteTexture = function (t) { L.delete(t); return od.apply(this, arguments); }; });
page.on('pageerror', (e) => console.log('PAGEERR ' + String(e).slice(0, 300)));
const g = async (fn, a) => { await page.waitForFunction(() => !window.__game || !__game.loadBusy || !__game.loadBusy(), null, { timeout: 180000 }); return page.evaluate(fn, a); };
await page.goto(URL0); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
// Track every Texture disposed and every texture uploaded (three's own module instance, same URL as the game's importmap).
await page.evaluate(async () => { const T = await import('/lib/three.module.min.js'); const W = window.__tw = { up: new Map(), disp: new Set() };
  const od = T.Texture.prototype.dispose; T.Texture.prototype.dispose = function () { W.disp.add(this.uuid); return od.apply(this, arguments); }; });
await page.evaluate(() => { window.__tlOn = true; });
for (const art of [false, true]) {
  await g((a) => { __game.config.PAL_ART.arch = a; __game.config.PAL_ART.props = a; }, art);
  for (let k = 0; k < 3; k++) {
    await g(() => { const G = __game; G.setSeed(12345); G.pickMode('rumble'); G.pickSchool(0); }); const r = await g(() => __game.render(true));
    await g(() => { const G = __game; G.pickMode('palace'); G.pickSchool(0); }); const p = await g(() => __game.render(true));
    if (art) { const ids = await g(() => __game.artTexIds()); await g(() => { __game.pickMode('rumble'); __game.pickSchool(0); }); const d = await page.evaluate(() => [...window.__tw.disp]); console.log('KITTEX ' + JSON.stringify({ n: ids.list.length, notDisposed: ids.list.filter((u) => !d.includes(u)), extra: ids.extra })); }
    console.log(`CYCLE art=${art} ${k} rumble texs ${r.texs} geoms ${r.geoms} palace texs ${p.texs} geoms ${p.geoms} art ${JSON.stringify(await g(() => __game.art().on))}`);
  }
}
const left = await page.evaluate(() => [...window.__tl.values()]);
console.log('LEFT ' + left.length); for (const x of left.slice(0, 12)) console.log('STACK ' + x.slice(0, 700));
await browser.close(); server.close();
