# Handoff (2026-11-23, after batch 8; written for a fresh session). GDD: docs/GDD.md (also Project "empress decrees", claude/GDD.md)

## Session start (every session)
1. Attach both repos: add_repo heavenfort77-cpu/Empress-decrees- (access push) and heavenfort77-cpu/dawnpunk (read; public, anonymous clone works). Dawnpunk = reference for frame-rate rules and bug pitfalls; read only the part needed.
2. Read this file, then only the GDD section being changed. Do not read the whole codebase.
3. Run the checks before and after any change: `node tests/static-check.mjs` then `node tests/run.mjs` (`-v` for details). Report pass/fail and failing lines only.

## Status
- Batches 1-8 done. All code is on branch `batches-3-5` (PR #1 open; merge to main when the user agrees). The owner has NOT yet said the loop works; no art before that.
- Batch 6 = apex fight on boxes (H key or Hunt button). Batch 7 = royale minions (kennel waves, cubs, plates). Batch 8 = faster cubs and minions, buff creatures from marble bags, cubs fuse into the statue at the wake.
- Static check PASS. Runtime 60 of 60 PASS (headless Chromium, software GPU: correctness and counts only). Tests run with a fixed seed (12345).
- Mutation rounds: batch 3 edge clamp caught after a fix; batch 4 5 of 5; batch 5 6 of 6; batch 6 11 of 11; batch 7 12 of 13 (the miss is an equivalent change); batch 8 11 of 11.
- Counts (software GPU, medium tier): spawn 27 calls / 2.8k tris; whole map 76 / 8.4k; hunt with all units and 3 tells 17 / 0.9k; 7 cubs with 3 tells 33 / 2.3k. Budget 500 / 0.5M. Shader programs 3 at load and after play; geometry count flat.
- Bot sweep in the hunt (test 42) with the faster minions, reaction / kill order (0 demon, 1 stalker, 2 howler): never-dodge loses all 3 (7-8 s); 0.3 s: demon-first loses (17 s), minions-first wins (57 s, 3-13 hp left); 0.15 s wins all 3.
  - GDD sim target "no kill order is dominant" is NOT met (minions-first is better for the 0.3 s bot). Player kit is still the placeholder; tuning waits for real kits.
- Cub farm bot (test 51, 0.3 s reaction, 170 s at the west camp): 2 plates, never hit. Cubs may be too soft for a player who dodges.
- NOT run: real-GPU fps (needs a GitHub Actions macOS runner; no workflow yet). NOT tried on a real phone (touch checked by simulated pointer events only).
- Phone review link (claude.ai artifact, same page with three.js from jsDelivr): https://claude.ai/artifact/3nQ67JCTmb1JfPKC3Y416z (version 1795409517-3475 = batch 8). Republish it after each batch: copy index.html, swap the importmap path for https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.min.js, publish to slug 1688f9ba-a0e5-4f7b-ac2e-3a68d6fc67c3.
- Project docs (claude/HANDOFF.md, claude/GDD.md, claude/code/index.html, claude/code/tests/run.mjs) are copies of the repo files; rewrite them after each batch. A project_read of a code file dumps the whole file into the session: avoid it, write from the local file.

## Next batch: 9 = bots (owner, 23 Nov: bots are what make the royale end and start the hunt on its own)
Not started. Plan to check with the owner in one line, then build:
- Goal: 9 bot suits so the royale plays out and the last suit alive wakes the demon without the H key. Then leader, crown marker and bounty become possible; decrees come after.
- Biggest change: today every hazard, cub, creature and enemy targets the player object `P` directly. Bots need one "suit" shape (position, layer, health, statuses, plates, boons, orders) shared by the player and bots, and "nearest suit" in place of `P` in: hazards, altars, collapse falls, cubThink, stepUnit (royale only), plates and boons (last hitter), vision.
- Movement: navSearch uses one shared PATH buffer; bots need a path buffer each and at most one search per tick (time-sliced), or straight steering inside a section plus waypoints between sections.
- Bot decisions (CONFIG weights): leave a warned section, fight the nearest seen suit, contest a camp or buff creature, stand on an altar when low, never walk into a tell that has been showing longer than its reaction time.
- End of royale: player dead = loss screen with retry (replaces the map-test respawn); last suit alive = startHunt (keep H as a debug trigger behind ?debug).
- Checks to add: match length band (GDD 3-4 min), win share per spawn, every bot death has a cause (hit, fall, collapse), idle player loses, no bot stuck longer than N s, invariants every tick, budget with 10 suits + 7 cubs + tells, memory flat over 3 runs.
- Premortem: path cost with 9 searchers; bots falling at broken rails by knockback only; a cub leashing between two suits; plates and boons going to bots (pool and HUD stay correct); hunt tests must keep passing when the royale has other suits; fixed seed so sims replay.
- Readiness: about 60 of 100 (no reference bot code read yet; suit refactor not designed in detail). Read Dawnpunk's bot or enemy update only if it has one; write the suit refactor note first.

## Owner decisions, 23 Nov (later session)
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
- tests/static-check.mjs: static rules. tests/run.mjs: 60 headless checks (33-45 = apex hunt, 46-51 = royale minions, 52-55 = bags and buff creatures); starts its own static server.
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
- Apex balance: kill-order target not met (see Status); demon 1000 hp against the placeholder kit gives a 50-60 s fight.
- Vision is a plain radius: walls/curtains do not block sight yet (comes with bots and hiding).
- Apex trigger: teleport to the core hall under a card (assumed) or walk there.
- Organiser answer on eligibility; OpenGame CLI test.
- Placeholder skills (line, burst, delayed ultimate) and 3 training dummies are map-test only; replaced by kits.
