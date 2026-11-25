# Colour clarity: characters on the palace floors (study and rules)

Status: proposal, ONE round (COLOUR, 25 Nov 2026). Not approved. Owner 25 Nov 13:08 with the screenshot of the nine suits on the hall floor:
"work on the colour that it is clear and not one mess when character on it". Owner decision 13:1x: change BOTH sides (hall floor calmer
and less saturated, replacing the approved round 2 floor; a light rim plus school-colour trim on every character). Suits keep Qin court
black lacquer plates; royal guards keep bronze and blue. Method: cocolito (measure, write exact values, compare at the same scale).

## 1. Measured before (local, numpy; no render)

Contrast = WCAG relative luminance, (L1 + 0.05) / (L2 + 0.05), L from linear sRGB (0.2126 R + 0.7152 G + 0.0722 B).

| Floor texture (1024 px, 256 px/m) | relative luminance | mean lum (0-255) | lum sd | saturation | own marks p95/p5 | autocorrelation half-width x by y |
|---|---|---|---|---|---|---|
| hall_floor round 2 (approved, in the game) | 0.081 | 77 | 9.1 | 0.52 | 1.55:1 | 39 x 10 px (15 x 4 cm, one-way strokes) |
| hall_floor round 1 (for reference) | 0.061 | 68 | 4.9 | 0.71 | - | 51 x 13 px |
| stone_paving (court) | 0.249 | 136 | 9.1 | 0.10 | 1.31:1 | 6 x 3 px |
| floor_tiles (corridor) | 0.164 | 112 | 9.2 | 0.10 | 1.78:1 | 4 x 7 px |
| garden_ground (garden) | 0.147 | 106 | 8.5 | 0.34 | 1.26:1 | 4 x 3 px |
| timber (bridge deck, also beams) | 0.092 | 83 | 11.3 | 0.47 | 1.73:1 | 8 x 65 px |

Floor names from src/palace_art.js on int-17c: hall and core keep the box floor with hall_floor; court palStone = stone_paving; corridor
palTiles = floor_tiles; garden palGround = garden_ground; bridge palTimber = timber.
Note: the brief's "luminance 0.062, saturation 0.71" are the round 1 texture's numbers; the file in the game (identical on int-17c and
batches-3-5) is round 2 at 0.081 / 0.52. On screen the round 2 floor is at 0.060 (below).

