import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { GLTFExporter } from 'three/examples/jsm/exporters/GLTFExporter.js';

// ---------------- CONFIG: tune by hand ----------------
const CONFIG = {
  steel: 0x9aa3ad, steelRough: 0.36,
  darkSteel: 0x565e69, darkRough: 0.5,
  brass: 0xb8923e, brassRough: 0.34,
  under: 0x15171b, cloth: 0x2f4a33, leather: 0x8a2f24,
  glow: 0x5fe6f0, glowPower: 2.2,
  engraveDepth: 3.2,          // how deep the carved engraving reads (0 = flat)
  background: 0x7d838c,
  flutes: 26, fluteDepth: 0.07,
  wear: 0.28,                 // 0 = clean, 0.5 = heavily scuffed
  autoRotate: true, rotateSpeed: 1.2,
};
// -------------------------------------------------------

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
document.body.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(CONFIG.background);
scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 50);
camera.position.set(1.5, 1.3, 3.9);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0.98, 0);
controls.enableDamping = true;
controls.autoRotate = CONFIG.autoRotate;
controls.autoRotateSpeed = CONFIG.rotateSpeed;
controls.minDistance = 1.2; controls.maxDistance = 7;
const key = new THREE.DirectionalLight(0xffffff, 2.0);
key.position.set(-2.5, 4, 3);
scene.add(key);
const fill = new THREE.DirectionalLight(0xdfe8ff, 2.4);
fill.position.set(1.8, 3, -4);
const fill2 = new THREE.DirectionalLight(0xffffff, 1.2);
fill2.position.set(-2.5, 2, -3);
scene.add(fill2);
key.castShadow = true; key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0005; key.shadow.normalBias = 0.02;
Object.assign(key.shadow.camera, { left: -1.4, right: 1.4, top: 2.4, bottom: -0.4, near: 0.5, far: 12 });
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
scene.add(fill);
scene.add(new THREE.HemisphereLight(0xffffff, 0x9a9fa8, 1.0));
const under = new THREE.DirectionalLight(0xffffff, 0.9); under.position.set(0, -1.5, 3); scene.add(under);

// worn-metal roughness texture
function wearTexture() {
  const c = document.createElement('canvas'); c.width = c.height = 256;
  const g = c.getContext('2d');
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  g.fillStyle = '#fff'; g.fillRect(0, 0, 256, 256);
  for (let i = 0; i < 2600; i++) {
    const v = 255 - Math.floor(rnd() * 255 * CONFIG.wear * 2);
    g.fillStyle = `rgb(${v},${v},${v})`;
    g.fillRect(rnd() * 256, rnd() * 256, 1 + rnd() * 3, 1 + rnd() * 2);
  }
  g.strokeStyle = 'rgba(40,40,40,0.5)';
  for (let i = 0; i < 70; i++) {
    g.lineWidth = 0.5 + rnd();
    const x = rnd() * 256, y = rnd() * 256;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + (rnd() - 0.5) * 60, y + (rnd() - 0.5) * 20); g.stroke();
  }
  const t = new THREE.CanvasTexture(c); t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(2, 2);
  return t;
}
const wear = wearTexture();
const M = {
  steel: new THREE.MeshStandardMaterial({ color: CONFIG.steel, metalness: 1, roughness: CONFIG.steelRough + 0.25, roughnessMap: wear, side: THREE.DoubleSide, envMapIntensity: 1.35, name: 'steel' }),
  dark: new THREE.MeshStandardMaterial({ color: CONFIG.darkSteel, metalness: 1, roughness: CONFIG.darkRough + 0.2, roughnessMap: wear, side: THREE.DoubleSide, envMapIntensity: 1.35, name: 'dark_steel' }),
  brass: new THREE.MeshStandardMaterial({ color: CONFIG.brass, metalness: 1, roughness: CONFIG.brassRough, name: 'brass' }),
  under: new THREE.MeshStandardMaterial({ color: CONFIG.under, metalness: 0, roughness: 0.9, name: 'undersuit' }),
  cloth: new THREE.MeshStandardMaterial({ color: CONFIG.cloth, metalness: 0, roughness: 1, side: THREE.DoubleSide, name: 'cloth' }),
  leather: new THREE.MeshStandardMaterial({ color: CONFIG.leather, metalness: 0, roughness: 0.75, name: 'grip_leather' }),
  glow: new THREE.MeshStandardMaterial({ color: 0x0a2a30, emissive: CONFIG.glow, emissiveIntensity: CONFIG.glowPower, name: 'glow' }),
};

// Carved engraving: draw a height picture on a canvas (white = surface, dark = cut), then derive a
// normal map from it. Colour map + normal map both export to GLB, and add no triangles.
function engrave(S, draw, tile) {
  const c = document.createElement('canvas'); c.width = c.height = S;
  const g = c.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, S, S);
  g.lineCap = 'round'; g.lineJoin = 'round';
  for (const [col, k] of [['#9a9fa6', 1], ['#1c1f25', 0.55]]) { g.strokeStyle = col; g.fillStyle = col; draw(g, k); }   // wide soft cut, then deep centre
  const src = g.getImageData(0, 0, S, S).data;
  const n = document.createElement('canvas'); n.width = n.height = S;
  const ng = n.getContext('2d'), out = ng.createImageData(S, S), H = (x, y) => {
    x = tile ? (x + S) % S : Math.min(S - 1, Math.max(0, x)); y = Math.min(S - 1, Math.max(0, y)); return src[(y * S + x) * 4] / 255;
  };
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    let nx = (H(x - 1, y) - H(x + 1, y)) * CONFIG.engraveDepth, ny = (H(x, y + 1) - H(x, y - 1)) * CONFIG.engraveDepth;
    const l = Math.hypot(nx, ny, 1), o = (y * S + x) * 4;
    out.data[o] = (nx / l * 0.5 + 0.5) * 255; out.data[o + 1] = (ny / l * 0.5 + 0.5) * 255; out.data[o + 2] = (1 / l * 0.5 + 0.5) * 255; out.data[o + 3] = 255;
  }
  ng.putImageData(out, 0, 0);
  const map = new THREE.CanvasTexture(c), normalMap = new THREE.CanvasTexture(n);
  map.colorSpace = THREE.SRGBColorSpace; map.anisotropy = normalMap.anisotropy = 4;
  if (tile) for (const t of [map, normalMap]) { t.wrapS = THREE.RepeatWrapping; t.repeat.set(4, 1); }
  return { map, normalMap };
}
const stroke = (g, pts, w) => { g.lineWidth = w; g.beginPath(); pts.forEach((p, k) => k ? g.lineTo(p[0], p[1]) : g.moveTo(p[0], p[1])); g.stroke(); };
const spiralPts = (cx, cy, r, turns, a0, dir, sq = 1) => { const pts = []; for (let k = 0; k <= 60; k++) { const t = k / 60, a = a0 + dir * t * turns * Math.PI * 2, rr = r * (1 - t * 0.92); pts.push([cx + Math.cos(a) * rr, cy + Math.sin(a) * rr * sq]); } return pts; };
// border tile for body plates: a running vine with curls along the rim, and a lozenge with scrolls above it
const bodyEngraving = engrave(512, (g, k) => {
  const S = 512, w = 9 * k;
  stroke(g, [[0, S * 0.94], [S, S * 0.94]], w); stroke(g, [[0, S * 0.72], [S, S * 0.72]], w);
  const vine = []; for (let x = 0; x <= S; x += 4) vine.push([x, S * 0.83 + Math.sin(x / S * Math.PI * 4) * S * 0.05]);
  stroke(g, vine, w);
  for (let q = 0; q < 4; q++) stroke(g, spiralPts(S * (q + 0.5) / 4, S * (q % 2 ? 0.865 : 0.795), S * 0.042, 1.6, q % 2 ? 1.6 : -1.6, q % 2 ? 1 : -1), w * 0.9);
  const cx = S / 2, cy = S * 0.4;
  stroke(g, [[cx, cy - S * 0.15], [cx + S * 0.085, cy], [cx, cy + S * 0.15], [cx - S * 0.085, cy], [cx, cy - S * 0.15]], w);
  stroke(g, [[cx, cy - S * 0.07], [cx + S * 0.04, cy], [cx, cy + S * 0.07], [cx - S * 0.04, cy], [cx, cy - S * 0.07]], w * 0.8);
  for (const d of [-1, 1]) {
    stroke(g, spiralPts(cx + d * S * 0.25, cy, S * 0.085, 1.9, d > 0 ? Math.PI : 0, d), w);
    stroke(g, spiralPts(cx + d * S * 0.4, cy - S * 0.13, S * 0.045, 1.5, d > 0 ? 0.5 : Math.PI - 0.5, -d), w * 0.85);
  }
}, true);
M.engr = M.steel.clone(); M.engr.name = 'engraved_steel';
M.engr.map = bodyEngraving.map; M.engr.normalMap = bodyEngraving.normalMap; M.engr.normalScale = new THREE.Vector2(1, 1);

