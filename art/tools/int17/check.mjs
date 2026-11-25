// Batch 17a decode driver: serves the repo root, opens art/tools/int17/check.html in headless Chromium (SwiftShader) and writes what it reads back.
// Usage: node check.mjs REPO STAGE OUT. STAGE holds desk/ phone/ (etc1s|uastc)/*.ktx2, mut/*.ktx2 and models/; OUT gets *.rgba, tex_*.json, models.json, caps.json.
import { createServer } from 'node:http';
import { readFile, writeFile, mkdir, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { extname, join, normalize, dirname } from 'node:path';
import { chromium } from 'playwright';
const [REPO, STAGE, OUT] = process.argv.slice(2);
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]);
  if (req.method === 'PUT' && u.startsWith('/__out/')) { const ch = []; for await (const c of req) ch.push(c); const p = join(OUT, u.slice(7)); await mkdir(dirname(p), { recursive: true }); await writeFile(p, Buffer.concat(ch)); res.end('ok'); return; }
  const root = u.startsWith('/__stage/') ? STAGE : REPO, rel = u.startsWith('/__stage/') ? u.slice(9) : u;
  const p = normalize(join(root, rel));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
await mkdir(OUT, { recursive: true });
const list = [];
for (const set of ['desk', 'phone']) for (const mode of ['etc1s', 'uastc', 'uastc4']) {
  const d = join(STAGE, set, mode); if (!existsSync(d)) continue;
  for (const f of (await readdir(d)).filter((x) => x.endsWith('.ktx2')).sort()) list.push([`/__stage/${set}/${mode}/${f}`, `${set}/${mode}/${f.slice(0, -5)}`]);
}
if (existsSync(join(STAGE, 'mut'))) for (const f of (await readdir(join(STAGE, 'mut'))).filter((x) => x.endsWith('.ktx2')).sort()) list.push([`/__stage/mut/${f}`, `mut/${f.slice(0, -5)}`]);
for (const mode of ['rgba', 'gpu']) {
  const page = await browser.newPage(); const errs = []; page.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));
  await page.goto(`${BASE}/art/tools/int17/check.html?mode=${mode}`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  const caps = await page.evaluate(() => window.__caps); await writeFile(join(OUT, `caps_${mode}.json`), JSON.stringify(caps, null, 1));
  const rows = [];
  for (let i = 0; i < list.length; i += 8) rows.push(...await page.evaluate((l) => window.runTex(l), list.slice(i, i + 8).map(([u, t]) => [u, mode + '/' + t])));
  await writeFile(join(OUT, `tex_${mode}.json`), JSON.stringify({ errs, rows }, null, 1));
  console.log(`TEX ${mode}: ${rows.filter((r) => r.ok).length} of ${rows.length} loaded, page errors ${errs.length}`);
  await page.close();
}
const models = [];
async function walk(d, rel) { for (const e of (await readdir(d, { withFileTypes: true })).sort((a, b) => a.name.localeCompare(b.name))) { if (e.isDirectory()) await walk(join(d, e.name), rel + e.name + '/'); else if (e.name.endsWith('.glb')) models.push(rel + e.name); } }
await walk(join(STAGE, 'models'), '');
const mlist = models.map((m) => [`/assets/models/${m}`, `/__stage/models/${m}`, m]);
if (existsSync(join(STAGE, 'mutm'))) for (const f of (await readdir(join(STAGE, 'mutm'))).filter((x) => x.endsWith('.glb')).sort()) { const src = f.split('__')[1].replace(/~/g, '/'); mlist.push([`/assets/models/${src}`, `/__stage/mutm/${f}`, 'mut/' + f]); }
const page = await browser.newPage({ viewport: { width: 64, height: 64 } }); const errs = []; page.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));
await page.goto(`${BASE}/art/tools/int17/check.html?mode=gpu`); await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
const mrows = [];
for (const m of mlist) mrows.push(...await page.evaluate((l) => window.runModels(l), [m]));
await writeFile(join(OUT, 'models.json'), JSON.stringify({ errs, rows: mrows }));
console.log(`MODELS ${mrows.filter((r) => r.ok).length} of ${mrows.length} loaded, page errors ${errs.length}`);
await browser.close(); server.close();