Owner screenshot (owner_suits_on_floor_1308.jpg, 1600 x 900, JPEG, figure masks by colour so approximate):
floor on screen: relative luminance 0.060 (sd 0.013, p5 0.046, p95 0.088), saturation 0.56. So screen = texture x 0.75 under the game's two
lights (hemisphere 1.1 + sun 2.2 at 51 degrees, no tone mapping: 0.21 + 0.55 of the albedo; in the figure's own shadow only 0.21).

| Suit | body median luminance | body vs floor | outline pixels >= 3:1 | where it melts |
|---|---|---|---|---|
| 法 fa | 0.009 | 1.87:1 | 0% | everywhere |
| 儒 ru | 0.012 | 1.76:1 | 0% | everywhere |
| 道 dao | 0.207 (yellow robe) | 2.25:1 | 12% | head and armour; the robe only partly reads |
| 墨 mo | 0.015 | 1.69:1 | 0% | everywhere |
| 阴阳 yy | 0.013 | 1.72:1 | 2% | all but the white spheres and horns |
| 杂 za | 0.020 | 1.57:1 | 0% | all but the pale skirt edge |
| 名 ming | 0.018 | 1.65:1 | 1% | all but the feather |
| 纵横 zh | 0.038 | 1.23:1 | 0% | everywhere, the green cloak has the floor's value |
| 农 nong | 0.016 | 1.69:1 | 0% | everywhere |

Suit sheet (suit_lamellar.png) and models (UV rows by surface area, local GLB read): the "brown" plate rows are already as dark as the black
rows (mean lum 43 against 36); they differ by saturation (0.59). Brown plate and lamella rows cover 14 to 72% of a suit; the school cord rows
5 to 9%; the cinnabar edge row is not used by any model. So the mess is a value problem (dark figure on a dark, busy, saturated floor), and
the school colour sits on too small and too dark an area: cord relative luminance 儒 0.15, 墨 0.10, 名 0.07, 纵横 0.19, 农 0.10.

## 2. The 3:1 maths (why both sides must change)

- Black lacquer on screen is 0.01 to 0.03. Against the old floor (0.060): (0.060 + 0.05) / (0.02 + 0.05) = 1.57:1. A darker figure
  cannot help: even pure black gives 2.2:1. Black on a dark floor can never reach 3:1.
- For the black body itself to reach 3:1 the floor must be at 3 x (0.02 + 0.05) - 0.05 = 0.16 on screen (texture 0.213); 2.5:1 needs 0.125
  on screen (texture 0.167).
- A pale rim (lead white, unlit, 0.74) reaches 3:1 on any floor up to (0.74 + 0.05) / 3 - 0.05 = 0.213 on screen. With margin: 0.20.
- So the window where BOTH the black body and its pale rim read is a floor at 0.125 to 0.20 on screen = texture 0.167 to 0.26.
  The hall floor is aimed at texture 0.20 (screen 0.15): black body 2.9 to 3.1:1, rim (0.79 / 0.20) = 3.9:1.
- Trim on a black plate: 3 x 0.07 - 0.05 = 0.16 on screen = texture >= 0.21.

## 3. Rules (proposed)

Floors (every walkable floor in every room; check: art/tools/floor_rule_check.py, on screen: art/tools/colour_measure.py)
1. Texture relative luminance 0.167 to 0.26 (on screen 0.125 to 0.20). No floor a character stands on may be darker or lighter.
2. Saturation: mean HSV saturation at most 0.50; the hall floor 0.38 to 0.50 (still a cinnabar 丹地 floor, not grey).
3. The floor's own marks: p95 against p5 at most 1.30:1 (a floor mark must never look like a figure edge). Hall floor luminance sd 5.5 to 8
   (the palace study's 8 to 30 stays for walls, pillars, doors and props; the hall floor row of tex_check.py is re-based on purpose).
4. Stroke scale on the hall floor: autocorrelation half-width at most 20 px (8 cm) on both axes, x:y at most 2 (no long one-way grain);
   tex_check.py brush-scale run 4 to 15 cm kept.
5. Density 256 px/m, seams clean, 50 cm block sd at most 3.5 (tex_check.py).

Characters (every character: suits, guards, rebels)
6. Rim: the existing inverted-hull outline (src/chars.js CHR.outline) in lead white 0xe6dfcc, unlit, 2 px on screen at every distance.
   Gate: at least 50% of each figure's outline pixels at >= 3:1 against the floor right behind them, at 10.5 m and at 14 m.
7. Plates: black lacquer, mean lum 20 to 45, saturation at most 0.42 (the brown rows become brown-black).
8. Trim brightness per school (cord rows; texture relative luminance >= 0.21 so the cord reads 3:1 on its own plate):

| School | pigment (owner mapping) | approved cord | proposed trim | relative luminance |
|---|---|---|---|---|
| 法 fa | lead white | #d9d2c3 | #d9d2c3 (kept) | 0.65 |
| 儒 ru | ochre | #94622c | #b88038 | 0.26 |
| 道 dao | gold | #e2b84a | #e2b84a (kept) | 0.51 |
| 墨 mo | cinnabar | #a8321e | #d6583e | 0.22 |
| 阴阳 yy | bone black | #1a1614 | #1a1614 with a lead-white strand #d9d2c3 | strand 0.65 |
| 杂 za | silver | #b2bccb | #b2bccb (kept) | 0.50 |
| 名 ming | Han purple | #5b3f8c | #9070d0 | 0.22 |
| 纵横 zh | malachite | #2f8a5c | #379e6a | 0.26 |
| 农 nong | azurite | #2e5a9c | #5286d2 | 0.24 |

9. Guards keep bronze and blue, rebels their hemp and patches: rim only, no texture change.

## 4. Made in this round (files)

- Hall floor round 3: art/tools/palace_tex.py floor() (seed 101 kept; base #a4705c; marks short, in every direction, plus fine grit), painted
  in klad on the runner by art/tools/floor_calibrate.py, which corrects four CONFIG scalars until the targets above are met.
  Round 2 kept: art/round2/tex/hall_floor.png, art/round2/src/hall_floor.klad, art/round2/palace_tex_round2.py.
- Candidates (not replacing approved files): corridor tiles and garden ground lifted in linear light (TEX_GAIN 1.20 and 1.35).
- Suit sheet proposal suit_lamellar_qin.png (art/tools/suit_tex.py with SUIT_QIN=1): same rows and UVs, brown rows as brown-black lacquer,
  cord rows in the trim colours. No model is rebuilt.
- Viewer and measures: art/viewer/colour.html, art/tools/colour_shoot.mjs, colour_measure.py, floor_rule_check.py, trim_check.py.

## 5. Results

RESULTS_PLACEHOLDER
