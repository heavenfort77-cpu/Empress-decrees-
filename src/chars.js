// Empress Decrees: character models (batches 17f-17h; PREP-CHR drop-in for INT, plan docs/INTEGRATION.md sections 7 and 9, hooks docs/HOOKS-17fgh.md).
// Render only: gameplay (positions, facing, timers, hits) stays in index.html; collision stays on the simple shapes (rule 42).
// Two routes, both measured on the real-GPU runner (docs/HOOKS-17fgh.md, run numbers there):
//   - Crowd (皇家 guard x5, 反贼 rebels x4): clips baked once at load into one bone-matrix float texture per type; every LOD level drawn
//     by one InstancedMesh per type x LOD x material (per-instance clip, start time, rate, tread offset, colour). 17a run 45514003926.
//   - Rigs (nine suits, Tiger Demon, Stalker, Howler, twelve giants): one Skeleton per unit shared by every part and LOD level (the loader
//     gives one per glTF node: 3-10 per unit, each uploading a bone texture per frame); THREE.LOD; animated only when on screen and near.
// Every geometry is rebuilt once at load in rig space (metres, float), so quantised (KHR_mesh_quantization) and source GLBs build the same.
// Files are loaded by name (CHR.files); colours come from the files (suit cloth = the GLB material colour), never baked in here.

// ===== MAP =====
// CONFIG    CHR (all tunables; comment line above each)
// FILES     charFiles(base)
// GEOMETRY  nodeName(), lodOf(), rigSpaceGeo(), mergeGeos(), transferWeights(), fitSphere()
// TEMPLATE  makeTemplate(gltf, opts): rig-space parts per LOD and material, one bone list, clips starting at 0 s
// MATERIALS charMaterials(tex): the name table (brass sheet, apex glow, suit cloth and faces from the file; unknown names stop the load),
//           .dispose(); chainCompile(); disposeTemplate()
// OUTLINE   outlineMaterial(), setOutlineSize(w, h, pr)   suits: 2 px inverted hull, one extra draw per suit material
// RIGS      spawnRig(tpl, opts) -> rig: place(), show(), hide(), play(), setRun(), setState(), setFace(), addTread(), update() [PERFRAME]; lodHold()
// STATUE    makeStatue(tpl, clip, t): a skinned pose frozen into static meshes (dormant giants)
// CROWD     makeCrowd(tpls, opts) -> crowd: makeState(), setClip(), setTime(), begin(), put(), end() [PERFRAME]
// HIT       HIT.dist(), HIT.line(), HIT.sector() [PERFRAME]; sectorGeometry(R, deg)
// FRAME     beginFrame(camera) [PERFRAME]; stats()
import * as THREE from 'three';

// ===== CONFIG =====
export const CHR = {
  // Switch: character models on (false = the game keeps its box shapes; INT wires both paths behind this until 17f-17h pass).
  on: true,
  // Model files by kind, relative to the model folder INT loads from ('assets/c/models/' when encoded, else 'assets/models/'); {id} = file id.
  files: { suit: 'suits/{id}.glb', guard: 'guard/{id}.glb', rebel: 'rebels/{id}.glb', tiger: 'apex/tiger.glb', stalker: 'apex/stalker.glb', howler: 'apex/howler.glb', giants: 'giants/giants.glb' },
  // Suit clip facts per suit (floor_y, run_v), produced by the SUITANIM builder; loaded with the models.
  suitInfo: 'art/suits/anim/suits_info.json',
  // Suit file id per school key (CONFIG.SCHOOLS order).
  suitIds: { ru: 'ru', dao: 'dao', fa: 'fa', mo: 'mo', yinyang: 'yy', za: 'za', ming: 'ming', zongheng: 'zh', nong: 'nong' },
  // 皇家 guard unit types (files guard/{id}.glb).
  guardTypes: ['zu', 'nu', 'dun', 'che', 'wz'],
  // 反贼 rebel unit types (files rebels/{id}.glb).
  rebelTypes: ['ls', 'fs', 'ss', 'qs'],
  // LOD switch distances, m: [LOD0 -> LOD1, LOD1 -> LOD2]. Lens FOV 50 at 1080p: px = height x 1158 / d; LOD0 while over ~200 px tall,
  // LOD2 under ~70 px (INTEGRATION section 6 targets: suit 2.4 m, guard 1.8-2.7 m, giant 5 m; tiger 2.5 m tall, cubs 1-1.8 m).
  lod: { suit: [14, 40], guard: [10, 30], tiger: [14, 40], cub: [8, 24], giant: [29, 83], neutral: [40, 90] },
  // LOD hysteresis: a level holds until the distance passes its switch point by this share (no flicker at the edge).
  lodHyst: 0.1,
  // Phone: every LOD distance x this (INTEGRATION section 6).
  phoneK: 0.6,
  // Model front: the GLBs face +Z (Blender -Y forward); yaw = atan2(fx, fz) from the game's facing.
  // Animation: units within nearM of the camera animate every frame; farther ones step at farHz; units off screen do not animate.
  anim: { nearM: 30, farHz: 10, fade: 0.12 },
  // Suits switch from idle to run above this ground speed, m/s; run timeScale = speed / run_v (art/suits/anim/suits_info.json).
  runMin: 0.3,
  // Clips that loop (others play once and hold, or return to the loop for hit and attack).
  loops: ['idle', 'run', 'move', 'walk', 'carry', 'dormant'],
  // Crowd bake rate, frames per second (clips are keyed at 60).
  bakeFps: 60,
  // Bounding spheres: bind-pose sphere radius x sphereK (attacks and falls reach past the rest pose). Never frustumCulled = false.
  sphereK: 1.6,
  // Crowd batches: the culling sphere is the instances' centres plus this many metres (unit size plus animation reach).
  crowdPad: 3,
  // Crowd hit flash colour (instance colour multiplies the material colour; brighter than white).
  flash: [2.5, 2.5, 2.5],
  // Rebel patch colours (FIX-A rebel_build.py PATCH_COL: olive, umber, madder; never a school colour); patch i wears [i % 3].
  patch: [0x6f6a34, 0x6a4a32, 0x8e5a52],
  // Suit outline (owner pick 25 Nov 02:1x: 2 px on screen, renderer-side): inverted hull, one extra draw per suit material.
  outline: { on: true, px: 2, color: 0x0b0908 },
  // Suit cloth colour by suit id (owner 25 Nov 14:08 colour option A, art/Colour-Clarity-Study.md section 8): sRGB. A suit not listed keeps the
  // colour in its file (道 keeps its gold, section 9; 阴阳 keeps its near black).
  clothTint: { fa: 0xefe9dc, ru: 0xc88c3e, mo: 0xe66044, za: 0xdfe6f2, ming: 0x9c7ae0, zh: 0x22754a, nong: 0x5a92e4 },
  // Rebel cloth tint (same decision): sRGB multiplier on the fodder sheet.
  rebelCloth: 0x8c7860,
  // Faces (owner picking A-D, 25 Nov): suit materials named with this prefix (fcBrass, fcFace in the face samples run 45533099431).
  // No face is chosen here: the suit file carries the face and its material is built from the file's own values, unless INT sets
  // mat = (name, srcMaterial, tex, state) -> Material before charMaterials builds; Rig.setFace(material) swaps it on a spawned rig.
  face: { prefix: 'fc', mat: null },
  // Characters cast shadows (false = as today: blob shadows only; the shadow map is not re-rendered per frame).
  shadows: false,
  // Tread belts (ASSET-LIST H, FIX-A run 45471050221): metres of travel per texture repeat; map.offset.x += metres / mpr.
  tread: { stalker: 0.554, howler: 0.477, zu: 0.54, nu: 0.54, dun: 0.54, che: 0.527, wz: 0.594 },
  // Hit shapes fitted to the models (owner 25 Nov 02:2x: "hit areas fitted to the new models (tiger, cubs)"): capsules along the facing.
  // r = radius m, half = half the axis length m (capsule length = 2 x (half + r)), off = axis centre ahead of the unit position, m.
  // Measured on the LOD0 bind pose (assets/models/apex, docs/HOOKS-17fgh.md): tiger body 1.52 x 6.07 m incl. the tail; the body without
  // the tail 1.5 x 4.9 m (INTEGRATION section 7) -> r 0.75, half 1.7, centre 0.26 m ahead. Stalker 1.18 x 1.93 m -> r 0.59 (half its
  // width, treads included; INTEGRATION's 0.45 left the treads outside), half 0.375; Howler 0.98 x 1.68 m -> r 0.49, half 0.351.
  hit: { tiger: { r: 0.75, half: 1.7, off: 0.26 }, stalker: { r: 0.59, half: 0.375, off: 0.025 }, howler: { r: 0.49, half: 0.351, off: 0.159 } },
  // Giant sweep (owner 25 Nov ~07:5x: "2.5 m radius over 120 degrees in front of the giant"): sector radius m and full angle degrees.
  sweep: { r: 2.5, deg: 120 },
  // Apex glow (owner 25 Nov 02:2x "apex glow water-blue"): model crack and organ emissive (art/viewer/apex_mat.js WATER, approved route);
  // effects (tells, painted cards) use apexFx, the brighter cyan-leaning water-blue of docs/VFX.md.
  apexGlow: 0x3a8fd0, apexFx: 0x2ea8e8,
  // Crack and organ glow intensities (apex_mat.js round 2: no neon), bronze brass surface (owner 02:1x: brass sheet for every bronze piece).
  apexCrackGlow: 0.3, apexOrganGlow: 0.8, brass: { metalness: 0.25, roughness: 0.5, gain: 1.3 },
};

