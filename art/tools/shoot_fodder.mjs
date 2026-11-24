// Screenshots of art/viewer/fodder.html (worker W5; copied from shoot_viewer.mjs). Serves the repo root, saves one PNG per shot and
// prints draw calls and triangles per shot. Usage: node art/tools/shoot_fodder.mjs OUTDIR [--quick]
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/fshots';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/fodder.html`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const UNITS = ['zu', 'nu', 'dun', 'che', 'wz', 'ls', 'fs', 'ss', 'qs'];
const SHOTS = [
  ['lineup_guard', 'view=lineup&faction=guard', 1920, 1080], ['lineup_rebels', 'view=lineup&faction=rebels', 1920, 1080],
  ['lineup_all_wide', 'view=lineup&faction=all&dist=22', 1920, 1080], ['lineup_all_sil', 'view=lineup&faction=all&dist=22&mode=sil&yaw=35', 1920, 1080],
  ['lineup_guard_wide', 'view=lineup&faction=guard&dist=22', 1920, 1080], ['lineup_guard_sil', 'view=lineup&faction=guard&mode=sil', 1920, 1080],
  ['schools', 'view=schools', 1920, 1080], ['schools_sil', 'view=schools&mode=sil', 1920, 1080],
];
// FIX-A: tread scroll proof (same view, belt scrolled by half a link and by one link: the links move, the seam does not show)
for (const [n, m] of [['0', 0], ['half', 0.0625], ['link', 0.125]]) SHOTS.push([`che_scroll_${n}`, `view=turn&unit=che&yaw=90&scroll=${m}`, 560, 640]);
for (const u of UNITS) {
  for (const y of [0, 35, 90, 180]) SHOTS.push([`${u}_turn_${y}`, `view=turn&unit=${u}&yaw=${y}`, 560, 640]);
  SHOTS.push([`${u}_tell`, `view=tell&unit=${u}`, 1280, 640], [`${u}_lods`, `view=lods&unit=${u}`, 1280, 640]);
}
const info = {};
for (const [name, q, w, h] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + q);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 }); } catch { errs.push('timeout'); }
  await page.screenshot({ path: `${OUT}/${name}.png` });
  info[name] = await page.evaluate(() => window.__info || null);
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok', JSON.stringify(info[name]));
  await page.close();
}
await writeFile(`${OUT}/shots.json`, JSON.stringify(info, null, 1));
await browser.close(); server.close();
