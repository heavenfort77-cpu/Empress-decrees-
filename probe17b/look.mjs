// 17b look probe (CI only, not committed to the game branch): the start hall drawn by the build before 17b (PNG textures, uploaded flipped) and
// by the 17b build (KTX2 from assets/c, v flipped by the texture transform), same seed, spot, game time and camera; mean dE2000 of the frame (every 2nd pixel), share of pixels over 10.
import { createServer } from 'node:http'; import { readFile } from 'node:fs/promises'; import { extname, join, normalize } from 'node:path';
import { chromium } from 'playwright';
const ROOT = new URL('..', import.meta.url).pathname, T = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.wasm': 'application/wasm' };
const srv = createServer(async (q, s) => { const p = normalize(join(ROOT, decodeURIComponent(q.url.split('?')[0]))); try { const b = await readFile(p); s.writeHead(200, { 'content-type': T[extname(p)] || 'application/octet-stream' }); s.end(b); } catch { s.writeHead(404); s.end(); } }).listen(0);
const B = `http://127.0.0.1:${srv.address().port}/`, Q = '?lock&tier=medium&bots=0&pkit=placeholder&layout=proto';
const br = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
async function shot(path, spot) {
  const p = await br.newPage({ viewport: { width: 1366, height: 768 } }); const errs = []; p.on('pageerror', (e) => errs.push(String(e).slice(0, 160)));
  await p.goto(B + path + Q); await p.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
  await p.evaluate(() => { const G = __game; G.setSeed(12345); G.setMode('palace'); G.reset(); });
  await p.waitForFunction(() => !__game.loadBusy || !__game.loadBusy(), null, { timeout: 120000 });
  await p.evaluate((spot) => { const G = __game, r = G.player(); G.teleport(r.x + spot[0], r.z + spot[1]); G.step(120);
    Object.defineProperty(document, 'hidden', { value: true, configurable: true }); document.dispatchEvent(new Event('visibilitychange')); G.render(true); }, spot);
  const b = (await p.screenshot({ type: 'png' })).toString('base64'); await p.close(); return { b, errs };
}
const de = async (a, b) => { const p = await br.newPage(); const r = await p.evaluate(async ([a, b]) => {
  const px = async (s) => { const im = new Image(); im.src = 'data:image/png;base64,' + s; await im.decode(); const c = document.createElement('canvas'); c.width = im.width; c.height = im.height; const x = c.getContext('2d', { willReadFrequently: true }); x.drawImage(im, 0, 0); return x.getImageData(0, 0, c.width, c.height).data; };
  const lab = (r, g, b) => { const f = (c) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; }; const R = f(r), G = f(g), B = f(b); const h = (t) => (t > 0.008856 ? Math.cbrt(t) : 7.787 * t + 16 / 116);
    const X = h((0.4124 * R + 0.3576 * G + 0.1805 * B) / 0.95047), Y = h(0.2126 * R + 0.7152 * G + 0.0722 * B), Z = h((0.0193 * R + 0.1192 * G + 0.9505 * B) / 1.08883); return [116 * Y - 16, 500 * (X - Y), 200 * (Y - Z)]; };
    const d2000 = (p, q) => { const [L1, a1, b1] = p, [L2, a2, b2] = q, rad = Math.PI / 180, C1 = Math.hypot(a1, b1), C2 = Math.hypot(a2, b2), Cm = (C1 + C2) / 2, G = 0.5 * (1 - Math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)));
      const a1p = (1 + G) * a1, a2p = (1 + G) * a2, C1p = Math.hypot(a1p, b1), C2p = Math.hypot(a2p, b2), h1 = (Math.atan2(b1, a1p) / rad + 360) % 360, h2 = (Math.atan2(b2, a2p) / rad + 360) % 360;
      const dL = L2 - L1, dC = C2p - C1p; let dh = h2 - h1; if (C1p * C2p === 0) dh = 0; else if (dh > 180) dh -= 360; else if (dh < -180) dh += 360;
      const dH = 2 * Math.sqrt(C1p * C2p) * Math.sin(dh * rad / 2), Lm = (L1 + L2) / 2, Cmp = (C1p + C2p) / 2;
      let hm = h1 + h2; if (C1p * C2p !== 0) hm = Math.abs(h1 - h2) <= 180 ? hm / 2 : hm < 360 ? (hm + 360) / 2 : (hm - 360) / 2;
      const T = 1 - 0.17 * Math.cos((hm - 30) * rad) + 0.24 * Math.cos(2 * hm * rad) + 0.32 * Math.cos((3 * hm + 6) * rad) - 0.2 * Math.cos((4 * hm - 63) * rad);
      const SL = 1 + 0.015 * (Lm - 50) ** 2 / Math.sqrt(20 + (Lm - 50) ** 2), SC = 1 + 0.045 * Cmp, SH = 1 + 0.015 * Cmp * T, RT = -2 * Math.sqrt(Cmp ** 7 / (Cmp ** 7 + 25 ** 7)) * Math.sin(60 * Math.exp(-(((hm - 275) / 25) ** 2)) * rad);
      return Math.sqrt((dL / SL) ** 2 + (dC / SC) ** 2 + (dH / SH) ** 2 + RT * (dC / SC) * (dH / SH)); };
  const x = await px(a), y = await px(b); let s = 0, n = 0, big = 0; for (let i = 0; i < x.length; i += 8) { const d = d2000(lab(x[i], x[i + 1], x[i + 2]), lab(y[i], y[i + 1], y[i + 2])); s += d; n++; if (d > 10) big++; }
  return { mean: s / n, over10: big / n }; }, [a, b]); await p.close(); return r; };
const rows = [];
for (const spot of [[0, 0], [-4, 3], [5, -3]]) {
  const o = await shot('probe17b/index_old.html', spot), n = await shot('index.html', spot);
  const d = await de(o.b, n.b); rows.push({ spot, dE2000: +d.mean.toFixed(3), over10: +(d.over10 * 100).toFixed(2), errs: o.errs.length + n.errs.length });
}
for (const r of rows) console.log('LOOK', JSON.stringify(r));
console.log(rows.every((r) => r.dE2000 <= 2 && r.errs === 0) ? 'LOOK PASS' : 'LOOK FAIL');
await br.close(); srv.close();
