// Palace architecture and props (batches 17d and 17e; PREP-PAL, 25 Nov 2026). Render only: collision stays on index.html's box solids.
// docs/HOOKS-17de.md says exactly how index.html calls this module. Sources: art/ASSET-LIST.md A, B, C, H; docs/INTEGRATION.md sections 5, 6, 9.
// Build rules: the palace is built once under card P (kit, then one art group per room); repeats are one InstancedMesh per piece and
// material per room with shared geometry; single props are THREE.LOD with every level merged per material; every matrix is frozen
// (matrixAutoUpdate false); materials are shared; no lights (lamps are emissive cards); nothing is created after the build; state changes
// swap visibility, materials or a precomputed matrix; disposeRoom and disposeKit free everything this module made (renderer.info flat).
// Approved assets (A1-A4) keep their textures and mapping: hall and core floors stay the game's own box floor (M.palFloor).
import * as THREE from 'three';

// ===================== CONFIG (tunables; the integration may copy this block into index.html CONFIG as CONFIG.PAL_ART) =====================
export const PAL_ART = {
  // Switch for the palace architecture (17d): off = the game's box rooms.
  arch: true,
  // Switch for the palace props (17e): off = the game's box pieces.
  props: true,
  // Per-feature switches (each new piece can wait switched off until the owner approves it).
  on: {
    // Stepped rammed-earth terrace on every edge that faces the lake (B1).
    terrace: true,
    // Eaves and round tile ends on hall walls, eaves on corridor walls (B5, A11).
    eaves: true,
    // Bamboo-slip racks and bundles on hall north walls (A20; add solids).
    racks: true,
    // Garden planting cards along the garden walls (A16, alpha-tested, no shadow).
    plants: true,
    // Signal flags on poles along court north walls (A19; parked look, colours 9 of 9).
    flags: true,
    // Paired 阙 gate towers at the forecourt's west and east bridge gates (B6; owner question: placement).
    que: true,
    // Star-map inlay on the core floor in front of the dais (A17 as floor inlay, FIXB).
    inlay: true,
    // Throne and dais model on the core dais block (B10, dais 1.5 m).
    throne: true,
    // Bronze tree lamps with flame and halo cards, no lights (C9; add solids).
    lamps: true,
    // Bell stands on the core side walls (C10; add solids).
    bells: true,
    // Split tiger tally on the core dais (C11, about 1.5k tris).
    tally: true,
    // School emblem standard beside each hall's 鼎 (C12; fa and mo sigils wait for the owner; add solids).
    standards: true,
    // Black-lake texture on the lake plane (A15).
    lake: true,
  },
  // GLB folder under the asset root (17a meshopt encodes) and the files this module reads.
  dir: 'assets/c/models/',
  // Architecture pieces in arch/ (B1-B11, A16, A19, A20 dressing).
  archFiles: ['wall_seg', 'wall_low', 'wall_earth_seg', 'wall_mural_seg', 'wall_walk_seg', 'eave_seg', 'tile_end', 'terrace_edge', 'pillar', 'door',
    'bridge_bay_8', 'bridge_bay_12', 'throne_dais', 'que_pair', 'slip_rack', 'slip_bundle', 'flag_pole', 'flag_0', 'flag_1', 'flag_2', 'flag_3', 'flag_4',
    'flag_5', 'flag_6', 'flag_7', 'flag_8', 'plant_wheat', 'plant_millet', 'plant_shrub', 'plant_grass'],
  // Props (C1-C12) at the folder root.
  propFiles: ['beast', 'ding', 'vat', 'crane', 'censer', 'clock', 'huabiao', 'merc', 'lamp', 'bells', 'tally', 'standard'],
  // Material table: GLB material name -> texture (CONFIG.LOAD file name, KTX2 desk/phone, PNG fallback), burnt variant (A18 swap), PBR values,
  // tint (linear multiplier), kind (std | basic | matcap), alpha (alpha-test cut), add (additive card), op (opacity of a blended card).
  // Values follow the approved game materials (A1-A4: index.html mat()) and the art viewers (arch.html, beast.html) the samples were judged in.
  MATS: {
    // A2 lime plaster wall (approved; box walls use the same image).
    palWall: { tex: 'hall_wall', burnt: 'wall_burnt', rough: 0.9 },
    // A1 red 丹 floor (approved; the throne dais top and debris).
    palFloor: { tex: 'hall_floor', rough: 0.9 },
    // A3 black lacquer pillar (approved).
    palPillar: { tex: 'pillar', burnt: 'timber_burnt', rough: 0.75 },
    // A4 black lacquer door (approved; index.html palDoor values).
    palDoor: { tex: 'door', burnt: 'timber_burnt', metal: 0.4, rough: 0.6 },
    // A13 bronze, brass sheet on every live piece (owner pick 25 Nov 02:1x).
    palBronze: { tex: 'bronze_trim_brass', metal: 0.4, rough: 0.6 },
    // A6 rammed earth (terrace sides, wall-walk).
    palEarth: { tex: 'rammed_earth', burnt: 'earth_burnt', rough: 0.85 },
    // A6 core rammed earth, 5-6 cm layers (core walls).
    palEarthCore: { tex: 'rammed_earth_core', rough: 0.85 },
    // B1 river-stone footing.
    palRiver: { tex: 'river_stone', rough: 0.85 },
    // A7 stone paving (court floors, plinths, kerbs).
    palStone: { tex: 'stone_paving', rough: 0.85 },
    // A8 floor tiles (corridor floors).
    palTiles: { tex: 'floor_tiles', rough: 0.85 },
    // A9 hollow-brick parapet.
    palBrick: { tex: 'hollow_brick', rough: 0.85 },
    // A10 mural band on plaster (corridor walls).
    palMural: { tex: 'mural_wall', burnt: 'wall_burnt', rough: 0.85 },
    // A11 grey roof tile.
    palRoof: { tex: 'roof_tile', rough: 0.85 },
    // A11 round tile ends.
    palTileEnd: { tex: 'tile_ends', rough: 0.85 },
    // A12 timber (beams, trestles, bridge decks).
    palTimber: { tex: 'timber', burnt: 'timber_burnt', rough: 0.85 },
    // Black lacquer on timber (timber image under a dark tint, arch viewer LACQUER_TINT 0x5a4f4a).
    palLacquer: { tex: 'timber', burnt: 'timber_burnt', rough: 0.85, tint: 0x5a4f4a },
    // A16 garden ground.
    palGround: { tex: 'garden_ground', rough: 0.85 },
    // A16 planting cards (alpha test, both sides).
    palPlant: { tex: 'garden_plants', rough: 0.85, alpha: 0.5, side: 2 },
    // A19 signal flags (alpha test, both sides).
    palFlag: { tex: 'signal_flags', rough: 0.85, alpha: 0.5, side: 2 },
    // A20 bamboo slips.
    palSlips: { tex: 'slips', burnt: 'slips_burnt', rough: 0.85 },
    // A15 black lake (blue-green near-black).
    palLake: { tex: 'black_lake', rough: 0.35 },
    // A17 star-map inlay on the core floor (alpha test, drawn over the floor with polygon offset).
    palStarInlay: { tex: 'star_inlay', rough: 0.5, metal: 0.3, alpha: 0.5, poly: true },
    // Silver inlay lines on bronze (props).
    palInlay: { col: 0xc8ccd0, metal: 0.6, rough: 0.35 },
    // Dark recesses (props): very dark, so matte.
    palDark: { col: 0x2a1f14, rough: 0.9 },
    // 鼎 ember bed, unlit (lit state).
    palEmber: { col: 0xe8742a, kind: 'basic' },
    // 鼎 coals (lit state).
    palCoal: { col: 0x3a1a0e, rough: 1 },
    // Warm halo card (鼎 lit, lamps): generated radial glow, additive, no light.
    palGlow: { glow: true, kind: 'basic', add: true, side: 2 },
    // Vat crack spray (cracked tell).
    palSpray: { col: 0xcfe4ee, rough: 0.4, op: 0.85 },
    // 鼎 ash crust (dry state).
    palAsh: { col: 0x4a443e, rough: 1 },
    // Vat water and puddle (the game's vat water colour).
    palWater: { col: 0x2a6a9a, rough: 0.3, metal: 0.1 },
    // Crane and censer smoke cards (klad smoke_card, blended, no depth write).
    palSmoke: { tex: 'smoke_card', rough: 1, op: 0.9167, side: 2 },
    // Lamp flame cards (klad flame_card, additive).
    palFlame: { tex: 'flame_card', kind: 'basic', add: true, side: 2 },
    // Cinnabar decoration.
    palCinnabar: { col: 0xa8321e, rough: 0.7 },
    // Plain black lacquer (props).
    palLacquerPlain: { col: 0x1c1512, rough: 0.6 },
    // Laid gold (clock graduations; matte, W1a measured gold as metal dE 7.3 from brass).
    palGold: { col: 0xe2b84a, metal: 0.25, rough: 0.5 },
    // 华表 eyes, asleep (decoration only, INTEGRATION reading 5).
    palEye: { col: 0x241a10, metal: 0.3, rough: 0.6 },
    // Lamp reflectors: the mercury matcap (A14).
    palMercRef: { tex: 'mercury_matcap', kind: 'matcap', side: 2 },
    // Mercury surface (A14 matcap with the FIXB ripple shimmer; three looks: idle, warn, hot).
    palMerc: { tex: 'mercury_matcap', kind: 'matcap', merc: true },
    // 鼎 school accent (one material per school, colours from the GLB extras in CONFIG.SCHOOLS order).
    palAccent: { accent: true },
    // School standard banner (atlas cell per school, alpha test, both sides).
    palBanner: { tex: 'school_standards', rough: 0.9, alpha: 0.5, side: 2, banner: true },
  },
  // Prop-family names that differ from the architecture's (beast.html matFor): plinths are the lion stone, lacquer is the pillar image.
  PROP_MATS: {
    // Beast and 华表 plinth stone (the old lion stone image; A5 retired as a lion, kept as plinth stone in the samples).
    palStone: { tex: 'lion_stone', rough: 0.9 },
    // 华表 lacquer column (A3 pillar image).
    palLacquer: { tex: 'pillar', rough: 0.55 },
  },
  // Mercury looks (FIXB round 2): colour multiplier on the matcap, ripple normal strength, shimmer slide speed (UV per second).
  merc: {
    // Calm between pulses.
    idle: { col: [0.6, 0.62, 0.66], ns: 0.12, speed: 0.02 },
    // The tell before a pulse.
    warn: { col: [1.7, 1.74, 1.8], ns: 0.45, speed: 0.35 },
    // Burning (damage on).
    hot: { col: [2.6, 2.6, 2.65], ns: 0.3, speed: 0.6 },
    // Ripple tile repeat on the surface UVs.
    rippleRep: 3,
    // Channel lip offset outside the mercury edge, m (merc.glb demo: 1.07 for a 2 m channel).
    lipOut: 0.07,
  },
  // Texture anisotropy (owner rule: 4 max).
  aniso: 4,
  // Metres per texture repeat for floors and the lake drawn by this module (256 px/m at 1024 px).
  tileM: 4,
  // Metres per repeat of the black-lake image on the lake plane.
  lakeTileM: 8,
  // Floor slab thickness, m (index.html palace floors: th 1.2, top at 0).
  floorTh: 1.2,
  // Wall render centre inside the room edge, m (index.html walls stand from the edge to wallT 0.5 inside, so their centre is 0.25 in).
  wallIn: 0.25,
  // Architecture segment length, m (B2/B5/B7/B1 pieces are 4 m); a run is filled with whole segments stretched by at most this share either way.
  segM: 4,
  // Wall piece per room type for tall edges (north, west, east; index.html wallH) and for low edges (south, bridge ends; lowH).
  walls: { hall: 'wall_seg', core: 'wall_earth_seg', court: 'wall_walk_seg', corridor: 'wall_mural_seg', garden: 'wall_seg', bridge: 'wall_low', low: 'wall_low' },
  // Floor material per room type drawn by this module ('' = keep the game's box floor: hall and core keep the approved A1 floor).
  floors: { hall: '', core: '', court: 'palStone', corridor: 'palTiles', garden: 'palGround', bridge: 'palTimber' },
  // Box part keys (index.html palPart) the art replaces per room type; the integration skips building those box meshes.
  replaces: { hall: ['palWall', 'palPillar'], core: ['palWall', 'palPillar', 'pillar', 'gold'], court: ['palWall', 'floor:court'],
    corridor: ['palWall', 'floor:bridge'], garden: ['palWall', 'floor:court'], bridge: ['palWall', 'floor:bridge'] },
  // Tile ends per eave segment and their place on the eave (arch viewer: x0 + i * step along, y, z outward), m.
  tileEnds: { n: 8, x0: 0.3867, step: 0.5, y: 4.09, z: -1.26 },
  // Bridge bays: deck lowered under the module's plain deck slab (the deck slab carries the burn tint), m; rail centre inside the edge, m.
  bridge: { bayY: -0.02, railIn: 0.25 },
  // Slip racks on a hall's north wall: first and last x inset, step, clear width either side of a door gap, gap to the wall face, m; max racks.
  racks: { inset: 3.2, step: 3.0, doorClear: 2.6, depth: 0.02, max: 8 },
  // Slip bundles per rack: shelves, bundles per shelf, layers, shelf height step and first shelf height, m; every skip-th bundle left out.
  bundles: { shelves: 5, per: 11, layers: 2, dy: 0.5, y0: 0.34, skip: 7 },
  // Garden planting: cards per garden at most, band from the walls, clear radius around doors, card scale range, seed.
  plants: { max: 360, band: 3.2, doorClear: 4.5, s0: 1.2, s1: 2.2, seed: 7 },
  // Court flags: poles at these offsets from the room centre along the north wall (m), the flag atlas index per pole, flag height on the pole.
  flags: { xs: [-20, -12, 12, 20], ids: [3, 0, 6, 8], y: 2.8, z: 0.9, doorClear: 3 },
  // 阙 pairs: room id and side of the gate they mark, distance outside the edge, m (owner question; W2 had them north of the forecourt,
  // where the 12 m approach bridge is wider than the 8 m passage).
  que: { at: [{ room: 'fore', side: 'w' }, { room: 'fore', side: 'e' }], out: 3.2 },
  // Star-map inlay cell size and margins (x from the core centre, z from the dais front and the south edge), m.
  inlay: { cell: 4, halfW: 12, zFromDais: 5, zSouth: 1, y: 0.003 },
  // Lamps: inset from the north corners of halls, offset beside the core dais, m; solid half size, m.
  lamps: { inset: 1.4, coreDx: 7.4, half: 0.45 },
  // Bell stands: inset from the core side walls, z offset from the core centre, m; solid half sizes (across, along the wall), m.
  bells: { inset: 1.3, dz: 3, halfX: 0.55, halfZ: 2.2 },
  // Tally on the dais top: x offset from the dais centre, m; dais top height, m.
  tally: { dx: 4.2, y: 1.5 },
  // Standard beside the 鼎: distance toward the room centre in x, m; solid half size, m.
  standard: { dx: 2.2, half: 0.3 },
  // LOD node name prefix per prop file where it differs from the file name (vat_body_lod0).
  lodNode: { vat: 'vat_body' },
  // Beast pose: bones whose highest point marks the strike windup (raised claw), samples over the strike clip.
  beast: { windupBones: ['paw_L', 'paw_R'], samples: 24 },
  // Water clock level steps (index.html CONFIG.PIECES2.clock.steps); the moving parts' matrices are precomputed per step.
  clockSteps: 48,
  // LOD switch rule (INTEGRATION section 6): FOV 50 at 1080p = 1158 px focal length; LOD0 while the prop is over near px tall, LOD2 under far px;
  // phone distances x phoneK. Distances in metres per prop = height x focal / px (kit.info() lists them).
  lod: { focalPx: 1158, nearPx: 200, farPx: 70, phoneK: 0.6 },
  // A LOD level whose floor is further than this from LOD0's is not used (it would float or sink), m.
  lodFloorM: 0.1,
  // Props shorter than this cast no shadow (small props castShadow off), m.
  shadowMinH: 2.0,
  // Pieces that never cast shadows (small or below the floor).
  noShadow: ['tile_end', 'slip_bundle', 'terrace_edge', 'plant_wheat', 'plant_millet', 'plant_shrub', 'plant_grass', 'flag'],
};

