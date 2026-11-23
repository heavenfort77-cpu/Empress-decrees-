# 03. Meter life cycle proven
Blocked by: 02

## Outcome
The meter behaves right across a whole run: casting, the wake, the hunt, a new run, the HUD and the budget.

## Acceptance criteria
- [x] Neither the player nor a bot can cast R under 100; casting empties the meter.
- [x] The wake fills the meter; the hunt keeps the 30 s ultimate cooldown; check 42 passes unchanged.
- [x] A new run (x3 in the same page) starts every suit at 0.
- [x] The HUD R charge text and ring are written only when the shown value changes (no writes over a quiet span).
- [x] Budget, shader programs and geometry count stay flat with the HUD ring.
- [x] Mutation round on every new check; static PASS (ratchet), runtime N of N; one commit, pushed.

## Notes
道甲 and 阴阳甲 keep their own ultimate rules later (ultMode per suit); not built here.

## Done (worker, 23 Nov)
Checks 89 (meter gate, player and bot, empty on cast, no royale cooldown), 90 (wake fills, hunt keeps the 30 s cooldown, meter neither gates nor gains), 91 (new run x3 resets every suit, incl. after a hunt), 92 (HUD R written only on change, text and ring match, calls 27 / programs 3 / geometries 96 flat). Check 42 unchanged and passing. Mutation round 10 of 10 caught by the named check (/home/claude/probe15/t03/mut.log). No game bug found; no game change.
