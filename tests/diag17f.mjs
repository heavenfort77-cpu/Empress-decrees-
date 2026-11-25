// Diagnostic only (not a check): names (A) the texture left on the GPU by each Rumble/palace cycle (check 1703), (B) the geometries first
// uploaded during check 401's door round trips, (C) the textures not back after a context restore (check 1705), (D) why the 杂甲 bot casts no
// copy in check 170's seeds. INT round 3, 25 Nov. Run: node tests/diag17f.mjs (GitHub runner, job mode cmd).
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
  window.__live = new Map(); window.__cur = null; window.__gOn = false; window.__glog = []; window.__last = null; window.__patchedEarly = false; window.__tid = 0;
  const chain = (o) => { const n = []; for (let q = o; q && n.length < 5; q = q.parent) n.push(q.name || q.type); return n.join('<'); };
  const desc = (t) => { if (!t) return 'NO-THREE-TEXTURE (render target or other)'; const im = t.image || {};
    return [t.constructor.name, 'name=' + t.name, 'u=' + t.uuid.slice(0, 8), 'src=' + (t.source ? t.source.uuid.slice(0, 8) : '?'), (im.width || 0) + 'x' + (im.height || 0),
      'wrap=' + t.wrapS, 'an=' + t.anisotropy, 'cs=' + t.colorSpace, 'fmt=' + t.format, 'min=' + t.minFilter, 'flipY=' + t.flipY].join(' '); };
  window.__desc = desc;
  const gc = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (kind, a) {
    const gl = gc.call(this, kind, a);
    if (gl && /webgl/.test(kind) && !gl.__hooked) {
      gl.__hooked = true; const ct = gl.createTexture.bind(gl), dt = gl.deleteTexture.bind(gl);
      gl.createTexture = () => { const x = ct(); const t = window.__cur; window.__cur = null;
        window.__live.set(x, { id: ++window.__tid, t, d: desc(t), by: window.__last ? chain(window.__last) : '?', st: new Error().stack.split('\n').slice(2, 12).map((s) => s.trim().replace(/\(http[^)]*\/([^/)]*)\)/, '($1)').slice(0, 80)).join(' < ') }); return x; };
      gl.deleteTexture = (x) => { window.__live.delete(x); return dt(x); };
    }
    return gl;
  };
  import('/lib/three.module.min.js').then((T) => {
    window.__patchedEarly = !window.__game;
    const ob = T.Object3D.prototype.onBeforeRender;
    T.Object3D.prototype.onBeforeRender = function () { window.__last = this; return ob.apply(this, arguments); };
    const od = T.EventDispatcher.prototype.addEventListener;
    T.Texture.prototype.addEventListener = function (type, l) { if (type === 'dispose') window.__cur = this; return od.call(this, type, l); };
    T.BufferGeometry.prototype.addEventListener = function (type, l) {
      if (type === 'dispose' && window.__gOn) { const b = this.boundingSphere; window.__glog.push((this.name || this.type) + ' verts ' + (this.attributes.position ? this.attributes.position.count : 0) + ' r ' + (b ? b.radius.toFixed(2) : '?') + ' by ' + (window.__last ? chain(window.__last) : '?') + ' mat ' + (window.__last && window.__last.material ? (window.__last.material.name || window.__last.material.type) : '?')); }
      return od.call(this, type, l); };
    const td = T.Texture.prototype.dispose;
    T.Texture.prototype.dispose = function () { this.__disp = (this.__disp || 0) + 1; return td.call(this); };
  });
});
page.on('pageerror', (e) => console.log('PAGEERR ' + String(e).slice(0, 300)));
const g = async (fn, a) => { await page.waitForFunction(() => !window.__game || !__game.loadBusy || !__game.loadBusy(), null, { timeout: 180000 }); return page.evaluate(fn, a); };
const idle = () => page.waitForFunction(() => !__game.loadBusy(), null, { timeout: 180000 });
const toPalace = () => { const G = __game; G.setSeed(12345); G.pickMode('palace'); G.pickSchool(0); };
const toRumble = () => { const G = __game; G.setSeed(12345); G.pickMode('rumble'); G.pickSchool(0); };
const mem = () => { const r = __game.render(true); return { geoms: r.geoms, texs: r.texs, programs: r.programs }; };
const ids = () => [...window.__live.values()].map((v) => v.id);
const rows = (known) => [...window.__live.values()].filter((v) => known.indexOf(v.id) < 0).map((v) => `#${v.id} ${v.t ? window.__desc(v.t) + ' disposed=' + (v.t.__disp || 0) : v.d} | first draw by ${v.by} | WHO ${v.t ? JSON.stringify(__game.texWho(v.t.uuid)) : '-'} | STACK ${v.st}`);
await page.goto(URL0); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
console.log('PATCHED_EARLY ' + await page.evaluate(() => window.__patchedEarly));
await g(() => { __game.setSeed(12345); __game.reset(); });

// ---- A: texture left per cycle.
await g(toRumble); await idle();
let known = await g(ids); console.log('A rumble0 ' + JSON.stringify(await g(mem)) + ' live GL textures ' + known.length);
for (let c = 0; c < 3; c++) {
  await g(toPalace); await idle(); await g(() => { __game.newRun(); }); await idle(); await g(() => { __game.pickSchool(0); }); await idle();
  const pm = await g(mem), pl = (await g(ids)).length;
  await g(toRumble); await idle();
  const rm = await g(mem), left = await g(rows, known);
  console.log(`A cycle ${c} palace ${JSON.stringify(pm)} live ${pl} rumble ${JSON.stringify(rm)} left ${left.length}`);
  for (const s of left) console.log('  LEFT ' + s);
  known = await g(ids);
}

await browser.close(); server.close();