// ===== FILES =====
// Every model file INT fetches for the characters: [{ key, url }]; base = model folder with a trailing slash.
export function charFiles(base) {
  const F = CHR.files, out = [];
  for (const k in CHR.suitIds) out.push({ key: 'suit_' + CHR.suitIds[k], url: base + F.suit.replace('{id}', CHR.suitIds[k]) });
  for (const t of CHR.guardTypes) out.push({ key: t, url: base + F.guard.replace('{id}', t) });
  for (const t of CHR.rebelTypes) out.push({ key: t, url: base + F.rebel.replace('{id}', t) });
  for (const k of ['tiger', 'stalker', 'howler', 'giants']) out.push({ key: k, url: base + F[k] });
  return out;
}

// ===== GEOMETRY (load time only) =====
const I4 = new THREE.Matrix4();
// glTF node name of a mesh: a multi-primitive node loads as a Group named after the node holding meshes named node_1, node_2 ...
export function nodeName(o) {
  const p = o.parent;
  return p && !p.isBone && p.name && o.name.startsWith(p.name + '_') && /_\d+$/.test(o.name) ? p.name : o.name;
}
export function lodOf(name) { return /_lod2$/.test(name) ? 2 : /_lod1$/.test(name) ? 1 : 0; }
function boneAncestor(o) { let p = o.parent; while (p && !p.isBone) p = p.parent; return p; }
// A float, rig-space copy of a primitive: positions and normals through X; skin indices remapped to the template bone list.
function rigSpaceGeo(src, X, remap, rigid) {
  const pa = src.attributes.position, na = src.attributes.normal, ua = src.attributes.uv, n = pa.count;
  const pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), uv = new Float32Array(n * 2), si = new Uint16Array(n * 4), sw = new Float32Array(n * 4);
  const nm = new THREE.Matrix3().getNormalMatrix(X), v = new THREE.Vector3();
  const ja = src.attributes.skinIndex, wa = src.attributes.skinWeight;
  for (let i = 0; i < n; i++) {
    v.fromBufferAttribute(pa, i).applyMatrix4(X); pos[i * 3] = v.x; pos[i * 3 + 1] = v.y; pos[i * 3 + 2] = v.z;
    if (na) { v.fromBufferAttribute(na, i).applyMatrix3(nm).normalize(); nor[i * 3] = v.x; nor[i * 3 + 1] = v.y; nor[i * 3 + 2] = v.z; }
    if (ua) { uv[i * 2] = ua.getX(i); uv[i * 2 + 1] = ua.getY(i); }
    if (rigid >= 0) { si[i * 4] = rigid; sw[i * 4] = 1; continue; }
    if (!ja) continue;
    for (let k = 0; k < 4; k++) { si[i * 4 + k] = remap[ja.getComponent(i, k)]; sw[i * 4 + k] = wa.getComponent(i, k); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  g.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); g.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(si, 4)); g.setAttribute('skinWeight', new THREE.BufferAttribute(sw, 4));
  const idx = src.index;
  if (idx) { const a = new Uint32Array(idx.count); for (let i = 0; i < idx.count; i++) a[i] = idx.getX(i); g.setIndex(new THREE.BufferAttribute(a, 1)); }
  else { const a = new Uint32Array(n); for (let i = 0; i < n; i++) a[i] = i; g.setIndex(new THREE.BufferAttribute(a, 1)); }
  g.userData.needWeights = rigid < 0 && !ja;
  return g;
}
// Join geometries of one material (same five attributes, all indexed).
function mergeGeos(list) {
  if (list.length === 1) return list[0];
  let nv = 0, ni = 0; for (const g of list) { nv += g.attributes.position.count; ni += g.index.count; }
  const out = new THREE.BufferGeometry(), idx = new Uint32Array(ni);
  for (const [k, w] of [['position', 3], ['normal', 3], ['uv', 2], ['skinIndex', 4], ['skinWeight', 4]]) {
    const A = k === 'skinIndex' ? new Uint16Array(nv * w) : new Float32Array(nv * w); let o = 0;
    for (const g of list) { A.set(g.attributes[k].array, o); o += g.attributes[k].array.length; }
    out.setAttribute(k, k === 'skinIndex' ? new THREE.Uint16BufferAttribute(A, w) : new THREE.BufferAttribute(A, w));
  }
  let vo = 0, io = 0;
  for (const g of list) { const a = g.index.array; for (let i = 0; i < a.length; i++) idx[io + i] = a[i] + vo; io += a.length; vo += g.attributes.position.count; }
  out.setIndex(new THREE.BufferAttribute(idx, 1));
  out.userData.needWeights = list.some((g) => g.userData.needWeights);
  for (const g of list) g.dispose();
  return out;
}
// Static LOD meshes of the crowd art carry no skin: each vertex takes the weights of the nearest LOD0 vertex (uniform grid search).
function transferWeights(dst, src) {
  const C = 0.06, key = (x, y, z) => x * 73856093 ^ y * 19349663 ^ z * 83492791, grid = new Map();
  const sp = src.attributes.position.array, n0 = sp.length / 3;
  for (let i = 0; i < n0; i++) { const k = key(Math.floor(sp[i * 3] / C), Math.floor(sp[i * 3 + 1] / C), Math.floor(sp[i * 3 + 2] / C)); let b = grid.get(k); if (!b) grid.set(k, b = []); b.push(i); }
  const dp = dst.attributes.position.array, n = dp.length / 3, si = dst.attributes.skinIndex.array, sw = dst.attributes.skinWeight.array;
  const ssi = src.attributes.skinIndex.array, ssw = src.attributes.skinWeight.array;
  let worst = 0;
  for (let i = 0; i < n; i++) {
    const x = dp[i * 3], y = dp[i * 3 + 1], z = dp[i * 3 + 2], cx = Math.floor(x / C), cy = Math.floor(y / C), cz = Math.floor(z / C);
    let best = -1, bd = Infinity;
    for (let r = 0; r < 40 && (best < 0 || Math.sqrt(bd) > (r - 1) * C); r++) {
      for (let a = -r; a <= r; a++) for (let b = -r; b <= r; b++) for (let c = -r; c <= r; c++) {
        if (Math.max(Math.abs(a), Math.abs(b), Math.abs(c)) !== r) continue;
        const L = grid.get(key(cx + a, cy + b, cz + c)); if (!L) continue;
        for (const j of L) { const dx = sp[j * 3] - x, dy = sp[j * 3 + 1] - y, dz = sp[j * 3 + 2] - z, d = dx * dx + dy * dy + dz * dz; if (d < bd) { bd = d; best = j; } }
      }
    }
    worst = Math.max(worst, Math.sqrt(bd));
    for (let k = 0; k < 4; k++) { si[i * 4 + k] = ssi[best * 4 + k]; sw[i * 4 + k] = ssw[best * 4 + k]; }
  }
  dst.userData.needWeights = false;
  return worst;
}
function fitSphere(geos) {
  const b = new THREE.Box3(), t = new THREE.Box3();
  for (const g of geos) { g.computeBoundingBox(); t.copy(g.boundingBox); b.union(t); }
  const s = new THREE.Sphere(); b.getBoundingSphere(s); s.radius *= CHR.sphereK;
  return { sphere: s, box: b };
}

