# 08. Palace pieces I: lions, mercury, smoke, 华表, 鼎
Blocked by: 03

## Outcome
Rooms fight back: stone lions at big doors, mercury channels, smoke from cranes and burners, 华表 beasts that mark you, and 鼎 cauldrons that heal, all hitting or helping every side.

## Acceptance criteria
- [x] 石狮 pair at hall/gate doors (lion code reused; 0.6 s ring, 3.5 m). Check 801. Test placement: garden-to-bridge door until 05 places them.
- [x] 水银 channels: damage over time in the channel, a shimmer >= 0.4 s before each pulse (802). Bots read shimmer and burn as danger after their reaction time and step out across the channel (806).
- [ ] Bots walking around or across channels in a real palace run: needs 03 (bots are not stepped in the palace before 03); verify after the merge.
- [x] 铜鹤 / 香炉 smoke: blocks sight in palSight and bot vision (803); one merged cloud mesh per room. Player view of rivals uses palSight once 03 draws rivals in the palace (verify after the merge); 死士 with 07.
- [x] 华表: passing it marks the suit for N s (existing mark), tell 0.5 s; a marked suit is seen through walls and smoke by bots (804).
- [x] 鼎: heals like the altars (palace only; Royal Rumble altars unchanged) (805). One in the BP01 hall now; the nine school halls come with 05.
- [x] Each piece hits or helps the player, a bot and a unit of another side (PIECE_SIDES; checks 801, 802, 805 with a stand-in unit). The 皇家 guard joins with one PIECE_SIDES push at the merge.
- [x] Checks 800-807; CI suite 45343934489 198 of 199 (only 42, known balance); mutation round 45343929495 18 of 18 named; static PASS.

## Notes
Design: docs/BURNING-PALACE.md "Palace pieces" (owner 24 Nov 14:24-14:27). Box shapes first; art later.
