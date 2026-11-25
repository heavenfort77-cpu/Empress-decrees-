s=open('main.js').read()
def rep(a,b,cnt=1):
    global s
    assert s.count(a)>=1, a
    s=s.replace(a,b)
# ---------- lighting from below so undersides (dragon jaw) are not black
rep("scene.add(new THREE.HemisphereLight(0xffffff, 0x555a66, 0.9));","scene.add(new THREE.HemisphereLight(0xffffff, 0x9a9fa8, 1.0));\nconst under = new THREE.DirectionalLight(0xffffff, 0.9); under.position.set(0, -1.5, 3); scene.add(under);")
# ---------- distinct arm, shoulder and leg shapes per character
i=s.index("function armParts(s, S, E, W, k) {"); j=s.index("// closed fist round a vertical grip at G")
arm=r'''// arms differ by character: 'sleeve' = mage (cloth upper sleeve, wide trumpet cuff), 'bracer' = rogue (bare upper arm, pointed elbow, bladed bracer)
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
'''
s=s[:i]+arm+s[j:]
rep("inGroup(grp(s * o.lx, 0, 0, o.k, 1, o.k, 'leg'), () => legParts(s, 0));","inGroup(grp(s * o.lx, 0, 0, o.k, 1, o.k, 'leg'), () => { legParts(s, 0); if (o.legExtra) o.legExtra(s); });")
rep("armParts(s, a.S, a.E, a.W, o.k); gripHand","armParts(s, a.S, a.E, a.W, o.k, o.style); gripHand")
rep("    if (o.paul(s)) pauldronParts(s, a.S.x + s * 0.01, a.S.y + 0.005, 0, o.paul(s));\n    else add(new THREE.SphereGeometry(0.095, 16, 10), M.dark, a.S.x, a.S.y, 0, 'shoulder_cap');","    shoulderParts(s, a.S.x + s * 0.01, a.S.y + 0.005, o.paul(s), o.style);")
rep("cloth: M.violet, paul: () => 0.15,","cloth: M.violet, style: 'sleeve', paul: () => 0.15,")
rep("cloth: M.red, paul: (s) => s < 0 ? 0.15 : 0.105,","cloth: M.red, style: 'bracer', legExtra: rogueLeg, paul: (s) => s < 0 ? 0.15 : 0.105,")
# ---------- beast: dragon body
rep("function buildBeast() {\n  const cy = 0.98;","""function buildBeast() {
  const cy = 0.98;
  // carved scales that tile round every body plate
  const sc = engrave(512, (g, k) => { const S = 512; for (let r = 0; r < 9; r++) for (let c = -1; c < 7; c++) { const cx = (c + (r % 2) * 0.5) * S / 6, cy2 = S * (0.02 + r * 0.118), pts = []; for (let q = 0; q <= 10; q++) pts.push([cx + Math.cos(q / 10 * Math.PI) * S / 12, cy2 + Math.sin(q / 10 * Math.PI) * S * 0.1]); stroke(g, pts, 8 * k); } }, true);
  const scales = M.steel.clone(); scales.name = 'body_scale_steel'; scales.map = sc.map; scales.normalMap = sc.normalMap; scales.normalScale = new THREE.Vector2(1, 1);""")
