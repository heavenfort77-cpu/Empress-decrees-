# 09. Palace pieces II: water clocks, water vats, twelve bronze giants
Blocked by: 04

## Outcome
The burning shows in the scene and can be fought: a water clock per wing counts down to its burning, bronze vats douse fire where they break, and each burning wakes one of the twelve bronze giants that slowly hunts the field.

## Acceptance criteria
- [x] 铜壶滴漏 in each wing: water level matches the time to that wing's burning (same clock as the HUD).
- [x] 门海 vats: break to flood a spot; douses the burning there for N s; knockback in the splash; the fairness invariant still holds.
- [x] 十二金人: one woken per burning wave (cap in CONFIG); slow, big tells >= 0.4 s, heavy hits; hunts the nearest suit; off-screen giants act in the simulation and are announced.
- [x] Checks per piece, fairness monitor still mutation-tested, budget with awake giants, Royal Rumble green, static PASS, CI suite, mutation round.

## Notes
Design: docs/BURNING-PALACE.md "Palace pieces". Escalation caps about 1.4x at the peak.

## Done (BP09)
Checks 1000-1006 (tests/bp09-checks.mjs); CI suite 45346524973 203 of 204 (42 only, balance item); mutation round 45346642958 22 of 22 by the named check (incl. BP04 fairness monitor mutants 602/603).
Off-screen: giants are always simulated in full (any room) and each wake is announced; BP03's rival simulation reads giantsInRoom(r) (to wire at the merge).
