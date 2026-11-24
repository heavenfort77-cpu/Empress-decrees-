# W1c report: C8 the twelve bronze giants 十二金人 (overnight 25 Nov 2026, owner asleep; not approved, not in the game)

Branch ci-art-w1c. Three rounds. Final run 45452564180 (GitHub runner, software GL: look only, no frame rate). Method: art/Qin-Bronze-Castings-Study.md (W1a's beast round 4, 鼎 and vat sections). Nothing integrated; no game code changed.

## What the GDD and research ask, and what was built
- GDD (docs/BURNING-PALACE.md "Palace pieces"): they stand along the approach to the core; she wakes one per burnt wing; a woken giant slowly hunts the nearest suit with slow, big tells and heavy hits; killable mini-boss with health and a bar; every side hurts it; it collapses and lies there for the run.
- Research (docs/research/Qin-palace-medieval-tech-fusion.md): bell-stand bearers (Shiji "of the type of bell stands") cast from the conquered states' melted weapons; no image survives. One shared skeleton and body, with a distinct head, shoulder beam and weapon-fragment motif per giant (two per conquered state); patina dormant, brass-gold awake; keep the low LOD for distance.
- Built: one shared cast body and rig: a columnar tunic in three cast tiers with mould seams down both flanks, a belt hook (带钩), crossed collar, pauldrons, banded forearms, fluted column legs, a workshop-mark plate on the back. Its pose is a bell-stand bearer: the beam held overhead while dormant (a row of them reads as a bell stand), carried across the shoulders when awake. Each giant has its own head, beam and weapon motif. The weapons are high-tin bronze (pale edges, palTin), with a fused pool and a drip where each one enters the cast (round 3).
- **Size follows the game, not the 11.5 m source.** index.html PIECES2.giant has r 1.1 m and the box giant is 4.9 m with its health bar at y 5.4. The fore giants stand 5 m apart. Built: 4.63-5.13 m tall when carrying, 3.90-4.36 m wide, body radius below 2.6 m is 0.94-1.05.

| # | State | Head | Beam (the bell-stand beam) | Melted-weapon motif |
|---|---|---|---|---|
| 00 | 韩 Han | side topknot, moustache | square, upturned, dragon-head ends | crossbow prods crossed on the chest, trigger locks on the belt |
| 01 | 韩 Han | tall pointed cap with ear flaps, long beard | round, ring ends, two chime stones (磬) | prods arched over the shoulders, trigger locks down the chest |
| 02 | 赵 Zhao | wide-brimmed hat | double bar, scroll ends | ruff of spearheads round the neck |
| 03 | 赵 Zhao | bull-horn helmet, chin beard | round, knob ends, two large bells | bundle of spears across the back, spearheads on the belt |
| 04 | 魏 Wei | twin pheasant-tail plumes (鹖冠), full beard | octagonal, broad spade ends | halberd (戟) heads rising from the shoulders and chest |
| 05 | 魏 Wei | hood with a crescent crest and lappets | square, flared ends, row of cast teeth | apron of halberd heads, halberds at the hips |
| 06 | 楚 Chu | three-spike crown, forked beard | round, bowed down (yoke), knob ends, four bands | fan of swords behind the shoulders |
| 07 | 楚 Chu | tall flared mountain cap (高山冠), side ribbons | square, tiger-head ends | swords hanging round the tunic hem |
| 08 | 燕 Yan | bald with a scalp ridge, large hoop earrings, braided beard | octagonal, crane-head ends | arrowheads laid like scales on chest and shoulders |
| 09 | 燕 Yan | round helmet with neck guard, nasal and crest | twisted, ring ends, four small bells | quiver of arrows over the shoulder |
| 10 | 齐 Qi | flat board cap (板冠) with chin straps | round, arched, flared ends, cloud fin crest | dagger-axe (戈) blades on both forearms |
| 11 | 齐 Qi | twin high buns with rings, forked beard | square, bowed down, taotie mask-block ends | great dagger-axe across the chest, dagger-axes at the knees |

## Concepts (ComfyUI run 45441111768, SD 1.5 + LCM, 32 images; reference only, nothing traced)
- SD 1.5 did not draw a beam in any image. Job 3 ("melted weapons") gave Greco-Roman nudes: not usable.
- Body pick **6105**: a columnar tunic over a pleated column, broad square shoulders, heavy beard. Measured with H = 650 px from crown to feet: head 0.15 H, shoulders 0.45 H wide at 0.18 H, tunic hem 0.34 H above the ground. Built at H = 4.63 m: head 0.73 m, pauldrons about 2.1 m wide, tunic hem at 1.42 m (0.31 H). The legs are fluted columns, so a standing giant reads as columnar and can still walk. Alternates **6101** (broad robed statue) and **6102** (stocky, open stance).
- Head pick **6127**: broad face, heavy almond lids, a nose ridge from the brow, defined lips, round flat cap. Alternates **6126** and **6123**.
- 6131 (arms raised overhead) confirms the dormant bearer pose. Files: art/giants/concepts/.

## Files
- art/tools/giant_blender.py: the builder. It writes one GLB, runs the printed gates, and has all tunables in its CONFIG block.
- art/tools/giant_tex.py and giant_tex_check.py: the patina sheet (klad) and its check.
- art/tools/giant_shoot.mjs: the review shots.
- art/tools/giant_sheets.py: the lineups, the silhouette sheets and the silhouette gates.
- art/viewer/giants.html: the review viewer, with the game's FOV 50, pitch 40, two lights, hall floor, and the box giant and player box for scale. Options: ?g=, &state=dormant|awake, &clip=, &t=, &lod=, &sheet=.
- ci_art/job.sh: the runner job.
- assets/models/giants/giants.glb (6.6 MB, from run 45452564180). It holds giant_rig (28 bones), giant_body_lod0/1/2 (shared) and giant_gNN_lod0/1/2 (head, beam and motif), all skinned rigid to one rig, plus giant_flakes. Clips: dormant, wake (2 s), carry, walk (1 s loop, in place, 3.2 m/s), slam (1 s windup), sweep (1.2 s windup), hit, fall (0.8 s, ends lying). Node extras `giants` lists each giant's state, head, beam and motif.
- assets/tex/bronze_trim_patina.png (klad, art/src/bronze_trim_patina.klad): the dormant sheet, same row layout as the bronze trim sheet. Awake uses bronze_trim_brass.png (or bronze_trim.png).
- Materials: palBronze (sheet swap patina to brass), palTin (pale verdigris dormant, #D8CDA8 awake) and palPatina (flakes).
- Shots and sheets are in art/giants/round1/, round2/ and round3/:
  - lineup_awake, lineup_dormant, lineup_slam_windup, lineup_wide_lod2
  - sil_lineup.png and sil_lineup_wide_lod2.png (flat black, fight and wide framing)
  - giant_00-11 (awake, dormant, slam windup, 3/4, back)
  - clips_g00, lods_g00, the g00 passes
  - g00_play_default_sheet.jpg (the current sheet) beside g00_play_awake.jpg (the brass sheet)
  - gates.txt and sheet_gates.txt
  - round1/ and round2/ also keep their builder scripts.

## Gates (run 45452564180, final code): 119 of 119
- giant_blender.py 109 of 109:
  - triangles per giant at LOD0 / LOD1 / LOD2: 6604-7804 / 2844-2972 / 988-992 (budget 15000 / 3000 / 1000). LOD1 and LOD2 are built light, then decimated to the cap; LOD2 body 620.
  - carried height 4.63-5.13 m (4.5-5.3, under the bar at 5.4); width 3.90-4.36 m (max 4.4); body radius below 2.6 m 0.94-1.05 (max 1.12).
  - dormant height (beam overhead) 4.88-5.48 m (max 5.8).
  - fall end lies down: top 1.54-1.64 m, lowest -0.24 to -0.13 m.
  - every vertex rigid on one bone; hands on the beam in every sampled frame of every clip (worst 0.000 m); feet planted outside walk and fall (drift 0.000 m).
  - walk stance foot speed 3.20 m/s (game 3.2); walk feet reach their gait targets.
  - slam tell: the beam moves 0.67 m by 0.4 s and rises 1.04 m by the 1.0 s windup, then drops 3.44 m to 1.26 m, 0.91 m in front.
  - sweep tell: the beam end moves 1.47 m by 0.4 s and turns 80 deg by the 1.2 s windup, then swings 175 deg in 0.28 s.
  - hit react: chest moves 0.35 m.
  - wake: every patina flake is on the floor by 1.5 s, and the clip ends in the carried pose.
  - Blender's evaluated pose matches the solver (0.0 mm).
- giant_tex_check.py 6 of 6: patina sheet density 256 px/m, brush 5.3 cm, lum sd 12.0, saturation 0.31, mean lum 110 (80-125), hue 141 deg (120-170).
- giant_sheets.py 4 of 4 (twelve silhouettes, flat black):
  - whole figure, most alike pair 00-08: IoU 0.901 (max 0.92; mean 0.842)
  - top region (head, beam, motif), most alike 05-11: 0.785 (max 0.80; mean 0.673)
  - wide framing on LOD2, top region, most alike 05-07: 0.839 (max 0.85)
  - LOD2 keeps the LOD0 wide silhouette: lowest IoU 0.879 (min 0.8)
  - The margins are thin: 0.785 against 0.80.
- Mutation tests, all caught:
  - beam out of reach: grip and dormant height gates FAIL
  - slam windup cut: slam tell FAIL
  - walk step / 3: speed FAIL
  - flakes late: wake FAIL
  - pelvis too high for the gait: speed and reach FAIL
  - one silhouette copied over another: three IoU gates FAIL (1.000)
  - brass sheet as patina: value and hue FAIL
- Rounds:
  - round 1, run 45445939424: 109 + 6 pass, silhouettes 1 of 4 (05-07 top-region IoU 0.90)
  - round 2, run 45450924340: 119 of 119
  - round 3: melt pools added; 119 of 119

## Verdict (my read of the round 3 shots, software GL; not the owner's)
| Criterion | Result |
|---|---|
| Twelve distinct figures on one shared body, not recolours | PASS: own head, beam and motif each; silhouette gates 4 of 4 (thin margins) |
| Bell-stand bearers with the beam | PASS: the dormant row reads as a bell stand (beams overhead, bells or chime stones on 01, 03, 09) |
| Melted weapons, two giants per state | PASS with notes: fragments read as weapons fused into the cast close up; at play size the melt pools are subtle (bronze on bronze), and 02's neck ruff and 07's hem swords read weakly |
| Dormant patina, awake brass, patina falling away | PASS: patina sheet plus 12 flakes that crack (0.3-0.9 s), fall and shrink in the wake clip (clips_g00) |
| Slow walk, big tells, heavy hits, hit react, fall | PASS: gates above; tells of 1.0 s and 1.2 s are carried by the whole figure (beam overhead, body twisted) |
| Fits the game's collision, bar and spacing | PASS: inside r 1.1 below 2.6 m, under the bar, 3.9-4.4 m wide for 5 m spacing |
| Budgets 15k / 3k / 1k; LOD2 carries the far read | PASS: under all three; LOD2 silhouette IoU 0.88 against LOD0; LOD2 texture smears (decimated UVs), fine at the wide framing |
| Round where round, sharp where sharp; Qin look, not a toy | PASS with notes: lofted round masses, sharp blades, flanges and ridges. From the 40 deg play pitch the shared body reads squat (bell tunic, pauldrons): the weakest point, for the owner to judge |
| Brass-gold, not dark brown | PASS on the brass sheet only: the current sheet reads dark brown (g00_play_default_sheet.jpg), as W1a found |

Per giant: all twelve PASS the gates. Look notes by giant:
- 00, 01, 03, 04, 06, 09, 10, 11: strongest reads (dragon beam, pointed cap with chimes, horns and bells, plumes, sword halo, quiver, forearm dagger-axes, buns and chest dagger-axe).
- 02, 05, 07, 08: weaker; the motif reads less at play size, and 05-11 is the most alike top pair.

## Needs owner
1. **Size:** built to the game's 4.9 m box giant (4.6-5.1 m), not the 11.5 m source. A bigger giant needs CONFIG giant.r, the bar height and the 5 m spacing changed first.
2. **Sweep hit shape:** the game's sweep is a 7 x 3 m line ahead. The beam's arc reaches about 2.2 m round the body. Either change the hit shape to an arc or accept the gap.
3. **Bronze sheet:** awake shots use the brass sheet; the current sheet reads dark brown. This is the same pick as W1a's.
4. **Body read:** the columnar tunic follows concept 6105 but reads squat at the play pitch. Alternate bodies are 6101 and 6102, alternate heads 6126 and 6123. 02, 05, 07 and 08 are the weakest motifs if any are to be redone.
5. **Integration (not tonight):**
   - Body and parts are separate meshes with two materials each, so a giant is 4 draw calls; merging them per giant at load gives 2 (12 awake = 24).
   - The GLB is 6.6 MB uncompressed: compress it (meshopt or Draco, KTX2).
   - Swap the material between dormant and awake. Show the flakes only during the wake, pooled.
   - Recompute skinned bounds (never turn culling off). Warm up under the loading card.
   - The dormant pose stands 4.9-5.5 m tall with the beam overhead (no bar while dormant).