// ===================== Shader hook: fog of war for this module's materials =====================
// The game's addFow writes the world position as modelMatrix * position, which ignores instanceMatrix (InstancedMesh pieces would all
// read as standing at the room origin) and needs <worldpos_vertex> (MeshMatcapMaterial has none). This hook covers both; its program key
// 'pafow1' keeps its programs apart from the game's 'fow1' programs. fow = { uFowC, uFowR, uFowDim } uniform objects (the game's FOW).
function fowHook(m, fow) {
  if (!fow) return;
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uFowC = fow.uFowC; sh.uniforms.uFowR = fow.uFowR; sh.uniforms.uFowDim = fow.uFowDim;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\nvarying vec3 vFowPos;')
      .replace('#include <project_vertex>', '#include <project_vertex>\nvec4 paW = vec4(transformed, 1.0);\n#ifdef USE_INSTANCING\npaW = instanceMatrix * paW;\n#endif\nvFowPos = (modelMatrix * paW).xyz;');
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\nvarying vec3 vFowPos;\nuniform vec3 uFowC;\nuniform float uFowR;\nuniform float uFowDim;')
      .replace('#include <dithering_fragment>', '#include <dithering_fragment>\ngl_FragColor.rgb *= mix(1.0, uFowDim, smoothstep(uFowR, uFowR + 3.0, distance(vFowPos.xz, uFowC.xz)));');
  };
  m.customProgramCacheKey = () => 'pafow1';
}

