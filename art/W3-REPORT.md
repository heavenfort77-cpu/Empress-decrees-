# W3 report: the nine school suits (overnight 25 Nov 2026)

Branch ci-art-w3. Nothing goes into the game (no game code touched). Study and full verdicts: art/Qin-Lamellar-Suits-Study.md.
Merge note for the lead: take art/, assets/models/suits/, assets/tex/suit_*.png; leave out .github/workflows/art-run.yml and ci_art/ (CI files, never on batches-3-5).

## Runs
- Concepts: ComfyUI run 45435893887 (branch ci-comfy-w3, 36 images, 9 suits x 4 seeds).
- Art runner rounds (klad sheets, Blender build of all nine, silhouette gates, 104 viewer shots each): round 1 45440123875, round 2 45443383613, round 3 45444757353 (final builder code). Results on ci-out under out/art/ci-art-w3/<run>/.

## Shared files
- Builder art/tools/suit_blender.py (one humanoid base + per-school parts as data; rig, clips, LODs, gates); silhouettes and readability art/tools/suit_sil.py; floor contrast art/tools/suit_contrast.py; sheets art/tools/suit_tex.py + art/tools/suit_paint.py (klad); sheet rules added to art/tools/tex_check.py; viewer art/viewer/suits.html (+ &rim=1 demo), shots art/tools/suit_shoot.mjs, review sheets art/tools/suit_sheet.py.
- Sheets assets/tex/suit_lamellar.png (1024), suit_bronze.png (512), suit_cloth.png (512); klad sources art/src/suit_lamellar.klad, suit_bronze.klad, suit_cloth.klad; passes strips in art/suits/round3/.
- Lineups: art/suits/round3/lineup_play.jpg, lineup_wide.jpg, lineup_play_rim.jpg, sil_lineup_front.png, sil_lineup_34.png, sil_matrix.txt; gate logs gates.txt, sil.txt, tex_check.txt.

## Per suit (round 3; every suit had 3 runner rounds)
Gates per suit = 14 build (tris x3, weights x3, heat solve, materials, tell, tip travel, idle, height, texel density, GLB re-import) + 3 (screen height, LOD1 and LOD2 outline) + 1 floor contrast.
| Suit | Files | Gates | Key numbers | Verdict | Concept pick / alternates |
|---|---|---|---|---|---|
| 法 廷尉 | assets/models/suits/fa.glb, art/suits/round3/fa_sheet.jpg | 17 of 18 | 12,572 / 2,600 / 899 tris; tell 0.45 s, 1.13 m; 219 px | outline passes; fails floor contrast (1.9:1 body, 0% outline at 3:1) | fa_5102 / fa_5103, fa_5101 |
| 儒 君子 | ru.glb, ru_sheet.jpg | 17 of 18 | 13,464 tris; 0.50 s, 2.70 m; 224 px | same (1.8:1, 1%) | ru_5111 / ru_5112, ru_5113 |
| 道 真人 | dao.glb, dao_sheet.jpg | 17 of 18 | 10,168 tris; 0.42 s, 0.73 m; 191 px | same (2.4:1, 23%) | dao_5122 / dao_5121, dao_5120 |
| 墨 墨守 | mo.glb, mo_sheet.jpg | 17 of 18 | 11,264 tris; 0.50 s, 0.53 m; 161 px | same (1.6:1, 0%) | mo_5133 / mo_5130, mo_5132 |
| 阴阳 太极 | yy.glb, yy_sheet.jpg | 17 of 18 | 13,440 tris; 0.60 s, 1.45 m; 196 px | same (1.7:1, 5%) | yy_5142 / yy_5141, yy_5143 |
| 杂 门客 | za.glb, za_sheet.jpg | 17 of 18 | 13,644 tris; 0.45 s, 1.33 m; 192 px | same (1.6:1, 0%) | za_5151 / za_5153, za_5150 |
| 名 辩者 | ming.glb, ming_sheet.jpg | 17 of 18 | 10,680 tris; 0.50 s, 1.53 m; 204 px | same (1.6:1, 1%) | ming_5162 / ming_5161, ming_5163 |
| 纵横 说客 | zh.glb, zh_sheet.jpg | 17 of 18 | 13,140 tris; 0.45 s, 1.30 m; 234 px | same (1.4:1, 0%) | zh_5171 / zh_5173, zh_5170 |
| 农 耕者 | nong.glb, nong_sheet.jpg | 17 of 18 | 11,444 tris; 0.50 s, 1.36 m; 224 px | same (1.6:1, 0%) | nong_5182 / nong_5181, nong_5183 |
LOD1 is 2,599-2,600 and LOD2 899-900 triangles for every suit; 3 materials each; all nine at LOD0 = 109,816 triangles, 27 draw calls.

## Silhouette test
30 of 30: every pair IoU <= 0.75 (most alike: front za-zh 0.73, 3/4 ru-yy 0.71, side ru-za 0.70); LOD outlines 0.92-0.99. By eye on sil_lineup_front.png: all nine named from outline alone. Gate mutation-tested (a copied suit 1.00 FAIL; a cut LOD1 0.68 FAIL).

## Sheets
39 of 40 (round 3): FAIL suit_bronze plain brush scale 3.9 cm (min 4). Suit sheet rules mutation-tested (4 of 4 mutations caught).

## Needs owner
1. Floor contrast: dark lacquer cannot reach the palace study's 3:1 on the approved hall floor (floor luminance 0.06; black ink max 2.2:1). Options with measured gain: pale rim in the material (viewer demo: 0-23% -> 23-48% of outline pixels at 3:1, white specks on lamella lips), a 2 px lead-white outline in the game renderer (about 7:1, game code), light plates (about 2.9:1, loses Qin black), or accept.
2. suit_bronze plain brush run 3.9 cm vs 4 cm after 3 rounds.
3. 6.4-head stylisation (concepts 7.5-8.5 heads); school colour mapping is a proposal.
4. Concepts are weak (SD 1.5): proportions and three cues only.
