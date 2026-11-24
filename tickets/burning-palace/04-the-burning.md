# 04. The burning (rooms fall into the lake)
Blocked by: 03

## Outcome
About every 40 s Kaymuse names a wing; after a 5 s warning its rooms fall into the black lake, closing routes and herding everyone to the centre. A locked room is never warned until its fight ends.

## Acceptance criteria
- [ ] Wave timing and warnings per wing (TEXT keys, banner, room map).
- [ ] Fairness invariant checked every tick in bot runs: no warned room is locked; no death from a fall without a 5 s warning.
- [ ] Rivals in a falling room off-screen die by the simulation (announced); traces handled.
- [ ] Checks + mutation of the fairness monitor.
- [ ] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [ ] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [ ] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).
