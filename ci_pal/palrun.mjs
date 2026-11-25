// PREP-PAL runner (GitHub runners only). Serves the repo, drives ci_pal/pal.html in Playwright Chromium.
//   node ci_pal/palrun.mjs checks            Linux SwiftShader: P1-P20 (correctness and counts; no fps)
//   node ci_pal/palrun.mjs mutants 0/3       Linux: mutant shard 0 of 3 (each mutant served in place of src/palace_art.js must fail its check)
//   node ci_pal/palrun.mjs perf              macOS real GPU: reference (the game) / palace art heaviest view medium and low / control / reference,
//                                            fresh browser per scene, 6 s settle + 20 s timed; P14 memory cycles on the real GPU.
// Every line a gate prints starts with PASS or FAIL; the last line is RESULT N of N. Gates fail on 0 measured.
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const MODE = process.argv[2] || 'checks', ARG = process.argv[3] || '', OUT = process.env.OUT || 'pal_out', SOFT = MODE !== 'perf' || process.argv.includes('--soft');
const SETTLE = Number(process.env.SETTLE_S || 6), TIMED = Number(process.env.TIMED_S || 20);
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary' };
// Mutants: [name, check it must fail, text in src/palace_art.js, replacement]. A mutant whose text is not found counts as a failure.
const MUTANTS = [
  ['fow-inst', 'P10', 'paW = instanceMatrix * paW;', 'paW = paW;'],
  ['no-inst-dispose', 'P14', 'for (const im of art.inst) im.dispose();', ''],
  ['no-warm-rack', 'P11', '  scene.add(g);\n', '\n'],
  ['wall-in', 'P5', 'wallIn: 0.25,', 'wallIn: 0.6,'],
  ['no-spread', 'P3', 'const dx = i === 0 ? 0 : spreadOf(nd, b0)', 'const dx = 0'],
  ['auto-matrix', 'P4', 'function still(art, o) { o.matrixAutoUpdate = false;', 'function still(art, o) { o.matrixAutoUpdate = true;'],
  ['burn-noop', 'P12', 'B[i].material = on ? B[i + 2] : B[i + 1];', 'B[i].material = B[i + 1];'],
  ['reset-vat', 'P12', "else if (p.kind === 'vat') setVat(p, 0);", "else if (p.kind === 'vat') {}"],
  ['clock-inverted', 'P13', 'mixer.setTime(Math.min(dur * s / steps, dur - 1e-4));', 'mixer.setTime(Math.min(dur * (1 - s / steps), dur - 1e-4));'],
  ['terrace-all', 'P17', 'for (const [a, b] of lakeRuns(r, side, rooms))', 'for (const [a, b] of [edgeSpan(r, side)])'],
  ['shadow-all', 'P15', 'cast = !C.noShadow.some((p) => piece.startsWith(p));', 'cast = true;'],
  ['rack-no-solid', 'P16', 'racks.push(mat4(x, 0, zp, 0)); art.solids.push(box);', 'racks.push(mat4(x, 0, zp, 0));'],
  ['plants-flood', 'P7', 'plants: { max: 360,', 'plants: { max: 70000,'],
  ['missing-file', 'P1', "'flag_8', 'plant_wheat'", "'flag_8x', 'plant_wheat'"],
  ['mat-table', 'P2', "    palRoof: { tex: 'roof_tile', rough: 0.85 },\n", ''],
  ['pillar-off', 'P6', 'spots.pillars.map(([x, z]) => mat4(x, 0, z, 0))', 'spots.pillars.map(([x, z]) => mat4(x + 0.5, 0, z, 0))'],
  ['light', 'P8', "art.group.name = 'palArt_' + r.id; kit.rooms++;", "art.group.name = 'palArt_' + r.id; kit.rooms++; art.group.add(new THREE.PointLight(0xffffff, 1));"],
  ['aniso', 'P9', 'const an = Math.min(C.aniso, o.maxAniso || C.aniso);', 'const an = 16;'],
  ['merc-off', 'P20', 'const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, rot', 'const cx = (x0 + x1) / 2 + 1, cz = (z0 + z1) / 2, rot'],
  ['replace-key', 'P18', "core: ['palWall', 'palPillar', 'pillar', 'gold']", "core: ['palWall', 'palPillar', 'pillar', 'throne']"],
  ['geo-copies', 'P19', 'const im = new THREE.InstancedMesh(part.geo,', 'const im = new THREE.InstancedMesh(part.geo.clone(),'],
];
let MUT = null;
const server = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u === '/' ? 'index.html' : u));
  if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  try {
    let b = await readFile(p);
    if (MUT && u === '/src/palace_art.js') b = Buffer.from(b.toString().replace(MUT[2], MUT[3]));
    res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b);
  } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/`;
const ARGS = (SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit']).concat(['--js-flags=--expose-gc', '--enable-precise-memory-info']);
await mkdir(OUT + '/shots', { recursive: true });
const lines = []; let pass = 0, fail = 0;
const gate = (ok, line) => { const s = (ok ? 'PASS ' : 'FAIL ') + line; console.log(s); lines.push(s); if (ok) pass++; else fail++; };
async function open(q, vp) {
  const browser = await chromium.launch({ args: ARGS });
  const page = await browser.newPage({ viewport: vp || { width: 1920, height: 1080 }, deviceScaleFactor: 1 }), errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));
  const t0 = Date.now();
  await page.goto(BASE + q);
  await page.waitForFunction(() => window.__ready === true || !!window.__err, null, { timeout: 900000, polling: 500 });
  const err = await page.evaluate(() => window.__err || '');
  return { browser, page, errs, err, loadMs: Date.now() - t0 };
}
const renderer = async (page) => page.evaluate(() => { const c = document.createElement('canvas'), gl = c.getContext('webgl2'), d = gl && gl.getExtension('WEBGL_debug_renderer_info'); return d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'unknown'; });

if (MODE === 'checks') {
  const o = await open('ci_pal/pal.html?mode=checks', { width: 1280, height: 720 });
  console.log('RENDERER ' + await renderer(o.page) + ' load+checks ' + o.loadMs + ' ms');
  if (o.err) gate(false, 'page error ' + o.err.slice(0, 300));
  const cs = o.err ? [] : await o.page.evaluate(() => window.__checks || []);
  for (const c of cs) { if (c.info) { console.log(c.line); lines.push(c.line); continue; } gate(c.ok, c.line.replace(/^(PASS|FAIL) /, '')); }
  if (!cs.filter((c) => !c.info).length) gate(false, 'checks: none ran');
  if (o.errs.length) gate(false, 'page errors: ' + o.errs.slice(0, 3).join(' | '));
  await o.page.screenshot({ path: OUT + '/shots/checks_end.png' }).catch(() => {});
  await o.browser.close();
} else if (MODE === 'mutants') {
  const [k, n] = (ARG || '0/1').split('/').map(Number), src = (await readFile(join(ROOT, 'src/palace_art.js'))).toString();
  for (let i = 0; i < MUTANTS.length; i++) {
    if (i % n !== k) continue;
    MUT = MUTANTS[i]; const [name, id, from] = MUT;
    if (!src.includes(from)) { gate(false, `mutant ${name}: text not found (not applied)`); continue; }
    const o = await open('ci_pal/pal.html?mode=checks&only=' + id, { width: 1280, height: 720 });
    const cs = o.err ? [] : await o.page.evaluate(() => window.__checks || []), c = cs.find((x) => x.id === id && !x.info);
    const caught = !!o.err || (c && !c.ok);
    gate(caught, `mutant ${name} -> ${id}: ${o.err ? 'page error ' + o.err.slice(0, 120) : c ? c.line.slice(0, 220) : 'check did not run'}`);
    await o.browser.close();
  }
  MUT = null;
} else if (MODE === 'perf') {
  // Real GPU: the game's reference scene (as prep-chr / perfgpu: lock, tier medium, no bots) twice around the palace art views.
  const scenes = (process.env.SCENES || 'reference,pal_med,pal_low,webglmin,reference').split(','), rows = [];
  for (const name of scenes) {
    const q = name === 'reference' ? '?lock&tier=medium&bots=0' : name === 'pal_med' ? 'ci_pal/pal.html?mode=perf&tier=medium' : name === 'pal_low' ? 'ci_pal/pal.html?mode=perf&tier=low' : 'ci_pal/webglmin.html';
    const o = await open(q);
    if (o.err) { gate(false, `${name}: page error ${o.err.slice(0, 200)}`); await o.browser.close(); continue; }
    if (name === 'reference') await o.page.evaluate(() => { if (window.__game && __game.setSeed) { __game.setSeed(12345); __game.reset(); } });
    const r = await o.page.evaluate(async ({ SETTLE, TIMED }) => {
      const wait = (s) => new Promise((res) => setTimeout(res, s * 1000)); await wait(SETTLE); if (window.gc) window.gc();
      const heap = () => (performance.memory ? +(performance.memory.usedJSHeapSize / 1048576).toFixed(1) : -1), G = window.__gl || null;
      const l0 = G ? G.link : 0, h0 = heap(), d = []; let last = 0, run = true;
      await new Promise((res) => { const f = (t) => { if (last) d.push(t - last); last = t; if (run) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); setTimeout(() => { run = false; }, TIMED * 1000); });
      d.sort((a, b) => a - b); const F = d.length, sum = d.reduce((a, b) => a + b, 0), V = window.__probe && window.__probe.view;
      return { frames: F, fps: F ? +(F / (sum / 1000)).toFixed(1) : 0, p50: F ? +d[Math.floor(F * 0.5)].toFixed(1) : 0, p95: F ? +d[Math.floor(F * 0.95)].toFixed(1) : 0, worst: F ? +d[F - 1].toFixed(1) : 0,
        over20: F ? +(100 * d.filter((x) => x > 20).length / F).toFixed(1) : 0, links: G ? G.link - l0 : -1, heap0: h0, heap1: heap(),
        view: V ? { id: V.id, counts: V.counts, steady: V.steady, prog0: V.prog0, prog1: V.programs(), props: V.propsN, doors: V.doorsN } : null };
    }, { SETTLE, TIMED });
    const row = { scene: name, loadMs: o.loadMs, errs: o.errs.length, gpu: await renderer(o.page), ...r }; rows.push(row); console.log('ROW ' + JSON.stringify(row));
    await o.page.screenshot({ path: `${OUT}/shots/${name}_${rows.length}.png` }).catch(() => {});
    await o.browser.close();
  }
  const gpu = rows[0] ? rows[0].gpu : 'none'; console.log('RENDERER ' + gpu + (/swiftshader|llvmpipe|software/i.test(gpu) ? '  (NOT a real GPU)' : ''));
  const refs = rows.filter((x) => x.scene === 'reference' && x.frames > 0), refP95 = refs.length ? refs.reduce((a, x) => a + x.p95, 0) / refs.length : 0, refFps = refs.length ? refs.reduce((a, x) => a + x.fps, 0) / refs.length : 0;
  gate(refs.length === 2 && !/swiftshader|llvmpipe|software/i.test(gpu), `reference measured twice on a real GPU: ${refs.map((x) => x.fps + ' fps p95 ' + x.p95).join(' / ')} (${gpu})`);
  for (const x of rows.filter((y) => y.scene.startsWith('pal_'))) {
    const lim = Math.max(refP95 * 1.25, refP95 + 2), V = x.view || {};
    gate(x.frames > 0 && V.props > 0 && refP95 > 0 && x.p95 <= lim && x.p95 <= 16.7, `${x.scene} ${V.id}: ${x.fps} fps p95 ${x.p95} ms (limit ${lim.toFixed(1)} = max(1.25 x ref ${refP95.toFixed(1)}, ref + 2), and 16.7) worst ${x.worst} ms; ref ${refFps.toFixed(1)} fps`);
    gate(x.frames > 0 && x.worst < 100, `${x.scene}: worst frame ${x.worst} ms < 100 (over 20 ms: ${x.over20} %)`);
    gate(x.frames > 0 && x.links === 0 && V.prog0 > 0 && V.prog1 === V.prog0, `${x.scene}: programs linked in play ${x.links} (programs ${V.prog0} -> ${V.prog1}), ${V.props} props and ${V.doors} doors toggling every 0.5 s`);
    gate(V.counts && V.counts.calls > 0 && V.counts.calls < 500 && V.counts.tris < 500000, `${x.scene}: GL draws ${V.counts && V.counts.calls} (steady ${V.steady && V.steady.calls}), triangles ${V.counts && V.counts.tris} (shadow frame) < 500 / 0.5M`);
  }
  // Memory cycles on the real GPU (P14) with the JS heap.
  const o = await open('ci_pal/pal.html?mode=checks&only=P14');
  const cs = o.err ? [] : await o.page.evaluate(() => window.__checks || []), c = cs.find((y) => y.id === 'P14');
  gate(!o.err && c && c.ok, 'real GPU ' + (c ? c.line.slice(0, 400) : o.err || 'P14 did not run'));
  await o.browser.close();
  const t = ['scene        fps     p50   p95   worst  >20ms%  draws  tris     links heapMB'];
  for (const x of rows) t.push([x.scene.padEnd(12), String(x.fps).padStart(6), String(x.p50).padStart(6), String(x.p95).padStart(5), String(x.worst).padStart(6), String(x.over20).padStart(6),
    String(x.view && x.view.counts ? x.view.counts.calls : '').padStart(6), String(x.view && x.view.counts ? x.view.counts.tris : '').padStart(8), String(x.links).padStart(5), (x.heap0 + '-' + x.heap1).padStart(11)].join(' '));
  console.log(t.join('\n')); await writeFile(OUT + '/perf_table.txt', t.join('\n') + '\n');
}
console.log(`RESULT ${pass} of ${pass + fail}${fail ? ' (FAIL)' : ''}`);
await writeFile(OUT + '/result.txt', lines.join('\n') + `\nRESULT ${pass} of ${pass + fail}\n`);
server.close(); process.exit(fail || !pass ? 1 : 0);
