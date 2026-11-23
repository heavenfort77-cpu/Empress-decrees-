# 04. 墨甲 · 墨守 (Mohist) kit
Blocked by: 03

## Outcome
A player or a bot can play 墨甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] No dash; the wall stops the demon's Pounce and minion dashes (dash length checks it).
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [x] Gate 65 (150-255 s) still passes (153-210.6 s).
- [ ] Check 83 FAILS (seed 7 told 2 decrees; told 12345:3,2:4,3:3,4:3,5:4,6:3,7:2,8:3,9:3,10:4,11:4,12:3): owner 24 Nov 01:22 "get all results first then talk about balanced": not tuned, check unchanged, settled at the balance pass.
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.

## Done (ticket 04)
Checks 112-120 added; 93 and 96 changed on purpose. Fix: bots' path searches go around raised walls (navInWall). Mutation 23 of 23 caught by the named check (first round 21: one no-op mutation of mine, one gap in 119 closed by counting fight walls apart from flee walls).