let knight = new THREE.Group();   // the group currently being built; every helper adds to it
M.violet = M.cloth.clone(); M.violet.color.set(0x3b2f63); M.violet.name = 'cloth_violet';
M.red = M.cloth.clone(); M.red.color.set(0x6b1f24); M.red.name = 'cloth_red';
const Y = new THREE.Vector3(0, 1, 0), PI = Math.PI;
const V = (x, y, z) => new THREE.Vector3(x, y, z);
function mesh(geo, mat, parent, x = 0, y = 0, z = 0, name = '') {
  const m = new THREE.Mesh(geo, mat); m.position.set(x, y, z); m.name = name; (parent || knight).add(m); return m;
}
const add = (geo, mat, x, y, z, name) => mesh(geo, mat, knight, x, y, z, name);
function flutedLathe(profile, flutes = CONFIG.flutes, depth = CONFIG.fluteDepth, seg = 78) {
  const pos = [], uv = [], idx = [], n = profile.length;
  for (let i = 0; i < n; i++) {
    const [r, y] = profile[i];
    for (let j = 0; j <= seg; j++) {
      const th = j / seg * PI * 2;
      const w = Math.min(1, Math.max(0, Math.cos(th) * 1.5 + 0.35));
      const rr = r * (1 - depth * (0.5 - 0.5 * Math.cos(flutes * th)) * w);
      pos.push(rr * Math.sin(th), y, rr * Math.cos(th)); uv.push(j / seg * 3, i / (n - 1));
    }
  }
  for (let i = 0; i < n - 1; i++) for (let j = 0; j < seg; j++) {
    const a = i * (seg + 1) + j, b = a + 1, c = a + seg + 1, d = c + 1;
    idx.push(a, b, c, b, d, c);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals(); return g;
}
const lathe = (pts, seg = 32) => new THREE.LatheGeometry(pts.map(p => new THREE.Vector2(p[0], p[1])), seg);
const ring = (rTop, rBot, h) => new THREE.CylinderGeometry(rTop, rBot, h, 22, 1, true);
function bead(r, tube, mat, parent, y, name) {            // rolled edge, lies flat (axis = Y)
  const t = mesh(new THREE.TorusGeometry(r, tube, 6, 26), mat, parent, 0, y, 0, name); t.rotation.x = PI / 2; return t;
}
function along(a, b, name, parent) {                                // group whose +Y runs from a to b
  const g = new THREE.Group(); const d = b.clone().sub(a);
  g.userData.len = d.length(); g.position.copy(a);
  g.quaternion.setFromUnitVectors(Y, d.normalize()); g.name = name; (parent || knight).add(g); return g;
}
function rod(a, b, r, mat, name) {
  const g = along(a, b, name);
  mesh(new THREE.CylinderGeometry(r, r, g.userData.len, 12), mat, g, 0, g.userData.len / 2, 0, name);
}
function cable(points, r, name) {
  const c = new THREE.CatmullRomCurve3(points);
  add(new THREE.TubeGeometry(c, 14, r, 6), M.under, 0, 0, 0, name);
}

function torsoParts(clothMat = M.cloth) {
// ---- body under the plates (keeps every joint closed) ----
add(new THREE.CapsuleGeometry(0.17, 0.5, 8, 20), M.under, 0, 1.25, 0, 'torso_undersuit').scale.set(1.1, 1, 0.8);
add(new THREE.SphereGeometry(0.2, 24, 16), M.under, 0, 0.93, 0, 'pelvis_undersuit').scale.set(1.05, 0.75, 0.8);
add(new THREE.CylinderGeometry(0.075, 0.09, 0.12, 20), M.under, 0, 1.6, 0, 'neck_undersuit');

// ---- torso plates ----
const tz = 0.85;
add(flutedLathe([[0.2, 1.1], [0.235, 1.17], [0.28, 1.29], [0.287, 1.38], [0.25, 1.475], [0.165, 1.548], [0.13, 1.565], [0.138, 1.58]]), M.steel, 0, 0, 0, 'breastplate').scale.set(1, 1, tz);
add(flutedLathe([[0.2, 1.02], [0.218, 1.07], [0.245, 1.16], [0.238, 1.175]]), M.steel, 0, 0, 0, 'plackart').scale.set(1, 1, tz + 0.02);
bead(0.134, 0.012, M.brass, null, 1.582, 'neck_rim').scale.set(1, tz, 1);
bead(0.243, 0.008, M.brass, null, 1.172, 'plackart_rim').scale.set(1, tz + 0.02, 1);
add(lathe([[0.15, 1.565], [0.125, 1.6], [0.112, 1.635], [0.118, 1.645]]), M.steel, 0, 0, 0, 'gorget');
bead(0.203, 0.024, M.brass, null, 1.035, 'belt').scale.set(1, tz, 1);
[[0.205, 1.03, 0.24, 0.972], [0.228, 0.985, 0.264, 0.927], [0.252, 0.94, 0.29, 0.878]].forEach((p, i) => {
  add(flutedLathe([[p[0], p[1]], [p[2], p[3]], [p[2] + 0.004, p[3] - 0.006]], CONFIG.flutes, CONFIG.fluteDepth * 0.8), M.steel, 0, 0, 0, 'fauld_lame_' + i).scale.set(1, 1, 0.84);
});
add(new THREE.BoxGeometry(0.19, 0.36, 0.012), clothMat, 0, 0.72, 0.15, 'cloth_front');
add(new THREE.BoxGeometry(0.19, 0.36, 0.012), clothMat, 0, 0.72, -0.15, 'cloth_back');
add(new THREE.BoxGeometry(0.02, 0.16, 0.012), M.glow, 0, 1.14, -0.208, 'spine_light');

}
function packParts() {
// ---- power pack: ribbed reactor drum, exhaust stacks, cables ----
add(new THREE.SphereGeometry(1, 28, 18), M.steel, 0, 1.36, -0.2, 'pack_mount').scale.set(0.23, 0.2, 0.1);
const drum = add(new THREE.CylinderGeometry(0.085, 0.085, 0.34, 28), M.dark, 0, 1.36, -0.3, 'reactor_drum'); drum.rotation.z = PI / 2;
for (const x of [-0.11, 0, 0.11]) { const t = add(new THREE.TorusGeometry(0.088, 0.012, 8, 28), M.brass, x, 1.36, -0.3, 'drum_rib'); t.rotation.y = PI / 2; }
for (const s of [-1, 1]) {
  const cap = add(new THREE.CylinderGeometry(0.06, 0.06, 0.012, 24), M.glow, s * 0.174, 1.36, -0.3, 'drum_cap'); cap.rotation.z = PI / 2;
  const st = along(V(s * 0.12, 1.42, -0.27), V(s * 0.2, 1.74, -0.36), 'exhaust');
  const L = st.userData.len;
  mesh(lathe([[0.03, 0], [0.036, L * 0.6], [0.046, L], [0.036, L - 0.005], [0.026, L - 0.03]], 20), M.dark, st, 0, 0, 0, 'exhaust_stack');
  bead(0.046, 0.007, M.brass, st, L, 'exhaust_rim');
  mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.006, 16), M.glow, st, 0, L - 0.03, 0, 'exhaust_glow');
  cable([V(s * 0.1, 1.29, -0.31), V(s * 0.2, 1.18, -0.27), V(s * 0.25, 1.06, -0.16), V(s * 0.215, 1.0, -0.05)], 0.016, 'hip_cable');
  cable([V(s * 0.15, 1.44, -0.29), V(s * 0.27, 1.53, -0.22), V(s * 0.36, 1.52, -0.12)], 0.014, 'shoulder_cable');
}

}
function legParts(s, lx) {
  add(new THREE.CapsuleGeometry(0.095, 0.7, 6, 16), M.under, lx, 0.5, 0, 'leg_undersuit');
  add(flutedLathe([[0.128, 0.91], [0.136, 0.9], [0.138, 0.79], [0.118, 0.64], [0.108, 0.59], [0.113, 0.583]], 16, CONFIG.fluteDepth), M.steel, lx, 0, 0, 'cuisse');
  add(new THREE.CylinderGeometry(0.152, 0.162, 0.2, 22, 1, true, -1.0, 2.0), M.engr, lx, 0.79, 0, 'tasset');
  const tr = add(new THREE.TorusGeometry(0.162, 0.007, 6, 20, 2.0), M.brass, lx, 0.69, 0, 'tasset_rim'); tr.rotation.set(PI / 2, 0, PI / 2 - 1.0);
  add(ring(0.108, 0.124, 0.05), M.steel, lx, 0.595, 0, 'knee_lame_upper');
  add(new THREE.SphereGeometry(0.118, 22, 16), M.steel, lx, 0.53, 0.012, 'poleyn').scale.set(1, 0.85, 1.05);
  add(ring(0.122, 0.106, 0.05), M.steel, lx, 0.462, 0, 'knee_lame_lower');
  const fan = add(new THREE.CylinderGeometry(0.07, 0.07, 0.014, 20), M.brass, lx + s * 0.112, 0.53, 0, 'poleyn_fan'); fan.rotation.z = PI / 2;
  add(new THREE.SphereGeometry(0.016, 10, 8), M.glow, lx, 0.53, 0.137, 'knee_light');
  add(lathe([[0.104, 0.45], [0.098, 0.44], [0.118, 0.36], [0.104, 0.24], [0.084, 0.13], [0.094, 0.105], [0.098, 0.1]], 28), M.engr, lx, 0, 0, 'greave');
  bead(0.097, 0.008, M.brass, null, 0.102, 'ankle_rim').position.x = lx;
  add(new THREE.BoxGeometry(0.012, 0.17, 0.012), M.glow, lx, 0.3, 0.108, 'shin_light');
  add(new THREE.SphereGeometry(0.015, 10, 8), M.glow, lx + s * 0.121, 0.53, 0, 'poleyn_fan_light');
  for (const d of [-1, 1]) add(new THREE.BoxGeometry(0.07, 0.011, 0.008), M.glow, lx + d * 0.028, 0.79, 0.158, 'tasset_chevron').rotation.z = d * 0.6;
  rod(V(lx + s * 0.06, 0.47, -0.09), V(lx + s * 0.045, 0.15, -0.085), 0.013, M.brass, 'calf_piston');
  rod(V(lx - s * 0.06, 0.47, -0.09), V(lx - s * 0.045, 0.15, -0.085), 0.013, M.brass, 'calf_piston');
  // heavy sabaton sized to the body: heel block, flared ankle guard, five overlapping lames, toe cap, thick sole
  add(new THREE.CylinderGeometry(0.108, 0.118, 0.13, 20), M.dark, lx, 0.065, -0.02, 'heel');
  add(ring(0.098, 0.128, 0.075), M.steel, lx, 0.135, -0.005, 'ankle_guard');
  for (let i = 0; i < 5; i++) {
    const r = 0.118 - i * 0.006;
    add(new THREE.SphereGeometry(r, 18, 8, 0, PI * 2, 0, PI / 2), M.steel, lx, 0.018, 0.05 + i * 0.062, 'sabaton_lame_' + i).scale.set(0.92, 0.98 - i * 0.1, 0.62);
  }
  const toe = add(new THREE.ConeGeometry(0.082, 0.15, 14), M.steel, lx, 0.036, 0.4, 'toe_cap'); toe.rotation.x = PI / 2; toe.scale.set(1, 1, 0.5);
  add(new THREE.BoxGeometry(0.225, 0.022, 0.5), M.dark, lx, 0.011, 0.15, 'sole');
}
// ================= shared parts for the other characters =================
const gSmooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const gProf = (P, y) => { if (y <= P[0][0]) return P[0][1]; for (let k = 0; k < P.length - 1; k++) if (y <= P[k + 1][0]) return P[k][1] + (P[k + 1][1] - P[k][1]) * gSmooth((y - P[k][0]) / (P[k + 1][0] - P[k][0])); return P[P.length - 1][1]; };
const gDistSeg = (px, py, ax, ay, bx, by) => { const t = Math.min(1, Math.max(0, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2))); return Math.hypot(px - ax - t * (bx - ax), py - ay - t * (by - ay)); };
const gTri = (t) => Math.abs((((t % 2) + 2) % 2) - 1) * 2 - 1;
// one continuous sculpted shell: posFn(u, v) gives the surface, ff(u, v) > 0 keeps metal, < 0 cuts it away
function shell(parent, b, NX, NY, posFn, ff, mat, name) {
  const [u0, u1, v0, v1] = b, pos = [], uv = [], idx = [], cache = new Map();
  const U = (i) => u0 + (u1 - u0) * i / NX, W = (j) => v0 + (v1 - v0) * j / NY, F = [];
  for (let j = 0; j <= NY; j++) { F.push([]); for (let i = 0; i <= NX; i++) F[j].push(ff(U(i), W(j))); }
  const vert = (key, u, v) => { if (cache.has(key)) return cache.get(key); const p = posFn(u, v); pos.push(p[0], p[1], p[2]); uv.push((u - u0) / (u1 - u0), (v - v0) / (v1 - v0)); cache.set(key, pos.length / 3 - 1); return pos.length / 3 - 1; };
  const edge = (i0, j0, i1, j1) => { const fa = F[j0][i0], fb = F[j1][i1], t = fa / (fa - fb); return vert('e' + Math.min(i0, i1) + '_' + Math.min(j0, j1) + (i0 === i1 ? 'v' : 'h'), U(i0) + (U(i1) - U(i0)) * t, W(j0) + (W(j1) - W(j0)) * t); };
  for (let j = 0; j < NY; j++) for (let i = 0; i < NX; i++) {
    const cs = [[i, j], [i + 1, j], [i + 1, j + 1], [i, j + 1]], poly = [];
    for (let q = 0; q < 4; q++) { const a = cs[q], c = cs[(q + 1) % 4], fa = F[a[1]][a[0]], fb = F[c[1]][c[0]];
      if (fa > 0) poly.push(vert('c' + a[0] + '_' + a[1], U(a[0]), W(a[1])));
      if ((fa > 0) !== (fb > 0)) poly.push(edge(a[0], a[1], c[0], c[1])); }
    for (let q = 1; q < poly.length - 1; q++) idx.push(poly[0], poly[q], poly[q + 1]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals(); return mesh(g, mat, parent, 0, 0, 0, name);
}
function engravedMaterial(base, S, draw, name) {
  const e = engrave(S, draw, false), m = base.clone(); m.name = name; m.map = e.map; m.normalMap = e.normalMap; m.normalScale = new THREE.Vector2(1, 1); m.roughnessMap = null; return m;
}
function inGroup(g, fn) { const prev = knight; prev.add(g); knight = g; fn(); knight = prev; return g; }
function grp(x = 0, y = 0, z = 0, sx = 1, sy = 1, sz = 1, name = '') { const g = new THREE.Group(); g.position.set(x, y, z); g.scale.set(sx, sy, sz); g.name = name; return g; }
function spikeOn(parent, a, dir, len, r, mat, name, flat = 0.32) {
  const g = along(a, a.clone().addScaledVector(dir.clone().normalize(), len), name, parent);
  mesh(new THREE.ConeGeometry(r, len, 4), mat, g, 0, len / 2, 0, name).scale.set(1, 1, flat); return g;
}
// lathe whose axis runs front to back (z), flutes on the top; used for the beast's body
function zLathe(profile, flutes = 0, depth = 0, seg = 40) {
  const pos = [], uv = [], idx = [], n = profile.length;
  for (let i = 0; i < n; i++) {
    const [r, z] = profile[i];
    for (let j = 0; j <= seg; j++) {
      const th = j / seg * PI * 2, w = Math.min(1, Math.max(0, Math.cos(th) * 1.5 + 0.35));
      const rr = r * (1 - depth * (0.5 - 0.5 * Math.cos(flutes * th)) * w);
      pos.push(rr * Math.sin(th), rr * Math.cos(th), z); uv.push(j / seg * 3, i / (n - 1));
    }
  }
  for (let i = 0; i < n - 1; i++) for (let j = 0; j < seg; j++) { const a = i * (seg + 1) + j, b = a + 1, c = a + seg + 1, d = c + 1; idx.push(a, b, c, b, d, c); }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals(); return g;
}
// arms differ by character: 'sleeve' = mage (cloth upper sleeve, wide trumpet cuff), 'bracer' = rogue (bare upper arm, pointed elbow, bladed bracer)
// split a built leg into a thigh group that turns at the hip and a shin group that turns at the knee
function rigLeg(g, lx) {
  const hip = grp(lx, 0.92, 0, 1, 1, 1, 'hip'), shin = grp(0, -0.39, 0, 1, 1, 1, 'shin'); g.parent.add(hip); hip.add(shin); g.parent.updateMatrixWorld(true);
  const LOWER = /^(knee_lame_lower|greave|ankle_rim|shin_light|calf_piston|heel|ankle_guard|sabaton_lame_\d|toe_cap|sole|poleyn|poleyn_fan|poleyn_fan_light|knee_light|knee_undersuit)$/;
  for (const c of [...g.children]) (LOWER.test(c.name) ? shin : hip).attach(c);
  g.parent.remove(g);
  const u = hip.getObjectByName('leg_undersuit'); if (u) { u.scale.y = 0.5; u.position.y += 0.17; }
  mesh(new THREE.CapsuleGeometry(0.085, 0.3, 4, 12), M.under, shin, 0, -0.2, 0, 'shin_undersuit');
  return { hip, shin };
}
function armParts(s, S, E, W, k, style) {
  const ua = along(S, E, 'upper_arm'), ul = ua.userData.len, fa = along(E, W, 'forearm'), fl = fa.userData.len;
  mesh(new THREE.CylinderGeometry(0.075 * k, 0.075 * k, ul, 14), M.under, ua, 0, ul / 2, 0, 'upper_arm_undersuit');
  mesh(new THREE.CylinderGeometry(0.068 * k, 0.078 * k, fl * 0.7, 18), M.steel, fa, 0, fl * 0.35, 0, 'vambrace');
  mesh(new THREE.CylinderGeometry(0.056 * k, 0.056 * k, fl * 0.1, 14), M.under, fa, 0, fl * 0.97, 0, 'wrist_joint');
  if (style === 'sleeve') {
    mesh(new THREE.CylinderGeometry(0.1 * k, 0.085 * k, ul * 0.8, 16), M.violet, ua, 0, ul * 0.55, 0, 'upper_sleeve');
    add(new THREE.CylinderGeometry(0.075 * k, 0.075 * k, 0.03, 18), M.brass, E.x + s * 0.07 * k, E.y, E.z, 'elbow_disc').rotation.z = PI / 2;
    add(new THREE.SphereGeometry(0.085 * k, 16, 10), M.steel, E.x, E.y, E.z, 'elbow_cop');
    mesh(lathe([[0.175 * k, fl * 0.26], [0.185 * k, fl * 0.3], [0.13 * k, fl * 0.55], [0.08 * k, fl * 0.86], [0.07 * k, fl * 0.94]], 26), M.engr, fa, 0, 0, 0, 'trumpet_cuff');
    bead(0.185 * k, 0.009, M.brass, fa, fl * 0.3, 'cuff_rim'); bead(0.105 * k, 0.0045, M.glow, fa, fl * 0.7, 'cuff_energy_seal');
  } else {
    mesh(ring(0.097 * k, 0.086 * k, 0.085), M.steel, ua, 0, ul * 0.5, 0, 'upper_arm_band');
    spikeOn(knight, E.clone(), V(s * 0.3, 0.2, -1), 0.17, 0.07 * k, M.steel, 'elbow_point', 0.8);
    add(new THREE.SphereGeometry(0.08 * k, 14, 10), M.steel, E.x, E.y, E.z, 'elbow_cop');
    mesh(lathe([[0.086 * k, fl * 0.22], [0.094 * k, fl * 0.27], [0.082 * k, fl * 0.75], [0.07 * k, fl * 0.93]], 8), M.steel, fa, 0, 0, 0, 'bracer');
    for (const q of [-1, 1]) spikeOn(fa, V(q * 0.08 * k, fl * 0.7, 0), V(q * 0.45, -1, 0), 0.19, 0.024, M.steel, 'bracer_blade', 0.3);
    bead(0.088 * k, 0.0045, M.glow, fa, fl * 0.5, 'bracer_light');
  }
}
function shoulderParts(s, x, y, R, style) {
  if (style === 'sleeve') {                                   // mage: three stacked spaulder plates under a spire
    const p = grp(x, y, 0, 1, 1, 1.15, 'spaulder'); p.rotation.z = -s * 0.3; knight.add(p);
    for (let i = 0; i < 3; i++) {
      const r = R * (1 - i * 0.04), sx = 1.1 + i * 0.12, sz = 1.1 + i * 0.1;
      mesh(new THREE.SphereGeometry(r, 22, 8, 0, PI * 2, 0, PI * 0.36), i ? M.steel : M.engr, p, s * i * 0.03, -i * 0.05, 0, 'spaulder_plate_' + i).scale.set(sx, 0.8, sz);
      const rim = bead(r * Math.sin(PI * 0.36), 0.007, M.brass, p, 0, 'spaulder_rim'); rim.position.set(s * i * 0.03, -i * 0.05 + r * Math.cos(PI * 0.36) * 0.8, 0); rim.scale.set(sx, sz, 1);
    }
    mesh(new THREE.ConeGeometry(0.028, 0.16, 10), M.brass, p, 0, R * 0.8 + 0.06, 0, 'spaulder_spire');
    mesh(new THREE.SphereGeometry(0.016, 8, 6), M.glow, p, 0, R * 0.8 + 0.15, 0, 'spire_light');
  } else {                                                    // rogue: faceted pointed plate with a spike
    const p = grp(x, y + 0.01, 0, 1, 1, 1.25, 'shoulder_plate'); p.rotation.z = -s * 0.55; knight.add(p);
    mesh(new THREE.ConeGeometry(R * 1.05, R * 0.9, 6), M.steel, p, 0, R * 0.3, 0, 'shoulder_facets');
    mesh(new THREE.CylinderGeometry(R * 1.05, R * 0.95, R * 0.35, 6, 1, true), M.steel, p, 0, -R * 0.32, 0, 'shoulder_skirt');
    bead(R * 1.0, 0.007, M.brass, p, -R * 0.15, 'shoulder_rim');
    spikeOn(p, V(s * R * 0.4, R * 0.5, 0), V(s * 0.9, 0.6, 0), R * 1.1, 0.022, M.steel, 'shoulder_spike', 0.5);
  }
}
// rogue legs: drop the heavy thigh plates, knee fans and plated feet; add soft split-toe boots, knee spikes and greave blades
function rogueLeg(s) {
  knight.traverse(o => { if (/^(tasset|tasset_rim|tasset_chevron|poleyn_fan|poleyn_fan_light|toe_cap|ankle_guard|sole|sabaton_lame_\d)$/.test(o.name)) o.visible = false; });
  const boot = add(new THREE.CylinderGeometry(0.05, 0.1, 0.36, 6), M.dark, 0, 0.045, 0.14, 'soft_boot'); boot.rotation.x = PI / 2; boot.scale.set(1, 1, 0.5);
  add(new THREE.BoxGeometry(0.012, 0.03, 0.14), M.under, 0, 0.07, 0.25, 'toe_split');
  spikeOn(knight, V(0, 0.55, 0.11), V(0, 0.7, 1), 0.13, 0.03, M.steel, 'knee_spike', 0.5);
  spikeOn(knight, V(s * 0.085, 0.42, -0.02), V(s * 0.5, -1, -0.3), 0.2, 0.022, M.steel, 'greave_blade', 0.3);
  add(new THREE.BoxGeometry(0.05, 0.1, 0.03), M.dark, s * 0.13, 0.78, 0.02, 'thigh_sheath');
}
// closed fist round a vertical grip at G, wrist at W; c = +1 or -1 picks which way the fingers wrap
function gripHand(G, W, c, k) {
  const d = W.clone().sub(G), hg = grp(G.x, G.y, G.z, 1, 1, 1, 'hand'); hg.rotation.y = Math.atan2(-d.z, d.x); knight.add(hg);
  const R = 0.044 * k, P = (a, r, y) => V(Math.cos(a) * r, y, c * Math.sin(a) * r);
  const hp = along(V(Math.hypot(d.x, d.z), d.y, 0), V(0.045 * k, 0, 0), 'hand_back', hg), hl = hp.userData.len;
  mesh(new THREE.CylinderGeometry(0.082 * k, 0.062 * k, hl, 12), M.steel, hp, 0, hl / 2, 0, 'metacarpal_plate').scale.set(1, 1, 0.8);
  bead(0.083 * k, 0.008, M.brass, hp, hl * 0.92, 'knuckle_ridge').scale.set(1, 0.8, 1);
  const finger = (y, r, rad, angles, mat, name) => {
    for (let q = 0; q < angles.length; q++) {
      mesh(new THREE.SphereGeometry(rad * (q === 0 ? 1.12 : 1), 8, 6), mat, hg, 0, 0, 0, name + '_knuckle_' + q).position.copy(P(angles[q], r, y));
      if (q < angles.length - 1) { const g = along(P(angles[q], r, y), P(angles[q + 1], r, y), name + '_segment_' + q, hg); mesh(new THREE.CylinderGeometry(rad, rad, g.userData.len, 8), mat, g, 0, g.userData.len / 2, 0, name + '_plate_' + q); }
    }
  };
  for (let i = 0; i < 4; i++) finger((-0.057 + i * 0.038) * k, R, 0.019 * k, [0, 0.9, 1.8, 2.6], M.steel, 'finger_' + i);
  finger(0.098 * k, R + 0.004, 0.023 * k, [-0.2, 0.75, 1.65], M.dark, 'thumb');
}
function pauldronParts(s, x, y, z, R) {
  const f = R / 0.2, p = grp(x, y, z, 1.05 * f, 0.92 * f, 1.22 * f, 'pauldron'); p.rotation.z = -s * 0.32; knight.add(p);
  mesh(new THREE.SphereGeometry(0.2, 24, 10, 0, PI * 2, 0, PI * 0.5), M.engr, p, 0, 0, 0, 'pauldron_dome');
  mesh(ring(0.2, 0.212, 0.07), M.steel, p, 0, -0.035, 0, 'pauldron_lame_1');
  mesh(ring(0.2, 0.205, 0.06), M.steel, p, 0, -0.095, 0, 'pauldron_lame_2');
  bead(0.206, 0.011, M.brass, p, -0.125, 'pauldron_rim'); bead(0.203, 0.006, M.dark, p, -0.002, 'pauldron_seam');
  const pl = mesh(new THREE.TorusGeometry(0.2135, 0.0045, 6, 24, 1.3), M.glow, p, 0, -0.04, 0, 'pauldron_light'); pl.rotation.x = PI / 2; pl.scale.x = s;
}
function coreParts(y, z) {
  const cc = grp(0, y, z, 1, 1, 1, 'chest_core'); cc.rotation.x = -0.5; knight.add(cc);
  mesh(new THREE.TorusGeometry(0.04, 0.01, 8, 28), M.brass, cc, 0, 0, 0, 'chest_core_ring');
  mesh(new THREE.CylinderGeometry(0.032, 0.032, 0.012, 24), M.glow, cc, 0, 0, -0.002, 'chest_core_light').rotation.x = PI / 2;
}
// body, pack, legs, arms, hands and shoulders for a two-legged suit; returns the head group
function humanoid(o) {
  inGroup(grp(0, 0, 0, o.w, 1, o.w, 'torso'), () => torsoParts(o.cloth));
  inGroup(grp(0, 1.36 * (1 - o.pack), -0.21 * (1 - o.pack) + 0.2 * (1 - o.w), o.pack, o.pack, o.pack, 'pack'), packParts);
  for (const s of [-1, 1]) {
    inGroup(grp(s * o.lx, 0, 0, o.k, 1, o.k, 'leg'), () => { legParts(s, 0); if (o.legExtra) o.legExtra(s); });
    const a = o.arm(s);
    armParts(s, a.S, a.E, a.W, o.k, o.style); gripHand(a.G, a.W, s, o.k);
    shoulderParts(s, a.S.x + s * 0.01, a.S.y + 0.005, o.paul(s), o.style);
  }
  coreParts(1.475, 0.203 * o.w);
  const head = grp(0, -0.105, 0, 1.08, 1.08, 1.08, 'head'); knight.add(head); return head;
}
const DOME = [[0.001, 1.875], [0.05, 1.868], [0.09, 1.84], [0.112, 1.79], [0.118, 1.73], [0.114, 1.66], [0.1, 1.61], [0.112, 1.585], [0.116, 1.58]];
function buildKnight() {
// groups that can move: the upper body (pivot at the pelvis), each leg (hip and knee pivots) and the sword
const root = knight, up = grp(0, 0.95, 0, 1, 1, 1, 'upper'), upIn = grp(0, -0.95, 0, 1, 1, 1, 'upper_parts'); root.add(up); up.add(upIn); knight = upIn;
torsoParts();
// ---- helmet ----
const head = new THREE.Group(); head.name = 'head'; head.position.y = 0.03; head.scale.setScalar(1.08); head.position.y = -0.105; knight.add(head);
mesh(lathe([[0.001, 1.875], [0.05, 1.868], [0.09, 1.84], [0.112, 1.79], [0.118, 1.73], [0.114, 1.66], [0.1, 1.61], [0.112, 1.585], [0.116, 1.58]], 36), M.steel, head, 0, 0, 0, 'helmet').scale.set(1, 1, 1.1);
// beast mask (original design): one continuous sculpted shell made from a height function, so the
// brow, sockets, cheekbones and prow flow into each other. No snout and no fangs: the menace comes
// from the V brow, slanted eye slits, a jagged glowing grin and long tines hanging off the jaw.
const smooth = (t) => { t = Math.min(1, Math.max(0, t)); return t * t * (3 - 2 * t); };
const PROFILE = [[1.5, 0], [1.56, 0.004], [1.6, 0.032], [1.655, 0.06], [1.7, 0.05], [1.748, 0.004], [1.785, 0.026], [1.86, 0]];
function profile(y) {
  for (let k = 0; k < PROFILE.length - 1; k++) if (y <= PROFILE[k + 1][0]) {
    const t = smooth((y - PROFILE[k][0]) / (PROFILE[k + 1][0] - PROFILE[k][0]));
    return PROFILE[k][1] + (PROFILE[k + 1][1] - PROFILE[k][1]) * t;
  }
  return 0;
}
function distSeg(px, py, ax, ay, bx, by) {
  const t = Math.min(1, Math.max(0, ((px - ax) * (bx - ax) + (py - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2)));
  return Math.hypot(px - ax - t * (bx - ax), py - ay - t * (by - ay));
}
function maskZ(x, y) {
  const ax = Math.abs(x);
  let z = 0.02 + 0.125 * Math.sqrt(Math.max(0, 1 - (x / 0.14) ** 2));
  z += profile(y) * Math.exp(-((x / 0.05) ** 2));                                           // prow down the centre
  z += 0.02 * Math.exp(-((distSeg(ax, y, 0.012, 1.752, 0.125, 1.825) / 0.013) ** 2));        // V brow ridge
  z -= 0.012 * Math.exp(-((Math.hypot(ax - 0.058, (y - 1.748) * 1.6) / 0.03) ** 2));         // eye socket
  z += 0.012 * Math.exp(-(((ax - 0.085) / 0.03) ** 2 + ((y - 1.69) / 0.03) ** 2));           // cheekbone
  return z * (1 - 0.3 * smooth((y - 1.79) / 0.07));
}
// signed field: positive = metal, negative = cut away (outline, eye slits, grin)
function maskF(x, y) {
  const ax = Math.abs(x);
  const xmax = y > 1.74 ? 0.128 - 2.2 * Math.max(0, y - 1.8) ** 2 * 10 : 0.128 - 0.36 * (1.74 - y);   // tapers to the chin
  let f = Math.min(xmax - ax, 1.795 + 0.52 * ax - y);                                              // V-notched crown
  let yb = 1.6 + 0.9 * ax;                                                                          // jaw line with hanging tines
  [[0, 0.09], [0.036, 0.062], [0.072, 0.046]].forEach(([c, L]) => { yb -= L * Math.max(0, 1 - Math.abs(ax - c) / 0.012); });
  f = Math.min(f, y - yb);
  const dx = ax - 0.058, dy = y - 1.748, u = dx * 0.9 + dy * 0.435, v = -dx * 0.435 + dy * 0.9;     // slanted eye slit
  f = Math.min(f, (Math.sqrt((u / 0.036) ** 2 + (v / 0.0105) ** 2) - 1) * 0.012);
  if (ax < 0.056) {                                                                                 // jagged grin
    const tri = Math.abs(((ax / 0.0125) % 2) - 1) * 2 - 1;
    f = Math.min(f, Math.abs(y - (1.642 + 0.35 * ax + 0.011 * tri)) - 0.0068 * (1 - ax / 0.058));
  }
  return f;
}
// engraving as a texture (no triangles): scrollwork drawn in mask space, used as colour and bump
const MX0 = -0.13, MX1 = 0.13, MY0 = 1.5, MY1 = 1.86;
const maskEngraving = engrave(1024, (g, k) => {
  const S = 1024, px = (x) => (x - MX0) / (MX1 - MX0) * S, py = (y) => (1 - (y - MY0) / (MY1 - MY0)) * S;
  const path = (pts, w) => stroke(g, pts.map(p => [px(p[0]), py(p[1])]), w * k);
  const curve = (p0, p1, p2) => { const pts = []; for (let q = 0; q <= 24; q++) { const t = q / 24; pts.push([(1 - t) ** 2 * p0[0] + 2 * t * (1 - t) * p1[0] + t * t * p2[0], (1 - t) ** 2 * p0[1] + 2 * t * (1 - t) * p1[1] + t * t * p2[1]]); } return pts; };
  for (const s of [-1, 1]) {
    const m = (pts) => pts.map(p => [s * p[0], p[1]]);
    path(m(spiralPts(0.086, 1.688, 0.032, 2.0, 1.2, -1, 0.72)), 13);                             // cheek scroll
    path(m(curve([0.086 + Math.cos(1.2) * 0.032, 1.688 + Math.sin(1.2) * 0.023], [0.12, 1.725], [0.113, 1.768])), 13);
    path(m(spiralPts(0.056, 1.637, 0.016, 1.5, 2.6, 1, 0.72)), 11);                              // jaw curl
    path(m(curve([0.042, 1.642], [0.07, 1.662], [0.1, 1.668])), 10);
    path(m(spiralPts(0.043, 1.797, 0.0135, 1.6, -0.4, 1, 0.72)), 11);                            // forehead S-scroll
    path(m(spiralPts(0.098, 1.827, 0.015, 1.6, 2.8, 1, 0.72)), 11);
    path(m(curve([0.056, 1.797], [0.07, 1.827], [0.084, 1.823])), 11);
    path(m(curve([0.02, 1.772], [0.07, 1.8], [0.122, 1.838])), 8);                               // line following the brow
    for (let q = 0; q < 4; q++) path(m([[0.006, 1.7 - q * 0.02], [0.022, 1.712 - q * 0.02]]), 10);   // chevrons on the prow
  }
  path([[0, 1.72], [0, 1.6]], 10);
}, false);
M.mask = M.steel.clone(); M.mask.name = 'mask_steel';
M.mask.map = maskEngraving.map; M.mask.normalMap = maskEngraving.normalMap; M.mask.normalScale = new THREE.Vector2(1, 1);
M.mask.roughnessMap = null; M.mask.roughness = CONFIG.steelRough + 0.06;
(function buildMask() {
  // marching squares over the field, so outline, tines, eye slits and grin get smooth edges
  const NX = 84, NY = 104, pos = [], uv = [], idx = [], cache = new Map();
  const X = (ix) => MX0 + (MX1 - MX0) * ix / NX, Yc = (jy) => MY0 + (MY1 - MY0) * jy / NY;
  const F = []; for (let jy = 0; jy <= NY; jy++) { F.push([]); for (let ix = 0; ix <= NX; ix++) F[jy].push(maskF(X(ix), Yc(jy))); }
  const vert = (key, x, y) => {
    if (cache.has(key)) return cache.get(key);
    pos.push(x, y, maskZ(x, y)); uv.push((x - MX0) / (MX1 - MX0), (y - MY0) / (MY1 - MY0));
    cache.set(key, pos.length / 3 - 1); return pos.length / 3 - 1;
  };
  const corner = (ix, jy) => vert('c' + ix + '_' + jy, X(ix), Yc(jy));
  const edge = (ix0, jy0, ix1, jy1) => {
    const key = 'e' + Math.min(ix0, ix1) + '_' + Math.min(jy0, jy1) + (ix0 === ix1 ? 'v' : 'h');
    const fa = F[jy0][ix0], fb = F[jy1][ix1], t = fa / (fa - fb);
    return vert(key, X(ix0) + (X(ix1) - X(ix0)) * t, Yc(jy0) + (Yc(jy1) - Yc(jy0)) * t);
  };
  for (let jy = 0; jy < NY; jy++) for (let ix = 0; ix < NX; ix++) {
    const cs = [[ix, jy], [ix + 1, jy], [ix + 1, jy + 1], [ix, jy + 1]], poly = [];
    for (let k = 0; k < 4; k++) {
      const a = cs[k], b = cs[(k + 1) % 4], fa = F[a[1]][a[0]], fb = F[b[1]][b[0]];
      if (fa > 0) poly.push(corner(a[0], a[1]));
      if ((fa > 0) !== (fb > 0)) poly.push(edge(a[0], a[1], b[0], b[1]));
    }
    for (let k = 1; k < poly.length - 1; k++) idx.push(poly[0], poly[k], poly[k + 1]);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  mesh(g, M.mask, head, 0, 0, 0, 'beast_mask');
})();
for (const s of [-1, 1]) mesh(new THREE.BoxGeometry(0.056, 0.026, 0.004), M.glow, head, s * 0.026, 1.654, 0.127, 'maw_glow').rotation.z = s * 0.34;
const spike = (a, dir, len, r, mat, name, flat = 0.32) => {
  const g = along(a, a.clone().addScaledVector(dir.normalize(), len), name, head);
  mesh(new THREE.ConeGeometry(r, len, 4), mat, g, 0, len / 2, 0, name).scale.set(1, 1, flat); return g;
};
for (const s of [-1, 1]) {
  mesh(new THREE.BoxGeometry(0.078, 0.026, 0.004), M.glow, head, s * 0.058, 1.749, 0.107, 'eye_glow').rotation.set(0, s * 0.5, s * 0.45);
  for (let k = 0; k < 3; k++) spike(V(s * 0.1, 1.72 - k * 0.04, 0.06 - k * 0.012), V(s * 0.8, 0.42 - k * 0.3, -0.6), 0.17 - k * 0.025, 0.034 - k * 0.004, M.steel, 'cheek_flare_' + k);
  // horns: dark blades swept back along the skull so the face, not the horns, leads
  const hp = [[0.07, 1.82, 0.045, 0.034], [0.122, 1.872, -0.005, 0.03], [0.156, 1.93, -0.085, 0.022], [0.162, 1.975, -0.185, 0.013], [0.148, 2.0, -0.285, 0.003]];
  for (let k = 0; k < hp.length - 1; k++) {
    const a = V(s * hp[k][0], hp[k][1], hp[k][2]), b = V(s * hp[k + 1][0], hp[k + 1][1], hp[k + 1][2]);
    const g = along(a, b, 'horn', head);
    mesh(new THREE.CylinderGeometry(hp[k + 1][3], hp[k][3], g.userData.len, 10), M.dark, g, 0, g.userData.len / 2, 0, 'horn_segment_' + k);
    mesh(new THREE.SphereGeometry(hp[k][3], 10, 6), k ? M.dark : M.brass, head, a.x, a.y, a.z, 'horn_joint_' + k);
  }
}
spike(V(0, 1.835, 0.085), V(0, 0.75, -0.55), 0.2, 0.03, M.steel, 'crest_blade', 0.35);
mesh(new THREE.OctahedronGeometry(0.014), M.glow, head, 0, 1.812, 0.128, 'forehead_gem');
for (let i = 0; i < 5; i++) {
  const t = 1.3 + i * 0.34;
  const fin = mesh(new THREE.ConeGeometry(0.024, 0.07 - i * 0.004, 4), M.steel, head, 0, 1.745 + 0.125 * Math.sin(t), 0.135 * Math.cos(t), 'dorsal_fin_' + i);
  fin.rotation.x = PI / 2 - t - 0.6; fin.scale.set(0.3, 1, 1);
}
for (const s of [-1, 1]) {
  const h = mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.014, 16), M.brass, head, s * 0.119, 1.72, 0.01, 'visor_pivot'); h.rotation.z = PI / 2;
}
mesh(new THREE.CylinderGeometry(0.004, 0.004, 0.16, 6), M.dark, head, -0.105, 1.86, -0.05, 'antenna');
mesh(new THREE.SphereGeometry(0.009, 8, 6), M.glow, head, -0.105, 1.945, -0.05, 'antenna_tip');

packParts();
// ---- arms ----
for (const s of [-1, 1]) {
  const hy = s < 0 ? 1.23 : 1.01;
  const S = V(s * 0.36, 1.43, 0), E = V(s * 0.46, 1.12, 0.05), W = V(s * 0.17, hy + 0.01, 0.265);
  // upper arm: undersuit + three overlapping lames
  const ua = along(S, E, 'upper_arm'), ul = ua.userData.len;
  mesh(new THREE.CylinderGeometry(0.075, 0.075, ul, 16), M.under, ua, 0, ul / 2, 0, 'upper_arm_undersuit');
  for (let i = 0; i < 3; i++) mesh(ring(0.1 - i * 0.003, 0.088 - i * 0.003, 0.085), M.steel, ua, 0, ul * (0.42 + i * 0.2), 0, 'upper_arm_lame_' + i);
  // elbow: cop, fan, piston
  add(new THREE.SphereGeometry(0.105, 20, 14), M.steel, E.x, E.y, E.z, 'elbow_cop');
  const fan = add(new THREE.CylinderGeometry(0.07, 0.07, 0.014, 20), M.brass, E.x + s * 0.1, E.y, E.z, 'elbow_fan'); fan.rotation.z = PI / 2;
  add(new THREE.SphereGeometry(0.014, 8, 6), M.glow, E.x + s * 0.108, E.y, E.z, 'elbow_light');
  rod(V(s * 0.4, 1.33, -0.085), V(E.x, E.y - 0.03, E.z - 0.1), 0.014, M.brass, 'elbow_piston');
  // forearm, built like the museum pieces: slim vambrace, bell cuff that opens toward the elbow,
  // narrow wrist, then a hand that widens again (metacarpal plate, mitten lames, fingers, thumb)
  const fa = along(E, W, 'forearm'), fl = fa.userData.len;
  mesh(new THREE.CylinderGeometry(0.068, 0.078, fl * 0.7, 20), M.steel, fa, 0, fl * 0.35, 0, 'vambrace');
  mesh(lathe([[0.122, fl * 0.42], [0.128, fl * 0.45], [0.112, fl * 0.58], [0.082, fl * 0.8], [0.064, fl * 0.93], [0.068, fl * 0.95]], 30), M.engr, fa, 0, 0, 0, 'gauntlet_cuff');
  bead(0.128, 0.009, M.brass, fa, fl * 0.45, 'cuff_rim');
  bead(0.1, 0.0045, M.glow, fa, fl * 0.67, 'cuff_energy_seal');
  mesh(new THREE.CylinderGeometry(0.056, 0.056, fl * 0.1, 16), M.under, fa, 0, fl * 0.97, 0, 'wrist_joint');
  const G = V(s * 0.045, hy, 0.326);
  const hp = along(W, G, 'hand_back'), hl = hp.userData.len;
  mesh(new THREE.CylinderGeometry(0.082, 0.062, hl, 14), M.steel, hp, 0, hl / 2, 0, 'metacarpal_plate').scale.set(1, 1, 0.8);
  bead(0.083, 0.008, M.brass, hp, hl * 0.92, 'knuckle_ridge').scale.set(1, 0.8, 1);
  // closed fist: four thick round fingers stacked with no gaps, each bent round the grip in three
  // segments with rounded knuckles and a rounded tip; thumb lies on top of the index finger
  const R = 0.044, gz = 0.33, fr = 0.019;
  const P = (a, r, y) => V(s * Math.cos(a) * r, y, gz + Math.sin(a) * r);
  const finger = (y, r, rad, angles, mat, name) => {
    for (let k = 0; k < angles.length; k++) {
      add(new THREE.SphereGeometry(rad * (k === 0 ? 1.12 : 1), 8, 6), mat, 0, 0, 0, name + '_knuckle_' + k).position.copy(P(angles[k], r, y));
      if (k < angles.length - 1) {
        const g = along(P(angles[k], r, y), P(angles[k + 1], r, y), name + '_segment_' + k);
        mesh(new THREE.CylinderGeometry(rad, rad, g.userData.len, 8), mat, g, 0, g.userData.len / 2, 0, name + '_plate_' + k);
      }
    }
  };
  for (let i = 0; i < 4; i++) finger(hy - 0.057 + i * 0.038, R, fr, [0, 0.9, 1.8, 2.6], M.steel, 'finger_' + i);
  finger(hy + 0.098, R + 0.004, 0.023, [-0.2, 0.75, 1.65], M.dark, 'thumb');
  // pauldron: dome, two lames, rolled rim, upright neck guard, rondel
  const p = new THREE.Group(); p.name = 'pauldron'; p.position.set(s * 0.37, 1.435, 0); p.rotation.z = -s * 0.32; p.scale.set(1.05, 0.92, 1.22); knight.add(p);
  mesh(new THREE.SphereGeometry(0.2, 24, 10, 0, PI * 2, 0, PI * 0.5), M.engr, p, 0, 0, 0, 'pauldron_dome');
  mesh(ring(0.2, 0.212, 0.07), M.steel, p, 0, -0.035, 0, 'pauldron_lame_1');
  mesh(ring(0.2, 0.205, 0.06), M.steel, p, 0, -0.095, 0, 'pauldron_lame_2');
  bead(0.206, 0.011, M.brass, p, -0.125, 'pauldron_rim');
  bead(0.203, 0.006, M.dark, p, -0.002, 'pauldron_seam');
  const pl = mesh(new THREE.TorusGeometry(0.2135, 0.0045, 6, 24, 1.3), M.glow, p, 0, -0.04, 0, 'pauldron_light'); pl.rotation.x = PI / 2; pl.scale.x = s;
  for (let i = 0; i < 3; i++) { const v = mesh(new THREE.TorusGeometry(0.2 * Math.cos(0.45 + i * 0.16), 0.004, 6, 20, 0.8), M.under, p, 0, 0.2 * Math.sin(0.45 + i * 0.16) + 0.001, 0, 'pauldron_vent'); v.rotation.x = PI / 2; v.scale.x = s; }
  add(new THREE.TorusGeometry(0.037, 0.005, 6, 20), M.glow, s * 0.225, 1.42, 0.2225, 'rondel_light');
  mesh(new THREE.CylinderGeometry(0.165, 0.175, 0.13, 24, 1, true, -s * PI / 2 - 0.75, 1.5), M.steel, p, 0, 0.1, 0, 'neck_guard');
  const ro = add(new THREE.CylinderGeometry(0.055, 0.055, 0.012, 22), M.brass, s * 0.225, 1.42, 0.215, 'rondel'); ro.rotation.x = PI / 2;
  add(new THREE.ConeGeometry(0.018, 0.034, 12), M.brass, s * 0.225, 1.42, 0.235, 'rondel_boss').rotation.x = PI / 2;
}

knight = root;
const legs = [-1, 1].map(s => { const g = grp(0, 0, 0, 1, 1, 1, 'leg_build'); root.add(g); knight = g; legParts(s, s * 0.165); knight = root; return rigLeg(g, s * 0.165); });
const sw = grp(0, 1.12, 0.33, 1, 1, 1, 'sword'), swIn = grp(0, -1.12, -0.33, 1, 1, 1, 'sword_parts'); upIn.add(sw); sw.add(swIn); knight = swIn;

// ---- greatsword, planted point down ----
const sz = 0.33;
add(new THREE.SphereGeometry(0.036, 14, 10), M.brass, 0, 1.385, sz, 'pommel');
add(new THREE.CylinderGeometry(0.024, 0.024, 0.45, 12), M.leather, 0, 1.135, sz, 'grip');
for (let i = 0; i < 10; i++) bead(0.025, 0.004, M.brass, null, 0.935 + i * 0.045, 'grip_wire').position.z = sz;
add(new THREE.BoxGeometry(0.46, 0.038, 0.048), M.brass, 0, 0.905, sz, 'guard');
for (const s of [-1, 1]) add(new THREE.SphereGeometry(0.03, 12, 8), M.brass, s * 0.235, 0.905, sz, 'guard_end');
add(new THREE.CylinderGeometry(0.03, 0.03, 0.04, 16), M.brass, 0, 0.87, sz, 'blade_collar').scale.set(1.6, 1, 0.6);
add(new THREE.CylinderGeometry(0.058, 0.058, 0.72, 4), M.steel, 0, 0.5, sz, 'blade').scale.set(1, 1, 0.22);
add(new THREE.ConeGeometry(0.058, 0.13, 4), M.steel, 0, 0.075, sz, 'blade_tip').scale.set(1, -1, 0.22);
add(new THREE.BoxGeometry(0.014, 0.64, 0.03), M.glow, 0, 0.52, sz, 'blade_core');
for (const s of [-1, 1]) {
  add(new THREE.BoxGeometry(0.005, 0.7, 0.005), M.glow, s * 0.0585, 0.5, sz, 'blade_edge_light');
  add(new THREE.SphereGeometry(0.017, 10, 8), M.glow, s * 0.262, 0.905, sz, 'guard_emitter');
}

knight = upIn;
// ---- extra tech, placed where medieval armour puts ornament ----
const cc = new THREE.Group(); cc.name = 'chest_core'; cc.position.set(0, 1.475, 0.203); cc.rotation.x = -0.5; knight.add(cc);
mesh(new THREE.TorusGeometry(0.04, 0.01, 8, 28), M.brass, cc, 0, 0, 0, 'chest_core_ring');
mesh(new THREE.CylinderGeometry(0.032, 0.032, 0.012, 24), M.glow, cc, 0, 0, -0.002, 'chest_core_light').rotation.x = PI / 2;
for (let i = 0; i < 6; i++) mesh(new THREE.SphereGeometry(0.006, 6, 5), M.dark, cc, Math.cos(i * PI / 3) * 0.04, Math.sin(i * PI / 3) * 0.04, 0.01, 'core_bolt');
add(new THREE.BoxGeometry(0.02, 0.2, 0.004), M.glow, 0, 0.73, -0.158, 'heraldic_cross_v');
add(new THREE.BoxGeometry(0.1, 0.02, 0.004), M.glow, 0, 0.78, -0.158, 'heraldic_cross_h');
for (const s of [-1, 1]) {
  add(new THREE.CylinderGeometry(0.028, 0.044, 0.07, 16, 1, true), M.dark, s * 0.085, 1.245, -0.3, 'thruster_nozzle');
  add(new THREE.CylinderGeometry(0.03, 0.03, 0.006, 16), M.glow, s * 0.085, 1.262, -0.3, 'thruster_glow');
  cable([V(s * 0.05, 1.46, -0.27), V(s * 0.07, 1.58, -0.24), V(s * 0.06, 1.69, -0.14)], 0.012, 'neck_cable');
  const pv = mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.018, 12), M.glow, head, s * 0.121, 1.72, 0.01, 'visor_pivot_light'); pv.rotation.z = PI / 2;
}
mesh(new THREE.BoxGeometry(0.028, 0.06, 0.07), M.dark, head, -0.124, 1.685, -0.045, 'comm_module');
mesh(new THREE.BoxGeometry(0.006, 0.03, 0.006), M.glow, head, -0.14, 1.685, -0.045, 'comm_light');

knight.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });

