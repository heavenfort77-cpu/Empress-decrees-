// In-page checks for src/chars.js (draft for INT; runs inside ci_probe/chars.html?test=1 through tests_draft/chars-checks.mjs).
// Each check: { name, pass, detail }. Names are what the mutation list in chars-checks.mjs expects to fail.
const frames = (n) => new Promise((res) => { let c = 0; const f = () => { if (++c >= n) res(); else requestAnimationFrame(f); }; requestAnimationFrame(f); });

export async function run(P) {
  const { CH, THREE, r, sc, cam, crowd, RIGS, TPL, GI, INFO } = P, out = [];
  const add = (name, pass, detail) => out.push({ name, pass: !!pass, detail: String(detail).slice(0, 300) });
  const tpls = [...Object.values(TPL), ...GI];
  await frames(20);

  // C1 one skeleton per unit (all parts, LOD levels and outline hulls share it).
  const sk = RIGS.map((u) => u.rig.skeletons());
  add('C1_one_skeleton', sk.every((n) => n === 1), 'skeletons per rig ' + sk.join(','));

  // C2 bone-texture uploads per frame <= rigs animated that frame (one per unit), crowd uploads no textures in play.
  const gl = r.getContext(); let up = 0; const o1 = gl.texSubImage2D, o2 = gl.texImage2D;
  gl.texSubImage2D = function (...a) { up++; return o1.apply(this, a); }; gl.texImage2D = function (...a) { up++; return o2.apply(this, a); };
  let mix = 0; const N = 30; const spin = () => new Promise((res) => { let c = 0; const f = () => { mix += CH.stats().mixers; if (++c >= N) res(); else requestAnimationFrame(f); }; requestAnimationFrame(f); });
  await spin(); gl.texSubImage2D = o1; gl.texImage2D = o2;
  const onScreen = RIGS.filter((u) => u.rig.on).length;
  add('C2_uploads_per_frame', up / N <= onScreen + 0.01 && up > 0, `uploads/frame ${(up / N).toFixed(2)} rigs ${onScreen} mixer steps/frame ${(mix / N).toFixed(2)}`);

  // C3 never frustumCulled = false on any character object.
  let off = 0; sc.traverse((o) => { if ((o.isMesh || o.isSkinnedMesh) && o.frustumCulled === false) off++; });
  add('C3_frustum_culled', off === 0, 'objects with frustumCulled false: ' + off);

  // C4 bounding spheres: rigs >= sphereK x the bind-pose sphere; every crowd instance centre inside its batch sphere.
  let bad = 0, worst = 99;
  for (const t of tpls) for (const L of t.lods) {
    const b = new THREE.Box3(), s = new THREE.Sphere(); for (const p of L.parts) { p.geo.computeBoundingBox(); b.union(p.geo.boundingBox); } b.getBoundingSphere(s);
    const k = L.sphere.radius / s.radius; worst = Math.min(worst, k); if (k < CH.CHR.sphereK * 0.999) bad++;
  }
  let outside = 0; const v = new THREE.Vector3(), m4 = new THREE.Matrix4();
  for (const B of crowd.batches) for (let i = 0; i < B.count; i++) { m4.fromArray(B.mat.array, i * 16); v.setFromMatrixPosition(m4); if (v.distanceTo(B.sphere.center) > B.sphere.radius - 1) outside++; }
  add('C4_spheres', bad === 0 && outside === 0 && crowd.batches.some((B) => B.count > 0), `rig spheres below k: ${bad} (min ratio ${worst.toFixed(2)}), crowd instances outside: ${outside}`);

  // C5 animation gating: a unit behind the camera does not animate; a unit past nearM steps at <= farHz.
  const u0 = RIGS[0].rig, a0 = u0.base;
  const save = [u0.x, u0.z];
  const holdPlace = (x, z) => { u0.update = ((f) => function (dt) { this.place(x, 0, z, 0, 1); return f.call(this, dt); })(Object.getPrototypeOf(u0).update); };
  holdPlace(cam.position.x, cam.position.z + 30); const tA = a0.time; const s0 = u0.animSteps; await frames(30); const behind = u0.animSteps - s0;
  holdPlace(0, -3 - (CH.CHR.anim.nearM + 2)); const s1 = u0.animSteps, t1 = performance.now(); await frames(60); const far = (u0.animSteps - s1) / ((performance.now() - t1) / 1000);
  delete u0.update; u0.place(save[0], 0, save[1], 0, 1);
  add('C5_anim_gating', behind === 0 && far <= CH.CHR.anim.farHz * 1.25 && far > 0, `behind camera steps ${behind} (time ${tA.toFixed(3)}), far steps/s ${far.toFixed(1)} (farHz ${CH.CHR.anim.farHz})`);

  // C6 suit placement y = -floor_y; run timeScale = speed / run_v.
  let pl = 0, ts = 0;
  for (const u of RIGS) if (u.rig.tpl.kind === 'suit') {
    const id = u.rig.tpl.id; if (Math.abs(u.rig.rig.position.y + INFO[id].floor_y) > 1e-6) pl++;
    u.rig.setRun(4.5); if (Math.abs(u.rig.actions.run.timeScale - 4.5 / INFO[id].run_v) > 1e-6) ts++;
  }
  add('C6_suit_floor_run', pl === 0 && ts === 0, `floor offsets wrong ${pl}, run timeScale wrong ${ts}`);

  // C7 every clip starts at 0 s.
  let late = 0; for (const t of tpls) for (const n in t.clips) for (const tr of t.clips[n].tracks) if (tr.times[0] > 1e-6) late++;
  add('C7_clips_start_0', late === 0, 'tracks starting after 0: ' + late);

  // C8 treads: offset = metres / mpr (wrapped to [0, 1)).
  const cub = RIGS.find((u) => u.rig.tpl.id === 'stalker').rig; cub.treadM = 0; cub.addTread(0.2);
  const st = crowd.makeState('zu'); crowd.addTread(st, 0.2);
  const ok8 = Math.abs(cub.tread.value - 0.2 / CH.CHR.tread.stalker) < 1e-9 && Math.abs(st.treadM - 0.2 / CH.CHR.tread.zu) < 1e-9;
  add('C8_tread_scroll', ok8, `stalker ${cub.tread.value.toFixed(4)} want ${(0.2 / CH.CHR.tread.stalker).toFixed(4)}, zu ${st.treadM.toFixed(4)} want ${(0.2 / CH.CHR.tread.zu).toFixed(4)}`);

  // C9 hit capsules fitted to the models: hit at the model edge, miss 0.3 m beyond (tiger: head to the 4.9 m body end; the tail is outside).
  const H = CH.HIT, res9 = [];
  for (const [k, end0] of [['tiger', 4.9], ['stalker', 0], ['howler', 0]]) {
    const s = CH.CHR.hit[k], b = TPL[k].lods[0].box, u = { x: 0, z: 0, fx: 0, fz: 1, r: s.r, hit: s };
    const front = b.max.z, back = end0 ? front - end0 : b.min.z, side = (b.max.x - b.min.x) / 2, mid = (front + back) / 2;
    const tests = [[0, front - 0.01, true], [0, front + 0.3, false], [0, back + 0.01, true], [0, back - 0.3, false], [side - 0.05, mid, true], [side + 0.3, mid, false]];
    for (const [x, z, want] of tests) { const hit = H.dist(u, x, z) <= s.r; if (hit !== want) res9.push(`${k} (${x.toFixed(2)},${z.toFixed(2)}) hit ${hit}`); }
    if (!H.line(u, 0, front + 1, 0, -1, 1.05, 0.1)) res9.push(k + ' line to the nose missed');
    if (H.line(u, side + 0.4 + s.r, -5, 0, 1, 10, 0.1)) res9.push(k + ' line beside hit');
  }
  add('C9_hit_capsules', res9.length === 0, res9.join('; ') || 'tiger/stalker/howler edges hit, 0.3 m beyond miss');

  // C10 giant sweep = owner pick 2.5 m over 120 deg; drawn sector equals the hit sector.
  const g = { x: 0, z: 0, fx: 0, fz: 1 }, R = 2.5, res10 = [];
  if (CH.CHR.sweep.r !== R || CH.CHR.sweep.deg !== 120) res10.push(`CHR.sweep ${CH.CHR.sweep.r} m ${CH.CHR.sweep.deg} deg (owner 2.5 / 120)`);
  const at = (deg, d) => [Math.sin(deg * Math.PI / 180) * d, Math.cos(deg * Math.PI / 180) * d];
  for (const [deg, d, want] of [[0, R - 0.01, true], [0, R + 0.01, false], [59, 2.4, true], [-59, 2.4, true], [61, 2.4, false], [-61, 2.4, false], [180, 0.5, false]]) { const [x, z] = at(deg, d); if (H.sector(g, x, z) !== want) res10.push(`(${deg} deg, ${d} m) ${!want}`); }
  const geo = CH.sectorGeometry(), p = geo.attributes.position; let rmax = 0, amin = 999, amax = -999;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = -p.getZ(i), d = Math.hypot(x, z); rmax = Math.max(rmax, d); if (d > 0.01) { const a = Math.atan2(x, z) * 180 / Math.PI; amin = Math.min(amin, a); amax = Math.max(amax, a); } }
  if (Math.abs(rmax - CH.CHR.sweep.r) > 1e-4 || Math.abs(amax - amin - CH.CHR.sweep.deg) > 0.01 || Math.abs(amax + amin) > 0.01) res10.push(`drawn r ${rmax.toFixed(3)} span ${(amax - amin).toFixed(2)} centre ${((amax + amin) / 2).toFixed(2)}`);
  add('C10_sweep_sector', res10.length === 0, res10.join('; ') || 'hit and drawn sector 2.5 m / 120 deg');

  // C11 baked crowd pose = CPU skinning of the same template at the same clip time (<= 1 mm).
  let worst11 = 0;
  for (const t of ['zu', 'ls', 'che']) {
    const T = crowd.types[t], tp = T.tpl, rig = CH.spawnRig(tp, { outline: false }), e = T.bake.table.move, fps = CH.CHR.bakeFps, f = 17;
    rig.play('move'); rig.actions.move.time = f / fps; rig.mixer.update(0); rig.root.updateMatrixWorld(true); rig.skel.update();
    const sm = rig.parts[0].mesh, geo0 = sm.geometry, d = T.bake.data, nb = T.bake.nb, A = new THREE.Vector3(), B = new THREE.Vector3(), M = new THREE.Matrix4(), tmp = new THREE.Vector3();
    for (let i = 0; i < geo0.attributes.position.count; i += 7) {
      B.fromBufferAttribute(geo0.attributes.position, i); sm.applyBoneTransform(i, B);
      A.set(0, 0, 0); const si = geo0.attributes.skinIndex, sw = geo0.attributes.skinWeight;
      for (let q = 0; q < 4; q++) { const w = sw.getComponent(i, q); if (!w) continue; M.fromArray(d, ((e.row0 + f) * nb * 4 + si.getComponent(i, q) * 4) * 4); tmp.fromBufferAttribute(geo0.attributes.position, i).applyMatrix4(M); A.addScaledVector(tmp, w); }
      worst11 = Math.max(worst11, A.distanceTo(B));
    }
  }
  add('C11_bake_matches_skin', worst11 <= 0.001, `worst vertex ${(worst11 * 1000).toFixed(3)} mm (zu, ls, che move frame 17)`);

  // C12 crowd static LODs got weights: every vertex sums to 1, indices inside the bone list; transfer distance reported.
  let bw = 0, bi = 0, gap = 0; const gl12 = [];
  for (const t in crowd.types) {
    const tp = crowd.types[t].tpl, nb = tp.boneNames.length; gap = Math.max(gap, tp.weightGap); gl12.push(t + ' ' + tp.gapLod.slice(1).map((x) => (x * 100).toFixed(1)).join('/'));
    for (const L of tp.lods) for (const pp of L.parts) { const w = pp.geo.attributes.skinWeight.array, ix = pp.geo.attributes.skinIndex.array;
      for (let i = 0; i < w.length; i += 4) { if (Math.abs(w[i] + w[i + 1] + w[i + 2] + w[i + 3] - 1) > 2e-3) bw++; for (let q = 0; q < 4; q++) if (w[i + q] > 0 && ix[i + q] >= nb) bi++; } }
  }
  add('C12_lod_weights', bw === 0 && bi === 0, `bad sums ${bw}, bad indices ${bi}, worst transfer distance ${(gap * 100).toFixed(1)} cm (LOD1/LOD2 cm: ${gl12.join(', ')})`);

  // C19 LOD1/LOD2 deform with LOD0: at the attack's middle frame, each LOD1/2 vertex stays as close to the posed LOD0 as it was at rest
  // (+3 cm at most); a vertex given the wrong bone leaves the body.
  const pose = (geo, d, nb, row) => { const P3 = geo.attributes.position, si = geo.attributes.skinIndex, sw = geo.attributes.skinWeight, out = new Float32Array(P3.count * 3), M = new THREE.Matrix4(), a = new THREE.Vector3(), t = new THREE.Vector3();
    for (let i = 0; i < P3.count; i++) { a.set(0, 0, 0); for (let q = 0; q < 4; q++) { const w = sw.getComponent(i, q); if (!w) continue; M.fromArray(d, (row * nb * 4 + si.getComponent(i, q) * 4) * 4); t.fromBufferAttribute(P3, i).applyMatrix4(M); a.addScaledVector(t, w); } a.toArray(out, i * 3); } return out; };
  const near = (p, i, L) => { let b = 1e9; for (let j = 0; j < L.length; j += 3) { const dx = L[j] - p[i], dy = L[j + 1] - p[i + 1], dz = L[j + 2] - p[i + 2], d = dx * dx + dy * dy + dz * dz; if (d < b) b = d; } return Math.sqrt(b); };
  let worst19 = 0, where19 = '';
  for (const t in crowd.types) {
    const T = crowd.types[t], tp = T.tpl, e = T.bake.table.attack, row = e.row0 + Math.floor(e.frames / 2), nb = T.bake.nb;
    const cat = (L, fn) => { const arrs = L.parts.map(fn); const n = arrs.reduce((s2, a2) => s2 + a2.length, 0), o2 = new Float32Array(n); let k2 = 0; for (const a2 of arrs) { o2.set(a2, k2); k2 += a2.length; } return o2; };
    const r0 = cat(tp.lods[0], (pp) => pp.geo.attributes.position.array), p0 = cat(tp.lods[0], (pp) => pose(pp.geo, T.bake.data, nb, row));
    for (let l = 1; l < tp.lods.length; l++) {
      const rk = cat(tp.lods[l], (pp) => pp.geo.attributes.position.array), pk = cat(tp.lods[l], (pp) => pose(pp.geo, T.bake.data, nb, row));
      for (let i = 0; i < rk.length; i += 3 * 3) { const dv = near(pk, i, p0) - near(rk, i, r0); if (dv > worst19) { worst19 = dv; where19 = t + ' LOD' + l; } }
    }
  }
  add('C19_lod_deform', worst19 <= 0.03, `worst extra distance from the posed LOD0 ${(worst19 * 100).toFixed(1)} cm (${where19}; attack mid frame, every 3rd vertex)`);

  // C13 suit outline: one hull per suit material per LOD level, shared skeleton, back faces, width 2 px x pixel ratio.
  let hullBad = 0;
  for (const u of RIGS) if (u.rig.tpl.kind === 'suit') for (const lvl of u.rig.lod.levels) {
    const ms = lvl.object.children, body = ms.filter((x) => x.material.name !== 'chrOutline'), hull = ms.filter((x) => x.material.name === 'chrOutline');
    if (hull.length !== body.length || hull.some((x) => x.skeleton !== body[0].skeleton || x.material.side !== THREE.BackSide)) hullBad++;
  }
  const om = CH.outlineMaterial(), px = r.getPixelRatio() * CH.CHR.outline.px;
  CH.setOutlineSize(innerWidth, innerHeight, r.getPixelRatio());
  const sh13 = { uniforms: {}, vertexShader: '#include <common>\n#include <project_vertex>' }; om.onBeforeCompile(sh13);
  const uOk = Math.abs(sh13.uniforms.uOPx.value - px) < 1e-6 && sh13.uniforms.uORes.value.x === innerWidth * r.getPixelRatio();
  add('C13_outline_hull', hullBad === 0 && uOk, `levels with a wrong hull set ${hullBad}, width uniform ok ${uOk} (want ${px} px)`);

  // C14 rest pose = bind pose in every file (the rig-space rebuild depends on it).
  const be = Math.max(...tpls.map((t) => t.bindErr));
  add('C14_bind_pose', be < 1e-3, 'max matrix difference ' + be.toExponential(2));

  // C15 memory flat over 5 spawn / despawn cycles (geometries, textures, programs equal after cycle 1 and 5; heap within 2 MB).
  const cyc = await P.cycles(5), c1 = cyc[0], c5 = cyc[4];
  add('C15_memory_flat', c1.geoms === c5.geoms && c1.texs === c5.texs && c1.programs === c5.programs && (c1.heapMB < 0 || c5.heapMB - c1.heapMB < 2), JSON.stringify(cyc.map((c) => [c.geoms, c.texs, c.programs, c.heapMB])));

  // C16 suit cloth colour comes from the file (the recolour round changes files, not code).
  let cb = 0;
  for (const u of RIGS) if (u.rig.tpl.kind === 'suit') for (const p2 of u.rig.parts) if (p2.mesh.material.name.startsWith('sCloth')) {
    const want = P.fileCloth[u.rig.tpl.id];
    if (!want || !p2.mesh.material.color.equals(want)) cb++;
  }
  add('C16_cloth_from_file', cb === 0, 'cloth materials not matching the file colour: ' + cb);

  // C17 0 new shader programs in play after the warm-up draw (all rigs, LODs and batches drawn once under the card).
  add('C17_programs_in_play', r.info.programs.length === P.progWarm, `programs after warm-up ${P.progWarm}, now ${r.info.programs.length}`);

  // C18 statue (dormant giant): plain meshes, no skeleton, matrices frozen.
  const stt = CH.makeStatue(GI[5], 'dormant', 0); stt.place(0, 0, -40, 0, 1); let sk18 = 0, auto = 0; stt.root.traverse((o) => { if (o.isSkinnedMesh) sk18++; if (o.isMesh && o.matrixAutoUpdate) auto++; });
  add('C18_statue_static', sk18 === 0 && auto === 0 && stt.meshes.length > 0, `skinned ${sk18}, auto-matrix meshes ${auto}, meshes ${stt.meshes.length}`);
  return out;
}
