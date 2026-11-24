# 09. 纵横甲 · 说客 (Diplomatist) kit
Blocked by: 08

## Outcome
A player or a bot can play 纵横甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] The hunter cap holds every tick while 不攻自破 and 事一强 steer bots; the player is never steered; the two confirmed hunt rules work.
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [x] Gate 65 (150-255 s) still passes; if not: stop, report numbers and cause, no tuning.
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.

## Done (batch 16 ticket 09)
- Checks 154-162 (154 passive + hunter cap + player never steered, 155 attack, 156 Q, 157 W into a warned section (the "Plays with" check) + 道甲 counter, 158 R, 159 hunt rules, 160 whole matches (bot casts R), 161 budget, 162 名甲 strike fix); check 96 updated (纵横甲 built).
- CI suite on the committed tree: run 45314497324, RUNTIME 167 of 167; 65, 83 and 144 pass (no FAIL lines).
- Mutation rounds: runs 45312289983, 45313799041 and 45314526406: 27 of 28 caught by a named check; link-no-precheck crashes the runner (TypeError), so it is caught only as a runner FAIL.
- Game bug fixed: cause: strikeHang read h.sk on every target, and a hit that breaks the 名甲 bot runs botOut -> endMing -> h.sk = null in the middle of the loop / removed by: the line's skill and shape are read once / proof: check 162, mutation run 45314526406.
- Balance items (no tuning): none new.
