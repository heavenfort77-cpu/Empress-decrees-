// PREP-PAL checks P1-P20 (CI only): run inside ci_pal/pal.html?mode=checks on the game's full palace plan. Each check returns
// { id, ok, line }; a check that measured nothing fails (lead rule 25 Nov). Mutants (ci_pal/palrun.mjs) must make their named check fail.
import * as THREE from 'three';
export async function run(P, X) {
  const W = (id) => !X.only || X.only.split(',').includes(id);
  const out = [], ok = (id, pass, line) => out.push({ id, ok: !!pass, line: (pass ? 'PASS ' : 'FAIL ') + id + ' ' + line });
  const { L, PA, r, scene } = P, C = PA.PAL_ART;
  let kit = P.kit, arts = P.arts;
  const v = new THREE.Vector3(), box = new THREE.Box3();
  const pieceOf = (im) => { for (const n in kit.pieces) for (const p of kit.pieces[n].parts) if (p.geo === im.geometry) return n; return null; };
  const instOf = (a, piece) => a.inst.filter((im) => pieceOf(im) === piece);
  const posOf = (im, i, M = new THREE.Matrix4()) => { im.getMatrixAt(i, M); const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3(); M.decompose(p, q, s); return { p, q, s }; };

  // P1 load: every GLB and every texture this module asks for loaded (KTX2 or the manifest's PNG), kit reports nothing missing.
  if (W('P1')) { const names = PA.textureNames(), bad = names.filter((n) => !P.TEX[n]), ktx = names.filter((n) => P.HOW[n] === 'ktx2').length;
    ok('P1', !P.FILEERR.length && !bad.length && !kit.missing.length && names.length > 0 && Object.keys(P.GL).length === PA.files('').length,
      `files ${Object.keys(P.GL).length}/${PA.files('').length} failed [${P.FILEERR}] textures ${names.length - bad.length}/${names.length} (ktx2 ${ktx}) missing [${bad} ${kit.missing}] load ${Math.round(P.loadMs)} ms build ${Math.round(P.buildMs)} ms`); }
  // P2 material table: every material name in the GLBs has a CONFIG entry (MATS or PROP_MATS), so none falls back to a stand-in.
  if (W('P2')) { const seen = new Set(); for (const k in P.GL) P.GL[k].scene.traverse((o) => { if (o.isMesh) seen.add(o.material.name); });
    const miss = [...seen].filter((n) => !C.MATS[n] && !C.PROP_MATS[n]);
    ok('P2', seen.size > 0 && !miss.length, `${seen.size} material names, without a table entry: [${miss}]`); }
  // P3 LOD levels sit on LOD0 (the 17a spread undone): centre within 0.5 m in x and z, floor within 0.1 m, every prop has 3 levels.
  if (W('P3')) { const bad = []; let n = 0;
    for (const k in kit.props) { const Pp = kit.props[k], b0 = new THREE.Box3(); for (const p of Pp.levels[0]) b0.union(p.geo.boundingBox);
      for (let i = 1; i < Pp.levels.length; i++) { const b = new THREE.Box3(); for (const p of Pp.levels[i]) b.union(p.geo.boundingBox); n++;
        const dx = (b.min.x + b.max.x - b0.min.x - b0.max.x) / 2, dz = (b.min.z + b.max.z - b0.min.z - b0.max.z) / 2;
        if (Math.abs(dx) > 0.5 || Math.abs(dz) > 0.5 || Math.abs(b.min.y - b0.min.y) > 0.1) bad.push(`${k}:${i} dx ${dx.toFixed(2)} dz ${dz.toFixed(2)}`); }
      if (Pp.levels.length !== 3) bad.push(`${k} levels ${Pp.levels.length}`); }
    ok('P3', n > 0 && !bad.length, `${n} LOD levels checked; off [${bad.join('; ')}]`); }
  // P4 frozen matrices and culling: every object under every art group and door has matrixAutoUpdate false and frustumCulled true.
  if (W('P4')) { let n = 0; const bad = [];
    const chk = (root) => root.traverse((o) => { n++; if (o.matrixAutoUpdate || o.frustumCulled === false) bad.push(o.name || o.type); });
    for (const a of arts) chk(a.group); for (const d of L.doors) if (d.art) chk(d.art.root);
    ok('P4', n > 0 && !bad.length, `${n} objects; auto-updating or unculled: ${bad.length} [${bad.slice(0, 5)}]`); }
  // P5 walls on the collision: per room and side, rendered wall length = the box walls' length (0.02 m), every wall instance's centre line
  // sits wallT / 2 inside the edge (0.02 m) and lies within a box wall's span.
  if (W('P5')) { let n = 0; const bad = [];
    for (const a of arts) { const rm = a.room, wallPieces = new Set([C.walls[rm.type], C.walls.low, C.walls.bridge]);
      const sideOfSolid = (s) => (s.z0 === rm.z0 ? 'n' : s.z1 === rm.z1 ? 's' : s.x0 === rm.x0 ? 'w' : s.x1 === rm.x1 ? 'e' : '');
      const want = { n: 0, s: 0, w: 0, e: 0 }, got = { n: 0, s: 0, w: 0, e: 0 }, spans = { n: [], s: [], w: [], e: [] };
      for (const s of rm.solids) if (s.kind === 'wall') { const sd = sideOfSolid(s); const len = sd === 'n' || sd === 's' ? s.x1 - s.x0 : s.z1 - s.z0;
        const longX = rm.x1 - rm.x0 >= rm.z1 - rm.z0;
        if (rm.type === 'bridge' && ((longX && (sd === 'n' || sd === 's')) || (!longX && (sd === 'w' || sd === 'e')))) continue;
        want[sd] += len; spans[sd].push(sd === 'n' || sd === 's' ? [s.x0, s.x1] : [s.z0, s.z1]); }
      const seen = new Set();
      for (const im of a.inst) { const pc = pieceOf(im); if (!wallPieces.has(pc) || seen.has(pc + im.count)) continue; seen.add(pc + im.count);
        for (let i = 0; i < im.count; i++) { const { p, q, s } = posOf(im, i), ax = new THREE.Vector3(1, 0, 0).applyQuaternion(q);
          const len = 4 * s.x, mid = p.clone().addScaledVector(ax, len / 2); n++;
          const sd = Math.abs(ax.x) > 0.5 ? (Math.abs(mid.z - rm.z0) < 1 ? 'n' : 's') : (Math.abs(mid.x - rm.x0) < 1 ? 'w' : 'e');
          got[sd] += len; const off = sd === 'n' ? mid.z - rm.z0 : sd === 's' ? rm.z1 - mid.z : sd === 'w' ? mid.x - rm.x0 : rm.x1 - mid.x;
          if (Math.abs(off - L.wallT / 2) > 0.02) bad.push(`${rm.id}:${sd} centre ${off.toFixed(2)} m in`);
          const u = sd === 'n' || sd === 's' ? mid.x : mid.z;
          if (!spans[sd].some(([a0, a1]) => u > a0 - 0.01 && u < a1 + 0.01)) bad.push(`${rm.id}:${sd} wall at ${u.toFixed(1)} outside the box walls`); } }
      for (const sd of ['n', 's', 'w', 'e']) if (Math.abs(want[sd] - got[sd]) > 0.02 * Math.max(1, spans[sd].length)) bad.push(`${rm.id}:${sd} length ${got[sd].toFixed(2)} vs box ${want[sd].toFixed(2)}`); }
    ok('P5', n > 0 && !bad.length, `${n} wall segments; off [${bad.slice(0, 6).join('; ')}]${bad.length > 6 ? ' +' + (bad.length - 6) : ''}`); }
  // P6 pillars on the pillar boxes' centres (0.01 m) and the throne on the dais block's centre.
  if (W('P6')) { let n = 0; const bad = [];
    for (const a of arts) { const want = a.room.pillars.map(([x, z]) => x + ',' + z); const ims = instOf(a, 'pillar');
      const got = new Set(); if (ims[0]) for (let i = 0; i < ims[0].count; i++) { const { p } = posOf(ims[0], i); got.add(Math.round(p.x * 100) / 100 + ',' + Math.round(p.z * 100) / 100); n++; }
      for (const w of want) if (!got.has(w)) bad.push(a.room.id + ' pillar ' + w);
      if (got.size !== want.length) bad.push(`${a.room.id} pillars ${got.size} vs ${want.length}`);
      if (a.room.dais) { const th = a.props.find((p) => p.kind === 'arch/throne_dais'); n++;
        if (!th || Math.abs(th.root.position.x - a.room.dais[0]) > 0.01 || Math.abs(th.root.position.z - a.room.dais[1]) > 0.01) bad.push('throne off the dais'); } }
    ok('P6', n > 0 && !bad.length, `${n} pillar and throne placements; off [${bad.slice(0, 5)}]`); }
  // P7 budget: every room with all its neighbours attached (all doors open, the game shows at most one or two), the game's camera, the
  // frame that redraws the shadow map (worst case), counted at the GL calls: draws < 500 and triangles < 0.5M, on this tier.
  if (W('P7')) { const H = X.heaviest(), b = H.best, t = H.byTris;
    ok('P7', H.rows.length === L.rooms.length && b.calls > 0 && b.calls < 500 && t.tris < 500000,
      `tier ${X.TIER}: worst draws ${b.calls} (${b.id}; three main pass ${b.mainCalls}), worst triangles ${t.tris} (${t.id}); ${H.rows.length} views`);
    out.push({ id: 'P7rows', ok: true, line: 'INFO P7 views ' + H.rows.map((x) => `${x.id}:${x.calls}/${Math.round(x.tris / 1000)}k`).join(' '), info: true }); }
  // P8 no lights: the art adds no light anywhere (lamps are emissive cards).
  if (W('P8')) { let lights = 0, n = 0; for (const a of arts) a.group.traverse((o) => { n++; if (o.isLight) lights++; }); for (const d of L.doors) if (d.art) d.art.root.traverse((o) => { if (o.isLight) lights++; });
    ok('P8', n > 0 && lights === 0, `${lights} lights in ${n} art objects`); }
  // P9 textures: every kit texture is at most 1024 px and anisotropy at most 4; image textures are GPU-compressed (KTX2) unless the
  // manifest ships a PNG (counted).
  if (W('P9')) { const bad = []; let comp = 0, n = 0;
    for (const t of kit.texList) { n++; const im = t.image || {}, w = im.width || (t.mipmaps && t.mipmaps[0] && t.mipmaps[0].width) || 0;
      if (w > 1024) bad.push('size ' + w); if (t.anisotropy > 4) bad.push('aniso ' + t.anisotropy); if (t.isCompressedTexture) comp++; }
    ok('P9', n > 0 && !bad.length, `${n} textures (${comp} compressed); over the limits [${bad.slice(0, 5)}]`); }
  // P10 fog of war on instanced pieces: an instanced piece 60 m from the fog centre is dimmed (its instance position is used), and the
  // same piece at the fog centre is not; also the matcap mercury compiles with the hook (pixel read, one frame each).
  if (W('P10')) { const rt = new THREE.WebGLRenderTarget(64, 64), sc2 = new THREE.Scene(); sc2.add(new THREE.HemisphereLight(0xffffff, 0xffffff, 3));
    const cam2 = new THREE.OrthographicCamera(-2, 2, 2, -2, 0.1, 50), im = new THREE.InstancedMesh(new THREE.PlaneGeometry(3, 3), kit.mats.palWall, 1);
    im.setMatrixAt(0, new THREE.Matrix4().makeTranslation(60, 0, 0)); im.computeBoundingSphere(); im.frustumCulled = true; sc2.add(im);
    cam2.position.set(60, 0, 10); cam2.lookAt(60, 0, 0); cam2.updateMatrixWorld();
    const read = () => { r.setRenderTarget(rt); r.render(sc2, cam2); const px = new Uint8Array(4); r.readRenderTargetPixels(rt, 32, 32, 1, 1, px); r.setRenderTarget(null); return px[0] + px[1] + px[2]; };
    const old = P.FOW.uFowC.value.clone(), oldR = P.FOW.uFowR.value; P.FOW.uFowR.value = 10;
    P.FOW.uFowC.value.set(0, 0, 0); const far = read(); P.FOW.uFowC.value.set(60, 0, 0); const near = read();
    im.material = kit.merc.idle; P.FOW.uFowC.value.set(0, 0, 0); const mfar = read(); P.FOW.uFowC.value.set(60, 0, 0); const mnear = read();
    P.FOW.uFowC.value.copy(old); P.FOW.uFowR.value = oldR; im.geometry.dispose(); im.dispose(); rt.dispose();
    ok('P10', near > 0 && far < near * 0.6 && mnear > 0 && mfar < mnear * 0.6, `instanced plaster at fog centre ${near}, 60 m out ${far}; mercury ${mnear} / ${mfar} (dim must be < 0.6 x)`); }
  // P11 0 programs in play: warm (rack plus every state) under the card, then every state of every prop, door and burnt swap drawn in the
  // heaviest view: no program is linked after the warm draw.
  if (W('P11')) { const H = X.heaviest(); const rm = L.byId[H.best.id]; X.attachView(rm, true);
    PA.warmOn(kit, scene, P.cam, arts); r.compile(scene, P.cam); X.frame(true); PA.warmOff(kit, scene, arts); X.frame(true);
    const l0 = window.__gl.link, p0 = r.info.programs.length; let frames = 0;
    for (let k = 0; k < 6; k++) {
      for (const a of arts) { PA.setBurnt(a, k % 2 === 1); for (const p of a.props) { if (p.kind === 'vat') PA.setVat(p, k % 3); else if (p.kind === 'ding') PA.setDing(p, k % 2 === 0);
        else if (p.kind === 'clock') PA.setClock(p, k / 5); else if (p.kind === 'beast') PA.setBeast(p, k % 2 === 1); else if (p.kind === 'merc') PA.setMerc(kit, p, ['idle', 'warn', 'hot'][k % 3]); } }
      for (const d of L.doors) if (d.art) PA.setDoor(d.art, k % 2 === 1, k % 3 === 2);
      for (const rr of [rm, ...L.rooms.filter((x) => x.type !== rm.type).slice(0, 6)]) { X.attachView(rr, true); X.frame(true); X.frame(false); frames += 2; }
    }
    for (const a of arts) PA.resetRoom(a);
    const links = window.__gl.link - l0;
    ok('P11', frames > 0 && p0 > 0 && links === 0 && r.info.programs.length === p0, `programs after warm ${p0}, links in play ${links}, programs now ${r.info.programs.length}, ${frames} play frames`); }
  // P12 states and reset: burnt swaps every listed surface and back; vat 0/1/2 shows body+water / +cracks / shards+puddle; 鼎 lit/dry; beast
  // windup; doors; resetRoom returns every one to rest (material identity and visibility).
  if (W('P12')) { const bad = []; let n = 0;
    for (const a of arts) {
      PA.setBurnt(a, true); for (let i = 0; i < a.burn.length; i += 3) { n++; if (a.burn[i].material !== a.burn[i + 2]) bad.push(a.room.id + ' burn'); }
      for (const p of a.props) {
        if (p.kind === 'vat') { PA.setVat(p, 1); n++; if (!p.states.vat_cracks.visible || !p.lod.visible) bad.push('vat 1'); PA.setVat(p, 2); if (p.lod.visible || !p.states.vat_shards.visible || !p.states.vat_puddle.visible) bad.push('vat 2'); }
        if (p.kind === 'ding') { PA.setDing(p, false); n++; if (p.states.ding_lit.visible || !p.states.ding_dry.visible) bad.push('ding dry'); }
        if (p.kind === 'beast') { PA.setBeast(p, true); n++; if (!p.windup.visible || p.idle.visible) bad.push('beast windup'); }
        if (p.kind === 'merc') { PA.setMerc(kit, p, 'hot'); n++; if (p.surface.material !== kit.merc.hot) bad.push('merc hot'); }
      }
      for (const d of a.doors) { PA.setDoor(d, true, true); n++; if (d.leaves.visible || !d.bar.visible) bad.push('door'); }
      PA.resetRoom(a);
      for (let i = 0; i < a.burn.length; i += 3) if (a.burn[i].material !== a.burn[i + 1]) bad.push(a.room.id + ' reset burn');
      for (const p of a.props) {
        if (p.kind === 'vat' && (!p.lod.visible || p.states.vat_cracks.visible || p.states.vat_shards.visible || !p.states.vat_water.visible)) bad.push('reset vat');
        if (p.kind === 'ding' && (!p.states.ding_lit.visible || p.states.ding_dry.visible)) bad.push('reset ding');
        if (p.kind === 'beast' && (p.windup.visible || !p.idle.visible)) bad.push('reset beast');
        if (p.kind === 'merc' && p.surface.material !== kit.merc.idle) bad.push('reset merc');
      }
      for (const d of a.doors) if (!d.leaves.visible || d.bar.visible) bad.push('reset door');
    }
    ok('P12', n > 0 && !bad.length, `${n} state changes; wrong [${[...new Set(bad)].slice(0, 6)}]`); }
  // P13 water clock: full (level 1) shows the water higher than empty (level 0); the matrix is written only when the step changes.
  if (W('P13')) { const cl = []; for (const a of arts) for (const p of a.props) if (p.kind === 'clock') cl.push(p); const bad = [];
    for (const p of cl) { const w = p.moving.find((g, i) => i % 2 === 0 && g.name === 'clock_water');
      if (!w) { bad.push('no clock_water'); continue; }
      const top = () => { p.root.updateMatrixWorld(true); box.setFromObject(w); return box.max.y; };
      PA.setClock(p, 1); const full = top(); PA.setClock(p, 0); const empty = top(); const s0 = p.step; PA.setClock(p, 0.001); const same = p.step === s0;
      if (!(full > empty + 0.05) || !same) bad.push(`full ${full.toFixed(2)} empty ${empty.toFixed(2)} same-step ${same}`); PA.setClock(p, 1); }
    ok('P13', cl.length > 0 && !bad.length, `${cl.length} clocks; wrong [${bad.slice(0, 3)}]`); }
  // P14 memory flat: build and dispose twice; live GL buffers, textures and programs, and renderer.info geometries and textures, equal after
  // each build and back to the pre-build values after each dispose (the art drawn between).
  if (W('P14')) { const rec = () => { const g = window.__gl; return { buf: g.buf, tex: g.tex, prog: g.prog, geo: r.info.memory.geometries, itex: r.info.memory.textures, progs: r.info.programs.length }; };
    const draw = () => { for (const rm of L.rooms) { X.attachView(rm, true); X.frame(true); } };
    for (const a of arts) { scene.remove(a.group); } P.teardown(); X.frame(false); X.frame(false);
    const base = rec(); const cyc = [];
    for (let c = 0; c < 2; c++) { P.build(); kit = P.kit; arts = P.arts; draw(); const b = rec(); P.teardown(); X.frame(false); X.frame(false); const d = rec(); cyc.push({ b, d }); }
    P.build(); kit = P.kit; arts = P.arts;
    const eq = (p, q) => p.buf === q.buf && p.tex === q.tex && p.geo === q.geo && p.itex === q.itex;
    const pass = eq(cyc[0].b, cyc[1].b) && eq(cyc[0].d, base) && eq(cyc[1].d, base) && cyc[0].b.geo > base.geo && cyc[0].d.progs === cyc[1].d.progs;
    ok('P14', pass, `base ${JSON.stringify(base)} built ${JSON.stringify(cyc[0].b)} / ${JSON.stringify(cyc[1].b)} disposed ${JSON.stringify(cyc[0].d)} / ${JSON.stringify(cyc[1].d)}`); }
  // P15 shadows: cards, small props (< shadowMinH), tile ends, bundles, plants, flags and terraces cast none; walls and pillars do.
  if (W('P15')) { const bad = []; let n = 0, casters = 0;
    for (const a of arts) { for (const im of a.inst) { n++; const pc = pieceOf(im) || 'inlay'; const no = C.noShadow.some((s) => pc.startsWith(s)) || pc === 'inlay'; if (im.castShadow && no) bad.push(pc); if (im.castShadow) casters++; }
      for (const p of a.props) { const kp = kit.props[p.kind]; p.root.traverse((o) => { if (!o.isMesh) return; n++; const card = o.material.transparent || o.material.alphaTest > 0 || o.material.isMeshBasicMaterial;
        if (o.castShadow && (card || (kp && kp.h < C.shadowMinH))) bad.push(p.kind + ':' + (o.material.name || o.material.type)); if (o.castShadow) casters++; }); } }
    ok('P15', n > 0 && casters > 0 && !bad.length, `${n} meshes, ${casters} casters; wrong casters [${[...new Set(bad)].slice(0, 5)}]`); }
  // P16 new props' solids: every rack, lamp, bell stand and standard has a solid; solids lie inside their room and overlap no game solid.
  if (W('P16')) { const bad = []; let n = 0;
    for (const a of arts) { const rm = a.room;
      for (const s of a.solids) { n++; if (s.x0 < rm.x0 || s.x1 > rm.x1 || s.z0 < rm.z0 || s.z1 > rm.z1) bad.push(rm.id + ' outside');
        for (const o of rm.solids) if (s.x0 < o.x1 && s.x1 > o.x0 && s.z0 < o.z1 && s.z1 > o.z0) bad.push(`${rm.id} overlaps ${o.kind}`); }
      const racks = instOf(a, 'slip_rack')[0], nr = racks ? racks.count : 0, np = a.props.filter((p) => p.kind === 'lamp' || p.kind === 'bells' || p.kind === 'standard').length;
      if (a.solids.length !== nr + np) bad.push(`${rm.id} solids ${a.solids.length} vs racks ${nr} + props ${np}`); }
    ok('P16', n > 0 && !bad.length, `${n} new solids; wrong [${[...new Set(bad)].slice(0, 5)}]`); }
  // P17 terraces only on lake-facing edges: each terrace segment's outside midpoint is in no room.
  if (W('P17')) { const bad = []; let n = 0;
    for (const a of arts) for (const im of instOf(a, 'terrace_edge').slice(0, 1)) for (let i = 0; i < im.count; i++) { n++;
      const { p, q, s } = posOf(im, i), mid = p.clone().addScaledVector(new THREE.Vector3(1, 0, 0).applyQuaternion(q), 2 * s.x).addScaledVector(new THREE.Vector3(0, 0, -1).applyQuaternion(q), 0.3);
      const inRoom = L.rooms.find((o) => mid.x > o.x0 && mid.x < o.x1 && mid.z > o.z0 && mid.z < o.z1); if (inRoom) bad.push(`${a.room.id} into ${inRoom.id}`); }
    ok('P17', n > 0 && !bad.length, `${n} terrace segments; under a room [${bad.slice(0, 4)}]`); }
  // P18 replaced box keys exist in index.html's box build for that room type (FMAT floors, palWall, palPillar, the core's 'pillar' and 'gold').
  if (W('P18')) { const fm = /const FMAT = (\{[^}]*\})/.exec(X.html), FM = fm ? Function('return ' + fm[1])() : {}, bad = []; let n = 0;
    const known = { hall: ['palWall', 'palPillar', 'stone', 'spawn'], court: ['palWall', 'stone'], corridor: ['palWall'], garden: ['palWall', 'pillar', 'silk', 'wall'], bridge: ['palWall'], core: ['palWall', 'palPillar', 'pillar', 'gold'] };
    for (const t in C.replaces) for (const k of C.replaces[t]) { n++; const keys = [...(known[t] || []), 'floor:' + FM[t]]; if (!keys.includes(k)) bad.push(t + ':' + k); }
    ok('P18', fm && n > 0 && !bad.length, `${n} replaced keys; unknown [${bad}]`); }
  // P19 instancing: repeats are instanced (no room has more than 40 plain meshes outside props), instanced geometry is shared with the kit.
  if (W('P19')) { const bad = []; let n = 0, shared = 0;
    for (const a of arts) { let plain = 0; for (const o of a.group.children) if (o.isMesh && !o.isInstancedMesh) plain++; if (plain > 40) bad.push(a.room.id + ' ' + plain);
      for (const im of a.inst) { n++; if (pieceOf(im) || im.material === kit.mats.palStarInlay) shared++; } }
    ok('P19', n > 0 && shared === n && !bad.length, `${n} instanced meshes, ${shared} on kit geometry; rooms with many plain meshes [${bad}]`); }
  // P20 mercury channels cover the game's channel boxes (surface box within 0.15 m of the channel's x/z extent).
  if (W('P20')) { const bad = []; let n = 0;
    for (const a of arts) { const ms = a.room.pieces.filter((p) => p.type === 'mercury'), hs = a.props.filter((p) => p.kind === 'merc');
      if (ms.length !== hs.length) bad.push(`${a.room.id} ${hs.length} vs ${ms.length}`);
      ms.forEach((m, i) => { const h = hs[i]; if (!h) return; n++; h.root.updateMatrixWorld(true); box.setFromObject(h.surface);
        const ex = [box.min.x - (m.x - m.sx / 2), box.max.x - (m.x + m.sx / 2), box.min.z - (m.z - m.sz / 2), box.max.z - (m.z + m.sz / 2)];
        if (ex.some((e) => Math.abs(e) > 0.15)) bad.push(`${a.room.id} ${ex.map((e) => e.toFixed(2))}`); }); }
    ok('P20', n > 0 && !bad.length, `${n} channels; off [${bad.slice(0, 4)}]`); }
  return out;
}
