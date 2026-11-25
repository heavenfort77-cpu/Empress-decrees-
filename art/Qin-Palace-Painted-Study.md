# Qin Palace Painted (3D, klad-painted materials): study

Status: proposal (not approved). Entry number: <next number>. Nearest neighbour: not checked (Style-Library.md is in the Art Styles Project and could not be opened from this session; going by what is recorded about the library, its entries are pixel-art character, mech and lighting studies, none for 3D architecture).
Type: single. Where: Empress Decrees, the Burning Palace (three.js, tier medium, desktop master, phone dialled down).

- Reference: Qin palace records (咸阳宫 site No. 1: 丹地 vermilion burnished floor, white-ground plaster with black lozenge bands, timber 都柱; Qin lacquer black and vermilion; bronze 铺首衔环), sources in art/REFERENCES.md. Technique reference only; no photo traced or sampled. Licence of the records: not applicable (descriptions).
- Measured on: sample 01, five klad textures (assets/tex, 1024 px, PNG) and the Blender lion (branch lion-sample-01), 24 Nov 2026, in the code tool and in a software-GPU screenshot of the exact build. Not seen on a real screen by Claude.

## Measured, sample 01

| Texture | mean lum | lum sd | mean sat | unique colours | texels per metre (u x v) | flat-run (same tone along a row) | main tones (k=6, share %) |
|---|---|---|---|---|---|---|---|
| hall_floor | 62 | 4.7 | 0.71 | 1,121 | 256 x 256 | 163 px = 64 cm | #712f20 23, #753222 22, #6d2d1e 19, #7a3524 19, #803928 9, #682a1c 7 |
| hall_wall | 130 | 65.0 | 0.23 | 2,758 | 256 x 256 | 44 px = 17 cm | #b8ac94 38, #1d1714 23, #b0a48b 21, #4a433a 8, #d2c8b2 7, #865b4c 2 |
| pillar | 33 | 17.0 | 0.47 | 2,127 | 543 x 256 | 8 px = 1.4 cm | #742d1e 24, #231a15 23, #17110e 20, #1e1612 17, #1a1310 14, #452d20 3 |
| door | 35 | 25.4 | 0.42 | 1,559 | 256 x 293 | 10 px = 3.9 cm | #654e32 22, #15100d 21, #211913 21, #1c1511 20, #19130f 14, #392c1d 1 |
| lion_stone | 135 | 4.0 | 0.08 | 333 | 640 x 640 | 67 px = 10 cm | #88857d 45, #848178 18, #8b887f 17, #8d8a82 12, #908d84 5, #939087 3 |

## Alignment verdict: off (three measured problems, one described)

1. Paint density differs 45x. The floor and the lion stone are near-flat fills (lum sd 4.7 and 4.0; tone runs of 64 cm and 10 cm), while the pillar and door are busy brushwork (sd 17 and 25; runs of 1.4 cm and 3.9 cm). On screen the floor and lions read as plain colour next to painted pillars and doors: two styles in one room.
2. Texel density differs up to 2.5x. Floor, wall and door are at 256 px per metre; the pillar is 543 x 256 (strokes stretched 2:1 vertically); the lion stone is 640 (marks 2.5x finer than the walls).
3. Saturation: the floor (0.71) is far above every other surface (0.08 to 0.47), so the floor outshouts the walls, props and characters.
4. Shape (described, not measured): the Blender lion is soft metaball forms (rounded, toy-like) while the architecture is hard-edged boxes with painted detail. Carved stone needs hard bevelled planes and cut grooves, not blobs.

## Values (proposed rules for every palace surface and prop)

