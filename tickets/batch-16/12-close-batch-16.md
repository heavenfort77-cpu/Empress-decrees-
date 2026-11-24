# 12. Close batch 16
Blocked by: 11

## Outcome
All nine kits and the 兵家 apex measured, recorded and handed to the owner to play.

## Acceptance criteria
- [ ] Per-school 12-seed sims: decided range, win share per school, R casts per suit (printed), decrees per match, plate rate, leader win share (reported only).
- [ ] Hunt sweep (test 42 bot) run once per suit, against the final 兵家 apex (ticket 11),: report win/loss per kill order; flag any suit that makes the apex trivial (never loses) or impossible (never wins), no tuning.
- [ ] GDD and docs/SUITS.md: 兵家 apex lore and renamed moves (owner 24 Nov 09:44-09:5x), the empty 10th disc as 兵家's place.
- [ ] HANDOFF: batch 16 section, numbers, owner decisions; Next batch = 17 (balance pass when the owner has played, then hiding 18, ending 19, map size 20 as queued).
- [ ] One commit, pushed. Lead: verify head and a fresh full run, republish the phone link, sync project docs.

## Notes
All heavy runs (suite, sims, hunt sweeps, mutations) on GitHub runners via ci_mut.sh (CLAUDE.md).
Known balance items to report, not fix: check 83 (decrees per match), check 144 R clause (农甲 bot never fills its meter).
Owner balances only when all is ready: report, never tune here.