// ===================== Geometry baking (build time only) =====================
const _v = new THREE.Vector3(), _n = new THREE.Vector3(), _nm = new THREE.Matrix3();
// One float geometry from [geometry, matrix] pairs (quantised glTF attributes read through fromBufferAttribute); position, normal, uv, index.
function merge(list) {
  let nv = 0, ni = 0;
  for (const [g] of list) { nv += g.attributes.position.count; ni += g.index ? g.index.count : g.attributes.position.count; }
  const pos = new Float32Array(nv * 3), nor = new Float32Array(nv * 3), uv = new Float32Array(nv * 2), idx = nv > 65535 ? new Uint32Array(ni) : new Uint16Array(ni);
  let ov = 0, oi = 0;
  for (const [g, m] of list) {
    const P = g.attributes.position, N = g.attributes.normal, U = g.attributes.uv; _nm.getNormalMatrix(m);
    for (let i = 0; i < P.count; i++) {
      _v.fromBufferAttribute(P, i).applyMatrix4(m); pos[(ov + i) * 3] = _v.x; pos[(ov + i) * 3 + 1] = _v.y; pos[(ov + i) * 3 + 2] = _v.z;
      if (N) { _n.fromBufferAttribute(N, i).applyMatrix3(_nm).normalize(); nor[(ov + i) * 3] = _n.x; nor[(ov + i) * 3 + 1] = _n.y; nor[(ov + i) * 3 + 2] = _n.z; }
      if (U) { uv[(ov + i) * 2] = U.getX(i); uv[(ov + i) * 2 + 1] = U.getY(i); }
    }
    if (g.index) for (let i = 0; i < g.index.count; i++) idx[oi + i] = g.index.getX(i) + ov;
    else for (let i = 0; i < P.count; i++) idx[oi + i] = i + ov;
    ov += P.count; oi += g.index ? g.index.count : P.count;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  out.setAttribute('uv', new THREE.BufferAttribute(uv, 2)); out.setIndex(new THREE.BufferAttribute(idx, 1));
  out.computeBoundingBox(); out.computeBoundingSphere();
  return out;
}
// A skinned mesh in its current pose as a float geometry in file-root space (CPU skinning of positions and normals, then the mesh matrix).
function skinned(o) {
  const g = o.geometry, P = g.attributes.position, N = g.attributes.normal, SI = g.attributes.skinIndex, SW = g.attributes.skinWeight, sk = o.skeleton;
  const bm = sk.bones.map((b, j) => new THREE.Matrix4().multiplyMatrices(b.matrixWorld, sk.boneInverses[j]));
  const pos = new Float32Array(P.count * 3), nor = new Float32Array(P.count * 3), M = new THREE.Matrix4(), T = new THREE.Matrix4(), e = M.elements;
  for (let i = 0; i < P.count; i++) {
    e.fill(0);
    for (let k = 0; k < 4; k++) { const w = SW.getComponent(i, k); if (!w) continue; const be = bm[SI.getComponent(i, k)].elements; for (let q = 0; q < 16; q++) e[q] += w * be[q]; }
    T.multiplyMatrices(o.matrixWorld, o.bindMatrixInverse).multiply(M).multiply(o.bindMatrix); _nm.getNormalMatrix(T);
    _v.fromBufferAttribute(P, i).applyMatrix4(T); pos[i * 3] = _v.x; pos[i * 3 + 1] = _v.y; pos[i * 3 + 2] = _v.z;
    _n.fromBufferAttribute(N, i).applyMatrix3(_nm).normalize(); nor[i * 3] = _n.x; nor[i * 3 + 1] = _n.y; nor[i * 3 + 2] = _n.z;
  }
  const out = new THREE.BufferGeometry();
  out.setAttribute('position', new THREE.BufferAttribute(pos, 3)); out.setAttribute('normal', new THREE.BufferAttribute(nor, 3));
  if (g.attributes.uv) out.setAttribute('uv', g.attributes.uv); if (g.index) out.setIndex(g.index);
  return out;
}
// Meshes under a node, grouped by material name, merged in file-root space (pre = matrix applied first, e.g. the LOD spread undone).
// skin: bake skinned meshes in the scene's current pose. Returns [{ mat, geo }].
function bake(node, pre, skin, skip) {
  const by = {}, tmp = [];
  node.updateMatrixWorld(true);
  const walk = (o) => {
    if (skip && skip.indexOf(o.name) >= 0) return;
    if (o.isMesh) {
      const name = o.material.name;
      if (o.isSkinnedMesh) { if (skin) { const g = skinned(o); tmp.push(g); (by[name] || (by[name] = [])).push([g, pre.clone()]); } }
      else (by[name] || (by[name] = [])).push([o.geometry, pre.clone().multiply(o.matrixWorld)]);
    }
    for (const c of o.children) walk(c);
  };
  walk(node);
  const out = [];
  for (const k of Object.keys(by).sort()) out.push({ mat: k, geo: merge(by[k]) });
  for (const g of tmp) g.dispose();
  return out;
}
// LOD levels that do not stand on LOD0's floor (more than lodFloorM apart) are not used: the previous level stays to the end.
// Listed in kit.lodDropped (an art note for the owner; que_pair LOD2 lacks its 0.5 m footing).
function keepLevels(kit, name, levels) {
  const b0 = boxOf(levels[0]), out = [levels[0]];
  for (let i = 1; i < levels.length; i++) {
    const b = boxOf(levels[i]), dy = b.min.y - b0.min.y;
    if (Math.abs(dy) > PAL_ART.lodFloorM) { kit.lodDropped.push(name + ':' + i + ' floor ' + dy.toFixed(2) + ' m'); for (const p of levels[i]) p.geo.dispose(); continue; }
    out.push(levels[i]);
  }
  return out;
}
function boxOf(parts) { const b = new THREE.Box3(); for (const p of parts) b.union(p.geo.boundingBox); return b; }
function tris(parts) { let n = 0; for (const p of parts) n += p.geo.index.count / 3; return n; }

// ===================== Generated textures (no image files) =====================
function glowTex() {
  const N = 64, d = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const r = Math.hypot(x - N / 2 + 0.5, y - N / 2 + 0.5) / (N / 2), i = (y * N + x) * 4;
    const a = r < 0.06 ? 1 : r < 0.4 ? 1 - 0.45 * (r - 0.06) / 0.34 : r < 1 ? 0.55 * (1 - (r - 0.4) / 0.6) : 0;
    const c = r < 0.4 ? [255, 190 - 74 * r / 0.4, 110 - 68 * r / 0.4] : [232, 116, 42];
    d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = Math.round(255 * a);
  }
  const t = new THREE.DataTexture(d, N, N); t.colorSpace = THREE.SRGBColorSpace; t.magFilter = THREE.LinearFilter; t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true; t.needsUpdate = true; return t;
}
function rippleTex(rep) {
  const N = 128, d = new Uint8Array(N * N * 4);
  const W = [[3, 1, 0.5, 0], [1, 4, 0.35, 1.3], [5, -2, 0.25, 2.1], [-2, 7, 0.2, 0.7], [7, 3, 0.12, 4.0], [-5, -6, 0.15, 2.9], [11, -4, 0.06, 1.1]];
  const h = (x, y) => { let a = 0; for (const [fx, fy, A, ph] of W) a += A * Math.sin(2 * Math.PI * (fx * x + fy * y) / N + ph); return a; };
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const dx = (h(x + 1, y) - h(x - 1, y)) * 2.5, dy = (h(x, y + 1) - h(x, y - 1)) * 2.5, l = Math.hypot(dx, dy, 1), i = (y * N + x) * 4;
    d[i] = 128 - 127 * dx / l; d[i + 1] = 128 - 127 * dy / l; d[i + 2] = 128 + 127 / l; d[i + 3] = 255;
  }
  const t = new THREE.DataTexture(d, N, N); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(rep, rep); t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter; t.generateMipmaps = true; t.needsUpdate = true; return t;
}

// ===================== Files and textures the kit needs =====================
// GLB list for the loader: [{ key, url }] (key 'arch/wall_seg', 'ding', ...). base = asset root ('' or './').
export function files(base) {
  const C = PAL_ART, out = [];
  for (const n of C.archFiles) out.push({ key: 'arch/' + n, url: (base || '') + C.dir + 'arch/' + n + '.glb' });
  for (const n of C.propFiles) out.push({ key: n, url: (base || '') + C.dir + n + '.glb' });
  return out;
}
// Texture names the kit asks the loader for (CONFIG.LOAD folders: desk KTX2, phone set, PNG fallback), burnt variants included.
export function textureNames() {
  const s = new Set();
  for (const T of [PAL_ART.MATS, PAL_ART.PROP_MATS]) for (const k in T) { if (T[k].tex) s.add(T[k].tex); if (T[k].burnt) s.add(T[k].burnt); }
  return [...s].sort();
}

