# 03. Door locks, rivals in rooms and the off-screen fights
Blocked by: 01 and 02

## Outcome
Entering a room with enemies locks its doors until they are broken; the 8 rivals move room to room and farm the guard; fights the player cannot see are settled by a seeded simulation, announced by Kaymuse and leave traces; opening a door spawns rivals in their current state; the last two are sealed into one hall; the winner opens the core hall and the 兵家 apex.

## Acceptance criteria
- [ ] Door lock rules (sealed both ways; no fleeing); locked rooms never take new entrants.
- [ ] Off-screen simulation deterministic per seed (same seed = same run, check 82 style), using the measured kit win shares, health, plates and meter; every result announced (TEXT keys) with a trace in the room.
- [ ] Rivals spawn on door open in their simulated state; the hunter rival may track the player between rooms.
- [ ] The core hall door stays sealed (preview says so, TEXT key) until the player is the last suit standing; walking to the core early is impossible (owner 24 Nov 14:16: reaching the core in under 5 min was too easy). Check: a run cannot enter the core while any rival lives.
- [ ] Final duel sealing and the apex start; Royal Rumble untouched.
- [ ] Checks: lock, determinism, announcements, spawn state, final seal, apex start.
- [ ] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [ ] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [ ] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).
