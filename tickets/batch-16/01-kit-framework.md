# 01. Kit framework, suit stats and school select
Blocked by: none, can start now

## Outcome
Suits get their school's stats and a kit slot; the player picks a school (or a random one) before each run; bots take the other eight. Every suit still plays the placeholder kit, so the game plays as now.

## Acceptance criteria
- [ ] CONFIG.KITS table per school (stats tier, attack/Q/W/R/passive slots, ultMode) with a comment line above each value; the placeholder kit is the Mid yardstick and stays the map-test kit (?bots=0).
- [ ] Armor per docs/STATS-MATH.md: taken = raw x (K + 40) / (K + armor), K 100, Low/Mid/High 20/40/70, HP 100; speed 5.6/6/6.4 m/s; statue, lions, drops and the void stay fixed. All suit and creature damage passes one function (道甲's counters and 杂甲's copy will hook there).
- [ ] School select before each run: 9 buttons plus a random button, 44 px targets on phone, keyboard and mouse on desktop, last pick in try/catch storage; HUD names the player's school; bots take the other eight (one each).
- [ ] Minimal unseen state: not drawn for other suits, not targetable by bots or auto-target, shimmer within 3 m, ends on attacking or being hit.
- [ ] A common skill interface (cast, tell, hit, tags for bots) that kits plug into, so 杂甲 can copy any skill later.
- [ ] Every existing check passes with all suits on the placeholder kit at Mid stats (no assertion loosened); new checks for armor, speed tiers, select screen, random pick, unseen state; mutation round; static PASS (ratchet); budget flat; one commit, pushed.

## Notes
Decided, do not reopen: one number set from the doc's 'about' values, no tuning (owner: balance when all is ready); stats per docs/STATS-MATH.md; minimal unseen state from T01. Player school select replaces "You" only in the HUD school line; the player is still SUITS[0].
