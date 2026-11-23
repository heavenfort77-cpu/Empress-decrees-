# 02. Charge sources proven
Blocked by: 01

## Outcome
Every way to gain charge is checked to give exactly its CONFIG amount, and the player-facing text says "charge", not "cooldown".

## Acceptance criteria
- [x] One scripted check per source: passive 0.5/s, 0.25 per hp dealt to suits, 0.1 per hp taken, kill +20, plate +30, crab 'ult' boon +20 x amount, bounty claimed = 100.
- [x] Under the "Ultimates 2x" decree every gain is doubled (DECREES.ultK), outside it not.
- [x] Text keys boon_ult, rule_plate_s, rule_plate_h, rule_dec_ult2x, hud_dec_ult2x describe charge; the text-key check passes.
- [x] Mutation round: each new check fails on a deliberate bug in its source; file restored and compared after each.
- [x] Static PASS (ratchet), runtime N of N; one commit, pushed.

## Notes
Amounts are the owner-approved set (21:45); no tuning.

## Done (23 Nov)
Lead scope change: ticket 01 already proves plate (48), crab boon (54), bot plate (60), bounty (71) and the 2x decree (76); this ticket adds 87 (passive, dealt, taken, kill, player and bot, nothing while broken) and 88 (charge wording), and runs the mutation round over every source.
Static PASS (no new FAIL), runtime 93 of 93. Mutation 9 of 9 caught by the named check (passive 87, dealt 87, taken 87, kill 87, plate 48+60, crab 54, bounty 71, 2x 76, wording 88).
