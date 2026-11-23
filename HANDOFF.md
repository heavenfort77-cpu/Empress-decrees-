# Handoff (2026-11-23, after batch 12; written for a fresh session). GDD: docs/GDD.md (also Project "empress decrees", claude/GDD.md)

## Session start (every session)
1. Attach both repos: add_repo heavenfort77-cpu/Empress-decrees- (access push) and heavenfort77-cpu/dawnpunk (read; public, anonymous clone works). Dawnpunk = reference for frame-rate rules and bug pitfalls; read only the part needed.
2. Clone with `--no-single-branch`; check out `batches-3-5` (PR #1 still open, not merged; use main only if it is merged: `gh api repos/heavenfort77-cpu/empress-decrees-/pulls/1 --jq .merged`, GraphQL is blocked).
3. Read this file, then only the GDD section being changed. Do not read the whole codebase.
4. Run the checks before and after any change: `node tests/static-check.mjs && node tests/run.mjs` (`-v` for details, `-vv 56,65` for named checks). Report pass/fail as N of N and failing lines only. `-sims` prints the GDD sim numbers. Expected now: static PASS, runtime 87 of 87.
5. Ask the owner the open questions under "Next batch" in ONE AskUserQuestion before building. Open design questions go to the panel (owner, 23 Nov 15:11).

## Status
- Batches 1-12 done on branch `batches-3-5` (PR #1 open). The owner has NOT yet said the loop works; no art before that.
- Built so far on boxes: map v2 (2 layers, collapses, hazards, altars), LoL/MLBB controls, fog of war, minimap, apex hunt (demon + 2 minions, skill transfer), royale cubs and plates, buff creatures from marble bags, 9 bots with a brain, royale end, player-target cap (hunter slot), leader + crown + HUD line, decree slot, bounty decree, five bagged decrees, W dash, slow + mark penalty.
- Static PASS. Runtime 87 of 87 (headless Chromium, software GPU: correctness and counts only). Fixed seed 12345. Checks 1-55 run with ?bots=0 (map test); 56+ set bots themselves. Whole-match checks (65, 67, 69, 72, 78) run 12 seeds since batch 12 (was 6).
- Mutation rounds: batches 4-8 all caught (batch 7 12 of 13, the miss an equivalent change); batch 9 32 of 32; batch 10 6 of 6; batch 11 10 of 10; batch 12 14 of 14 (first round 12 of 13: check 80 marked before the wake too early; fixed; plus check 82 catches the replay fix reverted). Script: /home/claude/probe12/mut.py (session disk).
- Counts (software GPU, medium): spawn 27 calls / 2.8k tris; whole map 76 / 8.4k; hunt 17 / 0.9k; heaviest royale (10 suits, 7 cubs, tells) 53 / 3.0k; with the crown 54 / 3.0k; with 10 marks, crown and zone tint 64 / 3.1k. Budget 500 / 0.5M. Shader programs 3, geometries 96 flat (mark marker +1).
- Batch 12 GDD sims (12 seeds, autopilot player, average bots): decided 166.4-201.2 s (in 165-255); longest leader won 3 of 12 (25%, band 25-45%: at the bottom edge); player took >= 1 plate in 2 of 12 (target 70%: MISSED); player out 76-177 s (won 3 of 12: seeds 5, 10, 11); bagged decrees per match 1-3 (GDD 3-4: MISSED); bounties 0-2 per match (6 in 12 matches; batch 11 had 8 in 6: the shared slot halves them), bot fighting share on a seen leader 0.75 with the bounty vs 0.06 without; decree breaks: player 0, bots 7 (all seed 3: a heights decree over a collapse forced a crossing). Player never marked in matches (autopilot obeys), so the mark cap is proven by the scripted check 77 only.
- Hunt sweep with the W dash (test 42, the sweep bot dashes out of seen tells): never-dodge loses all; 0.3 s wins howler-first only (batch 11: minions-first only); 0.15 s wins 2 of 3 (lost demon-first; batch 11: all 3).
- Pathfinding: walk graph built at load (8114 nodes). Worst bot search 0.8 ms (1.8 ms unreachable), player right-click worst 4.0 ms. At most one bot search per step.
- NOT run: real-GPU fps (needs a GitHub Actions macOS runner; no workflow yet). NOT tried on a real phone.
- Phone review link: https://claude.ai/artifact/3nQ67JCTmb1JfPKC3Y416z. Republish after each batch: copy index.html, swap the importmap path for https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.min.js, publish to slug 1688f9ba-a0e5-4f7b-ac2e-3a68d6fc67c3 (get_artifact first for base_version). Live: version 1795421416-227f = batch 12 (6ab86c8).; batch 12 republish is done by the lead.
- Project docs (claude/HANDOFF.md, claude/GDD.md, claude/code/index.html, claude/code/tests/run.mjs, claude/code/tests/static-check.mjs) are copies of repo files. The LEAD session syncs them after each batch with project_write local_path (a background worker cannot). If a write is refused, project_read first (code files print in full: do it once, then write).

## Next batch: 13 (not chosen yet; ask the owner)
Open items: decrees per royale under the GDD 3-4 (cause: the batch 11 queue keeps decree warnings 20 s clear of collapse warnings, and the bounty shares the slot; options: shorter clearS, or let a decree run over a collapse) - owner or panel; player plate rate and leader win share (tune or wait for kits); heights decree over a collapse forces a crossing (fair penalty or skip heights while a collapse is warned?); hiding; ultimate charge (bounty reward and ultimates 2x are cooldown stand-ins); school kits (W dash is a placeholder); the ending.

## Owner decisions (dated)
- 23 Nov 15:13: go for batch 12 (built as below).
- 23 Nov 15:11 panel votes (batch 12): (1) placeholder W becomes a 4 m Dash, burst on landing, dash flag (6-1); (2) bridges: true silence with 'Silenced' feedback (7-0); (3) a marked suit: up to 2 bots may target it (4-2-1); (4) 'Our roof' becomes 'Our heights' (whole upper level) (5-2); (5) her break line, gold zone tint and outline, dry altars look empty (7-0); (6) ultimates 2x and altars dry as written.
- 23 Nov 15:1x (batch 12 questions): bags draw decree, gap, length and zone; all 5 decrees now, none cut later; breaking = slow + mark; design note first, no code yet.
- 23 Nov 15:11: open design questions go to the panel (judges, players, critics); propose, debate, improve, vote; follow the majority. Batch 12 results under "Panel decisions".
- 23 Nov 15:06: decrees also use marble bags.
- 23 Nov 14:35 (batch 11 questions): (1) only one bot at a time may target the player by any rule except hitting back (BOT.maxHunters 1); (2) while the bounty lies on the player, up to 3 bots may (BOUNTY.maxHunters 3); (3) HUD line "Leader: <school>" for everyone, crown over the leader only when the leader is in vision, the leader on the minimap during the bounty (otherwise normal vision).
- 23 Nov 14:22: next open items are leader, crown marker and bounty decree (batch 11).
- 23 Nov 14:04: only one bot at a time may switch to the player on sight (built as batch 10, hunter slot).
- 23 Nov 14:04: apex hunt played by the owner: very hard but beatable. Cause per owner: the placeholder kit has no real skills; with real kits (dashes) the player can dodge apex attacks, which should balance it. No hunt tuning now; re-check the hunt sweep (test 42) when kits land.
- 23 Nov (batch 9): go 9a to 9d; bots use the placeholder kit; bots take plates and boons; bots go for the nearest seen suit but switch to the player on sight.
- 23 Nov: cubs and minions are four-legged machines on treads, faster than most suits (6.6 m/s vs 6); other numbers at the suits' median (read as health and damage once kits exist; confirm). Tread look waits for art.
- 23 Nov: buff creatures like a MOBA jungle crab and river wanderer, marble-bag draws for time, place, boon and size; own names and art (working: crab, wanderer).
- 23 Nov: cubs alive at the wake are seen going back to the statue (built as plates flying home during the 3 s wake; assumption).
- 23 Nov: order bots before decrees.

## As built: assumptions still standing (all in CONFIG; change by saying so)
- Batch 12 decrees (CONFIG.DECREES, switch on): bags (own seeded generator DRNG, so creature bags draw the same) for which, first [35, 45], gap [10, 15, 20, 25] after a decree ends, length [30, 35, 40, 45], zone (all 12 sections; fallen or warned skipped). A bagged request is drawn when its warning can start (place re-checked then); none left = retry in 5 s. Bagged decrees run only in a match (bots > 0), like the leader. A due bounty takes the place of a bagged request that is queued but not yet told (assumption: the bounty is the brake). The no-dash zone is tinted gold from the warning on.
- Batch 12 heights: standing (not airborne) at or above 3 m; breaks again every 2 s. Bots: leave the upper level from the warning on (flee search to a node under 2.5 m), skip high roam goals, altars and creatures, and their path search avoids every floor that reaches 3 m (whole ramps included). A bot crossing the upper level to leave a warned section breaks it (counted).
- Batch 12 dash (CONFIG.SKILLS[1]): 4 m in 0.2 s, always full length in the aim direction, steps of 0.33 m by the walking rule (a refused point ends it), the burst (2.5 m, 20) lands where it ends; no cast while dashing; a stun ends it. Bots dash at a target 3-5.5 m away on about its layer (BOT.dashMinM/dashMaxM), not inside the no-dash zone.
- Batch 12 silence: the caster's floor decides (a bridge section); bots and the autopilot do not cast there; the basic attack still works.
- Batch 12 mark: a marked suit is seen by every bot and by the player from anywhere (body, minimap dot with a red ring); target rules otherwise unchanged; player mark = cap 2 (bounty on the player = 3).
- Batch 12 fixes found while testing: bots already out keep their cause at the wake (lost when the player won the royale); every run of a seed starts alike (warnGen restarted after clearLeader; autopilot brain fields reset).
- Batch 11 leader (CONFIG.LEADER, switch on): most plates held now, then kills (suits only); a tie keeps the current leader; on a tie among new suits (old leader out) the first in suit order (player, then bots 1-9); nobody leads before 1 plate or 1 kill, or with every suit back at 0 plates and 0 kills. Re-checked on plate gained or expired, kill, suit out; only in a match (bots > 0). Crown = gold hexagonal box on the leader's body group (hidden with it), warmed at load. School names on the HUD for bots 1-9 follow the GDD table order (Dao ... Nong); the player is "You".
- Batch 11 decree slot (CONFIG.DECREE): one decree at a time; a request queues until the banner is free, no collapse warning starts within 20 s and no kennel warning within the 5 s warning; then 5 s warning (voice, banner, rule countdown), then in force; other notes (plate taken, fell) are skipped while the decree banner shows.
- Batch 11 bounty (CONFIG.BOUNTY): after 25 s of one leader, once per suit per run, 40 s. Ends at once when that suit is out or stops leading (assumption), at the wake and on a new run. Reward: the suit that breaks the leader while it is in force gets its ultimate cooldown reset (a fall or a test kill pays nobody; breaking it during the warning pays nothing). Bots that see the leader take it up with chance 0.6 (drawn once per bot per bounty), before new fights and also during the peace time; a bot leader under its bounty goes to an altar under 55 hp (40 otherwise). HUD shows "(bounty N s)".
- Batch 11 pacing: BOT.engage.p0 0.15 -> 0.1 to keep matches in 165-255 s after the cap and bounty (0.15 gave 149-225 s over 12 seeds, seed 4 159.9 s; 0.1 gives 180-224 s).
- Batch 11 hunter slot: the slot now covers every reason to fight the player but hitting back (nearest suit, a fight going on, on sight, bounty); hit-back fights are never capped, which is why the autopilot player is still out at 106-132 s (it starts fights at 120 s and the bots answer).
- Batch 10 hunter slot (now widened by batch 11): BOT.maxHunters 1; the slot frees when the hunter or the player is out, or after BOT.hunterLoseS 3 s without sight; a freed hunter drops the player at once. Other bots keep the nearest-suit and hit-back rules. 6-seed autopilot (seed / decided / place / player out / winner spawn): 12345 211 s / 7th / 146 s / 4; 2 183 / 9th / 122 / 8; 3 171 / 10th / 121 / 4; 4 179 / 10th / 122 / 0; 5 166 / 7th / 124 / 1; 6 181 / 9th / 121 / 7. Player out first in 2 of 6 (was 6 of 6).
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
- tests/static-check.mjs: per-frame rules, text keys, CONFIG comments, syntax, no Math.random. tests/run.mjs: 87 checks (33-45 apex hunt, 46-51 royale minions, 52-55 bags and buff creatures, 56-58 bot movement, 59-63 bot brain, 64-66 royale end and whole matches, 67-68 hunter slot, 69-74 leader, crown, bounty, player cap, budget with crown, 75-81 decree bags, the five decrees, penalty and mark, decrees in matches, W dash, wake/new run/keys, budget with marks, 82 replay of one seed).
- Suit object: SUITS[0] is the player (still named P in code); fields include hp, dead, cause, diedAt, killer, plates, boons, pk/pt (plate slots), bT/bV (boons). Generic helpers: hurtSuit(s, n, cause, by), suitDown, tickSuit, stepBody, hitTarget(by, d, n), hasPlate(s, k), cutUlt(s, sec).
- Batch 11 hooks: leader, suitsState, plateTo, decreeKeys, ultOf; hunters() now has capOnP and max = current cap.
- Batch 12 hooks: decree, forceDecree(key, zone, len, next), setDecNext, drawDecBag, pickDec, suits, sees, zoneTinted, breakBy, setFace, startState; hunters() has bountyP and markP; bots() list has markT, breaks, cd.
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
- Owner: pick batch 13 (see Next batch); tune or wait on the plate rate and leader win share (Status).
- Kaymuse's look; game title; apex ultimate rule (built: single use at half health; confirm); ultimate charge amounts; minion names; Tiger Demon hard-surface confirm.
- Apex balance: wait for real kits, then re-check test 42.
- Vision is a plain radius: walls/curtains do not block sight yet (comes with hiding).
- Decrees per royale under the GDD 3-4; hiding, ultimate charge, school kits, the ending.
- Apex trigger: teleport to the core hall (assumed) or walk there.
- Organiser answer on eligibility; OpenGame CLI test. Real-GPU fps workflow; real phone run.
- Placeholder skills and 3 training dummies are map-test only; replaced by kits.