knight = root; root.userData.rig = { up, sw, legs };
}
// ================= MAGE: robed plate, tall cross-visored helm with halo, emitter staff =================
function buildMage() {
  const sz = 0.41;
  const head = humanoid({ w: 0.86, k: 0.8, lx: 0.13, pack: 0.8, cloth: M.violet, style: 'sleeve', paul: () => 0.15,
    arm: (s) => { const hy = s < 0 ? 1.4 : 1.14; return { S: V(s * 0.3, 1.43, 0), E: V(s * 0.4, 1.17, 0.1), W: V(s * 0.16, hy + 0.01, 0.345), G: V(0, hy, sz) }; } });
  add(flutedLathe([[0.185, 1.03], [0.25, 0.82], [0.31, 0.45], [0.36, 0.06]], 20, 0.12, 60), M.violet, 0, 0, 0, 'robe').scale.set(1, 1, 0.86);
  bead(0.36, 0.012, M.brass, null, 0.065, 'robe_hem').scale.set(1, 0.86, 1);
  add(new THREE.BoxGeometry(0.1, 0.85, 0.012), M.engr, 0, 0.55, 0.268, 'stole').rotation.x = -0.155;
  add(new THREE.LatheGeometry([[0.17, 1.55], [0.21, 1.68], [0.235, 1.79]].map(p => new THREE.Vector2(p[0], p[1])), 20, PI * 0.55, PI * 0.9), M.engr, 0, 0, 0, 'high_collar');
  // staff
  add(new THREE.CylinderGeometry(0.02, 0.02, 2.3, 10), M.dark, 0, 1.17, sz, 'staff_shaft');
  for (const y of [0.3, 0.85, 1.7, 2.15]) bead(0.023, 0.006, M.brass, null, y, 'staff_band').position.z = sz;
  add(new THREE.ConeGeometry(0.03, 0.1, 8), M.steel, 0, 0.04, sz, 'staff_ferrule').rotation.x = PI;
  add(lathe([[0.02, 2.28], [0.055, 2.33], [0.03, 2.38]], 14), M.brass, 0, 0, sz, 'staff_collar');
  add(new THREE.TorusGeometry(0.13, 0.014, 8, 30), M.brass, 0, 2.51, sz, 'staff_ring');
  add(new THREE.SphereGeometry(0.05, 16, 12), M.glow, 0, 2.51, sz, 'staff_orb');
  const orbit = add(new THREE.TorusGeometry(0.088, 0.004, 6, 28), M.glow, 0, 2.51, sz, 'staff_orbit'); orbit.rotation.x = 1.1;
  for (let i = 0; i < 3; i++) add(new THREE.SphereGeometry(0.014, 8, 6), M.glow, Math.cos(i * 2.094) * 0.088, 2.51 + Math.sin(i * 2.094) * 0.04, sz + Math.sin(i * 2.094) * 0.078, 'staff_satellite');
  for (const s of [-1, 1]) spikeOn(knight, V(s * 0.095, 2.6, sz), V(s * 0.35, 1, 0), 0.17, 0.022, M.brass, 'staff_horn', 0.5);
  spikeOn(knight, V(0, 2.64, sz), V(0, 1, 0), 0.14, 0.018, M.steel, 'staff_spike', 0.5);
  // helm: tall pointed great helm, glowing cross slit, crown of spikes, halo
  mesh(lathe([[0.001, 2.0], [0.03, 1.96], [0.07, 1.87], [0.105, 1.79], [0.118, 1.72], [0.114, 1.65], [0.1, 1.61], [0.112, 1.585], [0.116, 1.58]], 30), M.steel, head, 0, 0, 0, 'helm').scale.set(1, 1, 1.1);
  const arc = (r, h, y, a, mat, name) => { const m = mesh(new THREE.CylinderGeometry(r, r, h, 24, 1, true, -a, 2 * a), mat, head, 0, y, 0, name); m.scale.z = 1.1; };
  arc(0.1195, 0.042, 1.735, 0.9, M.brass, 'visor_cross_bar'); arc(0.1215, 0.013, 1.735, 0.78, M.glow, 'visor_slit');
  mesh(new THREE.BoxGeometry(0.038, 0.15, 0.01), M.brass, head, 0, 1.685, 0.127, 'visor_cross_post');
  mesh(new THREE.BoxGeometry(0.012, 0.13, 0.012), M.glow, head, 0, 1.685, 0.129, 'visor_slit_vertical');
  for (let i = -3; i <= 3; i++) spikeOn(head, V(Math.sin(i * 0.5) * 0.108, 1.8, Math.cos(i * 0.5) * 0.118), V(Math.sin(i * 0.5) * 0.5, 1, Math.cos(i * 0.5) * 0.5), 0.1 - Math.abs(i) * 0.012, 0.014, M.brass, 'crown_spike', 0.6);
  mesh(new THREE.TorusGeometry(0.21, 0.009, 6, 36), M.brass, head, 0, 1.8, -0.1, 'halo');
  mesh(new THREE.TorusGeometry(0.188, 0.004, 6, 36), M.glow, head, 0, 1.8, -0.1, 'halo_light');
  for (let i = 0; i < 8; i++) mesh(new THREE.SphereGeometry(0.009, 8, 6), M.glow, head, Math.cos(i * PI / 4) * 0.21, 1.8 + Math.sin(i * PI / 4) * 0.21, -0.1, 'halo_node');
}