// ===== TEMPLATE (load time, under the loading card) =====
// opts: { kind, id, keep(name) -> bool, mat(name, srcMaterial, state) -> Material, states: ['awake'] | ['dormant', 'awake'], floorY, outline,
//         lodDist: [d1, d2], variantOf(name) -> key | null (rebel weapons), height }
export function makeTemplate(gltf, opts) {
  const scene = gltf.scene; scene.updateMatrixWorld(true);
  const keep = opts.keep || (() => true), meshes = [];
  scene.traverse((o) => { if (o.isMesh && keep(nodeName(o))) meshes.push(o); });
  const sk = meshes.find((o) => o.isSkinnedMesh).skeleton, bones = sk.bones.slice();
  let rig = bones[0]; while (rig.parent && rig.parent !== scene) rig = rig.parent;
  const rigInv = rig.matrixWorld.clone().invert();
  const boneInv = bones.map((b) => new THREE.Matrix4().multiplyMatrices(rigInv, b.matrixWorld).invert());
  const parts = [[], [], []], states = opts.states || ['awake'];
  let bindErr = 0;
  for (const o of meshes) {
    const name = nodeName(o), lod = lodOf(name), X = new THREE.Matrix4();
    let remap = null, rigid = -1;
    if (o.isSkinnedMesh) {
      remap = o.skeleton.bones.map((b) => bones.indexOf(b));
      const W = (k) => new THREE.Matrix4().multiplyMatrices(rigInv, o.skeleton.bones[k].matrixWorld).multiply(o.skeleton.boneInverses[k]).multiply(o.bindMatrix);
      X.copy(W(0));
      for (let k = 1; k < o.skeleton.bones.length; k++) { const e = W(k).elements; for (let q = 0; q < 16; q++) bindErr = Math.max(bindErr, Math.abs(e[q] - X.elements[q])); }
    } else {
      X.multiplyMatrices(rigInv, o.matrixWorld);
      const b = boneAncestor(o); rigid = b ? bones.indexOf(b) : -1;
    }
    const g = rigSpaceGeo(o.geometry, X, remap, rigid);
    g.userData.root = !o.isSkinnedMesh && rigid < 0;
    const vkey = opts.variantOf ? opts.variantOf(name) : null;
    parts[lod].push({ geo: g, src: o.material, matName: o.material.name, variant: vkey });
  }
  fixLayout(parts);
  const lods = [], src0 = mergeGeos(parts[0].map((p) => cloneGeo(p.geo)));
  let weightGap = 0; const gapLod = [0, 0, 0];
  for (let l = 0; l < 3; l++) {
    const by = new Map();
    for (const p of parts[l]) { const k = p.matName + '|' + (p.variant || ''); if (!by.has(k)) by.set(k, []); by.get(k).push(p); }
    const out = [];
    for (const [, L] of by) {
      const geo = mergeGeos(L.map((p) => p.geo));
      if (geo.userData.needWeights) { const gp = transferWeights(geo, src0); gapLod[l] = Math.max(gapLod[l], gp); weightGap = Math.max(weightGap, gp); }
      out.push({ geo, matName: L[0].matName, variant: L[0].variant, mats: states.map((s) => opts.mat(L[0].matName, L[0].src, s)) });
    }
    if (out.length) lods.push({ parts: out, ...fitSphere(out.map((p) => p.geo)) });
  }
  src0.dispose();
  const tpl = { kind: opts.kind, id: opts.id, rig: stripMeshes(rig), boneNames: bones.map((b) => b.name), boneInv, lods, states,
    clips: normClips(gltf.animations), floorY: opts.floorY || 0, runV: opts.runV || 1, outline: !!opts.outline, lodDist: opts.lodDist || CHR.lod.suit,
    height: lods[0].box.max.y - Math.min(0, lods[0].box.min.y), bindErr, weightGap, gapLod, tread: CHR.tread[opts.id] || 0 };
  return tpl;
}
function cloneGeo(g) { const c = g.clone(); c.userData = { needWeights: g.userData.needWeights }; return c; }
// The art lays static LODs out beside the rig (x 2.5 m, 5 m) for its viewers; centre them back over LOD0 (rounded to 0.5 m steps).
function fixLayout(parts) {
  const c0 = new THREE.Vector3(), c = new THREE.Vector3(), b = new THREE.Box3();
  const box = (L) => { const bb = new THREE.Box3(); for (const p of L) { p.geo.computeBoundingBox(); b.copy(p.geo.boundingBox); bb.union(b); } return bb; };
  box(parts[0]).getCenter(c0);
  for (let l = 1; l < 3; l++) {
    const roots = parts[l].filter((p) => p.geo.userData.root); if (!roots.length) continue;
    box(roots).getCenter(c);
    const dx = Math.round((c.x - c0.x) * 2) / 2, dz = Math.round((c.z - c0.z) * 2) / 2;
    if (dx || dz) for (const p of roots) p.geo.translate(-dx, 0, -dz);
  }
}
function stripMeshes(rig) {
  const t = rig.clone(true), drop = [];
  t.traverse((o) => { if (o.isMesh || (o.isGroup && o.children.length && o.children.every((c) => c.isMesh))) drop.push(o); });
  for (const o of drop) if (o.parent) o.parent.remove(o);
  t.position.set(0, 0, 0); t.quaternion.identity(); t.scale.set(1, 1, 1); t.updateMatrixWorld(true);
  return t;
}
// Clips start at 0 s: the approved idle and attack begin at 1/60 s (SUITANIM), which would hold the first pose one frame per loop.
function normClips(list) {
  const out = {};
  for (const c of list) {
    let t0 = Infinity; for (const tr of c.tracks) t0 = Math.min(t0, tr.times[0]);
    const k = c.clone(); if (t0 > 0 && t0 < Infinity) { for (const tr of k.tracks) tr.shift(-t0); k.resetDuration(); }
    out[c.name] = k;
  }
  return out;
}

