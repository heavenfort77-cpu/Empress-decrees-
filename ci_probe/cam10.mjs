// Ticket 10 probe: wide distance and player height per room at 1920x1080 and phone landscape (full plan).
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium; try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname, T = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript' };
const server = createServer(async (q, s) => { const u = decodeURIComponent(q.url.split('?')[0]), p = normalize(join(ROOT, u === '/' ? 'index.html' : u)); try { const b = await readFile(p); s.writeHead(200, { 'content-type': T[extname(p)] || 'application/octet-stream' }); s.end(b); } catch { s.writeHead(404); s.end(); } });
await new Promise((r) => server.listen(0, r));
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
for (const [k, w, h, t] of [['1080p', 1920, 1080, false], ['phoneL', 844, 390, true]]) {
  const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: t, hasTouch: t }); const pg = await ctx.newPage();
  await pg.goto(URL0); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
  const o = await pg.evaluate(() => {
    const G = __game; G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset();
    const rows = [];
    for (const r of G.palPlan().rooms) {
      if (r.type === 'core') continue;
      G.reset(); G.teleport(r.cx, r.cz); G.step(90); const c = G.palCam();
      rows.push({ id: r.id, w: r.x1 - r.x0, d: r.z1 - r.z0, area: (r.x1 - r.x0) * (r.z1 - r.z0), fit: c.fit, wd: +c.wd.toFixed(2), px: +c.px.toFixed(1), close: +c.close.toFixed(2), floor: +c.floor.toFixed(1) });
    }
    G.reset(); G.step(2); G.palPlaceBot(0, G.palace().x, G.palace().z - 5); G.step(40); const cc = G.palCam();
    rows.sort((a, b) => a.area - b.area);
    return { small: rows[0], big: rows[rows.length - 1], fitN: rows.filter((q) => q.fit).length, n: rows.length, closePx: +cc.px.toFixed(1), closeB: cc.b };
  });
  console.log(k, JSON.stringify(o)); await ctx.close();
}
await browser.close(); server.close();
