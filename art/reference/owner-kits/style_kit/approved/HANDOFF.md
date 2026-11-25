# Suit Mythology prototype: handoff (batch 1, 2026-11-06)
- Files: proto/suit_proto.html (one file, box-and-shape, phone d-pad + keys), proto/proto_test.js (node: bot-vs-bot pacing, pass/fail), proto/smoke.js (Playwright load check).
- Run: open suit_proto.html; `node proto_test.js 30`; `node smoke.js`.
- All tunables are in the CONFIG block at the top of the logic (storm table, HP_SCALE, EARLY_PEACE, AG_SCALE, per-faction stats, skills).
- Rules in: 64x64 grid, 20 suits, vision 5, bush clusters >= 5 (hide, attackable, regrow 60 s), resources (grow x2, used after 20 s, regrow 90 s), wrecks (resource + 巫师 raise + 墨将 units), growth clock with caps per faction, 猿魔 time-only quadratic with stages at 180/420 s, storm 7 phases (805 s total) with PUBG damage, regen, kill heal, all 8 skills (overdrive, stun+raise, turret+pack-up, sword array, cloak with 2x, channel, decay plant, vault), followers, turrets see into bushes, 天龙 range 8 in a bush with 1 s reveal.
- Not in: walls, 剑仙 true damage, 蛊师 erosion trail, pixel art, sound, faction lore.
- Measured (30 bot matches): average 544 s, min 409, max 682; winners spread over 7 of 8 factions; 剑仙 never won (early suit falls off). Target 600 s minimum NOT yet met.
- Levers that moved it: spawn gap 16, early peace 200 s, aggression x0.7, HP x2, slower storm. HP x2.5 and an aggression ramp did not help.
- Next: user plays it; decide whether to (a) hold the win until the storm's last phase, (b) slow the storm more, or (c) make bots hide better.

## Batch 2 (2026-11-06): player-style bots, 剑仙 buffs
- Bots now: pick the weakest target in reach, decide fight-or-avoid from relative power x aggression, kite (step out of reach while the attack cools when they outrange or outrun the foe), heal in bushes when under 45%, keep a 2-tile margin inside the coming ring and move 25 s before a shrink, and use faction openers (overdrive on contact, 冥将 cloaks on the approach for the 2x hit, 巫师 stuns on the way in, 墨将 drops a turret toward the foe and stands behind it, 天龙 walks to a bush within 7 of the foe, 蛊师 plants under itself and on resources, 猿魔 vaults in or out).
- 剑仙: HP 80, cap x2.2 by 300 s, sword array gives 1 s stun guard. 猿魔 cap lowered x5 -> x4 (it won 13/30 at x5).
- Prototype assumption to confirm: 天龙 in a bush sees 8 tiles (else its range 8 can never be used, since vision is 5).
- Measured, 60 bot matches: average 595 s (min 327, max 794); storm 3 kills of 1228. Wins: 猿魔 18, 剑仙 12, 天龙 8, 巫师 7, 天兵 6, 蛊师 6, 墨将 3, 冥将 0. 冥将 median death 176 s, mostly to turrets (it kites into them). 猿魔 still too strong late.
- Backup: suit_proto_v1.html (batch 1 bots).

## Batch 3 (2026-11-06): 冥将 unseen hits, 猿魔 early window
- 冥将: any hit the target cannot see is doubled (cloak now hides fully until it attacks; CLOAK [6,25,0]). Approved rule (CONFIG MJ_KILL, active): +0.25x per kill up to +1.2x (assassin grows by kills, not time).
- 猿魔 early window: bots prefer a 猿魔 below stage 3 as a target (HUNT_YM 25) and fight it when they are at least 0.8x its power. Early-window suits (aggression >= 0.8: 冥将, 剑仙) hunt from the start; the others hold back until 200 s.
- 天龙 bush vision 8 confirmed by the user.
- Measured, 60 bot matches: average 573 s (min 348, max 768). Wins: 天龙 18, 剑仙 14, 天兵 8, 猿魔 8, 蛊师 6, 墨将 3, 巫师 2, 冥将 1. Run-to-run noise is about +-5 wins per faction at 60 matches.
- Open: 冥将 bot still converts few fights (0.24 kills per suit); its kit works for a player (cloak, 2x unseen) but the bot walks into turrets and into range-2/3 suits. 天龙 is now the top bot.
- Fix 2026-11-06: ATK button on phone (pointer capture, no pointerleave cancel); a swing line shows on every press, white on a hit, grey on a miss; enemy 蛊师 decay areas are hidden until you stand inside one (bots do not avoid areas they cannot see either).

## Batch 4 (2026-11-06)
- 冥将: speed 3.5 -> 3.3, own dash 4 tiles with 3 s cooldown (MJ_DASH), a kill resets its dash and cloak. 剑仙 HP 70, cap x2.0 by 300 s (the 80/x2.2 buff overshot: 20/60 wins). 巫师 speed stays 3.2 (still below 冥将's 3.3).
- Bug found and fixed while tuning: a line comment inside the CONFIG line swallowed ATK_PERIOD in an intermediate build (attacks never cooled down). Never put `//` comments mid-line in CONFIG.
- 60 bot matches: average 587 s (min 327, max 788). Wins: 天龙 16, 猿魔 14, 剑仙 12, 巫师 6, 天兵 6, 蛊师 4, 墨将 2, 冥将 0.
- Open: 冥将 and 墨将 are weak in bot hands (0 and 2 wins) though their kits suit a human; the real test is play.

## Sandbox balance test (2026-11-06): `node balance_test.js 120`
- Verdict: NOT balanced. 120 full matches (avg 579 s) and a 1v1 duel matrix at growth clocks 0 / 250 / 500 s, bots only.
- Wins per appearance (fair 5.0%): 天龙 10.9, 猿魔 9.8, 剑仙 9.5, 蛊师 3.3, 巫师 2.3, 墨将 2.2, 天兵 1.3, 冥将 1.1.
- Failing pairs (same result at every clock): 剑仙 beats 天兵 100% and 冥将 100%; 墨将 beats 猿魔 87-88%; 冥将 loses to 巫师 0% and 天龙 0-5%; 蛊师 loses to 墨将 0-5%.
- Caveats: bots only; duels are open ground, no bushes, no storm, so 蛊师, 墨将, 天龙 (bush range) and 冥将 (cloak) are under-tested; the full-match 墨将 (2.2%) disagrees with its duel strength (60-97%), so its weak point is the walk between zones, as designed.
