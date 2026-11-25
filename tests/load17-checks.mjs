// Batch 17b checks (1701-1710): the loading cards, the palace set (KTX2 from assets/c with PNG fallback), dispose on Royal Rumble, the restore and
// adjust cards, the hidden-tab card clock, old saves, the encode manifest and the KTX2 look against the PNG route (docs/INTEGRATION.md 3, 5, 10).
// Called from tests/run.mjs with g (evaluate after the loader is idle), check, the page, the browser and the test URL. Every wait is on a condition
// with a large cap, never on the clock alone.
import { readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';

const idle = (page) => page.waitForFunction(() => !__game.loadBusy(), null, { timeout: 120000 });
// A palace run through the player's own path: the mode menu pick, then the school pick (which starts the run; a set it needs starts its card).
const toPalace = () => { const G = __game; G.setSeed(12345); G.pickMode('palace'); G.pickSchool(0); };
const toRumble = () => { const G = __game; G.setSeed(12345); G.pickMode('rumble'); G.pickSchool(0); };
const memNow = () => { const r = __game.render(true), l = __game.load(); return { geoms: r.geoms, texs: r.texs, programs: r.programs, palace: l.palace, ptex: l.ptex }; };

export async function load17Checks(g, check, page, browser, URL0) {
  const errs0 = [];
  page.on('pageerror', (e) => errs0.push(String(e).slice(0, 200)));
  const C = await g(() => ({ fmt: __game.config.LOAD.fmt, files: __game.config.TEX.files, cap: __game.config.LOAD.capS, mode: __game.config.PALACE.saveKey, school: __game.config.SELECT.saveKey }));

  // 1701 The palace set: picking the palace loads the five images from assets/c (KTX2, desktop set 1024 px, top-first rows, v flipped by the texture transform), all or
  // none; the card ran its warm draw (draws > 0 under it) and ended within the cap; five textures more on the GPU; the card was shown while it ran.
  await g(toRumble);
  await g(() => { __game.pickMode('palace'); __game.pickSchool(0); });
  const shown = await page.waitForFunction(() => __game.load().shown || !__game.loadBusy(), null, { timeout: 120000 }).then(() => page.evaluate(() => __game.load().shown || __game.load().led.kind));
  await idle(page);
  const l1 = await g(() => __game.load());
  check('1701 palace set: 5 images from assets/c as KTX2 (flipped v), all on, warm draw under the card, within the cap, +5 textures',
    l1.palace === 'ready' && l1.led.kind === 'palace' && l1.led.failed.length === 0 && l1.led.fmt.length === 5 && l1.led.fmt.every((f) => f.endsWith(':ktx2'))
    && l1.maps.every((m) => m.map && m.compressed && m.flipV === -1 && m.w === 1024) && l1.led.n === 1 && l1.led.draws > 0 && !l1.led.capped && l1.led.ms <= C.cap * 1000
    && l1.led.tex1 - l1.led.tex0 === 5 && l1.ptex === 5 && (shown === true || shown === 'palace'), JSON.stringify({ shown, led: l1.led, maps: l1.maps, palace: l1.palace }));

  // 1702 No shader program and no texture built in play after the card: 600 steps of a palace run (walking the start hall, the HUD and pieces
  // live), drawn every 20 steps, against the counts the card left.
  const p2 = await g(() => {
    const memNow = () => { const r = __game.render(true); return { geoms: r.geoms, texs: r.texs, programs: r.programs }; };
    const G = __game, o = { at0: memNow(), worst: null };
    const r = G.palace().cur, st = G.state();
    for (let i = 0; i < 30; i++) { G.setMove(Math.sin(i) * 0.7, Math.cos(i * 0.7) * 0.7); G.step(20); const m = memNow(); if (m.programs !== o.at0.programs || m.texs !== o.at0.texs) o.worst = m; }
    G.clearMove(); o.at1 = memNow(); o.room = r; o.t = st.t; return o;
  });
  check('1702 no program or texture built in palace play after the card (600 steps drawn every 20)', p2.worst === null && p2.at1.programs === p2.at0.programs && p2.at1.texs === p2.at0.texs,
    JSON.stringify(p2));

  // 1703 Memory flat over mode switches: 5 cycles of Royal Rumble then the palace (each with 2 new runs); in Royal Rumble the palace images are gone
  // (textures down by 5, maps off); cycle 1 and cycle 5 counts equal on both sides.
  const cyc = [];
  for (let c = 0; c < 5; c++) {
    await g(toRumble); const r = await g(memNow);
    await g(toPalace); await idle(page); await g(() => { __game.newRun(); }); await idle(page); await g(() => { __game.pickSchool(0); }); await idle(page);
    const p = await g(memNow); cyc.push({ r, p });
  }
  const eq = (a, b) => a.geoms === b.geoms && a.texs === b.texs && a.programs === b.programs;
  check('1703 memory flat over 5 Rumble/palace cycles (geometries, textures, programs); Rumble holds no palace image',
    eq(cyc[0].r, cyc[4].r) && eq(cyc[0].p, cyc[4].p) && cyc.every((x) => x.r.palace === 'none' && x.r.ptex === 0 && x.p.palace === 'ready' && x.p.texs - x.r.texs === 5),
    JSON.stringify(cyc));

  // 1704 A missing file (in its own page, so the blocked requests' console lines stay out of the main page's log): door.ktx2 blocked = the door
  // falls back to its PNG source (the rest stay KTX2); door.ktx2 and door.png both blocked = the whole set keeps its box colours (never half
  // textured), the ledger names the file; unblocked again = the set loads; no page error.
  const f4 = {};
  {
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } }), pg = await ctx.newPage(), e = [];
    // Expected here, and only here: the browser's console line for each deliberately blocked request, by exact text. Any other console error
    // or page error in this page fails the check (check 17 still counts every error of the main page).
    const BLOCKED = 'Failed to load resource: net::ERR_FAILED';
    f4.blocked = 0;
    pg.on('pageerror', (x) => e.push(String(x).slice(0, 160)));
    pg.on('console', (m) => { if (m.type() !== 'error') return; if (m.text() === BLOCKED) f4.blocked++; else e.push(m.text().slice(0, 160)); });
    await pg.goto(URL0); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    await pg.route('**/assets/c/desk/door.ktx2', (r) => r.abort());
    await pg.evaluate(toPalace); await idle(pg); f4.f1 = await pg.evaluate(() => __game.load());
    await pg.route('**/assets/tex/door.png', (r) => r.abort());
    await pg.evaluate(toRumble); await pg.evaluate(toPalace); await idle(pg); f4.f2 = await pg.evaluate(() => __game.load());
    await pg.unroute('**/assets/c/desk/door.ktx2'); await pg.unroute('**/assets/tex/door.png');
    await pg.evaluate(toRumble); await pg.evaluate(toPalace); await idle(pg); f4.f3 = await pg.evaluate(() => __game.load());
    f4.errs = e; await ctx.close();
  }
  const { f1, f2, f3 } = f4;
  check('1704 fallback: blocked KTX2 -> its PNG; KTX2 and PNG blocked -> the whole set on box colours, ledger names it; recovers after; no page error',
    f1.palace === 'ready' && f1.led.fmt.includes('door:png') && f1.led.fmt.filter((x) => x.endsWith(':ktx2')).length === 4
    && f2.palace === 'failed' && f2.led.failed.join() === 'door' && f2.maps.every((m) => !m.map) && f2.ptex === 0
    && f3.palace === 'ready' && f3.maps.every((m) => m.map) && f4.errs.length === 0 && f4.blocked > 0,
    JSON.stringify({ f1: [f1.palace, f1.led.fmt], f2: [f2.palace, f2.led.failed, f2.maps.map((m) => m.map)], f3: f3.palace, errs: f4.errs, blocked: f4.blocked }));

  // 1711 The page's load event fires before the boot's warm-up (a top-level yield): load event start < the boot's end mark, in a fresh page.
  {
    const ctx = await browser.newContext({ viewport: { width: 2560, height: 1080 } }), pg = await ctx.newPage();
    await pg.goto(URL0, { timeout: 120000 }); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    const t = await pg.evaluate(() => ({ load: performance.getEntriesByType('navigation')[0].loadEventStart, ready: window.__readyMs }));
    check('1711 page load event before the boot warm-up (2560x1080): loadEventStart < boot end', t.load > 0 && t.load < t.ready, JSON.stringify(t));
    await ctx.close();
  }

  // 1705 Graphics context lost and restored in palace play: the 'restore' card runs (upload, compile, one draw), then frames draw again with the
  // same texture count and no page error.
  const errC = errs0.length;
  const t0 = await g(() => __game.render(true).texs);
  await page.evaluate(() => { window.__lc = __game.loseContext(); });
  await page.waitForFunction(() => __game.state().ctxLost === true, null, { timeout: 30000 });
  await page.evaluate(() => { window.__lc.restoreContext(); });
  await page.waitForFunction(() => __game.state().ctxLost === false, null, { timeout: 60000 });
  await idle(page);
  const c5 = await g(() => { const l = __game.load(); const f0 = __game.state().frames; return { led: l.led, f0 }; });
  await page.waitForFunction((f0) => __game.state().frames > f0 + 5, c5.f0, { timeout: 60000 });
  const c5b = await g(() => __game.render(true));
  check('1705 context lost and restored in the palace: restore card ran (one draw under it), frames draw again, textures equal, no page error',
    c5.led.kind === 'restore' && c5.led.n === 1 && c5.led.draws > 0 && c5b.calls > 0 && c5b.texs === t0 && errs0.length === errC,
    JSON.stringify({ led: c5.led, calls: c5b.calls, texs: [t0, c5b.texs], errs: errs0.slice(errC) }));

  // 1706 Tier changed in play: the 'adjust' card compiles and draws once; switching low -> medium -> low -> medium ends with the programs it had.
  const a6 = [];
  for (const t of ['low', 'medium', 'low', 'medium']) { await g((t) => __game.tierInPlay(t), t); await idle(page); a6.push(await g(() => { const l = __game.load(); return { kind: l.led.kind, n: l.led.n, draws: l.led.draws, programs: __game.render(true).programs }; })); }
  await g(() => __game.tierInPlay('medium')); await idle(page);
  check('1706 tier changed in play: adjust card each time (one draw under it), programs back to the same count on the same tier',
    a6.every((x) => x.kind === 'adjust' && x.n === 1 && x.draws > 0) && a6[1].programs === a6[3].programs && a6[0].programs === a6[2].programs, JSON.stringify(a6));

  // 1707 Tab hidden while the palace set loads: the card's clock stops (visible time frozen, the card still busy), and the set finishes once the
  // tab shows again. Direct evaluates here (g waits for an idle loader).
  await g(toRumble);
  await page.evaluate(() => { __game.pickMode('palace'); __game.pickSchool(0); Object.defineProperty(document, 'hidden', { value: true, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); });
  const h0 = await page.evaluate(() => __game.load());
  await page.waitForTimeout(1500);
  const h1 = await page.evaluate(() => __game.load());
  await page.evaluate(() => { Object.defineProperty(document, 'hidden', { value: false, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); });
  await idle(page);
  const h2 = await page.evaluate(() => __game.load());
  check('1707 tab hidden mid-load: card clock frozen while hidden (still busy), the set finishes after the tab shows',
    h0.phase === 'busy' && h1.phase === 'busy' && h1.visS === h0.visS && h2.phase === 'idle' && h2.palace === 'ready', JSON.stringify({ h0: [h0.phase, h0.visS], h1: [h1.phase, h1.visS], h2: [h2.phase, h2.palace] }));

  // 1708 Saves from before batch 17 (mode, school, the audio key) and garbage in the same keys: the page loads with no error and runs a palace set.
  const saves = [{ [C.mode]: 'rumble', [C.school]: '3', 'empressDecrees.audio': '{"mode":"fx","reduce":true,"vol":{"music":0.5}}' },
    { [C.mode]: 'zzz', [C.school]: '{bad', 'empressDecrees.audio': '{bad json' }];
  const s8 = [];
  for (const sv of saves) {
    const ctx = await browser.newContext({ viewport: { width: 1366, height: 768 } }); const pg = await ctx.newPage(); const e = [];
    pg.on('pageerror', (x) => e.push(String(x).slice(0, 160)));
    await pg.addInitScript((sv) => { for (const k in sv) localStorage.setItem(k, sv[k]); }, sv);
    await pg.goto(URL0); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
    await pg.evaluate(toPalace); await idle(pg);
    s8.push({ errs: e, palace: await pg.evaluate(() => __game.load().palace) }); await ctx.close();
  }
  check('1708 old saves and garbage saves: page loads with no error, the palace set loads', s8.every((x) => x.errs.length === 0 && x.palace === 'ready'), JSON.stringify(s8));

  // 1709 The encode manifest is fresh: every file in assets/c/manifest.json exists with its hash, its source has the hash it was encoded from, and
  // every palace image has a desktop and a phone file.
  const ROOT = new URL('..', import.meta.url).pathname, man = JSON.parse(await readFile(ROOT + 'assets/c/manifest.json', 'utf8')), bad9 = [];
  const sha = async (p) => createHash('sha256').update(await readFile(ROOT + p)).digest('hex');
  for (const [f, v] of Object.entries(man.files)) {
    try { if ((await sha(f)) !== v.sha256) bad9.push('file ' + f); if ((await sha(v.source)) !== v.source_sha256) bad9.push('stale ' + f); } catch (e) { bad9.push('missing ' + f); }
  }
  for (const n of Object.values(C.files)) for (const set of ['desk', 'phone']) if (!man.files[`assets/c/${set}/${n}.ktx2`] && !man.files[`assets/c/${set}/${n}.png`]) bad9.push('no ' + set + ' ' + n);
  check('1709 encode manifest fresh (file and source hashes), desktop and phone file for every palace image', bad9.length === 0 && Object.keys(man.files).length > 0,
    `${Object.keys(man.files).length} files; ${bad9.slice(0, 6).join(' | ')}`);

  // 1710 The KTX2 look against the PNG route in the start hall (same seed, spot, camera, tier): mean dE2000 of the frame <= 2.
  // The run is stepped to the same game time, then the frame loop is held (tab marked hidden) so the shot is the one frame drawn here.
  const hide = (on) => { Object.defineProperty(document, 'hidden', { value: on, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); };
  const shot = async () => {
    await page.evaluate((hs) => { const hide = eval(hs); const G = __game, p = G.player(); G.teleport(p.x, p.z); G.step(120); hide(true); G.render(true); }, hide.toString());
    const b = (await page.screenshot({ type: 'png' })).toString('base64'); await page.evaluate((hs) => eval(hs)(false), hide.toString()); return b;
  };
  await g(toRumble); await g(toPalace); await idle(page); const A = await shot();
  await g(() => { __game.config.LOAD.fmt = 'png'; }); await g(toRumble); await g(toPalace); await idle(page); const pngFmt = await g(() => __game.load().led.fmt); const B = await shot();
  await g(() => { __game.config.LOAD.fmt = 'ktx2'; }); await g(toRumble); await g(toPalace); await idle(page);
  const de = await page.evaluate(async ([a, b]) => {
    const px = async (s) => { const im = new Image(); im.src = 'data:image/png;base64,' + s; await im.decode(); const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(im, 0, 0); return x.getImageData(0, 0, c.width, c.height).data; };
    const lab = (r, g, b) => { const f = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; }; const R = f(r), G = f(g), B = f(b);
      let X = (0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.95047, Y = 0.2126 * R + 0.7152 * G + 0.0722 * B, Z = (0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.08883;
      const h = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116); X = h(X); Y = h(Y); Z = h(Z); return [116 * Y - 16, 500 * (X - Y), 200 * (Y - Z)]; };
    const d2000 = (p, q) => { const [L1, a1, b1] = p, [L2, a2, b2] = q, rad = Math.PI / 180, C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cm = (C1 + C2) / 2, G = 0.5 * (1 - Math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)));
      const a1p = (1 + G) * a1, a2p = (1 + G) * a2, C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2), h1 = (Math.atan2(b1, a1p) / rad + 360) % 360, h2 = (Math.atan2(b2, a2p) / rad + 360) % 360;
      const dL = L2 - L1, dC = C2p - C1p; let dh = h2 - h1; if (C1p * C2p === 0) dh = 0; else if (dh > 180) dh -= 360; else if (dh < -180) dh += 360;
      const dH = 2 * Math.sqrt(C1p * C2p) * Math.sin(dh * rad / 2), Lm = (L1 + L2) / 2, Cmp = (C1p + C2p) / 2;
      let hm = h1 + h2; if (C1p * C2p !== 0) hm = Math.abs(h1 - h2) <= 180 ? hm / 2 : hm < 360 ? (hm + 360) / 2 : (hm - 360) / 2;
      const T = 1 - 0.17 * Math.cos((hm - 30) * rad) + 0.24 * Math.cos(2 * hm * rad) + 0.32 * Math.cos((3 * hm + 6) * rad) - 0.2 * Math.cos((4 * hm - 63) * rad);
      const SL = 1 + 0.015 * (Lm - 50) ** 2 / Math.sqrt(20 + (Lm - 50) ** 2), SC = 1 + 0.045 * Cmp, SH = 1 + 0.015 * Cmp * T, RT = -2 * Math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7)) * Math.sin(60 * Math.exp(-(((hm - 275) / 25) ** 2)) * rad);
      return Math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH)); };
    const x = await px(a), y = await px(b); let s = 0, n = 0;
    for (let i = 0; i < x.length; i += 16) { s += d2000(lab(x[i], x[i + 1], x[i + 2]), lab(y[i], y[i + 1], y[i + 2])); n++; }
    return s / n;
  }, [A, B]);
  check('1710 KTX2 look vs the PNG route in the start hall: mean dE2000 <= 2 (every 4th pixel)', de <= 2 && pngFmt.every((f) => f.endsWith(':png')), `dE ${de.toFixed(3)}; png route ${pngFmt.join(',')}`);
  await g(toRumble);
  await g(() => { const G = __game; G.setMode('rumble'); G.setSeed(12345); G.reset(); });
}
