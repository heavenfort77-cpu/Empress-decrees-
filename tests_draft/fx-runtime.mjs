// Runtime checks for fxEvent, sound.js and the options menu in headless Chromium (PREP-AV draft for INT; Linux runner, software GPU:
// correctness and counts only, never fps). Serves the repo, opens probe/prepav/index.html?mode=test. Usage: node tests_draft/fx-runtime.mjs [ids]
// Prints one line per check (PASS / FAIL with the failing detail) and a summary; exit 1 on any FAIL. Checks wait on conditions with caps, not the clock.
import { createServer } from 'node:http';
import { readFile } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json' };
const server = createServer(async (req, res) => {
  const u = decodeURIComponent(req.url.split('?')[0]), p = normalize(join(ROOT, u));
  if (!p.startsWith(ROOT)) { res.writeHead(403); res.end(); return; }
  try { const b = await readFile(p); res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(b); } catch { res.writeHead(404); res.end(); }
}).listen(0);
const URL0 = `http://127.0.0.1:${server.address().port}/probe/prepav/index.html?mode=test`;
const ONLY = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const results = [];
const rec = (id, ok, detail) => { results.push([id, ok]); console.log(`${ok ? 'PASS' : 'FAIL'} ${id}${ok ? '' : ' ' + detail}`); };

async function open(qs, ctxOpts, init) {
  const ctx = await browser.newContext(ctxOpts || { viewport: { width: 1280, height: 720 } });
  if (init) await ctx.addInitScript(init);
  const page = await ctx.newPage(), errs = [];
  page.on('pageerror', (e) => errs.push(e.message)); page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
  await page.goto(URL0 + (qs || '')); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  return { ctx, page, errs };
}
const ev = (page, f, a) => page.evaluate(f, a);
const until = (page, f, a, ms) => page.waitForFunction(f, a, { timeout: ms || 60000, polling: 50 }).then(() => true, () => false);
async function unlockAndRender(page) {
  await page.mouse.click(640, 360);
  const run = await until(page, () => window.__t.SND.status().ctx === 'running', null, 15000);
  const rendered = await until(page, () => { const s = window.__t.SND.status(); return s.total > 0 && s.ready === s.total; }, null, 180000);
  return { run, rendered };
}
const want = (id) => !ONLY.length || ONLY.includes(id);

