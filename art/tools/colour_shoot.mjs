// COLOUR FINAL (art/Colour-Clarity-Study.md; owner 25 Nov 14:08: new lighter hall floor + the game's existing dark outline, no rim).
// Shots of art/viewer/colour.html (art tool, not shipped): nine suits + guard zu + rebel ls on the old (round 2) and new hall floor, as the
// game is now and with the proposal (Qin sheet, cloth tint table, rebel tint), at the game's close framing (10.5 m) and CAM_DIST (14 m),
// close-ups, the row in a hall mock with plaster wall and pillars, the row on the other walkable floors, and ID masks for the measures.
// Usage: node art/tools/colour_shoot.mjs OUTDIR   (writes PNGs and manifest.json)   Software GL on the runner: look only, no frame rate.
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
// CONFIG
// Figures in the row (school order as the owner's screenshot, then one guard and one rebel).
const IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong', 'zu', 'ls'];
// The game's suit outline (src/chars.js CHR.outline: 2 px, this colour), kept (owner 14:08).
const DARK = '0b0908';
// Proposed rebel cloth tint (umber hemp, off the floor's value).
const RB = '8c7860';
// Cloth tint table (lead 25 Nov: 道 keeps the gold robe of its GLB, so it is not in the table; 阴阳 keeps its GLB black).
const CT_A = 'fa:efe9dc,ru:c88c3e,mo:e66044,za:dfe6f2,ming:9c7ae0,zh:22754a,nong:5a92e4';
// Floors: the approved round 2 hall floor (kept copy), the even COLOUR round 2 floor (the owner's pick A was made on it; sd 4.4), the new one.
const OLD = 'art/round2/tex/hall_floor.png', EVEN = 'art/colour/alt/hall_floor_even.png', NEW = 'assets/tex/hall_floor.png';
// Variants: name, floor, suit sheet, cloth table, rebel tint.
const V = [['old_cur', OLD, 'suit_lamellar', '', ''], ['even_a', EVEN, 'suit_lamellar_qin', CT_A, RB], ['new_a', NEW, 'suit_lamellar_qin', CT_A, RB]];
// The proposal (in the hall mock and in the close-ups).
const PROP = V[2];
// Other walkable floors: as delivered in run 45559220231, not shot again in the floor-only round.
const FLOORS = [];
// Close-up groups.
const GROUPS = [['fa', 'ru', 'dao', 'mo'], ['yy', 'za', 'ming', 'zh'], ['nong', 'zu', 'ls']];
const ROOT = new URL('../..', import.meta.url).pathname, OUTD = process.argv[2] || '/tmp/colshots';
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.glb': 'model/gltf-binary' };
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/art/viewer/colour.html`;
await mkdir(OUTD, { recursive: true });
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const all = IDS.join(','), SHOTS = [], MAN = [];
const q = (ids, view, dist, [, floor, lam, ct, rb], fl) => `ids=${ids}&view=${view}&dist=${dist}&floor=${fl || floor}&lam=${lam}&ol=${DARK}&olpx=2` + (ct ? `&ct=${ct}` : '') + (rb ? `&rb=${rb}` : '');
for (const d of [10.5, 14]) SHOTS.push([`id_d${d}`, q(all, 'play', d, V[0]) + '&mode=id']);
for (const v of V) for (const d of [10.5, 14]) { SHOTS.push([`${v[0]}_d${d}`, q(all, 'play', d, v)]); MAN.push({ shot: `${v[0]}_d${d}`, variant: v[0], dist: d, id: `id_d${d}`, floor: v[1], kind: 'hall' }); }
for (const v of [V[0], PROP]) { GROUPS.forEach((g, i) => SHOTS.push([`close_${v[0]}_${i}`, q(g.join(','), 'turn', 5.2, v)]));
  SHOTS.push([`hall_${v[0]}`, q(all, 'play', 14, v) + '&hall=1'], [`hall_low_${v[0]}`, q(all, 'turn', 12, v) + '&hall=1&pitch=14']); }
for (const [fname, path] of FLOORS) { SHOTS.push([`floor_${fname}`, q(all, 'play', 10.5, PROP, path)]); MAN.push({ shot: `floor_${fname}`, variant: PROP[0], dist: 10.5, id: 'id_d10.5', floor: path, kind: fname }); }
let bad = 0;
for (const [name, query] of SHOTS) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(BASE + '?' + query);
  try { await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    const e = await page.evaluate(() => window.__texErr || window.__loadErr || ''); if (e) errs.push('missing ' + e);
    await page.screenshot({ path: `${OUTD}/${name}.png` }); }
  catch (e) { errs.push('timeout'); }
  if (errs.length) bad++;
  console.log(name, errs.length ? 'ERR ' + errs[0].slice(0, 160) : 'ok');
  await page.close();
}
await writeFile(`${OUTD}/manifest.json`, JSON.stringify({ ids: IDS, shots: MAN, groups: GROUPS }));
console.log(`shots ${SHOTS.length - bad} of ${SHOTS.length} ok`);
console.log(bad ? `FAIL colour shots: ${bad} with errors` : 'PASS colour shots: all rendered');
await browser.close(); server.close();
