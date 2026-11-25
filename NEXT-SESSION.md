# NEXT SESSION: read this first (written 25 Nov 2026 02:2xZ / 10:2x Brunei, lead session ended because it was too long)

Owner works from a phone. Short factual reports, pass/fail N of N, no deadline talk, no apologising. Owner is angry about slowness: be fast, verify, never break an agreed rule (rules in the Project instructions, CLAUDE.md, /home/claude/RUNNERS.md if present, else art/RUNNERS-overnight.md).

## Where things are (batches-3-5 head 5a5696c at writing)
- Overnight art is all merged: palace surfaces/architecture, props, apex/cubs, guards/rebels, giants, school banners, painted VFX (assets/vfx, docs/VFX.md), audio (src/audio/sound.js, docs/AUDIO.md), suits FINAL at 303c726 (school-colour cloth, sash+cuffs on fa/ru/mo/nong, calm robes, run/hit/death clips; run 45529217658 all pass). Status per asset: art/ASSET-LIST.md (A, B, C, G, H). Owner decisions with dates: HANDOFF.md "Owner decisions".
- (g) lag CLOSED: first CJK text loading the system font; fix d4a076c CONFIG.FONT_WARM.
- Real-size map proof PASS (box only, needs grid collision): AFTER the assets are in (owner).

## In flight when this session ended (workers stopped with it; restart from files)
1. INT = the ONLY writer of index.html/tests/ and the consolidator. Plan docs/INTEGRATION.md (batches 17a-17i, owner GO 25 Nov). 17a DONE ab0473f (run 45523438520 15/15). 17b (loader, loading cards, dispose, KTX2 for the 4 approved textures, static-check extended to src/**, suite sharded on a GitHub matrix): round 3 read 02:14Z: sharded 45528753614 284 of 285 = unsharded 45528829496 (only 42, known balance); mutation 45528912792 11/11; Mac A/B 45529019503 0 FAIL. UNCOMMITTED work in /home/claude/empress-decrees- (index.html, tests/run.mjs, tests/static-check.mjs, tests/palace3-checks.mjs, probe17b/): check it, finish 17b (commit + report), then 17c-17i wiring the prep modules below. Suit encodes in assets/c are out of date: re-encode at 17f.
2. PREP-AV (branch prep-av): fxEvent dispatcher + painted VFX card system + sound options menu (owner: "follow lol or dota" = sliders in the Esc/options menu, no hotkey) as src/ modules + docs/HOOKS-17c.md. Last: preflight run 45530525426 PASS, round 4 pushed db8878b.
3. PREP-PAL (no branch pushed yet): src/palace_art.js v1 written locally 01:30Z in /home/claude/prepal-wt (palace + props assembly for 17d/17e; hooks docs/HOOKS-17de.md). Silent since 01:30Z: check the worktree first.
4. PREP-CHR (branch prep-chr): src/chars.js (baked-animation instancing for guards/rebels; shared skeletons for suits/tiger/cubs/giants; suit 2 px inverted-hull outline; tread UV scroll; hit shapes: tiger, cubs, giant sweep 2.5 m / 120 deg). Round 2 run 45530508832 perf PASS (chr_wide 141 fps p95 15.7 ms vs ref 192); checks were still running.
5. FACES (branch faces-sample): owner "i hate the face" (suits, guards/rebels, giants). Four options A bronze war mask, B closed visor, C painted terracotta face, D black lacquer mask, on suit fa, guard zu, giant g00, close-up + play size. Run 45531089330 was in progress at 02:2xZ. FIRST JOB of the next session: read that run, send the owner the three A-D sheets and ask him to pick. Owner waited a long time for this.

## Rules made automatic today
- Pre-push hook in /home/claude/empress-decrees-/.git/hooks/pre-push (session disk): refuses ci-*/prep-*/faces-*/vfx*/audio* pushes whose job script lacks a PREFLIGHT step or that track .pyc. Re-install it if the disk is fresh (copy below in HANDOFF "Working notes" or rewrite from RUNNERS.md RULE).
- Every runner job: preflight (tools, imports, inputs, mkdir outputs, clean tree) failing in the first minute; gates fail on 0 measured; mutation targets checked.
- Repeat scan: any failure cause seen 3 times becomes an automatic check at once.

## Open owner items (not decided)
- Face style (samples above).
- Parked: signal flags (contrast lum sd 30.5 vs 30), throne still small at the wide camera, smoke faint (accepted).