// ===================== Kit: shared materials and baked geometry (built once under card P) =====================
// gl: { key: parsed glTF } for every files() entry; tex(name): the loaded THREE.Texture or null (null = box colour fallback for that material);
// opts: { fow (the game's FOW uniforms), schools (CONFIG.SCHOOLS ids), phone (bool), maxAniso (renderer cap) }.
export function makeKit(gl, tex, opts) { const it = kitSteps(gl, tex, opts); let s; do s = it.next(); while (!s.done); return s.value; }
// The same build in steps for the card's job queue (one file per step, so a CONFIG.LOAD.sliceMs slice can stop between files):
// const it = kitSteps(...); each frame call it.next() until it returns { done: true, value: kit }.
export function* kitSteps(gl, tex, opts) {
  const C = PAL_ART, o = opts || {};
  const kit = { mats: {}, pmats: {}, burnt: {}, accent: [], banner: [], merc: {}, pieces: {}, props: {}, door: null, mercKit: null, clock: null,
    geos: [], matList: [], texList: [], missing: [], lodDropped: [], warm: null, schools: o.schools || [], phone: !!o.phone, lodDist: {}, ripples: [], rooms: 0 };
  const an = Math.min(C.aniso, o.maxAniso || C.aniso);
  const texFor = (name) => {
    const src = tex ? tex(name) : null;
    if (!src) { kit.missing.push(name); return null; }
    const t = src.clone(); t.colorSpace = THREE.SRGBColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; t.anisotropy = an; t.flipY = false; t.needsUpdate = true;
    kit.texList.push(t); return t;
  };
  const make = (spec, mapName, tint) => {
    const S = spec, p = { name: '' };
    if (mapName) { const t = texFor(mapName); if (t) p.map = t; }
    if (S.col !== undefined) p.color = new THREE.Color(S.col); else if (S.tint !== undefined) p.color = new THREE.Color(S.tint);
    if (tint) p.color = new THREE.Color(tint[0], tint[1], tint[2]);
    if (S.alpha) p.alphaTest = S.alpha;
    if (S.side === 2) p.side = THREE.DoubleSide;
    if (S.add) { p.transparent = true; p.depthWrite = false; p.blending = THREE.AdditiveBlending; }
    if (S.op !== undefined) { p.transparent = true; p.opacity = S.op; p.depthWrite = false; }
    if (S.poly) { p.polygonOffset = true; p.polygonOffsetFactor = -2; p.polygonOffsetUnits = -2; }
    let m;
    if (S.kind === 'basic') m = new THREE.MeshBasicMaterial(p);
    else if (S.kind === 'matcap') { const mt = p.map; delete p.map; if (mt) p.matcap = mt; m = new THREE.MeshMatcapMaterial(p); }
    else { p.roughness = S.rough !== undefined ? S.rough : 0.9; p.metalness = S.metal || 0; m = new THREE.MeshStandardMaterial(p); }
    fowHook(m, o.fow); kit.matList.push(m); return m;
  };
  for (const k in C.MATS) {
    const S = C.MATS[k];
    if (S.accent || S.banner || S.merc) continue;
    if (S.glow) { const t = glowTex(); kit.texList.push(t); const m = make(S, null); m.map = t; kit.mats[k] = m; continue; }
    kit.mats[k] = make(S, S.tex);
    if (S.burnt) kit.burnt[k] = make(S, S.burnt);
  }
  for (const k in C.PROP_MATS) kit.pmats[k] = make(C.PROP_MATS[k], C.PROP_MATS[k].tex);
  for (const st of ['idle', 'warn', 'hot']) {
    const L = C.merc[st], m = make(C.MATS.palMerc, C.MATS.palMerc.tex, L.col), r = rippleTex(C.merc.rippleRep);
    kit.texList.push(r); m.normalMap = r; m.normalScale.set(L.ns, L.ns); kit.merc[st] = m; kit.ripples.push(r, L.speed);
  }
  const lodD = (h) => { const L = C.lod, k = kit.phone ? L.phoneK : 1; return [h * L.focalPx / L.nearPx * k, h * L.focalPx / L.farPx * k]; };

  // Architecture pieces: one baked part per material, in piece space (origin and axes as the arch viewer places them).
  for (const n of C.archFiles) {
    yield;
    const g = gl['arch/' + n]; if (!g) { kit.missing.push('arch/' + n); continue; }
    const I = new THREE.Matrix4();
    if (n === 'door') {
      const by = (nm) => g.scene.getObjectByName(nm);
      kit.door = { frame: bake(by('door_frame'), I), leaves: [...bake(by('door_leaf_L'), I), ...bake(by('door_leaf_R'), I)], bar: bake(by('door_bar'), I) };
      for (const k of ['frame', 'leaves', 'bar']) for (const p of kit.door[k]) kit.geos.push(p.geo);
      continue;
    }
    const lods = [0, 1, 2].map((i) => g.scene.getObjectByName(n + '_lod' + i));
    if (lods[0]) {
      const levels = keepLevels(kit, n, lods.map((nd) => (nd ? bake(nd, I) : null)).filter(Boolean));
      for (const L of levels) for (const p of L) kit.geos.push(p.geo);
      const b = boxOf(levels[0]), h = b.max.y - Math.max(0, b.min.y);
      kit.props['arch/' + n] = { levels, states: {}, pose: {}, moving: null, h, dist: lodD(h), box: b }; kit.lodDist[n] = kit.props['arch/' + n].dist;
      continue;
    }
    const parts = bake(g.scene, I); for (const p of parts) kit.geos.push(p.geo);
    kit.pieces[n] = { parts, box: boxOf(parts), tris: tris(parts) };
  }

  // Props: LOD levels (the 17a GLBs spread LOD1/LOD2 along x for the viewers: the whole-metre spread is undone), state objects, poses.
  const spreadOf = (nd, b0) => { const b = new THREE.Box3().setFromObject(nd); return Math.round((b.min.x + b.max.x) / 2 - (b0.min.x + b0.max.x) / 2); };
  for (const n of C.propFiles) {
    yield;
    const g = gl[n]; if (!g) { kit.missing.push(n); continue; }
    const S = g.scene; S.updateMatrixWorld(true);
    if (n === 'merc') { kit.mercKit = mercKit(S); for (const k in kit.mercKit) for (const p of kit.mercKit[k].parts) kit.geos.push(p.geo); continue; }
    const P = { levels: [], states: {}, pose: {}, h: 0, dist: null, box: null, moving: null, accents: null };
    let mixer = null;
    const pose = (clipName, t) => {
      if (!mixer) mixer = new THREE.AnimationMixer(S);
      mixer.stopAllAction(); const clip = THREE.AnimationClip.findByName(g.animations, clipName);
      if (!clip) return false; const a = mixer.clipAction(clip); a.play(); mixer.setTime(t); S.updateMatrixWorld(true); return true;
    };
    const pre0 = C.lodNode[n] || n, l0 = S.getObjectByName(pre0 + '_lod0');
    if (n === 'beast' || n === 'standard') pose('idle', 0);
    const b0 = new THREE.Box3().setFromObject(l0);
    for (let i = 0; i < 3; i++) {
      const nd = i === 0 ? l0 : S.getObjectByName(pre0 + '_lod' + i); if (!nd) continue;
      const dx = i === 0 ? 0 : spreadOf(nd, b0), pre = new THREE.Matrix4().makeTranslation(-dx, 0, 0);
      if (n === 'clock' && i === 0) { P.levels.push(bake(nd, pre, false, ['clock_arrow', 'clock_catch', 'clock_water'])); continue; }
      P.levels.push(bake(nd, pre, true));
    }
    P.levels = keepLevels(kit, n, P.levels);
    if (n === 'beast') {
      // Strike windup: the strike clip time where a fore paw stands highest (the raised-claw tell), baked as a second LOD0 pose.
      const clip = THREE.AnimationClip.findByName(g.animations, 'strike'); let best = 0, bestY = -1e9;
      for (let k = 0; clip && k < C.beast.samples; k++) {
        const t = clip.duration * k / C.beast.samples; pose('strike', t);
        for (const bn of C.beast.windupBones) { const bo = S.getObjectByName(bn); if (bo) { bo.getWorldPosition(_v); if (_v.y > bestY) { bestY = _v.y; best = t; } } }
      }
      pose('strike', best); P.pose.windup = bake(l0, new THREE.Matrix4(), true); P.windupT = best; pose('idle', 0);
    }
    if (n === 'ding') { const d0 = S.getObjectByName('ding_lod0'); P.accents = (d0 && d0.userData && d0.userData.accents) || null; P.accentMetal = (d0 && d0.userData && d0.userData.accentMetal) || []; }
    const stateNames = { ding: ['ding_lit', 'ding_dry'], vat: ['vat_water', 'vat_cracks', 'vat_puddle'], crane: ['crane_smoke'], censer: ['censer_smoke'], lamp: ['lamp_flames'] }[n] || [];
    for (const sn of stateNames) { const nd = S.getObjectByName(sn); if (nd) P.states[sn] = bake(nd, new THREE.Matrix4()); }
    if (n === 'vat') {
      const sh = []; for (const c of S.children) if (c.name.startsWith('vat_shards')) sh.push(c);
      const grp = new THREE.Group(); for (const c of sh) grp.add(c.clone()); P.states.vat_shards = bake(grp, new THREE.Matrix4());
    }
    if (n === 'clock') P.moving = clockKit(S, g.animations, C.clockSteps);
    if (mixer) { mixer.stopAllAction(); mixer.uncacheRoot(S); }
    for (const L of P.levels) for (const p of L) kit.geos.push(p.geo);
    for (const k in P.states) for (const p of P.states[k]) kit.geos.push(p.geo);
    for (const k in P.pose) for (const p of P.pose[k]) kit.geos.push(p.geo);
    if (P.moving) for (const mv of P.moving.parts) for (const p of mv.parts) kit.geos.push(p.geo);
    P.box = boxOf(P.levels[0]); P.h = P.box.max.y - Math.max(0, P.box.min.y); P.dist = lodD(P.h); kit.lodDist[n] = P.dist;
    kit.props[n] = P;
  }
  // 鼎 accent and standard banner: one material per school (CONFIG.SCHOOLS order; one program each family).
  const dg = kit.props.ding;
  for (let i = 0; i < Math.max(9, kit.schools.length); i++) {
    const hex = dg && dg.accents && dg.accents[i] ? dg.accents[i] : '#b8862e', met = dg && dg.accentMetal ? dg.accentMetal[i] || 0 : 0;
    kit.accent.push(make({ col: new THREE.Color(hex).getHex(), metal: met, rough: met > 0 ? 0.35 : 0.85 }, null));
    const bm = make(C.MATS.palBanner, null), bt = texFor(C.MATS.palBanner.tex);
    if (bt) { bt.wrapS = bt.wrapT = THREE.ClampToEdgeWrapping; bt.offset.set((i % 5) * 0.2, Math.floor(i / 5) * 0.5); bm.map = bt; }
    kit.banner.push(bm);
  }
  kit.warm = warmGroup(kit);
  return kit;
}
// Water clock: each moving node's geometry in its own space, and its matrix (in clock space) for every level step 0..steps
// (level 1 = full, clip time 0; level 0 = empty, the clip's end). setClock copies one row; nothing is evaluated in play.
function clockKit(S, clips, steps) {
  const names = ['clock_arrow', 'clock_catch', 'clock_water'], mixer = new THREE.AnimationMixer(S), parts = [];
  const nodes = names.map((nm) => S.getObjectByName(nm)).filter(Boolean);
  for (const c of clips) mixer.clipAction(c).play();
  const dur = clips.length ? Math.max(...clips.map((c) => c.duration)) : 1;
  mixer.setTime(0); S.updateMatrixWorld(true);
  for (const nd of nodes) parts.push({ name: nd.name, parts: bake(nd, nd.matrixWorld.clone().invert()), table: new Float32Array((steps + 1) * 16) });
  for (let s = 0; s <= steps; s++) {
    mixer.setTime(Math.min(dur * s / steps, dur - 1e-4)); S.updateMatrixWorld(true);
    for (let i = 0; i < nodes.length; i++) parts[i].table.set(nodes[i].matrixWorld.elements, s * 16);
  }
  mixer.stopAllAction(); mixer.uncacheRoot(S);
  return { parts, steps };
}
// Mercury channel pieces from merc.glb's demo channel (2 x 6 m): node matrices as templates (rotation and scale), geometry per material.
function mercKit(S) {
  const pick = (nm) => { const nd = S.getObjectByName(nm); nd.updateMatrixWorld(true); return { m: nd.matrixWorld.clone(), parts: bake(nd, nd.matrixWorld.clone().invert()) }; };
  return { endA: pick('demo_end_00'), endB: pick('demo_end_10'), lipL: pick('demo_lipL_0'), lipR: pick('demo_lipR_0'), post: pick('demo_post_11'), surf: pick('demo_surface_00') };
}
// Warm-up rack: one tiny triangle per material, plain and instanced, so every program this module can use compiles under the card
// (states, burnt swaps and mercury looks included). warmOn places it in front of the warm camera; it never stays in the scene in play.
function warmGroup(kit) {
  const g = new THREE.Group(), tri = new THREE.BufferGeometry();
  tri.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-0.05, 0, 0, 0.05, 0, 0, 0, 0.08, 0]), 3));
  tri.setAttribute('normal', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1]), 3));
  tri.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 0.5, 1]), 2)); tri.computeBoundingSphere();
  kit.geos.push(tri); kit.warmInst = [];
  let i = 0;
  for (const m of kit.matList) {
    const a = new THREE.Mesh(tri, m); a.position.set((i % 20) * 0.11 - 1.1, Math.floor(i / 20) * 0.1 - 0.4, 0); a.updateMatrix(); a.matrixAutoUpdate = false; g.add(a);
    const b = new THREE.InstancedMesh(tri, m, 1); b.setMatrixAt(0, a.matrix); b.position.z = -0.01; b.updateMatrix(); b.matrixAutoUpdate = false; b.computeBoundingSphere(); g.add(b);
    kit.warmInst.push(b); i++;
  }
  g.matrixAutoUpdate = false;
  return g;
}

