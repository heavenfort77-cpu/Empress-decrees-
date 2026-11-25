// Event table for fxEvent (PREP-AV 25 Nov): every attack, tell, hit and state of docs/VFX.md "Effect map" (86 items) joined to the
// sounds of docs/AUDIO.md. One item per game move or piece; each item has phases, each phase one or two painted cards and one sound.
// Event name = '<item>:<phase>' (load-time strings; call sites use literals or the precomputed ids below, never concatenate per event).
//
// Item spec: 'row | phase card [size] [card2 [size]] [~sound[@rate]] | ...'
//   row    : a ramp row of assets/vfx/vfx.json; '*row' = the caller's school/row argument wins, row is the default when none is given.
//   phase  : tell (windup, held for opts.hold or hN s), rel (release, the move fires), hit (lands on a target: x, z = the target),
//            whiff (miss), trail (flies: move it with fxMove), state (held state: aura, shield, ring, smoke at a spot), end (it ends).
//   card   : slash impact bolt thrust shield aura heal burst smoke strip ring crack mark, or '-' (sound only); '+' joins a second card.
//   size   : sN scale (upright; negative mirrors), rN radius m (ring, mark, crack, burst), lN length m and wN width m (strip, thrust),
//            hN hold s (tells: the move's windup; states: duration; 0 = loop until fxKill). opts.a overrides r / l, opts.b overrides w,
//            opts.hold overrides h (pass the CONFIG windup or duration: the card then shows for exactly that long).
//   sound  : a name in SOUNDS (src/audio/sound.js); @rate = playback rate (heavier hit 0.8, bootleg copy 0.85). opts.rate overrides.
export const FX_ITEMS = {
  // ---- suits (CONFIG.KITS; ramp = the caster's school row) ----
  ru_atk: '*ru | rel slash s1 ~ru_atk | trail bolt s1 ~ru_atk | hit impact s1 ~ru_hit | whiff - ~ru_whiff',
  ru_q: '*ru | rel thrust l5 w1.8 ~ru_q | state smoke s1 | hit impact s1 ~ru_hit@0.8 | whiff - ~ru_whiff',
  ru_w: '*ru | rel thrust l8 w1.2 ~ru_w | hit impact s1 ~ru_hit@0.8 | state aura s1 h4 | whiff - ~ru_whiff',
  ru_r: '*ru | tell ring r4.5 h0.6 ~ru_r | rel burst r4.5 | hit impact s1 ~ru_hit',
  dao_atk: '*dao | rel slash s-0.8 ~dao_atk | hit impact s1 ~dao_hit | whiff - ~dao_whiff',
  dao_q: '*dao | state shield s1 h0.8 ~dao_q | hit burst s0.5 ~dao_counter',
  dao_w: '*dao | state shield s1 h0.8 ~dao_w | rel thrust l8 | hit - ~dao_counter',
  dao_r: '*dao | state aura s1 h8 ~dao_r',
  dao_p: '*dao | state smoke s0.6',
  fa_atk: '*fa | rel slash s1 ~fa_atk | hit impact s1 ~fa_hit | whiff - ~fa_whiff',
  fa_q: '*fa | rel thrust l5 ~fa_q | hit burst r1.6 ~fa_hit@0.8 | whiff - ~fa_whiff',
  fa_w: '*fa | state smoke s0.8 ~fa_w | hit ring r0.8 h3',
  fa_r: '*fa | state ring r6 h6 + aura s1 h6 ~fa_r',
  mo_atk: '*mo | trail bolt s0.8 ~mo_atk | hit impact s1 ~mo_hit | whiff - ~mo_whiff',
  mo_q: '*mo | rel crack r2 ~mo_q | state smoke s1',
  mo_w: '*mo | tell mark r2.2 h0.6 ~mo_w_tell | rel burst r2.2 ~mo_w | hit impact s1 ~mo_hit@0.8 | whiff - ~mo_whiff',
  mo_r: '*mo | state shield s1 h8 ~mo_r | hit impact s1',
  yy_atk: '*yinyang | trail bolt s1 ~yy_atk | hit impact s1 ~yy_hit | whiff - ~yy_whiff',
  yy_q: '*yinyang | trail bolt s1.4 ~yy_q | hit burst r0.9 ~yy_hit@0.8 | whiff - ~yy_whiff',
  yy_w: '*yinyang | tell mark r2.5 h0.8 ~yy_w_tell | rel burst r2.5 ~yy_w | hit impact s1 ~yy_hit | whiff - ~yy_whiff',
  yy_r: '*yinyang | tell mark r5 h1 ~yy_r_tell | rel - ~yy_r | state ring r5 h3 | hit impact s1 ~yy_hit@1.2',
  za_atk: '*za | trail bolt s1 ~za_atk | hit impact s1 ~za_hit | whiff - ~za_whiff',
  za_q: '*za | rel thrust l8 w1.2 ~za_q | hit impact s1 ~za_hit@0.8 | state aura s1 h2 | whiff - ~za_whiff',
  za_w: '*za | rel smoke s0.8 ~za_w | state smoke s0.8',
  za_r: '*za | rel - ~za_r',
  ming_atk: '*ming | trail bolt s1 ~ming_atk | hit impact s1 ~ming_hit | whiff - ~ming_whiff',
  ming_q: '*ming | rel smoke s0.8 ~ming_q',
  ming_w: '*ming | tell strip l8 w1.2 h1 ~ming_w | rel thrust l8 | hit impact s1 ~ming_hit@0.8 | whiff - ~ming_whiff',
  ming_r: '*ming | tell strip l30 w1.4 h1 ~ming_r | rel thrust l30 | hit impact s1 ~ming_hit@0.8 | whiff - ~ming_whiff',
  zh_atk: '*zongheng | trail bolt s0.8 ~zh_atk | hit impact s1 ~zh_hit | whiff - ~zh_whiff',
  zh_q: '*zongheng | rel impact s1 ~zh_q | state aura s1 h5 | end burst s0.5 | hit - ~zh_hit | whiff - ~zh_whiff',
  zh_w: '*zongheng | rel smoke s0.8 ~zh_w | state smoke s0.8',
  zh_r: '*zongheng | state ring r6 h5 ~zh_r | hit impact s1 ~zh_hit',
  nong_atk: '*nong | rel slash s0.9 ~nong_atk | hit impact s1 ~nong_hit | whiff - ~nong_whiff',
  nong_q: '*nong | rel smoke s0.4 ~nong_q',
  nong_w: '*nong | rel thrust l5 ~nong_w | state strip l5 w1.6 h4 | hit impact s1 ~nong_hit | whiff - ~nong_whiff',
  nong_r: '*nong | tell ring r8 h0.4 ~nong_r | rel burst r3 | hit heal s1 ~nong_hit',
  nong_p: '*nong | hit heal s0.8',
  suit_break: '*ash | rel burst s1 | state smoke s1.2',
  // ---- Tiger Demon and its minions (CONFIG.APEX, MOVES, DEMON_ULT, PLATE; ramp apex; cubs pass opts.rate 1.15) ----
  apex_wake: 'apex | tell aura s1.6 h3 ~demon_wake | rel crack r3',
  claw: 'apex | tell ring r2.6 h0.45 ~demon_claw_tell | rel slash s1.3 ~demon_claw | hit impact s1 ~demon_hit',
  pounce: 'apex | tell strip l7.5 w2.2 h0.5 ~demon_pounce_tell | rel thrust l7.5 ~demon_pounce | hit impact s1 ~demon_hit | end crack r1.5',
  roar: 'apex | tell ring r6 h0.7 ~demon_roar_tell | rel burst r6 ~demon_roar | hit - ~p_slow',
  demon_ult: 'apex | tell aura s1.6 h0.8 ~demon_ult_tell | rel burst r3 ~demon_roar@1.2 | state aura s1.6 h8',
  bite: 'apex | tell ring r1.7 h0.4 ~cub_bite_tell | rel slash s0.6 ~cub_bite | hit impact s1 ~unit_hit',
  lunge: 'apex | tell strip l4.5 w1.4 h0.45 ~cub_lunge_tell | rel thrust l4.5 ~cub_lunge | hit impact s1 ~unit_hit',
  rend: 'apex | tell ring r1.9 h0.5 ~cub_rend_tell | rel slash s0.6 ~cub_rend | hit impact s0.5 ~p_bleed',
  flank: 'apex | tell mark r2.2 h0.6 ~cub_flank_tell | rel burst r2.2 ~cub_flank | hit impact s1 ~p_stun',
  howl: 'apex | tell ring r7.5 h0.7 ~cub_howl_tell | rel burst r7.5 ~cub_howl | hit - ~p_slow',
  plate: 'apex | trail bolt s1 | hit heal s0.8 ~plate_take',
  // ---- 皇家 guard and 反贼 rebels (CONFIG.GUARD.moves, FANZEI; rebels pass their variant row) ----
  g_thrust: 'guard | tell strip l2.6 w0.8 h0.5 ~g_thrust_tell | rel thrust l2.6 ~g_thrust | hit impact s1 ~unit_hit',
  g_volley: 'guard | tell mark r1.6 h0.8 ~g_volley_tell | rel burst r1.6 ~g_volley | trail bolt s1 | hit impact s1 ~unit_hit',
  g_shove: 'guard | tell ring r1.8 h0.5 ~g_shove_tell | rel burst r1.8 ~g_shove | hit impact s1 ~unit_hit',
  g_charge: 'guard | tell strip l10 w1.8 h0.9 ~g_charge_tell | rel thrust l10 ~g_charge | state smoke s1 | hit impact s1 ~demon_hit@1.3',
  g_cut: 'guard | tell strip l2.4 w1 h0.5 ~g_cut_tell | rel slash s0.9 ~g_cut | hit impact s1 ~unit_hit',
  g_buff: 'guard | state aura s1 h0',
  g_break: 'guard | rel burst s0.6 ~g_break | state smoke s1',
  g_block: 'guard | hit impact s0.8 + shield s1 h0.2',
  unit_break: '*guard | rel smoke s0.8 ~unit_break',
  r_talisman: '*rebel_olive | tell mark r2.5 h0.8 ~r_talisman_tell | rel - ~r_talisman | hit heal s1',
  r_lunge: '*rebel_umber | tell strip l7 w1 h0.6 + impact s0.6 ~r_lunge_tell | rel thrust l7 ~r_lunge | hit impact s1 ~unit_hit',
  r_cleave: '*rebel_madder | tell ring r2.2 h0.6 ~r_cleave_tell | rel slash s1 ~r_cleave | hit impact s1 ~unit_hit',
  bl_ru: '*rebel_olive | tell strip l5 w1.6 h0.8 ~r_bootleg_tell | rel thrust l5 ~ru_q@0.85 | hit impact s1 ~ru_hit@0.85',
  bl_dao: '*rebel_olive | tell ring r1.8 h0.8 ~r_bootleg_tell | rel burst r1.8 ~dao_w@0.85 | hit impact s1 ~dao_hit@0.85',
  bl_fa: '*rebel_olive | tell strip l5 w1.4 h0.8 ~r_bootleg_tell | rel thrust l5 ~fa_q@0.85 | hit impact s1 ~fa_hit@0.85',
  bl_mo: '*rebel_olive | tell mark r2 h1 ~r_bootleg_tell | rel burst r2 ~mo_w@0.85 | hit impact s1 ~mo_hit@0.85',
  bl_yinyang: '*rebel_olive | tell mark r2.2 h1 ~r_bootleg_tell | rel burst r2.2 ~yy_w@0.85 | hit impact s1 ~yy_hit@0.85',
  bl_za: '*rebel_olive | tell strip l7 w1 h0.8 ~r_bootleg_tell | rel thrust l7 ~za_q@0.85 | hit impact s1 ~za_hit@0.85',
  bl_ming: '*rebel_olive | tell strip l7 w1 h0.8 ~r_bootleg_tell | rel thrust l7 ~ming_w@0.85 | hit impact s1 ~ming_hit@0.85',
  bl_zongheng: '*rebel_olive | tell ring r2.4 h0.9 ~r_bootleg_tell | rel burst r2.4 ~zh_w@0.85 | hit impact s1 ~zh_hit@0.85',
  bl_nong: '*rebel_olive | tell strip l5 w1.6 h0.8 ~r_bootleg_tell | rel thrust l5 ~nong_w@0.85 | hit impact s1 ~nong_hit@0.85',
  r_stall: '*rebel_umber | rel impact s0.8 ~r_stall | state smoke s0.6',
  r_charge: '*ru | rel - ~plate_take@0.9',
  // ---- palace pieces, hazards, heals (CONFIG.STATUE, LION, PIECES, PIECES2, BURN, ALTAR, BOONS) ----
  statue: 'bronze | tell ring r6.5 h0.6 ~statue_tell | rel crack r6.5 ~statue_strike | hit burst s1',
  lion: 'bronze | tell ring r4 h0.6 ~lion_tell | rel crack r4 ~lion_strike | hit burst s1',
  giant_wake: 'bronze | tell aura s2.4 h2 ~giant_wake | state smoke s1.5',
  giant_slam: 'bronze | tell ring r4 h1 ~giant_slam_tell | rel crack r4 ~giant_slam | hit burst s1.5 | state smoke s1.5',
  // Owner 25 Nov: the sweep hits 2.5 m over 120 deg in front. No cone card exists: a strip 2.5 m deep and 4.33 m wide (the 120 deg chord)
  // covers the arc and shows only the front (HOOKS-17c open item: a cone card would match the hit shape exactly).
  giant_sweep: 'bronze | tell strip l2.5 w4.33 h1.2 ~giant_sweep_tell | rel slash s2.5 ~giant_sweep | hit impact s1',
  giant_fall: 'bronze | rel crack r3 ~giant_fall | state smoke s2',
  vat: 'water | tell ring r3.5 h0.5 ~vat_crack | rel burst r3.5 ~vat_splash | state smoke s1',
  burn_warn: 'ash | tell smoke s2 ~st_burn | state smoke s2',
  burn_fall: 'ash | rel crack r3 ~burn_fall | state smoke s2',
  mercury: 'ash | tell - ~merc_warn | rel - ~merc_on',
  ding: 'jade | state heal s1.2 h0 ~ding_heal',
  boon: 'jade | rel burst s0.6 ~boon | state heal s1 h0',
  boon_buff: 'bronze | state aura s1 h0',
  door: 'ash | rel - ~door_open | end - ~door_lock',
  // ---- the player and menus (sound only) ----
  p_hurt: 'ash | hit - ~p_hurt', p_bleed: 'ash | hit - ~p_bleed', p_slow: 'ash | hit - ~p_slow', p_stun: 'ash | hit - ~p_stun',
  p_marked: 'ash | tell - ~p_marked', p_break: 'ash | rel - ~p_break', ult_ready: 'ash | rel - ~ult_ready',
  ui_move: 'ash | rel - ~ui_move', ui_ok: 'ash | rel - ~ui_ok', ui_back: 'ash | rel - ~ui_back',
};

