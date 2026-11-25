// PREP-CHR real-GPU probe (GitHub macOS runner, ANGLE Metal): the character cast page ci_probe/chars.html against the game's reference
// scene in the same job. Pattern of ci_probe/perfgpu.mjs on ci-perf (flags, 6 s settle + 20 s timed, fresh browser per scene).
// Usage: SCENES=reference,chr_wide,... OUT=dir node ci_probe/chrperf.mjs [--soft]   (--soft = SwiftShader, syntax run only)
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const SOFT = process.argv.includes('--soft'), SETTLE = Number(process.env.SETTLE_S || 6), TIMED = Number(process.env.TIMED_S || 20), OUT = process.env.OUT || 'chr_out';
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary' };
// Control: plain three.js r171, 30 boxes, one 2048 shadow sun re-rendered every frame (as perfgpu.mjs webglmin).
const WEBGL_MIN = `<!doctype html><html><body style="margin:0;background:#120d16"><script type="importmap">{"imports":{"three":"/lib/three.module.min.js"}}</script>
<script type="module">import * as THREE from 'three';
const r = new THREE.WebGLRenderer({ antialias: false }); r.setPixelRatio(1); r.setSize(innerWidth, innerHeight); r.shadowMap.enabled = true; document.body.appendChild(r.domElement);
const sc = new THREE.Scene(), cam = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.5, 120); cam.position.set(0, 14, 16); cam.lookAt(0, 0, 0);
sc.add(new THREE.HemisphereLight(0xffffff, 0x222233, 0.8)); const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(8, 16, 6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sc.add(sun);
const fl = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: 0x665544 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl);
const g = new THREE.BoxGeometry(1, 2, 1), bs = [];
for (let i = 0; i < 30; i++) { const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x8899aa + i * 997 })); m.position.set((i % 6) * 3 - 7.5, 1, Math.floor(i / 6) * 3 - 6); m.castShadow = m.receiveShadow = true; sc.add(m); bs.push(m); }
window.__game = { render: () => ({ calls: r.info.render.calls, tris: r.info.render.triangles, programs: r.info.programs.length, geoms: r.info.memory.geometries, texs: r.info.memory.textures }) };
const f = (t) => { requestAnimationFrame(f); for (let i = 0; i < bs.length; i++) bs[i].rotation.y = t * 0.001 + i; r.render(sc, cam); };
r.compile(sc, cam); requestAnimationFrame(f); window.__ready = true;</script></body></html>`;
const server = createServer(async (req, res) => {
  if (req.url.startsWith('/__webglmin')) { res.writeHead(200, { 'content-type': 'text/html' }); res.end(WEBGL_MIN); return; }
  const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u === '/' ? 'index.html' : u));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/`;
const ARGS = (SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit']).concat(['--js-flags=--expose-gc', '--enable-precise-memory-info']);
// GL call counters (no game change): texture uploads (bone textures, first uploads), buffer uploads (instance attributes), program links.
const INIT = `(() => { const C = window.__glc = { tex: 0, buf: 0, link: 0 };
  const wrap = (P, n, k) => { const o = P[n]; if (!o) return; P[n] = function (...a) { C[k]++; return o.apply(this, a); }; };
  for (const P of [WebGL2RenderingContext.prototype, WebGLRenderingContext.prototype]) {
    for (const n of ['texImage2D', 'texSubImage2D', 'texImage3D', 'texSubImage3D', 'compressedTexImage2D', 'compressedTexSubImage2D']) wrap(P, n, 'tex');
    for (const n of ['bufferData', 'bufferSubData']) wrap(P, n, 'buf');
    wrap(P, 'linkProgram', 'link'); } })();`;
const CHR = (q) => ({ path: 'ci_probe/chars.html', q });
const SCENES = {
  reference: { q: 'lock&tier=medium&bots=0', setup: () => { __game.setSeed(12345); __game.reset(); } },
  webglmin: { path: '__webglmin', q: '' },
  chr_wide: { ...CHR('tier=medium&cam=wide'), shot: 'chr_wide' },
  chr_close: { ...CHR('tier=medium&cam=close'), shot: 'chr_close' },
  chr_noout: { ...CHR('tier=medium&cam=close&out=0'), shot: 'chr_close_nooutline' },
  chr_low: { ...CHR('tier=low&cam=wide'), shot: 'chr_wide_low' },
  chr_dorm: { ...CHR('tier=medium&cam=wide&dorm=9') },
  chr_cycles: { ...CHR('tier=medium&cam=wide'), cycles: 5 },
};
await mkdir(OUT + '/shots', { recursive: true });
const rows = []; let gpu = '', browser = null;
for (const name of (process.env.SCENES || 'reference,chr_wide,chr_close').split(',')) {
  const sc = SCENES[name]; if (!sc) { console.log('UNKNOWN scene ' + name); continue; }
  if (browser) await browser.close();
  browser = await chromium.launch({ args: ARGS });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 }), errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 160)));
  await page.addInitScript(INIT);
  const t0 = Date.now();
  await page.goto(BASE + (sc.path || '') + '?' + sc.q);
  await page.waitForFunction(() => window.__ready === true || !!window.__err, null, { timeout: 180000 });
  const loadMs = Date.now() - t0, perr = await page.evaluate(() => window.__err || '');
  if (perr) { console.log('ROW ' + JSON.stringify({ scene: name, err: perr.slice(0, 300) })); rows.push({ scene: name, err: perr }); continue; }
  if (!gpu) gpu = await page.evaluate(() => { const c = document.createElement('canvas'), gl = c.getContext('webgl2'), d = gl && gl.getExtension('WEBGL_debug_renderer_info'); return d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'unknown'; });
  if (sc.setup) await page.evaluate(`(${sc.setup.toString()})()`);
  if (sc.cycles) {
    const cyc = await page.evaluate(async (n) => { const P = window.__probe; await new Promise((r) => setTimeout(r, 3000)); return { cyc: await P.cycles(n), info: P.info() }; }, sc.cycles);
    const a = cyc.cyc[0], b = cyc.cyc[cyc.cyc.length - 1];
    const row = { scene: name, loadMs, errs: errs.length, cycles: cyc.cyc, flat: a.geoms === b.geoms && a.texs === b.texs && a.programs === b.programs && b.heapMB - a.heapMB < 2, info: cyc.info };
    rows.push(row); console.log('ROW ' + JSON.stringify(row)); await page.close(); continue;
  }
  const r = await page.evaluate(async ({ SETTLE, TIMED }) => {
    const wait = (s) => new Promise((res) => setTimeout(res, s * 1000));
    await wait(SETTLE);
    if (window.gc) window.gc();
    const heap = () => performance.memory ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : -1, P = window.__probe;
    const g0 = Object.assign({}, window.__glc), h0 = heap(), d = []; let last = 0, run = true, mix = 0, n = 0;
    await new Promise((res) => { const f = (t) => { if (last) d.push(t - last); last = t; if (P) { mix += P.CH.stats().mixers; n++; } if (run) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); setTimeout(() => { run = false; }, TIMED * 1000); });
    const g1 = window.__glc, F = d.length, info = __game.render(false);
    d.sort((a, b) => a - b); const sum = d.reduce((a, b) => a + b, 0);
    return { frames: F, fps: +(F / (sum / 1000)).toFixed(1), p50: +d[Math.floor(F * 0.5)].toFixed(1), p95: +d[Math.floor(F * 0.95)].toFixed(1), worst: +d[F - 1].toFixed(1),
      over20: +(100 * d.filter((x) => x > 20).length / F).toFixed(1), calls: info.calls, tris: info.tris, programs: info.programs, geoms: info.geoms, texs: info.texs,
      texUpPerFrame: +((g1.tex - g0.tex) / F).toFixed(2), bufUpPerFrame: +((g1.buf - g0.buf) / F).toFixed(2), linksInTimed: g1.link - g0.link, heap0: h0, heap1: heap(),
      mixersPerFrame: n ? +(mix / n).toFixed(2) : 0, info: P ? P.info() : null };
  }, { SETTLE, TIMED });
  const row = { scene: name, loadMs, errs: errs.length, err0: errs[0] || '', ...r };
  rows.push(row); console.log('ROW ' + JSON.stringify(row));
  if (sc.shot) await page.screenshot({ path: `${OUT}/shots/${sc.shot}.png`, timeout: 120000 }).catch((e) => console.log('SHOT failed ' + sc.shot + ' ' + String(e).slice(0, 80)));
  await page.close();
}
console.log('RENDERER ' + gpu + (/swiftshader|llvmpipe|software/i.test(gpu) ? '  (NOT a real GPU)' : ''));
console.log('scene          fps     p50   p95   worst  >20ms%  calls  tris     prog  texUp/f bufUp/f links heapMB      mixers/f');
for (const r of rows) if (r.fps !== undefined) console.log([r.scene.padEnd(13), String(r.fps).padStart(6), String(r.p50).padStart(6), String(r.p95).padStart(5), String(r.worst).padStart(6), String(r.over20).padStart(6), String(r.calls).padStart(6), String(r.tris).padStart(8), String(r.programs).padStart(5), String(r.texUpPerFrame).padStart(7), String(r.bufUpPerFrame).padStart(7), String(r.linksInTimed).padStart(5), (r.heap0 + '-' + r.heap1).padStart(11), String(r.mixersPerFrame).padStart(7), r.errs ? ' ERR ' + r.err0 : ''].join(' '));
for (const r of rows) if (r.cycles) console.log(`CYCLES ${r.scene}: ${r.flat ? 'FLAT' : 'FAIL not flat'} ${JSON.stringify(r.cycles.map((c) => [c.geoms, c.texs, c.programs, c.heapMB]))}`);
for (const r of rows) if (r.err) console.log(`FAIL ${r.scene}: ${r.err.slice(0, 200)}`);
// Gates count what they measured: a timed scene with no frames, or a probe scene that drew no characters, is a FAIL (lead RULE 25 Nov).
let bad = rows.filter((r) => r.err).length;
for (const r of rows) if (r.fps !== undefined && (!r.frames || (r.scene.startsWith('chr') && (!r.info || !r.info.crowdDrawn || !r.mixersPerFrame)))) { console.log(`FAIL ${r.scene}: measured nothing (frames ${r.frames}, crowd ${r.info && r.info.crowdDrawn}, mixers ${r.mixersPerFrame})`); bad++; }
for (const r of rows) if (r.cycles && (!r.cycles.length || !r.flat)) { console.log(`FAIL ${r.scene}: cycles ${r.cycles.length} flat ${r.flat}`); bad++; }
if (!rows.length) { console.log('FAIL no scene ran'); bad++; }
// Budget gate (owner rule 32): every character scene, the heaviest included, under 500 draw calls and 0.5M triangles; a scene with
// 0 calls or triangles measured nothing and fails. The gate is self-tested first on rows at the limits (mutation test of the monitor).
const BUDGET = { calls: 500, tris: 500000 };
const overBudget = (r) => !(r.calls > 0 && r.tris > 0 && r.calls < BUDGET.calls && r.tris < BUDGET.tris);
const selfOk = overBudget({ calls: BUDGET.calls, tris: 1 }) && overBudget({ calls: 1, tris: BUDGET.tris }) && overBudget({ calls: 0, tris: 0 }) && !overBudget({ calls: 499, tris: 499999 });
if (!selfOk) { console.log('FAIL budget gate self-test'); bad++; }
const chrRows = rows.filter((r) => r.fps !== undefined && r.scene.startsWith('chr'));
for (const r of chrRows) if (overBudget(r)) { console.log(`FAIL ${r.scene}: budget calls ${r.calls} (< ${BUDGET.calls}) triangles ${r.tris} (< ${BUDGET.tris})`); bad++; }
if (!chrRows.length) { console.log('FAIL budget: no character scene measured'); bad++; }
if (chrRows.length) {
  const hc = chrRows.reduce((a, b) => (b.calls > a.calls ? b : a)), ht = chrRows.reduce((a, b) => (b.tris > a.tris ? b : a));
  console.log(`BUDGET ${selfOk ? 'self-test ok' : 'self-test FAIL'}; heaviest calls ${hc.calls} (${hc.scene}), heaviest triangles ${ht.tris} (${ht.scene}); limits < ${BUDGET.calls} / < ${BUDGET.tris}`);
}
console.log(`PROBE ${bad ? 'FAIL' : 'PASS'} scenes ${rows.length}`); process.exitCode = bad ? 1 : 0;
await browser.close(); server.close();
