// The Burning Palace ticket 03 checks (door locks, rivals out of sight, announcements, spawn state, core seal, final two, apex start), numbers 500+.
// Called from tests/run.mjs with its page helper g, check() and the load-time render (base). Every check ends back in Royal Rumble with bots 0.
export async function palace3Checks(g, check, base) {
  await g(() => {
    // Palace run with n bots (seed 12345 unless given); R = rooms by id, D = doors.
    // guards = keep the guard squads per room (ticket 02), burn = keep the burning (ticket 04, when built); both off by default so these checks
    // test the rivals alone (restored by __p3end).
    const GU = Object.assign({}, __game.config.PAL_SIM.guard), BU = __game.config.BURN ? __game.config.BURN.on : null;
    window.__p3 = (n, seed, guards, burn) => {
      const G = __game, C = G.config; for (const k in GU) C.PAL_SIM.guard[k] = guards ? GU[k] : 0; if (C.BURN) C.BURN.on = !!burn && BU;
      G.setSeed(seed || 12345); G.setMode('palace'); G.setBots(n); G.reset();
      const p = G.palace(); return { R: Object.fromEntries(p.rooms.map((r) => [r.id, r])), D: p.doors };
    };
    // Only rival k left, out of sight in room id with hp and meter (the others out).
    window.__p3only = (k, id, hp, ch) => { const G = __game, n = G.palSim().recs.length; for (let i = 0; i < n; i++) if (i !== k) G.palSimSet(i, null); G.palSimSet(k, id, hp, ch); };
    window.__p3end = () => { const G = __game; for (const k in GU) G.config.PAL_SIM.guard[k] = GU[k]; if (G.config.BURN) G.config.BURN.on = BU; G.clearMove(); G.setBots(0); G.setMode('rumble'); G.reset(); };
  });

  // 500 Door locks (owner 24 Nov 13:26: no fleeing): a rival behind the hall door comes into sight when it opens; inside the court and clear of its
  // doors the room locks (every court door shut and locked, her line queued); the door back does not open at arm's length, no route out;
  // a rival tracking the player does not enter the locked room; the rival broken, the court opens again.
  const d500 = await g(() => {
    const G = __game, o = {}; const { R, D } = __p3(8);
    __p3only(0, 'court', 100, 40); G.setHp(1e9);
    G.teleport(D[0].x, D[0].z + 1.6); G.step(1); let s = G.palSim();
    o.open = { door: G.palace().doors[0].open, st: s.recs[0].st, room: s.recs[0].room, inScene: s.recs[0].inScene, locked: s.locked.join() };
    G.teleport(R.court.cx, R.court.cz); G.step(1); s = G.palSim(); const p = G.palace();
    const courtDoors = p.doors.map((d, i) => (d.a === 'court' || d.b === 'court' ? i : -1)).filter((i) => i >= 0);
    o.lock = { locked: s.locked.join(), doors: courtDoors.map((i) => s.doorsLocked[i] && !p.doors[i].open).every(Boolean), n: courtDoors.length, lockN: s.lockN };
    G.teleport(D[0].x, D[0].z - 1.6); G.step(30); o.atDoor = { open: G.palace().doors[0].open, cur: G.palace().cur, card: G.palace().card === G.text.pal3_door_locked.replace('{room}', R.court.name) };
    o.route = G.palMoveTo(R.hall.cx, R.hall.cz);
    G.palSimSet(1, 'corridor', 100, 0); G.palHunter(1); G.teleport(R.court.cx, R.court.cz); G.step(600); s = G.palSim();
    o.hunterOut = { room: s.recs[1].room, st: s.recs[1].st };
    G.hitBot(0, 1e4); G.step(1); s = G.palSim();
    o.after = { r0: s.recs[0].st, locked: s.locked.join(), door0: s.doorsLocked[0], route: G.palMoveTo(R.hall.cx, R.hall.cz) };
    o.rumble = G.palSim().on; __p3end(); return o;
  });
  check('500 door locks: a rival comes into sight as the door opens; inside and clear of the doors the court locks (all doors shut + locked); no way out (door, route); a hunter waits outside; broken = open',
    d500.open.door && d500.open.st === 'live' && d500.open.room === 'court' && d500.open.inScene && d500.open.locked === ''
    && d500.lock.locked === 'court' && d500.lock.doors && d500.lock.n === 3 && d500.lock.lockN === 1 && !d500.atDoor.open && d500.atDoor.cur === 'court' && d500.atDoor.card && !d500.route
    && d500.hunterOut.room === 'corridor' && d500.hunterOut.st === 'sim' && d500.after.r0 === 'out' && d500.after.locked === '' && !d500.after.door0 && d500.after.route, JSON.stringify(d500));

  // 501 The off-screen simulation is deterministic per seed (owner 24 Nov 13:26; check 82 style): 8 rivals, the player standing in the start hall
  // (kept alive) for 150 s: the same seed gives the same results log twice; another seed differs; rivals were settled out of sight.
  const d501 = await g(() => {
    const G = __game, C = G.config;
    const run = (seed) => { __p3(8, seed); G.setHp(1e9); for (let t = 0; t < 150 / C.STEP && G.palace().phase === 'palace'; t++) G.step(1); const s = G.palSim(); return { log: s.log.join(';'), outN: s.outN, kinds: s.log.map((l) => l.split('|')[0]) }; };
    const a = run(12345), b = run(12345), c = run(2); __p3end();
    return { same: a.log === b.log, differs: a.log !== c.log, outA: a.outN, outC: c.outN, killsA: a.kinds.filter((k) => k === 'kill').length, farms: a.kinds.filter((k) => k === 'farm').length, a: a.log.slice(0, 300) };
  });
  check('501 off-screen simulation deterministic per seed: same seed same results log; another seed differs; rivals settled out of sight within 150 s',
    d501.same && d501.differs && d501.outA > 0 && d501.killsA > 0, JSON.stringify(d501));

  // 502 Every result is announced (owner 24 Nov 13:26): over a 150 s run every rival out is queued as her line from TEXT keys (winner, loser, room)
  // and shown on the banner (none dropped); each leaves a trace in its room; the hunter is announced.
  const d502 = await g(() => {
    const G = __game, C = G.config, T = G.text, shown = []; __p3(8, 12345); G.setHp(1e9); let last = '';
    for (let t = 0; t < 200 / C.STEP && G.palace().phase === 'palace'; t++) {
      G.step(1); const p = G.palace();
      if (p.banner === 'block' && p.rule !== last) { last = p.rule; shown.push(p.rule); }
      if (t > 150 / C.STEP && G.palSim().qn === 0) break;
    }
    const s = G.palSim(), names = Object.values(T).filter((v, i) => Object.keys(T)[i].startsWith('school_')), rooms = G.palace().rooms.map((r) => r.name);
    const kill = (r) => / broke /.test(r) && rooms.some((n) => r.indexOf(n) >= 0), fell = (r) => / fell in the /.test(r);
    const o = { outN: s.outN, shownOut: shown.filter((r) => kill(r) || fell(r)).length, drop: s.qDrop, qn: s.qn, traces: s.traces.length, hunt: shown.some((r) => r.indexOf('tracks you') >= 0),
      named: shown.filter(kill).every((r) => names.filter((n) => r.indexOf(n) >= 0).length >= 1), sample: shown.slice(0, 4), keys: ['pal3_r_kill', 'pal3_r_fell', 'pal3_v_kill', 'pal3_r_lock', 'pal3_v_lock', 'pal3_r_hunt', 'pal3_v_hunt', 'pal3_r_final', 'pal3_v_final', 'pal3_r_core', 'pal3_v_core', 'pal3_door_sealed', 'pal3_door_locked', 'pal3_you'].every((k) => !!T[k]) };
    __p3end(); return o;
  });
  check('502 every rival out is announced on the banner from TEXT keys (winner, loser, room; none dropped) and leaves a trace in its room; the hunter is announced',
    d502.outN > 0 && d502.shownOut === d502.outN && d502.drop === 0 && d502.qn === 0 && d502.traces === d502.outN && d502.named && d502.hunt && d502.keys, JSON.stringify(d502));

  // 503 Rivals come into sight in their simulated state (owner 24 Nov 13:26): health and meter as simulated, standing on a free point of their room;
  // out of sight again they keep it; a hunter walks in through the door it came by (inside the room, at that door), in its state.
  const d503 = await g(() => {
    const G = __game, o = {}; const { R, D } = __p3(8);
    __p3only(0, 'court', 37, 55); G.setHp(1e9);
    G.teleport(D[0].x, D[0].z + 1.6); G.step(1); let s = G.palSim(), r0 = s.recs[0];
    o.live = { st: r0.st, hp: r0.hp, ch: +r0.ch.toFixed(2), room: G.palRoomAt(r0.x, r0.z), walk: G.walkable ? G.walkable(r0.x, r0.z, 0.05) : true };
    G.teleport(R.hall.cx, R.hall.cz); G.step(60); s = G.palSim(); r0 = s.recs[0];
    o.parked = { st: r0.st, hp: r0.hp, inScene: r0.inScene, room: r0.room };
    G.palSimSet(0, 'court', 50, 10); G.palHunter(0); let t = 0;
    for (; t < 1200 && G.palSim().recs[0].st !== 'live'; t++) G.step(1);
    s = G.palSim(); r0 = s.recs[0]; const d = D[0];
    o.walkIn = { st: r0.st, room: G.palRoomAt(r0.x, r0.z), hp: r0.hp, atDoor: +Math.hypot(r0.x - d.x, r0.z - d.z).toFixed(2), s: +(t / 60).toFixed(1) };
    __p3end(); return o;
  });
  check('503 rivals come into sight in their simulated state (hp, meter) on a free point of their room, keep it out of sight; a hunter walks in at the door it came by',
    d503.live.st === 'live' && d503.live.hp === 37 && Math.abs(d503.live.ch - 55) < 0.1 && d503.live.room === 'court' && d503.live.walk
    && d503.parked.st === 'sim' && d503.parked.hp === 37 && !d503.parked.inScene && d503.parked.room === 'court'
    && d503.walkIn.st === 'live' && d503.walkIn.room === 'hall' && d503.walkIn.hp === 50 && d503.walkIn.atDoor < 2.5, JSON.stringify(d503));

  // 504 The core hall is sealed while any rival stands (owner 24 Nov 14:16): no route to it, its door stays shut at arm's length and walking into it
  // keeps the player on the bridge; the door card says sealed with the count; with every rival out it opens (her line) and walking in wakes the 兵家 apex.
  const d504 = await g(() => {
    const G = __game, o = {}; const { R, D } = __p3(8);
    G.setHp(1e9); const ci = D.findIndex((d) => d.a === 'core' || d.b === 'core'), dc = D[ci];
    o.route = G.palMoveTo(R.core.cx, R.core.cz);
    G.teleport(dc.x, dc.z + 1.6); G.step(30); let p = G.palace(), s = G.palSim();
    o.sealed = { open: p.doors[ci].open, locked: s.doorsLocked[ci], cur: p.cur, card: p.card === G.text.pal3_door_sealed.replace('{room}', R.core.name).replace('{n}', String(s.standing)), standing: s.standing };
    G.setMove(0, -1); G.step(300); G.clearMove(); o.pushed = { cur: G.palace().cur, phase: G.palace().phase };
    for (let k = 0; k < s.recs.length; k++) G.palSimSet(k, null);
    G.teleport(dc.x, dc.z + 1.6); G.step(2); s = G.palSim(); p = G.palace();
    o.opened = { open: s.open, locked: s.doorsLocked[ci], door: p.doors[ci].open };
    let rule = ''; for (let t = 0; t < 600 && rule.indexOf('core hall is open') < 0; t++) { G.step(1); rule = G.palace().rule; } o.line = rule.indexOf('core hall is open') >= 0;
    G.setMove(0, -1); let t = 0; for (; t < 600 && G.palace().phase === 'palace'; t++) G.step(1); G.clearMove();
    p = G.palace(); o.apex = { phase: p.phase, on: p.on, voice: p.voice === G.text.voice_wake };
    __p3end(); return o;
  });
  check('504 core sealed while rivals stand: no route, door shut and locked at arm\'s length, walking in keeps you on the bridge, card says sealed (count); all out = open, announced; walking in wakes the apex',
    !d504.route && !d504.sealed.open && d504.sealed.locked && d504.sealed.cur === 'bridge' && d504.sealed.card && d504.sealed.standing === 8 && d504.pushed.cur === 'bridge' && d504.pushed.phase === 'palace'
    && d504.opened.open && !d504.opened.locked && d504.opened.door && d504.line && d504.apex.phase === 'wake' && !d504.apex.on && d504.apex.voice, JSON.stringify(d504));

  // 505 The last two (owner 24 Nov 13:26): with one rival left it is announced and tracks the player room by room; it walks into the player's hall,
  // which locks with both inside; broken, the hall opens and the core seal lifts.
  const d505 = await g(() => {
    const G = __game, C = G.config, o = {}; __p3(8); G.setHp(1e9);
    __p3only(0, 'garden', 100, 0); G.palHunter(0); const r0 = () => G.palSim().recs[0];
    G.step(1); let s = G.palSim(); o.final = { final: s.final, hunter: s.hunter, line: G.palace().rule.indexOf('comes for you') >= 0 };
    let t = 0; for (; t < 40 / C.STEP && !(r0().st === 'live' && G.palRoomAt(r0().x, r0().z) === 'hall' && G.palSim().locked.indexOf('hall') >= 0); t++) G.step(1);
    s = G.palSim(); const p = G.palace(), hallDoors = p.doors.map((d, i) => (d.a === 'hall' || d.b === 'hall' ? i : -1)).filter((i) => i >= 0);
    o.duel = { st: s.recs[0].st, room: G.palRoomAt(s.recs[0].x, s.recs[0].z), locked: s.locked.join(), doors: hallDoors.every((i) => s.doorsLocked[i]), s: +(t * C.STEP).toFixed(1) };
    G.hitBot(0, 1e4); G.step(1); s = G.palSim(); const ci = p.doors.findIndex((d) => d.a === 'core' || d.b === 'core');
    o.after = { open: s.open, locked: s.locked.join(), core: s.doorsLocked[ci], standing: s.standing, alive: s.alive };
    __p3end(); return o;
  });
  check('505 the last two: one rival left is announced and tracks the player; it walks into the hall, which locks with both inside; broken = hall open and the core unsealed',
    d505.final.final && d505.final.hunter === 0 && d505.duel.st === 'live' && d505.duel.room === 'hall' && d505.duel.locked === 'hall' && d505.duel.doors && d505.final.line
    && d505.after.open && d505.after.locked === '' && !d505.after.core && d505.after.standing === 0 && d505.after.alive === 1, JSON.stringify(d505));

  // 506 Rivals fight in sight with the bot brain in the palace: two rivals put in the court with the player at the hall door see each other and fight
  // (one is broken within 60 s, no page errors from the brain), nobody walks out of the palace floors.
  const d506 = await g(() => {
    const G = __game, C = G.config, o = { off: 0 }; const { R, D } = __p3(8);
    for (let i = 2; i < G.palSim().recs.length; i++) G.palSimSet(i, null);
    G.palSimSet(0, 'court', 100, 0); G.palSimSet(1, 'court', 100, 0); G.setHp(1e9); G.teleport(R.hall.cx, R.hall.cz);
    G.teleport(D[0].x, D[0].z + 1.6); G.step(1); o.live = G.palSim().recs.slice(0, 2).map((r) => r.st).join();
    G.palPlaceBot(0, R.court.cx - 1.5, R.court.cz - 4); G.palPlaceBot(1, R.court.cx + 1.5, R.court.cz - 4);
    G.teleport(D[0].x, D[0].z + 2.2);
    let t = 0; for (; t < 60 / C.STEP && G.palSim().outN === 0; t++) { G.step(1); for (const r of G.palSim().recs.slice(0, 2)) if (r.st === 'live' && !G.palRoomAt(r.x, r.z)) o.off++; }
    o.outN = G.palSim().outN; o.s = +(t * C.STEP).toFixed(1); __p3end(); return o;
  });
  check('506 rivals in sight fight each other with the bot brain inside the palace (one broken within 60 s), never off the palace floors',
    d506.live === 'live,live' && d506.outN >= 1 && d506.off === 0, JSON.stringify(d506));

  // 507 Budget, tier medium: the heaviest palace room = the court with every rival in sight and fighting, the player inside (locked), 5 s of fighting:
  // calls < 500, tris < 500k, no shader compile; geometry flat between two renders 3 s apart.
  const d507 = await g(() => {
    const G = __game, o = {}; const { R } = __p3(8);
    G.setHp(1e9); G.teleport(R.court.cx, R.court.cz); G.step(1);
    for (let i = 0; i < G.palSim().recs.length; i++) G.palSimSet(i, 'court', 100, 0);
    o.pre = G.render(true).programs; o.card = G.load().led.prog1; o.cardKind = G.load().led.kind; o.progNew = G.load().progNew; G.step(120); const a = G.render(true); G.step(180); const b = G.render(true);
    o.live = G.palSim().recs.filter((r) => r.st === 'live').length; o.locked = G.palSim().locked.join();
    o.calls = Math.max(a.calls, b.calls); o.tris = Math.max(a.tris, b.tris); o.programs = [a.programs, b.programs]; o.geoms = [a.geoms, b.geoms];
    __p3end(); return o;
  });
  // Batch 17b (game changed on purpose): the palace images' program now compiles under the palace loading card, not at page load: the fight is
  // compared with the programs at its start. Prototype (game changed on purpose: the card also compiles the palace art's programs): the programs
  // at the fight's start are exactly the count the last loading card's ledger left (prog1), so nothing compiled between that card and the fight.
  check('507 budget: court with every rival in sight fighting the player (locked): calls<500, tris<500k, no shader compile, geometry flat',
    d507.live >= 6 && d507.locked === 'court' && d507.calls < 500 && d507.tris < 500000 && d507.programs[0] === d507.pre && d507.programs[1] === d507.pre && d507.pre === d507.card && d507.geoms[0] === d507.geoms[1], JSON.stringify(d507));

  // 508 New run in the same page after a palace run with rivals: every record back in its seeded start room at full health, no locks, no traces,
  // no hunter, the queue empty, the core sealed again; the same start for the same seed.
  const d508 = await g(() => {
    const G = __game, C = G.config;
    const start = () => { const s = G.palSim(); return s.recs.map((r) => r.st + ':' + r.room + ':' + r.hp).join(','); };
    __p3(8, 7); const s0 = start(); G.setHp(1e9);
    for (let t = 0; t < 80 / C.STEP && G.palace().phase === 'palace'; t++) G.step(1);
    const mid = G.palSim(); G.setSeed(7); G.reset(); const s = G.palSim(), ci = G.palace().doors.findIndex((d) => d.a === 'core' || d.b === 'core');
    const o = { midOut: mid.outN, same: start() === s0, locked: s.locked.join(), traces: s.traces.length, hunter: s.hunter, qn: s.qn, outN: s.outN, final: s.final, open: s.open, core: s.doorsLocked[ci], standing: s.standing };
    __p3end(); return o;
  });
  check('508 palace new run after rivals: same seeded start, no locks, traces, hunter, queue or results left; core sealed again',
    d508.midOut > 0 && d508.same && d508.locked === '' && d508.traces === 0 && d508.hunter === -1 && d508.qn === 0 && d508.outN === 0 && !d508.final && !d508.open && d508.core && d508.standing === 8, JSON.stringify(d508));

  // 509 The burning and the rivals together (BP04 merged; owner 24 Nov 13:44 fairness rule): 3 seeds of palace bot runs (8 rivals, the player kept
  // alive on the bridge, which never burns, up to 260 s): burnState().bad stays 0 every tick, no room is ever locked while warned or fallen, no rival stays out
  // of sight in a fallen room, and nothing is dropped from her queue; scripted: a rival entering the player's warned room does not lock it, and
  // a rival out of sight in a falling room falls (announced). Guard squads on, the player on the autopilot (it fights in its room, so locks end).
  // Needs the burning (ticket 04): without it this check is not registered (not a pass).
  const has509 = await g(() => typeof __game.burnState === 'function');
  if (!has509) console.log('SKIP 509 burning not in this build (ticket 04 not merged): not run');
  else {
    const d509 = await g(() => {
      const G = __game, C = G.config, o = { viol: [], runs: [] }, bad = (x) => { if (o.viol.length < 6) o.viol.push(x); };
      for (const seed of [12345, 2, 3]) {
        const { R } = __p3(8, seed, true, true); G.teleport(R.bridge.cx, R.bridge.cz); G.setHp(1e9); G.autoPlayer(true); let t = 0;
        for (; t < 260 / C.STEP && G.palace().phase === 'palace'; t++) {
          G.step(1); const b = G.burnState();
          if (b.bad !== 0) { bad(`s${seed} t${t} burn bad ${b.badWhy} ${b.badRoom}`); break; }
          if (t % 6) continue;
          const s = G.palSim(), fallen = new Set(b.rooms.filter((r) => r.fallen).map((r) => r.id)), warned = new Set(b.rooms.filter((r) => r.warned).map((r) => r.id));
          for (const id of s.locked) if (warned.has(id) || fallen.has(id)) bad(`s${seed} t${t} locked ${id} warned/fallen`);
          for (const r of s.recs) if (r.st === 'sim' && fallen.has(r.room)) bad(`s${seed} t${t} rival in fallen ${r.room}`);
        }
        const s = G.palSim(), b = G.burnState();
        o.runs.push({ seed, s: +(t * C.STEP).toFixed(0), phase: G.palace().phase, pcause: G.player().cause, falls: b.falls, out: s.outN, fellLog: s.log.filter((l) => l.startsWith('fell')).length, bad: b.bad, drop: s.qDrop });
        G.autoPlayer(false);
      }
      // Scripted: a rival walks into the player's warned courtyard: the room must not lock; a rival left out of sight in the corridor (west wing)
      // falls with it, announced as a fall.
      {
        const { R } = __p3(8, 12345, false, true); G.setHp(1e9); const n = G.palSim().recs.length;
        for (let i = 0; i < n; i++) G.palSimSet(i, null);
        G.palSimSet(1, 'garden', 100, 0); G.teleport(R.court.cx, R.court.cz); let t = 0;
        const warnedCourt = () => G.burnState().rooms.find((r) => r.id === 'court').warned;
        for (; t < 200 / C.STEP && !warnedCourt(); t++) { G.step(1); G.teleport(R.court.cx, R.court.cz); }
        G.palSimSet(0, 'court', 100, 0); let lockedWarned = 0; const sc = { warnedAt: +(t * C.STEP).toFixed(1), live: G.palSim().recs[0].st };
        for (let k = 0; k < 60; k++) { G.step(1); if (G.palSim().locked.indexOf('court') >= 0) lockedWarned++; }
        sc.lockedWarned = lockedWarned; sc.bad = G.burnState().bad; G.palSimSet(0, null);
        G.teleport(R.bridge.cx, R.bridge.cz); G.palSimSet(2, 'corridor', 100, 0);
        const fellCorr = () => G.burnState().rooms.find((r) => r.id === 'corridor').fallen;
        for (t = 0; t < 200 / C.STEP && !fellCorr(); t++) G.step(1);
        G.step(2); const s = G.palSim(); sc.r2 = s.recs[2].st; sc.fellLog = s.log.filter((l) => l.startsWith('fell|') && l.indexOf('corridor') >= 0).length; sc.bad2 = G.burnState().bad;
        o.scripted = sc;
      }
      __p3end(); return o;
    });
    check('509 burning + rivals + guard, 3 seeds (autopilot player; one run sees >= 3 wings fall): burnState().bad 0 every tick, never a locked warned/fallen room, no rival left in a fallen room, nothing dropped from her queue',
      d509.viol.length === 0 && d509.runs.every((r) => r.bad === 0 && r.drop === 0) && d509.runs.some((r) => r.falls >= 3)
      && d509.scripted.live === 'live' && d509.scripted.lockedWarned === 0 && d509.scripted.bad === 0 && d509.scripted.r2 === 'out' && d509.scripted.fellLog === 1 && d509.scripted.bad2 === 0, JSON.stringify(d509));
  }

  // 510 Rooms and the 皇家 guard (ticket 02 merged): a room's squad appears when its door opens (never in the start hall); inside with the squad the
  // room locks; every guard broken, it opens; a rival in sight fights the guard; out of sight a lone rival breaks a room's squads (guardLeft falls).
  // Needs spawnSquad (ticket 02): without it this check is not registered (not a pass).
  const has510 = await g(() => typeof __game.guardSpawn === 'function');
  if (!has510) console.log('SKIP 510 guard not in this build (ticket 02 not merged): not run');
  else {
    const d510 = await g(() => {
      const G = __game, C = G.config, o = {}; const { R, D } = __p3(8, 12345, true);
      const alive = () => G.guards().list.filter((u) => u.alive);
      const n = G.palSim().recs.length; for (let i = 0; i < n; i++) G.palSimSet(i, null); G.setHp(1e9);
      o.start = { guards: alive().length, hallLeft: G.palSim().guardLeft[G.palace().rooms.findIndex((r) => r.id === 'hall')] };
      G.teleport(D[0].x, D[0].z + 1.6); G.step(1);
      const inCourt = () => alive().filter((u) => G.palRoomAt(u.x, u.z) === 'court').length;
      o.spawn = { court: inCourt(), left: G.palSim().guardLeft[G.palace().rooms.findIndex((r) => r.id === 'court')] };
      G.teleport(R.court.cx + 12, R.court.cz + 10); G.step(2); o.lock = G.palSim().locked.join();
      const list = G.guards().list; for (let i = 0; i < list.length; i++) if (list[i].alive) G.guardStrike(-1, i, 1e4, false);
      G.step(2); o.open = { locked: G.palSim().locked.join(), court: inCourt() };
      __p3(8, 12345, true); G.setHp(1e9); for (let i = 0; i < n; i++) G.palSimSet(i, null); G.palSimSet(0, 'court', 100, 0);
      const k0 = G.guards().kills; G.teleport(D[0].x, D[0].z + 1.6);
      let t = 0; for (; t < 40 / C.STEP && G.guards().kills === k0; t++) { G.step(1); G.teleport(D[0].x, D[0].z + 1.6); }
      o.fight = { kills: G.guards().kills - k0, s: +(t * C.STEP).toFixed(1) };
      __p3(8, 12345, true); G.setHp(1e9); for (let i = 0; i < n; i++) G.palSimSet(i, null); G.palSimSet(0, 'garden', 100, 0);
      const gi = G.palace().rooms.findIndex((r) => r.id === 'garden'), g0 = G.palSim().guardLeft[gi];
      for (let s = 0; s < 30 / C.STEP; s++) G.step(1);
      o.farm = { before: g0, after: G.palSim().guardLeft[gi], log: G.palSim().log.filter((l) => l.startsWith('farm')).length };
      __p3end(); return o;
    });
    check('510 rooms and the guard: a squad appears when the door opens (not in the start hall); locked in with it; all broken = open; a rival fights it; off-screen farming',
      d510.start.guards === 0 && d510.start.hallLeft === 0 && d510.spawn.court > 0 && d510.spawn.left === 0 && d510.lock === 'court' && d510.open.locked === '' && d510.open.court === 0
      && d510.fight.kills > 0 && d510.farm.after < d510.farm.before && d510.farm.log > 0, JSON.stringify(d510));
  }

  // 511 (integration 24 Nov, lead's merge list) The full palace with rivals, guard, 反贼, giants and the burning: each rival starts in its own
  // school's hall; squads come from BP05's escalation (no squad in the start hall, none in the core); a seeded share of rooms hold rebels;
  // a palace bot run (8 rivals, the player kept alive on the forecourt, which never burns, autopilot, up to 260 s): burnState().bad 0 every tick,
  // never a locked warned/fallen room, no rival out of sight in a fallen room, nothing dropped from her queue, >= 3 wings fall.
  const has511 = await g(() => typeof __game.burnState === 'function' && typeof __game.setLayout === 'function' && typeof __game.pieces2State === 'function');
  if (!has511) console.log('SKIP 511 full palace pieces not in this build: not run');
  else {
    const d511 = await g(() => {
      const G = __game, C = G.config, o = { viol: [] }, bad = (x) => { if (o.viol.length < 6) o.viol.push(x); };
      G.setLayout('full'); const { R } = __p3(8, 12345, true, true);
      const p = G.palace(), pl = G.palPlan(), s0 = G.palSim(), byId = Object.fromEntries(pl.rooms.map((r) => [r.id, r]));
      o.layout = pl.layout;
      o.home = s0.recs.filter((r) => r.st !== 'out').map((r) => (byId[r.room] && byId[r.room].school === r.school ? 1 : 0)).reduce((a, b) => a + b, 0);
      o.rivals = s0.recs.filter((r) => r.st !== 'out').length;
      const ix = (id) => pl.rooms.findIndex((r) => r.id === id);
      o.startLeft = s0.guardLeft[ix(pl.start)]; o.coreLeft = s0.guardLeft[ix('core')];
      o.escOk = pl.rooms.every((r, i) => r.id === pl.start || s0.guardLeft[i] === G.palEsc(r.id, 0).squads);
      o.rebelRooms = s0.rebelLeft.filter((v) => v > 0).length;
      G.teleport(R.fore.cx, R.fore.cz); G.setHp(1e9); G.autoPlayer(true); let t = 0;
      // The autopilot is not burn-aware (first run: it walked into a burning wing and fell at 90 s): kept in the forecourt, where it fights what comes.
      for (; t < 260 / C.STEP && G.palace().phase === 'palace'; t++) {
        G.step(1); const b = G.burnState();
        if (G.palace().cur !== 'fore') G.teleport(R.fore.cx, R.fore.cz);
        // Kept alive: a guard kill's heal caps health at full, and the forecourt's woken giants and mercury hit hard (second run: 'hazard' at 90 s).
        if (t % 6 === 0) G.setHp(1e9);
        if (b.bad !== 0) { bad(`t${t} burn bad ${b.badWhy} ${b.badRoom}`); break; }
        if (t % 6) continue;
        const s = G.palSim(), fallen = new Set(b.rooms.filter((r) => r.fallen).map((r) => r.id)), warned = new Set(b.rooms.filter((r) => r.warned).map((r) => r.id));
        for (const id of s.locked) if (warned.has(id) || fallen.has(id)) bad(`t${t} locked ${id} warned/fallen`);
        for (const r of s.recs) if (r.st === 'sim' && fallen.has(r.room)) bad(`t${t} rival in fallen ${r.room}`);
      }
      const s = G.palSim(), b = G.burnState();
      o.run = { s: +(t * C.STEP).toFixed(0), phase: G.palace().phase, pcause: G.player().cause, falls: b.falls, out: s.outN, bad: b.bad, drop: s.qDrop, giantLog: s.log.filter((l) => l.startsWith('giant')).length };
      G.autoPlayer(false); G.setLayout('proto'); __p3end(); return o;
    });
    check('511 full palace: rivals start in their own halls, squads from the escalation table (none in the start hall or core), rebels in some rooms; bot run with the burning: bad 0, no locked warned/fallen room, no rival in a fallen room, nothing dropped, >= 3 wings fall',
      d511.layout === 'full' && d511.rivals === 8 && d511.home === 8 && d511.startLeft === 0 && d511.coreLeft === 0 && d511.escOk && d511.rebelRooms > 0
      && d511.viol.length === 0 && d511.run.bad === 0 && d511.run.drop === 0 && d511.run.falls >= 3, JSON.stringify(d511));
  }
}
