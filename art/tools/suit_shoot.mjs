// Screenshots of art/viewer/suits.html (art tool). Serves the repo root and saves one PNG per shot.
// Usage: node art/tools/suit_shoot.mjs OUTDIR INFO.json [ids]   (INFO = suits_info.json from suit_blender.py: windup times)
// Software GL on the runner: look only, no frame rate.
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/shots';
const INFO = JSON.parse(await readFile(process.argv[3], 'utf8'));
const IDS = process.argv[4] ? process.argv[4].split(',') : INFO.map((s) => s.id);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/suits.html`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const SHOTS = [];
for (const id of IDS) {
  const w = INFO.find((s) => s.id === id).tell;
  SHOTS.push([`${id}_front`, `id=${id}&view=turn&yaw=0`, 640, 640], [`${id}_34`, `id=${id}&view=turn&yaw=35`, 640, 640],
    [`${id}_side`, `id=${id}&view=turn&yaw=90`, 640, 640], [`${id}_back`, `id=${id}&view=turn&yaw=180`, 640, 640],
    [`${id}_play`, `id=${id}&view=play&yaw=20`, 1920, 1080], [`${id}_windup`, `id=${id}&view=turn&yaw=35&t=${w}`, 640, 640],
    [`${id}_strike`, `id=${id}&view=turn&yaw=35&t=${(w + 0.12).toFixed(2)}`, 640, 640], [`${id}_lods`, `id=${id}&view=lods&yaw=35`, 1280, 640]);
  for (const m of ['sil', 'flat', 'shade']) SHOTS.push([`${id}_pass_${m}`, `id=${id}&view=turn&yaw=35&mode=${m}`, 640, 640]);
}
const all = IDS.join(',');
SHOTS.push(['lineup_play', `ids=${all}&view=play`, 1920, 1080], ['lineup_wide', `ids=${all}&view=wide`, 1920, 1080],
  ['lineup_sil_front', `ids=${all}&view=play&mode=sil`, 1920, 1080], ['lineup_play_rim', `ids=${all}&view=play&rim=1`, 1920, 1080], ['lineup_sil_34', `ids=${all}&view=play&yaw=35&mode=sil`, 1920, 1080]);
for (const [name, q, w, h] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + q);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 }); await page.screenshot({ path: `${OUT}/${name}.png` }); }
  catch (e) { errs.push('timeout'); }
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
await browser.close(); server.close();
