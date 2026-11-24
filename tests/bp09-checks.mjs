// BP09 palace pieces II checks (1000-1006): 铜壶滴漏 water clocks, 门海 water vats, 十二金人 bronze giants (docs/BURNING-PALACE.md "Palace pieces").
// Called from tests/run.mjs with its page-evaluate helper g and its check(name, ok, detail).
export async function bp09Checks(g, check) {
  const tx = await g(() => __game.text);
  // 1000 Water clocks: one per wing, in that wing's room; the water level is the time left until that wing burns: the burning's own clock (each wing
  // named everyS after the last naming, so the steps add up to at most 4 fixed steps past 40/80/120/160 s), the seconds on the next-to-burn line;
  // the water mesh is written only when its level step changes.
  const c0 = await g(() => {
    const G = __game, o = { bad: [], hud: [], n: 0 };
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, false); G.reset();
    const R = Object.fromEntries(G.palace().rooms.map((r) => [r.id, r]));
    G.teleport(R.bridge.cx, R.bridge.cz); G.step(2);
    const s0 = G.pieces2State(); o.rooms = s0.clocks.map((c) => c.room + ':' + c.wing).join(','); o.start = s0.clocks.map((c) => c.step);
    const wings = ['outer', 'court', 'west', 'east'], steps = 48;
    for (let i = 0; i < 175 * 4 && G.palace().phase === 'palace'; i++) {
      G.step(15); o.n++;
      const s = G.pieces2State(), t = s.t, b = G.burnState();
      for (const c of s.clocks) {
        const k = wings.indexOf(c.wing), nominal = Math.max(0, 40 + 40 * k - t), full = 40 + 40 * k;
        // The game's clock: the next wing in nextAt - t; a later wing everyS per wing after the one before it (after the current naming while one burns).
        const game = k < b.i ? 0 : b.st === 0 ? (k === b.i ? Math.max(0, b.nextAt - t) : Math.max(0, b.nextAt - t) + (k - b.i) * 40) : k === b.i ? 0 : Math.max(0, b.warnAt + 40 - t) + (k - b.i - 1) * 40;
        if (Math.abs(c.eta - game) > 1e-6 || (c.eta > 0 && Math.abs(c.eta - nominal) > 4 / 60 + 1e-6) || Math.abs(c.level * c.full - c.eta) > 1e-6 || c.full !== full
          || Math.abs(c.scale - Math.max(0.001, Math.ceil(c.level * steps) / steps)) > 1e-9) {
          if (o.bad.length < 5) o.bad.push([c.wing, t, c.eta, game, nominal, c.level, c.scale]);
        }
        if (b.st === 0 && !b.waiting && b.i === k) { const m = /in (\d+) s/.exec(b.next); if (m && +m[1] !== Math.ceil(c.eta)) o.hud.push([c.wing, t, m[1], c.eta]); }
      }
    }
    o.writes = G.pieces2State().clocks.map((c) => c.writes);
    G.pieces2(true, true); G.setMode('rumble'); G.reset(); return o;
  });
  check('1000 water clocks: one per wing in its room; level = time left to that wing\'s burning (the burning\'s clock, 40/80/120/160 s within 4 steps), same seconds as the next-to-burn line; written only on a level-step change',
    c0.rooms === 'hall:outer,court:court,corridor:west,garden:east' && c0.start.every((v) => v === 48) && c0.bad.length === 0 && c0.hud.length === 0 && c0.n >= 600
    && c0.writes.every((w) => w >= 20 && w <= 50), JSON.stringify(c0));

  // 1001 A vat broken inside the burning wing: crack ring >= 0.4 s first, then the splash knocks the player back and holds that wing's fall douseS
  // (4 s) longer (her countdown follows); the fairness monitor stays clean through the whole burning.
  const v1 = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, false); G.reset();
    const R = Object.fromEntries(G.palace().rooms.map((r) => [r.id, r]));
    while (G.burnState().t < 40.1) G.step(1);
    const v = G.pieces2State().vats[0]; o.room = v.room;
    G.teleport(v.x + 1.6, v.z); G.step(1); G.vatAttack(0);
    let t1 = -1, t2 = -1, d1 = 0, ring = false;
    for (let i = 0; i < 60 * 6 && t2 < 0; i++) {
      G.step(1); const s = G.pieces2State(), q = s.vats[0], p = G.palace();
      if (q.st === 1 && t1 < 0) { t1 = s.t; ring = q.ring; d1 = Math.hypot(p.x - q.x, p.z - q.z); }
      if (q.st >= 2 && t2 < 0) t2 = s.t;
    }
    G.step(30); const p = G.palace(), q = G.pieces2State().vats[0];
    o.crack = +(t2 - t1).toFixed(3); o.ring = ring; o.push = +(Math.hypot(p.x - q.x, p.z - q.z) - d1).toFixed(2);
    o.vat = { st: q.st, solidOff: q.solidOff, body: q.body, flood: q.flood }; o.douses = G.pieces2State().douses;
    const rule = G.palace().rule; o.rule = rule;
    G.teleport(R.bridge.cx, R.bridge.cz);
    while (G.burnState().st !== 2 && G.burnState().t < 60) G.step(1);
    const b = G.burnState(), hall = b.rooms.find((r) => r.id === 'hall');
    o.fallGap = +(hall.fallAt - hall.warnAt).toFixed(3);
    for (let i = 0; i < 140 * 4 && G.palace().phase === 'palace'; i++) G.step(15);
    o.bad = G.burnState().bad; o.falls = G.burnState().falls;
    G.pieces2(true, true); G.setMode('rumble'); G.reset(); return o;
  });
  check('1001 vat in the burning wing: crack ring >= 0.4 s, splash pushes the player back, the wing falls warnS + douseS (9 s) after its warning; monitor clean',
    v1.room === 'hall' && v1.crack >= 0.4 && v1.ring && v1.push > 1 && v1.vat.st >= 2 && v1.vat.solidOff && !v1.vat.body && v1.douses === 1 && Math.abs(v1.fallGap - 9) < 0.05
    && v1.bad === 0 && v1.falls === 4, JSON.stringify(v1));

  // 1002 A vat outside the burning wing (the court's, broken while the outer hall burns): splash only (no douse, the burning clock unchanged); the flood shows floodS then goes; solid off, body gone;
  // a new run (twice) brings every vat back whole (hp, solid, body, no ring, no flood).
  const v2 = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, false); G.reset();
    while (G.burnState().t < 40.1) G.step(1);
    const v = G.pieces2State().vats[1]; o.room = v.room;
    G.teleport(v.x + 1.6, v.z); G.step(1); const warnAt = G.burnState().warnAt; o.st = G.burnState().st; G.vatAttack(1);
    let ts = -1, tg = -1;
    for (let i = 0; i < 60 * 12 && tg < 0; i++) { G.step(1); const s = G.pieces2State(), q = s.vats[1]; if (q.st === 2 && ts < 0) { ts = s.t; o.flood = q.flood; } if (q.st === 3 && tg < 0) { tg = s.t; o.floodAfter = q.flood; } }
    o.floodS = +(tg - ts).toFixed(3); o.warnAt = [warnAt, G.burnState().warnAt]; o.douses = G.pieces2State().douses;
    const q = G.pieces2State().vats[1]; o.after = { solidOff: q.solidOff, body: q.body, seen: q.seen, hp: q.hp };
    o.runs = [];
    for (let k = 0; k < 2; k++) { G.reset(); G.step(1); o.runs.push(G.pieces2State().vats.every((x) => x.st === 0 && x.hp === 30 && !x.solidOff && x.body && !x.ring && !x.flood)); }
    G.pieces2(true, true); G.setMode('rumble'); G.reset(); return o;
  });
  check('1002 vat outside the burning wing: no douse, burn clock unchanged; flood shows 3 s then goes; solid off, body gone; new run (twice) restores every vat',
    v2.room === 'court' && v2.st === 1 && v2.douses === 0 && v2.warnAt[0] === v2.warnAt[1] && v2.flood && !v2.floodAfter && Math.abs(v2.floodS - 3) < 0.05
    && v2.after.solidOff && !v2.after.body && !v2.after.seen && v2.after.hp === 0 && v2.runs.every((x) => x), JSON.stringify(v2));

  // 1003 Giants wake one per fall (nearest the core first), each glows and stands >= 0.4 s (wakeS 2) before it moves, her line once per wake when the
  // banner is free; at most cap (4) awake. The player kites between standing rooms (teleports away from the nearest awake giant).
  const gw = await g(() => {
    const G = __game, o = { wakesAt: [], wakeHold: [], firstHome: null };
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset();
    const P = G.palace(), R = Object.fromEntries(P.rooms.map((r) => [r.id, r]));
    const core = R.core, s0 = G.pieces2State();
    const order = s0.giants.slice().sort((a, b) => Math.hypot(a.hx - core.cx, a.hz - core.z1) - Math.hypot(b.hx - core.cx, b.hz - core.z1));
    o.firstWant = order[0].i;
    const since = {};
    let lastFalls = 0;
    for (let i = 0; i < 170 * 4 && G.palace().phase === 'palace'; i++) {
      const s = G.pieces2State(), b = G.burnState();
      let best = null, bd = -1;
      for (const r of b.rooms) {
        if (r.state !== 0 || r.warned || r.id === 'core') continue;
        const rr = R[r.id]; let md = 1e9;
        for (const gi of s.giants) if (gi.st >= 1 && gi.st <= 4) md = Math.min(md, Math.hypot(gi.x - rr.cx, gi.z - rr.cz));
        if (md > bd) { bd = md; best = rr; }
      }
      if (best) G.teleport(best.cx, best.cz);
      // Health topped up: this check is about the wakes, not the fights (1004 checks the hits).
      G.setHp(100); G.step(15);
      const s2 = G.pieces2State(), b2 = G.burnState();
      for (const gi of s2.giants) {
        if (gi.st === 1 && since[gi.i] === undefined) { since[gi.i] = s2.t; if (o.firstHome === null) o.firstHome = gi.i; }
        if (gi.st >= 2 && since[gi.i] !== undefined && since[gi.i] >= 0) { o.wakeHold.push(+(s2.t - since[gi.i]).toFixed(2)); since[gi.i] = -1; }
      }
      if (b2.falls !== lastFalls) { lastFalls = b2.falls; o.wakesAt.push([b2.falls, s2.wakes]); }
    }
    const s = G.pieces2State(); o.awake = s.awake; o.wakes = s.wakes; o.notes = s.notes; o.phase = G.palace().phase; o.pdead = G.state().dead;
    // Cap: wake more by hand until it refuses; then exactly cap are awake (some may have fallen with a burned room).
    let n = 0; while (n < 12 && G.giantWake()) n++;
    o.capAwake = G.pieces2State().awake; o.capLast = G.giantWake(); o.cap = s.cap;
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1003 giants: one woken per fall (nearest the core first), wake tell >= 0.4 s before moving, her line per wake; never more than cap awake',
    gw.wakesAt.length === 4 && gw.wakesAt.every((w, i) => w[0] === i + 1 && w[1] === i + 1) && gw.firstHome === gw.firstWant && gw.wakeHold.length >= 4
    && gw.wakeHold.every((h) => h >= 0.4) && gw.notes === 4 && gw.awake <= gw.cap && gw.capAwake === gw.cap && gw.capLast === false && gw.cap === 4 && gw.phase === 'palace', JSON.stringify(gw));

  // 1004 Giant moves: an awake giant routes through doors to the player's room (pushing shut doors open, which close again after it); its slam or
  // sweep shows its shape for the whole windup (>= 0.4 s) and hits only a suit still inside it; a giant's blow breaks a vat inside its shape.
  const gm = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset();
    const R = Object.fromEntries(G.palace().rooms.map((r) => [r.id, r]));
    // A: stand still next to a woken giant on the bridge: hit only after the full windup.
    G.giantWake(); const gi = G.pieces2State().giants.find((x) => x.st === 1);
    G.teleport(gi.x, gi.z + 2.4); const hp0 = G.state().hp;
    let tellSeen = false;
    for (let i = 0; i < 60 * 6 && G.pieces2State().giants[gi.i].hits === 0; i++) { G.step(1); const q = G.pieces2State().giants[gi.i]; if (q.ring || q.line) tellSeen = true; }
    const q = G.pieces2State().giants[gi.i];
    o.hit = { hits: q.hits, minTell: q.minTell, lost: +(hp0 - G.state().hp).toFixed(1), tellSeen };
    // B: dodge: when the next move's shape shows, step 12 m away; that move lands nothing.
    G.reset(); G.giantWake(); const g2 = G.pieces2State().giants.find((x) => x.st === 1);
    G.teleport(g2.x, g2.z + 2.4);
    let shown = false;
    for (let i = 0; i < 60 * 6 && !shown; i++) { G.step(1); const r = G.pieces2State().giants[g2.i]; if (r.ring || r.line) shown = true; }
    const hp1 = G.state().hp; G.teleport(g2.x + 12, R.bridge.cz); G.step(90);
    o.dodge = { shown, hits: G.pieces2State().giants[g2.i].hits, lost: +(hp1 - G.state().hp).toFixed(1) };
    // C: route: the player waits in the court beside its vat (the giant comes from the bridge through two doors) and never attacks.
    G.reset(); G.giantWake(); const g3 = G.pieces2State().giants.find((x) => x.st === 1);
    const v = G.pieces2State().vats[1];
    G.teleport(v.x + 1.8, v.z); G.step(1);
    const rooms = new Set(); let opened = false, vatBroke = false, tReach = -1;
    for (let i = 0; i < 40 * 4 && G.palace().phase === 'palace' && G.burnState().t < 44 && !(vatBroke && tReach > 0); i++) {
      G.step(15); const s = G.pieces2State(), r = s.giants[g3.i];
      rooms.add(r.room); if (r.room === 'court' && tReach < 0) tReach = s.t;
      if (G.palace().doors.some((d) => d.open && (d.a === 'bridge' || d.b === 'bridge' || d.a === 'corridor' || d.b === 'corridor') && Math.hypot(d.x - r.x, d.z - r.z) < 4)) opened = true;
      if (s.vats[1].st >= 1) vatBroke = true;
    }
    o.route = { rooms: [...rooms].join(','), opened, tReach, vatBroke, attackHeld: false, doorsShutAfter: null };
    G.teleport(R.court.cx, R.court.cz); G.step(240);
    o.route.doorsShutAfter = G.palace().doors.filter((d) => (d.a === 'corridor' && d.b === 'bridge') || (d.a === 'garden' && d.b === 'bridge')).every((d) => !d.open);
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1004 giant moves: routes through doors to the player\'s room (opens shut doors, they shut after); shape shown the whole windup (>= 0.4 s) and only a suit inside is hit; its blow breaks a vat',
    gm.hit.hits >= 1 && gm.hit.minTell >= 0.95 && gm.hit.lost > 0 && gm.hit.tellSeen && gm.dodge.shown && gm.dodge.hits === 0 && gm.dodge.lost === 0
    && gm.route.rooms.indexOf('court') >= 0 && gm.route.opened && gm.route.tReach > 0 && gm.route.vatBroke && gm.route.doorsShutAfter, JSON.stringify(gm));

  // 1005 Budget (tier medium): the bridge with 8 dormant and 4 awake giants, tells showing: under 500 calls / 0.5M tris; programs, geometries and
  // textures as at the start (warmed at load); instance matrices not written while no giant moves; Royal Rumble draws no piece (counts equal on/off).
  const gb = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(1);
    const base = G.render(true);
    const R = Object.fromEntries(G.palace().rooms.map((r) => [r.id, r]));
    G.teleport(R.bridge.x1 - 3, R.bridge.cz); G.step(2);
    const w0 = G.pieces2State().instWrites; G.step(120); o.still = G.pieces2State().instWrites - w0; o.dorm = G.pieces2State().nDorm;
    for (let k = 0; k < 4; k++) G.giantWake();
    const w1 = G.pieces2State().giants.find((x) => x.st === 1); G.teleport(w1.x, w1.z + 2.4);
    let tells = false;
    for (let i = 0; i < 60 * 8 && !tells; i++) { G.step(1); tells = G.pieces2State().giants.some((x) => x.ring || x.line); }
    const heavy = G.render(true), s = G.pieces2State();
    o.heavy = [heavy.calls, heavy.tris, s.nDorm, s.nAwake, tells];
    o.prog = [base.programs, heavy.programs]; o.geo = [base.geoms, heavy.geoms]; o.tex = [base.texs, heavy.texs];
    G.setBots(0); G.setMode('rumble'); G.reset(); G.step(2); const r1 = G.render(true); o.rIn = G.pieces2State().inScene;
    G.pieces2(false); G.reset(); G.step(2); const r0 = G.render(true); G.pieces2(true, true); G.reset();
    o.rumble = [r1.calls, r0.calls, r1.tris, r0.tris];
    return o;
  });
  check('1005 pieces budget (tier medium): bridge with 8 dormant + 4 awake giants and tells < 500 calls / 0.5M tris; programs, geometries, textures flat; no instance writes while still; Rumble unchanged',
    gb.heavy[0] < 500 && gb.heavy[1] < 500000 && gb.heavy[2] + gb.heavy[3] >= 10 && gb.heavy[3] >= 1 && gb.heavy[4] && gb.prog[0] === gb.prog[1] && gb.geo[0] === gb.geo[1] && gb.tex[0] === gb.tex[1]
    && gb.still === 0 && gb.dorm === 12 && !gb.rIn && gb.rumble[0] === gb.rumble[1] && gb.rumble[2] === gb.rumble[3], JSON.stringify(gb));

  // 1006 New run in the same page (twice) after giants, a douse and broken vats: every giant dormant at home, none awake, counters at zero, clocks
  // full and rewritten, no tell or flood left in the scene.
  const gr = await g(() => {
    const G = __game, o = { runs: [] };
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset();
    for (let k = 0; k < 3; k++) G.giantWake();
    for (let i = 0; i < 60 * 5; i++) G.step(1);
    for (let k = 0; k < 2; k++) {
      G.reset(); G.step(1); const s = G.pieces2State();
      o.runs.push({ home: s.giants.every((x) => x.st === 0 && x.x === x.hx && x.z === x.hz && !x.ring && !x.line && x.hits === 0), awake: s.awake, wakes: s.wakes, douses: s.douses, notes: s.notes,
        clocks: s.clocks.every((c) => c.step === 48 && c.writes >= 1), vats: s.vats.every((v) => v.st === 0 && !v.flood && !v.ring), inScene: s.inScene });
    }
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1006 pieces new run (twice): giants dormant at home, counters zero, clocks full and rewritten, vats whole, no tell or flood left',
    gr.runs.every((r) => r.home && r.awake === 0 && r.wakes === 0 && r.douses === 0 && r.notes === 0 && r.clocks && r.vats && r.inScene), JSON.stringify(gr) + ' ' + tx.piece2_giant_voice.length);
}
