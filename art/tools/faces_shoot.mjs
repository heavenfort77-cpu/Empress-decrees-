// Face masks round 2 (FACES worker): screenshots of art/viewer/faces.html for guard zu and giant 00, now and M, close (head and shoulders,
// 3/4) and play size (FOV 50, pitch 40, 10.5 m, 1920 x 1080). Serves the repo root; writes OUTDIR/<c>_<o>_<view>.png and shots.json
// (calls, triangles, screen boxes, contrast probes per shot). Software GL on the runner: look only, no frame rate.
// Usage: node art/tools/faces_shoot.mjs OUTDIR [chars] [opts]
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/fshots';
const CH = (process.argv[3] || 'zu,g00').split(','), OP = (process.argv[4] || '0,M').split(',');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/faces.html`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const info = {}; let ok = 0, n = 0;
for (const c of CH) for (const o of OP) for (const [view, w, h] of [['close', 640, 640], ['play', 1920, 1080]]) {
  const name = `${c}_${o}_${view}`; n++;
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(`${BASE}?c=${c}&o=${o}&view=${view}`);
  try {
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    info[name] = await page.evaluate(() => window.__info);
    if (info[name] && !info[name].err) { await page.screenshot({ path: `${OUT}/${name}.png` }); ok++; } else errs.push('load ' + JSON.stringify(info[name]));
  } catch (e) { errs.push('timeout'); }
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 200) : 'ok', JSON.stringify(info[name] || {}));
  await page.close();
}
await writeFile(`${OUT}/shots.json`, JSON.stringify(info, null, 1));
console.log(`${ok === n ? 'PASS' : 'FAIL'} shots ${ok} of ${n}`);
await browser.close(); server.close();
