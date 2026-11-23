# Handoff (2026-11-23 12:00). GDD: docs/GDD.md (also Project "empress decrees", claude/GDD.md)

## Session start (every session)
1. Attach both repos: add_repo heavenfort77-cpu/Empress-decrees- (access push) and heavenfort77-cpu/dawnpunk (read; public, anonymous clone works). Dawnpunk = reference for frame-rate rules and bug pitfalls; read only the part needed.
2. Read this file, then only the GDD section being changed. Do not read the whole codebase.
3. Run the checks before and after any change: `node tests/static-check.mjs` then `node tests/run.mjs` (`-v` for details). Report pass/fail and failing lines only.

## Status
- Batches 1-5 done. Code is on branch `batches-3-5` (merge to main when the user agrees).
- Static check PASS (per-frame rules, text keys, CONFIG comments, comment placement, module syntax). Runtime 37 of 37 PASS (headless Chromium, software GPU: correctness and counts only).
- Mutation rounds: batch 3 edge clamp caught after a fix; batch 4 5 of 5; batch 5 6 of 6.
- Counts (software GPU, medium tier): spawn 27 calls / 2.8k tris; centre while aiming 22 / 3.2k; whole map 77 / 8.5k. Budget 500 / 0.5M.
- NOT run: real-GPU fps (needs a GitHub Actions macOS runner; no workflow yet). NOT tried on a real phone (touch checked by simulated pointer events only).
- Phone review link (claude.ai artifact, same page with three.js from jsDelivr): https://claude.ai/artifact/3nQ67JCTmb1JfPKC3Y416z (version 1795405399-0f41).

## Next
- Waiting for the user to review map v2 and the controls.
- Then: apex fight on boxes (Tiger Demon, 2 minions, skill transfer) using the order/aim system already built; then royale minions (switch ROYALE_MINIONS), decrees, bots, hiding.
- Set up CI (GitHub Actions: Linux checks + macOS real-GPU perf gate) once pushing works from the session; prove the file-return route first.

## Files
- index.html: whole game (one module script, CONFIG block at top, TEXT keys, map data). lib/: three.js r171 (MIT, lib/three-LICENSE.txt).
- tests/static-check.mjs: static rules. tests/run.mjs: 37 headless checks; starts its own static server.
- Test hooks: window.__game (step, setMove, teleport, moveTo, attack, cast, aimKey, render, state, ...). ?lock locks the tier; ?debug shows counts and enables the M overview.

## Decisions (user, 23 Nov)
- Lore: Kaymuse on a throne in the core hall, the apex as a tiger statue under her; minions are the demon's shed plates (royale: plate buffs the killer; apex phase: plate flies home to the demon). Ending: even the winner becomes the next tiger statue; next run's statue wears the last winner's school colour (WINNER_STATUE, not built yet).
- Kaymuse voice: always haughty, imperial "We/Our" (朕), archaic English; HUD and rule text stay plain modern English. Closing line LOCKED: "Heaven chose thee. We chose what thou wouldst become."
- Royale minions give a lead (plate: +30% ult charge, 45 s buff); bounty decree is the brake.
- Map v2: 1.5x size; upper layer at 4 m (terraces, roof); open drops (8 dmg); rails, 4 broken gaps (knockback only); tiger statue and 4 stone lions strike after a 0.6 s red ring; 3 healing altars.
- Camera: follow, pitch 40, distance 14 (not first person).
- Minimap (desktop bottom-right, phone top-left). Fog of war: vision 11 m, units beyond hidden, no full-map view.
- Controls: desktop LoL/Dota (right-click move/attack, Q W R hold-aim release-cast, A attack-move, S stop); phone MLBB (stick, ATK auto-target, tap skill = auto-aim, drag = aim, Cancel zone). Skill keys Q W R (was Q E R in the GDD).

## Open
- Kaymuse's look; game title; apex ultimate rule; ultimate charge amounts; minion names; Tiger Demon hard-surface confirm.
- Vision is a plain radius: walls/curtains do not block sight yet (comes with bots and hiding).
- Apex trigger: teleport to the core hall under a card (assumed) or walk there.
- Organiser answer on eligibility; OpenGame CLI test.
- Placeholder skills (line, burst, delayed ultimate) and 3 training dummies are map-test only; replaced by kits.
