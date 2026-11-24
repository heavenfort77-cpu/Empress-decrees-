# 05. The full palace (阿房宫 model) and escalation
Blocked by: 04

## Outcome
About 25-30 rooms on a platform over the black lake: the nine halls on the rim, courtyards, corridors, gardens (curtains), bridges, the core hall; room types shape fights; squads grow toward the core; door previews and the room minimap complete.

## Acceptance criteria
- [ ] Layout data for all rooms (types: courtyard, corridor, garden, bridge, hall, core) with doors; reachability check (every room reachable, the core reachable from every rim hall until it burns).
- [ ] Escalation tables (squads per room by depth and time) in CONFIG; her reinforcement decree.
- [ ] Room minimap (fallen rooms shown; off-screen fights only by announcement).
- [ ] Pacing measured (dull-time probe from the audit): no stretch over about 5 s with nothing to fight, dodge or choose, over 12 seeds; run length 4-5 min.
- [ ] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [ ] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [ ] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).
