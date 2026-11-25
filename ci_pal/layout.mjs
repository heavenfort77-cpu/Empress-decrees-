// PREP-PAL test helper (CI and probes only, never in the game): the full palace plan read from index.html's own data literals
// (PAL_FULL_ROOMS, PAL_FULL_DOORS, PAL_FULL_PIECES, CONFIG.PALACE), rooms, doors and solids built as index.html builds them (lines ~2553-2760),
// so the art is placed on the game's real layout and checked against the game's real collision boxes.
export function layoutFrom(html) {
  const grab = (name) => { const i = html.indexOf('const ' + name + ' = '); if (i < 0) throw new Error('layout: ' + name + ' not found'); const a = html.indexOf('=', i) + 1;
    let d = 0, j = a; for (; j < html.length; j++) { const c = html[j]; if (c === '[' || c === '{') d++; else if (c === ']' || c === '}') { d--; if (d === 0) break; } }
    return Function('return (' + html.slice(a, j + 1) + ');')(); };
  const rooms0 = grab('PAL_FULL_ROOMS'), doors0 = grab('PAL_FULL_DOORS'), pieces0 = grab('PAL_FULL_PIECES');
  const pc = /PALACE: \{ origin: \[(-?\d+), (-?\d+)\], wallH: ([\d.]+), lowH: ([\d.]+), wallT: ([\d.]+), doorW: ([\d.]+), doorH: ([\d.]+)/.exec(html);
  if (!pc) throw new Error('layout: CONFIG.PALACE not found');
  const POX = +pc[1], POZ = +pc[2], t = +pc[5], w = +pc[6];
  const rooms = [], byId = {};
  for (const d of rooms0) {
    const r = { id: d.id, type: d.type, x0: POX + d.x0, x1: POX + d.x1, z0: POZ + d.z0, z1: POZ + d.z1, doors: [], school: d.school || null, solids: [], pieces: [],
      pillars: [], dais: null, spawn: d.spawn ? [POX + d.spawn[0], POZ + d.spawn[1]] : null };
    r.cx = (r.x0 + r.x1) / 2; r.cz = (r.z0 + r.z1) / 2;
    for (const q of pieces0[d.id] || []) r.pieces.push(Object.assign({}, q, { x: POX + q.x, z: POZ + q.z }));
    rooms.push(r); byId[r.id] = r;
  }
  const doors = [];
  for (const dd of doors0) {
    const A = byId[dd.a], B = byId[dd.b]; let vert, e;
    if (A.x1 === B.x0) { vert = true; e = A.x1; } else if (A.x0 === B.x1) { vert = true; e = A.x0; } else if (A.z1 === B.z0) { vert = false; e = A.z1; } else { vert = false; e = A.z0; }
    const c = (vert ? POZ : POX) + dd.at, d = { ra: A, rb: B, vert, e, c, w, x: vert ? e : c, z: vert ? c : e, open: false, locked: false };
    A.doors.push(d); B.doors.push(d); doors.push(d);
  }
  const sol = (r, x0, x1, z0, z1, kind) => r.solids.push({ x0, x1, z0, z1, kind });
  for (const r of rooms) {
    const hi = r.type === 'bridge' ? +pc[4] : +pc[3];
    const edges = [[false, r.z0, r.z0, r.z0 + t], [false, r.z1, r.z1 - t, r.z1], [true, r.x0, r.x0, r.x0 + t], [true, r.x1, r.x1 - t, r.x1]];
    for (const [vert, e, a, b] of edges) {
      const lo = vert ? r.z0 : r.x0, up = vert ? r.z1 : r.x1, gaps = [];
      for (const d of r.doors) if (d.vert === vert && d.e === e) gaps.push([d.c - d.w / 2, d.c + d.w / 2]);
      gaps.sort((p, q) => p[0] - q[0]); let u = lo;
      for (const [g0, g1] of gaps.concat([[up, up]])) { if (g0 - u > 0.01) { if (vert) sol(r, a, b, u, g0, 'wall'); else sol(r, u, g0, a, b, 'wall'); } u = g1; }
    }
    const pillar = (x, z) => { r.pillars.push([x, z]); sol(r, x - 0.6, x + 0.6, z - 0.6, z + 0.6, 'pillar'); };
    const block = (sx, sz, x, z, kind) => sol(r, x - sx / 2, x + sx / 2, z - sz / 2, z + sz / 2, kind);
    if (r.type === 'hall') { pillar(r.x0 + 3, r.z0 + 3); pillar(r.x1 - 3, r.z0 + 3); pillar(r.x0 + 3, r.z1 - 5); pillar(r.x1 - 3, r.z1 - 5);
      block(3, 8, r.doors.some((d) => d.vert && d.e === r.x0) ? r.x1 - 2.5 : r.x0 + 2.5, r.cz, 'stone'); }
    else if (r.type === 'court') { block(2, 2, r.cx - 8, r.cz - 4, 'stone'); block(2, 2, r.cx + 8, r.cz - 4, 'stone'); }
    else if (r.type === 'garden') { block(1.6, 1.6, r.x1 - 4, r.z1 - 6, 'planter'); block(1.6, 1.6, r.x1 - 4, r.z0 + 6, 'planter'); block(1.6, 1.6, r.x0 + 4, r.z0 + 6, 'planter'); }
    else if (r.type === 'core') { block(12, 6, r.cx, r.z0 + 4, 'dais'); r.dais = [r.cx, r.z0 + 4];
      pillar(r.x0 + 3, r.z0 + 10); pillar(r.x1 - 3, r.z0 + 10); pillar(r.x0 + 3, r.z1 - 5); pillar(r.x1 - 3, r.z1 - 5); }
    const H = { lion: [0.9, 1.1], huabiao: [0.7, 0.7], ding: [0.9, 0.9], smoke: [0.6, 0.6], clock: [0.7, 0.7], vat: [0.8, 0.8] };
    for (const p of r.pieces) if (H[p.type]) sol(r, p.x - H[p.type][0], p.x + H[p.type][0], p.z - H[p.type][1], p.z + H[p.type][1], p.type);
  }
  let bx0 = 1e9, bx1 = -1e9, bz0 = 1e9, bz1 = -1e9;
  for (const r of rooms) { bx0 = Math.min(bx0, r.x0); bx1 = Math.max(bx1, r.x1); bz0 = Math.min(bz0, r.z0); bz1 = Math.max(bz1, r.z1); }
  const schools = /SCHOOLS: (\[[^\]]*\])/.exec(html); 
  return { rooms, doors, byId, wallH: +pc[3], lowH: +pc[4], wallT: t, cx: (bx0 + bx1) / 2, cz: (bz0 + bz1) / 2, size: Math.max(bx1 - bx0, bz1 - bz0),
    schools: schools ? Function('return ' + schools[1])() : [] };
}
// Every room's art, doors and props from src/palace_art.js on the layout (what the integration does at the box code's places).
export function buildAll(PA, kit, L) {
  const arts = [];
  for (const r of L.rooms) {
    const art = PA.buildRoom(kit, r, L.rooms, { pillars: r.pillars, dais: r.dais, blocked: r.solids });
    const si = r.school ? L.schools.indexOf(r.school) : 0;
    for (const p of r.pieces) {
      if (p.type === 'lion') PA.addTo(art, PA.prop(kit, 'beast', p.x, p.z, (p.fz || 1) > 0 ? 0 : Math.PI));
      else if (p.type === 'ding') { PA.addTo(art, PA.ding(kit, p.x, p.z, si)); PA.standard(kit, art, r, p.x, p.z, si, r.solids); }
      else if (p.type === 'vat') PA.addTo(art, PA.prop(kit, 'vat', p.x, p.z, 0));
      else if (p.type === 'clock') PA.addTo(art, PA.prop(kit, 'clock', p.x, p.z, 0));
      else if (p.type === 'huabiao') PA.addTo(art, PA.prop(kit, 'huabiao', p.x, p.z, 0));
      else if (p.type === 'smoke') PA.addTo(art, PA.prop(kit, p.kind === 'crane' ? 'crane' : 'censer', p.x, p.z, 0));
      else if (p.type === 'mercury') PA.addTo(art, PA.mercury(kit, p.x - p.sx / 2, p.x + p.sx / 2, p.z - p.sz / 2, p.z + p.sz / 2));
    }
    arts.push(art);
  }
  for (const d of L.doors) { const h = PA.door(kit, d); d.art = h; PA.addTo(arts[L.rooms.indexOf(d.ra)], h); }
  return arts;
}
