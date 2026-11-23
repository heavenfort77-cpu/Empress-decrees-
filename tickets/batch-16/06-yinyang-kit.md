# 06. 阴阳甲 · 太极 (Yin-yang) kit
Blocked by: 05

## Outcome
A player or a bot can play 阴阳甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] ultMode 'lock': the yin-yang lock replaces charge; under Ultimates 2x only the cooldown after use runs 2x.
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [x] Gate 65 (150-255 s) still passes: 171.6-213.4 s; check 83 also passes this run (owner 24 Nov 01:22: pacing not tuned in batch 16).
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.