// ===== MATERIALS (load time) =====
// The material name table for every character GLB. tex(name) returns INT's texture for a sheet key (KTX2 or PNG, flipY false for glTF UVs).
// state: 'awake' | 'dormant' (apex and giants). Suit cloth keeps the colour in its file (the recolour round changes the files, not this code).
export function charMaterials(tex) {
  const cache = new Map(), B = CHR.brass;
  const std = (o) => new THREE.MeshStandardMaterial(o);
  const brassTint = new THREE.Color(1, 1, 1).multiplyScalar(B.gain);
  const T = {
    sLam: () => std({ map: tex('suit_lamellar_qin'), metalness: 0, roughness: 0.5 }),
    sBronze: () => std({ map: tex('suit_bronze'), metalness: 0.5, roughness: 0.45 }),
    gdBronze: () => std({ map: tex('bronze_trim_brass'), metalness: 0.4, roughness: 0.6 }),
    gdLacquer: () => std({ map: tex('fodder_trim'), metalness: 0.05, roughness: 0.8 }),
    treadBelt: (s) => std({ map: tex('tread_belt'), color: s === 'dormant' ? 0x8a8a7a : 0xffffff, metalness: 0.4, roughness: 0.6 }),
    rbCloth: () => std({ map: tex('fodder_trim'), color: CHR.rebelCloth, roughness: 0.85 }),
    rbPatch: () => std({ map: tex('fodder_trim'), roughness: 0.85 }),
    rbGlint: () => new THREE.MeshBasicMaterial({ color: 0xffe066 }),
    apexBronze: (s) => s === 'dormant' ? std({ map: tex('apex_patina'), metalness: 0.15, roughness: 0.85 }) : std({ map: tex('bronze_trim_brass'), color: brassTint, metalness: B.metalness, roughness: B.roughness }),
    apexCrack: (s) => s === 'dormant' ? std({ color: 0x6b5a2a, metalness: 0.3, roughness: 0.7, side: THREE.DoubleSide })
      : std({ color: 0xc9a050, emissive: CHR.apexGlow, emissiveIntensity: CHR.apexCrackGlow, metalness: 0.5, roughness: 0.4, side: THREE.DoubleSide }),
    apexOrgan: (s) => s === 'dormant' ? std({ color: 0x2a2f2a, metalness: 0.2, roughness: 0.8 }) : std({ color: 0x10181f, emissive: CHR.apexGlow, emissiveIntensity: CHR.apexOrganGlow, metalness: 0.2, roughness: 0.3 }),
    apexInlay: (s) => s === 'dormant' ? std({ color: 0x8a7a48, metalness: 0.3, roughness: 0.7 }) : std({ color: 0xe2b84a, metalness: 0.6, roughness: 0.35 }),
    apexDark: () => std({ color: 0x1a120c, roughness: 0.9 }),
    palBronze: (s) => s === 'dormant' ? std({ map: tex('bronze_trim_patina'), metalness: 0.15, roughness: 0.8 }) : std({ map: tex('bronze_trim_brass'), metalness: 0.4, roughness: 0.6 }),
    palTin: (s) => s === 'dormant' ? std({ color: 0x7c9c88, metalness: 0.15, roughness: 0.75 }) : std({ color: 0xd8cda8, metalness: 0.6, roughness: 0.35 }),
    palPatina: () => std({ map: tex('bronze_trim_patina'), metalness: 0.15, roughness: 0.8 }),
    // Pieces art (PIECES round 4, art/tools/pieces_mats.json on branch ci-art-missing): crab, wanderer, plate, crown, 墨 wall, decree mark, Kaymuse.
    palInlay: () => std({ color: 0xd6d8da, metalness: 0.15, roughness: 0.4 }),
    palGold: () => std({ color: 0xe2b84a, metalness: 0.25, roughness: 0.5 }),
    palCinnabar: () => std({ color: 0xa8321e, metalness: 0, roughness: 0.7 }),
    palLacquerPlain: () => std({ color: 0x1c1512, metalness: 0, roughness: 0.6 }),
    pcBlack: () => std({ color: 0x100c0b, metalness: 0, roughness: 0.85 }),
    pcDarkBronze: () => std({ map: tex('bronze_trim_brass'), color: 0x4a3f36, metalness: 0.3, roughness: 0.7 }),
    moEarth: () => std({ map: tex('rammed_earth'), color: 0xffe6c4, metalness: 0, roughness: 0.95 }),
    moEarthLine: () => std({ map: tex('rammed_earth'), color: 0xb89a70, metalness: 0, roughness: 0.95 }),
    moTimber: () => std({ map: tex('timber'), color: 0xa89684, metalness: 0, roughness: 0.9 }),
    moTimberLight: () => std({ map: tex('timber'), color: 0xffffff, metalness: 0, roughness: 0.85 }),
    moStone: () => std({ map: tex('river_stone'), color: 0xb0a89e, metalness: 0, roughness: 0.9 }),
    kmRobe: () => std({ map: tex('suit_cloth'), color: 0x1e1a18, metalness: 0, roughness: 0.9 }),
    kmJade: () => std({ color: 0xd9d2c3, metalness: 0, roughness: 0.45 }),
    kmSkin: () => std({ color: 0xdeb393, metalness: 0, roughness: 0.75 }),
    kmWhite: () => std({ color: 0xf2efe9, metalness: 0, roughness: 0.8 }),
  };
  const get = (name, src, state) => {
    const cloth = name.startsWith('sCloth'), face = name.startsWith(CHR.face.prefix);
    const key = name + '|' + (state || 'awake') + (cloth ? '|' + src.color.getHexString() : '') + (face ? '|' + src.uuid : '');
    if (cache.has(key)) return cache.get(key);
    let m;
    if (cloth) { const tint = CHR.clothTint[name.slice(name.indexOf('_') + 1)]; m = std({ map: tex('suit_cloth'), color: tint !== undefined ? new THREE.Color(tint) : src.color.clone(), metalness: 0, roughness: 0.85 }); }
    else if (face) m = (CHR.face.mat && CHR.face.mat(name, src, tex, state || 'awake')) || std({ map: src.map || null, color: src.color.clone(),
      metalness: src.metalness !== undefined ? src.metalness : 0, roughness: src.roughness !== undefined ? src.roughness : 0.5, side: src.side });
    else if (T[name]) m = T[name](state);
    else throw new Error('chars.js charMaterials: no material for "' + name + '" (add it to the table in charMaterials)');
    m.name = name; cache.set(key, m);
    return m;
  };
  // Palace set leaving (Royal Rumble): dispose every material this table made (textures belong to INT's loader).
  get.dispose = () => { for (const m of cache.values()) m.dispose(); cache.clear(); };
  return get;
}
// Dispose a template's rig-space geometries (palace set: guards, rebels, giants). Shared-set templates (suits, tiger, cubs) are kept.
export function disposeTemplate(tpl) { for (const L of tpl.lods) for (const p of L.parts) p.geo.dispose(); }
// Add our vertex code to a material after the game's own onBeforeCompile (fog of war), sharing one program per key.
function chainCompile(base, key, inject) {
  const m = base.clone(), prev = base.onBeforeCompile, pk = base.customProgramCacheKey();
  m.onBeforeCompile = (sh, r) => { prev.call(m, sh, r); inject(sh); };
  m.customProgramCacheKey = () => pk + '|' + key;
  return m;
}

// ===== OUTLINE =====
const OUT = { px: { value: CHR.outline.px }, res: { value: new THREE.Vector2(1920, 1080) }, mat: null };
// One shared material: back faces pushed out along the skinned normal in clip space by uOPx device pixels.
export function outlineMaterial() {
  if (OUT.mat) return OUT.mat;
  const m = new THREE.MeshBasicMaterial({ color: CHR.outline.color, side: THREE.BackSide });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uOPx = OUT.px; sh.uniforms.uORes = OUT.res;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nuniform float uOPx;\nuniform vec2 uORes;')
      .replace('#include <project_vertex>', `#include <project_vertex>
#ifdef USE_SKINNING
vec3 chrN = normalize( normalMatrix * objectNormal );
#else
vec3 chrN = normalize( normalMatrix * normal );
#endif
vec2 chrD = ( projectionMatrix * vec4( chrN, 0.0 ) ).xy;
gl_Position.xy += normalize( chrD + vec2( 1e-6 ) ) * uOPx * 2.0 / uORes * gl_Position.w;`);
  };
  m.customProgramCacheKey = () => 'chrOutline1';
  m.name = 'chrOutline';
  return (OUT.mat = m);
}
// Call on resize and tier change only (drawing-buffer size and pixel ratio).
export function setOutlineSize(w, h, pr) { OUT.res.value.set(w * pr, h * pr); OUT.px.value = CHR.outline.px * pr; }

