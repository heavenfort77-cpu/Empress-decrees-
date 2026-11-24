// Quick probe (not committed): load the page and run only the BP03 checks plus BP01 402/408 equivalents via run.mjs pieces.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { palace3Checks } from '../tests/palace3-checks.mjs';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': extname(p) === '.html' ? 'text/html' : 'text/javascript' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
const errors = []; page.on('pageerror', (e) => errors.push(String(e))); page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
await page.goto(URL0); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
const g = (fn, arg) => page.evaluate(fn, arg);
const base = await g(() => __game.render(true));
const results = [];
const check = (name, ok, detail) => { results.push({ name, ok: !!ok }); console.log((ok ? 'PASS ' : 'FAIL ') + name.slice(0, 4) + ' ' + String(detail).slice(0, 700)); };
const t0 = Date.now();
try { await palace3Checks(g, check, base); } catch (e) { console.log('THROW ' + String(e).slice(0, 800)); }
console.log('errors ' + errors.length + ' ' + errors.slice(0, 3).join(' | ').slice(0, 600));
console.log(`PROBE ${results.filter((r) => r.ok).length} of ${results.length} pass, ${((Date.now() - t0) / 1000).toFixed(0)} s`);
await browser.close(); server.close();
