// PREP-AV real-GPU measurement (macOS runner, ANGLE Metal, vsync and frame limit off, 1920x1080, pixel ratio 1.25): probe/prepav reference
// vs the heavy fight through fxEvent (cards + sounds), forward then reversed in one job. Settle SETTLE_S, time TIMED_S. Prints ROW lines,
// a table and GATE lines (PASS / FAIL). Usage: OUT=dir node ci_prepav/perfprepav.mjs [--soft]
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const SOFT = process.argv.includes('--soft');
const SETTLE = Number(process.env.SETTLE_S || 6), TIMED = Number(process.env.TIMED_S || 20), OUT = process.env.OUT || 'prepav_out', K = process.env.K || '1';
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.jpg': 'image/jpeg', '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u));
  if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/probe/prepav/index.html`;
const ARGS = (SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit']).concat(['--enable-precise-memory-info']);
const browser = await chromium.launch({ args: ARGS });
const ONE = [['ref', 'mode=ref'], ['heavy', `mode=heavy&k=${K}`]];
const SCENES = [...ONE, ...ONE.slice().reverse().map(([n, q]) => [n + '#2', q])];
const qn = (a, p) => a[Math.min(a.length - 1, Math.floor(a.length * p))];
const mean = (a) => a.length ? a.reduce((x, y) => x + y, 0) / a.length : null;
const rows = [];
await mkdir(OUT, { recursive: true });
for (const [name, qs] of SCENES) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = []; page.on('pageerror', (e) => errs.push(e.message)); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  const t0 = Date.now();
  await page.goto(`${BASE}?${qs}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 180000 });
  if (qs.includes('heavy')) await page.mouse.click(960, 540);
  const loadMs = Date.now() - t0;
  // Sounds: wait until every sound and loop is rendered (cap 120 s), so rendering never overlaps the timed window.
  if (qs.includes('heavy')) await page.waitForFunction(() => { const s = window.__probe.stop(); return s.sndTotal > 0 && s.sndReady === s.sndTotal; }, null, { timeout: 120000, polling: 500 }).catch(() => {});
  await page.waitForTimeout(SETTLE * 1000);
  await page.evaluate(() => window.__probe.start()); await page.waitForTimeout(TIMED * 1000);
  const s = await page.evaluate(() => window.__probe.stop());
  const ft = s.ft.slice().sort((a, b) => a - b), gt = s.gt.slice().sort((a, b) => a - b), gc = s.gc.slice().sort((a, b) => a - b), sum = s.ft.reduce((a, b) => a + b, 0);
  const row = { scene: name, fps: +(s.ft.length / (sum / 1000)).toFixed(1), p50: +qn(ft, 0.5).toFixed(2), p95: +qn(ft, 0.95).toFixed(2), worst: +ft[ft.length - 1].toFixed(1),
    over20: s.ft.filter((x) => x > 20).length, frames: s.ft.length, gpuMean: gt.length ? +mean(gt).toFixed(3) : null, cardGpuMean: gc.length ? +mean(gc).toFixed(3) : null, cardGpuP95: gc.length ? +qn(gc, 0.95).toFixed(3) : null,
    liveMean: s.live.length ? +mean(s.live).toFixed(1) : 0, liveMax: s.live.length ? Math.max(...s.live) : 0, calls: s.calls, tris: s.tris, progNew: s.programs - s.progsAtStart, progs: s.programs,
    sndPerS: s.simS > 0 ? +(s.sounds / s.simS).toFixed(1) : 0, evPerS: s.simS > 0 ? +(s.events / s.simS).toFixed(1) : 0, unknown: s.unknown, ctx: s.ctx, sndReady: s.sndReady, sndTotal: s.sndTotal,
    heapMB: +s.heapMB.toFixed(2), warmed: s.warmed, long: s.long.reduce((o, x, i) => (i % 6 === 0 ? o.push([]) : 0, o[o.length - 1].push(+x.toFixed(i % 6 === 2 ? 2 : 1)), o), []).map((q) => `t${q[0]}:${q[1]}ms heap${q[2] >= 0 ? '+' : ''}${q[2]}MB ev${q[3]} workPrev${q[4]}ms late${q[5]}ms`).join(' '),
    gpuWorst: gt.length ? +gt[gt.length - 1].toFixed(2) : null, cardGpuWorst: gc.length ? +gc[gc.length - 1].toFixed(2) : null, longTasks: s.longTasks, longTaskMax: +s.longTaskMax.toFixed(1), longTaskList: s.longTaskList.map((x) => +x.toFixed(0)).join(','), loadMs, timer: s.timer, gpu: s.gpu, errs: errs.length };
  rows.push(row); console.log('ROW ' + JSON.stringify(row)); if (errs.length) console.log('ERRS ' + name + ' ' + errs.slice(0, 5).join(' | '));
  if (qs.includes('heavy') && !name.includes('#2')) await page.screenshot({ path: `${OUT}/heavy.jpg`, type: 'jpeg', quality: 80 });
  await page.close();
}
console.log('\nscene      fps     p50    p95   worst >20ms stageGPU cardGPU cardP95 live(mean/max) calls  tris newProg snd/s ev/s heapMB long');
for (const r of rows) console.log([r.scene.padEnd(9), String(r.fps).padStart(7), String(r.p50).padStart(6), String(r.p95).padStart(6), String(r.worst).padStart(6), String(r.over20).padStart(5),
  String(r.gpuMean).padStart(8), String(r.cardGpuMean).padStart(7), String(r.cardGpuP95).padStart(7), (r.liveMean + '/' + r.liveMax).padStart(14), String(r.calls).padStart(5), String(r.tris).padStart(6),
  String(r.progNew).padStart(7), String(r.sndPerS).padStart(5), String(r.evPerS).padStart(5), String(r.heapMB).padStart(6), ' ' + r.long].join(' '));
