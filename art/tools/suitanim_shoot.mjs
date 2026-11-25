// SUITANIM review shots of the movement clips from art/viewer/suits.html (art tool): per suit a contact strip per clip (run carried at its
// ground speed so planted feet stay on one floor tile; hit; death) and play-size shots (fight framing: FOV 50, pitch 40, 10.5 m), plus lineups.
// Usage: node art/tools/suitanim_shoot.mjs OUTDIR INFO.json [ids]   Software GL on the runner: look only, no frame rate.
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/ashots';
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
const ts = (n, dur, end = false) => Array.from({ length: n }, (_, i) => (dur * i / (end ? n - 1 : n)).toFixed(4)).join(',');
const SHOTS = [];
for (const id of IDS) {
  const s = INFO.find((x) => x.id === id), fl = s.floor_y;
  SHOTS.push([`${id}_strip_run`, `id=${id}&view=strip&clip=run&yaw=90&move=${s.run_v}&floorline=${fl}&ts=${ts(12, s.run_s)}`, 2400, 420],
    [`${id}_strip_run_front`, `id=${id}&view=strip&clip=run&yaw=0&floorline=${fl}&ts=${ts(8, s.run_s)}`, 1600, 420],
    [`${id}_strip_hit`, `id=${id}&view=strip&clip=hit&yaw=60&floorline=${fl}&ts=0,0.033,0.067,0.1,0.15,0.2,0.25,${s.hit_s.toFixed(3)}`, 1600, 420],
    [`${id}_strip_death`, `id=${id}&view=strip&clip=death&yaw=90&dist=7&floorline=${fl}&ts=${ts(10, s.death_s, true)}`, 2400, 420],
    [`${id}_strip_play_run`, `id=${id}&view=strip&clip=run&yaw=20&pitch=40&dist=10.5&move=${s.run_v}&ts=${ts(8, s.run_s)}`, 1920, 1080],
    [`${id}_play_run`, `id=${id}&view=play&yaw=20&clip=run&t=${(s.run_s * 0.3).toFixed(3)}`, 1920, 1080],
    [`${id}_play_hit`, `id=${id}&view=play&yaw=20&clip=hit&t=0.08`, 1920, 1080],
    [`${id}_play_death`, `id=${id}&view=play&yaw=20&clip=death&t=${s.death_s.toFixed(3)}`, 1920, 1080]);
}
const all = IDS.join(',');
SHOTS.push(['lineup_run', `ids=${all}&view=play&clip=run&t=0.12`, 1920, 1080], ['lineup_death', `ids=${all}&view=play&clip=death&t=1.2`, 1920, 1080]);
let errN = 0;
for (const [name, q, w, h] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + q);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 }); await page.screenshot({ path: `${OUT}/${name}.png` }); }
  catch (e) { errs.push('timeout'); }
  if (errs.length) errN++;
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
console.log(`shots ${SHOTS.length - errN} of ${SHOTS.length} ok`);
await browser.close(); server.close();
