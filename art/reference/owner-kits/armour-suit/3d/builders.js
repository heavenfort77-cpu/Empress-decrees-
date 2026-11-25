// ================= MAGE: robed plate, tall cross-visored helm with halo, emitter staff =================
function buildMage() {
  const sz = 0.41;
  const head = humanoid({ w: 0.86, k: 0.8, lx: 0.13, pack: 0.8, cloth: M.violet, paul: () => 0.15,
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
  const head = humanoid({ w: 0.78, k: 0.72, lx: 0.12, pack: 0.55, cloth: M.red, paul: (s) => s < 0 ? 0.15 : 0,
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
  // helm: skull cap under a hood, raven beak, slanted eyes
  mesh(lathe(DOME, 30), M.dark, head, 0, 0, 0, 'skull_cap').scale.set(1, 1, 1.1);
  mesh(new THREE.SphereGeometry(0.15, 22, 14, PI / 2 + 0.75, PI * 2 - 1.5), M.red, head, 0, 1.73, -0.005, 'hood').scale.set(1, 1.1, 1.12);
  spikeOn(head, V(0, 1.87, -0.03), V(0, 0.25, -1), 0.17, 0.065, M.red, 'hood_peak', 0.5);
  const beak = mesh(new THREE.ConeGeometry(0.07, 0.25, 10), M.steel, head, 0, 1.685, 0.2, 'beak'); beak.rotation.x = PI / 2 + 0.38; beak.scale.set(0.72, 1, 0.9);
  const ridge = mesh(new THREE.BoxGeometry(0.01, 0.012, 0.22), M.brass, head, 0, 1.722, 0.2, 'beak_ridge'); ridge.rotation.x = 0.38;
  for (const s of [-1, 1]) {
    mesh(new THREE.BoxGeometry(0.075, 0.022, 0.05), M.dark, head, s * 0.056, 1.778, 0.105, 'brow').rotation.set(0.4, 0, s * 0.5);
    mesh(new THREE.BoxGeometry(0.048, 0.014, 0.02), M.glow, head, s * 0.056, 1.752, 0.118, 'eye').rotation.set(0, s * 0.4, s * 0.5);
    for (let q = 0; q < 2; q++) mesh(new THREE.SphereGeometry(0.006, 6, 5), M.glow, head, s * (0.04 - q * 0.012), 1.66 - q * 0.02, 0.2 + q * 0.04, 'breath_vent');
  }
}

// ================= BEAST: four-legged carnivore construct in the same plate =================
function buildBeast() {
  const cy = 0.98;
  const seg = (a, b, r0, r1, name) => { const g = along(a, b, name), L = g.userData.len;
    mesh(new THREE.CylinderGeometry(r1 * 0.7, r0 * 0.7, L, 12), M.under, g, 0, L / 2, 0, name + '_undersuit');
    mesh(lathe([[r0 * 0.9, L * 0.06], [r0 * 1.12, L * 0.3], [r1, L * 0.9], [r1 * 1.08, L * 0.94]], 18), M.steel, g, 0, 0, 0, name + '_plate'); };
  const joint = (p, r, s) => { add(new THREE.SphereGeometry(r, 14, 10), M.steel, p.x, p.y, p.z, 'joint_cop');
    const f = add(new THREE.CylinderGeometry(r * 0.7, r * 0.7, 0.014, 16), M.brass, p.x + s * r * 0.96, p.y, p.z, 'joint_fan'); f.rotation.z = PI / 2;
    add(new THREE.SphereGeometry(0.013, 8, 6), M.glow, p.x + s * (r + 0.004), p.y, p.z, 'joint_light'); };
  const paw = (s, p, from) => { seg(from, V(p.x, 0.09, p.z), 0.06, 0.052, 'pastern');
    add(new THREE.CylinderGeometry(0.072, 0.082, 0.09, 14), M.dark, p.x, 0.045, p.z, 'paw_block');
    for (let i = 0; i < 3; i++) add(new THREE.SphereGeometry(0.088 - i * 0.006, 16, 8, 0, PI * 2, 0, PI / 2), M.steel, p.x, 0.015, p.z + 0.06 + i * 0.055, 'paw_lame_' + i).scale.set(0.98, 0.8 - i * 0.12, 0.62);
    add(new THREE.BoxGeometry(0.19, 0.02, 0.3), M.dark, p.x, 0.01, p.z + 0.09, 'paw_sole');
    for (const c of [-0.058, 0, 0.058]) add(new THREE.ConeGeometry(0.017, 0.11, 8), M.brass, p.x + c, 0.036, p.z + 0.27, 'claw').rotation.x = PI / 2 + 0.45; };
  // body
  add(new THREE.CapsuleGeometry(0.19, 1.0, 6, 16), M.under, 0, cy - 0.03, -0.08, 'spine_undersuit').rotation.x = PI / 2;
  add(zLathe([[0.17, 0.74], [0.27, 0.64], [0.34, 0.44], [0.35, 0.26], [0.3, 0.08], [0.225, -0.03], [0.232, -0.04]], 26, 0.07, 78), M.steel, 0, cy, 0, 'chest');
  add(new THREE.SphereGeometry(0.17, 18, 12), M.under, 0, cy, 0.7, 'chest_front').scale.set(1, 1, 0.45);
  add(new THREE.TorusGeometry(0.172, 0.012, 6, 26), M.brass, 0, cy, 0.74, 'chest_rim');
  for (let i = 0; i < 4; i++) add(zLathe([[0.215 - i * 0.008, -0.02 - i * 0.095], [0.24 - i * 0.008, -0.14 - i * 0.095]]), M.steel, 0, cy - 0.02 - i * 0.012, 0, 'waist_lame_' + i);
  add(zLathe([[0.2, -0.4], [0.27, -0.52], [0.28, -0.68], [0.2, -0.82], [0.09, -0.88]], 20, 0.05, 60), M.steel, 0, cy - 0.06, 0, 'haunch');
  add(new THREE.TorusGeometry(0.05, 0.012, 8, 24), M.brass, 0, cy - 0.03, 0.782, 'chest_core_ring');
  add(new THREE.CylinderGeometry(0.04, 0.04, 0.012, 20), M.glow, 0, cy - 0.03, 0.78, 'chest_core').rotation.x = PI / 2;
  for (const s of [-1, 1]) {
    add(new THREE.BoxGeometry(0.008, 0.014, 0.34), M.glow, s * 0.348, cy - 0.02, 0.32, 'flank_light');
    const sh = V(s * 0.3, cy, 0.42), el = V(s * 0.35, 0.6, 0.28), wr = V(s * 0.35, 0.2, 0.44);
    pauldronParts(s, s * 0.33, cy + 0.06, 0.42, 0.17);
    seg(sh, el, 0.1, 0.08, 'foreleg_upper'); joint(el, 0.085, s); seg(el, wr, 0.08, 0.058, 'foreleg_lower'); joint(wr, 0.062, s);
    rod(V(el.x, el.y + 0.12, el.z - 0.1), V(wr.x, wr.y + 0.06, wr.z - 0.07), 0.012, M.brass, 'foreleg_piston');
    paw(s, V(s * 0.35, 0, 0.46), wr);
    const hip = V(s * 0.3, cy - 0.06, -0.62), kn = V(s * 0.37, 0.62, -0.36), hk = V(s * 0.37, 0.36, -0.76);
    pauldronParts(s, s * 0.33, cy + 0.01, -0.62, 0.19);
    seg(hip, kn, 0.12, 0.09, 'hind_upper'); joint(kn, 0.095, s); seg(kn, hk, 0.085, 0.06, 'hind_mid'); joint(hk, 0.065, s);
    rod(V(kn.x, kn.y + 0.1, kn.z - 0.12), V(hk.x, hk.y + 0.05, hk.z + 0.07), 0.012, M.brass, 'hind_piston');
    paw(s, V(s * 0.37, 0, -0.68), hk);
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
    const fin = add(new THREE.ConeGeometry(0.032, 0.14 - i * 0.008, 4), M.steel, 0, p[1], p[0], 'dorsal_fin_' + i); fin.rotation.x = -0.6; fin.scale.set(0.3, 1, 1);
  });
  // neck and head
  const nk = along(V(0, cy + 0.06, 0.66), V(0, 1.27, 1.0), 'neck'), nl = nk.userData.len;
  mesh(new THREE.CylinderGeometry(0.1, 0.14, nl, 14), M.under, nk, 0, nl / 2, 0, 'neck_undersuit');
  for (let i = 0; i < 4; i++) mesh(ring(0.135 - i * 0.012, 0.165 - i * 0.012, nl * 0.3), M.steel, nk, 0, nl * (0.14 + i * 0.22), 0, 'neck_lame_' + i);
  const head = grp(0, 1.31, 1.04, 1, 1, 1, 'head'); head.rotation.x = 0.22; knight.add(head);
  mesh(new THREE.SphereGeometry(1, 22, 14), M.steel, head, 0, 0, 0, 'cranium').scale.set(0.15, 0.125, 0.19);
  const sn = mesh(new THREE.CylinderGeometry(0.05, 0.108, 0.32, 8), M.steel, head, 0, -0.012, 0.27, 'snout'); sn.rotation.x = PI / 2; sn.scale.set(1, 1, 0.62);
  mesh(new THREE.SphereGeometry(0.036, 10, 8), M.dark, head, 0, 0.0, 0.435, 'nose').scale.set(1, 0.7, 0.8);
  const jaw = grp(0, -0.075, 0.07, 1, 1, 1, 'jaw'); jaw.rotation.x = 0.36; head.add(jaw);
  const jm = mesh(new THREE.CylinderGeometry(0.04, 0.09, 0.3, 8), M.steel, jaw, 0, -0.015, 0.17, 'jaw_plate'); jm.rotation.x = PI / 2; jm.scale.set(1, 1, 0.4);
  mesh(new THREE.BoxGeometry(0.1, 0.012, 0.26), M.glow, head, 0, -0.085, 0.24, 'maw_glow').rotation.x = 0.18;
  for (const s of [-1, 1]) {
    for (let q = 0; q < 5; q++) {
      const z = 0.13 + q * 0.058, x = s * (0.088 - q * 0.011);
      mesh(new THREE.ConeGeometry(0.01, 0.036, 6), M.brass, head, x, -0.078, z, 'upper_tooth').rotation.x = PI;
      mesh(new THREE.ConeGeometry(0.009, 0.03, 6), M.brass, jaw, x * 0.88, 0.022, z - 0.06, 'lower_tooth');
    }
    mesh(new THREE.ConeGeometry(0.017, 0.12, 8), M.brass, head, s * 0.046, -0.105, 0.4, 'sabre_fang').rotation.x = PI;
    mesh(new THREE.ConeGeometry(0.012, 0.055, 8), M.brass, jaw, s * 0.034, 0.03, 0.29, 'lower_fang');
    mesh(new THREE.BoxGeometry(0.1, 0.03, 0.09), M.dark, head, s * 0.075, 0.07, 0.115, 'brow').rotation.set(0.3, s * 0.35, s * 0.4);
    mesh(new THREE.BoxGeometry(0.06, 0.016, 0.02), M.glow, head, s * 0.082, 0.04, 0.155, 'eye').rotation.set(0, s * 0.6, s * 0.4);
    spikeOn(head, V(s * 0.09, 0.09, -0.02), V(s * 0.45, 0.6, -0.75), 0.24, 0.04, M.dark, 'ear_blade', 0.35);
    for (let q = 0; q < 3; q++) spikeOn(head, V(s * 0.12, -q * 0.04, 0.02 - q * 0.02), V(s * 0.85, 0.3 - q * 0.3, -0.7), 0.2 - q * 0.03, 0.036 - q * 0.004, M.steel, 'cheek_flare_' + q);
  }
  // segmented tail curling up to a blade
  const T = [[0.9, -0.88, 0.075], [0.8, -1.1, 0.065], [0.66, -1.3, 0.055], [0.62, -1.5, 0.046], [0.78, -1.64, 0.038], [1.02, -1.62, 0.03]];
  for (let i = 0; i < T.length - 1; i++) {
    const g = along(V(0, T[i][0], T[i][1]), V(0, T[i + 1][0], T[i + 1][1]), 'tail'), TL = g.userData.len;
    mesh(new THREE.CylinderGeometry(T[i + 1][2] * 0.7, T[i][2] * 0.7, TL, 10), M.under, g, 0, TL / 2, 0, 'tail_undersuit');
    for (let q = 0; q < 2; q++) mesh(ring(T[i][2] * 1.15, T[i][2] * 0.9, TL * 0.55), M.steel, g, 0, TL * (0.25 + q * 0.5), 0, 'tail_lame');
    add(new THREE.SphereGeometry(T[i][2] * 0.95, 10, 8), M.steel, 0, T[i][0], T[i][1], 'tail_joint');
  }
  const tb = spikeOn(knight, V(0, 1.02, -1.62), V(0, 1, 0.45), 0.3, 0.05, M.steel, 'tail_blade', 0.25);
  mesh(new THREE.BoxGeometry(0.008, 0.2, 0.02), M.glow, tb, 0, 0.12, 0, 'tail_blade_core');
}