// Unit moves (beginMove / resolveMove share MOVES; guards and rebels share GUARD.moves joined with FANZEI.bootleg as 'bl_<school>').
// Move key -> item. Two tables because MOVES.lunge (cubs) and GUARD.moves.lunge (死士) share a key.
export const UNIT_ITEM = { claw: 'claw', pounce: 'pounce', roar: 'roar', bite: 'bite', lunge: 'lunge', rend: 'rend', flank: 'flank', howl: 'howl', ult: 'demon_ult' };
export const GUARD_ITEM = { thrust: 'g_thrust', volley: 'g_volley', shove: 'g_shove', charge: 'g_charge', cut: 'g_cut', talisman: 'r_talisman', lunge: 'r_lunge', cleave: 'r_cleave',
  bl_ru: 'bl_ru', bl_dao: 'bl_dao', bl_fa: 'bl_fa', bl_mo: 'bl_mo', bl_yinyang: 'bl_yinyang', bl_za: 'bl_za', bl_ming: 'bl_ming', bl_zongheng: 'bl_zongheng', bl_nong: 'bl_nong' };

// Her stingers (docs/AUDIO.md): TEXT voice key -> stinger. Keys not listed stay silent (small events play their own sound).
export const STINGER_OF = {
  voice_dec_dry: 'st_decree', voice_dec_nodash: 'st_decree', voice_dec_silence: 'st_decree', voice_dec_heights: 'st_decree', voice_dec_ult2x: 'st_decree',
  voice_kennel: 'st_decree', voice_guard_break: 'st_decree', voice_marked: 'st_decree', voice_silenced: 'st_decree', piece_voice_hb: 'st_decree',
  burn_voice: 'st_burn', voice_wave0: 'st_burn', voice_wave1: 'st_burn', voice_wave2: 'st_burn', voice_wave3: 'st_burn', voice_wave4: 'st_burn', voice_fell: 'st_burn',
  voice_bounty: 'st_bounty', voice_bounty_paid: 'st_bounty', fz_voice_charge: 'st_bounty', voice_plate: 'st_bounty', voice_plate_take: 'st_bounty',
  voice_wake: 'st_wake', voice_frenzy: 'st_wake', pal_voice_core: 'st_wake', voice_won: 'st_wake', voice_lost: 'st_wake', pal_voice_lost: 'st_wake',
  voice_died: 'st_wake', voice_royale_lost: 'st_wake',
};

