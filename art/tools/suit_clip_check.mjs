// Gates for the suit movement clips (SUITANIM, 25 Nov): run, hit, death added to the nine school suits; attack and idle unchanged.
// Reads the GLBs as the game will (three r171 GLTFLoader + AnimationMixer, skinned vertices through SkinnedMesh.getVertexPosition),
// so every number is what the game draws. Art tool, not shipped. Pure Node, no browser.
// Usage: node art/tools/suit_clip_check.mjs NEWDIR OLDDIR INFO.json [--mutate] [ids]
//   NEWDIR = GLBs with the new clips, OLDDIR = the approved GLBs (attack/idle and meshes must be byte-identical), INFO = suits_info.json
//   (per suit: run speed v m/s and cycle s from suit_blender.py). Prints PASS/FAIL lines and 'N of M pass'; --mutate then runs each
//   mutation (a broken copy of the data) and prints whether the named gate caught it.
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';

// CONFIG -------------------------------------------------------------------------------------------------------------
const CFG = {
  // Sampling rate of the checks, frames per second (clips are keyed at 60 fps).
  fps: 60,
  // Clips every suit must carry, and no others.
  clips: ['attack', 'death', 'hit', 'idle', 'run'],
  // Hit flinch length band, s (brief: about 0.25-0.35 s).
  hitS: [0.25, 0.35],
  // Death length band, s (brief: about 0.8-1.2 s).
  deathS: [0.8, 1.2],
  // Foot slide allowed per foot per run cycle, m (brief: under 2 cm).
  slideMax: 0.02,
  // A foot vertex counts as touching the floor when it is at most this far above the floor reference, m.
  contactY: 0.02,
  // Contact vertices for the slide measure: at most this far above the floor at both frames of a step, m.
  slideY: 0.01,
  // Shortest ground contact per foot per cycle, frames at 60 fps.
  contactMinF: 4,
  // Allowed dip below the floor reference, m (no part under the floor).
  dipMax: 0.005,
  // Loop seam: closure (frame N vs frame 0) max vertex distance, m; seam acceleration may be at most this factor of the in-cycle max (+0.5 mm).
  seamClose: 0.001, seamAccK: 1.25,
  // Hiccup gate (skill 6j): max joint rotation per 60 fps frame, deg.
  stepMax: 70,
  // Death end: the last this-many seconds hold still (max vertex move, m); lying: top of the body above the floor at the end, m (max).
  stillS: 0.1, stillMax: 0.001, lieTop: 0.9,
  // Hit returns to idle frame 0 within this distance, m; feet stay planted during the hit within this distance, m.
  hitBack: 0.002, hitFeet: 0.02,
  // Budgets per LOD (owner rule 36 and the study), triangles.
  budget: { 0: [10000, 15000], 1: [2000, 3000], 2: [300, 999] },
  // Weight sum tolerance.
  wTol: 0.01,
  // New clips start at t = 0 (tolerance s).
  t0Tol: 1e-6,
};

const ROOT = new URL('../..', import.meta.url).pathname;
const args = process.argv.slice(2), MUT = args.includes('--mutate');
const [NEW, OLD, INFOF, IDARG] = args.filter((a) => a !== '--mutate');
const INFO = JSON.parse(await readFile(INFOF, 'utf8'));
const IDS = IDARG ? IDARG.split(',') : INFO.map((s) => s.id);

// three in Node: copy the vendored loader beside a rewritten import of lib/three.module.min.js
const shim = join(tmpdir(), 'suitcheck_shim'); await mkdir(join(shim, 'loaders'), { recursive: true }); await mkdir(join(shim, 'utils'), { recursive: true });
const threeURL = pathToFileURL(join(ROOT, 'lib/three.module.min.js')).href;
for (const f of ['loaders/GLTFLoader.js', 'utils/BufferGeometryUtils.js']) {
  const src = await readFile(join(ROOT, 'art/viewer/vendor', f), 'utf8');
  await writeFile(join(shim, f), src.replace(/from 'three'/g, `from '${threeURL}'`));
}
const THREE = await import(threeURL);
const { GLTFLoader } = await import(pathToFileURL(join(shim, 'loaders/GLTFLoader.js')).href);

