// Probe: does the single-file build load its ART (textures, models, vfx) when opened as a local file?
// Route NET = network allowed; route OFF = every external request blocked (what a sandboxed viewer does).
// Prints PASS/FAIL lines, counts requests per file type and outcome, saves a screenshot per route.
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
const FILE = path.resolve(process.argv[2]);
const OUT = process.argv[3] || '.';
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
let fails = 0;
const line = (ok, name, msg) => { if (!ok) fails++; console.log(`${ok ? 'PASS' : 'FAIL'} ${name}: ${msg}`); };
async function route(name, block, touch) {
  const ctx = await browser.newContext({ viewport: touch ? { width: 412, height: 800 } : { width: 1280, height: 720 }, hasTouch: touch, isMobile: touch });
  const page = await ctx.newPage();
  const errs = [], ok = {}, bad = {}, badList = [];
  const ext = (u) => (u.split('?')[0].match(/\.([a-z0-9]+)$/i) || [0, 'none'])[1];
  page.on('pageerror', (e) => errs.push('pageerror ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errs.push('console ' + m.text().slice(0, 160)); });
  page.on('response', (r) => { const e = ext(r.url()); if (r.status() < 400) ok[e] = (ok[e] || 0) + 1; else { bad[e] = (bad[e] || 0) + 1; badList.push(r.status() + ' ' + r.url().slice(-70)); } });
  page.on('requestfailed', (r) => { const e = ext(r.url()); bad[e] = (bad[e] || 0) + 1; badList.push('failed ' + r.url().slice(-70)); });
  if (block) await page.route((u) => !u.href.startsWith('file:'), (r) => r.abort());
  try {
    await page.goto('file://' + FILE, { timeout: 120000 });
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    await page.evaluate(() => { const G = __game; G.setSeed(12345); G.pickMode('palace'); G.pickSchool(1); });
    await page.waitForFunction(() => !__game.loadBusy(), null, { timeout: 180000 });
    await page.waitForTimeout(4000);
    const l = await page.evaluate(() => __game.load());
    const led = l.led || {};
    console.log(`INFO ${name} palace ${l.palace} fmt [${(led.fmt || []).join(',')}] failed [${(led.failed || []).join(',')}] capped ${led.capped}`);
    console.log(`INFO ${name} requests ok ${JSON.stringify(ok)} bad ${JSON.stringify(bad)}`);
    for (const b of badList.slice(0, 12)) console.log(`INFO ${name} bad ${b}`);
    const info = await page.evaluate(() => { const r = window.__game && __game.chars ? __game.chars() : null; return r ? JSON.stringify(r).slice(0, 400) : 'no chars hook'; });
    console.log(`INFO ${name} chars ${info}`);
    const nOk = Object.values(ok).reduce((a, b) => a + b, 0), nBad = Object.values(bad).reduce((a, b) => a + b, 0);
    if (!block) line((ok.png || 0) > 0 && (ok.glb || 0) > 0 && nBad === 0, `${name} art loads`, `png ${ok.png || 0}, glb ${ok.glb || 0}, ok ${nOk}, bad ${nBad}`);
    else line(true, `${name} blocked run`, `ok ${nOk}, bad ${nBad} (expected: all blocked)`);
    await page.screenshot({ path: path.join(OUT, `art_${name}.jpg`), type: 'jpeg', quality: 70 });
  } catch (e) { line(false, `${name} run`, String(e.message).split('\n')[0]); }
  for (const e of errs.slice(0, 8)) console.log(`INFO ${name} err ${e}`);
  line(errs.filter((e) => e.startsWith('pageerror')).length === 0, `${name} no page error`, `${errs.length} console/page errors`);
  await ctx.close();
}
await route('NET_desktop', false, false);
await route('NET_phone', false, true);
await route('OFF_phone', true, true);
await browser.close();
console.log(`FAIL lines: ${fails}`);
