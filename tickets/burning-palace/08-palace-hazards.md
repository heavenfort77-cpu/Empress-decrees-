# 08. Palace pieces I: lions, mercury, smoke, 华表, 鼎
Blocked by: 03

## Outcome
Rooms fight back: stone lions at big doors, mercury channels, smoke from cranes and burners, 华表 beasts that mark you, and 鼎 cauldrons that heal, all hitting or helping every side.

## Acceptance criteria
- [ ] 石狮 pair at hall/gate doors (lion code reused; 0.6 s ring, 3.5 m).
- [ ] 水银 channels: damage over time in the channel, a shimmer >= 0.4 s before each pulse; bots path around them or cross between pulses.
- [ ] 铜鹤 / 香炉 smoke: blocks sight (player fog and bot vision); hiding works for player, rivals and 死士; few small cards.
- [ ] 华表: passing it marks the suit for N s (existing mark); bots react as to any mark.
- [ ] 鼎: nine, one per school hall, healing like the altars (palace only; Royal Rumble altars unchanged).
- [ ] Each piece hits or helps guard, rivals and player alike (lure check).
- [ ] Checks per piece (tell, effect, all sides), budget in the busiest room, Royal Rumble green, static PASS, CI suite, mutation round.

## Notes
Design: docs/BURNING-PALACE.md "Palace pieces" (owner 24 Nov 14:24-14:27). Box shapes first; art later.
