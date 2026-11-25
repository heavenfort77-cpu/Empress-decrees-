// VFXP probe timing (painted cards, cards.js) on the real-GPU macOS runner (ANGLE Metal, vsync and frame limit off), 1920x1080. Serves the repo, opens
// probe/vfxp/index.html per scene, settles SETTLE_S, times TIMED_S of rAF frames and per-frame GPU time (EXT_disjoint_timer_query_webgl2).
// Scenes are interleaved and the heavy pair and the reference are measured twice for a noise band. Then shots (--shots): A and B side by
// side at each atlas frame, clipped round the pair at play size. Usage: node ci_vfx/perfvfx.mjs [--soft] [--shots-only]
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const SOFT = process.argv.includes('--soft'), SHOTS_ONLY = process.argv.includes('--shots-only');
const SETTLE = Number(process.env.SETTLE_S || 6), TIMED = Number(process.env.TIMED_S || 20), OUT = process.env.OUT || 'vfx_out';
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.jpg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u));
  if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/probe/vfxp/index.html`;
const ARGS = SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit'];
const browser = await chromium.launch({ args: ARGS });
// Forward, then reversed (#2): the reference at both ends. heavy = 10 suits + 37 fodder + the apex fighting (about 40-60 cards); x4 = stress.
const ONE = [['ref', 'mode=ref'], ['heavy', 'mode=heavy'], ['heavy_x4', 'mode=heavy&mult=4']];
const SCENES = [...ONE, ...ONE.slice().reverse().map(([n, q]) => [n + '#2', q])];
const q = (a, p) => a[Math.min(a.length - 1, Math.floor(a.length * p))];
const rows = [];
if (!SHOTS_ONLY) for (const [name, qs] of SCENES) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = []; page.on('pageerror', (e) => errs.push(e.message)); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  const t0 = Date.now();
  await page.goto(`${BASE}?${qs}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  const loadMs = Date.now() - t0;
  await page.waitForTimeout(SETTLE * 1000);
  await page.evaluate(() => window.__probe.start()); await page.waitForTimeout(TIMED * 1000);
  const s = await page.evaluate(() => window.__probe.stop());
  const ft = s.ft.slice().sort((a, b) => a - b), gt = s.gt.slice().sort((a, b) => a - b), gc = s.gc.slice().sort((a, b) => a - b), mean = (a) => a.length ? +(a.reduce((x, y) => x + y, 0) / a.length).toFixed(3) : null, sum = s.ft.reduce((a, b) => a + b, 0);
  const row = { scene: name, fps: +(s.ft.length / (sum / 1000)).toFixed(1), p50: +q(ft, 0.5).toFixed(2), p95: +q(ft, 0.95).toFixed(2), worst: +ft[ft.length - 1].toFixed(1),
    over20: s.ft.filter((x) => x > 20).length, frames: s.ft.length, liveMean: s.live.length ? +(s.live.reduce((a, b) => a + b, 0) / s.live.length).toFixed(1) : 0, liveMax: s.live.length ? Math.max(...s.live) : 0, gpuMean: gt.length ? +(gt.reduce((a, b) => a + b, 0) / gt.length).toFixed(3) : null,
    gpuP50: gt.length ? +q(gt, 0.5).toFixed(3) : null, cardGpuMean: mean(gc), cardGpuP95: gc.length ? +q(gc, 0.95).toFixed(3) : null, cardGpuN: gc.length, long: s.long.map((x) => +x.toFixed(0)).join(','), settleFrames: s.settleFrames, gpuP95: gt.length ? +q(gt, 0.95).toFixed(3) : null, gpuN: gt.length, calls: s.calls, tris: s.tris,
    progNew: s.programs - s.progsAtStart, progs: s.programs, texs: s.textures, cardTexMB: s.cardTexMB, loadMs, timer: s.timer, errs: errs.length };
  rows.push(row); console.log('ROW ' + JSON.stringify(row)); if (errs.length) console.log('ERRS ' + name + ' ' + errs.slice(0, 5).join(' | '));
  await page.close();
}
if (rows.length) {
  console.log('\nlive cards (mean/max): ' + rows.map((r) => r.scene + ' ' + r.liveMean + '/' + r.liveMax).join(', '));
  console.log('\nscene       fps     p50    p95   worst  >20ms  stageGPU stageP95 cardGPU cardP95 calls  tris   newProg texMB(cards) settleF long frames [t ms from start, ms]');
  for (const r of rows) console.log([r.scene.padEnd(10), String(r.fps).padStart(7), String(r.p50).padStart(6), String(r.p95).padStart(6), String(r.worst).padStart(6),
    String(r.over20).padStart(6), String(r.gpuMean).padStart(8), String(r.gpuP95).padStart(8), String(r.cardGpuMean).padStart(7), String(r.cardGpuP95).padStart(7), String(r.calls).padStart(5), String(r.tris).padStart(6), String(r.progNew).padStart(8), String(r.cardTexMB).padStart(8), String(r.settleFrames).padStart(7), ' ' + r.long].join(' '));
  // Gates: new programs during timing must be 0 (warm-up proven); every scene under 500 calls and 0.5 M triangles; no page errors.
  for (const r of rows) {
    console.log(`GATE ${r.scene} warmup newPrograms ${r.progNew} ${r.progNew === 0 ? 'PASS' : 'FAIL'}`);
    console.log(`GATE ${r.scene} budget calls ${r.calls} tris ${r.tris} ${r.calls < 500 && r.tris < 500000 ? 'PASS' : 'FAIL'}`);
    console.log(`GATE ${r.scene} errors ${r.errs} ${r.errs === 0 ? 'PASS' : 'FAIL'}`);
  }
}
// Shots: every card at play size beside a suit box (gallery, frozen at the peak frame) per ramp row and page; the new fa slash beside B per frame.
await mkdir(`${OUT}/shots`, { recursive: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
const perrs = []; page.on('pageerror', (e) => perrs.push(e.message)); page.on('console', (m) => { if (m.type() === 'error') perrs.push(m.text()); });
const ROWS = (process.env.ROWS || 'ru,dao,fa,mo,yinyang,za,ming,zongheng,nong,apex,rebel_olive,rebel_umber,rebel_madder,guard,bronze,jade,water,ash').split(',');
for (const row of ROWS) for (let pg = 0; pg < 4; pg++) {
  await page.goto(`${BASE}?mode=gallery&row=${row}&page=${pg}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/shots/g_${row}_${pg}.jpg`, type: 'jpeg', quality: 82 });
}
for (let f = 0; f < 13; f += 2) {
  await page.goto(`${BASE}?mode=pairB&frame=${f}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); await page.waitForTimeout(300);
  await page.screenshot({ path: `${OUT}/shots/pairB_f${String(f).padStart(2, '0')}.jpg`, type: 'jpeg', quality: 85 });
}
for (const [nm, qs] of [['heavy', 'mode=heavy'], ['heavy_x4', 'mode=heavy&mult=4']]) {
  await page.goto(`${BASE}?${qs}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); await page.waitForTimeout(2500);
  await page.screenshot({ path: `${OUT}/shots/${nm}.jpg`, type: 'jpeg', quality: 85 });
}
console.log(`GATE shots errors ${perrs.length} ${perrs.length === 0 ? 'PASS' : 'FAIL'} ${perrs.slice(0, 3).join(' | ')}`);
await writeFile(`${OUT}/rows.json`, JSON.stringify(rows, null, 1));
await browser.close(); server.close();
