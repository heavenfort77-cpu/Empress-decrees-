// Screenshots of art/viewer/beast.html (art tool). Serves the repo root and saves one PNG per shot.
// Usage: node art/tools/shoot_viewer.mjs OUTDIR [MODEL] [EXTRA]   (MODEL beast (default) | ding | vat; EXTRA = query added to every shot,
// e.g. metal=0.2; software GL locally: look only, no frame rate)
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/shots', MODEL = process.argv[3] || 'beast', EXTRA = process.argv[4] ? '&' + process.argv[4] : '';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/beast.html`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const TURN = (st) => [['turn_front', `view=turn&yaw=0${st}`, 640, 640], ['turn_34', `view=turn&yaw=35${st}`, 640, 640], ['turn_side', `view=turn&yaw=90${st}`, 640, 640], ['turn_back', `view=turn&yaw=180${st}`, 640, 640]];
const PASSES = [['pass_sil', 'view=turn&yaw=35&mode=sil', 640, 640], ['pass_flat', 'view=turn&yaw=35&mode=flat', 640, 640], ['pass_shade', 'view=turn&yaw=35&mode=shade', 640, 640], ['pass_tex', 'view=turn&yaw=35&mode=tex', 640, 640]];
const SHOTS = {
  beast: [['play', 'view=play', 1920, 1080], ['wide', 'view=wide', 1920, 1080], ['strike_windup', 'view=play&t=0.6', 1920, 1080], ...TURN(''), ...PASSES, ['lods', 'view=lods', 1280, 640]],
  ding: [['play_lit', 'view=play&state=lit', 1920, 1080], ['play_dry', 'view=play&state=dry', 1920, 1080], ['wide', 'view=wide', 1920, 1080], ...TURN(''),
    ['top_lit', 'view=turn&yaw=20&pitch=55&state=lit', 640, 640], ['top_dry', 'view=turn&yaw=20&pitch=55&state=dry', 640, 640], ...PASSES, ['lods', 'view=lods', 1280, 640],
    ...[0, 1, 2, 3, 4, 5, 6, 7, 8].map((i) => [`school_${i}`, `view=turn&yaw=20&pitch=30&school=${i}`, 320, 320])],
  vat: [['play_intact', 'view=play&state=intact', 1920, 1080], ['play_cracked', 'view=play&state=cracked', 1920, 1080], ['play_shards', 'view=play&state=shards', 1920, 1080], ['wide', 'view=wide', 1920, 1080],
    ...TURN(''), ['turn_cracked', 'view=turn&yaw=35&state=cracked', 640, 640], ['turn_shards', 'view=turn&yaw=35&pitch=40&state=shards', 640, 640], ...PASSES, ['lods', 'view=lods', 1280, 640]],
}[MODEL];
for (const [name, q, w, h] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?model=' + MODEL + '&' + q + EXTRA);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  await page.screenshot({ path: `${OUT}/${name}.png` });
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 120) : 'ok');
  await page.close();
}
await browser.close(); server.close();
