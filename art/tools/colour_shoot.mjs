// COLOUR (art/Colour-Clarity-Study.md): shots of art/viewer/colour.html (art tool, not shipped). Nine suits + guard zu + rebel ls on the
// old (round 2) and new hall floor, with the game's current dark outline and with the proposed silhouette rim, school tint and rebel tint, at the game's close
// framing (10.5 m) and CAM_DIST (14 m), close-ups, the same row on the other walkable floors, and ID masks for the measures.
// Usage: node art/tools/colour_shoot.mjs OUTDIR   (writes PNGs and manifest.json)   Software GL on the runner: look only, no frame rate.
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
// CONFIG
// Figures in the row (school order as the owner's screenshot, then one guard and one rebel).
const IDS = ['fa', 'ru', 'dao', 'mo', 'yy', 'za', 'ming', 'zh', 'nong', 'zu', 'ls'];
// The game's current suit outline (src/chars.js CHR.outline.color).
const DARK = '0b0908';
// Proposed rim colours (unlit): pale warm gold, and a deeper bronze-gold for comparison.
const GOLD = 'e8c888', BRONZE = 'd4a85a';
// Proposed rebel cloth tint (umber hemp, off the floor's value).
const RB = '8c7860';
// Floors: the approved round 2 hall floor (kept copy) and the repainted one.
const OLD = 'art/round2/tex/hall_floor.png', NEW = 'assets/tex/hall_floor.png';
// Variants: name, floor, suit sheet, outline colour ('' = none), outline px (0 = none), silhouette-only, school tint, rebel tint, fresnel.
const V = [['old_cur', OLD, 'suit_lamellar', DARK, 2, 0, 0, '', 0], ['old_sil2', OLD, 'suit_lamellar_qin', GOLD, 2, 1, 1, RB, 0],
  ['new_norim', NEW, 'suit_lamellar_qin', '', 0, 0, 1, RB, 0], ['new_dark', NEW, 'suit_lamellar_qin', DARK, 2, 0, 1, RB, 0],
  ['new_sil2', NEW, 'suit_lamellar_qin', GOLD, 2, 1, 1, RB, 0], ['new_sil3', NEW, 'suit_lamellar_qin', GOLD, 3, 1, 1, RB, 0],
  ['new_silbronze', NEW, 'suit_lamellar_qin', BRONZE, 2, 1, 1, RB, 0], ['new_fres', NEW, 'suit_lamellar_qin', '', 0, 0, 1, RB, 0.8]];
// The proposal (shot on the other floors and in the close-ups).
const PROP = V[4];
// Other walkable floors (src/palace_art.js floors: court, corridor, garden, bridge): the approved court paving and the round 2 proposals.
const FLOORS = [['stone_paving', 'assets/tex/stone_paving.png'], ['floor_tiles_prop', 'art/colour/cand/floor_tiles.png'],
  ['garden_ground_prop', 'art/colour/cand/garden_ground.png'], ['bridge_deck_prop', 'art/colour/cand/bridge_deck.png']];
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
const q = (ids, view, dist, [, floor, lam, ol, px, sil, tint, rb, fres], fl) => `ids=${ids}&view=${view}&dist=${dist}&floor=${fl || floor}&lam=${lam}` +
  (ol ? `&ol=${ol}&olpx=${px}` : '') + (sil ? '&sil=1' : '') + (tint ? '&tint=1' : '') + (rb ? `&rb=${rb}` : '') + (fres ? `&fres=${fres}` : '');
for (const px of [0, 2, 3]) for (const d of [10.5, 14]) SHOTS.push([`id_px${px}_d${d}`, q(all, 'play', d, ['', NEW, 'suit_lamellar', px ? DARK : '', px, 0, 0, '', 0]) + '&mode=id']);
for (const v of V) for (const d of [10.5, 14]) { SHOTS.push([`${v[0]}_d${d}`, q(all, 'play', d, v)]); MAN.push({ shot: `${v[0]}_d${d}`, variant: v[0], dist: d, id: `id_px${v[4]}_d${d}`, floor: v[1], kind: 'hall' }); }
for (const v of [V[0], PROP]) GROUPS.forEach((g, i) => SHOTS.push([`close_${v[0]}_${i}`, q(g.join(','), 'turn', 5.2, v)]));
for (const [fname, path] of FLOORS) { SHOTS.push([`floor_${fname}`, q(all, 'play', 10.5, PROP, path)]); MAN.push({ shot: `floor_${fname}`, variant: PROP[0], dist: 10.5, id: `id_px${PROP[4]}_d10.5`, floor: path, kind: fname }); }
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