// ===== RIGS (spawned under the card; pooled; per-frame update in PERFRAME) =====
const TREAD_INJECT = (u) => (sh) => {
  sh.uniforms.uTread = u;
  sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nuniform float uTread;')
    .replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\nvMapUv.x += uTread;\n#endif');
};
// opts: { lodK (phone 0.6), outline (default tpl.outline && CHR.outline.on), castShadow }
export function spawnRig(tpl, opts = {}) {
  const rig = tpl.rig.clone(true), byName = {};
  rig.traverse((o) => { if (o.isBone) byName[o.name] = o; });
  const skel = new THREE.Skeleton(tpl.boneNames.map((n) => byName[n]), tpl.boneInv);
  const lod = new THREE.LOD(), outline = opts.outline !== undefined ? opts.outline : tpl.outline && CHR.outline.on, k = opts.lodK || 1;
  const parts = [], tread = { value: 0 };
  tpl.lods.forEach((L, i) => {
    const grp = new THREE.Group();
    for (const p of L.parts) {
      const mats = p.mats.map((m) => p.matName === 'treadBelt' ? chainCompile(m, 'chrTread', TREAD_INJECT(tread)) : m);
      const sm = new THREE.SkinnedMesh(p.geo, mats[0]);
      sm.bind(skel, I4); sm.boundingSphere = L.sphere; sm.castShadow = !!opts.castShadow; sm.receiveShadow = false; sm.name = tpl.id + '_l' + i + '_' + p.matName;
      grp.add(sm); parts.push({ mesh: sm, mats, matName: p.matName });
      if (outline) { const o = new THREE.SkinnedMesh(p.geo, outlineMaterial()); o.bind(skel, I4); o.boundingSphere = L.sphere; o.name = sm.name + '_ol'; grp.add(o); }
    }
    lod.addLevel(grp, i === 0 ? 0 : tpl.lodDist[i - 1] * k, CHR.lodHyst);
  });
  rig.add(lod);
  const holder = new THREE.Group(); holder.name = 'chr_' + tpl.id;
  rig.position.y = -tpl.floorY; holder.add(rig);
  const mixer = new THREE.AnimationMixer(rig), actions = {};
  for (const n in tpl.clips) {
    const a = mixer.clipAction(tpl.clips[n]); a.clampWhenFinished = true;
    a.setLoop(CHR.loops.includes(n) ? THREE.LoopRepeat : THREE.LoopOnce, Infinity); actions[n] = a;
  }
  return new Rig(tpl, holder, rig, lod, skel, mixer, actions, parts, tread);
}
class Rig {
  constructor(tpl, root, rig, lod, skel, mixer, actions, parts, tread) {
    Object.assign(this, { tpl, root, rig, lod, skel, mixer, actions, parts, tread, base: null, once: null, acc: 0, on: false, state: 0, treadM: 0, x: 0, y: 0, z: 0, animSteps: 0 });
  }
  // Game facing (fx, fz) -> yaw for a +Z-front model. Event and per-frame safe (no allocation).
  place(x, y, z, fx, fz) { this.x = x; this.y = y; this.z = z; this.root.position.set(x, y, z); this.root.rotation.y = Math.atan2(fx, fz); }
  show(scene) { if (!this.root.parent) scene.add(this.root); this.on = true; }
  // Pool rule: a hidden unit leaves the scene graph (no matrix updates, no draw); its clip state resets on the next play().
  hide() { if (this.root.parent) this.root.parent.remove(this.root); this.on = false; }
  // Loops become the base clip; others play once (hit, attack return to the base; death and wake hold their last pose).
  play(name, rate = 1) {
    const a = this.actions[name]; if (!a) return false;
    // The clip in view now is the one-shot if one plays, else the base loop: the new clip always fades from that one. (A loop started
    // while a one-shot played used to fade from the hidden base and forget the one-shot, which then held its last frame at full weight
    // for good and blended into every later clip: a suit that attacked while starting to run, or was broken and then began a new run,
    // stood half in the attack's or the death's last pose. Owner 25 Nov 19:45.)
    const f = CHR.anim.fade, loop = CHR.loops.includes(name), prev = this.once || this.base, old = this.base;
    if (loop && this.base === a && !this.once) { a.timeScale = rate; return true; }
    a.reset(); a.timeScale = rate; a.setEffectiveWeight(1); a.play();
    if (prev && prev !== a) a.crossFadeFrom(prev, f, false);
    if (loop) { if (old && old !== a && old !== prev) old.stop(); this.base = a; this.once = null; } else this.once = a;
    return true;
  }
  // Suits: idle below CHR.runMin m/s, else run at timeScale = speed / run_v (suits_info.json).
  setRun(speed) {
    if (speed < CHR.runMin) { if (this.base !== this.actions.idle || this.once) return; return this.play('idle'); }
    const r = speed / this.tpl.runV;
    if (this.base === this.actions.run) { this.actions.run.timeScale = r; return true; }
    return this.play('run', r);
  }
  // Material state (0 = first state in tpl.states, e.g. dormant; 1 = awake): swaps the prebuilt, warmed materials, no new program.
  setState(i) { if (this.state === i) return; this.state = i; for (const p of this.parts) p.mesh.material = p.mats[i] || p.mats[0]; }
  // Face swap (event only, never per frame): every face part (material name starts with CHR.face.prefix) wears m in every state.
  // Draw m once under a loading card first (a new material can be a new program). Returns the number of face parts swapped.
  setFace(m) {
    let n = 0;
    for (const p of this.parts) if (p.matName.startsWith(CHR.face.prefix)) { for (let i = 0; i < p.mats.length; i++) p.mats[i] = m; p.mesh.material = m; n++; }
    return n;
  }
  // Tread belts: map.offset.x += metres / mpr (ASSET-LIST H), kept in [0, 1).
  addTread(m) { if (!this.tpl.tread) return; this.treadM = (this.treadM + m / this.tpl.tread) % 1; if (this.treadM < 0) this.treadM += 1; this.tread.value = this.treadM; }
  // Leaving for good (palace set): out of the graph, bone texture and per-unit tread materials released.
  dispose() { this.hide(); this.mixer.stopAllAction(); this.mixer.uncacheRoot(this.rig); this.skel.dispose(); for (const p of this.parts) for (const m of p.mats) if (m.name === 'treadBelt' && m.onBeforeCompile !== Object.getPrototypeOf(m).onBeforeCompile) m.dispose(); }
  // Distinct skeletons used by this unit's meshes (the gate wants 1).
  skeletons() { const s = new Set(); for (const p of this.parts) s.add(p.mesh.skeleton); this.root.traverse((o) => { if (o.isSkinnedMesh) s.add(o.skeleton); }); return s.size; }
}
const FR = { frustum: new THREE.Frustum(), pv: new THREE.Matrix4(), sph: new THREE.Sphere(), cx: 0, cy: 0, cz: 0, mixers: 0, skipped: 0 };
// PERFRAME-BEGIN
// Once per drawn frame, before the units update: camera frustum and position.
export function beginFrame(camera) {
  FR.pv.multiplyMatrices(camera.projectionMatrix, camera.matrixWorldInverse); FR.frustum.setFromProjectionMatrix(FR.pv);
  FR.cx = camera.position.x; FR.cy = camera.position.y; FR.cz = camera.position.z; FR.mixers = 0; FR.skipped = 0;
}
// Animate only units on screen; units farther than CHR.anim.nearM step at CHR.anim.farHz; dt = clamped frame dt (0 while paused).
Rig.prototype.update = function (dt) {
  if (!this.on) return;
  const r = this.tpl.lods[0].sphere.radius;
  FR.sph.center.set(this.x, this.y + this.tpl.height * 0.5, this.z); FR.sph.radius = r;
  this.acc += dt;
  if (!FR.frustum.intersectsSphere(FR.sph)) { FR.skipped++; return; }
  const dx = this.x - FR.cx, dy = this.y - FR.cy, dz = this.z - FR.cz;
  if (dx * dx + dy * dy + dz * dz > CHR.anim.nearM * CHR.anim.nearM && this.acc < 1 / CHR.anim.farHz) return;
  this.mixer.update(this.acc); this.acc = 0; FR.mixers++; this.animSteps++;
  const o = this.once;
  if (o && o.time >= o.getClip().duration && o.loop === THREE.LoopOnce && o.getClip().name !== 'death' && o.getClip().name !== 'wake' && o.getClip().name !== 'fall' && this.base) {
    this.base.reset(); this.base.play(); this.base.crossFadeFrom(o, CHR.anim.fade, false); this.once = null;
  }
};
// PERFRAME-END

