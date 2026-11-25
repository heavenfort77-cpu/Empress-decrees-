# FIXB report: palace surfaces and props after the owner's picks (25 Nov 02:1x-02:2x)

Branch ci-art-fixb (from batches-3-5 916292f). This is art only: index.html and tests/ were not touched. CI files (.github, ci_art) exist only on this branch.
Runs (art-run workflow, results in ci-out `out/art/ci-art-fixb/<run>/`):
- Round 1, run 45462167005 (commit 9d7fb2e).
- Round 2, run 45467670225 (commit e5a7695). This run is final. Every number below comes from its job.log, unless a line says round 1.

The deliverables commit adds the round 2 outputs (PNGs, .klad sources, GLBs, sheets, gate logs). No code changed after e5a7695.

## Checks on the final run (45467670225)
| Check | Result |
|---|---|
| tex_check | 258 of 260. FAIL signal_flags contrast (parked, see A19). FAIL suit_bronze (known, not FIXB). |
| Texture mutations | 23 of 23 caught (9 are new this round) |
| Mesh gates | 102 of 102 |
| Mesh mutations | uv 28, budget 27, dims 3, dais 1 (new), rack 1 (new). FAIL lines must be above 0, and all are. |
| Tally | 8 of 8. Mutations: budget 3, stripes 1 (both caught). |
| Mercury C7 (merc_blender, unchanged) | 9 of 9 |
| Shots | 70 of 70 clean |
| On-screen gates (`art/tools/fixb_measure.py`) | 16 of 16 |
| On-screen mutations | 12 of 12 caught |

Repaint check: the approved hall_wall repaints with mean absolute difference 0.0 against the committed PNG.

Logs: art/arch/round3/{tex_check,tex_mut,arch_gates,arch_mut,measure,measure_mut,repro}.txt, art/tally/round3/tally_gates.txt, art/merc/round2/gates.txt.

## Items (gates N of N, verdict)
| Item | Gates | Verdict |
|---|---|---|
| Brass for every bronze piece | brass-only 1 of 1: 69 shots, none loads bronze_trim.png or bronze_trim_patina.png. A mutation shot on the bronze sheet is caught. | PASS. arch.html palBronze now uses bronze_trim_brass. Tally and mercury were shot with sheet=brass. Pillar sleeve, door bar and masks, and dais edging are re-shot (art/arch/round3/r2/brass_pieces.jpg). |
| A19 flags, W1a mapping | tex 7 of 8. school colours: all 9 within 40 RGB of the owner mapping. band reads: all 9. **contrast: lum sd 30.5 against a maximum of 30.** | **PARKED after 2 rounds.** The colours are right, in CONFIG.SCHOOLS order (flag_i = school i). Yinyang's bone black gets 2 px bone keylines. Round 1 measured sd 35.4. Thinner bands (8 to 6 px) brought it to 30.5. The rule was not loosened. Proposed fix: BAND_W 6 to 5. The new PNG is in assets/tex because the old one fails the owner mapping. At the play camera the wall-walk flags are small and edge-on. |
| A2 plaster | hall_wall value 150-185: 1 of 1 (169). Repaint diff 0.0. | **KEPT (approved asset not changed).** Round 1 shot a candidate at 0.83x (mean 140) beside the floor, pillar and door. It still read as one palace, but it failed the study brush-scale rule (22.1 and 21.1 cm against 4-15). On screen it also put the wall under the floor (hall_wide wall 62, floor 64; the approved wall is 71). The study range is updated to 150-185 (art/Qin-Palace-Painted-Study.md), and tex_check gets the matching value rule. The candidate (PNG and .klad) and its side-by-side are in art/arch/round3/plaster_candidate/. No backups were needed because the approved files were not touched. |
| A16 pond water | tex 9 of 9 (lum 134, block sd 2.2, teal). On screen 2 of 2: pond 99 vs ground 93; margin 105 vs open water 97. | PASS. The pond reads as light blue-green water, not a hole. It uses a new pond_water texture plus vertex colours: the open water is darker and a 1 m margin is pale. The black lake A15 is unchanged. |
| A17 star inlay on the core floor | tex 9 of 9 (alpha loss 0.17, coverage 0.02-0.06, floor lum +2.4, nothing in the edge border). On screen 5 of 5: floor dE 0.12 wide and 0.26 play; hazard-ring contrast 67.5 to 67.5 and 71.0 to 70.9; inlay seen at play, mean lum 28.9. | PASS. It is a brass-line decal (star_inlay, alpha test) over the approved 丹 floor, which itself is not repainted. Each 4 m cell is turned or mirrored, so there is no repeat. It is visible at play and almost invisible at the wide camera (subtle, by design). The tell colours are clear: 138 from the ring colour, 73 from the warned colour. One draw call. |
| B10 dais 1.5 m | 1 of 1: dais top 1.50 m on 12 x 6 m (the game block is 12 x 6 x 1.5). The dais mutation is caught. | PASS. Throne size is set separately (next row). |
| Throne larger | Mesh 1 of 1: screen top 3.67 m over the dais (x1.4). On screen 1 of 1: 180 x 86 px to 186 x 115 px at core_wide (height x1.34). | PASS on the gate, **PARTIAL on the look**: still a small object at the far end of the wide view. Fixed on the way: the W2 viewer had turned the throne 180 deg (screen toward the camera, round 1-2 sheets). It now faces south. |
| A20 racks bigger | Mesh 3 of 3: rack 2.5 x 0.8 x 2.8 m, 5 shelves, 100 tris. Bundles 0.5 x 0.09 m lie end-on. The rack mutation is caught. On screen 1 of 1: 0.0037 to 0.0206 of hall_wide (x5.5). | PASS with note. There are now 9 racks: 3 on the west wall plus 6 on the north wall facing the camera (a placement change). They read as scroll racks at play, and as rows of shelved scrolls at the wide camera (small). "Burning" still needs the fire effects (D). |
| A16 fuller planting | On screen 2 of 2: calls 41 to 41, tris 3734 to 8934 (garden_wide); card coverage 0.071 to 0.174 (x2.4). | PASS. 820 cards at 1.2-2.2 m (was 170 at 0.8-1.3), still 4 instanced calls with no shadow casting. |
| A14/C7 mercury | Matcap tex 6 of 6 (mean 130 to 149; value rule raised to 145-190). On screen 2 of 2: idle 140, **warn 211 (+71 lum)**, hot 236. Round 1 on the same camera: idle 139, warn 161, hot 196. Shimmer: two warn stills 0.15 s apart differ by 30.9 lum (idle 2.1). C7 gates 9 of 9. | PASS with notes. Warn is clearly brighter in a still. The shimmer is a sliding ripple normal map; round 1's 0.5 m tile read as chain mail, and round 2 uses a calmer 1.33 m tile. At close range the 1 m mercury tiles show seams in the ripple. For the game this is an integration note: normal map plus UV offset in mercWarn. |
| C11 tally at 1.5k | 8 of 8: LOD0 1468 / 1500, LOD1 592 / 600, LOD2 236 / 260; 9 dark inlaid stripes per half, 6.5 cm; tiger 1.7 m long on a 2.7 m stand. | PASS with notes. At play size it reads as a striped walking tiger, split in two halves (round 2 read as a faceted cat). Gold inlay vanishes on brass (W1a measured dE 7.3), so the stripes are dark. The body is still faceted and the jaw boxy. Round 3a's angular tail was fixed in 3b. |
| Water clock slot, 阙 north | no change | as decided |

