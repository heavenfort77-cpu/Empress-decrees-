// Screenshots of art/viewer/apex.html (W4 art tool). Serves the repo root, saves one PNG per shot into OUTDIR.
// Usage: node art/tools/apex_shoot.mjs OUTDIR   (software GL on CI: look only, no frame rate)
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/apex_shots';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/apex.html`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const S = [];
for (const m of ['tiger', 'stalker', 'howler']) for (const [n, y] of [['front', 0], ['34', 35], ['side', 90], ['back', 180]]) S.push([`${m}_${n}`, `model=${m}&yaw=${y}`, 640, 640]);
S.push(['tiger_dormant_34', 'model=tiger&yaw=35&state=dormant', 640, 640], ['tiger_awake_34', 'model=tiger&yaw=35&state=awake&clip=idle', 640, 640]);
for (const t of [0, 1.4, 2.1, 2.6, 3.0]) S.push([`tiger_wake_${t}`, `model=tiger&yaw=35&state=${t < 0.8 ? 'dormant' : 'awake'}&clip=wake&t=${t}`, 480, 480]);
S.push(['tiger_pounce_rest', 'model=tiger&yaw=90&clip=pounce&t=0', 640, 640], ['tiger_pounce_windup', 'model=tiger&yaw=90&clip=pounce&t=0.5', 640, 640], ['tiger_pounce_leap', 'model=tiger&yaw=90&clip=pounce&t=0.85', 640, 640]);
S.push(['tiger_roar_windup', 'model=tiger&yaw=25&clip=roar&t=0.5', 640, 640]);
for (const m of ['stalker', 'howler']) S.push([`${m}_attack_rest`, `model=${m}&yaw=90&clip=attack&t=0`, 480, 480], [`${m}_attack_windup`, `model=${m}&yaw=90&clip=attack&t=0.5`, 480, 480], [`${m}_move`, `model=${m}&yaw=35&clip=move&t=0.3`, 480, 480]);
for (const m of ['tiger', 'stalker', 'howler']) S.push([`${m}_lods`, `model=${m}&view=lods`, 1280, 480], [`${m}_sil`, `model=${m}&yaw=35&mode=sil`, 480, 480]);
S.push(['play', 'view=play', 1920, 1080], ['statue', 'view=statue', 1920, 1080]);
S.push(['schools_awake', 'model=tiger&view=row&state=awake', 1280, 960], ['schools_dormant', 'model=tiger&view=row&state=dormant', 1280, 960]);
let bad = 0;
for (const [name, q, w, h] of S) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  try {
    await page.goto(BASE + '?' + q);
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
    await page.screenshot({ path: `${OUT}/${name}.png` });
  } catch (e) { errs.push(String(e).slice(0, 160)); }
  if (errs.length) bad++;
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
console.log(`shots ${S.length - bad} of ${S.length} ok`);
await browser.close(); server.close();
