# 08. 道甲 · 真人 (Daoist) kit
Blocked by: 07

## Outcome
A player or a bot can play 道甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] ultMode 'counters': R multiplies base damage, speed and ARMOR by 1 + counters x step (max 5, cap 1.4x); every hit (suits, cubs, minions, demon) passes the one counter function.
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [x] Gate 65 (150-255 s) still passes; if not: stop, report numbers and cause, no tuning.
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.

## Result (lead, 24 Nov)
- CI suite t08-suite-5 (run 45307171938): 157 of 158; 65 and 83 pass (royale 170-214.8 s).
- Check 144 FAILS on its R clause only (the 农甲 bot casts R 0 times in its 3 matches; it dies at 127-152 s and its meter needs about 200 s on passive gain): meter rate and survival = balance. Owner 24 Nov 01:22 "get all results first then talk about balanced": not tuned, check unchanged, settled at the balance pass.
- Bot fixes in this ticket (cause / removed by / proof in /home/claude/batch16.log): castAt reset per run; fleeing bot walks to its safe spot; navNode skips wall nodes; botReadyUlt (名甲 pierce R from keep-away, 农甲 harvest while healing); botFieldAhead (农甲 sows out of a fight).
- CI mutation runs: 45305273396 (24 of 24), 45308208031 (3 of 3).
