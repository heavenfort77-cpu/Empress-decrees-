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
    await pg.goto(URL0, { timeout: 120000 }); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 120000 });
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
    // pans (no step over 0.5 m) and frames the squad once a guard is within the fight radius (dynamic framing, owner 19:33: b reaches 0.99).
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
    for (let i = 0; i < 240 && o.sq.closeB < 0.99; i++) { G.step(1); G.setHp(1e9); o.sq.closeB = Math.max(o.sq.closeB, G.palCam().b); }
    G.setBots(0); G.setMode('rumble'); G.reset();
    return o;
  });
  check('1203 room change pans (hall -> court through the door): no camera step over 0.5 m; with 03\'s real court squad too, and it closes on the squad',
    door.rooms.join(',') === 'hall,court' && door.maxStep <= 0.5 && door.sq.rooms.join(',') === 'hall,court' && door.sq.maxStep <= 0.5 && door.sq.guards > 0 && door.sq.court === 0 && door.sq.closeB >= 0.99, JSON.stringify(door));

  // 1204 Fight framing (dynamic combat framing, owner 24 Nov 19:33), for each enemy kind (rival suit, 皇家 guard, 反贼, woken giant): an enemy in
  // sight within enterR blends the camera to the fight framing (b >= 0.9 within 0.6 s, >= 0.99 by 1.5 s; spring); the look point is 70/30
  // between the player and the foe; the distance is between the close and the wide one; it holds backS after the enemy leaves exitR, then
  // returns to wide; an enemy between enterR and exitR never starts it, nor a lurking 死士; lens and tilt unchanged throughout.
  const close = await g(() => {
    const G = __game, C = G.config.PAL_CAM, F = G.config.PAL_FRAME, o = { kinds: {}, lens: 0 };
    const lens = () => { const c = G.palCam(); if (Math.abs(c.fov - 50) > 1e-9 || Math.abs(c.pitch - 40) > 1e-6) o.lens++; return c; };
    const run = (k, place, away) => {
      G.setSeed(12345); G.setMode('palace'); G.pieces2(true, k === 'giant'); G.reset(); G.step(10);
      const r = { b0: lens().b };
      const at = place(); G.step(36); let c = lens(); r.b06 = +c.b.toFixed(3); G.step(54); c = lens(); r.b15 = +c.b.toFixed(3);
      const p = G.palace(); r.foc = c.fn ? 1 : 0; r.dIn = c.ftd >= c.close - 1e-6 && c.ftd <= Math.max(c.close, c.wd) + 1e-6; r.at = at;
      away(); G.step(60); r.hold = +lens().b.toFixed(3); G.step(120); r.back = +lens().b.toFixed(3);
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
    // Look point: one rival 6 m north of the player, settled: 30% of the way to it (the owner's 70/30 spec, a fixed number here, not read from
    // CONFIG: mutation cam11-mut 45393123516 set focus to 0 and a check reading CONFIG moved with it).
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true); G.reset(); G.step(10);
    { const p = P0(), bx = p.x, bz = p.z - 6; G.palPlaceBot(0, bx, bz); G.step(120); const c = lens(), q = P0(); o.focus = { fn: c.fn, dx: +(c.ftx - (q.x + (bx - q.x) * 0.3)).toFixed(3), dz: +(c.ftz - (q.z + (bz - q.z) * 0.3)).toFixed(3) }; }
    // Negatives: a rival between enterR and exitR in the court (40 m wide), and a lurking 死士 at 6 m (fresh run each).
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true); G.reset(); G.step(10);
    const ct = P0().rooms.find((q) => q.id === 'court'), far = (F.enterR + F.exitR) / 2;
    G.teleport(ct.x0 + 2, ct.cz); G.step(10); G.palPlaceBot(0, ct.x0 + 2 + far, ct.cz); G.step(90); o.far = +lens().b.toFixed(3); o.farM = far;
    G.reset(); G.step(10); const p = P0();
    G.guardSet(0, { alive: true, hid: true, faction: 'fanzei', x: p.x + 6, z: p.z, y: 0 }); G.step(90); o.lurk = +lens().b.toFixed(3);
    G.guardSet(0, { alive: false }); G.setMode('rumble'); G.reset();
    return o;
  });
  const kOk = (r) => r && r.b0 === 0 && r.b06 >= 0.9 && r.b15 >= 0.99 && r.foc === 1 && r.dIn && r.hold >= 0.99 && r.back <= 0.01;
  check('1204 fight framing for rival, guard, rebel and woken giant (enterR: b >= 0.9 in 0.6 s, >= 0.99 by 1.5 s; look point 30% to the foe; distance close..wide; held backS; back to wide); not between enterR and exitR, not a lurking 死士',
    ['rival', 'guard', 'rebel', 'giant'].every((k) => kOk(close.kinds[k])) && close.focus.fn === 1 && Math.abs(close.focus.dx) < 0.05 && Math.abs(close.focus.dz) < 0.05 && close.far <= 0.01 && close.lurk <= 0.01 && close.lens === 0, JSON.stringify(close));

  // 1205 Z override: wide holds wide with an enemy in reach, close holds close with none, auto follows the enemy rule again.
  const zo = await g(() => {
    const G = __game, o = {}, key = () => dispatchEvent(new KeyboardEvent('keydown', { code: 'KeyZ' }));
    G.setSeed(12345); G.setMode('palace'); G.reset(); G.step(10);
    const p = G.palace(); G.palPlaceBot(0, p.x, p.z - 6);
    key(); G.step(90); o.wide = { man: G.palace().man, b: G.palCam().b };
    key(); G.palPlaceBot(0, p.x - 500, p.z); G.step(90); o.close = { man: G.palace().man, b: G.palCam().b };
    key(); G.step(240); o.auto = { man: G.palace().man, b: G.palCam().b };
    G.setMode('rumble'); G.reset();
    return o;
  });
  check('1205 Z override: wide stays wide with an enemy in reach, close stays close with none, auto returns to the enemy rule',
    zo.wide.man === 1 && zo.wide.b <= 0.01 && zo.close.man === 2 && zo.close.b >= 0.99 && zo.auto.man === 0 && zo.auto.b <= 0.01, JSON.stringify(zo));

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

  // 1209-1213 Dynamic combat framing (owner 24 Nov 19:33; cause of the 19:31 phone shot: the explore look-ahead was in metres, up to 5 m, while a
  // phone in portrait shows about 2.4 m either side, so the player left the screen: NDC x -1.57 in the repro).
  // 1209 Explore safe zone at 4 screen sizes: the player on autopilot through the full palace for 40 s of game time, sampled every 0.25 s:
  // while exploring (b <= 0.05) he stays within 0.55 of the half-screen (safeExplore 0.45 + spring margin), in a fight (b >= 0.95) within 0.85
  // (safeFight 0.7 + margin), and never off screen.
  const Z = {};
  for (const [k, w, h, touch] of sizes) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: touch, hasTouch: touch });
    const pg = await ctx.newPage(), errs = [];
    pg.on('pageerror', (e) => errs.push(String(e).slice(0, 200)));
    await pg.goto(URL0, { timeout: 90000 }); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
    Z[k] = await pg.evaluate(() => {
      const G = __game, o = { ex: 0, fi: 0, exN: 0, fiN: 0, all: 0, n: 0, worst: null };
      G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset(); G.setHp(1e9); G.autoPlayer(true);
      for (let i = 0; i < 160; i++) {
        G.step(15); G.setHp(1e9);
        if (G.palace().phase !== 'palace') continue;
        const c = G.palCam(), m = Math.max(Math.abs(c.pnx), Math.abs(c.pny)); o.n++;
        if (c.b <= 0.05) { o.exN++; o.ex = Math.max(o.ex, m); } else if (c.b >= 0.95) { o.fiN++; o.fi = Math.max(o.fi, m); }
        if (m > o.all) { o.all = m; o.worst = [i, c.room, +c.b.toFixed(2), +c.pnx.toFixed(2), +c.pny.toFixed(2)]; }
      }
      G.autoPlayer(false); G.setLayout('proto'); G.setMode('rumble'); G.reset();
      o.ex = +o.ex.toFixed(3); o.fi = +o.fi.toFixed(3); o.all = +o.all.toFixed(3);
      return o;
    });
    Z[k].errs = errs.slice(0, 2);
    await ctx.close();
  }
  const zOk = (o) => o.exN >= 20 && o.ex <= 0.55 && o.fi <= 0.85 && o.all <= 0.95 && o.errs.length === 0;
  check('1209 explore safe zone at 4 sizes (autopilot 40 s, full palace): exploring <= 0.55 of the half-screen, fighting <= 0.85, never off screen',
    sizes.every(([k]) => zOk(Z[k])), JSON.stringify(Z));

  // 1210 Hysteresis: a rival between enterR and exitR does not start a fight; at 6 m it does; back between the radii it holds (3 s); stepping
  // across enterR back and forth every 0.25 s for 4 s switches the state at most once; beyond exitR the fight ends after backS (not before).
  const hy = await g(() => {
    const G = __game, F = G.config.PAL_FRAME, C = G.config.PAL_CAM, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true); G.reset(); G.step(10);
    const ct = G.palace().rooms.find((q) => q.id === 'court'), x0 = ct.x0 + 2, z0 = ct.cz;
    G.teleport(x0, z0); G.step(10);
    const put = (d) => G.palPlaceBot(0, x0 + d, z0), st = () => G.palCam();
    put((F.enterR + F.exitR) / 2); G.step(30); o.mid0 = st().fight;
    put(6); G.step(30); o.in = st().fight; const s0 = st().switches;
    put((F.enterR + F.exitR) / 2); G.step(180); o.held = st().fight;
    for (let i = 0; i < 16; i++) { put(i % 2 ? F.enterR - 0.5 : F.enterR + 0.5); G.step(15); }
    o.flips = st().switches - s0;
    put(F.exitR + 6); G.step(Math.round(C.backS * 60) - 20); o.before = st().fight; G.step(40); o.after = st().fight;
    G.setMode('rumble'); G.reset();
    return o;
  });
  check('1210 fight framing hysteresis: no start between enterR and exitR, start at 6 m, holds between the radii, <= 1 switch while crossing enterR back and forth, ends backS after leaving exitR',
    hy.mid0 === false && hy.in === true && hy.held === true && hy.flips <= 1 && hy.before === true && hy.after === false, JSON.stringify(hy));

  // 1211 Zoom-in capped by spread: three foes spread around the player (7 m west, 7 m east, 8 m north): after settling, the fight distance is
  // beyond the close one and no farther than the wide one, and the player and all three are inside safeFight (+0.05) on the real screen.
  const sp = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true); G.reset(); G.step(10);
    const ct = G.palace().rooms.find((q) => q.id === 'court'), x = ct.cx, z = ct.cz;
    G.teleport(x, z); G.step(10);
    G.palPlaceBot(0, x - 7, z); G.guardSet(0, { alive: true, hid: false, faction: 'huangjia', x: x + 7, z, y: 0 }); G.guardSet(1, { alive: true, hid: false, faction: 'fanzei', x, z: z - 8, y: 0 });
    G.step(150);
    const c = G.palCam(); o.fn = c.fn; o.ftd = +c.ftd.toFixed(2); o.close = +c.close.toFixed(2); o.wd = +c.wd.toFixed(2); o.b = +c.b.toFixed(3);
    o.ndc = G.palFoeNdc();
    G.guardSet(0, { alive: false }); G.guardSet(1, { alive: false }); G.setMode('rumble'); G.reset();
    return o;
  });
  const spMax = sp.ndc ? Math.max(...sp.ndc.map((q) => Math.max(Math.abs(q[0]), Math.abs(q[1])))) : 9;
  check('1211 zoom-in capped by the foes\' spread: 3 foes framed, distance > close and <= wide, player and foes inside safeFight + 0.05',
    sp.fn === 3 && sp.b >= 0.99 && sp.ftd > sp.close && sp.ftd <= Math.max(sp.close, sp.wd) + 1e-6 && spMax <= 0.75, JSON.stringify(sp) + ' max ' + spMax.toFixed(3));

  // 1212 Edge markers: a guard 22 m east of the player in the forecourt (off screen) gets one marker on the right half pointing right; with the
  // guard on screen there is none; out of the palace (Royal Rumble) none.
  const mk = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setLayout('full'); G.setMode('palace'); G.reset(); G.step(10);
    const fc = G.palace().rooms.find((q) => q.id === 'fore'), x = fc.x0 + 4, z = fc.cz;
    G.teleport(x, z); G.step(30);
    G.guardSet(0, { alive: true, hid: false, faction: 'huangjia', x: x + 22, z, y: 0 }); G.step(2);
    let m = G.palMarkState(); o.off = { n: m.n, list: m.list, W: m.W };
    G.guardSet(0, { alive: true, hid: false, faction: 'huangjia', x: x + 1.5, z: z - 1.5, y: 0 }); G.step(2);
    m = G.palMarkState(); o.on = m.n;
    G.guardSet(0, { alive: false }); G.setLayout('proto'); G.setMode('rumble'); G.reset(); m = G.palMarkState(); o.rumble = m.n;
    return o;
  });
  const m0 = mk.off.list[0];
  check('1212 edge markers: off-screen foe -> one marker at the right edge pointing right; on-screen foe -> none; Royal Rumble -> none',
    mk.off.n === 1 && m0 && m0[0] > mk.off.W / 2 && Math.abs(m0[2] - Math.PI / 2) < 0.6 && mk.on === 0 && mk.rumble === 0, JSON.stringify(mk));

  // 1213 Text stacking at 4 sizes: her announcement (two long lines) and the door card shown together never overlap, and both stay on screen.
  const TX = {};
  for (const [k, w, h, touch] of sizes) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, isMobile: touch, hasTouch: touch });
    const pg = await ctx.newPage();
    await pg.goto(URL0, { timeout: 90000 }); await pg.waitForFunction(() => window.__ready === true, null, { timeout: 90000 });
    TX[k] = await pg.evaluate(() => {
      const b = document.getElementById('banner'), d = document.getElementById('door');
      b.querySelector('.voice').textContent = 'We have seen it.'; b.querySelector('.rule').textContent = 'Ming suit broke Zongheng suit in the Bridge over the black lake. The west wing falls in 5 s.';
      d.textContent = 'Courtyard\nLocked: break every enemy in this room.'; b.style.display = 'block'; d.style.display = 'block';
      const A = b.getBoundingClientRect(), B = d.getBoundingClientRect(), W = innerWidth, H = innerHeight;
      const overlap = !(A.bottom <= B.top || B.bottom <= A.top || A.right <= B.left || B.right <= A.left);
      const inside = (R) => R.left >= 0 && R.right <= W && R.top >= 0 && R.bottom <= H;
      return { overlap, a: [A.top, A.bottom].map(Math.round), b: [B.top, B.bottom].map(Math.round), inside: inside(A) && inside(B) };
    });
    await ctx.close();
  }
  check('1213 announcement and door card stacked at 4 sizes: no overlap, both on screen', sizes.every(([k]) => !TX[k].overlap && TX[k].inside), JSON.stringify(TX));
}
