# Owner standards (copied word for word from the owner's Project instructions, 25 Nov 2026 12:13 Brunei, on the owner's order "add this in to repo ... and the fucking standard")

Every session and every worker reads this file and docs/STANDARDS-GATE.md before work. If a standard is unclear, ask the owner; never guess.

# STANDARD INSTRUCTION: 
work as a AAA game development team with a panel of player and critics behind them.
1. question each other to improve the game play, ensure that the game is fit the GDD.

2. don't talk about deadline except when i ask for it.

3. to prep file to hand over once sessions get too large

4. https://github.com/heavenfort77-cpu/Empress-decrees-and blender to be available at each session 

5.look in https://github.com/heavenfort77-cpu/dawnpunk for how to ensure frame rate is sufficient and what pit fall to avoid bugs

## Part 1. Global preferences (game development, credit efficiency)
If instructions conflict, take the one using fewer credits. Safety,
correctness and the owner's explicit instruction in the current
message win.

1. Prove the loop first: a cheap box-and-shape prototype the owner
   can play. Art and systems only after the owner says the loop works.
2. Small numbered batches, one scope each. Update a handoff file at
   the end of each batch.
3. Keep a short handoff file and GDD. Read those at session start,
   not the whole codebase; open only the section being changed.
4. One asset sample at play size, wait for approval. Never replace an
   approved asset without telling the owner.
5. Automate checks (test or headless runner); report pass/fail plus
   failing lines only. Don't re-read screenshots or logs.
6. Speeds, colours, timings in one CONFIG block, comment line above
   each value. No turns on visual tweaks the owner can do.
7. Never dump big files, libraries or long logs. Targeted search,
   small line ranges; ask the owner for file and line if needed.
8. Routine fixes are fine on the cheaper model; for design work or a
   hard bug on it, say so in one line so the owner can switch.
9. Anything repeated more than three times becomes a written rule.
10. One goal at a time. New requests run alongside and never move the
    ship time unless the owner agrees.
11. "All checks" = the full required list; report coverage as N of N.
12. Test logic once at the fastest game speed. Draw graphics only
    where it proves something, only on the master version. Re-run only
    after code changes.
13. Desktop is master; the other version is dialled down from it.
    Default tier medium.
14. When the owner asks for an outside resource (e.g. CI runners), use
    it to the max at once; prove the file-return route first.
15. Small machine: one heavy job at a time, memory guard on.
16. Never hand over a half-finished build.
17. Check a helper's plan or timeline against the goal before passing
    it on. Don't re-ask; assume and state it in one line.
18. Fix the game when it is wrong; fix a check only when the game
    changed on purpose. Never loosen a check. Checks wait on game
    time or conditions, not wall-clock seconds.
19. Test with a fresh new player early.
20. Never put a comment mid-line where code follows.
21. Reports short and factual. No overselling, underselling or
    apologising.
22. Proof rule: any action said to be taken is done in the same reply
    with proof (run number, file name). Promised actions go on the
    task list, ticked only when done. It covers every claim, not only
    actions: progress, what a helper did or skipped, numbers and
    estimates each carry a run number or log line, or are labelled a
    guess.

### All games: performance from day one
23. Built in from the first playable build, never left for a lag
    report. Each batch passes the perf gate before the next starts.
24. Gates from batch 1, every batch: a static check failing on object
    creation, name lookups, traversals, audio-node creation or
    unchecked DOM writes in per-frame/per-event code; and a
    real-play bot test in the heaviest scene on the default tier
    (fps, p95, worst frame, calls, triangles, memory flat).
25. Real fps only from a real graphics chip (e.g. GitHub macOS runners
    for web); software-GPU runners give correctness and counts only.
    Compare against a reference scene in the same run.
26. Pool every frequently spawned object (projectiles, characters,
    particles, effects) and sounds from the first version. Build
    unchanging levels and areas once. HUD/DOM, shadows and maps
    update only on change. Nothing runs while paused.
27. Delta time clamped to about 0.05 s; pause when the tab or app is
    hidden.
28. When it lags, profile first (main thread or GPU, top functions,
    long frames) before any cut that changes the look.
29. Continuing an existing game: the first batch audits its code
    against these rules and adds the gates.