export const PHASES = ['tell', 'rel', 'hit', 'whiff', 'trail', 'state', 'end'];

// Parse the table once at load. cardIdx = name -> card index (cards.idx), rowIdx = row name -> ramp row. Returns { ev: { name -> entry }, list }.
// entry: { item, phase, row, rowFixed, k1, sx1, sy1, r1, l1, w1, h1, k2, ..., snd, rate }; sizes are the card's own meanings (see the header).
export function parseFx(cardIdx, rowIdx) {
  const ev = {}, list = [], errs = [];
  for (const item of Object.keys(FX_ITEMS)) {
    const parts = FX_ITEMS[item].split('|').map((p) => p.trim());
    let row = parts[0], fixed = true;
    if (row[0] === '*') { fixed = false; row = row.slice(1); }
    if (!(row in rowIdx)) errs.push(item + ': row ' + row);
    for (let i = 1; i < parts.length; i++) {
      const tok = parts[i].split(/\s+/), phase = tok[0];
      if (PHASES.indexOf(phase) < 0) errs.push(item + ': phase ' + phase);
      const e = { name: item + ':' + phase, item, phase, row: rowIdx[row], rowName: row, rowFixed: fixed, cards: [], snd: '', rate: 1 };
      let cur = null;
      for (let j = 1; j < tok.length; j++) {
        const t = tok[j];
        if (t === '+') continue;
        if (t[0] === '~') { const [s, r] = t.slice(1).split('@'); e.snd = s; e.rate = r ? +r : 1; continue; }
        if (/^[srlwh]-?[\d.]+$/.test(t)) { if (cur) cur[t[0]] = +t.slice(1); else errs.push(item + ': size before card ' + t); continue; }
        if (t === '-') { cur = null; continue; }
        if (!(t in cardIdx)) { errs.push(item + ':' + phase + ' card ' + t); continue; }
        cur = { card: t, k: cardIdx[t], s: 1, r: 0, l: 0, w: 0, h: 0 }; e.cards.push(cur);
      }
      if (e.cards.length > 2) errs.push(item + ':' + phase + ' more than 2 cards');
      ev[e.name] = e; list.push(e);
    }
  }
  return { ev, list, errs };
}
