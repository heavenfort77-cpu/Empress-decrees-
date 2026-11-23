# 07. 农甲 · 耕者 (Agriculturalist) kit
Blocked by: 06

## Outcome
A player or a bot can play 农甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [ ] Sprouts come from a fixed pool of 9; enemies trample them; a field on a falling section is lost.
- [ ] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [ ] Its signature system interaction (the doc's "Plays with") has one check.
- [ ] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [ ] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [ ] Gate 65 (150-255 s) still passes; if not: stop, report numbers and cause, no tuning.
- [ ] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.
