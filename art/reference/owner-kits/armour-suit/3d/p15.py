s=open('main.js').read()
def rep(a,b):
    global s
    assert a in s, a
    s=s.replace(a,b)
# ---------- shared sculpting helpers
rep("// ================= shared parts for the other characters =================\n", r'''// ================= shared parts for the other characters =================
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
''')
# ---------- rogue head
i=s.index("  // helm: skull cap under a hood, raven beak, slanted eyes"); j=s.index("// ================= BEAST")
rogue=r'''  // helm: skull cap, sculpted raven mask (one shell: hooked beak, brow, slanted eye slits), deep hood with a
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
  mesh(new THREE.SphereGeometry(0.15, 22, 14, PI / 2 + 0.75, PI * 2 - 1.5), M.red, head, 0, 1.73, -0.005, 'hood').scale.set(1, 1.1, 1.12);
  spikeOn(head, V(0, 1.87, -0.03), V(0, 0.25, -1), 0.17, 0.065, M.red, 'hood_peak', 0.5);
  spikeOn(head, V(0, 1.872, 0.045), V(0, -0.18, 1), 0.15, 0.085, M.red, 'hood_brim', 0.3);
  add(lathe([[0.125, 1.66], [0.16, 1.6], [0.24, 1.52], [0.3, 1.455], [0.305, 1.44]], 24), M.red, 0, 0, 0, 'mantle');
}

'''
s=s[:i]+rogue+s[j:]
# ---------- dragon head for the beast
i=s.index("  // neck and head\n"); j=s.index("  // segmented tail curling up to a blade")
dragon=r'''  // long neck rising to a dragon head
  const N = [[1.04, 0.66, 0.15], [1.36, 0.86, 0.125], [1.62, 0.98, 0.105], [1.78, 1.07, 0.095]];
  for (let i = 0; i < N.length - 1; i++) {
    const g = along(V(0, N[i][0], N[i][1]), V(0, N[i + 1][0], N[i + 1][1]), 'neck'), NL = g.userData.len;
    mesh(new THREE.CylinderGeometry(N[i + 1][2] * 0.8, N[i][2] * 0.8, NL, 12), M.under, g, 0, NL / 2, 0, 'neck_undersuit');
    for (let q = 0; q < 3; q++) mesh(ring(N[i][2] * 0.95, N[i][2] * 1.15, NL * 0.4), M.steel, g, 0, NL * (0.18 + q * 0.32), 0, 'neck_lame');
    const fin = add(new THREE.ConeGeometry(0.03, 0.13, 4), M.steel, 0, N[i + 1][0] + 0.05, N[i + 1][1] - 0.12, 'neck_fin'); fin.rotation.x = -0.9; fin.scale.set(0.3, 1, 1);
  }
  const head = grp(0, 1.8, 1.08, 1, 1, 1, 'head'); head.rotation.x = 0.3; knight.add(head);
  // skull: an arched shell over (angle round the skull, distance along the snout)
  const hw = (z) => (z < 0.1 ? 0.15 : z < 0.3 ? 0.15 - (z - 0.1) * 0.3 : z < 0.56 ? 0.09 - (z - 0.3) * 0.08 : 0.069 * Math.sqrt(Math.max(0.02, 1 - ((z - 0.56) / 0.09) ** 2))) * (z < -0.1 ? Math.sqrt(Math.max(0.05, 1 - ((-0.1 - z) / 0.1) ** 2)) : 1);
  const HP = [[-0.2, 0.02], [-0.12, 0.1], [0, 0.125], [0.1, 0.115], [0.2, 0.075], [0.42, 0.06], [0.55, 0.072], [0.62, 0.045], [0.66, 0]], yb = -0.045;
  const skull = (a, z) => { const aa = Math.abs(a), h = gProf(HP, z), w = hw(z);
    const k = 1 + 0.22 * Math.exp(-(((aa - 0.72) / 0.28) ** 2 + ((z - 0.1) / 0.07) ** 2))                    // brow ridges
      + 0.07 * Math.exp(-((a / 0.16) ** 2)) * gSmooth((z - 0.12) / 0.1) * gSmooth((0.6 - z) / 0.1)            // ridge down the snout
      + 0.18 * Math.exp(-(((aa - 0.5) / 0.2) ** 2 + ((z - 0.575) / 0.035) ** 2));                             // nostril humps
    return [w * Math.sin(a) * k, yb + (h - yb) * Math.cos(a) * k, z]; };
  const skullF = (a, z) => { const aa = Math.abs(a);
    let f = Math.min(1.6 - aa - (z > 0.16 ? 0.11 * (gTri(z / 0.045) * 0.5 + 0.5) : 0), (z + 0.195) * 3, (0.655 - z) * 3);   // serrated lower edge
    const da = (aa - 1.02) * 0.14, dz = z - 0.115, u = da * 0.85 + dz * 0.52, v = -da * 0.52 + dz * 0.85;
    f = Math.min(f, (Math.sqrt((u / 0.036) ** 2 + (v / 0.011) ** 2) - 1) * 0.05);                             // slanted eye
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
  const jaw = grp(0, -0.05, -0.02, 1, 1, 1, 'jaw'); jaw.rotation.x = 0.42; head.add(jaw);
  const JP = [[0, 0.05], [0.2, 0.046], [0.5, 0.036], [0.6, 0.016], [0.64, 0]];
  shell(jaw, [-1.57, 1.57, 0, 0.645], 44, 60, (a, z) => [hw(z) * 0.9 * Math.sin(a), 0.03 - (gProf(JP, z) + 0.03) * Math.cos(a), z],
    (a, z) => Math.min(1.5 - Math.abs(a) - (z > 0.12 ? 0.11 * (gTri(z / 0.045 + 1) * 0.5 + 0.5) : 0), (z - 0.005) * 3, (0.64 - z) * 3), scaleSteel, 'dragon_jaw');
  mesh(new THREE.BoxGeometry(0.09, 0.008, 0.5), M.glow, jaw, 0, -0.012, 0.3, 'tongue_glow');
  mesh(new THREE.SphereGeometry(0.06, 14, 10), M.glow, head, 0, -0.03, 0.04, 'throat_fire');
  for (const s of [-1, 1]) {
    for (let q = 0; q < 8; q++) {
      const z = 0.2 + q * 0.05;
      mesh(new THREE.ConeGeometry(0.011, 0.046, 6), M.brass, head, s * hw(z) * 0.97, yb - 0.035, z, 'upper_tooth').rotation.x = PI;
      if (q < 7) mesh(new THREE.ConeGeometry(0.01, 0.04, 6), M.brass, jaw, s * hw(z) * 0.86, 0.045, z + 0.02, 'lower_tooth');
    }
    mesh(new THREE.ConeGeometry(0.017, 0.11, 8), M.brass, head, s * 0.058, yb - 0.065, 0.55, 'upper_fang').rotation.x = PI;
    mesh(new THREE.ConeGeometry(0.014, 0.075, 8), M.brass, jaw, s * 0.045, 0.062, 0.575, 'lower_fang');
    mesh(new THREE.BoxGeometry(0.012, 0.034, 0.085), M.glow, head, s * 0.117, 0.04, 0.115, 'eye_glow').rotation.x = -0.45;
    mesh(new THREE.SphereGeometry(0.012, 8, 6), M.glow, head, s * 0.03, 0.055, 0.585, 'nostril_glow');
    const horn = (pts, mat, name) => { for (let q = 0; q < pts.length - 1; q++) {
      const a = V(s * pts[q][0], pts[q][1], pts[q][2]), b2 = V(s * pts[q + 1][0], pts[q + 1][1], pts[q + 1][2]), g = along(a, b2, name, head);
      mesh(new THREE.CylinderGeometry(pts[q + 1][3], pts[q][3], g.userData.len, 10), q === pts.length - 2 ? M.brass : mat, g, 0, g.userData.len / 2, 0, name + '_segment_' + q);
      mesh(new THREE.SphereGeometry(pts[q][3], 10, 6), mat, head, a.x, a.y, a.z, name + '_joint_' + q); } };
    horn([[0.085, 0.1, -0.06, 0.042], [0.13, 0.2, -0.22, 0.035], [0.17, 0.3, -0.42, 0.026], [0.19, 0.42, -0.62, 0.015], [0.18, 0.5, -0.8, 0.003]], M.dark, 'main_horn');
    horn([[0.135, 0.03, -0.1, 0.028], [0.2, 0.07, -0.25, 0.021], [0.25, 0.14, -0.42, 0.011], [0.26, 0.19, -0.56, 0.002]], M.dark, 'side_horn');
    for (let q = 0; q < 3; q++) spikeOn(head, V(s * 0.135, -0.02 - q * 0.035, -0.04), V(s * 0.8, 0.1 - q * 0.3, -0.7), 0.27 - q * 0.04, 0.046 - q * 0.005, M.steel, 'cheek_frill_' + q);
    spikeOn(head, V(s * 0.1, 0.135, 0.07), V(s * 0.3, 1, -0.5), 0.075, 0.016, M.brass, 'brow_spike', 0.6);
    spikeOn(jaw, V(s * 0.03, -0.035, 0.5), V(0, -1, 0.25), 0.075, 0.015, M.brass, 'chin_spike', 0.6);
  }
  spikeOn(head, V(0, 0.08, 0.565), V(0, 1, -0.3), 0.1, 0.022, M.brass, 'nose_horn', 0.6);
  for (let q = 0; q < 3; q++) spikeOn(head, V(0, 0.125 - q * 0.012, -0.02 - q * 0.07), V(0, 1, -0.9), 0.1 - q * 0.015, 0.024, M.steel, 'crest_fin_' + q, 0.3);
'''
s=s[:i]+dragon+s[j:]
rep("beast: [0.75, 6.5, 3.0] };","beast: [0.95, 7.6, 3.3] };")
open('main.js','w').write(s); print('patched')
