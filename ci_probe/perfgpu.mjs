// Real-GPU frame-rate probe (GitHub macOS runner). Serves the game, opens it in Chromium on the real GPU (ANGLE Metal), and times frames
// with requestAnimationFrame for each scene: 6 s settle + 20 s timed, 1920x1080, tier locked. No game changes: scenes are set up through
// the existing __game hooks and CONFIG, as the checks do. Usage: node ci_probe/perfgpu.mjs [--soft]  (--soft = SwiftShader, for a local syntax run)
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';

let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const SOFT = process.argv.includes('--soft');
const SETTLE = Number(process.env.SETTLE_S || 6), TIMED = Number(process.env.TIMED_S || 20);
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript' };
// Controls for the ladder: an empty page, and the same with a fixed full-screen dark div (no WebGL, no game).
const EMPTY = (div) => `<!doctype html><html><body style="margin:0;background:#120d16">${div ? '<div style="position:fixed;inset:0;background:#120d16;z-index:8"></div>' : ''}<script>window.__game={render:()=>({calls:0,tris:0,programs:0,geoms:0,texs:0})};window.__ready=true;</script></body></html>`;
const server = createServer(async (req, res) => {
  if (req.url.startsWith('/__empty')) { res.writeHead(200, { 'content-type': 'text/html' }); res.end(EMPTY(req.url.includes('div'))); return; }
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/`;
const ARGS = SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit'];
const browser = await chromium.launch({ args: ARGS });

// Scene setups run inside the page after __ready. Each returns nothing; a driver (optional) runs every 250 ms of real time during the timing.
const SCENES = {
  // (a) reference: the royale start with no bots, idle (camera follows a standing player).
  reference: { q: 'lock&tier=medium&bots=0', setup: () => { __game.setSeed(12345); __game.reset(); } },
  // (b) heaviest royale: 9 suits brought together at the west camp as the 7-cub kennel wave lands; bots fight at once (peace off, ramp done),
  // the player on the autopilot, a crown (plates on a bot), marks renewed; health topped up so the fight keeps all suits in it (real AI, skills, effects).
  heavy: { q: 'lock&tier=medium&bots=8', setup: () => {
    const G = __game, C = G.config;
    C.KENNEL.waves = [[['stalker', 0], ['stalker', 0], ['stalker', 0], ['stalker', 0], ['howler', 0], ['howler', 0], ['howler', 0]]];
    G.setSeed(12345); G.reset(); G.setWatch(true);
    G.step(Math.round((C.KENNEL.firstS + 0.2) / C.STEP));
    C.BOT.engage.peaceS = 0; C.BOT.engage.rampS = 0.01; C.BOT.engage.p0 = 1;
    for (let i = 0; i < 8; i++) G.setBotHp(i, 100);
    const cx = G.camps[0][0], cz = G.camps[0][1] + 4; G.teleport(cx, cz);
    for (let i = 0; i < 8; i++) G.placeBot(i, cx - 4.5 + (i % 4) * 3, cz + 2 + Math.floor(i / 4) * 2.5);
    G.plateTo(3, 'stalker'); G.plateTo(3, 'howler'); G.forceDecree('nodash', 'W1', 60); G.setHp(1e9); G.autoPlayer(true);
    window.__bhp = G.bots().list.map((q) => q.hp);
  }, driver: () => {
    const G = __game; G.setHp(1e9);
    const b = G.bots().list; for (let i = 0; i < b.length; i++) if (!b[i].dead && b[i].hp < window.__bhp[i] * 0.9) G.setBotHp(i, window.__bhp[i]);
    const s = G.suits(); for (let i = 0; i < s.length; i++) if (s[i].markT < 0.2 && !s[i].dead && (i % 3 === 0)) G.breakBy(i - 1);
  } },
  // (c) the apex hunt mid-fight: demon and both minions alive, the player attacks the nearest unit and casts every skill when ready.
  hunt: { q: 'lock&tier=medium&bots=0', setup: () => {
    const G = __game, C = G.config; G.setSeed(12345); G.reset(); G.startHunt(); G.step(Math.round((C.APEX.wakeS + 0.2) / C.STEP)); G.setHp(1e9);
    const h0 = G.hunt(); window.__uhp = h0.units.map((u) => u.hp); G.teleport(h0.units[0].x, h0.units[0].z + 5);
  }, driver: () => {
    const G = __game, h = G.hunt(); G.setHp(1e9);
    for (let i = 0; i < h.units.length; i++) if (h.units[i].alive && h.units[i].hp < window.__uhp[i] * 0.4) G.zaUnitSet(h.units[i].kind, { hp: window.__uhp[i] });
    let ti = 0; for (let i = 1; i < 3; i++) if (h.units[i].alive && h.units[i].seen) ti = i;
    if (G.attackUnit(ti)) { const u = h.units[ti], cd = G.skills(); for (let k = 0; k < 3; k++) if (cd[k] === 0) G.cast(k, u.x, u.z); }
  } },
  // (d) the school select open (no bots in the address, so it opens at load), nothing chosen.
  select: { q: 'lock&tier=medium', setup: () => {} },
  // Ladder controls for the select screen: empty page, empty page plus a full-screen div, the select with the game canvas hidden.
  empty: { path: '__empty', q: '', setup: () => {} },
  emptydiv: { path: '__empty_div', q: '', setup: () => {} },
  select_nocanvas: { q: 'lock&tier=medium', setup: () => { document.querySelector('canvas').style.display = 'none'; } },
  // (b) again on the low tier.
  heavy_low: null,
  // (e) The Burning Palace (PERF2, 24 Nov): the full layout, the player standing in the forecourt (48x30 m, the largest room), nothing spawned.
  palace_room: { q: 'lock&tier=medium&bots=0&mode=palace', setup: () => {
    const G = __game, C = G.config; C.PAL_ESC.squads = C.PAL_ESC.squads.map(() => 0);
    G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset(); G.step(2); G.setHp(1e9);
    const R = Object.fromEntries(G.palPlan().rooms.map((r) => [r.id, r])); G.teleport(R.fore.cx, R.fore.cz + 6); G.step(30);
    window.__pal = G.palace().cur;
  } },
  // (f) the heaviest palace room: the forecourt (centre wing, never burns; lions, mercury, 华表, vats, giants) at 76 s game time, so the second
  // wave's wing is warned in the settle and falls in the timed window; a full 皇家 squad and a full 反贼 squad, 2 awake giants and 3 rivals
  // placed in the room, 8 rivals in the match, the player on the autopilot. Health topped up so the fight stays full. Smoke is not in this room
  // (only the two gardens have it): see palace_garden.
  palace_heavy: { q: 'lock&tier=medium&bots=8&mode=palace', setup: () => {
    const G = __game, C = G.config;
    G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset(); G.setHp(1e9);
    for (let k = 0; k < (window.__stepN || 760); k++) { G.setHp(1e9); G.step(6); }
    const R = Object.fromEntries(G.palPlan().rooms.map((r) => [r.id, r])), f = R[window.__room || 'fore'];
    G.teleport(f.cx, f.cz + 4); G.step(30); G.setHp(1e9);
    window.__sq = () => {
      G.guardSpawn('huangjia', ['wz', 'zu', 'zu', 'zu', 'zu', 'dun', 'dun', 'nu', 'nu', 'nu', 'che', 'zu'], f.cx - 6, f.cz - 5, { open: true });
      G.guardSpawn('fanzei', ['qs', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'fs', 'fs', 'ss', 'ss', 'ls'], f.cx + 6, f.cz - 5, { school: 'mo' });
    };
    window.__sq();
    let w = G.pieces2State().awake; for (let k = w; k < 2; k++) G.giantWake();
    G.step(Math.ceil(C.PIECES2.giant.wakeS * 60) + 2);
    const gs = G.pieces2State().giants; let n = 0;
    for (const g of gs) if (g.st !== 0 && g.alive !== false && n < 2) { G.giantPlace(g.i, f.cx + (n ? 7 : -7), f.cz + 3); n++; }
    for (let k = 0; k < 3; k++) G.palPlaceBot(k, f.cx - 3 + 3 * k, f.cz + 1);
    G.autoPlayer(true);
    const s = G.palace(), b = G.burnState(), p2 = G.pieces2State();
    window.__info = 'room ' + s.cur + ' t ' + Math.round(s.t) + ' burn ' + b.wing + '/' + b.st + ' falls ' + b.falls + ' giants awake ' + p2.awake + ' guards ' + G.guards().n;
  }, driver: () => {
    const G = __game; G.setHp(1e9);
    const p2 = G.pieces2State(); for (const g of p2.giants) if (g.st !== 0 && g.alive && g.hp < p2.hpMax * 0.5) G.giantSetHp(g.i, p2.hpMax);
    const b = G.bots().list; for (let i = 0; i < 3 && i < b.length; i++) if (!b[i].dead && b[i].hp < 50) G.setBotHp(i, 100);
    if (G.guards().n < 12) window.__sq();
    const s = G.palace(), bs = G.burnState(); window.__info2 = 'end room ' + s.cur + ' t ' + Math.round(s.t) + ' burn ' + bs.wing + '/' + bs.st + ' falls ' + bs.falls + ' guards ' + G.guards().n + ' awake ' + p2.awake;
  } },
  // (g) the same fight in the southeast garden (its smoke clouds, a clock and a vat) at 30 s game time: its wing burns second (warned at 80 s),
  // so it stands through the timed window while the first wing (southwest) falls out of view.
  palace_garden: null,
  // (h) first draw of each palace room (check 1207): geometry count and the worst frame in the 1.5 s after entering 5 rooms not drawn yet.
  palace_first: { q: 'lock&tier=medium&bots=0&mode=palace', custom: true },
};
SCENES.heavy_low = { ...SCENES.heavy, q: 'lock&tier=low&bots=8' };
SCENES.palace_heavy_low = { ...SCENES.palace_heavy, q: 'lock&tier=low&bots=8&mode=palace' };
SCENES.palace_garden = { ...SCENES.palace_heavy, pre: () => { window.__room = 'garden_se'; window.__stepN = 300; } };

async function renderer(page) {
  return page.evaluate(() => { const c = document.createElement('canvas'), gl = c.getContext('webgl2'); if (!gl) return 'no WebGL2'; const d = gl.getExtension('WEBGL_debug_renderer_info'); return d ? gl.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'unknown'; });
}

// First draw of palace rooms (check 1207): the player is moved into 5 rooms never drawn in this page, one by one; for each the geometry and texture
// counts before and 1.5 s after, and the worst and second-worst frame in that 1.5 s (the game runs at real time between moves).
const FIRST_DRAW = async () => {
  const G = __game, C = G.config; C.PAL_ESC.squads = C.PAL_ESC.squads.map(() => 0);
  G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset(); G.step(2); G.setHp(1e9);
  const wait = (s) => new Promise((res) => setTimeout(res, s * 1000));
  const frames = (s) => new Promise((res) => { const d = []; let last = 0, run = true; const f = (t) => { if (last) d.push(t - last); last = t; if (run) requestAnimationFrame(f); else res(d); }; requestAnimationFrame(f); setTimeout(() => { run = false; }, s * 1000); });
  await wait(3);
  const R = Object.fromEntries(G.palPlan().rooms.map((r) => [r.id, r])), ids = ['court_w', 'garden_sw', 'fore', 'hall_ming', 'bridge_ef'], out = [];
  const g00 = G.render(false);
  for (const id of ids) {
    const a = G.render(false), r = R[id]; G.teleport(r.cx, r.cz); const d = await frames(1.5), b = G.render(false);
    d.sort((x, y) => y - x);
    out.push({ room: id, cur: G.palace().cur, geo: a.geoms + '>' + b.geoms, tex: a.texs + '>' + b.texs, prog: a.programs + '>' + b.programs, worst: +d[0].toFixed(1), second: +(d[1] || 0).toFixed(1), n: d.length });
  }
  const back = G.render(false); const R2 = R.court_w; G.teleport(R2.cx, R2.cz); const d2 = await frames(1.5); d2.sort((x, y) => y - x); const back2 = G.render(false);
  return { start: { geo: g00.geoms, tex: g00.texs, prog: g00.programs }, rooms: out, revisit: { room: 'court_w', geo: back.geoms + '>' + back2.geoms, worst: +d2[0].toFixed(1) } };
};

const rows = []; let gpu = '';
let FILE = ''; try { FILE = (await readFile(new URL('scenes.txt', import.meta.url), 'utf8')).trim(); } catch { /* default list */ }
const LIST = (process.env.SCENES || FILE || 'reference,heavy,hunt,select,heavy_low').split(',');
for (const name of LIST) {
  const sc = SCENES[name];
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e).slice(0, 160)));
  await page.goto(BASE + (sc.path || '') + '?' + sc.q);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
  if (!gpu) gpu = await renderer(page);
  if (sc.custom) {
    const r = await page.evaluate(FIRST_DRAW);
    rows.push({ scene: name, errs: errs.length, err0: errs[0] || '', ...r });
    console.log('ROW ' + JSON.stringify(rows[rows.length - 1]));
    await page.close();
    continue;
  }
  const t0 = Date.now();
  if (sc.pre) await page.evaluate(`(${sc.pre.toString()})()`);
  await page.evaluate(`(${sc.setup.toString()})()`);
  const setupMs = Date.now() - t0;
  const drv = sc.driver ? sc.driver.toString() : '() => {}';
  const r = await page.evaluate(async ({ drv, SETTLE, TIMED }) => {
    const driver = eval('(' + drv + ')');
    const id = setInterval(() => { try { driver(); } catch (e) { window.__drvErr = String(e); } }, 250);
    const mem = () => ({ heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1 });
    const wait = (s) => new Promise((res) => setTimeout(res, s * 1000));
    await wait(SETTLE);
    const m0 = mem(), g0 = __game.render(false);
    const lt = []; let ob = null; try { ob = new PerformanceObserver((l) => { for (const e of l.getEntries()) lt.push(e.duration); }); ob.observe({ type: 'longtask' }); } catch (e) { /* no longtask API */ }
    const d = []; let last = 0, run = true;
    await new Promise((res) => { const f = (t) => { if (last) d.push(t - last); last = t; if (run) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); setTimeout(() => { run = false; }, TIMED * 1000); });
    clearInterval(id); if (ob) ob.disconnect();
    const m1 = mem(), info = __game.render(false);
    d.sort((a, b) => a - b);
    const sum = d.reduce((a, b) => a + b, 0), n = d.length;
    const extra = {};
    try { extra.bots = __game.bots().list.filter((q) => !q.dead).length; extra.cubs = __game.cubs().list.filter((u) => u.alive).length; } catch (e) { /* not in a match */ }
    try { const h = __game.hunt(); if (h.phase === 'hunt') extra.hunt = h.phase + ' alive ' + h.units.filter((u) => u.alive).length + ' hits ' + h.hits; } catch (e) { /* no hunt */ }
    return { frames: n, fps: +(n / (sum / 1000)).toFixed(1), p50: +d[Math.floor(n * 0.5)].toFixed(1), p95: +d[Math.floor(n * 0.95)].toFixed(1), worst: +d[n - 1].toFixed(1),
      over20: +(100 * d.filter((x) => x > 20).length / n).toFixed(1), over33: d.filter((x) => x > 33.4).length,
      calls: info.calls, tris: info.tris, programs: info.programs, geoms: info.geoms, texs: info.texs, heap0: m0.heap, heap1: m1.heap, longN: lt.length, longMax: Math.round(Math.max(0, ...lt)), longSum: Math.round(lt.reduce((a, b) => a + b, 0)), geo0: g0.geoms, tex0: g0.texs, drvErr: window.__drvErr || '', info: window.__info || '', info2: window.__info2 || '', ...extra };
  }, { drv, SETTLE, TIMED });
  rows.push({ scene: name, setupMs, errs: errs.length, err0: errs[0] || '', ...r });
  console.log('ROW ' + JSON.stringify(rows[rows.length - 1]));
  await page.close();
}
console.log('RENDERER ' + gpu + (/swiftshader|llvmpipe|software/i.test(gpu) ? '  (NOT a real GPU)' : ''));
console.log('scene       fps    p50   p95   worst  >20ms%  >33ms  calls  tris    prog geo  heap MB  geo/tex start-end  live');
for (const r of rows) console.log([r.scene.padEnd(10), String(r.fps).padStart(6), String(r.p50).padStart(5), String(r.p95).padStart(5), String(r.worst).padStart(6), String(r.over20).padStart(6), String(r.over33).padStart(6),
  String(r.calls).padStart(6), String(r.tris).padStart(7), String(r.programs).padStart(4), String(r.geoms).padStart(4), (r.heap0 + '-' + r.heap1).padStart(9), (r.geo0 + '-' + r.geoms + '/' + r.tex0 + '-' + r.texs).padStart(13), ' ' + (r.bots !== undefined ? 'bots ' + r.bots + ' cubs ' + r.cubs : '') + (r.hunt || '') + ' long ' + r.longN + '/' + r.longMax + 'ms/' + r.longSum + 'ms' + (r.errs ? ' ERR ' + r.err0 : '') + (r.drvErr ? ' DRV ' + r.drvErr.slice(0, 80) : '')].join(' '));
await browser.close(); server.close();
