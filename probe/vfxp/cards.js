// Pooled painted cards (VFXP, 25 Nov; reference implementation of docs/VFX.md "Card system"; the game writer ports it into index.html).
// One InstancedMesh-like draw per atlas (InstancedBufferGeometry + ShaderMaterial), a fixed pool of instances built at load; spawn() writes one
// instance's attributes (no allocation); the flipbook frame, the tell hold and the release all come from time in the vertex shader, so the
// per-frame cost on the CPU is one uniform (uTime) plus position writes for cards that follow a moving body.
// Atlas texels: R = value, G = alpha (RG8, linear, no mipmaps). Colour = ramp texture row (school / apex / rebel / neutral) at the value.
export function makeCards(THREE, meta, tex, ramp, opts = {}) {
  const POOL = Object.assign({ soft_a: 64, soft_b: 48, ground: 48 }, opts.pool || {});
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
  // smoke: the ash row mixed over the caster's row (vAsh = the card's ashMix), so the school colour is only a tint
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
  quad.setAttribute('position', new THREE.Float32BufferAttribute([0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0], 3)); quad.setIndex([0, 1, 2, 0, 2, 3]);
  const U = { A: [], B: [], C: [], D: [] };
  for (const n of names) {
    const e = meta.effects[n], [W, H] = e.atlasSize;
    U.A.push(new THREE.Vector4(e.originPx[0] / W, e.originPx[1] / H, e.cellPx[0] / W, e.cellPx[1] / H));
    U.B.push(new THREE.Vector4(e.stridePx[0] / W, e.stridePx[1] / H, e.cols, e.frames));
    U.C.push(new THREE.Vector4(e.pivotPx[0] / e.cellPx[0], e.pivotPx[1] / e.cellPx[1], e.fps, e.loop ? e.loop[0] : 0));
    U.D.push(new THREE.Vector4(e.loop ? e.loop[1] : 0, e.orient === 'ground' ? 1 : 0, e.ashMix || 0, 0));
  }
  const pools = {}, uTime = { value: 0 };
  for (const an of Object.keys(meta.atlases)) {
    const cut = meta.atlases[an].blend === 'cut', n = POOL[an];
    const g = new THREE.InstancedBufferGeometry(); g.index = quad.index; g.setAttribute('position', quad.getAttribute('position'));
    const a = new Float32Array(n * 4), b = new Float32Array(n * 4), c = new Float32Array(n * 4);
    const A = new THREE.InstancedBufferAttribute(a, 4), B = new THREE.InstancedBufferAttribute(b, 4), C = new THREE.InstancedBufferAttribute(c, 4);
    A.setUsage(THREE.DynamicDrawUsage); B.setUsage(THREE.DynamicDrawUsage); C.setUsage(THREE.DynamicDrawUsage);
    g.setAttribute('iA', A); g.setAttribute('iB', B); g.setAttribute('iC', C); g.instanceCount = n;
    // culling: one sphere round the room (frustum culling stays on; the game moves it on a room change)
    g.boundingSphere = new THREE.Sphere(new THREE.Vector3(), opts.sphereR || 40);
    const mat = new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: FS(cut), fog: true, side: THREE.DoubleSide,
      uniforms: THREE.UniformsUtils.merge([THREE.UniformsLib.fog, { map: { value: null }, ramp: { value: null }, uRampW: { value: meta.ramps.width }, uAshV: { value: (rows.indexOf('ash') + 0.5) / nRows },
        uFxA: { value: U.A }, uFxB: { value: U.B }, uFxC: { value: U.C }, uFxD: { value: U.D } }]) });
    mat.uniforms.map.value = tex[an]; mat.uniforms.ramp.value = ramp; mat.uniforms.uTime = uTime;
    if (cut) { mat.alphaToCoverage = true; mat.transparent = false; mat.depthWrite = true; mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -2; }
    else { mat.transparent = true; mat.depthWrite = false; mat.premultipliedAlpha = true; mat.blending = THREE.NormalBlending; }
    const mesh = new THREE.Mesh(g, mat); mesh.matrixAutoUpdate = false; mesh.renderOrder = cut ? 1 : 3;
    const end = new Float64Array(n).fill(-1);
    pools[an] = { mesh, g, A, B, C, a, b, c, end, n, next: 0 };
  }
  const HOLD_NONE = 1e9, pk = Object.keys(pools), pkI = {};
  pk.forEach((k, i) => { pkI[k] = i; });
  // HOT: spawn writes one instance (no allocation). name = card; x y z = anchor (feet, hit point or ground point); row = ramp row index;
  // sx, sy = scale of the card's own size (upright: sx = sy = scale, sx < 0 mirrors; ring / mark / crack: radius / unitRadiusM; strip: width / unitWidthM
  // and length / unitLenM; thrust: range / unitLenM and a width factor); rot = screen angle (upright) or yaw (ground: forward = (sin, 0, -cos));
  // hold = seconds a tell's loop is held (0 = none); alpha 0..1. Returns a handle (atlas << 8 | slot) for move / release / kill.
  function spawn(name, x, y, z, row, sx, sy, rot, hold, alpha) {
    const k = idx[name], e = meta.effects[name], p = pools[e.atlas]; let s = -1;
    for (let i = 0; i < p.n; i++) { const j = (p.next + i) % p.n; if (p.end[j] < uTime.value) { s = j; break; } }
    if (s < 0) s = p.next;
    p.next = (s + 1) % p.n;
    const lp = e.loop, held = lp && hold > 0, ww = e.sizeM[0] * sx, hh = e.sizeM[1] * sy;
    const t0 = uTime.value, holdEnd = held ? t0 + hold : (lp && lp[1] < e.frames ? t0 + lp[0] / e.fps : HOLD_NONE);
    p.a[s * 4] = x; p.a[s * 4 + 1] = y + (e.orient === 'ground' ? 0.02 : e.anchorHeightM * sy); p.a[s * 4 + 2] = z; p.a[s * 4 + 3] = t0;
    p.b[s * 4] = holdEnd; p.b[s * 4 + 1] = rot; p.b[s * 4 + 2] = ww; p.b[s * 4 + 3] = hh;
    p.c[s * 4] = k; p.c[s * 4 + 1] = (row + 0.5) / nRows; p.c[s * 4 + 2] = alpha; p.c[s * 4 + 3] = 0;
    // life: a looping card without hold loops until kill(); others end after their frames (and their hold)
    p.end[s] = lp && !held && lp[1] >= e.frames ? HOLD_NONE : (held ? holdEnd + (e.frames - lp[1]) / e.fps : t0 + e.frames / e.fps) + 0.05;
    p.A.addUpdateRange(s * 4, 4); p.B.addUpdateRange(s * 4, 4); p.C.addUpdateRange(s * 4, 4);
    p.A.needsUpdate = p.B.needsUpdate = p.C.needsUpdate = true;
    return (pkI[e.atlas] << 8) | s;
  }
  // HOT: move a following card (bolt in flight, aura on a walking suit); release a held tell now; kill a card.
  function move(hd, x, y, z) { const p = pools[pk[hd >> 8]], s = hd & 255; p.a[s * 4] = x; p.a[s * 4 + 1] = y; p.a[s * 4 + 2] = z; p.A.addUpdateRange(s * 4, 3); p.A.needsUpdate = true; }
  function release(hd, name) {
    const p = pools[pk[hd >> 8]], s = hd & 255, e = meta.effects[name]; p.b[s * 4] = uTime.value; p.B.addUpdateRange(s * 4, 1); p.B.needsUpdate = true;
    p.end[s] = uTime.value + (e.frames - (e.loop ? e.loop[1] : 0)) / e.fps + 0.05;
  }
  function kill(hd) { const p = pools[pk[hd >> 8]], s = hd & 255; p.c[s * 4 + 2] = 0; p.end[s] = -1; p.C.addUpdateRange(s * 4 + 2, 1); p.C.needsUpdate = true; }
  function live() { let n = 0; for (const k of pk) { const p = pools[k]; for (let i = 0; i < p.n; i++) if (p.end[i] >= uTime.value) n++; } return n; }
  return { pools, meshes: pk.map((k) => pools[k].mesh), uTime, spawn, move, release, kill, live, idx, rows };
}

// Loading: atlases as RG8 data (fetch + createImageBitmap with no premultiply and no colour conversion; no <img>, so the page load event is never held).
export async function loadCards(THREE, base) {
  const meta = await (await fetch(base + 'vfx.json')).json();
  const bm = async (f) => createImageBitmap(await (await fetch(base + f)).blob(), { premultiplyAlpha: 'none', colorSpaceConversion: 'none' });
  const tex = {};
  for (const [n, a] of Object.entries(meta.atlases)) {
    const t = new THREE.Texture(await bm(a.file)); t.format = THREE.RGFormat; t.flipY = false; t.generateMipmaps = false;
    t.minFilter = t.magFilter = THREE.LinearFilter; t.colorSpace = THREE.NoColorSpace; t.needsUpdate = true; tex[n] = t;
  }
  const ramp = new THREE.Texture(await createImageBitmap(await (await fetch(base + meta.ramps.file)).blob(), { premultiplyAlpha: 'none' }));
  ramp.flipY = false; ramp.generateMipmaps = false; ramp.minFilter = ramp.magFilter = THREE.LinearFilter; ramp.colorSpace = THREE.SRGBColorSpace; ramp.needsUpdate = true;
  return { meta, tex, ramp };
}