- Texel density: 256 px per metre on desktop, 128 on phone, on every axis (pillars: repeats around the shaft set so u = v; props: world or box mapping at the same density). Check: every material within 0.8x to 1.25x of 256.
- Brush scale: the median flat-run on screen 4 to 15 cm for every broad surface; fine detail (rules, lozenges, masks) may go lower but no surface above 20 cm (no flat fills).
- Local contrast: luminance sd 8 to 30 inside one material region (bands such as dado and frieze excluded); floor and stone raised from 4-5 to at least 8 by stronger burnish, wear and chisel marks.
- Value plan (mean lum, 0 to 255): Qin black lacquer 25 to 40 (matte, roughness 0.75 to 0.9); cinnabar floor 55 to 75; bronze 70 to 110; stone 120 to 150; lime plaster 150 to 185 (updated 25 Nov, see below). Characters must stay readable on each (3:1 against the floor and walls behind them).
- Plaster range update (FIXB 25 Nov; owner 02:2x: 'plaster can change but must align to surroundings'): the approved A2 wall measures 169 (A10 mural plaster 168), over the old 120-150. A candidate repainted at 0.83 x the plaster colours (mean 140) was shot beside the approved floor, pillar and door at the game camera (runner run 45462167005, art/arch/round3/plaster_candidate/). It still read as one palace, but it failed this study's brush-scale rule (runs 22.1 cm and 21.1 cm against 4-15 cm: the darker strokes merge), and on screen it put the wall under the floor (hall_wide wall 62 vs floor 64; approved wall 71). So A2 is kept and the plaster range is 150-185 (tex_check: hall_wall and mural_wall value 150-185). At the game camera the vertical walls render near the floor's value (71 vs 64), so the brighter texture does not glare.
- Saturation cap 0.55 for floors and walls (cinnabar floor to about 0.5 to 0.55); accents (vermilion bands, bronze) up to 0.6 in small areas.
- Palette ramps (from sample 01): lacquer #15100d #1d1612 #231a15 #2c2320; vermilion #742d1e #86281a #9a4a34; plaster #b0a48b #b8ac94 #d2c8b2; bronze #3a2b1a #654e32 #7b5f3a #b2925e, verdigris #3f5a4c; cinnabar floor #682a1c #712f20 #7a3524 #8e4330; stone #7b786f #88857d #939087 #a9a59b.
- One light: the game's sun and hemisphere only; no light or shadow painted into tiling textures (only in one-off pieces such as door masks).
- Props (lion, ding, huabiao, vats, cranes, giants): geometry is carved, hard-edged, bevelled (planes and cut grooves), 7k / 2.5k / 800 triangles (LOD0/1/2); textures are klad materials from the ramps above at 256 px per metre, never the source model's own photo textures.
- Scanned or downloaded models (Sketchfab etc.): geometry only, CC0 or CC BY only (never NC or ND), decimated to the budget, re-materialled in klad; credit in CREDITS.md.

