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
        window.__live.set(x, { id: ++window.__tid, t, d: desc(t), by: window.__last ? chain(window.__last) : '?', st: t ? '' : new Error().stack.split('\n').slice(2, 7).map((s) => s.trim().slice(0, 90)).join(' < ') }); return x; };
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
const rows = (known) => [...window.__live.values()].filter((v) => known.indexOf(v.id) < 0).map((v) => `#${v.id} ${v.t ? window.__desc(v.t) + ' disposed=' + (v.t.__disp || 0) : v.d} | first draw by ${v.by}${v.st ? ' | ' + v.st : ''}`);
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

// ---- B: geometries first uploaded in check 401's round trips.
await g(toPalace); await idle();
const b = await g(() => {
  const G = __game, o = {};
  G.setSeed(12345); G.setMode('palace'); G.reset();
  const d0 = G.palace().doors[0]; const r0 = G.render(true); window.__glog.length = 0; window.__gOn = true;
  G.teleport(d0.x, d0.z + 1.6); G.step(1); G.render(true); o.near = window.__glog.splice(0);
  G.setMove(0, -1); for (let i = 0; i < 120 && G.palace().cur !== 'court'; i++) G.step(1); G.step(60); G.clearMove(); G.render(true); o.court = window.__glog.splice(0);
  for (let k = 0; k < 5; k++) { G.teleport(d0.x, d0.z + 1.6); G.step(2); G.teleport(d0.x, d0.z - 1.6); G.step(2); G.teleport(d0.x, d0.z - 9); G.step(2); G.teleport(d0.x, d0.z + 9); G.step(2); }
  const r3 = G.render(true); o.trips = window.__glog.splice(0); window.__gOn = false; o.pg = [r0.programs, r3.programs, r0.geoms, r3.geoms]; return o;
});
console.log('B pg ' + JSON.stringify(b.pg));
for (const k of ['near', 'court', 'trips']) { const c = {}; for (const s of b[k]) c[s] = (c[s] || 0) + 1; console.log(`B ${k}: ${b[k].length} new geometries`); for (const s in c) console.log(`  NEWGEO ${c[s]}x ${s}`); }

// ---- C: context lost and restored in the palace.
await g(toPalace); await idle();
const c0 = await g(() => ({ mem: __game.render(true), rows: [...window.__live.values()].map((v) => (v.t ? v.t.uuid : 'rt' + v.id) + ' ## ' + (v.t ? window.__desc(v.t) : v.d) + ' | by ' + v.by) }));
await page.evaluate(() => { window.__lc = __game.loseContext(); });
await page.waitForFunction(() => __game.state().ctxLost === true, null, { timeout: 30000 });
await page.evaluate(() => { window.__live.clear(); window.__lc.restoreContext(); });
await page.waitForFunction(() => __game.state().ctxLost === false, null, { timeout: 60000 });
await idle();
const f0 = await g(() => __game.state().frames);
await page.waitForFunction((f) => __game.state().frames > f + 5, f0, { timeout: 60000 });
const c1 = await g(() => ({ led: __game.load().led, mem: __game.render(true), u: [...window.__live.values()].map((v) => (v.t ? v.t.uuid : 'rt' + v.id)) }));
console.log(`C before ${JSON.stringify(c0.mem)} live ${c0.rows.length}; after ${JSON.stringify(c1.mem)} live ${c1.u.length}; led ${JSON.stringify(c1.led)}`);
for (const r of c0.rows) { const u = r.split(' ## ')[0]; if (c1.u.indexOf(u) < 0) console.log('  NOTBACK ' + r.split(' ## ')[1]); }

// ---- D: the 杂甲 bot in check 170's seeds: ticks with a stored skill, with a full meter, with both; meter peak.
await g(toRumble); await idle();
const d = await g(() => {
  const G = __game, C = G.config, res = [];
  for (const seed of [12345, 2, 3]) {
    G.setSeed(seed); G.setBots(C.BOTS.count); G.setPkitP(true); G.pickSchool(0); G.autoPlayer(true); G.setWatch(true);
    const zi = G.schools().suits.findIndex((q) => q.school === 'za') - 1, c0 = G.zaState(zi).copyN, o = { seed, zi, copyAtStart: c0, alive: 0, store: 0, full: 0, both: 0, chMax: 0, chEnd: 0, ultMode: '', stores: [] };
    let last = '';
    for (let t = 0; t < 300 / C.STEP; t++) {
      G.step(1); if (G.royale().decidedAt >= 0) break;
      const z = G.zaState(zi), q = G.bots().list[zi]; if (q.dead) continue;
      o.alive++; const f = z.ch >= C.ULT.full; if (z.store) o.store++; if (f) o.full++; if (z.store && f) o.both++; if (z.ch > o.chMax) o.chMax = z.ch; o.chEnd = z.ch;
      if (z.store !== last) { o.stores.push(z.store + '@' + (t * C.STEP).toFixed(0) + ' ch' + Math.round(z.ch)); last = z.store; }
    }
    o.copies = G.zaState(zi).copyN - c0; o.full100 = C.ULT.full; G.setWatch(false); G.autoPlayer(false); res.push(o);
  }
  G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); return res;
});
for (const r of d) console.log('D ' + JSON.stringify(r));
await browser.close(); server.close();