// ---- main page: unlock, render, events, pause, visibility, dt clamp, warm-up, menu ----
{
  const { ctx, page, errs } = await open('', null, () => { const AC = window.AudioContext; window.AudioContext = class extends AC { constructor(o) { super(o); this.suspend(); } }; });
  // T1 unlock: no context before a gesture; the first click creates it and resumes it. Every new context starts suspended here (init script:
  // the iOS / autoplay-held case), so only unlock()'s resume can make it run.
  const before = await ev(page, () => window.__t.SND.status().ctx);
  const u = await unlockAndRender(page);
  if (want('T1')) rec('T1 unlock', before === 'none' && u.run, `before=${before} running=${u.run}`);
  if (want('T2')) rec('T2 every sound and loop renders', u.rendered, JSON.stringify(await ev(page, () => window.__t.SND.status())));
  // T3 one event: a sound starts and a card is drawn (handle >= 0, live up), position-culled sound beyond range is skipped.
  const t3 = await ev(page, () => {
    const { FX, SND } = window.__t, p0 = SND.status().played, l0 = FX.fxStatus().live;
    const h = FX.fxEvent('claw:tell', 0, -3, 'apex', FX.fxO(0, 1, 0, 0, 0.45));
    const p1 = SND.status().played, l1 = FX.fxStatus().live;
    const far = FX.fxEvent('claw:rel', 500, 500, 'apex', FX.fxO(0, 1)); const p2 = SND.status().played;
    return { h, p0, p1, l0, l1, far, p2 };
  });
  if (want('T3')) rec('T3 event plays sound and card', t3.h >= 0 && t3.p1 === t3.p0 + 1 && t3.l1 > t3.l0 && t3.p2 === t3.p1, JSON.stringify(t3));
  // T4 pause: the context suspends, the card clock holds, events are refused; resume undoes all three.
  await ev(page, () => window.__t.setPaused(true));
  const susp = await until(page, () => window.__t.SND.status().ctx === 'suspended', null, 5000);
  const tA = await ev(page, () => window.__t.FX.fxStatus().t); await page.waitForTimeout(400);
  const t4 = await ev(page, () => { const { FX } = window.__t; return { t: FX.fxStatus().t, h: FX.fxEvent('claw:tell', 0, -3, 'apex', FX.fxO()) }; });
  await ev(page, () => window.__t.setPaused(false));
  const res = await until(page, () => window.__t.SND.status().ctx === 'running', null, 5000);
  await page.waitForTimeout(300);
  const tB = await ev(page, () => window.__t.FX.fxStatus().t);
  if (want('T4')) rec('T4 pause holds cards and sound', susp && t4.t === tA && t4.h === -1 && res && tB > tA, JSON.stringify({ susp, tA, t4, res, tB }));
  // T5 hidden tab: suspended and silent while hidden, running again when shown.
  const t5 = await ev(page, () => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); return true; });
  const hid = await until(page, () => window.__t.SND.status().ctx === 'suspended', null, 5000);
  const silent = await ev(page, () => window.__t.SND.play('ui_ok'));
  await ev(page, () => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => false }); document.dispatchEvent(new Event('visibilitychange')); });
  const back = await until(page, () => window.__t.SND.status().ctx === 'running', null, 5000);
  if (want('T5')) rec('T5 hidden tab suspends audio', t5 && hid && silent === false && back, JSON.stringify({ hid, silent, back }));
  // T6 dt clamp: one huge frame step advances the card clock by at most dtMax.
  const t6 = await ev(page, () => { const { FX } = window.__t; window.__t.setPaused(true); FX.fxPause(false); const a = FX.fxStatus().t; FX.fxStep(10, false); const b = FX.fxStatus().t; window.__t.setPaused(false); return { d: b - a, max: FX.FX_CONFIG.dtMax }; });
  if (want('T6')) rec('T6 dt clamped', t6.d > 0 && t6.d <= 0.05 + 1e-9, JSON.stringify(t6));
  // T7 every event of the table fires (no unknown names, no page error) and no shader program is built after the warm-up.
  const t7 = await ev(page, async () => {
    const { FX } = window.__t, names = Object.keys(FX.fxTable()), p0 = window.__t.progs();
    let i = 0; for (const n of names) { FX.fxEvent(n, (i % 9) - 4, -(i % 5), 'ru', FX.fxO(1, 0, 0, 0, 0.5)); i++; }
    const liveFired = FX.fxStatus().live;
    for (let k = 0; k < 20; k++) { window.__t.renderOnce(); await new Promise((r) => requestAnimationFrame(r)); }
    return { n: names.length, unknown: FX.fxStatus().unknown, newProg: window.__t.progs() - p0, progsAfterWarm: window.__t.progs0, warmed: window.__t.warmed, warmCalls: FX.fxStatus().warmCalls, liveFired };
  });
  if (want('T7')) rec('T7 all events fire, warm-up complete', t7.n > 200 && t7.unknown === 0 && t7.newProg === 0 && t7.warmed === 13 && t7.warmCalls >= 3 && t7.liveFired >= 100, JSON.stringify(t7));
  // T16 the buffers the game plays are the rendered samples, unchanged (waveform comparison: max |difference| <= 1e-6).
  if (want('T16')) {
    const t16 = await ev(page, async () => {
      const { SND } = window.__t, st = SND.status(), out = [];
      for (const n of ['claw:tell', 'ru_hit', 'g_volley_tell', 'st_burn', 'ui_ok', 'demon_roar']) {
        const name = n.split(':')[0] === 'claw' ? 'demon_claw_tell' : n, b = SND.bufferOf(name);
        if (!b) { out.push([name, 'missing']); continue; }
        const x = await SND.renderSound(name, st.sr, st.profile), y = b.getChannelData(0);
        let d = x.length === y.length ? 0 : 1; for (let i = 0; i < Math.min(x.length, y.length); i++) d = Math.max(d, Math.abs(x[i] - y[i]));
        out.push([name, d]);
      }
      return out;
    });
    // Two offline renders of one sound differ by float rounding only (seen: <= 2.4e-7); 1e-6 = -120 dBFS. A gain or copy change is >> that.
    rec('T16 played buffers equal the renders', t16.length === 6 && t16.every((r) => typeof r[1] === 'number' && r[1] <= 1e-6), JSON.stringify(t16));
  }
  // T8 intensity mapping: each condition gives its level; the fall waits holdS of game steps; sound.js gets the value.
  const t8 = await ev(page, () => {
    const { IN, levelOf, stepIntensity, resetIntensity, INT_CONFIG: C, SND } = window.__t, out = [];
    resetIntensity(); out.push(levelOf(IN));
    IN.rivalsNear = 1; out.push(levelOf(IN)); IN.sinceFight = 1; out.push(levelOf(IN)); IN.hpFrac = 0.3; out.push(levelOf(IN)); IN.apex = 1; out.push(levelOf(IN));
    stepIntensity(0.016, SND); const top = SND.status().intensity;
    resetIntensity(); IN.sinceFight = 1; stepIntensity(0.016, SND); IN.sinceFight = 99;
    let n = 0; while (stepIntensity(0.05, SND) === C.fight && n < 1000) n++;
    resetIntensity(); stepIntensity(0.016, SND);
    return { out, top, holdSteps: n, holdS: C.holdS };
  });
  if (want('T8')) rec('T8 intensity levels and hold', JSON.stringify(t8.out) === '[0.1,0.3,0.5,0.7,1]' && t8.top === 1 && Math.abs(t8.holdSteps * 0.05 - t8.holdS) < 0.11, JSON.stringify(t8));
  // T9 menu: Esc opens (pauses), arrow keys move the master slider, the change is saved; mute blocks every sound; Esc closes (resumes).
  await page.keyboard.press('Escape');
  const opened = await ev(page, () => window.__t.G.menu.isOpen() && window.__t.G.paused);
  const m0 = await ev(page, () => window.__t.SND.status().vol.master);
  for (let i = 0; i < 10; i++) await page.keyboard.press('ArrowLeft');
  await ev(page, () => document.activeElement.dispatchEvent(new Event('change')));
  const m1 = await ev(page, () => ({ vol: window.__t.SND.status().vol.master, saved: JSON.parse(localStorage.getItem('empressDecrees.audio') || '{}') }));
  await page.click('.opts__btn--mute');
  await page.keyboard.press('Escape');
  const t9 = await ev(page, () => ({ open: window.__t.G.menu.isOpen(), paused: window.__t.G.paused, mute: window.__t.SND.status().mute, play: window.__t.SND.play('ui_ok') }));
  if (want('T9')) rec('T9 options: Esc, slider, save, mute', opened && m1.vol < m0 && Math.abs((m1.saved.vol || {}).master - m1.vol) < 1e-9 && !t9.open && !t9.paused && t9.mute && t9.play === false && typeof m1.saved.mute === 'boolean', JSON.stringify({ opened, m0, m1, t9 }));
  if (want('T10') || want('T11')) {
    // T10 reload: the saved master volume and mute come back into the menu.
    await page.reload(); await page.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    await page.keyboard.press('Escape');
    const t10 = await ev(page, () => ({ slider: +document.querySelector('.opts__range').value, out: document.querySelector('.opts__val').textContent, mute: window.__t.SND.status().mute, label: document.querySelector('.opts__btn--mute').textContent }));
    if (want('T10')) rec('T10 settings survive a reload', t10.slider === Math.round(m1.vol * 100) && t10.mute === true && t10.label === 'Sound on' && t10.out === t10.slider + '%', JSON.stringify({ t10, want: Math.round(m1.vol * 100) }));
  }
  if (want('T12')) rec('T12 no page errors (main page)', errs.length === 0, errs.slice(0, 4).join(' | '));
  await ctx.close();
}
// ---- storage blocked: the menu and sound still work, nothing throws ----
if (want('T13')) {
  const { ctx, page, errs } = await open('', null, () => { Storage.prototype.setItem = () => { throw new Error('blocked'); }; Storage.prototype.getItem = () => { throw new Error('blocked'); }; });
  await page.mouse.click(640, 360);
  await page.keyboard.press('Escape');
  for (let i = 0; i < 5; i++) await page.keyboard.press('ArrowLeft');
  await ev(page, () => document.activeElement.dispatchEvent(new Event('change')));
  await page.click('.opts__btn--mute'); await page.click('.opts__btn--mute');
  const v = await ev(page, () => window.__t.SND.status().vol.master);
  rec('T13 storage blocked', errs.length === 0 && v < 1, JSON.stringify({ errs: errs.slice(0, 3), v }));
  await ctx.close();
}
// ---- phone: every menu control is a 44 px target; low tier halves pools and skips smoke states and endless heal loops ----
if (want('T14') || want('T15')) {
  const { ctx, page, errs } = await open('&touch=1&tier=low&profile=phone', { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const btnShown = await ev(page, () => getComputedStyle(document.getElementById('btnOpts')).display !== 'none');
  await page.tap('#btnOpts');
  const sizes = await ev(page, () => [...document.querySelectorAll('.opts__range, .opts__btn, .opts-open')].map((e) => { const r = e.getBoundingClientRect(); return [e.className, Math.round(r.width), Math.round(r.height)]; }));
  const small = sizes.filter(([, w, h]) => w < 44 || h < 44);
  if (want('T14')) rec('T14 44 px targets on phone', btnShown && sizes.length >= 7 && small.length === 0 && errs.length === 0, JSON.stringify({ btnShown, small, n: sizes.length, errs: errs.slice(0, 2) }));
  const t15 = await ev(page, () => { const { FX } = window.__t; window.__t.setPaused(false); const s = FX.fxEvent('g_charge:state', 0, 0, '', FX.fxO()); const hl = FX.fxEvent('ding:state', 0, 0, '', FX.fxO()); const c = FX.fxEvent('claw:tell', 0, 0, 'apex', FX.fxO(0, 1, 0, 0, 0.45)); return { s, hl, c, pools: FX.fxMeshes().map((m) => m.geometry.instanceCount) }; });
  if (want('T15')) rec('T15 low tier', t15.s === -1 && t15.hl === -1 && t15.c >= 0 && JSON.stringify(t15.pools) === '[32,24,24]', JSON.stringify(t15));
  await ctx.close();
}
await browser.close(); server.close();
const nf = results.filter((r) => !r[1]).length + (results.length ? 0 : 1);
if (!results.length) console.log('FAIL no checks ran (passed on nothing)');
console.log(`FX-RUNTIME ${nf ? 'FAIL' : 'PASS'} ${results.length - (nf && results.length ? nf : 0)} of ${results.length}`);
process.exit(nf ? 1 : 0);