## Samples, round 1 (24 Nov 2026, not approved)
### Files
- assets/tex/hall_floor.png, hall_wall.png, pillar.png, door.png, lion_stone.png (1024 px); sources art/src/*.klad; generator art/tools/palace_tex.py (seeded; python3 palace_tex.py OUTDIR 1024, then klad new / apply / export --background).
- Blender lion: art/tools/lion_blender.py, art/src/lion.blend, assets/models/lion_lod0/1/2.glb (branch lion-sample-01).
- Screenshots: tex_sample01_door.png, tex_sample01_hall.png (software GPU, 1920x1080, Hall of the Ru).
### Checks run (code tool only)
- Tiling seams: 2x2 tiles of floor, wall and lion stone viewed, no seam visible (wrap copies of edge strokes).
- glTF validation of the lion GLBs: 0 errors, 0 warnings.
- The numbers in the table above, against the proposed rules: texel density fails for pillar and lion; contrast fails for floor and lion; saturation fails for the floor; brush scale fails for the floor.
### Open
- Round 2: repaint floor and lion stone with stronger marks, pillar repeats set for 256 px/m around, lion stone remapped to 256 px/m, floor saturation down to about 0.55; lion reshaped as hard carved planes (or a CC0/CC-BY lion re-materialled).
- Prop candidates from Sketchfab (helper search running): to be listed here with licence and triangle count.
- KTX2 compression, per-level loading, dispose, LOD (after approval).

## Samples, round 2 (24 Nov 2026, not approved)
### What changed (study rules + research report docs/research/Qin-palace-medieval-tech-fusion.md)
| Texture | change |
|---|---|
| hall_floor | base #6b3d30 (saturation 0.71 to 0.52); burnish strokes and 520 pebble dabs at 4-15 cm; lum sd 4.7 to 9.1 |
| hall_wall | 700 oil trowel strokes in the plaster; band strokes wrap mid-stroke (seam fixed: edge step 4.8 to 1.3) |
| pillar | one repeat around (543 to 272 px/m); smooth oil lacquer strokes 20-45 px (brush scale 1.3 to 11 cm) |
| door | unchanged look (bands wrap-safe) |
| lion_stone | 4 m per repeat (640 to 256 px/m); stronger mottling and chisel patches (lum sd 4.0 to 9.6) |
### Files
- assets/tex/*.png (round 2), art/src/*.klad, art/tools/palace_tex.py (paint stages), art/tools/paint_palace.py (klad pipeline + passes strips), art/tools/tex_check.py (rules check), art/round2/passes/*_passes.png, art/round1/ (round 1 PNGs and script).
- Run: python3 art/tools/palace_tex.py OPSDIR 1024; python3 art/tools/paint_palace.py KLAD OPSDIR art/src assets/tex art/round2/passes; python3 art/tools/tex_check.py assets/tex 1 4.
### Checks run (code tool only)
- tex_check.py: round 1 10 of 20, round 2 20 of 20 (density 0.8-1.25 x 256 px/m; brush scale 4-15 cm; lum sd 8-30; saturation cap 0.55 / 0.6 accents).
- Wrap seams (mean step at the edge vs inside): floor 1.4 vs 1.6, lion stone 1.7 vs 2.4, wall 1.3 vs 1.1, pillar 0.4 vs 0.5.
- Game: CI 45397493782 272 of 273 (only 42, a known balance item); software-GPU screenshots, Hall of the Ru: 12 calls, 842 tris, programs 8, textures 6.
### Open
- Lion shape and material: the research says stone lions are post-Qin and recommends segmented bronze guardian beasts with silver inlay; owner to choose (grey stone kept in round 2 for comparison).
- Not yet painted: corridor floor tiles (lozenge / 米 grid / cloud patterns), hollow-brick steps, rammed-earth terrace faces, grey unglazed roof tile with cloud tile ends, bronze for live machines (brass-gold) and dormant ones (patina), the core.
- Research suggests walls of white-ground plaster with painted bands and black kept for lacquer and cloth: round 2 already follows it.

## Draft library entry (proposal until approved)
## <N>. Qin Palace Painted (3D architecture, klad-painted materials), proposal
- Type: single
- Where: Empress Decrees (Burning Palace), tier medium; texel density 256 px/m desktop, 128 phone.
- Source: Qin palace records (咸阳宫 No. 1, Qin lacquerware, Warring States/Han bronze fittings); technique reference only; all art is original.
- Look: hard-edged Qin halls in matte black lacquer, cinnabar floors and lime plaster, painted by brush in klad with visible marks at one scale everywhere; bronze and stone props carved in hard planes with the same brush scale.
- Palette: as the ramps above.
- Grid, canvas, scale: 3D; textures 1024 desktop / 512 phone, 256 / 128 px per metre; KTX2.
- Proportions: props 7k / 2.5k / 800 tris; lion footprint 1.6 x 2.2 m, 2.4 to 2.6 m tall.
- Outline and light: no outlines; the game's single sun plus hemisphere; no baked light in tiling textures.
- Technique: art/tools/palace_tex.py (seeded strokes) into klad, export --background; props from Blender scripts or CC0/CC-BY geometry, re-materialled.
- Samples, approved <date>: none yet.
- Open: round 2 as above.