// ===================== Placement helpers (build time only) =====================
const _q = new THREE.Quaternion(), _up = new THREE.Vector3(0, 1, 0), _s = new THREE.Vector3(), _p = new THREE.Vector3();
function mat4(x, y, z, ry, sx) { return new THREE.Matrix4().compose(_p.set(x, y, z), _q.setFromAxisAngle(_up, ry || 0), _s.set(sx || 1, 1, 1)); }
// Side frames: along = unit vector of the piece's local +x along the edge, out = outward normal; the piece's local -z faces out.
const SIDE = { n: { ry: 0 }, s: { ry: Math.PI }, w: { ry: Math.PI / 2 }, e: { ry: -Math.PI / 2 } };
// Whole segments over [a, b] along a side (stretched by L / (4 n), n chosen closest to scale 1); d = distance inside the edge (negative = outside).
// Returns matrices for pieces whose local x runs 0..4 along the edge and local -z faces out of the room.
function runMats(side, r, a, b, d, seg) {
  const L = b - a; if (L < 0.05) return [];
  let n = Math.max(1, Math.round(L / seg)); if (Math.abs(Math.log(L / (seg * (n + 1)))) < Math.abs(Math.log(L / (seg * n)))) n++;
  if (n > 1 && Math.abs(Math.log(L / (seg * (n - 1)))) < Math.abs(Math.log(L / (seg * n)))) n--;
  const k = L / (seg * n), out = [];
  for (let i = 0; i < n; i++) {
    const u0 = a + i * seg * k, u1 = u0 + seg * k;
    if (side === 'n') out.push(mat4(u0, 0, r.z0 + d, 0, k));
    else if (side === 's') out.push(mat4(u1, 0, r.z1 - d, Math.PI, k));
    else if (side === 'w') out.push(mat4(r.x0 + d, 0, u1, Math.PI / 2, k));
    else out.push(mat4(r.x1 - d, 0, u0, -Math.PI / 2, k));
  }
  return out;
}
// Free stretches of [lo, up] outside the gaps [[g0, g1]].
function free(lo, up, gaps) {
  const g = gaps.slice().sort((p, q) => p[0] - q[0]), out = []; let u = lo;
  for (const [g0, g1] of g) { if (g0 - u > 0.01) out.push([u, Math.min(g0, up)]); u = Math.max(u, g1); }
  if (up - u > 0.01) out.push([u, up]);
  return out;
}
function sideOf(r, d) { return d.vert ? (d.e === r.x0 ? 'w' : d.e === r.x1 ? 'e' : '') : d.e === r.z0 ? 'n' : d.e === r.z1 ? 's' : ''; }
function edgeSpan(r, side) { return side === 'n' || side === 's' ? [r.x0, r.x1] : [r.z0, r.z1]; }
// Stretches of a side that face the lake (no other room on the far side of the edge).
function lakeRuns(r, side, rooms) {
  const [lo, up] = edgeSpan(r, side), cov = [];
  for (const o of rooms) {
    if (o === r) continue;
    const touch = side === 'n' ? o.z1 === r.z0 : side === 's' ? o.z0 === r.z1 : side === 'w' ? o.x1 === r.x0 : o.x0 === r.x1;
    if (!touch) continue;
    const a = side === 'n' || side === 's' ? Math.max(lo, o.x0) : Math.max(lo, o.z0), b = side === 'n' || side === 's' ? Math.min(up, o.x1) : Math.min(up, o.z1);
    if (b > a) cov.push([a, b]);
  }
  return free(lo, up, cov);
}
// Seeded generator (replays: never Math.random).
function rng(seed) { let s = seed >>> 0 || 1; return () => (s = (s * 16807) % 2147483647) / 2147483647; }

