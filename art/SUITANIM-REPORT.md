# SUITANIM: run, hit and death clips for the nine school suits (25 Nov, branch ci-art-suitanim)

Status: NOT DELIVERED. No round passed every gate, so nothing went to batches-3-5. Round 3 code is ready at e724002 (pushed with [skip ci], so no run started). The 2-round cap is reached.

## What was built (art/tools/suit_blender.py, same rig, same meshes)
- `run`: an in-place loop keyed every frame from frame 0. The suit runs at its kit's speed tier (index.html CONFIG.STATS.speed): ru, yy, za, ming, zh 6.0 m/s; dao, fa 6.4 m/s; mo, nong 5.6 m/s. Legs are solved with IK, so foot speed equals ground speed. Timing comes from Muybridge plate 10 (duty about 0.3, a flight phase, the heel rising off the toe). Each school has its own style values in the RUN table (cadence, lean, bob, arm swing and carry, twist, track width). Cycle lengths are 0.50-0.58 s. In game: timeScale = actual speed / run_v (suits_info.json).
- `hit`: 0.30 s and returns exactly to idle frame 0. Plate 51 gives the shape. Armour tier sets the strength (Low 1.0, Mid 0.85, High 0.7). The feet stay planted. On robe suits the hip drop is capped at 0.02 m.
- `death`: 0.9-1.1 s, ending lying still. A per-frame floor solve covers all LODs. Back falls: ru, dao, yy, ming, zh. Front falls (over the knees): fa, mo, za, nong.
- Gates: art/tools/suit_clip_check.mjs. It loads the GLBs with three r171 in Node and computes skinned vertices the way the game will. 26 gates per suit, plus 12 mutations.
- Tools: suit_clip_signfix.mjs (quaternion sign continuity), suit_clip_merge.mjs (fallback: approved GLB plus the new clips), suitanim_shoot.mjs and suitanim_sheet.py (contact strips and play-size shots), and a strip mode in art/viewer/suits.html.

## Runs
- Round 1, run 45515328643 (460aa37): builder 150 of 153, silhouettes 30 of 30, shots 65 of 65, clip gates 173 of 234, mutations 12 of 12. attack, idle and meshes were byte-identical to the approved GLBs in 27 of 27 checks (the rebuild is deterministic).
  - Causes found:
    - (a) A new NLA track was left unmuted, so it overrode the pose while hit and death were authored. The hit started 0.80 m off idle.
    - (b) The fixed toe pivot let the boot nose dip 6-21 mm under the floor.
    - (c) The exporter wrote quaternions with their own signs: 6-9 flips per clip.
    - (d) dao's robe went 122 mm under the floor in the run.
    - (e) Front falls dived in mid-air: the floor solve lifted the body up to 0.30 m.
- Round 2, run 45518008969 (bb4017c): fixes for (a) to (e). The run itself was green, but its push to ci-out failed (GitHub 500, 6 tries), so no GLBs or shots came back. Gates were read from the run log: builder 152 of 153, silhouettes 30 of 30, clips 217 of 234, mutations 11 of 12.
  - Fixed: hit returns to idle 9 of 9, flips 0, contact 18 of 18, death floor, still and lying 27 of 27.
  - New failure: run slide 13.4-15.5 cm per cycle on 8 suits. Cause: holding the lowest point of the turned boot let the contact jump from mid-sole (+0.05 m) to the boot nose (+0.15 m).
  - Still failing: dao run_floor -76 mm (robe), mo death lift 0.343 m (gate max 0.25).
  - The missed mutant hit a 2-key constant channel.
- Round 3, ready and not run (e724002): the lower hull of the sole rolls without slipping. Local proof: /home/claude/suitanim/rollcheck.py on fa's LOD0 boot vertices.
  - Round 1 method: slide 0.29 cm, dip -19.8 mm (run 1 measured -19.6 mm).
  - Round 2 method: slide 13.22 cm (run 2 measured 13.4 cm).
  - Hull roll: slide 0.19 cm, dip 0.0 mm.
  - The run_keys mutant now targets the chest.

## For INT (17f)
- The approved boots sit 23-52 mm below y = 0 at rest (floor_y per suit). All clips use the rest sole level as the floor. To put soles on the floor, place each suit at y = -floor_y.
- idle and attack keys start at 1/60 s (approved files, unchanged). The new clips start at 0.

## Needs owner / lead
1. Go for round 3 (one empty commit to ci-art-suitanim starts it), or keep gliding in 17f.
2. dao's long robe on bone-heat weights balloons and dips under the floor at 6.4 m/s. A clean fix needs reweighting the robe (an approved-asset change) or a slower or shorter-stride dao run.
3. mo's front fall needs a look at the strips (round 2 shots were lost).
