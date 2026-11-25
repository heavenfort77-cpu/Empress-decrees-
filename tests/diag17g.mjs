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
// ---- E: checks 1704/1708: a fresh page (boots into the palace), then the palace picked again.
{
  const { ctx, pg, log } = await mk();
  await pg.goto(URL0, { timeout: 120000 }); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  console.log('E ready ' + JSON.stringify(await pg.evaluate(ld)));
  await pg.evaluate(toPalace);
  for (let i = 0; i < 40; i++) { const s = await pg.evaluate(ld); console.log('E poll ' + i + ' ' + JSON.stringify({ phase: s.phase, kind: s.kind, step: s.step, palace: s.palace, visS: s.visS, capped: s.led.capped, ledKind: s.led.kind, ms: s.led.ms, t: s.t, err: s.err })); if (s.phase === 'idle') break; await pg.waitForTimeout(1000); }
  await idle(pg); console.log('E after ' + JSON.stringify(await pg.evaluate(ld)));
  for (const s of log) console.log('  E ' + s);
  await pg.evaluate(toRumble); await idle(pg); await pg.evaluate(toPalace); await idle(pg); console.log('E again ' + JSON.stringify(await pg.evaluate(ld)));
  await ctx.close();
}
// ---- F: check 507: programs after the palace card, at the start of the court fight and after it; the names that were not there at the card's end.
{
  const { ctx, pg, log } = await mk();
  const g = async (fn, a) => { await idle(pg); return pg.evaluate(fn, a); };
  await pg.goto(URL0, { timeout: 120000 }); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await g(toRumble); await g(toPalace); await idle(pg);
  const f = await g(() => {
    const G = __game, C = G.config, o = {}, names = () => G.progs().p.map((s) => s.split('|')[0] + '|' + s.split('|').slice(2).join('|')).sort();
    const diff = (a, b) => { const m = {}; for (const x of a) m[x] = (m[x] || 0) - 1; for (const x of b) m[x] = (m[x] || 0) + 1; return Object.keys(m).filter((k) => m[k] !== 0).map((k) => (m[k] > 0 ? '+' : '-') + k); };
    const A = names(); o.card = { kind: G.load().led.kind, prog1: G.load().led.prog1, now: A.length };
    for (const k in C.PAL_SIM.guard) C.PAL_SIM.guard[k] = 0; if (C.BURN) C.BURN.on = false;
    G.setSeed(12345); G.setMode('palace'); G.setBots(8); G.reset();
    const p = G.palace(), R = Object.fromEntries(p.rooms.map((r) => [r.id, r]));
    const B = names(); o.afterReset = { n: B.length, diff: diff(A, B), led: G.load().led.kind + ':' + G.load().led.prog1, busy: G.loadBusy() };
    G.setHp(1e9); G.teleport(R.court.cx, R.court.cz); G.step(1);
    for (let i = 0; i < G.palSim().recs.length; i++) G.palSimSet(i, 'court', 100, 0);
    o.pre = G.render(true).programs; const Cn = names(); o.atFight = { n: Cn.length, diff: diff(B, Cn) };
    G.step(120); G.render(true); G.step(180); G.render(true); const D = names(); o.afterFight = { n: D.length, diff: diff(Cn, D) };
    return o;
  });
  console.log('F ' + JSON.stringify(f));
  console.log('F led after ' + JSON.stringify(await g(() => __game.load().led)));
  for (const s of log) console.log('  F ' + s);
  // ---- G: check 907: rigs shown and crowd batches drawn in the empty scene and with both squads.
  const q = await g(() => {
    const G = __game, o = { rows: [] }, A = [-7, -6];
    G.setMode('rumble'); G.setSeed(12345); G.setBots(0); G.reset(); G.teleport(-7, -6);
    const empty = G.render(true); o.empty = { calls: empty.calls, on: G.chars().on, drawn: G.chars().crowdDrawn, dead: G.player().dead, hp: G.state().hp };
    G.guardSpawn('huangjia', ['wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'nu', 'che'], A[0], A[1] + 5, { fz: -1, open: true });
    G.guardSpawn('fanzei', ['qs', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'fs', 'ss', 'ss'], A[0], A[1] - 5, { fz: 1, school: 'nong' });
    for (let k = 0; k < 8; k++) { G.step(10); const r = G.guards(), rr = G.render(true), tells = r.list.filter((u) => u.alive && u.tellStaged).length + (G.fz().suits[0].zm.on ? 1 : 0);
      o.rows.push({ calls: rr.calls, tells, extra: rr.calls - empty.calls - tells, drawn: G.chars().crowdDrawn, on: G.chars().on, dead: G.player().dead, hp: Math.round(G.state().hp), falling: G.state().falling }); }
    G.reset(); return o;
  });
  console.log('G ' + JSON.stringify(q));
  await ctx.close();
}
await browser.close(); server.close();