rep("26, 0.07, 78), M.steel, 0, cy, 0, 'chest');","26, 0.07, 78), scales, 0, cy, 0, 'chest');")
rep("]), M.steel, 0, cy - 0.02 - i * 0.012, 0, 'waist_lame_' + i);","]), scales, 0, cy - 0.02 - i * 0.012, 0, 'waist_lame_' + i);")
rep("20, 0.05, 60), M.steel, 0, cy - 0.06, 0, 'haunch');","20, 0.05, 60), scales, 0, cy - 0.06, 0, 'haunch');")
rep("18), M.steel, g, 0, 0, 0, name + '_plate'); };","18), scales, g, 0, 0, 0, name + '_plate'); };")
rep("const sh = V(s * 0.3, cy, 0.42), el = V(s * 0.35, 0.6, 0.28), wr = V(s * 0.35, 0.2, 0.44);","const sh = V(s * 0.3, cy, 0.42), el = V(s * 0.44, 0.58, 0.28), wr = V(s * 0.42, 0.2, 0.44);")
rep("paw(s, V(s * 0.35, 0, 0.46), wr);","paw(s, V(s * 0.42, 0, 0.46), wr);\n    spikeOn(knight, el.clone(), V(s * 0.4, 0.5, -1), 0.2, 0.035, M.dark, 'elbow_spike', 0.5);\n    for (let q = 0; q < 3; q++) spikeOn(knight, V(s * 0.37, cy + 0.2 - q * 0.02, 0.44 - q * 0.08), V(s * 0.5, 1, -0.8), 0.16 - q * 0.02, 0.026, M.dark, 'shoulder_spike_' + q, 0.5);")
rep("seg(sh, el, 0.135, 0.1, 'foreleg_upper'); joint(el, 0.1, s); seg(el, wr, 0.1, 0.07, 'foreleg_lower'); joint(wr, 0.075, s);","seg(sh, el, 0.165, 0.12, 'foreleg_upper'); joint(el, 0.115, s); seg(el, wr, 0.12, 0.085, 'foreleg_lower'); joint(wr, 0.09, s);")
rep("const hip = V(s * 0.3, cy - 0.06, -0.62), kn = V(s * 0.37, 0.62, -0.36), hk = V(s * 0.37, 0.36, -0.76);","const hip = V(s * 0.3, cy - 0.06, -0.62), kn = V(s * 0.46, 0.6, -0.36), hk = V(s * 0.44, 0.36, -0.76);")
rep("paw(s, V(s * 0.37, 0, -0.68), hk);","paw(s, V(s * 0.44, 0, -0.68), hk);\n    spikeOn(knight, hk.clone(), V(s * 0.2, 0.6, -1), 0.2, 0.035, M.dark, 'hock_spike', 0.5);\n    for (let q = 0; q < 3; q++) spikeOn(knight, V(s * 0.37, cy + 0.17 - q * 0.02, -0.6 - q * 0.08), V(s * 0.5, 1, -0.8), 0.16 - q * 0.02, 0.026, M.dark, 'hip_spike_' + q, 0.5);")
rep("seg(hip, kn, 0.16, 0.11, 'hind_upper'); joint(kn, 0.11, s); seg(kn, hk, 0.105, 0.07, 'hind_mid'); joint(hk, 0.078, s);","seg(hip, kn, 0.2, 0.135, 'hind_upper'); joint(kn, 0.13, s); seg(kn, hk, 0.125, 0.09, 'hind_mid'); joint(hk, 0.095, s);")
rep("seg(from, V(p.x, 0.09, p.z), 0.072, 0.062, 'pastern');","seg(from, V(p.x, 0.09, p.z), 0.088, 0.075, 'pastern');")
rep("new THREE.SphereGeometry(0.088 - i * 0.006, 16, 8, 0, PI * 2, 0, PI / 2), M.steel, p.x, 0.015, p.z + 0.06 + i * 0.055, 'paw_lame_' + i)","new THREE.SphereGeometry(0.11 - i * 0.007, 16, 8, 0, PI * 2, 0, PI / 2), scales, p.x, 0.015, p.z + 0.06 + i * 0.062, 'paw_lame_' + i)")
rep("add(new THREE.BoxGeometry(0.19, 0.02, 0.3), M.dark, p.x, 0.01, p.z + 0.09, 'paw_sole');","add(new THREE.BoxGeometry(0.24, 0.02, 0.34), M.dark, p.x, 0.01, p.z + 0.1, 'paw_sole');")
rep("for (const c of [-0.058, 0, 0.058]) add(new THREE.ConeGeometry(0.017, 0.11, 8), M.brass, p.x + c, 0.036, p.z + 0.27, 'claw').rotation.x = PI / 2 + 0.45; };","for (const c of [-0.084, -0.028, 0.028, 0.084]) add(new THREE.ConeGeometry(0.021, 0.16, 8), M.brass, p.x + c, 0.04, p.z + 0.31, 'claw').rotation.x = PI / 2 + 0.45; };")
rep("const fin = add(new THREE.ConeGeometry(0.032, 0.14 - i * 0.008, 4), M.steel, 0, p[1], p[0], 'dorsal_fin_' + i);","const fin = add(new THREE.ConeGeometry(0.044, 0.24 - i * 0.012, 4), M.dark, 0, p[1] + 0.03, p[0], 'dorsal_fin_' + i);")
rep("const T = [[0.9, -0.88, 0.075], [0.8, -1.1, 0.065], [0.66, -1.3, 0.055], [0.62, -1.5, 0.046], [0.78, -1.64, 0.038], [1.02, -1.62, 0.03]];","const T = [[0.9, -0.86, 0.125], [0.78, -1.12, 0.105], [0.62, -1.36, 0.088], [0.52, -1.62, 0.072], [0.56, -1.88, 0.056], [0.76, -2.06, 0.043], [1.0, -2.08, 0.031]];")
rep("for (let q = 0; q < 2; q++) mesh(ring(T[i][2] * 1.15, T[i][2] * 0.9, TL * 0.55), M.steel, g, 0, TL * (0.25 + q * 0.5), 0, 'tail_lame');","for (let q = 0; q < 2; q++) mesh(ring(T[i][2] * 1.15, T[i][2] * 0.9, TL * 0.55), scales, g, 0, TL * (0.25 + q * 0.5), 0, 'tail_lame');\n    spikeOn(knight, V(0, T[i][0] + T[i][2] * 0.8, T[i][1]), V(0, 1, -0.7), 0.16 - i * 0.015, 0.028, M.dark, 'tail_spike_' + i, 0.3);")
rep("const tb = spikeOn(knight, V(0, 1.02, -1.62), V(0, 1, 0.45), 0.3, 0.05, M.steel, 'tail_blade', 0.25);","const tb = spikeOn(knight, V(0, 1.0, -2.08), V(0, 1, 0.3), 0.36, 0.065, M.steel, 'tail_blade', 0.25);")
rep("for (let q = 0; q < 3; q++) mesh(ring(N[i][2] * 0.95, N[i][2] * 1.15, NL * 0.4), M.steel, g, 0, NL * (0.18 + q * 0.32), 0, 'neck_lame');","for (let q = 0; q < 3; q++) mesh(ring(N[i][2] * 0.95, N[i][2] * 1.15, NL * 0.4), scales, g, 0, NL * (0.18 + q * 0.32), 0, 'neck_lame');")
# ---------- dragon eyes: larger, on the forward slope under the brow, with a slit pupil
rep("1 + 0.22 * Math.exp(-(((aa - 0.72) / 0.28) ** 2 + ((z - 0.1) / 0.07) ** 2))","1 + 0.3 * Math.exp(-(((aa - 0.62) / 0.26) ** 2 + ((z - 0.085) / 0.055) ** 2))")
rep("const da = (aa - 1.02) * 0.14, dz = z - 0.115, u = da * 0.85 + dz * 0.52, v = -da * 0.52 + dz * 0.85;","const da = (aa - 0.64) * 0.13, dz = z - 0.168, u = da * 0.85 + dz * 0.52, v = -da * 0.52 + dz * 0.85;")
rep("f = Math.min(f, (Math.sqrt((u / 0.036) ** 2 + (v / 0.011) ** 2) - 1) * 0.05);                             // slanted eye","f = Math.min(f, (Math.sqrt((u / 0.042) ** 2 + (v / 0.017) ** 2) - 1) * 0.05);                             // slanted eye")
rep("mesh(new THREE.BoxGeometry(0.008, 0.018, 0.07), M.glow, head, s * 0.112, 0.036, 0.115, 'eye_glow').rotation.x = -0.5;","mesh(new THREE.SphereGeometry(0.034, 14, 10), M.glow, head, s * 0.066, 0.05, 0.156, 'eye_glow');\n    mesh(new THREE.BoxGeometry(0.006, 0.034, 0.006), M.under, head, s * 0.082, 0.07, 0.181, 'eye_pupil').rotation.set(-0.6, 0, -s * 0.5);")
rep("beast: [0.75, 6.6, 3.0] };","beast: [0.75, 7.8, 3.8] };")
open('main.js','w').write(s); print('patched')