// ================= ROGUE: light plate, hooded raven-beak helm, half cape, twin daggers =================
function buildRogue() {
  const hand = (s) => V(s * 0.31, 1.0, 0.24);
  const head = humanoid({ w: 0.78, k: 0.72, lx: 0.12, pack: 0.55, cloth: M.red, style: 'bracer', legExtra: rogueLeg, paul: (s) => s < 0 ? 0.15 : 0.105,
    arm: (s) => { const G = hand(s); return { S: V(s * 0.27, 1.41, 0), E: V(s * 0.35, 1.12, -0.16), W: V(G.x, G.y + 0.012, G.z - 0.13), G }; } });
  for (const s of [-1, 1]) {                                                           // daggers, reverse grip
    const G = hand(s);
    add(new THREE.CylinderGeometry(0.016, 0.016, 0.17, 10), M.leather, G.x, G.y, G.z, 'dagger_grip');
    add(new THREE.SphereGeometry(0.022, 10, 8), M.brass, G.x, G.y + 0.1, G.z, 'dagger_pommel');
    add(new THREE.BoxGeometry(0.075, 0.014, 0.03), M.brass, G.x, G.y - 0.092, G.z, 'dagger_guard');
    add(new THREE.CylinderGeometry(0.03, 0.03, 0.3, 4), M.steel, G.x, G.y - 0.25, G.z, 'dagger_blade').scale.set(1, 1, 0.22);
    add(new THREE.ConeGeometry(0.03, 0.09, 4), M.steel, G.x, G.y - 0.445, G.z, 'dagger_tip').scale.set(1, -1, 0.22);
    add(new THREE.BoxGeometry(0.008, 0.27, 0.016), M.glow, G.x, G.y - 0.255, G.z, 'dagger_core');
  }
  add(new THREE.LatheGeometry([[0.19, 1.52], [0.3, 1.25], [0.34, 0.98], [0.33, 0.9]].map(p => new THREE.Vector2(p[0], p[1])), 16, PI * 0.85, PI * 0.75), M.red, 0, 0, 0, 'half_cape');
  const scarf = add(new THREE.TorusGeometry(0.125, 0.04, 8, 20), M.red, 0, 1.565, 0, 'scarf'); scarf.rotation.x = PI / 2; scarf.scale.set(1, 0.9, 1);
  spikeOn(knight, V(0.08, 1.55, -0.12), V(0.3, -1, -0.5), 0.42, 0.055, M.red, 'scarf_tail', 0.25);
  add(new THREE.BoxGeometry(0.05, 0.52, 0.012), M.under, 0, 1.3, 0.2, 'bandolier').rotation.z = 0.62;
  for (let i = 0; i < 4; i++) {
    const t = -0.17 + i * 0.11, x = -Math.sin(0.62) * t, y = 1.3 + Math.cos(0.62) * t;
    add(new THREE.BoxGeometry(0.02, 0.075, 0.01), M.steel, x, y, 0.21, 'throwing_knife').rotation.z = 0.62 + PI / 2;
    add(new THREE.SphereGeometry(0.007, 6, 5), M.glow, x, y, 0.217, 'knife_light');
  }
  for (const s of [-1, 1]) add(new THREE.BoxGeometry(0.06, 0.07, 0.04), M.dark, s * 0.15, 0.98, 0.1, 'belt_pouch');
  // helm: skull cap, sculpted raven mask (one shell: hooked beak, brow, slanted eye slits), deep hood with a
  // pointed brim, and a cloth mantle so the hood runs into the shoulders
  mesh(lathe(DOME, 30), M.dark, head, 0, 0, 0, 'skull_cap').scale.set(1, 1, 1.1);
  const RP = [[1.5, 0.05], [1.54, 0.105], [1.6, 0.122], [1.67, 0.085], [1.74, 0.012], [1.8, 0], [1.84, 0]];
  const rz = (x, y) => { const ax = Math.abs(x);
    let z = 0.032 + 0.115 * Math.sqrt(Math.max(0, 1 - (x / 0.125) ** 2));
    z += gProf(RP, y) * Math.exp(-((x / (0.026 + 0.03 * gSmooth((y - 1.66) / 0.1))) ** 2));        // hooked beak
    z += 0.014 * Math.exp(-((gDistSeg(ax, y, 0.012, 1.762, 0.105, 1.812) / 0.012) ** 2));        // brow
    z -= 0.01 * Math.exp(-((Math.hypot(ax - 0.05, (y - 1.745) * 1.6) / 0.028) ** 2));            // eye socket
    return z * (1 - 0.3 * gSmooth((y - 1.79) / 0.06)); };
  const rf = (x, y) => { const ax = Math.abs(x);
    let f = Math.min((y > 1.73 ? 0.108 : 0.108 - 0.5 * (1.73 - y)) - ax, 1.8 + 0.3 * ax - y, y - 1.512);
    const dx = ax - 0.05, dy = y - 1.745, u = dx * 0.88 + dy * 0.48, v = -dx * 0.48 + dy * 0.88;
    return Math.min(f, (Math.sqrt((u / 0.031) ** 2 + (v / 0.0085) ** 2) - 1) * 0.01); };
  const ravenSteel = engravedMaterial(M.dark, 512, (g, k) => {
    const S = 512, px = (x) => (x + 0.11) / 0.22 * S, py = (y) => (1 - (y - 1.5) / 0.34) * S, path = (pts, w) => stroke(g, pts.map(p => [px(p[0]), py(p[1])]), w * k);
    path([[0, 1.75], [0, 1.53]], 6);
    for (const s of [-1, 1]) {
      for (let q = 0; q < 5; q++) path([[s * 0.006, 1.7 - q * 0.03], [s * (0.03 + q * 0.004), 1.715 - q * 0.027], [s * (0.06 + q * 0.004), 1.745 - q * 0.02]], 6);   // feather strokes
      path(spiralPts(s * 0.082, 1.775, 0.014, 1.5, s > 0 ? 3 : 0.14, s, 0.65), 6);
      path([[s * 0.02, 1.775], [s * 0.06, 1.795], [s * 0.1, 1.82]], 5);
    }
  }, 'raven_mask_steel');
  shell(head, [-0.11, 0.11, 1.5, 1.84], 56, 80, (x, y) => [x, y, rz(x, y)], rf, ravenSteel, 'raven_mask');
  for (const s of [-1, 1]) {
    mesh(new THREE.BoxGeometry(0.066, 0.022, 0.004), M.glow, head, s * 0.05, 1.745, 0.121, 'eye_glow').rotation.set(0, s * 0.5, s * 0.5);
    for (let q = 0; q < 3; q++) mesh(new THREE.SphereGeometry(0.005, 6, 5), M.glow, head, s * (0.03 - q * 0.004), 1.66 - q * 0.022, 0.2 + q * 0.012, 'breath_vent');
  }
  // hood: deep cowl drawn back into a hanging point, with a rolled edge framing the mask
  mesh(new THREE.SphereGeometry(0.15, 22, 14, PI / 2 + 0.75, PI * 2 - 1.5), M.red, head, 0, 1.735, -0.02, 'hood').scale.set(1.02, 1.12, 1.22);
  const hpk = along(V(0, 1.8, -0.1), V(0, 1.6, -0.4), 'hood_point', head);
  mesh(new THREE.ConeGeometry(0.105, hpk.userData.len, 14), M.red, hpk, 0, hpk.userData.len / 2, 0, 'hood_point');
  mesh(new THREE.TorusGeometry(0.112, 0.02, 8, 26), M.red, head, 0, 1.742, 0.092, 'hood_edge').scale.set(1, 1.18, 1);
  add(lathe([[0.125, 1.66], [0.15, 1.61], [0.195, 1.555], [0.225, 1.52], [0.228, 1.508]], 24), M.red, 0, 0, 0, 'mantle');
}

