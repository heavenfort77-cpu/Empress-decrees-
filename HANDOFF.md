# Handoff (2026-11-23, after batch 6). GDD: docs/GDD.md (also Project "empress decrees", claude/GDD.md)

## Session start (every session)
1. Attach both repos: add_repo heavenfort77-cpu/Empress-decrees- (access push) and heavenfort77-cpu/dawnpunk (read; public, anonymous clone works). Dawnpunk = reference for frame-rate rules and bug pitfalls; read only the part needed.
2. Read this file, then only the GDD section being changed. Do not read the whole codebase.
3. Run the checks before and after any change: `node tests/static-check.mjs` then `node tests/run.mjs` (`-v` for details). Report pass/fail and failing lines only.

## Status
- Batches 1-6 done. Code is on branch `batches-3-5` (PR #1 open; merge to main when the user agrees).
- Batch 6 = apex fight on boxes: H key or the Hunt button starts it (test trigger until the royale exists). Wake 3 s, Tiger Demon + Stalker + Howler, skill transfer by plate, win / loss / retry.
- Static check PASS. Runtime 50 of 50 PASS (headless Chromium, software GPU: correctness and counts only).
- Mutation rounds: batch 3 edge clamp caught after a fix; batch 4 5 of 5; batch 5 6 of 6; batch 6 11 of 11.
- Counts (software GPU, medium tier): spawn 27 calls / 2.8k tris; whole map 76 / 8.4k; hunt with all units and 3 tells 17 / 0.9k. Budget 500 / 0.5M. Shader programs 3 at load and 3 after hunts; geometry count flat (94).
- Bot sweep (test 42), reaction / kill order (0 demon, 1 stalker, 2 howler): never-dodge loses all 3 (6-9 s); 0.3 s: demon-first LOSES (13 s), minions-first wins (57-58 s, 20-26 hp left); 0.15 s wins all 3 (50-60 s, 73-100 hp left).
  - GDD sim target "no kill order is dominant" is NOT met: minions-first is better for the 0.3 s bot. Player kit is still the placeholder, so tuning waits for real kits.
- NOT run: real-GPU fps (needs a GitHub Actions macOS runner; no workflow yet). NOT tried on a real phone (touch checked by simulated pointer events only).
- Phone review link (claude.ai artifact, same page with three.js from jsDelivr): see the latest session report for the current version.

## Next
- Waiting for the user to play the apex fight and say whether the loop works.
- Then: royale minions (switch ROYALE_MINIONS), decrees, bots, hiding; real kits replace the placeholder skills.
- Set up CI (GitHub Actions: Linux checks + macOS real-GPU perf gate); prove the file-return route first.

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

## Files
- index.html: whole game (one module script, CONFIG block at top, TEXT keys, map data). lib/: three.js r171 (MIT, lib/three-LICENSE.txt).
- tests/static-check.mjs: static rules. tests/run.mjs: 50 headless checks (33-45 = apex hunt); starts its own static server.
- Test hooks: window.__game (step, setMove, teleport, moveTo, attack, cast, aimKey, render, state, startHunt, hunt, huntUi, attackUnit, hitUnit, placeUnit, unitCd, ...). ?lock locks the tier; ?debug shows counts and enables the M overview.

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
