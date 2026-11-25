# SUITANIM: run, hit and death clips for the nine school suits (25 Nov)

Status: DELIVERED from round 3, run 45520428413 (ci-art-suitanim ebd66a3). Every gate passes.
- Builder: 153 of 153
- Silhouettes: 30 of 30
- Clip gates: 234 of 234 (26 per suit, all nine suits)
- Mutations: 12 of 12 caught
- Shots: 65 of 65
- Merged fallback route: also 234 of 234

The approved meshes, weights and attack/idle clips are byte-identical to the approved GLBs (27 of 27 checks: attack, idle and mesh for each suit). The only change to the approved GLBs is the three new clips.

## Clips (built in art/tools/suit_blender.py, on the same rig)
- `run`
  - An in-place loop keyed every frame from 0 s.
  - Ground speed is the kit's speed tier: ru, yy, za, ming, zh 6.0 m/s; dao, fa 6.4 m/s; mo, nong 5.6 m/s.
  - IK legs. The sole rolls over its lower edge without slipping: slide 0.16-0.94 cm per cycle (max 2), no dip under the floor.
  - Timing from Muybridge plate 10: duty about 0.2-0.32, a flight phase, the heel rising off the toe.
  - Each school has its own style (RUN table). Cycle 0.33-0.58 s.
  - dao (owner 25 Nov): a short gliding stride at 6.0 steps/s, 1.07 m per step, feet tucked up under the robe. The approved robe weights are unchanged and the robe stays above the floor (run_floor -0.1 mm vs the rest floor, which is the boot sole).
  - In game: timeScale = actual speed / run_v.
- `hit`
  - 0.30 s; ends exactly on idle frame 0. Plate 51 gives the shape.
  - Strength by armour tier: Low 1.0, Mid 0.85, High 0.7. Feet planted.
  - Robe suits drop the hips at most 0.02 m.
- `death`
  - 0.9-1.1 s, ending lying still and touching the floor. A floor solve runs over all LODs on every frame.
  - Back falls: ru, dao, yy, ming, zh. Front falls over the knees: fa, mo, za, nong.
  - Largest lift: 0.04-0.15 m (mo 0.111 m, was 0.343 m in round 2).

## Rounds
1. Run 45515328643: clips 173 of 234. Causes found:
   - A new NLA track left unmuted overrode the pose while the next clip was authored.
   - A fixed toe pivot let the boot nose dip under the floor.
   - The exporter wrote quaternion keys with their own signs.
   - dao's robe went under the floor.
   - Front falls dived in mid-air.
2. Run 45518008969: clips 217 of 234. The ci-out push failed (GitHub 500 x6); gates were read from the run log.
   - The new sole roll let the contact point jump from mid-sole to the boot nose: 13-15 cm slide.
   - dao's robe front hem is weighted to the shins, so it dipped 76 mm.
   - mo lifted 0.343 m in its fall.
3. Run 45520428413: all gates pass.
   - Fixes: the sole's lower edge now rolls; dao has a short gliding stride; the front-fall pivot eases into the lying height; the mutant now targets the chest; the ci-out push uses backoff plus a fallback branch.
   - Local checks before the run: /home/claude/suitanim/rollcheck.py and robesim.py. Both reproduced the earlier failures within 1-13 mm.

## Look (strips art/suits/anim)
- mo front fall: recoil, kneel at about 0.5 s, falls forward over the knees, lies face down with the crossbow ahead. No pop.
- dao run: clears the floor, but the robe flares into a bell in swing and the feet show under it at toe-off. That is the bone-heat robe weights at this speed. The owner should judge it at play size.
- The cloth robes on za and zh (knee length) balloon in the run but stay above the floor.

## For INT (17f)
- The approved boots sit 23-52 mm below y = 0 at rest. Every clip treats that rest sole level as the floor. To put the soles on the floor, place each suit at y = -floor_y (art/suits/anim/suits_info.json).
- The new clips start at 0 s. The approved idle and attack start at 1/60 s.
- Tools: suit_clip_check.mjs (gates, three r171 in Node), suit_clip_signfix.mjs (run after the builder), suit_clip_merge.mjs (fallback), suitanim_shoot.mjs and suitanim_sheet.py, and the strip mode in art/viewer/suits.html.
