// Diagnostic only (not a check, not committed): which objects first upload a geometry or texture after the suite's base snapshot,
// and what every draw call is in the crowd scene. INT round 2, 25 Nov.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
const { chromium } = await import('playwright');
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => { const u = decodeURIComponent(req.url.split('?')[0]); const p = normalize(join(ROOT, u === '/' ? 'index.html' : u)); try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); } }).listen(0);
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder&layout=proto`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
await page.addInitScript(() => {
  window.__gOn = false; window.__glog = []; window.__draw = null; window.__patchedEarly = false;
  import('/lib/three.module.min.js').then((T) => {
    window.__patchedEarly = !window.__game;
    const chain = (o) => { const n = []; for (let q = o; q && n.length < 5; q = q.parent) n.push(q.name || q.type); return n.join('<'); };
    const ob = T.Object3D.prototype.onBeforeRender;
    T.Object3D.prototype.onBeforeRender = function (r, s, c, geo, mat) { window.__last = this; if (window.__draw) { const k = chain(this) + ' | ' + (mat && (mat.name || mat.type)); window.__draw[k] = (window.__draw[k] || 0) + 1; } return ob.apply(this, arguments); };
    const od = T.EventDispatcher.prototype.addEventListener;
    const hook = function (kind) { return function (type, l) { if (type === 'dispose' && window.__gOn && !(this.__dl > 0)) window.__glog.push(kind + ' ' + (this.name || this.type || '') + ' by ' + (window.__last ? chain(window.__last) : '?') + (kind === 'tex' && this.isDataTexture ? ' DATA ' + (this.image && this.image.width) + 'x' + (this.image && this.image.height) : '')); if (type === 'dispose') this.__dl = (this.__dl || 0) + 1; return od.call(this, type, l); }; };
    T.BufferGeometry.prototype.addEventListener = hook('geo');
    T.Texture.prototype.addEventListener = hook('tex');
    const orm = T.EventDispatcher.prototype.removeEventListener;
    const unhook = function (type, l) { if (type === 'dispose' && this.__dl > 0) this.__dl--; return orm.call(this, type, l); };
    T.BufferGeometry.prototype.removeEventListener = unhook; T.Texture.prototype.removeEventListener = unhook;
  });
});
page.on('pageerror', (e) => console.log('PAGEERR ' + String(e).slice(0, 300)));
const g = async (fn, a) => { await page.waitForFunction(() => !window.__game || !__game.loadBusy || !__game.loadBusy(), null, { timeout: 180000 }); return page.evaluate(fn, a); };
await page.goto(URL0); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
console.log('PATCHED_EARLY ' + await page.evaluate(() => window.__patchedEarly));
await g(() => { __game.setSeed(12345); __game.reset(); });
const base = await g(() => __game.render(true));
console.log('BASE ' + JSON.stringify(base) + ' chars ' + JSON.stringify(await g(() => __game.chars())));
const dump = async (label) => { const r = await g(() => __game.render(true)); const L = await page.evaluate(() => { const x = window.__glog.slice(); window.__glog.length = 0; return x; }); console.log(`SCENE ${label} ${JSON.stringify(r)}`); const c = {}; for (const s of L) c[s] = (c[s] || 0) + 1; for (const k in c) console.log(`  NEW ${c[k]}x ${k}`); };
await page.evaluate(() => { window.__gOn = true; });
// A: nine suits in a royale, 5 s, all in view.
await g(() => { const G = __game; G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); for (let i = 0; i < G.config.BOTS.count; i++) G.placeBot(i, -4 + (i % 3) * 3, 4 + Math.floor(i / 3) * 1.5); G.step(300); });
await dump('A_suits');
// B: check 57 scene (7 cubs and their tells).
await g(() => {
  const G = __game, C = G.config, waves = C.KENNEL.waves;
  C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
  G.setSeed(12345); G.setBots(G.config.BOTS.count); G.reset(); G.step(Math.round((C.KENNEL.firstS + 0.1) / C.STEP)); G.setHp(1e9);
  const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
  for (let n = 0; n < 300; n++) { for (let i = 0; i < G.config.BOTS.count; i++) G.placeBot(i, cx - 4 + (i % 3) * 3, cz + 2 + Math.floor(i / 3) * 1.5); G.step(1); if (n % 30 === 0) G.render(true); }
  C.KENNEL.waves = waves;
});
await dump('B_cubs');
// C: the hunt (check 41's start).
await g(() => { const G = __game, C = G.config; G.setBots(0); G.reset(); G.startHunt(); G.step(Math.round(C.APEX.wakeS / C.STEP) + 1); for (let n = 0; n < 10; n++) { G.step(30); G.render(true); } });
await dump('C_hunt');
await g(() => { const G = __game; G.reset(); });
await dump('C_reset');
// D: check 306 scene (two full squads), with every draw named.
await g(() => { const G = __game; G.setSeed(12345); G.setBots(0); G.reset(); G.teleport(-7, -6); });
const empty = await g(() => { window.__draw = {}; const r = __game.render(true); const d = window.__draw; window.__draw = null; return { r, d }; });
await g(() => { const G = __game, full = ['wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'nu', 'che']; G.guardSpawn('huangjia', full, -7, -1, { fz: -1, open: true }); G.guardSpawn('huangjia', full, -7, -11, { fz: 1, open: true }); G.step(30); });
const full = await g(() => { window.__draw = {}; const r = __game.render(true); const d = window.__draw; window.__draw = null; return { r, d }; });
console.log('D_empty ' + JSON.stringify(empty.r) + ' D_full ' + JSON.stringify(full.r));
for (const k in full.d) if (full.d[k] !== (empty.d[k] || 0)) console.log(`  DRAW +${full.d[k] - (empty.d[k] || 0)} ${k}`);
await dump('D_guards');
await browser.close(); server.close();
