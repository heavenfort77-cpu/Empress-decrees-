// BP09B killable bronze giants checks (1100-1104; owner 24 Nov 15:41 "make them killable"): every side hurts an awake giant, a broken one
// collapses and lies there for the run (never acts again), her line and the breaker's charge, new run restores (docs/BURNING-PALACE.md "Palace pieces").
// Called from tests/run.mjs with its page-evaluate helper g and its check(name, ok, detail).
export async function bp09bChecks(g, check) {
  const tx = await g(() => __game.text);
  const C2 = await g(() => __game.config.PIECES2);

  // 1100 A suit's blows: a dormant giant takes nothing; the player's attack order hurts an awake one; the killing blow collapses it (fallS), gives the
  // player giant.charge, her line once (TEXT piece2_giant_down), frees its awake slot; its bar shows only while awake; it never acts again
  // (no tell, no hit on the player standing next to it for 10 s); shaders flat.
  const k0 = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(1);
    const base = G.render(true);
    G.giantWake();
    const s0 = G.pieces2State(), gi = s0.giants.find((x) => x.st === 1), dorm = s0.giants.find((x) => x.st === 0), i = gi.i;
    G.giantStrike(dorm.i, -1); o.dormHp = G.pieces2State().giants[dorm.i].hp;
    G.setHp(1000); G.teleport(gi.x, gi.z + 2.4); G.step(1);
    o.bars1 = G.pieces2State().nBars;
    G.giantAttack(i);
    for (let k = 0; k < 60 * 4; k++) { G.setHp(1000); G.step(1); }
    const s1 = G.pieces2State(); o.hpAfterOrder = s1.giants[i].hp; o.blow = s1.dmg.blow; o.max = s1.hpMax;
    // Last blows: the order goes on with the giant at 5 health and an empty meter; read the meter on the step before and on the step of the kill.
    G.giantSetHp(i, 5); G.setCharge(-1, 0); G.giantAttack(i);
    let before = 0, after = -1, n = 0;
    while (n < 60 * 6 && G.pieces2State().giants[i].st < 6) { before = G.chargeOf(-1); G.setHp(1000); G.step(1); n++; }
    after = G.chargeOf(-1);
    const s2 = G.pieces2State(), q2 = s2.giants[i];
    o.kill = { st: q2.st, hp: q2.hp, alive: q2.alive, seen: q2.seen, killer: q2.killer, kills: s2.kills, awake: s2.awake, gain: +(after - before).toFixed(3), bars: s2.nBars };
    let fallSteps = 0;
    while (fallSteps < 120 && G.pieces2State().giants[i].st === 6) { G.step(1); fallSteps++; }
    o.fallSteps = fallSteps; o.lying = G.pieces2State().giants[i].st;
    const hits0 = G.pieces2State().giants[i].hits, hp0 = G.state().hp; let tell = false, still = true;
    for (let k = 0; k < 60 * 10; k++) {
      G.step(1); const q = G.pieces2State().giants[i];
      if (q.ring || q.line) tell = true;
      still = still && q.st === 7;
    }
    const s3 = G.pieces2State();
    o.after = { st: s3.giants[i].st, hits: s3.giants[i].hits - hits0, lost: +(hp0 - G.state().hp).toFixed(1), tell, still, downNotes: s3.downNotes, vis: s3.giants[i].vis, bars: s3.nBars };
    o.rewake = G.giantWake(); o.awake2 = G.pieces2State().awake;
    const r = G.render(true); o.prog = [base.programs, r.programs]; o.geo = [base.geoms, r.geoms];
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1100 giants killable by a suit: dormant takes nothing; the player\'s order hurts an awake one; the kill collapses it (fallS), gives giant.charge, her line once, frees its slot; bar only while awake; never acts again; shaders flat',
    k0.dormHp === C2.giant.hp && k0.bars1 === 1 && k0.hpAfterOrder < k0.max && k0.blow > 0
    && k0.kill.st === 6 && k0.kill.hp === 0 && !k0.kill.alive && !k0.kill.seen && k0.kill.killer === 'P' && k0.kill.kills === 1 && k0.kill.awake === 0
    && k0.kill.gain >= C2.giant.charge && k0.kill.gain < C2.giant.charge + 1
    && k0.fallSteps >= Math.round(C2.giant.fallS * 60) - 2 && k0.fallSteps <= Math.round(C2.giant.fallS * 60) + 2 && k0.lying === 7
    && k0.after.st === 7 && k0.after.hits === 0 && k0.after.lost === 0 && !k0.after.tell && k0.after.still && k0.after.downNotes === 1 && k0.after.vis && k0.after.bars === 0
    && k0.rewake === true && k0.awake2 === 1 && k0.prog[0] === k0.prog[1] && k0.geo[0] === k0.geo[1] && typeof tx.piece2_giant_down === 'string' && tx.piece2_giant_down.length > 0,
    JSON.stringify(k0));

  // 1101 Bots: a bot that sees an awake giant (and no suit) takes it as a creature target; its basic attack hurts it; it dodges the giant's shown
  // slam once seen for its reaction time (inside the ring: danger; 12 m away: none).
  const b1 = await g(() => {
    const G = __game, o = { picks: 0, tries: 0 };
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(1);
    G.giantWake(); const gi = G.pieces2State().giants.find((x) => x.st === 1), i = gi.i;
    G.palPlaceBot(0, gi.x + 3, gi.z + 1.5); G.step(1);
    for (let k = 0; k < 20 && o.picks === 0; k++) { o.tries++; const d = G.botDecideNow(0); if (d.mode === 'creature' && d.giant === i) o.picks++; }
    const h0 = G.pieces2State().giants[i].hp; G.giantStrike(i, 0); o.botHit = +(h0 - G.pieces2State().giants[i].hp).toFixed(2);
    // A slam shown and seen for the reaction time: stand the player next to it, then ask the bot's dodge test.
    const gn = G.pieces2State().giants[i]; G.setHp(1000); G.teleport(gn.x, gn.z + 2.4);
    let q = null;
    for (let k = 0; k < 60 * 8 && !q; k++) { G.setHp(1000); G.step(1); const r = G.pieces2State().giants[i]; if (r.cur === 'slam' && r.ring && r.tellT >= 0.35) q = r; }
    o.slam = !!q;
    if (q) { o.inside = G.giantDanger(0, q.x + 1, q.z); o.outside = G.giantDanger(0, q.x + 12, q.z); }
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1101 bots: an awake giant in sight is a creature target; a bot\'s basic attack hurts it; bots dodge its shown slam (inside: danger, 12 m off: none)',
    b1.picks === 1 && b1.botHit > 0 && b1.slam && b1.inside === true && b1.outside === false, JSON.stringify(b1));

  // 1102 The 皇家 guard and the 反贼 hurt an awake giant with their moves and take it as a foe (guards act in the palace only once ticket 03 lists
  // the phase: the check adds it for the test and takes it out again).
  const gd = await g(() => {
    const G = __game, o = {}, ph = G.config.GUARD.phases;
    const run = (f, list) => {
      G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(1);
      ph.push('palace');
      G.giantWake(); const gi = G.pieces2State().giants.find((x) => x.st === 1), i = gi.i;
      const id = G.guardSpawn(f, list, gi.x, gi.z + 2, { fx: 0, fz: -1 });
      const d0 = G.pieces2State().dmg.guard; let k = 0;
      while (k < 60 * 6 && G.pieces2State().dmg.guard === d0) { G.giantSetHp(i, G.config.PIECES2.giant.hp); G.step(1); k++; }
      const r = { id, dmg: +(G.pieces2State().dmg.guard - d0).toFixed(2), steps: k, blow: G.pieces2State().dmg.blow };
      ph.splice(ph.indexOf('palace'), 1);
      return r;
    };
    o.huangjia = run('huangjia', ['zu', 'zu', 'zu']);
    o.fanzei = run('fanzei', ['qs', 'ls', 'ls']);
    o.phases = ph.join(',');
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1102 the 皇家 guard and the 反贼 hurt an awake giant (their moves; it is their foe); guard phases restored after the check',
    gd.huangjia.id >= 0 && gd.huangjia.dmg > 0 && gd.fanzei.id >= 0 && gd.fanzei.dmg > 0 && gd.phases === 'royale', JSON.stringify(gd));

  // 1103 Pieces hurt an awake giant: a burning mercury channel (while it stands in it) and a vat's splash (vat.giantDmg, a vat broken by the player).
  const pc = await g(() => {
    const G = __game, o = {};
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(1);
    G.giantWake(); const gi = G.pieces2State().giants.find((x) => x.st === 1), i = gi.i;
    // Mercury: the bridge's first channel (BP08 box placement: x 12-14, z -32..-24 from the palace origin); held there in its waking tell.
    const org = G.config.PALACE.origin, mx = org[0] + 13, mz = org[1] - 28;
    let k = 0; const d0 = G.pieces2State().dmg.piece;
    while (k < 60 * 6 && G.pieces2State().dmg.piece === d0) { G.giantPlace(i, mx, mz); G.step(1); k++; }
    o.merc = { dmg: +(G.pieces2State().dmg.piece - d0).toFixed(2), steps: k };
    // Vat: the giant beside the court's vat (index 1), the player breaks the vat by an attack order.
    G.reset(); G.step(1); G.giantWake(); const g2 = G.pieces2State().giants.find((x) => x.st === 1);
    const v = G.pieces2State().vats[1];
    G.setHp(1000); G.teleport(v.x + 1.8, v.z); G.step(1); G.vatAttack(1);
    let n = 0; const v0 = G.pieces2State().dmg.vat;
    while (n < 60 * 6 && G.pieces2State().vats[1].st < 2) { G.giantPlace(g2.i, v.x - 1.5, v.z); G.setHp(1000); G.step(1); n++; }
    G.step(1);
    o.vat = { st: G.pieces2State().vats[1].st, dmg: +(G.pieces2State().dmg.vat - v0).toFixed(2), hp: G.pieces2State().giants[g2.i].hp };
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1103 pieces hurt an awake giant: a burning mercury channel it stands in, and a vat\'s splash (vat.giantDmg)',
    pc.merc.dmg > 0 && pc.vat.st >= 2 && pc.vat.dmg === C2.vat.giantDmg && pc.vat.hp === C2.giant.hp - C2.vat.giantDmg, JSON.stringify(pc));

  // 1104 New run in the same page (twice) after a kill: every giant dormant at home with full health, none lying, kills and damage counters zero,
  // no bar drawn; a fresh wake gives a full-health giant again.
  const nr = await g(() => {
    const G = __game, o = { runs: [] };
    G.setSeed(12345); G.setMode('palace'); G.pieces2(true, true); G.reset(); G.step(1);
    G.giantWake(); const gi = G.pieces2State().giants.find((x) => x.st === 1);
    G.giantSetHp(gi.i, 1); G.giantStrike(gi.i, -1); for (let k = 0; k < 60; k++) G.step(1);
    o.before = { st: G.pieces2State().giants[gi.i].st, kills: G.pieces2State().kills };
    for (let r = 0; r < 2; r++) {
      G.reset(); G.step(1); const s = G.pieces2State();
      o.runs.push({ home: s.giants.every((x) => x.st === 0 && x.hp === s.hpMax && !x.alive && !x.seen && x.fallT === 0 && x.x === x.hx && x.z === x.hz), kills: s.kills, downNotes: s.downNotes,
        dmg: s.dmg.blow + s.dmg.guard + s.dmg.piece + s.dmg.vat, bars: s.nBars });
    }
    G.giantWake(); o.fresh = G.pieces2State().giants.find((x) => x.st === 1).hp;
    G.setMode('rumble'); G.reset(); return o;
  });
  check('1104 giants new run (twice) after a kill: all dormant at home with full health, none lying, counters zero, no bar; a fresh wake has full health',
    nr.before.st >= 6 && nr.before.kills === 1 && nr.runs.every((r) => r.home && r.kills === 0 && r.downNotes === 0 && r.dmg === 0 && r.bars === 0) && nr.fresh === C2.giant.hp,
    JSON.stringify(nr));
}
