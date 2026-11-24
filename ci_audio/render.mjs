// Renders every sound, loop and the 60 s ramp in headless Chromium (runner only). Usage: node ci_audio/render.mjs OUTDIR
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join, extname } from 'node:path';
const OUT = process.argv[2], ROOT = new URL('..', import.meta.url).pathname;
const RATE = { desktop: 48000, phone: 24000 };
const srv = createServer((q, r) => { try { const p = join(ROOT, decodeURIComponent(q.url.split('?')[0])); r.writeHead(200, { 'content-type': extname(p) === '.js' ? 'text/javascript' : 'text/html' }); r.end(readFileSync(p)); } catch (e) { r.writeHead(404); r.end(); } }).listen(8123);
const browser = await chromium.launch({ args: ['--autoplay-policy=no-user-gesture-required'] });
const page = await browser.newPage();
page.on('pageerror', (e) => console.log('PAGEERROR ' + e.message));
await page.goto('http://localhost:8123/ci_audio/harness.html');
await page.waitForFunction(() => window.HREADY === true, null, { timeout: 30000 });
const list = await page.evaluate(() => H.list()), loops = await page.evaluate(() => H.loops()), cfg = await page.evaluate(() => H.config());
console.log('NOTES (computed once, 五声 by 三分损益 from gong ' + cfg.music.gongHz + ' Hz):');
for (const l of await page.evaluate(() => H.notes())) console.log('  ' + l);
const stats = { sounds: {}, loops: {}, refs: {}, ramp: {}, mut: {} };
const save = (rel, b64) => { const p = join(OUT, rel); mkdirSync(join(p, '..'), { recursive: true }); writeFileSync(p, Buffer.from(b64, 'base64')); };
let fails = 0;
for (const prof of ['phone', 'desktop']) {
  const sr = RATE[prof];
  for (const s of list) {
    try { const r = await page.evaluate(([n, sr, p]) => H.sound(n, sr, p), [s.name, sr, prof]); save(`wav/${prof}/${s.name}.wav`, r.b64); delete r.b64; stats.sounds[prof + '/' + s.name] = Object.assign(r, { cat: s.cat, sr }); }
    catch (e) { fails++; console.log(`RENDER FAIL ${prof}/${s.name}: ${String(e.message).split('\n')[0]}`); }
  }
  for (const k of loops) {
    try { const r = await page.evaluate(([n, sr, p]) => H.loop(n, sr, p, false), [k, sr, prof]); save(`wav/${prof}/loop_${k}.wav`, r.b64); delete r.b64; stats.loops[prof + '/' + k] = Object.assign(r, { sr }); }
    catch (e) { fails++; console.log(`RENDER FAIL loop ${prof}/${k}: ${String(e.message).split('\n')[0]}`); }
    if (prof !== 'phone') continue;
    // Steady-state reference (second loop of a continuous two-loop render) for the seam check of phone loops.
    try { const r = await page.evaluate(([n, sr, p]) => H.loop(n, sr, p, 'ref'), [k, sr, prof]); save(`ref/${prof}/loop_${k}.wav`, r.b64); delete r.b64; stats.refs[prof + '/' + k] = Object.assign(r, { sr }); }
    catch (e) { fails++; console.log(`RENDER FAIL ref ${prof}/${k}: ${String(e.message).split('\n')[0]}`); }
  }
  try { const r = await page.evaluate(([sr, p]) => H.ramp(sr, 60, p), [sr, prof]); save(`preview/ramp_60s_${prof}.wav`, r.b64); delete r.b64; stats.ramp[prof] = Object.assign(r, { sr }); }
  catch (e) { fails++; console.log(`RENDER FAIL ramp ${prof}: ${String(e.message).split('\n')[0]}`); }
}
// Mutation material: loops rendered without the seam handling (no whole-cycle snap, no crossfade, no tail fold).
for (const k of ['m_drone', 'm_bells', 'a_wind', 'a_fire']) {
  const r = await page.evaluate(([n, sr]) => H.loop(n, sr, 'phone', 'raw'), [k, RATE.phone]); save(`mut/raw_${k}.wav`, r.b64); delete r.b64; stats.mut['raw_' + k] = r;
}
writeFileSync(join(OUT, 'stats.json'), JSON.stringify({ list, loops, config: cfg, rate: RATE, stats }, null, 1));
const ms = Object.values(stats.sounds).reduce((a, r) => a + r.ms, 0) + Object.values(stats.loops).reduce((a, r) => a + r.ms, 0);
console.log(`RENDERED sounds ${Object.keys(stats.sounds).length} loops ${Object.keys(stats.loops).length} ramps ${Object.keys(stats.ramp).length}; render time ${(ms / 1000).toFixed(1)} s (both profiles, runner CPU); render failures ${fails}`);
await browser.close(); srv.close();