// ===================== Room art (17d) =====================
// One art group per palace room: added once into the room's group (it falls, detaches and burns with the room). r = index.html room
// { id, type, x0, x1, z0, z1, cx, cz, doors[] { vert, e, c, w }, school, spawn }, rooms = every room of the plan (lake-facing edges),
// spots = { pillars: [[x, z]], dais: [x, z] | null } from index.html's own box placement (pillar(), the core dais block), so render = collision.
// Returns art { group, floorMeshes, floorMats, solids [{ x0, x1, z0, z1 }] (new props only), replaces [box part keys], burn, inst, geos, props }.
export function buildRoom(kit, r, rooms, spots) {
  const C = PAL_ART, art = { room: r, group: new THREE.Group(), floorMeshes: [], floorMats: [], solids: [], replaces: (C.replaces[r.type] || []).slice(),
    burn: [], inst: [], geos: [], props: [], doors: [], skipped: 0, counts: { inst: 0, meshes: 0 } };
  art.group.name = 'palArt_' + r.id; kit.rooms++;
  if (!C.arch) { art.replaces.length = 0; finish(art); return art; }
  const acc = {}, blocked = (spots && spots.blocked) || [];
  const put = (piece, mats, over) => { if (!mats.length || !kit.pieces[piece]) return; (acc[piece] || (acc[piece] = { mats: [], over })).mats.push(...mats); };
  const tall = r.type === 'bridge' ? C.walls.bridge : C.walls[r.type] || C.walls.hall;
  const doorGaps = (side) => { const g = []; for (const d of r.doors) if (sideOf(r, d) === side) g.push([d.c - d.w / 2, d.c + d.w / 2]); return g; };
  // Walls exactly where index.html's box walls stand (north, west, east tall; south low; bridges low all round, long sides drawn by the bays).
  const longX = r.x1 - r.x0 >= r.z1 - r.z0;
  for (const side of ['n', 'w', 'e', 's']) {
    if (r.type === 'bridge' && ((longX && (side === 'n' || side === 's')) || (!longX && (side === 'w' || side === 'e')))) continue;
    const piece = side === 's' ? C.walls.low : tall, [lo, up] = edgeSpan(r, side), runs = free(lo, up, doorGaps(side));
    for (const [a, b] of runs) {
      const ms = runMats(side, r, a, b, C.wallIn, C.segM); put(piece, ms);
      if (C.on.eaves && side !== 's' && (r.type === 'hall' || r.type === 'corridor')) {
        put('eave_seg', ms);
        if (r.type === 'hall') put('tile_end', tileEndMats(ms));
      }
    }
  }
  if (C.on.terrace && r.type !== 'bridge') for (const side of ['n', 'w', 'e', 's']) for (const [a, b] of lakeRuns(r, side, rooms)) put('terrace_edge', runMats(side, r, a, b, 0, C.segM));
  // Pillars on the game's pillar spots.
  if (spots && spots.pillars) put('pillar', spots.pillars.map(([x, z]) => mat4(x, 0, z, 0)));
  // Floors drawn here (court, corridor, garden, bridge); hall and core keep the approved box floor.
  const fm = C.floors[r.type];
  if (fm && kit.mats[fm]) {
    const g = slabGeo(r.x0, r.x1, r.z0, r.z1, C.floorTh, C.tileM), m = new THREE.Mesh(g, kit.mats[fm]);
    m.receiveShadow = true; still(art, m); art.geos.push(g); art.floorMeshes.push(m); art.floorMats.push(kit.mats[fm]);
    if (kit.burnt[fm]) art.burn.push(m, kit.mats[fm], kit.burnt[fm]);
  }
  if (r.type === 'bridge') {
    const w = longX ? r.z1 - r.z0 : r.x1 - r.x0, piece = w > 10 ? 'bridge_bay_12' : 'bridge_bay_8', half = (kit.pieces[piece] ? kit.pieces[piece].box.max.z : 4.4) - 0.1;
    const sc = (w / 2 - C.bridge.railIn) / half, ms = [];
    if (longX) for (const m of runMats('n', r, r.x0, r.x1, 0, C.segM)) { m.multiply(new THREE.Matrix4().makeScale(1, 1, sc)); m.elements[13] = C.bridge.bayY; m.elements[14] = (r.z0 + r.z1) / 2; ms.push(m); }
    else for (const m of runMats('e', r, r.z0, r.z1, 0, C.segM)) { m.multiply(new THREE.Matrix4().makeScale(1, 1, sc)); m.elements[13] = C.bridge.bayY; m.elements[12] = (r.x0 + r.x1) / 2; ms.push(m); }
    put(piece, ms);
  }
  if (r.type === 'hall' && C.on.racks) hallRacks(kit, art, r, put, doorGaps('n'), blocked);
  if (r.type === 'garden' && C.on.plants) gardenPlants(kit, r, put, blocked);
  if (r.type === 'court' && C.on.flags) {
    const gaps = doorGaps('n'), F = C.flags;
    for (let i = 0; i < F.xs.length; i++) {
      const x = r.cx + F.xs[i]; if (x < r.x0 + 1 || x > r.x1 - 1 || gaps.some(([a, b]) => x > a - F.doorClear && x < b + F.doorClear)) continue;
      if (blocked.some((b) => x > b.x0 - 0.3 && x < b.x1 + 0.3 && r.z0 + F.z > b.z0 - 0.3 && r.z0 + F.z < b.z1 + 0.3)) { art.skipped++; continue; }
      put('flag_pole', [mat4(x, 0, r.z0 + F.z, 0)]); put('flag_' + F.ids[i], [mat4(x, F.y, r.z0 + F.z, 0)]);
    }
  }
  // Instanced pieces: one InstancedMesh per piece and material for this room; matrices frozen; shared geometry from the kit.
  for (const piece in acc) {
    const P = kit.pieces[piece], ms = acc[piece].mats, cast = !C.noShadow.some((p) => piece.startsWith(p));
    for (const part of P.parts) {
      const im = new THREE.InstancedMesh(part.geo, kit.mats[part.mat] || kit.mats.palStone, ms.length);
      for (let i = 0; i < ms.length; i++) im.setMatrixAt(i, ms[i]);
      im.castShadow = cast; im.receiveShadow = true; im.computeBoundingSphere(); still(art, im); art.inst.push(im);
      if (kit.burnt[part.mat]) art.burn.push(im, kit.mats[part.mat], kit.burnt[part.mat]);
    }
  }
  // Single pieces per room type.
  if (r.type === 'core' && spots && spots.dais && C.on.throne && kit.props['arch/throne_dais']) addProp(art, propLOD(kit, 'arch/throne_dais', spots.dais[0], 0, spots.dais[1], 0, { cast: true }));
  if (r.type === 'core' && spots && spots.dais && C.on.inlay && kit.mats.palStarInlay) coreInlay(kit, art, r, spots.dais);
  if (C.on.que && kit.props['arch/que_pair']) for (const q of C.que.at) if (q.room === r.id) {
    const x = q.side === 'w' ? r.x0 - C.que.out : q.side === 'e' ? r.x1 + C.que.out : r.cx, z = q.side === 'n' ? r.z0 - C.que.out : q.side === 's' ? r.z1 + C.que.out : r.cz;
    const d = r.doors.find((dd) => sideOf(r, dd) === q.side), along = d ? d.c : (q.side === 'w' || q.side === 'e' ? r.cz : r.cx);
    addProp(art, propLOD(kit, 'arch/que_pair', q.side === 'w' || q.side === 'e' ? x : along, 0, q.side === 'w' || q.side === 'e' ? along : z, q.side === 'w' || q.side === 'e' ? Math.PI / 2 : 0, { cast: true }));
  }
  if (C.props) roomDressing(kit, art, r, spots, blocked);
  finish(art);
  return art;
}
// A new prop's box against the room's existing solids and the art's own: overlapping ones are skipped and counted (art.skipped).
function hits(b, blocked, art) {
  for (const L of [blocked, art.solids]) for (const o of L) if (b.x0 < o.x1 && b.x1 > o.x0 && b.z0 < o.z1 && b.z1 > o.z0) { art.skipped++; return true; }
  return false;
}
function finish(art) { art.group.matrixAutoUpdate = false; art.group.updateMatrix(); art.counts.inst = art.inst.length; }
function still(art, o) { o.matrixAutoUpdate = false; o.updateMatrix(); art.group.add(o); art.counts.meshes++; return o; }
function addProp(art, h) { if (!h) return null; art.group.add(h.root); art.props.push(h); return h; }
// Floor slab: top at 0, world UVs (top faces x / tile, -z / tile; sides along / tile, height / tile), one float geometry.
function slabGeo(x0, x1, z0, z1, th, tile) {
  const g = new THREE.BoxGeometry(x1 - x0, th, z1 - z0); g.translate((x0 + x1) / 2, -th / 2, (z0 + z1) / 2);
  const P = g.attributes.position, N = g.attributes.normal, U = g.attributes.uv;
  for (let i = 0; i < P.count; i++) {
    const X = P.getX(i), Y = P.getY(i), Z = P.getZ(i);
    if (Math.abs(N.getY(i)) > 0.5) U.setXY(i, X / tile, -Z / tile); else U.setXY(i, (Math.abs(N.getX(i)) > 0.5 ? Z : X) / tile, Y / tile);
  }
  g.computeBoundingSphere(); return g;
}
// Tile ends along an eave: the segment's origin and rotation, the along-axis stretch applied to positions only (discs keep their size).
function tileEndMats(segs) {
  const T = PAL_ART.tileEnds, out = [], pos = new THREE.Vector3(), q = new THREE.Quaternion(), sc = new THREE.Vector3();
  for (const m of segs) {
    m.decompose(pos, q, sc);
    for (let i = 0; i < T.n; i++) { _v.set((T.x0 + i * T.step) * sc.x, T.y, T.z).applyQuaternion(q).add(pos); out.push(new THREE.Matrix4().compose(_v, q, _s.set(1, 1, 1))); }
  }
  return out;
}
// A20: racks along a hall's north wall between the corner lamps and clear of its door; bundles lie end-on on the shelves (arch viewer layout).
function hallRacks(kit, art, r, put, gaps, blocked) {
  const R = PAL_ART.racks, B = PAL_ART.bundles, rk = kit.pieces.slip_rack; if (!rk) return;
  const wall = kit.pieces[PAL_ART.walls.hall], face = PAL_ART.wallIn + (wall ? wall.box.max.z : 0.35), w = rk.box.max.x - rk.box.min.x;
  const zp = r.z0 + face + R.depth - rk.box.min.z, racks = [];
  for (let x = r.x0 + R.inset; x + w <= r.x1 - R.inset + 0.01 && racks.length < R.max; x += R.step) {
    if (gaps.some(([a, b]) => x + rk.box.max.x > a - R.doorClear && x + rk.box.min.x < b + R.doorClear)) continue;
    const box = { x0: x + rk.box.min.x, x1: x + rk.box.max.x, z0: zp + rk.box.min.z, z1: zp + rk.box.max.z };
    if (hits(box, blocked, art)) continue;
    racks.push(mat4(x, 0, zp, 0)); art.solids.push(box);
  }
  put('slip_rack', racks);
  const b = [];
  for (const M of racks) for (let k = 0; k < B.shelves; k++) for (let j = 0; j < B.per; j++) for (let l = 0; l < B.layers; l++) {
    if ((j * 5 + k * 3 + l) % B.skip === B.skip - 1) continue;
    b.push(M.clone().multiply(mat4(0.2 + j * 0.2 + l * 0.1, B.y0 + k * B.dy + l * 0.165, -0.08 - l * 0.04, Math.PI / 2 + ((j + k) % 3 - 1) * 0.05)));
  }
  put('slip_bundle', b);
}
// A16: planting cards in a band along the garden's walls, clear of doors, planters and curtains (seeded; replays see the same garden).
function gardenPlants(kit, r, put, blocked) {
  const P = PAL_ART.plants, rnd = rng(P.seed + r.x0 * 7 + r.z0 * 13), kinds = ['plant_wheat', 'plant_millet', 'plant_shrub', 'plant_grass'], beds = [[], [], [], []];
  const doorsXZ = r.doors.map((d) => (d.vert ? [d.e, d.c] : [d.c, d.e]));
  let n = 0;
  for (let i = 0; i < P.max * 12 && n < P.max; i++) {
    const x = r.x0 + 0.9 + rnd() * (r.x1 - r.x0 - 1.8), z = r.z0 + 0.9 + rnd() * (r.z1 - r.z0 - 1.8);
    const band = Math.min(x - r.x0, r.x1 - x, z - r.z0) < P.band; if (!band) continue;
    if (doorsXZ.some(([dx, dz]) => Math.hypot(x - dx, z - dz) < P.doorClear)) continue;
    if (blocked.some((b) => x > b.x0 - 0.6 && x < b.x1 + 0.6 && z > b.z0 - 0.6 && z < b.z1 + 0.6)) continue;
    const k = Math.floor(rnd() * 4), s = P.s0 + rnd() * (P.s1 - P.s0);
    beds[k].push(new THREE.Matrix4().compose(_p.set(x, 0, z), _q.setFromAxisAngle(_up, rnd() * 3), _s.set(s, s, s))); n++;
  }
  for (let k = 0; k < 4; k++) put(kinds[k], beds[k]);
}
// A17: star-map inlay cells in front of the dais (one InstancedMesh; cells turned and mirrored by a hash), receive only.
function coreInlay(kit, art, r, dais) {
  const I = PAL_ART.inlay, cells = [];
  for (let x = dais[0] - I.halfW; x < dais[0] + I.halfW - 0.01; x += I.cell) for (let z = dais[1] + I.zFromDais; z < r.z1 - I.zSouth - 0.01; z += I.cell) cells.push([x, z]);
  if (!cells.length) return;
  const g = new THREE.PlaneGeometry(I.cell, I.cell); g.rotateX(-Math.PI / 2); art.geos.push(g);
  const im = new THREE.InstancedMesh(g, kit.mats.palStarInlay, cells.length);
  for (let i = 0; i < cells.length; i++) {
    const h = ((i * 7 + 3) * 2654435761 >>> 0) % 8, M = mat4(cells[i][0] + I.cell / 2, I.y, cells[i][1] + I.cell / 2, (h % 4) * Math.PI / 2);
    if (h >= 4) M.multiply(new THREE.Matrix4().makeScale(-1, 1, 1)); im.setMatrixAt(i, M);
  }
  im.receiveShadow = true; im.castShadow = false; im.computeBoundingSphere(); still(art, im); art.inst.push(im);
}
// New decorative props per room type (17e): lamps in hall corners and beside the core dais, bells on the core walls, tally on the dais.
function roomDressing(kit, art, r, spots, blocked) {
  const C = PAL_ART, sol = (x, z, hx, hz) => { const b = { x0: x - hx, x1: x + hx, z0: z - hz, z1: z + hz }; if (hits(b, blocked, art)) return false; art.solids.push(b); return true; };
  if (C.on.lamps && kit.props.lamp) {
    const L = C.lamps, at = r.type === 'hall' ? [[r.x0 + L.inset, r.z0 + L.inset], [r.x1 - L.inset, r.z0 + L.inset]]
      : r.type === 'core' && spots && spots.dais ? [[spots.dais[0] - L.coreDx, spots.dais[1]], [spots.dais[0] + L.coreDx, spots.dais[1]]] : [];
    for (const [x, z] of at) if (sol(x, z, L.half, L.half)) addProp(art, prop(kit, 'lamp', x, z, 0));
  }
  if (r.type === 'core' && C.on.bells && kit.props.bells) {
    const B = C.bells;
    if (sol(r.x0 + B.inset, r.cz + B.dz, B.halfX, B.halfZ)) addProp(art, prop(kit, 'bells', r.x0 + B.inset, r.cz + B.dz, Math.PI / 2));
    if (sol(r.x1 - B.inset, r.cz + B.dz, B.halfX, B.halfZ)) addProp(art, prop(kit, 'bells', r.x1 - B.inset, r.cz + B.dz, -Math.PI / 2));
  }
  if (r.type === 'core' && C.on.tally && kit.props.tally && spots && spots.dais) addProp(art, prop(kit, 'tally', spots.dais[0] + C.tally.dx, spots.dais[1], 0, { y: C.tally.y }));
}

