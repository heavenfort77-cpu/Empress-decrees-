# W6 report: C12 school emblem standard (25 Nov overnight, branch ci-art-w6)

Goal (ASSET-LIST C12, GDD G1): one standard per school hall that tells which school's hall it is. One shared mesh; the nine schools
differ only by the banner's atlas cell (UV offset). Colours = the owner's 25 Nov mapping (W1a's 鼎 accents, ding_blender.py ACCENTS), except the za banner: cooler silver #b2bccb
(owner 25 Nov 02:4x, banner only);
bronze = the brass sheet only.

## Files
- assets/models/standard.glb: LOD0 skinned (pole bone + 3 cloth bones, clip `idle` 0-2.0 s), LOD1 and LOD2 static (placed at x +3 / +6
  m like W1a's GLBs). Extras on the armature: `schools` (CONFIG.SCHOOLS order), `atlas`, `cell_uv` (0.2, 0.5), `alpha_test` 0.5.
  Game use: banner map offset = ((i % 5) * 0.2, floor(i / 5) * 0.5), flipY false, alphaTest 0.5, DoubleSide, never transparent.
- assets/tex/school_standards.png: 1024 atlas, 5 x 2 cells of 0.8 x 2.0 m at 256 px/m, cell 10 empty. Source art/src/school_standards.klad.
- art/tools/standard_tex.py (klad ops), standard_blender.py (builder + gates), standard_glb.py (re-read), standard_check.py (atlas and
  play-size checks), standard_sheet.py; viewer art/viewer/beast.html `?model=standard&school=0-8&lineup=1&atlas=`.
- Shots: art/standard/round1/ (run 45457382729), round2/ (run 45460704861), round3/ (run 45464846183, the shipped files): standard_play_sheet.png (all nine at
  the play camera, FOV 50, pitch 40, 10.5 m), standard_detail_sheet.png, lineup.png, fa_za_option.png, gate logs.

## Sigils (original, no characters)
ru ritual cauldron, dao spiral, fa Qin steelyard weight (权: beam, cord, nose loop, ribbed dome on a foot band; round 3),
mo rammed-earth wall with a flat-lintel gate under a gate tower with a straight hipped roof (round 3), yinyang sun disc beside a moon ring over a horizon bar, za nine dots,
ming diamond in diamond, zongheng crossed arrows, nong sprouting plant.

## Gates, round 2 (run 45460704861, commit 7590d41)
| Check | Result | Mutations (each must FAIL) |
|---|---|---|
| Atlas (tex_check) | 49 of 49 | dup, blend, flat, bleed, tongue: 5 of 5 caught |
| Builder (tris 224 + card 24 / LOD1 94 / LOD2 40, height 3.84 m under the 4 m wall, weights, rigid pole, sway 0.188 m, seam, clip seconds, texel 256 px/m) | 18 of 18 | tris, weights, rigid, height, loop, texel, fps: 7 of 7 |
| GLB re-read (MASK 0.5, no BLEND, skin sums, LOD tris, UVs in cell, clip 0-2.0 s, extras) | 13 of 13 | blend, skin, clip, late, uv, schools: 6 of 6 |
| Play size (rectified sigil IoU 0.84-0.96 vs 0.75, sigil distinct max 0.46 < 0.75, field dE >= 10) | 10 of 11 | dup, blur: 2 of 2 |

FAIL: play field colours fa (lead white) vs za (silver) dE 7.1 in play (11.1 on the atlas). These are the owner's colours, so not
changed. The two still part by sigil (balance vs nine dots).

## Round 1 to round 2 (cause / removed by / proof)
- Clip exported 0.04-2.54 s: keys were at frames 1-61 and the scene ran at 24 fps / keys from frame 0 at 30 fps, scene range 0-60,
  plus a builder gate on clip seconds and a GLB check that the clip starts at 0 / glb clip 13 of 13, run 45460704861.
- Play check 3 of 11 was the check's fault: it compared the perspective-sheared banner with the upright cell. Now it rectifies each
  banner from its projected corners (viewer `quads`). The threshold went up from 0.45 to 0.75 because a 3 px blur passed at 0.45; it
  now fails 9 of 9 / run 45460704861.
- yinyang sigil (disc stacked over a ring) read as a numeral 8 at play size / now side by side over a bar / round2 play sheet.

## Verdict per school (my own look at round2/standard_play_sheet.png)
Reads as a hall standard (lacquer pole, brass finial and foot, banner with tongues). All nine sigils are distinct shapes, and none
reads as text. ru, dao, mo, yinyang, ming, zongheng, nong: PASS. fa, za: SHIP WITH NOTES, because their fields are too close in play
(dE 7.1) and they part only by sigil. The sway is gentle and hard to see in stills (0.19 m at the banner foot).

## Round 3 (owner 25 Nov 02:4x; commit 1eea8e5, run 45464846183)
Changes: the za banner field is #b2bccb. fa is redrawn as a Qin weight (no scales of justice) and mo as a rammed-earth wall under a gate
tower (no crenellations). The other seven sigils are unchanged (approved).
Gates: atlas 49 of 49 (fa-za dE 19.0 on the atlas; sigil IoU max fa-mo 0.45 < 0.75); builder 18 of 18; GLB 13 of 13; play 11 of 11
(fa-za dE 12.2 in play; rectified sigil IoU 0.84-0.92 >= 0.75). Mutations 20 of 20 caught (tex 5, build 7, glb 6, play dup and blur).
Verdict (my look at round3/standard_play_sheet.png): all nine PASS. fa reads as a hanging domed weight, though it could also pass
for a bell. mo reads as a stepped gate house; the cut earth courses make the wall look stepped at play size.

## Needs owner (round 2, both answered 02:4x)
1. fa vs za fields in play: (a) keep #c8ccd0 silver: dE 7.1, the gate stays FAIL, and they part by sigil only; or (b) lay za's banner
   silver cooler at #b2bccb: dE 12.2 in play, play check 11 of 11 (run 45460704861, play_zacool.txt, fa_za_option.png lower row). The
   change is on the banner only, since the 鼎 keeps its metal silver inlay.
2. Approve the nine sigils, the yinyang one above all.
3. Round 3: approve the new fa and mo sigils (round3/standard_play_sheet.png).
