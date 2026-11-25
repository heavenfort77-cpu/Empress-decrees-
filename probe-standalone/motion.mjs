// Probe: every school suit's pose while the bot plays (idle, moving, after attacks), from the single-file build.
// Prints one cropped screenshot per school and time as IMG lines; FAIL on page errors.
import { chromium } from 'playwright';
import path from 'node:path';
const FILE = path.resolve(process.argv[2]);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
let fails = 0;
for (let s = 0; s < 9; s++) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  try {
    await page.goto('file://' + FILE, { timeout: 120000 });
    await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    await page.evaluate((k) => { const G = __game; G.setSeed(12345); G.pickMode('palace'); G.pickSchool(k); }, s);
    await page.waitForFunction(() => !__game.loadBusy(), null, { timeout: 180000 });
    await page.waitForTimeout(1500);
    const shot = async (tag) => { const b = await page.screenshot({ type: 'jpeg', quality: 50, clip: { x: 400, y: 120, width: 480, height: 480 } }); console.log(`IMG s${s}_${tag} ${b.toString('base64')}`); };
    await shot('a_idle');
    const t0 = await page.evaluate(() => __game.state().t);
    await page.evaluate(() => __game.autoPlayer(true));
    for (const [tag, dt] of [['b_4s', 4], ['c_10s', 10], ['d_18s', 18]]) {
      await page.waitForFunction(([t, d]) => __game.state().t > t + d, [t0, dt], { timeout: 180000 });
      await shot(tag);
    }
    const st = await page.evaluate(() => { const q = __game.state(); return JSON.stringify({ t: q.t, view: q.view, hp: q.hp, room: q.room }).slice(0, 200); });
    console.log(`INFO school ${s} ${st}`);
  } catch (e) { fails++; console.log(`FAIL school ${s} run: ${String(e.message).split('\n')[0]}`); }
  if (errs.length) { fails++; console.log(`FAIL school ${s} page errors: ${errs.slice(0, 3).join(' | ').slice(0, 300)}`); }
  await ctx.close();
}
await browser.close();
console.log(`FAIL lines: ${fails}`);
