# 05. The full palace (阿房宫 model) and escalation
Blocked by: 04, 08, 09

## Outcome
About 25-30 rooms on a platform over the black lake: the nine halls on the rim, courtyards, corridors, gardens (curtains), bridges, the core hall; room types shape fights; squads grow toward the core; door previews and the room minimap complete.

## Acceptance criteria
- [x] Layout data for all rooms (types: courtyard, corridor, garden, bridge, hall, core) with doors; reachability check (every room reachable, the core reachable from every rim hall until it burns). The shortest route from any rim hall to the core passes at least 5 rooms (owner 24 Nov 14:16). BP05 ca80ff1: 29 rooms, checks 700-704.
- [x] Escalation tables (squads per room by depth and time) in CONFIG (PAL_ESC, check 707). [ ] Her reinforcement decree: waits for 02/03 (spawning and her announcements).
- [x] Room minimap (fallen rooms shown; off-screen fights only by announcement) (check 706; fallen/warned flags come from 04).
- [ ] Pacing measured (dull-time probe from the audit): no stretch over about 5 s with nothing to fight, dodge or choose, over 12 seeds; run length 4-5 min. NOT YET: needs 02/03/04 merged (no guard, rivals or burning in the palace yet).
- [x] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [ ] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [x] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed. BP05: suite 45342471018 200 of 201 (42 only), mutation 45343086278 14 of 14, worst room garden_sw+corr_sw 13 calls / 566 tris (run 45344545140); branch bp05-layout. Budget to re-measure with guard squads and pieces drawn.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).
