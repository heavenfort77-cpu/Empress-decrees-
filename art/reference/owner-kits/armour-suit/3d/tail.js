// ---- character switcher, export, test hooks ----
const BUILD = { knight: buildKnight, mage: buildMage, rogue: buildRogue, beast: buildBeast };
const VIEW = { knight: [0.98, 4.1, 1], mage: [1.2, 5.3, 1], rogue: [0.95, 4.0, 1], beast: [0.72, 7.0, 3.2] };   // look-at height, camera distance, base scale
const built = {}, btns = {}; let shown = null, shownName = '';
function show(name) {
  if (shown) scene.remove(shown);
  if (!built[name]) {
    knight = new THREE.Group(); knight.name = 'TechnoPlate_' + name; BUILD[name]();
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
window.__view = (az) => { controls.autoRotate = false; const v = VIEW[shownName]; camera.position.set(Math.sin(az) * v[1], v[0] + 0.27, Math.cos(az) * v[1]); controls.update(); renderer.render(scene, camera); };
show('knight');
