// 皇家 guard checks (Burning Palace ticket 02), numbers 300+. Called from tests/run.mjs with its page helper g, check() and the load-time render (base).
// Map: the player stands at A in the south centre courtyard (C2); squads spawn at S, 10 m north, facing the player; FAR = 28 m away (outside aggro).
export async function guardChecks(g, check, base) {
  const SETUP = () => {
    window.__gs = (bots) => {
      const G = __game; G.setSeed(12345); G.setBots(bots || 0); G.reset(); G.teleport(-7, -6); return { A: [-7, -6], S: [-7, 4], FAR: [5, -22] };
    };
  };
  await g(SETUP);

  // 300 Spawn API and pools: fixed pool sizes; the squad cap; chariots only in open rooms; one 伍长 leads; unknown faction, full pools and the hunt refuse.
  // (Ticket 07: the pool table also holds the 反贼 types; this check reads the 皇家 ones, check 900 the rest.)
  const d300 = await g(() => {
    const G = __game, C = G.config, o = {}; const { S } = __gs(0);
    o.pool = G.guards().pool;
    const list = ['wz', 'wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'che', 'che', 'zu', 'zu'];
    // An open room first, from full pools: 18 asked (one 伍长), 12 placed.
    const q2 = G.guardSpawn('huangjia', ['wz', 'che', 'che', 'dun', 'dun', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'nu'], S[0] + 12, S[1], { fz: -1, open: true }), r2 = G.guards();
    o.open = { id: q2, n: r2.squads[q2] ? r2.squads[q2].n : -1, che: r2.list.filter((u) => u.alive && u.sq === q2 && u.type === 'che').length };
    G.reset();
    const q1 = G.guardSpawn('huangjia', list, S[0], S[1], { fz: -1 }), r1 = G.guards();
    o.closed = { id: q1, n: r1.n, che: r1.list.filter((u) => u.alive && u.type === 'che').length, wz: r1.list.filter((u) => u.alive && u.type === 'wz').length,
      lead: r1.squads[q1].lead, leadType: r1.list[r1.squads[q1].lead] ? r1.list[r1.squads[q1].lead].type : '', broken: r1.squads[q1].broken };
    o.badFaction = G.guardSpawn('nobody', ['zu'], S[0], S[1]);
    // Fill the pools: further squads take what is left, then -1; never more alive than the pool.
    const ids = [];
    for (let k = 0; k < 4; k++) ids.push(G.guardSpawn('huangjia', list, S[0] - 8, S[1] + 4 * k, { open: true }));
    const r3 = G.guards(), per = {};
    for (const u of r3.list) if (u.alive) per[u.type] = (per[u.type] || 0) + 1;
    o.more = ids; o.per = per; o.maxSquad = Math.max(...r3.squads.map((s) => s.n));
    o.over = Object.keys(per).filter((t) => per[t] > o.pool[t]);
    G.startHunt(); o.hunt = { id: G.guardSpawn('huangjia', ['zu'], S[0], S[1]), n: G.guards().n, staged: Object.values(G.guards().draw).some((d) => d.staged) };
    G.reset(); o.squadMax = C.GUARD.squadMax;
    return o;
  });
  check('300 guard spawn API: pools fixed (zu 10, nu 6, dun 4, che 2, wz 2); one 伍长 leads; no 车 unless open; cap 12 per squad; unknown faction, full pools and the hunt refuse',
    !!d300 && JSON.stringify(['zu', 'nu', 'dun', 'che', 'wz'].map((t) => d300.pool[t])) === JSON.stringify([10, 6, 4, 2, 2]) && d300.closed.id >= 0 && d300.closed.n === 11 && d300.closed.che === 0
    && d300.closed.wz === 1 && d300.closed.leadType === 'wz' && !d300.closed.broken && d300.open.id >= 0 && d300.open.n === d300.squadMax && d300.open.che === 2
    && d300.badFaction === -1 && d300.maxSquad <= d300.squadMax && d300.over.length === 0 && d300.more.includes(-1) && d300.hunt.id === -1 && d300.hunt.n === 0 && !d300.hunt.staged,
    JSON.stringify(d300));

  // 301 Each unit type's move: tell shown (red, its shape) for the whole windup (>= 0.4 s), then exactly its damage on the player (alone: no buff);
  // 弩手 marks the player's spot; 盾 shoves; 车 drives along its line; no 车 move without open.
  const d301 = await g(() => {
    const G = __game, C = G.config, GM = C.GUARD.moves, STEP = C.STEP, out = {};
    for (const t of ['zu', 'nu', 'dun', 'che', 'wz']) {
      const { A, S } = __gs(0), mv = C.GUARD.types[t].move, m = GM[mv];
      const dist = { zu: 6, nu: 7, dun: 6, che: 8, wz: 6 }[t];
      const q = G.guardSpawn('huangjia', [t], A[0], A[1] + dist, { fz: -1, open: true });
      const o = { q, move: mv, windup: m.windup, dmg: m.dmg, tell: null, hp: 100, hitAt: -1, x0: 0, x1: 0, p0: null, p1: null };
      let n = 0;
      for (; n < 15 / STEP; n++) {
        G.step(1);
        const r = G.guards(), s = G.state();
        if (!o.tell && r.tells.length) { const tl = r.tells[0]; o.tell = { shape: tl.shape, shown: tl.shown, red: tl.red, x: tl.x, z: tl.z, px: s.x, pz: s.z, left: tl.left }; o.x0 = r.list.find((u) => u.alive).z; o.p0 = [s.x, s.z]; }
        if (o.tell && r.tells.length && !r.tells[0].shown) o.tell.hidden = true;
        if (s.hp < 100) { o.hp = s.hp; o.hitAt = n; o.minTell = r.minTell; o.hits = r.hits; break; }
      }
      for (let k = 0; k < 40; k++) G.step(1);
      const r = G.guards(), s = G.state(), u = r.list.find((v) => v.alive);
      o.p1 = [s.x, s.z]; o.x1 = u ? u.z : 0; o.ownHurt = r.list.some((v) => v.alive && v.hp < v.max);
      out[t] = o;
    }
    // No 车 without open.
    const { A } = __gs(0); out.closedChe = G.guardSpawn('huangjia', ['che'], A[0], A[1] + 8, { fz: -1 });
    out.cfgMin = Math.min(...Object.values(GM).map((m) => m.windup));
    G.reset(); return out;
  });
  const ok301 = !!d301 && d301.cfgMin >= 0.4 && d301.closedChe === -1 && ['zu', 'nu', 'dun', 'che', 'wz'].every((t) => {
    const o = d301[t], sh = { zu: 'line', nu: 'mark', dun: 'circle', che: 'line', wz: 'line' }[t];
    if (!o || !o.tell || o.tell.shape !== sh || !o.tell.shown || !o.tell.red || o.tell.hidden || o.hitAt < 0) return false;
    if (Math.abs(100 - o.hp - o.dmg) > 1e-6 || o.minTell < o.windup - 0.02 || o.minTell < 0.4) return false;
    if (t === 'nu' && Math.hypot(o.tell.x - o.tell.px, o.tell.z - o.tell.pz) > 0.01) return false;
    if (t === 'dun' && Math.hypot(o.p1[0] - o.p0[0], o.p1[1] - o.p0[1]) < 1) return false;
    if (t === 'che' && Math.abs(o.x1 - o.x0) < 3) return false;
    return true;
  });
  check('301 guard moves: 卒 thrust, 弩手 volley on a ground marker, 盾 shove, 车 line charge (open only), 伍长 cut; red tell for the whole windup (>= 0.4 s), exact damage',
    ok301, JSON.stringify(d301));

  // 302 盾 block: a basic blow from its front deals block.k; from behind, or a skill from the front, deals full; a 卒 never blocks.
  const d302 = await g(() => {
    const G = __game, C = G.config, o = {}; const { A, S } = __gs(0);
    G.guardSpawn('huangjia', ['dun', 'zu'], S[0], S[1], { fz: -1 });
    const r = G.guards(), di = r.list.findIndex((u) => u.alive && u.type === 'dun'), zi = r.list.findIndex((u) => u.alive && u.type === 'zu');
    const hp = (i) => G.guards().list[i].hp, dun = r.list[di];
    G.teleport(dun.x, dun.z - 2); let h0 = hp(di); G.guardStrike(-1, di, 10, true); o.front = h0 - hp(di);
    h0 = hp(di); G.guardStrike(-1, di, 10, false); o.skill = h0 - hp(di);
    G.teleport(dun.x, dun.z + 2); h0 = hp(di); G.guardStrike(-1, di, 10, true); o.back = h0 - hp(di);
    const zu = G.guards().list[zi]; G.teleport(zu.x, zu.z - 2); h0 = hp(zi); G.guardStrike(-1, zi, 10, true); o.zu = h0 - hp(zi);
    o.blocks = G.guards().blocks; o.k = C.GUARD.block.k;
    G.reset(); return o;
  });
  check('302 盾 block: front basic blow x block.k; from behind and skills full; 卒 full; one block counted',
    !!d302 && Math.abs(d302.front - 10 * d302.k) < 1e-6 && Math.abs(d302.skill - 10) < 1e-6 && Math.abs(d302.back - 10) < 1e-6 && Math.abs(d302.zu - 10) < 1e-6 && d302.blocks === 1,
    JSON.stringify(d302));

  // 303 方阵: with the 伍长 alive the units hold their slots (盾 ahead, 弩手 behind), are buffed (damage x 1.25, taken x 0.75; not the 伍长) and a 卒 hit lands buffed;
  // killing the 伍长 breaks it (no buff, broken, one break counted, the player's note, charge, heal and the short boon); own volleys never hurt own units.
  const d303 = await g(() => {
    const G = __game, C = G.config, B = C.GUARD.buff, o = {}; const { S, FAR } = __gs(0);
    G.teleport(FAR[0], FAR[1]);
    const q = G.guardSpawn('huangjia', ['wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'nu', 'nu'], S[0], S[1], { fz: -1 });
    G.step(60);
    let r = G.guards(); const L = r.list[r.squads[q].lead], mine = r.list.filter((u) => u.alive && u.sq === q);
    o.form = mine.every((u) => u.form); o.buff = mine.every((u) => u.type === 'wz' ? u.dmgK === 1 && u.defK === 1 : Math.abs(u.dmgK - (1 + B.dmg)) < 1e-9 && Math.abs(u.defK - (1 - B.def)) < 1e-9);
    o.dunAhead = mine.filter((u) => u.type === 'dun').every((u) => u.z < L.z - 1); o.nuBehind = mine.filter((u) => u.type === 'nu').every((u) => u.z > L.z + 1);
    // One buffed thrust on the player: every other unit's move held back.
    const li = r.squads[q].lead, zi = r.list.findIndex((u) => u.alive && u.sq === q && u.type === 'zu' && Math.abs(u.slotL) < 1e-9);
    r.list.forEach((u, i) => { if (u.alive && i !== zi) G.guardSet(i, { gcd: 1e9 }); });
    G.teleport(L.x, L.z - C.GUARD.keep - 0.2); G.setHp(100);
    let n = 0; for (; n < 600 && G.state().hp >= 100; n++) G.step(1);
    o.thrust = 100 - G.state().hp; o.want = C.GUARD.moves.thrust.dmg * (1 + B.dmg);
    r = G.guards(); o.ownHurt = r.list.some((u) => u.alive && u.sq === q && u.hp < u.max);
    // Break the 方阵: the player kills the 伍长 (a skill blow, so no block).
    G.teleport(FAR[0], FAR[1]); G.step(1); G.setHp(50); G.setCharge(-1, 0);
    G.guardStrike(-1, li, 1000, false);
    const ch = G.chargeOf(-1), hp = G.state().hp, rv = G.royale();
    G.step(1);
    r = G.guards(); const left = r.list.filter((u) => u.alive && u.sq === q);
    o.after = { broken: r.squads[q].broken, breaks: r.breaks, form: left.some((u) => u.form), buff: left.some((u) => u.dmgK !== 1 || u.defK !== 1), n: left.length,
      ch, hp, bT: r.player.bT[C.GUARD.leaderBoon.i], bV: r.player.bV[C.GUARD.leaderBoon.i], voice: rv.voice, rule: rv.rule };
    o.wantCh = C.GUARD.types.wz.ult; o.wantHp = 50 + C.GUARD.types.wz.heal; o.boon = C.GUARD.leaderBoon;
    G.reset(); return o;
  });
  check('303 方阵: slots (盾 ahead, 弩手 behind), 伍长 buff on dealt and taken, a buffed thrust; 伍长 down breaks it (no buff), note, charge, heal, boon; no own-unit damage',
    !!d303 && d303.form && d303.buff && d303.dunAhead && d303.nuBehind && Math.abs(d303.thrust - d303.want) < 1e-6 && !d303.ownHurt
    && d303.after.broken && d303.after.breaks === 1 && !d303.after.form && !d303.after.buff && d303.after.n === 7 && Math.abs(d303.after.ch - d303.wantCh) < 1e-6
    && Math.abs(d303.after.hp - d303.wantHp) < 1e-6 && d303.after.bT > d303.boon.s - 0.1 && Math.abs(d303.after.bV - d303.boon.v) < 1e-9 && d303.after.voice.length > 0 && /伍长/.test(d303.after.rule),
    JSON.stringify(d303));

  // 304 Rewards: a kill by a suit gives that suit its type's charge and health (the player and a bot); no plate; a guard lost to a fall gives nothing
  // (fall.ch = only the meter's passive gain over the 2 steps, under 0.1).
  const d304 = await g(() => {
    const G = __game, C = G.config, T = C.GUARD.types, o = {}; const { S, FAR } = __gs(1);
    G.teleport(FAR[0], FAR[1]);
    G.guardSpawn('huangjia', ['zu', 'nu', 'dun', 'zu', 'zu'], S[0], S[1], { fz: -1 });
    // The bot on the placeholder kit (its ultimate on the meter), like the player.
    G.placeholderKit(0); G.setHp(50); G.setCharge(-1, 0); G.setCharge(0, 0);
    const r = G.guards(), idx = (t, k) => r.list.map((u, i) => [u, i]).filter(([u]) => u.alive && u.type === t)[k][1];
    for (const [t, k] of [['zu', 0], ['nu', 0], ['dun', 0]]) G.guardStrike(-1, idx(t, k), 1000, false);
    o.player = { ch: G.chargeOf(-1), hp: G.state().hp, plates: G.guards().player.plates, pk: G.guards().player.pk, kills: G.guards().kills };
    o.wantCh = T.zu.ult + T.nu.ult + T.dun.ult; o.wantHp = 50 + T.zu.heal + T.nu.heal + T.dun.heal;
    const b0 = G.bots().list[0]; o.botCh0 = G.chargeOf(0); o.botDead = b0.dead;
    G.guardStrike(0, idx('zu', 1), 1000, false); o.botCh = G.chargeOf(0); o.wantBot = T.zu.ult;
    // A fall: hit once by the player (it remembers its hitter), then moved over the void: lost with no reward.
    const fi = idx('zu', 2); G.guardStrike(-1, fi, 1, false); const ch1 = G.chargeOf(-1), k1 = G.guards().kills;
    G.guardSet(fi, { x: 0, z: -80, px: 0, pz: -80 }); G.step(2);
    const r2 = G.guards(); o.fall = { alive: r2.list[fi].alive, ch: G.chargeOf(-1) - ch1, kills: r2.kills - k1, n: r2.n };
    G.setBots(0); G.reset(); return o;
  });
  check('304 guard rewards: player kills give charge and health per type, a bot kill gives the bot its charge, no plate; a fall gives nothing',
    !!d304 && Math.abs(d304.player.ch - d304.wantCh) < 1e-6 && Math.abs(d304.player.hp - d304.wantHp) < 1e-6 && d304.player.plates === 0 && d304.player.kills === 3
    && !d304.botDead && Math.abs(d304.botCh - d304.botCh0 - d304.wantBot) < 1e-6 && !d304.fall.alive && d304.fall.ch < 0.1 && d304.fall.kills === 0 && d304.fall.n === 0,
    JSON.stringify(d304));

  // 305 Rival bots fight and farm the guard (bot target tag: the faction is hostile to suits): one bot near a squad goes for it and breaks guards.
  const d305 = await g(() => {
    const G = __game, C = G.config, STEP = C.STEP, o = { modes: {} }; __gs(1);
    G.teleport(5, -22); G.step(60);
    const b = G.bots().list[0];
    // 5 m beside the bot, on its own layer.
    const off = [[5, 0], [-5, 0], [0, 5], [0, -5]].find(([dx, dz]) => Math.abs(G.topY(b.x + dx, b.z + dz) - b.y) < 0.3) || [5, 0];
    o.q = G.guardSpawn('huangjia', ['zu', 'zu', 'zu', 'nu'], b.x + off[0], b.z + off[1], { fx: -off[0], fz: -off[1] });
    let n = 0; o.at = -1;
    for (; n < 40 / STEP; n++) {
      G.step(1);
      const bb = G.bots().list[0]; if (bb.mode) o.modes[bb.mode] = (o.modes[bb.mode] || 0) + 1;
      if (bb.mode === 'creature' && bb.tgt === -2 && o.at < 0) o.at = +(n * STEP).toFixed(2);
      if (G.guards().kills >= 2 || bb.dead) break;
    }
    const r = G.guards(); o.kills = r.kills; o.hurt = r.list.filter((u) => u.sq >= 0 && u.hp < u.max).length; o.botDead = G.bots().list[0].dead; o.t = +(n * STEP).toFixed(1);
    G.setBots(0); G.reset(); return o;
  });
  check('305 rival bots farm the 皇家 guard: a bot goes for a squad in sight and breaks guards (kills >= 1)',
    !!d305 && d305.q >= 0 && d305.at >= 0 && d305.kills >= 1, JSON.stringify(d305));

  // 306 Budget with two full squads drawn (24 guards, tells up): calls < 500, tris < 500k; the guards draw only instanced crowd batches and their tells
  // (prototype, game changed on purpose: the guard models draw one batch per type x LOD x material, docs/HOOKS-17fgh.md section 4; before the models
  // it was one box batch per type, <= 5 calls added). Exact, counted by the renderer per draw: every draw that is not a tell, a crowd batch, a
  // character rig mesh or a painted-card batch (other) is the same number as in the empty scene, and no crowd batch draws in the empty scene;
  // no shader compile, geometry flat; after all are broken, no guard mesh stays in the scene.
  const d306 = await g(() => {
    const G = __game, o = {}; const { A } = __gs(0);
    const empty = G.render(true), ec = G.census();
    const full = ['wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'nu', 'che'];
    o.q = [G.guardSpawn('huangjia', full, A[0], A[1] + 5, { fz: -1, open: true }), G.guardSpawn('huangjia', full, A[0], A[1] - 5, { fz: 1, open: true })];
    let best = null;
    for (let k = 0; k < 8; k++) {
      G.step(10);
      const r = G.guards(), rr = G.render(true), cs = G.census(), tells = r.list.filter((u) => u.alive && u.tellStaged).length;
      const seen = r.list.filter((u) => u.seen).length, counts = Object.values(r.draw).reduce((a, d) => a + d.count, 0);
      const row = { calls: rr.calls, tris: rr.tris, programs: rr.programs, geoms: rr.geoms, tells, seen, counts, alive: r.n, extra: rr.calls - empty.calls - tells, batches: rr.crowd, rigs: rr.rigs, fx: rr.fx,
        tellsDrawn: cs.tells, other: rr.calls - cs.tells - rr.crowd - rr.rigs - rr.fx, diff: Object.keys(Object.assign({}, cs.other, ec.other)).filter((k) => cs.other[k] !== ec.other[k]).map((k) => k + ':' + (ec.other[k] || 0) + '>' + (cs.other[k] || 0)) };
      if (!best || row.calls > best.calls) best = row;
    }
    o.best = best; o.empty = { calls: empty.calls, tris: empty.tris, crowd: empty.crowd, rigs: empty.rigs, fx: empty.fx, tells: ec.tells, other: empty.calls - ec.tells - empty.crowd - empty.rigs - empty.fx };
    const r = G.guards(); r.list.forEach((u, i) => { if (u.alive) G.guardStrike(-1, i, 1000, false); });
    G.step(1); const after = G.render(true), ra = G.guards();
    o.after = { n: ra.n, staged: Object.values(ra.draw).filter((d) => d.staged).length, tells: ra.list.filter((u) => u.tellStaged).length, geoms: after.geoms, programs: after.programs };
    G.reset(); return o;
  });
  check('306 budget two full squads: calls<500, tris<500k, every draw beyond tells, crowd batches, rigs and cards equals the empty scene for 24 instanced guards, all seen drawn, no shader compile, geometry flat; none staged after',
    !!d306 && d306.q.every((q) => q >= 0) && d306.best.calls < 500 && d306.best.tris < 500000 && d306.best.batches > 0 && d306.empty.crowd === 0 && d306.best.other === d306.empty.other && d306.best.alive === 24 && d306.best.counts === d306.best.seen
    && d306.best.seen === 24 && d306.best.programs === base.programs && d306.best.geoms === base.geoms && d306.after.n === 0 && d306.after.staged === 0 && d306.after.tells === 0
    && d306.after.programs === base.programs && d306.after.geoms === base.geoms, JSON.stringify(d306));

  // 307 Royal Rumble untouched: a whole bot match spawns no guard and stages no guard mesh; a new run and the wake clear live squads.
  const d307 = await g(() => {
    const G = __game, C = G.config, o = {}; const { S } = __gs(C.BOTS.count);
    let mx = 0, staged = false;
    for (let n = 0; n < 60 / C.STEP; n++) { G.step(1); if (n % 60 === 0) { const r = G.guards(); mx = Math.max(mx, r.n); staged = staged || Object.values(r.draw).some((d) => d.staged); } }
    o.match = { mx, staged };
    __gs(0); G.guardSpawn('huangjia', ['wz', 'zu', 'nu'], S[0], S[1], { fz: -1 }); G.step(5); G.render(true); G.reset();
    let r = G.guards(); o.reset = { n: r.n, staged: Object.values(r.draw).some((d) => d.staged), tells: r.list.some((u) => u.tellStaged), squads: r.squads.some((s) => s.on) };
    __gs(0); G.guardSpawn('huangjia', ['wz', 'zu', 'nu'], S[0], S[1], { fz: -1 }); G.step(5); G.render(true); G.startHunt(); G.render(true);
    r = G.guards(); o.wake = { n: r.n, staged: Object.values(r.draw).some((d) => d.staged), tells: r.list.some((u) => u.tellStaged), squads: r.squads.some((s) => s.on) };
    G.setBots(0); G.reset(); return o;
  });
  check('307 Royal Rumble spawns no guard (60 s bot match); a new run and the wake clear squads, meshes and tells',
    !!d307 && d307.match.mx === 0 && !d307.match.staged && Object.values(d307.reset).every((v) => !v) && Object.values(d307.wake).every((v) => !v), JSON.stringify(d307));

  // 308 Factions: a squad hits units of another faction, never its own; a faction not hostile to suits leaves the player alone (ticket 07 adds the 反贼 this way).
  const d308 = await g(() => {
    const G = __game, C = G.config, o = {}; const { FAR } = __gs(0);
    C.GUARD.factions.test = { foeSuits: false };
    try {
      G.teleport(FAR[0], FAR[1]);
      const a = G.guardSpawn('huangjia', ['zu', 'zu', 'zu'], -7, 0, { fz: 1 }), b = G.guardSpawn('huangjia', ['zu', 'zu', 'zu'], -7, 5, { fz: -1 });
      G.guardFaction(b, 'test');
      const ia = [], ib = []; G.guards().list.forEach((u, i) => { if (u.alive) (u.sq === a ? ia : ib).push(i); });
      // Only squad A attacks (B's moves held back): any damage on B is A hitting the other faction; A stays whole (it never hits its own).
      G.guards().list.forEach((u, i) => { if (u.alive && u.sq === b) G.guardSet(i, { gcd: 1e9 }); });
      for (let n = 0; n < 600; n++) G.step(1);
      const r = G.guards();
      o.hurtA = ia.filter((i) => r.list[i].hp < r.list[i].max).length; o.hurtB = ib.filter((i) => r.list[i].hp < r.list[i].max).length;
      // The test faction ignores the player standing next to it.
      __gs(0); G.teleport(-7, 2);
      const c = G.guardSpawn('huangjia', ['zu', 'zu'], -7, 4, { fz: -1 }); G.guardFaction(c, 'test');
      for (let n = 0; n < 300; n++) G.step(1);
      o.playerHp = G.state().hp; o.tgt = G.guards().list.filter((u) => u.alive).map((u) => u.tgt);
    } finally { delete C.GUARD.factions.test; G.reset(); }
    return o;
  });
  check('308 guard factions: a squad hits the other faction and never its own; a faction not hostile to suits leaves the player alone',
    !!d308 && d308.hurtA === 0 && d308.hurtB > 0 && d308.playerHp === 100 && d308.tgt.every((t) => t !== 'P'), JSON.stringify(d308));
}