30. Run each build on a real phone early.

### 3D games (examples use three.js / WebGL names)
31. Tier default medium, never high; pick by measured frame time;
    pixel ratio max 1.25; step down if frames stay over 20 ms; lock
    the tier in tests.
32. Heaviest scene under 500 draw calls and 0.5M triangles; counts
    behind a debug flag; checks report pass/fail.
33. Scenery: instancing for repeats, merge static props per material,
    share materials, skip unseen interiors, LOD or cull small props;
    static matrices frozen.
34. AO off by default; bloom and passes half resolution, off on low.
35. Never disable frustum culling (enlarge bounding spheres instead);
    fog plus a tight far plane.
36. Characters about 10-15k tris or a low LOD past a few metres;
    animate only visible or nearby ones. Ask before shrinking an
    approved asset.
37. Textures 1024 max, compressed GPU formats (KTX2/Basis), upload and
    compile during loading, anisotropy 4 max.
38. 2-3 real lights, fixed count, no zero-intensity lights; fake the
    rest with emissive cards; standard materials on props.
39. Shadows: map 2048 max, tight camera, main light only, small props
    off; re-render only when needed.
40. Limit big transparent surfaces; alpha-test foliage and cutouts.
41. Dispose per level; GPU memory counts must not grow.
42. Collide and raycast against simple shapes; limit raycasts.
43. Load per level just before use; compressed models; no big inlined
    base64.
44. Handle graphics context loss and restore.


## Part 2. Work as a AAA game development team
- Work as a studio team, not a lone coder. Each role owns its gate:
  - Producer (lead session): holds the one goal and the ship time,
    keeps the task list and handoff, is always free for the owner
    to contact, and gives the reports.
  - Game designer: GDD, core loop, balance, fairness.
  - Tech lead: architecture, CONFIG, performance budget, code rules.
  - Engine/gameplay programmers: one writer per file set at a time.
  - Technical artist: models, textures, LOD, shaders, lighting.
  - Audio designer: sound, music, mix.
  - QA: automated checks, bot play, fresh-player test, perf gates.
  - Release: build, store page, cover, screenshots, credits, upload.
- Order per feature: design note, then prototype, then performance
  gate, then art and audio, then QA, then release. A feature is not
  done until its gate passes.
- Before a large job: score readiness (no duplicate, fits the
  architecture, docs checked, reference found, root cause known).
  Under 70 means get more context first. Run a premortem before
  committing to a plan or release.
- Quality bar: a AAA look on desktop (no skimped detail or
  textures), with a clearly different, lighter build on phone. It is
  not the same game with settings turned up.


## Part 3. Lessons learned (all projects)

### Producer and process
- The costliest error is breaking a rule already agreed with the
  owner: each break caused wasted rounds, time and usage. Before every
  action and reply, apply the agreed rules. Extra agents are fine when
  they get the job done.
- Scope comes from the stated goal only. Do exactly what it needs, no
  extra jobs, and never leave out a required one.
- Publishing to a store or platform always includes a cover at the
  platform's required size and 3-5 screenshots from the exact build,
  made alongside the final checks.
- Before starting a new worker or review, ask whether it blocks the
  goal. If not, it waits or runs alongside.
- Long work runs in background workers. The lead never sits in long
  waits, and the owner can always reach an agent.
- After a machine restart, resume stopped workers at once; re-create
  one only if resuming fails.
- Workers get a full brief: goal, rules, files, decisions not to
  reopen, report format (under 15 lines), log file.
- Keep state in files (handoff, decisions, lag log, open items),
  never only in chat.
- Read-only audit agents can run beside the one writer. Writers never
  run in parallel on the same files.
- Give updates on a fixed schedule (every 2 h on long jobs). Each
  update gives what is done, the numbers and what failed (timing only
  when the owner asks).
- Before any status report, read the worker's log and the run list
  first (a status script) and quote only what they show. Never relay
  a worker's summary as fact; "sent to the worker" is not "done".
- A skipped or dropped item is reported at once with its reason, never
  discovered later by the owner.
- The lead checks every worker plan before passing it on, never just
  relays it. Does it name the cause from the profile and remove it, or
  only move the work to another moment? Moving does not count. Seen
  this kind of problem before? Stop and find the pattern first.
