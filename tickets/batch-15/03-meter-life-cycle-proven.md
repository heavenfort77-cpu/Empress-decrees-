# 03. Meter life cycle proven
Blocked by: 02

## Outcome
The meter behaves right across a whole run: casting, the wake, the hunt, a new run, the HUD and the budget.

## Acceptance criteria
- [ ] Neither the player nor a bot can cast R under 100; casting empties the meter.
- [ ] The wake fills the meter; the hunt keeps the 30 s ultimate cooldown; check 42 passes unchanged.
- [ ] A new run (x3 in the same page) starts every suit at 0.
- [ ] The HUD R charge text and ring are written only when the shown value changes (no writes over a quiet span).
- [ ] Budget, shader programs and geometry count stay flat with the HUD ring.
- [ ] Mutation round on every new check; static PASS (ratchet), runtime N of N; one commit, pushed.

## Notes
道甲 and 阴阳甲 keep their own ultimate rules later (ultMode per suit); not built here.
