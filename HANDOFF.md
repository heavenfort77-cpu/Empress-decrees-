# Handoff (2026-11-23, after batch 10; written for a fresh session). GDD: docs/GDD.md (also Project "empress decrees", claude/GDD.md)

## Session start (every session)
1. Attach both repos: add_repo heavenfort77-cpu/Empress-decrees- (access push) and heavenfort77-cpu/dawnpunk (read; public, anonymous clone works). Dawnpunk = reference for frame-rate rules and bug pitfalls; read only the part needed.
2. Read this file, then only the GDD section being changed. Do not read the whole codebase.
3. Run the checks before and after any change: `node tests/static-check.mjs` then `node tests/run.mjs` (`-v` for details). Report pass/fail and failing lines only.

## Status
- Batches 1-10 done. All code is on branch `batches-3-5` (PR #1 open; merge to main when the user agrees). The owner has NOT yet said the loop works; no art before that.
- Batch 6 = apex fight on boxes (H key or Hunt button). Batch 7 = royale minions (kennel waves, cubs, plates). Batch 8 = faster cubs and minions, buff creatures from marble bags, cubs fuse into the statue at the wake.
- Static check PASS. Runtime 73 of 73 PASS (headless Chromium, software GPU: correctness and counts only). Tests run with a fixed seed (12345); checks 1-55 run with ?bots=0 (map test), 56-68 set the bots themselves. `node tests/run.mjs -vv 56,65` prints full details.
- Mutation rounds: batch 3 edge clamp caught after a fix; batch 4 5 of 5; batch 5 6 of 6; batch 6 11 of 11; batch 7 12 of 13 (the miss is an equivalent change); batch 8 11 of 11; batch 9 32 of 32 (9a-9d); batch 10 6 of 6.
- Counts (software GPU, medium tier): spawn 27 calls / 2.8k tris; whole map 76 / 8.4k; hunt with all units and 3 tells 17 / 0.9k; 7 cubs with 3 tells 33 / 2.3k. Budget 500 / 0.5M. Shader programs 3 at load and after play; geometry count flat.
- Bot sweep in the hunt (test 42) with the faster minions, reaction / kill order (0 demon, 1 stalker, 2 howler): never-dodge loses all 3 (7-8 s); 0.3 s: demon-first loses (17 s), minions-first wins (57 s, 3-13 hp left); 0.15 s wins all 3.
  - GDD sim target "no kill order is dominant" is NOT met (minions-first is better for the 0.3 s bot). Player kit is still the placeholder; tuning waits for real kits.
- Cub farm bot (test 51, 0.3 s reaction, 170 s at the west camp): 2 plates, never hit. Cubs may be too soft for a player who dodges.
- NOT run: real-GPU fps (needs a GitHub Actions macOS runner; no workflow yet). NOT tried on a real phone (touch checked by simulated pointer events only).
- Phone review link (claude.ai artifact, same page with three.js from jsDelivr): https://claude.ai/artifact/3nQ67JCTmb1JfPKC3Y416z (version 1795414496-4791 = batch 10, commit 98aba5e; title 'Empress Decrees - box prototype (batch 10)'). Republish it after each batch: copy index.html, swap the importmap path for https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.min.js, publish to slug 1688f9ba-a0e5-4f7b-ac2e-3a68d6fc67c3.
- Project docs (claude/HANDOFF.md, claude/GDD.md, claude/code/index.html, claude/code/tests/run.mjs) are copies of the repo files; rewrite them after each batch. A project_read of a code file dumps the whole file into the session: avoid it, write from the local file.

## Next batch: 11 = decrees (owner order: bots before decrees). Waiting for the owner's go. Also open: player still out early (batch 10 below), real-GPU fps, real phone.

## Batch 10 = hunter slot (owner, 23 Nov 14:04: only one bot at a time may switch to the player). DONE 23 Nov.
- Built: one hunter slot (CONFIG.BOT.maxHunters 1). A fighting bot that sees the player takes the slot only if it is free, then targets the player. The slot frees when the hunter is out, the player is out, or the hunter has not seen the player for BOT.hunterLoseS (3 s, assumption); a freed hunter drops the player at once. Switch still BOT.preferPlayerOnSight.
- Assumptions: the other bots keep the nearest-suit rule (after the 2:00 truce the player can still be their nearest suit) and still hit back at whoever hit them; only the on-sight switch is limited.
- Checks: 67 (invariant every tick over the 6 matches of 65: at most maxHunters bots on the player by the switch; slots, flags and targets agree; 3+ bots saw the player in 10908 ticks), 68 (slot frees on hunter death and another claims it; held under 3 s out of sight, freed after; claimed again). Check 59 changed on purpose: with one slot either of its 2 bots may take it first, so 59 opens a second slot while it tests the switch itself, then restores it. New test hooks: hunters(), setBotHp(i, n). Mutation 6 of 6.
- 6 autopilot matches (seed / decided s / player place of 10 / player broken at / first bot out / winner spawn): 12345 211.3 / 7th / 146 s / 121 s / 4; 2 182.7 / 9th / 122 s / 60 s / 8; 3 170.7 / 10th / 121 s / 130 s / 4; 4 178.5 / 10th / 122 s / 123 s / 0; 5 165.7 / 7th / 124 s / 121 s / 1; 6 181.1 / 9th / 121 s / 121 s / 7.
  - Before batch 10 the player was out first in 6 of 6; now first in 2 of 6, still always at 121-146 s, just after the truce ends (120 s). While alive, 2-4 bots still had the player as target at once (nearest-suit and hit-back rules, not the switch). Not changed: the owner decides whether the nearest/hit-back rules should also count toward the cap.

## Batch 9 = bots (owner, 23 Nov: bots are what make the royale end and start the hunt on its own). DONE 23 Nov, commits 870fa84 (9a), 5e0e7cc (9b), 1aaf1d0 (9c), 9d below.
Owner said go for 9a to 9d on 23 Nov (see Owner decisions). Progress:
- 9a DONE: suit refactor. P stays the name of SUITS[0] (no 390-line rename); generic: hurtSuit(s, n, cause, by), suitDown, suitFell, tickSuit, suitSpeed, stepBody (knockback, walk, floors, void), tryMove(s, ...), hitTarget(by, d, n), hasPlate(s, k), cutUlt(s, sec). Hazards and altars loop over SUITS; enemy moves hit every suit in the shape; cubs pick the nearest suit on their layer (u.tgt) and keep it to the leash; plates and boons go to the last hitter (u.by, bleed kills to u.bleedBy). Static check PASS; runtime 60 of 60; counts unchanged (27/2.8k, 76/8.4k, hunt 17/0.9k). Mutation 9 of 9 (the x-axis knockback mutation was missed at first: test 20 now also knocks sideways through the west terrace gap). Static check now also fails on Math.random (mutation caught).
- 9b DONE: bot bodies and movement. 9 bots (box suits, school colours, health bars) spawn at the 9 other spawns; they roam to random spots on safe sections (9c replaces this with the brain). ?bots=N or __game.setBots(n); the map-test checks run with bots=0 (URL in tests/run.mjs).
  - Pathfinding cause: navSearch did the walking rule live per neighbour; measured headless 15.3 ms median, 58.7 p95, 92 ms worst, 192 ms for an unreachable goal (this also hit the player's right-click). Removed by: a walk graph built once at load (8114 nodes, 8 links each, a floor mask per node so fallen floors switch nodes off). Proof (scripts/bench2 in session, 182 searches): bots (turn points only) median 0.1, p95 0.6, max 0.8, unreachable 1.8 ms; player (straight-walk smoothing kept) median 1.2, max 4.0 ms. At most one bot search per step (round robin; check 56 gates the peak).
  - Fixes found by the bot runs: (1) a suit whose edge lost its floor when a neighbour section fell could not move at all (centre on C2, body over the fallen bridge): tryMove now allows steps that keep the centre on a floor while unsupported (player too). (2) bots cutting a corner clipped pillars or bridge edges: they now land exactly on cell centres and a path starts at the start node's centre.
  - New checks 56-58 (63 of 63): roam 230 s on a floor every tick, never stuck > 3 s (measured 0.62 s; measure = wanting to move without getting 1 m away, not reset by new goals), path searches per step peak 1, seen only inside vision, every out bot has a cause; budget 10 suits + 7 cubs + 4 tells = 52 calls / 2.7k tris, programs 3, geometry 94 flat; 3 runs with bots, memory flat. Mutation 8 of 8. Without dodging, roaming bots die to the lions and the statue (fixed by the 9c brain).
- 9c DONE: bot brain (CONFIG.BOT). Player actions only (walk, basic attack, Q W R with the placeholder kit; aim error from the skill profile; 0.8 s between two skills; R shows its ring for its whole 1 s delay and is kept to finish a target or used under 50 health). Knows only its own vision (11 m + vision boon) and the map layout. Priority each step: leave a warned section (shortest walk off it, own search) > dodge a tell seen for its reaction time (hazards, cubs, other bots' and the player's R) > altar under 40 health (leaves at 85) > fight > cub or buff creature (drawn by aggro) > roam (paths avoid warned sections, re-planned when a new warning starts). The player is just another target, except the owner rule: a fighting bot that sees the player switches to the player.
  - Pacing (assumption, all in CONFIG.BOT.engage; change by saying so): until 120 s a bot only answers a suit that hit it (4 s) and keeps 8 m from other suits; then the radius in which it starts a fight grows from 3 m to its vision over 100 s, starting with a 15% chance per suit (declined suits are drawn again after 4 s). Without this the bots spawn in pairs 14 m apart and the royale was over in 40-110 s.
  - Bot-only matches (player parked, invulnerable; session scratch runs, seeds 12345, 2-8): royale decided at 185, 199, 173, 163, 235, 246, 217, 215 s. 3 of 64 bot deaths were collapse falls (late drops off a terrace into a section warned seconds before).
  - New checks 59-63 (68 of 68): target rule (answers its attacker, switches to the player on sight, keeps the player while seen, lets go out of sight); plates and boons to the bot that took them, none to the player; dodge a stone lion 8 s with no damage; two bots fighting on the roof leave it in the 5 s warning; heal at an altar. Mutation 7 of 7 (the flee check was first passing without flee: rewritten with two fighting bots).
  - Test autopilot __game.autoPlayer(on): the same brain drives the player (checks only).
- 9d DONE: royale end. In a match (bots > 0) the player broken or fallen = frozen loss banner (Kaymuse line, 'Place N of 10', New run button / N); no map-test respawn. The last suit standing starts the hunt by itself. H and the Hunt button only with ?debug or with no bots (map test). __game.setWatch(on) keeps the bots going after the player is out (checks only).
  - New checks 64-66 (71 of 71): royale end flow; 6 whole matches with the player on autopilot: decided at 211, 181, 196, 206, 188, 209 s (band 165-255 = about 3-4 min), 0 broken invariants (alive count only falls, live suits on a floor with health in range, out bots not drawn), every out has a cause, bots took 14 plates and 22 boons, 6 different winning spawns; idle player loses (fell with W2 at 141 s). Mutation 8 of 8.
  - Seen in those runs, for the owner: the autopilot player (average bot) was the first suit broken in all 6 matches, at 121-146 s, i.e. right after the 2:00 peace. Cause: the owner's rule (bots switch to the player on sight) makes every fighting bot nearby go for the player at once. A real player can run, but the royale is hard. Options: keep; or only one bot at a time may switch (CONFIG); or shorten the switch to bots already fighting within N m. Not changed.
- Goal: 9 bot suits so the royale plays out and the last suit alive wakes the demon without the H key. Then leader, crown marker and bounty become possible; decrees come after.
- Readiness now about 75 of 100: audit done (below); Dawnpunk read (src/bots.js: its bots are test players, not opponents; patterns taken: bots use only the player's actions, skill profiles {react, hit} in CONFIG, waypoint walk between floors). Unknown: navSearch worst-case time (measured first in 9b).
- Audit (P.* references per function, index.html @ 89629c9): step 125, reset 28, updateStatus 23, startHunt 23, respawn 17, resolveMove 17, placeView 11, hurt 9, castSkill 9, grantPlayerPlate 7, stepUnit 6, applySkill 6, grantBoon 5, stepKennel 4, drawMini 4, cubThink 3; the ~39 in the test-hook object stay player-only. navSearch writes one shared PATH (1024 floats); grid A* 1 m cells, cap NAV_MAX 15000 nodes per search.

### Split into four batches, one scope each; each passes static + full runtime suite + budget before the next
- 9a Suit refactor, no bots spawned. P becomes SUITS[0]; per-suit state (pos, layer, hp, statuses, plates pk/pt, boons bT/bV, orders, path). hurt(s, n, cause). Hazards, altars, collapse falls, void, cubs, royale units and neutrals loop over live suits or pick the nearest suit on the same layer; plates and boons go to the last hitter. Player attacks can hit suits. Gate: 60 of 60 unchanged with 0 bots, counts unchanged, mutation round on the new loops.
- 9b Bot bodies and movement. 9 box suits at spawn points (school colours, one shared geometry). Path buffer per suit (one Float32Array 10x1024 allocated at load). Nav budget: at most one navSearch per tick, round-robin queue; straight steering when the goal is in line of walk. Measure navSearch worst case first; if over 2 ms, lower NAV_MAX for bots or add section waypoints. Gate: budget with 10 suits + 7 cubs + 3 tells, no bot stuck > 3 s, memory flat over 3 runs.
- 9c Bot brain. Uses only player actions (move, attack, Q W R). Knows only what its own 11 m vision shows (no map hacks). Priority list with CONFIG weights: leave a warned section > dodge a tell older than its reaction time > altar when hp low > fight nearest seen suit > contest camp or buff creature > walk toward centre. Skill profiles {react, hitChance, aggro} in CONFIG.
- 9d Royale end. Player dead = loss screen with Retry (replaces map-test respawn). Last suit alive = startHunt; H only with ?debug. Checks: match length 3-4 min band, every bot death has a cause (hit, fall, collapse), idle player loses, win share per spawn, invariants every tick (hp in range, alive count only falls, no suit inside a solid), hunt tests still pass.

### Bot rules (owner answers 23 Nov, plus one assumption)
1. Owner: bots use the player's placeholder kit until school kits exist.
2. Assumption: all bots "average" (0.3 s reaction), set per bot in CONFIG.
3. Owner: bots also take plates and boons.
4. Owner: bots attack the nearest suit they can see, but once a bot sees the player it switches to the player and keeps that target while the player stays seen (BOT.preferPlayerOnSight).

### Premortem
- 9 searchers spike a tick: one search per tick cap + measured cost.
- Bots fall at broken rails only by knockback, never walking in (nav already blocks drops).
- A cub leashing between two suits: cub keeps its first target until leash or death.
- Plates and boons to bots: HUD writes only for SUITS[0]; pool counts unchanged.
- Hunt tests: startHunt removes all bots before the wake; hunt runs as today.
- Fixed seed covers bot decisions too (one shared seeded RNG, no Math.random in bot code: static check).

## Owner decisions, 23 Nov (later session)
- 23 Nov 14:04: only one bot at a time may switch to the player on sight (built as batch 10, hunter slot).
- 23 Nov 14:04: apex hunt played by the owner: very hard but beatable. Cause per owner: the placeholder kit has no real skills; with real kits (dashes) the player can dodge apex attacks, which should balance it. No hunt tuning now; re-check the hunt sweep (test 42) when kits land.
- Batch 9 (session 3): go 9a to 9d back to back; bots use the placeholder kit; bots take plates and boons; bots go for the nearest seen suit but switch to the player on sight.
- Cubs and minions that move on the map are four-legged machines on treads, faster than most suits; their other numbers are to sit at the suits' median. Built now: speed 6.6 m/s against the suit's 6. The tread look waits for the art stage. "Median" is read as health and damage at the median of the ten suits once kits exist (assumption; confirm).
- Buff creatures in the manner of a MOBA jungle crab and river wanderer, with marble-bag draws for time, place, boon and size. Own names and art only (working names: crab, wanderer).
- Cubs alive at the wake must be seen going back to the statue. Built as plates flying home during the wake (a run across the map does not fit in 3 s; assumption).
- Order: bots before decrees.

## Batch 8 as built (assumptions, all in CONFIG; change by saying so)
- Marble bags (CONFIG.BAGS): draw without putting back, refill and reshuffle when empty. Seeded (mulberry32); a new seed each run, `__game.setSeed(n)` fixes it.
  - times [25, 35, 45, 55] s: until a creature appears, from the run start and then from its death or loss. One crab and one wanderer at most.
  - spots: 6 places (W2, E2, W1, E1, C1, C2); a spot whose section is warned or gone, or already taken, is skipped.
  - crab boons: ultimate cooldown cut 20% (stand-in for exp or charge), +10% damage 40 s, heal 20. Wanderer boons: 2 HP/s for 20 s, +3 m vision 40 s, +8% speed 30 s.
  - amounts [0.5, 1, 1, 1.5] multiply the boon. All stacks capped at 1.4x (BONUS_CAP).
- The creatures never attack. Crab 110 hp scuttles side to side; wanderer 70 hp walks a small circle. Announced by Kaymuse with the zone; yellow dot on the minimap when seen. Last hit takes the boon at once.
- Lost with a fallen section (no boon). Cleared at the wake. Boons and plates carry into the hunt. Switch: NEUTRALS.

## Batch 6 as built (assumptions, all in CONFIG; change by saying so)
- Arena = core hall; the gate seals for the hunt (APEX.gateZ). No altar inside, so no healing in the hunt.
- Player is placed at the hall entrance at once (no card yet). Collapses stop; a warned section is called off.
- Statue mesh and its solid are removed while the demon is awake; both return on a new run (N).
- Every enemy move shows its shape for the whole windup; the hit lands only if the player is still inside. All windups >= 0.4 s. Pounce windup is 0.5 s (GDD said 320 ms; the fairness rule of 0.4 s won).
- Demon: Claw, Pounce, Metal roar (40% slow 2 s). Ultimate = one use at half health (DEMON_ULT.mode 'once50'; 'cooldown' also built): 8 s, +40% speed, +30% damage.
- Stalker: Bite, Lunge, Rend (bleed 2/s for 4 s, 3 stacks). Howler: Bite, Flank (lands behind the player, 0.6 s stun), Howl (20% slow 3 s; the reveal part waits for hiding).
- Skill transfer: a killed minion's plate flies to the demon (0.9 s, always shown); on arrival the demon holds both of its skills (6 total). Stolen moves keep the minion's tell colour (purple / cyan).
- Pounce does not shed extra cubs yet. Units do not block each other or the player. Enemy immunity to stun/slow in frenzy is not needed yet (the player has no stun or slow).
- Win: sim freezes, closing line, time. Loss: sim freezes. H / Retry button = hunt again; N = new run. The ending (winner becomes the statue) is not built.
- Also fixed in this batch: every map section and hazard ring is drawn once at load, so no buffer uploads when first seen.

## Batch 7 as built (assumptions, all in CONFIG; change by saying so)
- Waves at 30, 90, 150, 210 s (GDD said about 0:40; 30 s keeps her kennel line clear of the collapse banners). 5 s warning: her line, a plain rule line with the zones, an orange ring on the minimap.
- Wave camps: Stalker W1; Stalker W1 + Howler E1; Stalker C2 + Howler E1; Stalker + Howler C2. Pool 4 Stalkers + 3 Howlers.
- Cubs use the apex minions' kits at 80% health and 60% damage. Aggro 6 m, leash 12 m from the camp; at rest or going home they heal 25/s. A cub still not home after 6 s is put back on its camp. Cubs never cross a drop and only hit a suit on their own layer.
- Solo kill time, standing still and attacking: 7.3 s (run in this session; GDD target 6-8 s).
- Last hit: the plate flies to the player (0.7 s). Two buff slots, 45 s each, the older one is replaced. Stalker plate: your hits cause 4/s bleed for 3 s. Howler plate: +10% speed (the shimmer part waits for hiding).
- "+30% ultimate charge" is a stand-in: 30% of the ultimate's cooldown is removed, until ultimate charge exists.
- A cub whose section falls is lost with no plate; a fallen camp is not announced and spawns nothing. At the wake live cubs fly home as plates (batch 8). Plate buffs carry into the hunt.
- Not built (need bots): leader, crown marker, bounty decree, bots contesting camps.

## Working notes for the next session
- Backups of index.html and run.mjs before each batch are kept outside the repo only (session disk); git history is the durable record.
- Mutation rounds: copy index.html aside, apply one deliberate bug, run tests/run.mjs, confirm the named check fails, restore, compare with cmp.
- A full run takes about 40 s. Hooks step the game synchronously inside page.evaluate, so each check is deterministic.
- Owner works from a phone: reports short, pass/fail as N of N, failing lines only; do not talk about the deadline.

## Files
- index.html: whole game (one module script, CONFIG block at top, TEXT keys, map data). lib/: three.js r171 (MIT, lib/three-LICENSE.txt).
- tests/static-check.mjs: static rules (incl. no Math.random). tests/run.mjs: 71 headless checks (33-45 = apex hunt, 46-51 = royale minions, 52-55 = bags and buff creatures, 56-58 bot movement, 59-63 bot brain, 64-66 royale end and whole matches); starts its own static server.
- Bot hooks: setBots, bots, botDbg, placeBot, hitBot, hitBy, setBotHp, setBotCd, hitCubBy, hitNeutralBy, autoPlayer, setWatch, royale, player, navTime, navNodes, setTime. ?bots=N sets the bot count.
- Test hooks: window.__game (step, setMove, teleport, moveTo, attack, cast, aimKey, render, state, startHunt, hunt, huntUi, attackUnit, hitUnit, placeUnit, unitCd, cubs, hitCub, placeCub, cubCd, attackCub, givePlate, neutrals, hitNeutral, forceNeutral, drawBag, setSeed, ...). ?lock locks the tier; ?debug shows counts and enables the M overview.

## Decisions (user, 23 Nov)
- Lore: Kaymuse on a throne in the core hall, the apex as a tiger statue under her; minions are the demon's shed plates (royale: plate buffs the killer; apex phase: plate flies home to the demon). Ending: even the winner becomes the next tiger statue; next run's statue wears the last winner's school colour (WINNER_STATUE, not built yet).
- Kaymuse voice: always haughty, imperial "We/Our" (朕), archaic English; HUD and rule text stay plain modern English. Closing line LOCKED: "Heaven chose thee. We chose what thou wouldst become."
- Royale minions give a lead (plate: +30% ult charge, 45 s buff); bounty decree is the brake.
- Map v2: 1.5x size; upper layer at 4 m (terraces, roof); open drops (8 dmg); rails, 4 broken gaps (knockback only); tiger statue and 4 stone lions strike after a 0.6 s red ring; 3 healing altars.
- Camera: follow, pitch 40, distance 14 (not first person).
- Minimap (desktop bottom-right, phone top-left). Fog of war: vision 11 m, units beyond hidden, no full-map view.
- Controls: desktop LoL/Dota (right-click move/attack, Q W R hold-aim release-cast, A attack-move, S stop); phone MLBB (stick, ATK auto-target, tap skill = auto-aim, drag = aim, Cancel zone). Skill keys Q W R (was Q E R in the GDD).

## Open
- Kaymuse's look; game title; apex ultimate rule (built as single use at half health; confirm); ultimate charge amounts; minion names; Tiger Demon hard-surface confirm.
- Apex balance: kill-order target not met (see Status); demon 1000 hp against the placeholder kit gives a 50-60 s fight. Owner played it 23 Nov 14:04: very hard but beatable; no tuning until real kits (dashes) land, then re-check test 42 (see Owner decisions).
- Vision is a plain radius: walls/curtains do not block sight yet (comes with hiding); bots use the same plain radius.
- Bots: no school behaviours (GDD: not chosen); bot Q/W show no flash yet (only R shows its ring, for fairness); bodies are boxes in school colours.
- Apex trigger: teleport to the core hall under a card (assumed) or walk there.
- Organiser answer on eligibility; OpenGame CLI test.
- Placeholder skills (line, burst, delayed ultimate) and 3 training dummies are map-test only; replaced by kits.
