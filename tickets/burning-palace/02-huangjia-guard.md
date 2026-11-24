# 02. The 皇家 guard (cannon fodder)
Blocked by: none, can start now (built in parallel on its own branch, merged after 01)

## Outcome
Kaymuse's imperial household guard: 卒 foot soldiers, 弩手 crossbowmen, 盾 shieldbearers, 车 chariots and a 伍长 squad leader holding a 方阵 formation; they fight the player and the rival suits, feed the ultimate meter, and come from fixed pools drawn as instances.

## Acceptance criteria
- [ ] Five unit types with their moves and tells (spear line, volley on a ground marker, shield block and shove, chariot line charge in open rooms only, leader buff); killing the 伍长 breaks the formation.
- [ ] Squads spawn from a fixed pool (cap about 12 per room), drawn as instances (about one draw call per unit type); a test hook spawns a squad at a point (works on the current map until rooms exist).
- [ ] Rewards: ultimate charge per kill (CONFIG), small heal and short boons; plates stay with cubs; bots (rivals) fight and farm them too.
- [ ] Checks: each move and tell, formation break, pool cap, meter gain, budget with two full squads drawn.
- [ ] Royal Rumble (parked mode) keeps every existing check green; nothing in it changes.
- [ ] Every new hit has a tell >= 0.4 s; new numbers in CONFIG with a comment line; TEXT keys; HUD/DOM only on change; PERFRAME without allocations; pooled and warmed at load.
- [ ] Budget in the heaviest room on tier medium: under 500 calls and 0.5M tris, programs and geometry flat; static PASS (ratchet); CI suite with no FAIL except known balance items; mutation round on the new checks (CI); one commit, pushed.

## Notes
Design: docs/BURNING-PALACE.md (owner 24 Nov 13:18-13:44). Heavy runs on GitHub only (CLAUDE.md). No balance tuning (owner: results first).
