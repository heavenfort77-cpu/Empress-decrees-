# 05. 名甲 · 辩者 (School of Names) kit
Blocked by: 04

## Outcome
A player or a bot can play 名甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [ ] Gate 65 FAILS on seed 2 only (decided 141.2 s < 150; 12 seeds 141.2-224.2 s; invariants, causes, plates/boons and spawn wins pass) and check 83 FAILS on seed 5 (told 5; told 12345:3,2:3,3:3,4:3,5:5,6:3,7:3,8:3,9:3,10:3,11:3,12:3): owner 24 Nov 01:22 "get all results first then talk about balanced": not tuned, checks unchanged, settled at the balance pass.
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.

## Done (ticket 05)
Checks 121-128 added (passive, wheel, shadow blink, W, R, signature: bots dodge the hanging lines, 名甲 in whole matches, budget); 96 changed on purpose.
Fix: cause: the 儒甲 bot held a full meter and never came within its R radius x botIn once 名甲 kept fights at range (110: seeds 2 and 3 maxCh 100, ultN 0) /
removed by: a bot with a ready aura ultimate walks in while it keeps attacking (botAuraIn) / proof: probe p110 ultN 1 and 1, check 110 passes.
Mutation 19 of 19 caught by the named check (first round 18 of 19: 126's free bot left the line by roaming; 126 now has it fighting in reach, so only the dodge moves it).
Assumptions (numbers where the doc gives none): passive restarts after 4 s; wheel 6 dmg x2 passes, range 8, speed 16 m/s, back over walls; blink 6 m, shadow 1 s (bots and the
player's auto-target only, not the hunt units); W 8 m line, 1 s, slow 30% 1 s on touch, 20 dmg; R 30 m line, 1 s, 45 dmg, stopped by a wall like every line skill; the
player's own W and R hit only targets the player can see (the game-wide rule for player skills); bots keep 4 m from their target while the step back is a plain walk.