// GLB parsing (raw JSON + BIN, for byte comparisons and key data) -----------------------------------------------------
function parseGLB(buf) {
  const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
  const jl = dv.getUint32(12, true); const json = JSON.parse(new TextDecoder().decode(buf.subarray(20, 20 + jl)));
  const bo = 20 + jl; const bl = dv.getUint32(bo, true); const bin = buf.slice(bo + 8, bo + 8 + bl);
  return { json, bin };
}
function writeGLB(g) {
  const js = new TextEncoder().encode(JSON.stringify(g.json)); const jp = (4 - (js.length % 4)) % 4; const bp = (4 - (g.bin.length % 4)) % 4;
  const total = 12 + 8 + js.length + jp + 8 + g.bin.length + bp; const out = new Uint8Array(total); const dv = new DataView(out.buffer);
  dv.setUint32(0, 0x46546c67, true); dv.setUint32(4, 2, true); dv.setUint32(8, total, true);
  dv.setUint32(12, js.length + jp, true); dv.setUint32(16, 0x4e4f534a, true); out.set(js, 20); out.fill(0x20, 20 + js.length, 20 + js.length + jp);
  const o = 20 + js.length + jp; dv.setUint32(o, g.bin.length + bp, true); dv.setUint32(o + 4, 0x004e4942, true); out.set(g.bin, o + 8);
  return out;
}
const NCOMP = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 }, CSIZE = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4 };
function accBytes(g, i) {
  const a = g.json.accessors[i], bv = g.json.bufferViews[a.bufferView]; const n = a.count * NCOMP[a.type], cs = CSIZE[a.componentType];
  const off = (bv.byteOffset || 0) + (a.byteOffset || 0), st = bv.byteStride;
  if (!st || st === n / a.count * cs) return g.bin.subarray(off, off + n * cs);
  const out = new Uint8Array(n * cs), el = (n / a.count) * cs; for (let k = 0; k < a.count; k++) out.set(g.bin.subarray(off + k * st, off + k * st + el), k * el); return out;
}
function accF(g, i) {
  const a = g.json.accessors[i], b = accBytes(g, i); const ab = b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength);
  const T = { 5126: Float32Array, 5121: Uint8Array, 5123: Uint16Array, 5125: Uint32Array, 5120: Int8Array, 5122: Int16Array }[a.componentType];
  let arr = Array.from(new T(ab));
  if (a.normalized) { const m = { 5121: 255, 5123: 65535, 5120: 127, 5122: 32767 }[a.componentType]; arr = arr.map((x) => Math.max(x / m, -1)); }
  return arr;
}
// write float values back into an accessor (mutations only; float accessors)
function accSet(g, i, k, val) {
  const a = g.json.accessors[i], bv = g.json.bufferViews[a.bufferView]; const off = (bv.byteOffset || 0) + (a.byteOffset || 0);
  new DataView(g.bin.buffer, g.bin.byteOffset).setFloat32(off + k * 4, val, true);
}
const eqBytes = (a, b) => a.length === b.length && a.every((x, k) => x === b[k]);
const clone = (g) => ({ json: JSON.parse(JSON.stringify(g.json)), bin: g.bin.slice() });
const anim = (g, n) => g.json.animations.find((a) => a.name === n);
const chanKey = (g, c) => `${g.json.nodes[c.target.node].name}/${c.target.path}`;