// Warm-up under the card: all = true draws every LOD level of every rig at once (geometry upload and first draw of each level);
// all = false hands the levels back to THREE.LOD. Call around one render under the opaque card, never in play.
export function lodHold(rigs, all) {
  for (const g of rigs) { g.lod.autoUpdate = !all; if (all) for (const L of g.lod.levels) L.object.visible = true; }
}

// ===== STATUE (load time): a pose frozen into plain meshes per LOD (dormant giants: no skeleton, no bone texture, no mixer) =====
export function makeStatue(tpl, clipName, t) {
  const rig = tpl.rig.clone(true), byName = {}; rig.traverse((o) => { if (o.isBone) byName[o.name] = o; });
  const bones = tpl.boneNames.map((n) => byName[n]), mixer = new THREE.AnimationMixer(rig), clip = tpl.clips[clipName];
  if (clip) { const a = mixer.clipAction(clip); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; a.play(); a.time = Math.min(t, clip.duration); mixer.update(0); }
  rig.updateMatrixWorld(true);
  const M = bones.map((b, j) => new THREE.Matrix4().multiplyMatrices(b.matrixWorld, tpl.boneInv[j]));
  const lod = new THREE.LOD(), meshes = [];
  tpl.lods.forEach((L, i) => {
    const grp = new THREE.Group();
    for (const p of L.parts) {
      const g = poseGeo(p.geo, M), m = new THREE.Mesh(g, p.mats[0]); m.matrixAutoUpdate = false; m.castShadow = false; grp.add(m); meshes.push({ mesh: m, mats: p.mats });
    }
    grp.matrixAutoUpdate = false; lod.addLevel(grp, i === 0 ? 0 : tpl.lodDist[i - 1], CHR.lodHyst);
  });
  mixer.uncacheRoot(rig);
  const root = new THREE.Group(); root.add(lod); root.name = 'statue_' + tpl.id;
  return { root, lod, meshes, place(x, y, z, fx, fz) { root.position.set(x, y, z); root.rotation.y = Math.atan2(fx, fz); root.updateMatrix(); root.matrixAutoUpdate = false; root.updateMatrixWorld(true); } };
}
function poseGeo(src, M) {
  const g = new THREE.BufferGeometry(), pa = src.attributes.position.array, na = src.attributes.normal.array, si = src.attributes.skinIndex.array, sw = src.attributes.skinWeight.array;
  const n = pa.length / 3, pos = new Float32Array(n * 3), nor = new Float32Array(n * 3), v = new THREE.Vector3(), w = new THREE.Vector3(), acc = new THREE.Vector3(), an = new THREE.Vector3(), nm = new THREE.Matrix3();
  for (let i = 0; i < n; i++) {
    acc.set(0, 0, 0); an.set(0, 0, 0);
    for (let k = 0; k < 4; k++) {
      const wt = sw[i * 4 + k]; if (!wt) continue; const m = M[si[i * 4 + k]];
      v.fromArray(pa, i * 3).applyMatrix4(m); acc.addScaledVector(v, wt);
      w.fromArray(na, i * 3).applyMatrix3(nm.getNormalMatrix(m)); an.addScaledVector(w, wt);
    }
    acc.toArray(pos, i * 3); an.normalize().toArray(nor, i * 3);
  }
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3)); g.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  g.setAttribute('uv', src.attributes.uv); g.setIndex(src.index); g.computeBoundingSphere();
  return g;
}

