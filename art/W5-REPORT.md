# W5 report: 皇家 guard and 反贼 rebels (overnight 25 Nov, worker W5, branch ci-art-w5)

Nothing goes into the game; no game code changed. Study and verdict table: art/Guard-Rebels-Study.md.
Runs: concepts 45435813341 (ComfyUI, 32 images); art runs 45440423895 (failed: missing ops dir and a tracked .pyc blocked the ci-out commit),
45442633307 (green; tex_check 37 of 39), 45445673747 (round 2, all green), 45446527903 (final, round 3; all numbers below are from it).
Builders also ran locally under flock for iteration (bpy 5.3, a few seconds each).

## Files
- Tools: art/tools/fodder_base.py (shared base, adapted from beast_blender.py and rig_test.py), guard_build.py, rebel_build.py,
  fodder_tex.py (klad op script for the new sheet), fodder_preview.py (quick sheets + silhouette gates), glb_info.py (GLB re-read check),
  shoot_fodder.mjs + art/viewer/fodder.html (three.js viewer: FOV 50, pitch 40, game lights, hall floor), tex_check.py (fodder_trim rules
  added), ci_art/job.sh.
- Models: assets/models/guard/{zu,nu,dun,che,wz}.glb, assets/models/rebels/{ls,fs,ss,qs}.glb (each: <key>_lod0 skinned + rig + clips
  idle/move/attack, <key>_lod1, <key>_lod2 static; ls also ls_w_<school> x9 skinned and ls_w_<school>_lod1, school colours in the rig's extras).
- Texture: assets/tex/fodder_trim.png (klad), source art/src/fodder_trim.klad, passes strip art/guard/round3/fodder_trim_passes.png.
- Shots: art/guard/round1-3, art/rebels/round1-3 (round 1 and the previews: flat-shaded tool sheets; round2/round3 viewer/: textured
  three.js shots from the runner), concepts in art/guard/concepts and art/rebels/concepts (reference only).

## Gates (run 45446527903). Per unit: builder gates + GLB re-read 5 + faction lineup silhouette 1
| Unit | Rounds | Gates | Numbers | Verdict |
|---|---|---|---|---|
| 卒 zu | 2 | 16 of 16 | tris 3232 / 914 / 266; windup 0.50 s, pike tip moves 2.38 m; half-width 0.45 (r 0.45); body 1.63 m, pike 2.36 m | PASS with notes |
| 弩手 nu | 3 | 16 of 16 | 3592 / 1050 / 312; 0.80 s, 0.60 m; body 1.47 m; IoU vs 卒 0.75 (round 2, at the limit) -> 0.70 | PASS with notes |
| 盾 dun | 2 | 16 of 16 | 3516 / 950 / 276; 0.50 s, 0.71 m; half-width 0.55 (r 0.6) | PASS with notes |
| 车 che | 2 | 16 of 16 | 1416 / 632 / 180; 0.90 s, ram 1.02 m; length 2.02 m, canopy 2.04 m, half-width 0.80 (r 0.9) | PASS with notes |
| 伍长 wz | 2 | 17 of 17 | 3448 / 954 / 276; 0.50 s, 1.28 m; banner top 2.93 m >= 1.15 x 2.36 (tallest squad member) | PASS |
| 黄巾力士 ls | 2 | 17 of 17 | 1634 + weapon 276 / 700 + 160 / 210; 0.80 s, 0.82 m; cloth bone heat solved 91% (rest nearest bone); weapon-only silhouettes 36 of 36 pairs under IoU 0.75 (max 0.50) | PASS with notes |
| 符水道人 fs | 2 | 16 of 16 | 1304 / 552 / 162; 0.80 s, 0.88 m; body 1.84 m | PASS |
| 死士 ss | 2 | 17 of 17 | 1308 / 536 / 160; 0.60 s, 0.42 m; crouch 1.34 m; glint hidden in idle/move, shown 0.2 s to the windup | PASS with notes |
| 渠帅 qs | 2 | 17 of 17 | 1472 / 748 / 224; 0.60 s, 1.57 m; pennant top 2.96 m >= 1.15 x 2.00 | PASS |
Shared: tex_check 39 of 39 (fodder_trim 14 of 14: density 256 px/m, brush 4.9 cm, lum sd 9.9, lacquer lum 31, blue 101, headband 154,
hemp 127, patch 180 sat 0.07); GLB re-read 45 of 45; silhouettes guard 10 of 10 (closest 卒/盾 0.72), rebels 6 of 6 (0.61), all nine 36 of 36.
Viewer shots 60 of 60 rendered without errors (software GL: look only, no frame rate).

## Needs owner
1. School patch colours use the game's COL.schools today: 道 #d5a03a is close to the headband yellow, 法 #6a6a6a and 阴阳 #3a3a3a are close
   to each other, 纵横 #40c0c0 is near the reserved hazard cyan (#3FE6F0, research rule). The weapon shape carries the read either way;
   the owner (or the approved suit palette) picks the final nine.
2. 死士 glint: a 0.36 m yellow star on each blade from 0.2 s to the 0.6 s windup; it reads in the tell shot but is small at the wide view.
   Option: add the game's ground tell or a brighter emissive flash.
3. Draw calls: guard types use two sheets (bronze_trim + fodder_trim) = 2 calls per type; 力士 = body + patch + its school weapon = 3.
   Option: paint a bronze row into fodder_trim (1 call per guard type) instead of the approved bronze sheet.
4. Instancing skinned units: three.js InstancedMesh does not skin. The rigs are small (5-17 bones; plates and bronze rigid) so a baked bone-matrix texture works;
   a game-side decision for the merge (not built tonight).
5. Tread belts do not roll (no UV scroll; the tread row shares the bronze material). Bootleg windups 0.9/1.0 s (墨, 阴阳, 纵横) need the
   game to time-scale the 0.8 s attack clip.
6. Close-up look: guard masks are plain and the rebels' faces are blank skin; fine at play size, simple at turntable distance.