// load with three and sample a clip: per frame, LOD0 world positions (Float32Array) and min/max y over all LODs
async function load(g) {
  const ab = writeGLB(g); const loader = new GLTFLoader();
  return await new Promise((res, rej) => loader.parse(ab.buffer, '', res, rej));
}
function lodOf(o) { for (let p = o; p; p = p.parent) { const m = /_lod(\d)/.exec(p.name || ''); if (m) return +m[1]; } return -1; }
function sample(gl, clipName, extra = {}) {
  const root = gl.scene; const clip = gl.animations.find((a) => a.name === clipName); if (!clip) return null;
  const meshes = []; root.traverse((o) => { if (o.isSkinnedMesh) meshes.push(o); });
  const mix = new THREE.AnimationMixer(root); const act = mix.clipAction(clip); act.setLoop(THREE.LoopOnce); act.clampWhenFinished = true; act.play();   // LoopOnce: t = duration reads the last key (a repeat would wrap to the first)
  const N = Math.round(clip.duration * CFG.fps); const v = new THREE.Vector3();
  const frames = [];
  for (let k = 0; k <= N; k++) {
    const t = Math.min(k / CFG.fps, clip.duration);
    act.time = t; mix.update(0); root.updateMatrixWorld(true);
    let ymin = 1e9, ymax = -1e9; const l0 = [];
    for (const m of meshes) {
      const L = lodOf(m); const n = m.geometry.attributes.position.count; const P = new Float32Array(n * 3);
      for (let i = 0; i < n; i++) { m.getVertexPosition(i, v); v.applyMatrix4(m.matrixWorld); P[i * 3] = v.x; P[i * 3 + 1] = v.y + (extra.dy || 0); P[i * 3 + 2] = v.z; if (P[i * 3 + 1] < ymin) ymin = P[i * 3 + 1]; if (P[i * 3 + 1] > ymax) ymax = P[i * 3 + 1]; }
      if (L === 0) l0.push(P);
    }
    frames.push({ t, ymin, ymax, l0 });
  }
  mix.stopAllAction(); mix.uncacheRoot(root);
  return { N, dur: clip.duration, frames, meshes: meshes.filter((m) => lodOf(m) === 0) };
}
// LOD0 vertex sets weighted (>= 0.99) to a bone, per LOD0 mesh (indices)
function boneVerts(meshes, boneName) {
  return meshes.map((m) => {
    const si = m.geometry.attributes.skinIndex, sw = m.geometry.attributes.skinWeight, out = [];
    const bi = m.skeleton.bones.findIndex((b) => b.name === boneName); if (bi < 0) return out;
    for (let i = 0; i < si.count; i++) for (let c = 0; c < 4; c++) if (si.getComponent(i, c) === bi && sw.getComponent(i, c) >= 0.99) { out.push(i); break; }
    return out;
  });
}

