// Ticket 10 checks (1200-1208): the palace camera (owner 24 Nov 15:43-15:46: wide = as far out as the 120 px floor allows, a room that fits is
// shown whole, a bigger one is revealed as you walk; close at attack distance; lens and tilt never change) and the room-layout minimap.
// Called from tests/run.mjs with its page-evaluate helper g, check(name, ok, detail), the browser and the test URL (layout=proto, bots=0).

// Every room of the full plan at one screen size: the player at the centre and 1.5 m inside each corner, after the pan settles (90 steps):
// his screen height against the floor, lens and tilt, and for rooms that fit whole, every room corner on screen.
function sizeProbe() {
  const G = __game, o = { n: 0, fitN: 0, fitShown: 0, spots: 0, minPx: 1e9, floor: 0, bad: [], fitBad: [], lens: [], resets: 0, aspect: 0 };
  G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset();
  const fits = G.palFits(), rooms = G.palPlan().rooms;
  o.n = rooms.length;
  for (const r of rooms) {
    // The core wakes the 兵家 apex on entry (BP03): the palace camera hands over to the hunt there (checked below), so it has no palace sample.
    if (r.type === 'core') { G.reset(); G.teleport(r.cx, r.cz); G.step(2); o.core = G.palace().phase; G.reset(); continue; }
    const fit = fits.find((f) => f.id === r.id).fit, m = 1.5;
    if (fit) o.fitN++;
    const spots = [[r.cx, r.cz], [r.x0 + m, r.z0 + m], [r.x1 - m, r.z0 + m], [r.x0 + m, r.z1 - m], [r.x1 - m, r.z1 - m]];
    G.reset();
    for (const [x, z] of spots) {
      G.teleport(x, z); G.step(90);
      if (G.palace().phase !== 'palace') { o.resets++; G.reset(); G.teleport(x, z); G.step(90); }
      const c = G.palCam(); o.floor = c.floor; o.aspect = c.aspect;
      if (c.room !== r.id) continue;
      o.spots++; o.minPx = Math.min(o.minPx, c.px);
      if (c.px < c.floor - 0.5 && o.bad.length < 6) o.bad.push([r.id, x, z, +c.px.toFixed(1)]);
      if ((Math.abs(c.fov - 50) > 1e-9 || Math.abs(c.pitch - 40) > 1e-6) && o.lens.length < 4) o.lens.push([r.id, c.fov, c.pitch]);
      if (fit && x === r.cx && z === r.cz) { if (c.allIn) o.fitShown++; else if (o.fitBad.length < 6) o.fitBad.push(r.id); }
    }
  }
  G.setLayout('proto'); G.setMode('rumble'); G.reset();
  return o;
}

