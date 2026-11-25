# 10. 杂甲 · 门客 (Syncretist) kit
Blocked by: 09

## Outcome
A player or a bot can play 杂甲 in the royale and the hunt with the full kit from docs/SUITS.md (passive, attack, Q, W, R, its "Against the apex" rules if any).

## Acceptance criteria
- [x] 一字千金 casts any stored skill of the other eight kits and of the demon/minions at full strength with the original's tell and colour; 正名 on the demon seals its stolen skills (confirmed hunt rule).
- [x] One check per skill: it does what docs/SUITS.md says for this suit, with its numbers read from CONFIG.KITS; every move that hits others shows its tell >= 0.4 s where the doc says it is shown.
- [x] Its signature system interaction (the doc's "Plays with") has one check.
- [x] A bot plays this suit in a whole match without breaking invariants (on a floor, never stuck > 3 s, hunter cap holds).
- [x] Budget, shader programs and geometry flat with every effect of this kit drawn (pooled, warmed at load).
- [x] Gate 65 (150-255 s) still passes; if not: stop, report numbers and cause, no tuning.
- [x] Mutation round on every new check; static PASS with no new FAIL (ratchet); runtime N of N; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01.

## Result (ticket 10, 24 Nov)
- CI suite on the committed index.html and tests/run.mjs: run 45327553792 (t10-suite-3), 180 of 181; only FAIL 42 (hunt sweep: known balance item, not tuned). 65, 83, 144 pass.
- CI mutation run 45328001408 (t10-mut-1): 11 of 11 caught by the named check (163-171).
- New checks 163-171: passive 兼收并蓄, attack 议 and stats, Q 兼儒墨, W 合名法, R 一字千金, copy table (22 stored skills: 8 kits, his own Q, 6 unit moves), hunt rules, whole matches, budget.
- Check fixes while resuming (checks written in this ticket; game unchanged): scenes 165-168 parked bots in the void (they fell) and a target on training dummy 1 (it took the orb); 167 asserted a meter of 0 after the copied hit (the dealt rule charges it); 169 cast Roar during the copied Pounce's dash and read health from player() (no hp). Check 56 (old) now also excuses an exposed suit (seen by every suit since ticket 02): game changed on purpose.
- Never stored by design (they never touch an enemy): 墨 wall and nine defences, 道 stances and R, 法 W, 名 blink, 农 sow, 纵横 R circle (persuasion, not a blow).
- Hunt probe (CI run 45329060502, report only): 杂甲 wins 1 of 9 sweep runs (0.15 s, order 0-1-2), 0 errors.