// ===================== Props (17e) =====================
// A single prop: THREE.LOD with the kit's merged levels (switch distances by the LOD rule), state objects beside it, matrices frozen.
// kind: 'beast' | 'ding' | 'vat' | 'crane' | 'censer' | 'clock' | 'huabiao' | 'lamp' | 'bells' | 'tally' | 'standard'. opts: { school (index in
// CONFIG.SCHOOLS), y, cast }. Returns a handle for the set* functions below; add handle.root to the room's art group (addTo) or any group.
export function prop(kit, kind, x, z, ry, opts) {
  if (!PAL_ART.props || !kit.props[kind]) return null;
  return propLOD(kit, kind, x, opts && opts.y || 0, z, ry, opts);
}
function propLOD(kit, kind, x, y, z, ry, opts) {
  const P = kit.props[kind], o = opts || {}, isProp = !kind.startsWith('arch/'), cast = o.cast !== undefined ? o.cast : P.h >= PAL_ART.shadowMinH;
  const h = { kind, root: new THREE.Group(), lod: new THREE.LOD(), lv0: null, idle: null, windup: null, states: {}, moving: [], step: -1, school: o.school || 0 };
  const matOf = (name) => {
    if (name === 'palAccent') return kit.accent[h.school] || kit.accent[0];
    if (name === 'palBanner') return kit.banner[h.school] || kit.banner[0];
    return (isProp && kit.pmats[name]) || kit.mats[name] || kit.mats.palDark;
  };
  const group = (parts, shadow) => {
    const g = new THREE.Group();
    for (const p of parts) {
      const m = new THREE.Mesh(p.geo, matOf(p.mat)), card = m.material.transparent || m.material.alphaTest > 0 || m.material.isMeshBasicMaterial;
      m.castShadow = shadow && !card; m.receiveShadow = !m.material.transparent; m.matrixAutoUpdate = false; m.updateMatrix(); g.add(m);
    }
    g.matrixAutoUpdate = false; return g;
  };
  const d = P.dist;
  for (let i = 0; i < P.levels.length; i++) {
    const g = group(P.levels[i], cast && i < 2);
    if (i === 0) {
      h.lv0 = new THREE.Group(); h.lv0.matrixAutoUpdate = false; h.idle = g; h.lv0.add(g);
      if (P.pose.windup) { h.windup = group(P.pose.windup, cast); h.windup.visible = false; h.lv0.add(h.windup); }
      if (P.moving) for (const mv of P.moving.parts) { const mg = group(mv.parts, false); mg.name = mv.name; mg.matrixAutoUpdate = false; h.moving.push(mg, mv.table); h.lv0.add(mg); }
      h.lod.addLevel(h.lv0, 0);
    } else h.lod.addLevel(g, i === 1 ? d[0] : d[1]);
  }
  for (const sn in P.states) { const g = group(P.states[sn], false); h.states[sn] = g; h.root.add(g); }
  h.lod.matrixAutoUpdate = false; h.lod.updateMatrix(); h.root.add(h.lod);
  h.root.position.set(x, y, z); h.root.rotation.y = ry || 0; h.root.updateMatrix(); h.root.matrixAutoUpdate = false;
  if (kind === 'ding') setDing(h, true);
  if (kind === 'vat') setVat(h, 0);
  if (kind === 'clock') setClock(h, 1);
  return h;
}
// 鼎 one per school hall (replaces the healing altar's box): lit coals and halo, or the dry ash crust.
export function ding(kit, x, z, school) { return prop(kit, 'ding', x, z, 0, { school }); }
// School standard (C12) beside a hall's 鼎, toward the room centre in x; skipped (null) if its pole box meets a solid. Adds its solid to art.
export function standard(kit, art, r, dingX, dingZ, school, blocked) {
  const S = PAL_ART.standard; if (!PAL_ART.on.standards || !kit.props.standard) return null;
  const x = dingX + (r.cx >= dingX ? S.dx : -S.dx), b = { x0: x - S.half, x1: x + S.half, z0: dingZ - S.half, z1: dingZ + S.half };
  if (hits(b, blocked || [], art)) return null;
  art.solids.push(b); return addTo(art, prop(kit, 'standard', x, dingZ, 0, { school }));
}
// Mercury channel (C7) over the game's channel box (x0..x1, z0..z1): bronze lips, ends and posts merged per material, and the matcap
// surface as one mesh whose material setMerc swaps between the three looks (all three compiled under the card by the warm rack).
export function mercury(kit, x0, x1, z0, z1) {
  const K = kit.mercKit; if (!PAL_ART.props || !K) return null;
  const alongX = x1 - x0 > z1 - z0, W = Math.max(1, Math.round(alongX ? z1 - z0 : x1 - x0)), L = Math.max(1, Math.round(alongX ? x1 - x0 : z1 - z0));
  const cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, rot = mat4(cx, 0, cz, alongX ? Math.PI / 2 : 0), by = {}, surf = [], o = PAL_ART.merc.lipOut;
  const add = (tpl, lx, lz, list) => { const m = tpl.m.clone(); m.elements[12] = lx; m.elements[14] = lz; const M = rot.clone().multiply(m); for (const p of tpl.parts) (list ? surf : (by[p.mat] || (by[p.mat] = []))).push([p.geo, M]); };
  for (let i = 0; i < W; i++) for (let j = 0; j < L; j++) add(K.surf, i + 0.5 - W / 2, j + 0.5 - L / 2, true);
  for (let j = 0; j < L; j++) { add(K.lipL, -(W / 2 + o), j + 0.5 - L / 2); add(K.lipR, W / 2 + o, j + 0.5 - L / 2); }
  for (let i = 0; i < W; i++) { add(K.endA, i + 0.5 - W / 2, -(L / 2 + o)); add(K.endB, i + 0.5 - W / 2, L / 2 + o); }
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) add(K.post, sx * (W / 2 + o), sz * (L / 2 + o));
  const h = { kind: 'merc', root: new THREE.Group(), surface: null, geos: [], state: 'idle', idleMat: kit.merc.idle };
  for (const k in by) { const g = merge(by[k]), m = new THREE.Mesh(g, kit.mats[k] || kit.mats.palBronze); m.receiveShadow = true; m.matrixAutoUpdate = false; h.root.add(m); h.geos.push(g); }
  const sg = merge(surf); h.geos.push(sg); h.surface = new THREE.Mesh(sg, kit.merc.idle); h.surface.matrixAutoUpdate = false; h.root.add(h.surface);
  h.root.matrixAutoUpdate = false;
  return h;
}
// Door (B3) on an index.html door { vert, e, c }: frame, leaves (shown while shut) and the bronze bar (shown while locked).
export function door(kit, d) {
  if (!PAL_ART.arch || !kit.door) return null;
  const h = { kind: 'door', root: new THREE.Group(), leaves: null, bar: null }, D = kit.door;
  h.burn = [];
  const grp = (parts, cast) => {
    const g = new THREE.Group();
    for (const p of parts) {
      const m = new THREE.Mesh(p.geo, kit.mats[p.mat] || kit.mats.palDoor); m.castShadow = cast; m.receiveShadow = true; m.matrixAutoUpdate = false; g.add(m);
      if (kit.burnt[p.mat]) h.burn.push(m, kit.mats[p.mat], kit.burnt[p.mat]);
    }
    g.matrixAutoUpdate = false; return g;
  };
  h.root.add(grp(D.frame, true)); h.leaves = grp(D.leaves, true); h.root.add(h.leaves); h.bar = grp(D.bar, false); h.bar.visible = false; h.root.add(h.bar);
  const x = d.vert ? d.e : d.c, z = d.vert ? d.c : d.e;
  h.root.position.set(x, 0, z); h.root.rotation.y = d.vert ? Math.PI / 2 : 0; h.root.updateMatrix(); h.root.matrixAutoUpdate = false;
  return h;
}
// Black lake (A15) on the game's lake plane: material and repeat set once; lakeRevert puts the box material back (Royal Rumble).
export function lakeApply(kit, mesh) {
  const m = kit.mats.palLake; if (!PAL_ART.on.lake || !m || !mesh) return false;
  const w = mesh.geometry.parameters ? mesh.geometry.parameters.width : 400;
  if (m.map) m.map.repeat.set(w / PAL_ART.lakeTileM, w / PAL_ART.lakeTileM);
  kit.lakeOld = kit.lakeOld || []; kit.lakeOld.push(mesh, mesh.material); mesh.material = m; return true;
}
export function lakeRevert(kit) { const L = kit.lakeOld || []; for (let i = 0; i < L.length; i += 2) L[i].material = L[i + 1]; L.length = 0; }

