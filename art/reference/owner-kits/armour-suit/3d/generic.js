// ================= shared parts for the other characters =================
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
function armParts(s, S, E, W, k) {
  const ua = along(S, E, 'upper_arm'), ul = ua.userData.len;
  mesh(new THREE.CylinderGeometry(0.075 * k, 0.075 * k, ul, 14), M.under, ua, 0, ul / 2, 0, 'upper_arm_undersuit');
  for (let i = 0; i < 3; i++) mesh(ring((0.1 - i * 0.003) * k, (0.088 - i * 0.003) * k, 0.085), M.steel, ua, 0, ul * (0.42 + i * 0.2), 0, 'upper_arm_lame_' + i);
  add(new THREE.SphereGeometry(0.105 * k, 18, 12), M.steel, E.x, E.y, E.z, 'elbow_cop');
  const fan = add(new THREE.CylinderGeometry(0.07 * k, 0.07 * k, 0.014, 18), M.brass, E.x + s * 0.1 * k, E.y, E.z, 'elbow_fan'); fan.rotation.z = PI / 2;
  add(new THREE.SphereGeometry(0.014, 8, 6), M.glow, E.x + s * (0.1 * k + 0.008), E.y, E.z, 'elbow_light');
  const fa = along(E, W, 'forearm'), fl = fa.userData.len;
  mesh(new THREE.CylinderGeometry(0.068 * k, 0.078 * k, fl * 0.7, 18), M.steel, fa, 0, fl * 0.35, 0, 'vambrace');
  mesh(lathe([[0.122 * k, fl * 0.42], [0.128 * k, fl * 0.45], [0.112 * k, fl * 0.58], [0.082 * k, fl * 0.8], [0.064 * k, fl * 0.93], [0.068 * k, fl * 0.95]], 26), M.engr, fa, 0, 0, 0, 'gauntlet_cuff');
  bead(0.128 * k, 0.009, M.brass, fa, fl * 0.45, 'cuff_rim'); bead(0.1 * k, 0.0045, M.glow, fa, fl * 0.67, 'cuff_energy_seal');
  mesh(new THREE.CylinderGeometry(0.056 * k, 0.056 * k, fl * 0.1, 14), M.under, fa, 0, fl * 0.97, 0, 'wrist_joint');
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
    inGroup(grp(s * o.lx, 0, 0, o.k, 1, o.k, 'leg'), () => legParts(s, 0));
    const a = o.arm(s);
    armParts(s, a.S, a.E, a.W, o.k); gripHand(a.G, a.W, s, o.k);
    if (o.paul(s)) pauldronParts(s, a.S.x + s * 0.01, a.S.y + 0.005, 0, o.paul(s));
    else add(new THREE.SphereGeometry(0.095, 16, 10), M.dark, a.S.x, a.S.y, 0, 'shoulder_cap');
  }
  coreParts(1.475, 0.203 * o.w);
  const head = grp(0, -0.105, 0, 1.08, 1.08, 1.08, 'head'); knight.add(head); return head;
}
const DOME = [[0.001, 1.875], [0.05, 1.868], [0.09, 1.84], [0.112, 1.79], [0.118, 1.73], [0.114, 1.66], [0.1, 1.61], [0.112, 1.585], [0.116, 1.58]];
