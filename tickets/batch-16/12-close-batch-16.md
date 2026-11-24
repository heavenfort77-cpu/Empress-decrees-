# 12. Close batch 16
Blocked by: 11

## Outcome
All nine kits and the 兵家 apex measured, recorded and handed to the owner to play.

## Acceptance criteria
- [x] Per-school 12-seed sims: decided range, win share per school, R casts per suit (printed), decrees per match, plate rate, leader win share (reported only).
- [x] Hunt sweep (test 42 bot) run once per suit, against the final 兵家 apex (ticket 11),: report win/loss per kill order; flag any suit that makes the apex trivial (never loses) or impossible (never wins), no tuning.
- [x] GDD and docs/SUITS.md: 兵家 apex lore and renamed moves (owner 24 Nov 09:44-09:5x), the empty 10th disc as 兵家's place.
- [x] HANDOFF: batch 16 section, numbers, owner decisions; Next batch = 17 (balance pass when the owner has played, then hiding 18, ending 19, map size 20 as queued).
- [x] One commit, pushed (73d5940). Lead (done 24 Nov 12:58: CI 45329305763 180 of 181 on the committed files, phone 1795496303-efbf, project docs synced): verify head and a fresh full run, republish the phone link, sync project docs.

## Notes
All heavy runs (suite, sims, hunt sweeps, mutations) on GitHub runners via ci_mut.sh (CLAUDE.md).
Known balance items to report, not fix: check 83 (decrees per match), check 144 R clause (农甲 bot never fills its meter).
Owner balances only when all is ready: report, never tune here.

## Result (T12, 24 Nov)
- CI: per-school matches 45329303870, hunt sweep per school 45329304057 (tools on branch t12-prep 6a178d3), full suite with -sims 45329305763 on 6c9cbb0: 180 of 181 (FAIL 42, balance item).
- Tables and known balance items in HANDOFF "Batch 16 (done)". GDD and docs/SUITS.md already carry the 兵家 lore (ticket 11, merged b298701).
- Nothing tuned (owner 24 Nov 01:22).

