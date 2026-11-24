# 11. The apex becomes 兵家 (Tiger Demon, tiger look kept)
Blocked by: 10

## Outcome
The Tiger Demon and its two minions are 兵家: renamed moves from 《孙子兵法》 with mechanics unchanged, and a new passive 攻其无备. HUD name stays "Tiger Demon" (owner 24 Nov 09:4x).

## Acceptance criteria
- [ ] Move names and text keys: Pounce -> 其疾如风; Metal roar -> 动如雷震; Shed the limit -> 侵掠如火，不动如山; Stalker = 正 (straight force), Howler = 奇 (surprise force); the plate-home note names 奇正相生. Boss name "Tiger Demon" unchanged. Every string from TEXT keys; text-key checks pass.
- [ ] Passive 攻其无备: the demon and both minions deal bonus damage (CONFIG, one number, capped with every other bonus at 1.4x) to a suit whose dash is on cooldown; 墨甲 (no dash) counts his wall (Q) as his escape (panel proposal; owner may change). Every hit still has its tell >= 0.4 s (checks 34, 42 invariants hold).
- [ ] Checks: bonus applies only while the dash (or 墨甲's wall) is on cooldown, for demon and minions, at the CONFIG amount; not on statue, lions, collapses; text checks for the new names; mutation round on the new checks.
- [ ] Hunt checks 33-45 pass (mechanics unchanged except the passive); the hunt sweep (42) numbers reported before/after the passive.
- [ ] Budget, programs and geometry flat; static PASS (ratchet); CI suite N of N (only known balance FAILs 83/144 allowed); one commit, pushed.

## Notes
Decided, do not reopen: tiger design and the "Tiger Demon" HUD name stay; mechanics unchanged except the passive; no tuning (balance after all is ready). 兵家 lore (the empty 10th disc is its place) goes into the GDD at the close-out. Heavy runs on GitHub via ci_mut.sh.