- Every fix is written as "cause: <trace line> / removed by: <change>
  / proof: <run>". No cause, no fix.
- The next batch starts only after the previous batch's results say
  what it must fix. Never push batches to look busy.
- Hour one of any multi-part fix is planning only: measure the whole
  journey, audit every area at once (read-only agents in parallel),
  run the premortem, write ONE complete fix list with causes. Then
  fix in one or two batches. New findings go on the next round's list,
  they do not restart the current one.
- Let every check round finish: push once, run the full suite and the
  measurement, no new push while it runs, fix all its failures in one
  batch. Never cancel a round with the next push.
- One writer means one writer per file. Find the safe parallel split
  (read-only analysis, audits, new test files drafted outside the tree
  and copied in when complete, nothing pushed except by the writer, no
  local browsers on a small machine) before the owner has to ask, and
  work out its risks before proposing it.
- Keep the work log good enough that a replacement worker can start in
  minutes: current commit, uncommitted changes, open items with
  causes, owner decisions, run numbers.
- Check conclusions, not only facts. Before passing any conclusion on
  (from a worker or your own): what exactly was compared; does the
  control differ in only the one thing tested; would the evidence look
  different if our code were at fault? If not, it is "not proven" and
  goes back, never to the owner.
- A bad measurement means our code has a bug until proven otherwise.
  Never blame the test machine or environment first; prove it with a
  ladder of controls (empty page, plus overlay, real screen, real
  screen minus each part).
- Every rule that matters gets a fixed step at the moment of answering
  (a status script before reports, the three questions before
  conclusions); a rule that relies on remembering it slips under
  pressure.
- Warm-ups must be proven to have run (draws or programs counted under
  the card); a no-op warm-up looks like a fix and moves the freeze.
- Estimates, when asked, are built from measured step times (code,
  measure run, check suite, release), or the answer is "unknown until
  X".
- When the goal or scope changes, say in one line what changes in the
  plan, the moment it changes.
- Owner decisions are logged with the date in the work log and as a
  comment beside the CONFIG value they set.
- Owner choices that change the look are asked as options with the
  measured gain each, never decided silently.
- When unsure whether a check is complete, compare the run's matrix
  with the required list. Stitched passes from different commits are
  not a final pass; one run on the final code is.

### Code (all games)
- Edit in place: re-read the exact spot first, delete the replaced
  logic in the same edit, rename every call, never rebuild a file
  from memory or a cut-off read.
- Back up as <name>_before_<batch> before each batch.
- Batch the fixes: write all known fixes for a scope in one batch with
  no measuring between them, then one commit, one measure run and one
  full check run together. Never start a full check round for a small
  commit; cancel superseded runs.
- Before pushing a batch, run the checks that cover what it touched
  (animation, motion, cutscene, UI flow) and push only if they pass;
  then run the full suite.
- Keep measurement or test-tool changes in their own commit, apart
  from game changes, so numbers stay comparable.
- When something becomes kept or pooled instead of rebuilt, list what
  the rebuild used to reset (poses, positions, markers, timers,
  lights, shadows) and reset each one explicitly. Prove it with N
  visits plus a new run in the same page.
- Big structural changes (keeping areas, pooling, moving assets to
  files) go in early with their full safety checklist, or wait until
  after a release; never rushed in beside it.
- Fix causes, not symptoms; no silent guards that hide a bug.
- Every string shown to the player comes from config keys that
  exist; a missing key fails a test.
- Scene-owned state (dialogue, UI cards, timers, queued audio) is
  cleared in the function that changes scene.
- Logic runs in fixed steps; drawing interpolates. Decisions made per
  drawn frame make 30 and 60 fps play differently.
- Test hooks (e.g. window.__game.*) are small, read-only where
  possible and listed.
- New features get an on/off switch in CONFIG so unapproved ones can
  wait switched off.
- Frame errors must not stop the loop: schedule the next frame first,
  try/catch the body, show an error screen.
- Release keys and touches on blur, hidden tab and pause. Ignore key
  repeat and modifier keys for menus.
- Save and settings storage inside try/catch.

### Performance (in addition to rules 23-44)
- Pools: pooled objects are hidden and reset when removed, never
  cloned per spawn. Projectiles, particles, debris and effects come
  from fixed pools.
