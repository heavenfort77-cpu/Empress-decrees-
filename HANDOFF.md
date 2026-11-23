# Handoff (2026-11-23 14:30, after batch 10; written for a fresh session). GDD: docs/GDD.md (also Project "empress decrees", claude/GDD.md)

## Session start (every session)
1. Attach both repos: add_repo heavenfort77-cpu/Empress-decrees- (access push) and heavenfort77-cpu/dawnpunk (read; public, anonymous clone works). Dawnpunk = reference for frame-rate rules and bug pitfalls; read only the part needed.
2. Clone with `--no-single-branch`; check out `batches-3-5` (PR #1 still open, not merged; use main only if it is merged: `gh api repos/heavenfort77-cpu/empress-decrees-/pulls/1 --jq .merged`, GraphQL is blocked).
3. Read this file, then only the GDD section being changed (batch 11: "Royale minions" -> "The leader", and "Kaymuse's decrees"). Do not read the whole codebase.
4. Run the checks before and after any change: `node tests/static-check.mjs && node tests/run.mjs` (`-v` for details, `-vv 56,65` for named checks). Report pass/fail as N of N and failing lines only. Expected now: static PASS, runtime 73 of 73.
5. Ask the owner the open questions under "Next batch" in ONE AskUserQuestion before building.

## Status
- Batches 1-10 done on branch `batches-3-5`, remote at d51ecc9 (code commit 98aba5e). The owner has NOT yet said the loop works; no art before that.
- Built so far on boxes: map v2 (2 layers, collapses, hazards, altars), LoL/MLBB controls, fog of war, minimap, apex hunt (demon + 2 minions, skill transfer), royale cubs and plates, buff creatures from marble bags, 9 bots with a brain, royale end (loss banner with place; last suit standing wakes the demon), one-bot hunter slot.
- Static PASS. Runtime 73 of 73 (headless Chromium, software GPU: correctness and counts only). Fixed seed 12345. Checks 1-55 run with ?bots=0 (map test); 56-68 set bots themselves.
- Mutation rounds: batches 4-8 all caught (batch 7 12 of 13, the miss an equivalent change); batch 9 32 of 32; batch 10 6 of 6.
- Counts (software GPU, medium): spawn 27 calls / 2.8k tris; whole map 76 / 8.4k; hunt 17 / 0.9k; heaviest royale (10 suits, 7 cubs, tells) 53 / 3.0k. Budget 500 / 0.5M. Shader programs 3, geometry flat over 3 runs.
- Pathfinding: walk graph built at load (8114 nodes). Worst bot search 0.8 ms (1.8 ms unreachable), player right-click worst 4.0 ms (was 92 ms). At most one bot search per step.
- NOT run: real-GPU fps (needs a GitHub Actions macOS runner; no workflow yet). NOT tried on a real phone.
- Phone review link: https://claude.ai/artifact/3nQ67JCTmb1JfPKC3Y416z (version 1795414496-4791 = batch 10). Republish after each batch: copy index.html, swap the importmap path for https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.min.js, publish to slug 1688f9ba-a0e5-4f7b-ac2e-3a68d6fc67c3 (get_artifact first for base_version).
- Project docs (claude/HANDOFF.md, claude/GDD.md, claude/code/index.html, claude/code/tests/run.mjs, claude/code/tests/static-check.mjs) are copies of repo files. The LEAD session syncs them after each batch with project_write local_path (a background worker cannot). If a write is refused, project_read first (code files print in full: do it once, then write).

## Next batch: 11 = leader, crown marker, bounty decree (owner, 23 Nov 14:22: these are the next open items)
Not started. Design note below; readiness about 70 of 100 (GDD rules known, suit fields exist; leader rule details and the bounty/hunter-cap clash need the owner).

### Questions for the owner first (one AskUserQuestion; recommended option first)
1. Carried over from batch 10 (unanswered): the player is still out at 121-146 s in all 6 test matches, because 2-4 bots target the player by the nearest-suit and hit-back rules (not the on-sight switch). Options: (a) recommended: only one bot at a time may pick the player as target by any rule except hitting back; (b) cap everything, even hit-back; (c) keep as is.
2. Bounty vs the one-bot rule: when the PLAYER is the leader and the bounty is on, may more than one bot chase the player? (a) recommended: yes, up to 3 while the bounty lasts (the bounty is the brake); (b) no, the one-bot cap always holds.
3. Who the crown shows to: (a) recommended: HUD line "Leader: <school>" for everyone; crown over the leader only when the leader is in vision; during the bounty the leader also shows on the minimap; (b) crown always visible through fog.

### Design (GDD "The leader"; numbers in CONFIG.LEADER and CONFIG.BOUNTY, switch LEADER.on)
- Leader = suit with most plates held now (0-2), then most kills, then the current leader keeps it (no flip on a tie). Nobody leads until some suit holds 1 plate or has 1 kill. Re-checked on change events (plate gained or expired, kill, suit out), not every frame.
- Suits get a `kills` count (killer already recorded per out). Kills count suits only, not cubs.
- Crown marker: one small gold box-crown mesh built once at load, moved onto the leader's head; hidden when no leader, the leader is unseen (fog rule), or at the wake. Minimap: gold dot for the leader under the same visibility rule. HUD: one line, written only on change ("Leader: You" / school name).
- Bounty decree "A bounty lieth upon the leader." / plain rule "Bounty on the leader: break them for a full ultimate.": 5 s warning (voice, banner, rule line), lasts 40 s. Fires when the same suit has led for 25 s; once per leader; one decree at a time; none in the last 20 s before a collapse banner overlaps (queue it). Reward: the suit that breaks the leader during the bounty gets its ultimate cooldown reset (stand-in for "big ultimate charge" until charge exists). Leader out = bounty ends at once. Cancelled at the wake; reset on a new run.
- Bots: during the bounty, bots that can see the leader add CONFIG weight to fighting it (subject to the owner's answer to question 2); the leader bot plays safer (altar threshold up). Bots know who leads (the HUD tells everyone).
- This is the first decree: build the decree banner and timing as a small reusable piece (one decree at a time, warning, duration, end), so batch 12 decrees reuse it.

### Checks to add (tests/run.mjs, mutation round on each)
- Leader invariant every tick over the 6 seeded matches: the leader matches the rule from suit state; no flip on a tie; no leader before the first plate or kill.
- Crown: on the leader's head when seen, hidden when unseen or no leader; HUD text written only on change (count writes).
- Bounty: announced >= 5 s before it starts; reward only for breaking the leader during the bounty; ends when the leader is out; none in the hunt; new run x3 resets it; text keys exist.
- Bots: with the bounty on, bots fight the leader more (measured share), and the agreed cap holds (invariant).
- GDD sims, report the numbers: leader win share (GDD band 25-45%), player plate rate with average bots (GDD target: at least 1 plate in 70% of runs), match length still 165-255 s, player place and time out per seed.
- Budget with crown + all units, programs and geometry flat.

### Premortem
- Leader flips every frame on ties -> tie keeps the current leader; event-driven re-check.
- Bounty sends every bot at a player leader -> owner's answer to question 2, invariant check.
- Bounty and collapse banners collide -> queue; one banner at a time.
- Crown leaks the leader's position through fog -> visibility rule + check.
- Crown mesh added on first use causes a compile -> built and drawn once at load (warm-up list).
- Leader out by a fall: the bounty reward goes to nobody (cause 'fall'), the bounty ends.
- Hunt tests: the wake clears the crown and the bounty.

## Owner decisions (dated)
- 23 Nov 14:22: next open items are leader, crown marker and bounty decree (batch 11).
- 23 Nov 14:04: only one bot at a time may switch to the player on sight (built as batch 10, hunter slot).
- 23 Nov 14:04: apex hunt played by the owner: very hard but beatable. Cause per owner: the placeholder kit has no real skills; with real kits (dashes) the player can dodge apex attacks, which should balance it. No hunt tuning now; re-check the hunt sweep (test 42) when kits land.
- 23 Nov (batch 9): go 9a to 9d; bots use the placeholder kit; bots take plates and boons; bots go for the nearest seen suit but switch to the player on sight.
- 23 Nov: cubs and minions are four-legged machines on treads, faster than most suits (6.6 m/s vs 6); other numbers at the suits' median (read as health and damage once kits exist; confirm). Tread look waits for art.
- 23 Nov: buff creatures like a MOBA jungle crab and river wanderer, marble-bag draws for time, place, boon and size; own names and art (working: crab, wanderer).
- 23 Nov: cubs alive at the wake are seen going back to the statue (built as plates flying home during the 3 s wake; assumption).
- 23 Nov: order bots before decrees.

## As built: assumptions still standing (all in CONFIG; change by saying so)
- Batch 10 hunter slot: BOT.maxHunters 1; the slot frees when the hunter or the player is out, or after BOT.hunterLoseS 3 s without sight; a freed hunter drops the player at once. Other bots keep the nearest-suit and hit-back rules. 6-seed autopilot (seed / decided / place / player out / winner spawn): 12345 211 s / 7th / 146 s / 4; 2 183 / 9th / 122 / 8; 3 171 / 10th / 121 / 4; 4 179 / 10th / 122 / 0; 5 166 / 7th / 124 / 1; 6 181 / 9th / 121 / 7. Player out first in 2 of 6 (was 6 of 6).
- Batch 9 bots (CONFIG.BOT): all 'average' (0.3 s reaction). Player actions only; own vision only. Priority: leave a warned section > dodge a tell seen for its reaction time > altar under 40 hp (leave at 85) > fight > cub or buff creature > roam. R kept to finish a target or used under 50 hp; 0.8 s between a bot's skills. Pacing: until 120 s a bot only answers a suit that hit it and keeps 8 m from others; then its fight radius grows from 3 m to vision over 100 s (without it matches ended at 40-110 s). In a match the player out = frozen loss banner with place; last suit standing starts the hunt; H / Hunt button only with ?debug or no bots. Bot Q/W show no flash (only R shows its ring).
- Batch 8: marble bags (seeded mulberry32, draw without putting back): times [25, 35, 45, 55] s; 6 spots (warned/fallen/taken skipped); crab boons ult cut 20%, +10% dmg 40 s, heal 20; wanderer boons 2 hp/s 20 s, +3 m vision 40 s, +8% speed 30 s; amounts [0.5, 1, 1, 1.5]; stacks capped 1.4x. Creatures never attack; lost with a fallen section; cleared at the wake.
- Batch 7: kennel waves at 30, 90, 150, 210 s, 5 s warning; cubs at 80% hp, 60% damage, aggro 6 m, leash 12 m, heal 25/s at rest; plate to the last hitter, two 45 s slots; Stalker plate = bleed 4/s 3 s on hits; Howler plate = +10% speed; "+30% ultimate charge" = 30% of the ultimate cooldown removed until charge exists.
- Batch 6 hunt: arena = core hall, gate sealed, no altar; every enemy move shows its shape for the whole windup (all >= 0.4 s; Pounce 0.5 s); demon ultimate once at half health (8 s, +40% speed, +30% damage); killed minion's plate flies to the demon (0.9 s) with its 2 skills; win/loss freeze; ending (winner becomes the statue) not built.
- Hunt bot sweep (test 42): never-dodge loses all; 0.3 s reaction wins minions-first only; 0.15 s wins all. GDD target "no kill order dominant" not met (placeholder kit; owner: wait for kits).
- Cub farm bot (test 51): 2 plates in 170 s, never hit; cubs may be soft for a dodging player.

## Working notes
- Long batches ran as one background worker (fork) per batch set, one writer; the lead stayed free, verified with git ls-remote, a full check run and get_artifact before reporting, then synced project docs. Worker log: /home/claude/batch9.log (session disk only).
- Backups before each batch: outside the repo (/home/claude/backup, session disk); git history is the durable record.
- Mutation rounds: copy index.html aside, apply one deliberate bug, run tests/run.mjs, confirm the named check fails, restore, compare with cmp.
- A full run takes about 60-90 s now (whole-match checks). Hooks step the game synchronously inside page.evaluate, so checks are deterministic.
- Commits: name 'Claude', email noreply@anthropic.com, attribution lines at the end; secret scan before push; push with `-c push.negotiate=true`.
- Owner works from a phone: short reports, pass/fail as N of N, failing lines only; no deadline talk.

## Files
- index.html: whole game (one module script, CONFIG block at top, TEXT keys, map data). lib/: three.js r171 (MIT).
- tests/static-check.mjs: per-frame rules, text keys, CONFIG comments, syntax, no Math.random. tests/run.mjs: 73 checks (33-45 apex hunt, 46-51 royale minions, 52-55 bags and buff creatures, 56-58 bot movement, 59-63 bot brain, 64-66 royale end and whole matches, 67-68 hunter slot).
- Suit object: SUITS[0] is the player (still named P in code); fields include hp, dead, cause, diedAt, killer, plates, boons, pk/pt (plate slots), bT/bV (boons). Generic helpers: hurtSuit(s, n, cause, by), suitDown, tickSuit, stepBody, hitTarget(by, d, n), hasPlate(s, k), cutUlt(s, sec).
- Bot hooks: setBots, bots, botDbg, placeBot, hitBot, hitBy, setBotHp, setBotCd, hitCubBy, hitNeutralBy, autoPlayer, setWatch, royale, player, navTime, navNodes, setTime, hunters. ?bots=N sets the bot count.
- Test hooks: window.__game (step, setMove, teleport, moveTo, attack, cast, aimKey, render, state, startHunt, hunt, huntUi, cubs, neutrals, drawBag, setSeed, ...). ?lock locks the tier; ?debug shows counts and enables the M overview.

## Decisions (user, 23 Nov)
- Lore: Kaymuse on a throne in the core hall, the apex as a tiger statue under her; minions are the demon's shed plates (royale: plate buffs the killer; apex phase: plate flies home to the demon). Ending: even the winner becomes the next tiger statue; next run's statue wears the last winner's school colour (WINNER_STATUE, not built yet).
- Kaymuse voice: always haughty, imperial "We/Our" (朕), archaic English; HUD and rule text plain modern English. Closing line LOCKED: "Heaven chose thee. We chose what thou wouldst become."
- Royale minions give a lead (plate: +30% ult charge, 45 s buff); bounty decree is the brake.
- Map v2: 1.5x size; upper layer at 4 m; open drops (8 dmg); rails, 4 broken gaps (knockback only); statue and 4 stone lions strike after a 0.6 s red ring; 3 healing altars.
- Camera: follow, pitch 40, distance 14.
- Minimap (desktop bottom-right, phone top-left). Fog of war: vision 11 m, units beyond hidden, no full-map view.
- Controls: desktop LoL/Dota (right-click move/attack, Q W R hold-aim release-cast, A attack-move, S stop); phone MLBB (stick, ATK auto-target, tap skill = auto-aim, drag = aim, Cancel zone).

## Open
- Owner answers for batch 11 (see Next batch questions 1-3).
- Kaymuse's look; game title; apex ultimate rule (built: single use at half health; confirm); ultimate charge amounts; minion names; Tiger Demon hard-surface confirm.
- Apex balance: wait for real kits, then re-check test 42.
- Vision is a plain radius: walls/curtains do not block sight yet (comes with hiding).
- Other decrees (batch 12+), hiding, ultimate charge, school kits, the ending.
- Apex trigger: teleport to the core hall (assumed) or walk there.
- Organiser answer on eligibility; OpenGame CLI test. Real-GPU fps workflow; real phone run.
- Placeholder skills and 3 training dummies are map-test only; replaced by kits.
