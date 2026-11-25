// Diagnostic only (not a check): (round 3b: E fresh-page palace load, F programs compiled after the palace card) names (A) the texture left on the GPU by each Rumble/palace cycle (check 1703), (B) the geometries first
// uploaded during check 401's door round trips, (C) the textures not back after a context restore (check 1705), (D) why the 杂甲 bot casts no
// copy in check 170's seeds. INT round 3, 25 Nov. Run: node tests/diag17f.mjs (GitHub runner, job mode cmd).
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
const { chromium } = await import('playwright');
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wasm': 'application/wasm' };
const server = createServer(async (req, res) => { const u = decodeURIComponent(req.url.split('?')[0]); const p = normalize(join(ROOT, u === '/' ? 'index.html' : u)); try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); } }).listen(0);
const URL0 = `http://127.0.0.1:${server.address().port}/?lock&tier=medium&bots=0&pkit=placeholder&layout=proto`;
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });

const mk = async () => { const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } }), pg = await ctx.newPage(), log = [];
  pg.on('pageerror', (e) => log.push('PAGEERR ' + String(e).slice(0, 300))); pg.on('console', (m) => { if (m.type() === 'error' || m.type() === 'warning') log.push('CONSOLE ' + m.type() + ' ' + m.text().slice(0, 300)); });
  return { ctx, pg, log }; };
const idle = (pg) => pg.waitForFunction(() => !__game.loadBusy(), null, { timeout: 180000 });
const toPalace = () => { const G = __game; G.setSeed(12345); G.pickMode('palace'); G.pickSchool(0); };
const toRumble = () => { const G = __game; G.setSeed(12345); G.pickMode('rumble'); G.pickSchool(0); };
const ld = () => { const l = __game.load(); return { phase: l.phase, kind: l.kind, step: l.step, palace: l.palace, visS: +l.visS.toFixed(2), led: l.led, ptex: l.ptex, pset: l.pset, err: document.getElementById('err').textContent.slice(0, 400), chars: __game.chars().ready, t: Math.round(performance.now()) }; };

// ---- H: checks 1704/1708 controls. Page A (the suite's main page stand-in) in a live palace run; page B fresh: its first palace card, with the
// step timeline. Then the same with page A paused in the mode menu (no frames drawn behind the menu).
const A = await mk();
await A.pg.goto(URL0, { timeout: 120000 }); await A.pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
await A.pg.evaluate(toRumble); await idle(A.pg); await A.pg.evaluate(toPalace); await idle(A.pg);
const fresh = async (tag, saves) => {
  const B = await mk();
  if (saves) await B.pg.addInitScript((sv) => { for (const k in sv) localStorage.setItem(k, sv[k]); }, saves);
  const t0 = Date.now();
  await B.pg.goto(URL0, { timeout: 120000 }); await B.pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  const r0 = await B.pg.evaluate(ld); const tl = []; let last = '';
  await B.pg.evaluate(toPalace);
  for (let i = 0; i < 400; i++) { const s = await B.pg.evaluate(() => { const l = __game.load(); return { phase: l.phase, k: l.kind + ':' + l.step, visS: +l.visS.toFixed(1), fr: __game.state().frames }; }); if (s.k !== last) { tl.push(s.k + '@' + ((Date.now() - t0) / 1000).toFixed(1) + 's vis' + s.visS + ' fr' + s.fr); last = s.k; } if (s.phase === 'idle') break; await B.pg.waitForTimeout(100); }
  const r1 = await B.pg.evaluate(ld);
  console.log(`H ${tag} readyAt ${r0.t} ms (${r0.kind}:${r0.step} palace ${r0.palace}) -> palace ${r1.palace} capped ${r1.led.capped} ms ${r1.led.ms} kind ${r1.led.kind} failed [${r1.led.failed}] wall ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  console.log('  H timeline ' + tl.join(' | '));
  for (const s of B.log) console.log('  H ' + s);
  await B.ctx.close();
};
const aFps = async () => { const f0 = await A.pg.evaluate(() => __game.state().frames); await A.pg.waitForTimeout(2000); return ((await A.pg.evaluate(() => __game.state().frames)) - f0) / 2; };
console.log('H A live palace fps ' + await aFps());
await fresh('A-live', null);
await fresh('A-live+saves', { 'empressDecrees.audio': '{bad', 'empressDecrees.mode': 'palace', 'empressDecrees.school': '99' });
await A.pg.evaluate(() => { __game.pickMode('rumble'); });
console.log('H A in menu fps ' + await aFps());
await fresh('A-menu', null);
await A.ctx.close();
await browser.close(); server.close();
