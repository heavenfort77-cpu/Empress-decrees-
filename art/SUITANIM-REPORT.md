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

## Robe round (owner 25 Nov "rebind robes calmer": dao, za, zh) - NOT DELIVERED
Run 45522030493 (ci-art-suitanim 588b218). Results: builder 152 of 153, silhouettes 30 of 30, clip gates 246 of 246, mutations 13 of 14, shots 74 of 74.
- Calm binding (ROBE_CALM in suit_blender.py; weights only): each robe vertex's shin weight moves to the thigh on the same side, the leg share is partly spread over both thighs and partly given to the hips.
  - Meshes unchanged: 0 accessors differ (positions, normals, UVs, indices).
  - Weight changes: 2113 / 1324 / 1252 vertices on dao / za / zh, all inside the robe (weights_scope: 0 outside).
- Robe flare gate. Threshold = the calmest suit before this round, fa at 0.379 m. Results (was → now):

  | Suit | Before | Now |
  |---|---|---|
  | dao | 0.413 | 0.151 m |
  | za | 0.454 | 0.210 m |
  | zh | 0.538 | 0.220 m |

- dao run: kick 0.4, m0k 0.3, the 1.07 m stride is kept.
- FAIL (builder): dao death floor solve lifts the body 0.364 m at frame 32 (0.53 s; max 0.25). The body visibly hovers in the strip. Cause: the calm robe follows the hips, and the back-fall squat lowers the hips 0.40 m while the hem is only 6 cm above the floor. The proposed fix is a shallower dao buckle (a stiff topple); whether it clears the gate is unknown until a run.
- MISSED mutant (fixed, [skip ci]): restoring dao's old weights did not trip the flare gate, because dao's run itself changed this round. The mutant now targets za. Local check on the returned za GLB: 14 of 14 mutations caught.
- Look: the dao robe stays calm (a steady cone, toes show at the hem). Its death is a stiff cone topple.
- dao play-size strip: ci-out out/art/ci-art-suitanim/45522030493/suits/strips/dao_strip_play_run.jpg
- Backup of the delivered GLBs: /home/claude/suitanim/backup_suits_before_robecalm. batches-3-5 still holds 64b7bd5.

## Robe round 2 - DELIVERED
Run 45523064942 (ci-art-suitanim 99f6dba).

Gates:
- Builder 153 of 153
- Silhouettes 30 of 30
- Clip gates 246 of 246, including robe_flare and weights_scope
- Mutations 14 of 14 (the robe_flare mutant now targets za)
- Shots 74 of 74

Changes this round:
- The calm robe weights from 588b218 are kept. Meshes are identical; only robe weights changed.
- dao's death is a stiff backward topple. The whole body turns as one piece about a floor point under its rear-most vertex, so the floor solve lifted 0.0 m (was 0.364 m).
- Robe hem swing per run cycle (limit 0.379 m): dao 0.151, za 0.210, zh 0.220.

Look (strips):
- za and zh robes hang calmly from the hips. At full stride the forward thigh shows in front of the robe panel: the cloth no longer follows the legs, so it clips there.
- dao falls like a rigid statue and lands on its back. No hover.
- dao's robe is a steady cone with no flare.

dao play-size strip: art/suits/anim/dao_strip_play_run.jpg (also on ci-out under out/art/ci-art-suitanim/45523064942/suits/strips/).
Backup of the previous GLBs (64b7bd5): /home/claude/suitanim/backup_suits_before_robecalm.

## Trim + recolour round - DELIVERED
Run 45529217658 (ci-art-suitanim 9649120; code = f186409 plus the fa tint).

Gates:
- Builder 153 of 153
- Silhouettes 30 of 30
- Clip gates 273 of 273, mutations 15 of 15
- tex_check suit_lamellar: all pass
- Colour gates 22 of 22, colour mutations 4 of 4

Robe binding (za, zh):
- The front of each robe follows its own thigh: za Kb .4 Kf .8, zh Kb .35 Kf .8.
- Hem swing: za 0.286 m, zh 0.341 m (gate 0.379).

Colour:
- One school colour mapping. Cloth tints are adjusted for the cloth sheet; each suit's cloth median is within dE 0.4 of its school colour (fa 6.6, see below).
- 法 cloth is a brighter, creamier lead white, #ffffed (owner).
- Cord rows repainted in klad. Shipped sheet = the approved rows 0-735 plus the klad cord rows. The full klad repaint (art/src/suit_lamellar.klad) differed in 226 pixels outside the cords, so those rows were not taken from it.

School-colour sash and sleeve cuffs for fa, ru, mo, nong:
- New cloth parts appended to every LOD. The approved mesh data is an exact prefix of the new data.
- Tris: LOD0 11,940-14,124; LOD1 about 2,664; LOD2 910-917.
- Cloth visible at play size: ru 813 px, fa 870, mo 1,190, nong 1,755.

Red-floor pairs: the closest pair is fa-za at dE 11.9.

Heads not touched. Lineup shot: art/suits/anim/lineup_colour.jpg.
