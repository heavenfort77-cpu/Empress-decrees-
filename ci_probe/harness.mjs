// Shared page setup for the ci_probe measurement scripts (same server, browser flags and start as tests/run.mjs).
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript' };
export async function open() {
  const server = createServer(async (req, res) => {
    const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u === '/' ? 'index.html' : u));
    try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
  }).listen(0);
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
  const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
  await page.goto(`http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder`);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  return { page, errors, close: async () => { await browser.close(); server.close(); } };
}