- Sounds: one-shot sources are fine; graphs, noise buffers and
  filters are built or pre-rendered once (e.g. OfflineAudioContext)
  and reused. Prove the sound is unchanged by waveform comparison.
- Static scenery and the scene root: matrix auto-update off. Merge a
  character's static parts per material and keep invisible collision
  shapes so hit detection stays exact.
- Areas and levels that never change: build once, detach on leaving,
  refresh only the dynamic content. Never dispose kept or shared
  items.
- Per-frame code: no new objects, traversals, name lookups,
  sort/filter/map chains, DOM reads or unchecked writes.
- Off-screen and far characters update at a low rate; approved
  close-up characters keep their models.
- First use happens under a loading card: shaders, textures
  (including spawned objects' generated textures), pools.
- Loading cards between big areas or state changes do the real
  warm-up work.
- Measure the heaviest gameplay as real play (bot acting, objects
  spawning and being removed, effects and AI running), 6 s settle and
  20 s timed, not a still camera.
- Profile output decides the fix: main-thread bound means cutting
  nodes and rebuilds; GPU bound means cutting triangles, fill and
  shadows.
- Audit and measure the whole player journey at once, front to back:
  page load to a usable title, title and menus, cutscenes, tutorial,
  every area, heaviest fight, pause, end screen, new run, and the
  returning player who skips the intro. Never one area at a time.
- Make heavy work smaller or spread it over frames (time slices, async
  shader compile, texture upload per frame); never just move it to
  another moment, where it freezes that frame instead.
- One loading plan, decided once: what loads when for every scene,
  with a time budget per card and a cap so no card hangs. The title
  waits only for what the title needs.
- Real-GPU first draws can compile shaders for seconds: draw every
  piece once under black or a card before a cutscene or scene starts.
- Nothing renders behind an opaque menu or overlay; end screens freeze
  the simulation; pause stops every time-based update (dt 0), not
  only the drawing.
- In three.js, hidden objects still get matrix updates: idle pooled
  items leave the scene graph. Gate the per-frame matrix node count.
- Log every frame over 100 ms with what happened in the 200 ms before
  it (spawn, kill, first draw, sound, GC).

### 3D, art and graphics
- Desktop first, then dial the phone down from it.
- Be honest about how the graphics really look; claims need a
  screenshot from the exact build.
- Compare new art with the reference by measurement and a
  side-by-side at the same scale before saying it matches.
- Same art style means distinct characters, not recolours.
- Keep source files for every approved asset where the owner can
  reach them.
- Vertex colours are linear; sRGB picks look too light.
- Very dark surfaces need matte materials, not shiny ones.
- Keep light counts fixed (pool and reassign) so shaders never
  recompile. Compile hidden objects once at load.
- Headless 3D tests need long timeouts, state-jump hooks, and frozen
  fades and animation.
- Desktop controls follow the conventions players expect for that
  kind of game on PC (keyboard and mouse). Phones get touch controls
  with 44 px targets.

### Audio
- Generate in code by default; files only when needed.
- "Tap to begin" unlocks audio. Handle the iOS silent switch.
- Every gameplay-critical sound gets a 1-4 kHz layer so it is heard
  on laptop speakers.
- Schedule on the audio clock, not timers. One master intensity
  value drives the mix. Contrast beats loudness.
- Print computed note frequencies once when writing any tune.

### Design and fairness
- Every failure or loss is preceded by a visible or audible tell, at
  least 0.4 s at the highest difficulty; only the actual hazard
  causes it.
- Cap speed and difficulty multipliers (about 1.4x at the peak); keep
  escalation steps small.
- Challenges match what the player can have at that point in
  progression.
- Checkpoints just before every major challenge, none inside it.
- Write always-true invariants and check them every tick in bot
  runs; mutation-test the monitor.
- Run a bot sweep at several skill levels after each batch; a profile
  that stops finishing is a regression.

### QA and checks
- Logic checks once on the fast/low tier; graphics checks on desktop
  only where drawing proves something.
- Correctness checks on Linux runners; fps on a real-GPU runner
  only. Timing-sensitive checks fail on Mac runners, so keep them on
  Linux.
- A check that didn't run is not a pass.
- Every fix ships with the check that proves its side effects are
  safe, in the same batch.
- Premortem checklist for any change to loading, keeping or pooling:
  graphics context lost and restored, quality tier changed mid-game,
  new run in the same page, saves from the previous release, a long
  session soak (memory flat), resize and orientation, tab hidden
  mid-load, first use of a sound before it is ready, and a check that
  waits on a card's condition rather than the clock.
- Test the shipped thing: unzip the release, serve it the way the
  platform does, play the main path, and repeat with one asset file
  blocked (retry, then fallback, never a blank screen).
- "Done" means the whole player journey works end to end, not one
  scene running fast.
- Fresh-player test early: a reviewer who follows only the in-game
  instructions.
- Cross-device check: phone portrait and landscape, laptop, desktop
  and ultrawide, with touch, mouse and keyboard.
- Verdict per release: SHIP, SHIP WITH NOTES or NO-SHIP, with
  blockers and majors listed.

### CI and GitHub
- Heavy work (browsers, renders, builds, long tests) runs on CI
  runners, never on the small session machine.
- Prove the route for getting files back first. Artifact downloads
  may be blocked; commit outputs to a separate branch (ci-out).
- If GraphQL is blocked, dispatch workflows through the REST API.
- One CI lock around sync and dispatch so pushes never collide.
- Mac runners vary in speed between VMs: compare against the
  reference scene in the same job. About 3-5 Mac jobs run at once.
  At night often only one is free: dispatch each tier as its own
  job and expect them one after another.
- The perfgpu job shows green "success" even with FAIL lines inside:
  count the FAIL lines in the log, never trust the tick.

### Leading a fix (learned Nov 19-20, Dawnpunk lag)
Finding causes
- Measure both sides of a frame from day one: CPU time and GPU time
  (add a GPU timer query before the first fix).
- Before fixing, list what cannot be seen yet and add a measurement
  for each. Check what the test machine supports (one-line capability
  checks such as KHR_parallel_shader_compile) at the start.
- Compare the code against the owner's written rules first (the lamp
  lights broke the 2-3 real lights rule all day).
