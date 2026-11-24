// VFX probe timing on the real-GPU macOS runner (ANGLE Metal, vsync and frame limit off), 1920x1080. Serves the repo, opens
// probe/vfx/index.html per scene, settles SETTLE_S, times TIMED_S of rAF frames and per-frame GPU time (EXT_disjoint_timer_query_webgl2).
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
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u));
  if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/probe/vfx/index.html`;
const ARGS = SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit'];
const browser = await chromium.launch({ args: ARGS });
const SCENES = [
  ['ref', 'kind=none'], ['A_n1', 'kind=a&n=1'], ['B_n1', 'kind=b&n=1'], ['A_n40', 'kind=a&n=40'], ['B_n40', 'kind=b&n=40'],
  ['B_n40#2', 'kind=b&n=40'], ['A_n40#2', 'kind=a&n=40'], ['ref#2', 'kind=none'], ['B_n1#2', 'kind=b&n=1'], ['A_n1#2', 'kind=a&n=1'],
];
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
  const ft = s.ft.slice().sort((a, b) => a - b), gt = s.gt.slice().sort((a, b) => a - b), sum = s.ft.reduce((a, b) => a + b, 0);
  const row = { scene: name, fps: +(s.ft.length / (sum / 1000)).toFixed(1), p50: +q(ft, 0.5).toFixed(2), p95: +q(ft, 0.95).toFixed(2), worst: +ft[ft.length - 1].toFixed(1),
    over20: s.ft.filter((x) => x > 20).length, frames: s.ft.length, gpuMean: gt.length ? +(gt.reduce((a, b) => a + b, 0) / gt.length).toFixed(3) : null,
    gpuP50: gt.length ? +q(gt, 0.5).toFixed(3) : null, gpuP95: gt.length ? +q(gt, 0.95).toFixed(3) : null, gpuN: gt.length, calls: s.calls, tris: s.tris,
    progNew: s.programs - s.progsAtStart, progs: s.programs, texs: s.textures, cardTexMB: s.cardTexMB, loadMs, timer: s.timer, errs: errs.length };
  rows.push(row); console.log('ROW ' + JSON.stringify(row)); if (errs.length) console.log('ERRS ' + name + ' ' + errs.slice(0, 5).join(' | '));
  await page.close();
}
if (rows.length) {
  console.log('\nscene      fps     p50    p95   worst  >20ms  gpuMean gpuP95  calls  tris   newProg texMB(cards)');
  for (const r of rows) console.log([r.scene.padEnd(9), String(r.fps).padStart(7), String(r.p50).padStart(6), String(r.p95).padStart(6), String(r.worst).padStart(6),
    String(r.over20).padStart(6), String(r.gpuMean).padStart(8), String(r.gpuP95).padStart(7), String(r.calls).padStart(6), String(r.tris).padStart(6), String(r.progNew).padStart(8), String(r.cardTexMB).padStart(8)].join(' '));
  // Gates: new programs during timing must be 0 (warm-up proven); every scene under 500 calls and 0.5 M triangles; no page errors.
  for (const r of rows) {
    console.log(`GATE ${r.scene} warmup newPrograms ${r.progNew} ${r.progNew === 0 ? 'PASS' : 'FAIL'}`);
    console.log(`GATE ${r.scene} budget calls ${r.calls} tris ${r.tris} ${r.calls < 500 && r.tris < 500000 ? 'PASS' : 'FAIL'}`);
    console.log(`GATE ${r.scene} errors ${r.errs} ${r.errs === 0 ? 'PASS' : 'FAIL'}`);
  }
}
// Shots: A (left) and B (right) beside two suit boxes, time frozen at each atlas frame; clip round the pair (play size, no scaling).
await mkdir(`${OUT}/shots`, { recursive: true });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
for (let f = 0; f < 17; f++) {
  await page.goto(`${BASE}?shot=pair&frame=${f}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); await page.waitForTimeout(400);
  await page.screenshot({ path: `${OUT}/shots/pair_f${String(f).padStart(2, '0')}.png` });
}
await page.screenshot({ path: `${OUT}/shots/full_last.png` });
for (const [nm, qs] of [['heavy_A', 'kind=a&n=40'], ['heavy_B', 'kind=b&n=40']]) {
  await page.goto(`${BASE}?${qs}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); await page.waitForTimeout(1500);
  await page.screenshot({ path: `${OUT}/shots/${nm}.png` });
}
await writeFile(`${OUT}/rows.json`, JSON.stringify(rows, null, 1));
await browser.close(); server.close();