// ===== CROWD (guards and rebels): baked bone textures, one InstancedMesh per type x LOD x material (x weapon variant) =====
const BAKE_VS = `
attribute vec4 aBoneIdx;
attribute vec4 aBoneW;
attribute vec4 aAnim;
uniform highp sampler2D uBake;
uniform float uTime;
mat4 chrBone( float b, int y ) { int x = int( b ) * 4; return mat4( texelFetch( uBake, ivec2( x, y ), 0 ), texelFetch( uBake, ivec2( x + 1, y ), 0 ), texelFetch( uBake, ivec2( x + 2, y ), 0 ), texelFetch( uBake, ivec2( x + 3, y ), 0 ) ); }
mat4 chrSkin() {
  float f = floor( max( uTime - aAnim.z, 0.0 ) * abs( aAnim.w ) * ${CHR.bakeFps.toFixed(1)} );
  f = aAnim.w > 0.0 ? mod( f, aAnim.y ) : min( f, aAnim.y - 1.0 );
  int y = int( aAnim.x + f );
  return aBoneW.x * chrBone( aBoneIdx.x, y ) + aBoneW.y * chrBone( aBoneIdx.y, y ) + aBoneW.z * chrBone( aBoneIdx.z, y ) + aBoneW.w * chrBone( aBoneIdx.w, y );
}
#ifdef CHR_TREAD
attribute float aTread;
#endif`;
function bakeInject(u) {
  return (sh) => {
    sh.uniforms.uBake = u.bake; sh.uniforms.uTime = u.time;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n' + BAKE_VS)
      .replace('void main() {', 'void main() {\n  mat4 chrM = chrSkin();')
      .replace('#include <skinnormal_vertex>', 'objectNormal = ( chrM * vec4( objectNormal, 0.0 ) ).xyz;')
      .replace('#include <skinning_vertex>', 'transformed = ( chrM * vec4( transformed, 1.0 ) ).xyz;')
      .replace('#include <uv_vertex>', '#include <uv_vertex>\n#if defined( CHR_TREAD ) && defined( USE_MAP )\nvMapUv.x += aTread;\n#endif');
  };
}
// Bake every clip of a template into one float texture: row = one frame, 4 texels per bone (rig-space bone matrix x bind inverse).
function bakeClips(tpl) {
  const rig = tpl.rig.clone(true), byName = {}; rig.traverse((o) => { if (o.isBone) byName[o.name] = o; });
  const bones = tpl.boneNames.map((n) => byName[n]), nb = bones.length, mixer = new THREE.AnimationMixer(rig), fps = CHR.bakeFps, table = {};
  let rows = 0; for (const n in tpl.clips) rows += Math.round(tpl.clips[n].duration * fps) + 1;
  const data = new Float32Array(nb * 4 * rows * 4), M = new THREE.Matrix4();
  let row = 0;
  for (const n in tpl.clips) {
    const clip = tpl.clips[n], F = Math.round(clip.duration * fps) + 1, a = mixer.clipAction(clip), loop = CHR.loops.includes(n);
    mixer.stopAllAction(); a.setLoop(THREE.LoopOnce, 1); a.clampWhenFinished = true; a.reset(); a.play();
    for (let f = 0; f < F; f++) {
      a.time = Math.min(f / fps, clip.duration); mixer.update(0); rig.updateMatrixWorld(true);
      for (let b = 0; b < nb; b++) { M.multiplyMatrices(bones[b].matrixWorld, tpl.boneInv[b]); data.set(M.elements, ((row + f) * nb * 4 + b * 4) * 4); }
    }
    table[n] = { row0: row, frames: loop ? Math.max(1, F - 1) : F, loop };
    row += F;
  }
  mixer.uncacheRoot(rig);
  const tex = new THREE.DataTexture(data, nb * 4, rows, THREE.RGBAFormat, THREE.FloatType); tex.needsUpdate = true;
  return { tex, table, data, nb, rows };
}
// tpls: { type: template } (variants: rebel 力士 weapons by school); opts: { pool: { type: n }, lodK, castShadow }
export function makeCrowd(tpls, opts = {}) {
  const C = { types: {}, meshes: [], time: { value: 0 }, flash: new THREE.Color().fromArray(CHR.flash), patch: CHR.patch.map((h) => new THREE.Color(h)), white: new THREE.Color(1, 1, 1), drawn: 0 };
  for (const t in tpls) C.types[t] = crowdType(C, t, tpls[t], (opts.pool && opts.pool[t]) || 16, opts);
  C.batches = [];
  for (const t in C.types) for (const L of C.types[t].levels) for (const B of L.batches) C.batches.push(B);
  return new Crowd(C, opts.lodK || 1);
}
function crowdType(C, t, tpl, n, opts) {
  const bk = bakeClips(tpl), u = { bake: { value: bk.tex }, time: C.time }, T = { tpl, bake: bk, n, levels: [], tread: tpl.tread };
  tpl.lods.forEach((L, li) => {
    const batches = new Map();
    for (const p of L.parts) {
      const key = p.variant || '';
      if (!batches.has(key)) batches.set(key, newBatch(n, key));
      const B = batches.get(key), geo = crowdGeo(p.geo, B), tread = p.matName === 'treadBelt';
      const mat = chainCompile(p.mats[0], tread ? 'chrBakeT' : 'chrBake', bakeInject(u)); if (tread) mat.defines = Object.assign({}, mat.defines, { CHR_TREAD: '' });
      const im = new THREE.InstancedMesh(geo, mat, n);
      im.instanceMatrix = B.mat; im.instanceColor = p.matName === 'rbPatch' ? B.patchCol : B.col;
      im.count = 0; im.visible = false; im.matrixAutoUpdate = false; im.castShadow = !!opts.castShadow; im.receiveShadow = false;
      im.boundingSphere = B.sphere; im.name = t + '_l' + li + '_' + p.matName + (key ? '_' + key : '');
      if (opts.castShadow) { const d = chainCompile(new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking }), 'chrBakeD', bakeInject(u)); im.customDepthMaterial = d; }
      B.meshes.push(im); C.meshes.push(im);
    }
    T.levels.push({ batches: [...batches.values()], base: batches.get('') || null, byVar: batches });
  });
  return T;
}
function newBatch(n, key) {
  const dyn = (a) => { a.setUsage(THREE.DynamicDrawUsage); return a; };
  const col = dyn(new THREE.InstancedBufferAttribute(new Float32Array(n * 3).fill(1), 3)), patchCol = dyn(new THREE.InstancedBufferAttribute(new Float32Array(n * 3).fill(1), 3));
  return { key, n, count: 0, meshes: [], mat: dyn(new THREE.InstancedBufferAttribute(new Float32Array(n * 16), 16)), col, patchCol,
    anim: dyn(new THREE.InstancedBufferAttribute(new Float32Array(n * 4), 4)), tread: dyn(new THREE.InstancedBufferAttribute(new Float32Array(n), 1)),
    sphere: new THREE.Sphere(), bb: new Float64Array(6) };
}
// The crowd geometry: the template part with its skin as aBoneIdx / aBoneW (not a SkinnedMesh) plus the batch's per-instance attributes.
function crowdGeo(src, B) {
  const g = new THREE.BufferGeometry();
  for (const k of ['position', 'normal', 'uv']) g.setAttribute(k, src.attributes[k]);
  g.setAttribute('aBoneIdx', new THREE.BufferAttribute(Float32Array.from(src.attributes.skinIndex.array), 4)); g.setAttribute('aBoneW', src.attributes.skinWeight);
  g.setAttribute('aAnim', B.anim); g.setAttribute('aTread', B.tread); g.setIndex(src.index);
  return g;
}
class Crowd {
  constructor(C, lodK) { Object.assign(this, C); this.lodK = lodK; this.cx = 0; this.cy = 0; this.cz = 0; }
  // Per unit (pool time): its animation and LOD state. type = crowd type key.
  makeState(type, patch = 0) { return { type, T: this.types[type], clip: null, a: new Float64Array([0, 1, 0, 1, 0]), lod: 0, patch: patch % CHR.patch.length }; }
  // Event time: start clip name at game time t0 (rate = playback speed). Unknown names keep the current clip.
  setClip(st, name, t0, rate = 1) {
    const e = st.T.bake.table[name]; if (!e) return false;
    st.clip = name; st.a[0] = e.row0; st.a[1] = e.frames; st.a[2] = t0; st.a[3] = e.loop ? rate : -rate;
    return true;
  }
  addTread(st, m) { if (!st.T.tread) return; const a = st.a; a[4] = (a[4] + m / st.T.tread) % 1; if (a[4] < 0) a[4] += 1; }
  // Palace set leaving: every crowd mesh out of the graph; its geometries, material clones and bake textures disposed.
  dispose() {
    for (const im of this.meshes) { if (im.parent) im.parent.remove(im); im.geometry.dispose(); im.material.dispose(); if (im.customDepthMaterial) im.customDepthMaterial.dispose(); }
    for (const t in this.types) this.types[t].bake.tex.dispose();
    this.meshes.length = 0; this.batches.length = 0;
  }
  // Everything the warm-up draw needs: one instance in every batch (INT draws once under the card, then calls begin/end).
  warmAll(x, y, z) { for (const B of this.batches) { B.count = 0; writeInst(B, x, y, z, 0, null, null, this); } this.endBatches(); }
}
const ZERO_ANIM = new Float64Array([0, 1, 0, 1, 0]);
const CW = { m: new THREE.Matrix4(), q: new THREE.Quaternion(), p: new THREE.Vector3(), s: new THREE.Vector3(1, 1, 1), up: new THREE.Vector3(0, 1, 0) };
// PERFRAME-BEGIN
// Game time for every crowd clip (stops while paused: the game passes its own clock).
Crowd.prototype.setTime = function (t) { this.time.value = t; };
// Start of a drawn frame: counts to 0 (units are packed into the first instances each frame, as drawGuards does today).
Crowd.prototype.begin = function (camera) {
  this.cx = camera.position.x; this.cy = camera.position.y; this.cz = camera.position.z; this.drawn = 0;
  const bs = this.batches; for (let i = 0; i < bs.length; i++) bs[i].count = 0;
};
// One seen unit: position, facing (game fx, fz), its state, a colour multiplier (null = none; flash / shimmer from the game), weapon variant key.
Crowd.prototype.put = function (st, x, y, z, fx, fz, col, variant) {
  const T = st.T, d = Math.sqrt((x - this.cx) * (x - this.cx) + (y - this.cy) * (y - this.cy) + (z - this.cz) * (z - this.cz));
  const D = T.tpl.lodDist, k = this.lodK, h = 1 + CHR.lodHyst;
  let l = st.lod;
  if (l === 0 && d > D[0] * k * h) l = 1;
  if (l === 1 && d > D[1] * k * h) l = 2;
  if (l === 2 && d < D[1] * k / h) l = 1;
  if (l === 1 && d < D[0] * k / h) l = 0;
  if (l >= T.levels.length) l = T.levels.length - 1;
  st.lod = l;
  const L = T.levels[l], yaw = Math.atan2(fx, fz);
  if (L.base) writeInst(L.base, x, y, z, yaw, st, col, this);
  if (variant) { const B = L.byVar.get(variant); if (B) writeInst(B, x, y, z, yaw, st, col, this); }
  this.drawn++;
};
function writeInst(B, x, y, z, yaw, s, col, C) {
  const i = B.count; if (i >= B.n) return;
  CW.q.setFromAxisAngle(CW.up, yaw); CW.p.set(x, y, z); CW.m.compose(CW.p, CW.q, CW.s); CW.m.toArray(B.mat.array, i * 16);
  const a = B.anim.array, sa = s ? s.a : ZERO_ANIM; a[i * 4] = sa[0]; a[i * 4 + 1] = sa[1]; a[i * 4 + 2] = sa[2]; a[i * 4 + 3] = sa[3];
  B.tread.array[i] = sa[4];
  const c = col || C.white, pc = s ? C.patch[s.patch] : C.white;
  B.col.array[i * 3] = c.r; B.col.array[i * 3 + 1] = c.g; B.col.array[i * 3 + 2] = c.b;
  B.patchCol.array[i * 3] = c.r * pc.r; B.patchCol.array[i * 3 + 1] = c.g * pc.g; B.patchCol.array[i * 3 + 2] = c.b * pc.b;
  const bb = B.bb;
  if (i === 0) { bb[0] = bb[1] = x; bb[2] = bb[3] = y; bb[4] = bb[5] = z; }
  else { if (x < bb[0]) bb[0] = x; if (x > bb[1]) bb[1] = x; if (y < bb[2]) bb[2] = y; if (y > bb[3]) bb[3] = y; if (z < bb[4]) bb[4] = z; if (z > bb[5]) bb[5] = z; }
  B.count = i + 1;
}
// End of the frame's puts: counts, visibility (a batch with no units draws nothing), culling spheres around the instances, uploads.
Crowd.prototype.end = function () { this.endBatches(); };
Crowd.prototype.endBatches = function () {
  const bs = this.batches;
  for (let i = 0; i < bs.length; i++) {
    const B = bs[i], n = B.count, on = n > 0;
    if (on) {
      const bb = B.bb, ex = bb[1] - bb[0], ey = bb[3] - bb[2], ez = bb[5] - bb[4];
      B.sphere.center.set((bb[0] + bb[1]) * 0.5, (bb[2] + bb[3]) * 0.5, (bb[4] + bb[5]) * 0.5);
      B.sphere.radius = 0.5 * Math.sqrt(ex * ex + ey * ey + ez * ez) + CHR.crowdPad;
      B.mat.needsUpdate = true; B.anim.needsUpdate = true; B.col.needsUpdate = true; B.patchCol.needsUpdate = true; B.tread.needsUpdate = true;
    }
    for (let m = 0; m < B.meshes.length; m++) { const im = B.meshes[m]; if (im.count !== n) im.count = n; if (im.visible !== on) im.visible = on; }
  }
};