// ================= BEAST: four-legged carnivore construct in the same plate =================
function buildBeast() {
  const cy = 0.98;
  // carved scales that tile round every body plate
  const sc = engrave(512, (g, k) => { const S = 512; for (let r = 0; r < 9; r++) for (let c = -1; c < 7; c++) { const cx = (c + (r % 2) * 0.5) * S / 6, cy2 = S * (0.02 + r * 0.118), pts = []; for (let q = 0; q <= 10; q++) pts.push([cx + Math.cos(q / 10 * Math.PI) * S / 12, cy2 + Math.sin(q / 10 * Math.PI) * S * 0.1]); stroke(g, pts, 8 * k); } }, true);
  const scales = M.steel.clone(); scales.name = 'body_scale_steel'; scales.map = sc.map; scales.normalMap = sc.normalMap; scales.normalScale = new THREE.Vector2(1, 1);
  const seg = (a, b, r0, r1, name) => { const g = along(a, b, name), L = g.userData.len;
    mesh(new THREE.CylinderGeometry(r1 * 0.7, r0 * 0.7, L, 12), M.under, g, 0, L / 2, 0, name + '_undersuit');
    mesh(lathe([[r0 * 0.9, L * 0.06], [r0 * 1.12, L * 0.3], [r1, L * 0.9], [r1 * 1.08, L * 0.94]], 18), scales, g, 0, 0, 0, name + '_plate'); };
  const joint = (p, r, s) => { add(new THREE.SphereGeometry(r, 14, 10), M.steel, p.x, p.y, p.z, 'joint_cop');
    const f = add(new THREE.CylinderGeometry(r * 0.7, r * 0.7, 0.014, 16), M.brass, p.x + s * r * 0.96, p.y, p.z, 'joint_fan'); f.rotation.z = PI / 2;
    add(new THREE.SphereGeometry(0.013, 8, 6), M.glow, p.x + s * (r + 0.004), p.y, p.z, 'joint_light'); };
  const paw = (s, p, from) => { seg(from, V(p.x, 0.09, p.z), 0.088, 0.075, 'pastern');
    add(new THREE.CylinderGeometry(0.072, 0.082, 0.09, 14), M.dark, p.x, 0.045, p.z, 'paw_block');
    for (let i = 0; i < 3; i++) add(new THREE.SphereGeometry(0.11 - i * 0.007, 16, 8, 0, PI * 2, 0, PI / 2), scales, p.x, 0.015, p.z + 0.06 + i * 0.062, 'paw_lame_' + i).scale.set(0.98, 0.8 - i * 0.12, 0.62);
    add(new THREE.BoxGeometry(0.24, 0.02, 0.34), M.dark, p.x, 0.01, p.z + 0.1, 'paw_sole');
    for (const c of [-0.084, -0.028, 0.028, 0.084]) add(new THREE.ConeGeometry(0.021, 0.16, 8), M.brass, p.x + c, 0.04, p.z + 0.31, 'claw').rotation.x = PI / 2 + 0.45; };
  // body
  add(new THREE.CapsuleGeometry(0.19, 1.0, 6, 16), M.under, 0, cy - 0.03, -0.08, 'spine_undersuit').rotation.x = PI / 2;
  add(zLathe([[0.17, 0.74], [0.27, 0.64], [0.34, 0.44], [0.35, 0.26], [0.3, 0.08], [0.225, -0.03], [0.232, -0.04]], 26, 0.07, 78), scales, 0, cy, 0, 'chest');
  add(new THREE.SphereGeometry(0.17, 18, 12), M.steel, 0, cy, 0.7, 'chest_front').scale.set(1, 1, 0.45);
  add(new THREE.TorusGeometry(0.172, 0.012, 6, 26), M.brass, 0, cy, 0.74, 'chest_rim');
  for (let i = 0; i < 4; i++) add(zLathe([[0.215 - i * 0.008, -0.02 - i * 0.095], [0.24 - i * 0.008, -0.14 - i * 0.095]]), scales, 0, cy - 0.02 - i * 0.012, 0, 'waist_lame_' + i);
  add(zLathe([[0.2, -0.4], [0.27, -0.52], [0.28, -0.68], [0.2, -0.82], [0.09, -0.88]], 20, 0.05, 60), scales, 0, cy - 0.06, 0, 'haunch');
  add(new THREE.TorusGeometry(0.05, 0.012, 8, 24), M.brass, 0, cy - 0.03, 0.782, 'chest_core_ring');
  add(new THREE.CylinderGeometry(0.04, 0.04, 0.012, 20), M.glow, 0, cy - 0.03, 0.78, 'chest_core').rotation.x = PI / 2;
  for (const s of [-1, 1]) {
    add(new THREE.BoxGeometry(0.008, 0.014, 0.34), M.glow, s * 0.348, cy - 0.02, 0.32, 'flank_light');
    const sh = V(s * 0.3, cy, 0.42), el = V(s * 0.44, 0.58, 0.28), wr = V(s * 0.42, 0.2, 0.44);
    pauldronParts(s, s * 0.33, cy + 0.06, 0.42, 0.17);
    seg(sh, el, 0.165, 0.12, 'foreleg_upper'); joint(el, 0.115, s); seg(el, wr, 0.12, 0.085, 'foreleg_lower'); joint(wr, 0.09, s);
    rod(V(el.x, el.y + 0.12, el.z - 0.1), V(wr.x, wr.y + 0.06, wr.z - 0.07), 0.012, M.brass, 'foreleg_piston');
    paw(s, V(s * 0.42, 0, 0.46), wr);
    spikeOn(knight, el.clone(), V(s * 0.4, 0.5, -1), 0.2, 0.035, M.dark, 'elbow_spike', 0.5);
    for (let q = 0; q < 3; q++) spikeOn(knight, V(s * 0.37, cy + 0.2 - q * 0.02, 0.44 - q * 0.08), V(s * 0.5, 1, -0.8), 0.16 - q * 0.02, 0.026, M.dark, 'shoulder_spike_' + q, 0.5);
    const hip = V(s * 0.3, cy - 0.06, -0.62), kn = V(s * 0.46, 0.6, -0.36), hk = V(s * 0.44, 0.36, -0.76);
    pauldronParts(s, s * 0.33, cy + 0.01, -0.62, 0.19);
    seg(hip, kn, 0.2, 0.135, 'hind_upper'); joint(kn, 0.13, s); seg(kn, hk, 0.125, 0.09, 'hind_mid'); joint(hk, 0.095, s);
    rod(V(kn.x, kn.y + 0.1, kn.z - 0.12), V(hk.x, hk.y + 0.05, hk.z + 0.07), 0.012, M.brass, 'hind_piston');
    paw(s, V(s * 0.44, 0, -0.68), hk);
    spikeOn(knight, hk.clone(), V(s * 0.2, 0.6, -1), 0.2, 0.035, M.dark, 'hock_spike', 0.5);
    for (let q = 0; q < 3; q++) spikeOn(knight, V(s * 0.37, cy + 0.17 - q * 0.02, -0.6 - q * 0.08), V(s * 0.5, 1, -0.8), 0.16 - q * 0.02, 0.026, M.dark, 'hip_spike_' + q, 0.5);
    // reactor stacks and cables
    add(new THREE.CylinderGeometry(0.055, 0.055, 0.012, 20), M.glow, s * 0.146, 1.37, 0.15, 'drum_cap').rotation.z = PI / 2;
    const st = along(V(s * 0.1, 1.4, 0.1), V(s * 0.18, 1.68, -0.14), 'exhaust'), SL = st.userData.len;
    mesh(lathe([[0.03, 0], [0.036, SL * 0.6], [0.046, SL], [0.036, SL - 0.005], [0.026, SL - 0.03]], 18), M.dark, st, 0, 0, 0, 'exhaust_stack');
    bead(0.046, 0.007, M.brass, st, SL, 'exhaust_rim');
    mesh(new THREE.CylinderGeometry(0.026, 0.026, 0.006, 14), M.glow, st, 0, SL - 0.03, 0, 'exhaust_glow');
    cable([V(s * 0.12, 1.34, 0.08), V(s * 0.25, 1.28, -0.2), V(s * 0.22, 1.18, -0.5)], 0.016, 'haunch_cable');
  }
  const drum = add(new THREE.CylinderGeometry(0.078, 0.078, 0.28, 24), M.dark, 0, 1.37, 0.15, 'reactor_drum'); drum.rotation.z = PI / 2;
  for (const x of [-0.09, 0, 0.09]) add(new THREE.TorusGeometry(0.081, 0.011, 8, 24), M.brass, x, 1.37, 0.15, 'drum_rib').rotation.y = PI / 2;
  [[0.6, 1.25], [0.42, 1.32], [-0.14, 1.2], [-0.34, 1.16], [-0.54, 1.18], [-0.72, 1.16]].forEach((p, i) => {
    const fin = add(new THREE.ConeGeometry(0.044, 0.24 - i * 0.012, 4), M.dark, 0, p[1] + 0.03, p[0], 'dorsal_fin_' + i); fin.rotation.x = -0.6; fin.scale.set(0.3, 1, 1);
  });
  // long neck rising to a dragon head
  const N = [[1.04, 0.66, 0.17], [1.2, 0.84, 0.15], [1.3, 0.96, 0.135]];
  for (let i = 0; i < N.length - 1; i++) {
    const g = along(V(0, N[i][0], N[i][1]), V(0, N[i + 1][0], N[i + 1][1]), 'neck'), NL = g.userData.len;
    mesh(new THREE.CylinderGeometry(N[i + 1][2] * 0.8, N[i][2] * 0.8, NL, 12), M.under, g, 0, NL / 2, 0, 'neck_undersuit');
    for (let q = 0; q < 3; q++) mesh(ring(N[i][2] * 0.95, N[i][2] * 1.15, NL * 0.4), scales, g, 0, NL * (0.18 + q * 0.32), 0, 'neck_lame');
    const fin = add(new THREE.ConeGeometry(0.03, 0.13, 4), M.steel, 0, N[i + 1][0] + 0.05, N[i + 1][1] - 0.12, 'neck_fin'); fin.rotation.x = -0.9; fin.scale.set(0.3, 1, 1);
  }
  const head = grp(0, 1.35, 1.0, 1.32, 1.3, 0.88, 'head'); head.rotation.x = 0.2; knight.add(head);   // broad, deep wedge
  // skull: an arched shell over (angle round the skull, distance along the snout)
  const hw = (z) => (z < 0.1 ? 0.15 : z < 0.3 ? 0.15 - (z - 0.1) * 0.3 : z < 0.56 ? 0.09 - (z - 0.3) * 0.08 : 0.069 * Math.sqrt(Math.max(0.02, 1 - ((z - 0.56) / 0.09) ** 2))) * (z < -0.1 ? Math.sqrt(Math.max(0.05, 1 - ((-0.1 - z) / 0.1) ** 2)) : 1);
  const HP = [[-0.2, 0.02], [-0.12, 0.1], [0, 0.125], [0.1, 0.115], [0.2, 0.075], [0.42, 0.06], [0.55, 0.072], [0.62, 0.045], [0.66, 0]], yb = -0.045;
  const skull = (a, z) => { const aa = Math.abs(a), h = gProf(HP, z), w = hw(z);
    const k = 1 + 0.3 * Math.exp(-(((aa - 0.62) / 0.26) ** 2 + ((z - 0.085) / 0.055) ** 2))                    // brow ridges
      + 0.07 * Math.exp(-((a / 0.16) ** 2)) * gSmooth((z - 0.12) / 0.1) * gSmooth((0.6 - z) / 0.1)            // ridge down the snout
      + 0.18 * Math.exp(-(((aa - 0.5) / 0.2) ** 2 + ((z - 0.575) / 0.035) ** 2));                             // nostril humps
    return [w * Math.sin(a) * k, yb + (h - yb) * Math.cos(a) * k, z]; };
  const skullF = (a, z) => { const aa = Math.abs(a);
    let f = Math.min(1.6 - aa - (z > 0.16 ? 0.11 * (gTri(z / 0.045) * 0.5 + 0.5) : 0), (z + 0.195) * 3, (0.655 - z) * 3);   // serrated lower edge
    const da = (aa - 0.64) * 0.13, dz = z - 0.168, u = da * 0.85 + dz * 0.52, v = -da * 0.52 + dz * 0.85;
    f = Math.min(f, (Math.sqrt((u / 0.042) ** 2 + (v / 0.017) ** 2) - 1) * 0.05);                             // slanted eye
    return Math.min(f, (Math.hypot((aa - 0.5) * 0.07, z - 0.585) - 0.011) * 4); };                            // nostril
  const scaleSteel = engravedMaterial(M.steel, 1024, (g, k) => {
    const S = 1024;
    for (let r = 0; r < 15; r++) for (let c = -1; c < 19; c++) {                                              // rows of overlapping scales on the back half
      const cx = (c + (r % 2) * 0.5) * S / 18, cy = S * (0.97 - r * 0.031), pts = [];
      for (let q = 0; q <= 10; q++) pts.push([cx + Math.cos(q / 10 * Math.PI) * S / 36, cy + Math.sin(q / 10 * Math.PI) * S * 0.026]);
      stroke(g, pts, 6 * k);
    }
    for (const d of [-1, 1]) { stroke(g, [[S * (0.5 + d * 0.035), S * 0.48], [S * (0.5 + d * 0.03), S * 0.1]], 7 * k); stroke(g, [[S * (0.5 + d * 0.11), S * 0.46], [S * (0.5 + d * 0.085), S * 0.14]], 5 * k); }
  }, 'dragon_scale_steel');
  shell(head, [-1.7, 1.7, -0.2, 0.66], 60, 84, skull, skullF, scaleSteel, 'dragon_skull');
  // lower jaw: the same kind of shell, hinged open
  const jaw = grp(0, -0.05, -0.02, 1, 1, 1, 'jaw'); jaw.rotation.x = 0.3; head.add(jaw);
  const JP = [[0, 0.05], [0.2, 0.046], [0.5, 0.036], [0.6, 0.016], [0.64, 0]];
  const jawSteel = scaleSteel.clone(); jawSteel.name = 'dragon_jaw_steel'; jawSteel.metalness = 0.45;   // the jaw faces the floor, so pure metal there reflects only dark and reads black
  shell(jaw, [-1.57, 1.57, 0, 0.645], 44, 60, (a, z) => [hw(z) * 0.9 * Math.sin(a), 0.03 - (gProf(JP, z) + 0.03) * Math.cos(a), z],
    (a, z) => Math.min(1.5 - Math.abs(a) - (z > 0.12 ? 0.11 * (gTri(z / 0.045 + 1) * 0.5 + 0.5) : 0), (z - 0.005) * 3, (0.64 - z) * 3), jawSteel, 'dragon_jaw');
  mesh(new THREE.BoxGeometry(0.04, 0.008, 0.34), M.glow, jaw, 0, -0.012, 0.24, 'tongue_glow');
  mesh(new THREE.SphereGeometry(0.06, 14, 10), M.glow, head, 0, -0.03, 0.04, 'throat_fire');
  for (const s of [-1, 1]) {
    for (let q = 0; q < 8; q++) {
      const z = 0.2 + q * 0.05;
      mesh(new THREE.ConeGeometry(0.011, 0.046, 6), M.brass, head, s * hw(z) * 0.97, yb - 0.035, z, 'upper_tooth').rotation.x = PI;
      if (q < 7) mesh(new THREE.ConeGeometry(0.01, 0.04, 6), M.brass, jaw, s * hw(z) * 0.86, 0.045, z + 0.02, 'lower_tooth');
    }
    mesh(new THREE.ConeGeometry(0.017, 0.11, 8), M.brass, head, s * 0.058, yb - 0.065, 0.55, 'upper_fang').rotation.x = PI;
    mesh(new THREE.ConeGeometry(0.014, 0.075, 8), M.brass, jaw, s * 0.045, 0.062, 0.575, 'lower_fang');
    mesh(new THREE.SphereGeometry(0.034, 14, 10), M.glow, head, s * 0.066, 0.05, 0.156, 'eye_glow');
    mesh(new THREE.BoxGeometry(0.006, 0.034, 0.006), M.under, head, s * 0.082, 0.07, 0.181, 'eye_pupil').rotation.set(-0.6, 0, -s * 0.5);
    mesh(new THREE.SphereGeometry(0.012, 8, 6), M.glow, head, s * 0.03, 0.055, 0.585, 'nostril_glow');
    const horn = (pts, mat, name) => { for (let q = 0; q < pts.length - 1; q++) {
      const a = V(s * pts[q][0], pts[q][1], pts[q][2]), b2 = V(s * pts[q + 1][0], pts[q + 1][1], pts[q + 1][2]), g = along(a, b2, name, head);
      mesh(new THREE.CylinderGeometry(pts[q + 1][3], pts[q][3], g.userData.len, 10), q === pts.length - 2 ? M.brass : mat, g, 0, g.userData.len / 2, 0, name + '_segment_' + q);
      mesh(new THREE.SphereGeometry(pts[q][3], 10, 6), mat, head, a.x, a.y, a.z, name + '_joint_' + q); } };
    horn([[0.085, 0.1, -0.06, 0.042], [0.13, 0.2, -0.22, 0.035], [0.17, 0.3, -0.42, 0.026], [0.19, 0.42, -0.62, 0.015], [0.18, 0.5, -0.8, 0.003]], M.dark, 'main_horn');
    horn([[0.135, 0.03, -0.1, 0.028], [0.2, 0.07, -0.25, 0.021], [0.25, 0.14, -0.42, 0.011], [0.26, 0.19, -0.56, 0.002]], M.dark, 'side_horn');
    for (let q = 0; q < 5; q++) spikeOn(head, V(s * 0.135, 0.03 - q * 0.032, -0.04), V(s * 0.75, 0.35 - q * 0.22, -0.7), 0.3 - q * 0.035, 0.05 - q * 0.005, M.steel, 'cheek_frill_' + q);
    for (let q = 0; q < 4; q++) spikeOn(head, V(s * (0.065 + q * 0.024), 0.14 - q * 0.014, 0.14 - q * 0.055), V(s * 0.35, 0.8, -0.75), 0.07 + q * 0.014, 0.017, M.dark, 'brow_spike_row_' + q, 0.6);
    horn([[0.05, 0.13, -0.1, 0.03], [0.07, 0.24, -0.26, 0.024], [0.085, 0.36, -0.44, 0.015], [0.085, 0.44, -0.6, 0.003]], M.dark, 'inner_horn');
    for (let q = 0; q < 3; q++) spikeOn(jaw, V(s * (0.105 - q * 0.02), 0.0, 0.12 + q * 0.13), V(s * 0.6, -1, -0.2), 0.065, 0.015, M.brass, 'jaw_spike_' + q, 0.6);
    spikeOn(head, V(s * 0.1, 0.135, 0.07), V(s * 0.3, 1, -0.5), 0.075, 0.016, M.brass, 'brow_spike', 0.6);
    spikeOn(jaw, V(s * 0.03, -0.035, 0.5), V(0, -1, 0.25), 0.075, 0.015, M.brass, 'chin_spike', 0.6);
  }
  spikeOn(head, V(0, 0.08, 0.565), V(0, 1, -0.3), 0.1, 0.022, M.brass, 'nose_horn', 0.6);
  for (let q = 0; q < 4; q++) spikeOn(head, V(0, 0.062 + q * 0.004, 0.46 - q * 0.08), V(0, 1, -0.5), 0.045 + q * 0.006, 0.014, M.dark, 'nasal_spike_' + q, 0.4);
  for (let q = 0; q < 3; q++) spikeOn(head, V(0, 0.125 - q * 0.012, -0.02 - q * 0.07), V(0, 1, -0.9), 0.1 - q * 0.015, 0.024, M.steel, 'crest_fin_' + q, 0.3);
  // segmented tail curling up to a blade
  const T = [[0.9, -0.86, 0.125], [0.78, -1.12, 0.105], [0.62, -1.36, 0.088], [0.52, -1.62, 0.072], [0.56, -1.88, 0.056], [0.76, -2.06, 0.043], [1.0, -2.08, 0.031]];
  for (let i = 0; i < T.length - 1; i++) {
    const g = along(V(0, T[i][0], T[i][1]), V(0, T[i + 1][0], T[i + 1][1]), 'tail'), TL = g.userData.len;
    mesh(new THREE.CylinderGeometry(T[i + 1][2] * 0.7, T[i][2] * 0.7, TL, 10), M.under, g, 0, TL / 2, 0, 'tail_undersuit');
    for (let q = 0; q < 2; q++) mesh(ring(T[i][2] * 1.15, T[i][2] * 0.9, TL * 0.55), scales, g, 0, TL * (0.25 + q * 0.5), 0, 'tail_lame');
    spikeOn(knight, V(0, T[i][0] + T[i][2] * 0.8, T[i][1]), V(0, 1, -0.7), 0.16 - i * 0.015, 0.028, M.dark, 'tail_spike_' + i, 0.3);
    add(new THREE.SphereGeometry(T[i][2] * 0.95, 10, 8), M.steel, 0, T[i][0], T[i][1], 'tail_joint');
  }
  const tb = spikeOn(knight, V(0, 1.0, -2.08), V(0, 1, 0.3), 0.36, 0.065, M.steel, 'tail_blade', 0.25);
  mesh(new THREE.BoxGeometry(0.008, 0.2, 0.02), M.glow, tb, 0, 0.12, 0, 'tail_blade_core');
}

