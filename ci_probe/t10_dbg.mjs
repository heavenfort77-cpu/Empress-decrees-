// Ticket 10 debug probe (deleted before commit): traces the scenes of failing checks 165, 166, 168 (yinyang:0) and 169 (roar).
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const server = createServer(async (req, res) => {
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': extname(p) === '.html' ? 'text/html' : 'text/javascript' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const page = await browser.newPage({ viewport: { width: 1366, height: 768 } });
const errors = []; page.on('pageerror', (e) => errors.push(String(e)));
await page.goto(`http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder`);
await page.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
const out = await page.evaluate(() => {
  const G = __game, C = G.config, R = {};
  const Z = {
    start(n, keep) { G.setSeed(12345); G.setPkitP(false); G.setBots(n); G.pickSchool(5); for (let i = 0; i < n; i++) if (!(keep || []).includes(i)) G.placeholderKit(i); G.setDecNext(1e9); G.setHp(1e9); for (let i = 0; i < n; i++) { G.setBotHp(i, 100); for (let k = 0; k < 3; k++) G.setBotCd(i, k, 99); } },
    park(at) { for (const k in at) { G.placeBot(+k, at[k][0], at[k][1]); for (let s = 0; s < 3; s++) G.setBotCd(+k, s, 99); } },
    lost: (i) => +(100 - G.bots().list[i].hp).toFixed(4),
    end() { G.setPkitP(true); G.pickSchool(0); G.setBots(0); G.reset(); } };
  const r1 = (v) => Math.round(v * 100) / 100;
  // A: 168 yinyang:0
  try {
    const dd = 3; Z.start(3); G.teleport(0, -15); const at = { 0: [0, -15 - dd], 1: [2.5, -15 - dd], 2: [24, -40] }, park = () => Z.park(at);
    park(); G.step(2); G.setStore(-1, 'yinyang', 0); G.setCharge(-1, C.ULT.full); const p0 = G.state(); const cast = G.cast(2, 0, -15 - dd);
    const tr = []; for (let n = 0; n < 40; n++) { park(); G.step(1); const y = G.yyState(-1), s = G.state(); if (n % 4 === 0) tr.push([n, r1(s.x), r1(s.z), y.orbs.map((o) => [o.on, r1(o.x), r1(o.z)]), Z.lost(0), r1(G.kitState(0).slowT)]); }
    R.A = { cast, p0: [r1(p0.x), r1(p0.z)], copy: G.zaState(-1).copy, store: G.zaState(-1).store, tr };
  } catch (e) { R.A = { err: String(e.stack).slice(0, 400) }; }
  Z.end();
  // B: 165 leader
  try {
    Z.start(4); G.teleport(0, -15); const at = { 0: [0, -20], 1: [-20, -40], 2: [20, -40], 3: [0, -20] };
    at[0] = [24, -44]; Z.park(at); G.step(2); G.plateTo(3, 'stalker'); G.step(1);
    R.B = { leader: G.leader().id, phase: G.royale().phase, botN: G.bots().n, st: G.suitsState(), b3: (({ id, dead, hp, pk }) => ({ id, dead, hp, pk }))(G.bots().list[3]), dec: G.leader().dec, k3: G.kitState(3).sealT };
  } catch (e) { R.B = { err: String(e.stack).slice(0, 400) }; }
  Z.end();
  // C: 166 far blink
  try {
    Z.start(3); const at = { 0: [24, -44], 1: [-24, -44], 2: [24, -40] }; G.teleport(0, -15); Z.park(at); G.step(1); const p0 = G.state();
    const cast = G.cast(1, 0, -5); const tr = []; for (let n = 0; n < 24; n++) { Z.park(at); G.step(1); const s = G.state(); if (n % 3 === 0) tr.push([n, r1(s.x), r1(s.z), r1(s.y), s.falling, s.zone]); }
    R.C = { p0: [r1(p0.x), r1(p0.z), p0.zone], cast, tr, sk: G.skills().map(r1) };
  } catch (e) { R.C = { err: String(e.stack).slice(0, 400) }; }
  Z.end();
  // D: 169 roar on the demon
  try {
    G.setPkitP(false); G.setSchool(5); G.reset(); G.startHunt(); G.step(Math.round(C.APEX.wakeS / C.STEP) + 1);
    for (let i = 0; i < 3; i++) for (const k of G.moves) G.unitCd(i, k, 9999); G.setHp(1e9);
    G.zhReady(); G.teleport(0, -50); G.placeUnit(0, 0, -55); G.step(1); G.setStore(-1, 'move', 'roar');
    const cast = G.cast(2, 0, -55); const tr = [];
    for (let n = 0; n < 60; n++) { G.step(1); const z = G.zaState(-1), u = G.zaUnit('demon'), s = G.state(); if (n % 6 === 0 || !z.zm.on) tr.push([n, z.zm.on, r1(u.x), r1(u.z), r1(s.x), r1(s.z), r1(u.slowT), u.st]); if (!z.zm.on && n > 2) break; }
    R.D = { cast, copy: G.zaState(-1).copy, skills: G.skills().map(r1), tr, hunt: G.hunt().phase };
  } catch (e) { R.D = { err: String(e.stack).slice(0, 400) }; }
  G.setPkitP(true); G.setSchool(0); G.reset();
  return R;
});
console.log(JSON.stringify(out));
console.log('errors', errors.slice(0, 3).join(' | '));
await browser.close(); server.close();
