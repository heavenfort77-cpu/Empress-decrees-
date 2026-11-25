// SUITS fa round 5: review shots of art/viewer/suits.html (art tool, not shipped). New fa (assets/models/suits/fa.glb) and the round-4 fa
// (fa_old.glb, copied by the runner job only) at close-up and at play size, the nine-suit lineups for the floor-contrast and silhouette
// measures (new fa, and the old fa for the before number), head close-ups, and the region-ID pass for mask vs helm.
// Usage: node art/tools/fa_shoot.mjs OUTDIR INFO.json     Software GL on the runner: look only, no frame rate.
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/fashots';
const INFO = JSON.parse(await readFile(process.argv[3], 'utf8'));
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/suits.html`;
await mkdir(join(OUT, 'old'), { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const w = INFO.find((s) => s.id === 'fa').tell;
const SHOTS = [];
for (const id of ['fa', 'fa_old']) {
  const P = id === 'fa' ? '' : 'old/';
  SHOTS.push([`${P}fa_front`, `id=${id}&view=turn&yaw=0`, 640, 640], [`${P}fa_34`, `id=${id}&view=turn&yaw=35`, 640, 640],
    [`${P}fa_side`, `id=${id}&view=turn&yaw=90`, 640, 640], [`${P}fa_back`, `id=${id}&view=turn&yaw=180`, 640, 640],
    [`${P}fa_sil_front`, `id=${id}&view=turn&yaw=0&mode=sil`, 640, 640],
    [`${P}fa_head_front`, `id=${id}&view=turn&yaw=0&look=1.88&dist=1.1`, 640, 640], [`${P}fa_head_34`, `id=${id}&view=turn&yaw=35&look=1.88&dist=1.1`, 640, 640],
    [`${P}fa_play`, `id=${id}&view=play&yaw=20`, 1920, 1080], [`${P}fa_play0`, `id=${id}&view=play&yaw=0`, 1920, 1080],
    [`${P}fa_windup`, `id=${id}&view=turn&yaw=35&t=${w}`, 640, 640], [`${P}fa_strike`, `id=${id}&view=turn&yaw=35&t=${(w + 0.12).toFixed(2)}`, 640, 640]);
}
SHOTS.push(['fa_matid_play', 'id=fa&view=play&yaw=0&mode=matid', 1920, 1080], ['fa_lods', 'id=fa&view=lods&yaw=35', 1280, 640]);
for (const m of ['sil', 'flat', 'shade']) SHOTS.push([`fa_pass_${m}`, `id=fa&view=turn&yaw=35&mode=${m}`, 640, 640]);
const NINE = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong'];
for (const [P, first] of [['', 'fa'], ['old/', 'fa_old']]) {
  const all = [first, ...NINE.slice(1)].join(',');
  SHOTS.push([`${P}lineup_play`, `ids=${all}&view=play`, 1920, 1080], [`${P}lineup_sil_front`, `ids=${all}&view=play&mode=sil`, 1920, 1080],
    [`${P}lineup_sil_34`, `ids=${all}&view=play&yaw=35&mode=sil`, 1920, 1080], [`${P}lineup_wide`, `ids=${all}&view=wide`, 1920, 1080]);
}
SHOTS.push(['pair_play', 'ids=fa_old,fa&view=play', 1920, 1080], ['pair_turn', 'ids=fa_old,fa&view=turn&dist=4.6', 1280, 720]);
let bad = 0;
for (const [name, q, wd, ht] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: wd, height: ht } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + q);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 }); await page.screenshot({ path: `${OUT}/${name}.png` }); }
  catch (e) { errs.push('timeout'); }
  if (errs.length) bad++;
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
console.log(`shots ${SHOTS.length - bad} of ${SHOTS.length} ok`);
await browser.close(); server.close();
