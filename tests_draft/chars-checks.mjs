// Runner for the src/chars.js checks (draft for INT). Serves the repo, opens ci_probe/chars.html?test=1&notex=1 in headless Chromium
// (SwiftShader: correctness and counts only, never fps), prints PASS/FAIL per check.
// Usage: node tests_draft/chars-checks.mjs            -> the checks on the tree as it is
//        node tests_draft/chars-checks.mjs --mutants  -> also every mutant below on a copy of src/chars.js; each must fail its named check
import { createServer } from 'node:http';
import { readFile, writeFile, mkdtemp } from 'node:fs/promises';
import { extname, join, normalize } from 'node:path';
import { tmpdir } from 'node:os';
let chromium;
try { ({ chromium } = await import('playwright')); } catch { ({ chromium } = await import('/opt/npm-tools/node_modules/playwright/index.mjs')); }
const ROOT = new URL('..', import.meta.url).pathname;
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.png': 'image/png', '.json': 'application/json', '.ktx2': 'image/ktx2', '.wasm': 'application/wasm', '.glb': 'model/gltf-binary' };
// Mutants: [name, check that must fail, exact text in src/chars.js, replacement].
export const MUTANTS = [
  ['per-part skeletons', 'C1_one_skeleton', 'sm.bind(skel, I4);', 'sm.bind(new THREE.Skeleton(skel.bones, tpl.boneInv), I4);'],
  ['frustum culling off', 'C3_frustum_culled', "sm.name = tpl.id + '_l' + i + '_' + p.matName;", "sm.name = tpl.id + '_l' + i + '_' + p.matName; sm.frustumCulled = !1;"],
  ['no off-screen gate', 'C5_anim_gating', 'if (!FR.frustum.intersectsSphere(FR.sph)) { FR.skipped++; return; }', 'FR.skipped += 0;'],
  ['no far rate', 'C5_anim_gating', 'this.acc < 1 / CHR.anim.farHz) return;', 'this.acc < 0) return;'],
  ['sphere not enlarged', 'C4_spheres', 's.radius *= CHR.sphereK;', 's.radius *= 1;'],
  ['crowd sphere stale', 'C4_spheres', 'B.sphere.center.set(', 'B.sphere.center.add('],
  ['floor offset dropped', 'C6_suit_floor_run', 'rig.position.y = -tpl.floorY;', 'rig.position.y = 0;'],
  ['run rate fixed', 'C6_suit_floor_run', 'const r = speed / this.tpl.runV;', 'const r = 1;'],
  ['clip start kept', 'C7_clips_start_0', 'if (t0 > 0 && t0 < Infinity)', 'if (t0 < 0)'],
  ['tread sign', 'C8_tread_scroll', 'this.treadM = (this.treadM + m / this.tpl.tread) % 1;', 'this.treadM = (this.treadM - m / this.tpl.tread) % 1;'],
  ['tiger capsule short', 'C9_hit_capsules', 'tiger: { r: 0.75, half: 1.7, off: 0.26 }', 'tiger: { r: 0.75, half: 1.2, off: 0.26 }'],
  ['cub radius old', 'C9_hit_capsules', 'stalker: { r: 0.59, half: 0.375', 'stalker: { r: 0.45, half: 0.515'],
  ['sweep 150 deg', 'C10_sweep_sector', 'sweep: { r: 2.5, deg: 120 }', 'sweep: { r: 2.5, deg: 150 }'],
  ['drawn sector off centre', 'C10_sweep_sector', 'Math.PI / 2 - t / 2, t);', 'Math.PI / 2 - t / 3, t);'],
  ['bake without bind inverse', 'C11_bake_matches_skin', 'M.multiplyMatrices(bones[b].matrixWorld, tpl.boneInv[b]);', 'M.copy(bones[b].matrixWorld);'],
  ['nearest weights from a far vertex', 'C19_lod_deform', 'for (let k = 0; k < 4; k++) { si[i * 4 + k] = ssi[best * 4 + k];', 'best = (best + 997) % n0; for (let k = 0; k < 4; k++) { si[i * 4 + k] = ssi[best * 4 + k];'],
  ['no weight transfer', 'C12_lod_weights', 'if (geo.userData.needWeights) weightGap', 'if (!1) weightGap'],
  ['outline width ignores pixel ratio', 'C13_outline_hull', 'OUT.px.value = CHR.outline.px * pr;', 'OUT.px.value = CHR.outline.px;'],
  ['memory grows per spawn', 'C15_memory_flat', 'show(scene) { if (!this.root.parent) scene.add(this.root); this.on = true; }', 'show(scene) { if (!this.root.parent) scene.add(this.root); this.on = true; this.root.add(new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.01, 0.01), outlineMaterial())); }'],
  ['cloth colour hard-coded', 'C16_cloth_from_file', "color: src.color.clone(), metalness: 0, roughness: 0.85", "color: new THREE.Color(0xb8862e), metalness: 0, roughness: 0.85"],
  ['statue skinned', 'C18_statue_static', "const g = poseGeo(p.geo, M), m = new THREE.Mesh(g, p.mats[0]);", "const g = p.geo, m = new THREE.SkinnedMesh(g, p.mats[0]); m.bind(new THREE.Skeleton(bones, tpl.boneInv), I4);"],
];
function serve(srcOverride) {
  return new Promise((res) => {
    const s = createServer(async (req, rq) => {
      const u = decodeURIComponent(req.url.split('?')[0]);
      const p = u === '/src/chars.js' && srcOverride ? srcOverride : normalize(join(ROOT, u));
      try { const b = await readFile(p); rq.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); rq.end(b); } catch { rq.writeHead(404); rq.end(); }
    }).listen(0, () => res(s));
  });
}
async function once(browser, srcOverride) {
  const server = await serve(srcOverride), port = server.address().port;
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } }), errs = [];
  page.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));
  page.on('console', (m) => { if (m.type() === 'error') errs.push(m.text().slice(0, 200)); });
  let checks = null;
  try {
    await page.goto(`http://127.0.0.1:${port}/ci_probe/chars.html?test=1&notex=1`);
    await page.waitForFunction(() => window.__ready === true || window.__err, null, { timeout: 600000 });
    checks = await page.evaluate(() => window.__checks || null);
  } catch (e) { errs.push('runner: ' + String(e).slice(0, 200)); }
  await page.close(); server.close();
  return { checks, errs };
}
const main = async () => {
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--js-flags=--expose-gc', '--enable-precise-memory-info'] });
  const base = await once(browser, null);
  let fails = 0;
  if (!base.checks) { console.log('FAIL page did not finish: ' + base.errs.join(' | ')); fails++; }
  else for (const c of base.checks) { console.log(`${c.pass ? 'PASS' : 'FAIL'} ${c.name}: ${c.detail}`); if (!c.pass) fails++; }
  if (base.errs.length) console.log('PAGE ERRORS ' + base.errs.length + ': ' + base.errs.slice(0, 3).join(' | '));
  console.log(`CHECKS ${base.checks ? base.checks.filter((c) => c.pass).length : 0} of ${base.checks ? base.checks.length : '?'}`);
  if (process.argv.includes('--mutants')) {
    const src = await readFile(join(ROOT, 'src/chars.js'), 'utf8'), dir = await mkdtemp(join(tmpdir(), 'chrmut-'));
    let caught = 0, named = 0, tried = 0;
    // MUT_SHARD=k/n runs every n-th mutant from k (parallel runner jobs); the base checks run in every shard.
    const [sk, sn] = (process.env.MUT_SHARD || '0/1').split('/').map(Number);
    for (const [mi, [name, want, a, b]] of MUTANTS.entries()) {
      if (mi % sn !== sk) continue; tried++;
      if (!src.includes(a)) { console.log(`MUTANT ${name}: NOT APPLIED (text not found)`); continue; }
      const f = join(dir, 'chars.js'); await writeFile(f, src.replace(a, b));
      const r = await once(browser, f), failed = r.checks ? r.checks.filter((c) => !c.pass).map((c) => c.name) : ['(page failed)'];
      const isCaught = failed.length > 0, isNamed = failed.includes(want);
      caught += isCaught; named += isNamed;
      console.log(`MUTANT ${name}: ${isNamed ? 'CAUGHT by ' + want : isCaught ? 'caught (not by ' + want + ')' : 'MISSED'}; failing: ${failed.join(',')}${r.errs.length ? ' errs ' + r.errs[0] : ''}`);
    }
    console.log(`MUTANTS shard ${sk}/${sn}: caught ${caught} of ${tried}, by the named check ${named} of ${tried}`);
    if (named < tried) fails++;
  }
  await browser.close();
  console.log(fails ? 'RESULT FAIL' : 'RESULT PASS');
  process.exit(fails ? 1 : 0);
};
main();
