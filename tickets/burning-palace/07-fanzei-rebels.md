# 07. The 反贼 rebels (黄巾 in bootleg 甲)
Blocked by: 02 and 03

## Outcome
A third side in the palace: 黄巾 rebels in bootleg suits, out to assassinate Kaymuse, fight the 皇家 guard and hunt whoever leads the run (usually the player).

## Acceptance criteria
- [ ] Four unit types: 黄巾力士 (bootleg move copied from one school, weaker, longer tell, stalls after a few uses), 符水道人 (healer), 死士 (hides, lunges at the run leader), 渠帅 (leader; its kill breaks the squad and drops a bootleg charge).
- [ ] Rebels and the guard fight each other on sight; three-way rooms work with the door locks.
- [ ] Door previews and Kaymuse's announcements cover rebel rooms (TEXT keys).
- [ ] Uses the 02 spawn API with a faction field; pooled, instanced, CONFIG switch (off in Royal Rumble).
- [ ] Checks: each move and tell (>= 0.4 s), leader targeting, squad break, three-way fight, budget with a guard squad and a rebel squad drawn.
- [ ] Royal Rumble checks stay green; static PASS; CI suite; mutation round on the new checks.

## Notes
Design: docs/BURNING-PALACE.md "Third side: the 反贼". Box prototype first; art later. No balance tuning.