## Files
- **Tools:**
  - arch_tex.py: MERC_LIFT, POND, INLAY, SCHOOLS, KEY_*/BAND_W, pond_water(), star_inlay().
  - palace_tex.py: PLASTER_K hook. Its default 1.0 keeps the approved ops byte-identical.
  - tex_check.py and tex_check_mut.py: new rows and rules.
  - arch_blender.py: DAIS, GAME_DAIS, THRONE_S, RACK, BUNDLE, mutations dais and rack.
  - tally_blender.py: round 3.
  - New: fixb_shoot.mjs, fixb_measure.py, fixb_sheets.py.
- **Viewers:**
  - arch.html: brass, pond, inlay, tell rings, masks, glbdir=arch_r2 before/after, at=x,z. Also fixes the async tag race that polluted the round 1 rack mask.
  - beast.html: MERC states, ripple shimmer, mask.
- **Assets:**
  - assets/tex: mercury_matcap, signal_flags, pond_water (new), star_inlay (new). Sources in art/src/*.klad.
  - assets/models/arch: slip_rack, slip_bundle, throne_dais.
  - assets/models/tally.glb.
- **Sheets:**
  - art/arch/round3/r1 and r2: core_inlay, core_throne, hall_racks, garden, flags_court, brass_pieces, textures.
  - art/arch/round3/plaster_candidate/
  - art/tally/round3/: tally_round3_r2.jpg; the r1 sheet is in r1/.
  - art/merc/round2/: merc_round2_r2.jpg; the r1 sheet is in r1/.
  - Earlier rounds are kept.

## Needs owner
1. **Flags:** allow a third round (BAND_W 6 to 5; the contrast is 30.5 against a maximum of 30), or accept as is. Also, the wall-walk flags are small and edge-on at play.
2. **Throne:** x1.4 is still small at the wide camera. Options:
   - go to about x1.7, which needs a top tier deeper than the game's 6 m dais block;
   - add a canopy;
   - accept it.
3. **Plaster:** A2 is kept and the study range is now 150-185. The darker candidate is kept if you prefer it, but it needs stroke-contrast work first (it failed brush scale).
4. **Racks:** 6 of the 9 are now on the north wall, facing the camera. Is this placement OK?
5. **Mercury:** ripple seams between the 1 m tiles show at close range. The shimmer was judged from stills only (the game needs the normal map plus a UV offset in the warn state).

## Process note
The round 2 push (e5a7695) was secret-scanned right after the push instead of before it. There were 0 hits, and the order slip is logged in overnight.log.
