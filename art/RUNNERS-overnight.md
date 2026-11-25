# Overnight runner guide (lead, 25 Nov 00:2x). Read before any heavy job.
Machine: 2 cores, 7 GB, shared by several workers. Local heavy jobs (Blender, klad, headless browser) ONLY under `flock /home/claude/heavy.lock <command>`, and prefer GitHub runners.

## Your own branches (never touch another worker's branch or worktree)
- Work tree: `git -C /home/claude/empress-decrees- fetch -q origin batches-3-5 && git -C /home/claude/empress-decrees- worktree add /home/claude/<w>-wt -b ci-art-<w> origin/batches-3-5`
- Copy the art runner workflow into it: `git -C /home/claude/<w>-wt checkout origin/ci-art-test -- .github/workflows/art-run.yml` (fetch ci-art-test first: `git -C /home/claude/empress-decrees- fetch -q origin +refs/heads/ci-art-test:refs/remotes/origin/ci-art-test`).
- Your deliverables (scripts, GLBs, textures, .klad sources, shots, study files) are committed on ci-art-<w>; the lead merges them into batches-3-5 in the morning. Branch workers never push to batches-3-5, main or another worker's branch. Exception: the shared-tree worker (W1a, W1b, W1c as briefed) commits art/ and assets/ files only to batches-3-5. CI files (.github, ci_art, ci_comfy) never go to batches-3-5 or main.

## Heavy job on a runner (Blender via pip bpy 5.3 / python 3.13, klad CLI, Chromium via playwright 1.63)
- Write ci_art/job.sh in your tree (bash; env: $BPY = python with bpy, $KLAD = klad binary, $OUT = folder to write results into). Commit, `git -c push.negotiate=true push -q origin ci-art-<w>`; every push starts a run (workflow art-run). Do not push again while your run is going (check: gh api "repos/heavenfort77-cpu/empress-decrees-/actions/runs?branch=ci-art-<w>&per_page=1").
- Results: branch ci-out, out/art/ci-art-<w>/<run id>/ (job.log + whatever $OUT held). Fetch: `git -C /home/claude/empress-decrees- fetch -q --depth=1 origin +refs/heads/ci-out:refs/remotes/origin/ci-out`, list with `git ls-tree -r --name-only origin/ci-out out/art/ci-art-<w>/<run>/`, read with `git show origin/ci-out:<path> > file`.
- Route proof run: ci-art-test run 45435204434 (first run builds klad, about 15 min; later runs use the cache). Check it finished green and its job.log shows RESULT PASS lines and klad 0.4.0 before your first heavy job; if it failed, tell the lead (SendMessage is not available to you: write it in /home/claude/overnight.log with prefix ALERT) and use local runs under flock.
- Viewer shots: node art/tools/shoot_viewer.mjs OUTDIR shoots art/viewer/beast.html; for your own assets add your own viewer page (copy and adapt; same FOV 50, pitch 40, the game's lights and floor) and your own shoot script.

## ComfyUI concepts (CPU runners)
- Your own branch: `git -C /home/claude/empress-decrees- fetch -q origin +refs/heads/ci-comfy:refs/remotes/origin/ci-comfy && git -C /home/claude/empress-decrees- worktree add /home/claude/<w>-comfy -b ci-comfy-<w> origin/ci-comfy`, then edit .github/workflows/comfy.yml so `branches: ['ci-comfy-<w>']`, edit ci_comfy/prompts.json, commit, push to ci-comfy-<w>. Results land in ci-out out/comfy/<run id>/job<N>/.
- Settings that work: SD 1.5 + LCM LoRA, 6 steps, about 2 min per image, 8 seeds per job, up to 4 jobs. Positive prompt under about 60 words (CLIP limit); avoid words that pull the material wrong (e.g. "silver" made beasts silver). Concepts are references only: never shipped, never traced.

## Commits and logs
- Name Claude, email noreply@anthropic.com; message ends with "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" and "Claude-Session: https://claude.ai/code/session_015w2gCFTByA9kWQ9LtEYXgQ". Secret scan the diff before every push.
- One line per step in /home/claude/overnight.log: `<w> HH:MM <what> <numbers / run id>`.

## RULE (lead, 25 Nov 09:5x local, after the same job-script bug hit 5 times: W5 ops dir, W4/W5 tracked .pyc, INT toktx + gates passing on 0 files, SUITANIM ops dir + scipy + wrong GLB path)
Every runner job starts with a PREFLIGHT step that runs in the first minute and FAILS the job before any heavy work if anything is missing:
1. every tool the job calls (`command -v` for each binary: blender/bpy, klad, toktx, ffmpeg, node, playwright browsers);
2. every Python import the scripts use (`python -c "import numpy, PIL, ..."`; no scipy unless installed by the job);
3. every input file and folder the job reads (GLBs, .klad sources, ops dirs) and `mkdir -p` of every folder it writes;
4. the git tree is clean of tracked build files (no .pyc, no generated files tracked) so the ci-out push cannot be blocked.
Every gate counts what it measured and FAILS when that count is 0 ("passed on nothing" is a FAIL).
Mutation scripts check their target file exists before mutating, and fail if it does not.
Prove the job script once with the preflight alone (a 1-minute run) after any change to the job script, before the heavy run.