let nFail = 0;
const G = (name, ok, detail) => { if (!ok) nFail++; console.log(`GATE ${name} ${detail} ${ok ? 'PASS' : 'FAIL'}`); };
// Real fps only from a real graphics chip (owner rule 25): every scene drew on a renderer that is named and is not a software one.
const SOFT_GPU = /swiftshader|llvmpipe|softpipe|software|basic render/i;
G('gpu real', rows.length > 0 && rows.every((r) => r.gpu && !SOFT_GPU.test(r.gpu)), `renderer "${rows.length ? rows[0].gpu : ''}"`);
// Passed on nothing is a FAIL: every scene measured, every scene with frames (and GPU samples when the timer exists).
G('scenes measured', rows.length === 4, `rows ${rows.length} of 4`);
for (const r of rows) G(`${r.scene} frames measured`, r.frames > 100 && (!r.timer || r.gpuMean !== null), `frames ${r.frames} gpu ${r.gpuMean}`);
for (const r of rows) {
  G(`${r.scene} errors`, r.errs === 0, `errors ${r.errs}`);
  G(`${r.scene} budget`, r.calls < 500 && r.tris < 500000, `calls ${r.calls} tris ${r.tris}`);
  G(`${r.scene} warmup`, r.progNew === 0, `newPrograms ${r.progNew}`);
  if (!r.scene.startsWith('heavy')) continue;
  G(`${r.scene} fps`, r.fps >= 60 && r.p95 <= 25 && r.worst <= 100, `fps ${r.fps} p95 ${r.p95} worst ${r.worst}`);
  G(`${r.scene} live cards 40-60`, r.liveMean >= 40 && r.liveMean <= 60, `mean ${r.liveMean} max ${r.liveMax}`);
  G(`${r.scene} card pass GPU`, r.cardGpuMean !== null && r.cardGpuMean <= 2.0, `mean ${r.cardGpuMean} ms (<= 2.0)`);
  G(`${r.scene} sounds`, r.ctx === 'running' && r.sndReady === r.sndTotal && r.sndPerS >= 5 && r.unknown === 0, `ctx ${r.ctx} ready ${r.sndReady}/${r.sndTotal} ${r.sndPerS}/s unknown ${r.unknown}`);
  G(`${r.scene} draws`, r.calls - (rows.find((x) => x.scene === 'ref').calls) <= 3, `cards add ${r.calls - rows.find((x) => x.scene === 'ref').calls} calls (<= 3)`);
}
const ratio = (a, b) => +(rows.find((x) => x.scene === a).fps / rows.find((x) => x.scene === b).fps).toFixed(3);
const r1 = ratio('heavy', 'ref'), r2 = ratio('heavy#2', 'ref#2');
G('heavy vs ref same job', (r1 + r2) / 2 >= 0.85, `fps ratio ${r1} / ${r2} (mean >= 0.85)`);
await writeFile(`${OUT}/rows.json`, JSON.stringify(rows, null, 1));
// A failed gate fails the step (the tick then means something; the FAIL lines stay the proof).
console.log(`GATES ${nFail ? 'FAIL ' + nFail : 'PASS'}`);
process.exitCode = nFail ? 1 : 0;
await browser.close(); server.close();
