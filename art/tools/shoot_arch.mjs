// Screenshots of art/viewer/arch.html (W2 room scene sheets and piece views; art tool). Serves the repo root, saves one PNG per shot and
// stats.json (draw calls and triangles per shot, with and without the shadow pass). Usage: node art/tools/shoot_arch.mjs OUTDIR [set]
// set: rooms (default: every room wide + play, hall burnt, hall locked, core up) | pieces (each GLB alone, 3/4 view) | all
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/arch_shots', SET = process.argv[3] || 'all';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/arch.html`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const SHOTS = [];
if (SET === 'rooms' || SET === 'all') {
  for (const room of ['hall', 'court', 'corridor', 'garden', 'bridge', 'core']) {
    SHOTS.push([`${room}_wide`, `room=${room}&view=wide`, 1920, 1080], [`${room}_play`, `room=${room}&view=play`, 1920, 1080]);
  }
  SHOTS.push(['hall_burnt_wide', 'room=hall&view=wide&burnt=1', 1920, 1080], ['hall_burnt_play', 'room=hall&view=play&burnt=1', 1920, 1080],
    ['hall_locked_play', 'room=hall&view=play&locked=1', 1920, 1080], ['core_up', 'room=core&view=up', 1920, 1080]);
}
if (SET === 'pieces' || SET === 'all') {
  for (const p of ['terrace_edge', 'wall_seg', 'wall_mural_seg', 'wall_low', 'door', 'pillar', 'eave_seg', 'que_pair', 'wall_walk_seg', 'parapet_seg', 'walk_post', 'bridge_bay_8', 'throne_dais', 'lake_rubble', 'debris', 'slip_rack'])
    SHOTS.push([`piece_${p}`, `piece=${p}&yaw=30`, 960, 720]);
}
const stats = {};
for (const [name, q, w, h] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + q);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); } catch (e) { errs.push('timeout'); }
  await page.screenshot({ path: `${OUT}/${name}.png` });
  stats[name] = await page.evaluate(() => window.__stats || null);
  console.log(name, JSON.stringify(stats[name]), errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
await writeFile(`${OUT}/stats.json`, JSON.stringify(stats, null, 1));
await browser.close(); server.close();
