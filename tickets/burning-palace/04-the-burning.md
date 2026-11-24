# 04. The burning (rooms fall into the lake)
Blocked by: 03

## Outcome
About every 40 s Kaymuse names a wing; after a 5 s warning its rooms fall into the black lake, closing routes and herding everyone to the centre. A locked room is never warned until its fight ends.

## Acceptance criteria
- [x] Wave timing and warnings per wing (TEXT keys, banner, room map).
- [x] Fairness invariant checked every tick in bot runs: no warned room is locked; no death from a fall without a 5 s warning.
- [ ] (needs BP03's simulation: it reads room.fallen; onWingFall is the entry point) Rivals in a falling room off-screen die by the simulation (announced); traces handled.
- [x] Checks + mutation of the fairness monitor.
- [x] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [x] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [x] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).

## Built (BP04, branch bp04-burn)
CONFIG.BURN (40 s from naming to naming, 5 s warning, order outer/court/west/east on the BP01 rooms via BURN_WINGS until BP05). Checks 600-605. CI suite 45341857830: 196 of 197 (42 only, known balance). Mutation 45342452301: 13 of 14 named; 'gone-stays-drawn' equivalent (a fallen room is never in view when it leaves: its doors close at the fall, and a player inside it is out before then).
Monitor (every tick, burnState().bad): no warned room locked; every room falls >= warnS after its warning; every palace fall death from such a room. BP03: lock rooms only when burnCanLock(room); its simulation kills rivals in a room with room.fallen and announces via palAnnounce.
