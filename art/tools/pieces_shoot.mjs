// Screenshots of art/viewer/pieces.html (PIECES round, art tool). Serves the repo root and saves one PNG per shot; prints one PASS/FAIL line
// (a shot fails on a page error, a GLB that does not load in three's GLTFLoader, or a clip the GLB does not carry).
// Usage: node art/tools/pieces_shoot.mjs OUTDIR   (software GL on the runner: look only, no frame rate)
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/pshots';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/pieces.html`;
await mkdir(OUT, { recursive: true });
// CONFIG: close-up framing per piece: [distance m, look height m, pitch deg]
const CLOSE = { crab: [3.6, 0.5, 15], wanderer: [5.4, 1.35, 12], plate: [1.7, 0.08, 35], leader_crown: [2.4, 0.45, 12], mo_wall: [7.0, 1.2, 15], decree_mark: [2.2, 0.45, 8], kaymuse: [5.0, 0.85, 10] };
const S = 720, FULL = [1920, 1080];
const shots = [];
for (const [id, [d, ly, p]] of Object.entries(CLOSE)) {
  const q = `scene=one&model=${id}&dist=${d}&ly=${ly}`;
  for (const [n, yaw] of [['front', 0], ['34', 35], ['side', 90], ['back', 180]]) shots.push([`${id}_turn_${n}`, `${q}&pitch=${p}&yaw=${yaw}`, S, S]);
  shots.push([`${id}_top`, `${q}&pitch=40&yaw=20`, S, S], [`${id}_sil`, `${q}&pitch=${p}&yaw=35&mode=sil`, S, S]);
  shots.push([`${id}_lods`, `scene=one&model=${id}&lod=all&dist=${d * 2.4}&ly=${ly}&lx=${id === 'mo_wall' ? 5 : id === 'kaymuse' ? 4 : d * 0.6}&pitch=${p}&yaw=0`, 1440, S]);
}
// clips: four poses each (same camera)
for (const [id, clip, ts] of [['crab', 'move', [0, 0.2, 0.4, 0.6]], ['crab', 'idle', [0, 0.6, 1.2, 1.8]], ['wanderer', 'move', [0, 0.4, 0.8, 1.2]], ['wanderer', 'idle', [0, 0.8, 1.6, 2.4]]]) {
  const [d, ly, p] = CLOSE[id];
  ts.forEach((t, i) => shots.push([`${id}_${clip}_${i}`, `scene=one&model=${id}&dist=${d}&ly=${ly}&pitch=${p}&yaw=60&clip=${clip}&t=${t}`, S, S]));
}
// silhouettes at the game camera, same place and scale (crab against wanderer: pieces_measure.py)
for (const id of ['crab', 'wanderer']) for (const yaw of [0, 90]) shots.push([`sil_${id}_${yaw}`, `scene=one&model=${id}&view=cam&yaw=${yaw}&mode=sil`, 960, 960]);
// play size on the hall floor beside in-game art, and one mask per piece (same camera)
shots.push(['lineup_play', 'scene=lineup', ...FULL], ['lineup_calm', 'scene=lineup&floor=calm', ...FULL], ['lineup_wide', 'scene=lineup&view=wide', ...FULL], ['lineup_move', 'scene=lineup&clip=move&t=0.2', ...FULL]);
for (const id of ['crab', 'wanderer', 'plate', 'leader_crown', 'mo_wall', 'decree_mark']) shots.push([`mask_${id}`, `scene=lineup&mode=mask&mask=${id}`, ...FULL]);
// Kaymuse on the throne: play size (three framings), close-ups, the bead curtain, idle poses, masks
shots.push(['throne_play', 'scene=throne&view=play', ...FULL], ['throne_approach', 'scene=throne&view=approach', ...FULL], ['throne_wide', 'scene=throne&view=wide', ...FULL],
  ['mask_kaymuse_play', 'scene=throne&view=play&mode=mask&mask=kaymuse', ...FULL], ['mask_kaymuse_approach', 'scene=throne&view=approach&mode=mask&mask=kaymuse', ...FULL],
  ['throne_close_front', 'scene=throne&view=close&yaw=0', 960, 960], ['throne_close_34', 'scene=throne&view=close&yaw=35', 960, 960], ['throne_close_side', 'scene=throne&view=close&yaw=80', 960, 960],
  ['throne_close_cam', 'scene=throne&view=close&yaw=0&pitch=40&dist=6', 960, 960],
  ['beads_front', 'scene=throne&view=close&yaw=0&dist=1.9&ly=3.62&pitch=5', S, S], ['beads_34', 'scene=throne&view=close&yaw=40&dist=1.9&ly=3.62&pitch=5', S, S],
  ['beads_idle_1', 'scene=throne&view=close&yaw=70&dist=1.9&ly=3.62&pitch=5&clip=idle&t=1', S, S], ['beads_idle_3', 'scene=throne&view=close&yaw=70&dist=1.9&ly=3.62&pitch=5&clip=idle&t=3', S, S]);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
let bad = 0;
for (const [name, q, w, h] of shots) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e)));
  page.on('console', (m) => { if (m.type() === 'error' && !/Failed to load resource/.test(m.text())) errs.push(m.text()); });
  page.on('response', (rs) => { if (rs.status() >= 400 && !/favicon/.test(rs.url())) errs.push(`HTTP ${rs.status()} ${rs.url().split('/').slice(-2).join('/')}`); });
  try {
    await page.goto(BASE + '?' + q);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
    const st = await page.evaluate(() => [window.__err || '', window.__noclip || '']);
    if (st[0]) errs.push('load: ' + st[0]); if (st[1]) errs.push('clip missing: ' + st[1]);
    await page.screenshot({ path: `${OUT}/${name}.png` });
  } catch (e) { errs.push(String(e).slice(0, 160)); }
  if (errs.length) { bad++; console.log(`FAIL shot ${name}: ${errs[0].slice(0, 200)}`); }
  await page.close();
}
console.log(`${bad ? 'FAIL' : 'PASS'} shots: ${shots.length - bad} of ${shots.length} rendered in three's GLTFLoader without errors`);
await browser.close(); server.close();