// ===== HIT (pure, allocation free; called from the fixed step) =====
// u: a unit with x, z, fx, fz (unit facing), r, and u.hit = one of CHR.hit (null = a circle of radius u.r, as today).
// PERFRAME-END
// Scratch for the line test, built once at load (outside the per-frame block: it is not per-frame code).
const HS = { ax: 0, az: 0, bx: 0, bz: 0, t0: 0, t1: 1 };
// PERFRAME-BEGIN
// Liang-Barsky step: keep the part of the segment where p * t <= q.
function clipT(p, q) {
  if (p === 0) return q >= 0;
  const t = q / p;
  if (p < 0) { if (t > HS.t1) return false; if (t > HS.t0) HS.t0 = t; } else { if (t < HS.t0) return false; if (t < HS.t1) HS.t1 = t; }
  return true;
}
function axis(u) {
  const s = u.hit, a = s.off - s.half, b = s.off + s.half;
  HS.ax = u.x + u.fx * a; HS.az = u.z + u.fz * a; HS.bx = u.x + u.fx * b; HS.bz = u.z + u.fz * b;
}
function segDist(px, pz, ax, az, bx, bz) {
  const dx = bx - ax, dz = bz - az, L = dx * dx + dz * dz;
  let t = L > 0 ? ((px - ax) * dx + (pz - az) * dz) / L : 0; t = t < 0 ? 0 : t > 1 ? 1 : t;
  const qx = ax + dx * t - px, qz = az + dz * t - pz;
  return Math.sqrt(qx * qx + qz * qz);
}
export const HIT = {
  // Distance from (x, z) to the unit's hit axis (its centre for a circle). Checks written 'dist <= R + u.r' keep their form; u.r = shape r.
  dist(u, x, z) {
    if (!u.hit) return Math.sqrt((x - u.x) * (x - u.x) + (z - u.z) * (z - u.z));
    axis(u); return segDist(x, z, HS.ax, HS.az, HS.bx, HS.bz);
  },
  // A line skill from (ox, oz) along unit (dx, dz), length len, half width hw: true if the unit's body touches it. Same rule as the game's
  // circle test (rectangle grown by u.r ahead and to the sides, not behind the caster), applied to every point of the capsule axis.
  line(u, ox, oz, dx, dz, len, hw) {
    const r = u.r;
    if (!u.hit) { const qx = u.x - ox, qz = u.z - oz, al = qx * dx + qz * dz, sd = Math.abs(qx * dz - qz * dx); return al >= 0 && al <= len + r && sd <= hw + r; }
    axis(u);
    const a0 = (HS.ax - ox) * dx + (HS.az - oz) * dz, s0 = (HS.ax - ox) * dz - (HS.az - oz) * dx;
    const a1 = (HS.bx - ox) * dx + (HS.bz - oz) * dz, s1 = (HS.bx - ox) * dz - (HS.bz - oz) * dx;
    HS.t0 = 0; HS.t1 = 1;
    const da = a1 - a0, ds = s1 - s0, W = hw + r;
    return clipT(-da, a0) && clipT(da, len + r - a0) && clipT(-ds, s0 + W) && clipT(ds, W - s0) && HS.t0 <= HS.t1;
  },
  // Giant sweep: true if a circle (x, z, r) touches the sector in front of g (g.x, g.z, facing g.fx, g.fz), CHR.sweep radius and angle.
  // r = 0 for the game's point tests (suits, guards, vats); r = a bot's dodge margin.
  sector(g, x, z, r = 0) {
    const R = CHR.sweep.r, half = CHR.sweep.deg * Math.PI / 360, dx = x - g.x, dz = z - g.z, d = Math.sqrt(dx * dx + dz * dz);
    if (d > R + r) return false;
    if (d <= r) return true;
    const c = Math.cos(half), s = Math.sin(half);
    if ((dx * g.fx + dz * g.fz) / d >= c) return true;
    const lx = g.fx * c - g.fz * s, lz = g.fx * s + g.fz * c, rx = g.fx * c + g.fz * s, rz = -g.fx * s + g.fz * c;
    return segDist(x, z, g.x, g.z, g.x + R * lx, g.z + R * lz) <= r || segDist(x, z, g.x, g.z, g.x + R * rx, g.z + R * rz) <= r;
  },
};
// PERFRAME-END

// The sweep tell drawn from the same values: flat sector, centre along local -Z (place with rotation.y = atan2(-fx, -fz), like the line tells).
export function sectorGeometry(R = CHR.sweep.r, deg = CHR.sweep.deg, segs = 32) {
  const t = THREE.MathUtils.degToRad(deg), g = new THREE.CircleGeometry(R, segs, Math.PI / 2 - t / 2, t);
  g.rotateX(-Math.PI / 2);
  return g;
}

// ===== FRAME =====
// Counters for the probe and the checks (read-only).
export function stats() { return { mixers: FR.mixers, offscreen: FR.skipped }; }