export async function cam10Checks(g, check, browser, URL0) {
  // 1200-1201 Four screen sizes (phone portrait and landscape with touch, laptop, ultrawide): the player at least the floor everywhere in every
  // room of the full plan, lens and tilt unchanged; rooms that fit whole are shown whole (at least one room fits on the laptop and ultrawide).
  const sizes = [['phoneP', 390, 844, true], ['phoneL', 844, 390, true], ['laptop', 1366, 768, false], ['ultrawide', 2560, 1080, false]], S = {};
  for (const [k, w, h, touch] of sizes) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: touch, hasTouch: touch });
    const pg = await ctx.newPage(), errs = [];
    pg.on('pageerror', (e) => errs.push(String(e)));
    await pg.goto(URL0); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 60000 });
    S[k] = await pg.evaluate(sizeProbe); S[k].errs = errs.slice(0, 2);
    await ctx.close();
  }
  const sum = (k) => { const o = S[k]; return `${k}: core ${o.core} rooms ${o.n} spots ${o.spots} minPx ${o.minPx.toFixed(1)} floor ${o.floor.toFixed(1)} fit ${o.fitN} shown ${o.fitShown} bad ${JSON.stringify(o.bad)} fitBad ${JSON.stringify(o.fitBad)} lens ${JSON.stringify(o.lens)} resets ${o.resets} errs ${o.errs.join('|')}`; };
  const okSize = (k) => S[k].spots >= (S[k].n - 1) * 4 && S[k].bad.length === 0 && S[k].lens.length === 0 && S[k].errs.length === 0 && S[k].core === 'wake';
  check('1200 palace camera at 4 sizes: the player is at least the floor (120 px at 1080p; phones /phone) in every room of the full plan (core: hands over to the apex), lens 50 and tilt 40 unchanged',
    sizes.every(([k]) => okSize(k)), sizes.map(([k]) => sum(k)).join(' || '));
  // 1201 Rooms that fit whole above the floor are shown whole. At the owner's 120 px floor no room of the full plan fits at any of the 4 sizes (the
  // far wall would show the player under the floor), so every room is revealed as you walk (counts in the detail). The whole-room path is proven
  // with a lower floor (36 px, a check fixture, restored after): rooms that fit are shown whole (every corner on screen) with the player at least
  // that floor at the centre and 1.5 m inside each corner; at least one room fits.
  const fitFx = await g(() => {
    const G = __game, C = G.config.PAL_CAM, keep = C.minPx, o = { fitN: 0, shown: 0, bad: [], low: [] };
    C.minPx = 36;
    G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset();
    const fits = G.palFits();
    for (const r of G.palPlan().rooms) {
      if (r.type === 'core' || !fits.find((f) => f.id === r.id).fit) continue;
      o.fitN++; G.reset();
      for (const [x, z] of [[r.cx, r.cz], [r.x0 + 1.5, r.z0 + 1.5], [r.x1 - 1.5, r.z0 + 1.5], [r.x0 + 1.5, r.z1 - 1.5], [r.x1 - 1.5, r.z1 - 1.5]]) {
        // BP10M (24 Nov): the camera's own move is capped per step, so after a test teleport across a fit room it takes more steps to settle;
        // wait until it stops (a condition, at most 300 more steps). The assertions are unchanged.
        G.teleport(x, z); G.step(90);
        for (let k = 0, q = G.palCam(), m = 1; k < 300 && m > 0.01; k++) { G.step(1); const q2 = G.palCam(); m = Math.hypot(q2.camX - q.camX, q2.camY - q.camY, q2.camZ - q.camZ); q = q2; }
        const c = G.palCam();
        if (c.room !== r.id) continue;
        if (!c.allIn && o.bad.length < 5) o.bad.push([r.id, x, z]);
        if (c.px < 36 - 0.5 && o.low.length < 5) o.low.push([r.id, x, z, +c.px.toFixed(1)]);
        if (x === r.cx && z === r.cz && c.allIn) o.shown++;
      }
    }
    C.minPx = keep; G.palFits(); G.setLayout('proto'); G.setMode('rumble'); G.reset();
    o.restored = G.config.PAL_CAM.minPx === keep;
    return o;
  });
  check('1201 rooms that fit whole are shown whole: none fit at the 120 px floor (4 sizes, in the detail); with a 36 px fixture floor every room that fits is whole on screen, player >= floor, >= 1 fits',
    sizes.every(([k]) => S[k].fitShown === S[k].fitN && S[k].fitBad.length === 0) && fitFx.fitN >= 1 && fitFx.shown === fitFx.fitN && fitFx.bad.length === 0 && fitFx.low.length === 0 && fitFx.restored,
    sizes.map(([k]) => `${k} fit@floor ${S[k].fitN} shown ${S[k].fitShown}`).join(' | ') + ' || fixture ' + JSON.stringify(fitFx));

  // 1202 Big room revealed as you walk (laptop): in the largest room that does not fit, walking from its centre toward a wall moves the camera
  // smoothly (no step over 0.5 m), keeps the player above the floor and on screen, and leans ahead of him along his walking direction (> 0.5 m,
  // against the open-space lean back to the centre); Royal Rumble camera unchanged.
  const walk = await g(() => {
    const G = __game, o = { steps: 0, maxStep: 0, minPx: 1e9, off: 0, ahead: [], lens: 0 };
    G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset();
    const fits = G.palFits(), rooms = G.palPlan().rooms;
    let big = null;
    for (const r of rooms) { const f = fits.find((q) => q.id === r.id); if (!f.fit && (!big || (r.x1 - r.x0) * (r.z1 - r.z0) > (big.x1 - big.x0) * (big.z1 - big.z0))) big = r; }
    o.room = big ? big.id : ''; if (!big) return o;
    const along = big.x1 - big.x0 >= big.z1 - big.z0, dx = along ? 1 : 0, dz = along ? 0 : 1;
    // From the centre toward a far wall: the open-space lean points back to the centre, so a forward lean proves the walking-direction lead.
    G.teleport(big.cx, big.cz); G.step(90);
    let c = G.palCam(), lx = c.camX, ly = c.camY, lz = c.camZ;
    o.floor = c.floor; G.setMove(dx, dz);
    for (let i = 0; i < 300; i++) {
      G.step(1); c = G.palCam(); const p = G.palace();
      if (c.room !== big.id) break;
      o.steps++; o.maxStep = Math.max(o.maxStep, Math.hypot(c.camX - lx, c.camY - ly, c.camZ - lz)); lx = c.camX; ly = c.camY; lz = c.camZ;
      o.minPx = Math.min(o.minPx, c.px); if (Math.abs(c.pnx) > 0.95 || Math.abs(c.pny) > 0.95) o.off++;
      if (Math.abs(c.fov - 50) > 1e-9 || Math.abs(c.pitch - 40) > 1e-6) o.lens++;
      if (i === 60 || i === 75) o.ahead.push(+((c.wx - p.x) * dx + (c.wz - p.z) * dz).toFixed(2));
    }
    G.clearMove();
    G.setMode('rumble'); G.reset(); G.step(2); o.rumbleK = G.palace().camK;
    G.setLayout('proto');
    return o;
  });
  check('1202 big room revealed as you walk: smooth follow (no camera step over 0.5 m), player above the floor, framing leans ahead (> 0.5 m), lens fixed; Rumble camK 1',
    walk.room !== '' && walk.steps >= 60 && walk.maxStep <= 0.5 && walk.minPx >= walk.floor - 0.5 && walk.off === 0 && walk.ahead.length === 2 && walk.ahead.every((a) => a > 0.5) && walk.lens === 0 && walk.rumbleK === 1,
    JSON.stringify(walk));

  // 1203 Room change pans, never cuts: walking from the hall through its door into the court (box plan), no camera step over 0.5 m.
  const door = await g(() => {
    const G = __game, o = { steps: 0, maxStep: 0, rooms: [] };
    G.setSeed(12345); G.setMode('palace'); G.reset();
    const p0 = G.palace(), D = p0.doors.find((d) => (d.a === 'hall' && d.b === 'court') || (d.a === 'court' && d.b === 'hall'));
    G.teleport(D.x, D.z + 4); G.step(90);
    let c = G.palCam(), lx = c.camX, ly = c.camY, lz = c.camZ;
    G.setMove(0, -1);
    for (let i = 0; i < 150; i++) {
      G.step(1); c = G.palCam(); o.steps++;
      if (o.rooms[o.rooms.length - 1] !== c.room) o.rooms.push(c.room);
      o.maxStep = Math.max(o.maxStep, Math.hypot(c.camX - lx, c.camY - ly, c.camZ - lz)); lx = c.camX; ly = c.camY; lz = c.camZ;
    }
    G.clearMove();
    // Integration 24 Nov (lead): the same walk with 8 rivals, so ticket 03 spawns the court's real 皇家 squad as its door opens; the camera still
    // pans (no step over 0.5 m) and closes on the squad once a guard is within attack distance (b reaches 1).
    G.setSeed(12345); G.setBots(8); G.reset(); const n = G.palSim().recs.length; for (let i = 0; i < n; i++) G.palSimSet(i, null);
    G.teleport(D.x, D.z + 4); G.step(90); G.setHp(1e9);
    c = G.palCam(); lx = c.camX; ly = c.camY; lz = c.camZ; o.sq = { maxStep: 0, guards: 0, closeB: 0, rooms: [] };
    G.setMove(0, -1);
    for (let i = 0; i < 150; i++) {
      G.step(1); G.setHp(1e9); c = G.palCam();
      if (o.sq.rooms[o.sq.rooms.length - 1] !== c.room) o.sq.rooms.push(c.room);
      o.sq.maxStep = Math.max(o.sq.maxStep, Math.hypot(c.camX - lx, c.camY - ly, c.camZ - lz)); lx = c.camX; ly = c.camY; lz = c.camZ;
    }
    G.clearMove(); o.sq.guards = G.guards().list.filter((u) => u.alive && u.faction === 'huangjia').length; o.sq.court = G.palSim().guardLeft[G.palace().rooms.findIndex((r) => r.id === 'court')];
    for (let i = 0; i < 240 && o.sq.closeB < 1; i++) { G.step(1); G.setHp(1e9); o.sq.closeB = Math.max(o.sq.closeB, G.palCam().b); }
    G.setBots(0); G.setMode('rumble'); G.reset();
    return o;
  });
  check('1203 room change pans (hall -> court through the door): no camera step over 0.5 m; with 03\'s real court squad too, and it closes on the squad',
    door.rooms.join(',') === 'hall,court' && door.maxStep <= 0.5 && door.sq.rooms.join(',') === 'hall,court' && door.sq.maxStep <= 0.5 && door.sq.guards > 0 && door.sq.court === 0 && door.sq.closeB >= 1, JSON.stringify(door));

  // 1204 Close at attack distance, for each enemy kind (rival suit, 皇家 guard, 反贼, woken giant): an enemy in sight within the kit's attack distance
  // eases the camera to close (b 1, camera at the close distance from the player) within 0.6 s; it holds for backS after the enemy leaves, then
  // eases back to wide; an enemy beyond attack distance or a lurking 死士 never closes it; lens and tilt unchanged throughout.
  const close = await g(() => {
    const G = __game, C = G.config.PAL_CAM, o = { kinds: {}, lens: 0 };
    const lens = () => { const c = G.palCam(); if (Math.abs(c.fov - 50) > 1e-9 || Math.abs(c.pitch - 40) > 1e-6) o.lens++; return c; };
    const run = (k, place, away) => {
      G.setSeed(12345); G.setMode('palace'); G.pieces2(true, k === 'giant'); G.reset(); G.step(10);
      const r = { b0: lens().b };
      const at = place(); G.step(36); let c = lens(); r.b1 = c.b; r.d = +(c.pd - c.close).toFixed(4); r.atk = c.atk; r.at = at;
      away(); G.step(60); r.hold = lens().b; G.step(60); r.back = lens().b;
      o.kinds[k] = r;
      return r;
    };
    const P0 = () => G.palace();
    run('rival', () => { const p = P0(); G.palPlaceBot(0, p.x, p.z - 6); return 6; }, () => { const p = P0(), R = p.rooms.find((q) => q.id === 'court'); G.palPlaceBot(0, R.cx, R.cz); });
    const unit = (f, hid) => () => { const p = P0(); G.guardSet(0, { alive: true, hid, faction: f, x: p.x + 6, z: p.z, y: 0 }); return 6; };
    run('guard', unit('huangjia', false), () => G.guardSet(0, { alive: false }));
    run('rebel', unit('fanzei', false), () => G.guardSet(0, { alive: false }));
    run('giant', () => {
      G.giantWake(); G.step(Math.ceil(G.config.PIECES2.giant.wakeS * 60) + 2);
      const s = G.pieces2State(), gi = s.giants.find((q) => q.st >= 2), br = P0().rooms.find((q) => q.id === gi.room), sx = Math.sign(br.cx - gi.x) || 1;
      G.teleport(gi.x + 6 * sx, gi.z); return [gi.room, gi.st];
    }, () => { const p = P0(), R = p.rooms.find((q) => q.id === 'hall'); G.teleport(R.cx, R.cz); });
    // Negatives: a rival 3 m beyond the attack distance (+ pad) in the court (40 m wide), and a lurking 死士 at 6 m (fresh run each).
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true); G.reset(); G.step(10);
    const ct = P0().rooms.find((q) => q.id === 'court'), far = lens().atk + C.pad + 3;
    G.teleport(ct.x0 + 2, ct.cz); G.step(10); G.palPlaceBot(0, ct.x0 + 2 + far, ct.cz); G.step(36); o.far = lens().b; o.farM = far;
    G.reset(); G.step(10); const p = P0();
    G.guardSet(0, { alive: true, hid: true, faction: 'fanzei', x: p.x + 6, z: p.z, y: 0 }); G.step(36); o.lurk = lens().b;
    G.guardSet(0, { alive: false }); G.setMode('rumble'); G.reset();
    return o;
  });
  const kOk = (r) => r && r.b0 === 0 && r.b1 === 1 && Math.abs(r.d) < 0.01 && r.hold === 1 && r.back === 0;
  check('1204 close at attack distance for rival, guard, rebel and woken giant (b 1 within 0.6 s at the close distance; held backS; back to wide); not beyond reach, not a lurking 死士',
    ['rival', 'guard', 'rebel', 'giant'].every((k) => kOk(close.kinds[k])) && close.far === 0 && close.lurk === 0 && close.lens === 0, JSON.stringify(close));

  // 1205 Z override: wide holds wide with an enemy in reach, close holds close with none, auto follows the enemy rule again.
  const zo = await g(() => {
    const G = __game, o = {}, key = () => dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyZ' }));
    G.setSeed(12345); G.setMode('palace'); G.reset(); G.step(10);
    const p = G.palace(); G.palPlaceBot(0, p.x, p.z - 6);
    key(); G.step(40); o.wide = { man: G.palace().man, b: G.palCam().b };
    key(); G.palPlaceBot(0, p.x - 500, p.z); G.step(40); o.close = { man: G.palace().man, b: G.palCam().b };
    key(); G.step(150); o.auto = { man: G.palace().man, b: G.palCam().b };
    G.setMode('rumble'); G.reset();
    return o;
  });
  check('1205 Z override: wide stays wide with an enemy in reach, close stays close with none, auto returns to the enemy rule',
    zo.wide.man === 1 && zo.wide.b === 0 && zo.close.man === 2 && zo.close.b === 1 && zo.auto.man === 0 && zo.auto.b === 0, JSON.stringify(zo));

  // 1206 Minimap shows the room layout: centred on the current room and enlarged (fill), its pieces as icons (count = its lions, 华表, 鼎, mercury,
  // smoke, clocks, whole vats and dormant giants); the static layer is not redrawn on frames without a change, and is redrawn once on a room
  // change, a warned room, a fallen room and a woken giant.
  const mm = await g(() => {
    const G = __game, C = G.config.PAL_MINI, o = { rooms: {} };
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(2);
    const want = (id) => {
      const q = G.pieces(), s = G.pieces2State();
      return q.haz.filter((h) => h.room === id).length + q.merc.filter((m) => m.room === id).length + q.smoke.filter((c) => c.room === id).length + q.ding.filter((a) => a.room === id).length
        + s.clocks.filter((c) => c.room === id).length + s.vats.filter((v) => v.room === id && v.st < 2).length + s.giants.filter((gi) => gi.room === id && gi.st === 0).length;
    };
    const look = () => {
      const m = G.palMiniState(), p = G.palace(), r = p.rooms.find((q) => q.id === m.cur), b = G.palPlan().bounds;
      const sc0 = Math.min((m.W - C.pad * 2) / (b[1] - b[0]), (m.H - C.pad * 2) / (b[3] - b[2])), rs = C.fill * Math.min(m.W / (r.x1 - r.x0), m.H / (r.z1 - r.z0));
      const cx = m.ox + (r.cx - b[0]) * m.scale, cz = m.oy + (r.cz - b[2]) * m.scale, big = rs > sc0;
      return { cur: m.cur, icons: m.icons, want: want(m.cur), scaleOk: Math.abs(m.scale - Math.max(sc0, rs)) < 1e-9, centred: !big || (Math.abs(cx - m.W / 2) < 1e-6 && Math.abs(cz - m.H / 2) < 1e-6) };
    };
    G.palMiniTick(1); const d0 = G.palMiniState().draws; G.palMiniTick(120); o.idle = G.palMiniState().draws - d0;
    o.rooms.hall = look();
    const R = Object.fromEntries(G.palace().rooms.map((r) => [r.id, r]));
    let d = G.palMiniState().draws; G.teleport(R.court.cx, R.court.cz); G.step(2); G.palMiniTick(30); o.roomChange = G.palMiniState().draws - d; o.rooms.court = look();
    d = G.palMiniState().draws; G.palTestRoomState('garden', true, false); G.palMiniTick(30); o.warned = G.palMiniState().draws - d;
    d = G.palMiniState().draws; G.palTestRoomState('garden', false, true); G.palMiniTick(30); o.fallen = G.palMiniState().draws - d;
    G.palTestRoomState('garden', false, false);
    G.teleport(R.bridge.cx, R.bridge.cz); G.step(2); G.palMiniTick(1); o.rooms.bridge = look();
    d = G.palMiniState().draws; G.giantWake(); G.palMiniTick(30); o.giant = G.palMiniState().draws - d; o.bridgeAfter = look();
    G.setMode('rumble'); G.reset();
    return o;
  });
  const rOk = (r) => r && r.icons === r.want && r.scaleOk && r.centred;
  check('1206 minimap room layout: centred and enlarged on the current room, its pieces as icons; no redraw on idle frames; one redraw per room change, warned, fallen, giant woken',
    mm.idle === 0 && mm.roomChange === 1 && mm.warned === 1 && mm.fallen === 1 && mm.giant === 1 && ['hall', 'court', 'bridge'].every((k) => rOk(mm.rooms[k])) && rOk(mm.bridgeAfter)
    && mm.rooms.bridge.want > mm.bridgeAfter.want - 1 && mm.rooms.court.icons > 0, JSON.stringify(mm));

  // 1207 Budget unchanged: every room of the full plan, wide and close, under 500 calls and 0.5M triangles, programs and geometries flat.
  const bud = await g(() => {
    const G = __game, o = { calls: 0, tris: 0, prog: [], geo: [] }, key = () => dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyZ' }));
    G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset(); G.step(2);
    const b0 = G.render(true); o.base = { programs: b0.programs, geoms: b0.geoms };
    for (const r of G.palPlan().rooms) {
      G.reset(); G.teleport(r.cx, r.cz); G.step(30);
      // Geometries are compared wide against close in the same room (a room's first draw uploads its own geometry, a camera change adds none).
      let gw = 0;
      for (let m = 0; m < 2; m++) {
        if (m === 1) { key(); key(); G.step(30); }
        const d = G.render(true); o.calls = Math.max(o.calls, d.calls); o.tris = Math.max(o.tris, d.tris);
        if (d.programs !== b0.programs && o.prog.length < 3) o.prog.push([r.id, d.programs]);
        if (m === 0) gw = d.geoms; else if (d.geoms !== gw && o.geo.length < 3) o.geo.push([r.id, gw, d.geoms]);
        if (m === 1) key();
      }
    }
    G.setLayout('proto'); G.setMode('rumble'); G.reset();
    return o;
  });
  check('1207 budget with the room-fit camera: every room of the full plan wide and close under 500 calls / 0.5M tris, programs flat, close adds no geometry over wide',
    bud.calls > 0 && bud.calls < 500 && bud.tris < 500000 && bud.prog.length === 0 && bud.geo.length === 0, JSON.stringify(bud));

  // 1208 New run in the same page: the camera snaps to the start room's wide framing (b 0, no pan left over), Z back to auto.
  const nr = await g(() => {
    const G = __game, o = {}, key = () => dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyZ' }));
    G.setSeed(12345); G.setMode('palace'); G.reset(); const a = G.palCam(); G.step(2);
    const p = G.palace(); G.palPlaceBot(0, p.x, p.z - 6); G.step(40); key(); key(); G.step(5); G.palPlaceBot(0, p.x - 500, p.z);
    G.reset(); const c = G.palCam();
    o.same = Math.abs(c.camX - a.camX) < 1e-9 && Math.abs(c.camY - a.camY) < 1e-9 && Math.abs(c.camZ - a.camZ) < 1e-9; o.b = c.b; o.hold = c.hold; o.man = G.palace().man;
    G.setMode('rumble'); G.reset();
    return o;
  });
  check('1208 palace new run: camera snaps to the start framing (same position as the first run), wide, no hold, Z auto', nr.same && nr.b === 0 && nr.hold === 0 && nr.man === 0, JSON.stringify(nr));
}
