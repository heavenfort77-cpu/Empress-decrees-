s=open('main.js').read()
def rep(a,b):
    global s
    assert s.count(a)==1, (s.count(a), a)
    s=s.replace(a,b)
rep("function buildKnight() {\ntorsoParts();\n","""function buildKnight() {
// groups that can move: the upper body (pivot at the pelvis), each leg (hip and knee pivots) and the sword
const root = knight, up = grp(0, 0.95, 0, 1, 1, 1, 'upper'), upIn = grp(0, -0.95, 0, 1, 1, 1, 'upper_parts'); root.add(up); up.add(upIn); knight = upIn;
torsoParts();
""")
rep("for (const s of [-1, 1]) legParts(s, s * 0.165);\n\n","""knight = root;
const legs = [-1, 1].map(s => { const g = grp(0, 0, 0, 1, 1, 1, 'leg_build'); root.add(g); knight = g; legParts(s, s * 0.165); knight = root; return rigLeg(g, s * 0.165); });
const sw = grp(0, 1.12, 0.33, 1, 1, 1, 'sword'), swIn = grp(0, -1.12, -0.33, 1, 1, 1, 'sword_parts'); upIn.add(sw); sw.add(swIn); knight = swIn;

""")
rep("// ---- extra tech, placed where medieval armour puts ornament ----","knight = upIn;\n// ---- extra tech, placed where medieval armour puts ornament ----")
i=s.index("// ================= MAGE"); k=s.rindex("}\n", 0, i)
s=s[:k]+"knight = root; root.userData.rig = { up, sw, legs };\n"+s[k:]
rep("function armParts(s, S, E, W, k, style) {","""// split a built leg into a thigh group that turns at the hip and a shin group that turns at the knee
function rigLeg(g, lx) {
  const hip = grp(lx, 0.92, 0, 1, 1, 1, 'hip'), shin = grp(0, -0.39, 0, 1, 1, 1, 'shin'); g.parent.add(hip); hip.add(shin); g.parent.updateMatrixWorld(true);
  const LOWER = /^(knee_lame_lower|greave|ankle_rim|shin_light|calf_piston|heel|ankle_guard|sabaton_lame_\\d|toe_cap|sole|poleyn|poleyn_fan|poleyn_fan_light|knee_light|knee_undersuit)$/;
  for (const c of [...g.children]) (LOWER.test(c.name) ? shin : hip).attach(c);
  g.parent.remove(g);
  const u = hip.getObjectByName('leg_undersuit'); if (u) { u.scale.y = 0.5; u.position.y += 0.17; }
  mesh(new THREE.CapsuleGeometry(0.085, 0.3, 4, 12), M.under, shin, 0, -0.2, 0, 'shin_undersuit');
  return { hip, shin };
}
function armParts(s, S, E, W, k, style) {""")
rep("window.__show = show;","""window.__show = show;
// ---- poses for sprite frames (knight only): idle breathing, a six-frame walk with the sword carried upright, a battle stance
const POSES = {
  idle: (i) => { const b = [0, 0.5, 1, 0.5][i % 4]; return { upY: -0.022 * b, hip: [-0.05 * b, -0.05 * b], knee: [0.1 * b, 0.1 * b] }; },
  walk: (i) => { const leg = (t) => [-0.44 * Math.sin(t), 0.1 + 0.62 * Math.max(0, Math.cos(t))], th = i / 6 * Math.PI * 2, a = leg(th), b = leg(th + Math.PI); return { raised: true, lean: 0.07, hip: [a[0], b[0]], knee: [a[1], b[1]] }; },
  battle: () => ({ raised: true, lean: 0.2, yaw: 0.55, upY: -0.02, hip: [-0.6, 0.42], knee: [0.55, 0.2] }),
};
window.__pose = (name, i) => {
  const P = POSES[name](i), R = built.knight, r = R.userData.rig;
  R.rotation.y = P.yaw || 0; R.position.y = 0; r.up.position.y = 0.95 + (P.upY || 0); r.up.rotation.x = P.lean || 0;
  r.legs.forEach((l, k) => { l.hip.rotation.x = P.hip[k]; l.shin.rotation.x = P.knee[k]; });
  R.updateMatrixWorld(true); const box = new THREE.Box3(); r.legs.forEach(l => box.expandByObject(l.shin)); R.position.y = -box.min.y;   // lowest foot on the ground
  r.sw.rotation.z = P.raised ? Math.PI : 0; r.sw.position.y = 1.12 + (P.raised ? 0 : -(P.upY || 0) - R.position.y);                  // a planted sword stays on the ground
};
window.__proj = () => { const p = (x, y, z) => { const v = new THREE.Vector3(x, y, z).project(camera); return [(v.x + 1) / 2 * window.innerWidth, (1 - v.y) / 2 * window.innerHeight]; }; const o = p(0, 0, 0), t = p(0, 1, 0); return [o[0], o[1], Math.hypot(t[0] - o[0], t[1] - o[1])]; };""")
open('main.js','w').write(s); print('patched')
