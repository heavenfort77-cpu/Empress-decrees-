// FIXB 25 Nov shots (art tool, not shipped): room sheets (art/viewer/arch.html) and prop shots (art/viewer/beast.html) for the owner's
// 02:1x-02:2x picks, plus unlit masks for the on-screen measurements (art/tools/fixb_measure.py). Records every texture each page loads
// (brass-only gate) and the viewer's draw stats. Usage: node art/tools/fixb_shoot.mjs OUTDIR [ONLY_PREFIX]
import { createServer } from 'node:http';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('../..', import.meta.url).pathname, OUT = process.argv[2] || '/tmp/fixb_shots', ONLY = process.argv[3] || '';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const URL0 = `http://127.0.0.1:${server.address().port}/art/viewer/`;
await mkdir(OUT, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const HD = [1920, 1080], SQ = [640, 640];
const S = [];
const A = (name, q, size = HD) => S.push([name, 'arch.html?' + q, ...size]);
const B = (name, q, size = HD) => S.push([name, 'beast.html?' + q, ...size]);
// rooms on the brass sheet (owner 02:1x), new pieces
for (const room of ['hall', 'court', 'corridor', 'garden', 'bridge', 'core']) { A(`${room}_wide`, `room=${room}&view=wide`); A(`${room}_play`, `room=${room}&view=play`); }
A('hall_burnt_wide', 'room=hall&view=wide&burnt=1'); A('hall_locked_play', 'room=hall&view=play&locked=1');
// star inlay: with and without, with the game's hazard rings, and masks
for (const v of ['wide', 'play']) {
  A(`core_${v}_noinlay`, `room=core&view=${v}&inlay=0`); A(`core_${v}_tell`, `room=core&view=${v}&tell=1`); A(`core_${v}_tell_noinlay`, `room=core&view=${v}&tell=1&inlay=0`);
  A(`mask_core_${v}_tell`, `room=core&view=${v}&tell=1&mask=tell`); A(`mask_core_${v}_floor`, `room=core&view=${v}&mask=floor,inlay`); A(`mask_core_${v}_inlay`, `room=core&view=${v}&mask=inlay`);
}
// throne, racks, garden: before (round 2 GLBs and layout) and after
A('mask_core_wide_throne', 'room=core&view=wide&mask=throne'); A('mask_core_wide_throne_r2', 'room=core&view=wide&mask=throne&glbdir=arch_r2');
A('core_wide_r2', 'room=core&view=wide&glbdir=arch_r2&inlay=0');
A('mask_hall_wide_racks', 'room=hall&view=wide&mask=racks'); A('mask_hall_wide_racks_r2', 'room=hall&view=wide&mask=racks&glbdir=arch_r2'); A('hall_wide_r2', 'room=hall&view=wide&glbdir=arch_r2');
A('hall_burnt_wide_r2', 'room=hall&view=wide&burnt=1&glbdir=arch_r2');
A('mask_garden_wide_plants', 'room=garden&view=wide&mask=plants'); A('mask_garden_wide_plants_r2', 'room=garden&view=wide&mask=plants&glbdir=arch_r2'); A('garden_wide_r2', 'room=garden&view=wide&glbdir=arch_r2');
A('garden_play_r2', 'room=garden&view=play&glbdir=arch_r2');
A('mask_garden_wide_pond', 'room=garden&view=wide&mask=pond'); A('mask_garden_wide_ground', 'room=garden&view=wide&mask=ground');
// plaster: the candidate side by side was round 1 (run 45462167005, art/arch/round3/plaster_candidate/); A2 kept (owner rule: align or keep)
// flags at play size on the court's north wall-walk (W1a mapping)
A('court_play_flags', 'room=court&view=play&at=-16,-10'); A('hall_play_racks', 'room=hall&view=play&at=-9,-6');
// pieces
for (const p of ['throne_dais', 'slip_rack', 'pillar', 'door', 'que_pair']) A(`piece_${p}`, `piece=${p}&yaw=30`, [960, 720]);
// props on the brass sheet: tally (round 3), mercury (round 2)
const TURN = (m, st = '') => [['turn_front', 0], ['turn_34', 35], ['turn_side', 90], ['turn_back', 180]].forEach(([n, y]) => B(`${m}_${n}`, `model=${m}&view=turn&yaw=${y}&sheet=brass${st}`, SQ));
B('tally_play', 'model=tally&view=play&sheet=brass'); B('tally_wide', 'model=tally&view=wide&sheet=brass'); TURN('tally');
B('tally_top', 'model=tally&view=turn&yaw=20&pitch=55&sheet=brass', SQ); B('tally_lods', 'model=tally&view=lods&sheet=brass', [1280, 640]);
for (const m of ['sil', 'flat', 'shade', 'tex']) B(`tally_pass_${m}`, `model=tally&view=turn&yaw=35&mode=${m}&sheet=brass`, SQ);
for (const st of ['idle', 'warn', 'hot']) { B(`merc_play_${st}`, `model=merc&view=play&state=${st}&sheet=brass`); B(`merc_close_${st}`, `model=merc&view=turn&yaw=35&pitch=35&state=${st}&sheet=brass`, SQ); }
B('merc_play_warn_t2', 'model=merc&view=play&state=warn&sheet=brass&t=0.55'); B('merc_close_warn_t2', 'model=merc&view=turn&yaw=35&pitch=35&state=warn&sheet=brass&t=0.55', SQ); B('merc_play_idle_t2', 'model=merc&view=play&state=idle&sheet=brass&t=0.55');
B('merc_wide', 'model=merc&view=wide&sheet=brass'); B('mask_merc_play', 'model=merc&view=play&mask=palMerc&sheet=brass');
// brass-gate mutation: the old bronze sheet must be caught by fixb_measure.py
B('mut_bronze_tally_play', 'model=tally&view=play');
const stats = {};
for (const [name, q, w, h] of S.filter(([n]) => !ONLY || n.startsWith(ONLY))) {
  const page = await browser.newPage({ viewport: { width: w, height: h } });
  const errs = [], texs = new Set(); page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('request', (rq) => { const u = rq.url().split('?')[0]; if (u.endsWith('.png')) texs.add(u.split('/').pop()); });
  await page.goto(URL0 + q);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 180000 }); } catch (e) { errs.push('timeout'); }
  await page.screenshot({ path: `${OUT}/${name}.png` });
  stats[name] = { q, stats: await page.evaluate(() => window.__stats || null), textures: [...texs].sort(), errs };
  console.log(name, JSON.stringify(stats[name].stats), errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
await writeFile(`${OUT}/stats.json`, JSON.stringify(stats, null, 1));
await browser.close(); server.close();
