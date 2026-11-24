// Screenshots of art/viewer/giants.html (art tool). Serves the repo root, saves one PNG per shot and shots.json (triangles and draw calls
// three.js drew per shot). Usage: node art/tools/giant_shoot.mjs OUTDIR [SET] [GIANTS]
//   SET quick (one giant: play, dormant, turn) | full (every giant: play awake / dormant, turns, slam windup, silhouettes; giant 0: all clips,
//   LODs, passes, the default sheet); GIANTS = comma list (default 0-11). Software GL: look only, no frame rate.
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/gshots', SET = process.argv[3] || 'quick';
const GS = (process.argv[4] || '0,1,2,3,4,5,6,7,8,9,10,11').split(',').map(Number);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/giants.html`;
await mkdir(OUT, { recursive: true });
const PLAY = [1920, 1080], SQ = [640, 640];
const shots = [];
const add = (name, q, [w, h]) => shots.push([name, q, w, h]);
for (const g of GS) {
  const p = `g${String(g).padStart(2, '0')}`;
  add(`${p}_play_awake`, `g=${g}&view=play`, PLAY);
  if (SET === 'quick') { add(`${p}_play_dormant`, `g=${g}&view=play&state=dormant`, PLAY); add(`${p}_turn_34`, `g=${g}&view=turn&yaw=35`, SQ); add(`${p}_turn_back`, `g=${g}&view=turn&yaw=160`, SQ); add(`${p}_slam`, `g=${g}&view=play&clip=slam&t=1.0`, PLAY); continue; }
  add(`${p}_play_dormant`, `g=${g}&view=play&state=dormant`, PLAY);
  add(`${p}_turn_34`, `g=${g}&view=turn&yaw=35`, SQ);
  add(`${p}_turn_back`, `g=${g}&view=turn&yaw=160`, SQ);
  add(`${p}_slam_windup`, `g=${g}&view=play&clip=slam&t=1.0`, PLAY);
  add(`${p}_sil`, `g=${g}&view=play&mode=sil&nobox=1`, PLAY);
  add(`${p}_sil_wide_lod2`, `g=${g}&view=wide&mode=sil&nobox=1&lod=2`, PLAY);
  add(`${p}_sil_wide`, `g=${g}&view=wide&mode=sil&nobox=1`, PLAY);
  add(`${p}_wide_lod2`, `g=${g}&view=wide&lod=2`, PLAY);
}
if (SET === 'full') {
  const g = GS[0], p = `g${String(g).padStart(2, '0')}`;
  for (const [c, ts] of [['wake', [0.4, 0.9, 1.2, 1.6, 2.0]], ['walk', [0, 0.25, 0.5, 0.75]], ['slam', [0.4, 1.12, 1.3]], ['sweep', [0.4, 1.2, 1.36, 1.5]], ['hit', [0.1]], ['fall', [0.3, 0.55, 0.8]]])
    for (const t of ts) add(`${p}_clip_${c}_${t}`, `g=${g}&view=play&clip=${c}&t=${t}`, PLAY);
  for (const l of [0, 1, 2]) add(`${p}_lod${l}`, `g=${g}&view=turn&yaw=35&lod=${l}`, SQ);
  for (const m of ['sil', 'flat', 'shade', 'tex']) add(`${p}_pass_${m}`, `g=${g}&view=turn&yaw=35&mode=${m}`, SQ);
  add(`${p}_play_default_sheet`, `g=${g}&view=play&sheet=default`, PLAY);
  add(`${p}_turn_front`, `g=${g}&view=turn&yaw=0`, SQ);
  add(`${p}_turn_side`, `g=${g}&view=turn&yaw=90`, SQ);
}
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const info = {};
for (const [name, q, w, h] of shots) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + q);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
  await page.screenshot({ path: `${OUT}/${name}.png` });
  info[name] = await page.evaluate(() => window.__info || null);
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok', JSON.stringify(info[name]));
  await page.close();
}
await writeFile(`${OUT}/shots.json`, JSON.stringify(info, null, 1));
await browser.close(); server.close();
