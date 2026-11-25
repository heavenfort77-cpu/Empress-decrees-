// 反贼 rebel checks (Burning Palace ticket 07), numbers 900+. Called from tests/run.mjs with its page helper g, check() and the load-time render (base).
// Map as the guard checks: the player at A in the south centre courtyard (C2); squads at S, 10 m north; FAR = 28 m away (outside aggro).
export async function fanzeiChecks(g, check, base) {
  const SETUP = () => {
    window.__fs = (bots) => {
      const G = __game; G.setSeed(12345); G.setBots(bots || 0); G.reset(); G.teleport(-7, -6); return { A: [-7, -6], S: [-7, 4], FAR: [5, -22] };
    };
  };
  await g(SETUP);

  // 900 Spawn: the 反贼 faction spawns only its own four types (and the 皇家 guard none of them); one 渠帅 leads; 力士 take the squad's school
  // (its bootleg move and colour); 死士 start lurking (yellow tell), 符水道人 have the green tell; pools fixed; the squad cap; the switch; the drawn school is seeded.
  const d900 = await g(() => {
    const G = __game, C = G.config, o = {}; const { S } = __fs(0);
    o.pool = G.guards().pool;
    const q = G.guardSpawn('fanzei', ['qs', 'ls', 'ls', 'ls', 'ls', 'ls', 'fs', 'ss', 'ss', 'zu', 'wz'], S[0], S[1], { fz: -1, school: 'mo' });
    const r = G.guards(), f = G.fz(), mine = r.list.map((u, i) => [u, i]).filter(([u]) => u.alive && u.sq === q);
    o.q = q; o.n = mine.length; o.types = mine.map(([u]) => u.type).sort().join(',');
    o.lead = r.list[r.squads[q].lead] ? r.list[r.squads[q].lead].type : ''; o.broken = r.squads[q].broken; o.school = f.squads[q].school;
    o.ls = mine.filter(([u]) => u.type === 'ls').every(([, i]) => f.list[i].atk === 'bl_mo' && f.list[i].col === f.cols[3]);
    o.ss = mine.filter(([u]) => u.type === 'ss').every(([, i]) => f.list[i].hid && f.list[i].yellow);
    o.fs = mine.filter(([u]) => u.type === 'fs').every(([, i]) => f.list[i].green && !f.list[i].hid);
    o.wrongA = G.guardSpawn('fanzei', ['zu', 'wz', 'dun'], S[0], S[1] - 3); o.wrongB = G.guardSpawn('huangjia', ['ls', 'qs', 'ss', 'fs'], S[0], S[1] - 3);
    G.reset(); const big = G.guardSpawn('fanzei', ['qs', ...Array(14).fill('ls')], S[0], S[1], { school: 0 }); o.big = G.guards().squads[big].n;
    // The drawn school: the same on a replay of the seed, a valid index.
    const draw = () => { __fs(0); const id = G.guardSpawn('fanzei', ['qs', 'ls'], S[0], S[1]); return G.fz().squads[id].school; };
    o.draw = [draw(), draw()];
    C.FANZEI_ON = false;
    try { __fs(0); o.off = G.guardSpawn('fanzei', ['qs', 'ls'], S[0], S[1]); o.offGuard = G.guardSpawn('huangjia', ['wz', 'zu'], S[0], S[1]); } finally { C.FANZEI_ON = true; G.reset(); }
    return o;
  });
  check('900 反贼 spawn: own four types only (皇家 none of them); 渠帅 leads; 力士 bootleg move and school colour; 死士 lurk (yellow), 符水 green; pools; cap 12; seeded school; switch',
    !!d900 && JSON.stringify({ ls: d900.pool.ls, fs: d900.pool.fs, ss: d900.pool.ss, qs: d900.pool.qs }) === JSON.stringify({ ls: 12, fs: 2, ss: 4, qs: 2 })
    && d900.q >= 0 && d900.n === 9 && d900.types === 'fs,ls,ls,ls,ls,ls,qs,ss,ss' && d900.lead === 'qs' && !d900.broken && d900.school === 3 && d900.ls && d900.ss && d900.fs
    && d900.wrongA === -1 && d900.wrongB === -1 && d900.big === 12 && d900.draw[0] === d900.draw[1] && d900.draw[0] >= 0 && d900.draw[0] < 9 && d900.off === -1 && d900.offGuard >= 0,
    JSON.stringify(d900));

  // 901 力士 bootleg moves, one per school: its tell (red, its shape) for the whole windup, longer than any 皇家 guard move's (>= 0.8 s), then exactly its damage on the player.
  const d901 = await g(() => {
    const G = __game, C = G.config, GM = C.GUARD.moves, STEP = C.STEP, out = {};
    out.guardMax = Math.max(...['thrust', 'shove', 'cut'].map((k) => GM[k].windup));
    for (const k of C.SCHOOLS) {
      const { A } = __fs(0), m = GM['bl_' + k];
      const dist = m.shape === 'mark' ? (m.min + m.max) / 2 : m.shape === 'circle' ? 3 : 3.5;
      const q = G.guardSpawn('fanzei', ['ls'], A[0], A[1] + dist, { fz: -1, school: k });
      const o = { q, shape: m.shape, windup: m.windup, dmg: m.dmg, tell: null, hp: 100, hitAt: -1 };
      for (let n = 0; n < 15 / STEP; n++) {
        G.step(1);
        const r = G.guards(), s = G.state();
        if (!o.tell && r.tells.length) { const tl = r.tells[0]; o.tell = { shape: tl.shape, shown: tl.shown, red: tl.red, move: tl.move }; }
        if (s.hp < 100) { o.hp = s.hp; o.hitAt = n; o.minTell = r.minTell; break; }
      }
      out[k] = o;
    }
    G.reset(); return out;
  });
  const ok901 = !!d901 && ['ru', 'dao', 'fa', 'mo', 'yinyang', 'za', 'ming', 'zongheng', 'nong'].every((k) => {
    const o = d901[k];
    return o && o.q >= 0 && o.tell && o.tell.shape === o.shape && o.tell.shown && o.tell.red && o.tell.move === 'bl_' + k && o.hitAt >= 0
      && o.windup >= 0.8 && o.windup > d901.guardMax && Math.abs(100 - o.hp - o.dmg) < 1e-6 && o.minTell >= o.windup - 0.02;
  });
  check('901 力士 bootleg moves (9 schools): red tell of its shape for the whole windup (>= 0.8 s, longer than the 皇家 foot moves), then exactly its damage', ok901, JSON.stringify(d901));

  // 902 Bootleg 甲 stalls: after stallN moves the next waits cd + stallS (the others: cd); one stall counted.
  const d902 = await g(() => {
    const G = __game, C = G.config, F = C.FANZEI, m = C.GUARD.moves.bl_za, STEP = C.STEP, o = { starts: [] }; const { A } = __fs(0);
    G.guardSpawn('fanzei', ['ls'], A[0], A[1] + 3.5, { fz: -1, school: 'za' });
    let prev = 0;
    for (let n = 0; n < 40 / STEP && o.starts.length < F.stallN + 2; n++) {
      G.setHp(100); G.step(1);
      const k = G.guards().tells.length; if (k && !prev) o.starts.push(+(n * STEP).toFixed(3)); prev = k;
    }
    o.gaps = o.starts.slice(1).map((t, i) => +(t - o.starts[i]).toFixed(3)); o.stalls = G.fz().stalls; o.cd = m.cd; o.stallS = F.stallS; o.N = F.stallN;
    G.reset(); return o;
  });
  check('902 bootleg 甲 stalls: after stallN moves the next waits cd + stallS (others about cd); a stall counted',
    !!d902 && d902.gaps.length >= d902.N && d902.gaps.slice(0, d902.N - 1).every((t) => t < d902.cd + 1) && d902.gaps[d902.N - 1] >= d902.cd + d902.stallS - 0.05 && d902.stalls >= 1,
    JSON.stringify(d902));

  // 903 符水道人: a hurt 力士 of its squad is mended by the talisman's heal after a green tell (at the hurt one); a hurt 皇家 卒 beside it is not; no damage dealt.
  const d903 = await g(() => {
    const G = __game, C = G.config, T = C.GUARD.moves.talisman, o = {}; const { FAR } = __fs(0);
    G.teleport(FAR[0], FAR[1]);
    const q = G.guardSpawn('fanzei', ['qs', 'ls', 'fs'], -7, 4, { fz: -1, school: 'ru' }), h = G.guardSpawn('huangjia', ['zu'], -6, 4.5, { fz: 1 });
    const r = G.guards(), li = r.list.findIndex((u) => u.alive && u.sq === q && u.type === 'ls'), zi = r.list.findIndex((u) => u.alive && u.sq === h);
    r.list.forEach((u, i) => { if (u.alive && u.type !== 'fs') G.guardSet(i, { gcd: 1e9, slowT: 1e9, slowK: 1 }); });
    G.guardSet(li, { hp: 4 }); G.guardSet(zi, { hp: 4 });
    o.tell = null;
    for (let n = 0; n < 300; n++) {
      G.step(1);
      const rr = G.guards(), t = rr.tells.find((x) => x.type === 'fs');
      if (t && !o.tell) { const ff = G.fz(); o.tell = { shape: t.shape, shown: t.shown, green: ff.list[t.i].green, atHurt: Math.hypot(t.x - rr.list[li].x, t.z - rr.list[li].z) < 0.5 }; }
      if (rr.list[li].hp > 4) break;
    }
    const rr = G.guards(); o.ls = rr.list[li].hp; o.zu = rr.list[zi].hp; o.heals = G.fz().heals; o.want = Math.min(4 + T.heal, C.GUARD.types.ls.hp); o.playerHp = G.state().hp;
    G.reset(); return o;
  });
  check('903 符水道人 mends a hurt ally (heal after a green tell at it), never a 皇家 unit beside it',
    !!d903 && !!d903.tell && d903.tell.shape === 'mark' && d903.tell.shown && d903.tell.green && d903.tell.atHurt && Math.abs(d903.ls - d903.want) < 1e-6 && d903.zu === 4 && d903.heals >= 1 && d903.playerHp === 100,
    JSON.stringify(d903));

  // 904 死士: lurks unseen (not drawn, not seen by the player) until its prey is within lurkR, then shows; it goes for the run leader (a bot) over the nearer
  // player, with a yellow glint (its lunge windup, >= 0.4 s; a hit, if the bot does not dodge, only after it); with no leader, the player.
  const d904 = await g(() => {
    const G = __game, C = G.config, F = C.FANZEI, STEP = C.STEP, o = {};
    // Part 1: unseen at 9 m (outside lurkR); shown at 6 m.
    let { A } = __fs(0);
    const q = G.guardSpawn('fanzei', ['ss'], A[0], A[1] + 9, { fz: -1 });
    let r = G.guards(); const si = r.list.findIndex((u) => u.alive && u.sq === q), sx = r.list[si].x, sz = r.list[si].z;
    G.teleport(sx, sz - 9); G.step(60); r = G.guards();
    o.far = { hid: G.fz().list[si].hid, seen: r.list[si].seen, count: r.draw.ss.count, reveals: G.fz().reveals, st: r.list[si].st };
    G.teleport(sx, sz - 6); G.step(1); r = G.guards();
    o.near = { hid: G.fz().list[si].hid, seen: r.list[si].seen, reveals: G.fz().reveals };
    // Part 2: a bot leads; the player is nearer. The 死士 shows and lunges at the bot.
    ({ A } = __fs(1));
    G.placeholderKit(0);
    const q2 = G.guardSpawn('fanzei', ['ss'], A[0], A[1] + 10, { fz: -1 });
    r = G.guards(); const s2 = r.list.findIndex((u) => u.alive && u.sq === q2), ux = r.list[s2].x, uz = r.list[s2].z;
    G.teleport(ux - 4.5, uz); G.placeBot(0, ux + 6, uz); G.fzLead(0);
    o.lead = G.fz().leader; o.botTgt0 = G.bots().list[0].tgt;
    const bhp0 = G.bots().list[0].hp; o.tell = null; o.botHitAt = -1;
    for (let n = 0; n < 6 / STEP; n++) {
      G.step(1);
      const rr = G.guards(), t = rr.tells.find((x) => x.i === s2), u = rr.list[s2];
      if (t && !o.tell) { const b = G.bots().list[0], ff = G.fz(); o.tell = { at: n, fx: u.fx, toBot: ((b.x - u.x) * u.fx + (b.z - u.z) * u.fz) / Math.hypot(b.x - u.x, b.z - u.z), yellow: ff.list[s2].yellow, shown: t.shown, windup: t.windup, tgt: u.tgt }; }
      if (o.tell && G.bots().list[0].hp < bhp0) { o.botHitAt = n; break; }
    }
    o.playerHp = G.state().hp; o.reveals = G.fz().reveals;
    // Part 3: no leader: the player is its prey; the glint lasts its windup before the hit.
    ({ A } = __fs(0));
    const q3 = G.guardSpawn('fanzei', ['ss'], A[0], A[1] + 10, { fz: -1 });
    r = G.guards(); const s3 = r.list.findIndex((u) => u.alive && u.sq === q3);
    G.teleport(r.list[s3].x - 5, r.list[s3].z);
    let n3 = 0; for (; n3 < 6 / STEP && G.state().hp >= 100; n3++) G.step(1);
    o.p3 = { hp: G.state().hp, minTell: G.guards().minTell, windup: C.GUARD.moves.lunge.windup, dmg: C.GUARD.moves.lunge.dmg };
    G.setBots(0); G.reset(); return o;
  });
  check('904 死士 lurks unseen (not drawn, not seen) outside lurkR, shows inside it; lunges at the bot leader over the nearer player (yellow glint >= 0.4 s first); no leader: the player',
    !!d904 && d904.far.hid && !d904.far.seen && d904.far.count === 0 && d904.far.reveals === 0 && !d904.near.hid && d904.near.seen && d904.near.reveals === 1
    && d904.lead === 'b0' && !!d904.tell && d904.tell.yellow && d904.tell.shown && d904.tell.toBot > 0.9 && d904.tell.tgt === 'b0' && d904.tell.windup >= 0.4
    && (d904.botHitAt < 0 || (d904.botHitAt - d904.tell.at) * (1 / 60) >= d904.tell.windup - 0.02) && d904.playerHp === 100
    && Math.abs(100 - d904.p3.hp - d904.p3.dmg) < 1e-6 && d904.p3.minTell >= d904.p3.windup - 0.02 && d904.p3.minTell >= 0.4,
    JSON.stringify(d904));

  // 905 渠帅: killing it breaks the squad and gives the killer its school's bootleg charge (note, charge and health of its type, no 伍长 boon);
  // the F button shows its name; F casts it once (yellow tell for the windup, then chargeK x the bootleg damage); then the button hides.
  const d905 = await g(() => {
    const G = __game, C = G.config, F = C.FANZEI, STEP = C.STEP, o = {}; const { FAR } = __fs(0);
    G.teleport(FAR[0], FAR[1]); G.setHp(50); G.setCharge(-1, 0);
    const q = G.guardSpawn('fanzei', ['qs', 'ls', 'ls', 'ls'], -7, 4, { fz: -1, school: 'yinyang' });
    let r = G.guards(); const qi = r.squads[q].lead;
    r.list.forEach((u, i) => { if (u.alive && u.sq === q) G.guardSet(i, { gcd: 1e9 }); });
    const bT0 = r.player.bT[C.GUARD.leaderBoon.i];
    G.guardStrike(-1, qi, 1000, false);
    const rv = G.royale(), ch = G.chargeOf(-1), hp0 = G.state().hp; G.step(1);
    r = G.guards(); let f = G.fz();
    o.kill = { broken: r.squads[q].broken, n: f.suits[0].n, sk: f.suits[0].sk, charges: f.charges, ch, hp: hp0, bT: r.player.bT[C.GUARD.leaderBoon.i] - bT0,
      voice: rv.voice, rule: rv.rule, btn: f.btn };
    o.wantCh = C.GUARD.types.qs.ult; o.wantHp = 50 + C.GUARD.types.qs.heal;
    // Cast it at the one 力士 left, 7 m away and held still (the 阳 mark reaches 9 m): the tell for the whole windup, then chargeK x the bootleg damage.
    const li = r.list.findIndex((u) => u.alive && u.sq === q && u.type === 'ls'), L = r.list[li];
    r.list.forEach((u, i) => { if (u.alive && u.sq === q && i !== li) G.guardStrike(-1, i, 1000, false); });
    G.guardSet(li, { hp: 100, maxHp: 100, slowT: 1e9, slowK: 1 });
    G.teleport(L.x, L.z - 7); G.step(1);
    G.fzKey(); f = G.fz();
    o.cast = { casts: f.casts, n: f.suits[0].n, zm: f.suits[0].zm, copy: f.suits[0].copy };
    let n = 0, at = -1; const hp = G.guards().list[li].hp;
    for (; n < 3 / STEP; n++) { G.step(1); if (G.guards().list[li].hp < hp) { at = n + 1; break; } }
    o.hit = { at, t: at * STEP, dmg: hp - G.guards().list[li].hp, want: C.GUARD.moves.bl_yinyang.dmg * F.chargeK, windup: C.GUARD.moves.bl_yinyang.windup };
    G.step(1); f = G.fz(); o.after = { btn: f.btn, again: G.fzCast(-1, L.x, L.z) };
    G.reset(); return o;
  });
  check('905 渠帅 down: squad broken, killer gets its school charge (note, charge, health, no boon); F button named; F casts once: yellow tell for the windup, then chargeK x damage; button hides',
    !!d905 && d905.kill.broken && d905.kill.n === 1 && d905.kill.sk === 'bl_yinyang' && d905.kill.charges === 1 && Math.abs(d905.kill.ch - d905.wantCh) < 1e-6
    && Math.abs(d905.kill.hp - d905.wantHp) < 1e-6 && d905.kill.bT === 0 && /渠帅/.test(d905.kill.rule) && d905.kill.voice.length > 0
    && d905.kill.btn.display === 'flex' && d905.kill.btn.label === 'Bootleg Yinyang'
    && d905.cast.casts === 1 && d905.cast.n === 0 && d905.cast.zm.on && d905.cast.zm.yellow && d905.cast.zm.sk === 'bl_yinyang' && d905.cast.zm.t >= d905.hit.windup - 1e-6
    && d905.hit.at > 0 && d905.hit.t >= d905.hit.windup - 0.02 && Math.abs(d905.hit.dmg - d905.hit.want) < 1e-6 && d905.after.btn.display === 'none' && d905.after.again === false,
    JSON.stringify(d905));

  // 906 Three sides: a 反贼 squad and a 皇家 squad near each other fight (each side hurts the other); a bot holding a charge uses it in a fight.
  const d906 = await g(() => {
    const G = __game, C = G.config, STEP = C.STEP, o = {}; const { FAR } = __fs(0);
    G.teleport(FAR[0], FAR[1]);
    const a = G.guardSpawn('huangjia', ['wz', 'zu', 'zu', 'zu'], -7, 0, { fz: 1 }), b = G.guardSpawn('fanzei', ['qs', 'ls', 'ls', 'ls'], -7, 7, { fz: -1, school: 'ru' });
    for (let n = 0; n < 15 / STEP; n++) G.step(1);
    const r = G.guards();
    o.hurtA = r.list.filter((u) => u.sq === a && (u.hp < u.max || !u.alive)).length;
    o.hurtB = r.list.filter((u) => u.sq === b && (u.hp < u.max || !u.alive)).length;
    o.kills = r.kills; o.playerHp = G.state().hp;
    // A bot with a charge (法 dash line) hit by the player hits back with it first.
    __fs(1); G.placeholderKit(0);
    const bb = G.bots().list[0]; G.teleport(bb.x - 3, bb.z); G.fzCharge(0, 2);
    G.hitBy(-1, 0, 1);
    let n = 0; for (; n < 5 / STEP && G.fz().casts === 0; n++) G.step(1);
    const f = G.fz(); o.bot = { casts: f.casts, n: f.suits[1].n, copy: f.suits[1].copy, t: +(n * STEP).toFixed(2) };
    G.setBots(0); G.reset(); return o;
  });
  check('906 three sides: 反贼 and 皇家 squads hurt each other; a bot with a bootleg charge uses it in a fight',
    !!d906 && d906.hurtA > 0 && d906.hurtB > 0 && d906.bot.casts === 1 && d906.bot.n === 0 && d906.bot.copy === 'bl_fa', JSON.stringify(d906));

  // 907 Budget with a full 皇家 squad and a full 反贼 squad drawn: calls < 500, tris < 500k, one instanced call per crowd batch in view and nothing else
  // (prototype, game changed on purpose: models draw one batch per type x LOD x material x weapon, docs/HOOKS-17fgh.md section 4; calls beyond
  // tells = the batches the crowd reports drawn, exactly; before the models it was one box batch per type, <= 9),
  // no shader compile, geometry flat; after all are broken none stays in the scene.
  const d907 = await g(() => {
    const G = __game, o = {}; const { A } = __fs(0);
    const empty = G.render(true);
    o.q = [G.guardSpawn('huangjia', ['wz', 'dun', 'dun', 'zu', 'zu', 'zu', 'zu', 'zu', 'nu', 'nu', 'nu', 'che'], A[0], A[1] + 5, { fz: -1, open: true }),
      G.guardSpawn('fanzei', ['qs', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'ls', 'fs', 'ss', 'ss'], A[0], A[1] - 5, { fz: 1, school: 'nong' })];
    let best = null;
    for (let k = 0; k < 8; k++) {
      G.step(10);
      const r = G.guards(), rr = G.render(true), tells = r.list.filter((u) => u.alive && u.tellStaged).length + (G.fz().suits[0].zm.on ? 1 : 0);
      const seen = r.list.filter((u) => u.seen).length, counts = Object.values(r.draw).reduce((a, d) => a + d.count, 0);
      const row = { calls: rr.calls, tris: rr.tris, programs: rr.programs, geoms: rr.geoms, tells, seen, counts, alive: r.n, extra: rr.calls - empty.calls - tells, batches: G.chars().crowdDrawn };
      if (!best || row.calls > best.calls) best = row;
    }
    o.best = best;
    const r = G.guards(); r.list.forEach((u, i) => { if (u.alive) G.guardStrike(-1, i, 1000, false); });
    G.step(1); const after = G.render(true), ra = G.guards();
    o.after = { n: ra.n, staged: Object.values(ra.draw).filter((d) => d.staged).length, tells: ra.list.filter((u) => u.tellStaged).length, geoms: after.geoms, programs: after.programs };
    G.reset(); return o;
  });
  check('907 budget 皇家 + 反贼 full squads: calls<500, tris<500k, calls beyond tells = the crowd batches drawn, seen units drawn, no shader compile, geometry flat; none staged after',
    !!d907 && d907.q.every((q) => q >= 0) && d907.best.calls < 500 && d907.best.tris < 500000 && d907.best.batches > 0 && d907.best.extra === d907.best.batches && d907.best.counts === d907.best.seen && d907.best.alive >= 20
    && d907.best.programs === base.programs && d907.best.geoms === base.geoms && d907.after.n === 0 && d907.after.staged === 0 && d907.after.tells === 0
    && d907.after.programs === base.programs && d907.after.geoms === base.geoms, JSON.stringify(d907));

  // 908 A new run and the wake: no suit keeps a charge, no rebel lurks or counts uses, squads and meshes cleared, the button hidden; the drawn school replays.
  const d908 = await g(() => {
    const G = __game, o = {}; const { S } = __fs(0);
    const q = G.guardSpawn('fanzei', ['qs', 'ls', 'ss'], S[0], S[1], { fz: -1 }); o.s1 = G.fz().squads[q].school;
    G.fzCharge(-1, 4); G.step(30); G.render(true); o.before = G.fz().btn.display;
    G.reset(); G.step(1);
    let f = G.fz(), r = G.guards();
    o.reset = { n: f.suits.some((s) => s.n > 0 || s.sk), hid: f.list.some((u) => u.hid || u.uses), sq: r.squads.some((s) => s.on), staged: Object.values(r.draw).some((d) => d.staged), btn: f.btn.display === 'flex' };
    const q2 = G.guardSpawn('fanzei', ['qs', 'ls', 'ss'], S[0], S[1], { fz: -1 }); o.s2 = G.fz().squads[q2].school;
    G.fzCharge(-1, 4); G.step(5); G.startHunt(); G.render(true);
    f = G.fz(); r = G.guards();
    o.wake = { n: f.suits.some((s) => s.n > 0 || s.sk), hid: f.list.some((u) => u.hid), sq: r.squads.some((s) => s.on), staged: Object.values(r.draw).some((d) => d.staged) };
    G.reset(); return o;
  });
  check('908 new run and wake clear the rebels: no charges, no lurking or worn units, squads and meshes gone, button hidden; the drawn school replays per seed',
    !!d908 && d908.before === 'flex' && Object.values(d908.reset).every((v) => !v) && Object.values(d908.wake).every((v) => !v) && d908.s1 === d908.s2, JSON.stringify(d908));
}
