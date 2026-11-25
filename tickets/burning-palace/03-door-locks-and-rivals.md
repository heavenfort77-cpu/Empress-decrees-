# 03. Door locks, rivals in rooms and the off-screen fights
Blocked by: 01 and 02

## Outcome
Entering a room with enemies locks its doors until they are broken; the 8 rivals move room to room and farm the guard; fights the player cannot see are settled by a seeded simulation, announced by Kaymuse and leave traces; opening a door spawns rivals in their current state; the last two are sealed into one hall; the winner opens the core hall and the 兵家 apex.

## Acceptance criteria
- [x] Door lock rules (sealed both ways; no fleeing); locked rooms never take new entrants.
- [x] Off-screen simulation deterministic per seed (same seed = same run, check 82 style), using the measured kit win shares, health, plates and meter; every result announced (TEXT keys) with a trace in the room.
- [x] Rivals spawn on door open in their simulated state; the hunter rival may track the player between rooms.
- [x] The core hall door stays sealed (preview says so, TEXT key) until the player is the last suit standing; walking to the core early is impossible (owner 24 Nov 14:16: reaching the core in under 5 min was too easy). Check: a run cannot enter the core while any rival lives.
- [x] Final duel sealing and the apex start; Royal Rumble untouched.
- [x] Checks: lock, determinism, announcements, spawn state, final seal, apex start.
- [x] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [x] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [x] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).

## Done (BP03, branch bp03-locks)
- Checks 500-510 in tests/palace3-checks.mjs (509 needs ticket 04, 510 needs ticket 02: registered only when those are in the build; both passed on a scratch merge of batches-3-5 085974f + bp04-burn 0530e68: probe CI 45347742015 11 of 11; mutation round on that merge CI 45347958405 5 of 5 named, its suites 215 of 217 with only 42 + the mutated check failing).
- Mutation round on this branch: CI 45347135927, 13 of 13 named (500-506, 508; 507 is a budget measurement).
- Changed on purpose: 402 and 407 (the core hall wakes the apex), 408 (end screen = the player broken in the palace).
- Assumptions (CONFIG.PAL_SIM / PAL_LOCK): rivals and squads only in a match (bots > 0); start hall empty; rivals start in seeded rooms (never the start hall or core) until ticket 05 gives school halls; the final duel = the last rival hunts the player and the room locks with both inside; the apex wakes in the royale core hall arena (the hunt as built).