// ---- display base ----
const base = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.58, 0.04, 48), new THREE.MeshStandardMaterial({ color: 0x4b4338, roughness: 0.8 }));
base.position.y = -0.02; base.name = 'base'; base.receiveShadow = true; scene.add(base);

function resize() {
  const w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h); camera.aspect = w / h;
  camera.fov = w < h ? 40 : 32; camera.updateProjectionMatrix();
}
window.addEventListener('resize', resize); resize();
let fN = 0, fT = performance.now();
renderer.setAnimationLoop(() => {
  controls.update(); renderer.render(scene, window.__cam || camera);
  if (++fN === 30) { const n = performance.now(); document.getElementById('tip').textContent = 'Drag to rotate, pinch to zoom  ·  ' + Math.round(30000 / (n - fT)) + ' fps'; fN = 0; fT = n; }
});

document.getElementById('spin').onclick = () => { controls.autoRotate = !controls.autoRotate; };
// ---- character switcher, export, test hooks ----
const BUILD = { knight: buildKnight, mage: buildMage, rogue: buildRogue, beast: buildBeast };
const VIEW = { knight: [0.98, 4.1, 1], mage: [1.2, 5.3, 1], rogue: [0.95, 4.0, 1], beast: [0.75, 7.8, 3.8] };   // look-at height, camera distance, base scale
const built = {}, btns = {}; let shown = null, shownName = '';
// Each character has its own metal, trim, glow and fluting, so the four do not read as one suit recoloured by cloth only.
const LOOK = {
  knight: { steel: CONFIG.steel, dark: CONFIG.darkSteel, trim: CONFIG.brass, glow: CONFIG.glow, flutes: 26, fluteDepth: 0.07 },      // bright fluted steel, brass, cyan
  mage:   { steel: 0x2b3760, dark: 0x151b33, trim: 0xdfe3ea, glow: 0xb48cff, flutes: 0, fluteDepth: 0, rough: 0.5 },                 // smooth midnight-blue plate, silver, violet
  rogue:  { steel: 0x2c2f34, dark: 0x16181b, trim: 0xb5673a, glow: 0xff4a3a, flutes: 44, fluteDepth: 0.03, rough: 0.72 },            // matt blackened steel with fine ribs, copper, red
  beast:  { steel: 0x8f1b1b, dark: 0x1e1a1a, trim: 0xd4a544, glow: 0xffa62b, flutes: 26, fluteDepth: 0.07, rough: 0.48 },            // crimson lacquer, black horn, gold, amber
};
const BASE = { steel: M.steel, dark: M.dark, brass: M.brass, glow: M.glow, engr: M.engr };
function applyLook(name) {
  const p = LOOK[name], c = (m, col) => { const n = m.clone(); n.color.set(col); n.name = m.name + '_' + name; return n; };
  const set = { steel: c(BASE.steel, p.steel), dark: c(BASE.dark, p.dark), brass: c(BASE.brass, p.trim), engr: c(BASE.engr, p.steel), glow: c(BASE.glow, 0x1a1210) };
  set.glow.emissive.set(p.glow);
  if (p.rough !== undefined) set.steel.roughness = set.engr.roughness = p.rough;
  Object.assign(M, name === 'knight' ? BASE : set); CONFIG.flutes = p.flutes; CONFIG.fluteDepth = p.fluteDepth;
}
function show(name) {
  if (shown) scene.remove(shown);
  if (!built[name]) {
    applyLook(name); knight = new THREE.Group(); knight.name = 'TechnoPlate_' + name; BUILD[name]();
    knight.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } }); built[name] = knight;
  }
  shown = built[name]; shownName = name; scene.add(shown);
  const v = VIEW[name]; controls.target.set(0, v[0], 0); base.scale.set(v[2], 1, v[2]);
  camera.position.set(v[1] * 0.36, v[0] + 0.3, v[1] * 0.93); controls.maxDistance = v[1] * 1.8;
  Object.assign(key.shadow.camera, { left: -1.4 * v[2], right: 1.4 * v[2], top: 2.9, bottom: -0.4 * v[2] }); key.shadow.camera.updateProjectionMatrix();
  let t = 0; shown.traverse(o => { if (o.isMesh) t += (o.geometry.index ? o.geometry.index.count : o.geometry.attributes.position.count) / 3; }); window.__tris = Math.round(t);
  for (const n in btns) btns[n].style.background = n === name ? '#2bb7c9' : '#1b1e25';
}
const bar = document.createElement('div'); bar.style.cssText = 'position:fixed;top:30px;left:0;right:0;display:flex;gap:6px;justify-content:center';
for (const n of Object.keys(BUILD)) {
  const b = document.createElement('button'); b.textContent = n[0].toUpperCase() + n.slice(1); b.style.cssText = 'font-size:14px;padding:8px 12px';
  b.onclick = () => show(n); bar.appendChild(b); btns[n] = b;
}
document.body.appendChild(bar);
document.getElementById('export').onclick = () => {
  new GLTFExporter().parse(shown, (buf) => {
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([buf], { type: 'model/gltf-binary' }));
    a.download = 'techno_plate_' + shownName + '.glb'; a.click();
  }, (e) => console.error(e), { binary: true });
};
window.__show = show;
// ---- poses for sprite frames (knight only): idle breathing, a six-frame walk with the sword carried upright, a battle stance
const POSES = {
  idle: (i) => { const b = [0, 0.5, 1, 0.5][i % 4]; return { upY: -0.022 * b, hip: [-0.05 * b, -0.05 * b], knee: [0.1 * b, 0.1 * b] }; },
  walk: (i) => { const leg = (t) => [-0.44 * Math.sin(t), 0.1 + 0.62 * Math.max(0, Math.cos(t))], th = i / 6 * Math.PI * 2, a = leg(th), b = leg(th + Math.PI); return { raised: true, turn: Math.PI / 2, lean: 0.07, hip: [a[0], b[0]], knee: [a[1], b[1]] }; },
  battle: () => ({ raised: true, lean: 0.28, yaw: 1.0, upY: -0.03, hip: [-0.85, 0.55], knee: [0.8, 0.05] }),
  guard: () => ({ raised: true, hip: [0, 0], knee: [0, 0] }),                       // standing, sword held upright in front
};
POSES.walk_thin = (i) => ({ ...POSES.walk(i), turn: 0 });                              // the walk with the blade edge-on to a side camera, as in the reference sprite
window.__pose = (name, i) => {
  const P = POSES[name](i), R = built.knight, r = R.userData.rig;
  R.rotation.y = P.yaw || 0; R.position.y = 0; r.up.position.y = 0.95 + (P.upY || 0); r.up.rotation.x = P.lean || 0;
  r.legs.forEach((l, k) => { l.hip.rotation.x = P.hip[k]; l.shin.rotation.x = P.knee[k]; });
  R.updateMatrixWorld(true); const box = new THREE.Box3(); r.legs.forEach(l => box.expandByObject(l.shin, true)); R.position.y = -box.min.y;
  if (window.__pxm) R.position.y = Math.round(R.position.y * window.__pxm) / window.__pxm;                                              // whole sprite pixels, so the body does not shimmer   // lowest foot on the ground
  r.sw.rotation.set(0, P.turn || 0, P.raised ? Math.PI : 0);                                                                          // turn: show the blade's flat to a side camera
  r.sw.position.y = 1.12 + (P.raised ? 0 : -(P.upY || 0) - R.position.y);                  // a planted sword stays on the ground
};
// keep the light on the viewer's upper left for every view, as sprites need: turn the lights with the camera
const L0 = [[key, -2.5, 4, 3], [fill, 1.8, 3, -4], [fill2, -2.5, 2, -3], [under, 0, -1.5, 3]];
window.__lights = (az) => { for (const [l, x, y, z] of L0) l.position.set(x * Math.cos(az) + z * Math.sin(az), y, -x * Math.sin(az) + z * Math.cos(az)); };
// sprite captures use a level camera with no perspective, so the ground is one row in every frame and view
const ortho = new THREE.OrthographicCamera(-1.2, 1.2, 1.6, -1.6, 0.1, 50);
window.__orthoView = (az) => { controls.autoRotate = false; const a = window.innerWidth / window.innerHeight; ortho.left = -1.6 * a; ortho.right = 1.6 * a; ortho.updateProjectionMatrix();
  ortho.position.set(Math.sin(az) * 10, 1.25, Math.cos(az) * 10); ortho.lookAt(0, 1.25, 0); ortho.updateMatrixWorld(); window.__cam = ortho; renderer.render(scene, ortho); };
