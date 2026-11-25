// Pooled painted cards (PREP-AV 25 Nov; ported from art/vfx/cards_reference.js, spec docs/VFX.md "Card system").
// One draw per atlas (InstancedBufferGeometry + ShaderMaterial), fixed pools built at load. spawnK() writes one instance's attributes
// (no allocation); the flipbook frame, the tell hold and the release all come from time in the vertex shader, so the per-frame CPU cost is
// one uniform (uTime = game time: pause freezes every card) plus position writes for cards that follow a moving body.
// Atlas texels: R = value, G = alpha (RG8, linear, no mipmaps). Colour = ramp row (school, apex, rebel or neutral) at the value.
// Differences from the reference: the card index is stored per slot (release needs no name), cards are addressed by index (no string
// lookup per spawn), the culling sphere follows the room (setSphere), counts and dispose for tests and level changes.

export function makeCards(THREE, meta, tex, ramp, opts) {
  const o = opts || {};
  const POOL = Object.assign({ soft_a: 64, soft_b: 48, ground: 48 }, o.pool || {});
  const names = Object.keys(meta.effects), NFX = names.length, idx = {};
  names.forEach((n, i) => { idx[n] = i; });
  const rows = meta.ramps.rows, nRows = rows.length;
  const VS = `#define NFX ${NFX}
attribute vec4 iA; attribute vec4 iB; attribute vec4 iC;
uniform float uTime; uniform vec4 uFxA[NFX]; uniform vec4 uFxB[NFX]; uniform vec4 uFxC[NFX]; uniform vec4 uFxD[NFX];
varying vec2 vUv; varying float vRow; varying float vAlpha; varying float vAsh;
#include <fog_pars_vertex>
void main() {
  int k = int(iC.x + 0.5); vec4 A = uFxA[k]; vec4 B = uFxB[k]; vec4 C = uFxC[k]; vec4 D = uFxD[k];
  float t = uTime - iA.w; float f = floor(t * C.z);
  if (D.x > C.w) { if (uTime < iB.x) { if (f >= C.w) f = C.w + mod(f - C.w, D.x - C.w); } else f = D.x + floor((uTime - iB.x) * C.z); }
  bool dead = t < 0.0 || f >= B.w || iC.z <= 0.0;
  vec2 local = vec2((position.x - C.x) * iB.z, (position.y - (1.0 - C.y)) * iB.w);
  float c = cos(iB.y), s = sin(iB.y);
  vec4 mvPosition;
  if (D.y < 0.5) { mvPosition = modelViewMatrix * vec4(iA.xyz, 1.0); mvPosition.xy += vec2(c * local.x - s * local.y, s * local.x + c * local.y); }
  else { vec3 w = iA.xyz + vec3(c, 0.0, s) * local.x + vec3(s, 0.0, -c) * local.y; mvPosition = modelViewMatrix * vec4(w, 1.0); }
  gl_Position = projectionMatrix * mvPosition;
  if (dead) gl_Position = vec4(2.0, 2.0, 2.0, 1.0);
  vec2 cell = vec2(mod(f, B.z), floor(f / B.z));
  vUv = A.xy + cell * B.xy + vec2(position.x, 1.0 - position.y) * A.zw;
  vRow = iC.y; vAlpha = iC.z; vAsh = D.z;
  #include <fog_vertex>
}`;
  const FS = (cut) => `uniform sampler2D map; uniform sampler2D ramp; uniform float uRampW; uniform float uAshV;
varying vec2 vUv; varying float vRow; varying float vAlpha; varying float vAsh;
#include <fog_pars_fragment>
void main() {
  vec2 va = texture2D(map, vUv).rg; float a = va.y * vAlpha;
  float rx = va.x * (uRampW - 1.0) / uRampW + 0.5 / uRampW;
  vec3 col = mix(texture2D(ramp, vec2(rx, vRow)).rgb, texture2D(ramp, vec2(rx, uAshV)).rgb, vAsh);
#ifdef USE_FOG
  col = mix(col, fogColor, smoothstep(fogNear, fogFar, vFogDepth));
#endif
  vec3 o = linearToOutputTexel(vec4(col, 1.0)).rgb;
${cut ? `#ifdef ALPHA_TO_COVERAGE
  float w = max(fwidth(a), 1e-4); a = smoothstep(0.5 - w, 0.5 + w, a); if (a <= 0.0) discard;
#else
  if (a < 0.5) discard; a = 1.0;
#endif
  gl_FragColor = vec4(o, a);` : `if (a < 0.004) discard;
  gl_FragColor = vec4(o * a, a);`}
}`;
  const quad = new THREE.BufferGeometry();
  quad.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0], 3));
  quad.setIndex([0, 1, 2, 0, 2, 3]);
  const U = { A: [], B: [], C: [], D: [] };
  // Per card constants as plain numbers too (spawn reads these, not the effect objects).
  const kFrames = new Float32Array(NFX), kFps = new Float32Array(NFX), kL0 = new Float32Array(NFX), kL1 = new Float32Array(NFX);
  const kW = new Float32Array(NFX), kH = new Float32Array(NFX), kAnchor = new Float32Array(NFX), kGround = new Uint8Array(NFX), kAtlas = new Uint8Array(NFX);
  const atlasNames = Object.keys(meta.atlases);
  names.forEach((n, i) => {
    const e = meta.effects[n], W = e.atlasSize[0], H = e.atlasSize[1];
    U.A.push(new THREE.Vector4(e.originPx[0] / W, e.originPx[1] / H, e.cellPx[0] / W, e.cellPx[1] / H));
    U.B.push(new THREE.Vector4(e.stridePx[0] / W, e.stridePx[1] / H, e.cols, e.frames));
    U.C.push(new THREE.Vector4(e.pivotPx[0] / e.cellPx[0], e.pivotPx[1] / e.cellPx[1], e.fps, e.loop ? e.loop[0] : 0));
    U.D.push(new THREE.Vector4(e.loop ? e.loop[1] : 0, e.orient === 'ground' ? 1 : 0, e.ashMix || 0, 0));
    kFrames[i] = e.frames; kFps[i] = e.fps; kL0[i] = e.loop ? e.loop[0] : -1; kL1[i] = e.loop ? e.loop[1] : -1;
    kW[i] = e.sizeM[0]; kH[i] = e.sizeM[1]; kAnchor[i] = e.anchorHeightM || 0; kGround[i] = e.orient === 'ground' ? 1 : 0;
    kAtlas[i] = atlasNames.indexOf(e.atlas);
  });
  const pools = [], uTime = { value: 0 };
  for (let ai = 0; ai < atlasNames.length; ai++) {
    const an = atlasNames[ai], cut = meta.atlases[an].blend === 'cut', n = POOL[an];
    const g = new THREE.InstancedBufferGeometry();
    g.index = quad.index; g.setAttribute('position', quad.getAttribute('position'));
    const a = new Float32Array(n * 4), b = new Float32Array(n * 4), c = new Float32Array(n * 4);
    const A = new THREE.InstancedBufferAttribute(a, 4), B = new THREE.InstancedBufferAttribute(b, 4), C = new THREE.InstancedBufferAttribute(c, 4);
    A.setUsage(THREE.DynamicDrawUsage); B.setUsage(THREE.DynamicDrawUsage); C.setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('iA', A); g.setAttribute('iB', B); g.setAttribute('iC', C); g.instanceCount = n;
    // Culling stays on: one sphere round the current room, moved by setSphere on a room change (never frustumCulled = false).
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), o.sphereR || 40);
    const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS(cut), fog: true, side: THREE.DoubleSide,
      uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, { map: { value: null }, ramp: { value: null }, uRampW: { value: meta.ramps.width },
        uAshV: { value: (rows.indexOf('ash') + 0.5) / nRows }, uFxA: { value: U.A }, uFxB: { value: U.B }, uFxC: { value: U.C }, uFxD: { value: U.D } }]) });
    mat.uniforms.map.value = tex[an]; mat.uniforms.ramp.value = ramp; mat.uniforms.uTime = uTime;
    if (cut) { mat.alphaToCoverage = true; mat.transparent = false; mat.depthWrite = true; mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -2; }
    else { mat.transparent = true; mat.depthWrite = false; mat.premultipliedAlpha = true; mat.blending = THREE.NormalBlending; }
    const mesh = new THREE.Mesh(g, mat);
    mesh.matrixAutoUpdate = false; mesh.renderOrder = cut ? 1 : 3; mesh.name = 'fxcards_' + an;
    pools.push({ name: an, mesh, g, A, B, C, a, b, c, end: new Float64Array(n).fill(-1), kc: new Int16Array(n), n, next: 0 });
  }
  const HOLD_NONE = 1e9;

  // PERFRAME-BEGIN (per-event card writes: typed arrays only, no allocation)
  // k = card index (idx[name]); x y z = anchor; row = ramp row index; sx, sy = scale of the card's own size (sx < 0 mirrors);
  // rot = screen angle (upright) or yaw (ground: forward = (sin, 0, -cos)); hold = seconds a tell or state loop is held (0 = none: a
  // full-loop card then loops until kill); alpha 0..1. Returns a handle (atlas << 8 | slot), the oldest slot is reused when the pool is full.
  function spawnK(k, x, y, z, row, sx, sy, rot, hold, alpha) {
    const p = pools[kAtlas[k]], now = uTime.value;
    let s = -1;
    for (let i = 0; i < p.n; i++) { const j = (p.next + i) % p.n; if (p.end[j] < now) { s = j; break; } }
    if (s < 0) s = p.next;
    p.next = (s + 1) % p.n;
    const l0 = kL0[k], l1 = kL1[k], fr = kFrames[k], fps = kFps[k], lp = l0 >= 0, held = lp && hold > 0;
    const holdEnd = held ? now + hold : (lp && l1 < fr ? now + l0 / fps : HOLD_NONE);
    const s4 = s * 4;
    p.a[s4] = x; p.a[s4 + 1] = y + (kGround[k] ? 0.02 : kAnchor[k] * (sy < 0 ? -sy : sy)); p.a[s4 + 2] = z; p.a[s4 + 3] = now;
    p.b[s4] = holdEnd; p.b[s4 + 1] = rot; p.b[s4 + 2] = kW[k] * sx; p.b[s4 + 3] = kH[k] * sy;
    p.c[s4] = k; p.c[s4 + 1] = (row + 0.5) / nRows; p.c[s4 + 2] = alpha; p.c[s4 + 3] = 0;
    p.end[s] = lp && !held && l1 >= fr ? HOLD_NONE : (held ? holdEnd + (fr - l1) / fps : now + fr / fps) + 0.05;
    p.kc[s] = k;
    p.A.addUpdateRange(s4, 4); p.B.addUpdateRange(s4, 4); p.C.addUpdateRange(s4, 4);
    p.A.needsUpdate = true; p.B.needsUpdate = true; p.C.needsUpdate = true;
    return (kAtlas[k] << 8) | s;
  }
  // Move a following card (a bolt in flight, an aura on a walking suit). y = the anchor y as passed to spawnK.
  function move(hd, x, y, z) {
    if (hd < 0) return;
    const p = pools[hd >> 8], s = hd & 255, k = p.kc[s], s4 = s * 4;
    p.a[s4] = x; p.a[s4 + 1] = y + (kGround[k] ? 0.02 : kAnchor[k] * Math.abs(p.b[s4 + 3] / kH[k])); p.a[s4 + 2] = z;
    p.A.addUpdateRange(s4, 3); p.A.needsUpdate = true;
  }
  // End a held tell or state loop now: its release frames play, then it is free.
  function release(hd) {
    if (hd < 0) return;
    const p = pools[hd >> 8], s = hd & 255, k = p.kc[s], now = uTime.value;
    if (p.end[s] < now) return;
    p.b[s * 4] = now; p.B.addUpdateRange(s * 4, 1); p.B.needsUpdate = true;
    p.end[s] = now + (kFrames[k] - (kL1[k] >= 0 ? kL1[k] : 0)) / kFps[k] + 0.05;
  }
  // Remove a card at once (caster killed, state ended with no release).
  function kill(hd) {
    if (hd < 0) return;
    const p = pools[hd >> 8], s = hd & 255;
    p.c[s * 4 + 2] = 0; p.end[s] = -1; p.C.addUpdateRange(s * 4 + 2, 1); p.C.needsUpdate = true;
  }
  // Live cards (tests and the debug line).
  function live() {
    let n = 0; const now = uTime.value;
    for (let i = 0; i < pools.length; i++) { const p = pools[i]; for (let j = 0; j < p.n; j++) if (p.end[j] >= now) n++; }
    return n;
  }
  // PERFRAME-END

  // Every card off (new run, scene change): no allocation.
  function clear() {
    for (let i = 0; i < pools.length; i++) {
      const p = pools[i];
      for (let j = 0; j < p.n; j++) { p.end[j] = -1; p.c[j * 4 + 2] = 0; }
      p.C.clearUpdateRanges(); p.C.needsUpdate = true; p.next = 0;
    }
  }
  // Culling sphere round the current room (called on a room change only).
  function setSphere(x, y, z, r) {
    for (let i = 0; i < pools.length; i++) { const bs = pools[i].g.boundingSphere; bs.center.set(x, y, z); bs.radius = r; }
  }
  // Leaving for good (shared keep-flagged otherwise): geometries, materials and the four textures.
  function dispose() {
    for (let i = 0; i < pools.length; i++) { const p = pools[i]; if (p.mesh.parent) p.mesh.parent.remove(p.mesh); p.g.dispose(); p.mesh.material.dispose(); }
    quad.dispose();
    for (const k in tex) tex[k].dispose();
    ramp.dispose();
  }
  return { pools, meshes: pools.map((p) => p.mesh), uTime, spawnK, move, release, kill, live, clear, setSphere, dispose, idx, rows, kGround, kW, kH };
}

// Loading: atlases as RG8 data (fetch + createImageBitmap, no premultiply, no colour conversion; no <img>, so the page load event is never held).
export async function loadCards(THREE, base) {
  const meta = await (await fetch(base + 'vfx.json')).json();
  const bm = async (f, o) => createImageBitmap(await (await fetch(base + f)).blob(), o);
  const tex = {};
  for (const n of Object.keys(meta.atlases)) {
    const t = new THREE.Texture(await bm(meta.atlases[n].file, { premultiplyAlpha: 'none', colorSpaceConversion: 'none' }));
    t.format = THREE.RGFormat; t.flipY = false; t.generateMipmaps = false;
    t.minFilter = THREE.LinearFilter; t.magFilter = THREE.LinearFilter; t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true; tex[n] = t;
  }
  const ramp = new THREE.Texture(await bm(meta.ramps.file, { premultiplyAlpha: 'none' }));
  ramp.flipY = false; ramp.generateMipmaps = false; ramp.minFilter = THREE.LinearFilter; ramp.magFilter = THREE.LinearFilter;
  ramp.colorSpace = THREE.SRGBColorSpace; ramp.needsUpdate = true;
  return { meta, tex, ramp };
}
