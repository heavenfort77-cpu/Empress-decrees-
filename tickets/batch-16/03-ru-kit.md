# 03. 儒甲 · 君子 (Confucian) kit
Blocked by: 02

## Outcome
A player or a bot can play 儒甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [x] Gate 65 (150-255 s) still passes (161.7-212 s).
- [ ] Check 83 still FAILS as at ticket 02 (seed 9 told 5; 12345:4,2:3,3:4,4:3,5:4,6:3,7:3,8:4,9:5,10:3,11:4,12:3): owner 24 Nov 01:22, not tuned, check unchanged.
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.

## Done (ticket 03)
- Checks 104-111 (passive, attack, Q, W, R, signature, whole matches, budget); 93, 96 and the 法甲 page helper changed on purpose (儒甲 built; the checks' placeholder player via ?pkit=placeholder for the default pick).
- Fix found: the player's last attacker (lastBy/lastByT) survived a new run (reset never cleared it); reset clears it now.
- Mutation: 27 of 28 caught by the named check after 109 was strengthened; 'pkit for every school' caught by 97-103 instead of 93 as named.
