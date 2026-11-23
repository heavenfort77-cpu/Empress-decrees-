# 01. Meter lands green
Blocked by: none, can start now

## Outcome
The ultimate charge meter (panel note 15, owner go 23 Nov 21:45) is in the game, with the royale band at 150-255 s (owner 23 Nov 22:05), and every existing check passes.

## Acceptance criteria
- [ ] The stopped patch (/home/claude/batch15b_stopped.patch: meter, CONFIG.ROYALE.band [150, 255], __game.setCharge) is applied; nothing from it is duplicated or left dead.
- [ ] Checks 26, 32, 48, 54, 60, 71, 76 give charge with setCharge where they cast R at once, each with the comment "game changed on purpose (batch 15)"; no assertion is loosened.
- [ ] Check 65 reads its band from CONFIG.ROYALE.band and passes on its 12 seeds.
- [ ] Static check PASS with no new FAIL against the before-build (ratchet); runtime N of N, all pass.
- [ ] One commit, pushed.

## Notes
Decided, do not reopen: meter 0-100, R casts only at 100 and empties it, no cooldown in the royale; the band floor is 150 s. If check 65 fails on the 150 floor, stop and report numbers and cause; do not tune.