// the gates for one suit; returns [ok, line] list and a map of named results for mutation checks ------------------------------
async function gates(sid, g, old, info, opt = {}) {
  const G = []; const R = {};
  const gate = (name, ok, line) => { G.push([ok, `${sid} ${name}: ${line}`]); R[name] = ok; };
  // 1. clip set
  const names = g.json.animations.map((a) => a.name).sort();
  gate('clips', JSON.stringify(names) === JSON.stringify(CFG.clips), `${names.join(',')}`);
  // 2. attack and idle byte-identical to the approved GLB (every channel: times and values)
  for (const cn of ['attack', 'idle']) {
    const a = anim(g, cn), b = anim(old, cn); let ok = !!(a && b) && a.channels.length === b.channels.length, diff = 0;
    if (ok) { const mb = new Map(b.channels.map((c) => [chanKey(old, c), b.samplers[c.sampler]]));
      for (const c of a.channels) { const s = a.samplers[c.sampler], t = mb.get(chanKey(g, c));
        if (!t || s.interpolation !== t.interpolation || !eqBytes(accBytes(g, s.input), accBytes(old, t.input)) || !eqBytes(accBytes(g, s.output), accBytes(old, t.output))) diff++; } }
    gate(`${cn}_identical`, ok && diff === 0, `${a ? a.channels.length : 0} channels, ${diff} differ from the approved GLB`);
  }
  // 3. meshes byte-identical (positions, normals, UVs, joints, weights, indices) and the skin (joint names, inverse binds)
  let md = 0, mc = 0;
  for (const m of g.json.meshes) { const o = old.json.meshes.find((x) => x.name === m.name); if (!o || o.primitives.length !== m.primitives.length) { md++; continue; }
    m.primitives.forEach((p, k) => { const q = o.primitives[k]; for (const [an, ai] of [...Object.entries(p.attributes), ['indices', p.indices]]) { mc++;
      const qi = an === 'indices' ? q.indices : q.attributes[an]; if (qi === undefined || !eqBytes(accBytes(g, ai), accBytes(old, qi))) md++; } }); }
  const sj = (x) => x.json.skins[0].joints.map((j) => x.json.nodes[j].name).join(',');
  const ibm = eqBytes(accBytes(g, g.json.skins[0].inverseBindMatrices), accBytes(old, old.json.skins[0].inverseBindMatrices));
  gate('mesh_identical', md === 0 && sj(g) === sj(old) && ibm, `${mc} accessors, ${md} differ; joints ${sj(g) === sj(old) ? 'same' : 'DIFFER'}; inverse binds ${ibm ? 'same' : 'DIFFER'}`);
  // 4. budgets and weights (from the GLB)
  for (const m of g.json.meshes) { const L = +/_lod(\d)/.exec(m.name)[1]; const tri = m.primitives.reduce((s, p) => s + g.json.accessors[p.indices].count / 3, 0);
    const [lo, hi] = CFG.budget[L]; gate(`lod${L}_tris`, tri >= lo && tri <= hi, `${tri} (budget ${lo}-${hi})`); }
  let wbad = 0, wn = 0;
  for (const m of g.json.meshes) for (const p of m.primitives) { const w = accF(g, p.attributes.WEIGHTS_0); for (let i = 0; i < w.length; i += 4) { wn++; const s = w[i] + w[i + 1] + w[i + 2] + w[i + 3]; if (Math.abs(s - 1) > CFG.wTol) wbad++; } }
  gate('weights', wbad === 0 && !g.json.meshes.some((m) => m.primitives.some((p) => p.attributes.JOINTS_1)), `${wn} vertices, ${wbad} sums off 1 (tol ${CFG.wTol}), max 4 influences (JOINTS_1 absent)`);
  // 5. raw keys of the new clips: start at 0, quaternion flips 0, max joint step per frame
  for (const cn of ['run', 'hit', 'death']) { const a = anim(g, cn); if (!a) { gate(`${cn}_keys`, false, 'missing'); continue; }
    let t0 = 1e9, flips = 0, step = 0, where = '';
    for (const c of a.channels) { const s = a.samplers[c.sampler]; const tin = accF(g, s.input); t0 = Math.min(t0, tin[0]);
      if (c.target.path !== 'rotation') continue; const q = accF(g, s.output);
      for (let k = 4; k < q.length; k += 4) { let d = q[k] * q[k - 4] + q[k + 1] * q[k - 3] + q[k + 2] * q[k - 2] + q[k + 3] * q[k - 1];
        const n1 = Math.hypot(q[k], q[k + 1], q[k + 2], q[k + 3]), n0 = Math.hypot(q[k - 4], q[k - 3], q[k - 2], q[k - 1]); d /= n1 * n0;
        if (d < 0) flips++; const ang = 2 * Math.acos(Math.min(1, Math.abs(d))) * 180 / Math.PI;
        const dt = (tin[k / 4] - tin[k / 4 - 1]) * CFG.fps; const per = ang / Math.max(dt, 1e-6);
        if (per > step) { step = per; where = `${g.json.nodes[c.target.node].name} key ${k / 4}`; } } }
    gate(`${cn}_keys`, Math.abs(t0) <= CFG.t0Tol && flips === 0 && step <= CFG.stepMax, `first key t=${t0.toFixed(4)} s, quaternion flips ${flips}, max joint step ${step.toFixed(1)} deg/frame at ${where} (max ${CFG.stepMax})`);
  }
  if (!R.clips) return { G, R };
  const gl = await load(g);
  // floor reference: rest = idle at its first key, lowest vertex over all LODs (the approved boots may sit below y = 0: reported)
  const idle = sample(gl, 'idle'); const F = idle.frames[0].ymin;
  R.F = F;
  // 6. run: length, loop seam, contact, slide, floor
  const run = sample(gl, 'run', { dy: opt.runDy || 0 }); const v = info.run_v * (opt.speedK || 1);
  gate('run_length', Math.abs(run.dur - info.run_s) < 0.5 / CFG.fps, `${run.dur.toFixed(3)} s (cycle ${info.run_s} s at ${info.run_v} m/s)`);
  {
    const fr = run.frames, N = run.N; let close = 0, accIn = 0, accSeam = 0;
    for (let mi = 0; mi < fr[0].l0.length; mi++) { const A = fr[0].l0[mi], B = fr[N].l0[mi];
      for (let i = 0; i < A.length; i += 3) close = Math.max(close, Math.hypot(A[i] - B[i], A[i + 1] - B[i + 1], A[i + 2] - B[i + 2]));
      const acc = (a, b, c) => { let m = 0; for (let i = 0; i < a.length; i++) m = Math.max(m, Math.abs(a[i] - 2 * b[i] + c[i])); return m; };
      for (let k = 1; k < N; k++) accIn = Math.max(accIn, acc(fr[k - 1].l0[mi], fr[k].l0[mi], fr[k + 1].l0[mi]));
      accSeam = Math.max(accSeam, acc(fr[N - 1].l0[mi], fr[0].l0[mi], fr[1].l0[mi])); }
    gate('run_seam', close <= CFG.seamClose && accSeam <= accIn * CFG.seamAccK + 0.0005, `closure ${(close * 1000).toFixed(2)} mm (max ${CFG.seamClose * 1000}), seam accel ${(accSeam * 1000).toFixed(2)} vs in-cycle max ${(accIn * 1000).toFixed(2)} mm/frame^2`);
    // feet: world = clip position + travel v*t along +Z (the suit faces +Z)
    for (const side of ['R', 'L']) {
      const sets = boneVerts(run.meshes, `foot${side}`); let nv = sets.reduce((s, x) => s + x.length, 0);
      const W = (k, mi, i) => { const P = fr[k % N].l0[mi]; return [P[i * 3], P[i * 3 + 1], P[i * 3 + 2] + v * (k / CFG.fps)]; };
      const fmin = (k) => { let m = 1e9; sets.forEach((s, mi) => s.forEach((i) => { m = Math.min(m, fr[k % N].l0[mi][i * 3 + 1]); })); return m; };
      const con = []; for (let k = 0; k < N; k++) con.push(fmin(k) <= F + CFG.contactY);
      // contact intervals on the cycle (wrapping)
      const ivs = []; const start = con.findIndex((c) => !c);
      if (start < 0) { ivs.push([0, N]); } else { let k = start, cur = null; for (let s = 0; s < N; s++, k++) { const kk = k % N; if (con[kk] && !cur) cur = [k, k]; else if (con[kk] && cur) cur[1] = k; else if (!con[kk] && cur) { ivs.push(cur); cur = null; } } if (cur) ivs.push(cur); }
      let slide = 0, dip = 1e9, longest = 0;
      for (const [a, b] of ivs) { longest = Math.max(longest, b - a + 1);
        for (let k = a; k < b; k++) { const ds = [];
          sets.forEach((s, mi) => s.forEach((i) => { const p = W(k, mi, i), q = W(k + 1, mi, i); if (p[1] <= F + CFG.slideY && q[1] <= F + CFG.slideY) ds.push(Math.hypot(q[0] - p[0], q[2] - p[2])); }));
          if (ds.length) { ds.sort((x, y) => x - y); slide += ds[ds.length >> 1]; } }
        for (let k = a; k <= b; k++) dip = Math.min(dip, fmin(k)); }
      gate(`run_contact_${side}`, nv > 0 && ivs.length >= 1 && longest >= CFG.contactMinF && dip >= F - CFG.dipMax,
        `${ivs.length} contact(s) per cycle, longest ${longest} frames (min ${CFG.contactMinF}), sole min ${((dip - F) * 1000).toFixed(1)} mm vs floor ref (${nv} foot vertices)`);
      gate(`run_slide_${side}`, ivs.length >= 1 && slide <= CFG.slideMax, `${(slide * 100).toFixed(2)} cm per cycle (max ${CFG.slideMax * 100})`);
    }
    const flight = con2flight(run, F);
    G.push([true, `${sid} run_info: ${flight} flight frames (both feet off) of ${N}; floor ref F = ${(F * 1000).toFixed(1)} mm`]);
    const dmin = Math.min(...fr.map((f) => f.ymin)); gate('run_floor', dmin >= F - CFG.dipMax, `lowest vertex ${((dmin - F) * 1000).toFixed(1)} mm vs floor ref, all LODs, all frames`);
  }
  // 7. hit: length, back to idle frame 0, feet planted, floor
  const hit = sample(gl, 'hit');
  gate('hit_length', hit.dur >= CFG.hitS[0] - 1e-6 && hit.dur <= CFG.hitS[1] + 1e-6, `${hit.dur.toFixed(3)} s (${CFG.hitS.join('-')})`);
  { let back = 0, feet = 0; const fe = ['R', 'L'].map((s) => boneVerts(hit.meshes, `foot${s}`));
    hit.frames[hit.N].l0.forEach((P, mi) => { const Q = idle.frames[0].l0[mi]; for (let i = 0; i < P.length; i += 3) back = Math.max(back, Math.hypot(P[i] - Q[i], P[i + 1] - Q[i + 1], P[i + 2] - Q[i + 2])); });
    for (const f of hit.frames) fe.forEach((sets) => sets.forEach((s, mi) => s.forEach((i) => { const P = f.l0[mi], Q = idle.frames[0].l0[mi]; feet = Math.max(feet, Math.hypot(P[i * 3] - Q[i * 3], P[i * 3 + 1] - Q[i * 3 + 1], P[i * 3 + 2] - Q[i * 3 + 2])); })));
    gate('hit_returns', back <= CFG.hitBack, `end vs idle frame 0: ${(back * 1000).toFixed(2)} mm (max ${CFG.hitBack * 1000})`);
    gate('hit_feet', feet <= CFG.hitFeet, `feet move ${(feet * 100).toFixed(2)} cm during the flinch (max ${CFG.hitFeet * 100})`);
    const dmin = Math.min(...hit.frames.map((f) => f.ymin)); gate('hit_floor', dmin >= F - CFG.dipMax, `lowest vertex ${((dmin - F) * 1000).toFixed(1)} mm vs floor ref`); }
  // 8. death: length, never under the floor, ends lying still and touching
  const de = sample(gl, 'death', { dy: opt.deathDy || 0 });
  gate('death_length', de.dur >= CFG.deathS[0] - 1e-6 && de.dur <= CFG.deathS[1] + 1e-6, `${de.dur.toFixed(3)} s (${CFG.deathS.join('-')})`);
  { const dmin = Math.min(...de.frames.map((f) => f.ymin)), wf = de.frames.findIndex((f) => f.ymin === dmin);
    gate('death_floor', dmin >= F - CFG.dipMax, `lowest vertex ${((dmin - F) * 1000).toFixed(1)} mm vs floor ref (frame ${wf}), all LODs, all frames`);
    const last = de.frames[de.N], ks = Math.round(CFG.stillS * CFG.fps); let mv = 0;
    for (let k = de.N - ks; k < de.N; k++) de.frames[k].l0.forEach((P, mi) => { const Q = last.l0[mi]; for (let i = 0; i < P.length; i++) mv = Math.max(mv, Math.abs(P[i] - Q[i])); });
    gate('death_still', mv <= CFG.stillMax, `last ${CFG.stillS} s max move ${(mv * 1000).toFixed(2)} mm (max ${CFG.stillMax * 1000})`);
    gate('death_lying', last.ymax - F <= CFG.lieTop && last.ymin - F <= CFG.contactY,
      `end: top ${(last.ymax - F).toFixed(2)} m above the floor ref (max ${CFG.lieTop}), lowest ${((last.ymin - F) * 1000).toFixed(1)} mm (touching <= ${CFG.contactY * 1000})`); }
  return { G, R };
}
function con2flight(run, F) {
  const sets = ['R', 'L'].map((s) => boneVerts(run.meshes, `foot${s}`)); let n = 0;
  for (let k = 0; k < run.N; k++) { const off = sets.every((ss) => { let m = 1e9; ss.forEach((s, mi) => s.forEach((i) => { m = Math.min(m, run.frames[k].l0[mi][i * 3 + 1]); })); return m > F + CFG.contactY; }); if (off) n++; }
  return n;
}