// ===================== State changes and the per-frame tick (no allocation, no lookups) =====================
// PERFRAME-BEGIN
// Burnt wing (A18): every timber, earth, plaster, lacquer and slip surface of the room swaps to its burnt material (on false = fresh).
export function setBurnt(art, on) {
  const B = art.burn;
  for (let i = 0; i < B.length; i += 3) B[i].material = on ? B[i + 2] : B[i + 1];
  for (let k = 0; k < art.doors.length; k++) { const D = art.doors[k].burn; for (let i = 0; i < D.length; i += 3) D[i].material = on ? D[i + 2] : D[i + 1]; }
  art.burnt = on;
}
// Door shut (leaves shown) or open (leaves hidden, as the game's panel); the bar shows while locked.
export function setDoor(h, open, locked) { if (!h) return; h.leaves.visible = !open; h.bar.visible = !!locked; }
// 鼎 lit (coals, embers, halo) or dry (ash crust).
export function setDing(h, lit) { if (!h) return; const s = h.states; if (s.ding_lit) s.ding_lit.visible = !!lit; if (s.ding_dry) s.ding_dry.visible = !lit; h.lit = !!lit; }
// Vat: 0 intact (body and water), 1 cracked (spray cracks: the tell), 2 broken (pooled shards and the puddle; body hidden).
export function setVat(h, st) {
  if (!h) return; const s = h.states;
  h.lod.visible = st < 2; if (s.vat_water) s.vat_water.visible = st < 2; if (s.vat_cracks) s.vat_cracks.visible = st === 1;
  if (s.vat_shards) s.vat_shards.visible = st >= 2; if (s.vat_puddle) s.vat_puddle.visible = st >= 2; h.st = st;
}
// Water clock level 0..1 (1 full): the moving parts take the precomputed matrices of the nearest step (written only when the step changes).
export function setClock(h, level) {
  if (!h || !h.moving.length) return;
  const n = PAL_ART.clockSteps, s = Math.max(0, Math.min(n, Math.round((1 - level) * n)));
  if (s === h.step) return;
  h.step = s;
  for (let i = 0; i < h.moving.length; i += 2) { const g = h.moving[i]; g.matrix.fromArray(h.moving[i + 1], s * 16); g.matrixWorldNeedsUpdate = true; }
}
// Bronze beast: the strike windup pose (raised claw) while its tell runs, the idle pose otherwise (LOD0; far levels keep one pose).
export function setBeast(h, windup) { if (!h || !h.windup) return; h.windup.visible = !!windup; h.idle.visible = !windup; }
// Mercury look: 'idle' | 'warn' | 'hot'.
export function setMerc(kit, h, state) { if (!h) return; h.surface.material = kit.merc[state] || kit.merc.idle; h.state = state; }
// Every frame while the palace is drawn: the three mercury ripple maps slide (the shimmer). dt in seconds (the game's clamped dt).
export function tick(kit, dt) {
  const R = kit.ripples;
  for (let i = 0; i < R.length; i += 2) { R[i].offset.x = (R[i].offset.x + R[i + 1] * dt) % 1; R[i].offset.y = (R[i].offset.y + R[i + 1] * dt * 0.37) % 1; }
}
// PERFRAME-END

// ===================== Warm-up, reset, dispose =====================
// Card P warm draw: the warm rack (every material, plain and instanced) in front of the camera, and every prop state shown, for one draw.
export function warmOn(kit, scene, camera, arts) {
  const g = kit.warm; camera.updateMatrixWorld();
  _v.set(0, 0, -2).applyMatrix4(camera.matrixWorld); g.position.copy(_v); g.quaternion.copy(camera.quaternion); g.updateMatrix(); g.updateMatrixWorld(true);
  scene.add(g);
  for (const a of arts || []) {
    for (const p of a.props) { for (const k in p.states) p.states[k].visible = true; if (p.windup) p.windup.visible = true; if (p.kind === 'vat') p.lod.visible = true; }
    for (const d of a.doors) d.bar.visible = true;
  }
}
// After the warm draw: the rack leaves the scene and every prop goes back to its rest state.
export function warmOff(kit, scene, arts) { scene.remove(kit.warm); for (const a of arts || []) resetRoom(a); }
// New run: the room's art back to rest (fresh materials, doors shut and unlocked, 鼎 lit, vats whole, clocks full, beasts idle, mercury calm).
export function resetRoom(art) {
  setBurnt(art, false);
  for (const d of art.doors) setDoor(d, false, false);
  for (const p of art.props) {
    if (p.kind === 'ding') setDing(p, true); else if (p.kind === 'vat') setVat(p, 0); else if (p.kind === 'clock') { p.step = -1; setClock(p, 1); }
    else if (p.kind === 'beast') setBeast(p, false); else if (p.kind === 'merc') { p.surface.material = p.idleMat; p.state = 'idle'; }
    for (const k in p.states) if (p.kind !== 'ding' && p.kind !== 'vat') p.states[k].visible = true;
  }
}
// Doors and loose props (built by the integration at the box code's place) join the room's art so reset, burn and dispose reach them.
export function addTo(art, h) {
  if (!h) return null;
  if (h.kind === 'door') art.doors.push(h); else art.props.push(h);
  if (h.kind !== 'door') art.group.add(h.root);
  return h;
}
// The room's own GPU objects: instanced pieces (their instance buffers), floors, inlay quads and mercury channel geometry.
// Shared kit geometry and materials stay until disposeKit.
export function disposeRoom(art) {
  for (const im of art.inst) im.dispose();
  for (const g of art.geos) g.dispose();
  for (const p of art.props) if (p.geos) for (const g of p.geos) g.dispose();
  if (art.group.parent) art.group.parent.remove(art.group);
  art.inst.length = 0; art.geos.length = 0; art.props.length = 0; art.doors.length = 0; art.burn.length = 0;
}
// The palace set leaves (Royal Rumble picked): every kit geometry, material and texture clone this module made.
export function disposeKit(kit) {
  lakeRevert(kit);
  for (const b of kit.warmInst || []) b.dispose();
  for (const g of kit.geos) g.dispose();
  for (const m of kit.matList) m.dispose();
  for (const t of kit.texList) t.dispose();
  kit.geos.length = 0; kit.matList.length = 0; kit.texList.length = 0; kit.props = {}; kit.pieces = {}; kit.door = null; kit.mercKit = null;
}
// Counts for the card ledger and the HOOKS doc: geometries, materials, textures, missing files or images, LOD distances per prop.
export function info(kit) {
  return { geos: kit.geos.length, mats: kit.matList.length, texs: kit.texList.length, missing: kit.missing.slice(), lodDropped: kit.lodDropped.slice(), lodDist: kit.lodDist, rooms: kit.rooms,
    windupT: kit.props.beast ? kit.props.beast.windupT : null };
}
