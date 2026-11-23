# 02. Charge sources proven
Blocked by: 01

## Outcome
Every way to gain charge is checked to give exactly its CONFIG amount, and the player-facing text says "charge", not "cooldown".

## Acceptance criteria
- [ ] One scripted check per source: passive 0.5/s, 0.25 per hp dealt to suits, 0.1 per hp taken, kill +20, plate +30, crab 'ult' boon +20 x amount, bounty claimed = 100.
- [ ] Under the "Ultimates 2x" decree every gain is doubled (DECREES.ultK), outside it not.
- [ ] Text keys boon_ult, rule_plate_s, rule_plate_h, rule_dec_ult2x, hud_dec_ult2x describe charge; the text-key check passes.
- [ ] Mutation round: each new check fails on a deliberate bug in its source; file restored and compared after each.
- [ ] Static PASS (ratchet), runtime N of N; one commit, pushed.

## Notes
Amounts are the owner-approved set (21:45); no tuning.