window.__proj = () => { const p = (x, y, z) => { const v = new THREE.Vector3(x, y, z).project(window.__cam || camera); return [(v.x + 1) / 2 * window.innerWidth, (1 - v.y) / 2 * window.innerHeight]; }; const o = p(0, 0, 0), t = p(0, 1, 0); return [o[0], o[1], Math.hypot(t[0] - o[0], t[1] - o[1])]; };
// sprite capture: plain magenta backdrop, no base, no buttons, and flat matt materials (no reflections, no engraving maps)
// so each plate keeps one clean colour that shades from light to dark; used by the 3D-to-pixel script
const envTex = scene.environment, savedMat = new Map();
window.__sprite = (on) => {
  base.visible = !on; scene.background = new THREE.Color(on ? 0xff00ff : CONFIG.background); scene.environment = on ? null : envTex;
  const hemi = scene.children.find(c => c.isHemisphereLight);                       // one strong key light, weak fills: clear light and shadow sides
  const flat = on === 'flat';                                                       // 'flat' = even light only, so every pixel shows its plain material colour
  key.intensity = flat ? 0 : on ? 2.5 : 2.0; key.castShadow = !on; fill.intensity = flat ? 0 : on ? 0.8 : 2.4; fill2.intensity = flat ? 0 : on ? 0.4 : 1.2; under.intensity = flat ? 0 : on ? 0.3 : 0.9; hemi.intensity = flat ? 1.7 : on ? 0.7 : 1.0; hemi.groundColor.set(flat ? 0xffffff : 0x9a9fa8);
  for (const el of [bar, document.getElementById('ui'), document.getElementById('tip')]) el.style.display = on ? 'none' : '';
  shown.traverse(o => { if (!o.isMesh) return; const m = o.material;
    if (on) { if (!savedMat.has(m)) savedMat.set(m, { metalness: m.metalness, roughness: m.roughness, map: m.map, normalMap: m.normalMap, roughnessMap: m.roughnessMap }); Object.assign(m, { metalness: 0, roughness: 1, map: null, normalMap: null, roughnessMap: null }); }
    else if (savedMat.has(m)) Object.assign(m, savedMat.get(m));
    m.needsUpdate = true; });
};
window.__view = (az) => { window.__cam = null; controls.autoRotate = false; const v = VIEW[shownName]; camera.position.set(Math.sin(az) * v[1], v[0] + 0.27, Math.cos(az) * v[1]); controls.update(); renderer.render(scene, camera); };
show('knight');
