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
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary' };
// Controls for the ladder: an empty page, and the same with a fixed full-screen dark div (no WebGL, no game).
const EMPTY = (div) => `<!doctype html><html><body style="margin:0;background:#120d16">${div ? '<div style="position:fixed;inset:0;background:#120d16;z-index:8"></div>' : ''}<script>window.__game={render:()=>({calls:0,tris:0,programs:0,geoms:0,texs:0})};window.__ready=true;</script></body></html>`;
// Control (item (g)): plain three.js r171 from lib/, 30 boxes on a floor, one directional light with a 2048 shadow map re-rendered every frame,
// standard materials, uncapped like the game. Not our game code: if it shows the same long frames, they come from the machine.
const WEBGL_MIN = `<!doctype html><html><body style="margin:0;background:#120d16"><script type="importmap">{"imports":{"three":"/lib/three.module.min.js"}}</script>
<script type="module">import * as THREE from 'three';
const r = new THREE.WebGLRenderer({ antialias: false }); r.setPixelRatio(1); r.setSize(innerWidth, innerHeight); r.shadowMap.enabled = true; document.body.appendChild(r.domElement);
const sc = new THREE.Scene(), cam = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.5, 120); cam.position.set(0, 14, 16); cam.lookAt(0, 0, 0);
sc.add(new THREE.HemisphereLight(0xffffff, 0x222233, 0.8)); const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(8, 16, 6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sc.add(sun);
const fl = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), new THREE.MeshStandardMaterial({ color: 0x665544 })); fl.rotation.x = -Math.PI / 2; fl.receiveShadow = true; sc.add(fl);
const g = new THREE.BoxGeometry(1, 2, 1), bs = [];
for (let i = 0; i < 30; i++) { const m = new THREE.Mesh(g, new THREE.MeshStandardMaterial({ color: 0x8899aa + i * 997 })); m.position.set((i % 6) * 3 - 7.5, 1, Math.floor(i / 6) * 3 - 6); m.castShadow = m.receiveShadow = true; sc.add(m); bs.push(m); }
window.__game = { render: () => ({ calls: r.info.render.calls, tris: r.info.render.triangles, programs: r.info.programs.length, geoms: r.info.memory.geometries, texs: r.info.memory.textures }) };
const f = (t) => { requestAnimationFrame(f); for (let i = 0; i < bs.length; i++) bs[i].rotation.y = t * 0.001 + i; r.render(sc, cam); };
r.compile(sc, cam); requestAnimationFrame(f); window.__ready = true;</script></body></html>`;
const server = createServer(async (req, res) => {
  if (req.url.startsWith('/__webglmin')) { res.writeHead(200, { 'content-type': 'text/html' }); res.end(WEBGL_MIN); return; }
  if (req.url.startsWith('/__empty')) { res.writeHead(200, { 'content-type': 'text/html' }); res.end(EMPTY(req.url.includes('div'))); return; }
  const p = normalize(join(ROOT, decodeURIComponent(req.url.split('?')[0]) === '/' ? 'index.html' : decodeURIComponent(req.url.split('?')[0])));
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/`;
const ARGS = SOFT ? ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
  : process.env.VSYNC === '1' ? ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal']
  : ['--ignore-gpu-blocklist', '--enable-gpu', '--enable-webgl', '--use-angle=metal', '--disable-gpu-vsync', '--disable-frame-rate-limit'];
console.log('MODE ' + (process.env.VSYNC === '1' ? 'vsync on (frame limit kept)' : 'vsync off, frame limit off'));
// Item (g) control, out of the browser: a separate Node process on the same machine ticks every 2 ms and logs every gap over 30 ms in epoch
// ms. If each long browser frame lines up with a gap here, the whole machine (VM) stalled, not the page. Lines: "GAP <start> <end>".
const { spawn } = await import('node:child_process');
const STALL_SRC = "const {performance:P}=require('perf_hooks');let l=P.timeOrigin+P.now();setInterval(()=>{const n=P.timeOrigin+P.now();if(n-l>30)process.stdout.write('GAP '+l.toFixed(1)+' '+n.toFixed(1)+'\\n');l=n;},2);";
const stallProc = spawn(process.execPath, ['-e', STALL_SRC], { stdio: ['ignore', 'pipe', 'inherit'] });
const nodeGaps = []; let stallBuf = '';
stallProc.stdout.on('data', (b) => { stallBuf += b; let k; while ((k = stallBuf.indexOf('\n')) >= 0) { const l = stallBuf.slice(0, k); stallBuf = stallBuf.slice(k + 1); const m = l.split(' '); if (m[0] === 'GAP') nodeGaps.push([+m[1], +m[2]]); } });
let browser = null;
// Measurement only (item (g), 24 Nov): every page gets an init script that times WebGL calls that can block (shader compile/link and their status
// reads, texture and buffer uploads) into window.__glog [t, ms, name, arg], counts them in window.__glc, and keeps the game's GL context in
// window.__gl for a GPU timer query per frame. No game code changes.
const INIT = `(() => {
  const now = () => performance.now(), LOG = window.__glog = [], C = window.__glc = { link: 0, compile: 0, buf: 0, bufBytes: 0, tex: 0 };
  const push = (e) => { LOG.push(e); if (LOG.length > 40000) LOG.splice(0, 20000); };
  // Item (g): every text change in the page that holds CJK characters, from page start: window.__cjkLog [t, element, text].
  const CJ = window.__cjkLog = [];
  document.addEventListener('DOMContentLoaded', () => { new MutationObserver((l) => { const t = now(); for (const m of l) { const e = m.target.nodeType === 3 ? m.target.parentNode : m.target; if (!e || CJ.length > 300) continue;
    const tx = e.textContent || ''; if (/[\u3000-\u9fff]/.test(tx)) CJ.push([t, e.id || (e.parentNode && e.parentNode.id) || e.className || e.nodeName, tx.slice(0, 50)]); } }).observe(document.body, { subtree: true, childList: true, characterData: true }); });
  const og = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, ...a) { const c = og.call(this, type, ...a); if (c && /webgl/.test(type) && !window.__gl) window.__gl = c; return c; };
  const wrap = (P, name, f) => { const o = P[name]; if (!o) return; P[name] = function (...a) { const t0 = now(), r = o.apply(this, a), d = now() - t0; f(t0, d, a); return r; }; };
  for (const P of [WebGL2RenderingContext.prototype, WebGLRenderingContext.prototype]) {
    wrap(P, 'linkProgram', (t, d) => { C.link++; push([t, d, 'linkProgram', C.link]); });
    wrap(P, 'compileShader', (t, d) => { C.compile++; push([t, d, 'compileShader', C.compile]); });
    for (const n of ['getProgramParameter', 'getShaderParameter', 'getProgramInfoLog', 'getShaderInfoLog', 'getError', 'readPixels', 'getUniformLocation', 'getAttribLocation', 'finish', 'clientWaitSync'])
      wrap(P, n, (t, d, a) => { if (d > 0.5) push([t, d, n, a[1] | 0]); });
    for (const n of ['texImage2D', 'texSubImage2D', 'texStorage2D', 'texImage3D', 'texSubImage3D', 'compressedTexImage2D', 'generateMipmap'])
      wrap(P, n, (t, d) => { C.tex++; push([t, d, n, C.tex]); });
    wrap(P, 'bufferData', (t, d, a) => { const b = (a[1] && a[1].byteLength) || (typeof a[1] === 'number' ? a[1] : 0); C.buf++; C.bufBytes += b; if (d > 0.5 || b > 16384) push([t, d, 'bufferData', b]); });
  }
})();`;
// CPU profile stretches: contiguous non-idle samples longer than minMs; top self-time leaves and their callers (3 frames up).
// The CPU profile samples inside each long frame [a, b] (performance.now times), lined up through the __probeMark spin.
function perFrame(prof, markT, frames) {
  const nodes = new Map(prof.nodes.map((n) => [n.id, n])), parent = new Map();
  for (const n of prof.nodes) for (const c of n.children || []) parent.set(c, n.id);
  const nm = (id) => { const cf = nodes.get(id).callFrame; return (cf.functionName || '(anon)') + (cf.url ? ':' + (cf.lineNumber + 1) : ''); };
  const path = (id) => { const a = []; let k = id; for (let i = 0; i < 5 && k !== undefined; i++) { a.push(nm(k)); k = parent.get(k); } return a.join(' < '); };
  const ts = []; let t = 0, mark = -1;
  for (let i = 0; i < prof.samples.length; i++) { t += (prof.timeDeltas[i] || 0) / 1000; ts.push(t); if (mark < 0 && nodes.get(prof.samples[i]).callFrame.functionName === '__probeMark') mark = t; }
  if (mark < 0) return [{ err: 'mark not found' }];
  const off = markT - mark;
  return frames.map(([a, b]) => { const m = new Map(); let n = 0;
    for (let i = 0; i < ts.length; i++) { const x = ts[i] + off; if (x < a || x > b) continue; n++; const k = path(prof.samples[i]); m.set(k, (m.get(k) || 0) + 1); }
    let gmax = 0, prev = -1; for (let i = 0; i < ts.length; i++) { const x = ts[i] + off; if (x < a - 50 || x > b) continue; if (prev >= 0) gmax = Math.max(gmax, x - prev); prev = x; }
    return { ms: Math.round(b - a), samples: n, profGapMax: Math.round(gmax), top: [...m].sort((p, q) => q[1] - p[1]).slice(0, 6).map(([k, v]) => v + ' ' + k) }; });
}
function stretches(prof, minMs) {
  const nodes = new Map(prof.nodes.map((n) => [n.id, n])), parent = new Map();
  for (const n of prof.nodes) for (const c of n.children || []) parent.set(c, n.id);
  const nm = (id) => { const cf = nodes.get(id).callFrame; return (cf.functionName || '(anon)') + (cf.url ? ':' + (cf.lineNumber + 1) : ''); };
  const path = (id) => { const a = []; let k = id; for (let i = 0; i < 4 && k !== undefined; i++) { a.push(nm(k)); k = parent.get(k); } return a.join(' < '); };
  const out = []; let cur = null, t = 0;
  for (let i = 0; i < prof.samples.length; i++) {
    const id = prof.samples[i], dt = (prof.timeDeltas[i] || 0) / 1000; t += dt;
    if (nodes.get(id).callFrame.functionName === '(idle)') { if (cur && cur.ms >= minMs) out.push(cur); cur = null; continue; }
    if (!cur) cur = { at: +(t / 1000).toFixed(2), ms: 0, self: new Map() };
    cur.ms += dt; const k = path(id); cur.self.set(k, (cur.self.get(k) || 0) + dt);
  }
  if (cur && cur.ms >= minMs) out.push(cur);
  return out.map((c) => ({ at_s: c.at, ms: Math.round(c.ms), top: [...c.self].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k, v]) => Math.round(v) + 'ms ' + k) }));
}

// Scene setups run inside the page after __ready. Each returns nothing; a driver (optional) runs every 250 ms of real time during the timing.
const SCENES = {
  // (a) reference: the royale start with no bots, idle (camera follows a standing player).
  reference: { q: 'lock&tier=medium&bots=0&perf=1', setup: () => { __game.setSeed(12345); __game.reset(); } },
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
  webglmin: { path: '__webglmin', q: '', setup: () => {} },
  // Batch 17a guard A/B (ci_probe/guards.html): 37 guard/rebel units; one difference per arm (see the page header).
  g_A0: { path: 'ci_probe/guards.html', q: 'arm=A0', setup: () => {} },
  g_Alod: { path: 'ci_probe/guards.html', q: 'arm=Alod&lod0=20', setup: () => {} },
  g_B0: { path: 'ci_probe/guards.html', q: 'arm=B0', setup: () => {} },
  g_caps: { path: 'ci_probe/guards.html', q: 'arm=caps', setup: () => {} },
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
  palace_heavy: { q: 'lock&tier=medium&bots=8&mode=palace&perf=1', setup: () => {
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
  // Map-scale proof (panel note 17, owner GO 25 Nov 02:2x): ci_probe/scale.html, box-only real-scale platform, streamed rooms, the heaviest
  // fight's unit counts following a bot that walks the route at 10 m/s. Not the shipped game. coll=scan = today's linear-scan collision rule.
  scale_med: { path: 'ci_probe/scale.html', q: 'tier=medium', setup: () => { window.__info = 'scale start ' + JSON.stringify(__game.stats()); }, driver: () => {
    const s = __game.stats(); window.__info2 = 'rooms ' + s.rooms + ' floors ' + s.floors + ' solids ' + s.solids + ' visited ' + s.visited + ' attach ' + s.attach + ' detach ' + s.detach + ' near ' + s.nearN + ' far ' + s.farN
      + ' units ' + s.unitsGR + ' spawns ' + s.spawns + ' deaths ' + s.deaths + ' despawn ' + s.despawn + ' shots ' + s.shots + ' step avg ' + (s.stepMs / s.steps).toFixed(3) + 'ms max ' + s.stepMax.toFixed(1) + 'ms checks/step ' + Math.round(s.checks / s.steps) + ' shadowRe ' + s.shadowRe + ' warmCalls ' + s.warmCalls + (window.__err ? ' ERR ' + window.__err.slice(0, 80) : '');
  } },
};
// Item (g) A/B (fresh browser each): base = index_base.html (the game before the fix), fix = index.html (the same game plus CONFIG.FONT_WARM, the only
// difference). heavy_* = the palace_heavy fight with its own banners; cjk_* / latin_* = the same fight plus one banner line written by the probe
// 3 s into the timed window, with CJK characters (as TEXT.voice_guard_break / rule_guard_break) or the same line in Latin letters only.
const INJ = (cjk) => `() => { const G = __game; G.setHp(1e9); const t = performance.now(); if (!window.__inj0) window.__inj0 = t;
  if (!window.__injDone && t - window.__inj0 > ${(SETTLE + 3) * 1000}) { window.__injDone = true; const v = document.querySelector('#banner .voice'), r = document.querySelector('#banner .rule');
    v.textContent = ${cjk ? "'Our 伍长 falls, and his square with him.'" : "'Our Wuzhang falls, and his square with him.'"}; r.textContent = ${cjk ? "'伍长 down: the 方阵 breaks. 反贼 华表 渠帅 奇正相生'" : "'Wuzhang down: the Fangzhen breaks. Fanzei Huabiao Qushuai Qizheng'"};
    document.getElementById('banner').style.display = 'block'; } }`;
SCENES.heavy_base = { ...SCENES.palace_heavy, path: 'index_base.html' };
SCENES.heavy_fix = { ...SCENES.palace_heavy };
SCENES.cjk_base = { ...SCENES.palace_heavy, path: 'index_base.html', timed: 15, driver: INJ(true) };
SCENES.cjk_fix = { ...SCENES.palace_heavy, timed: 15, driver: INJ(true) };
SCENES.latin_base = { ...SCENES.palace_heavy, path: 'index_base.html', timed: 15, driver: INJ(false) };
SCENES.reference30 = { ...SCENES.reference, timed: 30 };
SCENES.scale_med_scan = { ...SCENES.scale_med, q: 'tier=medium&coll=scan' };
SCENES.scale_low = { ...SCENES.scale_med, q: 'tier=low' };
SCENES.heavy_low = { ...SCENES.heavy, q: 'lock&tier=low&bots=8' };
SCENES.palace_heavy_low = { ...SCENES.palace_heavy, q: 'lock&tier=low&bots=8&mode=palace' };
// Batch 17b A/B: the build before 17b (index_base.html = ab0473f) in the same job.
SCENES.room_base = { ...SCENES.palace_room, path: 'index_base.html' };
SCENES.heavylow_base = { ...SCENES.palace_heavy_low, path: 'index_base.html' };
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
  // A fresh browser per scene (item (g)): font and shader caches start cold in every scene, as for a new player.
  if (browser) await browser.close();
  // PURGE=1 (item (g)): the macOS file cache is flushed before each scene, so files the OS keeps after first use (fonts) start cold in every scene.
  if (process.env.PURGE === '1') { try { (await import('node:child_process')).execSync('sudo purge'); } catch (e) { console.log('PURGE failed ' + String(e).slice(0, 80)); } }
  browser = await chromium.launch({ args: ARGS });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const errs = []; page.on('pageerror', (e) => errs.push(String(e).slice(0, 160)));
  await page.addInitScript(INIT);
  const tLoad = Date.now();
  await page.goto(BASE + (sc.path || '') + '?' + sc.q);
  await page.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
  const loadMs = Date.now() - tLoad;
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
  // Batch 17b: a set the scene needs loads under its card first (the timing starts on play frames).
  await page.waitForFunction(() => !window.__game || !__game.loadBusy || !__game.loadBusy(), null, { timeout: 120000 });
  const setupMs = Date.now() - t0;
  const drv = sc.driver ? sc.driver.toString() : '() => {}';
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Profiler.enable'); await cdp.send('Profiler.setSamplingInterval', { interval: 500 }); await cdp.send('Profiler.start');
  const r = await page.evaluate(async ({ drv, SETTLE, TIMED }) => {
    const driver = eval('(' + drv + ')');
    const drvLog = [], stLog = [], loaf = [], loafT = [];
    const wk = new Worker(URL.createObjectURL(new Blob(['let l=performance.timeOrigin+performance.now();const g=[];setInterval(()=>{const n=performance.timeOrigin+performance.now();if(n-l>30)g.push([+l.toFixed(1),+n.toFixed(1)]);l=n;},2);onmessage=()=>postMessage(g);'], { type: 'text/javascript' }))); let loafN = 0, loafN100 = 0; const mut = [];
    const mo = new MutationObserver((l) => { const t = performance.now(); for (const m of l) { mut.push([t, (m.target.id || (m.target.parentNode && m.target.parentNode.id) || m.target.nodeName)]); if (mut.length > 5000) mut.splice(0, 2500); } });
    mo.observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true });
    const id = setInterval(() => { const t0 = performance.now(); try { driver(); } catch (e) { window.__drvErr = String(e); } const d = performance.now() - t0; if (d > 5) drvLog.push([Math.round(t0), +d.toFixed(1)]); }, 250);
    const stId = setInterval(() => { try { const G = __game, b = G.burnState(), p2 = G.pieces2State(); const sv = 'room ' + G.palace().cur + ' burn ' + b.wing + '/' + b.st + ' falls ' + b.falls + ' awake ' + p2.awake; if (!stLog.length || stLog[stLog.length - 1][1] !== sv) stLog.push([Math.round(performance.now()), sv]); if (stLog.length > 2000) stLog.shift(); } catch (e) { /* not palace */ } }, 100);
    let lo = null; try { lo = new PerformanceObserver((l) => { for (const e of l.getEntries()) { if (e.duration > 50) loafN++; if (e.duration > 100) loafN100++; if (e.duration > 90 && e.startTime >= tStart && tStart > markT0 && loafT.length < 40) loafT.push({ t0: e.startTime, ms: Math.round(e.duration), preRender: Math.round(e.renderStart ? e.renderStart - e.startTime : e.duration), styleLayoutPaint: Math.round(e.styleAndLayoutStart ? e.startTime + e.duration - e.styleAndLayoutStart : 0), scripts: e.scripts.map((x) => Math.round(x.duration) + 'ms ' + x.invokerType + ' ' + x.sourceFunctionName) });
      if (e.duration > 60 && loaf.length < 30) loaf.push({ at_s: +((e.startTime - tStart) / 1000).toFixed(2), ms: Math.round(e.duration), block: Math.round(e.blockingDuration),
      preRender: Math.round(e.renderStart ? e.renderStart - e.startTime : e.duration), scriptsInRender: Math.round(e.styleAndLayoutStart && e.renderStart ? e.styleAndLayoutStart - e.renderStart : 0), styleLayoutPaint: Math.round(e.styleAndLayoutStart ? e.startTime + e.duration - e.styleAndLayoutStart : 0),
      scripts: e.scripts.map((x) => Math.round(x.duration) + 'ms ' + x.invokerType + ' ' + x.invoker + ' ' + x.sourceFunctionName + ' @' + x.sourceCharPosition + (x.forcedStyleAndLayoutDuration > 1 ? ' layout ' + Math.round(x.forcedStyleAndLayoutDuration) : '')) }); } }); lo.observe({ type: 'long-animation-frame' }); } catch (e) { loaf.push({ none: String(e).slice(0, 60) }); }
    const gl = window.__gl, ext = gl && gl.getExtension('EXT_disjoint_timer_query_webgl2'), caps = 'timerQuery ' + !!ext + ' parallelCompile ' + !!(gl && gl.getExtension('KHR_parallel_shader_compile'));
    let q = null; const pend = [], gpu = [], disj = []; let tStart = performance.now(); const markT0 = tStart;
    const gpuTick = (t) => {
      if (!ext) return;
      if (q) { gl.endQuery(ext.TIME_ELAPSED_EXT); pend.push([q, t]); q = null; }
      while (pend.length && gl.getQueryParameter(pend[0][0], gl.QUERY_RESULT_AVAILABLE)) { const [pq, pt] = pend.shift(), dis = gl.getParameter(ext.GPU_DISJOINT_EXT), ns = gl.getQueryParameter(pq, gl.QUERY_RESULT); gl.deleteQuery(pq); if (!dis) gpu.push([pt, ns / 1e6]); else disj.push(Math.round(pt - tStart)); }
      if (pend.length < 16) { q = gl.createQuery(); gl.beginQuery(ext.TIME_ELAPSED_EXT, q); }
    };
    const glc0 = Object.assign({}, window.__glc || {});
    const mem = () => ({ heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1 });
    const wait = (s) => new Promise((res) => setTimeout(res, s * 1000));
    await wait(SETTLE);
    const m0 = mem(), g0 = __game.render(false);
    const lt = []; let ob = null; try { ob = new PerformanceObserver((l) => { for (const e of l.getEntries()) lt.push(e.duration); }); ob.observe({ type: 'longtask' }); } catch (e) { /* no longtask API */ }
    const d = [], longF = []; let last = 0, run = true; tStart = performance.now();
    // Profile clock mark: a named 20 ms spin at a known performance.now(), found again in the CPU profile to line the two clocks up.
    const markT = performance.now(); (function __probeMark() { const e = performance.now() + 20; while (performance.now() < e) { /* spin */ } })();
    await new Promise((res) => { const f = (t) => { gpuTick(t); if (last) { d.push(t - last); if (t - last > 100) longF.push([last, t]); } last = t; if (run) requestAnimationFrame(f); else res(); }; requestAnimationFrame(f); setTimeout(() => { run = false; }, TIMED * 1000); });
    const wGaps = await new Promise((res) => { wk.onmessage = (e) => res(e.data); wk.postMessage(0); setTimeout(() => res([]), 2000); }); wk.terminate();
    const TO = performance.timeOrigin, tEnd = performance.now();
    clearInterval(id); clearInterval(stId); mo.disconnect(); if (ob) ob.disconnect(); if (lo) lo.disconnect(); if (q) { gl.endQuery(ext.TIME_ELAPSED_EXT); q = null; }
    // For each frame over 100 ms: the GL calls that can block from 200 ms before the frame to its end, the driver calls and the state samples around it.
    const G0 = window.__glog || [];
    const longs = longF.map(([a, b]) => ({ at_s: +((b - tStart) / 1000).toFixed(2), ms: Math.round(b - a),
      gl: G0.filter((e) => e[0] >= a - 200 && e[0] <= b && (e[1] > 0.5 || e[2] !== 'bufferData')).slice(-40).map((e) => Math.round(e[0] - a) + ' ' + e[2] + ' ' + e[1].toFixed(1) + 'ms #' + e[3]),
      drv: drvLog.filter((x) => x[0] >= a - 300 && x[0] <= b).map((x) => Math.round(x[0] - a) + ' ' + x[1] + 'ms'),
      dom: mut.filter((x) => x[0] >= a - 200 && x[0] <= b).slice(-12).map((x) => Math.round(x[0] - a) + ' ' + x[1]),
      st: stLog.filter((x) => x[0] >= a - 300 && x[0] <= b + 200).map((x) => Math.round(x[0] - a) + ' ' + x[1]),
      gpu: gpu.filter((x) => x[0] >= a && x[0] <= b + 40).map((x) => x[1].toFixed(1)),
      ea: +(TO + a).toFixed(1), eb: +(TO + b).toFixed(1), cjk: (window.__cjkLog || []).filter((x) => x[0] >= a - 300 && x[0] <= b).map((x) => Math.round(x[0] - a) + ' ' + x[1] + ' ' + x[2]),
      wGap: wGaps.filter((g) => g[1] > TO + a && g[0] < TO + b).map((g) => Math.round(Math.min(g[1], TO + b) - Math.max(g[0], TO + a))),
      loaf: loafT.filter((x) => x.t0 < b && x.t0 + x.ms > a).map((x) => ({ ms: x.ms, preRender: x.preRender, slp: x.styleLayoutPaint, scripts: x.scripts.slice(0, 4) })),
      stNear: stLog.filter((x) => x[0] >= a - 2000 && x[0] <= b + 500).map((x) => Math.round(x[0] - a) + ' ' + x[1]) }));
    const gs = gpu.map((x) => x[1]).sort((x, y) => x - y), gq = (k) => gs.length ? +gs[Math.min(gs.length - 1, Math.floor(gs.length * k))].toFixed(2) : -1;
    const glc1 = window.__glc || {}, glDelta = Object.keys(glc1).map((k) => k + ' ' + ((glc1[k] || 0) - (glc0[k] || 0))).join(', ');
    const evts = stLog.filter((x) => x[0] >= tStart).map((x) => +((x[0] - tStart) / 1000).toFixed(2) + 's ' + x[1]);
    const CJL = window.__cjkLog || [];
    window.__diag = { cjkFirst: CJL.length ? +((CJL[0][0] - tStart) / 1000).toFixed(2) + 's ' + CJL[0][1] + ' ' + CJL[0][2] : 'none', cjkN: CJL.length, fontWarm: (() => { const e = document.getElementById('fontWarm'); return e ? e.textContent.length + ' chars ' + e.dataset.ms + ' ms at load' : 0; })(), e0: +(TO + tStart).toFixed(1), e1: +(TO + tEnd).toFixed(1), wGapN: wGaps.filter((g) => g[0] > TO + tStart).length, wGap50: wGaps.filter((g) => g[0] > TO + tStart && g[1] - g[0] > 50).length, evts: evts.slice(0, 40), loafN, loafN100, domWrites: mut.filter((x) => x[0] >= tStart).length, markT, tStart, longRaw: longF, disj: disj.slice(0, 40), disjN: disj.length, caps, gpuN: gs.length, gpuP50: gq(0.5), gpuP95: gq(0.95), gpuMax: gq(1), longs, loaf: loaf.slice(0, 12), glDelta, drvSlow: drvLog.length };
    // Batch 17c (INT): the game's own per-part times (?perf=1 ring) over the timed window, and for every frame over 100 ms the frames of the
    // 200 ms before it with their parts (logic, fx+sound, view+characters, render submit) and the fx events dispatched in each.
    let parts = null, longParts = [];
    try {
      const rows = __game.perfRing ? __game.perfRing(tStart) : [];
      if (rows.length) {
        const av = (k) => +(rows.reduce((a, r) => a + r[k], 0) / rows.length).toFixed(3), mx = (k) => +Math.max(...rows.map((r) => r[k])).toFixed(1);
        const gq = gpu.map((x) => x[1]); const gav = gq.length ? +(gq.reduce((a, b) => a + b, 0) / gq.length).toFixed(3) : -1;
        parts = { n: rows.length, logic: av(2), fxsnd: av(3), view: av(4), render: av(5), gpu: gav, logicMax: mx(2), fxsndMax: mx(3), viewMax: mx(4), renderMax: mx(5), gpuMax: gq.length ? +Math.max(...gq).toFixed(1) : -1, events: rows[rows.length - 1][6] - rows[0][6], liveMax: mx(7) };
        for (const [a, b] of longF) {
          const pre = rows.filter((r) => r[0] >= a - 200 && r[0] <= b + 5).map((r) => Math.round(r[0] - a) + 'ms f' + r[1].toFixed(0) + ' L' + r[2].toFixed(1) + ' F' + r[3].toFixed(1) + ' V' + r[4].toFixed(1) + ' R' + r[5].toFixed(1) + ' ev' + r[6] + ' live' + r[7]);
          longParts.push({ at_s: +((b - tStart) / 1000).toFixed(2), ms: Math.round(b - a), pre, gpu: gpu.filter((x) => x[0] >= a - 200 && x[0] <= b + 40).map((x) => x[1].toFixed(1)) });
        }
      }
    } catch (e) { parts = { err: String(e) }; }
    window.__parts = { parts, longParts };
    const m1 = mem(), info = __game.render(false);
    d.sort((a, b) => a - b);
    const sum = d.reduce((a, b) => a + b, 0), n = d.length;
    const extra = {};
    try { extra.bots = __game.bots().list.filter((q) => !q.dead).length; extra.cubs = __game.cubs().list.filter((u) => u.alive).length; } catch (e) { /* not in a match */ }
    try { const h = __game.hunt(); if (h.phase === 'hunt') extra.hunt = h.phase + ' alive ' + h.units.filter((u) => u.alive).length + ' hits ' + h.hits; } catch (e) { /* no hunt */ }
    return { frames: n, fps: +(n / (sum / 1000)).toFixed(1), p50: +d[Math.floor(n * 0.5)].toFixed(1), p95: +d[Math.floor(n * 0.95)].toFixed(1), worst: +d[n - 1].toFixed(1),
      over20: +(100 * d.filter((x) => x > 20).length / n).toFixed(1), over33: d.filter((x) => x > 33.4).length,
      calls: info.calls, tris: info.tris, programs: info.programs, geoms: info.geoms, texs: info.texs, heap0: m0.heap, heap1: m1.heap, longN: lt.length, longMax: Math.round(Math.max(0, ...lt)), longSum: Math.round(lt.reduce((a, b) => a + b, 0)), geo0: g0.geoms, tex0: g0.texs, drvErr: window.__drvErr || '', info: window.__info || '', info2: window.__info2 || '', diag: window.__diag, ...extra };
  }, { drv, SETTLE, TIMED: sc.timed || TIMED });
  const { profile } = await cdp.send('Profiler.stop'); await cdp.detach();
  { const pp = await page.evaluate(() => window.__parts || null); if (pp) { console.log('PARTS ' + name + ' ' + JSON.stringify(pp.parts)); for (const L of pp.longParts) console.log('LONGPARTS ' + name + ' ' + JSON.stringify(L)); r.parts = pp.parts; } }
  const diag = r.diag; delete r.diag;
  rows.push({ scene: name, loadMs, setupMs, errs: errs.length, err0: errs[0] || '', ...r });
  if (diag) {
    const inWin = nodeGaps.filter((g) => g[0] >= diag.e0 && g[0] <= diag.e1);
    diag.nodeGapN = inWin.length; diag.nodeGap50 = inWin.filter((g) => g[1] - g[0] > 50).length; diag.nodeGapMax = Math.round(Math.max(0, ...inWin.map((g) => g[1] - g[0])));
    for (const L of diag.longs) L.nGap = nodeGaps.filter((g) => g[1] > L.ea && g[0] < L.eb).map((g) => Math.round(Math.min(g[1], L.eb) - Math.max(g[0], L.ea)));
    const pf = perFrame(profile, diag.markT, diag.longRaw);
    diag.longs.forEach((L, i) => { L.prof = pf[i]; });
    // One line per long frame: when it was, how long, and the share of it that each detector saw stalled.
    for (const L of diag.longs) console.log('LONG ' + name + ' at ' + L.at_s + 's ' + L.ms + 'ms nodeStall ' + (L.nGap.reduce((x, y) => x + y, 0)) + 'ms workerStall ' + (L.wGap.reduce((x, y) => x + y, 0)) + 'ms profSamples ' + (L.prof && L.prof.samples) + ' profGapMax ' + (L.prof && L.prof.profGapMax) + 'ms cjk ' + JSON.stringify(L.cjk) + ' gl ' + L.gl.length + ' dom ' + L.dom.length + ' gpu ' + L.gpu.join('/') + ' loaf ' + JSON.stringify(L.loaf) + ' top ' + JSON.stringify(L.prof && L.prof.top) + ' st ' + JSON.stringify(L.stNear.slice(-4)));
    console.log('STALLS ' + name + ' timed ' + ((diag.e1 - diag.e0) / 1000).toFixed(0) + 's: node gaps >30ms ' + diag.nodeGapN + ' (>50ms ' + diag.nodeGap50 + ', max ' + diag.nodeGapMax + 'ms), worker gaps >30ms ' + diag.wGapN + ' (>50ms ' + diag.wGap50 + '), frames >100ms ' + diag.longs.length + ', first CJK text ' + diag.cjkFirst + ' (' + diag.cjkN + '), fontWarm chars ' + diag.fontWarm);
  }
  console.log('DIAG ' + name + ' ' + JSON.stringify(diag));
    console.log('ROW ' + JSON.stringify(rows[rows.length - 1]));
  await page.close();
}
console.log('RENDERER ' + gpu + (/swiftshader|llvmpipe|software/i.test(gpu) ? '  (NOT a real GPU)' : ''));
console.log('scene       fps    p50   p95   worst  >20ms%  >33ms  calls  tris    prog geo  heap MB  geo/tex start-end  live');
for (const r of rows) console.log([r.scene.padEnd(10), String(r.fps).padStart(6), String(r.p50).padStart(5), String(r.p95).padStart(5), String(r.worst).padStart(6), String(r.over20).padStart(6), String(r.over33).padStart(6),
  String(r.calls).padStart(6), String(r.tris).padStart(7), String(r.programs).padStart(4), String(r.geoms).padStart(4), (r.heap0 + '-' + r.heap1).padStart(9), (r.geo0 + '-' + r.geoms + '/' + r.tex0 + '-' + r.texs).padStart(13), ' ' + (r.bots !== undefined ? 'bots ' + r.bots + ' cubs ' + r.cubs : '') + (r.hunt || '') + ' long ' + r.longN + '/' + r.longMax + 'ms/' + r.longSum + 'ms' + (r.errs ? ' ERR ' + r.err0 : '') + (r.drvErr ? ' DRV ' + r.drvErr.slice(0, 80) : '')].join(' '));
console.log('NODEGAPS total ' + nodeGaps.length + ' over 50ms ' + nodeGaps.filter((g) => g[1] - g[0] > 50).length + ' max ' + Math.round(Math.max(0, ...nodeGaps.map((g) => g[1] - g[0]))) + 'ms');
stallProc.kill(); await browser.close(); server.close();