// mutations: each breaks one thing; the named gate must fail ----------------------------------------------------------------------
function chanOf(g, clip, node, path) { const a = anim(g, clip); const c = a.channels.find((c) => g.json.nodes[c.target.node].name === node && c.target.path === path); return c ? a.samplers[c.sampler] : null; }
const MUTS = [
  ['run_slide_R', 'run played 20% faster than the ground speed', (g) => g, { speedK: 1.2 }],
  ['run_contact_R', 'run 5 cm above the floor', (g) => g, { runDy: 0.05 }],
  ['death_floor', 'death 5 cm into the floor', (g) => g, { deathDy: -0.05 }],
  ['run_seam', 'run last key of the chest moved', (g) => { const s = chanOf(g, 'run', 'chest', 'rotation'); const n = g.json.accessors[s.output].count; accSet(g, s.output, (n - 1) * 4, 0.3); return g; }],
  ['attack_identical', 'one attack key changed', (g) => { const s = chanOf(g, 'attack', 'chest', 'rotation'); accSet(g, s.output, 4, 0.2); return g; }],
  ['clips', 'hit clip dropped', (g) => { g.json.animations = g.json.animations.filter((a) => a.name !== 'hit'); return g; }],
  ['death_still', 'death last key of the head moved', (g) => { const s = chanOf(g, 'death', 'head', 'rotation'); const n = g.json.accessors[s.output].count; accSet(g, s.output, (n - 1) * 4, 0.4); return g; }],
  ['hit_returns', 'hit last key of the chest moved', (g) => { const s = chanOf(g, 'hit', 'chest', 'rotation'); const n = g.json.accessors[s.output].count; accSet(g, s.output, (n - 1) * 4, 0.3); return g; }],
  ['weights', 'one weight scaled', (g) => { const p = g.json.meshes[0].primitives[0]; accSet(g, p.attributes.WEIGHTS_0, 0, 0.5); return g; }],
  ['mesh_identical', 'one vertex moved', (g) => { const p = g.json.meshes[0].primitives[0]; accSet(g, p.attributes.POSITION, 0, 0.123); return g; }],
  // round 3: the chest is keyed every frame (spine was a 2-key constant: the mutant wrote past it and was missed)
  ['run_keys', 'one run key sign-flipped', (g) => { const s = chanOf(g, 'run', 'chest', 'rotation'); const q = accF(g, s.output); for (let c = 0; c < 4; c++) accSet(g, s.output, 8 + c, -q[8 + c]); return g; }],
  ['hit_length', 'hit stretched to 0.5 s', (g) => { const a = anim(g, 'hit'); const seen = new Set(); for (const s of a.samplers) { if (seen.has(s.input)) continue; seen.add(s.input); const t = accF(g, s.input); t.forEach((x, k) => accSet(g, s.input, k, x * 0.5 / 0.3)); g.json.accessors[s.input].max = [t[t.length - 1] * 0.5 / 0.3]; } return g; }],
];

let all = []; const mres = [];
for (const sid of IDS) {
  const info = INFO.find((s) => s.id === sid);
  const g = parseGLB(new Uint8Array(await readFile(join(NEW, `${sid}.glb`)))), old = parseGLB(new Uint8Array(await readFile(join(OLD, `${sid}.glb`))));
  const { G } = await gates(sid, g, old, info);
  for (const [ok, l] of G) console.log((ok ? 'PASS ' : 'FAIL ') + l);
  all = all.concat(G.filter(([ok, l]) => !l.includes('_info:')));
  if (MUT && sid === IDS[0]) for (const [name, what, fn, opt] of MUTS) {
    let caught; try { const r = await gates(sid, fn(clone(g)), old, info, opt); caught = r.R[name] === false; } catch (e) { caught = true; }
    mres.push(caught); console.log(`MUT ${caught ? 'caught' : 'MISSED'} ${sid} ${name}: ${what}`);
  }
}
const nf = all.filter(([ok]) => !ok).length;
console.log(`${all.length - nf} of ${all.length} pass`);
if (MUT) console.log(`mutations ${mres.filter(Boolean).length} of ${mres.length} caught`);