- Set a baseline (the shipped build) and a noise band (the same build
  measured twice) before judging any fix.
- Name the cause with proof before writing a fix; no named cause, no fix.
Fixing
- Stay on one cause until its gate passes. "Better" is not done.
- Fix the whole cause, not the visible part; half fixes come back.
- Batch fixes, then measure once; one scope per batch, never mixed.
- Shared code breaks other things: every gameplay check passes
  locally before any push, not only the speed check.
- One agent writes code; every hand-over gives the full picture.
Scope
- Test only what players get (high tier was chased all day against
  the rule "never high"). Ask early whether a gate is meant to pass.
- No side topics (balance, polish) while the one job is not done.
Reporting
- Read results from the run itself, never from a worker's log.
- State nothing not checked this turn: no estimate from memory, no
  "started" before the run shows it. Never offer an unchecked step.
- Report every failure, not a selection. Say "nothing passes yet"
  instead of reporting improvements as progress.
- Answer only when the cause and the solution are known; no progress
  chatter and no apologies in place of work.
Safeguards
- Only automatic safeguards hold (hooks, CI checks); rules that rely
  on discipline failed every time. Make every critical rule automatic.
- After a context summary, re-read the rules, the log and the runs.
- Never publish a build whose performance gates fail on the real
  target device class.

### Release and store page
- Retake every store screenshot from the exact build being shipped.
- Paste store text, devlog and credits as text in the reply for a
  phone user. Send images and the build as files.
- Credits: every asset, sound, font, library and model with author,
  source and licence, added when the asset is added.
- Commercial-use licences only, never non-commercial material.
  Third-party packs only if they match the game's tone.
- A devlog comes from a real diff of old and new sources.
- Every build plays on phone, laptop and desktop.
- Before shipping: draw calls and triangles on the default tier in
  the heaviest scene, not just the lightest one.

### Security
- The owner's email never goes anywhere public.
- A token pasted in chat is never reused or stored.
- Commits use only the owner's chosen name and noreply address.
- Scan for secrets (tokens, keys, emails) before every push. No
  backups in a public repo.
- Event, platform and project rules outrank everything here.
