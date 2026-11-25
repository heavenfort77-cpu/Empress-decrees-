// Probe: the single-file HTML build plays on its own (no lib/, no assets/ beside it).
// Routes: A = served alone over http, B = opened as a local file (how a downloaded file opens), C = texture host blocked (fallback must still play).
// Prints PASS/FAIL lines; FAIL on any page error, no ready, no palace, game clock not advancing, or (A, B) textures not loaded.
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const FILE = path.resolve(process.argv[2]);
const html = fs.readFileSync(FILE);
const srv = http.createServer((q, r) => { if (q.url === '/' || q.url === '/game.html') { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); } else { r.writeHead(404); r.end(); } });
await new Promise((ok) => srv.listen(8765, ok));
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
let fails = 0;
const line = (ok, name, msg) => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}: ${msg}`); };

async function route(name, url, blockTex, wantTex) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push('pageerror ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push('console ' + m.text()); });
  if (blockTex) await page.route('https://raw.githubusercontent.com/**', (r) => r.abort());
  try {
    await page.goto(url, { timeout: 120000 });
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    line(true, `${name} ready`, 'window.__ready');
    await page.evaluate(() => { const G = __game; G.setSeed(12345); G.pickMode('palace'); G.pickSchool(0); });
    await page.waitForFunction(() => !__game.loadBusy(), null, { timeout: 120000 });
    const l = await page.evaluate(() => __game.load());
    const led = l.led || {};
    const got = (led.fmt || []).join(',');
    line(!!l.palace, `${name} palace built`, `palace ${l.palace} kind ${led.kind} fmt [${got}] failed [${(led.failed || []).join(',')}] capped ${led.capped}`);
    if (wantTex) line((led.fmt || []).length >= 5 && (led.failed || []).length === 0, `${name} textures`, `loaded ${(led.fmt || []).length} of 5, failed ${(led.failed || []).length}`);
    else line(true, `${name} textures blocked`, `fallback, failed ${(led.failed || []).length}`);
    const s0 = await page.evaluate(() => __game.state());
    await page.evaluate(() => { if (__game.autoPlayer) __game.autoPlayer(true); });
    await page.waitForFunction((t0) => __game.state().t > t0 + 10, s0.t, { timeout: 120000 });
    const s1 = await page.evaluate(() => __game.state());
    line(s1.t > s0.t + 10 && s1.frames > s0.frames, `${name} plays`, `game time ${s0.t.toFixed(1)} -> ${s1.t.toFixed(1)} s, frames ${s0.frames} -> ${s1.frames}, view ${s1.view}`);
  } catch (e) { line(false, `${name} run`, String(e.message).slice(0, 300)); }
  const real = errs.filter((e) => !(blockTex && /raw\.githubusercontent|ERR_FAILED|Failed to load resource/.test(e)));
  line(real.length === 0, `${name} errors`, real.length ? real.slice(0, 5).join(' | ') : '0');
  await ctx.close();
}

await route('A_http', 'http://127.0.0.1:8765/game.html', false, true);
await route('B_file', 'file://' + FILE, false, true);
await route('C_blocked', 'http://127.0.0.1:8765/game.html', true, false);
await browser.close(); srv.close();
console.log(`RESULT ${fails === 0 ? 'PASS' : 'FAIL'} fails ${fails}`);
process.exit(0);
